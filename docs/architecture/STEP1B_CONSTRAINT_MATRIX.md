# STEP 1-B / B0 — Constraint Matrix

Status: **DESIGN PREPARATION — 不创建任何表**
来源：STEP 1-A 冻结设计（Round 3 版本）
字段级完整定义以 `CORE_DOMAIN_MODEL.md` §1 Entity Catalog 为准；本文档是 **B1 建表时的约束核对矩阵**。

> 全局 PK 策略：一律 `uuid`（UUIDv7）；分区表 PK = `(id, occurred_at)`。全表含 `created_at`；带 `updated_at` 的表由 trigger 维护。状态字段一律 `text + CHECK`，不用 PG enum（见 CORE_DOMAIN_MODEL §0.3）。

图例：NN = NOT NULL；FK 行为缩写（C=CASCADE / R=RESTRICT / SN=SET NULL）；UQ-部分 = 部分唯一索引。

---

## 1. Identity 域

### `users`

| 类别 | 约束 |
|---|---|
| PK | `id uuid NN`（UUIDv7） |
| UQ | `uq_users_email ON (lower(email)) WHERE deleted_at IS NULL`（部分）；`uq_users_username ON (lower(username)) WHERE deleted_at IS NULL`（部分） |
| CK | `status IN ('pending','active','suspended','locked','deleted')`；`email IS NOT NULL OR username IS NOT NULL` |
| NN | id, status, created_at, updated_at |
| NULL | email, username, display_name, email_verified_at, primary_identity_id, last_login_at, locked_until, deleted_at |
| failed_attempts | `int NN DEFAULT 0`（建议 `CHECK (failed_attempts >= 0 AND failed_attempts <= 20)`） |

### `identities`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `user_id → users.id C`（NN） |
| UQ | `uq_identities_ref ON (provider, COALESCE(issuer,''), subject)`；`uq_identities_email ON (provider, lower(email)) WHERE email IS NOT NULL AND revoked_at IS NULL`（部分） |
| CK | `status IN ('active','unverified','suspended','revoked')`；`provider IN ('local','oidc','saml','device','service')` |
| NN | id, user_id, provider, subject, status, created_at, updated_at |
| NULL | issuer, email, display_name, verified_at, last_used_at, revoked_at |
| 生命周期 | revoked 后不硬删（不可逆撤销） |

### `credentials`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `identity_id → identities.id C`（NN）；`user_id → users.id C`（NN，冗余检索） |
| UQ | `uq_credentials_active_password ON (identity_id) WHERE type='password' AND revoked_at IS NULL`（部分） |
| CK | `type IN ('password','api_key','recovery_code','device_cert','otp')`；`algorithm IN ('argon2id','scrypt','sha256_hmac')`；**`secret_hash <> ''`** |
| NN | id, secret_hash, algorithm, type, created_at, updated_at |
| NULL | secret_hint, expires_at, last_used_at, rotated_at, revoked_at, failed_attempts, locked_until |
| 安全 | **禁止明文列**（CI 扫描 `secret_hash` 之外不得出现明文密钥字段） |

### `devices`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `user_id → users.id C`（NN） |
| UQ | `uq_devices_fingerprint ON (user_id, fingerprint)` |
| CK | `status IN ('pending','active','untrusted','revoked','lost')` |
| NN | id, user_id, fingerprint, status, created_at, updated_at |
| NULL | label, platform, app_version, public_key, first_seen_at, last_seen_at, ip_last, revoked_at, revoked_reason |
| 生命周期 | revoked 不可逆；撤销不删行 |

### `sessions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `user_id → users.id C`（NN）；`identity_id → identities.id R`（NN）；`device_id → devices.id C`（NULL 允许，非设备会话） |
| UQ | `uq_sessions_token ON (token_hash)`；`uq_sessions_refresh ON (refresh_token_hash) WHERE refresh_token_hash IS NOT NULL`（部分） |
| CK | `status IN ('active','expired','revoked')`；**`expires_at > created_at`**；`absolute_expires_at >= expires_at`（建议） |
| NN | id, token_hash, status, expires_at, created_at, updated_at |
| NULL | refresh_token_hash, ip_created, ip_last, user_agent, absolute_expires_at, last_used_at, revoked_at, revoked_reason, replaced_by |
| 生命周期 | 多设备多会话不设唯一；过期/撤销后 retention 硬删 |

---

## 2. Tenant / Space / Role / Permission / Membership 域

### `tenants`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| UQ | `uq_tenants_slug ON (lower(slug))` |
| CK | `status IN ('provisioning','active','suspended','archived','deleted')`；**`slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'`** |
| NN | id, slug, display_name, status, created_at, updated_at |
| NULL | plan, region, settings, archived_at, deleted_at |

### `spaces`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id → tenants.id R`（NN）—— **RESTRICT（P2-03）** |
| UQ | `uq_spaces_key ON (tenant_id, lower(key)) WHERE deleted_at IS NULL`（部分） |
| CK | `status IN ('active','archived','deleted')`；`kind ~ '^[a-z][a-z0-9_.]{1,63}$'`（**kind 是运行时数据，Core 不枚举**）；`visibility IN ('private','tenant','link')` |
| NN | id, tenant_id, key, kind, name, visibility, status, created_at, updated_at |
| NULL | owner_id, settings, archived_at, deleted_at |
| 关系 | `owner_id → users.id`（NULL 允许） |

### `roles`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id NULL → tenants.id C`；`space_id NULL → spaces.id C` |
| UQ | 三 scope 互斥（部分唯一）：`uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL`；`uq_roles_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL`；`uq_roles_space ON (space_id, lower(key)) WHERE space_id IS NOT NULL` |
| CK | `scope IN ('PLATFORM','TENANT','SPACE')` |
| TRIGGER | scope 与 tenant_id/space_id 形状匹配；`is_system=true` 禁改删（详见 TRIGGER_INVENTORY） |
| NN | id, key, name, scope, is_system, status, created_at, updated_at |
| NULL | tenant_id, space_id, archived_at |
| 播种 | 内置：`platform_admin`(PLATFORM) / `tenant_admin`+`tenant_member`(TENANT, 每租户) / `space_admin`+`space_member`(SPACE, 每空间) —— P2-01 |

### `permissions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| UQ | `uq_permissions_key ON (key)` |
| CK | `key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$'` |
| NN | id, key, resource_type, action, is_system, created_at（`resource_type` 原文档标注 NULL 时 action 语义全局；建议 NN 或 NULL 择一，以 Entity Catalog 为准） |
| 备注 | 平台级字典，无租户维度 |

### `role_permissions`

| 类别 | 约束 |
|---|---|
| PK | `(role_id, permission_id, effect)` |
| FK | `role_id → roles.id C`；`permission_id → permissions.id C` |
| CK | `effect IN ('allow','deny')` |
| NN | role_id, permission_id, effect, created_at |
| NULL | conditions（jsonb） |
| 备注 | conditions 为 ABAC 静态条件；deny 行必须始终优先于 allow（求值在应用层） |

### `tenant_memberships`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id → tenants.id C`（NN）；`user_id → users.id C`（NN）；**`role_id → roles.id R`（NN）—— P2-01** |
| UQ | `uq_tenant_memberships ON (tenant_id, user_id)` |
| CK | `status IN ('invited','active','suspended','removed')` |
| TRIGGER | `role_id` 指向的 role 必须 `scope='TENANT' AND tenant_id = 本行 tenant_id`（跨表校验） |
| NN | id, tenant_id, user_id, role_id, status, created_at, updated_at |
| NULL | invited_by, invited_at, joined_at, role_assigned_at, role_assigned_by, removed_at |
| 默认 | role_id 默认 = `tenant_member`（应用层写入） |

### `memberships`（Space 级）

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id → tenants.id C`（冗余 NN）；`space_id → spaces.id C`（NN）；`user_id → users.id C`（NN）；**`role_id → roles.id R`（NN）—— P2-01** |
| UQ | `uq_memberships ON (space_id, user_id) WHERE removed_at IS NULL`（部分） |
| CK | `status IN ('invited','active','suspended','removed')` |
| TRIGGER | `role_id` 指向 role 须 `scope='SPACE' AND space_id = 本行 space_id`；`tenant_id = spaces.tenant_id`（冗余一致性） |
| NN | id, tenant_id, space_id, user_id, role_id, status, created_at, updated_at |
| NULL | invited_by, joined_at, removed_at |
| 默认 | role_id 默认 = `space_member` |

---

## 3. Resource / ACL 域

### `resources`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | **`tenant_id → tenants.id R`（NN）**；**`space_id NULL → spaces.id R`**；`owner_id NULL → users.id SN` —— **P2-03** |
| UQ | `uq_resources_natural ON (tenant_id, resource_type, natural_key) WHERE natural_key IS NOT NULL AND deleted_at IS NULL`（部分） |
| CK | `resource_type ~ '^[a-z][a-z0-9_.]{1,63}$'`；`classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')`；`status IN ('active','archived','deleted')` |
| NN | id, tenant_id, resource_type, classification, status, metadata, created_at, updated_at |
| NULL | space_id（平台级资源或未定空间）、owner_id、natural_key、label、archived_at、deleted_at |
| **TRIGGER** | **`tg_resources_tenant_space_consistency`**（R1 增补 · D-B14-10 = A-1 · **P06 / B1-4**）：BEFORE INSERT OR UPDATE —— `space_id IS NULL` → 放行；`space_id IS NOT NULL` → 要求 `resources.tenant_id = spaces.tenant_id`，否则 RAISE。<br>**边界：structural integrity only —— 不是 authorization evaluator**（授权判定仍在 Authorization Layer）；不引入 RLS；不引用任何未来阶段对象 |
| 生命周期 | archive → soft delete → retention → **controlled purge**（P2-03） |

### `acl_subject_types`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| UQ | `uq_acl_subject_types_key ON (lower(key)) WHERE archived_at IS NULL`（部分） |
| CK | **`key IN ('user','role','agent')` —— P2-02（不含 `group`）**；`key ~ '^[a-z][a-z0-9_]{1,31}$'` |
| TRIGGER | **`tg_acl_subject_types_protect`**（**D-B14-12 = A，2026-09-13**）：**platform-controlled registry 保护** —— 运行时 INSERT 拒绝；`key` UPDATE 拒绝（`description` 等非受控列允许）；DELETE 拒绝（退役走 `archived_at`）。**边界：registry governance only —— 不是 authorization evaluator，不演变为 Domain authorization** |
| NN | id, key, created_at |
| NULL | description, archived_at |
| Seed | user / role / agent（P13） |

### `resource_permissions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `resource_id → resources.id C`（NN，受控 purge 随删）；`subject_type_id → acl_subject_types.id R`（NN）；`granted_by NULL → users.id` **`ON DELETE SET NULL`**（**D-B14-09 = A，2026-09-13**：语义 = **actor attribution**，非 ownership；与 `resources.owner_id` 的 SET NULL **语义正交、相互独立**） |
| UQ | `uq_resource_perm ON (resource_id, subject_type_id, subject_id, action)` |
| CK | `effect IN ('allow','deny')` |
| TRIGGER | `tg_acl_subject_exists`：subject_id 必须存在于 subject_type 对应表（user→users.id / role→roles.id / agent→agents.id）；**不引用 groups**（P2-02） |
| NN | id, resource_id, subject_type_id, subject_id, action, effect, inherited, created_at |
| NULL | conditions, expires_at, granted_by |
| 备注 | user 软删保留 ACL；user 硬删 trigger 清 ACL；role 被引用禁删；agent 归档使 ACL 到期 |

### `resource_relations`（P2 可选，B1 不建）

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `parent_id/child_id → resources.id C` |
| UQ | `(parent_id, child_id, relation_type)` |
| 备注 | B1 不实现（Q3 决策：先扁平 space_id 归属） |

---

## 4. Tool 域

### `tools`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id NULL → tenants.id RESTRICT`（NULL = 平台内置） |
| UQ | 平台级 `uq_tools_platform ON (lower(key)) WHERE tenant_id IS NULL`；租户级 `uq_tools_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL` |
| CK | `risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')`；`timeout_ms BETWEEN 100 AND 600000`；`idempotency_mode IN ('none','key_required','natural_key')`；`audit_policy IN ('sampling','full','full_with_payload')` |
| NN | id, key, name, risk_level, timeout_ms, idempotency_mode, audit_policy, approval_required, enabled, created_at, updated_at |
| NULL | tenant_id（NULL=平台内置）、description, retry_policy, disabled_at |

### `tool_versions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tool_id → tools.id C`（NN） |
| UQ | `uq_tool_versions ON (tool_id, version)` |
| NN | id, tool_id, version, input_schema, output_schema, risk_level, timeout_ms, handler_ref, checksum, status, created_at |
| 不变性 | published 后禁 UPDATE/DELETE（trigger + 权限双保险） |

### `tool_permissions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tool_id → tools.id C`（NN）；`version_id NULL → tool_versions.id C`；`permission_id → permissions.id C`（NN） |
| UQ | `(tool_id, COALESCE(version_id,'0...'), permission_id)` |
| CK | `effect IN ('allow','deny')` |
| NULL | version_id, conditions |

### `tool_executions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tool_id → tools.id R`（NN）；`tool_version_id → tool_versions.id R`（NN）；`agent_id NULL → agents.id`；`actor_id NULL → users.id` |
| UQ | `uq_tool_exec_idem ON (tool_id, idempotency_key) WHERE idempotency_key IS NOT NULL`（部分） |
| CK | `status IN ('running','succeeded','failed','denied','timeout')`；`attempts >= 1`；`duration_ms >= 0` |
| NN | id, tool_id, tool_version_id, status, input_digest, attempts, started_at, correlation_id, created_at |
| NULL | tenant_id?（设计为 NN 若按租户隔离）、agent_id, actor_id, idempotency_key, output_digest, risk_level, finished_at, duration_ms, error_code |
| 保留 | 分区 90 天 hard delete |

---

## 5. Agent 域

### `agents`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id → tenants.id`（NN）；`space_id NULL → spaces.id`；`owner_id → users.id`（NN）；`current_version_id NULL → agent_versions.id SN`（**deferred FK**，见 DEPENDENCY §4.1）；`default_route_id NULL → ai_routes.id SN` |
| UQ | `uq_agents_key ON (tenant_id, lower(key)) WHERE archived_at IS NULL`（部分） |
| CK | `status IN ('draft','active','disabled','archived')`；`max_risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` |
| NN | id, tenant_id, key, name, status, max_risk_level, config, created_at, updated_at |
| NULL | space_id, description, current_version_id, default_route_id, archived_at |
| 安全 | `config jsonb` 禁止 DSN / 凭据（CI 扫描） |

### `agent_versions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `agent_id → agents.id C`（NN）；`published_by NULL → users.id` |
| UQ | `uq_agent_versions ON (agent_id, version)` |
| CK | `status IN ('draft','published','deprecated','revoked')` |
| NN | id, agent_id, version, definition, allowed_tools, checksum, status, created_at |
| NULL | input_schema, output_schema, published_at |
| 不变性 | published 后禁 UPDATE/DELETE |

### `agent_permissions`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `agent_id → agents.id C`（NN）；`version_id NULL → agent_versions.id C`；`permission_id NULL → permissions.id`；`tool_id NULL → tools.id` |
| UQ | `(agent_id, COALESCE(version_id,...), COALESCE(permission_id,...), COALESCE(tool_id,...), COALESCE(resource_scope,''))` |
| CK | **至少一列非 NULL**（permission_id / tool_id / resource_scope）；`effect IN ('allow','deny')` |
| 备注 | 白名单语义：未列出即拒绝 |

---

## 6. AI Gateway 域

### `ai_providers`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| UQ | `uq_ai_providers_key ON (key)` |
| CK | `privacy_tier IN ('public','vetted','private','self_hosted')`；`max_classification IN (...四级)`；`health_status IN ('unknown','healthy','degraded','down')`；`enabled bool NN` |
| NN | id, key, adapter, privacy_tier, max_classification, enabled, health_status, created_at, updated_at |
| NULL | display_name, base_url, capabilities, config, secret_ref, health_checked_at |
| 安全 | `config` 不含密钥；`secret_ref` 只存引用 |

### `ai_models`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `provider_id → ai_providers.id C`（NN） |
| UQ | `uq_ai_models ON (provider_id, model_key)` |
| CK | `max_classification IN (...四级)`；**`context_window > 0`** |
| NN | id, provider_id, model_key, context_window, max_classification, is_private, enabled, created_at, updated_at |
| NULL | display_name, capabilities, max_output_tokens, input/output_price_per_1k, latency_p95_ms |

### `ai_routes`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `primary_model_id → ai_models.id R`（NN）；`tenant_id NULL → tenants.id R`；`space_id NULL → spaces.id R` |
| UQ | `uq_ai_routes ON (COALESCE(tenant_id,'0...'), COALESCE(space_id,'0...'), capability, priority)` |
| CK | `capability IN ('chat','embeddings','rerank','vision','audio_asr','audio_tts','moderation')`；`priority >= 0` |
| NN | id, capability, priority, primary_model_id, enabled, created_at, updated_at |
| NULL | tenant_id（NULL=平台默认）、space_id、fallback_chain |

### `ai_policies`

| 类别 | 约束 |
|---|---|
| PK | `id` |
| FK | `tenant_id NULL → tenants.id R`；`space_id NULL → spaces.id R` |
| UQ | `uq_ai_policies ON (COALESCE(tenant_id,'0...'), COALESCE(space_id,'0...'), lower(name))` |
| CK | **`allow_fallback = false OR fallback_preserves_classification = true`**（HIGHLY_CONFIDENTIAL 降级封死）；`budget_daily_usd >= 0`（建议）；`latency_budget_ms >= 0`（建议） |
| NN | id, name, max_classification, require_private, allow_fallback, fallback_preserves_classification, enabled, created_at, updated_at |
| NULL | tenant_id, space_id, allowed_privacy_tiers, denied_providers, budget_daily_usd, latency_budget_ms, redaction_profile |

### `ai_request_logs`

| 类别 | 约束 |
|---|---|
| PK | `(id, occurred_at)`（分区） |
| FK | `provider_id NULL → ai_providers.id R`；`model_id NULL → ai_models.id R`（`agent_id` / `actor_id` / `tenant_id` / `space_id` 无 FK） |
| NN | id, capability, classification, status, occurred_at |
| NULL | tenant_id, space_id, actor_id, agent_id, provider_id, model_id, tokens, cost_usd, latency_ms, error_code, correlation_id |
| CK | `status IN (...)`（success/error/...按实现定义） |
| 保留 | 分区 90 天 |

---

## 7. Event / Audit 域

### `events`（at-least-once outbox — P1-03）

| 类别 | 约束 |
|---|---|
| PK | `(id, occurred_at)`（分区） |
| UQ | 无（PK 即 event_id） |
| CK | `event_type ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'`；**`status IN ('pending','claimed','delivered','dead')`**；`attempts >= 0 AND attempts <= 100` |
| NN | id, event_type, schema_version, payload, occurred_at, status, attempts, created_at |
| NULL | tenant_id, space_id, actor_type, actor_id, subject_type, subject_id, correlation_id, causation_id, worker_id, claimed_at, lease_expires_at, next_attempt_at, last_error, delivered_at |
| 备注 | worker_id/claimed_at/lease_expires_at 由 CAS claim 写入；无 DB trigger（claim 逻辑在应用层事务） |

### `audit_logs`

| 类别 | 约束 |
|---|---|
| PK | `(id, occurred_at)`（分区） |
| UQ | 无 |
| CK | `result IN ('success','denied','error')`；`risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')`；`classification IN (...四级)`（可空则按策略） |
| NN | id, occurred_at, actor_type, action, result, risk_level, metadata, created_at |
| NULL | tenant_id, space_id, actor_id, actor_ip, actor_user_agent, resource_type, resource_id, classification, reason, correlation_id, request_id |
| 不变性 | 无 updated_at/deleted_at；仅 `INSERT, SELECT` 权限；`tg_audit_immutable` 拦截 UPDATE/DELETE |
| 保留 | 分区 drop 365 天 |

---

## 8. ACL Subject 验证链（P1/P2-04 + P2-02 落地要点）

```
写入 resource_permissions (subject_type_id, subject_id)
  │
  ├─ FK: subject_type_id → acl_subject_types.id (RESTRICT)          [已注册?]
  ├─ CK: 注册表白名单仅 user/role/agent（无 group）                   [P2-02]
  └─ tg_acl_subject_exists (BEFORE INSERT/UPDATE):
        key='user'  → EXISTS(users.id)          → 无则 RAISE
        key='role'  → EXISTS(roles.id)          → 无则 RAISE
        key='agent' → EXISTS(agents.id)         → 无则 RAISE
        其它 key    → 注册表白名单已挡（不可能到达）
```

- **不存在伪造 subject**：任何 (type, id) 组合在 INSERT/UPDATE 时被 trigger 校验；type 不在注册表被 FK 拒绝
- **tenant/space isolation**：ACL 生效范围由 `resources.tenant_id/space_id` 承载；查询资源时先按资源归属过滤，再评估 ACL（应用层 + 可选 RLS）
- **role deletion**：被 ACL 引用的 role → 专用 trigger 拒绝删除（RESTRICT 语义）；归档后 deny 行不参与决策
- **agent archive**：ACL 置临时到期（inherited=true + expires_at=now()）
- **resource deletion / ACL cleanup**：resources soft delete 时 ACL 保留；**controlled purge** 时 `resource_id → resources.id CASCADE` 随删
- **membership removed**：不预先清理 ACL；授权阶段实时校验（重新加入自动恢复）

---

## 9. NOT NULL / NULL 汇总原则

| 判定 | 规则 |
|---|---|
| 一律 NN | 所有 PK、所有状态/枚举列、所有归属列（tenant_id 属租户表时）、`created_at`、所有 `*_hash`、schema 关键 jsonb（payload/metadata/config 默认 `{}`） |
| 允许 NULL | 一切时间语义 `*_at`（除 created_at/occurred_at）、外键中"可归属可不归属"者（space_id/issuer/owner_id）、可选描述/费用/延迟、部分唯一索引的 NULL 分支列 |
| jsonb | 默认 `'{}'`，NN（除 tool input/output schema 有 schema 约束时仍 NN） |

> B1 建表时以上表逐项实现；任何与 CORE_DOMAIN_MODEL 冲突处，**以 CORE_DOMAIN_MODEL.md 为准**（本文档是核对表，不是新设计）。
