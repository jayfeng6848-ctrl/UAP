# P15 CHANGE MATRIX（Consolidated · Batch 1–4）

日期：2026-09-28
说明：逐路径记录 classification / reason / contract section / test coverage

---

## 1. 汇总

```text
implementation files = 5
tests                 = 4
evidence docs         = Batch 3: 5 · Batch 4: 8 · PDL append: 1
schema / migration    = 0
runtime 业务域代码     = 0
```

---

## 2. 实现文件

### 2.1 `services/consumer/kernel.py`（Batch 1）

```yaml
classification: new
sha256: d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769
reason: 冻结纯逻辑（backoff / eligibility / allowlist）+ 7 段冻结 SQL 文本
contract_section: Contract §4 §7 §8 §9 · PDL 附录 S（O-2/O-4/O-5/O-6）
test_coverage: tests/unit/test_p15_consumer_kernel.py（13）
```

### 2.2 `services/consumer/claim.py`（Batch 2）

```yaml
classification: new
sha256: db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a
reason: session-scoped ClaimService（claim/heartbeat/retry/dead/recovery）
contract_section: Contract §7 §9 §10 · PDL 附录 S（O-1）
test_coverage: tests/integration/test_p15_claim.py（13）
```

### 2.3 `services/consumer/worker.py`（Batch 3）

```yaml
classification: new（Batch 3 内重写一次）
pre_image_sha256:  5f5d02b9c5e9134e9adf43afe8056a27ab7bb1ca6f3cc7880a0fea1deeef9063
post_image_sha256: 385306d9fec4b2d71e3ecee0ce87269c01b0c7d4b1ab4b13eb8731d9b64aa263
reason: lifecycle / poll / bounded concurrency / heartbeat / recovery / shutdown / drain
contract_section: Contract §6 §9 · PDL 附录 S（O-1/O-3/O-4/O-5）
test_coverage: tests/unit/test_p15_worker.py（30）
```

### 2.4 `services/consumer/__init__.py`（Batch 1 → Batch 3）

```yaml
classification: new → modified（docstring + export）
pre_image_sha256:  UNAVAILABLE（untracked，见 §5）
post_image_sha256: 32c146ff42af3490726d9aa56629366f12acad468bd4271017b44ff841700d19
reason: 修正过期 docstring（声称 worker 未实现）；导出 worker 公开符号
runtime_behavior_change: 0
```

### 2.5 `apps/worker/main.py`（Batch 4 · 最小补齐）

```yaml
classification: modified（STEP 0 placeholder → 真实 consumer 入口）
pre_image_sha256:  5045be3e2e6bfc8fd221145ed0e228df33e71478c47e81d8eb1223506233d7ad
post_image_sha256: 520a344f200981ed42995ffddd6a567410578e9fee97f5ec30ef712b69061b8c
reason: |
  Contract §2 / P15_IMPLEMENTATION_PREP 将 apps/worker/** 列为 IN（专用 consumer 入口）；
  P14 已将其列为 OUT OF SCOPE ⇒ 属 P15 真实 implementation gap，按 BATCH 4 §10 最小补齐。
contract_section: Contract §2 §6 §7 · BATCH 4 §8/§9/§10/§11
test_coverage: tests/unit/test_p15_worker_entry.py（9）
pre_image_git_state: 已提交于 HEAD 15feebad（P14 release commit）；本轮仅修改工作区文件，
  未修改该 commit、未修改 P14 tag、未修改 history。
```

`apps/worker/__init__.py` 未修改（sha256 = 2705388a80f53453d3d89397f50a41299655f9955f3a283e029fbf1847c6e963）。

---

## 3. 测试文件

```yaml
tests/unit/test_p15_consumer_kernel.py   sha256 aa4cd53f04179744712228ec57064b65cd41cc882b3fd90bf31344c60c3fd94f  （13）
tests/integration/test_p15_claim.py      sha256 599a0550b10d7bfe8ca7db969cf7eae4235b2fb07f0156fb44ffc8f75a91d09b  （13）
tests/unit/test_p15_worker.py            sha256 1bb1a4f158c1775c584ef23636139624c3e92f25b115b270fe7c8baa52e6e23e  （30）
tests/unit/test_p15_worker_entry.py      sha256 eb27da282872506580a61242dfee26729adc3e8b7d6bc1a58d04d602acc6dc4a  （9 · Batch 4 新增）
```

---

## 4. Evidence 文档

```yaml
Batch 3（前轮）:
  P15_BATCH3_IMPLEMENTATION_FILE_ALLOWLIST.md
  P15_BATCH3_CHANGE_MATRIX.md
  P15_BATCH3_IMPLEMENTATION_REPORT.md
  P15_BATCH3_TEST_EXECUTION_REPORT.md
  P15_BATCH3_TEST_EXECUTION_MANIFEST.md
Batch 4（本轮）:
  P15_BATCH1_RETROSPECTIVE_EVIDENCE.md      （RETROSPECTIVE RECONSTRUCTION）
  P15_BATCH2_RETROSPECTIVE_EVIDENCE.md      （RETROSPECTIVE RECONSTRUCTION）
  P15_IMPLEMENTATION_REPORT.md
  P15_CHANGE_MATRIX.md                      （本文件）
  P15_BATCH4_TEST_EXECUTION_MANIFEST.md
  P15_BATCH4_TEST_EXECUTION_REPORT.md
  P15_IMPLEMENTATION_ACCEPTANCE_REPORT.md
  P15_IMPLEMENTATION_ACCEPTANCE_MAPPING.md
  P15_FINAL_FINDING_REGISTRY.md
  P15_FINAL_EVIDENCE_INVENTORY.md
PDL:
  PLATFORM_DECISION_LOG.md                  （append-only 追加附录 T）
```

---

## 5. 明确未变更（受保护对象）

```text
services/reads.py                          sha256 aa5d2e61846919c2c637c9236b9dcda5dcf1a46ae6b4ac6edaba17a9b3129fe6（未改）
infrastructure/database/persistence.py     sha256 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（未改 · D-01）
tests/integration/test_runtime_db_wave1.py sha256 51a453f5c1858873525753b556438c4d42240fb393e5b4b770d058a3b0b25c46（未改 · Wave 1 frozen）
migrations_alembic/env.py                  sha256 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a（未改）
0016_open_p10_1_trust_boundary.py          sha256 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544（未改）
0017_p13_seed.py                           sha256 1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e（未改）
PLATFORM_DECISION_LOG.md 附录 O–S          未改写（仅 append T）
apps/api/**                               未修改
```

---

## 6. 边界计数

```text
new schema / migration / DDL / GRANT / REVOKE / role / principal / ACL subject / action = 0
formal DB DML = 0
new external dependency = 0
commit / tag / push / release = 0
```

