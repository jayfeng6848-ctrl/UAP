# P15 BATCH 3 — TEST EXECUTION MANIFEST（CF-C-4）

日期：2026-09-28
铁律：只允许**逐文件**显式 allowlist；禁止 `pytest` / `pytest tests/` /
`pytest tests/unit/` / `pytest tests/integration/` / `pytest tests/security/` 等目录级递归执行。
任何未在本 manifest 列明的文件，一律 **NOT RUN**。

---

## 1. ALLOWED — Batch 3 显式执行集合

### 1.1 Batch 3 unit

```text
tests/unit/test_p15_worker.py                         30 passed
```

### 1.2 Batch 3 integration

```text
（无）
本轮 Batch 3 未新增 integration 测试。原因：worker 的全部依赖（clock / sleep /
claim_service_factory / handler registry / dependency_probe）均可注入，lifecycle、
bounded concurrency、heartbeat、recovery、shutdown 与失败语义可在无数据库条件下
被完整证明。真库的原语语义已由 Batch 2 的 tests/integration/test_p15_claim.py 覆盖。
```

### 1.3 Batch 3 security

```text
（无新增文件）
安全面以只读实测锚点核验，见 P15_BATCH3_TEST_EXECUTION_REPORT.md §7：
  51/6/5/0/245 · default_acl 0 · schema CREATE false · ownership residual 0 ·
  user-defined membership 0 · C2 md5 不变 · P13 seed 3/12/12 · 0017 · 0018+ = 0
```

### 1.4 Regression（Batch 1 / Batch 2）

```text
tests/unit/test_p15_consumer_kernel.py                13 passed   （Batch 1 regression）
tests/integration/test_p15_claim.py                   13 passed   （Batch 2 regression）
```

---

## 2. DENY — CF-C-4 禁跑集合（19 条）· executed = 0

```text
tests/security/test_authorization_security.py          ← 事故触发文件
tests/integration/alembic_testkit.py                   （工具模块 · 定义 reset_test_database）
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

禁止理由：这些文件（或其所依赖的 toolkit）会执行 `reset_test_database()`，从而重置
BATCH-A ownership state，并可能触发 OI-G-9 的潜伏 stale assertion。

---

## 3. DENY — OI-G-4 文件 · executed = 0

```text
tests/unit/test_generate_build_info.py     （既有 REGISTERED / UNFIXED）
```

---

## 4. NOT RUN（未列入任何 allowlist）

```text
tests/ 下除本 manifest §1 明确列出的 3 个文件以外的**全部**文件
```

特别说明：`tests/conftest.py`、`tests/integration/alembic_testkit.py` 属 support/toolkit，
只作为被 import 的依赖出现，不作为执行目标。

---

## 5. 执行记录

```text
allowlist executed files = 3
forbidden files executed = 0
directory-level pytest    = 0
skipped                   = 0
failed                    = 0
total                     = 56 passed
```

执行命令（逐文件，等价形式）：

```text
python -m pytest tests/unit/test_p15_consumer_kernel.py   -p no:cacheprovider -q
python -m pytest tests/integration/test_p15_claim.py      -p no:cacheprovider -q
python -m pytest tests/unit/test_p15_worker.py            -p no:cacheprovider -q
```

---

## 6. 声明

```text
CF-C-4 = PASS（本 Batch 无任何禁跑文件被执行）
本 manifest 不覆盖 Batch 4（Full Acceptance + Cross-Wave Regression）的 allowlist；
Wave 1 / Wave 2 的全量 allowlist 需在 Batch 4 单独建立。
```

