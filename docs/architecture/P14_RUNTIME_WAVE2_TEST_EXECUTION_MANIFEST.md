# UAP — P14 RUNTIME WAVE 2 TEST EXECUTION MANIFEST

> ## 状态
>
> ```text
> 状态      = ACTIVE（Wave 2 实施期测试执行治理）
> 依据      = 第 36 条指令（CF-C-4 explicit allowlist）· Wave 1 TEST_EXECUTION_MANIFEST
> 铁律      = 逐文件 allowlist；禁止 `pytest tests/` / `pytest <directory>`
> ```

---

# 1. WAVE 2 ALLOWED TEST SET（逐文件）

## 1.1 Wave 2 Runtime Unit（无 DB）

```text
tests/unit/test_wave2_vocabulary_mapping.py      Domain↔Persistence 显式映射（§四/§七/§八）
tests/unit/test_wave2_credentials.py             Argon2id / 无明文 / 单向 token（§八/§三十五）
tests/unit/test_wave2_error_mapping.py           8 类 taxonomy → HTTP（§三十三）
```

## 1.2 Wave 2 Runtime Security / Integration（DB = uap_b1_test · identity = uap_runtime）

```text
tests/integration/test_wave2_identity_security.py         §三十七（12 用例）
tests/integration/test_wave2_device_security.py           §三十八（13 用例）
tests/integration/test_wave2_session_security.py          §三十九（11 用例）
tests/integration/test_wave2_authorization_security.py    §四十（10 用例）
tests/integration/test_wave2_api_security.py              §四十一（6 用例）
```

## 1.3 Wave 1 Regression（§四十八 · 每层完成后重跑）

```text
tests/architecture/test_dependency_rules.py
tests/architecture/test_p10_event_audit_boundary.py
tests/architecture/test_agent_resource_scope_opaque.py
tests/contract/test_health_contract.py
tests/contract/test_authorization_contract.py
tests/unit/test_runtime_error_taxonomy.py
tests/unit/test_runtime_retry_boundary.py
tests/unit/test_runtime_lifecycle_boundary.py
tests/integration/test_runtime_db_wave1.py
tests/integration/test_runtime_security_regression_wave1.py
tests/security/test_no_secrets.py
tests/unit/test_project_boot.py
tests/unit/test_config.py
tests/unit/test_logging.py
tests/unit/test_build_info.py
tests/unit/test_migration_runner.py
tests/unit/test_migration_state_probe.py
```

---

# 2. 测试支撑（非用例 · 不被收集）

```text
tests/integration/wave2_testkit.py    runtime_data_scope / provision_tenant_space_membership
                                      / provision_active_user / enroll_device / run_sql
tests/integration/runtime_testkit.py  UAP_RUNTIME_TEST_DSN 解析（Wave 1）
tests/integration/alembic_testkit.py  BASE_DSN（fixture provisioning 专用 · 既有文件）
```

---

# 3. 每个套件的执行属性

```text
file                                              | group        | DB target   | fixture dependency                    | CF-C-4 | expected
--------------------------------------------------|--------------|-------------|---------------------------------------|--------|---------
unit/test_wave2_vocabulary_mapping.py             | unit         | none        | 无                                     | N/A    | pass
unit/test_wave2_credentials.py                    | unit         | none        | argon2-cffi                           | N/A    | pass
unit/test_wave2_error_mapping.py                  | unit         | none        | 无                                     | N/A    | pass
integration/test_wave2_identity_security.py       | security     | uap_b1_test | runtime_data_scope（清理 users 级联）    | OK     | pass
integration/test_wave2_device_security.py         | security     | uap_b1_test | runtime_data_scope                    | OK     | pass
integration/test_wave2_session_security.py        | security     | uap_b1_test | runtime_data_scope                    | OK     | pass
integration/test_wave2_authorization_security.py  | security     | uap_b1_test | **provision_tenant_space_membership** | OK     | pass
integration/test_wave2_api_security.py            | security/api | uap_b1_test | runtime_data_scope + provisioning      | OK     | pass
```

```text
身份规则
  · 行为断言一律经 UAP_RUNTIME_TEST_DSN（role = uap_runtime）—— 缺省即 SKIP，不回退
  · fixture provisioning（tenants/spaces/roles）由 alembic_testkit.BASE_DSN 执行；
    uap_runtime 对这三张表只有 SELECT（SEC-05），无法自建模板数据
  · provisioning 与 cleanup 均为净零（测试结束 tenants=0 / spaces=0 / roles=1）
```

---

# 4. EXPECTED TEST DATA（§三十二 / §五十五）

```text
audit_logs = **append-only**（tg_audit_immutable · D-P10-11）：连 fixture 身份也无法 DELETE。
⇒ Wave 2 安全套件产生的审计行是**永久且预期**的：
   本轮结束实测 audit_logs = 926 行（其余数据表均已回到基线 0）
⇒ 这是 **EXPECTED TEST DATA**，不是意外写入；边界锚点（roles/grants/ownership/
   default_acl/C2/P13 seed/schema/alembic）**全部未变**（见 Wave 2 报告 §11）

其余测试数据（users/identities/credentials/devices/sessions + 成员关系与角色模板）
由 runtime_data_scope / provisioning cleanup 删除，回到基线。
```

---

# 5. DENY（NOT RUN）

```text
CF-C-4 禁跑集合（19 条）—— 与 Wave 1 manifest §3 完全一致，本轮同样 NOT RUN：
  tests/security/test_authorization_security.py
  tests/integration/alembic_testkit.py（工具模块）
  tests/integration/{test_agent_tool_permission_schema,test_ai_gateway_schema,
    test_alembic_smoke,test_authorization_service,test_authz_enforcement_migration,
    test_identity_schema,test_migration_failure,test_migration_lock,
    test_p10_event_audit_schema,test_p11_triggers,test_p12_indexes,
    test_platform_timestamp_precision,test_rbac_hardening,test_rbac_schema,
    test_resource_acl_schema,test_tenant_space_schema,test_tool_registry_schema}.py
tests/unit/test_generate_build_info.py（OI-G-4 · 既有 REGISTERED/UNFIXED）
```

---

# 6. 本轮执行结果

```text
Wave 2 Unit                 = 14 passed
Wave 2 Security/Integration = 54 passed（identity 12 · device 13 · session 11 · authz 10 · api 6）
Wave 2 合计                  = **68 passed · 0 failed**
Wave 1 Regression（§四十八）= **211 passed · 0 failed**
Forbidden tests executed    = 0
```

**END OF P14 RUNTIME WAVE 2 TEST EXECUTION MANIFEST（2026-09-28 · 68 + 211 passed · CF-C-4 compliant · HARD STOP ACTIVE）**
