# B1-5 — Schema Design（PREP）

Status: **PREP / DESIGN — 只设计，不创建任何数据库对象**
阶段：**B1-5 = P07 Tool 域**（推导与待确认项见 `B1-5_SCOPE.md` §1 / D-B15-01）
命名与风格对齐：B1-1~B1-4 既有 migration（`uap_uuid_v7()` 兜底 · `timestamptz(3)` · `set_updated_at()` 复用 · RAISE 型 trigger · 部分唯一索引内联）

---

## 1. 域总览

```
tools                平台/租户两级 Tool 注册表（ROOT）
   ├── tool_versions     契约快照（immutable 语义）
   └── tool_permissions  「调用本 Tool 需要哪些 permissions」
```

| 表 | purpose |
|---|---|
| `tools` | Agent 触达业务的**唯一通道**的注册表（`Agent → Policy → Tool → Service → DB`）。`tenant_id IS NULL` = 平台内置；非 NULL = 租户私有 |
| `tool_versions` | Tool 契约快照（input/output schema、risk、timeout、handler 引用、checksum）。**published 后不可变** |
| `tool_permissions` | 声明"调用该 Tool 所需权限"，绑定到 P04 的 `permissions` 字典行 |

---

## 2. `tools`

### 2.1 列定义

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK |
| `tenant_id` | uuid | **NULL** | — | NULL = 平台内置；非 NULL = 租户私有（**FK 已冻结**：`→ tenants.id ON DELETE RESTRICT`，D-B15-02 = FROZEN — A） |
| `key` | text | NN | — | 工具标识（平台级/租户级分别唯一，**大小写不敏感**） |
| `name` | text | NN | — | 显示名 |
| `description` | text | NULL | — | |
| `risk_level` | text | NN | — | `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` |
| `timeout_ms` | integer | NN | — | 100–600000 |
| `retry_policy` | jsonb | NULL | — | |
| `idempotency_mode` | text | NN | — | `none`/`key_required`/`natural_key` |
| `audit_policy` | text | NN | — | `sampling`/`full`/`full_with_payload` |
| `approval_required` | boolean | NN | — | |
| `enabled` | boolean | NN | — | 生命周期：disable 走 `enabled=false` |
| `disabled_at` | timestamptz(3) | NULL | — | |
| `created_at` | timestamptz(3) | NN | `now()` | |
| `updated_at` | timestamptz(3) | NN | `now()` | trigger 维护 |

来源：`CORE_DOMAIN_MODEL:316-326` · `CONSTRAINT_MATRIX:215-222` · `ER_MODEL:274-286`

### 2.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| FK | `tenant_id NULL → tenants.id ON DELETE RESTRICT`（**D-B15-02 = FROZEN — A**；NULL = 平台级 Tool，语义不变） |
| UQ-1 | **部分唯一**：`uq_tools_platform ON (lower(key)) WHERE tenant_id IS NULL` |
| UQ-2 | **部分唯一**：`uq_tools_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL` |
| CK-1 | `ck_tools_risk_level`：`risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` |
| CK-2 | `ck_tools_timeout`：`timeout_ms BETWEEN 100 AND 600000` |
| CK-3 | `ck_tools_idempotency`：`idempotency_mode IN ('none','key_required','natural_key')` |
| CK-4 | `ck_tools_audit_policy`：`audit_policy IN ('sampling','full','full_with_payload')` |
| NN | 见 §2.1 |
| 生命周期 | **disable**（`enabled=false`），版本不可删（`CORE:958`） |

> **`key` 无格式 CK**（**D-B15-05 = FROZEN — A**）：`tools.key` 保持 **opaque application identifier**，**不新增** regex / format CHECK；不得因 `permissions.key` / `acl_subject_types.key` 有正则而推导。

### 2.3 索引

| 索引 | 类型 | 说明 |
|---|---|---|
| `uq_tools_platform` | partial unique btree | 平台级 key 唯一 |
| `uq_tools_tenant` | partial unique btree | 租户级 key 唯一 |

（来源 `INDEX_STRATEGY:117-121`：「平台 + 租户两条部分 UQ」）

### 2.4 Trigger

| trigger | timing/event | 动作 |
|---|---|---|
| `tg_tools_set_updated_at` | BEFORE UPDATE | `EXECUTE FUNCTION set_updated_at()`（**复用 P00 函数，不重建**） |

---

## 3. `tool_versions`

### 3.1 列定义

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK |
| `tool_id` | uuid | NN | — | → `tools.id` CASCADE |
| `version` | integer | NN | — | 单调递增版本号 |
| `input_schema` | jsonb | NN | — | |
| `output_schema` | jsonb | NN | — | |
| `risk_level` | text | NN | — | 快照值（**本表无 CK**，见下） |
| `timeout_ms` | integer | NN | — | 快照值 |
| `handler_ref` | text | NN | — | 处理器引用（非代码路径；不引入行业语义） |
| `checksum` | text | NN | — | 契约校验和 |
| `status` | text | NN | — | **`status CHECK = 0`**（D-B15-04 = FROZEN — A）；仅冻结 **`published`** 作为 immutable 语义锚点 |
| `published_at` | timestamptz(3) | NULL | — | |
| `created_at` | timestamptz(3) | NN | `now()` | |

来源：`CORE_DOMAIN_MODEL:327-336` · `CONSTRAINT_MATRIX:225-233` · `ER_MODEL:286-295`

> **本表无 `updated_at`** ⇒ 无 `set_updated_at` trigger（与 `resources` 不同）。

### 3.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| FK | `tool_id → tools.id ON DELETE CASCADE`（NN） |
| UQ | `uq_tool_versions ON (tool_id, version)` |
| CK | **无**（冻结文档未给 `risk_level`/`timeout_ms`/`status` 的本表 CK） |
| NN | 见 §3.1 |
| 不变性 | **`status='published'` 的行禁止 UPDATE / DELETE** —— trigger 强制（条目 **K**） |

### 3.3 索引

| 索引 | 类型 |
|---|---|
| `uq_tool_versions` | unique（或 UQ constraint） |

### 3.4 Trigger

| trigger | timing/event | purpose |
|---|---|---|
| `tg_version_immutable` | **BEFORE UPDATE OR DELETE** | `status='published'` 行禁改删；`RAISE EXCEPTION` → 回滚。deprecate/revoke 走应用层状态迁移（后续阶段） |

- 函数：`enforce_tool_versions_immutable()`（命名属 implementation-level → D-B15-03）
- earliest legal phase：**表建时**（`SCHEMA_DEPENDENCY:240`）—— **不依赖 `agents`** ⇒ B1-5 可建 ✅
- 性质：**结构性不变式 only**（不做 authorization evaluation）

---

## 4. `tool_permissions`

### 4.1 列定义

| 列 | 类型 | NULL | 默认 | 说明 |
|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK |
| `tool_id` | uuid | NN | — | → `tools.id` CASCADE |
| `version_id` | uuid | **NULL** | — | NULL = 适用于 Tool 全部版本；否则 → `tool_versions.id` CASCADE |
| `permission_id` | uuid | NN | — | → `permissions.id` CASCADE（P04 已存在） |
| `effect` | text | NN | — | `allow` / `deny` |
| `conditions` | jsonb | NULL | — | **storage-only**（不解释，不构成 ABAC 契约） |
| `created_at` | timestamptz(3) | NN | `now()` | |

来源：`CORE_DOMAIN_MODEL:338-346` · `CONSTRAINT_MATRIX:235-243`

> **本表无 `updated_at`** ⇒ 无 `set_updated_at` trigger。

### 4.2 约束

| 类别 | 内容 |
|---|---|
| PK | `id` |
| FK | `tool_id → tools.id CASCADE`（NN）· `version_id NULL → tool_versions.id CASCADE` · `permission_id → permissions.id CASCADE`（NN） |
| UQ | `uq_tool_perm ON (tool_id, COALESCE(version_id, '<nil-uuid>'), permission_id)` |
| CK | `ck_tool_permissions_effect`：`effect IN ('allow','deny')` |
| NN | id, tool_id, permission_id, effect, created_at |
| NULL | version_id, conditions |

> ⚠️ **技术要点（必须记录）**：`uq_tool_perm` 含表达式 `COALESCE(...)` ⇒ PostgreSQL **不允许**用 `UNIQUE CONSTRAINT` 表达，**必须**实现为 **unique INDEX**。因此本表该唯一性**不计入 constraint 计数**，归入索引计数（与 `uq_resources_natural` 的 partial index 同类）。
>
> ⚠️ `conditions` = **storage-only**（与 B1-4 `resource_permissions.conditions` 同口径）：本阶段不定义其语义、不解释、不作为 ABAC 契约。

### 4.3 索引

| 索引 | 类型 | 说明 |
|---|---|---|
| `uq_tool_perm` | **unique index（表达式）** | 见上 |

（`INDEX_STRATEGY:123-131` 未为 `tool_permissions` 单列额外查询索引）

### 4.4 Trigger

**无。**

---

## 5. 对象计数（预计）

| 类别 | 数量 | 明细 |
|---|---|---|
| 表 | **3** | `tools` · `tool_versions` · `tool_permissions` |
| PK | **3** | 各表 `id` |
| FK | **5** | `tools.tenant_id`（待裁定）· `tool_versions.tool_id` · `tool_permissions.tool_id` · `.version_id` · `.permission_id` |
| UQ（constraint 形式） | **1** | `uq_tool_versions`（**D-B15-06 = FROZEN — A 口径**） |
| UQ（index 形式） | **3** | `uq_tools_platform`（partial）· `uq_tools_tenant`（partial）· `uq_tool_perm`（表达式） |
| CK | **5** | `ck_tools_risk_level` · `ck_tools_timeout` · `ck_tools_idempotency` · `ck_tools_audit_policy` · `ck_tool_permissions_effect` |
| 非 PK 索引 | **5** | 上述 3 个唯一索引 + 2 个（若 `uq_tool_versions` 以索引形式存在则 1 个差额，见下） |
| Trigger | **2** | `tg_tools_set_updated_at` · `tg_version_immutable`（**D-B15-03 FROZEN — A**） |
| Function（新增） | **1** | `enforce_tool_versions_immutable()` |
| Seed | **0** | 见 §6 |

> **索引计数口径说明**：`uq_tool_versions` 若以 `UniqueConstraint` 实现，则 PG 会自动建同名索引，此时"非 PK 索引"= 4 个（`uq_tools_platform` / `uq_tools_tenant` / `uq_tool_perm` / `uq_tool_versions` 的隐式索引）；若以 `CREATE UNIQUE INDEX` 实现则为 4 个也一致。**精确口径待实现时按 `pg_indexes` 实测确认**（B1-4 曾因 `CK ×5/×6` 摘要漂移出现过同类问题，本处**显式标注口径**，见 D-B15-06）。

---

## 6. Seed

```
B1-5 seed = 0
```
`tools` / `tool_versions` / `tool_permissions` 在 B1-5 完成后均为 **0 rows**。依据 `SCHEMA_DEPENDENCY:193`（P00–P10 无 seed）+ `SEED_STRATEGY` §1（清单不含 Tool 域）。

---

## 7. 明确不设计的对象（防范围蔓延）

| 对象 | 归属 | 原因 |
|---|---|---|
| `tool_executions` | **P09** | `agent_id → agents.id` 依赖 agents；`SCHEMA_DEPENDENCY:170` + §5 调整说明② |
| `agents` / `agent_versions` / `agent_permissions` | P09 | |
| `ai_*` | P08 | |
| `events` / `audit_logs` | P10 | |
| 任何 Domain / 行业表 | — | Core 无行业词汇 |
| RLS / POLICY | — | 不启用 |
| permission / action 词表 | P13 / 后续 | 不得自行发明 |

---

## 8. 与既有 schema 的风格一致性

| 项 | 对齐 |
|---|---|
| PK 默认值 | `uap_uuid_v7()`（P00 已建，**不重建**） |
| 时间精度 | `timestamptz(3)` |
| `updated_at` 维护 | trigger + `set_updated_at()`（**不重建函数**） |
| 部分唯一索引 | 建表内联（同 `uq_resources_natural` / `uq_acl_subject_types_key`） |
| trigger 失败语义 | `RAISE EXCEPTION` → 回滚（同 `enforce_acl_subject_types_protect`） |
| 命名 | `enforce_<subject>_<rule>()`（同 `enforce_roles_is_system_protect` 等 9 个既有函数） |

---

## 9. 待裁定项

| 编号 | 内容 |
|---|---|
| **D-B15-02** | `tools.tenant_id` 是否加 FK + 删除规则（冲突 C-1） | ✅ **FROZEN — A**：`→ tenants.id ON DELETE RESTRICT` |
| **D-B15-03** | immutable trigger 命名口径（冲突 C-2） | ✅ **FROZEN — A**：采用 `tg_version_immutable`（本文件已同步） |
| **D-B15-04** | `tool_versions.status` 取值域是否约束 | ✅ **FROZEN — A**：`status CHECK = 0`；仅 `published` 为锚点 |
| **D-B15-05** | `tools.key` 是否补格式 CK | ✅ **FROZEN — A**：不新增 regex |
| **D-B15-06** | 索引/UQ 计数口径 | ✅ **FROZEN — A**：`UNIQUE CONSTRAINT = 1` · `UNIQUE INDEX = 3`（见 §5） |
| **D-B15-08** | `tool_versions.risk_level`/`timeout_ms` 是否补快照 CK | ✅ **FROZEN — A**：不新增（该表保持零 CK） |
