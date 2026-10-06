# OPEN-P10-1 BATCH-C · HUMAN DECISION BLOCK

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 用途      = 供 Human 一次性回答 BATCH-C（Trust Boundary / 0016 + CC-7）的开工授权与 10 项关键口径
> 文件性质  = **DECISION BLOCK**（空白 · 未预填 · 未提交）
> 当前      = 空白 0 / 8（必需）+ 3 项补充冲突 · `BATCH-C = NOT STARTED` · `BATCH-D = NOT AUTHORIZED`
> 配套      = OPEN_P10_1_BATCH_C_EXECUTION_AUTHORIZATION_REQUEST.md（依据 / 影响面 / 候选 / 验证矩阵 / 风险）
> 原则      = **不得预填** · **不得推断** · **不补默认值** · 留空 = 未答复 = 不得开工
> ```

---

## §1 用途与三条提示

1. 本 Block 是唯一答复通道；Request §3 的候选结构（`CC-C-S1/S2/S3`）**不代表任何选择**。
2. **8 个必需槽位缺任一 ⇒ 不得开工**；3 项补充冲突（`CF-C-5/6/7`）为本轮发现的**新增**冲突，一并裁定以免多一轮往返。
3. 本 Block 的答复**不授权** BATCH-D；`CC-7` 改写仍受 `CC7-1…6` 六条件约束。

---

## §2 允许值

### §2.1 主开关

```text
BATCH-C START AUTHORIZATION =   AUTHORIZED / NOT AUTHORIZED /（留空 = 未答复）
```

### §2.2 四项指定冲突

| 槽位 | 问题 | 允许值 |
|---|---|---|
| **`CF-C-1`** | Trust Boundary 需要的 **schema CREATE 授权**（FD-C-1 实测：替换自有函数也需要 CREATE ⇒ 必要前置）与 BATCH-A 冻结的「uap_app grants = 5」是否冲突？ | `A` = **无冲突**（授权对象是 uap_migrator，不触碰 uap_app 的 5 项边界）+ 授权予以批准 · `B` = **有冲突**（说明理由）· `CUSTOM` |
| **`CF-C-2`** | 授予 CREATE 后，`uap_migrator` 的执行能力是否足以完成 0016（CC-7 改写）？与其 `NOSUPERUSER` 等限制是否冲突？ | `A` = **足够**（CREATE + 既有 ownership + USAGE 即覆盖 0016 全部 DDL；NOSUPERUSER 无需放宽）· `B` = 需要额外特权（附明细）· `CUSTOM` |
| **`CF-C-3`** | ownership transition 与「ownership residual = 0」是否冲突？ | `A` = **无冲突**（0016 改写不改变 owner；178/178 已终态）· `B` = 需要额外 transition（附明细）· `CUSTOM` |
| **`CF-C-4`** | integration test 执行 vs `reset_test_database()`（19 文件）会摧毁 BATCH-A ownership —— 如何解决？ | `A` = testkit 在 reset 后**重放 ownership**（幂等重应用步骤，入 BATCH-C 测试基建）· `B` = 测试改用**独立数据库**（不 reset `uap_b1_test`）· `C` = integration 测试**延后至 BATCH-D** · `CUSTOM` |

```text
CF-C-1 =
CF-C-2 =
CF-C-3 =
CF-C-4 =
```

### §2.3 三项补充冲突（本轮发现 · 一并裁定）

| 槽位 | 问题 | 允许值 |
|---|---|---|
| **`CF-C-5`** | **授权持久性**：`GRANT CREATE ON SCHEMA public TO uap_migrator` 是持久保留，还是迁移窗口期授权 + downgrade 回收（对齐 `D-OP101-12`）？ | `A` = **持久保留**（后续迁移仍需要）· `B` = **窗口期**（BATCH-C downgrade 内 REVOKE）· `C` = 保留至 BATCH-D 终验后再裁定 · `CUSTOM` |
| **`CF-C-6`** | **0016 内容边界**：0016 是否仅含 CC-7 改写（Trust Boundary 的其余部分已由 A/B 完成）？ | `A` = **仅 CC-7 改写**（无新对象创建）· `B` = CC-7 + 追加的 trust-boundary 对象（附明细）· `CUSTOM` |
| **`CF-C-7`** | **时序确认**：registry 的正/负探针（ALLOW/DENY 矩阵）必须以 CC-7 落地为前提；P13 seed 仍被 `D-PLAT-09` 序列阻塞 —— 本批**不**做任何 seed。 | `CONFIRM` / `CUSTOM` |

```text
CF-C-5 =
CF-C-6 =
CF-C-7 =
```

### §2.4 三个结构性槽位

> 候选结构 `CC-C-S1 / CC-C-S2 / CC-C-S3`（Request §3.1，**均未被选择**）与下列槽位的关系：
> `CC-C-S1`（部署身份先行）/ `CC-C-S2`（Runbook 步骤 0）/ `CC-C-S3`（窗口期授权 + 降级回收）三者是
> **CF-C-1 + CF-C-5** 的落地方式候选；`CC-7 MODEL` / `MIGRATION ROLE POLICY` / `OWNERSHIP POLICY`
> 是与它们**正交**的实现形态裁定。选择 `CF-C-1 = A` 时，请同时在 `CF-C-5` 中表达持久性倾向
> （或直接指定 `CC-C-S1/S2/S3` 之一作为组合方案）。

| 槽位 | 问题 | 允许值 |
|---|---|---|
| **`CC-7 MODEL`** | CC-7 改写在 0016 中的实现形态 | `A` = 函数体作为**迁移文件内的内联字符串常量**（由 Alembic 执行）· `B` = 函数体独立为 `migrations_alembic/sql/` 下的受版本控制文件，由迁移读取 · `C` = **自定义**（自由文本） |
| **`MIGRATION ROLE POLICY`** | 0016 的执行身份 | `A` = **`uap_migrator`**（经 `UAP_MIGRATION_DATABASE_URL`；与 `OI-B-1 = A` 的 C2 受信身份一致）· `B` = 部署身份执行后再 transition（**不推荐**：违背身份链）· `C` = **自定义** |
| **`OWNERSHIP POLICY`** | 0016 涉及对象的 ownership | `A` = **维持 `uap_migrator`**（CC-7 是对自有函数的替换；`OI-B-3 = CONFIRM` 的延续）· `B` = 其他（附明细）· `C` = **自定义** |

```text
CC-7 MODEL =
MIGRATION ROLE POLICY =
OWNERSHIP POLICY =
```

---

## §3 机读回填区（**全部空白 · 请逐行填写**）

```text
BATCH-C START AUTHORIZATION =
CF-C-1 =
CF-C-2 =
CF-C-3 =
CF-C-4 =
CF-C-5 =
CF-C-6 =
CF-C-7 =
CC-7 MODEL =
MIGRATION ROLE POLICY =
OWNERSHIP POLICY =
CC-7-MODEL-CUSTOM =
MIGRATION-ROLE-POLICY-CUSTOM =
OWNERSHIP-POLICY-CUSTOM =
CF-C-1-CUSTOM =
CF-C-2-CUSTOM =
CF-C-4-CUSTOM =
CF-C-5-CUSTOM =
CF-C-6-CUSTOM =
```

> 说明：`-CUSTOM` 行仅当对应主槽位取 `CUSTOM` 时必填；其余留空。
> **可开工的最小集合** = `BATCH-C START AUTHORIZATION = AUTHORIZED` + `CF-C-1…4` + `CC-7 MODEL` + `MIGRATION ROLE POLICY` + `OWNERSHIP POLICY`（**8 项**）；`CF-C-5/6/7` 强烈建议一并填写（否则实施期将再次 STOP）。

---

## §4 反向保证（可断言）

```text
RB-1  机读回填区无任何预填（全部槽位右侧为空）
RB-2  本文件不含任何 `**已选**` 形式的候选预选标记
RB-3  本文件不含实施步骤、SQL 执行、代码补丁或 diff
RB-4  Request §3 的 `CC-C-S1/S2/S3` 仅为结构描述，本文件未选择其中任何一个
RB-5  本文件未替 Human 裁定 CF-C-1…7 的任何一项
```

---

## §5 解析规则（下一轮直接适用）

| 规则 | 内容 |
|---|---|
| `P-1` | 归一：strip + 大写化；`CUSTOM` 文本保留原文 |
| `P-2` | 主开关 ∈ {`AUTHORIZED`, `NOT AUTHORIZED`}；其他文本 ⇒ `UNRECOGNIZED`（按未答复） |
| `P-3` | `CF-C-1..4` / `CC-7 MODEL` / `MIGRATION ROLE POLICY` / `OWNERSHIP POLICY` 取值须在 §2 各表允许值内 |
| `P-4` | `CUSTOM` 未附文本 ⇒ 视为未填写 |
| `P-5` | 留空 ⇒ `PENDING`（不等于任何候选被接受） |
| `P-6` | 消息通道提交 ⇒ 本文件保持空白时点快照，由 RECORD 登记 |
| `P-7` | 若 `CF-C-1 = B`（有冲突）或 `CF-C-2 = B` ⇒ 该冲突必须附解决路径，否则 `BLOCKED` |

---

---

## §6 消息通道输入登记（`P-6` · 2026-09-27 · 纯追加）

Human 经**消息通道**正式提交 BATCH-C 决策（8 必需 + 3 补充全部有值）。依 `P-6`：本文件 §3 机读回填区**保持空白时点快照**（上方 §3 未改动），决策由 **`OPEN_P10_1_BATCH_C_DECISION_RECORD.md`** 登记并解析。登记摘要：

```text
BATCH-C START AUTHORIZATION = AUTHORIZED
CF-C-1 = 仅批准向 uap_migrator 授予 0016 所需的 schema CREATE 能力          ⇒ A（+约束）
CF-C-2 = 保持 migration identity 为 NOSUPERUSER                            ⇒ A
CF-C-3 = 保持现有 ownership，不发生 ownership transition                   ⇒ A
CF-C-4 = 延后至 BATCH-D 处理 integration / reset_test_database 冲突        ⇒ C
CC-7 MODEL = Trusted Migration Identity Model                              ⇒ CUSTOM（实现形态 A/B ⇒ OI-DC-1）
MIGRATION ROLE POLICY = uap_migrator-only                                  ⇒ A
OWNERSHIP POLICY = Preserve Existing Ownership                             ⇒ A
CF-C-5 = Windowed Privilege + Post-Migration Revocation                    ⇒ B（对齐 D-OP101-12）
CF-C-6 = 0016 Scope Strictly Limited to CC-7                               ⇒ A
CF-C-7 = CC-7 落地并验证后，才允许进入 registry / seed 后续流程             ⇒ CONFIRM
```

⇒ `DECISION STATUS = REGISTERED`（8/8 · 3/3）· `BATCH-C IMPLEMENTATION = AUTHORIZED BUT NOT STARTED` · 下一轮 = `BATCH-C IMPLEMENTATION PRE-FLIGHT` · `0016 = ABSENT` · `BATCH-D = NOT AUTHORIZED`。

**END OF OPEN-P10-1 BATCH-C · HUMAN DECISION BLOCK（2026-09-27 · 空白 · `WAITING HUMAN DECISION` · `BATCH-C = NOT STARTED` · `BATCH-D = NOT AUTHORIZED`）**

**END OF OPEN-P10-1 BATCH-C · HUMAN DECISION BLOCK（2026-09-27 · §6 消息通道输入登记 · `DECISION = REGISTERED` · `BATCH-C IMPLEMENTATION = AUTHORIZED BUT NOT STARTED` · §3 保持空白时点快照 · `BATCH-D = NOT AUTHORIZED`）**
