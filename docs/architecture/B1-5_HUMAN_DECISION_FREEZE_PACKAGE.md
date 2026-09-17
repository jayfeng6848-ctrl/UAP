# B1-5 — Human Decision Freeze Package

Status: **FINAL HUMAN DECISION FREEZE（2026-09-14）** —— **9 项全部 FROZEN — A**
阶段：**B1-5 = P07 Tool 域**（D-B15-01 = FROZEN — A）
父基线：`B1-4 Commit = e9766fbe8b13294d8a6cdfbff640f14d8e57a68f` · `Tag = UAP-V0.1.4-B1-4-RESOURCE-ACL`

> 本文件区分四态：**FROZEN** / **OPEN** / **PROPOSED** / **DEFERRED**。未被 Human 裁定的项**一律保持 OPEN**。

---

## 1. Baseline

```
HEAD           = e9766fb（e9766fbe8b13294d8a6cdfbff640f14d8e57a68f）
Tag            = UAP-V0.1.4-B1-4-RESOURCE-ACL
branch         = main
migration      = 0001–0007（head = 0007_b1_4_resource_acl）
formal uap     = 0 tables
uap_test       = 2 tables（既有）
Git staged     = 0
Architecture Guard = 9 passed
Core→Domain    = 0
```

---

## 2. B1-5 ↔ P07 Evidence

| 项 | 内容 |
|---|---|
| 字面 `B1-5` 定义 | **NOT FOUND**（全库 0 命中；项目无 roadmap 文档） |
| 实质范围来源 | 冻结 phase plan（`STEP1B_SCHEMA_DEPENDENCY.md` §5） |
| 关键原文 | `:167` **P06 = Resource / ACL**（`resources → acl_subject_types → resource_permissions`）<br>`:168` **P07 = Tool**（`tools → tool_versions → tool_permissions`）<br>`B0_GATE_REPORT:45` phase 拓扑 `… P06 resource/ACL → P07 tool → P08 AI → P09 agent …`<br>`B1-4_DECISION_LOG:14`「**P06（= B1-4）**」<br>`B1-4_SCOPE:42`「Tool / AI / Agent 域 \| **P07** / P08 / P09」<br>`B1-4_DEPENDENCY:130`「**P07 Tool**」 |
| 实测对账 | P01–P06 **全部已建**（17 张业务表，无一缺失）⇒ 下一个未执行 phase = **P07** |
| 映射注意 | `B1-x` 与 `P0x` **非严格 1:1**（B1-1=P01+P02 · B1-2=P03+P05 · B1-3=P04(+hardening)） |
| **Human Decision** | **D-B15-01 = FROZEN — A**：`B1-5 = P07 Tool`；**不得据此改变历史 B0 的 phase 定义** |

---

## 3. Human Decisions（汇总）

| ID | 主题 | 状态 | 裁定内容 |
|---|---|---|---|
| **D-B15-01** | B1-5 编号 ↔ P07 绑定 | ✅ **FROZEN — A** | `B1-5 = P07 Tool` |
| **D-B15-02** | `tools.tenant_id` FK + 删除规则 | ✅ **FROZEN — A** | `tenant_id NULL → tenants.id` **`ON DELETE RESTRICT`**；`NULL` = platform-level；**不得**改 NOT NULL / **不得** CASCADE |
| **D-B15-03** | immutable trigger 命名 | ✅ **FROZEN — A** | 采用 **`tg_version_immutable`**（= PREP Options 的 B）；**PREP 推荐已被覆盖** |
| **D-B15-04** | `tool_versions.status` 取值域 | ✅ **FROZEN — A** | **`status CHECK = 0`**（不建枚举）；仅冻结 **`published`** 作为 immutable **语义锚点**；**不得**自创 draft/disabled/archived… 等词 |
| **D-B15-05** | `tools.key` 格式 CK | ✅ **FROZEN — A** | **不新增 regex / format CHECK**；保持 opaque application identifier |
| **D-B15-06** | UQ / Index 计数口径 | ✅ **FROZEN — A** | `UNIQUE CONSTRAINT = 1` · `UNIQUE INDEX = 3`；表达式唯一性**不计入** UNIQUE CONSTRAINT |
| **D-B15-07** | canonical 计数口径沿用 | ✅ **FROZEN — A** | 沿用 O-1-A 原则；独立编号空间；`Base 38` + `Decision 1` = **`Canonical 39`**；`Registration 6` 不计入 |
| **D-B15-08** | `tool_versions` 快照列 CK | ✅ **FROZEN — A** | **不新增 snapshot value-domain CHECK**；`tool_versions` 保持**零 CK** |
| **D-B15-09** | `handler_ref` 语义边界 | ✅ **FROZEN — A** | 仅存文本引用；**不** resolve / load / execute / plugin registration / runtime discovery |

```
FROZEN = 9（01 / 02 / 03 / 04 / 05 / 06 / 07 / 08 / 09）
OPEN   = 0 · BLOCKING = 0
```

---

## 4. Decision Evidence

### 4.1 D-B15-02 — `tools.tenant_id` 的 B0 原文冲突（**唯一阻塞级架构 Decision**）

| # | 来源 | 精确原文 | 口径 |
|---|---|---|---|
| **A** | `ER_MODEL.md:276` | `uuid tenant_id FK "nullable = platform"` | **支持 FK**（全库**唯一**明确标注）；但文件头部声明「图中只画主键、外键与关键字段」，属 ER 图示 |
| **B** | `SCHEMA_DEPENDENCY.md:51` | 表格为 `\| 表 \| 依赖 \| FK \| root \|`；`tools` 行 **FK 列 = `—`**，依赖列注「tenants（NULL=平台内置，**无实际 FK 强制**）」 | **不支持 FK**；对照 `resources` 行 FK 列写 `tenant_id → tenants.id RESTRICT`（P2-03） |
| **C** | `CONSTRAINT_MATRIX.md:215-222` | `tools` 段**完全没有 FK 行**（仅 PK/UQ/CK/NN/NULL） | **未列 FK** |
| **D** | `CORE_DOMAIN_MODEL.md:322` | `FK \| tenant_id NULL（NULL = 平台内置）` | **表述不完整**：无 → 目标、无删除规则（对照 `resources` 写全） |
| **E** | `CORE §11.1` | CASCADE 白名单**不含** `tenants → tools`；"明确禁止 CASCADE"含 `tenants → spaces` / `tenants → resources` | 若加 FK ⇒ 按"业务实体一律 RESTRICT"应为 **RESTRICT** |
| **F** | `SCHEMA_DEPENDENCY §1.4`（对照） | `tool_executions` 同把 `tenants` 列入依赖列，FK 列**无** `tenant_id → tenants.id` | 与 tools **同模式** |

**事实陈述（不含裁定）**：不支持或未列 FK 的来源 = **3**；支持 = **1**（ER_MODEL）。
**语义确认**：`tenant_id IS NULL` = **平台内置 Tool**（三方一致）；非 NULL = 租户私有。
**Tenant 删除的预期行为**：**未在任何冻结文档中规定**（若加 FK，按 §11.1 应为 RESTRICT；`ER_MODEL` 未给规则）。

**候选（未裁定）**
```
A. tools.tenant_id → tenants.id  ON DELETE RESTRICT
B. 不建立实际 FK（应用层保证存在性）
C. 其他更符合既有冻结架构的方案（须由 Human 明示）
```

**Human Decision（2026-09-14）= A —— FROZEN**：`tools.tenant_id NULL → tenants.id ON DELETE RESTRICT`。
**B0 同步已执行（B-5 授权范围）**：`SCHEMA_DEPENDENCY:51` · `CONSTRAINT_MATRIX` tools 段（新增 FK 行）· `CORE_DOMAIN_MODEL:322` · `ER_MODEL:276` —— 四处**当前有效口径**已统一。

### 4.2 D-B15-04 — `tool_versions.status` 原文证据

| # | 来源 | 内容 |
|---|---|---|
| ① | `CONSTRAINT_MATRIX.md:225-233` | `tool_versions` 段仅 PK / FK / UQ / NN / 不变性 —— **无 CK 行** |
| ② | `CORE_DOMAIN_MODEL.md:334` | fields 列出 `status`，但该表 § **无 CK**（对照：`tools:325` 有 · `ai_routes:291` 有 · `audit_logs:442` 有） |
| ③ | `STEP1A_DESIGN_REPORT.md:67` | 仅「published 后**不可变**」，**未给取值域** |
| ④ | 全库 `status IN (...)` 词表先例 | **12 处**（users / identities / credentials / devices / sessions / tenants / spaces / memberships / …）—— **均无 tool_versions** |
| ⑤ | `CORE_DOMAIN_MODEL.md:302` · `STEP1B_CONSTRAINT_MATRIX.md:281` | **⚠️ 纠正（2026-09-14 复核）：`agent_versions` 实为有 CK** —— `status IN ('draft','published','deprecated','revoked')`。**先前记录的「同族两表一致缺失」属误判**；真实情况是 **`tool_versions` 为该家族中唯一缺失者**，同族先例词表存在 |
| ⑥ | `SCHEMA_DEPENDENCY:240` | `tg_version_immutable`（agent_versions/tool_versions **published** 禁改删）—— 锚点为字面 `'published'` |

**结论（PREP，已更正）**：现有资料**未直接给出 `tool_versions` 词表**；但**同族 `agent_versions` 存在先例词表** `('draft','published','deprecated','revoked')`。
**Human Decision（2026-09-14）= A —— FROZEN**：**`status CHECK = 0`**（不建枚举）；仅冻结 **`published`** 作为 immutable lifecycle 的**语义锚点**。**边界**：不创造 draft/active/disabled/archived/deprecated/released 等词；immutability 由 `tg_version_immutable` 承担。
**残留说明（如实记录）**：`published` 之外的字面未被 DB 约束；不变式**仅对字面 `'published'` 生效** —— 这是 Human 明确选择的「最小约束」策略。
**⚠️ 裁定后补充发现（供复核）**：同族 `agent_versions` **有** status CK（4 值），故实施后 **`tool_versions` 与 `agent_versions` 在 status 约束上不一致**。若需对齐，须**另案批准**补 `ck_tool_versions_status`（新增约束）。**本轮未自行补，未改动裁定。**

### 4.3 D-B15-05 — `tools.key` 规范证据

| # | 来源 | 内容 |
|---|---|---|
| ① | `CONSTRAINT_MATRIX:215-222` | `tools` CK 仅 risk_level / timeout_ms / idempotency_mode / audit_policy —— **无 key 格式 CK** |
| ② | `CORE_DOMAIN_MODEL:324` | UQ 仅 `lower(key)` 两类部分唯一 |
| ③ | **有**格式正则先例 | `permissions.key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$'`（`CONSTRAINT_MATRIX:120`）· `acl_subject_types.key ~ '^[a-z][a-z0-9_]{1,31}$'` |
| ④ | **无**格式正则先例 | `spaces.key`（仅 `uq_spaces_key on (tenant_id, lower(key))`）· `tenants.slug`（仅 UQ）· **`tools.key`** |

**结论（PREP）**：B0 中 registry key 的格式约束**并不统一**，**无统一规范覆盖 Tool** —— 无统一规范覆盖 Tool。
**Human Decision（2026-09-14）= A —— FROZEN**：`tools.key` **不新增 regex / format CHECK**，保持 **opaque application identifier**。

**⚠️ 指令引用项核对**：用户指令 §六 引用 **`D-B14-13`** 作为 key 规范来源 —— 经核对，
`D-B14-13 = 「B1-4 的 seed 与 trigger 交付清单（R1 重新裁定）」`（`B1-4_DECISION_LOG:175`），
**与 key 规范无关**（疑为误引）。key 相关论述实为 **D-B14-08** 与 `permissions.key` 正则。

### 4.4 D-B15-08 — `tool_versions` 约束证据

| # | 来源 | 内容 |
|---|---|---|
| ① | `CONSTRAINT_MATRIX.md:225-233` | `tool_versions` 段 **无 CK 行** ✅ 确认 |
| ② | `CORE_DOMAIN_MODEL.md:334` | fields 含 `risk_level`/`timeout_ms`，该表 § **无 CK** |
| ③ | 对照 | `tools:325` 有 CK · `audit_logs:442` 有 CK · `ai_routes:291` 有 CK |
| ④ | **P08/P09 依赖检查** | 全库**无**任何文档声明 P08/P09 依赖 `tool_versions.risk_level`/`timeout_ms` 的**取值域**；`tool_executions.risk_level` 位于 NULL 列（`:354`）且**无 CK** |
| ⑤ | 结构保护 | `tg_version_immutable` 只保证 published 行**不可改**，**不校验取值** |

**结论（PREP）**：现有资料**未规定**该表 CK。
**Human Decision（2026-09-14）= A —— FROZEN**：**不新增 snapshot value-domain CHECK** —— `risk_level` / `timeout_ms` / `idempotency_mode` / `audit_policy` 均不新增 CK（`tool_versions` 保持零 CK）。

### 4.5 D-B15-03 — 命名命中检查（已完成）

```
tg_version_immutable       : 1 处（SCHEMA_DEPENDENCY:240，B0）
tg_tool_versions_immutable : 1 处（TRIGGER_INVENTORY:164，B0）+ B1-5 PREP 8 处（已同步为前者）
tg_agent_versions_immutable: 1 处（同上 inventory 行）
已实现对象依赖该名         : 0（0001–0007 中 0 命中；均属 DESIGN 阶段命名）
```
**⇒ 无"既有依赖"反证 ⇒ FROZEN — A（采用 `tg_version_immutable`）**

**⚠️ 残留项（如实报告）**：`TRIGGER_INVENTORY:164` 用**逐表命名**，与冻结名不一致；且既有 3 个已实现 trigger
均为逐表命名（`tg_resources_set_updated_at` / `tg_resources_tenant_space_consistency` / `tg_acl_subject_types_protect`）。
**该 B0 文档需同步修订（属另案，须 Human 授权）。本轮未改。**

---

## 5. Frozen Facts

| # | 事实 | 依据 |
|---|---|---|
| F-1 | `B1-5 = P07 Tool 域` | D-B15-01 = FROZEN — A |
| F-2 | B1-5 交付 **3 表**：`tools` / `tool_versions` / `tool_permissions` | `SCHEMA_DEPENDENCY:168` |
| F-3 | **`tool_executions` 属 P09**，不在 B1-5 | `SCHEMA_DEPENDENCY:170` + §5 调整说明② |
| F-4 | **G / H / I / J** 仍 **P09 后**，B1-5 = 0 | `TRIGGER_INVENTORY:163-166` |
| F-5 | **P00–P10 无 seed；P13 才有** ⇒ B1-5 **零 seed** | `SCHEMA_DEPENDENCY:193` · `SEED_STRATEGY` §1 清单不含 Tool 域 |
| F-6 | B1-5 **API = 0 · Socket = 0** | `B1-5_API_DESIGN.md` |
| F-7 | **不启用 RLS** | B1-4 同口径延续 |
| F-8 | B1-5 trigger = **2**（`tg_tools_set_updated_at` · `tg_version_immutable`）；function 新增 **1** | D-B15-03 = FROZEN — A |
| F-9 | `tools → tool_versions` / `tools → tool_permissions` / `tool_permissions.version_id` / `permission_id` = **CASCADE**（已在 `CORE §11.1` 白名单内） | `CONSTRAINT_MATRIX:230/240` |
| F-10 | `tool_permissions.effect ∈ ('allow','deny')` = **已冻结**（非新增） | `CONSTRAINT_MATRIX:242` |
| F-11 | `tool_permissions.conditions` = **storage-only** | 与 B1-4 `resource_permissions.conditions` 同口径 |
| F-12 | `handler_ref` = **仅文本引用**，不引入解析/加载/注册机制 | D-B15-09 = FROZEN — A |
| F-13 | `tools` 生命周期 = **disable**（`enabled=false`），版本不可删 | `CORE:958-959` |
| F-14 | 无 forward dependency · 无循环 FK · Core→Domain = 0 | `B1-5_DEPENDENCY.md` |
| F-15 | **Canonical Test = 39**（Base 38 + Decision 1）；Registration 6 不计入 | D-B15-07 = FROZEN — A |
| F-16 | UQ 计数区分 constraint-form（1）/ index-form（3） | D-B15-06 = FROZEN — A |

---

## 6. Open Decisions

```
OPEN Decision = 0
```

全部 9 项已由 2026-09-14 Human Decision 冻结为 **A**（详见 §3 与 `B1-5_DECISION_LOG.md`）。

**未裁定项曾存在期间的纪律**：`B1-5_SCHEMA_DESIGN.md` 对四项**曾标注为待裁定**，**从未**把它们伪装成冻结值；
裁定后已同步为正式口径（`tools.tenant_id` FK 行 · `status CK = 0` · `key` 无 regex · 快照零 CK）。

---

## 7. Implementation Blockers

```
B-1  ✅ CLOSED  D-B15-02 = FROZEN — A（含 B0 四处同步）
B-2  ✅ CLOSED  D-B15-04 = FROZEN — A（status CK = 0）
B-3  ✅ CLOSED  D-B15-05 = FROZEN — A（key 无 regex）
B-4  ✅ CLOSED  D-B15-08 = FROZEN — A（快照零 CK）
B-5  ✅ AUTHORIZED & DONE  B0 命名/口径同步（TRIGGER_INVENTORY 条目 K + 汇总表；ER / CORE / DEPENDENCY / CONSTRAINT 的 tools FK）
B-6  ⚠️ 既有：P3-3 生产迁移机械护栏（KEEP DEFERRED，非本轮范围）
B-7  ✅ 边界受约束：零 seed · 不启用 RLS · 不实现授权求值 · G/H/I/J = 0 · 不含 tool_executions
```

**结论**：设计层阻塞 **全部解除**；剩余条件为 **FINAL PREP GATE + 显式实施授权**。

---

## 8. Scope Boundary

```
IN :  tools · tool_versions · tool_permissions
       + PK×3 · FK×(4 或 5) · UQ 4(1 constraint + 3 index) · CK×5 · trigger×2 · function×1
       + migration 0008（NOT CREATED）

OUT:  tool_executions(P09) · agents/agent_versions/agent_permissions(P09)
       ai_*(P08) · events/audit_logs(P10) · resource_relations(P2 可选)
       G/H/I/J(P09 后) · Authorization Layer · Role/Deny Resolution
       API(0) · Socket(0) · RLS(0) · Seed(P13)
```

---

## 9. Security Boundary

| 维度 | 结论 |
|---|---|
| Tenant isolation | **PASS** —— D-B15-02 = FROZEN — A：`tenant_id NULL → tenants.id RESTRICT`，租户级 Tool 无法指向不存在的租户，删租户被阻塞；平台级 `NULL` 语义保留 |
| Space isolation | **N/A**（Tool 无 `space_id`） |
| Role / Permission | PASS（`permission_id` FK 到 P04 字典；**不做判定**） |
| Resource ACL | PASS（不写 `resource_permissions`；`acl_subject_types` 仍 0 rows） |
| Delete semantics | PASS（4 条 CASCADE 全在 `CORE §11.1` 白名单） |
| Privilege escalation | PASS（本阶段无判定逻辑） |
| RLS | PASS（未启用） |
| Sensitive data | WARN（`input_schema`/`output_schema`/`retry_policy`/`conditions` 为 JSONB 配置位；**不得存放凭据**，DB 无强制） |
| Seed / bootstrap | PASS（零 seed） |

**边界声明（强制）**：`tg_version_immutable` **仅**强制结构性不变式；**不做** authorization evaluation / role resolution / deny resolution / Domain authorization。

---

## 10. Test Matrix Accounting

```
Schema 8 · FK/Delete 4 · Constraint 9 · Immutability 4 · Migration 8 · Security 5
──────────────────────────────────
Base                = 38
Decision-dependent  = 1   （TD-01，依赖 D-B15-02）
──────────────────────────────────
Canonical Total     = 39      ← D-B15-07 = FROZEN — A
Registration        = 6       （§8，不计入）
Implementation tests written = 0
```
**口径声明**：UQ 统计须区分 constraint-form 与 index-form（D-B15-06 = FROZEN — A）。
**与 B1-4 无关**：B1-4 canonical（**84**）不因 B1-5 改变。
**待裁定条件行**：若 D-B15-04 / 05 / 08 裁定为"新增约束"，需另案增列条件行并**同步调整 canonical**（**不得自行变动 39**）。

---

## 11. Migration Boundary

```
预计 revision  : 0008_b1_5_tool_registry（命名待定）
down_revision  : 0007_b1_4_resource_acl
单事务         : 是
upgrade 顺序   : tools → tool_versions → tool_permissions → constraints/indexes(内联) → function → triggers
downgrade 顺序 : triggers → function → indexes → tables（逆序）
本轮           : NOT CREATED · NO DDL · NO DML
```

---

## 12. Production Safety

```
formal uap                = 0 tables（本轮未变更）
formal alembic_version    = absent
production migration      = 未执行
0001–0007                 = 未修改
env.py                    = 未修改
B1-4 sealed 文件           = 未修改
业务代码 / 测试实现        = 未修改
commit / tag              = NOT CREATED
```

---

## 13. Gate

```
D-B15-01 … D-B15-09          = ALL FROZEN — A
OPEN Decision = 0 · BLOCKING Decision = 0

B1-5 PREP                    = COMPLETE
B1-5 HUMAN DECISION FREEZE   = COMPLETE
B1-5 IMPLEMENTATION          = READY BUT NOT STARTED
B1-5 migration 0008          = NOT CREATED
