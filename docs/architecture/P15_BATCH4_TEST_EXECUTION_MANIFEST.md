# P15 BATCH 4 — TEST EXECUTION MANIFEST（唯一完整 test manifest）

日期：2026-09-28
铁律：**逐文件显式 allowlist**。禁止 `pytest`、`pytest tests/`、
`pytest --collect-only`、以及任何目录级 discovery。未列明文件一律 NOT RUN。

---

## 1. P15-KERNEL

```text
tests/unit/test_p15_consumer_kernel.py                 13 passed
```

## 2. P15-CLAIM

```text
tests/integration/test_p15_claim.py                    13 passed
```

## 3. P15-WORKER

```text
tests/unit/test_p15_worker.py                          30 passed
```

## 4. P15-INTEGRATION / P15-SECURITY / P15-ACCEPTANCE

```text
tests/unit/test_p15_worker_entry.py                     9 passed
  （Batch 4 新增 · 覆盖 process entry：startup / running / stop signal /
    draining / stopped / startup failure / config / no orphan / no false delivered）

真库安全面以只读实测锚点核验（51/6/5/0/245 · default_acl 0 · C2 · P13 3/12/12 ·
0017 · 0018+=0 · formal DB prestate == poststate），未新增 integration/security 文件。
P15 生产 allowlist = EMPTY，故 production 侧不存在可执行的真实业务事件路径。
```

汇总：P15 = **65 passed**

## 5. P14-REGRESSION — Wave 1 approved set（17 文件）

```text
tests/unit/test_runtime_error_taxonomy.py
tests/unit/test_runtime_retry_boundary.py
tests/unit/test_runtime_lifecycle_boundary.py
tests/architecture/test_dependency_rules.py
tests/architecture/test_p10_event_audit_boundary.py
tests/architecture/test_agent_resource_scope_opaque.py
tests/contract/test_health_contract.py
tests/contract/test_authorization_contract.py
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

预期（历史事实）：`210 passed + 1 failed`（D-02 记录，`test_runtime_db_wave1.py::test_approved_reads`
的 `assert audit == 0` 保持原样，不得改写为 211/211）。

## 6. WAVE2-REGRESSION（9 文件）

```text
tests/unit/test_wave2_vocabulary_mapping.py
tests/unit/test_wave2_credentials.py
tests/unit/test_wave2_error_mapping.py
tests/integration/test_wave2_identity_security.py
tests/integration/test_wave2_device_security.py
tests/integration/test_wave2_session_security.py
tests/integration/test_wave2_authorization_security.py
tests/integration/test_wave2_api_security.py
tests/integration/test_wave2_audit_invariant.py
```

预期：`72 passed`。

## 7. 测试支撑（非用例 · 不单独执行）

```text
tests/integration/runtime_testkit.py      UAP_RUNTIME_TEST_DSN 解析（Wave 1）
tests/integration/wave2_testkit.py        runtime_data_scope / provisioning（Wave 2）
tests/integration/alembic_testkit.py      含 reset_test_database ⇒ 属 DENY 面工具模块
tests/conftest.py
```

## 8. DENY — CF-C-4 禁跑集合（19 条）· executed = 0

```text
tests/security/test_authorization_security.py
tests/integration/alembic_testkit.py
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

## 9. DENY — OI-G-4 文件 · executed = 0

```text
tests/unit/test_generate_build_info.py
```

---

## 10. 执行顺序与实际用量

```text
1. P15-KERNEL            → 13 passed
2. P15-CLAIM             → 13 passed
3. P15-WORKER            → 30 passed
4. P15-ENTRY             →  9 passed
5. P14 Wave 1 regression → 210 passed + 1 failed（D-02 历史事实）
6. Wave 2 regression     → 72 passed

forbidden files executed = 0
directory-level pytest   = 0
collect-only             = 0
```

