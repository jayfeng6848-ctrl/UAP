# UAP — P14_RUNTIME_SLICE IMPLEMENTATION CONTRACT

> ## 状态
>
> ```text
> 阶段      = P14_RUNTIME_SLICE（FROZEN 编号 · PDL 附录 M.1）
> 契约状态   = **FROZEN**（内容全部来自 Human Decision 与既有冻结事实；无自行扩展）
> 决策来源   = PLATFORM_DECISION_LOG.md **附录 N**（15 项 HUMAN DECISION，2026-09-27）
>              + P14_HUMAN_DECISION_SHEET.md（请求单）
> 关联载体   = P14_RUNTIME_SLICE_SCOPE.md · _DEPENDENCY_MAP.md · _ACCEPTANCE_MATRIX.md
> 本轮未做   = 未创建 runtime code / API / CLI implementation / migration / schema ·
>              无 DDL / DML / GRANT / REVOKE / CREATE ROLE · 未 commit / tag / push
> 授权状态   = `P14 IMPLEMENTATION = NOT AUTHORIZED`（本契约不构成实施授权）
> ```

---

# 0. 三条身份与授权铁律（贯穿全文）

```text
TR-1  uap_app ≠ uap_migrator
      runtime 身份与 migration 身份是**两个不同的数据库角色**，职责与权限面不相交。

TR-2  runtime ≠ migration trust
      C2 / CC-7 仅用于 migration trust boundary；Runtime **不绕过 C2 · 不模拟 uap_migrator ·
      不继承 migration privilege**。

TR-3  new GRANT / role ≠ implicit P14 implementation
      任何新增数据库角色与授权**不并入本轮** Runtime implementation；
      必须另开 Privilege / Security Gate（见 §12）。
```

---

# 1. Runtime Scope

```text
构建（依 PDL 附录 N 的 OQ-P14-01/04/06/07/09/10/11）：
  · runtime execution layer（进程/服务宿主，single-host baseline + container-friendly）
  · API / service boundary（apps/api = transport / adaptation；services = use-case orchestration）
  · identity onboarding（Service-mediated staged onboarding）
  · credential 生命周期（独立于 identity）
  · device 绑定与撤销
  · authorization enforcement（应用/服务层）
  · bootstrap（local operator-controlled CLI）
  · observability（vendor-neutral structured）

不构建（依同一组决策与既有冻结约束）：
  · 任何 schema 对象（表/列/约束/索引/触发器/函数）
  · 任何 migration（0018+）
  · permission vocabulary 变更（12 项 canonical 与 action 词表不动）
  · 新授权模型 / 新 subject type / deny 行
  · DB RLS 作为主授权机制（OQ-P14-05 明确排除）
  · 公开网络的 bootstrap endpoint（OQ-P14-09 明确排除）
  · 第二套 dev bootstrap 身份路径（D-PLAT-11②）
```

---

# 2. Security Boundary

```text
SB-1  身份分离（TR-1 / TR-2）不得削弱
SB-2  C2 / CC-7 仅服务 migration trust boundary；Runtime 与 registry 完全解耦
SB-3  不得引入可伪造判据：普通 GUC · application_name · session variable · temporary flag
SB-4  secret 只以 Argon2id hash 形式存在；禁止 plaintext；**禁止 secrets 写入日志**
SB-5  operational logs 与 audit logs **分离**（不得混用载体）
SB-6  审计写入语义沿用既有契约（audit_logs 不可变 · tg_audit_immutable）
SB-7  不新增 GRANT / REVOKE / CREATE ROLE / default ACL（TR-3）
SB-8  不放宽既有 DB 层护栏（C2 · roles is_system · membership scope · audit immutable）
```

---

# 3. Identity Contract

```text
IC-1  onboarding 形态 = Service-mediated staged onboarding
IC-2  流程阶段 = pending → identity verification → credential/device verification → activation/session
IC-3  客户端**不得直接访问 DB**（只能经 API/服务边界）
IC-4  bootstrap 与普通 onboarding **分离**（前者见 §8）
IC-5  identity 行与 credential 分离（见 §4）；identity 不携带 secret
IC-6  授权主体词汇沿用 {user, role, agent}（D-AUTH-18）；identity kind / provider 词汇
      不得作为授权主体类型
```

---

# 4. Credential Contract

```text
CC-1  credential 隶属于 identity
CC-2  secret 仅存 **Argon2id hash**（禁止 plaintext / 可逆形式）
CC-3  支持 rotation（轮换）
CC-4  支持 revoke（撤销）
CC-5  支持 expire（到期失效）
CC-6  禁止 secrets 写入日志（含审计 metadata）
CC-7  生命周期动作须可审计（沿用既有 audit 面语义，不新增 schema）
```

---

# 5. Device Contract

```text
DC-1  关系基数 = 1 User : N Device
DC-2  关系基数 = 1 Device : 1 User（单归属）
DC-3  必须显式 enrollment / challenge（不得隐式绑定）
DC-4  Device revoke 时**同事务**撤销其 active sessions
DC-5  不得以设备引入新的授权主体类型（D-AUTH-18 保持）
```

---

# 6. Authorization Contract

```text
AC-1  判定位置 = **Centralized authorization precheck** + **Service / use-case mandatory enforcement**
AC-2  handler **不承载业务授权决策**（handler 薄）
AC-3  强制边界 = Application / Service 层（**P14 不使用 DB RLS 作为主授权机制**）
AC-4  原则 = default deny · deny precedence · ABAC（沿用 D-AUTH-07 / D-AUTH-12）
AC-5  失败语义 = FAIL CLOSED（判定不确定或依赖不可用 ⇒ 拒绝，不放行不降级）
AC-6  DB 层仅保留既有护栏；**不新增**策略表 / 视图 / 函数
```

---

# 7. Service Boundary

```text
SC-1  apps/api = transport / adaptation（**handler 不直接 SQL**）
SC-2  services = use-case orchestration + transaction boundary + persistence coordination
SC-3  domains = business rules + contracts；**domains 不依赖具体 services**
SC-4  分层硬门保持：G-1 core ↛ SQLAlchemy/psycopg · G-2 core ↛ services ·
      G-3 agent ↛ services · G-4 domains ↛ {services, infrastructure}
SC-5  不得新增越层依赖（AST 判定，禁字符串匹配）
```

---

# 8. Bootstrap Rules

```text
BR-1  Bootstrap = **local operator-controlled CLI**
BR-2  explicit invocation（不得由服务启动流程隐式触发）
BR-3  one-time initialization（一次初始化）
BR-4  bootstrap state lock（沿用既有 platform_state + PM 条件）
BR-5  **无公开网络 bootstrap endpoint**
BR-6  完成 bootstrap 后进入 normal onboarding（§3）
BR-7  沿用 R4/R5 既有语义：原子流程 = 插 PM → 翻转 state → audit('platform.admin.bootstrap') → COMMIT；
      普通 API / seed 永不写 PM；无恢复 API
```

---

# 9. Deployment Baseline

```text
DB-1  基线 = single-host + container-friendly；**无强制 orchestration dependency**
DB-2  未来允许 multi-instance expansion（不强制、不预置）
DB-3  期望 revision 由构建期只读工件承载（D-PLAT-15 v2），运行时不可覆盖
DB-4  readiness / liveness 语义沿用 D-PLAT-14 / D-PLAT-16（探针 2000 ms · 失败不重试不降级）
DB-5  不建立 CI（D-PLAT-17 ⑦）；硬门由人工执行并留证
```

---

# 10. Failure Rules

```text
FR-1  Fail-closed（默认拒绝）
FR-2  错误必须**分类**（区分依赖失败 / 输入错误 / 授权拒绝 / 内部错误）
FR-3  事务失败必须 **rollback**（不留半成品）
FR-4  Retry：仅幂等 / 安全场景 · bounded（有上限）· **no blanket retry**
FR-5  错误信息不得泄露 secret 或内部结构细节
```

---

# 11. Observability

```text
OB-1  Vendor-neutral structured observability（不绑定特定厂商/后端）
OB-2  必含：request ID · correlation ID
OB-3  面覆盖：logs · metrics · trace hooks
OB-4  禁止：secrets · sensitive payloads
OB-5  **operational logs 与 audit logs 分离**（不同载体、不同用途）
OB-6  审计事件语义沿用既有 audit_logs 契约（不新增 schema）
```

---

# 12. Privilege Boundary

```text
PB-1  uap_app = **保持当前最小权限**（5 项显式授权 + schema USAGE · CREATE = false）
PB-2  **不授予宽泛 DB 写权限**
PB-3  Runtime **不使用 uap_migrator**
PB-4  Runtime 使用**独立 runtime / trusted service principal**（形态属独立 Gate，见 §13）
PB-5  新 DB role / GRANT / privilege **不并入本轮** Runtime implementation
PB-6  新 privilege 必须**另开 Privilege / Security Gate**
PB-7  既有约束继续有效：D-OP101-07（未获新决策前不得扩权）· D-OP101-08（runtime 不持 DDL）·
      OI-G-1（runtime 逐表 DML 矩阵不可核定）· OI-G-2（分区不继承授权）· pg_default_acl = 0
```

---

# 13. P14 PRIVILEGE PRECONDITION

> **状态：PRECONDITION / SEPARATE SECURITY GATE**
> **禁止**将其视为已完成的权限实施。

```text
PP-1  事实：当前 uap_app 权限**不足以**完成完整 runtime onboarding / write path。
      实测：uap_app 仅持 5 项授权（alembic_version SELECT · audit_logs(+分区) INSERT/SELECT）
      + SCHEMA public USAGE；对 users / identities / credentials / sessions / roles /
      tenants / spaces / platform_memberships / memberships / resource_permissions /
      events / agents / platform_state 等表**零权限**（SELECT/INSERT/UPDATE/DELETE 全 False）。

PP-2  解决方式（依 OQ-P14-13 = OPTION B）：**Trusted Internal Service Boundary**
      —— 写路径经受信内部边界执行，runtime 不直接持宽泛写权限。

PP-3  未来需要（**不在本轮执行**）：
      · dedicated runtime principal（独立受信主体）
      · least-privilege grants（最小必要授权集）

PP-4  本轮明确不做：
      · 不执行 GRANT / REVOKE
      · 不创建新 DB role
      · 不修改 default ACL / ownership

PP-5  后续入口：**privilege / security gate**（独立授权轮），须先经 Human 授权；
      在此之前，runtime 的写路径实现不得依赖任何新授权。

PP-6  边界：PP-1…PP-5 不改变 uap_app 现有权限面，也不产生任何 DB 变更。
```

---

# 14. Implementation Preconditions

```text
IP-1  决策已冻结：PDL 附录 N（15 项）· 本契约 FROZEN ✔
IP-2  文档集合：5 份（SCOPE · DEPENDENCY_MAP · ACCEPTANCE_MATRIX · PREP_REPORT · 本契约）
IP-3  Scope / Dependency / Acceptance 已按冻结决策同步（见各文件同步章节）
IP-4  Acceptance 状态保持 **PENDING**（实施前不得填写结果）
IP-5  Privilege Precondition 已登记（§13），并明确属独立 Gate
IP-6  实施前须取得**独立的** `P14 IMPLEMENTATION AUTHORIZATION`（本契约不构成授权）
IP-7  若实施中发现需要 schema 变更 / 新授权 / 新主体类型 ⇒ 停止并另立独立授权
```

---

# 15. 契约边界

```text
本契约内容**全部**来自 Human Decision（PDL 附录 N）与既有冻结事实；无自行扩展。
本契约 = FROZEN；未产生实施授权。
本轮：DDL = 0 · DML = 0 · GRANT = 0 · CREATE ROLE = 0 · migration = 0 · runtime code = 0 ·
      commit = 0 · tag = 0 · push = 0
```

---

**END OF P14_RUNTIME_SLICE IMPLEMENTATION CONTRACT（2026-09-27 · FROZEN · 依 PDL 附录 N 的 15 项 HUMAN DECISION · Privilege Precondition = PRECONDITION / SEPARATE SECURITY GATE · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
