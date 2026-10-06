# UAP — OPEN-P10-1 IMPLEMENTATION AUTHORIZATION REQUEST

> ## 状态
>
> ```text
> 轮次        = OPEN-P10-1 IMPLEMENTATION AUTHORIZATION PREP（**只生成授权请求 · 不实施**）
> 文档状态    = **AUTHORIZATION REQUEST · 未授权 · 未冻结**
> 请求性质    = 本文件是**请求**，不是授权；它把「实施需要哪些授权」摆到 Human 面前，
>               由 Human 以显式授权行答复。**Bot 不代签、不推断、不默认。**
> 本轮未做    = 未 DDL · 未 DML · 未 migration（创建/修改）· 未 code 修改 · 未 database mutation ·
>               未 CREATE ROLE · 未 GRANT/REVOKE · 未 ALTER OWNER · 未函数改写 · 未改 C2/0007 ·
>               未 commit / tag / push
> 当前状态    = `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED`
> ```
>
> **三条不得混淆（贯穿本文件）**
>
> ```text
> ① 本请求 ≠ 授权        —— 收到授权行之前，任何实施动作均不得发生
> ② 授权 ≠ 实施完成       —— 授权只解除"禁止开始"，不改变验收门槛
> ③ 实施授权 ≠ 解除 CC-7   —— C2 改写另需单独确认（见 §5 `REQ-2` 与 §9）
> ```
>
> **as-of 基线（本轮实测 · 请求的有效期锚点）**
>
> ```text
> HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · branch main · tags 8 · remote none · dirty 72
> 单 HEAD = 0015_p12_indexes · versions/001[6-9]* = 0 ⇒ 0016 = ABSENT · 0017 = ABSENT
> PLATFORM_DECISION_LOG.md sha256 = a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
> 非 `pg_%` 角色 = 1（仅 uap）· C2 = unchanged · 0007 = unchanged
> ⇒ 若 Human 答复时上述任一发生变化，本请求须**重新签发**（见 §11 偏差 ④）
> ```

**依据文档**：`OPEN_P10_1_IMPLEMENTATION_PREP_BASELINE_REPORT.md`（Phase 0）·
`OPEN_P10_1_IMPLEMENTATION_CONTRACT.md`（Phase 1 · 含 `R-01…R-08` / `CC-7 Implementation Gate` / `SEQ-0…SEQ-6` / `RB-1…RB-6` / `OI-1…OI-3`）·
`OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md`（39 状态行 + `TRACE-01…14`）·
`PLATFORM_DECISION_LOG.md`（`D-OP101-01…14` + 附录 L）。

---

## 1. 请求性质与边界

```text
本请求要做的事：把"要开始实施 OPEN-P10-1，需要 Human 批准哪些内容"写成一份可答复的授权请求。
本请求不做的事：不实施、不预置环境、不接受风险、不代选任何 `OI-*`、不改任何既有文件。
```

**为什么需要一次独立的实施授权**

```text
J-1  `OPEN-P10-1 DECISION = FROZEN` 只冻结"决策"，不解除"禁止实施"（Charter §6 · `D-P13-15` 明文）
J-2  实施涉及 **6 类产出**（§3），其中 3 类触及既有文件（migration / env.py / settings / testkit / 测试）⇒ 需明确授权面
J-3  实施含**新先例**（跨迁移函数替换 `CC-7`）⇒ 授权不得默示推出（`D-OP101-05` 第 6 条）
J-4  实施含**集群级副作用**（角色为 cluster-scoped）⇒ 授权须覆盖"哪些库 / 哪个环境"
J-5  存在 **3 项未裁开放项**（`OI-1`/`OI-2`/`OI-3`）⇒ 不先裁定则实施范围不可确定（§5）
```

---

## 2. 请求内容（**Human 需答复的授权行**）

```text
OPEN-P10-1 IMPLEMENTATION AUTHORIZATION = AUTHORIZED
```

> **答复形**：请逐字给出上式（或 `NOT AUTHORIZED` / 留空 = 未答复）。**部分授权**请使用 §5 的 `REQ-5`（`AUTH-MODE`）分批形式。

**同时需答复的伴随项（缺任一项则本请求视为未完成答复）**

| 编号 | 需答复项 | 允许值 |
|---|---|---|
| `REQ-1` | 主授权行 | `AUTHORIZED` \| `NOT AUTHORIZED` \| 留空 |
| `REQ-2` | **C2 改写是否纳入本次授权**（`OI-2`） | `A`（纳入 OPEN-P10-1）\| `B`（留在 P13 B-1 Amendment）\| `CUSTOM` |
| `REQ-3` | **所有权转移的成员资格前提**（`OI-1`） | `A`（引导身份临时具备成员资格，转移后回收）\| `B`（由超级用户在受控窗口执行转移）\| `CUSTOM` |
| `REQ-4` | **`0016` 的 revision id / 文件名** | `A` = `0016_open_p10_1_trust_boundary` \| `B` = `0016_open_p10_1_role_boundary` \| `CUSTOM`（须 ≤ 32 字符且 `filename == revision`） |
| `REQ-5` | **授权模式** | `A` = 整体一次授权（`SEQ-0…SEQ-6`）\| `B` = 分批（Stage-1 = `SEQ-0…SEQ-4`；Stage-2 = `SEQ-5` 另开）\| `CUSTOM` |
| `REQ-6` | **独立键键名**（`OI-3`） | `A` = `MIGRATION_DATABASE_URL` \| `B` = `DATABASE_URL_MIGRATION` \| `CUSTOM` |
| `REQ-7` | **授权适用的环境/库范围** | 例：`local/docker only`（`uap` / `uap_b1_test` / `uap_test`）\| `+staging` \| `CUSTOM` |
| `REQ-8` | `commit / tag / push` 是否同时授权 | `NOT AUTHORIZED`（默认，各自独立授权）\| `AUTHORIZED` \| 留空 |

> **默认值声明（重要）**：`REQ-8` 的默认 = **`NOT AUTHORIZED`**（与既有纪律一致：commit/tag/push 各自独立授权）。
> 其余 `REQ-*` **无默认值**：留空 = 未答复 ⇒ 实施**不得**开始。

---

## 3. 授权将覆盖的产出范围（**6 类** · 与 `SEQ-0…SEQ-6` 对齐）

| 编号 | 产出 | 落点 | 授权后仍受约束 |
|---|---|---|---|
| `SCOPE-1` | **环境/编排预置角色**（非迁移） | `uap_seed` / `uap_migrator` / `uap_app`（全部 `NOSUPERUSER`）；compose init 或运维步骤 | 幂等 + 属性校验；不得与 runtime/迁移身份复用（`R-05`） |
| `SCOPE-2` | **每库授权落地** | 各库的 `GRANT`（最小集） | `GRANT` 不跨库 ⇒ 须逐库；不得授予 runtime 任何 DDL |
| `SCOPE-3` | **所有权转移** | **156** 对象 owner → `uap_migrator` | 须先解决 `REQ-3`；不得静默混合所有权；不得 `ALTER` 之外的对象定义改写 |
| `SCOPE-4` | **连接身份分离（配置面）** | `migrations_alembic/env.py` · `alembic.ini` · `config/settings.py` · `.env.example` · `docker-compose.yml` · `tests/conftest.py` · `tests/integration/alembic_testkit.py` | 必须显式化解析链 + 角色断言；`.env.example` 空值语义保持 fail-closed |
| `SCOPE-5` | **新 migration**（**唯一新增 revision**） | `migrations_alembic/versions/0016_*.py`（id 见 `REQ-4`） | `filename == revision` · id ≤ 32 · `down_revision = 0015_p12_indexes` · 单 HEAD · 不含 `CREATE ROLE` / `DROP ROLE` / `SECURITY DEFINER`；`downgrade` 零残留 |
| `SCOPE-6` | **C2 改写**（**仅当 `REQ-2 = A` 且 §9 的 CC-7 前置解除**） | `enforce_acl_subject_types_protect()` 函数体 | 必须满足 `CC7-1…CC7-6`；非 `INSERT` 分支逐字不变；runtime 拒绝消息逐字节一致 |
| （附带） | **测试面同步** | 17 个引用 `0015_p12_indexes` 的文件 · 链长/heads 断言 · `HEAD_REVISION` 常量 · 既有守卫 rationale（`D-OP101-14`） | 改测试须为已授权面；`D-OP101-14` 只改 rationale 不改断言 |

**明确不在请求范围内**

```text
NOT-1  `P13 IMPLEMENTATION`（含 `0017_p13_seed`）—— 属后续独立阶段
NOT-2  `Runtime` 阶段实现（服务/API/worker/scheduler）
NOT-3  `D-OP101-06` 的 `uap_readonly`（已 DEFER）—— 不得借实施之机引入
NOT-4  任何既有冻结决策的改写 / supersede
NOT-5  生产环境迁移（须另开授权并满足备份前置，`MIGRATION_STRATEGY §10`）
NOT-6  `commit / tag / push`（默认 `NOT AUTHORIZED`，见 `REQ-8`）
NOT-7  对 `docs/**` 中历史文档的顺手修改（`IO-1`/`IO-2` 的正式同步属相应用轮次）
```

---

## 4. 实施前置条件清单（**授权后、开工前必须全部成立**）

| 编号 | 前置条件 | 当前 | 谁来满足 |
|---|---|---|---|
| `P-1` | `REQ-1…REQ-7` 均已答复（无留空） | ❌ 未答复 | Human |
| `P-2` | 本请求的 as-of 基线仍成立（§0 的 HEAD / PDL sha / `0016+` = 0 / 角色 = 1） | ✅ 当前成立 | 实施轮复工前复核 |
| `P-3` | `OI-1` 处置（`REQ-3`）已裁定 ⇒ `SCOPE-3` 与 `RB-3` 可实施 | ❌ | Human |
| `P-4` | `OI-2` 处置（`REQ-2`）已裁定 ⇒ `GATE-01` 口径确定 | ❌ | Human |
| `P-5` | `OI-3` 处置（`REQ-6`）已裁定 ⇒ `RUN-01` 断言目标确定 | ❌ | Human |
| `P-6` | 引导身份（具 `CREATEROLE` 或超级用户）已就位且**不与** runtime/迁移身份复用 | ❌ | 环境/运维（`SCOPE-1`） |
| `P-7` | `R-07` 的**运行时读写面盘点**（只读）已完成 ⇒ `SCOPE-2` 的最小集有依据 | ❌ | 实施轮第一步（只读） |
| `P-8` | 目标环境已备份/可回滚（生产另需 `MIGRATION_STRATEGY §10`） | ❌ | 环境/运维 |
| `P-9` | **C2 相关**（仅 `REQ-2 = A` 时需要）：§9 的 `CC-7` 前置全部解除 | ❌ | Human |

---

## 5. 必须先裁定的开放项（**来源 = Phase 1 契约 §8**）

| 编号 | 事项 | 选项 | 为什么必须在授权时一并裁定 |
|---|---|---|---|
| `OI-1` | 所有权全量转移的**成员资格前提**（`D-OP101-09 × D-OP101-02`） | `A` 引导身份临时具备 `uap_migrator` 成员资格（转移后回收）<br>`B` 由超级用户在受控窗口执行转移<br>`CUSTOM` | 决定 `SCOPE-3` 是否可实施、以及 `RB-3`（回滚时的反向转移）路径 |
| `OI-2` | **C2 改写归属轮次** | `A` 纳入 `OPEN-P10-1`（则 `D-OP101-13` 的"八项测试全通过"在本阶段可达）<br>`B` 留在 `P13 B-1 Amendment`（须 Human 明确分期内判据口径）<br>`CUSTOM` | 决定 `GATE-01` 是否可达、`SCOPE-6` 是否在本次授权内、以及 `TEST-05` 的完成时点 |
| `OI-3` | 独立键键名与 `.env.example` 空值语义 | `A` / `B` / `CUSTOM` | 决定 `RUN-01`/`SEC-03` 的断言目标 |
| `REQ-4` | `0016` revision id | `A` / `B` / `CUSTOM` | 一旦写错即产生不可复用的编号（`D-PLAT-09` 阶段序纪律） |
| `REQ-5` | 授权模式（整体 / 分批） | `A` / `B` / `CUSTOM` | 分批可让 `SCOPE-1…SCOPE-5` 先落地、`SCOPE-6`（新先例）留待 `Stage-2` |

> **本文件不推荐任何选项、不代裁**。上述 5 项均为 Human 决策；Bot 仅登记影响面。

---

## 6. 风险接受声明（**授权即表示知悉并接受**）

| 编号 | 风险摘要（详见契约 §4） | 授权即接受的含义 |
|---|---|---|
| `R-01` | 角色为**集群级**、`GRANT` 每库独立、`reset_test_database()` 不清理角色 | 接受"角色存在性是全局副作用"；接受夹具必须幂等 |
| `R-02` | `DATABASE_URL` 同时喂 Alembic 与 Runtime（`env.py` 覆盖 `alembic.ini`） | 接受必须同时改 `env.py` 解析链（**若只改一侧即产生静默失效风险**） |
| `R-03` | C2 改写为**新先例**（跨迁移函数替换，先例前值 = 0）；`D-P13-15` 不授权 C2 修改 | 若 `REQ-2 = A`，即接受在该先例下实施 **并** 单独确认 |
| `R-04` | 156 对象所有权全量转移（35 表 / 108 索引 / 22 函数 / 分区附件） | 接受该改动面；接受"不得静默形成混合所有权" |
| `R-05` | 引导身份需 `CREATEROLE`/超级用户（"鸡生蛋"） | 接受须另行解决引导身份，且不得与 runtime/迁移身份复用 |
| `R-06` | `ALTER … OWNER` 的成员资格前提 | 接受须先解决（= `REQ-3`） |
| `R-07` | GRANT 跨库重复；降级只能回收本库授权；负向 DDL 探针只能在一次性测试库执行 | 接受跨库授权盘点须由环境/运维承担 |
| `R-08` | 环境/测试连带（角色泄漏、测试同步面必然被打破、改测试须批准） | 接受测试面改动属授权面的一部分 |

**已知残余（不阻塞授权，但已登记）**

```text
IO-1  4 行 design-vs-decision delta（CORE_DOMAIN_MODEL.md:1058 · STEP1A_DESIGN_REPORT.md:442 ·
      STEP1B_B0_GATE_REPORT.md:98 · STEP1B_SCHEMA_TEST_MATRIX.md:118）—— 三角色 + `uap_readonly` 的旧陈述；
      与 `D-OP101-01`（RM-D 四角色）/ `D-OP101-06`（`uap_readonly` DEFER）为分阶段口径差异
IO-2  2 行编号重映射（P13_DECISION_COMPLETION_EVIDENCE.md:231 · P13_DECISION_FREEZE_RECORD.md:242）
      —— `0016_p13_seed` → `0017_p13_seed`（由 P13 实施契约轮重登记）
⇒ 两者均由**相应用轮次**以附录式现行口径声明处理；本轮与实施轮**均不顺手修改历史文档**
```

---

## 7. 授权后的执行顺序与**停止点**

```text
SEQ-0  环境/编排预置角色（非迁移）        —— 停止点：角色属性与幂等证据留存
SEQ-1  每库 GRANT（最小集）               —— 停止点：逐库授权集合断言 == 约定最小集
SEQ-2  所有权转移（每库 · 156 对象）      —— 停止点：owner 集合 == {uap_migrator} 且无混合所有权
SEQ-3  连接身份分离（配置面 6 处 + 断言）  —— 停止点：生效 URL 角色 ≠ runtime 角色
SEQ-4  测试基建（幂等预置 + 双 DSN 夹具）  —— 停止点：双角色会话可用 + 集群隔离断言
SEQ-5  C2 改写（**仅 `REQ-2 = A` 且 §9 全开**）—— 停止点：`CC7-1…CC7-6` 逐条证据
SEQ-6  守卫 rationale 同步（只改 rationale）—— 停止点：断言谓词未变（集合运算证明）
```

**每个停止点都必须留存证据**（命令 + 退出码 + 摘要 + 负向样例），并按 `OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` 逐行回填状态；
**`PASSED` 仅在证据齐备后填写**（不得以"计划"或"静态审阅"充当通过）。

---

## 8. 证据与验收绑定（授权不改变门槛）

```text
验收矩阵     = OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md（39 状态行：B 4 · MIG 8 · SEC 9 · RUN 4 · TEST 7 · GATE/OI 7）
              其中 BLOCKED 9 项 = 6 项 C2 相关 SEC + TEST-05 + GATE-01/GATE-02（`REQ-2 = B` 时后者分期解除）
追溯         = TRACE-01…14（`D-OP101-01…14` 100% 覆盖）
回滚         = RB-1…RB-6（含"回滚须覆盖 6 处，遗漏即残留"与 FAIL-CLOSED）
回归基线     = 636 passed / 0 failed / 6 skipped（`RUN-04` 不得下降）
⇒ 授权**只**解除"禁止开始"，**不**降低任何验收门槛、**不**改变 BLOCKED 项的依赖
```

---

## 9. `CC-7` 单独确认（**仅当 `REQ-2 = A` 时适用**）

```text
`D-P13-15` 的 `Does not authorize` 逐字含「C2 修改」⇒ C2 改写**不得**由实施授权**默示**推出。
`D-OP101-05` 虽批准 `CC-7`（新先例），但其第 6 条明文：不得由该 OQ 单独授权实施，仍须独立 Implementation Authorization。

⇒ 若 `REQ-2 = A`，请**额外**逐字给出：
   OPEN-P10-1 C2 REWRITE AUTHORIZATION = AUTHORIZED
   （其效果仅限：允许以 `CREATE OR REPLACE FUNCTION` 改写 C2 的 `INSERT` 分支，
     且必须满足 `CC7-1…CC7-6`；downgrade 须复原授权前版本）

CC-7 Implementation Gate 当前 = **CLOSED**（6 条件中仅 `G-CC7-4` 满足）：
  G-CC7-1 身份隔离已成立        = ❌（实施前）
  G-CC7-2 IMPLEMENTATION 授权   = ❌（本请求待答）
  G-CC7-3 **C2 改写单独确认**    = ❌（§9 该行待答）
  G-CC7-4 CC-7 新先例已批准      = ✅（`D-OP101-05`）
  G-CC7-5 授权前版本已逐字节记录 = ❌
  G-CC7-6 `OI-2` 已裁定         = ❌（`REQ-2` 待答）
```

---

## 10. 机读回填区（**待 Human 填写**）

```text
# 语法：<KEY> = <VALUE>；右侧留空 = 未答复（未答复 ⇒ 实施不得开始）
# 允许值见 §2 的 REQ 表

OPEN-P10-1 IMPLEMENTATION AUTHORIZATION =
REQ-2 =
REQ-3 =
REQ-4 =
REQ-5 =
REQ-6 =
REQ-7 =
REQ-8 =

# 仅当 REQ-2 = A 时填写：
OPEN-P10-1 C2 REWRITE AUTHORIZATION =
```

---

## 11. 本轮边界与自证偏差

```text
本轮变更（全部新增 `.md`，位于 `docs/architecture/`）：
  OPEN_P10_1_IMPLEMENTATION_AUTHORIZATION_REQUEST.md（本文件）
非文档变更 = 0（DDL = 0 · DML = 0 · migration = 0 · code = 0 · database mutation = 0）
```

**自证偏差（逐条 · 如实披露）**

```text
① 本轮**未**执行任何实施动作；数据库侧仅执行只读计数（`pg_roles` 计数）用于确认 as-of 基线。
② 本请求给出 `REQ-4`（revision id）与 `REQ-5`（授权模式）等**选项**，属"请求的必要颗粒度"，
   不构成设计选择；**所有选项均由 Human 裁定**。
③ `REQ-8` 的默认值 `NOT AUTHORIZED` 依据既有纪律（commit/tag/push 各自独立授权）写明，
   属**对既有规则的引用**，非新增约束。
④ **as-of 有效期**：本请求以 §0 的基线为锚点（HEAD `034ee97c…` · PDL sha `a83fde5c…` · `0016+` = 0 · 角色 = 1）。
   若 Human 答复时该基线已变化（例如其他轮次已改动 PDL 或已创建 revision），本请求**须重新签发**。
⑤ 本请求**不代裁** `OI-1` / `OI-2` / `OI-3`；若 Human 希望先单独裁定三项再签发实施授权，属**合法路径**（可分两轮）。
```

---

**END OF OPEN-P10-1 IMPLEMENTATION AUTHORIZATION REQUEST（2026-09-27 · **REQUEST · 未授权** · `OPEN-P10-1 IMPLEMENTATION = NOT AUTHORIZED` · `P13 IMPLEMENTATION = NOT AUTHORIZED` · 等 Human 答复 §10）**
