# P16 AI / AGENT RUNTIME — IMPLEMENTATION CONTRACT

## 0. 状态与权威

```text
状态            = RULES AUTHORITY（由已冻结决策派生；本文件不是新决策来源）
派生自          = PDL 附录 V（P16-D01…D14 FROZEN）+ D-AGENT-01…16 + D-AUTH-* + D-B16-* + D-P10-*（含附录 U）
Baseline（实测）= HEAD 1bc60834415cb4f518cd695c93cd79bec986228e · Alembic 0017_p13_seed · 0018+ = 0
Supersede 关系   = 旧 AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md（untracked · 基线 034ee97/0012）
                   在本文件生效范围内 **obsolete as P16 authority**（其历史内容不改写、不删除）
不得           = 创建第二套 Decision Log · 修改历史 Decision · 以本文件替代 PDL
```

## 1. 范围

```text
IN        = Provider Runtime · Model Routing · Agent Runtime · Run lifecycle · Actor propagation ·
            Tool authorization · Tool execution · Credential boundary · AI request recording ·
            Agent run recording · Audit linkage · 最小 Agent API
CONDITIONAL = Event integration seam（test-only publisher/handler）
              Production Allowlist = EMPTY · Production Handlers = 0（D08 REJECT）
OUT       = C-7 · C-2 · C-4 · C-8 · D-01 repair · Marketplace · Multi-Agent · Memory · RAG ·
            Vector DB · Workflow Engine · Prompt Platform · Billing · Admin UI · Streaming ·
            具体消息框架 · 多区域 · 自动成本优化
```

## 2. 组件落位（层级边界）

```text
core/            仅契约与纯逻辑（无 SQLAlchemy / psycopg / FastAPI / provider SDK / HTTP / 文件系统 secret 解析）
  core/agent     Run 契约 · 状态机枚举 · ToolProposal 形状
  core/ai        AIRequest / AICompletion / 路由决策的纯数据形状（如需要）
agent/           既有契约包（registry / runtime / tools / memory / workflow）— 保持契约层
intelligence/    既有契约包（gateway / providers / models / router / policy / embeddings）
services/        编排：agent runtime · routing · gateway 编排 · credential 使用编排 · tool 执行编排
infrastructure/  传输与解析：HTTP、provider SDK 适配、credential resolver、DB 边界（RuntimeDatabase）
apps/            API（Router → Application Service → Runtime），handler 不含 SQL
```

```text
必须保持：Core → Domain = 0 · core ↛ services · core ↛ infrastructure ·
          agent ↛ services（执行必须经 Authorization + ToolGate）·
          runtime 经 RuntimeDatabase 访问数据库（禁止 ad-hoc engine / 全局连接）
```

## 3. Actor / Authorization 边界（D05）

```text
Run 必须保存：originating actor · agent · tenant · space
originating actor = immutable（不得替换为 platform_admin / uap_bootstrap / uap_migrator）
受保护操作的授权 = Actor Authorization ∧ Agent Authorization ∧ ToolGate
  ⇒ Agent 不因被 User 调用而获得 User 的全部权限
  ⇒ User 不能经被授权 Agent 绕过 Agent 自身权限
Actor ≠ Agent ≠ Worker ≠ DB principal（不得合并身份）
```

## 4. Run 契约（D02 / D12）

```text
生命周期：CREATED → RUNNING → WAITING_TOOL → COMPLETED
异常：FAILED · CANCELLED（终态）
同一 run_id 贯穿：agent_runs · ai_request_logs · tool_executions · audit（correlation）
agent_runs 必需字段：id · tenant_id(NOT NULL) · space_id · agent_id · agent_version_id ·
  originating actor（type + id）· status · input_digest · result_digest / safe result metadata ·
  created_at · started_at · completed_at · failure_code · failure_metadata
禁止持久化：API key · credential plaintext · provider auth header · 完整 secret · 原始 prompt（默认不存）
不新增：agent_run_steps / agent_execution_logs / agent_attempts / agent_tool_history / agent_runtime_events
```

## 5. Provider / Routing 边界（D03 / D04）

```text
三层：AIProvider（vendor-agnostic 契约）→ ProviderAdapter（构建 provider）→ ProviderRegistry（名称 → adapter）
第一阶段：只实现 1 个可用 adapter（作为纵向验证）；vendor 细节不得渗透 Core / Agent 契约
Routing（确定性）：Task → Capability → Policy → Route → Provider → Model
  必须：capability 匹配 · route/provider/model enabled · classification 满足 policy ·
        privacy tier 满足 policy · require_private ⇒ 仅 private-compatible model · priority 确定性
  fallback：仅当 allow_fallback ∧ fallback_preserves_classification，按显式顺序（禁随机/隐式/供应商内部 fallback）
不做：成本优化器 · 质量优化器 · 延迟预测 · ML routing
```

## 6. Credential 边界（D07）

```text
secret_ref = opaque reference（不是 secret）；第一阶段 = env-backed resolver（形如 env:OPENAI_API_KEY）
唯一流向：Runtime environment → Secret Resolver → Provider Adapter
Agent / Tool / Worker：NEVER SEE SECRET
禁止出现于：DB 明文 · source · JSON config · event · audit · ai_request_logs · exception · prompt · response
不得自动包含：secret_ref value · credential material · environment dump · provider auth header
```

## 7. Tool 边界（D06）

```text
唯一执行前闸门 = ToolGate
顺序：Tool exists → enabled → version valid → agent permission → actor authorization →
      resource scope → approval requirement → idempotency rule → execute
任何失败 ⇒ DENY（fail-closed）
scope：空 ⇒ 走已冻结普通 permission path；非空 ⇒ 仅当 ToolGate 能证明语义与边界时才执行，否则 DENY
handler_ref：**只能作为 Registry key**；禁止 dynamic import / eval / exec / 任意 callable / 任意模块加载
执行必须记录：tool_id · tool_version_id · status · attempts · duration_ms · error_code · correlation_id
第一把 Tool 必须 LOW RISK / DETERMINISTIC / SIDE-EFFECT FREE（如 platform.clock.now）
```

## 8. API 边界（D13）

```text
POST /agents/{agent_id}/runs   → create + execute one run
GET  /agent-runs/{run_id}      → status / safe result metadata
禁止：POST /tools/{tool_id}/execute（不暴露 tool 直调；不得绕过 Agent/Authorization/ToolGate/Runtime）
Handler 边界：Router → Application Service → Agent Runtime → Repository/RuntimeDatabase
             （Router 不得直接 SQL / provider SDK / tool handler）
```

## 9. Audit / AI request log 边界

```text
ai_request_logs ≠ audit（分别保留）
ai_request_logs 记录：provider · model · capability · classification · usage · cost · latency ·
                     status · run correlation · actor correlation · agent correlation
默认不记录：raw prompt · raw secret · raw credential
audit_logs 为审计证据（append-only）；run_id 通过 correlation_id 关联
三审计分离保持：authorization audit ≠ tool execution audit ≠ agent run audit
```

## 10. Error taxonomy（必须使用，不得自造）

```text
AUTHORIZATION_DENIED · AGENT_DISABLED · AGENT_VERSION_INVALID · POLICY_DENIED ·
ROUTE_UNAVAILABLE · PROVIDER_UNAVAILABLE · CREDENTIAL_UNAVAILABLE · MODEL_REQUEST_FAILED ·
TOOL_NOT_FOUND · TOOL_DISABLED · TOOL_UNAUTHORIZED · TOOL_SCOPE_DENIED ·
TOOL_APPROVAL_REQUIRED · TOOL_TIMEOUT · TOOL_EXECUTION_FAILED · IDEMPOTENCY_CONFLICT ·
INTERNAL_RUNTIME_ERROR
错误信息不得泄漏：API key · secret_ref resolved value · provider auth header · 内部凭据材料
```

## 11. 超时与循环上限（fail-closed）

```text
必须可配置且显式：AI request timeout · Tool timeout · Agent overall timeout
必须存在：MAX_TOOL_CALLS_PER_RUN · MAX_RUNTIME_DURATION
达到任一上限 ⇒ FAILED / TIMEOUT + 安全 failure evidence
禁止：unbounded wait · infinite retry · infinite agent loop · automatic provider retry（D09）
```

## 12. 版本 / 生命周期规则

```text
只执行 published AgentVersion（禁 draft / revoked / deprecated）
只执行 published/active ToolVersion；执行必须记录 tool_version_id
current_version_id 只能引用合法版本
不建设 Prompt 平台 / Memory / RAG / Vector DB（P16 明确 OUT）
```

## 13. Database / Migration 契约

```text
新增（且仅新增）：agent_runs（D12 LIMITED）
可选最小列追加：ai_request_logs.run_id（注意分区兼容 · 不建跨分区运行时 FK）·
                tool_executions.run_id（受控 FK 可选；删除策略不得级联删除历史台账）
禁止：修改 0013–0017 · 修改 P13/P14 表语义 · 修改 ai_request_logs 分区设计 · 删除既有列 ·
      变更既有 FK policy · 新增 dedup 表
Migration 必须：0017 → 0018_<name> · 支持 upgrade / downgrade / upgrade ·
                 ownership-aware downgrade · 不 rewrite 0017
Formal DB `uap`：除非独立授权，否则 NO seed / NO agent / NO credential / NO provider secret
Test DB：可建测试数据；audit_logs 保持 append-only（不得要求 == 0）
```

## 14. Grant 契约（D11）

```text
只扩展 uap_runtime（禁止新 role）
SELECT : agents · agent_versions · agent_permissions · tools · tool_versions · tool_permissions ·
         ai_providers · ai_models · ai_routes · ai_policies
INSERT : ai_request_logs · agent_runs · tool_executions
UPDATE : agent_runs · tool_executions
禁止   : DELETE（上述三表）· UPDATE agents/agent_versions/tools/tool_versions ·
         ALTER / DDL · CREATE ROLE · SET ROLE migrator
验证   : 见 P16_RUNTIME_PRIVILEGE_MATRIX.md · unexpected allowed = 0 · 禁止 GRANT ALL
```

## 15. 测试契约（D14）

```text
Unit        : provider registry · routing · policy filtering · actor propagation · tool gate ·
              idempotency · run state machine · credential redaction · failure taxonomy
Architecture: Core → Domain = 0 · core ↛ services · core ↛ infrastructure ·
              core/agent 契约无 provider SDK · core 无 DB import
Security    : secret 永不返回/记录/入审计/入事件/入 prompt · agent/tool/worker 不可读 secret ·
              runtime 不可升权（SET ROLE / CREATE ROLE / ALTER）· 不可绕过授权
Integration : Actor → Agent → AI Provider → Agent Run → ToolGate → Tool Execution → Audit
Regression  : P14 frozen 不变 · P15 frozen 不变 · D-02 历史失败保留 ·
              Forbidden tests = 0 · OI-G-4 = 0 execution
执行纪律    : 逐文件显式 allowlist（禁目录级 pytest / collect-only sweep）
```

## 16. 关键禁止（出现即 BLOCK）

```text
secret leakage · authorization bypass · agent 隐式继承 user 权限 · runtime 升权 ·
dynamic handler import · Core → Domain 违规 · core import infrastructure ·
未决策激活 production event · 提交生产 secret · 宽泛 DB grant · 无界 tool loop
```

**END OF P16 AI / AGENT RUNTIME IMPLEMENTATION CONTRACT（RULES AUTHORITY · 派生自已冻结决策）**
