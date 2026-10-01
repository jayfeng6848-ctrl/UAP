# P16 R-1 / R-2 / R-3 EVIDENCE

> 本轮证据（2026-10-01 · 工作区未提交）。历史文件 `P16_ACCEPTANCE_GAP_CLOSURE_REPORT.md`
> 描述的是上一轮状态，未回写；本文件是它的追加证据，遵循 observe → diagnose → correction → evidence。

## 1. R-2 — Provider path（两个根因已修复）

```text
诊断方法：沿 §12 链路定位“第一个真实失败点”，只记录异常类（不外泄消息）；
          之后通过 ToolGate decision_reason（安全码）继续定位授权层。

根因 #1  CHECKPOINT = adapter invocation          exception_class = NameError
  位置 = infrastructure/ai/adapters.py::EchoAdapter.build 内嵌 provider 引用未绑定的 `proposal`
  修正 = build() 内绑定 `proposal = self._proposal`
  为何 unit 绿 / integration 红 = unit 走 OpenAICompatibleAdapter；仅集成 ALLOW 用 EchoAdapter 的 tool 分支

根因 #2  CHECKPOINT = request logging             PG 23502 · NotNullViolation · ai_request_logs.id
  原因 = gateway 日志白名单不含 `id`，repository 以显式 NULL 写入 NOT NULL 列（默认值不生效）
  修正 = LOG_FIELDS 增加 `id`（沿用 correlation 的 UUIDv7）+ INSERT 用
         COALESCE(CAST(:id AS uuid), uap_uuid_v7()) 兜底

根因 #3  CHECKPOINT = tool lookup                 exception/decision = TENANT_SCOPE_DENIED
  原因 = AgentRuntimeRepository.get_tool_by_key 只按 key 查询、无 tenant 谓词；
         多租户数据下会取到其他租户的 tool 行，被 canonical ToolGate 判为 cross-tenant
  修正 = 查询改为 tenant 作用域（`tenant_id IS NULL OR tenant_id = :tenant`，平台工具优先）
         —— 这同时是一个真实的租户隔离缺陷修复（F-P16-I-07）

根因 #4  CHECKPOINT = audit write（成功路径）      PG 23502 · NotNullViolation · audit_logs.created_at
  原因 = services/agent/repository.insert_audit 未提供 created_at（该列无默认值）
  修正 = INSERT 增加 `created_at = now()`

最终：full-chain ALLOW = COMPLETED，AI request → tool proposal → ToolGate ALLOW → tool execution 全链真实通过
       provider transport failure 对照场景保持 FAILED + MODEL_REQUEST_FAILED（未被“改绿”）
```

## 2. R-3 — Tool disabled（已按真实原因闭合）

```text
观察：ToolGate 先返回 TENANT_SCOPE_DENIED（根因 #3）→ 修 tenant 作用域后，
      同一场景 ToolGate 第一拒绝原因为 tool disabled。
传播链：ToolGate Decision(effect=DENY, reason="tool-disabled")
        → ToolAuthorizationFacade（_REASONS 映射，未新增第二套 taxonomy）
        → AgentRuntimeError(TOOL_DISABLED)
        → agent_runs.failure_code = TOOL_DISABLED
证据：ledger 行 = FAILED | TOOL_DISABLED，且 tool_executions = 0（执行前拒绝）
附带：decision_reason 仅持久化“稳定机器码”（如 TOOL_DISABLED / TENANT_SCOPE_DENIED /
      AUTHORIZATION_UNAVAILABLE），已去除原始消息与 SQL 文本（§6 安全要求）
```

## 3. R-1 — Run 失败终态持久化（行为已证明）

```text
transaction model：
  T1 Run Admission（独立事务提交）→ agent_runs.status=CREATED 立即持久
  T2 Execution（状态变更各自事务）→ RUNNING → COMPLETED / FAILED
  _fail = 事务 A（mark_run_failed，WHERE status IN (CREATED/RUNNING/WAITING_TOOL)，
         rowcount 必须为 1，否则 _note_missing_transition 记 INTERNAL_RUNTIME_ERROR 证据）
        + 事务 B（审计 append，独立事务；失败只 warning，不回滚 FAILED）

真实 DB 证据（fresh 隔离库 uap_p16_test · 官方基线物化 · 6 场景）：
  COMPLETED | -                        | tool_calls=1 | ×1
  FAILED    | AUTHORIZATION_DENIED     | ×1
  FAILED    | CREDENTIAL_UNAVAILABLE   | ×1
  FAILED    | MODEL_REQUEST_FAILED     | ×1
  FAILED    | TOOL_DISABLED            | ×1
  （cross-tenant 场景在 admission 前被拒 → 按冻结语义不产生 run 行）
  correlation：ai_request_logs.run_id=1 · tool_executions.run_id=1（succeeded=1）·
               audit_logs correlation=5
  ⇒ 修复前“执行过但库里什么都没有”的情况已消除；失败运行是 durable fact

未完成（因此 R-1 未按 §10 完全闭合）：
  · 未编写 test_failure_audit_does_not_rollback_failed_state（审计注入失败测试）
  · 未编写 test_mark_run_failed_rowcount_one（rowcount 专项测试与 rowcount=0 证据测试）
```

## 4. 回归与边界

```text
P16 unit + architecture + security = 33 passed / 0 failed
P16 integration（6 场景）          = 6 passed / 0 failed
P15 allowlist（4 文件）            = 65 passed / 0 failed
既有架构守卫（4 文件）              = 37 passed / 0 failed
Forbidden tests = 0 · OI-G-4 = 0

F-P16-I-06（新登记 · 已定性）= 月份分区漂移
  P15 首轮回归出现 11 failed；根因不是 P16 代码，而是测试库只有 202609 分区，
  当天已是 2026-10（events/audit_logs 为月分区，D-B16-05/D-3 手工运维）。
  按冻结的 D-3 运维在 uap_b1_test 建立 events_202610 / audit_logs_202610（并授予与基线一致的
  uap_runtime 权限）后，P15 恢复 65/0 ⇒ 环境漂移，非回归。
  uap_runtime grant 计数因此从 51 → 56（51 基线 + 新分区 3+2）；这是分区而非新权限面。

Formal DB uap = 0 表（prestate == poststate）· 临时隔离库 uap_p16_test 已删除
HEAD = 1bc60834415cb4f518cd695c93cd79bec986228e · staged = 0 · tags = 13 · 未 commit/tag/push
```

**END OF P16 R-1 / R-2 / R-3 EVIDENCE**

---

## 5. R-1 §19 final evidence — audit failure does not roll back FAILED

```text
test   = tests/integration/test_p16_run_durability.py::test_failure_audit_does_not_rollback_failed_state
result = PASS（2 passed in 6.43s 的两个专项测试之一）

方法（真实路径 + 受控注入）：
  fresh 隔离库（uap_p16_test · 0018 · scripts.privileges.materialize · 真实 seed）
  → runtime.run()（真实 admission T1 + 真实执行失败：provider 无凭据）
  → monkeypatch services.agent.repository.AgentRuntimeRepository.insert_audit
    （canonical audit write boundary）抛出 RuntimeError("injected audit append failure")
  → 断言注入确实发生（calls["injected"] ≥ 1），不是“没有异常”当 pass

独立连接证据（fixture engine，与 runtime 连接分离）：
  status = FAILED · failure_code = CREDENTIAL_UNAVAILABLE · metadata 含稳定机器码
  ⇒ audit append 失败未回滚 agent_runs 终态（此前该路径会整体回滚）

run_id 与 status before/after：admission 后为 CREATED/RUNNING（已提交），
  audit 注入失败之后仍为 FAILED（终态），row 始终存在。
```

## 6. R-1 §21 final evidence — rowcount = 1 / rowcount = 0

```text
test   = tests/integration/test_p16_run_durability.py::test_mark_run_failed_rowcount_one
result = PASS

rowcount = 1：真实 run（T1 已提交）执行失败 → mark_run_failed() 命中该行
  → 独立连接确认 status=FAILED · failure_code=CREDENTIAL_UNAVAILABLE
rowcount = 0：使用真实不存在的 run_id（uuid4），DB 自然返回 0 行
  → 返回 False（未静默接受）· repository 层与应用层（_fail）均返回 False
  → 该 run_id 在 agent_runs 中确实不存在（count = 0）
corresponding run existence state：存在（rowcount=1 场景）/ 不存在（rowcount=0 场景）
final DB state：无伪造成败行，失败终态均为 FAILED + canonical failure_code
```

## 7. FINAL STATE（本轮末）

```text
P16 integration（6 场景）        = 6 passed / 0 failed
P16 unit + architecture + security = 33 passed / 0 failed
P15 allowlist（4 文件）          = 65 passed / 0 failed
existing architecture guards      = 37 passed / 0 failed
Forbidden tests = 0 · OI-G-4 = 0 · Production Allowlist = EMPTY · Handlers = 0
Core → Domain = 0 · Formal DB uap = 0 表（prestate == poststate）
临时隔离库 uap_p16_test 已删除（仅 uap / uap_b1_test / uap_test）
uap_b1_test = 0017_p13_seed · runtime grants 56 = 51 基线 + 5（202610 分区 events 3 + audit 2）
              roles 6 · DELETE 3（memberships/sessions/tenant_memberships，均属基线）
HEAD = 1bc6083 · staged = 0 · tags = 13 · commit/tag/push = NO
```

**END OF APPENDED EVIDENCE（R-1 CLOSED）**
