# AGENT RUNTIME — DECISION RESOLUTION PACKAGE（STAGE 3）

> **状态声明（先读）**
>
> ```text
> 本文档 = DECISION RESOLUTION PACKAGE
> 本文档 = DECISION FREEZE APPLIED（2026-09-25）
> ```
>
> **更新（2026-09-25）**：Human 通过 `UAP STAGE 3 — AGENT RUNTIME HUMAN DECISION FREEZE
> AUTHORIZATION` 逐项裁定 —— **16 项 OQ 全部 `FROZEN`，0 项未决**。
> 本文件已据此同步：`HUMAN DECISION` 由 `PENDING` 更新为**选定选项**，
> `STATUS` 由 `PROPOSED` 更新为 `FROZEN`（**16 / 16**）。
> **冻结正文写入 `PLATFORM_DECISION_LOG.md` 的 `D-AGENT-01`…`D-AGENT-16` —— 该处为唯一权威。**
>
> **历史记录（2026-09-24 原状，保留不改）**：本文件初次产出时，Human 指令逐项写明
> **"Human Decision Required"**，并规定 **"不得把 Recommended Direction 写成 Frozen"**，
> 故当时 16 项 `HUMAN DECISION = PENDING` / `STATUS = PROPOSED`，
> **未写入** `PLATFORM_DECISION_LOG.md`、**未冻结任何决策**、**未修改任何实现或 migration**。
>
> ⚠ **阅读约定**：本文件 §2–§17 中 `Current Evidence` / `Option A·B·C` / `Impact` /
> `Recommended Direction` 均为**当时的过程分析材料**（保留原貌，不改写）；其**结论**一律以
> `PLATFORM_DECISION_LOG.md` 的 `D-AGENT-*` 与下表 `选定` 列**为准**。
>
> **已由指令直接确定（非 OQ、非选项）的约束**（2026-09-24 轮）与冻结条文的映射：
> ① `D-PLAT-09` **不 supersede** + Runtime Implementation Gate ⇒ **`D-AGENT-16`**；
> ② Worker 禁止 ⇒ **`D-AGENT-12`**；③ Gateway 边界必须冻结 ⇒ **`D-AGENT-16`**；
> ④ 不可信上下文 / 输出安全流程 ⇒ **`D-AGENT-04`** + **`D-AGENT-03`**；
> ⑤ 版本不可变性 ⇒ 继承 `D-AUTH-19`（本组**重申不重定义**）。

---

## 0.1 OQ 状态总表

| OQ | 主题 | HUMAN DECISION | 选定（冻结） | 冻结条目 | STATUS |
|---|---|---|---|---|---|
| OQ-AGENT-01 | Sync vs Async | **FROZEN** | **C** Unified Run Model + Sync Fast Path + Async Long Path | `D-AGENT-01` | `FROZEN` |
| OQ-AGENT-02 | Run persistence | **FROZEN** | **B** Persistent Run State | `D-AGENT-02` | `FROZEN` |
| OQ-AGENT-03 | Plan model | **FROZEN** | **C** Hybrid（Response First / Structured Plan） | `D-AGENT-03` | `FROZEN` |
| OQ-AGENT-04 | Context architecture | **FROZEN** | **C** Provider Contracts + Immutable Snapshot + Lazy Retrieval | `D-AGENT-04` | `FROZEN` |
| OQ-AGENT-05 | Run state machine | **FROZEN** | **A** Eight-State Model（table-driven） | `D-AGENT-05` | `FROZEN` |
| OQ-AGENT-06 | Concurrency | **FROZEN** | **B** Run-level 并发 + Action-level 幂等（+ 资源版本控制） | `D-AGENT-06` | `FROZEN` |
| OQ-AGENT-07 | Cancellation | **FROZEN** | **A** disconnect ≠ automatic cancellation | `D-AGENT-07` | `FROZEN` |
| OQ-AGENT-08 | Idempotency | **FROZEN** | **B** Dual-level（Run + Tool Action） | `D-AGENT-08` | `FROZEN` |
| OQ-AGENT-09 | Tool limits | **FROZEN** | **C** Global + Agent + Tenant（Strictest Limit Wins） | `D-AGENT-09` | `FROZEN` |
| OQ-AGENT-10 | Runtime budget | **FROZEN** | **B** Multi-dimensional（hard cost limit **DEFERRED**） | `D-AGENT-10` | `FROZEN` |
| OQ-AGENT-11 | API contract | **FROZEN** | **B** 202 + Polling（streaming **DEFERRED**） | `D-AGENT-11` | `FROZEN` |
| OQ-AGENT-12 | Worker boundary | **FROZEN** | **B** Execution Abstraction Only | `D-AGENT-12` | `FROZEN` |
| OQ-AGENT-13 | Run persistence schema | **FROZEN** | **B** `agent_runs` + `agent_run_steps` | `D-AGENT-13` | `FROZEN` |
| OQ-AGENT-14 | Error contract | **FROZEN** | **B** 8 outer categories + 14 canonical codes | `D-AGENT-14` | `FROZEN` |
| OQ-AGENT-15 | Observability | **FROZEN** | **C** Structured Logs First + Future Event/Audit Surface | `D-AGENT-15` | `FROZEN` |
| OQ-AGENT-16 | AI Gateway dependency | **FROZEN** | **A + C**（契约可冻结 / 实施 BLOCKED） | `D-AGENT-16` | `FROZEN` |

> **统计（2026-09-25 终态）**：`FROZEN` **16** / `PENDING` **0** / `DEFERRED` **0**（条目级） /
> `SUPERSEDED` **0** / unresolved OQ **0**。
> **DEFERRED 子域 2**（已冻结决策内的明确子域，**非** OQ、**非**未决项）：
> ① `Streaming`（归 `D-AGENT-11`）· ② `AI Gateway Hard Cost Limit`（归 `D-AGENT-10`，条件 = Gateway Runtime ready）。

---

## 1. 已由本轮指令确定的约束（非 OQ）

| ID | 内容 | 来源 | 性质 |
|---|---|---|---|
| **GC-1** | `D-PLAT-09` **本轮不 supersede**；转化为 **Runtime Implementation Gate**：`P10 ready ∧ P11 ready ∧ P12 ready ∧ P13 ready ∧ AI Gateway Runtime ready` ⇒ 方可开启 Runtime 实施；否则 `IMPLEMENTATION GATE = CLOSED` | 指令 §1/§18 | 硬约束（已确定） |
| **GC-2** | `Agent Runtime → AI Gateway Contract → Gateway Runtime → Provider Adapter`；**禁止** Runtime 直接依赖 OpenAI/Anthropic/Gemini SDK | 指令 §19 | 硬约束（与 `D-AUTH-09` 同向） |
| **GC-3** | Worker 实施 = **FORBIDDEN**；仅定义 Execution abstraction；**禁止**绑定 Celery/Redis/RabbitMQ | 指令 §13 | 硬约束（已确定） |
| **GC-4** | `User Input / External Document / Tool Result / Memory / Retrieved Content` 均为 **Potentially Untrusted Context**；**禁止** `retrieved content → system instruction` 升级 | 指令 §21 | 硬约束（安全不变式） |
| **GC-5** | LLM 输出（text/JSON/tool proposal/plan）**均非** trusted execution command；必须 `Parse → Schema → Authorization → Policy → Approval → Tool` | 指令 §22 | 硬约束（与 PREP §16/§18 一致） |
| **GC-6** | Published version **immutable**；Run 必须绑定 `agent_id + version_revision`，Agent 后续升级**不得**改变历史 Run 的解释 | 指令 §26 | 硬约束（`D-AUTH-19` + P09 trigger 同向） |
| **GC-7** | 本轮不创建 migration/DDL/DML/代码 | 指令 §1/§34 | 硬约束 |

---

## 2. OQ-AGENT-01 — Sync vs Async

| 字段 | 内容 |
|---|---|
| **Question** | Run 的呈交模型采用何种形态？ |
| **Current Evidence** | Run 语义已统一（PREP §33）；API 端点仅 PROPOSED；`D-AUTH-11/14` 引入 `WAITING_APPROVAL`（异步本质）；`D-AUTH-13` 禁缓存 |
| **Option A** | **Sync-first**：仅进程内同步执行；实现最简 |
| **Option B** | **Async-first**：全部经队列/worker；一致性最强 |
| **Option C** | **Unified Run Model + sync fast-path + async long-path**（同一状态机/预算/审计，呈交方式不同） |
| **Engineering Impact** | A：短路径快，但审批/长任务无法承载，未来必然返工；B：早期即需 worker 与 run 持久化（撞 GC-1/GC-3）；C：需 Executor 抽象，复杂度中等但唯一可演进 |
| **Security Impact** | A：取消/审批窗口窄，风险面小；B/C：需保证异步路径不绕过授权与审批（同 `D-AUTH-09`） |
| **Migration Impact** | A：0；B/C：需 run 持久化（OQ-AGENT-02/13） |
| **Future Runtime Impact** | A 会在引入审批时**必然重写**；C 保住单一 Run 语义 |
| **Recommended Direction** | **Option C**（技术适配性：唯一不产生第二套 Runtime 的选项） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**C** — Unified Run Model + Sync Fast Path + Async Long Path（同一 Run / 同一状态机 / 同一授权模型 / 同一审计模型） → `D-AGENT-01`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 3. OQ-AGENT-02 — Run Persistence

| 字段 | 内容 |
|---|---|
| **Question** | AgentRun 初始形态：无状态 vs 持久？ |
| **Current Evidence** | `events`/`audit_logs` 不存在（P10）；`WAITING_APPROVAL` 必须可跨进程恢复；disconnect 留存策略（OQ-AGENT-07）依赖持久态 |
| **Option A** | **Stateless**：内存 + 结构化日志；最小起步 |
| **Option B** | **Persistent Run state**：run 状态入库，可 resume/reconnect |
| **Option C** | 混合：sync 无状态 / async 持久 |
| **Engineering Impact** | A：重试/恢复/审批不可实现；B：需新表（本轮 NOT AUTHORIZED）；C：两套路径 = 双语义风险 |
| **Security Impact** | A：状态不可恢复 ⇒ 失败即丢弃（安全但能力受限）；B：持久态需 tenant 隔离与脱敏审计 |
| **Migration Impact** | A：0；B/C：需 migration（**当前未授权**） |
| **Future Runtime Impact** | 决定 async 能否成立 |
| **Recommended Direction** | **Option B**（技术适配性：resume/approval/reconnect 均需之）；**但 `new table = NOT AUTHORIZED`** |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — Persistent Run State（`AgentRun` = 一等持久化运行对象） → `D-AGENT-02`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 4. OQ-AGENT-03 — Plan Model

| 字段 | 内容 |
|---|---|
| **Question** | Response-first / Plan-first / Hybrid？ |
| **Current Evidence** | `agent_versions.output_schema` 与 `allowed_tools` 已存在，两种模式均可承载；`max_risk_level` 为风险闸门 |
| **Option A** | **Response-first**：单次调用直接产出答复 |
| **Option B** | **Plan-first**：先产出结构化 action proposal 序列 |
| **Option C** | **Hybrid**：简单问答走 response-first；动作请求走结构化 plan/action proposal |
| **Engineering Impact** | A：无法承载动作类需求；B：简单问答也付 plan 成本 + 引入循环风险；C：需意图判别（可复用模型自身输出，风险点明确） |
| **Security Impact** | 三者共同不变式：**LLM output ≠ execution authorization**（GC-5）；B/C 提案面更大 ⇒ 逐项授权压力更高 |
| **Migration Impact** | 全 0（复用 `definition/allowed_tools`） |
| **Future Runtime Impact** | 决定工具编排能力上限 |
| **Recommended Direction** | **Option C**（技术适配性：能力与成本平衡；判别失败时降级为 response-first 并记审计） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**C** — Hybrid（Informational ⇒ Response First；Action/Tool/Multi-step ⇒ Structured Plan；**LLM Plan ≠ Execution Authority**） → `D-AGENT-03`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 5. OQ-AGENT-04 — Context Architecture

| 字段 | 内容 |
|---|---|
| **Question** | Context 层的实现形态：provider-based / pipeline-based / immutable snapshot / lazy retrieval？ |
| **Current Evidence** | PREP §12 已定八层（System/Tenant/Space/User/Agent/Task/Retrieved/Tool）；每层须 authorized+bounded+traceable；`resources.classification` 提供敏感度闸门 |
| **Option A** | **Provider-based**：每层一个 provider 契约，可独立替换/授权/限额 |
| **Option B** | **Pipeline-based**：单一构建器内部顺序拼装 |
| **Option C** | **Immutable snapshot + lazy retrieval**：装配后冻结快照；Retrieved 层惰性拉取 |
| **Engineering Impact** | A：可测性与审计最强，接口数量多；B：实现快，但层间边界易侵蚀；C：A + 快照不可变性，最适合审计与复现 |
| **Security Impact** | A/C：每层独立授权与敏感度过滤（防越权聚合）；B：单点过滤易漏层 |
| **Migration Impact** | 0（本阶段） |
| **Future Runtime Impact** | 决定 Memory 接入方式（`D-AUTH-21` deferred） |
| **Recommended Direction** | **Option C**（= A 的 provider 契约 + 不可变快照 + Retrieved 惰性；兼顾审计与 Memory 未来接入） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**C** — Provider Contracts + Immutable Context Snapshot + Lazy Retrieval（八层：System/Tenant/Space/User/Agent/Task/Retrieved/Tool） → `D-AGENT-04`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 6. OQ-AGENT-05 — Run State Machine

| 字段 | 内容 |
|---|---|
| **Question** | 状态集合与 transition matrix 是否采纳 PREP §7？ |
| **Current Evidence** | PREP §7 已给出 8 状态与转换表；`D-AUTH-14` 固定 `REQUIRES_APPROVAL ⇒ WAITING_APPROVAL` 唯一入口 |
| **Option A** | **采纳 PREP §7 原表**（8 状态 + 表驱动 + 非法转换 fail-closed） |
| **Option B** | 精简（合并 `WAITING`/`WAITING_APPROVAL`） |
| **Option C** | 扩展（增加 `PAUSED`/`RETRYING` 等） |
| **Engineering Impact** | A：语义清晰、可穷举测试；B：审批与等待语义混淆（审批≠等待输入），违反 `D-AUTH-14` 区分；C：状态爆炸，转换矩阵不可穷举验证 |
| **Security Impact** | B 会把"等人类输入"与"等审批"混为一谈 ⇒ 审批边界模糊（不可接受） |
| **Migration Impact** | 0（状态为契约对象，非 DB 枚举） |
| **Future Runtime Impact** | 状态机是审计与恢复的锚点 |
| **Recommended Direction** | **Option A**（采纳 PREP §7；转换矩阵详见 PREP §7，实施期加穷举测试） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**A** — Eight-State Model（CREATED/RUNNING/WAITING/WAITING_APPROVAL/COMPLETED/FAILED/CANCELLED/TIMEOUT；table-driven + fail closed） → `D-AGENT-05`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 7. OQ-AGENT-06 — Concurrency

| 字段 | 内容 |
|---|---|
| **Question** | 同一 Run / 同一 Agent / 同一 Resource 的并发语义？ |
| **Current Evidence** | 状态机假定单 Run 串行；工具副作用不可撤销（OQ-AGENT-07 §25）；`uq_agent_perm` 等 DB 约束提供资源级唯一性 |
| **Option A** | **全串行**：同 Run 单步、同 Agent 单 Run |
| **Option B** | **Run 级并发 + Action 级幂等** |
| **Option C** | **步级并行**（同 Run 内并行工具调用） |
| **Engineering Impact** | A：最简单，但吞吐受限；B：吞吐与安全平衡；C：与预算/审计/部分失败冲突最重 |
| **Security Impact** | C 引入同 Run 内竞态（同一资源并发写），审核困难；B 以幂等键收敛副作用 |
| **Migration Impact** | 0（除幂等记录随 OQ-AGENT-02） |
| **Future Runtime Impact** | 决定 worker 并发模型（OQ-AGENT-12） |
| **Recommended Direction** | **Option B**（Run-level 并发允许，Action-level 幂等强制）；**初版可退化为 A** 作为实现起点 |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — Run-level concurrency allowed + Action-level idempotency enforced（**补强**：真实资源冲突风险的动作必须使用资源版本 / 条件更新或等价并发控制） → `D-AGENT-06`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 8. OQ-AGENT-07 — Cancellation

| 字段 | 内容 |
|---|---|
| **Question** | 取消的传播/清理/终态，以及 **client disconnect 是否自动取消 Run**？ |
| **Current Evidence** | PREP §21 已给五源统一取消 + 检查点式协作取消 + disconnect 默认留结果；§25（本轮）要求区分"取消请求"与"副作用已回滚" |
| **Option A** | **采纳 PREP §21**：五源统一；`CLIENT_DISCONNECT ≠ 自动取消`（async 模式 Run 继续至终态，结果留存） |
| **Option B** | disconnect **即**取消（尽早释放资源） |
| **Option C** | 按 Run 类型（sync 取消 / async 留存） |
| **Engineering Impact** | A：async 语义一致、结果可回收；B：客户端抖动即杀 Run（对长任务不友好）；C：双语义（与 OQ-AGENT-01 的"统一模型"张力） |
| **Security Impact** | A：已启动的副作用不被"取消"掩盖（必须显式记 orphaned execution）；B：易把 cancel 误当 rollback（指令 §25 明令禁止的误读） |
| **Migration Impact** | 0 |
| **Future Runtime Impact** | 决定 disconnect 语义与恢复策略 |
| **Recommended Direction** | **Option A**（保持 PREP 推荐；并强制记录 cancel-ack 与 side-effect 完成状态分离） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**A** — 保持 disconnect ≠ automatic cancellation（取消来源：Explicit User Cancel / Timeout / Admin-System Cancel / Shutdown；Cancel Request ≠ Side Effect Rolled Back） → `D-AGENT-07`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 9. OQ-AGENT-08 — Idempotency

| 字段 | 内容 |
|---|---|
| **Question** | 幂等键的 key/scope/TTL/collision/replay 语义？ |
| **Current Evidence** | PREP §22 已给 run 级 + tool 级双层；`tool_executions` 表存在（可作为执行事实来源，但**本轮不读写语义未冻结**） |
| **Option A** | **仅 Run 级幂等** |
| **Option B** | **Run 级 + Tool 级**（非幂等工具必须有键） |
| **Option C** | 仅 Tool 级 |
| **Engineering Impact** | A：整 Run 重放安全，但 Run 内工具重试仍可能重复副作用；B：覆盖"network retry + worker retry = 无重复真实动作"；C：Run 级重放仍会重复 |
| **Security Impact** | 重复副作用 = 资金/外部系统类最高危；B 为唯一覆盖全路径者 |
| **Migration Impact** | 幂等记录载体随 OQ-AGENT-02（本轮 0） |
| **Future Runtime Impact** | 决定 tool retry 与 runtime retry 是否安全（§24 依赖项） |
| **Recommended Direction** | **Option B**（双层）；TTL/collision 规则建议：`(tenant_id, idempotency_key)` 命名空间，重复即返回首次结果，冲突键拒绝 |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — Dual-level Idempotency（Run + Tool Action；必须定义 Key / Scope / TTL / Collision / Replay / Result Reuse） → `D-AGENT-08`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 10. OQ-AGENT-09 — Tool Limits

| 字段 | 内容 |
|---|---|
| **Question** | `max_tool_calls` / `max_runtime_steps` / `max_ai_calls` / `max_duration` 的取值与覆盖层级？ |
| **Current Evidence** | PREP §23 建议 10/25/8 + 时长=Run 预算；`agents.max_risk_level` 与 `agent_versions.allowed_tools` 提供了 per-agent 覆盖的合法载体 |
| **Option A** | **全局默认值**（单一常量） |
| **Option B** | 全局默认 + **agent 级覆盖**（`version.definition` 内声明） |
| **Option C** | 全局 + agent + **tenant 上限**（三层取最严） |
| **Engineering Impact** | A：简单但无法适配不同 agent；B：覆盖够用；C：最强治理，需 tenant 级配置面（`tenants.settings` 已存在） |
| **Security Impact** | **关键不变式：所有上限不得被 LLM 自行提高**（指令 §10）；C 提供最严护栏 |
| **Migration Impact** | B 可复用 `definition jsonb`（0 迁移）；C 复用 `tenants.settings`（0 迁移） |
| **Future Runtime Impact** | 与循环防护（LOOP）直接耦合 |
| **Recommended Direction** | **Option C**（三层取最严，全部复用既有 jsonb 载体 ⇒ 0 schema 变更）；数值待压测后冻结 |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**C** — Global + Agent + Tenant（Strictest Limit Wins；缺失层**必须继承**上层，不得解释为无限制） → `D-AGENT-09`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 11. OQ-AGENT-10 — Runtime Budget

| 字段 | 内容 |
|---|---|
| **Question** | 统一预算维度（time/tokens/cost/tool calls/steps）与层级（Run → AI → Tool）？ |
| **Current Evidence** | PREP §14/§20/§23/§24 已给维度与"只减不增"；成本权威在 Gateway（`ai_request_logs`） |
| **Option A** | **仅时间预算** |
| **Option B** | **多维预算（time+tokens+tool_calls+steps）+ `child ≤ parent remaining`** |
| **Option C** | B + 独立 cost 上限（由 Gateway 回读累计） |
| **Engineering Impact** | A：不足以防"多步小额"耗尽；B：覆盖主要滥用面；C：需 Gateway 可用（OQ-AGENT-16 依赖） |
| **Security Impact** | 预算 = DoS/滥用护栏；无预算 ⇒ 模型可自循环烧资源 |
| **Migration Impact** | 0 |
| **Future Runtime Impact** | 与 OQ-AGENT-09 数值冻结成对 |
| **Recommended Direction** | **Option B 先行**（不依赖 Gateway 实现），C 待 Gateway Runtime ready 后追加（技术后果：避免与 OQ-AGENT-16 串联阻塞） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — Multi-dimensional Runtime Budget（Time/Tokens/AI Calls/Tool Calls/Steps；`Child ≤ Parent Remaining`；Cost Tracking 允许，**Hard Cost Limit = DEFERRED**） → `D-AGENT-10`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 12. OQ-AGENT-11 — API Contract

| 字段 | 内容 |
|---|---|
| **Question** | 三端点 + 呈交形式的采用？ |
| **Current Evidence** | `apps/api/routes/health.py` 为当前唯一路由先例；PREP §32 三端点为 PROPOSED；`D-PLAT-08/14` 已确立 API 契约风格（fail-closed + 明确状态码） |
| **Option A** | 三端点 + **同步响应** |
| **Option B** | 三端点 + **async（202 + 轮询 GET）** |
| **Option C** | 三端点 + **async + 流式（SSE/WebSocket）** |
| **Engineering Impact** | A：最简单；B：贴合 async 语义；C：体验最好但引入长连接/背压/取消复杂度 |
| **Security Impact** | 流式引入长连接鉴权续期与数据泄漏面（SSE 日志化风险）；B 最保守 |
| **Migration Impact** | 0 |
| **Future Runtime Impact** | 决定客户端契约与 OQ-AGENT-01 的落地形态 |
| **Recommended Direction** | **Option B 先行**（202 + `GET /agent-runs/{id}` 轮询），**C 作为后续独立决策**（不与之捆绑） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — 202 + Polling（`POST/GET/POST cancel` 三端点；Fast Path 可为完成结果但**不得**第二套 execution model；**Streaming = DEFERRED**） → `D-AGENT-11`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 13. OQ-AGENT-12 — Worker Boundary

| 字段 | 内容 |
|---|---|
| **Question** | Execution abstraction 的形态与 worker 归属阶段？ |
| **Current Evidence** | GC-3（本轮已定）：worker 实施 FORBIDDEN，仅定义抽象；指令 §13 允许"P12/P13 或 Runtime implementation phase 决定具体实现" |
| **Option A** | **进程内 Executor**（唯一实现，无 worker） |
| **Option B** | **Executor 契约 + 未来 worker 实现**（本阶段只定义契约） |
| **Option C** | 直接选定队列技术（Celery/RQ/…） |
| **Engineering Impact** | A：无法承载 async；B：与 OQ-AGENT-01 Option C 对齐；C：**违反 GC-3**（不可选） |
| **Security Impact** | worker 引入跨进程执行 ⇒ 授权与审计必须在 worker 侧重验（不得信任入队时决策） |
| **Migration Impact** | 0（本阶段） |
| **Future Runtime Impact** | 决定部署形态（`D-PLAT` 部署模型未涉 worker） |
| **Recommended Direction** | **Option B**（契约先行 + 实现延后；**C 因 GC-3 被排除**） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — Execution Abstraction Only（当前**禁止**绑定 Celery/Redis Queue/RabbitMQ 及其他具体 worker framework） → `D-AGENT-12`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 14. OQ-AGENT-13 — Run Persistence Schema

| 字段 | 内容 |
|---|---|
| **Question** | 进程重启后必须存活的对象与表设计？ |
| **Current Evidence** | 需存活候选：run 状态（审批/恢复）、步记录（审计/复现）、事件（P10 承接）；P09/B1-6 表中**无** run 载体 |
| **Option A** | `agent_runs` 单表（状态 + 最小元数据） |
| **Option B** | `agent_runs` + `agent_run_steps` |
| **Option C** | A/B + `agent_run_events`（与 P10 `events` 的关系需裁定） |
| **Engineering Impact** | A：恢复可行、复现不足；B：可复现步骤；C：与 P10 outbox 语义可能重叠 ⇒ 需划界 |
| **Security Impact** | run 载荷可能含敏感 prompt/结果 ⇒ 脱敏与访问控制必须与 `D-AUTH` 一致；**不得**把 `resource_scope` 语义引入（`D-AUTH-23`） |
| **Migration Impact** | **需要 migration（当前 NOT AUTHORIZED）**；且按 `D-PLAT-09` 须排在 P10–P13 之后 |
| **Future Runtime Impact** | 是 resume/approval/audit 三者的共同前置 |
| **Recommended Direction** | **Option B 起步**（`agent_runs` + `agent_run_steps`），`agent_run_events` 与 P10 的边界**单列**（见 §18 记录） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — `agent_runs` + `agent_run_steps`（`events`/`audit_logs` 归 P10 **保持独立**；**不得**把 Audit Event 与 Run Step 混成一表；不设立 `agent_run_events`） → `D-AGENT-13`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 15. OQ-AGENT-14 — Error Contract

| 字段 | 内容 |
|---|---|
| **Question** | 错误分类与码表采纳？（8 类目 × 码表） |
| **Current Evidence** | PREP §28 已给 14 码 + 4 类目；`D-AUTH-12` 要求 fail-closed 且**可区分**显式拒绝与系统故障 |
| **Option A** | 采纳 PREP §28（14 码 + 4 类目） |
| **Option B** | 8 类目细分（指令 §15 列出的 8 类） |
| **Option C** | 仅 code，不分类目 |
| **Engineering Impact** | A：已覆盖；B：更贴合指令命名，需把 14 码映射到 8 类目；C：客户端无法按语义处理（重试/告警混淆） |
| **Security Impact** | `AUTHORIZATION_DENIED ≠ AUTHORIZATION_FAILURE`、`USER_CANCELLED ≠ TIMEOUT` 必须正交（指令 §15 明令）；C 会混淆审计与告警 |
| **Migration Impact** | 0 |
| **Future Runtime Impact** | 决定可观测性与告警策略 |
| **Recommended Direction** | **Option B**（8 类目为外层 + 14 码为内层，二者正交映射；= 指令 §15 命名与 PREP §28 码表的合并） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**B** — 8 outer categories + 14 canonical error codes（必须区分 DENIED≠FAILURE / USER_CANCELLED≠TIMEOUT / AI_PROVIDER_FAILURE≠INVALID_MODEL_OUTPUT / TOOL_ERROR≠RUNTIME_ERROR；mapping deterministic） → `D-AGENT-14`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 16. OQ-AGENT-15 — Observability

| 字段 | 内容 |
|---|---|
| **Question** | 观测字段与载体（日志 / P10 事件）？ |
| **Current Evidence** | `infrastructure/logging/redaction.py` + `structured.py` 为既有脱敏基线；`ai_request_logs`（0010 分区表）承接 AI 侧；P10 未建 |
| **Option A** | 结构化日志先行（redaction 基线） |
| **Option B** | 全部走 P10 事件（等 P10） |
| **Option C** | A + P10 落地后补齐事件面 |
| **Engineering Impact** | A：立即可用；B：被 P10 阻塞（撞 GC-1）；C：分阶段、不阻塞 |
| **Security Impact** | 敏感输入**默认不落原始日志**（指令 §16）；日志载体必须在设计上强制脱敏字段白名单 |
| **Migration Impact** | 0（A/C 的日志面） |
| **Future Runtime Impact** | 决定 trace 贯通（run/authorization/tool 三审计以 run_id 关联） |
| **Recommended Direction** | **Option C**（字段集：run_id/request_id/trace_id/tenant/space/actor/agent/version/model/state/latency/cost/tools/error） |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**C** — Structured Logs First + Future Event/Audit Surface（默认 No raw sensitive prompt / No secret / No unrestricted tool payload；**不得**提前创建 P10 persistence） → `D-AGENT-15`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 17. OQ-AGENT-16 — AI Gateway Dependency

| 字段 | 内容 |
|---|---|
| **Question** | Agent Runtime 与尚未实现的 AI Gateway Runtime 的关系？ |
| **Current Evidence** | **实测：0010 五表（`ai_providers`/`ai_models`/`ai_routes`/`ai_policies`/`ai_request_logs`）存在；`infrastructure/ai/` 不存在；Provider Adapter 代码 = 0** |
| **Option A** | Runtime **contract 可先冻结**，runtime implementation 等 Gateway Runtime ready |
| **Option B** | Runtime **自带** Provider abstraction（绕过 Gateway） |
| **Option C** | Runtime 只能依赖已完成的 Gateway Runtime ⇒ **当前只能设计不能实现** |
| **Engineering Impact** | A：设计不被阻塞、实施被阻塞；B：**违反 GC-2**；C：与 A 的实施面等价，但表述更严（设计/实现分离） |
| **Security Impact** | B 会重建一套厂商接入面（密钥、日志脱敏、成本记账全部二次实现）⇒ 与 `D-PLAT` 的 Provider Adapter 铁律冲突 |
| **Migration Impact** | 0（本阶段） |
| **Future Runtime Impact** | **A+C 组合下**：`Runtime Contract → Gateway Contract → future Gateway Runtime → Provider`；Runtime 永不触 SDK |
| **Recommended Direction** | **A + C**（与指令 §17 推荐一致）：契约先冻结 + 实施以 Gateway Runtime ready 为门 |
| **Human Decision** | **FROZEN**（2026-09-25）—— 选定：**A + C** — `Runtime → Gateway Contract → Gateway Runtime → Provider Adapter`（**MUST NOT** 直依赖厂商 SDK；Contract 可冻结、**Implementation BLOCKED**） → `D-AGENT-16`（`PLATFORM_DECISION_LOG.md` 为唯一权威） |
| **Status** | `FROZEN` |

---

## 18. §27 DATABASE IMPACT — Proposed Classification（本轮 0 migration）

| 对象 | 分类 | 依据 |
|---|---|---|
| `agent_runs` | **REQUIRED**（若 OQ-AGENT-02 选 B/C） | 审批恢复、resume、async 的硬前提 |
| `agent_run_steps` | **REQUIRED**（同上） | 步骤级复现与审计 |
| `agent_run_events` | **DEFERRED**（待与 P10 `events` 划界） | 与 outbox 语义可能重叠，需单列裁定 |
| `agent_contexts`（上下文快照持久化） | **OPTIONAL** | 复现能力增强；亦可只存摘要 |
| approval 载体 | **DEFERRED → Tool Runtime / P10** | `D-AUTH-11` 已冻结归属 |
| 幂等记录 | **REQUIRED**（随 OQ-AGENT-08 Option B） | 防重复副作用 |
| `ai_request_logs`（既有） | **NOT NEEDED（复用）** | 已存在（0010），成本权威 |
| `tool_executions`（既有） | **NOT NEEDED（复用）** | 执行事实已有载体 |

**本阶段 migration 数 = 0**（实测 `0013+ = 0`）。

---

## 19. §28 P10 / P11 / P12 / P13 依赖图（**取自仓库冻结材料，非推测**）

来源：`STEP1B_SCHEMA_DEPENDENCY.md:171-174`（P10 起为表驱动阶段定义）+ `:193`（seed 纪律）。

| 阶段 | 冻结职责（原文） | 对 Runtime 的依赖关系 |
|---|---|---|
| **P10** | Event / Audit：`events` → `audit_logs`（分区父表 + 初始子分区） | **三类审计的 persistence 载体**；`D-AUTH-15` 授权审计、run 审计、tool 执行审计的落库前提 |
| **P11** | Triggers / 跨表约束（`STEP1B_TRIGGER_INVENTORY.md`）；**必须在 seed 前全部就位** | **G/H/I/J 集中地**（`D-PLAT-10`）；跨表不变量在 Runtime 写入前必须已就位 |
| **P12** | Indexes：非 PK 索引（`STEP1B_INDEX_STRATEGY.md`）；P12 只保留"纯查询索引" | run 查询性能面（实施后可评估补索引） |
| **P13** | Seed / built-in data（`STEP1B_SEED_STRATEGY.md`） | **首个可登录主体只经 P13**（`D-PLAT-11`）⇒ Runtime 的端到端联调前提 |
| **Runtime** | Agent 执行（本 PREP 设计对象） | 排在 P13 之后（`D-PLAT-09` 路线 A） |

> **纪律（原文 `:193`）**：`P00-P10 均无 seed 需求；P13 才有 seed。所有 trigger（P11）必须先于 P13 seed。`
> **无 OPEN QUESTION**：P10–P13 职责在仓库冻结材料中定义充分，**不需要**新的 OQ。

**Runtime Implementation Gate（由 GC-1 转化）**：

```text
P10 ready ∧ P11 ready ∧ P12 ready ∧ P13 ready ∧ AI Gateway Runtime ready
        ⇒ Agent Runtime Implementation may open
否则     ⇒ IMPLEMENTATION GATE = CLOSED
```

---

## 20. 冻结请求包 —— **已执行（2026-09-25）**

原请求项（保留原貌）：若认可 §2–§17 的 Recommended Direction
（**C / B / C / C / A / B / A / B / C / B / B / B / B / B / C / A+C**，按 OQ-AGENT-01..16 顺序），
**一次确认即可完成 16 项冻结**。

```text
2026-09-25 —— Human 已逐项明确批准（`UAP STAGE 3 — AGENT RUNTIME HUMAN DECISION FREEZE AUTHORIZATION`）。
选定序列与 Recommended Direction【逐项一致】。
```

**已执行的动作**（对照原计划）：

| 原计划动作 | 结果 |
|---|---|
| 写 `PLATFORM_DECISION_LOG.md`（`D-AGENT-01..16`，状态 `FROZEN`） | ✅ **已写入 16 条 `FROZEN`**（另新增 Charter §7 · 附录 F） |
| 同步 `ARCHITECTURE.md` / `DEPENDENCY_RULES.md` | ✅ **已完成** |
| 同步 `AGENT_RUNTIME_PREP_REPORT.md` | ✅ **append-only 注记（不改写既有结论）** |
| 同步 `AGENT_RUNTIME_ACCEPTANCE_MATRIX.md` | ✅ **已完成（含 16/16 traceability）** |
| 建立 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` | ✅ **已建立（DESIGN FROZEN / NOT IMPLEMENTED）** |
| 同步 `docs/api/README.md` · `docs/security/README.md` | ✅ **已完成（含 3 处 STAGE 2 遗留缺陷修正）** |
| `DECISION FREEZE = PASSED` | ✅ **PASSED**（10 项 Gate 全 PASS，见 Gate 报告） |

> **不变**：`COMMIT` / `TAG` / `PUSH` / `MIGRATION` / `DDL` / `DML` / `IMPLEMENTATION` = **NOT AUTHORIZED**。

---

## 21. ¶32 EXIT CHECK（2026-09-25 更新）

| 条件 | 2026-09-24 实测 | **2026-09-25 终态** |
|---|---|---|
| 16/16 OQ individually resolved | ❌ 0/16 | ✅ **16/16**（`HUMAN DECISION = FROZEN` × 16） |
| or explicitly DEFERRED | ❌ 0 项 | ✅ **DEFERRED 子域 2**（streaming · Gateway hard cost limit，属已冻结条文的明确子域） |
| No silent decision | ✅ 无静默决定 | ✅ **无静默决定**（16 项均逐条显式批准；过程材料与冻结条文分别留档） |
| Decision Log ↔ Architecture ↔ Contract ↔ Acceptance 一致 | ⚠ 未执行 | ✅ **已执行**（见 Gate 报告 10 项 PASS） |
| `D-PLAT-09` 未被 supersede | ✅ | ✅ **FROZEN / NOT SUPERSEDED**（转化为 Runtime Implementation Gate） |
| AI Gateway / D-PLAT-09 / implementation blocked 已记录 | ✅ | ✅ **已记录**（`D-AGENT-16` + 本 PREP §40 + Contract §G） |

⇒ **`DECISION FREEZE = PASSED`**（2026-09-25）
⇒ **`IMPLEMENTATION = BLOCKED`**（Runtime Implementation Gate = CLOSED；`D-PLAT-09` 未变）

---

**END OF AGENT RUNTIME DECISION RESOLUTION（2026-09-24）**
**END OF AGENT RUNTIME DECISION RESOLUTION（`DECISION FREEZE APPLIED` · `HUMAN DECISION` 16/16 `FROZEN`；冻结正文见 `PLATFORM_DECISION_LOG.md` 的 `D-AGENT-01`…`D-AGENT-16`，2026-09-25）**
