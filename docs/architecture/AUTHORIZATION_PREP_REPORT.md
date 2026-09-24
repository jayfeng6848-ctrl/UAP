# UAP STAGE 2 — AUTHORIZATION / ACL / POLICY

## PREP REPORT

| 字段 | 内容 |
|---|---|
| **阶段名称** | `STAGE 2 — AUTHORIZATION / ACL / POLICY PREP` |
| **性质** | `PREP / DESIGN / AUDIT`（**非** Implementation / Runtime / P10） |
| **日期** | 2026-09-23 |
| **基线 HEAD** | `eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6` |
| **基线 TAG** | `UAP-V0.1.7-GOVERNANCE-GATE` |
| **Alembic head** | `0011_p09_agent_tool_permission`（单头 · branches none · 0012+ absent） |
| **实施授权** | **NOT AUTHORIZED**（本报告不产生任何 schema / code 变更） |

> **本报告的边界**：所有结论均为**只读审计发现**或**设计选项**。
> `Recommendation` 只描述工程后果与技术适配性，**不构成人工授权**。最终选择必须由 Human Decision Freeze。

---

## ⚑ DECISION FREEZE 状态（2026-09-23）

> 本报告 §18 的 **22 项 OQ 已全部由 Human 逐项裁定**：
> **19 `FROZEN`（`D-AUTH-01`…`D-AUTH-22`）+ 3 `DEFERRED`（`D-AUTH-03` / `13` / `21`）+ 0 `SUPERSEDED`**。
> ⚠ **该计数为 `OQ` 序列口径**，**不等于**完整 Decision Registry。完整 registry 另含一条**非 OQ** 决策
> **`D-AUTH-23`**（来源 `GAP-11`）：
>
> ```text
> FULL REGISTRY : D-AUTH total = 25  →  FROZEN = 22  +  DEFERRED = 3  +  SUPERSEDED = 0（命名空间内）
> 平台级 supersession = 1：`D-B14-08` → SUPERSEDED by `D-AUTH-05`（登记于 `D-AUTH-24`，2026-09-24）
> OQ  SEQUENCE  : OQ total     = 22  →  FROZEN = 19  +  DEFERRED = 3
> ```
>
> - 决策正文 → [`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md)
> - 决议映射（22 项状态表 + `D-AUTH-23`）→ [`AUTHORIZATION_DECISION_RESOLUTION.md`](./AUTHORIZATION_DECISION_RESOLUTION.md) §0.1
> - 验收判据 → [`AUTHORIZATION_ACCEPTANCE_MATRIX.md`](./AUTHORIZATION_ACCEPTANCE_MATRIX.md) §17（含 §17.4 `GAP-11` 专项）
>
> **`GAP-11`（本报告 §18 未列为 OQ 的 schema 冲突）已由 `D-AUTH-23`（`FROZEN`）处置**：
> `agent_permissions.resource_scope` = **OPAQUE TEXT** — **NOT AUTHORIZATION AUTHORITY**（不构成授权权威）；
> `ND-A = RESOLVED`（**不追加** `<> ''`）· `P09` / `0011` **unchanged** · **无 schema 动作**。
>
> **本报告全文仍为 PREP 阶段的证据记录** —— §18 的 OQ 描述保留**裁定前**的原始分析（含 Human 裁定所依据的
> `Current Evidence` 与选项比较），**不得据以推断任何实施已完成**。
> **`IMPLEMENTATION = NOT AUTHORIZED`**（`D-AUTH-01`…`D-AUTH-23` 的落盘不等于实施授权）。

---

## 1. Executive Summary

UAP 此刻在授权领域处于一个**罕见且有利**的位置：**数据层几乎完整，契约层已存在但未对齐，实现层为零**。

三项决定性事实（均有证据）：

1. **数据层已冻结并通过 11 个 migration 落地**：`roles` / `permissions` / `role_permissions` /
   `platform_memberships` / `tenant_memberships` / `memberships` / `resources` / `acl_subject_types` /
   `resource_permissions` / `agents` / `agent_permissions` / `tools` / `tool_permissions` / `tool_executions`
   共 14 张与授权直接相关的表已存在于 0011。
2. **关键语义已被历史轮次冻结**：`DENY > ALLOW`（`R2-D-14` FROZEN）、permission scope-neutral（`R2-D-15`）、
   `effective_platform_admin` canonical 谓词（`PMB-1`）、fail-closed 平台级请求（`R3-D-07`/`R4`）、
   ACL 主体白名单 `user|role|agent`（`P2-02`）。**本阶段不是从零设计。**
3. **实现层为 0**：`core/permission`、`core/policy`、`core/resource`、`agent/tools`、`agent/runtime` **全部只有
   `Protocol` / `dataclass` 契约**，无任何 evaluator / service / route。经扫描确认无实现代码。

**但存在 6 处真实的语义冲突**，必须在实施前由 Human Decision 裁定（详见 §18）：

| # | 冲突 | 证据 |
|---|---|---|
| C-1 | **主体词汇表三套并存** | `core/identity` 的 `IDENTITY_KINDS=(user, service, device_subject)` · DB `identities.provider=(local, oidc, saml, device, service)` · DB `acl_subject_types=(user, role, agent)` |
| C-2 | **风险等级两套** | `core/policy.RiskPolicy.score → float[0.0,1.0]` vs DB 四档 `LOW/MEDIUM/HIGH/CRITICAL`（`tools.risk_level`、`agents.max_risk_level`、`tool_executions.risk_level`） |
| C-3 | **Membership 契约与表不对齐** | `core/membership.Membership` 仅 space 级、用 `identity_id` + `role_key`；DB 有 `platform_memberships`/`tenant_memberships`/`memberships` 三级、用 `user_id` + `role_id` |
| C-4 | **Delegation 不可表达** | `core/policy.PolicyContext` 只有单个 `actor_id`；DB `tool_executions` 有 `agent_id` **与** `actor_id` 两列 |
| C-5 | **审批两套** | `tools.approval_required`（静态 boolean，已落库）vs `core/policy.RiskPolicy`（动态 float 打分）；`Decision` 无 `REQUIRES_APPROVAL` |
| C-6 | **Action 无统一词汇** | `core/permission.Action(name, resource_type)` 结构体 vs DB `permissions.action`/`resource_permissions.action` 均为**自由 text**，无 CHECK、无共享枚举 |

**结论**：`PREP = PASSED`（审计完整、无 scope 越界、P09 未受影响），
但 `DECISION READINESS = READY` 的前提是 **Human 必须对 §18 的 22 项 OQ（含 6 处冲突）作出裁定**。

---

## 2. Current Baseline

```text
HEAD            = eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6
TAG             = UAP-V0.1.7-GOVERNANCE-GATE  →  eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6
branch          = main
working tree    = CLEAN (porcelain = 0)
index           = CLEAN (diff --cached = 0)
untracked       = 0
Alembic head    = 0011_p09_agent_tool_permission (单一)
branches        = none
0012+           = ABSENT
0010 sha256     = 6d9907237f80e9da4acdff86c8da371af721fec3dccbe00d7e1c3035ab1b0322
0011 sha256     = cdaf8383630335db92cfe54f12e6b65385ea1b4273e86653026afc80893f9f57
```

数据库实测（`uap_b1_test` @ 0011）：**31 张表**。授权相关 14 张：
`roles` · `permissions` · `role_permissions` · `platform_memberships` · `tenant_memberships` · `memberships` ·
`resources` · `acl_subject_types` · `resource_permissions` · `agents` · `agent_versions` · `agent_permissions` ·
`tools` · `tool_versions` · `tool_permissions` · `tool_executions`

**缺席（重要）**：`events` · `audit_logs` · `resource_relations` · `groups` —— 四者**在 0011 均不存在**。
⇒ 审计持久化（`audit_logs`）属 **P10**，**当前不可用**（影响 OQ-A15）。

生产库 `uap` = **0 表**，全程未触碰。

---

## 3. Existing Authorization Evidence（只读实测）

### 3.1 角色与权限（RBAC 层）

| 表 | 关键列 | 冻结约束 / 证据 |
|---|---|---|
| `permissions` | `id` · `key` · **`resource_type`(NULL)** · `action` · `is_system` | `ck_permissions_key` 正则 `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$` |
| `roles` | `tenant_id`(NULL) · `space_id`(NULL) · `key` · `scope` · `is_system` · `status` | `ck_roles_scope IN (PLATFORM,TENANT,SPACE)`；`ck_roles_status IN (active,disabled,archived)`；**3 个部分唯一索引** `uq_roles_platform`(both NULL) · `uq_roles_tenant`(tenant≠NULL ∧ space=NULL) · `uq_roles_space`(space≠NULL) |
| `role_permissions` | `role_id` · `permission_id` · **`effect`** · **`conditions`(jsonb)** | **PK = (role_id, permission_id, effect)** —— 允许同一 (role,permission) **并存 allow + deny**；`ck_role_permissions_effect IN (allow,deny)`；两侧 FK **CASCADE** |

### 3.2 主体绑定（三层，与 role.scope 一一对应）

| 表 | 主体列 | 角色列 | 状态 |
|---|---|---|---|
| `platform_memberships` | `user_id` | `role_id`（仅 PLATFORM scope，由 `tg_pm_role_scope` 强制） | `active` / `revoked` |
| `tenant_memberships` | `user_id` | `role_id` | `invited` / `active` / `suspended` / `removed` |
| `memberships` | `user_id` | `role_id`（space 级） | 同上 |

触发器：`tg_pm_last_admin` · `tg_pm_bootstrap_gate` · `tg_pm_role_scope` · `tg_roles_pm_lifecycle` · `tg_roles_scope_shape` ·
`tg_roles_is_system_protect` —— 平台管理员计数恒 ≥1、scope 形状、系统角色保护均已由 DB 强制。

### 3.3 资源与 ACL（ABAC/实例级层）

| 表 | 关键列 | 约束 |
|---|---|---|
| `resources` | `tenant_id`(NN) · `space_id`(NULL) · `owner_id` · `resource_type` · `natural_key` · **`classification`** · `status` · `metadata`(jsonb) | `ck_resources_classification IN (PUBLIC, INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL)`；`ck_resources_type` 正则；`tg_resources_tenant_space_consistency` |
| `acl_subject_types` | `key` | **白名单硬编码** `ck_acl_subject_types_whitelist CHECK (key IN ('user','role','agent'))`；`tg_acl_subject_types_protect`（runtime INSERT/UPDATE key/DELETE 拒绝，仅 `archived_at` 退役） |
| `resource_permissions` | `resource_id` · `subject_type_id` · `subject_id` · `action` · **`effect`** · **`conditions`** · **`inherited`** · **`expires_at`** · `granted_by` | `ck_resource_permissions_effect IN (allow,deny)`；**`UNIQUE(resource_id, subject_type_id, subject_id, action)`**（注意：**不含 `effect`**）；`subject_type_id` FK **RESTRICT** |

⚠ **`resource_permissions` 与 `role_permissions` / `agent_permissions` / `tool_permissions` 上均无触发器**
—— 与 `R2-D-14` 的「DB 仅存数据，授权解释在 Authorization Layer」一致（设计如此，非缺失）。

### 3.4 Agent 与 Tool

| 表 | 授权相关列 |
|---|---|
| `agents` | `tenant_id`(NN) · `space_id`(NULL) · **`owner_id`(NN → users, RESTRICT)** · **`max_risk_level`** · `current_version_id` · `status(draft/active/disabled/archived)` |
| `agent_versions` | `version`(**integer**) · **`allowed_tools`(jsonb)** · `checksum` · `status(draft/published/deprecated/revoked)` |
| `agent_permissions` | `permission_id`(NULL) · `tool_id`(NULL) · **`resource_scope`(text, 无 FK)** · `effect` · `conditions`；`ck_agent_permissions_scope_target`：**三者至少一个非 NULL** |
| `tools` | **`risk_level`** · **`approval_required`(boolean)** · **`audit_policy`(sampling/full/full_with_payload)** · `idempotency_mode` · `enabled` |
| `tool_permissions` | `tool_id` · `version_id` · `permission_id` · `effect` · `conditions` |
| `tool_executions` | `tenant_id`(NN) · `tool_id` · `tool_version_id` · **`agent_id`(NULL)** · **`actor_id`(NULL)** · `risk_level` · `status(running/succeeded/failed/**denied**/timeout)` · `correlation_id` |

**关键先例**：`tool_executions` 同时具有 `agent_id` 与 `actor_id` —— **委托/代理执行在数据层已可表达**（C-4 的正面先例）。
`status` 已含 **`denied`** —— 授权拒绝已进入执行生命周期。
`tools.approval_required` —— 审批需求**已在数据层存在**（静态、工具级）。

### 3.5 契约层（`core/` 与 `agent/`，全部为 Protocol/dataclass，零实现）

```text
core/permission/interfaces.py
    Action(name, resource_type)
    Decision(allowed, reason, matched_rules)
    DENY = Decision(allowed=False, reason="default-deny")
    Subject(identity_id, role_keys, scopes)      ← 无 agent / 无 tenant / 无 subject_type
    Authorizer.authorize(subject, action, resource) -> Decision

core/policy/interfaces.py
    PolicyContext(action, actor_id, tenant_id, space_id, environment)
    PolicyDecision(allowed, policy_id, reasons)
    PolicyEvaluator.evaluate(context)
    RiskPolicy.score(context) -> float in [0.0, 1.0]     ← 与 DB 四档冲突
    combine(decisions): 「Any denial wins」                ← deny-overrides 已在契约层成文

core/resource/interfaces.py
    ResourceRef(type, id, tenant_id, space_id, owner_identity_id)
    ResourceScope(tenant_id, space_id)
    is_in_scope(ref, scope)                              ← tenant 必须相等；space 有值时须相等

core/identity/interfaces.py   IDENTITY_KINDS = (user, service, device_subject)
core/membership/interfaces.py Membership(id, space_id, identity_id, role_key, status)
core/tenant/interfaces.py     TenantContext(tenant_id) · require_same_tenant(*ids)
core/space/interfaces.py      SpaceContext(tenant_id, space_id, kind)
core/audit/interfaces.py      AuditEvent(action, outcome, actor_id, tenant_id, space_id,
                                         target_type, target_id, metadata) · AUDIT_OUTCOMES=(success,denied,error)

agent/runtime/interfaces.py   「Agent -> Policy -> Tool -> Service -> Database」· AgentInput(..., actor_id)
agent/tools/interfaces.py     「A tool is the only path from an agent to a service」
                              ToolContext(tenant_id, actor_id, space_id, request_id)
agent/memory/interfaces.py    MemoryRecord / MemoryStore —— **零授权参数**
agent/workflow/interfaces.py  WorkflowRunner.run(steps) —— **零授权参数**
agent/registry/interfaces.py  AgentDescriptor.version: str  ← 与 DB integer 冲突
```

### 3.6 历史冻结的授权语义（**必须继承，不得重新发明**）

| 来源 | 冻结内容 |
|---|---|
| `R2-D-14`（STEP1B_ACL_STRATEGY §9） | **DENY > ALLOW**（FROZEN SECURITY INVARIANT）：同 `(role,permission)` 并存 allow+deny ⇒ **DENY**；多角色任一 deny ⇒ **DENY**。由 **Authorization Layer** 解释；**DB 不做授权解释** |
| `R2-D-15` | **Permission scope-neutral**：permission = capability，不承担 tenant/space 边界；实例级边界来自 Membership / Role Scope / Request Context / Resource ACL。B1-3 **不建 ABAC evaluator**；`role_permissions.conditions` **storage-only**（存不解析） |
| `R3-D-07` / `R4 PMB-1..4` | `effective_platform_admin` canonical 谓词 = `pm.active ∧ u.active ∧ r.active ∧ r.scope='PLATFORM' ∧ r.key='platform_admin'`；计数恒 ≥1；平台级请求无 effective 权限 ⇒ **DENY（fail-closed）** |
| `R5` | 用户停用 ⇒ PM 行保持（DB 不自动 revoke）；`deactivate` = 应用层单事务 revoke；`reactivate` **不**恢复 PM；`user inactive ⇒ 永久 DENY`（fail-closed 防线） |
| `P2-02` / `D-B14-12` | ACL 主体白名单 = `user|role|agent`（**无 group**）；注册表 platform-controlled；**registry governance only，不构成 authorization evaluation** |
| `ER_MODEL:221` | 「`resource_permissions` 是显式 ACL，**deny 优先于 RBAC 继承来的 allow**」 |
| `D-B14-09` | `granted_by` = **actor attribution，非 ownership** |
| `D-PLAT-01..06` | 分层与 `services/` 职责（见 §16） |
| `P09`（`D-P09-07`） | P09 = **SCHEMA ONLY**，不修改 `agent/`，不实现 Runtime |

---

## 4. Architecture Findings

```text
层现状（.py 计数）：core 25 · agent 11 · apps 8 · domains 9 · intelligence 13 · infrastructure 17 · services 0（不存在）
```

1. **`services/` 包不存在**（`D-PLAT-01` 定为唯一业务持久化承载层）⇒ 授权服务**尚无落点**，这是一个**已知的、已决策的**前置缺口，不是意外。
2. **`agent ↛ services` 是硬门（G-3）**；`agent` 进入服务层**只能经 Policy / Tool 契约**（`D-PLAT-05`）。
   ⇒ 授权服务若需持久化，必须 `services/`，而 `agent` 只能通过 `core/policy` 契约触达 —— **架构上已给出唯一合法路径**。
3. **`core` 不得承载持久化（G-1）**，不得依赖 `services`（G-2）⇒ 授权契约放 `core`，授权实现放 `services`，二者必须分离。
4. 守卫实测：`tests/architecture` **14 passed**；`agent ↛ {sqlalchemy,psycopg,infrastructure,apps,services}` 命中 **0**；
   `core ↛ {sqlalchemy,psycopg,services}` 命中 **0**；`apps ↛ {sqlalchemy,psycopg}` 命中 **0**。
5. **授权实现为零**：全仓仅存在 `Authorizer` / `PolicyEvaluator` / `RiskPolicy` 三个 `Protocol`，**无任何** `def authorize` 实现。

---

## 5. Identity / Subject Findings

`WHO` 这一层当前存在**三套互不相同的词汇表**（**C-1**，P0 级）：

| 来源 | 取值 | 语义 |
|---|---|---|
| `core/identity` | `user` · `service` · `device_subject` | 契约层 identity kind |
| DB `identities.provider` | `local` · `oidc` · `saml` · `device` · `service` | 认证提供方 |
| DB `acl_subject_types` | `user` · `role` · `agent` | ACL 主体类型（硬白名单） |

**三者的交集与差集**：
- `agent` 是 ACL 主体，**但不是** identity kind，**也不是** identitiy provider ⇒ **Agent 的 identity 载体当前未定义**。
- `role` 是 ACL 主体，但不是 identity —— role 是**聚合主体**（principal aggregation），非身份。
- `service` 在 `identities.provider` 与 `IDENTITY_KINDS` 中都出现 ⇒ **Service Identity 已有先例**（回应 §8.2）。
- `device_subject` 只在契约层，无 DB 对应。
- `Subject(identity_id, role_keys, scopes)` 用 **identity_id** 寻址，而 ACL 用 **user_id/role_id/agent_id** 寻址 ⇒ **寻址键不一致**。

⇒ 记录为 **OQ-A18**（不擅自统一）。**本阶段不新增任何主体类型**（遵守 §8.2「不得直接新增主体」）。

---

## 6. RBAC / ACL / Policy Analysis

### 6.1 职责边界（现状 vs 应有）

| 机制 | 应有语义 | 现状证据 |
|---|---|---|
| **RBAC** | "这个角色**基线**携带哪些权限？" | `roles` + `role_permissions`（含 `effect` + `conditions`）**已存在** |
| **ACL** | "谁可以访问**这个具体资源**？" | `resources` + `resource_permissions`（含 `effect`/`inherited`/`expires_at`）**已存在** |
| **Policy** | "在**什么条件下**该动作被允许？" | `core/policy` 契约存在；**`conditions` 目前 storage-only（`R2-D-15`）** ⇒ **Policy 无实现、无解析** |

⚠ **真实的重叠风险**：`core/permission/__init__.py` 声明 Owns「RBAC / **ABAC** / Authorization / Default Deny」，
而 `core/policy/__init__.py` 声明 Owns「**Policy Evaluation** / Risk Policy / Security Policy」。
`conditions`（ABAC 载体）若由 `core.permission` 解析，将与 `core.policy` 职责重叠 ⇒ **OQ-A01**。

### 6.2 三个选项

**Option A — RBAC only**：删除/停用 ACL 与 Policy 语义。

| 维度 | 评估 |
|---|---|
| 优点 | 最简单；`roles`/`role_permissions` 已完整；决策可完全离线计算 |
| 缺点 | **不可行**：`resources`/`resource_permissions`/`acl_subject_types` **已落库并冻结**（0007）；`tools.approval_required` 亦已落库。删除需破坏既有 migration ⇒ 违反「0010/0011 不得改写」 |
| 安全影响 | 无法表达实例级授权；无法表达"某资源的例外" |
| 结论 | **不推荐**（与既有 schema 冲突） |

**Option B — RBAC + ACL**（无 Policy）

| 维度 | 评估 |
|---|---|
| 优点 | 与既有 schema **完全吻合**；`deny > allow` 可在两层统一实现；实现面小、可完全确定性；`conditions` 保持 storage-only（延续 `R2-D-15`） |
| 缺点 | 无法表达条件式授权（金额阈值、时间窗、环境）；`tools.approval_required` 只能静态；无法做风险自适应 |
| 安全影响 | 强（确定性高、可审计）；但表达力不足可能诱发"用 ACL 行数爆炸模拟条件"的反模式 |
| 性能 | 最优（无规则解析） |
| 复杂度 | 低 |
| Agent 适配 | 中（agent 可作为 ACL 主体，`acl_subject_types` 已允许） |
| Module 适配 | 中（模块只能用资源+主体+动作表达） |
| 迁移成本 | **最低（0 新表）** |
| 运维成本 | 低 |

**Option C — RBAC + ACL + Policy**（完整三层）

| 维度 | 评估 |
|---|---|
| 优点 | 表达力完整；支持 `REQUIRES_APPROVAL`、风险自适应、条件授权；`conditions` 从 storage-only **升级为解析**；与 §42 的目标链路（Policy → Approval if required）一致 |
| 缺点 | 复杂度最高；`conditions` 解析引入策略版本与确定性风险；需解决 **C-2**（风险两套）与 **C-5**（审批两套） |
| 安全影响 | 需强制"策略仅能**收紧**不能被静态授予绕过"；`combine()` 的 any-deny-wins 必须与 `R2-D-14` 合并为单一算法 |
| 性能 | 需缓存（见 §14/OQ-A13） |
| 复杂度 | 高 |
| Agent 适配 | 高（Agent 需在 Policy 中作为 subject 与 delegator 表达） |
| Module 适配 | 高（§28 目标正是"模块只声明自己的 Resource/Action/Policy"） |
| 迁移成本 | 中（`conditions` 语义升级 + 策略载体可能新增表 ⇒ OQ-A17） |
| 运维成本 | 中高 |

**Recommendation（仅工程评估）**：Option C 是唯一能满足 §42 目标链路、
且能同时消化 `resources`/`resource_permissions`（0007）与 `tools.approval_required`（0008）**已落库资产**的选项；
Option B 是它的**严格子集**，可作为分阶段落地（先 B 后 C）的中间形态。
**代价**：必须同步解决 C-2/C-5，否则 Policy 与 DB 事实不一致。

**→ Human Decision Required（OQ-A01）**

---

## 7. Resource Model

### 7.1 现状（已落库，可直接继承）

```text
ResourceRef(type, id, tenant_id, space_id?, owner_identity_id?)
ResourceScope(tenant_id, space_id?)
DB resources: id · tenant_id(NN) · space_id? · owner_id? · resource_type · natural_key?
              · classification(PUBLIC|INTERNAL|CONFIDENTIAL|HIGHLY_CONFIDENTIAL) · status · metadata(jsonb)
```

### 7.2 与需求（§10）的覆盖对照

| §10 要求的属性 | 现状承载 | 判定 |
|---|---|---|
| Resource Type | `resources.resource_type`（正则约束）| ✅ 已有 |
| Resource ID | `resources.id`（UUIDv7） | ✅ 已有 |
| Resource Owner | `resources.owner_id` → users(ON DELETE SET NULL) | ✅ 已有（注意：**只能指向 user，不能指向 agent**） |
| Tenant | `resources.tenant_id`(NN, RESTRICT) | ✅ 已有 |
| Space | `resources.space_id`? (RESTRICT) | ✅ 已有 |
| **Parent Resource** | **无 parent 列** | ❌ **缺失**（`resource_relations` 文档标注为"可选 P2"，0011 实测**不存在**） |
| Sensitivity | `resources.classification` 四档 | ✅ 已有 |
| Lifecycle | `status(active/archived/deleted)` + `archived_at` + `deleted_at` | ✅ 已有 |

**发现**：`resources.owner_id` 只能引用 `users`，但 `acl_subject_types` 允许 `agent` 作为主体 ⇒
**agent 拥有的资源无法用 `owner_id` 表达**（需 ACL 行或 owner 扩展）⇒ 并入 **OQ-A04**。

**推荐方向**：`ResourceRef` 作为 runtime 引用形状已足够；**层级**需求通过 `resource_relations`（可选）或
约定化 `natural_key` 表达 —— **不擅自建表**（OQ-A04 / OQ-A17）。

---

## 8. Action Model

**现状**：
- 契约层 `Action(name, resource_type)` —— 结构体，无枚举。
- DB `permissions.action` = **自由 text**（无 CHECK）；`permissions.resource_type` = **NULL 允许**的 text。
- DB `resource_permissions.action` = **自由 text**（无 CHECK）。
⇒ **三处均无统一词汇表，无强制**（**C-6**）。

**候选词汇**（供裁定，**不冻结**）：`read` `list` `create` `update` `delete` `execute` `publish` `approve` `reject` `export` `share` `admin`

**关键判断点（§11 强调）**：
> 「能读取某资源」≠「能执行该资源上的动作」

现证据支持**独立动作**：`tools`（可执行实体）与 `resources`（被访问对象）在 DB **是分离的两张表**，
且 `tool_permissions` 与 `resource_permissions` **是两张独立的授权表** ⇒ 架构上已隐含
「**execute 作用于 tool，read/write 作用于 resource**」的分离。
但 `agent_permissions` 的 `ck_agent_permissions_scope_target` 允许 `tool_id` 与 `permission_id` 并存 ⇒ 二者可组合。

**→ Human Decision Required（OQ-A05）**

---

## 9. Scope Model

### 9.1 现状：三套 scope 表达并存

| 来源 | 取值 | 说明 |
|---|---|---|
| `roles.scope` | `PLATFORM` / `TENANT` / `SPACE` | **DB 强制**（`ck_roles_scope` + `tg_roles_scope_shape` + 3 个部分唯一索引） |
| `ResourceScope` | `tenant_id` + `space_id?` | 契约层，**无 PLATFORM 概念** |
| Request context | `TenantContext(tenant_id)` · `SpaceContext(tenant_id, space_id, kind)` · `PolicyContext(action, actor_id, tenant_id, space_id?)` | 契约层 |

### 9.2 继承关系（现状可推导）

```text
PLATFORM  (roles.tenant_id IS NULL AND roles.space_id IS NULL)
   ↓
TENANT    (roles.tenant_id NOT NULL AND roles.space_id IS NULL)
   ↓
SPACE     (roles.space_id NOT NULL)
   ↓
RESOURCE  (resources.tenant_id / resources.space_id → resource_permissions)
```
- **PLATFORM → TENANT → SPACE 的继承由 `roles.scope` + membership 三层表已确定**。
- **RESOURCE 级的 `inherited` 列已存在于 `resource_permissions`**，但**无 parent 资源**（见 §7）⇒ 「从父资源继承」当前**不可表达**。
- **`SELF` 作用域在现有模型中不存在**（§12 要求的 `Self` 无承载）。

**→ Human Decision Required（OQ-A06）**：需裁定是否引入 `SELF`，以及 `RESOURCE` 是否作为第 4 个正式 scope。

---

## 10. Agent Subject Model

### 10.1 三种模式对比

| 模式 | 表达 | 现状支持度 |
|---|---|---|
| **M1 — User acts as Agent** | 只有 user 是主体；agent 是 user 的"手套" | 契约层 `Subject` **只认 identity_id** ⇒ 最贴合现状；但 `acl_subject_types` 已允许 `agent` ⇒ 数据层已越过 M1 |
| **M2 — Agent is independent Subject** | agent 自身持有授权边界 | `acl_subject_types` 白名单含 `agent` ✅；`agent_permissions`（`effect`/`resource_scope`/`conditions`）已存在 ✅；`agents.max_risk_level` 已存在 ✅ ⇒ **数据层已完整支持**；契约层 `Subject` **不支持**（无 agent 字段）❌ |
| **M3 — Agent acts on behalf of User** | 双主体：delegator + delegate | **数据层已支持**：`tool_executions.agent_id` **+** `actor_id` 两列并存 ✅；`agent_runtime.AgentInput.actor_id` ✅；契约层 `PolicyContext` 只有单一 `actor_id` ❌ |

### 10.2 对 §13 必答问题的回答

> `User A → invokes Agent X → executes Tool Y → changes Resource Z` —— **谁是真正的授权主体？**

**基于现有证据**：`tool_executions` 的 `agent_id` + `actor_id` 双列设计
**已经把答案写进了 schema**：**两者都是主体，且各自承载不同的授权语义**——
- `agent_id` = **执行主体**（受 `agents.max_risk_level` 与 `agent_permissions` 约束）
- `actor_id` = **委托主体 / 归属主体**（决定"代表谁"、审计归属、以及 user 侧额度/权限）

⇒ 推荐 `EffectiveSubject = f(actor, agent)`（见 §11），但**最终裁定属 Human**。
**本报告不宣布 M1/M2/M3 中任何一个为最终方案** → **OQ-A02 / OQ-A03**。

---

## 11. Impersonation / Delegation

### 11.1 §14 四问的现状回答

| 问题 | 现状 | 判定 |
|---|---|---|
| Agent 权限能否超过 User？ | 无任何强制 | ❌ **未定义**（安全上必须限制） |
| 是否取 User ∩ Agent？ | 无表达 | ❌ 未定义 |
| Agent 是否拥有独立权限？ | `agent_permissions` 表 + `agents.max_risk_level` 已存在 | ✅ 数据层支持 |
| Delegation 如何撤销？ | `agent_versions.status` 有 `revoked`；`acl_subject_types` 走 `archived_at`；但**无权委托表** | ⚠ 部分 |
| Delegation 是否需审计？ | `core/audit` 契约有 `AuditEvent`，但**无 `delegator` 字段**；`audit_logs` 表**不存在**（P10） | ❌ 缺 |

### 11.2 关键安全原则（需在实施时落为守卫）

> **Agent 不得通过代理调用获得超过其授权边界的有效权限。**

**候选实现**：`EffectivePermission = Permission(actor) ∩ Permission(agent) ∩ PolicySpace`
**但**：这与「Agent 可拥有独立权限（`agent_permissions`）」存在张力——若取交集，
`agent_permissions` 中超出 user 的授权将永不可用；若取并集则违反上述原则。
⇒ 这是**必须由 Human 裁定的语义分叉** → **OQ-A03**（本报告不擅自选择）。

---

## 12. Tool Authorization

### 12.1 现状链路

```text
tools.risk_level / approval_required / audit_policy / enabled   ← 工具自身属性（0008 已落库）
        ↓
tool_permissions(tool_id, version_id, permission_id, effect, conditions)   ← 工具↔权限（0008/0011）
        ↓
agent_versions.allowed_tools(jsonb)      ← 版本级白名单
agent_permissions(tool_id | permission_id | resource_scope)  ← agent 级（0011）
        ↓
tool_executions(tool_id, tool_version_id, agent_id, actor_id, risk_level, status)  ← 执行事实（0011）
```

**§17 目标表达**（`Tool → Required Permission → Resource → Action → Scope`）**当前不能完整表达**：
- `tool_permissions` 指向 `permission_id`（能力），但**没有 resource / action / scope 列**。
- `agent_permissions.resource_scope` 是 **自由 text、无 FK、无格式约束** ⇒ 无法结构化查询。
- 结论：**"工具声明所需权限"的形态未定** → **OQ-A09**。

**已确认的良好先例**：`agent/tools/interfaces.py` 明确「A tool is the only path from an agent to a service」
—— **工具是唯一出口**，与 `D-PLAT-05` 一致。**Tool 不得自行实现授权**（§17 要求）在架构上已有支撑。

---

## 13. Risk Model & Human Approval Boundary

### 13.1 风险模型（**C-2 冲突**）

| 来源 | 形态 | 值域 |
|---|---|---|
| DB `tools.risk_level` / `agents.max_risk_level` / `tool_executions.risk_level` | 枚举，4 档 | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `core/policy.RiskPolicy.score()` | 连续标量 | `float ∈ [0.0, 1.0]` |

⇒ **两套不可直接比较的值域**。§18 要求的四档（LOW/MEDIUM/HIGH/CRITICAL）**与 DB 一致**，
故 `core/policy.RiskPolicy` 的 `float` 契约是**唯一需要重新裁定的一方** → **OQ-A10**。

### 13.2 审批边界（**C-5 冲突**）

| 来源 | 形态 |
|---|---|
| DB `tools.approval_required` | **静态 boolean**（工具级，已落库） |
| `core/permission.Decision` | 仅 `allowed: bool` —— **无 `REQUIRES_APPROVAL`** |
| `agent/registry.AgentRunResult.status` | `completed` / `denied` / `failed` —— **无 pending-approval** |
| `tool_executions.status` | `running` / `succeeded` / `failed` / **`denied`** / `timeout` —— **无 awaiting_approval** |

⇒ §22 要求的 `REQUIRES_APPROVAL` 结果在三处契约中**均无处安放** → **OQ-A14 / OQ-A11**。

**§19 候选分级（不冻结）**：

| 动作类别 | 候选默认 |
|---|---|
| `Delete` / `Permission Change` / `Cross-Space Operation` | 人工审批（HIGH+） |
| `Export` / `External Send` | 用户确认或审批 |
| `Financial Operation` / `High-Value Transaction` | 审批 + 阈值策略 |
| 只读 `read`/`list` | 自动（受 RBAC/ACL） |

---

## 14. Failure Semantics（已有多处冻结先例）

| 失败情形 | 现状 | 依据 |
|---|---|---|
| 平台级请求无 effective 权限 | **DENY** | `R3-D-07`/`R4`（FROZEN） |
| user 非 active | **永久 DENY** | `R5`（FROZEN） |
| 授权契约缺省 | `DENY = Decision(allowed=False, reason="default-deny")` | `core/permission` |
| policy 组合 | `combine()`「any denial wins」 | `core/policy` |
| 未知角色/资源/求值异常 | 契约 docstring 明示「all yield a denial」 | `core/permission/interfaces.py` docstring |
| 授权服务 / Policy 不可用 | **未定义** | ❌ 缺口 |
| 授权缓存过期 / 撤销后 | **未定义** | ❌ 缺口 |

⇒ §20 的 `FAIL CLOSED` 统一原则**与既有冻结先例一致**，但**服务级不可用语义尚无定义** → **OQ-A12**。

---

## 15. Cache Semantics

**现状**：`infrastructure/cache/` 存在（17 个 py 中的一部分），但**无任何授权缓存**。
`Role.archived_at` / `platform_memberships.revoked_at` / `expires_at` / `user.status` 均已是"可失效信号"。

**§21 的核心风险**：**stale allow 存活**。现证据显示四个可直接触发失效的事件源**均已落库**：
`revoked_at` · `archived_at` · `expires_at` · `status`。

**本报告不设计缓存**，只登记为 **OQ-A13**（须在实施前确定 TTL/失效/撤销语义）。

---

## 16. Architecture Placement

**§25 的答案由既有冻结决策唯一决定**：

| 组成 | 落点 | 依据 |
|---|---|---|
| Authorization **契约**（Request/Decision/Reason/Policy 接口） | **`core/`** | `D-PLAT-02`：core 保持契约与基础抽象；G-1/G-2 禁止 core 承载持久化/依赖 services |
| Authorization **实现**（RBAC/ACL 求值、持久化读取） | **`services/`** | `D-PLAT-03`：services 是**唯一**允许承载业务持久化的业务层；`D-PLAT-07` 链条 |
| `agent` 触达方式 | **仅经 Policy / Tool 契约** | `D-PLAT-05`（FROZEN）+ G-3 硬门 |
| `domains` 触达方式 | 约定契约（形式待 Runtime PREP 定义） | `D-PLAT-06` / `06.a` |
| `apps` | 入口/装配；不得用 SQLAlchemy 做业务持久化 | `D-PLAT-04` / `04.a` |

**架构倒置风险检查**：本设计**不要求** `core → domains`（禁止）或 `agent → infrastructure`（禁止）。
唯一需要新增的是 **`services/` 包本身**（`D-PLAT-01` 已冻结，尚未创建）—— 属**已知前置条件**，不是新决策。

**→ OQ-A16** 仅需确认"授权实现落在 `services/authorization/`"这一具体粒度（`D-PLAT-03` 待办项）。

---

## 17. Migration Impact（**Proposed only — 未实施**）

| 项 | 现状 | 若采用 Option C 的**潜在**影响（**未裁定、未实施**） |
|---|---|---|
| 已有表 | 14 张授权相关表 @0011 | 可能需新增列（如 `resources.parent_id`、`policy` 载体、`approval` 载体） |
| 新表 | — | 候选：`policy_rules` / `resource_relations` / `approval_requests`（**§26 禁止创建 0012**） |
| 新列 | — | 候选：`tool_executions.awaiting_approval` 相关列、`resource_permissions.effect` 入 UQ |
| 索引 | — | 候选：ACL 决策路径的反查索引（属 P12 范畴） |
| 约束 | — | 候选：`permissions.action` 的 CHECK 词汇表（会与既有自由 text 冲突 ⇒ 需评估） |
| 触发器 | — | **不建议**新增授权解释触发器（违反 `R2-D-14`「DB 不做授权解释」） |
| migration 数量 | 0 | **本阶段 0**。任何新增一律属未来阶段，且**必须** Human 授权 |

**硬边界**：`0010` / `0011` **不得修改**（hash 已登记）；**不得创建 0012**；P09 schema/trigger/约束/测试一律不得触碰。

---

## 18. Open Questions（OQ-A01 … OQ-A22）

> 每项含：证据 · 选项 · 影响（安全/复杂度/性能/迁移/Agent/模块）· 工程建议 · **Human Decision Required**。

### OQ-A01 — RBAC / ACL / Policy 组合模式
- **Question**：最终采用 A（RBAC only）/ B（RBAC+ACL）/ C（RBAC+ACL+Policy）？
- **Evidence**：`roles`+`role_permissions`+`resources`+`resource_permissions` 已落库（0005/0007）；
  `role_permissions.conditions` **storage-only**（`R2-D-15`）；`core/permission` 与 `core/policy` 职责重叠。
- **Option A / B / C**：见 §6.2（A 不可行：与既有 schema 冲突；B 为子集；C 完整）。
- **Security**：C 需强制"策略只能收紧"；B 确定性最高。
- **Complexity**：A 低 / B 低 / C 高。**Performance**：A≈B 优 / C 需缓存。
- **Migration**：A 需破坏性变更（禁止）/ B **0 新表** / C 可能新增策略载体。
- **Agent**：C 才满足 §42 链路。**Module**：C 才满足 §28。
- **Recommendation（工程）**：**C，并允许以 B 作为分阶段中间形态**。
- **Human Decision Required**：✅

### OQ-A02 — Agent 是否为独立 Subject
- **Evidence**：`acl_subject_types` 白名单含 `agent`（硬 CHECK）；`agent_permissions` 表存在；`agents.max_risk_level` 存在；但 `core/permission.Subject` **无 agent 字段**。
- **Option A** M1 仅 user 主体 / **B** M2 agent 独立 / **C** M3 双主体。
- **Security**：M1 最保守但浪费已落库资产；M2 需防止 agent 权限溢出；M3 需交集/边界规则。
- **Complexity**：M1 低 / M2 中 / M3 高。
- **Migration**：M1 需**移除** `acl_subject_types` 的 `agent`（破坏性，禁止）⇒ 实际不可行。
- **Recommendation（工程）**：**M3（双主体）**，因它是唯一同时解释 `tool_executions.agent_id + actor_id`、
  `acl_subject_types.agent`、`agent_permissions` 的模型；M2 作为 M3 的退化情形。
- **Human Decision Required**：✅

### OQ-A03 — Agent 与 User 的 Delegation / Acting 关系
- **Question**：`Effective = actor ∩ agent`？还是 agent 独立（可超越 actor）？撤销与审计如何？
- **Evidence**：`tool_executions` 双列；`AgentInput.actor_id`；**无委托表、无 delegator 审计字段**。
- **Option A** 交集（最安全，但 `agent_permissions` 超出部分永不可用）/ **B** agent 独立（违反 §14 原则）/ **C** 交集 + 显式"提升授权"（需审批与审计）。
- **Security**：A/C 强；B **直接违反** §14「不得获得超过其授权边界的有效权限」。
- **Recommendation（工程）**：**A 为默认，C 为显式审批的例外通道**；撤销以 `actor.status` / `membership` / `agent_versions.status='revoked'` 实时校验实现。
- **Human Decision Required**：✅

### OQ-A04 — Authorization Resource canonical model
- **Question**：`ResourceRef` 是否即最终 canonical？是否引入 `parent`/层级？
- **Evidence**：`resources` 8 项属性中 7 项已具备；**parent 缺失**；`resource_relations` 0011 不存在；
  `resources.owner_id` 只能指向 user（**agent 无法成为 owner**）。
- **Option A** 保持现状（无层级）/ **B** 引入 `resources.parent_id`（自引用 FK）/ **C** 引入 `resource_relations` 通用关系表。
- **Migration**：B/C 均需新列或新表 ⇒ 未来 migration。
- **Recommendation（工程）**：**A 先行**（当前无已证实层级需求）；B/C 留待出现真实用例再定，避免过早建表（§3 禁止）。
- **Human Decision Required**：✅

### OQ-A05 — Action vocabulary
- **Question**：是否冻结统一 action 词表？`execute` / `approve` / `publish` / `export` 是否独立？
- **Evidence**：`permissions.action`、`resource_permissions.action` **均为自由 text、无 CHECK**；`Action(name, resource_type)` 结构体无枚举。
- **Option A** 不冻结（保持自由 text）/ **B** 冻结枚举 + DB CHECK / **C** 冻结枚举但仅契约层强制。
- **Migration**：B 需为已落库表加 CHECK（**若表中已有越界值将失败**；当前 seed=0 ⇒ 风险低）。
- **Recommendation（工程）**：**B**（DB+契约双层），并明确 `execute` **独立于** `read`（§11 强调），
  `approve` **独立**（因 §19 要求审批边界）。`export` 建议独立（外泄风险）。
- **Human Decision Required**：✅

### OQ-A06 — Scope hierarchy
- **Question**：是否引入 `SELF`？`RESOURCE` 是否为第 4 个正式 scope？
- **Evidence**：`roles.scope` 仅 3 值（DB 强制）；`ResourceScope` 无 PLATFORM；`resource_permissions.inherited` 存在但无 parent。
- **Option A** 3 层不变 / **B** 4 层（+RESOURCE）/ **C** 5 层（+RESOURCE+SELF）。
- **Migration**：B/C 需修改 `ck_roles_scope`（**属已发布表约束变更，需新 migration，且不得改 0005**）。
- **Recommendation（工程）**：**A**（`SELF` 可用 `resources.owner_id` + ACL 表达，无需新 scope），
  但这与 §12 的明确要求（列出 `Self`）存在张力 ⇒ **必须由 Human 裁定**。
- **Human Decision Required**：✅

### OQ-A07 — Allow / Deny precedence
- **Question**：最终算法？
- **Evidence（已有冻结先例）**：**`R2-D-14` = DENY > ALLOW（FROZEN SECURITY INVARIANT）**；
  `ER_MODEL:221`「ACL deny 优先于 RBAC 继承的 allow」；`core/policy.combine()`「any denial wins」。
  ⚠ **但** `resource_permissions` 的 `UNIQUE` **不含 `effect`** ⇒ ACL 层无法并存 allow+deny（**C / OQ-A20**）。
- **Option A** Deny overrides（延续 `R2-D-14`）/ **B** Specific overrides general / **C** 混合（先比对 specificity，再 deny 优先）。
- **Security**：A 最保守且**已有冻结依据**。
- **Recommendation（工程）**：**A（沿用 R2-D-14）**，并明确**确定性 / 顺序无关 / 可审计**三项性质需在契约层强制。
- **Human Decision Required**：✅（确认沿用即可，但**不得由本报告自行冻结**）

### OQ-A08 — Permission inheritance
- **Question**：`Tenant→Space→Resource` 与 `Role→Permission` 的继承/覆盖/例外/撤销规则？
- **Evidence**：`roles` 三层 + 部分唯一索引已定；`resource_permissions.inherited` 存在但**无 parent（§7）**；
  `resource_permissions.expires_at` 支持时间过期。
- **Option A** 仅角色层继承（资源层不继承）/ **B** 双层继承（需 parent 支持）。
- **Recommendation（工程）**：**A**（与 OQ-A04 Option A 一致，避免依赖不存在的 parent）。
- **Human Decision Required**：✅

### OQ-A09 — Tool permission 与 resource permission 的关系
- **Question**：工具"声明所需权限"的形态？风险策略在其中何处？
- **Evidence**：`tool_permissions` 仅指向 `permission_id`（**无 resource/action/scope 列**）；
  `agent_permissions.resource_scope` 为**无约束自由 text**；`agent/tools` 契约明示工具是唯一出口。
- **Option A** 工具只声明 permission（现状）/ **B** 工具声明 (permission, resource_type, action, scope) 元组 / **C** 工具引用外部策略对象。
- **Migration**：B/C 需新列或新表。
- **Recommendation（工程）**：**B**（结构化四元组）——它是唯一能让 §17 目标表达（Tool→Permission→Resource→Action→Scope）
  可**静态验证**的形态；A 无法验证，C 过重。
- **Human Decision Required**：✅

### OQ-A10 — Risk classification（**C-2 冲突**）
- **Question**：风险值是四档枚举还是连续评分？
- **Evidence**：DB **三张表**已用四档 `LOW/MEDIUM/HIGH/CRITICAL`（CHECK 强制）；
  `core/policy.RiskPolicy.score() -> float[0,1]`。
- **Option A** 四档（对齐 DB）/ **B** float（对齐契约）/ **C** 双轨（float 打分 → 映射四档）。
- **Migration**：B 需改三张表的 CHECK（**破坏性**）；A 仅需改契约（1 处）。
- **Recommendation（工程）**：**A 或 C**。A 最简且与 DB/§18 一致；C 保留打分能力但必须定义**确定性映射**与阈值。
  B 与实际数据模型冲突，不推荐。
- **Human Decision Required**：✅

### OQ-A11 — Human Approval boundary（**C-5 冲突**）
- **Question**：审批需求如何表达？静态工具属性还是动态策略？
- **Evidence**：`tools.approval_required`（静态 bool，已落库）；`Decision` 无 `REQUIRES_APPROVAL`；
  `tool_executions.status` 无 `awaiting_approval`。
- **Option A** 保持工具级静态 / **B** 策略驱动（按风险/金额/资源分类）/ **C** 静态为下限 + 策略可**追加**。
- **Security**：A 简单但无法覆盖 §19 的高价值/跨空间场景；**C 最贴合 §19**（策略只能加严不能放宽）。
- **Migration**：B/C 需新增审批载体（表/列）。
- **Recommendation（工程）**：**C**。
- **Human Decision Required**：✅

### OQ-A12 — Authorization failure semantics
- **Question**：服务/策略不可用时是否统一 FAIL CLOSED？
- **Evidence**：已有冻结先例——`R3-D-07`/`R4`（平台级无权限 ⇒ DENY）、`R5`（user inactive ⇒ 永久 DENY）、
  `DENY`/`default_decision()`、`combine()` any-deny-wins、`core/permission` docstring。
- **Option A** 统一 FAIL CLOSED / **B** 分级降级（只读放行） / **C** 可配置。
- **Security**：A 唯一符合 §20 原则；B **直接违反**「不能因为检查不到权限而默认允许」。
- **Recommendation（工程）**：**A**，并需覆盖 §20 列出的 8 类失败分支。
- **Human Decision Required**：✅

### OQ-A13 — Authorization cache semantics
- **Question**：是否缓存？TTL？失效？撤销后？
- **Evidence**：**当前无任何授权缓存**；四个失效信号已落库（`revoked_at`/`archived_at`/`expires_at`/`status`）。
- **Option A** 不缓存 / **B** 短 TTL 缓存 + 显式失效 / **C** 事件驱动失效（依赖 `events`，**0011 不存在**）。
- **Security**：A 最安全但性能差；C 依赖 P10 未落地组件 ⇒ **当前不可行**。
- **Recommendation（工程）**：**A 首发**（零 stale allow 风险），待 P10 `events` 落地后再评估 B/C。
- **Human Decision Required**：✅

### OQ-A14 — Authorization decision API contract
- **Question**：Request/Context/Decision/Reason 形状？结果集是否含 `REQUIRES_APPROVAL`？
- **Evidence**：现有 `Subject`/`Action`/`ResourceRef`/`Decision(allowed, reason, matched_rules)`；
  §22 要求 `ALLOW|DENY|REQUIRES_APPROVAL` + `policy_version`；**三处契约无处安放 `REQUIRES_APPROVAL`**。
- **Option A** 保持 `allowed: bool` / **B** 三值枚举 / **C** 三值 + 独立 approval 对象。
- **Recommendation（工程）**：**B**（`Decision.effect ∈ {ALLOW, DENY, REQUIRES_APPROVAL}`），
  并补充 `policy_version`、`subject`、`delegator`、`scope`、`context` 字段以对齐 §22/§23。
- **Human Decision Required**：✅

### OQ-A15 — Audit requirements（依赖 P10）
- **Question**：授权决策审计需记录哪些字段？`Authorization Decision` 与 `Tool Execution` 如何区分？
- **Evidence**：`core/audit.AuditEvent` 有 `action/outcome/actor_id/tenant_id/space_id/target_type/target_id/metadata`；
  **缺** `subject` / `delegator` / `decision` / `reason` / `policy` / `risk` / `approval`；
  `AUDIT_OUTCOMES=(success,denied,error)`；
  **`audit_logs` 与 `events` 表在 0011 均不存在（属 P10）** ⇒ **审计**当前**无处落库**。
- **Option A** 复用 `AuditEvent` 并仅存 metadata / **B** 扩展契约 + 待 P10 落表 / **C** 独立授权审计表。
- **Dependency**：**强依赖 P10（`events` → `audit_logs`）**。
- **Recommendation（工程）**：**B**，并登记「授权审计的持久化被 P10 阻塞」为**显式依赖**（§27 依赖图）。
- **Human Decision Required**：✅

### OQ-A16 — Authorization Service placement
- **Question**：契约/实现/粒度的最终落点？
- **Evidence**：`D-PLAT-02`（core=契约）· `D-PLAT-03`（services=唯一持久化）· `D-PLAT-05`（agent 经 Policy/Tool 契约）·
  G-1/G-2/G-3 硬门；`services/` **尚不存在**。
- **Option A** 契约 `core/authorization` + 实现 `services/authorization` / **B** 复用既有 `core/permission`+`core/policy` 双契约。
- **Recommendation（工程）**：**B**（复用既有 `core/permission` + `core/policy`，扩展其契约），
  实现落 `services/authorization/`；**不新建第三个契约模块**，避免概念分裂。
- **Human Decision Required**：✅

### OQ-A17 — Future schema impact
- **Question**：最终 schema 影响清单（表/列/索引/约束/触发器/迁移数）？
- **Evidence**：见 §17（**Proposed only**）。
- **Recommendation（工程）**：任何 schema 变更**不得**触碰 `0010`/`0011`，**不得**创建 `0012` 于本阶段；
  宜将 schema 变更**推迟到实施阶段的独立 migration 批次**并单独授权。
- **Human Decision Required**：✅

### OQ-A18 — 【新增】Subject / Identity 词汇表统一（**C-1**）
- **Question**：`IDENTITY_KINDS` / `identities.provider` / `acl_subject_types` 三套词汇如何收敛？Agent 的 identity 载体是什么？
- **Evidence**：见 §5（三套词汇表 + 交集差集分析）。
- **Option A** 保持三套（分层语义）/ **B** 收敛为单一声明式 subject 词汇 / **C** 引入 `subject_registry` 统一注册（含 agent/service/role）。
- **Migration**：B/C 需变更 `acl_subject_types` 白名单（**该表受 `tg_acl_subject_types_protect` 保护，且 CHECK 硬编码**）⇒ 属破坏性变更，须新 migration。
- **Security**：A 保持既有防线不变（无迁移风险）；B/C 需重新证明 subject 验证链（`enforce_acl_subject_exists`）。
- **Recommendation（工程）**：**A 先行**（零迁移、零防线变更），把"Agent 的 identity 载体"单列为实施阶段的**首要待解项**。
- **Human Decision Required**：✅

### OQ-A19 — 【新增】Agent 版本标识类型不一致
- **Question**：`AgentDescriptor.version: str` 与 `agent_versions.version: integer` 如何对齐？
- **Evidence**：`agent/registry/interfaces.py`（`version: str = "0.1.0"`）vs DB `agent_versions.version integer NOT NULL`。
- **Option A** 契约改为 int / **B** 契约保留语义化版本并在 DB 增列 / **C** 契约版本 = DB version 的字符串形式。
- **Migration**：B 需新列。
- **Recommendation（工程）**：**A**（改契约 1 行，零迁移）；语义化版本若确有需求，另立 OQ。
- **Human Decision Required**：✅

### OQ-A20 — 【新增】ACL 唯一键不含 `effect`（与 DENY>ALLOW 的交互）
- **Question**：`UNIQUE(resource_id, subject_type_id, subject_id, action)` **不含 `effect`**
  ⇒ 同一 (资源, 主体, 动作) **不可能**并存 allow 与 deny。这是否与 `R2-D-14`「DENY > ALLOW」相容？
- **Evidence**：0011 实测唯一约束定义；`R2-D-14` 明确该不变式针对 `(role, permission)` 并存情形（`role_permissions` PK **含** effect）。
- **Option A** 保持（ACL 层以"行替换"表达改判；deny-by-absence + 撤销行）/ **B** 将 `effect` 纳入 UQ（允许并存，由决策层解释）/ **C** 引入 tombstone deny。
- **Security**：A 语义更简单，但**"显式拒绝"在 ACL 层不可表达**（只能靠"不授予"）；
  若需 ACL 层显式 deny 覆盖 RBAC allow（`ER_MODEL:221` 所述），则 **A 不足**。
- **Migration**：B/C 需重建唯一约束（新 migration）。
- **Recommendation（工程）**：**需明确裁定**——本报告**不擅自选择**，因为它直接决定 `ER_MODEL:221` 是否可实现。
- **Human Decision Required**：✅（**建议优先裁定**）

### OQ-A21 — 【新增】Memory / Workflow 契约缺授权面
- **Question**：记忆读写与工作流执行是否需要授权，契约应如何携带？§27 要求列出"缺授权则不能安全实现的能力"。
- **Evidence**：`MemoryStore.read/write/delete(key)` 与 `WorkflowRunner.run(steps)` **均无任何 context/authz 参数**；
  对比 `Tool.invoke(params, context: ToolContext)` **有** context，`AgentRuntime.run(agent_id, AgentInput)` **有** actor_id。
- **Option A** 复用 `ToolContext` / **B** 引入统一 `AuthorizationContext` / **C** 暂不授权（置为受限能力）。
- **Security**：C **不安全**（记忆可能跨 space 泄漏）；§27 明确要求把这些列为"未授权前不可安全实现"。
- **Recommendation（工程）**：**B**，与 OQ-A14 的 `AuthorizationContext` 合并为同一对象，避免第二套上下文。
- **Human Decision Required**：✅

### OQ-A22 — 【新增】`AuditEvent.id` 生成策略与 UUIDv7 数据律
- **Question**：`core/audit` 用 `uuid.uuid4()` 生成 id，与「ID = UUIDv7（应用层）」的数据律是否冲突？
- **Evidence**：`core/audit/interfaces.py: _new_id() -> uuid.uuid4()`；
  数据律 §3.1「ID 统一 UUIDv7（应用层生成）；对外不透明标识用 UUIDv4」；
  DB 全部授权相关表 `id uuid PRIMARY KEY DEFAULT uap_uuid_v7()`。
- **Option A** 视为"对外不透明标识"（uuid4 合规）/ **B** 改为 UUIDv7（对齐数据律与 DB）。
- **Recommendation（工程）**：**B**（`AuditEvent` 是实体记录而非对外指针，宜与 DB 一致）；
  但需 Human 确认「对外不透明标识」的适用边界。
- **Human Decision Required**：✅

### OQ 汇总

| 编号 | 主题 | 冲突 | 阻塞实施 |
|---|---|---|---|
| A01 | RBAC/ACL/Policy 组合 | C-1(§6 重叠) | ✅ |
| A02 | Agent 是否独立 Subject | C-1 | ✅ |
| A03 | Delegation 关系 | C-4 | ✅ |
| A04 | Resource canonical | — | ✅ |
| A05 | Action 词汇表 | C-6 | ✅ |
| A06 | Scope hierarchy | — | ✅ |
| A07 | Allow/Deny precedence | — | ✅（已有先例待确认） |
| A08 | Inheritance | — | ✅ |
| A09 | Tool vs resource permission | — | ✅ |
| A10 | Risk classification | **C-2** | ✅ |
| A11 | Approval boundary | **C-5** | ✅ |
| A12 | Failure semantics | — | ✅（已有先例待确认） |
| A13 | Cache semantics | — | ✅ |
| A14 | Decision API contract | C-3/C-4/C-5 | ✅ |
| A15 | Audit requirements | **依赖 P10** | ✅ |
| A16 | Service placement | — | ✅ |
| A17 | Future schema impact | — | ✅ |
| **A18** | Subject/Identity 词汇表 | **C-1** | ✅ |
| **A19** | Agent 版本标识类型 | — | ⬜（低） |
| **A20** | ACL 唯一键不含 effect | — | ✅（**建议优先**） |
| **A21** | Memory/Workflow 缺授权面 | — | ✅ |
| **A22** | AuditEvent.id uuid4 vs UUIDv7 | — | ⬜（低） |

**22 项 OQ**（原 17 + 新增 5）。**全部已由 Human 逐项裁定**（2026-09-23）：
**19 `FROZEN` + 3 `DEFERRED`**（**OQ 口径**；完整 registry 另有非 OQ 的 `D-AUTH-23/24/25` ⇒ 共 25 条 = 22 + 3 + 0）
—— 逐项状态见 [`AUTHORIZATION_DECISION_RESOLUTION.md`](./AUTHORIZATION_DECISION_RESOLUTION.md) §0.1。
下表「阻塞实施」列保留**裁定前**的原始判断，作为历史证据。

---

## 19. Proposed Decisions → **已冻结为 `D-AUTH-01`…`D-AUTH-23`**

> **状态更新（2026-09-23）**：本节原为**建议草案**（`D-AUTH-P01`…`P10`）。
> Human 已逐项裁定，最终以 **`D-AUTH-01`…`D-AUTH-22`**（`OQ` 序列）编号写入
> [`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md)：**19 `FROZEN` + 3 `DEFERRED`**；
> 另经 `GAP-11` 专项追加非 OQ 的 **`D-AUTH-23`**（`FROZEN`）；2026-09-24 再追加 **`D-AUTH-24`**（`D-B14-08` → SUPERSEDED by `D-AUTH-05`）与 **`D-AUTH-25`**（Action canonical 形 = 小写）⇒ 完整 registry **25 条 = 22 + 3 + 0**。
> 以下草案保留为**历史记录**（其方向与最终冻结一致，但编号与粒度以 PDL 为准）。

以下为**当时建议写入** `PLATFORM_DECISION_LOG.md` 的条目草案：

```
D-AUTH-P01  [PROPOSED · Pending Human Decision]  Authorization 采用三层模型 RBAC + ACL + Policy（OQ-A01）
D-AUTH-P02  [PROPOSED · Pending Human Decision]  Agent 为独立 Subject，执行时以双主体表达（OQ-A02/A03）
D-AUTH-P03  [PROPOSED · Pending Human Decision]  Allow/Deny 沿用 R2-D-14「DENY > ALLOW」（OQ-A07）
D-AUTH-P04  [PROPOSED · Pending Human Decision]  Authorization 失败统一 FAIL CLOSED（OQ-A12）
D-AUTH-P05  [PROPOSED · Pending Human Decision]  授权契约置 core/，实现置 services/（OQ-A16）
D-AUTH-P06  [PROPOSED · Pending Human Decision]  审批采用「静态下限 + 策略加严」模型（OQ-A11）
D-AUTH-P07  [PROPOSED · Pending Human Decision]  风险等级统一为四档枚举 LOW/MEDIUM/HIGH/CRITICAL（OQ-A10）
D-AUTH-P08  [PROPOSED · Pending Human Decision]  首发不启用授权缓存（OQ-A13）
D-AUTH-P09  [PROPOSED · Pending Human Decision]  Decision 契约扩展为三值 ALLOW/DENY/REQUIRES_APPROVAL（OQ-A14）
D-AUTH-P10  [PROPOSED · Pending Human Decision]  授权审计持久化显式依赖 P10（OQ-A15）
```

> **状态更新**：上述 `D-AUTH-P01`…`P10` 草案**已被 `D-AUTH-01`…`D-AUTH-23` 取代**（2026-09-23，经 Human 明确授权写入；
> `D-AUTH-01`…`22` = OQ 序列，`D-AUTH-23` = `GAP-11` 专项）。
> 本报告产出时（PREP 轮）**未**向 `PLATFORM_DECISION_LOG.md` 写入任何内容；写入发生在随后的 Decision Freeze 轮。

---

## 20. Out of Scope（§3 全量遵守）

未执行且未授权：Agent Runtime / Tool Runtime / Workflow / Memory / Business Module 实现 ·
Adaptive Module Provisioning · **migration 0012+ 创建** · 任何 migration · DDL · DML · 生产库修改 ·
API runtime 代码 · service 实现 · worker · scheduler · Celery · 生产部署 · commit · tag · push。

**特别遵守**：未因"权限系统最终肯定要用到某张表"而提前建表（`resources.parent_id`、`policy_rules`、
`approval_requests`、`resource_relations` 一律**仅登记为 PROPOSED**）。

---

## 21. Exit Criteria（§38 逐项）

| # | 条件 | 状态 | 证据 |
|---|---|---|---|
| 1 | Baseline verified | ✅ | §2（HEAD/tag/hash/tree 全核验） |
| 2 | Existing model audited | ✅ | §3 |
| 3 | Identity model audited | ✅ | §5 |
| 4 | Subject model audited | ✅ | §5 · §10 |
| 5 | RBAC/ACL/Policy analyzed | ✅ | §6（A/B/C 三选项） |
| 6 | Resource model proposed | ✅ | §7 |
| 7 | Action model proposed | ✅ | §8 |
| 8 | Scope model proposed | ✅ | §9 |
| 9 | Agent delegation analyzed | ✅ | §10 · §11 |
| 10 | Tool authorization analyzed | ✅ | §12 |
| 11 | Risk model proposed | ✅ | §13 |
| 12 | Approval boundary proposed | ✅ | §13 |
| 13 | Failure semantics analyzed | ✅ | §14 |
| 14 | Cache semantics analyzed | ✅ | §15 |
| 15 | Audit model proposed | ✅ | §3.5 · OQ-A15 |
| 16 | Architecture placement analyzed | ✅ | §16 |
| 17 | Migration impact documented | ✅ | §17（Proposed only） |
| 18 | Security boundary audited | ✅ | §4 · 矩阵 SECURITY |
| 19 | Dependency impact audited | ✅ | §4 · 矩阵 DEPENDENCY |
| 20 | P09 protected | ✅ | 矩阵 P09 行 · 0010/0011 hash 未变 |
| 21 | OQ list complete | ✅ | §18（22 项） |
| 22 | Acceptance Matrix complete | ✅ | `AUTHORIZATION_ACCEPTANCE_MATRIX.md` |
| 23 | Scope clean | ✅ | 见下 |
| 24 | No implementation performed | ✅ | 见下 |

**Scope clean / No implementation 的证据**：

```text
migration 变更        = 0（0010/0011 hash 未变；0012+ absent）
代码变更              = 0（core/ agent/ apps/ infrastructure/ 未修改）
数据库变更            = 0（formal uap = 0 表，全程未触碰；无 DDL/DML）
本阶段新增文件        = 2（本报告 + 验收矩阵，均属 §37 允许的 PREP artifacts）
commit / tag / push   = 未执行
```

---

## 附：安全边界审计发现（§24）

| 潜在路径 | 现状 | 证据 | 处置 |
|---|---|---|---|
| `Agent → Database` | **不存在** | `agent/` 无 `sqlalchemy`/`psycopg`/`infrastructure` import；G-3 硬门通过 | 保持 |
| `Agent → SQL / session / engine` | **不存在** | 全层扫描仅命中 `memory/interfaces.py:13` 的 `scope: str = "session"`（字面量，非 DB session）—— **谓词已核对，非缺陷** | 保持 |
| `Agent → Infrastructure` | **不存在** | G-3 硬门 | 保持 |
| `Module → Cross-Tenant Resource` | **当前不可判定** | 无 Module 实现；`resources.tenant_id` NN + `require_same_tenant()` 契约存在 | 留待实施（矩阵 TENANT） |
| `Tool → Permission Bypass` | **未定义** | `Tool.invoke(params, context)` **不携带授权结果**；工具自行调用服务层无静态约束 | **OQ-A09 / OQ-A21** |
| `API → Direct Execution` | **不存在** | `apps/` 仅 health/meta 路由；无执行端点 | 保持 |
| `User Input → Privilege Escalation` | **未定义** | 无授权实现 ⇒ 无输入面；但 `Subject.role_keys` 由调用方构造 | 实施时必须由 trusted context 提供（矩阵 SECURITY） |

> ⚠ **本报告不修复任何上述项**（§24 明令"不得直接修复"）。

---

## 附：§27 Agent Runtime 依赖图（Authorization Dependency Map）

| 能力 | 缺完整 Authorization Model 时的风险 |
|---|---|
| Agent Invocation | **不能安全实现**（无法判定 actor 是否有权触发该 agent） |
| Context Retrieval | **不能安全实现**（无 scope 过滤依据 ⇒ 跨 tenant/space 泄漏） |
| Tool Selection | **不能安全实现**（`allowed_tools` 与 `agent_permissions` 无统一求值） |
| Tool Execution | **不能安全实现**（无 `REQUIRES_APPROVAL` 判定） |
| Memory Retrieval | **不能安全实现**（`MemoryStore` 零授权参数，OQ-A21） |
| Memory Write | **不能安全实现**（同上） |
| Workflow Action | **不能安全实现**（`WorkflowRunner.run(steps)` 零 context，OQ-A21） |
| External Action | **不能安全实现**（§19 外部发送属高审批档） |

---

**END OF AUTHORIZATION PREP REPORT（2026-09-23）**

> 本报告为 PREP / DESIGN / AUDIT 产物。**HUMAN DECISION REQUIRED — 不得自行实施。**
