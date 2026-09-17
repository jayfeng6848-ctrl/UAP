# B1-5 — Decision Log（PREP）

Status: **FINAL HUMAN DECISION FREEZE（2026-09-14）**
**9 项全部 FROZEN — A** · `OPEN = 0` · `BLOCKING = 0`
阶段：**B1-5 = P07 Tool 域**（待 D-B15-01 确认编号绑定）

> **核心规则**：本文件不构成任何冻结。所有 `CURRENT = OPEN / PROPOSED` 项**不自动升级为 FROZEN**；冻结只能由 Human Decision 作出。

---

## 汇总表

| ID | 主题 | 性质 | 是否阻塞 B1-5 实施前 | Status |
|---|---|---|---|---|
| **D-B15-01** | B1-5 编号 ↔ P07 Tool 域的绑定确认 | 阶段范围 | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-02** | `tools.tenant_id` 是否加 FK + 删除规则 | 新增约束（**B0 冲突 C-1**） | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-03** | immutable trigger 命名口径统一（冲突 C-2） | 文档一致性 | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-04** | `tool_versions.status` 取值域是否约束 | **不变式锚点** | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-05** | `tools.key` 是否补格式 CK | 新增格式契约 | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-06** | 索引 / UQ 计数口径（表达式唯一索引归属） | 计数口径 | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-07** | B1-5 是否沿用 B1-4 的 O-1-A canonical 口径 | 计数口径 | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-08** | `tool_versions.risk_level` / `timeout_ms` 是否补快照 CK | 新增约束 | 否（已关闭） | ✅ **FROZEN — A** |
| **D-B15-09** | `handler_ref` 语义边界（不引入解析/加载机制） | 边界确认 | 否（已关闭） | ✅ **FROZEN — A** |

---

## D-B15-01 — B1-5 编号 ↔ P07 绑定 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | 全库搜索 `B1-5` = **0 命中**；项目**无 roadmap 文档**。本轮"B1-5"是外部引入的编号，其**实质范围**必须由冻结 phase plan 推导，而该推导严格来说不是"字面冻结" |
| **事实依据** | `SCHEMA_DEPENDENCY:167-168`（P06=Resource/ACL · **P07=Tool**）· `B0_GATE_REPORT:45`（phase 拓扑）· `B1-4_DECISION_LOG:14`「**P06（= B1-4）**」· `B1-4_SCOPE:42`「Tool / AI / Agent 域 \| **P07** / P08 / P09」· `B1-4_DEPENDENCY:130`「**P07 Tool**」 |
| **实测支撑** | P01–P06 **全部已建**（17 张业务表对账无缺）；计划外仅 `platform_memberships`/`platform_state`（B1-3 hardening） |
| **推导** | `P06 = B1-4`（已接受）⇒ 下一个未执行 phase = `P07 = Tool` ⇒ **B1-5 = P07** |
| **风险** | 编号映射**非严格 1:1**：B1-1 覆盖 P01+P02 · B1-2 覆盖 P03+P05 · B1-3 覆盖 P04(+hardening)。故 `B1-5 = P07` 是**强推导但非字面冻结** |
| **Options** | **A**：确认 `B1-5 = P07 Tool 域`（采纳本推导，scope = `tools`/`tool_versions`/`tool_permissions`）<br>**B**：指定其他范围（须显式给出 phase 与表清单）<br>**C**：先补一份 roadmap 文档再定 scope（PREP 暂停） |
| **Recommended** | **A**（唯一与冻结 phase plan 自洽的选项） |
| **需 Human 裁定** | ✅ **已裁定** |
| **Human Decision（2026-09-14）** | **A —— FROZEN**。定义：*本项目当前阶段编号采用已建立的 B1-x → Phase 映射规则；B1-4 已对应 P06，因此下一阶段 B1-5 对应 P07 Tool。* 明确 `B1-5 = P07 Tool`。**约束**：不得据此改变历史 B0 文档中已有的 phase 定义 |
| **Status** | **FROZEN — A** |

---

## D-B15-02 — `tools.tenant_id` 的 FK 与删除规则 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | `tools.tenant_id` 是否加 FK、删除规则如何——**B0 文档内部冲突** |
| **冲突取证（C-1，2026-09-14 精化）** | **A（支持 FK）**：`ER_MODEL.md:276` = `uuid tenant_id FK "nullable = platform"` —— 全库**唯一**明确标注 FK 的来源；但其头部声明"图中只画主键、外键与关键字段"，属 ER 图示。<br>**B（不支持 FK）**：`SCHEMA_DEPENDENCY.md:51` 的 **FK 列 = `—`**（表格列结构为 `\| 表 \| 依赖 \| FK \| root \|`），依赖列注明"**无实际 FK 强制**"；对照 `resources` 行 FK 列写 `tenant_id → tenants.id RESTRICT`（P2-03）。<br>**C（表述不完整）**：`CONSTRAINT_MATRIX.md` 的 `tools` 段**完全没有 FK 行**（仅 PK/UQ/CK/NN/NULL）；`CORE_DOMAIN_MODEL.md:322` 的 `FK` 行写 `tenant_id NULL（NULL = 平台内置）`，**无 → 目标、无删除规则**（对照 `resources` 写全）。<br>**D（删除策略）**：`CORE §11.1` CASCADE 白名单**不含** `tenants → tools`；"明确禁止 CASCADE"列表含 `tenants → spaces` / `tenants → resources` ⇒ 若加 FK，按"业务实体一律 RESTRICT"应为 **RESTRICT**。<br>**E（对照）**：`tool_executions` 同样把 `tenants` 列入依赖列，但 FK 列**无** `tenant_id → tenants.id` —— 与 tools 同模式。<br>**证据加权（仅陈述，不裁定）**：不支持/未列 FK 的来源 = **3**（SCHEMA_DEPENDENCY / CONSTRAINT_MATRIX / CORE 的模糊写法）；支持 = **1**（ER_MODEL）。 |
| **Options** | **A**：加 FK `tools.tenant_id → tenants.id`，`ON DELETE RESTRICT`（符合 `CORE §11.1`「业务实体一律 RESTRICT」；NULL 行不受影响）<br>**B**：加 FK，`ON DELETE CASCADE`（不符合白名单 —— `CORE §11.1` 未把 `tenants → tools` 列入 CASCADE 白名单）<br>**C**：**不加** FK（采纳 `SCHEMA_DEPENDENCY` 口径；租户级 Tool 的存在性仅由应用层保证） |
| **影响** | A：+1 FK；删租户被 Tool 阻塞（需先 disable/purge Tool）· B：删租户静默删除租户私有 Tool（**不建议**）· C：无 FK，出现"指向不存在租户的 Tool"的可能性 |
| **Recommended** | **A**（与 ER_MODEL / CONSTRAINT_MATRIX 一致，且满足 P2-03 RESTRICT 原则）—— 但这会使 `SCHEMA_DEPENDENCY:51` 的表述需**同步修订**（属冻结文档修订，需批准） |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：`tools.tenant_id NULL → tenants.id` **`ON DELETE RESTRICT`**；`tenant_id IS NULL` = **platform-level tool**（语义不变）。**约束**：① **不得**把 NULL 改成 NOT NULL；② **不得**引入 `tenant_id → tenants` 的 CASCADE；③ **不得**因本决定改变 platform-level tool 语义 |
| **B0 同步结果（B-5 授权范围，已完成）** | `STEP1B_SCHEMA_DEPENDENCY.md:51`（FK 列 `—` → `tenant_id NULL → tenants.id RESTRICT`；依赖列去掉"无实际 FK 强制"）· `STEP1B_CONSTRAINT_MATRIX.md`（`tools` 段**新增 FK 行**）· `CORE_DOMAIN_MODEL.md:322`（FK 行补 → 目标 + `ON DELETE RESTRICT`）· `ER_MODEL.md:276`（补 `; ON DELETE RESTRICT`）。**未改动** phase / 其他 Tool Schema / `tool_executions` / Agent / AI / Event |
| **Status** | **FROZEN — A** |

---

## D-B15-03 — immutable trigger 命名口径 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | 同一 trigger 在 B0 文档中有两个名字（**冲突 C-2**） |
| **冲突取证** | `TRIGGER_INVENTORY:164`：`tg_agent_versions_immutable` / **`tg_tool_versions_immutable`**（逐表命名）<br>`SCHEMA_DEPENDENCY:240`：统一名 **`tg_version_immutable`**（agent_versions/tool_versions 共用一个名） |
| **影响** | trigger 名是 DDL 级标识；两名并存会导致实现与文档不一致、测试断言歧义 |
| **Options（PREP 原编号）** | **A（PREP）**：逐表命名 `tg_tool_versions_immutable` · **B（PREP）**：统一名 `tg_version_immutable` |
| **PREP Recommended** | A（PREP）—— **已被本轮 Human Decision 覆盖**（如实记录） |
| **全库命中检查（2026-09-14）** | `tg_version_immutable`：**1 处**（`SCHEMA_DEPENDENCY:240`，B0）· `tg_tool_versions_immutable`：**1 处**（`TRIGGER_INVENTORY:164`，B0）+ B1-5 PREP 8 处 · `tg_agent_versions_immutable`：1 处（同上 inventory 行）。**无任何已实现对象依赖这两个名字**（均属 DESIGN 阶段命名，`0001–0007` 中 0 命中）⇒ 无"既有依赖"反证 |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：采用 **`tg_version_immutable`**（= PREP Options 的 B）。理由：B0 已存在该命名口径；`tool_versions` 明确属 version immutable 家族；避免 B0→B1-5 继续漂移 |
| **⚠️ 残留项（如实报告，本轮未改 B0）** | 采用 `tg_version_immutable` 后，`TRIGGER_INVENTORY:164` 的**逐表命名**（`tg_agent_versions_immutable` / `tg_tool_versions_immutable`）与之不一致，且既有 3 个已实现 trigger 均为**逐表命名**（`tg_resources_set_updated_at` / `tg_resources_tenant_space_consistency` / `tg_acl_subject_types_protect`）。**该 B0 文档需同步修订（属另案，须 Human 授权）**，否则产生新的文档漂移 |
| **Status** | **FROZEN — A** |

---

## D-B15-04 — `tool_versions.status` 取值域 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | `tool_versions.status` 列存在且 NN，但**取值域从未冻结**；而 `tg_version_immutable` 的判定锚点正是 `status='published'` ⇒ **不变式的锚点无冻结依据** |
| **原文证据（2026-09-14）** | ① `CONSTRAINT_MATRIX.md:225-233`（`tool_versions` 段）：仅 PK/FK/UQ/NN/不变性 —— **无 CK 行**<br>② `CORE_DOMAIN_MODEL.md:334`（fields）列出 `status`，但 § 中**无 CK**（对照 `:325` `tools` 有 CK、`:291` `ai_routes` 有 CK、`:442` `audit_logs` 有 CK）<br>③ `STEP1A_DESIGN_REPORT.md:67`：仅"published 后**不可变**"，未给取值域<br>④ 全库 `status IN (...)` 词表先例共 12 处（users/identities/credentials/devices/sessions/tenants/spaces/memberships/…），**均无 tool_versions**<br>⑤ **⚠️ 纠正（2026-09-14 复核发现）**：同族的 `agent_versions` **有** CK —— **`status IN ('draft','published','deprecated','revoked')`**（`CORE_DOMAIN_MODEL.md:302` · `STEP1B_CONSTRAINT_MATRIX.md:281`）。
**先前记录的「agent_versions 同样无 status CK」属误判，特此更正。** 真实情况：**同族存在一个先例词表**，`tool_versions` 是该家族中**唯一缺失者**。<br>**结论：现有资料未直接给出 tool_versions 词表，但同族先例可作为候选证据（先例词表 = draft / published / deprecated / revoked）。** |
| **影响** | 不变性 trigger **必须**判断 `status='published'`；若取值域不冻结，trigger 的判定锚点即无冻结依据 |
| **Options** | **A**：不新增 CK（保持与 B1-4 `action` 同口径：只存不约束；trigger 仅按字面 `'published'` 比较）<br>**B**：加结构性 CK（如 `status IN ('draft','published','deprecated','revoked')`）—— **属新增语义契约**，需批准<br>**C**：defer 到 Agent/版本管理阶段（与 `agent_versions` 一并冻结，避免两表口径分叉） |
| **Recommended** | **C**（与 `agent_versions` 同族，成对冻结更一致；B1-5 仅实现 trigger 的字面判定） |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：`tool_versions.status` **不建立完整状态枚举 CHECK**（**`status CHECK = 0`**）。当前阶段**只冻结 `published`** 作为 immutable lifecycle 的**语义锚点** ⇒ 一旦 `tool_versions.status = 'published'`，该 version 必须进入不可修改 / 不可删除的 published immutable 状态。**明确边界**：这**不是** `status IN ('draft','published','disabled',…)`；**不得自行创造** draft / active / disabled / archived / deprecated / released 等**任何无证据**的状态词。immutability 由 **`tg_version_immutable`** 负责（DB 层无 status 取值约束） |
| **⚠️ 裁定后补充发现（如实告知，供复核）** | Human 裁定作出后复核发现：**同族 `agent_versions` 存在 status CK** `('draft','published','deprecated','revoked')`（见上「原文证据」⑤的纠正）。
**后果**：按 D-B15-04 = A 实施后，`tool_versions`（零 CK）与 `agent_versions`（4 值 CK）在 **status 约束上将不一致** —— 这是 Human 明确选择的「最小约束」策略的**已知代价**。
**候选若需对齐**：可另案批准补 `ck_tool_versions_status`（属新增约束，**须 Human 显式授权**，不得自行添加）。
**本轮未自行补 CK，未改动裁定。** |
| **Status** | **FROZEN — A** |

---

## D-B15-05 — `tools.key` 格式约束 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | `tools.key` 只有**大小写不敏感唯一**（`lower(key)`），**无格式 CK** |
| **原文证据（2026-09-14）** | ① `CONSTRAINT_MATRIX.md:215-222`（`tools` 段）：CK 仅 risk_level/timeout_ms/idempotency_mode/audit_policy —— **无 key 格式 CK**<br>② `CORE_DOMAIN_MODEL.md:324`：UQ 仅 `lower(key)` 两类部分唯一<br>③ **有**格式正则的先例：`permissions.key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'`（`CONSTRAINT_MATRIX:120`）· `acl_subject_types.key ~ '^[a-z][a-z0-9_]{1,31}$'`<br>④ **无**格式正则的先例：`spaces.key`（仅 `uq_spaces_key on (tenant_id, lower(key))`）· `tenants.slug`（仅 UQ）· `tools.key`<br>⇒ **registry key 的格式约束在 B0 中并不统一**，无统一规范覆盖 Tool<br>**⚠️ 附注：用户指令 §六 引用 `D-B14-13` 作为 key 规范来源 —— 经核对，`D-B14-13 = "B1-4 的 seed 与 trigger 交付清单（重新裁定）"`（`B1-4_DECISION_LOG:175`），与 key 规范无关（疑为误引；key 相关论述见 D-B14-08 / `permissions.key` 正则）** |
| **Options** | **A**：零新增（保持现状；key 由注册者定义）<br>**B**：补格式 CK（沿用 `permissions.key` 正则 `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$` 或 `acl_subject_types` 正则）—— 属新增格式契约 |
| **Recommended** | **A**（冻结文档未定义 ⇒ 不自行发明；如需格式约束，应与 `permissions.key` / Tool 命名空间一并裁定） |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：`tools.key` **不新增 regex / format CHECK**，保持 **opaque application identifier**。**不得**因 `permissions.key` / `acl_subject_types.key` 存在 regex，就推导 `tools.key` 必须拥有同样 regex；**不得**新增 `^[a-z]…` 或任何其他格式约束 |
| **Status** | **FROZEN — A** |

---

## D-B15-06 — 索引 / UQ 计数口径 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | `uq_tool_perm` 含表达式 `COALESCE(version_id, …)` ⇒ PostgreSQL **不允许**作为 `UNIQUE CONSTRAINT`，**必须**是 unique **index**。这导致"UQ × N / INDEX × M"的摘要口径可能出现 B1-4 式的漂移（B1-4 曾出现 `CK ×5` vs 实际 `×6`） |
| **处置** | `B1-5_SCHEMA_DESIGN.md` §5 **已显式标注**：UQ 分"constraint 形式（1 个）"与"index 形式（3 个）"，并在实施时以 `pg_constraint` / `pg_indexes` **实测为准** |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：采用 **`UNIQUE CONSTRAINT = 1` · `UNIQUE INDEX = 3`** 口径；所有 B1-5 文档必须明确「UQ 统计区分 constraint-form 与 index-form；**表达式唯一性不计入 UNIQUE CONSTRAINT**」 |
| **Status** | **FROZEN — A** |

---

## D-B15-07 — canonical 计数口径沿用 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | B1-4 的 `O-1 = FROZEN — A`（Canonical Total = **正式表格行数**）是 **B1-4 专属**决策。B1-5 是否沿用同一规则？ |
| **本文件做法** | 已按同一规则给出 **Canonical Total = 39**（基础 38 + §7 决策行 1），并在 `B1-5_TEST_MATRIX.md` §0.2 显式声明"**沿用需 Human 确认**" |
| **Options** | **A**：沿用 O-1-A 口径（表格行 = canonical；登记项不计入）<br>**B**：为 B1-5 另立口径（须显式定义） |
| **Recommended** | **A**（保持一致，避免跨阶段计数口径分叉） |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：B1-5 沿用 O-1-A 原则（**canonical test rows 与 conditional / registration / future rows 分离**），使用**独立编号空间**。确立：`Base = 38` · `Decision-dependent = 1` · **`Canonical = 39`** · `Registration = 6`（**登记项不得混入 canonical**） |
| **Status** | **FROZEN — A** |

---

## D-B15-08 — `tool_versions` 快照列的 CK 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | `tools` 有 `risk_level` / `timeout_ms` 的 CK，但 `tool_versions` 同名列**无 CK**（值由发布时从 `tools` 快照） |
| **原文证据（2026-09-14）** | ① `CONSTRAINT_MATRIX.md:225-233`（`tool_versions` 段）：**无 CK 行** ✅ 确认<br>② `CORE_DOMAIN_MODEL.md:334` fields 含 `risk_level`/`timeout_ms`，但该表 § **无 CK**<br>③ 对照：`tools`（`:325`）有 CK；`audit_logs`（`:442`）有 CK；`ai_routes`（`:291`）有 CK<br>④ **P08/P09 依赖检查**：全库无任何文档声明 P08/P09 依赖 `tool_versions.risk_level` 或 `timeout_ms` 的**取值域**；`tool_executions.risk_level` 在 NULL 列（`:354`）且**无 CK**<br>⑤ 结构性保护：`tg_version_immutable` 只保证 published 行不可改，**不校验取值**<br>⇒ 现有资料**未规定**该表 CK；是否补属**新增约束** |
| **Options** | **A**：不加（快照值由应用层从合法 `tools` 行复制；DB 不重复校验）<br>**B**：加同域 CK（保证快照值即使被绕过应用层也不会越界） |
| **Recommended** | **A**（冻结文档未给该表 CK ⇒ 不自行新增；如需，B1-5 应作为**新增约束**显式批准） |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：**不新增 snapshot value-domain CHECK** —— `risk_level` / `timeout_ms` / `idempotency_mode` / `audit_policy` 本轮**均不新增额外 CK**（`tool_versions` 保持**零 CK**）。**不得**从 `tool_executions` / Agent / P08 / P09 **反向推导** P07 的取值域。**B1-5 保持 Schema 最小约束** |
| **Status** | **FROZEN — A** |

---

## D-B15-09 — `handler_ref` 语义边界 【✅ FROZEN — A（2026-09-14）】

| 项 | 内容 |
|---|---|
| **Problem** | `tool_versions.handler_ref`（NN，text）指向"处理器"。若在 B1-5 引入 handler 解析/加载/插件注册机制，将越界（违反"不引入 Plugin registration API"） |
| **本文件立场** | **不引入**任何解析、加载、注册机制；`handler_ref` 仅为**文本引用列**（`B1-5_API_DESIGN.md` §5 已声明） |
| **Human Decision（2026-09-14）** | **A —— FROZEN**：*B1-5 仅存储 `handler_ref` 文本引用，不定义解析、加载、执行、插件注册或 runtime discovery 机制。* 这些能力留待后续阶段 |
| **Status** | **FROZEN — A** |

---

## 未列入本文件的项（明确不变）

以下**不是** B1-5 的 Decision，因其已在既有阶段冻结或明确不适用：

| 项 | 依据 |
|---|---|
| `tool_permissions.effect ∈ ('allow','deny')` | **已冻结**（`CONSTRAINT_MATRIX:242`）；B1-5 只执行，非新增 |
| `tools → tool_versions` / `tools → tool_permissions` CASCADE | **已冻结**（`CORE §11.1` CASCADE 白名单） |
| G/H/I/J 的 phase | **已冻结 = P09 后**（`TRIGGER_INVENTORY:163-166`）；**不得**因 B1-4 已有 ACL 而拉入 B1-5 |
| `tool_executions` 归属 | **已冻结 = P09**（`SCHEMA_DEPENDENCY:170` + §5 调整说明②） |
| B1-5 零 seed | **已冻结**（`SCHEMA_DEPENDENCY:193`） |
| 不启用 RLS / 不实现授权求值 | **已冻结**（B1-4 同口径，延续） |

---

## Gate

```
D-B15-01 … D-B15-09 = ALL FROZEN — A
OPEN Decision = 0 · BLOCKING Decision = 0

B1-5 PREP = COMPLETE
B1-5 HUMAN DECISION FREEZE = COMPLETE
B1-5 IMPLEMENTATION = READY BUT NOT STARTED
```
