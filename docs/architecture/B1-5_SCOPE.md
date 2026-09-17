# B1-5 — Scope（PREP）

Status: **PREP / DESIGN — 不创建任何对象**
阶段性质：**READ-ONLY RECONNAISSANCE → 设计草案**
父基线：`B1-4 Commit = e9766fbe8b13294d8a6cdfbff640f14d8e57a68f` · `Tag = UAP-V0.1.4-B1-4-RESOURCE-ACL`

> **本文件不构成任何冻结。** 所有 `OPEN` 项等待 Human Decision（见 `B1-5_DECISION_LOG.md`）。

---

## 0. 关于 "B1-5" 这一编号（必读）

| 项 | 结论 |
|---|---|
| 全库搜索 `B1-5` / `B1.5` | **0 命中** —— 项目现有文档**没有**名为 "B1-5" 的正式阶段定义 |
| 是否存在 roadmap / 阶段总表 | **不存在**（无 `ROADMAP` / 路线图文档） |
| 因此 B1-5 的**实质范围**如何确定 | 只能由**冻结的 phase plan** 唯一推导（见 §1） |
| **字面结论** | `B1-5 definition (literal) = NOT FOUND` |
| **实质结论** | `B1-5 = P07 Tool 域`（推导链见 §1）—— **D-B15-01 = FROZEN — A（2026-09-14 Human Decision）** |

> 本文件**不猜测** scope：§1 的推导全部引用现有冻结原文，且把"编号绑定"本身登记为待裁定项。

---

## 1. 推导链（B1-5 → P07 Tool）

### 1.1 冻结的 phase plan（原文）

`STEP1B_SCHEMA_DEPENDENCY.md` §5「调整后的 Migration Phase 顺序」：

| Phase | 内容 | 原文行 |
|---|---|---|
| P00 | 扩展 / DB primitives（`uap_uuid_v7()`、`set_updated_at()`） | :161 |
| P01 | Root identity：`users` | :162 |
| P02 | Identity 附属：`identities → credentials → devices → sessions` | :163 |
| P03 | Tenant / Space：`tenants → spaces` | :164 |
| P04 | Role / Permission：`permissions → roles → role_permissions` | :165 |
| P05 | Membership：`tenant_memberships → memberships` | :166 |
| **P06** | **Resource / ACL：`resources → acl_subject_types → resource_permissions`** | :167 |
| **P07** | **Tool：`tools` → `tool_versions` → `tool_permissions`** | :168 |
| P08 | AI Gateway：`ai_providers → ai_models → ai_routes → ai_policies → ai_request_logs` | :169 |
| P09 | Agent：`agents → agent_versions → agent_permissions → tool_executions → 补 agents.current_version_id FK` | :170 |
| P10 | Event / Audit：`events → audit_logs` | :171 |
| P11 | Triggers / 跨表约束 | :172 |
| P12 | Indexes | :173 |
| P13 | Seed / built-in data | :174 |

`STEP1B_B0_GATE_REPORT.md:45` 同口径：
```
P00 primitives → P01 users → P02 identity → P03 tenant/space → P04 role/permission
→ P05 membership → P06 resource/ACL → P07 tool → P08 AI → P09 agent(+tool_executions+补 FK)
→ P10 event/audit → P11 triggers → P12 indexes → P13 seed
```

### 1.2 P01–P06 已完成（实测对账）

从 `0003`–`0007` 提取的实际建表（17 张业务表）：

| Phase | 计划表 | 实际已建 | 状态 |
|---|---|---|---|
| P01 | `users` | `users` | ✅ |
| P02 | `identities`/`credentials`/`devices`/`sessions` | 同 | ✅ |
| P03 | `tenants`/`spaces` | 同 | ✅ |
| P04 | `permissions`/`roles`/`role_permissions` | 同 | ✅ |
| P05 | `tenant_memberships`/`memberships` | 同 | ✅ |
| P06 | `resources`/`acl_subject_types`/`resource_permissions` | 同（`0007`） | ✅ |

> 计划外新增（B1-3 hardening）：`platform_memberships`、`platform_state`（D-07）。

### 1.3 编号映射先例

`B1-4_DECISION_LOG.md:14` 等原文明确写 **"P06（= B1-4）"**；`B1-4_SCOPE.md:42` 写 **"Tool / AI / Agent 域 | P07 / P08 / P09 | 依赖顺序在 `resources` 之后"**。

⇒ `B1-4 = P06` 已被接受，且 B1-4 文档明确把 **P07 Tool** 指为下游。

### 1.4 结论

```
P06 = B1-4（已完成、已封存）
P07 = 下一个未执行 phase
⇒ B1-5（本轮编号）= P07 = Tool 域
```

> ⚠️ **映射不是严格 1:1**：B1-1 覆盖 P01+P02；B1-2 覆盖 P03+P05；B1-3 覆盖 P04（+hardening）。因此 `B1-5 = P07` 是**强推导但非字面冻结** ⇒ 已由 **D-B15-01 = FROZEN — A（2026-09-14）** 正式确认。

---

## 2. Objective

在 `resources`（P06）之上建立 **Tool 域的数据层基座**：工具注册表、工具契约版本、工具所需权限绑定。交付**仅 schema 层**（表 + 约束 + 索引 + 2 个 trigger + 1 个 function），**零 seed、零 API、零授权求值**。

---

## 3. In Scope

| # | 对象 | 说明 |
|---|---|---|
| 1 | `tools` | Tool 注册表（平台级 `tenant_id IS NULL` + 租户级）· ROOT（无出边 FK 除 tenant） |
| 2 | `tool_versions` | Tool 契约快照（schema / risk / timeout / handler_ref / checksum）；published 后不可变 |
| 3 | `tool_permissions` | 「调用该 Tool 需要哪些 `permissions`」的绑定行 |
| 4 | 约束 | PK ×3 · **FK ×5**（含 `tools.tenant_id → tenants.id RESTRICT`，D-B15-02 = FROZEN — A）· UQ ×4（1 constraint + 3 index，D-B15-06）· CK ×5 · NN/DEFAULT |
| 5 | 索引 | `tools` 两条部分唯一（平台级 / 租户级）· `uq_tool_versions` · `uq_tool_perm`（含 `COALESCE` ⇒ **必须是 unique index 而非 constraint**） |
| 6 | Trigger ×2 | `tg_tools_set_updated_at`（复用 B1-1 `set_updated_at()`）· `tg_version_immutable`（BEFORE UPDATE OR DELETE） |
| 7 | Function ×1 | `enforce_tool_versions_immutable()`（命名属 implementation-level，见 D-B15-03） |
| 8 | Migration | 预计 `0008`（**本轮不创建**） |

---

## 4. Out of Scope

| 对象 | 归属 | 依据 |
|---|---|---|
| **`tool_executions`** | **P09**（Agent phase 尾部） | `SCHEMA_DEPENDENCY:170` + §5 调整说明②"`tool_executions` 从 Tool phase **挪到** Agent phase 尾部（依赖 agents）" |
| `agents` / `agent_versions` / `agent_permissions` | P09 | 同上 |
| `ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs` | P08 | `SCHEMA_DEPENDENCY:169` |
| `events` / `audit_logs` | P10 | `:171` |
| `resource_relations` | P2 可选，B1 不建 | `SCHEMA_DEPENDENCY:45` |
| G / H / I / J（ACL trigger 四件套） | **P09 后**（实际 P11 集中） | `TRIGGER_INVENTORY:163-166`（**不得因 B1-4 已有 ACL 而拉入 B1-5**） |
| Authorization Layer / Role Resolution / Deny Resolution | 后续阶段 | 无 phase 归属；`B1-4_DESIGN:28` 同口径 |
| API / Socket.IO | 本阶段 = 0 | 见 `B1-5_API_DESIGN.md` |
| Seed | **P13** | `SCHEMA_DEPENDENCY:193`「P00–P10 均无 seed 需求」；`SEED_STRATEGY` 清单不含 Tool 域 |

---

## 5. Dependencies

| 依赖 | 来源 phase | 状态 |
|---|---|---|
| `tenants` | P03 / `0004` | ✅ 已存在（仅当 `tools.tenant_id` 加 FK，见 D-B15-02） |
| `permissions` | P04 / `0005` | ✅ 已存在（`tool_permissions.permission_id` 目标） |
| `uap_uuid_v7()` | P00 / `0003` | ✅ 已存在（**不重建**） |
| `set_updated_at()` | P00 / `0003` | ✅ 已存在（**不重建**，`tools` 复用） |
| `resources` | P06 / `0007` | ✅ 已存在（**无直接 FK**；Tool 归属/授权未来可挂 `resources` —— `B1-4_DEPENDENCY:130`） |

**无 forward dependency**（不引用 `agents` / `ai_*` / `events` / `audit_logs`）✅

---

## 6. Phase Boundary

```
P00 primitives ─┐
P01 users ──────┤
P02 identity ───┤
P03 tenant/space┤
P04 role/perm ──┤ 均已交付（0003–0006）
P05 membership ─┤
P06 resource/ACL┤ 已交付（0007 = B1-4，已封存）
────────────────┴──▶ ★ B1-5 起点
P07 Tool ★ B1-5（tools / tool_versions / tool_permissions）
P08 AI        ── 不进入
P09 Agent     ── 不进入（含 tool_executions、G/H/I/J）
P10 Event/Audit ── 不进入
P11 Triggers  ── 不进入（B1-5 自带 2 个表级 trigger；跨表 trigger 集中期不变）
P12 Indexes   ── 不进入（B1-5 索引建表内联）
P13 Seed      ── 不进入（B1-5 零 seed）
```

**P07 与 P09 之间的阶段隔离**：`tool_executions`（含 `agent_id → agents.id`）是**唯一**把 Tool 概念域拖向 P09 的表 —— 已被 phase plan 显式移出 P07。B1-5 **不得**通过"先建表后补 FK"绕过该边界。

---

## 7. Database Objects（预计 3 表）

```
tools                ROOT（tenant 除外）
  └─ tool_versions        tool_id → tools.id CASCADE
  └─ tool_permissions     tool_id → tools.id CASCADE
                          version_id NULL → tool_versions.id CASCADE
                          permission_id → permissions.id CASCADE
```

**禁止出现**：`tool_executions` / `agents*` / `ai_*` / `events` / `audit_logs` / `groups` / 任何 Domain 表。

---

## 8. Trigger Boundary

| trigger | 表 | timing/event | earliest legal phase | 性质 |
|---|---|---|---|---|
| `tg_tools_set_updated_at` | `tools` | BEFORE UPDATE | 表建时（P07） | 机械（复用 `set_updated_at()`） |
| `tg_version_immutable` | `tool_versions` | BEFORE UPDATE OR DELETE | **表建时**（`SCHEMA_DEPENDENCY:240` 原文；`TRIGGER_INVENTORY` 条目 **K**） | **结构性不变式**（published 行禁改删） |

| 类别 | 清单 |
|---|---|
| **existing**（B1-1~B1-4，7 个） | `tg_set_updated_at`(×8 表实例) · `tg_roles_scope_shape` · `tg_roles_is_system_protect` · `tg_tm_role_scope` · `tg_membership_role_scope` · `tg_membership_tenant_consistency` · `tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` · `tg_resources_set_updated_at` · `tg_resources_tenant_space_consistency` · `tg_acl_subject_types_protect` |
| **B1-5（本轮）** | `tg_tools_set_updated_at` · `tg_version_immutable`（**共 2 个**） |
| **P09 后** | **G** `tg_acl_subject_exists` · **H** `tg_acl_user_hard_delete` · **I** `tg_acl_role_delete_block` · **J** `tg_agent_acl_expire` —— **保持不实施** |
| **future** | `tg_version_immutable`（随 P09 `agent_versions` —— **与 B1-5 共用同一名**，D-B15-03 = FROZEN — A）· `tg_audit_logs_immutable`（L，P10） |

**边界声明（强制）**：`tg_version_immutable` **仅**强制"已发布版本快照不可变"这一**结构性不变式**；**不承担** authorization evaluation / role resolution / deny resolution / Domain authorization。

---

## 9. API Boundary

```
API    = 0
Socket = 0
```

理由与 B1-4 同构（`B1-4_API_DESIGN:4,18`）：Tool 的调用入口（Agent → Policy → Tool → Service → DB）必须建立在**已实现的 Authorization Layer** 之上，该层属后续阶段。本阶段引入接口将产生"没有授权判定的写入口"，违反 default-deny。

---

## 10. Security Boundary

| 维度 | B1-5 立场 |
|---|---|
| Tenant isolation | `tools.tenant_id`（NULL=平台内置）；平台级/租户级由**两条部分唯一索引**区分 |
| Space isolation | **不适用**（Tool 无 `space_id`） |
| Identity boundary | 不引入新主体 |
| Role / Permission boundary | `tool_permissions.permission_id → permissions.id`（P04 已存在）；**不做授权判定** |
| Resource ACL boundary | 无 ACL 主体写入（`acl_subject_types` 仍 0 rows） |
| Cross-tenant FK | **PASS** —— D-B15-02 = FROZEN — A：`tools.tenant_id NULL → tenants.id RESTRICT` |
| Delete semantics | 业务实体 RESTRICT；`tools → tool_versions` / `tools → tool_permissions` / `tool_permissions.version_id` / `permission_id` = **CASCADE**（`CORE:11.1` 白名单"版本快照"+"配置行"） |
| Privilege escalation | 本阶段无判定逻辑 ⇒ 无新面；不变式面向"快照完整性" |
| RLS | **不启用**（与 B1-4 一致） |
| Sensitive data | `input_schema` / `output_schema` / `retry_policy` / `conditions` 为**配置**，不得存放凭据（登记为约束纪律，见 Security Review） |

---

## 11. Seed Boundary

```
B1-5 seed = 0
```
依据：`SCHEMA_DEPENDENCY:193`「**P00-P10 均无 seed 需求；P13 才有 seed**」；`SEED_STRATEGY` §1 的 seed 清单（`acl_subject_types` / `permissions` / roles / 租户 / 用户 / memberships / role_permissions）**不含 Tool 域任何行**。

⇒ B1-5 完成后 `tools` / `tool_versions` / `tool_permissions` 均为 **0 rows**。

---

## 12. Migration Boundary

| 项 | 值 |
|---|---|
| 预计 revision | `0008`（命名待定，风格对齐 `0007_b1_4_resource_acl`） |
| `down_revision` | `0007_b1_4_resource_acl` |
| 单事务 | 是（沿用 B1-0 契约） |
| upgrade 顺序 | `tools` → `tool_versions` → `tool_permissions` → constraints/indexes（内联）→ function → triggers |
| downgrade 顺序 | drop triggers → drop function → drop indexes → drop tables（逆序） |
| **本轮** | **不创建任何 migration**；**不执行 DDL/DML** |

---

## 13. Test Boundary

- 不重复 B1-4 已完成的测试。
- B1-4 的 canonical count（**84**）**不因 B1-5 改变**；B1-5 使用**独立编号空间**（`B1-5_TEST_MATRIX.md`）。
- 依赖未来对象的测试（如 `tool_executions` 幂等锚点、`agent_permissions.tool_id`）**标记为后续阶段**，不得伪装成 B1-5 可执行。

---

## 14. Decisions

见 `B1-5_DECISION_LOG.md` 与 `B1-5_HUMAN_DECISION_FREEZE_PACKAGE.md`。

```
FROZEN（9）: D-B15-01 = A · D-B15-02 = A · D-B15-03 = A · D-B15-04 = A · D-B15-05 = A
            D-B15-06 = A · D-B15-07 = A · D-B15-08 = A · D-B15-09 = A
OPEN  （0）: ——     BLOCKING（0）: ——
```

**D-B15-01 = FROZEN — A** 已确认 `B1-5 = P07 Tool`（不得据此改变历史 B0 的 phase 定义）。

---

## 15. Gate

```
B1-5 SCOPE = COMPLETE（9 项 Decision 全部 FROZEN — A）
B1-5 IMPLEMENTATION = READY BUT NOT STARTED
```
