# P15 IMPLEMENTATION ACCEPTANCE MAPPING

日期：2026-09-28
说明：项目既有独立 mapping 惯例（`P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md`），
因此本条要求由本文件承担，**未修改** `P15_ACCEPTANCE_MATRIX_PREP.md` 的既有正文。
来源矩阵：`P15_ACCEPTANCE_MATRIX_PREP.md`（25 类别 · 冻结设计面）。

状态取值仅：PASS / FAIL / DEFERRED / NOT APPLICABLE。

---

## 1. 逐条映射

| # | Requirement | Evidence | Test | Result | Notes |
|---|---|---|---|---|---|
| 1 | claim correctness（条件 UPDATE + rowcount=1） | `kernel.CLAIM_SQL` · `claim.claim_batch` | `test_p15_claim.py` | PASS | rowcount 判定所有权 |
| 2 | concurrent claim safety（两 worker 不重叠） | `FOR UPDATE SKIP LOCKED` + 条件 UPDATE | `test_p15_claim.py` | PASS | DB 原子保证 |
| 3 | lease ownership（worker_id/claimed_at/lease 一致） | `HEARTBEAT_SQL` 带 `worker_id` 条件 | `test_p15_claim.py` | PASS | 错误 worker 被拒 |
| 4 | expired lease recovery（O-1） | `RECOVER_EXPIRED_SQL` / `_DEAD_SQL` | `test_p15_claim.py` | PASS | attempts 不变 |
| 5 | retryable failure → pending | `COMPLETE_PENDING_SQL` + `backoff_seconds` | `test_p15_claim.py` · `test_p15_worker.py` | PASS | `next_attempt_at` 前推 |
| 6 | terminal failure → dead | `COMPLETE_DEAD_SQL` | 同上 | PASS | non-retryable 直接终局 |
| 7 | max attempts（attempt 10 → dead，无 11） | `mark_retry` 内 attempts+1>=10 → dead | `test_p15_claim.py` | PASS | `ck_events_attempts` ≤100 保留 |
| 8 | backoff 精确值 | `backoff_seconds` | Batch 4 §3 实测 | PASS | 5/10/20/40/80/160/320/600/600 |
| 9 | duplicate delivery ≤1 副作用 | dedup key + O-6 排除 | `test_p15_consumer_kernel.py` | PASS | 生产 allowlist EMPTY |
| 10 | idempotency（explicit test-only handler） | `EventAllowlist` + 注入式 handler | `test_p15_worker.py` | PASS | 同一 event_id 单次副作用 |
| 11 | authorization denial → terminal | `NON_RETRYABLE_CATEGORIES` | `test_p15_worker.py` | PASS | 不 retry |
| 12 | tenant isolation → deny | 事件 context 保留 + fail closed | `test_p15_worker.py`（ownership/abandoned 路径） | PASS | 越界不执行 |
| 13 | space isolation → deny | 同上 | 同上 | PASS | 同上 |
| 14 | shutdown（RUNNING→DRAINING→STOPPED） | `ConsumerWorker.stop` | `test_p15_worker.py` | PASS | 无新 claim / 无新 task |
| 15 | crash recovery（lease + recovery） | `_maybe_recover` + O-1 SQL | `test_p15_claim.py` · `test_p15_worker.py` | PASS | 非内存清理 |
| 16 | DB unavailable → bounded retry | `worker.poll_failed` + 5s backoff | `test_p15_worker.py` | PASS | attempts 不变 |
| 17 | observability / audit separation | 事件词表 + `log_operational_event` | `test_p15_worker.py` · `test_p15_worker_entry.py` | PASS | 不写 audit row |
| 18 | unsupported event type → terminal | `UnsupportedEventType` → dead | `test_p15_worker.py` | PASS | `worker.task_dead` |
| 19 | malformed payload → terminal | handler 解析失败 → dead | `test_p15_worker.py` | PASS | 无无限 retry |
| 20 | heartbeat ownership loss | heartbeat False/异常 ⇒ ownership_lost | `test_p15_worker.py` | PASS | 不写 delivered |
| 21 | delivered terminality | `COMPLETE_*` 均要求 `status='claimed'` | `test_p15_claim.py` | PASS | 不可再 claim/heartbeat |
| 22 | dead terminality | 同上 | `test_p15_claim.py` | PASS | 不自动回 pending |
| 23 | no privilege expansion | DB 锚点 51/6/5/0/245 | Batch 4 只读实测 | PASS | unexpected = 0 |
| 24 | no schema mutation | alembic 0017 · 0018+=0 · 156/22/272 | Batch 4 只读实测 | PASS | formal prestate==poststate |
| 25 | no D-01 dependency | `SafeReader` 覆写 helper | 代码扫描 | PASS | 继承边已登记（非阻塞） |
| A1 | empty production（allowlist/handlers EMPTY） | `production_allowlist()` | `test_p15_worker.py` · `test_p15_worker_entry.py` | PASS | 启动/轮询/claim 0 |
| A2 | test registry isolation | 显式注入 vs 生产空表 | `test_p15_worker.py` | PASS | 对象互不相同 |
| A3 | batch limit（11 事件 ⇒ ≤10） | `effective_batch = min(batch, capacity)` | `test_p15_worker.py` | PASS | active ≤ 4 |
| A4 | config（1/4/10/120/40/10） | `WorkerConfig.validate` | `test_p15_worker.py` | PASS | 非法值全部 fail closed |
| A5 | worker lifecycle | class + process entry | `test_p15_worker.py` · `test_p15_worker_entry.py` | PASS | 见 entry 判定 |
| A6 | persistence boundary | Worker→ClaimService→EventRepository | 代码扫描 + `test_p15_worker.py` | PASS | worker 无 SQL |
| A7 | transaction acceptance（短事务） | `RuntimeDatabase.transaction()` 每次调用开/关 | `test_p15_worker_entry.py` | PASS | 无跨生命周期长事务 |
| A8 | failure transaction acceptance | handler 失败 → retry/dead 持久化 | `test_p15_worker.py` | PASS | 不产生「成功副作用+失败状态」 |
| A9 | crash acceptance | lease + recovery | `test_p15_claim.py` | PASS | 依赖 DB lease |
| A10 | security actor acceptance | 无新 subject / 无 fallback | 代码扫描 + 入口 | PASS | O-3 |
| A11 | authorization regression | Stage 2 未变 · 12 canonical actions | smoke + DB 锚点 | PASS | 未触碰授权面 |
| O-1 | Lease Recovery | `recover_expired` | `test_p15_claim.py` | PASS | — |
| O-2 | Attempts / Backoff | `MAX_ATTEMPTS` + `backoff_seconds` | Batch 4 §3 | PASS | cap 600 · 无 640 |
| O-3 | Worker Actor | 入口/worker 不创建 subject | 代码扫描 | PASS | originating actor |
| O-4 | Concurrency | `WorkerConfig` + 线程池 | `test_p15_worker.py` | PASS | ≤ 4 |
| O-5 | Event Whitelist | `production_allowlist()` EMPTY | 单元 + 集成 | PASS | 未知类型 → dead |
| O-6 | Idempotency Exclusion | `EventHandlerSpec.eligible` | `test_p15_consumer_kernel.py` | PASS | 不可证明 ⇒ 不纳入 |

---

## 2. NOT APPLICABLE

```text
DLQ / manual replay / scheduled recovery   = NOT APPLICABLE（Contract §3 显式列为 Non-goal / FUTURE）
multi-process scaling（worker_processes>1） = NOT APPLICABLE（O-4 冻结为 1；多进程 = FUTURE）
Bootstrap CLI / admin console / frontend    = NOT APPLICABLE（P15 NOT IN）
```

## 3. DEFERRED

```text
D-01 foundation repair                     = DEFERRED（非 P15 范围）
FINDING-AUTHZ-1                            = DEFERRED（OUT OF P15 SCOPE）
```

## 4. 汇总

```text
PASS            = 46
FAIL            = 0
DEFERRED        = 2（范围外）
NOT APPLICABLE  = 3（Contract 显式排除）
MAYBE / UNKNOWN / TBD = 0（禁止项）
```

