# OPEN-P10-1 BATCH-B · HUMAN DECISION BLOCK

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 用途      = 供 Human 一次性回答 BATCH-B（migration/runtime 配置分离）的开工授权与 4 项关键口径
> 文件性质  = **DECISION BLOCK**（空白 · 未预填 · 未提交）
> 当前      = 空白 0 / 7 · `BATCH-B = NOT STARTED` · `OPEN-P10-1 IMPLEMENTATION = IN PROGRESS（BATCH-A 已完成）`
> 配套      = OPEN_P10_1_BATCH_B_EXECUTION_AUTHORIZATION_REQUEST.md（依据与范围）
> 原则      = **不得预填** · **不得推断** · **不补默认值** · 留空 = 未答复 = 不得开工
> ```

---

## §1 用途与三条提示

1. **本 Block 是唯一答复通道**。Request §2.3 给出结构候选名字，**不代表任何选择**。
2. **7 个槽位缺任一 ⇒ 不得开工**（`CF-BB-1…4` 决定"改什么"，`CF-BB-S1/S2` 决定"改哪些文件"，`START AUTHORIZATION` 是总开关）。
3. **不得因本 Block 的答复而提前执行 BATCH-C / BATCH-D**（C2 改写 / 迁移创建 / 终验仍须各自独立授权）。

---

## §2 允许值

### §2.1 主开关

```text
BATCH-B START AUTHORIZATION =
    AUTHORIZED            ⇒ 允许按 §2.1 裁定范围开工
    NOT AUTHORIZED        ⇒ 不开工（本批保持 NOT STARTED）
    （留空）               ⇒ 未答复 ⇒ 不开工
```

### §2.2 `CF-BB-1` CONFIG SEPARATION TARGET

| 值 | 含义 | 与 `D-OP101-10` 的关系 |
|---|---|---|
| `KEEP_LEGACY` | 保持旧结构（单一 `DATABASE_URL` 同时决定迁移与运行时） | ❌ 与该 FROZEN 决策的「禁止」项**直接冲突**（不得以部署纪律替代可验证的键分离） |
| `NEW_STRUCTURE` | 新结构：引入 migration 专用键，使其在解析链中**优先于** runtime 键 | ✅ 与该 FROZEN 决策的「决策」一致（`R-02.2` / `R-02.3`） |
| `CUSTOM` | Human 给出等价结构（须同时满足：可验证键分离 · 身份不可被覆盖 · 缺配置 fail-closed） | 待裁 |

```text
CF-BB-1 CONFIG SEPARATION TARGET =
CF-BB-1-CUSTOM（仅当为 CUSTOM 时填写，自由文本） =
```

### §2.3 `CF-BB-2` MIGRATION URL KEY

```text
A = UAP_MIGRATION_DATABASE_URL      ← 沿用 env.py 既有 `UAP_MIGRATION_*` 前缀族（见 Request FD-BB-1）
B = MIGRATION_DATABASE_URL          ← 更早授权请求 `REQ-6` 的选项 A
C = CUSTOM（自由文本）
CF-BB-2 MIGRATION URL KEY =
CF-BB-2-CUSTOM（仅当为 CUSTOM 时填写） =
```

> **`CF-R-1` 的收敛点**：`OI-B-4 = CONFIRM` 绑定 `UAP_MIGRATION_DATABASE_URL`，而 `REQ-6` 选项 `A` 是 `MIGRATION_DATABASE_URL`（**不同串**）。本槽位为**最终确认点**；两串之间**不静默择一**。

### §2.4 `CF-BB-3` RUNTIME DSN SOURCE

```text
A = settings.DATABASE_URL（保持现状：runtime 继续读 `DATABASE_URL`，键名不变）
B = settings 中的**另一个**专用键（runtime 亦改名，与 migration 键对称）
C = CUSTOM（自由文本）
CF-BB-3 RUNTIME DSN SOURCE =
CF-BB-3-CUSTOM（仅当为 CUSTOM 时填写） =
```

> 提示：选项 `A` 与 `D-OP101-10` **相容**（runtime 键**只**决定 runtime；本批**不**切换实际连接）。
> 选项 `B` 会**扩大**变更面（额外连带 `settings.py` 校验器 · `compose` · `conftest` · `testkit` · `infrastructure/database/config.py`）。

### §2.5 `CF-BB-4` ENV TEMPLATE POLICY

```text
A = 新增 migration 专用键为**空值**（沿用 .env.example 既有"全部空值"基线）；既有 `DATABASE_URL=` 行保持
B = 新增键为**空值**，且同时调整既有 `DATABASE_URL=` 的注释以说明两侧身份
C = CUSTOM（自由文本）
CF-BB-4 ENV TEMPLATE POLICY =
CF-BB-4-CUSTOM（仅当为 CUSTOM 时填写） =
```

### §2.6 `CF-BB-S1` 测试基建配置载体归属

| 值 | 含义 | 后果 |
|---|---|---|
| `A` | 测试基建配置载体（`tests/integration/alembic_testkit.py` · `tests/conftest.py`）**排除**出 BATCH-B（归 BATCH-C） | BATCH-B 只改 5 个对象；但测试侧 `DATABASE_URL` 默认值继续指向 runtime 身份 ⇒ **测试期的分离证据缺失** |
| `B` | **纳入** BATCH-B | BATCH-B 扩为 7 个对象，与 `CF-BA-1` 的批次边界**局部重叠**（test infrastructure 名义上归 BATCH-C） |
| `C` | `CUSTOM` | 由 Human 逐文件指定 |

```text
CF-BB-S1 TEST CONFIG CARRIER SCOPE =   （A / B / CUSTOM）
```

### §2.7 `CF-BB-S2` DSN 管道与非配置文件归属

| 值 | 含义 | 后果 |
|---|---|---|
| `A` | `infrastructure/database/config.py` 与 `README.md` / `tests/unit/test_config.py` 均**排除** | runtime 读取点保持原样（属预期）；文档与单测清单不同步 |
| `B` | `infrastructure/database/config.py` **纳入**；文档类（`README.md`）**排除** | 需同步 DSN 管道读取点 |
| `C` | 全部**纳入**（含 `README.md` 示例与 `tests/unit/test_config.py` 清单） | 变更面最大 |
| `D` | `CUSTOM` | 由 Human 逐文件指定 |

```text
CF-BB-S2 PIPELINE/DOC SCOPE =   （A / B / C / CUSTOM）
```

---

## §3 机读回填区（**全部空白 · 请逐行填写**）

```text
BATCH-B START AUTHORIZATION =
CF-BB-1 CONFIG SEPARATION TARGET =
CF-BB-1-CUSTOM =
CF-BB-2 MIGRATION URL KEY =
CF-BB-2-CUSTOM =
CF-BB-3 RUNTIME DSN SOURCE =
CF-BB-3-CUSTOM =
CF-BB-4 ENV TEMPLATE POLICY =
CF-BB-4-CUSTOM =
CF-BB-S1 TEST CONFIG CARRIER SCOPE =
CF-BB-S2 PIPELINE/DOC SCOPE =
```

> 说明：上列 11 行中，`-CUSTOM` 行**仅当**对应主槽位取 `CUSTOM` 时需要填写；其余情况可留空。
> **可开工的最小集合** = `BATCH-B START AUTHORIZATION` + `CF-BB-1` + `CF-BB-2` + `CF-BB-3` + `CF-BB-4` + `CF-BB-S1` + `CF-BB-S2`（**7 项**）且主开关为 `AUTHORIZED`。

---

## §4 反向保证（可断言）

```text
RB-1  机读回填区**无任何预填**：11 行右侧全部为空
RB-2  本文件不含任何 `**已选**` 形式的候选预选标记
RB-3  本文件不含实施步骤、SQL、代码补丁或 diff
RB-4  Request §2.3 的 `BB-S1`/`BB-S2`/`BB-S3` 仅为**结构描述**，不构成选择
RB-5  本文件未替 Human 裁定 `CF-BB-S1`/`CF-BB-S2` 的任一读法
```

---

## §5 解析规则（下一轮直接适用 · 无需再发明口径）

| 规则 | 内容 |
|---|---|
| **`P-1`** | 归一：`strip` + 大写化比较主开关值；`CUSTOM` 文本**保留原文**不改写 |
| **`P-2`** | 主开关允许词表：`AUTHORIZED` / `NOT AUTHORIZED`；其他文本 ⇒ `UNRECOGNIZED`（按未答复处理） |
| **`P-3`** | `CF-BB-1` ∈ {`KEEP_LEGACY`,`NEW_STRUCTURE`,`CUSTOM`}；`CF-BB-2` ∈ {`A`,`B`,`CUSTOM`}；`CF-BB-3` ∈ {`A`,`B`,`CUSTOM`}；`CF-BB-4` ∈ {`A`,`B`,`CUSTOM`}；`CF-BB-S1` ∈ {`A`,`B`,`CUSTOM`}；`CF-BB-S2` ∈ {`A`,`B`,`C`,`CUSTOM`} |
| **`P-4`** | `CF-BB-1 = KEEP_LEGACY` 与 `D-OP101-10`（FROZEN）**冲突** ⇒ 若 Human 选择该项，须**同时**明示是否 supersede 该决策；否则登记为 `BLOCKED` |
| **`P-5`** | 任一槽位为 `CUSTOM` 但**未附文本** ⇒ 视为**未填写**（不计入 7 项） |
| **`P-6`** | 留空 ⇒ `PENDING`（**不等于** `KEEP` / 不等于接受任何候选） |
| **`P-7`** | 若 Human 以**消息**通道提交（不回填本文件）⇒ 本文件**保持空白时点快照**，由下一轮的 RECORD 登记；`§3` 是否回填由 Human 明确指示 |

---

**END OF OPEN-P10-1 BATCH-B · HUMAN DECISION BLOCK（2026-09-27 · 空白 0 / 7 · `WAITING HUMAN DECISION` · `BATCH-B = NOT STARTED`）**

> 上行为**决策提交前**的时点快照 END 行（**保留不删** · 逐字未改）；以下为提交后的输入登记与**现行** END 行。END 行计数 1 → 2。

---

## §8 输入登记（第 1 次 · **已提交**）

> **纯插入节**：§1…§7 逐字未改；§3 机读回填区**仍为空白**（见 §8.2 的通道说明）。

### §8.1 提交（逐字 · 消息通道）

```text
BATCH-B START AUTHORIZATION = AUTHORIZED
CF-BB-1 = NEW_STRUCTURE
CF-BB-2 = A
CF-BB-3 = A
CF-BB-4 = CUSTOM
CF-BB-S1 = B
CF-BB-S2 = CUSTOM

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

CF-BB-S1 = B 的边界说明：
允许把 `alembic_testkit.py` / `conftest.py` 纳入 BATCH-B，
但仅限双 DSN / configuration carrier / fixture injection。
不在 BATCH-B 实现新的业务测试、C2 测试、ownership 测试或其他测试逻辑。
这些继续属于后续验证范围。
```

### §8.2 通道说明（**重要**）

```text
提交走**消息通道**，本文件 §3 机读回填区**保持空白**（`0 / 7` 形态）。
理由（沿用本项目先例）：§3 的空白形态本身是**时点快照**，具有审计价值；
回填会让同一文件同时承载"模板"与"答复"两重身份 ⇒ 易被误读为**第二套权威**。
⇒ "已被回应"这一事实由本 §8 与 `OPEN_P10_1_BATCH_B_DECISION_RECORD.md` 声明。
⇒ 若 Human 要求回填 §3，请**显式指示**（属新增授权面）。
```

### §8.3 解析结果

```text
7 / 7 非空 ✅ · 7 / 7 属允许矩阵 ✅ · CUSTOM 附文本 2 / 2 ✅ · 非法值 0 · 隐式推断 0
CF-BB-0（拼写口径冲突）= **RESOLVED**（Human 以 Block 原词表 `AUTHORIZED` 提交，未扩表）
判别结论：
  CF-BB-2 = A ⇒ migration 键 = `UAP_MIGRATION_DATABASE_URL`（`CF-R-1` 收敛）
  CF-BB-3 = A ⇒ runtime 键 = `settings.DATABASE_URL`（不变）
Gate = `G-BB-1…G-BB-5` 全 **PASS** ⇒ `BATCH-B DECISION = REGISTERED`
```

### §8.4 状态（本 BENCH 时点）

```text
BATCH-B = **AUTHORIZED TO START** · BATCH-B IMPLEMENTATION = **NOT STARTED**（不得自动开工）
BATCH-A = PASSED · BATCH-C / BATCH-D = NOT AUTHORIZED
0016 = ABSENT · 0017 = ABSENT · C2 = UNCHANGED · supersede 需求 = 0
本文件 §1…§7 逐字未改；§3 回填区仍空白
```

---

**END OF OPEN-P10-1 BATCH-B · HUMAN DECISION BLOCK（2026-09-27 · §3 回填区 0 / 7 · **§8 输入登记：已提交（消息通道）** · `BATCH-B = AUTHORIZED TO START` · `BATCH-B IMPLEMENTATION = NOT STARTED`）**
