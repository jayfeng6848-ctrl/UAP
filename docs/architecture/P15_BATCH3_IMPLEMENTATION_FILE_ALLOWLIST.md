# P15 BATCH 3 — IMPLEMENTATION FILE ALLOWLIST

日期：2026-09-28
范围：P15 Implementation Batch 3（Worker Entry / Lifecycle / Shutdown / Bounded Concurrency）
性质：只记录 Batch 3 的写入边界与白名单；不含任何 implementation 结果判定

---

## 1. 授权边界（依 BATCH 3 指令 §0）

```text
P15 Implementation Batch 3 = AUTHORIZED
Repository Write Access    = GRANTED

写入范围：
services/consumer/**
tests/**                    仅 P15 Batch 3 测试/support
docs/architecture/P15_BATCH3_*
```

本 Batch 的 white list 只覆盖上表；任何不在此表内的路径一律视为 out-of-scope。

---

## 2. 实际扫描结果（Batch 3 开始前的现状）

```text
services/consumer/
  __init__.py     存在（Batch 1 建立 · 当时 docstring 仍写着 worker 未实现）
  kernel.py       存在（Batch 1 · sha256 = d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769）
  claim.py        存在（Batch 2 · sha256 = db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a）
  worker.py       存在（前一轮创建的 pre-image · sha256 = 5f5d02b9c5e9134e9adf43afe8056a27ab7bb1ca6f3cc7880a0fea1deeef9063）

runtime lifecycle / configuration / application startup / observability /
DB connection：
  未新增文件。Worker 的 lifecycle、config、observability 与 DB 依赖全部由
  services/consumer/worker.py 承载，通过注入式依赖与 Batch 2 ClaimService 对接。
```

结论：本轮不需要新建 `runner.py`、lifecycle adapter 或 worker config adapter ——
按指令“只有确有必要才新增，不创建空壳”，不新增任何空壳模块。

---

## 3. Batch 3 写入白名单（实际使用）

| # | 路径 | 分类 | 说明 |
|---|---|---|---|
| 1 | `services/consumer/worker.py` | modified（重写） | Batch 3 主体：entry / lifecycle / poll / claim orchestration / bounded concurrency / heartbeat / recovery / shutdown / drain / failure handling / observability |
| 2 | `services/consumer/__init__.py` | modified（docstring + export） | 修正过期的 “Not yet implemented: … worker loop” 描述；导出 worker 公开符号 |
| 3 | `tests/unit/test_p15_worker.py` | modified（重写） | Batch 3 单元测试（离线，注入式依赖，不连数据库） |
| 4 | `docs/architecture/P15_BATCH3_IMPLEMENTATION_FILE_ALLOWLIST.md` | new | 本文件 |
| 5 | `docs/architecture/P15_BATCH3_CHANGE_MATRIX.md` | new | 变更矩阵 |
| 6 | `docs/architecture/P15_BATCH3_IMPLEMENTATION_REPORT.md` | new | 实施报告 |
| 7 | `docs/architecture/P15_BATCH3_TEST_EXECUTION_REPORT.md` | new | 测试执行报告 |
| 8 | `docs/architecture/P15_BATCH3_TEST_EXECUTION_MANIFEST.md` | new | 逐文件测试清单（CF-C-4） |

---

## 4. 明确排除（Batch 3 未写入）

```text
services/consumer/kernel.py          未修改（sha256 与 Batch 1 一致）
services/consumer/claim.py           未修改（sha256 与 Batch 2 一致）
tests/integration/test_p15_claim.py  未修改
tests/unit/test_p15_consumer_kernel.py 未修改
tests/conftest.py                    未修改（由 P14 遗留的既有 modified 状态，非本轮改动）
migrations_alembic/**                未修改
apps/**                              未创建
config/**                            未修改
PLATFORM_DECISION_LOG.md             未修改
任何 P13 / P14 冻结文档              未修改
```

---

## 5. 边界结论

```text
new schema        = 0
migration         = 0
DDL               = 0
formal DB DML     = 0
GRANT / REVOKE    = 0
ROLE change       = 0
new principal     = 0
new ACL subject   = 0
new action        = 0
Stage 2 change    = 0
P14 change        = 0
D-01 repair       = 0
commit / tag / push = 0
```

