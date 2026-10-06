# AGENT RUNTIME — PREP REPORT（STAGE 3 · READ-ONLY DESIGN）

> **状态（先读这个）**
>
> ```text
> 本文档 = PREP / DESIGN / AUDIT 产物
> 本文档 ≠ 冻结 ≠ 实现 ≠ 授权
> ```
>
> 所有设计内容均为 **PROPOSED**，须经 Human Decision Freeze（`D-AGENT-*`）后方可进入
> Implementation Contract。本报告**不构成**任何实施授权（Charter §6）。
>
> **两条先决张力（REPORT-ONLY，已识别、未消解，见 §21 / §22）：**
> ① `D-PLAT-09`（FROZEN，路线 A）冻结了 **P10 → P11 → P12 → P13 → Runtime** 的阶段顺序
> —— 本 PREP 是设计工作，不违反路线 A；但 **Runtime 实施**在 P13 完成前不可启动。
> ② **AI Gateway 当前实现 = 0**（0010 只有 schema：`ai_providers` / `ai_models` /
> `ai_routes` / `ai_policies` / `ai_request_logs`，`infrastructure/ai/` 不存在）——
> Agent Runtime 实施以 AI Gateway 实施为硬前置。

---

## 1. Executive Summary

本报告为 UAP 第一个统一 Agent Runtime 建立设计基础：Run 生命周期、Agent/Version 解析、
Context 边界、AI 决策类型、Tool 提案边界、失败/超时/取消/幂等/环路防护模型、安全分析、
架构放置、API 与 Sync/Async 选项、DB 影响、测试矩阵与 **15+1 项 OQ（OQ-AGENT-01..16）**。

核心设计立场（全部 PROPOSED）：

1. **Run 是一等对象**：`AgentRun` 有状态机、预算、幂等键与审计身份；`AgentRuntime.run()`
   从"一次性调用"升级为"受治理的 Run"。
2. **LLM 输出 ≠ 执行授权**：模型输出只是 *提案*（proposal），必须经 Parse → Schema
   Validation → Policy → Authorization → (Approval) → Tool。
3. **一切从既有冻结继承**：不新造授权语义（继承 `D-AUTH-*` 全部 25 条）、不新造版本语义
   （`D-AUTH-19` 单调整数）、不解释 `resource_scope`（`D-AUTH-23`）。
4. **零实现**：本阶段仅产出 Contract 与验收矩阵。

---

## 2. Baseline（§2 实测）

| 项 | 值 |
|---|---|
| HEAD | `034ee97c315e5d483acb7ac4b7e8e0eb992ef10e`（`feat(authz): implement authorization model and enforcement`） |
| Tags | `UAP-V0.1.7-GOVERNANCE-GATE` → `eb6d4cb` · **`UAP-V0.1.8-AUTHORIZATION` → `034ee97`** |
| Alembic head | `0012_authz_enforcement`（单一 · branches none · 0013+ = 0） |
| 0010 | `6d9907237f80e9da…` 未变 · 0011 = `cdaf8383630335db…` 未变 · 0012 = `5ecd1ef30b40…`（本轮起始实测） |
| 工作树 | clean（本 PREP 仅新增本文档 + 验收矩阵） |
| 授权面 | `D-AUTH-01..25`（22 FROZEN + 3 DEFERRED · 平台级 supersession 1）—— Source of Truth |

---

## 3. 现有授权契约（§3，Runtime 必须继承的冻结面）

| 冻结决策 | 对 Runtime 的直接约束 |
|---|---|
| `D-AUTH-01` RBAC+ACL+Policy | 每次 Run 内的工具/资源访问都走 `AuthorizationService`（`services/authorization/`），不得自带第二套判定 |
| `D-AUTH-02` Agent = 独立主体 | Agent 以自身 Subject（`AGENT`）进入授权；不得自动继承 User 权限 |
| `D-AUTH-03`（DEFERRED → 本阶段） | 只设计 **base delegation context**（actor / agent / delegator 区分），lifecycle 留待后续 |
| `D-AUTH-05` + `D-AUTH-25` | Action 词表 12 项、**小写存储形**、NFKC→strip→casefold |
| `D-AUTH-06` / `D-AUTH-08` | scope = PLATFORM/TENANT/SPACE 存储 + RESOURCE/SELF 谓词；显式向下继承 |
| `D-AUTH-07` / `D-AUTH-12` | DENY > ALLOW · DEFAULT DENY · **FAIL CLOSED**（授权不可用 ⇒ DENY，绝不 fail-open） |
| `D-AUTH-09` | Tool = 唯一受控执行出口；Tool 不得旁路 Authorization |
| `D-AUTH-10` | 风险四档（`LOW/MEDIUM/HIGH/CRITICAL`）≠ Permission ≠ Decision |
| `D-AUTH-11` | `approval_required = tool intrinsic OR policy`；审批 ≠ ALLOW |
| `D-AUTH-13`（DEFERRED → Tool Runtime） | Runtime **不得**自建授权缓存 |
| `D-AUTH-14` | Decision 三值；`REQUIRES_APPROVAL` 非执行许可 ⇒ Run 进入 `WAITING_APPROVAL` |
| `D-AUTH-15` / `D-AUTH-22` | 授权审计 ≠ 工具执行审计 ≠ **Agent Run 审计**（三者分离）；事件 ID UUIDv7 |
| `D-AUTH-19` | Agent Version = **单调整数 revision**；runtime identity ≠ 展示串 |
| `D-AUTH-23` | `agent_permissions.resource_scope` = **OPAQUE**：Runtime 不得解析/规范化/提升 |

---

## 4. Agent Model（§4，P09 substrate 实测）

`agents`（执行实体，**不是模型**）：`tenant_id`（RESTRICT）· `space_id NULL` · `owner_id → users` ·
`current_version_id NULL → agent_versions` · `key`（`uq_agents_key on (tenant_id, lower(key)) WHERE archived_at IS NULL`）·
`status IN ('draft','active','disabled','archived')` · `max_risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')` ·
`default_route_id NULL → ai_routes.id` · `config jsonb` · `archived_at`。

`agent_versions`（不可变快照）：`version int` · `definition jsonb` · `input_schema jsonb NULL` ·
`output_schema jsonb NULL` · `allowed_tools jsonb` · `checksum` · `status IN ('draft','published','deprecated','revoked')` ·
`published_at`；**published 后 UPDATE/DELETE 被 trigger 禁止**（双保险）。

`agent_permissions`：`permission_id NULL` / `tool_id NULL` / `resource_scope NULL（OPAQUE，D-AUTH-23）` /
`effect ∈ ('allow','deny')` / `conditions jsonb`；三选一 CK + `uq_agent_perm`（COALESCE 归一）。

**设计结论**：解析（§8/§9）所需的全部数据面已存在；`max_risk_level` 与 `default_route_id`
为 Run 预算与模型路由提供了权威来源；**无需任何新表**即可完成解析语义（§35）。

---

## 5. AI Gateway 关系（§5）

实测：**AI Gateway 实现 = 0**。0010 提供了 5 张表（`ai_providers` / `ai_models` / `ai_routes` /
`ai_policies` / `ai_request_logs`（分区表）），`infrastructure/ai/` **不存在**，无 Provider Adapter 代码。

关系（PROPOSED）：

```text
Agent Runtime（编排）
      ↓  AI Gateway Contract（core 契约 + services 实现，同 D-AUTH-16 模式）
AI Gateway（实现：路由 ai_routes / 记账 ai_request_logs / provider adapter）
      ↓
Provider（openai / anthropic / …—— 经 adapter，Agent Runtime 永不直接 import 厂商 SDK）
```

- Runtime 只依赖 **Gateway 契约**（`CompleteRequest/CompleteResponse/usage`），不知道 provider。
- 模型路由的权威 = `ai_routes`（agents.default_route_id 已指向它）；Runtime 不自选模型。
- usage/token/cost 记账权威 = Gateway（`ai_request_logs`）；Runtime 只透传 run_id 关联（§24）。
- **依赖缺口（REPORT-ONLY）**：Gateway 实施是 Runtime 实施的硬前置（见 §22）。

---

## 6. Core Run Model（§6，契约对象 · PROPOSED）

放在 `core/agent/run/`（纯值对象与纯规则，无 I/O——延续 `D-AUTH-16` 的 core=契约 / services=实现 分层）：

| 对象 | 内容（PROPOSED） |
|---|---|
| `AgentRunRequest` | `request_id`（UUIDv7，`D-AUTH-22`）· `tenant_id` · `space_id NULL` · `actor`（SubjectRef）· `agent_ref`（key 或 id）· `version_ref NULL`（缺省=解析）· `input`（受 `input_schema` 约束）· `metadata`（脱敏白名单）· `correlation_id NULL` · `idempotency_key NULL` · `deadline NULL` |
| `AgentRunContext` | 解析产物 + 预算 + 授权上下文的不可变快照（§12），含 `run_id`、`agent_id`、`agent_version_id`、`revision`、`delegation`（§11）、`budget`（§14/§20） |
| `AgentRunState` | 状态机（§7），纯函数 `transition(state, event) -> state`，非法转换抛 `InvalidTransition` |
| `AgentRunResult` | `status` · `output`（受 `output_schema` 校验）· `usage`（透传自 Gateway）· `steps` 摘要 · `error NULL` |
| `AgentRunError` | 错误契约（§28）：`code`（14 值枚举）· `category`（business_denial / system_failure / dependency_failure / user_cancelled）· `retryable` · `reason` |
| `AgentRunBudget` | tokens / steps / tool_calls / wall-clock / ai_calls 计数与上限（§14/§20/§23），**只减不增**，超限触发既定策略 |

现有 `agent/runtime/interfaces.py`（`AgentInput/AgentRunResult/AgentRuntime` Protocol）为 **EXTEND**
而非 REPLACE：`run(agent_id, payload)` 保留为薄兼容门面，内部转 `AgentRunRequest`。

---

## 7. Run State Machine（§7，PROPOSED）

```text
CREATED → RUNNING → {COMPLETED | FAILED | CANCELLED | TIMEOUT}
RUNNING → WAITING → RUNNING            （等外部输入：无授权含义）
RUNNING → WAITING_APPROVAL → {RUNNING | CANCELLED | TIMEOUT}
                    （批准 ⇒ 回 RUNNING 且继续；拒绝/撤销 ⇒ FAILED/CANCELLED，绝不自动执行）
任意态 → CANCELLED（用户/管理员取消，传播见 §21）
RUNNING → TIMEOUT（全局预算耗尽）
```

| 规则 | 内容 |
|---|---|
| 合法转换 | 仅上表；实现为**穷举表驱动**（非 if 链），非法转换 = `InvalidTransition`（fail closed） |
| `WAITING_APPROVAL` | 仅由 `AuthorizationDecision = REQUIRES_APPROVAL`（`D-AUTH-14`）进入；**不得**由模型输出直接进入 |
| 终态 | `COMPLETED/FAILED/CANCELLED/TIMEOUT` 为终态，不可再转换 |
| 幂等 | 同一 `run_id` 重复事件 = no-op（§22） |

---

## 8. Agent Resolution（§8，PROPOSED）

输入 `(tenant_id, space_id?, agent_ref)` → 输出唯一 active agent；全部失败路径**不得自动执行**：

| 失败 | 判定 | Run 错误码（§28） |
|---|---|---|
| 不存在 | tenant 内无该 key/id | `AGENT_NOT_FOUND` |
| 已禁用 | `status='disabled'` | `AGENT_NOT_ACTIVE` |
| 已归档 | `archived_at IS NOT NULL` 或 `status='archived'` | `AGENT_NOT_ACTIVE` |
| 草稿 | `status='draft'`（不可被调用） | `AGENT_NOT_ACTIVE` |
| 越权 | actor 对该 agent 无 `execute` 授权（经 AuthorizationService） | `AUTHORIZATION_DENIED` |

顺序（PROPOSED）：**存在性 → 状态 → 授权**；每次判定产出授权审计事件（`D-AUTH-15`，persistence → P10）。

---

## 9. Version Resolution（§9，继承 `D-AUTH-19`）

`agent.current_version_id` 为权威默认；`request.version_ref` 仅允许**显式 pin**：

| 输入 | 解析 |
|---|---|
| 无 version_ref | `current_version_id`；若 NULL ⇒ `VERSION_NOT_FOUND` |
| `version_ref = int` | 精确 revision；`uq_agent_versions(agent_id, version)` 唯一 |
| pinned 但 status ≠ published | `VERSION_NOT_FOUND`（draft/deprecated/revoked 均不可执行） |
| 正常 | 必须且只能 `status='published'` |

**不可变性**：published 后 trigger 禁改 ⇒ Runtime **只读**版本快照（`definition/allowed_tools/schema/checksum`），
运行期不存在"热更新"；`checksum` 进入 run 观测记录（§25）以便复现。

---

## 10. Request Model（§10）

见 §6 `AgentRunRequest`。**关键区分（冻结继承）**：

```text
actor  = 发起 Run 的人类/系统主体（Subject，USER 或 service 身份）
agent  = 独立授权主体（D-AUTH-02）—— 授权按 AGENT 计算，不按 actor
delegator = base delegation context 中的"代表谁"记录（D-AUTH-03：仅记录，无生命周期）
```

`input` 必须通过该 pinned version 的 `input_schema` 校验；未提供 schema 时按"仅允许 JSON 标量/容器，
拒绝二进制"处理（fail closed）。

---

## 11. Delegation Context（§11，`D-AUTH-03` base-only）

Run 全生命周期携带不可变三元组：`actor` / `agent` / `delegator`（= actor 的记录，显式声明"本次 Run
以 agent 身份、受 actor 委托"）。**不实现** grant/revoke/expiry/scope 生命周期（`D-AUTH-03` Exit
Condition 留给后续独立裁定）。约束：Agent 有效权威**永不**因 delegator 而扩大（`D-AUTH-02`）。

---

## 12. Context Builder（§12，PROPOSED）

分层装配，每层独立可测、可审计、可限额：

```text
System（版本快照 definition 的 system 部分）
  + Tenant（租户级静态设定）
  + Space（空间级设定）
  + User（actor 偏好，最小化）
  + Agent（当前 agent/revision 元数据）
  + Task（本次 input）
  + Retrieved（未来检索层 —— 接口位，不在本阶段实现）
  + Tool（工具 schema 描述，来自 allowed_tools ∩ 授权可见集）
```

**严禁**把数据库整表/任意查询结果直接注入 prompt；每层来源必须是**显式声明的 provider 契约**
（签名 + 授权 + 限额），禁止 arbitrary Python/SQL 注入（§42）。

---

## 13. Context Authorization（§13）

进入 AI Gateway 前，Context 组装管道必须通过：

1. **Authorization**：每个 retrieved/tool 层按 (subject, action=`read`, resource) 求值；
2. **Data Boundary**：tenant/space 谓词过滤（`D-AUTH-06/08`）——跨租户内容**结构性不可达**；
3. **Sensitivity Filter**：`resources.classification` 四档门槛（HIGHLY_CONFIDENTIAL 禁降级）；
4. **Token Budget**：§14 限额。

任何一层失败 ⇒ 该层内容整体剔除并记审计；**剔除 ≠ 报错**（避免 DoS），但**授权失败 ≠ 剔除**
（= 该内容不可用，fail closed）。

---

## 14. Context Size / Token Budget（§14）

`AgentRunBudget`（PROPOSED 初始值，待 OQ-AGENT-10 冻结）：
`max_system_tokens` / `max_retrieval_tokens` / `max_context_tokens` / `max_tool_result_tokens` /
`max_total_tokens`（从 Gateway usage 回读累计）。

超限策略（优先级序）：**drop lowest-priority layer → truncate（保序截断）→ summarize（Gateway 二次调用，
计入预算）→ 拒绝 Run（`RUNTIME_TIMEOUT` 前置失败：`BUDGET_EXCEEDED` 归入 `INVALID_REQUEST` 族）**。
禁止：无限扩容、隐藏超限、用 LLM confidence 决定截断。

---

## 15. Intent / Plan Model（§15，OQ-AGENT-03）

两个候选均保留为 OQ：

- **Response-only**：单次 Gateway 调用 → 最终输出。简单、低成本、无工具编排能力。
- **Plan-first**：input → intent → plan（工具提案序列）→ 逐项 Authorization → 执行 → 综合。
  能力强但引入循环/预算/部分失败问题（§23）。

**共同不变式（不受 OQ 结果影响）**：无论哪种模式，模型产出的每一步都是 **proposal**，
执行前走 §17 边界。**本 PREP 不假设 Planner 必须存在**——由 Human Decision 冻结。

---

## 16. AI Decision Types（§16，PROPOSED）

Gateway 结构化输出（经 §18 校验后）恰好为以下之一：

```text
FINAL_RESPONSE | TOOL_CALL | REQUEST_APPROVAL | ASK_USER | RETRY | FAIL
```

不变式：**LLM output ≠ execution authorization**。`TOOL_CALL` 只是提案；`REQUEST_APPROVAL`
只是"建议请求审批"，真正的 `WAITING_APPROVAL` 只能由 AuthorizationService 的
`REQUIRES_APPROVAL` 触发；无法解析/不属六类 ⇒ `INVALID_MODEL_OUTPUT`（fail closed）。

---

## 17. Tool Call Boundary（§17）

```text
模型输出 TOOL_CALL 提案
  ↓ schema 校验（tool 名 ∈ version.allowed_tools，参数 schema 校验）
  ↓ AuthorizationService（Subject=AGENT, action=execute, resource=tool/<key>, scope=run 的 tenant/space）
  ↓ PolicyEvaluator（conditions/risk —— tools.max_risk_level 与 agent.max_risk_level 相交）
  ↓ Approval（REQUIRES_APPROVAL ⇒ WAITING_APPROVAL，人工批准后重入）
  ↓ ToolRuntime（未来阶段；本阶段仅契约位）
  ↓ 结果 → 审计（tool execution ≠ authorization audit ≠ run audit）
```

禁止 `LLM → direct execution`；`allowed_tools` 是**上限**，授权是**下限**，二者取交。

---

## 18. AI Output Validation（§18）

```text
raw output → parse（严格 JSON）→ schema 校验（version.output_schema / 决策类型 schema）
→ 决策类型识别 → Policy → Authorization → 执行
```

失败分级：parse 失败 = `INVALID_MODEL_OUTPUT`（可按 §19 重试 1 次）；schema 不匹配 = 同上；
**语义越权**（如要求未授权工具）= 直接拒绝该提案并记安全审计（不重试）。

---

## 19. Retry Model（§19，三类分离）

| 类别 | 可重试 | 上限（PROPOSED） | 说明 |
|---|---|---|---|
| **Model Retry**（Gateway 调用失败：429/5xx/超时） | 是 | 2 次 · 指数退避（1s/4s） | 计入预算与 wall-clock |
| **Tool Retry**（工具暂失败） | 仅 `retryable=true` 且**幂等**工具 | 1 次 | 非幂等工具禁止重试（§22） |
| **Runtime Retry**（整个 Run 重跑） | 仅 idempotency_key 显式提供且首次失败为依赖类 | 1 次 | 由调用方发起，Runtime 不自循环 |

不可重试：`AUTHORIZATION_DENIED`（业务拒绝）、`INVALID_REQUEST`、终态后的任何事件。
所有重试计入 `AgentRunBudget`；重试不重置预算。

---

## 20. Timeout Model（§20，PROPOSED）

| 层 | 缺省（PROPOSED） | 关系 |
|---|---|---|
| Context Build | 2s | 包含授权求值 |
| Authorization（单次） | 2s | 与 `D-PLAT-16` readiness 2000ms 独立，不共享全局默认 |
| AI Gateway（单次调用） | 30s | Gateway 内部可再分 provider 超时 |
| Tool（单次调用） | 15s | Tool Runtime 细化 |
| **Run Total（wall-clock）** | **60s** | **硬上界**：所有层超时之和被 Run 预算钳制，累加不得超过总预算 |

超时 ⇒ `CANCELLED(timeout)` 传播（§21）→ 终态 `TIMEOUT`；已启动且不可撤销的 Tool 调用
记录为"orphaned execution"并强制审计。

---

## 21. Cancellation（§21）

五种来源统一为一个取消事件：`USER_CANCEL` / `CLIENT_DISCONNECT` / `SYSTEM_SHUTDOWN` /
`TIMEOUT_CANCEL` / `ADMIN_CANCEL`。传播规则（PROPOSED）：

1. **检查点式协作取消**（无跨进程强杀）：状态机在每次 Gateway/Tool 调用前后检查取消标志；
2. 取消 ⇒ 当前工具调用尽力中止；不可中止者记 orphaned execution + 审计；
3. 终态 `CANCELLED`；`WAITING_APPROVAL` 中取消 ⇒ 审批单作废（P10 载体，未来）；
4. `CLIENT_DISCONNECT` **不**默认取消 Run（async 模式下 Run 继续至终态，结果留存）——PROPOSED，OQ-AGENT-07。

---

## 22. Idempotency（§22）

- `idempotency_key`（调用方提供）+ `tenant_id` 构成幂等命名空间；重复请求返回**首次结果**（或进行中状态），绝不二次执行；
- **Tool 层**：幂等工具（声明 `idempotent=true`）允许重试；非幂等工具遇到重试场景必须先有幂等键，否则拒绝（fail closed）；
- Worker 重试（未来）以 run 级幂等键为去重权威；
- 幂等记录的持久化属 §35 PROPOSED（OQ-AGENT-02/13）——**本阶段不建表**。

---

## 23. Loop Protection（§23）

`AgentRunBudget` 内置：`max_tool_calls`（PROPOSED 10）· `max_runtime_steps`（PROPOSED 25）·
`max_runtime_duration`（= §20 总预算）· `max_ai_calls`（PROPOSED 8）。
**Loop Detection**：对 `(tool_key, 规范化参数哈希)` 维护调用序列；同一签名在窗口内重复 ≥ 2 次 ⇒
判定循环 ⇒ 终止（`FAILED`，reason=`loop_detected`，非 retryable）。全部计数**只减不增**。

---

## 24. Cost Governance（§24）

Runtime **不计算成本**，只**透传关联键**：Gateway 记 `ai_request_logs`（token/成本权威），
Tool Runtime 记工具成本，Runtime 记时长与步数。三方以 `run_id`/`trace_id` 关联，避免重复计算。

---

## 25. Observability（§25，PROPOSED）

每次 Run 必备观测字段：`run_id`（UUIDv7）· `request_id` · `trace_id` · `tenant_id` · `actor_id` ·
`agent_id` · `agent_version_id` · `revision` · `checksum` · `model/route` · `state` · `latency` ·
`result/error code` · budget 消耗。**敏感输入/输出不入普通日志**（沿用 `infrastructure/logging/redaction.py`
双重脱敏基线）；完整 payload 仅存于受控审计面（P10）。

---

## 26. Audit（§26，三分离）

```text
Agent Run Audit（run 生命周期：状态转换/预算/错误）
  ≠ Authorization Decision Audit（D-AUTH-15：决策/reason/policy/risk/approval）
  ≠ Tool Execution Audit（执行期：参数摘要/结果/outcome）
```

三者以 `run_id` 关联但**不得合并为一张表/一个事件流**；persistence 均属 **P10**（`events`/`audit_logs`
当前不存在——实测），契约面（`core/audit`）先行，实现 deferred（`D-AUTH-15`）。

---

## 27. Security（§27，分析 · 全部"已识别，防御位已设计"）

| 威胁 | 防御位（PROPOSED） |
|---|---|
| Prompt Injection（直接） | input 经 schema 校验；system 层与 input 层**物理分离**；system 不可被 input 覆盖 |
| Indirect Injection（经 retrieved/tool 结果） | 检索/工具结果标记为 **data 层**，永不进入指令层；工具结果再注入前重过预算与过滤（§13） |
| Tool Injection | 工具集 = `allowed_tools` ∩ 授权 ∩ policy；提案必须逐项授权（§17） |
| Context Leakage | 层间隔离 + sensitivity filter + tenant 谓词（§13） |
| Cross-Tenant Leakage | tenant 谓词为**结构性**过滤（查询层），非提示词约束（§13） |
| Privilege Escalation | Subject=AGENT 独立授权；delegator 不扩权（§11）；`resource_scope` 不参与（`D-AUTH-23`） |
| Agent Impersonation | agent 解析必须经 tenant 绑定校验（uq_agents_key per tenant）+ 授权 |
| Unauthorized Tool Call | `TOOL_CALL` 提案未经 ALLOW 不得触 ToolRuntime（§17，fail closed） |
| **LLM confidence 当安全决策** | **禁止**——安全判定只来自 AuthorizationService/Policy；模型输出只是提案（§16） |

---

## 28. Failure Model（§28，错误契约 PROPOSED）

| code | category | retryable |
|---|---|---|
| `INVALID_REQUEST` | business_denial | no |
| `AGENT_NOT_FOUND` / `AGENT_NOT_ACTIVE` | business_denial | no |
| `VERSION_NOT_FOUND` | business_denial | no |
| `AUTHORIZATION_DENIED` | **business_denial**（≠ 系统故障） | no |
| `AUTHORIZATION_FAILURE` | **system_failure**（fail closed ⇒ DENY，`D-AUTH-12`） | no |
| `AI_PROVIDER_FAILURE` | dependency_failure | per §19 |
| `AI_TIMEOUT` | dependency_failure | per §19 |
| `INVALID_MODEL_OUTPUT` | system_failure | 1 次（§18） |
| `TOOL_ERROR` / `TOOL_TIMEOUT` | dependency_failure | per §19 |
| `RUNTIME_TIMEOUT` / `BUDGET_EXCEEDED` | system_failure | no |
| `CANCELLED` | user_cancelled | no |
| `INTERNAL_ERROR` | system_failure | no |

四类语义分离：**business denial**（安全拒绝，审计为 EXPLICIT_DENIAL）≠ **system failure**
（`AUTHORIZATION_FAILURE` vs `AUTHORIZATION_DENIED` 必须可区分——`D-AUTH-12` fail closed 但审计可辨）
≠ **dependency failure** ≠ **user cancellation**。

---

## 29. Human Approval（§29，继承 `D-AUTH-14`/`D-AUTH-11`）

`AuthorizationDecision = REQUIRES_APPROVAL` ⇒ 状态机进入 `WAITING_APPROVAL`（唯一入口）。
审批载体 persistence 属 Tool Runtime / P10（`D-AUTH-11`），本阶段仅定义状态与转换。
**禁止** `REQUIRES_APPROVAL → auto execute`；审批通过 ⇒ 回 `RUNNING` 并**重新求值**该提案
（不缓存旧决策——`D-AUTH-13` no-cache 精神）；审批拒绝/超时 ⇒ `FAILED`/`CANCELLED`。

---

## 30. Memory Boundary（§30，`D-AUTH-21`）

Memory 实现 = OUT。仅在 `Context` 层保留 **Retrieved** 层的接口位（provider 契约签名），
其授权动作/生命周期 DEFERRED TO AGENT RUNTIME（后续 decision round）。**禁止**本阶段实现任何记忆读写。

---

## 31. Workflow Boundary（§31，`D-AUTH-21`）

Workflow 实现 = OUT。唯一设计约束：未来 Workflow 通过**启动 `AgentRun`**（同一 Request/Run 模型 +
幂等键）编排 Agent，**不得**出现第二套执行引擎。`agent/workflow/interfaces.py` 契约保留。

---

## 32. API Contract（§32，PROPOSED，OQ-AGENT-11）

候选（未冻结）：

```text
POST /agent-runs            （创建 Run；携带 idempotency_key；返回 202 + run_id 或 200 同步结果）
GET  /agent-runs/{id}       （状态/结果；脱敏视图）
POST /agent-runs/{id}/cancel（取消；幂等）
```

全部路由进入必须先过认证/租户解析/`execute` 授权（`D-AUTH-09` 之外，Run 本身也是受控操作）。
**是否采用、路径与形态 ⇒ OQ-AGENT-11**，本阶段不实现。

---

## 33. Synchronous vs Asynchronous（§33，OQ-AGENT-01）

| 维度 | Sync | Async |
|---|---|---|
| 适合 | 短答案/无工具/低风险 | 工具编排/审批/长推理/工作流 |
| 复杂度 | 低（进程内） | 高（worker/状态持久化/恢复） |
| 与冻结的关系 | 两者都必须落在**同一 Run 模型**上（同状态机/预算/审计） | |

**PROPOSED 统一模型**：Run 语义唯一；`Executor` 是可替换抽象（in-process executor / future worker），
API 层按 Run 特征选择 sync/async **呈交方式**，而非两套运行时。最终由 OQ-AGENT-01/06/12 冻结。

---

## 34. Worker Boundary（§34）

禁止实现 Worker。只定义：`Agent Runtime → Execution abstraction（Executor 契约） → Future Worker`。
**禁止** Runtime 绑定 Celery/RabbitMQ/Redis（依赖面见 §37）；worker 选型属未来独立决策（OQ-AGENT-12）。

---

## 35. Database Impact（§35，只读分析 · 全部 PROPOSED）

实测现有面：`agents` / `agent_versions` / `agent_permissions` / `tool_executions`（P09）·
`ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs`（B1-6）·
授权八表（0005/0007）+ 0012 CHECK。**现有 schema 足以支撑解析与授权**。

| 问题 | 分析（PROPOSED） |
|---|---|
| AgentRun 能否初始无状态？ | **能**：sync 短 Run 可仅内存 + 日志/审计事件；状态机契约不依赖持久化 |
| 需要持久 run 状态？ | async/审批场景需要（`WAITING_APPROVAL` 必须可跨进程恢复）⇒ PROPOSED 新表 |
| run history / context storage / approval storage？ | 均指向 `agent_runs` / `agent_run_steps` / `agent_run_contexts` / approval 载体 —— **全部 PROPOSED ONLY**，归属 `agent_runs` 族（OQ-AGENT-02/13），本阶段**零建表** |

**本阶段 migration 数 = 0**（0013+ 不存在，实测）。

---

## 36. Architecture Placement（§36，PROPOSED，延续 `D-AUTH-16` 模式）

```text
core/agent/run/*        = 纯契约与值对象（Run/State/Budget/Error · 无 I/O）
services/agentruntime/* = 编排（解析/上下文/边界/状态机驱动）—— future，经授权后创建
infrastructure/         = persistence/adapter（Gateway adapter · run repository · executor）
apps/api                = 路由（§32）
```

依赖方向：`services → core`；`services → infrastructure`（经契约）；**agent 编排不直接触 DB**
（`Agent → Policy → Tool → Service → Database`，`agent/runtime/interfaces.py` 冻结注释）。
不产生 `core → domains/services` 或 `agent → infrastructure` 倒置（§42）。

---

## 37. Dependency Rules（§37）

```text
Agent Runtime → AI Gateway contract      （经 core 契约；不 import 厂商 SDK）
Agent Runtime → Authorization contract   （services/authorization 经其契约）
Agent Runtime → Tool contract            （agent/tools 契约）
✗ Agent Runtime → OpenAI/Anthropic SDK · PostgreSQL 直连 · Redis · Celery
```

守卫面：`tests/architecture/` 既有断言继续有效（agent↛db/infra/services = 0）；新增
`services/agentruntime` 后须加同向守卫（实施阶段）。

---

## 38. Test Strategy（§38，PROPOSED · 明细见验收矩阵）

九类：Unit（状态机/预算/错误/解析纯逻辑）· Contract（Request/Result/Decision 形状）·
Integration（解析走真库、授权联动、PG 分区感知）· Architecture（依赖方向/无厂商 SDK）·
Security（§27 九威胁）· Failure（§28 全 14 码）· Concurrency（幂等/重复事件）·
Cancellation（§21 五源）· Regression（全量不下降）。重点清单见 §38 原文 13 项全覆盖。

---

## 39. Open Questions（§39 · 15+1 项，全部 PROPOSED / Human Decision Required）

> 已由冻结材料覆盖的**不重复设 OQ**：版本语义（`D-AUTH-19` 已冻结）、授权语义（`D-AUTH-*` 全套）、
> resource_scope（`D-AUTH-23`）、授权缓存（`D-AUTH-13`）、Memory/Workflow 授权（`D-AUTH-21`）、
> delegation lifecycle（`D-AUTH-03`）。

| OQ | 问题 | 候选 | 建议（仅技术后果） |
|---|---|---|---|
| **OQ-AGENT-01** | Sync vs Async 呈交 | A 仅 sync · B 仅 async · C 统一 Run 模型 + 双呈交 | C：避免两套 Runtime（§33） |
| **OQ-AGENT-02** | Run persistence 初始形态 | A 无状态（日志+审计）· B 持久 run 状态 | 与 01 联动；A 最小起步 |
| **OQ-AGENT-03** | Plan-first vs Response-only | A response-only · B plan-first · C 双模式按 agent 声明 | C，但 loop/budget 先行（§23） |
| **OQ-AGENT-04** | Context 架构 | 分层 provider 契约 vs 单一上下文构建器 | 分层（§12），每层独立授权/限额 |
| **OQ-AGENT-05** | 状态机冻结 | §7 转换表采纳/修订 | 采纳；表驱动 + fail-closed |
| **OQ-AGENT-06** | 并发模型 | 单 run 串行 · 步级并行 | 初版串行（预算/审计简单） |
| **OQ-AGENT-07** | Cancellation 模型 | disconnect 即取消 vs 结果留存 | 留存（§21.4） |
| **OQ-AGENT-08** | Run 幂等范围 | run 级 · tool 级 · 双级 | 双级（§22） |
| **OQ-AGENT-09** | Tool-call 上限数值 | max_tool_calls / steps / ai_calls 具体值 | §23 PROPOSED 值起步 |
| **OQ-AGENT-10** | Runtime budget 数值 | §14/§20 缺省值 | PROPOSED 值起步，压测后修订 |
| **OQ-AGENT-11** | API 契约 | §32 三端点采纳/路径 | 采纳三端点形态 |
| **OQ-AGENT-12** | Worker 边界 | executor 抽象形态 · 未来选型（不绑 Celery） | 抽象先行，选型延后 |
| **OQ-AGENT-13** | Run persistence schema | agent_runs 族表设计 | PROPOSED，须独立 Schema Impact |
| **OQ-AGENT-14** | 错误契约 | §28 14 码采纳 | 采纳 + category 四分 |
| **OQ-AGENT-15** | Observability 载体 | 结构化日志先行 · P10 事件 | 日志先行（redaction 基线） |
| **OQ-AGENT-16**（追加） | **AI Gateway 实施顺序** | Runtime 前 / 并行 / 同 slice | 须先裁（§22 硬前置） |

---

## 40. RUNTIME IMPLEMENTATION GATE（§30 必录 · 硬顺序依赖）

> **本节为 HUMAN DECISION RESOLUTION 轮（2026-09-24）确认记录，非新冻结决策。**

```text
AI Gateway Runtime = ABSENT
  （0010 仅 schema：ai_providers / ai_models / ai_routes / ai_policies / ai_request_logs；
   infrastructure/ai/ 不存在；Provider Adapter 代码 = 0 —— 本轮实测）

D-PLAT-09 = HARD SEQUENCING DEPENDENCY（FROZEN，路线 A）
  P10 → P11 → P12 → P13 → Runtime
  P10 = Event/Audit（events → audit_logs 分区父表 + 初始子分区）
  P11 = Triggers / 跨表约束（必须在 seed 前全部就位；D-PLAT-10 G/H/I/J 集中地）
  P12 = Indexes（纯查询索引）
  P13 = Seed / built-in data（首个可登录主体只经 P13，D-PLAT-11）
  来源：STEP1B_SCHEMA_DEPENDENCY.md:171-174 · :193（原文）

Runtime Implementation = BLOCKED until prerequisite phases
```

**门禁（Gate）**：

```text
P10 ready ∧ P11 ready ∧ P12 ready ∧ P13 ready ∧ AI Gateway Runtime ready
        ⇒ Agent Runtime Implementation may open
否则     ⇒ IMPLEMENTATION GATE = CLOSED
```

**允许 vs 禁止**：

```text
Agent Runtime PREP          = ALLOWED（本报告）
Agent Runtime Decision Freeze = ALLOWED
Agent Runtime Implementation  = BLOCKED
```

**配套文档**：[`AGENT_RUNTIME_DECISION_RESOLUTION.md`](./AGENT_RUNTIME_DECISION_RESOLUTION.md)
（16 项 OQ 的逐项决议材料 · `HUMAN DECISION = PENDING` ×16）·
[`AGENT_RUNTIME_ACCEPTANCE_MATRIX.md`](./AGENT_RUNTIME_ACCEPTANCE_MATRIX.md)（82 行实测）。

> **[`D-AGENT-01`…`D-AGENT-16` 注记 · 2026-09-25]** 本节「配套文档」所列的
> `HUMAN DECISION = PENDING` ×16 与「82 行实测」**均已过期**；实际终态为
> **16/16 `FROZEN`**（`AGENT_RUNTIME_DECISION_RESOLUTION.md` §0.1 终态表）·
> **矩阵 116 行**（`AGENT_RUNTIME_ACCEPTANCE_MATRIX.md` §19 脚本实测）。
> 关联：`D-AGENT-01`…`D-AGENT-16`（本文档 §40「配套文档」段与下方「允许 vs 禁止」块）。
> 性质：**状态更新 + 交叉引用**。**不修改本文档既有权衡与结论**（`DECISION FREEZE = ALLOWED`
> 与 `Agent Runtime Implementation = BLOCKED` **依然成立**，后者仍是终态）。

---

## 40A. 与冻结路线的张力（§21/§22 汇总 · REPORT-ONLY）

1. **`D-PLAT-09` 路线 A**：`P10 → P11 → P12 → P13 → Runtime`。本 PREP（设计）不违反；**Runtime
   实施须在 P13（首个可登录主体 seed）之后**——若 Human 希望调整顺序，须走 `D-PLAT-09` 的
   显式 supersession，本阶段不得代裁。
2. **AI Gateway 实现 = 0**：0010 仅有 schema。Agent Runtime 的模型调用面无实现可依赖 ⇒
   OQ-AGENT-16 必须在任何 Runtime Implementation Authorization 之前裁定。
3. **P10 未建**：run/authorization/tool 三类审计的 persistence 均挂 P10（契约先行）。

---

## 41. Exit Criteria（§41）

✓ Baseline verified ✓ Authorization 契约继承面明确 ✓ P09 protected（含 resource_scope opaque）✓
Agent/Run 生命周期建模 ✓ Context 边界与预算 ✓ Tool 提案边界 ✓ 失败/超时/取消/幂等/环路 ✓
安全九威胁 ✓ 架构放置与依赖 ✓ API 选项 ✓ Sync/Async ✓ Worker 边界 ✓ DB 影响（0 migration）✓
测试矩阵 ✓ OQ 16 项 ✓ **零实现**

---

## 42. HARD STOP 触发面（§42 · 本轮实测未触发）

`Agent→DB/Infrastructure/arbitrary Python` · `LLM→direct execution` · `resource_scope 被解释` ·
`授权旁路` · `跨租户 context` · `新 migration/DDL/DML` —— 本轮**零命中**（纯文档轮；
仅新增本报告与验收矩阵两份文档）。

---

## 43. FINAL（§43）

```text
PREP = PASSED
DECISION READINESS = READY（取决于 Human 对 OQ-AGENT-01..16 的裁定）
IMPLEMENTATION = NOT AUTHORIZED
MIGRATION      = NOT AUTHORIZED
COMMIT / TAG / PUSH = NOT AUTHORIZED
```

---

---

## 44. 后续注记（**append-only** · 遵 `PLATFORM_DECISION_LOG.md` Charter §5.2 格式）

> **[`D-AGENT-01`…`D-AGENT-16` 注记 · 2026-09-25]** STAGE 3 Decision Freeze 完成：16 项 OQ 全部冻结；
> 本 PREP 的全部 PROPOSED 内容据此进入契约层。
> 关联：本文档 §15（Plan Model）· §21.4（disconnect）· §25（Observability）· §28（错误契约）·
> §32（API）· §33（Sync/Async）· §34（Worker）· §35（DB 影响）· §39（OQ 表）· §40（IMPLEMENTATION GATE）。
> 性质：**状态更新 + 交叉引用**。**不修改本文档既有段落、表格行或任何结论。**

**状态更新对照**：

| 项 | 本文档原状（2026-09-24） | **2026-09-25 终态** | 冻结条目 |
|---|---|---|---|
| §39 16 项 OQ | `HUMAN DECISION = PENDING`（`PROPOSED`） | **16 / 16 `FROZEN`** | `D-AGENT-01`…`D-AGENT-16` |
| §15 Plan Model | A/B 两候选均留作 OQ | **Hybrid**（Informational ⇒ Response First；Action ⇒ Structured Plan） | `D-AGENT-03` |
| §33 Sync / Async | PROPOSED 统一模型 | **Unified Run Model + Sync Fast Path + Async Long Path** | `D-AGENT-01` |
| §21.4 disconnect | PROPOSED（待 OQ-AGENT-07） | **`disconnect ≠ cancel`**；`cancel ≠ rollback` | `D-AGENT-07` |
| §32 API 三端点 | PROPOSED | **202 + Polling**；**Streaming = DEFERRED** | `D-AGENT-11` |
| §34 Worker | 禁止实现 | **Execution Abstraction Only**（禁绑 Celery/Redis/RabbitMQ） | `D-AGENT-12` |
| §35 DB 影响 | `agent_runs` 族 **PROPOSED ONLY** | **`agent_runs` + `agent_run_steps`** —— **仍为 DESIGN，本轮 0 migration** | `D-AGENT-13` |
| §28 错误契约 | 码表 + 4 类目语义（PROPOSED） | **8 outer categories + 14 canonical codes** | `D-AGENT-14` |
| §25 Observability | PROPOSED 字段集 | **Structured Logs First + Future Event/Audit Surface** | `D-AGENT-15` |
| §14/§20/§23 预算 | PROPOSED 数值 | 多维预算冻结；**hard cost limit = DEFERRED** | `D-AGENT-10` |
| §23 Tool 上限 | PROPOSED 数值（单一层） | **Global + Agent + Tenant**（Strictest Limit Wins） | `D-AGENT-09` |
| §40 实施门 | `IMPLEMENTATION = BLOCKED` | **不变**（`D-PLAT-09` **未 supersede**） | `D-AGENT-16` |
| §43 FINAL | `IMPLEMENTATION = NOT AUTHORIZED` | **不变**；`COMMIT / TAG / PUSH = NOT AUTHORIZED` | — |

**注记新增的契约层内容（来源 = Human Decision 正文，非本 PREP 的追认）**：

```text
① 资源版本 / 条件更新并发控制  —— D-AGENT-06 补强规则
   （本 PREP §22 仅论幂等；Human 明确"仅有 idempotency 不足以解决所有 race condition"）
② 限额缺失层的【继承】规则     —— D-AGENT-09
   （本 PREP §23 仅给建议数值；Human 明确"缺失层不得解释为无限制，必须继承上层"）
```

**新增配套文档**：`AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`（`DESIGN FROZEN` / `NOT IMPLEMENTED`）。

**END OF AGENT RUNTIME PREP REPORT（2026-09-24）**
**后续注记追加：STAGE 3 Decision Freeze（`D-AGENT-01`…`D-AGENT-16` 全部 `FROZEN`），2026-09-25**
**后续注记追加：`O-1` 错误码枚举算术裁定（`APPROVED`），2026-09-25**

> **[`O-1` 注记 · 2026-09-25]** `O-1` 已由 Human Decision 裁定 `APPROVED`：
> **`AI_TIMEOUT` 合并归入 `AI_PROVIDER_FAILURE`，不作为独立 canonical error code**
> ⇒ canonical error codes **恰为 14**。
> 关联：本文档 §28（错误契约 PROPOSED）· §44 上表「§28 错误契约」行对
> `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` §O-1 的引用（该处标注的 `REPORT-ONLY，非新决策` **已由本次裁定取代**）。
> 性质：**状态更新 + 交叉引用**。**不修改本文档既有段落与结论。**

**裁定要点（与本文档 §28 的关系）**：

| 项 | 本文档 §28（2026-09-24 · PROPOSED） | **2026-09-25 裁定终态** |
|---|---|---|
| 错误类目 | 4 类语义（business / system / dependency / user_cancelled） | **8 outer categories**（`D-AGENT-14`） |
| canonical 码数 | 码表（`AI_TIMEOUT` 曾为候选） | **恰为 14**；`AI_TIMEOUT` ⊂ `AI_PROVIDER_FAILURE` |
| `TIMEOUT` 语义 | `RUNTIME_TIMEOUT` 为运行时超时 | **`TIMEOUT` = Run / Runtime 整体执行期限**超时；**Provider 层 timeout 归 `AI_PROVIDER_FAILURE`** |
| `BUDGET_EXCEEDED` | 归 `INVALID_REQUEST` 族（§14） | **保持独立 canonical code**；**禁止**并入 `TIMEOUT` |
| 四对不可合并 | §28 已分离 4 类语义 | **逐条不变**（DENIED≠FAILURE · USER_CANCELLED≠TIMEOUT · AI_PROVIDER_FAILURE≠INVALID_MODEL_OUTPUT · TOOL_ERROR≠RUNTIME_ERROR） |

**同步面（仅此）**：`PLATFORM_DECISION_LOG.md`（`D-AGENT-14` 契约级留项行 + 附录 **F.8**）·
`AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`（§I.1 / §I.2 / §I.3 / §O）·
`AGENT_RUNTIME_ACCEPTANCE_MATRIX.md`（§11 + `FAIL-05` · §16 · §18 · 汇总）· 本注记。

**未触碰**：`migration` / `DDL` / `DML` / runtime code / tests / configuration ·
`agent_runs` / `agent_run_steps`（**未创建**）· **Runtime Implementation Gate 未解除** · 无 `commit` / `tag` / `push`。
