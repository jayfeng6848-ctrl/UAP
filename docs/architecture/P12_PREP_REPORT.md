# P12 PREP REPORT — INDEXES

> **Status**: `PREP / DESIGN FROZEN-PENDING` —— **本轮 STRICT READ-ONLY**。
> **`P12 IMPLEMENTATION = NOT AUTHORIZED`** · **`P13 IMPLEMENTATION = NOT AUTHORIZED`** ·
> **`Runtime Implementation Gate = CLOSED`**。
> 本轮**零实施**：`CREATE/ALTER/DROP INDEX = 0` · `DDL = 0` · `DML = 0` · `migration = 0` ·
> `code = 0` · `test = 0` · `config = 0` · `commit/tag/push = 0`。
> **`RECOMMENDED ≠ FROZEN`** —— 全部 OQ 的 `HUMAN DECISION = PENDING` · `STATUS = PROPOSED`。

---

## 1. Baseline（只读实测）

| 项 | 值 |
|---|---|
| `HEAD` | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` |
| `TAG` | `UAP-V0.1.8-AUTHORIZATION`（tags 总数 **8**） |
| `remote` | **none**（从未 push） |
| `alembic heads` | **单头** `0012_authz_enforcement` |
| `0013+` | **0** |
| `0010` sha256 | `6d9907237f80e9da…`（未变） |
| `0011` sha256 | `cdaf8383630335db…`（未变） |
| `0012` sha256 | `5ecd1ef30b403fb4…`（未变） |

`D-PLAT-09 = P10 → P11 → P12 → P13 → Runtime` —— **FROZEN / NOT SUPERSEDED**。
`P10 DECISION FREEZE = PASSED` · `P11 DECISION FREEZE = PASSED`。

---

## 2. P12 Scope（**由冻结证据定义，非本轮发明**）

```text
P12 = INDEXES
    = 非 PK 索引（纯查询索引 + FK 反查支撑索引）
    + 已冻结但尚未落地的索引（P10 表索引）
```

### 2.1 冻结证据（逐条可核）

| # | 冻结陈述 | 路径 |
|---|---|---|
| 1 | **「上表『动作』列的补充索引进入 **P12**」**（§3 FK 反查强制清单） | `STEP1B_INDEX_STRATEGY.md:202` |
| 2 | P09 **显式**将 FK 列索引推迟：**「不额外补 FK 列索引」**，并注明「FK 反查补索引进入 **P12**」 | `P09_DECISION_LOG.md:248` · `P09_SCOPE.md:29` · `P09_SCHEMA_DESIGN.md:112` |
| 3 | 授权决策路径索引 = **P12 候选** | `AUTHORIZATION_PREP_REPORT.md:549` |
| 4 | **`P10 必须先于 P12 存在`（`ix_events_*` / `ix_audit_*` 建在 P10 表上）** | `P10_PREP_REPORT.md:132` · `:326` · `P10_ACCEPTANCE_MATRIX.md:159` |
| 5 | **seed 前必须有：全部表（P01–P10）+ 全部 trigger（P11）+ 全部 index（P12）** | `STEP1B_SEED_STRATEGY.md:138` |
| 6 | **P12 只保留「纯查询索引」** | `AGENT_RUNTIME_DECISION_RESOLUTION.md:404` |
| 7 | **「不新增索引（属 P12 范畴）」** | `0012_authz_enforcement.py` docstring |
| 8 | B1-5 **不进入** P12（索引建表内联） | `B1-5_SCOPE.md:155` |
| 9 | 路线 A：`P10 → P11 → P12 → P13 → Runtime` | `D-PLAT-09`（`PLATFORM_DECISION_LOG.md`） |

### 2.2 **OUT OF SCOPE**（P12 不得吞入）

```text
trigger / constraint redesign / FK redesign
authorization semantics / policy evaluation / ACL 求值
runtime / worker / seed / partition redesign / business query implementation
P11 未完成事项（G/H/I/J = P11-owned，`D-P11-01`）
P10 audit-local immutability（`tg_audit_immutable` = P10-owned，`D-P10-11`）
```

**边界铁律**：索引 **不等于** 授权；不得通过新增索引偷渡任何授权语义（`D-P11-07`）。
**机制铁律**：约束若已由 `CHECK` / `FK` / `UNIQUE constraint` / `trigger` 承载，则**保持原机制**，不得因 P12 再造等价约束。

---

## 3. Existing Substrate（**migration 层实测清单**）

> 数字为脚本实测（`p12_inventory.log`），非估算。口径：**每个可独立创建/删除的索引对象计 1**；
> 内联 `sa.UniqueConstraint` 会隐式建立 real btree index，**计入**。

### 3.1 总量

| 项 | 值 |
|---|---|
| 独立创建索引对象 | **52**（`op.create_index` **25** + 原生 SQL **27**） |
| 内联 UNIQUE CONSTRAINT 隐式索引 | **5** |
| **索引对象总数** | **57** |
| 前缀分布（52） | `ix=` **24** · `uq=` **28** |
| unique / non-unique / partial（52） | **20** / **32** / **16** |
| 建表形态 | `op.create_table` 表数 **29** · FK 约束 **54** |

### 3.2 逐 revision（**与 migration docstring 声明的对象数逐项对账 ✅**）

| revision | 索引对象 | docstring 声明 | 对账 |
|---|---|---|---|
| `0003_b1_1_root_identity` | **15** | — | — |
| `0004_b1_2_tenant_space` | **7** | B1-2「实际新建 **7**」 | ✅ |
| `0005_b1_3_authorization` | **10** | B1-3 §5「实际新建 **8**」= 4 UQ + 3 btree + **1 PK**（PK 随表创建，**不计**为独立索引对象）⇒ 7 个索引对象；实测 **10** = 7 + **R3 增补 3**（`platform_memberships`） | ⚠ 口径差（见 §5.3） |
| `0007_b1_4_resource_acl` | **8** | 「indexes (8)」（含内联 UQ） | ✅ |
| `0008_b1_5_tool_registry` | **4** | 「UNIQUE INDEX = 3 · non-PK INDEX = 4」 | ✅ |
| `0010_b1_6_ai_gateway` | **5** | 「UNIQUE INDEX = 2 · non-PK INDEX = 5」 | ✅ |
| `0011_p09_agent_tool_permission` | **8** | 「交付 **8 个索引对象**」 | ✅ |
| `0001 / 0002 / 0006 / 0009 / 0012` | **0** | `0009`：「不新增/删除任何 … Index」· `0012`：「不新增索引」 | ✅ |
| **合计** | **57** | | |

### 3.3 内联 UNIQUE CONSTRAINT（隐式索引，5）

```text
uq_resource_perm   ON resource_permissions (resource_id, subject_type_id, subject_id, action)
uq_tool_versions   ON tool_versions        (tool_id, version)
uq_ai_providers_key ON ai_providers        (key)
uq_ai_models       ON ai_models            (provider_id, model_key)
uq_agent_versions  ON agent_versions       (agent_id, version)
```

> **重要**：这 5 个对象是 **real btree index**，在 **FK 反查覆盖判定中必须计入**（否则产生假阳性 gap）。

---

## 4. FK 反查覆盖分析（**本轮核心实测**）

> 判据：父行 `DELETE` / `RESTRICT` 检查会在**子表 FK 列**上做查找；若该列**无以其打头的非部分索引**，
> 则触发**子表全扫**。**部分索引（partial）不服务 FK 检查**（谓词不保证覆盖全部行）。

### 4.1 总览（54 FK）

| 判定 | 数量 |
|---|---|
| **已覆盖**（PK 打头 / 非部分索引打头） | **25** |
| **partial-only**（部分索引打头 ⇒ **不可用**） | **5** |
| **无索引（GAP）** | **24** |
| 合计 | **54** ✅（分划自洽断言通过） |

### 4.2 GAP 明细（24，按 `ondelete` 分布：`CASCADE=6` · `RESTRICT=11` · `SET NULL=7`）

```text
-- 0011（P09）10 项 --
agent_permissions  permission_id   -> permissions.id        CASCADE
agent_permissions  tool_id         -> tools.id              CASCADE
agent_permissions  version_id      -> agent_versions.id     CASCADE
agent_versions     published_by    -> users.id              SET NULL
agents             default_route_id-> ai_routes.id          SET NULL
agents             owner_id        -> users.id              RESTRICT
agents             space_id        -> spaces.id             RESTRICT
tool_executions    actor_id        -> users.id              SET NULL
tool_executions    agent_id        -> agents.id             SET NULL
tool_executions    tool_version_id -> tool_versions.id      RESTRICT

-- 0010（P08）7 项 --
ai_policies        space_id        -> spaces.id             RESTRICT
ai_policies        tenant_id       -> tenants.id            RESTRICT
ai_request_logs    model_id        -> ai_models.id          RESTRICT
ai_request_logs    provider_id     -> ai_providers.id       RESTRICT
ai_routes          primary_model_id-> ai_models.id          RESTRICT
ai_routes          space_id        -> spaces.id             RESTRICT
ai_routes          tenant_id       -> tenants.id            RESTRICT

-- 0008（B1-5）2 项 --
tool_permissions   permission_id   -> permissions.id        CASCADE
tool_permissions   version_id      -> tool_versions.id      CASCADE

-- 策略文档时代（0004/0007）5 项 --
memberships        user_id         -> users.id              CASCADE
resource_permissions granted_by    -> users.id              SET NULL
resources          owner_id        -> users.id              SET NULL
resources          space_id        -> spaces.id             RESTRICT
spaces             owner_id        -> users.id              SET NULL
```

> 分划闭合：**10 + 7 + 2 + 5 = 24**（与 §4.1 一致）。
> 注：`tool_versions.tool_id` / `ai_models.provider_id` / `agent_versions.agent_id` /
> `resource_permissions.resource_id` **不计入 GAP** —— 它们分别由内联 `uq_tool_versions` /
> `uq_ai_models` / `uq_agent_versions` / `uq_resource_perm` **以首列覆盖**（§3.3）。

### 4.3 partial-only（5——**最隐蔽的一类**）

```text
credentials        identity_id -> identities.id   CASCADE    partial 名: uq_credentials_active_password
roles              space_id    -> spaces.id       CASCADE    partial 名: uq_roles_space
roles              tenant_id   -> tenants.id      CASCADE    partial 名: uq_roles_tenant
tool_executions    tool_id     -> tools.id        RESTRICT   partial 名: uq_tool_exec_idem
tools              tenant_id   -> tenants.id      RESTRICT   partial 名: uq_tools_tenant
```

**为何危险**：这 5 条**看起来"有索引"**（`uq_*` 存在），但**部分谓词**（`WHERE status='active'` /
`WHERE idempotency_key IS NOT NULL` / `WHERE tenant_id IS NOT NULL` / `WHERE removed_at IS NULL` 等）
使 PostgreSQL **无法**用其做 FK 完整性检查 ⇒ 运行时等同 **无索引**。

### 4.4 时代切分（**关键结构发现**）

| 分类 | 数量 |
|---|---|
| GAP 总数 | **24** |
| ├ **策略文档之后**建的表的 GAP | **19** |
| └ 策略文档时代的表的 GAP | **5** |
| partial-only 总数 | **5** |
| └ 策略文档之后的表 | **2**（`tool_executions.tool_id` · `tools.tenant_id`） |

**结论**：`STEP1B_INDEX_STRATEGY.md` §3「FK 反查强制清单」**成文早于** `0008` / `0010` / `0011` 的建表
⇒ 其中 **19 个 GAP 从未被该清单adjudicate**（既未"要求补"，也未"判定免建"），属**清单完整性缺口**，
与 P11 的 `GAP-INV-1` 同类。⇒ 登记为 **`GAP-INV-P12`**（见 §9）。

---

## 5. 设计层 vs 实现层对账

### 5.1 设计层已声明、**尚未落地**的冻结索引

| 索引 | 表 / 定义 | 冻结状态 | 归属判定 |
|---|---|---|---|
| `ix_events_dispatch` | `events (status, next_attempt_at) WHERE status IN ('pending','claimed')` | 冻结（`INDEX_STRATEGY` §1） | **P12**（`ix_events_*`；P10 表先存在） |
| `ix_events_tenant_type_time` | `events (tenant_id, event_type, occurred_at DESC)` | 冻结 | **P12** |
| `ix_audit_tenant_time` | `audit_logs (tenant_id, occurred_at DESC)` | 冻结 | **P12** |
| `ix_audit_actor_time` | `audit_logs (actor_id, occurred_at DESC)` | 冻结 | **P12** |
| `ix_audit_resource` | `audit_logs (resource_type, resource_id, occurred_at DESC)` | 冻结 | **P12** |
| `ix_audit_correlation` | `audit_logs (correlation_id)` | 冻结 | **P12** |
| `ix_audit_risk` | `audit_logs (risk_level, occurred_at) WHERE risk_level IN ('HIGH','CRITICAL')` | 冻结 | **P12** |

⇒ **P10 表索引 = 7**（`events` 2 + `audit_logs` 5）· 全为**非唯一**索引（`events`/`audit_logs` **UQ = 无**，
`CONSTRAINT_MATRIX` §7）⇒ **不触发「分区表唯一索引必须含分区键」约束**。

### 5.2 设计层已声明、**判定为 P3 或 DEFERRED**（未落地）

| 索引 | 状态 | 依据 |
|---|---|---|
| `ix_users_status` | **P3 候选** | `INDEX_STRATEGY:218` |
| `ix_tenants_status` | **P3 候选**（B1-2 已判「无批扫 job → 不建」） | `INDEX_STRATEGY:218` · `B1_2:19` |
| `ix_rp_permission` | **P3 候选**……但**功能上已落地**（见 §7.3 命名漂移） | `INDEX_STRATEGY:218` · `B1-3:41` |
| roles FK 反查（`roles.tenant_id` / `roles.space_id`） | **P3 候选**（「roles 少、低风险」） | `INDEX_STRATEGY:196` · `:218` |
| `agents.owner_id` | **P3 候选**（「少」） | `INDEX_STRATEGY:200` · `:218` |
| `ix_aimodels_capability ON (capability) WHERE enabled` | **`T-1` = DEFERRED** | `0010` docstring · `B1-6_DECISION_LOG:436` |

**`T-1` 根因（本轮核实）**：设计谓词引用 `capability`，而**实测** `ai_models` 只有
**`capabilities jsonb`**（复数、JSONB），`capability` 列**不存在**；`enabled` 列**存在**。
且 `INDEX_STRATEGY` §2 明示 **「jsonb GIN 不建」** ⇒ 该 index 同时受 **列名不存在** 与 **反模式禁令** 双重阻断。

### 5.3 实现层有、**B0 策略文档无对应条目**

| 对象 | 说明 |
|---|---|
| `uq_platform_memberships_user_role` · `uq_platform_memberships_active_user` · `ix_platform_memberships_role_status` | 三者**已在** `STEP1B_B1_3_INDEX_STRATEGY.md` **R3 增补**中冻结并落地；但 **B0 `STEP1B_INDEX_STRATEGY.md` §1 无 `platform_memberships` 小节** ⇒ **B0 文档不完整**（登记，不重写） |

> 其余实现层索引**均可回溯至 B0 §1 / §3 或 B1-2 / B1-3 分阶段策略**，未发现"无来源索引"。

---

## 6. 查询证据规则（`OQ-P12-02` 的输入）

**P12 每个候选索引必须给出证据来源**，优先级：

```text
1. frozen Decision
2. existing schema contract（CONSTRAINT_MATRIX / INDEX_STRATEGY / ER_MODEL）
3. explicit documented query pattern（B1-2 / B1-3 索引策略的 Query Pattern 列）
4. acceptance / test query
5. measured implementation requirement（FK 反查为 PG 语义级要求）
```

**禁止**以「未来可能会查」/「一般都应建」/「为了性能先建」为**唯一**依据。
每个 proposed index 须回答：**服务哪个查询 · 涉及哪些 filter/order · 哪个 tenant/space 边界 ·
既有索引为何不足 · 基数/选择性理由**。

> **例外说明**：`§4` 的 FK 反查项证据等级为 **①（PG 语义级强制）** —— 它不是"性能优化"，
> 而是"父表删除**不得**退化为子表全扫"的**结构性要求**（`INDEX_STRATEGY` §3 原文定此口径）。

---

## 7. 命名与语义审计

### 7.1 B0 §4 命名规范（冻结）

```text
唯一：uq_<table>_<cols>
查询：ix_<table>_<cols>（列序同索引定义）
部分：名内含 WHERE 语义注释；DDL 必须写明谓词
复合列序 = 等值在前、范围在后
```

### 7.2 观测到的**缩写偏移**（登记，**不在 PREP 改名**）

`ix_tm_user` · `ix_rp_subject` · `ix_res_*` · `ix_ap_agent` · `ix_texec_*` · `ix_airl_*` · `ix_aimodels_*`
—— 均以**表名缩写**代替全表名（受 PG 标识符长度等实践约束）。

### 7.3 **命名漂移（真实不一致，2 处）**

| 设计层名称 | 出处 | 实现层名称 | 出处 |
|---|---|---|---|
| `ix_rp_permission` | `B1-3_INDEX_STRATEGY.md:41` · `B1-3_GATE_REPORT.md:42` · `B1-6_DECISION_LOG.md:331` | **`ix_role_permissions_permission`** | `0005…:386` |
| `ix_tm_role` | `B1-2_INDEX_STRATEGY.md:37` · `B1-3_INDEX_STRATEGY.md:49` · `B1-3_GATE_REPORT.md:42` | **`ix_tenant_memberships_role`** | `0005…:438` |

**连带陈旧陈述**：`B1-6_DECISION_LOG.md:331` 断言 P3 候选 6 项
「实测**全部未在 0003–0008 落地**」——其中 `ix_rp_permission` **功能上已落地**（改名）。
⇒ 登记为 **`CF-3`**（`INDEX_STRATEGY` §5 与 `B1-6` 陈述 **vs** 实现层事实）。

### 7.4 唯一 / 部分语义审计（冻结定义已落实）

- `uq_tool_exec_idem ON (tool_id, idempotency_key) WHERE idempotency_key IS NOT NULL` —— **部分 UNIQUE INDEX**（非 CONSTRAINT），
  落实 `D-P09-04 = A`；NULL 分支（`idempotency_key IS NULL`）**不受唯一约束**（幂等键可缺省）✅
- `uq_memberships … WHERE removed_at IS NULL` —— 软删后可重新加入（幂等重入）✅
- `uq_users_email/username … WHERE deleted_at IS NULL` —— 软删后同名可重建 ✅
- `uq_resources_natural … WHERE natural_key IS NOT NULL AND deleted_at IS NULL` ✅
- `uq_roles_{platform,tenant,space}` —— **三 scope 互斥**谓词（`tenant_id IS NULL AND space_id IS NULL` 等）✅
- `uq_spaces_key … WHERE deleted_at IS NULL` · `uq_agents_key … WHERE archived_at IS NULL` ·
  `uq_acl_subject_types_key … WHERE archived_at IS NULL` · `uq_tools_{platform,tenant}` ✅
- **表达式唯一性**：`uq_ai_routes` / `uq_ai_policies` / `uq_agent_perm` / `uq_tool_perm` 用 `COALESCE(…, '{NIL_UUID}')`
  —— 落实 `D-B16-07 = A` / `D-P09-16（ND-04）`：「表达式唯一性必须是 unique INDEX，不能是 UNIQUE CONSTRAINT」✅
- **无任何**唯一性规则被误用为索引（反查：`events`/`audit_logs` UQ = **无**；`resource_permissions` 唯一性 = **UNIQUE CONSTRAINT** 形式，保持原机制）✅

---

## 8. 分区交互（`OQ-P12-10` 的输入）

| 项 | 实测 |
|---|---|
| 现存在分区表 | **1**：`ai_request_logs`（`0010`，`PARTITION BY RANGE (occurred_at)`；父表 + 当月子分区） |
| 父表上的索引 | `ix_airl_tenant_occurred`（**建在父表** ⇒ PG 自动下推子分区） |
| 冻结规则 | 「分区表索引建在父表自动下推」；`B1-6 DC-4`：**子分区继承父表 PK，不额外建本地索引** |
| P12 将新增 | `events` 2 条 + `audit_logs` 5 条（**同为分区表**） |
| 唯一索引 × 分区键 | `events` / `audit_logs` **UQ = 无** ⇒ **不涉及**「分区表唯一索引必须含分区键」约束 |
| **不得改变** | partition key · PK · partition strategy · retention policy（任何此类发现 = `DEPENDENCY / OUT OF SCOPE`） |
| 保留期 | `events` 投递后 **30d**（dead 90d）· `audit_logs` **365d**、**不做行级删除**（分区 drop） |

**运维张力（登记，见 §9 `CF-6`）**：`D-P10-01` 以**「分区表二次 `ALTER` 代价高」**为由，
把 `events` 的 outbox 状态列**一次建齐**；而 P12 将在**同一批分区表**上后置创建 **7 个索引**。
索引 ≠ 加列（不属 `D-P10-01` 字面禁止），但属**同类运维代价**，须由 `OQ-P12-08` 明确
「P10 建表 + P12 建索引」两段式是否为**有意**结构，还是应将 7 条索引前移/后移。

---

## 9. 交叉一致性扫描（Charter §7 · **6 项登记，本轮不修**）

| ID | 事项 | 类型 | 性质 |
|---|---|---|---|
| **`CF-1`** | `INDEX_STRATEGY` §3 称 resources「复合索引打头 tenant/space/**owner** 均覆盖 → **通过**」；**实测**无一索引以 `space_id` 或 `owner_id` **打头**（`ix_res_tenant_space_type_status` 以 `tenant_id` 打头；`ix_res_tenant_owner` 以 `tenant_id` 打头） | **SCHEMA vs DOC** | **真实不一致**，须裁定 |
| **`CF-2`** | `ix_aimodels_capability`：§1 **声明** · §5 标 **P3** · `O-E` 登记**相位歧义**（`B1-6_DEPENDENCY` 归「P11/P12」，`INDEX_STRATEGY:218` 未 assign）· 谓词**引用不存在列** · §2 **禁止 jsonb GIN** | **DECISION vs SCHEMA vs DECISION** | **多重不一致**，不得静默解决 |
| **`CF-3`** | `B1-6_DECISION_LOG:331` 称 P3 候选「全部未在 0003–0008 落地」，但 `ix_rp_permission` **已以 `ix_role_permissions_permission` 落地** | **DOC vs SCHEMA** | 陈旧陈述（P3 清单需重新对账） |
| **`CF-4`** | **B0 `STEP1B_INDEX_STRATEGY.md` 无 `platform_memberships` 小节**，而该表 3 个索引对象已落地 | **DOC 不完整** | 登记（原 B0 不改写） |
| **`CF-5`** | **部分索引不可服务 FK 检查**：`uq_tool_exec_idem` / `uq_tools_tenant` / `uq_roles_*` / `uq_credentials_active_password` 被**当作**"已覆盖"，实测为 **partial-only** | **SEMANTICS** | 机制语义澄清（须写入 P12 判据） |
| **`CF-6`** | `D-P10-01`「分区表二次 ALTER 代价高」（列一次建齐）**vs** P12 在同两表**后置建 7 索引** | **DECISION vs PHASE** | 运维结构张力，须裁定 |

**陈旧"P12 已实现"声明扫描 = 0 命中**（`P12` 在 `docs/` 的全部命中均为**相位/依赖引用**，
无任何「P12 已实现/已落地」陈述）。

**`GAP-INV-P12`**：§4.4 —— 19 个 FK GAP 属**清单未覆盖**（非"判定免建"），与 `P11 GAP-INV-1` 同类。

---

## 10. Open Questions（15 · 全部 `PENDING` / `PROPOSED`）

| ID | 主题 |
|---|---|
| `OQ-P12-01` | canonical index inventory（权威载体与对账口径） |
| `OQ-P12-02` | query evidence standard |
| `OQ-P12-03` | tenant/space index policy |
| `OQ-P12-04` | unique index semantics |
| `OQ-P12-05` | partial index semantics（**含 FK-scan 不可用性**） |
| `OQ-P12-06` | idempotency index（`uq_tool_exec_idem`） |
| `OQ-P12-07` | Agent / Tool lookup indexes |
| `OQ-P12-08` | **Event / Audit indexes（7 条 · 分区表 · P10-vs-P12 相位边界）** |
| `OQ-P12-09` | P11-dependent indexes（G/H/I/J 复用 `ix_rp_subject`） |
| `OQ-P12-10` | partition index policy |
| `OQ-P12-11` | redundancy policy |
| `OQ-P12-12` | index naming convention（含漂移处置） |
| **`OQ-P12-13`** | **FK 反查补索引闭合范围**（24 GAP + 5 partial-only）— 证据驱动新增 |
| **`OQ-P12-14`** | **P3 候选 6 项 + `T-1` 的处置**— 证据驱动新增 |
| **`OQ-P12-15`** | **机制边界与索引所有权**（index vs CHECK/FK/UQ/trigger）— 证据驱动新增 |

逐项材料见 `P12_DECISION_RESOLUTION.md`。

---

## 11. Dependency（四类分离）

| 关系 | 方向 | 性质 | 依据 |
|---|---|---|---|
| P10 → P12 | P12 依赖 P10 | **schema / index dependency**（`events` / `audit_logs` 必须先存在） | `P10_PREP_REPORT:132/326` |
| P11 → P12 | 弱依赖 | **顺序依赖**（`P10→P11→P12`）；**语义解耦**：P11 正确性 **MUST NOT** 依赖 P12 业务语义 | `D-P11-11` |
| P12 → P13 | P13 依赖 P12 | **seed 前置**（全部 index 须先于 seed） | `SEED_STRATEGY:138` |
| P12 → Runtime | Runtime 依赖 P12 | **phase gate**（`P10∧P11∧P12∧P13∧Gateway`） | `D-PLAT-09` · `D-AGENT-16` |
| P12 → P09 | 无 | **P09 保护**：`0010`/`0011`/`0012` **不得修改** | 指令 §7 · hash 登记 |

**P12 不得依赖**：`P13` seed 数据（索引必须能在**空数据**上建立）。
**P12 不得引入**任何 P13 seed。

---

## 12. 连带同步面（P12 落地时**必须**同步 · 前序血泪教训）

| 面 | 实测 |
|---|---|
| 测试中的索引名断言 | **33 个不同索引名**被测试引用（`uq_*` 21 · `ix_*` 12），落地时须同步 |
| `ix_aimodels_capability` | 测试引用 **3** 处（含"不建立"的负向断言） |
| `tests/architecture/` | **仅 2 文件**（`test_agent_resource_scope_opaque` · `test_dependency_rules`）⇒ **无索引守卫**，P12 若需守卫须新增 |
| head 断言 | 前序实测 **15** 个测试断言 head `0012`（P12 迁移落地后须同步） |
| `FORBIDDEN_TABLES` | **8** 个集成测试含 `events`/`audit_logs`（P10 落地连带面，P12 不涉及） |

---

## 13. Gate（本轮只读验收）

见 `P12_ACCEPTANCE_MATRIX.md` §Gate 与 `p12_prep_gate.log`。

```text
P12 PREP = COMPLETE
P12 DECISION FREEZE = NOT YET
P12 IMPLEMENTATION = NOT AUTHORIZED
P13 IMPLEMENTATION = NOT AUTHORIZED
Runtime Implementation Gate = CLOSED
```

**END OF P12 PREP REPORT（2026-09-25 · READ-ONLY）**

---

## 14. 后续注记（**append-only** · 2026-09-25 Human Decision Freeze）

> **本节为追加注记**：不修改上文任何既有结论与数字；仅登记 Freeze 轮的结果与状态变更。
> 权威载体 = `PLATFORM_DECISION_LOG.md` 的 `# P12 Canonical Model` 区段与**附录 I**。

### 14.1 状态变更

```text
P12 DECISION FREEZE = PASSED        （PREP 轮为 NOT YET）
OQ-P12-01 … OQ-P12-15 = 15/15 FROZEN （PREP 轮为 15/15 PENDING/PROPOSED）
P12 IMPLEMENTATION  = NOT AUTHORIZED（不变）
P13 IMPLEMENTATION  = NOT AUTHORIZED（不变）
Runtime Implementation Gate = CLOSED（不变）
```

### 14.2 与上文 §10 OQ 清单的对应（**编号未变，无重映射**）

`OQ-P12-01`…`15` ↔ `D-P12-01`…`15` **一一对应（15/15）**。
唯一表述差异：§10 中 `OQ-P12-13` 写作「FK 反查补索引闭合范围」· `OQ-P12-14` 写作「P3 候选与 `T-1` 处置」·
`OQ-P12-15` 写作「机制边界与索引所有权」；canonical 主题分别为 **Post-Strategy FK Coverage** ·
**`ix_aimodels_capability` / `T-1`** · **Scope Closure / No Opportunistic Indexing**。
`OQ-P12-15` 的机制边界内容已被 canonical 的「不包括」清单**涵盖** ⇒ **不构成重映射**。

### 14.3 上文 §9 六项 `CF` 的终态（**登记→处置**）

| ID | PREP 轮 | Freeze 轮终态 |
|---|---|---|
| `CF-1` | 登记 | **CLARIFIED** —— 不得据此自动创建 `space_id`/`owner_id`-leading 索引；「documented coverage claim」与「implemented coverage」必须区分 |
| `CF-2` | 登记 | **RESOLVED** —— `D-P12-14`：**DO NOT IMPLEMENT** `ix_aimodels_capability`；`T-1` 关闭为 stale/mismatched design claim |
| `CF-3` | 登记 | **CLARIFIED** —— canonical = **`ix_role_permissions_permission`**；`ix_rp_permission` 仅作历史命名记录；**不 rename** |
| `CF-4` | 登记 | **CLARIFIED** —— B0 缺段**不自动**转成 index requirement；按 `D-P12-02` 单独 adjudicate |
| `CF-5` | 登记 | **RESOLVED** —— `partial index ≠ full FK coverage`；`partial-only` 继续单独统计 |
| `CF-6` | 登记 | **CLARIFIED** —— `P10 schema ownership + P12 index ownership`，**非阶段错误** |

### 14.4 `GAP-INV-P12` 与 `T-1` 终态

```text
GAP-INV-P12 = inventory / adjudication completeness gap（非 implementation list）
            ⇒ 受 per-gap adjudication 治理（D-P12-13）
            ⇒ 24 GAP 在 Implementation Contract 中逐项 CREATE / DEFER / ALREADY COVERED / NOT REQUIRED
            ⇒ 19 个 post-strategy FK 须单独标记来源年代
T-1         = CLOSED as stale / mismatched design claim（D-P12-14）
```

### 14.5 P12 交付面（Freeze 后）

```text
① Frozen P12 indexes
② Explicitly evidenced Event/Audit indexes   → 7 条（ix_events_* 2 + ix_audit_* 5），归 P12
③ Explicitly adjudicated FK reverse-lookup indexes → 24 GAP 逐项裁定
④ Explicitly evidenced ACL / Agent / Tool query indexes
（"不包括"六类见 D-P12-15）
```

### 14.6 本轮仍**不含实施**

`CREATE/ALTER/DROP INDEX = 0` · `DDL = 0` · `DML = 0` · `migration = 0` · `code/test/config = 0` · `commit/tag/push = 0`。
**`P12 IMPLEMENTATION = NOT AUTHORIZED`**。

**END OF P12 PREP REPORT（2026-09-25 · READ-ONLY PREP + DECISION FREEZE 注记）**
