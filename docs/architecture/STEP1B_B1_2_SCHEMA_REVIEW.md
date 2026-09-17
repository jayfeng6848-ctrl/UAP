# STEP 1-B / B1-2 — Schema Review（Tenant / Space Foundation）

Status: **PREP ONLY — 不创建表、不写 migration、不改代码**
来源优先级：① `CORE_DOMAIN_MODEL.md` §1.2 + §2（主）② `ER_MODEL.md` §2 ③ 已批准 B0 文档（CONSTRAINT_MATRIX / INDEX_STRATEGY / TRIGGER_INVENTORY / SCHEMA_DEPENDENCY / UUID_STRATEGY / SEED_STRATEGY）④ B1-1 已实现 `0003_b1_1_root_identity`

目标实体：`tenants` · `spaces` · `tenant_memberships` · `memberships`
**`roles` / `permissions` 不在本阶段（Forward Dependency，见 §5）**

---

## 0. 与 B1-1 Identity 的衔接（已核对）

| B1-2 外键 | 指向 B1-1 表 | 状态 |
|---|---|---|
| `spaces.owner_id` | `users.id` | ✅ B1-1 已建 |
| `tenant_memberships.user_id` | `users.id` | ✅ |
| `tenant_memberships.invited_by` / `role_assigned_by` | `users.id` | ✅ |
| `memberships.user_id` / `invited_by` | `users.id` | ✅ |

B1-1 五张表**保持不变**（不新增列、不改约束、不改 trigger）。

---

## 1. `tenants`

| column | type | nullable | default | notes |
|---|---|---|---|---|
| id | uuid | NO | `uap_uuid_v7()` | PK（UUIDv7 兜底） |
| slug | text | NO | — | `uq_tenants_slug ON (lower(slug))`（全局唯一） |
| display_name | text | NO | — | 展示名 |
| status | text | NO | — | CK `('provisioning','active','suspended','archived','deleted')` |
| plan | text | YES | NULL | 计费档（可选） |
| region | text | YES | NULL | 部署区域（可选） |
| settings | jsonb | NO | `'{}'` | 租户级配置（无密钥） |
| archived_at | timestamptz | YES | NULL | 归档（只读保留） |
| deleted_at | timestamptz | YES | NULL | 软删 |
| created_at / updated_at | timestamptz | NO | `now()` | updated_at 由 trigger 维护 |

- **FK：无**（root 表）
- UQ：`uq_tenants_slug ON (lower(slug))`
- CK：`status IN (...)`；`slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'`
- 软删语义：`archived` → `deleted` → retention purge（不可恢复窗口内可回滚）
- 无 tenant_id 自身（租户是隔离边界根）

## 2. `spaces`

| column | type | nullable | default | notes |
|---|---|---|---|---|
| id | uuid | NO | `uap_uuid_v7()` | PK |
| tenant_id | uuid | NO | — | FK → tenants.id **ON DELETE RESTRICT**（Space 必须属于唯一 Tenant） |
| key | text | NO | — | 租户内标识；UQ `(tenant_id, lower(key)) WHERE deleted_at IS NULL` |
| name | text | NO | — | 展示名 |
| kind | text | NO | — | **运行时数据**：CK 仅约束格式 `^[a-z][a-z0-9_.]{1,63}$`，Core 不枚举 `family`/`company` 等 |
| visibility | text | NO | — | CK `('private','tenant','link')` |
| status | text | NO | — | CK `('active','archived','deleted')` |
| settings | jsonb | NO | `'{}'` | |
| owner_id | uuid | YES | NULL | → users.id（ON DELETE SET NULL，冻结设计 owner 可空） |
| archived_at / deleted_at | timestamptz | YES | NULL | |
| created_at / updated_at | timestamptz | NO | `now()` | |

- UQ（部分）：`uq_spaces_key ON (tenant_id, lower(key)) WHERE deleted_at IS NULL`
- **隔离保证**：`tenant_id NOT NULL` → 不存在"无租户的 Space"；单列 tenant_id → 不存在"Space 属多租户"

## 3. `tenant_memberships`（Tenant 层成员关系）

| column | type | nullable | default | notes |
|---|---|---|---|---|
| id | uuid | NO | `uap_uuid_v7()` | PK |
| tenant_id | uuid | NO | — | FK → tenants.id **ON DELETE CASCADE**（关系行白名单） |
| user_id | uuid | NO | — | FK → users.id **ON DELETE CASCADE** |
| role_id | uuid | **YES（B1-2，D-01）** | NULL | 列保留；**B1-2 不创建 FK**（roles 属 B1-3）；B1-3 回填后 `SET NOT NULL` + `ADD FK → roles.id ON DELETE RESTRICT` |
| status | text | NO | — | CK `('invited','active','suspended','removed')` |
| invited_by | uuid | YES | NULL | → users.id |
| invited_at / joined_at | timestamptz | YES | NULL | |
| role_assigned_at / role_assigned_by | timestamptz/uuid | YES | NULL | |
| removed_at | timestamptz | YES | NULL | 软删（保留"曾是成员"） |
| created_at / updated_at | timestamptz | NO | `now()` | |

- UQ：`uq_tenant_memberships ON (tenant_id, user_id)`（一个用户在一个租户只有一行成员关系）
- CK：`status IN (...)`；role scope 由 **trigger** 校验（PG 无跨表 CHECK）：`roles.scope='TENANT' AND roles.tenant_id = 本行 tenant_id` —— **FUTURE**（随 roles 表）
- 默认 role_id = `tenant_member`（TENANT scope 内置角色；P2-01）

## 4. `memberships`（Space 层成员关系）

| column | type | nullable | default | notes |
|---|---|---|---|---|
| id | uuid | NO | `uap_uuid_v7()` | PK |
| tenant_id | uuid | NO | — | **冗余列**（隔离/索引/RLS）；FK → tenants.id **ON DELETE CASCADE**；trigger 保证 `= spaces.tenant_id` |
| space_id | uuid | NO | — | FK → spaces.id **ON DELETE CASCADE** |
| user_id | uuid | NO | — | FK → users.id **ON DELETE CASCADE** |
| role_id | uuid | **YES（B1-2，D-01）** | NULL | 列保留；**B1-2 不创建 FK**；B1-3 回填后 `SET NOT NULL` + `ADD FK → roles.id ON DELETE RESTRICT` |
| status | text | NO | — | CK `('invited','active','suspended','removed')` |
| invited_by | uuid | YES | NULL | |
| joined_at / removed_at | timestamptz | YES | NULL | |
| created_at / updated_at | timestamptz | NO | `now()` | |

- UQ（部分）：`uq_memberships ON (space_id, user_id) WHERE removed_at IS NULL`
- CK：`status IN (...)`；`tenant_id = spaces.tenant_id`（**跨表 → trigger** `tg_membership_tenant_consistency`）；role scope（`scope='SPACE' AND roles.space_id = 本行 space_id`）→ FUTURE trigger

---

## 5. Forward Dependency：`role_id → roles.id`（**D-01 已冻结**）

冻结设计要求 `tenant_memberships.role_id` 与 `memberships.role_id` 指向 `roles.id`，但 `roles` 属 **B1-3**。

**决策（D-01）**：

| 阶段 | `role_id` 列 | FK | NULL/NOT NULL | scope 校验 |
|---|---|---|---|---|
| **B1-2** | **保留** | **不创建**（roles 表不存在） | **NULL 允许** | 无 DB 校验；**应用层必须强制**（D-02） |
| **B1-3** | — | `ADD CONSTRAINT ... REFERENCES roles(id) ON DELETE RESTRICT` | 回填内置角色后 `SET NOT NULL` | `tg_tm_role_scope` / `tg_membership_role_scope` + 应用层 |

**这是 Forward Dependency / Deferred Constraint，不是 DEFERRABLE FK**：
- `DEFERRABLE INITIALLY DEFERRED` 仅把**已存在**约束的检查时机延后到事务提交
- 它**不能**在目标表 `roles` 不存在时创建 FK
- 把 DEFERRABLE 理解为"可以引用不存在的表"是**错误认知**，本文档明确禁止该理解

**禁止**：B1-2 创建指向 `roles` 的 FK；B1-2 创建 `roles` / `permissions` / `role_permissions` 表；B1-2 提前 seed 角色。

---

## 6. Scope 分离审计（任务 §5）

| 规则 | 结论 |
|---|---|
| Tenant Membership 只表达 Tenant 层成员关系 | ✅ 只含 tenant_id + user_id + (tenant) role |
| Space Membership 只表达 Space 层成员关系 | ✅ 只含 space_id(+冗余 tenant_id) + user_id + (space) role |
| **禁止 Tenant Membership 直接授予 Space 权限** | ✅ 冻结设计：Tenant **权限**向下继承（授权计算），但**成员关系不复制**；Space 访问仍须有 `memberships` 行 |
| **禁止 Space Membership 自动拥有 Tenant Admin** | ✅ role 作用域互斥（scope='SPACE' ≠ 'TENANT'）；继承方向只向下（Tenant→Space），不上溯 |
| **禁止 User→Space 绕过 Membership** | ✅ 授权 Pipeline [3] Space Resolution 必须命中 `memberships.status='active'`，否则 DENY |
| **禁止 User→Tenant 绕过 Tenant Membership** | ✅ Pipeline [2] 必须命中 `tenant_memberships.status='active'`，否则 DENY |

## 7. Tenant / Space 隔离（任务 §6）

| 保证 | 机制 |
|---|---|
| Space 必须属唯一 Tenant | `spaces.tenant_id NOT NULL` + FK |
| 不存在无 Tenant 的 Space | 同上（NOT NULL 强制） |
| 不存在 Space 属多 Tenant | 单列 `tenant_id`（非数组/非关联表） |
| 跨 Tenant 访问默认 DENY | 授权 Pipeline [2] + 应用层 tenant scope + 可选 RLS（Q1）+ 越权写 audit（CRITICAL） |
| memberships 冗余 tenant_id 不漂移 | `tg_membership_tenant_consistency`（BEFORE INSERT/UPDATE 校验 `= spaces.tenant_id`） |
| 通过 A 租户成员身份访问 B 租户 Space | **不可能**：访问 Space 必须走 `memberships(space_id)`，而 space_id 归属唯一 tenant；跨租户即无 membership 行 → DENY |

## 8. 时间/软删语义汇总

| 表 | 软删字段 | 生命周期 |
|---|---|---|
| tenants | `archived_at` + `deleted_at` | provisioning→active→suspended→archived→deleted→purge |
| spaces | `archived_at` + `deleted_at` | active→archived→deleted→purge（purge job 先清资源与成员） |
| tenant_memberships | `removed_at` | invited→active→suspended→removed（保留历史） |
| memberships | `removed_at` | 同上 |

---

## 9. 决策状态与 PROPOSED（不升级为冻结）

| 项 | 状态 |
|---|---|
| `role_id` Forward Dependency | **RESOLVED — D-01**（保留列、不建 FK、B1-2 可空、B1-3 收敛） |
| Role Scope 窗口期 | **RESOLVED — D-02**（B1-2 应用层 fail-closed；B1-3 DB 强制 + 5 项测试） |
| `spaces.owner_id` ON DELETE | **PROPOSED — HUMAN APPROVAL REQUIRED（D-03）**：建议 `SET NULL`；**本阶段不实现**，禁止 CASCADE |
| RLS | **OPEN DESIGN QUESTION（D-04）**：不启用、不创建 policy、不改 PG 安全配置 |
| `ix_tenants_status`（后台批扫） | PROPOSED / 不建（B0 标 P3，无批扫需求） |
| 租户级 `settings` 加密 | PROPOSED（settings 严禁存密钥；CI 扫描，非 DB 约束） |
