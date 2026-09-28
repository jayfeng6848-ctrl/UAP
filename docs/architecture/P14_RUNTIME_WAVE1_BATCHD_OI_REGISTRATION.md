# UAP — P14 RUNTIME WAVE1 BATCH-D OI REGISTRATION

> ## 状态
>
> ```text
> 轮次      = P14 WAVE 1 INCIDENT RECOVERY + TEST SCOPE REMEDIATION（§十七 / §十八）
> 性质      = 登记（REGISTER ONLY）——**本轮不修复**
> 依据      = HD-P14-REC-02（stale head OI）· HD-P14-REC-03（新测试载体双归属）
> ID 选取    = 扫描现行 OI 台账后取**下一个未占用编号**（不猜）
> ```

---

# 1. ID 选取依据（§十七 "不要猜新的 OI ID"）

```text
扫描面 = docs/** 全量 `OI-*` 引用
已占用编号（实测）：
  OI-B-1…6 · OI-BB-1…8 · OI-BB-11/13/14 · OI-DC-1…2 · OI-G-1…8
  （另：CF-C-1…7 · P0-ENV 为不同类别前缀）
现行最大 = **OI-G-8**（OPEN_P10_1_BATCH_A_EXECUTION_REPORT.md §尾）
⇒ 下一个合法、未占用编号 = **OI-G-9**（沿用 OI-G-* 通例族）
```

---

# 2. OI-G-9 — Stale Head Assertion（BATCH-D test governance）

```text
ID                     = OI-G-9
Title                  = Stale migration-head assertions in test carriers
Classification         = BATCH-D / maintenance / stale-head test-governance
Status                 = REGISTERED / UNFIXED
Owner stage            = BATCH-D

Observed stale assertion (Active · reachable)
  file                 = tests/security/test_authorization_security.py:158
  code                 = assert current_revision() == "0015_p12_indexes"

Observed stale assertions (Latent · gated by CF-C-4 NOT RUN)
  files（16 个 integration 载体 · 行号见 TEST EXECUTION MANIFEST §6）
    test_migration_lock.py · test_tool_registry_schema.py · test_tenant_space_schema.py ·
    test_alembic_smoke.py · test_agent_tool_permission_schema.py · test_rbac_hardening.py ·
    test_ai_gateway_schema.py（HEAD_REVISION 常量）· test_authorization_service.py ·
    test_platform_timestamp_precision.py（CURRENT_HEAD 常量）· test_rbac_schema.py ·
    test_resource_acl_schema.py · test_identity_schema.py ·
    test_p10_event_audit_schema.py（HEAD_REVISION 常量）· test_p11_triggers.py

Expected canonical head  = 0017_p13_seed
Current bad expectation  = 0015_p12_indexes
Failure mode
  · fixture 先 reset_test_database()，再断言 head；断言必然失败
  · 结果是 "setup ERROR + 数据库已被重建" —— 错误发生在**破坏性副作用之后**
Impact
  · 2026-09-28 事故：uap_b1_test 被 DROP/CREATE；SECURITY EVIDENCE FREEZE 库内基线丢失
    （已按 HD-P14-REC-01 恢复，见 INCIDENT RECOVERY REPORT）
  · 该失效面**不是** P14 Runtime 缺陷；属测试治理缺陷
Recommended fix（BATCH-D 执行 · 本轮不做）
  1. 全部 stale head 断言改为**从 migration chain 推导**（single-head derive）而非硬编码；
  2. 断言位置移到破坏性 fixture 之后（先验证，再破坏）；
  3. 破坏性 fixture 增加 "已授权执行上下文" 断言（未授权 ⇒ 立即 skip/fail-fast）。
Related（不重复登记）
  tests/unit/test_generate_build_info.py:23（REV = "0015_p12_indexes"）⇒ 既有 **OI-G-4**
```

---

# 3. 新 P14 测试载体 — BATCH-D 治理登记（§十八）

> 双归属：**执行治理** → CF-C-4 / BATCH-D；**语义归属** → P14 Runtime。
> 本轮**不物理迁移**任何文件。

```text
file                                                | type              | destructive | allowed context            | forbidden context        | fixture dependency        | DB target      | current head assumption
----------------------------------------------------|-------------------|-------------|----------------------------|--------------------------|---------------------------|----------------|------------------------
tests/unit/test_runtime_error_taxonomy.py           | unit              | NO          | 任意                         | —                        | 无                        | 无             | 无
tests/unit/test_runtime_retry_boundary.py           | unit              | NO          | 任意                         | —                        | 无                        | 无             | 无
tests/unit/test_runtime_lifecycle_boundary.py       | unit              | NO          | 任意                         | —                        | 无（DB 边界被 monkeypatch） | 无             | 无
tests/integration/runtime_testkit.py                | test support      | NO          | 仅被 P14 测试 import          | 目录级 pytest            | 无                        | uap_b1_test    | 无
tests/integration/test_runtime_db_wave1.py          | integration       | NO（全回滚）  | 显式 allowlist + DSN 注入     | 目录级 pytest            | 无（不 import testkit）     | uap_b1_test    | 不硬编码 head
tests/integration/test_runtime_security_regression_wave1.py | security regression | NO（全回滚） | 显式 allowlist + DSN 注入 | 目录级 pytest       | 无                        | uap_b1_test    | 不硬编码 head
```

```text
BATCH-D 义务（承接自 HD-P14-REC-03）
  allowlist / denylist 维护 · 执行范围 · stale test 清理 · head 断言一致性 ·
  fixture 安全 · 破坏性 fixture 治理

P14 保留义务
  Runtime 行为 · DB 连接行为 · 持久化行为 · Runtime 安全边界断言 · P14 验收映射

⇒ 新载体**不因进入 BATCH-D 治理而离开 P14 语义归属**
```

---

# 4. DESTRUCTIVE FIXTURE 登记（§十四）

```text
fixture #1  tests.integration.alembic_testkit.reset_test_database()
  behavior    = DROP DATABASE IF EXISTS "uap_b1_test" WITH (FORCE) → CREATE DATABASE
  target DB   = uap_b1_test
  allowed     = CF-C-4 决议（BATCH-D）授权后的隔离执行
  forbidden   = 任何 allowlist 之外的执行；任何目录级 pytest 递归
  recovery    = TEST EXECUTION MANIFEST §5（migration window + exact grant replay）

fixture #2  tests.security.test_authorization_security.env
  behavior    = 调 #1（setup）→ 断言 head（陈旧）→ 调 #1（teardown）
  status      = DESTRUCTIVE + STALE（本 OI-G-9 的 Active 面）
  disposition = 本轮不修改（REGISTER ONLY）

autouse 复核    = 未发现 `autouse=True` 的破坏性 fixture；风险来自**目录级 pytest 参数**
                  （等价于隐式全局触发）⇒ 已用逐文件 allowlist 阻断
```

---

# 5. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 3 份）
测试代码修改 = 0（未修改任何既有测试文件；仅新增 P14 载体）
正式库 uap 变更 = 0 · migration 变更 = 0 · commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE1 BATCH-D OI REGISTRATION（2026-09-28 · OI-G-9 REGISTERED/UNFIXED · 新载体双归属登记 · HARD STOP ACTIVE）**
