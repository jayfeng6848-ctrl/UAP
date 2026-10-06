# P20 EVENT PRODUCER / HANDLER QUALIFICATION IMPLEMENTATION REPORT — BATCH 1

```yaml
P20 EVENT PRODUCER / HANDLER QUALIFICATION IMPLEMENTATION = PASS

Producer:            IMPLEMENTED · READY FOR ACCEPTANCE · QUALIFIED = NO
Handler Binding:     IMPLEMENTED · PRODUCTION REGISTERED = NO
Payload Validation:  IMPLEMENTED · PRODUCTION HANDLER = NO
Qualification Tests: IMPLEMENTED · 34 passed

Business Handler:    NOT AUTHORIZED（无真实下游用例）
Production Allowlist: EMPTY
Production Event:    NOT AUTHORIZED
Worker:              NOT AUTHORIZED
Migration:           NOT AUTHORIZED（No 0021）
Schema Change:       NOT AUTHORIZED

Commit: NO   Tag: NO   Push: NO
HARD STOP: ACTIVE
```

## 1. Executive Summary

```text
本轮把 Appendix AI 冻结的 Employee Event Contract 落成**可被资格化验证的代码能力**，
且**未接入生产 Company 路径**：

新增/变更（4 个代码文件 + 3 个测试模块，全部在授权范围内）：
  services/company/event_contract.py   冻结常量 + 纯 payload 校验器（无 I/O / 无 DB / 无授权）
  services/company/producer.py         Company Event Producer（构造/校验/持久化 · 复用调用方 session）
  services/consumer/kernel.py          EventHandlerSpec 增加显式 handler callable（HD-Q-01 最小增量）
  tests/company/test_company_event_contract.py
  tests/company/test_company_event_producer.py
  tests/company/test_company_event_consumer.py

核心证据：
  * 生产事件静默：真实 Company 11 条路由/用例运行后 events 行数**不变**，allowlist 仍 EMPTY
  * 事务原子性实测：成功三者同提交；事件失败 ⇒ 业务+审计回滚；审计失败 ⇒ 业务+事件回滚
  * actor 端到端保真：event.actor_type='USER' · event.actor_id = 原始认证用户（无任何 fallback）
  * Consumer 无 HTTP 亦可重建 USER 并重新授权（SubjectResolver 只依赖 users.id + active）
  * subject_type/subject_id = NULL · space_id = NULL · causation_id = NULL（与 AI 一致）
  * event identity ≠ business identity（event.id ≠ employee.id）
  * 生产 handler 注册 = 0（仅测试专用 handler，且不进入 production_allowlist()）

回归全绿（显式选择）：P15 冻结 53 passed/12 env-gated skipped · architecture 63 · Company 26 ·
  P20 API 15 · P17+P18 API 21 · 新增资格化 34

⇒ 实现完成，等待 **P20 EVENT PRODUCER / HANDLER QUALIFICATION ACCEPTANCE GATE**。
```

## 2. Authorization Sources

```text
Appendix AH = Event Design / Qualification Authorization
Appendix AI = Batch 1 Employee Event Contract Freeze（naming / schema_version=1 / payload 白名单 /
              resource identity in payload / actor=USER / subject=NULL / correlation 复用 /
              same-transaction / consumer re-auth / 逐类型幂等前置 / 无级联 / 无全局顺序）
Appendix AJ = Producer / Handler Qualification Implementation Authorization（HD-Q-01…05）
AGENTS.md（证据优先 · 显式测试 · 禁 broad sweep · 禁 commit/tag/push）
```

## 3. Baseline

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 · staged = 0（实现前后一致）
0019 sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020 sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4（未变）
No 0021 · alembic head = 0020_p20_company_authorization · production_allowlist() = EMPTY
```

## 4. Implementation Scope

```text
授权内实现：Producer · Handler binding infrastructure · Payload validation · Qualification tests
未实现（明确禁止）：业务 Handler · allowlist 注册 · allowlist 激活 · 生产事件发射 ·
  Worker 激活/部署 · migration / 新表 / 新权限 / 新授权引擎 / 新 subject 词表
范围：仅 employee.created / .updated / .suspended / .terminated（Batch 2 未触碰）
```

## 5. Files Changed

| 文件 | 变更 | 依据 |
| --- | --- | --- |
| `services/company/event_contract.py` | 新增（冻结常量 + 纯校验器） | AI D-P20E-DES-01/02/03/04 · HD-Q-02 |
| `services/company/producer.py` | 新增（envelope 构造 + 持久化 + 4 个 typed helper） | AI · AJ（Producer implementation） |
| `services/consumer/kernel.py` | **最小增量**：`EventHandlerSpec.handler: Callable|None = None` | HD-Q-01 |
| `tests/company/test_company_event_contract.py` | 新增（契约/校验/绑定） | AJ Qualification tests |
| `tests/company/test_company_event_producer.py` | 新增（envelope/原子性/事件静默） | AJ |
| `tests/company/test_company_event_consumer.py` | 新增（actor/重新授权/资源/租户/幂等基础设施） | AJ |

```text
未改动：apps/api/**（11 路由与 DTO 白名单未变）· domains/company/** · services/company/use_cases.py ·
  services/company/repository.py · migrations/** · services/consumer 的其余部分 · apps/worker/main.py
```

## 6. Producer Implementation

```text
`services/company/producer.py`
  emit_employee_event(session, *, event_type, tenant_id, actor_id, payload, correlation_id)
    ① 先 validate_event_payload(...)（非法 ⇒ MalformedEventPayload，**写入前**失败）
    ② event_id = core.audit.interfaces.new_event_id()（UUIDv7 · 与 DB default 二选一，不叠加）
    ③ INSERT public.events(... status='pending', attempts=0)
    ④ 返回 event_id
  四个 typed helper：employee_created / employee_updated / employee_suspended / employee_terminated
    （各自只组装 AI 白名单字段，绝不整行序列化）
事务规则：只接受调用方 session；**不 commit / 不 rollback / 不新开连接**（AJ §19）
接线状态：**未被 use_cases 调用** ⇒ 生产路径保持事件静默（AJ §7）
```

## 7. Event Contract Mapping（实测写入值）

| 契约字段 | 实测写入 | 依据 |
| --- | --- | --- |
| event_type | employee.created / .updated / .suspended / .terminated | AI DES-01 |
| schema_version | 1 | AI DES-02（core EVENT_SCHEMA_VERSION） |
| id（event identity） | new_event_id()（UUIDv7）· ≠ employee.id | AI DES-04 · AJ §16 |
| occurred_at | now() | envelope |
| tenant_id | 员工 tenant | AI DES-07 |
| space_id | NULL | AI DES-07 |
| actor_type / actor_id | 'USER' / 原始认证用户 | AI DES-05 |
| subject_type / subject_id | NULL / NULL | AI DES-06 |
| payload | 白名单字段（见 §15） | AI DES-03 |
| correlation_id | 请求 correlation（x-correlation-id） | AI DES-07 |
| causation_id | NULL | AI DES-07 |
| status / attempts | 'pending' / 0 | P15 消费端字段 |

## 8. Actor Propagation

```text
实测：producer 写入 actor_type='USER'（大写，AI 冻结值）· actor_id = 传入的认证用户 id；
     缺失或非法 actor ⇒ MalformedEventPayload（missing_actor / invalid_actor），**不写事件**
禁止的替代路径均有测试覆盖：无 synthetic USER · 无 platform_admin fallback ·
无 worker-as-actor · 无 DB-principal-as-actor（§29 负向测试）
载体：沿用现有 actor carrier（API authenticate_actor → 用例 actor_id → producer 入参），未创建第二套 actor context
```

## 9. Tenant / Space

```text
tenant_id = 调用方给出的员工 tenant（Company 用例中来自 path tenant 且已校验 active）
space_id  = NULL（写入语句硬编码 NULL，无法被 payload 覆盖）
禁止推导：不从 Assignment、当前用户、worker 推导 space；payload 中不允许出现 tenant_id/space_id
  （额外字段会被校验器判为 unknown_field，见 §29）
```

## 10. Subject

```text
写入 subject_type = NULL · subject_id = NULL（AI DES-06 冻结）
未引入 COMPANY_EMPLOYEE / EMPLOYEE / USER 等任何 subject 词表值；consumer 侧亦不依赖该两列
```

## 11. Correlation

```text
correlation_id = 复用既有请求 correlation（API `x-correlation-id` → 用例 → producer 入参）
producer 对 correlation 做 UUID 校验（列类型为 uuid）；非 UUID ⇒ MalformedEventPayload("invalid_correlation_id")
causation_id 恒为 NULL（不伪造 lineage）
```

## 12. Event Identity

```text
生成：core.audit.interfaces.new_event_id()（UUIDv7）· 单一来源（不依赖 DB default，避免双重生成）
实测：event.id ≠ employee.id（业务身份与事件身份分离）
身份三分离：event identity（events.id）· business identity（payload.resource_id=employee.id）·
idempotency key（业务自然键 tenant_id+employee_no）
```

## 13. Authorization

```text
Producer **未新增任何 permission**：业务操作仍由既有 AuthorizationService 判定
  employee.created    → company_employee / create
  employee.updated    → company_employee / update
  employee.suspended  → company_employee / update
  employee.terminated → company_employee / update
Event 不是权限；producer 不重复建第二套授权（未 import 授权模块之外的任何授权逻辑）
```

## 14. Transaction Integration

```text
实测矩阵（隔离库）：
  Success            ：business + audit + event **三者同事务提交**（同一 session / 同一 DB TX）
  Event 失败         ：business + audit 全部回滚（company_employees 0 行 · audit_logs 0 行）
  Audit 失败         ：business + event 全部回滚（company_employees 0 行 · 无对应事件行）
  业务失败           ：既有验证（Company 轮）——同一机制自然覆盖
commit owner 仍为 RuntimeDatabase.transaction()；producer 无 commit/rollback/独立连接
```

## 15. Payload Validation

```text
实现：`services/company/event_contract.validate_event_payload(event_type, schema_version, payload)`
  · 纯函数（无 DB / 无 I/O / 无授权；AST 断言已测试）
  · 检查顺序：event_type 冻结 → schema_version=1 → payload 是对象 → 未知字段 → 禁止字段 →
    必填字段 → 类型 → resource_type=company_employee → resource_id 为 UUID →
    逐事件语义（changed_fields ⊆ updatable · 生命周期方向）
落点：Producer 写入前（§6）+ Handler Boundary（测试内示范：非法 payload 在业务副作用前抛错）
终态：MalformedEventPayload ⇒ 既有 P15 `malformed_payload` 语义（未新增失败类别）
```

## 16. Handler Binding

```text
`services/consumer/kernel.py::EventHandlerSpec` 新增字段：
    handler: Callable[[Any], None] | None = None
兼容性：既有 5 个位置参数构造不受影响（P15 冻结测试 53 passed）；
        既有 `getattr(spec, "handler", None)` 语义保持不变（None ⇒ handler_not_bound 终态）
安全性：仅 trusted code registration 可绑定；**不来自 payload / 模块路径 / 任何动态加载**
        （无 importlib / 无字符串解析 / 无 DB 驱动执行）
资格规则未改：eligible 仍要求 producer evidence + authorization semantics + acceptance +
        幂等证明；`handler` 字段不参与（避免悄然放宽冻结门槛）
```

## 17. Test-Only Handler

```text
仅存在于 `tests/company/test_company_event_*.py`（TEST ONLY / NON-PRODUCTION），用途：
  verify EventHandlerSpec binding · payload validation · actor reconstruction ·
  authorization path · idempotency harness
明确证明：production_allowlist().is_empty = True · specs = {} ·
          四个事件类型在生产注册表中 **不可解析**（resolve 抛 UnsupportedEventType）
生产代码中 `EventHandlerSpec(` 实例化 = 0（全仓非测试扫描）
```

## 18. Consumer Actor Reconstruction（无 HTTP）

```text
实测：由事件 envelope 直接构造 Subject(identity_id=actor_id, subject_type='USER',
      actor_id=actor_id, tenant_id=tenant_id) → 既有 SubjectResolver 按 users.id + status='active'
      解析（不依赖 session / bearer / worker 身份）⇒ 授权成功（平台管理员 actor）
负向：actor 无授权 ⇒ DENY；actor 不存在 ⇒ DENY（SubjectResolutionError）
```

## 19. Consumer Re-Authorization

```text
实测：Consumer 侧重新进入唯一引擎 AuthorizationService（Action('read', 'company_employee') ·
      ResourceRef(type='company_employee', id=<集合资源 id>, tenant_id=<事件 tenant>)）
分支：原 actor 有授权 → ALLOW；无授权/未知 actor → DENY；投影缺失 → DENY；伪造资源 id → DENY
禁止路径未被使用：无 platform_admin fallback · 无 worker fallback · 无 system principal 替代
```

## 20. Resource Resolution

```text
实测：payload.resource_type='company_employee' + payload.resource_id=employee.id
      → Consumer 先以 (tenant, resource_type) 解析**集合资源**（services/company/projection.collection_resource）
      → 再以集合资源 id 调用引擎
缺投影：collection_resource = None ⇒ 判定 DENY（不创建、不修复）
明确区分：payload.resource_id（业务身份）≠ resources.id（授权资源行）
```

## 21. Tenant Isolation

```text
Producer：tenant_id 直接取自业务对象（Employee），无法从 payload 覆盖
Consumer：(a) 伪造资源 id（未知 resources 行）⇒ DENY（实测）
          (b) 伪造 tenant（事件声称 B、业务对象属 A）⇒ 以 B 的 tenant 谓词重新解析业务对象得到 0 行
              ⇒ 业务层 DENY（实测：tenant A 下 1 行、tenant B 下 0 行）
结论：Batch 1 的租户隔离由**tenant 谓词的业务重解析**保证（见 O-P20E-IMPL-001 说明）
```

## 22. Idempotency

```text
本轮交付**幂等基础设施与证据形式**，不宣称生产 Handler 幂等：
  逐事件凭证（AI 词表）：employee.created = schema_guaranteed（uq_company_employees_no）·
    employee.updated = naturally_idempotent（目标状态幂等）·
    employee.suspended = naturally_idempotent（条件更新）·
    employee.terminated = naturally_idempotent（终态）
  重复投递测试：same event_id + same natural key 的第二次投递被判定为 no-op（实测 applied set 仅 1）
明确状态：Idempotency Infrastructure/Test Design = IMPLEMENTED ·
          **Production Handler Idempotency = NOT QUALIFIED**（无业务 Handler）
未使用 "UUID uniqueness" 作为任何幂等证明；未创建 dedup / receipt / identity 表
```

## 23. Failure / Retry

```text
未修改任何 P15 冻结值：MAX_ATTEMPTS 10 · backoff 5/10/20/40/80/160/320/600/600 · 无 jitter ·
  lease 120s · heartbeat 40s · batch ≤10 · concurrency 4
Handler 侧不得 retry/sleep/backoff/attempt++（测试专用 handler 仅做纯校验与记录）
失败类别沿用既有 6 种终态（含 malformed_payload / handler_not_bound），未新增 Company 类别
```

## 24. Partition

```text
沿用 P10 手工分区维护（未创建 2026-11 分区 · 无 scheduler / 无自动 DDL）
实测当前月 2026-10 分区 events_202610 覆盖完整，producer 写入成功（本报告 §6 的写入均落在该分区）
未来跨月属于 Activation Gate 的运维前置条件（已登记）
```

## 25. Production Event Silence（核心证据）

```text
实测：在真实 Company 服务路径上依次执行 create → update → suspend → terminate → create_assignment
      （全部经 canonical 授权与审计），断言：
        events 行数 **未变化**
        production_allowlist().is_empty = True · specs = {}
原因：producer 未被 use_cases 接线（implementation present / activation disabled），
      且 allowlist 从未包含 Company 事件类型（allowlist 不是 producer 开关）
⇒ 正常生产 Company 请求不会产生任何 production event（AJ §7 要求已满足）
```

## 26. Allowlist

```text
production_allowlist() = EMPTY（0 entries）· 未加入 employee.created/.updated/.suspended/.terminated
测试：生产注册表无法 resolve 任何 Company 事件类型；公司 handler 与生产注册表严格分离
```

## 27. Worker

```text
未修改 apps/worker/main.py（仍以 handlers=production_allowlist() 启动）
生产 handler 注册 = 0（扫描 services/consumer/ 与 apps/worker/ 无 Company 注册）
Worker = NOT AUTHORIZED（未启动、未部署、未新增 task/scheduler）
```

## 28. Regression

```text
新增资格化测试（本轮）        = 34 passed
P15 冻结测试（内核改动回归）   = 53 passed / 12 skipped（env-gated：UAP_RUNTIME_TEST_DSN 未设置，
                               fail-closed 跳过，非失败）
tests/architecture            = 63 passed（Core → Domain = 0 保持）
Company 既有套件（5 模块）      = 26 passed
tests/api/test_company_api.py = 15 passed（11 路由 / DTO / 错误码 / 租户路径未变）
P17 acceptance + P18 HTTP API = 21 passed
```

## 29. Security Negative Tests

```text
payload：missing field · wrong type · unknown field · forbidden secret field ·
         wrong schema_version · wrong resource_type · invalid resource_id ·
         invalid changed_fields · 非法生命周期方向 → 全部 MalformedEventPayload（且零业务副作用）
actor  ：missing actor · invalid actor → 拒绝且不写事件
payload 伪造 tenant：额外 tenant_id 字段 → unknown_field 拒绝（tenant 不可由 payload 覆盖）
consumer：未知资源 id → DENY · 未知 actor → DENY · 无授权 actor → DENY · 投影缺失 → DENY
worker 与 actor 分离：runtime principal 可写业务行，但无授权的 actor 仍 DENY（DB 权限 ≠ 业务授权）
泄露面：payload 白名单 + 禁止字段；无 SQL/堆栈/DSN/凭据进入 payload 的路径
```

## 30. Findings

```text
BLOCKING：无
  （未发现无法在现有分层内实现冻结契约的情形；未新增 schema/权限/授权引擎/词表）

O-P20E-IMPL-001【观察 · 非阻断】Batch 1 的授权主体为 platform_admin（PLATFORM scope，附录 AF D-P20D-01）
  ⇒ 引擎层面的 scope 检查**不会**单独拒绝"跨租户上下文"（PLATFORM 授权合法覆盖所有租户）。
  因此租户隔离实际由**tenant 谓词的业务重解析**保证（与 Company 用例一致），
  这一点必须写入未来 Handler 的实现约束（不得接受调用方提供的 tenant，必须从事件 tenant 派生并解析业务对象）。

O-P20E-IMPL-002【观察 · 非阻断】事件 envelope 的 actor_type 依 AI 冻结写入 "USER"（大写），
  而 audit_logs 的历史约定为小写 'user'。两者数据结构不同、无约束冲突；未来 Handler 必须按冻结契约值处理。

O-P20E-IMPL-003【观察 · 非阻断】producer 未被业务路径接线（本轮设计要求如此）；
  未来接线轮次需在 use_cases 的同一 `with db.transaction()` 块内调用 producer，并补充
  "PATCH 实际变更字段 → changed_fields" 的字段级计算来源（当前 use case 已可计算 changed 列表）。

保留既有：O-1（services/company 3 处 inline SQL）· O-2（list = limit-only）· events 分区手工维护 ·
OI-G-4（未修，本轮授权未覆盖）
```

## 31. Qualification Status

```text
                   IMPLEMENTED   QUALIFICATION-PROVEN   QUALIFIED   PRODUCTION-ACTIVE
Producer               YES              partial             NO            NO
Handler Binding        YES              partial             NO            NO
Payload Validation     YES              YES（纯逻辑）        —             NO
Business Handler       NO               NO                  NO            NO
Allowlist              —                —                   —             EMPTY
```

```text
Producer / Handler Binding = IMPLEMENTED，**等待 Acceptance Gate** 正式判 Qualified；
Business Handler = NOT AUTHORIZED（无真实下游用例，HD-Q-03）。
```

## 32. Acceptance Inputs（交下一 Gate 的证据包）

```text
① Producer test results            ：34 passed（含 envelope 映射与 4 事件写入）
② Transaction rollback evidence    ：成功/事件失败/审计失败三条路径实测
③ Actor propagation evidence       ：actor_type='USER' · actor_id 精确保真 · 非法 actor 拒绝
④ Payload validation evidence      ：12 项非法 payload 参数化 + 纯函数性断言
⑤ Consumer USER reconstruction     ：无 HTTP 重建 Subject 并授权成功
⑥ Consumer re-auth evidence        ：有授权 ALLOW / 无授权 DENY / 未知 actor DENY
⑦ Resource resolution evidence     ：集合资源映射 · 缺失 DENY · 伪造 id DENY
⑧ Tenant isolation evidence        ：伪造 tenant ⇒ 业务重解析 0 行
⑨ Idempotency evidence             ：重复投递 no-op（基础设施层）· 生产 Handler 幂等 NOT QUALIFIED
⑩ Production event silence evidence：真实 Company 路径 events 行数不变
⑪ Allowlist empty evidence         ；⑫ No worker activation evidence；⑬ No migration evidence
```

## 33. Final Gate

```text
P20 EVENT PRODUCER / HANDLER QUALIFICATION IMPLEMENTATION = PASS

Producer:             IMPLEMENTED · READY FOR ACCEPTANCE
Handler Binding:      IMPLEMENTED · READY FOR ACCEPTANCE
Business Handler:     NOT AUTHORIZED
Qualified Handler:    0
Production Allowlist: EMPTY
Production Event:     NOT AUTHORIZED
Worker:               NOT AUTHORIZED
Migration:            NOT AUTHORIZED

（PASS 不代表 Producer Qualified = YES / Handler Qualified = YES / Production Event = YES /
  Allowlist = ACTIVE / Worker = ACTIVE）
```

## 34. Hard Stop

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0 · 未 commit / tag / push
0019 / 0020 sha256 未变 · No 0021 · alembic head 未变 · allowlist EMPTY（0 entries）
events（共享库）= 0 · company 表（共享库）= 0 · formal uap = 0 public 表 · 无残留临时库
本轮代码写入 = 4 个文件（3 生产 + 3 测试中的实现面）· 未激活 allowlist · 未注册生产 handler ·
未启动 worker · 未发射生产事件

HARD STOP = ACTIVE
下一阶段只能是：P20 EVENT PRODUCER / HANDLER QUALIFICATION ACCEPTANCE GATE
  （重点验证：业务+审计+事件同事务 · 原始 USER 端到端保真 · Consumer 无 HTTP 重建 USER ·
    消费侧确实重新授权 · worker 身份不能提升 actor · 缺投影 = DENY · malformed payload 零副作用 ·
    重复投递安全 · 生产路径保持事件静默 · Allowlist 保持 EMPTY）
```

**END OF P20 EVENT PRODUCER / HANDLER QUALIFICATION IMPLEMENTATION REPORT（Producer/Handler Binding/Payload Validation 已实现且未接线 · 34 资格化测试 + 53 P15 + 63 架构 + 26 Company + 15 API + 21 P17/P18 全绿 · 生产事件静默 · allowlist EMPTY · 未 commit；2026-10-04）**
