# P15 BATCH 3 — IMPLEMENTATION REPORT

主题：C-5 Events / Outbox Consumer — Worker Entry / Lifecycle / Shutdown / Bounded Concurrency
日期：2026-09-28
基线：HEAD `15feebadeecd6f7d90e81569c3e869bc20cb18c5` · tag `UAP-V0.1.10-P14-RUNTIME-SLICE` · migration `0017_p13_seed`
结论：**P15 BATCH 3 = PASS**（implementation + regression 已执行；Batch 4 未执行）

---

## 1. Worker

```text
类            services/consumer/worker.py :: ConsumerWorker
职责          configuration validation / startup / poll / claim / bounded scheduling /
              heartbeat coordination / execution orchestration / retry-finalize /
              lease recovery / shutdown / drain / observability
不负责        business rules / authorization policy / schema / credential / identity /
              device-session / bootstrap / migration / ACL
SQL 所有权    0（不新增 SQL / ORM query / 分散事务；全部经 Batch 2 ClaimService）
```

Event 通过注入的 `claim_service_factory` 取得，handler 通过闭合 allowlist 解析；
生产 allowlist 默认 `production_allowlist()` = EMPTY。

---

## 2. Lifecycle / Startup

```text
状态            CREATED → STARTING → RUNNING → DRAINING → STOPPED
失败路径        STARTING → STOPPED（fail-closed）
```

`start()` 顺序严格按 §10：

```text
validate config
  ↓
initialize observability（发出 worker.startup）
  ↓
initialize runtime DB dependency（dependency_probe · 缺省走 claim_service_factory 开一次连接）
  ↓
initialize worker identity（发出 worker.identity · process-scope worker_id）
  ↓
mark worker RUNNING（发出 worker.running）
  ↓
启动 poll loop（run_once / run_until_stopped）
```

任一步失败 ⇒ 状态置 `STOPPED`，发出 `worker.startup_failed`，抛 `WorkerStartupError`；
不会留下部分初始化的 worker，也不存在 fallback 到不安全默认值的路径。

重启安全（§12/§47）：同一实例重复 `start()` 抛 `ValueError`；`STOPPED → RUNNING`
不是合法迁移。多进程 supervisor / auto-scale / 分布式调度 **未实现**（FUTURE）。

---

## 3. Configuration

```text
worker_processes = 1      （!= 1 拒绝）
concurrency      = 4      （> 4 拒绝）
batch_size       = 10     （> 10 拒绝）
lease_seconds    = 120    （<= 0 拒绝）
heartbeat_seconds= 40     （<= 0 或 >= lease 拒绝）
max_attempts     = 10     （!= 10 拒绝）
```

非法取值一律 fail closed（`WorkerConfigurationError`），不回落默认值。

---

## 4. Poll / Claim Orchestration

```text
while RUNNING:
    recover expired claims when scheduled
    claim bounded batch（仅在有界容量可用时）
    schedule bounded tasks
    wait for capacity（有界 sleep，避免 busy-loop）
```

```text
poll_interval_seconds = 1.0 s（空队列时的有界 sleep）
poll 失败 ⇒ worker.poll_failed + POLL_ERROR_BACKOFF_SECONDS(5.0 s)
          ⇒ 不触碰 event.attempts（poll failure ≠ event execution failure）
effective_batch = min(batch_size, concurrency - in_flight)
```

空队列：claim 返回 0，worker 保持 `RUNNING`、sleep、继续；不退出、不报错、不 busy-spin。

---

## 5. Bounded Concurrency

```text
ThreadPoolExecutor(max_workers = concurrency = 4)
active handler 峰值 <= 4
claim 上限 <= min(batch_size, 可用容量)
```

不存在无界 task 创建、不存在 gather 整个队列、不存在持久的无界内存排队。

---

## 6. Heartbeat Coordination / Ownership Lost

每个 Worker 只有 **一个** 受管 heartbeat 线程（`p15-heartbeat`，daemon），按
`heartbeat_seconds` 为全部 in-flight 事件续租；执行开始前先做一次所有权确认。

```text
heartbeat 返回 False      → OWNERSHIP_LOST
heartbeat 抛异常          → 不得假设所有权（§43）⇒ 同样按 OWNERSHIP_LOST 处理
OWNERSHIP_LOST            ⇒ 不写 delivered、不覆盖 event、停止正常 finalize
drain 期间                ⇒ heartbeat 继续，直到任务 finalize 或所有权丢失
```

---

## 7. Recovery

```text
recover_expired() 按 recovery_interval_seconds = 30.0 s 有界调度（首个 poll 视为到期）
不改变 O-1 语义：attempts < 10 → pending（attempts 不变）；attempts >= 10 → dead
```

---

## 8. Shutdown / Drain / Crash Semantics

```text
RUNNING → DRAINING：停止新 claim、停止新 task 调度、允许有界 active task 完成
DRAINING → STOPPED：停止 heartbeat 线程 → 关闭 executor → worker.stopped
```

```text
drain_deadline_seconds = 30.0 s（有限 · 默认）；测试可覆盖
超期仍在执行 ⇒ 标记 abandoned + worker.drain_deadline_exceeded
             ⇒ 绝不 mark delivered；由 lease 过期 + O-1 recovery 决定结局
```

硬崩溃语义：worker 进程消失后无需自己清理；claimed 事件由 lease 过期 +
下一轮 `recover_expired()` 按 O-1 恢复。worker 不承担 crash 后的自我清理职责。

---

## 9. Failure Handling

| 失败类别 | 行为 | 可观测事件 |
|---|---|---|
| startup failure | fail closed，置 `STOPPED`，抛 `WorkerStartupError` | `worker.startup_failed` |
| poll failure | 有界 backoff，不增加 attempts，保持 RUNNING | `worker.poll_failed` |
| claim failure | 同 poll failure 路径 | `worker.poll_failed` |
| heartbeat failure | 视为所有权丢失，不继续盲目执行 | `worker.heartbeat_failed` / `worker.ownership_lost` |
| finalize failure | 绝不宣称成功；交由 lease / recovery | `worker.finalize_failed` |
| handler 非 retryable / 未知异常 | terminal（dead） | `worker.task_dead` |
| handler retryable | pending + 确定性 backoff | `worker.task_retry` |
| unknown event type | dead（O-5） | `worker.task_dead`（reason `unsupported_event_type`） |
| drain 超期 | abandoned，不写 delivered | `worker.drain_deadline_exceeded` / `worker.task_abandoned` |

---

## 10. Actor / Tenant / Space

```text
worker 不创造 system / worker / platform subject（O-3）
handler 需要 actor ⇒ 使用事件原始 originating actor
tenant / space ⇒ 保留事件 context；context 无效 ⇒ fail closed（dead）
授权仍然经过 Stage 2，worker 不绕过授权
worker_id 是 process-scope 标识，不是 ACL identity
```

---

## 11. Observability / Audit Separation

```text
worker.startup / worker.identity / worker.running / worker.poll / worker.claim /
worker.recovery / worker.task_start / worker.task_success / worker.task_retry /
worker.task_dead / worker.heartbeat / worker.heartbeat_failed /
worker.ownership_lost / worker.draining / worker.stopped /
worker.startup_failed / worker.poll_failed / worker.finalize_failed /
worker.drain_deadline_exceeded / worker.task_abandoned

metadata = worker_id / event_id / event_type / attempt / state（无 secret）
```

空队列不产生 per-second log 洪泛：`worker.poll` 仅在产生实际工作时发出。

```text
operational log ≠ audit_logs（未修改 audit schema / semantics）
```

---

## 12. Production Allowlist / Test-only Isolation

```text
production_event_allowlist = EMPTY
production_handler_registry = EMPTY
```

依据（只读证据）：仓库内不存在 event producer；`public.events` 行数 = 0。
因此 production worker 的合法状态是：能启动、能轮询、claim 到 0 条业务事件。

测试通过显式注入 `EventAllowlist` + test-only handler 覆盖执行路径；生产模块不导入
测试注册表。两者在测试中被断言为互相独立的对象。

---

## 13. DB Boundary

```text
worker 自身无 SQL；DB 访问全部经 Batch 2 ClaimService（session-scoped · never commits）
claim session 在 handler 执行前结束（不跨 handler 持有 claim 事务）
handler 使用各自 request/task 级事务边界
整个 worker 生命周期绝不置于单一长事务
```

---

## 14. Security Boundary（实测）

```text
roles                     = 6（uap / uap_app / uap_bootstrap / uap_migrator / uap_runtime / uap_seed）
grant fingerprint         = uap_runtime 51 / uap_bootstrap 6 / uap_app 5 / uap_seed 0 / uap_migrator 245
default_acl               = 0
user-defined membership   = 0
public schema CREATE      = false（全部非超级用户角色）
public schema USAGE       = true
ownership residual        = 0
pg_class_public           = 156
pg_proc_public            = 22
pg_trigger_total          = 272
C2 md5                    = 185e95be8bc4304edbcd3f4d5cda1eff
tg_acl_subject_types_protect = enabled（tgenabled = O）
P13 seed                  = acl_subject_types 3 / permissions 12 / role_permissions 12
users                     = 0
events                    = 0
agents family             = 0
alembic_version           = 0017_p13_seed
0018+                     = 0
正式库 uap                = prestate == poststate（0 对象 · 未变更）
```

---

## 15. D-01 Boundary

```text
infrastructure/database/persistence.py sha256 = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（不变）
P15 active worker path → defective helper 使用 = 0
（services/consumer/*.py 内唯一的 "persistence" 命中是 infrastructure.runtime.errors.PersistenceError）
D-01 = DEFERRED（未修复、未触碰）
```

---

## 16. P14 Integrity

```text
HEAD             = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
HEAD subject     = release(p14): accept runtime slice
origin/main      = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
tag 数           = 10（未新增）
UAP-V0.1.10-P14-RUNTIME-SLICE^{} = 15feebadeecd6f7d90e81569c3e869bc20cb18c5
UAP-V0.1.9-P13-SEED^{}           = c420403d5469241e8b03855428ebce435d539c9e
P14 文档 / 测试 / runtime / security boundary = 未修改
PDL 附录 A–S                                 = 未修改
```

---

## 17. Test Results

```text
Batch 1 regression  tests/unit/test_p15_consumer_kernel.py   13 passed
Batch 2 regression  tests/integration/test_p15_claim.py      13 passed
Batch 3 tests       tests/unit/test_p15_worker.py            30 passed
                                                             ---------
合计                                                          56 passed / 0 failed

forbidden tests（19 个 CF-C-4 文件 + tests/unit/test_generate_build_info.py）= 0 executed
推荐使用过的执行方式：逐文件 allowlist（无目录级 pytest）
```

---

## 18. Known Findings（保留 · 未修复）

```text
F-B3-01  services/consumer/__init__.py 的 pre-image sha256 未采集（untracked ⇒ 不可恢复）。
F-B3-02  P15_BATCH1_* / P15_BATCH2_* evidence 文档缺失（BATCH 3 §1 引用但不存在）；
         本轮未伪造历史证据，以 kernel.py / claim.py / test_p15_claim.py 的实测 sha256
         与 13 passed 作为现存依据。建议 Batch 4 处理。
F-B3-03  已移除 test_p15_worker.py 中一行无意义语句（`for future in list(...) and []`）。
F-B3-04  handler 线程无法被强制中断；drain 超期后线程运行至自然结束，结果被 abandoned 丢弃。
         属 Python runtime 既有限制，记录为 implementation detail。
F-B3-05  Batch 3 未实现真实进程入口（apps/worker/**）；当前 worker 是库内类，
         未接 RuntimeDatabase 工厂与信号处理。生产 allowlist 为空，此项不构成 blocker，
         但若 Batch 4 要求“可启动进程”，需要新的授权范围。
```

---

## 19. 工程变更计数

```text
DDL = 0
formal DB DML = 0
migration = 0
schema object = 0
role / grant / owner change = 0
runtime 业务代码（apps/**, core/**, infrastructure/**）= 0
commit = 0
tag = 0
push = 0
release = 0
```

