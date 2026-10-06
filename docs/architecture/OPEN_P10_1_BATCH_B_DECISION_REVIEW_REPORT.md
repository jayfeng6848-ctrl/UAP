# OPEN-P10-1 BATCH-B HUMAN DECISION SUBMISSION REVIEW · REVIEW REPORT

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-B HUMAN DECISION SUBMISSION REVIEW
> 模式      = DECISION REVIEW ONLY · NO IMPLEMENTATION · NO CONFIG CHANGE · NO DATABASE CHANGE
> 文件性质  = **REVIEW REPORT**（只读审阅记录 · 未提交裁定 · 非决策载体 · 非授权）
> 结论      = `BATCH-B DECISION REVIEW = BLOCKED`
> as-of     = HEAD 034ee97c… · branch main · tags 8 · remote none · 单头 0015_p12_indexes
>             PDL sha256 a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
>             C2 md5 6867874166ae36966763c1026ab2af19 · 触发器 31|O|0 · 0007 sha 9e0105b9…
>             所有权 178 / 残留 0 · `uap_app` 直接授权 5 · 角色 4 · 正式库 uap 0 表
> Gate      = G-BB-1 PASS · G-BB-2 PASS · G-BB-3 **FAIL** · G-BB-4 PASS · G-BB-5 **FAIL**
> 自证缺陷  = 真实缺口 **0** · harness 实测失败 **1 项**（首跑中断，修正后 70/70）· 预防性规避 **5 项**
> ```
>
> ### 关于 Human 指令指定的文件名（**显式登记偏离**）
>
> 指令 Phase 2 要求生成 `OPEN_P10_1_BATCH_B_DECISION_RECORD.md`。该生成是**条件式**的 ——
> 其条件（Phase 1：「**7/7 非空** 且值属允许矩阵 且无冲突 且无隐式推断」）**本轮未满足**（实测 `0 / 7`）。
> 依本项目**既有先例**（`OPEN-P10-1 REVISION RESOLUTION EXECUTION PREP` 轮：0/7 ⇒ 明示 `RECORD **NOT GENERATED**`，
> 改交付 REVIEW REPORT；待裁定真正提交后，下一轮才生成 `<PHASE>_..._RECORD.md`）：
>
> ```text
> OPEN_P10_1_BATCH_B_DECISION_RECORD.md = **NOT GENERATED**（本轮）
> 替代交付 = 本 REVIEW REPORT（记录"未提交"这一事实，而非记录决策）
> 理由 = ① 条件式生成未触发；② 若生成一份名为 "DECISION RECORD" 而**不含任何决策**的文件，
>        会被后续轮次误读为"该批决策已登记"，**构成第二套权威**；③ 指令 Phase 3 的 `G-BB-3`
>        （Decision complete）本就 FAIL，生成 RECORD 将与自身 Gate 结论矛盾。
> 如 Human 明确要求**强制生成**该文件名，请明示 —— 届时将以「NOT SUBMITTED 快照」形态生成并同样标注非决策载体。
> ```

---

## §1 Human 输入（逐字 · 消息通道）

### §1.1 提交通道

```text
通道 = **消息**（对话指令），**未**回填 `OPEN_P10_1_BATCH_B_HUMAN_DECISION_BLOCK.md`
Block 文件 = 逐字节未变（sha256 4a2c1e437834678534bd41ad5dd3f4a43ed3b71c1f37f640982aa3cac1f03b7c · 156 行）
§3 机读回填区 = **11 个槽位右侧全部为空**（`FILLED_COUNT = 0 / 7`）
```

### §1.2 本轮指令中与裁定相关的原文（逐字摘录）

```text
Phase 1:
解析 Human Decision Block。
要求：
仅接受：
BATCH-B START AUTHORIZATION =
AUTHORISED
并且：
CF-BB-1 =
KEEP_LEGACY / NEW_STRUCTURE / CUSTOM
CF-BB-2 =
A / B / CUSTOM
CF-BB-3 =
A / B / CUSTOM
CF-BB-4 =
A / B / CUSTOM
CF-BB-S1 =
A / B / CUSTOM
CF-BB-S2 =
A / B / C / CUSTOM
必须：
- 7/7 非空
- 值属于允许矩阵
- 无冲突
- 无隐式推断
```

### §1.3 输入性质判定（**关键**）

该段是**验收规则声明**（"仅接受 … 允许矩阵"），**不是裁定提交**。判据：

| 判据 | 观察 |
|---|---|
| 结构形态 | 每个键后跟 **候选集合**（`KEEP_LEGACY / NEW_STRUCTURE / CUSTOM`），而非**单一取值** ⇒ 是在声明**允许值域** |
| 与 Block 的对应 | 该值域与 Block §2 的允许值矩阵**逐项一致**（`CF-BB-1` 三值 · `CF-BB-2/3/4` 三值 · `CF-BB-S1` 三值 · `CF-BB-S2` 四值） |
| 文件状态 | Block `§3` **仍为空白**（0/7） |
| 上下文 | 指令以 `要求：` / `必须：` / `若 drift：STOP` 等**规程语气**写就 |

⇒ **本轮未收到任何裁定值**。依禁令「**无隐式推断**」，**不将值域声明推断为选择**。

---

## §2 解析结果

### §2.1 逐槽位

| 槽位 | 提交值 | 状态 |
|---|---|---|
| `BATCH-B START AUTHORIZATION` | *（空）* | `PENDING` |
| `CF-BB-1 CONFIG SEPARATION TARGET` | *（空）* | `PENDING` |
| `CF-BB-2 MIGRATION URL KEY` | *（空）* | `PENDING` |
| `CF-BB-3 RUNTIME DSN SOURCE` | *（空）* | `PENDING` |
| `CF-BB-4 ENV TEMPLATE POLICY` | *（空）* | `PENDING` |
| `CF-BB-S1 TEST CONFIG CARRIER SCOPE` | *（空）* | `PENDING` |
| `CF-BB-S2 PIPELINE/DOC SCOPE` | *（空）* | `PENDING` |
| `CF-BB-1-CUSTOM` … `CF-BB-4-CUSTOM` | *（空）* | 不适用（主槽位非 `CUSTOM`） |

### §2.2 汇总

```text
必需 7 槽非空计数 = **0 / 7**
提交状态          = **NOT SUBMITTED**（`WAITING HUMAN DECISION`）
非法值            = 0（无值可判）
词表外值          = 0（无值可判）
隐式推断          = **0**（未作任何推断；值域声明不被采信为取值）
```

### §2.3 作用域陷阱复核（解析健壮性）

> 同一键族在 Block 内**多处出现**（§2 图例 / §3 回填区），故解析**必须锚定 `^## §3` 后取首个围栏块**，
> 并**按区域归属**断言。本轮实测：区内槽位 **11 个**、键集合与期望集合**相等**（`missing = []`）、
> 区外图例键**未被计入**。若以键文本为锚而吞入 §2 图例（56 行），会因为图例中的 `= KEEP_LEGACY / NEW_STRUCTURE / CUSTOM`
> 被当作"已填内容"而产生**假 `SUBMITTED`** —— 该陷阱本轮已被规避。

---

## §3 合法性检查

| 检查 | 结果 | 说明 |
|---|---|---|
| **7 / 7 非空** | ❌ **FAIL** | 实测 0 / 7 |
| **值属允许矩阵** | ⚪ `NOT EVALUABLE` | 无值可判 |
| **无冲突** | ⚪ `NOT EVALUABLE` | 无值可判；但见 §3.1 的**词表级冲突** |
| **无隐式推断** | ✅ **PASS** | 未从值域声明推断任何选择 |

### §3.1 `CF-BB-0` —— 拼写口径冲突（**登记 · 不阻断 · 须 Human 收敛**）

```text
本轮指令的允许词表写作 **`AUTHORISED`**（英式拼写，-ISED）；
而 Block §2.1 声明的主开关允许词表为 **`AUTHORIZED` / `NOT AUTHORIZED`**（美式拼写，-IZED），
且 Block §5 的解析规则 **`P-2`** 逐字规定：「主开关允许词表：`AUTHORIZED` / `NOT AUTHORIZED`；
其他文本 ⇒ `UNRECOGNIZED`（按未答复处理）」。
```

**处置（Bot 不裁）**：`AUTHORISED` 在 `P-2` 的**严格读法**下 = `UNRECOGNIZED` ⇒ **按未答复处理**。
因此即便 Human 以 `AUTHORISED` 提交，主开关也**不会**被视为有效授权 —— 此点必须在下一轮之前收敛。
两条出路（**均需 Human 明示**）：

| 出路 | 内容 |
|---|---|
| **(i)** | Human 以 Block 词表形态提交：`AUTHORIZED` |
| **(ii)** | Human 明示**扩展**词表以接受 `AUTHORISED`（属**修改验收词表**，非 Bot 可自决） |

> 说明：本项为**词表/拼写层面**的差异，与实体裁定无关；登记它是因为 `P-2` 已把"词表外文本"定义为未答复，
> 若静默归一即等于**擅自放宽**验收门。

### §3.2 其它口径提示（供 Human 填写时参照 · 不构成推荐）

```text
① `CF-BB-1 = KEEP_LEGACY` 与 `D-OP101-10`（FROZEN）的「禁止」项**直接冲突**
   （"不得以部署纪律替代**可验证**的键分离"）⇒ 若 Human 选它，须**同时**明示是否 supersede 该决策，
   否则该取值本身即构成 `CF-BB-1` 处置中的 `BLOCKED`（Block §5 `P-4` 已写死该规则）。
② `CF-BB-2` 的两个候选串**不同**：`A = UAP_MIGRATION_DATABASE_URL` · `B = MIGRATION_DATABASE_URL`
   ⇒ 此槽位是 `CF-R-1`（`OI-B-4 = CONFIRM` 与 `REQ-6` 选项 A 不一致）的**最终收敛点**。
③ `CF-BB-S1/S2` 未裁定 ⇒ 变更对象清单**无法闭合**（5 项 / 7 项 / 10 项三种可能）⇒ BATCH-B 无法开工。
```

---

## §4 `D-OP101-10` 影响

```text
状态 = **NOT EVALUABLE**（无裁定对象）
理由 = `CF-BB-1`（是否保留"单一 `DATABASE_URL` 同时决定两侧身份"的旧结构）未裁定 ⇒
       无法判断该 FROZEN 决策是否被**满足**、被**参数补齐**、还是需要 **supersede**。
```

**已核验的既有事实（只读 · 供裁定参照）**：

| 项 | 现状 |
|---|---|
| `D-OP101-10` 载体 | `PLATFORM_DECISION_LOG.md` sha256 `a83fde5c…` —— **逐字节未变**（本轮未改决策载体） |
| 决策内容 | **independent migration/runtime keys + explicit resolution chain**（`OQ-OP101-10 = ACCEPT OPTION A`） |
| 决策「禁止」 | ① 不得保留"runtime 的键决定迁移身份"的倒置；② 不得以部署纪律替代**可验证**的键分离 |
| 本批与它的关系 | 本批是**执行**该决策的配置面；`CF-BB-1 = KEEP_LEGACY` 将**与该决策冲突**（见 §3.2 ①） |

---

## §5 `R-02` 影响

```text
状态 = **NOT EVALUABLE**（无裁定对象）
理由 = `CF-BB-1` 决定分离结构、`CF-BB-2/3` 决定键位、`CF-BB-S1/S2` 决定变更对象范围 ⇒
       `R-02.2`（配置隔离需求）/ `R-02.3`（解析优先级调整需求）/ `R-02.4`（**回滚须覆盖 6 处**）
       的**实际触点**均无法点名 ⇒ 无法给出实施前置与回滚面。
```

**已核验的既有事实（只读 · 供裁定参照）**：

```text
R-02.1 风险陈述（现状）：`env.py::_resolve_url()` 优先级 = attributes → **`DATABASE_URL` env** → `alembic.ini`；
        runtime 亦读同一 `DATABASE_URL`（`config/settings.py:57`）⇒ 两侧身份在配置层不可区分。
R-02.3 现状链序（逐字）：`env.py:52` `os.environ.get("DATABASE_URL")`（**覆盖** `alembic.ini:5` 硬编码）。
R-02.4 回滚面（6 处 · 待裁定后点名）：独立键 · `env.py` 解析链 · `alembic.ini` · `.env.example` · compose · testkit。
FD-BB-1（既有发现）：`env.py` 已有 `UAP_MIGRATION_*` 前缀族（`:64` / `:93`）—— 键名裁定的**语境证据**，未代裁。
配置对象现状（7 个已核 sha，全部与本轮 Phase 0 记录一致 ⇒ **本批未开工**）：
        env.py 44ae7966c68b6e3c · settings.py 4079edba2376e5dc · alembic.ini 3a6f5ad9105ad027 ·
        .env.example 861d23d85aeb9b98 · docker-compose.yml bd646ec2717b1beb ·
        conftest.py 173f035e38171aab · alembic_testkit.py 66fd8847356045d7
```

---

## §6 Contract 影响

```text
状态 = **NOT EVALUABLE**（无裁定对象）
```

**已核验**：`OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` sha256 `2c1fec371de5ab3b…` —— **本轮未修改**。
**待同步项仍在**（承自上轮 `REVISION RESOLUTION RECORD` 的 `CS-1…CS-7`，**本轮不处置**）：
`§3.3` slug · `§5.3` `CC-7` Gate 状态 · `§8` `OI-1/2/3` 结项 · `§6.1/§6.2` `OI-1` 指向 · `§3.10` 键名 · 全文 `0016` 补 slug · `§7.3` `IO-2` 保持不变。

> 本批若获裁定，将**新增** Contract 待同步项（`R-02.2/2.3` 的落地形态 · `BB-P02` 的断言形态 · `BB-P03` 的回滚触点），
> 但**具体清单依赖裁定值** ⇒ 无法在本轮产出。**本轮未修改该文件**。

---

## §7 Matrix 影响

```text
状态 = **NOT EVALUABLE**（无裁定对象）
```

**已核验**：`OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` sha256 `b1c7e797d0159432…` —— **本轮未修改**。
**待同步项仍在**（承自上轮 `MS-1…MS-10`，**本轮不处置**）：`MIG-01` 期望值 · `OI-1/2/3` 三行状态 · `GATE-02` 条件计数 · `TEST-05`/`GATE-01` 保持 `BLOCKED` · `TEST-07` 触发点 · `§8` 汇总重算 · `MIG-05` 库范围 · `RUN-01` 断言目标。

> 本批的验收项（`RUN-01` 断言目标 · `SEC-03` 身份独立性的可证形式）依赖 `CF-BB-1/2/3` ⇒ 无法在本轮产出。
> **本轮未修改该文件**。

---

## §8 Decision Gate

| Gate | 判据 | 结果 | 证据 |
|---|---|---|---|
| **`G-BB-1`** | Revision Resolution = PASS | ✅ **PASS** | `OPEN_P10_1_REVISION_RESOLUTION_RECORD.md` 行 337 `Gate = **8 / 8 PASS** ⇒ OPEN-P10-1 REVISION RESOLUTION = PASS`；行 404 结论行在位；`0016_open_p10_1_trust_boundary.py` **不存在**（未创建，符合该轮结论） |
| **`G-BB-2`** | BATCH-A unchanged | ✅ **PASS** | 角色 **4**（`uap` + 三新角色）· 所有权总数 **178** / **残留 0** · `uap_app` 直接授权 **5** · 正式库 `uap` **0 表 / 0 授权** · C2 md5 `6867874166ae36966763c1026ab2af19` · 触发器 `31|O|0` · 三新角色属性未变 |
| **`G-BB-3`** | Decision complete（7/7 非空 · 属允许矩阵 · 无冲突 · 无隐式推断） | ❌ **FAIL** | 实测 `0 / 7` ⇒ `NOT SUBMITTED`（§2） |
| **`G-BB-4`** | No supersede required | ✅ **PASS** | 无任何取值提交 ⇒ **无取值与冻结决策冲突** ⇒ 无需 supersede；`D-OP101-10` 载体 sha 逐字节未变（顺带登记：**若**未来选 `KEEP_LEGACY`，则该项将**需要** supersede 处置） |
| **`G-BB-5`** | Scope conflicts resolved | ❌ **FAIL** | `CF-BB-S1`（测试载体归属）与 `CF-BB-S2`（DSN 管道/文档归属）**均未裁定** ⇒ 变更对象清单无法闭合（5 / 7 / 10 三种可能） |

```text
G-BB-1 = PASS · G-BB-2 = PASS · G-BB-3 = **FAIL** · G-BB-4 = PASS · G-BB-5 = **FAIL**
⇒ **BATCH-B DECISION REVIEW = BLOCKED**
```

---

## §9 变更面 / 未越界 / 自证缺陷

### §9.1 本轮变更面

```text
新增 = 1 个 .md（本 REVIEW REPORT）
修改 = 0（`_DECISION_RECORD.md` **未生成** —— 见抬头"关于文件名"节）
跨轮校验 = 上一轮轮末内容快照 84 条 **完整保留** · `files changed since prev round-end = []`（逐字节零变更）
脏集 = 84 → 85
```

### §9.2 未越界

```text
## 禁止（本轮未做）
Contract 修改 · Decision Log 修改 · Implementation Matrix 修改 · 配置对象修改
（env.py / settings.py / alembic.ini / .env.example / compose / testkit / conftest 全 0）
migration 创建 · alembic upgrade|downgrade · DDL · DML · 写入探针
CREATE/ALTER/DROP ROLE · GRANT · REVOKE · ALTER OWNER · C2 / 触发器改动
BATCH-B 实施 · BATCH-C/D · commit · tag · push

## 允许（已完成）
docs/architecture/OPEN_P10_1_BATCH_B_DECISION_REVIEW_REPORT.md（新增 · 本文件）
../uap-stage3-evidence/open_p10_1_batch_b_decision_review_gate.log（Gate 留档）
```

### §9.3 自证缺陷（如实披露）

```text
真实缺口 = **0**（未改任何受保护文件；`D7`/`G4` 已逐字节断言 7 个配置对象 + 84 个前序脏条目零变更）

harness 实测失败 = **1 项**（首跑在第 20 项即中断，**未产出任何结论** ⇒ 修正后 70 / 70 PASS）：
  ① `D3`（及 `G4`）读取**上一轮的轮末快照**时按**嵌套** schema 解析（`{path: {sha256, mtime}}`），
     而该快照实际由上一轮 harness 写成**扁平**形态（`{path: "<sha16>"}`）⇒
     `AttributeError: 'str' object has no attribute 'get'`，脚本在 A/B/C 组全 PASS 后崩溃。
     **根因 = 同一项目内快照存在两种 schema，而读取方未做容错**。
     修正 = 引入 **schema 容错归一读取器** `load_norm()`（`dict` ⇒ 取 `sha256`；`str` ⇒ 直接用），
     使**轮初嵌套**与**轮末扁平**两形态均可读；并把它提升到脚本顶部，避免"定义晚于使用"的顺序陷阱。
     **教训**：跨轮传递的副产物（快照 / 账本 / 指纹）必须**显式声明 schema**，否则下一轮必然踩坑；
     本次已在轮末快照中保持扁平形态并加注说明。

预防性规避 = **5 项**（写 harness 时即按既有教训编码，本轮未真实触发）：
  ① **作用域锚定**：`filled` 计数严格锚定 `^## §3` 后取首个围栏块 —— 否则 §2 的**允许值图例**
     （`= KEEP_LEGACY / NEW_STRUCTURE / CUSTOM`）会被计为"已填"而产出**假 `SUBMITTED`**（教训 61 同类）；
  ② **键「集合」断言**（`set(seen) == set(EXPECTED)`）而非仅数量 —— 使位数 / 字符集 / 前缀错误**立即定位**（教训 81）；
  ③ **键行区域归属**断言（§2 图例 = decoy / §3 = 槽位，各 1 行），避免同键多表重复计（教训 61）；
  ④ `psql` 结果**合并 stderr**（教训 63），避免阻断证据假阴；
  ⑤ **行首 DDL 动词 + 零计数/否定式排除**判定（教训 74），避免"命名而未执行"行被误判为可执行 DDL。

本轮未执行任何写入探针（`INSERT` / `DDL` / `DML` 皆 0）⇒ 「只读 + 只写文档」**字面成立**。
```

---

## §10 FINAL GATE

```text
OPEN-P10-1 BATCH-B DECISION REVIEW = BLOCKED

Phase 0 baseline re-verification = PASS（drift = 0 · 未触发 STOP）
Phase 1 parse                   = 0 / 7 · **NOT SUBMITTED**
Phase 2 DECISION RECORD         = **NOT GENERATED**（条件式未触发 · 改交付本 REVIEW REPORT）
Phase 3 Decision Gate           = G-BB-1 PASS · G-BB-2 PASS · G-BB-3 FAIL · G-BB-4 PASS · G-BB-5 FAIL

BATCH-B IMPLEMENTATION = **NOT STARTED**      ← 保持
BATCH-A = PASSED（unchanged）· BATCH-C / BATCH-D = NOT AUTHORIZED
OPEN-P10-1 IMPLEMENTATION = IN PROGRESS（BATCH-A 已完成）
REVISION RESOLUTION = PASS（`G-BB-1` 依据，保持）

env.py / settings.py / alembic.ini / .env.example / compose / testkit / conftest = 未修改
migration creation = 0 · alembic upgrade|downgrade = 0 · DDL = 0 · DML = 0
CREATE/ALTER/DROP ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER OWNER = 0 · C2 modification = 0
Contract / Decision Log / Matrix = 未修改（sha 逐字节未变）
commit = 0 · tag = 0 · push = 0 · HEAD 034ee97c 未动 · tags 8 · remote none · 脏集 84 → 85
```

---

**END OF OPEN-P10-1 BATCH-B HUMAN DECISION SUBMISSION REVIEW · REVIEW REPORT（2026-09-27 · **REVIEW ONLY** · `NOT SUBMITTED` · `DECISION RECORD = NOT GENERATED` · `BATCH-B DECISION REVIEW = BLOCKED` · `BATCH-B IMPLEMENTATION = NOT STARTED`）**
