# PLATFORM_DECISION_LOG

**载体性质**：UAP **跨阶段（cross-stage）决策载体**
**Status**：`FROZEN`（`D-PLAT-01`…`D-PLAT-12` 及其子条款经 **2026-09-20** Human 确认；`D-PLAT-13`…`D-PLAT-17` 经 **2026-09-23** Decision Resolution 确认；`D-AUTH-01`…`D-AUTH-25` 经 **2026-09-23 / 09-24** 确认；**`D-AGENT-01`…`D-AGENT-16` 经 `UAP STAGE 3 — AGENT RUNTIME HUMAN DECISION FREEZE AUTHORIZATION`（2026-09-25）确认**；**`D-P10-01`…`D-P10-18` 经 `UAP P10 — HUMAN DECISION RESOLUTION`（2026-09-25）确认**；**`D-P11-01`…`D-P11-14` 经 `UAP P11 — HUMAN DECISION RESOLUTION`（2026-09-25）确认**；**`D-P12-01`…`D-P12-15` 经 `UAP P12 — HUMAN DECISION RESOLUTION`（2026-09-25）确认**）
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

## 7. 跨决策扫描义务（Cross-Decision Scan）

> **来源**：`UAP STAGE 3 — AGENT RUNTIME HUMAN DECISION FREEZE AUTHORIZATION`（2026-09-25）**§18**。
> 本条为**永久治理规则**，对所有后续 Decision Freeze 生效（不限于 Agent Runtime）。

7.1 **扫描范围（强制，缺一不可）**：任何后续 Decision Freeze **之前**必须扫描

```text
Current Decision Log
+ Historical Decision Logs   （含各阶段 *_DECISION_LOG.md 与 B1-* 系列）
+ Architecture               （ARCHITECTURE.md / DEPENDENCY_RULES.md / CORE_DOMAIN_MODEL.md / ER_MODEL.md）
+ Schema Decisions           （*_SCHEMA_DESIGN.md / MIGRATION_PLAN.md / CONSTRAINT_MATRIX.md）
+ Implementation Contracts   （*_IMPLEMENTATION_CONTRACT.md / *_IMPLEMENTATION_TEST_MATRIX.md）
```

7.2 **必须检测的三类冲突**：

| 冲突类型 | 含义 |
|---|---|
| `ACTIVE vs FROZEN` | 某 `ACTIVE`/`PROPOSED` 条目与既有 `FROZEN` 决策矛盾 |
| `FROZEN vs FROZEN` | 两条冻结决策互相矛盾（先例：`D-B14-08` vs `D-AUTH-05`） |
| `SCHEMA vs DECISION` | 已落库 schema / 迁移实现与冻结决策不一致 |

7.3 **禁止**：不同 Decision Log **各自冻结而互相不可见**。冻结前未执行本扫描者，其 `FROZEN` 状态**不具备约束辩护力**，须补扫。

7.4 **留档义务**：扫描范围、命令、命中/零命中结果须随该轮 Gate 报告留档，并登记于本载体的阶段汇总附录。

7.5 **本条的首次适用** = **2026-09-25 `STAGE 3 — AGENT RUNTIME` Decision Freeze**；扫描结果见
「附录 F — Agent Runtime 冻结状态汇总」§F.6。

7.6 本条**不修改** Charter §1–§6 的任何既有结论；本条**不产生**任何实施授权（Charter §6 继续适用）。

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

> **▶ `D-PLAT-12.a` 正式登记指针（append-only · 2026-09-27）**
>
> ```text
> `P14_RUNTIME_SLICE`：**暂定（tentative）→ 正式冻结（formally frozen）**（本 PREP 门）。
> 正式登记 = **附录 M — STEP 2 Runtime Slice 正式定义冻结登记**（EOF · append-only）。
> 本指针**不修改** `D-PLAT-12.a` 任何既有字段；其「待确认」三项的裁决结论登记于附录 M。
> ```

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

> **[`D-P10-02` 注记 · 2026-09-25]**（**append-only clarification** · 遵 Charter §5.2）
> 本条**理由**段中「现 `core/audit._new_id()` 使用 `uuid.uuid4()`，为**唯一异形方**」一句**已过期**：
> 现行实现契约 **`core/audit` 已与 UUIDv7 对齐**（`new_event_id()`），**历史 "`core/audit` exception" 表述作废**；
> 当前与 UUIDv7 不对齐者为 `core/event`（由 `OQ-P10-02` 裁定其在实施期修正）。
> 关联：`D-AUTH-22`（本条「理由 / 依据」段末句）· `D-P10-02`（附录 G）· `C-2`。
> 性质：**追加说明（append-only clarification）**。**不改写历史冻结条文、不修改本条既有结论、不产生新 supersession。**

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

# Agent Runtime Canonical Model — `D-AGENT-01` … `D-AGENT-16`

> **来源**：`STAGE 3 — AGENT RUNTIME` 的 PREP（`AGENT_RUNTIME_PREP_REPORT.md`）与
> Decision Resolution（`AGENT_RUNTIME_DECISION_RESOLUTION.md`）；OQ 编号 `OQ-AGENT-01`…`OQ-AGENT-16`。
> **Human 于 2026-09-25 通过 `UAP STAGE 3 — AGENT RUNTIME HUMAN DECISION FREEZE AUTHORIZATION`
> 逐项明确裁定**：**16 项全部 `FROZEN`**（无 unresolved OQ）。
>
> **编号空间**：本组为**新建命名空间** `D-AGENT-NN`，与 `OQ-AGENT-01`…`OQ-AGENT-16` **一一对应（16 / 16）**。
> 本命名空间**不覆盖、不复用**任何既有命名空间（`D-PLAT` · `D-B14` · `D-B15` · `D-B16` · `D-P09` · `D-MCI` · `D-AUTH`）。
> 冻结前全仓 `D-AGENT-` 命中 = **2**（均为 STAGE 3 文档中的**前瞻引用**，非定义）⇒ 无编号冲突。
>
> **本组条目不产生任何实施授权**（Charter §6）。`D-PLAT-01`…`D-PLAT-17`、`D-AUTH-01`…`D-AUTH-25`
> 与全部既有冻结决策**保持原状**；本组**不构成**对任何既有决策的 silent replacement。
> 特别地：**`D-PLAT-09` 与 `D-PLAT-11` 未被 supersede**（见下表与 §Runtime Implementation Gate）。
>
> **DEFERRED 子域**：本组含 **2 个**由冻结条文**显式**划出的 Deferred 子域（`D-AGENT-11` 流式呈交 ·
> `D-AGENT-10` Gateway 硬成本上限）。它们是**已冻结决策的明确 Deferred sub-scope**，
> **不重新产生 OQ、不构成未决项**（见附录 F.2）。

## 总表

| ID | OQ | 主题 | 状态 | 实施阶段 |
|---|---|---|---|---|
| `D-AGENT-01` | AGENT-01 | Sync / Async = 统一 Run 模型 + Sync Fast Path + Async Long Path | **FROZEN** | Agent Runtime |
| `D-AGENT-02` | AGENT-02 | Run Persistence = Persistent Run State | **FROZEN** | Agent Runtime（schema 归 `D-AGENT-13`） |
| `D-AGENT-03` | AGENT-03 | Plan Model = Hybrid（Response-first / Plan-first 双路） | **FROZEN** | Agent Runtime |
| `D-AGENT-04` | AGENT-04 | Context = Provider Contracts + Immutable Snapshot + Lazy Retrieval | **FROZEN** | Agent Runtime |
| `D-AGENT-05` | AGENT-05 | Run State Machine = Eight-State Model（表驱动） | **FROZEN** | Agent Runtime |
| `D-AGENT-06` | AGENT-06 | Concurrency = Run-level 并发 + Action-level 幂等（+ 资源版本控制补强） | **FROZEN** | Agent Runtime / Tool Runtime |
| `D-AGENT-07` | AGENT-07 | Cancellation = disconnect ≠ automatic cancellation | **FROZEN** | Agent Runtime |
| `D-AGENT-08` | AGENT-08 | Idempotency = Dual-level（Run + Tool Action） | **FROZEN** | Agent Runtime / Tool Runtime |
| `D-AGENT-09` | AGENT-09 | Tool Limits = Global + Agent + Tenant，Strictest Limit Wins | **FROZEN** | Agent Runtime |
| `D-AGENT-10` | AGENT-10 | Runtime Budget = Multi-dimensional（cost 上限 **DEFERRED**） | **FROZEN** | Agent Runtime |
| `D-AGENT-11` | AGENT-11 | API Contract = 202 + Polling（streaming **DEFERRED**） | **FROZEN** | Agent Runtime |
| `D-AGENT-12` | AGENT-12 | Worker Boundary = Execution Abstraction Only | **FROZEN** | Agent Runtime（worker 实施 **FORBIDDEN**） |
| `D-AGENT-13` | AGENT-13 | Run Persistence Schema = `agent_runs` + `agent_run_steps` | **FROZEN** | 未来 schema 阶段（**须**在 P10–P13 之后） |
| `D-AGENT-14` | AGENT-14 | Error Contract = 8 outer categories + 14 canonical codes | **FROZEN** | Agent Runtime |
| `D-AGENT-15` | AGENT-15 | Observability = Structured Logs First + Future Event/Audit Surface | **FROZEN** | Agent Runtime（P10 面延后） |
| `D-AGENT-16` | AGENT-16 | AI Gateway Dependency = **A + C**（契约可冻结 / 实施被阻塞） | **FROZEN** | Agent Runtime |

> **计数**：`FROZEN` **16** · `DEFERRED`（条目级）**0** · `SUPERSEDED` **0** ·
> `unresolved OQ` **0**；**DEFERRED 子域 2**（`D-AGENT-10` hard cost limit · `D-AGENT-11` streaming）。

---

## Runtime Implementation Gate（**引用** `D-PLAT-09` / `D-PLAT-12`，**不 supersede**）

> 本节为**引用 + 门禁表达**，**不修改** `D-PLAT-09` / `D-PLAT-12` 正文，**不构成** supersession
> （Charter §2.2：只允许引用编号与结论）。来源：Human Decision Freeze Authorization **§16 / §17**。

```text
D-PLAT-09 = FROZEN · NOT SUPERSEDED
路线 = P10 → P11 → P12 → P13 → Runtime          （路线 A）

Runtime Implementation Gate：
  P10 READY ∧ P11 READY ∧ P12 READY ∧ P13 READY ∧ AI GATEWAY RUNTIME READY
        ⇒ Agent Runtime Implementation MAY OPEN
  否则    ⇒ IMPLEMENTATION GATE = CLOSED

DECISION FREEZE ≠ IMPLEMENTATION OPEN
```

**当前实测事实（2026-09-25）**：

```text
AI Gateway Schema  = EXISTS   （0010：ai_providers / ai_models / ai_routes / ai_policies / ai_request_logs）
AI Gateway Runtime = ABSENT   （infrastructure/ai/ 不存在；Provider Adapter 代码 = 0；厂商 SDK 引用 = 0）
P10 / P11 / P12 / P13 = NOT STARTED（0013+ = 0）
⇒ Runtime Implementation Gate = CLOSED
```

---

# D-AGENT-01 — Sync / Async 呈交模型

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-01` · Human 选择 **C**） |
| **决策** | 采用 **Unified Run Model + Sync Fast Path + Async Long Path**。**Sync 与 Async 不是两套 Runtime**，而是**同一个 `AgentRun` 模型的两种呈现方式**。 |
| **冻结不变式** | `同一个 Run` · `同一状态机` · `同一授权模型` · `同一审计模型`。短任务可以同步返回；长任务、审批、长时间 Tool Execution 等使用 Async。 |
| **理由 / 依据** | 便于承载 `D-AUTH-11`/`D-AUTH-14` 的 `WAITING_APPROVAL`（异步本质）与 `D-AUTH-13` 禁缓存；避免第二套 Runtime 导致语义分叉。 |
| **影响范围** | Run 模型（`D-AGENT-02`）· API 呈交（`D-AGENT-11`）· 执行抽象（`D-AGENT-12`） |
| **实施阶段** | Agent Runtime |
| **禁止** | 不得以 sync/async 为由建立第二套状态机 / 第二套授权判定 / 第二套审计语义；不得在 Fast Path 中跳过 Authorization / Policy |

---

# D-AGENT-02 — Run Persistence

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-02` · Human 选择 **B**） |
| **决策** | 采用 **Persistent Run State**：`AgentRun` 是**一等持久化运行对象**，而非仅存在于进程内存。 |
| **冻结理由域** | `Restart Recovery` · `Approval` · `Reconnect` · `Async` · `Retry` · `Audit Correlation` |
| **未来至少允许** | `agent_runs` · `agent_run_steps`（具体 schema 在 Implementation Contract 落实，见 `D-AGENT-13`） |
| **影响范围** | `D-AGENT-13`（表设计）· `D-AGENT-07`（disconnect 留存）· `D-AGENT-08`（幂等记录） |
| **实施阶段** | Agent Runtime；**schema 实施须在 P10–P13 之后**（Runtime Implementation Gate） |
| **禁止** | 不得把本决策解释为**即刻建表授权**（本轮 `New Migration = 0`）；不得创建进程内第二套状态权威 |

---

# D-AGENT-03 — Plan Model

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-03` · Human 选择 **C**） |
| **决策** | 采用 **Hybrid**：`Simple Informational Request → Response First`；`Action / Tool / Multi-step Request → Structured Plan / Action Proposal`。 |
| **冻结不变式** | **禁止** `LLM Plan = Execution Authority`。所有 Action Proposal **仍然必须**依次经过 `Authorization → Policy → Approval → Tool`。 |
| **理由 / 依据** | 与 `D-AUTH-09`（Tool = 唯一受控出口）及 PREP §16/§18 一致；能力与成本平衡。 |
| **影响范围** | Context/Plan 边界（`D-AGENT-04`）· Tool 提案边界 · 环路防护（`D-AGENT-09`）· 错误契约（`D-AGENT-14`） |
| **实施阶段** | Agent Runtime |
| **禁止** | 不得因"Plan 已产出"而免除逐项授权；不得把模型自评的确定性/置信度当作执行许可 |

---

# D-AGENT-04 — Context Architecture

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-04` · Human 选择 **C**） |
| **决策** | 采用 **Provider Contracts + Immutable Context Snapshot + Lazy Retrieval**。 |
| **冻结八层（逻辑）** | `System` · `Tenant` · `Space` · `User` · `Agent` · `Task` · `Retrieved` · `Tool`；**每层必须** `Authorized` · `Bounded` · `Traceable`。 |
| **特别冻结** | **Context Snapshot 是本次 Run 的不可变上下文事实基线**；需要时**允许** Lazy Retrieval，但 **Retrieval 结果必须重新经过 authorization / policy / boundary checks**。 |
| **明确禁止** | `Database dump → Prompt`；`Retrieved content → System instruction`（升级为指令层）。 |
| **理由 / 依据** | 每层独立授权/限额/审计；与 `D-AUTH-06`/`D-AUTH-08`（向下继承、无隐式父继承）及 `D-AUTH-21`（Memory 授权 DEFERRED）同向。 |
| **影响范围** | Context Builder · 检索层接口位 · 安全不变式（Potentially Untrusted Context） |
| **实施阶段** | Agent Runtime |
| **禁止** | 不得把 DB 整表 / 任意查询结果直接注入 prompt；不得让 retrieved/tool 结果进入指令层；不得解释 `agent_permissions.resource_scope`（`D-AUTH-23`） |

---

# D-AGENT-05 — Run State Machine

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-05` · Human 选择 **A**） |
| **决策** | 采用 **Eight-State Model**：`CREATED` · `RUNNING` · `WAITING` · `WAITING_APPROVAL` · `COMPLETED` · `FAILED` · `CANCELLED` · `TIMEOUT`。 |
| **冻结规则** | `State transition = table-driven`；`Invalid transition = reject / fail closed`。 |
| **特别冻结** | `REQUIRES_APPROVAL → WAITING_APPROVAL`（唯一入口，`D-AUTH-14`）。**审批完成后必须重新执行 Authorization + Policy Evaluation**；**不得复用旧的授权结果**。 |
| **理由 / 依据** | 8 状态语义可穷举验证；`WAITING`（等外部输入，无授权含义）与 `WAITING_APPROVAL`（等审批）**必须分离**，否则审批边界模糊（与 `D-AUTH-14` 冲突）。 |
| **影响范围** | Run 生命周期 · 恢复/重连（`D-AGENT-02`）· 取消（`D-AGENT-07`） |
| **实施阶段** | Agent Runtime |
| **禁止** | 不得由模型输出直接进入 `WAITING_APPROVAL`；不得静默跳转或隐式恢复；不得缓存审批前的授权结论（`D-AUTH-13` 精神） |

---

# D-AGENT-06 — Concurrency

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-06` · Human 选择 **B**） |
| **决策** | 采用 **Run-level concurrency allowed + Action-level idempotency enforced**。允许 `Agent A Run 1 + Agent A Run 2` **并发存在**。 |
| **补强规则（同条冻结）** | 对**存在真实资源冲突风险**的 Tool Action，**必须**使用**资源版本 / 条件更新 / 等价并发控制机制**；**仅有 idempotency 不足以解决所有 race condition**。 |
| **冻结约束** | `same resource + same mutation` **不得**因并发而产生不可控重复或覆盖。 |
| **理由 / 依据** | 幂等键收敛"重复投递"，但**不收敛"丢失更新"（lost update）**；并发写同一资源需要乐观/悲观并发控制。 |
| **影响范围** | Tool 提案边界 · Tool Runtime 并发控制 · 幂等（`D-AGENT-08`）· 预算（`D-AGENT-10`） |
| **实施阶段** | Agent Runtime / Tool Runtime（资源版本机制归 Tool Runtime） |
| **禁止** | 不得以"有幂等键"为由免除资源版本/条件更新要求；不得开启**同一 Run 内**的步级并行（本冻结未授权） |

---

# D-AGENT-07 — Cancellation

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-07` · Human 选择 **A**） |
| **决策** | 保持 **`disconnect ≠ automatic cancellation`**。`Client disconnect` **≠** `Run cancellation`。 |
| **明确取消来源** | `Explicit User Cancel` · `Timeout` · `Admin/System Cancel` · `Shutdown` |
| **传播义务** | Cancel **必须**向 `AI` · `Tool` · `Future Worker` 传播 cancellation signal。 |
| **特别冻结** | `Cancel Request` **≠** `External Side Effect Rolled Back`。已启动且不可撤销的外部副作用必须显式记录（orphaned execution），不得以"已取消"掩盖。 |
| **理由 / 依据** | 客户端抖动不应杀死长任务；async 语义一致、结果可回收。 |
| **影响范围** | 状态机（`D-AGENT-05`）· API 取消端点（`D-AGENT-11`）· worker 侧取消传播（`D-AGENT-12`）· 审计 |
| **实施阶段** | Agent Runtime |
| **禁止** | 不得把 disconnect 解释为取消；不得把 cancel 解释为副作用回滚；不得跨进程强杀（协作式取消） |

---

# D-AGENT-08 — Idempotency

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-08` · Human 选择 **B**） |
| **决策** | 采用 **Dual-level Idempotency**：`Run Idempotency` + `Tool Action Idempotency`。 |
| **必须定义（契约义务）** | `Key` · `Scope` · `TTL` · `Collision` · `Replay` · `Result Reuse` |
| **特别冻结** | `Network Retry` + `Worker Retry` **不得**导致**重复的真实世界操作**。 |
| **理由 / 依据** | 重复副作用（资金/外部系统类）为最高危失败模式；双层为唯一覆盖"网络重试 + worker 重试"全路径者。 |
| **影响范围** | Run 幂等命名空间（`(tenant_id, idempotency_key)`）· Tool 幂等声明 · 与 `D-AGENT-06` 资源版本控制**互补且不替代** |
| **实施阶段** | Agent Runtime / Tool Runtime |
| **禁止** | 非幂等工具在缺少幂等键的重试场景下**必须拒绝**（fail closed），不得"尽力而为"执行 |

---

# D-AGENT-09 — Tool Limits

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-09` · Human 选择 **C**） |
| **决策** | 采用 **Global + Agent + Tenant** 三层限制，全部遵循 **Strictest Limit Wins**：`Effective Limit = min(Platform Limit, Tenant Limit, Agent Limit)`。 |
| **至少覆盖维度** | `max_tool_calls` · `max_runtime_steps` · `max_ai_calls` · `max_duration` |
| **特别冻结（继承规则）** | 如果**任何一层不存在限制**，**不能被解释为"无限制"**，**必须继承上层限制**。 |
| **理由 / 依据** | 防止"未配置 = 无限"的静默 fail-open；三层复用既有 jsonb 载体（`tenants.settings` / `agent_versions.definition`）⇒ 设计层 **0 schema 变更**。 |
| **影响范围** | 预算（`D-AGENT-10`）· 环路防护 · Tenant/Agent 配置面 |
| **实施阶段** | Agent Runtime |
| **禁止** | **所有上限不得被 LLM 自行提高**；不得把缺失配置解释为无限制；不得引入"哪层更宽就取哪层"的语义 |

---

# D-AGENT-10 — Runtime Budget

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-10` · Human 选择 **B**） |
| **决策** | 采用 **Multi-dimensional Runtime Budget**。冻结预算维度：`Time` · `Tokens` · `AI Calls` · `Tool Calls` · `Steps`。 |
| **预算关系（冻结）** | `Child Budget ≤ Parent Remaining Budget` |
| **Cost（分项冻结）** | `Cost Tracking = 允许`；**`Hard Cost Limit = DEFERRED until AI Gateway Runtime is ready`** |
| **DEFERRED 理由** | **不得**在 Gateway 尚未提供可靠 cost model 时**伪造 cost enforcement**。 |
| **理由 / 依据** | 多维预算覆盖"多步小额"耗尽攻击面；成本权威在 Gateway（`ai_request_logs`，`D-AGENT-16`）。 |
| **影响范围** | 预算载体 · Tool/AI 调用闸门 · 观测（`D-AGENT-15`，`cost` 字段仅作**透传/可观测**，非硬限额） |
| **实施阶段** | Agent Runtime（hard cost limit 待 Gateway Runtime ready 后**另行** Decision） |
| **禁止** | 不得把 DEFERRED 的硬成本上限当作已实现；不得用本地估算值冒充 Gateway 的成本权威；预算**只减不增**，重试**不重置**预算 |

---

# D-AGENT-11 — API Contract

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-11` · Human 选择 **B**） |
| **决策** | 采用 **202 + Polling**。Canonical API：`POST /agent-runs` · `GET /agent-runs/{id}` · `POST /agent-runs/{id}/cancel`。 |
| **呈交流程** | `POST → 202 Accepted + run_id`；Client `GET → state / result`。 |
| **Fast Path 例外（冻结边界）** | Fast Path **可以**在 Run 已立即完成**且 API contract 明确允许**时返回完成结果，但**不得创建第二套 execution model**。 |
| **DEFERRED 子域** | **`Streaming`（SSE / WebSocket）= DEFERRED**，后续**单独** Decision。 |
| **理由 / 依据** | 贴合 `D-AGENT-01` 的统一 Run 语义；流式引入长连接鉴权续期与数据泄漏面，需独立评估。 |
| **影响范围** | 路由层 · 认证/租户解析/授权前置（Run 本身亦为受控操作）· 客户端契约 |
| **实施阶段** | Agent Runtime（streaming 另行 Decision） |
| **禁止** | 不得以 Fast Path 为名绕过 Authorization / Policy / Approval；不得把 DEFERRED 的 streaming 当作已规划实现；不得新增第四端点而未经 Decision |

---

# D-AGENT-12 — Worker Boundary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-12` · Human 选择 **B**） |
| **决策** | 采用 **Execution Abstraction Only**：`Agent Runtime → Execution abstraction`。 |
| **冻结禁止（当前）** | **禁止绑定** `Celery` · `Redis Queue` · `RabbitMQ` 以及**其他具体 worker framework**。 |
| **未来约束** | Worker **必须消费统一 `AgentRun`**，**而不是**建立独立 execution engine。 |
| **理由 / 依据** | 与 `D-AGENT-01` 统一 Run 模型一致；避免过早绑定部署形态。 |
| **影响范围** | 执行抽象契约 · 取消传播（`D-AGENT-07`）· 幂等（`D-AGENT-08`） |
| **实施阶段** | Agent Runtime（**worker 实施 = FORBIDDEN**，本轮及本阶段） |
| **禁止** | 不得实现 worker；不得引入队列框架依赖；worker 未来必须**重验授权与审批**（不得信任入队时决策） |

---

# D-AGENT-13 — Run Persistence Schema

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-13` · Human 选择 **B**） |
| **决策** | 采用 **`agent_runs` + `agent_run_steps`** 两表。 |
| **冻结职责** | `agent_runs` = `Run identity / lifecycle / result / budget / correlation`；`agent_run_steps` = `Execution step state / ordering / retry / tool interaction`。 |
| **具体字段** | **仍须进入 Implementation Contract**（本冻结不逐字段裁定） |
| **P10 边界（冻结）** | `events` / `audit_logs`（**P10**）**保持独立**。**不得**把 `Audit Event` 和 `Run Step` **混成一个表**。 |
| **与 `agent_run_events` 的关系** | PREP §18 曾将 `agent_run_events` 列为 DEFERRED 候选；**本条以"Audit Event ⊥ Run Step"划界**，故**不设立 `agent_run_events`**（Run Step 归 `agent_run_steps`，审计事件归 P10 `events`/`audit_logs`）。 |
| **影响范围** | 未来 schema 阶段 · `D-AGENT-02/07/08/15` |
| **实施阶段** | **未来 schema 阶段**；按 `D-PLAT-09` **须排在 P10–P13 之后** |
| **禁止** | 本轮不得创建 `agent_runs` / `agent_run_steps`（**FROZEN DESIGN ≠ IMPLEMENTED SCHEMA**）；不得把 `resource_scope` 语义引入 run 载荷（`D-AUTH-23`）；不得与 P10 `events` 合并 |

---

# D-AGENT-14 — Error Contract

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-14` · Human 选择 **B**） |
| **决策** | 采用 **8 outer categories + 14 canonical error codes**。 |
| **必须区分（冻结，不可合并）** | `AUTHORIZATION_DENIED` ≠ `AUTHORIZATION_FAILURE` · `USER_CANCELLED` ≠ `TIMEOUT` · `AI_PROVIDER_FAILURE` ≠ `INVALID_MODEL_OUTPUT` · `TOOL_ERROR` ≠ `RUNTIME_ERROR` |
| **冻结规则** | `Error mapping 必须 deterministic`。**不得**通过**异常字符串**判断业务类型。 |
| **理由 / 依据** | `D-AUTH-12` 要求 fail-closed **且审计可辨**（系统故障不得伪装成业务拒绝，反之亦然）。 |
| **影响范围** | 错误契约值对象 · 观测（`D-AGENT-15`，`error` 字段）· API 状态码映射 · 重试分类 |
| **实施阶段** | Agent Runtime |
| **禁止** | 不得按异常字符串分类；不得合并上述四对语义；不得把 `AUTHORIZATION_FAILURE` 呈现为业务拒绝 |
| **契约级留项** | **`O-1` = RESOLVED（2026-09-25 Human Decision · APPROVED）**。8 类目的**具体命名**与 14 码的**具体枚举**（冻结条文仅具名 8 码：`AUTHORIZATION_DENIED` · `AUTHORIZATION_FAILURE` · `USER_CANCELLED` · `TIMEOUT` · `AI_PROVIDER_FAILURE` · `INVALID_MODEL_OUTPUT` · `TOOL_ERROR` · `RUNTIME_ERROR`）已在 Implementation Contract 内以**受冻结结构约束**的方式落实：契约层候选 7 条 **减去** `AI_TIMEOUT`（**合并入 `AI_PROVIDER_FAILURE`**）= 6 条 ⇒ **canonical error codes 总数恰为 14**。**`AI_TIMEOUT` 不作为独立 canonical error code**；**`BUDGET_EXCEEDED` 保持独立 canonical code，禁止并入 `TIMEOUT`**；**不得新增第 15 个 canonical code**。裁定正文见附录 **F.8**；契约见 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` §O-1 |

---

# D-AGENT-15 — Observability

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-15` · Human 选择 **C**） |
| **决策** | 采用 **Structured Logs First + Future Event/Audit Surface**。 |
| **Run 必须可关联字段** | `run_id` · `request_id` · `trace_id` · `tenant` · `space` · `actor` · `agent` · `agent_version` · `model` · `state` · `latency` · `cost` · `tool_calls` · `error` |
| **日志默认（冻结）** | `No raw sensitive prompt` · `No secret` · `No unrestricted tool payload` |
| **P10 到位后补充** | `events` · `audit_logs` |
| **特别冻结** | **不得提前创建 P10 persistence**。 |
| **理由 / 依据** | 沿用 `infrastructure/logging/redaction.py` 双重脱敏基线；三审计分离（`D-AUTH-15`）以 `run_id` 关联但不合并。 |
| **影响范围** | 日志字段白名单 · `D-AUTH-15` 三审计关联键 · `cost` 为**透传/可观测**（非硬限额，`D-AGENT-10`） |
| **实施阶段** | Agent Runtime（事件/审计面 → P10） |
| **禁止** | 不得在 P10 之外创建 `events` / `audit_logs`；不得记录原始敏感 prompt / 密钥 / 无限制 tool payload |

---

# D-AGENT-16 — AI Gateway Dependency

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-AGENT-16` · Human 选择 **A + C**） |
| **决策** | **A + C 合并**：`Agent Runtime → AI Gateway Contract → AI Gateway Runtime → Provider Adapter`。 |
| **冻结禁止** | Agent Runtime **MUST NOT** 直接依赖 `OpenAI SDK` · `Anthropic SDK` · `Gemini SDK` · **其他 Provider SDK**。 |
| **当前事实（2026-09-25 实测）** | `AI Gateway Schema = EXISTS`；`AI Gateway Runtime = ABSENT`。 |
| **冻结结论** | `Agent Runtime Contract = 可以冻结`；**`Agent Runtime Implementation = BLOCKED until AI Gateway Runtime ready`**。 |
| **理由 / 依据** | 避免重建第二套厂商接入面（密钥、日志脱敏、成本记账二次实现）；与 `D-PLAT` 的 Provider Adapter 铁律及 `D-AUTH-09` 同向。 |
| **影响范围** | Runtime 依赖面 · 模型路由权威（`ai_routes`）· 成本/token 权威（`ai_request_logs`）· Runtime Implementation Gate（见本区段 §Runtime Implementation Gate） |
| **实施阶段** | Agent Runtime（契约可先行；实施被门禁阻塞） |
| **禁止** | 不得让 Runtime 直接 import 厂商 SDK；不得让 Runtime 直连 DB（`Agent → Policy → Tool → Service → Database`）；不得绕过 Gateway 自建 provider 抽象 |

---

# 附录 F — Agent Runtime 冻结状态汇总（2026-09-25）

## F.1 计数

```text
D-AGENT 条目总数 = 16
FROZEN    = 16     （D-AGENT-01 … D-AGENT-16）
DEFERRED  = 0      （条目级）
SUPERSEDED= 0
unresolved OQ = 0  （OQ-AGENT-01 … OQ-AGENT-16 全部有明确 Human Decision）
```

## F.2 DEFERRED 子域（**已冻结决策内的明确子域，非 OQ**）

```text
① Streaming（SSE / WebSocket）
   → 归属 D-AGENT-11（API Contract）；后续【单独 Decision】
② AI Gateway Hard Cost Limit
   → 归属 D-AGENT-10（Runtime Budget）；条件 = AI Gateway Runtime ready
   → Cost Tracking 本身 = 允许（非 deferred）
```

## F.3 与既有冻结的关系（**无 supersession**）

```text
D-PLAT-09 （阶段顺序路线 A）        = FROZEN · NOT SUPERSEDED
D-PLAT-11 （首个主体只经 P13）      = FROZEN · NOT SUPERSEDED
D-PLAT-12 （Runtime 阶段门）        = FROZEN · NOT SUPERSEDED
D-AUTH-01…25                        = 原状不变（本组逐条继承，不重解释）
P09 四表 / 0011 / 0012              = 原状不变（本组不触碰）
D-B14-08 → SUPERSEDED（登记于 D-AUTH-24）= 未变；本组不产生新的 supersession
```

**显式继承清单**：`D-AUTH-01`（RBAC+ACL+Policy）· `D-AUTH-02`（Agent 独立主体）·
`D-AUTH-05`+`D-AUTH-25`（12 项小写 canonical action）· `D-AUTH-06/08`（scope 与向下继承）·
`D-AUTH-07/12`（DENY>ALLOW / FAIL CLOSED）· `D-AUTH-09`（Tool 唯一受控出口）·
`D-AUTH-10`（四档 risk，≠ permission ≠ decision）· `D-AUTH-11/14`（approval ≠ ALLOW）·
`D-AUTH-13`（无缓存）· `D-AUTH-15`（三审计分离）· `D-AUTH-16`（core=契约 / services=实现）·
`D-AUTH-19`（单调整数 revision）· `D-AUTH-21`（Memory/Workflow 授权）· `D-AUTH-22`（UUIDv7）·
`D-AUTH-23`（`resource_scope` = Legacy Opaque）。

## F.4 一致性要求

`PLATFORM_DECISION_LOG.md` ↔ `ARCHITECTURE.md` ↔ `DEPENDENCY_RULES.md` ↔
`docs/security/README.md` ↔ `docs/api/README.md` ↔ `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` ↔
`AGENT_RUNTIME_ACCEPTANCE_MATRIX.md` ↔ `AGENT_RUNTIME_PREP_REPORT.md` ↔
`AGENT_RUNTIME_DECISION_RESOLUTION.md` **语义必须一致**。

## F.5 不产生实施授权

`D-AGENT-01`…`D-AGENT-16` 的落盘与 `FROZEN` 状态**不等于**任何代码 / 迁移 / 数据库 / 配置 / 部署
授权的开启（Charter §6、附录 D）。`Runtime Implementation Gate` 见本区段前述章节。

## F.6 跨决策扫描结果（Charter §7 首次适用 · 2026-09-25）

> 依据本日志 **Charter §7.1**（扫描范围）与 **§7.2**（三类冲突），于 **2026-09-25 Decision Freeze**
> 之前执行。命令与结果见 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` §G（Decision Freeze Gate）。
> **本节为扫描的结果登记（append-only），不修改任何被扫描文档的既有结论。**

```text
扫描对象（范围）：
  本载体 PLATFORM_DECISION_LOG.md（Charter + D-PLAT-01…17 + 附录 A–E + D-AUTH-01…25）
  阶段日志：B1-4 / B1-5 / B1-6 / P09 / STEP1B_B1_2 / STEP1B_B1_3 的 *_DECISION_LOG.md
  架构面：ARCHITECTURE.md · DEPENDENCY_RULES.md · CORE_DOMAIN_MODEL.md · ER_MODEL.md
  Schema 面：P09_SCHEMA_DESIGN.md · B1-6_SCHEMA_DESIGN.md · STEP1B_CONSTRAINT_MATRIX.md ·
            STEP1B_SCHEMA_DEPENDENCY.md · STEP1B_TRIGGER_INVENTORY.md ·
            STEP1B_INDEX_STRATEGY.md · STEP1B_SEED_STRATEGY.md
  契约面：AUTHORIZATION_IMPLEMENTATION_CONTRACT.md · AUTHORIZATION_SCHEMA_IMPACT.md ·
          AUTHORIZATION_IMPLEMENTATION_TEST_MATRIX.md · STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md

结果：
  FROZEN  vs FROZEN 冲突 = 0（本轮新冻结）
  ACTIVE  vs FROZEN 冲突 = 0
  SCHEMA  vs DECISION 冲突 = 0
  陈旧一致性缺陷 = 3 处（STAGE 2 遗留，已于 2026-09-25 修正，见 §F.7）
```

## F.7 STAGE 2 遗留一致性缺陷（**本轮修正 · 主动披露**）

> 以下 3 处为 `034ee97`（STAGE 2 实施提交）**之后**仍与已实施事实不符的**陈旧声明**，
> 属**跨文档同步遗漏**（非决策冲突）。本轮依 Freeze Authorization **§20** 授权修正。

| # | 文件 | 陈旧声明 | 事实 | 处置 |
|---|---|---|---|---|
| 1 | `ARCHITECTURE.md` | "**design frozen — not implemented**. No authorization code, service or schema exists yet and `services/` has not been created." | `services/authorization/` 已存在（12 模块）；`0012` 已落库 | 修正为 **implemented**（2026-09-25） |
| 2 | `DEPENDENCY_RULES.md` §8 | "**design frozen — not implemented**. This round adds no new guard" | 同上 | 修正为 **implemented**（2026-09-25） |
| 3 | `docs/api/README.md` · `docs/security/README.md` | "Implementation exists in the working tree (**uncommitted**); acceptance pending" **且** `api/README.md` 列 canonical actions 为**大写** `READ LIST …` | 已提交（`034ee97`）· 已验收（542 passed）· `D-AUTH-25` canonical 形 = **小写** | 修正为 **committed / accepted** 与大写→小写（2026-09-25） |

> 缺陷 #3 属**文档内部自相矛盾**（同一文件第 49 行写 lowercase form，第 59 行列大写），
> 与 `D-AUTH-25` 直接冲突 ⇒ 已按 `D-AUTH-25` 归一为小写。**未修改任何冻结决策正文。**

## F.8 `O-1` 错误码枚举算术 —— **RESOLVED**（2026-09-25 Human Decision）

> **本条为 `O-1` 的正式裁定登记**。`O-1` **不是** OQ、**不是**冲突裁决，**不产生**新 canonical code，
> **不改变** `D-AGENT-14` 的任何冻结语义。**Human Decision = APPROVED**。

### F.8.1 裁定正文

```text
AI_TIMEOUT 合并归入 AI_PROVIDER_FAILURE，【不作为】独立 canonical error code。

语义解释：
  TIMEOUT              = Agent Run / Runtime 整体执行期限超时
  AI_PROVIDER_FAILURE  = AI Provider 层执行失败（【包括】 Provider Timeout）
  ⇒ AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE
```

### F.8.2 算术闭合（15 → 14）

| 部分 | 条数 |
|---|---|
| 冻结条文**直接具名**的 canonical code | 8 |
| **契约层候选**（PREP §28 `carried forward`） | 7 |
| 候选合计 | **15** |
| **减去**（`AI_TIMEOUT` ⊂ `AI_PROVIDER_FAILURE`，不设独立码） | **−1** |
| **canonical error codes 总数** | **14** ✅ |

### F.8.3 明确不变（Human 强约束）

```text
✓ 8 类错误类别                              = 不变
✓ 14 个 canonical error codes               = 不变
✓ AUTHORIZATION_DENIED ≠ AUTHORIZATION_FAILURE = 不变
✓ USER_CANCELLED ≠ TIMEOUT                  = 不变
✓ AI_PROVIDER_FAILURE ≠ INVALID_MODEL_OUTPUT = 不变
✓ TOOL_ERROR ≠ RUNTIME_ERROR                = 不变

✗ 不得增加第 15 个 canonical error code
✗ 不得将 BUDGET_EXCEEDED 合并到 TIMEOUT（BUDGET_EXCEEDED 保持独立 canonical code）
✗ 不得修改 `OQ-AGENT-14` / `D-AGENT-14` 的其他冻结语义
```

### F.8.4 同步面（**仅此**）与未触碰面

```text
同步：AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md（§I.1 · §I.2 · §I.3 · §O）
      AGENT_RUNTIME_ACCEPTANCE_MATRIX.md（§11 · §16 · §18）
      AGENT_RUNTIME_PREP_REPORT.md（§44 追加注记）
      PLATFORM_DECISION_LOG.md（本条 + `D-AGENT-14` 契约级留项行）

未触碰：migration · DDL · DML · runtime code · tests · configuration
        agent_runs / agent_run_steps  —— 【未创建】，仍为 FROZEN DESIGN
        Runtime Implementation Gate     —— 【未解除】，仍为 CLOSED
        commit / tag / push             —— 【未执行】

只读验收：7 项全 PASS（账本 ../uap-stage3-evidence/o1_acceptance.log）
```

---

**END OF PLATFORM_DECISION_LOG（B-1′ ，2026-09-20）**
**END OF PLATFORM_DECISION_LOG（Decision Resolution · `D-PLAT-13`…`D-PLAT-17` 写入并置 `FROZEN`，2026-09-23）**
**END OF PLATFORM_DECISION_LOG（STAGE 2 Decision Freeze · `D-AUTH-01`…`D-AUTH-22` 写入：19 `FROZEN` + 3 `DEFERRED`，2026-09-23）**
**END OF PLATFORM_DECISION_LOG（`GAP-11` 专项 · `D-AUTH-23` 写入并置 `FROZEN`；`ND-A` = 不追加 `<> ''` ⇒ `D-AUTH` 共 23 条：20 `FROZEN` + 3 `DEFERRED`，2026-09-23）**
**END OF PLATFORM_DECISION_LOG（`D-B14-08` 冲突裁定 · `D-AUTH-24`（supersession）与 `D-AUTH-25`（Action canonical 形 = 小写）写入并置 `FROZEN` ⇒ `D-AUTH` 共 25 条：22 `FROZEN` + 3 `DEFERRED` + 0 `SUPERSEDED`；平台级 supersession = 1，2026-09-24）**
**END OF PLATFORM_DECISION_LOG（Charter §7 跨决策扫描义务新增；附录 F.7 修正 3 处 STAGE 2 遗留陈旧一致性缺陷，2026-09-25）**
**END OF PLATFORM_DECISION_LOG（STAGE 3 Decision Freeze · `D-AGENT-01`…`D-AGENT-16` 写入并置 `FROZEN` ⇒ `D-AGENT` 共 16 条：16 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`；DEFERRED 子域 2（streaming · Gateway hard cost limit）；`D-PLAT-09` **未 supersede**；Runtime Implementation = BLOCKED，2026-09-25）**
# P10 Canonical Model — `D-P10-01` … `D-P10-18`

> **来源**：`P10 — EVENT / AUDIT` 的 READ-ONLY PREP（`P10_PREP_REPORT.md` · `P10_DECISION_RESOLUTION.md` ·
> `P10_ACCEPTANCE_MATRIX.md`，2026-09-25）与 `UAP P10 — HUMAN DECISION RESOLUTION`（2026-09-25）。
> **Human 于 2026-09-25 逐项裁定**：**18 项全部 `FROZEN`**（无 unresolved OQ）。
>
> **编号空间**：本组为**新建命名空间** `D-P10-NN`，与 `OQ-P10-01`…`OQ-P10-18` **一一对应（18 / 18）**。
> 冻结前全仓 `D-P10-` 命中 = **0** ⇒ 无编号冲突。本命名空间**不覆盖、不复用**任何既有命名空间。
>
> **本组条目不产生任何实施授权**（Charter §6）。`D-PLAT-01`…`D-PLAT-17`、`D-AUTH-01`…`D-AUTH-25`、
> `D-AGENT-01`…`D-AGENT-16` 与全部既有冻结决策**保持原状**；本组**不构成**对任何既有决策的 silent replacement。
> 特别地：**`D-PLAT-09`（路线 A）与 `D-PLAT-10`（P11 纳入 G/H/I/J）未被 supersede**；
> **`D-AUTH-15` 未被 supersede**（`D-P10-05` 明确声明）；**不产生任何新 supersession**。
> **`D-PLAT-10` 的待办 ④（`L` 与 P11 的分界）由 `D-P10-11` 闭合**，属**该待办的兑现**，非对 `D-PLAT-10` 的修订。
>
> **P10 冻结交付面（本组共同约束）**：

```text
P10 = Event / Audit persistence
      events      （分区父表 + 初始子分区）
      audit_logs  （分区父表 + 初始子分区）
    + Audit-local immutability protection（tg_audit_immutable）      ← D-P10-11

【禁止】新建 events / audit_logs / outbox 之外的表；【禁止】创建 0013+ 迁移（本组不授权）
【禁止】把 P10 扩张为 Runtime / worker / AI Gateway runtime / business event implementation
```

## 总表

| ID | OQ | 主题 | 状态 |
|---|---|---|---|
| `D-P10-01` | 01 | outbox 状态列**全部**属 P10 DDL（一次建齐） | **FROZEN** |
| `D-P10-02` | 02 | Domain Event ID = **UUIDv7 canonical**；**Outbox = durable delivery authority**，`EventBus` = 可选进程内辅助 | **FROZEN** |
| `D-P10-03` | 03 | P10 定义 `core/event` **写入契约**（实现留 `services/`） | **FROZEN** |
| `D-P10-04` | 04 | **不建** `event_types` 注册表；仅 CK 正则 + 命名约定 | **FROZEN** |
| `D-P10-05` | 05 | Authorization Audit 五类扩展语义**采用结构化 `metadata`**（**不加 first-class column**；**不产生 `D-AUTH-15` supersession**） | **FROZEN** |
| `D-P10-06` | 06 | `core/audit.AuditEvent` ↔ 列/`metadata` **映射显式化** | **FROZEN** |
| `D-P10-07` | 07 | audit 写入：**HIGH/CRITICAL 同步 · LOW 异步批量**（`STEP1A` R6） | **FROZEN** |
| `D-P10-08` | 08 | `metadata` 脱敏 = **应用层强制 + 测试守卫**；DB 侧**不加**转换逻辑 | **FROZEN** |
| `D-P10-09` | 09 | 月分区 + **仅当月子分区**；**不建 `DEFAULT` 分区** | **FROZEN** |
| `D-P10-10` | 10 | 分区创建与 retention = **手工运维**（沿用 `D-3 = D`）+ runbook | **FROZEN** |
| `D-P10-11` | 11 | **`tg_audit_immutable` = P10-owned**；消除"audit 存在但可变"窗口 | **FROZEN** |
| `D-P10-12` | 12 | **不建** linkage 列（靠 `correlation_id` / `request_id`） | **FROZEN** |
| `D-P10-13` | 13 | `GRANT` 归属记为 **OPEN（非 P10 交付）**——角色体系未落地 | **FROZEN** |
| `D-P10-14` | 14 | `classification` **可空**；"CRITICAL 只存摘要"作为**契约纪律**（不加列） | **FROZEN** |
| `D-P10-15` | 15 | **不引入 RLS**；RLS 单独立项 | **FROZEN** |
| `D-P10-16` | 16 | Runtime 关联键 = `correlation_id` + `metadata`；run 细节归 `agent_runs` | **FROZEN** |
| `D-P10-17` | 17 | 五类承载面边界**形式化 + `tests/architecture` 守卫**（实施期落地） | **FROZEN** |
| `D-P10-18` | 18 | P10 = 表 + 状态机契约 + runbook；**投递 worker 归 Runtime** | **FROZEN** |

> **计数**：`FROZEN` **18** · `DEFERRED`（条目级）**0** · `SUPERSEDED` **0** · `unresolved OQ` **0**。
> **OPEN（非 OQ，显式登记）**：`D-P10-13` 的 `GRANT` 归属（待角色体系立项）。

---

## P10 / P11 边界（`C-4` 闭合 · 冻结原文）

```text
P10 owns audit-local immutability.
P11 owns remaining trigger / cross-table constraints.
```

- **P10 不得依赖 P11 完成**才具备 `audit_logs` 的**基础不可修改性**。
- **P11 不得成为** `audit_logs` 基础 immutable security property 的**前置条件**。
- **禁止**形成如下窗口：`P10 implemented → audit exists but mutable → P11 later fixes immutability`。**该窗口必须被消除**（`D-P10-11`）。

## EventBus 与 Outbox 的关系（`C-3` 冻结原文）

```text
EventBus != Outbox
```

- 二者**不得**被描述成同一种 delivery mechanism。
- `Outbox` = **durable / reliable event delivery authority**（`events` 表 + CAS claim + lease + Reaper）。
- `EventBus` = **optional in-process auxiliary mechanism**，且：
  - **MUST NOT** replace outbox persistence
  - **MUST NOT** be treated as the durable delivery boundary
  - **MUST NOT** become the canonical cross-process delivery mechanism

---

# D-P10-01 — outbox 状态列全部属 P10 DDL

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-01` · Human Decision） |
| **决策** | `events` 的 outbox 状态列（`status` · `worker_id` · `claimed_at` · `lease_expires_at` · `attempts` · `next_attempt_at` · `last_error` · `delivered_at`）**全部**属 P10 DDL，**一次建齐**。 |
| **理由 / 依据** | `CORE_DOMAIN_MODEL` §1.6 · `ER_MODEL` §6 · `STEP1B_EVENT_OUTBOX.md` §1 三处一致列出这些列；`STEP1B_CONSTRAINT_MATRIX` §7 已冻结其 CK（`status IN (…)` · `attempts BETWEEN 0 AND 100`）。分区表二次 `ALTER` 代价高。 |
| **影响范围** | `events` 表定义（P10 唯一迁移） |
| **实施阶段** | P10 |
| **禁止** | 不得拆分成后续阶段加列；不得新增**第三张表**（`events` **即** outbox 载体，见 `D-P10-04`） |

---

# D-P10-02 — Event Identity 与 Delivery Model

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-02` · Human Decision · **含 `C-2` / `C-3`**） |
| **决策①** | **Domain Event ID = UUIDv7 canonical**。`uuid.uuid4()` **不属于**最终 P10 Event identity contract，**仅**为当前实现遗留（`core/event/interfaces.py`），**未来实施阶段修正**。 |
| **决策②** | **`Outbox` = durable / reliable event delivery authority**；**`EventBus` = optional in-process auxiliary mechanism**。 |
| **决策③（`EventBus` 强约束）** | `EventBus` **MUST NOT** replace outbox persistence；**MUST NOT** be treated as the durable delivery boundary；**MUST NOT** become the canonical cross-process delivery mechanism。 |
| **决策④** | Outbox 的 claim / lease / reaper / retry 等行为，按 P10 已发现的权威设计（`CORE` §8.2 · `STEP1B_EVENT_OUTBOX.md`）继续作为**后续 Implementation Contract** 的依据。 |
| **`C-2`（append-only clarification）** | `D-AUTH-22` 理由段「`core/audit` 为唯一异形方」**已过期**。**现行实现契约已与 UUIDv7 对齐**；历史 "`core/audit` exception" 表述**作废**。**不改写历史条文、不产生新 supersession。** |
| **`C-3`** | 所有权威文档必须明确 `EventBus != Outbox`（见本区段「EventBus 与 Outbox 的关系」）。 |
| **理由 / 依据** | 数据律「ID = UUIDv7」（`D-AUTH-22` · `UUID_STRATEGY` §6 · `CORE` §9）；outbox 语义为 `at-least-once` 持久投递（`CORE` §8.2）。 |
| **影响范围** | `core/event`（**实施期**修正，**本轮不改**）· `events` 表（`GP-11`）· 文档层 `EventBus` 表述 |
| **实施阶段** | P10（表）；`core/event` 契约修正属**未来实施阶段** |
| **禁止** | **本轮不得修改 `core/event/interfaces.py`**；不得以 `EventBus` 取代 outbox；不得承诺 exactly-once |

---

# D-P10-03 — events 写入契约与生产者边界

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-03` · Human Decision） |
| **决策** | P10 定义 **`core/event` 写入契约**（值对象 + 校验 + "与业务写入同事务"约束）；**实现留 `services/`**（后续阶段，`D-AUTH-16` 模式）。 |
| **理由 / 依据** | `STEP1B_EVENT_OUTBOX.md` §7 已冻结写入模式（`BEGIN; 业务写入; INSERT events; COMMIT;`）并**禁止**把投递放入业务事务；但未定义契约载体。 |
| **影响范围** | `core/event`（写入契约）· 未来 `services/` 实现 |
| **实施阶段** | P10（契约）；实现 → 后续阶段 |
| **禁止** | 不得在 P10 实施投递或业务写入实现；不得让写入绕过同事务约束（否则 `at-least-once` 前提被破坏） |

---

# D-P10-04 — event_type 命名空间与 schema_version

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-04` · Human Decision） |
| **决策** | **不建** `event_types` 注册表。`event_type` 仅由 CK 正则 + 命名约定（`namespace.aggregate.action`）约束；`schema_version` 仅**单调递增**。 |
| **理由 / 依据** | CK 已冻结（`STEP1B_CONSTRAINT_MATRIX` §7）；P10 冻结交付面**只有两张表**，新增 `event_types` 表将构成**隐含 scope 扩张**。 |
| **影响范围** | `events.event_type` 约束解释 |
| **实施阶段** | P10 |
| **禁止** | 不得在 P10 新增注册表；不得以自由字符串绕过 CK；未来若需注册表 ⇒ **新的 Human Decision** |

---

# D-P10-05 — Authorization Audit 表达力（**`C-1` 闭合**）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-05` · Human Decision · **`C-1` = RESOLVED**） |
| **决策** | `Authorization Audit` 至少必须能够表达 `subject` · `delegator` · `decision` · `policy` · `approval`。**在当前 P10 schema contract 下，这些语义采用结构化 `metadata` 表达**，即由 **`audit_logs.metadata`** 承担上述扩展审计上下文。 |
| **保持** | `reason` · `risk_level` · `metadata` 的现有审计承载方式**不变**；**不自动增加新的 first-class columns**。 |
| **重要约束** | `metadata` 必须保持**结构化、可验证、可追踪**；**不得**把 `metadata` 视为任意非结构化文本垃圾桶；**不得**把 `metadata` 作为**绕过 canonical audit fields 的手段**。 |
| **Supersession** | **不产生 `D-AUTH-15` supersession。** `D-AUTH-15` 保持 `FROZEN` 原状。 |
| **理由 / 依据** | `D-AUTH-15` 要求"**至少需能表达**"，未指定落列；冻结 `audit_logs` 列集（`CORE` §1.6 · `CONSTRAINT` §7 · `ER_MODEL` §6）**无**这 5 类列。选 `metadata` ⇒ **P10 不触碰任何冻结 schema**。 |
| **影响范围** | `audit_logs.metadata`（契约层语义）· `core/audit.AuditEvent`（`D-P10-06` 映射） |
| **实施阶段** | P10（契约）；持久化随 P10 migration（**本轮未授权**） |
| **禁止** | 不得为这 5 类语义新增 first-class column（除非**新的 Human Decision + 显式 supersession**）；不得把 `metadata` 变成非结构化垃圾桶；不得用 `metadata` 绕过 canonical audit fields |

---

# D-P10-06 — `core/audit.AuditEvent` 映射显式化

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-06` · Human Decision） |
| **决策** | 将 `core/audit.AuditEvent` 与 `audit_logs` **列 + `metadata` 路径**的映射**显式化**（一对一可测）。 |
| **理由 / 依据** | `D-AUTH-15` 影响范围原文已列 `core/audit.AuditEvent`（契约扩字段）；`D-P10-05` 决定扩展语义走 `metadata` ⇒ 需显式映射以防漂移。 |
| **影响范围** | `core/audit`（映射表）· `audit_logs` |
| **实施阶段** | P10（契约） |
| **禁止** | 不得留下"契约字段无落点"的字段；不得让映射依赖隐式约定 |

---

# D-P10-07 — audit 写入同步 / 异步策略

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-07` · Human Decision） |
| **决策** | 采纳 `STEP1A_DESIGN_REPORT.md` **`R6`**：**HIGH / CRITICAL 同步写**，**LOW 异步批量**；写入失败进 outbox 补偿，**不阻塞主流程**。 |
| **理由 / 依据** | `STEP1A` R6 原文；`CORE` §13 的脱敏与摘要纪律。 |
| **影响范围** | 审计写入路径 · outbox 补偿面 |
| **实施阶段** | P10 |
| **禁止** | **FAIL CLOSED 语义不受影响**：审计写入失败**不得**放行受控操作（`D-AUTH-12`）；不得把异步通道当作丢审计的借口 |

---

# D-P10-08 — `metadata` 脱敏执行点

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-08` · Human Decision） |
| **决策** | `metadata` 脱敏 = **应用层强制**（沿用 `infrastructure/logging/redaction.py` 单点权威）+ **测试守卫**（AK/SK / token / PII 模式扫描）；**DB 侧不加转换逻辑**。 |
| **理由 / 依据** | `CORE` §1.6 已冻结"`metadata` **写入前已脱敏**"；`CORE` §13"审计 `metadata` 与日志统一走 `redaction`"。 |
| **影响范围** | 应用层写入路径 · `tests/security` 守卫 |
| **实施阶段** | P10 |
| **禁止** | 不得在 `audit_logs` 上引入 `tg_audit_immutable` **以外**的 trigger；不得让脱敏规则出现第二套权威（DB 侧） |

---

# D-P10-09 — 分区粒度与 `DEFAULT` 分区

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-09` · Human Decision） |
| **决策** | 月分区（`RANGE (occurred_at)`）+ **仅当月子分区**；**不建立 `DEFAULT` 分区**。 |
| **理由 / 依据** | `STEP1B_SCHEMA_DEPENDENCY.md:265-270` 冻结"建父表 + **当月子分区**"；`DEFAULT` 分区会使 `ATTACH PARTITION` 需先移动行，并**静默捕获越界写入**（与"审计不得静默"相悖）。 |
| **影响范围** | `events` / `audit_logs` 分区结构（P10 迁移） |
| **实施阶段** | P10 |
| **禁止** | 不得建立 `DEFAULT` 分区；不得改变冻结的月分区粒度 |

---

# D-P10-10 — 分区创建与 retention 的运维模型

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-10` · Human Decision） |
| **决策** | **手工运维模型**：沿用 **B1-6 先例（`D-3 = D`）**——未来月份分区创建与到期 `DROP` 为**手工运维职责**，自动化延后至未来 operational/runtime 阶段；P10 交付 **runbook**。 |
| **理由 / 依据** | `B1-6_DECISION_LOG.md:363`（原文：*manual operational responsibilities … Automation is deferred*）· `B1-6_TEST_MATRIX.md` RF5。 |
| **影响范围** | 运维面（非 schema）；不发生 DDL 于迁移之外 |
| **实施阶段** | P10（runbook）；自动化 → 未来立项 |
| **禁止** | 不得在 P10 引入 `pg_partman` 等新组件；不得给应用运行时 DDL 权限（`CORE` §13 三角色模型） |

---

# D-P10-11 — Audit Immutability Ownership（**`C-4` 闭合**）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-11` · Human Decision · **`C-4` = RESOLVED**） |
| **决策** | **`tg_audit_immutable` = P10-owned**。P10 implementation **必须**保证 `audit_logs → immutable protection`，**不能依赖 P11 完成后**才具备基本的审计不可修改性。 |
| **边界（冻结原文）** | `P10 = Event / Audit persistence + Audit-local immutability protection`；`P11 = remaining trigger / cross-table constraint layer`。 |
| **强约束** | **P11 不得成为** `audit_logs` 基础 immutable security property 的**前置条件**。**禁止**形成 `P10 implemented → audit exists but mutable → P11 later fixes immutability`；**该窗口必须被消除**。 |
| **与 `D-PLAT-10` 的关系** | `D-PLAT-10`（FROZEN）**待办 ④** 原文即载明「`L`（`tg_audit_immutable`）**属 P10**，须与 P11 明确分界」。本条**闭合该待办**（**兑现**，非修订）；`D-PLAT-10` 的「P11 纳入 **G/H/I/J**」**未被改动**（`L` 本不在 G/H/I/J 之列）。 |
| **理由 / 依据** | `STEP1B_TRIGGER_INVENTORY.md` §L（最早 phase = P10）· `STEP1B_SCHEMA_DEPENDENCY.md:241` · `D-PLAT-10` 待办 ④；否则存在真实可改写的安全窗口。 |
| **影响范围** | P10 迁移含 `tg_audit_immutable` · P11 trigger 清单（`L` 不计入） |
| **实施阶段** | P10 |
| **禁止** | 不得把 `tg_audit_immutable` 推迟到 P11；不得形成可变窗口；不得改动 G/H/I/J 的 P11 归属 |

---

# D-P10-12 — `events` ↔ `audit_logs` linkage

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-12` · Human Decision） |
| **决策** | **不建**显式 linkage 列（`audit_logs.event_id` / `events.audit_id`）。以 `correlation_id` / `request_id` 承担关联。 |
| **理由 / 依据** | `ER_MODEL` §6 已定义为**弱关系** `events \|\|--o\| audit_logs : "may be mirrored by"`（无 FK）；改列集将波及三份冻结 schema 文档。 |
| **影响范围** | 关联查询语义（`audit_logs.correlation_id`） |
| **实施阶段** | P10 |
| **禁止** | 不得新增 linkage 列，除非**新的 Human Decision + 显式 supersession** |

---

# D-P10-13 — DB 角色与 `GRANT` 归属

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-13` · Human Decision） |
| **决策** | `audit_logs` 的 `GRANT INSERT, SELECT` **不属 P10 交付**；登记为 **OPEN**——角色体系（`uap_app` / `uap_migrator` / `uap_readonly`）**尚未在任何 migration 中落地**（实测：既有 12 个 migration 中 `GRANT` 语句 = 0）。 |
| **理由 / 依据** | `CORE` §13 定义三角色模型，但**尚未实现**；在角色不存在时于 P10 单方面发明权限模型将产生**不可执行的 `GRANT`** 与**第二套权威**。 |
| **影响范围** | 权限面（非 schema）；OPEN 台账 |
| **实施阶段** | **非 P10**；随角色体系立项统一裁定 |
| **禁止** | 不得在 P10 单方面创造权限模型；不得给应用运行时 DDL 权限；**`audit_logs` 的不可变性由 `D-P10-11` 的 trigger 保证，不依赖 `GRANT`** |
| **OPEN 登记** | `OPEN-P10-1`：DB 角色体系 + `GRANT` 归属（**非 OQ · 显式开放项**） |

> **指针（append-only · 2026-09-27 · **不改写上方任何字段**）**：`OPEN-P10-1` 已由
> **`OPEN-P10-1 DECISION FREEZE`** 结项（`D-P10-13` 的 `GRANT` 归属问题转由该命名空间裁定）
> ⇒ 见 **`# OPEN-P10-1 Canonical Model — D-OP101-01 … D-OP101-14`** 与**附录 L**。
> 本行**仅**建立指针；`D-P10-13` 的「决策」「理由 / 依据」「影响范围」「禁止」「OPEN 登记」字段
> **逐字保持原样**（历史记录不得改写）。

---

# D-P10-14 — `classification` 与摘要策略

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-14` · Human Decision） |
| **决策** | `audit_logs.classification` **可空**（`NULL` = 不适用，如平台级事件）；NULL 的语义在**契约层显式定义**并加守卫。"**CRITICAL 只存摘要**"作为**契约纪律**落实，**不新增列**。 |
| **理由 / 依据** | 冻结 CK 原文即「`classification IN (…)`（**可空则按策略**）」⇒ 可空在冻结文本之内；`CORE` §13"CRITICAL 只存摘要"。 |
| **影响范围** | `audit_logs.classification` 语义 · 契约守卫 |
| **实施阶段** | P10 |
| **禁止** | 不得新增摘要列（如需 ⇒ 新 Human Decision）；分级**只能升不能随意降**，降级必须写 `audit_logs` 并注明 `reason`（`CORE` §7） |

---

# D-P10-15 — RLS

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-15` · Human Decision） |
| **决策** | **不在 P10 引入 RLS**。租户隔离继续依赖 tenant 谓词 + 应用层强制断言 + 越权写入审计；RLS **单独立项**（未来 phase）。 |
| **理由 / 依据** | `CORE` §13 原文将 RLS 标为"**（可选，见 Q1）**"（**非强制**）；既有边界先例 `D-B14-10` / `D-B14-12` 的 trigger 均**强制声明"不引入 RLS"**；RLS 依赖会话变量，缺失即策略失配（配置错误时 fail-open 面）。 |
| **影响范围** | 隔离实现方式（保持应用层） |
| **实施阶段** | P10（不引入）；RLS → 未来立项 |
| **禁止** | 不得在 P10 引入 RLS；不得以 RLS 替代既有 `CORE` §2.8 的四层隔离设计 |

---

# D-P10-16 — Runtime 关联键载体

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-16` · Human Decision） |
| **决策** | Runtime 关联键（`run_id` / `trace_id` 等）**不新增 `audit_logs` 列**；由 **`correlation_id`（跨面关联）+ `metadata`** 承担；**run 细节归 `agent_runs`**（`D-AGENT-13`，独立于 P10）。 |
| **理由 / 依据** | `D-AGENT-15` 冻结 "Structured Logs First + Future Event/Audit Surface"，P10 面延后补充；`D-AGENT-13` 已把 run 持久化归于 **`agent_runs` / `agent_run_steps`**（**非 P10**）。 |
| **影响范围** | 跨面关联语义 · 与 `D-AGENT-13` 的分工边界 |
| **实施阶段** | P10（关联语义）· Runtime（run 载荷） |
| **禁止** | **不得把 P10 扩张为 Agent Runtime persistence**；不得在 `audit_logs` 加 `run_id` / `trace_id` 列（除非新 Human Decision） |

---

# D-P10-17 — 五类承载面边界的形式化与守卫

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-17` · Human Decision） |
| **决策** | 五类承载面（`event` / `audit` / `operational log` / `trace` / `metric`）边界**形式化声明** | `event` → `events` · `audit` → `audit_logs` · 其余**非 P10**（log → `infrastructure/logging`；trace → 日志信封字段；metric → 未定义） | 并**新增 `tests/architecture/` 守卫**使边界**可强制**（守卫随**实施提交**同批落地）。 |
| **理由 / 依据** | `DEPENDENCY_RULES.md` 末节纪律："**写在文档而无测试的规则属文档，非强制**"；`tests/architecture/` 现有 2 文件、**无** event/audit 守卫。 |
| **影响范围** | 文档声明 · `tests/architecture/`（实施期） |
| **实施阶段** | P10（声明）；守卫 → 实施提交 |
| **禁止** | 不得把 operational log 写入 `audit_logs`；不得让 `event` 与 `audit` 混为一体；不得无测试地声明边界为"强制" |

---

# D-P10-18 — outbox 投递 worker 的阶段归属

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P10-18` · Human Decision） |
| **决策** | **P10 仅交付 `events` / `audit_logs` 表 + outbox 状态机契约 + 运维 runbook**；**投递 worker 实施归 Runtime 阶段**（`P13` 之后，`D-PLAT-09` 路线 A）。 |
| **理由 / 依据** | `TRIGGER_INVENTORY` §M（claim 由应用层 CAS；依赖**应用侧 worker 进程**）· `apps/worker/main.py` 为 placeholder · `D-AGENT-12`（**Execution Abstraction Only**，禁 Celery/Redis Queue/RabbitMQ）· `D-PLAT-09` 路线 A。 |
| **影响范围** | P10 交付边界 · Runtime 范围（是否含 outbox 投递） |
| **实施阶段** | P10（表 + 契约）；worker → Runtime |
| **禁止** | 不得在 P10 实施投递 worker；不得绑定队列框架（`D-AGENT-12`）；不得承诺 exactly-once |

---

# 附录 G — P10 冻结状态汇总（2026-09-25）

## G.1 计数

```text
D-P10 条目总数 = 18
FROZEN     = 18    （D-P10-01 … D-P10-18）
DEFERRED   = 0     （条目级）
SUPERSEDED = 0
unresolved OQ = 0  （OQ-P10-01 … OQ-P10-18 全部有明确 Human Decision）
```

## G.2 `C-1` … `C-4` 处置

| ID | 性质 | 处置 | 依据 |
|---|---|---|---|
| `C-1` | `FROZEN` vs `SCHEMA`（`D-AUTH-15` 五类语义 vs `audit_logs` 列集） | **RESOLVED** —— 采用**结构化 `metadata`**；**不加 first-class column**；**不产生 `D-AUTH-15` supersession** | `D-P10-05` |
| `C-2` | `DECISION` 描述 vs `CODE` 现状（`D-AUTH-22` 理由段过期） | **CLARIFIED** —— append-only clarification：现行实现契约已 UUIDv7 对齐；历史 "`core/audit` exception" 表述作废；**不改写历史条文、不产生新 supersession** | `D-P10-02` + `D-AUTH-22` 注记 |
| `C-3` | `CONTRACT` vs `SCHEMA DESIGN`（`EventBus` vs outbox） | **RESOLVED** —— 冻结 `EventBus != Outbox`；Outbox = durable authority；`EventBus` = 可选进程内辅助（三项 MUST NOT） | `D-P10-02` |
| `C-4` | `DECISION` 待办未闭合（`L` 与 P11 分界） | **RESOLVED** —— `tg_audit_immutable` = **P10-owned**；`P10 = persistence + audit-local immutability`；`P11 = remaining trigger / cross-table constraints`；**消除可变窗口** | `D-P10-11` |

## G.3 与既有冻结的关系（**无 supersession**）

```text
D-PLAT-09 （P10 → P11 → P12 → P13 → Runtime） = FROZEN · NOT SUPERSEDED
D-PLAT-10 （P11 纳入 G/H/I/J）                 = FROZEN · 未修订（L 本不在 G/H/I/J 之列；待办 ④ 由 D-P10-11 兑现）
D-PLAT-11 （首个主体只经 P13）                 = FROZEN · NOT SUPERSEDED
D-AUTH-15 （审计 ≠ 工具执行审计）              = FROZEN · NOT SUPERSEDED（D-P10-05 显式声明）
D-AUTH-01…25                                   = 原状不变（本组逐条继承）
D-AGENT-12/13/15                               = 原状不变（本组逐条继承）
P09 四表 / 0010 / 0011 / 0012                  = 原状不变（本组不触碰）
平台级 supersession 计数 = 1（D-B14-08，登记于 D-AUTH-24）——【本组不新增】
```

## G.4 四类依赖分离（如实登记）

```text
schema dependency       : events / audit_logs 依赖 users 存在；tenant_id / space_id 无强制 FK
design dependency       : 依赖 STEP 1-A 冻结设计；P11 依赖 P10 表存在（tg_audit_immutable 除外 → D-P10-11）
implementation dependency: P10 实施依赖 P09 完成（已 ✅）与单头 0012（已 ✅）
runtime dependency      : P10 不依赖任何 Runtime；Runtime 单向依赖 P10（D-AGENT-15）
```

## G.5 一致性要求

`PLATFORM_DECISION_LOG.md` ↔ `P10_PREP_REPORT.md` ↔ `P10_DECISION_RESOLUTION.md` ↔
`P10_ACCEPTANCE_MATRIX.md` ↔ `ARCHITECTURE.md` ↔ `DEPENDENCY_RULES.md` **语义必须一致**。

## G.6 不产生实施授权

`D-P10-01`…`D-P10-18` 的落盘与 `FROZEN` 状态**不等于**任何代码 / 迁移 / 数据库 / 配置授权的开启
（Charter §6、附录 D）。**P10 / P11 Implementation = NOT AUTHORIZED**。

## G.7 跨决策扫描结果（Charter §7）

```text
扫描面：本载体（Charter + D-PLAT-01..17 + 附录 A–F + D-AUTH-01..25 + D-AGENT-01..16）
        阶段日志（B1-4 / B1-5 / B1-6 / P09 / STEP1B_B1_2 / STEP1B_B1_3）
        架构面（ARCHITECTURE / DEPENDENCY_RULES / CORE_DOMAIN_MODEL / ER_MODEL）
        Schema 面（STEP1B_SCHEMA_DEPENDENCY / CONSTRAINT_MATRIX / TRIGGER_INVENTORY /
                  INDEX_STRATEGY / SEED_STRATEGY / UUID_STRATEGY）
        契约面（STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT / STEP1A_DESIGN_REPORT）

结果：FROZEN vs FROZEN 冲突 = 0
      ACTIVE vs FROZEN 冲突 = 0
      SCHEMA vs DECISION 冲突 = 0（C-1 已按 D-P10-05 闭合）
      条目级 supersession 新增 = 0
      陈旧描述 = C-2（已 append-only clarification）+ ER/CONSTRAINT 两项次要不一致（登记，未修改）
```

---

# P11 Canonical Model — `D-P11-01` … `D-P11-14`

> **来源**：`P11 — TRIGGERS / CROSS-TABLE CONSTRAINTS` 的 READ-ONLY PREP（`P11_PREP_REPORT.md` ·
> `P11_DECISION_RESOLUTION.md` · `P11_ACCEPTANCE_MATRIX.md`，2026-09-25）与
> `UAP P11 — HUMAN DECISION RESOLUTION`（2026-09-25）。
> **Human 于 2026-09-25 逐项裁定**：**14 项全部 `FROZEN`**（无 unresolved OQ）。
>
> **编号空间**：本组为**新建命名空间** `D-P11-NN`，与 `OQ-P11-01`…`OQ-P11-14` **一一对应（14 / 14）**。
> 冻结前全仓 `D-P11-` 命中 = **1**（本阶段文档中的**前瞻引用**，非定义）⇒ 无编号冲突。
>
> **本轮不含任何实施**：无 trigger / function / migration / DDL / DML / code / test / config 变更；
> 本组条目**不产生任何实施授权**（Charter §6）。`P11 / P12 / P13 IMPLEMENTATION = NOT AUTHORIZED`。
>
> **编号重映射（显式登记，非静默）**：PREP 轮的 OQ 编号中，**`OQ-P11-06` 与 `OQ-P11-07` 的主题相对
> 本轮 Human Decision 对调**。**canonical 编号以本条区段为准**：
> `D-P11-06` = **Existing Version Immutability Boundary**（`K`）· `D-P11-07` = **Tenant / Space / Authorization Boundary**。
> 本节及其下所有引用一律使用 canonical 编号；PREP 报告保留 pre-freeze 编号并以 append-only 注记给出映射。

## 总表

| ID | OQ | 主题 | 状态 |
|---|---|---|---|
| `D-P11-01` | 01 | P11 canonical delivery scope = **G/H/I/J**；其余保持原阶段归属 | **FROZEN** |
| `D-P11-02` | 02 | G/H/I/J **exact semantics** | **FROZEN** |
| `D-P11-03` | 03 | Trigger timing（G BEFORE · H AFTER · I BEFORE · J AFTER） | **FROZEN** |
| `D-P11-04` | 04 | Failure semantics（`RAISE` ⇒ 事务失败 ⇒ DML 回滚） | **FROZEN** |
| `D-P11-05` | 05 | Role / Agent lifecycle **asymmetry = INTENTIONAL** | **FROZEN** |
| `D-P11-06` | 06 | **Existing Version Immutability Boundary**（`K` 不得重建/改语义/移所有权） | **FROZEN** |
| `D-P11-07` | 07 | **Tenant / Space / Authorization Boundary**（禁止把授权决策塞进 trigger） | **FROZEN** |
| `D-P11-08` | 08 | `SECURITY INVOKER` = canonical；**禁止** `SECURITY DEFINER` | **FROZEN** |
| `D-P11-09` | 09 | Recursion / hidden DML 边界（J 限定；禁 trigger chain） | **FROZEN** |
| `D-P11-10` | 10 | P10 / P11 ownership（`L` = P10-owned ⇒ OUT OF P11） | **FROZEN** |
| `D-P11-11` | 11 | P11 / P12 边界（**不建顺手索引**） | **FROZEN** |
| `D-P11-12` | 12 | P11 / P13 边界（trigger 先于 seed；**P11 零 seed**） | **FROZEN** |
| `D-P11-13` | 13 | **`GAP-INV-1`** = supplementary inventory gap（**不重排、不插入、不迁移、不重分类**） | **FROZEN** |
| `D-P11-14` | 14 | 既有 P3 audit 陈述（**trigger does NOT write audit**） | **FROZEN** |

> **计数**：`FROZEN` **14** · `DEFERRED` **0** · `SUPERSEDED` **0** · `unresolved OQ` **0**。

---

## P11 canonical invariants（本轮冻结后必须保持）

```text
G/H/I/J                       = 4 canonical P11 triggers
L                             = P10-owned（tg_audit_immutable）
A/B/C/C2/D/E/F/F2/K           = existing（已有阶段实现，不得重建/复制）
M                             = events 无 DB trigger
阶段顺序                      = P10 → P11 → P12 → P13 → Runtime
                                （D-PLAT-09 未被 supersede，亦不得 supersede）
```

## 三向边界（冻结原文）

```text
P10 = Event / Audit persistence + tg_audit_immutable
P11 = G/H/I/J + remaining cross-table trigger constraints
P12 = indexes
P13 = seed / data initialization

P11 ──✗──▶ P12 index scope（不得在 P11 migration 内私自加入）
P11 ──✗──▶ P13 seed（不得插 acl_subject_types / bootstrap user / bootstrap role / agent subject seed）
P11 ──✗──▶ P10 audit trigger（不得 CREATE / MODIFY audit_logs 或 events 的 trigger，不得 replace L）

P11 semantic correctness MUST NOT depend on P12 business semantics
```

---

# D-P11-01 — P11 Trigger Scope / Ownership

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-01` · Human Decision） |
| **决策** | P11 的 **canonical delivery scope** 固定为 **G / H / I / J**（`tg_acl_subject_exists` · `tg_acl_user_hard_delete` · `tg_acl_role_delete_block` · `tg_agent_acl_expire`）。 |
| **其余对象** | `A / B / C / C2 / D / E / F / F2 / K` = **已有阶段实现**；`L` = **P10-owned**；`M` = **events 无 DB trigger**。 |
| **理由 / 依据** | 实测：迁移内 `CREATE TRIGGER` **24 语句 / 8 migration**；A–M 清单中 9 项已实现、L 归 P10、M 无对象 ⇒ **仅 G/H/I/J 未实现**；与 `D-PLAT-10`「P11 纳入 G/H/I/J」**逐字一致**。 |
| **影响范围** | P11 实施清单（4 trigger + 4 function） |
| **实施阶段** | P11（**本轮未授权**） |
| **禁止** | **不得**因 P11 再次实现或复制上述已有对象；不得扩张 P11 交付面至上述任何项 |

---

# D-P11-02 — G/H/I/J Exact Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-02` · Human Decision） |
| **G** | `name = tg_acl_subject_exists` · `table = resource_permissions` · `timing = BEFORE INSERT OR UPDATE OF subject_type_id, subject_id`。职责：`user → users.id` · `role → roles.id` · `agent → agents.id`；**必须拒绝不存在的 subject**。**不得引用 `groups`**。**不得承担 Authorization Evaluation**。 |
| **H** | `name = tg_acl_user_hard_delete` · `table = users` · `timing = AFTER DELETE`。**只针对硬删除流程**清理 `resource_permissions` 中的 user ACL。**软删除不得通过 H 清理**。 |
| **I** | `name = tg_acl_role_delete_block` · `table = roles` · `timing = BEFORE DELETE`。role 仍被 ACL 引用时**拒绝删除**。其语义是 **ACL reference protection**，**不是授权求值器**。 |
| **J** | `name = tg_agent_acl_expire` · `table = agents` · `timing = AFTER UPDATE OF status OR AFTER DELETE`。agent 归档/删除时**使其 ACL 失效**：`inherited = true` · `expires_at = now()`。**J 不负责删除 agent 本身**。 |
| **理由 / 依据** | `STEP1B_TRIGGER_INVENTORY.md` §G/§H/§I/§J（原始语义）· `B1-4_DEPENDENCY.md` §3 · `B1-4_SCHEMA_DESIGN.md` §4.2/§4.3；**实测列/状态值吻合**：`resource_permissions.inherited` / `.expires_at`（0007）· `agents.status ∈ {draft,active,disabled,archived}`（0011）· `acl_subject_types.key ∈ {user,role,agent}`（0007） |
| **影响范围** | 4 trigger + 4 function 的语义基线 |
| **实施阶段** | P11 |
| **禁止** | G 不得引用 `groups`；G/H/I 不得承担 authorization evaluation；H 不得用于软删除路径；J 不得删除 agent 行 |

---

# D-P11-03 — Trigger Timing

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-03` · Human Decision） |
| **决策** | 保持既定 timing，**不调整**为其他相位：`G = BEFORE` · `H = AFTER` · `I = BEFORE` · `J = AFTER`。 |
| **理由 / 依据** | **保持既有 trigger contract 与当前行为语义一致**（既有 24 条触发器即按 BEFORE=校验 / AFTER=清理 分工）。 |
| **影响范围** | 4 trigger 的事件相位 |
| **实施阶段** | P11 |
| **禁止** | 不得把 G/I 改为 AFTER，不得把 H/J 改为 BEFORE |

---

# D-P11-04 — Failure Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-04` · Human Decision） |
| **决策** | 任何违反 P11 trigger invariant 的情况：`RAISE` → **当前事务失败** → **当前相关 DML 回滚**。 |
| **H/J 的额外规则** | H/J 的**内部 DML 若失败** ⇒ **整个外层操作失败并回滚**。 |
| **理由 / 依据** | 与 `D-AUTH-12`（FAIL CLOSED）同向；既有先例 `RAISE EXCEPTION` 共 37 处、无一处吞异常。 |
| **影响范围** | 4 个 function 的异常语义 |
| **实施阶段** | P11 |
| **禁止** | 不得 `silently ignore` · `warn-only` · `partial success` · `best-effort continuation` |

---

# D-P11-05 — Role / Agent Lifecycle Asymmetry

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-05` · Human Decision） |
| **决策** | **保留当前机制的不对称，不强行统一**：<br>`Archived Role` → **ACL 数据保留**；**Authorization Layer** 在 decision 时依据 `archived_at` **排除/拒绝**。<br>`Archived Agent` → **J trigger 使 ACL 到期**；`resource_permissions` **数据保留**。 |
| **性质判定** | 该不对称是**有意保留的机制差异**，**不是 P11 缺陷**。 |
| **理由 / 依据** | `B1-4_SCHEMA_DESIGN.md:136/137`；两者语义不同（role 的 deny 行需保留用于审计追溯；agent 需 ACL 临时到期）。 |
| **影响范围** | 生命周期机制边界（role 走授权层 · agent 走 trigger） |
| **实施阶段** | P11（仅 J 侧） |
| **禁止** | P11 **不得新增** `role archive → ACL mutation`；**不得移除 J** |

---

# D-P11-06 — Existing Version Immutability Boundary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-06` · Human Decision） |
| **决策** | `K = tg_version_immutable` **已属于既有阶段**。P11：**MUST NOT** recreate K · **MUST NOT** modify K semantics · **MUST NOT** move K ownership。**P11 只负责 G/H/I/J。** |
| **理由 / 依据** | 实测：`tg_version_immutable` 已于 `0008`（`tool_versions`）与 `0011`（`agent_versions`）实现（`D-B15-03 = A`：统一名共用）。 |
| **影响范围** | K 的所有权与语义边界 |
| **实施阶段** | 既有阶段（非 P11） |
| **禁止** | 不得重建 / 修改语义 / 迁移所有权；不得把 K 计入 P11 交付面 |

---

# D-P11-07 — Tenant / Space / Authorization Boundary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-07` · Human Decision） |
| **决策** | P11 trigger **只保护已经明确的结构性跨表不变量**。**不得**把以下内容塞进 trigger：`cross-tenant authorization decision` · `ACL DENY/ALLOW evaluation` · `membership real-time authorization` · `resource classification policy` · `delegation semantics` · `authorization policy evaluation`。 |
| **关键区分（冻结原文）** | `G = subject existence` **不等于** `subject is authorized for this resource`。 |
| **归属** | **Tenant / Space / policy authorization 继续由 Authorization Layer 负责**（`D-AUTH-01..25`）。 |
| **理由 / 依据** | 指令 §3 本体论（`trigger ≠ authorization decision / ACL evaluation / policy engine`）；`B1-4` 的 F2/C2 亦均声明"structural integrity only / registry governance only，不做 authorization evaluation"。 |
| **影响范围** | G 的语义边界（**不追加同租户比较**）· 授权层职责边界 |
| **实施阶段** | P11（结构性不变量）；授权判定 → Authorization Layer |
| **禁止** | 不得在 trigger 内做租户级授权判定；不得以 `G` 的存在性校验替代授权；不得引入 RLS（`D-P10-15` 同向） |

---

# D-P11-08 — SECURITY DEFINER Policy

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-08` · Human Decision） |
| **决策** | P11 trigger functions：**`SECURITY INVOKER` = canonical**。**明确禁止引入 `SECURITY DEFINER`** —— 除非未来产生**新的独立 Human Decision**。 |
| **保留为实施期安全检查项** | `unqualified object resolution risk` · `search_path risk` · `privilege escalation risk`。 |
| **理由 / 依据** | 实测：全仓 `SECURITY DEFINER` = **0**（8 migration / 24 trigger / 15 function 全部默认 INVOKER），**无任何 `SET search_path`**。 |
| **影响范围** | 4 个 function 的安全属性 |
| **实施阶段** | P11 |
| **禁止** | **本轮不得引入任何 `SECURITY DEFINER` function**（非本轮实施面，政策本身即刻生效） |

---

# D-P11-09 — Recursion / Hidden DML Boundary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-09` · Human Decision） |
| **决策** | `J` 的隐藏 DML **保持限定于 ACL 生命周期失效**：`UPDATE resource_permissions SET inherited = true, expires_at = now()`。 |
| **J 的强约束** | **MUST NOT** UPDATE `subject_type_id` · **MUST NOT** UPDATE `subject_id` ⇒ **不得通过 J 人为触发 G**。 |
| **合并禁止** | `G = subject identity validation` 与 `J = agent ACL expiration` **二者不得合并**。**禁止增加 trigger chain**。 |
| **理由 / 依据** | 本轮分析：`G` 为 `UPDATE OF subject_type_id, subject_id`，J 的 SET 列表不含该两列 ⇒ 现状**不触发 G**；须把该结论固化为禁令。 |
| **影响范围** | J 的 SET 列表（可测断言）· 全局 trigger 链政策 |
| **实施阶段** | P11 |
| **禁止** | 不得扩展 J 的 SET 列表至 subject 列；不得合并 G/J；不得引入 trigger chain |

---

# D-P11-10 — P10 / P11 Ownership

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-10` · Human Decision） |
| **决策（严格固定）** | `P10 = Event / Audit persistence + tg_audit_immutable`；`P11 = G/H/I/J + remaining cross-table trigger constraints`。 |
| **推论** | **`L = OUT OF P11`**。 |
| **P11 禁止** | **不得** CREATE / MODIFY `audit_logs` trigger · **不得** CREATE / MODIFY `events` trigger · **不得** replace `tg_audit_immutable`。 |
| **特别确认** | **`tg_audit_immutable = P10-owned`**（承 `D-P10-11`，**未 supersede**）。 |
| **理由 / 依据** | `D-P10-11`；实测已挂载触发器的表集合**不含** `audit_logs` / `events` ⇒ P11 与 P10 在 trigger 面**零交叠**。 |
| **影响范围** | 两阶段的 trigger 面归属 |
| **实施阶段** | P11（仅 G/H/I/J） |
| **禁止** | 上述四项 P11 禁止逐条适用 |

---

# D-P11-11 — P11 / P12 Dependency

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-11` · Human Decision） |
| **决策** | P11 **不创建"顺手索引"**；索引属于 **P12**。P11 trigger implementation 所需的性能支持**若尚未存在** ⇒ **记录为 P12 dependency**；**不得**在 P11 migration 中私自加入 P12 index scope。 |
| **语义独立** | `P11 semantic correctness` **MUST NOT** depend on `P12 business semantics`。 |
| **理由 / 依据** | G/H/I/J 的查询路径已有 `ix_rp_subject`（`resource_permissions(subject_type_id, subject_id)`，**0007 / P06 已建**）⇒ 现状无缺口。 |
| **影响范围** | P11 迁移对象清单（index = 0） |
| **实施阶段** | 索引 → P12 |
| **禁止** | 不得在 P11 迁移内建索引；不得让 P11 语义正确性依赖 P12 |

---

# D-P11-12 — P11 / P13 Dependency

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-12` · Human Decision） |
| **决策** | G/H/I/J **必须在 P13 seed 之前完成挂载**。原因（冻结原文）：`trigger protection must exist before seed writes`。**P11 不承担任何 P13 seed。** |
| **特别禁止** | `insert acl_subject_types seed` · `insert bootstrap user` · `insert bootstrap role` · `insert agent subject seed`。 |
| **边界** | **P11 只建立 structural protection。** |
| **理由 / 依据** | `STEP1B_SCHEMA_DEPENDENCY.md:193`（`P00–P10 无 seed；P13 才有 seed`；trigger 必须先于 seed）· `STEP1B_SEED_STRATEGY.md:138` · `D-PLAT-11`（首个主体只经 P13）。 |
| **影响范围** | P11 迁移不含 seed（seed = 0） |
| **实施阶段** | P11（无 seed）；seed → P13 |
| **禁止** | 上述四类 INSERT 逐条禁止；不得"为便于自测"携带 seed |

---

# D-P11-13 — Inventory Gap `GAP-INV-1`

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-13` · Human Decision） |
| **决策** | 以下 **6 个已实现**的 trigger **不属于**历史 A–M canonical letter 清单：`tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` · `tg_platform_state_guard` · `tg_pm_bootstrap_gate` · `tg_agents_tenant_space_consistency`。 |
| **正式裁定** | **DO NOT** renumber A–M · **DO NOT** insert new letters · **DO NOT** move them into G/H/I/J · **DO NOT** reclassify them as P11 delivery。 |
| **保留** | **`GAP-INV-1` = supplementary inventory gap**。其含义 = **`historical inventory completeness issue`**，**而非** `missing implementation` —— 因为上述对象**已真实存在并已属于既有阶段**。 |
| **理由 / 依据** | 实测：6 者均已实现（0005 ×4 · 0006 ×2 中的 `tg_platform_state_guard`/`tg_pm_bootstrap_gate` · 0011 ×1）；`STEP1B_TRIGGER_INVENTORY.md` 成文早于 0005/0006/0011 ⇒ 属**清单完整性**问题。 |
| **影响范围** | trigger 清单的权威性与完整性表述（文档层） |
| **实施阶段** | 非实施项（治理登记） |
| **禁止** | 不得重排 letter；不得插入新 letter；不得迁入 G/H/I/J；不得重分类为 P11 交付 |

---

# D-P11-14 — Existing P3 Audit Claims

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P11-14` · Human Decision） |
| **决策** | 对于历史文档中「`role archive → trigger writes audit`」这一**陈述**：**NOT a P11 implementation requirement**。**正式保持：`trigger does NOT write audit`。** |
| **归属** | Audit persistence **属于 `P10` Event / Audit layer**。 |
| **P11 不新增** | 不新增 `role archive audit trigger` · 不新增 `ACL audit-writing trigger`。 |
| **历史描述处置** | **append-only clarification**；**不得改写既有历史 Decision 正文**。 |
| **理由 / 依据** | `CORE_DOMAIN_MODEL.md:263` 的该表述与触发器本体论冲突（`B1-4_DEPENDENCY.md:103` 已记为 **P3**）；且 `D-P10-11` 已把审计面归 **P10**。 |
| **影响范围** | 审计写入路径的唯一性（application/service + P10） |
| **实施阶段** | 非实施项（P11 不产生 audit 写入） |
| **禁止** | 不得在 P11 引入任何写 `audit_logs` 的 trigger；不得以该历史陈述为实施依据 |

---

# 附录 H — P11 冻结状态汇总（2026-09-25）

## H.1 计数

```text
D-P11 条目总数 = 14
FROZEN     = 14    （D-P11-01 … D-P11-14）
DEFERRED   = 0
SUPERSEDED = 0
unresolved OQ = 0  （OQ-P11-01 … OQ-P11-14 全部有明确 Human Decision）
```

## H.2 `CF-1` … `CF-4` 处置

| ID | 性质 | 处置 | 依据 |
|---|---|---|---|
| `CF-1` | 清单缺口（6 项已实现触发器不在 A–M） | **CLARIFIED** = `GAP-INV-1`，属 **inventory completeness issue**，**不是 implementation gap** | `D-P11-13` |
| `CF-2` | 既有 P3 陈旧 audit 陈述 | **CLARIFIED** —— 保持 **application/service + P10 audit boundary**；`trigger does NOT write audit` | `D-P11-14` |
| `CF-3` | H/I「P09 后」理由不充分 | **CLARIFIED** —— 正式表述：**`P09-after is an explicit phase freeze, not a dependency-derived conclusion`**；**不得据此重排 H/I** | `D-P11-13` / `D-P11-01` |
| `CF-4` | role 与 agent 生命周期机制不对称 | **INTENTIONAL / FROZEN** —— **不得通过 P11 强制统一机制** | `D-P11-05` |

## H.3 与既有冻结的关系（**无 supersession**）

```text
D-PLAT-09（P10 → P11 → P12 → P13 → Runtime） = FROZEN · NOT SUPERSEDED
D-PLAT-10（P11 纳入 G/H/I/J）                 = FROZEN · 未修订（本条区段为其兑现）
D-P10-01..18                                  = 原状不变（D-P10-11 的 L ownership 被显式继承）
D-AUTH-01..25                                 = 原状不变
D-AGENT-01..16                                = 原状不变
P09 四表 / 0010 / 0011 / 0012                 = 原状不变（本轮不触碰）
平台级 supersession 计数 = 1（D-B14-08）——【本组不新增】
```

## H.4 本轮 append-only clarification 落点

```text
STEP1B_TRIGGER_INVENTORY.md   → GAP-INV-1（6 项缺口登记）· CF-3（P09 后 = 显式阶段冻结）
CORE_DOMAIN_MODEL.md          → CF-2（role archive 写 audit 的陈旧陈述澄清）
两处均为【追加注记】，【未改写】任何既有结论 / 表格行 / 数值。
```

## H.5 一致性要求

`PLATFORM_DECISION_LOG.md` ↔ `P11_PREP_REPORT.md` ↔ `P11_DECISION_RESOLUTION.md` ↔
`P11_ACCEPTANCE_MATRIX.md` ↔ `STEP1B_TRIGGER_INVENTORY.md` ↔ `CORE_DOMAIN_MODEL.md` **语义必须一致**。

## H.6 不产生实施授权

`D-P11-01`…`D-P11-14` 的落盘与 `FROZEN` 状态**不等于**任何代码 / 迁移 / 数据库 / 配置授权的开启
（Charter §6、附录 D）。**`P11 / P12 / P13 IMPLEMENTATION = NOT AUTHORIZED`** ·
**`Runtime Implementation Gate = CLOSED`**。

## H.7 跨决策扫描结果（Charter §7）

```text
扫描面：本载体（Charter + D-PLAT-01..17 + 附录 A–H + D-AUTH-01..25 + D-AGENT-01..16 + D-P10-01..18）
        阶段日志（B1-4 / B1-5 / B1-6 / P09 / STEP1B_B1_2 / STEP1B_B1_3）
        架构面 / Schema 面 / 契约面（同附录 G.7）

结果：FROZEN vs FROZEN 冲突 = 0
      ACTIVE vs FROZEN 冲突 = 0
      SCHEMA vs DECISION 冲突 = 0
      条目级 supersession 新增 = 0
      陈旧描述 = CF-2 / CF-3（均已 append-only clarification）；CF-1 = 清单完整性登记
```

---

# P12 Canonical Model — `D-P12-01` … `D-P12-15`

> **来源**：`P12 — INDEXES` 的 READ-ONLY PREP（`P12_PREP_REPORT.md` · `P12_DECISION_RESOLUTION.md` ·
> `P12_ACCEPTANCE_MATRIX.md`，2026-09-25）与 `UAP P12 — HUMAN DECISION RESOLUTION`（2026-09-25）。
> **Human 于 2026-09-25 逐项裁定**：**15 项全部 `FROZEN`**（无 unresolved OQ）。
>
> **编号空间**：本组为**新建命名空间** `D-P12-NN`，与 `OQ-P12-01`…`OQ-P12-15` **一一对应（15 / 15）**。
> 冻结前全仓 `D-P12-` 命中 = **0** ⇒ 无编号冲突。
>
> **本轮不含任何实施**：无 `CREATE/ALTER/DROP INDEX` / migration / DDL / DML / code / test / config 变更；
> 本组条目**不产生任何实施授权**（Charter §6）。`P12 / P13 IMPLEMENTATION = NOT AUTHORIZED`。
>
> **编号对账（与 P11 不同：本轮无重映射）**：PREP 轮的 `OQ-P12-01`…`15` 与本轮 Human Decision
> **编号顺序完全一致**。仅 `OQ-P12-15` 的**侧重**由「机制边界」收敛为「**Scope Closure / No Opportunistic Indexing**」
> ——PREP 的机制边界内容（不得新增 `CHECK`/`FK`/`trigger`/seed）已被 `D-P12-15` 的「不包括」清单**涵盖**，
> 故**不构成重映射**，无需重排。

## 总表

| ID | OQ | 主题 | 状态 |
|---|---|---|---|
| `D-P12-01` | 01 | Canonical index inventory（以 PREP 实测 57/52/5 为基线；既有索引**不重建/不改名/不合并/不删除**） | **FROZEN** |
| `D-P12-02` | 02 | Query evidence standard（五级证据；四类理由**不得单独**构成依据；**GAP ≠ automatic CREATE INDEX**） | **FROZEN** |
| `D-P12-03` | 03 | Tenant / Space index policy（**禁机械前缀规则**；须有明确查询模式） | **FROZEN** |
| `D-P12-04` | 04 | UNIQUE semantics（**不得**以索引替换约束 / 以约束替换索引 / 改唯一语义；部分谓词保持） | **FROZEN** |
| `D-P12-05` | 05 | Partial index semantics（**partial index ≠ full FK coverage**；`partial-only = 5` 独立分类） | **FROZEN** |
| `D-P12-06` | 06 | `uq_tool_exec_idem` 语义不变；**不得**再建等价 idempotency index | **FROZEN** |
| `D-P12-07` | 07 | Agent / Tool lookup indexes（**仅限**有 PREP query evidence 者；**禁**因 Runtime 将至而批量预建） | **FROZEN** |
| `D-P12-08` | 08 | **Event / Audit indexes = P12**（`ix_events_*` 2 + `ix_audit_*` 5 = **7**）；**P10 不负责这些索引** | **FROZEN** |
| `D-P12-09` | 09 | P11-dependent reverse lookup（P11 语义 **MUST NOT** 依赖 P12；P12 索引 **MUST NOT** 改 P11 语义；**禁 blanket-create 24 GAP**） | **FROZEN** |
| `D-P12-10` | 10 | Partitioned table index policy（partition key / strategy / PK / retention **不变**） | **FROZEN** |
| `D-P12-11` | 11 | Redundancy / overlap（五类重叠检查；**overlap ≠ 可删**；删除/合并一律 `DEFERRED`） | **FROZEN** |
| `D-P12-12` | 12 | Index naming（沿用 canonical convention；命名漂移**只登记，不改名**） | **FROZEN** |
| `D-P12-13` | 13 | **Post-strategy FK coverage**（`GAP-INV-P12` = inventory/adjudication gap，**非**实施清单；24 GAP 逐项 `CREATE/DEFER/ALREADY COVERED/NOT REQUIRED`；19 项须标来源年代） | **FROZEN** |
| `D-P12-14` | 14 | **`ix_aimodels_capability` / `T-1` = DO NOT IMPLEMENT**（stale/mismatched design claim；**禁**偷换为 `GIN(capabilities)`） | **FROZEN** |
| `D-P12-15` | 15 | **P12 Scope Closure / No Opportunistic Indexing**（四项 canonical scope；六类"不包括"） | **FROZEN** |

> **计数**：`FROZEN` **15** · `DEFERRED` **0** · `SUPERSEDED` **0** · `unresolved OQ` **0**。

---

## P12 canonical invariants（本轮冻结后必须保持）

```text
implemented index objects        = 57（独立创建 52 + 内联 UNIQUE CONSTRAINT 隐式 5）
existing implemented indexes     = NOT recreated · NOT renamed · NOT merged · NOT deleted
P12 交付面                        = missing / additional indexes only
ix_events_* / ix_audit_*         = P12（共 7；表在 P10 建立）
uq_tool_exec_idem                = 保持（UNIQUE INDEX · predicate = idempotency_key IS NOT NULL）
partial-only                     = 5（独立分类，不得计入 full FK coverage）
FK coverage GAP                  = 24（per-gap 裁定，不得批量创建）
阶段顺序                          = P10 → P11 → P12 → P13 → Runtime
                                   （D-PLAT-09 未被 supersede，亦不得 supersede）
```

## 所有权边界（冻结原文）

```text
P10 = Event / Audit persistence（建 events / audit_logs 表 + tg_audit_immutable）
P12 = 对应查询索引（ix_events_* / ix_audit_*）

P10 建表            = YES
P12 建对应 index     = YES
⇒ P10 schema ownership + P12 index ownership（阶段分工，非阶段错误）
⇒ 不得把 P12 后置 index 解释成 P10 schema regression
```

## GAP-INV-P12 永久判定规则（2026-09-25 起永久生效）

```text
FK coverage GAP
    ↓
query evidence adjudication
    ↓
CREATE / DEFER / NOT REQUIRED

禁止：FK exists  →  automatic index
```

**附带义务**：24 GAP 中的 **19 个 post-strategy FK** 必须**单独标记来源年代**，
以防把「历史策略文档未 adjudicate」误写成「历史 schema defect」。

---

# D-P12-01 — Canonical Index Inventory

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-01` · Human Decision） |
| **决策** | 采用 PREP **实测** inventory 作为 P12 基线：**implemented index objects = 57**（独立创建 **52** + 隐式 UNIQUE **5**）。现有已实现索引 **NOT recreated / NOT renamed / NOT merged / NOT deleted**。P12 **只处理** `missing / additional indexes`。 |
| **理由 / 依据** | `P12_PREP_REPORT.md` §3 实测（逐 revision 与 migration docstring 逐项对账 ✅）· `OQ-P12-01` |
| **影响范围** | P12 的实施面界定与对账口径 |
| **禁止** | 不得把历史已存在 index 当作 P12 新建对象；不得借 P12 清理/改名既有对象 |

---

# D-P12-02 — Query Evidence Standard

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-02` · Human Decision） |
| **决策** | 每个新增 index **必须具备明确 query evidence**。有效证据优先级：`Frozen Decision → schema/query contract → explicit documented query → acceptance/test query → measured runtime requirement`。 |
| **理由 / 依据** | `STEP1B_INDEX_STRATEGY.md` 首部原则 · `OQ-P12-02` |
| **影响范围** | 全部 P12 候选索引的准入门槛 |
| **禁止** | 下列**不得单独**构成建索引理由：「future may query」·「database best practice」·「**FK exists**」·「performance safety」；**`GAP ≠ automatic CREATE INDEX`** —— 必须逐项 adjudicate |

---

# D-P12-03 — Tenant / Space Index Policy

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-03` · Human Decision） |
| **决策** | **不采用机械的 tenant/space 前缀规则**。仅在存在**明确查询模式**时建立 `tenant_id` / `space_id` / `tenant_id + space_id` / `tenant_id + status` / `tenant_id + created_at` 等组合索引。 |
| **理由 / 依据** | `INDEX_STRATEGY` §2「低基数列单列不建」· `OQ-P12-03` |
| **影响范围** | 多租户/多空间查询索引 |
| **禁止** | 不得通过 P12 引入新的 **authorization semantics** |

---

# D-P12-04 — UNIQUE Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-04` · Human Decision） |
| **决策** | 现有 `UNIQUE` / `UNIQUE INDEX` 语义**全部保持**。 |
| **理由 / 依据** | `D-B15-06 = A` · `D-B16-07 = A` · `D-P09-04 = A` · `D-P09-16（ND-04）`（表达式唯一 ⇒ unique INDEX；纯列唯一 ⇒ UNIQUE CONSTRAINT）· `OQ-P12-04` |
| **影响范围** | 全部唯一性对象 |
| **禁止** | `MUST NOT replace a UNIQUE constraint with an index` · `MUST NOT replace an index with a constraint` · `MUST NOT alter uniqueness semantics` · 已有部分唯一索引的 **predicate 必须保持** |

---

# D-P12-05 — Partial Index Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-05` · Human Decision） |
| **决策** | **Partial index 可以服务查询，但不能因为存在该 index 就声称完整覆盖对应 FK reverse lookup / integrity-support requirement。** PREP 已识别的 **`partial-only = 5`** 继续作为**独立分类**。 |
| **理由 / 依据** | `P12_PREP_REPORT.md` §4.3（`CF-5`）· `OQ-P12-05` |
| **影响范围** | FK 覆盖统计与验收口径 |
| **禁止** | 不得把 partial-only 误计为 **full FK coverage** |

---

# D-P12-06 — `uq_tool_exec_idem`

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-06` · Human Decision） |
| **决策** | **保留 `uq_tool_exec_idem`**；其现有 `UNIQUE` + `predicate = idempotency_key IS NOT NULL` 语义**不变**。 |
| **理由 / 依据** | `D-P09-04 = A`（FROZEN：部分唯一 ⇒ UNIQUE INDEX，不得伪装为 CONSTRAINT）· `OQ-P12-06` |
| **影响范围** | Tool 幂等锚点（`D-AGENT-08` 双层幂等的工具侧） |
| **禁止** | 不得在 P12 再创建一个**等价** idempotency index |

---

# D-P12-07 — Agent / Tool Lookup Indexes

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-07` · Human Decision） |
| **决策** | Agent / Tool 相关索引**仅限** `explicitly supported by PREP query evidence` 者可进入 P12 implementation candidate set。 |
| **理由 / 依据** | `OQ-P12-07` · `D-P12-02` |
| **影响范围** | Agent / Tool 生命周期操作性能 |
| **禁止** | 不得因为 **Agent Runtime 即将实现**就提前批量创建所有可能查询索引；**尤其不得**把 Runtime future query speculation 当作当前 P12 evidence |

---

# D-P12-08 — Event / Audit Indexes

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-08` · Human Decision） |
| **决策** | **`ix_events_*` = P12** · **`ix_audit_*` = P12**；共 **7**（`events` **2** + `audit_logs` **5**）。**这些索引属于 P12，即使对应表在 P10 建立。** |
| **理由 / 依据** | `P10_PREP_REPORT:132/326`（index dependency）· `P10 GP-6`（冻结索引清单）· `SEED_STRATEGY:138`（index(P12) 先于 seed）· `OQ-P12-08` |
| **影响范围** | `events` 2 条（`ix_events_dispatch` · `ix_events_tenant_type_time`）· `audit_logs` 5 条（`tenant_time` · `actor_time` · `resource` · `correlation` · `risk`） |
| **禁止** | **P10 不负责这些 indexes**；`P10 Event/Audit persistence ≠ P12 Index delivery` |

---

# D-P12-09 — P11-Dependent Reverse Lookup Indexes

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-09` · Human Decision） |
| **决策** | P11 trigger（`G/H/I/J`）所需的 reverse lookup **可以依赖 P12 提供性能索引**；对 FK / reverse-lookup candidate **逐项依据 PREP 的 query evidence adjudicate**。 |
| **理由 / 依据** | `D-P11-11`（P11 不建顺手索引）· `P11_ACCEPTANCE_MATRIX DEP-04`（复用既有 `ix_rp_subject`）· `OQ-P12-09` |
| **影响范围** | `resource_permissions` 相关查询路径 |
| **禁止** | `P11 semantics MUST NOT depend on P12` · `P12 index MUST NOT change P11 semantics` · **不得 blanket-create 24 个 GAP** |

---

# D-P12-10 — Partitioned Table Index Policy

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-10` · Human Decision） |
| **决策** | 对 P10 分区表（`events` · `audit_logs`），**P12 负责对应查询索引**；保持 **partition key / partition strategy / primary key / retention policy 全部不变**。 |
| **理由 / 依据** | `INDEX_STRATEGY:160`（索引建父表自动下推）· `B1-6 DC-4` · `P10 GP-4`（PK = `(id, occurred_at)`）· `P10 GP-7`（保留期）· `OQ-P12-10` |
| **影响范围** | 分区表的索引落点与运维 |
| **禁止** | 不得借由 P12 改造 **partition design** |

---

# D-P12-11 — Redundancy / Overlap

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-11` · Human Decision） |
| **决策** | 新 index 必须经过：`exact duplicate` · `left-prefix overlap` · `predicate overlap` · `existing query coverage` · `constraint-support overlap` 五项检查。 |
| **理由 / 依据** | `INDEX_STRATEGY` §2（共享前缀可接受、不合并）· `OQ-P12-11` |
| **影响范围** | 新增索引的准入与对账 |
| **禁止** | `overlap ≠ permission to delete existing index`；任何历史 index 删除/合并 **一律 `DEFERRED`**，除非产生**独立** Human Decision |

---

# D-P12-12 — Index Naming

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-12` · Human Decision） |
| **决策** | 采用**现有 canonical naming convention**，优先沿用 `ix_<semantic_name>` / `uq_<semantic_name>`。现有命名漂移 **只登记，不在 P12 Freeze 中改名**。 |
| **理由 / 依据** | `INDEX_STRATEGY §4` · `P12_PREP_REPORT` §7.3（`CF-3`）· `OQ-P12-12` |
| **影响范围** | 新增对象命名 |
| **禁止** | 不得在 P12 内执行 **index renaming cleanup**；漂移对：`ix_rp_permission` ↔ `ix_role_permissions_permission` · `ix_tm_role` ↔ `ix_tenant_memberships_role`（**canonical 实现名 = 后者**） |

---

# D-P12-13 — Post-Strategy FK Coverage

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-13` · Human Decision） |
| **决策** | **`GAP-INV-P12` 正式认定为 inventory / adjudication completeness gap**，**不是** automatic implementation list。PREP 实测 **54 FK**（**25** full coverage · **5** partial-only · **24** GAP）必须在本阶段 Implementation Contract 中**逐项列明** `CREATE / DEFER / ALREADY COVERED / NOT REQUIRED`。 |
| **理由 / 依据** | `INDEX_STRATEGY §3:202`（补充索引进入 P12）· `P09_DECISION_LOG:248`（P09 显式移交）· `P12_PREP_REPORT` §4.4 · `OQ-P12-13` |
| **影响范围** | P12 实施清单的**唯一**生成路径 |
| **禁止** | 不得以「FK reverse lookup」四字**整体批量创建**；其中 **19 个 post-strategy FK** 必须**单独标记来源年代**，防止把历史策略文档缺失误写成历史 schema defect |

---

# D-P12-14 — `ix_aimodels_capability` / `T-1`

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-14` · Human Decision） |
| **决策** | **`DO NOT IMPLEMENT ix_aimodels_capability`**。理由：① 文档引用 `capability`，**实际列 = `capabilities` JSONB**；② 既有设计**明确排除** JSONB GIN；③ 现行 predicate / column reference **不是有效的 canonical implementation target**。⇒ **`T-1 = stale / mismatched design claim`**。 |
| **理由 / 依据** | `0010` docstring（`T-1 = DEFERRED`）· `B1-6_DECISION_LOG:436`（`T-1` / `O-E`）· `INDEX_STRATEGY §2`（jsonb GIN 不建）· `OQ-P12-14` |
| **影响范围** | `ai_models` 的 capability 枚举查询（**无当前有效实现目标**） |
| **禁止** | 不得通过 P12 **偷换**为 `GIN(capabilities)`；不得发明其他 JSONB index |
| **append-only clarification** | *the historical `ix_aimodels_capability` proposal is not a P12 implementation target until a separate schema/query contract explicitly defines a valid queryable key/path.* |

---

# D-P12-15 — P12 Scope Closure / No Opportunistic Indexing

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-25 · `OQ-P12-15` · Human Decision） |
| **决策** | **P12 canonical scope**：① Frozen P12 indexes ② Explicitly evidenced Event/Audit indexes ③ Explicitly adjudicated FK reverse-lookup indexes ④ Explicitly evidenced ACL / Agent / Tool query indexes。 |
| **理由 / 依据** | `OQ-P12-15` · `D-P12-02` · `INDEX_STRATEGY` 首部原则 |
| **影响范围** | P12 的**封闭**交付面 |
| **禁止（六类"不包括"）** | 「just in case」indexes · future Runtime speculation · future business-module speculation · authorization policy indexes **without query evidence** · trigger-generated performance guesses · schema redesign · index renaming cleanup |

---

# P13 Canonical Model — `D-P13-01` … `D-P13-14`

> **来源**：`P13 — SEED / BOOTSTRAP` 的 READ-ONLY PREP（`P13_PREP_REPORT.md` · `P13_DECISION_RESOLUTION.md` ·
> `P13_ACCEPTANCE_MATRIX.md`，2026-09-26）· Freeze Gate 部分裁定登记（附录 **I.10**，2026-09-26）·
> Decision Completion Evidence（`P13_DECISION_COMPLETION_EVIDENCE.md`，2026-09-26）·
> Human Decision Sheet（`P13_HUMAN_DECISION_SHEET.md`）与 Exact Extraction（`P13_HUMAN_DECISION_EXTRACTION.md`，2026-09-26）·
> 以及本轮 `UAP — P13 HUMAN DECISION / DECISION RESOLUTION EXECUTION`（2026-09-26 最终架构裁定）。
> **Human 于 2026-09-26 逐项裁定**：**14 项全部 `FROZEN`** —— 11 项由本轮架构裁定解决，3 项**继承**既有 `FROZEN`（`OQ-P13-03/06/13`，未重裁）。
>
> **编号空间**：本组为**新建命名空间** `D-P13-NN`，与 `OQ-P13-01`…`OQ-P13-14` **一一对应（14 / 14）**。
> 冻结前全仓 `D-P13-` 命中 = **0** ⇒ 无编号冲突。
>
> **编号重映射（显式登记 · 不得静默）**：本轮 Human 指令 §3 以「`OQ-P13-02` — manage / write mapping」为标题下发的裁定，
> 其**内容**对应 `P13_HUMAN_DECISION_SHEET.md` 中 `OQ-P13-01` 的**第 2 问**（`manage`/`write` 映射），
> **并非** SHEET 的 `OQ-P13-02`（System role ownership）。
> ⇒ 处置：该映射裁定登记于 **`D-P13-01`**（作为 `OQ-P13-01` Q2 的闭项，见其「子问题闭项」字段）；
> SHEET 的 `OQ-P13-02`（System role ownership）依 Human 指令 **§0 的授权**做**派生裁定**，登记为
> **`D-P13-02`（DELEGATED RESOLUTION）** —— 其依据**全部**来自本轮已给定决策（`D-P13-05`）与既有冻结事实
> （0005 幂等先例 / R2 / 指令 §15 边界），**未新增任何设计**，且**可被 Human 显式否决并重述**。
>
> **本轮不含任何实施**：无 `CREATE/ALTER/DROP` · 无 migration · 无 DDL / DML / seed INSERT · 无 code / test / config 变更。
> 本组条目**不产生任何实施授权**（Charter §6）。`P13 IMPLEMENTATION = NOT AUTHORIZED` · `Runtime = NOT AUTHORIZED`；
> `0016_p13_seed.py` = **MUST NOT EXIST**（须再次取得显式 `P13 IMPLEMENTATION AUTHORIZATION`）。

## 总表

| ID | OQ | 主题 | 状态 |
|---|---|---|---|
| `D-P13-01` | 01 | permissions canonical seed list = **12 项**（取代 13 项草稿）· `manage→admin` · `write→update` · 排除 `system.*` · **无 deny 行** | **FROZEN** |
| `D-P13-02` | 02 | System role ownership（`platform_admin` 归 0005，P13 仅校验存在；tenant/space 四角色因无 bootstrap tenant ⇒ P13 **零播种**） | **FROZEN**（DELEGATED） |
| `D-P13-03` | 03 | `acl_subject_types` seed 走 **migration-controlled path**；runtime INSERT = FORBIDDEN；C2 保持 | **FROZEN**（继承） |
| `D-P13-04` | 04 | **仅注册** `agent` subject type；不得创建 agents / agent_versions / agent_permissions / tool_executions | **FROZEN** |
| `D-P13-05` | 05 | **不创建 bootstrap tenant**（`tenants = 0`）；不得虚构 slug / name / owner / administrator identity | **FROZEN** |
| `D-P13-06` | 06 | identity row = allowed；plaintext password / credential secret = forbidden（可登录性由 onboarding 提供） | **FROZEN**（继承） |
| `D-P13-07` | 07 | P13 = **0** `platform_memberships`；首个平台管理员只经既有 bootstrap CLI / 状态机 | **FROZEN** |
| `D-P13-08` | 08 | **不创建** `tenant_memberships` / `memberships` | **FROZEN** |
| `D-P13-09` | 09 | seed 顺序 = SEED_STRATEGY §1 十步序为**唯一拓扑**（step 4 / 6 / 9 因本轮决策为空操作） | **FROZEN** |
| `D-P13-10` | 10 | 幂等 = 既有 precedent（`WHERE NOT EXISTS` / 冲突即**显式失败**）；**禁**统一 `ON CONFLICT DO NOTHING` | **FROZEN** |
| `D-P13-11` | 11 | seed 在 **39 triggers 全部启用**下执行；**禁** DISABLE / DROP / ALTER TRIGGER 与绕过 C2 | **FROZEN** |
| `D-P13-12` | 12 | 降级 = **FAIL-CLOSED**；**禁** `DELETE WHERE key IN (...)`；**禁**新增 ownership marker 列 | **FROZEN** |
| `D-P13-13` | 13 | credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0 | **FROZEN**（继承） |
| `D-P13-14` | 14 | runtime 数据保护 = natural-key filtering + FK protection + `D-P13-12` fail-closed + pre-downgrade 验证；**不新增** schema marker | **FROZEN** |

> **计数**：`FROZEN` **14** · `DEFERRED` **0** · `SUPERSEDED` **0** · `unresolved OQ` **0**。
> 其中 **3** 项（`D-P13-03` / `06` / `13`）为**继承** Freeze Gate 既有 `FROZEN`（未重裁、未改写）；
> **1** 项（`D-P13-02`）为 **DELEGATED RESOLUTION**；其余 **10** 项为本轮 Human 架构裁定。

---

# D-P13-01 — Permissions Canonical Seed List

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-01` · **`CUSTOM DECISION`** · 架构裁定） |
| **Human 决策原文（定性）** | 「**`CUSTOM DECISION`**」·「**不接受原始 13 项草稿直接作为 seed**」 |
| **决策** | 采用**确定性的 12 项** canonical permission seed；全部满足 `action ∈ canonical vocabulary` · `key` = lower-case canonical form · `is_system = true` · `effect = allow`：`tenant.read` · `tenant.admin` · `space.read` · `space.admin` · `member.read` · `member.admin` · `resource.read` · `resource.update` · `resource.delete` · `agent.execute` · `tool.execute` · `audit.read` |
| **子问题闭项（SHEET §1 五问）** | **Q1** = 采用本轮 12 项清单（**非**草稿 13 项）· **Q2** = `manage → admin`、`write → update`（**不再标记 OPEN**；Human 明确架构映射）· **Q3** = `system.*` **排除** · **Q4** = **不创建 deny 行** · **Q5** = **不新增** `resource_type` DB 词表 / `CHECK`（**派生闭项**：由「P13 零 schema 变更」原则与既有 `ck_permissions_*` 承载；如 Human 要求 DB 层词表须另行下发决策） |
| **明确排除（不得 seed）** | `system.*` · `tenant.manage` · `space.manage` · `member.manage` · `resource.write` · **任何 deny permission** |
| **理由 / 依据** | `system.*` 仅是形状占位、不是具体 permission · `manage` 映射为 `admin` · `write` 映射为 `update` · deny 无权威分配清单**不得凭空创建** · P13 **不建立 deny policy** · P13 保持最小、明确、可审计的 platform permission vocabulary · `EVID` §1.2/§1.3 词表比对证据 |
| **影响范围** | `0016_p13_seed` 的 permissions 段（**12 行**）及其确定性 `role_permissions` 绑定 |
| **禁止** | 建立第二套 Action vocabulary · 修改 `ck_permissions_action_canonical` · 新增 action 表 · 为通过 CHECK 而**偷改 action** · 由 13 项草稿直接 seed · 创建 deny 行 |

---

# D-P13-02 — System Role Ownership

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-02` · **DELEGATED RESOLUTION**（Human 指令 §0 授权）） |
| **决策** | ① `platform_admin` 所有权**维持 0005**（`_seed_system_roles()` 已幂等播种）⇒ P13 **仅校验存在，不重复播种**；② `tenant_admin` / `tenant_member` / `space_admin` / `space_member` 为**按既有 tenant / space 行补种**的既有机制，因 `D-P13-05`（不创建 bootstrap tenant）⇒ **P13 零播种**，留待 onboarding / Runtime 在真实 tenant / space 建立后补种；③ 既有 migration-controlled 行**不得**重复纳入 P13。 |
| **理由 / 依据** | Human 指令 §15「EXPECTED P13 SEED BOUNDARY」：`roles: existing platform role ownership respected` · `tenant/space role structures only where valid baseline requires` · `D-P13-05`（`tenants = 0`）· 0005 `WHERE NOT EXISTS` 幂等先例 · R2 幂等键 = `scope+ownership+key` |
| **影响范围** | `0016_p13_seed` 的 roles 段（**0 行新增**）与 roles 校验步骤 |
| **禁止** | 重复播种 `platform_admin` · 为不存在的 tenant / space 预建角色 · 绕过 0005 所有权 |
| **派生说明（双向披露）** | 本项为指令 **§0 授权**下的**派生裁定**：依据**全部**来自本轮已给定决策与既有冻结事实，**未新增设计**。**若与 Human 原意不符，请显式否决并重述**。 |
| **编号注记** | Human 指令 §3 标题编号「`OQ-P13-02`」对应 SHEET `OQ-P13-01` 的 **Q2**（manage / write 映射），已登记于 `D-P13-01`；本项为 SHEET 的 `OQ-P13-02`（System role ownership）。 |

---

# D-P13-03 — Registry Controlled Path

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 Freeze Gate · **本轮继承**，未重裁、未改写） |
| **决策** | `acl_subject_types` seed **必须**走 **migration-controlled path**；**runtime INSERT = FORBIDDEN**；**C2** registry protection（`tg_acl_subject_types_protect`）**必须保持** —— 不得删除、不得绕过、不得长期关闭。 |
| **理由 / 依据** | `OQ-P13-03`（Freeze Gate 裁定）· 附录 I.10 · C2 为数据层真实防线 |
| **影响范围** | registry 三行 seed（`user` / `role` / `agent`）的写入路径 |
| **禁止** | 走普通 runtime path 写 registry · 移除 / 绕过 / 长期关闭 C2 · 以 seed 为由放宽 registry 保护 |

---

# D-P13-04 — Agent Subject Registration Only

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-04` · **`ACCEPT OPTION A`**） |
| **决策** | **只注册** `acl_subject_types.key = agent`；**不创建** `agents` / `agent_versions` / `agent_permissions` / `tool_executions`；**不得**创建 demo Agent。 |
| **理由 / 依据** | Agent 是 Runtime / Domain object，**不是** Platform baseline 的虚构演示数据 · `EVID` §3.2 · `ck_acl_subject_types_whitelist` 已含 `'agent'` |
| **影响范围** | registry 第 3 行；G（`tg_acl_subject_exists`）的合法分派目标集合 |
| **禁止** | 创建实际 Agent / Version / Permission / Run · 播种演示业务数据 |

---

# D-P13-05 — No Bootstrap Tenant

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-05` · **`ACCEPT OPTION B`**） |
| **决策** | P13 **不创建** bootstrap tenant ⇒ `P13 seed: tenants = 0`；**不得虚构** tenant slug / tenant name / owner / tenant administrator identity；既有 tenant schema、tenant FK、tenant-level role infrastructure **保留不变**。 |
| **理由 / 依据** | Tenant 是 **Runtime / onboarding domain data**，不应由 Platform migration 制造一个「真实租户」；亦**避免 P13 downgrade ownership 问题进一步扩大**（与 `D-P13-12` 联动） |
| **影响范围** | `0016_p13_seed` 的 tenant 段 = **空操作**；`D-P13-08` 的连带后果 |
| **禁止** | 播种首租户行 · 虚构 slug / name / owner / administrator · 借 bootstrap 名义引入业务数据 |
| **登记后果** | 本项为 `OQ-P13-05` 的 **Option B**，其既有 Engineering Impact 已载明「B ⇒ `D-PLAT-11` 需重新解释」⇒ 该解释义务登记为 **P13 实施轮的前置澄清项**（见附录 `J.3`），本轮**不改写、不 supersede** `D-PLAT-11`。 |

---

# D-P13-06 — Identity / Credential Boundary

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 Freeze Gate · **本轮继承**，未重裁、未改写） |
| **决策** | create/bootstrap **identity row = allowed**；**plaintext password / credential secret = forbidden**；「首个可登录主体」与「P13 创建主体记录」**必须区分**；登录能力由后续 onboarding / runtime credential establishment 提供。 |
| **理由 / 依据** | `OQ-P13-06`（Freeze Gate 裁定）· 附录 I.10 · R4/R5 |
| **影响范围** | 凭据面边界（P13 与 onboarding 的职责切分） |
| **禁止** | 明文密码 · 凭据 secret · 伪造密码 · 以 P13 代替 onboarding 建立可登录性 |

---

# D-P13-07 — Platform Membership Remains Bootstrap-CLI Owned

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-07` · **`ACCEPT OPTION A`**） |
| **决策** | 严格维持既有 R4/R5：`P13 = 0 platform_memberships`；首个平台管理员**必须**通过既有 bootstrap CLI / 状态机路径产生。 |
| **理由 / 依据** | R4/R5（单事务：插首行 PM → 翻转 `platform_state` → audit `platform.admin.bootstrap`）· `tg_pm_bootstrap_gate` / `tg_pm_last_admin` · PM 现状 0 行 |
| **影响范围** | `0016_p13_seed` 的 PM 段 = **零写入** |
| **禁止** | P13 INSERT `platform_memberships` · 绕过 `tg_pm_bootstrap_gate` · 绕过 `platform_state` · 关闭 bootstrap protection · 伪造首个管理员 |

---

# D-P13-08 — No Tenant / Space Membership Seeding

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-08` · **`ACCEPT OPTION B`**） |
| **决策** | P13 **不创建** `tenant_memberships` / `memberships`。 |
| **理由 / 依据** | 本轮已决定 `D-P13-05`（P13 不创建 bootstrap tenant）与「P13 不创建真实 user / administrator identity」⇒ **不应产生没有真实主体与真实 container 的 membership**；Runtime / onboarding 在真实 tenant、space、identity 建立后完成绑定；这比制造「半成品管理员关系」更符合 UAP Platform Base 的边界 |
| **影响范围** | `0016_p13_seed` 的 membership 段 = **空操作**（含 SEED_STRATEGY §1 的 step 6 / 9） |
| **禁止** | 播种无主体 / 无容器的 membership · 以 membership 之名引入半成品管理员关系 |

---

# D-P13-09 — Seed Ordering (Single Canonical Topology)

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-09` · **`ACCEPT OPTION A`**） |
| **决策** | 使用既有 `SEED_STRATEGY` §1 顺序作为**唯一实施拓扑**：`1 registry` → `2 permissions` → `3 roles 校验` → `4 tenant` → `5 tenant roles` → `6 tenant_membership` → `7 space` → `8 space roles` → `9 membership` → `10 role_permissions`。依本轮决策：**step 4 tenant = no seed** · **step 6 tenant_membership = no seed** · **step 9 membership = no seed** —— 实施阶段**只执行实际需要的步骤**。 |
| **理由 / 依据** | `SEED_STRATEGY` §1 十步序 · PREP 静态依赖图**无环** · **无 deferred FK**（实测 `condeferrable=false`）· 唯一适配点 = C2 受控路径（`D-P13-03`） |
| **影响范围** | `0016_p13_seed` 的 upgrade 内部顺序 |
| **禁止** | 因部分 seed 被裁掉而**自行重新设计另一套拓扑** · 跳过 roles 校验 · 变更 C2 受控路径 |

---

# D-P13-10 — Idempotency Semantics

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-10` · **`ACCEPT OPTION A`**） |
| **决策** | 严格保持既有 migration precedent：`registry` = `WHERE NOT EXISTS` · `permissions` = `WHERE NOT EXISTS` · `membership / role_permissions` = **conflict = explicit failure**。 |
| **理由 / 依据** | `SEED_STRATEGY` §6 · R2（幂等键 = `scope+ownership+key`；**重复冲突即失败，不 upsert**）· 0005 / 0006 先例 · `uq_permissions_key` / `uq_acl_subject_types_key` 在位 |
| **影响范围** | `0016_p13_seed` 的全部 INSERT 语义 |
| **禁止** | 统一改成 `ON CONFLICT DO NOTHING` · 使用 upsert 覆盖已有 Runtime 数据 · 静默吞掉 ownership / definition conflict |
| **目标** | 重复执行 = **deterministic**；错误数据 = **fail loudly** |

---

# D-P13-11 — Trigger Interaction (All Triggers Enabled)

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-11` · **`ACCEPT OPTION A`**） |
| **决策** | P13 seed **必须**在既有 **39 triggers 保持启用**的状态下执行；实施阶段**必须逐触发器验证** seed interaction。 |
| **理由 / 依据** | `D-P11-12`（triggers 先于 seed）· G/H/I/J 对 P13 seed 零副作用（实测语义）· 数据层词表与形状校验对 seed 行天然满足 |
| **特别确认（继续作为数据层真实防线存在）** | C2 registry protection · B/C/D/E/F/F2 · tenant / space membership scope triggers · permissions canonical action `CHECK` · acl subject whitelist |
| **影响范围** | 实施阶段的验证面（每触发器行为测试） |
| **禁止** | `DISABLE TRIGGER` · `DROP TRIGGER` · `ALTER TRIGGER` · 绕过 C2 · **临时关闭保护后再恢复** |

---

# D-P13-12 — Downgrade Ownership Protection (FAIL-CLOSED)

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-12` · **`ACCEPT OPTION C`** · 原 BLOCKING 项已解除） |
| **决策** | 采用 **FAIL-CLOSED**：P13 downgrade **不允许**在无法可靠证明 seed ownership 时执行潜在 DELETE。规则：`若发现无法证明数据库处于 P13 clean baseline ⇒ RAISE / FAIL ⇒ 整个 downgrade 回滚 ⇒ 0 DELETE`。 |
| **允许 downgrade 的前提（三者须同时成立）** | ① 没有 runtime 数据超出已定义 seed baseline；② 没有无法解释的 dependent rows；③ 没有可能与 runtime 数据混用的 ownership ambiguity |
| **理由 / 依据** | `EVID` §2.0 实测 schema 证据：`is_system` / `audit_logs` / FK RESTRICT / natural key **均不能单独证明**「该行一定由 P13 创建」· 全库无 `seed_batch` / `migration_owned` 行级标记 · 与 UAP **可恢复性原则**同向 |
| **影响范围** | `0016_p13_seed` 的 `downgrade()` 实现语义（本组冻结**不包括**任何实现） |
| **禁止** | 以 `DELETE WHERE key IN (...)` 作为**默认**降级行为 · 因「理论上这些 key 是 seed」而删除 · **新增** `seed_batch` / `migration_owned` / ownership marker column（超出 P13 当前 scope） |
| **降级语义（最终）** | `clean baseline: allow downgrade` · `runtime / ownership ambiguity: fail closed` · `never: guess ownership / delete uncertain rows` |

---

# D-P13-13 — Zero Credential Seeding

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 Freeze Gate · **本轮继承**，未重裁、未改写） |
| **决策** | P13 seed：`credentials = 0` · `plaintext secrets = 0` · `fabricated passwords = 0`；任何需要 secret 的 onboarding **必须**走后续安全流程。 |
| **理由 / 依据** | `OQ-P13-13`（Freeze Gate 裁定）· 附录 I.10 · `SEED_STRATEGY` §6 / R4 |
| **影响范围** | 凭据与 secret 面（P13 = 零） |
| **禁止** | 明文 / 编码 / 可逆形式的凭据 · 环境变量注入初始密码 · 伪造密码 |

---

# D-P13-14 — Runtime-Created Data Protection

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · `OQ-P13-14` · **`ACCEPT OPTION A`**） |
| **决策** | **不增加**新的 schema marker；保护由以下机制**共同**形成：`natural-key filtering` + `existing FK protection` + `D-P13-12 fail-closed` + `pre-downgrade verification`。 |
| **理由 / 依据** | `EVID` §2.0（无现成行级标记）· `D-P13-12`（fail-closed 承载保护）· P13 零 schema 变更边界 |
| **影响范围** | runtime 数据保护策略（**不新增 schema 对象**） |
| **禁止** | P13 新增 `seed_batch` / `migration_owned` / `seed_origin` / ownership metadata column —— **除非未来另开正式 Decision / Design scope** |

---

# D-P13-15 — B-1 Amendment（Trust Boundary Precondition）

> **来源**：`UAP — P13 B-1 HUMAN DECISION FINAL DIRECTION`（2026-09-26 Human 裁定）·
> `P13_B1_HUMAN_DECISION_AMENDMENT.md`（PROPOSED · 未冻结 → 已获正式裁定回应）·
> `P13_B1_HUMAN_DECISION_FINAL_DIRECTION.md`。登记于附录 **K**。

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-26 · **B-1 FINAL DIRECTION** · Human **逐字提供**文本） |
| **决策** | **`B-1 Amendment`** —— `Purpose`：**允许未来受信 migration context 建立 system registry seed，但前提是数据库身份隔离已经成立。** |
| **理由 / 依据** | Human 裁定：`O-1 = REJECT` · `O-4 = REJECT` · `O-3 = ACCEPT AS ARCHITECTURAL DIRECTION` · `O-2 = DEFERRED`。核心原因：当前 UAP 数据库**不存在** migration/runtime 可区分信任边界（`runtime = uap(superuser)` · `migration = uap(superuser)`）⇒ GUC / `application_name` / session variable / temporary flag **均不得作为安全机制**（实测复验 `FD-1`…`FD-7`）。因此执行顺序调整为 `OPEN-P10-1 → P13 B-1 Amendment → P13 Implementation`。 |
| **影响范围** | ① 本记录**不授权**任何实施（见「禁止」）；② 为未来的 `P13 B-1 Amendment` 确立**唯一前置**＝数据库身份隔离成立（`OPEN-P10-1`）；③ `D-P13-03` 的「migration-controlled path」**核心目标保持**，其"受信主体"的定义待 `OPEN-P10-1` 冻结后形式化；④ `D-P13-11` 的禁止字段**保持原样**（`O-1` 被 REJECT ⇒「禁临时关闭保护后再恢复」不被 amend）。 |
| **禁止** | **`Does not authorize`（逐字）**：`0016 migration` · `seed INSERT` · `C2 修改` · `runtime permission expansion`。并禁止：`DISABLE TRIGGER` · `session_replication_role` · 普通 GUC 信任 · `application_name` 判断 · runtime 可获得 migration 权限；不得在 `OPEN-P10-1` 冻结前推进 `P13` 实施。 |

> **登记口径声明（如实披露）**：Human 指令 §6 的标题字样为「`D-P13-15` 建议新增」，其块内**逐字给出** ID / 标题 / `Purpose` / `Does not authorize`；
> 本轮轮次名为 `HUMAN DECISION FINAL DIRECTION`且 §1 为「Human Decision 裁定」⇒ 本登记为该 FINAL DIRECTION 的**忠实转录**，status 取 `FROZEN`。
> 本记录**可被 Human 显式否决或重述**（append-only 载体）；若 Human 本意是「待批 / `PROPOSED`」，须**显式登记降级**，**Bot 不自行降级**。
>
> **不修改**：`D-P13-01…14` 正文 · `D-P13-11` 禁止字段 · `D-PLAT-09` · `D-PLAT-11` · `D-P10-13` · 附录 I/J。**supersession 新增 = 0**。

---

# OPEN-P10-1 Canonical Model — `D-OP101-01` … `D-OP101-14`

> **来源**：`OPEN_P10_1_DECISION_RESOLUTION.md`（REVISION 2 · 请求单 · 全程保持 `PENDING` 时点快照，**未被回填**）·
> `OPEN_P10_1_HUMAN_DECISION_INPUT.md`（空白模板 → §8 输入登记）·
> `OPEN_P10_1_HUMAN_DECISION_RECORD.md`（**收据与登记** · `DECISION RECEIPT · REGISTERED`）·
> Human 提交 `UAP — OPEN-P10-1 HUMAN DECISION`（2026-09-27）·
> 写入授权 `UAP — OPEN-P10-1 DECISION CARRIER WRITE AUTHORIZATION`（2026-09-27 · `DECISION CARRIER WRITE AUTHORIZATION = AUTHORIZED`）。
>
> **编号空间**：本组为**新建命名空间** `D-OP101-NN`，与 `OQ-OP101-01`…`OQ-OP101-14` **一一对应（14 / 14）**。
> 冻结前全仓 `D-OP101-` 命中 = **0**（实测）⇒ 无编号冲突。
>
> **本轮性质 = 决策冻结登记（DECISION FREEZE）**：仅登记 14 项 Human Decision、2 项 `CUSTOM DECISION` **原文**、
> 冻结决议摘要、相关不变量与前置关系。**`DECISION CARRIER WRITE AUTHORIZATION` ≠ `IMPLEMENTATION AUTHORIZATION`**（Human 明文）。
> **`OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED`** · **`P13 IMPLEMENTATION = NOT AUTHORIZED`**。
>
> **不修改**：任何既有 `D-*` 正文 · 任何已冻结历史决策（**不得删除 / 重写 / supersede**）；
> `D-P10-13` 仅**指针式 append**（见其记录下方指针行）。**supersession 新增 = 0**。
> 本组条目**不产生任何实施授权**（Charter §6）。`0016` = **ABSENT** · `0017` = **ABSENT**。
> 本轮**未**执行 `CREATE ROLE` / `GRANT` / `REVOKE` / `ALTER ROLE` / `ALTER OWNER` / `CREATE|ALTER|DROP FUNCTION` /
> `C2 修改` / `0007 修改` / `DDL` / `DML` / `seed INSERT` / migration 创建 / runtime 修改 / `alembic upgrade|downgrade` / `commit` / `tag` / `push`。

## 总表

| ID | OQ | 主题 | Human Decision | 状态 |
|---|---|---|---|---|
| `D-OP101-01` | 01 | 角色拓扑 | `ACCEPT OPTION D` ⇒ **`RM-D`** | **FROZEN** |
| `D-OP101-02` | 02 | migration identity 的权限等级 | `ACCEPT OPTION A` ⇒ **必须 `NOSUPERUSER`** | **FROZEN** |
| `D-OP101-03` | 03 | revision 编号归属 | **`CUSTOM DECISION`**（`0016` 归 `OPEN-P10-1`；P13 seed = `0017_p13_seed`，不授权创建） | **FROZEN** |
| `D-OP101-04` | 04 | 角色创建者 | `ACCEPT OPTION C` ⇒ **deployment / orchestration / operations 预置** | **FROZEN** |
| `D-OP101-05` | 05 | C2 判据形态 | **`CUSTOM DECISION`**（**`CP-F`**：`current_user` ∧ `session_user` 合取；**批准 `CC-7`**） | **FROZEN** |
| `D-OP101-06` | 06 | 是否同时落地 `uap_readonly` | `ACCEPT OPTION B` ⇒ **DEFER** | **FROZEN** |
| `D-OP101-07` | 07 | runtime GRANT 矩阵范围 | `ACCEPT OPTION C` ⇒ **minimum required set** | **FROZEN** |
| `D-OP101-08` | 08 | 「runtime 不持 DDL」是否由 DB 层强制 | `ACCEPT OPTION C` ⇒ **DB enforced + positive assertion + negative probe** | **FROZEN** |
| `D-OP101-09` | 09 | 既有 156 对象的所有权 | `ACCEPT OPTION B` ⇒ **full ownership transition** | **FROZEN** |
| `D-OP101-10` | 10 | 配置 / 环境面承载双身份 | `ACCEPT OPTION A` ⇒ **independent migration/runtime keys + explicit resolution chain** | **FROZEN** |
| `D-OP101-11` | 11 | 测试基建与集群级角色 | `ACCEPT OPTION A` ⇒ **testkit role provisioning + dual DSN fixtures** | **FROZEN** |
| `D-OP101-12` | 12 | downgrade 语义 | `ACCEPT OPTION B` ⇒ **REVOKE and retain cluster role** | **FROZEN** |
| `D-OP101-13` | 13 | 「身份隔离已成立」的机读判据 | `ACCEPT OPTION C` ⇒ **topology landed + complete eight-test proof** | **FROZEN** |
| `D-OP101-14` | 14 | 既有守卫 rationale 的同步口径 | `ACCEPT OPTION A` ⇒ **update rationale while retaining existing assertions** | **FROZEN** |

> **计数**：`FROZEN` **14** · `DEFERRED` **0** · `SUPERSEDED` **0** · `unresolved OQ` **0**；
> `PENDING` **0** · `KEEP OPEN` **0** · `NEED MORE EVIDENCE` **0**；`CUSTOM DECISION` **2**（`D-OP101-03` / `D-OP101-05`）。
> `CF-1` = **RESOLVED**（`CC-7` 与本组冻结均由 `D-OP101-05` 明文承载）。**supersession 新增 = 0**。

## OPEN-P10-1 不变量与前置关系

| 编号 | 不变量 | 状态 |
|---|---|---|
| `INV-01` | runtime 角色 ≠ migration 角色 | **FROZEN** |
| `INV-02` | runtime **无法**成为 migration 角色（严格非成员） | **FROZEN** |
| `INV-03` | runtime 的 registry `INSERT` = **DENY**（拒绝消息与 0007 原版逐字一致） | **FROZEN** |
| `INV-04` | 受信 migration context 的 controlled registry seed = **ALLOW** | **FROZEN** |
| `INV-05` | runtime **不持 DDL**（DB 层强制 + 正向断言 + 负向探针） | **FROZEN** |
| `INV-06` | 信任判据**不可伪造**（不得以 GUC / `application_name` / session flag / 可伪造判据作为信任依据） | **FROZEN** |
| `INV-07` | downgrade 后 C2 恢复为**对应授权前版本**（逐字节） | **FROZEN** |
| `INV-08` | downgrade 后**无残留**受信主体（角色由 `REVOKE` 保留、**不由单个 migration 擅自 `DROP`**） | **FROZEN** |

**前置关系（不改写任何既有决策）**

```text
① 执行顺序（Human 裁定 · 见 D-P13-15 与附录 K.4）：
     OPEN-P10-1（本组）→ P13 B-1 Amendment → P13 Implementation
② D-P13-15 的 Purpose「允许未来受信 migration context 建立 system registry seed，但前提是数据库身份隔离已经成立」
   ⇒ 其**前置判据**由 `D-OP101-13` 形式化（topology landed + complete eight-test proof）。
③ D-P13-15 的 Does not authorize 含「C2 修改」⇒ C2 改写**不得**由 D-P13-15 授权；
   本组 `D-OP101-05` 明确批准 `CC-7`（跨迁移函数替换新先例，先例前值 = 0），并附 6 项条件，
   且明文「该修改**不得由本 OQ 单独授权实施**，仍须经过独立 Implementation Authorization」。
④ D-P13-11（禁 `DISABLE TRIGGER` / `DROP TRIGGER` / `ALTER TRIGGER` / 绕过 C2 / 临时关闭后恢复）**保持原样**；
   本组 `D-OP101-05` 不触及触发器状态，仅约定**函数体**判据 ⇒ 与 D-P13-11 **不冲突**。
⑤ D-P10-13 的 `OPEN-P10-1`（DB 角色体系 + GRANT 归属）开放项**由本组结项**（指针见 D-P10-13 记录下方）。
⑥ `0016` / `0017` 的**创建**均**未被授权**（`D-OP101-03`）。
```

---

# D-OP101-01 — 角色拓扑（`RM-D`）

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-01` · **`ACCEPT OPTION D`**） |
| **决策** | 采用 **`RM-D`（三层角色）**：`uap_seed` / `uap_migrator` / `uap_app`。`uap_readonly` 不由本组引入（见 `D-OP101-06`）。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION D`；`RM-D` 是唯一把 **seed 权限**与 **DDL 权限**分离的拓扑，与 `D-OP101-02`（`NOSUPERUSER`）组合后受信主体权限面最小（请求单 §3.2 候选对照）。 |
| **影响范围** | 角色集合（含 `CORE §13` 之外的第四角色 `uap_seed` ⇒ 属**扩展**，`CORE §13` 保持为其**子集**）；多库一致性（角色为集群级；`GRANT` 每库独立）；GRANT 矩阵与测试连带面。 |
| **禁止** | 不得引入**超级用户**作为受信主体；不得把 seed 权限授予 runtime 身份；不得把本项解释为实施授权。 |

---

# D-OP101-02 — migration identity 的权限等级

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-02` · **`ACCEPT OPTION A`**） |
| **决策** | `R_mig` **必须为 `NOSUPERUSER`**，仅持 seed / DDL 所需的最小权限；不得以集群超级用户作为受信 migration context。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION A`；实测 `uap` 具 `rolsuper/createdb/createrole/rolreplication/rolbypassrls` 全 true（`E-9`）⇒ 保留超级用户等于放弃 `D-P13-11` 的实质约束力。 |
| **影响范围** | 环境引导顺序（谁能 `CREATE ROLE … NOSUPERUSER`）；`ALTER … OWNER` 的**成员资格前提**（见 `D-OP101-09`）；迁移 DSN 解析链（见 `D-OP101-10`）。 |
| **禁止** | 不得以便利为由回退为超级用户；不得让 runtime 凭据获得受信 migration identity 的能力。 |

---

# D-OP101-03 — revision 编号归属

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-03` · **`CUSTOM DECISION`**） |
| **决策** | **`0016` 归属 `OPEN-P10-1 Database Trust Boundary Foundation`；P13 seed 不占用 `0016`；P13 seed 在 OPEN-P10-1 完成并冻结、前置条件满足后使用下一连续 revision，即由后续 P13 Implementation Contract 正式登记为 `0017_p13_seed`。本裁定不授权创建 `0016` 或 `0017`。** |
| **理由 / 依据** | Human `CUSTOM DECISION` 原文（下方逐字）；`D-PLAT-09` 阶段序已含 `OPEN-P10-1` 作为 P13 之前的前置闸门。 |
| **影响范围** | 既有 `P13_IMPLEMENTATION_CONTRACT.md` §4 的 `0016_p13_seed` **设计记录**的**编号**须在 P13 实施契约轮重登记为 `0017_p13_seed`（该文件不在本轮授权面内，**本轮未修改**）。 |
| **禁止** | **不得创建 `0016` 或 `0017`**；不得在本轮预占或改写任何既有契约中的 revision 引用语义；不得据本项推导实施步骤。 |

> **`CUSTOM DECISION` 原文（逐字 · `OQ-OP101-03-CUSTOM`）**
>
> ```text
> 0016 归属 OPEN-P10-1 Database Trust Boundary Foundation；
> P13 seed 不占用 0016；
> P13 seed 在 OPEN-P10-1 完成并冻结、前置条件满足后使用下一连续 revision，
> 即由后续 P13 Implementation Contract 正式登记为 0017_p13_seed。
> 本裁定不授权创建 0016 或 0017。
> ```

---

# D-OP101-04 — 角色创建者

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-04` · **`ACCEPT OPTION C`**） |
| **决策** | 角色由 **deployment / orchestration / operations 预置**（pre-provision）；迁移与 runtime **均不承担**角色创建。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION C`；角色为**集群级**对象（`K-1`）且 `reset_test_database()` **不清理**集群角色（`K-4`）⇒ 由环境引导承担最自洽；legacy runner 已停用（`D-PLAT-07.a`、`M-6`）。 |
| **影响范围** | 环境引导流程；测试夹具的幂等与清理责任（见 `D-OP101-11`）；`scripts/` 需新增引导能力（属实施面，本轮不实施）。 |
| **禁止** | 不得由迁移创建角色；不得由 runtime 创建角色；不得依赖 legacy SQL runner 承担角色创建。 |

---

# D-OP101-05 — C2 判据形态

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-05` · **`CUSTOM DECISION`**） |
| **决策** | 采用 **`CP-F`**：以 `current_user` 与 `session_user` 对受信 migration identity 实施**合取判定**；仅当**两者均**满足受信 migration identity 条件时，C2 的 `INSERT` 才允许继续；普通 runtime identity **必须被拒绝**。**不得**使用 GUC · `application_name` · session flag · `session_replication_role` · `DISABLE TRIGGER` 作为信任依据。**同时明确批准 `CC-7`**：允许在未来受信数据库身份分离成立后，由后续独立授权的 migration 修改 `0007` 中 C2 触发器函数体，作为既有安全机制的**明确新先例**（先例前值 = **0**）。 |
| **理由 / 依据** | Human `CUSTOM DECISION` 原文（下方逐字）；`CP-F` 为请求单 §4.3 中**最强**判据形态（两身份量合取，且均可静态断言）；`CP-C` 已排除（C2 无条件 `RAISE` ⇒ 权限层无法放行任何人）。 |
| **影响范围** | `0007` 所建 C2 函数体的**未来**改写（属后续**独立授权**的实施面）；`INV-03`/`INV-04`/`INV-06` 的可证性形式；`D-P13-11` 的相容性（`D-OP101-05` 仅约定函数体判据，**不触及触发器状态**）。 |
| **禁止** | 不得使用 GUC / `application_name` / session flag / `session_replication_role` / `DISABLE TRIGGER` 作为信任依据；不得改变原有**非 `INSERT`** 保护语义；不得由本项**单独**授权实施；不得省略 `CC-7` 的 6 项条件。 |

> **`CUSTOM DECISION` 原文（逐字 · `OQ-OP101-05-CUSTOM`）**
>
> ```text
> 采用 CP-F：以 current_user 与 session_user 对受信 migration identity
> 实施合取判定。
> 仅当两者均满足受信 migration identity 条件时，C2 INSERT 才允许继续；
> 普通 runtime identity 必须被拒绝。
> 不得使用 GUC、application_name、session flag、session_replication_role
> 或 DISABLE TRIGGER 作为信任依据。
> 同时明确批准 CC-7：
> 允许在未来受信数据库身份分离成立后，由后续独立授权的 migration
> 修改 0007 中 C2 触发器函数体作为既有安全机制的明确新先例。
> 该修改必须满足：
> 1. 触发器本身不被 DISABLE；
> 2. runtime identity 继续 DENY；
> 3. 仅受信 migration identity 获得 INSERT 例外；
> 4. 原有非 INSERT 保护语义保持不变；
> 5. downgrade 后 C2 恢复为对应授权前版本；
> 6. 该修改不得由本 OQ 单独授权实施，仍须经过独立 Implementation Authorization。
> ```
>
> **`CC-7` 条件（机读编号 · 逐字取自上方原文）**
>
> ```text
> CC7-1  触发器本身不被 DISABLE
> CC7-2  runtime identity 继续 DENY
> CC7-3  仅受信 migration identity 获得 INSERT 例外
> CC7-4  原有非 INSERT 保护语义保持不变
> CC7-5  downgrade 后 C2 恢复为对应授权前版本
> CC7-6  不得由本 OQ 单独授权实施；仍须经过独立 Implementation Authorization
> ```

---

# D-OP101-06 — 是否同时落地 `uap_readonly`

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-06` · **`ACCEPT OPTION B`**） |
| **决策** | **DEFER**：本阶段只落受信角色与 runtime 角色；`uap_readonly` 另行立项。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION B`；`uap_readonly` 与「信任边界成立」正交（不影响 `INV-01`…`INV-08`）。 |
| **影响范围** | `CORE §13` 为**子集落地**（须显式声明分阶段，避免被视为偏离）；只读消费者（如 `/ready` 探针）暂复用 runtime 凭据。 |
| **禁止** | 不得以"补全 `CORE §13`"为由在本阶段引入 `uap_readonly`；不得在本阶段为其建立 GRANT。 |

---

# D-OP101-07 — runtime GRANT 矩阵范围

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-07` · **`ACCEPT OPTION C`**） |
| **决策** | runtime GRANT = **minimum required set**（按运行时**实际读写面**逐表核定的最小集，含 `audit_logs` 的写读动词组合，具体组合在实施契约中逐表核定）。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION C`；`D-P10-13` 禁止「不得给应用运行时 DDL 权限」；`CORE §13`「`audit_logs` 仅授予 `INSERT, SELECT`」。 |
| **影响范围** | 每个数据库的迁移内 GRANT（`GRANT` 不跨库）；权限相关测试套件连带面。 |
| **禁止** | 不得过度授权；**不得**在未获新决策前扩权（禁止以扩权替代"最小集"）；不得授予 runtime 任何 DDL 权限。 |

---

# D-OP101-08 — 「runtime 不持 DDL」是否由 DB 层强制

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-08` · **`ACCEPT OPTION C`**） |
| **决策** | **DB enforced + positive assertion + negative probe**：由 **DB 层强制**（GRANT 面排除 DDL）＋**正向断言**＋**负向探针**（尝试 DDL 必须失败）。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION C`；`D-P10-13` 禁止项「不得给应用运行时 DDL 权限」；平台铁律「**仅写在文档的规则必须落为测试**」（`DEPENDENCY_RULES`）。 |
| **影响范围** | `INV-05` 的可证性形式；测试基建（见 `D-OP101-11`）。 |
| **禁止** | 不得仅以文档约定替代 DB 层强制；不得移除负向探针。 |

---

# D-OP101-09 — 既有 156 对象的所有权

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-09` · **`ACCEPT OPTION B`**） |
| **决策** | **full ownership transition**：既有 **156** 个对象的**所有权全量转移**至受信角色（`R_mig`）。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION B`；实测 `public` 156 对象 owner 全为 `uap`（`E-3`），且全仓**无** `OWNER TO` / `ALTER … OWNER` 先例（`M-2`）。 |
| **影响范围** | 所有权变更面（含索引 / 约束 / 分区附件）；**派生必然结果**：`ALTER … OWNER TO <R_mig>` 要求**执行角色为 `<R_mig>` 的成员**（或在目标角色为 `NOSUPERUSER` 时先解决成员资格）⇒ 属**实施契约必须先解决的前置项**（**非新决策**）；与 `D-OP101-12`（保留集群角色、不 `DROP`）**相容**。 |
| **禁止** | 不得部分转移造成**未登记的**混合所有权状态；不得以所有权转移为名执行任何 DDL（本轮未授权）。 |

---

# D-OP101-10 — 配置 / 环境面承载双身份

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-10` · **`ACCEPT OPTION A`**） |
| **决策** | **independent migration/runtime keys + explicit resolution chain**：新增独立键承载 migration 身份，并**显式化** DSN 解析链（`env.py` 的优先级须被显式处理）。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION A`；实测 `env.py::_resolve_url()` 优先级为 `attributes` → **`DATABASE_URL` env** → `alembic.ini`，而 runtime 亦读同一 `DATABASE_URL`（`M-5`）⇒ 若不显式化，迁移会以 runtime 身份执行。 |
| **影响范围** | `config/settings.py` · `alembic.ini` · `.env.example` · `docker-compose.yml` · `tests/integration/alembic_testkit.py` · `tests/conftest.py`（**均属实施面，本轮未修改**）。 |
| **禁止** | 不得保留"runtime 的键决定迁移身份"的倒置；不得以部署纪律替代**可验证**的键分离。 |

---

# D-OP101-11 — 测试基建与集群级角色

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-11` · **`ACCEPT OPTION A`**） |
| **决策** | **testkit role provisioning + dual DSN fixtures**：testkit 负责角色**预置**（幂等），并提供 runtime / migration **双 DSN 夹具**。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION A`；`A-5` 的**八项可证性测试必须**在真实双角色会话下执行；`reset_test_database()` 仅 DROP/CREATE DATABASE、**不清理**集群角色（`K-4`）。 |
| **影响范围** | `tests/integration/alembic_testkit.py` 等（**实施面，本轮未修改**）；`INV-01`/`INV-02`/`INV-03`/`INV-06` 的可证性。 |
| **禁止** | 不得以"未伪造时 DENY"替代"runtime impossible"的可证性；不得降级为无角色夹具；不得改动既有负向守卫的**断言谓词**（其 rationale 同步见 `D-OP101-14`）。 |

---

# D-OP101-12 — downgrade 语义

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-12` · **`ACCEPT OPTION B`**） |
| **决策** | **REVOKE and retain cluster role** —— 降级执行 `REVOKE`（回收授权）并**保留**集群角色；**角色生命周期不由单个 migration 擅自 `DROP`**。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION B`；角色为集群级（`K-1`）、`DROP ROLE` 受"不得拥有对象 / 不得持有权限"约束（`K-3`）⇒ 保留角色可避免跨库副作用与 `D-OP101-09`（所有权转移）冲突。 |
| **影响范围** | `INV-08` 的口径为「**无残留授权**（角色可保留）」而非「角色实体消失」；降级后 C2 仍须复原（`D-OP101-05` `CC-7` 第 5 条 / `INV-07`）。 |
| **禁止** | 不得在 migration 的 `downgrade` 中执行 `DROP ROLE`；不得以静默跳过替代 `REVOKE`。 |

---

# D-OP101-13 — 「身份隔离已成立」的机读判据

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-13` · **`ACCEPT OPTION C`**） |
| **决策** | 判据 = **topology landed + complete eight-test proof**：所选拓扑**落地** **且** 八项可证性测试**全部通过**。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION C`；该判据即 `D-P13-15` `Purpose` 中「数据库身份隔离已经成立」的**形式化**（前置关系 ②）。 |
| **影响范围** | `D-P13-15` 前置条件的机读化；`P13 B-1 Amendment` 的**解冻条件**；`INV-01`…`INV-08` 的证据形式。 |
| **禁止** | 不得以文档声明或人工结论代替可执行证据；不得在八项测试未全通过时宣告隔离已成立。 |

---

# D-OP101-14 — 既有守卫 rationale 的同步口径

| 字段 | 内容 |
|---|---|
| **状态** | `FROZEN`（2026-09-27 · `OQ-OP101-14` · **`ACCEPT OPTION A`**） |
| **决策** | **update rationale while retaining existing assertions**：**保留**既有断言（`G-1`/`G-2`/`G-3` 的谓词语料为 `0013` 源码，**不改**），仅**更新其 rationale 文本**以反映 `OPEN-P10-1` 已承接。 |
| **理由 / 依据** | Human 裁定 `ACCEPT OPTION A`；断言语义（`0013` 零 `GRANT`）**仍然有效**，仅其解释文本随治理状态陈旧（`TEST vs DECISION` 登记项）。 |
| **影响范围** | `tests/architecture/test_p10_event_audit_boundary.py` · `tests/integration/test_p10_event_audit_schema.py`（**实施面，本轮未修改**）。 |
| **禁止** | 不得改动断言谓词以外扩大改动面；不得删除任何守卫；改动须以集合运算证明最小（`removed ⊆ {rationale 文本}`）。 |

---

**END OF PLATFORM_DECISION_LOG（`O-1` 裁定 · `AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE`，canonical error codes 恰为 **14**；8 类目 / 14 码 / 四对区分 **不变**；`BUDGET_EXCEEDED` **不得**并入 `TIMEOUT`；附录 F.8 登记，2026-09-25）**
**END OF PLATFORM_DECISION_LOG（P10 Decision Freeze · `D-P10-01`…`D-P10-18` 写入并置 `FROZEN` ⇒ `D-P10` 共 18 条：18 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`；附录 G 登记；`C-1` RESOLVED · `C-2` CLARIFIED · `C-3` RESOLVED · `C-4` RESOLVED；`D-PLAT-09`/`D-PLAT-10`/`D-AUTH-15` **未 supersede**；supersession 新增 = 0；P10/P11 Implementation = NOT AUTHORIZED，2026-09-25）**
# 附录 I — P12 冻结状态汇总（2026-09-25）

## I.1 计数

```text
D-P12 条目                 = 15
  FROZEN                   = 15
  DEFERRED                 = 0
  SUPERSEDED               = 0
  unresolved OQ            = 0
OQ-P12-01 … OQ-P12-15      = 15 / 15 已裁定
```

## I.2 Deferred

```text
无本轮 Deferred 条目。
（既有 index 删除/合并 = DEFERRED，见 D-P12-11；属"未发生事项"，非本组条目）
```

## I.3 与既有冻结的关系

| 关系 | 说明 |
|---|---|
| `D-PLAT-09` | **未 supersede**；本轮唯一承认的阶段顺序不变 |
| `D-PLAT-11`（首个主体只经 P13） | 未触及；无 seed |
| `D-P10-01` / `D-P10-11` | 未 supersede；`D-P12-08`/`CF-6` 仅澄清 **schema vs index ownership** |
| `D-P11-01` / `D-P11-11` | 未 supersede；`D-P12-09` 与其**同向**（P11 不建顺手索引 ⇒ P12 逐项裁定） |
| `D-B15-06` / `D-B16-07` / `D-P09-04` / `D-P09-16` | 未 supersede；`D-P12-04` 明确**保持**其形式二分法 |
| `D-AGENT-08`（双层幂等） | 未触及；`D-P12-06` 仅确认工具侧锚点语义不变 |
| `D-AGENT-16`（Gateway Contract/Runtime） | 未触及；Runtime Gate 仍 CLOSED |
| **supersession 新增** | **0**（平台级 supersession 仍恒 = 1，即 `D-B14-08`） |

## I.4 本轮不含实施

```text
CREATE INDEX = 0 · DROP INDEX = 0 · ALTER INDEX = 0
DDL = 0 · DML = 0 · migration = 0
code = 0 · test = 0 · config = 0
commit = 0 · tag = 0 · push = 0
P12 IMPLEMENTATION = NOT AUTHORIZED
P13 IMPLEMENTATION = NOT AUTHORIZED
Runtime Implementation Gate = CLOSED
```

## I.5 编号对账

`OQ-P12-01`…`15` ↔ `D-P12-01`…`15` **一一对应（15/15）**，**无重映射**。
`OQ-P12-15` 侧重点由 PREP 的「机制边界与索引所有权」收敛为「Scope Closure / No Opportunistic Indexing」；
PREP 机制边界内容已被 `D-P12-15` 的「不包括」清单涵盖 ⇒ **非重映射，无需重排**。
（对照：P11 轮曾发生 `06`/`07` 对调，本轮**未发生**。）

## I.6 跨决策扫描结果（Charter §7 义务）

扫描范围：Current Decision Log · Historical Decision Logs · Architecture · Schema Decisions · Implementation Contracts。

| 检查类 | 结果 |
|---|---|
| `ACTIVE vs FROZEN` | **0 冲突**（P12 未新增任何 active 未冻结项） |
| `FROZEN vs FROZEN` | **0 冲突**（15 条与 `D-PLAT-09`/`D-P10-01`/`D-P10-11`/`D-P11-01`/`D-P11-11`/`D-B15-06`/`D-B16-07`/`D-P09-04`/`D-P09-16`/`D-AGENT-08` 逐条核对一致） |
| `SCHEMA vs DECISION` | **6 项已登记并处置**（`CF-1`…`CF-6`，见 I.7） |
| 陈旧「P12 已实现」声明 | **0 命中** |
| `D-P12-` 命名空间冲突 | **0**（冻结前命中 0） |

## I.7 `CF-1` … `CF-6` 处置（终态）

| ID | 事项 | 终态 | 落地 |
|---|---|---|---|
| `CF-1` | `INDEX_STRATEGY` §3 称 resources 的 space/owner「复合索引打头均覆盖」vs 实测无打头索引 | **CLARIFIED** | **不得据此自动创建** `space_id`-leading / `owner_id`-leading 索引；保留为**文档一致性事项**：明确「documented coverage claim」与「implemented coverage」**必须区分**（`P12_PREP_REPORT` §9 · `P12_ACCEPTANCE_MATRIX` FK-10） |
| `CF-2` | `ix_aimodels_capability`（`T-1`）多重不一致 | **RESOLVED** | 采用 `D-P12-14`：**DO NOT IMPLEMENT**；`T-1` **关闭为 stale / mismatched design claim** |
| `CF-3` | `B1-6_DECISION_LOG:331` 称 P3 候选「全部未在 0003–0008 落地」，而 `ix_rp_permission` 实已落地 | **CLARIFIED** | canonical implemented object = **`ix_role_permissions_permission`**；`ix_rp_permission` **仅作历史命名记录**；**P12 不 rename**（`D-P12-12`） |
| `CF-4` | B0 `STEP1B_INDEX_STRATEGY.md` 缺 `platform_memberships` 小节 | **CLARIFIED** | 文档缺失**不自动**转成 index implementation requirement；以后是否需 index 按 `D-P12-02` **单独 adjudicate** |
| `CF-5` | 部分索引被误当 FK 覆盖 | **RESOLVED** | 确认 **`partial index ≠ full FK coverage`**；`partial-only` **继续单独统计**；**不得**在 acceptance 中归入 full coverage（`D-P12-05`） |
| `CF-6` | `D-P10-01`「分区表二次 ALTER」理由 vs P12 后置建 7 索引 | **CLARIFIED** | **P10 建表 = YES；P12 建对应 index = YES**；这是 **`P10 schema ownership + P12 index ownership`**，**不是**阶段错误；**不得**把 P12 后置 index 解释成 **P10 schema regression**（`D-P12-08`） |

### I.7.1 处置汇总（可机读）

```text
CF-1 = CLARIFIED
CF-2 = RESOLVED
CF-3 = CLARIFIED
CF-4 = CLARIFIED
CF-5 = RESOLVED
CF-6 = CLARIFIED
GAP-INV-P12 = governed by per-gap adjudication
T-1 = resolved / stale claim
```

## I.8 `GAP-INV-P12` 与 `T-1` 终态

```text
GAP-INV-P12 = inventory / adjudication completeness gap
              ⇒ 受「per-gap adjudication」治理（D-P12-13 · 永久规则见 P12 Canonical Model 节）
              ⇒ 24 GAP 逐项 CREATE / DEFER / ALREADY COVERED / NOT REQUIRED
              ⇒ 19 个 post-strategy FK 须单独标记来源年代

T-1         = CLOSED as stale / mismatched design claim（D-P12-14）
              ⇒ 不实施、不偷换为 GIN(capabilities)、不发明其他 JSONB index
              ⇒ append-only clarification 已写入 STEP1B_INDEX_STRATEGY.md 与本文 D-P12-14
```

## I.9 `NUM-1` / `MEASURE-1` / `GUARD-1` 裁定同步（**2026-09-25 Human Decision** · append-only）

> 本区为**追加登记**：**不**修改 `I.1`…`I.8`、**不**改写任何 `D-P12-*` 决策正文、**不**产生新的 supersession。
> 被更正者**仅为实测数字与 revision 编号**，决策**语义逐条不变**。

### I.9.1 可机读裁定汇总

```text
NUM-1       = RESOLVED
MEASURE-1   = ACCEPTED
GUARD-1     = ACCEPTED

P10 = 0013_p10_event_audit
P11 = 0014_p11_triggers
P12 = 0015_p12_indexes

FK total        = 57
ALREADY COVERED = 27
partial-only    = 5
GAP             = 25
adjudicable     = 30

T-22 removals = exactly 5
T-22 retained = exactly 5

D-P12-13 semantics = unchanged
```

### I.9.2 `NUM-1` — revision 编号分配（**RESOLVED**）

```text
0012_authz_enforcement
    ↓
0013_p10_event_audit
    ↓
0014_p11_triggers
    ↓
0015_p12_indexes
```

```text
规则（永久）：每个 phase 占用**唯一** Alembic revision；
              不得两个 phase 使用同一个 numeric revision；
              不得因前一阶段尚未实施而复用其 revision number。
```

- 本裁定**纠正** `P12_IMPLEMENTATION_CONTRACT.md`（契约轮）将 P12 误记为 `0013_p12_indexes` 的编号。
- 纠正内容为**纯编号**，**不改任何 P12 决策语义**（`D-P12-01`…`D-P12-15` 逐条不变）。
- **派生必然结果**：P12 migration 的 `down_revision = 0014_p11_triggers`（不再是 `0012_authz_enforcement`）——
  这是 `D-PLAT-09` 顺序（`P10 → P11 → P12`）的**机械后果**，**非新决策**。
- 当前状态仍为 `0013+ = ABSENT`（三份 migration **均未创建**）。

### I.9.3 `MEASURE-1` — 实测口径校正（**ACCEPTED**）

```text
PREP 实测（冻结文本所引用）  →  校正后（现行口径）
FK 总数              54      →  57
ALREADY COVERED      25      →  27
partial-only          5      →   5（不变）
GAP                  24      →  25
FK 反查候选集        29      →  30

算术闭合：27 + 5 + 25 = 57 · 25 + 5 = 30
```

**漏检的 3 条 FK**（以原生 `ALTER TABLE … ADD CONSTRAINT … FOREIGN KEY` 创建，不在 `op.create_table` 体内）：

| FK constraint | FK source → target | ON DELETE | 分类 | 证据 |
|---|---|---|---|---|
| `fk_tm_role` | `tenant_memberships.role_id` → `roles.id` | RESTRICT | **ALREADY COVERED** = `ix_tenant_memberships_role` | `0005:432` |
| `fk_membership_role` | `memberships.role_id` → `roles.id` | RESTRICT | **ALREADY COVERED** = `ix_memberships_role` | `0005:435` |
| `fk_agents_current_version` | `agents.current_version_id` → `agent_versions.id` | SET NULL | **GAP** ⇒ **CREATE candidate** | `0011:356` |

```text
性质 = measurement correction only
D-P12-13 的【规则语义不变】：
      FK coverage GAP → query evidence adjudication → CREATE / DEFER / ALREADY COVERED / NOT REQUIRED
      禁止  FK exists → automatic index
```

> `I.8` 中引用的 `24 GAP` 为 **PREP 时点**的实测值；**现行口径为 25**（以本区为准）。
> **未改写** `P12_PREP_REPORT` / `P12_DECISION_RESOLUTION` / `P12_ACCEPTANCE_MATRIX`
> 三份冻结文档中的历史实测值（append-only 纪律）。

### I.9.4 `GUARD-1` — T-22 测试契约同步（**ACCEPTED**）

```text
T-22（test_t22_no_extra_fk_column_indexes）= 旧阶段 protection，
     **不 supersede `D-P12-13`**

P12 实施时必须从 forbidden 集移除【恰好 5 名】：
     ix_ap_permission · ix_ap_tool · ix_ap_version ·
     ix_agents_current_version · ix_agents_default_route
必须保留【恰好 5 名】（DEFER / NOT REQUIRED ⇒ 不建）：
     ix_agents_owner · ix_agents_space · ix_texec_agent ·
     ix_texec_actor · ix_agent_versions_published_by

验收规则（硬）：
     removed_forbidden_names   ⊆ P12 CREATE set
     remaining_forbidden_names ∩ P12 CREATE set = ∅
     且 P12 CREATE set ↔ T-22 expectations ↔ index-name test assertions 三方一致
```

本轮**未修改任何测试代码**；改写范围由 Human 裁定，执行时点在 **P12 实施轮**。

### I.9.5 本轮边界

```text
migration files added = 0 · migration files modified = 0
DDL = 0 · DML = 0 · CREATE / DROP / ALTER INDEX = 0
code = 0 · tests = 0 · config = 0
commit = 0 · tag = 0 · push = 0
P10 / P11 / P12 / P13 IMPLEMENTATION = NOT AUTHORIZED
Runtime Implementation Gate = CLOSED
```

**END OF PLATFORM_DECISION_LOG（P11 Decision Freeze · `D-P11-01`…`D-P11-14` 写入并置 `FROZEN` ⇒ `D-P11` 共 14 条：14 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`；附录 H 登记；`CF-1`/`CF-2`/`CF-3` CLARIFIED · `CF-4` INTENTIONAL-FROZEN；`L` = P10-owned 保持；`D-PLAT-09`/`D-PLAT-10` **未 supersede**；supersession 新增 = 0；P11/P12/P13 Implementation = NOT AUTHORIZED，2026-09-25）**
**END OF PLATFORM_DECISION_LOG（P12 Decision Freeze · `D-P12-01`…`D-P12-15` 写入并置 `FROZEN` ⇒ `D-P12` 共 15 条：15 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`；附录 I 登记；`CF-1`/`CF-3`/`CF-4`/`CF-6` CLARIFIED · `CF-2`/`CF-5` RESOLVED；`GAP-INV-P12` = per-gap adjudication 治理 · `T-1` = CLOSED as stale/mismatched design claim；`ix_events_*`/`ix_audit_*`（7）= P12；`D-PLAT-09`/`D-PLAT-10`/`D-PLAT-11`/`D-P10-01`/`D-P10-11`/`D-P11-01`/`D-P11-11` **未 supersede**；supersession 新增 = 0；P12/P13 Implementation = NOT AUTHORIZED，2026-09-25）**
## I.10 `P13` Freeze Gate 登记部分裁定（**2026-09-26 Human Decision Freeze Gate** · append-only）

> 本区为**追加登记**：**不**修改 `I.1`…`I.9`、**不**写 `D-P13-01…14` 正式条目
> （指令 §4：须 **14/14 OQ** 均有明确 Human Decision 后方允许写入）· **不**产生新 supersession。

```text
P13 DECISION FREEZE GATE（2026-09-26）登记：

OQ-P13-01 = PENDING   （permissions canonical list 未完成人工审计；禁止自动生成清单）
OQ-P13-02 = PENDING   （system role ownership 待裁）
OQ-P13-03 = FROZEN    （registry seed = migration-controlled path ·
                       runtime INSERT = FORBIDDEN · C2 保持，不得删除/绕过/长期关闭）
OQ-P13-04 = PENDING   （agent subject seed 待裁）
OQ-P13-05 = PENDING   （bootstrap tenant 待裁）
OQ-P13-06 = FROZEN    （identity row = allowed · plaintext password/credential secret = forbidden ·
                       「首个可登录主体」与「P13 创建主体记录」必须区分；
                       登录能力 = 后续 onboarding / runtime credential establishment）
OQ-P13-07 = PENDING   （platform membership 待裁）
OQ-P13-08 = PENDING   （tenant/space membership 待裁）
OQ-P13-09 = PENDING   （seed ordering 待裁）
OQ-P13-10 = PENDING   （idempotency 待裁）
OQ-P13-11 = PENDING   （trigger interaction 待裁）
OQ-P13-12 = BLOCKING  （downgrade 的 migration-owned vs runtime-created 区分机制未裁定；
                       key-marker / NO-OP / fail-closed 三案均不得自行采用）
OQ-P13-13 = FROZEN    （credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0；
                       需 secret 的 onboarding 走后续安全流程）
OQ-P13-14 = PENDING   （runtime-created data protection 待裁）

FROZEN = 3 · PENDING = 10 · BLOCKING = 1  ⇒  14/14 未满足
⇒ D-P13-01…14 本轮不写入；P13 DECISION FREEZE = BLOCKED
```

```text
本轮边界：
0016+ = ABSENT · INSERT/UPDATE/DELETE/DDL/DML = 0 · code/test/config = 0
commit = 0 · tag = 0 · push = 0
P13 IMPLEMENTATION = NOT AUTHORIZED · Runtime = NOT AUTHORIZED
完整 Evidence/Options 补齐：OQ-04/06/07/08/09/10/11/13/14 增补 Impact 三字段
（PREP 轮编写遗漏，本轮补齐 · 双向披露）· 推荐 Direction 未被默认采用
```

**END OF PLATFORM_DECISION_LOG（`NUM-1` / `MEASURE-1` / `GUARD-1` 裁定同步 · 附录 **I.9**（append-only）；`P10 = 0013_p10_event_audit` · `P11 = 0014_p11_triggers` · `P12 = 0015_p12_indexes`；MEASURE-1 实测口径校正 **57 / 27 / 5 / 25 / 30**（`D-P12-13` 规则语义**不变**）；GUARD-1 T-22 移除**恰好 5** · 保留**恰好 5**；`D-P12-01`…`D-P12-15` **未改写**；supersession 新增 = 0；P10–P13 Implementation = NOT AUTHORIZED，2026-09-25）**
**END OF PLATFORM_DECISION_LOG（`P13` Freeze Gate 部分裁定登记 · 附录 **I.10**（append-only）；FROZEN 3（OQ-03/06/13）· PENDING 10 · BLOCKING 1（OQ-12）· 14/14 未满足 ⇒ `D-P13-01…14` 未写入 · P13 DECISION FREEZE = BLOCKED · 2026-09-26）**

# 附录 J — P13 冻结状态汇总（2026-09-26）

## J.1 计数

```text
D-P13 共 14 条：FROZEN 14 · DEFERRED 0 · SUPERSEDED 0 · unresolved OQ 0
  继承既有 FROZEN（Freeze Gate 未重裁）  = 3   （D-P13-03 / 06 / 13）
  本轮 Human 架构裁定                    = 10  （D-P13-01 / 04 / 05 / 07 / 08 / 09 / 10 / 11 / 12 / 14）
  本轮 DELEGATED RESOLUTION（§0 授权）    = 1   （D-P13-02，派生 · 可被 Human 否决）
○ OQ-P13-01 = CUSTOM DECISION      ○ OQ-P13-05 = ACCEPT OPTION B
○ OQ-P13-04 = ACCEPT OPTION A      ○ OQ-P13-07 = ACCEPT OPTION A
○ OQ-P13-08 = ACCEPT OPTION B      ○ OQ-P13-09 = ACCEPT OPTION A
○ OQ-P13-10 = ACCEPT OPTION A      ○ OQ-P13-11 = ACCEPT OPTION A
○ OQ-P13-12 = ACCEPT OPTION C      ○ OQ-P13-14 = ACCEPT OPTION A
※ OQ-P13-02 对应的 Human 指令 §3 实为 OQ-P13-01 Q2（manage/write 映射）⇒ 已登记重映射
```

## J.2 编号重映射登记（显式 · 不得静默）

```text
Human 指令 §3 标题 = 「OQ-P13-02 — manage / write mapping」
SHEET 的 OQ-P13-02 = 「System role ownership」
⇒ 指令 §3 的**内容**属 OQ-P13-01 的第 2 问 ⇒ 登记为 D-P13-01 的子问题闭项 Q2
⇒ SHEET 的 OQ-P13-02 按指令 §0 授权派生裁定 ⇒ 登记为 D-P13-02（DELEGATED RESOLUTION）
```

## J.3 P13 实施轮前置澄清项（登记 · 不阻塞 FREEZE）

```text
① D-PLAT-11（路线 A：首个可登录主体只经 P13 seed）与本轮 D-P13-05 / D-P13-08 存在语义张力：
   既然 P13 不创建 tenant / membership（且 §15 的 CREATE 面不含 users），
   「首个可登录主体」的产生路径需**正式重新解释**。
   该义务由 OQ-P13-05 的既有 Engineering Impact（「B ⇒ D-PLAT-11 需重新解释」）**预先载明**，
   属 Human 已知并接受的后果 ⇒ 登记为本轮派生后果，**非新冲突**。
   本轮**不改写、不 supersede** D-PLAT-11；建议在 P13 实施契约轮形式化处理。
② D-AUTH-05 的 canonical action 词表在 D-P13-01 下**未被修改**；`manage` / `write` 仅作为**输入别名**
   映射为 `admin` / `update`，**不进入** DB 词表。
③ OQ-P13-01 Q5（`resource_type` 词表）为**派生闭项** ⇒ 不新增 DB 词表 / CHECK。
```

## J.4 本轮边界

```text
migration files added = 0 · migration files modified = 0
DDL = 0 · DML = 0 · seed INSERT = 0 · runtime code = 0
0016+ = ABSENT · 0010–0015 sha256 逐字节未变
commit = 0 · tag = 0 · push = 0
P13 IMPLEMENTATION = NOT AUTHORIZED · Runtime = NOT AUTHORIZED
D-PLAT-09 / D-AUTH-01..25 / D-AGENT-01..16 / D-P10-01..18 / D-P11-01..14 / D-P12-01..15 未改
supersession 新增 = 0
```

**END OF PLATFORM_DECISION_LOG（P13 Decision Freeze · `D-P13-01`…`D-P13-14` 写入并置 `FROZEN` ⇒ `D-P13` 共 **14** 条：14 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`；继承 Freeze Gate 既有 FROZEN **3**（03/06/13）· 本轮架构裁定 **10** · DELEGATED RESOLUTION **1**（02）；附录 **J** 登记；`D-PLAT-11` 需重新解释项登记于 `J.3`（不阻塞）；0016+ = ABSENT · DDL/DML = 0 · supersession 新增 = 0；`P13 IMPLEMENTATION = NOT AUTHORIZED`；2026-09-26）**

---

# 附录 K — B-1 Human Decision Final Direction 登记（2026-09-26）

> **本区为追加登记**：**不**修改 `J.1`…`J.4`、**不**改写 `D-P13-01…14` 正文、**不**改写 `D-P13-11` 禁止字段、**不**改写 `D-PLAT-09` / `D-PLAT-11` / `D-P10-13`。
> `D-P13-15` 正式条目已**纯插入**于 `# P13 Canonical Model` 命名空间内（`D-P13-14` 之后）。

## K.1 Human 裁定（**逐字**）

```text
O-1 = REJECT
O-4 = REJECT
O-3 = ACCEPT AS ARCHITECTURAL DIRECTION
O-2 = DEFERRED
```

## K.2 核心原因（**逐字** + 机读）

```text
当前 UAP 数据库不存在 migration/runtime 可区分信任边界：
runtime   = uap(superuser)
migration = uap(superuser)

因此：GUC · application_name · session variable · temporary flag
均不得作为安全机制。
```

**实测复验（`uap_b1_test` @0015 · 全为只读）**

```text
FD-1  alembic.ini:5 与 config/settings.py:57 DSN 相同（uap:uap）
FD-2  pg_roles: uap → rolsuper=t · rolcreatedb=t · rolcreaterole=t · rolbypassrls=t · rolcanlogin=t
FD-3  public 对象 156 个全部 owner = uap；pg_proc 22 函数 owner = uap
FD-4  非 pg_% 角色 = 仅 uap（1 个）
FD-5  显式 GRANT 到非 owner = 0；datacl = NULL
FD-6  自定义 GUC 可被任意会话设置并读回（事务级；新会话复原）⇒ 无权限门槛
FD-7  application_name / 会话变量同属客户端自述 ⇒ 无服务端身份校验
```

## K.3 `D-P13-15` 登记与**现行计数口径**

```text
D-P13-15 = FROZEN（B-1 Amendment · Human 逐字提供文本）
现行计数口径（2026-09-26 B-1 FINAL DIRECTION 起）：
  D-P13 共 15 条：FROZEN 15 · DEFERRED 0 · SUPERSEDED 0
  （原 14 条 = 2026-09-26 P13 Decision Freeze 时点快照，见附录 J.1；**该快照不改写**）
新增条目归属：本轮 Human 架构裁定 = 1（D-P13-15）
supersession 新增 = 0
```

> **口径说明（依先例）**：命名空间标题「`# P13 Canonical Model — D-P13-01 … D-P13-14`」与总表（14 行）保持 **Freeze 时点快照**，**不改写**；
> 现行计数由本附录声明（与 `NUM-1`/`MEASURE-1` 轮「旧实测值不改写、由新附录声明现行口径」的处理一致）。

## K.4 执行顺序调整（Human 裁定）

```text
执行顺序 = OPEN-P10-1（Database Trust Boundary Foundation）
        → P13 B-1 Amendment
        → P13 Implementation
禁止     = 不得直接实施 P13
```

**派生必然结果（机械后果 · 非新决策）**

```text
① D-PLAT-09（路线 A：P10 → P11 → P12 → P13 → Runtime）**未 supersede · 未改写**；
   本裁定在其 P13 之前**插入一个前置闸门**（属路线 A 的细化）。
② `0016+` 的 revision 归属 **尚未确定**：若 OPEN-P10-1 需独占 revision，则 P13 seed 的编号将顺延。
   该编号**必须由 Human 裁定**（`OQ-OP101-03`）；本轮**不预占、不改写**既有契约中 `0016_p13_seed` 设计记录的语义。
```

## K.5 C2 原则保持（Human 裁定 · **逐字**）

```text
不得：DISABLE TRIGGER · session_replication_role · 普通 GUC 信任
      · application_name 判断 · runtime 可获得 migration 权限
```

```text
CP-1 = DISABLE TRIGGER 禁止（与 D-P13-11 一致）
CP-2 = session_replication_role 禁止
CP-3 = 普通 GUC 信任 禁止（由 FD-6 实测证明可伪造）
CP-4 = application_name 判断 禁止（**本轮升格为 Human 明令禁止项**）
CP-5 = runtime 可获得 migration 权限 禁止（与 D-P10-13「不得给应用运行时 DDL 权限」一致）
```

## K.6 机读汇总

```text
O-1 = REJECT
O-2 = DEFERRED
O-3 = ACCEPT AS ARCHITECTURAL DIRECTION
O-4 = REJECT
D-P13-15 = FROZEN
D-P13 现行条数 = 15
supersession 新增 = 0
P13 IMPLEMENTATION = NOT AUTHORIZED
0016 = ABSENT
DDL = 0
DML = 0
0007 = unchanged
C2 = unchanged
commit = 0
tag = 0
push = 0
执行顺序 = OPEN-P10-1 → P13 B-1 Amendment → P13 Implementation
下一阶段 = OPEN-P10-1 PREP / Database Trust Boundary Design / 只读设计阶段
```

## K.7 本轮边界

```text
migration files added = 0 · migration files modified = 0
DDL = 0 · DML = 0 · seed INSERT = 0 · CREATE ROLE = 0 · GRANT/REVOKE = 0
runtime code = 0 · test = 0 · config = 0
0016+ = ABSENT · 0010–0015 sha256 逐字节未变
commit = 0 · tag = 0 · push = 0
D-PLAT-09 / D-AUTH-01..25 / D-AGENT-01..16 / D-P10-01..18 / D-P11-01..14 / D-P12-01..15 / D-P13-01..14 未改
```

**END OF PLATFORM_DECISION_LOG（B-1 Human Decision Final Direction · `D-P13-15` 写入并置 `FROZEN` ⇒ `D-P13` 现行 **15** 条：15 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`（Freeze 时点快照 14 见附录 J.1，不改写）；裁定 `O-1 = REJECT` · `O-4 = REJECT` · `O-3 = ACCEPT AS ARCHITECTURAL DIRECTION` · `O-2 = DEFERRED`；执行顺序调整为 `OPEN-P10-1 → P13 B-1 Amendment → P13 Implementation`；C2 原则保持（禁 `DISABLE TRIGGER` / `session_replication_role` / 普通 GUC 信任 / `application_name` 判断 / runtime 获 migration 权限）；附录 **K** 登记；`D-PLAT-09` / `D-PLAT-11` / `D-P10-13` / `D-P13-01…14` **未 supersede · 未改写**；supersession 新增 = 0；0016 = ABSENT · DDL/DML = 0 · `0007` = unchanged · `C2` = unchanged · commit/tag/push = 0；`P13 IMPLEMENTATION = NOT AUTHORIZED`；下一阶段 = `OPEN-P10-1 PREP`（只读设计）；2026-09-26）**

---

# 附录 L — OPEN-P10-1 冻结状态汇总（2026-09-27）

> **本区为追加登记**：**不**修改 `K.1`…`K.7`、**不**改写 `D-P10-13` 正文（仅指针）、**不**改写任何既有 `D-*` 正文。
> `D-OP101-01`…`D-OP101-14` 正式条目已**纯插入**于 `# OPEN-P10-1 Canonical Model` 命名空间内。

## L.1 计数

```text
D-OP101 共 14 条：FROZEN 14 · DEFERRED 0 · SUPERSEDED 0 · unresolved OQ 0
  Human Decision 派生的 `ACCEPT OPTION *`（明文）  = 12
  Human Decision 派生的 `CUSTOM DECISION`          = 2   （D-OP101-03 · D-OP101-05）
  `PENDING` / `KEEP OPEN` / `NEED MORE EVIDENCE`   = 0 · 0 · 0
○ OQ-OP101-01 = ACCEPT OPTION D    ○ OQ-OP101-02 = ACCEPT OPTION A
○ OQ-OP101-03 = CUSTOM DECISION    ○ OQ-OP101-04 = ACCEPT OPTION C
○ OQ-OP101-05 = CUSTOM DECISION    ○ OQ-OP101-06 = ACCEPT OPTION B
○ OQ-OP101-07 = ACCEPT OPTION C    ○ OQ-OP101-08 = ACCEPT OPTION C
○ OQ-OP101-09 = ACCEPT OPTION B    ○ OQ-OP101-10 = ACCEPT OPTION A
○ OQ-OP101-11 = ACCEPT OPTION A    ○ OQ-OP101-12 = ACCEPT OPTION B
○ OQ-OP101-13 = ACCEPT OPTION C    ○ OQ-OP101-14 = ACCEPT OPTION A
OQ ↔ D-OP101 一一对应 = 14 / 14（编号空间冻结前 `D-OP101-` 命中 = 0）
SUPERSESSION 新增 = 0 · 平台级 supersession 恒 = 1（D-B14-08 → SUPERSEDED by D-AUTH-05，未改）
```

**命名空间计数（现行口径 · 2026-09-27）**

```text
D-PLAT 17 · D-AUTH 25 · D-AGENT 16 · D-P10 18 · D-P11 14 · D-P12 15 · D-P13 15 · **D-OP101 14**
（Freeze 时点快照：J.1 记 D-P13 = 14、K.3 记 D-P13 = 15；均**不改写**，以本行为现行口径）
```

## L.2 Deferred 登记

```text
D-OP101-06（`uap_readonly`）= **DEFER**（本组唯一 DEFERRED 语义条目；其 status 为 FROZEN-DEFER，
  即「决定 = 暂不落地」，非"决策未决"）。
D-OP101-12 明确：downgrade **不 `DROP`** 集群角色（角色生命周期不由单个 migration 擅自处置）。
```

## L.3 与既有冻结的关系（**不 supersede 任何决策**）

| 既有冻结 | 与本组的关系 |
|---|---|
| `D-PLAT-09`（路线 A） | **未 supersede**；本组即 Human 裁定插入的 `OPEN-P10-1` 前置闸门的**决策冻结** |
| `D-P10-13` / `OPEN-P10-1` | **开放项由本组结项**（`GRANT` 归属 → `D-OP101-07`/`08`/`10`）；`D-P10-13` 正文**逐字未改**，仅加**指针行** |
| `D-P11-08`（禁 `SECURITY DEFINER`） | **保持**；本组未引入任何 `DEFINER` |
| `D-P13-03`（migration-controlled path） | **核心目标保持**；受信主体由本组（`RM-D` + `CP-F`）形式化 |
| `D-P13-11`（禁 trigger bypass） | **保持原样**；`D-OP101-05` 不触及触发器状态（仅函数体判据）⇒ 相容 |
| `D-P13-15`（B-1 Amendment） | **未改写**；其 `Purpose` 前置由 `D-OP101-13` 形式化；其 `Does not authorize` 含「C2 修改」⇒ `D-OP101-05` 的 `CC-7` 仍**不构成**实施授权 |
| `D-P13-01…14` / `D-PLAT-11` / `CORE` §13 | **未改写**；`CORE §13` 保持为 `RM-D` 的**子集**（`uap_seed` 为扩展角色） |

## L.4 Charter §7 跨决策扫描结果（**Decision Freeze 前强制义务**）

```text
§7.1 扫描范围（强制，缺一不可）—— 本轮覆盖：
  Current Decision Log      = PLATFORM_DECISION_LOG.md
  Historical Decision Logs  = B1-4 / B1-5 / B1-6 / P09 / STEP1B_B1_2 / STEP1B_B1_3 等 *_DECISION_LOG.md
  Architecture              = ARCHITECTURE.md · DEPENDENCY_RULES.md · CORE_DOMAIN_MODEL.md · ER_MODEL.md
  Schema Decisions          = *_SCHEMA_DESIGN.md · *_MIGRATION_PLAN.md · *CONSTRAINT_MATRIX.md
  Implementation Contracts   = *_IMPLEMENTATION_CONTRACT.md · *_IMPLEMENTATION_TEST_MATRIX.md
  扫描面 = docs/**.md 共 **123** 个文件（纯 Python 逐行扫描；raw / exempt / adjudicated 三报）

§7.2 三类冲突检测：
  ACTIVE vs FROZEN   = **0**（无 ACTIVE/PROPOSED 条目与既有 FROZEN 矛盾；带**决策指针**的 DRAFT 文档已标注"时点快照"）
  FROZEN vs FROZEN   = **0**（`D-OP101-*` × `D-P13-11` / `D-P13-15` / `D-P10-13` / `D-P11-08` 逐条求交 ⇒ 相容，见 L.3）
  SCHEMA vs DECISION = **0**（本组为**决策冻结**、`OPEN-P10-1` 未实施 ⇒ 库内现状（1 角色 / registry 0 行 / C2 无条件 RAISE）
                        与"未实施"一致，**非**不一致）

六类目标扫描（raw / exempt / residual）：
  T1 `GRANT = 0` 历史陈述        raw 14 · exempt 14 · residual **0**
  T2 `OPEN-P10-1 … DEFER` 陈述   raw 14 · exempt 14 · residual **0**
  T3 `uap_readonly` 提及         raw 35 · exempt 31 · residual **4**   → 见 `CF-3`
  T4 `0016_p13_seed` 引用        raw 32 · exempt 32 · residual **0**   （编号重映射待 P13 实施契约轮登记）
  T5 三角色模型陈述              raw 27 · exempt 23 · residual **4**   → 见 `CF-3`（同 4 行）
  T6 `OQ-OP101-* PENDING` 残留   raw 14 · exempt 14 · residual **0**
  合计 raw 136 · residual **8**（去重后 = **4 行**，全部为 `CF-3`）
```

**`CF-3`（新登记 · **只登记不修改**）**

```text
残余 4 行（同一语义 · 分布 4 个非决策载体文档）：
  ① CORE_DOMAIN_MODEL.md:1058      「最小权限 DB 角色 | uap_app（DML）、uap_migrator（DDL，仅迁移窗口）、uap_readonly；…」
  ② STEP1A_DESIGN_REPORT.md:442    「DB 角色 | uap_app(DML) / uap_migrator(DDL，仅迁移窗口) / uap_readonly；…」
  ③ STEP1B_B0_GATE_REPORT.md:98    （同义枚举，含 `uap_app/uap_migrator/uap_readonly`）
  ④ STEP1B_SCHEMA_TEST_MATRIX.md:118「SEC1 | uap_app（DML）无 DDL 权限；uap_migrator 仅迁移窗口；uap_readonly 只读」
性质 = **design-vs-decision delta**（非 §7.2 三类冲突）：上述文档陈述"三角色 + `uap_readonly` 只读"，
  而 `D-OP101-01` 采用 `RM-D`（含第四角色 `uap_seed`）、`D-OP101-06` 将 `uap_readonly` **DEFER**。
处置 = **登记**（`CORE §13` 仍为**目标态**、`RM-D` 为其**扩展** + `uap_readonly` 分阶段 ⇒ 非矛盾，属**分阶段口径差异**）；
  正式现行口径声明与文本同步**属 P13 / OPEN-P10-1 实施契约轮**。
本 轮 = **未修改**上述 4 个文件（**不在本轮授权写入面内**，授权仅限 `PLATFORM_DECISION_LOG.md`）。
```

## L.5 `CF` 处置

```text
CF-1（词表 A–E 与候选 CP-F 的口径差异）= **RESOLVED** —— 由 `D-OP101-05` 以 `CUSTOM DECISION` 明文指定 `CP-F` 承载
CF-2（`P10 implementation = NOT AUTHORIZED` 的读法）= **登记**（前瞻语义：不得再执行 P10 实施动作；P10 已于 `0013` 验收）
CF-3（4 行 design-vs-decision delta）= **新增登记**（见 L.4；本轮不改，待实施契约轮）
```

## L.6 冲突终态

```text
本组冻结后：**无新冲突**（ACTIVE vs FROZEN 0 · FROZEN vs FROZEN 0 · SCHEMA vs DECISION 0）
残余 = `CF-3` 的 4 行**分阶段口径差异**（已登记、不阻塞冻结）
`D-P10-13` 的 `OPEN-P10-1` 开放项 = **CLOSED**（指针见其记录下方；其正文未改）
```

## L.7 本轮边界（**逐项实测**）

```text
允许写入面 = 仅 docs/architecture/PLATFORM_DECISION_LOG.md
  纯插入 1 = `# OPEN-P10-1 Canonical Model — D-OP101-01 … D-OP101-14`（含总表 + 不变量与前置关系 + 14 条记录 + 2 段 CUSTOM 原文 + CC-7 条件）
  纯插入 2 = `D-P10-13` 记录下方**指针行**（append-only）
  纯追加 1 = `# 附录 L — OPEN-P10-1 冻结状态汇总`（EOF）
  纯追加 2 = 新增 1 条 END 行（旧 END 行**不删**）
未执行（= 0）：CREATE ROLE · GRANT · REVOKE · ALTER ROLE · ALTER OWNER · CREATE|ALTER|DROP FUNCTION · C2 修改 ·
  0007 修改 · 0016 migration 创建 · 0017 migration 创建 · DDL · DML · seed INSERT · runtime 修改 ·
  test/config/code 修改 · alembic upgrade · alembic downgrade · commit · tag · push
不变量：既有 `D-*` 正文**零改写** · 无删除 · 无 supersede · 无章节重排 · 无格式统一 · 未顺手修改其他 architecture docs
0007 sha256 = 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef（未变）
C2 = unchanged（活体 `pg_get_functiondef`：`INSERT` 段无条件 `RAISE`，无身份判据；触发器 `31|O|0`）
OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED · P13 IMPLEMENTATION = NOT AUTHORIZED
```

## L.8 冻结状态

```text
OPEN-P10-1 DECISION FREEZE = **FROZEN**
Decision carrier write      = **COMPLETE**
⇒ 停止。等下一轮**独立**的 `OPEN-P10-1 IMPLEMENTATION PREP`；本组**不得**被解释为实施授权。
```

**END OF PLATFORM_DECISION_LOG（OPEN-P10-1 Decision Freeze · `D-OP101-01`…`D-OP101-14` 写入并置 `FROZEN` ⇒ `D-OP101` 共 **14** 条：14 `FROZEN` + 0 `DEFERRED` + 0 `SUPERSEDED`；`CUSTOM DECISION` **2**（03/05）· `CC-7` **批准**（附 6 条件，仍须独立 Implementation Authorization）· `CF-1` RESOLVED · `CF-3` 新增登记 4 行 · 附录 **L** 登记 · Charter §7 跨决策扫描 = 三类冲突 **0** · 命名空间现行计数 `D-PLAT 17 / D-AUTH 25 / D-AGENT 16 / D-P10 18 / D-P11 14 / D-P12 15 / D-P13 15 / D-OP101 14` · supersession 新增 = **0** · 既有 `D-*` 正文**零改写** · `D-P10-13` 仅**指针式 append** · `0016` = ABSENT · `0017` = ABSENT · `0007` = unchanged · `C2` = unchanged · `CREATE ROLE`/`GRANT`/`REVOKE`/`ALTER OWNER`/`DDL`/`DML` = 0 · commit/tag/push = 0 · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`；2026-09-27）**

---

# 附录 M — STEP 2 Runtime Slice 正式定义冻结登记（2026-09-27）

> **本区为追加登记（append-only）**：**不**修改 `D-PLAT-12` / `D-PLAT-12.a` / `D-PLAT-13` 正文；
> **不** supersede 任何既有 `D-*`；**不**删除任何历史行；**不**重排章节。
> 来源：Human 指令「STEP 2 — RUNTIME SLICE FORMAL DEFINITION FREEZE」（2026-09-27），
> 即 `D-PLAT-12.a` ③ 所称的 **PREP 门**。

## M.1 登记事项（编号冻结）

```text
previous : `P14_RUNTIME_SLICE` = tentative（D-PLAT-12.a ②）
current  : `P14_RUNTIME_SLICE` = **formally frozen**（本 PREP 门 · 2026-09-27）
路线名    : `STEP 2 — Runtime Slice`（正式冻结）
⇒ 自本附录生效起，`P14_RUNTIME_SLICE` 为本路线首阶段的正式阶段编号。
```

## M.2 为何以「附录」而非新 `D-PLAT-NN`

```text
指令原拟以 `D-PLAT-16` 作为登记 ID；实测：
  `D-PLAT-16` = readiness 迁移探针的独立短超时：2000 ms（2026-09-23 · FROZEN）—— **已占用**
  `D-PLAT-17` = Guard 门级划分与实施责任（2026-09-23 · FROZEN）—— **已占用**
⇒ 采用指令明确给出的替代路径：**在 `D-PLAT-12.a` 下新增正式登记附录**（本附录）。
⇒ 若 Human 希望另立顶层决策条目（例如 `D-PLAT-18`），须另行授权追加；本轮不自行编号。
```

## M.3 正式冻结内容（摘要 · 详文见对应文档）

```text
① 阶段编号      = `P14_RUNTIME_SLICE`（FROZEN）
② 文档集合      = 4 份（FROZEN）—— 见 `RUNTIME_DOCUMENT_SET_DECISION.md`
③ 附录 C 裁决   = C-8 RESOLVED（不加注 P06–P13 表）· C-9 RESOLVED（三层关系模型）
④ Scope Boundary = Included / Excluded 见 `P14_RUNTIME_SLICE_FORMALIZATION_GATE_REPORT.md` §5
⑤ PREP 入口条件 = 见同报告 §6
```

## M.4 不变量与边界（本附录自证）

```text
既有 `D-*` 正文 = 零改写 · 无删除 · 无 supersede · 无章节重排
本轮写入面     = 本附录（EOF 纯追加）+ 1 条新 END 行 + `D-PLAT-12.a` 下方 1 个指针块（纯插入）
               + 2 份新文档（docs/architecture/）
未执行          = DDL / DML / migration / runtime code / services 目录 / API / schema /
               0018+ · P14 implementation 文件 · commit / tag / push
本附录不构成任何实施授权。P14 IMPLEMENTATION = NOT AUTHORIZED（保持）。
```

## M.5 冻结状态

```text
RUNTIME STAGE FORMALIZATION = **FROZEN**（阶段编号 + 文档集合 + C-8/C-9 + Boundary + PREP 入口条件）
⇒ 停止。等下一轮**独立**的 `P14 RUNTIME SLICE PREP`（按已冻结文档集合执行）。
```

---

**END OF PLATFORM_DECISION_LOG（STEP 2 Runtime Slice 正式定义冻结 · 附录 **M**（append-only）· `P14_RUNTIME_SLICE` 由 **tentative → formally frozen**（`D-PLAT-12.a` ③ 的 PREP 门，2026-09-27）· 文档集合 4 份已冻结 · 附录 C `C-8` = RESOLVED（不加注 P06–P13 表）· `C-9` = RESOLVED（Schema → Authorization/Data Baseline → Runtime 三层关系）· `D-PLAT-16`/`D-PLAT-17` 已占用 ⇒ 采附录登记路径 · 既有 `D-*` 正文**零改写** · supersession 新增 = 0 · DDL/DML/migration/runtime = 0 · commit/tag/push = 0 · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**

---

# 附录 N — P14 Runtime Slice Decisions（2026-09-27 · HUMAN DECISION 登记）

> **本区为追加登记（append-only）**：**不**修改任何既有 `D-*` 正文；**不**删除历史；
> **不**重排章节；每项保留 OQ ID 并标记 `HUMAN DECISION`。
> 来源：Human 指令「P14 HUMAN DECISION REGISTRATION → CONTRACT SYNC → FREEZE」（2026-09-27）。
> 对应载体：`P14_HUMAN_DECISION_SHEET.md`（15 项）· `P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md`。

## N.1 计数

```text
P14 决策共 **15** 条：FROZEN 15 · DEFERRED 0 · REJECTED 0 · unresolved 0
  组成：Meta 2（ADD-2 · ADD-1）+ OQ 13（OQ-P14-01 … OQ-P14-13）
⇒ P14 DECISION COMPLETION = COMPLETE · P14 DECISION FREEZE = FROZEN
```

## N.2 逐项登记（HUMAN DECISION）

### ADD-2 — 决策登记位置

```text
Context        : P14 决策的登记载体未定；PDL 为跨阶段 canonical carrier。
HUMAN DECISION : **PDL 新 Appendix**（即本附录 N）
Constraints    : append-only · 不改既有 D-* 正文 · 不删除历史
Consequences   : P14 决策以附录 N 为唯一权威登记；不启用"Contract 内附录"路径
Affected Scope : 决策载体（PDL）· 后续 P14 裁定的登记位置
```

### ADD-1 — Contract 载体

```text
Context        : 现有 P14 文档缺 F-4 实施规则载体（与 P13 先例存在落差）。
HUMAN DECISION : **独立 `P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md`**
Constraints    : 内容仅来自 Human Decision 与既有冻结事实；不得自行扩展
Consequences   : 文档集合 4 → 5；实施规则单一权威载体；与 P13 形态一致
Affected Scope : 文档集合 · 实施者阅读路径 · 验收边界
```

### OQ-P14-13 — runtime privilege boundary

```text
Context        : uap_app 仅持 5 项授权，对 15 张关键表零权限；写路径不存在。
HUMAN DECISION : **OPTION B — Trusted Internal Service Boundary**
规则           : · uap_app 保持当前最小权限
                 · 不授予宽泛 DB 写权限
                 · Runtime 不使用 uap_migrator
                 · Runtime 使用独立 runtime / trusted service principal
                 · 新 DB role / GRANT / privilege **不并入本轮** Runtime implementation
                 · 新 privilege 必须**另开 Privilege / Security Gate**
Constraints    : D-OP101-07（未获新决策前不得扩权）· OI-G-1 · 本路线不新增 GRANT
Consequences   : 写路径经受信内部边界；uap_app 与授权面保持不变；
                 新 principal 的创建与授权属独立 Gate（P14 PRIVILEGE PRECONDITION）
Affected Scope : runtime 权限面 · 身份边界 · 验收 PRV-1…PRV-6
```

### OQ-P14-12 — C2 / CC-7 trust boundary usage

```text
Context        : C2 经 CC-7 改写，受信分支仅对 uap_migrator 放行。
HUMAN DECISION : **CC-7 / C2 仅用于 migration trust boundary**
Runtime 规则   : · 不绕过 C2 · 不模拟 uap_migrator · 不继承 migration privilege
Constraints    : D-P13-03 · D-P13-15（Does not authorize 不含对 Runtime 的授权）· D-OP101-05
Consequences   : Runtime 与 registry 完全解耦；C2 保持现状（md5 不变）
Affected Scope : 安全边界 · 验收 SEC-2 / IDL-5
```

### OQ-P14-01 — identity onboarding flow

```text
HUMAN DECISION : **Service-mediated staged onboarding**
流程           : pending → identity verification → credential/device verification → activation/session
规则           : 客户端不得直接访问 DB · bootstrap 与普通 onboarding 分离
Constraints    : D-P13-06 · D-PLAT-11①/②（禁第二套 dev bootstrap 路径）· D-P13-13
Consequences   : onboarding 经受信服务边界；客户端仅与 API 交互
Affected Scope : users / identities / sessions 建立路径 · 验收 IDF-1 / IDL-1
```

### OQ-P14-02 — credential lifecycle

```text
HUMAN DECISION : **Credential 独立生命周期**
规则           : credential 隶属于 identity · secret 只存 **Argon2id hash** ·
                 rotation · revoke · expire · 禁止 plaintext · 禁止 secrets 写日志
Constraints    : D-P13-13（明文/可逆/伪造 = 0）
Consequences   : 凭据与其生命周期独立于 identity 行；日志面需过滤 secret
Affected Scope : credentials 存储与校验 · 审计/日志面 · 验收 SEC-4 / IDL-2 / IDL-3 / AUDX-5
```

### OQ-P14-03 — device / user association

```text
HUMAN DECISION : **1 User : N Device** 且 **1 Device : 1 User**
规则           : 必须显式 enrollment / challenge · Device revoke 时**同事务**撤销其 active sessions
Constraints    : D-AUTH-18（identity 词汇 ≠ authorization subject）· 不新增 schema
Consequences   : 设备绑定与撤销纳入同一事务边界；会话随设备撤销同步失效
Affected Scope : devices / identities / sessions · 验收 IDF-3 / IDL-6
```

### OQ-P14-04 — permission check location

```text
HUMAN DECISION : **Centralized authorization precheck + Service / use-case mandatory enforcement**
规则           : handler 不承载业务授权决策
Constraints    : D-AUTH-16（分层冻结）· D-AUTH-12（FAIL CLOSED）
Consequences   : 判定集中前置 + use-case 强制双重保障；handler 保持薄
Affected Scope : authorization 判定链 · services/authorization · 验收 AUT-4
```

### OQ-P14-05 — policy enforcement boundary

```text
HUMAN DECISION : **Application / Service authorization boundary**
规则           : default deny · deny precedence · ABAC · **P14 不使用 DB RLS 作为主授权机制**
Constraints    : D-AUTH-07 / D-AUTH-12 · Runtime Excluded = schema evolution
Consequences   : 强制面在应用/服务层；DB 层仅保留既有触发器；无 schema 变更
Affected Scope : authorization runtime · 验收 AUT-1…AUT-4 / SEC-2
```

### OQ-P14-06 — API boundary

```text
HUMAN DECISION : **apps/api = transport / adaptation；services = use-case orchestration**
规则           : handler 不直接 SQL
Constraints    : D-PLAT-01/03/04/05 · G-2 / G-3 硬门
Consequences   : 传输与业务编排分离；SQL 仅经 services
Affected Scope : API 层职责 · services 调用链 · 验收 ABC-4（间接）
```

### OQ-P14-07 — service ownership（PDL 附录 C 的 C-5）

```text
HUMAN DECISION : services/ 负责 = use-case orchestration · transaction boundary ·
                 persistence coordination
                 domains = business rules · contracts；**domains 不依赖具体 services**
Constraints    : D-PLAT-01/03 · D-PLAT-03.a（domains → core 允许，反向禁止）
Consequences   : services 成为事务与持久化协调的唯一层；domains 保持自治契约
Affected Scope : services/ 结构（C-5 收敛）· domains 契约（C-6 方向）· 验收 ABC-4
```

### OQ-P14-08 — failure handling

```text
HUMAN DECISION : **Fail-closed**；错误必须分类；事务失败必须 rollback
Retry 规则      : 仅幂等 / 安全场景 · bounded · **no blanket retry**
Constraints    : D-AUTH-12 · D-PLAT-16（readiness 不重试不降级先例）
Consequences   : 失败即拒绝；重试面受限且需幂等保证
Affected Scope : 错误分类体系 · 事务边界 · 验收 FAL-1…FAL-3 / FLM-2…FLM-4
```

### OQ-P14-09 — bootstrap process

```text
HUMAN DECISION : **Bootstrap = local operator-controlled CLI**
规则           : explicit invocation · one-time initialization · bootstrap state lock ·
                 无公开网络 bootstrap endpoint · 完成 bootstrap 后进入 normal onboarding
Constraints    : R4/R5（FROZEN）· D-P13-07（P13 零 PM 写入）
Consequences   : 平台初始化仅经本地 CLI；网络面不暴露 bootstrap
Affected Scope : CLI 形态 · platform_state / platform_memberships 写入路径 ·
                 验收 OPS-3 / AUD-3 / AUDX-2
```

### OQ-P14-10 — deployment model

```text
HUMAN DECISION : **Single-host baseline + container-friendly**；无强制 orchestration dependency；
                 未来允许 multi-instance expansion
Constraints    : D-PLAT-15 v2（构建期只读工件）· D-PLAT-17 ⑦（不建 CI）
Consequences   : 基线部署为单机容器友好形态；扩展路径保留但不强制
Affected Scope : 部署拓扑 · secret 注入 · 验收 OPS-4
```

### OQ-P14-11 — observability

```text
HUMAN DECISION : **Vendor-neutral structured observability**
内容           : request ID · correlation ID · logs · metrics · trace hooks
禁止           : secrets · sensitive payloads
规则           : operational logs 与 audit logs **分离**
Constraints    : D-PLAT-14/16（readiness 语义）· 安全基线（不泄密）
Consequences   : 观测面结构化且厂商中立；审计面与运维日志不混用
Affected Scope : 日志/指标/追踪接入点 · 审计边界 · 验收 OPS-4 / AUD-1 / AUDX-5
```

## N.3 不变量与边界

```text
既有 `D-*` 正文 = 零改写 · 无删除 · supersession 新增 = 0
本轮未执行     = GRANT / REVOKE / CREATE ROLE / DDL / DML / migration / runtime code
uap_app        = 保持现状（5 项授权 + schema USAGE · CREATE = false）
uap_migrator   = 仅 migration 身份（不被 runtime 使用）
新 privilege    = 不并入本轮；须另开 Privilege / Security Gate（见 N.4）
P14 IMPLEMENTATION = **NOT AUTHORIZED**（本附录不构成实施授权）
```

## N.4 Privilege Precondition 指针

```text
完整定义见 `P14_RUNTIME_SLICE_IMPLEMENTATION_CONTRACT.md` 的
「P14 PRIVILEGE PRECONDITION」章节（状态 = PRECONDITION / SEPARATE SECURITY GATE）。
```

---

**END OF PLATFORM_DECISION_LOG（P14 Runtime Slice Decisions · 附录 **N**（append-only）· 15 项 HUMAN DECISION 登记 · `ADD-2` = PDL 新 Appendix · `ADD-1` = 独立 Contract · `OQ-P14-13` = OPTION B（Trusted Internal Service Boundary）· `OQ-P14-12` = CC-7 仅 migration trust boundary · 既有 `D-*` 正文**零改写** · supersession 新增 = 0 · GRANT / CREATE ROLE / DDL / DML / migration / runtime = 0 · uap_app 权限面未变 · `P14 IMPLEMENTATION = NOT AUTHORIZED`；2026-09-27）**

---

# 附录 O — P14 PRIVILEGE / SECURITY HUMAN DECISION（2026-09-27 · canonical registration）

> **本区为 append-only canonical registration**：**不**修改任何既有 `D-*` 正文；
> **不**修改既有 `附录 A–N` 正文；**不**删除；**不**重排；**不** reformat。
> 授权来源：Human 指令「P14 — SECURITY CANONICAL REGISTRATION + IMPLEMENTATION GATE PREPARATION」（2026-09-27）。
> 权威载体：`P14_PRIVILEGE_SECURITY_HUMAN_DECISION_SHEET.md`（**HUMAN DECISION RESOLVED** ·
> Resolution Registry 为逐项字段记录）。

## O.1 计数

```text
P14 Privilege / Security Decision 共 **14** 条：resolved 14 · unresolved 0 · UNKNOWN 0
SEC-P14-01 … SEC-P14-14（与 Decision Sheet 的 14 个 ID **一一对应**）
⇒ `Security Decision = FROZEN` · `Security Implementation = NOT STARTED`
⇒ `P14 IMPLEMENTATION = NOT AUTHORIZED`
```

## O.2 逐项 canonical 登记

### SEC-P14-01 — Runtime Principal Model

```text
DECISION : **DEDICATED RUNTIME PRINCIPAL**
明文     : · Runtime **不复用** `uap_app`
           · Runtime **不复用** `uap_migrator`
           · Runtime **不复用** `uap_seed`
           · Runtime principal **独立**
关联     : Contract §12 PB-1/PB-2/PB-3/PB-4 · OQ-P14-13 = OPTION B · D-OP101-07/08
```

### SEC-P14-02 — Runtime Trust Boundary

```text
DECISION : **TRUSTED INTERNAL SERVICE BOUNDARY**
明文     : · Runtime principal 属 **Runtime trusted internal service boundary**
           · migration 与 Runtime **分离**
           · seed 与 Runtime **分离**
           · bootstrap 与 Runtime **分离**
           · **不绕过 C2 / CC-7**
关联     : Contract §2 SB-1/SB-2/SB-3 · TR-1 / TR-2
```

### SEC-P14-03 — Runtime Required Read Scope

```text
DECISION : **EXPLICIT REQUIRED-READ ALLOWLIST**
明文     : · 只有 Required read 才允许进入 Runtime access surface
           · **UNKNOWN → DENY**
           · **禁止未来预授权**
关联     : Contract §6 AC-1/AC-4 · §12 PB-2
```

### SEC-P14-04 — Runtime Required Write Scope

```text
DECISION : **USE-CASE + OPERATION EXACT WRITE**
明文     : · 权限按 **use-case 和 operation** 精确授予
           · **不得** broad CRUD
           · **不得** all-table write
关联     : Contract §3/§4/§5/§6/§8 · §12 PB-2
```

### SEC-P14-05 — Tenants / Spaces

```text
DECISION : **TENANTS / SPACES = SELECT ONLY**
明文     : · 不得将 administration 能力混入普通 Runtime
           · 不负责 tenant/space creation / deletion / mutation
           · 不允许跨 tenant 任意扫描
关联     : D-P13-05 · Contract §12
```

### SEC-P14-06 — Memberships

```text
DECISION : **MEMBERSHIP = SERVICE-MEDIATED**
明文     : · 普通 membership 与 platform membership **分离**
           · 不得 handler direct SQL；不得等价为 platform administration
关联     : D-P13-07 · R4 / R5 · Contract §3 / §5
```

### SEC-P14-07 — Events / Resources

```text
DECISION : **EVENTS / RESOURCES = S/I/U USE-CASE LIMITED**
明文     : · SELECT / INSERT / UPDATE 允许（仅实际 use-case）
           · 默认 **DELETE = DENY**（仅经独立 Security Review 的硬删除需求可追加）
关联     : P10（events = outbox）· Contract §12
```

### SEC-P14-08 — Credential Lifecycle

```text
DECISION : **NO PHYSICAL CREDENTIAL DELETE**
明文     : · 生命周期 = `issue → active → rotate → revoke/expire`
           · 禁止 plaintext storage / logging、secret 进入 audit payload / exception / 普通日志
关联     : **OQ-P14-02 核心语义不变** · Contract §4
```

### SEC-P14-09 — Resource Permission Write Side

```text
DECISION : **RESOURCE_PERMISSIONS WRITE = DENY**
明文     : · Runtime **不得拥有通过 resource permission mutation 改变自身
             authorization boundary 的能力**
           · 授权模型 mutation 属更高权限 administration / security boundary
           · 不得建立 self-escalation 闭环
关联     : Contract §6 AC-3/AC-6 · §12
```

### SEC-P14-10 — Authorization Read Path

```text
DECISION : **HYBRID AUTHORIZATION READ PATH**
明文     : `Central Authorization Service` + `Restricted Runtime DB Read`
           保留：· default deny · deny precedence · ABAC · centralized enforcement
                 · **handler 不自行决定 authorization**
关联     : Contract §6 AC-1…AC-5 · §7 SC-1/SC-2 · D-AUTH-07 / D-AUTH-12 / D-AUTH-16
```

### SEC-P14-11 — Bootstrap Execution Identity

```text
DECISION : **DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL**
明文     : · **不使用** `uap_migrator`
           · **不使用** Runtime principal
           · **不使用** `uap_app`
           · bootstrap authority 生命周期与 Runtime principal 分离
关联     : R4 / R5 · D-P13-07 · Contract §8 · §12 PB-3
```

### SEC-P14-12 — Bootstrap Credential Source

```text
DECISION : **LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT**
明文     : · secret **不进入** CLI argument
           · **不** hard-code
           · **不进入**日志
           · **不进入** audit
           · **不进入**普通 persistent storage
           · 允许受控：`secret file / container secret`
关联     : OQ-P14-02 · 安全基线
```

### SEC-P14-13 — platform_memberships / platform_state

```text
DECISION : **BOOTSTRAP-OWNED INITIALIZATION**
明文     : · `platform_memberships` 与 `platform_state` 由 **bootstrap authority** 完成初始化
           · Normal Runtime：`READ MAY BE REQUIRED` · **`WRITE = DENY`**
           · 不得重新执行 bootstrap · 不得绕过 one-time state lock
           · **Bootstrap Authority ≠ Runtime Authority**
关联     : R4 / R5（FROZEN）· D-P13-07 · Contract §8 BR-7
```

### SEC-P14-14 — Privilege Grant Strategy

```text
DECISION : **EXACT LEAST-PRIVILEGE GRANT STRATEGY**
明文     : · object-level · operation-level · exact grants
           · necessary sequence / function / view only
           · **no `GRANT ALL`** · **no broad schema write** · **no inheritance-based expansion**
关联     : D-OP101-07（minimum required set）· D-OP101-08（runtime 不持 DDL）· Contract §12 PB-2/PB-5/PB-6
```

## O.3 Decision Correspondence（ID 与模型命名对应）

```text
本附录的 ID 集合 = `SEC-P14-01 … SEC-P14-14`
  ⇒ 与 `P14_PRIVILEGE_SECURITY_HUMAN_DECISION_SHEET.md` 的 14 个 ID **一一对应**
  ⇒ 无「一个 Decision 两个 ID」· 无「一个 ID 两套语义」

模型命名对应（不产生重复决策）：
  最终 resolution      = **DEDICATED RUNTIME PRINCIPAL**（= 本 Sheet 的 MODEL C）
  + 信任边界定位        = **TRUSTED INTERNAL SERVICE BOUNDARY**（SEC-P14-02）
  ⇒ 二者为**同一方案的两个侧面**（独立 principal 作为受信内部 Service Boundary 的数据库身份）
  ⇒ 历史文档中的 MODEL A / MODEL B 命名**仅为候选分析标签**，
    不构成独立 Decision，也不与本附录的 SEC-P14 产生重复语义。
```

## O.4 不变量与边界（本附录自证）

```text
既有 `D-*` 正文            = 零改写
既有 `附录 A–N` 正文        = 零改写
删除 / 重排 / reformat      = 0
本轮 DB 变更                = 0（CREATE ROLE / ALTER ROLE / GRANT / REVOKE / DDL / DML / migration = 0）
本轮 runtime code           = 0 · commit / tag / push = 0
`Security Implementation`   = NOT STARTED（须另行授权）
```

---

**END OF PLATFORM_DECISION_LOG（P14 PRIVILEGE / SECURITY HUMAN DECISION · 附录 **O**（append-only canonical registration）· `SEC-P14-01…14` = **FROZEN**（14 resolved · 0 unresolved · 0 UNKNOWN）· SEC-01 = DEDICATED RUNTIME PRINCIPAL · SEC-02 = TRUSTED INTERNAL SERVICE BOUNDARY · SEC-03/04 = explicit allowlist / exact write · SEC-05 = SELECT ONLY · SEC-06 = service-mediated · SEC-07 = S/I/U（DELETE DENY）· SEC-08 = NO PHYSICAL DELETE · SEC-09 = resource_permissions write DENY · SEC-10 = HYBRID read path · SEC-11/12/13 = dedicated one-time bootstrap principal / local operator secret input / bootstrap-owned initialization · SEC-14 = EXACT LEAST-PRIVILEGE GRANT · 既有 `D-*` 与 `附录 A–N` **零改写** · DB / role / grant / revoke / migration / runtime = 0 · `Security Implementation = NOT STARTED` · `P14 IMPLEMENTATION = NOT AUTHORIZED`；2026-09-27）**

---

# 附录 P — P14 WAVE 2 DECISION RESOLUTION（2026-09-28 · canonical registration）

> **本区为 append-only canonical registration**：**不**修改任何既有 `D-*` 正文；
> **不**修改既有 `附录 A–O` 正文；**不**删除；**不**重排；**不** reformat。
> 授权来源：Human 指令「P14 — WAVE 2 HUMAN DECISION FREEZE」（2026-09-28）。
> 权威载体：`P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET.md`（Resolution Registry）。
> 编号 = **附录 P**（写入前实测：PDL 既有附录止于 `O`；`附录 P/Q/…` 均未被占用）。

## P.1 计数

```text
Wave 2 Human Decision 共 **36** 条：resolved 36 · unresolved 0 · UNKNOWN 0
  Batch 0 Governance/Root   : SCOPE-W2-01 · VOC-W2-01…04                （5）
  Batch 1 Identity          : ID-W2-01…05                              （5）
  Batch 2 Device            : DV-W2-01…05                              （5）
  Batch 3 Session           : SS-W2-01…05                              （5）
  Batch 4 Context           : CTX-W2-01…04                             （4）
  Batch 5 Authorization     : AUTH-W2-01…03                            （3）
  Batch 6 API               : API-W2-01…04                             （4）
  Batch 7 Security          : SEC-W2-01…05                             （5）
⇒ `Wave 2 Decision = FROZEN` · `Wave 2 Implementation = NOT STARTED`
⇒ `Wave 2 Authorization = REQUIRED`（W2-AUTH-01…07 未勾选）
```

## P.2 记法

```text
Selected = 该 Decision 在 Sheet 中的**实际 option label**（A/B/C/D 或 CUSTOM）
Basis    = EXPLICIT（Human 明文）/ DERIVED（由 Human 明文条款推导，引用条款号）
           / REPURPOSED（Human 以本 ID 承载了与 Sheet 原问题不同的裁定内容 —— 明确标注）
Contract Impact / Schema Impact = 对既有冻结契约与 0017 schema 的影响（本附录全部为
                                  "0 改写"或"经显式 mapping"）
```

---

## P.3 Batch 0 — Governance / Root

```text
SCOPE-W2-01 ｜ Selected = A/B/C/D 之外：**REPURPOSED（§三）+ DERIVED（节点组成）**
  Resolution  ：Wave 2 Domain / Persistence Boundary 采用 **Persistence Adapter /
                Anti-Corruption Mapping**；**不修改既有 0017 schema**。
                Domain ↔ persistence vocabulary 可不同，但 mapping 必须显式、确定、可测试；
                禁止隐式字符串转换。
                链条冻结：Domain → Repository Contract → Persistence Mapping → 0017 Schema
                （禁止 Domain 强迫 Schema 改名/改状态/改聚合）。
  Basis       ：EXPLICIT（§三）；节点组成（Identity+Device+Session+API 同轮）
                = DERIVED（§三十一 明列 API Wave 2 scope；§九–§三十七 覆盖全链）
  AFFECTED    ：Wave 2 全链 · Repository Contract · Persistence Mapping · Acceptance
  IMPL CONSEQ ：Wave 2 必须实现 anti-corruption mapping 层（可作为 repository/adapter 的一部分）
  RELATED     ：RTA-10 = OPTION B · Wave 1 Persistence Adapter（ACCEPTED）· D-1…D-9
  Contract    ：既有 core 契约 0 改写 ｜ Schema：0 变更

VOC-W2-01 ｜ Selected = **C（双根显式映射）**
  Resolution  ：保留 Domain 的 Identity 语义中心；**不**把 `users` 提升为新的 Domain 身份语义核心；
                但在 Service / Persistence 层以 `users.id` 作为实际持久化 anchor。
                允许后续出现 `UserRef` / `UserId` / `UserSnapshot` 等明确基础类型 / DTO；
                禁止第二套身份模型或 `UserAuthEngine`。
                Identity onboarding 必须能在**单一 use-case transaction** 内协调
                users + identities + credentials + devices + sessions；
                不得因为"没有 User Domain object"而让 Handler 直接操作 `users`。
  Basis       ：EXPLICIT（§四 / §五）
  AFFECTED    ：Identity · Device · Session · Persistence anchor · Authenticated Context
  IMPL CONSEQ ：需显式 mapping（Domain Identity ↔ users.id anchor）；handler 不得触 users
  RELATED     ：D-1 · Wave 1 Transaction Boundary · RUNTIME-G-05
  Contract    ：core 契约 0 改写 ｜ Schema：0 变更

VOC-W2-02 ｜ Selected = **A（以 0017 持久化词表为准，Domain enum 经 explicit mapping）**
  Resolution  ：`0017` persisted credential vocabulary = Persistence Truth；**不修改 schema CK**。
                Wave 2 第一期只实现 `password` 作为正常 interactive local credential；
                `api_key` / `recovery_code` / `device_cert` / `otp` 保持 schema-valid，
                但不纳入本轮 normal login flow。
                Domain 如需 enum，必须经 `Domain CredentialType ↕ Persistence credential.type`
                的显式 mapping；**禁止** domain enum 值未经 mapping 直接写入 DB。
  Basis       ：EXPLICIT（§七）
  AFFECTED    ：Identity（凭据）· Persistence Mapping · Security（Argon2id）
  IMPL CONSEQ ：仅实现 password 路径；其余类型无实现路径（保持 vocabulary 有效）
  RELATED     ：D-2 · SEC-P14-08 · §三十三
  Contract    ：core/auth.CREDENTIAL_TYPES 保留为 Domain 词表，经 mapping 使用 ｜ Schema：0 变更

VOC-W2-03 ｜ Selected = **A（采用 0017 完整五态作为 persistence truth）**
  Resolution  ：`pending / active / untrusted / revoked / lost` 五态为 persistence truth；
                不把 Domain 缩成 3 态。
                应用语义：pending=未完成验证 · active=可正常认证 ·
                untrusted=存在但不满足正常信任条件 · revoked=永久撤销 · lost=丢失状态。
                `untrusted` **不得**自动等同 `active`；`lost` **不得**自动等同 `revoked`
                （除非既有 use-case 明确执行该转换）。
  Basis       ：EXPLICIT（§八）
  AFFECTED    ：Device · Session（device trust 判定）· Security
  IMPL CONSEQ ：device trust 判定必须区分 5 态；不得二值化为 active/not-active
  RELATED     ：D-3 · VP-1（live 复核）· §十六
  Contract    ：core/device.DEVICE_STATUS（3 态）为 Domain 子集，须经 mapping 表达 5 态 ｜ Schema：0 变更

VOC-W2-04 ｜ Selected = **C（两套并存 + 显式映射）**
  Resolution  ：`users.status` = pending → active → suspended / locked → active → deleted
                （`deleted` 继续为 soft-delete）；`identities.status` = unverified → active →
                suspended → revoked。
                **禁止**新增 persisted status（如 `verified` / `onboarding`）。
                "verification in progress" 只能是 **Application Workflow State**，
                不得写入 schema status。
  Basis       ：EXPLICIT（§九 / §十 / §十一）
  AFFECTED    ：Identity · Session（active 判定）· Acceptance
  IMPL CONSEQ ：需两张显式状态映射表（user / identity），无第三套状态机
  RELATED     ：D-4 · D-6 · §十一（Onboarding State Mapping）· VP-4
  Contract    ：core/identity.Identity.status（无枚举）经 mapping 映射到 identities.status ｜ Schema：0 变更
```

---

## P.4 Batch 1 — Identity

```text
ID-W2-01 ｜ Selected = **A（public onboarding path）+ 约束**
  Resolution  ：允许 public onboarding entry；但匿名 caller **不得**获得超出 onboarding
                的权限；必须受 fail-closed 与 abuse/replay 边界约束（SEC-W2-01…03）。
  Basis       ：DERIVED（§三十一 明列 "identity onboarding/authentication entry" 为允许的
                API 面 ⇒ onboarding 对外可达；§三十六 fail-closed；§三十七 要求无 ACTIVE UNKNOWN）
  AFFECTED    ：Identity · API · Security · Acceptance
  IMPL CONSEQ ：onboarding 入口须有 abuse 边界与重复创建处理（见 ID-W2-03 / SEC-W2-01）
  RELATED     ：SEC-W2-01…03 · ID-W2-03 · SEC-P14-03（allowlist · UNKNOWN→DENY）
  Contract    ：0 改写 ｜ Schema：0 变更

ID-W2-02 ｜ Selected = **A（采用 VOC-W2-04 选定集合）**
  Resolution  ：identities.status = unverified → active → suspended → revoked；
                creation = `unverified`；successful verification = `active`；
                temporary security suspension = `suspended`；permanent invalidation = `revoked`。
                **禁止** `pending` 作为 identities.status 新值。
  Basis       ：EXPLICIT（§十）
  AFFECTED    ：Identity · Session（active 判定）· Acceptance
  IMPL CONSEQ ：identity 状态机固定为 4 态；verification 过程状态留在应用层
  RELATED     ：VOC-W2-04 · D-4 · §十一
  Contract    ：0 改写 ｜ Schema：0 变更

ID-W2-03 ｜ Selected = **A（全局唯一）** · normalization = **trim（应用层）+ lower（DB 已强制）**
           · case sensitivity = **不敏感**
  Resolution  ：唯一性沿用 0017 既有唯一索引（全局 · lower · soft-delete 后释放）；
                不采用 tenant-scoped 唯一性（与既有索引冲突）。
  Basis       ：EXPLICIT（§一 "0017 = persistence truth"）+ 本轮 live 复核
                （`uq_users_email` / `uq_users_username` = UNIQUE(lower(...)) WHERE deleted_at IS NULL）
  AFFECTED    ：Identity · Persistence · Security（重复创建）· Acceptance
  IMPL CONSEQ ：应用层 trim；DB 负责 lower 唯一；软删除后 identifier 可复用
  RELATED     ：VP-4 · SEC-W2-01 · §十二（device 侧为 per-user 唯一，两者尺度不同）
  Contract    ：0 改写 ｜ Schema：0 变更（若未来需 tenant 范围唯一 ⇒ 独立 Schema Decision）

ID-W2-04 ｜ Selected = **C（两者必填且需一致）**
  Resolution  ：credential 同时绑定 identity 与 user，且二者必须一致（应用层校验）。
  Basis       ：EXPLICIT（§六 User → Identity → Credential）+ 0017 强制
                （`credentials.identity_id` 与 `credentials.user_id` 均 NOT NULL）
  AFFECTED    ：Identity · Session · Persistence · Security
  IMPL CONSEQ ：写入时必须同时提供两个 FK 且校验一致；Argon2id（§三十三）
  RELATED     ：VOC-W2-02 · §三十三 · SEC-P14-08
  Contract    ：0 改写 ｜ Schema：0 变更

ID-W2-05 ｜ Selected = **CUSTOM（revoke 传播矩阵）**
  Resolution  ：identity → `revoked`（permanent invalidation）；凭据 revoke；
                **同一事务**内撤销该 identity 的 related active sessions；
                `device` 状态**不**由 identity revoke 自动改写（依 §八 状态独立性）。
                矩阵来源 = §二十一（revoke 触发源）+ §三十六 SEC-W2-04（传播要求）。
  Basis       ：EXPLICIT（§二十一 · §三十六 SEC-W2-04）；"device 不自动连带"为
                DERIVED（§八 明确 untrusted/lost/revoked 相互独立，§三十六 未列 identity→device）
  AFFECTED    ：Identity · Device · Session · Transaction Boundary · Security
  IMPL CONSEQ ：identity revoke 与 session revoke 必须同事务；device 行不改写
  RELATED     ：SS-W2-03 · DV-W2-04 · SEC-W2-04 · DC-19（既有原子性要求）
  Contract    ：0 改写 ｜ Schema：0 变更
```

---

## P.5 Batch 2 — Device

```text
DV-W2-01 ｜ Selected = **B（authenticated/eligible user + enrollment challenge + device verification）**
  Resolution  ：Device enrollment = Authenticated / Eligible User + Enrollment Challenge +
                Device Verification → `devices.status = active`；
                创建时为 `pending`，验证成功后为 `active`；
                **不得**直接 INSERT `active` 绕过 challenge / verification。
  Basis       ：EXPLICIT（§十三）
  AFFECTED    ：Device · Identity · Security（replay）· Acceptance
  IMPL CONSEQ ：enrollment 必须实现 challenge + verification 两步；禁止直插 active
  RELATED     ：DV-W2-03 · SEC-W2-03（replay resistance）· VOC-W2-03
  Contract    ：0 改写 ｜ Schema：0 变更

DV-W2-02 ｜ Selected = **B（依赖既有 DB 约束 + 应用层补充）**
  Resolution  ：正式采用 **Per-user fingerprint uniqueness**（`UNIQUE(user_id, fingerprint)`）；
                不采用 global fingerprint uniqueness；Wave 2 不改变现有约束。
                跨用户出现相同 fingerprint：DB 允许；是否视为安全异常由
                application / device trust policy 判定。
                冻结：one device → one user · one user → many devices。
  Basis       ：EXPLICIT（§十二）
  AFFECTED    ：Device · Session · Security · Persistence
  IMPL CONSEQ ：应用层不得假设指纹全局唯一；重复指纹需按 trust policy 处理
  RELATED     ：VP-1（live 复核 `uq_devices_fingerprint`）· DV-W2-05
  Contract    ：0 改写 ｜ Schema：0 变更

DV-W2-03 ｜ Selected = **A（以既有 schema 载体承载 challenge）**
  Resolution  ：已有 schema 承载方式优先；**禁止**因缺少理想独立表而自动新增
                `device_challenges` 之类对象。
                若实现阶段证明必须独立 schema ⇒ `SCHEMA DEPENDENCY` → **STOP** →
                独立 Schema Decision（RTA-10 = OPTION B）。
  Basis       ：EXPLICIT（§十四）
  AFFECTED    ：Device · Security · Persistence · Test Governance
  IMPL CONSEQ ：challenge 短期持久化优先落在既有载体；不得新增表
  RELATED     ：SEC-W2-03 · SCHEMA_DEPENDENCY_REGISTER · §三十五
  Contract    ：0 改写 ｜ Schema：0 变更（当前）

DV-W2-04 ｜ Selected = **A（同事务原子撤销：status = revoked + active sessions = revoked）**
  Resolution  ：device → `revoked`，且该 device 的**全部 active sessions** → `revoked`，
                二者必须在**同一个 Service Transaction** 内完成（atomic）；
                **不得**先提交 device revoke 再异步处理 session revoke。
  Basis       ：EXPLICIT（§十五）
  AFFECTED    ：Device · Session · Transaction Boundary · Security
  IMPL CONSEQ ：复用 Wave 1 Transaction Boundary；单事务内 UPDATE devices + UPDATE sessions
  RELATED     ：SS-W2-03 · SEC-W2-04 · DC-19 · Wave 1 §10/§12
  Contract    ：0 改写 ｜ Schema：0 变更

DV-W2-05 ｜ Selected = **A（旧设备继续有效；需显式 revoke）**
  Resolution  ：新设备加入**不**自动撤销旧设备（多设备并存）；需显式 revoke 才失效；
                并发 enrollment 的串行化 / 幂等语义须由实现按 SEC-W2-03
                （bounded lifetime · single-use · explicit consumption）落实。
  Basis       ：DERIVED（§十二 多设备模型 + §十八 granular revoke；§十六 明示
                lost→active 恢复另行明确且本轮不自动实现）
  AFFECTED    ：Device · Session · Security
  IMPL CONSEQ ：不实现 auto-kick；并发 enrollment 需幂等/单次消费语义
  RELATED     ：DV-W2-01/03 · SEC-W2-03 · §十六
  Contract    ：0 改写 ｜ Schema：0 变更
```

---

## P.6 Batch 3 — Session

```text
SS-W2-01 ｜ Selected = **A（service 层在已验证身份 + 已验证设备后创建）**
  Resolution  ：Normal human login session **MUST** have a verified device ⇒
                `device_id` 在 use-case 层 **REQUIRED**；schema 的 nullable **不改**。
                非 human / service identity 的 device-less session 保留为未来 capability，
                **不纳入**本轮 normal human login flow。
  Basis       ：EXPLICIT（§十七）
  AFFECTED    ：Session · Device · Identity · API · Security
  IMPL CONSEQ ：use-case 强制校验 device 存在且 trusted；schema 层不新增 NOT NULL
  RELATED     ：VP-3（live 复核 device_id 可空）· DV-W2-01 · VOC-W2-03
  Contract    ：core/session.SessionStore.create(identity_id, device_id, ttl) 保留 ｜ Schema：0 变更

SS-W2-02 ｜ Selected = **A（active → expired | revoked；使用既有附加字段）**
  Resolution  ：Session 状态固定为 `active / expired / revoked`（Domain 与 DB 一致）；
                **禁止**新增 `pending` / `verified` / `locked` 等 Session status。
                `replaced_by` 与 `absolute_expires_at` 纳入使用（见 SS-W2-05）。
  Basis       ：EXPLICIT（§十九 / §二十）
  AFFECTED    ：Session · Persistence · Acceptance
  IMPL CONSEQ ：状态机 3 态；不新建状态名
  RELATED     ：D-8（本项无分歧）· SS-W2-05 · VP-3
  Contract    ：与 core/session.SESSION_STATUS 一致 ｜ Schema：0 变更

SS-W2-03 ｜ Selected = **CUSTOM（granular revoke 矩阵）**
  Resolution  ：
                explicit logout        → 仅撤销该 session（granular）
                device revoke          → 该 device 的全部 active sessions（同事务 · §十五）
                identity revoke        → 该 identity 的 related active sessions（同事务 · §三十六）
                credential revoke      → 该凭据认证被拒 + 其相关 active sessions 撤销（§二十一）
                administrator revoke   → 按操作范围（granular 或 account-level）
                禁止把任意单个 session revoke 自动扩展成该 user 的全部 session revoke，
                除非触发的是 **identity / account-level 安全事件**。
  Basis       ：EXPLICIT（§二十一 + §三十六 SEC-W2-04 + §十五）
  AFFECTED    ：Session · Device · Identity · Security · Acceptance
  IMPL CONSEQ ：revoke API 必须显式区分 scope（session / device / identity / credential）
  RELATED     ：ID-W2-05 · DV-W2-04 · SEC-W2-04
  Contract    ：0 改写 ｜ Schema：0 变更

SS-W2-04 ｜ Selected = **B（每设备允许多 session）**
  Resolution  ：one user → many devices → **each device may have many sessions**；
                **不增加** `UNIQUE(device_id)`；**不做** "新登录自动踢掉旧登录"；
                Wave 2 必须支持 concurrent sessions + granular revoke。
  Basis       ：EXPLICIT（§十八）
  AFFECTED    ：Session · Device · Security · Acceptance
  IMPL CONSEQ ：并发会话为正常状态；revoke 需按 SS-W2-03 的 scope
  RELATED     ：VP-3（live 复核无唯一约束）· SS-W2-03
  Contract    ：0 改写 ｜ Schema：0 变更

SS-W2-05 ｜ Selected = **B（参数由部署配置提供；语义本轮冻结）**
  Resolution  ：继续采用 relative expiration（`expires_at`）+ absolute expiration
                （`absolute_expires_at`）双上限；relative 控制 idle / session lifetime，
                absolute 为最终上限；**refresh 不得无限延长 absolute expiry**。
                时钟 = UTC；revocation 传播 = **每请求校验（即时）**（依 §二十九 评估顺序）。
                具体秒数属部署配置（不写入 schema / 不写入 GUC 作为信任判据）。
  Basis       ：EXPLICIT（§二十）；时钟 UTC 与即时传播 = DERIVED（§二十九 评估顺序含
                "Session validity" 前置校验；§三十六 SEC-W2-04 要求遵守事务边界）
  AFFECTED    ：Session · Security · Observability · Acceptance
  IMPL CONSEQ ：双上限字段均使用；配置化 TTL；不得以 refresh 绕过 absolute
  RELATED     ：SS-W2-02 · §二十九 · CTX-W2-01
  Contract    ：core/session.create(..., ttl_seconds) 语义扩展为双上限（契约新增字段属 Wave 2 实现面）｜Schema：0 变更
```

---

## P.7 Batch 4 — Authenticated Context

```text
CTX-W2-01 ｜ Selected = **A（采用候选枚举；字段名按 §二十二 定为 authentication assurance）**
  Resolution  ：Authenticated Context 最小组成 =
                actor/user id · identity id · device id（仅非 human/service 可为空）·
                session id · tenant context · space context · **authentication assurance**。
                assurance 派生自 §二十九 的前置校验链
                （identity validity → device trust → session validity）。
  Basis       ：EXPLICIT（§二十二）；assurance 映射 = DERIVED（§二十九 评估顺序）
  AFFECTED    ：Context · Session · Authorization · API · Acceptance
  IMPL CONSEQ ：context 为 immutable request-scoped value object；assurance 非持久化
  RELATED     ：CTX-W2-04 · SS-W2-02/05 · AUTH-W2-01（§二十六）
  Contract    ：不改既有 core 契约 ｜ Schema：0 变更

CTX-W2-02 ｜ Selected = **CUSTOM（tenant / space fail-closed 矩阵）**
  Resolution  ：Authentication success ≠ tenant authorization；User 可为 1 → N tenants。
                tenant 无法确定 / 无 active membership / inactive membership ⇒ **DENY**
                （cross-tenant 无明确 active membership ⇒ DENY）。
                多 candidate ⇒ **禁止在 authorization 层隐式随机选 context**；
                Service 必须接收明确 context → 校验 membership → 再进入 authorization；
                仅当只存在唯一 active candidate 时，可由 service **deterministic resolve**；
                不得由 handler 自行选择。
                Space 同理：必须经 active membership；请求 context 不足 ⇒
                `context required` 然后 **fail-closed**。
  Basis       ：EXPLICIT（§二十三 / §二十四 / §二十五）
  AFFECTED    ：Context · Authorization · API · Security · Acceptance
  IMPL CONSEQ ：context 解析规则确定且可测；handler 不参与选择
  RELATED     ：AUTH-W2-02（§二十七/§三十）· SEC-W2-01（§三十六）· core.tenant/space
  Contract    ：复用 core/tenant + core/space（require_same_tenant）｜ Schema：0 变更

CTX-W2-03 ｜ Selected = **A（白名单）**
  Resolution  ：允许进入 observability 的字段白名单 =
                { correlation_id, session_id, device_id, identity_id, tenant_id, space_id,
                  subject_type, scope, decision_effect }；
                **禁止**任何 secret / hash / 凭据材料（logs / trace / metrics / audit /
                response / exception 全部适用）。
  Basis       ：EXPLICIT（§二十二 最小不可变快照 + §三十六 SEC-W2-02）
  AFFECTED    ：Observability · Security · Acceptance
  IMPL CONSEQ ：沿用 Wave 1 redaction / structured logging，不新增字段面
  RELATED     ：SEC-W2-02（§三十六）· Wave 1 Observability（ACCEPTED）
  Contract    ：0 改写 ｜ Schema：0 变更

CTX-W2-04 ｜ Selected = **A（context 仅携带标识；AuthorizationRequest 由 service 逐次构造）**
  Resolution  ：Context = **minimal immutable request-scoped representation**；
                禁止把 credential secret/hash、full user record、full device record、
                arbitrary memberships、authorization tables 塞入 request context。
  Basis       ：EXPLICIT（§二十二）
  AFFECTED    ：Context · Authorization · Service · Acceptance
  IMPL CONSEQ ：不预构造 AuthorizationRequest；不缓存判定；不预授权
  RELATED     ：SEC-P14-03（UNKNOWN→DENY · 禁止未来预授权）· AUTH-W2-01
  Contract    ：0 改写 ｜ Schema：0 变更
```

---

## P.8 Batch 5 — Authorization Integration

```text
AUTH-W2-01 ｜ Selected = **REPURPOSED（§二十六：role_permissions.effect divergence）**
  Resolution  ：Wave 2 authorization persistence path **只消费 `allow / deny`**。
                `REQUIRES_APPROVAL`：不转换为 allow；不转换为 deny；
                不塞入 `role_permissions.effect`；不修改 schema vocabulary；
                不创建第三套 effect enum。
                未来如需 approval semantics ⇒ 建立独立 Approval / Decision model。
                本轮 `REQUIRES_APPROVAL = OUT OF SCOPE / DEFERRED`。
  Supplementary（同 Batch 明文条款，无独立 ID）
                §二十七：复用 Stage 2；禁止 new authorization engine / new permission
                         vocabulary / second role evaluator / second ABAC evaluator。
                §二十八：normal human request 的 subject = authenticated user；
                         Identity / Device / Session 用于证明"who authenticated"，
                         不自动成为三个独立 authorization subjects；agent/service
                         subjects 保留既有模型。
                §二十九：评估顺序冻结 = Authentication → Identity validity → Device trust →
                         Session validity → Tenant membership → Space membership →
                         Stage 2 Authorization → Use-case；任一前置失败 ⇒ DENY / STOP。
  Basis       ：EXPLICIT（§二十六 / §二十七 / §二十八 / §二十九）
  AFFECTED    ：Authorization · Context · Service · API · Security · Acceptance
  IMPL CONSEQ ：effect 只读写 allow/deny；REQUIRES_APPROVAL 无实现路径（明确 deferred）
  RELATED     ：D-9（→ DEFERRED）· SEC-P14-10（HYBRID）· Wave 1 Authorization Integration
                Boundary（ACCEPTED）· core.permission.EFFECTS
  Contract    ：core.permission.EFFECTS 保留（REQUIRES_APPROVAL 标记 deferred）｜ Schema：0 变更

AUTH-W2-02 ｜ Selected = **A（确认：判定只在 service + Stage 2；handler 仅适配）**
  Resolution  ：API 为 transport / adaptation only；不得直接 SQL、不得直接决定 authorization、
                不得直接写 users/devices/sessions、不得自行 orchestration onboarding transaction。
                目标链路：HTTP → Authentication Adapter → Authenticated Context →
                Authorization → Service / Use-case → Repository。
                明确禁止：`Authentication → handler if role == admin`。
  Basis       ：EXPLICIT（§三十 + §二十七）
  AFFECTED    ：API · Service · Authorization · Security
  IMPL CONSEQ ：handler 无授权分支；强制点在 service
  RELATED     ：RUNTIME-G-04 / RUNTIME-G-05 · DL-2 · AUTH-W2-01
  Contract    ：0 改写 ｜ Schema：0 变更

AUTH-W2-03 ｜ Selected = **A（Wave 2 写 audit，限身份/设备/会话关键事件）**
  Resolution  ：Wave 2 参与审计写入，范围限 identity / device / session 关键事件；
                写点集中在 service 层；审计内容**不得**含 secret / hash / 凭据材料；
                不得修改审计不可变语义。
  Basis       ：DERIVED（§三十六 SEC-W2-02 明确约束 audit 面 ⇒ 审计参与本轮；
                §二十一 含 "security administration action"；§三十二 认证失败路径需可观测）
  AFFECTED    ：Authorization · Observability · Security · Acceptance
  IMPL CONSEQ ：使用既有 audit_logs INSERT 授权（无 UPDATE/DELETE）；payload 白名单
  RELATED     ：SEC-W2-02（§三十六）· SEC-P14-07 · Wave 1 ACCEPTANCE §17（SEC-5 原为 PLANNED）
  Contract    ：0 改写 ｜ Schema：0 变更
```

---

## P.9 Batch 6 — API Adaptation

```text
API-W2-01 ｜ Selected = **A（transport / adaptation only）**
  Resolution  ：API 不含 business orchestration；不含直接 DB；不含授权决策；
                不得自行 orchestration onboarding transaction。
  Basis       ：EXPLICIT（§三十）
  AFFECTED    ：API · Service · Security
  IMPL CONSEQ ：API 仅做协议适配与错误映射
  RELATED     ：AUTH-W2-02 · RUNTIME-G-05
  Contract    ：0 改写 ｜ Schema：0 变更

API-W2-02 ｜ Selected = **A（Yes — API 与 Wave 2 同轮）**
  Resolution  ：API Wave 2 允许范围仅含：identity onboarding/authentication entry ·
                device enrollment · session lifecycle · authenticated context ·
                controlled logout/revoke operations · 既有已授权的最小 health/diagnostic 适配。
                **不实现**：generic CRUD API · administration API · Bootstrap API ·
                permission-management API · schema-management API。
  Basis       ：EXPLICIT（§三十一）
  AFFECTED    ：API · Wave 2 Scope · Acceptance · Test Governance
  IMPL CONSEQ ：路由面被明确限定；超出清单的端点不得出现
  RELATED     ：API-W2-01/03/04 · SCOPE-W2-01
  Contract    ：0 改写 ｜ Schema：0 变更

API-W2-03 ｜ Selected = **A（确认既定链路）**
  Resolution  ：HTTP request → authentication adapter → authenticated context →
                authorization → service；**禁止** handler → direct DB。
  Basis       ：EXPLICIT（§三十）
  AFFECTED    ：API · Context · Authorization · Service
  IMPL CONSEQ ：认证适配器不落库；context 由 service 层消费
  RELATED     ：CTX-W2-01/04 · AUTH-W2-01 · AUTH-W2-02
  Contract    ：0 改写 ｜ Schema：0 变更

API-W2-04 ｜ Selected = **A（显式错误映射；security 类统一模糊化）**
  Resolution  ：以下必须全部进入 **fail-closed 认证/授权失败路径**：
                malformed credential · invalid credential · revoked credential ·
                expired credential · revoked device · expired session ·
                invalid tenant context · invalid space context；
                **不得**因 authentication failure fallback 到 anonymous business execution。
                映射必须与既有 Wave 1 Error Taxonomy 的 8 类一致；
                conflict（唯一性冲突）与 validation failure 依既有 Error Taxonomy 派生
                （分别对应持久化冲突与校验失败，且不得泄露内部结构）。
  Basis       ：EXPLICIT（§三十二）；conflict / validation 语义 = DERIVED（既有 Error Taxonomy）
  AFFECTED    ：API · Security · Observability · Acceptance
  IMPL CONSEQ ：集中式错误映射表；security 类响应模糊化
  RELATED     ：Wave 1 Error Taxonomy（ACCEPTED）· SEC-W2-01 · ID-W2-03
  Contract    ：0 改写 ｜ Schema：0 变更
```

---

## P.10 Batch 7 — Security

```text
SEC-W2-01 ｜ Selected = **REPURPOSED（§三十六：authentication fail-closed）**
  Resolution  ：以下全部 **DENY**：credential invalid · identity revoked ·
                device revoked / lost · session expired / revoked ·
                membership inactive · authorization unknown。
  原 Sheet 问题的其余部分（重复 identity 创建的可观测性）= DERIVED：
                重复创建按 conflict 拒绝，且**不披露存在性**（依 fail-closed 原则与最小信息披露）；
                与 ID-W2-03 一致。
  Basis       ：EXPLICIT（§三十六）；重复创建可观测性 = DERIVED（§三十六 fail-closed 精神 + ID-W2-03）
  AFFECTED    ：Security · Identity · Device · Session · Authorization · Acceptance
  IMPL CONSEQ ：默认拒绝为唯一默认；任何不确定 ⇒ DENY
  RELATED     ：SEC-P14-03（UNKNOWN→DENY）· ID-W2-03 · API-W2-04
  Contract    ：0 改写 ｜ Schema：0 变更

SEC-W2-02 ｜ Selected = **REPURPOSED（§三十六：no credential leakage）**
  Resolution  ：secret 不得出现在 logs · trace · metrics · audit · API response · exception。
  原 Sheet 问题（onboarding abuse / replay 边界）= 由 SEC-W2-03 的 replay resistance
                与 §十四 challenge 语义覆盖（本条不再单列限流载体）。
  Basis       ：EXPLICIT（§三十六）
  AFFECTED    ：Security · Observability · API · Acceptance
  IMPL CONSEQ ：沿用 Wave 1 redaction；跨 6 个输出面断言无 secret
  RELATED     ：SEC-P14-08 · CTX-W2-03 · Wave 1 Observability（ACCEPTED）
  Contract    ：0 改写 ｜ Schema：0 变更

SEC-W2-03 ｜ Selected = **REPURPOSED（§三十六：replay resistance）**
  Resolution  ：challenge / enrollment / session material 必须：bounded lifetime ·
                single-use where applicable · explicit consumption · expired material denied。
  原 Sheet 问题（跨租户 / 越权 deny 证明清单）仍为 Wave 2 验收必测项，由
                CTX-W2-02（tenant/space fail-closed）· AUTH-W2-02（§二十九 评估顺序）·
                SEC-W2-01（authorization unknown ⇒ DENY）共同承担。
  Basis       ：EXPLICIT（§三十六）；原问题归属 = DERIVED（§二十九 + §二十三…§二十五 + §三十六 SEC-W2-01）
  AFFECTED    ：Security · Device · Session · Authorization · Acceptance
  IMPL CONSEQ ：challenge 与 session material 需显式消费与过期拒绝
  RELATED     ：DV-W2-03 · DV-W2-05 · SS-W2-05 · SEC-W2-01
  Contract    ：0 改写 ｜ Schema：0 变更

SEC-W2-04 ｜ Selected = **REPURPOSED（§三十六：revoke propagation）**
  Resolution  ：identity revoke → related active sessions revoke；
                device revoke → related active sessions revoke；
                credential revoke → authentication denied；
                以上均必须遵守 transaction boundary（同事务原子完成）。
  原 Sheet 问题（secret 可达面逐项裁定）= 由 CTX-W2-03（字段白名单）+
                SEC-W2-02（§三十六 六面禁泄露）覆盖。
  Basis       ：EXPLICIT（§三十六）；原问题归属 = DERIVED（CTX-W2-03 + SEC-W2-02）
  AFFECTED    ：Security · Identity · Device · Session · Transaction Boundary · Acceptance
  IMPL CONSEQ ：传播矩阵落为 service 层同事务操作（复用 Wave 1 Transaction Boundary）
  RELATED     ：ID-W2-05 · DV-W2-04 · SS-W2-03 · DC-19
  Contract    ：0 改写 ｜ Schema：0 变更

SEC-W2-05 ｜ Selected = **REPURPOSED（§三十六：no privilege expansion）**
  Resolution  ：Wave 2 不新增 role；不新增 grant；不改变 existing Grant Matrix；
                不修改 C2 / CC-7；不改变 `uap_runtime` privilege boundary。
  原 Sheet 问题（credential algorithm / rotation 参数）= 由 §三十三 覆盖
                （interactive 仅 local password + Argon2id；无明文、无日志；
                 failed attempt 依既有 schema 字段）；具体数值参数 = DERIVED
                （由部署配置提供，与 SS-W2-05 同口径）。
  Basis       ：EXPLICIT（§三十六）；algorithm/参数归属 = DERIVED（§三十三 + §二十 同口径）
  AFFECTED    ：Security · Identity · Persistence · Acceptance
  IMPL CONSEQ ：无 GRANT/REVOKE/ALTER ROLE；无新角色；Argon2id 为唯一实现算法
  RELATED     ：SEC-P14-14 · SEC-P14-09 · OI-G-1（CLOSED · 不自动重开）
  Contract    ：0 改写 ｜ Schema：0 变更
```

---

## P.11 Contract Divergence D-1…D-9 最终状态（§三十七）

```text
D-1  聚合根（Domain identity-centric vs DB user-centric）  → **RESOLVED BY MAPPING**（§四 / §五）
D-2  credential type 词表                                  → **RESOLVED BY MAPPING**（§七）
D-3  device status 词表                                    → **RESOLVED BY MAPPING**（§八）
D-4  identity status 词表                                  → **RESOLVED BY MAPPING**（§十）
D-5  identity kind vs provider 轴                          → **RESOLVED BY MAPPING**（§六）
D-6  user status 词表                                      → **RESOLVED BY MAPPING**（§九）
D-7  credential algorithm（Domain 未表达）                  → **RESOLVED BY MAPPING**（§三十三）
D-8  session status                                        → **NOT A DIVERGENCE**（Domain 与 DB 一致）
D-9  permission effect（REQUIRES_APPROVAL 无持久化载体）    → **DEFERRED / OUT OF SCOPE**（§二十六）

⇒ ACTIVE UNKNOWN = 0 · unresolved divergence = 0
```

## P.12 边界输出（§四十六 · Decision 输出 · 非 implementation evidence）

```text
Existing Grants Sufficient = **YES**
New Grant Required         = **NO**
New Role Required          = **NO**
New Schema Object Required = **NO**
Migration Required         = **NO**
C2 Change Required         = **NO**
CC-7 Change Required       = **NO**
```

**END OF PLATFORM_DECISION_LOG（P14 WAVE 2 HUMAN DECISION FREEZE · 附录 **P**（append-only canonical registration）· `SCOPE-W2-01` + `VOC/ID/DV/SS/CTX/AUTH/API/SEC-W2-*` 共 **36 条 = FROZEN**（36 resolved · 0 unresolved · 0 UNKNOWN）· 0017 schema = **unchanged** · Domain = 经显式 mapping 归一（anti-corruption），非"从未存在分歧" · D-1…D-8 = RESOLVED BY MAPPING · D-9 = DEFERRED / OUT OF SCOPE · 既有 `D-*` 与 `附录 A–O` **零改写** · DB / role / grant / revoke / migration / runtime = 0 · `Wave 2 Implementation = NOT STARTED` · `W2-AUTH-01…07 = HUMAN AUTHORIZATION REQUIRED`；2026-09-28）**

---

# 附录 Q — P14 D-02 HUMAN DECISION（OPTION B · 2026-09-28 · canonical registration）

> **本区为 append-only canonical registration**：**不**修改任何既有 `D-*` 正文；
> **不**修改既有 `附录 A–P` 正文；**不**删除；**不**重排。
> 授权来源：Human 裁决（2026-09-28）「授权裁决：OPTION B」。

## Q.1 裁决内容

```text
事项          = D-02：Wave 1 frozen 断言 `audit_logs == 0`
                与 append-only 审计数据（tg_audit_immutable · EXPECTED TEST DATA）的冲突
Human Decision = **OPTION B**
明文           = · 不授权任何测试库重建（reset）
                 · 不授权 GRANT / REVOKE replay
                 · 不授权 schema / migration / role 操作
                 · **不改变 Wave 1 frozen artifact**（tests/integration/test_runtime_db_wave1.py
                   保持原始 `assert audit == 0`，逐字节恢复后不得再改）
                 · 该断言确认为 **Wave-1-only baseline 断言**；其在含 append-only
                   EXPECTED TEST DATA 的库状态下的失败登记为**环境状态产物**，
                   非代码回归、非验收缺陷
                 · 审计不变量改由**独立 Wave 2 测试**覆盖：
                   tests/integration/test_wave2_audit_invariant.py（delta 语义 · 4 用例）

⇒ **D-02 = CLOSED（by Human adjudication · OPTION B）**
⇒ P14 Overall 的唯一 blocking item 解除（不触发 OPTION A 的基线重建）
```

## Q.2 后续约束（持续有效）

```text
Q-1  audit_logs 不得强制归零（沿用 immutable 语义 D-P10-11 与 §二十七）
Q-2  Wave 1 frozen set 在本库状态下的该项失败为**已知且已裁决**；
     不得据此判定 "Wave 1 regression 失败"，也不得再修改该 artifact
Q-3  任何未来改动 Wave 2 / P14 已接受行为 ⇒ 必须新开 CHANGE / MAINTENANCE DECISION
Q-4  管理类身份/设备/会话操作（FINDING-AUTHZ-1）仍为 SEPARATE HUMAN DECISION
Q-5  D-01（Wave 1 persistence.py foundation defect）保持 frozen；
     SafeReader 为 P14 approved persistence path；修复需独立 foundation 授权
```

**END OF PLATFORM_DECISION_LOG（P14 D-02 HUMAN DECISION · 附录 **Q**（append-only canonical registration）· `D-02 = CLOSED（OPTION B）` · 不重建测试库 · 不 replay GRANT/REVOKE · 不改 Wave 1 frozen artifact · 审计不变量由独立 Wave 2 测试覆盖 · 既有 `D-*` 与 `附录 A–P` 零改写 · DB / role / grant / revoke / migration / schema = 0；2026-09-28）**

---

# 附录 R — P15 HUMAN DECISIONS（2026-09-28 · canonical registration）

> **append-only**：不修改任何既有 `D-*` 正文；不修改附录 A–Q；不删除；不重排。
> 授权来源：Human 指令「UAP P15 HUMAN DECISION RESOLUTION + IMPLEMENTATION CONTRACT PREP」。
> Selected Option 以**真实 Decision Sheet 文本**为准（非编号猜测），文本记于本附录。

## R.1 计数

```text
P15 Human Decision 共 **6** 条：resolved 6 · unresolved 0 · UNKNOWN 0
P15 Primary Theme = **C-5 Events / Outbox Consumer**
⇒ `P15 Decisions = FROZEN` · `P15 Implementation = NOT AUTHORIZED`
```

## R.2 逐项登记（全部 FROZEN）

```text
P15-DEC-01 ｜ P15 主题 / scope 组成
  Selected Option = **Option A（真实文本：「运行时/后台能力优先（C-5 outbox consumer + C-8 审计深化）」）
                      + Human 细化：P15 primary theme = **仅 C-5**；C-8 排除出 P15（= FUTURE）**
  Status = FROZEN
  Resolution：P15 = EVENT / OUTBOX CONSUMER RUNTIME SLICE；Primary Candidate = C-5
  Basis：C-5 补齐"事件已产生但无受控、可靠、可观测、可重放受限、具幂等语义的 Consumer 执行层"
  Non-goals：AI feature / Frontend / Business module / Admin console / Bootstrap CLI /
             Audit redesign / Foundation maintenance 均非 P15 主题
  Impact：Schema 需依据 C-5 证据判定（本轮判定 = 无需变更）· Runtime = major · API = indirect

P15-DEC-02 ｜ 管理类能力与 authorization 词表
  Selected Option = **Option A（真实文本：「保持现状（不引入管理类能力）」）**
  Status = FROZEN
  Resolution：保持自助模型 + ownership validation + authenticated-user based authorization；
              不引入 admin-on-behalf-of-user
  New admin action = NO · New authorization action = NO · New role = NO · New permission = NO ·
  New grant = NO · New principal = NO
  不得修改：Stage 2 · canonical 12 actions · role_permissions · permissions · acl_subject_types
  C-2 = NOT IN P15 ACTIVE SCOPE（未来需 admin 能力 ⇒ 重新建立独立 Human Decision）

P15-DEC-03 ｜ Bootstrap CLI 时机
  Selected Option = **Option A（真实文本：「本轮不实现（保持 DB 层就绪、无代码）」）**
  Status = FROZEN
  Resolution：Bootstrap CLI implementation = NOT PART OF P15 · uap_bootstrap grant change = NO ·
              new/public bootstrap endpoint = NO · new bootstrap schema object = NO
  Basis：RTA-09 既有分离边界 · uap_bootstrap 安全边界已建立 · operational bootstrap 保持独立能力
  C-4 = OUT OF P15

P15-DEC-04 ｜ D-01 foundation maintenance
  Selected Option = **Option A（真实文本：「Keep Deferred」）**
  Status = FROZEN
  Resolution：D-01 = KEEP DEFERRED；不得修改 infrastructure/database/persistence.py、
              不得重写 Repository helper / 修 _fetch_one / 修 _fetch_all / 改 Wave 1 foundation 行为
  Frozen invariant：persistence.py sha256 = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6
  P15 Consumer read path 必须沿用已验证安全路径（services/reads.SafeReader）；
  不得为 P15 方便重新启用 D-01 defective helper
  若 P15 证明 Worker/Consumer active path 无法安全避开 D-01 ⇒
              **STOP · FOUNDATION CHANGE REQUIRED**（不得自行修复）

P15-DEC-05 ｜ FINDING-ENGINE-1（engine 双轨）
  Selected Option = **Option A（真实文本：「保持现状（accepted compatibility）」）**
  Status = FROZEN
  Resolution：`/ready` 继续保留 Wave-0 process-engine compatibility；
              P14 RuntimeDatabase 继续作为 Runtime 数据访问路径
  不得：rewrite /ready · remove process engine · replace Wave0 engine · merge health engine ·
        change existing health contract
  FINDING-ENGINE-1 = ACCEPTED COMPATIBILITY（保持）

P15-DEC-06 ｜ events / outbox consumer
  Selected Option = **Option B（真实文本：「引入专用 consumer」）
                      + Human 前置条件：先冻结 Worker Boundary 与 Idempotency Contract，再实施 Consumer**
  Status = FROZEN
  Resolution：必须先把以下语义写进 Implementation Contract 并冻结：
              worker boundary 明确 · consumer responsibility 明确 · idempotency semantics 冻结 ·
              retry semantics 冻结 · failure semantics 冻结 · audit/observability semantics 冻结 ·
              仅当这些契约被接受后，implementation 才可开始
  Impact：Security = worker security（**SECURITY DECISION REQUIRED 若现有 uap_runtime 授权不足**）·
          Authorization = 必须继承 P14（不得绕过）· Schema = TBD（本轮判定：现有 events 表已足够）·
          Runtime = primary · API = indirect · Migration = TBD
```

## R.3 Final Candidate Disposition（P15 scope decision · 非永久 roadmap 承诺）

```text
C-1 D-01                       = MAINTENANCE / DEFERRED
C-2 Management Capability      = DEFERRED / NOT P15
C-3 /ready Dual Track          = ACCEPTED COMPATIBILITY
C-4 Bootstrap CLI              = OUT OF P15
C-5 Events / Outbox Consumer   = **PRIMARY P15 THEME（IN P15）**
C-6 AI Activation              = FUTURE
C-7 Frontend                   = FUTURE
C-8 Audit Deepening            = FUTURE
（未来如需改变 ⇒ 建立新的 Decision；本附录不作为 roadmap 承诺）
```

## R.4 边界

```text
本附录仅登记决策；**不构成 implementation / migration / release 授权**
P15 IMPLEMENTATION = NOT AUTHORIZED（须 Decisions FROZEN + Implementation Contract FROZEN +
                                    Security Gate PASS + Schema Decision RESOLVED +
                                    Acceptance Matrix FROZEN）
既有 `D-*` 与附录 A–Q 零改写 · DB / role / grant / revoke / migration / schema = 0
```

**END OF PLATFORM_DECISION_LOG（P15 HUMAN DECISIONS · 附录 **R**（append-only canonical registration）· `P15-DEC-01…06` = **FROZEN**（6 resolved · 0 unresolved · 0 UNKNOWN）· Primary Theme = **C-5 Events / Outbox Consumer** · DEC-02/03/04/05 = Option A · DEC-01 = Option A（细化为仅 C-5）· DEC-06 = Option B + 契约前置 · D-01 保持 DEFERRED（sha 69d2c140…）· Stage 2 / 12 canonical actions / uap_runtime 51 / uap_bootstrap 6 未变 · 既有 `D-*` 与附录 A–Q 零改写 · DB / role / grant / revoke / migration / schema = 0 · `P15 IMPLEMENTATION = NOT AUTHORIZED`；2026-09-28）**

---

# 附录 S — P15 C-5 OPEN DECISIONS FREEZE（2026-09-28 · canonical registration）

> **append-only**：不改写 `D-*`；不改写附录 A–R；不删除；不重排。
> 授权来源：Human 指令「P15 EVENT/OUTBOX — OPEN DECISIONS FREEZE + IMPLEMENTATION CONTRACT FINALIZATION」。

## S.1 计数

```text
P15-DEC-01…06 = FROZEN（承附录 R）
O-1 … O-6     = **FROZEN**（本次新增冻结）
OPEN DECISIONS = **0** · UNKNOWN = 0 · MAYBE = 0 · TBD = 0
Primary P15 Theme = **C-5 Events / Outbox Consumer** · C-8 = FUTURE
```

## S.2 O-1 … O-6 冻结内容

```text
O-1 Lease Recovery = FROZEN
  条件：status='claimed' AND lease_expires_at < now()
  attempts < MAX_ATTEMPTS ⇒ status='pending' · worker_id=NULL · claimed_at=NULL ·
                             lease_expires_at=NULL · **保留 attempts** · 保留足量诊断 last_error
  attempts >= MAX_ATTEMPTS ⇒ status='dead' · terminal reason = `lease_expired_max_attempts`
  关键规则：**lease recovery 不增加 attempts**（attempts = 实际执行尝试次数）
  禁止：claimed → claimed（无限占用 lease）· expired claim 未重新 claim 即执行
  Atomicity：claim/recovery 必须使用条件 UPDATE 并检查 rowcount；rowcount=0 ⇒ 不假设所有权、
             不执行、重新读取或跳过

O-2 Attempts / Backoff = FROZEN
  MAX_ATTEMPTS = **10**（application policy）· DB 硬上限 100 保留（ck_events_attempts）
  Backoff = 确定性指数：base 5s · multiplier 2 · cap 10min
     失败 1→+5s · 2→+10s · 3→+20s · 4→+40s · 5→+80s · 6→+160s · 7→+320s · 8→+640s · 9→+600s(cap)
     attempt 10 失败 ⇒ status='dead'
  禁止：infinite retry · random unbounded retry · retry forever · 本轮**不引入 jitter**
  理由：deterministic · testable · auditable · predictable（未来高并发多实例再单独 Decision）

O-3 Worker Actor = FROZEN
  **不新增 authorization subject vocabulary**：不得引入 system / service / platform / worker /
  consumer 作为新的 canonical ACL subject type；保持现有 `user` / `role` / `agent`
  Actor provenance = **originating actor**：actor_type = 既有受支持 subject type ·
                                   actor_id = 既有 subject identity
  禁止：NULL actor 自动升级为 platform_admin · 借用 uap_bootstrap / uap_migrator 执行业务操作
  Authorization：Worker = execution mechanism ≠ superuser；需用户授权的 use-case 必须满足
      original actor valid AND tenant valid AND space valid AND ownership/membership valid
      AND Stage2 authorization allows ⇒ execute；actor 无效 ⇒ deny
  若某 use-case 必须新增 system/service/platform subject ⇒
      **STOP · AUTHORIZATION DECISION REQUIRED**（不得自行扩展）

O-4 Concurrency = FROZEN
  worker process count = 1 · concurrency = 4 · batch size = 10 ·
  lease duration = 120s · heartbeat = 40s
  Claim：单批 ≤ 10 events · atomic / conditional / bounded；
         禁止 "SELECT many → 逐个 UPDATE"；ownership 由 DB 原子条件保证（非 Python 内存锁）
  Lease：初始 120s；heartbeat 每 40s；仅当 status='claimed' AND worker_id=current_worker
         AND lease 未终局过期 ⇒ lease_expires_at = now+120s；
         rowcount != 1 ⇒ worker 失去所有权 ⇒ **必须安全停止执行**
  Shutdown：stop claiming → 完成有界操作 → 持久化结果 → 释放/结束所有权 → exit
  Hard crash：lease 过期 ⇒ O-1 recovery（不依赖 graceful shutdown）

O-5 Event Type Whitelist = FROZEN
  **CLOSED ALLOWLIST**；禁止 `*` / `%` / unknown event_type / auto-discover & execute /
  dynamic import from event_type；只有 event_type + explicit handler + explicit acceptance
  coverage 才可执行
  初始集合（只读证据）：仓库**无任何 event producer 代码**（services/apps/core 无
  `INSERT INTO events`）；`events` 行数 = 0 · distinct event_type = 0
  ⇒ **ALLOWLIST = EMPTY**（合法状态）：P15 可先实现 consumer infrastructure / claiming /
     lease / retry / idempotency / observability，但 **no production event handler enabled**；
     不得为"让 Consumer 有东西跑"而创造 fake business event type
  注册机制：仅 code-level explicit mapping（或项目既有已冻结注册机制）；
            禁止 DB 动态注册；未知类型 ⇒ status='dead' · reason=`unsupported_event_type`（不死循环重试）

O-6 Idempotency Exclusion = FROZEN
  Consumer **默认排除**无法证明幂等安全的 use-case；允许执行者必须满足至少一项：
     A. naturally idempotent · B. transactional idempotency key ·
     C. persistent deduplication/uniqueness already guaranteed by existing schema
  必须可证明：duplicate delivery ⇒ no unacceptable duplicate side effect
  无法证明 idempotent=true ⇒ **NOT ELIGIBLE FOR CONSUMER**（不得"probably safe"/"小心重试"）
  Idempotency key：优先 `event_id` 作为 primary delivery identity；更细粒度用
                   `event_id + operation identity`（须在 handler contract 显式定义）
  禁止以 timestamp / retry 期间生成的 random UUID / worker_id 作为 duplicate identity
```

## S.3 其它冻结项（同轮）

```text
Event lifecycle（最终）：pending → claimed → execute
     success ⇒ delivered · retryable failure ⇒ pending + next_attempt_at · terminal ⇒ dead
  crash：claimed → lease expires → recovery → pending OR dead
  禁止：delivered → pending · dead → pending（自动）；dead replay = 未来独立 Decision（不在 P15 baseline）
Success semantics：仅当 use-case side effect + required persistence outcome 完成并满足事务契约 ⇒
  delivered + delivered_at=now；禁止 mark delivered before side effect；禁止 catch → mark delivered
Authorization failure：不按 transient 重试 ⇒ 记 terminal denial ⇒ dead
Transaction：claim → execute bounded use-case → persist durable outcome；失败 rollback；
  禁止 commit partial business state 后假设 retry 安全
Tenant/Space：必须使用事件明确的 tenant/space/actor/ownership；禁止 random/global fallback；
  tenant missing / space ambiguous / membership invalid ⇒ fail-closed
Audit/Observability：operational event ≠ audit row；audit 继续 append-only（禁 DELETE/UPDATE/truncate）；
  新增 audit semantics ⇒ AUDIT DECISION REQUIRED
Security boundary：不新增 principal/role/grant/default ACL/RLS；沿用 uap_runtime 51 · uap_bootstrap 6 ·
  uap_app 5 · uap_seed 0 · uap_migrator 245 · default_acl 0；
  若 uap_runtime 授权不足 ⇒ **STOP · SECURITY IMPLEMENTATION GATE REQUIRED**（不得自行 GRANT）
Schema boundary：Schema Decision = RESOLVED FOR CURRENT SCOPE；优先使用现有 events / events_202609
  与既有列（status/worker_id/claimed_at/lease_expires_at/attempts/next_attempt_at/last_error/
  delivered_at）；不得创建 0018 / new events 表 / worker 表 / consumer 表 / dedup 表 / lease 表 /
  dead-letter 表（除非新证据显示现有 schema 无法满足已冻结契约）
Scope finalization：IN = C-5；OUT = C-1 D-01 repair · C-2 admin management · C-3 /ready redesign ·
  C-4 Bootstrap CLI · C-6 AI · C-7 Frontend · C-8 Audit deepening
  注：C-8 虽曾出现在 P15-DEC-01 Option A 原文，本次 Human Resolution 已将 primary theme 收敛为
      "仅 C-5" ⇒ C-8 不进入本轮 implementation scope（历史 Option 原文不改）
```

**END OF PLATFORM_DECISION_LOG（P15 C-5 OPEN DECISIONS FREEZE · 附录 **S**（append-only canonical registration）· `O-1…O-6` = **FROZEN**（MAX_ATTEMPTS=10 · 确定性退避 5s×2 cap10min · 不新增 subject · worker=1/concurrency4/batch10/lease120s/hb40s · CLOSED ALLOWLIST（当前 EMPTY）· 幂等不可证明者排除）· `P15-DEC-01…06` FROZEN（附录 R）· OPEN DECISIONS = 0 · Primary Theme = C-5 Events / Outbox Consumer · C-8 = FUTURE · D-01 sha 69d2c140… 保持 · uap_runtime 51 / uap_bootstrap 6 / default_acl 0 未变 · 既有 `D-*` 与附录 A–R 零改写 · DB / role / grant / revoke / migration / schema = 0 · `P15 IMPLEMENTATION = NOT AUTHORIZED`；2026-09-28）**

---

# 附录 T — P15 IMPLEMENTATION ACCEPTANCE CLOSURE（2026-09-28 · canonical registration）

## T.1 登记性质

```text
性质        = append-only 追加登记（附录 A–S 零改写）
依据        = P15_IMPLEMENTATION_ACCEPTANCE_REPORT.md
            · P15_IMPLEMENTATION_ACCEPTANCE_MAPPING.md
            · P15_BATCH4_TEST_EXECUTION_REPORT.md
            · P15_FINAL_FINDING_REGISTRY.md
权限声明    = 本附录 ≠ Release Authorization ≠ Commit/Tag/Push Authorization
新的 Decision ID = 0（本附录只登记实现验收结果，不产生新决策）
```

## T.2 Batch 结果登记

```text
Batch 1 Consumer Kernel                     = PASS（13 passed）
Batch 2 Claim / Lease / Heartbeat / Recovery = PASS（13 passed）
Batch 3 Worker（lifecycle/concurrency/shutdown）= PASS（30 passed）
Batch 4 Full Acceptance + Cross-Wave        = PASS（9 passed entry + 完整验收）
P15 测试合计                                 = 65 passed / 0 failed

P14 Wave 1 regression = 210 passed + 1 failed（D-02 HISTORICAL RECORD · 断言保持原样）
Wave 2 regression     = 72 passed
Cross-Wave            = PASS
```

```text
Process entry 判定 = Contract §2 明确要求 `apps/worker/**`（专用 consumer 入口）
  （P14 已将其列为 OUT OF SCOPE ⇒ 属 P15 范围）
  已按最小补齐执行：apps/worker/main.py = load config → 既有 runtime DB 依赖 →
  构造 worker → SIGINT/SIGTERM → poll → drain → exit
  未引入新框架 / process manager / Celery / scheduler / broker / 新 principal / 新 schema / 新 grant
```

## T.3 冻结值复核（O-1…O-6 · 逐项）

```text
O-1 Lease Recovery  = PASS（attempts<10 → pending · attempts 不变；attempts>=10 → dead）
O-2 Attempts/Backoff = PASS（MAX_ATTEMPTS=10 · 5/10/20/40/80/160/320/600/600 · cap=600 · 无 640）
O-3 Worker Actor     = PASS（不新增 subject；使用事件 originating actor；不绕过 Stage 2）
O-4 Concurrency      = PASS（worker=1 · concurrency=4 · batch<=10 · lease=120s · heartbeat=40s）
O-5 Event Whitelist  = PASS（CLOSED ALLOWLIST · 当前 EMPTY；未知类型 → dead）
O-6 Idempotency      = PASS（幂等不可证明的 use-case 不纳入 consumer 范围）
```

## T.4 边界不变量（本附录自证）

```text
Security Boundary   = INTACT（uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 ·
                       uap_migrator 245 · default_acl 0 · memberships 0 · ownership residual 0）
C2 / CC-7           = INTACT（C2 md5 185e95be8bc4304edbcd3f4d5cda1eff）
P13 seed            = INTACT（acl_subject_types 3 · permissions 12 · role_permissions 12）
Schema / Migration  = 0017_p13_seed · 0018+ = 0 · pg_class/proc/trigger = 156/22/272（未变）
Formal DB uap       = prestate == poststate
test db 唯一差异     = audit_logs 1412 → 1655（+243 · append-only EXPECTED TEST DATA）

DDL / DML（正式库）/ ROLE / GRANT / REVOKE / OWNER / MIGRATION = 0
commit / tag / push / release = 未执行

D-01                = DEFERRED（persistence.py sha 69d2c140… 未变 · P15 活跃路径依赖 = 0）
D-02                = CLOSED（historical · 未改写）
FINDING-AUTHZ-1     = DEFERRED / OUT OF P15 SCOPE
Blocking findings   = 0
```

## T.5 未授权项（硬边界）

```text
P15 RELEASE PREPARATION = NOT STARTED
P15 COMMIT / TAG / PUSH = FORBIDDEN
P16+                    = FORBIDDEN
下一步                  = 必须单独授权：P15 OVERALL ACCEPTANCE → P15 RELEASE PREPARATION
```

**END OF PLATFORM_DECISION_LOG（P15 IMPLEMENTATION ACCEPTANCE CLOSURE · 附录 T（append-only）· P15 IMPLEMENTATION = PASS · P15 ACCEPTANCE = PASS · O-1…O-6 复核 PASS · Security / Schema / Migration / Role / Grant 变更 = 0 · Wave 1 = 210/211 HISTORICAL · Wave 2 = 72 PASS · Blocking findings = 0 · Release / Commit / Tag / Push = 未授权；2026-09-28）**
