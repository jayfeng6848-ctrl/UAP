# P15 IMPLEMENTATION REPORT（Consolidated · Batch 1–4）

主题：C-5 Events / Outbox Consumer — 完整实现报告
日期：2026-09-28
基线：HEAD `15feebadeecd6f7d90e81569c3e869bc20cb18c5` · tag `UAP-V0.1.10-P14-RUNTIME-SLICE` · migration `0017_p13_seed`
性质：Batch 1–3 的实现已在各自报告中记录；本文件为**跨 Batch 汇总**，不替代逐 Batch evidence。

---

## 1. 实现范围（依 Contract §2 IN）

```text
apps/worker/**            专用 consumer 入口            （Batch 4 最小补齐）
services/** consumer       claim / lease / heartbeat / retry / idempotency / observability
infrastructure/**          仅复用（未新增 engine）
对应测试                    逐文件 allowlist
```

NOT IN（未实现 · 未触碰）：frontend · AI feature activation · admin console ·
bootstrap CLI · D-01 repair · /ready redesign · audit redesign ·
dead-letter queue · manual replay · scheduled recovery。

---

## 2. 分级实现清单

| Batch | 主题 | 产物 | 状态 |
|---|---|---|---|
| 1 | Consumer Kernel（纯逻辑） | `services/consumer/kernel.py` | PASS（见 retrospective evidence） |
| 2 | Claim / Lease / Heartbeat / Recovery | `services/consumer/claim.py` | PASS（见 retrospective evidence） |
| 3 | Worker Entry / Lifecycle / Shutdown / Bounded Concurrency | `services/consumer/worker.py` | PASS（见 P15_BATCH3_*） |
| 4 | Full Acceptance + Cross-Wave Regression | 本文件 + Acceptance Report + Entry 补齐 | PASS |

---

## 3. 运行期数据流（最终形态）

```text
apps/worker/main.py（进程入口 · adaptation only）
    │  load settings -> RuntimeApplication.start()（既有 P14 引导）
    ▼
ConsumerWorker（services/consumer/worker.py · 无 SQL）
    │  with claim_service_factory() as service   ← 短事务
    ▼
ClaimService（services/consumer/claim.py · session-scoped · never commits）
    │  EventRepository(SafeReader)
    ▼
RuntimeDatabase.transaction()（infrastructure/database/runtime.py）
    ▼
public.events（0017 既有 outbox · 无新 schema）
```

```text
Worker → ClaimService → EventRepository      = 唯一持久化路径
Worker → raw SQL                             = 0
handler → service / use-case                 = 约定（当前生产 handler = 0）
```

---

## 4. 关键语义（最终值）

```text
worker_processes = 1 · concurrency = 4 · batch_size = 10
lease = 120s · heartbeat = 40s · max_attempts = 10
backoff = min(5 * 2^(attempt-1), 600) → 5/10/20/40/80/160/320/600/600（无 640）
status 状态机 = pending → claimed → delivered | pending（retry）| dead（terminal）
O-1 lease 回收 = attempts<10 → pending（attempts 不变）；attempts>=10 → dead
production allowlist = EMPTY · production handler registry = EMPTY
```

实现细节（非 Decision）：poll interval 1.0s · recovery interval 30.0s ·
drain deadline 30.0s · poll error backoff 5.0s · 单个受管 heartbeat 线程 ·
claim 容量感知（`effective_batch = min(batch_size, concurrency - in_flight)`）。

---

## 5. 进程入口（Batch 4 最小补齐）

```text
契约依据  = P15_IMPLEMENTATION_PREP §Implementation scope（IN）: `apps/worker/**`（专用 consumer 入口）
           + P15 Contract §2 IN（实现载体）
P14 归属  = P14_RUNTIME_IMPLEMENTATION_FILE_INVENTORY.md 明确将 apps/worker/main.py 列为
           “generic background scheduler；Contract 未要求 ⇒ 不自动纳入”
           + P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md 将其列为 OUT OF SCOPE
           ⇒ 修改 apps/worker/** 属 P15 范围，不构成 P14 semantic modification
变更      = apps/worker/main.py 由 STEP 0 placeholder 改为真实 consumer 入口
入口序列  = load config → runtime DB 依赖（RuntimeApplication.start）
           → build_worker → install SIGINT/SIGTERM → poll → drain → exit
禁止项    = 未引入 Celery / broker / scheduler / process manager / 新框架
           = 未新增 security principal / schema / grant / role
```

---

## 6. Fail-closed 与错误语义

```text
startup 失败（DB 不可达 / principal 断言失败） ⇒ exit code 1 · 不启动半初始化 worker
config 非法（O-4 越界）                      ⇒ exit code 2 · 不回落不安全默认值
正常停机（SIGINT/SIGTERM）                   ⇒ exit code 0 · 有界 drain
handler retryable                            ⇒ pending + attempts+1 + deterministic backoff
handler 非 retryable / 未知异常               ⇒ dead（terminal）
unknown event_type                           ⇒ dead（unsupported_event_type）
drain 超期                                   ⇒ abandoned（绝不写 delivered）· 交 lease + O-1
```

---

## 7. 未变更 / 未触碰

```text
migrations_alembic/**（含 env.py）              未修改
0016 / 0017                                    未修改
infrastructure/database/persistence.py（D-01）  未修改（DEFERRED）
services/reads.py                              未修改（P14 Wave 2 既有文件）
PLATFORM_DECISION_LOG.md 附录 O–S               未修改（仅 append 附录 T）
apps/api/**                                    未修改
P13 / P14 冻结文档                              未修改
```

---

## 8. 结论

```text
P15 IMPLEMENTATION = PASS（Batch 1–4 全部完成并验收）
P15 ACCEPTANCE     = PASS（见 P15_IMPLEMENTATION_ACCEPTANCE_REPORT.md）
Release / Commit / Tag / Push = 未执行（FORBIDDEN）
```

