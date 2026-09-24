# UAP STAGE 2 — AUTHORIZATION / ACL / POLICY

## DECISION RESOLUTION PACKAGE

| 字段 | 内容 |
|---|---|
| **阶段** | `STAGE 2 — AUTHORIZATION / ACL / POLICY · DECISION RESOLUTION ROUND` |
| **日期** | 2026-09-23 |
| **基线 HEAD** | `eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6` |
| **基线 TAG** | `UAP-V0.1.7-GOVERNANCE-GATE`（→ 同一 commit） |
| **Alembic head** | `0011_p09_agent_tool_permission`（单头 · branches none · 0012+ absent） |
| **配套** | [`AUTHORIZATION_PREP_REPORT.md`](./AUTHORIZATION_PREP_REPORT.md) · [`AUTHORIZATION_ACCEPTANCE_MATRIX.md`](./AUTHORIZATION_ACCEPTANCE_MATRIX.md) |

---

## 0. 本文档的状态

```text
本文档 = DECISION RESOLUTION PACKAGE  →  已获 Human Decision Freeze
STATUS = FROZEN（19 项 OQ） + DEFERRED（3 项 OQ）     ← OQ 序列口径
FULL REGISTRY = D-AUTH total 25 → FROZEN 22 + DEFERRED 3 + SUPERSEDED 0   ← 含非 OQ 的 D-AUTH-23（GAP-11）· **D-AUTH-24/25**（D-B14-08 冲突裁定，2026-09-24）；**平台级 supersession = 1**（`D-B14-08` → `D-AUTH-05`）
```

### 0.1 HUMAN DECISION FREEZE（2026-09-23）

Human 已于 **2026-09-23** 对本文件 §3 的全部 **22 项 OQ** 给出**逐项明确裁定**，
并授权写入 [`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md)（`D-AUTH-01`…`D-AUTH-22`，OQ 序列；
另有非 OQ 的 `D-AUTH-23`（GAP-11）与 `D-AUTH-24` / `D-AUTH-25`（D-B14-08 冲突裁定，2026-09-24）见 §0.1 补注）。

```text
OQ SEQUENCE ONLY（本节及下表的口径）
OQ total = 22    OQ FROZEN = 19    OQ DEFERRED = 3    OQ SUPERSEDED = 0
```

> ⚠ **口径限定（2026-09-23 补注）**：本节 `19 FROZEN + 3 DEFERRED` 与 `D-AUTH-01…D-AUTH-22`
> **仅覆盖 `OQ` 序列**（`OQ-A01`…`OQ-A22`），**不**等于完整 Decision Registry。
> **完整 registry** 另含一条非 OQ 决策 **`D-AUTH-23`**（来源 `GAP-11`）：

```text
FULL DECISION REGISTRY（完整口径）
D-AUTH total = 23    FROZEN = 20    DEFERRED = 3    SUPERSEDED = 0
其中：22 项 OQ（19 FROZEN + 3 DEFERRED） + 1 项 GAP-11 专项（D-AUTH-23，FROZEN）
```

> **`D-AUTH-23` 规范表述**：`agent_permissions.resource_scope` = **OPAQUE TEXT** · **NOT AUTHORIZATION AUTHORITY** ·
> `ND-A = RESOLVED`（**不追加** `<> ''`）· `P09` / `0011` **unchanged**。

| OQ | 决策 ID | 状态 | Owner Phase（DEFERRED） |
|---|---|---|---|
| A01 | `D-AUTH-01` | **FROZEN** | — |
| A02 | `D-AUTH-02` | **FROZEN** | — |
| A03 | `D-AUTH-03` | `DEFERRED` | **Agent Runtime** |
| A04 | `D-AUTH-04` | **FROZEN** | — |
| A05 | `D-AUTH-05` | **FROZEN** | — |
| A06 | `D-AUTH-06` | **FROZEN** | — |
| A07 | `D-AUTH-07` | **FROZEN** | — |
| A08 | `D-AUTH-08` | **FROZEN** | — |
| A09 | `D-AUTH-09` | **FROZEN** | — |
| A10 | `D-AUTH-10` | **FROZEN** | — |
| A11 | `D-AUTH-11` | **FROZEN** | persistence → Tool Runtime |
| A12 | `D-AUTH-12` | **FROZEN** | — |
| A13 | `D-AUTH-13` | `DEFERRED` | **Tool Runtime** |
| A14 | `D-AUTH-14` | **FROZEN** | — |
| A15 | `D-AUTH-15` | **FROZEN** | persistence → P10 |
| A16 | `D-AUTH-16` | **FROZEN** | — |
| A17 | `D-AUTH-17` | **FROZEN** | — |
| A18 | `D-AUTH-18` | **FROZEN** | — |
| A19 | `D-AUTH-19` | **FROZEN** | — |
| A20 | `D-AUTH-20` | **FROZEN** | — |
| A21 | `D-AUTH-21` | `DEFERRED` | **Agent Runtime** |
| A22 | `D-AUTH-22` | **FROZEN** | persistence → P10 |
| —（`GAP-11`） | `D-AUTH-23` | **FROZEN** | — （**非 OQ**；`agent_permissions.resource_scope` = Legacy Opaque） |

> 逐项决策正文已写入 `PLATFORM_DECISION_LOG.md` 的 `D-AUTH-01`…`D-AUTH-23`；
> 本文件 §3 保留 **PREP 阶段的证据与选项分析**（含 Human 裁定所依据的原始 Current Evidence），
> 其 `HUMAN DECISION` / `STATUS` 字段已按上表统一更新。
> **`DEFERRED` 三项均已带 Owner Phase 与 Exit Condition**，不存在 `TBD`。
> **口径提醒**：本表 22 行属 `OQ` 序列；`D-AUTH-23` 为 `GAP-11` 专项（非 OQ），一并列出以保持 registry 完整。

---

## 0.2 本轮的原始依据（历史留存）

本轮 Human 指令 §25 原文为
> 「Bot 可以给出专业推荐，但**不得代替 Human**。」
> 「注意：以上全部只是 **RECOMMENDED DIRECTION**，**不得写成 FROZEN，除非 Human 明确批准**。」

且 §29 规定「**仅当 Human 明确决定后**，`PLATFORM_DECISION_LOG.md` 才允许写 `FROZEN`」，
§35 将「**No silent decision**」列为退出条件。

⇒ 在本文件**首次产出时**（2026-09-23 稍早），Human **尚未给出**逐项决定，
故当时一律未写 FROZEN、未改 Decision Log，并附「冻结请求包」（原 §7）供 Human 一次批准。
**该请求已于 2026-09-23 获 Human 明确批准**（见 §0.1），本文件随之更新为 `FROZEN` / `DEFERRED`。

---

## 1. §30 / §31 保护面核验（只读实测）

```text
HEAD                             = eb6d4cba71d4b69dc3604d860b9ab37ee8661cd6（未推动）
TAG                              = UAP-V0.1.7-GOVERNANCE-GATE → 同一 commit ✓
worktree                         = 2 untracked（上一轮 PREP 产物）· 0 modified · 0 staged
0010 sha256                      = 6d9907237f80e9da…（未变）
0011 sha256                      = cdaf8383630335db…（未变）
Alembic head                     = 0011_p09_agent_tool_permission（单一）· branches none · 0012+ = 0
migration diff                   = 0
PLATFORM_DECISION_LOG.md         = mtime 2026-09-23 20:33（早于本轮，未写入）· 最高编号 D-PLAT-17
```

**§30 既有冻结决策在位核验**（逐项 grep，全部仍在原始文档中，未被本轮的 PREP 文档覆盖）：

| 冻结项 | 原文出处（仍在位） |
|---|---|
| `R2-D-14`（DENY > ALLOW） | `STEP1B_ACL_STRATEGY.md` · `STEP1B_B1_3_DECISION_LOG.md` · `B1-4_*` |
| `R2-D-15`（permission scope-neutral） | `STEP1B_ACL_STRATEGY.md` · `STEP1B_B1_3_SCHEMA_REVIEW.md` |
| `effective_platform_admin`（R4/PMB-1） | `STEP1B_ACL_STRATEGY.md` · `STEP1B_B1_3_DECISION_LOG.md` |
| `acl_subject_types = user\|role\|agent` | `ER_MODEL.md` · `CORE_DOMAIN_MODEL.md` · `B1-4_DECISION_LOG.md` |
| P09 frozen schema | `P09_DECISION_LOG.md` · 0011 sha256 未变 |

⇒ 无任何既有冻结决策被无声覆盖。§30 若有需要变更之处，一律以 **OPEN SUPERSESSION QUESTION** 形式提出（见 §3 · D4）。

---

## 2. §26 DECISION GROUPING（22/22 覆盖检查）

```text
D1 Subject              → A02 A03 A18        (3)
D2 Resource             → A04                (1)
D3 Action / Scope       → A05 A06 A08        (3)
D4 Permission/ACL/Policy→ A01 A07 A20        (3)
D5 Agent / Tool         → A09 A19            (2)
D6 Risk / Approval      → A10 A11            (2)
D7 Runtime Semantics    → A12 A13 A14 A16    (4)
D8 Audit / P10          → A15 A21 A22        (3)
D9 Schema               → A17                (1)
                        ─────────────────────
                        合计 22 / 22  ✓ 无遗漏、无重复
```

---

## 3. OQ 逐项决议（§24 格式）

> 每项含 §24 要求的全部字段。`RECOMMENDED DIRECTION` 为工程建议，**不构成授权**；
> `HUMAN DECISION = APPROVED`（2026-09-23）· `STATUS` 见 §0.1（**OQ 口径** 19 `FROZEN` / 3 `DEFERRED`）。

---

### D1 — SUBJECT

---

#### OQ-A18 — Canonical Subject Vocabulary

| 字段 | 内容 |
|---|---|
| **Question** | 三套词汇（`IDENTITY_KINDS` / `identities.provider` / `acl_subject_types`）如何收敛？Authorization Subject 与 Identity 是否同一概念？ |
| **Current Evidence** | `core/identity/interfaces.py`: `IDENTITY_KINDS = ("user","service","device_subject")`；DB `identities.provider CHECK IN (local,oidc,saml,device,service)`；DB `acl_subject_types` 硬白名单 `CHECK (key IN ('user','role','agent'))` + `tg_acl_subject_types_protect`。三者交集：仅 `user`/`service` 部分重合；`agent` 仅在 ACL；`device_subject`/`role` 各自孤立。 |
| **Option A** | 维持三套（各层各自词汇）：零迁移、零防线变更 |
| **Option B** | 单一"Subject Vocabulary"：ACL 与 Identity 共用一套枚举 |
| **Option C** | 显式分离：`Identity`（认证层）与 `Authorization Subject`（授权层）为两个正交概念，各自词汇独立且**文档化映射** |
| **Engineering Consequences** | A：最小改动，但语义漂移风险高（Agent 的 identity 载体永远缺位）。C：需新增一份映射契约（无 schema 变更）。B：需改 `acl_subject_types` 白名单 CHECK —— **该表受 protect trigger 保护且 CHECK 硬编码**，属破坏性变更 |
| **Security Consequences** | A/B 需重新证明 `enforce_acl_subject_exists()` 的 subject 存在性链；C 保持既有防线完全不变 |
| **Migration Consequences** | A：0。C：0。B：需新 migration 重建 CHECK（**不得改写 0007**） |
| **Agent Runtime Consequences** | C 是唯一能回答「Agent 的 identity 是什么」的选项：Agent 的 authorization subject = `agents.id`，不要求 Agent 拥有 `identities` 行 |
| **Module Consequences** | C 让 Module 只需面向 Authorization Subject 声明，无需了解认证提供方 |
| **Recommended Direction** | **Option C** —— `Canonical Subject Types = {USER, ROLE, AGENT}`（授权域）；`Identity Provider = {local, oidc, saml, device, service}`（认证域）；二者**正交**，Authorization Subject ≠ Provider。`IDENTITY_KINDS` 的 `device_subject` 与 `service` 保留为认证/身份域词汇，不进授权域 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A02 — Agent 是否为独立 Authorization Subject

| 字段 | 内容 |
|---|---|
| **Question** | Agent = independent authorization subject，还是 User 的纯执行配置？二者可否并存？ |
| **Current Evidence** | `acl_subject_types` 白名单**已允许 `agent`**；`agent_permissions`（`effect`/`resource_scope`/`conditions`）已落库；`agents.max_risk_level` 已落库；`agents.owner_id NOT NULL → users(RESTRICT)`。契约层 `core/permission.Subject(identity_id, role_keys, scopes)` **无 agent 字段**。 |
| **Option A** | Agent = User 的纯执行配置（仅 user 为主体）—— 与 `acl_subject_types` 已允许 `agent` **直接冲突** |
| **Option B** | Agent = independent subject（自身持授权边界） |
| **Option C** | B + 显式 delegation 上下文（由 OQ-A03 定义） |
| **Engineering Consequences** | A 需移除 `agent` 白名单项 ⇒ 破坏性、不可能。B/C 均可复用现成表结构 |
| **Security Consequences** | B 必须额外约束"agent 权限不得超出其 owner 有效授权"（否则构成提权面）；C 把该约束显式化 |
| **Migration Consequences** | A：破坏性（禁止）。B/C：**0**（`agents`/`agent_permissions` 已足够） |
| **Agent Runtime Consequences** | B/C 才能表达"Agent 作为主体被授权"；A 下 `agent_permissions` 成为死表 |
| **Module Consequences** | B/C 允许 Module 面向 Agent 授权 |
| **Recommended Direction** | **Option C** —— Agent 为**独立 Subject**；同时始终携带 delegation context（OQ-A03） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A03 — User / Agent Delegation Semantics

| 字段 | 内容 |
|---|---|
| **Question** | `effective_subject` / `delegator` / `actor` / `agent` 的语义？Agent 能否超过 User 权限？Delegation 默认还是显式？如何撤销？是否审计？ |
| **Current Evidence** | `tool_executions` **同时有 `agent_id`（NULL 允许）与 `actor_id`（NULL 允许）**；`agent/runtime.AgentInput.actor_id`；`core/policy.PolicyContext` **只有单一 `actor_id`**（无法表达双主体）；§14 原则「Agent 不得通过代理调用获得超过其授权边界的有效权限」。 |
| **Option A** | Agent 权限独立（可超越 User）—— **违反 §14 原则** |
| **Option B** | Agent 完全使用 User 权限（无独立边界）—— 与 `agent_permissions` 已落库冲突 |
| **Option C** | `Effective = Agent 独立权限 ∩ User effective authority` |
| **Option D** | `Agent 独立权限 + 显式 delegation scope`（显式授权可超出交集，但需 grant + 审批 + 审计） |
| **Engineering Consequences** | C 最保守；D 需 delegation 载体（**当前不存在**，属 schema 影响 OQ-A17） |
| **Security Consequences** | **A 必须排除**（直接违反 §14 与 §35「Agent permission can exceed user boundary」HARD STOP 条件）。C 零提权面。D 引入受控提权通道，必须审计 |
| **Migration Consequences** | A/B/C：0 新表（C 可纯计算）。D：需 delegation 表或列 |
| **Agent Runtime Consequences** | C 可直接实施；D 需先定 delegation 载体 |
| **Module Consequences** | 无直接差异 |
| **Recommended Direction** | **C 为默认**（零 schema 变更、零提权面）；**D 仅作为未来显式审批的例外通道**，并置为 DEFERRED（owner = Agent Runtime，phase = 待 delegation 载体获批）。四问的推荐答案：**能否超过 = 否（默认）**；**是否默认 = 否（不默认委托）**；**是否需显式 grant = 是（若采用 D）**；**如何撤销 = 实时校验 `actor.status` / membership / `agent_versions.status='revoked'`**；**是否审计 = 是（依赖 OQ-A15/P10）** |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D2 — RESOURCE

---

#### OQ-A04 — Resource Canonical Model

| 字段 | 内容 |
|---|---|
| **Question** | Resource canonical 形状？是否引入 `parent`？Owner 能否是 Agent / Role？ |
| **Current Evidence** | `resources`: `id` · `tenant_id`(NN) · `space_id` · `owner_id`→**users** · `resource_type`(正则) · `natural_key` · `classification`(四档) · `status` · `metadata` · `archived_at`/`deleted_at`。**无 parent 列**；`resource_relations` **在 0011 不存在**。8 项要求中 7 项已具备。 |
| **Option A** | 保持现状（无层级；owner 仅 User） |
| **Option B** | 新增 `resources.parent_id`（自引用 FK） |
| **Option C** | 新增通用 `resource_relations` 表 |
| **Engineering Consequences** | A：0 变更、零风险。B/C：需新 migration + 层级解析逻辑 + 环检测 |
| **Security Consequences** | B/C 引入继承路径 ⇒ 必须重新证明「继承不产生跨 tenant/space 逃逸」与「环不导致无限授权」。A 无此风险 |
| **Migration Consequences** | A：0。B/C：新列/新表（需 Human 单独授权，**不得创建 0012**） |
| **Agent Runtime Consequences** | 当前无已证实的层级需求；A 不阻塞 Agent Runtime |
| **Module Consequences** | Module 可用 `natural_key` + `resource_type` 表达归属，无需 parent |
| **Recommended Direction** | **Option A（本阶段）** —— 保持 8 属性现状；**owner 仅允许 USER**（与既有 FK 一致，不变更）；Agent 对资源的关系用 **ACL 行**（`acl_subject_types` 已允许 `agent`）表达，而非 owner 字段。B/C 列为 `DEFERRED`（owner = Authorization Implementation，phase = 出现真实层级用例时）。 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D3 — ACTION / SCOPE

---

#### OQ-A05 — Canonical Action Vocabulary

| 字段 | 内容 |
|---|---|
| **Question** | 是否冻结全平台 Action 词表？Tool Action 是否等同 Resource Action？Module 能否自定义？ |
| **Current Evidence** | `permissions.action` **自由 text（无 CHECK）**；`permissions.resource_type` **NULL 允许**；`resource_permissions.action` **自由 text（无 CHECK）**；契约 `Action(name, resource_type)` 无枚举。⇒ 三处均无强制（C-6）。 |
| **Option A** | 不冻结（保持自由 text） |
| **Option B** | 冻结平台词表 + DB CHECK + 契约枚举 |
| **Option C** | 冻结词表但仅契约层强制（DB 不校验） |
| **Engineering Consequences** | B 提供最强静态可验证性；C 保留 DB 灵活性但允许脏数据入库 |
| **Security Consequences** | A/C 下"拼写变体绕过授权"成为可能（如 `delete` vs `DELETE` vs `Delete`）。B 结构性消除该类绕过 |
| **Migration Consequences** | B 需为两张已落库表加 CHECK。**当前 seed = 0（P00–P12 无 seed）** ⇒ 存量越界值风险极低，但**仍属对已发布表加约束，须新 migration 且单独授权** |
| **Agent Runtime Consequences** | B 使 Agent 可被静态校验"只允许动作集" |
| **Module Consequences** | 需配一个**受控 registry**（Module 声明额外动作须注册，不得自由产生不可审计字符串） |
| **Recommended Direction** | **Option B**，词汇表 = `READ LIST CREATE UPDATE DELETE EXECUTE APPROVE REJECT PUBLISH EXPORT SHARE ADMIN`（~~大写规范化~~ → **2026-09-24 `D-AUTH-25`：canonical 存储形 = 小写**；入站 NFKC + casefold 归一）。**明确**：`EXECUTE` **独立于** `READ`（§11 要求）；`APPROVE`/`REJECT` **独立**（§19）；`EXPORT` **独立**（外泄风险）；Tool Action 与 Resource Action **同一词表**（不设第二套）。Module 扩展动作须入 registry（registry 载体属 OQ-A17） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A06 — Scope Hierarchy

| 字段 | 内容 |
|---|---|
| **Question** | 是否引入 `RESOURCE` / `SELF`？`SELF` 是 Scope 还是 Context predicate？ |
| **Current Evidence** | DB 已强制 `roles.scope IN (PLATFORM, TENANT, SPACE)` + `tg_roles_scope_shape` + 3 个部分唯一索引。`ResourceScope(tenant_id, space_id?)` 无 PLATFORM。`resource_permissions.inherited` 存在但无 parent。**`SELF` 无任何承载**。 |
| **Option A** | 维持 3 层；`SELF` = **Context predicate**（`resource.owner_id = subject.id`），非 scope |
| **Option B** | 引入 `RESOURCE` 为第 4 个正式 scope |
| **Option C** | 引入 `RESOURCE` + `SELF` 两个新 scope |
| **Engineering Consequences** | A：0 变更。B/C：需改 `ck_roles_scope`（**已发布表约束，破坏性，须新 migration**） |
| **Security Consequences** | A 下 `SELF` 为纯判定谓词，不产生新的授权继承路径 ⇒ 无新增逃逸面。B/C 新增 scope 需重新证明层级不越租户 |
| **Migration Consequences** | A：0。B/C：新 migration（不得改 0005） |
| **Agent Runtime Consequences** | A 已足够（"仅本人资源"可用 owner 谓词表达） |
| **Module Consequences** | A 不限制 Module（Module 用 resource + action + owner 即可） |
| **Recommended Direction** | **Option A** —— 继承链冻结为 `PLATFORM → TENANT → SPACE → RESOURCE`（**RESOURCE 为资源实例层，不是 role scope**；`resource_permissions` 即该层的授权载体）；**`SELF` 明确为 Context predicate，不是 Scope**（避免与 §8 要求的混淆） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A08 — Permission Inheritance

| 字段 | 内容 |
|---|---|
| **Question** | `Tenant→Space→Resource` 与 `Role→User effective` 的 Inheritance / Override / Explicit Deny / Revocation？ |
| **Current Evidence** | `roles` 三层（部分唯一索引 + shape trigger）已定；`resource_permissions.inherited` 存在但**无 parent（OQ-A04）**；`resource_permissions.expires_at` 支持时间过期；`platform_memberships.revoked_at`；`memberships.status`；`STEP1B_ACL_STRATEGY §5` 已定 role 归档/agent 归档/user 硬删的 cleanup 语义。 |
| **Option A** | **角色层继承 only**（resource 层不继承）：`Role → User effective` 单向；资源层仅实例 ACL |
| **Option B** | 双层继承（resource 亦继承自 parent）—— 依赖 OQ-A04 的 parent |
| **Engineering Consequences** | A 与现有 schema 完全吻合、可判定；B 依赖尚不存在的 parent |
| **Security Consequences** | A 的继承面最小，易证明；B 需证明层级不越租户 |
| **Migration Consequences** | A：0。B：随 OQ-A04 |
| **Agent Runtime Consequences** | A 足够 |
| **Module Consequences** | A 足够 |
| **Recommended Direction** | **Option A** + 明确四条规则：① **Inheritance** = `Role(scope) → Membership → User effective`，加上 `PLATFORM → TENANT → SPACE` 的作用域包含；② **Override** = ACL 对具体资源可覆盖 RBAC 基线（方向见 OQ-A07）；③ **Explicit Deny** = 任一层的 deny 在最终合并中胜出；④ **Revocation** = `revoked_at` / `status` / `archived_at` / `expires_at` 实时校验，**不预先清理 ACL**（沿用 `STEP1B_ACL_STRATEGY §5`） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D4 — PERMISSION / ACL / POLICY

---

#### OQ-A01 — Canonical Composition（RBAC / ACL / Policy）

| 字段 | 内容 |
|---|---|
| **Question** | 最终组合：A（RBAC only）/ B（RBAC+ACL）/ C（RBAC+Policy）/ D（RBAC+ACL+Policy）？ |
| **Current Evidence** | RBAC 与 ACL 的**全部表已落库**（0005/0006/0007）；`role_permissions.conditions` 已存在但 `R2-D-15` 定为 **storage-only**；`core/permission` 与 `core/policy` 的 Owns 描述**已重叠**（前者含 ABAC，后者含 Policy Evaluation）。 |
| **Option A** | RBAC only —— 需废弃 `resources`/`resource_permissions`/`acl_subject_types`（**破坏性，禁止**） |
| **Option B** | RBAC + ACL —— 与现 schema **完全吻合**，0 新表，`conditions` 维持 storage-only |
| **Option C** | RBAC + Policy —— 需废弃 ACL 资产（**破坏性，禁止**） |
| **Option D** | RBAC + ACL + Policy —— 完整三层；需把 `conditions` 升级为可解析，并解决 C-2/C-5 |
| **Engineering Consequences** | B 是 D 的严格子集，可作为分阶段落地形态。D 需额外的策略载体（OQ-A17） |
| **Security Consequences** | B 确定性最强、最容易证明；D 必须强制"策略只能收紧"（策略不得放宽静态授予），否则引入提权面 |
| **Migration Consequences** | A/C：破坏性（禁止）。B：**0**。D：可能新增策略载体（需授权） |
| **Agent Runtime Consequences** | 仅 D 能满足 §42 目标链路（`… → Policy → Approval if required → Tool → …`） |
| **Module Consequences** | 仅 D 能满足 §28「模块只声明 Resource/Action/Policy」 |
| **Recommended Direction** | **Option D 为终态**，**明确以 B 作为可分阶段交付的中间形态**；职责划分冻结为 **RBAC = baseline grant / ACL = resource-specific grant / Policy = contextual decision**。`conditions` 的归属必须单一：**归 `core/policy`，`core/permission` 只做 RBAC+ACL 合并**（消除现存职责重叠） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A07 — Allow / Deny Precedence

| 字段 | 内容 |
|---|---|
| **Question** | `Role ALLOW + ACL DENY + Policy ALLOW` 的最终结果？如何保证 deterministic / order-independent / auditable？ |
| **Current Evidence** | **`R2-D-14`（FROZEN SECURITY INVARIANT）：DENY > ALLOW** —— 同 `(role,permission)` 并存 allow+deny ⇒ DENY；多角色任一 deny ⇒ DENY；由 Authorization Layer 解释，**DB 不做授权解释**。`ER_MODEL.md:221`：「`resource_permissions` 是显式 ACL，**deny 优先于 RBAC 继承来的 allow**」。`core/policy.combine()`：「Any denial wins」。 |
| **Option A** | **Deny overrides allow**（正式继承 `R2-D-14`，并扩展到跨层） |
| **Option B** | Specific overrides general（ACL 优先于 RBAC，policy 优先于静态） |
| **Option C** | 混合：先比 specificity，再在同等 specificity 内 deny 优先 |
| **Engineering Consequences** | A 最简单、最易证明；C 语义最强但需定义 specificity 序且复杂度显著上升 |
| **Security Consequences** | A 最保守。B 单独使用时可能被"具体 allow"绕过"一般 deny" ⇒ 不安全。C 需严格证明 specificity 偏序无歧义 |
| **Migration Consequences** | 三者皆 **0**（纯决策层语义） |
| **Agent Runtime Consequences** | A 使 Agent 的拒绝面最大，最安全 |
| **Module Consequences** | Module 无法通过"更具体的 allow"绕过平台 deny ⇒ 符合 §42 |
| **Recommended Direction** | **Option A** —— 正式继承并**跨层统一**为单一算法：`DENY > ALLOW`，且 **Policy 的 deny 与 ACL 的 deny 与 RBAC 的 deny 效力等同**（不设层级特权）。同时冻结三项性质：**deterministic**（同输入同输出）· **order-independent**（规则顺序无关）· **auditable**（可解释命中来源）。**注**：`R2-D-14` 为既有 FROZEN，本项**不是新决策**，而是**确认继承 + 扩展到跨层**；若需变更须走 OPEN SUPERSESSION QUESTION |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A20 — `resource_permissions` UNIQUE 不含 `effect`

| 字段 | 内容 |
|---|---|
| **Question** | 现有 `UNIQUE(resource_id, subject_type_id, subject_id, action)` **不含 `effect`** ⇒ 同一 (资源,主体,动作) **不可能并存 allow 与 deny**。与 `R2-D-14` / `ER_MODEL:221` 是否相容？ |
| **Current Evidence** | 0011 实测唯一约束原文；对照 `role_permissions` 的 **PK 含 effect**（允许并存）。`STEP1B_ACL_STRATEGY §5` 已定义 role 归档时"deny 行不再参与、allow 行保留"。 |
| **Option A** | **保持**（ACL 层每元组单行；改判 = 行替换 + 同事务审计） |
| **Option B** | 将 `effect` 纳入 UQ（允许并存，由决策层解释） |
| **Option C** | 引入 tombstone deny（软删除式显式拒绝） |
| **Engineering Consequences** | A：0 变更，语义清晰（"ACL 层不并存"）。B：需**重建唯一约束**（新 migration，触及已发布表 0007）。C：最复杂 |
| **Security Consequences** | **关键分析**：跨层 `DENY > ALLOW`（ACL deny 覆盖 RBAC allow）在 **A 下完全可行** —— 因为 RBAC allow 来自 `role_permissions`（另一张表），与 ACL 行不构成 UNIQUE 冲突。**层内**并存需求未被证实。A 无安全缺口 |
| **Migration Consequences** | A：0。B：重建约束（须授权、不得改 0007 文件本身，须新 migration） |
| **Agent Runtime Consequences** | A 下 Agent 的资源级改判走 UPDATE，需保留审计（`STEP1B_ACL_STRATEGY §6` 已要求同事务审计） |
| **Module Consequences** | A 要求 Module 理解"改判 = 替换 + 审计" |
| **Recommended Direction** | **Option A（保持现状，0 schema 变更）**，并**显式文档化**该语义：「ACL 层每 (resource, subject, action) 唯一；改判即行替换，替换必须同事务写审计；跨层 deny 优先由决策层统一实现」。理由：跨层 DENY>ALLOW 不依赖层内并存；层内并存需求未获证据支持；变更已冻结表风险的边际收益不足 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D5 — AGENT / TOOL

---

#### OQ-A09 — Tool Authorization Model

| 字段 | 内容 |
|---|---|
| **Question** | `Tool Permission` vs `Resource Permission` vs `Policy` 的关系？如何表达 `Agent → Tool → Action → Resource → Scope → Policy`？ |
| **Current Evidence** | `tool_permissions(tool_id, version_id, permission_id, effect, conditions)` —— **无 resource/action/scope 列**；`agent_permissions.resource_scope` 为**无 FK、无格式约束的自由 text**；`agent_versions.allowed_tools`(jsonb)；`agent/tools` 契约：「A tool is the only path from an agent to a service」；`Tool.invoke(params, context)` **不携带授权决策**。 |
| **Option A** | 工具只声明 `permission_id`（现状） |
| **Option B** | 工具声明结构化四元组 `(permission, resource_type, action, scope)` |
| **Option C** | 工具引用外部策略对象 |
| **Engineering Consequences** | A 无法静态验证"工具声明"与"实际访问"一致；B 可静态校验；C 最灵活但引入第二套策略载体 |
| **Security Consequences** | A 下"工具声称需要 X 权限但实际访问 Y 资源"**无法被静态发现** ⇒ 存在权限旁路面（§12 明令禁止 Tool bypass）。B 结构性收窄该面。**且必须在执行前强制携带授权决策**（现状 `Tool.invoke` 不带 ⇒ 需扩契约） |
| **Migration Consequences** | B 需为 `tool_permissions` 增列（**触及 P09 相关领域，须 Human 授权；不得改 0011**）。C 需新表 |
| **Agent Runtime Consequences** | B 使 Tool Selection 阶段即可静态过滤（§27 中"Tool Selection 不能安全实现"得以解除） |
| **Module Consequences** | Module 注册工具时必须声明结构化权限 ⇒ 可静态审计 |
| **Recommended Direction** | **Option B** —— 工具声明结构化四元组；**并明确分层职责**：`Tool Permission` = 工具**固有**所需能力；`Resource Permission`（ACL）= 对**具体资源实例**的授权；`Policy` = **上下文条件**（金额/时间/环境）。三者**不得**互相替代。契约侧扩为 `Tool.invoke(params, context, decision)` 或在 context 内强制携带决策句柄 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A19 — Agent Version Semantics

| 字段 | 内容 |
|---|---|
| **Question** | `version number` vs `version identifier` 的职责？str/int 冲突如何解？ |
| **Current Evidence** | `agent/registry/interfaces.py`: `AgentDescriptor.version: str = "0.1.0"`；DB `agent_versions.version integer NOT NULL`；DB 另有 `uq_agent_versions` 唯一约束与 `checksum`；`agent_versions.status(draft/published/deprecated/revoked)`；`agents.current_version_id` → `agent_versions.id`（**版本以 ID 引用，而非 version 号**）。 |
| **Option A** | 契约改为 `int`（对齐 DB revision） |
| **Option B** | 契约保留语义化字符串，DB 增列 |
| **Option C** | `opaque version ID`（=`agent_versions.id`）+ 独立 display version |
| **Engineering Consequences** | C 与现有 `current_version_id` 设计**最一致**；A 改动最小；B 需新列 |
| **Security Consequences** | 版本识别必须**不可变且可校验**（`checksum` 已在位）；A/B/C 均不影响该性质 |
| **Migration Consequences** | A：0（只改契约）。B：新列。C：0（复用 `id`） |
| **Agent Runtime Consequences** | **从 immutable version / deployment 需求反推**（§20 要求）：部署与回滚以**不可变版本身份**为准 ⇒ C 最贴合；`version`(int) 作为单调 revision，`checksum` 作为内容身份 |
| **Module Consequences** | Module 以版本 ID 引用 Agent，无需解析版本号语义 |
| **Recommended Direction** | **Option C** —— 三层职责分离：① **revision** = `agent_versions.version`(int，单调，DB 已定)；② **identity** = `agent_versions.id`（不可变引用，已被 `agents.current_version_id` 采用）；③ **display** = 语义化字符串（如需，属展示层，**不参与授权判定**）。契约 `AgentDescriptor.version: str` 应改为 **version id 或显式命名 `version_id`**，避免与 int revision 混淆 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D6 — RISK / APPROVAL

---

#### OQ-A10 — Canonical Risk Model

| 字段 | 内容 |
|---|---|
| **Question** | 四档 enum / numeric score / classification+score？Risk 属于 authorization、policy 还是 execution？ |
| **Current Evidence** | DB **三处**四档：`ck_tools_risk_level` · `ck_agents_max_risk_level` · `tool_executions.risk_level` 均为 `LOW/MEDIUM/HIGH/CRITICAL`；契约 `core/policy.RiskPolicy.score() -> float [0.0, 1.0]`（C-2）。`resources.classification` 另有四档（PUBLIC/INTERNAL/CONFIDENTIAL/HIGHLY_CONFIDENTIAL）。 |
| **Option A** | 四档枚举（对齐 DB 与 §18/§13） |
| **Option B** | numeric score（对齐契约）—— 需改三张表的 CHECK（**破坏性**） |
| **Option C** | classification + score 双轨（score → 确定性映射到四档） |
| **Engineering Consequences** | A 最简且与 DB 一致；C 保留打分能力但必须定义**确定性映射**与阈值 |
| **Security Consequences** | 若 score 与四档无确定映射，则"同一动作在不同代码路径得到不同风险档" ⇒ 破坏确定性。C 必须冻结映射表 |
| **Migration Consequences** | A：**0**（仅改契约 1 处）。B：破坏性。C：0（映射在契约层） |
| **Agent Runtime Consequences** | A 足以支撑 `agents.max_risk_level` 与工具风险交叉校验 |
| **Module Consequences** | Module 只需使用四档 |
| **Recommended Direction** | **Option A（四档 canonical）**，并把 `RiskPolicy.score()` 降级为**可选辅助**：`score` 用于排序/提示，**授权判定只使用四档枚举**。**职责分离**（§13 要求）：`Risk` **不是 authorization 本体** —— 它是**policy 的输入**与 **execution 的属性**（`tool_executions.risk_level` 记录事实），**不得与 permission 混为一体** |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A11 — Canonical Approval Model

| 字段 | 内容 |
|---|---|
| **Question** | `tools.approval_required`（静态）与 dynamic policy approval 的关系？ |
| **Current Evidence** | DB `tools.approval_required boolean NOT NULL`（**已落库**）；`tool_versions` 亦有独立字段组；`core/permission.Decision` 仅 `allowed: bool`；`agent/runtime.AgentRunResult.status ∈ (completed, denied, failed)`；`tool_executions.status ∈ (running, succeeded, failed, denied, timeout)` —— **三处均无"待审批"态**。 |
| **Option A** | 保持静态工具级 flag |
| **Option B** | 纯动态策略驱动 |
| **Option C** | **静态 flag = 工具固有下限；动态 policy = 上下文追加；`approval_required = static OR policy`** |
| **Engineering Consequences** | C 零 schema 变更（静态侧已存在），仅需 policy 侧补足；A 无法覆盖 §19 高价值/跨空间场景；B 丢弃已落库静态字段 |
| **Security Consequences** | C 保证"只能加严不能放宽" ⇒ 安全；B 若策略缺失则审批被静默跳过 ⇒ 不安全 |
| **Migration Consequences** | C：**0**（`approval_required` 已在位）。B：需废弃该列（破坏性） |
| **Agent Runtime Consequences** | C 使 Agent 在 Tool Selection 阶段即可预判审批需求；但 **`REQUIRES_APPROVAL` 无状态承载**（见 OQ-A14） |
| **Module Consequences** | Module 通过工具静态声明 + 策略动态追加表达审批需求 |
| **Recommended Direction** | **Option C** —— `approval_required = tool.approval_required OR policy.requires_approval`（逻辑或；**永不做逻辑与**，因为 and 会削弱静态下限）。§19 六类高敏动作（Delete / Export / External Send / Financial / Permission Change / Cross-Space）全部**至少**落入静态或策略其一。**本阶段只设计，不实现审批系统**（§18 明令） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D7 — RUNTIME SEMANTICS

---

#### OQ-A12 — Failure Semantics

| 字段 | 内容 |
|---|---|
| **Question** | 8 类失败分支是否统一 FAIL CLOSED？ |
| **Current Evidence** | 多重冻结先例：`R3-D-07`/`R4`（平台级无 effective 权限 ⇒ DENY）· `R5`（user inactive ⇒ **永久 DENY**）· `core/permission.DENY` + `default_decision()` · `combine()` any-deny-wins · `core/permission` docstring「unknown roles/resources/evaluation errors all yield a denial」。**服务级不可用语义未定义**。 |
| **Option A** | 统一 FAIL CLOSED（全部 8 类 → DENY） |
| **Option B** | 分级降级（只读放行）—— **违反 §20** |
| **Option C** | 可配置 |
| **Engineering Consequences** | A 与全部既有先例一致；C 引入配置面 ⇒ 配置错误即安全事件 |
| **Security Consequences** | **B 必须排除**（§20 明令：不能因检查不到权限而默认允许）；亦被 §35 列为 HARD STOP 条件（"Authorization failure can default ALLOW"） |
| **Migration Consequences** | 0 |
| **Agent Runtime Consequences** | A 下 Agent 在授权服务故障时停止执行（安全但可用性低）—— 这是**有意为之** |
| **Module Consequences** | Module 无法以"降级"方式绕过 |
| **Recommended Direction** | **Option A** —— 8 类分支（Service unavailable / Policy unavailable / Permission lookup failure / Unknown Subject / Unknown Resource / Unknown Action / Expired grant / Revoked grant）**全部 FAIL CLOSED → DENY**；`DENY` 必须携带 `reason` 以区分"无权限"与"系统故障"（可观测性），但**结果一律 DENY** |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A13 — Cache Semantics

| 字段 | 内容 |
|---|---|
| **Question** | 决策能否缓存？缓存什么？TTL？失效？撤销后？是否禁止 fail-open？ |
| **Current Evidence** | **当前 0 授权缓存**。失效信号已落库：`roles.archived_at`/`status` · `memberships.status`/`removed_at` · `platform_memberships.revoked_at` · `resource_permissions.expires_at` · `users.status`/`deleted_at` · `agents.status` · `agent_versions.status`。**`events`（outbox）在 0011 不存在 ⇒ 事件驱动失效不可用**。 |
| **Option A** | 不缓存（首发） |
| **Option B** | 短 TTL + 显式失效 |
| **Option C** | 事件驱动失效（依赖 `events`，属 P10） |
| **Engineering Consequences** | A 零风险零复杂度；B 引入"stale allow 窗口"；C 依赖不存在的组件 |
| **Security Consequences** | **任何缓存都不得产生 stale allow**（§21）。A 结构性消除该风险。B 的 TTL 上限即最大安全窗口，必须冻结 |
| **Migration Consequences** | 0（缓存不落库） |
| **Agent Runtime Consequences** | A 下每次决策实时读库 ⇒ 延迟上升，但正确性无损 |
| **Module Consequences** | 无差异 |
| **Recommended Direction** | **Option A 首发**（不缓存），并冻结四条语义以备未来：① 决策**可**缓存（语义允许）；② 仅可缓存**完整决策三元组**（不可缓存部分结果）；③ 任何缓存**必须**在 `revoked_at`/`archived_at`/`expires_at`/`status` 变化时失效；④ **fail-open 绝对禁止**（缓存未命中/不可用 ⇒ 走 FAIL CLOSED）。B/C 置 `DEFERRED`（owner = Authorization Implementation，phase = P10 `events` 落地后） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A14 — Authorization Decision API Contract

| 字段 | 内容 |
|---|---|
| **Question** | Request/Context/Decision 形状？`REQUIRES_APPROVAL` 是终态还是中间态？ |
| **Current Evidence** | 现有 `Subject(identity_id, role_keys, scopes)` · `Action(name, resource_type)` · `ResourceRef(type, id, tenant_id, space_id, owner_identity_id)` · `Decision(allowed: bool, reason, matched_rules)`。§22 要求 `subject/action/resource/scope/context/decision/reason/policy_version`；§17 要求三值结果。**`REQUIRES_APPROVAL` 在三处契约中均无处安放**。 |
| **Option A** | 保持 `allowed: bool` |
| **Option B** | 三值枚举 `ALLOW / DENY / REQUIRES_APPROVAL` |
| **Option C** | 三值 + 独立 approval 对象 |
| **Engineering Consequences** | B 最小且满足 §22；C 携带更多审批上下文但增加耦合 |
| **Security Consequences** | **若 `REQUIRES_APPROVAL` 被当作"可继续"的中间态，则审批被绕过**。必须语义上视为**未授权**（fail closed 的第三种表现），只有审批流可将其转为 ALLOW |
| **Migration Consequences** | 0（纯契约） |
| **Agent Runtime Consequences** | Agent 必须在收到 `REQUIRES_APPROVAL` 时**暂停而非继续** |
| **Module Consequences** | Module 需处理三值而非两值 |
| **Recommended Direction** | **Option B** —— `Decision.effect ∈ {ALLOW, DENY, REQUIRES_APPROVAL}`，并补齐 §22 字段：`subject` · `delegator` · `action` · `resource` · `scope` · `context` · `decision` · `reason` · `policy_version`。**`REQUIRES_APPROVAL` 为终态语义**（对调用方等价于"现在不能执行"），**不得**被任何调用方当作允许。保留 `allowed` 为派生只读属性（`effect == ALLOW`）以兼容既有断言 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A16 — Authorization Service Placement

| 字段 | 内容 |
|---|---|
| **Question** | 授权决策在哪执行？数据在哪？谁拥有持久化？ |
| **Current Evidence** | `D-PLAT-02`（core = 契约与基础抽象，不承载持久化）· `D-PLAT-03`（services = 唯一业务持久化承载层）· `D-PLAT-05`（agent 不依赖 services 具体实现，经 Policy/Tool 契约进入）· G-1/G-2/G-3 硬门。`services/` 包**尚不存在**。现成契约面：`core/permission` `core/policy` `core/resource` `core/audit` `core/membership`。 |
| **Option A** | 新契约包 `core/authorization` + 实现 `services/authorization` |
| **Option B** | 复用既有 `core/permission` + `core/policy` 双契约；实现 `services/authorization/` |
| **Option C** | 实现置于 `infrastructure` —— **违反 G-1/D-PLAT-03** |
| **Engineering Consequences** | B 避免第三套契约（防止概念分裂）；A 更整齐但增加迁移成本 |
| **Security Consequences** | 三者均不改变安全性质；B 要求消除 `core/permission` 与 `core/policy` 的职责重叠（OQ-A01） |
| **Migration Consequences** | 0（纯代码组织） |
| **Agent Runtime Consequences** | agent 只能经 `core/policy` 契约触达（G-3 硬门），故契约必须放 `core` |
| **Module Consequences** | domains 经约定契约消费（`D-PLAT-06`） |
| **Recommended Direction** | **Option B** —— **Contract**：复用 `core/permission`（RBAC/ACL 合并）+ `core/policy`（条件/风险）+ `core/resource`（资源引用）+ `core/audit`（审计契约）；**Application service**：`services/authorization/`（决策编排、事务协调）；**Persistence adapter**：`services/` 内部经 `infrastructure` 访问 DB。**三者边界冻结**：core 无 I/O、services 无 HTTP、infrastructure 无业务规则 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D8 — AUDIT / P10

---

#### OQ-A15 — Audit Model & Dependency Classification

| 字段 | 内容 |
|---|---|
| **Question** | 授权决策审计需记录什么？`Authorization Decision` 与 `Tool Execution` 如何区分？审计持久化是实施前置吗？ |
| **Current Evidence** | `core/audit.AuditEvent(action, outcome, actor_id, tenant_id, space_id, target_type, target_id, metadata)` + `AUDIT_OUTCOMES=(success,denied,error)` —— **缺** `subject`/`delegator`/`decision`/`reason`/`policy`/`risk`/`approval`；**`events` 与 `audit_logs` 在 0011 均不存在**（属 P10）；`D-PLAT` 数据律规定 `audit_logs` 不可变。 |
| **Option A** | P10 前置（授权审计必须等 P10） |
| **Option B** | 授权实施可用**临时非持久审计契约**推进 |
| **Option C** | 授权在审计持久化就绪前不得视为 implementation-complete |
| **Engineering Consequences** | B 允许并行推进设计/契约；A 使授权实现完全阻塞；C 是 B 的"完成门"版本 |
| **Security Consequences** | 若决策不可审计，则无法事后取证。B 的"临时非持久"**不得**被当作生产可用 |
| **Migration Consequences** | **不得**因发现审计缺失而自行创建 `events`/`audit_logs`（§19 明令） |
| **Agent Runtime Consequences** | Agent 的每次都决策必须可追溯 |
| **Module Consequences** | Module 产生的授权决策同样需审计 |
| **Recommended Direction** | **Option B + C 组合**：① **Design dependency = 无**（契约现在即可冻结，`AuditEvent` 扩字段）；② **Implementation dependency = P10**（审计**持久化**依赖 `events`/`audit_logs`）；③ **Runtime dependency = P10**（运行期审计写入）；④ **Audit dependency 分类见 OQ-A21**。⇒ 授权**设计可继续**，但**不得**在审计持久化就绪前宣告 implementation-complete。**`Authorization Decision` ≠ `Tool Execution`**：前者记录"判定过程与结果"，后者记录"执行事实"，二者**必须是不同载体**（现 `tool_executions` 与未来 `audit_logs` 已分离） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A21 — P10 Dependency Classification（Memory / Workflow）

| 字段 | 内容 |
|---|---|
| **Question** | Audit / Event / Workflow authorization / Memory authorization 各属何种依赖？ |
| **Current Evidence** | `agent/memory/interfaces.py` `MemoryStore.read/write/delete` 与 `agent/workflow/interfaces.py` `WorkflowRunner.run(steps)` **零授权参数**（对比 `Tool.invoke(params, context)` 有 context）。`events`/`audit_logs` 不在 0011。 |
| **Option A** | 全部视为 P10 前置（阻塞授权设计） |
| **Option B** | 四类依赖分离，逐项归类 |
| **Engineering Consequences** | B 允许"设计不阻塞、实施分级阻塞"；A 会让 §23 警告的误判发生（"P10 missing ⇒ Authorization cannot be designed"） |
| **Security Consequences** | Memory/Workflow 无授权面 ⇒ 若提前实现会导致跨 tenant/space 泄漏 |
| **Migration Consequences** | 0 |
| **Agent Runtime Consequences** | Memory/Workflow 授权属 **Agent Runtime 阶段**能力 |
| **Module Consequences** | 无 |
| **Recommended Direction** | **Option B** —— 四类分离：<br>① **Audit**：Design=现在 · Implementation=P10 · Runtime=P10<br>② **Event（outbox）**：Implementation=P10（授权本身不依赖 outbox；仅缓存失效的未来选项依赖它）<br>③ **Workflow authorization**：Design=现在（契约补 context）· Implementation=`DEFERRED TO AGENT RUNTIME`<br>④ **Memory authorization**：Design=现在（契约补 context）· Implementation=`DEFERRED TO AGENT RUNTIME`<br>**Memory/Workflow 契约必须与 `ToolContext` 统一为同一 `AuthorizationContext`**（避免第二套上下文） |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

#### OQ-A22 — Audit Event ID 生成

| 字段 | 内容 |
|---|---|
| **Question** | audit event id 用 uuid4 还是 UUIDv7？是否需时间排序？谁生成？ |
| **Current Evidence** | `core/audit/interfaces.py: _new_id() -> uuid.uuid4()`（应用层生成）；数据律「ID = UUIDv7（应用层生成）；对外不透明标识用 UUIDv4」；DB 全部授权相关表 `PRIMARY KEY DEFAULT uap_uuid_v7()`。 |
| **Option A** | 视为"对外不透明标识" ⇒ uuid4 合规 |
| **Option B** | 改为 UUIDv7（对齐数据律与 DB 默认） |
| **Engineering Consequences** | B 提供**时间有序**（利于分页/归档/分区裁剪）；A 无顺序性 |
| **Security Consequences** | uuid4 不泄漏时间；uuid7 泄漏毫秒级创建时间。**审计记录本身即时间序列**，故该泄漏无实际意义 |
| **Migration Consequences** | 0（契约层） |
| **Agent Runtime Consequences** | 有序 id 便于按时间检索审计 |
| **Module Consequences** | 无 |
| **Recommended Direction** | **Option B（UUIDv7，应用层生成）** —— 审计事件天然是时间序列，有序 id 对**分区裁剪与归档（P10 的 `audit_logs` 分区）**有直接收益；且与 DB `uap_uuid_v7()` 默认一致。**"对外不透明标识用 UUIDv4"的适用边界应收窄为"对外暴露的指针类标识"**，审计实体 id 不属该类 |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

### D9 — SCHEMA

---

#### OQ-A17 — Schema Impact Classification

| 字段 | 内容 |
|---|---|
| **Question** | 哪些 schema 变更**必需**？哪些属未来/P10？哪些可被现有结构避免？ |
| **Current Evidence** | 候选对象：`resources.parent_id`（OQ-A04）· `policy_rules` / 策略载体（OQ-A01 D）· `approval_requests` / 待审批态（OQ-A11/A14）· `resource_relations`（OQ-A04 C）· `permissions.action` CHECK（OQ-A05）· `tool_permissions` 结构化列（OQ-A09）· `resource_permissions` UNIQUE 重建（OQ-A20）· `agent_versions` 版本列（OQ-A19）。**全部当前均不存在**（0011 实测）。 |
| **Option A** | 全部 `PROPOSED`，本阶段 0 变更 |
| **Option B** | 分类为 必需 / 未来 / 可避免 三档，仍 0 变更 |
| **Engineering Consequences** | B 提供实施阶段的清晰输入 |
| **Security Consequences** | 无（0 变更） |
| **Migration Consequences** | **本阶段 0**；`0010`/`0011` 不得改写；**不得创建 0012** |
| **Agent Runtime Consequences** | 实施顺序受 schema 变更节奏约束 |
| **Module Consequences** | Module 扩展动作的 registry 载体须先定（OQ-A05） |
| **Recommended Direction** | **Option B** —— 三档分类：<br>**必需（授权实施阶段）**：`permissions.action`/`resource_permissions.action` 词表 CHECK（OQ-A05）· `tool_permissions` 结构化四元组（OQ-A09，**触及 P09 邻域，须单独授权**）<br>**未来（P10 或 Runtime）**：`events`/`audit_logs`（P10，**非授权自有**）· 审批载体（`DEFERRED TO TOOL RUNTIME`）· delegation 载体（`DEFERRED TO AGENT RUNTIME`）<br>**可避免**：`resources.parent_id`（OQ-A04 判 A）· `resource_relations`（同上）· `resource_permissions` UNIQUE 重建（OQ-A20 判 A）<br>**全部仅登记为 `PROPOSED`，本阶段不创建任何对象** |
| **HUMAN DECISION** | **APPROVED**（2026-09-23）— 逐项正文见 §0.1 与 `PLATFORM_DECISION_LOG.md` |
| **STATUS** | 见 §0.1（`FROZEN` / `DEFERRED`） |

---

## 4. §27 DECISION RESOLUTION MATRIX

| OQ ID | Decision Domain | Question（简） | Current Evidence（简） | Human Decision | Status | Affected Components | Implementation Impact | Migration Impact |
|---|---|---|---|---|---|---|---|---|
| A01 | D4 | RBAC/ACL/Policy 组合 | 全部表已落库；契约职责重叠 | **APPROVED**（2026-09-23） | 见 §0.1 | core/permission · core/policy · services/ | 高 | 0（B）· 可能新增策略载体（D） |
| A02 | D1 | Agent 是否独立 Subject | ACL 白名单已含 agent | **APPROVED**（2026-09-23） | 见 §0.1 | core/permission · agents | 中 | 0 |
| A03 | D1 | Delegation 语义 | `tool_executions` 双列 | **APPROVED**（2026-09-23） | 见 §0.1 | core/policy · tool_executions | 高 | 0（C）· 新表（D） |
| A04 | D2 | Resource canonical | 8 项中 7 项已具备 | **APPROVED**（2026-09-23） | 见 §0.1 | core/resource · resources | 低 | 0 |
| A05 | D3 | Action 词汇表 | 三处自由 text | **APPROVED**（2026-09-23） | 见 §0.1 | permissions · resource_permissions | 中 | **需新增 CHECK** |
| A06 | D3 | Scope hierarchy | DB 已强制 3 层 | **APPROVED**（2026-09-23） | 见 §0.1 | roles · core/resource | 中 | 0 |
| A07 | D4 | Allow/Deny 优先 | `R2-D-14` 已冻结 | **APPROVED**（2026-09-23） | 见 §0.1 | core/permission · core/policy | 中 | 0 |
| A08 | D3 | 继承规则 | roles 三层 + expired_at | **APPROVED**（2026-09-23） | 见 §0.1 | core/permission · core/membership | 中 | 0 |
| A09 | D5 | Tool 授权模型 | `tool_permissions` 无四元组 | **APPROVED**（2026-09-23） | 见 §0.1 | tool_permissions · agent/tools | 高 | **需增列（P09 邻域）** |
| A10 | D6 | 风险模型 | 四档 enum vs float | **APPROVED**（2026-09-23） | 见 §0.1 | core/policy · tools/agents | 中 | 0（A） |
| A11 | D6 | 审批模型 | `approval_required` 已落库 | **APPROVED**（2026-09-23） | 见 §0.1 | tools · core/permission | 中 | 0 |
| A12 | D7 | 失败语义 | 多重 fail-closed 先例 | **APPROVED**（2026-09-23） | 见 §0.1 | core/permission · core/policy | 中 | 0 |
| A13 | D7 | 缓存语义 | 0 缓存；信号已落库 | **APPROVED**（2026-09-23） | 见 §0.1 | infrastructure/cache | 低 | 0 |
| A14 | D7 | Decision API | 三值无处安放 | **APPROVED**（2026-09-23） | 见 §0.1 | core/permission | 高 | 0 |
| A15 | D8 | 审计模型 | `audit_logs` 不在 0011 | **APPROVED**（2026-09-23） | 见 §0.1 | core/audit · P10 | 中 | **P10** |
| A16 | D7 | 服务落点 | D-PLAT-02/03/05 | **APPROVED**（2026-09-23） | 见 §0.1 | core/* · services/ | 高 | 0 |
| A17 | D9 | Schema 影响 | 全部候选均不存在 | **APPROVED**（2026-09-23） | 见 §0.1 | migrations | — | **分类见 OQ** |
| A18 | D1 | 主体词汇表 | 三套词汇并存 | **APPROVED**（2026-09-23） | 见 §0.1 | core/identity · acl_subject_types | 中 | 0（C） |
| A19 | D5 | Agent 版本语义 | str vs int | **APPROVED**（2026-09-23） | 见 §0.1 | agent/registry · agent_versions | 低 | 0（A/C） |
| A20 | D4 | ACL UQ 不含 effect | 0011 实测约束 | **APPROVED**（2026-09-23） | 见 §0.1 | resource_permissions | 低 | 0（A） |
| A21 | D8 | P10 依赖分类 | Memory/Workflow 无授权面 | **APPROVED**（2026-09-23） | 见 §0.1 | agent/memory · agent/workflow | 中 | 0 |
| A22 | D8 | AuditEvent id | uuid4 vs UUIDv7 | **APPROVED**（2026-09-23） | 见 §0.1 | core/audit | 低 | 0 |

**统计**（2026-09-23 冻结后）：22 行 · `APPROVED` 22 · **`FROZEN` 19** · **`DEFERRED` 3** · `SUPERSEDED` **0**。

---

## 5. §32 Decision ↔ Acceptance 映射

| OQ | 对应 Acceptance 行 | 说明 |
|---|---|---|
| A01 | AUTH-01 · POLICY-01 · POLICY-05 | 组合模式与职责唯一性 |
| A02 | AGENT-01 · AUTH-05 | Agent 作为主体可表达 |
| A03 | AGENT-02 · AGENT-06 | 越权边界 + delegation 审计 |
| A04 | SCOPE-05 | 资源继承可用性 |
| A05 | AUTH-06 | Action 词表可校验 |
| A06 | SCOPE-01 · SCOPE-02 · SCOPE-03 · SCOPE-04 | Scope 层级与 SELF 定性 |
| A07 | POLICY-05 · SEC-06 | 单一合并算法 + fail-closed |
| A08 | SCOPE-05 · CACHE-03 · CACHE-04 | 继承 / 归档 / 到期 |
| A09 | TOOL-01 · TOOL-03 · TOOL-07 · SEC-03 · AUTH-09 | 工具授权结构化 + 无旁路 |
| A10 | RISK-01 · RISK-02 · RISK-03 · RISK-04 | 风险值域统一 |
| A11 | APPROVAL-01 · APPROVAL-03 · APPROVAL-04 | 审批模型与状态 |
| A12 | SEC-06 | 失败语义统一 |
| A13 | CACHE-01 · CACHE-02 | 缓存与撤销 |
| A14 | APPROVAL-02 · AUTH-05 · POLICY-04 | Decision 契约三值 |
| A15 | AUDIT-02 · AUDIT-03 · AUDIT-05 | 审计字段与持久化 |
| A16 | ARCH-02 · ARCH-05 | 契约/实现落点 |
| A17 | MIG-05 · MIG-06 | schema 分类与零变更 |
| A18 | AUTH-05 · SEC-09 · SEC-10 | 主体词汇统一 + 防线保持 |
| A19 | AGENT-07 | 版本语义 |
| A20 | SEC-08 · CACHE-03 | ACL 改判与审计 |
| A21 | DEP-06 · DEP-07 | 依赖图与 Module 消费 |
| A22 | AUDIT-06 | 审计 id 生成 |

**要求核对（§32）**：「Every FROZEN decision → at least one acceptance criterion」——
**已于 2026-09-23 获 Human 冻结**，FROZEN 决策数 = **20**（19 OQ + `D-AUTH-23`），
§16 映射覆盖 **50** 条验收行（实测，去重）；本表即 FROZEN 决策到验收判据的**完整映射**（无 orphan）。

---

## 6. §33 EXIT CONDITIONS 逐项

| # | 条件 | 状态 | 说明 |
|---|---|---|---|
| 1 | 22 OQ individually resolved | ✅ | **22/22 已获 Human 明确裁定**（**OQ 口径** 19 `FROZEN` + 3 `DEFERRED`；另 `D-AUTH-23` 非 OQ） |
| 2 | or explicitly DEFERRED | ✅ | 3 项 `DEFERRED`（A03 / A13 / A21），**均带 Owner Phase + Exit Condition，无 `TBD`** |
| 3 | No silent decision | ✅ | 全部经 Human 逐项明确裁定；无任何自主冻结 |
| 4 | Existing frozen decisions protected | ✅ | §1 逐项核验在位 |
| 5 | Subject vocabulary unified | ✅ | `D-AUTH-18`（Canonical Subject Types = USER/ROLE/AGENT） |
| 6 | Agent delegation defined | ✅ | 基础语义由 `D-AUTH-02`/`D-AUTH-03` 冻结；完整 delegation contract → `DEFERRED TO AGENT RUNTIME` |
| 7 | Resource model defined | ✅ | `D-AUTH-04` |
| 8 | Action model defined | ✅ | `D-AUTH-05`（12 项 platform canonical） |
| 9 | Scope model defined | ✅ | `D-AUTH-06`（PLATFORM/TENANT/SPACE；`SELF` = predicate） |
| 10 | RBAC/ACL/Policy composition defined | ✅ | `D-AUTH-01` |
| 11 | Allow/Deny precedence defined | ✅ | `D-AUTH-07`（继承 `R2-D-14`） |
| 12 | Tool authorization defined | ✅ | `D-AUTH-09` |
| 13 | Risk model defined | ✅ | `D-AUTH-10`（四档 canonical） |
| 14 | Approval model defined | ✅ | `D-AUTH-11`（静态 OR 策略；persistence `DEFERRED`） |
| 15 | Failure semantics defined | ✅ | `D-AUTH-12`（FAIL CLOSED） |
| 16 | Cache semantics defined | ✅ | `D-AUTH-13`（当前 `No Authorization Cache` 冻结；实现 `DEFERRED`） |
| 17 | Authorization API contract frozen | ✅ | `D-AUTH-14`（`ALLOW`/`DENY`/`REQUIRES_APPROVAL`） |
| 18 | Service placement frozen | ✅ | `D-AUTH-16` |
| 19 | Audit dependency explicitly classified | ✅ | `D-AUTH-15` / `D-AUTH-21` |
| 20 | Schema impact explicitly classified | ✅ | `D-AUTH-17` |
| 21 | P09 unchanged | ✅ | `agents`/`agent_versions`/`agent_permissions`/`tool_executions` 未触碰；0011 sha256 未变 |
| 22 | 0010 unchanged | ✅ | sha256 `6d9907237f80e9da…` |
| 23 | No 0012 created | ✅ | 0012+ = 0 |
| 24 | No runtime implementation | ✅ | 0 代码变更 |
| 25 | Architecture docs synchronized | ✅ | 见 §34 文档同步（8 份文档语义一致） |
| 26 | Decision Log synchronized | ✅ | `D-AUTH-01`…`D-AUTH-23`（23 条 = 20 `FROZEN` + 3 `DEFERRED`）已写入 `PLATFORM_DECISION_LOG.md` |
| 27 | Acceptance Matrix synchronized | ✅ | §16 映射 + 状态翻转（22/22 可追踪） |

⇒ **`DECISION FREEZE = PASSED`**（27/27 条件满足）

---

## 7. 冻结请求包 → **已于 2026-09-23 获 Human 批准并执行**

> **状态更新**：本节原为"待批准"的请求包。Human 已于 2026-09-23 **逐项明确批准**
> （**OQ 口径** 19 `FROZEN` + 3 `DEFERRED`），决策正文已写入 `PLATFORM_DECISION_LOG.md`（`D-AUTH-01`…`D-AUTH-23`；
> 完整 registry = 23 条：20 `FROZEN` + 3 `DEFERRED`，含非 OQ 的 `D-AUTH-23`）。
> 以下内容保留为**批准时的原始对照基线**（Human 裁定的逐项落地形式）。

以下即 §25 RECOMMENDED BASELINE 的**逐项落地形式**：

```text
【D1 Subject】
A18 → Option C  Canonical Subject Types = {USER, ROLE, AGENT}（授权域）
                Identity Provider = {local,oidc,saml,device,service}（认证域）
                Authorization Subject ≠ Provider（正交）
A02 → Option C  Agent = independent authorization subject
A03 → Option C  Effective = Agent 权限 ∩ Actor 有效授权（默认不委托、不可超越、可撤销、必审计）
                Option D（显式 delegation scope）→ DEFERRED TO AGENT RUNTIME

【D2 Resource】
A04 → Option A  保持 8 属性现状；owner 仅 USER；Agent 关系走 ACL 行
                parent_id / resource_relations → DEFERRED（Authorization Implementation，出现真实用例时）

【D3 Action / Scope】
A05 → Option B  平台统一词表（12 项；**存储形 = 小写**，`D-AUTH-25`）+ DB CHECK + 契约枚举；Tool Action = Resource Action 同表
A06 → Option A  PLATFORM→TENANT→SPACE→RESOURCE；SELF = Context predicate（非 Scope）
A08 → Option A  角色层继承 only + 四条规则（Inheritance/Override/Explicit Deny/Revocation）

【D4 Permission / ACL / Policy】
A01 → Option D  终态 RBAC+ACL+Policy（B 为中间形态）
                RBAC=baseline · ACL=resource-specific · Policy=contextual
                conditions 归属 core/policy（消除职责重叠）
A07 → Option A  正式继承 R2-D-14：DENY > ALLOW，跨层统一，无层级特权
                冻结 deterministic / order-independent / auditable
A20 → Option A  保持 UNIQUE 不含 effect；文档化「ACL 层每元组唯一，改判=行替换+同事务审计」

【D5 Agent / Tool】
A09 → Option B  tool_permissions 结构化四元组 (permission, resource_type, action, scope)
                执行前强制携带授权决策；Tool 不得自实现授权
A19 → Option C  revision(int, DB 已定) / identity(agent_versions.id) / display(str, 不参与授权)

【D6 Risk / Approval】
A10 → Option A  四档 LOW/MEDIUM/HIGH/CRITICAL 为 canonical；score 降为可选辅助
                Risk = Policy 的输入 + Execution 的属性，不是 authorization 本体
A11 → Option C  approval_required = tool.approval_required OR policy.requires_approval（永不做 AND）

【D7 Runtime Semantics】
A12 → Option A  8 类失败分支全部 FAIL CLOSED → DENY（携带 reason 供观测）
A13 → Option A  首发不缓存；缓存四语义预冻结；fail-open 绝对禁止
                B/C → DEFERRED（Authorization Implementation，P10 events 落地后）
A14 → Option B  Decision.effect ∈ {ALLOW, DENY, REQUIRES_APPROVAL}（三值为终态语义）
                补齐 subject/delegator/action/resource/scope/context/decision/reason/policy_version
A16 → Option B  Contract=core/{permission,policy,resource,audit} · Service=services/authorization/
                Persistence=services 内经 infrastructure；core 无 I/O

【D8 Audit / P10】
A15 → Option B+C  Design 现在可冻结 · Implementation=P10 · Runtime=P10
                  Authorization Decision ≠ Tool Execution（不同载体）
                  不得自行创建 events/audit_logs
A21 → Option B  四类依赖分离（Audit=P10 / Event=P10 / Workflow auth=DEFERRED TO AGENT RUNTIME /
                Memory auth=DEFERRED TO AGENT RUNTIME）；Memory/Workflow 契约统一为 AuthorizationContext
A22 → Option B  AuditEvent.id = UUIDv7（应用层生成）

【D9 Schema】
A17 → Option B  三档：必需（A05 CHECK · A09 增列）/ 未来（P10 审计 · 审批载体 · delegation 载体）/
                可避免（parent_id · resource_relations · ACL UQ 重建）
                全部 PROPOSED；0010/0011 不得改写；不得创建 0012
```

**Human 确认后的动作** —— **已于 2026-09-23 执行完毕**：写 `PLATFORM_DECISION_LOG.md`
（`D-AUTH-01`…`D-AUTH-23`；**OQ 口径** 19 `FROZEN` + 3 `DEFERRED`，完整 registry 20 + 3）→ 同步 `ARCHITECTURE.md` /
`DEPENDENCY_RULES.md` / `docs/security/README.md` / `docs/api/README.md` →
`AUTHORIZATION_ACCEPTANCE_MATRIX.md` 状态由 `PENDING` 改为 `FROZEN` → **`DECISION FREEZE = PASSED`**。

---

## 8. §35 HARD STOP 自查

| 触发条件 | 是否发生 |
|---|---|
| Existing frozen decision conflict | ❌ 未发生（§1 逐项在位） |
| P09 conflict | ❌ 未发生（0011 sha256 未变） |
| Ambiguous delegation | ⚠ **存在** —— A03 未裁定（已上升为 OQ，**未实施**） |
| Undefined tenant isolation | ❌ 未发生（`resources.tenant_id` NN + trigger + `require_same_tenant`） |
| Undefined deny precedence | ⚠ **存在** —— A07/A20 未裁定（已有 `R2-D-14` 先例，**未实施**） |
| Undefined tool authorization | ⚠ **存在** —— A09 未裁定（**未实施**） |
| Audit dependency unclear | ⚠ 已分类（A15/A21）但**未获批准** |
| Schema impact unknown | ❌ 未发生（A17 三档分类已备） |
| Agent permission can exceed user boundary | ❌ 未发生（A03 推荐 C 明确禁止；**但未获批**） |
| Authorization failure can default ALLOW | ❌ 未发生（A12 推荐 A；**但未获批**） |

⇒ 三项 ⚠ 均为**待裁定的设计分叉**（已转为 OQ），**未产生任何实施行为**。
**HARD STOP 生效中：未进入 implementation。**

---

**END OF DECISION RESOLUTION PACKAGE（2026-09-23）**

> `HUMAN DECISION = APPROVED` × 22 OQ（2026-09-23）· **完整 registry：`D-AUTH` = 23 → 20 `FROZEN` + 3 `DEFERRED` + 0 `SUPERSEDED`**
> （**OQ 口径**：22 = 19 `FROZEN` + 3 `DEFERRED`；`D-AUTH-23` 来自 `GAP-11`，非 OQ）
> **`DECISION FREEZE = PASSED`** · `GAP-11 = RESOLVED` · `IMPLEMENTATION / COMMIT / TAG / PUSH = NOT AUTHORIZED`
> **HUMAN DECISION REQUIRED — 不得自行实施。**
