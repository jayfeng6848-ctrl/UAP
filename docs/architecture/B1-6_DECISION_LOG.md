# B1-6 Decision Log

**Stage**: B1-6（= P08 AI Gateway）— Human Decision Freeze
**Status**: **FROZEN — A（2026-09-16）**
**Scope of this document**: 仅记录 Human 已裁定事项。**不含任何未经裁定的新设计。**
**Design-Layer Decision Freeze**: D-1 / D-2 / T-1 / D-3 / D-4 / DC-1 = **FROZEN / DEFERRED（2026-09-16 第二轮）** —— 见 §9

---

## 0. Baseline

```
HEAD           = 964ea2c47f1b561a1dca5abed45ca4bc89d9f5e7
branch         = main
migration      = 0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009
head migration = 0009_timestamp_precision（唯一 head）
0010           = ABSENT
formal uap     = 0 tables · alembic_version = absent
staged = 0 · modified = 5 · untracked = 30 · tags = 4
Architecture Guard = 9 passed · Core → Domain = 0
```

**阶段编号依据**：`STEP1B_SCHEMA_DEPENDENCY.md:169`（`P08 | AI Gateway | ai_providers → ai_models → ai_routes → ai_policies → ai_request_logs`）·
`STEP1B_B0_GATE_REPORT.md:45`（拓扑 `… P07 tool → P08 AI → P09 agent …`）·
`migrations_alembic/versions/0009_timestamp_precision.py:35`（「P08 后续 migration 编号顺延至 0010」）。
> **D-B16-01 = FROZEN — A** 已由 Human 确认下列绑定；**不得据此改变历史 B0 文档中已有的 phase 定义**。

---

## 1. 最终裁定总表

| ID | 主题 | 状态 |
|---|---|---|
| **D-B16-01** | B1-6 编号绑定 | ✅ **FROZEN — A** |
| **D-B16-02** | `ai_routes` / `ai_policies` 的 `tenant_id` / `space_id` FK | ✅ **FROZEN — A** |
| **D-B16-03** | `ai_request_logs` FK（列范围 + 删除规则） | ✅ **FROZEN — A** |
| **D-B16-04** | `ai_request_logs.status` 取值域 | ✅ **FROZEN — A** |
| **D-B16-05** | `ai_request_logs` 分区创建时机 | ✅ **FROZEN — A** |
| **D-B16-06** | `ai_providers.adapter` 语义边界 | ✅ **FROZEN — A** |
| **D-B16-07** | UQ 计数口径 | ✅ **FROZEN — A** |
| **D-B16-08** | `SCHEMA_DEPENDENCY:136` 「Phase 08」陈旧引用 | ✅ **FROZEN — C** |
| **D-B16-09** | B1-6 PREP 文档集 | ✅ **FROZEN — A** |
| **D-B16-10** | Canonical Test Matrix | ✅ **FROZEN — A** |
| **D-B16-11** | `ai_providers` 平台级 ROOT | ✅ **FROZEN — A** |

```
FROZEN = 11        OPEN = 0        BLOCKING = 0
```

---

## 2. 逐项决策记录

### D-B16-01 — B1-6 编号绑定 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | 全库 `B1-6` / `B1.6` / `B16` / `b1_6` **0 命中**（无字面定义）；B1-6 与哪个 phase 绑定未定 |
| **证据** | `SCHEMA_DEPENDENCY:169`（P08 = AI Gateway 五表）· `B0_GATE_REPORT:45`（phase 拓扑）· P01–P07 实测全部已建（migration 0001–0009 / 20 张业务表无缺）· `0009_timestamp_precision.py:35` |
| **冲突** | 无字面定义 ⇒ 绑定属**推导**；`B1-x → P-x` 映射非 1:1（B1-1=P01+P02 · B1-2=P03+P05 · B1-3=P04） |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：`B1-6 = P08 AI Gateway`。**约束**：不得据此改变历史 B0 文档中已有的 phase 定义 |

### D-B16-02 — `ai_routes` / `ai_policies` 的 `tenant_id` / `space_id` FK 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | 该两表的 tenant/space 归属是否建立 FK？删除规则为何？ |
| **证据（四来源冲突）** | `SCHEMA_DEPENDENCY:74/75`「tenant/space NULL 无 FK」· FK 列「—（无强 FK）」<br>`CONSTRAINT_MATRIX:327` ai_routes FK 行仅 `primary_model_id`；`:333-341` ai_policies 段**无 FK 行**<br>`CORE_DOMAIN_MODEL:391/402` FK 行**无 → 目标、无删除规则**<br>`ER_MODEL:352-353/361-362` **明确标 FK**（唯一支持来源） |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：加 FK，**`ON DELETE RESTRICT`** |
| **冻结事实（权威）** | `ai_routes.tenant_id → tenants.id ON DELETE RESTRICT`<br>`ai_routes.space_id → spaces.id ON DELETE RESTRICT`<br>`ai_policies.tenant_id → tenants.id ON DELETE RESTRICT`<br>`ai_policies.space_id → spaces.id ON DELETE RESTRICT`<br>**四列均保持 nullable** |
| **边界** | **不得**自行增加其他 tenant/space FK 或 trigger |

### D-B16-03 — `ai_request_logs` FK 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | `ai_request_logs` 是否建 FK？对哪些列？删除规则为何？ |
| **证据（三来源冲突）** | `SCHEMA_DEPENDENCY:76`「分区表；FK 尽量保持 NULL 宽松或**仅 provider/model**」（条件式）<br>`CONSTRAINT_MATRIX:343-352` **FK 行 = 0** · `CORE_DOMAIN_MODEL:407-412` **FK 行 = 0**<br>`ER_MODEL:375-376` `provider_id FK` / `model_id FK`（明确标 FK）；`:327` 另有 `agents \|\|--o{ ai_request_logs` 关系线<br>`CORE §11.1:985`「`ai_models → ai_request_logs`（**若建 FK**）」条件式 |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：建 FK，列范围 = `provider_id` + `model_id`，**两列均 `ON DELETE RESTRICT`** |
| **冻结事实（权威）** | `ai_request_logs.provider_id → ai_providers.id ON DELETE RESTRICT`<br>`ai_request_logs.model_id → ai_models.id ON DELETE RESTRICT`<br>**`agent_id` = NO FK · `actor_id` = NO FK · `tenant_id` = NO FK · `space_id` = NO FK** |
| **边界** | **不得**形成 P08 → P09 forward FK dependency |

### D-B16-04 — `ai_request_logs.status` 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | `status` 是否建立取值域 CHECK？ |
| **证据** | `CONSTRAINT_MATRIX:350` = `status IN (...)`（**success/error/...按实现定义**）⇒ 从未冻结<br>词表先例：`CORE_DOMAIN_MODEL` 12 处真实词表（含 `agent_versions` `('draft','published','deprecated','revoked')`、`tool_executions` `('running','succeeded','failed','denied','timeout')`）；`tool_versions` = **0 CK**（D-B15-04 = FROZEN — A）<br>`STEP1B_SCHEMA_TEST_MATRIX:19 S5`「CHECK 生效（status/scope/risk/classification/enum 类）」 |
| **Human wording（2026-09-16，逐字权威）** | *`ai_request_logs.status` 在 B1-6 中不新增取值域 CHECK。不凭空定义或冻结新的 status vocabulary。沿用 D-B15-04 的边界口径：本阶段仅保留 status 字段，不建立新的 status CHECK 约束。Canonical Test Matrix 中，S5 对 `ai_request_logs.status` 的 CHECK 检查不适用/予以明确豁免。* |
| **冻结事实** | `status CHECK = 0`；**S5 对该列明确豁免**（须登记入 B1-6 Canonical Test Matrix） |
| **边界** | **不得**自行增加 status vocabulary |

### D-B16-05 — `ai_request_logs` 分区创建时机 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | 父表与子分区在哪个 phase 创建？ |
| **证据** | `SCHEMA_DEPENDENCY:267`（建父表 `PARTITION BY RANGE (occurred_at)` + **当月子分区**）· `:270`（downgrade 先 DROP 子分区）<br>`:169`（P08 行，未提分区）vs `:171`（P10 行，显式「分区父表 + 初始子分区」）<br>`CORE:412/414`（PK 含分区键 / 按月 RANGE）· `:921`（分区键 UTC 月边界）· `INDEX_STRATEGY:147-151`（`ai_request_logs（分区表）`）<br>`STEP1B_SCHEMA_TEST_MATRIX:112 M8`（分区表子分区创建正确）· `STEP1A_DESIGN_REPORT:511 R2`（按月分区需预建，否则写入失败） |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：**P08 建父表 + 当月子分区** |
| **边界** | 分区命名 / 数量 / 维护机制属 **B1-6_SCHEMA_DESIGN** 交付内容，本 Log 不预先冻结 |

### D-B16-06 — `ai_providers.adapter` 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | `adapter` 在 P08 的语义边界？是否允许代码侧连接？ |
| **证据** | `CORE:370`（适配器注册键，代码侧注册表）· `:709`（指向 `intelligence/providers` 中已注册的适配器）<br>`ER_MODEL:332` · `CONSTRAINT_MATRIX:307`（NN，**无 CK / 无 UQ / 无 FK**）<br>`intelligence/providers/interfaces.py`（`ProviderRegistry` **类已存在实现体**，全库 **0 处调用**）<br>`AIGateway` Protocol 存在无实现；`FORBIDDEN_DIRECT_IMPORTS = ("openai","anthropic","deepseek","ollama")` |
| **Precedent** | **D-B15-09 = FROZEN — A**：`handler_ref` 仅文本引用，不 resolve / load / execute / plugin registration / runtime discovery |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：`adapter` 仅文本引用；**P08 不引入解析 / 加载 / 注册** |
| **边界** | 不得把 runtime 行为带入 P08；不得引入 adapter 校验；不得实例化 registry |

### D-B16-07 — UQ 计数口径 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | P08 是否沿用 D-B15-06 的 UQ 计数口径？ |
| **证据** | P08 共 4 个 UQ：`ai_providers(key)` / `ai_models(provider_id, model_key)` = 纯列；`ai_routes` / `ai_policies` = 含 `COALESCE(...)` **表达式**<br>`INDEX_STRATEGY:137/139/144` 三条均标「UQ」，未区分形式<br>`B1-5_DECISION_LOG:111`（表达式唯一不可为 UNIQUE CONSTRAINT）· D-B15-06 = `UNIQUE CONSTRAINT = 1` · `UNIQUE INDEX = 3` |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：沿用 D-B15-06 口径 ⇒ `UNIQUE CONSTRAINT = 2` · `UNIQUE INDEX = 2` |
| **边界** | 不得修改计数规则；不得把表达式唯一计为 constraint |

### D-B16-08 — `SCHEMA_DEPENDENCY:136` 「Phase 08」陈旧引用 【✅ FROZEN — C】

| 项 | 内容 |
|---|---|
| **Exact stale statement** | `STEP1B_SCHEMA_DEPENDENCY.md:136` =「该约束加入 **Phase 08** 尾部。」（描述 `agents.current_version_id` deferred FK） |
| **正确归属证据** | `:170`（P09 行「**补** `agents.current_version_id` FK」）· `B0_GATE_REPORT:45`（`P09 agent(…+补 FK)`）· `B1-4_DEPENDENCY:132`（P09 Agent）· `B1-5_SCOPE:42`（P09） |
| **Human Decision（2026-09-16）** | **C —— FROZEN**：**不回改 B0**；加注说明由 **B1-6 文档**承载 |
| **B1-6 侧义务（须落地）** | B1-6 文档必须承载下列说明：**该处「Phase 08」属于陈旧引用；`agents.current_version_id` deferred FK 的正式归属为 P09。** |
| **边界** | **不得**修改 `STEP1B_SCHEMA_DEPENDENCY.md:136`；不得把该修订混入 B0 文件 |

### D-B16-09 — B1-6 PREP 文档集 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | B1-6 文档集范围与命名？ |
| **Precedent** | B1-4 = 12 份（全 tracked）· B1-5 = 9 份（全 untracked）· 现状：P08 专属文档 **0 份** |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：沿用 **B1-5 的 9 份模式** |
| **冻结文档集（9 份载体）** | ① `B1-6_SCOPE.md` ② `B1-6_DEPENDENCY.md` ③ `B1-6_SCHEMA_DESIGN.md` ④ `B1-6_SECURITY_REVIEW.md` ⑤ `B1-6_API_DESIGN.md` ⑥ `B1-6_TEST_MATRIX.md` ⑦ `B1-6_MIGRATION_PLAN.md` ⑧ `B1-6_DECISION_LOG.md` ⑨ `B1-6_HUMAN_DECISION_FREEZE_PACKAGE.md` |
| **创建状态（截至本 Log）** | ⑧ 已于本阶段创建；**其余 8 份属 DESIGN 交付物，创建属 B1-6 DESIGN Gate** |

### D-B16-10 — Canonical Test Matrix 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | P08 是否建立 canonical test matrix？编号空间？ |
| **证据** | P08 canonical **不存在**（`STEP1B_SCHEMA_TEST_MATRIX` 10 类中无 P08 章节；P08 唯一命中 `:121 SEC4`）<br>先例：B1-4 = **84**（`O-1 = FROZEN — A`）· B1-5 = **39**（`D-B15-07 = FROZEN — A`，独立编号空间 `TS/TF/TC/TV/TM/TSEC/TD`）<br>**5 个测试文件列 ai_* 为 FORBIDDEN/FUTURE**（`test_identity_schema:44-47` · `test_rbac_schema:37-40` · `test_resource_acl_schema:91-94` · `test_tenant_space_schema:53-56` · `test_tool_registry_schema:71-74`）<br>head 断言 = `"0009_timestamp_precision"` **20 处 / 8 文件** |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：建立**独立编号空间**的 canonical matrix（沿用 B1-5 模式） |
| **必须登记项** | **S5 对 `ai_request_logs.status` 的 CHECK 检查不适用 / 明确豁免**（源自 D-B16-04） |
| **边界** | 具体行数与编号属 **B1-6_TEST_MATRIX** 交付内容；**不得修改 tests**（属实施轮） |

### D-B16-11 — `ai_providers` 平台级 ROOT 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | 是否显式冻结「平台级 ROOT / 无 tenant_id / 零 seed」？ |
| **证据** | `SCHEMA_DEPENDENCY:72`（✅ **ROOT**）· `:95`（零依赖）· `:103`（root 组）· `B0_GATE_REPORT:42`（root 清单）<br>`CORE:364-371` fields **无 tenant_id** · `CONSTRAINT_MATRIX:300-309` **无 FK 行** · `ER_MODEL:329-338` **无 tenant_id**<br>`SEED_STRATEGY` **0 命中** · `intelligence/` 6 模块 **无 tenant 提及**<br>有 `updated_at`（`TRIGGER_INVENTORY:19`）；**无** archived_at / deleted_at / status |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：`ai_providers` = **平台级 ROOT / 无 tenant_id / 零 seed** |
| **边界** | 不得自行新增 tenant_id |

---

## 3. Cross-Decision Coupling

```
D-B16-01 ↔ 全部           前置锚点：确定 B1-6 的阶段载体与范围边界
D-B16-02 ↔ D-B16-11      platform-level 语义族：
                         ai_providers「无 tenant_id 列」vs ai_routes/ai_policies「tenant_id NULL」
D-B16-03 ↔ D-B16-05      分区 + FK：§9 仅对 events/audit_logs 声明「不设强制 FK」，未覆盖 ai_request_logs
D-B16-04 ↔ D-B16-10      S5 豁免须登记入 canonical matrix ← 已由 D-B16-04 措辞明确
D-B16-06 ↔ D-B15-09      边界口径先例：handler_ref 仅文本引用（FROZEN — A）
D-B16-07 ↔ D-B15-06      UQ 计数口径先例：1 constraint + 3 index（FROZEN — A）
D-B16-08 ↔ P09 boundary   :136「Phase 08」与 :170「P09」矛盾；加注义务落 B1-6 文档（D-B16-08 = C）
D-B16-09 ↔ repository/document strategy
                         9 份载体已冻结；入库(tracking) 策略另属 HD-5 / D-MCI-05
D-B16-10 ↔ existing test suite
                         5 处 FORBIDDEN/FUTURE + 20 处 head 断言 + smoke 表清单为实施轮必然连带修改
```

---

## 4. 由裁定推导的事实盘点（非设计）

> 下列为**已冻结决策的直接推论**，用于一致性核验。精确 CK 命名/条数与索引命名属 **B1-6_SCHEMA_DESIGN** 交付内容。

```
tables = 5     PK = 5（ai_request_logs = (id, occurred_at) 复合）
FK     = 8     （7 RESTRICT + 1 CASCADE）
  1  ai_models.provider_id      → ai_providers.id  CASCADE    冻结文档明确
  2  ai_routes.primary_model_id → ai_models.id     RESTRICT   冻结文档明确
  3  ai_routes.tenant_id        → tenants.id       RESTRICT   D-B16-02
  4  ai_routes.space_id         → spaces.id        RESTRICT   D-B16-02
  5  ai_policies.tenant_id      → tenants.id       RESTRICT   D-B16-02
  6  ai_policies.space_id       → spaces.id        RESTRICT   D-B16-02
  7  ai_request_logs.provider_id→ ai_providers.id  RESTRICT   D-B16-03
  8  ai_request_logs.model_id   → ai_models.id     RESTRICT   D-B16-03
UQ          = 4  （constraint 形式 2 · index 形式 2 —— D-B16-07）
status CK   = 0  （D-B16-04）
trigger     = 4  （tg_ai_providers/ai_models/ai_routes/ai_policies_set_updated_at）
function    = 0 新增（复用 set_updated_at）
seed        = 0
P08 → P09 forward FK = 0（agent_id 无 FK）
partition   = ai_request_logs 父表 + 当月子分区（D-B16-05）
```

---

## 5. AUTH-02 — B0 Limited Sync（已授权并执行）

**授权范围（严格限定）**

```
STEP1B_SCHEMA_DEPENDENCY.md  :74 / :75 / :76
STEP1B_CONSTRAINT_MATRIX.md  :327 / :333-341 / :343-352
CORE_DOMAIN_MODEL.md         :391 / :402 / :985
```

**同步依据**：仅根据已冻结的 **D-B16-02 / D-B16-03** 的 FK 事实。

**执行结果**

| # | 位置 | 变更 |
|---|---|---|
| 1 | `STEP1B_SCHEMA_DEPENDENCY.md:74` | `ai_routes` 依赖列去掉「无 FK」；FK 列补 `tenant_id NULL → tenants.id RESTRICT` / `space_id NULL → spaces.id RESTRICT` |
| 2 | `STEP1B_SCHEMA_DEPENDENCY.md:75` | `ai_policies` 依赖列「（NULL 无 FK）」→「（NULL 允许）」；FK 列「—（无强 FK）」→ 两条 RESTRICT |
| 3 | `STEP1B_SCHEMA_DEPENDENCY.md:76` | `ai_request_logs` FK 列由条件式表述改为确定的 `provider_id` / `model_id` RESTRICT；注记 `agent_id`/`actor_id`/`tenant_id`/`space_id` 无 FK |
| 4 | `STEP1B_CONSTRAINT_MATRIX.md:327` | `ai_routes` FK 行补两条 RESTRICT |
| 5 | `STEP1B_CONSTRAINT_MATRIX.md:333-341` | `ai_policies` 段**新增 FK 行**（原无） |
| 6 | `STEP1B_CONSTRAINT_MATRIX.md:343-352` | `ai_request_logs` 段**新增 FK 行**（原无） |
| 7 | `CORE_DOMAIN_MODEL.md:391` | `ai_routes` FK 行补 → 目标 + `ON DELETE RESTRICT` |
| 8 | `CORE_DOMAIN_MODEL.md:402` | `ai_policies` FK 行补 → 目标 + `ON DELETE RESTRICT` |
| 9 | `CORE_DOMAIN_MODEL.md:985` | `ai_models → ai_request_logs` 由「(若建 FK)」改为「FK 已建，**ON DELETE RESTRICT**」 |

**遵守声明**
```
✅ 未修改授权范围之外的 B0 内容
✅ 未重新设计 / 未重新解释任何已冻结决策
✅ 未改变 D-B16-01～11 的最终裁定
✅ 未修改 STEP1B_SCHEMA_DEPENDENCY.md:136（D-B16-08 = C）
✅ 未做格式化 / 排序 / 全文重写 / 无关清理
✅ 未修改 pyproject.toml / requirements.txt / STEP1B_TRIGGER_INVENTORY.md
✅ 修改前状态已保存（含原有 Human 修改的 patch），见 §7
```

---

## 6. 冻结新产生的文档不一致（已报告，**未修复**）

| # | 内容 | 状态 |
|---|---|---|
| **N-1** | `CORE_DOMAIN_MODEL:985` 的原类别标签为「技术子实体」（该节其余条目均 CASCADE 族），而冻结规则为 RESTRICT。本次**仅按授权范围标注了 FK 与删除规则**，**未改动类别标签** | **未解决**（超出 AUTH-02「仅按 D-B16-02/03 修正 FK 事实」的范围） |
| **N-2** | `SCHEMA_DEPENDENCY:76` 原有的「FK 尽量保持 NULL 宽松」取向已被本次同步替换为确定的 RESTRICT 事实；该句原表述的取向与其后冻结决策相反 | 已随同步消解（该位置在授权范围内） |
| **N-3** | `ai_request_logs` 带 FK RESTRICT ⇒ 清除 `ai_providers` / `ai_models` 前须先清 request log；与 `CORE:963`（90 天分区 hard delete）、`CORE:985`（模型目录随 provider purge 清理）的**运维顺序需另行明确** | **未解决**（需另案） |
| **N-4** | `SCHEMA_DEPENDENCY:136` 保持原样（D-B16-08 = C）；加注义务由 B1-6 文档承载（见 D-B16-08 条目） | 已由裁定承接 |
| **N-5** | `CONSTRAINT_MATRIX:350` 的 `status IN (...)`（按实现定义）**未被修改**（D-B16-04 非 AUTH-02 的同步依据） | 保持原样，与 D-B16-04 = 零新增 CK 不冲突 |

---

## 7. 修改前状态记录（AUTH-02 要求 7）

```
修改前 sha256(前 16 位)：
  1df70b2a59c89ad5  docs/architecture/STEP1B_SCHEMA_DEPENDENCY.md   （原有 Human 修改，未回退）
  3dab85f30ec807af  docs/architecture/STEP1B_CONSTRAINT_MATRIX.md   （原有 Human 修改，未回退）
  89215cefce57101d  docs/architecture/CORE_DOMAIN_MODEL.md          （修改前为 tracked + clean）

原有 Human 修改（2 份被授权文件）已单独存为 patch：PRE_existing_human_diff.patch（25 行）
最终 `git diff` 为「原有修改 ∪ 本次授权修改」的并集；
「本次授权修改」可比对 PRE_* 备份副本单独得出。
```

---

## 8. 授权与边界

```
AUTH-01  Decision Log 落档                 = APPROVED（本文件）
AUTH-02  B0 Sync（9 个指定位置）            = APPROVED（已按范围执行完成）

本轮未授权（保持 BLOCKED）：
  · B1-6 DESIGN（其余 8 份文档的实质创建）
  · 0010 migration
  · 任何 DDL / DML / migration 执行
  · 业务代码 / 测试修改
  · commit / tag
```

---

## 9. Design-Layer Decision Freeze（第二轮，2026-09-16）

**背景**：B1-6 DESIGN 完成后登记了 5 项「设计层未裁定项」（D-1 ～ D-4 · DC-1）。Human 于 2026-09-16 作出正式裁定；
**本 Log 为该批裁定的唯一权威载体**。本节不改变 D-B16-01 ～ D-B16-11 的任何已冻结内容。

### 9.1 设计层裁定总表

| ID | 主题 | 裁定 | 状态 |
|---|---|---|---|
| **D-1** | `ai_policies` 两条「建议」CHECK | **B = 不实现** | ✅ **FROZEN — B** |
| **D-2** | `ix_aimodels_capability` | **B = 不建立 / 延后** | ✅ **FROZEN — B** |
| **T-1** | `INDEX_STRATEGY` 索引定义引用不存在列 | 登记为待澄清缺陷 | ⏸ **DEFERRED / FUTURE DESIGN CLARIFICATION** |
| **D-3** | `ai_request_logs` 分区维护机制 | **D = 手工运维（Manual Operations）** | ✅ **FROZEN — D** |
| **D-4** | `ai_request_logs` 字段命名 | **A = `prompt_tokens` + `completion_tokens`** | ✅ **FROZEN — A** |
| **DC-1** | 分区子表命名 | **A = `ai_request_logs_<YYYYMM>`** | ✅ **FROZEN — A** |

```
FROZEN = 5        DEFERRED = 1（T-1）        OPEN = 0        BLOCKING = 0
```

### 9.2 D-1 — `ai_policies` 两条「建议」CHECK 【✅ FROZEN — B：不实现】

| 项 | 内容 |
|---|---|
| **Problem** | `ai_policies.budget_daily_usd >= 0` / `latency_budget_ms >= 0` 是否实现 |
| **证据** | `STEP1B_CONSTRAINT_MATRIX.md:340`（ai_policies CK 行）两条标注「（**建议**）」；B0「（建议）」标注全库仅 2 处：`:24` 与 `:340` |
| **Precedent** | `:24` 的同型「建议 CHECK」（`users.failed_attempts`）在 `0003_b1_1_root_identity.py` 中**未落地** —— users 表仅 `ck_users_status` / `ck_users_login` |
| **Human Decision（2026-09-16）** | **B —— FROZEN**：**不实现**该两条 CHECK |
| **冻结事实** | 必做 CHECK 总数保持 **8** · `ai_policies` CHECK 保持 **1** · **不新增 constraint** |
| **Rationale（Human）** | 该两项属 B0「建议 CHECK」，本阶段不实现；参考既有 `users.failed_attempts` 同型「建议 CHECK」未在 0003 中落地的先例 |
| **Affected design sections** | `B1-6_SCHEMA_DESIGN.md` §5.2 / §7 / §8 / §9.2 · `B1-6_SCOPE.md` §2 · `B1-6_DEPENDENCY.md` §7 · `B1-6_SECURITY_REVIEW.md` §5 O-6 |
| **Migration impact** | **无**（0010 upgrade 不含该两条；downgrade 不变） |
| **Test impact** | **无**（AC 计数不变；canonical 保持 38） |
| **Operational impact** | `budget_daily_usd` / `latency_budget_ms` 在 DB 层**允许负值**（两列均 NULL 允许，PG CHECK 对 NULL 不生效）；无其他层承担该取值域约束 |
| **Boundary** | 日后若实现，属**新决策**，须显式授权 |

### 9.3 D-2 — `ix_aimodels_capability` 【✅ FROZEN — B：不建立 / 延后】

| 项 | 内容 |
|---|---|
| **Problem** | `ix_aimodels_capability`（partial btree）是否在本阶段建 |
| **证据** | `STEP1B_INDEX_STRATEGY.md:139` = ``ix_aimodels_capability ON (capability) WHERE enabled``，标注「若路由缓存充分可免（**P3**）」；`:218` 列入「P3 候选（确认后建）」 |
| **Precedent** | P3 候选 6 项（`ix_users_status` / `ix_tenants_status` / `ix_rp_permission` / 部分 roles FK 反查 / `agents.owner_id` / `ix_aimodels_capability`）实测**全部未在 0003–0008 落地** |
| **Human Decision（2026-09-16）** | **B —— FROZEN**：**不建立 / 延后** |
| **冻结事实** | 非 PK 索引 = **5**（不变）· UQ accounting 不变（2 constraint + 2 index）· Canonical Test Matrix = **38**（不变）· **不新增 AX2 索引断言** |
| **同时登记** | **T-1 = DEFERRED**（见 §10） |
| **Affected design sections** | `B1-6_SCHEMA_DESIGN.md` §3.3 / §7 / §8 / §9.2 · `B1-6_TEST_MATRIX.md` §4 · `B1-6_DEPENDENCY.md` §7 |
| **Migration impact** | **无**（0010 不含 `CREATE INDEX ix_aimodels_capability`；downgrade 不变） |
| **Test impact** | **无**（AX2 断言值保持 5；canonical 保持 38） |
| **Operational impact** | 无（可选查询优化未落地；不影响 schema 完整性） |
| **Boundary** | 不修改 B0 · 不擅自决定目标列 · 不宣布该索引作废 |

### 9.4 T-1 — `INDEX_STRATEGY` 索引定义引用不存在列 【⏸ DEFERRED】

原文事实（**逐字保留，不做任何改动**）
```
位置 : STEP1B_INDEX_STRATEGY.md
定义 : ix_aimodels_capability ON (capability) WHERE enabled
事实 : ai_models 不存在 capability 列，仅存在 capabilities jsonb
```
**本阶段处置（Human 明确）**：**不创建该索引 · 不修改 B0 `STEP1B_INDEX_STRATEGY.md` · 不擅自决定目标列 ·
不将目标改为 `ai_models.capabilities` · 不改为其他表 · 不宣布该索引作废 · 登记为 DEFERRED / FUTURE DESIGN CLARIFICATION。**

### 9.5 D-3 — `ai_request_logs` 分区维护机制 【✅ FROZEN — D：手工运维】

| 项 | 内容 |
|---|---|
| **Problem** | 父表/子分区之外的月份分区由何机制产生与清理 |
| **证据** | `STEP1A_DESIGN_REPORT.md:511 R2`（风险等级 中）「按月分区需预建与清理，否则写入失败」；缓解方式列出「分区管理 job + 监控」或「pg_partman」；`CORE:963`（90 天分区 hard delete）· `:965`（默认 90 天）· `:1054`（到期整分区 drop） |
| **基础设施实测** | `apps/worker/main.py` = placeholder（无 job 注册）· compose 3 服务（无 job 服务）· 无 celery / apscheduler / cron 依赖 · `postgres:16-alpine` 不含 pg_partman · 全仓无分区/调度运行时代码 |
| **Human Decision（2026-09-16）** | **D —— FROZEN**：**手工运维（Manual Operations）** |
| **冻结事实** | B1-6 / P08 只负责 **parent partitioned table + current-month child partition**（= D-B16-05 不变） |
| **0010 不得包含** | 预建未来月份 · 自动清理机制 · worker/job · scheduler · pg_partman · `CREATE EXTENSION` · Docker/compose 修改 · worker runtime 修改 |
| **因此 0010 不负责** | 未来月份自动创建 · 90 天自动清理；**不增加运行时依赖**；**不改变 D-B16-05** |
| **Operational policy（原文记录）** | *Future partition creation and retention cleanup are manual operational responsibilities in P08. Automation is deferred to a future operational/runtime phase.* |
| **Affected design sections** | `B1-6_SCHEMA_DESIGN.md` §6.3 / §8 / §9.2 · `B1-6_SCOPE.md` §4 · `B1-6_MIGRATION_PLAN.md` §4 / §7 / §9 · `B1-6_TEST_MATRIX.md` §11 RF5 · `B1-6_SECURITY_REVIEW.md` §3 |
| **Migration impact** | **无**（0010 只建父表 + 当月子分区；不新增对象） |
| **Test impact** | **无**（canonical 保持 38；RF5 更新归属说明，仍不计入） |
| **Operational impact** | 保留期（90 天）与未来月份分区的创建转为**人工职责**；自动化延后至未来 operational/runtime 阶段 |

### 9.6 D-4 — `ai_request_logs` 字段命名 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | 采用 CORE 细分的 `prompt_tokens` / `completion_tokens`，还是 `CONSTRAINT_MATRIX` 的单一 `tokens` |
| **命名核对** | `CORE_DOMAIN_MODEL.md:413` = `prompt_tokens` + `completion_tokens`；`ER_MODEL.md:378` = 仅 `prompt_tokens`；`STEP1B_CONSTRAINT_MATRIX.md:351` = `tokens`（单一）；当前设计已与 CORE 逐字一致；`B1-6_TEST_MATRIX` / `B1-6_MIGRATION_PLAN` 均未使用具体 token 列名 |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：`prompt_tokens` + `completion_tokens` |
| **冻结事实** | **Schema Design 不变** · `ai_request_logs` 保持 **17 columns** · 总设计列数保持 **73** · **不改成单一 `tokens`** |
| **B0 处置** | **不修改** `CORE_DOMAIN_MODEL.md` · **不修改** `ER_MODEL.md` · **不修改** B0 Constraint Matrix |
| **登记** | `STEP1B_CONSTRAINT_MATRIX.md` 中的 `tokens` 属**陈旧字面引用**；本轮**未授权**修改 B0 文档 |
| **Affected design sections** | `B1-6_SCHEMA_DESIGN.md` §6.1 / §9.2 · `B1-6_SECURITY_REVIEW.md` §5 O-1 · `B1-6_DEPENDENCY.md` §9 O-1 |
| **Migration impact** | **无** |
| **Test impact** | **无**（矩阵未使用该列名） |
| **Operational impact** | **无** |

### 9.7 DC-1 — 分区子表命名 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem** | 子分区命名是否为 `ai_request_logs_<YYYYMM>` |
| **B0 现状** | B0 **无**任何分区子表命名规范（`YYYYMM` / 子分区命名 / `PARTITION OF` 在 B0 中 0 命中）；`SCHEMA_DEPENDENCY:267/270` 只规定「父表 + 当月子分区」与「downgrade 先 DROP 子分区」；`MIGRATION_IMPLEMENTATION_CONTRACT:84` 只管 revision 文件名 |
| **Human Decision（2026-09-16）** | **A —— FROZEN**：**`ai_request_logs_<YYYYMM>`**（例：`ai_request_logs_202609`） |
| **规则** | `<YYYYMM>` 使用 **UTC calendar month** · 当前月份子分区采用该命名 · **downgrade 必须按该命名删除对应 child partition** · 后续手工创建月份分区时**继续遵循该规则** |
| **确认** | PostgreSQL identifier 长度安全（实测 `max_identifier_length = 63`；`ai_request_logs_202609` = 22 字节）· 与当前 migration/downgrade 设计一致 · **不改变 D-B16-05 的 parent + current-month child 边界** |
| **Affected design sections** | `B1-6_SCHEMA_DESIGN.md` §6.3 / §9.1 · `B1-6_MIGRATION_PLAN.md` §4 · `B1-6_TEST_MATRIX.md` §6 AP 附带断言 · `B1-6_SECURITY_REVIEW.md` §5 O-5 |
| **Migration impact** | 命名成为 0010 STEP 6 与 downgrade 步骤 3 的**既定字面**（本阶段不创建 0010） |
| **Test impact** | AP 附带断言的命名项由「首次约定」升为**冻结契约**（canonical 仍 38，不新增条目） |
| **Operational impact** | 后续手工创建月份分区须沿用该命名（与 D-3 = D 一致） |

### 9.8 N-3 状态同步（随 D-3 = D）

`ai_request_logs` 的 provider/model 删除顺序问题**保持不变**；**不得因 D-3 冻结而修改 D-B16-03**。

```
删除路径：
  1) 优先通过分区维护 / 清理处理 request logs
  2) 或在必要情况下显式 DELETE request logs
  3) 再处理 route references
  4) 再删除 models
  5) 最后删除 provider
```
**明确**：分区自动维护机制**不属于** B1-6 migration implementation。

### 9.9 Explicit Non-Decisions（本轮明确「不做」清单）

```
No new CHECK
No new index
No automated partition maintenance
No runtime worker/job
No pg_partman
No B0 correction
No migration implementation
```

---

## 10. Deferred Items（登记，不修复）

| # | 内容 | 状态 |
|---|---|---|
| **T-1** | `STEP1B_INDEX_STRATEGY.md` 的 `ix_aimodels_capability ON (capability) WHERE enabled` 引用 `ai_models` 上不存在的列（该表只有 `capabilities jsonb`） | ⏸ **DEFERRED / FUTURE DESIGN CLARIFICATION**（D-2 = B 同时登记） |
| **N-1** | `CORE_DOMAIN_MODEL:985` 的类别标签「技术子实体」（该节其余条目均 CASCADE 族）与冻结的 RESTRICT 不符 | 已登记（本轮不动 CORE） |
| **O-1** | `STEP1B_CONSTRAINT_MATRIX.md` 的 `tokens` 为陈旧字面引用（D-4 = A 已冻结为 `prompt_tokens` + `completion_tokens`） | 已登记（**本轮不授权修改 B0**） |
| **O-3** | `CORE_DOMAIN_MODEL:985` 未记录 `ai_request_logs.provider_id → ai_providers`（F7） | 已登记（DEFERRED） |
| **O-A** | B1-6 文档对 `STEP1B_INDEX_STRATEGY.md` 的行号引用偏移（实际 `:139`，引作 `:140`） | **只登记，不修复** |
| **O-D** | `B1-6_DEPENDENCY.md` 中 D-1 的依据交叉引用笔误（指向 §9 D-3） | **只登记，不修复** |
| **O-E** | `B1-6_DEPENDENCY.md` 将 `ix_aimodels_capability` 归入「P11 / P12」，而 `INDEX_STRATEGY:218` 未 assign phase | **只登记，不修复** |

---

## 11. Gate

```
D-B16-01 … D-B16-11        = ALL FROZEN（10 × A + 1 × C）—— 未变
D-1 = B FROZEN   D-2 = B FROZEN   T-1 = DEFERRED   D-3 = D FROZEN   D-4 = A FROZEN   DC-1 = A FROZEN
DESIGN DECISION FREEZE     = PASS
OPEN = 0 · BLOCKING = 0

B1-6 HUMAN DECISION FREEZE = FROZEN — A
DECISION LOG               = CREATED（含设计层裁定）
B0 SYNC                    = AUTHORIZED SCOPE ONLY（本轮 B0 = PROTECTED，未修改）
B1-6 DESIGN                = COMPLETE
0010                       = ABSENT
DATABASE                   = UNTOUCHED
IMPLEMENTATION             = BLOCKED
NEXT GATE                  = B1-6 Implementation Authorization（须显式授权）
```
