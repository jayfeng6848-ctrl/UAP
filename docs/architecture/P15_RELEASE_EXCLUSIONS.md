# P15 RELEASE EXCLUSIONS

日期：2026-09-28
轮次：P15 RELEASE PREPARATION
原则：任何 EXCLUDE 必须给出可审计的理由分类；重要文件逐文件列出。
可复现命令：`git status --short` · `git diff --name-only` · `git ls-files -o --exclude-standard`

---

## 1. 排除分类总表

| 类别 | 数量 | 理由分类 |
|---|---|---|
| BATCH-D maintenance（CF-C-4 / OI-G-4 面 · tracked-modified） | 16 | another batch（BATCH-D） |
| historical dirty（tracked-modified · pre-P15） | 13 | pre-existing / another batch |
| handoff 包（untracked） | 17 | pre-existing handoff（跨阶段交接材料） |
| tests other（untracked） | 5 | P10/P11/P12-era 测试与 testkit |
| docs/architecture 非 P15 文档（untracked） | 80 | P09–P14 历史阶段文档 / 未来 scope |
| **合计排除** | **131** | — |

> P15 RELEASE GATE 变更：原“P13/P10.1-era 未跟踪 migration = 4”已转入
> **BASELINE INTEGRITY REPAIR**（见 `P15_RELEASE_PAYLOAD_MANIFEST.md`），
> 不再是 EXCLUDE；`migrations_alembic/env.py` / `alembic.ini` /
> `migrations_alembic/README.md` / `.env.example` / `README.md` /
> `config/settings.py` / `docker-compose.yml` 同样转入 INCLUDE。

```text
git 视角（P15 RELEASE GATE payload 刷新后实测）
  tracked-modified = 39 · untracked = 155  ⇒ inventory = 194
  − P15 INCLUDE 63（见 P15_RELEASE_PAYLOAD_MANIFEST.md）
  = EXCLUDE 131

拆分核对
  已排除的 tracked-modified = 39 − 10（INCLUDE）= 29
                              = 16（BATCH-D）+ 13（historical dirty）
  已排除的 untracked        = 155 − 53（INCLUDE：4 migration + 4 impl + 4 tests
                                        + 35 evidence + 6 release docs）= 102
                              = 17（handoff）+ 5（tests other）+ 80（architecture other）
  29 + 102 = 131  ✓ 与上表 "合计排除 131" 一致
```

---

## 2. 历史未跟踪 migration（已于 P15 RELEASE GATE 转入 INCLUDE）

```text
migrations_alembic/versions/0013_p10_event_audit.py
migrations_alembic/versions/0014_p11_triggers.py
migrations_alembic/versions/0015_p12_indexes.py
migrations_alembic/versions/0016_open_p10_1_trust_boundary.py
```

```text
理由 = pre-existing / historical：来自 P10.1 / P11 / P12 / OPEN-P10-1 各阶段，
       从未进入 git index；P15 未创建、未修改、未删除这 4 个文件。
P15 ownership = NO，但属 **Release Baseline Integrity** ⇒
分类 = BASELINE INTEGRITY REPAIR（INCLUDE）
```

**F-RP-01（P15 RELEASE GATE 裁决：CLOSED）**

```text
事实：git HEAD tree 的 migrations_alembic/versions/ 只包含 0001–0012 与 0017；
      0013–0016 在 HEAD 中不存在（仅存在于工作区，untracked）。
      但 migrations_alembic/versions/0017_p13_seed.py 的 down_revision =
      "0016_open_p10_1_trust_boundary"，其 revision 定义位于 0015_p12_indexes。
      ⇒ 在**已提交的树**上，Alembic revision 链在 0012 → 0017 之间断裂。

分类 = PRE-EXISTING REPOSITORY BASELINE INTEGRITY DEFECT（非 P15 引入 · 非 P15 scope）
裁决 = P15 RELEASE GATE §6 Option A（独立 Baseline Integrity Repair）⇒ 已修复
结果 = F-RP-01 = CLOSED（fresh clone / isolated DB 的 upgrade → downgrade → upgrade 全部 PASS）
详见 = docs/architecture/P15_BASELINE_INTEGRITY_REPAIR_RECORD.md
```

---

## 3. BATCH-D maintenance（EXCLUDE · another batch）

```text
tests/security/test_authorization_security.py
tests/unit/test_generate_build_info.py
tests/integration/alembic_testkit.py
tests/integration/test_agent_tool_permission_schema.py
tests/integration/test_ai_gateway_schema.py
tests/integration/test_alembic_smoke.py
tests/integration/test_authorization_service.py
tests/integration/test_authz_enforcement_migration.py
tests/integration/test_identity_schema.py
tests/integration/test_migration_lock.py
tests/integration/test_platform_timestamp_precision.py
tests/integration/test_rbac_hardening.py
tests/integration/test_rbac_schema.py
tests/integration/test_resource_acl_schema.py
tests/integration/test_tenant_space_schema.py
tests/integration/test_tool_registry_schema.py
```

```text
理由 = another batch：属 CF-C-4 禁跑面与 OI-G-4 / OI-G-9 范围，由 BATCH-D 统一对账。
       P15 未修改这些文件；本轮不 fix / rewrite / upgrade / delete / merge。
       tests/unit/test_generate_build_info.py 在 P15 全程 executed = 0。
P15 ownership = NO ⇒ EXCLUDE
```

---

## 4. Historical dirty（tracked-modified · EXCLUDE · pre-existing）

```text
core/event/interfaces.py
docs/api/README.md
docs/architecture/ARCHITECTURE.md
docs/architecture/CORE_DOMAIN_MODEL.md
docs/architecture/DEPENDENCY_RULES.md
docs/architecture/STEP1B_B1_2_INDEX_STRATEGY.md
docs/architecture/STEP1B_B1_3_INDEX_STRATEGY.md
docs/architecture/STEP1B_INDEX_STRATEGY.md
docs/architecture/STEP1B_SEED_STRATEGY.md
docs/architecture/STEP1B_TRIGGER_INVENTORY.md
docs/security/README.md
infrastructure/database/__init__.py
tests/conftest.py
```

```text
理由 = pre-existing / another batch：
  · 均为 P15 之前（STEP 0 / STEP 1B / P10 / P10.1 / BATCH-B-C）时期的既有工作区差异
  · P15 未修改这些文件
P15 ownership = NO ⇒ EXCLUDE
  · 例外登记：core/event/interfaces.py · infrastructure/database/__init__.py ·
    tests/conftest.py 属同一 BATCH-B/C 已验收变更集，但不在 Release Integrity scope 内
    ⇒ 见 §9 F-RP-02（REGISTERED / DO NOT FIX）
```

---

## 5. handoff 包（EXCLUDE · pre-existing handoff）

```text
docs/architecture/handoff/00_HANDOFF_INDEX.md
docs/architecture/handoff/01_PROJECT_OVERVIEW.md
docs/architecture/handoff/02_ARCHITECTURE_BOUNDARY.md
docs/architecture/handoff/03_COMPLETED_MILESTONES.md
docs/architecture/handoff/04_P13_FROZEN_DECISIONS.md
docs/architecture/handoff/05_OPEN_P10_1_STATUS.md
docs/architecture/handoff/06_D_OP101_DECISION_STATE.md
docs/architecture/handoff/07_REVISION_AND_MIGRATION_RULES.md
docs/architecture/handoff/08_CURRENT_BLOCKER.md
docs/architecture/handoff/09_P0_FIX_OPTIONS.md
docs/architecture/handoff/10_OPEN_ISSUES_REGISTRY.md
docs/architecture/handoff/11_DATABASE_SECURITY_BASELINE.md
docs/architecture/handoff/12_EVIDENCE_MAP.md
docs/architecture/handoff/13_GIT_HANDOFF_RULES.md
docs/architecture/handoff/14_AGENT_OPERATING_RULES.md
docs/architecture/handoff/15_NEXT_ACTION.md
docs/architecture/handoff/UAP_AGENT_HANDOFF_BUNDLE.md
```

```text
理由 = pre-existing handoff：跨阶段 Agent 交接材料，非 P15 deliverable。
P15 ownership = NO ⇒ EXCLUDE
```

---

## 6. tests other（EXCLUDE · pre-existing / P10–P12 era）

```text
tests/architecture/test_p10_event_audit_boundary.py
tests/integration/runtime_testkit.py
tests/integration/test_p10_event_audit_schema.py
tests/integration/test_p11_triggers.py
tests/integration/test_p12_indexes.py
```

```text
理由 = pre-existing / another phase（P10 / P11 / P12 及 P14 runtime testkit）。
P15 ownership = NO ⇒ EXCLUDE
```

---

## 7. docs/architecture 非 P15 文档（EXCLUDE · historical / future scope）

### 7.1 AGENT_RUNTIME（4 · 未来 scope）

```text
docs/architecture/AGENT_RUNTIME_ACCEPTANCE_MATRIX.md
docs/architecture/AGENT_RUNTIME_DECISION_RESOLUTION.md
docs/architecture/AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md
docs/architecture/AGENT_RUNTIME_PREP_REPORT.md
```

### 7.2 OPEN_P10_1（30 · 历史阶段）

```text
docs/architecture/OPEN_P10_1_ACCEPTANCE_MATRIX.md
docs/architecture/OPEN_P10_1_BATCH_A_EXECUTION_AUTHORIZATION_REQUEST.md
docs/architecture/OPEN_P10_1_BATCH_A_EXECUTION_REPORT.md
docs/architecture/OPEN_P10_1_BATCH_A_HUMAN_DECISION_BLOCK.md
docs/architecture/OPEN_P10_1_BATCH_B_DECISION_RECORD.md
docs/architecture/OPEN_P10_1_BATCH_B_DECISION_REVIEW_REPORT.md
docs/architecture/OPEN_P10_1_BATCH_B_EXECUTION_AUTHORIZATION_REQUEST.md
docs/architecture/OPEN_P10_1_BATCH_B_FINAL_EXECUTION_REPORT.md
docs/architecture/OPEN_P10_1_BATCH_B_HUMAN_DECISION_BLOCK.md
docs/architecture/OPEN_P10_1_BATCH_C_0016_IMPLEMENTATION_BLOCKER_REPORT.md
docs/architecture/OPEN_P10_1_BATCH_C_CLOSURE_RECORD.md
docs/architecture/OPEN_P10_1_BATCH_C_DECISION_RECORD.md
docs/architecture/OPEN_P10_1_BATCH_C_DECISION_REVIEW_REPORT.md
docs/architecture/OPEN_P10_1_BATCH_C_EXECUTION_AUTHORIZATION_REQUEST.md
docs/architecture/OPEN_P10_1_BATCH_C_HUMAN_DECISION_BLOCK.md
docs/architecture/OPEN_P10_1_BATCH_C_IMPLEMENTATION_PRE_FLIGHT_REPORT.md
docs/architecture/OPEN_P10_1_BLOCKER_BA1_FACT_SHEET.md
docs/architecture/OPEN_P10_1_DECISION_RESOLUTION.md
docs/architecture/OPEN_P10_1_HUMAN_DECISION_INPUT.md
docs/architecture/OPEN_P10_1_HUMAN_DECISION_RECORD.md
docs/architecture/OPEN_P10_1_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
docs/architecture/OPEN_P10_1_IMPLEMENTATION_AUTHORIZATION_REQUEST.md
docs/architecture/OPEN_P10_1_IMPLEMENTATION_BATCH_A_BLOCKER_REPORT.md
docs/architecture/OPEN_P10_1_IMPLEMENTATION_CONTRACT.md
docs/architecture/OPEN_P10_1_IMPLEMENTATION_PREP_BASELINE_REPORT.md
docs/architecture/OPEN_P10_1_PREP_REPORT.md
docs/architecture/OPEN_P10_1_REVISION_ID_HUMAN_DECISION_BLOCK.md
docs/architecture/OPEN_P10_1_REVISION_ID_RESOLUTION_REQUEST.md
docs/architecture/OPEN_P10_1_REVISION_RESOLUTION_EXECUTION_PREP_REPORT.md
docs/architecture/OPEN_P10_1_REVISION_RESOLUTION_RECORD.md
```

### 7.3 P13（15 · 已发布阶段）

```text
docs/architecture/P13_ACCEPTANCE_MATRIX.md
docs/architecture/P13_B1_HUMAN_DECISION_AMENDMENT.md
docs/architecture/P13_B1_HUMAN_DECISION_FINAL_DIRECTION.md
docs/architecture/P13_DECISION_COMPLETION_EVIDENCE.md
docs/architecture/P13_DECISION_COMPLETION_FREEZE_GATE_REPORT.md
docs/architecture/P13_DECISION_FREEZE_RECORD.md
docs/architecture/P13_DECISION_RESOLUTION.md
docs/architecture/P13_HUMAN_DECISION_EXTRACTION.md
docs/architecture/P13_HUMAN_DECISION_SHEET.md
docs/architecture/P13_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
docs/architecture/P13_IMPLEMENTATION_CLARIFICATION_HUMAN_DECISION_SHEET.md
docs/architecture/P13_IMPLEMENTATION_CONTRACT.md
docs/architecture/P13_IMPLEMENTATION_READINESS_GATE_REPORT.md
docs/architecture/P13_PREP_REPORT.md
docs/architecture/P13_RELEASE_FINAL_ARCHIVE_GATE_REPORT.md
```

### 7.4 P14（14 · 已发布阶段）

```text
docs/architecture/P14_RELEASE_ARTIFACT_INVENTORY.md
docs/architecture/P14_RELEASE_CANDIDATE_MANIFEST.md
docs/architecture/P14_RELEASE_CANDIDATE_REGRESSION_MATRIX.md
docs/architecture/P14_RELEASE_COMMIT_RECORD.md
docs/architecture/P14_RELEASE_GATE_PRESTATE.md
docs/architecture/P14_RELEASE_GATE_REPORT.md
docs/architecture/P14_RELEASE_IDENTITY_GATE.md
docs/architecture/P14_RELEASE_PAYLOAD_FREEZE.md
docs/architecture/P14_RELEASE_PREPARATION_GIT_BASELINE.md
docs/architecture/P14_RELEASE_SCOPE_LOCK.md
docs/architecture/P14_RELEASE_TAG_RECORD.md
docs/architecture/P14_REMOTE_IDENTITY_GATE.md
docs/architecture/P14_REMOTE_PUSH_PRESTATE.md
docs/architecture/P14_REMOTE_PUSH_RECORD.md
```

### 7.5 其他历史阶段文档（17 · P10 / P11 / P12 / P0 / STEP 2）

```text
docs/architecture/P0_FIX_ACCEPTANCE_RECORD.md
docs/architecture/P10_ACCEPTANCE_MATRIX.md
docs/architecture/P10_DECISION_RESOLUTION.md
docs/architecture/P10_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
docs/architecture/P10_IMPLEMENTATION_CONTRACT.md
docs/architecture/P10_PREP_REPORT.md
docs/architecture/P11_ACCEPTANCE_MATRIX.md
docs/architecture/P11_DECISION_RESOLUTION.md
docs/architecture/P11_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
docs/architecture/P11_IMPLEMENTATION_CONTRACT.md
docs/architecture/P11_PREP_REPORT.md
docs/architecture/P12_ACCEPTANCE_MATRIX.md
docs/architecture/P12_DECISION_RESOLUTION.md
docs/architecture/P12_IMPLEMENTATION_ACCEPTANCE_MATRIX.md
docs/architecture/P12_IMPLEMENTATION_CONTRACT.md
docs/architecture/P12_PREP_REPORT.md
docs/architecture/RUNTIME_DOCUMENT_SET_DECISION.md
```

```text
7.1–7.5 合计 = 4 + 30 + 15 + 14 + 17 = 80（逐文件列出，无未审计汇总数字）
理由 = historical / future scope：这些文档在 P14 release（15feebad）之后仍未跟踪，
       属于已发布阶段的历史材料或未来 scope（AGENT_RUNTIME），非 P15 deliverable。
P15 ownership = NO ⇒ EXCLUDE
```

---

## 8. 明确未被排除（对照）

```text
tracked-modified = 39，其中 10 个 INCLUDE：
  apps/worker/main.py                        → P15 IMPLEMENTATION
  docs/architecture/PLATFORM_DECISION_LOG.md → P15 GOVERNANCE（附录 T）
  migrations_alembic/env.py                  → BASELINE INTEGRITY REPAIR
  alembic.ini                                → BASELINE INTEGRITY REPAIR
  migrations_alembic/README.md               → BASELINE INTEGRITY REPAIR
  .env.example                               → BASELINE INTEGRITY REPAIR
  README.md                                  → BASELINE INTEGRITY REPAIR
  pyproject.toml                             → RELEASE METADATA
  config/settings.py                         → RELEASE METADATA
  docker-compose.yml                         → RELEASE METADATA
其余 29 个 tracked-modified → EXCLUDE（16 BATCH-D + 13 historical dirty）
```

---

## 9. F-RP-02 残留登记（REGISTERED · DO NOT FIX）

```text
ID             = F-RP-02
Classification = BATCH-B/C ACCEPTED CHANGESET RESIDUAL（非 Release Integrity scope）
Blocking       = NO
处置           = REGISTER / DO NOT FIX

残留文件（3）
  tests/conftest.py                    dual-DSN 测试夹具（migration_dsn / runtime_dsn）
  core/event/interfaces.py             EventBus != Outbox 说明 · UUIDv4 → UUIDv7 · nullable tenant_id
  infrastructure/database/__init__.py  导出 RuntimeDatabase / Repository / principal helpers

列入 EXCLUDE 的理由
  · 不满足任何 Release Gate 判据：
      - 不影响 committed Alembic graph 的重建与 upgrade
      - 不影响版本权威一致性
  · core/event/interfaces.py 含**行为语义变更**（事件 id 生成器改为 UUIDv7、
    tenant_id 允许 NULL）⇒ 超出 Release Integrity scope，须独立裁决
  · tests/conftest.py 为测试装配面，被 CF-C-4 禁跑文件依赖，非 release 运行路径

建议 = 在后续独立 Gate 中裁决（授权纳入 / 授权独立修复 / 授权豁免）
```
