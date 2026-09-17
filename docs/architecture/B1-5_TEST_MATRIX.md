# B1-5 — Test Matrix（PREP）

Status: **PREP / DESIGN — 不写任何测试代码**（实施阶段才写）
阶段：**B1-5 = P07 Tool 域**
Revision: **R1**（首版）

> **与 B1-4 的关系**：B1-4 canonical count（**84**）**不因 B1-5 改变**。B1-5 使用**独立编号空间**（`TS`/`TF`/`TC`/`TV`/`TM`/`TSEC`/`TD`），且**不重复** B1-4 已完成的测试。

---

## 0. 状态模型与计数口径

### 0.1 双字段状态模型（沿用 B1-4 的 O-2 = FROZEN）

| 字段 | 规则 |
|---|---|
| `Current Status` | **每条测试只能有一个**：`【B1-5】` / `【后续】` / `【待裁定】` |
| `Post-Approval Level` | 仅当"当前待裁定、批准后归属某阶段"时填写；已批准或无需批准填 `—` |

**禁止**同一 Status 字段出现两个 `【…】`。

### 0.2 Canonical 计数口径

| 项 | 值 |
|---|---|
| B1-5 Canonical Total（本版） | **39** = 基础六类 **38** + §7 decision-dependent 表格行 **1** |
| 条件项 | **无**（B1-5 首版未引入非表格行条件测试） |
| §8 登记项（后续阶段） | **6 行**，**不计入** canonical，**不参与**三分状态统计 |

> **口径先例**：本计数沿用 B1-4 的 **O-1 = FROZEN — A**（Canonical Total = 正式表格行数）的**同一规则**。
> 该沿用**需 Human 确认** → **D-B15-07**。**本文件不自行冻结。**

---

## 1. Schema Tests（8）

| ID | 测试内容 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TS1 | `tools` / `tool_versions` / `tool_permissions` 三表存在 | 存在 | 【B1-5】 | — |
| TS2 | 业务表数 17 → **20**；物理表数 18 → **21** | 计数一致 | 【B1-5】 | — |
| TS3 | `tools` 列集合与 NN/NULL 与冻结定义一致（15 列） | 逐列断言 | 【B1-5】 | — |
| TS4 | `tool_versions` 列集合（12 列）· **无 `updated_at`** | 逐列断言 | 【B1-5】 | — |
| TS5 | `tool_permissions` 列集合（7 列）· **无 `updated_at`** | 逐列断言 | 【B1-5】 | — |
| TS6 | PK **×3**（各表 `id`，`uuid`，default `uap_uuid_v7()`） | 计数 + 默认值 | 【B1-5】 | — |
| TS7 | 时间列精度统一 `timestamptz(3)` | 类型断言 | 【B1-5】 | — |
| TS8 | **不存在** `tool_executions` / `agents*` / `ai_*` / `events` / `audit_logs` / `groups` | 集合断言 | 【B1-5】 | — |

---

## 2. FK / Delete Rule Tests（4）

| ID | 测试内容 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TF1 | 删 `tools` 行 → `tool_versions` 随行删除（CASCADE） | 级联生效 | 【B1-5】 | — |
| TF2 | 删 `tools` 行 → `tool_permissions` 随行删除（CASCADE） | 级联生效 | 【B1-5】 | — |
| TF3 | 删 `tool_versions` 行 → 引用它的 `tool_permissions` 随行删除（CASCADE） | 级联生效 | 【B1-5】 | — |
| TF4 | 删 `permissions` 行 → 引用它的 `tool_permissions` 随行删除（CASCADE） | 级联生效 | 【B1-5】 | — |

**FK 计数断言**：`pg_constraint` 中 B1-5 三表 FK = **5**（含 `tools.tenant_id`，见 TD-01）

---

## 3. Constraint Tests（9）

| ID | 测试内容 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TC1 | `risk_level` 非法值（`'low'` / `'UNKNOWN'`）→ 拒绝 | 拒绝 | 【B1-5】 | — |
| TC2 | `timeout_ms` 越界（`99` / `600001`）→ 拒绝；边界 `100`/`600000` → 允许 | 拒绝/允许 | 【B1-5】 | — |
| TC3 | `idempotency_mode` 非法值 → 拒绝 | 拒绝 | 【B1-5】 | — |
| TC4 | `audit_policy` 非法值 → 拒绝 | 拒绝 | 【B1-5】 | — |
| TC5 | `tool_permissions.effect` 非法值 → 拒绝；`allow`/`deny` → 允许 | 拒绝/允许 | 【B1-5】 | — |
| TC6 | **平台级 key 唯一**：两行 `tenant_id IS NULL` 且 `lower(key)` 相同 → 拒绝 | 拒绝 | 【B1-5】 | — |
| TC7 | **租户级 key 唯一**：同租户同 `lower(key)` → 拒绝；**不同租户同 key → 允许** | 拒绝/允许 | 【B1-5】 | — |
| TC8 | **平台级与租户级互不冲突**：`tenant_id IS NULL` 与 `tenant_id = X` 可同 `key` | 允许 | 【B1-5】 | — |
| TC9 | `uq_tool_versions (tool_id, version)` 重复 → 拒绝 | 拒绝 | 【B1-5】 | — |

**补充断言（并入 TC9 执行）**：`uq_tool_perm` 为**表达式唯一索引**（`(tool_id, COALESCE(version_id,'<nil>'), permission_id)`）：`version_id IS NULL` 的两行同 `(tool_id, permission_id)` → 拒绝；一行 NULL 一行非 NULL → 允许。
**CK 计数断言**：`pg_constraint` 中 B1-5 三表 CK = **5**

---

## 4. Version Immutability Tests（4）

| ID | 测试内容 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TV1 | `status='published'` 行 **UPDATE** → 拒绝（RAISE，含专属消息） | 拒绝 | 【B1-5】 | — |
| TV2 | `status='published'` 行 **DELETE** → 拒绝（RAISE） | 拒绝 | 【B1-5】 | — |
| TV3 | 非 published（如 `draft`）行 UPDATE/DELETE → 允许（选择性强制） | 允许 | 【B1-5】 | — |
| TV4 | **trigger 是唯一施加者**：DISABLE/ENABLE A/B 对照证明（排除 CHECK/FK/UQ 归因） | A/B 对照 | 【B1-5】 | — |

> **TV4 方法论沿用 B1-4 教训**：BEFORE trigger 先于 CHECK 执行；要证明"某 trigger 是拒绝者"必须做 DISABLE/ENABLE A/B 对照 + 断言其**专属错误消息**。仅凭"被拒"无法归因。

---

## 5. Migration Tests（8）

| ID | 测试内容 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TM1 | `upgrade 0007 → 0008` PASS | PASS | 【B1-5】 | — |
| TM2 | `downgrade 0008 → 0007` PASS | PASS | 【B1-5】 | — |
| TM3 | Round-trip（0007→0008→0007→0008）对象集一致 | PASS | 【B1-5】 | — |
| TM4 | downgrade 后**无残留**：B1-5 表 / trigger / function / index = 0 | 0 残留 | 【B1-5】 | — |
| TM5 | `set_updated_at()` **唯一实例**（未被重建） | 计数 = 1 | 【B1-5】 | — |
| TM6 | `uap_uuid_v7()` 完好（未被破坏） | 存在 | 【B1-5】 | — |
| TM7 | 既有 B1-0~B1-4 对象未被破坏（`resources` 三表 + 3 trigger + 2 function 仍在） | 断言 | 【B1-5】 | — |
| TM8 | `head` = `0008_b1_5_tool_registry` | 断言 | 【B1-5】 | — |

---

## 6. Security / Architecture Tests（5）

| ID | 测试内容 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TSEC1 | 无 RLS 语句（`row level security` / `create policy`）· 三表 `relrowsecurity=false` | 0 | 【B1-5】 | — |
| TSEC2 | **Core→Domain = 0**（`core/*` 不 import `domains/*` / `agent` / `intelligence`） | 0 | 【B1-5】 | — |
| TSEC3 | **零 seed**：migration 内 `INSERT INTO` = 0；三表 rows = 0 | 0 | 【B1-5】 | — |
| TSEC4 | **G/H/I/J = 0**（`tg_acl_subject_exists` / `tg_acl_user_hard_delete` / `tg_acl_role_delete_block` / `tg_agent_acl_expire` 均不存在） | 0 | 【B1-5】 | — |
| TSEC5 | 无未授权建表（`agents` / `ai_*` / `events` / `audit_logs` / `groups`）+ 无行业词 | 0 | 【B1-5】 | — |

---

## 7. Decision-Dependent Tests（1）

| ID | 测试内容 | 依赖决策 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TD-01 | **`tools.tenant_id` 隔离行为**（**D-B15-02 = FROZEN — A**：`→ tenants.id ON DELETE RESTRICT`）：<br>· 指向不存在租户 → **拒绝**（FK）<br>· 删除被引用租户 → **拒绝**（RESTRICT）<br>· `tenant_id IS NULL`（平台级）→ 允许 | **D-B15-02（✅ FROZEN — A）** | 【B1-5】 | — |

> **D-B15-02 已于 2026-09-14 冻结为 A** ⇒ TD-01 由 `【待裁定】` 升为 **`【B1-5】` / `Post-Approval Level = —`**（**行数不变，canonical 仍为 39**）。

---

## 8. 后续阶段登记（承接，不在 B1-5 执行）

**不计入 canonical total（39）· 不参与三分状态统计**

| ID | 内容 | 归属 |
|---|---|---|
| TDF1 | `tool_executions` 幂等锚点 `uq_tool_exec_idem`（部分唯一） | **P09** |
| TDF2 | `tool_executions` 状态/attempts/duration CK | **P09** |
| TDF3 | `agent_permissions.tool_id → tools.id` FK 行为 | **P09** |
| TDF4 | `tool_executions.agent_id → agents.id` 行为 | **P09** |
| TDF5 | Tool 高危操作写 `audit_logs` | **P10** |
| TDF6 | Tool 版本 `deprecate` / `revoke` 状态迁移语义 | 后续 |

> **（已关闭）** **D-B15-04 / D-B15-05 / D-B15-08 均已冻结为 A（不新增约束）** ⇒ **不产生**新的条件行，
> canonical **保持 39**。以下为历史说明：若未来裁定新增约束，需另案增列条件行（不得自行变动 39）。
>
> 原说明：若 **D-B15-04**（`status` 词表）/
> **D-B15-05**（`key` 格式）/ **D-B15-08**（快照列 CK）裁定为"新增约束"，则需在 §7 增列对应的
> 条件行，**届时 canonical 才随之调整**（须另案裁定，**不得自行变动 39** —— D-B15-07 = FROZEN — A）。

---

## 9. 优先级

| 级别 | 测试 | 说明 |
|---|---|---|
| **P0** | TS1–TS8 · TF1–TF4 · TC1–TC9 · TV1–TV3 · TM1–TM4 · TM7–TM8 · TSEC1–TSEC5 | 缺失会使交付物不可用或产生未授权状态 |
| **P1** | TV4 · TM5 · TM6 | 完整性 / 可运维性 |
| **P0** | TD-01（**D-B15-02 已冻结，可执行**） | FK/隔离行为 |
| **P3** | §8 登记项 | 后续阶段 |

**预期可执行性**：B1-5 **无** B1-4 式的"空窗口"限制 —— `tools` 无 protect trigger，测试可直接构造夹具 ⇒ **§1–§7 全部测试（含 TD-01）在 B1-5 阶段可执行**。

---

## 10. 计数汇总

**口径（D-B15-06 = FROZEN — A）**：UQ 统计区分 constraint-form（**1**：`uq_tool_versions`）与 index-form（**3**：`uq_tools_platform` / `uq_tools_tenant` / `uq_tool_perm`）；**表达式唯一性不计入 UNIQUE CONSTRAINT**。

```
Schema Tests        = 8    (TS1–TS8)
FK/Delete Tests     = 4    (TF1–TF4)
Constraint Tests    = 9    (TC1–TC9)
Immutability Tests  = 4    (TV1–TV4)
Migration Tests     = 8    (TM1–TM8)
Security Tests      = 5    (TSEC1–TSEC5)
────────────────────────────
基础六类            = 38
§7 decision-dependent = 1  (TD-01)
────────────────────────────
Canonical Total     = 39
（§8 登记项 6 行不计入）

三分统计（唯一状态计）
  【B1-5】  = 38
  【待裁定】= 0（TD-01 已随 D-B15-02 冻结转为【B1-5】）
  【后续】  = 0
```

---

## 11. Implementation tests written = 0（本阶段）
