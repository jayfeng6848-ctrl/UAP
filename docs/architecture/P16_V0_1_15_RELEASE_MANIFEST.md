# P16 V0.1.15 RELEASE MANIFEST

```text
release_version = 0.1.15
release_tag     = UAP-V0.1.15-P16-AGENT-RUNTIME
base_commit     = 1bc60834415cb4f518cd695c93cd79bec986228e   （0.1.14）
candidate_commit= <由 commit 阶段生成后回填>
migration_head  = 0018_p16_agent_runtime   （单一 head · 0017 → 0018 连续）
hash_basis      = committed Git blob bytes（F-RP-06 冻结规则；禁止工作区渲染）
```

## 1. Release notes（P16 = AI / Agent Runtime Activation）

```text
主要新增：
  · request-scoped synchronous Agent Run（CREATED → RUNNING → WAITING_TOOL → COMPLETED/FAILED/CANCELLED）
  · persisted agent_runs 执行台账（唯一新表）+ run correlation（agent_runs / ai_request_logs /
    tool_executions / audit_logs 共用 run_id）
  · AI routing / policy / provider / model 链（确定性 priority · classification/privacy 约束 ·
    显式 fallback）
  · canonical ToolGate 授权（runtime → ToolAuthorizationFacade → ToolGate，单一授权路径）
  · tool execution 集成（published tool version · trusted handler registry · timeout · 幂等）
  · credential secret resolver 边界（env: 引用 · Agent/Tool/Worker 均不可见明文）
  · failure durability（T1 admission 提交 + 失败终态独立提交 + 审计隔离）
  · actor / agent 授权分离（Actor ∧ Agent；DENY>ALLOW；无权限继承捷径）
  · tenant-scoped tool lookup（跨租户工具解析缺陷修复）
  · least privilege（uap_runtime 仅新增 ai_*/tool_*/agent_runs 面的最小 grant）

明确未激活（冻结边界）：
  · Production Event Allowlist = EMPTY
  · Production Handlers = 0
  · 无 dedup table · 无 agent_run_steps · 无 provider 自动重试 · 无 tool 直调 API
  ⇒ 本次发布不包含“事件驱动 Agent Runtime 全面上线”的能力
```

## 2. File allowlist（P16 release payload）

### 2.1 P16 newly added（41）

| 分类 | 路径 |
|---|---|
| schema | `migrations_alembic/versions/0018_p16_agent_runtime.py` |
| contract | `core/agent/__init__.py` · `core/agent/run.py` · `core/agent/errors.py` · `core/ai/__init__.py` · `core/ai/routing.py` |
| services | `services/ai/__init__.py` · `services/ai/credentials.py` · `services/ai/routing.py` · `services/ai/gateway.py` · `services/agent/__init__.py` · `services/agent/tools.py` · `services/agent/repository.py` · `services/agent/runtime.py` · `services/agent/authorizer.py` · `services/agent/tool_authorization.py` · `services/agent/use_cases.py` |
| infrastructure | `infrastructure/ai/__init__.py` · `infrastructure/ai/adapters.py` |
| api | `apps/api/routes/agent_runs.py` |
| tooling | `scripts/privileges.py`（P16-D15 基线权限物化机制） |
| tests | `tests/unit/test_p16_routing.py` · `tests/unit/test_p16_credentials.py` · `tests/unit/test_p16_run_contract.py` · `tests/unit/test_p16_tools.py` · `tests/architecture/test_p16_boundaries.py` · `tests/architecture/test_p16_single_authorization_path.py` · `tests/security/test_p16_secret_boundary.py` · `tests/integration/test_p16_agent_run.py` · `tests/integration/test_p16_run_durability.py` |
| evidence | `docs/architecture/P16_PREPARATION.md` · `P16_AI_AGENT_RUNTIME_ARCHITECTURE_ANALYSIS.md` · `P16_SECURITY_BOUNDARY_ANALYSIS.md` · `P16_DECISION_MATRIX.md` · `P16_ACCEPTANCE_DRAFT.md` · `P16_DEPENDENCY_IMPACT.md` · `P16_HUMAN_DECISION_FREEZE.md` · `P16_AI_AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md` · `P16_RUNTIME_PRIVILEGE_MATRIX.md` · `P16_IMPLEMENTATION_REPORT.md` · `P16_ACCEPTANCE_GAP_CLOSURE_REPORT.md` · `P16_R1_R2_R3_EVIDENCE.md` |

### 2.2 P16 modified（3）

```text
apps/api/main.py                             路由注册（agent-runs）
services/authorization/tools.py              ToolGate.authorize 增补式 agent_id 参数
docs/architecture/PLATFORM_DECISION_LOG.md   附录 V（P16 freeze + governance reconciliation · append-only）
```

### 2.3 Version metadata（3）

```text
pyproject.toml · config/settings.py · docker-compose.yml   0.1.14 → 0.1.15
```

### 2.4 Explicitly EXCLUDED（historical dirty · 未纳入）

```text
tracked modified（25）：docs/api/README.md · docs/architecture/ARCHITECTURE.md · CORE_DOMAIN_MODEL.md ·
  DEPENDENCY_RULES.md · STEP1B_*（5）· docs/security/README.md · infrastructure/database/__init__.py ·
  tests/conftest.py · tests/integration/*（14）· tests/security/test_authorization_security.py ·
  tests/unit/test_generate_build_info.py
untracked historical（104）：AGENT_RUNTIME_*（4 · 已 obsolete）· OPEN_P10_1_*（30）· P13/P14_*（29）·
  handoff（17）· P10/P11/P12/P0/RUNTIME_DOCUMENT_SET 等 · __pycache__
⇒ 这些文件保留在工作区，但不进入 release commit
```

## 3. Test commands 与结果（release candidate 复验）

```text
P16 unit/architecture/security = python -m pytest -q <7 个 P16 文件>            → 33 passed / 0 failed
P16 integration                = python -m pytest -q tests/integration/test_p16_agent_run.py
                                                                              → 6 passed / 0 failed
R-1 durability                 = python -m pytest -q tests/integration/test_p16_run_durability.py
                                                                              → 2 passed / 0 failed
P15 allowlist                  = python -m pytest -q <4 个 P15 文件>            → 65 passed / 0 failed
architecture guards            = python -m pytest -q <4 个既有守卫>             → 37 passed / 0 failed
forbidden tests = 0 · OI-G-4 = 0 · 目录级 pytest = 0
```

## 4. Security / DB / 边界

```text
security fingerprint = 51（P14 baseline）+ 5（202610 分区：events_202610 3 + audit_logs_202610 2）
                     = uap_runtime 56 · uap_app 5 · roles 6 · default ACL 0
unexpected privilege expansion = 0 · secret leakage = 0 · authorization bypass = 0
Production Event Allowlist = EMPTY · Production Handlers = 0
Core → Domain = 0
Formal DB uap = prestate == poststate（0 表 · 本轮只读）
Test DB：uap_p16_test 已删除（仅 uap / uap_b1_test / uap_test 保留）
fresh clone（tag 指向 commit）→ 迁移 + 官方基线物化 + 测试全部重跑 = 见 final record
```

**END OF P16 V0.1.15 RELEASE MANIFEST**
