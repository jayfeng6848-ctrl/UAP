# OPEN-P10-1 BATCH-B EXECUTION AUTHORIZATION REQUEST

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-B EXECUTION AUTHORIZATION PREP
> 模式      = IMPLEMENTATION MODE = PREP ONLY · STOP-GATED = ENABLED · STRICT READ-ONLY
> 文件性质  = **REQUEST**（请求 · 未授权 · 未实施）
> 目标      = 把 BATCH-B（migration/runtime 配置分离）的**开工授权**摆到 Human 面前；**不自行开工**
> as-of 锚点 = HEAD 034ee97c… · 分支 main · tags 8 · remote none · 单头 0015_p12_indexes
>             PDL sha256 a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
>             0007 sha256 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef
>             C2 md5(pg_get_functiondef) 6867874166ae36966763c1026ab2af19 · 触发器 31|O|0
> 有效期    = 基线若变（HEAD / 上述 sha / 0016-0017 状态 / 角色数 / 所有权计数）须**重新签发**
> Gate      = 73 / 73 PASS（exit 0）· 证据 ../uap-stage3-evidence/open_p10_1_batch_b_authz_request_gate.log
> 自证缺陷  = 真实缺口 **0** · harness 实测失败 **3 项**（修正后 73/73）· 预防性规避 **4 项**（见 §6.4）
> 本轮未做  = 无任何 mutation：`env.py` / `settings.py` / `alembic.ini` / `.env.example` / compose /
>             testkit / conftest **未修改** · 无 migration 创建 · 无 `alembic upgrade|downgrade` ·
>             无 DDL/DML · 无角色创建或修改 · 无 `GRANT`/`REVOKE` · 无 `commit` / `tag` / `push`
> ```

---

## §1 状态声明

### §1.1 三条不得混淆

```text
① 本请求 ≠ 授权                  —— 本文件是 REQUEST；在 §6 的答复行被提供之前，
                                    `BATCH-B = NOT STARTED`，任何配置修改均不得发生。
② 授权 ≠ 实施完成                —— 获授权只解除"开工"门槛；BATCH-B 仍须按 §6 Stop Gate
                                    逐项留存证据，`PASSED` 仅在证据齐备后填写。
③ 实施授权 ≠ 解除后续专项门槛     —— 本批**不触碰** C2 / 触发器 / 角色 / 授权 / 所有权 /
                                    migration 创建；`CC-7` 仍归 BATCH-C，`0016` 仍须独立授权。
```

### §1.2 当前权威状态（as-of §0 锚点）

```text
OPEN-P10-1 DECISION FREEZE   = FROZEN（D-OP101-01…14 全 FROZEN · 载体 sha 未变）
OPEN-P10-1 REVISION RESOLUTION = PASS（已结项 · 目标 revision 0016_open_p10_1_trust_boundary）
BATCH-A                      = PASSED（A-1…A-5 全 PASS · 独立复算 Gate 69/69）
BATCH-B                      = **NOT STARTED**（本请求对象）
BATCH-C / BATCH-D            = NOT AUTHORIZED
OPEN-P10-1 IMPLEMENTATION    = IN PROGRESS（BATCH-A 已完成 · 等 BATCH-B 开工授权）
P13 IMPLEMENTATION           = NOT AUTHORIZED
0016 / 0017                  = ABSENT / ABSENT
```

### §1.3 本请求依据的裁定（逐条点名，不新增）

| 依据 | 内容 |
|---|---|
| **`CF-BA-1 = NEW`** | 采用**当前**批次边界：`BATCH-B = config separation`（旧 `REQ-5-CUSTOM` 把 configuration foundation 归 BATCH-A 的分组**不再沿用**） |
| **`D-OP101-10`**（FROZEN · `OQ-OP101-10 = ACCEPT OPTION A`） | **independent migration/runtime keys + explicit resolution chain**；`禁止`：不得保留"runtime 的键决定迁移身份"的倒置；不得以部署纪律替代**可验证**的键分离 |
| **`R-02`**（实施契约 §5 · 重点风险） | `R-02.1` 风险陈述 · `R-02.2` 配置隔离需求 · `R-02.3` 解析优先级调整需求（**要求，非实现**）· `R-02.4` 回滚风险（**须同时回退 6 处**） |
| **`OI-B-4 = CONFIRM` → `CF-R-1`** | 生效键名 = `UAP_MIGRATION_DATABASE_URL`；**登记差异**：≠ 更早请求 `REQ-6` 选项 `A`（`MIGRATION_DATABASE_URL`）⇒ 本请求 `CF-BB-2` 提供**最终确认点** |
| **`OI-B-6 = B`** | C2 授权采**语义授权**（无需逐字行）—— 与本批无关（BATCH-B **不触碰** C2） |

---

## §2 执行范围

### §2.1 IN —— BATCH-B 唯一目标

```text
migration / runtime 配置分离（configuration separation）
```

即：使**迁移身份**与**运行时身份**在**配置层可区分**且**不可互相覆盖**，并把 DSN 解析链**显式化**。
本批**只做配置与解析链**，不做任何连接切换、不做任何数据库变更。

### §2.2 OUT —— 明确不在本批范围

```text
migration creation（0016 / 0017 创建）        · alembic upgrade / downgrade
database schema 变更（DDL / DML）             · migration file 修改
C2 function 改动                              · trigger modification
ownership change（ALTER OWNER）               · grants change（GRANT / REVOKE）
role change（CREATE ROLE / ALTER ROLE / DROP）· runtime code behavior 变更
runtime cutover（实际连接切换到 uap_app）      · BATCH-C / BATCH-D 任何动作
正式库 uap 的任何操作（uap = EXCLUDED）        · commit / tag / push
```

### §2.3 配置分离目标 —— 结构候选（**描述性 · 非代码补丁**）

> 说明：下列为**语义结构描述**，用于 Human 裁定 `CF-BB-1`；**不构成**代码补丁、diff 或可直接落地的实现文本。

**现状（基线 `C-1`，逐字）**：`env.py::_resolve_url()` 优先级 = ① `config.attributes["url"]` → ② **`DATABASE_URL` env** → ③ `alembic.ini::sqlalchemy.url`；而 runtime 亦读**同一** `DATABASE_URL`（`config/settings.py:57`）。
⇒ 「谁是迁移」与「谁是运行时」在配置层**不可区分**（`R-02.1`）。

| 候选 | 语义 | 与 `D-OP101-10` 的关系 |
|---|---|---|
| **`BB-S1` 保持旧结构** | 维持单一 `DATABASE_URL` 同时决定迁移与运行时；靠部署纪律区分 | ❌ **与 `D-OP101-10` 的「禁止」直接冲突**（"不得以部署纪律替代可验证的键分离"） |
| **`BB-S2` 新结构（迁移专用键优先）** | 引入 migration 专用键，并使其在解析链中**优先于** runtime 键；runtime 键**不得**再决定迁移身份 | ✅ 与 `D-OP101-10` 的「决策」一致（`R-02.2` / `R-02.3`） |
| **`BB-S3` CUSTOM** | 由 Human 给出等价结构（须同时满足：键分离可验证 · 身份不可被覆盖 · 缺配置时 fail-closed） | 待裁定 |

**`BB-S2` 需显式处理的四个语义点（仅登记，不在本批实现）**：

```text
1. 解析链顺序：migration 专用键须排在 runtime 键之前（现行顺序须被调整；R-02.3）
2. 缺配置行为：生产环境缺少 migration 专用配置时必须 FAIL-CLOSED（不得静默回退到 runtime DSN）
3. 身份断言：迁移生效连接须做**角色身份断言**（读取生效 URL 的角色部分，断言 ≠ runtime 角色）
4. 回滚面：独立键 · env.py 解析链 · alembic.ini · .env.example · compose · testkit 共 **6 处**（R-02.4）
```

### §2.4 需要另行裁定的范围边界（**本请求不代裁**）

| 编号 | 边界问题 | 为什么必须由 Human 定 |
|---|---|---|
| **`CF-BB-S1`** | **测试基建配置载体是否属 BATCH-B？** Human 本指令 §3 IN 列 = `env.py` / `settings.py` / `alembic.ini` / `.env.example` / compose/deployment config（**5 项**）；而 `D-OP101-10` 的**影响范围**另点名 `tests/integration/alembic_testkit.py` · `tests/conftest.py`。同时 `CF-BA-1 = NEW` 把 **test infrastructure 归 BATCH-C**，BATCH-A 报告 `OI-G-7` 亦称测试期行为属 BATCH-C/D 面 | 两条读法后果不同：<br>**(a) 测试载体属 BATCH-C** ⇒ BATCH-B 只改 5 项；但 testkit/conftest 的 `DATABASE_URL` 默认值会**继续指向 runtime 身份** ⇒ 测试期**无法验证**分离（`RUN-01` 的测试侧证据缺失）<br>**(b) 测试载体属 BATCH-B** ⇒ BATCH-B 扩为 7 项，与 `CF-BA-1` 的批次边界**局部重叠** |
| **`CF-BB-S2`** | **`infrastructure/database/config.py` 与文档类载体如何归类？** `DatabaseConfig.from_settings()`（`config.py:37` 读 `settings.DATABASE_URL`）是 DSN 管道，但位于 `infrastructure/`（Human 的 OUT 含 "runtime code behavior"）；另 `README.md:43` 有 `export DATABASE_URL=…` 示例、`tests/unit/test_config.py` 有 `DATABASE_URL` 环境变量清单断言 | 若归 OUT ⇒ 该文件的读取点在本批**保持原样**（runtime 侧继续读 runtime 键，属**预期**）；若归 IN ⇒ 需同步。文档类（`README.md`）是否需同步亦未定 |

### §2.5 本请求**不授权**的面

```text
除「被授权去修改 §3 中 IN 类的配置对象」这一项以外的任何变更，本请求**均不授权**，
即使被答复为 AUTHORIZED 亦不含：0016/0017 migration 创建 · `alembic upgrade|downgrade` ·
C2 / trigger / 角色 / 授权 / 所有权 的任何变更 · DDL · DML · runtime 实际连接切换 ·
正式库 `uap` 的任何操作 · `tests/**` 的行为断言变更（若 `CF-BB-S1` 未裁）· `commit` · `tag` · `push`。
```

---

## §3 配置对象清单（Config Object Inventory）

### §3.1 分类判定（实测）

| # | 对象 | 现载身份 | 现行取值点（逐字） | 预期动作 | 归类 |
|---|---|---|---|---|---|
| **1** | `migrations_alembic/env.py` | **迁移（判定点）** | `:52` `os.environ.get("DATABASE_URL")`（优先级 2，**覆盖** ini） | 解析链显式化（`R-02.3`） | **IN** |
| **2** | `config/settings.py` | **运行时** | `:57` `DATABASE_URL: str = Field(default="postgresql+psycopg://uap:uap@localhost:5432/uap")` | 运行时身份来源的键位（`CF-BB-3`） | **IN** |
| **3** | `alembic.ini` | **迁移（默认值）** | `:5` `sqlalchemy.url = postgresql+psycopg://uap:uap@localhost:5432/uap`（`:3` 注释描述现行优先级） | 默认值与注释同步 | **IN** |
| **4** | `.env.example` | **模板** | `:14` `DATABASE_URL=`（空值）；**无** migration/runtime 分离键（`C-7`） | 增补分离键（空值语义，`CF-BB-4`） | **IN** |
| **5** | `docker-compose.yml` | **运行时（容器注入）** | `api.environment.DATABASE_URL: postgresql+psycopg://uap:uap@postgres:5432/uap` | 部署注入键位同步 | **IN** |
| **6** | `tests/integration/alembic_testkit.py` | **测试（迁移侧）** | `:21` `BASE_DSN = …//uap:uap@localhost:5432/uap_b1_test` · `:22` `_ADMIN_DSN = …/postgres` | **待裁**（`CF-BB-S1`） | **PENDING** |
| **7** | `tests/conftest.py` | **测试（两侧）** | `:21` `os.environ.setdefault("DATABASE_URL", "…5432/uap_test")` | **待裁**（`CF-BB-S1`） | **PENDING** |
| **8** | `infrastructure/database/config.py` | **运行时（管道）** | `:37` `url=settings.DATABASE_URL`（`from_settings`） | **待裁**（`CF-BB-S2`） | **PENDING** |
| **9** | `README.md` | 文档 | `:43` `export DATABASE_URL=postgresql+psycopg://uap:uap@localhost:5432/uap` | **待裁**（`CF-BB-S2`） | **PENDING** |
| **10** | `tests/unit/test_config.py` | 测试（环境变量清单） | `:21` 环境变量名清单含 `DATABASE_URL`；`:54`/`:70` 校验器用例 | **连带面**（若 2 变更则需同步） | **PENDING** |

### §3.2 关键实测发现（供裁定参考 · **非推荐**）

```text
FD-BB-1  `env.py` 已存在 **`UAP_MIGRATION_*` 前缀族**：
         `:64` `os.environ.get("UAP_MIGRATION_LOCK_MODE", "wait")`
         `:93` `os.environ.get("UAP_MIGRATION_LOCK_TIMEOUT_SECONDS", …)`
         ⇒ 同一文件内已有 `UAP_MIGRATION_` 命名先例（对 `CF-BB-2` 的键名确认是**语境证据**）。

FD-BB-2  `alembic.ini:5` 与 `config/settings.py:57` 的 DSN **完全相同**
         (`postgresql+psycopg://uap:uap@localhost:5432/uap`) ⇒ 默认值层面二者亦无区分。

FD-BB-3  `docker-compose.yml` 仅 postgres 服务声明 `POSTGRES_USER: uap`（**未创建任何新角色**）；
         api 服务注入的 `DATABASE_URL` 与迁移默认值同为 `uap` 超级用户身份。

FD-BB-4  **正式库守卫的连带面**：`tests/integration/test_p10_event_audit_schema.py:618` 与
         `tests/integration/test_ai_gateway_schema.py:883` 以字面 DSN 连 `…5432/uap`（formal-DB 只读守卫）；
         `tests/unit/test_migration_state_probe.py:23` 以字面 DSN 连 `uap_test`。
         ⇒ 任何 DSN 键位改造**不得**改变这三个字面量，否则会破坏既有守卫。

FD-BB-5  本批**不改** `infrastructure/database/config.py` 时，runtime 引擎仍由
         `settings.DATABASE_URL` 构建 ⇒ 与 `D-OP101-10` 的「runtime 键**只**决定 runtime」**相容**。
```

### §3.3 变更面规模（预估 · 仅登记）

```text
若 CF-BB-S1 = (a) 且 CF-BB-S2 = OUT ⇒ 变更对象 = 5 个（#1…#5）
若 CF-BB-S1 = (b) 且 CF-BB-S2 = IN  ⇒ 变更对象 = 10 个（#1…#10）
本请求**不预设**任何一种；实际规模由 §2.4 两项 + §6 四项裁定共同确定。
```

---

## §4 前置条件（Preconditions）

> 每项在开工前必须成立；未成立者标 `❌`，并由**指明的主体**满足。

| 编号 | 前置 | 内容 | 当前状态 |
|---|---|---|---|
| **`BB-P01`** | **baseline verification** | 开工前重跑 §0 六组锚点：`HEAD` / `branch` / `tags` / `remote` / 单头 `0015_p12_indexes` / 活体 `alembic_version` / `0016-0017` ABSENT / 三新角色属性 / 所有权 178 残留 0 / 授权 5 项 / `pg_default_acl` 0 / 正式库 `uap` 0 表 / PDL sha / `0007` sha / C2 md5。**任一 drift ⇒ STOP** | ✅ 本轮已实测：**零 drift** |
| **`BB-P02`** | **DSN separation proof** | 需给出**可验证**的分离证据形式：① 迁移生效 URL 的角色部分 ≠ runtime 角色；② 缺 migration 专用配置时**不得**静默回退到 runtime DSN（FAIL-CLOSED）；③ runtime 键**不再**决定迁移身份（含反向：migration 键**不得**决定 runtime）。证据形态与断言位置须在开工前确定 | ⏳ 待 `CF-BB-1`/`CF-BB-2`/`CF-BB-3` 裁定后确定 |
| **`BB-P03`** | **rollback evidence** | 回滚面须**逐处点名**并对每处给出恢复目标（`R-02.4` 的 **6 处** + 本批实际触点）。回滚后必须满足：**无任何"身份可被覆盖"的残余**；且 `git diff` 只剩预期文件 | ⏳ 待 `CF-BB-S1`/`CF-BB-S2` 确定实际触点后点名 |
| **`BB-P04`** | **secret handling** | ① `.env.example` 新增键必须为**空值**（沿用既有基线）；② 不得把任何真实密钥写入仓库 / 日志 / 报告；③ 报告与日志中的 DSN 一律脱敏（既有 `database_url_without_credentials()` 机制）；④ 新增键的**默认值策略**须明确（有默认值 ⇒ 可能静默回退；无默认值 ⇒ fail-closed，须与 `BB-P02` ② 一致） | ⏳ 待 `CF-BB-4` 裁定 |
| **`BB-P05`** | **validation queries** | 开工后须执行并留档的**只读**校验集（草案 `V-B1…V-B8`）：<br>`V-B1` 迁移生效连接的角色 = 预期迁移身份<br>`V-B2` runtime 连接的角色 = 预期运行时身份<br>`V-B3` 二者 ≠ 且不互为成员<br>`V-B4` 缺 migration 配置 ⇒ FAIL-CLOSED（不得回退）<br>`V-B5` runtime 键变化**不影响**迁移身份<br>`V-B6` migration 键变化**不影响** runtime 身份<br>`V-B7` 正式库守卫三个字面量与 `alembic.ini` 默认值**未被改变**<br>`V-B8` 无新增密钥落地（`.env.example` 新键为空值） | ⏳ 待裁定后冻结 |

---

## §5 风险接受（Risk Acceptance）

> 授权即表示**已知情接受**下列风险及其后果。

| 编号 | 风险 | 后果 | 接受含义 |
|---|---|---|---|
| **`R-02`** | **迁移身份与运行时身份在配置层耦合**（`R-02.1`） | 若不显式化，迁移将跟随 runtime 身份 ⇒ ① 无 DDL ⇒ 迁移失败；或 ② 为让迁移可行而给 runtime 提权 ⇒ **直接违反** `D-P10-13` / `D-OP101-08` | 接受「必须引入独立键 + 显式解析链」，并接受解析链顺序变更带来的行为差异 |
| **`R-02.4`** | **静默失效**：若只改一侧而漏改另一侧，迁移以**错误身份**执行且**可能不报错** | 身份错配在运行期无异常，只在权限被拒时才暴露 | 接受「必须以**断言**防护（`SEC-03` / `V-B5`/`V-B6`）」 |
| **`R-BB-1`** | **回滚残留**：回滚须覆盖 **6 处**，遗漏任一处即留下"身份可被覆盖"的残余 | 回滚后仍存在覆盖路径 ⇒ 分离形同虚设 | 接受「回滚后须逐处复核，且以 `V-B4` 证明无残余」 |
| **`R-BB-2`** | **本地口令为 dev 约定**（角色名=口令，与既有 `uap:uap` 同性质） | 非 dev 环境若直接沿用即高危 | 接受「非 dev 必须替换；不得写入日志」（沿用 `OI-G-4`） |
| **`R-BB-3`** | **测试基建副作用**：本仓库 **19 个测试文件会 `reset_test_database()`**（A 批实测） | 一旦在本批跑全量测试套件，会销毁 BATCH-A 的所有权转移结果 | 接受「本批**不跑**全量套件；只跑定向只读校验」 |
| **`R-BB-4`** | **正式库守卫连带**：`test_p10_event_audit_schema.py:618` / `test_ai_gateway_schema.py:883` / `test_migration_state_probe.py:23` 使用**字面 DSN** | 若被一并改动，会破坏既有 formal-DB 只读守卫 | 接受「三个字面量**保持不改**」（`FD-BB-4`） |
| **`R-05`** | **引导身份的"鸡生蛋"**（角色已由 BATCH-A 建立，本批**不**再动角色） | —— | 本批**不涉及**；登记以证明本批未扩大角色面 |
| **`R-BB-5`** | **运行时行为不变性**：本批不切换实际连接 ⇒ runtime 仍以现行身份运行 | 配置分离**不会**立即生效于运行中的进程（需重启/重新部署才生效） | 接受「本批只建立配置层分离；实际切换属后续批次」 |

---

## §6 Stop Gate

### §6.1 停止规则

```text
任何一步失败 ⇒ STOP
  · 不得继续下一步
  · 不得以"顺手修复"扩大本批范围
  · 不得自动回滚其它已验证内容
  · 不得自行修改任何冻结 Decision / 实施契约
若发现「冻结决策 / 实施契约 / 实际状态」之间的**新冲突** ⇒ HARD STOP + 上报，不得自行消解
```

### §6.2 完成判定（勾选表 · 证据齐备后方可填 `PASS`）

| 判定 | 说明 | 状态 |
|---|---|---|
| `BB-1` 配置分离已落地（IN 面逐项） | 按裁定后的对象清单逐项完成 | ☐ |
| `BB-2` 解析链显式化 | migration 专用键**优先**；runtime 键不再决定迁移身份 | ☐ |
| `BB-3` FAIL-CLOSED 已验证 | 缺 migration 专用配置时**不**回退（`V-B4`） | ☐ |
| `BB-4` 身份双向独立性已验证 | `V-B5` / `V-B6` | ☐ |
| `BB-5` 无密钥落地 | `.env.example` 新键为空值；日志脱敏（`V-B8`） | ☐ |
| `BB-6` 既有守卫未破坏 | `V-B7`（三个字面 DSN + `alembic.ini` 默认值） | ☐ |
| `BB-7` 未越界证明 | `git status` 变更集 ⊆ 裁定后的对象清单；无 migration / 无 DDL / 无角色 / 无 GRANT | ☐ |
| `BB-8` 回滚面已点名并验证 | `R-02.4` 六处 + 实际触点 | ☐ |
| `BB-9` 证据清单 | 逐文件 `bytes` / `sha256` + 校验日志 | ☐ |

### §6.3 暂停点

```text
BB-1…BB-9 全部 PASS ⇒ BATCH-B = PASSED ⇒ **立即停止**
等 Human 的 BATCH-C 授权（C2 / CC-7 rewrite），**不得自动进入下一批**
```

### §6.4 自证缺陷（如实披露）

```text
真实缺口 = **0**（本轮未修改任何配置对象；未创建 migration；未执行 DDL/DML；未动角色/授权/所有权）

harness 实测失败 = **3 项**（首次运行 70/73 ⇒ 修正后 73/73，全部为非内容问题）：
  ① `C14` 断言写成 `**<N> / <N> PASS**`（要求加粗），而本报告该行位于无需加粗的抬头块
     ⇒ 恒假阴。（教训 68 同类：断言不应绑定格式细节）⇒ 改为**加粗无关**的 `\d+ / \d+ PASS`。
  ② `D3` 空白槽位正则字符集 `[A-Z0-9\- ]` **漏 `/`**，而键名 `CF-BB-S2 PIPELINE/DOC SCOPE` 含 `/`
     ⇒ blank=10≠11（**数量断言**，非**集合断言** ⇒ 只能报"少了一个"，无法报"少了哪一个"）
     ⇒ 字符集补 `/()`，并保留"计数 == 11"。**这是 lesson 59 的另一面：数量断言必须配合集合断言**。
  ③ `F3` 用「与上一轮写入的**闲置间隔 ≥ 1h**」作为轮次边界的客观性证明 —— 本轮与上一轮仅相隔
     **0.89 h**（BATCH-A 执行轮刚结束）⇒ 启发式失效（**非内容问题**）。
     ⇒ 改用**更强的自校准判据**：以轮次起始快照的**逐文件 mtime** 为基线，
        「本轮写入」= ∉ 快照 ∪ (mtime > 快照值)；断言 `touched == {两份交付物}`。
        该判据**不需要任何阈值**，且可证伪；F4 同时打印 `gap` 仅作参考信息。

预防性规避 = **4 项**（写 harness 时即按既有教训编码，未在本轮真实触发）：
  ④ 章节号正则 `^## (\d)` 会漏 `§` ⇒ 预先写成 `^## §(\d)`；
  ⑤ 「无 SQL」类断言会被**零计数命名行** / **引用块**击穿（教训 74）⇒ 预先实现
     「按行剥离行内代码跨度（不跨行）+ 去加粗 + 排除 `=\s*0` + 要求行首为动词」；
  ⑥ `os.walk` / 目录枚举的 `./` 前缀未归一（教训 29）⇒ 预先统一剥离；
  ⑦ 「无代码补丁」最初拟断言 `+++`/`---`，而 markdown 表格分隔线 `|---|---|` 含 `---` ⇒ 预先改为
     断言**不存在 `diff`/`python`/`sql` 语言的围栏代码块**（更贴合语义、无假阳）。

本轮未执行任何写入探针（`INSERT`/`DDL`/`DML` 皆 0）⇒ 「只读 + 只写文档」为**字面成立**。
```

---

**END OF OPEN-P10-1 BATCH-B EXECUTION AUTHORIZATION REQUEST（2026-09-27 · REQUEST · 未授权 · 未实施 · `BATCH-B = NOT STARTED`）**
