# UAP — P14 RUNTIME WAVE1 TEST EXECUTION MANIFEST

> ## 状态
>
> ```text
> 轮次      = P14 WAVE 1 INCIDENT RECOVERY + TEST SCOPE REMEDIATION（§十一–§十五）
> 性质      = 测试执行治理载体（explicit allowlist / denylist / destructive fixture governance）
> 依据      = HD-P14-REC-03（双归属：execution governance → CF-C-4 / BATCH-D；
>             semantic ownership → P14 Runtime）
> 铁律      = 只允许**逐文件**显式 allowlist；禁止 `pytest` / `pytest tests/` /
>             `pytest tests/security/` / `pytest tests/integration/` 这类目录级递归执行
> ```

---

# 1. 事故根因（本清单为何存在）

```text
2026-09-28：Agent 以 `pytest tests/unit tests/architecture tests/security tests/contract`
运行，目录级递归把 tests/security/test_authorization_security.py（CF-C-4 禁跑文件）
纳入执行；其 fixture 先 reset_test_database() 再断言陈旧 head ⇒ 26 errors 且
uap_b1_test 被 DROP/CREATE。

⇒ 治理修复 = 用**逐文件 allowlist** 取代目录级执行；任何未列明文件一律 NOT RUN。
```

---

# 2. P14 WAVE1 ALLOWED TEST SET（逐文件 · 不允许只写目录）

## 2.1 Runtime Unit

```text
tests/unit/test_runtime_error_taxonomy.py
tests/unit/test_runtime_retry_boundary.py
tests/unit/test_runtime_lifecycle_boundary.py
```

## 2.2 Runtime Architecture

```text
tests/architecture/test_dependency_rules.py
tests/architecture/test_p10_event_audit_boundary.py
tests/architecture/test_agent_resource_scope_opaque.py
```

## 2.3 Runtime Contract

```text
tests/contract/test_health_contract.py
tests/contract/test_authorization_contract.py
```

## 2.4 Runtime Integration

```text
tests/integration/test_runtime_db_wave1.py
```

## 2.5 Runtime Security

```text
tests/integration/test_runtime_security_regression_wave1.py
tests/security/test_no_secrets.py
```

## 2.6 P14 Acceptance subset（既有基线面 · 非 destructive）

```text
tests/unit/test_project_boot.py
tests/unit/test_config.py
tests/unit/test_logging.py
tests/unit/test_build_info.py
tests/unit/test_migration_runner.py
tests/unit/test_migration_state_probe.py
```

```text
测试支撑模块（非测试用例 · 不单独执行，仅被 import）：
  tests/integration/runtime_testkit.py      （P14 新增 · env 注入 runtime DSN）
  tests/integration/alembic_testkit.py      （既有 · 含 reset_test_database 定义 ⇒ 属 DENY 面文件，
                                              但仍被 17 个 integration 测试 import，见 §3）
```

---

# 3. P14 WAVE1 DENY TEST SET（NOT RUN）

## 3.1 CF-C-4 禁跑集合（19 条 · 含 `reset_test_database()`）

```text
tests/security/test_authorization_security.py          ← 事故触发文件
tests/integration/alembic_testkit.py                   （工具模块，定义 reset_test_database）
tests/integration/test_agent_tool_permission_schema.py
tests/integration/test_ai_gateway_schema.py
tests/integration/test_alembic_smoke.py
tests/integration/test_authorization_service.py
tests/integration/test_authz_enforcement_migration.py
tests/integration/test_identity_schema.py
tests/integration/test_migration_failure.py
tests/integration/test_migration_lock.py
tests/integration/test_p10_event_audit_schema.py
tests/integration/test_p11_triggers.py
tests/integration/test_p12_indexes.py
tests/integration/test_platform_timestamp_precision.py
tests/integration/test_rbac_hardening.py
tests/integration/test_rbac_schema.py
tests/integration/test_resource_acl_schema.py
tests/integration/test_tenant_space_schema.py
tests/integration/test_tool_registry_schema.py
```

```text
⇒ 禁止通过以下任一方式被间接执行：
   directory discovery · pytest recursion · import side effect · fixture reuse
⇒ 禁止把上述文件所在**目录**作为 pytest 参数（目录级参数会连带执行它们）
```

## 3.2 其他禁跑项

```text
tests/unit/test_generate_build_info.py      ← OI-G-4（既有 REGISTERED / UNFIXED；
                                              与本事故无关，本轮不修）
```

---

# 4. Destructive Fixture Governance（§十四 / §十五）

```text
DESTRUCTIVE FIXTURE #1
  名称        = tests.integration.alembic_testkit.reset_test_database()
  行为        = DROP DATABASE IF EXISTS "uap_b1_test" WITH (FORCE) → CREATE DATABASE
  目标 DB     = uap_b1_test（唯一）· 管理 DSN 指向 postgres 库，身份 uap
  影响        = 摧毁 uap_b1_test 的全部 schema / ownership / grants 状态
  allowed     = 仅在 CF-C-4 决议（BATCH-D）授权后的隔离执行环境
  forbidden   = 任何 allowlist 之外的执行；任何目录级 pytest 调用
  调用条件     = 显式 fixture 请求（无 autouse）；但 setup 阶段即在断言之前触发
  恢复规程     = 见 §5（migration window + exact grant replay）

DESTRUCTIVE FIXTURE #2（同源）
  名称        = tests.security.test_authorization_security.env（fixture）
  行为        = 调 #1（setup）+ 调 #1（teardown）· 并在两者之间断言 head == 0015_p12_indexes
  当前状态     = STALE（现行 head = 0017_p13_seed）⇒ 必然 setup ERROR，且库已被重建
  处置        = 本轮仅登记 OI-G-9（§6）；**不修改该 fixture**

autouse 评估（§十五）
  实测        = reset_test_database() 无 autouse 传播；但**目录级 pytest 参数**
                等价于隐式全局触发 ⇒ 已由 §2/§3 的逐文件 allowlist 阻断
  范围控制     = 本轮不重构 fixture 框架（避免扩大改动面）；框架级整改 → BATCH-D（OI-G-9 关联项）
```

---

# 5. 恢复规程（本次事故已执行 · 供 BATCH-D 复用）

```text
1. GRANT CREATE ON SCHEMA public TO uap_migrator        （CF-C-5=B 窗口期开启）
2. UAP_MIGRATION_DATABASE_URL=<uap_migrator DSN>  python -m alembic -c alembic.ini upgrade head
3. REVOKE CREATE ON SCHEMA public FROM uap_migrator      （窗口期关闭 · 回到基线）
4. GRANT USAGE ON SCHEMA public TO uap_app / uap_runtime / uap_bootstrap
5. 重放 exact grants：uap_app 5 · uap_runtime 51（26 S/12 I/10 U/3 D）· uap_bootstrap 6
6. 逐向校验：信息模式集合相等（无缺、无多）· nspacl · default_acl=0 · 归属残留=0 ·
   memberships=0 · C2 md5=185e95be8bc4304edbcd3f4d5cda1eff · registry/permissions/role_permissions=3/12/12
⇒ 全程 identity：迁移 = uap_migrator；GRANT = uap（schema owner）；runtime 测试 = uap_runtime
⇒ 正式库 uap 不参与任何步骤
```

---

# 6. Stale Head Assertion 分类（§十六）与 OI 登记（§十七）

```text
扫描面 = 全仓 `0015_p12_indexes`（rg）

Active wrong assertion（可达且错误）
  tests/security/test_authorization_security.py:158            ⇒ OI-G-9（事故触发）

Latent stale assertion（同类错误，但文件属 CF-C-4 NOT RUN ⇒ 当前不可达）
  tests/integration/test_migration_lock.py:68/111/134
  tests/integration/test_tool_registry_schema.py:95/669/748
  tests/integration/test_tenant_space_schema.py:86
  tests/integration/test_alembic_smoke.py:53/179/186
  tests/integration/test_agent_tool_permission_schema.py:172/330/994/1032
  tests/integration/test_rbac_hardening.py:43
  tests/integration/test_ai_gateway_schema.py:70/872（HEAD_REVISION 常量）
  tests/integration/test_authorization_service.py:42
  tests/integration/test_platform_timestamp_precision.py:66（CURRENT_HEAD 常量）
  tests/integration/test_rbac_schema.py:47/288
  tests/integration/test_resource_acl_schema.py:106/238
  tests/integration/test_identity_schema.py:55/216/220
  tests/integration/test_p10_event_audit_schema.py:60（HEAD_REVISION 常量）
  tests/integration/test_p11_triggers.py:65/391/503
  ⇒ 同属 OI-G-9 范围（BATCH-D 统一对账），本轮不逐个登记为新 ID

Already registered（既有 OI · 不重复登记）
  tests/unit/test_generate_build_info.py:23（REV = "0015_p12_indexes"）⇒ OI-G-4

非缺陷（不登记）
  migrations_alembic/versions/0015_p12_indexes.py:29        （revision 定义 · 正确）
  migrations_alembic/versions/0016_open_p10_1_trust_boundary.py:41（down_revision 链 · 正确）
  docs/**                                                    （历史记录 / 时点快照 · 不得改写）
```

---

# 7. 本轮执行顺序（§十九）

```text
1 Architecture → 2 Contract → 3 Unit → 4 Runtime Integration
→ 5 Security allowed → 6 P14 acceptance subset

每组之间记录结果；任一组出现「非预期执行 DENY 文件」⇒ 立即 STOP。
```

---

# 8. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 3 份）
测试代码变更 = 0（本轮未修改任何既有测试文件）
migration / schema / grant（正式库）= 0 · commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE1 TEST EXECUTION MANIFEST（2026-09-28 · explicit allowlist 25 文件 · denylist 19+1 · destructive fixture 治理 · HARD STOP ACTIVE）**
