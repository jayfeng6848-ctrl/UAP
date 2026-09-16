# UAP Core ER Model

Status: **DESIGN — STEP 1-A（Round 3 修订完成）**
配套文档：[CORE_DOMAIN_MODEL.md](./CORE_DOMAIN_MODEL.md)

> 图中只画主键、外键与关键字段。完整字段见 Entity Catalog。
> 符号：`||--o{` 1:N，`||--||` 1:1，`}o--o{` N:M。

---

## 1. Identity：User / Identity / Device / Session / Credential

```mermaid
erDiagram
    users ||--o{ identities : "has"
    users ||--o{ credentials : "holds"
    users ||--o{ devices : "registers"
    users ||--o{ sessions : "opens"
    identities ||--o{ credentials : "authenticates with"
    identities ||--o{ sessions : "establishes"
    devices  ||--o{ sessions : "bound to"

    users {
        uuid id PK
        citext email UK "lower, partial where deleted_at is null"
        citext username UK "nullable"
        text status "pending|active|suspended|locked|deleted"
        timestamptz last_login_at
        timestamptz deleted_at
    }
    identities {
        uuid id PK
        uuid user_id FK
        text provider "local|oidc|saml|device|service"
        text issuer "nullable"
        text subject
        text status
        timestamptz revoked_at
    }
    credentials {
        uuid id PK
        uuid user_id FK
        uuid identity_id FK
        text type "password|api_key|recovery_code|device_cert|otp"
        text secret_hash "never plaintext"
        text algorithm "argon2id"
        timestamptz expires_at
        timestamptz revoked_at
        timestamptz rotated_at
    }
    devices {
        uuid id PK
        uuid user_id FK
        text fingerprint
        text status "pending|active|untrusted|revoked|lost"
        timestamptz last_seen_at
        timestamptz revoked_at
    }
    sessions {
        uuid id PK
        uuid user_id FK
        uuid identity_id FK
        uuid device_id FK
        text token_hash UK
        text status "active|expired|revoked"
        timestamptz expires_at
        timestamptz absolute_expires_at
        inet ip_created
    }
```

**关键点**
- `users` 1:N `identities` —— 一人多种登录方式，不合并成一张宽表
- `credentials` 挂在 `identity` 上（密码属于某个身份），同时冗余 `user_id` 便于检索
- `devices` 1:N `sessions` —— 多设备、每设备多会话
- 设备撤销级联撤销其 active session（应用层同事务，非 DB trigger）

---

## 2. Tenant / Space / Membership / Role / Permission

```mermaid
erDiagram
    tenants ||--o{ spaces : "contains"
    tenants ||--o{ tenant_memberships : "has"
    tenants ||--o{ roles : "defines (TENANT scope)"
    spaces  ||--o{ memberships : "has"
    spaces  ||--o{ roles : "defines (SPACE scope)"
    users   ||--o{ tenant_memberships : "joins"
    users   ||--o{ memberships : "joins"
    roles   ||--o{ memberships : "assigned in"
    roles   }o--o{ permissions : "granted via"
    role_permissions ||--|| roles : "of"
    role_permissions ||--|| permissions : "refers"

    tenants {
        uuid id PK
        text slug UK
        text status "provisioning|active|suspended|archived|deleted"
        timestamptz archived_at
        timestamptz deleted_at
    }
    spaces {
        uuid id PK
        uuid tenant_id FK
        text key
        text kind "runtime value, not hardcoded"
        text visibility "private|tenant|link"
        text status "active|archived|deleted"
        timestamptz archived_at
        timestamptz deleted_at
    }
    tenant_memberships {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        uuid role_id FK "仅引用 TENANT scope; 默认 tenant_member (P1-01+P2-01)"
        text status "invited|active|suspended|removed"
        timestamptz role_assigned_at
    }
    memberships {
        uuid id PK
        uuid tenant_id FK "denormalised for isolation"
        uuid space_id FK
        uuid user_id FK
        uuid role_id FK "仅引用 SPACE scope; 默认 space_member"
        text status
        timestamptz removed_at
    }
    roles {
        uuid id PK
        uuid tenant_id FK "nullable, TENANT/PLATFORM 区分"
        uuid space_id FK "nullable, SPACE/PLATFORM 区分"
        text scope "PLATFORM|TENANT|SPACE, 互斥"
        text key "平台内置: platform_admin | tenant_admin|tenant_member | space_admin|space_member"
        boolean is_system
    }
    permissions {
        uuid id PK
        text key UK "resource.read"
        text action
        text resource_type
    }
    role_permissions {
        uuid role_id PK
        uuid permission_id PK
        text effect "allow|deny"
        jsonb conditions "ABAC static conditions"
    }
    platform_memberships {
        uuid id PK
        uuid user_id FK "CASCADE -> users; 每 user 至多 1 active"
        uuid role_id FK "RESTRICT -> roles; 仅 PLATFORM scope"
        text status "active|revoked; revoke->re-grant = UPDATE 本行"
        timestamptz revoked_at
    }
    platform_state {
        smallint id PK "=1 单例"
        text bootstrap_state "uninitialized|initialized; 单向状态机"
        timestamptz initialized_at
    }
```

**关键点**
- 用户跨租户：`users` 全局，通过 `tenant_memberships` 归属（1 用户可属 N 租户）
- 用户跨空间：`memberships` 以 `(space_id, user_id)` 唯一（1 用户可属 N 空间）
- `platform_memberships`（**2026-09-08 D-07 Round 3 决策增补，当前未建表**）：PLATFORM role 唯一绑定载体；`role_id` 仅允许 scope='PLATFORM' 的 role；见 `STEP1B_B1_3_DECISION_LOG.md` R3-2
- `memberships.tenant_id` 冗余列 → 隔离索引 + RLS 可用，trigger 保证与 `spaces.tenant_id` 一致
- `roles` 三作用域用部分唯一索引互斥；`role_permissions` 是 N:M 联结并携带 `effect` 与 ABAC 条件

---

## 3. Resource / Resource Permission

```mermaid
erDiagram
    tenants   ||--o{ resources : "owns"
    spaces    ||--o{ resources : "scopes"
    users     ||--o{ resources : "owns (owner_id)"
    resources ||--o{ resource_permissions : "protected by"
    acl_subject_types ||--o{ resource_permissions : "registers subject type (P1/P2-04)"
    resources ||--|| domain_extension : "1:1 shared PK (Domain layer)"

    acl_subject_types {
        uuid id PK
        text key UK "user|role|agent (STEP 1-B 白名单, 不含 group)"
        text description
        timestamptz archived_at
    }
    resources {
        uuid id PK
        uuid tenant_id FK
        uuid space_id FK "nullable"
        uuid owner_id FK "nullable"
        text resource_type "generic, e.g. 'note'"
        text natural_key "nullable, per type unique"
        text classification "PUBLIC|INTERNAL|CONFIDENTIAL|HIGHLY_CONFIDENTIAL"
        text status "active|archived|deleted"
        jsonb metadata
        timestamptz deleted_at
    }
    resource_permissions {
        uuid id PK
        uuid resource_id FK
        uuid subject_type_id FK "→ acl_subject_types.id (NOT裸字符串)"
        uuid subject_id "trigger 验证存在"
        text action
        text effect "allow|deny"
        jsonb conditions
        timestamptz expires_at
    }
    domain_extension {
        uuid id PK "REFERENCES resources(id) ON DELETE CASCADE"
        text domain_payload "business columns live here"
    }
```

**关键点**
- **共享主键 1:1**：域业务表 `id` 同时是 PK 与 FK → 有外键强约束，避免无 RI 的多态弱引用
- Core 只读写 `resources`；Domain 只读写自己的扩展表 → 双向解耦
- `resource_permissions` 是显式 ACL，deny 优先于 RBAC 继承来的 allow
- **P1/P2-04 ACL subject 注册**：通过 `acl_subject_types` 表把"ACL 主体是 user/role/agent"这件事从字符串拼接升级为**注册表 + trigger 验证**：subject 写入前 trigger 检查 `subject_type_id` 必须在注册表中 active 且 `subject_id` 必须在对应表存在；**P2-02：STEP 1-B 白名单不含 `group`，trigger 不引用 `groups` 表**（未来 `group` 需先建表 → 注册 → 扩展 trigger validation，见 STEP1A_ARCHITECTURE_REVIEW Round 3）

---

## 4. Agent / Agent Version / Tool / Tool Version

```mermaid
erDiagram
    tenants ||--o{ agents : "owns"
    spaces  ||--o{ agents : "scopes"
    agents  ||--o{ agent_versions : "versioned as"
    agents  ||--|| agent_versions : "current_version (nullable)"
    agents  ||--o{ agent_permissions : "granted"
    agent_permissions }o--o{ tools : "may invoke"
    agent_permissions }o--o{ permissions : "may hold"

    tools ||--o{ tool_versions : "versioned as"
    tools ||--o{ tool_permissions : "requires"
    tool_permissions ||--|| permissions : "refers"
    tools ||--o{ tool_executions : "runs"
    agents ||--o{ tool_executions : "initiates"

    agents {
        uuid id PK
        uuid tenant_id FK
        uuid space_id FK "nullable"
        uuid owner_id FK
        text key
        text status "draft|active|disabled|archived"
        text max_risk_level "LOW|MEDIUM|HIGH|CRITICAL"
        uuid current_version_id FK "nullable"
        uuid default_route_id FK "nullable"
    }
    agent_versions {
        uuid id PK
        uuid agent_id FK
        int version
        jsonb definition
        jsonb input_schema
        jsonb output_schema
        text checksum
        text status "draft|published|deprecated|revoked"
    }
    agent_permissions {
        uuid id PK
        uuid agent_id FK
        uuid version_id FK "nullable"
        uuid permission_id FK "nullable"
        uuid tool_id FK "nullable"
        text resource_scope
        text effect
    }
    tools {
        uuid id PK
        uuid tenant_id FK "nullable = platform; ON DELETE RESTRICT"
        text key
        text risk_level "LOW|MEDIUM|HIGH|CRITICAL"
        int timeout_ms
        jsonb retry_policy
        text idempotency_mode "none|key_required|natural_key"
        text audit_policy "sampling|full|full_with_payload"
        boolean approval_required
        boolean enabled
    }
    tool_versions {
        uuid id PK
        uuid tool_id FK
        int version
        jsonb input_schema
        jsonb output_schema
        text risk_level
        text handler_ref
        text checksum
    }
    tool_executions {
        uuid id PK
        uuid tenant_id FK
        uuid tool_id FK
        uuid tool_version_id FK
        uuid agent_id FK "nullable"
        text idempotency_key "nullable, unique per tool"
        text status "running|succeeded|failed|denied|timeout"
        text input_digest
        int attempts
    }
```

**关键点**
- Agent 与 Model 完全解耦：Agent 通过 `default_route_id → ai_routes` 间接选模型
- Agent 无 DB 权限：`agent_permissions` 是白名单，未列出即拒绝；`agents` 表不存任何连接信息
- 已发布版本不可变（`agent_versions` / `tool_versions`）
- `tool_executions` 提供幂等锚点：`(tool_id, idempotency_key)` 唯一

---

## 5. AI Provider / Model / Route / Policy

```mermaid
erDiagram
    ai_providers ||--o{ ai_models : "offers"
    ai_models   ||--o{ ai_routes : "primary of"
    tenants     ||--o{ ai_routes : "overrides"
    tenants     ||--o{ ai_policies : "overrides"
    spaces      ||--o{ ai_policies : "overrides"
    ai_models   ||--o{ ai_request_logs : "logged as"
    agents      ||--o{ ai_request_logs : "initiated by"

    ai_providers {
        uuid id PK
        text key UK "logical key, data not code"
        text adapter "adapter registry key"
        text base_url
        text privacy_tier "public|vetted|private|self_hosted"
        text max_classification
        text health_status
        text secret_ref "never plaintext"
        boolean enabled
    }
    ai_models {
        uuid id PK
        uuid provider_id FK
        text model_key
        jsonb capabilities "chat|embeddings|rerank|vision..."
        int context_window
        text max_classification
        boolean is_private
        boolean enabled
    }
    ai_routes {
        uuid id PK
        uuid tenant_id FK "nullable = platform default"
        uuid space_id FK "nullable"
        text capability "chat|embeddings|rerank|vision..."
        int priority
        uuid primary_model_id FK
        jsonb fallback_chain "ordered candidates"
        boolean enabled
    }
    ai_policies {
        uuid id PK
        uuid tenant_id FK "nullable"
        uuid space_id FK "nullable"
        text max_classification
        jsonb allowed_privacy_tiers
        boolean require_private
        boolean allow_fallback
        boolean fallback_preserves_classification "default true"
        numeric budget_daily_usd
        int latency_budget_ms
    }
    ai_request_logs {
        uuid id PK
        uuid provider_id FK
        uuid model_id FK
        text capability
        text classification
        int prompt_tokens
        numeric cost_usd
        int latency_ms
        text status
    }
```

**关键点**
- 厂商是**数据行**，Core 代码不 import 任何 SDK（架构守卫持续强制）
- `ai_policies` 约束 `ai_routes`：fallback 链上每个候选都要重新校验 `max_classification` 与 `privacy_tier`
- 硬约束 `CK (allow_fallback = false OR fallback_preserves_classification = true)` 从数据库层面禁止"降级到公共模型"

---

## 6. Event / Audit

```mermaid
erDiagram
    events ||--o| audit_logs : "may be mirrored by"

    events {
        uuid id PK "partitioned by occurred_at"
        text event_type "namespace.aggregate.action"
        int schema_version
        uuid tenant_id FK "nullable"
        uuid space_id FK "nullable"
        text actor_type
        uuid actor_id
        text subject_type
        uuid subject_id
        jsonb payload
        uuid correlation_id
        uuid causation_id
        timestamptz occurred_at "partition key"
        text status "pending|claimed|delivered|dead (P1-03 at-least-once)"
        text worker_id "claim owner"
        timestamptz claimed_at
        timestamptz lease_expires_at "Reaper 回收过期 claim"
        int attempts
        timestamptz next_attempt_at
        text last_error
        timestamptz delivered_at
    }
    audit_logs {
        uuid id PK "partitioned by occurred_at"
        timestamptz occurred_at "partition key"
        uuid tenant_id FK "nullable"
        uuid space_id FK "nullable"
        text actor_type
        uuid actor_id
        inet actor_ip
        text action
        text resource_type
        uuid resource_id
        text classification
        text result "success|denied|error"
        text risk_level
        text reason
        uuid correlation_id
        uuid request_id
        jsonb metadata "redacted before write"
    }
```

**关键点**
- `events` = **at-least-once** transactional outbox：与业务写入同事务；投递用 **CAS claim**（单行 UPDATE 上的 status 条件=乐观锁）取代纯 SKIP LOCKED；lease 过期由 Reaper 回收 → pending；状态机 `pending → claimed → delivered`，**绝不承诺 exactly-once**，消费方按 `event_id` 幂等
- `audit_logs` 不可变：无 `updated_at` / `deleted_at`，仅 `INSERT, SELECT`
- 两者都是按月分区，到期整分区 drop

---

## 7. 关系矩阵总览

| 关系 | 基数 | FK | 删除策略 |
|---|---|---|---|
| users → identities | 1:N | `identities.user_id` | CASCADE |
| users → credentials | 1:N | `credentials.user_id` | CASCADE |
| users → devices | 1:N | `devices.user_id` | CASCADE |
| users → sessions | 1:N | `sessions.user_id` | CASCADE |
| identities → credentials | 1:N | `credentials.identity_id` | CASCADE |
| identities → sessions | 1:N | `sessions.identity_id` | RESTRICT |
| devices → sessions | 1:N | `sessions.device_id` | CASCADE |
| tenants → spaces | 1:N | `spaces.tenant_id` | **RESTRICT** |
| tenants → tenant_memberships | 1:N | `tenant_memberships.tenant_id` | CASCADE |
| tenants → roles | 1:N | `roles.tenant_id` | CASCADE |
| **roles (TENANT scope) → tenant_memberships** | 1:N | `tenant_memberships.role_id` | **RESTRICT**（P1-01 方案 A：Tenant Role 挂在 membership 上） |
| users → tenant_memberships | 1:N | `tenant_memberships.user_id` | CASCADE |
| spaces → memberships | 1:N | `memberships.space_id` | CASCADE |
| users → memberships | 1:N | `memberships.user_id` | CASCADE |
| roles → memberships | 1:N | `memberships.role_id` | RESTRICT |
| **acl_subject_types → resource_permissions** | 1:N | `resource_permissions.subject_type_id` | **RESTRICT**（P1/P2-04 注册表） |
| roles ↔ permissions | N:M | `role_permissions` | CASCADE / CASCADE |
| tenants → resources | 1:N | `resources.tenant_id` | **RESTRICT**（P2-03：资源不随租户删除级联） |
| spaces → resources | 1:N | `resources.space_id` | **RESTRICT**（P2-03：资源不随空间删除级联） |
| resources → resource_permissions | 1:N | `resource_permissions.resource_id` | CASCADE（技术子实体，随资源受控 purge） |
| resources → domain 扩展表 | 1:1 | 域表 `id` → `resources.id` | CASCADE（1:1 共享 PK，完全从属 registry，随受控 purge） |
| agents → agent_versions | 1:N | `agent_versions.agent_id` | CASCADE |
| agents → agent_permissions | 1:N | `agent_permissions.agent_id` | CASCADE |
| tools → tool_versions | 1:N | `tool_versions.tool_id` | CASCADE |
| tools → tool_permissions | 1:N | `tool_permissions.tool_id` | CASCADE |
| tools → tool_executions | 1:N | `tool_executions.tool_id` | RESTRICT |
| ai_providers → ai_models | 1:N | `ai_models.provider_id` | CASCADE |
| ai_models → ai_routes | 1:N | `ai_routes.primary_model_id` | RESTRICT |
| agents → ai_routes | N:1 | `agents.default_route_id` | SET NULL |

**规则（P2-03 统一）**：**业务数据实体**（`resources`、域扩展表及其承载内容）一律 `RESTRICT`；`ON DELETE CASCADE` **只允许**用于技术/关系子实体 —— sessions / credentials / devices / versions / 权限绑定 / 纯关系行 / ACL / 1:1 域扩展（随 registry 受控 purge）。完整白名单与逐项理由见 `CORE_DOMAIN_MODEL.md` §11.1。Tenant/Space 的资源清理走 archive → soft delete → retention → controlled purge，**不依赖数据库级联**。
