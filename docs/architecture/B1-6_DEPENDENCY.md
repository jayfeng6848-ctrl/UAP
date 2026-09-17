# B1-6 Dependency

**Stage**: B1-6（= P08 AI Gateway）· **Status**: DESIGN
**输入**: `B1-6_DECISION_LOG.md`（D-B16-01 ～ D-B16-11 FROZEN）· B0 同步后口径
**边界**: 只做依赖分析，**不创建 migration、不改代码/测试/B0**。

---

## 1. 全局阶段链（已交付 → B1-6）

```
B1-0（P00）      0001, 0002        primitives：uap_uuid_v7() · set_updated_at()
B1-1（P01+P02）  0003             users / identities / credentials / devices / sessions
B1-2（P03+P05）  0004             tenants / spaces / tenant_memberships / memberships
B1-3（P04）      0005, 0006        permissions / roles / role_permissions / platform_memberships / platform_state
B1-4（P06）      0007             resources / acl_subject_types / resource_permissions
B1-5（P07）      0008             tools / tool_versions / tool_permissions
 corrective       0009            平台时间精度 timestamptz(3)（20 表 / 72 列）
 recovery         964ea2c         仓库基线补入（0001–0006 + Alembic runtime + test harness + 8 docs）
────────────────────────────────────────────────────────────────────
★ B1-6（P08）     0010（预计）     ai_providers → ai_models → ai_routes → ai_policies → ai_request_logs
```

---

## 2. B1-6 内部对象依赖（拓扑）

```
                ┌──────────────────┐
                │  ai_providers    │  ROOT（平台级，无 tenant_id，零依赖）
                └────────┬─────────┘
                         │ provider_id  CASCADE
                         ▼
                ┌──────────────────┐
                │   ai_models      │
                └───┬──────────┬───┘
                    │          │
     primary_model_id│          │model_id
                  RESTRICT     RESTRICT
                    │          │
                    ▼          │
        ┌──────────────────┐   │
        │   ai_routes      │   │
        └──────────────────┘   │
                               ▼
    ┌──────────────────┐   ┌────────────────────┐
    │  ai_policies     │   │  ai_request_logs   │  ← 分区表
    └──────────────────┘   └────────────────────┘
        （与 ai_request_logs 可并行 —— SCHEMA_DEPENDENCY:212）

外部前置（均已存在，不重建）
    tenants ──▶ ai_routes.tenant_id      RESTRICT
    spaces  ──▶ ai_routes.space_id       RESTRICT
    tenants ──▶ ai_policies.tenant_id    RESTRICT
    spaces  ──▶ ai_policies.space_id     RESTRICT
    ai_providers ──▶ ai_request_logs.provider_id  RESTRICT
    ai_models    ──▶ ai_request_logs.model_id     RESTRICT
```

**创建顺序（拓扑序）**

```
1. ai_providers                       （ROOT）
2. ai_models                          （依赖 1）
3. ai_routes                          （依赖 2 + tenants + spaces）
4. ai_policies                        （依赖 tenants + spaces）
5. ai_request_logs（父表）             （依赖 ai_providers + ai_models）
6. ai_request_logs 当月子分区           （依赖 5）
4 与 5 可并行（`SCHEMA_DEPENDENCY:212`）
```

---

## 3. FK 清单（8 条 —— 逐条，无模糊描述）

| # | 子表.列 | → 目标 | ON DELETE | NULL | 依据 |
|---|---|---|---|---|---|
| F1 | `ai_models.provider_id` | `ai_providers.id` | **CASCADE** | NN | 冻结文档明确（`ER_MODEL:479` · `CORE:380` · `CONSTRAINT_MATRIX:316`） |
| F2 | `ai_routes.primary_model_id` | `ai_models.id` | **RESTRICT** | NN | 冻结文档明确（`SCHEMA_DEPENDENCY:74` · `CONSTRAINT_MATRIX:327`） |
| F3 | `ai_routes.tenant_id` | `tenants.id` | **RESTRICT** | NULL | **D-B16-02 = FROZEN — A** |
| F4 | `ai_routes.space_id` | `spaces.id` | **RESTRICT** | NULL | **D-B16-02 = FROZEN — A** |
| F5 | `ai_policies.tenant_id` | `tenants.id` | **RESTRICT** | NULL | **D-B16-02 = FROZEN — A** |
| F6 | `ai_policies.space_id` | `spaces.id` | **RESTRICT** | NULL | **D-B16-02 = FROZEN — A** |
| F7 | `ai_request_logs.provider_id` | `ai_providers.id` | **RESTRICT** | NULL | **D-B16-03 = FROZEN — A** |
| F8 | `ai_request_logs.model_id` | `ai_models.id` | **RESTRICT** | NULL | **D-B16-03 = FROZEN — A** |

```
FK 合计 = 8     （CASCADE 1 · RESTRICT 7）
```

### 3.1 明确「不建立 FK」的列（**D-B16-03 = FROZEN — A**）

```
ai_request_logs.agent_id        → 无 FK   （不构成 P08 → P09 前向依赖）
ai_request_logs.actor_id        → 无 FK
ai_request_logs.tenant_id       → 无 FK
ai_request_logs.space_id        → 无 FK
```

**不得扩大**：`tenant_id` / `space_id` 的 FK **只**存在于 `ai_routes` / `ai_policies`（D-B16-02），
**不得**扩展到 `ai_request_logs`。

### 3.2 `ai_providers` 无 FK（ROOT）

```
ai_providers FK 行 = 0
ai_providers 无 tenant_id 列（D-B16-11 = FROZEN — A）
```

---

## 4. Forward Dependency 检查

| 检查 | 结果 | 依据 |
|---|---|---|
| **P08 → P09 forward FK** | **0** ✅ | `ai_request_logs.agent_id` / `actor_id` 无 FK（D-B16-03） |
| P08 是否引用 P09 对象（agents / agent_versions / agent_permissions / tool_executions） | **0** ✅ | `CONSTRAINT_MATRIX` ai_* 段 FK 行逐条核对（见 §3） |
| P08 是否引用 P10 对象（events / audit_logs） | **0** ✅ | 同上 |
| P08 是否引用未裁定对象 | **0** ✅ | 8 条 FK 全部指向已存在的表（`ai_providers` / `ai_models` / `tenants` / `spaces`） |
| 是否需要「先建表后补 FK」绕道 | **不需要** ✅ | 无真循环（见 §5） |

### 4.1 B0 既有前向依赖（**非 B1-6，仅记录**）

`SCHEMA_DEPENDENCY.md:138-144` 记录的 3 条前向依赖：`agent_permissions.tool_id → tools`（已由 P07 先于 P09 消解）·
`agents.default_route_id → ai_routes`（**由 P08 先于 P09 消解 —— 本阶段是消解方**）·
`tool_executions.agent_id → agents`（P09 内部）。

---

## 5. 循环 FK 检查

**B1-6 内部循环 = 0**（DAG）。**无需 `DEFERRABLE` / 无需 deferred FK。**

```
a. ai_request_logs 是否为 ai_models 的父？  → 否（ai_models 无 FK 指向 ai_request_logs）  ✅ 非循环
b. ai_routes 是否为 ai_models 的父？        → 否（ai_models 无 FK 指向 ai_routes）        ✅ 非循环
c. ai_policies 是否被引用？                 → 否（无任何 FK 指向 ai_policies）             ✅ 非循环
d. tenants/spaces 是否有出边指向 ai_*？      → 否                                            ✅ 非循环
```

### 5.1 B0 既有循环（**非 B1-6，仅记录**）

```
agents.current_version_id ──(SET NULL)──→ agent_versions.id
agent_versions.agent_id   ──(CASCADE)──→ agents.id
```
该循环属 **P09**，其 deferred FK（`fk_agents_current_version`）**在 P09 尾部补**。

> **D-B16-08 = FROZEN — C —— 陈旧引用说明义务（本阶段承载）**
>
> `STEP1B_SCHEMA_DEPENDENCY.md:136` 原文写「…该约束加入 **Phase 08** 尾部。」
> **该处「Phase 08」属于陈旧引用；`agents.current_version_id` deferred FK 的正式归属为 P09。**
> 正确归属证据：`:170`（P09 行「补 agents.current_version_id FK」）· `B0_GATE_REPORT:45`（`P09 agent(…+补 FK)`）·
> `B1-4_DEPENDENCY:132`（P09 Agent）· `B1-5_SCOPE:42`（P09）。
> **物理事实**：P08 时 `agents` 表不存在 ⇒ 照 `:136` 字面执行 `ALTER TABLE agents` 不可执行。
> **D-B16-08 = C 决定不回改 B0**；本段即 B1-6 侧的加注义务履行。

---

## 6. 既有对象复用（不重建）

| 对象 | 来源 | 本阶段动作 |
|---|---|---|
| `set_updated_at()` 函数 | 0003（B1-1） | **复用**（挂 4 个 trigger），**不重建** |
| `uap_uuid_v7()` 函数 | 0002（B1-0） | 复用（主键生成兜底），不重建 |
| `tenants` 表 | 0004（B1-2） | 仅作为 FK 目标 |
| `spaces` 表 | 0004（B1-2） | 仅作为 FK 目标 |
| 既有 27 个 trigger | B1-1 ～ B1-5 | 不触碰 |
| 既有 15 个 public 函数 | B1-0 ～ B1-5 | 不触碰 |

---

## 7. 对下游 phase 的契约（只记录，不实现）

| 下游 | 契约 | 依据 |
|---|---|---|
| **P09 Agent** | `agents.default_route_id → ai_routes.id ON DELETE SET NULL`（**P09 侧建立**） | `SCHEMA_DEPENDENCY:143` · `CONSTRAINT_MATRIX:267` · `ER_MODEL:481` |
| **P09 Agent** | `agents.current_version_id` deferred FK **在 P09 尾部补**（与 P08 无关） | `SCHEMA_DEPENDENCY:170`（**不是** `:136`，见 §5.1） |
| **P09 Agent** | `ai_request_logs.agent_id` 保持**无 FK**；若未来要加，属**新决策**，须显式授权 | D-B16-03 = FROZEN — A 的「不得扩大」边界 |
| **P10 Event / Audit** | `events` / `audit_logs` 同为分区表（`occurred_at` 月分区 / PK `(id, occurred_at)`），约定共用；与 `ai_request_logs` **无 FK 关系** | `SCHEMA_DEPENDENCY:82-83/171` · `CORE:901` |
| **—（不建）** | `ix_aimodels_capability`：**D-2 = B FROZEN ⇒ 本阶段不建立 / 延后**；其 B0 定义引用 `ai_models` 上不存在的列 ⇒ **T-1 = DEFERRED** | `INDEX_STRATEGY:139` · D-2 · T-1 |
| **D-1 = B FROZEN** | `ai_policies` 的 `budget_daily_usd >= 0` / `latency_budget_ms >= 0`（B0「建议」）⇒ **不实现**；必做 CK 保持 8 | `B1-6_DECISION_LOG.md` §9.2 |

---

## 8. Core / Domain 依赖检查

```
core → domains / agent / intelligence / apps = 0   ✅
core 行业词 = 0                                    ✅
core 文件数 = 25
Architecture Guard = 9 passed                      ✅
```

**本阶段不新增任何跨层依赖**：P08 是纯 schema；不产生 `core → intelligence` 或 `core → ai_*` 的代码依赖
（架构铁律 3 由 `tests/architecture` 持续强制）。

---

## 9. 边界冲突登记（域内不一致 —— 只报告，不解决）

| # | 内容 | 处置 |
|---|---|---|
| **N-1** | `CORE_DOMAIN_MODEL:985` 将 `ai_models → ai_request_logs` 归入「**技术子实体**」类别（该节其余条目均 CASCADE 族），与冻结的 **RESTRICT** 不符 | **未解决** —— 改类别标签超出 AUTH-02「仅按 D-B16-02/03 修正 FK 事实」的范围。登记为 **DESIGN OBSERVATION / DEFERRED ISSUE**（见 `B1-6_SECURITY_REVIEW.md` §4） |
| **N-3** | `ai_request_logs` 带 FK RESTRICT ⇒ 删除 `ai_providers` / `ai_models` 前须先清 request log；与 `CORE:963`（90 天分区 hard delete）、`CORE:985`（模型目录随 provider purge 清理）的**运维顺序**需明确 | **本设计给出结论**（见 `B1-6_MIGRATION_PLAN.md` §7）—— 属 operational ordering，**不需要改变 D-B16-03**；**D-3 = D FROZEN** 后分区清理为人工职责，自动维护机制**不属于** B1-6 migration implementation |
| **O-1** | `ai_request_logs` 字段命名：`CONSTRAINT_MATRIX:351` 写 `tokens`，`CORE:413` 写 `prompt_tokens` + `completion_tokens` | **D-4 = A FROZEN** ⇒ 采用 CORE 细分命名；`tokens` 属**陈旧字面引用**，**本轮未授权修改 B0** |
| **O-2** | `ER_MODEL` ai_policies 块未画 `name`（ER 图为节选，非全量） | 以 `CONSTRAINT_MATRIX` / `CORE` 为准；不视为冲突 |
| **O-3** | `CORE:985` 未记录 `ai_request_logs.provider_id → ai_providers`（D-B16-03 新增的那条） | 超出 AUTH-02 范围，**未补**；登记为 DEFERRED |
| **T-1** | `STEP1B_INDEX_STRATEGY.md` 的 `ix_aimodels_capability ON (capability) WHERE enabled` 引用 `ai_models` 上**不存在**的列（该表只有 `capabilities jsonb`） | **DEFERRED / FUTURE DESIGN CLARIFICATION**（D-2 = B 同时登记；不改 B0、不决定目标列、不宣布作废） |

---

## 10. 校验汇总

```
FK = 8（逐条列于 §3；CASCADE 1 + RESTRICT 7）
P08 → P09 forward FK        = 0  ✅
B1-6 内部循环 FK            = 0  ✅
引用不存在的表              = 0  ✅
引用未裁定对象              = 0  ✅
无需 DEFERRABLE / 补 FK     = 是 ✅
既有对象复用（不重建）      = 5 项 ✅
Core → Domain               = 0  ✅
open 冲突（需另案）          = N-1 · O-3 · T-1（均仅登记；N-3 已定论；O-1 已由 D-4 = A 裁定）
设计层裁定                   = D-1 = B · D-2 = B · D-3 = D · D-4 = A · DC-1 = A（FROZEN）· T-1（DEFERRED）
```
