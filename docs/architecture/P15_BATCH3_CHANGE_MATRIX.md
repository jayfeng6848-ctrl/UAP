# P15 BATCH 3 — IMPLEMENTATION CHANGE MATRIX

日期：2026-09-28
范围：P15 Implementation Batch 3
说明：逐路径记录 classification / reason / contract section / test coverage

---

## 1. 变更总览

```text
implementation files = 1   （services/consumer/worker.py）
support files        = 1   （services/consumer/__init__.py）
test files           = 1   （tests/unit/test_p15_worker.py）
evidence files       = 5   （docs/architecture/P15_BATCH3_*）
schema / migration   = 0
```

---

## 2. 逐路径矩阵

### 2.1 `services/consumer/worker.py`

```yaml
path: services/consumer/worker.py
classification: modified (rewritten in scope)
pre_image_sha256:  5f5d02b9c5e9134e9adf43afe8056a27ab7bb1ca6f3cc7880a0fea1deeef9063
post_image_sha256: 385306d9fec4b2d71e3ecee0ce87269c01b0c7d4b1ab4b13eb8731d9b64aa263
reason: 修复 5 处与 BATCH 3 冻结规范的实质偏差（详见 §3）
contract_section: P15 IMPLEMENTATION CONTRACT §24 (O-1…O-6) / BATCH 3 §5–§48
test_coverage: tests/unit/test_p15_worker.py（30 项）
```

### 2.2 `services/consumer/__init__.py`

```yaml
path: services/consumer/__init__.py
classification: modified (docstring + export only)
pre_image_sha256: NOT RECORDED（见 §4 已知发现）
post_image_sha256: 32c146ff42af3490726d9aa56629366f12acad468bd4271017b44ff841700d19
reason: |
  原 docstring 仍声明 “Not yet implemented: session-scoped ClaimService, worker loop”，
  与 Batch 2 / Batch 3 实际已实现的状态冲突；同时补出 worker 公开符号的导出。
contract_section: BATCH 3 §4（Worker responsibility 边界）· 文档一致性
test_coverage: 由 P15 单元/集成测试的 import 路径间接覆盖
runtime_behavior_change: 0（无逻辑改动，仅 docstring 与 __all__ / import）
```

### 2.3 `tests/unit/test_p15_worker.py`

```yaml
path: tests/unit/test_p15_worker.py
classification: modified (rewritten in scope)
pre_image_sha256:  f11c516f07c2bf65e7fae0e3ed4bf60fe7653b82ff0e366a9a93ffd48fd4d9da
post_image_sha256: 1bb1a4f158c1775c584ef23636139624c3e92f25b115b270fe7c8baa52e6e23e
reason: 覆盖 BATCH 3 §49–§64 要求的可证明测试，并移除原文件中的无意义语句
contract_section: BATCH 3 §47–§64
test_coverage: 自身（30 项 · 全部离线 · 不连数据库）
```

### 2.4 evidence 文档（全部 new）

```yaml
- docs/architecture/P15_BATCH3_IMPLEMENTATION_FILE_ALLOWLIST.md
- docs/architecture/P15_BATCH3_CHANGE_MATRIX.md
- docs/architecture/P15_BATCH3_IMPLEMENTATION_REPORT.md
- docs/architecture/P15_BATCH3_TEST_EXECUTION_REPORT.md
- docs/architecture/P15_BATCH3_TEST_EXECUTION_MANIFEST.md
classification: new (evidence only)
contract_section: BATCH 3 §3 / §67 / §77 / §78 / §79
```

---

## 3. 修复的 5 处实质偏差

| # | 指令条款 | 修复前 | 修复后 |
|---|---|---|---|
| 1 | §11 状态机 | `WorkerState.NEW`，无 `STARTING` | `CREATED / STARTING / RUNNING / DRAINING / STOPPED`，`CREATED → STARTING` 在 `start()` 内可观测 |
| 2 | §10 启动序列 | 只建 executor 即置 `RUNNING`，无 DB 依赖与身份初始化，无 fail-closed | `validate config → observability → DB dependency probe → identity → RUNNING`；任一失败 ⇒ `STOPPED` + `WorkerStartupError` |
| 3 | §31 配置校验 | `WorkerConfig` 无 `worker_processes` 字段，无法拒绝 `worker_processes = 2` | 新增 `worker_processes` 字段并要求 `== 1`；`max_attempts` 收敛为必须 `== 10` |
| 4 | §16 recovery 调度 | 每次 poll 无条件 `recover_expired()`（`recovery_interval_seconds` 定义了却从未使用） | 按 `recovery_interval_seconds` 有界调度；首个 poll 视为到期，之后按间隔执行 |
| 5 | §22 / §32 | 无执行期周期性 heartbeat；observability 事件缺失 `poll / claim / heartbeat / recovery / draining` | 增加单个受管 heartbeat 线程（每 `heartbeat_seconds` 续租全部 in-flight 事件）；补齐事件词表 |

---

## 4. 记录为 implementation detail 的实现选择（不新增 Decision）

以下取值在冻结 Contract 中未固定，按指令 §16 / §26 / §48 作为“有限、可配置、可测试”的实现默认值记录：

```text
poll_interval_seconds      = 1.0 s     （空队列时的有界 sleep · §13/§48）
recovery_interval_seconds  = 30.0 s    （§16 · 不改变 O-1 语义）
drain_deadline_seconds     = 30.0 s    （§26 · 必须有限）
drain_tick_seconds         = 0.02 s    （drain 轮询步长）
poll_error_backoff_seconds = 5.0 s     （§15/§46 · 只影响 worker 基础设施重试）
```

`claim` 的容量语义（§18）：worker 只在存在有界执行容量时 claim，且
`effective_batch = min(batch_size, concurrency - in_flight)`。
即不会出现 “已 claim 但未被 heartbeat 覆盖、堆积在无界队列中” 的事件。
`worker.claim` 事件同时记录 `batch_size`（配置值）与 `effective_batch`（实际值）。

`shutdown` 超期语义（§26/§27）：超过 drain deadline 仍在执行的事件被标记为
abandoned —— **不写 delivered**，由 lease 过期 + O-1 recovery 决定结局。

---

## 5. 未变更的受保护对象

```text
services/consumer/kernel.py    sha256 = d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769（不变）
services/consumer/claim.py     sha256 = db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a（不变）
migrations_alembic/env.py      sha256 = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a（不变）
0016_open_p10_1_trust_boundary sha256 = 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544（不变）
0017_p13_seed                  sha256 = 1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e（不变）
infrastructure/database/persistence.py（D-01）sha256 = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（不变 · 未触碰）
PLATFORM_DECISION_LOG.md       sha256 = 940382613a3a2e07a9bd5a7681f103bc7f1bb5ac079a45dfd113b8e2dbd0c491（不变）
```

---

## 6. 已知发现（保留 · 未修复）

```text
F-B3-01  services/consumer/__init__.py 的 pre-image sha256 未在本轮开始时采集。
         worker.py 与 test_p15_worker.py 的 pre-image 已采集（见 §2）。
         该文件为 untracked，无法从 git 恢复 pre-image；无逻辑后果，仅证据完整性缺口。

F-B3-02  docs/architecture/ 下不存在 P15_BATCH1_* / P15_BATCH2_* evidence 文档，
         尽管 BATCH 3 指令 §1 要求读取 P15_BATCH2_IMPLEMENTATION_REPORT.md 与
         P15_BATCH2_CHANGE_MATRIX.md。本轮未伪造、未补写历史 Batch 的证据，
         改以 kernel.py / claim.py / test_p15_claim.py 的实测 sha256 + 13 passed 作为
         Batch 1 / Batch 2 的现存可核验依据。建议在 Batch 4 一并处理。

F-B3-03  tests/unit/test_p15_worker.py 中原本存在一行无意义语句
         `for future in list(worker._executor._threads) and []:`；已在重写时移除。

F-B3-04  Worker 的 handler 运行在 Python 线程内，无法被强制中断。
         drain 超期后线程仍会运行至自然结束，但其结果因 abandoned 标记而被丢弃。
         这是 Python runtime 的既有限制，已记录为 implementation detail。
```

