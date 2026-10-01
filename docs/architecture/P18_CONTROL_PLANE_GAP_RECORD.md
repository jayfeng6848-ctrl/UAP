# P18 CONTROL PLANE GAP RECORD

```text
登记日期   = 2026-10-01
阶段       = P18 DECISION FREEZE（Human Decision 已裁定；本文件保留原始 observation）
基线       = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME（9fe282b0）
依据       = P18 HUMAN DECISION + PREP 指令 + P18 HUMAN DECISION FREEZE 指令
             + P18_HUMAN_DECISION_PREP.md（原始勘验）
状态       = STOP-1 / STOP-3 / STOP-4 / initial-role blocker / control-plane authorization blocker
             = RESOLVED BY HUMAN DECISION
```

> 原则：原始 STOP 与原始 observation **保留不删**；本节记录裁定与实现后果。

---

## 1. 原始 observation（PREP 勘验事实 · 保留）

```text
O-1  uap_bootstrap 实测仅 3 项权限：audit_logs INSERT · platform_memberships INSERT/SELECT ·
     platform_state SELECT/UPDATE；tenants / spaces / resources 等**无任何写权限**
O-2  uap_runtime = 56 grants；tenants/spaces = SELECT only
O-3  全新平台 roles = 1（platform_admin · PLATFORM · is_system=true）⇒ 无 eligible TENANT/SPACE 角色
O-4  uap_bootstrap / uap_seed 的授权在 migrations 与 scripts 中**无版本化来源**（环境态）
O-5  spaces.status ∈ {active, archived, deleted}（无 provisioning / suspended）；
     tenants.status ∈ {provisioning, active, suspended, archived, deleted}
O-6  tenants 无 owner 列
O-7  tenant_memberships 触发器要求 active 的同租户 TENANT 角色；
     memberships 触发器要求 active 的同空间 SPACE 角色
O-8  roles 触发器：SPACE 角色必须 tenant_id IS NULL 且 space_id NOT NULL；
     is_system=true 不可在运行期创建；system 行不可变
O-9  FK：spaces/resources → tenants RESTRICT；roles/memberships → tenants CASCADE
O-10 audit_logs 为 append-only（UPDATE/DELETE 一律拒绝）
O-11 uap_runtime 仍持有 resources INSERT/UPDATE（P14 残留）
```

## 2. 原始 STOP（保留）

```text
STOP-1  控制面结构写权限 = 新 privilege surface（uap_bootstrap 无 tenants/spaces/resources 写）
STOP-2  平台不存在 eligible TENANT/SPACE 角色 ⇒ 首个租户/空间管理员无法成立
STOP-3  控制面主体授权无可重现来源（uap_bootstrap/uap_seed 未版本化）
STOP-4  spaces.status 缺 provisioning/suspended（若需要则为 schema gap）
STOP-5  控制面授权模型未定义（结构对象在创建前无 resource 行）
```

## 3. Human Decision（裁定）

```text
P18-D01 = dedicated uap_control（新建最小权限控制面主体）
P18-D02 = existing tenant lifecycle states + soft lifecycle（无物理删除）
P18-D03 = explicit initial tenant admin（显式输入 initial_admin_user_id）
P18-D04 = explicit initial space admin（显式输入 initial_space_admin_user_id）
P18-D05 = bootstrap-only non-system scoped administrator roles（不新增 permission）
P18-D06 = platform_admin-only control-plane authorization（复用既有 AuthorizationService）
P18-D07 = existing one-time platform bootstrap unchanged（未 initialized 时结构 provisioning = DENY）
P18-D08 = natural-key idempotency + exact-match replay + conflict on mismatch
P18-D09 = single logical transaction + atomic audit
P18-D10 = authenticated dedicated control-plane API namespace（非 P17 runtime 命名空间）
P18-D11 = structural audit（actor = 真实认证平台主体）
P18-D12 = Production Event Activation = REJECT
P18-D13 = dedicated least-privilege privilege surface + no runtime expansion
P18-D14 = 派生运行时规则：仅 ACTIVE Tenant / ACTIVE Space 可建立正常运行时上下文
Q14 one platform admin may provision multiple tenants
Q15 platform_admin 可在任意既有 tenant 内 provisioning space；tenant admin 在 P18 不可建 space
Q16 tenant suspended → 常规运行时不可用（控制面可 restore/archive/inspect）
Q17 tenant suspended 后 memberships 保留但运行时 mutation DENY
Q18 P18 不定义 space suspended（schema 不支持）
Q19 archived/deleted space → P17 space membership 操作 DENY；membership 行保留
Q20 resources 保留；控制面只 INSERT projection，不 DELETE，不做 GC
```

## 4. STOP 解决路径

```text
STOP-1 → 新建 uap_control（最小写面：tenants I/U · spaces I/U · roles I · role_permissions I ·
         tenant_memberships I · memberships I · resources I · audit_logs I；无任何 DELETE）
STOP-2 → 控制面在 provisioning 时创建**非 system** 的 tenant/space administrator 角色，
         并绑定既有 canonical permission（不新增 permission · 14 仍为 12 条）
STOP-3 → 全部控制面授权必须版本化、可审计（复用 scripts/privileges 的物化机制，新增
         CONTROL_PLANE 基线；禁止 private GRANT / 手工无源授权）
STOP-4 → P18 不引入 space provisioning/suspended：space 保持 active → archived → deleted；
         create 语义为"事务内直接 active" ⇒ **无 schema gap**
STOP-5 → pre-resource structural authorization：既有 AuthorizationService + 显式 platform scope
         + resource = NULL；要求 actor 具备显式 PLATFORM membership、role = platform_admin、
         permission = admin。若既有引擎无法安全表达该入口：只允许最小 additive capability，
         且必须先用真实 DB 证明；不得新建第二套授权系统，不得写 platform-admin `if` 分支
```

## 5. 实现后果（必须写进 P18 Implementation Contract）

```text
C-1  结构对象 + 资源投影 + 初始管理员（角色 / role_permissions / membership）必须同一事务；
     任一失败（resource / role / role_permissions / membership / audit / DB）⇒ 全量回滚
C-2  逻辑删除不物理删除任何 projection；授权因 lifecycle 非 ACTIVE 而失败（先 gate 后授权）
C-3  audit 写入失败 ⇒ provisioning 回滚（与 P16 execution failure 语义明确区分）
C-4  幂等：natural key（tenants.slug · spaces(tenant_id,key) · resources natural_key）+
     exact-match replay；不匹配 = CONFLICT；不新增 dedup/idempotency 表
C-5  控制面 API 不提供物理 DELETE 端点（使用 PATCH lifecycle/state）
C-6  控制面授权仅 platform_admin（Q15：tenant/space admin 不得创建结构对象）
C-7  未 initialized 的平台不得执行结构化 provisioning（不得自动初始化）
C-8  uap_runtime 权限不变（56 · tenants/spaces SELECT only）；P18 运行时不得使用
     resources INSERT/UPDATE（见 F-P18-S-01）
C-9  API 必须防枚举（授权先于对象细节披露）
C-10 PostgreSQL 错误不得原样返回（映射为稳定应用错误 + 安全诊断日志）
```

## 6. 附带遗留项（登记 · 不在 P18 修）

```text
F-P18-S-01  Residual uap_runtime resource write privilege
            = uap_runtime 仍持有 resources INSERT/UPDATE（P14 基线残留）
            状态：DEFERRED HARDENING DEBT · NOT A P18 ACCEPTANCE BLOCKER
            约束：P18 实现不得使用；不是权限扩张；本版不撤销（避免改动历史安全指纹
                  与历史测试）；未来独立 hardening decision 处理

F-P18-D-01  roles.tenant_id 形状冲突（文本 vs 冻结触发器）
            指令 §14 描述 space administrator role 为
              scope = SPACE · tenant_id = target tenant · space_id = target space
            但冻结触发器 enforce_roles_scope_shape 要求 SPACE 角色
              tenant_id IS NULL 且 space_id IS NOT NULL
            裁定（本文件的规范澄清）：以**冻结 DB 约束**为准 —— space 角色的 tenant 归属
            由 spaces.tenant_id 表达（一个 space 只属于一个 tenant），roles.tenant_id 必须为 NULL。
            该澄清不改变 D05 的实质（非 system · SPACE scope · 绑定目标 space 与目标 tenant 语境），
            与 P17 membership runtime 的既有处理一致。
            Implementation 阶段必须按 §110 先核验实际 role/role_permissions schema。

F-P18-D-02  tenant membership 重邀请语义（唯一键含 removed 行）
            继续继承 P17：re-invite 现有 user → MEMBERSHIP_DUPLICATE
            P18 不修复；future independent decision
```

## 7. 安全债与不变性声明

```text
权限扩张：仅新增 uap_control 控制面写面（被冻结的 ceiling）；uap_runtime 无扩张
schema   ：无变化（P18 migration = NONE · new tables = 0）
event    ：Production Event Allowlist = EMPTY · Handlers = 0
formal DB：uap prestate == poststate（本阶段未触碰）
历史文件 ：未清理、未改写；P14/P15/P16/P17 实现未修改
```

---

## 8. IMPLEMENTATION 阶段新增 blocker（2026-10-01 · OPEN · 未粉饰）

```text
IMPLEMENTATION 轮按 §4–§8（角色 provisioning 发现）与 §11–§14（pre-resource 授权证明）执行，
命中两个 security-baseline blocker ⇒ P18 IMPLEMENTATION = BLOCKED（§197）。
两者均未做 workaround，保持 OPEN 等待 Human Decision。
```

### F-P18-I-01 — ROLE PROVISIONING SOURCE GAP（RESOLVED BY IMPLEMENTATION）

```text
Observation ：仓库不存在任何 PostgreSQL 角色创建机制
              · 代码/迁移/脚本中 CREATE ROLE = 0（仅文档提及）
              · scripts/privileges.py 只 GRANT，不创建角色（自述 no new principal）
              · migrations 0001–0018 无角色 DDL；无 initdb 脚本；无 role provisioning helper
              · 同向历史：P14 记录 CREATE ROLE 为 deployment 动作；OPEN_P10_1 R-06 与 OQ-P14-09 = BLOCKED
Impact     ：uap_control 只能经 manual CREATE ROLE 建立 ⇒ 不可版本化、不可 clean-clone 重现
指令依据    ：§6 / §63 / §148 / §171（versioned source）· §197 · §198 SPECIAL STOP — ROLE CREATION
已避免     ：psql CREATE ROLE · GRANT · SET ROLE · uap_migrator 复用 · superuser 应用路径 ·
             未记录的环境状态
需要裁定    ：D-A（见 P18_IMPLEMENTATION_EVIDENCE.md §6）：在 P18 内新增版本化角色 provisioning 能力 /
             由环境引导提供带来源的角色创建路径 / 明确"环境预置 + 证据形式"
状态        ：**RESOLVED BY IMPLEMENTATION（Human Decision D-A 授权后闭合）**

Resolution（实现细节 · 见 P18_IMPLEMENTATION_EVIDENCE.md §5）：
  · 新增版本化、可审计、clean-clone 可重现的来源：`scripts/role_provisioning.py`
      - 单一权威定义 `CONTROL_PLANE_ROLE`（uap_control：LOGIN · NOSUPERUSER · NOCREATEDB ·
        NOCREATEROLE · NOREPLICATION · NOBYPASSRLS · NOINHERIT）
        与 `CONTROL_PLANE_WRITE` / `CONTROL_PLANE_READ` / `CONTROL_PLANE_FORBIDDEN` 基线
      - 操作：存在性检查 → CREATE ROLE / ALTER ROLE 收敛 → 逐表 + 逐分区 GRANT（幂等）
        → 自校验（missing / unexpected / forbidden / attribute_drift 必须全空）
      - 明确不做：DROP ROLE · REVOKE · SET ROLE · ALTER 其它 principal · 存储任何 secret
      - 应用路径不可达（架构守卫禁止 apps/services/infrastructure/core 引用该模块）
      - CLI：`python -m scripts.role_provisioning --dsn <admin-dsn> [--verify-only]`
  · 执行（操作员步骤 · 非应用路径）：`uap_control` 已在本集群创建并物化 CONTROL_PLANE 基线，
    verify ok=True（missing/unexpected/forbidden/attribute_drift 全空）
  · 边界实测（以 uap_control 身份 · 全部回滚）16 项检查 0 mismatch：
      拒绝 = SET ROLE uap_migrator / uap_bootstrap · CREATE TABLE（DDL） ·
              DELETE audit_logs / tenant_memberships / memberships / resources ·
              INSERT permissions / platform_memberships / resource_permissions
      允许 = INSERT/UPDATE tenants · INSERT spaces · INSERT audit_logs ·
              SELECT tenants / platform_state
  · 未新增 permission / 角色语义 · 未新增 migration（head 仍 0018）· 未触碰其它 principal
```

### F-P18-I-02 — PRE-RESOURCE AUTHORIZATION GAP（RESOLVED BY IMPLEMENTATION）

```text
Observation ：既有 canonical AuthorizationService 无法评估 platform scope + resource = None
              实测（一次性探针库 · 真实 engine）：
                platform actor  + admin  + resource=None → EXCEPTION AttributeError（'NoneType' … 'type'）
                non-platform    + admin  + resource=None → 同异常
                platform actor  + create + resource=None → 同异常
              即不产生 Decision，异常逃出 engine（违反其 fail-closed 自述契约）
Impact     ：P18-D06 冻结的 pre-resource structural authorization 目前不可执行
指令依据    ：§11–§14 · §199 SPECIAL STOP — AUTHORIZATION · §197（resource=None authorization unavailable）
已避免     ：invent resource / permission / role · platform_admin if 分支 · 第二套授权引擎 ·
             修改 P17 授权语义
需要裁定    ：D-B：授权对既有 AuthorizationService 的最小 additive capability（platform scope +
             resource=None 的显式支持 + 契约测试），或改用其它既有语义的可表达方式
状态        ：**RESOLVED BY IMPLEMENTATION（同一轮内闭合）**

Resolution（实现细节 · 见 P18_IMPLEMENTATION_EVIDENCE.md §3）：
  · 依 P18-D06 的授权（"仅允许对既有 AuthorizationService 做最小 additive capability"），
    对 canonical AuthorizationService 做**纯新增**能力：
      - `AuthorizationService.authorize()` 新增唯一入口分支：`request.resource is None`
      - 新增 `PermissionResolver.platform()`：仅 PLATFORM-scope 角色授权可参与，
        permission 必须同时匹配 action 与调用方**显式声明**的 resource_type
      - 未声明 resource_type ⇒ 明确 DENY（`pre-resource-requires-declared-resource-type`）
      - ACL 层 abstain（无资源实例）· policy 层照常评估（只能收紧）· 默认 DENY
      - `AuditBoundary` 与 `_finish` 对无资源实例的决策做 None-safe 记录
    未新增 resource grammar / permission / role / 第二套引擎；无 platform_admin if 分支
  · 证明（真实 DB · 一次性库；授权层只读，以 uap_runtime 作为 uap_control 等价的读取语境）：
      platform actor + admin + resource=None + resource_type=tenant → ALLOW
      non-platform actor 同请求                                     → DENY
      任何组合均返回 Decision（不再有异常逃逸）
      canonical CRUD 动作（create/update/delete）仍无结构授权        → DENY
      未声明 resource_type                                          → 干净 DENY
  · 回归：P17 97/0 · 新增 P18 14/0 · 授权引擎单元/契约 122/0 · 架构守卫 61/0 ·
          P16 单元+安全 24/0 与集成 8/0 · P15 65/0（详见 evidence §4）
```

```text
本轮未创建 uap_control 角色 / 未 GRANT / 未 migration / 未创建测试数据；
唯一代码变更 = P18-D06 授权的最小 additive 能力（services/authorization/* · 纯新增路径）；
Formal DB 未变；Git 基线未变（HEAD 9fe282b0 = origin/main · staged = 0 · 未 commit / tag / push）。
```

---

## 9. F-P18-I-03 CONSISTENCY GATE（2026-10-01 · **OPEN · 阻塞 Wave 3/4/D14 继续**）

```text
触发依据：P18 IMPLEMENTATION（Wave 3→4→D14）指令 §1–§4「FIRST TASK — F-P18-I-03 CONSISTENCY GATE」
状态    ：OPEN（未闭合 · 未粉饰）；在裁定前 Wave 3 收尾 / Wave 4 API / D14 agent gate 全部暂停
```

### 9.1 original condition

```text
§7（实现指令）冻结表述：
  before object exists → resource=None → declared resource_type
  object already exists → canonical resource
同时 §48/§49 冻结：uap_control 对 resource_permissions / acl_subject_types **无任何权限**（绝对禁止）
实测（本次取证）：
  has_table_privilege('uap_control','resource_permissions','SELECT') = false
  has_table_privilege('uap_control','acl_subject_types','SELECT')  = false
  has_table_privilege('uap_runtime','resource_permissions','SELECT') = true
  uap_control 授权总数 = 23（= 冻结 ceiling）
```

### 9.2 frozen requirement

```text
必须同时满足：① 使用 canonical AuthorizationService ② P18-D06 platform-admin-only
              ③ uap_control 最小权限（§48/§49）④ 冻结 resource 语义（§7）
```

### 9.3 observed implementation（当前工作区 · 未提交）

```text
services/use_cases/control_plane.py::_authorize 目前对**所有**控制面操作使用
pre-resource 平台 scope 入口（resource=None），对象身份仅用于 use-case 校验与审计关联。
该实现**尚未被判定为合规**：它正是 §2 明令禁止的「直接把 all control operations → resource=None
当作已满足冻结契约」的做法，因此在 I-03 裁定前不得作为已接受语义。
```

### 9.4 判定（按指令 §3 的 A/B 条件）

```text
A（保持 canonical resource path 且 uap_control 不读 ACL 表，且真实 DB 授权可完成）
  = **不成立**（真实 DB 取证）：
    existing-object 授权实测结果
      decision = DENY
      reason   = authorization-unavailable:(psycopg.errors.InsufficientPrivilege)
                 permission denied for table resource_permissions
    即 canonical 引擎的 ACL 层必然读取 resource_permissions + acl_subject_types，
    而 uap_control 对这两张表无任何权限 ⇒ 资源侧授权在该 ceiling 下**不可执行**。
    （若要让 A 成立，只能新增 SELECT 到 resource_permissions/acl_subject_types
      → 属新 privilege surface ⇒ §200 要求 STOP，未执行）

B（冻结文本已明确规定「control-plane authorization 仅 platform scope；resource identity 属
   审计/用例上下文」）
  = **部分证据、不足以断言"已明确规定"**：
    · 附录 Z / D13 冻结的**读面 ceiling**（users·tenants·spaces·roles·permissions·
      role_permissions·tenant_memberships·memberships·platform_state·platform_memberships·
      resources）**不含 ACL 两表** —— 与"控制面决策不读 ACL"一致；
    · 但冻结文本（附录 Z · D06）只写明了 **pre-resource（对象创建前）** 的 platform scope 形式，
      未明文写明 **existing-object** 操作也使用 platform scope。
    ⇒ 属**可由 ceiling 推出的解释**，而非明文冻结语句；按 §3 要求不能由 BOT 自行认定。
```

```text
结论：A 不成立、B 不充分 ⇒ 按 §2/§3 必须 STOP，登记 F-P18-I-03 consistency blocker，
      不得静默改写冻结语义，不得新增 privilege。
```

### 9.5 remaining risk

```text
· 若最终选择 B（冻结澄清为 platform-scope only）：需在 PDL append-only 中记录该澄清
  （由 Human Decision 产生），control-plane 用例的 resource id 仅用于审计关联。
· 若最终选择 A 变体（保留 resource 侧授权）：必须解决"谁执行 ACL 读取"——
  例如由**独立只读授权引擎/主体**（如既有 uap_runtime 已持 ACL SELECT）承担决策读取，
  而写入仍属 uap_control；这属新的架构决定（第二 principal 进入控制面请求路径），
  同样需要 Human Decision；且不得复用 uap_migrator / 不得 SET ROLE。
· 任何路径都不得：新增 ACL 写权限 · 绕过 canonical 引擎 · role-name 判定 · 静默降级。
```

### 9.6 I-03 裁定结果（2026-10-01 · Human Decision B′）

```text
裁定 = B′（明文冻结 · PDL 附录 AA / P18-AUTH-CLARIFICATION-01）
内容 = Control Plane 的所有授权决策一律采用 PLATFORM scope；
       resource / object identity 仅作为审计与用例上下文，不参与资源侧授权决策。
约束 = 不得新增 ACL 读取权限 · 不得引入第二授权主体/引擎 · 不得改造 uap_control ceiling
状态 = F-P18-I-03 = RESOLVED BY HUMAN DECISION（Wave 3/4/D14/Wave 5 据此恢复执行）
```

---

## 10. F-P18-I-04 CONTROL API AUTHENTICATION PRINCIPAL（2026-10-01 · **RESOLVED BY HUMAN DECISION + IMPLEMENTATION**）

```text
Observation：Wave 4 控制面 API（apps/api/routes/control_plane.py）已实现为
             transport-only（authenticate_actor → use case → error mapping）。
             但其 actor 认证复用 P17 的会话校验（读取 sessions / devices / identities），
             而这三张表在 §44/§49 对 uap_control 属禁止面（实测无任何权限）。
             ⇒ 在 uap_control 单一连接下无法完成 HTTP 认证。
Impact     ：控制面 API 的 HTTP 端到端验证（Wave 5 API 用例）暂不可执行；
             进程内 use-case 层已全部实测通过（uap_control 执行）。
候选裁定   ：① 主体分离：认证走应用身份（既有 DATABASE_URL），结构写走 uap_control
               —— 需要新增控制面 DSN/引擎配置（配置面变更，非权限面）
             ② 或为 uap_control 增加 sessions/devices/identities SELECT
               —— 属 ceiling 变更（§200 要求 STOP + 新决策）
裁定       ：Human Decision = **OPTION ①**（认证走既有应用身份/会话边界；结构写走专用 uap_control）
             明确禁止 Option ②（禁止向 uap_control 增加 sessions/devices/identities SELECT）
实现       ：· config/settings.py 新增 `CONTROL_DATABASE_URL`（空 ⇒ 控制面 API 不可用，返回 503）
             · apps/api/main.py lifespan 构建并启动专用控制面 RuntimeDatabase（require_role=uap_control）
             · apps/api/dependencies.py::get_control_database（未配置 ⇒ 503，绝不借用其它主体）
             · apps/api/routes/control_plane.py：认证用 `get_database`（应用/runtime 身份），
               结构写用 `get_control_database`（uap_control）
实测证据   ：tests/integration/test_p18_control_api_http.py（5/0）
             · runtime 引擎 current_user = uap_runtime；control 引擎 current_user = uap_control
             · HTTP POST /control/tenants → 201（tenant active）· GET/PATCH → 200 · lifecycle suspend → 200
             · 审计 actor = 已认证用户 id（≠ uap_control）
             · 幂等重放 replayed=true · 冲突 409 · 未认证 401 · 非平台用户 403 · 无 DELETE 端点（404/405）
             · 未配置 CONTROL_DATABASE_URL ⇒ 503（不降级、不借用主体）
权限面     ：uap_control = 23 grants（未变）· uap_runtime = 56（未变）· 未新增任何权限
状态       ：RESOLVED（无剩余风险项；Wave 4 HTTP 端到端与主体验分离均已验证）
```

**END OF P18 CONTROL PLANE GAP RECORD（STOP-1/3/4/5 + initial-role blocker = RESOLVED BY HUMAN DECISION · F-P18-S-01 = deferred security debt · F-P18-I-01 = RESOLVED（D-A）· F-P18-I-02 = RESOLVED（最小 additive 能力）· **F-P18-I-03 = RESOLVED BY HUMAN DECISION（附录 AA · B′）** · **F-P18-I-04 = OPEN（控制面 API 认证主体 · HTTP 端到端待裁定）** · 原始 observation 与 STOP 保留；2026-10-01）**
