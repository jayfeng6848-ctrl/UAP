# P09_DEPENDENCY

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE（依赖与 FK 规则 FROZEN）**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**权威记录**: `P09_DECISION_LOG.md`（`D-P09-02` / `D-P09-03` / `D-P09-10` / `D-P09-11` · ND 轮 `D-P09-15` / `D-P09-17`）
**设计轮次**: DESIGN WRITE（2026-09-17；对象命名 / trigger / retention 见 `P09_SCHEMA_DESIGN.md` §2B）

> 本文档冻结 **FK 逐条规则**与**依赖方向**。所有 `ON DELETE` 均为已冻结值；
> 未冻结的仅剩对象**命名**与 **DESIGN 层口径**（见 §7）。

---

## 1. 依赖链（既有权威）

```
P09（STEP1B_SCHEMA_DEPENDENCY.md:170）:
  agents（无 current_version FK）→ agent_versions → agent_permissions → tool_executions
  → 补 agents.current_version_id FK
```

**P09 → 既有表**：`tenants` · `spaces` · `users` · `permissions` · `tools` · `tool_versions` · `ai_routes`
**P09 → P08 表**：仅 `ai_routes`（经 `agents.default_route_id`，SET NULL）—— 方向正确
**P08 → P09**：**0**（`ai_request_logs.agent_id` = NO FK，见 `D-P09-10`）
**P09 → P10**：仅审计写入（已 defer，`D-B14-07`）
**P09 → P09 内部**：见 §2

---

## 2. FK 候选清单（**16 条，全部 FROZEN**）

| # | source → target | nullable | **ON DELETE** | 冻结来源 |
|---|---|---|---|---|
| **F1** | `agents.tenant_id → tenants.id` | NN | **RESTRICT** | `D-P09-03`（新冻结） |
| **F2** | `agents.space_id → spaces.id` | NULL | **RESTRICT** | `D-P09-03`（新冻结） |
| **F3** | `agents.owner_id → users.id` | NN | **RESTRICT** | `D-P09-03`（新冻结） |
| F4 | `agents.default_route_id → ai_routes.id` | NULL | **SET NULL** | 既有（`CORE:289` / `CM:267` / `ER:481` / `SD:62`） |
| F5 | `agents.current_version_id → agent_versions.id` | NULL | **SET NULL** | 既有（`SD:132-134`，**deferred FK**） |
| F6 | `agent_versions.agent_id → agents.id` | NN | **CASCADE** | 既有（`CORE:299` / `CM:279` / `§11.1:978`） |
| **F7** | `agent_versions.published_by → users.id` | NULL | **SET NULL** | `D-P09-03`（新冻结） |
| F8 | `agent_permissions.agent_id → agents.id` | NN | **CASCADE** | 既有（`CM:291` / `§11.1:979`） |
| F9 | `agent_permissions.version_id → agent_versions.id` | NULL | **CASCADE** | 既有（`CM:291`） |
| **F10** | `agent_permissions.permission_id → permissions.id` | NULL | **CASCADE** | `D-P09-03`（新冻结） |
| **F11** | `agent_permissions.tool_id → tools.id` | NULL | **CASCADE** | `D-P09-03`（新冻结） |
| **F12** | `tool_executions.tenant_id → tenants.id` | NN | **RESTRICT** | `D-P09-02` + `D-P09-03`（新冻结） |
| F13 | `tool_executions.tool_id → tools.id` | NN | **RESTRICT** | 既有（`CM:251` / `SD:54`） |
| F14 | `tool_executions.tool_version_id → tool_versions.id` | NN | **RESTRICT** | 既有（`CM:251` / `SD:54`） |
| **F15** | `tool_executions.agent_id → agents.id` | NULL | **SET NULL** | `D-P09-03`（新冻结） |
| **F16** | `tool_executions.actor_id → users.id` | NULL | **SET NULL** | `D-P09-03`（新冻结） |

**统计（FK = 16）**
```
CASCADE   = 5   {F6, F8, F9, F10, F11}
RESTRICT  = 6   {F1, F2, F3, F12, F13, F14}
SET NULL  = 5   {F4, F5, F7, F15, F16}
合计      = 16  ✅
```

---

## 3. 删除语义（FROZEN 后果）

```
· agents 删除（受控）      → agent_versions / agent_permissions 随删（F6/F8 CASCADE）
                            → current_version_id 置 NULL（F5 SET NULL，若引用自身版本行）
· 版本行删除（受控 purge）  → agent_versions.agent_id CASCADE 触发父实体整棵清理（白名单语义）
· users 删除（受控 purge）  → agents.owner_id 被 RESTRICT 拒绝（F3）
                            → agent_versions.published_by / tool_executions.actor_id 置 NULL（F7/F16 SET NULL）
· tenants 删除（受控 purge）→ agents.tenant_id / tool_executions.tenant_id 被 RESTRICT 拒绝（F1/F12）
· spaces 删除（受控 purge） → agents.space_id 被 RESTRICT 拒绝（F2）
· tools 删除               → agent_permissions.tool_id 级联（F11）· tool_executions.tool_id 被 RESTRICT 拒绝（F13）
· **历史记录保护**          → tool_executions 的 5 条 FK 中 **CASCADE = 0**
                              ⇒ Agent / User 删除**不会**级联清除历史 execution
```

---

## 4. 与既有冻结文档的一致性

| 项 | 状态 |
|---|---|
| `CORE §11.1` CASCADE 白名单含 `agents → agent_versions` / `agents → agent_permissions` | ✅ 与 F6/F8 一致 |
| `CORE §11.1`「凡不在白名单者，一律 RESTRICT」 | ⚠ **不能机械适用**：`D-P09-03` 逐条给出 F1/F2/F3/F12 = RESTRICT，而 F7/F15/F16 = SET NULL、F10/F11 = CASCADE（后者与 B1-5 `tool_permissions` 实作先例一致） |
| `D-P09-03` 与先例分叉（登记） | F3 = RESTRICT，而 `spaces.owner_id`（`0004:104`）/ `resources.owner_id`（`0007:133`）为 SET NULL —— **仅登记，不代表先例被推翻** |
| `ER_MODEL:474-481` 的删除规则表 | F4/F6/F8 一致；其余为本文档新增冻结 |

---

## 5. 循环与 deferred FK（FROZEN）

```
agents.current_version_id ──(SET NULL)──→ agent_versions.id      ← F5（deferred）
agent_versions.agent_id   ──(CASCADE)───→ agents.id              ← F6
```

**Upgrade 顺序（沿用 `SD §4.1:131-134`）**：
1. 建 `agents`（**不含** `current_version_id` 的 FK 约束）
2. 建 `agent_versions`（`agent_id → agents` 正常声明）
3. `ALTER TABLE agents ADD CONSTRAINT fk_agents_current_version FOREIGN KEY (current_version_id) REFERENCES agent_versions(id) ON DELETE SET NULL;`

**Downgrade 顺序（`D-P09-11` = A，0005 同构）**：
```
DROP CONSTRAINT fk_agents_current_version  →  DROP TABLE agent_versions  →  DROP TABLE agents
```

---

## 6. 下游契约（登记，非 P09 交付）

| 对象 | 关系 | 状态 |
|---|---|---|
| `ai_request_logs.agent_id` | 记录用途，**无 FK** | `D-P09-10`（NO FK 维持） |
| `G/H/I/J` | 依赖 `resource_permissions` + `agents` 等 | `D-P09-06`（P09 后） |
| `agent` subject（`acl_subject_types`） | `tg_acl_subject_exists` 的 agent 分支依赖 `agents.id` | P09 后 / P13（seed） |
| `resources` tenant/space 一致性 | `tg_resources_tenant_space_consistency`（P06） | 先例；P09 对 `agents` 的同型约束见 `D-P09-12` |
| **索引权威归属** | P09 索引清单以 **`STEP1B_INDEX_STRATEGY`** 为准（`CORE §12` 为不完整摘要，**不回改**）；8 个对象的逐项清单见 `P09_SCHEMA_DESIGN.md` §2.7 | `D-P09-15`（ND-03） |
| **`0008:36-37` 措辞漂移** | 「G/H/I/J **仍属 P09**」为**措辞漂移**；权威 = `TRIGGER_INVENTORY:200-203` + `D-P09-06 = A` ⇒ **G/H/I/J = P09 后** | `D-P09-17`（ND-05）· 详见 `P09_DECISION_LOG.md` §4A |
| **`agents` 一致性 trigger**（`U-2`） | `tg_agents_tenant_space_consistency` + `enforce_agents_tenant_space_consistency()`（BEFORE INSERT OR UPDATE；structural integrity only） | `D-P09-12` · DESIGN RESOLVED（§2B.3） |
| **`agent_versions` 不可变性**（`NU-07`） | trigger `tg_version_immutable`（共用名）· function `enforce_agent_versions_immutable()`（独立函数，**不修改 0008**） | `D-P09-14` · DESIGN RESOLVED（§2B.4） |
| **retention 资格锚**（`U-1`） | `tool_executions.created_at < now() - interval '90 days'`；**executor = 人工运维**（不属 P09） | `D-P09-01` · DESIGN RESOLVED（§2B.7） |

---

## 7. 本阶段**未**冻结（NOT FROZEN）

- **已由 DESIGN WRITE 收敛（`DESIGN RESOLVED`，非 Human Decision）**：对象命名表（FK 16 / CK 8 / 索引 8 /
  trigger 3 / function 2）· 列类型与 DEFAULT 矩阵（54 列）· P09 时间列清单（9 列）·
  consistency trigger 名称与语义 · 不可变性函数名 · retention policy 与 eligibility
  → 全部见 `P09_SCHEMA_DESIGN.md` §2B
- **仍 NOT FROZEN**：canonical **总计数**与编号空间
- **仍 HUMAN DECISION REQUIRED**：`ND-A`（`resource_scope <> ''` 可选收紧）· `ND-B`（`fk_agents_current_version`
  是否 `DEFERRABLE`）—— 不阻断其余设计
- 上述未冻结项**不得**在本阶段推定或补齐

---

## 8. Gate

```
P09 FK 规则 = FROZEN（16/16）· ON DELETE = FROZEN（16/16）
P09 索引权威 = `STEP1B_INDEX_STRATEGY`（`D-P09-15`）· 索引对象 = 8（`D-P09-15`）
对象命名 / trigger / retention = DESIGN RESOLVED（`P09_SCHEMA_DESIGN.md` §2B）
P08 → P09 forward FK = 0 · P09 → Core = 0
P09 DESIGN = WRITE COMPLETE · 0011 = ABSENT · MIGRATION = NO · DDL = NO · DML = NO
NOT FROZEN = canonical 总计数 · HUMAN DECISION REQUIRED = ND-A · ND-B
```
