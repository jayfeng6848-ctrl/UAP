# UAP STAGE 2 — AUTHORIZATION / ACL / POLICY

## IMPLEMENTATION CONTRACT

| 字段 | 内容 |
|---|---|
| **阶段** | `STAGE 2 — IMPLEMENTATION CONTRACT PREP` |
| **性质** | `PREP / DESIGN / CONTRACT`（**非** implementation） |
| **日期** | 2026-09-23 |
| **基线 HEAD** | `eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6` |
| **基线 TAG** | `UAP-V0.1.7-GOVERNANCE-GATE`（→ 同一 commit） |
| **Alembic head** | `0011_p09_agent_tool_permission`（单头 · branches none · 0012+ absent） |
| **权威来源** | `D-AUTH-01`…`D-AUTH-25`（`PLATFORM_DECISION_LOG.md`） |
| **决策 registry** | `D-AUTH` total **25** = `FROZEN` **22** + `DEFERRED` **3** + `SUPERSEDED` **0**（`OQ` 22 = 19 + 3；+ 非 OQ `D-AUTH-23` / `GAP-11` 与 `D-AUTH-24` / `D-AUTH-25` / `D-B14-08` 冲突裁定）；**平台级 supersession = 1**（`D-B14-08` → `D-AUTH-05`） |
| **实施授权** | **NOT AUTHORIZED** |

> **本文件的地位**：把已 `FROZEN` 的 `D-AUTH-01`…`23`（22 OQ + `GAP-11` 专项）转成**可实施、可验证、无歧义**的契约。
> 本文件**不重新解释**任何冻结决策。若发现冻结决策与现有 schema / 代码不一致，**只记录 `IMPLEMENTATION GAP`**，
> **不得修补**（§2）。

---

## 1. Baseline 与保护面（只读实测）

```text
HEAD = eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6（未推动）
TAG  = UAP-V0.1.7-GOVERNANCE-GATE → 同一 commit ✓
worktree = 8 项（5 modified docs + 3 untracked docs）· staged 0 · tags 7 · remote none
0010 sha256 = 6d9907237f80e9da4acdff86…（未变）
0011 sha256 = cdaf8383630335db92cfe54f…（未变）
Alembic head = 0011_p09_agent_tool_permission（单一）· branches none · 0012+ = 0
code diff = 0（无任何源代码变更）
D-AUTH 条目 = 22
```

---

## 2. Frozen Decisions（22 OQ / 22 + `GAP-11` 专项 1 = **23** 条）

> **范围说明**：`D-AUTH-01`…`D-AUTH-22` 与 `OQ-A01`…`OQ-A22` **一一对应（22 / 22）**。
> **`D-AUTH-23` 不来自任何 OQ** —— 它来自 `GAP-11`（Implementation Gap，非 OQ），
> 于 2026-09-23 经单条 Human Decision（**Option A — Legacy Opaque**）追加为 `FROZEN`。
> 合计：**`FROZEN` 20 + `DEFERRED` 3 = 23**。

| OQ | ID | 状态 | 契约落点（本文件节） |
|---|---|---|---|
| A01 | `D-AUTH-01` | FROZEN | §14 组合 · §11 §12 §13 |
| A02 | `D-AUTH-02` | FROZEN | §7 Subject |
| A03 | `D-AUTH-03` | `DEFERRED` | §7 base delegation context（完整 subsystem → Agent Runtime） |
| A04 | `D-AUTH-04` | FROZEN | §8 Resource |
| A05 | `D-AUTH-05` | FROZEN | §9 Action |
| A06 | `D-AUTH-06` | FROZEN | §10 Scope |
| A07 | `D-AUTH-07` | FROZEN | §14 Decision Combination |
| A08 | `D-AUTH-08` | FROZEN | §11 §12（继承语义） |
| A09 | `D-AUTH-09` | FROZEN | §18 Tool |
| A10 | `D-AUTH-10` | FROZEN | §16 Risk |
| A11 | `D-AUTH-11` | FROZEN | §17 Approval |
| A12 | `D-AUTH-12` | FROZEN | §19 Failure |
| A13 | `D-AUTH-13` | `DEFERRED` | §22 Cache（零实现） |
| A14 | `D-AUTH-14` | FROZEN | §15 Decision States |
| A15 | `D-AUTH-15` | FROZEN | §23 Audit |
| A16 | `D-AUTH-16` | FROZEN | §5 §6 §21 边界 |
| A17 | `D-AUTH-17` | FROZEN | `AUTHORIZATION_SCHEMA_IMPACT.md` |
| A18 | `D-AUTH-18` | FROZEN | §7 Subject |
| A19 | `D-AUTH-19` | FROZEN | §24 Agent Version |
| A20 | `D-AUTH-20` | FROZEN | §12 ACL |
| A21 | `D-AUTH-21` | `DEFERRED` | §23 / Agent Runtime |
| A22 | `D-AUTH-22` | FROZEN | §25 Audit Event ID |
| — | `D-AUTH-23` | FROZEN | §10 Scope 保护 · §19 Service 禁令（`GAP-11` / `ND-A`） |
| — | `D-AUTH-24` | FROZEN | §8 Action（`D-B14-08` → SUPERSEDED by `D-AUTH-05`；`SC-1b` 保留） |
| — | `D-AUTH-25` | FROZEN | §8.2 Case / Normalization / Storage / Comparison（canonical 形 = 小写） |

> `D-AUTH-23` 的 `OQ` 列为 `—`：其来源是 `GAP-11` 而非 OQ。
> 它**不改变** `D-AUTH-01`…`D-AUTH-22` 的任何既有语义，仅**封堵一条潜在旁路**（见 §19）。

---

## 3. Contract Traceability（§4，22 OQ + 非 OQ 专项 3（`GAP-11` + `D-B14-08` 冲突裁定）= **25**）

```text
D-AUTH-NN → Contract Requirement → Implementation Component → Test → Acceptance
```

| D-AUTH | Contract Requirement | Implementation Component | Test ID | Acceptance |
|---|---|---|---|---|
| 01 | 三层组合、职责不重复 | `DecisionCombiner` · `services/authorization` | T-COMBO · T-ARCH-04 | AUTH-01 |
| 02 | Agent 为独立主体 | `SubjectResolver` | T-SUBJ-03 · T-AGENT-01 | AGENT-01 |
| 03 | base delegation context（Agent/Actor/Delegator 可区分） | `SubjectResolver` · `ToolContext` | T-SUBJ-05 · T-AGENT-02 | AGENT-02 |
| 04 | Resource 7 项 canonical / owner 仅 USER | `ResourceResolver` | T-RES-01…03 | SCOPE-05 |
| 05 | 12 项 Action 词表 | `ActionResolver` | T-ACT-01…05 | AUTH-06 |
| 06 | 3 层 stored scope；SELF/RESOURCE 为 predicate | `ScopeEvaluator` | T-SCOPE-01…05 | SCOPE-01…04 |
| 07 | DENY > ALLOW，确定性/顺序无关/可审计 | `DecisionCombiner` | T-COMB-01…08 | POLICY-05 |
| 08 | Explicit & Downward；无 parent 继承 | `PermissionResolver` | T-INHERIT-01…02 | SCOPE-05 |
| 09 | Tool 唯一出口 + 结构化四元组 | `ToolGate` · `tool_permissions` 增列 | T-TOOL-01…05 | TOOL-01 · 03 · 07 |
| 10 | 四档 Risk；score 仅内部信号 | `PolicyEvaluator`（risk 输入） | T-RISK-01…04 | RISK-01…04 |
| 11 | 审批 = 静态 OR 策略；审批 ≠ Permission | `ApprovalGate`（contract only） | T-APPR-01…03 | APPROVAL-01 · 03 · 04 |
| 12 | FAIL CLOSED（8 类分支） | `AuthorizationService` | T-FAIL-01…09 | SEC-06 |
| 13 | 当前零缓存；不得 fail-open | （无组件） | T-CACHE-01 | CACHE-01 |
| 14 | 三值决策；REQUIRES_APPROVAL 为终态语义 | `Decision` value object | T-DEC-01…04 | APPROVAL-02 |
| 15 | 授权审计 ≠ 工具执行审计 | `AuditBoundary` | T-AUDIT-01…04 | AUDIT-02 · 03 |
| 16 | core 契约 / services 实现 / infra 适配 | 分层落点 | T-ARCH-01…04 | ARCH-02 · 05 |
| 17 | 0 schema 变更（本冻结）；实施期变更见 SC | `AUTHORIZATION_SCHEMA_IMPACT.md` | T-MIG-01…04 | MIG-05 · 06 |
| 18 | Subject Types = {USER, ROLE, AGENT} ⊥ Provider | `SubjectType` enum | T-SUBJ-01…02 | AUTH-05 |
| 19 | 单调整数 revision | `AgentVersionRef` | T-VER-01…02 | AGENT-07 |
| 20 | ACL unique key 不变 | `ACLStore`（契约） | T-ACL-01…04 | SEC-08 |
| 21 | Memory/Workflow 同一 Authorization Model | （DEFERRED） | T-DEP-01 | DEP-06 · 07 |
| 22 | Audit/Event ID = UUIDv7 | `AuditBoundary` | T-AUDIT-05 | AUDIT-06 |
| **`23`** | **`resource_scope` = Legacy Opaque（不解释 · 非授权权威 · `ND-A` 不追加 `<> ''`）** | `AuthorizationService`（**禁令**，§19.1） | `AGENT-RESOURCE-SCOPE-01…04` | `AGENT-RESOURCE-SCOPE-01…04` |

**Traceability 结果：22 / 22 OQ 无 orphan；另加 `D-AUTH-23`（`GAP-11`）与 `D-AUTH-24` / `D-AUTH-25`（`D-B14-08` 冲突裁定）3 条（**非** OQ）⇒ 合计 **25**，无 orphan**
（每个 `D-AUTH` 均有 Contract / Component / Test / Acceptance）。

---

## 4. Component Boundaries（§5）

> 原则（§5）：**若仓库已有对应 Contract，优先复用，不平白创建重复抽象。**

| 候选组件 | 现有契约 | 处理 |
|---|---|---|
| `SubjectResolver` | `core/identity.IdentityResolver` + `core/permission.Subject` | **REUSE + EXTEND**（`Subject` 需支持 subject_type / agent / tenant） |
| `ResourceResolver` | `core/resource.ResourceResolver` / `ResourceRef` | **REUSE**（形状已满足 `D-AUTH-04`） |
| `ActionResolver` | `core/permission.Action` | **EXTEND**（增补 canonical 词表与 NFKC+小写归一，`D-AUTH-25`） |
| `ScopeEvaluator` | `core/resource.is_in_scope` + `core/tenant.require_same_tenant` | **REUSE** |
| `PermissionResolver` | `core/permission.Authorizer`（Protocol） | **REUSE 契约；实现落 `services/`** |
| `PolicyEvaluator` | `core/policy.PolicyEvaluator` + `RiskPolicy` | **REUSE + CLARIFY**（`score` 降为内部信号，见 GAP-1） |
| `DecisionCombiner` | `core/permission.Decision` + `core/policy.combine` | **EXTEND**（统一为单一跨层算法；三值） |
| `AuthorizationService` | **无** | **NEW** → `services/authorization/` |
| `AuditBoundary` | `core/audit.AuditSink` + `AuditEvent` | **EXTEND**（字段 + id 策略；persistence → P10） |
| `ToolGate` | `agent/tools.Tool` / `ToolContext` | **EXTEND**（执行前强制携带决策） |
| `ApprovalGate` | **无**（仅 `tools.approval_required`） | **NEW（contract only）**；persistence → Tool Runtime |

**结论**：**不新增第三个 core 契约包**（延续 `D-AUTH-16`），复用 `core/{permission,policy,resource,audit,identity}`。

---

## 5. Core Contract Analysis（§6）

### 5.1 逐模块

| 模块 | Existing Contract | Frozen Requirement | Missing | Duplicate | Implementation Boundary |
|---|---|---|---|---|---|
| `core/permission` | `Action` · `Decision` · `DENY` · `Subject` · `Authorizer` | D-AUTH-01/02/07/14/18 | `SubjectType` · `Effect` 三值 · canonical action 校验 | 与 `core/policy` 的 **Owns 重叠**（前者声明含 ABAC） | **纯契约 + 纯规则**；不得 import DB |
| `core/policy` | `PolicyContext` · `PolicyDecision` · `PolicyEvaluator` · `RiskPolicy` · `combine` | D-AUTH-01/10/11/13 | 风险四档枚举 · approval 需求表达 | `combine` 与 `core/permission` 的合并语义重复 | 纯契约；**`conditions` 解析归此层** |
| `core/resource` | `ResourceRef` · `ResourceScope` · `is_in_scope` | D-AUTH-04/06/08 | —（7 项齐备） | 无 | 纯值对象 |
| `core/audit` | `AuditEvent` · `AuditSink` | D-AUTH-15/22 | `subject`/`delegator`/`decision`/`reason`/`policy`/`risk`/`approval` | 无 | 契约 + 边界；**persistence → P10** |
| `core/membership` | `Membership`（space-only; `identity_id` + `role_key`） | D-AUTH-08（继承） | tenant/platform 层级；`user_id`/`role_id` 对齐 | 与 DB **三张** membership 表语义不一致 | **契约层扩展**；DB 读取归 `services/` |

### 5.2 分层边界（`D-AUTH-16` 冻结）

```text
Core            = pure contracts / value objects / pure rules        （无 I/O）
Application     = authorization decision orchestration               （services/authorization）
Infrastructure  = persistence / adapters / external integration
```

**禁止**（本轮已在 `DEPENDENCY_RULES.md §8` 记录）：
`Core → DB` · `Core → SQLAlchemy` · `Core → psycopg` · `Core → services` ·
`Agent → DB` · `Agent → Infrastructure` · `Agent → services`。

---

## 6. SUBJECT CONTRACT（§7）

### 6.1 类型（`D-AUTH-18`）

```text
SubjectType = USER | ROLE | AGENT        ← Authorization 域（canonical）
IdentityKind / IdentityProvider           ← Authentication 域（正交，不得混用）
```

### 6.2 值对象

```python
@dataclass(frozen=True)
class SubjectRef:
    subject_type: SubjectType      # USER | ROLE | AGENT
    subject_id: str                # uuid；对应 users.id / roles.id / agents.id
    tenant_id: str | None          # 解析结果携带租户归属
    role_keys: tuple[str, ...] = ()      # RBAC 基线（既有 Subject 字段保留）
    scopes: tuple[str, ...] = ()         # 既有字段保留
```

### 6.3 Delegation 语义（`D-AUTH-02` / `D-AUTH-03`）

```text
Agent       = Independent Authorization Subject        （执行主体）
Actor       = 发起动作的用户（适用时）
Delegator   = 委托来源（适用时；当前与 Actor 同源）
Effective   = Agent 权限 ∩ Actor 有效授权              （D-AUTH-03 已冻结的基础语义）
```

**冻结的禁止项**：
- ❌ `Agent permission = User permission automatically`
- ❌ `Agent authority > effective authority of delegating user`

**本轮 Contract 只冻结 base delegation context**（`agent_id` / `actor_id` / `delegator_id` 三者可区分且可传递）；
**完整 delegation grant/revoke/expiry/scope subsystem → `DEFERRED TO AGENT RUNTIME`**（不提前实现）。

---

## 7. RESOURCE CONTRACT（§8）

```python
@dataclass(frozen=True)
class ResourceRef:
    type: str                  # resources.resource_type（正则 ^[a-z][a-z0-9_.]{1,63}$）
    id: str                    # resources.id（UUIDv7）
    tenant_id: str             # NOT NULL
    space_id: str | None = None
    owner_identity_id: str | None = None   # 仅 USER（D-AUTH-04）
```

| 属性 | 来源 | 状态 |
|---|---|---|
| `resource_type` | `resources.resource_type` | EXISTING |
| `resource_id` | `resources.id` | EXISTING |
| `tenant` | `resources.tenant_id` (NN) | EXISTING |
| `space` | `resources.space_id` | EXISTING |
| `classification` | `resources.classification`（PUBLIC/INTERNAL/CONFIDENTIAL/HIGHLY_CONFIDENTIAL） | EXISTING |
| `owner` | `resources.owner_id` → users | EXISTING（**owner 仅 USER**） |
| `lifecycle` | `resources.status` + `archived_at` + `deleted_at` | EXISTING |
| `parent` | — | **NOT ADOPTED**（`D-AUTH-04` / `D-AUTH-08`） |

**禁止**：不引入 `parent_id` / `resource_relations`；不因 Agent 成为 Subject 而允许 Agent 做 owner。

---

## 8. ACTION CONTRACT（§9）

### 8.1 Canonical vocabulary（`D-AUTH-05`，12 项）

```text
READ  LIST  CREATE  UPDATE  DELETE  EXECUTE  APPROVE  REJECT  PUBLISH  EXPORT  SHARE  ADMIN
```

### 8.2 实现必须明确的六项（§9）

> **2026-09-24 更新（`D-AUTH-25`）**：canonical **存储/传输形 = 小写**（`read`…`admin`）。
> `D-AUTH-05` 的 12 个动作名不变，变的只是其规范形；宽容度只在**入站归一**。

| 项 | 契约规定 |
|---|---|
| **Case** | canonical **存储/传输形式为小写**（`read`…`admin`）；`Action.name` 对外统一小写（**`D-AUTH-25`**） |
| **Normalization** | 归一 = **NFKC → strip → casefold**；比较前对**双侧**执行（防同形字符绕过） |
| **Validation** | 必须属于 canonical 集合（或已注册 Module 扩展） |
| **Storage** | DB 中 `permissions.action` / `resource_permissions.action` 为 `text`；**新增 CHECK 约束，取值 = 小写 canonical 形**（`SC-1` / `SC-1b`）；`READ`/`Read`/`rEaD` 在**存储边界**一律拒绝（宽容只在入站归一） |
| **Comparison** | 仅按归一化后的**小写**形式比较；`_same_action` 对 stored 与 requested **双侧归一**，非字符串存储值安全返回 False |
| **Extensibility** | Module 扩展 action 必须 **Registered / Discoverable / Auditable / Policy-compatible**；registry 载体属 Schema Impact（`SC-3`，**本阶段仅登记**） |

**禁止**：不得建立第二套 Action 词表；不得让 Module 自由产生不可审计字符串；
**不得在 canonical 路径使用 `upper()` / 大写比较**（§5 —— 禁止大小写敏感比较与 case-specific 比较）。

---

## 9. SCOPE CONTRACT（§10）

```text
Stored grant scope (canonical) = PLATFORM | TENANT | SPACE        （D-AUTH-06）
Predicate (NOT a stored scope) = RESOURCE | SELF
```

| 概念 | 契约规定 |
|---|---|
| **Scope Match** | `is_in_scope(ref, scope)`：`tenant` 必须相等；若 scope 含 space 则 space 必须相等 |
| **Scope Inheritance** | `PLATFORM → TENANT → SPACE → Resource Context`；**Explicit and Downward**（`D-AUTH-08`） |
| **Scope Restriction** | 子作用域**不得**扩大父作用域的授权（只可收紧） |
| **Scope Conflict** | 跨 tenant ⇒ **无条件 DENY**（`lib `require_same_tenant()` 语义） |
| **`SELF`** | **Context predicate**：`resource.owner_id == subject.subject_id ∧ subject_type == USER` |
| **`RESOURCE`** | 资源实例层，由 `resource_permissions` 承载，**不是 role scope** |
| **Canonical Scope 承载面** | Canonical Stored Scope **恒由** `roles.scope`（`ck_roles_scope` + `tg_roles_scope_shape`）承载。**`agent_permissions.resource_scope` 不是** canonical scope carrier —— **不得**据其推导出 `PLATFORM` / `TENANT` / `SPACE`（**`D-AUTH-23`**） |

> **`D-AUTH-23` 补充（`GAP-11`）**：`agent_permissions.resource_scope` = **Legacy Opaque**。
> 它**既不禁也不授** —— `invalid` / `unknown` / `empty` / whitespace / 任意 opaque 取值**均不产生 `ALLOW`**，
> 因为本契约**不从该字段推导授权**。实现禁令与 Runtime 引用规则见 **§19.1**。

---

## 10. RBAC CONTRACT（§11）

```text
Role          ← roles(scope ∈ PLATFORM|TENANT|SPACE)      ← 3 部分唯一索引 + tg_roles_scope_shape
Permission    ← permissions(key / resource_type / action / is_system)
RolePermission← role_permissions(role_id, permission_id, effect, conditions)
                PK = (role_id, permission_id, effect)  ⇒ allow+deny 可并存
```

**Effective Grant 计算**：

```text
Membership(3 层) → Role(active) → RolePermission(effect) → 基线 Grant 集合
任一匹配的 deny  ⇒ 该 permission 在 RBAC 层被拒绝（D-AUTH-07）
```

**RBAC = baseline authorization**（`D-AUTH-01`）：提供"角色基线能力"，**不承担** tenant/space 实例级边界
（延续 `R2-D-15` permission scope-neutral —— **不得**把 `permissions` 当作边界载体）。

**禁止**：不得让 RBAC 直接裁定实例级授权（那是 ACL 的职责）。

---

## 11. ACL CONTRACT（§12）

```text
Resource      ← resources
Subject       ← acl_subject_types(key ∈ user|role|agent) + subject_id（trigger 验存在性）
Permission    ← resource_permissions.action（canonical）
Effect        ← allow | deny
Inheritance   ← inherited 布尔；**语义 ≠ parent 继承**（无 parent，D-AUTH-08）
Expiration    ← expires_at（过期即不参与）
```

**ACL = resource-specific grant**（`D-AUTH-01`）。

**冻结不变（`D-AUTH-20`）**：
- `UNIQUE (resource_id, subject_type_id, subject_id, action)` **保持不变**；**不新增 `effect`** 到唯一键。
- ACL 层同一唯一槽位**不要求** Allow 与 Deny 并存；**改判 = 行替换/更新**。
- 改判**必须**同事务写审计（`STEP1B_ACL_STRATEGY §6` 既有要求）。
- **跨层 `ACL DENY > RBAC ALLOW` 仍然成立**（由 `DecisionCombiner` 实现，非 DB）。

**禁止**：不得重建 unique key；不得在 trigger 中做授权解释（延续 `R2-D-14`「DB 不做授权解释」）。

---

## 12. POLICY CONTRACT（§13）

```text
Input       ← PolicyContext(action, actor_id, tenant_id, space_id, environment) + 扩展字段
Condition   ← role_permissions.conditions / 未来策略载体（当前 storage-only，R2-D-15）
Evaluation  ← core/policy.PolicyEvaluator（纯函数，确定性）
Effect      ← allow | deny
Result      ← PolicyDecision(allowed, policy_id, reasons)
```

**Policy = Contextual / conditional decision**（`D-AUTH-01`）。

**关键约束**：
- 策略**只能收紧**，**不得**放宽 RBAC/ACL 的静态授予（否则构成提权面）。
- `conditions` 当前为 **storage-only**（`R2-D-15`）→ 本轮**只**定义契约形状与归属（归 `core/policy`），
  **不**直接扩展为完整 rule engine（§13）。
- `policy_version` 必须进入 `Decision` 与审计（`D-AUTH-14` / `D-AUTH-15`）。

---

## 13. DECISION COMBINATION（§14）

### 13.1 唯一算法（`D-AUTH-01` + `D-AUTH-07`）

```text
1. 归一化输入（subject / action / resource / scope）
2. 解析主体        → 失败 ⇒ DENY
3. 解析资源        → 失败/不存在 ⇒ DENY
4. 校验 action     → 非 canonical ⇒ DENY
5. tenant/space 边界 → 跨 tenant ⇒ DENY（无条件）
6. RBAC  求值      → allow / deny / 无
7. ACL   求值      → allow / deny / 无
8. Policy 求值     → allow / deny / 失败
9. 合并：
     任一 deny（RBAC ∪ ACL ∪ Policy）           ⇒ DENY
     Policy 失败                                ⇒ DENY（fail closed）
     审批需求成立（静态 OR 策略）               ⇒ REQUIRES_APPROVAL
     否则任一 allow                             ⇒ ALLOW
     否则（无任何 allow，default deny）          ⇒ DENY
```

**性质（`D-AUTH-07` 冻结）**：**deterministic** · **order-independent** · **auditable**（携带命中来源）。

### 13.2 Decision Truth Table（§14 要求）

| # | RBAC | ACL | Policy | 审批需求 | 结果 | 依据 |
|---|---|---|---|---|---|---|
| 1 | allow | — | — | 否 | **ALLOW** | 基线授予 |
| 2 | — | allow | — | 否 | **ALLOW** | 资源授予 |
| 3 | allow | allow | allow | 否 | **ALLOW** | 全部通过 |
| 4 | **deny** | allow | allow | — | **DENY** | `D-AUTH-07` deny 优先 |
| 5 | allow | **deny** | allow | — | **DENY** | `ER_MODEL:221` ACL deny > RBAC allow |
| 6 | allow | allow | **deny** | — | **DENY** | `D-AUTH-07` |
| 7 | deny | deny | deny | — | **DENY** | `D-AUTH-07` |
| 8 | 无 | 无 | 无 | 否 | **DENY** | **DEFAULT DENY** |
| 9 | allow | — | — | **是** | **REQUIRES_APPROVAL** | `D-AUTH-11` / `D-AUTH-14` |
| 10 | — | — | — | 是 | **REQUIRES_APPROVAL** | 策略侧要求 |
| 11 | — | — | **失败** | — | **DENY** | `D-AUTH-12` fail closed |
| 12 | — | — | — | — | **DENY** | `D-AUTH-12` authorization unavailable |
| 13 | — | — | — | — | **DENY** | `D-AUTH-12` 未知 subject / resource / action |
| 14 | allow（**已过期/已撤销**） | — | — | — | **DENY** | `D-AUTH-12` |

> **注意第 9/10 行**：`REQUIRES_APPROVAL` **优先于** ALLOW —— 即"允许但需审批"**不是** ALLOW。

---

## 14. DECISION STATES（§15）

```python
class DecisionEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
```

**语义（`D-AUTH-14` 冻结）**：`REQUIRES_APPROVAL` **不是最终 execution authorization** ——
它表示 **`Execution blocked until approval requirement satisfied`**。

**禁止**：任何调用方（Agent / Tool / Module）**不得**把 `REQUIRES_APPROVAL` 当作可继续执行。

`Decision` 必含字段（`§22` + `D-AUTH-14`）：

```text
subject · delegator · action · resource · scope · context · effect · reason · policy_version
（保留 allowed: bool 为派生只读属性 = (effect == ALLOW)）
```

---

## 15. RISK CONTRACT（§16）

```text
canonical RiskLevel = LOW | MEDIUM | HIGH | CRITICAL      （D-AUTH-10）
```

**冻结关系**：

```text
Risk ≠ Permission
Risk ≠ Decision
Risk 影响 Policy / Approval（作为输入）
```

**`RiskPolicy.score() -> float[0,1]` 的处理（`IMPLEMENTATION GAP-1`）**：
该 float 契约**保留为内部 calculation signal**（用于排序/提示/阈值映射），
**不得**被重新定义成 platform canonical risk model；对外/入库一律使用四档枚举
（`tools.risk_level` · `agents.max_risk_level` · `tool_executions.risk_level` 已是四档）。
若未来需要 score → 四档映射，**必须**冻结**确定性映射表**（当前**未**冻结，记为待定项）。

---

## 16. APPROVAL CONTRACT（§17）

```text
ApprovalRequired = ToolRequirement OR PolicyRequirement          （D-AUTH-11，逻辑或）
```

**冻结禁止项**：
- ❌ 不得使用 **AND**（会削弱静态下限）。
- ❌ **`Approval ≠ Permission`**；**审批结果 ≠ `ALLOW`**。

```text
approval_required(tool)  ← tools.approval_required（静态，已落库）
approval_required(policy)← PolicyEvaluator 判定（动态；载体属 Tool Runtime / P10）
```

**本轮**：只定义 contract；**不实现 Approval Persistence**；**不创建** `approval_requests`。

---

## 17. TOOL CONTRACT（§18）

```text
Tool → Authorization → Policy → Approval if required → Execution
```

**Tool = controlled execution boundary**（`D-AUTH-09`）。

**结构化要求（`D-AUTH-09` 明确要求"必须能够结构化表达"）**：

```text
Tool + Action/Capability + Scope + Resource Context
```

→ 实现落点：`tool_permissions` **增列**（Schema Impact `SC-2`）。
**具体 schema structure 属本 Contract 的输出**，见 `AUTHORIZATION_SCHEMA_IMPACT.md`。

**冻结禁止项**：
- ❌ `Tool → direct DB`
- ❌ `Tool → permission bypass`
- ❌ 让 Tool 自行实现授权逻辑

**契约扩展**：`Tool.invoke(params, context)` 需扩展为**执行前强制携带授权决策**
（`decision` 句柄或等价参数），否则 `TOOL-03` 不可验证。

---

## 18. FAILURE CONTRACT（§19）

### 18.1 8 类失败分支（全部 ⇒ `DENY`）

```text
Unknown Subject · Unknown Resource · Unknown Action
Permission Lookup Failure · Policy Failure · Authorization Service Failure
Expired Grant · Revoked Grant
```

### 18.2 错误映射（§19 明确要求区分）

```text
DecisionEffect.DENY  + reason.kind = EXPLICIT_DENIAL   ← 明确的策略/授权拒绝
DecisionEffect.DENY  + reason.kind = INTERNAL_FAILURE  ← 系统故障（查找失败/服务不可用/求值错误）
```

> **要求**：两者**结果相同（DENY）**，但**可观测性不同**（日志/指标/告警必须可分辨）。
> **禁止**：不得把所有 DENY 都表现为系统故障，也不得把内部故障伪装成"明确的业务拒绝"。

---

## 19. AUTHORIZATION SERVICE（§20）

**只定义 Contract，不实现。**

```python
@dataclass(frozen=True)
class AuthorizationRequest:
    subject: SubjectRef
    action: Action
    resource: ResourceRef
    context: AuthorizationContext      # tenant / space / environment / request_id / delegator

@dataclass(frozen=True)
class AuthorizationContext:
    tenant_id: str
    space_id: str | None = None
    request_id: str | None = None
    actor_id: str | None = None        # base delegation context（D-AUTH-03）
    delegator_id: str | None = None
    environment: Mapping[str, Any] = field(default_factory=dict)

class AuthorizationService(Protocol):
    def authorize(self, request: AuthorizationRequest) -> Decision: ...
```

**落点**：契约 → `core/`；实现 → `services/authorization/`（`D-AUTH-16`）。`services/` 包**尚不存在**。

### 19.1 实现禁令（`D-AUTH-23` — `GAP-11`）

> **规范表述**：`agent_permissions.resource_scope` = **OPAQUE TEXT** · **NOT AUTHORIZATION AUTHORITY**（不构成授权权威）·
> `ND-A = RESOLVED`（**不追加** `<> ''`）· `P09` / `0011` **unchanged**。

```text
AuthorizationService MUST NOT derive
    any authoritative authorization decision, scope, tenant boundary, or permission grant
from agent_permissions.resource_scope.
```

也**不得**对该字段执行 `parse` / `normalize` / `map` / `promote` / `reinterpret` 为 Canonical Authorization Scope。

| 项 | 内容 |
|---|---|
| **权威来源限定** | `AuthorizationService` 的授权权威**只能**来自：`roles` / `role_permissions`（RBAC）· `resource_permissions`（ACL）· `core/policy` 条件（Policy）· `tool_permissions`（Tool 侧，`D-AUTH-09`）。**`agent_permissions.resource_scope` 不在其中。** |
| **安全后果** | `invalid` / `unknown` / `empty` / opaque 的 `resource_scope` 取值**均不得产生 `ALLOW`** —— 因为服务**不从该字段推导授权**（与 `D-AUTH-12` FAIL CLOSED 一致）。 |
| **Runtime 引用规则** | 运行时 `.py` 对 `agent_permissions.resource_scope` 的引用数 **= 0**（测试见 `AGENT-RESOURCE-SCOPE-01`）。允许的引用面**仅限**：migration 源 · integration test · design documentation · implementation contract。 |
| **未来变更** | 任何规范化 / 验证 / 重新定义该字段的需求 ⇒ **NEW HUMAN DECISION + P09 SUPERSESSION**，不得由实现轮自行处理。 |

---

## 20. PERSISTENCE BOUNDARY（§21）

```text
Domain / Application  (services/authorization)
        ↓  Repository / Adapter（在 services/ 内定义接口）
Infrastructure        (infrastructure/database)
        ↓
Database
```

**Authorization core 不直接**：`SQLAlchemy` · `psycopg` · `PostgreSQL`。

---

## 21. CACHE（§22）

`D-AUTH-13` 已 **`DEFERRED TO TOOL RUNTIME`** ⇒ 本轮 **`CACHE IMPLEMENTATION = 0`**。

契约必须明确：**`AuthorizationService` 不得依赖未来 cache 的存在**（即：无 cache 时功能完整、语义不变）。

---

## 22. AUDIT（§23）

```text
Authorization Decision Audit  ≠  Tool Execution Audit          （D-AUTH-15）
```

**AuthorizationDecisionAudit 必备字段**（12）：

```text
subject · delegator/actor context · tenant · space · resource · action
decision · reason · policy · risk · approval · timestamp
```

**边界**：本轮只定义 **`AuthorizationDecisionAudit` boundary**（契约 + 字段）；
**persistence → `DEFERRED TO P10`**；**不得创建** `events` / `audit_logs`。

---

## 23. AGENT VERSION（§24）

`D-AUTH-19` 冻结：**`Runtime Version Resolution = Monotonic Integer Revision`**。

Contract 必须明确四件事：

```text
Agent Version Selection   : 由 agents.current_version_id（不可变引用）选定
Published Version         : agent_versions.status = 'published'（0008/0011 已强制不可回退）
Runtime Version           : 单调整数 revision（agent_versions.version integer）
Immutable Reference       : agent_versions.id（UUIDv7）+ checksum
```

**禁止**：不得重新设计 P09 schema；不得以 display 字符串驱动版本解析。

---

## 24. AUDIT EVENT ID（§25）

`D-AUTH-22`：未来 Audit / Event ID = **UUIDv7**（应用层生成；时间有序；利于 P10 分区裁剪）。
本轮**只**在 Contract 中确认 future event identity requirement；**P10 persistence 另行实现**。

---

## 25. Schema Change Set（§26/§27，摘要）

**完整分析与变更集见 [`AUTHORIZATION_SCHEMA_IMPACT.md`](./AUTHORIZATION_SCHEMA_IMPACT.md)。**

摘要：

```text
MODIFY : permissions.action          → 新增 canonical CHECK          （SC-1，D-AUTH-05）
ADD    : tool_permissions            → 结构化四元组列                （SC-2，D-AUTH-09）
登记   : Module 扩展 action registry → PROPOSED（本阶段不创建）      （SC-3，D-AUTH-05）
NO CHANGE: resource_permissions / roles / role_permissions / resources / agent_permissions / tools
```

**迁移决策（§27）**：**1 migration**（append-only · single-head · 不改历史）：
`0012_authz_enforcement`（**计划中，未创建**）。

**P09 保护**：`agents` / `agent_versions` / `agent_permissions` / `tool_executions` **不改**；
`agent_permissions.resource_scope` 的非结构化问题记为 **GAP-11** ⇒ 已由 **`D-AUTH-23`（`FROZEN`，2026-09-23）**
裁定为 **Legacy Opaque**：**保持 `OPAQUE TEXT`** · **不解释** · **不构成授权判定** · **不追加** `<> ''`（`ND-A` = `RESOLVED`）。
⇒ **`GAP-11 = RESOLVED`**；**schema 动作 = 0**；迁移决策**不变**（仍 **1 migration**：`0012_authz_enforcement`，未创建）。

---

## 26. IMPLEMENTATION GAPS（§2 要求：记录，不修补）

| # | Gap | 证据 | 影响 | 处置 |
|---|---|---|---|---|
| GAP-1 | `core/policy.RiskPolicy.score() -> float[0,1]` vs `D-AUTH-10` 四档 | 契约 vs DB 三处四档 CHECK | 风险值域双轨 | 契约：score 降为内部信号；对外四档。映射表**未冻结** → 待定项 |
| GAP-2 | `core/permission.Subject` 无 `subject_type` / agent / tenant | 契约仅 `identity_id/role_keys/scopes` | 无法表达 Agent 主体 | 实施期 EXTEND（§6） |
| GAP-3 | `core/policy.PolicyContext` 仅单 `actor_id` | vs `tool_executions` 双列 | delegation 不可表达 | 实施期 EXTEND base context（完整 → Agent Runtime） |
| GAP-4 | `core/permission.Decision.allowed: bool` | vs `D-AUTH-14` 三值 | 三值无处安放 | 实施期 EXTEND 为 `effect` |
| GAP-5 | `core/membership.Membership`（space-only, `identity_id`+`role_key`）vs DB 三张表（`user_id`+`role_id`） | 契约 vs 0011 实测 | 契约与 schema 语义不一致 | 契约层扩展 + `services/` 适配；**不改 DB** |
| GAP-6 | `AgentDescriptor.version: str` vs `agent_versions.version integer` | 契约 vs DB | 版本语义混淆 | 实施期对齐（`D-AUTH-19`） |
| GAP-7 | `core/audit.AuditEvent` 缺 7 类字段 + `uuid.uuid4()` | 契约 vs `D-AUTH-15`/`D-AUTH-22` | 审计不可表达 | 实施期 EXTEND；persistence → P10 |
| GAP-8 | `agent/memory` / `agent/workflow` 零授权参数 | 契约实测 | 无法授权 | **`D-AUTH-21` DEFERRED → Agent Runtime**（本轮不处理） |
| GAP-9 | `IDENTITY_KINDS` vs `acl_subject_types` 词汇不同 | 契约 vs DB CHECK | 词汇混用风险 | 契约层显式分离（§6）；**不改** `acl_subject_types` |
| GAP-10 | Action 词汇在契约与 DB **均无枚举** | 契约 `Action.name` 自由 str；DB 无 CHECK | 拼写变体绕过 | **SC-1**（DB CHECK）+ 契约枚举 |
| GAP-11 | `agent_permissions.resource_scope` 为无约束自由 text | 0011 实测 | agent 级资源范围不可验证 | ✅ **RESOLVED** — `D-AUTH-23`（`FROZEN`）：**Legacy Opaque**（保持 opaque · 不解释 · 不构成授权判定 · `ND-A` 不追加 `<> ''`）；**P09 不改**；`parse`/`normalize` 禁令见 **§19.1** |
| GAP-12 | `services/` 包不存在 | 目录实测 | 实现无落点 | 实施期**首个**动作：建立包（`D-PLAT-01`） |
| GAP-13 | `tool_permissions` 无 resource/action/scope 列 | 0008 实测 vs `D-AUTH-09` | 工具授权不可结构化 | **SC-2**（增列，非 P09 表） |

> **本阶段不修补任何 GAP**（§2）。**例外**：`GAP-11` 已于 2026-09-23 经 **`D-AUTH-23`** 完成 Human Decision ⇒
> **`RESOLVED`**（**Legacy Opaque** · `ND-A` 不追加 `<> ''`）。其处置**不含任何 schema 动作**：`0011` / `agent_permissions` /
> 现有约束 / 现有索引**全部不变**；配套约束落在**契约与测试层**（**§19.1** + `AGENT-RESOURCE-SCOPE-01..04`）。
> 其余 **12** 项 GAP 状态**不变**（仍为「记录，不修补」）。

---

## 27. Implementation Sequence（§32，**本轮不执行**）

```text
1.  Authorization primitives        （core/ 纯值对象与枚举：SubjectType/Effect/RiskLevel/Action 词表）
2.  Subject resolution              （SubjectResolver；base delegation context）
3.  Resource resolution             （ResourceResolver）
4.  Permission resolution           （RBAC + ACL 读取；经 services/ 适配）
5.  Policy evaluation               （core/policy；conditions 解析）
6.  Decision combination            （DecisionCombiner；DENY>ALLOW / default deny / fail closed）
7.  Authorization service           （services/authorization；含 AuditBoundary 契约）
8.  Tool integration                （ToolGate；执行前强制决策）
9.  Audit boundary                  （契约 + 字段；persistence 待 P10）
10. Security tests                  （§30 矩阵）
11. Migration verification          （§27 变更集；0012 执行须单独授权）
12. Full regression                 （基线 ≥ 342 passed，不得下降）
```

---

## 28. Gate 与验收

| 项 | 状态 |
|---|---|
| `IMPLEMENTATION CONTRACT` | **PASSED**（23/23 traceable · Contract complete · Schema Impact complete · Migration plan complete · P09 protected · 无未决歧义） |
| `IMPLEMENTATION` | **NOT AUTHORIZED** |
| `MIGRATION` | **NOT AUTHORIZED**（`0012` 未创建） |
| `COMMIT` / `TAG` / `PUSH` | **NOT AUTHORIZED** |

**放行条件**：另需 Human 明确签发 **`IMPLEMENTATION AUTHORIZATION`**（§33）；
门报告见 [`AUTHORIZATION_IMPLEMENTATION_GATE_REPORT.md`](./AUTHORIZATION_IMPLEMENTATION_GATE_REPORT.md)。

---

**END OF AUTHORIZATION IMPLEMENTATION CONTRACT（2026-09-23）**

> `IMPLEMENTATION CONTRACT = PASSED` · `IMPLEMENTATION = NOT AUTHORIZED`
