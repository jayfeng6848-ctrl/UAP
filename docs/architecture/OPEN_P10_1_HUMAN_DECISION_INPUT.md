# UAP — OPEN-P10-1 HUMAN DECISION INPUT（最终输入模板 · **空白待填**）

> ## 状态
>
> ```text
> 轮次          = OPEN-P10-1 HUMAN DECISION RESOLUTION（输入模板生成轮）
> 文档状态      = **INPUT TEMPLATE · 空白（已填 0 / 14）**
> 前置校验      = `OPEN_P10_1_DECISION_RESOLUTION.md` §6 表结构 = **PASS**
>                 （§6 含 6.1…6.14 共 **14** 个子节；每子节含 Human 指定**九字段**；`Current Human Decision` 全部留空）
> 本模板未预选  = `RM-A` / `RM-B` / `RM-C` / `RM-D` **均未被选中**；`CP-A` / `CP-B` / `CP-D` / `CP-E` / `CP-F` **均未被选中**
> 状态保持      = `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`
> 本轮严禁      = ① 只读取现有权威材料（`CORE §13` / `OPEN_P10_1_PREP_REPORT.md` / `OPEN_P10_1_DECISION_RESOLUTION.md` /
>                 `PLATFORM_DECISION_LOG.md` / `D-P13-15` / `D-P11-08`）② 不新增设计 ③ 不选择 `RM-A/B/C/D`
>                 ④ 不选择 `CP-A/B/D/E/F` ⑤ 不推导实施方案 ⑥ 不创建 migration ⑦ 不修改 C2 ⑧ 不 `CREATE ROLE`
>                 ⑨ 不 `GRANT`/`REVOKE` ⑩ 不执行 DDL/DML ⑪ 不 commit/tag/push
> ```
>
> **本文件用途**：把 14 项裁定收敛为**一份可直接填写并回传的输入表**。Human 填毕后，下一轮据此
> 重新读取、解析、并按 §6 规则重算冻结条件。
> **本文件不含任何设计、不含任何实施推导、不含任何裁定倾向**：选项文本**逐字转录**自
> `OPEN_P10_1_DECISION_RESOLUTION.md` §6 各 OQ 的 `Options` 行。

---

## 0. 使用说明（Human 填写须知）

### 0.1 两条填写通道（任选其一；**不一致时以 §3 机读回填区为准**）

```text
通道 A · §2 登记表    ：人类可读；逐行填「裁定结果」列（可选填「备注」列）
通道 B · §3 机读回填区 ：机器可读；每行右侧填写结果，格式 OQ-OP101-NN = <RESULT>
⇒ 只填通道 A 亦可（下一轮会从登记表的**最后一格**解析）；两通道都填且冲突时，以通道 B 为准并**登记冲突**。
```

### 0.2 结果词表（**逐字** · Human 指定）

```text
ACCEPT OPTION A | ACCEPT OPTION B | ACCEPT OPTION C | ACCEPT OPTION D | ACCEPT OPTION E
CUSTOM DECISION | KEEP OPEN | NEED MORE EVIDENCE
```

### 0.3 逐项**有效选项字母**（由 RESOLUTION §6 `Options` 行机械导出 · 供校验用）

| OQ | 主题 | 有效选项字母 | 说明 |
|---|---|---|---|
| `OQ-OP101-01` | 角色拓扑 | `A B C D` | A=`RM-A` · B=`RM-B` · C=`RM-C` · D=`RM-D` |
| `OQ-OP101-02` | migration identity 权限等级 | `A B C` | A=必须 `NOSUPERUSER` · B=接受超级用户 · C=分阶段 |
| `OQ-OP101-03` | revision 编号归属 | `A B C` | A=独占 `0016` · B=不经 Alembic · C=Human 指定编号 |
| `OQ-OP101-04` | 角色创建者 | `A B C` | A=迁移内创建 · B=独立引导脚本 · C=编排/运维预置 |
| `OQ-OP101-05` | C2 判据形态 | **`A B D E F`** | **无 `C`**（`CP-C` 已排除）· A=`CP-A` · B=`CP-B` · D=`CP-D` · E=`CP-E` · F=`CP-F` |
| `OQ-OP101-06` | 是否同时落地 `uap_readonly` | `A B C` | A=同时落地 · B=DEFER · C=较窄的自定义变体（原文 `CUSTOM`） |
| `OQ-OP101-07` | runtime GRANT 矩阵范围 | `A B C` | A=按实际读写面核定 · B=保守全表 DML · C=最小集 |
| `OQ-OP101-08` | 「不持 DDL」是否 DB 层强制 | `A B C` | A=DB 层强制+正向断言 · B=仅文档 · C=A+负向探针 |
| `OQ-OP101-09` | 既有 156 对象所有权 | `A B C` | A=保持 `uap` · B=全量 `ALTER OWNER` · C=仅未来对象 |
| `OQ-OP101-10` | 配置/环境面承载双身份 | `A B C` | A=新增独立键+显式解析链 · B=只改 runtime 侧 · C=仓库零改动 |
| `OQ-OP101-11` | 测试基建与 cluster 级角色 | `A B C` | A=testkit 预置+双 DSN 夹具 · B=仅 integration 夹具 · C=不引入角色 |
| `OQ-OP101-12` | downgrade 语义 | `A B C` | A=FAIL-CLOSED+`DROP ROLE` · B=只 `REVOKE` 保留角色 · C=`CUSTOM` |
| `OQ-OP101-13` | 「身份隔离已成立」机读判据 | `A B C` | A=子集(01∧02∧05∧07∧08) · B=全部 `INV-01…08` · C=拓扑落地+八项测试 |
| `OQ-OP101-14` | 既有守卫 rationale 同步口径 | `A B C` | A=更新 rationale 保留断言 · B=全不动+附录声明 · C=`CUSTOM` |

> **字母集差异是实质信息，不得省略**：`ACCEPT OPTION D` 仅对 `OQ-OP101-01` 合法；`ACCEPT OPTION E` 仅对 `OQ-OP101-05` 合法；
> **`ACCEPT OPTION C` 对 `OQ-OP101-05` 不合法**（`CP-C` 已排除）。

### 0.4 三条硬规则

```text
① `CUSTOM DECISION` 必须附**自由文本**（在 §3.2 明细区写明；未附文本 ⇒ 该行视为**未填写**）。
② **占位符不构成任何一种允许结果**：留空 = 未填写（`PENDING`）；**不得**把留空推断为 `KEEP OPEN`，
   **不得**把留空视为接受任何 `Recommended Direction`。
③ `KEEP OPEN` / `NEED MORE EVIDENCE` 对**全部** 14 项均合法（无需附文本）。
```

### 0.5 `CF-1`（本轮登记的不一致 · **只登记不修改**）

```text
发现：Human 指定结果词表含 `ACCEPT OPTION A/B/C/D/E`（**无 `F`**）；
      而 `OPEN_P10_1_DECISION_RESOLUTION.md` §6.5（`OQ-OP101-05`）的 `Options` 行含候选 `CP-F`（字母 `F`）。
⇒ 处理：**不静默丢弃 `CP-F`，也不擅自扩展词表**。若 Human 期望选 `CP-F`，请二选一：
   (i) 在 §3.2 以 `CUSTOM DECISION` 写明「`CP-F`（`current_user` ∧ `session_user` 合取）」；
   (ii) 明示将词表扩展为 `A…F`（须由 Human 显式给出，本模板不代扩）。
⇒ 本项登记为 `CF-1`（跨文档口径差异）；**不修改** `OPEN_P10_1_DECISION_RESOLUTION.md`（该文件不在本轮授权面内）。
```

---

## 1. 前置校验（本轮**重新读取** RESOLUTION · 只读）

### 1.1 结构校验

| # | 检查项 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| 1 | 文件存在 | 存在 | `docs/architecture/OPEN_P10_1_DECISION_RESOLUTION.md`（647 行） | ✅ |
| 2 | §6 子节数 | 14 | `### 6.1` … `### 6.14` = **14** | ✅ |
| 3 | 子节编号与 OQ 编号一一对应且有序 | `OQ-OP101-01…14` | 6.1→01 · 6.2→02 · … · 6.14→14（逐项核对） | ✅ |
| 4 | 每子节含 Human 指定**九字段**且**顺序正确** | 9 / 9 | `Question` → `Evidence` → `Options` → `Security Impact` → `Runtime Impact` → `Migration Impact` → `Compatibility Impact` → `Downgrade Impact` → `Current Human Decision`（14/14 子节全过） | ✅ |
| 5 | `Current Human Decision` 单元格**全部留空** | 14 / 14 空 | 14 个 `______________` 占位符，无任何已填值 | ✅ |
| 6 | 汇总声明 | `PENDING × 14` | 「`Current Human Decision = **PENDING × 14** · FROZEN = 0 · DEFERRED = 0`」 | ✅ |
| 7 | 冻结条件 | `0 / 7` | 「冻结条件满足 = **0 / 7**」⇒ `DECISION FREEZE WRITE = NOT PERMITTED` | ✅ |
| 8 | 候选标签齐备（**未被选中**） | `RM-A…RM-D` · `CP-A/B/D/E/F` · `CP-C` 已排除 | 全部在位；无任何"已选"标记 | ✅ |
| 9 | 文档状态 | `NOT FROZEN` | `REVISION 2 · NOT FROZEN` | ✅ |
| 10 | 输出状态词 | `READY FOR HUMAN DECISION` | 「`OPEN-P10-1 DECISION PREP = READY FOR HUMAN DECISION`」；且无**肯定式** `IMPLEMENTATION PASS` | ✅ |

### 1.2 决议单指纹（供下一轮比对「填写期间是否被改动」）

```text
文件      = docs/architecture/OPEN_P10_1_DECISION_RESOLUTION.md
行数      = 647
sha256    = 2854fe9d18e77da2a338592539677f0d25da562d206c258694ec513d5580afa3
⇒ 下一轮接线规则：重新计算 sha256；若与上式**逐字节相同** ⇒ 填写期间该文件未被改动（仅本模板被填写）。
   若不同 ⇒ 必须**先登记差异**再解析（不得静默以新版为准）。
```

---

## 2. 14 项 Human Decision 登记表（**待填**）

> 填写方式：在「裁定结果」列写入 §0.2 词表中的**一项**（逐字）；如选 `CUSTOM DECISION`，须同时在 §3.2 写明文本。
> 「备注」列为**可选**；不填不影响解析。

| # | OQ | 主题 | 有效选项字母 | **裁定结果（待填）** | 备注（可选，待填） |
|---|---|---|---|---|---|
| 1 | `OQ-OP101-01` | 角色拓扑 | `A B C D` | | |
| 2 | `OQ-OP101-02` | migration identity 权限等级 | `A B C` | | |
| 3 | `OQ-OP101-03` | revision 编号归属 | `A B C` | | |
| 4 | `OQ-OP101-04` | 角色创建者 | `A B C` | | |
| 5 | `OQ-OP101-05` | C2 判据形态 | `A B D E F` | | |
| 6 | `OQ-OP101-06` | 是否同时落地 `uap_readonly` | `A B C` | | |
| 7 | `OQ-OP101-07` | runtime GRANT 矩阵范围 | `A B C` | | |
| 8 | `OQ-OP101-08` | 「不持 DDL」是否 DB 层强制 | `A B C` | | |
| 9 | `OQ-OP101-09` | 既有 156 对象所有权 | `A B C` | | |
| 10 | `OQ-OP101-10` | 配置/环境面承载双身份 | `A B C` | | |
| 11 | `OQ-OP101-11` | 测试基建与 cluster 级角色 | `A B C` | | |
| 12 | `OQ-OP101-12` | downgrade 语义 | `A B C` | | |
| 13 | `OQ-OP101-13` | 「身份隔离已成立」机读判据 | `A B C` | | |
| 14 | `OQ-OP101-14` | 既有守卫 rationale 同步口径 | `A B C` | | |

```text
已填计数（填写后自报）= 0 / 14
```

---

## 3. 机读回填区（**待填** · 下一轮解析源）

### 3.1 逐项结果（每行右侧填写 §0.2 词表中的一项）

```text
# 语法：OQ-OP101-NN = <RESULT>
# 右侧留空 = 未填写（PENDING）；**不得**推断为 KEEP OPEN，也**不得**视为接受任何 Recommended Direction

OQ-OP101-01 =
OQ-OP101-02 =
OQ-OP101-03 =
OQ-OP101-04 =
OQ-OP101-05 =
OQ-OP101-06 =
OQ-OP101-07 =
OQ-OP101-08 =
OQ-OP101-09 =
OQ-OP101-10 =
OQ-OP101-11 =
OQ-OP101-12 =
OQ-OP101-13 =
OQ-OP101-14 =
```

### 3.2 `CUSTOM DECISION` 明细（如适用）

```text
# 语法：OQ-OP101-NN-CUSTOM = <自由文本>
# 仅当该 OQ 的结果为 CUSTOM DECISION 时必填；未附文本 ⇒ 该行视为未填写

OQ-OP101-01-CUSTOM =
OQ-OP101-02-CUSTOM =
OQ-OP101-03-CUSTOM =
OQ-OP101-04-CUSTOM =
OQ-OP101-05-CUSTOM =
OQ-OP101-06-CUSTOM =
OQ-OP101-07-CUSTOM =
OQ-OP101-08-CUSTOM =
OQ-OP101-09-CUSTOM =
OQ-OP101-10-CUSTOM =
OQ-OP101-11-CUSTOM =
OQ-OP101-12-CUSTOM =
OQ-OP101-13-CUSTOM =
OQ-OP101-14-CUSTOM =
```

---

## 4. 可选：决策载体写入授权（**不属于** §0.2 的 14 项裁定词表）

> 本节为**可选**项，与 §3.1 的 14 项裁定**不同轴**：§3.1 回答「选什么」，本节回答「是否授权把结果写入决策载体」。
> **留空 = 不解锁任何下游动作**（下一轮仍不得写入 `PLATFORM_DECISION_LOG.md`）。

```text
DECISION CARRIER WRITE AUTHORIZATION =
# 可选值（逐字）：AUTHORIZED | NOT AUTHORIZED | （留空 = 未表态）
# 作用范围（若填 AUTHORIZED）：仅授权在 PLATFORM_DECISION_LOG.md **新增** OPEN-P10-1 命名空间条目 + 附录；
#   不改任何既有 D-* 决策正文；不授权 0016/0017 migration、不授权 CREATE ROLE / GRANT / REVOKE、不授权 C2 修改。
```

---

## 5. 下一轮解析与校验规则（机读 · 预先声明）

```text
P-1  结果词表（严格）：
     ACCEPT OPTION A | ACCEPT OPTION B | ACCEPT OPTION C | ACCEPT OPTION D | ACCEPT OPTION E
     | CUSTOM DECISION | KEEP OPEN | NEED MORE EVIDENCE
     归一：strip + 折叠空白 + 去 markdown 标记（` * ）+ 大小写不敏感比对。
P-2  逐项有效性：`ACCEPT OPTION <X>` 仅在该 OQ 的 §0.3 有效字母集内有效；
     例：`OQ-OP101-05 = ACCEPT OPTION C` ⇒ **非法**（`CP-C` 已排除）⇒ 记为无效并**不代裁**。
P-3  `CUSTOM DECISION` 必须有对应 `-CUSTOM =` 非空文本；否则该 OQ 记为**未填写（PENDING）**。
P-4  留空 / 占位符 / 未识别文本 ⇒ 一律**未填写（PENDING）**；**禁止**推断为任何一种结果。
P-5  通道冲突：§3.1 与 §2 不一致 ⇒ 以 §3.1 为准，并**登记冲突**（不得静默）。
P-6  决议单指纹：重新计算 `OPEN_P10_1_DECISION_RESOLUTION.md` 的 sha256 并与 §1.2 比对；不一致须先登记差异。
P-7  冻结条件重算：见 §6。
```

---

## 6. 冻结条件（重算口径 · **当前 0 / 7**）

| # | 冻结条件 | 当前 | 重算方式（下一轮） |
|---|---|---|---|
| 1 | 14 / 14 `OQ-OP101-NN` 均已裁定 | ❌ 0 / 14 | `§3.1` 非空行数 == 14 |
| 2 | 无 `PENDING` 残留 | ❌ | 同上 |
| 3 | 角色拓扑唯一确定（`OQ-OP101-01`） | ❌ | 该行 == `ACCEPT OPTION <A|B|C|D>` 且至多一个字母 |
| 4 | C2 判据唯一确定且 `CC-7` 新先例态度明确（`OQ-OP101-05`） | ❌ | 该行有效字母内 == 恰一项；`F` 按 `CF-1` 处置 |
| 5 | revision 归属确定（`OQ-OP101-03`） | ❌ | 该行 ∈ {A, B, C}；若 `C` 须有编号文本 |
| 6 | `D-P13-15` 前置判据机读化（`OQ-OP101-13`） | ❌ | 该行 ∈ {A, B, C} |
| 7 | 连带同步面口径确定（含 `TEST vs DECISION`，`OQ-OP101-14`） | ❌ | 该行 ∈ {A, B, C} |

```text
当前：冻结条件满足 = **0 / 7** ⇒ `DECISION FREEZE WRITE = NOT PERMITTED`
（即使 §4 填 `AUTHORIZED`，条件 1–7 未满足时**仍不得写入**）
```

---

## 7. 状态保持（本轮实测）

```text
OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED     ← 保持
P13 IMPLEMENTATION        = NOT AUTHORIZED     ← 保持
0016 = ABSENT · 0017 = ABSENT · CREATE ROLE = 0 · GRANT = 0 · REVOKE = 0
C2 = unchanged · DDL = 0 · DML = 0 · commit = 0 · tag = 0 · push = 0
等待 Human 填写：ACCEPT OPTION A/B/C/D/E · CUSTOM DECISION · KEEP OPEN · NEED MORE EVIDENCE
```

---

---

## 8. 输入登记（**append-only · 2026-09-27**）

> 本节为**追加登记**：**不**修改 §0–§7 正文。§2 登记表与 §3.1/§3.2 回填区**保持"空白模板"时点快照**（0 / 14），
> 实际裁定内容逐字登记于本节与 `OPEN_P10_1_HUMAN_DECISION_RECORD.md`（避免形成第二套权威）。

### 8.1 提交原文形（逐字 · 提交通道 = 对话，非本文件回填）

```text
OQ-OP101-01 = ACCEPT OPTION D      OQ-OP101-02 = ACCEPT OPTION A
OQ-OP101-03 = CUSTOM DECISION      OQ-OP101-04 = ACCEPT OPTION C
OQ-OP101-05 = CUSTOM DECISION      OQ-OP101-06 = ACCEPT OPTION B
OQ-OP101-07 = ACCEPT OPTION C      OQ-OP101-08 = ACCEPT OPTION C
OQ-OP101-09 = ACCEPT OPTION B      OQ-OP101-10 = ACCEPT OPTION A
OQ-OP101-11 = ACCEPT OPTION A      OQ-OP101-12 = ACCEPT OPTION B
OQ-OP101-13 = ACCEPT OPTION C      OQ-OP101-14 = ACCEPT OPTION A
```
（另附 `§3.2` 两项 `CUSTOM DECISION` 全文 + 「裁定后的架构边界」+「当前不得提前执行」；全文见 `OPEN_P10_1_HUMAN_DECISION_RECORD.md` §1。）

### 8.2 解析结果（依 §5 `P-1…P-7` 规则）

```text
词表合法性 = 14 / 14 PASS · 逐项有效字母 = 12 / 12 PASS · 已填 = 14 / 14 · PENDING = 0
`KEEP OPEN` = 0 · `NEED MORE EVIDENCE` = 0 · 非法值 = 0 · 未识别文本 = 0 · 通道冲突 = 0
`CF-1` = **RESOLVED**（`OQ-OP101-05` 以 `CUSTOM DECISION` 明文指定 `CP-F` ⇒ 走 §0.5 路线 (i)）
冻结条件重算 = **7 / 7 满足**（前值 0 / 7）
```

### 8.3 §4「决策载体写入授权」= **未提供**

```text
⇒ 依本文件 §4 既定语义「留空 = 不解锁任何下游动作（下一轮仍不得写入 PLATFORM_DECISION_LOG.md）」
⇒ 本轮 `PLATFORM_DECISION_LOG.md` **未被写入**；冻结写入 = **AWAITING AUTHORIZATION**
```

### 8.4 指纹

```text
本文件交付版（追加 §8 之前）= sha256 08c40cf861db1bd6eb52e7aed77b2cd19efb9bf6802f299ac925b507ad96dea8 · 254 行
被回应的解析单   = OPEN_P10_1_DECISION_RESOLUTION.md
                   sha256 2854fe9d18e77da2a338592539677f0d25da562d206c258694ec513d5580afa3 · 647 行（**未变**）
登记载体         = OPEN_P10_1_HUMAN_DECISION_RECORD.md
```

---

**END OF OPEN-P10-1 HUMAN DECISION INPUT（2026-09-27 · **INPUT TEMPLATE · 空白 0/14** · 前置校验 `PASS` · `CF-1` 登记 · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`）**

**END OF OPEN-P10-1 HUMAN DECISION INPUT（2026-09-27 · 追加登记 · §8 输入登记：回应 **14 / 14** · `CF-1` RESOLVED · 冻结条件 **7 / 7** · §4 授权未提供 ⇒ 冻结写入 `AWAITING AUTHORIZATION` · §0–§7 保持空白模板时点快照）**
