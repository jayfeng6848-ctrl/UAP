# UAP — OPEN-P10-1 REVISION RESOLUTION RECORD

> ## 状态
>
> ```text
> 轮次                      = OPEN-P10-1 REVISION RESOLUTION（HUMAN DECISION = SUBMITTED）
> 文件性质                  = **RESOLUTION RECORD**（裁定记录 · 非授权 · 非实施 · 非 Decision Carrier）
> Phase 2 生成条件          = 「7 项完整」⇒ **已满足**（本次提交 7 / 7）
> Gate                      = 见 §8
> BATCH-A                   = **NOT STARTED**（Human 明示：本消息**不等于** `BATCH-A START AUTHORIZED`）
> OPEN-P10-1 IMPLEMENTATION = **NOT STARTED**
> ```
>
> **只读 + 只写文档**：未创建 migration · 未创建 role · 无 `GRANT` / `REVOKE` / `ALTER OWNER` · 未改 C2 ·
> 未执行 `alembic upgrade|downgrade` · 无 `DDL` / `DML` · 未 commit / tag / push。
> **未修改**：`PLATFORM_DECISION_LOG.md` · 任何既有 `D-*` 决策 · 任何 migration 文件 · 任何 implementation 文件
> （`OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` / `OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` 均逐字节未变）。
> **未回填** Decision Block 的 `§3 机读回填区`（提交走**消息通道**；理由见 §9.2）。

---

## 1. 原始 Human 输入（**逐字**）

### 1.1 提交形（7 项）

```text
REQ-4-CUSTOM-REVISION = RV-A
REQ-4-CUSTOM-REVISION-TEXT =
OI-B-1 = A
OI-B-2 = A
OI-B-3 = CONFIRM
OI-B-4 = CONFIRM
OI-B-5 = CONFIRM
OI-B-6 = B
```

### 1.2 裁定语义（**逐字**）

```text
1. RV-A:
实际 Alembic revision 使用：
0016_open_p10_1_trust_boundary
原始：
0016_open_p10_1_database_trust_boundary
仅作为历史授权消息中的 canonical identity 记录，不作为 Alembic revision。
2. OI-B-1:
C2 / CC-7 受信 migration identity：
仅：
uap_migrator
不扩展：
uap_seed
3. OI-B-2:
正式数据库：
不纳入本轮迁移。
保持：
uap_b1_test / stage verification flow
不修改：
test_sec4_formal_database_untouched
4. OI-B-3:
owner target:
uap_migrator
5. OI-B-4:
migration 独立键：
UAP_MIGRATION_DATABASE_URL
6. OI-B-5:
确认：
CC-7 纳入 OPEN-P10-1 Implementation
7. OI-B-6:
接受现有语义授权：
OPEN-P10-1 C2 Rewrite Authorization 已通过语义授权。
无需额外逐字行。
```

### 1.3 本消息的边界声明（**逐字**）

```text
注意：
本消息仅完成 Revision Resolution。
不等于：
BATCH-A START AUTHORIZED
等待 BOT 输出：
OPEN-P10-1 REVISION RESOLUTION RECORD
并执行 Gate。
禁止：
migration 创建
role 创建
GRANT
ALTER OWNER
C2 修改
upgrade
commit
tag
push
```

### 1.4 提交通道登记

```text
通道    = **Human 消息**（非 Decision Block `§3` 回填区；该区仍为空白 0 / 7，本轮**未回填**）
被裁定对象 = `OPEN_P10_1_REVISION_ID_HUMAN_DECISION_BLOCK.md` 的 7 个槽位（§2 允许值矩阵定义）
登记   = 追加至该文件 `§9 输入登记（第 2 次 · 已提交）`（**append-only**）
```

---

## 2. 解析结果

### 2.1 逐项解析与合法性校验

| # | 槽位 | 原始值 | 允许值集合（Block §2） | 合法 | 归一后语义 |
|---|---|---|---|---|---|
| 1 | `REQ-4-CUSTOM-REVISION` | `RV-A` | `{RV-A, RV-B, RV-C, CUSTOM}` | ✅ | 实际 revision = `0016_open_p10_1_trust_boundary` |
| 1b | `REQ-4-CUSTOM-REVISION-TEXT` | *（空）* | 仅 `CUSTOM` 时必填 | ✅ 不适用 | 非 `CUSTOM` ⇒ 该槽位不适用，**不得**视为缺项 |
| 2 | `OI-B-1` | `A` | `{A, B}` | ✅ | C2 受信身份 = **仅 `uap_migrator`**（不扩展 `uap_seed`） |
| 3 | `OI-B-2` | `A` | `{A, B}` | ✅ | 正式库 `uap` **排除**出本轮迁移范围 |
| 4 | `OI-B-3` | `CONFIRM` | `{CONFIRM, CUSTOM}` | ✅ | owner target = **`uap_migrator`** |
| 5 | `OI-B-4` | `CONFIRM` | `{CONFIRM, CUSTOM}` | ✅ | migration 独立键 = **`UAP_MIGRATION_DATABASE_URL`** |
| 6 | `OI-B-5` | `CONFIRM` | `{CONFIRM, CUSTOM}` | ✅ | `CC-7` **纳入** `OPEN-P10-1` Implementation ⇒ PREP `OI-2` = 选项 **(a)** |
| 7 | `OI-B-6` | `B` | `{A, B}` | ✅ | **接受现有语义授权** ⇒ 无需补逐字行 |

```text
合法性：**7 / 7 通过**（词表 7/7 · `REQ-4-CUSTOM-REVISION-TEXT` 因非 CUSTOM 而**不适用**，非缺项）
缺失项：**0** · 越界项：**0** · 未识别文本：**0**
```

### 2.2 与既有材料的交叉对照（**只对账，不改写**）

| 本次裁定 | 既有材料中的对应项 | 一致性 |
|---|---|---|
| `REQ-4 = RV-A` ⇒ `0016_open_p10_1_trust_boundary` | `OPEN_P10_1_IMPLEMENTATION_AUTHORIZATION_REQUEST.md:75`：**`REQ-4` 选项 `A` = `0016_open_p10_1_trust_boundary`** | ✅ **完全一致**（即本次 RV-A = 该请求的既有选项 A） |
| `OI-B-5 = CONFIRM`（`OI-2` = 纳入） | 同一请求 `REQ-2` 选项 `A`（纳入 OPEN-P10-1） | ✅ 一致 |
| `OI-B-6 = B`（接受语义授权） | 该请求 §9 要求单独逐字行；Human 2026-09-27 §3.2 明文「允许本轮实施修改 0007 中 C2 触发器函数体」 | ✅ 以 §3.2 明文作为**显式单独确认**（非默示） |
| `OI-B-1 = A`（仅 `uap_migrator`） | `D-OP101-05` / REQ-2 逐字「受信 **migration** identity」 | ✅ 取**字面**读法（未扩宽唯一安全例外） |
| `OI-B-2 = A`（排除 `uap`） | 既有守卫 `test_sec4_formal_database_untouched`（要求 `uap` 保持 0 表） | ✅ 与守卫**相容**（该守卫**无需改动**） |
| `OI-B-3 = CONFIRM`（`uap_migrator`） | `D-OP101-09`（FROZEN）逐字「全量转移至 `uap_migrator`」 | ✅ 一致 |
| `OI-B-4 = CONFIRM`（`UAP_MIGRATION_DATABASE_URL`） | ⚠️ 同一请求 `REQ-6` 选项 `A` = **`MIGRATION_DATABASE_URL`**（**不同串**） | ⚠️ **不一致 —— 见 `CF-R-1`** |
| `REQ-4-CUSTOM-REVISION-TEXT` 空 | — | ✅ 非 `CUSTOM` ⇒ 不适用 |

> **`CF-R-1`（登记 · 不阻断）**：`OI-B-4 = CONFIRM` 绑定的是 **Decision Block `§2` 中列明的值**
> `UAP_MIGRATION_DATABASE_URL`，而**不是**授权请求 `REQ-6` 的选项 `A`（`MIGRATION_DATABASE_URL`）。
> 依 Block §1 `P-5`「通道冲突以 §3 机读块为准」与 §2「允许值」的逐字绑定，**生效值 = `UAP_MIGRATION_DATABASE_URL`**。
> 该差异**只登记、不解释为冲突**，并**提请 Human 在下一轮确认**（若非本意，须显式更正）。

### 2.3 归一化说明（依 Block §1 `P-1`）

```text
`RV-a` / `rv-A` 等大小写变体 ⇒ 归一为 `RV-A`（本次原文即规范形，无变体）
首尾空白已剥离；无全角字符；无未识别文本
```

---

## 3. 验证结果

### 3.1 裁定所指 revision 的形态校验（**目标态** · 未创建）

| 校验项 | 值 | 结果 |
|---|---|---|
| `revision` | `0016_open_p10_1_trust_boundary` | — |
| 长度 | **30** | ✅ ≤ 32（`alembic_version.version_num` = `varchar(32)`） |
| 形状 | `^\d{4}_[a-z0-9_]+$` | ✅ 匹配（`config/build_info.py::REVISION_PATTERN`） |
| 文件名 | `0016_open_p10_1_trust_boundary.py` | ✅ `filename == revision`（stem 30 = revision 30） |
| 文件名冲突 | 仓库内**不存在**同名文件（实测 `No such file or directory`） | ✅ 无冲突 |
| `down_revision`（若创建） | `0015_p12_indexes`（16 → 合规） | ✅ 链式自洽 |
| 与现行最长者对比 | 与 `0011_p09_agent_tool_permission`（30）等长 · 仍 ≤ 32 | ✅ 未突破既有区间上限 |
| 运行期可写性 | 30 ≤ 32 ⇒ 可写入 `alembic_version.version_num` | ✅（对照探针已于 `B-A1` 轮验证 30 字符可插入） |

### 3.2 as-of baseline 复核（**本轮实测**）

| 维度 | 值 | 与 Block/请求锚点 |
|---|---|---|
| `HEAD` | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` | ✅ 一致 |
| tags / remote | 8 / none | ✅ 一致 |
| migration heads | `0015_p12_indexes`（单头） | ✅ 一致 |
| 活体 `alembic_version` | `0015_p12_indexes` | ✅ 一致 |
| `0016` / `0017` | ABSENT / ABSENT | ✅ 一致 |
| PDL sha256 | `a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56` | ✅ 与前两轮同一锚点（`GAP-anchor-1` 所缺者，本轮补齐记录） |
| `0007` sha256 | `9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef` | ✅ 未变 |
| C2 `md5(pg_get_functiondef)` | `6867874166ae36966763c1026ab2af19` | ✅ 未变（`CC7-5` 比对基线） |
| 非 `pg_%` 角色 / 显式 GRANT 到非 owner | 1 / 0 | ✅ 未变 |
| 工作树脏集 | 78 | — |

### 3.3 基线 drift 判定

```text
DRIFT = **0**（已记录锚点全部一致；`GAP-anchor-1`（PDL sha 未列入锚点）**本轮补齐记录**，见 §3.2）
⇒ 无需 HARD STOP；无 drift report
```

---

## 4. 对 `D-OP101-01` … `D-OP101-14` 的影响扫描

> **扫描口径**：对 14 条 **FROZEN** 决策逐条判定「本次裁定是否**要求修改**该决策」。
> 「参数被补齐」≠「决策被修改」：前者是既有决策中**显式留待裁定**的参数被确定；后者需要 supersede。

| 决策 | 主题 | 本次裁定的影响 | 类型 |
|---|---|---|---|
| `D-OP101-01` | 角色拓扑 `RM-D` | 无修改。`uap_seed` 仍在拓扑内（本阶段仅**预置**，不获 C2 权限） | 无 |
| `D-OP101-02` | `R_mig` 必须 `NOSUPERUSER` | 无修改 | 无 |
| `D-OP101-03` | revision 编号归属 | 无修改。该决策冻结的是「`0016` 归属 OPEN-P10-1」与「P13 seed = `0017_p13_seed`」，**从未冻结任何 slug** ⇒ RV-A 是**首次**确定实际 slug，非改写 | 无（**参数补齐**） |
| `D-OP101-04` | 角色创建者 = 环境预置 | 无修改 | 无 |
| `D-OP101-05` | C2 判据形态 `CP-F` | 无修改。**受信身份集合**由 `OI-B-1 = A` 确定为 **仅 `uap_migrator`**（原文「受信 migration identity」的字面实现） | 无（**参数补齐**） |
| `D-OP101-06` | `uap_readonly` = DEFER | 无修改 | 无 |
| `D-OP101-07` | runtime GRANT = 最小集 | 无修改 | 无 |
| `D-OP101-08` | DDL 边界 DB 层强制 | 无修改 | 无 |
| `D-OP101-09` | 既有 156 对象全量转移 | 无修改。**目标 owner = `uap_migrator`** 由 `OI-B-3 = CONFIRM` 再确认 | 无（**参数确认**） |
| `D-OP101-10` | 双身份配置 + 显式解析链 | 无修改。**独立键键名**由 `OI-B-4 = CONFIRM` 确定为 `UAP_MIGRATION_DATABASE_URL` | 无（**参数补齐**） |
| `D-OP101-11` | testkit 角色预置 + 双 DSN | 无修改。**库范围**由 `OI-B-2 = A` 收窄（排除正式库 `uap`） | 无（**参数补齐**） |
| `D-OP101-12` | downgrade = `REVOKE` + 保留角色 | 无修改 | 无 |
| `D-OP101-13` | 「身份隔离已成立」判据 | 无修改。C2 项**纳入本阶段**（`OI-B-5`）⇒ 判据在本阶段**可达** | 无（**可达性恢复**） |
| `D-OP101-14` | 既有守卫 rationale 同步 | 无修改。`OI-B-2 = A` ⇒ `test_sec4_formal_database_untouched` **不需改动**（超出原 rationale 同步范围） | 无 |

```text
影响汇总：
  要求修改的决策 = **0 / 14**
  参数被补齐/确认 = **5**（`D-OP101-03` slug · `D-OP101-05` 受信集合 · `D-OP101-09` owner · `D-OP101-10` 键名 · `D-OP101-11` 库范围）
  可达性恢复     = **1**（`D-OP101-13`）
  ⇒ **PDL 无需任何写入**；supersede 新增 = **0**；本 RECORD **不是** Decision Carrier
```

---

## 5. 对 `OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` 的影响扫描

> **本轮未修改该文件**（逐字节未变）。以下为**待同步项登记**，供下一轮（实施轮或独立同步轮）处置。

| # | 位置 | 现状 | 裁定后应成为 | 处置 |
|---|---|---|---|---|
| `CS-1` | §3.3 `D-OP101-03` Implementation Requirement | 只写「`0016` 归属 `OPEN-P10-1 Database Trust Boundary Foundation`」（**无 slug**） | 补记实际 revision = `0016_open_p10_1_trust_boundary`、`down_revision = 0015_p12_indexes` | **待同步**（本轮未改） |
| `CS-2` | §5.3 `CC-7 Implementation Gate` 状态块（契约 369–375 行） | `CLOSED`；`G-CC7-3` / `G-CC7-5` / `G-CC7-6` = 未满足 | `G-CC7-3` = 已满足（`OI-B-6 = B`）· `G-CC7-5` = 已满足（`md5 6867874166ae36966763c1026ab2af19` 已固化）· `G-CC7-6` = 已满足（`OI-B-5`）；`G-CC7-1`/`G-CC7-2` 仍未满足（实施未开始） | **待同步** |
| `CS-3` | §8 开放项 `OI-1` / `OI-2` / `OI-3` | 「**须 Human 裁定 · 本契约不代裁**」 | `OI-1` **RESOLVED**（REQ-3-CUSTOM 两阶段 bootstrap）· `OI-2` **RESOLVED = (a)** · `OI-3` **RESOLVED**（`UAP_MIGRATION_DATABASE_URL`） | **待同步** |
| `CS-4` | §6.1 `SEQ-0` / §6.2 `RB-3`（`OI-1` 引用） | 「见 `OI-1`」（未定） | 指向已裁定方案（两阶段：Phase A 由受信运维身份完成所有权转移，Phase B 迁移以 `uap_migrator` 执行；`REQ-3-CUSTOM`） | **待同步** |
| `CS-5` | §3.10 `D-OP101-10` 影响范围列表 | 列举 `.env.example` / compose 等（**键名未定**） | 键名 = `UAP_MIGRATION_DATABASE_URL` | **待同步** |
| `CS-6` | 全文 `0016` 引用（§2 总表 · §3.3 · X-4 · §6.1） | 仅写序号 `0016` / `0017` | 补 slug（`0016` → `0016_open_p10_1_trust_boundary`） | **待同步** |
| `CS-7` | §7.3 `IO-2`（`0016_p13_seed` → `0017_p13_seed` 重映射） | 由 **P13 实施契约轮**处理 | **不变**（本次裁定不触及 P13） | 保持 |

```text
本轮修改的 implementation 文件 = **0**
影响面性质 = **纯登记**（7 项待同步，全部留待授权轮处置）
```

---

## 6. 对 `OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` 的影响扫描

> **本轮未修改该文件**（逐字节未变）。

| # | 行 | 现状状态 | 裁定后应成为 | 处置 |
|---|---|---|---|---|
| `MS-1` | `MIG-01` | `PLANNED` | **`PLANNED`（期望值已可填）**：`filename == revision` = `0016_open_p10_1_trust_boundary` · ≤32 · 单 HEAD · `down_revision = 0015_p12_indexes` | **待同步**（期望值确定） |
| `MS-2` | `OI-1` | `OPEN` | **`RESOLVED`**（`REQ-3-CUSTOM` 两阶段 bootstrap） | **待同步** |
| `MS-3` | `OI-2` | `OPEN` | **`RESOLVED = (a)`**（`OI-B-5 = CONFIRM`：`CC-7` 纳入 OPEN-P10-1） | **待同步** |
| `MS-4` | `OI-3` | `OPEN` | **`RESOLVED`**（`OI-B-4 = CONFIRM`：`UAP_MIGRATION_DATABASE_URL`） | **待同步** |
| `MS-5` | `GATE-02`（`CC-7 Gate` 全开） | `BLOCKED` | **仍 `BLOCKED`**，但条件满足数 1/6 → **4/6**（`G-CC7-3`/`4`/`5`/`6` 满足；`G-CC7-1`/`G-CC7-2` 待实施） | **待同步** |
| `MS-6` | `TEST-05` / `GATE-01` | `BLOCKED` | **仍 `BLOCKED`**（实施未开始）；但 `OI-2` 已定 ⇒ `D-OP101-13` 判据在本阶段**可达** | 保持 |
| `MS-7` | `TEST-07`（17 文件 / 34 处同步） | `PLANNED` | 目标 revision 字面量已确定；触发点 `test_p12_indexes.py:24`（**保持 `0015` 不改**）与 `:108`（改为新 head） | 保持 `PLANNED`（实施轮执行） |
| `MS-8` | §8 汇总（`OPEN` = 3 · `BLOCKED` = 9 · `PLANNED` = 21） | 冻结计数 | `OPEN` → **0**；`BLOCKED` → **8**；`PLANNED` → **22**（仅 `OI-1/2/3` 三行转 `RESOLVED` 后的重算） | **待同步** |
| `MS-9` | `MIG-05`（GRANT 每库落地） | `PLANNED` | 库范围收窄 ⇒ 目标库 = `uap_b1_test` + testkit 定义的库；**排除** `uap` | **待同步**（范围注记） |
| `MS-10` | `RUN-01`（DSN 分离断言目标） | `PLANNED` | 断言目标键名 = `UAP_MIGRATION_DATABASE_URL` | **待同步** |

```text
本轮修改的矩阵 = **0**
影响面性质 = **纯登记**（10 项待同步）
```

---

## 7. 派生后果与结项

### 7.1 结项清单

| 项 | 原状态 | 现状态 | 依据 |
|---|---|---|---|
| `B-A1`（revision 标识阻断） | BLOCKED | **RESOLVED** | `REQ-4-CUSTOM-REVISION = RV-A` |
| `OI-1` | OPEN | **RESOLVED** | Human `REQ-3-CUSTOM`（两阶段 ownership bootstrap） |
| `OI-2` | OPEN | **RESOLVED = (a)** | `OI-B-5 = CONFIRM` |
| `OI-3` | OPEN | **RESOLVED** | `OI-B-4 = CONFIRM` |
| `OI-B-1` | PENDING | **RESOLVED**（受信身份 = 仅 `uap_migrator`） | `OI-B-1 = A` |
| `OI-B-2` | PENDING | **RESOLVED**（`uap` 排除） | `OI-B-2 = A` |
| `OI-B-3` | PENDING | **RESOLVED**（owner = `uap_migrator`） | `OI-B-3 = CONFIRM` |
| `OI-B-4` | PENDING | **RESOLVED**（键 = `UAP_MIGRATION_DATABASE_URL`） | `OI-B-4 = CONFIRM` |
| `OI-B-5` | PENDING | **RESOLVED**（`CC-7` 纳入） | `OI-B-5 = CONFIRM` |
| `OI-B-6` | PENDING | **RESOLVED**（语义授权可接受） | `OI-B-6 = B` |
| `GAP-anchor-1` | 未登记锚点 | **CLOSED**（PDL sha 已入本 RECORD §3.2） | 本轮补齐 |

```text
未结项 = **0**（本阶段开放项全部结项）
```

### 7.2 派生后果（**登记 · 非新决策**）

```text
N-R-1  `0016` 实际 revision = `0016_open_p10_1_trust_boundary` · 文件名 = `0016_open_p10_1_trust_boundary.py`
       ⇒ 链长 15 → 16；新单头 = `0016_open_p10_1_trust_boundary`；`down_revision = "0015_p12_indexes"`
N-R-2  39 字符串 `0016_open_p10_1_database_trust_boundary` **永久降级为「历史 canonical identity 标签」**，
       **不得**作为 revision / 文件名 / 键名 / 任何可执行标识使用。
       当前留存位置（**均不改动**）：Human 授权消息 · `OPEN_P10_1_BLOCKER_BA1_FACT_SHEET.md` ·
       `OPEN_P10_1_IMPLEMENTATION_BATCH_A_BLOCKER_REPORT.md` · `OPEN_P10_1_REVISION_ID_RESOLUTION_REQUEST.md`
N-R-3  C2 判据（`CP-F`）的实现形态确定为：
       `current_user = 'uap_migrator' AND session_user = 'uap_migrator'` ⇒ 允许继续；否则按 0007 原版消息**逐字**拒绝
       `uap_seed` **不进入**受信集合（本阶段）
N-R-4  迁移库范围 = `uap_b1_test`（stage verification flow）；正式库 `uap` **排除**；
       既有守卫 `test_sec4_formal_database_untouched` **保持不动**
N-R-5  `CC-7 Implementation Gate` 条件满足数 = **4 / 6**（满足：`G-CC7-3` / `G-CC7-4` / `G-CC7-5` / `G-CC7-6`）；
       未满足：`G-CC7-1`（隔离尚未实施）/ `G-CC7-2`（尚待 `BATCH-A START AUTHORIZED`）
N-R-6  `CF-R-1`：生效键名 = `UAP_MIGRATION_DATABASE_URL`（**≠** 授权请求 `REQ-6` 的选项 A `MIGRATION_DATABASE_URL`）⇒ 提请 Human 确认
```

### 7.3 明确**不**由本 RECORD 产生的事项

```text
× 不产生 implementation 授权（Human 逐字：本消息仅完成 Revision Resolution，
  **不等于** `BATCH-A START AUTHORIZED`）
× 不产生任何 Decision Carrier 写入（PDL 未改；无新 `D-*`）
× 不产生 migration / role / GRANT / ownership / C2 的任何变更
× 不修改任何 implementation 文件（Contract / Matrix 逐字节未变）
× 不解除 `CC-7 Implementation Gate` 的 `G-CC7-1` / `G-CC7-2`
```

---

## 8. Gate

| # | 验证项 | 结果 | 证据 |
|---|---|---|---|
| `G-1` | revision 长度 ≤ 32 | **PASS** | `0016_open_p10_1_trust_boundary` = **30** 字符 |
| `G-2` | `filename == revision` | **PASS** | stem `0016_open_p10_1_trust_boundary` == revision（同串 · 30） |
| `G-3` | revision pattern 合法 | **PASS** | 匹配 `^\d{4}_[a-z0-9_]+$`（`config/build_info.py::REVISION_PATTERN`） |
| `G-4` | 不产生第二套 Decision Carrier | **PASS** | PDL sha256 = `a83fde5c…`（逐字节未变）· 未新增 `D-*` 命名空间 · 无 PDL 写入通道被打开 |
| `G-5` | 不改变冻结决策 | **PASS** | 14 条 `D-OP101-*` 全部逐字未变（影响 = 0 处修改；见 §4） |
| `G-6` | 未越界（无 migration / role / GRANT / ALTER OWNER / C2 / upgrade / commit / tag / push） | **PASS** | 见 §9.1 实测 |
| `G-7` | 7 项裁定合法性 | **PASS** | 7 / 7 落在允许值集合内（§2.1） |
| `G-8` | 基线 drift = 0 | **PASS** | §3.3（`GAP-anchor-1` 本轮补齐） |

```text
Gate = **8 / 8 PASS**  ⇒ `OPEN-P10-1 REVISION RESOLUTION = PASS`
⚠️ 但 `BATCH-A = NOT STARTED` —— 依 Human 逐字边界，`PASS` **不等于** `BATCH-A START AUTHORIZED`
```

---

## 9. 本轮变更面、未越界确认与自证缺陷

### 9.1 未越界（实测）

```text
## 禁止（本轮未做）
migration 创建 · role 创建 · GRANT · REVOKE · ALTER OWNER · C2 修改 · 0007 修改 ·
alembic upgrade|downgrade · DDL · DML · 写入探针 · commit · tag · push ·
PDL 修改 · 既有 Decision 修改 · migration 文件修改 · implementation 文件修改 · 进入 BATCH-A

## 允许（已完成）
docs/architecture/OPEN_P10_1_REVISION_RESOLUTION_RECORD.md（新增 · 本文件）
docs/architecture/OPEN_P10_1_REVISION_ID_HUMAN_DECISION_BLOCK.md（**append-only** §9 输入登记）

实测不变量：HEAD 034ee97c…（未动）· tags 8 · remote none · 0016/0017 = ABSENT ·
           migration heads = 0015_p12_indexes（单头）· 非 pg_% 角色 = 1 · 显式 GRANT 到非 owner = 0 ·
           PDL sha = a83fde5c… · 0007 sha = 9e0105b9… · C2 md5 = 6867874166ae36966763c1026ab2af19
```

### 9.2 关于「未回填 `§3`」的显式披露

```text
Decision Block `§3 机读回填区` 保持**空白 0 / 7**（本轮实测），裁定内容仅记入本 RECORD + 该文件 §9 输入登记。
理由（沿用本项目既有先例 `N-7`，2026-09-27 P13 DECISION FREEZE 轮）：
  ① 回填会使**模板**成为**第二套权威**，与 RECORD 形成双重来源；
  ② 模板 §3 的空白是「提交前状态」的**时点快照**，具有审计价值；
  ③ 既有先例已由 Human 接受（P13 轮的 `DECISION_RESOLUTION.md` 同样保持 `PENDING` 快照未回填）。
若 Human 意在**必须回填**，请显式指示 —— 该动作属**新增授权面**，Bot 不自行执行。
```

### 9.3 自证缺陷（如实披露）

```text
真实缺口 = **0**（未做任何实施动作；未改写任何冻结文本或 implementation 文件）

自证偏差 = **2 项**（均为「登记而非执行」的主动披露）：
  ① `CF-R-1`：`OI-B-4 = CONFIRM` 所绑定的键名（`UAP_MIGRATION_DATABASE_URL`）**不等于**
     授权请求 `REQ-6` 的选项 `A`（`MIGRATION_DATABASE_URL`）。Bot **未静默择一**，
     而是依 Block §2 的逐字绑定取生效值并**显式登记差异**，提请 Human 确认。
  ② `§3` 未回填（见 §9.2）—— 属**有意的选择**，已披露并给出更正途径。

脚本缺陷 = **2 项**（Gate harness v1 → v2 修正，全部非内容问题）：
  ③ 断言 `exactly 2 key lines` 未预期 **§9 自身**（逐字回显提交内容）引入的**第 3 处**同键行 ⇒ 自造假阴。
     修正：按**区域归属**分别断言 —— `§2 图例（decoy）= 1` · `§3 答案槽（空）= 1` · `§9 逐字回显 = 1`。
     （属「断言必须限定语义作用域」一类 · 教训 61 **第 6 次复发**）
  ④ `no affirmative decision-carrier claim` 的否定式词表只含「未」，而正文用的是「**无需**任何写入」
     ⇒ 假阳。修正：弃用该弱断言，改为**可证伪的三条强断言** ——
     `supersede 新增 = **0**` 在位 · 显式否定句「本 RECORD **不是** Decision Carrier」在位 ·
     且全文**无**任何 `supersede 新增 = **<非零>**` 行。

本轮未执行任何写入探针（`INSERT` / `DDL` / `DML` 皆 0）⇒ 「只读 + 只写文档」为**字面成立**。

Gate harness = %TEMP%/op_p10_1_revision_resolution_gate.py → ../uap-stage3-evidence/open_p10_1_revision_resolution_gate.log
             = **73 / 73 PASS**（exit 0）
```

---

## 10. FINAL GATE

```text
OPEN-P10-1 REVISION RESOLUTION = **PASS**

B-A1 = RESOLVED
OI-B-1 … OI-B-6 = RESOLVED（6 / 6）
OI-1 / OI-2 / OI-3 = RESOLVED（3 / 3）
未结项 = 0

revision（目标态，未创建） = 0016_open_p10_1_trust_boundary（30 字符）
filename（目标态，未创建） = 0016_open_p10_1_trust_boundary.py
down_revision            = 0015_p12_indexes
链长                     = 15 → 16 · 新单头 = 0016_open_p10_1_trust_boundary

Gate = 8 / 8 PASS（G-1 长度 · G-2 filename==revision · G-3 pattern · G-4 无第二套载体 ·
                   G-5 冻结决策未变 · G-6 未越界 · G-7 裁定合法 · G-8 drift=0）

BATCH-A = **NOT STARTED**   BATCH-B / C / D = NOT STARTED
OPEN-P10-1 IMPLEMENTATION = **NOT STARTED**

migration 创建 = 0 · role 创建 = 0 · GRANT/REVOKE = 0 · ALTER OWNER = 0 · C2 modification = 0
0007 modification = 0 · alembic upgrade|downgrade = 0 · DDL = 0 · DML = 0
PDL 修改 = 0 · implementation 文件修改 = 0 · commit = 0 · tag = 0 · push = 0
0016 = ABSENT（尚未创建）· 0017 = ABSENT

等待 = Human 的 `BATCH-A IMPLEMENTATION START AUTHORIZED`
⇒ **不得自动进入 BATCH-A**
```

---

**END OF OPEN-P10-1 REVISION RESOLUTION RECORD（2026-09-27 · `REVISION RESOLUTION = PASS` · `BATCH-A = NOT STARTED` · 未越界 · `0016 = ABSENT`）**
