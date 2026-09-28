# P15 BATCH 2 — CLAIM / LEASE / HEARTBEAT / RECOVERY — RETROSPECTIVE EVIDENCE

```text
Evidence type            = RETROSPECTIVE RECONSTRUCTION
Contemporaneous artifact  = NOT AVAILABLE
Not original execution report
Reconstructed on         = 2026-09-28（Batch 4）
Reconstructed from       = 仓库现存源文件 + 现存测试 + 本轮实际重跑 + 只读 DB 证据
依据授权                 = BATCH 4 §6
```

> 本文件**不是**当时的原始执行报告。原始 Batch 2 执行时的命令输出 / 报告文件在仓库与
> 工作证据目录中均不存在（见 §5）。以下内容由**现存代码与测试的实测**重建。

---

## 1. 范围（Batch 2 = Claim / Lease / Heartbeat / Recovery）

```text
落盘位置 = services/consumer/claim.py（EventRepository + ClaimService）
        + kernel.py 中的冻结 SQL 文本（Batch 1 产物）
        + tests/integration/test_p15_claim.py（真库集成测试）
```

---

## 2. Source paths

```text
services/consumer/claim.py
services/consumer/kernel.py
tests/integration/test_p15_claim.py
tests/integration/runtime_testkit.py           （UAP_RUNTIME_TEST_DSN 身份约束）
tests/integration/alembic_testkit.py           （BASE_DSN · 仅 fixture provisioning）
docs/architecture/P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md（§7 · §9 · §10）
docs/architecture/PLATFORM_DECISION_LOG.md（附录 S · O-1）
```

---

## 3. Current hash（2026-09-28 实测）

```text
services/consumer/claim.py              sha256 = db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a
tests/integration/test_p15_claim.py     sha256 = 599a0550b10d7bfe8ca7db969cf7eae4235b2fb07f0156fb44ffc8f75a91d09b
```

```text
稳定性证据：claim.py 与 test_p15_claim.py 两个 hash 在 Batch 3 开始、Batch 3 结束、
Batch 4 开始三次独立采集中完全一致 ⇒ 自首次捕获以来未被改写。
```

---

## 4. Reconstructable test result（本轮实际重跑）

```text
命令    = python -m pytest tests/integration/test_p15_claim.py -p no:cacheprovider -q
DSN     = $env:UAP_RUNTIME_TEST_DSN = postgresql+psycopg://uap_runtime:uap_runtime@localhost:5432/uap_b1_test
结果    = 13 passed · 0 failed（Batch 4 实测）
DB 目标  = uap_b1_test（identity = uap_runtime · 缺省即 SKIP · 不回退）
净零     = 测试后 events 行数 = 0（fixture 建 / fixture 清）
```

可重建的语义（逐项已在测试中断言）：

```text
session-scoped：ClaimService 从不 commit（事务由 RuntimeDatabase.transaction() 拥有）
所有权判定：条件 UPDATE + rowcount == 1（DB 保证唯一所有权，非 Python 内存锁）
两 worker 并发 claim 不重叠（FOR UPDATE SKIP LOCKED + 条件 UPDATE）
O-1：claimed 且 lease_expires_at < now() ⇒ attempts < 10 → pending（attempts 不变）
                                      ⇒ attempts >= 10 → dead（reason lease_expired_max_attempts）
未过期租约不被回收
delivered / dead 为终局态
retryable → pending + attempts+1 + 确定性 backoff；attempts+1 >= 10 ⇒ 自动转 dead
错误分类经 PersistenceError 上抛（不吞异常）
production_allowlist() = EMPTY
```

---

## 5. Known limitations / What cannot be reconstructed

```text
1. 原始 Batch 2 执行报告文件不存在（P15_BATCH2_IMPLEMENTATION_REPORT.md /
   P15_BATCH2_CHANGE_MATRIX.md 在本轮开始时均不存在）⇒ BATCH 3 §1 引用了不存在的文件。
2. 原始命令行输出（stdout）、执行时间戳、执行者记录 —— 无留存，不可重建。
3. Batch 2 当时测试库的 audit_logs 行数快照 —— 无留存。
   （本轮实测基线：测试库 audit_logs = 1412 → 1655，见 Batch 4 测试报告 §5）
4. “当时是否按同一命令执行” 无法从产物证明；只能证明“以该命令执行现在通过”。
5. 本文件不构成 Evidence Freeze；治理上等价于“现存产物的可核验快照”。
```

---

## 6. 结论

```text
Batch 2 能力（claim/lease/heartbeat/recovery） = 现存且可核验 ⇒ PASS
Batch 2 原始 contemporaneous 证据               = 不存在（RETROSPECTIVE 替代）
Blocking 影响                                   = 0
```

