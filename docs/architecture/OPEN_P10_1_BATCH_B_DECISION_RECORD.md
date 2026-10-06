# OPEN-P10-1 BATCH-B · DECISION RECORD

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-B HUMAN DECISION SUBMISSION
> 模式      = DECISION REGISTRATION ONLY · 不实施（无 config / 无 DB / 无 migration / 无 code 变更）
> 文件性质  = **DECISION RECORD**（裁定登记 · 非授权 · 非实施）
> 结论      = `BATCH-B DECISION = REGISTERED` · `BATCH-B = AUTHORIZED TO START`
> as-of     = HEAD 034ee97c… · branch main · tags 8 · remote none · 单头 0015_p12_indexes
>             PDL sha256 a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
>             0007 sha256 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef
>             C2 md5 6867874166ae36966763c1026ab2af19 · 触发器 31|O|0
>             角色 4（含 uap_seed/uap_migrator/uap_app）· 所有权 178 / 残留 0 · uap_app 授权 5 · 正式库 uap 0 表
> Gate      = G-BB-1 PASS · G-BB-2 PASS · G-BB-3 **PASS** · G-BB-4 PASS · G-BB-5 **PASS**
> 自证缺陷  = 真实缺口 **0** · harness 实测失败 **2 类 / 4 项断言** · **文档纪律偏离 1 项**（自检发现并修正）· 预防性规避 **4 项**
> ```
>
> ### 三条不得混淆
>
> ```text
> ① 本 RECORD 记录的是「已提交的裁定」            —— 不是授权文本本身，也不是实施记录。
> ② `BATCH-B = AUTHORIZED TO START`  ≠ 已实施    —— 本批**尚未开工**（见 §12 未越界）。
> ③ Human 明确：提交本身**不授权** BATCH-C / BATCH-D —— 二者仍 `NOT AUTHORIZED`。
> ```

---

## §1 Human 输入（逐字 · 消息通道）

### §1.1 提交通道

```text
通道 = **消息**（对话指令）。**未**回填 `OPEN_P10_1_BATCH_B_HUMAN_DECISION_BLOCK.md`。
Block 文件 = 逐字节未变（sha256 4a2c1e437834678534bd41ad5dd3f4a43ed3b71c1f37f640982aa3cac1f03b7c · 156 行）
Block §3 机读回填区 = **11 槽仍全部为空**（`0 / 7`）—— 保持"时点快照"，避免形成第二套权威
```

### §1.2 裁定原文（逐字）

```text
BATCH-B START AUTHORIZATION = AUTHORIZED
CF-BB-1 = NEW_STRUCTURE
CF-BB-2 = A
CF-BB-3 = A
CF-BB-4 = CUSTOM
CF-BB-S1 = B
CF-BB-S2 = CUSTOM
```

### §1.3 `CF-BB-4-CUSTOM` 原文（逐字）

```text
CF-BB-4-CUSTOM =
`.env.example` 必须同时展示 runtime 与 migration 两条独立配置入口：
DATABASE_URL=
UAP_MIGRATION_DATABASE_URL=
仅提供空值/示例占位，不写入真实凭据。
必须明确说明：
DATABASE_URL = runtime application identity
UAP_MIGRATION_DATABASE_URL = Alembic / migration identity
禁止 migration URL 回退到 DATABASE_URL。
禁止 runtime URL 回退到 UAP_MIGRATION_DATABASE_URL。
本 CUSTOM 不授权真实 secret 写入。
```

### §1.4 `CF-BB-S2-CUSTOM` 原文（逐字）

```text
CF-BB-S2-CUSTOM =
BATCH-B 纳入与"双身份配置链"直接相关的 deployment / pipeline / documentation
同步，但仅限名称、来源、解析链和示例配置的一致性同步。
IN：
- deployment / pipeline 中 migration DSN 的显式来源
- README / deployment documentation 中双 DSN 的说明
- 配置样例中的双身份说明
- CI/CD 中与 migration DSN 注入有关的配置载体
OUT：
- runtime business logic
- runtime authorization logic
- test behavior implementation
- migration creation
- C2 rewrite
- database DDL/DML
- role / grant / ownership mutation
任何超出上述范围的文件必须进入下一批或重新授权。
```

### §1.5 `CF-BB-S1 = B` 边界说明原文（逐字）

```text
CF-BB-S1 = B 的边界说明：
允许把 `alembic_testkit.py` / `conftest.py` 纳入 BATCH-B，
但仅限双 DSN / configuration carrier / fixture injection。
不在 BATCH-B 实现新的业务测试、C2 测试、ownership 测试或其他测试逻辑。
这些继续属于后续验证范围。
```

### §1.6 关键语义冻结原文（逐字）

```text
runtime DSN
= settings.DATABASE_URL
migration DSN
= UAP_MIGRATION_DATABASE_URL
Alembic
= 只使用 UAP_MIGRATION_DATABASE_URL
Runtime
= 只使用 DATABASE_URL
两条解析链必须显式、独立、可验证。
禁止：
DATABASE_URL → migration fallback
UAP_MIGRATION_DATABASE_URL → runtime fallback
GUC / application_name / session flag → trust decision
```

### §1.7 本轮保持原文（逐字）

```text
BATCH-A = PASSED
BATCH-B = AUTHORIZED TO START
BATCH-C = NOT AUTHORIZED
BATCH-D = NOT AUTHORIZED
0016 = ABSENT
0017 = ABSENT
C2 = UNCHANGED
```

---

## §2 解析结果

| 槽位 | 提交值 | 允许矩阵 | 判定 |
|---|---|---|---|
| `BATCH-B START AUTHORIZATION` | **`AUTHORIZED`** | `AUTHORIZED` \| `NOT AUTHORIZED` | ✅ 合法 |
| `CF-BB-1 CONFIG SEPARATION TARGET` | **`NEW_STRUCTURE`** | `KEEP_LEGACY` \| `NEW_STRUCTURE` \| `CUSTOM` | ✅ 合法 |
| `CF-BB-2 MIGRATION URL KEY` | **`A`** | `A` \| `B` \| `CUSTOM` | ✅ 合法 |
| `CF-BB-3 RUNTIME DSN SOURCE` | **`A`** | `A` \| `B` \| `CUSTOM` | ✅ 合法 |
| `CF-BB-4 ENV TEMPLATE POLICY` | **`CUSTOM`** | `A` \| `B` \| `CUSTOM` | ✅ 合法（附文本，见 §1.3） |
| `CF-BB-S1 TEST CONFIG CARRIER SCOPE` | **`B`** | `A` \| `B` \| `CUSTOM` | ✅ 合法（附边界说明，见 §1.5） |
| `CF-BB-S2 PIPELINE/DOC SCOPE` | **`CUSTOM`** | `A` \| `B` \| `C` \| `CUSTOM` | ✅ 合法（附文本，见 §1.4） |

```text
必需 7 槽非空        = **7 / 7** ✅
值属允许矩阵         = **7 / 7** ✅
CUSTOM 附文本        = **2 / 2** ✅（`CF-BB-4-CUSTOM` · `CF-BB-S2-CUSTOM`；`CF-BB-S1 = B` 另附边界说明）
非法值 / 词表外值     = **0**
隐式推断             = **0**（全部取值逐字取自 Human 提交，无任何推断）
```

### §2.1 `CF-BB-0`（上轮登记的拼写口径冲突）= **RESOLVED**

```text
上轮：指令写 `AUTHORISED`（英式），而 Block §2.1 词表为 `AUTHORIZED`（美式），
      且 Block §5 `P-2` 规定词表外文本 ⇒ `UNRECOGNIZED`（按未答复处理）。
本轮：Human 以 **`AUTHORIZED`**（美式 · Block 原词表形态）提交
⇒ 走**路线 (i)**（按原词表提交），**词表未被扩展**
⇒ `CF-BB-0` = **RESOLVED**（无需修改 Block 词表，无需 `P-2` 特例）
```

### §2.2 作用域陷阱复核

> 解析严格锚定 `^## §3` 后取首个围栏块；键**集合**与期望集合相等（`missing = []`）；§2 图例键不计入。
> 本轮另经**双通道交叉核验**：消息通道的 7 项取值 与 Block 内 7 个主槽位的键名逐一对应，无键名歧义。

---

## §3 合法性检查

| 检查 | 结果 | 说明 |
|---|---|---|
| **7 / 7 非空** | ✅ **PASS** | 实测 7 / 7 |
| **值属允许矩阵** | ✅ **PASS** | 7 / 7（含 2 项 `CUSTOM` 均附文本） |
| **无冲突** | ✅ **PASS** | `CF-BB-1 = NEW_STRUCTURE` 与 `D-OP101-10` 的**决策**一致，**未触发**其「禁止」项 ⇒ **supersede 需求 = 0** |
| **无隐式推断** | ✅ **PASS** | 全部取值逐字取自提交 |
| **CUSTOM 文本自洽** | ✅ **PASS** | `CF-BB-4-CUSTOM` 的双键 + 语义标注 + 双向禁回退 + 不授权 secret，与 §1.6 语义冻结**逐条一致** |
| **范围阐述完备** | ✅ **PASS** | `CF-BB-S1` 附边界说明 · `CF-BB-S2-CUSTOM` 显式列 `IN` / `OUT` + 「超出范围须下一批或重新授权」 |

---

## §4 决策语义冻结（由本轮裁定**导出** · 非新决策）

```text
D1  migration DSN 键  = **`UAP_MIGRATION_DATABASE_URL`**（`CF-BB-2 = A`）
D2  runtime DSN 键    = **`settings.DATABASE_URL`**（`CF-BB-3 = A`，键名不变）
D3  Alembic           = **只使用** `UAP_MIGRATION_DATABASE_URL`
D4  Runtime           = **只使用** `DATABASE_URL`
D5  两条解析链         = **显式 · 独立 · 可验证**
D6  禁止方向 ①        = `DATABASE_URL` → migration **fallback**
D7  禁止方向 ②        = `UAP_MIGRATION_DATABASE_URL` → runtime **fallback**
D8  禁止信任来源       = `GUC` / `application_name` / `session flag`（**不得**作为 trust decision）
D9  结构形态          = `NEW_STRUCTURE`（相对 `KEEP_LEGACY` 的新结构；`env.py` 现行解析链须被显式化）
D10 模板策略          = `.env.example` 同时展示 payload 两键，**空值/占位**，附语义说明；**不授权真实 secret 写入**
```

> **`CF-R-1` 收敛**：上轮登记的「`OI-B-4 = CONFIRM` 绑定 `UAP_MIGRATION_DATABASE_URL` 而 `REQ-6` 选项 `A` 为 `MIGRATION_DATABASE_URL`」——
> 本轮 `CF-BB-2 = A` 明确取 **`UAP_MIGRATION_DATABASE_URL`** ⇒ **`CF-R-1` = RESOLVED**（生效键名由此确定）。

---

## §5 Scope Validation

### §5.1 IN —— 由裁定**导出**的变更对象（8 个）

| # | 对象 | 依据 | 类型 |
|---|---|---|---|
| 1 | `migrations_alembic/env.py` | `CF-BB-1 = NEW_STRUCTURE` + `CF-BB-2 = A`（解析链显式化） | 配置（迁移侧） |
| 2 | `alembic.ini` | `CF-BB-2 = A`（默认值与注释同步）—— 见 `OI-BB-2` | 配置（迁移侧） |
| 3 | `.env.example` | `CF-BB-4 = CUSTOM`（**逐字要求**两键 + 语义说明 + 空值） | 模板 |
| 4 | `docker-compose.yml` | `CF-BB-S2-CUSTOM` IN「deployment 中 migration DSN 的显式来源」 | 部署 |
| 5 | `README.md` | `CF-BB-S2-CUSTOM` IN「README / deployment documentation 中双 DSN 的说明」—— 见 `OI-BB-7` | 文档 |
| 6 | `migrations_alembic/README.md` | `CF-BB-S2-CUSTOM` IN（同上）—— 见 `OI-BB-7` | 文档 |
| 7 | `tests/integration/alembic_testkit.py` | `CF-BB-S1 = B`（**仅限**双 DSN / configuration carrier / fixture injection） | 测试基建 |
| 8 | `tests/conftest.py` | `CF-BB-S1 = B`（同上）—— 见 `OI-BB-1` | 测试基建 |

### §5.2 OUT —— 明确不在本批（含理由）

| 对象 | 判定 | 依据 |
|---|---|---|
| `infrastructure/database/config.py` | **OUT** | `CF-BB-S2-CUSTOM` 的 OUT 明列「runtime business logic」；该文件为 runtime DSN 管道，且 `CF-BB-3 = A` 未改 runtime 键 |
| `config/settings.py` | **可能零改动**（见 `OI-BB-4`） | `CF-BB-3 = A` 保持 runtime 键不变；migration 键由 `env.py` 直接读取（既有 `UAP_MIGRATION_LOCK_MODE` 先例） |
| `tests/unit/test_config.py` | **OUT** | 不在 `CF-BB-S1 = B` 的点名集合（仅 `alembic_testkit.py` / `conftest.py`）内；亦非 deployment/documentation ⇒ 见 `OI-BB-3` |
| `tests/unit/test_migration_state_probe.py` | **OUT** | 同上（其 `:23` 为字面 DSN） |
| `tests/integration/test_p10_event_audit_schema.py:618` · `test_ai_gateway_schema.py:883` | **OUT（受保护）** | formal-DB 只读守卫的**字面 DSN 不得改变**（`FD-BB-4`）；改动会破坏既有守卫 |
| `scripts/migrate.py` · `Dockerfile` | **载体存在但无 DSN 注入点**（见 `OI-BB-6`） | 实测两者均**不含**任何 DSN / 环境注入 ⇒ 同步面为空 |
| CI/CD 载体 | **不存在**（见 `OI-BB-5`） | 实测 `.github` / `.gitlab-ci.yml` / `Jenkinsfile` / `.circleci` … **全部缺失** ⇒ `CF-BB-S2-CUSTOM` 的 CI 项为**空集** |
| `docs/architecture/**` | **OUT（属治理轨，非本批配置轨）** | 属 governance 文档，不属 `CF-BB-S2-CUSTOM` 的「deployment / pipeline / documentation」范围 |
| migration 创建 / C2 / 触发器 / 角色 / 授权 / 所有权 / DDL / DML | **OUT** | `CF-BB-S2-CUSTOM` OUT 明列；且分别属 BATCH-C/D |
| runtime business logic / authorization logic / test behavior implementation | **OUT** | `CF-BB-S2-CUSTOM` OUT 明列 |

> **范围纪律**：`CF-BB-S2-CUSTOM` 逐字规定「**任何超出上述范围的文件必须进入下一批或重新授权**」
> ⇒ 本 RECORD 的 IN 清单为**封闭集**；实施期若发现需要触及清单外文件，须**STOP + 重新授权**，不得顺手扩范围。

### §5.3 登记的开放项 `OI-BB-1…8`（**只登记 · 不代裁**）

| 编号 | 事项 | 性质 |
|---|---|---|
| **`OI-BB-1`** | `tests/conftest.py:21` 现为 `os.environ.setdefault("DATABASE_URL", "…5432/uap_test")` —— 这是 **fixture 默认注入**（非 *fallback*）。`CF-BB-S1 = B` 允许 "fixture injection"，而 `CF-BB-4-CUSTOM` 禁的是**回退**语义 ⇒ 实现期须使二者调和（例如在并存两条 fixture 键的同时保持"无回退"语义） | 实施期调和项 |
| **`OI-BB-2`** | `alembic.ini:5` 仍有 dev 硬编码 `sqlalchemy.url`（`uap:uap@localhost:5432/uap`，与 runtime 默认**同串**）及 `:3` 注释（描述**旧**优先级）。在「Alembic **只使用** `UAP_MIGRATION_DATABASE_URL`」之下，须裁定：**移除 / 清空 / 保留为显式 dev 默认**。**Bot 不裁** | 需 Human 口径 |
| **`OI-BB-3`** | `tests/unit/test_config.py`（`SETTING_ENV_KEYS`）与 `tests/unit/test_migration_state_probe.py`（`:23` 字面 DSN）**不在** `CF-BB-S1 = B` 的点名集合内 ⇒ 按范围纪律 = **OUT**；若确需同步，须**下一批或重新授权** | 范围边界 |
| **`OI-BB-4`** | `config/settings.py` 是否需要任何改动：`CF-BB-3 = A` 未改 runtime 键，且 `env.py` 可直接读 `UAP_MIGRATION_DATABASE_URL`（有 `UAP_MIGRATION_LOCK_MODE` 先例）⇒ **可能为零改动**；最终归属由实施契约确定 | 范围边界 |
| **`OI-BB-5`** | **CI/CD 载体实测不存在** ⇒ `CF-BB-S2-CUSTOM` 的「CI/CD 中与 migration DSN 注入有关的配置载体」为**空集**（无可同步对象）。若 Human 期望**新建** CI 载体，属**新增**而非同步，须明示 | 事实 + 需 Human 口径 |
| **`OI-BB-6`** | `Dockerfile` 与 `scripts/migrate.py` 实测**不含任何 DSN / 环境注入点**（`Dockerfile` 刻意只固化 build-time revision artifact；`migrate.py` 无 `environ` 读取）⇒ 属"载体存在但无需改动" | 事实 |
| **`OI-BB-7`** | **文档陈旧陈述与新决策直接矛盾，且属 IN 范围（必须同步）**：① `README.md:43,48` —— 先 `export DATABASE_URL=…` 再 `alembic upgrade head` ⇒ 在新语义下会**以 runtime 身份跑迁移**（正是 `R-02.1` 的**静默失效**陷阱）；② `migrations_alembic/README.md:6` —— 「开发/CI（需要 `DATABASE_URL` 指向目标库；缺省用 alembic.ini 的 dev DSN）」⇒ 与新语义矛盾。二者**不是冲突**（同属本批文档同步面），但**必须**在本批内修正 | **必改项** |
| **`OI-BB-8`** | `CF-R-1` 由 `CF-BB-2 = A` **收敛**：生效 migration 键 = `UAP_MIGRATION_DATABASE_URL` | 收尾登记 |

---

## §6 `D-OP101-10` 影响（`independent migration/runtime keys + explicit resolution chain`）

```text
判定 = **该 FROZEN 决策被本轮裁定完整满足，且未触发其「禁止」项**
```

| `D-OP101-10` 要素 | 本轮裁定 | 一致性 |
|---|---|---|
| 新增独立键承载 migration 身份 | `CF-BB-2 = A` ⇒ `UAP_MIGRATION_DATABASE_URL` | ✅ 满足 |
| 显式化 DSN 解析链 | `CF-BB-1 = NEW_STRUCTURE` + D5「显式 · 独立 · 可验证」 | ✅ 满足 |
| **禁止** ① 保留"runtime 的键决定迁移身份"的倒置 | D3/D4「Alembic 只用 migration 键；Runtime 只用 runtime 键」+ D6 | ✅ **未触发禁止** |
| **禁止** ② 以部署纪律替代**可验证**的键分离 | D5「可验证」+ `BB-P02` 的身份断言要求 | ✅ **未触发禁止** |
| 影响范围（`settings.py` / `alembic.ini` / `.env.example` / compose / testkit / `conftest`） | 与本轮 IN 清单**一致**（+ 2 项文档载体与 `env.py`） | ✅ 相容 |

```text
⇒ **supersede 需求 = 0** · PDL 载体 sha256 `a83fde5c…` **逐字节未变**（本轮未写入任何决策载体）
```

---

## §7 `R-02` 影响

```text
判定 = **本轮裁定正好消除了 `R-02.1` 的耦合**，并使 `R-02.2` / `R-02.3` / `R-02.4` 成为**可执行要求**
```

| `R-02` 子项 | 现状（基线） | 本轮裁定后的要求 |
|---|---|---|
| **`R-02.1`** 风险陈述 | `env.py::_resolve_url()` 优先级 = `attributes` → **`DATABASE_URL` env** → `alembic.ini`；runtime 亦读同一 `DATABASE_URL` ⇒ 两侧身份在配置层**不可区分** | 由 D3/D4/D6/D7 解除：migration 键**独立且优先**，runtime 键不再决定迁移身份 |
| **`R-02.2`** 配置隔离需求 | —— | ✅ 独立键 = `UAP_MIGRATION_DATABASE_URL`；须被 `env.py` 解析链**显式支持**并**优先于** runtime 键；`.env.example` 以**空值**提供（fail-closed） |
| **`R-02.3`** 解析优先级调整需求 | 现行：`attributes` → `DATABASE_URL` → ini | 须改为「**migration 专用键 → attributes → ini**」或等价形态，使迁移身份**不再可能被 runtime 变量覆盖**；并配套**可机读断言**（读取生效 URL 的**角色部分**，断言 ≠ runtime 角色） |
| **`R-02.4`** 回滚风险 | —— | 回滚须同时回退 **6 处**（独立键 · `env.py` 解析链 · `alembic.ini` · `.env.example` · compose · testkit）+ 本批新增的**文档载体**（`README.md` / `migrations_alembic/README.md`）⇒ 实际回滚面 **≥ 8 处**；遗漏任一处即留下"身份可被覆盖"的残余 |

**本轮裁定的增量强化（相对 Block §2.4 的通用表述）**：

```text
Block §2.4 / `R-02.2` ②：缺 migration 专用配置 ⇒ **FAIL-CLOSED**（不得静默回退到 runtime DSN）
CF-BB-4-CUSTOM 逐字：**双向**禁止回退 —— ① `DATABASE_URL` → migration（禁）；② migration 键 → runtime（禁）
⇒ 后者是**更严**的要求（对称禁止），已登记为 D6/D7，实施期须同时满足两向。
```

---

## §8 Contract 影响

```text
状态 = **已扫描 · 本轮未修改**
```

`OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` sha256 `2c1fec371de5ab3b…` —— **逐字节未变**。
**本批需新增/更新的 Contract 内容（登记为待同步项 `CS-B-1…CS-B-4`，**本批不动该文件**）**：

| 编号 | 位置 | 现状 | 应成为 |
|---|---|---|---|
| `CS-B-1` | `§5 R-02.2` | 「键名由实施契约轮确定」 | 键名已定 = `UAP_MIGRATION_DATABASE_URL`（`CF-BB-2 = A`） |
| `CS-B-2` | `§5 R-02.3` | 「须被改为…或等价形态」（未定形态） | 形态已定 = `NEW_STRUCTURE`（`CF-BB-1`）；并须加「双向禁止回退」与「不得以 GUC/application_name/session flag 作信任依据」 |
| `CS-B-3` | `§5 R-02.4` | 「回滚 6 处」 | 回滚面 **≥ 8 处**（+ `README.md` / `migrations_alembic/README.md`） |
| `CS-B-4` | `§3.10` `D-OP101-10` 影响范围 | 列 6 个载体 | 实际 IN = **8 个**（+ `env.py`、2 个文档载体；`settings.py` 见 `OI-BB-4`） |

**承自上轮的 `CS-1…CS-7`** 仍待处置，**本批不动**（属治理轨）。

---

## §9 Matrix 影响

```text
状态 = **已扫描 · 本轮未修改**
```

`OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` sha256 `b1c7e797d0159432…` —— **逐字节未变**。
**本批需新增/更新的 Matrix 内容（登记 `MS-B-1…MS-B-3`，**本批不动该文件**）**：

| 编号 | 项 | 现状 | 应成为 |
|---|---|---|---|
| `MS-B-1` | `RUN-01`（application DSN separation） | 断言目标未定 | 断言目标 = 生效 migration URL 的角色部分 ≠ runtime 角色；双向独立性（`V-B5`/`V-B6`） |
| `MS-B-2` | `SEC-03`（migration identity separation verified） | 未定可证形式 | 双向无回退 + 缺配置 FAIL-CLOSED（`BB-P02` ①②③） |
| `MS-B-3` | `RUN-02`（least privilege verification） | —— | 新增：**不得**以 `GUC` / `application_name` / `session flag` 作为信任判据（`CF-BB-S2-CUSTOM` / §1.6） |

**承自上轮的 `MS-1…MS-10`** 仍待处置，**本批不动**。

---

## §10 Decision Gate

| Gate | 判据 | 结果 | 证据 |
|---|---|---|---|
| **`G-BB-1`** | Revision Resolution = PASS | ✅ **PASS** | `REVISION RESOLUTION RECORD` 行 337 `Gate = 8 / 8 PASS`；`0016_open_p10_1_trust_boundary.py` **不存在**（未创建） |
| **`G-BB-2`** | BATCH-A unchanged | ✅ **PASS** | 角色 **4**（`new_roles = 3`）· 所有权 **178** / 残留 **0** · `uap_app` 直接授权 **5** · 正式库 `uap` **0 表** · C2 md5 `6867874166ae36966763c1026ab2af19` · 触发器 `31|O|0` · PDL/`0007` sha 未变 |
| **`G-BB-3`** | Decision complete（7/7 · 属矩阵 · 无冲突 · 无隐式推断） | ✅ **PASS** | §2 表 7/7 合法；`CF-BB-0` RESOLVED；supersede 需求 0 |
| **`G-BB-4`** | No supersede required | ✅ **PASS** | `CF-BB-1 = NEW_STRUCTURE` 与 `D-OP101-10` 决策一致、未触发其禁止项 ⇒ 需 supersede 的剔除项 = **0**；PDL sha 未变 |
| **`G-BB-5`** | Scope conflicts resolved | ✅ **PASS** | `CF-BB-S1 = B`（附边界说明 · 限定 `alembic_testkit.py` / `conftest.py`）· `CF-BB-S2-CUSTOM`（显式 IN/OUT + 超范围须重新授权）⇒ 变更对象清单**已闭合（8 个）**；无未决范围冲突（`OI-BB-1…8` 均为**实施期调和项 / 已登记事实**，非范围冲突） |

```text
G-BB-1 = PASS · G-BB-2 = PASS · G-BB-3 = PASS · G-BB-4 = PASS · G-BB-5 = PASS
⇒ **BATCH-B DECISION = REGISTERED** · `BATCH-B = AUTHORIZED TO START`
   但 **`BATCH-B IMPLEMENTATION = NOT STARTED`**（本 RECORD 不是实施记录；见 §12）
```

---

## §11 变更面 / 未越界 / 自证缺陷

### §11.1 本轮变更面

```text
新增 = 2 个 .md：本 DECISION RECORD + 对 Block 的 **纯插入** §8 输入登记
修改 = 0（既有内容零改写；Block §1…§7 逐字未改，§3 回填区仍为空白时点快照）
跨轮校验 = 上一轮轮末内容快照 **完整保留** · 前序文件逐字节零变更
```

**Block 的 END 行纪律**（**自检发现并已修正的一处偏离**，见 §11.3 ⑦）：

```text
END 行计数 = **1 → 2**：原 END 行（「空白 0 / 7 · WAITING HUMAN DECISION」）**逐字保留**，
新 END 行（「§3 回填区仍 0 / 7 · §8 输入登记：已提交」）**追加**于其后 —— 符合项目先例
（"追加 1 条新 END 行，旧 END 行不删"）。
```

### §11.2 未越界

```text
## 禁止（本轮未做）
## 实施动作
env.py / settings.py / alembic.ini / .env.example / compose / Dockerfile / README / testkit / conftest **全部未修改**
migration 创建 · alembic upgrade|downgrade · DDL · DML · 写入探针
CREATE/ALTER/DROP ROLE · GRANT · REVOKE · ALTER OWNER · C2 / 触发器改动
PLATFORM_DECISION_LOG.md 写入 · 任何既有 `D-*` 改写 · Contract 修改 · Matrix 修改
BATCH-C · BATCH-D · commit · tag · push

## 允许（已完成）
docs/architecture/OPEN_P10_1_BATCH_B_DECISION_RECORD.md（新增）
docs/architecture/OPEN_P10_1_BATCH_B_HUMAN_DECISION_BLOCK.md（**纯插入** §8 输入登记）
../uap-stage3-evidence/open_p10_1_batch_b_decision_submission_gate.log（Gate 留档）
```

### §11.3 自证缺陷（如实披露）

```text
真实缺口 = **0**（未改任何受保护文件；7 个配置对象 + 全部前序脏条目逐字节未变）

自证缺陷汇总 = { 真实缺口 = **0** ; harness 实测失败 = **2 类 / 4 项断言** ; 文档纪律偏离 = **1 项** ; 预防性规避 = **4 项** }

harness 实测失败 = **2 类 / 4 项断言**（首跑 84/87 → 修正后 86/87 → 再修正后 **87/87**）：
  ① **`C5` 误设前提**：断言假定 Block 含 `§6` / `§7`，而该文件**从来只有** `§1…§5` + 本轮新增的 `§8`
     （`§6`/`§7` 在最初设计里就不存在 —— 答案槽在 `§3`、解析规则在 `§5`）
     ⇒ **2 项假 FAIL**（`§6 missing` / `§7 missing`）。
     修正 = 改为断言**原始标题集** `{1,2,3,4,5}` 逐一在位 + `§8` 为**唯一**新增 + **显式断言 `§6`/`§7` 不存在**
     （即"什么都没丢"，而非"少了两个"）。**教训**：断言"章节未丢失"时，必须**以实际原始标题集为基准**，
     不能凭设计意图假定编号是连续的 —— 这与 lesson 59/81（断言要落在真实集合上）同源。
  ② **`D14` 两处口径错**：断言未**去加粗**（文档写作 `harness 实测失败 = **2 项**`），且要求 `=` 分隔符
     而文档汇总行用 `·` 连接 ⇒ **连续两轮各 1 项 FAIL**。
     修正 = 断言前对文档做 `replace("**","")`，并把汇总行的分隔符统一为 `=`。
     **教训**：凡"文档应包含某计数字样"的断言，一律**先归一格式**（去加粗 / 统一分隔符 / 折叠空白）。

预防性规避 = **4 项**（写 harness 时即按既有教训编码，本轮未真实触发）：
  ③ 快照读取做 **schema 容错**（`dict` ⇒ 取 `sha256`；`str` ⇒ 直接用），避免"轮初嵌套 / 轮末扁平"两形态崩溃（教训 84）；
  ④ 解析严格锚定 `^## §3` 后取首个围栏块 + **键集合断言**，且键名字符集**显式包含 `_`**（`[A-Z0-9\-_ /()]`），
     避免 `UAP_MIGRATION_DATABASE_URL` 被漏判（教训 81 的直接应用）；
  ⑤ `psql` 结果**合并 stderr**（教训 63）；
  ⑥ 「无 SQL / 无 DDL」断言按**行首动词 + 零计数排除 + 行内代码跨度剥离**判定（教训 74），
     避免本报告合法引用的 `CREATE ROLE = 0` 等零计数行被误判。
     同时 **`G3` 直接用内容比对**（`sha16` vs 上一轮轮末快照）而非 mtime 间隔启发式（教训 80），故本轮未失败。

本轮未执行任何写入探针（`INSERT` / `DDL` / `DML` 皆 0）⇒ 「只读 + 只写文档」**字面成立**。

**自检发现的第 3 项偏离（文档纪律 · 非 harness）**：

```text
⑦ **END 行被误替换（已修正）**：首次向 Block 追加 §8 时，我把「提交前的 END 行」当作可替换对象
   —— 即改写为新的 END 行，导致 **旧 END 行被删除**。这违反本项目先例
   （教训 39 ④ / 56 ②：「**追加 1 条新 END 行，旧 END 行不删**」——旧 END 行是 Freeze/提交时点的快照，
   删除它会破坏"时点可追溯"这一审计属性）。
   **发现路径**：交付后自查"本轮对既有文件的改动是否为纯插入"时比对 END 行计数，发现应为 1 → 2 而实际为 1 → 1。
   **修正**：把原 END 行**逐字复原**并置于 §8 之前，新 END 行追加于文末 ⇒ 现行 `END 行 = 2`，
   且 `§1…§7` 的标题行与 `§3` 回填区（0 / 7）**逐字未变**（见 Gate `D4b`/`D4c`）。
   **教训**：**任何"追加到文档末尾"的动作，都要先判定末尾是否存在"不可删的时点快照行"**
   （END 行 / 汇总行 / 计数行）。这与 lesson 40（重生成时截断尾部小节）是同一类风险的两面：
   前者是**多删**、后者是**少留**。
```
```

---

## §12 FINAL GATE

```text
OPEN-P10-1 BATCH-B DECISION = REGISTERED

Phase 0 baseline verification = PASS（drift = 0）
Phase 1 decision parse        = **7 / 7** 合法 · 全属允许矩阵 · 2 项 CUSTOM 均附文本
Phase 2 DECISION RECORD       = **GENERATED**（本轮 · 取代上一轮 REVIEW REPORT 的 NOT GENERATED 结论）
Phase 3 Decision Gate         = G-BB-1 PASS · G-BB-2 PASS · G-BB-3 PASS · G-BB-4 PASS · G-BB-5 PASS
Scope Validation              = IN **8** 个对象 · OUT 逐项含理由 · `OI-BB-1…8` 登记（不代裁）

BATCH-A = PASSED（unchanged）
BATCH-B = **AUTHORIZED TO START**
BATCH-B IMPLEMENTATION = **NOT STARTED**        ← 本 RECORD 不构成实施
BATCH-C = NOT AUTHORIZED · BATCH-D = NOT AUTHORIZED
0016 = ABSENT · 0017 = ABSENT · C2 = UNCHANGED
supersede 需求 = 0 · PDL 未写入

env.py / settings.py / alembic.ini / .env.example / compose / Dockerfile / README / testkit / conftest = 未修改
migration creation = 0 · alembic upgrade|downgrade = 0 · DDL = 0 · DML = 0
CREATE/ALTER/DROP ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER OWNER = 0 · C2 modification = 0
Contract / Decision Log / Matrix = 未修改（sha 逐字节未变）
commit = 0 · tag = 0 · push = 0 · HEAD 034ee97c 未动 · tags 8 · remote none
```

---

**END OF OPEN-P10-1 BATCH-B DECISION RECORD（2026-09-27 · **DECISION REGISTERED** · `BATCH-B = AUTHORIZED TO START` · `BATCH-B IMPLEMENTATION = NOT STARTED` · `BATCH-C/D = NOT AUTHORIZED` · `0016/0017 = ABSENT` · `C2 = UNCHANGED`）**
