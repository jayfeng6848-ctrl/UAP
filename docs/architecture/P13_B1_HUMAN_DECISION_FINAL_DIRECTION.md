# UAP — P13 B-1 HUMAN DECISION FINAL DIRECTION

> ## 状态
>
> ```text
> 轮次            = P13 B-1 HUMAN DECISION FINAL DIRECTION（Human 裁定登记 + 阶段切换）
> Gate 结果       = **B-1 FINAL DIRECTION = REGISTERED**
> D-P13-15        = **写入 PLATFORM_DECISION_LOG · FROZEN**（Human 逐字提供文本）
> 执行顺序        = **调整**：OPEN-P10-1 → P13 B-1 Amendment → P13 Implementation
> 下一阶段        = **OPEN-P10-1 PREP / Database Trust Boundary Design（只读设计）**
> P13 IMPLEMENTATION = **NOT AUTHORIZED**（保持）· Runtime = NOT AUTHORIZED
> 0016+ = ABSENT · DDL = 0 · DML = 0 · seed INSERT = 0 · 0007 = unchanged · C2 = unchanged
> commit = 0 · tag = 0 · push = 0
> ```
>
> **本轮性质**：**决策登记轮（DECISION REGISTRATION）**，非实施轮、非验证轮。
> **本轮输入**：`UAP — P13 B-1 HUMAN DECISION FINAL DIRECTION`（2026-09-26，Human）作为
> `P13_B1_HUMAN_DECISION_AMENDMENT.md`（PROPOSED · 未冻结）的正式裁定回应。
> **本轮不做**：不创建 `0016` · 不改 `0007` · 不改 C2 · 不执行 migration · 不 seed · 不改 code / test / config ·
> 不改任何既有 `D-*` 决策正文 · 不 commit / tag / push。

**权威来源（本轮原样读取）**：`P13_B1_HUMAN_DECISION_AMENDMENT.md`（§1–§12）·
`PLATFORM_DECISION_LOG.md`（`D-P10-13` · `D-P11-08` · `D-P13-01…14` · 附录 I.10 / J）·
`P13_IMPLEMENTATION_CONTRACT.md`（§3 BLOCKER B-1）· `P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md`（I-12）·
`CORE_DOMAIN_MODEL.md` §13（三角色模型）· `MIGRATION_STRATEGY.md` §11。

---

## 1. Human Decision（**逐字**）

```text
裁定：
O-1 = REJECT
O-4 = REJECT
O-3 = ACCEPT AS ARCHITECTURAL DIRECTION
O-2 = DEFERRED
```

---

## 2. 核心原因（**逐字** + 机读化）

**核心原因（逐字）**

```text
当前 UAP 数据库不存在 migration/runtime 可区分信任边界：
runtime   = uap(superuser)
migration = uap(superuser)

因此：
* GUC
* application_name
* session variable
* temporary flag
均不得作为安全机制。
```

**机读化（本轮实测复验，`uap_b1_test` @0015）**

| 编号 | 事实 | 实测证据 | 与 Human 核心原因的关系 |
|---|---|---|---|
| `FD-1` | 迁移与运行时**同一 DSN / 同一角色** | `alembic.ini:5` 与 `config/settings.py:57` 均为 `postgresql+psycopg://uap:uap@localhost:5432/uap`；`tests/integration/alembic_testkit.py:21` `BASE_DSN` 同角色 | 直接支撑「不存在可区分信任边界」 |
| `FD-2` | 该角色为**超级用户**且具备全部逃逸能力 | `pg_roles`：`uap` → `rolsuper=t` · `rolcreatedb=t` · `rolcreaterole=t` · `rolbypassrls=t` · `rolcanlogin=t` | 支撑「runtime = uap(superuser)」 |
| `FD-3` | 全库对象**全部**归 `uap` 所有 | `pg_class`（public, 156 对象）→ `owner=uap n=156`；`pg_proc` → `owners=uap`（22 函数） | 所有权不构成额外边界 |
| `FD-4` | 不存在第二个非内建角色 | `pg_roles` 非 `pg_%` 角色 = **仅 `uap`** | 角色分离**完全未落地** |
| `FD-5` | 显式 `GRANT` 面 = 0 | `information_schema.role_table_grants` 中 non-owner grantee = `NONE`；`pg_database.datacl = NULL`；`public` schema ACL = PG16 默认（owner `pg_database_owner`） | 无权限层边界 |
| `FD-6` | 自定义 GUC **可被任意普通会话设置并读回** | 同会话 `set_config('uap.probe_ctx','x',true)` → 读回 `x`；**新会话读回 `<NULL>`** ⇒ 事务级可复原但**无权限门槛、不提供信任** | 支撑「GUC ... 不得作为安全机制」 |
| `FD-7` | `application_name` / 会话变量同属**客户端自述** | 与 `FD-6` 同源（PG 会话参数无服务端身份校验） | 支撑「application_name / session variable / temporary flag 均不得作为安全机制」 |

> **判定**：`FD-1`…`FD-7` 与 `P13_B1_HUMAN_DECISION_AMENDMENT.md` §3 的 `B-1`…`B-4` **逐条一致**，本轮**复验通过**（无新增偏差）。
> ⇒ Human 核心原因**成立**：任何依赖「上下文判据」（GUC / `application_name` / 会话变量 / 临时标志）的方案在**当前信任模型下不可作为安全机制**，
> 与 O-1 / O-4 的 REJECT、O-2 的 DEFERRED 直接对应。

---

## 3. 裁定落地登记表（**逐项 · 机读**）

| 编号 | Human 裁定 | 落地含义（依 Human 指令原文） | 对既有冻结的作用 | 后续义务 |
|---|---|---|---|---|
| `O-1`（受控 DISABLE→INSERT→ENABLE） | **REJECT** | 不接受「临时关闭保护后再恢复」的任何形态 | `D-P13-11` **保持原样**（其「禁临时关闭保护后再恢复」**不被 amend**） | 无（已关闭） |
| `O-4`（承认 registry 保持空） | **REJECT** | 不接受「registry 恒为空 / ACL 在 P13 后仍不可写」 | `D-P13-04` / `D-PLAT-11` 影响面**不重述为"不可达"** | 无（已关闭） |
| `O-3`（移交部署期受信路径） | **ACCEPT AS ARCHITECTURAL DIRECTION** | **方向**被接受：受信写入须发生在**与 runtime 可区分的受信 context** 中；**但**该方向的**前置 = 数据库身份隔离成立** | `D-P13-03` 的「migration-controlled path」**核心目标保持**；其"path"定义的**受信主体**待 `OPEN-P10-1` 落地后重新形式化 | 立项 `OPEN-P10-1`（本文件 §5/§9）；在 `OPEN-P10-1` 冻结后方可回到 P13 B-1 Amendment |
| `O-2`（C2 受控豁免） | **DEFERRED** | **非 REJECT**：技术上仍属"唯一可满足准则的机制族"（Amendment §6①②），但因**前置 `OPEN-P10-1` 未就绪**而**挂起** | `D-P13-11` 核心原则**保持**；**不得**在 `OPEN-P10-1` 落地前实施任何 C2 改写 | 与 `O-3` **共用同一前置**；先决条件解除后再裁定 |

> **重要区分（不得混淆）**：`O-3 = ACCEPT AS ARCHITECTURAL DIRECTION` **不是**实施授权。
> 其本身**不**授权：`0016` migration · registry seed `INSERT` · C2 修改 · runtime 权限扩张（见本文件 §6 与 `D-P13-15`）。
> `O-2 = DEFERRED` **不是** `REJECT`；其**不被关闭**，但在 `OPEN-P10-1` 冻结前**不得**推进。

---

## 4. 执行顺序调整（Human 裁定 · 机读）

```text
执行顺序 = OPEN-P10-1
              Database Trust Boundary Foundation
           ↓
           P13 B-1 Amendment
           ↓
           P13 Implementation

禁止       = 不得直接实施 P13（跳过 OPEN-P10-1）
```

**派生现状（机械后果 · 非新决策）**

| 项 | 原顺序（`D-PLAT-09` 路线 A） | 现行顺序（本裁定后） |
|---|---|---|
| 阶段序列 | `P10 → P11 → P12 → P13 → Runtime` | `P10 → P11 → P12 → OPEN-P10-1 → P13(B-1 Amendment) → P13(Implementation) → Runtime` |
| `D-PLAT-09` | `FROZEN` | **未 supersede · 未改写**；本裁定在 **P13 之前插入一个前置闸门**（`D-PLAT-09` 路线 A 的**细化**，非替代） |
| revision 号 | `P10=0013 · P11=0014 · P12=0015 · P13=0016`（已预留） | **`0016+` 的归属由 `OPEN-P10-1` 冻结时裁定** —— **本轮不由 Bot 指定**（登记为 `OQ-OP101-03`） |

> **编号连续性的风险已登记**：若 `OPEN-P10-1` 需要自己的 revision，则 P13 seed 的 revision 号将**顺延**。
> 这属于 `D-PLAT-09` 阶段序的**派生必然结果**，但**具体编号必须由 Human 裁定**（见 `OPEN_P10_1_DECISION_RESOLUTION.md` `OQ-OP101-03`），
> **本轮不预占、不改写任何既有契约中的 `0016_p13_seed` 引用语义**。

---

## 5. 新增架构目标（Human 裁定 · 机读）

```text
目标 = 建立数据库角色分离，至少区分：
         migration trust context
         runtime application context

运行时不变量（目标态）：
  runtime   : registry INSERT = **DENY**
  migration : controlled registry seed = **ALLOW**
```

**目标态的判据化（分析层 · 供 `OPEN-P10-1` PREP 使用）**

| 维度 | 目标态要求 | 可证伪判据 |
|---|---|---|
| 身份可区分 | migration 与 runtime 使用**不同数据库角色** | `current_user` / `session_user` 在两路径下**不同**且不可互相切换 |
| 不可伪造 | runtime 角色**不是** migration 角色的成员 | 以 runtime 凭据执行 `SET ROLE <migration_role>` **失败** |
| 最小权限 | migration 角色仅持完成 seed 所需最小权限；runtime 角色**不持 DDL** | `has_table_privilege` / `has_schema_privilege` 逐项断言 |
| runtime 拒绝 | registry INSERT 在 runtime context **被拒** | 错误消息与 0007 原版**逐字一致** |
| migration 放行 | controlled registry seed 在 migration context **成功** | 仅 registry 目标行写入；其他一切写入仍被拒 |
| downgrade 完整 | 降级后 C2 定义 = 0007 原文本（逐字）+ 角色/GRANT 回收 | 逐字节比对 + `pg_roles` 无残留受信角色 |

> **本表为"目标态判据清单"，不构成机制选择**。机制族（`M-2` 角色判据 / `M-6` 路径迁移 + `M-4` 载体）已在
> `P13_B1_HUMAN_DECISION_AMENDMENT.md` §4/§6 逐项分析；**具体实现形态属 Human 决策**（见 `OPEN_P10_1_DECISION_RESOLUTION.md`）。

---

## 6. C2 原则保持（Human 裁定 · **逐字**）

**不得（逐字）**

```text
不得：
* DISABLE TRIGGER
* session_replication_role
* 普通 GUC 信任
* application_name 判断
* runtime 可获得 migration 权限
```

**本轮逐条落实登记**

| # | 禁止项 | 落实方式（本轮） | 与既有冻结的关系 |
|---|---|---|---|
| `CP-1` | `DISABLE TRIGGER` | 未执行、未设计、未写入任何文档为可选路径 | 与 `D-P13-11` 一致（该条明文禁止 `DISABLE TRIGGER`） |
| `CP-2` | `session_replication_role` | 未执行；登记为 **永久禁止的安全机制** | `D-P13-11` + Amendment `M-5` |
| `CP-3` | 普通 GUC 信任 | 已由 `FD-6` 实测证明**可伪造** ⇒ 永久排除 | Amendment `M-1`（不满足准则） |
| `CP-4` | `application_name` 判断 | 客户端自述属性 ⇒ 永久排除 | 本轮新增为**显式禁止项**（原 Amendment 仅在测试③中作"伪造尝试"） |
| `CP-5` | runtime 可获得 migration 权限 | 目标态要求 role 严格非成员 + 最小 GRANT（§5） | 与 `D-P10-13` 禁止项「不得给应用运行时 DDL 权限」一致 |

> **新增语义（须在 `OPEN-P10-1` 冻结时形式化）**：`CP-4` 使「`application_name` 判据」从"未被评估为有效机制"升格为
> **Human 明令禁止的机制**。该升格**不修改**任何既有 `D-*` 正文，登记于 `D-P13-15` 与附录 K。

---

## 7. `D-P13-15` 登记（写入 `PLATFORM_DECISION_LOG.md`）

**写入位置（纯插入 · 不改历史正文）**

```text
记录正文   : 插于 `# P13 Canonical Model` 命名空间内、`D-P13-14` 之后（`# 附录 I` 之前的区域）
汇总登记   : `# 附录 K — B-1 Human Decision Final Direction 登记`（**追加至 EOF**）
END 行     : 追加 1 条（旧 END 行**不删**）
```

**记录内容（Human 逐字提供）**

```text
D-P13-15
B-1 Amendment
Purpose:
允许未来受信 migration context 建立 system registry seed，
但前提是数据库身份隔离已经成立。
Does not authorize:
0016 migration
seed INSERT
C2 修改
runtime permission expansion
```

**登记口径声明（如实披露 · 不自行降级）**

```text
① Human 指令 §6 的标题字样为「D-P13-15 建议新增」，其块内**逐字给出** ID / 标题 / Purpose / Does not authorize。
② 本轮轮次名为 `HUMAN DECISION FINAL DIRECTION` 且 §1 为「Human Decision 裁定」⇒ 本登记为该 FINAL DIRECTION 的
   **忠实转录**，status 取 **`FROZEN`**。
③ 该记录**可被 Human 显式否决或重述**（append-only 载体；否决须以新的 Human Decision 进行，不得由 Bot 静默改写）。
④ 若 Human 本意是「待批 / PROPOSED」，须**显式登记降级**；**Bot 不自行降级**（避免 `WRITTEN` 与 `FROZEN` 语义被静默混用）。
```

**`D-P13-15` 的边界（逐条 · 机读）**

| 维度 | 内容 |
|---|---|
| 允许 | 未来**受信 migration context** 建立 **system registry seed** —— **前提**是**数据库身份隔离已经成立** |
| 不授权 | `0016` migration · seed `INSERT` · C2 修改 · runtime permission expansion |
| 前置 | `OPEN-P10-1`（Database Trust Boundary Foundation）**已冻结** |
| 不修改 | `D-P13-01…14` 正文 · `D-P13-11` 禁止字段 · `D-PLAT-09` / `D-PLAT-11` · `D-P10-13` |
| supersession | **0**（本记录为**新增**，不取代任何既有决策） |

---

## 8. 当前状态保持（Human 裁定 · 本轮实测核对）

| 状态项 | Human 指令 | 本轮实测 | 结果 |
|---|---|---|---|
| `P13 IMPLEMENTATION` | `NOT AUTHORIZED` | 无 `0016` · 无实施动作 | ✅ 保持 |
| `0016` | `ABSENT` | `alembic heads` = `0015_p12_indexes`（单头）· `versions/001[6-9]*` = 0 | ✅ 保持 |
| `DDL` | `0` | 本轮 0（仅只读查询 + 1 次事务级 `set_config` 探针） | ✅ 保持 |
| `DML` | `0` | 本轮 0 | ✅ 保持 |
| `0007` | `unchanged` | `0007_b1_4_resource_acl.py` 未修改（`git status` 无该项） | ✅ 保持 |
| `C2` | `unchanged` | 未执行 `CREATE OR REPLACE FUNCTION` · 未 `DISABLE` · 未 `ALTER TRIGGER` | ✅ 保持 |
| `commit / tag / push` | `0` | `HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` · tags = 8 · remote = 0 | ✅ 保持 |

---

## 9. 下一阶段：`OPEN-P10-1 PREP`（**只读设计**）

```text
进入 = OPEN-P10-1 PREP
       Database Trust Boundary Design
       只读设计阶段
禁止 = 不得进入实现
```

**本阶段交付物（本轮已产出 · 全部为**只读设计**，不含实现）**

| 文件 | 性质 | 状态 |
|---|---|---|
| `OPEN_P10_1_PREP_REPORT.md` | 设计报告：Scope · Baseline · Existing Substrate · 实测清单 · 角色模型设计面 · 连接与凭据面 · C2 判据面 · 迁移/恢复面 · 连带同步面 · 依赖四类分离 | **DRAFT · NOT FROZEN** |
| `OPEN_P10_1_DECISION_RESOLUTION.md` | 逐 `OQ-OP101-NN` 决策请求单（九字段；`Recommended Direction ≠ Human Decision`） | **REQUEST SHEET · 未裁定** |
| `OPEN_P10_1_ACCEPTANCE_MATRIX.md` | 验收项（`P-xx` / `R-xx` / `T-xx` / `S-xx` / `GATE`）+ 汇总 | **DRAFT · NOT FROZEN** |

**本阶段明确不做**

```text
不创建角色（CREATE ROLE = 0）· 不授予权限（GRANT = 0）· 不新增/改动任何 migration
不创建 0016+ · 不改 0007 / C2 · 不改 code / test / config · 不改 .env / alembic.ini / settings 默认值
不 commit / tag / push
```

---

## 10. 连带同步面（本轮已同步的文档）

| 文档 | 同步动作 | 性质 |
|---|---|---|
| `PLATFORM_DECISION_LOG.md` | 插入 `# D-P13-15` + 追加 `# 附录 K` + 追加 1 条 END 行 | **纯插入 + 纯追加** |
| `P13_B1_HUMAN_DECISION_AMENDMENT.md` | 插入**决策指针块**（顶部）+ 追加 §13「FINAL DIRECTION 登记」 | 指针 + 纯追加 |
| `P13_IMPLEMENTATION_CONTRACT.md` | 插入**决策指针块**（顶部）+ 追加 §20「B-1 裁定登记」 | 指针 + 纯追加（该契约为 `DRAFT · NOT FROZEN`） |
| `P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md` | 追加 §5「B-1 裁定同步」（`I-12` 状态语义不变） | 纯追加（该矩阵为 `DRAFT · NOT FROZEN`） |

> **未同步项（有意保留 · 不改写）**：`D-P13-01…14` 正文 · `D-P13-11` 禁止字段 · 附录 J · 附录 I.1–I.10 ·
> `0013`/`0014`/`0015` 迁移及其源码内注释（其 `GRANT = 0` 表述属**历史时点事实**，由附录 K 声明**现行口径**）。

---

## 11. 本轮边界与自证偏差（**如实披露**）

```text
本轮变更（全部为 `.md`，位于 `docs/architecture/`）：
  修改 = PLATFORM_DECISION_LOG.md · P13_B1_HUMAN_DECISION_AMENDMENT.md
         · P13_IMPLEMENTATION_CONTRACT.md · P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
  新增 = P13_B1_HUMAN_DECISION_FINAL_DIRECTION.md · OPEN_P10_1_PREP_REPORT.md
         · OPEN_P10_1_DECISION_RESOLUTION.md · OPEN_P10_1_ACCEPTANCE_MATRIX.md
非文档变更 = 0（migration = 0 · code = 0 · test = 0 · config = 0）
```

**自证偏差（逐条）**

```text
① 为复验 `FD-1`…`FD-7`，本轮在**一次性测试库** `uap_b1_test`（@0015）执行了**只读查询** +
   **一次事务本地 `set_config` 探针**（`is_local = true`）。新会话复验 `current_setting('uap.probe_ctx', true)` = `<NULL>`
   ⇒ **无持久影响**；非 DDL / 非 DML；未改变任何触发器状态。
② 未执行 `session_replication_role` / `DISABLE TRIGGER` / `CREATE ROLE` / `GRANT` / `REVOKE`
   —— 仅**登记**"当前角色具备这些能力"这一既有事实（`FD-2`，Amendment `SEC-F1` 沿用）。
③ `uap` 库（formal）实测 `tables = 0` ⇒ 本轮 schema 级实测在 `uap_b1_test` 完成；该库 revision = `0015_p12_indexes`。
4 个库均存在（`postgres` / `uap` / `uap_b1_test` / `uap_test`），本轮**未创建/删除任何库**。
④ 文档切片的强证据不变式（PDL「既有正文零改写」）以 `deleted ⊆ added` 逐行子集证明，见 Gate harness 日志。
```

---

## 12. Gate 结论

| 检查项 | 结果 |
|---|---|
| Human 裁定（`O-1`/`O-4`/`O-3`/`O-2`）= 逐字登记 | ✅ §1/§3 |
| 核心原因 = 复验成立（`FD-1`…`FD-7`） | ✅ §2（实测） |
| 执行顺序调整 = 登记 + 派生后果显式化 | ✅ §4 |
| 新增架构目标 = 登记 + 判据化 | ✅ §5 |
| C2 原则保持 = 五条禁止逐项落实登记 | ✅ §6（`CP-1`…`CP-5`） |
| `D-P13-15` = 写入 PDL（含 Purpose / Does not authorize 逐字） | ✅ §7 + 附录 K |
| 当前状态保持（7 项） | ✅ §8（实测核对） |
| `OPEN-P10-1 PREP` = 已启动（只读设计三件套） | ✅ §9 |
| 状态不变式：`0016+` = ABSENT · `0007` / C2 unchanged · DDL/DML = 0 | ✅ §8/§11 |
| `HEAD` / tags / remote unchanged | ✅ `034ee97c…` / 8 / 0 |
| `D-PLAT-09` / `D-P13-11` / `D-PLAT-11` = **未 supersede · 未改写** | ✅ 附录 K（supersession 新增 = 0） |

```text
P13 B-1 FINAL DIRECTION = **REGISTERED**
D-P13-15                = **FROZEN**（Human 逐字提供文本）
P13 IMPLEMENTATION      = **NOT AUTHORIZED**
OPEN-P10-1 PREP         = **STARTED（READ-ONLY DESIGN）**
⇒ 等待：`OPEN-P10-1` 的 Human Decision（`OQ-OP101-01…14`）
```

---

**END OF P13 B-1 HUMAN DECISION FINAL DIRECTION（2026-09-26 · Gate = `REGISTERED` · `D-P13-15` 写入 · `P13 IMPLEMENTATION = NOT AUTHORIZED` · `OPEN-P10-1 PREP = STARTED`）**
