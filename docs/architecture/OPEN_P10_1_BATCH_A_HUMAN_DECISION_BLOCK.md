# UAP — OPEN-P10-1 BATCH-A · HUMAN DECISION BLOCK

> ## 状态
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-A EXECUTION START AUTHORIZATION PREP
> 文件性质  = **DECISION INPUT TEMPLATE · 全部空槽 · 未预填**
> 上游      = OPEN_P10_1_BATCH_A_EXECUTION_AUTHORIZATION_REQUEST.md（请求 · §1…§7）
>             OPEN_P10_1_REVISION_RESOLUTION_RECORD.md（`REVISION RESOLUTION = PASS`）
> BATCH-A   = **NOT STARTED**（保持）
> ```
>
> **本文件不含任何推荐、排序或预选**；**不构成**开工授权。
> `BATCH-A REQUEST ≠ AUTHORIZATION` · `AUTHORIZATION ≠ EXECUTION COMPLETE`。

---

## §1 填写规则（预先声明 · 下一轮无需再发明口径）

```text
P-1  归一：去首尾空白 · 全角→半角 · 大小写不敏感
P-2  逐项有效性：答案必须落在 §2「允许值」内；越界 = 未通过
P-3  留空 ⇒ 该项登记为 `PENDING`；**占位符不构成任何一种允许结果**
P-4  通道冲突：以 §3 机读回填区为准
P-5  `CUSTOM`：须附自由文本（另起一行写明），否则视为未填写
P-6  冻结条件重算：**3 / 3** 全部为允许值 ⇒ 方可生成 BATCH-A 执行指令；
     任意一项 `PENDING` / 越界 ⇒ `BATCH-A = NOT STARTED` 保持，**不得开工**
```

---

## §2 逐项有效值矩阵

| # | 槽位 | 主题 | 允许值 | 是否开工前置 | 待填 |
|---|---|---|---|---|---|
| 1 | `BATCH-A START AUTHORIZATION` | 开工授权 | `AUTHORIZED` · `NOT AUTHORIZED` · 留空 | **必需** | ☐ |
| 2 | `CF-BA-1` | 批次构成口径（新指令 vs 旧 `REQ-5-CUSTOM`） | `NEW`（以本次指令为准）· `OLD`（以 `REQ-5-CUSTOM` 为准）· `CUSTOM` | **范围关键** | ☐ |
| 3 | `CF-BA-2` | 本批创建的角色集合 | `A`（仅 `uap_migrator`）· `B`（`RM-D` 三角色 `uap_seed`/`uap_migrator`/`uap_app`）· `CUSTOM` | **范围关键** | ☐ |

**逐项含义（逐字取自本轮请求与既有决策 · 不增不减）**

```text
① `BATCH-A START AUTHORIZATION`
   `AUTHORIZED`     ⇒ 允许开始 BATCH-A（范围见请求 §2/§3；对象见 §3；前置见 §4；停止条件见 §6）
   `NOT AUTHORIZED` ⇒ 明确不开工（本请求归档）
   留空             ⇒ `PENDING` ⇒ BATCH-A 不得开始
   ⚠️ 该授权**仅**覆盖 BATCH-A；**不含** BATCH-B（config separation）/**C**（migration execution）/**D**（validation）

② `CF-BA-1` 批次构成口径
   背景（逐字对照）：
     本次指令：BATCH-A = Role creation / Role membership / Ownership transfer / Grant boundary preparation
               BATCH-B = config separation · BATCH-C = migration execution · BATCH-D = validation
     旧 REQ-5-CUSTOM：BATCH-A = Role / ownership / grant / **configuration** foundation
               BATCH-B = C2 CC-7 rewrite · BATCH-C = Test infrastructure + security proof · BATCH-D = Full acceptance
   差异要点：`config separation` 旧属 BATCH-A / 新属 BATCH-B；`C2 改写` 旧属 BATCH-B / 新归 BATCH-C。
   `NEW` ⇒ Contract / Matrix 的批次引用按本次指令同步
   `OLD` ⇒ 按 `REQ-5-CUSTOM` 同步（则 `env.py` 等配置面**回到** BATCH-A 范围）
   影响：直接决定 BATCH-A 是否包含 `env.py` / `alembic.ini` / `.env.example` / compose 的改动

③ `CF-BA-2` 本批创建的角色集合
   `D-OP101-01`（FROZEN）冻结的 `RM-D` = **三个角色**：`uap_seed`（registry seed 受信 context）/
       `uap_migrator`（DDL 与所有权承载）/ `uap_app`（runtime 身份）
   本次请求 §3.1 仅登记 **`uap_migrator`**
   `A` ⇒ 本批只创建 `uap_migrator`；`uap_seed` / `uap_app` 留待后续批次
         （后果：`D-OP101-07/08` 的 runtime GRANT 在本批**无受体**；
          `D-OP101-01` 的三角色拓扑在 BATCH-A 后**尚未落地** ⇒ `D-OP101-13` 判据不可达）
   `B` ⇒ 本批创建 `RM-D` 全部三角色（§3.1 只是把与所有权转移直接相关的 `uap_migrator` 列为主对象）
```

---

## §3 机读回填区（**冲突时以本区为准** · 全部留空）

```text
BATCH-A START AUTHORIZATION =
CF-BA-1 =
CF-BA-1-CUSTOM =
CF-BA-2 =
CF-BA-2-CUSTOM =
```

---

## §4 人类可读登记表（与 §3 等价；冲突时以 §3 为准）

| # | 槽位 | 待填 |
|---|---|---|
| 1 | `BATCH-A START AUTHORIZATION` | |
| 2 | `CF-BA-1` | |
| 2b | `CF-BA-1-CUSTOM`（仅 `CUSTOM` 时） | |
| 3 | `CF-BA-2` | |
| 3b | `CF-BA-2-CUSTOM`（仅 `CUSTOM` 时） | |

---

## §5 反向保证（可断言 · 本轮已核）

```text
① §3 机读回填区的 `=` 行**全部空白**（已填 = 0 / 3 主槽位）⇒ 无预填、无"建议值"
② 不含任何裸 `**已选**` 标记 ⇒ 所有候选**均未被预选**
③ 不含实施步骤、不含 SQL、不含代码 ⇒ 不构成实施方案推导
④ 不构成开工授权；不构成任何对 `D-OP101-01…14` 的修改
```

---

## §6 答复后 Bot 的动作（预先声明 · 供 Human 预期）

```text
若 3 / 3 均为允许值且 `BATCH-A START AUTHORIZATION = AUTHORIZED`：
  → 依 §2 的两项口径确定 BATCH-A 的**实际范围与对象**
  → 进入 BATCH-A 执行（`BA-P01`…`BA-P10` 前置逐项落实后才动第一刀）
  → 每步留证；任一步失败 ⇒ 立即 STOP（请求 §6）

若 `AUTHORIZATION = NOT AUTHORIZED` 或留空：
  → `BATCH-A = NOT STARTED` 保持；不得开工

若 `CF-BA-1` / `CF-BA-2` 留空：
  → 即使授权为 `AUTHORIZED`，BATCH-A **仍不得开始**（范围未定 ⇒ 无法安全执行）
  → Bot 将只重新提请未通过的项
```

---

## §7 最终状态（本轮 · 保持）

```text
OPEN-P10-1 BATCH-A = **NOT STARTED**
OPEN-P10-1 IMPLEMENTATION = NOT STARTED
REVISION RESOLUTION = PASS（已结项 · 见 RECORD）

CREATE ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER OWNER = 0
CREATE migration = 0 · alembic upgrade|downgrade = 0 · C2 modification = 0
runtime/config/test 修改 = 0 · DDL = 0 · DML = 0
commit = 0 · tag = 0 · push = 0
0016 = ABSENT · 0017 = ABSENT
```

---

**END OF OPEN-P10-1 BATCH-A · HUMAN DECISION BLOCK（2026-09-27 · 全部空槽 · 未预填 · `BATCH-A = NOT STARTED`）**
