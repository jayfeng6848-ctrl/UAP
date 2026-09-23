# GOVERNANCE / GATE SLICE — IMPLEMENTATION REPORT

**Stage**: `Governance / Gate Slice`（**不是** Runtime · **不是** `P14`）— `D-PLAT-13`
**Status**: `IMPLEMENTATION COMPLETE` · `VERIFICATION COMPLETE` · `ACCEPTANCE READY`
**Created**: 2026-09-23
**Authority**: `PLATFORM_DECISION_LOG.md`（`D-PLAT-08` · `13` · `14` · `15 v2` · `16` · `17`）·
`GOVERNANCE_GATE_SLICE_PREP_REPORT.md` · `GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md`
**Evidence location**: this document (CI is not part of this slice — `D-PLAT-17` ⑦)

---

## A. Baseline（实施前，STEP 1）

```
HEAD = 71c36c1d5129c4f7f1b0d6a2f67d980711ba70ab · branch = main · staged = 0 · tags = 6 · remotes = none
modified = 6（B-2′ 文档）· untracked = 3（PLATFORM_DECISION_LOG + PREP 报告 + 验收矩阵）
migration chain = 11 revisions · single head = 0011_p09_agent_tool_permission
DB = uap 0 表 · uap_b1_test 31 表 @0011 · uap_test 2 表（legacy 记账）
test baseline（历史）= 272 passed
⇒ 与 HUMAN DECISION RESOLUTION REPORT §A **逐项一致**，无差异需要报告
```

## B. Implementation Files

### B.1 Created（6）

| # | 文件 | 行数 | 理由（决策） |
|---|---|---|---|
| 1 | `config/build_info.py` | 101 | 运行时**唯一**读取入口（`D-PLAT-14` ⑤ / `D-PLAT-15 v2` ③）；含 `REVISION_PATTERN`、`is_valid_revision`、`get_artifact_revision`、`resolve_expected_revision`；**不** import alembic、**不**扫描迁移目录 |
| 2 | `scripts/generate_build_info.py` | 126 | 构建期生成器（`D-PLAT-15 v2` ①）：`ScriptDirectory.from_config` → 唯一 head → 形态校验 → 写工件；`--revision` 仅校验（`v2` ②）；失败 exit 2 |
| 3 | `tests/unit/test_build_info.py` | 123 | 工件权威性 / env 回退 / missing / 形态 / 不 import alembic |
| 4 | `tests/unit/test_generate_build_info.py` | 113 | 唯一 head 推导 + 0/多 head + 形态非法 + override 匹配/不匹配 + 确定性 + 无 DB 驱动/runtime import |
| 5 | `tests/unit/test_migration_state_probe.py` | 222 | 探针全部判定分支 + 短路 + 超时传播 + dispose + 全局默认未变 |
| 6 | `docs/operations/DEPLOYMENT_AND_RECOVERY.md` | 220 | `Q-6` / `Q-10` 交付物：D-R-1…D-R-7 + **F-1** |

### B.2 Modified（17 tracked · 其中 16 为本 Slice 变更）

| 文件 | +/- | 理由（决策） |
|---|---|---|
| `config/settings.py` | +10/−2 | 删 `ENABLE_MIGRATIONS_ON_STARTUP`；加 `EXPECTED_ALEMBIC_REVISION`（非 secret）（`D-PLAT-14` ① / `D-PLAT-07.a`） |
| `apps/api/main.py` | +3/−10 | 删启动迁移分支（`D-PLAT-07.a`） |
| `apps/api/routes/health.py` | +22/−2 | `collect_components()` 追加 critical `migration` 组件（`D-PLAT-08.c` / `D-PLAT-14`） |
| `infrastructure/database/health.py` | +114/−5 | `check_migration_state()` + `READINESS_STATEMENT_TIMEOUT_MS=2000`（`D-PLAT-14` / `D-PLAT-16`） |
| `Dockerfile` | +7/−0 | 构建期执行 generator + 镜像内 artifact 自检；**无 revision ARG**（`D-PLAT-15 v2`） |
| `.gitignore` | +3/−0 | 忽略构建产物 `config/_build_info.py` |
| `.env.example` | +7/−0 | `EXPECTED_ALEMBIC_REVISION=`（空值 + 用途说明，**不写死 revision**）（`D-PLAT-14` ⑥） |
| `tests/unit/test_config.py` | +32/−1 | `SETTING_ENV_KEYS` 同步 + 新键行为（`CFG-04`） |
| `tests/architecture/test_dependency_rules.py` | +94/−4 | `G-1`…`G-5`、`G-7`（`D-PLAT-17`） |
| `tests/contract/test_health_contract.py` | +69/−0 | `G-6` + `/ready` 503/200 + `/health` 零 I/O |
| `docs/api/README.md` | +30/−0 | 实施后事实：readiness 两组件、503 语义、探针性质（`Q-8`） |
| `docs/security/README.md` | +25/−0 | 实施后事实：fail-closed、权威不可漂移、只读探针（`Q-8`） |
| `docs/architecture/DEPENDENCY_RULES.md` | +43/−0 | §7 Enforcement status = **implemented** + 门级表（`D-PLAT-17` ⑧） |
| `docs/architecture/STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` | +4/−0 | §16 Charter §5 注记（启动入口下线；文件与本体保留）（`D-PLAT-07.a`） |
| `docs/architecture/GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md` | 行级 | `BLD-03` / `BLD-04` / `BLD-09` / `GRD-08` 修正 + §5 实施结果回填 |
| `docs/architecture/PLATFORM_DECISION_LOG.md` | 行级 | 附录 C `C-4` → `RESOLVED`（以实际 Guard 实现为准） |

> 说明：`README.md`(+6/−2)、`docs/architecture/ARCHITECTURE.md`(+17/−3)、
> `docs/architecture/MIGRATION_STRATEGY.md`(+6/−0) 属 **B-2′（2026-09-20）** 既有修改，本 Slice **未触碰**。

### B.3 Deleted（0）

`legacy runner` 本体与测试、`migrations/*.sql`、`scripts/migrate.py`、`scripts/doctor.py` **全部保留**（`D-PLAT-07.a` ③④）。

### B.4 明确未创建（按授权边界）

`services/` · 任何 `.github/workflows/` · `config/_build_info.py`（构建产物）· 任何 0012+ migration ·
P10/P11/P14 相关文件 · Adaptive Module Provisioning 相关任何内容（§25）。

## C. Decision Traceability

| 决策 | 实施证据 |
|---|---|
| **`D-PLAT-13`** | 仅文档层：本报告的 stage 标注 + `PLATFORM_DECISION_LOG` 条目；**未创建 `P14` 文件/引用**；`D-PLAT-12`/`12.a` 原文与状态未改 |
| **`D-PLAT-14`** | `config/settings.py`（键、默认空、非 secret、redacted 不遮蔽）· `config/build_info.py`（形态单一来源）· `infrastructure/database/health.py::check_migration_state`（8 类不通过分支 + 短路不查 DB）· `apps/api/routes/health.py`（503 门）· `tests/unit/test_migration_state_probe.py`（17）· `tests/contract/test_health_contract.py`（503/200） |
| **`D-PLAT-15 v2`** | `scripts/generate_build_info.py`（推导唯一 head、形态校验、override 仅校验、fail-fast exit 2）· `config/build_info.py`（工件优先、env 仅回退、missing）· `Dockerfile`（无 ARG；构建期生成 + 自检）· `.gitignore` · `docker-compose.yml` **未改**（无字面量）· 运行时**无** alembic import / 目录扫描（`test_build_info.py` / `test_migration_state_probe.py` 的 AST 断言） |
| **`D-PLAT-16`** | `READINESS_STATEMENT_TIMEOUT_MS = 2000`（`infrastructure/database/health.py`）· 复用 `statement_timeout_ms` + `build_engine` options 通道 · 连接超时 5s 未改 · 全局默认 `None` 未改（`test_global_statement_timeout_default_is_unchanged`）· `finally: dispose()`（2 项测试） |
| **`D-PLAT-17`** | `tests/architecture/test_dependency_rules.py`（`G-1` 新测试、`G-2`/`G-3` 扩充、`G-4`/`G-5`/`G-7` 新增）· `tests/contract/`（`G-6`）· 无 CI（`Q-7`）· 负向样例 14/14 · `DEPENDENCY_RULES.md §7` 门级表 |
| **`D-PLAT-08`（+ 注记）** | `docs/operations/DEPLOYMENT_AND_RECOVERY.md`：D-R-1…D-R-7 全覆盖 + F-1 明确记录 |

## D. Tests

### D.1 硬门（`D-PLAT-17` ⑦；命令 + 退出码留存）

```bash
python -m pytest tests/architecture tests/contract tests/unit -q --no-header -p no:cacheprovider
```
```
结果：114 passed, 1 warning in 2.61s        exit = 0
（1 warning = starlette/anyio 的第三方 DeprecationWarning，非项目代码）
```

### D.2 Guard 负向样例（证明守卫生效，非"恰好没有违规"）

以合成树（`%TEMP%`，**仓库零写入**）注入违规后运行同一守卫函数，再对真实仓库做对照：

```
G-1 core -> sqlalchemy/psycopg    -> 守卫拒绝 ✓   | 真实仓库通过 ✓
G-2 core -> services              -> 守卫拒绝 ✓   | 真实仓库通过 ✓
G-3 agent -> services             -> 守卫拒绝 ✓   | 真实仓库通过 ✓
G-4 domains -> infrastructure     -> 守卫拒绝 ✓   | 真实仓库通过 ✓
G-5 apps -> psycopg（advisory）    -> 守卫拒绝 ✓   | 真实仓库通过 ✓
G-7 startup -> legacy runner      -> 守卫拒绝 ✓   | 真实仓库通过 ✓
G-7 settings 开关回归             -> 守卫拒绝 ✓   | 真实仓库通过 ✓
汇总：14 / 14 PASS（7 负向 + 7 对照）
```

### D.3 定向测试（本 Slice 新增）

```
新增测试文件 3 个（build_info / generator / migration probe）= 46 项
扩充既有：tests/unit/test_config.py（+6）· tests/architecture/test_dependency_rules.py（+5 函数）
         · tests/contract/test_health_contract.py（+4）
```

### D.4 全量回归

```
python -m pytest -q --no-header -p no:cacheprovider
结果：341 passed, 0 failed, 0 error, 1 warning in 1303.24s (21m43s)
基线 272 ⇒ +69 项（>= baseline，无未解释 failure/error/skip）
```

### D.5 发现并修正的测试缺陷（如实披露）

```
1 项首轮 FAIL：test_is_valid_revision 的**测试数据**选了 "2026_09_23"，而该值**确实**匹配冻结形状
`^\d{4}_[a-z0-9_]+$` ⇒ 属测试用例选择错误，**正则未改**（`D-PLAT-14` ⑤ 冻结形状），
已替换为 "001_p09_agent_tool_permission" 等真正非法样例后全绿。
```

## E. DB / Migration

```
✅ 0011 unchanged：sha256(16) = cdaf8383630335db（0010 = 6d9907237f80e9da）
✅ 0012+ absent：migrations_alembic/versions 仍为 11 个 revision
✅ single head = 0011_p09_agent_tool_permission
✅ formal `uap` = 0 表（未触碰；无 alembic_version；无 events/audit_logs）
✅ 一次性验证库 `uap_b1_test`：回归套件结束后被 testkit 置于 base（0 表）⇒ 用仓库自带 testkit
   （`tests.integration.alembic_testkit`）恢复到 head，当前 = 31 表 @0011（= 历次审计记录状态）
   ⚠ 该操作仅作用于一次性验证库；`TEST_DB == "uap_b1_test"` 已断言，**绝不指向** `uap` / `uap_test`
✅ 未执行任何生产备份 / 恢复 / migration / downgrade
```

### E.1 端到端探针验证（真实 PostgreSQL，只读 `SELECT`）

```
match  case -> status=ok    detail={'expected': '0011_p09_agent_tool_permission',
                                    'actual':   '0011_p09_agent_tool_permission', 'source': 'environment'}
                              latency = 39 ms（阈值 2000 ms）
ahead  case -> error  "revision mismatch: expected 0012_future_revision actual 0011_p09_agent_tool_permission"
behind case -> error  "revision mismatch: expected 0010_b1_6_ai_gateway actual 0011_p09_agent_tool_permission"
no-table    -> error  "alembic_version is unreadable: ProgrammingError: (psycopg.errors.UndefinedTable) …"
汇总：6 / 6 PASS（含 T-TO-5 真实库时延）
```

## F. Architecture Boundary

```
Core -> Domain = 0 · Core -> SQLAlchemy/psycopg = 0 · Core -> services = 0
agent -> services = 0 · domains -> services/infrastructure = 0
apps -> sqlalchemy/psycopg = 0（G-5 advisory）· services/ 不存在
（AST 实测 + 硬门测试双证据）
```

## G. Docker

```
✅ no revision ARG（`grep -c "ARG EXPECTED_ALEMBIC" Dockerfile` = 0）
✅ no compose literal（`docker-compose.yml` **未修改**：sha256(16) = bd646ec2717b1beb = 基线）
✅ build generator runs（真实仓库推导 = 0011_p09_agent_tool_permission；0/多 head 与形态非法均 fail-fast）
✅ artifact generated（`render_artifact` 确定性；写出后可 import 且常量正确）
✅ runtime reads artifact（工件优先 / env 仅回退 / missing ⇒ fail closed —— 单测）
❌ 镜像构建（`docker build`）**已尝试但环境受限而失败**（详见 §J U-1）：
   `#2 ERROR: failed to authorize: failed to fetch anonymous token:
    Get "https://auth.docker.io/token…": Bad Gateway` —— 失败发生在 **`FROM python:3.13-slim` 元数据拉取**，
   Dockerfile 的后续指令（含 generator 的 `RUN`）**从未被执行** ⇒ 属**沙箱网络限制**，非 Dockerfile 缺陷
```

## H. Readiness

```
/health          : 200 · 零 I/O（monkeypatch 探针后仍 200 —— 契约测试）
/ready           : 两个 critical 组件（database + migration）；任一 error ⇒ 503
2000 ms          : READINESS_STATEMENT_TIMEOUT_MS（专用探针引擎；全局默认仍为 None）
5 s              : connect_timeout_seconds 未修改
error + critical : 所有失败分支统一 status="error"、critical=True
503 semantics    : 缺失/非法（不查 DB）· 表缺失 · 查询失败 · 0 行 · NULL/空 · 多行 · 严格不等（含领先）
```

## I. Deployment / Recovery

`docs/operations/DEPLOYMENT_AND_RECOVERY.md`（sha256(16) = `cc82f9c3b2f16d6e`）：

```
D-R-1 build revision 来自 artifact（含镜像内读取命令 + 部署记录字段）        ✓
D-R-2 迁移前 pg_dump -Fc + pg_restore --list 验证 + 5 项证据（人工门）      ✓
D-R-3 只允许 alembic upgrade head（禁止 legacy runner / psql DDL）           ✓
D-R-4 maintenance window                                                    ✓
D-R-5 migration 完成后才启动 / rollout 新镜像                                ✓
D-R-6 post-upgrade checks（5 项）                                           ✓
D-R-7 readiness failure decision tree（9 行场景表）                          ✓
F-1   回滚 = 应用 + DB downgrade（或 forward-fix）；备份恢复优先             ✓
```

## J. Final Gate

```
IMPLEMENTATION = PASSED
VERIFICATION   = PASSED
ACCEPTANCE     = READY
```

### 未验证项 / 观察项（不得据本报告推断为已验证）

```
U-1 **【已由 U-1 修复轮取代 — 2026-09-23，见 `GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md §5.1`】**
    首次尝试时 `docker build` 在拉取基础镜像阶段因沙箱网络受限而失败：
```
#2 [internal] load metadata for docker.io/library/python:3.13-slim
#2 ERROR: failed to authorize: failed to fetch anonymous token:
   Get "https://auth.docker.io/token?scope=repository%3Alibrary%2Fpython%3Apull&service=registry.docker.io": Bad Gateway
ERROR: failed to build: failed to resolve source metadata for docker.io/library/python:3.13-slim
```
    失败点 = `Dockerfile:1`（`FROM`）⇒ **Dockerfile 后续指令未被求值**，无法据此判定镜像层正确性，
    也无法判定其错误。⇒ `DOC-01` 保持 **PARTIAL（未验证）**；**需 Human 决定**是否在有网环境补做。
    已完成的等价验证：同一 Python 3.13 环境下 generator 真实推导 + 工件写出 + 工件被 `config/build_info`
    读取（单测）——即 RUN 的**命令语义**已验证，仅"在容器内"这一层未验证。
    ⇒ **后续进展（U-1 修复轮，2026-09-23）**：网络恢复后真实构建得以推进到 `[6/6]`，并暴露出
    **实现缺陷**（`Dockerfile` 以 `python scripts/generate_build_info.py` 调用生成器 ⇒ `sys.path[0]`
    为 `scripts/` 而非仓库根 ⇒ `ModuleNotFoundError: No module named 'config'`，构建失败）。
    经最小修复（改用 `python -m scripts.generate_build_info`）后，`docker build --no-cache`
    = **exit 0**，工件在镜像内生成且 `source == "build_artifact"`；`DOC-01` 由 **PARTIAL** 更正为
    **PASS**。⇒ 本节中「`DOC-01` 保持 **PARTIAL（未验证）**」及「仅"在容器内"这一层未验证」的表述
    **已被取代**；原始失败日志保留于上文以存证。
U-2 §G 中「build generator runs / artifact generated / runtime reads artifact」三项均已验证；
    唯一未验证的是"在真实镜像内"这一容器层事实。
U-3 运行时"**不** import alembic / **不**扫描迁移目录"目前由**单测 AST 断言**（build_info、
    migration probe）覆盖，**未**新增独立 Guard 编号（未获授权新增 Guard，§27.16）⇒ 若需硬门化，
    须另行授权（例如作为 `G-10`）。
U-4 未建立 CI（`Q-7` 已裁定）：硬门执行与证据留存依赖人工，本报告即为证据载体。
U-5 `docs/architecture/GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX.md` 中未逐行更新的行仍保留
    原始 `NOT IMPL/PARTIAL/OK` 登记；其实现状态以该文件 §5「实施结果回填」为准。
```

### Git（未 commit / 未 tag / 未 push）

```
HEAD = 71c36c1d5129c4f7f1b0d6a2f67d980711ba70ab（未推进）
staged = 0 · tags = 6 · remotes = none
worktree = 17 modified（tracked：+492 / −29）+ 10 untracked
untracked = config/build_info.py · scripts/generate_build_info.py ·
            tests/unit/{test_build_info,test_generate_build_info,test_migration_state_probe}.py ·
            docs/operations/DEPLOYMENT_AND_RECOVERY.md ·
            docs/architecture/{GOVERNANCE_GATE_SLICE_PREP_REPORT,GOVERNANCE_GATE_SLICE_ACCEPTANCE_MATRIX,
            GOVERNANCE_GATE_SLICE_IMPLEMENTATION_REPORT,PLATFORM_DECISION_LOG}.md
DB（终态）= formal `uap` 0 表 · `uap_b1_test` 31 表 @0011_p09_agent_tool_permission
```

---

**END OF GOVERNANCE / GATE SLICE IMPLEMENTATION REPORT（2026-09-23）**
