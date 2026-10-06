# P20 EVENT CONTRACT FREEZE — BATCH 1 EMPLOYEE（PREP / HUMAN DECISION SUPPORT）

```text
阶段     = Contract Design / Freeze Preparation / Human Decision Support（**非 Contract Freeze 生效 · 非实现**）
输入     = 附录 AH（P20 EVENT DECISION = OPTION B）+ P20 EVENT DESIGN / QUALIFICATION PREP（PASS）
本批范围 = employee.created · employee.updated · employee.suspended · employee.terminated（4 项）
非本批   = assignment.created · assignment.updated · assignment.ended（保持 CANDIDATE / DESIGN COMPLETE /
           NOT CONTRACT-FROZEN / NOT PRODUCTION）
仓库写入 = 仅本报告（**不改 PDL** · 不实现 · 不注册 · 不激活）
```

## 1. Executive Summary

```text
Layer A（Recommended Contract）已为 4 个 Employee 事件完成可冻结的契约提案：
  event_type / schema_version / actor / tenant / space / resource identity / subject identity /
  payload 白名单 / correlation / causation / idempotency / authorization / lifecycle / audit /
  transaction atomicity / failure semantics / ordering / handler responsibility /
  acceptance gate / activation gate

三项既有阻断均已给出可执行解决路径（§21）：
  F-P20E-001（envelope 无 resource_type/resource_id）→ payload 承载（**无需 schema 变更**）
  F-P20E-002（Company service subject_type 硬编码 USER）→ Batch 1 冻结 actor = USER（不新增主体）
  F-P20E-003（producer 无 event 写入集成）→ 冻结同事务原子规则（未来实现项）

Layer B（Human Decision Items）D-P20E-DES-01…13 已列明；其中多项标记 ALREADY FROZEN BY AB/AH，
不重复制造决策。

当前状态未改变：Allowlist EMPTY · Producer 0 · Qualified Handler 0 · Worker NOT AUTHORIZED ·
  events 0 · 无 0021 · P20 API/Domain/Service/Authorization 基线未变。

⇒ P20 EVENT CONTRACT FREEZE BATCH 1 PREP = PASS
   Contract = READY FOR HUMAN FREEZE（尚未冻结）
```

## 2. Authority Sources

```text
AGENTS.md（证据优先 · 禁止代填 Human Decision）
PDL 附录 AB（P19 Governance）· AC / AD / AE / AF / AG（P20 模块/Schema/OPT-2/Domain/API）
     · AH（P20 EVENT DECISION = OPTION B · D-P20E-01…13）
docs/architecture/P20_EVENT_DECISION_PREP_REPORT.md（24 节只读证据）
docs/architecture/P20_EVENT_DESIGN_QUALIFICATION_PREP_REPORT.md（29 节设计/资格证据）
docs/architecture/P20_COMPANY_API_ACCEPTANCE_REPORT.md（API ACCEPTANCE = PASS）
真实实现：core/event/interfaces.py · services/consumer/{kernel,claim,worker}.py · apps/worker/main.py ·
         services/company/** · domains/company/** · apps/api/** · migrations_alembic/** · tests/**
```

## 3. Baseline Integrity

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（与附录 AH 基线一致）· staged = 0 · tags = 16（未新增）
0019 sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020 sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4（未变）
No 0021 · alembic single head = 0020_p20_company_authorization
Allowlist EMPTY（0 entries）· Producer 0 · Handler 0 · Worker 0/NOT AUTHORIZED · events 行数 0
常驻库：uap_b1_test = 0017_p13_seed（company 表 0 · events 0）· 正式库 uap = 0 public 表
⇒ BASELINE: PASS（未触发 BLOCKED）
```

## 4. ALREADY FROZEN BY AB/AH（本轮不得重复决策）

```text
ALREADY FROZEN BY AH：actor 原则（真实认证原始主体）· tenant/space 归属原则 ·
  canonical authorization 复用 · **Consumer 必须重新授权** · 幂等证明为激活前置 ·
  生命周期原则（无自动级联）· payload 安全禁用项 · retry/lease 冻结值 ·
  不新增 permission · 不新增 dedup/identity 表 · Allowlist EMPTY · Production Activation NOT AUTHORIZED
ALREADY FROZEN BY AB：P19-D02 逐类型激活 · D03 producer 资格 · D04 handler 资格 ·
  D05 actor · D06 authorization · D07 tenant/space · D08 lifecycle · D09 idempotency ·
  D10 retry/lease · D11 versioning 须显式 · D12 audit≠event · D15 payload 安全 · D16–D18 失败/可观测/首激活门
⇒ 本报告只在"新增可冻结细节"层面提出 D-P20E-DES-*（§24）
```

## 5. Existing Envelope & Consumer Infrastructure（实测事实）

```text
Envelope（public.events · P10/P15 冻结 · 不可改）：
  id(uuid) · occurred_at(timestamptz · 分区键) · event_type(text · CHECK 点分小写 ≥2 段) ·
  schema_version(int NOT NULL) · tenant_id(uuid null) · space_id(uuid null) ·
  actor_type(text null) · actor_id(uuid null) · subject_type(text null) · subject_id(uuid null) ·
  payload(jsonb NOT NULL) · correlation_id(uuid null) · causation_id(uuid null) ·
  status ∈ {pending,claimed,delivered,dead} · worker_id · claimed_at · lease_expires_at ·
  attempts ∈ [0,100] · next_attempt_at · last_error · delivered_at · created_at
  **无 resource_type / resource_id 列**（实测 0 列）· **subject_type 无 CHECK 约束**
core 契约（core/event/interfaces.py）：DomainEvent{type, tenant_id, actor_id, space_id, payload, id,
  occurred_at, schema_version} · **EVENT_SCHEMA_VERSION = 1**（既有常量）·
  type 必须形如 'namespace.aggregate.action'（点分）
消费端（services/consumer/）：
  CLAIM_SQL：status='pending' AND next_attempt_at ≤ now() AND attempts < max_attempts
             **ORDER BY occurred_at** LIMIT batch FOR UPDATE SKIP LOCKED
  COMPLETE_PENDING 递增 attempts + 退避；COMPLETE_DEAD 递增 attempts + last_error；COMPLETE_DELIVERED 置 delivered
  worker：CLOSED allowlist；handler 未绑定 → 终态 `handler_not_bound`；未知类型 → `unsupported_event_type`；
          HandlerExecutionError(retryable) 决定 pending vs dead
  并发：WORKER_PROCESS_COUNT=1 · WORKER_CONCURRENCY=4（事件可并行处理 ⇒ 顺序不保证）
Producer：非测试代码 `INSERT INTO events` = 0（无 producer）
```

## 6. Envelope Compatibility（Batch 1 · 逐字段判定）

| 契约字段 | envelope 实况 | 判定 | Batch 1 结论 |
| --- | --- | --- | --- |
| event_type | `event_type` + 正则 | **REUSE** | 4 个名称均满足正则（§7） |
| schema_version | `schema_version` int NOT NULL | **REUSE** | core 已定义 `EVENT_SCHEMA_VERSION = 1` → 建议 V1 = 1 |
| actor | `actor_type` + `actor_id` | **REUSE** | actor_type='user' · actor_id=users.id（Batch 1 仅 USER） |
| tenant_id | `tenant_id` | **REUSE** | = employee.tenant_id（非空） |
| space_id | `space_id` | **REUSE** | = NULL（Employee 类固定） |
| resource identity | **无对应列** | **NEEDS DESIGN DECISION（F-P20E-001）** | 建议 payload.resource_type/resource_id |
| subject identity | `subject_type` + `subject_id`（无约束） | **NEEDS DESIGN DECISION** | 见 §11（词表未定义） |
| payload | `payload` jsonb NOT NULL | **REUSE** | 白名单见 §8/§9 |
| correlation_id | `correlation_id` | **REUSE** | 取自 API `x-correlation-id`（已存在 carrier） |
| causation_id | `causation_id` | **NOT APPLICABLE（V1）** | 无事件链 · 保持 NULL |
| dispatch 字段 | status/attempts/… | **REUSE（消费端所有）** | producer 仅写 status='pending' · attempts=0 |

## 7. Layer A — Recommended Contract（4 事件 · **recommended · 非 FROZEN**）

```text
# employee.created（recommended）
event_type      = employee.created（满足 envelope 正则）
schema_version  = 1（core EVENT_SCHEMA_VERSION 既有值 · 建议冻结）
actor           = actor_type='user' · actor_id = 认证发起用户（users.id）
tenant_id       = employee.tenant_id
space_id        = NULL
resource identity = payload.resource_type='company_employee' · payload.resource_id=employee_id
subject identity  = 见 §11（建议 V1 = NULL · 或 HUMAN DECISION 后使用专用取值）
payload          = {resource_type, resource_id, employee_no, display_name, status, user_id?}
correlation_id   = 发起请求 correlation（x-correlation-id）
causation_id     = NULL
idempotency      = schema_guaranteed（uq_company_employees_no (tenant_id, employee_no)）
authorization    = producer: company_employee.create（集合资源 · tenant path）
                   consumer: 必须重新走 AuthorizationService（AH）
lifecycle        = 仅创建成功（employee 落库且 tenant active）后产生
audit            = 同事务 audit_logs（company_employee.create）· audit ≠ event
atomicity        = business + audit + event 同逻辑事务（§12）
failure          = 沿用 P15（authorization_denied/handler_not_bound 终态 · connection/persistence 可重试）
ordering         = 无全局顺序保证（§16）
handler 职责      = 下游读取方同步（职责未定义 → 当前 QUALIFICATION BLOCKED）
acceptance gate   = §18 九项证据齐备方可
activation gate   = NOT AUTHORIZED（AH D-P20E-13）

# employee.updated
event_type      = employee.updated
payload          = {resource_type, resource_id, changed_fields[]（白名单字段名）, display_name?, title?}
idempotency      = naturally_idempotent（同一目标状态重复应用等价）
lifecycle        = 仅在**非 terminal 的 mutable 状态更新成功**后产生（display_name / title）
其余字段同 employee.created；authorization = company_employee.update
开放项           = "什么变化才算 updated"（是否含 user 绑定/解绑）→ HUMAN DECISION（D-P20E-DES-03）

# employee.suspended
event_type      = employee.suspended
payload          = {resource_type, resource_id, from_status='active', to_status='suspended'}
idempotency      = naturally_idempotent（条件更新 expect=active；重复 suspend 无副作用）
lifecycle        = 仅 active → suspended 成功转换后产生（**不发 attempted 事件**）
authorization    = company_employee.update

# employee.terminated
event_type      = employee.terminated
payload          = {resource_type, resource_id, from_status, to_status='terminated', terminated_at}
idempotency      = naturally_idempotent（终态；重复终止被拒）
lifecycle        = 仅 active|suspended → terminated 成功转换后产生；**不得引入 assignment cascade / auto-end**
authorization    = company_employee.update
```

```text
命名互斥规则（建议随 Contract 冻结）：状态专用事件与 generic `.updated` **互斥** ——
  suspend 只产生 employee.suspended；terminate 只产生 employee.terminated；二者不得再伴随 .updated。
```

## 8. Payload Field Spec（recommended · 逐字段）

| Event | field | type | required | purpose | source | allowed |
| --- | --- | --- | --- | --- | --- | --- |
| employee.created | resource_type | text | yes | 资源类型（consumer 重新解析授权资源） | 常量 'company_employee' | ✅ |
| employee.created | resource_id | uuid | yes | 员工业务身份 | INSERT RETURNING id | ✅ |
| employee.created | employee_no | text | yes | 组织内稳定业务键（幂等自然键） | 请求输入 | ✅ |
| employee.created | display_name | text | yes | 下游展示 | 请求输入 | ✅ |
| employee.created | status | text | yes | 创建后状态（'active'） | 常量 | ✅ |
| employee.created | user_id | uuid | no | 平台身份引用（V1 create 不设置，通常缺省） | 业务行 | ✅（可空） |
| employee.updated | resource_type / resource_id | text/uuid | yes | 同上 | 常量 / 目标员工 | ✅ |
| employee.updated | changed_fields | text[] | yes | 变更字段白名单（display_name / title） | 由输入推导 | ✅ |
| employee.updated | display_name / title | text | no | 变更后值（可选，便于下游收敛） | 变更结果 | ✅ |
| employee.suspended | resource_type / resource_id | text/uuid | yes | 同上 | 常量 / 目标员工 | ✅ |
| employee.suspended | from_status / to_status | text | yes | 明确转换方向（'active'→'suspended'） | 状态机 | ✅ |
| employee.terminated | resource_type / resource_id | text/uuid | yes | 同上 | 常量 / 目标员工 | ✅ |
| employee.terminated | from_status / to_status | text | yes | 转换方向（'active'/'suspended'→'terminated'） | 状态机 | ✅ |
| employee.terminated | terminated_at | timestamptz | yes | 终止时刻（业务语义） | 行数据 | ✅ |

```text
禁止进入 payload（AB/AH 已有 · 此处仅落实）：password · token · bearer · API credential ·
  secret 明文 · secret_ref 值 · DSN · connection string · SQL · stack trace · internal exception ·
  安全实现细节。另：不得整行 dump（不含 created_at/updated_at/tenant_id 冗余副本）。
```

## 9. Resource Identity Resolution（F-P20E-001 的推荐解决）

```text
问题：envelope 无 resource_type / resource_id 列。
建议（**无需 schema 变更**）：payload 承载 resource_type='company_employee' + resource_id=<employee_id>；
  **resource identity 不是授权凭证**，仅作为 consumer 重新进入既有 Resource / Authorization 解析的输入。
Consumer 解析规则（复用既有语义 · 不得自愈）：
  1) 以 envelope.tenant_id + payload.resource_type 查找 tenant 级**集合资源**（natural_key=employees）
  2) 缺失 ⇒ DENY（RESOURCE_NOT_PROVISIONED 同族 · 终态）
  3) 以集合资源 id 构造 ResourceRef 并调用既有 AuthorizationService
禁止：event-specific authorization · resource auto-provision · resource self-healing
```

## 10. Subject Identity（envelope subject_type / subject_id）

```text
实测：events.subject_type / subject_id 列存在且**无 CHECK 约束**；但仓库中**不存在**事件级 subject 词表
      （现有 subject 词表仅属授权域：USER / ROLE / AGENT · core.permission.vocabulary）
选项（**Human Decision Required** · 不得自行扩展枚举）：
  A) subject_type='USER' · subject_id=actor_id（镜像 actor）——与 actor 重复，信息量低
  B) subject_type='COMPANY_EMPLOYEE' · subject_id=employee_id ——需**新词表值**（DB 无约束，
     但属新语义 ⇒ 需裁定）
  C) V1 保持 NULL —— 最保守；资源身份已由 payload 承载（§9）
建议：C（V1 NULL），若需 B 必须先裁定；**不得因 actor=USER 就自动认定 subject=同一 USER**。
```

## 11. Correlation / Causation

```text
correlation_id：envelope 支持（uuid · nullable）；现有 API 已提供 `x-correlation-id` carrier
  （apps/api/routes/company.py::_correlation）⇒ **可复用**（建议 Producer 透传）
causation_id  ：V1 保持 NULL（不存在由事件触发的次级事件链）· 不得假造 lineage
若未来需要"事件触发事件"，须新 Human Decision（本轮不得设计 chain）
```

## 12. Producer Transaction Atomicity（D-P20E-005 建议冻结）

```text
规则：Business Mutation + Audit Log + Event Persistence 必须处于**同一逻辑数据库事务**；
  成功全提交；失败全回滚。
明确禁止两种反模式：business commit → event failure（业务成功但事件丢失）；
                    event commit → business rollback（幽灵事件）。
现状（F-P20E-003）：Company service 已有 business + audit 同事务（已实现并验收），
  但**尚无 event 写入集成**（生产代码 INSERT INTO events = 0）⇒ 属未来 Producer Implementation。
本轮只冻结规则，不实现。
```

## 13. Consumer Re-Authorization Mechanics（建议冻结）

```text
Consumer 不信任 Event 作为授权凭证（AH）。逐事件必须重新执行：
  actor  = envelope actor（user） —— 不得用 worker/系统主体替代
  tenant = envelope tenant_id（上下文；仍须经 canonical 授权与资源解析确认）
  space  = NULL（Employee 类）
  action = handler 所需 canonical action（read/update 等 · 不得新增 action）
  resource = 集合资源（§9 解析；缺失 = DENY）
分支语义（建议）：
  原 actor 仍有效            → 正常授权（ALLOW 继续 / DENY 终态）
  actor 已失效              → DENY · 终态 authorization_denied（不重试）
  tenant inactive           → DENY · 终态（对齐 P18-D14）
  resource projection 缺失   → DENY · 终态
  handler 未绑定             → 终态 handler_not_bound（既有 worker 语义）
禁止：platform_admin fallback · worker elevation · system principal 替代 · 跳过 AuthorizationService
若 Consumer 运行环境**无法恢复真实 USER actor context** ⇒ QUALIFICATION BLOCKED（AH 明令）
```

## 14. Idempotency Proof Plan（逐事件 · 建议冻结形式）

```text
event_id = event identity（P15 冻结）· 词表 {naturally_idempotent, transactional_key, schema_guaranteed}
employee.created      → schema_guaranteed：以 (tenant_id, employee_no) 为自然键；重复投递时
                        handler 判定"已存在且状态一致即视为成功"（不产生第二次业务副作用）
employee.updated      → naturally_idempotent：目标状态幂等；重复应用同值无额外副作用
employee.suspended    → naturally_idempotent：条件更新（active→suspended）；重复投递时第二/第三次
                        执行不改变状态，也不得改写审计/业务
employee.terminated   → naturally_idempotent：终态；重复终止被既有状态机拒绝
场景矩阵（每个 Handler 必须证明）：重复 delivery · 第一次成功 · 第二次成功 · 第一次失败 · 第二次重试
  → 结论要求：任何组合都不得产生错误的重复业务副作用
禁止：dedup table · event identity table · consumer receipt table（若无证明 ⇒ Activation = BLOCKED）
```

## 15. Lifecycle & Consumer Revalidation

```text
Producer gate（已实现）：tenant active 必需；Employee 类事件不涉及 space
Consumer gate（设计）：必须校验 tenant active? · employee 状态有效? · resource projection 存在? ·
  授权仍有效?（§13）
失败处理：使用 P15 已冻结 failure taxonomy（authorization_denied / handler_not_bound /
  unsupported_event_type / malformed_payload / max_attempts_reached / lease_expired_max_attempts /
  non_retryable_failure）；**不得新增 Company 专属 failure category**
不得修改 MAX_ATTEMPTS=10 · backoff 5→600 无 jitter · lease 120s · heartbeat 40s · concurrency 4 · batch ≤10
Employee 终态（terminated）不产生后续事件；不得引入 assignment cascade / auto-end / space cascade
```

## 16. Ordering & Delivery Assumptions

```text
实测：CLAIM_SQL 单批次 `ORDER BY occurred_at`，但 worker concurrency = 4 + 重试重排 + SKIP LOCKED
⇒ **无全局顺序保证**（建议 Contract 明确写为 NO GLOBAL ORDERING GUARANTEE）
Consumer 不得假定 created → updated → suspended → terminated 严格按序抵达；
若某 Handler 强依赖顺序 ⇒ QUALIFICATION BLOCKED（不得新增 ordering subsystem）
投递语义：at-least-once（失败重试至 delivered/dead）· 幂等即为此设计（§14）
```

## 17. Handler Responsibility（最小职责 · 未实现）

```text
单用途 · 幂等 · 授权感知 · 租户感知 · 生命周期感知
建议职责（PROPOSED）：employee.created/updated/suspended/terminated → 下游读取方/协作视图同步
  （**当前无已知下游消费者 ⇒ 职责未定义 ⇒ QUALIFICATION BLOCKED**）
禁止 Handler：改变 actor 身份 · 改变 tenant · 改变 ACL · 自建资源 · 执行无关 Company CRUD ·
  发出任意新事件 · 提升权限
当前：Qualified Handler = 0（保持）
```

## 18. Acceptance Evidence Matrix（未来 Activation Gate 所需）

| Event | Producer | Authorization | Transaction | Handler | Idempotency | Lifecycle | Tenant Isolation | Payload | Retry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| employee.created | MISSING | PROVEN（producer 侧）· 消费侧 DESIGNABLE | DESIGNABLE | MISSING | DESIGNABLE | DESIGNABLE | PROVEN | HUMAN DECISION | DESIGNABLE |
| employee.updated | MISSING | PROVEN · 消费侧 DESIGNABLE | DESIGNABLE | MISSING | DESIGNABLE | DESIGNABLE | PROVEN | HUMAN DECISION | DESIGNABLE |
| employee.suspended | MISSING | PROVEN · 消费侧 DESIGNABLE | DESIGNABLE | MISSING | DESIGNABLE | DESIGNABLE | PROVEN | HUMAN DECISION | DESIGNABLE |
| employee.terminated | MISSING | PROVEN · 消费侧 DESIGNABLE | DESIGNABLE | MISSING | DESIGNABLE | DESIGNABLE | PROVEN | HUMAN DECISION | DESIGNABLE |

```text
（PROVEN = 已由现有实现/验收证明；DESIGNABLE = 有设计路径未证明；MISSING = 不存在；
  HUMAN DECISION = 需裁定；BLOCKED = 当前不可解决。禁止以 PASS 替代状态。）
```

## 19. Activation Readiness

```text
Contract Frozen?        = NOT YET（本轮仅 recommended）
Qualification Complete? = NO（producer/handler 缺位）
Activation Authorized?  = NO（AH D-P20E-13 · Production Activation NOT AUTHORIZED）
⇒ ACTIVATABLE = NO（4/4）
（三者是不同状态，不得互相替代）
```

## 20. Final Contract Table（recommended · 未冻结）

| Event | Version | Actor | Tenant | Space | Resource | Payload | Auth | Idempotency | Lifecycle | Ordering | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| employee.created | 1 | USER | employee.tenant_id | NULL | company_employee collection（payload 承载） | §8 白名单（5–6 字段） | create | schema_guaranteed | 创建成功后 | 无保证 | **PROPOSED** |
| employee.updated | 1 | USER | employee.tenant_id | NULL | 同上 | §8（changed_fields 等） | update | naturally_idempotent | 非终态更新后 | 无保证 | **PROPOSED** |
| employee.suspended | 1 | USER | employee.tenant_id | NULL | 同上 | §8（from/to） | update | naturally_idempotent | active→suspended 成功后 | 无保证 | **PROPOSED** |
| employee.terminated | 1 | USER | employee.tenant_id | NULL | 同上 | §8（from/to + terminated_at） | update | naturally_idempotent | active/suspended→terminated 成功后 | 无保证 | **PROPOSED** |

```text
Status 取值仅允许：PROPOSED / HUMAN DECISION REQUIRED / FROZEN / NOT AUTHORIZED。
本表全部为 PROPOSED；payload 白名单与 subject identity 为 HUMAN DECISION REQUIRED。
```

## 21. Contract Freeze Findings（F-P20E-001…003 逐项处置）

| Finding | Problem | Existing Authority | Recommended Resolution | Impact | Requires Schema? | Requires Code? | Requires Human Decision? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **F-P20E-001** | events envelope 无 `resource_type` / `resource_id` 列 | 附录 AH D-P20E-08/§8（资源模型）· P10/P15 envelope 冻结 | 由 **payload 承载** resource_type/resource_id，consumer 重新解析集合资源；不改 schema | 契约可表达，无需迁移 | **NO** | NO（consumer 侧解析属未来实现） | **YES**（确认 payload 承载方案） |
| **F-P20E-002** | Company service 授权主体硬编码 `subject_type="USER"` | 附录 AH D-P20E-05（真实认证主体）· F-P20E-002 登记 | Batch 1 冻结 **actor = USER**；Role/Agent 明确排除于 V1 Scope（未来需新决策） | 事件 actor 可确定；不新增主体 | NO | NO（V1 不做 role/agent） | **YES**（确认 V1 = USER 范围） |
| **F-P20E-003** | producer 事务无 event 写入集成（生产代码 0） | 附录 AH D-P20E-01（Design only）· P19-D03 | 冻结"business + audit + event 同逻辑事务"规则（§12）；实现属未来轮次 | 规则可冻结，实现后置 | NO | **YES（未来轮次）** | **YES**（确认原子规则） |

## 22. Schema Change Decision

```text
默认原则：**NO ENVELOPE SCHEMA CHANGE**（本 Batch 不创建 0021 · 不改 0019/0020 · 不改 events 表）
依据：Batch 1 的 4 个事件所需字段均可由既有 envelope + payload 白名单表达（§6/§9），
      且既有 Authorization / Resource Resolution 可通过 tenant 级集合资源重新进入（§13）。
触发条件：若未来实现证明 payload 承载无法满足 canonical authorization ⇒
      CONTRACT FREEZE = BLOCKED 并提交 Human Decision（不得自行创建迁移）。
```

## 23. Recommended Batch Strategy

```text
建议（Human Decision 项 D-P20E-DES-13）：
  BATCH 1 = Employee 4 事件（本报告范围）· BATCH 2 = Assignment 3 事件（待 Batch 1 成熟后）
理由：Employee 无 space 语义 · user actor 已实现 · 生命周期与租户边界更简；
      Assignment 涉及显式 space、tenant 一致性（三向相等）与 `.updated`/`.ended` 边界裁定。
```

## 24. Layer B — Human Decision Items

| ID | 议题 | 状态 | 说明 |
| --- | --- | --- | --- |
| D-P20E-DES-01 | Event naming | **NEW**（建议 FREEZE THESE 4 EXACT NAMES） | employee.created/.updated/.suspended/.terminated · 互斥规则（§7） |
| D-P20E-DES-02 | Schema version | **NEW**（建议 1） | core 既有 `EVENT_SCHEMA_VERSION = 1`；breaking change ⇒ 新版本 |
| D-P20E-DES-03 | Payload whitelist | **NEW** | §8 逐字段表（含 "什么算 updated" 的边界） |
| D-P20E-DES-04 | Resource identity representation | **NEW** | payload 承载（F-P20E-001 推荐解） |
| D-P20E-DES-05 | Actor scope = USER for Batch 1 | **NEW**（与 AH 原则一致） | role/agent 排除于 V1（F-P20E-002） |
| D-P20E-DES-06 | Subject identity | **NEW** | 选项 A/B/C（§10）；建议 V1 = NULL |
| D-P20E-DES-07 | Correlation / causation | **NEW** | correlation 复用既有 carrier；causation = NULL |
| D-P20E-DES-08 | Producer transaction atomicity | **NEW**（规则）· 原则已被 AH/AB 覆盖 | §12 |
| D-P20E-DES-09 | Consumer re-authorization mechanics | **NEW（机制）** · 原则 ALREADY FROZEN BY AH | §13 |
| D-P20E-DES-10 | Idempotency proof form | **NEW（形式）** · 要求 ALREADY FROZEN BY AH | §14 |
| D-P20E-DES-11 | Lifecycle rejection | **NEW（行为）** · 原则 ALREADY FROZEN BY AH | §15 |
| D-P20E-DES-12 | Ordering assumption | **NEW** | NO GLOBAL ORDERING GUARANTEE（§16） |
| D-P20E-DES-13 | Batch 1 scope | **NEW** | Employee 4 项（§23） |

## 25. Blocking / Non-blocking

```text
DESIGN BLOCKING（对 Contract Freeze）：
  F-P20E-001（资源身份表示方案待裁）· F-P20E-002（subject identity 词表待裁）·
  D-P20E-DES-03（payload 白名单待裁）—— 三项均为**待 Human 裁定**，不是系统缺陷。
实现层阻断（未来）：
  F-P20E-003（producer 事务集成未实现）· Handler 职责未定义（无已知下游）⇒ QUALIFICATION BLOCKED
NON-BLOCKING（观察）：
  O-P20E-003（events 分区手工运维）· O-P20E-004（consumer 必须以原始 actor 身份重新授权）·
  既有 O-1（services/company 3 处 inline SQL）· O-2（list = limit-only）
系统 BLOCKING：**无**（无意外事件/producer/handler/worker · allowlist EMPTY · 无 schema 变更 ·
  P20 API/Domain/Authorization 基线未变）
```

## 26. Final Verdict

```text
P20 EVENT CONTRACT FREEZE BATCH 1 PREP = PASS

Contract:            READY FOR HUMAN FREEZE（Layer A 已备 · 尚未冻结）
Producer:            0
Qualified Handler:   0
Allowlist:           EMPTY
Production Event:    NOT AUTHORIZED
Worker:              NOT AUTHORIZED
Migration:           NOT AUTHORIZED
ACTIVATABLE:         NO（4/4）

Human 可确定性冻结 Layer A（Layer B 13 项裁定后），本轮不冻结、不写入 PDL、不实现。
```

## 27. Hard Stop

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0
0019 / 0020 sha256 未变 · No 0021 · Allowlist EMPTY · Producer 0 · Handler 0 · Worker 0 · events 0
常驻库未变（uap_b1_test = 0017_p13_seed · 正式库 uap = 0 public 表）
本轮仓库写入 = 仅本报告 · **未修改 PDL** · 未实现 producer/handler · 未注册 handler ·
未激活 allowlist · 未创建 event 行 · 未 commit / tag / push

HARD STOP = ACTIVE
下一步：Human 对 Batch 1 Contract 做正式 Freeze Decision（可据 Layer A 逐条确认 Layer B 的 13 项）
```

**END OF P20 EVENT CONTRACT FREEZE BATCH 1 PREP REPORT（4 个 Employee 事件 recommended contract 完成 · 三项阻断皆有可执行解决路径且无需 schema 变更 · 13 项 Human Decision Items 列明 · 未冻结 / 未实现 / 未激活 / 未 commit；2026-10-04）**
