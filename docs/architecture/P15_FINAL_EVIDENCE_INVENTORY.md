# P15 FINAL EVIDENCE INVENTORY

日期：2026-09-28
轮次：P15 IMPLEMENTATION — Batch 4（Final Closure）
每条：artifact · hash · authority · result

> 本文件自身的 hash 无法自引用（写入后才会确定）；其余全部为写入后实测值。

---

## 1. Decision / Governance

| artifact | hash | authority | result |
|---|---|---|---|
| `docs/architecture/PLATFORM_DECISION_LOG.md`（含附录 T） | `9221b4d78b6543eb9d289593f15bf968da8e73ae62a546db8d0cb194ae5a5c83` | PDL canonical | 附录 A–S 零改写 · T append-only · PASS |
| `docs/architecture/P15_HUMAN_DECISION_SHEET.md` | （未修改） | Human decision 载体 | 未触碰 |
| `docs/architecture/P15_DECISION_COMPLETION_REPORT.md` | （未修改） | Decision closure | 未触碰 |

## 2. Contract / Matrix / Prep

| artifact | hash | authority | result |
|---|---|---|---|
| `docs/architecture/P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md` | `260a784c643600da6fdf76b823c7fa4cff08a1ae61c3f2df85f69c64f0a1b3c2` | FROZEN contract | 未修改 · PASS |
| `docs/architecture/P15_ACCEPTANCE_MATRIX_PREP.md` | `87a7a5bc5425cc6a4bfd285a711cc7d58202d46f1e142bb1db556bebc9ad444a` | 冻结设计矩阵 | 未修改 · 由 mapping 承接 |
| `docs/architecture/P15_IMPLEMENTATION_PREP.md` | （未修改） | Prep | 未修改 |

## 3. Implementation

| artifact | hash | authority | result |
|---|---|---|---|
| `services/consumer/kernel.py` | `d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769` | Batch 1 | PASS |
| `services/consumer/claim.py` | `db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a` | Batch 2 | PASS |
| `services/consumer/worker.py` | `385306d9fec4b2d71e3ecee0ce87269c01b0c7d4b1ab4b13eb8731d9b64aa263` | Batch 3 | PASS |
| `services/consumer/__init__.py` | `32c146ff42af3490726d9aa56629366f12acad468bd4271017b44ff841700d19` | 导出面 | PASS（pre-image UNAVAILABLE） |
| `apps/worker/main.py` | `520a344f200981ed42995ffddd6a567410578e9fee97f5ec30ef712b69061b8c` | Batch 4 consumer entry | PASS |
| `apps/worker/__init__.py` | `2705388a80f53453d3d89397f50a41299655f9955f3a283e029fbf1847c6e963` | 未修改 | PASS |

## 4. Tests

| artifact | hash | authority | result |
|---|---|---|---|
| `tests/unit/test_p15_consumer_kernel.py` | `aa4cd53f04179744712228ec57064b65cd41cc882b3fd90bf31344c60c3fd94f` | Batch 1 | 13 passed |
| `tests/integration/test_p15_claim.py` | `599a0550b10d7bfe8ca7db969cf7eae4235b2fb07f0156fb44ffc8f75a91d09b` | Batch 2 | 13 passed |
| `tests/unit/test_p15_worker.py` | `1bb1a4f158c1775c584ef23636139624c3e92f25b115b270fe7c8baa52e6e23e` | Batch 3 | 30 passed |
| `tests/unit/test_p15_worker_entry.py` | `eb27da282872506580a61242dfee26729adc3e8b7d6bc1a58d04d602acc6dc4a` | Batch 4 | 9 passed |
| `tests/integration/test_runtime_db_wave1.py` | `51a453f5c1858873525753b556438c4d42240fb393e5b4b770d058a3b0b25c46` | P14 Wave 1 frozen | 未修改 · 1 failed（D-02） |

## 5. Security / Schema / DB

| artifact | hash / value | authority | result |
|---|---|---|---|
| `infrastructure/database/persistence.py`（D-01） | `69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6` | 冻结 · DEFERRED | 未修改 |
| `services/reads.py`（SafeReader） | `aa5d2e61846919c2c637c9236b9dcda5dcf1a46ae6b4ac6edaba17a9b3129fe6` | P14 Wave 2 | 未修改 |
| `migrations_alembic/env.py` | `577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a` | P0 fix 冻结 | 未修改 |
| `0016_open_p10_1_trust_boundary.py` | `10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544` | 冻结 | 未修改 |
| `0017_p13_seed.py` | `1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e` | 冻结 | 未修改 |
| privilege fingerprint | 51 / 6 / 5 / 0 / 245 | security evidence freeze | 未变 · PASS |
| default_acl | 0 | security evidence freeze | 未变 · PASS |
| C2 md5 | `185e95be8bc4304edbcd3f4d5cda1eff` | CC-7 | 未变 · PASS |
| P13 seed | 3 / 12 / 12 | P13 release | 未变 · PASS |
| alembic / 0018+ | `0017_p13_seed` / 0 | schema baseline | 未变 · PASS |
| pg_class / pg_proc / pg_trigger | 156 / 22 / 272 | schema baseline | 未变 · PASS |
| formal db `uap` | prestate == poststate | DB boundary | PASS |
| test db `uap_b1_test` | 仅 audit_logs +243（append-only 预期） | DB boundary | PASS |

## 6. Regression

| artifact | value | authority | result |
|---|---|---|---|
| P14 Wave 1 approved set（17 文件） | 210 passed + 1 failed | P14 Wave 1 manifest | HISTORICAL RECORD · D-02 CLOSED |
| Wave 2 accepted set（9 文件） | 72 passed | P14 Wave 2 manifest | PASS |
| Cross-Wave | P15 变更后结果与历史逐项一致 | BATCH 4 §54 | PASS |
| CF-C-4 | 19 禁跑文件 + OI-G-4 文件 executed = 0 | P14 manifest §3 | PASS |

## 7. Evidence documents（Batch 4 新增）

| artifact | hash |
|---|---|
| `P15_BATCH1_RETROSPECTIVE_EVIDENCE.md` | `6868c63706a7e09a9b8dba8efb23422679556d705450e02b1d3a2380002993f7` |
| `P15_BATCH2_RETROSPECTIVE_EVIDENCE.md` | `5bc34af52db8245ad2056f6b3499b4d2d462590885e18c2b2d2243616af2216a` |
| `P15_IMPLEMENTATION_REPORT.md` | `f39e8c2318c1b6259fbe27c24fb0b3b6f6de6e1833c3377afaa7d5e748167c54` |
| `P15_CHANGE_MATRIX.md` | `4cdf1e8ea1fd8609f9ca3fef9c631f5c9d5d396ccfeaa7f6f604f3d29e00c920` |
| `P15_BATCH4_TEST_EXECUTION_MANIFEST.md` | `262e5de0150231b5c2fb25324a90f3989924568bc2e66f6526b15c2f10d460b2` |
| `P15_BATCH4_TEST_EXECUTION_REPORT.md` | `87bfc1d8a128f4c34915f4bc4114a95faceae22f8e8fea0311f26b55939d68b8` |
| `P15_IMPLEMENTATION_ACCEPTANCE_REPORT.md` | `98cdd3c803358224dc3760b7fed28b4d49f2587b073d0d25e1033b6149976b1d` |
| `P15_IMPLEMENTATION_ACCEPTANCE_MAPPING.md` | `074ebf1d2432ffa35786206d5712a22d1dc0ea15448bedc9bb27f25b0293791a` |
| `P15_FINAL_FINDING_REGISTRY.md` | `33d6c4288cfbe73202b28769f759590a6f289f8d479ee740f0f9726987d48c6c` |
| `P15_OVERALL_ACCEPTANCE_REPORT.md` | `3191690a26f51220ae693ad288bd2dbd88e4941cd5bdfbe23319c29df3e2a0b5` |
| `P15_OVERALL_ACCEPTANCE_CLOSURE.md` | `00268e7a078226e46dfa9f6bb337392ab311048dc5a8df0c61e3e68e2b3951a0` |
| `P15_FINAL_EVIDENCE_INVENTORY.md` | （self-referential · 不适用） |

> 说明：`P15_FINAL_FINDING_REGISTRY.md` 的 hash 因 P15 OVERALL ACCEPTANCE 的
> F-B4-08 最终裁决（分类由 AUTHORIZED 更正为 CLOSED / EXPECTED P15 GOVERNANCE DELTA）
> 而更新，属本轮允许的“hash 引用/证据措辞最小更正”。

## 8. 完备性

```text
P15 implementation report          = EXISTS
P15 change matrix                  = EXISTS
P15 test manifest                  = EXISTS
P15 test execution report          = EXISTS
P15 Batch1 retrospective evidence  = EXISTS（RETROSPECTIVE · 已标注）
P15 Batch2 retrospective evidence  = EXISTS（RETROSPECTIVE · 已标注）
P15 Batch3 implementation report   = EXISTS
P15 Batch3 change matrix           = EXISTS
P15 Batch3 test execution evidence = EXISTS
P15 acceptance evidence            = EXISTS（Acceptance Report + Mapping + Finding Registry）
P15 overall acceptance evidence    = EXISTS（P15_OVERALL_ACCEPTANCE_REPORT.md +
                                      P15_OVERALL_ACCEPTANCE_CLOSURE.md）
Production Allowlist / Worker / Observability / D-01 / D-02 / CF-C-4 = 均已登记
```

```text
Git: HEAD 15feebad（未变）· tags 10（未新增）· staged 0 · commit/tag/push = 0
```
