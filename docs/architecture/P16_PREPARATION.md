# P16 PREPARATION

## 0. 性质与边界

```text
阶段     = P16 PREPARATION / HUMAN DECISION PREPARATION
性质     = DISCOVERY / ANALYSIS / PROPOSAL / DECISION INPUT
NOT      = FROZEN · ACCEPTED · IMPLEMENTED · RELEASED
本轮禁止 = code / migration / DB mutation / commit / tag / push / prototype
```

```text
Baseline（实测）
  HEAD           = 1bc60834415cb4f518cd695c93cd79bec986228e
  origin/main    = 1bc60834415cb4f518cd695c93cd79bec986228e
  latest tag     = UAP-V0.1.14-P15-EVENT-CONSUMER
  local tags     = 13 · real staged = 0
  dirty          = 28 modified tracked + 103 untracked（historical / F-RP-02 / BATCH-D / future docs）
  Alembic        = 0017_p13_seed（single head）· 0018+ = 0
  Security       = 51/6/5/0/245 · default ACL 0 · C2 185e95be… · CC-7 intact
  Formal `uap`   = 0 表（prestate == poststate）
```

---

## 1. Executive Summary

```text
结论 = P16 的“设计”已经冻结（D-AGENT-01…16 · tracked PDL），
       但“运行时”整体不存在；Schema 侧已有大量可用结构。
       P16 不是从零设计 AI 平台，而是：把已冻结的 Run 契约落到
       Identity + Authorization + Runtime Principal + Tool + Event + Audit 边界内，
       并补齐 3 类硬缺口：执行路径 · 数据库授权 · 凭据边界。
```

三个最重要的发现：

```text
F-P16-01（CRITICAL）AI/Agent 运行时代码 = 0
  · agent/ 与 intelligence/ 仅有 Protocol / dataclass 契约，无任何实现
  · services/ 无 ai / agent / tool 执行服务
  · 全仓无 ai_request_logs / tool_executions 写入代码
  · 无 provider adapter 实例化路径（ProviderRegistry 为空 registry）

F-P16-02（CRITICAL）运行时 principal 当前对 AI/Agent 面完全无权限
  · uap_runtime 对 ai_providers / ai_models / ai_routes / ai_policies /
    ai_request_logs / tool_executions / tool_versions / tool_permissions = 无任何 grant
  · 仅对 agents / agent_versions / agent_permissions / tools 有 SELECT
  · ⇒ P16 必然需要新 grant（或新 principal）⇒ 必须 Human Decision（P16-D11/P16-D12）

F-P16-03（HIGH）P16 设计权威部分是未提交文档
  · AGENT_RUNTIME_*（4 份，含 IMPLEMENTATION_CONTRACT）当前 untracked
  · 其声明的 HEAD/Alembic 基线为 034ee97 / 0012（已过期）
  · 决策正文 D-AGENT-01…16 确在 tracked PDL（84 处命中）⇒ 权威可追溯，但契约层未入库
```

## 2. Current Architecture Baseline（只读实测）

```text
层次          内容                                                                  状态
core/         audit · auth · device · event · identity · membership · permission · 契约（纯逻辑）
              policy · resource · session · space · tenant（28 py）
services/     authorization · audit · consumer(P15) · context · device · identity · 实现（无 AI/Agent）
              mapping · session · use_cases（43 py）
infrastructure/ database（runtime/principal/health/…）· logging · runtime（24 py）  实现
agent/        registry · runtime · tools · memory · workflow interfaces（11 py）     契约 only
intelligence/ gateway · providers · models · router · policy · embeddings（13 py）  契约 only
apps/         api（health/meta/identity/devices/sessions）· worker(P15) · frontend   实现 / 无 AI API
domains/      （9 py）                                                              —
```

```text
DB 表（P08/P09/P10 既有）
  AI Gateway（0010）: ai_providers · ai_models · ai_routes · ai_policies · ai_request_logs(分区)
  Agent/Tool（0011）: agents · agent_versions · agent_permissions · tool_executions
  Tool Registry（0008）: tools · tool_versions · tool_permissions
  Event/Audit（0013）: events(分区) · audit_logs(分区)
  Identity/Authz: users · identities · credentials · devices · sessions · roles · permissions ·
                  role_permissions · resource_permissions · resources · memberships ·
                  tenant_memberships · platform_memberships · acl_subject_types
```

## 3. Capability Inventory（摘要 · 详细见架构分析文档）

```text
AI Gateway
  schema      = 完整（5 表 / 73 列 / 分区 / FK RESTRICT / 无 status CHECK / capability / privacy_tier /
                max_classification / secret_ref / pricing / context_window / is_private / latency）
  contract    = AIGateway / AIProvider / AIRequest / AICompletion（Protocol + dataclass）
  runtime     = ABSENT（无 adapter · 无 gateway 实现 · 无 request log 写入 · 无 router 实现）
  seed        = ZERO（ai_providers = 平台级 ROOT · 零 seed · D-B16-11）
  config      = AI_DEFAULT_PROVIDER=none · AI_DEFAULT_MODEL=none · AI_REQUEST_TIMEOUT_SECONDS=30

Agent
  schema      = agents / agent_versions / agent_permissions（+ tool_executions ledger）
  contract    = AgentRuntime / AgentInput / AgentRunResult（Protocol + dataclass）
  runtime     = ABSENT（无 runner · 无 lifecycle · 无 context 管道 · 无 tool dispatcher）
  permission  = ToolGate（授权侧）已实现；执行侧不存在

Tool
  schema      = tools / tool_versions（handler_ref · checksum · timeout · retry · idempotency_mode ·
                audit_policy · approval_required）· tool_permissions
  authz       = services/authorization/tools.py::ToolGate（enabled / grant / scope / approval）
  execution   = ABSENT（handler_ref 无任何解析或调用点）

Authorization
  subjects    = USER / ROLE / AGENT（D-AUTH-18）
  actions     = 12 canonical（read…admin · D-AUTH-05/25）
  scopes      = PLATFORM / TENANT / SPACE（D-AUTH-06）
  semantics   = DENY > ALLOW · FAIL CLOSED · 无授权缓存 · approval ≠ ALLOW

Event / Audit
  consumer    = P15 完整（claim/lease/heartbeat/retry/recovery/finalize）
  production allowlist = EMPTY · production handlers = 0
  audit       = services/audit/writer.py + audit_logs（append-only · 触发器防改）
```

## 4. Runtime Gap Analysis（P16 必须补齐的缺口）

| 链路环节 | 现状 | 缺口 |
|---|---|---|
| Authorized Actor → Agent | AuthenticatedContext（P14）已有；agents 表已有 | Agent 运行入口（谁触发 · 如何绑定 actor） |
| Agent → AI Provider | 契约存在 | Provider adapter 实现 · secret 解析 · timeout 映射 |
| Provider → Model | ai_models/ai_routes/ai_policies 表存在 | routing 实现（capability/policy/privacy/classification） |
| Model → Tool Decision | agent_versions.allowed_tools 存在 | 提案（proposal）与解析路径 |
| Tool Decision → Authorization | ToolGate 已实现 | agent→tool→permission 的绑定解析（agent_permissions/tool_permissions） |
| Tool → Execution | tool_versions.handler_ref 存在 | 执行器 / dispatcher / 进程边界（不存在） |
| Execution → Event | P15 consumer 就绪 | producer（当前 allowlist EMPTY） |
| Event → Persisted State | P15 完整 | handler 实现（0 个） |
| 全链 → Audit | 审计写入路径存在 | AI/Agent 三审计分离的落地（D-AUTH-15） |
| 全链 → Runtime Principal | uap_runtime 边界存在 | ai_*/tool_executions 的 grant（当前为 0） |

## 5. Risk / Finding Registry

| ID | Finding | Evidence | Severity | P16 Impact | Blocking? | Human Decision? | Recommended disposition |
|---|---|---|---|---|---|---|---|
| F-P16-01 | AI/Agent 运行时代码为 0（仅契约） | agent/·intelligence/ 仅 Protocol；services/ 无 ai/agent 服务；0 处 ai_request_logs/tool_executions 写入 | CRITICAL | 决定 P16 工作量全部落在新实现 | NO（预期内） | YES（P16-D02/P16-D03） | 登记为 P16 主体范围 |
| F-P16-02 | uap_runtime 对 ai_*/tool_executions 无 grant | 实测 grant 清单（29 表 · 51 项） | CRITICAL | 无 grant ⇒ 无法读写 | YES（若坚持现有 principal） | YES（P16-D11/P16-D12） | 新 grant / 新 principal 二选一，须 Human 冻结 |
| F-P16-03 | AGENT_RUNTIME_* 契约层未入库（untracked）且基线过期 | `git ls-files --error-unmatch` 失败；文档声明 HEAD 034ee97 / 0012 | HIGH | 设计权威不在发布物内；clean clone 无该契约 | NO | YES（P16-D02） | 建议以独立 governance 决定是否入库 |
| F-P16-04 | Tool 执行器不存在（handler_ref 无解析点） | 全仓 0 处 handler_ref 调用 | CRITICAL | vertical slice 的关键缺口 | YES（若 slice 含真实 tool 执行） | YES（P16-D06） | 决议 tool 执行边界（同进程/隔离进程） |
| F-P16-05 | AI provider 凭据解析路径不存在 | secret_ref 0 处引用；.env.example 仅占位 | CRITICAL | 无凭据边界无法调用 provider | YES | YES（P16-D07） | 冻结凭据注入与读取边界 |
| F-P16-06 | first production event 不存在（allowlist EMPTY / handlers 0） | services/consumer/kernel.production_allowlist() 返回空 | HIGH | 事件链末端需要决策 | NO | YES（P16-D08） | 决策是否在 P16 激活首个 production event |
| F-P16-07 | ai_request_logs 无 status CHECK 且「不存 prompt 原文」为非审计定位 | 0010 迁移注释 D-B16-04 / 表注释 | MEDIUM | 影响可观测与审计边界划分 | NO | YES（P16-D05 相关） | 明确 AI request log ≠ audit |
| F-P16-08 | ai_request_logs.agent_id/actor_id/tenant_id/space_id 无 FK（D-B16-03 冻结） | 0010 / schema 测试 | LOW | 历史设计，禁止自行加 FK | NO | NO（已冻结） | 保持不变 |
| F-P16-09 | agents.tenant_id NOT NULL vs events.tenant_id nullable | 0011 vs 0013 | MEDIUM | 平台级 agent 语义未定义 | NO | YES（P16-D10） | 冻结 agent 的 tenant 语义 |
| F-P16-10 | F-RP-02 remaining（tests/conftest.py · infrastructure/database/__init__.py）仍在工作区 | git status 实测 | MEDIUM | P16 集成测试可能依赖 dual-DSN fixtures | NO（当前） | 独立决定 | 登记为 P16 dependency candidate（非 blocker） |
| F-P16-11 | 17 个 tracked 文件在 Windows 工作区为 CRLF（含 AUTHORIZATION 面） | 实测扫描 | LOW | 若进入 release payload 会影响哈希基准（F-RP-06 已冻结规则） | NO | NO | 沿用 committed-blob 哈希基准即可 |
| F-P16-12 | UAP_PROJECT_MASTER_DOSSIER.md 不存在（AGENTS.md 引用之） | Test-Path = False | LOW | 影响跨会话连续性，不影响 P16 | NO | YES（文档治理） | 登记 discrepancy |
| F-P16-13 | 第一个 production handler / 生产者缺失导致 P15 capability 处于「就绪但空转」 | P15 文档 + 实测 | INFO | P16 正是激活它的阶段 | NO | YES（P16-D08） | 纳入 P16 决策 |

```text
Blocking findings（对 P16 实施）= F-P16-02 / F-P16-04 / F-P16-05
（三者均需 Human Decision，不能在 PREP 阶段自行选择）
```

## 6. Recommended P16 Scope（摘要）

```text
IN（建议最小 vertical slice）
  一条 Request → Run → Provider → Tool Proposal → Authorization → Tool Execution →
  Event → P15 Consumer → State → Audit 的最小链路，且：
    · 只用既有表（除非 Human 决定需要新表）
    · 只增加必要 grant（Human 冻结）
    · production event = 最多 1 个且必须有 handler + idempotency 证据

OUT（明确不做）
  C-7 Frontend · C-2 Management · C-4 Bootstrap CLI · C-8 Audit Deepening ·
  D-01 Foundation Repair · Agent Marketplace · Multi-Agent Orchestration ·
  Memory System · Prompt Management · Vector DB · RAG · Workflow Engine ·
  Billing · Admin UI · Streaming · 具体 worker 框架（Celery 等）
```

## 7. PREP Verdict

```text
P16 PREP = PASS WITH OPEN DECISIONS

理由：
  · Architecture / Security / Data / Event / Tests / Git 六个面均已建立可核查基线
  · 所有需要语义冻结的点已单列为 P16-D01…D14（无可自行决定项）
  · 存在 3 个阻塞性决策（principal/grant · tool 执行边界 · 凭据边界）尚未由 Human 冻结
  · 未发生任何 implementation / schema / runtime code / release 行为

不得使用：READY TO IMPLEMENT（Human Decision 未完成）
```

## 8. Next

```text
下一步 = HUMAN DECISION — P16-D01…D14（见 P16_DECISION_MATRIX.md）
在 Human Decision 完成前：NO IMPLEMENTATION / NO SCHEMA / NO RUNTIME CODE / NO RELEASE
```

**END OF P16 PREPARATION（PREP ONLY · NOT FROZEN）**
