# P12 — IMPLEMENTATION CONTRACT（Indexes）

> ## 状态
>
> ```text
> DESIGN FROZEN
> IMPLEMENTATION AUTHORIZED（2026-09-26）
> IMPLEMENTED · ACCEPTED（0015_p12_indexes）
> ```
>
> **本文件是设计契约，不是实施记录**。本契约**未创建任何索引**、**未创建任何 migration**、
> **未执行任何 DDL/DML**。全部 `CREATE` 条目均为**待授权**的计划项。
> `P12 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED` ·
> `Runtime Implementation Gate = CLOSED`。
>
> **基线**：`HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` · `TAG = UAP-V0.1.8-AUTHORIZATION` ·
> `ALEMBIC HEAD = 0012_authz_enforcement` · `0013+ = ABSENT` · `D-PLAT-09 = P10 → P11 → P12 → P13 → Runtime`。
> 决策依据：`D-P12-01`…`D-P12-15`（FROZEN）· 冻结证据见 `P12_PREP_REPORT.md` / `P12_DECISION_RESOLUTION.md` /
> `P12_ACCEPTANCE_MATRIX.md` / `PLATFORM_DECISION_LOG.md`（`# P12 Canonical Model` + 附录 I）。

---

## 0. 本轮**不得**做的事（硬清单）

```text
CREATE INDEX / CREATE UNIQUE INDEX / ALTER INDEX / DROP INDEX = 0
DDL = 0 · DML = 0
migration creation = 0 · migration modification = 0
alembic upgrade = 0 · alembic downgrade = 0
code changes = 0 · test changes = 0 · config changes = 0
commit = 0 · tag = 0 · push = 0
```

**`0013` 在本轮 MUST NOT 被创建**（§9 仅设计）。

---

## 1. 决策词表与裁定规则

`decision` **只能**取四值：

```text
CREATE          本轮计划新建（待授权）
DEFER           需求成立但当前不建（须写明重开条件）
ALREADY COVERED 已被既有**非部分**索引以前导列覆盖
NOT REQUIRED    在冻结生命周期模型内该反查**不会发生**
```

**裁定规则（本契约一致适用，来自 `D-P12-02` / `D-P12-13`）**

```text
CREATE  ⇔  父行硬删除是「真实存在的运维/业务动作」（含运维退场流程）
           ∧ 该 FK 动作会在子表上做**无谓词**查找（PG FK 检查语义）
           ∧ 该列**无**以其前导的非部分索引
DEFER   ⇔  删除路径**存在但属例外**（软删为主 / 需管理员强制）∧ 当前**无**实测查询证据
NOT REQUIRED ⇔ 父表带软删/生命周期列，冻结模型只做**归档而非 DELETE** ⇒ 反查不发生
ALREADY COVERED ⇔ 既有非部分索引**以前导列**覆盖（PK 前导亦计）

禁止：FK exists  →  automatic index
禁止：以「FK reverse lookup」四字整体批量创建
```

**父表可删除性（实测依据）**

| 父表 | 生命周期列 | 判定 | 依据 |
|---|---|---|---|
| `users` | `deleted_at` | **软删为主**（硬删为设计中的例外路径：`P11 H = tg_acl_user_hard_delete` 专为 `users` AFTER DELETE 而设） | 命令 |
| `spaces` | `archived_at` · `deleted_at` | 归档/软删 | 命令 |
| `tenants` | `archived_at` · `deleted_at` | 归档/软删 | 命令 |
| `agents` | `archived_at` | 归档 | 命令 |
| `identities` | `revoked_at` | 吊销 | 命令 |
| `roles` | `archived_at` | 归档 | 命令 |
| `credentials` | `revoked_at` | 吊销 | 命令 |
| `memberships` | `removed_at` | 移除 | 命令 |
| `tools` | `disabled_at`（**无** `deleted_at`） | 停用 + **可硬删** | 命令 |
| `agent_versions` · `tool_versions` | **无** | **可硬删** | 命令 |
| `ai_providers` · `ai_models` · `ai_routes` | **无** | **可硬删**（运维退场） | 命令 |
| `permissions` | **无** | 平台字典；删除由既有先例认定需 FK 反查索引 | `B1-3_INDEX_STRATEGY:41` |

---

## 2. Part A — 既有索引保护（**57 对象，全部 ALREADY COVERED / 不得改**）

```text
implemented index objects        = 57
  independent created indexes    = 52（op.create_index 25 + 原生 SQL 27）
  implicit UNIQUE indexes        = 5（内联 sa.UniqueConstraint 的 backing index）
```

**本轮禁止把任何既有对象重列为 `CREATE`。** 逐 revision 实测（与 migration docstring 对账 ✅）：

| revision | 对象数 | revision | 对象数 |
|---|---|---|---|
| `0003_b1_1_root_identity` | 15 | `0008_b1_5_tool_registry` | 4（含 1 内联 UQ） |
| `0004_b1_2_tenant_space` | 7 | `0010_b1_6_ai_gateway` | 5（含 2 内联 UQ） |
| `0005_b1_3_authorization` | 10 | `0011_p09_agent_tool_permission` | 8（含 1 内联 UQ） |
| `0007_b1_4_resource_acl` | 8（含 1 内联 UQ） | `0001/0002/0006/0009/0012` | 0 |

**点名保护（指令 §4）**

| 对象 | 状态 | 说明 |
|---|---|---|
| `ix_role_permissions_permission` | **既有（`0005:386`）** | canonical 实现名；设计名 `ix_rp_permission` 仅作历史记录（`CF-3`）；**不 rename** |
| `ix_tenant_memberships_role` | **既有（`0005:438`）** | canonical 实现名；设计名 `ix_tm_role` 仅作历史记录；**不 rename** |
| `uq_tool_exec_idem` | **既有（`0011`）** | **UNIQUE INDEX（部分）**；语义**不变**（`D-P12-06`）；**不再建等价幂等索引** |
| P09 索引（8 对象） | **既有** | `uq_agents_key` · `ix_agents_tenant_status` · `uq_agent_perm` · `ix_ap_agent` · `uq_tool_exec_idem` · `ix_texec_tenant_created` · `ix_texec_status` · `uq_agent_versions`（CONSTRAINT-backed） |
| P10 索引 | **尚不存在** | ⚠ **不得读作"已存在"**：`events` / `audit_logs` 表本身尚未建立（P10 未实施）⇒ 7 条属 **P12 待建**（§4） |

---

## 3. Part B — Canonical Index Decision Table（P12 计划新建）

> `phase owner` 一律 **P12**；`implementation status` 一律 **IMPLEMENTED · ACCEPTED（2026-09-26）**。
> `index_id` 采用 `P12-IDX-01`…`19`（12 条 FK 反查 + 7 条 P10 表）。

### 3.1 FK 反查补索引（**12 条 CREATE**）

| index_id | table | index_name（提议） | columns | unique | partial predicate | query pattern | evidence source | dependency | decision | impl status |
|---|---|---|---|---|---|---|---|---|---|---|
| `P12-IDX-01` | `agent_permissions` | `ix_ap_permission` | `(permission_id)` | no | — | `DELETE FROM permissions` → CASCADE 反查 | `B1-3_INDEX_STRATEGY:41` 同类先例（`ix_role_permissions_permission`）· `D-P12-13` | 无（表已存在） | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-02` | `agent_permissions` | `ix_ap_tool` | `(tool_id)` | no | — | `DELETE FROM tools` → CASCADE 反查 | `D-P12-13` · `tools` 无软删列 | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-03` | `agent_permissions` | `ix_ap_version` | `(version_id)` | no | — | `DELETE FROM agent_versions` → CASCADE 反查 | `D-P12-13` · `agent_versions` 无软删列 | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-04` | `agents` | `ix_agents_current_version` | `(current_version_id)` | no | — | `DELETE FROM agent_versions` → **SET NULL** 反查 | `fk_agents_current_version`（`0011:356-359`）· `D-P12-13` · **`MEASURE-1`** | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-05` | `agents` | `ix_agents_default_route` | `(default_route_id)` | no | — | `DELETE FROM ai_routes` → SET NULL 反查 | `D-P12-13` · `ai_routes` 无软删列 | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-06` | `ai_request_logs` | `ix_airl_provider` | `(provider_id)` | no | — | `DELETE FROM ai_providers` → RESTRICT 反查（**分区表**：无索引则全分区扫） | `D-P12-13` · `ai_providers` 无软删列 | **P08 表**（已存在） | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-07` | `ai_request_logs` | `ix_airl_model` | `(model_id)` | no | — | `DELETE FROM ai_models` → RESTRICT 反查（**分区表**） | `D-P12-13` · `ai_models` 无软删列 | **P08 表** | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-08` | `ai_routes` | `ix_airoutes_primary_model` | `(primary_model_id)` | no | — | `DELETE FROM ai_models` → RESTRICT 反查 | `D-P12-13` | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-09` | `tool_executions` | `ix_texec_tool` | `(tool_id)` | no | — | `DELETE FROM tools` → RESTRICT 反查（**`uq_tool_exec_idem` 为部分索引，不可用** `D-P12-05`） | `D-P12-05` · `D-P12-13` | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-10` | `tool_executions` | `ix_texec_tool_version` | `(tool_version_id)` | no | — | `DELETE FROM tool_versions` → RESTRICT 反查 | `D-P12-13` · `tool_versions` 无软删列 | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-11` | `tool_permissions` | `ix_tperm_permission` | `(permission_id)` | no | — | `DELETE FROM permissions` → CASCADE 反查 | `B1-3_INDEX_STRATEGY:41` 同类先例 · `D-P12-13` | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-12` | `tool_permissions` | `ix_tperm_version` | `(version_id)` | no | — | `DELETE FROM tool_versions` → CASCADE 反查 | `D-P12-13` · `tool_versions` 无软删列 | 无 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |

> **提议名称说明**：`index_name` 为**设计提议**，沿用既有缩写先例（`ix_ap_agent` · `ix_texec_*` · `ix_airl_*`）；
> 其中 **5 个名称已在既有测试 T-22 的 forbidden 集中出现**（`§7 GUARD-1`）——
> `ix_ap_permission` · `ix_ap_tool` · `ix_ap_version` · `ix_agents_current_version` ·
> `ix_agents_default_route`。
> 最终名称在实施轮冻结（PG 标识符 ≤63 字节）。

### 3.2 P10 表索引（**7 条 CREATE** · `D-P12-08`）

| index_id | table | index_name | columns / expression | unique | partial predicate | query evidence | partition behavior | decision | impl status |
|---|---|---|---|---|---|---|---|---|---|
| `P12-IDX-13` | `events` | `ix_events_dispatch` | `(status, next_attempt_at)` | no | `WHERE status IN ('pending','claimed')` | **outbox claim 扫描**（`FOR UPDATE SKIP LOCKED`） | 父表建、自动下推；**子分区零本地索引** | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-14` | `events` | `ix_events_tenant_type_time` | `(tenant_id, event_type, occurred_at DESC)` | no | — | 事件查询（排障 / 回放） | 同上 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-15` | `audit_logs` | `ix_audit_tenant_time` | `(tenant_id, occurred_at DESC)` | no | — | 租户审计页 | 同上 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-16` | `audit_logs` | `ix_audit_actor_time` | `(actor_id, occurred_at DESC)` | no | — | 用户行为轨迹 | 同上 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-17` | `audit_logs` | `ix_audit_resource` | `(resource_type, resource_id, occurred_at DESC)` | no | — | 资源历史 | 同上 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-18` | `audit_logs` | `ix_audit_correlation` | `(correlation_id)` | no | — | 链路追踪 | 同上 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |
| `P12-IDX-19` | `audit_logs` | `ix_audit_risk` | `(risk_level, occurred_at)` | no | `WHERE risk_level IN ('HIGH','CRITICAL')` | 安全告警扫描 | 同上 | **CREATE** | IMPLEMENTED · ACCEPTED（2026-09-26） |

**P10 不动清单（`D-P12-08` / `D-P12-10` / `CF-6`）**

```text
table ownership        = P10（events / audit_logs 的 DDL 归 P10）
partition strategy     = 不变（RANGE (occurred_at)）
primary key            = 不变（(id, occurred_at)）
retention              = 不变（events 30d/dead 90d；audit_logs 365d，不做行级删除）
audit semantics        = 不变（audit_logs 不可变；tg_audit_immutable = P10-owned）
UNIQUE on both tables  = 无 ⇒ 不触发「分区表唯一索引必须含分区键」
```

### 3.3 汇总（Part B）

```text
P12 计划新建索引对象 = 12（FK 反查）+ 7（P10 表）= 19
全部 implementation status = IMPLEMENTED · ACCEPTED（2026-09-26）
全部 decision ∈ {CREATE}
```

---

## 4. Part C — FK 反查逐项裁定（**30 项 = 25 GAP + 5 partial-only**）

> 指令要求逐项编号、禁止整体批量创建。以下为**完整裁定矩阵**。
> `#` 为裁定编号（`P12-FK-01`…`30`）。**post-strategy 与时代项分别标注**（`D-P12-13`）。

### 4.1 GAP 类（25 项：无任何以其前导的索引）

| # | FK source | FK target | ON DELETE | 既有索引候选 | partial-only 候选 | 证据 | 反查需求 | 基数/选择性理由 | 年代 | decision | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `P12-FK-01` | `agent_permissions.permission_id` | `permissions.id` | CASCADE | 无 | 无 | `B1-3:41` 同类先例 | 删 permission 需扫子表 | 子表小、但 CASCADE 语义要求定位 | post-strategy（0011） | **CREATE** | 与既有 `ix_role_permissions_permission` 同构先例 |
| `P12-FK-02` | `agent_permissions.tool_id` | `tools.id` | CASCADE | 无（`uq_agent_perm` 前导 `agent_id`） | 无 | `D-P12-13` | 删 tool 需扫子表 | 高选择性 | post-strategy（0011） | **CREATE** | `tools` 无软删列 ⇒ 硬删可达 |
| `P12-FK-03` | `agent_permissions.version_id` | `agent_versions.id` | CASCADE | 无 | 无 | `D-P12-13` | 删版本需扫子表 | 高选择性 | post-strategy（0011） | **CREATE** | `agent_versions` 无软删列 |
| `P12-FK-04` | `agent_versions.published_by` | `users.id` | SET NULL | 无 | 无 | `D-P12-13` | 删 user 需扫子表 | 低（版本数有限） | post-strategy（0011） | **DEFER** | `users` 软删为主；硬删为例外路径 ⇒ 待硬删流程正式化 |
| `P12-FK-05` | `agents.current_version_id` | `agent_versions.id` | SET NULL | 无 | 无 | `fk_agents_current_version`（`0011:356-359`）· **`MEASURE-1`** | 删版本需清空指针 | 高选择性（每 agent ≤1） | post-strategy（0011） | **CREATE** | 父表无软删列；**既有测试 T-22 已预留该名** |
| `P12-FK-06` | `agents.default_route_id` | `ai_routes.id` | SET NULL | 无 | 无 | `D-P12-13` | 删路由需清空指针 | 中 | post-strategy（0011） | **CREATE** | `ai_routes` 无软删列；运维退场可达 |
| `P12-FK-07` | `agents.owner_id` | `users.id` | RESTRICT | 无 | 无 | `D-P12-13` | 删 user 需 R 检查 | 中 | post-strategy（0011） | **DEFER** | `users` 软删为主 |
| `P12-FK-08` | `agents.space_id` | `spaces.id` | RESTRICT | `ix_agents_tenant_status` 前导 `tenant_id` ✗ | 无 | 命令实测 | 删 space 需 R 检查 | 中 | post-strategy（0011） | **NOT REQUIRED** | `spaces` 带 `archived_at`/`deleted_at` ⇒ 只归档 |
| `P12-FK-09` | `ai_policies.space_id` | `spaces.id` | RESTRICT | 无（`uq_ai_policies` 为表达式） | 无 | 命令实测 | 删 space 需 R 检查 | 低 | post-strategy（0010） | **NOT REQUIRED** | `spaces` 只归档 |
| `P12-FK-10` | `ai_policies.tenant_id` | `tenants.id` | RESTRICT | 无（表达式 UQ 不服务裸列） | 无 | 命令实测 | 删 tenant 需 R 检查 | 低 | post-strategy（0010） | **NOT REQUIRED** | `tenants` 只归档 |
| `P12-FK-11` | `ai_request_logs.model_id` | `ai_models.id` | RESTRICT | 无 | 无 | `D-P12-13` | 删 model 需 R 检查（**分区表**） | 中；无索引 = 全分区扫 | post-strategy（0010） | **CREATE** | `ai_models` 无软删列；分区表代价放大 |
| `P12-FK-12` | `ai_request_logs.provider_id` | `ai_providers.id` | RESTRICT | 无 | 无 | `D-P12-13` | 删 provider 需 R 检查（**分区表**） | 同上 | post-strategy（0010） | **CREATE** | `ai_providers` 无软删列 |
| `P12-FK-13` | `ai_routes.primary_model_id` | `ai_models.id` | RESTRICT | 无 | 无 | `D-P12-13` | 删 model 需 R 检查 | 中 | post-strategy（0010） | **CREATE** | `ai_models` 无软删列 |
| `P12-FK-14` | `ai_routes.space_id` | `spaces.id` | RESTRICT | 无 | 无 | 命令实测 | 删 space 需 R 检查 | 低 | post-strategy（0010） | **NOT REQUIRED** | `spaces` 只归档 |
| `P12-FK-15` | `ai_routes.tenant_id` | `tenants.id` | RESTRICT | 无 | 无 | 命令实测 | 删 tenant 需 R 检查 | 低 | post-strategy（0010） | **NOT REQUIRED** | `tenants` 只归档 |
| `P12-FK-16` | `memberships.user_id` | `users.id` | CASCADE | 无（`uq_memberships` 前导 `space_id`；`ix_memberships_tenant_user` 前导 `tenant_id`） | 无 | 命令实测 | 删 user 需扫子表 | 高（空间×用户） | **strategy-era（0004）** | **DEFER** | `users` 软删为主；硬删路径未正式化 |
| `P12-FK-17` | `resource_permissions.granted_by` | `users.id` | SET NULL | 无 | 无 | 命令实测 | 删 user 需清空列 | 高（ACL 行数大） | **strategy-era（0007）** | **DEFER** | 同上；重开条件见 §4.3 |
| `P12-FK-18` | `resources.owner_id` | `users.id` | SET NULL | `ix_res_tenant_owner` 前导 `tenant_id` ✗ | 无 | 命令实测 · **`CF-1`** | 删 user 需清空列 | 高 | **strategy-era（0007）** | **DEFER** | 同上；`CF-1` 明示不得据此自动创建 |
| `P12-FK-19` | `resources.space_id` | `spaces.id` | RESTRICT | `ix_res_tenant_space_type_status` 前导 `tenant_id` ✗ | 无 | 命令实测 · **`CF-1`** | 删 space 需 R 检查 | 高 | **strategy-era（0007）** | **NOT REQUIRED** | `spaces` 只归档 |
| `P12-FK-20` | `spaces.owner_id` | `users.id` | SET NULL | 无 | 无 | 命令实测 | 删 user 需清空列 | 低 | **strategy-era（0004）** | **DEFER** | `users` 软删为主 |
| `P12-FK-21` | `tool_executions.actor_id` | `users.id` | SET NULL | 无 | 无 | 命令实测 | 删 user 需清空列 | **高**（执行历史可极大） | post-strategy（0011） | **DEFER** | `users` 软删为主；若硬删正式化则升级为 CREATE |
| `P12-FK-22` | `tool_executions.agent_id` | `agents.id` | SET NULL | 无 | 无 | 命令实测 | 删 agent 需清空列 | 高 | post-strategy（0011） | **NOT REQUIRED** | `agents` 带 `archived_at` ⇒ 只归档 |
| `P12-FK-23` | `tool_executions.tool_version_id` | `tool_versions.id` | RESTRICT | 无 | 无 | `D-P12-13` | 删版本需 R 检查 | 高 | post-strategy（0011） | **CREATE** | `tool_versions` 无软删列 |
| `P12-FK-24` | `tool_permissions.permission_id` | `permissions.id` | CASCADE | 无 | 无 | `B1-3:41` 先例 | 删 permission 需扫子表 | 中 | post-strategy（0008） | **CREATE** | 与 `ix_role_permissions_permission` 同构 |
| `P12-FK-25` | `tool_permissions.version_id` | `tool_versions.id` | CASCADE | 无 | 无 | `D-P12-13` | 删版本需扫子表 | 中 | post-strategy（0008） | **CREATE** | `tool_versions` 无软删列 |

### 4.2 partial-only 类（5 项：**部分索引不可服务 FK 检查**，`D-P12-05`）

| # | FK source | FK target | ON DELETE | 既有索引候选 | partial-only 候选 | 证据 | 反查需求 | 基数/选择性理由 | 年代 | decision | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `P12-FK-26` | `credentials.identity_id` | `identities.id` | CASCADE | 无 | `uq_credentials_active_password` | `D-P12-05` | 删 identity 需扫子表 | 低（每 identity 少量凭据） | **strategy-era（0003）** | **NOT REQUIRED** | `identities` 带 `revoked_at` ⇒ 吊销；且子表极小 |
| `P12-FK-27` | `roles.space_id` | `spaces.id` | CASCADE | 无 | `uq_roles_space` | `D-P12-05` | 删 space 需扫子表 | 低（每 space 少量角色） | **strategy-era（0005）** | **NOT REQUIRED** | `spaces` 只归档；子表小 |
| `P12-FK-28` | `roles.tenant_id` | `tenants.id` | CASCADE | 无 | `uq_roles_tenant` | `D-P12-05` | 删 tenant 需扫子表 | 低 | **strategy-era（0005）** | **NOT REQUIRED** | `tenants` 只归档；子表小 |
| `P12-FK-29` | `tool_executions.tool_id` | `tools.id` | RESTRICT | 无 | `uq_tool_exec_idem`（谓词 `idempotency_key IS NOT NULL`） | `D-P12-05` | 删 tool 需 R 检查 | **高**（执行历史） | post-strategy（0011） | **CREATE** | 部分谓词不覆盖全行 ⇒ PG **不可用**；`tools` 无软删列 |
| `P12-FK-30` | `tools.tenant_id` | `tenants.id` | RESTRICT | 无 | `uq_tools_tenant`（谓词 `tenant_id IS NOT NULL`） | `D-P12-05` | 删 tenant 需 R 检查 | 低 | post-strategy（0008） | **NOT REQUIRED** | `tenants` 只归档 |

### 4.3 裁定汇总与 `DEFER` 重开条件

```text
GAP 类（25）      ：CREATE 11 · DEFER 7 · NOT REQUIRED 7 · ALREADY COVERED 0   （11+7+7 = 25 ✅）
partial-only（5） ：CREATE  1 · DEFER 0 · NOT REQUIRED 4 · ALREADY COVERED 0   （ 1+0+4 =  5 ✅）
──────────────────────────────────────────────────────────────
合计 30           ：CREATE 12 · DEFER 7 · NOT REQUIRED 11 · ALREADY COVERED 0  （12+7+11 = 30 ✅）
```

> **与 §3.1 的 12 条 CREATE 的对应**：§4 的 30 项即 FK 反查候选全集的逐项裁定；
> 其 `CREATE` 恰为 **12**，与 §3.1 的 12 条 `P12-IDX-01`…`P12-IDX-12` **一一对应**：
> `4.1` 的 11 项（`P12-FK-01/02/03/05/06/11/12/13/23/24/25`）+ `4.2` 的 1 项（`P12-FK-29`）= **12** ✅
> `DEFER` 7 项 + `NOT REQUIRED` 11 项**无对应 IDX 行**（明确「不建」）。

**`DEFER` 重开条件（7 项，统一）**

```text
重开触发（任一）：
  ① `users` 硬删除路径被正式化为受支持运维流程（当前仅为设计中例外：P11 H 已为其设 trigger）
  ② 出现实测慢查询证据（`pg_stat_statements` / EXPLAIN 显示子表全扫）
  ③ 角色/空间/租户 purge 从「归档」改为「硬删」
重开前一律不建（D-P12-02 · D-P12-15）
```

**年代标注（`D-P12-13` 强制）**

```text
post-strategy（0008/0010/0011）：GAP 20 + partial-only 2 = 22
strategy-era  （0003/0004/0005/0007）：GAP 5 + partial-only 3 = 8
合计 = 30
```

> **不得**把 post-strategy 缺口读作 historical schema defect：`STEP1B_INDEX_STRATEGY` §3 成文早于
> `0008`/`0010`/`0011` 建表，其未 adjudicate 属**清单完整性缺口**（`GAP-INV-P12`），非历史缺陷。

---

## 5. Part D — ALREADY COVERED（**27 项 FK**，本轮**不建**）

```text
FK 总数（校正后，MEASURE-1）= 57
  ALREADY COVERED           = 27
  partial-only              =  5（§4.2，独立分类）
  GAP                       = 25（§4.1）
  27 + 5 + 25 = 57 ✅
```

其中 **2 项为 `MEASURE-1` 新增的已覆盖项**：

| FK source | FK target | ON DELETE | 覆盖索引 | 依据 |
|---|---|---|---|---|
| `tenant_memberships.role_id` | `roles.id` | RESTRICT | `ix_tenant_memberships_role` | `0005:432` ADD CONSTRAINT `fk_tm_role` + `0005:438` 建索引 |
| `memberships.role_id` | `roles.id` | RESTRICT | `ix_memberships_role` | `0005:435` ADD CONSTRAINT `fk_membership_role` + `0005:439` 建索引 |

> 这 2 项**恰好印证**既有 FK 反查政策：`0005` 在加 role FK 的同时建了对应索引。
> 它们此前未被计入是因为解析器只扫 `op.create_table`（见 `MEASURE-1`）。

---

## 6. `MEASURE-1` — PREP 实测口径校正（**`MEASURE-1` = APPROVED** · 2026-09-25 Human Decision）

**发现**：`P12_PREP_REPORT.md` 的 FK 实测数（`54 / 25 / 5 / 24`）**漏计 3 条以原生
`ALTER TABLE … ADD CONSTRAINT … FOREIGN KEY` 创建的 FK**——它们不在 `op.create_table` 体内，
故未被 `sa.ForeignKeyConstraint` 扫描捕获：

```text
0005:432  fk_tm_role                 tenant_memberships.role_id → roles.id          RESTRICT
0005:435  fk_membership_role         memberships.role_id        → roles.id          RESTRICT
0011:356  fk_agents_current_version  agents.current_version_id  → agent_versions.id SET NULL
```

**校正后**

| 量 | PREP（冻结文本引用） | **校正后（本契约实测）** |
|---|---|---|
| FK 总数 | 54 | **57** |
| ALREADY COVERED | 25 | **27** |
| partial-only | 5 | **5**（不变） |
| GAP | 24 | **25** |
| FK 反查候选集 | 29 | **30** |

**影响评估（必须显式声明）**

```text
D-P12-13 的【规则】不受影响：per-gap adjudication 依旧适用（本契约即其执行）。
D-P12-13 引用的【实测数字】"54 FK（25/5/24）" 现已不准确。
```

**处置（`MEASURE-1` = APPROVED · 2026-09-25 Human Decision）**

```text
① 本契约**不**改写 `D-P12-13`、**不**改写 `P12_PREP_REPORT` / `P12_DECISION_RESOLUTION` /
   `P12_ACCEPTANCE_MATRIX` 三份冻结文档、**不**改写 PDL 既有区段；
② 本契约按【校正后】的 30 项完整裁定（覆盖旧 29 项 + 新增 agents.current_version_id）；
③ Human 已**明确接受** **57 / 27 / 5 / 25 / 30** 这组校正数字；校正以 **append-only** 方式
   登记于 `PLATFORM_DECISION_LOG.md` **附录 I.9**（不改任何历史冻结正文）；
④ 门槛条件 ① 已满足 ⇒ 实施门剩余前置见 §13（`NUM-1` 亦已 RESOLVED）。
```

> 另有 3 处 PREP 数字同步校正（同因：解析器覆盖不足/口径窄）：
> · `FORBIDDEN_TABLES` 文件数 **4**（PREP 曾记 8）· · 测试中提及 `events`/`audit_logs` 的文件 **10**（PREP 曾记 8）·
> · 测试引用索引名：**原始 token 61**（`ix_` 28 / `uq_` 33），其中**确属索引清单者为 40**（其余 21 为测试函数名片段）。

---

## 7. `GUARD-1` — 既有测试守卫与 P12 裁定**同步契约**
（**`GUARD-1` = APPROVED** · 2026-09-25 Human Decision）

**发现**：`tests/integration/test_agent_tool_permission_schema.py:478-490` 存在**已生效的负向守卫**：

```python
def test_t22_no_extra_fk_column_indexes(db):
    """T-22 — no additional single FK-column indexes (STEP1B_INDEX_STRATEGY authority)."""
    forbidden = {
        "ix_agents_owner", "ix_agents_space", "ix_agents_current_version",
        "ix_agents_default_route", "ix_texec_agent", "ix_texec_actor",
        "ix_ap_version", "ix_ap_permission", "ix_ap_tool",
        "ix_agent_versions_published_by",
    }
    assert not (names & forbidden)
```

**冲突分析（逐名对本契约裁定）**

| T-22 forbidden 名 | 对应 FK | 本契约裁定 | 实施后 T-22 是否仍成立 |
|---|---|---|---|
| `ix_agents_owner` | `agents.owner_id` | **DEFER** | ✅ 成立（不建） |
| `ix_agents_space` | `agents.space_id` | **NOT REQUIRED** | ✅ 成立（不建） |
| `ix_agents_current_version` | `agents.current_version_id` | **CREATE** | ❌ **失效** |
| `ix_agents_default_route` | `agents.default_route_id` | **CREATE** | ❌ **失效** |
| `ix_texec_agent` | `tool_executions.agent_id` | **NOT REQUIRED** | ✅ 成立（不建） |
| `ix_texec_actor` | `tool_executions.actor_id` | **DEFER** | ✅ 成立（不建） |
| `ix_ap_version` | `agent_permissions.version_id` | **CREATE** | ❌ **失效** |
| `ix_ap_permission` | `agent_permissions.permission_id` | **CREATE** | ❌ **失效** |
| `ix_ap_tool` | `agent_permissions.tool_id` | **CREATE** | ❌ **失效** |
| `ix_agent_versions_published_by` | `agent_versions.published_by` | **DEFER** | ✅ 成立（不建） |

**Human Decision（2026-09-25 · `GUARD-1` = APPROVED）**

```text
T-22 属旧阶段 protection，**不 supersede `D-P12-13`**。
P12 实施时必须从 forbidden 集移除**恰好 5 名**：
      removed  = { ix_ap_permission · ix_ap_tool · ix_ap_version ·
                   ix_agents_current_version · ix_agents_default_route }
      retained = { ix_agents_owner · ix_agents_space · ix_texec_agent ·
                   ix_texec_actor · ix_agent_versions_published_by }
                   —— 均为 DEFER / NOT REQUIRED，**不建**

实施轮 T-22 验收规则（硬）：
      removed_forbidden_names   ⊆ P12 CREATE set
      remaining_forbidden_names ∩ P12 CREATE set = ∅
      P12 CREATE set ↔ T-22 expectations ↔ index-name test assertions  三方一致

性质：TEST vs DECISION 冲突（非实现缺陷）。T-22 的依据是【P09 时点】的 STEP1B_INDEX_STRATEGY 口径，
      而 D-P12-13 已把 FK 反查的裁量权显式移交 P12 ⇒ 二者是**时序先后**，非语义矛盾。
处置：本轮**不修改测试**；改写范围已由 Human 裁定（10 → 5），执行时点在 P12 实施轮（见 §12.2）。
```

---

## 8. `T-1` 硬规则（`D-P12-14` · 写入实施契约）

```text
ix_aimodels_capability = IMPLEMENTED · ACCEPTED（2026-09-26）
```

**明确禁止**（除非未来出现**新的独立** schema/query contract 定义有效可查询键/路径）

```text
GIN(capabilities)          禁 —— 与 INDEX_STRATEGY §2「jsonb GIN 不建」相悖
JSONB path index           禁
JSONB expression index     禁
capability virtual column  禁
```

**理由**：设计谓词引用 `capability`，而 `ai_models` 实际只有 **`capabilities` JSONB**（复数）；
现行 column reference **不是有效的 canonical implementation target** ⇒ `T-1 = stale / mismatched design claim`（已 CLOSED）。

**现状核对（实测）**：`tests/integration/test_ai_gateway_schema.py:696-698` 已有负向断言
`SELECT count(*) FROM pg_indexes WHERE indexname='ix_aimodels_capability'` ⇒ **该禁止已被测试固化**，
P12 **不触碰**。

---

## 9. P11 交互（`D-P12-09`）

| 触发器 | P12 允许提供 | 不得改变 |
|---|---|---|
| `tg_acl_subject_exists` (G) | 仅**性能支持**（复用 `ix_rp_subject`；本轮**不新建**） | timing / semantics / failure semantics |
| `tg_acl_user_hard_delete` (H) | 仅性能支持（H 清理 `resource_permissions` 走 `ix_rp_subject`） | 同上 |
| `tg_acl_role_delete_block` (I) | 仅性能支持（`ix_rp_subject`）；role 删除另由 `ix_tenant_memberships_role` / `ix_memberships_role` 支撑 | 同上 |
| `tg_agent_acl_expire` (J) | 无需（J 逐行 UPDATE，无集合查询） | 同上 |

```text
P11 semantic correctness MUST NOT depend on P12
P12 index MUST NOT change P11 semantics
P10 / P11 ownership 不变（tg_audit_immutable = P10-owned；G/H/I/J = P11-owned）
P12 **不新增** trigger / function / CHECK / FK / seed
```

---

## 10. 命名（`D-P12-12`）

```text
canonical 形式：ix_<semantic_name> · uq_<semantic_name>
既有缩写先例（沿用，不发明第二套）：ix_ap_* · ix_texec_* · ix_airl_* · ix_tm_user · ix_res_* · ix_rp_subject
```

**命名漂移（只登记，**不 rename**）**

```text
ix_rp_permission  → 实际 canonical implemented = ix_role_permissions_permission
ix_tm_role        → 实际 canonical implemented = ix_tenant_memberships_role
```

**本契约只使用实际 canonical implemented names**；新增对象名称见 §3.1/§3.2（设计提议，实施轮冻结）。
PG 标识符上限 **63 字节** —— 全部提议名均远低于上限（最长 `ix_airoutes_primary_model` = 26）。

---

## 11. Part E — 迁移设计（**DESIGN ONLY** · `0013` / `0014` / `0015` 本轮 MUST NOT 创建）

### 11.1 revision 契约

```text
revision allocation（`NUM-1` = RESOLVED · 2026-09-25 Human Decision）：
      P10 = 0013_p10_event_audit
      P11 = 0014_p11_triggers
      P12 = 0015_p12_indexes

filename / revision id : 0015_p12_indexes          （16 字符 ≤ 32 上限 ✅）
down_revision          : 0014_p11_triggers         （经 `0013` / `0014` 衔接 `0012_authz_enforcement`）
single-head expectation: 本 phase 完成时 alembic heads = 0015_p12_indexes（单头）
                         0016+ = 0

规则：每个 phase 占用**唯一** revision；**不得**两 phase 共用同一编号；
      **不得**因前一阶段尚未实施而复用其编号。
关键：P12 生效的 `down_revision` 取决于 P11 是否已实施 —— 见 §13 前置 ④。
```

### 11.2 upgrade 顺序（设计）

```text
[1] FK 反查补索引（非分区表）— 12 条
      ix_ap_permission · ix_ap_tool · ix_ap_version · ix_agents_current_version ·
      ix_agents_default_route · ix_airoutes_primary_model · ix_texec_tool ·
      ix_texec_tool_version · ix_tperm_permission · ix_tperm_version
      + ix_airl_provider · ix_airl_model（分区表，见 [2] 归属）
[2] 分区表索引 — 建在**父表**（PG 自动下推子分区）：ix_airl_provider · ix_airl_model
[3] P10 分区表索引 — 建在**父表**：ix_events_* (2) · ix_audit_* (5)
```

> **前提（硬）**：`events` / `audit_logs` 必须**已存在** ⇒ P12 **必须在 P10 之后**执行
> （`D-PLAT-09` · `D-P12-08` · `DEP-02`）。若 P10 未实施，[3] 组**不可执行**。

### 11.3 downgrade 顺序（设计）

```text
逆序 DROP INDEX IF EXISTS（先分区表索引，后普通表索引）；
不得留下孤儿索引；downgrade 后 `pg_indexes` 相对本 revision 前**零残留**。
```

### 11.4 事务 / 锁 / 并发约束

```text
Alembic 在事务内执行 ⇒ **禁止** CREATE INDEX CONCURRENTLY（非法）—— 与 D-P12-10 一致
分区父表建索引会取得父表 + 各子分区锁（PG 语义）⇒ 实施窗口须报备
**禁止** `ON ONLY` / `ALTER INDEX … ATTACH PARTITION`（与 B1-6 DC-4 / AP3 口径不符）
**禁止** 子分区本地索引
**禁止** 改 partition key / PK / partition strategy / retention / audit semantics
```

### 11.5 不写入的内容（本轮）

```text
不创建 migrations_alembic/versions/0015_p12_indexes.py
  （亦不创建 0013_p10_event_audit.py / 0014_p11_triggers.py —— 均属其他 phase）
不修改 alembic.ini / env.py / 任何既有 migration
不执行 alembic upgrade / downgrade
```

---

## 12. Part F — 测试 / 守卫设计与同步面（**仅设计，不修改测试**）

### 12.1 既有受影响测试（实测计数）

| 面 | 实测 | 说明 |
|---|---|---|
| head 断言 `0012_authz_enforcement` | **15 文件** | 逐阶段同步：P10 → `0013` · P11 → `0014` · **P12 → `0015_p12_indexes`** |
| 引用索引名的测试文件 | **7 文件** | 原始 token **61**；确属清单者 **40** |
| `FORBIDDEN_TABLES` 文件 | **4** | `test_agent_tool_permission_schema` · `test_ai_gateway_schema` · `test_resource_acl_schema` · `test_tool_registry_schema` |
| 提及 `events`/`audit_logs` 的测试 | **10 文件** | P10 落地连带面（P12 间接） |
| 引用 G/H/I/J 的测试 | **3 文件** | P11 实施连带面 |
| **T-22 负向 FK 索引守卫** | **1 处**（10 名） | **`GUARD-1` = APPROVED**：移除**恰好 5 名**，保留**恰好 5 名** |

### 12.2 同步计划（实施轮执行，本轮不动）

```text
① head 断言     ：15 文件 `0012` → `0015`（经 `0013` / `0014` 逐阶段递增；单头）
② T-22 改写     ：forbidden 10 → 5（移除 ix_ap_permission / ix_ap_tool / ix_ap_version /
                  ix_agents_current_version / ix_agents_default_route；保留 5 名 DEFER/NOT REQUIRED）
                  验收：removed ⊆ CREATE set · remaining ∩ CREATE set = ∅（§7）
③ 索引名断言    ：新增/扩展至覆盖 19 条新对象（存在性 + 唯一性/部分谓词形态）
④ FORBIDDEN     ：无新增（P12 不建表、不建 trigger/SQL 侧对象）
⑤ 新增守卫建议  ：`tests/architecture/test_index_inventory.py`
                  - 断言 public schema 索引集合 == 57（既有）+ 19（P12）− 0
                  - 命名规范（ix_/uq_ 前缀 + 无 rename）
                  - 断言不存在 ix_aimodels_capability（T-1 硬规则，可并入既有 ai_gateway 测试）
⑥ 迁移往返      ：upgrade → downgrade → upgrade；`pg_indexes` 零残留
⑦ schema smoke  ：`alembic heads` 单头 `0015_p12_indexes`；`0016+ = 0`
```

### 12.3 本轮**不**修改（硬约束）

```text
tests/**           不改
新增测试文件         不建
tests/architecture/ 不加守卫（仅设计）
```

---

## 13. Part G — 实施门（GATE）

```text
IMPLEMENTATION GATE = CLOSED

前置（全部满足方可实施）：
  ① ✅ SATISFIED — `MEASURE-1` = APPROVED（57/27/5/25/30 口径校正已接受）
  ② ✅ SATISFIED — `GUARD-1` = APPROVED（T-22 改写范围 = 移除恰好 5 名）
  ③ ⏳ P10 IMPLEMENTED（events / audit_logs 存在）—— 7 条 P10 索引的硬前提
  ④ ⏳ P11 IMPLEMENTED（G/H/I/J）—— 按 `D-PLAT-09` 顺序；亦为 `down_revision = 0014_p11_triggers` 的前提
  ⑤ ⏳ P12 IMPLEMENTATION 显式授权

`NUM-1` = RESOLVED（`0013` / `0014` / `0015` 已冻结分配；见 §11.1 与 PDL 附录 I.9）

当前：
  P12 IMPLEMENTATION = NOT AUTHORIZED
  P13 IMPLEMENTATION = NOT AUTHORIZED
  Runtime Implementation Gate = CLOSED
```

---

## 14. 零实施自证（本轮）

```text
CREATE INDEX = 0 · DROP INDEX = 0 · ALTER INDEX = 0
DDL = 0 · DML = 0
migration files added = 0 · migration files changed = 0
code = 0 · tests = 0 · config = 0
commit = 0 · tag = 0 · push = 0
```

见 `P12_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` 与 `p12_contract_gate.log`。



---

## 16. 实施记录（2026-09-26 · IMPLEMENTATION AUTHORIZATION）

```text
revision            = 0015_p12_indexes（sha256 94b0d22800c8971e…）
down_revision       = 0014_p11_triggers
single head         = 0015_p12_indexes（链长 15 · 0016+ = ABSENT）

indexes（新建）      = 19 = 12 FK 反查（§3.1 逐字命名）+ 7 P10 Event/Audit（§3.2）
partial indexes      = 2（ix_events_dispatch · ix_audit_risk，谓词与契约一致）
partitioned parents  = 9（ai_request_logs ×2 · events ×2 · audit_logs ×5，父表级自动下推）
T-1                  = 未创建（ix_aimodels_capability 仍 ABSENT，D-P12-14）
既有索引             = 保全（roundtrip 前后 pre-P12 集合逐项一致）
seed/trigger/table   = 0
```

**验收**：`p12_impl_acceptance.log` **20/20 PASS**（exit 0）·
`p12_impl_full_regression.log` **636 passed / 0 failed / 6 skipped**（exit 0，基线 623 ⇒ 净增 13）。
行为/边界/降级/往返全部 PASS；T-22 同步 = removed 5 ⊆ CREATE · retained 5 ∩ CREATE = ∅ · 三方一致。

**END OF P12 IMPLEMENTATION CONTRACT（2026-09-26 · IMPLEMENTED · ACCEPTED）**（2026-09-25 · DESIGN FROZEN · IMPLEMENTATION NOT YET AUTHORIZED）**
**后续注记：`NUM-1` / `MEASURE-1` / `GUARD-1` 裁定同步（2026-09-25 Human Decision）—— `P12 = 0015_p12_indexes` · `MEASURE-1` = APPROVED（57/27/5/25/30）· `GUARD-1` = APPROVED（T-22 移除恰好 5 / 保留恰好 5）；实施门前置 ① ② 已 SATISFIED，③ ④ ⑤ 未满足 ⇒ IMPLEMENTATION NOT YET AUTHORIZED**
