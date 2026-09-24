# AUTHORIZATION / ACL / POLICY — SCHEMA IMPACT

| 字段 | 内容 |
|---|---|
| **阶段** | `STAGE 2 — IMPLEMENTATION CONTRACT PREP` |
| **性质** | `SCHEMA IMPACT ANALYSIS`（**未创建任何对象**） |
| **日期** | 2026-09-23 |
| **基线** | HEAD `eb6d4cb…` · Alembic head `0011_p09_agent_tool_permission` · 0012+ absent |
| **权威** | `D-AUTH-17`（schema impact）· `D-AUTH-05`（action）· `D-AUTH-09`（tool）· `D-AUTH-20`（ACL UQ）· `D-AUTH-23`（`GAP-11`） |
| **决策 registry** | `D-AUTH` total **23** = `FROZEN` **20** + `DEFERRED` **3** + `SUPERSEDED` **0**（`OQ` 22 = 19 + 3；+ 非 OQ `D-AUTH-23` / `GAP-11`） |
| **迁移授权** | **NOT AUTHORIZED**（本文件只做计划） |

---

## 1. 表 → 迁移 归属（只读实测，用于判定 P09 保护面）

| 表 | 来源 migration | 是否 P09（0011） | 本轮可否变更 |
|---|---|---|---|
| `permissions` | `0005_b1_3_authorization` | ❌ | ✅（需新 migration） |
| `roles` | `0005_b1_3_authorization` | ❌ | ✅ |
| `role_permissions` | `0005_b1_3_authorization` | ❌ | ✅ |
| `resources` | `0007_b1_4_resource_acl` | ❌ | ✅ |
| `acl_subject_types` | `0007_b1_4_resource_acl` | ❌ | ✅ |
| `resource_permissions` | `0007_b1_4_resource_acl` | ❌ | ✅ |
| `tools` | `0008_b1_5_tool_registry` | ❌ | ✅ |
| `tool_versions` | `0008_b1_5_tool_registry` | ❌ | ✅ |
| `tool_permissions` | `0008_b1_5_tool_registry` | ❌ | ✅ |
| `agents` | `0011_p09_agent_tool_permission` | **✅ P09** | ❌ **保护** |
| `agent_versions` | `0011_p09_agent_tool_permission` | **✅ P09** | ❌ **保护** |
| `agent_permissions` | `0011_p09_agent_tool_permission` | **✅ P09** | ❌ **保护** |
| `tool_executions` | `0011_p09_agent_tool_permission` | **✅ P09** | ❌ **保护** |

> **判定依据**：`grep -ln "\"<table>\"" migrations_alembic/versions/*.py` 实测（`0009_timestamp_precision` 为全体时间精度校正轮，非建表）。
> **关键结论**：`tool_permissions` 属 **0008**，**不是 P09 表** ⇒ `SC-2` **不触碰 P09**。

---

## 2. §26 逐表分析（8 张指定表）

### 2.1 `permissions` — **MODIFY**

| 项 | 内容 |
|---|---|
| **现状** | `id` · `key` · `resource_type`(NULL) · `action`(text, 无 CHECK) · `description` · `is_system` · `created_at` |
| **分类** | **MODIFY** |
| **Why** | `D-AUTH-05` 冻结 12 项 canonical action；实测 `action` 为**自由 text 且无 CHECK** ⇒ 拼写变体（`delete`/`Delete`/`DELETE`）可绕过统一授权语义（`IMPLEMENTATION GAP-10`） |
| **Which Frozen Decision** | `D-AUTH-05` |
| **Backward Compatibility** | **兼容**：仅新增 CHECK。当前 **seed = 0**（P00–P12 无 seed）⇒ 存量越界值风险极低；但须在 migration 中**先校验再添加**（防御性） |
| **Migration Need** | ✅ 需新 migration（**不得改写 0005**） |

### 2.2 `resource_permissions` — **NO CHANGE**

| 项 | 内容 |
|---|---|
| **现状** | `id` · `resource_id` · `subject_type_id` · `subject_id` · `action`(text) · `effect` · `conditions` · `inherited` · `expires_at` · `granted_by` · `created_at`；`UNIQUE(resource_id, subject_type_id, subject_id, action)` |
| **分类** | **NO CHANGE**（唯一例外见下） |
| **Why** | `D-AUTH-20` **明确冻结**：保持现有唯一性模型、**不新增 `effect` 到唯一键**、不重建 unique key |
| **唯一动作** | `action` 列的 canonical CHECK（属 **SC-1** 的一部分，见 §3）—— **不修改** `UNIQUE` |
| **Which Frozen Decision** | `D-AUTH-20`（唯一键不变）· `D-AUTH-05`（action 词表） |
| **Backward Compatibility** | 兼容：CHECK 为新增约束；唯一键**零变更** |

### 2.3 `tools` — **NO CHANGE**

| 项 | 内容 |
|---|---|
| **现状** | `risk_level`(四档) · `timeout_ms` · `retry_policy` · `idempotency_mode` · `audit_policy` · **`approval_required`** · `enabled` … |
| **分类** | **NO CHANGE** |
| **Why** | `D-AUTH-10` 四档风险已在位；`D-AUTH-11` 静态审批下限已在位（`approval_required`）；`D-AUTH-09` 的结构化要求落在 `tool_permissions`（见 2.4），**不需要**改 `tools` |
| **Which Frozen Decision** | `D-AUTH-09` / `D-AUTH-10` / `D-AUTH-11` |
| **Backward Compatibility** | N/A（无变更） |

### 2.4 `tool_permissions` — **ADD（增列）** ← `SC-2`

| 项 | 内容 |
|---|---|
| **现状** | `id` · `tool_id` · `version_id`(NULL) · `permission_id` · `effect`(allow/deny) · `conditions` · `created_at` |
| **分类** | **ADD** |
| **Why** | `D-AUTH-09` 明文：「未来 Tool Authorization **必须能够结构化表达** `Tool + Action/Capability + Scope + Resource Context`」。现表**无** `resource_type` / `action` / `scope` 列 ⇒ 工具声明不可静态验证 ⇒ 存在**权限旁路**面（`TOOL-01`/`TOOL-03`/`TOOL-07`） |
| **Which Frozen Decision** | `D-AUTH-09`（并且 `D-AUTH-17` 将该方向列为"未来允许研究"的两方向之一） |
| **拟定新增列** | `resource_type text NULL` · `action text NULL` · `scope text NULL`（`CHECK (scope IN ('PLATFORM','TENANT','SPACE'))`） |
| **Backward Compatibility** | **兼容**：全部 **NULL 允许**（存量行不受影响）；新增列**不参与** NOT NULL 约束；不改既有列语义 |
| **Migration Need** | ✅ 需新 migration；**不触碰 P09**（本表属 0008） |
| **备选方案（已评估）** | 新增独立表 `tool_capability_requirements` — **不采用**：① 与现有 `*_permissions` 家族不一致；② 增加 JOIN 与一致性风险；③ `D-AUTH-17` 未授权新表。**增列是最小满足方案** |

### 2.5 `roles` — **NO CHANGE**

| 项 | 内容 |
|---|---|
| **分类** | **NO CHANGE** |
| **Why** | `D-AUTH-06` 冻结 `PLATFORM/TENANT/SPACE`，已由 `ck_roles_scope` + `tg_roles_scope_shape` + 3 部分唯一索引强制；`D-AUTH-06` 明确**不新增** `RESOURCE`/`SELF` 为 stored scope |
| **Which Frozen Decision** | `D-AUTH-06` |

### 2.6 `role_permissions` — **NO CHANGE**

| 项 | 内容 |
|---|---|
| **分类** | **NO CHANGE** |
| **Why** | `PK = (role_id, permission_id, effect)` 已支持 allow+deny 并存（`R2-D-14` 的实现前提）；`conditions` 已存在（storage-only，`R2-D-15`）；`D-AUTH-01`/`D-AUTH-07` 不要求 schema 变更 |
| **Which Frozen Decision** | `D-AUTH-01` / `D-AUTH-07` / `D-AUTH-08`；**继承** `R2-D-14` / `R2-D-15` |

### 2.7 `resources` — **NO CHANGE**

| 项 | 内容 |
|---|---|
| **分类** | **NO CHANGE** |
| **Why** | `D-AUTH-04` 明确**不增加** `parent_id`；`D-AUTH-08` 明确 **No implicit resource-parent inheritance**；`resource_relations` 亦**不采用**。7 项 canonical 属性已齐备 |
| **Which Frozen Decision** | `D-AUTH-04` / `D-AUTH-08` |

### 2.8 `agent_permissions` — **NO CHANGE（P09 保护）**

| 项 | 内容 |
|---|---|
| **现状** | `id` · `agent_id` · `version_id` · `permission_id`(NULL) · `tool_id`(NULL) · **`resource_scope`(text, 无 FK/无约束/无触发器)** · `effect` · `conditions` · `created_at` |
| **分类** | **NO CHANGE**（`GAP-11` 裁定后**仍然** NO CHANGE） |
| **Why** | 属 **P09（0011）保护面**（§28）。其 `resource_scope` 为非结构化自由 text（`IMPLEMENTATION GAP-11`），**不得擅改** |
| **Which Frozen Decision** | `D-AUTH-02`（Agent 独立主体，**已被本表满足**）· `D-AUTH-09`（针对 **Tool**，不针对本表）· **`D-AUTH-23`**（`GAP-11` 裁定：**Legacy Opaque** · **NO CHANGE**） |
| **处置** | ✅ **已裁定** —— **`D-AUTH-23`（`FROZEN`，2026-09-23）**：`resource_scope` = **OPAQUE TEXT** · **NOT AUTHORIZATION AUTHORITY**（不构成授权判定）· `ND-A = RESOLVED`（**不追加** `<> ''`）⇒ **`GAP-11 = RESOLVED`**，**本表 schema 动作 = 0** |

---

## 3. §27 Schema Change Set

### 3.1 变更集

| ID | 对象 | 类别 | 内容 | 依据 | P09 影响 |
|---|---|---|---|---|---|
| **SC-1** | `permissions.action` | MODIFY（+CHECK） | `CHECK (action IN (12 项 canonical，**小写形**，`D-AUTH-25`))` | `D-AUTH-05` · `25` | 无 |
| **SC-1b** | `resource_permissions.action` | MODIFY（+CHECK） | 同上（小写形）—— **依据 `D-AUTH-24`**：`D-B14-08` 已由 `D-AUTH-05` 取代，本变更成立 | `D-AUTH-05` · `24` · `25` | 无 |
| **SC-2** | `tool_permissions` | ADD COLUMNS | `resource_type` / `action` / `scope`(含 CHECK) | `D-AUTH-09` | 无（表属 0008） |
| **SC-3** | Module 扩展 action registry | **PROPOSED ONLY** | 载体未定（新表或复用 registry） | `D-AUTH-05` | 无 |
| — | 其余全部 | **NO CHANGE** | — | `D-AUTH-04/06/10/11/17/20` | 无 |

**明确不采用**（`D-AUTH-17` 冻结）：`resources.parent_id` · `resource_relations` · **ACL unique-key redesign**。

### 3.2 §27 迁移数量决策

```text
决策：1 migration
```

**理由**：

| 判定项 | 结论 |
|---|---|
| `0 migration`？ | ❌ 不可：`SC-1`/`SC-2` 是 `D-AUTH-05`/`D-AUTH-09` 的实现前提（"必须能够结构化表达"） |
| `1 migration`？ | ✅ **采用**：两项变更同属"authorization canonical enforcement"这一逻辑单元，且均为**附加式**（CHECK + 可空列），**无跨表依赖** |
| `multiple migrations`？ | ❌ 不必要：SC-3 属 PROPOSED（未决），不应与之捆绑 |

### 3.3 计划中的 migration（**未创建**）

```text
filename == revision : 0012_authz_enforcement
revision id 长度      : 22 字符（≤ 32 上限 ✓ —— 见硬约束 §7.1）
down_revision         : 0011_p09_agent_tool_permission
作用                  : SC-1 + SC-1b（CHECK） + SC-2（增列）
```

**满足（§27 要求）**：

```text
Append-only              : ✅（仅新增 0012，不改任何历史 migration）
Single-head              : ✅（down_revision = 0011，维持单头）
No historical migration edits : ✅（0001–0011 逐字节不动）
```

**不采用**默认名 `0012_authorization.py`（§27 明令禁止默认该命名）。

---

## 4. Migration Plan

### 4.1 upgrade 步骤（计划）

```text
1. 防御性预检：SELECT count(*) FROM permissions WHERE action NOT IN (<12>);  期待 0；非 0 ⇒ RAISE
2. 防御性预检：SELECT count(*) FROM resource_permissions WHERE action NOT IN (<12>);  期待 0；非 0 ⇒ RAISE
3. ALTER TABLE permissions            ADD CONSTRAINT ck_permissions_action_canonical ...
4. ALTER TABLE resource_permissions   ADD CONSTRAINT ck_resource_permissions_action_canonical ...
5. ALTER TABLE tool_permissions       ADD COLUMN resource_type text
6. ALTER TABLE tool_permissions       ADD COLUMN action text
7. ALTER TABLE tool_permissions       ADD COLUMN scope text
8. ALTER TABLE tool_permissions       ADD CONSTRAINT ck_tool_permissions_scope CHECK (scope IN ('PLATFORM','TENANT','SPACE'))
```

**注**：不新增触发器（延续 `R2-D-14`「DB 不做授权解释」）；不新增索引（属 P12 范畴，另行评估）。

### 4.2 downgrade 步骤（计划）

```text
1. ALTER TABLE tool_permissions DROP CONSTRAINT ck_tool_permissions_scope
2. ALTER TABLE tool_permissions DROP COLUMN scope / action / resource_type
3. ALTER TABLE resource_permissions DROP CONSTRAINT ck_resource_permissions_action_canonical
4. ALTER TABLE permissions          DROP CONSTRAINT ck_permissions_action_canonical
```

**可逆性**：全部**完全可逆**（纯附加式变更；无数据迁移、无数据丢失）。

### 4.3 Rollback Plan

| 场景 | 动作 |
|---|---|
| migration 失败 | 事务回滚（Alembic 单事务）；DB 保持 0011 |
| migration 成功后需回退 | `alembic downgrade 0011_p09_agent_tool_permission`（完全可逆） |
| 应用回滚（**F-1**） | 参见 `DEPLOYMENT_AND_RECOVERY.md` **F-1**：严格 `/ready` 相等 + 镜像绑定 revision ⇒ **应用回滚 ≠ 仅回滚镜像**，须配套 DB 处理 |

### 4.4 执行前置（§28/§33）

```text
Migration 执行 = NOT AUTHORIZED
```
必须先取得 **Human Implementation Authorization**（`AUTHORIZATION_IMPLEMENTATION_GATE_REPORT.md`）。

---

## 5. P09 保护（§28）

| 保护项 | 状态 | 证据 |
|---|---|---|
| `0011_p09_agent_tool_permission` 文件 | ✅ 未变 | sha256 `cdaf8383630335db92cfe54f…` |
| `agents` | ✅ NO CHANGE | §2.8 类推（P09 表，本轮零变更） |
| `agent_versions` | ✅ NO CHANGE | 同上 |
| `agent_permissions` | ✅ NO CHANGE | §2.8（`resource_scope` → **`GAP-11` 已由 `D-AUTH-23` 裁定为 Legacy Opaque，本表仍零变更**） |
| `tool_executions` | ✅ NO CHANGE | 同上 |
| P09 触发器 / 约束 / 测试 | ✅ 未触碰 | 本轮零代码、零 migration |

---

## 6. IMPLEMENTATION GAPS（schema 相关，§2 记录不修补）

| # | Gap | 判定 | 处置 |
|---|---|---|---|
| GAP-10 | `permissions.action` / `resource_permissions.action` 自由 text | **可解** | `SC-1` / `SC-1b`（新 migration） |
| GAP-11 | `agent_permissions.resource_scope` 自由 text，**P09 表** | ✅ **RESOLVED** | **`D-AUTH-23`（`FROZEN`）**：**Legacy Opaque** · P09 **零变更** · `ND-A` 不追加 `<> ''` ⇒ **无 schema 动作** |
| GAP-13 | `tool_permissions` 无结构化列 | **可解** | `SC-2`（表属 0008，非 P09） |
| GAP-14 | Module 扩展 action registry 载体未定 | **PROPOSED** | `SC-3` 仅登记；载体属后续裁定 |

---

## 7. 结论

```text
SCHEMA CHANGE SET   = 3 项（SC-1/SC-1b/SC-2 实施；SC-3 仅 PROPOSED）
决策 registry        = D-AUTH total 25 → FROZEN 22 + DEFERRED 3 + SUPERSEDED 0
                      （SC-1b 依据 D-AUTH-24：D-B14-08 → SUPERSEDED by D-AUTH-05）
MIGRATION COUNT     = 1（0012_authz_enforcement，未创建）
APPEND-ONLY         = 满足
SINGLE-HEAD         = 满足
HISTORICAL EDITS    = 0
P09 PROTECTION      = PASS
GAP-11              = RESOLVED（D-AUTH-23 · Legacy Opaque · ND-A 不追加 <> ''）⇒ 本表零变更
MIGRATION AUTHORIZED= NO
```

**END OF AUTHORIZATION SCHEMA IMPACT（2026-09-23）**
