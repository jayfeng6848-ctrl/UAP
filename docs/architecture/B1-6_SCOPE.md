# B1-6 Scope

**Stage**: B1-6（= P08 AI Gateway）· **Phase**: P08 · **Status**: DESIGN（未实施）
**输入**: Human Decision Freeze（D-B16-01 ～ D-B16-11，见 `B1-6_DECISION_LOG.md`）· B0 已同步口径
**边界**: 本文档只做范围界定，**不创建 migration、不创建表、不改代码/测试/B0**。

---

## 0. 关于 "B1-6" 这一编号（必读）

```
全库 `B1-6` / `B1.6` / `B16` / `b1_6` 字面命中 = 0（无预定义名称）
```

**D-B16-01 = FROZEN — A（2026-09-16）**：`B1-6 = P08 AI Gateway`。

**推导链（实际证据）**

| 来源 | 内容 |
|---|---|
| `STEP1B_SCHEMA_DEPENDENCY.md:169` | `\| **P08** \| AI Gateway \| ai_providers → ai_models → ai_routes → ai_policies → ai_request_logs \|` |
| `STEP1B_B0_GATE_REPORT.md:45` | `… P06 resource/ACL → P07 tool → P08 AI → P09 agent(+tool_executions+补 FK) → P10 …` |
| `B1-4_SCOPE.md:42` | `\| Tool / AI / Agent 域 \| P07 / P08 / P09 \| 依赖顺序在 resources 之后 \|` |
| `B1-5_SCOPE.md:41` | `\| P08 \| AI Gateway：ai_providers → ai_models → ai_routes → ai_policies → ai_request_logs \| :169 \|` |
| `0009_timestamp_precision.py:35` | 「因 0009 被本 correction 专用，**P08 后续 migration 编号顺延至 0010**」 |
| 实测对账 | P01–P07 全部已建（migration 0001–0009 · 20 张业务表无缺） |

> `B1-x → P-x` 映射**非 1:1**（B1-1 = P01+P02 · B1-2 = P03+P05 · B1-3 = P04）。
> **本冻结不得反向修改历史 B0 文档中已有的 phase 定义。**

---

## 1. Objective

在 P08 交付 **AI Gateway 的持久化数据模型**（5 张表 + 其约束/索引/触发器/分区），
使"厂商是数据行而非代码分支"（架构铁律 3）具备可存储的结构基础。

**本阶段只交付 schema 与其结构性不变式**；不交付任何 AI 运行时行为。

---

## 2. In Scope

```
表（5）
  ai_providers        平台级 ROOT（无 tenant_id）
  ai_models           模型目录（provider 技术子实体）
  ai_routes           capability → model 路由 / fallback 链
  ai_policies         分级 / 准入 / fallback / 预算 / 延迟策略
  ai_request_logs     成本 / 配额 / 可观测（分区表）

结构对象
  PK 5 · FK 8（7 RESTRICT + 1 CASCADE）· UQ 4（2 CONSTRAINT + 2 INDEX）
  CK 8（B0 另有 2 条「建议」CHECK —— **D-1 = B FROZEN ⇒ 不实现**）· trigger 4 · function 0 新增
  分区：ai_request_logs 父表 + 当月子分区（子分区命名 **DC-1 = A FROZEN**）
  索引：2 个唯一索引（表达式）+ ix_airl_tenant_occurred ⇒ 非 PK 索引共 5（**D-2 = B FROZEN：不建 P3 索引**）
  seed 0

配套交付
  B1-6 9 份设计文档（D-B16-09 = A）
  Canonical Test Matrix 规范（独立编号空间，D-B16-10 = A）
  未来 migration 0010 的规划（本轮不创建）
```

---

## 3. Out of Scope

```
tool_executions · agents · agent_versions · agent_permissions            ← P09
events · audit_logs                                                      ← P10
G / H / I / J（ACL trigger 四件套）                                       ← P09 后
agents.current_version_id 的 deferred FK · agents.default_route_id FK    ← P09
（见 §6 之 D-B16-08 = C 说明义务）
resource_relations                                                       ← P2 可选
P11 跨表 trigger 集中批次 · P12 纯查询索引 · P13 seed                     ← 后续 phase
Authorization Layer / 授权求值 / ABAC / RLS                               ← 不在本阶段
HTTP API / Socket.IO · 任何业务服务端实现                                 ← 0
Provider 适配器实现 · 模型调用 · 路由选择执行 · policy 求值               ← 见 §4
```

---

## 4. Deferred（本阶段明确不做，且不属后续 phase 的既有承诺）

| 项 | 归属判定 | 依据 |
|---|---|---|
| **adapter runtime**（解析 / 加载 / 注册 / 动态导入 / 运行时发现） | **本阶段不做**，后续阶段未指定 | **D-B16-06 = FROZEN — A**：`adapter` 仅文本引用（沿用 D-B15-09 口径） |
| **provider SDK loading** | 不做 | 架构铁律 3（core/intelligence 禁直接 import 厂商 SDK，`tests/architecture` 强制） |
| **secret storage implementation** | 不做 | `CORE:1047`「`secret_ref` 只存引用；任何表不得存 API Key 明文」；密钥管理实现不在本阶段 |
| **agent integration** | P09 | `ai_request_logs.agent_id` **无 FK**（D-B16-03）⇒ 本阶段与 Agent 无结构耦合 |
| **tool execution** | P09 | `tool_executions` 属 P09（`SCHEMA_DEPENDENCY:170`） |
| **路由 / fallback / 降级 执行引擎** | 不在本阶段 | 本阶段只存数据；`fallback_chain` 为 jsonb 存储 |
| **policy 求值 / 预算计算 / 延迟预算执行** | 不在本阶段 | 同上 |
| **分区维护 job / pg_partman** | **本阶段不做 —— D-3 = D FROZEN（手工运维）** | `STEP1A_DESIGN_REPORT:511 R2` 记录该需求；P08 只交付 parent + current-month child；自动化延后至未来 operational/runtime 阶段 |

---

## 5. Dependencies

```
前置（均已存在，本阶段不重建）
  tenants · spaces            ← 0004（B1-2）
  users                       ← 0003（B1-1）
  set_updated_at()            ← 0003（B1-1）· uap_uuid_v7() ← 0002（B1-0）

P08 内部
  ai_providers ──▶ ai_models ──▶ ai_routes ──┐
                      │                      ├─▶ ai_policies
                      └──────────────────────┴─▶ ai_request_logs
  （ai_policies 与 ai_request_logs 可并行 —— `SCHEMA_DEPENDENCY:212`）

下游
  P09 agents.default_route_id → ai_routes.id（SET NULL）  ← P09 引用 P08，方向正确
  P10 ai_request_logs 与 events/audit_logs 同为分区表（约定共用，无 FK 关系）
```

---

## 6. Phase Boundary

```
P07 Tool（已交付 0008）──▶ P08 AI Gateway（本阶段）──▶ P09 Agent
```

**边界事实**

| 项 | 判定 | 依据 |
|---|---|---|
| P08 → P09 forward FK | **0** | `ai_request_logs.agent_id` 无 FK（D-B16-03） |
| `agent_id` | **P08 不建立 FK** | D-B16-03 = FROZEN — A |
| `actor_id` | **P08 不建立 FK** | D-B16-03 = FROZEN — A |
| `tenant_id` / `space_id` | **仅在 `ai_routes` / `ai_policies` 范围内建 FK** | D-B16-02 = FROZEN — A；**不得扩大** |
| `tool_executions` | 不在本阶段 | `SCHEMA_DEPENDENCY:170` |
| G / H / I / J | 仍属 P09 后，**本阶段为 0** | `TRIGGER_INVENTORY` 既有声明 |
| **deferred FK 归属** | **P09**（不是 P08） | 见下 |

### 6.1 D-B16-08 = C 的说明义务（**必须在本阶段文档中承载**）

```
`STEP1B_SCHEMA_DEPENDENCY.md:136` 原文：
  「…该约束加入 Phase 08 尾部。」
  （语境：§4.1 agents ↔ agent_versions 真循环的 deferred FK 解法）

≡ 该处「Phase 08」属于陈旧引用；
≡ `agents.current_version_id` deferred FK 的正式归属为 P09。

正确归属证据：
  :170（P09 行）「… → 补 agents.current_version_id FK」
  STEP1B_B0_GATE_REPORT.md:45「P09 agent(+tool_executions+补 FK)」
  B1-4_DEPENDENCY.md:132「P09 Agent … deferred FK」
  B1-5_SCOPE.md:42「P09 … 补 agents.current_version_id FK」

D-B16-08 = FROZEN — C ⇒ 不回改 B0。加注义务由 B1-6 文档承载（即本段）。
物理事实：P08 时 `agents` 表不存在 ⇒ 若照 :136 字面执行 `ALTER TABLE agents` 不可执行。
```

---

## 7. Database Objects（预计 5 表）

| # | 表 | 角色 | tenant 维度 | 分区 |
|---|---|---|---|---|
| 1 | `ai_providers` | 平台级 ROOT | **无 tenant_id** | 否 |
| 2 | `ai_models` | provider 技术子实体 | 无（随 provider） | 否 |
| 3 | `ai_routes` | 路由/fallback | `tenant_id NULL` + `space_id NULL` | 否 |
| 4 | `ai_policies` | 分级/准入/预算 | `tenant_id NULL` + `space_id NULL` | 否 |
| 5 | `ai_request_logs` | 成本/可观测 | `tenant_id NULL` / `space_id NULL`（**无 FK**） | **是**（`occurred_at` 月分区） |

对象计数见 `B1-6_SCHEMA_DESIGN.md` §6。

---

## 8. Trigger Boundary

| 类别 | 清单 |
|---|---|
| **existing**（B1-1 ～ B1-5） | `set_updated_at`（14 表）· roles 系 3 · membership 系 3 · platform_memberships 系 2 · resources 系 2 · acl_subject_types_protect · `tg_version_immutable`（tool_versions） |
| **★ B1-6（4 个）** | `tg_ai_providers_set_updated_at` · `tg_ai_models_set_updated_at` · `tg_ai_routes_set_updated_at` · `tg_ai_policies_set_updated_at`（均复用 `set_updated_at()`） |
| **P09 后** | G / H / I / J —— **保持 0** |
| **future** | `tg_agent_versions_immutable`（P09，与 `tg_version_immutable` 共用同一名）· `tg_audit_logs_immutable`（P10） |

**边界声明**：B1-6 的 4 个 trigger **仅**维护 `updated_at` 赋值；**不做** authorization evaluation / role resolution / deny resolution / 任何 AI 运行时逻辑。
`ai_request_logs` **无 `updated_at`** ⇒ **无 trigger**（`TRIGGER_INVENTORY` 条目 A 的表清单不含该表）。

---

## 9. API Boundary

```
HTTP API    = 0
Socket.IO   = 0
gRPC        = 0
业务 service 层实现 = 0
```

本质因：P08 是**数据模型阶段**；调用链 `Agent → Policy → Tool → Service → DB` 的 Policy/Agent 侧尚未就位。
详见 `B1-6_API_DESIGN.md`。

**明确**：`B1-6_API_DESIGN.md` **不是** API 实现，只界定边界与未来契约。

---

## 10. Security Boundary

```
不引入 authorization evaluator / ABAC / RLS（RLS = 0）
不引入密钥存储实现（secret_ref = 仅引用；config 不含密钥）
不引入 P09 权限模型
不引入代码执行入口（adapter = 纯文本，D-B16-06 = A）
零 seed（不产生任何内置行）
```

详见 `B1-6_SECURITY_REVIEW.md`。

---

## 11. Seed Boundary

```
seed rows = 0
```

依据：`STEP1B_SEED_STRATEGY.md` 中 `ai_` **0 命中**；P00–P10 均无 seed，**P13 才有 seed**。
**不得** seed `ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs`。
**D-B16-11 = FROZEN — A** 明确 `ai_providers` 零 seed。

---

## 12. Migration Boundary

```
本轮：0010 = ABSENT（不创建）
预期 revision：0010（编号由 0009 docstring:35 指定"P08 顺延至 0010"）
约束：revision id ≤ 32 字符（alembic_version.version_num = varchar(32)）· filename == revision
```

详见 `B1-6_MIGRATION_PLAN.md`。

---

## 13. Test Boundary

```
本阶段（DESIGN）新增/修改测试 = 0
Implementation tests written = 0
```

`B1-6_TEST_MATRIX.md` 为 **DESIGN SPECIFICATION ONLY**。
实施轮的连带修改（FORBIDDEN 集合 + head 断言）见该文档 §9。

---

## 14. Decisions

```
D-B16-01 … D-B16-11 = ALL FROZEN（10 × A + 1 × C）·  OPEN = 0 ·  BLOCKING = 0
```

| ID | 裁定 | 内容 |
|---|---|---|
| D-B16-01 | **A** | B1-6 = P08 AI Gateway |
| D-B16-02 | **A** | `ai_routes` / `ai_policies` 的 `tenant_id` / `space_id` → FK + `ON DELETE RESTRICT`（四列均 nullable） |
| D-B16-03 | **A** | `ai_request_logs.provider_id` / `.model_id` → FK + `RESTRICT`；**不含 `agent_id`** |
| D-B16-04 | **A** | `ai_request_logs.status`：**零新增取值域 CHECK**；Canonical Test Matrix 中 **S5 明确豁免** |
| D-B16-05 | **A** | `ai_request_logs`：P08 建父表 + 当月子分区 |
| D-B16-06 | **A** | `adapter` 仅文本引用；不引入解析/加载/注册/运行时机制 |
| D-B16-07 | **A** | UQ 口径：`UNIQUE CONSTRAINT = 2` · `UNIQUE INDEX = 2` |
| D-B16-08 | **C** | 不回改 B0 `:136`；说明义务由 B1-6 文档承载（见 §6.1） |
| D-B16-09 | **A** | 沿用 B1-5 的 9 份文档模式 |
| D-B16-10 | **A** | 独立编号空间 Canonical Test Matrix（须登记 S5 EXEMPT） |
| D-B16-11 | **A** | `ai_providers` 平台级 ROOT / 无 tenant_id / 零 seed |

**设计层事项（已由 Human 于 2026-09-16 裁定，权威记录见 `B1-6_DECISION_LOG.md` §9）**

| ID | 裁定 | 内容 |
|---|---|---|
| D-1 | **B** | `ai_policies` 两条「建议」CHECK ⇒ **不实现**（必做 CK 保持 8） |
| D-2 | **B** | `ix_aimodels_capability` ⇒ **不建立 / 延后**（非 PK 索引保持 5） |
| T-1 | **DEFERRED** | `INDEX_STRATEGY` 的 `ix_aimodels_capability` 引用 `ai_models` 上不存在的列（只有 `capabilities jsonb`） |
| D-3 | **D** | 分区维护 ⇒ **手工运维**（P08 不做自动化） |
| D-4 | **A** | 字段命名 = `prompt_tokens` + `completion_tokens`（= 设计现状，列数保持 73） |
| DC-1 | **A** | 子分区命名 = `ai_request_logs_<YYYYMM>`（UTC calendar month） |

---

## 15. Gate

```
B1-6 SCOPE = DESIGN（已通过 Human 审核）
B1-6 DESIGN DECISION FREEZE = PASS
B1-6 IMPLEMENTATION = BLOCKED
0010 = ABSENT
DATABASE = UNTOUCHED · B0 = PROTECTED
```
