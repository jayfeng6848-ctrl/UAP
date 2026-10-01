# P16 AI / AGENT RUNTIME ARCHITECTURE ANALYSIS

## 0. 性质

```text
PROPOSAL / ANALYSIS ONLY（NOT FROZEN · NOT APPROVED）
依据 = 现有 repository code / schema / 已冻结 Decision（D-AUTH-* · D-B16-* · D-P10-* · D-AGENT-*）
```

---

## 1. 现有分层与依赖方向（实测）

```text
core/           契约与纯逻辑（无 I/O）            —— 不得依赖 services / infrastructure / domains
services/       用例编排与持久化（Authorization · Audit · Consumer · Context · Identity …）
infrastructure/ 数据库 / 日志 / 运行时边界（RuntimeDatabase · principal 断言）
agent/          契约（registry · runtime · tools · memory · workflow）
intelligence/   契约（gateway · providers · models · router · policy · embeddings）
apps/           API（health/meta/identity/devices/sessions）· worker（P15 consumer）· frontend
domains/        （当前 9 py）
```

```text
当前守卫（实测）
  Core → Domain = 0（0 命中）
  core/event/interfaces.py 仅依赖 stdlib + core.audit（0 反向依赖）
  禁止直接 vendor SDK：intelligence/providers 声明 FORBIDDEN_DIRECT_IMPORTS
  tests/architecture/test_dependency_rules.py 覆盖既有 G-1…G-9
```

### 1.1 建议的 P16 依赖方向（提案，不是冻结）

```text
core/            AgentRun / ToolProposal / AIRequest 等**契约**（纯数据 + 协议）
services/        agent runtime 编排 · tool 执行编排 · AI gateway 实现 · routing 实现
intelligence/    provider adapter 实现（**不得**被 core/ 引用；不得被 agent/ 直接引用）
infrastructure/  provider HTTP 客户端 / secret 解析 / DB 边界
agent/           保持契约层（或迁移到 core/agent 契约 + services/agent 实现）

禁止方向（沿用既有规则）
  core → services · core → infrastructure · core → domains
  agent → services（执行必须经 Authorization + Tool）
  runtime → DB 直连（必须经 RuntimeDatabase / 明确 principal）
```

## 2. AI Gateway Capability Inventory

```text
Schema（0010 · P08 · FROZEN）
  ai_providers : key · display_name · adapter(opaque text) · base_url · enabled · health_status ·
                 health_checked_at · privacy_tier · max_classification · capabilities(JSONB) ·
                 config(JSONB) · secret_ref(text) · created_at/updated_at
                 = 平台级 ROOT（无 tenant_id · 零 seed · D-B16-11）
  ai_models    : provider_id(FK RESTRICT) · model_key · capabilities · context_window ·
                 max_output_tokens · input/output_price_per_1k · max_classification · is_private ·
                 latency_p95_ms · enabled
  ai_routes    : tenant_id(nullable) · space_id(nullable) · capability · priority ·
                 primary_model_id · fallback_chain · enabled
  ai_policies  : tenant_id(nullable) · space_id(nullable) · name · max_classification ·
                 allowed_privacy_tiers · denied_providers · require_private · allow_fallback ·
                 fallback_preserves_classification · budget_daily_usd · latency_budget_ms ·
                 redaction_profile · enabled
  ai_request_logs : 分区父表 + 当月子分区 · provider_id/model_id FK RESTRICT ·
                 agent_id/actor_id/tenant_id/space_id **无 FK**（D-B16-03）· status **无 CHECK**(D-B16-04) ·
                 列名 prompt_tokens/completion_tokens（D-4）· 表注释：「不存 prompt 原文，非审计」

Contract
  AIRequest(prompt, model?, parameters, tenant_id?) · AICompletion(text, model, provider, usage)
  AIProvider(Protocol: name, complete) · AIGateway(Protocol: complete, health)
  ProviderAdapter(Protocol: build(config) → AIProvider) · ProviderRegistry（空字典 registry）

Runtime = ABSENT
  · 无 adapter 实现 · 无 gateway 实现 · 无 request log 写入 · 无 health 巡检实现
  · config: AI_DEFAULT_PROVIDER=none · AI_DEFAULT_MODEL=none · AI_REQUEST_TIMEOUT_SECONDS=30
```

## 3. Agent Inventory

```text
Schema（0011 · P09）
  agents            : tenant_id NOT NULL · space_id · owner_id · key · name · status(draft/active/
                      disabled/archived) · max_risk_level · current_version_id · default_route_id ·
                      config · archived_at
  agent_versions    : agent_id · version · definition(JSONB) · input_schema · output_schema ·
                      allowed_tools(JSONB) · checksum · status(draft/published/deprecated/revoked) ·
                      published_by/published_at
  agent_permissions : agent_id · version_id · permission_id · tool_id · resource_scope(Legacy Opaque,
                      D-AUTH-23) · effect(allow/deny) · conditions
  tool_executions   : tenant_id · tool_id · tool_version_id · agent_id · actor_id ·
                      idempotency_key · status(running/succeeded/failed/denied/timeout) ·
                      input_digest · output_digest · risk_level · attempts · started_at/finished_at ·
                      duration_ms · error_code · correlation_id

Contract（agent/）
  AgentInput(text, tenant_id, space_id?, actor_id?, metadata) · AgentRunResult(status, output, reason)
  AgentRuntime(Protocol: run(agent_id, payload))
  registry / memory / workflow interfaces（契约）

Runtime = ABSENT
  · 无 runner · 无 lifecycle · 无 ExecutionContext 实现 · 无 context 八层管道
  · 无 tool dispatcher · 无 AI 调用 · 无 event 生产
```

```text
Agent Runtime State = PARTIAL FOUNDATION
  （Schema 完整 + 契约完整 + 授权侧就绪；但零执行能力）
```

## 4. Tool Execution Analysis

```text
Schema（0008 · B1-5）
  tools          : tenant_id(nullable) · key · name · risk_level · timeout_ms · retry_policy(JSONB) ·
                   idempotency_mode · audit_policy · approval_required · enabled · disabled_at
  tool_versions  : tool_id · version · input_schema · output_schema · risk_level · timeout_ms ·
                   handler_ref(text) · checksum · status · published_at
  tool_permissions: tool_id · version_id · permission_id · effect(allow/deny) · conditions

Authorization（存在）
  services/authorization/tools.py::ToolGate.authorize(tool_id, subject, action, resource,
                                                      tenant_id, space_id, scope, request_id)
    · tool 不存在 / disabled ⇒ DENY
    · PermissionResolver.tool(grant_rows, action, resource, scope)
    · scope 评估 + approval_required 组合（ToolGate 与 policy 取 OR ⇒ 任一要求即需人工）
    · fail-closed：AuthorizationUnavailable ⇒ DENY

Execution = ABSENT
  · handler_ref 全仓 0 处解析 / 调用
  · 无 dispatcher · 无进程边界 · 无 timeout/retry 落地 · 无 tool_executions 写入
  · ⇒ tool 授权已完成，tool 执行完全缺失
```

## 5. Event / Outbox Readiness（P16 Producer Analysis）

```text
事件载体 = events（分区表）
  可用列：event_type · schema_version · tenant_id(NULLABLE) · space_id · actor_type · actor_id ·
          subject_type · subject_id · payload(JSONB) · correlation_id · causation_id · status ·
          worker_id/claimed_at/lease_expires_at/attempts/next_attempt_at/last_error/delivered_at
消费侧 = P15（claim / lease / heartbeat / retry / recovery / finalize · concurrency 4 · lease 120s ·
          heartbeat 40s · MAX_ATTEMPTS 10 · backoff 5→600s · event_id 为幂等主键）
生产侧 = EMPTY（production_allowlist() 返回空 allowlist · handlers = 0）

提案（PROPOSAL，不是冻结）
  若 Human 决定激活首个 production event，必须同时给出：
    event_type（命名空间形态 `namespace.aggregate.action`，受 ck_events_event_type 约束）
    producer（哪个服务在哪个事务边界内写 events）
    payload schema（版本化 schema_version）
    tenant semantics（tenant-scoped 或 NULL=platform-scoped）
    actor semantics（originating actor 保留 · 不得伪造 system actor）
    handler（幂等可证明；否则不做——O-6）
    failure/retry 语义（复用 P15 冻结模型，不新增）
    audit 关联（correlation_id / causation_id 串联）
  备选：P16 不激活 production event（slice 以 tool_executions + audit 作为产出），
        把首个 production event 留给后续阶段。两种都属于 Human Decision。
```

## 6. Proposed Minimum Vertical Slice（提案）

| 环节 | 依赖对象（已存在） | 缺口 | 需 Human Decision |
|---|---|---|---|
| Authorized Actor | AuthenticatedContext(P14) · sessions/devices/identity | — | — |
| Agent | agents / agent_versions（已发布版本） | Run 入口与 binding | P16-D02 |
| AI Provider | ai_providers / ai_models / ai_policies（表） | adapter 实现 + 凭据 | P16-D03 / D07 |
| Model | ai_routes / ai_models（表） | routing 实现 | P16-D04 |
| Tool Decision | agent_versions.allowed_tools | 提案解析 | P16-D06 |
| Authorization | ToolGate · 12 actions · scopes | agent→tool→permission 绑定解析 | P16-D06 |
| Tool Execution | tools / tool_versions | dispatcher（不存在） | P16-D06 / D11 |
| Event | events + P15 consumer | producer（EMPTY） | P16-D08 |
| P15 Consumer | 完整 | handler（0） | P16-D08 / D09 |
| Persisted State | 既有表 | 视 slice 而定 | P16-D12 |
| Audit Evidence | services/audit + audit_logs | 三审计分离落地（AI/工具/授权） | P16-D05 / D07 |

```text
最小可交付形态（建议方向，非冻结）：
  Run 记录（agent_runs：DESIGN ONLY 存在于未入库契约）→ 或复用 tool_executions 作为唯一执行台账，
  避免设计重复 ledger（P16-D02/D12 需裁决）
```

## 7. Provider / Model Routing（提案）

```text
建议逻辑（PROPOSAL · NOT FROZEN）：
  Task → Capability → Policy → Provider → Model
    Task        ：来自 agent_versions.definition / 请求意图
    Capability  ：ai_models.capabilities ∩ ai_providers.capabilities
    Policy      ：ai_policies（tenant/space 覆盖平台默认）⇒ max_classification / privacy /
                  require_private / denied_providers / budget / latency / redaction_profile
    Provider    ：ai_providers.enabled ∧ health_status ∧ privacy_tier ∧ max_classification
    Model       ：ai_models.enabled ∧ capability ∧ context_window ∧ max_classification ∧
                  is_private ∧ latency_p95 · fallback_chain（ai_routes）
  失败语义：fallback 仅当 allow_fallback ∧ fallback_preserves_classification
```

```text
要求（Required abstraction，若 Human 批准实施）
  1. ProviderAdapter 实现 + registry 注入（禁止 adapter 猜测 · adapter 文本为 opaque）
  2. 凭据注入边界（secret_ref → 解析器 → adapter；不得进入日志/事件/审计/prompt）
  3. 请求/响应模型（usage 统计 → ai_request_logs；**不写 prompt 原文**）
  4. 错误分类与 timeout/retry 映射（与 P15 的 retry 语义区分：AI 调用是同步调用，不是 outbox 重试）
```

## 8. 实施顺序建议（PROPOSAL）

```text
1. 先冻结 P16-D01…D14（Human Decision）
2. 最小契约落地（core 层）：Run / ToolProposal / AIRequest 的最终形状
3. Authorization 绑定解析（agent → tool → permission）
4. Provider adapter + 凭据边界（不含真实 key）
5. Tool 执行边界（进程内 or 隔离；失败/超时/幂等）
6. Event producer + handler（若 D08 批准激活）
7. Audit 三分离落地 + 证据
8. 测试矩阵（unit / architecture / security / integration · 逐文件 allowlist）
```

**END OF P16 AI / AGENT RUNTIME ARCHITECTURE ANALYSIS（PROPOSAL ONLY）**
