# P12 — DECISION RESOLUTION（Indexes）

> **Status**: `FROZEN` —— **`P12 DECISION FREEZE = PASSED`（2026-09-25 · Human Decision）**。
> 本文档承载 `OQ-P12-01` … `OQ-P12-15` 的逐项决议材料。
> **15 项全部 `HUMAN DECISION = FROZEN`** · **`STATUS = FROZEN`**（逐项正文见下；权威载体为
> `PLATFORM_DECISION_LOG.md` 的 `# P12 Canonical Model` 区段与**附录 I**）。
> **`RECOMMENDED ≠ FROZEN`** —— PREP 的推荐方向**本身**不构成冻结；本轮的冻结**仅**来自 Human Decision。
> **`P12 IMPLEMENTATION = NOT AUTHORIZED`** ·
> **`P13 IMPLEMENTATION = NOT AUTHORIZED`** · **`Runtime Implementation Gate = CLOSED`**。
>
> **本轮不含任何实施**：`CREATE/ALTER/DROP INDEX = 0` · `DDL = 0` · `DML = 0` · migration/code/test/config = 0 ·
> `commit/tag/push = 0`。本组条目**不产生任何实施授权**（Charter §6）。
>
> **编号对账（本轮无重映射）**：`OQ-P12-01`…`15` ↔ `D-P12-01`…`15` **一一对应（15/15）**。
> 仅 `OQ-P12-15` 侧重由 PREP 的「机制边界与索引所有权」收敛为 **Scope Closure / No Opportunistic Indexing**；
> PREP 的机制边界内容已被其「不包括」清单**涵盖** ⇒ **非重映射，无需重排**（对照：P11 轮曾发生 06/07 对调）。

---

## 0. 本轮基线

```text
HEAD          = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e
TAG           = UAP-V0.1.8-AUTHORIZATION
ALEMBIC HEAD  = 0012_authz_enforcement
D-PLAT-09     = P10 → P11 → P12 → P13 → Runtime（FROZEN / NOT SUPERSEDED）
P10 FREEZE    = PASSED      P11 FREEZE = PASSED
P12 本轮       = PREP（零实施）
```

**实测基线（`p12_inventory.log`）**

```text
索引对象总数        = 57（独立创建 52 + 内联 UNIQUE CONSTRAINT 隐式 5）
FK 约束             = 54（覆盖 25 · partial-only 5 · GAP 24）
GAP ondelete 分布   = CASCADE 6 · RESTRICT 11 · SET NULL 7
GAP 时代切分        = 策略文档之后 19 · 策略文档时代 5
分区表              = 1（ai_request_logs）
```

**本轮冻结（2026-09-25 · HUMAN DECISION RESOLUTION）**

```text
P12 HUMAN DECISION FREEZE = AUTHORIZED
OQ-P12-01 … OQ-P12-15     = 15 / 15 FROZEN（0 DEFERRED · 0 SUPERSEDED · 0 unresolved）
D-P12-01 … D-P12-15       = 写入 PLATFORM_DECISION_LOG.md 并置 FROZEN（附录 I 登记）

P12 canonical scope       = ① Frozen P12 indexes
                            ② Explicitly evidenced Event/Audit indexes
                            ③ Explicitly adjudicated FK reverse-lookup indexes
                            ④ Explicitly evidenced ACL / Agent / Tool query indexes
P12 implementation         = NOT AUTHORIZED
```

---

## 1. `OQ-P12-01` — Canonical Index Inventory

| 字段 | 内容 |
|---|---|
| **Question** | P12 的**权威索引清单**由谁承载？以何口径对账？B0 `STEP1B_INDEX_STRATEGY.md` 是否仍为唯一权威，还是须承认「分阶段策略（B1-2/B1-3/…）+ B0」的**多文档合成**口径？ |
| **Current Evidence** | 实测：索引声明分散于 **B0 `STEP1B_INDEX_STRATEGY.md` §1/§3/§4/§5** · **`STEP1B_B1_2_INDEX_STRATEGY.md`** · **`STEP1B_B1_3_INDEX_STRATEGY.md`（含 R3/R4 增补）** · 各 migration docstring（`0007`「indexes (8)」· `0008` · `0010` · `0011`「8 个索引对象」）；四份来源**逐项对账一致**（§3.2）。但 B0 §1 **无 `platform_memberships` 小节**（`CF-4`），且 B0 成文早于 `0008`/`0010`/`0011`。 |
| **Option A** | B0 为**唯一权威**，分阶段文档仅为其**分解**；缺项（`platform_memberships`）由后续阶段文档补足，**B0 不回改** |
| **Option B** | 建立**新统一索引清单文档**（`P12_INDEX_LEDGER.md`）作为 P12 权威，B0 降为历史设计来源 |
| **Option C** | 维持多文档合成，P12 仅在 `P12_*` 包内**只读汇总**，不新建权威载体 |
| **Engineering Impact** | A：0 新文档、零漂移风险；但 B0 缺项**永久**由旁文档承担。B：单一权威、对账最简；但**引入第三套清单**，与前序「不回改 B0」纪律需协调。C：最小动作；但"权威分散"本身即是 `CF-3`/`CF-4` 的成因 |
| **Compatibility** | A ✅ 与「历史迁移/历史文档不回改」一致。B ⚠ 须避免形成第二套权威（前序教训：**复制必须成为受验证的复制**）。C ✅ 最保守 |
| **Future Runtime Impact** | 决定 Runtime / 运维（`pg_stat_user_indexes` 季度清理）引用哪份清单 |
| **Recommended Direction** | **Option C + A 之兼容读法**：**不新建权威文档**；承认「B0 §1/§3/§4/§5 + B1-2/B1-3 分阶段策略 + migration 实测」为**合成权威**，并在 P12 落地时以**对账表**（`P12_ACCEPTANCE_MATRIX`）作为可执行 ledger。理由：前序「文档不回改」纪律 + 禁止形成第二套权威 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：采用 PREP 实测 inventory 为 P12 基线（**57 = 52 + 5**）；既有索引 **NOT recreated / NOT renamed / NOT merged / NOT deleted**；P12 只处理 **missing / additional indexes** → `D-P12-01`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 2. `OQ-P12-02` — Query Evidence Standard

| 字段 | 内容 |
|---|---|
| **Question** | P12 候选索引的**证据等级**如何定？FK 反查项（PG 语义级强制）是否与「查询性能」项**同级**？ |
| **Current Evidence** | `INDEX_STRATEGY` 首部：**「只为已知查询模式建索引」**；B1-2/B1-3 要求每个索引回答 **Query Pattern / Why / Cardinality / Why Existing Cannot Serve**；§3 把 FK 反查列为**强制清单**并注明「进入 P12」（`:202`） |
| **Option A** | **五级证据制**（frozen Decision > schema contract > documented query pattern > test query > measured requirement），FK 反查归入**①（PG 语义级）**，与性能项同级但**理由类别不同** |
| **Option B** | FK 反查**独立成类**（结构完整性），不与查询性能混合计数 |
| **Option C** | 仅接受 ①–③（拒绝 ④⑤） |
| **Engineering Impact** | A：口径统一、易审计。B：**语义最清晰**（"结构必需" vs "性能优化"不混淆）。C：过严 ⇒ 事实日志类（`ai_request_logs`）无测试查询时被排除，反致全扫 |
| **Compatibility** | A/B ✅ 均不违反 `INDEX_STRATEGY` 原则。C ⚠ 与 §3「FK 反查强制」精神冲突 |
| **Future Runtime Impact** | 决定后续（Runtime/业务）新增索引的门槛与审计强度 |
| **Recommended Direction** | **Option B**：把 **①结构完整性（FK 反查/唯一性语义）** 与 **②查询性能** 分为**两类**分别举证；性能类禁用「未来可能会查」为唯一依据 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：每个新增 index **必须具备明确 query evidence**（五级优先级）；「future may query」/「database best practice」/「**FK exists**」/「performance safety」**不得单独**构成依据 ⇒ **`GAP ≠ automatic CREATE INDEX`** → `D-P12-02`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 3. `OQ-P12-03` — Tenant / Space Index Policy

| 字段 | 内容 |
|---|---|
| **Question** | 是否允许**机械套用** `(tenant_id, id)` / `(tenant_id, status)` / `(tenant_id, created_at)` 形态？tenant/space 前缀索引的**准入条件**是什么？ |
| **Current Evidence** | 实测 24 个 tenant 打头索引对象；`INDEX_STRATEGY §2`：**「多索引共享同一前缀（如 resources 三索引均 tenant 打头）——可接受：列顺序不同，服务不同查询；不合并」**；**「低基数列单列索引（status/scope/risk_level）**不建**」**；`B1-2 §1` 判 `ix_tenants_status` **不建**；`B1-3 §1` 判 `ix_roles_status` **不建** |
| **Option A** | **沿用既有三条铁律**：① 每个 tenant/space 前缀组合必须有**documented query pattern** ② 低基数列单列**不建** ③ 共享前缀**不视为冗余** |
| **Option B** | 收紧：新增 tenant 打头索引须证明**既有多列索引无法服务**（强制填「Why Existing Cannot Serve」） |
| **Option C** | 放宽：允许为多租户隔离查询预置 `(tenant_id, …)` 组合 |
| **Engineering Impact** | A：与既有 24 个对象一致、零回溯。B：最强、但已落地对象**无法回溯**（只约束 P12 新增）。C：**index inflation**，被 §2 明文禁止 |
| **Compatibility** | A ✅ B ✅（仅前瞻） C ❌ 违反 `INDEX_STRATEGY §2`「不建」条款 |
| **Future Runtime Impact** | 决定多租户查询性能面与索引维护成本 |
| **Recommended Direction** | **Option B**（在 A 三条铁律之上，对 P12 **新增**对象强制「Why Existing Cannot Serve」举证）|
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**不用机械 tenant/space 前缀规则**；仅在**明确查询模式**下建组合索引；**不得**引入新的 authorization semantics → `D-P12-03`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 4. `OQ-P12-04` — Unique Index Semantics

| 字段 | 内容 |
|---|---|
| **Question** | 唯一性规则在 P12 中**是否允许**以新索引形式（再）表达？何时必须保持 `UNIQUE CONSTRAINT` 形式？ |
| **Current Evidence** | **已冻结先例**：`D-B15-06 = A` / `D-B16-07 = A` / `D-P09-16（ND-04）`——**「表达式唯一性必须是 unique INDEX，不能是 UNIQUE CONSTRAINT」**（实测：`uq_ai_routes` · `uq_ai_policies` · `uq_agent_perm` · `uq_tool_perm` 均为 unique INDEX）；**纯列唯一** ⇒ `UNIQUE CONSTRAINT` 形式（实测 5 个内联：`uq_resource_perm` · `uq_tool_versions` · `uq_ai_providers_key` · `uq_ai_models` · `uq_agent_versions`）；`D-P09-04 = A`：**部分唯一 ⇒ UNIQUE INDEX，不得伪装为 CONSTRAINT** |
| **Option A** | **完整沿用既有二分法**：纯列唯一 ⇒ CONSTRAINT；表达式唯一 / 部分唯一 ⇒ unique INDEX。P12 **不新增**唯一性对象（P12 交付面为**已冻结但未落地**者） |
| **Option B** | P12 统一收敛为 unique INDEX |
| **Option C** | P12 允许按需新增唯一约束以"加固"既有表 |
| **Engineering Impact** | A：零回溯、与 3 条冻结决策一致。B：**改写已发布对象形式**（`ALTER` CONSTRAINT→INDEX）⇒ 需新 migration + 破坏性。C：**越界**（唯一性属 schema/constraint 阶段，且 P12 = 索引 ≠ 约束重构） |
| **Compatibility** | A ✅ B ❌（违反 `D-B15-06`/`D-B16-07` 的**形式即语义**裁定） C ❌ 违反 P12 scope |
| **Future Runtime Impact** | 决定幂等/唯一语义的可预测性 |
| **Recommended Direction** | **Option A** —— 二分法**原样保持**；P12 **不新增**唯一性对象；`uq_tool_exec_idem` 的 **UNIQUE INDEX（部分）** 形式作为 `D-P09-04` 的既有落地**不动** |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：现有 `UNIQUE` / `UNIQUE INDEX` 语义**全部保持**；**不得**以索引替换约束 / 以约束替换索引 / 改唯一语义；部分唯一 predicate 保持 → `D-P12-04`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 5. `OQ-P12-05` — Partial Index Semantics（**含 FK-scan 不可用性**）

| 字段 | 内容 |
|---|---|
| **Question** | 部分索引的**语义边界**如何界定？**是否承认"部分索引不可服务 FK 完整性检查"**这一机制事实？部分唯一索引（NULL 分支）的唯一性边界如何陈述？ |
| **Current Evidence** | **本轮实测（`CF-5`）**：**5 个 partial-only** —— `credentials.identity_id`（`uq_credentials_active_password`）· `roles.space_id`（`uq_roles_space`）· `roles.tenant_id`（`uq_roles_tenant`）· `tool_executions.tool_id`（`uq_tool_exec_idem`）· `tools.tenant_id`（`uq_tools_tenant`）；**PG 仅在谓词蕴含时可用部分索引**，FK 检查使用**无谓词**查询 ⇒ **不可用**。部分唯一索引的 NULL 分支不受约束（`uq_tool_exec_idem`：`idempotency_key IS NULL` 行可任意多） |
| **Option A** | **明确冻结该机制事实**：部分索引**从不**计入 FK 反查覆盖；部分唯一索引的**唯一性仅覆盖谓词为真行**；P12 判据须据此修订 |
| **Option B** | 仅在"新证据"下承认，不写成通则 |
| **Option C** | 视为 PostgreSQL 实现细节，不入 P12 判据 |
| **Engineering Impact** | A：判据正确、消除 `CF-5` 假覆盖。B：同类缺陷可复发。C：**错误留档** ⇒ 后续误判"已有索引" |
| **Compatibility** | A ✅（纯澄清，不改任何既有对象）。C ❌（与 §3 FK 反查强制口径冲突） |
| **Future Runtime Impact** | 直接决定 24 GAP + 5 partial-only 的**去重后真实补索引数** |
| **Recommended Direction** | **Option A** —— 把「**部分索引不服务 FK 检查**」写为 P12 判据通则；**不修改**任何既有部分索引（`D-P09-04` 语义不动） |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**Partial index 可服务查询，但不能据此声称完整覆盖 FK reverse lookup / integrity-support requirement**；**`partial-only = 5`** 继续作为**独立分类**，**不得**误计为 full coverage → `D-P12-05`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 6. `OQ-P12-06` — Idempotency Index

| 字段 | 内容 |
|---|---|
| **Question** | `uq_tool_exec_idem` 的 P12 处置：**保持不动** / 补配套索引 / 改造？idempotency 语义与 FK 反查是否**分离**？ |
| **Current Evidence** | `D-P09-04 = A`（FROZEN）：`uq_tool_exec_idem = (tool_id, idempotency_key) WHERE idempotency_key IS NOT NULL`，**必须是 UNIQUE INDEX**（不得伪装 CONSTRAINT）；实测已落地（`0011`），且**测试引用 5 处**；同时 `tool_executions.tool_id` FK 为 `RESTRICT` 但 `uq_tool_exec_idem` **为部分索引 ⇒ 不服务 FK 检查**（`CF-5`）；`D-AGENT-08`（FROZEN）规定**双层幂等**（Run + Tool）与 Key/Scope/TTL/Collision/Replay/Result Reuse 六要素——**Agent Runtime 侧幂等表**属 Runtime 阶段（`D-AGENT-13`：`agent_runs`/`agent_run_steps` 为 **P10 之后的 Runtime 设计**，非 P12） |
| **Option A** | **保持 `uq_tool_exec_idem` 不动**（`D-P09-04` 已冻结）；把 `tool_executions.tool_id` 的 FK 反查需求**单列**进入 `OQ-P12-13` 的补索引集合 |
| **Option B** | 将 `uq_tool_exec_idem` 改为**非部分**唯一索引 |
| **Option C** | P12 为 Agent Runtime 幂等预置索引 |
| **Engineering Impact** | A：零回溯、职责清晰。B：**改变幂等语义**（`idempotency_key IS NULL` 行将被迫唯一 ⇒ 破坏"可缺省"）⇒ 违反 `D-P09-04`。C：**越界**（Runtime 表尚不存在 ⇒ 依赖 `D-PLAT-09` 更晚阶段） |
| **Compatibility** | A ✅ B ❌（supersede `D-P09-04`） C ❌（违反 `D-PLAT-09` 与 P12 scope） |
| **Future Runtime Impact** | 决定 `POST /agent-runs` 幂等（`D-AGENT-08`）能否复用既有锚点 |
| **Recommended Direction** | **Option A** —— 幂等索引**保持不动**；`tool_id` FK 反查需求归入 `OQ-P12-13`；**P12 不触碰** Runtime 幂等设计 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**保留 `uq_tool_exec_idem`**（`UNIQUE` + `predicate = idempotency_key IS NOT NULL`）语义**不变**；**不得**再建等价 idempotency index → `D-P12-06`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 7. `OQ-P12-07` — Agent / Tool Lookup Indexes

| 字段 | 内容 |
|---|---|
| **Question** | P09 已交付 8 个索引对象；其 **19 个 FK GAP**（`agent_permissions`×3 · `agent_versions`×1+1 · `agents`×3 · `tool_executions`×3 · `tool_permissions`×2 · `tool_versions`×1 …）在 P12 中如何处置？ |
| **Current Evidence** | `P09_DECISION_LOG:248` / `P09_SCOPE:29` / `P09_SCHEMA_DESIGN:112` **显式**：「**不额外补 FK 列索引**（FK 反查补索引进入 **P12**）」；`D-P09-15（ND-03）`：索引权威 = `STEP1B_INDEX_STRATEGY`，交付 8 个对象，不额外补 FK 列索引；`INDEX_STRATEGY §3:200`将「`agents.owner_id`」标 **P3**；`§3:202`「补充索引进入 **P12**」 |
| **Option A** | 按 `INDEX_STRATEGY §3` 的**筛选口径**（"父行会被删除?"+"风险"）**逐项**裁定 19 项：一部分补、一部分判"免/P3" |
| **Option B** | 全量补 19 项 |
| **Option C** | 沿用 P09「不额外补」⇒ P12 亦不补 |
| **Engineering Impact** | A：与 §3 判例法一致、最省对象。B：**index inflation**（含 `RESTRICT` 但父行几乎不删者）。C：**与 §3:202 明文冲突**，且 `CASCADE` 项在父行删除时确实全扫 |
| **Compatibility** | A ✅ B ⚠（违反"只建已知需求"） C ❌（违反 `:202`） |
| **Future Runtime Impact** | Agent/Tool 生命周期操作（归档、撤销、删除）的可预测性能 |
| **Recommended Direction** | **Option A** —— 逐项裁定；**优先** `CASCADE` 与 `RESTRICT` 且父行**确会被删除**者，`SET NULL` 与"父行不删"者按 §3 判例归 **P3/免**。理由：`D-P09-15` 已把"是否补"的裁量权**留给 P12**，且 §3 本身即采用**风险筛选**而非全量 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：Agent / Tool 索引**仅限**有 PREP query evidence 者；**不得**因 Runtime 将至而提前批量创建；**尤其不得**把 Runtime future query speculation 当作当前 evidence → `D-P12-07`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 8. `OQ-P12-08` — Event / Audit Indexes（**7 条 · 分区表 · 相位边界**）

| 字段 | 内容 |
|---|---|
| **Question** | `ix_events_dispatch` · `ix_events_tenant_type_time` · `ix_audit_{tenant_time,actor_time,resource,correlation,risk}`（**共 7**）究竟由 **P10** 在建表时一并建立，还是由 **P12** 后置建立？ |
| **Current Evidence** | `P10_PREP_REPORT:132`：**「P10 必须先于 P12 存在（`ix_events_*` / `ix_audit_*` 建在 P10 表上）」**；`:326`：**「P10 → P12 · P12 依赖 P10 · index dependency」**；`P10_ACCEPTANCE_MATRIX:159` DEP-03 同义；`P10 GP-6` 将 7 条列为**继承的冻结索引**；`D-P10-01` 以**「分区表二次 `ALTER` 代价高」**为由把 outbox 列**一次建齐**（**仅针对列**）；实测 `0010` 对 `ai_request_logs` 采「**建表即建索引**」形态（`ix_airl_tenant_occurred` 在 `0010` 内创建）。 |
| **Option A** | P10 建表**不建索引**；7 条索引**全部**在 P12 建立（严格按阶段名 P12 = Indexes） |
| **Option B** | P10 建表**同时**建立 7 条索引（沿用 `0010` 对分区表的既有形态） |
| **Option C** | 混合：`ix_events_dispatch`（outbox claim 热点）随 P10；其余 5 条查询索引入 P12 |
| **Engineering Impact** | A：相位语义最纯；但**与 `0010` 既有形态不一致**，且 P12 需对分区父表后置建索引（获取父+各子分区锁）。B：与 `0010` 形态一致、一次事务；但**P12 的交付面将缩至 0**（仅剩 FK 反查类），且与 `P10_PREP:132` 的措辞（"**建在 P10 表上**"可读作"P12 建、但**建在** P10 表上"）产生歧义。C：折中；但引入**两处相位**，对账复杂 |
| **Compatibility** | A ✅ B ⚠（`D-P10-01` 的**列**禁令不涵盖索引，故不构成硬冲突，但**运维理由同源**） C ⚠ |
| **Future Runtime Impact** | outbox claim 扫描性能（`D-P10-18` 投递 worker）；审计页/链路追踪查询性能；`D-AGENT-15` 可观测面 |
| **Recommended Direction** | **Option A 语义 + 显式相位声明**：7 条索引归 **P12**（与 `P10_PREP:326` 的「P12 依赖 P10」一致）；**P10 的 DDL 不含索引**。理由：`D-PLAT-09` 以「**P12 = Indexes**」命名该相位，且 `P10_PREP` 明确写为 **index dependency（P12 依赖 P10）**；`D-P10-01` 的「二次 ALTER」理由**字面仅针对列** |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**`ix_events_*` = P12** · **`ix_audit_*` = P12**，共 **7**（events 2 + audit_logs 5）；**P10 不负责这些 indexes** ⇒ `P10 Event/Audit persistence ≠ P12 Index delivery` → `D-P12-08`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 9. `OQ-P12-09` — P11-dependent Indexes

| 字段 | 内容 |
|---|---|
| **Question** | `G/H/I/J`（P11）是否存在 P12 必须补的索引？P12 可否为 trigger 复建索引？ |
| **Current Evidence** | `OQ-P11-11 = A`（**FROZEN**）：**P11 不创建"顺手索引"**（索引属 **P12**）；若 trigger 所需性能支持尚未存在 ⇒ **记录为 P12 dependency**；`P11_ACCEPTANCE_MATRIX:140` DEP-04：**「P11 不新增索引（复用既有 `ix_rp_subject`，0007 已建）」**；实测 `ix_rp_subject ON resource_permissions (subject_type_id, subject_id)` **已存在**（`0007`）⇒ G/I/J 查询路径**已有索引**；`DEP-07`：**`P11 semantic correctness` MUST NOT depend on `P12 business semantics`**。 |
| **Option A** | **P12 不为 G/H/I/J 新建任何索引**（`ix_rp_subject` 已覆盖）；`G` 的 `acl_subject_types` 反查由 `ix_rp_subject` 首列覆盖 |
| **Option B** | 为 J 的 `UPDATE … SET inherited=true, expires_at=now()` 新建 `(inherited, expires_at)` 部分索引 |
| **Option C** | 为 H（`users` 硬删 → 清 `resource_permissions`）新建 `ix_rp_granted_by` / 依赖 `OQ-P12-13` |
| **Engineering Impact** | A：0 新对象、与 `D-P11-11` 完全一致。B：**无 documented query pattern**（J 的 UPDATE 由触发器逐行驱动，无集合查询）⇒ 违反 `INDEX_STRATEGY` 原则。C：属 `resource_permissions.granted_by` **FK 反查**，归 `OQ-P12-13` 而非"trigger 索引" |
| **Compatibility** | A ✅ B ⚠（无查询证据） C ✅（但须归入 13） |
| **Future Runtime Impact** | ACL 撤销 / agent 归档 / role 删除的性能面 |
| **Recommended Direction** | **Option A** —— **P12 不为 G/H/I/J 新建索引**；`H` 涉及的 `resource_permissions.granted_by` 归入 `OQ-P12-13` 统一裁定 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：P11 trigger（G/H/I/J）可依赖 P12 性能索引，但 FK/reverse-lookup candidate **逐项依据 query evidence adjudicate**；`P11 semantics MUST NOT depend on P12` · `P12 index MUST NOT change P11 semantics`；**禁 blanket-create 24 GAP** → `D-P12-09`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 10. `OQ-P12-10` — Partition Index Policy

| 字段 | 内容 |
|---|---|
| **Question** | P12 在**分区表**上的索引策略：建在父表还是子分区？是否允许 `ATTACH PARTITION` / 本地索引 / 并发建索引？是否改变 PK/分区键/保留策略？ |
| **Current Evidence** | `INDEX_STRATEGY:160`：**「分区表索引建在父表自动下推」**；现有唯一先例 = `ai_request_logs` 的 `ix_airl_tenant_occurred`（**父表**，`0010`）；`B1-6_SCHEMA_DESIGN:346 DC-4`：**「子分区继承父表 PK，不额外建本地索引」**；`B1-6_TEST_MATRIX:147 AP3`：**「索引建在父表并下推至子分区」**（验收项）；`P10_ACCEPTANCE_MATRIX:113 PART-03` 同义（**ASSET**）；`events`/`audit_logs` **UQ = 无** ⇒ 不触发「分区表唯一索引必须含分区键」；`OQ-P10-09`（FROZEN）**拒绝 `DEFAULT` 分区**（避免 `ATTACH PARTITION` 需移动行）；`D-10` 分区维护 = **手工运维**（`D-3 = D`）。 |
| **Option A** | **父表建索引 + 自动下推**；**禁止**子分区本地索引；**禁止**改变 PK/分区键/保留策略；索引维护**跟随**既有手工运维模型；**不引入** `CONCURRENTLY`（迁移在事务内） |
| **Option B** | 允许 `CREATE INDEX … ON ONLY parent` + `ALTER INDEX … ATTACH PARTITION`（精细控制） |
| **Option C** | 允许子分区本地索引（规避父表锁） |
| **Engineering Impact** | A：与 4 处既有冻结/验收项一致、形态统一。B：**引入新机制**（与 DC-4 及 AP3 验收口径不符），SOP 复杂度↑。C：**违反 DC-4**，且新子分区**不会**自动获得本地索引 ⇒ 长期不一致 |
| **Compatibility** | A ✅ B ⚠ C ❌ |
| **Future Runtime Impact** | 分区滚动（月新增子分区）后索引的**自动继承性**；`audit_logs` 365d 分区 drop 的连带清理 |
| **Recommended Direction** | **Option A** —— 严格沿用「**父表建、自动下推**」；**子分区零本地索引**；**不改** PK / 分区键 / 分区策略 / 保留策略（任何此类发现 = `OUT OF SCOPE`）；迁移内**不**使用 `CONCURRENTLY` |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：P12 负责 `events`/`audit_logs` 的查询索引；**partition key / strategy / PK / retention 全部不变**；**不得**借 P12 改造 partition design → `D-P12-10`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 11. `OQ-P12-11` — Redundancy Policy

| 字段 | 内容 |
|---|---|
| **Question** | 重叠/冗余索引如何处置？**是否允许删除**既有索引？ |
| **Current Evidence** | `INDEX_STRATEGY §2`：**「多索引共享同一前缀……可接受……**不合并**」**；`§5`：**「季度用 `pg_stat_user_indexes` 清理零扫描索引（列入运维手册）」**；实测**未发现**完全重复（同名/同列同序）对象；已识别的**语义重叠**：`ix_res_tenant_*` 三条共享 `tenant_id` 前缀（`§2` 明文允许）· `ix_agents_tenant_status` 与 `uq_agents_key` 共享 `tenant_id` 前缀（谓词不同）· `ix_tm_user` 与 `uq_tenant_memberships` 列序互补（`B1-2:36` 已论证） |
| **Option A** | **不删除任何既有索引**；重叠**仅登记**；`P12` 新增对象须通过 `OQ-P12-03` 的「Why Existing Cannot Serve」举证；零扫描清理**移交运维手册**（不属 P12） |
| **Option B** | P12 顺带清理"看似重复"的既有索引 |
| **Option C** | P12 合并前缀重叠索引 |
| **Engineering Impact** | A：零风险、与 §2 明文一致。B/C：**删除已冻结/已发布对象** ⇒ 破坏性 + 需新 migration + 与「不回改」纪律冲突 |
| **Compatibility** | A ✅ B ❌ C ❌ |
| **Future Runtime Impact** | 写放大与存储成本（可观测后由运维清理） |
| **Recommended Direction** | **Option A** —— **重叠 ≠ 可删**；既有索引**一律保留**；候选删除**一律 `DEFERRED`**（除非另有显式 Human Decision） |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：新 index 须过五类重叠检查（exact duplicate / left-prefix overlap / predicate overlap / existing query coverage / constraint-support overlap）；**`overlap ≠ permission to delete existing index`**；删除或合并一律 **`DEFERRED`** → `D-P12-11`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 12. `OQ-P12-12` — Index Naming Convention

| 字段 | 内容 |
|---|---|
| **Question** | P12 新增索引的命名如何定？已观测的**命名漂移**（`CF-3`）与**缩写偏移**如何处置？ |
| **Current Evidence** | B0 §4：**`uq_<table>_<cols>` / `ix_<table>_<cols>`（列序同索引定义）**；实测**缩写偏移**（`ix_tm_user` · `ix_rp_subject` · `ix_res_*` · `ix_ap_agent` · `ix_texec_*` · `ix_airl_*` · `ix_aimodels_*`）；**命名漂移 2 处**：设计 `ix_rp_permission` → 实现 `ix_role_permissions_permission`；设计 `ix_tm_role` → 实现 `ix_tenant_memberships_role`（`CF-3`，文档命中 10 / 7 处） |
| **Option A** | 沿用 B0 §4；**缩写允许**（受 PG 标识符长度约束）；**不重命名**既有对象；P12 **新增**对象须用**全表名**或**已确立的稳定缩写**，且**一次性**写入对账表 |
| **Option B** | P12 统一重命名为全表名形态（含 `ALTER INDEX … RENAME`） |
| **Option C** | 沿用 B0 §4 但**禁止**新缩写（仅用全表名） |
| **Engineering Impact** | A：零回溯；但 §4 与既存缩写并存的现状**被正式接受**。B：**破坏性**（`RENAME` 触及测试断言 33 处 + 引用文档）+ 违反「PREP 不改名」指令。C：新对象名可能超长（PG 63 字节上限） |
| **Compatibility** | A ✅ B ❌（指令 §11「不要在 PREP 阶段改名」+ 破坏性） C ⚠ |
| **Future Runtime Impact** | 运维/监控引用稳定性（`pg_stat_user_indexes` 报表可读性） |
| **Recommended Direction** | **Option A** —— 命名**沿用既有先例**，**不发明第二套**；缩写**正式承认**；**不重命名**；**漂移只登记**（`CF-3`），由后续独立 Human Decision 处理 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：采用现有 canonical naming convention（`ix_<semantic_name>` / `uq_<semantic_name>`）；命名漂移**只登记，不在 P12 Freeze 中改名** → `D-P12-12`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 13. `OQ-P12-13` — Post-Strategy FK Coverage（**证据驱动新增** · canonical 主题）

| 字段 | 内容 |
|---|---|
| **Question** | 实测 **24 GAP + 5 partial-only** 中，P12 **最终**补建哪些？判定矩阵是什么？ |
| **Current Evidence** | `INDEX_STRATEGY §3:202`：**「上表『动作』列的补充索引进入 P12」**；§3 实际只 adjudicate 了 **3 项**（`ix_tm_role` · `ix_memberships_role` · `ix_rp_permission`，**均已在 0005 落地**）并**明确判免 P3 若干**；**实测 19 个 GAP 属策略文档之后建的表**（`0008` 2 · `0010` 6 · `0011` 11）**从未被 §3 adjudicate** ⇒ `GAP-INV-P12`；`P09_DECISION_LOG:248` 把裁量权**显式**留给 P12 |
| **Option A** | **风险筛选法（§3 判例法）**：仅补 **① `RESTRICT`/`CASCADE` 且父行确会被删除 ② 无其他索引可服务** 者；`SET NULL` 与"父行不删"者归 **P3/免**；逐项写入对账表 |
| **Option B** | **全量补 24+5** |
| **Option C** | **全不补**（沿用 P09 最小化口径） |
| **Engineering Impact** | A：对象数最省、与 §3 判例一致；但需**逐项** Human 裁定（24+5 项）。B：index inflation；`permissions`/`users` 等**几乎不硬删**的表建索引属过度设计。C：`CASCADE` 项在父行删除时**确定**全扫（违反 §3「必须补」） |
| **Compatibility** | A ✅ B ⚠ C ❌（违反 `:202` + P09 明示移交） |
| **Future Runtime Impact** | 租户/空间/用户/角色/资源/工具的删除与归档操作性能；`D-P10-11` 的 retention purge 路径 |
| **Recommended Direction** | **Option A** —— 逐项裁定；**参照 §3 既有判例的分档**（`RESTRICT`+父行会删 ⇒ 补；`SET NULL` ⇒ 视父行删除频率；"父行几乎不删"（`permissions`/`acl_subject_types`）⇒ 免；`users` 软删为主 ⇒ 降级 P3）。**建议优先集合（待你裁定）**：`agent_versions.agent_id`（`CASCADE`）· `agent_permissions.{version_id,permission_id,tool_id}`（`CASCADE`）· `tool_permissions.{permission_id,version_id}`（`CASCADE`）· `tool_versions.tool_id`（`CASCADE`）· `tool_executions.{tool_version_id,agent_id}` |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**`GAP-INV-P12` = inventory / adjudication completeness gap，非 automatic implementation list**；24 GAP 在 Implementation Contract 中**逐项**列 `CREATE / DEFER / ALREADY COVERED / NOT REQUIRED`；**19 个 post-strategy FK** 必须**单独标记来源年代**；**禁**以「FK reverse lookup」四字整体批量创建 → `D-P12-13`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 14. `OQ-P12-14` — `ix_aimodels_capability` / `T-1`（**证据驱动新增** · canonical 主题）

| 字段 | 内容 |
|---|---|
| **Question** | P3 候选 6 项（`ix_users_status` · `ix_tenants_status` · `ix_rp_permission` · roles FK 反查 · `agents.owner_id` · `ix_aimodels_capability`）与 `T-1` 在本轮如何处置？ |
| **Current Evidence** | `INDEX_STRATEGY §5:218` 列 **P3 候选（确认后建）**；实测：`ix_users_status` / `ix_tenants_status` / roles FK 反查 / `agents.owner_id` **未落地**；`ix_rp_permission` **已以 `ix_role_permissions_permission` 落地**（`CF-3`）；`ix_aimodels_capability` = **`T-1`**：谓词引用**不存在列** `capability`（实测 `ai_models` 仅有 **`capabilities jsonb`**），且 §2 **禁止 jsonb GIN**，且 `O-E` 已登记**相位歧义**（`B1-6_DEPENDENCY` 归「P11/P12」，`INDEX_STRATEGY:218` 未 assign）；B1-2 已独立判定 `ix_tenants_status` **不建**（"无批扫 job"） |
| **Option A** | **P3 一律维持 `DEFERRED`**（不属 P12 交付面）；`T-1` **维持 DEFERRED**，并把 `ix_aimodels_capability` 的**定义失效**（列名不存在）**登记**为待后续澄清项；`CF-3` 陈旧陈述**登记** |
| **Option B** | 本轮把 P3 6 项**全部**裁定为"建"或"不建" |
| **Option C** | `T-1` 本轮**改写** `INDEX_STRATEGY` 定义（`capability` → `capabilities` 表达式索引） |
| **Engineering Impact** | A：最小动作、严守 P12 scope；P3 保持"确认后建"语义。B：**扩张 P12 scope**（P3 是"待确认"而非"已冻结必建"）。C：**改写 B0 冻结文档** ⇒ 违反「不回改」纪律 |
| **Compatibility** | A ✅ B ⚠ C ❌ |
| **Future Runtime Impact** | 后台批扫（用户/租户状态）与 AI 模型枚举的查询性能 |
| **Recommended Direction** | **Option A** —— P3 **维持 `DEFERRED`**；`T-1` **维持 DEFERRED**（不建、不改 B0、不作废，沿用 `0010` 既有处置）；`CF-3` / `CF-4` / `O-E` **只登记不修复** |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**`DO NOT IMPLEMENT ix_aimodels_capability`** —— 文档引用 `capability`，实际列 = **`capabilities` JSONB**；既有设计**明确排除** JSONB GIN ⇒ **`T-1 = stale / mismatched design claim`**；**不得**偷换为 `GIN(capabilities)`，不得发明其他 JSONB index → `D-P12-14`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 15. `OQ-P12-15` — Scope Closure / No Opportunistic Indexing（**证据驱动新增** · canonical 主题）

| 字段 | 内容 |
|---|---|
| **Question** | 哪些"不变量"**不属于**索引机制？P12 如何防止把 `CHECK`/`FK`/`UNIQUE constraint`/`trigger` 的职责**误搬**为索引（或反之）？ |
| **Current Evidence** | 既有机制分区（实测）：**`CHECK`** = `0003`–`0011` 的 CK 集（如 `ck_agents_status` · `ck_tool_executions_status`）；**`FK`** = 54 条（含 `RESTRICT`/`CASCADE`/`SET NULL`）；**`UNIQUE CONSTRAINT`** = 5（纯列唯一）；**`trigger`** = 24 语句（A–F2/C2/K 已实现；G/H/I/J 归 P11）；**`R2-D-14`**：**「DB 不做授权解释」**（`AUTHORIZATION_PREP:549` 复核「**不建议**新增授权解释触发器」）；`D-P11-07`：trigger **不得**承担授权求值；`events`/`audit_logs` **无 FK**（事实日志，`tenant_id`/`space_id` 无强制引用）。 |
| **Option A** | **冻结机制边界表**：索引**仅**承担 ① 查询加速 ② FK 反查支撑 ③ 唯一性（**仅当**需表达式/部分时，且已由 `D-B15-06`/`D-B16-07`/`D-P09-04` 规定形式）；**不**承担授权求值、**不**承担跨表一致性、**不**承担不可变性；`UNIQUE CONSTRAINT` 与 unique INDEX 的**分界沿用既有三分法** |
| **Option B** | 允许索引作为"轻量约束"在 P12 内自由使用 |
| **Option C** | 不写边界表，逐案判断 |
| **Engineering Impact** | A：防"以索引偷渡语义"、防机制混杂。B：**违反** `R2-D-14` 精神与 `D-P11-07`。C：同类缺陷可复发（前序已多次出现"机制误用"类教训） |
| **Compatibility** | A ✅ B ❌ C ⚠ |
| **Future Runtime Impact** | 决定后续任何"加索引即加固"的错误提案能否被机制化拒绝 |
| **Recommended Direction** | **Option A** —— 冻结**机制边界表**（index / CHECK / FK / UNIQUE constraint / trigger 各自唯一归属），并明确 **P12 交付面 ⊆ 索引**：`P12` 不新增 `CHECK`/`FK`/`trigger`/seed，**不修改** PK/UQ 语义 |
| **HUMAN DECISION** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**P12 canonical scope** = ① Frozen P12 indexes ② Explicitly evidenced Event/Audit indexes ③ Explicitly adjudicated FK reverse-lookup indexes ④ Explicitly evidenced ACL / Agent / Tool query indexes；**不包括**：「just in case」indexes · future Runtime speculation · future business-module speculation · authorization policy indexes without query evidence · trigger-generated performance guesses · schema redesign · index renaming cleanup → `D-P12-15`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **STATUS** | `FROZEN` |

---

## 16. 继承面（**已冻结、本轮不重开**；本轮**逐条确认为 unchanged**）

| ID | 已冻结事实 | 依据 |
|---|---|---|
| `GP-1` | `D-PLAT-09` 路线 A：`P10 → P11 → P12 → P13 → Runtime`（**未 supersede**） | `D-PLAT-09` |
| `GP-2` | `P10 = Event/Audit persistence + tg_audit_immutable`（L = **P10-owned**，OUT OF P11/P12） | `D-P10-11` |
| `GP-3` | `P11 = G/H/I/J`；**P11 不新增索引**（复用 `ix_rp_subject`） | `D-P11-01` · `D-P11-11` |
| `GP-4` | **`P11 semantic correctness` MUST NOT depend on `P12 business semantics`** | `D-P11-11` |
| `GP-5` | 索引清单（7 条 `ix_events_*`/`ix_audit_*`）= **继承的冻结索引** | `P10 GP-6` |
| `GP-6` | **seed 前必须有：全部表（P01–P10）+ 全部 trigger（P11）+ 全部 index（P12）** | `SEED_STRATEGY:138` |
| `GP-7` | 分区表：**父表建索引 + 自动下推**；子分区零本地索引 | `INDEX_STRATEGY:160` · `B1-6 DC-4` · `AP3` |
| `GP-8` | 命名：`uq_<table>_<cols>` / `ix_<table>_<cols>`；**不为"未来可能"建索引** | `INDEX_STRATEGY §4` · 首部原则 |
| `GP-9` | 表达式唯一 ⇒ unique INDEX；纯列唯一 ⇒ UNIQUE CONSTRAINT；部分唯一 ⇒ unique INDEX | `D-B15-06` · `D-B16-07` · `D-P09-04` · `D-P09-16` |
| `GP-10` | `events`/`audit_logs` **UQ = 无**；**无 FK**（事实日志）；保留期 30d/365d | `CONSTRAINT_MATRIX §7` |
| `GP-11` | `D-P10-01`：outbox **列**属 P10 DDL 一次建齐（**仅列**） | `D-P10-01` |
| `GP-12` | 授权审计 persistence = **DEFERRED TO P10**；**不得在 P10 外**创建 `events`/`audit_logs` | `D-AUTH-15/22` · `P10 GP-13` |
| `GP-13` | `D-AUTH-01..25` · `D-AGENT-01..16` · `D-P10-01..18` · `D-P11-01..14` **本轮不 supersede** | 指令 §0/§D |
| `GP-14` | `P09` 保护：`0010`/`0011`/`0012` **不得修改**；`0013+` **不得创建** | 指令 §7/§E |
| `GP-15` | 四类审计分离：**Agent Run Audit ≠ Authorization Decision Audit ≠ Tool Execution Audit** | `D-AUTH-15` · `D-AGENT-13` · `P10 GP-12` |

---

## 17. 交叉一致性登记（`CF-1` … `CF-6` · `GAP-INV-P12`）

见 `P12_PREP_REPORT.md` §9。PREP 轮**只登记**；**本轮（2026-09-25 Human Decision）给出终态处置**，
**仍不改写任何历史正文**（历史陈述由本区段与 PDL 附录 I 承担**跨日志可见性**）。

| ID | 事项 | **终态** | 落地 |
|---|---|---|---|
| `CF-1` | `INDEX_STRATEGY` §3 称 resources 的 space/owner「复合索引打头均覆盖」vs 实测无打头索引 | **CLARIFIED** | **不得据此自动创建** `space_id`-leading / `owner_id`-leading 索引；保留为**文档一致性事项**：明确「documented coverage claim」与「implemented coverage」**必须区分** |
| `CF-2` | `ix_aimodels_capability`（`T-1`）多重不一致 | **RESOLVED** | 采用 `D-P12-14`：**DO NOT IMPLEMENT**；`T-1` **关闭为 stale / mismatched design claim** |
| `CF-3` | `B1-6_DECISION_LOG:331` 称 P3 候选「全部未落地」，而 `ix_rp_permission` 实已落地 | **CLARIFIED** | canonical implemented object = **`ix_role_permissions_permission`**；`ix_rp_permission` **仅作历史命名记录**；**P12 不 rename** |
| `CF-4` | B0 `STEP1B_INDEX_STRATEGY.md` 缺 `platform_memberships` 小节 | **CLARIFIED** | 文档缺失**不自动**转成 index implementation requirement；以后是否需 index 按 `D-P12-02` **单独 adjudicate** |
| `CF-5` | 部分索引被误当 FK 覆盖 | **RESOLVED** | 确认 **`partial index ≠ full FK coverage`**；`partial-only` **继续单独统计**；**不得**归入 full coverage |
| `CF-6` | `D-P10-01`「分区表二次 ALTER」理由 vs P12 后置建 7 索引 | **CLARIFIED** | **P10 建表 = YES；P12 建对应 index = YES** ⇒ **`P10 schema ownership` + `P12 index ownership`**，**不是**阶段错误；**不得**解释成 P10 schema regression |

```text
GAP-INV-P12 = inventory / adjudication completeness gap（非 implementation gap）
            ⇒ 受「per-gap adjudication」治理（D-P12-13）
            ⇒ 24 GAP 逐项 CREATE / DEFER / ALREADY COVERED / NOT REQUIRED
            ⇒ 19 个 post-strategy FK 须单独标记来源年代
T-1         = CLOSED as stale / mismatched design claim（D-P12-14）
```

---

## 18. Exit Check

```text
OQ-P12-01 … OQ-P12-15  = 15 / 15 FROZEN（0 DEFERRED · 0 SUPERSEDED · 0 unresolved）
本轮已冻结 15 项决策               ✅（写入 PLATFORM_DECISION_LOG.md · 附录 I 登记）
新建 migration = 0                 ✅
CREATE/ALTER/DROP INDEX = 0        ✅
DDL = 0 · DML = 0                  ✅
code / test / config = 0           ✅
commit / tag / push = 0            ✅
P12 DECISION FREEZE = PASSED
P12 IMPLEMENTATION  = NOT AUTHORIZED
P13 IMPLEMENTATION  = NOT AUTHORIZED
Runtime Implementation Gate = CLOSED
```

**不变**：`P12 / P13 IMPLEMENTATION = NOT AUTHORIZED` · **`Runtime Implementation Gate = CLOSED`**。

**END OF P12 DECISION RESOLUTION（2026-09-25 · DECISION FREEZE · 15/15 FROZEN）**
