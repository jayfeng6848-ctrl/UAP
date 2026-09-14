# B1-4 REMAINING HUMAN DECISION FREEZE PACKAGE

**状态**：PREP 阶段 · **仅整理材料，未裁定任何决策**
**版本**：R4（2026-09-13，五项 Human Decision 冻结：D-B14-08 / D-B14-09 / D-B14-10 / D-B14-12 / O-1 / O-2）
**范围**：**D-B14-08 = FROZEN — A** · **D-B14-09 = FROZEN — A** · **D-B14-10 = FROZEN — A-1** · **D-B14-12 = FROZEN — A** · **O-1 = FROZEN — A（84）** · **O-2 = FROZEN** · O-3 / O-4 = P3 · **O-5 = CLOSED** —— **本文件不再存在 OPEN 决策**
**已冻结参照**：D-B14-10 = FROZEN — A-1（2026-09-13）

> **本文件不构成任何冻结**（冻结由 Human Decision 作出）。**R4（2026-09-13）：全部 6 项已由 Human Decision 冻结** —— `D-B14-08 = A` · `D-B14-09 = A` · `D-B14-10 = A-1` · `D-B14-12 = A` · `O-1 = A` · `O-2 = FROZEN`；**不再存在 OPEN / PROPOSED 项**。
> 本轮**未**创建 0007 · **未**修改 migration/Alembic · **未**写 trigger/function SQL · **未**改 tests/ 与业务代码 · **未**执行 DDL/DML · **未** commit/tag。

---

## 1. Current Frozen Facts

| # | 事实 | 复核证据 | 结果 |
|---|---|---|---|
| F-1 | B1-4 不 seed | migration 内 `INSERT INTO acl_subject_types` = 0 处；`SEED_STRATEGY` seed 归 P13 | ✅ |
| F-2 | B1-4 = **0 个** ACL G/H/I/J trigger | `TRIGGER_INVENTORY` §1/§2/§3：G/H/I/J = **P09 后**，逐字未改 | ✅ |
| F-3 | `acl_subject_types` 当前 **0 rows** | 表尚未创建；交付后仍 0 rows | ✅ |
| F-4 | `resource_permissions` 不能产生合法 FK 行 | 注册表空 ⇒ `subject_type_id`(NN,R) 不可满足 | ✅ |
| F-5 | **action vocabulary 未冻结** | `CONSTRAINT_MATRIX:192-197`：`action` **仅在 NN 行**；CK 行**只有** `effect IN ('allow','deny')` ⇒ **无取值约束** | ✅ |
| F-6 | `granted_by` = **actor attribution**，非 owner | `ACL_STRATEGY:115`（写入/删除必须同事务写 `audit_logs` 的 actor 组） | ✅ |
| F-7 | `owner_id` 与 `granted_by` 必须独立处理 | `ACL_STRATEGY:44`：`granted_by uuid REFERENCES users(id)` —— **DDL 无 ON DELETE**；`owner_id` SET NULL 已冻结（F3/GB-02） | ✅ |
| F-8 | Tenant/Space consistency **已冻结为 A-1** | `TRIGGER_INVENTORY` 条目 **F2** = P06/B1-4 · `SCHEMA_DEPENDENCY` §7 · `CONSTRAINT_MATRIX` §3 | ✅ |
| F-9 | Subject Type Registry governance 当前 **OPEN** | `CORE:244-250` · `ACL_STRATEGY:120-129` | ✅ |
| F-10 | B1-4 Implementation = **BLOCKED** | 正式 uap = 0 tables · head `0006` · `0007` absent | ✅ |
| F-11 | **已冻结新 trigger 尚未实现** | `migrations_alembic/` 内 `tg_resources_tenant_space_consistency` = **0 处** | ✅ |
| F-12 | whitelist 现状 = `user` / `role` / `agent`（**不含 `group`**） | `CORE:248` CK 白名单 | ✅ |

---

## 2. D-B14-08 — `resource_permissions.action`

### 2.1 冻结依据重核（五份文档逐份取证）

| 文档 | 原文要点 | 含义 |
|---|---|---|
| `STEP1B_CONSTRAINT_MATRIX.md:192-197` | `NN` 行含 `action`；`UQ uq_resource_perm ON (resource_id, subject_type_id, subject_id, action)`；**CK 行仅 `effect IN ('allow','deny')`** | `action` **只有 NOT NULL + UQ**，**无任何格式或取值约束** |
| `STEP1B_SEED_STRATEGY.md` §4（L99） | `resource.read / resource.write / resource.delete` 出现在 **`permissions` 表（平台级字典，P13）**的 **seed 示例**中；文件明写"**本文档只给形状**"、"具体清单 B1 定稿前由人工审计确认" | 该词表属**另一张表**且**未定稿** —— **不可移植**到 `resource_permissions.action` |
| `STEP1B_B0_GATE_REPORT.md:125` | P3 项："**seed permissions 字典清单待人工定稿** | SEED_STRATEGY §4 已给形状" | 字典**明确未定稿** |
| `B1-4_DECISION_LOG.md:106-119` | 已**撤回**"与 `permissions.key` 同族 CK"旧推荐；现默认 **A**；C = 越界明确禁止 | 现推荐 A |
| `B1-4_SCHEMA_DESIGN.md:186` | 差异 #4：`action` 无格式/取值约束；"**禁止**定义取值语义" | 与 A 一致 |
| `B1-4_TEST_MATRIX.md:157-162,202` | ACT-01/ACT-02 = 表格行；**ACT-03 = 正文条件项** | 见 §6 |

### 2.2 当前事实（确认）

1. **`resource_permissions.action` 必须 NOT NULL** —— 已冻结（`NN` 行），**结构性要求**，无需新裁定。
2. **当前没有冻结 action semantic vocabulary** —— 无 CK、无枚举、无 seed（`resource_permissions` 无任何 seed 行）。
3. **不得自行引入** `read` / `write` / `create` / `update` / `delete` / `resource.read` / `resource.write` 等语义词表。
4. **不得因为测试方便而擅自增加 action CHECK vocabulary** —— ACT-03 的存废须由 Human 裁定，**不得为让 ACT-03 成立而反向发明词表**。

> **易混淆点（本轮取证重点）**：`SEED_STRATEGY:99` 确实存在 `resource.read/write/delete` 字样，但它属于 **`permissions` 表（P13 平台字典，且明确未定稿）**；`CORE:180` 同理（`permissions` 用途举例）。
> **把该形状移植到 `resource_permissions.action` 即构成跨表语义扩张，属 Human 决策范围，Bot 无权采用。**

### 2.3 候选方案

| 候选 | 内容 | 是否构成新 semantic contract | 需 Human |
|---|---|---|---|
| **A** | **不新增** semantic action constraint。仅保留：`NOT NULL` + 已冻结的 `UQ(resource_id, subject_type_id, subject_id, action)`（+ 既有结构性约束） | **否** —— `action` 为**不透明字符串** | 无需（默认）；仍列为选项 |
| **B** | **增加结构性 CHECK**。**具体内容**（二择一，均只约束"形状"）<br>**B-1**：`action ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$'`（**沿用 `permissions.key` 既有正则**，`CONSTRAINT_MATRIX:120`）<br>**B-2**：`action ~ '^[a-z][a-z0-9_.]{1,63}$'`（长度+字符集，`DECISION_LOG:112`） | **边界情形**：正则本身不含语义词 ⇒ 属结构 CK；**但若与命名空间约定（如 `resource.` 前缀）绑定，即演化为 semantic contract**，须重新裁定 | **是（新增约束）** |
| **C** | **建立 action vocabulary**（枚举 / 白名单 / 语义词表） | **是（强语义契约）** —— 冻结授权语义 | **该方案会形成新的语义契约，因此不能由 Bot 自行决定** |

| 项 | 值 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— 零新增 semantic/format contract；`action` = **opaque identifier**；不新增 regex/命名空间 CHECK、enum、whitelist、vocabulary；**不迁移**未来 `permissions` seed dictionary；候选 B 未采纳 ⇒ **`ACT-03` 条件未成立（conditional / non-canonical）** |
| **裁定结果** | ✅ **A（2026-09-13 Human Decision）**；候选 B **未采纳**；C 不在可选范围 |
| **ACT-03 存在性** | **条件未成立** —— D-B14-08 = A ⇒ B 未采纳 ⇒ ACT-03 **不登记、不计入 canonical（84）** |
| **裁定时间** | 2026-09-13（Human Decision） |

---

## 3. D-B14-09 — `granted_by`

### 3.1 冻结依据重核

| 来源 | 原文要点 |
|---|---|
| `ACL_STRATEGY:44` | `granted_by uuid REFERENCES users(id)` —— **未写 ON DELETE（默认 NO ACTION）** ⇒ **删除行为未冻结** |
| `ACL_STRATEGY:115` | "`resource_permissions` 写入/删除必须同事务写 `audit_logs`：actor、resource、subject、action、effect、**granted_by**" ⇒ **audit actor 组** |
| `CONSTRAINT_MATRIX:193` | FK：`granted_by NULL → users.id`（**可空**）；NULL 行含 `granted_by` |
| `B1-4_DECISION_LOG.md:123-137` | 语义 = **actor attribution** |

### 3.2 语义独立性证明

```text
granted_by   ∈  resource_permissions  ，语义 = actor attribution（审计主体：谁授予）
owner_id     ∈  resources             ，语义 = resource ownership（所有权：资源归谁）
```

| 维度 | `granted_by` | `owner_id` |
|---|---|---|
| 所属表 | `resource_permissions` | `resources` |
| 语义 | **审计归属**（谁授予这次授权） | **所有权**（资源属主） |
| 可空性 | **NULL 允许**（已有） | NULL 允许（已有） |
| ON DELETE | **未冻结**（本决策对象） | **SET NULL 已冻结**（F3/GB-02） |
| 删除后受影响对象 | 授权**仍然有效**，仅审计主体丢失 | 资源**仍然存在**，仅属主丢失 |
| 是否可互换 | ❌ **不可** —— 二者行不存在于同一表，且语义正交 | ❌ 同左 |

**结论：两者语义独立、不可合并** ⇒ `GB-01` 与 `F3` / `GB-02` **必须分列测试，禁止合并**。

### 3.3 候选方案分析

| 分析维度 | **A** `SET NULL`（proposed） | **B** `RESTRICT` | **C** `CASCADE` |
|---|---|---|---|
| **ACL 记录生命周期** | ACL 行**保留** ✅ | ACL 行**保留** ✅ | **ACL 行被删除** ⚠️ |
| **actor attribution 是否应保留** | 行保留但 `granted_by` → NULL，**审计主体丢失**（依赖 `audit_logs` 补偿；P10 才建表） | **完整保留**（引用不可破坏） | **彻底丢失** ❌ |
| **user hard delete 行为** | 可删 user；ACL 静默失去审计主体 | **删 user 被阻止** ⇒ 须先处理 ACL 引用 | 可删 user；**连带删除全部授权** |
| **与 `owner_id` 删除策略区别** | **同为 SET NULL，但对象与语义不同**：owner 丢失不影响资源存在；actor 丢失不影响授权有效 | 更严于 `owner_id`（owner 是 SET NULL，actor 变 RESTRICT ⇒ **不一致**） | 与 `owner_id` **性质相反**（一处保留、一处删除） |
| **是否可能造成 ACL 意外删除** | **否** ✅ | **否** ✅ | **是** ❌ —— 删 user 即静默撤销授权，存在越权/失效边界漂移 |
| **与既有语义冲突** | 与 user 软删保留 ACL 一致；硬删清理属条目 **H（P09 后）** 职责 | **与 user 软删保留 ACL 的既有语义冲突**（删除需先解引用） | 与 **H** 职责重叠、且方向相反 |

| 项 | 值 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— `resource_permissions.granted_by` **`ON DELETE SET NULL`**；语义 = **actor attribution**（非 ownership）；**`F3` / `GB-02`（owner_id）与 `GB-01`（granted_by）三条分列，禁止合并**；**不得**因 SET NULL 修改 `owner_id` 既有删除策略 |
| **需 Human 裁定** | 选择 **A / B / C** |
| **裁定时间** | 2026-09-13（Human Decision） |

---

## 4. D-B14-10 = **FROZEN — A-1**

| 项 | 值 |
|---|---|
| **CURRENT** | **FROZEN — A-1（2026-09-13 Human Decision）** |
| **冻结内容** | `tg_resources_tenant_space_consistency`：**BEFORE INSERT OR UPDATE**；`tenant_id` NOT NULL；`space_id` nullable；`space_id IS NOT NULL` ⇒ 要求 `spaces.tenant_id = resources.tenant_id`；Tenant-A + Tenant-A Space → **ALLOW**；Tenant-A + Tenant-B Space → **REJECT**；`space_id IS NULL` → **ALLOW**；**覆盖 INSERT + UPDATE** |
| **边界** | **structural integrity only —— 不是 authorization evaluator**；不引入 RLS；不引入 Domain/Agent/Tool/AI/Event/Audit 依赖 |
| **B0 同步（已完成）** | `TRIGGER_INVENTORY` 条目 **F2**（P06/B1-4）· `SCHEMA_DEPENDENCY` §7 = P06 · `CONSTRAINT_MATRIX` §3 `resources` 增 TRIGGER 行。**G/H/I/J 保持 P09 后，既有相位未重排** |
| **实现状态** | **未实现** —— migration 内 0 处；`0007` absent |
| **阻塞状态** | ✅ 已关闭，不再阻塞 |

---

## 5. D-B14-12 — Subject Type Registry Governance

### 5.1 冻结依据重核

| 来源 | 原文要点 |
|---|---|
| `CORE:244` | purpose = "把『ACL 主体是多态』升级为**受控的注册机制**；新增 subject type 必须先在此注册，否则 ACL 写入触发 trigger 拒绝" |
| `CORE:248` | CK 白名单：`key IN ('user','role','agent')`（**不含 `group`**） |
| `CORE:249` | 扩展路径：新增 type = 插一行注册；删除 = 先归档 + 清理该 type 的 ACL |
| `CORE:250` | **"`group` 是未来扩展，不是 STEP 1-B 可用 ACL subject"** |
| `ACL_STRATEGY:120-129` | 未来 group 启用路径（4 步），**B1 不实现** |

### 5.2 当前事实（确认）

- `acl_subject_types` = **platform-controlled registry**（`CORE:252` 备注：平台级，无租户维度）。
- whitelist = `user` / `role` / `agent`，**本轮不修改**。
- **B1-4 不 seed**（F-1）。
- **Domain / Plugin 不允许 runtime 自由注册**。
- **不得增加 `group` 等未冻结 subject type**；**不得修改现有 whitelist**。

### 5.3 候选方案

| 候选 | 内容 | 结构性影响 | 治理边界评估 |
|---|---|---|---|
| **A** | **Platform-controlled registry + protection mechanism**（`tg_acl_subject_types_protect`：运行时 INSERT / `key` UPDATE / DELETE 拒绝，退役走 `archived_at`） | +1 trigger +1 function（B1-4 内，仅依赖自身对象） | ✅ **不越界** —— 强化"平台受控"既有定位 |
| **B** | **维持 CK + migration/process discipline**（现状，无 DB 强制） | 无 DDL 变更 | ✅ **不越界** —— 但 registry 可被运行时 INSERT 绕过（依赖纪律，DB 无保证） |

**非推荐扩展方案（仅登记，不得自行加入冻结设计）**：

| 方案 | 内容 | 判定 |
|---|---|---|
| **C（非推荐）** | Plugin API runtime registration —— 运行期注册新 subject type | ❌ **违反既有 Core/Platform governance 边界**（registry 为平台级受控；`CORE:250` 明确扩展须走平台路径） |

| 项 | 值 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— **platform-controlled registry + protection mechanism**（`tg_acl_subject_types_protect`，P06/B1-4）；whitelist 保持 `user`/`role`/`agent`（**不增 `group`、不改 whitelist、不提前 seed**）；Domain / Plugin / 普通业务代码 runtime 注册**不允许**；**registry governance only，不演变为 Domain authorization** |
| **需 Human 裁定** | 选择 **A / B** |
| **裁定时间** | 2026-09-13（Human Decision） |

---

## 6. O-1 — TEST MATRIX Canonical Count

### 6.1 已复核计数事实（逐条解析正文）

| 项 | 值 | 依据 |
|---|---|---|
| 基础七类 | **71** | S1–S11(11) + F1–F7(7) + C1–C10(10) + A0-1…A0-5 + A1–A11(16) + I1–I5 + R-ISOLATION-01…05(10) + M1–M10(10) + SEC1–SEC7(7) |
| §8 decision-dependent 表格行 | **13** | ACT-01/02(2) + GB-00/01/02(3) + TC-00…TC-04(5) + REG-01…03(3) |
| **正式表格行** | **84** | 71 + 13 |
| ACT-03 | **条件项（非表格行）** | 仅出现于正文 L162 / L202 |
| §10 登记项 D1–D7 | **7 行（无标注）** | **不属于** canonical count |

### 6.2 两个方案

#### O-1-A — Canonical total = **84**

> **定义**：Total 指**正式测试矩阵表格中的测试行数量**。ACT-03 为**条件性测试项**，**不计入** canonical table total。

- 优点：定义客观可机检（`^\| <ID> \|` 行计数），**不随条件存续漂移**。
- 缺点：ACT-03 若被采纳，需另设"条件测试登记区"，易被漏读。

#### O-1-B — Canonical total = **85**

> **定义**：Total **包含 ACT-03 条件测试项**。**若采用 B，必须将 ACT-03 明确纳入 canonical test inventory**（即在正文以**可机读条目**形式登记，而非仅散文提及）。

- 优点：覆盖全部潜在测试。
- 缺点：**ACT-03 存在性依赖 D-B14-08 裁定** ⇒ canonical total **随裁定结果在 84 / 85 间变化**，数字不稳定。

### 6.3 确认项

- **`D1–D7` 不属于 B1-4 TEST_MATRIX canonical count** —— 已确认（§10 = "后续阶段登记（承接，不在 B1-4 执行）"，7 行均无三分标注）。

| 项 | 值 |
|---|---|
| **CURRENT** | **FROZEN — A（2026-09-13 Human Decision）** —— **Canonical Total = 84**（71 + 13）；`ACT-03` = conditional / non-canonical（不计入）；`D1–D7` 不计入 |
| **需 Human 裁定** | **O-1-A（84）** 或 **O-1-B（85）** |
| **本轮是否修改 TEST_MATRIX** | ❌ 否（仅提出方案） |

---

## 7. O-2 — Test Status 单一状态规范

### 7.1 现状实读（**与提问前提的差异必须报告**）

提问列出"三个双标签：R-ISOLATION-01 / GB-01 / REG-01"。**逐行实读结果如下**：

| 行 | ID | **实际标签** | 判定 |
|---|---|---|---|
| ~~L112~~ | ~~`R-ISOLATION-01`~~ | `【B1-4】` | ✅ **单标签** —— **已随 D-B14-10 = A-1（R3）解决**，原双标签**已不存在** |
| L169 | `GB-01` | 原 `【后续】` + `【待裁定】` | ✅ **已于 R4 修正为 `Current Status = 【后续】` / `Post-Approval Level = —`**（D-B14-09 = A 已批准） |
| L188 | `REG-01` | 原 `【B1-4】` + `【待裁定】` | ✅ **已于 R4 修正为 `Current Status = 【B1-4】` / `Post-Approval Level = —`**（D-B14-12 = A 已批准） |

> **事实修正**：双标签实际**仅剩 2 处**（`GB-01` / `REG-01`），**并非 3 处**。`R-ISOLATION-01` 的问题已由 A-1 冻结自然消解。**本轮未修改文件，仅报告。**
> 其余 `R-ISOLATION-02…05`、`GB-00`、`GB-02`、`REG-02`、`REG-03` 均为单标签 ✅。

### 7.2 统一格式提案（**已由 O-2 = FROZEN 采纳并落地**）

**禁止**在同一 `Status` 字段出现双标签（如 `【B1-4】+【待裁定】`）。改为**两个独立字段**：

```text
Current Status       = 【待裁定】
Post-Approval Level  = 【B1-4】
```

示例（GB-01 / REG-01 改造后）：

```text
| ID     | 断言                                     | 期望      | Current Status | Post-Approval Level |
| GB-01  | 删 granted_by 对应 user → ACL 保留 + NULL | 保留+NULL | 【后续】        | —                    |
| REG-01 | 运行时 INSERT acl_subject_types 被拒       | 拒绝      | 【B1-4】        | —                    |
```

**规则**：
1. `Current Status` —— **唯一**状态，取值 ∈ {`【B1-4】`,`【后续】`,`【待裁定】`}。
2. `Post-Approval Level` —— **仅当 `Current Status = 【待裁定】` 时填写**；表示批准后的归属层级，**不改变**"当前不可执行"的事实。
3. 三分状态统计**只对 `Current Status` 计数** ⇒ 天然满足"一测试一状态"。

| 项 | 值 |
|---|---|
| **CURRENT** | **FROZEN（2026-09-13 Human Decision）** —— 采用 **`Current Status` + `Post-Approval Level`** 双字段模型；`Current Status` **每条唯一**；禁止同一字段出现两个 `【…】` |
| **需 Human 裁定** | 采纳上述双字段格式，或**显式允许**双记法并同步修订审计规则 |
| **本轮是否修改 TEST_MATRIX** | ❌ 否（仅提出方案） |

---

## 8. O-3 / O-4 — P3 Deferred Items

### O-3 — §5 表格行序

实读 §5 实际行序：`I1 → I2 → I3 → I4 → R-ISOLATION-01…05 → I5`。
`I5` 仍排在 `R-ISOLATION-05` 之后（R3 插入 R-ISOLATION 行后**该问题更明显**）。

- **性质**：纯排版，**不改变编号含义与任何测试状态**。
- **与 A-1 文档冲突检查**：**无冲突** —— 仅顺序，不涉及 phase/dependency/purpose。
- **CURRENT = P3**（记录；**未升级、未关闭、未转为 blocker、未修改**）

### O-4 — §10 登记项归属

`D1–D7`（7 行）**继续作为矩阵外登记项**：
- **不参与**三分状态计数（无标注，设计如此）；
- **不参与** canonical count（无论 O-1-A 或 O-1-B）。

- **与 A-1 文档冲突检查**：**无冲突** —— `D7` 引用 `A1–A11 / F4–F6 / C10 / ACT-02`，未涉及 D-B14-10 相关项。
- **CURRENT = P3**（记录；**未升级、未关闭、未转为 blocker、未修改**）

---

## 9. O-5 — 文档表述风险（**CLOSED，2026-09-13**）

### 9.1 原问题（Closed 记录）

| 项 | 内容 |
|---|---|
| **位置** | `B1-4_SCHEMA_DESIGN.md:106` |
| **原文** | `\| action \| text \| NN \| — \| 动作（如 read/write/share；**格式校验与取值约束见 D-B14-08**） \|` |
| **问题** | 该行以 **`read` / `write` / `share` 作为 `action` 的示例取值**。虽以"如"限定并指向 D-B14-08，但在 D-B14-08 尚 OPEN、且明令"不得自行引入 action 语义词表"的前提下，**该表述可能被误读为已隐含词表**，与 `B1-4_SCHEMA_DESIGN:186`（"**禁止**定义取值语义"）存在**表述张力** |
| **性质** | 文档表述风险（非结构冲突）；**不构成 code/migration 风险** |
| **原级别** | **P2**（文档表述一致性） |

### 9.2 修改内容（Closed 记录）

| # | 文件 | 变更 | 性质 |
|---|---|---|---|
| 1 | `B1-4_SCHEMA_DESIGN.md:106` | 示例取值 `（如 read/write/share）` → **`**opaque action identifier**（占位记法 `<action>`）：action 为**当前未冻结语义**的非空标识符；本阶段**不定义**其 vocabulary、业务语义或命名空间。格式与取值约束见 **D-B14-08（OPEN）**` | **缺陷修复**（移除语义示例） |
| 2 | `STEP1B_SEED_STRATEGY.md` §4（L104 后） | 追加**边界声明**：上列示例属**未来 `permissions` 表（P13 平台字典）** seed 草稿，**仅说明 `key` 形状**；**不构成 `resource_permissions.action` 的 vocabulary 冻结**，不得迁移 | **非规范性澄清**（不改任何决策） |

**未新增任何 semantic contract**（逐项核对）：
- ❌ 未新增 action CHECK · ❌ 未新增 action regex · ❌ 未新增 action vocabulary · ❌ 未新增 permission dictionary · ❌ 未新增 semantic namespace
- 仅**删除**示例取值并把表述改为中性占位 ⇒ 约束面**单调收缩**，不扩张。

### 9.3 为何不改变 D-B14-08 的 Human Decision

| 理由 | 说明 |
|---|---|
| 未触及候选实质 | A / B / C 三候选、`ACT-03` 条件性、以及"默认推荐 A"**均未改动** |
| 未产生新约束 | 修改不新增任何 CK/正则/词表 ⇒ **不构成方案 B 的既有实施，也不等于采纳 B** |
| 状态未变（**R4 复核**） | O-5 修复当时 `D-B14-08` 仍为 **OPEN / PROPOSED** —— 修改仅消除**误读风险**，**不代 Human 裁定**；其后由 2026-09-13 Human Decision 独立冻结为 **A**（与 O-5 无因果关系） |

| 项 | 值 |
|---|---|
| **O-5 = CLOSED（2026-09-13）** | 原问题已消除；未新增 semantic contract；随后 **`D-B14-08` 由 Human Decision 冻结为 A**（与 O-5 修复相互独立，无因果） |
| **未修改** | `B1-4_TEST_MATRIX.md` · 所有 D-B14 决策状态 |

### 9.4 §2 同步检查结果

| 位置 | 字样 | 判定 |
|---|---|---|
| `B1-4_DECISION_LOG.md:111-112` | `read`/`write`/`resource.read`（在 **Problem 描述**与 **C 越界**语境） | ✅ 合规 —— 属"**未冻结**"的说明，非取值定义 |
| `B1-4_TEST_MATRIX.md:160` | 同族词表 | ✅ 合规 —— **明令禁止**条款 |
| `B1-4_PREP_GATE_REPORT.md:197` · `B1-4_HUMAN_DECISION_FREEZE_PACKAGE.md:36` | 同族词表 | ✅ 合规 —— **禁令**表述 |
| `STEP1B_SEED_STRATEGY.md:99` | `resource.read / resource.write / resource.delete` | ✅ 合规 —— **P13 `permissions` 字典草稿**；已补**显式边界声明**（§9.2 #2） |
| `CORE_DOMAIN_MODEL.md:180` | `permissions` purpose 举例 | ✅ 合规 —— 表级自明归属（`permissions` 表，非 `resource_permissions.action`），**无需改写** |
| `ER_MODEL.md:140` | `key UK "resource.read"`（位于 `permissions { }` 块内） | ✅ 合规 —— 表级自明归属；同文件 `resource_permissions { }` 块的 `text action` **无示例值** ⇒ 无误读面 |
| `ER_MODEL.md:202-211` | `resource_permissions.action` | ✅ **无示例取值** |

**结论**：除已修复的 `SCHEMA_DESIGN:106` 外，**不存在**会让读者认为 `resource_permissions.action` 已拥有正式 vocabulary 的表述。

---

## 10. Remaining Implementation Blocking Conditions

| # | 阻塞条件 | 类别 | 状态 |
|---|---|---|---|
| ~~B-1~~ | ~~**D-B14-08** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A）** |
| ~~B-2~~ | ~~**D-B14-09** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A）** |
| ~~B-3~~ | ~~D-B14-10~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A-1）** |
| ~~B-4~~ | ~~**D-B14-12** 未裁定~~ | 设计裁定 | ✅ **CLOSED（FROZEN — A）** |
| ~~B-5~~ | ~~**O-1** 未裁定~~ | 文档裁定 | ✅ **CLOSED（O-1 = FROZEN — A：84）** |
| ~~B-6~~ | ~~**O-2** 未裁定~~ | 文档裁定 | ✅ **CLOSED（O-2 = FROZEN：双字段模型）** |
| B-7 | 冻结事实 F-1…F-12 受约束（不 seed · 0 个 G/H/I/J · 不实现授权求值 · 不启用 RLS · 不建 Domain/Tool/AI/Agent/Event/Audit 表） | 边界约束 | 受约束（**非阻塞**） |
| B-8 | 生产迁移护栏 **KEEP DEFERRED**（实施阶段禁止裸 `alembic upgrade head`） | 护栏 | defer |
| — | O-3 / O-4 = **P3**（记录）· **O-5 = CLOSED（2026-09-13，文档已修正）** | 文档 | **不构成 Implementation blocker** |

**B-1…B-6 全部 CLOSED（2026-09-13）** —— B1-4 的**设计/文档阻塞已全部解除**；剩余条件为 **B-8 迁移护栏 + FINAL PREP GATE 通过**；**IMPLEMENTATION 保持 BLOCKED（本轮不得创建 0007）**。

---

## 11. Read-only Environment State（本轮审计时刻）

```text
0001–0006           = exists（6 个 revision）
0007                = absent
head                = 0006_b1_3_bootstrap_state
formal uap          = 0 tables
B1-4 tables         = 0（resources / acl_subject_types / resource_permissions 均不存在）
Git HEAD            = 72ade9f（未变）
tags                = UAP-V0.1.0-INIT, UAP-V0.1.0-INIT-DB-VALIDATED
staged              = 0
tracked changes     = 2 行（pyproject/requirements，B1-0 遗留）
untracked           = 55
tests/              = unchanged（8 个既有文件仍为未跟踪状态）
business code       = unchanged（src/ app/ 改动 = 0）
no commit
no tag
```

**D-B14-10 冻结的 trigger**：`tg_resources_tenant_space_consistency` 在 `migrations_alembic/` 中出现 **0 处** ⇒ **仅冻结设计，尚未实现**。

---

## 12. 状态汇总

| 项 | 状态 |
|---|---|
| **D-B14-08** | **FROZEN — A** |
| **D-B14-09** | **FROZEN — A** |
| **D-B14-10** | **FROZEN — A-1** |
| **D-B14-12** | **FROZEN — A** |
| **O-1** | **FROZEN — A**（Canonical Total = 84） |
| **O-2** | **FROZEN**（双字段状态模型；双标签已消除） |
| **O-3** | **P3** |
| **O-4** | **P3** |
| **O-5** | **CLOSED**（2026-09-13 文档修正；未新增语义契约） |

```
B1-4 PREP           = READY FOR HUMAN REVIEW
B1-4 IMPLEMENTATION = BLOCKED
```

**本文件所述 6 项决策已全部由 2026-09-13 Human Decision 冻结**（`D-B14-08/09/10/12` · `O-1` · `O-2`）；**不再存在 OPEN / PROPOSED 项**（历史记录保留于各 §「原问题」表）。
