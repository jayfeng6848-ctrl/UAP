# P12 — IMPLEMENTATION ACCEPTANCE MATRIX（Indexes · CONTRACT 层）

> ## 状态
>
> ```text
> DESIGN FROZEN
> IMPLEMENTATION NOT YET AUTHORIZED
> ```
>
> 本矩阵是 `P12_IMPLEMENTATION_CONTRACT.md` 的**验收口径**，**不是验收结论**。
> 全部 `PLANNED` 条目**尚未实施**（`NOT IMPLEMENTED`）；`PASSED` 仅指**本轮只读核对通过**。
>
> **状态词表**：**`ASSET`**（既有冻结资产）· **`PASSED`**（本轮只读核验通过）·
> **`PLANNED`**（设计已冻结、**实施未授权**）· **`BLOCKED`**（被实施门阻塞）。
> **§0 口径声明**：状态**一律从最后一格（状态单元）解析**，**禁止**扫描整行正文判定。
> 跨文档比对**一律双侧归一**（剥离 `` ` `` `*`、统一空白、casefold）。

---

## 1. INV — Index Inventory（本轮只读实测）

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| INV-01 | 既有索引对象 = **57**（独立创建 52 + 隐式 UNIQUE 5） | 脚本实测 | **PASSED** |
| INV-02 | 既有 FK 总数（**校正后**）= **57** | 实测 + **`MEASURE-1`** | **PASSED** |
| INV-03 | FK 分划：ALREADY COVERED **27** + partial-only **5** + GAP **25** = **57**（自洽） | 脚本实测 | **PASSED** |
| INV-04 | FK 反查候选集 = **25 GAP + 5 partial-only = 30** | 脚本实测 | **PASSED** |
| INV-05 | 年代标注：post-strategy **22**（GAP 20 + partial 2）· strategy-era **8**（GAP 5 + partial 3） | `D-P12-13` 强制 | **PASSED** |
| INV-06 | **`MEASURE-1` = APPROVED**：PREP 的 54/25/5/24 漏计 3 条 raw-`ALTER` FK ⇒ 校正 **57/27/5/25/30** | `0005:432` · `0005:435` · `0011:356` · PDL 附录 I.9 | **PASSED** |
| INV-07 | P12 计划新建索引对象 = **19**（12 FK 反查 + 7 P10 表） | `P12_IMPLEMENTATION_CONTRACT` §3 | **PASSED** |
| INV-08 | 既有 57 对象全部标注 **ALREADY COVERED**（不得重列为 CREATE） | `D-P12-01` | **PASSED** |

## 2. ADJ — FK 逐项裁定（**30 项全覆盖**）

### 2.1 GAP 类（25）

| ID | FK | ON DELETE | 年代 | decision | 状态 |
|---|---|---|---|---|---|
| ADJ-01 | `agent_permissions.permission_id → permissions.id` | CASCADE | post-strategy | **CREATE** | **PASSED** |
| ADJ-02 | `agent_permissions.tool_id → tools.id` | CASCADE | post-strategy | **CREATE** | **PASSED** |
| ADJ-03 | `agent_permissions.version_id → agent_versions.id` | CASCADE | post-strategy | **CREATE** | **PASSED** |
| ADJ-04 | `agent_versions.published_by → users.id` | SET NULL | post-strategy | **DEFER** | **PASSED** |
| ADJ-05 | `agents.current_version_id → agent_versions.id` | SET NULL | post-strategy | **CREATE** | **PASSED** |
| ADJ-06 | `agents.default_route_id → ai_routes.id` | SET NULL | post-strategy | **CREATE** | **PASSED** |
| ADJ-07 | `agents.owner_id → users.id` | RESTRICT | post-strategy | **DEFER** | **PASSED** |
| ADJ-08 | `agents.space_id → spaces.id` | RESTRICT | post-strategy | **NOT REQUIRED** | **PASSED** |
| ADJ-09 | `ai_policies.space_id → spaces.id` | RESTRICT | post-strategy | **NOT REQUIRED** | **PASSED** |
| ADJ-10 | `ai_policies.tenant_id → tenants.id` | RESTRICT | post-strategy | **NOT REQUIRED** | **PASSED** |
| ADJ-11 | `ai_request_logs.model_id → ai_models.id` | RESTRICT | post-strategy | **CREATE** | **PASSED** |
| ADJ-12 | `ai_request_logs.provider_id → ai_providers.id` | RESTRICT | post-strategy | **CREATE** | **PASSED** |
| ADJ-13 | `ai_routes.primary_model_id → ai_models.id` | RESTRICT | post-strategy | **CREATE** | **PASSED** |
| ADJ-14 | `ai_routes.space_id → spaces.id` | RESTRICT | post-strategy | **NOT REQUIRED** | **PASSED** |
| ADJ-15 | `ai_routes.tenant_id → tenants.id` | RESTRICT | post-strategy | **NOT REQUIRED** | **PASSED** |
| ADJ-16 | `memberships.user_id → users.id` | CASCADE | **strategy-era** | **DEFER** | **PASSED** |
| ADJ-17 | `resource_permissions.granted_by → users.id` | SET NULL | **strategy-era** | **DEFER** | **PASSED** |
| ADJ-18 | `resources.owner_id → users.id` | SET NULL | **strategy-era** | **DEFER** | **PASSED** |
| ADJ-19 | `resources.space_id → spaces.id` | RESTRICT | **strategy-era** | **NOT REQUIRED** | **PASSED** |
| ADJ-20 | `spaces.owner_id → users.id` | SET NULL | **strategy-era** | **DEFER** | **PASSED** |
| ADJ-21 | `tool_executions.actor_id → users.id` | SET NULL | post-strategy | **DEFER** | **PASSED** |
| ADJ-22 | `tool_executions.agent_id → agents.id` | SET NULL | post-strategy | **NOT REQUIRED** | **PASSED** |
| ADJ-23 | `tool_executions.tool_version_id → tool_versions.id` | RESTRICT | post-strategy | **CREATE** | **PASSED** |
| ADJ-24 | `tool_permissions.permission_id → permissions.id` | CASCADE | post-strategy | **CREATE** | **PASSED** |
| ADJ-25 | `tool_permissions.version_id → tool_versions.id` | CASCADE | post-strategy | **CREATE** | **PASSED** |

### 2.2 partial-only 类（5 · `D-P12-05`）

| ID | FK | ON DELETE | 既有 partial 索引 | 年代 | decision | 状态 |
|---|---|---|---|---|---|---|
| ADJ-26 | `credentials.identity_id → identities.id` | CASCADE | `uq_credentials_active_password` | **strategy-era** | **NOT REQUIRED** | **PASSED** |
| ADJ-27 | `roles.space_id → spaces.id` | CASCADE | `uq_roles_space` | **strategy-era** | **NOT REQUIRED** | **PASSED** |
| ADJ-28 | `roles.tenant_id → tenants.id` | CASCADE | `uq_roles_tenant` | **strategy-era** | **NOT REQUIRED** | **PASSED** |
| ADJ-29 | `tool_executions.tool_id → tools.id` | RESTRICT | `uq_tool_exec_idem`（谓词不覆盖全行） | post-strategy | **CREATE** | **PASSED** |
| ADJ-30 | `tools.tenant_id → tenants.id` | RESTRICT | `uq_tools_tenant` | post-strategy | **NOT REQUIRED** | **PASSED** |

### 2.3 ALREADY COVERED（27 · 本轮**不建**）

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| ADJ-31 | ALREADY COVERED = **27** 项（含 `MEASURE-1` 新增的 `tenant_memberships.role_id` → `ix_tenant_memberships_role` · `memberships.role_id` → `ix_memberships_role`） | 脚本实测 · `0005:432/435/438/439` | **PASSED** |
| ADJ-32 | 无任何 ALREADY COVERED 项被重列为 `CREATE` | `D-P12-01` | **PASSED** |
| ADJ-33 | 裁定汇总自洽：`CREATE 12 + DEFER 7 + NOT REQUIRED 11 + ALREADY COVERED 0`（30 项）；`+27 ALREADY COVERED` = 57 | 脚本实测 | **PASSED** |

## 3. IDX — 计划新建对象（**19 · 全部 NOT IMPLEMENTED**）

| ID | index_name | table | 形态 | 状态 |
|---|---|---|---|---|
| IDX-01 | `ix_ap_permission` | `agent_permissions` | btree `(permission_id)` | **PASSED** |
| IDX-02 | `ix_ap_tool` | `agent_permissions` | btree `(tool_id)` | **PASSED** |
| IDX-03 | `ix_ap_version` | `agent_permissions` | btree `(version_id)` | **PASSED** |
| IDX-04 | `ix_agents_current_version` | `agents` | btree `(current_version_id)` | **PASSED** |
| IDX-05 | `ix_agents_default_route` | `agents` | btree `(default_route_id)` | **PASSED** |
| IDX-06 | `ix_airl_provider` | `ai_request_logs` | btree `(provider_id)` · **分区表** | **PASSED** |
| IDX-07 | `ix_airl_model` | `ai_request_logs` | btree `(model_id)` · **分区表** | **PASSED** |
| IDX-08 | `ix_airoutes_primary_model` | `ai_routes` | btree `(primary_model_id)` | **PASSED** |
| IDX-09 | `ix_texec_tool` | `tool_executions` | btree `(tool_id)` | **PASSED** |
| IDX-10 | `ix_texec_tool_version` | `tool_executions` | btree `(tool_version_id)` | **PASSED** |
| IDX-11 | `ix_tperm_permission` | `tool_permissions` | btree `(permission_id)` | **PASSED** |
| IDX-12 | `ix_tperm_version` | `tool_permissions` | btree `(version_id)` | **PASSED** |
| IDX-13 | `ix_events_dispatch` | `events` | btree `(status, next_attempt_at)` · partial | **PASSED** |
| IDX-14 | `ix_events_tenant_type_time` | `events` | btree `(tenant_id, event_type, occurred_at DESC)` | **PASSED** |
| IDX-15 | `ix_audit_tenant_time` | `audit_logs` | btree `(tenant_id, occurred_at DESC)` | **PASSED** |
| IDX-16 | `ix_audit_actor_time` | `audit_logs` | btree `(actor_id, occurred_at DESC)` | **PASSED** |
| IDX-17 | `ix_audit_resource` | `audit_logs` | btree `(resource_type, resource_id, occurred_at DESC)` | **PASSED** |
| IDX-18 | `ix_audit_correlation` | `audit_logs` | btree `(correlation_id)` | **PASSED** |
| IDX-19 | `ix_audit_risk` | `audit_logs` | btree `(risk_level, occurred_at)` · partial | **PASSED** |

## 4. PROT — 既有索引保护

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| PROT-01 | 既有 **57** 对象在本轮与实施后**均不得**被重列为 `CREATE` / 改动 | `D-P12-01` | **PASSED** |
| PROT-02 | `ix_role_permissions_permission`（canonical）**不 rename**；`ix_rp_permission` 仅历史名 | `D-P12-12` · `CF-3` | **PASSED** |
| PROT-03 | `ix_tenant_memberships_role`（canonical）**不 rename**；`ix_tm_role` 仅历史名 | `D-P12-12` · `CF-3` | **PASSED** |
| PROT-04 | `uq_tool_exec_idem` 语义**不变**（UNIQUE INDEX + `WHERE idempotency_key IS NOT NULL`）；**不再建等价幂等索引** | `D-P12-06` | **PASSED** |
| PROT-05 | P09 索引 8 对象（`uq_agents_key` · `ix_agents_tenant_status` · `uq_agent_perm` · `ix_ap_agent` · `uq_tool_exec_idem` · `ix_texec_tenant_created` · `ix_texec_status` · `uq_agent_versions`）**不动** | `D-P09-15/16` · `D-P12-01` | **PASSED** |
| PROT-06 | **P10 索引尚不存在**（`events`/`audit_logs` 表未建）⇒ 7 条属 P12 待建，**不得读作"已存在"** | `D-P12-08` · `DEP-02` | **PASSED** |

## 5. T1 — `T-1` 禁止（`D-P12-14`）

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| T1-01 | `ix_aimodels_capability` = **NOT IMPLEMENTED**（本契约亦不建） | `D-P12-14` | **PASSED** |
| T1-02 | **禁** `GIN(capabilities)` · **禁** JSONB path/expression index · **禁** `capability` virtual column | `D-P12-14` · `INDEX_STRATEGY §2` | **PASSED** |
| T1-03 | 既有负向断言已固化该禁止（`test_ai_gateway_schema.py:696-698`） | 命令 | **PASSED** |
| T1-04 | `T-1` = CLOSED as stale / mismatched design claim | `D-P12-14` · `CF-2` | **PASSED** |

## 6. P09 / P10 / P11 — 边界保护

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| P09-01 | `0010` / `0011` / `0012` sha256 **逐字节未变**；`0013+ = 0` | 命令 | **PASSED** |
| P09-02 | `core/` `services/` `agent/` `intelligence/` `infrastructure/` `tests/` `apps/` `config/` `scripts/` `migrations_alembic/` 相对 HEAD **diff 空** | 命令 | **PASSED** |
| P10-01 | `P10 = Event/Audit persistence + tg_audit_immutable`（L = P10-owned）；P12 **不建/不改** `events`/`audit_logs` trigger | `D-P10-11` · `D-P12-08` | **PASSED** |
| P10-02 | P12 **不在** P10 之外创建 `events` / `audit_logs` 表 | `P10 GP-13` | **PASSED** |
| P10-03 | `ix_events_*` / `ix_audit_*`（**7**）= **P12**；`P10 不负责这些 indexes`；`P10 persistence ≠ P12 index delivery` | `D-P12-08` | **PASSED** |
| P10-04 | `P10 schema ownership + P12 index ownership` = 阶段分工（`CF-6` CLARIFIED），**非** P10 schema regression | `D-P12-08` · `CF-6` | **PASSED** |
| P11-01 | P12 对 G/H/I/J **仅提供性能支持**（复用 `ix_rp_subject`），**不改** trigger timing / semantics / failure semantics | `D-P12-09` | **PASSED** |
| P11-02 | `P11 semantics MUST NOT depend on P12` · `P12 index MUST NOT change P11 semantics` | `D-P12-09` | **PASSED** |
| P11-03 | P12 **不新增** trigger / function / CHECK / FK / seed | `D-P12-15` | **PASSED** |
| P11-04 | P11 的 4 触发器（`tg_acl_subject_exists` · `tg_acl_user_hard_delete` · `tg_acl_role_delete_block` · `tg_agent_acl_expire`）**均未落地**（属 P11） | `P11_PREP_REPORT` | **PASSED** |

## 7. NAME / PARTITION

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| NAME-01 | 沿用 canonical 形式 `ix_<semantic_name>` / `uq_<semantic_name>`，不发明第二套 | `D-P12-12` | **PASSED** |
| NAME-02 | **不 rename** 任何既有索引（禁 `ALTER INDEX … RENAME`） | `D-P12-12` | **PASSED** |
| NAME-03 | 全部 19 条提议名 ≤ PG 63 字节上限（最长 26） | 脚本核对 | **PASSED** |
| PART-01 | P10 表索引**建在父表**、PG 自动下推；**子分区零本地索引** | `INDEX_STRATEGY:160` · `B1-6 DC-4` · `AP3` | **PASSED** |
| PART-02 | **禁** `CREATE INDEX CONCURRENTLY`（Alembic 事务内非法）；**禁** `ON ONLY` / `ATTACH PARTITION` | `D-P12-10` | **PASSED** |
| PART-03 | partition key / partition strategy / PK / retention **全部不变** | `D-P12-10` | **PASSED** |
| PART-04 | `events` / `audit_logs` **UQ = 无** ⇒ 不触发分区唯一索引约束 | `CONSTRAINT_MATRIX §7` | **PASSED** |

## 8. MIG — 迁移设计完整性（**design only**）

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| MIG-01 | revision id = `0015_p12_indexes`（16 ≤ 32 字符） | 契约 §11.1 · **`NUM-1`** | **PASSED** |
| MIG-02 | `down_revision = 0012_authz_enforcement` | 契约 §11.1 | **PASSED** |
| MIG-03 | 本 phase 完成后 `alembic heads` = **单头** `0015_p12_indexes`；`0016+ = 0` | 契约 §11.1 | **PASSED** |
| MIG-04 | upgrade 顺序 = FK 反查（普通表）→ 分区表父索引；**P10 表须先存在** | 契约 §11.2 | **PASSED** |
| MIG-05 | downgrade = 逆序 `DROP INDEX IF EXISTS`，**零残留** | 契约 §11.3 | **PASSED** |
| MIG-06 | 本轮**未创建** migration 文件；**未**执行 upgrade / downgrade | 命令 | **PASSED** |
| MIG-07 | 迁移往返（upgrade → downgrade → upgrade）为实施轮验收项 | 契约 §12.2 | **PASSED** |
| MIG-08 | 文件数与单头状态相对 HEAD **未变**（12 版本文件 · 单头 `0012` · `0013+ = 0`） | 命令 | **PASSED** |
| MIG-09 | **`NUM-1` = RESOLVED**：编号分配 `P10 = 0013_p10_event_audit` · `P11 = 0014_p11_triggers` · `P12 = 0015_p12_indexes`（唯一 · 无复用） | PDL 附录 I.9 | **PASSED** |
| MIG-10 | revision 链连续：`0012 → 0013 → 0014 → 0015`；本 phase `down_revision = 0014_p11_triggers` | 契约 §11.1 · `D-PLAT-09` | **PASSED** |

## 9. QE — 查询证据

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| QE-01 | 全部 19 条 `CREATE` 均具**明确 query evidence**（FK 语义级 / 冻结索引清单） | `D-P12-02` | **PASSED** |
| QE-02 | 无「future may query」/「FK exists」/「best practice」作为**唯一**依据 | `D-P12-02` | **PASSED** |
| QE-03 | `GAP ≠ automatic CREATE INDEX`：30 项**逐项**裁定，仅 **12** 为 CREATE | `D-P12-13` | **PASSED** |

## 10. GUARD / TEST — 同步计划

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| GUARD-01 | **`GUARD-1` = APPROVED**：T-22（10 名）中 **5 名**将由 P12 CREATE 变为存在；**不 supersede** `D-P12-13` | 契约 §7 · PDL 附录 I.9 | **PASSED** |
| GUARD-02 | T-22 实施时移除**恰好 5** 名（`ix_ap_permission` · `ix_ap_tool` · `ix_ap_version` · `ix_agents_current_version` · `ix_agents_default_route`）；保留**恰好 5** 名 | 契约 §7 | **PASSED** |
| GUARD-03 | head 断言同步面 = **15 文件**（`0012` → `0013`） | 命令 | **PASSED** |
| GUARD-04 | 索引名断言同步面 = **7 文件**（原始 token 61；确属清单 40） | 命令 | **PASSED** |
| GUARD-05 | `FORBIDDEN_TABLES` = **4 文件**（P12 无新增） | 命令 | **PASSED** |
| GUARD-06 | 本轮**未修改**任何测试；**未新增**守卫文件（`tests/architecture/test_index_inventory.py` 仅设计） | 命令 | **PASSED** |
| GUARD-07 | T-22 验收规则：`removed ⊆ P12 CREATE set` 且 `remaining ∩ P12 CREATE set = ∅` | 契约 §7 | **PASSED** |
| GUARD-08 | 三方一致：`P12 CREATE set` ↔ T-22 期望 ↔ 索引名断言 | 契约 §7 / §12.2 | **PASSED** |

## 11. SCOPE / GATE

| ID | 检查项 | 依据 | 状态 |
|---|---|---|---|
| SCOPE-01 | 本轮新增 **2 份文档**（`P12_IMPLEMENTATION_{CONTRACT,ACCEPTANCE_MATRIX}.md`）；未改任何既有文档 | 命令 | **PASSED** |
| SCOPE-02 | `CREATE/ALTER/DROP INDEX = 0` · `DDL = 0` · `DML = 0` · migration 变更 = 0 · code/test/config = 0 | 命令 | **PASSED** |
| SCOPE-03 | `commit = 0` · `tag = 0` · `push = 0` | 命令 | **PASSED** |
| SCOPE-04 | 跨决策：`D-PLAT-09` / `D-AUTH-01..25` / `D-AGENT-01..16` / `D-P10-01..18` / `D-P11-01..14` / `D-P12-01..15` **未被 supersede**；supersession 恒 = **1**（`D-B14-08`） | 命令 | **PASSED** |
| SCOPE-05 | `NUM-1` / `MEASURE-1` / `GUARD-1` **均已 APPROVED**；**未**借校正改写任何冻结正文（校正以 append-only 登记于 PDL 附录 I.9） | 契约 §6/§7/§11.1 · PDL I.9 | **PASSED** |
| SCOPE-06 | 本轮变更**仅限授权集**：`P12_IMPLEMENTATION_CONTRACT` · `P12_IMPLEMENTATION_ACCEPTANCE_MATRIX` · `PLATFORM_DECISION_LOG` · 2 份 P10 文档的 `NUM-1` 记录行 | 命令 | **PASSED** |
| GATE-01 | `IMPLEMENTATION GATE`：前置 ①–⑤ 于 2026-09-26 全部满足（P10/P11 已实施） | 契约 §13 · 实施轮 | **PASSED** |
| GATE-02 | `P12 IMPLEMENTATION = AUTHORIZED`（2026-09-26）→ 已实施 | 授权指令 §0 | **PASSED** |
| GATE-03 | `P13 IMPLEMENTATION = NOT AUTHORIZED` | `D-PLAT-09` | **BLOCKED** |
| GATE-04 | `Runtime Implementation Gate = CLOSED` | `D-AGENT-16` | **BLOCKED** |

## 12. TRACE — 索引裁定 ↔ 验收（**19/19 + 30/30**）

| ID | 对象 / 裁定 | 对应验收行 | 状态 |
|---|---|---|---|
| TRACE-01 | `IDX-01` `ix_ap_permission` | ADJ-01 · IDX-01 · QE-03 | **PASSED** |
| TRACE-02 | `IDX-02` `ix_ap_tool` | ADJ-02 · IDX-02 · GUARD-01 | **PASSED** |
| TRACE-03 | `IDX-03` `ix_ap_version` | ADJ-03 · IDX-03 · GUARD-01 | **PASSED** |
| TRACE-04 | `IDX-04` `ix_agents_current_version` | ADJ-05 · IDX-04 · INV-06 · GUARD-01 | **PASSED** |
| TRACE-05 | `IDX-05` `ix_agents_default_route` | ADJ-06 · IDX-05 · GUARD-01 | **PASSED** |
| TRACE-06 | `IDX-06` `ix_airl_provider` | ADJ-12 · IDX-06 · PART-01 | **PASSED** |
| TRACE-07 | `IDX-07` `ix_airl_model` | ADJ-11 · IDX-07 · PART-01 | **PASSED** |
| TRACE-08 | `IDX-08` `ix_airoutes_primary_model` | ADJ-13 · IDX-08 | **PASSED** |
| TRACE-09 | `IDX-09` `ix_texec_tool` | ADJ-29 · IDX-09 | **PASSED** |
| TRACE-10 | `IDX-10` `ix_texec_tool_version` | ADJ-23 · IDX-10 | **PASSED** |
| TRACE-11 | `IDX-11` `ix_tperm_permission` | ADJ-24 · IDX-11 | **PASSED** |
| TRACE-12 | `IDX-12` `ix_tperm_version` | ADJ-25 · IDX-12 | **PASSED** |
| TRACE-13 | `IDX-13` `ix_events_dispatch` | IDX-13 · P10-03 · PART-01 | **PASSED** |
| TRACE-14 | `IDX-14` `ix_events_tenant_type_time` | IDX-14 · P10-03 · PART-01 | **PASSED** |
| TRACE-15 | `IDX-15` `ix_audit_tenant_time` | IDX-15 · P10-03 · PART-01 | **PASSED** |
| TRACE-16 | `IDX-16` `ix_audit_actor_time` | IDX-16 · P10-03 · PART-01 | **PASSED** |
| TRACE-17 | `IDX-17` `ix_audit_resource` | IDX-17 · P10-03 · PART-01 | **PASSED** |
| TRACE-18 | `IDX-18` `ix_audit_correlation` | IDX-18 · P10-03 · PART-01 | **PASSED** |
| TRACE-19 | `IDX-19` `ix_audit_risk` | IDX-19 · P10-03 · PART-01 | **PASSED** |

> **裁定级追溯（30/30）**：`ADJ-01`…`ADJ-30` 逐行即为 30 项 FK 反查裁定的**唯一权威表**；
> 其中 `CREATE` 的 12 项一一映射到 `IDX-01`…`IDX-12`（见上表）。
> `DEFER` 7 项（ADJ-04/07/16/17/18/20/21）与 `NOT REQUIRED` 11 项**无对应 IDX 行**（不建）—— 追溯关系为「显式无对象」。

## 13. 汇总（**脚本实测** · 实施轮复核 `p12_impl_acceptance.log`；TRACE 表不计状态）

| 分组 | 行数 | `PASSED` | `PLANNED` | `BLOCKED` |
|---|---|---|---|---|
| ADJ | 33 | 33 | 0 | 0 |
| GATE | 4 | 2 | 0 | 2 |
| GUARD | 8 | 8 | 0 | 0 |
| IDX | 19 | 19 | 0 | 0 |
| IMPL | 9 | 9 | 0 | 0 |
| INV | 8 | 8 | 0 | 0 |
| MIG | 10 | 10 | 0 | 0 |
| NAME | 3 | 3 | 0 | 0 |
| P09 | 2 | 2 | 0 | 0 |
| P10 | 4 | 4 | 0 | 0 |
| P11 | 4 | 4 | 0 | 0 |
| PART | 4 | 4 | 0 | 0 |
| PROT | 6 | 6 | 0 | 0 |
| QE | 3 | 3 | 0 | 0 |
| SCOPE | 6 | 6 | 0 | 0 |
| T1 | 4 | 4 | 0 | 0 |
| **合计** | **127** | **125** | **0** | **2** |



## 14. IMPL — 实施结果（2026-09-26 · `p12_impl_acceptance.log`）

> 授权：`UAP P12 — IMPLEMENTATION AUTHORIZATION`（2026-09-26）。
> 实施对象：`migrations_alembic/versions/0015_p12_indexes.py`（sha256 `94b0d22800c8971e…`）。

| # | 检查 | 证据 | 结果 |
|---|---|---|---|
| IMPL-01 | revision 身份 / 单头 / 链长 15 · `0016+` = 0 | harness #1–4 | **PASSED** |
| IMPL-02 | 19 索引 = 12 FK + 7 P10，名称/表/列/谓词与 §3 逐字一致（btree · 非 UNIQUE） | harness #6–9 · `test_p12_indexes.py` 13/13 | **PASSED** |
| IMPL-03 | partial 谓词：`ix_events_dispatch`（pending/claimed）· `ix_audit_risk`（HIGH/CRITICAL） | indexdef 比对 | **PASSED** |
| IMPL-04 | 分区：9 父表级（airl×2 / events×2 / audit×5）自动下推 13 子分区索引；无 ON ONLY / ATTACH / 子本地 | `pg_index` relkind 校验 | **PASSED** |
| IMPL-05 | 既有索引保全：roundtrip 前后 pre-P12 集合逐项一致（无 DROP/RENAME/MERGE） | harness #15 | **PASSED** |
| IMPL-06 | T-1 = 未创建（`D-P12-14`）· T-22 = 恰 5 retained 缺席 + removed 5 ⊆ CREATE · 三方一致 | harness #10/11/20 · 三方断言 | **PASSED** |
| IMPL-07 | 边界：L/tg_audit_immutable 不变 · P11 4 触发器不变 · seed = 0 · 物理表 35 | harness #12–13 | **PASSED** |
| IMPL-08 | 降级零残留（19→0）· 往返一致 | harness #14/16 | **PASSED** |
| IMPL-09 | Scope：新文件 = 0015 + `test_p12_indexes.py` · 同步 **26 处 / 15+ 文件** · PDL 删除行 = 1（既有） | harness #17–19 | **PASSED** |

**测试**：全量回归 **636 passed / 0 failed / 6 skipped**（exit 0 · 36m47s）；基线 623 ⇒ 净增 **13**，无回归。
**同步面**：head 0014→0015（×29 / 15 文件）· 链长 15 · AM5 父 → 0014 · T-22 移除恰 5 · T-21 索引集 +7 ·
AX2 AI_INDEXES +3 · BND2 翻转（P12 索引已在 P10 表交付）· P11 边界 known-list + agents×2。

**状态**：`P12 = IMPLEMENTED / ACCEPTED` · `P13 = NOT AUTHORIZED` · `Runtime = NOT AUTHORIZED` ·
`commit / tag / push = NOT YET AUTHORIZED`。

**END OF P12 IMPLEMENTATION ACCEPTANCE MATRIX（2026-09-26 · 实施轮验收；见 §14）**
**后续注记：`NUM-1` / `MEASURE-1` / `GUARD-1` 裁定同步（2026-09-25）—— revision → `0015_p12_indexes` · `MEASURE-1` = APPROVED（57/27/5/25/30）· `GUARD-1` = APPROVED（T-22 移除恰好 5 / 保留恰好 5）；实施时限未变（P12 IMPLEMENTATION = NOT AUTHORIZED）**
>
> **[`D-P12-01` 实施注记 · 2026-09-26]** `UAP P12 — IMPLEMENTATION AUTHORIZATION` 下发并已实施
> （`0015_p12_indexes`，sha256 `94b0d22800c8971e…`）；验收 20/20 + 全量回归 636/0/6；
> 上一行的「P12 IMPLEMENTATION = NOT AUTHORIZED」为**该时点状态**，已被本轮授权消耗。**
