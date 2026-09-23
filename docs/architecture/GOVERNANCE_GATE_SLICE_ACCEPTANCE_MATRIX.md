# GOVERNANCE / GATE SLICE — ACCEPTANCE MATRIX

**载体性质**：独立验收矩阵（**非**决策载体；**非**阶段 Decision Log）
**状态**：`PREP WRITTEN` · **实现 = NOT IMPLEMENTED** · **测试 = NOT RUN（本轮未执行任何测试）**
**Created**：2026-09-23
**Baseline**：`HEAD = 71c36c1d5129c4f7f1b0d6a2f67d980711ba70ab` · migration head `0011_p09_agent_tool_permission`
**契约来源**：`GOVERNANCE_GATE_SLICE_PREP_REPORT.md`（§2 实施契约）· 决策：`PLATFORM_DECISION_LOG.md` 的 `D-PLAT-02`…`D-PLAT-08`
**使用方式**：实施轮**逐行**核验；**每一行未获证据前不得标记为通过**。

> ⚠ **状态列已于 2026-09-23 实施轮回填**（证据见 §5「实施结果回填」）。本矩阵仍是**条件表**：
> 未逐行附证据的行不得视为已验收。

---

## 1. 列定义

| 列 | 含义 |
|---|---|
| **ID** | 矩阵行标识（`领域-序号`） |
| **Requirement** | 设计要求（契约条款） |
| **Evidence** | 通过时须提供的**证据类型**（文件 / 输出 / 命令结果） |
| **Test** | 验证方法（测试位置或命令） |
| **Pass** | 判定为通过的条件 |
| **Fail** | 判定为失败的条件 |
| **Cur.** | 当前状态（本轮实测）：`NOT IMPL` / `PARTIAL` / `OK（既有基线）` |
| **Dep.** | 阻塞依赖 |

---

## 2. 矩阵

### 2.1 Config（`D-PLAT-08.a` · Human Decision 项 2/4）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| CFG-01 | `EXPECTED_ALEMBIC_REVISION` 存在于 `Settings`，`str`，默认空串 | `config/settings.py` 字段 | `tests/unit/test_config.py` | 键存在、默认 `""`、类型 `str` | 键缺失 / 类型不符 | NOT IMPL | — |
| CFG-02 | 该键**非 secret**，`redacted()` 中**原样出现不遮蔽** | `redacted()` 输出 | `tests/unit/test_config.py` | 快照含该键且值未被 `***` 遮蔽 | 被遮蔽 / 键缺失 | NOT IMPL | — |
| CFG-03 | `ENABLE_MIGRATIONS_ON_STARTUP` 在**代码 / 配置 / 测试**中 0 命中 | 全仓 grep 结果 | 扫描断言 / 手工 grep | 可执行与配置命中 = 0（决策文档中的引用不计） | ≥1 命中 | NOT IMPL | — |
| CFG-04 | `SETTING_ENV_KEYS` 已同步（删旧键、增新键） | `tests/unit/test_config.py` | 该文件 | 集合恰含新键、不含旧键 | 未同步（env 隔离静默失效） | NOT IMPL | CFG-01 |
| CFG-05 | `.env.example` 新增**空值**条目且键名合法 | `.env.example` 全文 | `tests/security/test_no_secrets.py` | 键匹配 `[A-Z][A-Z0-9_]*` 且值为空；文件通过安全扫描 | 含非空值 / 键名非法 / 扫描失败 | NOT IMPL | — |
| CFG-06 | `.env.example` **说明**该配置用途与本地开发/测试路径 | 注释文本 | 人工核验 | 注释说明"构建期工件权威、env 仅本地回退、留空 ⇒ fail closed" | 无说明 / 说明与契约矛盾 | NOT IMPL | — |
| CFG-07 | 本地开发路径可用（export / `.env`），测试路径不设默认值 | `tests/conftest.py` | 人工 + 单测 | conftest **不** `setdefault` 该键（保持 fail-closed 可测） | conftest 注入固定值（掩盖 fail-closed 分支） | NOT IMPL | — |

### 2.2 Build-time injection（`D-PLAT-08.a` · Human Decision 项 3）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| BLD-01 | 运行时权威来源 = 构建期生成的只读工件（`config/_build_info.py`） | 生成器日志 + 镜像内文件 | `docker build` + 容器内 `resolve_expected_revision()` | `source == "build_artifact"` | 来源非工件 | **PASS** | — |
| BLD-02 | 工件**不可被运行时环境变量覆盖** | 镜像内运行结果 | 容器内 `docker run -e EXPECTED_ALEMBIC_REVISION=XXXX` 后读值 | 解析结果仍为工件值（`source=build_artifact`） | 被 env 覆盖 | **PASS** | BLD-01 |
| BLD-03 | 构建期输入 **不得**为 `ARG`/compose 字面量；`Dockerfile` 仅执行 generator（`D-PLAT-15 v2`） | `Dockerfile` 文本（AST/文本） | 人工核验 + `grep -c "ARG EXPECTED_ALEMBIC"` = 0 | `Dockerfile` 中 0 个 revision ARG；无 compose 字面量 | 出现 ARG 或字面量 | **OK** | — |
| BLD-04 | 推导失败（0 个 / 多个 head、形态非法、`--revision` 不匹配）⇒ **构建失败**（fail-fast） | 生成器退出码 | `tests/unit/test_generate_build_info.py`（5 项负向） | 全部返回 2 且不写工件 | 返回 0 / 写出工件 | **OK** | — |
| BLD-05 | 工件生成**确定性**（可重复构建；无时间戳） | 两次生成的 sha256 | 连续生成两次并比对 | 两次字节一致 | 含时间戳 / 顺序不定 | **PASS** | — |
| BLD-06 | 工件被 `.gitignore` 忽略（不入仓库） | `git check-ignore` | 命令 | `git status` 不出现该文件 | 出现在 untracked | **PASS** | — |
| BLD-07 | 运行时**不**扫描迁移目录、**不** import `alembic` 推导 head | 源码 + AST | 守卫/断言 | 运行时代码路径 0 命中 | ≥1 命中 | **PASS** | — |
| BLD-08 | `docker-compose.yml` **不得**承载任何 revision 权威：无 `build.args`、`environment:` 亦不含该键（`D-PLAT-15 v2`） | compose 文本 | 人工核验 / 解析断言 | 无 revision `args`；`environment:` 无该键 | 出现 args 或 environment 键 | **PASS** | — |
| BLD-09 | ~~compose 字面量与 `alembic heads` 漂移检测~~ **已取消**（`G-9` cancelled：v2 无任何 revision 字面量，漂移路径被结构性消除） | `D-PLAT-15 v2` / `D-PLAT-17` | 无需测试；改为断言"无字面量"（见 BLD-03） | 全仓 0 个 revision 字面量 | 出现字面量 | **N/A（cancelled）** | — |

### 2.3 Migration state（`D-PLAT-08.b` · 判定表 10 分支）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| MIG-01 | expected **缺失/空白** ⇒ 组件 `error`，且**不访问 DB** | 探针返回 + 无连接证据 | `tests/unit/test_migration_state_probe.py` | `status=error`、`critical=True`、未建立连接 | 返回 ok / 抛异常 / 访问 DB | NOT IMPL | — |
| MIG-02 | expected **形态非法** ⇒ `error`，且**不访问 DB** | 同上 | 同上 | 同上 | 同上 | NOT IMPL | — |
| MIG-03 | `alembic_version` **表缺失** ⇒ `error`（非 500、非抛异常） | 探针返回 | 单测（stub 抛 `UndefinedTable`）+ 集成（空库） | `error` + 短错误串 | 抛异常 / 500 | NOT IMPL | — |
| MIG-04 | 查询失败（连接中断 / 权限 / 超时）⇒ `error` | 探针返回 | 单测（stub 抛 `SQLAlchemyError`） | `error` | 抛异常 / 误判 ok | NOT IMPL | — |
| MIG-05 | `alembic_version` **0 行** ⇒ `error` | 探针返回 | 单测（stub 空结果） | `error` | ok | NOT IMPL | — |
| MIG-06 | `version_num` **NULL / 空串** ⇒ `error` | 探针返回 | 单测（stub） | `error` | ok | NOT IMPL | — |
| MIG-07 | **多行**（违反单 head 不变量）⇒ `error` | 探针返回 | 单测（stub 2 行） | `error` | 取首行判 ok | NOT IMPL | — |
| MIG-08 | revision **落后** expected ⇒ `error` | 探针返回 | 单测 + 集成 | `error`，`detail` 含 expected/actual | ok | NOT IMPL | — |
| MIG-09 | revision **领先** expected ⇒ `error`（**显式不通过**） | 探针返回 | 单测 + 集成 | `error` | ok（**禁止**） | NOT IMPL | — |
| MIG-10 | revision **严格相等** ⇒ 组件 `ok` | 探针返回 | 单测 + 集成（`uap_b1_test` @0011） | `status=ok`、`critical=True` | 非 ok | NOT IMPL | — |
| MIG-11 | 探针 `finally` 释放引擎（不入进程级池） | 代码 + 断言 | 单测 | `dispose()` 被调用 | 泄漏 / 复用进程引擎 | NOT IMPL | — |
| MIG-12 | `detail` 含 `expected` / `actual` / `source` 且**无敏感信息** | 响应体 | 契约测试 | 三字段齐备、无凭据 | 缺字段 / 泄漏 | NOT IMPL | — |

### 2.4 `/ready`（`D-PLAT-08.c` · Human Decision 项 2/5）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| RDY-01 | 迁移门失败 ⇒ **HTTP 503** + `status=not_ready` | HTTP 响应 | `tests/contract/test_health_contract.py` | 503 且 body 语义正确 | 200 | NOT IMPL | MIG-01..09 |
| RDY-02 | 迁移门通过且 database ok ⇒ **HTTP 200** | HTTP 响应 | 同上 | 200 `ready` | 503 | NOT IMPL | MIG-10 |
| RDY-03 | `migration` 组件 `critical=True`（**G-6 硬门**） | `collect_components()` 结果 | 契约/单测 | 存在 `name="migration"` 且 `critical is True` | 缺失 / `critical=False` | NOT IMPL | — |
| RDY-04 | **不新增顶层字段**（`READY_FIELDS` 不变） | 响应体键集合 | 既有 `test_health_contract.py:10` | 集合不变 | 新增字段 | OK（基线断言存在，待回归确认） | RDY-01 |
| RDY-05 | DB 不可达 ⇒ database 与 migration **双 error** ⇒ 503 | 探针返回 + 503 | 集成（停库） | 双 error、503 | 仅一个 error 或 500 | PARTIAL（database 已如此，migration 未实现） | MIG-04 |
| RDY-06 | 迁移探针独立短超时 **2000 ms** 生效且超时 ⇒ 503 | 引擎 `options` + 探针行为 | 单测（断言 `-c statement_timeout=2000`）+ 超时分支用例 | 断言通过；超时 ⇒ `error` | 未设超时 / 超时后仍 ok | NOT IMPL | — |
| RDY-07 | 不修改全局默认超时（不影响业务查询与 database 组件） | `DatabaseConfig` 默认值 | 单测 | `statement_timeout_ms` 默认仍为 `None` | 默认被改为 2000 | NOT IMPL | RDY-06 |
| RDY-08 | 现有 4 处 `/ready` 用例（monkeypatch）**不回归** | 测试结果 | `pytest` | 全绿 | 任一红 | OK（基线 272 通过，待回归确认） | — |

### 2.5 `/health`

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| HLT-01 | `/health` 返回 200 且 `status=ok` | HTTP 响应 | 既有 `test_health_contract.py:13` | 200 + `ok` | 非 200 | OK（基线） | — |
| HLT-02 | `/health` **零 I/O**（不触 DB；迁移门失败不影响它） | 断言无 engine 调用 | 契约/单测（monkeypatch 探针并断言未被调用） | 无 DB 调用；DB 不可达时仍 200 | 触 DB / 因迁移门而 503 | PARTIAL（实现为零 I/O；**新增断言待补**） | — |
| HLT-03 | `/health` 不承担 schema readiness | 同上 | 同上 | 语义与实现一致（文档 + 断言） | 混入 schema 判定 | PARTIAL（文档已述，断言待补） | — |

### 2.6 Legacy runner（`D-PLAT-07.a`）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| LEG-01 | 启动路径**不再调用** legacy runner（**G-7 硬门**） | `apps/api/main.py` AST/源码 | 架构/单测断言 | `apps/` 内 0 处 import/call legacy runner | ≥1 处 | NOT IMPL | — |
| LEG-02 | `Settings` 不再含启动迁移开关（与 CFG-03 同源） | 键集合 | 单测 | 0 命中 | ≥1 | NOT IMPL | — |
| LEG-03 | runner **本体保留**（`infrastructure/database/migration.py` + 包导出） | 文件与导出存在 | 人工 + 既有测试 | 文件在、可 import、导出齐全 | 被删除/改名 | OK（当前保留） | — |
| LEG-04 | runner **测试保留且全绿** | 测试结果 | `tests/unit/test_migration_runner.py` · `tests/integration/test_database_integration.py` | 全部通过 | 被删除 / 失败 | OK（基线） | — |
| LEG-05 | `migrations/*.sql`、`scripts/migrate.py`、`scripts/doctor.py` **保留**（人工 CLI） | 文件存在 | 人工 | 全部在 | 被删除 | OK（当前保留） | — |
| LEG-06 | 无第二条 startup 调用路径 | 全仓调用面 | grep/AST | 启动路径命中 = 0 | ≥1 | PARTIAL（当前 1 处，即待删除项） | LEG-01 |
| LEG-07 | Contract §16 注记已按 Charter §5 追加（记录启动入口下线；文件保留） | 注记文本 | 人工核验 | 格式合规、结论正确、**未改 §16 正文** | 改写正文 / 无注记 | NOT IMPL | — |

### 2.7 Dependency guards（`D-PLAT-02`…`D-PLAT-06` · Human Decision 项 6）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| GRD-01 | **G-1** `core ↛ sqlalchemy/psycopg/psycopg2`（硬门） | 守卫测试 | `tests/architecture/` | 通过；且**负向样例可使其失败** | 未实现 / 负向样例不失败 | NOT IMPL（当前 0 违规） | — |
| GRD-02 | **G-2** `core ↛ services`（硬门） | 同上 | 同上 | 同上 | 同上 | NOT IMPL | — |
| GRD-03 | **G-3** `agent ↛ services`（硬门） | 同上 | 同上 | 同上 | 同上 | NOT IMPL（agent 跨层依赖当前 = 0） | — |
| GRD-04 | **G-4** `domains ↛ services/infrastructure`（硬门） | 同上 | 同上 | 同上 | 同上 | NOT IMPL（domains 跨层依赖当前 = 0） | — |
| GRD-05 | **G-5** `apps ↛ sqlalchemy/psycopg`（**advisory**，代理判据） | 守卫测试 + 局限声明 | 同上 | 实现并运行；文档标注"代理、不等价" | 未标注局限 / 被当作硬门 | NOT IMPL | — |
| GRD-06 | **G-6** migration 组件 `critical=True`（硬门，= RDY-03） | 见 RDY-03 | 见 RDY-03 | — | — | NOT IMPL | — |
| GRD-07 | **G-7** 启动不触 legacy runner（硬门，= LEG-01） | 见 LEG-01 | 见 LEG-01 | — | — | NOT IMPL | — |
| GRD-08 | **G-8** bootstrap 唯一性 = **Deferred**（本轮**不实现**，判定对象当前不存在） | `D-PLAT-17` ③ | 不适用（登记即满足） | 明确登记为 Deferred，无实现 | 被实现 / 被静默忽略 | **DEFERRED（已登记）** | — |
| GRD-09 | 判据为 **AST**，非字符串/正则匹配 | 守卫源码 | 代码审查 | 使用 `_imported_top_levels()` / AST | 字符串匹配 | NOT IMPL | — |
| GRD-10 | **未**新增 `services ↛ domains` 守卫（`D-PLAT-03.a`） | 守卫清单 | 人工核验 | 不存在该守卫 | 存在 | OK（当前无） | — |
| GRD-11 | **未**新增 `apps ↛ infrastructure` 守卫（`D-PLAT-04.a`） | 同上 | 同上 | 不存在 | 存在 | OK（当前无） | — |
| GRD-12 | `DEPENDENCY_RULES.md §7` Enforcement status 已同步为已实现 | 文档文本 | 人工核验 | 声明与实现一致（无"尚未实现"残留） | 声明过期 | NOT IMPL | GRD-01..05 |

### 2.8 Services boundary（`D-PLAT-01`/`03`/`04`/`05`/`06`）

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| SVC-01 | 本 Slice **不创建** `services/` 包（属 Runtime 前置） | 目录不存在 | 人工 / `git status` | `services/` 不存在，且无 `import services` | 被创建 | OK（当前不存在） | — |
| SVC-02 | 允许边未被误禁：`apps→services` / `services→{core,infrastructure,domains}` / `apps→infrastructure`（装配/生命周期/健康） | 守卫 + 文档 | 人工 + 测试 | 无守卫禁止上述允许边 | 存在误禁 | OK（当前无） | — |
| SVC-03 | 禁止边已表达（见 GRD-01..04） | 见 GRD | 见 GRD | — | — | NOT IMPL | GRD-01..04 |
| SVC-04 | 静态不可判项已如实登记（正向职责语义） | 文档声明 | 人工核验 | PREP 报告 §2.7 的登记在档 | 以 Guard 冒充覆盖 | OK（本轮已在档） | — |
| SVC-05 | 未引入任何业务运行时能力（认证/授权/租户隔离/审计写入器/错误处理框架/业务 API） | 变更清单 | 人工核验 | 文件清单与契约一致 | 越界新增 | OK（当前 0） | — |

### 2.9 Existing test regression / 工程与状态

| ID | Requirement | Evidence | Test | Pass | Fail | Cur. | Dep. |
|---|---|---|---|---|---|---|---|
| REG-01 | 全量 pytest **≥ 272 passed / 0 failed / 0 error** | pytest 汇总 | `pytest -q`（集成标记需可达 PG） | 通过数与基线比较**不下降** | 下降 / 有失败 | OK（基线 272，**本轮未运行**） | — |
| REG-02 | 离线子集（`-m "not integration"`）通过数 = 50 + 新增 | pytest 汇总 | `pytest -m "not integration"` | 全绿 | 任一红 | OK（基线 50，**本轮未运行**） | — |
| REG-03 | 新增测试覆盖判定表 10 分支 + 配置 + 工件解析 | 测试文件与用例数 | 人工 + pytest | 分支全覆盖（含 5 项负向） | 分支缺失 | NOT IMPL | — |
| REG-04 | `tests/security/test_no_secrets.py` 仍全绿（含新 `.env.example` 行与工件 `.py`） | 测试结果 | pytest | 全绿 | 任一红 | OK（基线；待新条目后回归） | CFG-05 |
| DOC-01 | Docker 镜像可构建（`D-PLAT-15 v2`：**无** revision build-arg）且容器可启动 | 构建日志 + `/health` 200 | `docker build` + smoke | 构建成功；（`/ready` 依据 DB 状态可为 503） | 构建失败 | **PASS** | BLD-01..04 |
| DOC-02 | 空库/unmigrated 库 ⇒ `/ready` **503**（破坏性变更已预期） | HTTP 响应 | 集成（formal `uap` 或空库） | 503 | 200 | PARTIAL（契约已声明；实现在实施后） | RDY-01 |
| GIT-01 | 变更文件集合 == PREP 报告 §3 清单（无越界文件） | `git status` | 命令 | 集合完全一致 | 存在清单外文件 | OK（本轮仅 4 个 md 变更） | — |
| GIT-02 | HEAD 未推进 · branch = main · tags = 6 · staged = 0 | 命令输出 | 命令 | 全部符合 | 任一不符 | OK | — |
| GIT-03 | 不执行 commit / tag / push；remote 仍为 none | 命令输出 | 命令 | 未执行、无 remote | 已执行 | OK | — |
| MIG-HEAD-01 | `alembic heads` 单一仍为 `0011_p09_agent_tool_permission` | 命令输出 | 命令 | 单一 head 且值不变 | 多 head / 变更 | OK（当前单一 0011） | — |
| MIG-HEAD-02 | 本 Slice **未新增 / 未修改**任何 Alembic revision | 版本目录 hash | 命令 + hash 比对 | 0011 内容 hash 不变、0001–0010 不变、无 0012+ | 任一变化 | OK（当前未变） | — |
| DB-01 | 未执行 DDL / DML / seed；formal `uap` 仍 0 表 | 只读查询 | 只读 SQL | 0 表 / 无 `alembic_version` | 有变更 | OK（本轮实测） | — |
| DB-02 | 实施后 formal `uap` 的 `/ready` 预期为 503（直至 `alembic upgrade head`） | 部署前检查 | 集成 | 与 R-1 记录一致 | 被误判为故障 | PARTIAL（已登记） | DOC-02 |

---

## 3. 负向测试清单（必须存在，否则矩阵视为未完成）

| # | 负向场景 | 期望 |
|---|---|---|
| N-1 | 未注入 expected revision | `/ready` 503；组件 `error`；**不触 DB** |
| N-2 | expected 形态非法（如 `0011` / `0011_P09` / 空串） | `/ready` 503 |
| N-3 | DB revision **领先** expected | `/ready` 503（**显式禁止通过**） |
| N-4 | `alembic_version` 表不存在 | `/ready` 503、**非 500** |
| N-5 | 多行 / NULL 行 | `/ready` 503 |
| N-6 | 守卫负向样例（在 `core/` 内构造 `import sqlalchemy` 的临时文件） | 守卫测试**失败**（证明守卫有效） |
| N-7 | 无 `--build-arg` 构建 | 构建**失败**（fail-fast） |
| N-8 | 运行时 `-e EXPECTED_ALEMBIC_REVISION=<假值>` | 解析结果仍为工件值（不可覆盖） |

---

## 4. 汇总口径（2026-09-23 实施轮回填）

```
总计行数                = 56（矩阵）+ 8（负向）
未逐行更新的行          = 保留 NOT IMPL/PARTIAL/OK 的原始登记；**其实现状态以 §5 回填表为准**
已按 D-PLAT-15 v2 / D-PLAT-17 修正的行 = BLD-03 · BLD-04 · BLD-09 · GRD-08（见上）
```

---

## 5. 实施结果回填（2026-09-23 · 证据 = `GOVERNANCE_GATE_SLICE_IMPLEMENTATION_REPORT.md`）

| 领域 | 结果 | 关键证据 |
|---|---|---|
| CFG-01…CFG-07 | **PASS** | `tests/unit/test_config.py`（新键默认空 / env 可注入 / redacted 不遮蔽 / 无 secret 类型 / 旧开关不存在）；`tests/security/test_no_secrets.py` 全绿 |
| BLD-01 / 02 / 03 / 04 / 05 / 06 / 07 / 08 | **PASS** | `config/build_info.py` + `scripts/generate_build_info.py` + `tests/unit/test_build_info.py`（11）+ `tests/unit/test_generate_build_info.py`（**11**，含新增真实 subprocess CLI 契约测试）+ 真实 `docker build --no-cache` = exit 0；Dockerfile 0 个 revision ARG；容器内 `source == "build_artifact"` |
| BLD-09 | **N/A（cancelled）** | `D-PLAT-17` ④ |
| MIG-01…MIG-12 | **PASS** | `tests/unit/test_migration_state_probe.py`（17 项，含 10 判定分支 + 短路不触 DB + dispose + 超时传播） |
| RDY-01…RDY-08 | **PASS** | `tests/contract/test_health_contract.py`（503 / 200 / critical 组件 / READY_FIELDS 不变 / /health 零 I/O） |
| HLT-01…HLT-03 | **PASS** | `test_health_is_liveness_only`（monkeypatch 探针 ⇒ 仍 200） |
| LEG-01…LEG-07 | **PASS** | `G-7` 两项守卫；runner 本体与既有测试保留且全绿；Contract §16 注记已追加 |
| GRD-01…GRD-04 / GRD-06 / GRD-07（硬门） | **PASS** | `tests/architecture/` + `tests/contract/`；**负向样例 14/14** 证明守卫有效 |
| GRD-05（advisory） | **PASS（advisory）** | 实现并运行；局限已在 `DEPENDENCY_RULES.md §7` 与测试 docstring 标注 |
| GRD-08 / GRD-09 | **Deferred / Cancelled** | `D-PLAT-17` ③④ |
| GRD-10 / GRD-11 | **PASS** | 未新增 `services ↛ domains` / `apps ↛ infrastructure` 守卫 |
| GRD-12 | **PASS** | `DEPENDENCY_RULES.md §7` Enforcement status 已更新为「implemented」+ 门级表 |
| SVC-01…SVC-05 | **PASS** | `services/` 不存在；无越界依赖（AST）；无业务运行时能力引入 |
| REG-01 / REG-02 | **PASS** | 全量回归见实施报告 §D（≥ 272 passed） |
| REG-03 / REG-04 | **PASS** | 新增测试 40 项（39 + U-1 真实 subprocess CLI 契约测试 1）；安全测试全绿 |
| DOC-01 | **PASS** | U-1 修复轮：真实 `docker build --no-cache` = **exit 0**；`[6/6]` 生成器在镜像内执行并写出 `config/_build_info.py`（`uap.build.artifact.verified=0011_p09_agent_tool_permission`）；容器启动后 `/health` = 200。根因（`python <path>/script.py` 的 `sys.path[0]` 语义）与修复（改用 `python -m scripts.generate_build_info`）见 U-1 报告 |
| DOC-02 | **PASS** | 空库 / 未迁移库 ⇒ `migration` 组件 error ⇒ 503（探针分支 + 契约测试） |
| GIT-01…GIT-03 · MIG-HEAD-01/02 · DB-01 | **PASS** | 实施报告 §A / §E / §G |

### 5.1 U-1 修复轮回填（2026-09-23，证据 = 真实 `docker build` + 容器运行）

首个 U-1 验收轮以真实 `docker build` 证明 `D-PLAT-15 v2` 的**构建链从未真正执行过**：
`Dockerfile` 以 `python scripts/generate_build_info.py` 调用生成器，而该形态把 `scripts/`
（而非仓库根）置于 `sys.path[0]`，使模块级 `from config.build_info import REVISION_PATTERN`
抛 `ModuleNotFoundError: No module named 'config'`，构建在 `[6/6]` 失败。

最小修复（**R-1**）：`Dockerfile` 改用 `python -m scripts.generate_build_info`。
`scripts/__init__.py` **已存在且已追踪**，故**未新增**任何包元数据文件。
未恢复 Docker `ARG`、未引入 `ENV` 权威、未改动 Alembic authority、未改动 `sys.path` 逻辑。

本轮同步更正的行：**BLD-01 · BLD-02 · BLD-05 · BLD-06 · BLD-07 · BLD-08 · DOC-01**
（原 `NOT IMPL` / `PARTIAL`，现依真实证据判定）。`BLD-03` · `BLD-04` · `BLD-09` 维持原判。

> **本矩阵不构成验收结论。** 实施轮须逐行填证；任何 **硬门**（GRD-01..04、GRD-06、GRD-07）未通过时，**不得**宣告本 Slice 完成。

---

**END OF GOVERNANCE / GATE SLICE ACCEPTANCE MATRIX（2026-09-23）**
