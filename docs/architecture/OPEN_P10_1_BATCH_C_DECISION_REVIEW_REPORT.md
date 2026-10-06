# OPEN-P10-1 BATCH-C · HUMAN DECISION SUBMISSION · DECISION REVIEW REPORT

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次              = BATCH-C HUMAN DECISION SUBMISSION（STRICT REGISTRATION ONLY）
> DECISION STATUS   = NOT SUBMITTED（0 / 8 必需槽位 + 0 / 3 补充槽位）
> DECISION RECORD   = NOT GENERATED（条件式未触发 · 见 §0）
> 本报告性质        = REVIEW REPORT（替代交付 · 非决策载体）
> BATCH-C           = NOT STARTED
> BATCH-D           = NOT AUTHORIZED
> 基线              = Phase 0 全锚点零 drift（见 §2）
> ```

---

## §0 命名偏离登记（显式披露）

指令 Phase 4 规定：**仅当 8/8 必填槽位合法**才生成 `OPEN_P10_1_BATCH_C_DECISION_RECORD.md`；若未满足，生成 `OPEN_P10_1_BATCH_C_DECISION_REVIEW_REPORT.md` 并明确 `NOT SUBMITTED`。

本轮实测 = **0/8** ⇒ 生成 `DECISION RECORD` 的条件**未触发**。理由三条：

1. 条件式交付物的前置（8/8 合法取值）客观不成立；
2. 一份名为 "DECISION RECORD" 却不含任何决策的文件会被后续轮次误读为"决策已登记"，构成**第二套权威**；
3. 与本轮 Gate `G-C-2 = FAIL`（Decision completeness）自相矛盾。

替代交付 = 本 REVIEW REPORT。此处置沿用先例：BATCH-B 第八轮（`0/7 ⇒ DECISION_RECORD NOT GENERATED`）与 REVISION RESOLUTION EXECUTION PREP 轮（`0/7 ⇒ RECORD NOT GENERATED`）。

---

## §1 输入性质判定（判据表）

| # | 判据 | 本轮观测 | 结论 |
|---|---|---|---|
| ① | 结构形态 | Human 消息 = Phase 0–5 **规程定义** + 各槽位**允许值描述**（如 `A / B / C`、`CONFIRM / CUSTOM`、候选 `A/B/C`），键名后均为**候选集合**而非单一取值 | 值域声明 |
| ② | 与既有 Block 对应 | Phase 2 所列各槽位允许值与 `OPEN_P10_1_BATCH_C_HUMAN_DECISION_BLOCK.md` §2.2/§2.3/§2.4 逐项一致（CF-C-1…4 · CF-C-5/6/7 · CC-7 MODEL / MIGRATION ROLE POLICY / OWNERSHIP POLICY） | 转载验收规则 |
| ③ | 文件状态（**决定性反证**） | Block §3 机读回填区 **19 行全部空白**（8 必需 + 3 补充 + 8 行 CUSTOM 明细均未填）；文件至 `END OF … HUMAN DECISION BLOCK` 行止，**无「输入登记」追加节**；配套消息通道亦无逐项取值 | 未提交 |
| ④ | 语气 | 规程句在位：`若存在空槽…则 DECISION STATUS = NOT SUBMITTED`、`不得生成 Decision Record`、`如果 Decision 未完整提交：保持 BATCH-C IMPLEMENTATION = NOT STARTED` | 规程指令 |

⇒ **判定 = 规程指令 + 验收规则声明 ≠ 裁定提交**。遵守「无隐式推断 / 不补默认值 / 不从候选矩阵或建议文本推断答案」三条禁令：未把任何文本推断为取值，未把占位/空白解读为 `KEEP OPEN` 或任何候选。

---

## §2 Phase 0 — Baseline Verification（只读实测 · 零 drift）

### §2.1 Git

| 锚点 | 期望（轮前记录） | 实测 | 判定 |
|---|---|---|---|
| HEAD | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` | 同 | PASS |
| branch | `main` | `main` | PASS |
| tags | 8 | 8 | PASS |
| remote | 0 | 0 | PASS |
| dirty | 98（轮前记录） | 98 | PASS |

轮次起始内容快照已落盘（`%TEMP%\uap_snapshot_20260927_batchc_decision_submission.json`，98 条目，schema = `{path:{sha256[:16],mtime,status}}`）。

### §2.2 Migration

| 锚点 | 期望 | 实测 | 判定 |
|---|---|---|---|
| Alembic 单头 | `0015_p12_indexes` | `alembic heads` = `0015_p12_indexes (head)` | PASS |
| 活体 `alembic_version` | 同上 | `0015_p12_indexes` | PASS |
| versions 目录 `.py` 数 | 15 | 15 | PASS |
| `0016` | ABSENT | ABSENT | PASS |
| `0017` | ABSENT | ABSENT | PASS |
| filename/revision 契约 | 无 0016/0017 可违反 | —（无新迁移对象） | PASS |

### §2.3 Database（`uap_b1_test` · 只读查询）

| 锚点 | 期望 | 实测 | 判定 |
|---|---|---|---|
| 非 `pg_%` 角色 | 4（`uap` / `uap_app` / `uap_migrator` / `uap_seed`） | 4，名单一致 | PASS |
| ownership（`pg_class` public，`relkind IN (p,r,i,I)`） | 156 全归 `uap_migrator` · `uap` 残留 0 | `uap_migrator=156`，无其他 owner | PASS |
| ownership（`pg_proc` public） | 22 全归 `uap_migrator` | `uap_migrator=22` | PASS |
| `uap_app` 显式授权（非 owner 合成行口径） | 恰 5 | 5 | PASS |
| 用户级 `pg_auth_members` | 0 | 0 | PASS |
| `pg_default_acl` | 0 | 0 | PASS |
| schema `public` ACL | `pg_database_owner=UC` · `=U` · `uap_app=U` | 完全一致（无 `uap_migrator`/`uap_seed` 项） | PASS |
| schema 特权 | `uap_migrator` CREATE=f（OI-G-3 现状）· `uap_app` CREATE=f / USAGE=t | `f / f / t` | PASS |
| 正式库 `uap` | 0 表（`test_sec4_formal_database_untouched` 守卫基线） | 0 | PASS |

### §2.4 安全锚点

| 锚点 | 期望 | 实测 | 判定 |
|---|---|---|---|
| PDL sha256 | `a83fde5c…ef56` | `a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56` | PASS |
| `0007` 迁移 sha256 | `9e0105b9…c1ef` | `9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef` | PASS |
| C2 函数 md5（`pg_get_functiondef`） | `68678741…af19` | `6867874166ae36966763c1026ab2af19`（`enforce_acl_subject_types_protect`） | PASS |
| 父级触发器 | 39 | 39（`tgparentid=0 AND NOT tgisinternal`，见 §7 口径注记） | PASS |

⇒ **受保护对象 drift = 0，未触发 STOP**。

---

## §3 Phase 1 — Decision Block Parse（逐槽）

语料 = Block §3 机读回填区（唯一答案区；`P-6` 声明消息通道提交时本文件保持空白时点快照——本轮两种通道均无取值）。

| 槽位 | 类别 | 允许值（Block §2） | 实测 | 判定 |
|---|---|---|---|---|
| `BATCH-C START AUTHORIZATION` | 必需 | `AUTHORIZED` / `NOT AUTHORIZED` | 空 | PENDING |
| `CF-C-1` | 必需 | `A` / `B` / `CUSTOM`(+文本) | 空 | PENDING |
| `CF-C-2` | 必需 | `A` / `B` / `CUSTOM`(+文本) | 空 | PENDING |
| `CF-C-3` | 必需 | `A` / `B` / `CUSTOM`(+文本) | 空 | PENDING |
| `CF-C-4` | 必需 | `A` / `B` / `C` / `CUSTOM`(+文本) | 空 | PENDING |
| `CC-7 MODEL` | 必需 | `A` / `B` / `C`(+文本) | 空 | PENDING |
| `MIGRATION ROLE POLICY` | 必需 | `A` / `B` / `C`(+文本) | 空 | PENDING |
| `OWNERSHIP POLICY` | 必需 | `A` / `B` / `C`(+文本) | 空 | PENDING |
| `CF-C-5` | 补充 | `A` / `B` / `C` / `CUSTOM`(+文本) | 空 | PENDING |
| `CF-C-6` | 补充 | `A` / `B` / `CUSTOM`(+文本) | 空 | PENDING |
| `CF-C-7` | 补充 | `CONFIRM` / `CUSTOM`(+文本) | 空 | PENDING |
| CUSTOM 明细 8 行 | 条件必填 | 仅主槽位=CUSTOM 时 | 全空 | 一致（无 CUSTOM 主取值） |

⇒ **必需 0/8 · 补充 0/3 · `DECISION STATUS = NOT SUBMITTED`**（依 Block `P-4`/`P-5`：留空 = PENDING = 未答复 = 不得开工）。

---

## §4 Phase 2 / Phase 3 — NOT EVALUABLE

- **Phase 2（Decision Matrix Validation）= NOT EVALUABLE**：无任何取值可对照 Authorization Request 验证；`CF-C-1…7` 的合法性校验、`P-7`（`B` 取值须附解决路径）均无对象。
- **Phase 3（Scope Validation）= NOT EVALUABLE**：IN/OUT 清单**必须由裁定导出**（本序列先例：BATCH-B 第九轮由 `CF-BB-*` 裁定推导出 8 对象 IN 清单），**不得复制旧名单**。本轮无裁定 ⇒ 无法导出；亦不预先演练"若如此则如何"（防形成未授权的第二套材料）。已核验的既有事实：BATCH-C PREP 轮交付的 `CF-C-1…7` 登记与 `OI-G-3`（`uap_migrator` 无 schema CREATE）现状均保持原样（见 §2）。

---

## §5 Gate（G-C-1…G-C-6）

| Gate | 内容 | 结果 |
|---|---|---|
| `G-C-1` | Baseline unchanged | **PASS**（§2 全锚点实测一致，drift = 0） |
| `G-C-2` | Decision completeness | **FAIL**（必需 0/8） |
| `G-C-3` | Decision values belong matrix | **NOT EVALUABLE**（无取值可校验；可证伪事实 = 识别出的非空取值 = 0） |
| `G-C-4` | No implementation artifact | **PASS**（`0016`/`0017` ABSENT · 迁移 `.py` 数 15 不变 · 无 DDL/DML/ROLE/GRANT/REVOKE/OWNER/C2 变更——以 §2.3/§2.4 等号组证明） |
| `G-C-5` | Scope conflicts resolved | **FAIL**（`CF-C-1…4` 指定冲突 + `CF-C-5/6/7` 补充冲突全部未裁定） |
| `G-C-6` | Protected object unchanged | **PASS**（PDL / `0007` / C2 / 触发器 / 所有权 / 角色 / 授权面全部不变；BATCH-B 9 载体 sha 亦未变——快照逐文件比对） |

harness 独立复算：见 `%TEMP%` 脚本 + 留档日志 `../uap-stage3-evidence/batch_c_decision_review_gate.log`（`checks / passed / failed` 见末行）。

---

## §6 变更面（本轮）

| 类别 | 对象 | 说明 |
|---|---|---|
| 仓库内新增 | 本报告（`docs/architecture/OPEN_P10_1_BATCH_C_DECISION_REVIEW_REPORT.md`） | 唯一仓库内写入 |
| 仓库外 | `%TEMP%` 快照脚本 + 快照 JSON + Gate harness + 证据日志 | 不入审计面 |
| 未触碰 | Decision Block（含其 END 行）/ PDL / 全部代码、迁移、测试、配置 | 逐文件 sha 快照比对未变 |

dirty 集预期 98 → 99（仅 +1 本报告）。

---

## §7 自证缺陷（含口径注记）

| # | 类别 | 描述 | 处置 |
|---|---|---|---|
| 1 | 脚本缺陷 | 父级触发器首查漏 `NOT tgisinternal` ⇒ 267（混入 FK 内建 RI 触发器）；修正口径后 = 39（与冻结记录一致） | 口径注记留档，防下轮误用 267 |
| 2 | 脚本缺陷 | C2 md5 定位首查因列名/别名歧义报 `array_agg` 错误 ⇒ 改逐函数列表法命中 | 无残留影响 |
| 3 | 脚本缺陷 | harness 首轮 **5 项断言 FAIL，全部为脚本缺陷**：① 所有权 SQL `GROUP BY 1` 命中含聚合的输出列（`aggregate functions are not allowed in GROUP BY`）⇒ 改 `GROUP BY pg_get_userbyid(...)`；② `has_schema_privilege(...)||'\|'` 输出 `false/true` 全拼而断言写 `f/t`（语义一致）⇒ 归一后比对；③ §3 切片正则误写 `^## §3\.` 而实际标题为 `## §3 <空格>` ⇒ 改 `^## §3[ ]` | 修正后复跑 **40/40 PASS** |
| 4 | 脚本缺陷（警示） | ③ 的切片失败曾使 2.3–2.5 在 `vals` 为空时**空洞通过**（vacuous truth）——`all(blank)` 对空集合恒真 ⇒ 已由 2.2（键集合相等断言）拦截；此为"数量断言 ≠ 集合断言"的另一面，留档警示 | 复跑确认 vals 含全部 11 键后 blanks 才算数 |
| 5 | 环境事实 | venv `python.exe` 位于 `Scripts/` 子目录（非 env 根） | 非缺陷 |
| 6 | 真实缺口 | **0** | — |

---

## FINAL GATE

```text
FINAL GATE

BATCH-C HUMAN DECISION = BLOCKED（NOT SUBMITTED · 0/8 必需 + 0/3 补充）

Phase 0 baseline = PASS（零 drift · 未触发 STOP）
Phase 1 parse = 0/8 · NOT SUBMITTED
Phase 2 validation = NOT EVALUABLE（无裁定对象）
Phase 3 scope = NOT EVALUABLE（IN/OUT 须由裁定导出，无裁定可导出）
Phase 4 decision record = NOT GENERATED（条件式未触发 · 替代交付 = 本 REVIEW REPORT）
Phase 5 gate = G-C-1 PASS · G-C-2 FAIL · G-C-3 NOT EVALUABLE · G-C-4 PASS · G-C-5 FAIL · G-C-6 PASS

BATCH-C IMPLEMENTATION = NOT STARTED

0016 = ABSENT
0017 = ABSENT

DDL = 0
DML = 0
ROLE CHANGE = 0
GRANT = 0
COMMIT = 0
TAG = 0
PUSH = 0

Gate harness = 留档 ../uap-stage3-evidence/batch_c_decision_review_gate.log
```

## 解除条件（HARD STOP · 等待）

Human 需提交 **8 个必需槽位**（`BATCH-C START AUTHORIZATION` + `CF-C-1…4` + `CC-7 MODEL` + `MIGRATION ROLE POLICY` + `OWNERSHIP POLICY`）的合法取值（Block §3 机读区**或**消息通道均可——消息通道提交时按 `P-6` 处理：Block 保持空白时点快照，由 Decision Record 登记）；**强烈建议连同 `CF-C-5/6/7` 一并裁定**（否则实施期将再次 STOP）。8/8 齐备且主开关 `= AUTHORIZED` 方可进入 BATCH-C 实施；本报告与该裁定**均不授权** BATCH-D。

---

## §8 第二轮再确认（REGISTRATION ROUND · 2026-09-27 20:00 · 纯追加）

第二轮 `BATCH-C HUMAN DECISION SUBMISSION / REGISTRATION`（STRICT REGISTRATION ONLY）执行结果：

### §8.1 Phase 0 再确认（零 drift · 未触发 STOP）

| 锚点组 | 实测 |
|---|---|
| Git | HEAD `034ee97c…` ✓ · `main` ✓ · tags 8 ✓ · remote 0 ✓ · dirty 99（= 98 + 本报告，轮次相对一致） |
| Migration | 活体 `alembic_version` = `0015_p12_indexes` ✓ · 0016/0017 ABSENT ✓ |
| Database | 角色 4 ✓ · ownership `uap_migrator:156` + `uap_migrator:22` = **178/178、残留 0** ✓ · `uap_app` 显式授权 5 ✓ · 用户级成员关系 0 ✓ · `default_acl` 0 ✓ · `uap_migrator` schema CREATE = **false** ✓ · 正式库 `uap` = **0 表** ✓ |
| 安全锚点 | PDL sha `a83fde5c…` ✓ · `0007` sha `9e0105b9…` ✓ · C2 md5 `68678741…` 命中 1 ✓ · 父级触发器 39 ✓ |

### §8.2 Phase 1/2 —— 双通道均无取值

- **Block §3 机读回填区**：仍为 **19 行全空白**（文件 sha 未变，仍为空白时点快照）；
- **消息通道**：本轮 Human 消息仍为 Phase 规程 + 验收规则声明（含"不得从建议、上下文、候选结构或历史习惯推断 Human 选择"明文），**无任何 `槽位 = 取值` 形式的提交**；
- ⇒ 按本轮规则第 4 条：两边均无取值 ⇒ **`DECISION STATUS = NOT SUBMITTED`（0/8）**。

### §8.3 具体缺项清单（等价于等待矩阵）

| # | 槽位 | 类别 | 状态 |
|---|---|---|---|
| 1 | `BATCH-C START AUTHORIZATION` | 必需 | PENDING（空） |
| 2 | `CF-C-1`（schema CREATE 授权 vs `uap_app grants=5` 冲突判定） | 必需 | PENDING（空） |
| 3 | `CF-C-2`（CREATE 后能力充分性 vs NOSUPERUSER） | 必需 | PENDING（空） |
| 4 | `CF-C-3`（ownership transition vs residual=0） | 必需 | PENDING（空） |
| 5 | `CF-C-4`（integration reset vs BATCH-A ownership baseline） | 必需 | PENDING（空） |
| 6 | `CC-7 MODEL`（内联字符串 / sql/ 受版本控制文件 / 自定义） | 必需 | PENDING（空） |
| 7 | `MIGRATION ROLE POLICY` | 必需 | PENDING（空） |
| 8 | `OWNERSHIP POLICY` | 必需 | PENDING（空） |
| 9 | `CF-C-5`（授权生命周期：permanent / window / runbook） | 补充·**实施前实际冲突** | OPEN（空） |
| 10 | `CF-C-6`（0016 是否仅含 CC-7 改写） | 补充·**实施前实际冲突** | OPEN（空） |
| 11 | `CF-C-7`（registry/seed 时序确认） | 补充·**实施前实际冲突** | OPEN（空） |

### §8.4 关键事实保持提醒（Decision Record 生成时的硬约束）

1. **`FD-C-1`**：`CREATE OR REPLACE` 对 `uap_migrator` 自有既有函数**仍需 schema CREATE**（已实测）⇒ `OI-G-3` 是 0016/CC-7 的**实际前置**；未来 Record 不得将其记为"无需处理"。
2. **`OI-BB-14`**：`migrations_alembic/env.py` **不可直接 import**（import 即进入 Alembic 执行路径）；后续测试只能经 CLI/subprocess 探针、独立 helper 或 DB 集成探针；**本阶段不修改测试基建**。
3. **`CF-C-4`**：`reset_test_database()`（19 文件）与 BATCH-A ownership baseline 的冲突是**真实状态冲突**，必须由 Human 显式选择路线，不得在实施阶段隐式决定。

### §8.5 本轮 Gate

复用上轮 harness（G-C-1…6）复跑：Phase 0 各锚点、Block 空白断言、无实施工件断言（0016/0017 ABSENT、无 `.sql`、快照逐文件 byte-identical、新增面仍 = {本报告}）全部成立；日志留档 `../uap-stage3-evidence/batch_c_decision_review_gate_round2.log`。`DECISION RECORD` 仍 = **NOT GENERATED**。

---

## §9 第三轮 Gate 确认（SUBMISSION GATE · 2026-09-27 20:06 · 纯追加）

第三轮 `BATCH-C HUMAN DECISION SUBMISSION GATE` 执行结果：

- **Phase 0 零 drift**：HEAD `034ee97c…` · `main` · tags 8 · remote 0 · dirty 99（轮次相对一致）· 活体 `alembic_version` = `0015_p12_indexes` · 角色 4 · 所有权 `uap_migrator:156`+`uap_migrator:22`（残留 0）· `uap_app` 显式授权 5 · 用户级成员关系 0 · `default_acl` 0 · `uap_migrator` schema CREATE = false · 父级触发器 39 · C2 md5 `68678741…` 命中 1 · 正式库 `uap` 0 表 · PDL sha `a83fde5c…` / `0007` sha `9e0105b9…` / Block sha `255ed9f5` 全部未变。
- **提交载体判定（按本轮 §3 优先级）**：A 不成立（Block §3 仍 19 行全空白，sha 未变）；B 不成立（消息通道仍为规程 + 验收规则声明，无逐项取值）；**C 成立 ⇒ `DECISION STATUS = NOT SUBMITTED` · `BATCH-C = BLOCKED`**。
- **无效取值词核查**：本轮消息列出的"空白 / 未决定 / TBD / 保持开放 / 见上文 / 采用建议"六类均**未出现**（消息中无任何槽位取值文本），无需逐项排除；判定不依赖该排除，而依赖"无取值存在"这一事实。
- **三个既定事实保持**：`FD-C-1`/`OI-G-3`（CREATE OR REPLACE 仍需 schema CREATE，实测）· `OI-BB-14`（env.py 不可直接 import）· `CF-C-4`（reset 与 BATCH-A baseline 真实冲突须显式裁定）——三条硬约束状态不变，仍待未来 Record 显式处理。
- **Gate**：harness 复跑 **40/40 PASS**，日志 `../uap-stage3-evidence/batch_c_decision_review_gate_round3.log`。
- **本轮变更面**：仅本报告 §9 纯追加（END 行保持不动、计数仍 1）；无其他仓库写入。`DECISION RECORD` 仍 = **NOT GENERATED**。

**END OF OPEN-P10-1 BATCH-C DECISION REVIEW REPORT（2026-09-27 · `DECISION STATUS = NOT SUBMITTED` · `BATCH-C = NOT STARTED` · `BATCH-D = NOT AUTHORIZED`）**
