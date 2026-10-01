# P18 HUMAN DECISION PREP

# PLATFORM CONTROL PLANE / TENANT-SPACE LIFECYCLE

# PREP ONLY — NO IMPLEMENTATION

```text
性质        = PREP ONLY（只读勘验 + 决策输入；NOT FROZEN · NOT AUTHORIZED）
基线        = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME = RELEASED
              commit 9fe282b009aba3965236402971ab963694f7ce05
              tree   de420083cbb3fa01b77e7d4d0cc7c317bebba06c
              tag object 1327828f884f18dd537ea2898096261449009f51
权威        = PLATFORM_DECISION_LOG.md 附录 A–X（本次仅 append 附录 Y）
              + P17 Implementation Contract / Evidence / Acceptance / Release Record
证据来源     = 实测 schema + pg_catalog + information_schema（uap_b1_test · 只读）
              + 仓库代码只读检索
日期        = 2026-10-01
```

---

## 0. 本轮结论摘要

```text
P18 PREP = PASS（勘验完成；决策矩阵与 OQ 已就绪）
但勘验同时触发 4 项必须由 Human Decision 裁定的 STOP 条件：
  STOP-1  uap_bootstrap 缺少结构写权限（tenants/spaces/resources 均无 INSERT）
          → 控制面写权限属"新 privilege surface"，必须 Human Decision（不得自行 GRANT）
  STOP-2  平台不存在任何 eligible TENANT/SPACE 角色
          （全新平台 roles 仅 1 行：platform_admin · PLATFORM · is_system=true）
          → 首个 tenant/space 管理员无法在不新建角色 taxonomy 的前提下成立（§90 STOP）
  STOP-3  control-plane principal 的既有授权（uap_bootstrap 3 项 · uap_seed 0 项）
          在仓库中**没有任何版本化来源**（migrations/scripts 均无）→ 环境态
          → 需要新的 materialization 决策（与 F-P16-I-04 同类）
  STOP-4  Space 生命周期状态与 Tenant 不一致（spaces.status 无 provisioning / suspended）
          → 若 P18 需要 space suspend/provisioning 语义，属 schema gap（PREP 不得建 migration）
```

```text
本轮：不写代码 / 不建 migration / 不建表 / 不 DML / 不 GRANT / 不 commit / 不 tag / 不 push
     Formal DB（uap）= 0 public 表，prestate == poststate
     Production Event Allowlist = EMPTY · Handlers = 0
     Core → Domain = 0
```

---

## 1. Git baseline（本轮开始与结束一致）

```text
HEAD        = 9fe282b009aba3965236402971ab963694f7ce05（= origin/main）
tags        = 15（最新 UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME · annotated）
staged      = 0
tracked_mod = 28（历史脏文件 · 未触碰）
untracked   = 105（历史未跟踪文件 · 未触碰）
本轮新增    = docs/architecture/P18_*.md（仅文档）
```

---

## 2. Decision inheritance matrix（P13 → P18）

| 版本 | 冻结内容（继承，不得改动） | 对 P18 的约束 |
|---|---|---|
| P13 | canonical permission 词表 12 条 · `acl_subject_types` 3 行 · `platform_admin × 12 allow` | P18 不得新增 permission / 不得改 seed；结构生命周期不得变成新 permission taxonomy |
| P14 | DB 信任边界 · 6 个 uap* 主体 · `uap_runtime` 最小面（56 grants）· default ACL 0 | 结构写属于 control-plane 面，不得扩大 `uap_runtime` |
| P15 | Event/consumer 基础 · Production Allowlist = EMPTY | P18 不得激活 event / handler |
| P16 | Agent runtime · Agent ≠ User · ToolGate 单一授权路径 · 0018 为 head | 结构生命周期不得走 Agent/Tool 面向；0018 不得修改 |
| P17 | Identity/Tenant/Space runtime · membership runtime · 资源投影前置条件 · `member.read`/`member.admin` · cross-tenant/space DENY · audit 原子 | P18 必须接续"runtime 之前"的结构段；不得改 runtime 语义 |
| **P18** | 待裁定（见 §10 决策矩阵） | 本轮不冻结任何 P18 决策 |

---

## 3. Boundary inventory（只读实测）

### 3.1 Runtime（P17，已发布）

```text
拥有：context resolution · tenant/space read · tenant/space membership read/write ·
      canonical authorization 调用 · audit · agent scope 解析
DB 主体：uap_runtime（56 grants；tenants/spaces = SELECT only；resources = SELECT/INSERT/UPDATE）
代码：services/identity_runtime/* · services/use_cases/identity_runtime.py ·
      apps/api/routes/identity_runtime.py
不得变成：Tenant/Space Provisioner · Schema Administrator · Role/Permission Seed Engine
实测确认：仓库中没有任何 runtime 路径创建 tenant/space（grep = 0）
```

### 3.2 Control Plane（当前仅存在 P17 引入的 capability）

```text
代码：services/control_plane/provisioning.py（P17-AUTH-Q1 的唯一落点）
能力：provision_tenant / provision_space（对象 + 投影，同事务）·
      ensure_resource_projection / ensure_agent_projection（幂等）·
      backfill_resource_projections（显式 · 手动 · 非自动）
边界：非 HTTP surface；uap_runtime 物理上无法执行（无 tenants/spaces 写权限）
缺口：没有任何"控制面主体"被指定；没有授权层；没有 API；没有可用 principal 具备写权限
```

### 3.3 Bootstrap（DB 侧）

```text
uap_bootstrap 主体存在（LOGIN · 非 superuser）
实测授权（uap_b1_test · information_schema.role_table_grants）：
  audit_logs           : INSERT
  platform_memberships : INSERT, SELECT
  platform_state       : SELECT, UPDATE
  tenants / spaces / resources / roles / role_permissions / tenant_memberships / memberships : 无
结论（§8"不得以名字推断权限"）：uap_bootstrap 目前**不能**创建 tenant/space，
       也不能创建 resource 投影，更不能创建初始 membership。
```

### 3.4 Migrator（schema authority）

```text
uap_migrator：14 张业务表的 owner（含全部 DDL/DML 权利）·
              alembic 迁移唯一身份（UAP_MIGRATION_DATABASE_URL）·
              scripts/privileges.materialize() 的执行身份
实测：uap_migrator = 245 grants（含 TRUNCATE / TRIGGER / REFERENCES）
结论：schema authority ≠ 运营控制面（§46）；不得把迁移身份复用为控制面应用主体
```

### 3.5 uap_app / uap_seed

```text
uap_app     ：5 grants（alembic_version SELECT · audit_logs SELECT/INSERT）—— 仅就绪/审计追加
uap_seed    ：0 grants —— 命名存在但无任何权限，仓库内无任何引用
```

### 3.6 版本化缺口（STOP-3）

```text
scripts/privileges.py 仅物化 uap_runtime（P14 基线）与 uap_app（就绪面）。
uap_bootstrap / uap_seed 的授权在 migrations 与 scripts 中**均无来源**
⇒ 当前 uap_bootstrap 权限属环境态、不可在 clean clone 中重现
⇒ 若 P18 采用控制面主体，其授权必须成为版本化 artifact（新决策）
```

---

## 4. 平台初始化 vs Tenant/Space provisioning（§9/§10）

```text
实测三件不同的事，不得合并：

A. platform_state（单例）
   bootstrap_state ∈ {uninitialized, initialized}
   约束（enforce_platform_state_guard）：不可 DELETE；INSERT 仅允许 'uninitialized'；
   UPDATE 仅允许 uninitialized → initialized 一次（且 initialized_at NOT NULL）
   当前 uap_b1_test ：uninitialized · initialized_at = NULL

B. platform_memberships（平台管理员绑定）
   约束（enforce_pm_bootstrap_gate）：uninitialized 时仅允许插入首行；
   已 initialized 时正常插入
   约束（enforce_pm_role_scope）：role 必须是 active PLATFORM 角色；active 绑定要求 user 为 active
   约束（enforce_pm_last_admin）：不得撤销/删除最后一个 active platform_admin 绑定
   当前：0 行

C. tenant / space provisioning
   与 A、B 无 FK 关系；当前无任何 principal 具备写权限

⇒ 结论：A = 平台一次性初始化；B = 平台管理员绑定（可多次，受 gate 保护）；
        C = 结构对象生命周期。三者是**不同的生命周期状态**，P18 必须分开裁定。
```

---

## 5. Tenant lifecycle inventory（实测）

```text
表 tenants（owner = uap_migrator）
  id uuid PK default uap_uuid_v7()
  slug text NOT NULL · UNIQUE(lower(slug)) · CHECK ^[a-z0-9][a-z0-9-]{1,62}$
  display_name text NOT NULL
  status text NOT NULL
    CHECK ∈ {provisioning, active, suspended, archived, deleted}
  plan text NULL · region text NULL · settings jsonb NOT NULL default '{}'
  archived_at / deleted_at / created_at / updated_at (timestamptz)
  触发器：tg_tenants_set_updated_at（仅 updated_at）
  外键：无（tenants 是根）
  反向依赖：spaces.tenant_id RESTRICT · resources.tenant_id RESTRICT ·
            roles.tenant_id CASCADE · tenant_memberships.tenant_id CASCADE ·
            memberships.tenant_id CASCADE
  无 owner 列（§32 的 "tenant owner field" 在 schema 中**不存在**）
```

```text
生命周期可表达性（仅凭现有 schema）：
  create       = 可（status='provisioning' 已存在，语义天然支持两阶段创建）
  active       = 可
  suspend      = 可（status='suspended'）
  archive      = 可（status='archived' + archived_at）
  soft delete  = 可（status='deleted' + deleted_at）
  hard delete  = 受限：spaces/resources 为 RESTRICT（有 space 或 resource 行即拒绝）；
                 若强行删除会 CASCADE 掉 roles / tenant_memberships / memberships
  ⇒ schema gap = 无（生命周期状态齐备）；hard delete 语义需决策，不建议
```

---

## 6. Space lifecycle inventory（实测）

```text
表 spaces（owner = uap_migrator）
  id uuid PK default uap_uuid_v7()
  tenant_id uuid NOT NULL · FK → tenants(id) ON DELETE RESTRICT
  key text NOT NULL · UNIQUE(tenant_id, key)（uq_spaces_key）
  name text NOT NULL · kind text NOT NULL CHECK ^[a-z][a-z0-9_.]{1,63}$
  visibility text NOT NULL CHECK ∈ {private, tenant, link}   （无 'public'）
  status text NOT NULL CHECK ∈ {active, archived, deleted}    （无 provisioning / suspended）
  owner_id uuid NULL · FK → users(id) ON DELETE SET NULL
  settings jsonb NOT NULL default '{}' · archived_at / deleted_at / created_at / updated_at
  触发器：tg_spaces_set_updated_at
  反向依赖：roles.space_id CASCADE · memberships.space_id CASCADE · resources.space_id RESTRICT
```

```text
Can a Space exist without Tenant?  NO（tenant_id NOT NULL + FK RESTRICT）——与预期方向一致
生命周期可表达性：
  create/active/archive/soft delete = 可
  suspend / provisioning           = **不可**（status 枚举缺失）→ STOP-4（schema gap，记录不修）
  hard delete                      = 受限（resources.space_id RESTRICT）
```

---

## 7. Membership / role / resource 的前置条件（实测触发器语义）

```text
roles（owner = uap_migrator · 现有 1 行 platform_admin）
  scope ∈ {PLATFORM, TENANT, SPACE}
  status ∈ {active, disabled, archived}
  key CHECK ^[a-z][a-z0-9_]{1,63}$
  enforce_roles_scope_shape   ：PLATFORM → tenant_id/space_id 均 NULL；
                                TENANT → tenant_id NOT NULL & space_id NULL；
                                SPACE  → tenant_id NULL & space_id NOT NULL
  enforce_roles_is_system_protect：is_system=true 的 INSERT 被拒（"system roles cannot be created
                                at runtime"）；system 行不可 UPDATE/DELETE
  enforce_roles_pm_lifecycle  ：platform_admin 角色在有 active 平台绑定时不得离开 active
  FK：tenant_id → tenants CASCADE · space_id → spaces CASCADE

tenant_memberships
  enforce_tm_role_scope ：role 必须存在且 scope='TENANT' · role.tenant_id = membership.tenant_id ·
                          role.status='active'
  UNIQUE uq_tenant_memberships (tenant_id, user_id) —— **无条件唯一**（含 removed 行）
  FK：tenant CASCADE · user CASCADE · role RESTRICT

memberships（space 级）
  enforce_membership_role_scope       ：role 必须 scope='SPACE' · role.space_id = membership.space_id ·
                                        active
  enforce_membership_tenant_consistency：space 必须存在且 membership.tenant_id = spaces.tenant_id
  UNIQUE uq_memberships (space_id, user_id) WHERE removed_at IS NULL —— **部分唯一**（允许重新加入）
  FK：tenant CASCADE · space CASCADE · user CASCADE · role RESTRICT

resources
  enforce_resources_tenant_space_consistency：space_id 非空时其 tenant 必须 = resources.tenant_id
  UNIQUE uq_resources_natural (tenant_id, resource_type, natural_key)
         WHERE natural_key IS NOT NULL AND deleted_at IS NULL
  FK：tenant RESTRICT · space RESTRICT · owner SET NULL

audit_logs
  enforce_audit_logs_immutable：UPDATE / DELETE 一律拒绝（append-only）
  无 tenants/spaces 外键 ⇒ 历史审计事实不随结构删除消失

platform_state / platform_memberships：见 §4
```

### 7.1 关键推论（P18 的核心难点）

```text
(1) 初始 tenant administrator 无法凭空成立：
    tenant_memberships 要求存在 active 的 **同租户 TENANT 角色**；
    全新平台只有 platform_admin（PLATFORM · is_system=true）。
    ⇒ 若 P18 不允许创建 TENANT/SPACE 角色，则"首个租户管理员"无法写入（§90 STOP）。
(2) 同理，初始 space administrator 需要 active 的 **同空间 SPACE 角色**。
(3) 角色创建本身受两条冻结约束：is_system 必须为 false；shape 必须与 scope 匹配。
(4) tenant_memberships 的唯一键是无条件的 ⇒ 软删除后无法重新邀请（P17 已记录 · 不在 P18 修）。
(5) space membership 的部分唯一键允许重新加入 ⇒ 两层 membership 语义**不对称**（事实记录）。
```

---

## 8. Resource projection ownership（贴续 P17-AUTH-Q1）

```text
现有 canonical 表示（P17 已冻结并实现）：
  tenant 对象            → resources(resource_type='tenant', tenant_id=T, space_id NULL)
  space 对象             → resources(resource_type='space',  tenant_id=T, space_id=S)
  tenant membership 集合  → resources(resource_type='member', tenant_id=T, space_id NULL)
  space  membership 集合  → resources(resource_type='member', tenant_id=T, space_id=S)
  agent 对象             → resources(resource_type='agent',  id = agent 自身 id)
幂等键：natural_key（tenant 用 slug · space 用 key · member 集合用保留键 'members' / space key）
原子性：对象 + 投影同事务；投影失败 ⇒ 对象回滚（P17 acceptance 已实测）
授权前置：resource 行缺失 ⇒ member.read / member.admin 均 DENY（fail closed）
P18：必须继承该模型，不得发明新 resource grammar（§88/§89）
```

---

## 9. Data ownership matrix（提案 · 待裁定）

| Data | Runtime（uap_runtime） | Control Plane（待定主体） | Bootstrap（uap_bootstrap） | Migrator（uap_migrator） |
|---|---|---|---|---|
| users | 既有 identity 路径读写 | NO | NO | schema only |
| tenants | READ | **WRITE（待裁定）** | 无权限（实测） | schema / owner |
| spaces | READ | **WRITE（待裁定）** | 无权限（实测） | schema / owner |
| tenant_memberships | 常规运行期 WRITE | 初始管理员 provisioning | 无权限（实测） | schema / owner |
| memberships（space） | 常规运行期 WRITE | 初始管理员 provisioning | 无权限（实测） | schema / owner |
| platform_memberships | READ | 待裁定（bootstrap 现可 INSERT） | INSERT / SELECT | schema / owner |
| platform_state | READ | 待裁定 | SELECT / UPDATE | schema / owner |
| roles | READ | 待裁定（是否允许创建 tenant/space 角色） | 无权限 | schema / owner |
| permissions | READ | NO（P13 冻结） | 无权限 | seed only |
| role_permissions | READ | 待裁定（是否允许为既有 permission 建立绑定） | 无权限 | seed only |
| resource_permissions | READ（consume） | OUT（除非另行决定） | 无权限 | schema / owner |
| resources | READ（consume · 且有 INSERT/UPDATE 但不得使用） | **provision（待裁定）** | 无权限 | schema / owner |
| audit_logs | INSERT | INSERT（若采用控制面主体） | INSERT | schema / owner |

```text
注：uap_runtime 目前仍持有 resources INSERT/UPDATE（P14 基线遗留）。
    P17 未使用它（没有任何 runtime 路径写 resources），但**权限仍然存在**。
    P18 必须裁定：保留（现状）还是在大版本内收窄（需要 Human Decision，不得自行 REVOKE）。
```

---

## 10. P18 DECISION MATRIX（候选 · 全部 NOT FROZEN）

### D01 — 控制面执行主体（DB principal）

| 选项 | 内容 | 代价 | 证据 |
|---|---|---|---|
| A | 复用 `uap_bootstrap`，扩展其授权 | 需新增 tenants/spaces/resources/roles/role_permissions 写权限（新 privilege surface）+ 需版本化物化 | 实测其现有权限仅 3 表 |
| **B（建议）** | 专用控制面应用边界（`services/control_plane` 之上的 use-case 层），执行主体 = `uap_bootstrap`（最小化扩展） | 需明确授权清单与物化 artifact | §13 建议 B |
| C | `uap_app` | 该主体定位为就绪/审计，语义冲突 | 5 grants |
| D | `uap_migrator` | 违反 §46（schema authority ≠ 运营控制面） | 245 grants / table owner |
| E | 新建 DB 角色 | 新主体 = 新决策；增加运维面 | §15 |

```text
裁定项：principal 名称 + 精确 grant 清单 + 是否将授权纳入 scripts/privileges.py（版本化）
禁止：扩大 uap_runtime；SET ROLE bootstrap；拒绝后回落到 bootstrap（§27）
```

### D02 — Tenant/Space 生命周期状态机

| 选项 | 内容 | 证据/代价 |
|---|---|---|
| **A（建议）** | 软生命周期：`provisioning → active → suspended ⇄ active → archived → deleted`（仅用 status + archived_at/deleted_at） | tenants 五态齐备；spaces 缺 provisioning/suspended |
| B | 只支持 `active / archived / deleted`（space 与 tenant 取交集） | 无需 schema 变更，但 tenant 的 provisioning/suspended 浪费 |
| C | 硬删除 | 受 RESTRICT 阻塞（spaces/resources），且会 CASCADE memberships/roles；审计留痕仍在 | 不推荐 |

```text
若选择包含 space provisioning/suspended ⇒ STOP-4（schema gap，需独立决策 + migration，P18 默认 migration = NONE）
```

### D03 — 初始 Tenant 管理员（§19）

| 选项 | 内容 | 可行性（实测） |
|---|---|---|
| A | 请求方 platform administrator 成为首个 tenant 管理员 | 可行（需该 user id）· 与 P17 Q3 一致 |
| B | provisioning 参数显式指定首个管理员 user | 可行 · 最明确 |
| C | `tenants.owner_id` 自动成为管理员 | **不可行**：tenants 无 owner 列（schema gap） |
| D | bootstrap 服务身份 | 可行但需禁止其成为长期人类管理员 |
| E | 独立邀请流程 | 超出 P18 范围（未来） |

```text
同时必须裁定：首个管理员使用哪个角色（见 D05）
```

### D04 — 初始 Space 管理员（§20）

```text
必需（不可省）：space 无成员时，Q5 双成员资格要求使运行期无法自举
⇒ 必须由控制面 provisioning 写入首个 space membership（非绕过，而是 provisioning authority）
同时必须满足 DB 约束：active 的 SPACE 角色 + 目标 user ∈ tenant（否则 tenant_memberships 缺失）
裁定项：哪个角色 + 由谁指定 + 是否强制 target user 已属 tenant（DB 不强制 tenant 成员资格）
```

### D05 — 角色 provisioning 权限（STOP-2 核心）

| 选项 | 内容 | 代价 |
|---|---|---|
| **A（建议）** | 控制面在 provisioning 时创建**非 system** 的 TENANT/SPACE 角色（模板键如 `tenant_admin` / `space_admin`），并为其绑定既有 canonical permission（`member.read` / `member.admin`） | 需裁定"控制面可创建角色 + 可写 role_permissions"（新写面） |
| B | 只允许绑定**既有**角色 | 不可行：全新平台无任何 TENANT/SPACE 角色（实测 roles=1） |
| C | 修改 P13 seed 增加 tenant/space 模板角色 | 违反 P13 冻结（禁止） |
| D | 以 platform_admin 代替租户管理员 | 违反"platform_admin 非 fallback"（§27）；且 tenant_memberships 只接受 TENANT 角色（DB 拒绝） |

```text
注意：选项 A 不新增 permission（仍 12 条），只新增"角色行 + role_permissions 绑定"的写权限。
      该项必须 Human Decision；不得自行 GRANT 或自行 seed。
```

### D06 — 控制面授权模型（§61/§62）

| 选项 | 内容 | 关键难点 |
|---|---|---|
| **A（建议）** | 复用既有 canonical 授权机制 + 平台/控制面 scope | 结构对象在创建**之前不存在 resource 行**，无法用对象自身资源做决策（鸡与蛋） |
| B | 专用控制面 permission 命名空间 | 需新增 permission（违反 P13 冻结 ⇒ 需重开 permission 模型） |
| C | 仅 bootstrap/服务级授权（无 actor 层） | 缺少 actor 判定，违反 §26（actor 授权必须存在） |

```text
建议解决方向（待裁定，不得自行实现）：
  以"平台级控制面资源"（平台 scope 的既有权限，如 tenant.admin / space.admin）
  作为创建操作的授权对象，而 runtime 的对象级授权保持 P17 现状。
  必须在 Human Decision 中明确：授权对象、permission、scope、以及 platform_admin 的参与方式。
```

### D07 — 平台初始化（§33/§34）

```text
现状：platform_state（单例 · 一次性 uninitialized → initialized）+
      platform_memberships（首个绑定受 gate 允许；后续需 initialized）
裁定项：谁执行一次性初始化（运维/控制面）？是否由 P18 API 暴露？是否要求审计？
禁止：runtime 触发；拒绝后回落 bootstrap。
```

### D08 — 幂等与并发（§35/§85）

```text
可用既有唯一键：tenants.slug(uq) · spaces(tenant_id,key)(uq) · resources natural_key(uq 部分)
候选规则：
  A（建议）同 slug/key 重复 provisioning = 显式冲突（409），不静默幂等
  B 幂等重放：同请求返回既有对象（需定义"同请求"指纹）
  C 幂等键（idempotency key）表 —— 需新表 ⇒ 需决策（默认 OUT）
裁定项：并发同 slug 的两个 provisioning 的行为（DB 唯一键兜底）
```

### D09 — 事务与失败原子性（§36/§37/§83/§84）

```text
候选（建议）：单事务内 object + resource projection + initial admin；
              任一步失败 ⇒ 整体回滚（不得留 half-provisioned tenant/space）
若采用两步（先 provisioning 状态再激活）：需要显式状态机 + 补偿语义（更复杂，需决策）
审计原子性：结构变更 + 审计同事务（与 P17 membership 同风格；不得 best-effort）
注意：audit_logs 对 UPDATE/DELETE 永久拒绝；审计写入失败必须导致回滚
```

### D10 — API 表面（§23/§24/§25/§87）

| 选项 | 内容 |
|---|---|
| A | 无 HTTP；仅内部控制面 capability |
| **B（建议）** | 独立控制面 API 命名空间（例如 `/control/...`），与 runtime `/tenants` 分离；命名遵循仓库既有 convention |
| C | tenant-owner API |
| D | 公开 API |

```text
硬约束：不得放进 P17 runtime 命名空间；不得变成通用 CRUD；
        每个结构变更必须有显式 lifecycle 语义 + 授权 + 审计 + 事务边界；
        必须防枚举（§63）。
```

### D11 — 审计与关联（§38/§39/§64）

```text
候选（建议）：复用既有 audit_logs 与 correlation（x-correlation-id）；
              审计记录 actor（人类）+ DB principal 语境分离；
              结构生命周期 audit action 命名需与既有风格一致（如 tenant.provision / space.provision）
禁止：以 DB principal 取代 actor；记录 secret/token/SQL/stack
```

### D12 — 事件边界与未来兼容（§65/§66）

```text
本轮与 P18 实现均保持：Production Event Allowlist = EMPTY · Handlers = 0
候选 future event（不得激活）：tenant.created · space.created · membership.bootstrapped ·
                              resource.provisioned
要求：P18 的数据/审计结构不得使未来激活不可能（审计事实已包含 actor/tenant/space/action）
```

### D13 — 权限与安全基线（§71–§77）

```text
必须保持：permissions = 12 · uap_runtime = 56 · default ACL = 0 · public schema PUBLIC grants = 0
          roles = 6（uap* 主体）· Core → Domain = 0 · OI-G-4 = 0
新增授权（若有）只能落在控制面主体，且必须成为版本化 artifact（STOP-3）
候选收窄（需单独决策）：uap_runtime 的 resources INSERT/UPDATE 是否移除
```

---

## 11. OPEN QUESTIONS（OQ · 必须由 Human 裁定）

```text
OQ-01 控制面 DB 主体：uap_bootstrap（扩展）还是新建专用角色？（D01）
OQ-02 控制面授权清单：精确到表 + 动作（INSERT/UPDATE/DELETE 各自是否存在）？（D01/§71）
OQ-03 控制面授权是否纳入 scripts/privileges.py 版本化物化？（STOP-3）
OQ-04 uap_bootstrap / uap_seed 的既有环境态权限如何登记（现状不可重现）？（STOP-3）
OQ-05 Tenant 生命周期状态机最终形态（是否使用 provisioning / suspended）？（D02）
OQ-06 Space 生命周期是否需要 provisioning / suspended（涉及 schema gap）？（STOP-4/D02）
OQ-07 结构删除语义：archive 还是 hard delete？（若 hard delete，如何绕过 RESTRICT/CASCADE）？（D02/§28）
OQ-08 首个 tenant 管理员的来源（请求方 platform admin / 显式参数 / 其他）？（D03）
OQ-09 首个 space 管理员的来源与是否强制"已属 tenant"？（D04）
OQ-10 控制面是否可创建非 system 的 TENANT/SPACE 角色？（D05 · STOP-2）
OQ-11 控制面是否可写 role_permissions（为既有 permission 建立绑定）？（D05）
OQ-12 角色模板命名与语义（tenant_admin / space_admin 等）由谁定义？（D05）
OQ-13 控制面创建操作的授权对象与 permission（鸡与蛋问题）？（D06）
OQ-14 platform_admin 在控制面操作中的角色（显式授权，非 fallback）？（D06）
OQ-15 平台一次性初始化（platform_state 转换 + 首个 platform_membership）由谁执行、是否暴露 API？（D07）
OQ-16 provisioning 幂等策略（冲突 vs 幂等重放）？（D08）
OQ-17 是否允许半初始化状态（若允许，需显式状态机与补偿）？（D09）
OQ-18 控制面 API 是否存在、命名与认证模型？（D10）
OQ-19 结构变更审计的 action 命名与 correlation 复用方式？（D11）
OQ-20 是否在大版本内收窄 uap_runtime 的 resources INSERT/UPDATE？（D13）
OQ-21 tenant/space 是否需要在 resources 之外新增资源类型（默认：不需要）？（§88）
OQ-22 space membership 可重新加入、tenant membership 不可（唯一键不对称）是否接受？（§91）
```

---

## 12. Security risks（勘验识别）

```text
R-01 新 privilege surface：控制面写权限是本轮最大的安全面变更；必须以最小集 + 版本化物化落地
R-02 主体语义漂移：uap_bootstrap 名称暗示权限，但实测权限极窄 → 不得以名称推断授权
R-03 环境态授权不可重现：uap_bootstrap/uap_seed 无仓库来源 → clean clone 不可重现（与 F-P16-I-04 同类）
R-04 提权路径：必须禁止 runtime → SET ROLE bootstrap / 拒绝后回落 bootstrap（§27）
R-05 角色自举风险：控制面若可自由创建角色 + 绑定 member.admin，需限制在 provisioning 语境并审计
R-06 runtime 残留 resources 写权限：现状存在但未被使用；如不收窄，需在文档中登记为已知残留
R-07 硬删除风险：CASCADE 会连带删除 roles/memberships；建议以软生命周期替代
R-08 半初始化状态：若无显式状态机，失败可能留下 tenant 无 resource / 无管理员（§83/§84）
R-09 审计不可变（好）：audit_logs 拒绝 UPDATE/DELETE，历史事实天然可靠；但审计失败必须触发回滚
R-10 幂等缺失：并发同 slug/key 依赖 DB 唯一键兜底，需明确错误映射
```

---

## 13. Dependency risks

```text
DP-01 控制面 API → 需新增授权语义（D06）；不得复用 member.admin 作为 tenant.create 语义（§61）
DP-02 初始管理员 → 依赖角色 provisioning（D05）→ 依赖 role_permissions 写面（OQ-11）
DP-03 资源投影 → 依赖 resources 写权限（D01）；不得由 runtime 自建（P17 冻结）
DP-04 未来事件系统 → 依赖结构生命周期稳定（本阶段不激活）
DP-05 未来业务模块（Company/Commercial/Entertainment）→ 依赖 tenant/space 生命周期与隔离语义稳定
DP-06 P17 runtime 契约 → 本阶段不得改动（P18 只在 runtime 之前插入结构段）
DP-07 测试基线 → P17 97/0 · P16 33/0+8/0 · P15 65/0 · guards 57/0 必须保持
```

---

## 14. Scope（IN / OUT）

```text
P18 IN（候选 · 待冻结）
  · 控制面主体与授权边界（D01/D06）
  · Tenant 生命周期（create / active / suspend? / archive / delete?）（D02）
  · Space 生命周期（create / active / archive / delete?）（D02）
  · 结构对象 + 资源投影 + 初始管理员的原子 provisioning（D04/D09）
  · 初始角色 provisioning（非 system 角色 + 既有 permission 绑定）（D05）
  · 控制面 API（若裁定暴露）（D10）
  · 控制面审计与关联（D11）
  · 控制面测试矩阵（含 §68 的 N1–N20）

P18 OUT（明确不做）
  · 修改 P13/P14/P15/P16/P17 冻结语义
  · 新增 permission（词表保持 12）
  · 扩大 uap_runtime 权限（除另行裁定的收窄）
  · production event / handler 激活
  · ACL（resource_permissions）管理
  · 修复 tenant membership 重邀请（§91）
  · 业务模块（Company / Commercial / Entertainment）
  · 任何 migration / schema 变更（除非 STOP-4 被裁定为必须）
```

---

## 15. PREP acceptance checklist（§97 逐条）

```text
[x] Control Plane boundary 勘验（P17 capability 范围与缺口）
[x] Bootstrap boundary 勘验（uap_bootstrap 实测权限 3 表）
[x] Migrator boundary 勘验（table owner + 245 grants）
[x] Runtime boundary 勘验（56 grants · 无结构写路径）
[x] Tenant schema 勘验（5 态生命周期齐备 · 无 owner 列）
[x] Space schema 勘验（3 态 · tenant 必需 · 无 provisioning/suspended）
[x] platform_state 勘验（单例 · 一次性转换 · 当前 uninitialized）
[x] platform_memberships 勘验（gate + role scope + last-admin 保护 · 当前 0 行）
[x] resources 勘验（natural_key 唯一 · tenant/space 一致性 · RESTRICT）
[x] role provisioning 勘验（shape/is_system/pm 保护 · 无 eligible TENANT/SPACE 角色）
[x] initial admin 路径勘验（两层 membership 的 DB 前置条件）
[x] DB principals 勘验（6 主体 · 逐表授权矩阵）
[x] existing privilege matrix 勘验（uap_runtime 56 · uap_app 5 · uap_migrator 245 · uap_seed 0）
[x] lifecycle gaps 识别（STOP-4 space 状态；tenants 无 owner 列）
[x] authorization model gap 识别（控制面创建操作的授权对象鸡与蛋问题）
[x] API options 准备（D10）
[x] audit model 准备（D11）
[x] atomicity model 准备（D09）
[x] idempotency model 准备（D08）
[x] event boundary 保持（EMPTY / 0）
[x] P17 handoff 定义（见 §16）
[x] future business dependency 记录（DP-05）
[x] open questions 登记（OQ-01…22）
[x] Human Decision matrix 准备（D01…D13）
[x] P18 contract skeleton 准备（独立文档）
[x] Formal DB unchanged（uap = 0 public 表）
[x] Git baseline preserved（HEAD/origin/staged/tags 未变）
```

---

## 16. Control Plane → P17 handoff（提案）

```text
控制面 provisioning 完成后，必须同时成立：
  tenant 行存在
  + tenant canonical resource 存在
  + tenant membership collection resource 存在
  + 初始 tenant administrator（tenant_memberships 行 + 合规 TENANT 角色）存在
  + （若有 space）space 行 + space/space-collection resource + 初始 space administrator 存在
        ↓
P17 runtime 接管：context resolution · membership 读写 · authorization · audit
控制面不再位于普通请求路径
```

---

## 17. 本轮为何不实现

```text
勘验显示：P18 的核心不是"写几个 CRUD 端点"，而是三件必须先裁定的架构事实：
  1. 谁拥有平台结构的创建/销毁权（DB 主体 + 授权模型）
  2. 初始管理员如何在无角色可用时成立（role provisioning 权限）
  3. 生命周期语义（尤其是删除/停用）与失败原子性
任一自决都会违反 P13/P14/P17 冻结边界或制造隐式提权面，因此本轮严格停在 PREP。
```

**END OF P18 HUMAN DECISION PREP（PREP ONLY · 4 项 STOP 命中待裁定 · OQ-01…22 · D01…D13 · Formal DB unchanged · Git unchanged · 未实现 / 未 commit / 未 tag / 未 push；2026-10-01）**
