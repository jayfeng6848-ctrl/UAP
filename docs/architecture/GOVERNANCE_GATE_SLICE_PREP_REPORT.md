# GOVERNANCE / GATE SLICE — PREP REPORT

**载体性质**：**PREP / 实施契约**（**非**决策载体、**非**阶段 Decision Log）
**状态**：`PREP WRITTEN` · **实现 = NOT IMPLEMENTED** · **测试 = NOT RUN（本轮未执行）** · **未冻结**
**阶段名称**：`Governance / Gate Slice`（Human Decision 项 9；**不属于** Runtime Slice，见 §2.1）
**Created**：2026-09-23
**Baseline**：`HEAD = 71c36c1d5129c4f7f1b0d6a2f67d980711ba70ab` · branch `main` · migration head `0011_p09_agent_tool_permission`
**决策权威**：`PLATFORM_DECISION_LOG.md`（`D-PLAT-01`…`D-PLAT-12`，`FROZEN`）。**本文件不承载决策权威，不修改任何已冻结内容。**
**验收矩阵**：见同目录 `GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md`（独立文件，勿与本文件混用）

> **本文件不授权任何变更。** 代码 / 配置 / 测试 / 迁移 / 部署清单的变更须经**独立实施授权**（见 §9）。

---

# 0. 本轮授权边界与写操作清单

本轮 Human 授权范围（Human Decision 项 1–10）：

```
✅ 允许：实施契约（本文件）· 独立验收矩阵（另一文件）· 起草新决策条目（**仅列出精确文本**）
✅ 允许：对 B-2′ 状态与 /ready 文档做**最小必要校正**
⛔ 禁止：修改代码 / 配置 / 测试 / 迁移文件
⛔ 禁止：DDL / DML / seed / 正式数据库迁移
⛔ 禁止：创建 P10–P13 或 Runtime 业务能力；不创建 services/ 包
⛔ 禁止：commit / tag / push；不得修改 D-PLAT-01..12
```

**实际写操作（4 个文件，全部为 `docs/**`）**

| # | 文件 | 操作 | 授权依据 |
|---|---|---|---|
| 1 | `docs/architecture/GOVERNANCE_GATE_SLICE_PREP_REPORT.md` | **新增** | Human Decision 项 7 |
| 2 | `docs/architecture/GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md` | **新增** | Human Decision 项 7 |
| 3 | `docs/architecture/PLATFORM_DECISION_LOG.md` | **追加注记**（Charter §5 格式，B-2′ 状态校正） | Human Decision 项 10 |
| 4 | `docs/architecture/ARCHITECTURE.md` · `docs/api/README.md` · `docs/security/README.md` | **最小必要校正**（/ready schema 门语义补全） | Human Decision 项 10 |

**未写入**：`PLATFORM_DECISION_LOG.md` 的 `D-PLAT-13..17`（草案见 §5，**待独立授权**）。

---

# 1. Preflight（只读核验，本轮实测）

## 1.1 Git / Alembic / DB

```
HEAD            = 71c36c1d5129c4f7f1b0d6a2f67d980711ba70ab
subject         = feat(uap): add P09 agent tool permission schema
branch          = main · staged = 0 · remotes = []
tags(6)         = …UAP-V0.1.6-B1-6-AI-GATEWAY · UAP-V0.1.7-P09-AGENT-TOOL-PERMISSION
worktree(7)     = M README.md · M docs/api/README.md · M docs/architecture/ARCHITECTURE.md
                  M docs/architecture/DEPENDENCY_RULES.md · M docs/architecture/MIGRATION_STRATEGY.md
                  M docs/security/README.md · ?? docs/architecture/PLATFORM_DECISION_LOG.md
                  ⇒ 与 2026-09-20/09-22 记录逐项一致（无漂移）
alembic heads   = ['0011_p09_agent_tool_permission']（单一 head · 链长 11）
DB（只读）      = uap 0 表 / 无 alembic_version · uap_b1_test 31 表 @0011 · uap_test 2 表（legacy 记账）
测试基线（收集）= 272 total · 离线子集 50（**本轮仅 collect-only，未执行**）
services/ 包    = 不存在（`import services` 全仓 0 命中）
```

## 1.2 关键实现事实（`/ready`、启动、配置、构建）

```
/ready 现状     : apps/api/routes/health.py:25-31 collect_components() → 仅 [check_database(...)]
                  :34-49 build_readiness_report() → critical 组件全 ok 才 ready；顶层字段 4 个
DB 探针现状     : infrastructure/database/health.py:25-75 check_database() = 仅 `SELECT 1`，**从不抛异常**
启动现状        : apps/api/main.py:44-53 仍存在 `ENABLE_MIGRATIONS_ON_STARTUP` → 调用 **legacy runner**
配置现状        : config/settings.py 共 17 键；`:69 ENABLE_MIGRATIONS_ON_STARTUP`；`:127-132 redacted()`
                  仅遮蔽 DATABASE_URL / SECRET_KEY
DB 超时现状     : DatabaseConfig.statement_timeout_ms = **None（默认未设）**；connect_timeout_seconds = 5
                  build_engine() 已支持 `connect_args["options"] = "-c statement_timeout=<ms>"`
构建现状        : Dockerfile 16 行 · **ARG = 0** · ENV = 1；docker-compose.yml `api.build: .`（**无 args**）
CI 现状         : `.github` 不存在
```

## 1.3 全仓引用面（实施影响面实测）

```
`ENABLE_MIGRATIONS_ON_STARTUP` 命中（可执行/配置/测试）：**3 处**
  · config/settings.py:69          （字段定义 → 待删除）
  · apps/api/main.py:44            （启动分支 → 待删除）
  · tests/unit/test_config.py:29   （SETTING_ENV_KEYS → 待同步）
  （另有 3 处位于 PLATFORM_DECISION_LOG 的决策文本，属**只读引用**，不改）
legacy runner 调用面：
  · 启动路径 = **仅** apps/api/main.py:45,48（待删除）—— 无第二条 startup 路径
  · 人工 CLI  = scripts/migrate.py · scripts/doctor.py（**保留**）
  · 本体与导出 = infrastructure/database/migration.py · infrastructure/database/__init__.py（**保留**）
  · 测试 = tests/unit/test_migration_runner.py · tests/integration/test_database_integration.py · tests/unit/test_project_boot.py（**保留**）
`EXPECTED_ALEMBIC_REVISION` / `build_info` 命中 = **0**（命名空间无冲突）
`/ready` 的测试调用 = **4 处，全部 monkeypatch `collect_components`**（⇒ 新增组件不破坏既有用例）
```

---

# 2. 实施契约（IMPLEMENTATION CONTRACT）

> 本章为**下一轮实施**的精确行为契约。**本轮未实施任何一条**；文中所写行为均为**设计意图**，不得表述为已实现。

## 2.1 阶段定性与命名（Human Decision 项 1 / 9）

```
① 本阶段 = **独立 Governance / Gate Slice**，**不属于** Runtime Slice。
② `D-PLAT-12`（Runtime 必须在 P10–P13 验收后开始）**原文与 FROZEN 状态保持不变**；
   本阶段**不受**其 P10–P13 前置约束（消解方式 (i)：定性为治理门控，而非 Runtime）。
③ 阶段名称 = `Governance / Gate Slice`；**不**引入 schema 阶段编号；
   **不**修改 `STEP1B_SCHEMA_DEPENDENCY.md` 的 P06–P13 阶段表（该表语义为 schema 阶段链，本阶段零 schema）。
④ Runtime 阶段名称与编号（`STEP 2 — Runtime Slice` / `P14_RUNTIME_SLICE`）**继续保持 provisional**（D-PLAT-12.a 不变）。
```

## 2.2 C-1 — 配置键契约（`EXPECTED_ALEMBIC_REVISION`）

| 项 | 契约 |
|---|---|
| 键名 | `EXPECTED_ALEMBIC_REVISION`（符合现有 UPPER_SNAKE_CASE；`case_sensitive=False`） |
| 类型 / 默认 | `str = Field(default="")` —— **空串 = 未注入** |
| 归属 | `config/settings.py`（唯一配置入口）；位置：`# --- runtime` 段（该段在删除 legacy 开关后仅余本键，或新建 `# --- schema governance` 段） |
| secret | **false**；`redacted()` 快照中**原样出现**、**不遮蔽**（revision 是公开的 migration identity，非凭据） |
| 校验 | **Settings 层不做抛异常的校验**（见下「失败关闭语义」）；形态校验 `^\d{4}_[a-z0-9_]+$` 由 `config/build_info.py::is_valid_revision()` 提供**单一来源** |
| `.env.example` | **新增空值条目** + 用途注释（Human Decision 项 4） |
| 本地开发 / 测试路径 | ① 本地：`export EXPECTED_ALEMBIC_REVISION=<rev>`（或写入 `.env`）；② 测试：`tests/conftest.py` 的 `os.environ.setdefault(...)` 基线**不**设置该键（保持空 ⇒ fail-closed 可被显式测试）；③ 需要固定值的用例通过 `load_settings_from_env({...})` 或 monkeypatch 注入 |
| 测试同步 | `tests/unit/test_config.py` 的 `SETTING_ENV_KEYS`：**删除** `ENABLE_MIGRATIONS_ON_STARTUP`、**新增** `EXPECTED_ALEMBIC_REVISION`（否则 env 隔离静默失效） |

**失败关闭语义（Human Decision 项 2；解析 附录 C 的 C-3）**

```
应用**可启动**：Settings 在 expected revision 缺失/非法时**不得**抛异常（避免连带 /health 不可用）
失败表现为     ：/ready 的 migration 组件 `status = "error"` ⇒ HTTP **503 not_ready**
不采用        ：启动失败（进程崩溃 / 容器 crash-loop）
组件状态取值   ：全部失败分支统一 `error`（**不**使用 `not_configured`）
```

## 2.3 C-2 — 构建期注入契约（解析附录 C 的 C-2）

**Human Decision 项 3 的约束**：构建期生成**只读工件**注入；**运行时不得通过环境变量覆盖**；不得扫描迁移目录或 import 迁移模块推断 head。

**方案裁定（基于上一轮 A/B/C 比较 + 本轮约束）**

| 方案 | 是否满足「构建期注入」 | 运行时不可覆盖 | 结论 |
|---|---|---|---|
| A `Docker ARG → image ENV` | ✅ | ❌ `docker run -e` / compose `environment:` 可覆盖 | **不可单独采用**（仅可作构建期**输入通道**） |
| B `构建期生成只读 Python 工件` | ✅ | ✅ 镜像内文件，运行时无写入路径 | **采用（主形态）** |
| C `Docker LABEL` | ✅ | —（容器内进程默认读不到自身 LABEL） | **不可用** |

**最终契约**

```
① 运行时读取的期望 revision：**唯一权威来源 = 构建期生成的只读工件**
     文件    = config/_build_info.py（**git-ignored**，不提交）
     形态    = `EXPECTED_ALEMBIC_REVISION = "<rev>"`（纯常量，无逻辑）
     不变性  = 随镜像固化；运行时不重建、不覆盖
② 构建期输入通道：Docker `ARG EXPECTED_ALEMBIC_REVISION`（**build-scope**，**不**写入镜像 ENV）
     生成器  = scripts/generate_build_info.py --revision "<rev>"（**必填**）
     失败策略 = 缺省 / 非法 revision ⇒ **构建失败（fail-fast）**，不产出必然 not-ready 的镜像
     确定性  = 输出仅含常量与固定头部（**不含时间戳**），保证可重复构建
③ 运行时解析顺序（config/build_info.py）：
     build_artifact（工件存在且非空）> environment（Settings 值，**仅本地开发/测试**）> missing
     解析结果以 (value, source) 返回；source ∈ {build_artifact, environment, missing}
④ 禁止：
     ✗ 运行时扫描 migrations_alembic/ 推断 head
     ✗ 运行时 import alembic 以推导 head
     ✗ 从迁移文件名猜测 head
     ✗ docker-compose.yml 的 `environment:` 设置该键（会与构建期工件语义冲突，且构成"运行时覆盖"）
⑤ 部署语义：镜像内的期望 revision **绑定该镜像** ⇒ 回滚 = 回滚镜像 + 数据库 downgrade（与 OD-3 的滚动发布责任一致）
⑥ 已知待办：compose 的 `build.args` 字面量需与 `alembic heads` 同步 ⇒ 登记为 **advisory** 漂移检测（§7 G-9，机制待确认）
```

## 2.4 `/ready` 迁移状态门契约（`D-PLAT-08` + Human Decision 项 2 / 5）

**组件形态（`D-PLAT-08.c`：不新增顶层字段）**

```
在**既有** collect_components() 返回列表中**追加**一个组件：
  ComponentHealth(name="migration", status="ok"|"error", critical=True,
                  detail={"expected": <str|None>, "actual": <str|None>, "source": <str>},
                  error=<短错误信息|None>)
`build_readiness_report()`、`READY_FIELDS`、OPTIONAL_COMPONENTS **均不变**
```

**判定表（fail-closed；任一不满足 ⇒ 组件 `error` ⇒ 503）**

| # | expected | DB `alembic_version` | 结果 | 是否访问 DB |
|---|---|---|---|---|
| 1 | 缺失 / 空串 / 仅空白 | — | not ready | **否**（短路） |
| 2 | 形态非法（不匹配 `^\d{4}_[a-z0-9_]+$`） | — | not ready | **否**（短路） |
| 3 | 合法 | 表不存在（`UndefinedTable`） | not ready | 是（异常被捕获） |
| 4 | 合法 | 查询失败（权限/超时/连接中断） | not ready | 是 |
| 5 | 合法 | 0 行 | not ready | 是 |
| 6 | 合法 | 值 NULL / 空串 | not ready | 是 |
| 7 | 合法 | 多行（违反单 head 不变量） | not ready | 是 |
| 8 | 合法 | ≠ expected（**落后**） | not ready | 是 |
| 9 | 合法 | ≠ expected（**领先**）—— **显式不通过** | not ready | 是 |
| 10 | 合法 | == expected（严格相等） | **ready**（该组件不为 `ok` 之外的状态） | 是 |

**边界行为细则**

```
· 查询形态：仅 SQL `SELECT version_num FROM alembic_version`（**不 import alembic、不读迁移目录**）
· 异常处理：探针**从不抛异常**（沿用 check_database 的既有约定）；异常 → status=error + 短错误串
· DB 不可达：database 组件与 migration 组件**同时** error（两者独立探针，均 critical）⇒ 503
· 探针引擎：独立构建 + `finally` 中 `dispose()`，**不**进入进程级 engine 池
· 超时：独立 statement timeout（见 §2.5），不继承默认（当前默认为 None = 无限制）
· /health：**保持零 I/O liveness**，不承担 schema readiness，不因本组件失败而失败
```

## 2.5 迁移探针的独立短超时（Human Decision 项 5）

```
常量      : READINESS_STATEMENT_TIMEOUT_MS = 2000（**候选值**，Human 已授权按此实施）
实现      : dataclasses.replace(DatabaseConfig, statement_timeout_ms=2000) → 复用既有 build_engine()
            既有通道：connect_args["options"] = "-c statement_timeout=2000"（**不新增 infra 机制**）
连接超时  : 沿用 DatabaseConfig.connect_timeout_seconds = 5
失败语义  : 超时 ⇒ 组件 error ⇒ /ready 503（与其它失败分支同语义；不得降级为"允许通过"）
不做      : 不引入全局 statement_timeout 默认值（不改变 database 组件与业务查询的既有行为）
待确认    : 若实施中该值与慢环境冲突，须**回报 Human**，不得自行放宽
```

## 2.6 Legacy runner 移除契约（`D-PLAT-07.a`）

```
① 删除 config/settings.py:69 `ENABLE_MIGRATIONS_ON_STARTUP`（字段 + 空段头）
② 删除 apps/api/main.py:44-53 启动迁移分支（含局部 import）
   ⇒ lifespan 收紧为：startup 日志 → yield → reset_engine() → shutdown 日志
③ **保留** legacy runner 本体：infrastructure/database/migration.py · infrastructure/database/__init__.py 导出
④ **保留** migrations/*.sql 与 scripts/migrate.py / scripts/doctor.py（人工 CLI，非 startup 入口）
⑤ **保留**其全部测试：tests/unit/test_migration_runner.py · tests/integration/test_database_integration.py
   · tests/unit/test_project_boot.py（discover_migrations 可用性断言）
⑥ 契约注记：`STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` §16「一个发布周期后旧 runner 下线」
   的**启动入口部分**在本 Slice 执行完毕 ⇒ 按 Charter §5 追加注记（**不改 §16 正文**）
   注记须写明：文件与本体仍保留（只读），删除其文件的决定仍未作出
⑦ 一致性结论：③④⑤⑥ 全部与 Contract §16 一致；本次不删除任何文件
```

## 2.7 依赖边界与 Guard 契约（Human Decision 项 6）

**允许 / 禁止边**（源自 `D-PLAT-02`…`D-PLAT-06`，**不得新增冻结外禁止边**）

```
apps      → services         ALLOWED
apps      → infrastructure   ALLOWED（**仅**装配 / 生命周期 / 健康检查 —— D-PLAT-04.a）
services  → core             ALLOWED（契约）
services  → infrastructure   ALLOWED（业务持久化实现）
services  → domains          ALLOWED（**仅公开稳定契约** —— D-PLAT-03.a）
domains   → services         FORBIDDEN
domains   → infrastructure   FORBIDDEN
core      → services         FORBIDDEN
agent     → services         FORBIDDEN（经 Policy / Tool 契约 —— D-PLAT-05）
apps 直接 SQLAlchemy/psycopg 业务持久化   FORBIDDEN（D-PLAT-04.a）
⛔ **明确不得新增**：`services ↛ domains`（D-PLAT-03.a）· `apps ↛ infrastructure`（D-PLAT-04.a）
```

**Guard 清单与门级（Human Decision 项 6）**

| Guard | 规则 | 判据 | 位置 | 门级 | 现状 |
|---|---|---|---|---|---|
| **G-1** | `core ↛ sqlalchemy / psycopg / psycopg2` | AST `_imported_top_levels()` | `tests/architecture/`（扩充 `test_core_imports_only_core` 或新增） | **硬门** | 未实现（当前 0 违规） |
| **G-2** | `core ↛ services` | 同上（forbidden 集 += `services`） | 同上 | **硬门** | 未实现 |
| **G-3** | `agent ↛ services` | 同上 | `tests/architecture/`（扩充 `test_agent_never_reaches_the_database`） | **硬门** | 未实现（agent 当前内部跨层依赖 = 0） |
| **G-4** | `domains ↛ services / infrastructure` | 同上 | `tests/architecture/`（新增） | **硬门** | 未实现（domains 当前内部跨层依赖 = 0） |
| **G-5** | `apps ↛ sqlalchemy / psycopg` | 同上 | `tests/architecture/`（新增） | **advisory**（代理判据） | 未实现 |
| **G-6** | readiness `migration` 组件 `critical=True` | 运行时断言 `collect_components()` 组件名与 critical 标志 | `tests/contract/`（新增） | **硬门** | 未实现（组件尚不存在） |
| **G-7** | 启动不调用 legacy runner（且 Settings 不含该开关） | AST/源码断言 + 键集合断言 | `tests/architecture/` 或 `tests/unit/`（新增） | **硬门** | 未实现（当前 :44-53 仍在） |
| **G-8** | bootstrap 唯一性（拒绝第二套 dev bootstrap 入口） | **仅可文件级**（非 import 可判） | `tests/architecture/`（新增，可选） | **advisory** | 未实现；范围待定（附录 C `C-11`） |
| **G-9** | compose 的 expected revision 与 `alembic heads` 漂移检测 | 文本/AST 混合（compose 无 yaml 依赖，需正则解析） | `tests/`（新增，可选） | **advisory** | 未实现；机制待确认（附录 C `C-2` 延伸） |

**Guard 实现纪律**

```
· 判据 = **AST**（复用 tests/architecture/test_dependency_rules.py:55-73 `_imported_top_levels()`）
  **禁止**字符串/正则匹配 —— 先例：P09 审计中出现「docstring 否定式声明被误判为违规」
· `if TYPE_CHECKING:` 块内 import 计入（**不豁免**，保持严格）
· 硬门 = G-1 G-2 G-3 G-4 G-6 G-7；advisory = G-5 G-8 G-9（后者**实施并运行**，违规由 Human 裁定是否豁免，须记录局限）
· `DEPENDENCY_RULES.md:61-64`：规则必须与测试**同批**提交 ⇒ 本 Slice 的文档与 Guard 必须同一变更批次
· 落地后须更新 `DEPENDENCY_RULES.md §7` 的「**Enforcement status: not yet implemented**」声明
· 静态不可判、只能靠架构审查的项（须如实登记，不得以 Guard 冒充覆盖）：
  「apps 不承载核心业务规则」（D-PLAT-04）·「services 负责用例编排/事务协调」（D-PLAT-03）·
  「apps→infrastructure 仅装配/生命周期/健康」中"装配 vs 业务"的边界 ·「domains 公开稳定契约」的形态（附录 C `C-6`）
```

## 2.8 数据库义务

```
**本 Slice 零 schema 变更**：不创建、不修改、不删除任何表 / 列 / 索引 / 约束 / trigger / function；
不新增/修改 Alembic revision；不执行 DDL / DML / seed；不修改 migrations_alembic/**。
EXPECTED_ALEMBIC_REVISION 指向**既有** 0011_p09_agent_tool_permission。
```

---

# 3. 文件变更计划（**本轮未执行**，供实施授权界定范围）

## 3.1 新增（6）

| # | 文件 | 用途 |
|---|---|---|
| 1 | `config/build_info.py` | 构建期工件的**加载器/解析器**（`get_artifact_revision()` · `resolve_expected_revision()` · `is_valid_revision()` · `REVISION_PATTERN`） |
| 2 | `scripts/generate_build_info.py` | 构建期**生成器**（`--revision` 必填；缺省/非法 ⇒ 非 0 退出） |
| 3 | `tests/unit/test_build_info.py` | 工件优先 / 环境回退 / missing 分支 / 形态校验单测（**纯离线**） |
| 4 | `tests/unit/test_migration_state_probe.py` | 探针判定表 10 分支单测（**纯离线**，stub engine） |
| 5 | `docs/architecture/GOVERNANCE_GATE_SLICE_PREP_REPORT.md` | 本文件（**本轮已写**） |
| 6 | `docs/architecture/GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md` | 验收矩阵（**本轮已写**） |

## 3.2 修改（16）

| # | 文件 | 变更 |
|---|---|---|
| 1 | `config/settings.py` | 删 `ENABLE_MIGRATIONS_ON_STARTUP`；增 `EXPECTED_ALEMBIC_REVISION` |
| 2 | `apps/api/main.py` | 删 lifespan 启动迁移分支（:44-53） |
| 3 | `apps/api/routes/health.py` | `collect_components()` 追加 migration 组件并传 expected |
| 4 | `infrastructure/database/health.py` | 新增 `check_migration_state()` + `READINESS_STATEMENT_TIMEOUT_MS` |
| 5 | `Dockerfile` | 增 `ARG EXPECTED_ALEMBIC_REVISION` + 生成工件 `RUN` |
| 6 | `docker-compose.yml` | `api.build.args.EXPECTED_ALEMBIC_REVISION`（**不**入 `environment:`） |
| 7 | `.gitignore` | 忽略 `config/_build_info.py`（**实施时先核验是否已覆盖**） |
| 8 | `.env.example` | 新增 `EXPECTED_ALEMBIC_REVISION=`（空值）+ 用途注释（Human Decision 项 4） |
| 9 | `tests/unit/test_config.py` | `SETTING_ENV_KEYS` 同步 + 新键行为用例 |
| 10 | `tests/contract/test_health_contract.py` | 新增 `/ready` 迁移门用例（503/200 两态）、断言 `READY_FIELDS` 不变 |
| 11 | `tests/unit/test_project_boot.py` | 新增「启动不触 legacy runner」用例（G-7） |
| 12 | `tests/architecture/test_dependency_rules.py` | G-1…G-5 · G-7（G-6 视位置） |
| 13 | `docs/architecture/DEPENDENCY_RULES.md` | §7 的 Enforcement status 更新 + 门级表 |
| 14 | `docs/architecture/STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` | §16 **追加注记**（Charter §5 格式） |
| 15 | `docs/api/README.md` · `docs/security/README.md` | 实现状态段更新（"not implemented yet" → 实施后事实） |
| 16 | `docs/architecture/PLATFORM_DECISION_LOG.md` | 追加 `D-PLAT-13..17`（**须独立授权**，草案见 §5） |

> ⚠ **`D-PLAT-15 v2` 对本表的修正（2026-09-23）**：第 5 行「`Dockerfile` 增 `ARG EXPECTED_ALEMBIC_REVISION`」与
> 第 6 行「`docker-compose.yml` 增 `build.args`」**均已作废** —— v2 采用**构建期推导唯一 head**，
> `Dockerfile` **仅需**生成工件的 `RUN`（**无需** `ARG`），`docker-compose.yml` **无需变更**。
> 其余 14 行不变。

## 3.3 明确不动

```
core/ · domains/ · agent/ · intelligence/ · infrastructure/cache|queue|storage ·
apps/worker/ · apps/frontend/ · services/（**不创建**）· migrations/*.sql ·
migrations_alembic/**（含 env.py / versions/ / alembic.ini）·
docs/architecture/{CORE_DOMAIN_MODEL,STEP1A_*,STEP1B_SCHEMA_DEPENDENCY,STEP1B_TRIGGER_INVENTORY,
STEP1B_SEED_STRATEGY,STEP1B_MIGRATION_STRATEGY 已由 B-2′ 处理} ·
所有历史阶段报告（*_GATE_REPORT.md / *_PREP_REPORT.md）· P09/B1-4/B1-5/B1-6 阶段文档
```

---

# 4. 只读一致性审计

## 4.1 与 `D-PLAT-01`…`D-PLAT-12` 逐条比对

| 决策 | 本契约的一致性 | 判定 |
|---|---|---|
| D-PLAT-01 服务层落点 | 本 Slice **不创建** `services/`（属 Runtime 前置）；§2.7 仅登记边界 | ✅ 不冲突 |
| D-PLAT-02 core 契约定位 | G-1 / G-2 实施 | ✅ |
| D-PLAT-03 / 03.a services 职责 | §2.7 保留 `services → domains` 许可；**未**新增反向禁止 | ✅ |
| D-PLAT-04 / 04.a apps 边界 | G-5 实现为 **advisory 代理判据**（§2.7 如实标注） | ✅ |
| D-PLAT-05 agent ↛ services | G-3 实施 | ✅ |
| D-PLAT-06 / 06.a domains 边界 | G-4 实施 | ✅ |
| D-PLAT-07 / 07.a / 07.b / 07.c | §2.6 逐条对应；注记采 Charter §5 | ✅ |
| D-PLAT-08 / 08.a / 08.b / 08.c | §2.2–2.5 补全留白（C-1/C-2/C-3），**未**改严格相等、**未**改不新增顶层字段 | ✅ |
| D-PLAT-09 阶段顺序 | 本 Slice 不改变 P10→P11→P12→P13→Runtime 顺序 | ✅ |
| D-PLAT-10 P11 纳入 G/H/I/J | 未触及 | ✅ |
| D-PLAT-11 首个主体只经 P13 | 未引入任何 bootstrap 入口 | ✅ |
| D-PLAT-12 / 12.a Runtime 门 | §2.1 明确本阶段**不是** Runtime，**D-PLAT-12 原文与状态不变** | ✅ |

**结论**：**0 项覆盖/改写/重新解释既有冻结决策。**

## 4.2 与 Migration Contract 的一致性

```
✅ §1「唯一入口 = alembic.ini + migrations_alembic/」—— 删除启动 legacy 调用 = **修复既有违规**
✅ §11「顺序：备份 → alembic upgrade head → 冒烟(health/ready)」—— 本契约的 /ready schema 门**正是该冒烟步**
✅ §16「旧 runner 只读保留 / 一个发布周期后下线」—— §2.6 ③④⑤ 保留文件与测试；仅在注记中记录**启动入口已下线**
⚠ §12「任何生产 DDL 前必须有备份」—— 本 Slice 无 DDL，不触发；但 /ready 门使"先迁移"成为硬前置 ⇒
   与 `docs/operations/`（空，仅 .gitkeep）的部署手册缺失叠加为运维风险（附录 C `C-10`）
```

## 4.3 破坏性影响面（已核验）

```
✅ READY_FIELDS（tests/contract/test_health_contract.py:10）**无需修改**（不新增顶层字段）
✅ 4 处 /ready 用例全部 monkeypatch `collect_components` ⇒ 新增组件不影响既有断言
✅ legacy runner 的两个测试文件与 project_boot 的 discover_migrations 断言**不受影响**（本体保留）
✅ 离线子集 50 / 全量 272 的现有收集结果不变（本轮仅 collect-only）
⚠ 破坏性后果（Human 已知情）：formal `uap` = 0 表 ⇒ 实施后其 `/ready` 恒 503，直至执行 `alembic upgrade head`
⚠ `tests/unit/test_config.py:29` 必须同步（否则 env 隔离静默削弱 —— 静默失效风险）
```

## 4.4 文档 ↔ 实现差异清单

| # | 差异 | 处置 |
|---|---|---|
| **D-1** | `PLATFORM_DECISION_LOG.md:276` 仍写「B-2′ 范围，**本轮未执行**」，而 B-2′ 已于 2026-09-20 执行 | **本轮已按 Charter §5 追加注记**（不改该行正文） |
| **D-2** | `ARCHITECTURE.md:83-84` 的 `/ready` 描述仅「probes PostgreSQL」，未含 schema 门 | **本轮已最小校正** |
| **D-3** | §3 参考路径 `docs/architecture/MIGRATION_IMPLEMENTATION_CONTRACT.md` **不存在**；实际 = `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` | **如实记录，不创建别名、不移动文件**（见 §4.5） |
| **D-4** | `docs/api/README.md` / `docs/security/README.md` 的 /ready 语义未含「**领先亦 not ready**」 | **本轮已最小校正** |
| **D-5** | `DEPENDENCY_RULES.md §7` 声明"守卫尚未实现" | 保持（实施轮同步更新）——**属已知且已披露的差距** |
| **D-6** | `docs/operations/` 为空；`/ready` 门使"先迁移"成为硬前置 | 登记（附录 C `C-10`，本 Slice 不含） |
| **D-7** | `.github` 不存在 ⇒ 硬门 Guard 无自动化执行载体 | 登记（风险 R-6） |
| **D-8** | `.env.example`（14 键）与 Settings（17 键）不同步 | **既有现象**；本 Slice 仅补新增键（不追求全量同步） |
| **D-9** | 附录 C `C-1`…`C-11` 未裁定 | 本 Slice 已解析 `C-1`/`C-2`/`C-3`（草案见 §5）；其余保持 |

## 4.5 迁移契约路径差异（Human Decision 项 10：**必须记录**）

```
声明路径（Human 输入 / 上轮 PREP §3 第 2 项）：docs/architecture/MIGRATION_IMPLEMENTATION_CONTRACT.md
实际路径（仓库实测）                          ：docs/architecture/STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md
处置：
  ① **不创建别名**、**不复制**、**不移动**、**不重命名**（本轮与实施轮均不）；
  ② 本报告与验收矩阵统一引用**实际路径**；
  ③ 本差异须在实施轮的契约注记中一并写明（指向实际路径），避免后续会话再次踩坑；
  ④ 若 Human 希望"别名化"，须作为**独立文档任务**另行授权（不属本 Slice）。
```

---

# 5. 决策条目草案（`D-PLAT-13`…`D-PLAT-17`）

> **未写入任何文件。** 依 Human Decision 项 8，「先列出精确文本、理由、影响与一致性结果」。
> 若获授权，将**追加**到 `PLATFORM_DECISION_LOG.md`（**不改** `D-PLAT-01..12` 的既有文本）。状态拟为 `WRITTEN`（未经 Human 确认不得置 `FROZEN`）。

## 5.1 `D-PLAT-13` — Governance / Gate Slice 定性、命名与 `D-PLAT-12` 关系

| 字段 | 内容 |
|---|---|
| **状态** | `WRITTEN`（拟） |
| **来源** | Human Decision（项 1、项 9） |
| **背景** | `D-PLAT-12` 规定 Runtime 必须在 P10–P13 完成并验收后开始。本阶段工作项为**迁移治理 + 层边界门控**（配置门、readiness schema 门、legacy 启动路径停用、依赖守卫），**不含任何业务运行时能力**。若表述为「首个 Runtime Slice」，将与 `D-PLAT-12` 冲突（先例：`D-B14-02` 判定"提前实施 = 静默扩权"）。 |
| **决策** | ① 本阶段归属为**独立 Governance / Gate Slice**，**不属于** Runtime Slice；② 阶段名称 = `Governance / Gate Slice`；③ `D-PLAT-12` 与 `D-PLAT-12.a` 的**原文与 `FROZEN` 状态保持不变**，本阶段**不受** `D-PLAT-12` 的 P10–P13 前置约束；④ Runtime 阶段名称与编号继续保持 **provisional**，其冻结仍属未来 PREP 门。 |
| **依据** | Human Decision 项 1 · 项 9 · `D-PLAT-12` · `D-PLAT-12.a` |
| **影响面** | 本阶段不引入 schema 阶段编号；不修改 `STEP1B_SCHEMA_DEPENDENCY.md` 的 P06–P13 表；不创建 `P14` 相关文件或引用；不改变 P10→P11→P12→P13→Runtime 的顺序（`D-PLAT-09`） |
| **待办** | ① 治理阶段的正式编号（如需）须 Human 另行裁定 ② 阶段文档集合 = 本 PREP 报告 + 验收矩阵（实施轮完成后由实施报告承接） |
| **禁止** | 不得将本阶段表述为 Runtime 或 `P14`；不得据本条款改写阶段表 |

## 5.2 `D-PLAT-14` — `/ready` 迁移状态门的配置键与失败语义（解析附录 C `C-1` / `C-3`）

| 字段 | 内容 |
|---|---|
| **状态** | `WRITTEN`（拟） |
| **来源** | Human Decision（项 2、项 4、项 5）；`OD-2`；附录 C `C-1` / `C-3` |
| **背景** | `D-PLAT-08.a` 已冻结「构建期注入 + 缺失或无效失败关闭」，但**键名**与**失败分支语义**留白（附录 C `C-1` / `C-3`）。 |
| **决策** | ① 配置键名 = `EXPECTED_ALEMBIC_REVISION`（`str`，默认空串；**非 secret**；`redacted()` 快照中**不遮蔽**）；② 失败关闭语义 = **应用可启动**（Settings 不抛异常）+ **`/ready` 恒 503**；`/health` 保持零 I/O liveness；③ 不通过分支全集 = expected 缺失/空白/形态非法（**短路，不访问 DB**）· DB 表缺失 · 查询失败 · 0 行 · NULL/空串 · 多行 · 与 expected 严格不等（**含领先**）；④ 组件状态统一取 `error`（不使用 `not_configured`）；⑤ revision 形态 `^\d{4}_[a-z0-9_]+$`，单一来源 = `config/build_info.py`；⑥ `.env.example` 新增空值条目并说明本地开发/测试路径。 |
| **依据** | Human Decision 项 2 · `OD-2` · `D-PLAT-08.a` · `D-PLAT-08.b`（严格相等）· 实测 `.env.example` 约束（`tests/security/test_no_secrets.py:47-64`） |
| **影响面** | `config/settings.py` · `.env.example` · `tests/unit/test_config.py` 的 `SETTING_ENV_KEYS` · 新增配置与探针测试 |
| **待确认** | 探针返回值是否需要在 `detail` 中包含 `source`（本契约建议包含：`build_artifact`/`environment`/`missing`） |
| **禁止** | 不得为"可启动"而在生产放宽严格相等；不得把「DB 版本高于期望」视为通过（`OD-3`） |

## 5.3 `D-PLAT-15` — 期望 revision 的注入形态：构建期只读工件（运行时不可覆盖）（解析附录 C `C-2`）

> ⚠ **本小节为 v1 历史文本 · `SUPERSEDED`（2026-09-23）**：Human 已于 Decision Resolution 裁定
> **`Q-5`（采用 A′）+ `Q-9`（v1 → v2）**，现行条款 = **`D-PLAT-15 v2`**（见 `PLATFORM_DECISION_LOG.md` 与本节 §5.6）。
> **v1 不得作为现行方案引用**；其「`ARG` 字面量为输入通道」的表述已被取代。

| 字段 | 内容 |
|---|---|
| **状态** | `SUPERSEDED`（原拟 `WRITTEN`；2026-09-23 被 v2 取代） |
| **来源** | Human Decision（项 3）；`OD-2`；附录 C `C-2` |
| **背景** | 上一轮比较 A（`Docker ARG → image ENV`）/ B（构建期生成只读工件）/ C（`Docker LABEL`），当时推荐 A。Human 裁定要求「**运行时不得通过环境变量覆盖**」⇒ A 的可覆盖性不可接受，C 在容器内不可读，**B 为唯一满足者**。 |
| **决策** | ① 运行时权威来源 = 构建期生成的**只读工件** `config/_build_info.py`（git-ignored，随镜像固化，运行时不重建/不覆盖）；② 构建期输入通道 = Docker `ARG EXPECTED_ALEMBIC_REVISION`（**build-scope**，**不**写入镜像 ENV），由 `scripts/generate_build_info.py --revision <rev>` 生成；缺省/非法 ⇒ **构建失败**；③ 解析顺序 = 工件 > 环境（**仅本地开发/测试**）> missing，并以 `source` 标注；④ **禁止**运行时扫描迁移目录、import `alembic` 推导 head、从文件名猜测 head；⑤ `docker-compose.yml` 的 `environment:` **不得**设置该键。 |
| **依据** | Human Decision 项 3 · `OD-2` · 附录 C `C-2` · 实测（`Dockerfile` ARG = 0 · compose 无 `build.args`） |
| **影响面** | `Dockerfile` · `docker-compose.yml` · `scripts/generate_build_info.py` · `config/build_info.py` · `.gitignore` |
| **待办** | ① compose 中 revision 字面量与 `alembic heads` 的漂移检测（advisory，机制待确认）② 镜像回滚语义（镜像 + DB downgrade）须写入部署手册（`docs/operations/` 为空 —— 附录 C `C-10`） |
| **禁止** | 不得以环境变量覆盖工件；不得在运行时推导 head |

## 5.4 `D-PLAT-16` — readiness 迁移探针的独立短超时

| 字段 | 内容 |
|---|---|
| **状态** | `WRITTEN`（拟） |
| **来源** | Human Decision（项 5） |
| **背景** | `DatabaseConfig.statement_timeout_ms` 默认 `None`（未设）⇒ readiness 探针在慢查询/锁等待下可能长时间阻塞，拖垮编排器探测周期。 |
| **决策** | ① 迁移状态探针使用**独立** statement timeout，候选值 **2000 ms**（`READINESS_STATEMENT_TIMEOUT_MS = 2000`）；② 实现复用既有 `DatabaseConfig.statement_timeout_ms` + `build_engine()` 的 `-c statement_timeout=<ms>` 通道，**不新增 infra 机制**；③ 连接超时沿用 `connect_timeout_seconds = 5`；④ 超时 ⇒ 组件 `error` ⇒ `/ready` 503；⑤ 探针引擎 `finally` 中 dispose；⑥ **不**修改全局默认超时（不影响业务查询与 database 组件既有行为）。 |
| **依据** | Human Decision 项 5 · 实测 `infrastructure/database/config.py:30`（默认 `None`）· `infrastructure/database/session.py:24-28`（既有时超时通道） |
| **影响面** | `infrastructure/database/health.py`；测试须覆盖超时分支 |
| **待确认** | 2000 ms 为**候选值**；实施中若与慢环境冲突，须回报 Human，不得自行放宽 |

## 5.5 `D-PLAT-17` — Guard 门级划分与实施责任

| 字段 | 内容 |
|---|---|
| **状态** | `WRITTEN`（拟） |
| **来源** | Human Decision（项 6） |
| **背景** | 上一轮已给出 `G-1`…`G-8` 设计，但未定「硬门 / advisory」；`DEPENDENCY_RULES.md:61-64` 规定"规则必须与测试同批"。 |
| **决策** | ① **硬门** = `G-1` core ↛ SQLAlchemy/psycopg · `G-2` core ↛ services · `G-3` agent ↛ services · `G-4` domains ↛ {services, infrastructure} · `G-6` readiness migration 组件 `critical=True` · `G-7` 启动不调用 legacy runner 且 Settings 不含该开关；② **advisory** = `G-5`（`apps ↛ SQLAlchemy/psycopg`，**代理判据**，与 `D-PLAT-04.a` 的"业务持久化"语义**不等价**）· `G-8`（bootstrap 唯一性，仅文件级可判）· `G-9`（compose expected revision 与 `alembic heads` 漂移检测，机制待确认）；③ 判据统一用 **AST**（复用 `_imported_top_levels()`），**禁止**字符串/正则匹配；④ 测试位置：`G-1`…`G-5`、`G-7` → `tests/architecture/`；`G-6` → `tests/contract/`；⑤ 落地后同步更新 `DEPENDENCY_RULES.md §7` 的 Enforcement status。 |
| **依据** | Human Decision 项 6 · `DEPENDENCY_RULES.md:61-64` · `D-PLAT-04.a`（代理局限）· `D-PLAT-11`（bootstrap 唯一性） |
| **影响面** | `tests/architecture/` · `tests/contract/` · `DEPENDENCY_RULES.md §7` |
| **待确认** | ① advisory 违规的豁免流程（是否需 Human 逐次裁定）② `G-8` / `G-9` 是否纳入本 Slice（范围） |
| **禁止** | 不得新增 `services ↛ domains`（`D-PLAT-03.a`）或 `apps ↛ infrastructure`（`D-PLAT-04.a`）守卫 |

**一致性结果（5 项草案）**

```
· 编号连续性：本载体现有 01..12 ⇒ 草案接续 13..17，**无重复、无缺号**
· 与 D-PLAT-01..12：**0 项覆盖/改写**（仅补全 08.a 的留白，且以**新条目**承载，不改 08.a 正文）
· 命名空间冲突：`D-PLAT-13`…`D-PLAT-17` 全仓 0 命中（与 `D-PLAT` 前缀一致，无新命名空间）
· 状态规则：草案状态为 `WRITTEN`；**未经 Human 明确确认不得置 `FROZEN`**（Charter §4）
· 关联解析：`C-1`/`C-2`/`C-3` 由 `D-PLAT-14`/`D-PLAT-15` 解析；建议在附录 C 中标注解析结果
  （**附录 C 属载体正文 ⇒ 该标注须与草案一并授权，不得先行修改**）
```

---

## 5.6 `D-PLAT-15` v2（**现行** · 2026-09-23）

**v1 已被取代**（见 §5.3 顶部标记）。v2 全文 = `PLATFORM_DECISION_LOG.md` 的 `D-PLAT-15`（`FROZEN`）。

```
权威链 = migrations_alembic/versions/ → Alembic graph → 唯一 HEAD → build-time generator
        → config/_build_info.py（工件）→ image → /ready → DB alembic_version
① 构建期：ScriptDirectory.from_config(Config("alembic.ini"))；恰 1 个 head；匹配 ^\d{4}_[a-z0-9_]+$ → 写工件
② --revision 仅可选 override，且必须等于推导值，否则构建失败（fail-fast）
③ 工件 = config/_build_info.py（git-ignored）· 读取入口 = config/build_info.py
④ 解析顺序 = 工件 > 环境（仅本地开发/测试）> missing（source 如实标注）
⑤ compose 的 environment: 不得设置该键
禁止：ARG 作为权威输入 · compose 字面量 · ENV 覆盖工件 · runtime 扫描迁移目录 ·
      runtime import alembic · 按文件名猜 head
连带结论：G-9（compose 漂移检测）随之 Cancelled（见 D-PLAT-17）
```

---

# 6. 验收矩阵

**独立文件**：`docs/architecture/GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md`（**本轮已写**）。
覆盖领域：Config · Build-time injection · Migration state · `/ready` · `/health` · Legacy runner · Dependency guards · Services boundary · Existing test regression · Docker build · Git cleanliness · migration head consistency。

> 矩阵中每行均标注 **当前状态**；本轮**未运行任何测试**，所有 Pass/Fail 条件均为**待验证条件**。

---

# 7. 测试计划（实施轮执行，**本轮未执行**）

| 层 | 计划 | 类型 |
|---|---|---|
| 配置 | `EXPECTED_ALEMBIC_REVISION` 存在 / 默认空 / env 可注入 / redacted 不遮蔽；`ENABLE_MIGRATIONS_ON_STARTUP` 全仓 0 命中 | 单测 + 扫描断言 |
| 工件解析 | 工件优先于环境；工件缺失回退；missing 分支；形态校验（合法 / 非四位 / 大写 / 空 / 空白） | 单测（monkeypatch `sys.modules["config._build_info"]`） |
| 探针 | 判定表 10 分支（§2.4）：短路分支不触 DB；stub engine 覆盖 0 行 / 多行 / NULL / 不等 / 相等；异常与超时 → error 且 critical=True | 单测（**纯离线**，stub） |
| `/ready` | migration 组件 error ⇒ 503；两组件 ok ⇒ 200；`READY_FIELDS` 不变 | 契约测试 |
| `/health` | 200 且**零 I/O**（断言不触发 engine） | 契约测试 |
| 启动 | 不调用 legacy runner（AST/源码断言 + 键集合断言） | 架构/单测 |
| 依赖守卫 | G-1…G-5 · G-7 通过；**负向样例**须使守卫失败（构造违规 import 的临时样例，验证守卫有效性） | 架构测试 |
| 漂移（advisory） | compose 字面量 == `alembic heads` | 文本解析测试 |
| 回归 | 全量 pytest **≥ 272 passed / 0 failed / 0 error**；离线子集 50 → 50 + 新增 | 全量 |
| 构建 | `docker build`（含 `--build-arg`）成功；容器内 resolve 出 `source=build_artifact`；缺 arg 时构建**失败** | 手工/集成 |
| DB | `alembic heads` 单一仍为 0011；未新增 revision | 命令 |
| Git | 变更文件 == §3 清单；HEAD 未推进；tags 仍 6 | 命令 |

**负向测试必须存在**：① 未注入 expected ⇒ 503；② expected 非法 ⇒ 503；③ DB 领先 ⇒ 503（**显式**）；④ `alembic_version` 表缺失 ⇒ 503；⑤ 守卫负向样例 ⇒ 测试红。

---

# 8. 未决事项与风险

## 8.1 未决（须 Human 裁定或实施轮确认）

```
Q-1 §5 的 D-PLAT-13..17 是否授权写入载体（**未写入**）；若授权，是否同时标注附录 C 的解析结果
Q-2 advisory 守卫（G-5 / G-8 / G-9）的范围与豁免流程（G-8 / G-9 是否纳入本 Slice）
Q-3 2000 ms 超时为**候选值** —— 实施中如遇环境冲突的处理方式（回报 vs 允许区间）
Q-4 `config/build_info.py` 的工件模块路径（`config/_build_info.py`）是否为首选（备选：`config/_version.py`）
Q-5 compose 的 revision 字面量同步机制（手工维护 + advisory 测试，或构建期脚本）
Q-6 `docs/operations/` 部署手册（"先迁移后启动"硬前置）是否本 Slice 一并补齐（附录 C C-10）
Q-7 实施轮是否需要 CI（.github）承载硬门 —— 当前无自动化载体
Q-8 实施轮是否将 `docs/api/README.md` 的"not implemented yet"改为实施后事实（本 Slice 已做最小校正，仅语义补全）
```

**Decision Resolution（2026-09-23）：全部 `APPROVED` 并已在载体落盘**

```
Q-1  写入 D-PLAT-13…17 + 同步附录 C C-1/C-2/C-3        → ✅ 已写入（状态 FROZEN）
Q-2  Advisory 仅 G-5；G-8 Deferred；G-9 Cancelled       → ✅ 见 D-PLAT-17
Q-3  2000 ms = 实施硬值（冲突 ⇒ HARD STOP）              → ✅ 见 D-PLAT-16
Q-4  工件路径 = config/_build_info.py                    → ✅ 见 D-PLAT-15 v2
Q-5  采用 A′（构建期推导，取消字面量）                    → ✅ 见 D-PLAT-15 v2
Q-6  实施轮必须交付 docs/operations/DEPLOYMENT_AND_RECOVERY.md → ✅ D-PLAT-08 注记
Q-7  不建 CI；人工硬门 + 证据留存                        → ✅ 见 D-PLAT-17
Q-8  实施后必须同步 docs/api|security README 事实        → ✅ D-PLAT-14 待办
Q-9  D-PLAT-15 v1 → v2 正式修订                          → ✅ 见 D-PLAT-15 版本沿革
Q-10 备份/恢复边界（只交付手册+命令契约；人工门）         → ✅ D-PLAT-08 注记
⇒ §8.1 已**无未决项**（Q-9 / Q-10 为本轮复核新增项，同批裁定）
```

## 8.2 风险

```
R-1 【高】formal `uap` = 0 表 ⇒ 实施后 `/ready` 恒 503，直至 `alembic upgrade head`。
         部署/运维顺序未形成手册（docs/operations 为空）⇒ 运维风险放大
R-2 【中】工件与 compose 字面量分离 ⇒ 存在漂移风险（G-9 仅 advisory；无 CI）
R-3 【中】应用"可启动但恒 not_ready"可能被误读为健康 ⇒ 须在部署手册/runbook 中明确 503 的语义与处置
R-4 【中】G-5 / G-8 / G-9 为代理或弱判据 ⇒ 存在"看起来被强制、实际未覆盖"的假安全
R-5 【中】无 CI ⇒ 硬门依赖人工执行 `pytest`
R-6 【低】`SETTING_ENV_KEYS` 漏改会**静默**削弱 env 隔离（无声失效）
R-7 【低】新增探针每次 `/ready` 多建一个引擎（两次连接）⇒ 观测到频率/成本问题时再优化（**不在本 Slice 扩大范围**）
R-8 【低】`.gitignore` 需确认 `config/_build_info.py` 被覆盖（实施首步核验）
R-9 【低】工件为 `.py` ⇒ 被 `tests/security` 扫描（内容无凭据形态，预期无命中；实施时验证）
```

## 8.3 非目标（防止范围蔓延）

```
⛔ 不创建 services/ 包、不实现认证 / 授权 / 租户运行时隔离 / 审计写入器 / 错误处理框架
⛔ 不进入 P10 / P11 / P12 / P13；不做 seed；不做任何 schema 变更
⛔ 不修改任何历史阶段报告与阶段冻结文档正文（仅允许 Charter §5 注记）
```

---

# 9. 实施门禁自评

```
PREP 交付物完整性                 = 完整（本报告 §2 契约 + 独立验收矩阵 + 文件计划 + 差异清单）
只读一致性审计                    = PASS（0 项与冻结决策冲突；0 项覆盖）
决策草案（D-PLAT-13..17）          = 已列精确文本，**未写入**
迁移契约路径差异                  = 已记录（§4.5，不创建别名）
本轮代码 / 配置 / 测试变更         = 0（未修改，未执行测试）
本轮 DB 变更                      = 0（未执行 DDL / DML / migration / seed）

进入实施（IMPLEMENTATION）的前置条件（2026-09-23 Decision Resolution 后的状态）：
  ① Human 授权 §3 的文件变更计划（实施范围）                    —— ⏳ **仍未授权（唯一剩余前置）**
  ② Q-1（决策条目写入）与 Q-2（advisory 范围）                   —— ✅ APPROVED 并已落盘
  ③ Q-3（2000 ms = 实施硬值）                                   —— ✅ APPROVED
  ④ Q-6（实施轮必须交付部署/恢复手册）                           —— ✅ APPROVED
  ⑤ Q-5 / Q-9（A′ + `D-PLAT-15 v2`）· Q-4 · Q-7 · Q-8 · Q-10     —— ✅ APPROVED 并已落盘
  ⇒ **决策侧前置已全部闭环**；实施权限仍未开启。
```

---

**END OF GOVERNANCE / GATE SLICE PREP REPORT（2026-09-23）**
