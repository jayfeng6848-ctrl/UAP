# AGENT RUNTIME — ACCEPTANCE MATRIX（STAGE 3 · DECISION FREEZE APPLIED）

> **条目性质**：`FROZEN-DESIGN` = 契约已冻结（`D-AGENT-*`）、**实现未开始**；
> 本矩阵**不构成实现验收结论**。

> **状态（2026-09-25 更新）**：`OQ-AGENT-01`…`OQ-AGENT-16` 已**全部冻结**为
> `D-AGENT-01`…`D-AGENT-16`（见 `PLATFORM_DECISION_LOG.md`）。
> 本矩阵的状态词表同步升级（**语义映射 1:1**）：
>
> | 旧（2026-09-24） | 新（2026-09-25） | 含义 |
> |---|---|---|
> | `PENDING` | **`FROZEN-DESIGN`** | **决策已冻结**；实施待 Runtime Implementation Gate 开放（契约见 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`） |
> | `BLOCKED-OQ` | **`BLOCKED-GATE`** | 明确被 **Runtime Implementation Gate** 阻塞（P10 ∧ P11 ∧ P12 ∧ P13 ∧ AI Gateway Runtime） |
> | `**ASSET**` | **`**ASSET**`** | 既有冻结资产，无需新实现（未变） |
> | `**PASSED**` | **`**PASSED**`** | 本轮（文档轮）实测通过（未变） |
>
> **数字为脚本实测**（按 ID 前缀分组、逐行主状态计数），非估算。
> **本矩阵仍不构成实现验收结论** —— 所有 `FROZEN-DESIGN` 行的验收须待实施阶段执行。
> **实施门 = CLOSED**（`D-AGENT-16` + `D-PLAT-09`）。

## 0. ID 前缀映射

| 前缀 | 类别 | 前缀 | 类别 |
|---|---|---|---|
| `BASE-` | 基线与保护 | `FAIL-` | 失败模型（§28） |
| `AUTH-` | 授权继承面 | `TIME-` | 超时与预算 |
| `AGENT-` | Agent/Version 解析 | `CANCEL-` | 取消 |
| `RUN-` | Run 模型与状态机 | `IDEM-` | 幂等 |
| `CTX-` | Context 边界/预算 | `LOOP-` | 环路防护 |
| `AI-` | Gateway 关系/决策类型 | `SEC-` | 安全（§27） |
| `TOOL-` | Tool 提案边界 | `OBS-` | 观测/审计/成本 |
| `API-` | API / Sync-Async / Worker | `ARCH-` | 架构放置与依赖 |
| `MIG-` | DB 影响 | `REG-` | 测试与回归 |
| `STATE-` | 状态机（§29 STATE） | `RETRY-` | 重试层级（§29 RETRY） |
| `WORKER-` | 执行抽象（§29 WORKER） | `DATABASE-` | DB 影响细化（§29 DATABASE） |
| `DEPENDENCY-` | 依赖与阶段门（§29 DEPENDENCY） | — | — |

> **§29 类别名 ↔ 本矩阵前缀**：CONTEXT↔`CTX-` · AUTHORIZATION↔`AUTH-` · SECURITY↔`SEC-` ·
> OBSERVABILITY↔`OBS-` · TIMEOUT↔`TIME-` · DATABASE↔`MIG-`+`DATABASE-` · DEPENDENCY↔`ARCH-`+`DEPENDENCY-` ·
> STATE/RETRY/WORKER 为本轮新增前缀（见 §17）· **CONCURRENCY↔`CONCUR-`（2026-09-25 依 `D-AGENT-06` 新增，见 §12A）**。
>
> **17 个要求类别全覆盖核对**（指令 §21）：STATE · CONTEXT · AUTHORIZATION · AI · TOOL · TIMEOUT ·
> RETRY · CANCEL · IDEMPOTENCY · **CONCURRENCY** · LOOP · SECURITY · API · WORKER · OBSERVABILITY ·
> DATABASE · DEPENDENCY ⇒ **17 / 17**（前缀映射见 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` §N.1）。

## 1. BASE — 基线与保护

| ID | 要求 | 证据 | 判定方法 | 状态 |
|---|---|---|---|---|
| BASE-01 | HEAD = `034ee97…` · tag `UAP-V0.1.8-AUTHORIZATION` 在位 | git | 命令 | **ASSET** |
| BASE-02 | alembic 单头 0012 · 0013+ absent | 迁移目录 | 命令 | **ASSET** |
| BASE-03 | 0010/0011 sha256 = 保护值 | sha256sum | 命令 | **ASSET** |
| BASE-04 | 本阶段 0 migration / 0 DDL / 0 DML | git | diff 审计 | **PASSED** |
| BASE-05 | 工作树仅新增 2 份 PREP 文档 | git status | 命令 | **PASSED** |

## 2. AUTH — 授权继承面（冻结，Runtime 不得另造）

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| AUTH-01 | Run 内一切访问经 `AuthorizationService`；无第二套判定 | `D-AUTH-01/09` | **ASSET** |
| AUTH-02 | Subject=AGENT 独立授权；delegator 不扩权 | `D-AUTH-02/03` | **ASSET** |
| AUTH-03 | DENY>ALLOW · DEFAULT DENY · FAIL CLOSED | `D-AUTH-07/12` | **ASSET** |
| AUTH-04 | `REQUIRES_APPROVAL` ⇒ `WAITING_APPROVAL`，绝不 auto-execute | `D-AUTH-14` | **ASSET** |
| AUTH-05 | 无授权缓存（cache 归 Tool Runtime） | `D-AUTH-13` | **ASSET** |
| AUTH-06 | `resource_scope` opaque：0 消费路径 | `D-AUTH-23` | **ASSET** |
| AUTH-07 | 三审计分离（run / authorization / tool execution） | `D-AUTH-15` | **FROZEN-DESIGN** |

## 3. AGENT — 解析（§8/§9）

| ID | 要求 | 验证方法 | 状态 |
|---|---|---|---|
| AGENT-01 | 解析序：存在→状态→授权；四类失败全 DENY 型错误码 | unit+integration | `FROZEN-DESIGN` |
| AGENT-02 | draft/disabled/archived 均不可执行 | `AGENT_NOT_ACTIVE` 注入 | `FROZEN-DESIGN` |
| AGENT-03 | 跨租户 agent 解析不可达（uq_agents_key per tenant） | 注入测试 | `FROZEN-DESIGN` |
| AGENT-04 | 版本：无 pin ⇒ current_version_id；NULL ⇒ `VERSION_NOT_FOUND` | unit | `FROZEN-DESIGN` |
| AGENT-05 | 仅 `published` 可执行；pinned draft/deprecated/revoked 拒绝 | unit | `FROZEN-DESIGN` |
| AGENT-06 | 运行期版本只读（trigger + 契约只读）；checksum 入观测 | 契约审计 | `FROZEN-DESIGN` |
| AGENT-07 | revision = 单调整数（`D-AUTH-19`），display 串不混入 | 契约审计 | **ASSET** |

## 4. RUN — Run 模型与状态机（§6/§7）

| ID | 要求 | 验证方法 | 状态 |
|---|---|---|---|
| RUN-01 | 6 个契约对象成形（Request/Context/State/Result/Error/Budget） | contract test | `FROZEN-DESIGN` |
| RUN-02 | 状态机表驱动；穷举合法转换 | property/unit | `FROZEN-DESIGN` |
| RUN-03 | 非法转换 ⇒ `InvalidTransition`（fail closed） | unit | `FROZEN-DESIGN` |
| RUN-04 | 终态不可再转换 | unit | `FROZEN-DESIGN` |
| RUN-05 | `WAITING_APPROVAL` 仅由 `REQUIRES_APPROVAL` 进入 | unit | `FROZEN-DESIGN` |
| RUN-06 | 审批通过 ⇒ 回 RUNNING 并**重新求值**（不缓存旧决策） | unit | `FROZEN-DESIGN` |
| RUN-07 | Budget 只减不增；重试不重置预算 | unit | `FROZEN-DESIGN` |
| RUN-08 | 既有 `AgentRuntime.run()` 兼容门面为 EXTEND 非 REPLACE | 契约审计 | `FROZEN-DESIGN` |
| RUN-09 | Run 绑定 `agent_id + version_revision`；**后续升级不得改变历史 Run 的解释** | `D-AUTH-19` · `D-AGENT-02` | `FROZEN-DESIGN` |

## 5. CTX — Context（§12–§14）

| ID | 要求 | 状态 |
|---|---|---|
| CTX-01 | 八层分层装配；每层独立 provider 契约（签名+授权+限额） | `FROZEN-DESIGN` |
| CTX-02 | 禁止整库/任意查询注入 prompt | `FROZEN-DESIGN` |
| CTX-03 | 进入 Gateway 前：Authorization + Data Boundary + Sensitivity + Budget | `FROZEN-DESIGN` |
| CTX-04 | 跨租户内容**结构性不可达**（查询层谓词，非提示词约束） | `FROZEN-DESIGN` |
| CTX-05 | 过滤失败 ⇒ 剔除该层；授权失败 ⇒ 不可用（区分，fail closed） | `FROZEN-DESIGN` |
| CTX-06 | 超限策略序：drop → truncate → summarize → 拒绝；无无限扩容 | `FROZEN-DESIGN` |
| CTX-07 | Retrieved 层仅为接口位（Memory 不实现，`D-AUTH-21`） | `FROZEN-DESIGN` |
| CTX-08 | **Snapshot 不可变**；Lazy Retrieval 结果**必须重过** authorization / policy / boundary | `D-AGENT-04` | `FROZEN-DESIGN` |

## 6. AI — Gateway 关系与决策类型（§5/§15/§16）

| ID | 要求 | 状态 |
|---|---|---|
| AI-01 | Runtime → Gateway contract；永不 import 厂商 SDK | `FROZEN-DESIGN` |
| AI-02 | 模型路由权威 = `ai_routes`（agents.default_route_id）；Runtime 不自选模型 | `FROZEN-DESIGN` |
| AI-03 | usage/cost 权威 = Gateway（`ai_request_logs`）；Runtime 只透传 run_id | `FROZEN-DESIGN` |
| AI-04 | 输出六类决策；无法解析 ⇒ `INVALID_MODEL_OUTPUT` | `FROZEN-DESIGN` |
| AI-05 | LLM output ≠ execution authorization（每步皆为 proposal） | `FROZEN-DESIGN` |
| AI-06 | **AI Gateway Runtime = ABSENT ⇒ Runtime 实施被门禁阻塞**（`D-AGENT-16` 已冻结：契约可冻结 / 实施 BLOCKED） | **BLOCKED-GATE** |
| AI-07 | Runtime **不得**自建第二套 provider 抽象（只经 Gateway 契约） | `D-AGENT-16` | `FROZEN-DESIGN` |

## 7. TOOL — 提案边界（§17）

| ID | 要求 | 状态 |
|---|---|---|
| TOOL-01 | 提案 → schema 校验 → Authorization → Policy → Approval → Tool | `FROZEN-DESIGN` |
| TOOL-02 | 工具集 = allowed_tools ∩ 授权 ∩ policy（上限∩下限取交） | `FROZEN-DESIGN` |
| TOOL-03 | 未经 ALLOW 的提案不得触 ToolRuntime（fail closed） | `FROZEN-DESIGN` |
| TOOL-04 | 语义越权提案不重试，记安全审计 | `FROZEN-DESIGN` |

## 8. API / EXEC — API、Sync-Async、Worker（§32–§34）

| ID | 要求 | 状态 |
|---|---|---|
| API-01 | 三端点形态仅 PROPOSED（OQ-AGENT-11）；路由前先认证/授权 | `FROZEN-DESIGN` |
| API-02 | 统一 Run 模型，双呈交；禁止两套 Runtime | `FROZEN-DESIGN` |
| API-03 | Executor 为可替换抽象；Runtime 不绑定 Celery/RabbitMQ/Redis | `FROZEN-DESIGN` |
| API-04 | Workflow 只能经启动 AgentRun 编排（无第二引擎，`D-AUTH-21`） | `FROZEN-DESIGN` |
| API-05 | Fast Path 可为完成结果，但**不得创建第二套 execution model** | `D-AGENT-11` | `FROZEN-DESIGN` |

## 9. MIG — DB 影响（§35）

| ID | 要求 | 状态 |
|---|---|---|
| MIG-01 | 本阶段 migration = 0；agent_runs 族全部 PROPOSED ONLY | **PASSED** |
| MIG-02 | 现有 schema（P09+B1-6+授权）足以支撑解析与授权 | **ASSET** |
| MIG-03 | run 状态持久化需求与 OQ-AGENT-02/13 联动 | `FROZEN-DESIGN` |

## 10. ARCH — 架构与依赖（§36/§37）

| ID | 要求 | 状态 |
|---|---|---|
| ARCH-01 | core=契约 / services=编排 / infrastructure=适配（同 `D-AUTH-16` 模式） | `FROZEN-DESIGN` |
| ARCH-02 | agent↛DB · agent↛infrastructure · core↛services（守卫延续） | **ASSET** |
| ARCH-03 | 无厂商 SDK 依赖（守卫断言） | `FROZEN-DESIGN` |
| ARCH-04 | `D-PLAT-09` 路线 A：Runtime **实施**须在 P13 之后（本 PREP 不违路线） | **ASSET**（张力已登记） |

## 11. FAIL — 失败模型（§28 · `D-AGENT-14`）

> **`O-1` 已裁定（RESOLVED / APPROVED · 2026-09-25）**：`AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE`（不设独立码）
> ⇒ canonical error codes **恰为 14**；**`BUDGET_EXCEEDED` 保持独立**（禁止并入 `TIMEOUT`）。
> 契约见 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` §I.2 / §O-1；裁定登记见 `PLATFORM_DECISION_LOG.md` 附录 F.8。

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| FAIL-01 | **14 canonical error codes** + **8 outer categories**（`D-AGENT-14`） | `D-AGENT-14` | `FROZEN-DESIGN` |
| FAIL-02 | `AUTHORIZATION_DENIED` ≠ `AUTHORIZATION_FAILURE`（业务拒绝 vs 系统故障可辨） | `D-AGENT-14` | `FROZEN-DESIGN` |
| FAIL-03 | 全部错误码有注入测试 | `D-AGENT-14` | `FROZEN-DESIGN` |
| FAIL-04 | Error mapping **deterministic**；**禁止**用异常字符串判断业务类型 | `D-AGENT-14` | `FROZEN-DESIGN` |
| FAIL-05 | canonical 集合**恰为 14**：`AI_TIMEOUT` **不作为**独立码（⊂ `AI_PROVIDER_FAILURE`）；`BUDGET_EXCEEDED` **不得**并入 `TIMEOUT`；另两对（`USER_CANCELLED` ≠ `TIMEOUT` · `TOOL_ERROR` ≠ `RUNTIME_ERROR`）保持可区分 | `O-1` · `D-AGENT-14` | `FROZEN-DESIGN` |

## 12. TIME / CANCEL / IDEM / LOOP（§19–§23）

| ID | 要求 | 状态 |
|---|---|---|
| TIME-01 | 五层超时 + Run 总预算钳制（累加不越界） | `FROZEN-DESIGN` |
| TIME-02 | 三类 Retry 分离；不可重试清单 | `FROZEN-DESIGN` |
| TIME-03 | Cost Tracking **允许**（透传/可观测）；**Hard Cost Limit = DEFERRED**（不得伪造） | `D-AGENT-10` | `FROZEN-DESIGN` |
| CANCEL-01 | 五源统一取消事件；检查点式协作取消 | `FROZEN-DESIGN` |
| CANCEL-02 | 不可中止工具调用 ⇒ orphaned execution + 强制审计 | `FROZEN-DESIGN` |
| IDEM-01 | run 级幂等键；重复请求返回首次结果 | `FROZEN-DESIGN` |
| IDEM-02 | 非幂等工具遇重试场景必须先有幂等键，否则拒绝 | `FROZEN-DESIGN` |
| IDEM-03 | 必须定义 `Key` / `Scope` / `TTL` / `Collision` / `Replay` / `Result Reuse` 六项 | `D-AGENT-08` | `FROZEN-DESIGN` |
| LOOP-01 | max_tool_calls/steps/ai_calls/duration 预算 | `FROZEN-DESIGN` |
| LOOP-02 | 签名环检测 ⇒ `loop_detected`（非 retryable） | `FROZEN-DESIGN` |
| LOOP-03 | 三层限额 **Strictest Limit Wins**；**缺失层必须继承上层**，不得解释为"无限制" | `D-AGENT-09` | `FROZEN-DESIGN` |

## 12A. CONCUR — 并发（`D-AGENT-06`）

> 依指令 §21 的 **CONCURRENCY** 类别新增（2026-09-25）。与 `IDEM-` 行**不重复**：
> `IDEM-` 管"重复投递"，`CONCUR-` 管"并发写同一资源"。

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| CONCUR-01 | **Run 级并发允许**：`Agent A Run 1` 与 `Agent A Run 2` 可并发存在 | `D-AGENT-06` | `FROZEN-DESIGN` |
| CONCUR-02 | **Action 级幂等强制**；步级并行 = **未授权**（同 Run 内不并行工具调用） | `D-AGENT-06` | `FROZEN-DESIGN` |
| CONCUR-03 | 真实资源冲突风险的 Tool Action **必须**使用资源版本 / 条件更新 / 等价并发控制 | `D-AGENT-06` 补强规则 | `FROZEN-DESIGN` |
| CONCUR-04 | `same resource + same mutation` **不得**因并发产生不可控重复或覆盖（含 lost update） | `D-AGENT-06` | `FROZEN-DESIGN` |

## 13. SEC — 安全（§27 · 九威胁）

| ID | 威胁 | 防御位（PROPOSED） | 状态 |
|---|---|---|---|
| SEC-01 | Prompt Injection | 层物理分离；system 不可被 input 覆盖 | `FROZEN-DESIGN` |
| SEC-02 | Indirect Injection | retrieved/tool 结果 = data 层，永不入指令层 | `FROZEN-DESIGN` |
| SEC-03 | Tool Injection | allowed ∩ 授权 ∩ policy，逐项授权 | `FROZEN-DESIGN` |
| SEC-04 | Context Leakage | 层隔离 + sensitivity filter | `FROZEN-DESIGN` |
| SEC-05 | Cross-Tenant Leakage | 查询层 tenant 谓词（结构性） | `FROZEN-DESIGN` |
| SEC-06 | Privilege Escalation | Subject=AGENT；delegator 不扩权；resource_scope 不参与 | `FROZEN-DESIGN` |
| SEC-07 | Agent Impersonation | tenant 绑定校验 + 授权 | `FROZEN-DESIGN` |
| SEC-08 | Unauthorized Tool Call | 提案未经 ALLOW 不触执行 | `FROZEN-DESIGN` |
| SEC-09 | LLM confidence 当安全决策 | **禁止**——判定只来自 AuthorizationService/Policy | `FROZEN-DESIGN` |

## 14. OBS — 观测 / 审计 / 成本（§24–§26）

| ID | 要求 | 状态 |
|---|---|---|
| OBS-01 | run 观测字段 13 项（含 checksum/route/budget） | `FROZEN-DESIGN` |
| OBS-02 | 敏感输入输出不入普通日志（redaction 基线） | `FROZEN-DESIGN` |
| OBS-03 | 三审计分离；persistence → P10（契约先行） | `FROZEN-DESIGN` |
| OBS-04 | Runtime 不计成本，只透传关联键 | `FROZEN-DESIGN` |

## 15. REG — 测试与回归（§38）

| ID | 要求 | 状态 |
|---|---|---|
| REG-01 | 九类测试齐备（unit/contract/integration/architecture/security/failure/concurrency/cancellation/regression） | `FROZEN-DESIGN` |
| REG-02 | §38 13 项重点全覆盖（解析/版本/边界/授权/AI 失败/提案/审批/取消/超时/重试/幂等/环路/租户隔离） | `FROZEN-DESIGN` |
| REG-03 | 全量回归不下降（基线 542 passed） | `FROZEN-DESIGN` |

## 16. OQ ↔ Matrix 映射（§39 · 16 项）

| OQ | 决策域 | 主要验收行 |
|---|---|---|
| 01 Sync/Async | 呈交 | API-02 · RUN-01 |
| 02 Run persistence | 持久化 | MIG-03 · RUN-01 |
| 03 Plan vs Response | 编排 | AI-05 · TOOL-01 · LOOP-01 |
| 04 Context 架构 | 上下文 | CTX-01..03 |
| 05 状态机 | 生命周期 | RUN-02..06 |
| 06 并发 | 执行 | RUN-07 · IDEM-01 |
| 07 取消 | 生命周期 | CANCEL-01..02 |
| 08 幂等范围 | 可靠性 | IDEM-01..02 |
| 09 Tool 上限 | 预算 | LOOP-01 |
| 10 Budget 数值 | 预算 | TIME-01 · CTX-06 |
| 11 API 契约 | 接口 | API-01 |
| 12 Worker | 执行 | API-03 |
| 13 Persistence schema | 持久化 | MIG-03 |
| 14 错误契约 | 可靠性 | FAIL-01..05 |
| 15 Observability | 观测 | OBS-01..04 |
| 16 **AI Gateway 顺序** | **前置依赖** | **AI-06** |

## 17. §29 类别补充行（STATE / RETRY / WORKER / DATABASE / DEPENDENCY）

> 本组为使矩阵显式覆盖指令 §29 要求的全部分类；与既有行**不重复**（既有行归 API/RUN/ARCH/MIG 等）。

| ID | 要求 | 依据 | 状态 |
|---|---|---|---|
| STATE-01 | 8 状态齐备（CREATED/RUNNING/WAITING/WAITING_APPROVAL/COMPLETED/FAILED/CANCELLED/TIMEOUT） | PREP §7 | `FROZEN-DESIGN` |
| STATE-02 | 完整 transition matrix：`state × event → next_state` **可穷举** | OQ-AGENT-05 | `FROZEN-DESIGN` |
| STATE-03 | 非法 transition ⇒ **DENY/拒绝，不得静默跳转** | 指令 §6 | `FROZEN-DESIGN` |
| STATE-04 | 终态不可再转换；`WAITING_APPROVAL` 唯一入口 = `REQUIRES_APPROVAL` | `D-AUTH-14` | `FROZEN-DESIGN` |
| STATE-05 | `WAITING`（等输入，无授权含义）与 `WAITING_APPROVAL`（等审批）**必须分离** | `D-AGENT-05` | `FROZEN-DESIGN` |
| RETRY-01 | AI Retry 独立（仅依赖类错误，指数退避，上限 2） | PREP §19 | `FROZEN-DESIGN` |
| RETRY-02 | Tool Retry 仅限 `retryable=true` 且**幂等**工具 | PREP §19/§22 | `FROZEN-DESIGN` |
| RETRY-03 | Runtime Retry **不得重复已完成的 Tool 动作**（依赖 Tool 幂等） | 指令 §24 | `FROZEN-DESIGN` |
| RETRY-04 | 三类重试均计入预算；重试**不重置**预算 | PREP §19 | `FROZEN-DESIGN` |
| WORKER-01 | 仅定义 Execution abstraction（Executor 契约），无 worker 实现 | GC-3 / OQ-AGENT-12 | `FROZEN-DESIGN` |
| WORKER-02 | **禁止**绑定 Celery / Redis / RabbitMQ | GC-3 | `FROZEN-DESIGN` |
| WORKER-03 | worker 侧必须**重验授权与审批**（不信任入队时决策） | `D-AUTH-09/12` | `FROZEN-DESIGN` |
| DATABASE-01 | 本轮 migration = 0 · 不生成 DDL/DML | 指令 §27 | **PASSED** |
| DATABASE-02 | `agent_runs` / `agent_run_steps` = **REQUIRED**（条件**已满足**：`D-AGENT-02` 选 **B** ⇒ 持久 Run 状态） | §27 分类 · `D-AGENT-02/13` | `FROZEN-DESIGN` |
| DATABASE-03 | `agent_run_events` **不设立** —— `D-AGENT-13` 已划界：**Run Step 归 `agent_run_steps`，审计事件归 P10 `events`/`audit_logs`** | §27 分类 · `D-AGENT-13` | `FROZEN-DESIGN` |
| DATABASE-04 | 复用既有 `ai_request_logs` / `tool_executions`，**不重复建**载体 | §27 分类 | **ASSET** |
| DATABASE-05 | run 载荷密钥/敏感面须脱敏 + tenant 隔离；**不得**引入 `resource_scope` 语义 | `D-AUTH-23` | `FROZEN-DESIGN` |
| DEPENDENCY-01 | `Runtime → Gateway contract → Authorization contract → Tool contract` | GC-2 | `FROZEN-DESIGN` |
| DEPENDENCY-02 | **禁止** Runtime → OpenAI/Anthropic/Gemini SDK；禁 DB 直连 / Redis / Celery | GC-2 | **ASSET** |
| DEPENDENCY-03 | `D-PLAT-09` 硬顺序门：`P10∧P11∧P12∧P13∧Gateway ready` ⇒ 方可实施 | GC-1 | **ASSET**（门禁已录入 PREP §40） |
| DEPENDENCY-04 | `Agent Runtime Contract → AI Gateway Contract → future Gateway Runtime → Provider` | OQ-AGENT-16 A+C | `FROZEN-DESIGN` |
| DEPENDENCY-05 | **AI Gateway Runtime = ABSENT** ⇒ Runtime **实施**被门禁阻塞（设计不受阻） | 实测 | **BLOCKED-GATE** |

## 18. TRACEABILITY — Decision → Contract → Test → Acceptance（**16 / 16**）

> 指令 §21 要求：**16/16 OQ 必须有 traceability**。下表为**唯一**映射权威；
> 冻结条目见 `PLATFORM_DECISION_LOG.md`，契约见 `AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`。

| # | Decision（`D-AGENT-NN`） | Contract 节 | 测试类别 | 主要验收行 | Acceptance 判据 |
|---|---|---|---|---|---|
| 01 | `D-AGENT-01` Sync/Async | §B · §C · §K | `API` · `RUN` | API-02 · API-05 · RUN-01 | 单一 Run 模型双呈交；无第二套 execution model |
| 02 | `D-AGENT-02` Run Persistence | §C · §L | `DATABASE` · `MIG` | DATABASE-02 · DATABASE-05 · MIG-03 | Run 状态可跨进程恢复（设计）；本轮零建表 |
| 03 | `D-AGENT-03` Plan Model | §F | `AI` · `TOOL` · `LOOP` | AI-05 · TOOL-01 · LOOP-01 | Hybrid 双路；`LLM Plan ≠ Execution Authority` |
| 04 | `D-AGENT-04` Context | §E | `CTX` · `SEC` | CTX-01..08 · SEC-02/04/05 | 八层各 authorized/bounded/traceable；快照不可变 |
| 05 | `D-AGENT-05` State Machine | §D | `STATE` · `RUN` | RUN-02..06 · STATE-01..05 | 8 态穷举表驱动；非法转换 fail closed |
| 06 | `D-AGENT-06` Concurrency | §H.1 | `CONCUR` · `IDEM` | CONCUR-01..04 · IDEM-01 | Run 级并发 + 资源版本控制；无 lost update |
| 07 | `D-AGENT-07` Cancellation | §D · §K | `CANCEL` · `API` | CANCEL-01/02 · API-03 | disconnect ≠ cancel；cancel ≠ rollback |
| 08 | `D-AGENT-08` Idempotency | §H.2 | `IDEM` | IDEM-01..03 | 双层幂等；六项定义齐备；无重复真实操作 |
| 09 | `D-AGENT-09` Tool Limits | §J.1 | `LOOP` | LOOP-01 · LOOP-03 | 三层取最严；缺失层继承上层 |
| 10 | `D-AGENT-10` Budget | §J.2 | `TIME` · `CTX` | TIME-01 · TIME-03 · CTX-06 | 五维预算；`child ≤ parent`；硬成本上限 DEFERRED |
| 11 | `D-AGENT-11` API Contract | §K | `API` | API-01 · API-05 | 三端点 + 202 轮询；streaming DEFERRED |
| 12 | `D-AGENT-12` Worker Boundary | §M | `WORKER` | WORKER-01..03 | 仅执行抽象；无队列框架绑定 |
| 13 | `D-AGENT-13` Persistence Schema | §L | `DATABASE` · `MIG` | DATABASE-02/03/05 · MIG-03 | `agent_runs` + `agent_run_steps`；与 P10 分离 |
| 14 | `D-AGENT-14` Error Contract | §I | `FAIL` | FAIL-01..05 | 8 类目 + **14 码**（`O-1` 已裁定：`AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE`）；四对区分；映射 deterministic |
| 15 | `D-AGENT-15` Observability | §J · §L | `OBS` | OBS-01..04 | 字段可关联；默认不落敏感原文；P10 面延后 |
| 16 | `D-AGENT-16` AI Gateway Dependency | §A · §G · §M · §P | `AI` · `DEPENDENCY` | AI-01/06/07 · DEPENDENCY-01..05 | 无厂商 SDK；契约冻结 / 实施 BLOCKED |

**追溯完备性（脚本核对）**：`D-AGENT` 冻结条目 **16** · 本表行 **16** · 覆盖矩阵前缀 **21 / 21**。

## 19. 汇总（**脚本实测** · 2026-09-25）

| 分类 | 行数 | `ASSET` | `PASSED` | `FROZEN-DESIGN` | `BLOCKED-GATE` |
|---|---|---|---|---|---|
| BASE | 5 | 3 | 2 | 0 | 0 |
| AUTH | 7 | 6 | 0 | 1 | 0 |
| AGENT | 7 | 1 | 0 | 6 | 0 |
| RUN | 9 | 0 | 0 | 9 | 0 |
| CTX | 8 | 0 | 0 | 8 | 0 |
| AI | 7 | 0 | 0 | 6 | 1 |
| TOOL | 4 | 0 | 0 | 4 | 0 |
| API | 5 | 0 | 0 | 5 | 0 |
| MIG | 3 | 1 | 1 | 1 | 0 |
| ARCH | 4 | 2 | 0 | 2 | 0 |
| FAIL | 5 | 0 | 0 | 5 | 0 |
| TIME / CANCEL / IDEM / LOOP | 11 | 0 | 0 | 11 | 0 |
| SEC | 9 | 0 | 0 | 9 | 0 |
| OBS | 4 | 0 | 0 | 4 | 0 |
| REG | 3 | 0 | 0 | 3 | 0 |
| STATE | 5 | 0 | 0 | 5 | 0 |
| RETRY | 4 | 0 | 0 | 4 | 0 |
| WORKER | 3 | 0 | 0 | 3 | 0 |
| DATABASE | 5 | 1 | 1 | 3 | 0 |
| DEPENDENCY | 5 | 2 | 0 | 2 | 1 |
| CONCUR | 4 | 0 | 0 | 4 | 0 |
| **合计** | **117** | **16** | **4** | **95** | **2** |

> **计数口径**：按 **ID 前缀**分组、**逐行主状态**计数（每行恰一个主状态 ⇒ 列和 = 行数）。
> **一致性断言（脚本已验证）**：`ASSET + PASSED + FROZEN-DESIGN + BLOCKED-GATE == 行数合计`。
> `BLOCKED-GATE` = `AI-06`（AI Gateway Runtime = ABSENT）+ `DEPENDENCY-05`（同上）—— 二者同因，
> 均为 `D-AGENT-16` 冻结后**剩余的实施门禁**（非未决 OQ）。
> `ASSET` = 既有冻结资产（继承面，无需新实现）；`PASSED` = 本轮文档轮实测通过（含零迁移）。

---

**END OF AGENT RUNTIME ACCEPTANCE MATRIX（2026-09-24）**
**END OF AGENT RUNTIME ACCEPTANCE MATRIX（STAGE 3 Decision Freeze · 状态词表升级 + `CONCUR-01..04` 新增 + §18 traceability 16/16；实测 116 行 = `ASSET` 16 + `PASSED` 4 + `FROZEN-DESIGN` 94 + `BLOCKED-GATE` 2，2026-09-25）**
**END OF AGENT RUNTIME ACCEPTANCE MATRIX（`O-1` 裁定同步 · 新增 `FAIL-05`（canonical 恰为 14 · `AI_TIMEOUT ⊂ AI_PROVIDER_FAILURE` · `BUDGET_EXCEEDED` 不并入 `TIMEOUT`）；§11 改写 + §16/§18 行号更新 ⇒ 实测 117 行 = `ASSET` 16 + `PASSED` 4 + `FROZEN-DESIGN` 95 + `BLOCKED-GATE` 2，2026-09-25）**
