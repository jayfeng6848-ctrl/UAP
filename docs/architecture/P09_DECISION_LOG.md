# P09_DECISION_LOG

**Stage**: P09（= Agent / Tool / Permission 域）· **Status**: **DECISION FREEZE ONLY**
**DESIGN**: **NOT STARTED** · **0011**: **ABSENT** · **IMPLEMENTATION**: NOT STARTED
**Freeze date**: 2026-09-17（OQ 轮：`D-P09-01`～`D-P09-12`）· 2026-09-17（ND 轮：`D-P09-13`～`D-P09-18`）
**Basis**: `P09 HUMAN DECISION FREEZE PREP REPORT`（OQ 轮）· `P09 HUMAN DECISION FREEZE PREP REPORT — ND-01～ND-06`（ND 轮）
**DESIGN WRITE（2026-09-17）**: 已收敛 `U-1` / `U-2` / `U-3` / `NU-07` / `NU-08` / `NU-09` → **§2B**（`DESIGN RESOLVED`，**未新增决策号**）

> 本文档是 P09 的**决策权威载体**。它**只记录已由 Human 明确冻结的决策**。
> 它**不**包含设计细节、不包含 canonical 计数、不包含 migration、不包含任何实现。
> 未冻结事项在 §3 明确列出，**不得**被理解为已冻结。

---

## 0. 编号约定

| 编号 | 含义 |
|---|---|
| `D-P09-01` … `D-P09-12` | 本阶段冻结决策的正式编号（与 PREP 阶段的 `OQ-01` … `OQ-12` **一一对应**） |
| `OQ-01` … `OQ-12` | PREP 阶段的**问题编号**（保留以便追溯） |
| `U-1` / `U-2` / `U-3` | 仍未冻结项（见 §3） |
| `ND-01` … `ND-06` | **DESIGN EVIDENCE GATE** 提出的待裁事项编号（保留以便追溯；与 `D-P09-13` … `D-P09-18` **一一对应**） |
| `NU-07` / `NU-08` / `NU-09` | ND 轮取证发现的**仍未冻结**项（见 §3） |
| `F1` … `F16` | P09 FK 候选清单编号（见 `P09_DEPENDENCY.md` §2） |

---

## 1. 冻结总表（18 / 18）

> `D-P09-01`～`D-P09-12` = OQ 轮（12 项）· `D-P09-13`～`D-P09-18` = ND 轮（6 项）· 详情分别见 §2 与 §2A。

| ID | 对应 OQ | 决策 | 冻结结论摘要 | 状态 |
|---|---|---|---|---|
| `D-P09-01` | OQ-01 | **B** | `tool_executions` **不分区**；PK = `id`；保留 = 90 天 hard delete | **FROZEN — B** |
| `D-P09-02` | OQ-02 | **A** | `tool_executions.tenant_id` = **NOT NULL**；FK → `tenants.id` **RESTRICT** | **FROZEN — A** |
| `D-P09-03` | OQ-03 | — | 9 条 FK 的 `ON DELETE` 逐条冻结（F1/F2/F3/F12 = RESTRICT；F7/F15/F16 = SET NULL；F10/F11 = CASCADE） | **FROZEN** |
| `D-P09-04` | OQ-04 | **A** | 幂等唯一性对象名 = `uq_tool_exec_idem`；类型 = **UNIQUE INDEX**；谓词 `idempotency_key IS NOT NULL`；按 UNIQUE INDEX 计 | **FROZEN — A** |
| `D-P09-05` | OQ-05 | **B** | `agent_permissions` = **2 条 CHECK**（① 至少一列非 NULL；② `effect IN ('allow','deny')`），不得合并 | **FROZEN — B** |
| `D-P09-06` | OQ-06 | **A** | `G/H/I/J` **不属于 P09 implementation**；保持「P09 后」 | **FROZEN — A** |
| `D-P09-07` | OQ-07 | **A** | P09 = **SCHEMA ONLY**；不修改 `agent/` 及其子模块；不实现任何 Runtime | **FROZEN — A** |
| `D-P09-08` | OQ-08 | — | P09 采用 **9 份文档模式**（沿用 B1-5 / B1-6） | **FROZEN** |
| `D-P09-09` | OQ-09 | — | revision = `0011_p09_agent_tool_permission`（filename == revision · ≤32 · 单头 · append-only） | **FROZEN** |
| `D-P09-10` | OQ-10 | — | `ai_request_logs.agent_id` **维持 NO FK**（并维持 `actor_id`/`tenant_id`/`space_id` = NO FK） | **FROZEN** |
| `D-P09-11` | OQ-11 | **A** | deferred FK downgrade 采用 **0005 同构**顺序 | **FROZEN — A** |
| `D-P09-12` | OQ-12 | **A** | 为 `agents` 增加 tenant/space **consistency trigger**（**structural integrity only**） | **FROZEN — A** |
| `D-P09-13` | ND-01 | — | `tool_executions` = **3 条 CHECK**（`status IN (...)` · `attempts >= 1` · `duration_ms >= 0`） | **FROZEN**（ND 轮） |
| `D-P09-14` | ND-02 | **A** | `agent_versions` 沿用 0008 同构：`OLD.status='published'` ⇒ UPDATE / DELETE **均 RAISE**；不允许 published → deprecated / revoked | **FROZEN — A** |
| `D-P09-15` | ND-03 | — | P09 索引权威 = `STEP1B_INDEX_STRATEGY`；交付 **8 个索引对象**；**不**额外补 FK 列索引；`ix_texec_status` 纳入交付；**CORE §12 不回改** | **FROZEN** |
| `D-P09-16` | ND-04 | — | UQ 计数：**UNIQUE CONSTRAINT = 1**（`uq_agent_versions`）· **UNIQUE INDEX = 3**（`uq_agents_key` / `uq_agent_perm` / `uq_tool_exec_idem`）；canonical 必须区分 `pg_constraint` 与 `pg_indexes` | **FROZEN** |
| `D-P09-17` | ND-05 | **A** | **不修改** `0008` 及任何已发布 migration；在 P09 文档登记 `0008:36-37` 措辞漂移；权威 = `TRIGGER_INVENTORY` + `D-P09-06`（G/H/I/J = P09 后） | **FROZEN — A** |
| `D-P09-18` | ND-06 | — | 授权**最小文字补注**：CM ×3（`published_by` / NN-NULL 行 / `uq_agent_perm`）+ CORE ×1（`tool_executions` 2 条 CK）；**已执行** | **FROZEN — 已执行** |

---

## 2. 逐项决策记录

### D-P09-01 — `tool_executions` 分区 【✅ FROZEN — B】

| 项 | 内容 |
|---|---|
| **Problem（OQ-01）** | `tool_executions` 在 P09 是否建为分区表？ |
| **权威来源** | `CORE_DOMAIN_MODEL.md:358` / `:960` · `STEP1B_CONSTRAINT_MATRIX.md:256` · `STEP1A_DESIGN_REPORT.md:69` / `:384`（称「分区」）vs `STEP1B_SCHEMA_DEPENDENCY.md:265` §9 分区表清单（**仅** events / audit_logs / ai_request_logs）· PK 三源一致 = `id` |
| **冲突** | 5 处「分区」表述 vs §9 清单缺列；若分区则分区键必须进 PK（与 PK=`id` 结构性冲突） |
| **Human Decision（2026-09-17）** | **B —— FROZEN**：`tool_executions` **不分区** |
| **冻结事实** | PK = `id` 保持不变；保留策略 = **90 天 hard delete**；**不实现**自动清理 scheduler / job |
| **边界** | 本决策**不**定义 90 天 hard delete 的**执行机制**（见 §3 `U-1`，NOT FROZEN） |
| **连带处理** | 历史文档中 5 处「分区」文字已按 **B-2 授权**做最小修订（见 §5） |

### D-P09-02 — `tool_executions.tenant_id` 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem（OQ-02）** | `tool_executions.tenant_id` 是否 NOT NULL？ |
| **权威来源** | `CORE_DOMAIN_MODEL.md:354`（无 NULL 标记）· `ER_MODEL.md:298`（无 `"nullable"` 注记）· `STEP1B_CONSTRAINT_MATRIX.md:251`（FK 行未列）· `:255`（`tenant_id?（设计为 NN 若按租户隔离）` = 全库唯一未定标记） |
| **冲突** | CORE / ER 的「无标记」可读作 NN；CM 显式标 `?` ⇒ 两读法相反，官方未冻结 |
| **Human Decision（2026-09-17）** | **A —— FROZEN**：`tool_executions.tenant_id` = **NOT NULL** |
| **冻结事实** | FK `tool_executions.tenant_id → tenants.id` **ON DELETE RESTRICT**（= 本日志 D-P09-03 的 F12） |
| **边界** | **不**扩展任何新的租户模型 |

### D-P09-03 — 9 条 FK 的 `ON DELETE` 【✅ FROZEN】

**新冻结（原 UNKNOWN 9 条）**

| # | source → target | nullable | **ON DELETE（FROZEN）** |
|---|---|---|---|
| F1 | `agents.tenant_id → tenants.id` | NN | **RESTRICT** |
| F2 | `agents.space_id → spaces.id` | NULL | **RESTRICT** |
| F3 | `agents.owner_id → users.id` | NN | **RESTRICT** |
| F7 | `agent_versions.published_by → users.id` | NULL | **SET NULL** |
| F10 | `agent_permissions.permission_id → permissions.id` | NULL | **CASCADE** |
| F11 | `agent_permissions.tool_id → tools.id` | NULL | **CASCADE** |
| F12 | `tool_executions.tenant_id → tenants.id` | NN | **RESTRICT** |
| F15 | `tool_executions.agent_id → agents.id` | NULL | **SET NULL** |
| F16 | `tool_executions.actor_id → users.id` | NULL | **SET NULL** |

**保持不变的既有明确决策（7 条，不得改变）**

| # | source → target | **ON DELETE（既有 FROZEN）** |
|---|---|---|
| F4 | `agents.default_route_id → ai_routes.id` | **SET NULL** |
| F5 | `agents.current_version_id → agent_versions.id` | **SET NULL**（deferred FK） |
| F6 | `agent_versions.agent_id → agents.id` | **CASCADE** |
| F8 | `agent_permissions.agent_id → agents.id` | **CASCADE** |
| F9 | `agent_permissions.version_id → agent_versions.id` | **CASCADE** |
| F13 | `tool_executions.tool_id → tools.id` | **RESTRICT** |
| F14 | `tool_executions.tool_version_id → tool_versions.id` | **RESTRICT** |

**语义后果（登记，非新增决策）**：`tool_executions` 的 5 条 FK 中 **CASCADE = 0** ⇒ Agent / User 被删除时**不会**级联清除历史 execution（F15/F16 = SET NULL，F12/F13/F14 = RESTRICT）。

> **登记（不阻断，见 §3）**：F3 采用 RESTRICT 与既有先例 `spaces.owner_id` / `resources.owner_id`（均 SET NULL）**方向相反** —— 属 Human 决策与先例的分叉，已登记备查，**不代表**先例被推翻。

### D-P09-04 — 幂等唯一性对象 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem（OQ-04）** | `(tool_id, idempotency_key)` 部分唯一性的正式名与计数形式？ |
| **权威来源** | `STEP1B_CONSTRAINT_MATRIX.md:252`（`uq_tool_exec_idem …`）· `STEP1B_INDEX_STRATEGY.md:128`（`ix_texec_idem …`）· 同文件 `:7`（自述「部分唯一索引在 CONSTRAINT_MATRIX 列出，本文档不重复」）· D-B15-06 = A（区分 constraint-form / index-form；表达式唯一不计入 UNIQUE CONSTRAINT） |
| **冲突** | 同一对象两个名字；INDEX_STRATEGY 自相矛盾 |
| **Human Decision（2026-09-17）** | **A —— FROZEN**：正式对象名 = **`uq_tool_exec_idem`**；对象类型 = **UNIQUE INDEX**；谓词 = `idempotency_key IS NOT NULL`；**按 UNIQUE INDEX 计数** |
| **边界** | **不得**伪装为 UNIQUE CONSTRAINT；**不得**同时保留两个实际对象 |
| **连带处理** | `STEP1B_INDEX_STRATEGY.md:128` 已按 B-2 授权更名为 `uq_tool_exec_idem` 并标注 UNIQUE INDEX |

### D-P09-05 — `agent_permissions` CHECK 【✅ FROZEN — B】

| 项 | 内容 |
|---|---|
| **Problem（OQ-05）** | `agent_permissions` 的 CK 计为 1 条还是 2 条？ |
| **权威来源** | `CORE_DOMAIN_MODEL.md:314`（仅「至少一列非 NULL」）vs `STEP1B_CONSTRAINT_MATRIX.md:293`（「至少一列非 NULL」+ `effect IN ('allow','deny')`） |
| **冲突** | 1 vs 2 |
| **Human Decision（2026-09-17）** | **B —— FROZEN**：**2 条 CHECK** |
| **冻结事实** | **CHECK-1** = `permission_id IS NOT NULL OR tool_id IS NOT NULL OR resource_scope IS NOT NULL`<br>**CHECK-2** = `effect IN ('allow', 'deny')` |
| **边界** | **不得**合并为一条 CHECK；canonical 计数 = **2 CHECK constraints** |
| **未冻结** | 两条 CHECK 的**正式约束名** → **`命名待 P09 DESIGN 确定`**（见 §3 `U-3`） |

### D-P09-06 — `G/H/I/J` 归属 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem（OQ-06）** | `tg_acl_subject_exists` / `tg_acl_user_hard_delete` / `tg_acl_role_delete_block` / `tg_agent_acl_expire` 是否属 P09？ |
| **权威来源** | `STEP1B_TRIGGER_INVENTORY.md:200-203`（§2「最早 phase」列 = **P09 后** ×4）· `:124/:136/:147/:158`（各条 dependency）· `:214` · `STEP1B_SCHEMA_DEPENDENCY.md:237-239` · **`:241`（该列语义 = trigger「最早可挂的 phase」）** · `:176`③ · `B1-4_DECISION_LOG.md:28/:50`（D-B14-02 = A）· `B1-4_DEPENDENCY.md:71-82` |
| **冲突** | 「P09 后」的字面（严格晚于 P09）vs B1-4 旁注「实际按 P11 集中」（旁注非独立冻结条款） |
| **Human Decision（2026-09-17）** | **A —— FROZEN**：**G/H/I/J 不属于 P09 implementation**；P09 **不创建**这 4 个 ACL cross-table trigger；保持「**P09 后**」 |
| **边界** | **不得**移入 P09 · **不得**移入 P10 · **不得**创建 P11 migration · **不得**创建 trigger / function |

### D-P09-07 — `agent/` 代码层 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem（OQ-07）** | P09 是否触及 `agent/` 代码层？ |
| **权威来源** | `agent/`（11 tracked 文件，`72ade9f` = `UAP-V0.1.0-INIT`，全部 Protocol / frozen dataclass）· `ARCHITECTURE.md:13` / `:51-58` · `DEPENDENCY_RULES.md §4` · `tests/architecture/test_dependency_rules.py:123-131` · `STEP1A_DESIGN_REPORT.md:560` |
| **冲突** | 无（P09 是否落代码层此前未规定） |
| **Human Decision（2026-09-17）** | **A —— FROZEN**：**P09 = SCHEMA ONLY** |
| **冻结事实** | P09 **不修改** `agent/` / `runtime/` / `registry/` / `tools/` / `memory/` / `workflow/`（STEP 0 骨架**保持原样**）；**不实现** Agent Runtime / Agent Registry Runtime / Tool Runtime / Memory Runtime / Workflow Runtime |

### D-P09-08 — P09 文档集 【✅ FROZEN】

| 项 | 内容 |
|---|---|
| **Problem（OQ-08）** | P09 采用何种文档集？ |
| **权威来源** | `B1-5_*` = 9 份（tracked）· `B1-6_*` = 9 份（tracked；`D-B16-09 = A` 沿用）· `B1-4_*` = 12 份（tracked） |
| **Human Decision（2026-09-17）** | **FROZEN**：P09 沿用 **B1-5 / B1-6 的 9-document mode**（**固定 9 份**） |
| **冻结事实** | 本阶段实际创建 9 份（见 §6）；**不恢复** B1-4 的 12-document mode；**不创造**第 10–12 份 |

### D-P09-09 — migration revision 【✅ FROZEN】

| 项 | 内容 |
|---|---|
| **Problem（OQ-09）** | `0011` 的 revision id 字面？ |
| **权威来源** | `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md §7:83/:85/:86` · `B1-6_MIGRATION_PLAN.md:15/:16` · `0009_timestamp_precision.py:35` |
| **Human Decision（2026-09-17）** | **FROZEN**：`revision = 0011_p09_agent_tool_permission` · `filename = 0011_p09_agent_tool_permission.py` · `filename == revision` · ≤ 32 字符 · single Alembic head · append-only |
| **核对** | 长度 **30 ≤ 32** ✅ · 格式 `<4位序号>_<snake_case>` ✅ · 无重名 ✅ · 当前 head = `0010_b1_6_ai_gateway`（单头）✅ |
| **边界（强制）** | 本阶段**只冻结 identity**；**不得创建**该 migration 文件；**不得执行** migration |

### D-P09-10 — `ai_request_logs.agent_id` 【✅ FROZEN】

| 项 | 内容 |
|---|---|
| **Problem（OQ-10）** | P09 是否为 `ai_request_logs.agent_id` 增加 FK？ |
| **权威来源** | `B1-6_DECISION_LOG` §D-B16-03（**FROZEN — A**）· `B1-6_DEPENDENCY.md:179`（若未来要加，属**新决策**，须显式授权）· `tests/integration/test_ai_gateway_schema.py:455-470`（AF5 断言） |
| **Human Decision（2026-09-17）** | **FROZEN**：**维持 NO FK** |
| **冻结事实** | `ai_request_logs.agent_id` = **NO FOREIGN KEY**；同时维持 `actor_id` = NO FK · `tenant_id` = NO FK · `space_id` = NO FK |
| **边界** | **禁止**通过 P09 顺手增加 `agent_id → agents.id`；若未来要增加，必须作为**新的 Human Decision**（本阶段**不启动**新决策） |

### D-P09-11 — deferred FK downgrade 顺序 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem（OQ-11）** | `fk_agents_current_version` 的 downgrade 顺序为何？ |
| **权威来源（升级侧）** | `STEP1B_SCHEMA_DEPENDENCY.md §4.1:124-134`（deferred FK 三步；约束名 `fk_agents_current_version`；`ON DELETE SET NULL`）· `:136` 的「Phase 08」已由 `D-B16-08 = C` 判为陈旧引用，正式归属 **P09** |
| **权威来源（降级侧先例）** | `0005_b1_3_authorization.py`：upgrade `ADD CONSTRAINT`（`:431-436`）；downgrade **先** `DROP CONSTRAINT IF EXISTS`（`:519-520`）再 `DROP TABLE roles`（`:37`） |
| **Human Decision（2026-09-17）** | **A —— FROZEN**：采用 **0005 同构**模式 |
| **冻结事实** | **Upgrade**：`agents` → `agent_versions` → `ADD fk_agents_current_version`<br>**Downgrade**：`DROP fk_agents_current_version` → `DROP agent_versions` → `DROP agents` |
| **边界** | `fk_agents_current_version` 必须保持 `ON DELETE SET NULL`；**不得**修改其升级侧既有定义 |

### D-P09-12 — `agents` tenant/space consistency 【✅ FROZEN — A】

| 项 | 内容 |
|---|---|
| **Problem（OQ-12）** | 是否为 `agents` 建立 tenant/space 一致性约束？ |
| **权威来源** | `STEP1B_CONSTRAINT_MATRIX.md:169/:171`（resources 同形 + `tg_resources_tenant_space_consistency`）· `STEP1B_TRIGGER_INVENTORY.md:86-93`（F2 定义）· `B1-4_DECISION_LOG.md:152/:213`（D-B14-10 = A-1 · P06）· `STEP1B_CONSTRAINT_MATRIX.md:267`（agents FK 行） |
| **冲突** | `resources` 与 `agents` 同形，但 agents 此前**无**对应 trigger（先例 ≠ 冻结要求） |
| **Human Decision（2026-09-17）** | **A —— FROZEN**：为 `agents` **增加** tenant/space consistency trigger |
| **冻结语义** | `agents.space_id IS NULL` → **允许**；`agents.space_id IS NOT NULL` → 必须满足 `agents.tenant_id = spaces.tenant_id` |
| **边界（强制）** | 该 trigger **只负责 STRUCTURAL INTEGRITY**；**绝对不得**在 trigger 中解释 ALLOW / DENY / 权限继承 / 角色 / 资源授权 / ACL decision —— 授权解释仍属 **Authorization Layer** |
| **未冻结** | 该 trigger 的**正式名称** → 见 §3 `U-2` |

---

## 2A. ND 轮冻结（`D-P09-13` ～ `D-P09-18`，2026-09-17）

> 本轮冻结对象 = DESIGN EVIDENCE GATE 提出的 `ND-01` ～ `ND-06`。
> 它们**不替代、不修改** `D-P09-01` ～ `D-P09-12`（本轮与后者无冲突）。

### D-P09-13 — `tool_executions` 的 CHECK 数 【✅ FROZEN — ND-01】

| 项 | 内容 |
|---|---|
| **Problem（ND-01）** | CK 计为 1 条（`CORE:357`）还是 3 条（`CM:253`）？ |
| **权威来源** | `CORE:357`（1 条）vs `CM:253`（3 条）· `ER:296-306` 无 CK 行 · `STEP1A:69` 无 CK |
| **实作先例** | `0007` = 6 CK（= CM 6）· `0008` = 5 CK（= CM 5）· `0010` = 8 CK（= CM 8）—— 六次实施**全部采用 CM 超集**；`ck_tools_timeout`（`timeout_ms BETWEEN 100 AND 600000`，0008:115）为同类**数值域 CK**先例；OQ-05（CORE 1 vs CM 2）已由 Human 裁为 CM 超集 |
| **Human Decision（2026-09-17）** | **3 条 CHECK** |
| **冻结事实** | ① `status IN ('running','succeeded','failed','denied','timeout')`<br>② `attempts >= 1`<br>③ `duration_ms >= 0` |
| **语义边界** | `duration_ms >= 0` 对 NULL 返回 NULL ⇒ `duration_ms IS NULL` 行**通过**（与 `duration_ms NULL` 一致）；`attempts` 为 NN（`CM:254`）⇒ `attempts >= 1` 为有效域收紧 |
| **未冻结** | 3 条 CHECK 的**约束名**（与 `U-3` 同族，见 §3） |
| **连带处理** | `CORE:357` 已按 `D-P09-18` 补注（标注 `D-P09-13`）；`CM:253` 无需修改 |

### D-P09-14 — `agent_versions` 的 `published` 状态迁移 【✅ FROZEN — A / ND-02】

| 项 | 内容 |
|---|---|
| **Problem（ND-02）** | `status='published'` 行是否允许 `published → deprecated` / `published → revoked` 迁移？ |
| **权威来源** | `CORE:303` · `CORE:957`（§13 保留策略表：immutable，只能 deprecate/revoke）· `CM:284` · `TRIGGER_INVENTORY:164/:204`（K 与 tool_versions 共用名 · 表建时）· `0008` 实作（`OLD.status='published'` 一律 RAISE）· **`B1-5_SCHEMA_DESIGN:127`**（「deprecate/revoke 走应用层状态迁移（**后续阶段**）」）· `B1-5_TEST_MATRIX:143 TDF6`（后续） |
| **Human Decision（2026-09-17）** | **A —— 沿用 `0008` 同构语义** |
| **冻结事实** | `agent_versions` 中 `OLD.status='published'` 时：**UPDATE = RAISE** · **DELETE = RAISE** · **不允许** published → deprecated · **不允许** published → revoked |
| **归属** | deprecate / revoke 属**后续应用层治理阶段**（P09 不实现，与 `D-P09-07` = SCHEMA ONLY 一致） |
| **层级澄清（非新决策）** | `CORE:303` = trigger / 不变式条款；`CORE:957` = **§13 保留策略分类**（immutable vs hard delete / soft delete）。二者层级不同，**不构成实质矛盾**：`CORE:957` 描述"不做物理删除、退役走治理动作"，该动作的 DB 可达性属后续阶段 |
| **边界（强制）** | **不得修改 `0008_b1_5_tool_registry.py`**；不得为 `agent_versions` 设状态迁移豁免（否则与共用 trigger 名 `tg_version_immutable` 的语义一致性冲突） |

### D-P09-15 — P09 索引清单权威与 8 个索引对象 【✅ FROZEN — ND-03】

| 项 | 内容 |
|---|---|
| **Problem（ND-03）** | P09 索引清单以何为准？是否补 FK 列索引？ |
| **权威来源** | `CORE §12:1022-1026`（P09 仅 4 行，无 agent_permissions 行）vs `STEP1B_INDEX_STRATEGY:103-131`（逐表 + 用途 + §4 命名规范 + §5 三分汇总）· `INDEX_STRATEGY:202`（FK 反查补索引**进入 P12**） |
| **决定性先例** | `0010` 实作 5 个非 PK 索引对象（`uq_ai_providers_key` / `uq_ai_models` / `uq_ai_routes` / `uq_ai_policies` / `ix_airl_tenant_occurred`），而 `CORE §12` 仅列 2 条 ⇒ **实作采用 INDEX_STRATEGY 超集，CORE §12 为不完整摘要** |
| **Human Decision（2026-09-17）** | **`STEP1B_INDEX_STRATEGY` = P09 最终索引清单权威**；**交付 8 个索引对象** |
| **冻结事实（8 对象）** | ① `uq_agents_key`（部分唯一）② `ix_agents_tenant_status` ③ `uq_agent_versions`（唯一约束）④ `ix_ap_agent` ⑤ `uq_agent_perm`（表达式唯一）⑥ `uq_tool_exec_idem`（部分唯一）⑦ `ix_texec_tenant_created` ⑧ `ix_texec_status` |
| **不补** | **不额外补 FK 列索引**（`INDEX_STRATEGY §3:200` 将 `agents.owner_id` 标 P3；`§3:202` 明示 FK 反查补索引进入 **P12**） |
| **子项** | `ix_texec_status`（用途注明"若实现重试 job 需要"）**纳入本次 P09 交付** |
| **CORE §12** | **不回改**；由 P09 文档（本文档 + `P09_SCHEMA_DESIGN.md`）明确 `INDEX_STRATEGY` 为 P09 索引权威 |

### D-P09-16 — UQ constraint / index 计数口径 【✅ FROZEN — ND-04】

| 项 | 内容 |
|---|---|
| **Problem（ND-04）** | P09 的 UQ 如何计数（constraint-form / index-form）？ |
| **权威来源** | `D-B15-06 = A`（FROZEN：`UNIQUE CONSTRAINT = 1` · `UNIQUE INDEX = 3`；表达式唯一不计入 UNIQUE CONSTRAINT；以 `pg_constraint` / `pg_indexes` 实测为准）· PG 结构规则：部分唯一（`WHERE`）与表达式唯一（`COALESCE`）只能是 index |
| **Human Decision（2026-09-17）** | **UNIQUE CONSTRAINT = 1** · **UNIQUE INDEX = 3** |
| **冻结事实** | **UNIQUE CONSTRAINT** = `uq_agent_versions`（1）<br>**UNIQUE INDEX** = `uq_agents_key` · `uq_agent_perm` · `uq_tool_exec_idem`（3） |
| **计数要求（强制）** | canonical 统计**必须区分** `pg_constraint` 与 `pg_indexes` |
| **与既有决策关系** | 与 `D-B15-06` 完全同构（B1-5 亦为 1 + 3）；与 `D-P09-04` 一致（`uq_tool_exec_idem` 计 UNIQUE INDEX） |
| **未冻结** | canonical **总计数**与编号空间（仍属 P09 DESIGN 交付物，见 §3） |

### D-P09-17 — `0008` 历史措辞漂移的处置 【✅ FROZEN — A / ND-05】

| 项 | 内容 |
|---|---|
| **Problem（ND-05）** | `0008_b1_5_tool_registry.py:36-37` 写「不实施 G/H/I/J（…）—— **仍属 P09**」，与 `D-P09-06 = A`（G/H/I/J = **P09 后**）字面矛盾 |
| **权威来源** | `TRIGGER_INVENTORY:200-203`（最早 phase 列 = P09 后 ×4）· `SCHEMA_DEPENDENCY:237-241` · `D-B14-02 = A` · `D-P09-06 = A` · `MIGRATION_IMPLEMENTATION_CONTRACT §7:86`（已发布 revision 永不改写） |
| **Human Decision（2026-09-17）** | **A —— 不回改 `0008`**（亦不修改任何已发布 migration） |
| **冻结事实** | ① 不修改 `0008_b1_5_tool_registry.py`；② 不修改任何已发布 migration；③ **在 P09 文档中登记该措辞漂移**（见 §4A）；④ 权威解释 = `TRIGGER_INVENTORY` + `D-P09-06 = A` ⇒ **G/H/I/J 属于 P09 后**；⑤ 处置方式与 `D-B16-08 = C`（B1-6 陈旧引用）**同构** —— 由后续阶段文档加注承载说明义务 |
| **物理后果** | 该处为 docstring 注释，**不产生任何 DDL / 结构后果** |

### D-P09-18 — ND-06 最小文字补注包 【✅ FROZEN — 已执行】

| 项 | 内容 |
|---|---|
| **Problem（ND-06）** | 是否授权对 CM / CORE 做最小文字补注以消除文档内部不一致？ |
| **Human Decision（2026-09-17）** | **授权**（含 7 条约束） |
| **授权范围（4 处，已执行）** | ① `CM` `agent_versions` **NULL 列表补 `published_by`**<br>② `CM` `agent_permissions` 段**增加 NN / NULL 列表**（NN = id, agent_id, effect, created_at；NULL = version_id, permission_id, tool_id, resource_scope, conditions）<br>③ `CM` 该表 UQ 行**补名 `uq_agent_perm`**<br>④ `CORE` `tool_executions` CK **补 `attempts >= 1` 与 `duration_ms >= 0`**（标注 `D-P09-13`） |
| **约束（强制）** | ⑤ 所有补注**必须保持既有语义，不得新增设计**<br>⑥ **不修改已发布 migration**<br>⑦ **不修改代码和测试** |
| **执行结果** | **4/4 完成**，全部为**单位置唯一命中**替换；补注内容均由既有 `CORE` 定义派生，**未引入任何新设计** |

---

## 2B. DESIGN RESOLVED 登记（2026-09-17 · **非 Human Decision**）

> 本节登记 DESIGN WRITE 轮对六项 DESIGN UNKNOWN 的收敛结果。
> **重要**：`DESIGN RESOLVED` **不等于** `HUMAN DECISION FROZEN`；本节**未新增任何 `D-P09-*` 决策号**，
> 也不修改 `D-P09-01` ～ `D-P09-18`。实现依据 = 冻结决策 + 历史先例 + 显式架构规则。

| UNKNOWN | 收敛结果 | 依据 |
|---|---|---|
| `U-1` retention | policy = 90 天 hard delete · **eligibility = `created_at < now() - interval '90 days'`** · **executor = 人工运维（不属 P09）** | `D-P09-01` · `CORE:960/:965` · `ix_texec_tenant_created`（唯一范围索引）· `D-3 = D` 先例 |
| `U-2` consistency trigger | trigger = `tg_agents_tenant_space_consistency` · function = `enforce_agents_tenant_space_consistency()` · **BEFORE INSERT OR UPDATE** · NULL 放行 / mismatch RAISE / 只做结构完整性 | `D-P09-12` · F2 先例（0007:232-236） |
| `U-3` CK 名称（8） | `ck_agents_status` · `ck_agents_max_risk_level` · `ck_agent_versions_status` · `ck_agent_permissions_scope_target` · `ck_agent_permissions_effect` · `ck_tool_executions_status` · `ck_tool_executions_attempts` · `ck_tool_executions_duration` | `D-P09-05` · `D-P09-13` · `ck_<table>_<semantic>` 先例 |
| `NU-07` immutability function | function = `enforce_agent_versions_immutable()`（**独立函数**）· trigger = `tg_version_immutable`（共用名）· BEFORE UPDATE OR DELETE · published 行双拒、无豁免 | `D-P09-14` · `D-B15-03` · **不修改 0008** |
| `NU-08` 列类型 / DEFAULT | 54 列逐项收敛：uuid 20 · text 16 · timestamptz(3) 9 · jsonb 6 · integer 3；DEFAULT 仅 `id → uap_uuid_v7()`、`created_at/updated_at → now()`；时间列一律 `_TS` | `CORE` / `CM` 列清单 · `_TS`（0010:86）· 0008/0010 列级先例 |
| `NU-09` CK-1 边界 | `NULL` ⇒ 不满足；`''` / `'   '` ⇒ **满足**（PG `IS NOT NULL` 语义，**不** trim/normalize）；`conditions` 不参与 CK-1 | `D-P09-05` 冻结文本 · 全库无 trim 先例 |

**全部细节见 `P09_SCHEMA_DESIGN.md` §2B**（2B.1 列矩阵 · 2B.2 对象命名表 · 2B.3～2B.7 逐项设计 · 2B.8 canonical · 2B.9 待决项）。

**DESIGN WRITE 新增的待决项（不得自行冻结）**

| ID | 问题 | 状态 |
|---|---|---|
| `ND-A` | 是否对 `resource_scope` 追加 `<> ''`（拒绝空串）—— 会改动 `D-P09-05` 冻结文本 | **HUMAN DECISION REQUIRED** |
| `ND-B` | `fk_agents_current_version` 是否带 `DEFERRABLE` —— 与 `D-P09-11`「不得修改升级侧定义」相关 | **HUMAN DECISION REQUIRED** |
| `NU-C` | retention 自动化执行器是否立项 | `DESIGN DEFERRED` |
| `NU-D` | 一致性 trigger 的存在性 RAISE 与 FK 并存（沿用 F2 同构） | DESIGN RESOLVED（登记备查） |

---

## 3. NOT FROZEN（不得自行决定）

| ID | 未冻结事项 | 说明 | 处置 |
|---|---|---|---|
| **U-1** | `tool_executions` 90 天 hard delete 的**执行机制** | D-P09-01 定为不分区后，该保留策略由何承载（手工运维 / 未来 job）**未冻结**；本阶段**不得**借修订历史文档之机扩展 retention 执行机制 | 待 **P09 DESIGN** 澄清 |
| **U-2** | `agents` tenant/space consistency trigger 的**正式名称** | D-P09-12 只冻结语义，未给名称；既有命名惯例为 `tg_<table>_<语义>`，但本阶段**不自行冻结** | 待 **P09 DESIGN** 确定 |
| **U-3** | `agent_permissions` 两条 CHECK 的**正式名称** | D-P09-05 已明示「命名待 P09 DESIGN 确定」；D-P09-13 对 `tool_executions` 的 3 条 CHECK 保持同一口径（**名称未冻结**） | 待 **P09 DESIGN** 确定 |
| **NU-07** | `tg_version_immutable` 的 **trigger 函数名**（`agent_versions` 侧） | D-B15-03 = A 只冻结 **trigger 名共用**；`0008` 的函数名 `enforce_tool_versions_immutable()` 内嵌表名且**不得修改 0008** | 待 **P09 DESIGN**（任何候选名**不得**视为冻结） |
| **NU-08** | **列类型 / DEFAULT 逐项** 与 **P09 时间列清单** | `CM` 不承载列类型；P09 时间列清单未冻结（平台铁律 = `timestamptz(3)`，`CORE:923`） | 待 **P09 DESIGN** |
| **NU-09** | `agent_permissions` CK-1 的**空串 / NULL 边界** | `resource_scope = ''` 可通过 `IS NOT NULL`；`effect = NULL` 时 `IN` 返回 NULL ⇒ 该 CK 通过 | 待 **P09 DESIGN** |

> **已由 ND 轮关闭**（移出 NOT FROZEN）：P09 **索引清单与 8 个索引对象命名**（D-P09-15）·
> **UQ constraint / index 计数口径**（D-P09-16）· `tool_executions` **CK 数**（D-P09-13）·
> `agent_versions` **published 迁移语义**（D-P09-14）· `0008` **措辞漂移处置**（D-P09-17）·
> **CM / CORE 补注授权**（D-P09-18）。
>
> **已由 DESIGN WRITE 轮收敛**（见 §2B，`DESIGN RESOLVED` —— 非 Human Decision）：
> `U-1`（retention policy + eligibility）· `U-2`（trigger 名与语义）· `U-3`（8 个 CK 名）·
> `NU-07`（不可变性函数名）· `NU-08`（54 列类型 / DEFAULT / 时间列清单）· `NU-09`（CK-1 边界）。
>
> 仍**未冻结 / 待决**：canonical **总计数**与编号空间 · `ND-A`（`resource_scope <> ''`）·
> `ND-B`（`DEFERRABLE`）· `NU-C`（retention 自动化执行器，`DESIGN DEFERRED`）。

---

## 4. DEFERRED（已明确属后续阶段）

| 事项 | 归属 | 依据 |
|---|---|---|
| `G/H/I/J` 四件 ACL trigger | 「P09 后」（实际 P11 集中） | `TRIGGER_INVENTORY.md:200-203` · `SCHEMA_DEPENDENCY.md:241` · `D-B14-02 = A` |
| `events` / `audit_logs` | **P10** | `SCHEMA_DEPENDENCY.md:171` |
| Audit 写入（ACL / 工具高危操作） | **P10** | `B1-4_DECISION_LOG.md:99-100`（D-B14-07 = FROZEN-defer） |
| `acl_subject_types` 的 `agent` 行 seed | **P13** | `STEP1B_SEED_STRATEGY.md:111-117` · `D-B14-01 = A` |
| `ai_request_logs.agent_id` 加 FK | **新决策**（未排期） | `D-B16-03` · `B1-6_DEPENDENCY.md:179` |
| Agent Runtime / 具体 Agent·Tool 实现 | 未排期（不在 STEP 1-B） | `STEP1A_DESIGN_REPORT.md:560` · `D-P09-07` |
| 分区维护自动化（预建 / 清理） | 未来 operational / runtime 阶段 | `B1-6` RF5（D-3 = D） |

---

## 4A. 历史措辞漂移登记（ND-05 / `D-P09-17`）

> 本段承载 `D-P09-17` 的**说明义务**（与 `D-B16-08 = C` 的 B1-6 陈旧引用处置**同构**：不回改旧文档，
> 由后续阶段文档加注承载）。

| 项 | 内容 |
|---|---|
| **位置** | `migrations_alembic/versions/0008_b1_5_tool_registry.py:36-37` |
| **漂移原文** | 「不实施 G/H/I/J（`tg_acl_subject_exists` / `tg_acl_user_hard_delete` / `tg_acl_role_delete_block` / `tg_agent_acl_expire`）—— **仍属 P09**」 |
| **权威表述** | `STEP1B_TRIGGER_INVENTORY.md:200-203`（最早 phase 列 = **P09 后** ×4）· `STEP1B_SCHEMA_DEPENDENCY.md:237-241` · `D-B14-02 = A` · **`D-P09-06 = A`** |
| **正确结论** | **G/H/I/J 属于「P09 后」**（**不属于** P09 implementation） |
| **处置** | **不修改 `0008`**（`MIGRATION_IMPLEMENTATION_CONTRACT §7:86`「已发布 revision 永不改写」）；亦不修改 `0007`（其 `:18`「最早 P09 后」表述**正确**）；**本登记即为说明义务的履行** |
| **物理后果** | 该处为 docstring 注释 ⇒ **无 DDL / 结构后果**；不改变 P09 范围、不改变 `D-P09-06` |
| **同族旁证** | `0008:17`（`tg_version_immutable` 与 P09 共用）与 `0008:38`（`tool_executions` 属 P09）表述**正确**，无需登记 |

---

## 5. B-1 / B-2 解锁与执行记录（2026-09-17）

**B-1 解锁（创建 P09 承载文档）**：Human 授权创建 P09 的 **9 份**正式决策承载文档（固定 9 份）。
本阶段实际创建清单见 §6。

**B-2 解锁（历史文档最小必要性修订）**：Human 授权对 PREP 报告 §7 列出的 6 组冲突做**最小必要文字修订**。
修订清单与精确位置见 §6；**未修改**任何其它内容，**未**借机扩展 retention 执行机制或租户模型。

**B-1 / B-2 均未触及**：`0001`–`0010` migration · B1-6 implementation（`0010_b1_6_ai_gateway.py`）· B1-6 测试 ·
B1-6 Frozen Decisions（`D-B16-01`–`D-B16-11`）· `agent/` · Core / Domain / intelligence · 任何测试 · DB。

---

## 6. 本轮文档变更清单

**新建（9 份，P09 决策承载）**

| # | 文件 | 承载的决策 |
|---|---|---|
| 1 | `P09_DECISION_LOG.md`（本文档） | 全部 12 项的权威记录 |
| 2 | `P09_HUMAN_DECISION_FREEZE_PACKAGE.md` | 12 项决策证据包 + Not Frozen + Deferred |
| 3 | `P09_SCOPE.md` | `D-P09-06` · `D-P09-07` · `D-P09-08` |
| 4 | `P09_DEPENDENCY.md` | `D-P09-02` · `D-P09-03`（F1–F16）· `D-P09-10` · `D-P09-11` |
| 5 | `P09_SCHEMA_DESIGN.md` | `D-P09-01` · `D-P09-02` · `D-P09-04` · `D-P09-05` · `D-P09-12` |
| 6 | `P09_SECURITY_REVIEW.md` | `D-P09-12` 边界 · `D-P09-10` · 历史记录保护 · 零 seed |
| 7 | `P09_API_DESIGN.md` | `D-P09-07`（SCHEMA ONLY ⇒ API = 0） |
| 8 | `P09_TEST_MATRIX.md` | canonical = **NOT FROZEN**；决策派生断言清单 |
| 9 | `P09_MIGRATION_PLAN.md` | `D-P09-09` · `D-P09-11` · `D-P09-01`（无分区 DDL） |

**修订（历史文档，B-2 授权范围）**

| 文件 | 位置 | 修订内容 |
|---|---|---|
| `CORE_DOMAIN_MODEL.md` | `:358` · `:960` | 「分区」→ **不分区**（`D-P09-01`） |
| `CORE_DOMAIN_MODEL.md` | `:314` | CK 行补 `effect IN ('allow','deny')`（`D-P09-05` = 2 条 CHECK；名称待 DESIGN） |
| `CORE_DOMAIN_MODEL.md` | `:288` · `:299` · `:311` · `:354` | 9 条 FK 的 `ON DELETE` 补注（`D-P09-03`） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:256` | 「分区 90 天 hard delete」→ **不分区**（`D-P09-01`） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:254` · `:255` | `tenant_id` 移出 NULL 列表、补入 NN 列表（`D-P09-02`） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:251` | 补 `tenant_id → tenants.id R`（NN）；F15/F16 补 SN（`D-P09-02` · `D-P09-03`） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:267` | F1/F2/F3 补 `R`（`D-P09-03`） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:279` | `published_by` 补 `SN`（`D-P09-03` F7） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:291` | `permission_id` / `tool_id` 补 `C`（`D-P09-03` F10/F11） |
| `STEP1B_CONSTRAINT_MATRIX.md` | `:270` | NN 列表补 `owner_id`（CM 内部缺口修复 · `D-P09-03` F3） |
| `STEP1B_INDEX_STRATEGY.md` | `:128` | `ix_texec_idem` → **`uq_tool_exec_idem`**，标注 **UNIQUE INDEX**（`D-P09-04`） |
| `STEP1A_DESIGN_REPORT.md` | `:69` · `:384` | 「分区」→ **不分区**（仅 `tool_executions`；`events` / `ai_request_logs` 分区语义不变）（`D-P09-01`） |

**ND 轮文档变更（2026-09-17 · `D-P09-13` ～ `D-P09-18`）**

| 类别 | 文件 | 变更 |
|---|---|---|
| 权威载体 | `P09_DECISION_LOG.md` | 新增 §2A（`D-P09-13`～`D-P09-18` 逐项记录）· §4A（`0008` 措辞漂移登记）· §1/§3/§6/§7 同步 |
| 承载文档同步 | `P09_SCHEMA_DESIGN.md` | CK 数（3）· 索引清单（8）与权威归属 · UQ 计数口径 · NOT FROZEN 收敛 |
| 承载文档同步 | `P09_DEPENDENCY.md` | 索引权威 · `0008` 漂移登记指针 · NOT FROZEN 收敛 |
| 承载文档同步 | `P09_MIGRATION_PLAN.md` | CK 3 / 索引 8 / `ix_texec_status` 纳入 · 验证清单增补 |
| 承载文档同步 | `P09_TEST_MATRIX.md` | 测试义务增补（CK 3 · 索引 8 · UQ 分类口径） |
| 承载文档同步 | `P09_SCOPE.md` | IN SCOPE 索引项收敛为「8 对象 · 权威 = INDEX_STRATEGY」· 可追溯性补 ND 映射 |
| 承载文档同步 | `P09_HUMAN_DECISION_FREEZE_PACKAGE.md` | 新增 §2A（ND 证据包）· NOT FROZEN / Gate 同步 |
| 承载文档同步 | `P09_SECURITY_REVIEW.md` | 登记项增补（`D-P09-13` 两条数值域 CK；仍不含授权语义） |
| 未修改 | `P09_API_DESIGN.md` | API = 0 不受 ND 轮影响（无需同步） |
| **历史文档补注** | `STEP1B_CONSTRAINT_MATRIX.md` | 3 处（`agent_versions` NULL 补 `published_by` · `agent_permissions` 增 NN/NULL · UQ 补名 `uq_agent_perm`）—— `D-P09-18` 授权 |
| **历史文档补注** | `CORE_DOMAIN_MODEL.md` | 1 处（`tool_executions` CK 补 `attempts >= 1` / `duration_ms >= 0`）—— `D-P09-18` 授权 |
| **未修改（强制）** | `0008_b1_5_tool_registry.py` · `0001`–`0007` · `0009` · `0010` · 任何测试 · 任何代码 | `D-P09-17` / ND-06 约束 ⑥⑦ |

---

## 7. Gate

```
P09 HUMAN DECISION FREEZE = COMPLETE
DECISIONS RECEIVED = 18/18（OQ 轮 12 + ND 轮 6）
DECISIONS WRITTEN  = 18/18
DESIGN RESOLVED（非 Human Decision）= U-1 · U-2 · U-3 · NU-07 · NU-08 · NU-09（见 §2B）
HUMAN DECISION REQUIRED（新增待决）= ND-A · ND-B      DESIGN DEFERRED = NU-C

P09 DESIGN          = WRITE COMPLETE（2026-09-17）
P09 IMPLEMENTATION  = NOT STARTED
0011                = ABSENT
MIGRATION = NO · DDL = NO · DML = NO · COMMIT = NO · TAG = NO
新增决策号 = 0（DESIGN WRITE 未产生新的 Human Decision）
未修改   = 0001–0010 · 任何已发布 migration · 任何测试 · 任何代码
```
