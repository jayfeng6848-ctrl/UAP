# P18 IMPLEMENTATION EVIDENCE

```text
阶段        = P18 IMPLEMENTATION → VALIDATION → EVIDENCE（NO ACCEPTANCE / NO RELEASE）
结果        = 无 blocker（两个 blocker 均已闭合）· 实现**未完成**（Wave 1–5 尚未开始）
基线        = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME
              HEAD = origin/main = 9fe282b009aba3965236402971ab963694f7ce05
权威        = PDL 附录 Y（P18 PREP）· 附录 Z（P18 HUMAN DECISION FREEZE）
              + P18_CONTROL_PLANE_TENANT_SPACE_LIFECYCLE_IMPLEMENTATION_CONTRACT.md（FROZEN）
              + Human Decision D-A（授权新增版本化 role provisioning 能力）
日期        = 2026-10-01
```

---

## 0. 本轮结论

```text
F-P18-I-01  ROLE PROVISIONING SOURCE GAP = RESOLVED BY IMPLEMENTATION（D-A 授权）
            新增版本化、可审计、clean-clone 可重现的 role provisioning 来源；
            uap_control 已创建，CONTROL_PLANE 最小权限基线已物化并通过自校验与边界实测。

F-P18-I-02  PRE-RESOURCE AUTHORIZATION GAP = RESOLVED BY IMPLEMENTATION（P18-D06 授权）
            对既有 canonical AuthorizationService 增加唯一 additive 入口
            （resource=None ⇒ platform-scope 决策），真实 DB 证明 + 全量回归。

因此：**当前无 blocker**；但 P18 实现尚未完成 —— Wave 1–5
（control-plane persistence / provisioning transaction / lifecycle / API / tests）尚未开始。
本轮不进入 Acceptance / Release。
```

---

## 1. 已实现（1）— control-plane role provisioning（D-A 授权）

```text
新增文件：scripts/role_provisioning.py（**唯一**版本化来源 · 非 Alembic 迁移）
  · CONTROL_PLANE_ROLE = uap_control
      LOGIN · NOSUPERUSER · NOCREATEDB · NOCREATEROLE · NOREPLICATION · NOBYPASSRLS · NOINHERIT
      （INHERIT=false 与既有 uap_runtime / uap_bootstrap 约定一致）
  · CONTROL_PLANE_WRITE（P18-D13 写面 ceiling · 无任何 DELETE）
      tenants I,U · spaces I,U · roles I · role_permissions I · tenant_memberships I ·
      memberships I · resources I · audit_logs I
  · CONTROL_PLANE_READ（由控制面查询图推导）
      users · tenants · spaces · roles · permissions · role_permissions ·
      tenant_memberships · memberships · platform_memberships · platform_state · resources
  · CONTROL_PLANE_FORBIDDEN（任何权限都不允许）
      acl_subject_types · credentials · identities · sessions · devices · tools · tool_versions ·
      tool_executions · agent_* · ai_* · events · resource_permissions
  · 操作：存在性检查 → CREATE ROLE / ALTER ROLE 收敛 → 逐表 + 逐分区 GRANT（幂等、additive）
          → 自校验（missing / unexpected / forbidden / attribute_drift 必须全空）
  · 明确不做：DROP ROLE · REVOKE · SET ROLE · ALTER 其它 principal · 存储任何 secret
  · 应用路径不可达：架构守卫禁止 apps / services / infrastructure / core 引用该模块
  · CLI：python -m scripts.role_provisioning --dsn <admin-dsn> [--verify-only]

执行（操作员步骤 · 环境引导 · **非应用路径** · 无 SET ROLE · 未使用 uap_migrator）：
  python -m scripts.role_provisioning --dsn postgresql+psycopg://<admin>@localhost:5432/uap_b1_test
  → principal=uap_control · observed_grants=23 · missing=[] · unexpected=[] · forbidden=[]
    attribute_drift=[] · ok=True
```

## 2. 权限边界实测（以 uap_control 身份 · 全部回滚 · 16 项 0 mismatch）

```text
拒绝（DENIED）：
  SET ROLE uap_migrator · SET ROLE uap_bootstrap · CREATE TABLE（DDL）·
  DELETE audit_logs / tenant_memberships / memberships / resources ·
  INSERT permissions / platform_memberships / resource_permissions
允许（ALLOWED）：
  INSERT/UPDATE tenants · INSERT spaces · INSERT audit_logs ·
  SELECT tenants · SELECT platform_state
```

---

## 3. 已实现（2）— pre-resource 授权能力（P18-D06 授权 · 纯新增）

```text
services/authorization/service.py
  · authorize() 新增唯一分支：request.resource is None ⇒ _authorize_pre_resource()
  · 要求调用方在 Action 上显式声明 resource_type，否则 DENY
    （reason = pre-resource-requires-declared-resource-type）
  · subject 以 tenant_id=None / space_id=None 解析（只可能得到 PLATFORM 角色授权）
  · RBAC 仅取 PLATFORM-scope 授权；ACL 层 abstain（无资源实例）；policy 层照常评估（只能收紧）
  · _finish() 对无资源实例的决策做 None-safe 审计字段处理
services/authorization/permissions.py
  · 新增 PermissionResolver.platform(resolved, action, *, resource_type)：
      仅 PLATFORM-scope 授权可参与；permission 必须同时匹配 action 与声明的 resource_type；deny 优先
services/authorization/audit.py
  · AuditBoundary.record() 支持无资源实例的决策（记录声明类型、无资源 id）

未新增：resource grammar · permission · role · 第二套引擎 · platform_admin if 分支 ·
        role name 字符串判定 · 任何 GRANT / SET ROLE
既有语义：未改动 —— resource 非 None 的请求路径不变（引擎自身 122 项单元/契约套件验证）
```

## 4. 证明与回归（本轮全部实测）

```text
pre-resource 授权证明（真实 DB · 一次性库 uap_p18_authz_test，运行后 DROP；以 uap_runtime 作为
uap_control 等价的**读取**语境）：
  platform actor + admin + resource=None + resource_type=tenant → ALLOW
  non-platform actor 同请求                                    → DENY
  任意组合                                                     → 返回 Decision（无异常逃逸）
  canonical CRUD（create/update/delete）                        → DENY（结构授权沿用 admin）
  未声明 resource_type                                          → DENY

回归：
  授权引擎单元/契约（test_authorization_* ×5 + contract）  = 122 passed / 0 failed
  P18 新增（unit 9 + integration 5 + arch 6）              = 20 passed / 0 failed
  P17 显式 allowlist（8 文件）                             = 97 passed / 0 failed
  架构守卫（含 6 项新增 P18 守卫）                          = 63 passed / 0 failed
  P16 单元 + 安全 = 24/0 · P16 集成 = 8/0 · P15 = 65/0
  Core → Domain = 0 · forbidden tests = 0 · skip / xfail / deselect = 0
```

## 5. 环境修复记录（测试库 · 非正式库）

```text
为分类一次回归运行了 P13 时代的 tests/security/test_authorization_security.py（**不在任何 allowlist**、
属历史脏文件）。该套件在 fixture 阶段就 DROP/CREATE 共享测试库 uap_b1_test 并直接写受触发器保护的
acl_subject_types，因此 26 项 error 出现在 fixture（失败在任何授权调用之前，由 DB 触发器
enforce_acl_subject_types_protect 拒绝），与本轮变更无关。

其后 uap_b1_test 已恢复并再次物化：
  alembic upgrade 0017_p13_seed + scripts.privileges.materialize() + 补齐 202609 月分区
  实测：revision=0017_p13_seed · permissions 12 · roles 1 · tenants/spaces/resources/users 0 ·
        uap_runtime = 56 · uap_migrator = 245 · default ACL = 0
        （uap_app = 7，随 audit_logs 月分区数量变化；属 §88 承认的月分区维护，非 P18 权限变更）
  P15（65/0）与 P16 集成（8/0）均在该库上复跑通过；正式库 uap 未触碰（public 表 0）。
```

## 6. 尚未完成（诚实记录）

```text
Wave 1  control-plane persistence（repository · scope-explicit）      = NOT STARTED
Wave 2  provisioning transaction（tenant/space + 投影 + 初始管理员）    = NOT STARTED
Wave 3  lifecycle（suspend/restore/archive/delete + metadata/visibility）= NOT STARTED
Wave 4  control-plane API（/control/... · 无删除端点 · 防枚举）          = NOT STARTED
Wave 5  P18 测试矩阵（正/负/半初始化/幂等/生命周期/agent gate/API）      = NOT STARTED
D14     P17 runtime lifecycle gate（非 ACTIVE ⇒ context/membership DENY） = NOT STARTED
migration / 新表 / 新 permission / event 激活                            = 未发生（符合冻结）
```

## 7. 状态

```text
P18 IMPLEMENTATION = 未完成（无 blocker；Wave 1–5 + D14 待实现）
P18 ACCEPTANCE     = NOT EXECUTED
P18 RELEASE        = NOT AUTHORIZED
P19 / Business Modules / Event Activation = NOT STARTED
HARD STOP          = ACTIVE
```

---

## 8. 本轮续做：Wave 1 / Wave 2 / Wave 3（部分）/ D14

```text
Wave 1 — control plane persistence                     = DONE
  services/control_plane/repository.py（scope-explicit · 无 generic get_by_id / list_all）
    platform state · tenant by slug/id · space by (tenant, key)/id · user status ·
    role find/insert · role_permissions bind/read · membership read/insert ·
    resource id lookup · lifecycle state read · metadata/status writes（rowcount + expect）
  services/control_plane/errors.py（additive P18 error taxonomy）

Wave 2 — provisioning transaction                       = DONE
  services/use_cases/control_plane.py :: provision_tenant / provision_space
    单一逻辑事务：authorization → bootstrap/initial-admin/前置校验 → tenant(provisioning)
    → 管理员角色（非 system · 作用域匹配）+ role_permissions(member.read/member.admin/tenant.admin
      或 space.admin/member.read/member.admin) → P17 资源投影（tenant/space + member 集合）
    → 初始 membership → audit → status=active（rowcount 必须为 1）→ COMMIT
    幂等：自然键 exact replay（同 slug/name/admin 且 active）；不一致 ⇒ CONFLICT
    失败：任一步异常 ⇒ 整事务回滚（无半初始化残留）

Wave 3 — lifecycle（部分）                              = PARTIAL
  transition_tenant / transition_space：冻结迁移矩阵（tenant：active↔suspended ·
    active/suspended→archived · archived→active · archived→deleted · deleted=terminal；
    space：active↔archived · archived→deleted · deleted=terminal）+ rowcount expect + audit
  未做：metadata/visibility 更新的 use-case 包装（repository 层已具备）与其审计

D14 — runtime lifecycle gate                            = DONE（context/membership）
  services/identity_runtime/resolver.py：仅 ACTIVE Tenant / ACTIVE Space 可建立普通运行时上下文
  （tenant suspended/archived/deleted ⇒ TENANT_NOT_ACTIVE；space archived/deleted ⇒ SPACE_NOT_ACTIVE）
  membership 行保留、无级联删除；P17 membership 操作同样被该门禁覆盖
  未做（下一轮）：P16 Agent Run admission 门禁（§41）
```

## 9. 本轮新增证据

```text
tests/integration/test_p18_control_plane_provisioning.py（9 项 · 以 uap_control 身份 · 一次性库）
  tenant provisioning 完整性（tenant active · 角色 shape/权限集合 · 两类资源投影 · membership · audit）
  exact replay · conflict
  space 前置（初始管理员必须已属 tenant）· space provisioning 完整性（SPACE 角色 tenant_id NULL）
  非 platform actor ⇒ AUTHORIZATION_DENIED 且零写入
  lifecycle 迁移矩阵 + D14 门禁（suspended ⇒ runtime context DENY；恢复后可读）
  space archived ⇒ SPACE_NOT_ACTIVE
  audit 原子性（审计写入失败 ⇒ 整事务回滚 · 独立连接确认无残留）
  audit append-only（uap_control UPDATE/DELETE 均被拒绝）

回归（本轮实测）：
  P17 allowlist 8 文件 = 97/0 · 架构守卫 = 63/0（含 6 项 P18 守卫）
  P18 新增 = 23/0（unit 9 + integration 9 + integration(authz) 5）
  P15 = 65/0 · P16 单元+安全 = 24/0 · P16 集成 = 8/0 · Core → Domain = 0 · forbidden = 0
  为 D14 同步更新：tests/unit/test_p17_identity_runtime.py（fake 行补 status）·
  tests/architecture/test_p17_boundaries.py（runtime provisioning 守卫排除 control-plane use case）
```

## 10. 本轮新增发现

```text
F-P18-I-03  CONTROL-PLANE AUTHORIZATION EXPRESSION（RESOLVED BY DESIGN · 已记录）
  Observation：§7 要求"对象已存在时用 canonical resource 授权"，但 canonical 引擎的 ACL 层会读取
               resource_permissions / acl_subject_types —— 这两张表在 §49 属**绝对禁止**，
               uap_control 无任何权限 ⇒ resource 侧授权必然 AuthorizationUnavailable ⇒ DENY。
  Resolution ：控制面权威统一通过冻结的 pre-resource 平台 scope 入口表达（D06 = platform_admin-only）；
               对象身份由 use-case 在同一事务内校验（tenant/space 存在 · 状态 · 归属），
               resource id 仅用于审计关联，不参与决策。
  边界保持   ：未新增任何 privilege（ceiling 未变）· 未绕过 canonical engine · 未做 role-name 判定 ·
               未降低 §48/§49 约束。§200（额外 SELECT 需求 ⇒ STOP）因此未触发。
```

---

## 11. F-P18-I-03 CONSISTENCY GATE — 本轮判定与暂停（OPEN）

```text
依据：本轮指令 §1–§4（FIRST TASK — F-P18-I-03 CONSISTENCY GATE）
判定：A 不成立；B 证据不足（详见 P18_CONTROL_PLANE_GAP_RECORD.md §9）
动作：按 §2/§3 STOP —— 不再继续 Wave 3 收尾 / Wave 4 API / D14 agent gate / Wave 5 完整矩阵
      （本轮未新增任何实现代码；上一轮的 Wave 1/2/D14 成果保持原状、未提交）
```

```text
original condition
  §7：before object exists → resource=None；object already exists → canonical resource
  §48/§49：uap_control 对 resource_permissions / acl_subject_types 无任何权限（绝对禁止）

frozen requirement
  ① canonical AuthorizationService ② D06 platform-admin-only ③ uap_control 最小权限 ④ 冻结 resource 语义

observed implementation（未提交）
  services/use_cases/control_plane.py::_authorize 目前对所有控制面操作使用 platform scope + resource=None；
  **该实现尚未被判定合规**（正是 §2 禁止的"未证明即统一改写"），对象身份仅用于 use-case 校验与审计。

evidence（真实 DB）
  has_table_privilege('uap_control','resource_permissions','SELECT') = false
  has_table_privilege('uap_control','acl_subject_types','SELECT')    = false
  uap_control 授权总数 = 23（冻结 ceiling · 未变）
  existing-object canonical-resource 授权实测：DENY · authorization-unavailable:
    (psycopg.errors.InsufficientPrivilege) permission denied for table resource_permissions
  ⇒ A 不成立（资源侧授权在冻结 ceiling 下不可执行）

resolution
  PENDING HUMAN DECISION（两个候选，均需 Human Decision 记录）：
   B' 冻结澄清：control-plane authorization 仅 platform scope，resource identity 属审计/用例上下文
      （append-only 记录于 PDL；与 D13 读面 ceiling 一致，但当前冻结文本未明文写明 existing-object 情形）
   A' 保留 resource 侧授权：由**独立只读授权主体**（例如已持 ACL SELECT 的 uap_runtime）执行决策读取，
      写入仍属 uap_control（第二 principal 进入控制面请求路径 ⇒ 新的架构决定；不得用 uap_migrator / SET ROLE）

remaining risk
  在裁定前，控制面 existing-object 授权语义处于"未认定"状态；
  Wave 3/4/D14 的后续实现与 Wave 5 完整矩阵相应暂停，避免把未冻结语义固化进代码与测试。
```

---

## 12. B′ 之后：Wave 3 收尾 / Wave 4 / D14 agent gate / Wave 5（本轮）

```text
B′ 裁定（PDL 附录 AA）：Control Plane 所有授权决策一律 PLATFORM scope；
                        resource / object identity 仅作审计与用例上下文。
⇒ F-P18-I-03 = RESOLVED BY HUMAN DECISION；以下实现据此恢复并完成。

Wave 3 收尾 = DONE
  services/use_cases/control_plane.py：update_tenant_metadata（display_name/plan/region）·
    update_space_metadata（name/visibility/owner_id）· read_tenant / read_space
    （授权先于披露；空 payload ⇒ INVALID_INPUT；非法 visibility ⇒ INVALID_INPUT；rowcount=1 强制）
  repository：update_space_metadata 增补 owner_id（owner 语义 = 元数据，非授权）

D14 agent gate = DONE
  services/identity_runtime/agent_scope.py::require_active_agent_scope（复用 P17 agent scope 解析 +
    tenant/space ACTIVE 检查；inactive ⇒ TENANT_NOT_ACTIVE / SPACE_NOT_ACTIVE，无 owner/platform 回落）
  services/agent/use_cases.py::run_agent 在 admission 前执行该门禁（additive；
    active 场景 P16 语义逐字不变 —— P16 集成 8/8 复验通过）

Wave 4 Control API = IMPLEMENTED（HTTP 端到端待裁定 · F-P18-I-04）
  apps/api/routes/control_plane.py（/control 命名空间 · transport-only）：
    POST /control/tenants · GET/PATCH /control/tenants/{id} · POST /control/tenants/{id}/lifecycle
    POST /control/spaces · GET/PATCH /control/tenants/{t}/spaces/{s} ·
    POST /control/tenants/{t}/spaces/{s}/lifecycle
    无任何 DELETE 端点 · 无通用 CRUD · 授权全部在 use-case 内经 canonical 引擎
  apps/api/error_mapping.py：ControlPlaneError → 既有 taxonomy（authorization/conflict/validation/persistence）
  阻塞：actor 认证复用的 P17 会话校验需读 sessions/devices/identities，而这三表属 uap_control 禁止面
        ⇒ 需主体分离（认证走应用身份）或 ceiling 变更 → F-P18-I-04（未新增任何权限）

Wave 5（本轮部分）= PARTIAL
  tests/integration/test_p18_control_plane_metadata_and_gate.py（5）：
    tenant metadata 更新 + 审计（fields 精确）· 空 payload 拒绝 · space visibility 更新 + 审计 +
    不产生 membership/role/ACL · 非法 visibility 拒绝 · D14 agent gate（active ⇒ 通过；
    tenant suspended ⇒ TENANT_NOT_ACTIVE；space archived ⇒ SPACE_NOT_ACTIVE）
```

## 13. 本轮回归（实测）

```text
P17 allowlist 8 文件 = 97/0 · 架构守卫 = 63/0 · Core → Domain = 0
P18 新增 = 28/0（unit 9 · authz 5 · provisioning 9 · metadata+gate 5）
P15 = 65/0 · P16 单元+安全 = 24/0 · P16 集成 = 8/0
为 B′/D14 同步更新：tests/architecture/test_p17_boundaries.py（control-plane 为 provisioning 唯一合法调用点）
未新增 privilege（uap_control 仍 23 grants）· 未新增角色/表/migration（head 仍 0018）· event EMPTY · handlers 0
```

---

## 14. F-P18-I-04 实现完成（OPTION ① · 主体验分离）

```text
裁定：认证走既有应用身份/会话边界；结构写走专用 uap_control（禁止 Option ②，禁止新增任何权限）
实现：
  config/settings.py              新增 CONTROL_DATABASE_URL（空 ⇒ 控制面 API 不可用）
  apps/api/main.py                lifespan 启动专用控制面 RuntimeDatabase(require_role=uap_control)
  apps/api/dependencies.py        get_control_database（未配置 ⇒ 503；绝不借用其它主体）
  apps/api/routes/control_plane.py 认证 = get_database（应用身份）· 结构写 = get_control_database
证据（tests/integration/test_p18_control_api_http.py · 5/0）：
  runtime 引擎 current_user = uap_runtime ；control 引擎 current_user = uap_control
  HTTP：POST /control/tenants 201 · GET/PATCH 200 · lifecycle 200 · 幂等 replayed=true ·
        冲突 409 · 未认证 401 · 非平台用户 403 · 无 DELETE 端点（404/405）· 未配置 DSN ⇒ 503
  审计 actor = 已认证用户（≠ uap_control）
权限面：uap_control 23 grants（未变）· uap_runtime 56（未变）· 未新增权限/角色/表/migration
```

## 15. Wave 5 复验（本轮最终）

```text
P17 allowlist（8 文件） = 97/0　·　P18 全部新增 = 33/0
  单元 9 · 授权集成 5 · provisioning 9 · metadata+gate 5 · HTTP 端到端 5
架构守卫 = 63/0（Core → Domain = 0）　·　P15 = 65/0
P16 单元+安全 = 24/0　·　P16 集成（6 场景 + durability）= 8/0
forbidden tests = 0 · OI-G-4 = 0 · skip/xfail/deselect = 0
Formal DB（uap） = public 表 0（未触碰）· DBs = uap / uap_b1_test / uap_test（临时库已清理）
Git = HEAD 9fe282b0 = origin/main · tags 15 · staged 0 · 无 0019 · 未 commit / tag / push
```

**END OF P18 IMPLEMENTATION EVIDENCE（F-P18-I-01/02/03/04 = RESOLVED · 无 blocker · Wave 1–4 + D14 完成 · P18 = ACCEPTANCE READY · 未 migration / 未 commit；2026-10-01）**
