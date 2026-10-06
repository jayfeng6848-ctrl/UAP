# P12 — ACCEPTANCE MATRIX（Indexes · DECISION FREEZE）

> **状态**：本矩阵随 `P12_PREP_REPORT.md`（PREP）产出，并于 **2026-09-25 Human Decision Freeze** 后升级。
> 条目状态取值：**`ASSET`**（既有冻结资产）· **`PASSED`**（只读实测通过）·
> **`FROZEN-DESIGN`**（已冻结设计，**未实施**）· **`BLOCKED`**（被 Runtime Implementation Gate 阻塞）。
> **数字为脚本实测**（按 ID 前缀分组、**逐行最后一格**主状态计数），非估算。
> **本轮零实施**（无索引 / 无 migration / 无代码 / 无测试变更）——`FROZEN-DESIGN` **不等于**已实施。
>
> **§0 口径声明**：状态**一律从最后一格（状态单元）解析**，**禁止**扫描整行正文判定
> （教训：行内出现的状态词会污染计数）。跨文档比对**一律双侧归一**
> （剥离 `` ` `` `*` 强调标记、统一空白、casefold）。

---

## 1. INV — Index Inventory Completeness

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| INV-01 | **索引对象总数 = 57**（独立创建 52 + 内联 UNIQUE CONSTRAINT 隐式 5） | 脚本实测 | **PASSED** |
| INV-02 | 独立创建 52 = `op.create_index` **25** + 原生 SQL **27** | 脚本实测 | **PASSED** |
| INV-03 | 前缀分布 `ix=24` · `uq=28`（含内联则 `uq=33`） | 脚本实测 | **PASSED** |
| INV-04 | unique **20** · non-unique **32** · partial **16**（52 口径） | 脚本实测 | **PASSED** |
| INV-05 | 逐 revision 对账：`0003`=15 · `0004`=7 · `0005`=10 · `0007`=8 · `0008`=4 · `0010`=5 · `0011`=8 · 其余=0 | 脚本实测 | **PASSED** |
| INV-06 | `0007`「indexes (8)」声明 vs 实测 **8** | migration docstring | **PASSED** |
| INV-07 | `0008`「UNIQUE INDEX = 3 · non-PK INDEX = 4」vs 实测 **4** | migration docstring | **PASSED** |
| INV-08 | `0010`「UNIQUE INDEX = 2 · non-PK INDEX = 5」vs 实测 **5** | migration docstring | **PASSED** |
| INV-09 | `0011`「交付 8 个索引对象」vs 实测 **8** | migration docstring · `D-P09-15` | **PASSED** |
| INV-10 | `0009` / `0012` docstring 声明「不新增 Index」vs 实测 **0** | migration docstring | **PASSED** |
| INV-11 | 内联 `UNIQUE CONSTRAINT` **5** 个已识别并计入覆盖判定 | 脚本实测 | **PASSED** |
| INV-12 | **canonical inventory** = PREP 实测 **57 / 52 / 5** 为 P12 基线 | **`D-P12-01`** | **FROZEN-DESIGN** |
| INV-13 | 既有索引 **NOT recreated / NOT renamed / NOT merged / NOT deleted**；P12 只处理 missing/additional | **`D-P12-01`** | **FROZEN-DESIGN** |
| INV-14 | `platform_memberships` 3 对象**无 B0 条目**（`CF-4`）⇒ 不自动转成 index requirement；按 `D-P12-02` 单独 adjudicate | `D-P12-02` · `CF-4` | **FROZEN-DESIGN** |

## 2. QE — Query Evidence

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| QE-01 | 五级证据优先级（Frozen Decision → schema/query contract → documented query → acceptance/test query → measured runtime requirement） | **`D-P12-02`** | **FROZEN-DESIGN** |
| QE-02 | 四类理由**不得单独**构成建索引理由（future may query / best practice / **FK exists** / performance safety） | **`D-P12-02`** | **FROZEN-DESIGN** |
| QE-03 | **`GAP ≠ automatic CREATE INDEX`** —— 必须逐项 adjudicate | **`D-P12-02`** · **`D-P12-13`** | **FROZEN-DESIGN** |
| QE-04 | 禁止「未来可能会查 / 一般都应建 / 为性能先建」为唯一依据 | `INDEX_STRATEGY` 首部原则 | **ASSET** |
| QE-05 | 每个 P12 新增索引须回答 Query / Filter-Order / Boundary / Why-Existing-Not-Serve / Cardinality | `B1-2 §1` · `B1-3 §1` | **ASSET** |
| QE-06 | 既有 24 个 tenant 打头对象的 Query Pattern 可回溯至 B0 §1/B1-2/B1-3（无"无来源索引"） | 脚本实测 | **PASSED** |

## 3. UQ — Unique Index Semantics

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| UQ-01 | 表达式唯一性 = **unique INDEX**（非 CONSTRAINT）：`uq_ai_routes` · `uq_ai_policies` · `uq_agent_perm` · `uq_tool_perm` | `D-B15-06` · `D-B16-07` · `D-P09-16` | **PASSED** |
| UQ-02 | 纯列唯一 = **UNIQUE CONSTRAINT**（5 个内联对象） | `CONSTRAINT_MATRIX` | **PASSED** |
| UQ-03 | 部分唯一 = **UNIQUE INDEX**（`uq_tool_exec_idem`），**不得**伪装为 CONSTRAINT | `D-P09-04 = A` | **PASSED** |
| UQ-04 | `uq_tool_exec_idem` NULL 分支（`idempotency_key IS NULL`）**不受唯一约束** | 脚本实测 | **PASSED** |
| UQ-05 | 现有 `UNIQUE` / `UNIQUE INDEX` 语义**全部保持**；**不得**以索引替换约束 / 以约束替换索引 / 改唯一语义；部分唯一 predicate 保持 | **`D-P12-04`** | **FROZEN-DESIGN** |
| UQ-06 | `uq_tool_exec_idem` **保留**（`UNIQUE` + `predicate = idempotency_key IS NOT NULL`）；**不得**再建等价 idempotency index | **`D-P12-06`** | **FROZEN-DESIGN** |
| UQ-07 | **P12 不改 PK / UQ 语义**（表级身份语义不动） | 指令 §7/§8 · `D-P12-10` | **FROZEN-DESIGN** |

## 4. PART — Partial Predicate Semantics

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| PART-01 | 部分索引对象 = **16**（52 口径），谓词逐项可核 | 脚本实测 | **PASSED** |
| PART-02 | partial-only 清单：`credentials.identity_id` · `roles.{space_id,tenant_id}` · `tool_executions.tool_id` · `tools.tenant_id` | 脚本实测 | **PASSED** |
| PART-03 | 既有部分索引**一律不修改**（含软删语义 `uq_memberships` / `uq_agents_key` 等） | `D-P09-04` · **`D-P12-06`** | **FROZEN-DESIGN** |
| PART-04 | **`partial index ≠ full FK coverage`**（不得因存在该 index 而声称完整覆盖 FK reverse lookup / integrity-support requirement） | **`D-P12-05`** · `CF-5` | **FROZEN-DESIGN** |
| PART-05 | **`partial-only = 5` 继续作为独立分类**，**不得**在 acceptance 中归入 full coverage | **`D-P12-05`** · `CF-5 = RESOLVED` | **FROZEN-DESIGN** |
| PART-06 | 部分唯一索引的**唯一性仅覆盖谓词为真行**（语义显式陈述） | **`D-P12-05`** | **FROZEN-DESIGN** |

## 5. TS — Tenant / Space Scope

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| TS-01 | 低基数列单列索引（status/scope/risk_level）**不建** | `INDEX_STRATEGY §2` | **ASSET** |
| TS-02 | 多索引共享 tenant 前缀**可接受、不合并**（列序服务不同查询） | `INDEX_STRATEGY §2` · `B1-2 §6` | **ASSET** |
| TS-03 | **不用机械 tenant/space 前缀规则**；仅在**明确查询模式**下建组合索引 | **`D-P12-03`** | **FROZEN-DESIGN** |
| TS-04 | **P12 不得引入新的 authorization semantics** | **`D-P12-03`** · `D-P11-07` | **FROZEN-DESIGN** |
| TS-05 | 实测 **24** 个 tenant 打头对象，无 `(tenant_id, id)` 机械形态 | 脚本实测 | **PASSED** |

## 6. FK — FK 反查覆盖（本轮核心实测）

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| FK-01 | FK 约束总数 = **54**（去重后）· 建表数 = **29** | 脚本实测 | **PASSED** |
| FK-02 | 分划闭合：覆盖 **25** + partial-only **5** + GAP **24** = **54**（脚本内断言） | 脚本实测 | **PASSED** |
| FK-03 | GAP `ondelete` 分布：`CASCADE 6` · `RESTRICT 11` · `SET NULL 7` | 脚本实测 | **PASSED** |
| FK-04 | GAP 时代切分：策略文档之后 **19** · 策略文档时代 **5** | 脚本实测 | **PASSED** |
| FK-05 | 时代 GAP 5 项：`memberships.user_id` · `resource_permissions.granted_by` · `resources.{owner_id,space_id}` · `spaces.owner_id` | 脚本实测 | **PASSED** |
| FK-06 | **`GAP-INV-P12` = inventory / adjudication completeness gap**，**非** automatic implementation list | **`D-P12-13`** | **FROZEN-DESIGN** |
| FK-07 | **24 GAP 在 Implementation Contract 中逐项列** `CREATE` / `DEFER` / `ALREADY COVERED` / `NOT REQUIRED` | **`D-P12-13`** | **FROZEN-DESIGN** |
| FK-08 | **19 个 post-strategy FK 必须单独标记来源年代**（防把策略文档缺失误写成 schema defect） | **`D-P12-13`** | **FROZEN-DESIGN** |
| FK-09 | **禁**以「FK reverse lookup」四字整体批量创建 | **`D-P12-13`** · **`D-P12-09`** | **FROZEN-DESIGN** |
| FK-10 | **永久判定规则**：`FK coverage GAP → query evidence adjudication → CREATE / DEFER / NOT REQUIRED`；禁止 `FK exists → automatic index` | **`D-P12-13`** · PDL `GAP-INV-P12 永久判定规则` | **FROZEN-DESIGN** |
| FK-11 | `STEP1B_INDEX_STRATEGY:202`「补充索引进入 **P12**」= P12 交付面的**明文来源** | `:202` | **ASSET** |
| FK-12 | P09 **显式**将 FK 列索引移交 P12（不额外补） | `P09_DECISION_LOG:248` · `P09_SCOPE:29` | **ASSET** |
| FK-13 | `CF-1`：resources「space/owner 已覆盖」陈述 vs 实测**不一致** ⇒ **不得据此自动创建** `space_id`/`owner_id`-leading 索引 | `CF-1 = CLARIFIED` | **FROZEN-DESIGN** |

## 7. P09 — P09 Protection

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| P09-01 | `0010` sha256 **未变**（`6d9907237f80e9da…`） | 命令 | **PASSED** |
| P09-02 | `0011` sha256 **未变**（`cdaf8383630335db…`） | 命令 | **PASSED** |
| P09-03 | `0012` sha256 **未变**（`5ecd1ef30b403fb4…`） | 命令 | **PASSED** |
| P09-04 | `migrations_alembic/` 相对 HEAD **diff 空** · `0013+ = 0` · 单头 `0012` | 命令 | **PASSED** |
| P09-05 | `core/` `services/` `agent/` `intelligence/` `infrastructure/` `tests/` `apps/` `config/` `scripts/` relative HEAD **diff 空** | 命令 | **PASSED** |
| P09-06 | P09 交付的 8 个索引对象**不动**（`D-P09-15` / `D-P09-16` 语义保持） | `D-P09-15` · **`D-P12-01`** | **FROZEN-DESIGN** |

## 8. P10 — P10 Boundary

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| P10-01 | `P10 = Event/Audit persistence + tg_audit_immutable`（L = **P10-owned**） | `D-P10-11` | **ASSET** |
| P10-02 | P12 **不得**创建/修改 `audit_logs` / `events` **trigger** | `D-P10-11` · **`D-P12-08`** | **FROZEN-DESIGN** |
| P10-03 | P12 **不得**在 P10 之外创建 `events` / `audit_logs` **表** | `P10 GP-13` | **ASSET** |
| P10-04 | **`ix_events_*` = P12 · `ix_audit_*` = P12**，共 **7**（events 2 + audit_logs 5）；**P10 不负责这些 indexes** | **`D-P12-08`** | **FROZEN-DESIGN** |
| P10-05 | `events` / `audit_logs` **UQ = 无** ⇒ 不触发分区唯一索引约束 | `CONSTRAINT_MATRIX §7` | **PASSED** |
| P10-06 | **`P10 Event/Audit persistence ≠ P12 Index delivery`** | **`D-P12-08`** | **FROZEN-DESIGN** |
| P10-07 | **`P10 schema ownership` + `P12 index ownership` = 阶段分工，非阶段错误**；**不得**把 P12 后置 index 解释成 P10 schema regression | **`CF-6 = CLARIFIED`** · `D-P12-08` | **FROZEN-DESIGN** |

## 9. P11 — P11 Boundary

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| P11-01 | `P11 = G/H/I/J`；P12 **不得**重新解释 P11 未完成事项 | `D-P11-01` | **ASSET** |
| P11-02 | **P11 不新增索引**（复用既有 `ix_rp_subject`，`0007` 已建） | `D-P11-11` · `P11 DEP-04` | **PASSED** |
| P11-03 | P11 trigger（G/H/I/J）reverse lookup 候选**逐项依据 PREP query evidence adjudicate**；**禁 blanket-create 24 GAP** | **`D-P12-09`** | **FROZEN-DESIGN** |
| P11-04 | `P11 semantics MUST NOT depend on P12` · `P12 index MUST NOT change P11 semantics` | **`D-P12-09`** · `D-P11-11` | **FROZEN-DESIGN** |
| P11-05 | `G/H/I/J` 均**未**落地（P11 PREP 已实测确认，属 P11 交付面） | `P11_PREP_REPORT` | **ASSET** |
| P11-06 | P12 **不为 G/H/I/J 新建无查询证据的索引**（`ix_rp_subject` 已覆盖其查询路径） | **`D-P12-09`** | **FROZEN-DESIGN** |

## 10. PGRP — Partition Interaction

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| PGRP-01 | 现存在分区表 = **1**（`ai_request_logs`）；父表索引 `ix_airl_tenant_occurred` | 脚本实测 | **PASSED** |
| PGRP-02 | 冻结口径：**索引建在父表 + 自动下推**；**子分区零本地索引** | `INDEX_STRATEGY:160` · `B1-6 DC-4` · `AP3` | **ASSET** |
| PGRP-03 | P12 **不得**改变 partition key / PK / partition strategy / retention policy | 指令 §8 · **`D-P12-10`** | **FROZEN-DESIGN** |
| PGRP-04 | **不得**借 P12 改造 **partition design** | **`D-P12-10`** | **FROZEN-DESIGN** |
| PGRP-05 | P12 **负责** `events` / `audit_logs` 的查询索引（7 条） | **`D-P12-10`** · **`D-P12-08`** | **FROZEN-DESIGN** |
| PGRP-06 | `events`/`audit_logs` 保留期（30d / 365d）**不变**；分区 drop 机制**不变** | `P10 GP-7` · **`D-P12-10`** | **FROZEN-DESIGN** |

## 11. DUP — Duplicate / Overlap

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| DUP-01 | **无完全重复**索引对象（同名/同列同序） | 脚本实测 | **PASSED** |
| DUP-02 | 共享前缀重叠**已登记且允许**（`ix_res_tenant_*` 三条 · `ix_agents_tenant_status` vs `uq_agents_key`） | `INDEX_STRATEGY §2` | **ASSET** |
| DUP-03 | `ix_tm_user` 与 `uq_tenant_memberships` 列序互补（非冗余，`B1-2:36` 已论证） | `B1-2 §3` | **ASSET** |
| DUP-04 | 新 index 必过**五类重叠检查**（exact duplicate / left-prefix overlap / predicate overlap / existing query coverage / constraint-support overlap） | **`D-P12-11`** | **FROZEN-DESIGN** |
| DUP-05 | **`overlap ≠ permission to delete existing index`**；历史 index 删除/合并**一律 `DEFERRED`**（除非独立 Human Decision） | **`D-P12-11`** | **FROZEN-DESIGN** |
| DUP-06 | 零扫描索引清理**移交运维手册**（不属 P12） | `INDEX_STRATEGY §5` | **ASSET** |

## 12. NAME — Naming

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| NAME-01 | B0 §4 规范：`uq_<table>_<cols>` / `ix_<table>_<cols>`（列序同定义） | `INDEX_STRATEGY §4` | **ASSET** |
| NAME-02 | 采用现有 canonical naming convention（`ix_<semantic_name>` / `uq_<semantic_name>`） | **`D-P12-12`** | **FROZEN-DESIGN** |
| NAME-03 | **命名漂移 2 处**：`ix_rp_permission` ↔ `ix_role_permissions_permission`；`ix_tm_role` ↔ `ix_tenant_memberships_role` | 脚本实测 · **`D-P12-12`** | **FROZEN-DESIGN** |
| NAME-04 | **canonical implemented object = `ix_role_permissions_permission`**；`ix_rp_permission` **仅作历史命名记录** | **`CF-3 = CLARIFIED`** | **FROZEN-DESIGN** |
| NAME-05 | **P12 不 rename** 任何既有索引（`ALTER INDEX … RENAME` 禁用 · 禁 renaming cleanup） | **`D-P12-12`** · 指令 §11 | **FROZEN-DESIGN** |
| NAME-06 | 缩写偏移已登记（`ix_tm_user` · `ix_rp_subject` · `ix_res_*` · `ix_ap_agent` · `ix_texec_*` · `ix_airl_*` · `ix_aimodels_*`） | 脚本实测 | **PASSED** |

## 13. DEP — Dependency Order

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| DEP-01 | `D-PLAT-09` 路线 A：`P10 → P11 → P12 → P13 → Runtime`（**未 supersede**） | `D-PLAT-09` | **ASSET** |
| DEP-02 | P12 **依赖 P10 表存在**（7 条索引建于 P10 表） | `P10_PREP:132/326` · `D-P12-08` | **ASSET** |
| DEP-03 | **P13 seed 依赖 P12 完成**（「全部 index（P12）」先于 seed） | `SEED_STRATEGY:138` | **ASSET** |
| DEP-04 | **P12 不依赖 P13 seed 数据**（索引须在**空数据**上可建） | `D-P12-01` | **ASSET** |
| DEP-05 | P12 顺序位于 P11 之后（弱顺序依赖；语义解耦） | `D-P12-09` | **ASSET** |
| DEP-06 | Runtime gate：`P10 ∧ P11 ∧ P12 ∧ P13 ∧ AI Gateway Runtime` **未满足** | `D-AGENT-16` | **BLOCKED** |
| DEP-07 | 四类依赖分离（design / schema / implementation / runtime） | `P12_PREP §11` | **ASSET** |
| DEP-08 | **P10 schema ownership + P12 index ownership**（同表不同交付面，两段式**有意**） | **`D-P12-08`** · **`CF-6`** | **FROZEN-DESIGN** |

## 14. XD — Cross-Decision Scan（Charter §7）

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| XD-01 | `ACTIVE vs FROZEN` 冲突 = **0**（P12 未新增 active 未冻结项） | PDL 附录 I.6 | **PASSED** |
| XD-02 | `FROZEN vs FROZEN` 冲突 = **0**（15 条与 `D-PLAT-09`/`D-P10-01`/`D-P10-11`/`D-P11-01`/`D-P11-11`/`D-B15-06`/`D-B16-07`/`D-P09-04`/`D-P09-16`/`D-AGENT-08` 逐条一致） | PDL 附录 I.6 | **PASSED** |
| XD-03 | `SCHEMA vs DECISION` 冲突 = **6 项已登记并处置**（`CF-1`…`CF-6`） | PDL 附录 I.6/I.7 | **PASSED** |
| XD-04 | 陈旧「P12 已实现」声明扫描 = **0 命中** | 命令 | **PASSED** |
| XD-05 | `D-PLAT-09` / `D-AUTH-01..25` / `D-AGENT-01..16` / `D-P10-01..18` / `D-P11-01..14` **未被 supersede** | 命令 | **PASSED** |
| XD-06 | 命名空间计数：`D-PLAT` 17 · `D-AUTH` 25 · `D-AGENT` 16 · `D-P10` 18 · `D-P11` 14 · **`D-P12` 15** | 命令 | **PASSED** |
| XD-07 | 平台级 supersession 关系行 **恒 = 1**（`D-B14-08`）；本轮新增 = **0** | 命令 | **PASSED** |
| XD-08 | `PLATFORM_DECISION_LOG.md` 相对 HEAD 的**内容删除行 = 恰 1**（仅顶部 `Status` 行）⇒ 既有决策正文**零改写** | 命令 | **PASSED** |
| XD-09 | `D-P12-` 冻结前全仓命中 = **0** ⇒ 无命名空间冲突 | 命令 | **PASSED** |

## 15. CF — 交叉一致性处置终态

| ID | 事项 | 依据 | 状态 |
|---|---|---|---|
| CF-01 | `CF-1` resources space/owner「已覆盖」陈述 vs 实测 ⇒ **CLARIFIED**；**不得据此自动创建** `space_id`/`owner_id`-leading 索引；「documented coverage claim」与「implemented coverage」**必须区分** | `CF-1 = CLARIFIED` | **FROZEN-DESIGN** |
| CF-02 | `CF-2` `ix_aimodels_capability`（`T-1`）⇒ **RESOLVED**：采用 `D-P12-14` **DO NOT IMPLEMENT** | `CF-2 = RESOLVED` · `D-P12-14` | **FROZEN-DESIGN** |
| CF-03 | `CF-3` stale `ix_rp_permission` 名 ⇒ **CLARIFIED**：canonical = `ix_role_permissions_permission`；**不 rename** | `CF-3 = CLARIFIED` · `D-P12-12` | **FROZEN-DESIGN** |
| CF-04 | `CF-4` B0 缺 `platform_memberships` 小节 ⇒ **CLARIFIED**：**不自动**转成 index requirement；按 `D-P12-02` 单独 adjudicate | `CF-4 = CLARIFIED` | **FROZEN-DESIGN** |
| CF-05 | `CF-5` partial-only ⇒ **RESOLVED**：`partial index ≠ full FK coverage`；**继续单独统计** | `CF-5 = RESOLVED` · `D-P12-05` | **FROZEN-DESIGN** |
| CF-06 | `CF-6` P10 建表 / P12 建索引 ⇒ **CLARIFIED**：`P10 schema ownership + P12 index ownership`，**非阶段错误** | `CF-6 = CLARIFIED` · `D-P12-08` | **FROZEN-DESIGN** |

## 16. TI — `T-1` 终态

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| TI-01 | `ix_aimodels_capability` ⇒ **DO NOT IMPLEMENT**（文档引用 `capability`，实际列 = `capabilities` JSONB；既有设计**明确排除** JSONB GIN；现行 column reference **非有效 canonical implementation target**） | **`D-P12-14`** | **FROZEN-DESIGN** |
| TI-02 | `T-1` **CLOSED as stale / mismatched design claim** | **`D-P12-14`** · `CF-2 = RESOLVED` | **FROZEN-DESIGN** |
| TI-03 | **不得**偷换为 `GIN(capabilities)`；**不得**发明其他 JSONB index | **`D-P12-14`** · `INDEX_STRATEGY §2` | **FROZEN-DESIGN** |
| TI-04 | append-only clarification 已落地：historical `ix_aimodels_capability` proposal **is not a P12 implementation target** until a separate schema/query contract explicitly defines a valid queryable key/path | **`D-P12-14`** · PDL 附录 I.8 | **FROZEN-DESIGN** |

## 17. SCOPE — Scope Integrity

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| SCOPE-01 | 本轮写入面 = **3 份 `P12_*.md`（新建）** + **`PLATFORM_DECISION_LOG.md`（冻结写入）** + **3 份索引策略文档（append-only clarification）**；**无代码/迁移/测试/配置** | 命令 | **PASSED** |
| SCOPE-02 | **未改写**任何既有冻结正文（PDL 内容删除行 = 1；澄清文档删除行 = 0） | 命令 | **PASSED** |
| SCOPE-03 | `CREATE INDEX` / `CREATE UNIQUE INDEX` / `ALTER INDEX` / `DROP INDEX` / `REINDEX` 新增 = **0** | 命令 | **PASSED** |
| SCOPE-04 | `DDL = 0` · `DML = 0` · `migration = 0` · `code = 0` · `test = 0` · `config = 0` | 命令 | **PASSED** |
| SCOPE-05 | `commit = 0` · `tag = 0` · `push = 0`（HEAD 仍 `034ee97` · tags 仍 8 · remote none） | 命令 | **PASSED** |
| SCOPE-06 | **P12 canonical scope** = ① Frozen P12 indexes ② Explicitly evidenced Event/Audit indexes ③ Explicitly adjudicated FK reverse-lookup indexes ④ Explicitly evidenced ACL / Agent / Tool query indexes | **`D-P12-15`** | **FROZEN-DESIGN** |
| SCOPE-07 | **六类"不包括"**：「just in case」indexes · future Runtime speculation · future business-module speculation · authorization policy indexes **without query evidence** · trigger-generated performance guesses · schema redesign · index renaming cleanup | **`D-P12-15`** | **FROZEN-DESIGN** |
| SCOPE-08 | **不得**因 Agent Runtime 即将实现而提前批量创建可能查询索引（禁 Runtime future query speculation 作证据） | **`D-P12-07`** · **`D-P12-15`** | **FROZEN-DESIGN** |

## 18. GATE

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| GATE-01 | `P12 DECISION FREEZE = PASSED`（15/15 OQ `FROZEN` ⇒ `D-P12-01..15`） | PDL `P12 Canonical Model` · 附录 I | **PASSED** |
| GATE-02 | `P12 IMPLEMENTATION = NOT AUTHORIZED` | 本轮指令 §0/§19 | **BLOCKED** |
| GATE-03 | `P13 IMPLEMENTATION = NOT AUTHORIZED` | `D-PLAT-09` | **BLOCKED** |
| GATE-04 | `Runtime Implementation Gate = CLOSED` | `D-AGENT-16` | **BLOCKED** |
| GATE-05 | 零实施复核：`CREATE/ALTER/DROP INDEX = 0` · `DDL/DML = 0` · `migration = 0` · `code/test/config = 0` · `commit/tag/push = 0` | 命令 | **PASSED** |

## 19. TRACE — OQ ↔ Matrix（15/15）

| ID | OQ | 冻结出处 | 对应行 | 状态 |
|---|---|---|---|---|
| TRACE-01 | `OQ-P12-01` | `D-P12-01` | INV-12 · INV-13 · DEP-04 | **FROZEN-DESIGN** |
| TRACE-02 | `OQ-P12-02` | `D-P12-02` | QE-01 · QE-02 · QE-03 | **FROZEN-DESIGN** |
| TRACE-03 | `OQ-P12-03` | `D-P12-03` | TS-03 · TS-04 | **FROZEN-DESIGN** |
| TRACE-04 | `OQ-P12-04` | `D-P12-04` | UQ-05 · UQ-07 | **FROZEN-DESIGN** |
| TRACE-05 | `OQ-P12-05` | `D-P12-05` | PART-04 · PART-05 · PART-06 | **FROZEN-DESIGN** |
| TRACE-06 | `OQ-P12-06` | `D-P12-06` | UQ-03 · UQ-04 · UQ-06 | **FROZEN-DESIGN** |
| TRACE-07 | `OQ-P12-07` | `D-P12-07` | SCOPE-08 | **FROZEN-DESIGN** |
| TRACE-08 | `OQ-P12-08` | `D-P12-08` | P10-04 · P10-06 · P10-07 · PGRP-05 · DEP-02 · DEP-08 | **FROZEN-DESIGN** |
| TRACE-09 | `OQ-P12-09` | `D-P12-09` | P11-03 · P11-04 · P11-06 · FK-09 | **FROZEN-DESIGN** |
| TRACE-10 | `OQ-P12-10` | `D-P12-10` | PGRP-03 · PGRP-04 · PGRP-05 · UQ-07 | **FROZEN-DESIGN** |
| TRACE-11 | `OQ-P12-11` | `D-P12-11` | DUP-04 · DUP-05 | **FROZEN-DESIGN** |
| TRACE-12 | `OQ-P12-12` | `D-P12-12` | NAME-02 · NAME-03 · NAME-05 | **FROZEN-DESIGN** |
| TRACE-13 | `OQ-P12-13` | `D-P12-13` | FK-06 · FK-07 · FK-08 · FK-09 · FK-10 · QE-03 | **FROZEN-DESIGN** |
| TRACE-14 | `OQ-P12-14` | `D-P12-14` | TI-01 · TI-02 · TI-03 · TI-04 · CF-02 | **FROZEN-DESIGN** |
| TRACE-15 | `OQ-P12-15` | `D-P12-15` | SCOPE-06 · SCOPE-07 · SCOPE-08 | **FROZEN-DESIGN** |

## 20. 汇总（**脚本实测** · `p12_freeze_acceptance.log`）

| 分组 | 行数 | `ASSET` | `PASSED` | `FROZEN-DESIGN` | `BLOCKED` |
|---|---|---|---|---|---|
| CF | 6 | 0 | 0 | 6 | 0 |
| DEP | 8 | 6 | 0 | 1 | 1 |
| DUP | 6 | 3 | 1 | 2 | 0 |
| FK | 13 | 2 | 5 | 6 | 0 |
| GATE | 5 | 0 | 2 | 0 | 3 |
| INV | 14 | 0 | 11 | 3 | 0 |
| NAME | 6 | 1 | 1 | 4 | 0 |
| P09 | 6 | 0 | 5 | 1 | 0 |
| P10 | 7 | 2 | 1 | 4 | 0 |
| P11 | 6 | 2 | 1 | 3 | 0 |
| PART | 6 | 0 | 2 | 4 | 0 |
| PGRP | 6 | 1 | 1 | 4 | 0 |
| QE | 6 | 2 | 1 | 3 | 0 |
| SCOPE | 8 | 0 | 5 | 3 | 0 |
| TI | 4 | 0 | 0 | 4 | 0 |
| TRACE | 15 | 0 | 0 | 15 | 0 |
| TS | 5 | 2 | 1 | 2 | 0 |
| UQ | 7 | 0 | 4 | 3 | 0 |
| XD | 9 | 0 | 9 | 0 | 0 |
| **合计** | **143** | **21** | **50** | **68** | **4** |

**END OF P12 ACCEPTANCE MATRIX（2026-09-25 · DECISION FREEZE · 零实施）**
