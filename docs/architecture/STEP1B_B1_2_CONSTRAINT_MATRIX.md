# STEP 1-B / B1-2 — Constraint Matrix（Tenant / Space Foundation）

Status: **PREP ONLY — 不创建任何约束（仅规划）**
配套：[STEP1B_B1_2_SCHEMA_REVIEW.md](./STEP1B_B1_2_SCHEMA_REVIEW.md)（逐字段核对）
来源：`CORE_DOMAIN_MODEL.md` §1.2 + 已批准 B0 `STEP1B_CONSTRAINT_MATRIX.md` §2

图例：`FUTURE` = 依赖后续阶段（roles），本阶段不建；`PROPOSED` = 建议但未冻结，本阶段不实施。

---

## 1. tenants

| 类别 | 约束 |
|---|---|
| PK | `id uuid NOT NULL DEFAULT uap_uuid_v7()` |
| FK | **无**（root） |
| UQ | `uq_tenants_slug ON (lower(slug))`（全局唯一，表达式索引） |
| CK | `ck_tenants_status: status IN ('provisioning','active','suspended','archived','deleted')`；`ck_tenants_slug: slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'` |
| NOT NULL | id, slug, display_name, status, settings, created_at, updated_at |
| NULL | plan, region, archived_at, deleted_at |
| DEFAULT | `settings = '{}'`、`created_at/updated_at = now()` |
| ON DELETE | —（无 FK） |
| ON UPDATE | 默认 `NO ACTION`（PK 不更新；slug 变更走应用层 + audit） |
| 软删 | `archived_at` / `deleted_at`（`status` 同步） |
| 隔离 | 租户自身即隔离根；无 tenant_id 列 |

## 2. spaces

| 类别 | 约束 |
|---|---|
| PK | `id uuid NOT NULL DEFAULT uap_uuid_v7()` |
| FK | `tenant_id → tenants.id ON DELETE RESTRICT`（`fk_spaces_tenant`）；`owner_id → users.id ON DELETE SET NULL`（`fk_spaces_owner`，**PROPOSED 默认值** 待确认） |
| UQ | `uq_spaces_key ON (tenant_id, lower(key)) WHERE deleted_at IS NULL`（部分 + 表达式） |
| CK | `ck_spaces_status: status IN ('active','archived','deleted')`；`ck_spaces_kind: kind ~ '^[a-z][a-z0-9_.]{1,63}$'`（**不枚举业务值**）；`ck_spaces_visibility: visibility IN ('private','tenant','link')` |
| NOT NULL | id, tenant_id, key, name, kind, visibility, status, settings, created_at, updated_at |
| NULL | owner_id, archived_at, deleted_at |
| DEFAULT | `settings='{}'`、`created_at/updated_at=now()` |
| ON DELETE | tenant → **RESTRICT**（禁止级联删空间）；owner → SET NULL |
| ON UPDATE | NO ACTION |
| 软删 | `archived_at` / `deleted_at` |
| 隔离 | `tenant_id NOT NULL`（Space 唯一归属） |

## 3. tenant_memberships

| 类别 | 约束 |
|---|---|
| PK | `id uuid NOT NULL DEFAULT uap_uuid_v7()` |
| FK | `tenant_id → tenants.id ON DELETE CASCADE`（关系行白名单）；`user_id → users.id ON DELETE CASCADE`；**`role_id`：B1-2 无 FK（D-01 Forward Dependency）** |
| UQ | `uq_tenant_memberships ON (tenant_id, user_id)`（**非部分唯一**：一个用户一个租户只一行，含 removed 历史行） |
| CK | `ck_tm_status: status IN ('invited','active','suspended','removed')` |
| TRIGGER | `tg_tm_role_scope`（**B1-3，D-02**）：引用角色必须 `scope='TENANT' AND roles.tenant_id = 本行 tenant_id`；**B1-2 由应用层 fail-closed 校验替代** |
| NOT NULL | id, tenant_id, user_id, status, created_at, updated_at；**`role_id` 在 B1-2 为 NULL 允许（D-01）**，B1-3 回填后 `SET NOT NULL` |
| NULL | invited_by, invited_at, joined_at, role_assigned_at, role_assigned_by, removed_at |
| DEFAULT | `created_at/updated_at=now()`；`status='invited'`（应用层显式） |
| ON DELETE | tenant/user → CASCADE（关系行）；role → RESTRICT（FUTURE） |
| ON UPDATE | NO ACTION |
| 软删 | `removed_at` + `status='removed'` |
| 隔离 | 天然按 `tenant_id`；查询必须带 tenant scope |

## 4. memberships

| 类别 | 约束 |
|---|---|
| PK | `id uuid NOT NULL DEFAULT uap_uuid_v7()` |
| FK | `tenant_id → tenants.id ON DELETE CASCADE`（冗余列）；`space_id → spaces.id ON DELETE CASCADE`；`user_id → users.id ON DELETE CASCADE`；**`role_id`：B1-2 无 FK（D-01）** |
| UQ | `uq_memberships ON (space_id, user_id) WHERE removed_at IS NULL`（**部分唯一**：允许历史 removed 行） |
| CK | `ck_memberships_status: status IN ('invited','active','suspended','removed')` |
| TRIGGER | `tg_membership_tenant_consistency`（**本阶段建**）：BEFORE INSERT/UPDATE 校验 `tenant_id = (SELECT tenant_id FROM spaces WHERE id = space_id)`；`tg_membership_role_scope`（**B1-3，D-02**）：`scope='SPACE' AND roles.space_id = 本行 space_id`；B1-2 由应用层 fail-closed 替代 |
| NOT NULL | id, tenant_id, space_id, user_id, status, created_at, updated_at；**`role_id` 在 B1-2 为 NULL 允许（D-01）** |
| NULL | invited_by, joined_at, removed_at |
| DEFAULT | `created_at/updated_at=now()` |
| ON DELETE | tenant/space/user → CASCADE；role → RESTRICT（FUTURE） |
| ON UPDATE | NO ACTION |
| 软删 | `removed_at` + `status='removed'` |
| 隔离 | `tenant_id` 冗余（隔离/索引/RLS），trigger 保证不漂移 |

---

## 5. Forward Dependency 约束（`role_id`）— D-01 已冻结

| 阶段 | role_id 列 | FK | NULL / NOT NULL | scope 校验 |
|---|---|---|---|---|
| **B1-2（本阶段）** | **存在** | **无**（严禁创建指向不存在表的 FK） | **NULL 允许** | 无 DB 校验 → **应用层 fail-closed**（D-02） |
| **B1-3（roles 建立后）** | — | `ADD CONSTRAINT ... REFERENCES roles(id) ON DELETE RESTRICT` | 回填内置角色后 `SET NOT NULL` | `tg_tm_role_scope` / `tg_membership_role_scope` |

**明确禁止的误解**：`DEFERRABLE INITIALLY DEFERRED` **不是**"可以先建引用不存在表的 FK"。DEFERRABLE 只延后检查时机；目标表不存在时 FK 无法创建。B1-2 采用 **Deferred Constraint（后续补约束）**，与 DEFERRABLE 无关。

> B1-2 **不创建 `roles` / `permissions` / `role_permissions` 表**，不提前 seed 角色；FK 与 scope 强制在 B1-3 完成并做完整一致性验证。

## 6. ON DELETE 汇总与理由（任务 §7）

| 关系 | 行为 | 理由 |
|---|---|---|
| `tenants → spaces` | **RESTRICT** | Space 是业务实体（承载成员与资源）；删除必须走 space archive→soft delete→purge |
| `tenants → tenant_memberships` | CASCADE | **关系行**（无独立业务数据），随租户受控清理；成员历史由 audit 承担 |
| `tenants → memberships`（冗余列） | CASCADE | 同上 |
| `spaces → memberships` | CASCADE | 关系行；实际清理由 purge job 显式执行（FK 仅兜底） |
| `users → tenant_memberships / memberships` | CASCADE | 关系行；用户硬删时清理归属 |
| `spaces.owner_id → users` | **PROPOSED — HUMAN APPROVAL REQUIRED（D-03）**：建议 SET NULL；**未批准前不实现**；**禁止 CASCADE**（删除 owner 不得删除 Space） |
| `*.role_id → roles` | **RESTRICT** | 被引用角色不可删（FUTURE） |

**原则**：业务实体之间（tenant↔space）一律 RESTRICT；CASCADE 仅限 B0 §11.1 白名单的**关系行/技术子实体**；真实删除流程 = archive → soft delete → retention → **controlled purge**（不依赖 FK 级联）。

## 7. PROPOSED（不实施，仅登记）

| PROPOSED | 说明 | 影响 |
|---|---|---|
| `spaces.owner_id ON DELETE SET NULL` | **D-03：需人工批准**；冻结未明示 owner 删除行为 | 未批准前不实现任何 owner FK 行为 |
| RLS policy | **D-04：OPEN DESIGN QUESTION** | 本阶段不启用/不创建/不改 PG 配置 |
| `ck_tenants_slug` 长度下限 1 | 现正则 `{1,62}` 已含 | 无 |
| `memberships` 增加 `(tenant_id, user_id)` 唯一（非部分） | 防止并发插入重复 | 现由部分唯一 + 应用层覆盖 |
| `tenants.region` 枚举 | 部署区域白名单 | 运行时数据更灵活，暂不枚举 |
| `jsonb` 密钥扫描 | settings 严禁存密钥 | CI 扫描项（非 DB 约束） |

---

## 8. 一致性核对

- 与 B0 `STEP1B_CONSTRAINT_MATRIX.md` §2 完全一致（UQ/CK/NN/ON DELETE）
- 与 `CORE_DOMAIN_MODEL.md` §1.2 字段集一致（无新增/删除字段）
- 与 B1-1 `users` 表衔接（owner_id/invited_by/user_id 均指向已建 users）
- 无 `roles` / `permissions` / `resources` / `acl_*` 约束出现在本阶段清单（除 FUTURE 标记）
