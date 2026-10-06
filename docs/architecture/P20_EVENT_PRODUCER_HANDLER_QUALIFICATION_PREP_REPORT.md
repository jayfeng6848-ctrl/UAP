# P20 EVENT PRODUCER / HANDLER QUALIFICATION PREP REPORT — BATCH 1

```text
阶段     = Qualification PREP（只读审计 / Qualification Design / Evidence Package）
输入     = 附录 AI（Batch 1 Employee Event Contract = FROZEN）+ 附录 AH / AB + 既往 4 份 PREP/ACCEPTANCE 报告
本轮禁止 = Producer/Handler 实现 · register() · allowlist 条目 · INSERT INTO events · Worker/Handler 激活 ·
           0021 · DDL/DML · 新表/新词表/新权限/新授权引擎 · 修改 Company/P15/P16/P18/P20 · 修改 PDL · commit/tag/push
仓库写入 = 仅本报告
```

## 1. Executive Summary

```text
结论：Batch 1 的 Producer 侧证据链基本齐备（调用链、事务所有者、身份载体、授权点、DB 权限、
      事件身份机制均可证明或可设计）；Consumer/Handler 侧存在**两处结构性阻断**，且**当前不存在
      任何下游业务消费用例**。

Producer Readiness   = DESIGNABLE（唯一缺失步骤 = 事件写入代码本身，属未来实现）
Handler Readiness    = BLOCKED / NOT YET QUALIFIABLE（见 F-P20E-QUAL-001…003）

关键实测（详见各节）：
  * uap_runtime **已具备 events INSERT**（含 events_202609/202610 分区）⇒ 未来 producer **无需新权限**
  * 事务所有者唯一：`RuntimeDatabase.transaction()`；审计与业务写共用同一 session
    ⇒ 事件写入可加入**同一 DB 事务**（DESIGNABLE）
  * `events` 为 occurred_at 月度分区；当前月（2026-10）分区存在且覆盖完整 ⇒ 写入路径可行
  * Consumer 可仅凭 `event.actor_id` 重建 USER 主体（SubjectResolver 只查 users.id + active，无 session 依赖）
  * `events.subject_type/subject_id` 甚至未被 CLAIM SQL 选取 ⇒ **subject = NULL 完全兼容**
  * **F-P20E-QUAL-001（BLOCKING）**：`EventHandlerSpec` **没有 handler 字段**，而 worker 以
    `getattr(spec, "handler", None)` 取处理函数 ⇒ 现状下任何 allowlist 条目都会以
    `handler_not_bound` 终结，**当前内核不存在绑定可调用 handler 的机制**（P15 冻结代码，不得改）
  * **F-P20E-QUAL-002（BLOCKING for Handler Qualification）**：`malformed_payload` 终态常量存在但
    **生产代码中无任何使用点** ⇒ payload 白名单校验在现有内核中**没有执行位置**
  * **F-P20E-QUAL-003（NOT YET QUALIFIABLE）**：平台内**不存在**任何 Employee 事件的下游业务消费用例
    ⇒ 不得为"让事件跑通"虚构 Handler

系统状态未改变：Allowlist EMPTY · Producer 0 · Qualified Handler 0 · Worker NOT AUTHORIZED ·
  events 0 · 无 0021 · P20 Domain/API/Authorization 基线未变。

⇒ P20 EVENT PRODUCER / HANDLER QUALIFICATION PREP = PASS（Qualification 准备完成，未实现、未授权）
```

## 2. Authority Sources

```text
AGENTS.md · PDL 附录 AB / AC / AD / AE / AF / AG / AH / **AI（本轮契约权威）**
P20_EVENT_DECISION_PREP_REPORT.md · P20_EVENT_DESIGN_QUALIFICATION_PREP_REPORT.md ·
P20_EVENT_CONTRACT_FREEZE_BATCH1_PREP_REPORT.md · P20_COMPANY_API_ACCEPTANCE_REPORT.md
真实实现：apps/api/** · services/company/** · domains/company/** · services/consumer/** ·
          apps/worker/main.py · core/event/** · core/auth（授权主体契约）· services/authorization/** ·
          infrastructure/database/runtime.py · migrations_alembic/** · 实际 DB GRANT 快照
```

## 3. Baseline Integrity

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0 · tags = 16（未新增）
0019 sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020 sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4（未变）
No 0021 · alembic single head = 0020_p20_company_authorization
production_allowlist() = EMPTY（0 entries）· Producer = 0 · Qualified Handler = 0 · Worker = 0 ·
events 行数 = 0 · uap_b1_test = 0017_p13_seed · formal uap = 0 public 表
⇒ BASELINE: PASS
```

## 4. AI Contract Recovery（逐项映射到代码能力）

| AI 冻结项 | 冻结值 | 现有代码能力 | 判定 |
| --- | --- | --- | --- |
| event_type | employee.created / .updated / .suspended / .terminated | events CHECK 正则接受点分小写 ≥2 段 | PROVEN |
| schema_version | 1 | envelope 列 + `EVENT_SCHEMA_VERSION = 1`（core） | PROVEN |
| actor | USER · 真实认证发起用户 | API `authenticate_actor` → `actor.user_id` → 用例 `actor_id` | PROVEN（载体）/ DESIGNABLE（写入 envelope） |
| tenant_id | employee.tenant_id | 用例内已取得并校验（tenant active） | PROVEN |
| space_id | NULL | envelope 可空；Employee 无语义空间 | PROVEN |
| subject_type/subject_id | NULL | CLAIM SQL 未选取该两列；ClaimedEvent 无该字段 | **PROVEN（兼容）** |
| resource identity | payload.resource_type=company_employee · resource_id=employee identity | payload jsonb；集合投影 helper 存在 | DESIGNABLE（需 consumer 侧映射，§15） |
| correlation_id | 既有请求 correlation | API `x-correlation-id` → `_correlation()`；envelope 有列 | PROVEN |
| causation_id | NULL | envelope 可空 | PROVEN |
| consumer re-authorization | 必须重新授权 | AuthorizationService + SubjectResolver（无 session 依赖） | DESIGNABLE |
| missing projection = DENY / no self-healing | 冻结 | 现状即如此（RESOURCE_NOT_PROVISIONED） | PROVEN |
| business + audit + event 同事务 | 冻结 | 单一事务所有者（§6） | DESIGNABLE（事件写入未实现） |
| no global ordering | 冻结 | CLAIM SQL：ORDER BY occurred_at + concurrency + SKIP LOCKED | PROVEN（语义已如此） |
| event_id = event identity | 冻结 | `new_event_id()`（UUIDv7）+ DB 默认；PK(id, occurred_at) | PROVEN（机制）/ DESIGNABLE（生成点） |
| no new permission / dedup / table | 冻结 | uap_runtime 已有 events INSERT（§7） | PROVEN |
| Production Activation | NOT AUTHORIZED | allowlist EMPTY | PROVEN |

## 5. Producer Call Graph（真实调用链 · Employee 四事件共用）

```text
HTTP POST/PATCH/POST(action)
  apps/api/routes/company.py::create_employee / update_employee / suspend_employee / terminate_employee
   └─ _actor(db, request) → services.use_cases.authenticate_actor(bearer token)      [actor_id = users.id]
   └─ _run(use_case, ...) → services/company/use_cases.py::<use case>
        └─ with db.transaction() as session:                ← 事务开启处（RuntimeDatabase.transaction）
             1) _authorize(db, session, actor_id, tenant_id, action, resource_type)
                  ├─ ResourceProjectionRepository().collection(...)   ← 集合资源解析（缺 → RESOURCE_NOT_PROVISIONED）
                  └─ AuthorizationService(engine=db.engine).authorize(Subject(USER), Action, ResourceRef)
             2) _require_active_tenant(session, tenant_id)           ← 上下文门禁
             3) domain validation（不变量 / 生命周期）
             4) repository write（services/company/repository.py · 同一 session · 不 commit）
             5) _audit(session, ...)                                  ← INSERT audit_logs（同一 session）
        └─ 退出 with → COMMIT（成功）/ ROLLBACK（异常）
                                                       ↑
                                  未来 event INSERT 应插入此处（步骤 5 之后、提交之前）
```

```text
谁创建 transaction/session ：RuntimeDatabase.transaction()（infrastructure/database/runtime.py）
谁 commit / rollback      ：RuntimeDatabase.transaction()（成功 commit · 异常 rollback）
Business mutation 在哪写   ：services/company/repository.py（同一 session）
Audit 在哪写              ：services/company/use_cases.py::_audit（同一 session · 同一事务）
未来 event 应插在哪里      ：同一 `with db.transaction()` 块内（步骤 5 之后）
event_id 由谁生成          ：现有机制为 core.audit.interfaces.new_event_id()（UUIDv7）；DB 侧默认 uap_uuid_v7()
correlation_id 从哪来      ：apps/api/routes/company.py::_correlation(request)（x-correlation-id）
actor_id 从哪来            ：authenticate_actor → actor.user_id → 用例参数 actor_id（已贯穿到 _authorize 与 _audit）
tenant_id 从哪来           ：path tenant_id（用例已校验 active）
⇒ 所有载体均存在（PROVEN）；唯一缺口 = **事件写入步骤本身未实现**（F-P20E-003 延续）
```

## 6. Transaction Boundary（核心审计）

```text
transaction owner : RuntimeDatabase.transaction()（sessionmaker 绑 engine；autoflush=False/expire_on_commit=False）
session lifetime  : 单个 use case 调用（with 块内）
commit owner      : RuntimeDatabase.transaction()（成功路径）
rollback owner    : RuntimeDatabase.transaction()（异常路径；异常向上抛出）
repository flush  : 仓储不 commit / 不 rollback（仅 session.execute）
audit write       : 同一 session（_audit 使用 session.execute → 同事务）
```

| Operation | Business Mutation | Audit | Current Transaction Owner | Event Can Join Same TX? | Evidence |
| --- | --- | --- | --- | --- | --- |
| employee.create | INSERT company_employees | INSERT audit_logs（同 session） | RuntimeDatabase.transaction() | **YES（same session + same DB TX）** | use_cases.py::create_employee（单 with 块 · 两处 execute） |
| employee.update | UPDATE company_employees | 同上 | 同上 | YES | use_cases.py::update_employee |
| employee.suspend | UPDATE（条件 expect='active'） | 同上 | 同上 | YES | use_cases.py::_transition_employee |
| employee.terminate | UPDATE（终态 + terminated_at） | 同上 | 同上 | YES | 同上 |

```text
区分（不得混淆）：same session = 是；same DB transaction = 是；same logical transaction = 是（三者同时成立）。
"同一 Python request" 不是证据 —— 证据是同一 session 对象上执行的三条语句位于同一 with 块内。
结论：事件写入可**在不改变事务边界的前提下**加入同一事务（DESIGNABLE · 需代码）。
```

## 7. DB Privilege Feasibility（只读 GRANT 快照）

```text
Company business write principal = uap_runtime（get_database → RuntimeDatabase(require_role="uap_runtime")）
Audit write principal           = uap_runtime（audit_logs INSERT 已具备）
Future event write principal    = uap_runtime（同一事务内的第三条语句）

实测 uap_runtime 相关授权：
  events            = INSERT, SELECT, UPDATE
  events_202609     = INSERT, SELECT, UPDATE
  events_202610     = INSERT, SELECT, UPDATE
  audit_logs(_*)    = INSERT, SELECT
  resources         = INSERT, SELECT, UPDATE
  company_employees = INSERT, SELECT, UPDATE（0019 授予）
  company_assignments = INSERT, SELECT, UPDATE（0019 授予）
⇒ 未来 producer **无需新增任何 GRANT**（events INSERT 已存在）· 不存在"授权会破坏边界"的问题
⇒ 权限维度：PROVEN（No HUMAN DECISION required）
```

## 8. Event Partition Write Path

```text
events 为 LIST/RANGE 分区父表（分区键 occurred_at）：
  events_202609 :: FOR VALUES FROM ('2026-09-01') TO ('2026-10-01')
  events_202610 :: FOR VALUES FROM ('2026-10-01') TO ('2026-11-01')
当前日期 = 2026-10-04 ⇒ 当前月分区 events_202610 存在且覆盖完整
INSERT INTO public.events（父表）由 PostgreSQL 按 occurred_at 自动路由到当月分区（父表 INSERT 权限已具备）
⇒ 写入路径 PROVEN（当前月）
GAP（运维级 · 非阻断设计）：**不存在 2026-11 及以后分区**；P10-D10 已冻结"分区维护 = 手工运维（无 scheduler）"。
  激活前必须确认分区维护责任与流程（属运维事项，不得在本轮 DDL 创建）。
```

## 9. Event Identity

```text
event_id 类型/生成：uuid · 应用侧 core.audit.interfaces.new_event_id()（UUIDv7：时间有序 + 随机）
                    DB 侧默认 uap_uuid_v7()（0002 建立）
唯一性约束：PRIMARY KEY (id, occurred_at)（分区表以 occurred_at 为分区键，故 PK 含之）
三类身份区分（不得混同）：
  event identity   = events.id（投递/幂等对账的事件身份）
  business identity= employee_id（业务对象身份 · 置于 payload.resource_id）
  idempotency key  = 业务自然键（tenant_id + employee_no 等）· 供 handler 判定重复
Producer retry 风险：若业务事务整体重试 ⇒ 前一事务已回滚（无事件残留）；若业务操作被重复执行
  ⇒ 属**新的业务操作**，由业务幂等键拦截（见 §21）。UUID 随机性**本身不构成**幂等证明。
⇒ 机制 PROVEN；"不会生成两条重复业务事件"依赖同事务规则 + 业务唯一键 ⇒ DESIGNABLE
```

## 10. Actor Propagation

```text
实测链路：HTTP Bearer session → authenticate_actor(db, token) → RuntimeActor(user_id, subject_type='USER')
          → route 传入 actor_id → use case 参数 actor_id → _authorize(Subject(identity_id=actor_id,
            subject_type="USER", actor_id=actor_id)) → _audit(actor_id) → （未来）events.actor_id
结论：actor_id 在整个链路中**已是显式参数**（非隐式全局状态）⇒ PROVEN（载体）
未来 producer 只需把同一 actor_id 写入 envelope.actor_id（actor_type='user'）⇒ DESIGNABLE
禁止（AI 冻结）：worker/DB principal/platform_admin/bootstrap/migrator/service identity 伪装 USER
注意：Company 用例当前只接受 user 主体的 actor_id（F-P20E-002 既有登记）⇒ 与 AI「USER only」一致
```

## 11. Producer Authorization

| Event | Business operation | canonical action | resource_type | actor | tenant | 授权时机 |
| --- | --- | --- | --- | --- | --- | --- |
| employee.created | create_employee | create | company_employee | 认证用户 | path tenant（active 校验） | 业务写入**之前** |
| employee.updated | update_employee | update | company_employee | 同上 | 同上 | 同上 |
| employee.suspended | suspend_employee | update | company_employee | 同上 | 同上 | 同上 |
| employee.terminated | terminate_employee | update | company_employee | 同上 | 同上 | 同上 |

```text
证据：四个用例的首步均为 `_authorize(...)`（use_cases.py），且 _authorize 内部先解析集合资源，
      再调用唯一引擎；返回非 ALLOW 即抛 AUTHORIZATION_DENIED（fail-closed）。
⇒ PROVEN（producer 侧授权）；不新增任何 permission。
```

## 12. Consumer Actor Reconstruction（核心可行性）

```text
问题：Consumer 无 HTTP session，如何用 event.actor_id 重建可被引擎接受的主体？
实测（services/authorization/subjects.py::SubjectResolver._resolve_user）：
  user = repository.get_user(subject.identity_id)      ← 仅按 users.id 查询
  if user is None or status != 'active' → SubjectResolutionError（→ DENY）
  role_ids = repository.role_ids_for_user(user_id, tenant_id, space_id)
⇒ **引擎不依赖 session/HTTP，只依赖 users.id + 状态 + 会员关系** ⇒ Consumer 可直接构造
  Subject(identity_id=event.actor_id, subject_type='USER', actor_id=event.actor_id, tenant_id=event.tenant_id)
  并调用 AuthorizationService → 重新得到 canonical 决策。
⇒ DESIGNABLE（无需新机制）；"原 actor 已失权/停用/不存在" ⇒ 自然 DENY（fail-closed）
```

## 13. Consumer Identity Boundary

| Identity | Meaning | Used For Authorization? | Used For DB Access? |
| --- | --- | --- | --- |
| Event Actor | 原始业务主体（`event.actor_id`） | **YES**（重建 Subject） | NO |
| Worker Identity | 执行进程（worker_id 字符串） | **NO as user** | NO（仅用于 claim/lease 归属） |
| DB Principal | PostgreSQL 角色（uap_runtime） | NO | YES |
| Platform Admin | 特权角色 | 仅当它就是原始 actor 时才成立 | 依冻结模型 |

```text
实测依据：ClaimedEvent 仅携带 id/occurred_at/event_type/schema_version/tenant_id/space_id/actor_type/
          actor_id/payload/attempts/correlation_id（不含 worker 身份 · 不含 subject）；
          handler 在 `_execute` 中仅收到 `event` 对象（worker 身份不注入 handler）。
⇒ Worker ≠ Actor 且 DB Principal ≠ Actor（结构上成立）· PROVEN
```

## 14. Consumer Re-Authorization（设计 + 负向矩阵）

```text
设计路径（复用既有引擎，不新增授权语义）：
  1) subject  = Subject(identity_id=event.actor_id, subject_type='USER', actor_id=event.actor_id,
                        tenant_id=event.tenant_id)
  2) resource = 以 (event.tenant_id, payload.resource_type) 解析**集合资源**（复用
                services/company/projection.py::collection_resource · 缺 → DENY）
  3) action   = handler 所需的既有 canonical action（Batch 1 = read/update 之一，具体由未来 handler 职责决定）
  4) 调用 AuthorizationService（唯一引擎）→ 非 ALLOW 即 DENY（终态）
```

| Scenario | Expected | 状态 |
| --- | --- | --- |
| Original user still authorized | ALLOW | DESIGNABLE |
| Original user loses permission | DENY | DESIGNABLE（引擎天然如此） |
| Resource projection missing | DENY | PROVEN（现状即 DENY） |
| Tenant mismatch（payload 伪造 tenant） | DENY | DESIGNABLE（以 tenant 谓词解析 + 引擎 cross-tenant 判定） |
| Inactive tenant | DENY / 冻结生命周期处理 | DESIGNABLE（需在 handler 内显式校验 tenant active） |
| Worker privileged but actor unauthorized | DENY | PROVEN（worker 身份不进授权） |
| Platform admin is worker only | DENY | PROVEN（同上） |
| Event payload forged to another tenant | DENY | DESIGNABLE（**不得信任 payload tenant**，须 canonical 解析） |

## 15. Resource Resolution（关键澄清）

```text
现有引擎：AuthorizationService → ResourceResolver.resolve(ref) 按 **resources.id** 读取资源行；
          Company 的授权目标 = **tenant 级集合资源**（resource_type=company_employee · natural_key='employees' ·
          独立 row id，**不等于 employee.id**）。
因此 payload.resource_id（= employee 业务身份）**不能直接**作为引擎的 resource id：
  Consumer 必须先 (tenant_id, resource_type) → 集合资源 id（既有 helper：collection_resource），
  再构造 ResourceRef(type='company_employee', id=<collection id>, tenant_id=<tenant>)。
投影存在 → 可授权；投影缺失 → DENY（RESOURCE_NOT_PROVISIONED 同族）· 无自愈、无自动创建。
⇒ 该映射关系为 **DESIGNABLE**（复用既有 helper）；**不得**因此新增 events.resource_type/resource_id 列（AI 已冻结不改 envelope）。
```

## 16. Tenant Isolation

```text
Producer：event.tenant_id = employee.tenant_id（用例内已取得并校验 active）
Consumer：event.tenant_id 仅作**上下文提示**，必须由 canonical 解析/授权确认；不得覆盖授权 tenant context
负向证明设计（未来 Acceptance 必测）：
  Employee A（Tenant A）+ 事件被伪造/改路由到 Tenant B → DENY（集合资源解析在 B 下不存在 → DENY）
  resource 属 Tenant A 而 event.tenant_id = B          → DENY（同上 + 引擎 cross-tenant）
  **不得依赖 API path**（Consumer 无 path）⇒ 必须由 tenant 谓词 + 引擎判定完成
⇒ DESIGNABLE（复用既有 tenant 谓词与引擎）
```

## 17. Space Semantics（= NULL）

```text
envelope.space_id 可空；ClaimedEvent.space_id 可为 None；Employee 事件固定 NULL
不得从 Assignment 或其他关联自动推导 space（AI D-P20E-DES-11「No Cascade」+ 本批仅 Employee）
Consumer 侧不得因 space_id=NULL 而跳过租户校验（租户校验独立于 space）
⇒ PROVEN（无冲突）
```

## 18. Subject Semantics（= NULL）

```text
实测：CLAIM_SQL 的 RETURNING 列表**不包含** subject_type/subject_id；ClaimedEvent 亦无这两个字段
⇒ 现有 Consumer 基础设施**完全不依赖** subject ⇒ AI 冻结的 subject=NULL **兼容，无冲突**
若未来 handler 需要 Event-level subject ⇒ 由 AI 明确留待新的 Human Decision（本轮不得引入 COMPANY_EMPLOYEE）
⇒ PROVEN（兼容）
```

## 19. Payload Validation

```text
实测：`TERMINAL_REASON_MALFORMED_PAYLOAD = "malformed_payload"` **仅定义与导出，生产代码无任何使用点**
      （全仓非测试代码检索 malformed_payload → 仅 kernel.py 定义与 __init__ 导出）
结论：现有 Consumer 内核**没有 payload 白名单校验的执行位置**；handler 收到的 payload 为原样 dict
未来测试四类（设计）：missing required / unknown field / forbidden secret field / wrong type
可行落点（设计，不实现）：(a) 未来 handler 内自校验；(b) 内核增加校验点（**P15 冻结代码 ⇒ 需新授权**）
⇒ **F-P20E-QUAL-002（BLOCKING for Handler Qualification）**：当前无法产生"payload 非法 → malformed_payload 终态"
   的资格化证据；须由 Human 决定落点（handler 内校验 vs 内核扩展）
```

## 20. Event-Specific Semantics（employee.updated 漂移风险最高）

```text
实测 use case 边界（互相独立、无交叉）：
  update_employee      → 仅 display_name / title（mutable profile）
  suspend_employee     → status active→suspended（专用路径）
  terminate_employee   → status →terminated（专用路径）
⇒ 服务层已天然满足 AI 的互斥要求：suspend/terminate 不会走 update 路径
未来 Acceptance 断言（设计）：
  PATCH ordinary field → employee.updated = 1（且 suspended/terminated = 0）
  suspend             → employee.suspended = 1（且 employee.updated = 0）
  terminate           → employee.terminated = 1（且 employee.updated = 0）
仍需裁定（AI 遗留）：update 是否覆盖 user_id 绑定/解绑 —— 当前 V1 **无 bind 用例**（未实现），
  故 Batch 1 `changed_fields` 实际只可能出现 display_name / title ⇒ 无漂移
⇒ DESIGNABLE（服务层边界 PROVEN；事件发射未实现）
```

## 21. Idempotency

```text
四层区分（不得互相替代）：Producer idempotency · Event persistence idempotency ·
                          Handler idempotency · Business idempotency
| Event | 凭证（AI 词表） | 依据的不变量 | 重复投递测试（设计） |
| employee.created | schema_guaranteed | uq_company_employees_no (tenant_id, employee_no) | same event_id 重放：handler 判定已存在且等价即成功，不产生第二次业务副作用 |
| employee.updated | naturally_idempotent | 目标状态幂等（display_name/title 同值） | 同值重复应用 → 无额外副作用 |
| employee.suspended | naturally_idempotent | 条件更新 expect='active'（重复 suspend 无副作用） | 第二次投递 → 状态不变、无审计/业务变化 |
| employee.terminated | naturally_idempotent | 终态（重复终止被拒） | 第二次投递 → 状态不变 |
明确否定："UUID 唯一" 与 "DB 有唯一键" **都不自动构成** Event-level 幂等证明；
  必须由 handler 逻辑显式处理重复投递（未来实现 + Acceptance 证明）。
⇒ 全部 DESIGNABLE；**当前 Qualification = NOT YET COMPLETE**
```

## 22. Audit / Event Atomicity（Proof Plan）

```text
成功路径：Business row + Audit row + Event row 三者同事务提交（同一 session）
提交前失败：三者全部回滚（无残留）
事件写入失败：Business + Audit 一起回滚（不得 business success + event missing）
审计写入失败：Business + Event 一起回滚（现状：_audit 抛 AUDIT_UNAVAILABLE → 事务失败；已由 Domain 轮验收证明）
本轮仅设计测试方法，不操作正式 DB（测试须在一次性隔离库执行并清理）
⇒ DESIGNABLE（事务边界 PROVEN · 事件写入未实现）
```

## 23. Failure Injection Design（未来受控测试）

```text
注入点（设计）：① event insert 失败（如违反 ck_events_* 约束）② audit insert 失败
  ③ authorization denial ④ resource projection 缺失 ⑤ tenant mismatch
  ⑥ serialization failure（并发争用）⑦ handler 抛 retryable / non-retryable
每项断言：无部分提交（业务/审计/事件三者一致缺失或一致存在）
非重试类别（既有）：authorization / authentication / security_boundary / validation / configuration
可重试类别（既有）：connection / persistence
⇒ 设计完成；执行属未来 Acceptance（本轮不注入生产逻辑）
```

## 24. Retry / Lease

```text
实测冻结值：MAX_ATTEMPTS=10 · backoff 5/10/20/40/80/160/320/600/600（无 jitter）· lease=120s ·
            heartbeat=40s · batch≤10 · concurrency=4 · worker_processes=1
Handler 边界（实测）：handler 在 `_execute` 中被直接调用（`handler(event)`），**运行于 claim 事务之外**
  （worker.py 注释：「The handler runs outside any claim transaction」）⇒ Handler 必须自行管理其业务事务
Handler 禁止：自行 retry / sleep / backoff / 修改 attempts / 派生 worker（一律由既有 Consumer 管理）
失败分类：retryable → COMPLETE_PENDING（尝试次数+1 + 退避）；non-retryable → COMPLETE_DEAD（last_error）
⇒ DESIGNABLE（规则清晰 · 不得新增 Company 专属重试语义）
```

## 25. Handler Qualification（含结构性阻断）

```text
F-P20E-QUAL-001（BLOCKING）：
  `EventHandlerSpec` 字段 = {event_type, has_producer_evidence, has_authorization_semantics,
   has_acceptance_coverage, idempotency}；**没有 handler 字段**，而 worker 以
   `getattr(spec, "handler", None)` 读取 → 恒为 None → `_finalize_dead(event, "handler_not_bound")`。
  ⇒ 现有 P15 内核**不存在可调用 handler 的绑定机制**；注册任何 spec 都只会让事件终态死亡。
  P15 代码属冻结范围（本轮禁改）⇒ 需 Human Decision（是否授权扩展内核 handler 绑定）。

F-P20E-QUAL-003（NOT YET QUALIFIABLE）：
  平台内**不存在** Employee 事件的下游业务消费用例（无订阅者、无业务 Side Effect 定义）。
  ⇒ 不得为"让事件跑通"虚构 handler；Handler Qualification = BLOCKED，直到出现真实业务消费需求。

（若未来提供 handler，其最低资格标准见 AI.6 与本报告 §15/§16/§21/§24：
  known producer · frozen event_type · schema_version=1 · consumer re-authorization · tenant 校验 ·
  resource 解析 · 幂等证明 · 生命周期处理 · 失败映射 · P15 兼容 · 验收覆盖）
当前：Qualified Handler = 0
```

## 26. Producer / Handler Readiness

```text
Producer Readiness：
  real production path      = PROVEN（11 条 Company 路由 + 11 个用例 · 已验收）
  real USER actor           = PROVEN（authenticate_actor → actor_id 显式贯穿）
  canonical authorization   = PROVEN（_authorize 首步 · fail-closed）
  tenant semantics          = PROVEN（path tenant + active 校验）
  space = NULL              = PROVEN（Employee 无 space 语义）
  resource identity         = DESIGNABLE（集合资源解析已存在）
  business+audit+event 原子  = DESIGNABLE（同一事务可承载 · 事件写入未实现）
  payload whitelist         = DESIGNABLE（字段可取自已实现的用例参数/结果）
  event identity            = PROVEN（UUIDv7 机制）· 生成点 = DESIGNABLE
  ⇒ Producer = 0（未实现）；**就绪度 = DESIGNABLE（无权限/事务/身份阻断）**

Handler Readiness：
  real registered handler   = **BLOCKED**（F-P20E-QUAL-001：内核无 handler 绑定字段）
  payload validation point  = **BLOCKED**（F-P20E-QUAL-002：malformed_payload 无使用点）
  business consumer purpose = **MISSING**（F-P20E-QUAL-003：无下游消费用例）
  consumer re-authorization = DESIGNABLE（引擎可重建 USER 主体）
  resource resolution       = DESIGNABLE（集合资源映射）
  idempotency proof         = DESIGNABLE（词表可用 · 需实现与验证）
  ⇒ Qualified Handler = 0；**就绪度 = BLOCKED / NOT YET QUALIFIABLE**
```

## 27. Implementation Map（未来变更面 · 仅映射，不实施）

| Component | Expected Future Change | Existing Boundary | Needs Code? | Needs Schema? | Needs New Decision? |
| --- | --- | --- | --- | --- | --- |
| Company Service | producer hook（同一事务内插入事件） | services/company/use_cases.py | YES | NO | NO（AI 已冻结规则） |
| Transaction layer | 事件写入复用既有 with 块 | RuntimeDatabase.transaction() | NO（无需改动） | NO | NO |
| Audit | 保持同事务 | use_cases.py::_audit | NO | NO | NO |
| Event persistence | INSERT INTO public.events | 父表 + 当月分区 + uap_runtime INSERT | YES | NO | NO |
| Actor carrier | 复用 actor_id 参数 | apps/api + use_cases | NO | NO | NO |
| Event payload | 按 AI 白名单组装 | payload jsonb | YES | NO | NO |
| Consumer actor resolution | 由 event.actor_id 重建 USER Subject | services/authorization/subjects.py | YES（handler 内） | NO | NO |
| Authorization | 复用唯一引擎 | services/authorization | NO | NO | NO |
| Resource resolver | 集合资源映射（tenant+type→collection id） | services/company/projection.py + resources.py | YES（handler 内） | NO | NO |
| **Handler binding** | **内核需支持 handler callable** | services/consumer/kernel.py（P15 冻结） | **YES** | NO | **YES（F-P20E-QUAL-001）** |
| **Payload validation** | 校验落点（handler 内 or 内核） | kernel/worker（P15 冻结） | **YES** | NO | **YES（F-P20E-QUAL-002）** |
| Handler business purpose | 需真实下游消费需求 | — | YES | NO | **YES（F-P20E-QUAL-003）** |
| Allowlist | 保持 EMPTY 直至 Activation Gate | production_allowlist() | NO | NO | NO（Activation 未授权） |
| Worker | 未授权启动 | apps/worker/main.py | NO | NO | NO |

## 28. Findings

```text
F-P20E-QUAL-001【BLOCKING（Handler Qualification）】
  Problem：EventHandlerSpec 无 handler 字段，worker 读取恒为 None ⇒ 任何 allowlist 条目都会
           `handler_not_bound` 终态；内核不存在绑定可调用 handler 的机制。
  Existing Authority：P15 冻结内核（services/consumer/kernel.py）+ AI（Handler Qualification 要求）
  Recommended Resolution：由 Human 授权扩展内核 handler 绑定（属 P15 变更，需独立决策与回归）
  Impact：Handler 无法被执行 ⇒ Handler Qualification 不可完成；Producer 可先行实现（无影响）
  Requires Schema? NO · Requires Code? YES（P15 内核）· Requires Human Decision? YES

F-P20E-QUAL-002【BLOCKING（Handler Qualification）】
  Problem：`malformed_payload` 仅定义未使用 ⇒ payload 白名单校验无执行位置。
  Existing Authority：P15 内核 + AI D-P20E-DES-03（payload 白名单为契约强制）
  Recommended Resolution：二选一并由 Human 裁定：(a) handler 内自校验（无需改内核）
          (b) 内核增加校验点（P15 变更）—— 两者都必须能产生 malformed_payload 终态证据
  Impact：无法证明"非法 payload → 终态"；payload 合规性依赖 handler 实现质量
  Requires Schema? NO · Requires Code? YES · Requires Human Decision? YES

F-P20E-QUAL-003【NOT YET QUALIFIABLE（Handler）】
  Problem：平台内无 Employee 事件的下游业务消费用例（无订阅者/无 Side Effect 定义）。
  Existing Authority：AI（不得虚构 handler）+ AGENTS.md（不得为通过而制造证据）
  Recommended Resolution：在出现真实业务消费需求前，保持 Handler Qualification = BLOCKED；
          Producer 侧可独立推进（其资格不依赖下游）
  Impact：Batch 1 即使实现 producer 也只能写入 events 并停留在 pending（不可消费）
  Requires Schema? NO · Requires Code? NO（需业务需求）· Requires Human Decision? YES

OBSERVATION：O-P20E-Q1 分区维护（2026-11 及以后分区不存在 · P10-D10 手工运维）——激活前需运维流程
OBSERVATION：O-P20E-Q2 handler 运行于 claim 事务之外（worker 注释明示）⇒ handler 必须自管业务事务
（既有 O-1 / O-2 保留，不因本轮修复）
系统级 BLOCKING：无（基线未变 · 无意外实现 · allowlist EMPTY · 无 schema/权限变更）
```

## 29. Acceptance Matrix

| Area | employee.created | employee.updated | employee.suspended | employee.terminated |
| --- | --- | --- | --- | --- |
| Producer path | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Actor propagation | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Tenant | PROVEN | PROVEN | PROVEN | PROVEN |
| Space | PROVEN | PROVEN | PROVEN | PROVEN |
| Resource | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Producer Auth | PROVEN | PROVEN | PROVEN | PROVEN |
| Transaction Atomicity | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Audit Atomicity | PROVEN（现状同事务） | PROVEN | PROVEN | PROVEN |
| Event Persistence | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Consumer Actor | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Consumer Re-Auth | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Resource Re-resolution | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Lifecycle | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Idempotency | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Payload | HUMAN DECISION（校验落点） | HUMAN DECISION | HUMAN DECISION | HUMAN DECISION |
| Failure | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Retry | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Handler | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Security Negative | DESIGNABLE | DESIGNABLE | DESIGNABLE | DESIGNABLE |
| Acceptance Evidence | MISSING | MISSING | MISSING | MISSING |

```text
（PROVEN = 已由现有实现/验收证明；DESIGNABLE = 有明确路径未实现/未证明；MISSING = 尚不存在；
  BLOCKED = 现存结构阻断；HUMAN DECISION = 需裁定。禁止使用 PASS 伪装未完成证据。）
```

## 30. Future Test Matrix（设计 · 本轮不执行）

```text
Producer      ：create → created；ordinary update → updated；suspend → suspended only；
                terminate → terminated only（互斥断言：updated 计数为 0）
Authorization ：no permission → deny；unauthenticated → deny；cross tenant → deny；
                projection missing → deny
Actor         ：exact USER preserved；no worker substitution；no admin fallback
Transaction   ：all commit；all rollback；event failure rollback；audit failure rollback
Consumer      ：original actor authorized → continue；original actor unauthorized → deny；
                worker privileged only → deny；resource projection missing → deny；tenant mismatch → deny
Idempotency   ：duplicate delivery；retry after failure；same event_id replay
Security      ：secret payload rejected；SQL/stack leakage absent；forged tenant denied；
                forged resource denied
执行约束      ：仅显式选择的测试文件；禁止 broad sweep；一次性隔离库 + 事后清理；
                uap_b1_test 与 formal uap 必须证明未变
```

## 31. Human Decision Requirements

| ID | 议题 | 状态 | 说明 |
| --- | --- | --- | --- |
| HD-Q-01 | Handler 绑定机制（内核扩展） | **NEW（BLOCKING）** | F-P20E-QUAL-001 · 属 P15 变更 |
| HD-Q-02 | Payload 校验落点（handler 内 vs 内核） | **NEW（BLOCKING）** | F-P20E-QUAL-002 |
| HD-Q-03 | 是否存在真实下游消费需求（Handler 业务目的） | **NEW（BLOCKING）** | F-P20E-QUAL-003 |
| HD-Q-04 | 分区维护流程责任（2026-11+） | **NEW（运维）** | O-P20E-Q1 |
| HD-Q-05 | Producer Implementation 授权（若继续推进） | **NEW** | 需 Implementation/Acceptance Gate |
| — | Actor=USER / Space=NULL / Subject=NULL / payload resource identity / consumer re-auth / 同事务 / 无新权限 / 无 dedup / 无全局顺序 | **ALREADY FROZEN BY AI** | 不重复裁定 |

## 32. Final Qualification Verdict

```text
P20 EVENT PRODUCER / HANDLER QUALIFICATION PREP = PASS

Producer Readiness:          DESIGNABLE（载体/权限/事务均无阻断 · 缺事件写入代码）
Handler Readiness:           BLOCKED / NOT YET QUALIFIABLE
Transaction Atomicity:       DESIGNABLE
Actor Propagation:           DESIGNABLE（载体 PROVEN）
Consumer Re-Authorization:   DESIGNABLE
Resource Resolution:         DESIGNABLE
Idempotency:                 DESIGNABLE
Security:                    无泄露面（payload 白名单已冻结）；负向矩阵设计完成；
                             校验落点待裁（HD-Q-02）

New Human Decisions:         HD-Q-01（handler 绑定）· HD-Q-02（payload 校验落点）·
                             HD-Q-03（下游消费需求）· HD-Q-04（分区运维）· HD-Q-05（实现授权）

Producer:                    0
Qualified Handler:           0
Production Allowlist:        EMPTY
Production Event:            NOT AUTHORIZED
Worker:                      NOT AUTHORIZED
Implementation:              NOT AUTHORIZED
Migration:                   NOT AUTHORIZED

Commit: NO   Tag: NO   Push: NO
HARD STOP: ACTIVE
```

```text
边界复述：证明"怎么实现" ≠ 现在实现；证明"可以资格化" ≠ 已 Qualified；
Contract Frozen ≠ Production Authorized；Producer/Handler Design ≠ Active ≠ Registered；
Qualification PASS ≠ Activation PASS。
下一阶段若进入 P20 EVENT PRODUCER / HANDLER IMPLEMENTATION，必须等待新的明确 Human Authorization。
```

## 33. Hard Stop

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0
0019 / 0020 sha256 未变 · No 0021 · allowlist EMPTY · Producer 0 · Qualified Handler 0 ·
Worker NOT AUTHORIZED · events 行数 0 · uap_b1_test 与 formal uap 未变（只读验证）
本轮仓库写入 = 仅本报告 · 未修改 PDL · 未实现 producer/handler · 未注册 · 未激活 ·
未创建 event 行 · 未新增权限/表/migration · 未 commit / tag / push

HARD STOP = ACTIVE
```

**END OF P20 EVENT PRODUCER / HANDLER QUALIFICATION PREP REPORT（Producer = DESIGNABLE（uap_runtime 已具 events INSERT · 同事务可承载）· Consumer 重建 USER 主体可行 · subject=NULL 兼容 · 两处结构性阻断 F-P20E-QUAL-001/002 + 无下游消费用例 F-P20E-QUAL-003 · 4 项新 Human Decision · 未实现 / 未激活 / 未 commit；2026-10-04）**
