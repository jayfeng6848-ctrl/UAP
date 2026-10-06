# AGENT RUNTIME — IMPLEMENTATION CONTRACT（STAGE 3 · DESIGN FREEZE）

> ## 状态（先读这个）
>
> ```text
> DESIGN         = FROZEN          （依据 D-AGENT-01…D-AGENT-16，2026-09-25）
> IMPLEMENTATION = NOT STARTED     （本文件是契约，不是实现）
> IMPLEMENTATION GATE = CLOSED     （P10 ∧ P11 ∧ P12 ∧ P13 ∧ AI Gateway Runtime）
> MIGRATION / DDL / DML = 0
> COMMIT / TAG / PUSH   = NOT AUTHORIZED
> ```
>
> **权威层级**：冻结决策正文以 `PLATFORM_DECISION_LOG.md` 的 `D-AGENT-01`…`D-AGENT-16` 为**唯一权威**；
> 本文件是其在**契约层的展开**（字段、枚举、转换表、测试映射）。
> **本文件与冻结正文冲突时，以冻结正文为准**（Charter §2.3 同义）。
>
> **本文件不产生任何实施授权**（Charter §6）。凡标注 `DESIGN ONLY` 的对象**尚不存在**，
> 不得据此创建代码、表、迁移或配置。

---

# §A 基线与权威

| 项 | 值 |
|---|---|
| 冻结载体 | `PLATFORM_DECISION_LOG.md` → `D-AGENT-01`…`D-AGENT-16`（16 `FROZEN`） |
| HEAD | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e` |
| Alembic head | `0012_authz_enforcement`（单一 · `0013+ = 0`） |
| 既有 tag | `UAP-V0.1.8-AUTHORIZATION` |
| 继承冻结面 | `D-AUTH-01`…`D-AUTH-25` · `D-PLAT-01`…`D-PLAT-17` · P09 四表 |
| 阶段顺序 | `D-PLAT-09` 路线 A：`P10 → P11 → P12 → P13 → Runtime`（**未 supersede**） |

**继承不变式（禁止重造）**：`D-AUTH-01`（RBAC+ACL+Policy）· `D-AUTH-02`（Agent 独立主体）·
`D-AUTH-05`+`D-AUTH-25`（12 项小写 canonical action · NFKC→strip→casefold）·
`D-AUTH-06/08`（scope 与显式向下继承）· `D-AUTH-07/12`（`DENY > ALLOW` · FAIL CLOSED）·
`D-AUTH-09`（Tool = 唯一受控出口）· `D-AUTH-10`（四档 risk，≠ permission ≠ decision）·
`D-AUTH-11/14`（approval ≠ ALLOW）· `D-AUTH-13`（无授权缓存）· `D-AUTH-15`（三审计分离）·
`D-AUTH-16`（core=契约 / services=实现）· `D-AUTH-19`（单调整数 revision）·
`D-AUTH-21`（Memory / Workflow 授权 DEFERRED）· `D-AUTH-22`（UUIDv7）·
`D-AUTH-23`（`agent_permissions.resource_scope` = **Legacy Opaque**）。

---

# §B 范围

## B.1 IN SCOPE（契约层）

```text
Run 契约对象 · 状态机（8 态）· Context 八层管道 · Tool 提案边界
授权继承面 · 错误契约（8 类目 + 14 码）· 预算与限额 · 幂等与并发
API 契约（3 端点）· 持久化设计（DESIGN ONLY）· 依赖守卫清单 · 测试矩阵映射
```

## B.2 OUT OF SCOPE（本阶段明确不做）

```text
✗ 任何代码 / 包 / 模块创建（含 services/agentruntime/）
✗ 任何 migration / DDL / DML（含 agent_runs / agent_run_steps 建表）
✗ Worker 实现（Celery / Redis Queue / RabbitMQ / 其他具体框架）— D-AGENT-12
✗ Streaming（SSE / WebSocket）                                  — D-AGENT-11 DEFERRED
✗ AI Gateway Hard Cost Limit                                    — D-AGENT-10 DEFERRED
✗ Memory / Workflow 授权语义                                    — D-AUTH-21 DEFERRED
✗ events / audit_logs（P10）                                    — D-AGENT-15
✗ P09 四表 / 0011 / 0012 的任何修改
```

---

# §C 契约对象（`core/agent/run/` · DESIGN ONLY）

延续 `D-AUTH-16` 模式（core = 契约与纯规则 · 无 I/O）：

| 对象 | 设计职责（DESIGN ONLY） | 依据 |
|---|---|---|
| `AgentRunRequest` | `request_id`（UUIDv7 · `D-AUTH-22`）· `tenant_id` · `space_id?` · `actor`（SubjectRef）· `agent_ref` · `version_ref?` · `input`（受 `input_schema` 约束）· `metadata`（脱敏白名单）· `correlation_id?` · `idempotency_key?` · `deadline?` | `D-AGENT-01/02/08` |
| `AgentRunContext` | 解析产物 + 预算 + 授权上下文的**不可变快照**：`run_id` · `agent_id` · `agent_version_id` · `revision` · `delegation`(actor/agent/delegator) · `budget` · `layers`（八层快照引用） | `D-AGENT-04` · `D-AUTH-03`（base-only） |
| `AgentRunState` | 8 态枚举 + **纯函数** `transition(state, event) -> state`；非法转换 ⇒ `InvalidTransition`（fail closed） | `D-AGENT-05` |
| `AgentRunResult` | `state` · `output`（受 `output_schema` 校验）· `usage`（**透传**自 Gateway）· `steps` 摘要 · `error?` | `D-AGENT-14/15` |
| `AgentRunError` | `category`（8 外层类目）· `code`（14 canonical）· `retryable` · `reason`（结构化，非自由文本判类） | `D-AGENT-14` |
| `AgentRunBudget` | `time` · `tokens` · `ai_calls` · `tool_calls` · `steps` 的**已用/上限**；**只减不增**；`child ≤ parent remaining` | `D-AGENT-09/10` |
| `Executor`（抽象） | 执行抽象接口：**唯一**执行入口形态；进程内实现 / 未来 worker 均实现之 | `D-AGENT-12` |

**兼容约束**：既有 `agent/runtime/interfaces.py`（`AgentInput` / `AgentRunResult` / `AgentRuntime` Protocol）
为 **EXTEND 而非 REPLACE** —— `run(agent_id, payload)` 保留为薄兼容门面，内部转 `AgentRunRequest`。

---

# §D 状态机（8 态 · table-driven）

`D-AGENT-05` 冻结状态集合：

```text
CREATED · RUNNING · WAITING · WAITING_APPROVAL · COMPLETED · FAILED · CANCELLED · TIMEOUT
终态（不可再转换）= COMPLETED · FAILED · CANCELLED · TIMEOUT
```

## D.1 转换表（穷举 · 未列出的组合一律 `InvalidTransition`）

| # | From | Event | To | 来源 |
|---|---|---|---|---|
| 1 | `CREATED` | `start` | `RUNNING` | PREP §7 |
| 2 | `RUNNING` | `complete` | `COMPLETED` | PREP §7 |
| 3 | `RUNNING` | `fail` | `FAILED` | PREP §7 |
| 4 | `RUNNING` | `cancel` | `CANCELLED` | PREP §7 |
| 5 | `RUNNING` | `timeout` | `TIMEOUT` | PREP §7 |
| 6 | `RUNNING` | `wait_input` | `WAITING` | PREP §7 |
| 7 | `WAITING` | `resume` | `RUNNING` | PREP §7 |
| 8 | `WAITING` | `cancel` | `CANCELLED` | PREP §7（「任意态 → CANCELLED」） |
| 9 | `RUNNING` | `need_approval` | `WAITING_APPROVAL` | `D-AGENT-05`（唯一入口 = `REQUIRES_APPROVAL`） |
| 10 | `WAITING_APPROVAL` | `approved` | `RUNNING` | `D-AGENT-05` + `D-AUTH-14` |
| 11 | `WAITING_APPROVAL` | `rejected` | `FAILED` | PREP §29 |
| 12 | `WAITING_APPROVAL` | `cancel` | `CANCELLED` | PREP §7 |
| 13 | `WAITING_APPROVAL` | `timeout` | `TIMEOUT` | PREP §7 |
| 14 | `CREATED` | `cancel` | `CANCELLED` | PREP §7（「任意态 → CANCELLED」） |

**规则（`D-AGENT-05` 冻结）**：

1. `State transition = table-driven`（穷举表，**非** if 链）。
2. `Invalid transition = reject / fail closed` —— 抛 `InvalidTransition`，**不得静默跳转**。
3. `WAITING_APPROVAL` **只能**由 `AuthorizationDecision = REQUIRES_APPROVAL` 进入；
   **不得**由模型输出直接进入。
4. 审批完成后（`approved`）**必须重新执行 Authorization + Policy Evaluation**；
   **不得复用旧的授权结果**（`D-AUTH-13` 无缓存精神）。
5. 同一 `run_id` 的重复事件 = **no-op**（幂等，`D-AGENT-08`）。

> **契约层留项（REPORT-ONLY）**：`WAITING → timeout` 与 `CREATED → timeout` 未见于 PREP §7 原文，
> 本契约**不擅自新增**；若实施期需要，属**契约扩展**，须在实施前显式记录（见 §O 登记格式）。

---

# §E Context 管道（八层 · `D-AGENT-04`）

## E.1 层定义（冻结逻辑分层）

| # | 层 | 内容 | 授权动作 | 边界 |
|---|---|---|---|---|
| 1 | `System` | pinned version `definition` 的 system 部分 | — | **不可被 input 覆盖** |
| 2 | `Tenant` | 租户级静态设定 | `read` | tenant 谓词 |
| 3 | `Space` | 空间级设定 | `read` | space 谓词 |
| 4 | `User` | actor 偏好（**最小化**） | `read` | actor 自身 |
| 5 | `Agent` | 当前 agent / revision 元数据 | — | 只读快照 |
| 6 | `Task` | 本次 `input` | — | 经 `input_schema` 校验 |
| 7 | `Retrieved` | 检索层（**接口位**，本阶段不实现） | `read` | Lazy retrieval，**须重过检查** |
| 8 | `Tool` | 工具 schema 描述（来自 `allowed_tools` ∩ 授权可见集） | `read` | 交集 |

**每层必须**：`Authorized` · `Bounded` · `Traceable`。

## E.2 装配与不可变性（冻结）

```text
Context Snapshot = 本次 Run 的不可变上下文事实基线（装配后冻结）
Lazy Retrieval   = 允许，但 Retrieval 结果【必须重新经过】authorization / policy / boundary checks
```

**明确禁止**（`D-AGENT-04`）：

```text
✗ Database dump → Prompt
✗ Retrieved content → System instruction（data 层永不升级为指令层）
✗ 整表 / 任意查询结果直接注入 prompt（每层来源须为显式声明的 provider 契约）
```

## E.3 进入 AI Gateway 前的四道门（顺序固定）

```text
1. Authorization     （subject=AGENT, action=read, resource=层来源）
2. Data Boundary     （tenant / space 查询层谓词 —— 跨租户【结构性不可达】）
3. Sensitivity Filter（resources.classification 四档；HIGHLY_CONFIDENTIAL 禁降级）
4. Token Budget      （§J）
```

语义区分（**冻结**）：**过滤失败 ⇒ 剔除该层**（防 DoS）；**授权失败 ⇒ 内容不可用**（fail closed）——
两者**不得**混同。

## E.4 超限策略（优先级序）

```text
drop lowest-priority layer → truncate（保序）→ summarize（计入预算）→ 拒绝 Run
```

**禁止**：无限扩容 · 隐藏超限 · 用模型 confidence 决定截断。

---

# §F 授权与 Tool 提案边界（`D-AGENT-03` · 继承 `D-AUTH-09`）

```text
模型输出 TOOL_CALL 提案
  ↓ schema 校验（tool 名 ∈ version.allowed_tools；参数经 schema）
  ↓ AuthorizationService（Subject=AGENT · action=execute · resource=tool/<key> · tenant/space 范围）
  ↓ PolicyEvaluator（conditions / risk；tools.max_risk_level ∩ agent.max_risk_level）
  ↓ Approval（REQUIRES_APPROVAL ⇒ WAITING_APPROVAL；批准后【重新求值】）
  ↓ ToolRuntime（未来阶段；本阶段仅契约位）
  ↓ 审计（tool execution ≠ authorization audit ≠ run audit）
```

**冻结不变式**：

- `LLM Plan / LLM Output` **≠** `Execution Authority`（`D-AGENT-03`）。
- `allowed_tools` 是**上限**，授权是**下限**，二者取**交**。
- 未经 `ALLOW` 的提案**不得**触 ToolRuntime（fail closed）。
- **语义越权**（要求未授权工具）⇒ 直接拒绝该提案 + 记安全审计，**不重试**。
- 安全判定**只**来自 `AuthorizationService` / `Policy` —— 模型 confidence **不得**作为安全决策。
- `agent_permissions.resource_scope` **不参与**任何判定（`D-AUTH-23`）。

---

# §G Decision Freeze Gate（§22 十项校验）

> 执行日期 **2026-09-25**，同一冻结快照。命令与原始输出见本文件 **§G.2**；
> 汇总见 `AGENT_RUNTIME_PREP_REPORT.md` §44 与 `PLATFORM_DECISION_LOG.md` 附录 F.6。

## G.1 结果矩阵

| # | 校验项 | 判定 | 证据 |
|---|---|---|---|
| 1 | Decision consistency | **PASS** | §G.2-1 |
| 2 | Architecture consistency | **PASS** | §G.2-2 |
| 3 | Security consistency | **PASS** | §G.2-3 |
| 4 | API consistency | **PASS** | §G.2-4 |
| 5 | Dependency consistency | **PASS** | §G.2-5 |
| 6 | P09 protection | **PASS** | §G.2-6 |
| 7 | Migration integrity | **PASS** | §G.2-7 |
| 8 | Acceptance mapping（16/16 traceability） | **PASS** | §G.2-8 |
| 9 | Cross-decision scan（Charter §7） | **PASS** | §G.2-9 |
| 10 | Scope scan（本轮写入面） | **PASS** | §G.2-10 |

## G.2 命令与结果

```text
环境    HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · branch main · remote none
账本    ../uap-stage3-evidence/decision_freeze_gate.log（仓库外，2026-09-25）
执行    python（managed 3.13.12）· 只读（git show / git diff / git status / sha256 / 词法解析）
结果    10 / 10 PASS · DECISION FREEZE = PASSED · exit 0
```

| # | 校验项 | 关键证据（实测） |
|---|---|---|
| 1 | Decision consistency | PDL `D-AGENT` 条目 **16** · 条目状态 `FROZEN` **16** · RESOLUTION `HUMAN DECISION = FROZEN` **16** / `PENDING` **0** / `STATUS = PROPOSED` **0** · traceability 行 **16** · 选项序列 `C/B/C/C/A/B/A/B/C/B/B/B/B/B/C/A+C` **= 期望序列** |
| 2 | Architecture consistency | `ARCHITECTURE.md` 授权状态 = **implemented and accepted** · 新增 `## Agent runtime (design frozen)` · 陈旧串 `has not been created` = **0** · `DEPENDENCY_RULES.md` 新增 `## 9. Agent runtime boundary` · 陈旧串 = **0** |
| 3 | Security consistency | `docs/security/README.md` 新增 `## Agent runtime security` · 三项不变式（`LLM output ≠ trusted execution command` / `Cancellation ≠ rollback` / `No vendor SDK`）齐备 · 陈旧串 = **0** |
| 4 | API consistency | `docs/api/README.md` 新增 `## Agent runs (design frozen)` · canonical actions = **小写**（`D-AUTH-25`） · 大写残留 = **0** · 陈旧串 = **0** |
| 5 | Dependency consistency | 厂商 SDK import（`core`/`intelligence`/`agent`/`services`/`apps`）= **0** · worker 框架 import（`celery`/`redis`/`pika`/`amqp`/`kombu`/`rq`）= **0** · `infrastructure/ai/` = **不存在** · `services/agentruntime/` = **不存在** |
| 6 | P09 protection | `0010` sha256 = `6d9907237f80e9da…` **逐字节未变** · `0011` sha256 = `cdaf8383630335db…` **逐字节未变** · `git diff HEAD -- migrations_alembic/` = **空** · `git diff HEAD -- core/ services/ agent/ intelligence/ infrastructure/ tests/ apps/ migrations/` = **空** |
| 7 | Migration integrity | 版本文件 **12** · revision **12** · **heads = `['0012_authz_enforcement']`（单头）** · 匹配 `0013+` 的文件 = **0** · `0012` sha256 = `5ecd1ef30b403fb4…` |
| 8 | Acceptance mapping | 矩阵 **117** 行 = `ASSET` **16** + `PASSED` **4** + `FROZEN-DESIGN` **95** + `BLOCKED-GATE` **2** · traceability **16/16** · 指令 §21 的 **17** 个测试类别 **无缺失**<br>（2026-09-25 `O-1` 裁定后：`FAIL-05` 新增 ⇒ 116 → **117**；见矩阵 §11 / §19） |
| 9 | Cross-decision scan（Charter §7） | **PDL 相对 HEAD 的删除行 = 恰 1 行**，且删除内容 = **顶部 `Status` 行**（⇒ 既有决策正文 **零改写**：`D-PLAT-09` · `D-AUTH-01..25` · `D-PLAT-01..17` · Charter §1–§6 · 附录 A–E 全部原状） · `D-AUTH` 条目 = **25** · Charter §7 = 存在 · 附录 F.6/F.7 = 存在 · 本文件 §G = 存在 |
| 10 | Scope scan | 变更文件 **9** 个，**全部为 `.md`**，**全部落在** Freeze Authorization §20 的授权集内（8 份同步文档 + 1 份新建契约）：`outside set = none` · `non-.md = none` |

**§G.3 冲突扫描结论（Charter §7.2 三类）**

```text
ACTIVE vs FROZEN 冲突 = 0
FROZEN vs FROZEN 冲突 = 0
SCHEMA vs DECISION 冲突 = 0
陈旧一致性缺陷 = 3 处（STAGE 2 遗留 · 已于本轮修正 · 登记于 PDL 附录 F.7）
```

> 扫描面（`Charter §7.1` 五类）：本载体 · 阶段型决策日志（`B1-4`/`B1-5`/`B1-6`/`P09`/`STEP1B_B1_2`/`STEP1B_B1_3`）·
> 架构面（`ARCHITECTURE.md`/`DEPENDENCY_RULES.md`/`CORE_DOMAIN_MODEL.md`/`ER_MODEL.md`）·
> Schema 面（`P09_*`/`B1-6_*`/`STEP1B_CONSTRAINT_MATRIX`/`SCHEMA_DEPENDENCY`/`TRIGGER_INVENTORY`/`INDEX_STRATEGY`/`SEED_STRATEGY`）·
> 契约面（`AUTHORIZATION_IMPLEMENTATION_CONTRACT`/`SCHEMA_IMPACT`/`IMPLEMENTATION_TEST_MATRIX`/`STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT`）。
> 登记处：`PLATFORM_DECISION_LOG.md` 附录 **F.6**（扫描结果）· **F.7**（陈旧缺陷修正）。

---

# §H 并发与幂等（`D-AGENT-06` · `D-AGENT-08`）

## H.1 并发模型

| 项 | 冻结内容 |
|---|---|
| Run 级 | **允许并发**：`Agent A Run 1` 与 `Agent A Run 2` 可同时存在 |
| 步级 | **未授权**（同一 Run 内**不**并行工具调用） |
| Action 级 | **幂等强制** |
| **资源冲突补强** | 对**存在真实资源冲突风险**的 Tool Action，**必须**使用**资源版本 / 条件更新 / 等价并发控制**；**仅有 idempotency 不足以解决所有 race condition** |
| 硬约束 | `same resource + same mutation` **不得**因并发产生不可控重复或覆盖（lost update 亦属违规） |

## H.2 幂等契约（必须定义项）

| 项 | 设计要求（DESIGN ONLY） |
|---|---|
| `Key` | 调用方提供 `idempotency_key`（Run 级）；Tool 级另有 action 幂等键 |
| `Scope` | 命名空间 = `(tenant_id, idempotency_key)`；**跨租户不共享** |
| `TTL` | 幂等记录保留窗口（数值待实施期冻结） |
| `Collision` | 同键不同载荷 ⇒ **拒绝**（不得"最后一次覆盖"） |
| `Replay` | 重复请求返回**首次结果**（或进行中状态），**绝不二次执行** |
| `Result Reuse` | 复用首次结果，不重放副作用 |
| 非幂等工具 | 在缺少幂等键的重试场景下 **拒绝执行**（fail closed） |
| **硬约束** | `Network Retry` + `Worker Retry` **不得**导致**重复的真实世界操作** |

---

# §I 错误契约（8 外层类目 + 14 canonical codes · `D-AGENT-14`）

## I.1 外层 8 类目（DESIGN FROZEN · 契约层展开）

| # | 外层类目 | 语义 | 归属码（见 I.2） |
|---|---|---|---|
| 1 | `REQUEST_INVALID` | 请求不可受理（校验/参数） | `INVALID_REQUEST` |
| 2 | `AGENT_UNAVAILABLE` | 目标 agent / version 不可用 | `AGENT_NOT_FOUND` · `AGENT_NOT_ACTIVE` · `VERSION_NOT_FOUND` |
| 3 | `AUTHORIZATION_DENIED` | **业务拒绝**（显式、可审计，≠ 系统故障） | `AUTHORIZATION_DENIED` |
| 4 | `AUTHORIZATION_FAILURE` | **系统故障**（fail closed ⇒ 结果仍为 DENY） | `AUTHORIZATION_FAILURE` |
| 5 | `AI_PROVIDER` | 厂商/网关侧依赖失败（**含 Provider 层 timeout** —— `O-1`） | `AI_PROVIDER_FAILURE`（唯一的 provider 类码，见 §O-1） |
| 6 | `MODEL_OUTPUT` | 模型输出不可解析 / 不合 schema | `INVALID_MODEL_OUTPUT` |
| 7 | `TOOL` | 工具依赖失败 | `TOOL_ERROR` · `TOOL_TIMEOUT` |
| 8 | `RUNTIME` | 运行时内部失败 / 预算 / 超时 / 用户取消 | `RUNTIME_ERROR` · `TIMEOUT` · `BUDGET_EXCEEDED` · `USER_CANCELLED` |

> **类目 8 内含 `USER_CANCELLED` 与 `TIMEOUT` 两个码** —— `D-AGENT-14` 要求二者**可区分**
> （区分在**码层**，不要求分属不同类目）。
>
> **`O-1` 已裁定（`RESOLVED / APPROVED` · 2026-09-25）**：类目 5 中**不存在独立的 provider-timeout 码** ——
> `AI_TIMEOUT` **合并归入 `AI_PROVIDER_FAILURE`**，**不作为** canonical error code（详见 §O-1）。
> 类目 5 因此**只有一个** canonical code。

## I.2 14 canonical codes（8 条具名 + 6 条契约层枚举 = **14** · `O-1` 已由 Human 裁定）

**A. 冻结条文直接具名（8 条 · 不可改名）**

```text
AUTHORIZATION_DENIED · AUTHORIZATION_FAILURE · USER_CANCELLED · TIMEOUT
AI_PROVIDER_FAILURE · INVALID_MODEL_OUTPUT · TOOL_ERROR · RUNTIME_ERROR
```

**B. 契约层枚举（6 条 · 受冻结结构约束；**算术已闭合**）**

```text
INVALID_REQUEST · AGENT_NOT_FOUND · AGENT_NOT_ACTIVE · VERSION_NOT_FOUND
TOOL_TIMEOUT · BUDGET_EXCEEDED
```

> 枚举依据 = PREP §28 候选码表（`carried forward`，未重新裁定）；
> **算术闭合** = 具名 8 + 候选 7 **− `AI_TIMEOUT`**（⊂ `AI_PROVIDER_FAILURE`）= **14**。
> **`O-1` = RESOLVED / APPROVED（2026-09-25 Human Decision）** —— 裁定正文见
> `PLATFORM_DECISION_LOG.md` 附录 **F.8**，契约登记见 **§O-1**。
> **`AI_TIMEOUT` 不作为独立 canonical code**；**`BUDGET_EXCEEDED` 保持独立**，**禁止**并入 `TIMEOUT`。

## I.3 不可合并的四对语义（`D-AGENT-14` 冻结）

| 对 | 必须可区分的原因 |
|---|---|
| `AUTHORIZATION_DENIED` ≠ `AUTHORIZATION_FAILURE` | 业务拒绝 vs 系统故障 —— 审计可辨、告警不同、**均 fail closed**（`D-AUTH-12`） |
| `USER_CANCELLED` ≠ `TIMEOUT` | 主体意志 vs 系统上界 —— 取消 ≠ 失败 |
| `AI_PROVIDER_FAILURE` ≠ `INVALID_MODEL_OUTPUT` | 依赖故障 vs 内容不合格 —— 前者可重试，后者按 §I.4 |
| `TOOL_ERROR` ≠ `RUNTIME_ERROR` | 工具侧 vs 运行时侧 —— 责任域不同 |

> **`TIMEOUT` 的语义边界（`O-1` 裁定 · 不改变四对区分）**：
> `TIMEOUT` = **Agent Run / Runtime 整体执行期限**超时；
> **Provider 层 timeout 归 `AI_PROVIDER_FAILURE`**（`AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE`，不设独立码）。
> 四对区分**逐条不变**，尤其 `USER_CANCELLED` ≠ `TIMEOUT`。

## I.4 映射规则（**deterministic** · 冻结）

```text
① Error mapping 必须 deterministic（同 (state, cause) ⇒ 同 (category, code)）
② 【禁止】通过异常字符串判断业务类型
③ 【禁止】把 AUTHORIZATION_FAILURE 呈现为业务拒绝（反之亦然）
④ 重试性由 (category, code) 决定，不依赖异常类型名
⑤ 终端 API 状态码由 category 映射（授权拒绝 403 · 资源不可用 404 · 请求无效 400 ·
   取消 409/499 语义 · 系统故障 500 · 依赖故障 502/504）
```

---

# §J 预算与限额（`D-AGENT-09` · `D-AGENT-10`）

## J.1 三层限额（`D-AGENT-09`）

```text
Effective Limit = min(Platform Limit, Tenant Limit, Agent Limit)       ← Strictest Limit Wins
缺失层限制 ⇏ 无限制；【必须继承】上层限制
```

| 维度 | 覆盖层 |
|---|---|
| `max_tool_calls` | Platform / Agent / Tenant |
| `max_runtime_steps` | Platform / Agent / Tenant |
| `max_ai_calls` | Platform / Agent / Tenant |
| `max_duration` | Platform / Agent / Tenant |

载体（**复用既有 jsonb，设计层 0 schema 变更**）：`tenants.settings` · `agent_versions.definition`。

**禁止**：所有上限**不得被 LLM 自行提高**。

## J.2 多维预算（`D-AGENT-10`）

| 维度 | 状态 |
|---|---|
| `Time` | 计入 |
| `Tokens` | 计入（权威来自 Gateway usage） |
| `AI Calls` | 计入 |
| `Tool Calls` | 计入 |
| `Steps` | 计入 |
| `Cost` — Cost Tracking | **允许**（**透传 / 可观测**，非硬限额） |
| `Cost` — Hard Cost Limit | **DEFERRED** until AI Gateway Runtime ready |

```text
Child Budget ≤ Parent Remaining Budget
预算只减不增；重试【不重置】预算
【禁止】在 Gateway 无可靠 cost model 时伪造 cost enforcement
```

---

# §K API 契约（`D-AGENT-11`）

| 方法 | 路径 | 语义 |
|---|---|---|
| `POST` | `/agent-runs` | 创建 Run（携带 `idempotency_key`）⇒ `202 Accepted` + `run_id` |
| `GET` | `/agent-runs/{id}` | 查询状态 / 结果（脱敏视图） |
| `POST` | `/agent-runs/{id}/cancel` | 取消（**幂等**） |

**冻结边界**：

```text
① 全部路由进入前必须先过 认证 / 租户解析 / 授权（Run 本身也是受控操作）
② Fast Path 可在 Run 已立即完成【且 API contract 明确允许】时返回完成结果，
   但【不得】创建第二套 execution model
③ Streaming（SSE / WebSocket）= DEFERRED，后续单独 Decision
④ 【禁止】未经 Decision 新增第四端点
```

---

# §L 持久化设计（`D-AGENT-13` · **DESIGN ONLY · 未建表**）

> ⚠ 本节为**设计**。`agent_runs` / `agent_run_steps` **当前不存在**（实测 `0013+ = 0`，
> 全仓 `.py` / `.sql` 对二表引用 = **0**）。**本轮 migration = 0。**

| 表 | 设计职责 | 要点 |
|---|---|---|
| `agent_runs` | `Run identity / lifecycle / result / budget / correlation` | PK = run id（UUIDv7）· FK → `agents` / `agent_versions` / `tenants` / `spaces` · `state` · `revision` · `checksum` · budget 计数 · `idempotency_key` 命名空间 · `created_at`/`updated_at` = `timestamptz(3)` |
| `agent_run_steps` | `Execution step state / ordering / retry / tool interaction` | 从属于 run（**严格从属 ⇒ 可 CASCADE**）· `step_index` 有序 · 与 `tool_executions` 关联（**复用，不重建**） |

**冻结边界（`D-AGENT-13`）**：

```text
✓ events / audit_logs 归 P10，【保持独立】
✗ 不得把 Audit Event 与 Run Step 混成一个表
✗ 不设立 agent_run_events（Run Step 归 agent_run_steps；审计事件归 P10）
✗ 不得把 agent_permissions.resource_scope 语义引入 run 载荷（D-AUTH-23）
✗ 不得复用 / 重建 ai_request_logs 与 tool_executions（既有载体）
```

**实施顺序约束**：`D-PLAT-09` 路线 A ⇒ 表创建须排在 **P10 → P11 → P12 → P13** 之后。

---

# §M 依赖与守卫

## M.1 允许的依赖方向

```text
Agent Runtime ─▶ AI Gateway Contract      （经 core 契约；D-AGENT-16）
Agent Runtime ─▶ Authorization Contract   （core 契约；实现经 services/authorization）
Agent Runtime ─▶ Tool Contract            （agent/tools 契约）
Agent Runtime ─▶ Execution abstraction    （Executor；D-AGENT-12）
```

## M.2 禁止的依赖（`D-AGENT-12` / `D-AGENT-16` / `D-PLAT-05`）

```text
✗ Runtime → OpenAI / Anthropic / Gemini / 其他 Provider SDK（直接）
✗ Runtime → PostgreSQL 直连（Agent → Policy → Tool → Service → Database）
✗ Runtime → Redis / Celery / RabbitMQ / 其他具体 worker framework
✗ core → services（G-2）· agent → services（G-3）· agent → infrastructure（G-4/既有）
```

## M.3 未来实施时必须新增的守卫（`tests/architecture/` · **尚未创建**）

| 守卫（建议 ID） | 断言 | 级别 |
|---|---|---|
| `G-10` | `services/agentruntime/**` 不 import 任何厂商 SDK | hard |
| `G-11` | `core/agent/**` 不 import `sqlalchemy` / `psycopg` / `infrastructure` | hard |
| `G-12` | `agent/**` 与 `services/agentruntime/**` 不 import `celery` / `redis` / `pika` / `amqp` | hard |
| `G-13` | 状态机转换表穷举（未列出组合必抛 `InvalidTransition`） | hard |
| `G-14` | 错误码 ∈ 14 canonical 集合（AST 比对契约常量） | hard |

> 依 `DEPENDENCY_RULES.md` 末节纪律：**写在文档而无测试的规则属文档，非强制**。
> 上述守卫须在**实施提交**中与代码同批落地；本轮**不创建**。

---

# §N 测试类别与验收映射

## N.1 指令 §21 要求的 17 个测试类别 ↔ 验收矩阵前缀

| 要求类别 | 矩阵前缀 | 覆盖 |
|---|---|---|
| `STATE` | `STATE-` | 8 态 + 转换矩阵 |
| `CONTEXT` | `CTX-` | 八层管道 / 快照 / 惰性检索 |
| `AUTHORIZATION` | `AUTH-` | 授权继承面 |
| `AI` | `AI-` | Gateway 契约 / 决策类型 |
| `TOOL` | `TOOL-` | 提案边界 |
| `TIMEOUT` | `TIME-` | 五层超时 + 总预算钳制 |
| `RETRY` | `RETRY-` | 三类重试分离 |
| `CANCEL` | `CANCEL-` | 五源取消 |
| `IDEMPOTENCY` | `IDEM-` | 双层幂等 |
| **`CONCURRENCY`** | **`CONCUR-`** | Run 级并发 + 资源版本控制 |
| `LOOP` | `LOOP-` | 环路检测 + 上限 |
| `SECURITY` | `SEC-` | 九威胁 |
| `API` | `API-` | 三端点 / 呈交 |
| `WORKER` | `WORKER-` | 执行抽象 |
| `OBSERVABILITY` | `OBS-` | 观测字段 / 脱敏 |
| `DATABASE` | `DATABASE-` + `MIG-` | 持久化设计 / 零迁移 |
| `DEPENDENCY` | `DEPENDENCY-` + `ARCH-` | 依赖方向 / 阶段门 |

> **17/17 全覆盖**；`CONCUR-` 为本轮依 `D-AGENT-06` **新增**前缀（矩阵 §12A）。

## N.2 验收矩阵

主表见 [`AGENT_RUNTIME_ACCEPTANCE_MATRIX.md`](./AGENT_RUNTIME_ACCEPTANCE_MATRIX.md)（含 §18 traceability 16/16）。

---

# §O 契约层枚举登记（`O-1` = **RESOLVED**）

> 本区登记**契约层枚举项**：它们**不构成**未决 OQ、**不构成**冲突、**不改变**任何冻结语义。
> 登记目的：使实施期不得静默裁定。
> **`O-1` 已于 2026-09-25 经 Human Decision 裁定（`APPROVED`）** —— 见 §O-1；
> `O-2`…`O-4` 仍为登记项（见 §O-3）。

## O-1 错误码枚举算术 —— **RESOLVED / APPROVED（2026-09-25 Human Decision）**

### O-1.a 裁定正文

```text
Human Decision = APPROVED

AI_TIMEOUT 合并归入 AI_PROVIDER_FAILURE，【不作为】独立 canonical error code。

语义解释：
  TIMEOUT              = Agent Run / Runtime 整体执行期限超时
  AI_PROVIDER_FAILURE  = AI Provider 层执行失败（【包括】 Provider Timeout）
  ⇒ AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE

性质：不是新增 canonical code；不改变已冻结的 8 类错误类别、14 个 canonical error codes，
      以及四对不可合并语义。
```

### O-1.b 算术闭合（15 → 14）

```text
冻结条文：14 canonical error codes（D-AGENT-14）
  具名 8 条（冻结条文直接给出）
+ 契约层候选 7 条（PREP §28 carried forward）：
    INVALID_REQUEST · AGENT_NOT_FOUND · AGENT_NOT_ACTIVE · VERSION_NOT_FOUND ·
    AI_TIMEOUT · TOOL_TIMEOUT · BUDGET_EXCEEDED
= 候选合计 15
− 1（AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE，不设独立码）
= 14  ✅ 与冻结条文一致

⇒ §I.2 的 canonical 集合 = A(8) + B(6) = 14；`AI_TIMEOUT` **不在集合内**。
```

### O-1.c 强约束（Human 明示 · 不得违反）

```text
✗ 不得增加第 15 个 canonical error code
✗ 不得将 BUDGET_EXCEEDED 合并到 TIMEOUT      （BUDGET_EXCEEDED 保持独立 canonical code）
✗ 不得修改 OQ-AGENT-14 / D-AGENT-14 的其他冻结语义
✓ 8 类错误类别 · 14 个 canonical error codes · 四对不可合并语义 —— 逐条不变
```

> **不采纳的备选（登记留痕，不实施）**：本契约 §O-1 原登记的等价备选为
> `TOOL_TIMEOUT` ⊂ `TOOL_ERROR` · `BUDGET_EXCEEDED` ⊂ `TIMEOUT` · `AGENT_NOT_ACTIVE` ⊂ `AGENT_NOT_FOUND`。
> 其中 **`BUDGET_EXCEEDED ⊂ TIMEOUT` 已被 Human 明示禁止**；其余备选**未采纳**
> （现行裁定 = `AI_TIMEOUT` 合并）。**上述备选在本契约内不再构成合法变更路径**；
> 任何改动仍须新的 Human Decision。

### O-1.d 只读一致性验收（2026-09-25 · 验收账本 `../uap-stage3-evidence/o1_acceptance.log`）

| # | 验收项 | 结果 |
|---|---|---|
| 1 | `O-1` arithmetic = resolved | **PASS** |
| 2 | canonical error codes = exactly 14 | **PASS** |
| 3 | `D-AGENT-14` = consistent across all authoritative documents | **PASS** |
| 4 | cross-decision conflicts = 0 | **PASS** |
| 5 | migration files = unchanged | **PASS** |
| 6 | code / test / config = unchanged | **PASS** |
| 7 | Runtime Implementation Gate = CLOSED | **PASS** |

## O-3 其他登记

| ID | 事项 | 性质 |
|---|---|---|
| `O-2` | `WAITING → timeout` · `CREATED → timeout`（PREP §7 未列） | 契约扩展候选，实施前须显式记录 |
| `O-3` | 幂等记录 `TTL` 具体数值 | 数值冻结（实施期） |
| `O-4` | 三层限额 / 五层超时的**具体数值** | 数值冻结（实施期，先行值见 PREP §20/§23） |

> `O-2`…`O-4` **未**被本轮裁定覆盖；保持**开放登记**状态，**未决项仍为 0**（它们不是 OQ）。

---

# §P 执行门禁与禁止清单

## P.1 门禁（`D-AGENT-16` + 引用 `D-PLAT-09` / `D-PLAT-12`）

```text
P10 READY ∧ P11 READY ∧ P12 READY ∧ P13 READY ∧ AI GATEWAY RUNTIME READY
        ⇒ Agent Runtime Implementation MAY OPEN
否则    ⇒ IMPLEMENTATION GATE = CLOSED          （当前状态：CLOSED）
```

## P.2 本轮禁止清单（HARD STOP 触发面）

```text
✗ D-PLAT-09 被改变（含 supersede / 重排阶段）
✗ AI Gateway SDK 直接依赖（Runtime / core / intelligence）
✗ 新 migration / 新 schema / 新 DDL / 新 DML
✗ Worker 实现（Celery / Redis Queue / RabbitMQ / 其他）
✗ P10 实现（events / audit_logs）
✗ P09 修改（四表 / 0011 / 0012）
✗ 未消解 OQ / 跨决策冲突 / 架构违规 / 安全旁路
✗ commit / tag / push
```

---

**END OF AGENT RUNTIME IMPLEMENTATION CONTRACT（DESIGN FREEZE · 2026-09-25）**
