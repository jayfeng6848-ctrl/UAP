# P15 RELEASE PAYLOAD MANIFEST

日期：2026-09-28（**P15 RELEASE GATE 后重新计算版本**）
Parent baseline：`15feebadeecd6f7d90e81569c3e869bc20cb18c5`（`UAP-V0.1.10-P14-RUNTIME-SLICE`）
Tag candidate：`UAP-V0.1.11-P15-EVENT-CONSUMER`
Hash：SHA-256（全部为当前 working tree 实测值）

```text
Payload total = 64
  P15 IMPLEMENTATION        = 5
  P15 TEST                  = 4
  P15 EVIDENCE              = 35
  P15 RELEASE (docs)        = 7
  P15 GOVERNANCE            = 1
  BASELINE INTEGRITY REPAIR = 9
  RELEASE METADATA          = 3
```

> 历史说明：Release Preparation 轮的 manifest 记录 payload = 49。
> 经 P15 RELEASE GATE 的 baseline integrity repair（F-RP-01 / F-RP-03）与
> version synchronization 后，该数字已作废；本版本为唯一有效 payload 定义。

## 1. Payload Table

### 1.1 P15 IMPLEMENTATION（5）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `apps/worker/main.py` | P15 IMPLEMENTATION | P15 | `520a344f200981ed42995ffddd6a567410578e9fee97f5ec30ef712b69061b8c` | 专用 consumer 进程入口（Batch 4 最小补齐 · Contract §2 IN） |
| `services/consumer/__init__.py` | P15 IMPLEMENTATION | P15 | `32c146ff42af3490726d9aa56629366f12acad468bd4271017b44ff841700d19` | 包导出面 + docstring 与 Batch 1–3 实现对齐 |
| `services/consumer/kernel.py` | P15 IMPLEMENTATION | P15 | `d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769` | Batch 1 kernel（冻结纯逻辑 + 冻结 SQL + CLOSED allowlist） |
| `services/consumer/claim.py` | P15 IMPLEMENTATION | P15 | `db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a` | Batch 2 session-scoped ClaimService |
| `services/consumer/worker.py` | P15 IMPLEMENTATION | P15 | `385306d9fec4b2d71e3ecee0ce87269c01b0c7d4b1ab4b13eb8731d9b64aa263` | Batch 3 ConsumerWorker（lifecycle/poll/concurrency） |

### 1.2 P15 TEST（4）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `tests/unit/test_p15_consumer_kernel.py` | P15 TEST | P15 | `aa4cd53f04179744712228ec57064b65cd41cc882b3fd90bf31344c60c3fd94f` | Batch 1 · 13 tests |
| `tests/integration/test_p15_claim.py` | P15 TEST | P15 | `599a0550b10d7bfe8ca7db969cf7eae4235b2fb07f0156fb44ffc8f75a91d09b` | Batch 2 · 13 tests（uap_b1_test · uap_runtime） |
| `tests/unit/test_p15_worker.py` | P15 TEST | P15 | `1bb1a4f158c1775c584ef23636139624c3e92f25b115b270fe7c8baa52e6e23e` | Batch 3 · 30 tests |
| `tests/unit/test_p15_worker_entry.py` | P15 TEST | P15 | `eb27da282872506580a61242dfee26729adc3e8b7d6bc1a58d04d602acc6dc4a` | Batch 4 · 9 tests（process entry） |

### 1.3 P15 EVIDENCE（35）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `docs/architecture/P15_ACCEPTANCE_MATRIX_PREP.md` | P15 EVIDENCE | P15 | `87a7a5bc5425cc6a4bfd285a711cc7d58202d46f1e142bb1db556bebc9ad444a` | 验收矩阵（冻结设计面） |
| `docs/architecture/P15_BATCH1_RETROSPECTIVE_EVIDENCE.md` | P15 EVIDENCE | P15 | `6868c63706a7e09a9b8dba8efb23422679556d705450e02b1d3a2380002993f7` | Batch 1 回溯证据（RETROSPECTIVE 已标注） |
| `docs/architecture/P15_BATCH2_RETROSPECTIVE_EVIDENCE.md` | P15 EVIDENCE | P15 | `5bc34af52db8245ad2056f6b3499b4d2d462590885e18c2b2d2243616af2216a` | Batch 2 回溯证据（RETROSPECTIVE 已标注） |
| `docs/architecture/P15_BATCH3_CHANGE_MATRIX.md` | P15 EVIDENCE | P15 | `90557a635e755a04b31baaa5da218efc6227a92d1dc246596aa9f3b70608879e` | Batch 3 变更矩阵 |
| `docs/architecture/P15_BATCH3_IMPLEMENTATION_FILE_ALLOWLIST.md` | P15 EVIDENCE | P15 | `50100249efdf1b0ffde30032092f2586e76b483c95f3e90e716b5bde0d8e17fc` | Batch 3 文件白名单 |
| `docs/architecture/P15_BATCH3_IMPLEMENTATION_REPORT.md` | P15 EVIDENCE | P15 | `2371a623c325e02a87518c1644cd5bcb84ec4822b78378e6d7e98c237d429473` | Batch 3 实施报告 |
| `docs/architecture/P15_BATCH3_TEST_EXECUTION_MANIFEST.md` | P15 EVIDENCE | P15 | `0c967fad8da8f5ff1eb087bb44f055c9f189419dec2eff4265f3daed418bac40` | Batch 3 逐文件清单 |
| `docs/architecture/P15_BATCH3_TEST_EXECUTION_REPORT.md` | P15 EVIDENCE | P15 | `7a8d1e033cf205ba1d83b6ec1c3125b731beec257681bb91be89c441cc6b1962` | Batch 3 测试执行报告 |
| `docs/architecture/P15_BATCH4_TEST_EXECUTION_MANIFEST.md` | P15 EVIDENCE | P15 | `262e5de0150231b5c2fb25324a90f3989924568bc2e66f6526b15c2f10d460b2` | Batch 4 逐文件 allowlist / denylist |
| `docs/architecture/P15_BATCH4_TEST_EXECUTION_REPORT.md` | P15 EVIDENCE | P15 | `87bfc1d8a128f4c34915f4bc4114a95faceae22f8e8fea0311f26b55939d68b8` | Batch 4 测试执行报告（含 O-2 canonical） |
| `docs/architecture/P15_CANDIDATE_SCOPE_DISCOVERY.md` | P15 EVIDENCE | P15 | `d4626d10a8001d418499b74f9711f207cac18ebf741ec4cf86165595c92756fc` | 候选 scope 发现 |
| `docs/architecture/P15_CHANGE_MATRIX.md` | P15 EVIDENCE | P15 | `4cdf1e8ea1fd8609f9ca3fef9c631f5c9d5d396ccfeaa7f6f604f3d29e00c920` | 汇总变更矩阵 |
| `docs/architecture/P15_DECISION_COMPLETION_GATE_REPORT.md` | P15 EVIDENCE | P15 | `d0a2442c1a5f14022498cf63bd92f8e25938d364712d239d33f2f02e7698e409` | 决策完成 Gate 报告 |
| `docs/architecture/P15_DECISION_COMPLETION_PREP.md` | P15 EVIDENCE | P15 | `cebad103240c58e0a87f572dac93307594563f8be214dadf257be9c7d9e37875` | 决策完成准备 |
| `docs/architecture/P15_DECISION_COMPLETION_REPORT.md` | P15 EVIDENCE | P15 | `7f74d1dd37009250ee5ba1fc2ab1f9f481608d626e77aff3bba1f5fd47f48892` | 决策完成报告 |
| `docs/architecture/P15_DECISION_IMPACT_MATRIX.md` | P15 EVIDENCE | P15 | `3472834138d6e6c5a4107ff48db685bcb2dc7cbc1c1a3a0d3c088bb718f52499` | 决策影响矩阵 |
| `docs/architecture/P15_DEPENDENCY_MAP.md` | P15 EVIDENCE | P15 | `3da27ad00c08d65263ebebd979d2f8a790c04e7dbd457897d6feb56973500ab9` | 依赖映射 |
| `docs/architecture/P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md` | P15 EVIDENCE | P15 | `260a784c643600da6fdf76b823c7fa4cff08a1ae61c3f2df85f69c64f0a1b3c2` | FROZEN contract（验收基准） |
| `docs/architecture/P15_FINAL_EVIDENCE_INVENTORY.md` | P15 EVIDENCE | P15 | `3af37acd89645453ab41cd1b2f704351d46f36c42c83fcfe43fdef7ba0ed816e` | 证据清单（artifact/hash/authority/result） |
| `docs/architecture/P15_FINAL_FINDING_REGISTRY.md` | P15 EVIDENCE | P15 | `33d6c4288cfbe73202b28769f759590a6f289f8d479ee740f0f9726987d48c6c` | Finding 分类（F-B4-08 CLOSED） |
| `docs/architecture/P15_HUMAN_DECISION_REVIEW_PACKAGE.md` | P15 EVIDENCE | P15 | `72dcae3400483dfccb4d3c71431437155534a2cb9257f43814ef593624af14d3` | 决策评审包 |
| `docs/architecture/P15_HUMAN_DECISION_SHEET.md` | P15 EVIDENCE | P15 | `7e106c77a804b45a220b667478f370db42b10aec884c57cc80f56040bd6b7feb` | OQ 决策载体 |
| `docs/architecture/P15_IMPLEMENTATION_ACCEPTANCE_MAPPING.md` | P15 EVIDENCE | P15 | `074ebf1d2432ffa35786206d5712a22d1dc0ea15448bedc9bb27f25b0293791a` | 矩阵逐条映射 |
| `docs/architecture/P15_IMPLEMENTATION_ACCEPTANCE_REPORT.md` | P15 EVIDENCE | P15 | `98cdd3c803358224dc3760b7fed28b4d49f2587b073d0d25e1033b6149976b1d` | Contract 逐节验收证据 |
| `docs/architecture/P15_IMPLEMENTATION_BLOCKER.md` | P15 EVIDENCE | P15 | `1ac9d90d874bf924acac461bc4119865e1a47c313faa91c32575dcafbd88c9cc` | 历史 blocker 记录 |
| `docs/architecture/P15_IMPLEMENTATION_PREP.md` | P15 EVIDENCE | P15 | `411520719d73f428c414f8e3aea3241bbdb2421fd4c78e45e2f0a883d41a6b43` | 实施准备（scope IN 依据） |
| `docs/architecture/P15_IMPLEMENTATION_REPORT.md` | P15 EVIDENCE | P15 | `f39e8c2318c1b6259fbe27c24fb0b3b6f6de6e1833c3377afaa7d5e748167c54` | 汇总实现报告 |
| `docs/architecture/P15_OVERALL_ACCEPTANCE_CLOSURE.md` | P15 EVIDENCE | P15 | `00268e7a078226e46dfa9f6bb337392ab311048dc5a8df0c61e3e68e2b3951a0` | 收口与 F-B4-08 裁决 |
| `docs/architecture/P15_OVERALL_ACCEPTANCE_REPORT.md` | P15 EVIDENCE | P15 | `3191690a26f51220ae693ad288bd2dbd88e4941cd5bdfbe23319c29df3e2a0b5` | 项目级接受报告 |
| `docs/architecture/P15_PREP_ARCHITECTURE_SNAPSHOT.md` | P15 EVIDENCE | P15 | `e4b574d9beba8c5f6633c962f67f13235d8141bb285350c53021852220aa19b0` | 架构快照 |
| `docs/architecture/P15_PREP_BASELINE_FREEZE.md` | P15 EVIDENCE | P15 | `f678e083ca39543137cf24499cdd86895e5d5faf0b1dc7462156f105b555b8f6` | 基线冻结 |
| `docs/architecture/P15_PREP_GIT_BASELINE.md` | P15 EVIDENCE | P15 | `dd8608814fbce3c60882a1c50130706cc33af2ae372ad1c1277534dab6df1baa` | Git 基线 |
| `docs/architecture/P15_PREP_SCHEMA_BASELINE.md` | P15 EVIDENCE | P15 | `8e77cdb66a8a03c414671f53493f3b92f9382783a60a660fbe8f3e806a9163ad` | Schema 基线 |
| `docs/architecture/P15_SECURITY_GATE_PREP.md` | P15 EVIDENCE | P15 | `a3cfa60fc3fbc9ea7d1dd6545bec858943bd94db89b8e24b9c67bfe2bc5c1d5b` | 安全 Gate 准备 |
| `docs/architecture/P15_THEME_ANALYSIS.md` | P15 EVIDENCE | P15 | `fb7ccc571ae794663ef48ef92f6fe555a6196bb78abff04764ff210524ff267f` | 主题分析 |

### 1.4 P15 RELEASE (docs)（6）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `docs/architecture/P15_BASELINE_INTEGRITY_REPAIR_RECORD.md` | P15 RELEASE | P15 | `e842e34921436fde7326d06484ae86112dcf9c886397019c0f95f7742bdc0614` | Baseline 完整性修复记录（F-RP-01 / F-RP-03） |
| `docs/architecture/P15_COMMIT_TAG_GATE_REPORT.md` | P15 RELEASE | P15 | `3d93d845dd249dd032b5b5b0cfd4248aea512f4d75faea1ca2a0c37ae3686d20` | Commit + Tag Gate 报告（提交前定稿） |
| `docs/architecture/P15_RELEASE_EXCLUSIONS.md` | P15 RELEASE | P15 | `9820be2e05f978488008efa68137d067131be564a505e94c917a7b52b3bb2a97` | 排除清单（逐文件 + reason） |
| `docs/architecture/P15_RELEASE_GATE_REPORT.md` | P15 RELEASE | P15 | `c6b1316ce9e39b999adc8fe2f66e0d8256c108c30860eff733db419fd83cd256` | Release Gate 报告 |
| `docs/architecture/P15_RELEASE_PAYLOAD_MANIFEST.md` | P15 RELEASE | P15 | `自引用（写入后由 Final Gate 输出）` | 本 payload manifest（自引用） |
| `docs/architecture/P15_RELEASE_PREPARATION_REPORT.md` | P15 RELEASE | P15 | `968fd2f12b92f2f2d7e71115f1ca84daf8938f0630bf60209798d23b9a076e29` | Release Preparation 报告（Gate 后刷新） |
| `docs/architecture/P15_RELEASE_VERSION_DECISION.md` | P15 RELEASE | P15 | `3e3e84369d673a56898ebc653fb611ab8c6658c1369d0605a7e90dcf15d4d4e9` | 版本裁决与元数据同步（0.1.11） |

### 1.5 P15 GOVERNANCE（1）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `docs/architecture/PLATFORM_DECISION_LOG.md` | P15 GOVERNANCE | P15 | `9221b4d78b6543eb9d289593f15bf968da8e73ae62a546db8d0cb194ae5a5c83` | P15 governance authority append-only update（附录 T）· A–S 未改写 · 文件不可拆分 |

### 1.6 BASELINE INTEGRITY REPAIR（9）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `migrations_alembic/versions/0013_p10_event_audit.py` | BASELINE INTEGRITY REPAIR | P15 | `da1bdffd4ddd2202f1132557701d3fe23e8aeee035527561cbb1b4cc5b7a3937` | 历史 migration 纳入 committed tree（revision 语义未变 · F-RP-01） |
| `migrations_alembic/versions/0014_p11_triggers.py` | BASELINE INTEGRITY REPAIR | P15 | `3be9c8c092869c8d3ffb29bed7e755af5f4305861c420034c41e0f2836e0357f` | 历史 migration 纳入 committed tree（revision 语义未变 · F-RP-01） |
| `migrations_alembic/versions/0015_p12_indexes.py` | BASELINE INTEGRITY REPAIR | P15 | `94b0d22800c8971ef6968dfeb72a88c6ac11d467d17a2f741692598adaf98031` | 历史 migration 纳入 committed tree（revision 语义未变 · F-RP-01） |
| `migrations_alembic/versions/0016_open_p10_1_trust_boundary.py` | BASELINE INTEGRITY REPAIR | P15 | `10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544` | 历史 migration 纳入 committed tree（revision 语义未变 · F-RP-01） |
| `migrations_alembic/env.py` | BASELINE INTEGRITY REPAIR | P15 | `577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a` | migration identity（fail-closed）+ P0 fix（connection.rollback）· F-RP-03 |
| `alembic.ini` | BASELINE INTEGRITY REPAIR | P15 | `2eccf6473d859d0f3eb14aac60b75fe8fa23bcf902b4b341a92a0cfe1b831f5f` | 移除可执行 DSN · 与 env.py 配对 · F-RP-03 |
| `migrations_alembic/README.md` | BASELINE INTEGRITY REPAIR | P15 | `3c44245a805506e61dea24e65df7837f0a785c9ca423339d08464cdcdada1f2d` | 同一变更的子系统文档 · F-RP-03 |
| `.env.example` | BASELINE INTEGRITY REPAIR | P15 | `b95436542da3273709a746685e7fda8800a602aee4a323e737fdc22568718564` | 记录 UAP_MIGRATION_DATABASE_URL 键 · 基线文档 |
| `README.md` | BASELINE INTEGRITY REPAIR | P15 | `ef81a770286374aca2d0987cdf93cd3dbe9334d5e4278a44c2ffe9c69c8b5707` | 记录双 DSN 身份 · 基线文档 |

### 1.7 RELEASE METADATA（3）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `pyproject.toml` | RELEASE METADATA | P15 | `cb078a79739a77a008965f4f95e58655a389a30a022c6aae14f147a6f25abdfe` | Release Metadata Synchronization → 0.1.11 |
| `config/settings.py` | RELEASE METADATA | P15 | `4c3bb4519519b4fa359b8ca95172baa8729f8d2b8f8b4b6eaea1530225a5cc1c` | APP_VERSION 默认值 → 0.1.11 |
| `docker-compose.yml` | RELEASE METADATA | P15 | `2c70e0588216497a7534bc2c823a9990e9ae7009729707d52e9f0d4cb3103326` | APP_VERSION → 0.1.11 |

```text
table rows = 63
```

## 2. 分类说明

```text
P15 IMPLEMENTATION        = C-5 consumer 实现（apps/worker + services/consumer）
P15 TEST                  = P15 测试（逐文件 allowlist 执行）
P15 EVIDENCE              = 验收/决策/回溯证据
P15 RELEASE (docs)        = 本次 release 过程文档
P15 GOVERNANCE            = PLATFORM_DECISION_LOG.md（附录 T · append-only · 不可拆分）
BASELINE INTEGRITY REPAIR = 历史 Alembic 链与 migration runner 的仓库完整性修复
                            （revision semantics unchanged · historical source already
                             existing · required to restore committed Alembic graph）
RELEASE METADATA          = 版本元数据同步（0.1.11）
```

```text
0017_p13_seed.py 不作为 P15 migration（保持 P13 归属 · 不进入本 payload）
新建 Alembic revision = 0（0018+ = 0）
```

## 3. SELF-HASH RULE（P15 COMMIT + TAG GATE §10）

```text
SELF-HASH RULE =
  本 manifest 对**自身行**不写入 SHA256（该字段值为
  「自引用（写入后由 Final Gate 输出）」这一说明性文字，不是 hash）。
  即：self-hash field is EXCLUDED from the canonical hash set.

  ⇒ 不存在 SHA256(full file) == embedded SHA256 这种数学自引用的断言。

canonical hash set = manifest 中所有携带 64 位十六进制 SHA256 的行
  |canonical hash set| = (行总数 − 1)
  校验方式（独立、可复现）：
    1. 统计携带 64-hex SHA256 的行数 ⇒ 必须等于 行总数 − 1
    2. 逐行重新计算 sha256(磁盘文件) ⇒ 必须全部相等
    3. manifest 自身的完整性由 git commit object / annotated tag 背书，
       而不是由文件内部自证

违反任一条件 ⇒ P15 COMMIT = BLOCKED
```

## 4. 双向完整性（§32）

```text
A — Ownership → Manifest：所有 P15-owned 路径均已登记
B — Manifest → Ownership：每条 path 均有 ownership 证据

missing    = 0
orphan     = 0
unresolved = 0
candidate index simulation vs manifest = exact match
```

## 5. Candidate 形态（隔离临时 index 实测）

```text
Files Added    = 54
Files Modified = 10
Files Deleted  = 0
Payload total  = 64
64 files changed, 9021 insertions(+), 46 deletions(-)
非 payload 泄漏 = 0 · real staged = 0
```
