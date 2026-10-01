# P16 ACCEPTANCE GAP CLOSURE REPORT

## 0. 结论

```text
F-P16-I-03 = CLOSED
F-P16-I-01 = OPEN（根因已定位 → 新登记 F-P16-I-04）
F-P16-I-02 = OPEN（依赖 I-01）

P16 ACCEPTANCE = NOT PASSED
```

```text
本轮未 commit / 未 tag / 未 push（HEAD = 1bc6083 · staged = 0）
```

## 1. F-P16-I-03 — Single canonical authorization path（CLOSED）

### Before（问题）

```text
services/agent/runtime.py 自行判断：tool 存在 / enabled / agent grant(effect) /
approval_required / idempotency —— 与 ToolGate 的组合判定重复（duplicate authorization logic）。
```

### Correction（本轮修正）

```text
1. services/authorization/tools.py::ToolGate.authorize(..., agent_id=None)
   —— 增补式参数（默认 None · 既有调用者行为不变）：当调用方声明 agent 时，
      额外要求 agent_permissions 对该 tool 的 allow（deny 优先 · 无 grant 即 DENY）。
2. 新增 services/agent/tool_authorization.py::ToolAuthorizationFacade
   —— 薄委托：只做 ToolGate 调用 + Decision→冻结错误码映射，不实现任何授权算法。
3. runtime 收敛职责：
   保留 load context/version、route、model 调用、proposal 解析、执行层（version 选择、
   handler dispatch、幂等执行语义、timeout、ledger、错误映射）；
   删除自身 tool/enabled/grant/approval 判定，改为单一调用
   `self._tool_auth.authorize(...)`（缺失即 fail-closed）。
```

### 最终授权路径

```text
Agent Runtime → ToolAuthorizationFacade → ToolGate → (ToolGate 组合判定) → ALLOW / DENY
```

### Architecture guard（新增）

```text
tests/architecture/test_p16_single_authorization_path.py（4 项）
  · runtime 必须依赖 facade 且调用 self._tool_auth.authorize(...)
  · runtime 不得包含 approval_required / tool_grants / resource_permissions / permissions.tool / effect
  · runtime 不得 import services.authorization，也不得出现 opaque 字段名
  · use_cases 必须接线 ToolAuthorizationFacade.from_engine + P09ActorAuthorizer.from_engine
实测 = 4 passed
```

## 2. F-P16-I-01 / I-02 — 已建立真实 DB 集成测试，但被新根因阻塞

### 已交付（真实 DB · 非 mock）

```text
tests/integration/test_p16_agent_run.py（新建 · 6 场景）
  · 专用数据库 uap_p16_test（fixture 内 CREATE + alembic upgrade head → 0018）——
    不触碰冻结的 uap_b1_test（保持 0017）
  · fixture 全部为真实行：tenants · users · resources · resource_permissions(ACL) ·
    agents · agent_versions(published) · tools · tool_versions(published) ·
    agent_permissions · ai_providers · ai_models · ai_routes · ai_policies
  · 场景：full-chain ALLOW（agent_runs + ai_request_logs + tool_executions + audit delta +
    run_id correlation）· ACL deny · cross-tenant · tool disabled · missing credential ·
    provider transport failure
  · 仅 provider transport 被 stub（契约 §12 允许）；DB/授权/台账均为真实数据
```

### 阻塞根因（新登记 F-P16-I-04）

```text
F-P16-I-04（BLOCKING for I-01/I-02）
Classification = PRE-EXISTING ENVIRONMENT/REPRODUCIBILITY DEFECT（非 P16 代码缺陷）
Evidence       = 在 fresh-migrated 数据库上以 uap_runtime 访问失败：
                 psycopg.errors.InsufficientPrivilege: permission denied for table agents
原因           = P14 基线 grant（agents/agent_versions/agent_permissions/tools/users/resources/
                 resource_permissions/... 的 SELECT · users/identities/... 的 INSERT/UPDATE ·
                 events/audit_logs 的 INSERT/SELECT 及其分区）**不在 migration 内**，
                 是对既有数据库（uap_b1_test / uap）单独施加的结果；
                 0018 只授予 P16 新增面（ai_*/tool_versions/tool_permissions/tool_executions/agent_runs）。
⇒ 任何“fresh DB + alembic upgrade head”的 P16 集成测试都会在第一步被拒绝；
   而既有集成套件之所以能跑，是因为它使用已经被基线授权过的 uap_b1_test。
需要的决定     = 是否允许（a）在 P16 测试 fixture 中复制 P14 基线 grant（仅测试库），
                 或（b）为 fresh DB 提供可复现的基线授权步骤（基础设施变更 · 独立 Gate），
                 或（c）将 P16 集成测试改为运行在已授权的 uap_b1_test 上（需评估对冻结基线的影响）。
当前处置       = 不猜测、不复制授权、不改 P14 面 ⇒ 本轮停在报告点。
```

## 3. 其他验证（本轮实测）

```text
P16 unit + architecture + security（含 I-03 guard）= 33 passed / 0 failed
  （routing 7 · credentials 4 · run 5 · tools 5 · architecture 9 · security 4 —— 含负路径）
P16 集成测试 fixture 建设 = 完成（真实行 · 6 场景主体已写完）
P16 集成测试执行          = BLOCKED at uap_runtime baseline privileges（见 §2）
未修改：tests/conftest.py · infrastructure/database/__init__.py（F-RP-02 保持 PARTIALLY RESOLVED）
未修改：0013–0017 · P13/P14/P15 语义 · production allowlist 保持 EMPTY · handlers 0
Formal DB uap = 未触碰；uap_b1_test 保持 0017_p13_seed（未被本轮改动）
```

## 4. 本轮变更文件（工作区 · 未提交）

```text
services/authorization/tools.py        ToolGate.authorize 增补 agent_id + _agent_permission
services/agent/tool_authorization.py   ToolAuthorizationFacade（新）
services/agent/runtime.py              移除重复授权判定 · 单一 facade 调用 · 失败类名诊断（不含消息）
services/agent/use_cases.py            接线 facade
infrastructure/ai/adapters.py          EchoAdapter 支持 proposal（测试注入 tool 提案）
tests/architecture/test_p16_single_authorization_path.py（新）
tests/integration/test_p16_agent_run.py（新）
```

**END OF P16 ACCEPTANCE GAP CLOSURE REPORT（I-03 CLOSED · I-01/I-02 OPEN · F-P16-I-04 新登记 · ACCEPTANCE NOT PASSED）**
