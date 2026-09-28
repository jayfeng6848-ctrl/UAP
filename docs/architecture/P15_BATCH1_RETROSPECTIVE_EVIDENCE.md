# P15 BATCH 1 — CONSUMER KERNEL — RETROSPECTIVE EVIDENCE

```text
Evidence type            = RETROSPECTIVE RECONSTRUCTION
Contemporaneous artifact  = NOT AVAILABLE
Not original execution report
Reconstructed on         = 2026-09-28（Batch 4）
Reconstructed from       = 仓库现存源文件 + 现存测试 + 本轮实际重跑
依据授权                 = BATCH 4 §6（retrospective reconstruction of missing Batch 1/2 evidence）
```

> 本文件**不是**当时的原始执行报告。原始 Batch 1 执行时的命令输出 / 报告文件在仓库与
> 工作证据目录中均不存在（见 §5），因此以下内容由**现存代码与测试的实测**重建。
> 任何“当时发生过什么”的陈述都被限定为“可由现存产物证明的部分”。

---

## 1. 范围（Batch 1 = Consumer Kernel）

```text
Batch 1 主题 = 纯逻辑 Consumer Kernel（无 I/O）
落盘位置     = services/consumer/kernel.py（+ services/consumer/__init__.py 导出）
```

对应 Contract / Decision：

```text
P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md（§4 生命周期 · §7 claim · §8 幂等 · §9 retry）
PLATFORM_DECISION_LOG.md 附录 R（P15-DEC-01…06）
PLATFORM_DECISION_LOG.md 附录 S（O-1…O-6 FROZEN）
```

---

## 2. Source paths（现存的唯一权威来源）

```text
services/consumer/kernel.py
services/consumer/__init__.py
tests/unit/test_p15_consumer_kernel.py
docs/architecture/P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md
docs/architecture/PLATFORM_DECISION_LOG.md
```

---

## 3. Current hash（2026-09-28 实测）

```text
services/consumer/kernel.py                 sha256 = d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769
services/consumer/__init__.py               sha256 = 32c146ff42af3490726d9aa56629366f12acad468bd4271017b44ff841700d19
tests/unit/test_p15_consumer_kernel.py      sha256 = aa4cd53f04179744712228ec57064b65cd41cc882b3fd90bf31344c60c3fd94f
```

```text
kernel.py 稳定性证据：该 hash 在 Batch 3 开始前的首次采集、Batch 3 结束、Batch 4 开始
三次独立采集中完全一致 ⇒ 可证明 Batch 1 的 kernel 产物自首次捕获以来未被改写。
tests/unit/test_p15_consumer_kernel.py 同样三次一致。
services/consumer/__init__.py 在 Batch 3 被修改过（docstring + worker 导出），
因此其当前 hash 不等于 Batch 1 当时的 hash —— 该项无法回溯（见 §5）。
```

---

## 4. Reconstructable test result（本轮实际重跑）

```text
命令    = python -m pytest tests/unit/test_p15_consumer_kernel.py -p no:cacheprovider -q
环境    = Python 3.13.14 · pytest 8.3.4 · rootdir = <repo>
结果    = 13 passed · 0 failed（Batch 4 实测）
DB 依赖  = 0（kernel 为纯逻辑 · 无 I/O）
D-01 依赖 = 0
```

可由现存源码重建的冻结语义（逐项已在测试中断言）：

```text
MAX_ATTEMPTS = 10                 （O-2）
backoff       = 5/10/20/40/80/160/320/600/600（cap = 600 · 无 640）
WORKER_PROCESS_COUNT = 1 · WORKER_CONCURRENCY = 4 · CLAIM_BATCH_SIZE = 10
LEASE_SECONDS = 120 · HEARTBEAT_SECONDS = 40     （O-4）
production_allowlist() = EMPTY                    （O-5）
EventHandlerSpec.eligible 需同时满足 producer evidence + authorization semantics
  + acceptance coverage + provable idempotency   （O-5 / O-6）
未知 event_type ⇒ UnsupportedEventType（terminal）
冻结 SQL 文本：CLAIM_SQL / HEARTBEAT_SQL / COMPLETE_DELIVERED_SQL /
  COMPLETE_PENDING_SQL / COMPLETE_DEAD_SQL / RECOVER_EXPIRED_SQL /
  RECOVER_EXPIRED_DEAD_SQL
```

---

## 5. Known limitations / What cannot be reconstructed

```text
1. 原始 Batch 1 执行报告文件不存在。§1 的 BATCH 3 指令曾要求读取
   P15_BATCH2_IMPLEMENTATION_REPORT.md / P15_BATCH2_CHANGE_MATRIX.md，二者同样缺失
   ⇒ 可判定 Batch 1/2 当时未产出 contemporaneous evidence 文档。
2. 原始命令行输出（stdout）、执行时间戳、执行者记录 —— 无留存，不可重建。
3. services/consumer/__init__.py 的 Batch 1 pre-image hash —— 不可重建（untracked 且已被修改）。
4. “当时是否按同一命令执行” 无法从产物证明；只能证明“以该命令执行现在通过”。
5. 本文件不构成 Evidence Freeze；它是 RETROSPECTIVE RECONSTRUCTION，
   在治理上等价于“现存产物的可核验快照”，不等价于原始执行证据。
```

---

## 6. 结论

```text
Batch 1 能力（consumer kernel）     = 现存且可核验 ⇒ PASS
Batch 1 原始 contemporaneous 证据    = 不存在（RETROSPECTIVE RECONSTRUCTION 替代）
Blocking 影响                        = 0（不影响 Contract 满足性；仅影响证据链完备性措辞）
```

