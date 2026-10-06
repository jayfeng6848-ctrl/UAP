# P20 EVENT DESIGN / QUALIFICATION PREP REPORT

```text
阶段     = P20 EVENT DESIGN / QUALIFICATION PREP（Design / Qualification PREP · 非 Contract Freeze · 非实现 · 非激活）
授权依据 = PDL 附录 AH（D-P20E-01…13 = OPTION B · Event Design / Qualification AUTHORIZED）
本轮禁止 = Producer/Handler 实现 · Allowlist 激活 · Worker 激活 · INSERT INTO events ·
           Migration / DDL / DML · Outbox / Dedup / 新表 · 新 permission / authorization engine ·
           Company API/Domain/Service 改动 · P15/P16/P18/P20 既有 schema 改动
仓库写入 = 仅本报告
```

## 1. Executive Summary

```text
结论：7 个 Candidate Event 均已完成逐类型设计分析，并建立了 Producer / Handler 资格标准、
      幂等与生命周期设计、Acceptance Matrix 与 Activation Readiness。

关键发现（设计层）：
  F-P20E-001【Contract Freeze 阻断·非系统阻断】现有 events envelope **没有 resource_type /
             resource_id 列**（实测 0 列）⇒ 资源身份只能进 payload 或需新 schema 决策。
  F-P20E-002【Contract Freeze 阻断·非系统阻断】Company service 的授权主体当前**硬编码
             subject_type="USER"** ⇒ worker/role/agent actor 目前不可达；V1 事件若限定 user actor
             则无冲突，否则需新的授权决策（不得在实现中自行扩展）。
  F-P20E-003【设计阻断】producer 事务内**尚无 event 写入集成**（生产代码 INSERT INTO events = 0），
             属于未来 Producer Implementation requirement，本轮不得实现。

系统状态未改变：Allowlist EMPTY · Producer 0 · Qualified Handler 0 · Worker NOT AUTHORIZED ·
  events 行数 0 · 无 0021 · P20 API/Domain/Service/Authorization 基线未变。

⇒ P20 EVENT DESIGN / QUALIFICATION PREP = PASS（Design / Qualification 完成，供 Human 审阅）
```

## 2. Authority Sources

```text
AGENTS.md（证据优先 · 禁止代填 Human Decision · 禁止 broad test sweep）
PDL 附录 AB（P19 Event Governance · D01–D21）· AC / AD / AE / AF / AG（P20 模块/Schema/OPT-2/Domain/API）
PDL 附录 AH（P20 EVENT DECISION = OPTION B · D-P20E-01…13）
docs/architecture/P20_EVENT_DECISION_PREP_REPORT.md（24 节只读证据）
docs/architecture/P20_COMPANY_API_ACCEPTANCE_REPORT.md（API ACCEPTANCE = PASS）
真实仓库：services/consumer/** · apps/worker/** · services/company/** · domains/company/** ·
          apps/api/** · migrations_alembic/** · tests/**
UAP_PROJECT_MASTER_DOSSIER.md（仅 continuity aid · 非权威）
```

## 3. Baseline Integrity

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（与 P20 API Acceptance / 附录 AH 基线一致）
staged = 0 · 自 release 以来 commit = 0 · tags = 16（未新增）
0019 sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020 sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4（未变）
0021 存在性 = 0 · alembic single head = 0020_p20_company_authorization
⇒ BASELINE: PASS（未触发 BLOCKED）
```

## 4. AH Scope Recovery

```text
Design Scope = 7 项（CANDIDATE = YES · DESIGN SCOPE = YES · PRODUCTION EVENT = NO · ALLOWLIST = NO）
  employee.created · employee.updated · employee.suspended · employee.terminated
  assignment.created · assignment.updated · assignment.ended
排除（无 V1 用例 · 不得扩展）：company_employee.delete · company_employee.admin · company_assignment.delete
AH 冻结且本轮再次确认：Production Event NOT AUTHORIZED · Allowlist EMPTY · Producer 0 ·
  Qualified Handler 0 · Worker NOT AUTHORIZED · Migration NOT AUTHORIZED
```

## 5. Existing Event Infrastructure（实测）

```text
持久化（P10/P15 · 不可改）：public.events（按 occurred_at 月度分区：events_202609 / events_202610）
  envelope 列（22）：id, occurred_at, event_type, schema_version(int NOT NULL), tenant_id(null), space_id(null),
    actor_type(null), actor_id(null), subject_type(null), subject_id(null), payload(jsonb NOT NULL),
    correlation_id(null), causation_id(null), status, worker_id, claimed_at, lease_expires_at,
    attempts(int NOT NULL), next_attempt_at, last_error, delivered_at, created_at
  约束：ck_events_status ∈ {pending,claimed,delivered,dead} · ck_events_attempts ∈ [0,100] ·
        ck_events_event_type ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'（点分小写 · ≥2 段）· PK (id, occurred_at)
  索引：ix_events_dispatch(status, next_attempt_at) WHERE status ∈ {pending,claimed} ·
        ix_events_tenant_type_time(tenant_id, event_type, occurred_at DESC)
内核（services/consumer/kernel.py · 冻结常量）：
  MAX_ATTEMPTS=10 · BACKOFF 5/10/20/40/80/160/320/600/600（无 jitter）· WORKER_PROCESS_COUNT=1 ·
  WORKER_CONCURRENCY=4 · CLAIM_BATCH_SIZE=10 · LEASE=120s · HEARTBEAT=40s
  终态原因 6 类：lease_expired_max_attempts · unsupported_event_type · non_retryable_failure ·
    max_attempts_reached · malformed_payload · authorization_denied
  可重试类别 {connection, persistence} · 不可重试 {authorization, authentication, security_boundary,
    validation, configuration} · 幂等凭证词表 {naturally_idempotent, transactional_key, schema_guaranteed}
注册表：EventAllowlist（CLOSED）· EventHandlerSpec 要求 4 项资格齐备；
  production_allowlist() = EMPTY（services/consumer/kernel.py:124）
Worker：apps/worker/main.py 以 handlers=production_allowlist() 启动；无 Company 引用
Producer：非测试代码 `INSERT INTO events` = 0
测试夹具（非生产 · 允许存在）：tests/integration/test_p10_event_audit_schema.py 直接插入 events
⇒ 结论：P20 Candidate Events **在不修改基础设施的前提下可被表达**（除 §6 标注的 2 项需设计决策）
```

## 6. Envelope Compatibility（字段矩阵 · 以代码/DB 实况为准）

| 指令假定字段 | 真实列/机制 | 判定 | 说明 |
| --- | --- | --- | --- |
| event_id | `id`(uuid) + PK(id, occurred_at) | **REUSE** | event identity = id（P15 冻结） |
| occurred_at | `occurred_at` | **REUSE** | 分区键 · 生产者写入 now() |
| event_type | `event_type` + CHECK 正则（点分小写 ≥2 段） | **REUSE** | 7 个候选名（employee.created 等）**符合**该正则 |
| schema_version | `schema_version` int NOT NULL | **REUSE（值未定）** | 结构已支持；具体版本号 → NEEDS DESIGN DECISION |
| actor | `actor_type` + `actor_id`（另有 `subject_type`/`subject_id`） | **REUSE（映射待定）** | 建议 actor_type='user' · actor_id=users.id；subject_* 语义 → NEEDS DESIGN DECISION |
| tenant_id | `tenant_id`(nullable) | **REUSE** | Company 全部候选均非空（Employee=员工 tenant；Assignment=assignment tenant） |
| space_id | `space_id`(nullable) | **REUSE** | Employee 类 = NULL；Assignment 类 = assignment.space_id |
| resource_type / resource_id | **不存在**（实测列数 0） | **NEEDS DESIGN DECISION** | 只能 (a) 放入 payload 或 (b) 未来 schema 决策新增列；二者均需 Contract Freeze 裁定 |
| payload | `payload` jsonb NOT NULL | **REUSE** | 白名单未冻结 → NEEDS DESIGN DECISION |
| correlation_id | `correlation_id`(nullable) | **REUSE（建议携带）** | 现有 API 已有 `x-correlation-id` carrier |
| causation_id | `causation_id`(nullable) | **NOT APPLICABLE（V1）** | 无上游事件链 |
| status / attempts / next_attempt_at / last_error / worker_id / claimed_at / lease_expires_at / delivered_at | 消费端字段 | **REUSE（消费端所有）** | 生产者仅需 status='pending' · attempts=0 |

## 7. Employee Event Design（Design Cards · 未冻结）

```text
# employee.created
1  候选名        = employee.created（PROPOSED）
2  业务触发      = create_employee 成功提交（新员工行落库）
3  Producer 边界 = services/company/use_cases.py::create_employee（同一事务内）
4  Actor         = 认证用户（actor_id = users.id）· 现 carrier：apps/api/routes/company.py → actor.user_id
5  Tenant        = employee.tenant_id（用例已校验 tenant active）
6  Space         = NULL
7  Resource Type = company_employee（collection resource）
8  Resource Id   = 集合资源 id（resources.id · 缺投影 = DENY · 无自愈）
9  Event Identity= events.id（uuid）
10 Schema Version= 未定（NEEDS DESIGN DECISION）
11 Payload 白名单= PROPOSED：employee_id · employee_no · display_name? · status · user_id?（最小业务数据）
12 禁止 Payload  = password/token/bearer/API key/secret 明文/SQL/stack/DSN/内部安全细节
13 Producer 授权 = company_employee.create（resource_type=company_employee · 集合资源 · tenant 上下文）
14 Consumer 授权 = 必须重新 canonical 授权（不得信 Event）
15 幂等依据      = PROPOSED schema_guaranteed（uq_company_employees_no (tenant_id, employee_no)）+ 一致重放
16 生命周期门禁  = tenant active（现有实现）；employee 新建为 active
17 事务边界      = 现有 RuntimeDatabase.transaction()（事件写入集成 = F-P20E-003 未来实现项）
18 审计关系      = 同事务 audit_logs（company_employee.create）；audit ≠ event
19 Handler 职责  = PROPOSED：下游同步/通知（未定义 · 属 Contract Freeze）
20 失败语义      = 沿用 P15（authorization_denied 为终态 · connection/persistence 可重试）
21 重试兼容      = 兼容（无自定义退避）
22 验收证据要求  = producer 证据 · payload 白名单 · 幂等证明 · 授权证明 · 租户证明 · 事件身份证明
23 Activation    = NOT ACTIVATABLE（缺 producer/handler/契约/激活决策）
24 待裁 Human    = event_type 命名 · schema_version · payload 字段 · envelope 映射 · 事务集成

# employee.updated
2  业务触发      = update_employee 成功提交（display_name / title 变更）
15 幂等依据      = PROPOSED naturally_idempotent（同一目标状态重复应用等价）
11 Payload 白名单= PROPOSED：employee_id · changed_fields（字段名白名单）· 可选 from/to 值
其他字段同 employee.created（除 §7.2 提出的 open question：generic update vs business transition）
24 待裁 Human    = 追加"什么变化才算 updated"（含是否含 user_id 绑定/解绑 → 见 F-P20E-002）

# employee.suspended
2  业务触发      = suspend_employee 成功（active → suspended）
15 幂等依据      = PROPOSED naturally_idempotent（条件更新 + rowcount；重复 suspend 无副作用）
11 Payload 白名单= PROPOSED：employee_id · from_status='active' · to_status='suspended'
设计原则        = **仅成功转换后产生事件**（不产生"attempted suspend"），与现有 service 语义一致

# employee.terminated
2  业务触发      = terminate_employee 成功（active|suspended → terminated）
15 幂等依据      = PROPOSED naturally_idempotent（终止为终态 · 重复终止被拒 409）
11 Payload 白名单= PROPOSED：employee_id · from_status · to_status='terminated' · terminated_at
边界            = 不得引入 assignment cascade / auto-end / space cascade（AH D-P20E-10 明令）
```

## 8. Assignment Event Design（Design Cards · 未冻结）

```text
# assignment.created
2  业务触发      = create_assignment 成功（active 分配落库）
5  Tenant        = assignment.tenant_id（= employee.tenant_id = space.tenant_id · DB 触发器强制）
6  Space         = assignment.space_id
7  Resource Type = company_assignment（collection resource）
11 Payload 白名单= PROPOSED：assignment_id · employee_id · space_id · assignment_role · status
13 Producer 授权 = company_assignment.create
15 幂等依据      = PROPOSED schema_guaranteed（uq_company_assignments_active (employee_id, space_id)
                   WHERE ended_at IS NULL）+ 一致重放
前置证明（已实现）：employee 存在且同租户 · space 存在且同租户且 active · tenant active

# assignment.updated
2  业务触发      = update_assignment 成功（assignment_role 变更）
11 Payload 白名单= PROPOSED：assignment_id · employee_id · space_id · from_role · to_role
15 幂等依据      = PROPOSED naturally_idempotent（同一目标 role 重复应用等价）
边界（必须由 Contract Freeze 裁定）：`.updated` 与 `.ended` 的重叠边界 ——
   现状：role 变更走 update_assignment；结束走 end_assignment（两者互斥）
   规则建议：`status` 变化 → `.ended`；仅 `assignment_role` 变化 → `.updated`；
   **不得对同一次变更同时发两个事件**（AH：不得自行解决）

# assignment.ended
2  业务触发      = end_assignment 成功（active → ended · ended_at 落库）
11 Payload 白名单= PROPOSED：assignment_id · employee_id · space_id · from_status='active' ·
                   to_status='ended' · ended_at
15 幂等依据      = PROPOSED naturally_idempotent（ended 为终态 · 重复 end 被拒 409）
语义            = 状态变化事件，**不是物理删除**（Company 无 physical delete path）
```

## 9. Actor

```text
AH 冻结：actor = 真实经过认证的原始业务主体（user / role / agent），依生产请求的 authenticated subject。
实测 carrier：apps/api/routes/company.py::_actor → services.use_cases.authenticate_actor(bearer session)
              → actor.user_id → 用例参数 actor_id
实测限制（F-P20E-002）：services/company/use_cases.py::_authorize **硬编码** subject_type="USER"
              （第 120 行）⇒ 当前 Company 用例只可能以 USER 主体授权。
含义：V1 事件 actor 若限定为 user，则与现有实现一致；若未来需要 role / agent actor，
      必须先有新的授权决策 + service 变更（本轮不得实现）。
禁止（沿用 AH）：worker actor · DB principal · platform_admin/bootstrap/migrator 兜底。
```

## 10. Tenant

```text
Employee 类：tenant_id = employee.tenant_id（NOT NULL · 用例已校验 tenant active）
Assignment 类：tenant_id = assignment.tenant_id（= employee.tenant_id = space.tenant_id）
Consumer 侧关键问题（Qualification Decision）：**是否可以相信 envelope.tenant_id？**
  推荐设计：Consumer 必须将 envelope 的 tenant_id 作为**上下文提示**，但仍以
  canonical 授权 + 业务资源解析（tenant 谓词）重新确认；不得仅凭 envelope 决定数据访问范围。
  该机制属 Contract Freeze 决策（D-P20E-DES-06）。
```

## 11. Space

```text
Employee 类：space_id = NULL（V1 员工无直接 space 归属）
Assignment 类：space_id = assignment.space_id（显式）
结构一致性由 DB 触发器 tg_company_assignment_tenant_consistency 强制；
Event 不得重新定义 Company 关系模型，也不得通过 payload 绕过 tenant isolation。
```

## 12. Resource

```text
Company 现有投影：tenant 级集合资源（company_employee / company_assignment）·
  missing projection = DENY · no self-healing · 无自动 provisioning
事件不得：create resource / repair resource / bypass resource check / event-triggered provisioning
Consumer 若需资源授权：必须复用现有 AuthorizationService 与集合资源（不得建第二套授权）。
envelope 限制：events 表无 resource_type/resource_id 列 ⇒ 资源身份需 (a) payload 携带或
  (b) 未来 schema 决策（F-P20E-001 · 本轮不实现）。
```

## 13. Authorization

```text
Producer 侧（逐事件 · 以实际 use case 为准 · 与 AH/AG 一致）：
  employee.created → company_employee.create ；employee.updated/.suspended/.terminated → …update
  assignment.created → company_assignment.create ；assignment.updated/.ended → …update
  资源目标 = tenant 级集合资源 · actor = 认证用户 · tenant 上下文来自 path
不得新增：company_employee.event_publish / event_publish 类新权限（AH §19 明令）
Event 本身不得作为授权凭证。
```

## 14. Consumer Re-Authorization

```text
AH 冻结：Consumer 必须重新授权。设计问题与建议方向（均属 Contract Freeze 决策）：
  Q1 Consumer 以谁为 actor？        → 建议保留 envelope 的原始 subject（user）作为 actor 输入；
                                        不得用 worker/系统主体替代（AH D-P20E-05）
  Q2 使用什么 tenant context？       → envelope.tenant_id 作为上下文，但必须经 canonical 授权校验
  Q3 原 actor 已失去权限？           → 授权 DENY ⇒ 终态 authorization_denied（不可重试）
  Q4 tenant 已 inactive？            → DENY（对齐 P18-D14）⇒ terminal（不可重试）
  Q5 space 已 inactive？             → 同上（Assignment 类事件）
  Q6 resource projection 消失？      → DENY（RESOURCE_NOT_PROVISIONED 同族）⇒ terminal
禁止：trust event as authorization · platform_admin fallback · system principal · 跳过 AuthorizationService
```

## 15. Idempotency

```text
event_id = event identity（P15 冻结）· 凭证词表 {schema_guaranteed, naturally_idempotent, transactional_key}
逐事件分析（PROPOSED · 需在 Contract Freeze 形成逐类型证明）：
  employee.created      → schema_guaranteed：uq_company_employees_no；handler 重复应用需以
                           (tenant_id, employee_no) 为自然键判定"已存在即幂等"
  employee.updated      → naturally_idempotent：目标状态幂等（重复设置同值）
  employee.suspended    → naturally_idempotent：条件更新（expect=active）；重复 suspend 无副作用
  employee.terminated   → naturally_idempotent：终态；重复终止不改变状态
  assignment.created    → schema_guaranteed：uq_company_assignments_active（部分唯一）
  assignment.updated    → naturally_idempotent：同一目标 role 幂等
  assignment.ended      → naturally_idempotent：终态
禁止：新增 dedup 表 / event identity 表 / consumer receipt 表（若未来需要 → 新 Human Decision）
```

## 16. Transaction / Atomicity

| Operation | Business Write | Audit | Event Candidate | Same Transaction Feasibility |
| --- | --- | --- | --- | --- |
| employee.create | INSERT company_employees | audit_logs（同事务 · 已实现） | employee.created | 可设计（同事务 INSERT events）· **当前未集成（F-P20E-003）** |
| employee.update | UPDATE display_name/title | audit_logs（同事务） | employee.updated | 可设计 · 未集成 |
| employee.suspend | UPDATE status（条件） | audit_logs（同事务） | employee.suspended | 可设计 · 未集成 |
| employee.terminate | UPDATE status + terminated_at | audit_logs（同事务） | employee.terminated | 可设计 · 未集成 |
| assignment.create | INSERT company_assignments | audit_logs（同事务） | assignment.created | 可设计 · 未集成 |
| assignment.update | UPDATE assignment_role | audit_logs（同事务） | assignment.updated | 可设计 · 未集成 |
| assignment.end | UPDATE status + ended_at | audit_logs（同事务） | assignment.ended | 可设计 · 未集成 |

```text
结论：现有事务边界（RuntimeDatabase.transaction）**足以承载**原子事件写入，
      但事件写入本身属未来 Producer Implementation requirement（本轮不得实现）。
```

## 17. Audit / Event Boundary

```text
现有：Company 8 条 mutation 动作在**同一逻辑事务**写 audit_logs（已实现并验收）
未来顺序建议（设计）：business mutation → audit（同事务）→ event（同事务）→ COMMIT
铁律：audit_logs ≠ event；不得把 audit_logs 视为 Producer；不得将 audit_logs 改造成
      outbox / event queue / dedup store（AH §13 明令）
```

## 18. Lifecycle

```text
Producer gate（已实现）：tenant active 必需；涉及 space 的用例要求 space active 且同租户
Consumer gate（设计）：必须重新校验 tenant / space / employee / assignment 状态；
  inactive ⇒ DENY（authorization_denied 或同等终态），不得绕过 lifecycle gate
post-event conflict：事件产生合法 ≠ 消费时仍合法 ⇒ 设计上必须 revalidation（§14 Q3–Q6）
Company V1 无自动级联：不得因事件引入 assignment/employee/space cascade（AH D-P20E-10）
```

## 19. Payload

```text
PROPOSED 白名单（逐事件见 §7/§8）· 分类：
  mandatory = 对象 id（employee_id / assignment_id）+ 状态字段（status / from/to）
  optional  = display_name? · user_id? · assignment_role? · 时间戳（terminated_at / ended_at）
  derived   = occurred_at · event_id · correlation_id（envelope 承载，不进 payload）
  forbidden = password · token · bearer · API key · secret 明文 · secret_ref 值 · SQL · stack ·
              internal exception · database URL · connection string · 内部安全细节
原则：最小必要业务数据；不得为"以后方便"塞入整行字段（附录 AG：Schema ≠ API Contract）
```

## 20. Versioning

```text
要求：每个正式事件必须显式 event_type + schema_version（AH §5 冻结 · events.schema_version 已支持 int）
未定（Contract Freeze 决策）：起始版本号、兼容规则（新增可选字段 = 兼容？语义变更 = 新版本？）、
  是否允许多版本并存于同一 event_type。
本轮不注册任何 production schema、不创建 migration。
```

## 21. Producer Qualification Model

```text
进入 Implementation / Acceptance 的前置（全部需可证明）：
  real production business path · successful business mutation · authenticated actor available ·
  authorization passed（canonical）· tenant/space established · audit recorded ·
  event atomically persisted · event identity established · payload whitelist enforced ·
  event contract frozen · acceptance evidence available
明确否定（AH 已冻结）：
  "API endpoint exists" ≠ qualified producer · "repository write exists" ≠ qualified producer
当前：Producer = 0（全部 7 项）
```

## 22. Handler Qualification Model

```text
每个未来 Qualified Handler 的最低标准：
  known producer · known event type · known schema version · actor semantics ·
  authorization semantics（consumer 侧重新授权）· tenant/space semantics · idempotency proof ·
  lifecycle behavior · failure mapping（P15 分类）· acceptance tests
Handler 职责（PROPOSED · 逐事件）：employee.* → 下游读取方/协作同步；assignment.* → 组织视图同步
  说明：当前**尚不能**从仓库证据推导出具体业务职责（无下游订阅者）⇒ 每项标记为
  QUALIFICATION BLOCKED（阻塞原因 = 无已知下游消费者/职责未定义）。
不计入 Qualified：placeholder · TODO · mock-only · test-only · unregistered · unused helper
当前：Qualified Handler = 0
```

## 23. Acceptance Matrix

| Event | Producer | Handler | Actor | Auth | Tenant | Space | Idempotency | Lifecycle | Payload | Audit | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| employee.created | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN(NULL) | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |
| employee.updated | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN(NULL) | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |
| employee.suspended | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN(NULL) | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |
| employee.terminated | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN(NULL) | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |
| assignment.created | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |
| assignment.updated | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |
| assignment.ended | MISSING | MISSING | PROVEN | PROVEN | PROVEN | PROVEN | DESIGNABLE | DESIGNABLE | HUMAN DECISION | PROVEN | MISSING |

```text
（单元格语义：PROVEN = 已由现有实现/验收证明；DESIGNABLE = 有明确设计路径但未证明；
  MISSING = 尚不存在；HUMAN DECISION = 需裁定；BLOCKED = 当前不可解决。禁止使用 PASS 伪装未证明项。）
```

## 24. Contract Freeze Candidate Decisions

```text
已由 AH/AB 冻结（不得重复制造新决策 · ALREADY FROZEN BY AB/AH）：
  actor 原则（真实认证主体）· tenant/space 归属原则 · canonical authorization 复用 ·
  consumer 必须重新授权 · 幂等证明为激活前置 · 生命周期原则（无自动级联）·
  payload 安全原则（禁用项）· retry/lease 冻结值 · 不新增 permission · 不新增 dedup ·
  不新增表 · Allowlist = EMPTY

尚未冻结（Contract Freeze 需裁定）：
  ① 精确 event_type 命名（现状：候选名；需确认是否采用 employee.* / assignment.* 或 company.* 前缀）
  ② 精确 schema_version 起始值与演进规则
  ③ 精确 payload 字段白名单（逐事件）
  ④ 精确 envelope 映射（尤其 resource identity 放 payload 还是新增列 → F-P20E-001）
  ⑤ producer 事务集成方式（同事务 INSERT events 的具体位置与失败语义）
  ⑥ consumer 重新授权的具体机制（actor 来源、tenant 信任边界）
  ⑦ 幂等证据形式（逐事件以何种凭证落证）
  ⑧ 生命周期拒绝行为的具体失败分类映射
  ⑨ handler 职责（当前无已知下游消费者）
  ⑩ 失败分类映射细节（复用 P15 但需逐事件确认可重试性）
  ⑪ ordering / delivery 假设（事件顺序与重复投递语义）
  ⑫ Contract Freeze 范围（7 项一起 / 分批）
```

## 25. Event Batching Recommendation

```text
建议（仅为 Recommendation · 不冻结）：**Batch 1 = Employee 4 项；Batch 2 = Assignment 3 项**
理由：Employee 类事件语义最简（space_id = NULL · 单一 resource_type · 生命周期简单），
      可作为第一个 Contract Freeze 的模板；Assignment 类涉及 space 语义 + `.updated`/`.ended`
      边界裁定（§8.2），复杂度更高。
风险：分批会让 Assignment 事件的投产时间线延后；若 Human 偏好一次性冻结，则须先解决
      `.updated` vs `.ended` 边界与 space 语义（两者均已在 §8 明示）。
备选：7 项一起进入 Contract Freeze（需同时完成 ⑫ 与 §24 全部未冻结项）。
```

## 26. Blocking / Non-blocking Findings

```text
F-P20E-001【DESIGN BLOCKING（对 Contract Freeze）· 非系统缺陷】
  events envelope 无 resource_type / resource_id 列（实测 0 列）⇒ 资源身份表示方式必须裁定
  （payload 承载 or 新增列 = 未来 schema 决策）。不构成系统 BLOCKED。
F-P20E-002【DESIGN BLOCKING（对 Contract Freeze）· 非系统缺陷】
  Company service 授权主体硬编码 subject_type="USER"（use_cases.py:120）⇒ role/agent actor 不可达；
  V1 事件限定 user actor 则无冲突，否则需新的授权决策。
F-P20E-003【设计阻断（对未来实现）】producer 事务内无 event 写入集成（生产代码 = 0）；
  属未来 Producer Implementation requirement。

O-P20E-001【非阻断】7 项候选的缺口高度同质（缺 producer / handler / 契约 / 激活决策），
  可共用同一 Contract Freeze 模板。
O-P20E-002【非阻断】`assignment.updated` 与 `assignment.ended` 的边界需在 Contract Freeze 明确，
  当前实现下两者互斥（role 变更 vs 状态结束），不存在同一变更双事件的风险。
O-P20E-003【非阻断】events 分区按 occurred_at 月度维护（P10-D10 手工运维，无 scheduler）；
  激活前需评估分区维护责任。
O-P20E-004【非阻断】consumer 侧重新授权会使"消费者身份"成为设计焦点：当前平台无 service/system
  主体（且 AH 禁止新增），因此消费者必须以原始 actor 身份重新授权。

保留既有观察（本轮不修复）：O-1（services/company/use_cases.py 3 处 inline SQL）· O-2（list = limit-only）
未发现任何真正的系统 BLOCKING（无意外事件/producer/handler/worker · allowlist 仍为空 · 无 schema 变更 ·
  P20 API/Domain/Authorization 基线未变）。
```

## 27. Human Decision Options

```text
Option A — 7 个 Candidate 全部进入 Contract Freeze
Option B — 先冻结 Employee 4 项（employee.created / .updated / .suspended / .terminated），Assignment 3 项暂缓
Option C — 先冻结 Assignment 3 项，Employee 暂缓
Option D — 继续保持 Design Only，不进入 Contract Freeze
（以上仅为候选方向；本轮不选择、不冻结）
```

## 28. Final PREP Verdict

```text
P20 EVENT DESIGN / QUALIFICATION PREP = PASS

Design = COMPLETE FOR HUMAN REVIEW
Qualification Design = COMPLETE FOR HUMAN REVIEW

Contract Freeze = NOT YET FROZEN
Producer = 0
Qualified Handler = 0
Production Allowlist = EMPTY
Production Event = NOT AUTHORIZED
Worker = NOT AUTHORIZED
Migration = NOT AUTHORIZED
Implementation = NOT AUTHORIZED

逐事件 Readiness：DESIGNABLE = YES（7/7）· QUALIFIABLE = PARTIAL（设计标准已明确，缺 producer/handler/契约）
                    · ACTIVATABLE = NO（7/7 · 且 AH 未授权生产激活）

Human Decision Requirements（D-P20E-DES-01…12）：
  01 event naming = NEW  02 schema version = NEW  03 payload whitelist = NEW
  04 envelope field mapping = NEW  05 producer transaction atomicity = NEW
  06 consumer re-authorization mechanics = NEW（原则已由 AH 冻结 · 机制未定）
  07 idempotency evidence form = NEW（要求已冻结 · 形式未定）
  08 lifecycle denial behavior = NEW（原则已冻结 · 行为未定）
  09 handler responsibility = NEW  10 failure classification = ALREADY FROZEN BY AB/AH
  11 ordering / delivery assumptions = NEW  12 contract freeze scope = NEW
```

## 29. Hard Stop

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0
0019 / 0020 sha256 未变 · 无 0021 · Allowlist EMPTY · Producer 0 · Qualified Handler 0 ·
Worker NOT AUTHORIZED · production events = 0
常驻库未变：uap_b1_test = 0017_p13_seed（events 0 · company 表 0）· 正式库 uap = 0 public 表
本轮仓库写入 = 仅本报告 · 未实现任何代码 · 未注册 handler · 未激活 allowlist ·
未创建 event 行 · 未 commit / tag / push

HARD STOP = ACTIVE
下一步：Human 审阅本报告 → 决定是否启动 P20 EVENT CONTRACT FREEZE（Option A/B/C/D）
```

**END OF P20 EVENT DESIGN / QUALIFICATION PREP REPORT（7 项候选逐类型设计完成 · Producer/Handler 资格标准建立 · Acceptance Matrix 与 Activation Readiness 就绪 · 3 项设计层发现 F-P20E-001…003 · 4 项非阻断观察 · 未实现 / 未注册 / 未激活 / 未 commit；2026-10-04）**
