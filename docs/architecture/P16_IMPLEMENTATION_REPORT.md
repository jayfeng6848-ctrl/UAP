# P16 IMPLEMENTATION REPORT

## 0. 性质

```text
阶段 = P16 IMPLEMENTATION（D01…D14 已冻结）· 本文件 = 实施 + 验收证据
状态 = 未 commit / 未 tag / 未 push（全部为工作区变更）
```

## 1. 交付物清单（实际写入的文件）

### Governance

```text
docs/architecture/PLATFORM_DECISION_LOG.md           附录 V（append-only · P16 freeze）
docs/architecture/P16_HUMAN_DECISION_FREEZE.md       决策摘要
docs/architecture/P16_AI_AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md   rules authority
docs/architecture/P16_RUNTIME_PRIVILEGE_MATRIX.md    权限矩阵（含 unexpected allowed = 0 验证法）
docs/architecture/P16_IMPLEMENTATION_REPORT.md       本文件
```

### Schema

```text
migrations_alembic/versions/0018_p16_agent_runtime.py
  · 新增 agent_runs（唯一新表 · FK 全 RESTRICT · status/actor_type/tool_calls CHECK · updated_at trigger）
  · ai_request_logs + run_id（不建跨分区 FK）· tool_executions + run_id（不建 FK）+ 部分索引
  · uap_runtime 最小 GRANT（SELECT 9 表 · INSERT 3 表 · UPDATE 2 表 · DELETE 0）
```

### Contracts / Services / Infrastructure / API

```text
core/agent/{__init__,run,errors}.py        Run 状态机 · ToolProposal · 17 项错误码（封闭集合）
core/ai/{__init__,routing}.py              RouteRequest / RouteDecision
services/ai/{credentials,routing,gateway}.py  凭据解析边界 · 确定性路由 · gateway 编排（含日志白名单）
infrastructure/ai/{__init__,adapters}.py      provider adapter + stdlib HTTP transport（唯一传输层）
services/agent/{tools,repository,runtime,authorizer,use_cases}.py
                                          工具 registry/executor · 台账读写 · run 编排 · P09 授权适配 · use-case
apps/api/routes/agent_runs.py             POST /agents/{agent_id}/runs · GET /agent-runs/{run_id}
apps/api/main.py                          路由注册
```

### Tests

```text
tests/unit/test_p16_routing.py · test_p16_credentials.py · test_p16_run_contract.py · test_p16_tools.py
tests/architecture/test_p16_boundaries.py
tests/security/test_p16_secret_boundary.py
```

## 2. 验收矩阵（实测）

| 面 | 判据 | 结果 |
|---|---|---|
| A Architecture | Core 无 SQLAlchemy/psycopg/FastAPI/HTTP/SDK import · Core ↛ services/infrastructure · 无 vendor SDK 名称 · runtime 无 dynamic import/eval · 传输只在 infrastructure | **PASS**（`test_p16_boundaries.py` 5 项） |
| B Identity / Authorization | Actor≠Agent≠Worker≠DB principal（沿用）· 无特权 fallback · Actor ∧ Agent 授权（actor 授权缺失 ⇒ 直接 DENY，fail-closed） | **PASS**（runtime 强制 authorizer；无 authorizer ⇒ AUTHORIZATION_DENIED） |
| C AI | ProviderRegistry 可用 · adapter 可用 · routing 确定性（priority→id）· policy 强制（classification ceiling / privacy / denied providers）· fallback 需授权且保分类 · 凭据边界强制 | **PASS**（routing 7 项 · credentials 4 项 · gateway 3 项） |
| D Tool | ToolGate 语义保留 · version 校验（需 published）· agent grant（allow）· scope 无证明即 DENY（不解析 opaque 字段）· approval 阻断 · 幂等不可证明即拒绝 · timeout 有界 · 失败不泄漏 | **PASS**（tools 5 项 + runtime 实现） |
| E Run | agent_runs 生命周期（CREATED→RUNNING→…→COMPLETED/FAILED）· run_id 贯穿 · 失败态与 failure_code · 安全结果元数据 | **PASS**（状态机 5 项 + migration 实测） |
| F Audit | ai_request_logs ≠ audit · audit append-only · run/agent/actor 可追踪（run_id 关联） | **PASS**（代码路径 + 权限面；审计写入复用既有 INSERT 权限） |
| G Security | unexpected allowed = 0 · secret leakage = 0 · privilege escalation = 0 | **PASS**（见 §3） |
| H Regression | P14/P15 frozen 不变 · D-02 保留 · Forbidden tests = 0 · OI-G-4 = 0 | **PASS**（P15 = 65/0；冻结守卫 37/0） |

## 3. 安全验证（实测）

```text
P16 测试集          = 29 passed / 0 failed
  含负路径：未注册 handler ⇒ TOOL_NOT_FOUND（不以字符串执行）· handler 抛错 ⇒ 不泄漏原始消息 ·
            timeout ⇒ TOOL_TIMEOUT · 凭据缺失 ⇒ CREDENTIAL_UNAVAILABLE 且未发起调用 ·
            gateway 失败 ⇒ 消息不含 secret/引用名 · 日志 payload ⊆ 白名单（无 prompt / 无 secret）
冻结回归            = P15 allowlist 65/0 · 架构守卫 37/0（含 agent resource scope opaque 与依赖规则）
迁移与权限（隔离库 uap_p15_verify）
  upgrade head → 0018_p16_agent_runtime（single head）
  agent_runs 存在 · ai_request_logs.run_id 存在 · tool_executions.run_id 存在
  uap_runtime 实测：agent_runs INSERT,SELECT,UPDATE · tool_executions INSERT,SELECT,UPDATE ·
                    ai_request_logs INSERT · ai_providers/ai_models/ai_routes/ai_policies/
                    tool_versions/tool_permissions SELECT
  DELETE 授权计数 = 0（unexpected allowed = 0）
  downgrade base → upgrade head = PASS（验证后删除验证库）
Formal DB uap = 0 表（未触碰）· Test DB 未因本轮写入业务数据
```

## 4. 与冻结契约的一致性

```text
Production Allowlist = EMPTY（未激活任何生产事件）· Production Handlers = 0
未修改 0013–0017 · 未改写 P13/P14/P15 语义 · 未新增 role / principal
未使用 dynamic import / eval / exec · handler_ref 仅作 registry key
Core → Domain = 0 · 凭据只经 env → resolver → adapter
agents.tenant_id NOT NULL 保持；run.tenant_id NOT NULL；space 可空
```

## 5. 明示缺口与限制（不隐藏）

```text
G-1 未编写全链 DB 集成测试（Actor→Agent→Provider→Tool→Audit 走真实数据库行）。
    本轮验证为：unit 29 + architecture 5 + security 4 + migration/grants 实测 + 冻结回归。
    原因：上下文/执行预算限制；已登记为 **F-P16-I-01（OPEN · 必须在 P16 ACCEPTANCE GATE 前补齐）**。
G-2 `P09ActorAuthorizer` 已在生产路径接线（apps/api use-case → AuthorizationService(engine)），
    但本轮未有集成测试证明其在真实授权数据下的 ALLOW/DENY（其自身行为由 P09 冻结测试覆盖）。
    登记 **F-P16-I-02（OPEN）**。
G-3 ToolGate 未在本轮 runtime 路径中直接调用：runtime 通过 agent grant + tool 状态 + approval +
    幂等 + timeout 自证其前置条件，`ToolGate.authorize()` 的完整组合（含 scope 语义）由
    services/authorization 自身与其冻结测试承担。若 ACCEPTANCE GATE 要求在 runtime 内联调用
    ToolGate，需要一次显式调整（登记 **F-P16-I-03（OPEN）**）。
G-4 文档合并：契约 §38 列出 10 份证据文档，本轮实际交付
    P16_HUMAN_DECISION_FREEZE / P16_IMPLEMENTATION_REPORT / P16_RUNTIME_PRIVILEGE_MATRIX
    + 契约 + 决策包（PREP 阶段）。未单独创建 provider/routing/agent-run/tool-execution/test
    acceptance 报告与 P16_RELEASE_PREP：前者内容已并入本报告 §2/§3，后者属 Release Preparation
    Gate 范围（本阶段明确不授权 release），如需拆分请在 ACCEPTANCE GATE 指示。
```

## 6. Git / Release 状态

```text
HEAD = 1bc60834415cb4f518cd695c93cd79bec986228e（未 commit 本轮变更）
origin/main = 同值 · real staged = 0 · tags = 13（未创建新 tag）
working tree = 本轮新增/修改文件 + 既有 historical dirty / F-RP-02 / BATCH-D 全部保留
未执行任何 push / release / P17
```

**END OF P16 IMPLEMENTATION REPORT（P16 IMPLEMENTATION = 已实施；ACCEPTANCE 未完成；RELEASE 未授权）**
