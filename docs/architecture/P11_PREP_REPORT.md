# P11 — TRIGGERS / CROSS-TABLE CONSTRAINTS · PREP REPORT

> **状态（先读这个）**
>
> ```text
> 本文档 = READ-ONLY PREP / DISCOVERY / DESIGN / EVIDENCE COLLECTION 产物
> 本文档 ≠ FROZEN ≠ APPROVED ≠ IMPLEMENTED ≠ AUTHORIZED
> ```
>
> 本轮（`UAP P11 PREP — TRIGGERS / CROSS-TABLE CONSTRAINTS · READ-ONLY DESIGN / PREPARATION GATE`）
> **仅允许** READ-ONLY / DISCOVERY / DESIGN / EVIDENCE COLLECTION / PREP / DECISION PACKAGE PREPARATION。
>
> **本轮实测零实施**：`DDL = 0` · `DML = 0` · `CREATE/ALTER/DROP TRIGGER = 0` · `CREATE/ALTER FUNCTION = 0` ·
> `migration 创建/修改 = 0` · `alembic upgrade/downgrade = 0` · `runtime/API/worker 实施 = 0` ·
> `test 代码修改 = 0` · `应用代码修改 = 0` · `配置修改 = 0` · `commit = 0` · `tag = 0` · `push = 0` ·
> **既有文档修改 = 0**（本轮仅新增 3 份 P11 文档）。
>
> **全部设计为 PROPOSED**；`OQ-P11-01`…`OQ-P11-14` 的 `HUMAN DECISION` **一律 `PENDING`**。

---

## 1. Executive Summary

P11 = **Triggers / Cross-table Constraints**（`D-PLAT-09` 路线 A 的第二阶段）。
**实测结论（本轮最重发现）**：

```text
A–M 清单中的 13 项触发器【已在 0003–0011 内联实施】；
唯一未实施的组 = 【G / H / I / J】—— 即 P11 的实质范围；
L（tg_audit_immutable）= 【P10-owned】（D-P10-11）⇒ P11 不得触碰；
M（events 无 trigger）= 无对象；
另有 【6 项已实现触发器不在冻结 A–M 清单内】（清单缺口，见 §4.3）。
```

即：**P11 的实际交付面 = `tg_acl_subject_exists`（G）· `tg_acl_user_hard_delete`（H）·
`tg_acl_role_delete_block`（I）· `tg_agent_acl_expire`（J）`**，与 `D-PLAT-10`「P11 纳入 G/H/I/J」**逐字一致**。

三条需要 Human 注意的发现（全部 **REPORT-ONLY**，未修改任何文件）：

1. **清单缺口（实测）**：6 项已实现触发器（`tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` ·
   `tg_platform_state_guard` · `tg_pm_bootstrap_gate` · `tg_agents_tenant_space_consistency`）**不在**冻结的
   A–M 清单内（该清单成文于 `0005`/`0006`/`0011` 之前）⇒ **登记为清单缺口，不并入 A–M**（遵指令 §4：DO NOT MERGE）。
2. **H/I 的相位理由不充分（既有已登记结论，非本轮新发现）**：`B1-4_DEPENDENCY.md:74-76` 原文级结论载明
   H/I 的 `dependency` 字段**不含 `agents`**，"P09 后"是**显式阶段冻结**而非依赖推导；
   `TRIGGER_INVENTORY:177` 以"依赖 agents"概括四项**对 H/I 理由不充分** ⇒ 属**冻结文档修订事项**，**本 PREP 不自行裁定**。
3. **既有 P3 文档不一致（延续登记）**：`CORE_DOMAIN_MODEL.md:263`「归档 role 时**由 trigger 写 audit**」
   与触发器本体论「**trigger 不写 audit**」（`B1-4_DEPENDENCY.md:103` 记为 P3）冲突 ⇒ **P11 不得把它变成新 trigger**，
   该不一致须由 Human 裁定归属（授权层 / P10 审计面 / 文档修订）。

**零实施**：本轮无任何 DDL / DML / trigger / function / migration / code / test / config 变更。

---

## 2. Baseline（实测 · 2026-09-25）

| 项 | 值 | 证据 |
|---|---|---|
| HEAD | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` | 命令 |
| tag | `UAP-V0.1.8-AUTHORIZATION` · tags = **8** | 命令 |
| remote | **none**（从未 push） | 命令 |
| `alembic heads` | **`0012_authz_enforcement (head)`**（单头） | 命令 |
| `0013+` | **0** | 命令 |
| `0010` sha256 | `6d9907237f80e9da4acdff86c8da371af721fec3dccbe00d7e1c3035ab1b0322`（未变） | 命令 |
| `0011` sha256 | `cdaf8383630335db92cfe54f12e6b65385ea1b4273e86653026afc80893f9f57`（未变） | 命令 |
| `0012` sha256 | `5ecd1ef30b403fb432a497cb9cf70d32c6c49708d341ab6ad029c19b22b3171a`（未变） | 命令 |
| `P10 DECISION FREEZE` | **PASSED**（`D-P10-01..18` FROZEN） | PDL 附录 G |
| `D-PLAT-09` | `P10 → P11 → P12 → P13 → Runtime`（**未 supersede**） | PDL |

---

## 3. P11 权威定义与边界

### 3.1 冻结定义（原文）

| 来源 | 原文 |
|---|---|
| `STEP1B_SCHEMA_DEPENDENCY.md:172` | **P11** \| **Triggers / 跨表约束** \| 见 `STEP1B_TRIGGER_INVENTORY.md`；**必须在 seed 前全部就位** |
| `D-PLAT-10`（FROZEN） | `P11` **纳入 G/H/I/J**，并在 **P11 设计阶段**冻结触发器清单、依赖与验收范围 |
| `STEP1B_SCHEMA_DEPENDENCY.md:193` | `P00-P10 均无 seed 需求；P13 才有 seed。**所有 trigger（P11）必须先于 P13 seed**` |
| `D-P10-11`（FROZEN） | `P10 owns audit-local immutability.` · `P11 owns remaining trigger / cross-table constraints.` |

### 3.2 HARD SCOPE BOUNDARY（指令 §3）

```text
P10 = Event / Audit persistence + tg_audit_immutable      ← 【P10-owned，P11 不得触碰】
P11 = remaining trigger / cross-table constraints          ← 本轮设计对象（G/H/I/J）
P12 = indexes
P13 = seed
```

**P11 不得吞入**：

```text
✗ P10 audit-local immutability（tg_audit_immutable）
✗ P12 index-only work
✗ P13 seed / data initialization
✗ Agent Runtime · AI Gateway Runtime · Tool Runtime
✗ business authorization semantics
✗ worker framework
```

**本体论约束（指令 §3 原文）**：

```text
trigger ≠ authorization decision
trigger ≠ ACL evaluation
trigger ≠ application policy engine
```

> DB 触发器**只**承担已经冻结的**结构性不变量 / 跨表一致性约束**。

---

## 4. 触发器物量清点（实测 · P11 范围的唯一依据）

### 4.1 迁移内已实现的触发器（`grep -c "CREATE TRIGGER"` 实测）

| migration | CREATE TRIGGER 语句数 | 对象 |
|---|---|---|
| `0003_b1_1_root_identity` | 1（循环） | `tg_<table>_set_updated_at`（identity 族） |
| `0004_b1_2_tenant_space` | 2 | `tg_<table>_set_updated_at` · **`tg_membership_tenant_consistency`（F）** |
| `0005_b1_3_authorization` | **9** | `tg_roles_set_updated_at` · **`tg_roles_scope_shape`（B）** · **`tg_roles_is_system_protect`（C）** · **`tg_tm_role_scope`（D）** · **`tg_membership_role_scope`（E）** · `tg_platform_memberships_set_updated_at` · `tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` |
| `0006_b1_3_bootstrap_state` | 3 | `tg_platform_state_set_updated_at` · `tg_platform_state_guard` · `tg_pm_bootstrap_gate` |
| `0007_b1_4_resource_acl` | 3 | `tg_resources_set_updated_at` · **`tg_resources_tenant_space_consistency`（F2）** · **`tg_acl_subject_types_protect`（C2）** |
| `0008_b1_5_tool_registry` | 2 | `tg_tools_set_updated_at` · **`tg_version_immutable`（K）** |
| `0009_timestamp_precision` | **0** | 无 trigger 变更（纯列类型修正） |
| `0010_b1_6_ai_gateway` | 1（循环） | `tg_<table>_set_updated_at`（AI 族） |
| `0011_p09_agent_tool_permission` | 3 | `tg_agents_set_updated_at` · `tg_agents_tenant_space_consistency` · **`tg_version_immutable`（K，agent_versions）** |
| `0012_authz_enforcement` | **0** | 无 trigger（仅 CHECK + 列） |
| **合计** | **24** | — |

### 4.2 A–M 清单逐项对账（**实测 vs 冻结清单**）

| 清单项 | trigger | 实测状态 | 归属 |
|---|---|---|---|
| **A** | `tg_<table>_set_updated_at`（族） | ✅ **已实现**（0003/0004/0005/0006/0007/0008/0010/0011） | 各表建时 |
| **B** | `tg_roles_scope_shape` | ✅ **已实现**（0005） | P04 |
| **C** | `tg_roles_is_system_protect` | ✅ **已实现**（0005） | P04 |
| **C2** | `tg_acl_subject_types_protect` | ✅ **已实现**（0007） | P06 |
| **D** | `tg_tm_role_scope` | ✅ **已实现**（0005） | P05 |
| **E** | `tg_membership_role_scope` | ✅ **已实现**（0005） | P05 |
| **F** | `tg_membership_tenant_consistency` | ✅ **已实现**（0004） | P05 |
| **F2** | `tg_resources_tenant_space_consistency` | ✅ **已实现**（0007） | P06 |
| **K** | `tg_version_immutable`（agent/tool_versions） | ✅ **已实现**（0008 tool / 0011 agent） | 表建时 |
| **L** | `tg_audit_immutable` | ⛔ **未实现** —— **P10-owned**（`D-P10-11`） | **P10**（**OUT OF P11**） |
| **M** | （events 无 trigger） | — 无对象 | — |
| **G** | `tg_acl_subject_exists` | ❌ **未实现** | **P11（唯一剩余之一）** |
| **H** | `tg_acl_user_hard_delete` | ❌ **未实现** | **P11** |
| **I** | `tg_acl_role_delete_block` | ❌ **未实现** | **P11** |
| **J** | `tg_agent_acl_expire` | ❌ **未实现** | **P11** |

> **⇒ P11 实质范围 = { G, H, I, J }，与 `D-PLAT-10` 逐字一致。**
> **G/H/I/J 的独立性（指令 §4）**：四者**表不同 / 时机不同 / 目的不同**，历史文档无同名异义者 ⇒
> **不存在需要拆分的同名冲突**；四者**不得**被合并为单一 trigger。

### 4.3 **清单缺口**（实测 · 6 项已实现触发器不在 A–M 清单内）

| # | trigger | table | migration | 说明 |
|---|---|---|---|---|
| 1 | `tg_pm_role_scope` | `platform_memberships` | 0005 | PLATFORM role 绑定校验 |
| 2 | `tg_pm_last_admin` | `platform_memberships` | 0005 | 最后管理员保护（信任根 ≥1） |
| 3 | `tg_roles_pm_lifecycle` | `roles` | 0005 | PM 生命周期与 role 联动 |
| 4 | `tg_platform_state_guard` | `platform_state` | 0006 | 单向 `uninitialized → initialized` |
| 5 | `tg_pm_bootstrap_gate` | `platform_memberships` | 0006 | bootstrap 唯一性门 |
| 6 | `tg_agents_tenant_space_consistency` | `agents` | 0011 | 与 F2 同族的归属一致性（P09 内联，清单成文之前） |

> **处置**：依指令 §4「DO NOT MERGE / DO NOT ASSUME EQUIVALENCE」——
> 本 PREP **不把**它们并入 A–M 清单，**不重排**既有 letter 编号；**单独登记为清单缺口 `GAP-INV-1`**（仅记录，不修改 `STEP1B_TRIGGER_INVENTORY.md`）。
> 影响：`STEP1B_TRIGGER_INVENTORY.md` 的"完整清单"表述**已不完整**；是否补注记属**冻结文档修订事项**（见 `OQ-P11-01`）。

---

## 5. P11 TRIGGER INVENTORY（G / H / I / J · 15 字段逐项）

> 字段按指令 §4 要求；语义**逐字取自** `STEP1B_TRIGGER_INVENTORY.md` §G/§H/§I/§J 与
> `B1-4_DEPENDENCY.md` §3 · `B1-4_SCHEMA_DESIGN.md` §4.2/§4.3（**不凭记忆推导**）。

### 5.1 `G` — `tg_acl_subject_exists`

| 字段 | 值 |
|---|---|
| trigger id | `G` |
| trigger name | `tg_acl_subject_exists` |
| function name（**建议，遵既有命名约定**） | `enforce_acl_subject_exists()`（先例：`enforce_roles_scope_shape` / `enforce_acl_subject_types_protect`） |
| table | `resource_permissions` |
| timing / operation | `BEFORE INSERT OR UPDATE OF subject_type_id, subject_id` · `FOR EACH ROW` |
| purpose | `subject_id` 必须存在于 `subject_type` 对应表：`user → users.id` · `role → roles.id` · `agent → agents.id`；且 `type` 必须已注册 |
| invariant protected | **受控多态边完整性**（`subject_id` 无 FK ⇒ 完整性由「`acl_subject_types` 注册 + 本 trigger 校验」承担 —— `B1-4_DEPENDENCY.md:53` 明载**这是 P1/P2-04 的冻结结论**） |
| referenced tables | `resource_permissions` · `acl_subject_types` · `users` · `roles` · **`agents`** |
| failure behavior | `RAISE EXCEPTION` → INSERT/UPDATE 失败回滚（伪造 subject 被拒） |
| recursive risk | **低**：不写被触发对象（无 hidden DML） |
| ordering dependency | 与 `resource_permissions` 上的其他 trigger 无竞争（本表除 `tg_rp_*` 外无其他 BEFORE 触发器） |
| P10/P11 ownership | **P11** |
| P12 dependency | 无（索引不影响触发语义） |
| P13 dependency | **无**（本 trigger 在 `acl_subject_types` 为空时**必然拒绝**一切写入 ⇒ 与 P13 seed 顺序为"先 trigger 后 seed"） |
| existing precedent | `tg_acl_subject_types_protect`（0007）· `enforce_*` 命名族 |

### 5.2 `H` — `tg_acl_user_hard_delete`

| 字段 | 值 |
|---|---|
| trigger id | `H` |
| trigger name | `tg_acl_user_hard_delete` |
| function name（建议） | `enforce_acl_user_hard_delete()` |
| table | `users` |
| timing / operation | **`AFTER DELETE`** · `FOR EACH ROW` |
| purpose | `DELETE FROM resource_permissions WHERE subject_type_id = (SELECT id FROM acl_subject_types WHERE key='user') AND subject_id = OLD.id` |
| invariant protected | **user 硬删后无悬空 ACL 行**（仅 retention purge 触发硬删） |
| referenced tables | `users` · `resource_permissions` · `acl_subject_types` |
| failure behavior | DELETE 失败 → 整体回滚（硬删流程整体回滚，安全） |
| recursive risk | **低**：`resource_permissions` 上的 G 是 `BEFORE INSERT OR UPDATE`（**不含 DELETE**）⇒ H 的 DELETE **不会**触发 G；`resource_permissions` 无 DELETE 触发器 |
| ordering dependency | 无 |
| P10/P11 ownership | **P11** |
| P12 dependency | 无 |
| P13 dependency | 无（但**实际只在 retention purge 时触发**，purge 本身属后续运维阶段） |
| existing precedent | 无同类（首个 AFTER DELETE 清理触发器） |

### 5.3 `I` — `tg_acl_role_delete_block`

| 字段 | 值 |
|---|---|
| trigger id | `I` |
| trigger name | `tg_acl_role_delete_block` |
| function name（建议） | `enforce_acl_role_delete_block()` |
| table | `roles` |
| timing / operation | **`BEFORE DELETE`** · `FOR EACH ROW` |
| purpose | `IF EXISTS (SELECT 1 FROM resource_permissions WHERE subject_type_id=(role type) AND subject_id=OLD.id) THEN RAISE` —— **复刻 FK RESTRICT 语义** |
| invariant protected | 被 ACL 引用的 role **不可删除** |
| referenced tables | `roles` · `resource_permissions` · `acl_subject_types` |
| failure behavior | `RAISE` → 删除被拒（回滚） |
| recursive risk | **低**：不写任何行 |
| ordering dependency | **与 `C`（`tg_roles_is_system_protect`）同表同时机（BEFORE DELETE）** ⇒ 二者触发顺序 = **PostgreSQL 默认 `name` 字母序**（`tg_acl_role_delete_block` < `tg_roles_is_system_protect`）⇒ **I 先执行**。两者语义独立（I 查引用；C 查 `is_system`），先后**不影响**正确性（任一 RAISE 均回滚） ⇒ **需在设计中显式记录顺序，不视为缺陷** |
| P10/P11 ownership | **P11** |
| P12 dependency | 无（但 `resource_permissions(subject_type_id, subject_id)` 上的索引（P12 `ix_rp_subject` **已存在**于 0007）影响本 trigger 的查询性能） |
| P13 dependency | 无 |
| existing precedent | `B1-4_SCHEMA_DESIGN.md:135` 明确"FK 在 type 表上，需业务 trigger" |

### 5.4 `J` — `tg_agent_acl_expire`

| 字段 | 值 |
|---|---|
| trigger id | `J` |
| trigger name | `tg_agent_acl_expire` |
| function name（建议） | `enforce_agent_acl_expire()` |
| table | `agents` |
| timing / operation | **`AFTER UPDATE OF status`**（→ `archived`）**或 `AFTER DELETE`** · `FOR EACH ROW` |
| purpose | 使该 agent 的 ACL 到期：`UPDATE resource_permissions SET inherited=true, expires_at=now() WHERE subject=agent`；**agent 行不删，仅失效** |
| invariant protected | **agent 归档/删除后其 ACL 不再生效**（跨表生命周期一致性） |
| referenced tables | `agents` · `resource_permissions` · `acl_subject_types` |
| failure behavior | 归档事务失败 → 回滚（安全） |
| recursive risk | **中 —— 本组唯一执行 hidden DML 者（需显式论证）**：<br>① J 的 `UPDATE resource_permissions SET inherited, expires_at` **不包含** `subject_type_id` / `subject_id` ⇒ `UPDATE OF subject_type_id, subject_id` 的 **G 不会触发**（`UPDATE OF <cols>` 仅当列出现在 SET 列表中才触发）；<br>② 若未来把 J 改为同时写 subject 列 ⇒ **将触发 G** ⇒ **须显式禁止该变更**；<br>③ `resource_permissions` 上无 UPDATE 触发器会再写 `agents` ⇒ **无互递归** |
| ordering dependency | 与 `tg_agents_set_updated_at`（BEFORE UPDATE）**时机不同**（J 为 AFTER）⇒ 无竞争；与 `K`（`tg_version_immutable`，在 `agent_versions`）**表不同** |
| P10/P11 ownership | **P11** |
| P12 dependency | 无（`ix_rp_subject` 已在 0007 存在） |
| P13 dependency | 无 |
| existing precedent | **无同类**（首个 AFTER + hidden DML 的跨表生命周期触发器） |
| **实测依据** | `resource_permissions` 确有 `inherited boolean NOT NULL` 与 `expires_at timestamptz NULL` 列（0007 实测）；`agents.status IN ('draft','active','disabled','archived')`（0011 实测）⇒ **J 的设计列与状态值均真实存在** |

---

## 6. Cross-table Invariant → 机制映射（指令 §5：**禁止无依据地把 application rule 提升为 trigger**）

| # | 不变量 | 候选机制 | **判定** | 依据 |
|---|---|---|---|---|
| V-1 | `resource_permissions.subject_id` 必须指向真实 subject（**受控多态**） | FK ✗（跨 3 张表）· CHECK ✗ · **trigger ✔** | **trigger（G）** | 无 FK 可表达；`B1-4_DEPENDENCY.md:53` 冻结结论 |
| V-2 | 被 ACL 引用的 role 不可删 | FK RESTRICT ✗（FK 在 `subject_type_id → acl_subject_types`，非 `subject_id`）· **trigger ✔** | **trigger（I）** | `B1-4_SCHEMA_DESIGN.md:135` 冻结说明 |
| V-3 | user 硬删后无悬空 ACL | FK CASCADE ✗（`subject_id` 无 FK）· **trigger ✔** | **trigger（H）** | CORE §11.1 CASCADE 白名单不含该边 |
| V-4 | agent 归档后 ACL 失效 | FK ✗ · **trigger（J）** · **或授权层 checking `status`/`archived_at`** | **⚠ `OQ-P11-05`（候选不对称）** | 见 §6.1 |
| V-5 | `roles.scope` ↔ `tenant_id`/`space_id` 形状 | **trigger（B）已实现** | 已落地 | 0005 |
| V-6 | `memberships.tenant_id = spaces.tenant_id` | **trigger（F）已实现** | 已落地 | 0004 |
| V-7 | `resources.tenant_id = spaces.tenant_id`（space 非空时） | **trigger（F2）已实现** | 已落地 | 0007 |
| V-8 | `agents` 的 tenant/space 一致性 | **trigger 已实现**（`tg_agents_tenant_space_consistency`，0011） | 已落地（**清单缺口 #6**） | 0011 |
| V-9 | published 版本不可改删 | **trigger（K）已实现** | 已落地 | 0008 / 0011 |
| V-10 | `audit_logs` 不可改删 | **trigger（L）= P10-owned** | **P10，非 P11** | `D-P10-11` |
| V-11 | `acl_subject_types` 注册表受保护 | **trigger（C2）已实现** | 已落地 | 0007 |
| V-12 | 最后管理员 ≥1（信任根） | **trigger 已实现**（`tg_pm_last_admin`） | 已落地（**清单缺口 #2**） | 0005 |
| V-13 | PLATFORM role 绑定形状 | **触发器已实现**（`tg_pm_role_scope`，清单缺口 #1） | 已落地 | 0005 |
| V-14 | bootstrap 唯一性 | **触发器已实现**（`tg_pm_bootstrap_gate` + `tg_platform_state_guard`，缺口 #4/#5） | 已落地 | 0006 |
| V-15 | **ACL 变更同事务写 `audit_logs`** | **application/service rule** | **✗ 不得提升为 trigger** | `B1-4_DEPENDENCY.md:102`（defer，`D-B14-07`）；与"trigger 不写 audit"本体论冲突 |
| V-16 | **role 归档 → 写 audit** | **application rule** | **✗ 不得提升为 trigger**（**既有 P3 文档不一致**） | `B1-4_DEPENDENCY.md:103` |
| V-17 | role 归档 → deny 行不参与决策 | **authorization layer** | **✗ 不得提升为 trigger** | `B1-4_SCHEMA_DESIGN.md:136`「授权层检查 `archived_at`」 |
| V-18 | membership removed → 实时校验 ⇒ DENY | **authorization layer** | **✗ 不得提升为 trigger** | `B1-4_SCHEMA_DESIGN.md:140` |

### 6.1 **V-4 不对称（`OQ-P11-05` 的实证基础）**

```text
role 归档   → 【授权层】检查 archived_at（无 DB 动作）        —— B1-4_SCHEMA_DESIGN.md:136
agent 归档  → 【trigger J】UPDATE resource_permissions …      —— B1-4_SCHEMA_DESIGN.md:137
```

**同一类生命周期事件，role 走授权层、agent 走 trigger** —— 该不对称**已存在于冻结文档**（非本轮发明）。
⇒ 须由 Human 裁定：**保留不对称**（各有理由）**或**统一机制；**本 PREP 不代裁**。

---

## 7. P10 交互与所有权（指令 §6）

### 7.1 `tg_audit_immutable`（P10-owned）—— **P11 四项禁止**

```text
P11 MUST NOT duplicate  tg_audit_immutable
P11 MUST NOT replace    tg_audit_immutable
P11 MUST NOT weaken     tg_audit_immutable
P11 MUST NOT relocate   tg_audit_immutable
```

依据：`D-P10-11`（`tg_audit_immutable` = **P10-owned**；`P10 owns audit-local immutability`；
`P11 owns remaining trigger / cross-table constraints`）。

### 7.2 P11 triggers 是否触及 P10 对象（`events` / `audit_logs` / outbox）

| P11 trigger | 触发表 | 是否触及 `events` / `audit_logs` / outbox | 所有权判定 |
|---|---|---|---|
| `G` `tg_acl_subject_exists` | `resource_permissions` | **否**（不读不写 P10 对象） | **P11-owned** |
| `H` `tg_acl_user_hard_delete` | `users` | **否** | **P11-owned** |
| `I` `tg_acl_role_delete_block` | `roles` | **否** | **P11-owned** |
| `J` `tg_agent_acl_expire` | `agents` | **否** | **P11-owned** |

> **结论**：**无 cross-stage 隐式重复责任**；P11 与 P10 在 trigger 面上**零交叠**。
> **前提约束（须冻结）**：**G/H/I/J 一律不得写入 `events` / `audit_logs`**（否则会与 P10 的审计面
> 及"trigger 不写 audit"本体论冲突，见 V-15/V-16）。

---

## 8. FUNCTION DESIGN 与安全审阅（指令 §7 · **仅设计，不写代码**）

### 8.1 共用设计约束（拟）

| 项 | 拟设计 | 依据 |
|---|---|---|
| 语言 | `plpgsql` · `RETURNS trigger` | 既有先例（0003–0011 全部 plpgsql） |
| 命名 | `enforce_<invariant>()`（trigger `tg_<...>`） | 既有命名族 |
| 时机 | 严格按 §5（G/I = BEFORE；H/J = AFTER） | 冻结清单 |
| `OLD` / `NEW` | G：`NEW.subject_type_id` / `NEW.subject_id`；H：`OLD.id`；I：`OLD.id`；J：`OLD.id` / `OLD.status` | 语义要求 |
| 失败条件 | 不满足不变量 ⇒ `RAISE EXCEPTION`（**fail closed**，与 `D-AUTH-12` 同向） | 既有先例（17 处 `RAISE EXCEPTION`） |
| 异常行为 | 异常 ⇒ 事务回滚（**不做 EXCEPTION 吞异常**） | 既有先例 |
| 递归防护 | ① G/H/I **不含 hidden DML** ⇒ 无递归面；② J 含 hidden DML ⇒ 依赖"不写 subject 列"（见 §5.4） | 本轮分析 |
| `SECURITY DEFINER` | **不需要** —— 拟用默认 **`SECURITY INVOKER`** | **实测先例：全仓 `SECURITY DEFINER` = 0** |
| `search_path` | **不设** `SET search_path`（既有先例一致）；所有对象引用**建议 schema-qualified**（`public.<table>`）或依赖受控 `search_path` ⇒ **`OQ-P11-08`** | 需裁定 |

### 8.2 风险逐项审阅（指令 §7 五类）

| 风险 | 评估 | 结论 |
|---|---|---|
| **security-definer privilege escalation** | **不引入 SECURITY DEFINER** ⇒ **无此风险**（全仓先例 = 0） | ✅ 无 |
| **unqualified object resolution** | 现有触发器使用不限定名（依赖默认 `search_path`）。若 `search_path` 被外部改写，存在解析歧义面 | ⚠ **`OQ-P11-08`**（是否强制 schema-qualified / 设 `search_path`） |
| **cross-tenant leakage** | **本组 4 个 trigger 均不做租户过滤判定**：G 只查 subject **存在性**（不比较 tenant）；H/I/J 均以 `OLD.id` 精确定位。**G 的语义天然跨表**（`agents` 等表本身有 tenant 归属，但 G 只校验存在性） | ⚠ **`OQ-P11-06`**：G 是否需**同租户**约束（vs 仅存在性）？**不得无依据地扩张** |
| **trigger recursion** | G/H/I 无 hidden DML ⇒ 无递归；J 有 hidden DML 但**不触发 G**（列不在 SET 列表）⇒ 无递归 | ✅ 低（**须在未来变更中保持**） |
| **hidden DML** | **仅 J**（`UPDATE resource_permissions`）。须显式登记为"受控 hidden DML"，并冻结"不得写入 subject 列 / `events` / `audit_logs`" | ⚠ **受控**（`OQ-P11-04` / `OQ-P11-09`） |

### 8.3 若未来确需 `SECURITY DEFINER`

```text
【记录风险，不实施】：
  ① 提升权限 ⇒ 必须最小化：REVOKE ALL FROM PUBLIC + 仅授必要对象
  ② 必须 SET search_path = <固定值>（否则是经典提权面）
  ③ 必须显式记录"为何 INVOKER 不可行"
  ⇒ 本 PREP 的立场：G/H/I/J 【无一需要】 SECURITY DEFINER（不跨权限边界）
```

---

## 9. Dependency Order（指令 §8）

```text
表依赖（实测，均已满足）：
  G 依赖 users(P01) + roles(P04) + agents(P09) + acl_subject_types(P06) + resource_permissions(P06)  ⇒ 【全部已存在】
  H 依赖 users(P01) + resource_permissions(P06) + acl_subject_types(P06)                            ⇒ 【全部已存在】
  I 依赖 roles(P04) + resource_permissions(P06) + acl_subject_types(P06)                            ⇒ 【全部已存在】
  J 依赖 agents(P09) + resource_permissions(P06) + acl_subject_types(P06)                           ⇒ 【全部已存在】

⇒ 【无未来对象依赖】：G/H/I/J 的实施前置【已经全部满足】（P09 已于 0011 完成）

阶段顺序：
  P10 (events/audit_logs + tg_audit_immutable)
    ↓
  P11 (G/H/I/J)          ← 本 PREP 设计对象
    ↓
  P12 (indexes)          ← G/H/I/J 均【不新增】索引需求（复用既有 ix_rp_subject）
    ↓
  P13 (seed)             ← trigger 必须先于 seed（DEPENDENCY:193）

P13 依赖核查（指令 §8）：
  ① 【无】任何 G/H/I/J 需要 P13 seed 才能成立
  ② 反之：G 在 acl_subject_types 为空时【必然拒绝一切写入】⇒ 与"先 trigger 后 seed"一致
  ③ 【不得偷带 seed】：P11 不得插入 acl_subject_types / roles / users 任何行（P00–P10 无 seed；P13 才有）
```

**关键顺序结论**：`G/H/I/J` 的**唯一**阻断因素曾是"引用不存在的 `agents`"（`B1-4_DEPENDENCY.md:64`），
该阻断**已随 P09（0011）解除** ⇒ **P11 无外部前置缺失**。

---

## 10. 连带同步面（P11 落地时必须同步 · 实测）

| # | 同步面 | 数量 | 证据 |
|---|---|---|---|
| 1 | 断言 G/H/I/J **不存在**的集成测试（`FORBIDDEN`/`absent` 集合） | **3** 文件 · **12** 名目 | `test_agent_tool_permission_schema.py:152-155` · `test_resource_acl_schema.py:87-90` · `test_tool_registry_schema.py:76-79` |
| 2 | 断言 alembic head = `0012` 的测试 | **15** 文件 | `grep -rln 0012_authz_enforcement tests/` |
| 3 | `tests/architecture/` 触发器/依赖守卫 | 现有 **2** 文件（无 trigger 相关守卫） | `ls tests/architecture/` |
| 4 | 迁移 docstring 中的"不实施 G/H/I/J"声明 | 0007 · 0008（**原文在位**） | 两文件 docstring |
| 5 | `STEP1B_TRIGGER_INVENTORY.md` 的"完整清单"表述 | 1 处（**已不完整**，见 §4.3） | `GAP-INV-1` |

---

## 11. 一致性与冲突扫描（Charter §7 · 实测）

| 检查 | 结果 | 证据 |
|---|---|---|
| `tg_audit_immutable` 是否已实现？ | **否**（P10-owned，未实施） | 迁移内 `CREATE TRIGGER … audit_logs` 命中 **0** |
| P11 是否重复/搬移 P10 的 L？ | **否**（本轮零实施） | — |
| 是否存在同名异义的 trigger？ | **否**（A–M 名称互异；G/H/I/J 语义独立） | §4.2 / §5 |
| 冻结清单是否完整？ | **⚠ 不完整（6 项缺口）** | §4.3 `GAP-INV-1` |
| 是否存在"trigger 写 audit"的冲突？ | **⚠ 是（既有 P3 已登记）** | `CORE_DOMAIN_MODEL.md:263` vs `B1-4_DEPENDENCY.md:103` |
| H/I 的相位理由是否充分？ | **⚠ 否（既有已登记）** | `B1-4_DEPENDENCY.md:74-76`（"原文不精确之处"，属冻结文档修订事项） |
| role/agent 归档机制是否对称？ | **⚠ 不对称（既有）** | `B1-4_SCHEMA_DESIGN.md:136` vs `:137` |
| `SEARCH_PATH` / `SECURITY DEFINER` 先例 | 全仓 `SECURITY DEFINER` = **0** | 命令 |
| **陈旧"P11 已实现"声明扫描**（排除本轮 3 份 P11 文档） | **0 命中** | `grep -rniE "P11…(implemented\|已实现\|已实施\|已完成\|已落地)" docs/` |
| **陈旧"G/H/I/J 已实现"声明扫描** | **0 命中** | 四名 grep（`已实现\|implemented`）= 0 |
| **已挂载触发器的表集合**（实测去重） | `roles` · `platform_memberships` · `platform_state` · `tools` · `tenant_memberships` · `resources` · `memberships` · `agents` —— **不含** `audit_logs` / `events` | 命令（`CREATE TRIGGER … ON <table>` 提取） |
| P09 保护 | `0010`/`0011`/`0012` sha256 未变 · 代码/测试/迁移 diff **空** | 命令 |

**候选冲突/缺口登记（**不代裁**）**：

```text
CF-1  GAP-INV-1  冻结 A–M 清单缺 6 项已实现触发器
CF-2  P3(既有)   「trigger 写 audit」 vs 「trigger 不写 audit」
CF-3  P3(既有)   H/I「P09 后」理由不充分（显式阶段冻结 vs 依赖推导）
CF-4  新登记      role 归档（授权层）vs agent 归档（trigger）机制不对称
```

---

## 12. Open Questions（`OQ-P11-01` … `OQ-P11-14` · 全部 `PENDING`）

> 指令 §9 要求**至少**覆盖 `OQ-P11-01`…`OQ-P11-12`；本轮**据实际证据新增 2 项**（`13`/`14`），
> **未凭空扩大**。全部 `HUMAN DECISION = PENDING` / `STATUS = PROPOSED`。

| OQ | 主题 | 问题（摘要） |
|---|---|---|
| `OQ-P11-01` | trigger inventory ownership | A–M 清单**归属**：已实现的 9 项是否正式"归 P11 复核"？§4.3 的 **6 项缺口**如何登记（补注记 / 新清单）？ |
| `OQ-P11-02` | G/H/I/J exact semantics | 四者表/时机/目的**逐一确认**（§5）；是否需任何语义修正？ |
| `OQ-P11-03` | trigger timing | G/I = BEFORE、H/J = AFTER 是否确认？J 是否同时挂 `AFTER UPDATE OF status` **与** `AFTER DELETE`？ |
| `OQ-P11-04` | trigger failure semantics | 一律 `RAISE EXCEPTION` + 回滚（fail closed）？**是否允许吞异常**？（倾向不允许） |
| `OQ-P11-05` | cross-table consistency | **V-4 不对称**：agent 归档走 trigger vs role 归档走授权层 —— 保留还是统一？ |
| `OQ-P11-06` | tenant/space consistency | **G 只做存在性校验，是否需**同租户**约束？**（不得无依据扩张） |
| `OQ-P11-07` | published immutability boundary | `K`（`tg_version_immutable`）**已实现**；P11 仅确认边界**不含** L（P10-owned）？ |
| `OQ-P11-08` | security-definer / search_path 政策 | 是否强制 **schema-qualified** 引用 / 设 `search_path`？是否**永久禁止** `SECURITY DEFINER`（除非显式批准）？ |
| `OQ-P11-09` | recursion policy | 递归防护政策：禁止 trigger 写入**自身表 / subject 列 / `events` / `audit_logs`**？J 的 hidden DML 是否限定为**唯一受控例外**？ |
| `OQ-P11-10` | P10/P11 ownership | 四项禁止（MUST NOT duplicate/replace/weaken/relocate L）是否正式冻结？ |
| `OQ-P11-11` | P11/P12 dependency | P11 是否**不新增索引**（G/H/I/J 复用 `ix_rp_subject`）？P12 是否**不重复**为 trigger 建索引？ |
| `OQ-P11-12` | P11/P13 dependency | 确认"trigger 先于 seed"；确认 P11 **不携带任何 seed**（不插 `acl_subject_types`/`roles`/`users`） |
| `OQ-P11-13` | **（新增）** 清单缺口处置 | `GAP-INV-1`（6 项）：是否对 `STEP1B_TRIGGER_INVENTORY.md` 追加 **append-only 注记**？是否**重排** letter 编号（**倾向不重排**）？ |
| `OQ-P11-14` | **（新增）** 既有 P3 文档不一致处置 | `CF-2`（trigger 写 audit）与 `CF-3`（H/I 相位理由）如何处置：**保持 defer** / **追加 clarification** / **提为正式修订**？ |

---

## 13. Implementation Gate

```text
P11 PREP（本轮）        = ALLOWED（本报告 + 决策包 + 验收矩阵）
P11 DECISION FREEZE     = NOT YET（14 项 OQ 全部 PENDING）
P11 IMPLEMENTATION      = NOT AUTHORIZED
P12                     = NOT AUTHORIZED
P13                     = NOT AUTHORIZED
Runtime Implementation Gate = CLOSED（D-AGENT-16）

实施前置（全部满足方可开启）：
  ① Human Decision Freeze（OQ-P11-01…14 全部裁定）
  ② 显式实施授权
  ③ 跨决策扫描（Charter §7）完成并留档
  ④ P10 对象保护复核（0010/0011/0012 逐字节未变）—— 已 ✅
```

---

## 14. 本轮禁止面（§1）与实测结果

| 禁止项 | 实测 |
|---|---|
| DDL / DML | **未发生** |
| `CREATE / ALTER / DROP TRIGGER` | **未发生** |
| `CREATE / ALTER FUNCTION` | **未发生** |
| migration 创建 / 修改 | **未发生**（versions/ = 12 文件；`0013+ = 0`） |
| `alembic upgrade` / `downgrade` | **未执行**（仅 `heads` 只读查询） |
| runtime / API / worker 实施 | **未发生** |
| test 代码修改 | **未发生** |
| 应用代码修改 / 配置修改 | **未发生**（`git diff` 全空） |
| commit / tag / push | **未发生**（HEAD 仍 `034ee97`；tags 仍 8；remote none） |
| 既有文档修改 | **未发生**（本轮仅新增 3 份 P11 文档） |

---

## 15. Exit Criteria

✓ Baseline verified ✓ P11 权威定义与 HARD 边界明确 ✓ 触发器物量清点（24 语句 / 15 不变量触发器）✓
**A–M 逐项对账完成** ✓ **G/H/I/J 15 字段清单完成** ✓ 清单缺口登记（6 项）✓
Cross-table invariant → 机制映射（18 项 V-*）✓ P10 交互与所有权（四项禁止）✓
Function Design + 五类风险审阅 ✓ Dependency Order（无外部前置缺失）✓ 连带同步面 ✓
一致性与冲突扫描（4 项登记）✓ OQ 14 项（全 PENDING）✓ **零实施**

---

## 16. HARD STOP 触发面（本轮实测未触发）

`DDL / DML` · `trigger / function 创建或修改` · `migration 创建或修改` · `alembic upgrade/downgrade` ·
`runtime / API / worker 实施` · `测试代码修改` · `应用代码修改` · `配置修改` ·
`commit / tag / push` · `改写历史冻结正文` —— **本轮零命中**。

---

## 17. FINAL

```text
P11 PREP = COMPLETE
P11 DECISION FREEZE = NOT YET
P11 IMPLEMENTATION  = NOT AUTHORIZED
P12 / P13           = NOT AUTHORIZED
Runtime Implementation Gate = CLOSED
DDL / DML / trigger / function / migration / code / test / config / commit / tag / push = 0
```

---

**配套文档**：[`P11_DECISION_RESOLUTION.md`](./P11_DECISION_RESOLUTION.md)（14 项 OQ 逐项决议材料 ·
`HUMAN DECISION = PENDING` ×14）· [`P11_ACCEPTANCE_MATRIX.md`](./P11_ACCEPTANCE_MATRIX.md)（脚本实测）。

**END OF P11 PREP REPORT（2026-09-25 · READ-ONLY）**

---

## 18. 后续注记（**append-only** · 遵 `PLATFORM_DECISION_LOG.md` Charter §5.2）

> **[`D-P11-01`…`D-P11-14` 注记 · 2026-09-25]** P11 Decision Freeze 完成：14 项 OQ 全部冻结；
> 本 PREP 的全部 PROPOSED 内容据此进入契约层。
> 关联：本文档 §12（OQ 表）· §13（Implementation Gate）· §17（FINAL）。
> 性质：**状态更新 + 交叉引用**。**不修改本文档既有段落、表格行或任何结论。**

**⚠ 编号重映射（canonical，本节显式登记）**

本轮 `UAP P11 — HUMAN DECISION RESOLUTION` 中，`OQ-P11-06` 与 `OQ-P11-07` 的主题相对**本 PREP §12 的编号对调**。
**canonical 编号以 `PLATFORM_DECISION_LOG.md` 的 `D-P11-*` 为准**：

| 本 PREP §12 的编号 | 主题 | **canonical 编号** |
|---|---|---|
| `OQ-P11-05` | cross-table consistency（V-4 不对称） | `D-P11-05`（**未变**） |
| `OQ-P11-06` | Tenant / Space Consistency（G 是否需同租户） | **`D-P11-07`** ← **移至 07** |
| `OQ-P11-07` | Published Immutability Boundary（`K`） | **`D-P11-06`** ← **移至 06** |
| `OQ-P11-08`…`OQ-P11-14` | （各自主题） | `D-P11-08`…`D-P11-14`（**未变**） |

> 本 PREP 的 §12 表格**保留 pre-freeze 编号**（append-only 纪律，不改写既有表格行）；
> **消费本文档时须以上表映射到 canonical 编号**。`P11_DECISION_RESOLUTION.md` §7/§8 已按 canonical 重排。

**状态更新对照**：

| 项 | 本 PREP 原状（2026-09-25 PREP） | **Decision Freeze 终态** | 冻结条目 |
|---|---|---|---|
| §12 14 项 OQ | `HUMAN DECISION = PENDING`（`PROPOSED`） | **14 / 14 `FROZEN`** | `D-P11-01`…`D-P11-14` |
| §4.3 `GAP-INV-1`（6 项清单缺口） | 登记（未代裁） | **CLARIFIED** —— `supplementary inventory gap` · **DO NOT** renumber A–M / insert letters / move into G/H/I/J / reclassify as P11 delivery | `D-P11-13` · `CF-1` |
| §11 `CF-2`（trigger 写 audit） | 登记（既有 P3） | **CLARIFIED** —— `trigger does NOT write audit`；audit persistence 属 **P10**；**P11 不新增任何 audit 写入 trigger** | `D-P11-14` · `CF-2` |
| §11 `CF-3`（H/I 相位理由） | 登记（既有，属冻结文档修订） | **CLARIFIED** —— **`P09-after is an explicit phase freeze, not a dependency-derived conclusion`**；**不得据此重排 H/I** | `D-P11-13` · `CF-3` |
| §6.1 `CF-4`（role/agent 不对称） | 登记（未代裁） | **INTENTIONAL / FROZEN** —— **保留不对称，不得强制统一**；P11 不新增 `role archive → ACL mutation`，不移除 J | `D-P11-05` · `CF-4` |
| §8.3 SECURITY DEFINER | 记录风险（不实施） | **冻结政策** —— `SECURITY INVOKER` = canonical；**禁止** `SECURITY DEFINER`（除非**新的独立 Human Decision**）；保留三项风险为**实施期安全检查项** | `D-P11-08` |
| §5.4 J 的 hidden DML | 分析（不触发 G） | **冻结禁令** —— J 的 SET 列表 **MUST NOT** 含 `subject_type_id` / `subject_id`；**禁止 trigger chain** | `D-P11-09` |
| §17 FINAL `P11 DECISION FREEZE = NOT YET` | `NOT YET` | **`PASSED`** | — |
| §17 FINAL `P11/P12/P13 IMPLEMENTATION = NOT AUTHORIZED` | `NOT AUTHORIZED` | **不变** | — |

**注记新增的契约层内容（来源 = Human Decision 正文，非本 PREP 的追认）**：

```text
① G 【不得引用 `groups`】·【不得承担 Authorization Evaluation】          —— D-P11-02
② H 仅硬删除流程（软删除不得通过 H 清理）· I = ACL reference protection（非授权求值器）· J 不删 agent 本身
③ G = subject existence ≠ subject is authorized（六类授权语义明确禁止入 trigger） —— D-P11-07
④ 禁 trigger chain · J 不得写 subject 列                                    —— D-P11-09
⑤ CF-1..CF-4 的正式定性（CLARIFIED ×3 · INTENTIONAL/FROZEN ×1）              —— 附录 H.2
```

**append-only clarification 落点**：`STEP1B_TRIGGER_INVENTORY.md`（`GAP-INV-1` + `CF-3`）·
`CORE_DOMAIN_MODEL.md`（`CF-2`）。**两处均为追加注记，未改写任何既有结论 / 表格行 / 数值。**

**未触碰**：`DDL` / `DML` / trigger / function / migration（含 `0013+`）· `core/` / `services/` /
`infrastructure/` / `tests/` / `apps/` / `config` · `0010` / `0011` / `0012` · `commit` / `tag` / `push`。

**END OF P11 PREP REPORT（2026-09-25 · READ-ONLY）**
**后续注记追加：P11 Decision Freeze（`D-P11-01`…`D-P11-14` 全部 `FROZEN`；`CF-1`…`CF-4` 已处置；含 `OQ-P11-06`/`07` canonical 重映射），2026-09-25**
