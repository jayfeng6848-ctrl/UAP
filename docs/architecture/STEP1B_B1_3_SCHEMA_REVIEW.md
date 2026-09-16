# STEP 1-B / B1-3 — Schema Review（Role & Permission Foundation）

Status: **PREP + DECISION RESOLUTION（D-05…D-16 FROZEN，2026-09-08）— 不建表、不写 migration、不执行 DDL**
范围：`roles` · `permissions` · `role_permissions`
当前 Alembic head = `0004_b1_2_tenant_space`（**不修改** 0001–0004）
未来 revision（本阶段不创建）：`0005_b1_3_roles_permissions`（down = `0004`）

来源优先级：① `CORE_DOMAIN_MODEL.md` §1.2（主）② `ER_MODEL.md` §2 ③ B0 文档（CONSTRAINT_MATRIX / INDEX_STRATEGY / TRIGGER_INVENTORY / SCHEMA_DEPENDENCY / SEED_STRATEGY / UUID_STRATEGY）④ B1-2 `DECISION_LOG.md`（D-01/D-02）

---

## 0. 逐字段核对结论（**只列冻结设计存在的字段**）

> 用户清单中出现的若干字段在冻结设计中**不存在**，一律标记 **OPEN DECISION**（记录于 `STEP1B_B1_3_DECISION_LOG.md`），本阶段**不新增**。

### 0.1 `roles`

| column | type | nullable | default | 冻结依据 | notes |
|---|---|---|---|---|---|
| id | uuid | NO | `uap_uuid_v7()` | PK | UUIDv7 兜底（复用，不重建） |
| tenant_id | uuid | YES | NULL | FK → tenants.id **ON DELETE CASCADE** | PLATFORM scope 时为 NULL |
| space_id | uuid | YES | NULL | FK → spaces.id **ON DELETE CASCADE** | SPACE scope 时非空 |
| key | text | NO | — | 部分唯一索引（按 scope） | `lower(key)`；**CK `^[a-z][a-z0-9_]{1,63}$`（R-D-13）** |
| name | text | NO | — | fields | 展示名 |
| scope | text | NO | — | CK `('PLATFORM','TENANT','SPACE')` |
| is_system | bool | NO | — | trigger：`is_system=true` **无条件禁止 UPDATE/DELETE**（R-D-05，含禁改 is_system 自身） |
| status | text | NO | — | **CK `('active','disabled','archived')`（R-D-06）**；被 membership 引用要求 `active` |
| created_at / updated_at | timestamptz | NO | `now()` | 通用列 | updated_at 由 trigger 维护 |
| archived_at | timestamptz | YES | NULL | 归档而非删除 |
| created_at / updated_at | timestamptz | NO | `now()` | 通用列 | updated_at 由 trigger 维护 |
| archived_at | timestamptz | YES | NULL | fields | 归档而非删除 |

**不存在于冻结设计**：`description` → **OPEN（D-01）**，本阶段不新增。

- UQ（三条**部分唯一索引**，scope 互斥）：
  - `uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL`
  - `uq_roles_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL`
  - `uq_roles_space ON (space_id, lower(key)) WHERE space_id IS NOT NULL`
  → **key 唯一性是 scope-scoped（含 tenant/space 命名空间），不是 global unique**：同一 `key` 可存在于不同租户/空间/平台，各一行。
- CK：`scope IN (...)`；scope ↔ tenant_id/space_id 形状匹配（**trigger**，PG 无跨表 CHECK）；`is_system=true` 禁修改/删除（**trigger**）

### 0.2 `permissions`

| column | type | nullable | default | notes |
|---|---|---|---|---|
| id | uuid | NO | `uap_uuid_v7()` | PK |
| key | text | NO | — | `uq_permissions_key ON (key)`（**全局唯一**） |
| resource_type | text | YES | NULL | 权限作用的资源类型（Core 不绑定业务语义） |
| action | text | NO | — | 动作 |
| description | text | ? | — | 冻结 fields 有 `description`（未标 NULL；NN 见 D-02） |
| is_system | bool | NO | — | 系统内置权限标记 |
| created_at | timestamptz | NO | `now()` | 冻结**无 updated_at**（字典表） |

**不存在于冻结设计**：`name` / `scope` / `status` → **OPEN（D-02/D-03）**，本阶段不新增。
- CK：`key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$'`
- **无 FK**（平台级字典，无租户维度）

### 0.3 `role_permissions`

| column | type | nullable | default | notes |
|---|---|---|---|---|
| role_id | uuid | NO | — | FK → roles.id **ON DELETE CASCADE** |
| permission_id | uuid | NO | — | FK → permissions.id **ON DELETE CASCADE** |
| effect | text | NO | — | CK `('allow','deny')` |
| conditions | jsonb | YES | NULL | ABAC 静态条件 |
| created_at | timestamptz | NO | `now()` | |

- **PK = `(role_id, permission_id, effect)`**（冻结，非 `UNIQUE(role_id, permission_id)`）
  → 允许同一 (role, permission) 同时存在 allow 与 deny 两行；deny 优先由**应用层**决策（见 D-04）
- FK 删除行为：两侧均 **CASCADE**（冻结）

---

## 1. 依赖图

```
                 ┌──────────┐        ┌────────────┐
                 │ tenants  │        │   users    │  (B1-1/B1-2 已存在)
                 └────┬─────┘        └─────┬──────┘
                      │                    │
        ┌─────────────┼──────────┐         │
        ▼             ▼          │         ▼
   ┌─────────┐  ┌──────────┐    │   ┌────────────────────┐
   │ spaces  │  │  roles   │    │   │ tenant_memberships │
   └────┬────┘  └────┬─────┘    │   └─────────┬──────────┘
        │            │          │             │ role_id (B1-3 补 FK)
        │            │          └─────────────┤
        ▼            ▼                        ▼
   ┌──────────────┐  │                  ┌───────────┐
   │ memberships  │──┼──role_id────────→│   roles   │
   └──────────────┘  │  (B1-3 补 FK)    └─────┬─────┘
                     │                        │
                     ▼                        ▼
              ┌──────────────┐        ┌──────────────┐
              │role_permissions│──────→│ permissions │
              └──────────────┘        └──────────────┘
```

| 表 | 依赖 | FK（→ 目标，ON DELETE） |
|---|---|---|
| `roles` | tenants, spaces（均 NULL 允许） | `tenant_id → tenants CASCADE`；`space_id → spaces CASCADE` |
| `permissions` | —（root） | 无 |
| `role_permissions` | roles, permissions | `role_id → roles CASCADE`；`permission_id → permissions CASCADE` |
| `tenant_memberships`（既有） | + **roles（B1-3 补）** | `role_id → roles.id **RESTRICT**` |
| `memberships`（既有） | + **roles（B1-3 补）** | `role_id → roles.id **RESTRICT**` |

### 1.1 循环 / 前向依赖检查

| 检查 | 结论 |
|---|---|
| `roles ↔ tenants/spaces` | roles→父单向（tenants/spaces 无回边）→ **无循环** |
| `roles ↔ tenant_memberships/memberships` | membership→roles 单向（roles 不引用 membership）→ **无循环** |
| `roles ↔ role_permissions ↔ permissions` | 单向链 → **无循环** |
| `memberships(role_id) → roles` 与 `roles(space_id) → spaces` | 两者都在 B1-3 前已存在（spaces 于 B1-2）→ 不再是前向依赖 |
| **新前向依赖** | 无（B1-3 所有依赖表均已存在） |

**结论：B1-3 不产生新循环 FK，也不遗留前向依赖。**

## 2. 与 B1-2 `role_id` 的衔接（D-01 收敛）

| 阶段 | `tenant_memberships.role_id` / `memberships.role_id` |
|---|---|
| B1-2（现状） | 列存在、**NULL 允许**、**无 FK** |
| **B1-3** | ① 建 `roles` + seed 内置角色 → ② 回填已有 NULL 行 → ③ `SET NOT NULL` → ④ `ADD CONSTRAINT fk_tm_role / fk_membership_role REFERENCES roles(id) ON DELETE RESTRICT` → ⑤ 挂 scope trigger |

- 回填策略：对每个 NULL 行按作用域回填内置角色（`tenant_member` / `space_member`）；无对应内置角色时 **migration 失败并报告**（不允许静默填假值）
- **不修改 0004**，收敛动作放在 `0005`（未来 revision）

## 3. Role Scope 最终模型（冻结；含 2026-09-08 Resolution R3-D-16/R3-D-07（Option A FROZEN））

| Role Scope | 只能用于 | tenant_id | space_id | 绑定/引用 |
|---|---|---|---|---|
| `PLATFORM` | 平台层 | **NULL** | **NULL** | **`platform_memberships`（R3-D-07 FROZEN Option A，设计冻结；未建表待批准）** |
| `TENANT` | `tenant_memberships` | **NOT NULL** | **NULL** | `tm.role_id`（scope 校验 + 同租户） |
| `SPACE` | `memberships` | **NULL（R-D-16：不冗余）** | **NOT NULL** | `m.role_id`（scope 校验 + 同空间）；租户经 `spaces.tenant_id` 间接获得 |

**Scope Shape 完整性规则**（`tg_roles_scope_shape` 强制，R-D-16）：
- `PLATFORM` → `tenant_id IS NULL AND space_id IS NULL`
- `TENANT` → `tenant_id IS NOT NULL AND space_id IS NULL`
- `SPACE` → `tenant_id IS NULL AND space_id IS NOT NULL`

**Key 唯一性谓词澄清**（R2-D-12，冻结 CORE_DOMAIN_MODEL 三条部分唯一**不含 archived 排除**）：
- `uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL`；`uq_roles_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL`；`uq_roles_space ON (space_id, lower(key)) WHERE space_id IS NOT NULL`
- ⇒ **archive 不释放 key**：archived 角色仍占用同 scope/owner 的 key（可恢复停用记录）；**key 复用唯一途径 = DELETE 该自定义角色**（未被引用时）；系统角色 key 永不复用。

**Enforcement 分层**（不能模糊）：

| 层 | 负责 | 机制 |
|---|---|---|
| **Database** | **引用完整性**（scope 与归属匹配、`role.status='active'`、引用存在） | `tg_roles_scope_shape`、`tg_tm_role_scope`、`tg_membership_role_scope` |
| **Application Authorization** | **授权决策**（default deny、**deny 绝对优先 R-D-14**、ABAC） | `core/policy` / `core/permission` |
| **两层都必须存在** | DB 层只保证"数据不越界"；应用层 fail-closed 保证"决策不默认放行" | |

> Trigger **只做数据库完整性**：不修改权限、不提升角色、不复制 membership、不写审计、不产生业务副作用。

### 3.1 DENY > ALLOW（R-D-14 SECURITY INVARIANT）

同一 `(role, permission)` 并存 `allow` 与 `deny` 时 → **DENY**。由 Authorization Layer 解释（DB 允许两行并存，PK 含 effect）。**不在 Database Trigger 中做授权解释**。

## 4. Default / System Roles（冻结，见 SEED_STRATEGY）

| key | scope | 播种位置 |
|---|---|---|
| `platform_admin` | PLATFORM | 全局 1 行 |
| `tenant_admin` / `tenant_member` | TENANT | 每租户各 1 行 |
| `space_admin` / `space_member` | SPACE | 每空间各 1 行 |

默认：`tenant_memberships.role_id → tenant_member`、`memberships.role_id → space_member`（P2-01 冻结）。

## 5. RBAC 边界声明

**B1-3 只建立 RBAC Foundation（Role → Permission）**，**不**实现：Resource ACL、`resource_permissions`、`resource_relations`、ABAC 求值器落地、Resource Permission 系统。
> B1-3 的 Role/Permission 是**授权基础**，不是完整 Resource Authorization System。
（`role_permissions.conditions` 只是 ABAC 静态条件的**存储位**，求值在应用层，不属本阶段实现。）

## 6. Permission Scope 决策（FROZEN — R-D-15，对齐 D-03）

冻结 `permissions` **无 scope 列** → **Permission 不拥有授权 Scope（scope-neutral）**：
- Permission 描述 **Capability**；Role 拥有 **Role Scope**；Membership 表达 **Context**
- 授权链：`Identity → Membership → Role → Role Scope → Permission → Request Context`
- **不给 `permissions` 增加 `scope`**（D-01/D-02 的 OPEN 同样不阻塞 0005：默认不加列）
- 该语义写入授权设计契约与测试（不只存在于注释）
- 不建立 `Role.scope == Permission.scope` 约束（因 permission 无 scope）
- 可用范围由 **Role 的 scope** 决定；该语义写入文档与决策日志，**不只存在于代码注释**

---

## 8. R4 增补（2026-09-08 D-07 Hardening — PMB-1..4）

- **PMB-1（Last Admin × Role Lifecycle）**：canonical effective 谓词 = `pm.status='active' AND u.status='active' AND r.status='active' AND r.scope='PLATFORM' AND r.key='platform_admin'`；信任根初始化后计数恒 ≥1。双层强制：PM 侧 `tg_pm_last_admin` + **Role 侧新增 `tg_roles_pm_lifecycle`**（有 active 绑定时 `platform_admin` 行不得 active→disabled/archived、不得 DELETE）。system 角色不可变（R2-D-05）已排除运行时路径；此不变量为纵深防线。
- **PMB-2（Bootstrap）**：仅当 PM 行数=0（=未初始化，可判定、无需状态表）；一次性，成功后 audit `platform.admin.bootstrap`（同事务）并永久关闭；普通 API 不可伪造 actor='system'（actor 由认证派生）；丢失恢复 = 独立维护机制（人工批准，非业务 API）。
- **PMB-3（Re-grant）**：单行历史（UQ user+role 非部分）；revoke → re-grant = **UPDATE 本行**回 active（revoked_at=NULL）；禁止 INSERT 新行；duplicate active grant 拒绝。
- **PMB-4（User Lifecycle）**：停用/软删 = 应用工作流先 revoke（PMB-1 校验）再停用，DB 无 users→PM 自动 revoke trigger；hard delete 才 CASCADE（purge 终态，非正常撤销手段）；user 非 active → effective=0 → DENY。
- 测试面：见 TEST_MATRIX §13（R40–R47/PM 系列扩展）。
