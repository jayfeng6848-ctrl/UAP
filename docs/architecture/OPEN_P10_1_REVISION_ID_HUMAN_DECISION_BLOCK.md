# UAP — OPEN-P10-1 REVISION ID · HUMAN DECISION BLOCK

> ## 状态
>
> ```text
> 轮次                      = OPEN-P10-1 IMPLEMENTATION BLOCKER RESOLUTION ROUND
> 文件性质                  = **DECISION INPUT TEMPLATE · 空白 0 / 7**（待 Human 填写）
> 上游                      = OPEN_P10_1_BLOCKER_BA1_FACT_SHEET.md（事实）·
>                             OPEN_P10_1_REVISION_ID_RESOLUTION_REQUEST.md（请求）
> BATCH-A                   = **BLOCKED**（保持）
> OPEN-P10-1 IMPLEMENTATION = **BLOCKED**（保持）
> ```
>
> **一次性裁定**：Human 指令 §Phase 2 明令「**不要拆散多轮**」⇒ 本块把 **1 项 revision 裁定 + 6 项开放项**
> 合并为**一轮答复**。全部填毕即同时解除 `B-A1` 与 `OI-B-1…6`。
>
> 本文件**不含**任何推荐、排序或预选；**不构成** revision 选择，**不构成** implementation authorization。

---

## 1. 填写规则（下一轮解析口径 · 预先声明，无需再发明）

```text
P-1  归一：去首尾空白 · 全角→半角 · 大小写不敏感（`RV-a` = `RV-A`）
P-2  逐项有效性：每项的答案必须落在该项的**允许值集合**内（见 §2 表）；越界 = 未通过
P-3  `CUSTOM`：选 `RV-D` 时必须附**自由文本**（`REQ-4-CUSTOM-REVISION-TEXT = <字符串>`），且该文本须满足
       长度 ≤ 32 · 形状 `^\d{4}_[a-z0-9_]+$`（`config/build_info.py::REVISION_PATTERN`）· 序号前缀 = `0016`
P-4  留空 ⇒ 该项登记为 `PENDING`，**不等于**任何允许结果（占位符不构成答复）
P-5  通道冲突：以 §3 机读块为准
P-6  指纹比对：本块填写期间若 §2 的**允许值集合**被改动，须显式登记后再解析
P-7  冻结条件重算：7 / 7 全部为允许值 ⇒ `B-A1` 解除 + `OI-B-1…6` 全部结项；
       任意一项 `PENDING` / 越界 ⇒ `BATCH-A = BLOCKED` 保持，**不进入实施**
```

---

## 2. 逐项有效值矩阵

| # | 项 | 主题 | 允许值 | 待填 |
|---|---|---|---|---|
| 1 | `REQ-4-CUSTOM-REVISION` | 0016 的实际 revision 形态 | `RV-A` · `RV-B` · `RV-C` · `CUSTOM`（＋ `REQ-4-CUSTOM-REVISION-TEXT`，仅 `CUSTOM` 时必填） | ☐ |
| 2 | `OI-B-1` | C2 trusted identity 集合 | `A` = 仅 `uap_migrator` · `B` = `uap_migrator` + `uap_seed` | ☐ |
| 3 | `OI-B-2` | 正式库 `uap` 的处置 | `A` = 将 `uap` 排除出本轮迁移范围 · `B` = 纳入 `uap` 并同步更新既有守卫 | ☐ |
| 4 | `OI-B-3` | ownership target | `CONFIRM`（`uap_migrator`）· `CUSTOM` | ☐ |
| 5 | `OI-B-4` | migration DSN 键名 | `CONFIRM`（`UAP_MIGRATION_DATABASE_URL`）· `CUSTOM` | ☐ |
| 6 | `OI-B-5` | `CC-7` implementation scope | `CONFIRM`（纳入本轮 / 即 PREP `OI-2` 选项 **(a)**）· `CUSTOM` | ☐ |
| 7 | `OI-B-6` | C2 授权形式 | `A` = 须补逐字行 `OPEN-P10-1 C2 REWRITE AUTHORIZATION = AUTHORIZED` · `B` = 接受现有语义授权（§3.2 明文） | ☐ |

**选项含义（逐字取自 Human 指令 §Phase 2，不增不减）**

```text
REQ-4-CUSTOM-REVISION =
  <RV-A / RV-B / RV-C / CUSTOM>
    RV-A = 0016_open_p10_1_trust_boundary   （30 字符）
    RV-B = 0016_p10_1_database_trust        （25 字符）
    RV-C = 0016_db_trust_boundary           （22 字符）
    RV-D/CUSTOM = 由 Human 给定（须 ≤ 32）

OI-B-1: C2 trusted identity:
    A = only uap_migrator
    B = uap_migrator + uap_seed
  事实要点：`D-OP101-05` / REQ-2 逐字为「受信 **migration** identity」（⇒ 字面 = `uap_migrator`）；
            `D-OP101-01`（`RM-D`）把 `uap_seed` 定义为「仅 registry seed 的受信 context」，
            而被保护的表正是 registry `acl_subject_types`。
  影响：`A` ⇒ `uap_seed` 在本阶段无任何权限用途；`B` ⇒ **扩宽唯一安全例外**的接受集合。

OI-B-2: 正式库 uap:
    A = exclude uap from migration scope
    B = include uap and update guards
  事实要点：实测 `uap` = **base**（0 表 / 0 函数 / 无 `alembic_version`）；
            既有守卫 `test_p10_event_audit_schema.py::test_sec4_formal_database_untouched` 断言 `uap` 必须保持 **0 表**。
  影响：`B` 需同时迁 0001…0015（新增 35 表 + 121 索引 + 22 函数）**并**修改该既有守卫。
  注：无论 A/B，`uap` 的**角色层**效果均存在（角色为集群级）；差异仅在**库内对象/授权**层。

OI-B-3: ownership target: confirm uap_migrator
  事实要点：`REQ-3-CUSTOM` 写「历史对象 owner = `uap_owner` / 按冻结 Role Model 的目标 owner」；
            `RM-D`（`D-OP101-01`）**无** `uap_owner`；`D-OP101-09`（FROZEN）逐字为「全量转移至 `uap_migrator`」。
  影响：若确需独立的 `uap_owner` 角色 ⇒ 属**新决策**（`RM-D` 之外的第 4 个角色）。

OI-B-4: migration DSN key: confirm UAP_MIGRATION_DATABASE_URL
  事实要点：`REQ-6` 只规定「完全独立的配置键」与 6 条要求，**未给键名**。
  影响：决定 `env.py` 解析链与 `RUN-01` 的断言目标；亦决定 `.env.example` / compose 的键名。

OI-B-5: CC-7 implementation scope: confirm inclusion
  事实要点：`REQ-2 = CUSTOM DECISION` + §3.2 明文「纳入 CC-7 C2 Rewrite」⇒ 即 PREP §8 `OI-2` 的选项 **(a)**。
  影响：`D-OP101-13` 的「八项测试全通过」判据在 `OPEN-P10-1` 内**可达**；`CC-7 Gate` 的 `G-CC7-6` 同时满足。

OI-B-6: C2 authorization: require exact authorization line or accept existing semantic authorization
  事实要点：请求书 §9 要求单独一行 `OPEN-P10-1 C2 REWRITE AUTHORIZATION = AUTHORIZED`；
            Human 2026-09-27 §1 **未给该行**，但 §3.2 逐字写「**允许本轮实施修改 0007 中 C2 触发器函数体**」。
  影响：`A` ⇒ Bot 在 BATCH-B 之前等待该逐字行；`B` ⇒ 以 §3.2 明文作为显式单独确认（非默示）继续。
```

---

## 3. 机读回填区（**冲突时以本区为准** · 全部留空）

```text
REQ-4-CUSTOM-REVISION =
REQ-4-CUSTOM-REVISION-TEXT =

OI-B-1 =
OI-B-2 =
OI-B-3 =
OI-B-4 =
OI-B-5 =
OI-B-6 =
```

---

## 4. 人类可读登记表（与 §3 等价；冲突时以 §3 为准）

| # | 项 | 待填 |
|---|---|---|
| 1 | `REQ-4-CUSTOM-REVISION` | |
| 1b | `REQ-4-CUSTOM-REVISION-TEXT`（仅 `CUSTOM` 时） | |
| 2 | `OI-B-1` | |
| 3 | `OI-B-2` | |
| 4 | `OI-B-3` | |
| 5 | `OI-B-4` | |
| 6 | `OI-B-5` | |
| 7 | `OI-B-6` | |

---

## 5. 反向保证（可断言 · 本轮已核）

```text
① 本块 `= ` 行**全部空白**（已填 = 0 / 7）⇒ 不含任何预填、不含任何"建议值"
② 不含任何 `**已选**` 标记 ⇒ `RV-A…RV-D` / `OI-B-1…6` 的候选**均未被预选**
③ 不含实施步骤、不含 SQL、不含代码 ⇒ 不构成实施方案推导
④ 不构成 revision 选择；不构成 implementation authorization
```

---

## 6. 答复后 Bot 的动作（预先声明 · 供 Human 预期）

```text
若 §3 全部为允许值（7 / 7）：
  → `B-A1` 解除；`OI-B-1…6` 全部结项；产出「BLOCKER RESOLUTION 轮」记录（append-only 登记）
  → 随后**仍需 Human 的显式开工确认**（`BATCH-A 可以开始` 或等效指令）才进入 BATCH-A
     —— 因为本轮的性质是「仅解除启动前阻断」，不自动开启实施（Human 指令 §目标）

若任意一项 `PENDING` / 越界：
  → `BATCH-A = BLOCKED` 保持；仅重新提请未通过项
```

---

## 7. 最终状态（本轮，保持）

```text
OPEN-P10-1 REVISION RESOLUTION = **WAITING HUMAN DECISION**
OPEN-P10-1 IMPLEMENTATION      = **BLOCKED**
BATCH-A / B / C / D            = BLOCKED / NOT STARTED / NOT STARTED / NOT STARTED

未创建 migration = 0 · 未创建 role = 0 · GRANT/REVOKE = 0 · ALTER OWNER = 0
C2 modification = 0 · 代码/配置/testkit 修改 = 0 · alembic upgrade|downgrade = 0
commit = 0 · tag = 0 · push = 0
0016 = ABSENT · 0017 = ABSENT
```

---

## 8. 输入登记（**第 1 次 · 未提交裁定** · append-only）

> 本节由 `OPEN-P10-1 REVISION RESOLUTION EXECUTION PREP` 轮（2026-09-27 · STRICT READ-ONLY）**纯插入**，
> **§1…§7 逐字未改**；`§3 机读回填区` 保持空白（本节不填写任何槽位）。

```text
登记轮次        = OPEN-P10-1 REVISION RESOLUTION EXECUTION PREP
登记时点        = 2026-09-27
被登记文件      = 本文件（sha256 于登记前 = 3a316f22167d77ad1f5ce3be0d21cf015e281af2be21d590d47455781c4ffb6f · 167 行）

提交形态        = **空白** —— §3（行 99…107）8 个槽位右侧**全部为空**
裁定解析结果    = **7 项 = `NOT SUBMITTED`**（`REQ-4-CUSTOM-REVISION` · `OI-B-1…OI-B-6`）
                  ⇒ **不得**登记为 `KEEP OPEN`、**不得**登记为任何允许结果（占位符不构成答复）

作用域核验      = PASS —— 解析严格锚定 `## 3.` 之后的首个围栏块（行 99…107）
                  §2 行 52 的同键族 `REQ-4-CUSTOM-REVISION =` = **选项图例（decoy）**，命中数 1，**永不计入答案**
反向保证核验    = PASS —— 预选标记 `**已选**` 的 affirmative = **0**（raw = 1，落在 §5 反向保证的自述行）

锚点核验（Phase 0）= 已记录锚点 **6 / 6 一致** ⇒ **drift = 0**，未触发 HARD STOP
  HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · tags = 8 · remote = none
  migration heads = 0015_p12_indexes（单头）· alembic_version = 0015_p12_indexes · 0016/0017 = ABSENT/ABSENT
  附加：PDL sha256 = a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56（未变）
        0007 sha256 未变 · C2 md5 = 6867874166ae36966763c1026ab2af19 未变 · 非 pg_% 角色 = 1 · 显式 GRANT 到非 owner = 0
  登记为 `GAP-anchor-1`（**非 drift**）：三份 Phase 0 文档均未把 PDL sha256 作为锚点 ⇒ 只登记、不回填

Gate 条件重算    = `REVISION RESOLUTION = BLOCKED`
                  `G-1`（长度 ≤ 32）· `G-2`（filename == revision）· `G-3`（pattern 合法）= **NOT EVALUABLE**（无裁定对象）
                  `G-4`（不产生第二套 Decision Carrier）· `G-5`（不改变冻结决策）= **PASS**

解除条件        = 填写 §3 的 7 个槽位，取值须落在 §2「允许值」列内：
                  `REQ-4-CUSTOM-REVISION ∈ {RV-A, RV-B, RV-C, CUSTOM}`
                    （若 `CUSTOM` ⇒ 必须同时填 `REQ-4-CUSTOM-REVISION-TEXT`，须 ≤ 32 · `^\d{4}_[a-z0-9_]+$` · 序号前缀 `0016`）
                  `OI-B-1 ∈ {A, B}` · `OI-B-2 ∈ {A, B}` · `OI-B-3 ∈ {CONFIRM, CUSTOM}`
                  `OI-B-4 ∈ {CONFIRM, CUSTOM}` · `OI-B-5 ∈ {CONFIRM, CUSTOM}` · `OI-B-6 ∈ {A, B}`
后续            = 填毕并裁定后，**仍需** Human 的 `BATCH-A IMPLEMENTATION START AUTHORIZED`（或等效指令）
                  ⇒ **不得自动进入 BATCH-A**

禁令复核        = ① 未推断缺失字段 · ② 未补任何默认值 ·
                  ③ **未把授权消息历史文本作为当前裁定** —— 2026-09-27 `IMPLEMENTATION AUTHORIZATION` 消息中的
                     `REQ-4-CUSTOM-REVISION` 段（39 字符 canonical identity 文本）**不构成当前裁定**；
                     该段现状 = 触发 `B-A1` 的**历史授权文本** ⇒ `0016` 的 revision 形态当前 = **UNDETERMINED**
```

---

## 9. 输入登记（**第 2 次 · 已提交裁定** · append-only）

> 本节由 `OPEN-P10-1 REVISION RESOLUTION` 轮（2026-09-27）**纯插入**，**§1…§8 逐字未改**；
> `§3 机读回填区` **保持空白 0 / 7**（本次提交走 **Human 消息通道**，**未回填**；理由与先例见 RECORD §9.2）。

```text
登记轮次        = OPEN-P10-1 REVISION RESOLUTION（HUMAN DECISION = SUBMITTED）
登记时点        = 2026-09-27
提交通道        = **Human 消息**（非 §3 回填区）
记录载体        = docs/architecture/OPEN_P10_1_REVISION_RESOLUTION_RECORD.md（新增）

提交内容（逐字 7 项）
  REQ-4-CUSTOM-REVISION      = RV-A      ⇒ 实际 revision = 0016_open_p10_1_trust_boundary
  REQ-4-CUSTOM-REVISION-TEXT =           （空 · 非 CUSTOM ⇒ 不适用）
  OI-B-1                     = A         ⇒ C2 受信身份 = 仅 uap_migrator（不扩展 uap_seed）
  OI-B-2                     = A         ⇒ 正式库 uap 排除出本轮迁移
  OI-B-3                     = CONFIRM   ⇒ owner target = uap_migrator
  OI-B-4                     = CONFIRM   ⇒ 独立键 = UAP_MIGRATION_DATABASE_URL
  OI-B-5                     = CONFIRM   ⇒ CC-7 纳入 OPEN-P10-1
  OI-B-6                     = B         ⇒ 接受现有语义授权（无需逐字行）

解析结果        = **7 / 7 合法**（全部落在 §2 允许值集合内；越界 0 · 缺项 0）
形式校验        = revision `0016_open_p10_1_trust_boundary`：长度 30 ≤ 32 · 形状合法 · `filename == revision` · 无同名文件
基线复核        = drift = **0**（HEAD / tags / remote / heads / alembic_version / 0016-0017 全部一致）

结项            = `B-A1` RESOLVED · `OI-B-1…OI-B-6` RESOLVED（6/6）· `OI-1`/`OI-2`/`OI-3` RESOLVED（3/3）· 未结项 0
Gate            = **8 / 8 PASS**（G-1…G-8）

登记项 `CF-R-1`（提请确认）
  `OI-B-4 = CONFIRM` 绑定的是本文件 §2 中列明的 `UAP_MIGRATION_DATABASE_URL`，而**不是**
  授权请求 `OPEN_P10_1_IMPLEMENTATION_AUTHORIZATION_REQUEST.md` 的 `REQ-6` 选项 `A`（`MIGRATION_DATABASE_URL`）。
  依 §1 `P-5`（通道冲突以 §3 为准）与 §2 的逐字绑定，**生效值 = `UAP_MIGRATION_DATABASE_URL`**。
  差异**只登记**，提请 Human 确认（若非本意须显式更正）。

边界（逐字来自本次提交）
  「本消息仅完成 Revision Resolution。不等于：BATCH-A START AUTHORIZED」
  ⇒ `BATCH-A = NOT STARTED` · `OPEN-P10-1 IMPLEMENTATION = NOT STARTED`
  ⇒ **不得自动进入 BATCH-A**；等待 `BATCH-A IMPLEMENTATION START AUTHORIZED`

本轮未做      = migration 创建 · role 创建 · GRANT/REVOKE · ALTER OWNER · C2 修改 · upgrade/downgrade ·
                DDL · DML · PDL 修改 · implementation 文件修改 · commit · tag · push
本轮已做      = RECORD（新增）+ 本节（纯插入）
```

---

**END OF OPEN-P10-1 REVISION ID · HUMAN DECISION BLOCK（2026-09-27 · 空白 0 / 7 · `WAITING HUMAN DECISION` · `OPEN-P10-1 IMPLEMENTATION = BLOCKED`）**
