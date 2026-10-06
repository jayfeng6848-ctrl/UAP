# UAP Core Domain Model

Status: **DESIGN — STEP 1-A（Round 3 修订完成）**，等待第三次人工审计批准后冻结。
Version: `0.1.0-design` · Target: PostgreSQL 16+

> 本文是**设计文档，不是实现**。STEP 1-B 之前不创建任何表、不写 migration。

## 0. 全局约定

### 0.1 命名

- 表名：复数、小写蛇形（`audit_logs`）
- 字段：`snake_case`；时间字段统一 `_at` 后缀；布尔 `is_` / `has_` 前缀
- 外键列：`<entity>_id`
- 索引：`ix_<table>_<cols>`；唯一约束：`uq_<table>_<cols>`；检查：`ck_<table>_<rule>`

### 0.2 通用列

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | `uuid` | 主键，UUIDv7（见 §11） |
| `created_at` | `timestamptz` | `NOT NULL DEFAULT now()` |
| `updated_at` | `timestamptz` | `NOT NULL DEFAULT now()`，由 trigger 维护 |

例外：`audit_logs`、`events`、`ai_request_logs` 无 `updated_at`（不可变或追加写）。

### 0.3 状态机表示

状态用 `text` + `CHECK` 约束表达（**不用 PG enum 类型**）：PG enum 修改顺序/新增值需要 `ALTER TYPE`，在在线变更中代价高，且 ORM 映射脆弱。

### 0.4 JSON 使用原则

- `jsonb` 只用于**真正无模式**的部分（tool input/output schema、ABAC 条件、provider 配置）
- **禁止**把需要 JOIN / WHERE / 索引的字段塞进 jsonb
- 需要查询的 jsonb 键必须建 GIN 并写入索引策略文档（§15）

---

## 1. Entity Catalog

图例：PK = 主键，FK = 外键，UQ = 唯一，CK = 检查约束。

### 1.1 Identity 域

#### `users`

| 项 | 内容 |
|---|---|
| purpose | 全局登录主体（自然人或服务主体），跨租户存在，是认证的目标 |
| PK | `id` |
| fields | `email citext NULL`、`email_verified_at`、`username citext NULL`、`display_name`、`status`、`primary_identity_id NULL`、`last_login_at`、`locked_until`、`failed_attempts int`、`created_at`、`updated_at`、`deleted_at` |
| UQ | `uq_users_email` on `(lower(email)) WHERE deleted_at IS NULL`；`uq_users_username` on `(lower(username)) WHERE deleted_at IS NULL` |
| CK | `status IN ('pending','active','suspended','locked','deleted')`；`email IS NOT NULL OR username IS NOT NULL` |
| lifecycle | `pending → active → suspended/locked → active`；删除走 soft delete（`deleted_at`），硬删除由 retention job 执行 |
| 关系 | 1:N → `identities`、`credentials`、`devices`、`sessions` |

> `citext` 需扩展；不可用时用 `text` + `lower()` 表达式唯一索引（推荐后者，零依赖）。

#### `identities`

| 项 | 内容 |
|---|---|
| purpose | 用户在某个**身份源**下的表示（本地密码 / OIDC / SAML / 设备）。User 与 Identity 分离，才可能一人多登录方式而不污染 `users` |
| PK | `id` |
| FK | `user_id → users.id ON DELETE CASCADE` |
| fields | `provider`（`local`/`oidc`/`saml`/`device`/`service`）、`issuer NULL`、`subject`、`email NULL`、`display_name NULL`、`status`、`verified_at`、`last_used_at`、`revoked_at`、`created_at`、`updated_at` |
| UQ | `uq_identities_ref` on `(provider, COALESCE(issuer,''), subject)`；`uq_identities_email` on `(provider, lower(email)) WHERE email IS NOT NULL AND revoked_at IS NULL` |
| CK | `status IN ('active','unverified','suspended','revoked')` |
| lifecycle | 创建即 `unverified`，验证后 `active`；撤销置 `revoked_at`，**不硬删除**（审计需要） |

#### `credentials`

| 项 | 内容 |
|---|---|
| purpose | 可验证的秘密（密码哈希、API key 哈希、恢复码、设备证书、OTP 种子）。**永不存明文** |
| PK | `id` |
| FK | `identity_id → identities.id ON DELETE CASCADE`；`user_id → users.id ON DELETE CASCADE`（冗余，便于按用户检索） |
| fields | `type`、`secret_hash text NOT NULL`、`algorithm`（`argon2id`/`scrypt`/`sha256_hmac`）、`secret_hint NULL`、`expires_at NULL`、`last_used_at NULL`、`rotated_at NULL`、`revoked_at NULL`、`failed_attempts int`、`locked_until`、`created_at`、`updated_at` |
| UQ | `uq_credentials_active_password` on `(identity_id) WHERE type='password' AND revoked_at IS NULL`（每种类型同时只有一份有效） |
| CK | `type IN ('password','api_key','recovery_code','device_cert','otp')`；`secret_hash <> ''` |
| lifecycle | **rotation**：新增一行 + 旧行 `revoked_at=now()`，`rotated_at` 串联；过期/已撤销凭据由 retention job 硬删除（含 hash，不留残余）。永不做 soft delete |

#### `devices`

| 项 | 内容 |
|---|---|
| purpose | 注册设备，支撑多设备与设备级信任 |
| PK | `id` |
| FK | `user_id → users.id ON DELETE CASCADE` |
| fields | `fingerprint`、`label`、`platform NULL`、`app_version NULL`、`public_key NULL`、`status`、`first_seen_at`、`last_seen_at`、`ip_last inet NULL`、`revoked_at NULL`、`revoked_reason NULL`、`created_at`、`updated_at` |
| UQ | `uq_devices_fingerprint` on `(user_id, fingerprint)` |
| CK | `status IN ('pending','active','untrusted','revoked','lost')` |
| lifecycle | `pending → active`；撤销 → `revoked`（**不可恢复**，不可逆）；`lost` 由用户标记触发自动 revoke 其全部 session。撤销不删行 |

#### `sessions`

| 项 | 内容 |
|---|---|
| purpose | 一次认证的会话，绑定设备，可多开、可单独失效 |
| PK | `id` |
| FK | `user_id → users.id ON DELETE CASCADE`；`identity_id → identities.id ON DELETE RESTRICT`；`device_id → devices.id ON DELETE CASCADE` |
| fields | `token_hash text NOT NULL`、`refresh_token_hash NULL`、`status`、`ip_created inet`、`ip_last inet NULL`、`user_agent text NULL`、`expires_at`、`absolute_expires_at`、`last_used_at`、`revoked_at NULL`、`revoked_reason NULL`、`replaced_by NULL`、`created_at`、`updated_at` |
| UQ | `uq_sessions_token` on `(token_hash)`；`uq_sessions_refresh` on `(refresh_token_hash) WHERE refresh_token_hash IS NOT NULL` |
| CK | `status IN ('active','expired','revoked')`；`expires_at > created_at` |
| lifecycle | `active → expired`（TTL job）/ `revoked`（用户、管理员、设备撤销级联）；过期会话由 retention 硬删除 |

> **多 Session**：同一 user + device 允许多个 session（不同登录），不设唯一约束。
> **设备撤销级联**：`devices.status='revoked'` 时，应用层在同一事务内撤销其全部 active session（DB 层不写跨表 trigger，保持逻辑可见）。

---

### 1.2 Tenant / Space / Membership 域

#### `tenants`

| 项 | 内容 |
|---|---|
| purpose | 顶层隔离与治理边界：计费、配额、策略、数据隔离的锚点 |
| PK | `id` |
| fields | `slug`、`display_name`、`status`、`plan NULL`、`region NULL`、`settings jsonb`、`archived_at NULL`、`deleted_at NULL`、`created_at`、`updated_at` |
| UQ | `uq_tenants_slug` on `(lower(slug))` |
| CK | `status IN ('provisioning','active','suspended','archived','deleted')`；`slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'` |
| lifecycle | `provisioning → active → suspended → active`；`archived`（不可写，只读保留）；`deleted`（soft，retention 后 purge） |

#### `spaces`

| 项 | 内容 |
|---|---|
| purpose | 租户内的协作上下文。承载成员、资源、Agent 运行边界 |
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE RESTRICT` |
| fields | `key`、`name`、`kind`、`visibility`、`status`、`settings jsonb`、`owner_id → users.id`、`archived_at NULL`、`deleted_at NULL`、`created_at`、`updated_at` |
| UQ | `uq_spaces_key` on `(tenant_id, lower(key)) WHERE deleted_at IS NULL` |
| CK | `status IN ('active','archived','deleted')`；`kind ~ '^[a-z][a-z0-9_.]{1,63}$'`；`visibility IN ('private','tenant','link')` |
| lifecycle | `active → archived`（软归档，只读）→ `deleted`（soft）→ purge job |

> **`kind` 是运行时数据**：Core 只约束格式，**不枚举** `family`/`company` 等具体值。域名空间由 Domain 层注册（未来 `domain_space_kinds` 注册表，不在 STEP 1-A 范围）。

#### `tenant_memberships`

| 项 | 内容 |
|---|---|
| purpose | 用户与租户的归属关系（回答"一个 User 能否属于多个 Tenant"）**+ 租户角色分配（P1-01 方案 A）** |
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE CASCADE`；`user_id → users.id ON DELETE CASCADE`；**`role_id → roles.id ON DELETE RESTRICT`** |
| fields | **`role_id`（NOT NULL，Tenant Role）**、`status`、`invited_by NULL`、`invited_at NULL`、`joined_at NULL`、`role_assigned_at`、`role_assigned_by NULL`、`removed_at NULL`、`created_at`、`updated_at` |
| UQ | `uq_tenant_memberships` on `(tenant_id, user_id)` |
| CK | `status IN ('invited','active','suspended','removed')`；`role_id` 指向的 role 必须满足 `scope='TENANT' AND tenant_id = 本行 tenant_id`（**trigger 校验**，PG 无跨表 CHECK） |
| 分配 | 邀请/加入时写入 `role_id`（缺省 **`tenant_member`** —— TENANT scope 内置角色，**不是** PLATFORM scope 的 `member`）；变更 = `UPDATE role_id` + 写 `audit_logs`（action=`tenant.role.assign`） |
| 撤销 | 撤销租户角色 = 改 `role_id` 为最小权限角色（或 `status='removed'` 移除成员）；**角色本身被引用时不可删（RESTRICT）** |
| 失效 | `status <> 'active'` → 成员资格不存在 → **Tenant Role 立即不参与任何权限计算**（授权实时计算，决策缓存按成员变更事件失效） |

#### `memberships`（Space 级）

| 项 | 内容 |
|---|---|
| purpose | 用户在某个 Space 内的成员资格 + 角色绑定 |
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE CASCADE`（冗余，隔离与索引）、`space_id → spaces.id ON DELETE CASCADE`、`user_id → users.id ON DELETE CASCADE`、`role_id → roles.id ON DELETE RESTRICT` |
| fields | **`role_id`（NOT NULL，SPACE Role，仅引用 `scope='SPACE'` 的角色）**、`status`、`invited_by NULL`、`joined_at NULL`、`removed_at NULL`、`created_at`、`updated_at` |
| UQ | `uq_memberships` on `(space_id, user_id) WHERE removed_at IS NULL` |
| CK | `status IN ('invited','active','suspended','removed')`；`(tenant_id) = (SELECT tenant_id FROM spaces WHERE id = space_id)` — **跨表一致性用 trigger 校验**（PG 不支持跨表 CHECK）；`role_id` 指向的 role 必须满足 `scope='SPACE' AND space_id = 本行 space_id`（trigger 校验） |
| 分配 | 加入时写入 `role_id`（缺省 **`space_member`** —— SPACE scope 内置角色）；变更 = `UPDATE role_id` + 写 `audit_logs`（action=`space.role.assign`） |

#### `roles`

| 项 | 内容 |
|---|---|
| purpose | 权限集合，支持三个作用域 |
| PK | `id` |
| FK | `tenant_id NULL → tenants.id ON DELETE CASCADE`；`space_id NULL → spaces.id ON DELETE CASCADE` |
| fields | `key`、`name`、`scope`、`is_system bool`、`status`、`created_at`、`updated_at`、`archived_at NULL` |
| UQ | 三选一互斥，用**部分唯一索引**：`uq_roles_platform on (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL`；`uq_roles_tenant on (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL`；`uq_roles_space on (space_id, lower(key)) WHERE space_id IS NOT NULL` |
| CK | `scope IN ('PLATFORM','TENANT','SPACE')`；scope 与 tenant/space 是否为空必须匹配（trigger 校验）；`is_system = true` 时禁止修改/删除（trigger） |

#### `permissions`

| 项 | 内容 |
|---|---|
| purpose | 平台级权限字典（`resource.read`、`member.manage`…），无租户维度 |
| PK | `id` |
| fields | `key`、`resource_type NULL`、`action`、`description`、`is_system bool`、`created_at` |
| UQ | `uq_permissions_key` on `(key)` |
| CK | `key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$'` |

#### `role_permissions`

| 项 | 内容 |
|---|---|
| purpose | 角色到权限的绑定，携带 ABAC 条件与 deny 语义 |
| PK | `(role_id, permission_id, effect)` |
| FK | 均 `ON DELETE CASCADE` |
| fields | `effect`（`allow`/`deny`）、`conditions jsonb NULL`（ABAC：space/resource/classification/context 限制）、`created_at` |
| CK | `effect IN ('allow','deny')` |

#### `platform_memberships`（**2026-09-08 D-07 Round 3 决策增补 / Round 4 Hardening** — PLATFORM role 专用绑定表；当前**未建表**，实施待人工批准）

| 项 | 内容 |
|---|---|
| purpose | PLATFORM scope 角色（当前仅 `platform_admin`）的用户绑定；与 tenant/space membership 隔离的第三类成员关系 |
| PK | `id` |
| FK | `user_id → users.id ON DELETE CASCADE`；`role_id → roles.id ON DELETE RESTRICT` |
| fields | `status`（`active`/`revoked`，默认 `active`）、`revoked_at NULL`、`created_at`（首次授予时间，re-grant 不改）、`updated_at` |
| UQ | `uq_platform_memberships_user_role ON (user_id, role_id)`（每 user+role 单条历史；**re-grant = UPDATE 回 active，禁止 INSERT 新行**）；`uq_platform_memberships_active_user ON (user_id) WHERE status='active'`（一用户至多 1 个 active 平台绑定） |
| CK | `status IN ('active','revoked')` |
| TRIGGER | `tg_pm_role_scope`：引用角色必须 `scope='PLATFORM' AND status='active'`，结果态 active 时 user 须 `status='active'`（BEFORE INSERT/UPDATE）；`tg_pm_last_admin`：禁止使 active `platform_admin` 绑定数从 >0 变为 0（BEFORE UPDATE/DELETE）；均复用 RAISE → 回滚 |
| INDEX | `ix_platform_memberships_role_status ON (role_id, status) WHERE status='active'`（持有者查询 / last-admin 计数） |
| 说明 | 授权语义：无 active 绑定 → 无平台权限（default deny）；`is_system=true` 不隐含授权；grant/revoke/transfer 仅 active platform_admin（首行由 **bootstrap，一次性**），逐条写 `audit_logs(action='platform.*')`。**有效平台管理员谓词（PMB-1）** = `pm.status='active' AND u.status='active' AND r.status='active' AND r.scope='PLATFORM' AND r.key='platform_admin'`，信任根初始化后计数恒 ≥1（PM 侧 `tg_pm_last_admin` + Role 侧 `tg_roles_pm_lifecycle` 双层强制）。详见 `STEP1B_B1_3_DECISION_LOG.md` R3-2 / R4 / R5 |

#### `platform_state`（**2026-09-08 R5 Hardening 增补** — Bootstrap 初始化状态单例；migration 0006，已建表）

| 项 | 内容 |
|---|---|
| purpose | **显式、独立、不可重置**的 Platform bootstrap 状态；取代"PM row count=0"作为唯一判据（R5-1）。与 platform_memberships/users 无任何 FK 依赖 → 硬删/CASCADE 不可能重置 |
| PK | `id smallint = 1`（CK `id=1` 单例） |
| fields | `bootstrap_state` CK `('uninitialized','initialized')` 默认 `uninitialized`；`initialized_at NULL`；`created_at`；`updated_at` |
| TRIGGER | `tg_platform_state_guard`：仅允许 seed 插入 uninitialized 单例；仅允许 `uninitialized→initialized`（initialized_at 非空）；DELETE / 再插 / 回退 → RAISE；`tg_platform_state_set_updated_at`（复用 set_updated_at） |
| TRIGGER（PM 侧） | `tg_pm_bootstrap_gate`（BEFORE INSERT ON platform_memberships）：仅当 state='initialized' 或（state='uninitialized' 且 PM 无行）→ 初始化后 count=0 无法重开 bootstrap |
| 说明 | bootstrap 原子流程（服务层契约）：校验 uninitialized 且 PM 空 → 插首行 PM → 翻转 state（initialized_at=now()）→ audit `platform.admin.bootstrap` → COMMIT；recovery 不作 API（独立维护程序+人工批准）。详见 `STEP1B_B1_3_DECISION_LOG.md` R5-1 |

---

### 1.3 Resource 域

#### `resources`

| 项 | 内容 |
|---|---|
| purpose | **通用**资源注册表：Core 只管理身份、归属、分类、状态，不理解业务语义 |
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE RESTRICT`；`space_id NULL → spaces.id ON DELETE RESTRICT`；`owner_id NULL → users.id ON DELETE SET NULL` |

> **P2-03：`resources.tenant_id` / `resources.space_id` 一律 `RESTRICT`，不随 Tenant/Space 物理删除级联**。资源删除必须走受控流程：Tenant/Space **archive → soft delete → retention → controlled purge**（见 §2.7 与 §12）；purge job 先按 tenant+space 分批清 `resources`（连同域扩展表与 ACL），再清理 Tenant/Space 本身。业务数据绝不因父行删除被数据库静默级联抹掉。
> **保留 CASCADE 仅限技术/关系子实体**（白名单见 §12），并逐项说明理由：`resource_permissions.resource_id → resources.id CASCADE`（ACL 是资源的纯技术从属，随资源 purge 删除）、域扩展表 `id → resources.id CASCADE`（共享主键 1:1，生命周期完全从属 registry，随资源受控 purge 销毁）、`resource_relations` parent/child CASCADE（层级边，无独立业务数据）。
| fields | `resource_type`、`natural_key NULL`、`classification`、`status`、`label NULL`、`metadata jsonb NOT NULL DEFAULT '{}'`、`archived_at NULL`、`deleted_at NULL`、`created_at`、`updated_at` |
| UQ | `uq_resources_natural on (tenant_id, resource_type, natural_key) WHERE natural_key IS NOT NULL AND deleted_at IS NULL` |
| CK | `resource_type ~ '^[a-z][a-z0-9_.]{1,63}$'`；`classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')`；`status IN ('active','archived','deleted')` |
| lifecycle | `active → archived → deleted(soft) → purge` |

#### `acl_subject_types`（注册表 — P1/P2-04）

| 项 | 内容 |
|---|---|
| purpose | **ACL Subject 类型注册表**：把"ACL 主体是多态"这件事从字符串拼接升级为**受控的注册机制**。新增 subject type 必须先在此注册，否则 ACL 写入触发 trigger 拒绝 |
| PK | `id` |
| fields | `key`（`^[a-z][a-z0-9_]{1,31}$`）、`description`、`created_at`、`archived_at NULL` |
| UQ | `uq_acl_subject_types_key on (lower(key)) WHERE archived_at IS NULL` |
| CK | `key IN ('user','role','agent')`（**STEP 1-B 初始白名单**；**不含 `group`**） |
| 扩展 | 新增 type（含未来 `group`）：插一行注册 + 写 trigger 验证 `subject_id` 在对应表存在；删除：先归档 + 清理该 type 的所有 `resource_permissions`。**`group` 是未来扩展，不是 STEP 1-B 可用 ACL subject**（见下） |

#### `resource_permissions`（**强引用 subject，不留弱多态** — P1/P2-04 修正）

| 项 | 内容 |
|---|---|
| purpose | 资源级 ACL（显式授权/拒绝），ABAC 的落点之一。subject 引用通过**类型注册 + trigger 验证**保证完整性，**拒绝** `subject_type + subject_id` 裸字符串 |
| PK | `id` |
| FK | `resource_id → resources.id ON DELETE CASCADE`；`subject_type_id → acl_subject_types.id ON DELETE RESTRICT` |
| fields | `subject_type_id`（替代原 `subject_type`，引用注册表）、`subject_id`（受 trigger 验证存在的 uuid）、`action`、`effect`、`conditions jsonb NULL`、`inherited bool`、`expires_at NULL`、`granted_by NULL → users.id`、`created_at` |
| UQ | `uq_resource_perm on (resource_id, subject_type_id, subject_id, action)` |
| CK | `effect IN ('allow','deny')` |
| 验证 | **BEFORE INSERT/UPDATE trigger** 校验 `subject_id` 在 `acl_subject_types.key` 对应的表中存在：<br>· `key='user'` → `users.id`（不限制 `status`；软删用户保留历史 ACL）<br>· `key='role'` → `roles.id`（不限制 `archived_at`）<br>· `key='agent'` → `agents.id`（不限制 `archived_at`）<br>任何不在注册表中的 key → 拒绝写入。<br>**P2-02：STEP 1-B 不注册 `group`，trigger 也不引用不存在的 `groups` 表**。未来启用路径：CREATE groups → 注册 group subject type → 增加 group validation 分支 → 增加 ACL group 测试（见 STEP1A_ARCHITECTURE_REVIEW Round 3） |
| User 删除 | 软删：保留 ACL（用户历史行为可能引用）；硬删：trigger 级联清理 `resource_permissions` 中 subject_id=该 user 的行 |
| Role 删除 | FK `ON DELETE RESTRICT`：被 ACL 引用的 role 不可删；归档 role（`archived_at`）时由 trigger 写 audit 并在授权决策时跳过已归档 role 的 deny 行（但仍能 match allow 用于审计追溯） |

> **[`D-P11-14` 注记 · 2026-09-25]**（**append-only clarification** · 遵 `PLATFORM_DECISION_LOG.md` Charter §5.2）
> 上表「Role 删除」行中的「归档 role（`archived_at`）时**由 trigger 写 audit**」**不是 P11 实施要求**，
> 且与触发器本体论冲突（`B1-4_DEPENDENCY.md:103` 已将其登记为 **P3 文档不一致**）。
> **正式保持：`trigger does NOT write audit`。** Audit persistence **属于 `P10` Event / Audit layer**
> （`D-P10-01`…`D-P10-18`）；本行的「跳过已归档 role 的 deny 行」部分由 **Authorization Layer** 承担
> （`B1-4_SCHEMA_DESIGN.md:136`），亦非 trigger 职责。
> 关联：本文档 §1.3 `roles` 行的「Role 删除」列（被注记内容）· `D-P11-14` · `CF-2`。
> 性质：**追加说明（append-only clarification）**。**不改写本表既有行、不修改任何结论、不产生 supersession。**
> **P11 不新增** `role archive audit trigger` / `ACL audit-writing trigger`（`D-P11-14`）。
| Membership removed | **不预先清理 ACL**：`memberships.removed_at` 触发的授权决策失败记 `audit_logs(result='denied', reason='membership_removed')`；ACL 本身在成员重新加入时自动恢复有效 |
| Agent 删除 | agent 归档：trigger 标记该 agent 的所有 ACL 为 `inherited=true, expires_at=now()`（临时）使历史 ACL 自然到期，避免悬空引用 |
| 设计原则 | **不**为每个 subject_type 单独建子表 —— 触发器校验 + 注册表白名单已在工程上等价于强引用；引入专用子表会大幅增加 JOIN 与写入复杂度，而 ACL 评估主要按 `resource_id` 走，subject 反查频次低 |

#### `resource_relations`（**可选，P2**）

| 项 | 内容 |
|---|---|
| purpose | 资源层级（parent/child、belongs_to），支撑权限继承 |
| PK | `id` |
| FK | `parent_id`/`child_id` → `resources.id ON DELETE CASCADE` |
| UQ | `uq_resource_rel on (parent_id, child_id, relation_type)` |
| 说明 | 引入成本：权限评估需递归查询。建议 STEP 1-B 先不建，用 `space_id` 表达扁平归属；确有层级需求时再引入（见 §18 开放问题 Q3） |

---

### 1.4 Agent / Tool 域

#### `agents`

| 项 | 内容 |
|---|---|
| purpose | 执行实体（**不是模型**）：编排工具、策略与模型路由 |
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE RESTRICT`；`space_id NULL → spaces.id ON DELETE RESTRICT`；`owner_id → users.id ON DELETE RESTRICT`；`current_version_id NULL → agent_versions.id ON DELETE SET NULL` |
| fields | `key`、`name`、`description NULL`、`status`、`max_risk_level`、`default_route_id NULL → ai_routes.id`、`config jsonb`、`archived_at NULL`、`created_at`、`updated_at` |
| UQ | `uq_agents_key on (tenant_id, lower(key)) WHERE archived_at IS NULL` |
| CK | `status IN ('draft','active','disabled','archived')`；`max_risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` |

#### `agent_versions`

| 项 | 内容 |
|---|---|
| purpose | Agent 定义的不可变快照（发布后不可改） |
| PK | `id` |
| FK | `agent_id → agents.id ON DELETE CASCADE`；`published_by NULL → users.id ON DELETE SET NULL` |
| fields | `version int`、`definition jsonb`、`input_schema jsonb NULL`、`output_schema jsonb NULL`、`allowed_tools jsonb`、`checksum`、`status`、`published_at NULL`、`created_at` |
| UQ | `uq_agent_versions on (agent_id, version)` |
| CK | `status IN ('draft','published','deprecated','revoked')` |
| 不变性 | `status='published'` 后禁止 `UPDATE`/`DELETE`：由 trigger + 撤掉 `UPDATE` 权限双保险 |

#### `agent_permissions`

| 项 | 内容 |
|---|---|
| purpose | Agent 能碰什么（权限、工具、资源范围），是"Agent 无 DB 权限"的数据表达 |
| PK | `id` |
| FK | `agent_id → agents.id ON DELETE CASCADE`；`version_id NULL → agent_versions.id ON DELETE CASCADE`；`permission_id NULL → permissions.id ON DELETE CASCADE`；`tool_id NULL → tools.id ON DELETE CASCADE` |
| fields | `resource_scope NULL`（限定 space/resource_type）、`effect`、`conditions jsonb NULL`、`created_at` |
| UQ | `uq_agent_perm on (agent_id, COALESCE(version_id,'00000000-...'), COALESCE(permission_id,'00000000-...'), COALESCE(tool_id,'00000000-...'), COALESCE(resource_scope,''))` |
| CK | ① 至少一列非 NULL（permission_id / tool_id / resource_scope）；② `effect IN ('allow','deny')` —— D-P09-05 = B（**2 条 CHECK**；约束名待 P09 DESIGN 确定） |

#### `tools`

| 项 | 内容 |
|---|---|
| purpose | Agent 触达业务的唯一通道（Agent → Policy → Tool → Service → DB） |
| PK | `id` |
| FK | `tenant_id NULL → tenants.id ON DELETE RESTRICT`（NULL = 平台内置） |
| fields | `key`、`name`、`description NULL`、`risk_level`、`timeout_ms int`、`retry_policy jsonb`、`idempotency_mode`、`audit_policy`、`approval_required bool`、`enabled bool`、`disabled_at NULL`、`created_at`、`updated_at` |
| UQ | 平台级：`uq_tools_platform on (lower(key)) WHERE tenant_id IS NULL`；租户级：`uq_tools_tenant on (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL` |
| CK | `risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')`；`timeout_ms BETWEEN 100 AND 600000`；`idempotency_mode IN ('none','key_required','natural_key')`；`audit_policy IN ('sampling','full','full_with_payload')` |

#### `tool_versions`

| 项 | 内容 |
|---|---|
| purpose | Tool 契约快照（schema、风险、超时），发布后不可变 |
| PK | `id` |
| FK | `tool_id → tools.id ON DELETE CASCADE` |
| fields | `version int`、`input_schema jsonb NOT NULL`、`output_schema jsonb NOT NULL`、`risk_level`、`timeout_ms`、`handler_ref`、`checksum`、`status`、`published_at`、`created_at` |
| UQ | `uq_tool_versions on (tool_id, version)` |
| 不变性 | 同 `agent_versions` |

#### `tool_permissions`

| 项 | 内容 |
|---|---|
| purpose | 调用该 Tool 所需的权限 |
| PK | `id` |
| FK | `tool_id`；`version_id NULL`；`permission_id` |
| UQ | `uq_tool_perm on (tool_id, COALESCE(version_id,'0...'), permission_id)` |
| fields | `effect`、`conditions jsonb NULL`、`created_at` |

#### `tool_executions`

| 项 | 内容 |
|---|---|
| purpose | 执行记录 + **幂等锚点** + 重试依据 |
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE RESTRICT`（NN）；`tool_id → tools.id ON DELETE RESTRICT`；`tool_version_id → tool_versions.id ON DELETE RESTRICT`；`agent_id NULL → agents.id ON DELETE SET NULL`；`actor_id NULL → users.id ON DELETE SET NULL` |
| fields | `idempotency_key NULL`、`status`、`input_digest`、`output_digest NULL`、`risk_level`、`attempts int`、`started_at`、`finished_at NULL`、`duration_ms NULL`、`error_code NULL`、`correlation_id`、`created_at` |
| UQ | `uq_tool_exec_idem on (tool_id, idempotency_key) WHERE idempotency_key IS NOT NULL` |
| CK | `status IN ('running','succeeded','failed','denied','timeout')`；`attempts >= 1`；`duration_ms >= 0` —— D-P09-13（ND-01 = **3 条 CHECK**） |
| 保留 | 90 天后 hard delete（**不分区** —— D-P09-01 = B，2026-09-17；详见 §13） |

---

### 1.5 AI Gateway 域

#### `ai_providers`

| 项 | 内容 |
|---|---|
| purpose | 厂商/网关连接的**数据化**描述。厂商名是数据行，不是 Core 逻辑分支 |
| PK | `id` |
| fields | `key`、`display_name`、`adapter`（适配器注册键，代码侧注册表，如 `openai_compatible`）、`base_url NULL`、`enabled bool`、`health_status`、`health_checked_at NULL`、`privacy_tier`、`max_classification`、`capabilities jsonb`、`config jsonb`（不含密钥）、`secret_ref NULL`（指向密钥管理，**绝不存明文**）、`created_at`、`updated_at` |
| UQ | `uq_ai_providers_key on (key)` |
| CK | `privacy_tier IN ('public','vetted','private','self_hosted')`；`max_classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')`；`health_status IN ('unknown','healthy','degraded','down')` |

#### `ai_models`

| 项 | 内容 |
|---|---|
| purpose | 模型能力、成本、合规上限的目录 |
| PK | `id` |
| FK | `provider_id → ai_providers.id ON DELETE CASCADE` |
| fields | `model_key`、`display_name`、`capabilities jsonb`、`context_window int`、`max_output_tokens NULL`、`input_price_per_1k numeric NULL`、`output_price_per_1k numeric NULL`、`max_classification`、`is_private bool`、`latency_p95_ms NULL`、`enabled bool`、`created_at`、`updated_at` |
| UQ | `uq_ai_models on (provider_id, model_key)` |
| CK | `max_classification IN (...)`；`context_window > 0` |

#### `ai_routes`

| 项 | 内容 |
|---|---|
| purpose | capability → model 的路由与 fallback 链 |
| PK | `id` |
| FK | `tenant_id NULL → tenants.id ON DELETE RESTRICT`（平台默认）、`space_id NULL → spaces.id ON DELETE RESTRICT`、`primary_model_id → ai_models.id ON DELETE RESTRICT` |
| fields | `capability`、`priority int`、`fallback_chain jsonb`（`[{model_id, when: {...}}]`）、`enabled bool`、`created_at`、`updated_at` |
| UQ | `uq_ai_routes on (COALESCE(tenant_id,'0...'), COALESCE(space_id,'0...'), capability, priority)` |
| CK | `capability IN ('chat','embeddings','rerank','vision','audio_asr','audio_tts','moderation')` |

#### `ai_policies`

| 项 | 内容 |
|---|---|
| purpose | 数据分级 → 供应商准入 / fallback / 预算 / 延迟约束 |
| PK | `id` |
| FK | `tenant_id NULL → tenants.id ON DELETE RESTRICT`、`space_id NULL → spaces.id ON DELETE RESTRICT` |
| fields | `name`、`max_classification`、`allowed_privacy_tiers jsonb`、`denied_providers jsonb`、`require_private bool`、`allow_fallback bool`、`fallback_preserves_classification bool DEFAULT true`、`budget_daily_usd NULL`、`latency_budget_ms NULL`、`redaction_profile NULL`、`enabled bool`、`created_at`、`updated_at` |
| UQ | `uq_ai_policies on (COALESCE(tenant_id,'0...'), COALESCE(space_id,'0...'), lower(name))` |
| CK | `allow_fallback = false OR fallback_preserves_classification = true`（**禁止绕过分级的降级**） |

#### `ai_request_logs`

| 项 | 内容 |
|---|---|
| purpose | 成本 / 配额 / 可观测（不是审计，不存 prompt 原文） |
| PK | `(id, occurred_at)`（分区键必须进 PK） |
| fields | `tenant_id NULL`、`space_id NULL`、`actor_id NULL`、`agent_id NULL`、`provider_id NULL`、`model_id NULL`、`capability`、`classification`、`prompt_tokens int NULL`、`completion_tokens int NULL`、`cost_usd numeric NULL`、`latency_ms int NULL`、`status`、`error_code NULL`、`correlation_id`、`occurred_at` |
| 分区 | 按月 RANGE（`occurred_at`） |

---

### 1.6 Event / Audit 域

#### `events`（**at-least-once** 事务性 outbox + 事件日志 — P1-03 修正）

| 项 | 内容 |
|---|---|
| purpose | 领域事实 + **transactional outbox**。明确语义：**at-least-once delivery**（绝不承诺 exactly-once；消费方必须按 `event_id` 幂等） |
| PK | `(id, occurred_at)` |
| fields | `event_type`、`schema_version int`、`tenant_id NULL`、`space_id NULL`、`actor_type NULL`、`actor_id NULL`、`subject_type NULL`、`subject_id NULL`、`payload jsonb NOT NULL`、`correlation_id NULL`、`causation_id NULL`、`occurred_at`、`status`、`worker_id NULL`、`claimed_at NULL`、`lease_expires_at NULL`、`attempts int DEFAULT 0`、`next_attempt_at NULL`、`last_error NULL`、`delivered_at NULL` |
| CK | `event_type ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'`；`status IN ('pending','claimed','delivered','dead')`；`attempts >= 0`；`attempts <= 100`（防失控） |
| 状态机 | `pending → claimed → delivered`（成功路径）；`pending → claimed → pending`（重试路径，attempts++）；`pending → claimed → dead`（超阈值） |
| 投递器（CAS） | 1) `UPDATE events SET status='claimed', worker_id=$w, claimed_at=now(), lease_expires_at=now()+interval '60s' WHERE id=$id AND status='pending' AND next_attempt_at<=now() RETURNING payload,...` 2) 发送 Webhook 3) `UPDATE ... SET status='delivered' WHERE id=$id AND status='claimed' AND worker_id=$w` 4) 失败：`UPDATE ... SET status='pending', attempts=attempts+1, next_attempt_at=now()+exp_backoff, last_error=...` |
| Lease Reaper | 周期 job：`UPDATE events SET status='pending', next_attempt_at=now(), last_error='lease expired' WHERE status='claimed' AND lease_expires_at < now()` —— Worker 崩溃后由其他 Worker 接管 |
| 多实例抢锁 | **CAS 取代 SKIP LOCKED**：单行 UPDATE 上的 status 条件本身就是乐观锁，多 worker 同时 claim 同一行只有一个能成功；其余 0 行受影响，跳过该事件 |
| 三个崩溃场景 | 见 §8.2 重写章节 |
| 分区 | 按月（投递完成 30 天后清理；dead 行保留 90 天供人工复盘） |

#### `audit_logs`

| 项 | 内容 |
|---|---|
| purpose | 合规记录：谁、何时、对什么、做了什么、结果、从哪、为什么 |
| PK | `(id, occurred_at)` |
| fields | `occurred_at`、`tenant_id NULL`、`space_id NULL`、`actor_type`、`actor_id NULL`、`actor_ip inet NULL`、`actor_user_agent text NULL`、`action`、`resource_type NULL`、`resource_id NULL`、`classification`、`result`、`risk_level`、`reason NULL`、`correlation_id NULL`、`request_id NULL`、`metadata jsonb`（**写入前已脱敏**）、`created_at` |
| CK | `result IN ('success','denied','error')`；`risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` |
| 不变性 | 无 `updated_at`、无 `deleted_at`；DB 角色仅 `INSERT, SELECT`；append-only 由权限 + trigger 保证 |
| 分区 | 按月；保留期见 §13 |

---

## 2. Tenant / Space 模型（含 8 个必答问题）

### 2.1 Tenant 与 Space 的区别

| 维度 | Tenant | Space |
|---|---|---|
| 本质 | 治理与隔离边界（账单、配额、策略、数据隔离） | 协作与上下文边界（成员、资源、Agent 作用域） |
| 数量级 | 少（每客户 1 个起） | 多（每租户 N 个） |
| 是否跨 | 用户可跨租户 | Space 严格属于单一租户 |
| 删除影响 | 全量 purge | 仅该空间数据 |
| 谁创建 | 平台/开通流程 | 租户内管理员 |

一句话：**Tenant 是"墙"，Space 是"房间"**。墙决定谁能进这栋楼，房间决定这批人一起做什么。

### 2.2 一个 User 能否属于多个 Tenant？

**能。** `users` 是全局表（不属于任何租户），归属由 `tenant_memberships` 表达。同一 `user_id` 可在多行 `tenant_memberships` 中出现。
用户切换租户时切换 `tenant_id` 上下文；全局 profile 不变。

### 2.3 一个 User 能否属于多个 Space？

**能。** `memberships` 以 `(space_id, user_id)` 唯一，同一用户可在多个 Space。

### 2.4 Membership 属于 Tenant 还是 Space？

**两层都存在，语义不同**：
- `tenant_memberships`：租户成员资格（是否能进入该租户）
- `memberships`：Space 成员资格 + 角色（在该空间里能做什么）

`memberships.tenant_id` 为**冗余列**，用途：租户隔离索引、避免 JOIN 上溯、RLS 策略直接可用。一致性由 trigger 保证（`memberships.tenant_id = spaces.tenant_id`）。

### 2.5 Role 是 Tenant 级、Space 级还是两者都支持？

**两者都支持，外加平台级**：`roles.scope ∈ {PLATFORM, TENANT, SPACE}`，三者互斥（部分唯一索引 + trigger 校验 scope 与 tenant_id/space_id 是否为空必须匹配）。

**系统内置角色目录**（`is_system=true`，不可改；播种方式见下）—— 每个 scope 有各自独立的关键字命名空间，**默认角色按 scope 就近命名，不跨 scope 复用**：

| scope | 判定 | 内置角色（STEP 1-B 播种） | 用途 |
|---|---|---|---|
| `PLATFORM` | `tenant_id IS NULL AND space_id IS NULL` | `platform_admin` | 平台根管理（跨租户运维），只授予平台运维身份 |
| `TENANT` | `tenant_id` 非空、`space_id` 空 | `tenant_admin`、**`tenant_member`** | 租户管理；**`tenant_member` 是 `tenant_memberships.role_id` 的默认角色** |
| `SPACE` | `space_id` 非空 | `space_admin`、**`space_member`** | 空间管理；`space_member` 是空间默认成员角色（由 Space 创建流程写入 `memberships.role_id`） |

> **P2-01 消歧**：`member` 这个名字**不作为任何 scope 的默认角色**。租户默认角色是 **`tenant_member`（TENANT scope）**——避免"默认 `member`，但 `member` 又挂在 PLATFORM"的语义冲突。三 scope 的 key 命名空间相互独立（部分唯一索引各自约束），`tenant_member`、`space_member`、`platform_admin` 之间不存在重名歧义。

**播种语义**（`is_system=true` 角色**不是**全局单行）：
- `platform_admin`：全局 1 行（`tenant_id NULL, space_id NULL`）
- `tenant_admin` / `tenant_member`：**每租户 1 行**（`tenant_id = 各自租户 id`）—— 因为 trigger 要求 `tenant_memberships.role_id` 指向的 role 其 `tenant_id = 本行 tenant_id`
- `space_admin` / `space_member`：**每空间 1 行**（`space_id = 各自空间 id`）

`roles` 表结构中的 `tenant_id NULL → tenants.id ON DELETE CASCADE` / `space_id NULL → spaces.id ON DELETE CASCADE` 只用于**租户/空间受控 purge** 时清理其配置行（角色是权限配置，不承载独立业务数据；见 §2.7/§12 删除策略白名单）。

有效权限计算（见 §3）：**Space 级角色权限 ∪ 该用户在 Space 所属租户的 TENANT 级角色权限**（租户权限向下继承到所有 Space），deny 优先。

### 2.6 Permission 如何继承？

```
PLATFORM role ─┐
TENANT   role ─┼─→ 有效权限集合 ─→ ABAC 过滤 ─→ Resource ACL ─→ 决策
SPACE    role ─┘
```

- 方向：**只向下**（Tenant 权限在其所有 Space 生效；Space 权限不上溯）
- 冲突：`deny` 绝对优先于任何层级的 `allow`
- 资源显式 ACL（`resource_permissions`）可覆盖继承结果（仍然 deny 优先）
- `role_permissions.conditions` 是 ABAC 的静态条件（如对特定 space/resource_type 生效）

### 2.7 Space 删除 / 归档后数据怎么办？

三阶段，**不做物理级联删除**：

1. **archive**（`status='archived'`，`archived_at`）：只读，成员保留，Agent 停止调度，界面隐藏。可恢复。
2. **delete**（`status='deleted'`，`deleted_at`）：软删除。该 Space 的 `resources` 同步置 `deleted_at`（异步 job，按 tenant 分批处理）；`memberships` 置 `removed_at`。
3. **purge**（retention job，默认归档后 90 天 / 软删后 30 天）：按 tenant + space 批量 `DELETE`，顺序自底向上（子表 → 父表），每批 ≤ 1000 行，记录到 `audit_logs`。

**删除策略总则（P2-03 统一）**：业务实体（含 `resources`、域扩展表、一切可承载独立业务价值的行）一律 `ON DELETE RESTRICT`；`ON DELETE CASCADE` **只允许**用于技术/关系子实体（sessions/credentials/versions/ACL/纯关系行/纯配置行），且必须逐项说明理由（完整白名单见 §12）。**`users`/`tenants`/`spaces` 的删除不得级联删除业务数据**——所有清理走 archive → soft delete → retention → controlled purge。

### 2.8 Tenant Isolation 如何保证？

四层，缺一不可：

1. **模式层**：所有租户范围表带 `tenant_id NOT NULL`（平台级表除外），复合索引以 `tenant_id` 打头
2. **应用层**：查询必须携带 tenant scope；仓储层强制注入，提供 `require_same_tenant()` 断言（已在 `core/tenant` 定义）
3. **隔离层（推荐启用）**：PostgreSQL RLS，`app.tenant_id` 会话变量 + `USING (tenant_id = current_setting('app.tenant_id')::uuid)`。注意与连接池配合：必须在事务内 `SET LOCAL`，连接归还前重置
4. **审计层**：跨租户访问尝试写入 `audit_logs`，`result='denied'`，`risk_level='CRITICAL'`

> RLS 是否随 STEP 1-B 启用属开放问题（Q1），设计上预留。

---

## 3. Authorization Model（RBAC + ABAC）

### 3.1 Pipeline（P1-01 修正：Role Resolution + Deny Resolution 显式分阶段）

```
[1] Authentication          → 谁？（session/token → user + identity + device）
      │
[2] Tenant Resolution       → 在哪个租户下？（tenant_memberships.status='active'）
      │  fail                 → DENY (reason='not_tenant_member')
      ▼
[3] Space Resolution        → 在哪个空间下？（memberships.status='active'，含跨空间列表）
      │  fail                 → DENY (reason='not_space_member')
      ▼
[4] Role Resolution         → 收集该用户在该 Space 的所有有效 role：
      │                          - PLATFORM role（始终生效，与 tenant 无关）
      │                          - TENANT role（取 tenant_memberships.role_id）
      │                          - SPACE role（取 memberships.role_id）
      │  fail (无 role)         → DENY (reason='no_role')
      ▼
[5] Permission Resolution   → 上述 roles 全部 JOIN role_permissions，得到 allow 集 ∪ deny 集
      ▼
[6] Deny Resolution         → 任一 deny 命中 action → DENY (reason='explicit_deny' 或 'role_deny')
      │  （deny 压过一切，**包括 Resource ACL 里的 allow**）
      ▼
[7] ABAC Condition          → 求值 role_permissions.conditions + role_conditions
      │                          subject: user_id, identity_id, membership_role, tenant_id
      │                          resource: resource_type/id, owner_id, classification, status, space_id
      │                          action: action, risk_level, is_write, is_bulk
      │                          context: time/ip/geo/device_trust/session_age/mfa_age
      │                          environment: tenant_status, space_status, feature_flags
      │  condition 不成立       → 该 permission 行视为不存在
      │  求值异常 (fail-closed) → DENY (reason='abac_eval_error')
      ▼
[8] Resource ACL            → 显式 ACL 叠加（resource_permissions）：
      │                          - allow 行：可补充 role 未授予的权限
      │                          - deny 行：再次压过
      │  subject 解析：
      │                          - subject_type_id 必须在 acl_subject_types 注册
      │                          - subject_id 须 trigger 验证存在
      │                          - membership_removed 时不预先清理 ACL，由本阶段实时校验失败
      ▼
[9] Final Decision          → 任一环节 deny → DENY
      │                       未匹配任何 allow → DENY (reason='default-deny')
      │                       错误即拒绝 (fail-closed)
      ▼
  ALLOW  /  DENY  +  reason + 决策 trace（不写入 payload）
```

> **关键不变量**：步骤 [6] 的 deny 是绝对压过——即便步骤 [8] Resource ACL 给了 allow，也会被压回 DENY。这是有意的安全设计："Deny 写在哪里都生效"。

### 3.2 决策规则

- **Default Deny**：未匹配任何 allow 规则 → `DENY`，`reason='default-deny'`
- **Deny 优先**：任何 deny 命中即拒绝，无论其他 allow
- **错误即拒绝**：评估过程异常 → `DENY`（fail-closed），并记录 error 审计
- **全链路审计**：每次决策（含 allow）写入 `audit_logs`；高频读路径可采样（`LOW` 风险采样 10%）

### 3.3 ABAC 属性维度

| 类别 | 属性 |
|---|---|
| subject | `user_id`、`identity_id`、`membership_role`、`tenant_id` |
| resource | `resource_type`、`resource_id`、`owner_id`、`classification`、`status`、`space_id` |
| action | `action`、`risk_level`、`is_write`、`is_bulk` |
| context | `time`（时间窗）、`ip`/`geo`、`device_trust`、`session_age`、`mfa_age` |
| environment | `tenant_status`、`space_status`、`feature_flags` |

条件以 `jsonb` 存储，求值器实现在 Core（`core/policy`），**不在 SQL 里做条件求值**（避免把授权逻辑塞进数据库）。

### 3.4 与现有代码的关系

`core/permission` 已定义 `Subject` / `Action` / `Decision` / `DENY`；STEP 1-B 只需补持久化与求值器，接口不变。

---

## 4. Resource Model

### 4.1 是否需要 polymorphic resource reference？

**需要"多态"的能力，但不要用无外键的 `(resource_type, resource_id)` 弱引用。**

三种方案对比：

| 方案 | 描述 | 引用完整性 | 评价 |
|---|---|---|---|
| A. 单表多态 | `resources` 存全部数据，`resource_type` 区分 | 强（单表） | Core 无法承载业务字段，域被迫塞 jsonb → 不可接受 |
| B. 弱引用 | 各处存 `resource_type + resource_id`，无 FK | **无** | 删除后悬空、无法级联、查询需应用层拼装 → 不可接受 |
| C. **注册表 + 共享主键（推荐）** | `resources` 存身份/归属/分类/状态；Domain 业务表以 `id REFERENCES resources(id)` 做 1:1 扩展 | **强** | 兼顾统一治理与强约束 |

**采用方案 C**：

```
resources(id PK, tenant_id, space_id, resource_type, owner_id, classification, status, ...)
        ▲
        │ 1:1  (domain 表 id 既是 PK 也是 FK)
        │
domain_<x>(id PK REFERENCES resources(id) ON DELETE CASCADE, ...业务字段)
```

- 写入：同一事务内先插 `resources` 再插域表
- 删除：删 `resources` → 域表级联；或先删域表再删 registry
- Core 侧：权限/审计/分类只查 `resources`，永远不 JOIN 域表 → Core 与 Domain 解耦
- Domain 侧：业务查询 JOIN `resources` 取归属与分类
- 纯 Core 资源（无域扩展）：只有 `resources` 一行

### 4.2 分类与权限

- `classification` 驱动 AI 准入（§8）与审计力度
- `resource_permissions` 提供显式 ACL；`inherited=true` 表示来自父资源/空间继承
- `resource_permissions.expires_at` 支持临时授权

---

## 5. Agent / Tool Model

### 5.1 Agent ≠ Model

| | Agent | Model |
|---|---|---|
| 是什么 | 执行实体（有状态、有权限、有版本） | 无状态推理服务 |
| 存储 | `agents` + `agent_versions` | `ai_models`（由 provider 提供） |
| 选择模型 | 通过 `ai_routes` 与 `ai_policies` 间接决定 | 被动 |
| 能做什么 | 由 `agent_permissions` 限定 | 只产出文本/向量 |

### 5.2 执行链路（数据层面的强制）

```
agents ──(agent_permissions)──→ tools ──(tool_permissions)──→ permissions
   │                              │
   └──→ ai_routes → ai_policies   └──→ tool_executions（幂等 + 审计）
```

**Agent 不持有数据库权限**：
- 数据库层面不存在 `agent` 角色；所有查询以应用服务账号执行
- `agents` 表**不存储**任何连接串/凭据；`config jsonb` 中禁止出现 DSN（CI 扫描项）
- `agent_permissions` 是**白名单**：未列出的 tool/permission 一律拒绝
- 未来若需强隔离：为 Agent 执行建立独立 DB role + RLS，但那是 STEP 2+ 议题

### 5.3 Tool Risk Level 执行策略

| Risk | 前置条件 | 审批 | 审计 | 幂等 | 超时/重试 |
|---|---|---|---|---|---|
| **LOW** | 权限校验通过 | 无 | 采样（10%） | 建议 | 5s，最多 2 次 |
| **MEDIUM** | 权限 + ABAC | 无 | 全量（不含 payload） | 建议 | 15s，最多 3 次，指数退避 |
| **HIGH** | 权限 + ABAC + 风险策略 | **可配置人工审批**（`approval_required`） | 全量（含 input digest） | **必须**（`idempotency_mode != 'none'`） | 60s，最多 2 次 |
| **CRITICAL** | 权限 + ABAC + 风险策略 + **强制人工审批** | **必须** | 全量（含 payload 摘要 + 审批人） | **必须** | 300s，不自动重试 |

通用约束：
- `risk_level` 高于 Agent 的 `max_risk_level` → 拒绝执行
- CRITICAL 工具默认 `enabled=false`，需显式启用
- 所有执行写 `tool_executions`，`denied` 也要写（审计不能只记成功）
- 重试只对**幂等**工具生效；非幂等工具 `retry_policy.max_attempts = 1`

---

## 6. AI Gateway Model

### 6.1 抽象层次

```
ai_policies (租户/空间：分级、准入、预算、是否允许降级)
     ↓ 约束
ai_routes   (capability → primary model + fallback chain)
     ↓ 选择
ai_models   (能力、成本、延迟、max_classification、是否私有)
     ↓ 属于
ai_providers(适配器、base_url、隐私档位、健康状态、密钥引用)
```

未来接入 OpenAI / Anthropic / Google / DeepSeek / Qwen / GLM / Ollama / vLLM / OpenAI-compatible / 私有模型，**全部是往 `ai_providers` + `ai_models` 插数据**，Core 代码零改动、零 SDK 依赖（`tests/architecture` 持续强制）。

`ai_providers.adapter` 是**适配器注册键**（如 `openai_compatible`），指向 `intelligence/providers` 中已注册的适配器；它不是 `if provider == 'openai'` 这种业务分支。

### 6.2 路由决策顺序

1. 取请求 `capability` 与数据 `classification`
2. 匹配 `ai_policies`（space > tenant > platform，取最具体的启用策略）
3. 取 `ai_routes`（同上优先级，按 `priority` 升序尝试）
4. 主模型校验：`model.max_classification >= 请求分级`、`provider.privacy_tier ∈ allowed_privacy_tiers`、`provider.enabled`
5. 失败时按 `fallback_chain` 依次尝试，**每个候选重新执行第 4 步校验**
6. 全失败 → 返回错误，**绝不降级到不合规模型**

### 6.3 关键不变式

> **HIGHLY_CONFIDENTIAL 数据永不因主 Provider 故障而落到公共模型。**

由三重保障：
- `ai_models.max_classification`：模型自身的合规上限
- `ai_policies.require_private` + `allowed_privacy_tiers`：租户级准入
- `CK: allow_fallback = false OR fallback_preserves_classification = true`：数据库层面的硬约束

---

## 7. Data Classification

| 级别 | 含义 | 默认 AI 准入 | 审计 |
|---|---|---|---|
| `PUBLIC` | 可公开 | 任意 enabled provider | 采样 |
| `INTERNAL` | 内部信息，外泄影响有限 | provider.privacy_tier ∈ {vetted, private, self_hosted} | 全量 |
| `CONFIDENTIAL` | 个人/商业敏感 | provider.privacy_tier ∈ {private, self_hosted} | 全量 + payload 摘要 |
| `HIGHLY_CONFIDENTIAL` | 凭据、医疗、财务核心、未成年人数据 | **仅 self_hosted**，`require_private=true`，**禁止跨 provider 降级** | 全量 + 独立告警 |

流向：

```
Data (resource.classification)
  → Classification
  → AI Policy (ai_policies.max_classification)
  → Provider Eligibility (ai_providers.privacy_tier + ai_models.max_classification)
  → 允许 / 拒绝（拒绝写 audit，risk=HIGH）
```

分类只能**升**不能随意降：降低 classification 需写 `audit_logs` 并注明 `reason`。

---

## 8. Event / Audit Model

### 8.1 为什么要分开

| | Event | Audit |
|---|---|---|
| 语义 | "发生了什么"（事实） | "谁对什么做了什么、结果如何"（责任） |
| 消费方 | 系统内部（投递、集成、Webhook） | 合规、安全、用户可见历史 |
| 可否删除 | 投递后可清理 | **不可变**，只按保留期整分区 drop |
| 是否重放 | 可 | 不可（重放会产生误导） |
| 是否含决策理由 | 否 | 是（`reason`、`risk_level`） |
| 存储 | `events`（outbox） | `audit_logs` |

### 8.2 events — **at-least-once** transactional outbox（P1-03 修正）

**核心承诺**：`Event delivery = at-least-once`；`Consumer = idempotent by event_id`。
**绝不**承诺 exactly-once —— 本系统（应用 + DB + Webhook target）无法证明端到端 exactly-once 语义。

#### 8.2.1 写入与投递（业务事务 + CAS claim）

```sql
-- 业务事务内同时写事件
BEGIN;
  INSERT INTO resources (...);
  INSERT INTO events (id, occurred_at, event_type, payload,
                      status='pending', attempts=0, next_attempt_at=now(), ...)
  VALUES (...);
COMMIT;

-- 投递器（单实例也可多实例并行）
-- 步骤 1：CAS claim（一行 UPDATE 既是原子 claim 又是乐观锁）
UPDATE events
SET    status='claimed',
       worker_id=$worker,
       claimed_at=now(),
       lease_expires_at=now() + interval '60 seconds'
WHERE  id IN (
         SELECT id FROM events
         WHERE  status='pending'
         AND    next_attempt_at <= now()
         ORDER  BY next_attempt_at
         LIMIT  100
         FOR UPDATE SKIP LOCKED
       )
RETURNING id, payload, event_type, correlation_id, attempts;

-- 步骤 2：调用外部 Webhook / handler
-- 步骤 3a：成功
UPDATE events SET status='delivered', delivered_at=now(), lease_expires_at=NULL
WHERE  id=$id AND status='claimed' AND worker_id=$worker;

-- 步骤 3b：失败（可重试）
UPDATE events
SET    status='pending',
       attempts = attempts + 1,
       next_attempt_at = now() + (interval '1 second' * power(2, attempts)),
       last_error = $err,
       lease_expires_at = NULL
WHERE  id=$id AND status='claimed' AND worker_id=$worker;

-- 步骤 3c：超阈值
UPDATE events SET status='dead', lease_expires_at=NULL, last_error='max_attempts_exceeded'
WHERE  id=$id AND status='claimed' AND worker_id=$worker AND attempts >= 8;
```

#### 8.2.2 Lease Reaper（Worker 崩溃恢复）

周期 job（建议 30s）：
```sql
UPDATE events
SET    status='pending',
       next_attempt_at = now(),
       last_error = COALESCE(last_error,'') || 'lease_expired:',
       lease_expires_at = NULL
WHERE  status='claimed'
AND    lease_expires_at < now()
RETURNING id;
```
被 reaper 拉回 pending 的事件，由任一 worker 重新 claim。

#### 8.2.3 三个崩溃场景的处理

| 场景 | 现象 | 处理 |
|---|---|---|
| **A. Worker claim 后崩溃** | 事件处于 `claimed`，`lease_expires_at` 未到 | Lease Reaper 周期扫描到过期 → 改回 `pending` 并重试。**注**：如 Worker 在 lease 期内重启，会出现"两个 Worker 都认为自己是 owner"；**消费方按 `event_id` 幂等**解决了该问题 |
| **B. Webhook 已发但写 delivered 失败** | 业务侧实际收到事件，DB 仍是 `claimed` | ① 重新投递会**重复发送** Webhook（at-least-once 保证）<br>② **消费方必须**用 `event_id` 去重（最简：维护本地 `(event_id, processed_at)` 集合，命中即 ack 不执行）<br>③ Core 侧无法消除该重复，**这是 at-least-once 的固有代价** |
| **C. 两个 Worker 同时 claim 同一行** | 各自执行步骤 1 | 步骤 1 的 UPDATE 是单行原子操作，**只有一个**能成功（其他 0 行受影响），CAS 自动胜出。`SKIP LOCKED` 只是减少行级锁等待，并不构成投递保证；CAS 才是保证 |

#### 8.2.4 幂等保障

- **事件层**：`event_id`（= PK）做天然幂等键，消费方按此去重
- **Tool 层**：另有 `tool_executions.(tool_id, idempotency_key)` 部分唯一约束做执行幂等
- **投递层**：`FOR UPDATE SKIP LOCKED` 是性能优化（避免锁等待），**不是**正确性保证；正确性由 §8.2.1 的 CAS claim 步骤 1 保证

#### 8.2.5 Dead 行处理

- 超阈值（默认 8 次）置 `dead` + 写 `audit_logs(result='error', action='event.delivery.failed', risk_level='HIGH')` + 触发告警
- 人工介入：重置 `attempts=0, status='pending', next_attempt_at=now()` 重投；或确认放弃后归档

#### 8.2.6 死信 vs 终态

- **`dead` ≠ 已交付**：消费方不会收到 `dead` 事件，必须显式重投
- **消费方不能假设**"没收到 Webhook = 业务未发生"：业务事务内已 commit，事件可能仍在 pending 队列等待

### 8.3 audit_logs 字段覆盖

| 问题 | 字段 |
|---|---|
| 谁 | `actor_type`, `actor_id` |
| 什么时候 | `occurred_at`（UTC） |
| 对什么 | `resource_type`, `resource_id` |
| 做了什么 | `action` |
| 结果 | `result`, `error_code` |
| 从哪 | `actor_ip`, `actor_user_agent` |
| 为什么 | `reason` |
| 关联 | `correlation_id`, `request_id` |
| 风险 | `risk_level`, `classification` |
| 上下文 | `metadata jsonb`（**写入前脱敏**） |

### 8.4 脱敏

- 写入前统一过 `infrastructure/logging/redaction` 的 `redact_mapping()`
- `metadata` 禁止出现：密码、token、API key、完整请求体（除非 `risk_level='CRITICAL'` 且策略允许存摘要）
- CRITICAL 工具执行只存 `input_digest`（SHA-256 前 16 位），不存原文

---

## 9. ID 策略：UUIDv7

### 9.1 候选评估

| 维度 | BIGINT | UUIDv4 | **UUIDv7** |
|---|---|---|---|
| 索引局部性 | 优 | **差**（随机插入 → 页分裂、WAL 放大） | 优（时间前缀单调递增） |
| 排序 | 天然有序 | 无序 | 近似时间序（ms 粒度） |
| 分布式生成 | 需协调（snowflake） | 自由 | 自由 |
| 跨库迁移 | 冲突风险高 | 安全 | 安全 |
| 枚举攻击 | **易**（顺序可猜） | 安全 | 中等（时间可推断，随机位 62 bit） |
| 存储 | 8B | 16B | 16B |
| 日志追踪 | 好 | 好 | 好（可从 ID 反推时间） |

### 9.2 结论

**UAP Core 标准 ID = UUIDv7**（`uuid` 类型，RFC 9562）。

- 主键、外键统一 UUIDv7
- 生成位置：**应用层为主**（Python 侧生成，可批量预生成、可跨库一致）；数据库提供 `uap_uuid_v7()` 兜底函数供 migration 回填与手工运维（STEP 1-B 实现）
- 分区表（`events`/`audit_logs`/`ai_request_logs`）主键为 `(id, occurred_at)`

### 9.3 隐私取舍

UUIDv7 会泄露创建时间（毫秒）。因此：
- 面向外部的**不透明标识**（邀请码、分享链接、密码重置 token）使用 **UUIDv4** 或独立随机串，不用 v7
- 若某资源类型需要隐藏创建时间，其对外暴露 ID 使用单独的 `public_id`（v4）
- 枚举风险由授权层（`resource_permissions` + tenant scope）承担，不靠 ID 不可猜

---

## 10. 时间策略

| 规则 | 内容 |
|---|---|
| 类型 | **只用 `timestamptz`**，禁用 `timestamp`（无时区） |
| 存储 | PostgreSQL 以 UTC 存储，`timestamptz` 自动转换 |
| 会话 | 应用连接设置 `TIME ZONE 'UTC'`，避免 session 时区影响 |
| 命名 | `created_at`、`updated_at`、`deleted_at`、`archived_at`、`expires_at`、`occurred_at`、`*_at` 统一后缀 |
| `updated_at` | **数据库 trigger** 维护（`BEFORE UPDATE ... SET updated_at = now()`），不依赖应用层 |
| 分区键 | 一律 UTC 月边界 |
| 比较 | 全部在 SQL 层用 UTC 比较；展示层按用户时区格式化 |
| 精度 | `timestamptz(3)`（毫秒）——UUIDv7 与延迟统计同为毫秒级，避免微秒带来的无意义精度 |

时间字段语义：

| 字段 | 含义 |
|---|---|
| `created_at` | 记录创建 |
| `updated_at` | 最后一次变更（trigger 维护） |
| `deleted_at` | 软删除时间 |
| `archived_at` | 归档时间（只读保留） |
| `expires_at` | 到期（session、credential、临时授权） |
| `occurred_at` | 事件发生时间（审计/事件表，**业务时间**，可能回填） |
| `revoked_at` | 撤销时间（设备、会话、凭据） |

---

## 11. Delete / Retention 策略

**不做全局 soft delete**。逐类判定：

| 实体 | 策略 | 理由 |
|---|---|---|
| `users` | **soft delete**（`deleted_at`） | 外键众多；合规要求保留"谁做过什么"。硬删除由 retention job 在 N 天后执行并匿名化审计中的 PII |
| `identities` | **revoke**（`revoked_at`），随 user 级联 | 撤销即失效；保留用于追溯登录来源 |
| `credentials` | **hard delete**（撤销/过期后） | 存的是哈希与秘密材料，保留无价值且增加泄露面；rotation 留新不留旧 |
| `devices` | **revoke**（不可恢复） | 安全审计需要"这台设备曾存在并被吊销" |
| `sessions` | **expire / revoke + hard delete** | 量最大、价值随时间归零；过期即删，不留软删标记 |
| `tenant_memberships` | **soft delete**（`removed_at`） | 保留"曾是成员"的历史 |
| `memberships` | **soft delete**（`removed_at`） | 同上 |
| `tenants` | **archive → soft delete → purge** | 涉及计费与法律留存，必须可恢复 |
| `spaces` | **archive → soft delete → purge** | 数据不可静默消失 |
| `resources` | **soft delete**（`deleted_at`），受控 purge | 域数据需要可恢复窗口；purge 时域扩展表与 ACL 随行删除（见下方 CASCADE 白名单） |
| `resource_permissions` | **hard delete**（随资源 purge / 到期） | 授权关系失效即无意义；到期记录已在 audit |
| `agents` | **disable / archive**（版本不删） | 已发布版本必须可追溯，否则无法复现历史决策 |
| `agent_versions` | **immutable**（只能 deprecate/revoke） | 同上 |
| `tools` | **disable**（`enabled=false`），版本不可删 | 同上 |
| `tool_versions` | **immutable** | 同上 |
| `tool_executions` | **hard delete**（**不分区**，90 天 —— D-P09-01 = B） | 高吞吐运维数据 |
| `events` | **hard delete**（分区，投递后 30 天） | outbox 语义，投递完成即失去价值 |
| `audit_logs` | **immutable + 分区 drop**（默认 1 年，可配置） | 合规留存；不做行级删除 |
| `ai_request_logs` | **hard delete**（分区，90 天） | 成本运维数据 |

**保留期默认值**（可配置）：audit 365 天、events 30 天、tool_executions 90 天、ai_request_logs 90 天、软删数据 30 天后 purge、归档空间 90 天后 purge。

### 11.1 FK `ON DELETE CASCADE` 白名单（P2-03 统一，逐项理由）

> 业务实体一律 RESTRICT；CASCADE **只允许**出现在下面两类中。**凡不在白名单者，一律 RESTRICT**。

| 类别 | 关系 | 保留 CASCADE 的理由 |
|---|---|---|
| 技术子实体 | `users → sessions`（`sessions.user_id`） | session 无独立业务价值，随用户硬删消失；不涉及业务数据丢失 |
| 技术子实体 | `users → credentials`、`identities → credentials` | 凭据哈希随主体删除，留存量无意义且扩大泄露面 |
| 技术子实体 | `users → devices` | 设备注册行随用户删除；审计追溯靠 audit_logs 而非 devices 行 |
| 技术子实体 | `users → identities` | 身份源行随用户删除；revoke 历史由 audit_logs 承担 |
| 技术子实体 | `devices → sessions`、`users → sessions`（user_id） | 会话是纯运行时技术行 |
| 版本快照 | `agents → agent_versions`、`tools → tool_versions` | 版本是父实体定义的**纯从属快照**；父实体受控 purge 时整棵删除（正常路径不可变，仅 purge/revoke 触发） |
| 版本快照 | `agents → agent_permissions`、`tools → tool_permissions`、`roles → role_permissions` | 权限绑定是配置行，无独立业务数据 |
| 关系行 | `tenants → tenant_memberships`、`spaces → memberships`、`users → tenant_memberships`、`users → memberships` | membership 是纯关系行，随任一端 purge 清理；成员历史由 audit_logs 承担 |
| 配置行 | `tenants → roles`（tenant 级）、`spaces → roles`（space 级） | role 定义随父实体 purge 清理；`role_id` 被引用处一律 RESTRICT 保证无悬空 |
| 技术子实体 | `resources → resource_permissions`（resource_id） | ACL 是资源的技术从属，随资源**受控 purge** 删除（资源 soft delete 时 ACL 保留） |
| 1:1 扩展 | 域扩展表 `id → resources.id` | 共享主键 1:1，域表生命周期**完全从属** registry 行；随资源受控 purge 销毁。**注意**：触发路径是 `DELETE FROM resources`（purge job 显式执行），不是 tenants/spaces 级联 |
| 层级边 | `resource_relations` parent/child → resources.id | 层级边无独立业务价值；`resource_relations` 为 P2 可选（STEP 1-B 不建） |
| 技术子实体 | `ai_providers → ai_models`、`ai_models → ai_request_logs`（FK 已建，**ON DELETE RESTRICT**） | 模型目录随 provider purge 清理 |

**明确禁止 CASCADE**（RESTRICT / 受控流程）：
- `tenants → spaces`（RESTRICT）
- `spaces → resources` / `tenants → resources`（RESTRICT；P2-03）
- `resources → 域扩展表`（反向不允许：域表删除必须显式，FK 在域表侧）
- `sessions.identity_id → identities`（RESTRICT：撤销 identity 前必须处理会话）
- `memberships.role_id` / `tenant_memberships.role_id` → roles（RESTRICT：被引用角色不可删）

---

## 12. Index Strategy

原则：**只为已知查询模式建索引**；不为"以后可能用"建；季度用 `pg_stat_user_indexes` 清理零扫描索引。

| 表 | 索引 | 类型 | 服务查询 |
|---|---|---|---|
| `users` | `(lower(email)) WHERE deleted_at IS NULL` | 唯一（表达式+部分） | 登录 |
| `users` | `(status)` | btree | 后台任务 |
| `identities` | `(provider, issuer, subject)` | 唯一 | 登录解析 |
| `credentials` | `(identity_id) WHERE type='password' AND revoked_at IS NULL` | 唯一（部分） | 当前密码唯一 |
| `devices` | `(user_id, fingerprint)` | 唯一 | 设备注册 |
| `devices` | `(user_id, status)` | btree | 设备列表 |
| `sessions` | `(token_hash)` | 唯一 | 认证 |
| `sessions` | `(user_id, status)` | btree | 会话列表/批量撤销 |
| `sessions` | `(expires_at) WHERE status='active'` | 部分 | TTL 清理 |
| `spaces` | `(tenant_id, lower(key)) WHERE deleted_at IS NULL` | 唯一（部分） | 空间查找 |
| `spaces` | `(tenant_id, status)` | btree | 空间列表 |
| `memberships` | `(space_id, user_id) WHERE removed_at IS NULL` | 唯一（部分） | 成员唯一 |
| `memberships` | `(tenant_id, user_id)` | btree | "我的空间" |
| `tenant_memberships` | `(tenant_id, user_id)` | 唯一 | 租户成员 |
| `roles` | 三个作用域各一条部分唯一索引 | 部分唯一 | 见 §1.2 |
| `resources` | `(tenant_id, space_id, resource_type, status)` | 复合 | 资源列表（主查询） |
| `resources` | `(tenant_id, owner_id)` | 复合 | "我的资源" |
| `resources` | `(tenant_id, resource_type, created_at DESC)` | 复合 | 时间序列表 |
| `resource_permissions` | `(resource_id, subject_type, subject_id, action)` | 唯一 | ACL 判定 |
| `resource_permissions` | `(subject_type, subject_id)` | btree | "我有哪些授权" |
| `agents` | `(tenant_id, lower(key)) WHERE archived_at IS NULL` | 唯一（部分） | Agent 查找 |
| `agent_versions` | `(agent_id, version)` | 唯一 | 版本定位 |
| `tools` | 平台级 + 租户级两条部分唯一 | 部分唯一 | 见 §1.4 |
| `tool_executions` | `(tool_id, idempotency_key) WHERE idempotency_key IS NOT NULL` | 唯一（部分） | 幂等 |
| `tool_executions` | `(tenant_id, created_at DESC)` | 复合 | 执行历史 |
| `ai_models` | `(provider_id, model_key)` | 唯一 | 模型定位 |
| `ai_routes` | `(tenant_id, space_id, capability, priority)` | 唯一 | 路由匹配 |
| `events` | `(status, next_attempt_at) WHERE status='pending'` | 部分 | outbox 轮询 |
| `events` | `(tenant_id, event_type, occurred_at DESC)` | 复合 | 事件查询 |
| `audit_logs` | `(tenant_id, occurred_at DESC)` | 复合 | 租户审计 |
| `audit_logs` | `(actor_id, occurred_at DESC)` | 复合 | 用户行为 |
| `audit_logs` | `(resource_type, resource_id, occurred_at DESC)` | 复合 | 资源历史 |
| `audit_logs` | `(correlation_id)` | btree | 链路追踪 |
| `audit_logs` | `(risk_level, occurred_at DESC) WHERE risk_level IN ('HIGH','CRITICAL')` | 部分 | 安全告警 |

**不建**：低基数列单列索引（如 `status`、`classification` 单独建）、未确认查询的 jsonb GIN（需要时单独立项）。

---

## 13. Security Review（数据层）

| 主题 | 设计 |
|---|---|
| 凭据存储 | 只存哈希（argon2id），`credentials` 表明文列为**禁止列**（CI 扫描） |
| 会话令牌 | 只存 `token_hash`；session 支持 `absolute_expires_at` 防无限续期 |
| 密钥管理 | `ai_providers.secret_ref` 只存引用；**任何表不得存 API Key 明文**（CI 扫描 + 测试守卫） |
| 最小权限 DB 角色 | `uap_app`（DML）、`uap_migrator`（DDL，仅迁移窗口）、`uap_readonly`；应用运行时不持有 DDL 权限 |
| 审计不可变 | `audit_logs` 仅授予 `INSERT, SELECT`；`BEFORE UPDATE/DELETE` trigger 抛异常 |
| 版本不可变 | `agent_versions` / `tool_versions` 已发布行禁止 UPDATE/DELETE |
| 租户隔离 | 复合索引 + 应用层强制 + RLS（可选，见 Q1）+ 越权审计 |
| 数据分级 | 见 §7；分级只升不降，降级需审计 |
| 脱敏 | 审计 `metadata` 与日志统一走 `redaction`；CRITICAL 执行只存摘要 |
| 分区与留存 | 按月分区，到期整分区 drop（避免大表 DELETE 的锁与膨胀） |
| 加密 | 静态加密由卷/云盘提供；如需列级加密（PII）用应用层信封加密 + KMS，不在 STEP 1-B 范围 |
| 备份 | PITR（WAL 归档）+ 迁移前 snapshot；恢复演练纳入运维手册 |
