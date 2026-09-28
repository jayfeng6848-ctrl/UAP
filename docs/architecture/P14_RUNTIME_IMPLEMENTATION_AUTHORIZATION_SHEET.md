# UAP — P14 RUNTIME IMPLEMENTATION AUTHORIZATION SHEET

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION（§二十一）
> 状态      = **HUMAN AUTHORIZATION RESOLVED**（2026-09-27 · 10 / 10 已裁决）
>             权威裁决记录见文末 **Resolution Registry**；
>             §1 的 RTA-01…RTA-10 候选与勾选框**保留为历史候选**（未删除、未重新编号）
> 基线      = Security DB Boundary = ACCEPTED（uap_runtime 51 / uap_bootstrap 6 · OI-G-1 CLOSED）
>             HEAD c420403d… · migration 0017_p13_seed · 0018+ = 0
> 前置      = Security Closure = PASS · Runtime file inventory / dependency lock /
>             DB connection contract / acceptance mapping / impact = COMPLETE
> ```

---

# 1. Human Authorization Requests（RTA-01 … RTA-10）

## RTA-01 — 授权 Runtime application implementation

```text
范围    : apps/ 与 services/ 下的 Runtime 应用实现（IN SCOPE 清单 §3 A/B/F）
不包含  : schema / migration / 新角色 / 新授权 / bootstrap CLI
影响    : 开始实际编写 Runtime 代码（当前 0 行新增）
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM（请说明）     Notes:
```

## RTA-02 — 授权 Runtime 使用 `uap_runtime` 连接数据库

```text
范围    : 运行时连接身份切换为 uap_runtime（含 config/settings.py 的 DSN 与部署面凭据注入）
依据    : SEC-P14-01 / 02 · DC-1…DC-10
不包含  : 使用 uap_migrator / uap_bootstrap 凭据；新增任何 grant
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-03 — 授权 database-backed identity onboarding

```text
范围    : staged onboarding（pending → identity verification → credential/device verification →
          activation）的落库实现（users / identities / credentials）
依据    : OQ-P14-01 · SEC-P14-03/04/08 · 已授权权限（users S/I/U · credentials S/I/U 等）
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-04 — 授权 device enrollment / session lifecycle implementation

```text
范围    : 设备绑定（显式 challenge）· 设备撤销（**同事务**撤销 active sessions）·
          会话建立与失效
依据    : OQ-P14-03 · DV-1…DV-5 · SS-1/2（sessions 为唯一含 DELETE 的对象之一）
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-05 — 授权 centralized authorization implementation

```text
范围    : SEC-10 HYBRID 的集中式 precheck + service/use-case mandatory enforcement
依据    : AP-1…AP-10 · 服务只读授权模型（roles/permissions/role_permissions/
          acl_subject_types/resource_permissions = SELECT only）
不包含  : 任何授权模型变更 / 任何授权表写
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-06 — 授权 Repository / Service / API implementation

```text
范围    : repository 适配 · service 编排与事务边界 · API 边界
依据    : SC-1/2/3 · DC-16…DC-20（事务由 service 控制）
不包含  : handler direct SQL · handler direct authorization decision
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-07 — 授权 fail-closed / transaction / retry implementation

```text
范围    : 错误分类 · FAIL CLOSED · 事务回滚 · bounded retry（no blanket retry）
依据    : Contract §10 FR-1…FR-5 · DC-21…DC-35
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-08 — 授权 observability implementation

```text
范围    : request/correlation ID · 结构化日志 · metrics · trace hooks ·
          脱敏（无 secret / credential / raw sensitive payload）· operational ≠ audit
依据    : Contract §11 OB-1…OB-6 · OB 边界（不引入新权限模型）
Human : [ ] 授权   [ ] 不授权   [ ] CUSTOM     Notes:
```

## RTA-09 — Bootstrap CLI implementation 是否与 Runtime 同轮

```text
问题    : Bootstrap CLI 实现（`Bootstrap Principal` → one-time bootstrap）是否纳入本轮授权，
          或保持**独立**后续授权？
现状    : DB 层权限已就位（uap_bootstrap 6 项 · catalog 断言 5/5 PASS）；CLI 未实现
依据    : SEC-P14-11/12/13 · BC-1…BC-10（本地 CLI · 无公开端点 · 一次性锁）
选项    : [ ] A 同轮实施   [ ] B 保持独立（后续单独授权）   [ ] CUSTOM
注意    : 无论选 A 或 B，均须遵守「Bootstrap CLI ≠ Runtime API」与一次性边界
Human : 选择：____     Notes:
```

## RTA-10 — 是否允许在 P14 内部加入非 migration 的 Runtime support object

```text
问题    : 若 Runtime 实现需要新增任何**数据库对象**（表 / 视图 / 函数 / 索引）——
          是否允许在 P14 内部加入？
判定    : **若答"是"且涉及 schema ⇒ 必须单独进入 Schema Decision**
          （不得通过 Runtime Authorization 隐式授权 migration；0018+ 仍为 FORBIDDEN）
选项    : [ ] A 不需要新增对象（保持零 schema 变更）   [ ] B 需要 ⇒ 单列 Schema Decision
          [ ] CUSTOM
Human : 选择：____     Notes:
```

---

# 2. Runtime Implementation Hard Constraints（§二十三 · 冻结）

```text
RUNTIME MUST NOT:
  use uap_migrator
  use uap_seed
  use uap_bootstrap for normal requests
  bypass authorization
  direct SQL from handlers
  modify resource_permissions through normal Runtime
  modify platform_memberships through normal Runtime
  modify platform_state through normal Runtime
  modify tenants/spaces
  physical-delete credentials
  change C2
  change CC-7
  change P13 seed
  create roles
  grant privileges
  alter default ACL
  run migrations
（以上 17 条与 Security DB Boundary 的实测拒绝面一一对应：54 次负向探针 0 意外放行）
```

---

# 3. Runtime Security Boundary Invariants（§二十四 · 正式不变量）

```text
RUNTIME-SEC-01  Normal Runtime uses uap_runtime only.
RUNTIME-SEC-02  Migration uses uap_migrator only.
RUNTIME-SEC-03  Bootstrap uses uap_bootstrap only.
RUNTIME-SEC-04  No cross-principal credential reuse.
RUNTIME-SEC-05  Authorization is centralized.
RUNTIME-SEC-06  Unknown access is denied.
RUNTIME-SEC-07  Runtime cannot mutate resource_permissions.
RUNTIME-SEC-08  Runtime cannot mutate bootstrap-owned platform state.
RUNTIME-SEC-09  Runtime cannot acquire migration authority.
RUNTIME-SEC-10  Security DB boundary is not modifiable by Runtime code.

⇒ 10 条不变量在实施期须由测试与探针持续保持；任一被破坏 ⇒ STOP 并上报
```

---

# 4. 本轮工程变更

```text
未修改任何文件 · runtime code / API / service / repository / identity / device / session /
authorization / bootstrap CLI 实现 = 0 · new role / grant / revoke / DDL / DML / migration = 0
新增文档 = 本文件（+ 同轮 6 份）· commit = 0 · tag = 0 · push = 0
P14 RUNTIME IMPLEMENTATION = **NOT AUTHORIZED** · HARD STOP = ACTIVE
```

---

# RESOLUTION REGISTRY（HUMAN AUTHORIZATION RESOLVED · 2026-09-27）

> **本 Registry 为权威裁决记录**。§1 的候选文本与勾选框保留为历史候选（依"保留历史、
> 不得删除、不得重新编号、不得创造第二套 RTA ID"）。本轮**不产生任何实现**。

```text
RTA-01 = **AUTHORIZED**   Runtime application implementation
        范围：Runtime process · API boundary · service layer · repository/persistence layer ·
              centralized authorization integration · identity/device/session workflow ·
              operational health · observability · 测试
        约束：严格服从 P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md 与
              P14_RUNTIME_IMPLEMENTATION_FILE_INVENTORY.md；不得扩大 scope

RTA-02 = **AUTHORIZED**   Runtime 使用 `uap_runtime` 连接数据库
        冻结映射：Normal Runtime → uap_runtime · Migration → uap_migrator ·
                  Seed → uap_seed · Bootstrap → uap_bootstrap
        禁止：使用 migrator / bootstrap / seed credential · role switching 获取其他 principal 能力 ·
              读取 repository 中的 privileged credentials
        实现契约：P14_RUNTIME_DB_CONNECTION_IMPLEMENTATION_CONTRACT.md

RTA-03 = **AUTHORIZED**   Database-backed identity onboarding
        状态机：pending → identity verification → credential/device verification → activation/session
        要求：service-mediated · 事务边界明确 · fail-closed · 无 plaintext · Argon2id ·
              rotation/revoke/expire · handler 不做数据库 orchestration ·
              **不绕过 centralized authorization** · **不得新增认证模型**

RTA-04 = **AUTHORIZED**   Device enrollment / session lifecycle
        范围：device enrollment / verification / revoke · session creation / expiration ·
              active-session revoke · refresh/rotation 生命周期 · 多设备语义
        不变量：one user → many devices · one device → one user
        原子性：device revoke 与 active session revoke 必须在明确 transaction boundary 内

RTA-05 = **AUTHORIZED**   Centralized authorization（HYBRID MODEL）
        形态：Central Authorization Service / Use-case + Restricted Runtime DB Read
        要求：centralized precheck · service mandatory enforcement · handler 不决定授权 ·
              default deny · deny precedence · ABAC · authorization failure → fail closed ·
              决策可审计 · 无 bypass
        约束：Stage 2 Authorization 基线可扩展，**不得无故重写**已有 authorization architecture

RTA-06 = **AUTHORIZED**   Repository / Service / API
        冻结职责：Handler = transport/adaptation · Service = orchestration + authorization
                  enforcement + transaction boundary + persistence coordination ·
                  Repository = persistence access · Domain = rules/contracts
        禁止：handler direct SQL · handler direct authorization · domain import concrete service ·
              service/domain 循环依赖 · persistence 逻辑散落 API 层
        不变量：Core → Domain = 0

RTA-07 = **AUTHORIZED**   Fail-closed / transaction / retry
        Fail Closed：授权失败 / 安全边界异常 / 未知状态 / 凭据或会话验证歧义 ⇒ **DENY**
        Transaction：BEGIN → use-case → COMMIT；异常 ⇒ ROLLBACK
        Retry：仅 idempotent / deterministic safe / bounded；禁止 catch-all → retry-all；
               不得用 retry 掩盖 authorization failure / constraint violation /
               credential error / security failure

RTA-08 = **AUTHORIZED**   Observability
        范围：request ID · correlation ID · structured logging · metrics · trace hooks ·
              health status · runtime diagnostic context
        禁止：NO SECRET / NO PASSWORD / NO TOKEN / NO CREDENTIAL MATERIAL / NO RAW SENSITIVE PAYLOAD
        分离：Operational Logs ≠ Audit Logs

RTA-09 = **OPTION B — REMAINS SEPARATE**   Bootstrap CLI NOT IMPLEMENTED THIS ROUND
        冻结：Runtime API ≠ Bootstrap CLI · Runtime Principal ≠ Bootstrap Principal
        本轮：BOOTSTRAP CLI = **OUT OF SCOPE**（须另一独立 implementation authorization）
        禁止：Runtime 调用 Bootstrap CLI 作为 normal request path

RTA-10 = **OPTION B**   NO IMPLICIT RUNTIME SUPPORT OBJECT CREATION
        禁止隐式创建任何 schema support object（table / view / matview / function / procedure /
          trigger / index / sequence / type / schema）
        若发现现有 schema 无法完成功能 ⇒ 登记 **SCHEMA DEPENDENCY DISCOVERED** ⇒
          **STOP AT SCHEMA BOUNDARY** ⇒ 建立独立 **Schema Decision**
        禁止：自行写 migration / 创建 0018 / 手动 DDL / 临时 CREATE VIEW 或 FUNCTION /
              把 support object 藏在 test fixture / 把 schema modification 藏在 startup hook
```

```text
汇总：RTA-01…RTA-08 = AUTHORIZED（8）· RTA-09 / RTA-10 = OPTION B（2）⇒ 10 / 10 RESOLVED
ID 完整性：RTA-01…RTA-10 无重复、无重编号、无第二套 RTA ID
本轮工程变更：runtime code / DDL / DML / migration / new role / grant / revoke = 0
```

---

**END OF P14 RUNTIME IMPLEMENTATION AUTHORIZATION SHEET（2026-09-27 · **HUMAN AUTHORIZATION RESOLVED 10/10** · RTA-01…08 AUTHORIZED · RTA-09/10 = OPTION B · 本轮未产生实现）**
