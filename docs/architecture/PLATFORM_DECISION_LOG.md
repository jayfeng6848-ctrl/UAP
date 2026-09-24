# PLATFORM_DECISION_LOG

**载体性质**：UAP **跨阶段（cross-stage）决策载体**
**Status**：`FROZEN`（`D-PLAT-01`…`D-PLAT-12` 及其子条款经 **2026-09-20** Human 确认；`D-PLAT-13`…`D-PLAT-17` 经 **2026-09-23** Decision Resolution 确认）
**Created**：2026-09-20
**Carrier baseline**：`HEAD = 71c36c1d5129c4f7f1b0d6a2f67d980711ba70ab` · branch `main` · migration head `0011_p09_agent_tool_permission`
**Decision ID namespace**：`D-PLAT-NN`（**新建；不覆盖、不复用任何既有命名空间**）
**写入依据**：`UAP NEXT-STEP DECISION RESOLUTION — READ-ONLY` 报告（2026-09-20）§2.2 拟议分配 + Human 已提供的 `OD-1`…`OD-10` 裁定输入

> **本文件不授权任何变更。** 见 Charter §6。

---

# Charter

## 1. 载体性质与适用范围

1.1 本载体承载**跨阶段**（不属于任何单一 phase / B1-x 阶段）的架构、层规则、迁移治理与路线决策。

1.2 适用范围：

- **适用**：跨阶段生效、影响多个后续阶段的决策（层边界、迁移治理、路线与阶段门、bootstrap 唯一性等）。
- **不适用**：单一阶段的 schema / migration / 测试义务 —— 此类决策仍由该阶段的 `<STAGE>_DECISION_LOG.md` +
  `<STAGE>_HUMAN_DECISION_FREEZE_PACKAGE.md` 承载（先例：`B1-4_*` · `B1-5_*` · `B1-6_*` · `P09_*` ·
  `STEP1B_B1_2_DECISION_LOG.md` · `STEP1B_B1_3_DECISION_LOG.md`）。

1.3 本载体**只记录决策**，不实现、不替代设计文档，也不替代 Migration Contract 等权威规范。

## 2. 与阶段型 Decision Log 的关系

2.1 **关系**：本载体与阶段型 Decision Log **并列**，不构成上下级。阶段型 Decision Log 仍是该阶段决策的
**唯一权威**；本载体不得重新解释、弱化或改写任何阶段型决策。

2.2 **引用规则**：本载体引用阶段型决策时，只允许**引用其编号与结论**，不得复述并替代其论证。

2.3 **冲突处置**：若本载体条目与任一阶段型冻结决策冲突，以**阶段型冻结决策为准**，本载体条目视为失效并
须由 Human 裁定后修订。

## 3. 既有阶段历史编号保持不变

3.1 既有决策命名空间**全部保持不变**，本载体不新增、不改号、不重排：

```
D-B14-01 … D-B14-13     （B1-4，含 R1/R4 增补）
D-B15-01 … D-B15-09     （B1-5）
D-B16-01 … D-B16-11     （B1-6）
D-P09-01 … D-P09-18     （P09，OQ 轮 12 + ND 轮 6）
D-MCI-05                （迁移契约实施相关，非阶段命名空间；**本载体不追溯、不重定义**）
```

3.2 阶段编号（`P00`…`P13`）与 B1 编号（`B1-0`…`B1-6`）在既有文档中的表述**一律不修改**。
`D-PLAT-12.a` 中出现的 `P14` 为**暂定**新增阶段编号，其正式冻结属**独立的 PREP 门**事项。

## 4. 决策状态三态

本载体所有条目使用且仅使用以下三态：

| 状态 | 含义 | 进入条件 |
|---|---|---|
| `INPUT PROVIDED` | Human 已提供决策输入，尚未写入本载体 | Human 口头/书面给出裁定 |
| `WRITTEN` | 决策已写入本载体，内容可供评审 | 本载体成文 |
| `FROZEN` | 决策已冻结，具约束力 | **仅当 Human 明确确认后**方可置为此态 |

4.1 **不得**将以下情形解释为 `FROZEN`：

- 某轮审计或报告判定为 PASS；
- 决策输入已提供；
- 决策已写入本载体（`WRITTEN` ≠ `FROZEN`）。

4.2 尚未确认的实施机制、配置细节、阶段命名，须在条目内显式标注「**待确认**」，不得默认为已定。

## 5. 冻结文档后续注记格式

5.1 **适用范围**：仅用于**冻结文档**（阶段 Decision Log / HUMAN_DECISION_FREEZE_PACKAGE / SCHEMA_DESIGN /
SCOPE / MIGRATION_PLAN / TEST_MATRIX / SECURITY_REVIEW / DEPENDENCY，以及 `STEP1B_*` 设计文档）。
冻结文档的**实质内容不得修改**（不得改结论、改编号、改数值、改顺序）。

5.2 **唯一允许的操作是追加注记（append-only annotation）**，格式如下：

```
> **[D-PLAT-NN 注记 · YYYY-MM-DD]** <一句话说明本注记追加了什么>
> 关联：D-PLAT-NN（本文档第 <章节/行> 处的 <被注记内容>）
> 性质：追加说明 / 状态更新 / 交叉引用。**不修改本文档既有结论。**
```

5.3 **位置**：追加在**被注记章节的末尾**，或在文档末尾的「后续注记」小节；不得插入既有表格行之间
造成语义位移。

5.4 **引用规则**：注记必须写出 `D-PLAT-NN` 编号 + 被注记内容定位 + 注记性质。禁止无编号的自由说明。

5.5 **禁止事项**：

- 禁止改写、删除、重排冻结文档的既有结论 / 编号 / 表格行；
- 禁止在冻结文档中新增强制性规则（新规则只能落在本载体或新阶段文档）；
- 禁止以注记方式"追认"未获授权的变更；
- 禁止重写历史阶段报告（`*_GATE_REPORT.md` / `*_PREP_REPORT.md` / `STEP1A_*`）。

## 6. 授权边界（本载体不自动授权任何变更）

6.1 本载体**不**自动授权：

```
· 代码变更        · 配置变更        · 环境变量变更      · 测试变更
· 迁移变更        · DDL / DML       · seed             · 数据库操作
· 文件修订（B-2′）· 新建顶层包（services/ 等）          · 进入任何实施阶段
· commit / tag / push · remote 或分支变更
```

6.2 每一项变更均须**独立授权**。本载体仅声明"决策是什么"，不声明"何时、由谁执行"。

6.3 本载体的条目即使全部达到 `FROZEN`，也**不构成**对实施轮的授权。

---

# D-PLAT-01 — 服务层落点：新增顶层 `services/` 包

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（NEXT-STEP DECISION FREEZE，项 1）；方案 A-1 选定 |
| **背景** | `ARCHITECTURE.md:54` 与 `DEPENDENCY_RULES.md:40` 早已声明 `Agent ─▶ Policy ─▶ Tool ─▶ Service ─▶ Database`；`CORE_DOMAIN_MODEL.md:219` 与 `STEP1B_B1_3_DECISION_LOG.md:600` 进一步引用「服务层契约」。但仓库实际**不存在任何服务/持久化层包**（实测顶层包：`agent/ apps/ config/ core/ docs/ domains/ infrastructure/ intelligence/ migrations/ migrations_alembic/ scripts/ tests/`），链路中的 `Service` 无落点。 |
| **决策** | 采用**顶层 `services/` 包**作为服务层与业务持久化访问的唯一归属。 |
| **依据** | `ARCHITECTURE.md:51-58`（链路名逐字对齐）· `DEPENDENCY_RULES.md:37-45` · 方案比较见 DECISION RESOLUTION 报告 Task A（A-1 vs A-2 vs A-3） |
| **影响面** | 新增顶层包；`ARCHITECTURE.md:11-21` 分层图须加入 `services`；`DEPENDENCY_RULES.md` 须新增 §7；架构守卫须扩充 |
| **待办** | ① `services/` 包的**内部结构**（模块划分、契约位置）未定义 —— 待 Runtime PREP ② 包建立时点属实施轮，**不属 B-1′** |
| **禁止** | 不得把持久化实现放入 `core/`（见 D-PLAT-02） |

---

# D-PLAT-02 — `core` 保持契约与基础抽象定位

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 6） |
| **背景** | `ARCHITECTURE.md:17-18` 定义 `core/` 为 12 个业务无关模块；`DEPENDENCY_RULES.md:13-14` 规定「Core must stay business-agnostic forever」。但现有守卫 `tests/architecture/test_dependency_rules.py:84-92` 仅禁止 `core → {domains, apps, agent, intelligence, infrastructure}`，**未禁止 `core → sqlalchemy`**（第三方库不在 forbidden 集内）—— 即"core 不得承载持久化"这一语义**当前无守卫**。 |
| **决策** | ① `core` 保持**契约与基础抽象**定位；② `core` **不依赖 `services`**；③ `core` **不承载 SQLAlchemy 业务持久化实现**。 |
| **依据** | `ARCHITECTURE.md:17-18` · `DEPENDENCY_RULES.md:13-14` · 实测 `core` 当前 0 处 `sqlalchemy`/`psycopg` 引用 |
| **影响面** | 需新增守卫：`core ↛ sqlalchemy/psycopg/psycopg2`（G-1）· `core ↛ services`（G-2）。两条**在当前代码上已成立**（前瞻性守卫） |
| **待办** | 守卫的具体断言形式（扩充 `test_core_imports_only_core` 或新增独立测试）待实施轮确定 |
| **禁止** | 不得为"让 core 能落持久化"而放宽既有 forbidden 集 |

---

# D-PLAT-03 — `services` 职责定义

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 7）+ `OD-7` |
| **背景** | 服务层在既有文档中只以链路名出现，职责从未定义。 |
| **决策** | `services` 负责三件事：① **业务用例编排**；② **事务协调**；③ **业务持久化访问**。 |
| **依据** | `DEPENDENCY_RULES.md:40` · `CORE_DOMAIN_MODEL.md:219`（服务层契约）· `STEP1B_B1_2_TRIGGER_STRATEGY.md:48`（审计由应用层/服务层写入） |
| **影响面** | `services` 是**唯一**允许承载业务持久化的业务层；`infrastructure` 保持技术设施语义 |
| **待办** | `services` 内部模块命名与粒度 —— 待 Runtime PREP |

### D-PLAT-03.a — `services` 可以依赖 `domains` 的公开稳定契约

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-7`（**必写项之一**，与 D-PLAT-06.a 成对） |
| **背景** | `OD-7` 明确许可 `services → domains` 方向，以支持可插拔 Domain 的编排接入。既有规则只约束 `core → domains`（禁止），从未约束 `services → domains`。 |
| **决策** | `services` **可以**依赖 `domains` 的**公开稳定契约**。 |
| **依据** | `OD-7` · `DEPENDENCY_RULES.md:6-19`（仅规定 domains→core 允许、core→domains 禁止） |
| **影响面** | **明确不得**新增 `services ↛ domains` 守卫（新增即为违反本条款） |
| **待办** | 「公开稳定契约」的**载体与组织方式尚未定义** —— `OD-7` 已明确留待 **Runtime PREP**；当前 `domains/*` 仅有 `manifest.py`（`DOMAIN_MANIFEST`，`status="placeholder"`） |

---

# D-PLAT-04 — `apps` 边界

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 8）+ `OD-6` |
| **背景** | `ARCHITECTURE.md:11` 将 `apps/` 定义为 `delivery (FastAPI api, worker, frontend)`，但未给出可执行的边界。实测 `apps → {config, core, domains, infrastructure}`。 |
| **决策** | `apps` 负责**入口、请求适配与依赖装配**，**不承载核心业务规则**。 |
| **依据** | `ARCHITECTURE.md:11` |
| **影响面** | 需新增守卫（见 04.a） |
| **待办** | 「核心业务规则」的静态判据不可得 —— 守卫只能以代理方式表达（见 04.a） |

### D-PLAT-04.a — `apps` 对 `infrastructure` 的允许用途与禁止用途

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-6` |
| **决策** | **允许**：`apps` 依赖 `infrastructure` 进行 ① 依赖装配 ② 生命周期管理 ③ 健康检查。<br>**禁止**：`apps` 直接使用 `SQLAlchemy` / `psycopg` 实现**业务持久化**。 |
| **依据** | `OD-6` · 实测 `apps` 当前对 `infrastructure` 的使用：`apps/api/main.py:19`（`reset_engine`）· `:18`（`DatabaseConfig`）· `apps/api/routes/health.py:16`（`check_database`）—— 均属装配/生命周期/健康检查，**合规** |
| **影响面** | **不得**新增 `apps ↛ infrastructure` 守卫（会与 `OD-6` 允许项冲突）。守卫只能是 `apps ↛ sqlalchemy/psycopg` |
| **待办 / 待确认** | ⚠ **代理式守卫局限**：静态分析无法区分"业务持久化"与其他用途。守卫 `apps ↛ sqlalchemy/psycopg` 仅为**代理判据**，语义不等价。此局限须在实施轮文档中如实标注。 |

---

# D-PLAT-05 — `agent` 不直接依赖 `services` 具体实现

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 9） |
| **背景** | 既有守卫 `tests/architecture/test_dependency_rules.py:123-131` 禁止 `agent → {sqlalchemy, psycopg, psycopg2, infrastructure, apps}`，但**未包含 `services`**（该包尚不存在）。 |
| **决策** | `agent` **不直接依赖 `services` 的具体实现**；执行路径经 **Policy / Tool 等契约**进入。 |
| **依据** | `DEPENDENCY_RULES.md:37-45` · `P09_SECURITY_REVIEW.md:55` |
| **影响面** | 需扩充既有守卫的 forbidden 集（G-3）。实测 `agent` 当前内部跨层依赖 = 0，扩充后即成立 |
| **待办** | `agent` 经 Policy/Tool 进入服务层的**具体契约形态**未定义 —— 属 Runtime PREP |

---

# D-PLAT-06 — `domains` 不依赖 `services` / `infrastructure` 实现

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 10）+ `OD-7` |
| **背景** | `DEPENDENCY_RULES.md:6-19` 仅规定 `domains → core` 允许、`core → domains` 禁止；§5 规定「Domains do not define schema in this phase」。未涉及 `domains → services/infrastructure`。 |
| **决策** | `domains` **不直接依赖 `services` 或基础设施实现**，通过**约定契约**协作。 |
| **依据** | `OD-7` · `DEPENDENCY_RULES.md:6-19` · `:47-52` |
| **影响面** | 需新增守卫 `domains ↛ {services, infrastructure}`（G-4）。实测 `domains` 当前内部跨层依赖 = 0 |
| **待办** | **「约定契约」的形式未定义** —— `OD-7` 明确留待 **Runtime PREP** |

### D-PLAT-06.a — 方向澄清（与 D-PLAT-03.a 成对）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-7`（**必写项之一**） |
| **决策** | ① `domains ↛ services`（本条款禁止）；② `domains ↛ infrastructure`（本条款禁止）；③ **`services → domains` 方向由 `D-PLAT-03.a` 许可**，本条款**不构成对其的限制**。 |
| **影响面** | 消费本条款时必须同时读取 `D-PLAT-03.a`；单独引用 06.a 会得出"services 不得 import domains"的**错误结论** |

---

# D-PLAT-07 — Legacy 启动迁移路径停用 + Alembic 唯一正式入口

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 3，C-1 与"C：Alembic 唯一入口"）+ `OD-4` + `OD-9` + `OD-10` |
| **背景** | 契约 `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` §1 规定「**唯一入口**：`alembic.ini` + `migrations_alembic/`」；§16 规定旧 `scripts/migrate.py` + `infrastructure/database/migration.py`「**只读保留**，一个发布周期后下线」。但 `apps/api/main.py:44-53` 的 `ENABLE_MIGRATIONS_ON_STARTUP` 分支实际调用的是**遗留 runner 链**（`migrations/*.sql` + `schema_migrations`），**违背 §1**；且该链不包含 0001–0011，开启后**建不出业务表却启动成功**。 |
| **决策** | ① **停用**应用启动时调用 legacy SQL migration runner 的行为；② **保留**历史 SQL 文件与 legacy runner 本体（**不得删除**）；③ **Alembic 是唯一正式 Schema migration 入口**。 |
| **依据** | Contract §1 · §16 · `migrations_alembic/README.md:3` · DECISION RESOLUTION 报告 §2.1（判定：C-1 属**修复既有契约违规**，非新增冲突） |
| **影响面** | 见 07.a / 07.b / 07.c |
| **待办** | 实施轮改动面：`apps/api/main.py:44-53`（10 行）· `config/settings.py:69` · `tests/unit/test_config.py:29` |

### D-PLAT-07.a — 实现语义（停用范围）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-4` |
| **决策** | ① **删除** `ENABLE_MIGRATIONS_ON_STARTUP` 配置项；② **删除** `apps/api/main.py` 中的应用启动迁移分支；③ **保留** legacy runner 本体（`infrastructure/database/migration.py`）**及其全部测试**（`tests/unit/test_migration_runner.py` · `tests/integration/test_database_integration.py`）；④ **保留** `migrations/*.sql` 文件本体的历史事实。 |
| **依据** | `OD-4` · Contract §16（保留本体）· 实测该配置项仅出现在 3 处：`config/settings.py:69` · `apps/api/main.py:44` · `tests/unit/test_config.py:29` |
| **影响面** | `tests/unit/test_config.py:15-30` 的 `SETTING_ENV_KEYS` 必须同步（删除该键、加入新键 —— 见 D-PLAT-08.a） |
| **注记要求** | `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` §16 的「一个发布周期后旧 runner 下线（README 标注 deprecation）」条款，**执行状态需按 Charter §5 追加注记**（不得改写 §16 正文） |
| **禁止** | 不得删除 legacy runner 或其测试；不得删除 `migrations/*.sql` |

### D-PLAT-07.b — 文档权威归属

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-9` |
| **决策** | `ARCHITECTURE.md` **保留简洁的迁移规则**并**指向 Migration Contract**；**Migration Contract 为权威来源**。 |
| **依据** | `OD-9` · `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md:7`（自称「本 Contract 是 B1 全阶段 migration 的唯一行为规范」） |
| **影响面** | `ARCHITECTURE.md:63-64` 现行表述「Migrations are ordered `.sql` files in `migrations/`, applied transactionally with a `schema_migrations` checksum ledger (`scripts/migrate.py`)」与 Alembic 唯一入口**冲突**，须改为简洁规则 + 指针。 |
| **禁止** | 不得在 `ARCHITECTURE.md` 复述契约全文（避免同一规则多处副本漂移） |

### D-PLAT-07.c — 文档最小修订与冻结文档处理规则

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-10` |
| **决策** | ① **最小修订**仍把 legacy runner 描述为**正式入口**的现行文档与迁移指引；② **不重写历史阶段报告**；③ **冻结文档只允许按规则添加后续注记**（规则见 Charter §5）。 |
| **依据** | `OD-10` · Charter §5 |
| **受影响文档（B-2′ 范围，**本轮未执行**）** | 现行指引 7 处：`ARCHITECTURE.md:11-21`（分层图加 services）、`:63-64`（迁移规则改指针）、`DEPENDENCY_RULES.md`（新增 §7）、`MIGRATION_STRATEGY.md:7`（标注历史入口）、`README.md:48`（改用 `alembic upgrade head`）、`docs/api/README.md`（/ready schema 门语义）、`docs/security/README.md`（readiness 补 schema 门） |
| **明确不改** | `STEP1B_B0_GATE_REPORT.md` · `STEP1B_B1_3_GATE_REPORT.md` · `B1-4_PREP_GATE_REPORT.md` · `STEP1B_B1_2_PREP_REPORT.md`（含 `:95-98` cutover 流程记录）及全部阶段冻结文档的实质内容 |
| **待评估（非必需）** | `CORE_DOMAIN_MODEL.md:674`「STEP 2+ 议题」是否加交叉引用注记（与 D-PLAT-12.a 的命名相关） |
| **未纳入** | `ARCHITECTURE.md:3` / `README.md:3` / `pyproject.toml:3` / `config/settings.py:47` 的「Version 0.1.0 · PHASE-0」陈旧表述（`OD-9`/`OD-10` 未要求；如需修订须另行授权） |

> **[D-PLAT-07 注记 · 2026-09-23]** B-2′ 已于 2026-09-20 执行完毕（6 个文件 · +77/−4），本段末「受影响文档（B-2′ 范围，**本轮未执行**）」一行中的执行状态陈述已被取代。
> 关联：D-PLAT-07.c（本文档「受影响文档（B-2′ 范围，**本轮未执行**）」一行）
> 性质：状态更新。**不修改本文档既有结论。**

---

# D-PLAT-08 — `/ready` 迁移状态门

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 3，`/ready` 503 条）+ `OD-2` + `OD-3` + `OD-5` |
| **背景** | 现行 `/ready` 仅经 `infrastructure/database/health.py:25-31` 的 `check_database()` 执行 `SELECT 1` ⇒ **空库或未迁移的库同样返回 200 ready**（`apps/api/routes/health.py:34-49`）。Schema 状态完全不被检查。同时 0001–0011 的 Alembic 链与 legacy `schema_migrations` 并存，二者不对齐。 |
| **决策** | `/ready` **必须检查迁移状态**；Schema **缺失、落后或无法确认**时返回 **未就绪（HTTP 503）**。 |
| **依据** | Human Decision 项 3 · Contract §1（Alembic 唯一入口，故以 `alembic_version` 为判据） |
| **影响面** | 见 08.a / 08.b / 08.c |
| **已知后果（Human 已确认）** | **行为破坏性变更**：空库/unmigrated 库的 `/ready` 由 200 → **503**。部署须**先迁移后启动**。 |
| **待办** | `docs/operations/` 当前为空（仅 `.gitkeep`）⇒ 部署手册缺失会放大本条款的运维风险，建议另行登记 |

### D-PLAT-08.a — expected head 的来源与失败语义

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-2` |
| **决策** | ① expected head 使用**构建期注入的预期 revision**；② **运行时不扫描迁移目录**推导目标版本；③ 缺失或无效时**失败关闭**（fail closed）。 |
| **依据** | `OD-2` |
| **影响面** | 需新增配置项（键名**待确认**）· `.env.example` 需新增**空值**条目 · `tests/unit/test_config.py` 的 `SETTING_ENV_KEYS` 需同步 · `tests/security/test_no_secrets.py:47-64` 要求 `.env.example` 仅含空值且键名匹配 `[A-Z][A-Z0-9_]*` |
| **自洽性** | 因 expected head 为注入值，运行时可**只读 `alembic_version` 做 SQL 比对**，无需 import `alembic`、无需访问迁移目录 ✅ |
| **待确认** | ⚠ **构建期注入机制不存在**：实测 `Dockerfile` 的 `ARG` 计数 = 0、`docker-compose.yml` 无 `build.args`、`scripts/` 无 build-info 生成脚本。`OD-2` 已定**语义**，机制待实施轮设计并需 Human 确认。 |
| **待确认** | ⚠ 「缺失或无效」的具体分支语义（组件状态取 `error` 还是 `not_configured`）未定 |

### D-PLAT-08.b — 判定阈值

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-3` |
| **决策** | 当前数据库 revision **必须严格等于** expected head；**不采用最低版本阈值**。部署须先迁移，并保证滚动发布兼容性。 |
| **依据** | `OD-3` |
| **影响面** | 严格相等 ⇒ 滚动发布期间新旧版本并存时，旧版本会因 head 前移而判 not_ready。`OD-3` 已明确由**部署流程**承担该兼容性责任 |

### D-PLAT-08.c — 契约形态

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-5` |
| **决策** | ① 在**现有 readiness 组件机制**中增加 **critical migration component**；② **不新增顶层字段**；③ 迁移未就绪时 `/ready` 返回 **503**；④ `/health` **保持 liveness 语义**（零 I/O、不因依赖故障而失败）。 |
| **依据** | `OD-5` · `apps/api/routes/health.py:25-31`（`collect_components`）· `:34-49`（`build_readiness_report`）· `:52-67`（liveness 注释） |
| **影响面（已核验为"无破坏"）** | `tests/contract/test_health_contract.py:10` 的 `READY_FIELDS` **无需修改**（不新增顶层字段）；`:19-53` 与 `tests/unit/test_project_boot.py:51-83` 全部 **monkeypatch `collect_components`** ⇒ 不受新增组件影响。实测**全仓无任何测试在不 monkeypatch 的情况下命中 `/ready`**。 |
| **待办** | 需新增 4 条测试：空库 ⇒ 503 · head 落后 ⇒ 503 · 无 `alembic_version` 表 ⇒ 503 · head 一致 ⇒ 200 |

> **[D-PLAT-08 注记 · 2026-09-23]** 记录 Human 已批准的 `Q-6` / `Q-10` 落点（运维闭环），**不新增编号条目**。
> 关联：D-PLAT-08（本文档 `/ready` 迁移状态门本体）
> 性质：追加说明（获批决策的落点记录）。**不修改本文档既有结论。**
>
> - **`Q-6` APPROVED**：本 Slice 后续 **Implementation 必须交付** `docs/operations/DEPLOYMENT_AND_RECOVERY.md`，
>   契约链 = `backup → verify → migration → startup / rollout → /ready`，并必须写明 **F-1**：
>   严格相等 + 镜像绑定 schema revision ⇒ **应用回滚不得被理解为「只回滚镜像」**（须成对 DB downgrade 或前滚修复）。
> - **`Q-10` APPROVED**：本 Slice **不执行**任何真实生产备份 / 恢复 / migration / downgrade；
>   只交付**手册 + 命令契约 + 验收要求**，并把「**备份先于迁移**」设为实施/部署验收的**人工门**，
>   证据要求 = backup artifact + `pg_restore --list` + backup id + timestamp + target revision。

---

# D-PLAT-09 — 阶段顺序路线：P10 → P11 → P12 → P13 → Runtime

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 2，路线 A） |
| **背景** | `STEP1B_SCHEMA_DEPENDENCY.md:167-174` 已冻结 P06→P07→P08→P09→P10→P11→P12→P13 阶段链；`:172`「P11 必须在 seed 前全部就位」；`:193`「P00–P10 均无 seed 需求；P13 才有 seed」。 |
| **决策** | 采用路线 **A**：`P10 → P11 → P12 → P13 → Runtime`；**Runtime 延后**至四阶段完成并验收之后。 |
| **依据** | Human Decision 项 2 · `STEP1B_SCHEMA_DEPENDENCY.md:167-174` · `:193` |
| **影响面** | 无 schema 影响；决定后续工作顺序 |
| **禁止** | 不得据此改写 `STEP1B_SCHEMA_DEPENDENCY.md` 的既有阶段表（按 Charter §5，至多加注） |

---

# D-PLAT-10 — P11 纳入 G/H/I/J

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 4） |
| **背景** | `D-B14-02 = A`（RESOLVED BY FROZEN TEXT）已冻结：G/H/I/J 的**最早 phase = P09 后**，且原文写明「**实际按 P11 集中**」；`STEP1B_TRIGGER_INVENTORY.md:200-203` 的「最早 phase」列 = `P09 后`；`STEP1B_SCHEMA_DEPENDENCY.md:241` 规定「P11 的 trigger DDL 也必须按上表顺序排列」。 |
| **决策** | `P11` **纳入 G/H/I/J**，并在 **P11 设计阶段**冻结触发器清单、依赖与验收范围。 |
| **依据** | Human Decision 项 4 · `D-B14-02 = A` · **`D-P09-06 = A`（G/H/I/J 不在 P09 实施，保持「P09 后」）** · `P09_SCOPE.md:42`（G/H/I/J 列 OUT OF SCOPE）· `STEP1B_TRIGGER_INVENTORY.md:200-203` · `STEP1B_SCHEMA_DEPENDENCY.md:237-241` |
| **性质判定** | **与既有冻结决策逐字一致，非扩权**（`P11 ⊂ "P09 后"`）。消费本条款时不得视为对 `D-B14-02` 的修订。 |
| **影响面** | 结构上已解锁：G/H/I/J 的依赖对象 `agents`（P09）· `users` · `roles` · `resource_permissions` 均已存在 |
| **待办** | P11 设计阶段需冻结：① 四条 trigger 的**正式名称与时序** ② 依赖与 DDL 顺序（按 TRIGGER_INVENTORY 最早 phase 列） ③ 验收范围 ④ `L`（`tg_audit_immutable`）属 P10，须与 P11 明确分界 |
| **禁止** | 不得修改 `STEP1B_TRIGGER_INVENTORY.md` 的既有表格行（按 Charter §5，至多加注） |

---

# D-PLAT-11 — 首个正式可登录主体只经 P13 建立

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 5） |
| **背景** | `STEP1B_SEED_STRATEGY.md:14-27` 定义了 P13 的单一 10 步 bootstrap 顺序（含「首租户 + 首管理员用户」「首空间」「role_permissions 含 deny 行」）。`B1-4_DECISION_LOG.md:58` 已声明「ACL 能力要到 **P13 seed 之后**才真正可用 —— 这是冻结设计的既定顺序，非缺陷」。实测验证库 `uap_b1_test` 的种子现状：`roles = 1`（Platform Admin）· `platform_state = 1`（`uninitialized`）· **其余 29 张业务表全部 0 行**。 |
| **决策** | ① 首个正式可登录主体**只通过 P13 建立**；② **不引入第二套开发 bootstrap 身份路径**。 |
| **依据** | Human Decision 项 5 · `STEP1B_SEED_STRATEGY.md:14-27` · `STEP1B_SCHEMA_DEPENDENCY.md:193` · `B1-4_DECISION_LOG.md:58` |
| **影响面** | Runtime Slice 的演示主体来源**被唯一限定为 P13** ⇒ 任何"dev bootstrap"实现均属违反；同时意味着 `resource_permissions` 在 P13 之前**不可写入**（`acl_subject_types` 为空 ⇒ FK 不可满足） |
| **待办** | ① 若 P13 之外确需可登录主体，须**另行提请 Human 裁定**，不得自行增设 ② 可选守卫：拒绝新增第二套 bootstrap 入口（范围待定） |

---

# D-PLAT-12 — Runtime 阶段门

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | Human Decision（项 11）+ `OD-8` |
| **背景** | 仓库**不存在**任何 Runtime / P14 / STEP 2 的阶段定义文档（实测 `STEP 2` 全仓仅两处命中：`B1-6_MIGRATION_PLAN.md:51` 为迁移步骤编号的误命中；`CORE_DOMAIN_MODEL.md:674` 提及「那是 STEP 2+ 议题」，非阶段定义）。最近一次明确的 runtime 出界声明为 **`D-P09-07 = A`**（P09 = **SCHEMA ONLY**，不实施 agent runtime / API / worker / scheduler），见 `P09_SCOPE.md:19` 与 `:43-45`。 |
| **决策** | Runtime **必须在 P10、P11、P12、P13 完成并验收后**开始；Runtime **开工前必须先定义正式阶段文档、范围、依赖与验收门**。 |
| **依据** | Human Decision 项 11 · `STEP1B_SCHEMA_DEPENDENCY.md:167-174`（P10–P13 链） |
| **影响面** | Runtime 的起点被硬性绑定于 P13 验收通过 |

### D-PLAT-12.a — 路线名与暂定阶段编号

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN` |
| **来源** | `OD-8` |
| **决策** | ① 路线名称：**`STEP 2 — Runtime Slice`**；② 首阶段**暂定**为 **`P14_RUNTIME_SLICE`**；③ **正式编号及文档集合须在 PREP 门冻结**。 |
| **依据** | `OD-8` |
| **影响面** | `P14` 为**暂定**编号，当前全仓 0 命中（无冲突）；`RUNTIME_SLICE` / `Runtime Slice` 亦 0 命中 |
| **待确认** | ⚠ 「暂定」⇒ 不得在 PREP 门之前作为既成编号使用；不得据 `P14` 创建任何文件或引用 |
| **待确认** | ⚠ 是否需在 `STEP1B_SCHEMA_DEPENDENCY.md` 的 P06–P13 表中加注 `P14`：该表语义为**schema 阶段链**，而 Runtime Slice **不引入 schema** ⇒ 建议**不加注**，改由本载体与未来 P14 PREP 文档集合承载（待 Human 确认） |
| **待确认** | ⚠ `CORE_DOMAIN_MODEL.md:674`「STEP 2+ 议题」是否加交叉引用注记（与本节命名相关） |

---

# D-PLAT-13 — Governance / Gate Slice 定性、命名与 `D-PLAT-12` 关系

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 经 Human 正式裁定 · `Q-1` APPROVED） |
| **来源** | Human Decision（项 1、项 9）；Decision Resolution `Q-1` |
| **背景** | `D-PLAT-12` 规定 Runtime 必须在 P10–P13 完成并验收后开始。本阶段工作项为**迁移治理 + 层边界门控**（配置门、readiness schema 门、legacy 启动路径停用、依赖守卫），**不含任何业务运行时能力**。若表述为「首个 Runtime Slice」，将与 `D-PLAT-12` 冲突（先例：`D-B14-02` 判定"提前实施 = 静默扩权"）。 |
| **决策** | ① 本阶段归属为**独立 Governance / Gate Slice**，**不属于** Runtime Slice；② 阶段名称 = `Governance / Gate Slice`；③ `D-PLAT-12` 与 `D-PLAT-12.a` 的**原文与 `FROZEN` 状态保持不变**，本阶段**不受** `D-PLAT-12` 的 P10–P13 前置约束；④ Runtime 阶段名称与编号继续保持 **provisional**，其冻结仍属未来 PREP 门；⑤ **本阶段不是 `P14`** —— 本 Slice 不得创建任何 `P14` 文件、引用或阶段编号。 |
| **依据** | Human Decision 项 1 · 项 9 · `Q-1` · `D-PLAT-12` · `D-PLAT-12.a` · 先例 `D-B14-02` |
| **影响面** | 不引入 schema 阶段编号；不修改 `STEP1B_SCHEMA_DEPENDENCY.md` 的 P06–P13 表；不创建 `P14` 相关文件或引用；不改变 `D-PLAT-09` 的阶段顺序 |
| **待办** | ① 治理阶段的**正式编号**（如需）须 Human 另行裁定 ② 阶段文档集合 = `GOVERNANCE_GATE_SLICE_PREP_REPORT.md` + `GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md`（实施完成后由实施报告承接） |
| **禁止** | 不得将本阶段表述为 Runtime 或 `P14`；不得据本条款改写阶段表 |

---

# D-PLAT-14 — `/ready` 迁移状态门的配置键与失败语义（解析附录 C `C-1` / `C-3`）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `Q-1`） |
| **来源** | Human Decision（项 2、项 4、项 5）；`OD-2`；Decision Resolution `Q-1`；附录 C `C-1` / `C-3` |
| **背景** | `D-PLAT-08.a` 已冻结「构建期注入 + 缺失或无效失败关闭」，但**键名**与**失败分支语义**留白（附录 C `C-1` / `C-3`）。 |
| **决策** | ① 配置键名 = `EXPECTED_ALEMBIC_REVISION`（`str`，默认空串；**非 secret**；`redacted()` 快照中**不遮蔽**）；② 失败关闭语义 = **应用可启动**（Settings 不抛异常）+ **`/ready` 恒 503**；`/health` 保持**零 I/O liveness**；③ 不通过分支全集（**任一 ⇒ 503**）= `missing` / `invalid`（**短路，不访问 DB**）· DB `alembic_version` **表缺失** · **查询失败** · **0 行** · **NULL / 空串** · **多行** · 与 expected **严格不等**（**含领先**）；④ 组件状态统一取 `error`（**不**使用 `not_configured`），`critical = True`；⑤ revision 形态 `^\d{4}_[a-z0-9_]+$`，**单一来源** = `config/build_info.py`（生成器与探针共用）；⑥ `.env.example` 新增**空值**条目并说明本地开发/测试路径。 |
| **依据** | Human Decision 项 2 · `OD-2` · `D-PLAT-08.a` · `D-PLAT-08.b`（严格相等）· `Q-1` · 实测 `.env.example` 约束（`tests/security/test_no_secrets.py:47-64`） |
| **影响面** | `config/settings.py` · `.env.example` · `tests/unit/test_config.py` 的 `SETTING_ENV_KEYS` · 新增配置与探针测试 |
| **待办** | ① 探针 `detail` 包含 `source`（`build_artifact` / `environment` / `missing`）② **`Q-8`**：实施完成后 `docs/api/README.md` 与 `docs/security/README.md` **必须反映真实实施状态**（未实施不得写成已实施；已实施不得继续写成 `not implemented yet`），并保留 `D-PLAT-08` 指针 |
| **禁止** | 不得为"可启动"而在生产放宽严格相等；不得把「DB 版本高于期望」视为通过（`OD-3`） |

---

# D-PLAT-15 — 期望 revision 的注入形态：构建期只读工件（运行时不可覆盖）

> **版本沿革（强制）**：**v1 = `SUPERSEDED`（已被 v2 取代，不得作为现行方案引用）**；**v2 = 本条款唯一现行版本（`FROZEN`，2026-09-23）**。
> v1 的历史文本见 `GOVERNANCE_GATE_SLICE_PREP_REPORT.md` §5.3（仅作历史记录，不得据其引用）。

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（**v2 为唯一现行版本** · 2026-09-23 · `Q-1` + `Q-5` + `Q-9`） |
| **来源** | Human Decision（项 3）；`OD-2`；Decision Resolution `Q-5`（采用 A′）、`Q-9`（v1 → v2 正式修订）、`Q-4`（工件路径） |
| **背景** | 方案 A（`Docker ARG → image ENV`）**可被运行时覆盖**（`docker run -e` / compose `environment:`），违反「运行时不得通过环境变量覆盖」；方案 C（`Docker LABEL`）容器内进程不可读 ⇒ 必须以**构建期生成的只读工件**为运行时权威来源。**v2 进一步消除人工版本字面量**：v1 以 `ARG` 字面量为输入通道，仍存在「字面量 vs Alembic head」漂移路径；v2 改为**构建期从 Alembic 图推导**唯一 head。 |
| **决策（v2 全文）** | **权威链**：`migrations_alembic/versions/` → Alembic graph → **唯一 HEAD** → build-time generator → `config/_build_info.py` → image → `/ready` → DB `alembic_version`。<br>① **构建期**：生成器使用 `ScriptDirectory.from_config(Config("alembic.ini"))` 取 head；**必须恰好 1 个 head**；**必须**匹配 `^\d{4}_[a-z0-9_]+$`；满足后写入工件。<br>② `--revision` **仅**为可选 override：**若提供则必须等于推导值**，否则**构建失败**（fail-fast）。<br>③ **工件路径 = `config/_build_info.py`**（生成物、git-ignored、随镜像固化）；**稳定读取入口 = `config/build_info.py`**（**不**与 `APP_VERSION` 混淆）。<br>④ **解析顺序** = 工件 > 环境（**仅本地开发/测试**）> `missing`，并以 `source` 如实标注。<br>⑤ `docker-compose.yml` 的 `environment:` **不得**设置该键。 |
| **明确禁止** | ① Docker `ARG` 作为**权威** revision 输入；② compose revision **字面量**；③ ENV 覆盖工件；④ runtime 扫描 migration 目录；⑤ runtime `import alembic`；⑥ runtime 从 migration filename 猜测 head。 |
| **依据** | Human Decision 项 3 · `OD-2` · `Q-4` / `Q-5` / `Q-9` · 实测 `ScriptDirectory.from_config(Config('alembic.ini'))` **离线可用**（不连 DB、不执行 `env.py`）· `.dockerignore` 不存在 ⇒ 迁移文件必入 build context |
| **影响面** | `Dockerfile`（v2：**仅需生成 RUN**，**不需要** `ARG`）· `docker-compose.yml`（v2：**无需变更**）· `scripts/generate_build_info.py` · `config/build_info.py` · `.gitignore`（实测**无**覆盖规则 ⇒ 必须新增） |
| **待办** | ① 构建期自检 + 离线一致性测试（工件 == Alembic head）② 镜像回滚语义须写入 `docs/operations/DEPLOYMENT_AND_RECOVERY.md`（`Q-6`） |
| **禁止（衍生）** | 不得同时保留 v1 与 v2 作为现行方案；引用本条款时**必须**以 v2 为准 |

---

# D-PLAT-16 — readiness 迁移探针的独立短超时：2000 ms

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `Q-1` + `Q-3`） |
| **来源** | Human Decision（项 5）；Decision Resolution `Q-3` |
| **背景** | `DatabaseConfig.statement_timeout_ms` 默认 `None`（未设）⇒ readiness 探针在慢查询 / 锁等待下可能长时间阻塞，拖垮编排器探测周期。 |
| **决策** | ① 迁移状态探针使用**独立** server-side `statement_timeout` = **2000 ms**（`READINESS_STATEMENT_TIMEOUT_MS = 2000`）—— **候选值已被 Human 正式裁定为实施硬值**；② 实现复用既有 `DatabaseConfig.statement_timeout_ms` + `build_engine()` 的 `-c statement_timeout=<ms>` 通道，**不新增 infra 机制**；③ 连接超时沿用 `connect_timeout_seconds = 5`；④ 超时 ⇒ 组件 `error` ⇒ `/ready` **503**（不重试、不放行、不降级）；⑤ 探针引擎在 `finally` 中 `dispose()`，**不**进入进程级池；⑥ **不**修改全局默认超时（不影响 database 探针与业务查询）。 |
| **冲突策略** | 出现环境冲突 ⇒ **HARD STOP + 报告**。**禁止**：自行放宽、改为区间、修改全局默认值、实施阶段自行改变既有数值。 |
| **依据** | Human Decision 项 5 · `Q-3` · 实测 `infrastructure/database/config.py:30`（默认 `None`）· `infrastructure/database/session.py:24-28`（既有时超时通道） |
| **影响面** | `infrastructure/database/health.py`；测试须覆盖超时分支与「全局默认未变」断言 |
| **待办** | 复合时界须记录并纳入验收：单次探针最坏 ≈ 5 s（连接）+ 2 s（语句）；单次 `/ready` 最坏 ≈ 12 s（两个 critical 探针） |

---

# D-PLAT-17 — Guard 门级划分与实施责任

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `Q-1` + `Q-2` + `Q-7`） |
| **来源** | Human Decision（项 6）；Decision Resolution `Q-2`、`Q-7` |
| **背景** | 既有设计已给出 `G-1`…`G-8`，但未定「硬门 / advisory」；`DEPENDENCY_RULES.md:61-64` 规定「规则必须与测试同批」。 |
| **决策** | ① **Hard（硬门：未通过即不得验收）** = `G-1` `core ↛ SQLAlchemy/psycopg` · `G-2` `core ↛ services` · `G-3` `agent ↛ services` · `G-4` `domains ↛ {services, infrastructure}` · `G-6` readiness `migration` 组件 `critical=True` · `G-7` 启动不调用 legacy runner（且 `Settings` 不含该开关）；② **Advisory**（实施并运行，违规由 Human 裁定豁免，须记录局限）= `G-5` `apps ↛ SQLAlchemy/psycopg`（**代理判据**，与 `D-PLAT-04.a` 的"业务持久化"语义**不等价**）；③ **Deferred**（延后，不属本 Slice）= `G-8` bootstrap 唯一性（判定对象当前不存在）；④ **Cancelled**（取消）= `G-9` compose 与 `alembic heads` 漂移检测 —— 采用 `D-PLAT-15 v2` 后**不再存在**人工 revision 字面量，漂移路径被结构性消除；⑤ 判据统一用 **AST**（复用 `_imported_top_levels()`），**禁止**字符串 / 正则匹配；⑥ 测试位置：`G-1`…`G-5`、`G-7` → `tests/architecture/`；`G-6` → `tests/contract/`；⑦ **`Q-7`**：本 Slice **不建立 CI**（不得创建 `.github/workflows/`），硬门由**人工执行**并**留存证据**（命令 + 退出码 + 摘要 + 每项硬门的**负向样例**证明）；**advisory 结果不得作为硬门通过的依据**；⑧ 落地后同步更新 `DEPENDENCY_RULES.md §7` 的 Enforcement status。 |
| **失败停止条件** | 任一硬门红 · 负向样例无法使守卫失败（守卫无效）· 回归下降 · `alembic heads` 非单一 · 变更文件越界 · 无法产出证据 ⇒ **HALT + 报告 BLOCKED** |
| **依据** | Human Decision 项 6 · `Q-2` · `Q-7` · `DEPENDENCY_RULES.md:61-64` · `D-PLAT-04.a`（代理局限）· `D-PLAT-15 v2`（G-9 取消原因） |
| **影响面** | `tests/architecture/` · `tests/contract/` · `DEPENDENCY_RULES.md §7` |
| **禁止** | 不得新增 `services ↛ domains`（`D-PLAT-03.a`）或 `apps ↛ infrastructure`（`D-PLAT-04.a`）守卫 |

---

# 附录 A — `OD-1`…`OD-10` 落点索引

| OD | 内容摘要 | 落点 | 是否完整落位 |
|---|---|---|---|
| `OD-1` | 载体 = `PLATFORM_DECISION_LOG.md`；命名空间 `D-PLAT-NN`（首轮 `01..12`；`13..17` 见 2026-09-23 Decision Resolution）；阶段历史编号不变 | **Charter §1–§3**（不占 D-PLAT 编号） | ✅ |
| `OD-2` | expected head 构建期注入；运行时不扫描迁移目录；缺失/无效失败关闭 | **D-PLAT-08.a** | ✅ |
| `OD-3` | 严格等于 expected head；不采用最低版本阈值 | **D-PLAT-08.b** | ✅ |
| `OD-4` | 删除 `ENABLE_MIGRATIONS_ON_STARTUP` 与启动分支；保留 legacy runner 本体及测试 | **D-PLAT-07.a** | ✅ |
| `OD-5` | 现有 readiness 组件机制加 critical migration component；不新增顶层字段；503；/health 保持 liveness | **D-PLAT-08.c** | ✅ |
| `OD-6` | apps 可依赖 infrastructure 做装配/生命周期/健康检查；禁止用 SQLAlchemy/psycopg 做业务持久化 | **D-PLAT-04.a** | ✅ |
| `OD-7` | domains 不依赖 services/infrastructure；services 可依赖 domains 公开稳定契约；契约细节留待 Runtime PREP | **D-PLAT-06.a + D-PLAT-03.a**（**双重落点**） | ✅ |
| `OD-8` | 路线名 `STEP 2 — Runtime Slice`；首阶段暂定 `P14_RUNTIME_SLICE`；PREP 门冻结 | **D-PLAT-12.a** | ✅ |
| `OD-9` | `ARCHITECTURE.md` 保留简洁规则并指向 Migration Contract；Contract 为权威 | **D-PLAT-07.b** | ✅ |
| `OD-10` | 最小修订现行迁移指引；不重写历史阶段报告；冻结文档仅按规则加注 | **D-PLAT-07.c** + **Charter §5** | ✅ |

**覆盖统计**：10 / 10 项全部有明确落点，无遗漏。

---

# 附录 B — 状态总表

| ID | 主题 | 状态 |
|---|---|---|
| D-PLAT-01 | 服务层落点 = 顶层 `services/` | `FROZEN` |
| D-PLAT-02 | `core` 契约定位 | `FROZEN` |
| D-PLAT-03 | `services` 职责（含 03.a） | `FROZEN` |
| D-PLAT-04 | `apps` 边界（含 04.a） | `FROZEN` |
| D-PLAT-05 | `agent` 不依赖 `services` 实现 | `FROZEN` |
| D-PLAT-06 | `domains` 边界（含 06.a） | `FROZEN` |
| D-PLAT-07 | Legacy 启动迁移停用 + Alembic 唯一入口（含 07.a–c） | `FROZEN` |
| D-PLAT-08 | `/ready` 迁移状态门（含 08.a–c） | `FROZEN` |
| D-PLAT-09 | 阶段顺序路线 A | `FROZEN` |
| D-PLAT-10 | P11 纳入 G/H/I/J | `FROZEN` |
| D-PLAT-11 | 首个主体只经 P13 | `FROZEN` |
| D-PLAT-12 | Runtime 阶段门（含 12.a） | `FROZEN` |
| D-PLAT-13 | Governance / Gate Slice 定性、命名与 `D-PLAT-12` 关系 | `FROZEN` |
| D-PLAT-14 | `/ready` 迁移状态门的配置键与失败语义（解析 `C-1` / `C-3`） | `FROZEN` |
| D-PLAT-15 | 期望 revision 注入形态：构建期只读工件（**v2 现行**；v1 `SUPERSEDED`） | `FROZEN` |
| D-PLAT-16 | readiness 迁移探针独立短超时 = **2000 ms** | `FROZEN` |
| D-PLAT-17 | Guard 门级划分（Hard / Advisory / Deferred / Cancelled） | `FROZEN` |

```
FROZEN 条目数 = 17   （`01`…`12` 于 2026-09-20 经 Human 明确确认置入；`13`…`17` 于 2026-09-23 经 Decision Resolution 确认置入）
```

---

# 附录 C — 待确认事项登记（不得默认为已定）

| # | 项 | 关联 | 性质 |
|---|---|---|---|
| C-1 | 新配置项的**键名**（expected revision） | D-PLAT-08.a | ✅ **RESOLVED（2026-09-23）** = `EXPECTED_ALEMBIC_REVISION`，见 **D-PLAT-14** |
| C-2 | **构建期注入机制**（原：`Dockerfile` 无 `ARG`、compose 无 `build.args`、无 build-info 脚本） | D-PLAT-08.a | ✅ **RESOLVED（2026-09-23）** = 构建期推导唯一 head → 只读工件 `config/_build_info.py`（见 **D-PLAT-15 v2**）；**不是** `ARG` 字面量 |
| C-3 | 「缺失或无效」的分支语义（`error` vs `not_configured`） | D-PLAT-08.a | ✅ **RESOLVED（2026-09-23）** = 统一 `error` + `critical=True` ⇒ `/ready` 503；`/health` 保持 liveness，见 **D-PLAT-14** |
| C-4 | 守卫的具体断言形式（扩充既有 or 新增独立测试） | D-PLAT-02/05 | ✅ **RESOLVED（2026-09-23，实施轮以实际测试证据为准）**：`G-1` 新增独立测试 `test_core_does_not_import_persistence` · `G-2`/`G-3` **扩充既有** forbidden 集 · `G-4`/`G-5`/`G-7` 新增独立测试 · `G-6` 位于 `tests/contract/`；判据统一 AST（见 `tests/architecture/test_dependency_rules.py` 与 `D-PLAT-17` ⑤⑥） |
| C-5 | `services/` 内部结构与模块粒度 | D-PLAT-01/03 | 留待 Runtime PREP |
| C-6 | 「domains 公开稳定契约」的载体与组织方式 | D-PLAT-03.a/06.a | `OD-7` 明确留待 Runtime PREP |
| C-7 | `apps ↛ sqlalchemy` 守卫为**代理判据**的语义局限 | D-PLAT-04.a | 已声明局限，需在实施轮文档标注 |
| C-8 | `P14_RUNTIME_SLICE` 是否需在 `STEP1B_SCHEMA_DEPENDENCY.md` 加注 | D-PLAT-12.a | 建议不加注，待确认 |
| C-9 | `CORE_DOMAIN_MODEL.md:674` 是否加交叉引用注记 | D-PLAT-07.c/12.a | 待评估 |
| C-10 | `docs/operations/` 部署手册缺失（先迁移后启动的运维前置） | D-PLAT-08 | 建议另行登记 |
| C-11 | 可选守卫：拒绝新增第二套 bootstrap 入口 | D-PLAT-11 | 范围待定 |

---

# 附录 D — 本载体明确**不**产生的约束

- ❌ **不**新增 `services ↛ domains` 守卫（与 `D-PLAT-03.a` 直接冲突）
- ❌ **不**新增 `apps ↛ infrastructure` 守卫（与 `D-PLAT-04.a` 直接冲突）
- ❌ **不**修改任何既有阶段历史编号（见 Charter §3）
- ❌ **不**重写任何历史阶段报告（见 D-PLAT-07.c）
- ❌ **不**授权任何代码 / 配置 / 测试 / 迁移 / 数据库 / 包结构变更（见 Charter §6）
- ❌ **不**在未经 Human 明确确认的情况下将任何条目标为 `FROZEN`（本载体 **17** 项条目的 `FROZEN` 状态：`01`…`12` 于 2026-09-20、`13`…`17` 于 2026-09-23 经 Human 明确确认置入）
- ✅ **本载体不产生实施授权**：`D-PLAT-13`…`D-PLAT-17` 的落盘**不等于**任何代码 / 配置 / 测试 / 迁移 / 部署授权的开启（见 Charter §6）

---

---

# Authorization Canonical Model — `D-AUTH-01` … `D-AUTH-25`

> **来源**：`STAGE 2 — AUTHORIZATION / ACL / POLICY` 的 PREP（`AUTHORIZATION_PREP_REPORT.md`）与
> Decision Resolution（`AUTHORIZATION_DECISION_RESOLUTION.md`）；OQ 编号 `OQ-A01`…`OQ-A22`。
> **Human 于 2026-09-23 逐项明确裁定**：**19 项 `FROZEN` + 3 项 `DEFERRED`**。
> **追加（2026-09-23）**：**`D-AUTH-23`** 来自 **`GAP-11`**（Implementation Gap，**非** OQ），单条 Human Decision **A — Legacy Opaque** ⇒ `FROZEN`。
> **追加（2026-09-24）**：**`D-AUTH-24`** = `D-B14-08` 由 `D-AUTH-05` **取代**（保留 `SC-1b`）；
> **`D-AUTH-25`** = **Action canonical 形式 = 小写**。二者均**非** OQ，逐条正文见本区段末尾。
> ⇒ **`D-AUTH` 条目共 25 条**：**`FROZEN` 22 + `DEFERRED` 3 + `SUPERSEDED` 0**（`OQ` 口径仍为 **19 + 3 = 22**）；
> **平台级 supersession = 1**（`D-B14-08`，登记于 `D-AUTH-24`）。
> **本组条目不产生任何实施授权**（Charter §6）；`D-PLAT-01`…`D-PLAT-17` 与全部既有冻结决策**保持原状**，
> 本组**不构成**对任何既有决策的 silent replacement（`R2-D-14` / `R2-D-15` / `R4` / ACL 主体白名单 / P09 均被显式继承）。
> `D-B14-08` 的取代是**显式、经 Human Decision 并留档**的 supersession，**非** silent replacement。

## 总表

| ID | OQ | 主题 | 状态 | 实施阶段 |
|---|---|---|---|---|
| `D-AUTH-01` | A01 | 组合模式 = RBAC + ACL + Policy | **FROZEN** | Authorization Implementation |
| `D-AUTH-02` | A02 | Agent = 独立授权主体 | **FROZEN** | Authorization Implementation |
| `D-AUTH-03` | A03 | 显式 Delegation Scope / Lifecycle | **DEFERRED** | Agent Runtime |
| `D-AUTH-04` | A04 | Resource Canonical Model | **FROZEN** | Authorization Implementation |
| `D-AUTH-05` | A05 | Canonical Action Vocabulary（12 项） | **FROZEN** | Authorization Implementation |
| `D-AUTH-06` | A06 | Scope Model（PLATFORM/TENANT/SPACE） | **FROZEN** | Authorization Implementation |
| `D-AUTH-07` | A07 | `DENY > ALLOW` | **FROZEN** | Authorization Implementation |
| `D-AUTH-08` | A08 | Inheritance = Explicit and Downward | **FROZEN** | Authorization Implementation |
| `D-AUTH-09` | A09 | Tool Authorization Boundary | **FROZEN** | Tool Runtime / Authorization Implementation |
| `D-AUTH-10` | A10 | 四档 Risk Classification | **FROZEN** | Authorization Implementation |
| `D-AUTH-11` | A11 | Approval = 静态 OR 策略 | **FROZEN** | Tool Runtime（persistence） |
| `D-AUTH-12` | A12 | FAIL CLOSED / DEFAULT DENY | **FROZEN** | Authorization Implementation |
| `D-AUTH-13` | A13 | Authorization Cache | **DEFERRED** | Tool Runtime |
| `D-AUTH-14` | A14 | Decision States（ALLOW/DENY/REQUIRES_APPROVAL） | **FROZEN** | Authorization Implementation |
| `D-AUTH-15` | A15 | Authorization Audit 设计边界 | **FROZEN** | Authorization Decision Audit（persistence → P10） |
| `D-AUTH-16` | A16 | Service Placement（core/application/infrastructure） | **FROZEN** | Authorization Implementation |
| `D-AUTH-17` | A17 | Schema Impact（本冻结不产生 schema 变更） | **FROZEN** | Authorization Implementation |
| `D-AUTH-18` | A18 | Canonical Subject Vocabulary | **FROZEN** | Authorization Implementation |
| `D-AUTH-19` | A19 | Agent Version Semantics（单调整数 revision） | **FROZEN** | Authorization Implementation |
| `D-AUTH-20` | A20 | ACL Uniqueness Semantics | **FROZEN** | Authorization Implementation |
| `D-AUTH-21` | A21 | Memory / Workflow Authorization | **DEFERRED** | Agent Runtime |
| `D-AUTH-22` | A22 | Audit / Event ID = UUIDv7 | **FROZEN** | P10（persistence） |
| `D-AUTH-23` | **—**（`GAP-11`） | `agent_permissions.resource_scope` = **Legacy Opaque**（`ND-A` = 不追加 `<> ''`） | **FROZEN** | Authorization Implementation（契约 / 测试层，**无** schema 动作） |
| `D-AUTH-24` | **—**（`D-B14-08` 冲突） | `D-B14-08` → **`SUPERSEDED`** by `D-AUTH-05`；`SC-1b` **保留** | **FROZEN** | Authorization Implementation（已实施于 `0012`） |
| `D-AUTH-25` | **—**（`D-B14-08` 冲突） | Action **canonical 存储形 = 小写**；归一 = NFKC → strip → casefold | **FROZEN** | Authorization Implementation（已实施） |

---

# D-AUTH-01 — Authorization 组合模式：RBAC + ACL + Policy

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A01`） |
| **决策** | 采用 **RBAC + ACL + Policy** 三层。职责冻结：`RBAC` = Role-based baseline grant · `ACL` = Resource-specific grant · `Policy` = Contextual / conditional decision。 |
| **理由 / 依据** | `roles`/`role_permissions`（0005）与 `resources`/`acl_subject_types`/`resource_permissions`（0007）**已全部落库并冻结**，废弃任一层均为破坏性变更；`role_permissions.conditions` 已存在（`R2-D-15` 定为 storage-only）；`core/permission` 与 `core/policy` 双契约已在位。 |
| **影响范围** | `core/permission`（RBAC+ACL 合并）· `core/policy`（条件/风险判定）· `services/authorization/` |
| **实施阶段** | Authorization Implementation（`services/` 包须先建立，`D-PLAT-01`） |
| **禁止** | 三层**不得重复实现同一授权逻辑**；`conditions` 归属**唯一**（归 `core/policy`）；不得新增第四套授权机制 |

---

# D-AUTH-02 — Agent = 独立授权主体

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A02`） |
| **决策** | **Agent = Independent Authorization Subject**。Agent 可拥有自身 Permission、自身 Policy applicability、自身 Tool authorization、自身 lifecycle/status。**Agent 不等同于创建它的 User。** |
| **理由 / 依据** | `acl_subject_types` 硬白名单**已允许 `agent`**（`ck_acl_subject_types_whitelist` + `tg_acl_subject_types_protect`，0007）；`agent_permissions`（`effect`/`resource_scope`/`conditions`）与 `agents.max_risk_level` 已落库（0011）。 |
| **影响范围** | `core/permission.Subject`（须可表达 agent 主体）· `agents`/`agent_permissions`（沿用，不新建） |
| **实施阶段** | Authorization Implementation |
| **禁止** | 不得把 Agent 的授权等同于其 `owner_id` 指向的 User；不得移除 `acl_subject_types` 的 `agent` 白名单项 |

---

# D-AUTH-03 — 显式 Delegation Scope / Lifecycle ｛`DEFERRED`｝

| 字段 | 内容 |
|---|---|
| **状态** | `DEFERRED`（2026-09-23 · `OQ-A03`） |
| **已冻结的基础语义** | ① Agent = Independent Subject；② User = Actor / Delegator Context（适用时）；③ 执行记录**必须能区分** `Agent` / `Actor` / `Delegator`；④ **禁止** `Agent permission = User permission automatically`；⑤ **禁止** `Agent authority > effective authority of delegating user`。 |
| **Owner Phase** | **Agent Runtime** |
| **理由** | `tool_executions` 已同时具备 `agent_id` 与 `actor_id`（0011），基础语义可立即冻结；而 `grant`/`revoke`/`expiry`/`delegation-specific scope` 需 delegation 载体（**当前不存在**），且与 Agent Runtime 的生命周期设计耦合。 |
| **Exit Condition** | Agent Runtime PREP 完成，且 delegation 载体形态（新表/新列）经 Human 单独授权后，冻结完整 delegation contract。 |
| **影响范围** | `core/policy.PolicyContext`（现仅单 `actor_id`，需扩展双主体）· 未来 delegation 载体 |
| **禁止** | 在 Exit Condition 满足前**不得**创建 delegation 表/列；**不得**使 Agent 权限超出委派 User 的有效授权 |

---

# D-AUTH-04 — Resource Canonical Model

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A04`） |
| **决策** | Authorization Resource 的 canonical 概念**至少包括**：`resource_type` · `resource_id` · `tenant` · `space` · `classification` · `owner` · `lifecycle`。**当前不增加** `parent_id` / `resource_relations`（除非未来出现明确业务需求）。Owner 当前**保持 `User`** 为 canonical owner 类型。 |
| **理由 / 依据** | `resources` 表已具备全部 7 项（`resource_type` 正则 · `tenant_id` NN · `space_id` · `classification` 四档 · `owner_id`→users · `status`/`archived_at`/`deleted_at`），0011 实测；`resource_relations` 在 0011 **不存在**。 |
| **影响范围** | `core/resource.ResourceRef`（沿用）· `resources`（**不新增列**） |
| **实施阶段** | Authorization Implementation |
| **禁止** | **不因 Agent 成为 Subject 就自动允许 Agent 成为 Resource Owner**；不得创建 `resources.parent_id` / `resource_relations` |

---

# D-AUTH-05 — Canonical Action Vocabulary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A05`） |
| **决策** | 平台基础 Action vocabulary = `READ` `LIST` `CREATE` `UPDATE` `DELETE` `EXECUTE` `APPROVE` `REJECT` `PUBLISH` `EXPORT` `SHARE` `ADMIN`。**Core Action vocabulary = platform canonical**；Module 可提出扩展 Action，但必须 **Registered / Discoverable / Auditable / Policy-compatible**；**不得**通过任意自由字符串绕过统一授权语义。后续实现阶段**应考虑**对 canonical action 集合增加数据层约束。 |
| **理由 / 依据** | 实测三处 action 均为自由 text 且无 CHECK（`permissions.action` · `resource_permissions.action` · 契约 `Action.name`），构成"拼写变体绕过授权"面。 |
| **影响范围** | `permissions.action` · `resource_permissions.action`（未来 CHECK，见 `D-AUTH-17`）· `core/permission.Action` |
| **实施阶段** | Authorization Implementation（数据层约束须在 Implementation Contract 中细化） |
| **禁止** | Module 不得自由产生不可审计的 action 字符串；不得建立第二套 Action 词表 |

---

# D-AUTH-06 — Scope Model

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A06`） |
| **决策** | canonical grant scopes = `PLATFORM` → `TENANT` → `SPACE`（**层级**）。**暂不把 `RESOURCE` / `SELF` 作为独立的 canonical grant scope 存储类型**；二者在需要时作为 **Resource / Context predicate** 表达。 |
| **理由 / 依据** | `roles.scope CHECK IN (PLATFORM,TENANT,SPACE)` + `tg_roles_scope_shape` + 3 个部分唯一索引（`uq_roles_platform`/`uq_roles_tenant`/`uq_roles_space`）已在 DB 强制，0011 实测。 |
| **影响范围** | `roles.scope`（**沿用，不扩枚举**）· `core/resource.ResourceScope` · 未来判定谓词 |
| **实施阶段** | Authorization Implementation |
| **禁止** | 不得新增第 4/第 5 个 canonical grant scope；不得把 `SELF` 误作 Scope 存储（它是 Context predicate） |

---

# D-AUTH-07 — `DENY > ALLOW`

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A07`） |
| **决策** | **正式继承既有冻结 `R2-D-14`：`DENY > ALLOW`**。授权结果必须 **Deterministic** · **Order-independent** · **Auditable**；**不得**因 evaluation order 不同而产生不同结果。 |
| **理由 / 依据** | `R2-D-14`（FROZEN SECURITY INVARIANT，`STEP1B_ACL_STRATEGY.md §9`）· `ER_MODEL.md:221`（ACL deny 优先于 RBAC 继承的 allow）· `core/policy.combine()`「Any denial wins」· 平台 default-deny 方向。 |
| **影响范围** | `core/permission`（合并算法）· `core/policy`（`combine`） |
| **实施阶段** | Authorization Implementation |
| **禁止** | **本条目不是新决策**，而是**确认继承**；不得解释为对 `R2-D-14` 的修改。如需变更须走 **New Supersession Decision** |

---

# D-AUTH-08 — Inheritance = Explicit and Downward

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A08`） |
| **决策** | `Inheritance = Explicit and Downward`。允许 `TENANT → SPACE → Resource Context`；**不允许**通过不存在的 Resource Parent Tree 自动继承。特别规定 **No implicit resource-parent inheritance**。`parent_id` / `resource_relations` 均**保持未采用**。**Explicit Deny 必须参与最终授权计算。** |
| **理由 / 依据** | `roles` 三层层级已由 DB 强制；`resource_permissions.inherited` 列存在但**无 parent 资源**（`resources` 无 parent 列，`resource_relations` 不存在）。 |
| **影响范围** | `core/permission`（继承合并）· `core/membership` · `resource_permissions.inherited`（语义：**非** parent 继承） |
| **实施阶段** | Authorization Implementation |
| **禁止** | 不得实现隐式资源父级继承；不得引入 `parent_id` / `resource_relations` |

---

# D-AUTH-09 — Tool Authorization Boundary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A09`） |
| **决策** | **Tool 是唯一受控执行出口**。链路冻结：`Agent → Tool Authorization → Resource Authorization → Policy → Execution`。**Tool Permission 与 Resource Permission 不合并成同一个概念**。未来 Tool Authorization **必须能结构化表达** `Tool + Action/Capability + Scope + Resource Context`。具体 schema structure 属后续 **Implementation Contract**。 |
| **理由 / 依据** | `agent/tools/interfaces.py` docstring「A tool is the only path from an agent to a service」；`tools`/`tool_versions`/`tool_permissions` 已落库（0008）；`tool_permissions` **当前无** resource/action/scope 列（需结构化，见 `D-AUTH-17`）。 |
| **影响范围** | `agent/tools`（执行前须携带授权决策）· `tool_permissions`（未来结构化增列）· `services/authorization` |
| **实施阶段** | Tool Runtime / Authorization Implementation |
| **禁止** | **不得让 Tool 自己绕过 Authorization Service**；不得让 Tool 自实现授权逻辑 |

---

# D-AUTH-10 — 四档 Risk Classification

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A10`） |
| **决策** | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` 为平台 **canonical Risk Classification**。数值 `0.0 ~ 1.0` **不得**成为外部 canonical authorization vocabulary；如未来内部需要风险评分，可作为 **internal signal**。**`Risk ≠ Permission`** 且 **`Risk ≠ Authorization Decision`**。 |
| **理由 / 依据** | DB 三处四档 CHECK 已落库并冻结：`ck_tools_risk_level` · `ck_agents_max_risk_level` · `tool_executions.risk_level`（0011 实测）；契约 `core/policy.RiskPolicy.score() -> float[0,1]` 为唯一异形方。 |
| **影响范围** | `core/policy.RiskPolicy`（`score` 降为可选内部信号）· `tools`/`agents`/`tool_executions`（**沿用**） |
| **实施阶段** | Authorization Implementation |
| **禁止** | 不得把数值评分作为对外的授权词表；不得把 Risk 与 Permission/Decision 混为一谈 |

---

# D-AUTH-11 — Approval = 静态 OR 策略

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A11`） |
| **决策** | `approval_required = Static Tool Requirement OR Dynamic Policy Requirement`（**逻辑或**；任一成立即要求人工审批）。**审批不是 Permission；审批结果不等同于 `ALLOW`。** 审批 persistence carrier：**`DEFERRED TO TOOL RUNTIME / P10 dependency`**（**不视为新 OQ、不另增编号**）。 |
| **理由 / 依据** | `tools.approval_required boolean NOT NULL` 已落库（0008，静态侧在位）；`core/permission.Decision` 与 `tool_executions.status` 均无"待审批"态（三处缺承载）。 |
| **影响范围** | `tools.approval_required`（沿用为静态下限）· `core/policy`（动态侧）· 未来审批载体（**本轮不创建**） |
| **实施阶段** | Tool Runtime（persistence carrier） |
| **禁止** | 本轮**不得创建** `approval_requests` 等数据库对象；**不得**把审批结果直接视为 `ALLOW` |

---

# D-AUTH-12 — FAIL CLOSED / DEFAULT DENY

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A12`） |
| **决策** | 统一 **FAIL CLOSED / DEFAULT DENY**。以下情况**不得自动 ALLOW**，最终行为一律 **`DENY`**：`Authorization Service unavailable` · `Policy lookup failure` · `Permission lookup failure` · `Unknown subject` · `Unknown resource` · `Unknown action` · `Expired grant` · `Revoked grant`。 |
| **理由 / 依据** | 多重既有冻结先例：`R3-D-07`/`R4`（平台级无 effective 权限 ⇒ DENY）· `R5`（user inactive ⇒ 永久 DENY）· `core/permission.DENY`/`default_decision()` · `combine()` any-deny-wins · `core/permission` docstring。 |
| **影响范围** | `core/permission` · `core/policy` · `services/authorization`（异常处理路径） |
| **实施阶段** | Authorization Implementation |
| **禁止** | 任何失败分支**不得**降级为 ALLOW；不得引入"只读放行"式降级 |

---

# D-AUTH-13 — Authorization Cache ｛`DEFERRED`｝

| 字段 | 内容 |
|---|---|
| **状态** | `DEFERRED`（2026-09-23 · `OQ-A13`） |
| **当前冻结事实** | **`No Authorization Cache`**；**不得为性能提前实现**。 |
| **Owner Phase** | **Tool Runtime**（需结合真实 Runtime traffic model 再冻结具体方案） |
| **未来约束（已冻结）** | 若允许研究 bounded cache，**必须**满足：`No Fail Open` · `Bounded TTL` · `Explicit Revocation Invalidation` · `No stale ALLOW after security-critical revoke`。 |
| **Exit Condition** | Tool Runtime PREP 提供真实流量模型与失效路径分析，并经 Human 授权后冻结具体 cache 方案。 |
| **影响范围** | `infrastructure/cache` · `services/authorization` |
| **禁止** | 在 Exit Condition 满足前**不得**实现任何授权缓存；**绝对禁止 fail-open** |

---

# D-AUTH-14 — Decision States

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A14`） |
| **决策** | Authorization Decision 的 canonical states = **`ALLOW`** / **`DENY`** / **`REQUIRES_APPROVAL`**。其中 **`REQUIRES_APPROVAL` 不是最终 Permission Grant**；它表示 `Policy / Risk ⇒ Action cannot execute yet`，**必须**经过批准流程后才能进入实际执行。 |
| **理由 / 依据** | §22 要求三值结果；现 `Decision(allowed: bool)` 无三值承载（三处契约均缺），需扩展为 `effect` 枚举并补齐 `subject`/`delegator`/`action`/`resource`/`scope`/`context`/`reason`/`policy_version`。 |
| **影响范围** | `core/permission.Decision` · `agent/runtime.AgentRunResult` · 调用方（Agent/Tool/Module） |
| **实施阶段** | Authorization Implementation |
| **禁止** | **任何调用方不得把 `REQUIRES_APPROVAL` 当作可继续执行** |

---

# D-AUTH-15 — Authorization Audit 设计边界

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A15`） |
| **决策** | **`Authorization Decision Audit ≠ Tool Execution Audit`**。Authorization Audit **至少**需能表达：`subject` · `delegator / actor context` · `tenant` · `space` · `resource` · `action` · `decision` · `reason` · `policy` · `risk` · `approval` · `timestamp`。**当前 Audit Persistence：`DEFERRED TO P10`。** |
| **理由 / 依据** | `core/audit.AuditEvent` 现缺 `subject`/`delegator`/`decision`/`reason`/`policy`/`risk`/`approval` 七类字段；`events` 与 `audit_logs` **在 0011 均不存在**（属 P10）。 |
| **影响范围** | `core/audit.AuditEvent`（契约扩字段）· 未来 `audit_logs`（P10） |
| **实施阶段** | 设计边界：Authorization Implementation（契约）；persistence：**P10** |
| **禁止** | **本轮不得创建 `events` / `audit_logs`**；不得把授权审计与工具执行审计合并为同一载体 |

---

# D-AUTH-16 — Service Placement

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A16`） |
| **决策** | 分层冻结：**`Core`** = Authorization contracts / value objects / **pure rules**；**`Application / Domain service`** = Authorization decision orchestration；**`Infrastructure`** = Persistence / adapter / external integration。 |
| **理由 / 依据** | `D-PLAT-02`（core = 契约与基础抽象，不承载持久化）· `D-PLAT-03`（services = 唯一业务持久化承载层）· `D-PLAT-05`（agent 经 Policy/Tool 契约进入）· 硬门 `G-1`/`G-2`/`G-3`。 |
| **影响范围** | `core/{permission,policy,resource,audit}`（契约）· `services/authorization/`（实现，包**尚不存在**，须先建立）· `infrastructure`（适配） |
| **实施阶段** | Authorization Implementation |
| **禁止** | **禁止** `Core → Database` · `Core → Services` · `Agent → Database` · `Agent → Infrastructure`。Agent 只能经 `Authorization Contract + Policy Contract + Tool Contract` 访问受控能力 |

---

# D-AUTH-17 — Schema Impact（本冻结不产生 schema 变更）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A17`） |
| **决策** | 本次 Decision Freeze **不产生任何 schema modification**。未来 Authorization Implementation **允许研究**的必要方向：① **Canonical Action enforcement**；② **Structured Tool Permission representation**。当前**明确不采用**：`resources.parent_id` · `resource_relations` · **ACL unique-key redesign**。 |
| **理由 / 依据** | `D-AUTH-04`/`D-AUTH-08` 判定不引入 parent；`D-AUTH-20` 判定保持 ACL 唯一键；`D-AUTH-05`/`D-AUTH-09` 指出 action 约束与 tool 结构化是唯二必要方向。 |
| **影响范围** | `migrations_alembic/`（**本轮 0**）· 未来 Implementation Contract |
| **实施阶段** | Authorization Implementation（须经独立 Implementation Contract + Authorization） |
| **禁止** | **不修改 `0010` / `0011`**；**不得创建 `0012`**；本轮 **New Migration = 0**、`DDL`/`DML` 均未授权 |

---

# D-AUTH-18 — Canonical Subject Vocabulary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A18`） |
| **决策** | Canonical **Authorization Subject Types** = **`USER`** / **`ROLE`** / **`AGENT`**。并明确 **`Authorization Subject Type ≠ Identity Kind ≠ Identity Provider`**：`identities.provider` 属 **Identity / Authentication Provider** 语义；`acl_subject_types` 属 **Authorization Subject** 语义。三套历史词汇**不得继续作为同义词使用**。 |
| **理由 / 依据** | `acl_subject_types` 硬白名单 `CHECK (key IN ('user','role','agent'))`（0007，0011 实测）；`core/identity.IDENTITY_KINDS = (user, service, device_subject)`；`identities.provider CHECK IN (local,oidc,saml,device,service)` —— 三套词汇交集不重合。 |
| **影响范围** | `core/identity`（Identity 域词汇）· `acl_subject_types`（Authorization 域词汇）· `core/permission.Subject` |
| **实施阶段** | Authorization Implementation |
| **禁止** | 不得把 Identity Provider 值当作授权主体类型；不得移除 `acl_subject_types` 白名单（该表受 `tg_acl_subject_types_protect` 保护） |

---

# D-AUTH-19 — Agent Version Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A19`） |
| **决策** | **`Runtime Version Resolution = Monotonic Integer Revision`**（`1, 2, 3, …`），用于 **immutable published version / runtime resolution / rollback·reference**。如未来需要 semantic version，可作为 **display / release metadata**。**不得让 `runtime identity = display version string` 混在一起。** |
| **理由 / 依据** | DB `agent_versions.version integer NOT NULL` + `uq_agent_versions` + `checksum`；`agents.current_version_id` 已以**版本 ID（不可变引用）**解析版本；契约 `AgentDescriptor.version: str = "0.1.0"` 为唯一异形方。 |
| **影响范围** | `agent/registry.AgentDescriptor`（`version` 语义须改为 revision 或显式 `version_id`）· `agent_versions`（**沿用，不改**） |
| **实施阶段** | Authorization Implementation / Agent Runtime |
| **禁止** | 不得把 display 字符串作为 runtime identity；不得以字符串比较驱动版本解析 |

---

# D-AUTH-20 — ACL Uniqueness Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A20`） |
| **决策** | **保持现有 ACL 唯一性模型**。**不因 `DENY > ALLOW` 而强制修改 `resource_permissions UNIQUE`**；**不新增 `effect` 到当前 ACL uniqueness key**。冻结语义：ACL 层在同一唯一授权槽位中**不要求**同时保存 Allow 与 Deny 两条并存记录；授权状态变更采用**行替换/更新语义**，并在后续实现时保证**事务一致性与审计**。跨层 **`ACL DENY > RBAC ALLOW` 仍然成立**。 |
| **理由 / 依据** | `resource_permissions` 唯一约束 `UNIQUE (resource_id, subject_type_id, subject_id, action)` 已落库（0007，0011 实测）；跨层 deny 优先依赖 `role_permissions`（另一张表），与 ACL 行的唯一键**不冲突**；层内 allow/deny 并存需求**未获证据支持**。 |
| **影响范围** | `resource_permissions`（**不改约束**）· `services/authorization`（改判=替换 + 同事务审计） |
| **实施阶段** | Authorization Implementation |
| **禁止** | 不得重建 ACL 唯一约束；不得新增 `effect` 到唯一键 |

---

# D-AUTH-21 — Memory / Workflow Authorization ｛`DEFERRED`｝

| 字段 | 内容 |
|---|---|
| **状态** | `DEFERRED`（2026-09-23 · `OQ-A21`） |
| **已冻结的架构原则** | 未来 **Memory** 与 **Workflow** **必须使用同一 Canonical Authorization Model**；**禁止** `Memory-specific ACL system` 或 `Workflow-specific permission system`。 |
| **Owner Phase** | **Agent Runtime** |
| **理由** | `MemoryStore.read/write/delete` 与 `WorkflowRunner.run(steps)` **零授权参数**（对比 `Tool.invoke(params, context)` 有 context）；其授权动作、生命周期与 runtime semantics 需与 Agent Runtime 一并设计。 |
| **Exit Condition** | Agent Runtime PREP 产出 Memory/Workflow 授权动作与作用域定义，并经 Human 授权后冻结。 |
| **影响范围** | `agent/memory/interfaces.py` · `agent/workflow/interfaces.py`（须统一为 `AuthorizationContext`） |
| **禁止** | 在 Exit Condition 满足前**不得**为 Memory/Workflow 建立独立授权体系 |

---

# D-AUTH-22 — Audit / Event ID = UUIDv7

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `OQ-A22`） |
| **决策** | 未来 Audit / Event ID **推荐采用 `UUIDv7`**。理由：`Globally unique` + `Time ordered` + `Better index locality` + `Useful for event/audit chronology`。具体 persistence implementation 属 **P10**。 |
| **理由 / 依据** | 数据律「ID = UUIDv7（应用层生成）」；DB 全部授权相关表 `PRIMARY KEY DEFAULT uap_uuid_v7()`；现 `core/audit._new_id()` 使用 `uuid.uuid4()`，为唯一异形方；审计事件天然为时间序列，有序 id 对 **P10 `audit_logs` 分区裁剪与归档**有直接收益。 |
| **影响范围** | `core/audit`（id 生成策略）· 未来 `events`/`audit_logs`（P10） |
| **实施阶段** | P10（persistence）；契约调整可随 Authorization Implementation |
| **禁止** | 不得在 P10 之外创建 `events` / `audit_logs` |

---

# D-AUTH-23 — `agent_permissions.resource_scope` = Legacy Opaque（`GAP-11`）

> 本条**不是** OQ。它是对 `AUTHORIZATION_IMPLEMENTATION_CONTRACT.md` §26 登记的 **`GAP-11`**（P09 Schema Conflict）
> 的专项 Human Decision。**Human 显式选择 = `A — LEGACY OPAQUE`**，并同时裁定 **`ND-A`**。

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-23 · `GAP-11` · Human Decision **A**） |
| **`GAP` 状态** | **`GAP-11 = RESOLVED`** —— 本条为其**唯一**处置；**无** schema 动作。**规范表述**：`resource_scope` = **OPAQUE TEXT** · **NOT AUTHORIZATION AUTHORITY** · `ND-A = RESOLVED`（**不追加** `<> ''`）· `P09` / `0011` **unchanged** |
| **决策** | `agent_permissions.resource_scope` 保持 **P09 原有语义 = `OPAQUE TEXT`**。其值 **MUST NOT** 被解释为 Authorization Scope；**MUST NOT** 用作 canonical authorization authority；**MUST NOT** 用于推导 `PLATFORM` / `TENANT` / `SPACE` 权限；**MUST NOT** 用于扩大 effective authorization。该字段继续是 **P09 historical field + opaque metadata / restriction context**，**不是** Canonical Authorization Scope carrier。 |
| **`ND-A`** | **`RESOLVED` = 不追加** `resource_scope <> ''`。⇒ `''` / `'   '` / 其他 opaque text 在当前 P09 结构规则下**仍可存在**（`ck_agent_permissions_scope_target` 仅要求「三选一非空」，**不约束取值**）。理由：该字段**不承担** Canonical Authorization Decision，**无需通过非空约束制造伪语义**。 |
| **Canonical Scope 保护** | Canonical Authorization Scope 恒为 **`PLATFORM` / `TENANT` / `SPACE`**；`RESOURCE` / `SELF` 为 **predicate / contextual semantics**（`D-AUTH-06`）。**不得**从本字段推导上述 canonical scope。 |
| **理由 / 依据** | ① `0011` 迁移源码自述 `# 范围限定（opaque text —— 不解释、不构成授权判定）`（`0011_p09_agent_tool_permission.py:216`）；② `P09_SCHEMA_DESIGN.md:203` = `范围限定（text，**不解释**）`；③ `agent_permissions` 上**无触发器**，`resource_scope` **无 FK / 无取值约束**，唯一涉它者 `ck_agent_permissions_scope_target` 不约束取值；④ 全仓 `.py` 对其**运行时引用 = 0**（仅 0011 源 + P09 集成测试）；⑤ 表行数 = **0**（P13 seed 前）；⑥ canonical scope 已有独立承载（`roles.scope` + `ck_roles_scope` + `tg_roles_scope_shape`）。⇒ 本条是**既有 P09 设计意图在授权层的正式化**，**非**新增授权语义。 |
| **影响范围** | `AUTHORIZATION_IMPLEMENTATION_CONTRACT`（Service 禁令 / Runtime 引用规则 / `GAP-11` 行）· `AUTHORIZATION_SCHEMA_IMPACT`（`agent_permissions` = NO CHANGE）· `AUTHORIZATION_IMPLEMENTATION_TEST_MATRIX`（`AGENT-RESOURCE-SCOPE-01..04`）· `AUTHORIZATION_ACCEPTANCE_MATRIX` |
| **实施阶段** | Authorization Implementation（**仅契约 / 测试层**；**无** schema 动作） |
| **禁止** | 不得 `parse` / `normalize` / `map` / `promote` / `reinterpret` 该字段为 Canonical Authorization Scope；不得修改 `0011` 迁移 / `agent_permissions` 表 / 现有约束 / 现有索引；任何未来规范化、验证或重新定义需求 ⇒ **NEW HUMAN DECISION + P09 SUPERSESSION**。 |
| **迁移影响** | **0** —— 本次不产生 schema 变更；`0012_authz_enforcement` 的既有规划**不变**。 |

---

# D-AUTH-24 — `D-B14-08` 由 `D-AUTH-05` 取代（保留 `SC-1b`）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-24 · 冲突裁定 **A**） |
| **决策** | `D-B14-08`（"`resource_permissions.action` 零新增 semantic/format contract；`action` = opaque action identifier"）**被 `D-AUTH-05` 取代**。`resource_permissions.action` **不再**维持"无词表约束"语义；**`SC-1b`（canonical action CHECK）成立并保留**。 |
| **Supersession 关系** | `D-B14-08` → **`SUPERSEDED`** · **superseded by `D-AUTH-05`**（关系登记于本条） |
| **理由 / 依据** | ① STAGE 2 Canonical Authorization Model（`D-AUTH-05`）冻结统一 Action 词表，并要求实现可在数据层校验；② `D-AUTH-05` 的影响范围**原文即已列明** `resource_permissions.action`（"未来 CHECK，见 `D-AUTH-17`"）；③ `D-B14-08` 自身把"词表与对齐规则"**defer 到 Permission Dictionary / Authorization 阶段** —— 本阶段即该阶段，deferred 条件已兑现；④ 否则 ACL 可长期存有永不匹配的 action，数据完整性与可审计性受损。 |
| **影响范围** | `resource_permissions.action` · `SC-1b` · `tests/integration/test_resource_acl_schema.py`（`ACT-01`/`ACT-02` **保留**；"任意 opaque action 被接受"断言**移除**，改以 canonical 接受 + 非 canonical 拒绝） |
| **实施阶段** | Authorization Implementation（**已实施**，见 `0012_authz_enforcement`） |
| **禁止** | 不得据此改动 **P09 四表**（`agents`/`agent_versions`/`agent_permissions`/`tool_executions`）；不得改写 `B1-4_DECISION_LOG.md` 的**历史条文**（只允许追加 supersession 标记）；不得创建 `SC-3` |

---

# D-AUTH-25 — Action canonical 形式 = 小写

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-24 · 与冲突裁定 **A** 同批） |
| **决策** | Action 的 **canonical 存储/传输形 = 小写**：`read` `list` `create` `update` `delete` `execute` `approve` `reject` `publish` `export` `share` `admin`。**`D-AUTH-05` 的 12 个动作名与其词表成员不变**；本条规定的是其**规范形（canonical form）**。归一规则 = **NFKC → strip → casefold**；数据层 CHECK 精确匹配小写形，调用方写入前必须归一。 |
| **理由 / 依据** | 平台既有 `action` 惯例即为小写（既有 fixture `read`/`execute`/`invoke`/`delete`，以及 B1-4 文档示例 `read`/`write`/`share`）。若规范形取大写，则既有数据面与既有测试面全面失败，并使"防止拼写变体绕过授权"的防护与平台惯例**相互对立**。 |
| **影响范围** | `core/permission/vocabulary.py`（`ACTIONS` · `normalize_action`）· `services/authorization/permissions.py`（`_same_action` 双侧归一）· `migrations_alembic/versions/0012_authz_enforcement.py`（CHECK 取值）· 相关测试 |
| **明确不变（各词表保持自身大小写）** | `SUBJECT_TYPES`（`USER/ROLE/AGENT` · `D-AUTH-18`）· `STORED_SCOPES`（`PLATFORM/TENANT/SPACE` · `D-AUTH-06`）· `RISK_LEVELS`（`LOW/MEDIUM/HIGH/CRITICAL` · `D-AUTH-10`）· `EFFECTS`（`ALLOW/DENY/REQUIRES_APPROVAL` · `D-AUTH-14`）· `GRANT_EFFECTS`（`allow/deny`） |
| **实施阶段** | Authorization Implementation（**已实施**） |
| **禁止** | 不得据此改变 `D-AUTH-06`/`D-AUTH-10`/`D-AUTH-14`/`D-AUTH-18` 的词表大小写；不得反向放宽为"大小写不敏感存储"（存储形仍是精确小写，宽容度只在**入站归一**） |

---

# 附录 E — Authorization 冻结状态汇总（2026-09-24 更新）

```text
FROZEN   = 22
  D-AUTH-01 · 02 · 04 · 05 · 06 · 07 · 08 · 09 · 10 · 11
  D-AUTH-12 · 14 · 15 · 16 · 17 · 18 · 19 · 20 · 22 · 23 · 24 · 25

DEFERRED = 3
  D-AUTH-03  → Agent Runtime   （显式 Delegation Scope / Lifecycle）
  D-AUTH-13  → Tool Runtime    （Authorization Cache implementation）
  D-AUTH-21  → Agent Runtime   （Memory / Workflow authorization semantics）

SUPERSEDED（`D-AUTH` 命名空间内）= 0
  命名空间内不存在自取代。

平台级 SUPERSEDED = 1
  D-B14-08（B1-4 Decision Log，2026-09-13 `FROZEN — A`）
      → SUPERSEDED by D-AUTH-05（取代关系登记于 D-AUTH-24，2026-09-24 Human Decision A）
  显式继承并保持不变：R2-D-14（DENY > ALLOW）· R2-D-15（permission scope-neutral）·
  R4 / PMB-1（effective_platform_admin）· ACL Subject Types `user | role | agent` · P09 schema。
```

> **编号空间说明**：`D-AUTH-01`…`D-AUTH-22` 一一对应 `OQ-A01`…`OQ-A22`（22 / 22）。
> **`D-AUTH-23` 不属该序列** —— 来源自 `GAP-11`（Implementation Gap，非 OQ）。
> **`D-AUTH-24` / `D-AUTH-25` 亦不属该序列** —— 来源自 **`D-B14-08` 冲突裁定**
> （2026-09-24 Human Decision：**A — supersede `D-B14-08` 并保留 `SC-1b`**；**Action canonical 形 = 小写**）。
> 故：**`OQ` 冻结 19 `FROZEN` + 3 `DEFERRED` = 22**（未变）；
> **`D-AUTH` 条目总数 = 25，其中 `FROZEN` 22 + `DEFERRED` 3 + `SUPERSEDED` 0**。
> **平台级 supersession 计数 = 1**（`D-B14-08`），与命名空间内计数**分开表述，不得混用**。

**一致性要求（§27/§28）**：`PLATFORM_DECISION_LOG.md` ↔ `ARCHITECTURE.md` ↔ `DEPENDENCY_RULES.md` ↔
`docs/security/README.md` ↔ `docs/api/README.md` ↔ `AUTHORIZATION_ACCEPTANCE_MATRIX.md` ↔
`AUTHORIZATION_PREP_REPORT.md` ↔ `AUTHORIZATION_DECISION_RESOLUTION.md` **语义必须一致**。

**本组条目不产生实施授权**：`D-AUTH-01`…`D-AUTH-23` 的落盘与 `FROZEN` 状态**不等于**任何代码 / 迁移 / 数据库 /
配置 / 部署授权的开启（见 Charter §6 与本日志附录 D）。

---

**END OF PLATFORM_DECISION_LOG（B-1′ ，2026-09-20）**
**END OF PLATFORM_DECISION_LOG（Decision Resolution · `D-PLAT-13`…`D-PLAT-17` 写入并置 `FROZEN`，2026-09-23）**
**END OF PLATFORM_DECISION_LOG（STAGE 2 Decision Freeze · `D-AUTH-01`…`D-AUTH-22` 写入：19 `FROZEN` + 3 `DEFERRED`，2026-09-23）**
**END OF PLATFORM_DECISION_LOG（`GAP-11` 专项 · `D-AUTH-23` 写入并置 `FROZEN`；`ND-A` = 不追加 `<> ''` ⇒ `D-AUTH` 共 23 条：20 `FROZEN` + 3 `DEFERRED`，2026-09-23）**
**END OF PLATFORM_DECISION_LOG（`D-B14-08` 冲突裁定 · `D-AUTH-24`（supersession）与 `D-AUTH-25`（Action canonical 形 = 小写）写入并置 `FROZEN` ⇒ `D-AUTH` 共 25 条：22 `FROZEN` + 3 `DEFERRED` + 0 `SUPERSEDED`；平台级 supersession = 1，2026-09-24）**
