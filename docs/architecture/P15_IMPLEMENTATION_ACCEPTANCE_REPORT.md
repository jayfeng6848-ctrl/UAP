# P15 IMPLEMENTATION ACCEPTANCE REPORT

日期：2026-09-28
验收问题（BATCH 4 §2）：

> P15 C-5 Events / Outbox Consumer 是否已经满足 Frozen Implementation Contract，并且没有破坏
> P14、Security Boundary、Schema Boundary、Authorization Boundary、CF-C-4 和历史 Evidence Freeze？

答案：**是（PASS）**。以下每项均给出 implementation / test / security / DB / regression 证据。
状态只允许 PASS / FAIL / DEFERRED / NOT APPLICABLE。

---

## 1. Contract requirement — 逐节验收

| Contract 节 | 要求 | 证据 | 状态 |
|---|---|---|---|
| §2 Scope IN | `apps/worker/**` 专用 consumer 入口 | `apps/worker/main.py`（Batch 4 最小补齐 · sha256 520a344f…） | PASS |
| §2 Scope IN | `services/**` consumer service/use-case | `services/consumer/{kernel,claim,worker}.py` | PASS |
| §2 Scope IN | `infrastructure/**` 仅复用不新 engine | 无新增 engine；复用 `RuntimeDatabase` | PASS |
| §3 Non-goals | 不新增 schema/role/grant/action/ACL | DB 锚点前后一致（§4） | PASS |
| §3 Non-goals | 不实现 DLQ / manual replay / scheduled recovery | 代码中不存在 | PASS |
| §4 Event lifecycle | `pending→claimed→{delivered,pending,dead}` | `kernel.py` 冻结 SQL · `claim.py` 过渡 | PASS |
| §5 Outbox | outbox = events 表本身 · 无第二套模型 | 无新表；07 段 SQL 只针对 `public.events` | PASS |
| §6 Worker boundary | Worker 只做 claim/execute/record/retry/stop | `worker.py` 无业务规则 · 无 SQL | PASS |
| §6 Worker boundary | 与 `apps/api` 并列，不复用 API handler 逻辑 | 入口不 import `apps.api.*` | PASS |
| §7 Claim semantics | 条件 UPDATE + rowcount 判定所有权 | `CLAIM_SQL` + `claim_batch` | PASS |
| §7 Claim semantics | 索引 `ix_events_dispatch` 支撑 | 未新增索引；复用 0017 既有 | PASS |
| §8 Idempotency | dedup key = `(id, occurred_at, event_type, schema_version)` | `EventHandlerSpec` + O-6 排除规则 | PASS |
| §8 Idempotency | 无法证明幂等的 use-case 不纳入 | production allowlist = EMPTY | PASS |
| §9 Retry | retryable = connection/persistence | `is_retryable` + `RETRYABLE_CATEGORIES` | PASS |
| §9 Retry | non-retryable = auth/security/validation… | `NON_RETRYABLE_CATEGORIES` | PASS |
| §9 Retry | max attempts 上界 + backoff + terminal | `MAX_ATTEMPTS=10` · backoff 序列 · dead | PASS |
| §10 Failure | read→validate→authorize→execute→persist | `_execute` 顺序 + 失败即 terminal | PASS |
| §24 O-1 | lease 回收语义 | `recover_expired` + 测试 | PASS |
| §24 O-2 | attempts/backoff | 5/10/20/40/80/160/320/600/600 | PASS |
| §24 O-3 | worker actor 不新增 subject | 入口不创建 system/worker/platform subject | PASS |
| §24 O-4 | 1 进程 / concurrency 4 / batch ≤10 / lease 120 / heartbeat 40 | `WorkerConfig.validate` | PASS |
| §24 O-5 | 闭合 allowlist（当前 EMPTY） | `production_allowlist()` | PASS |
| §24 O-6 | 幂等排除规则 | 见 §8 两项 | PASS |

---

## 2. Test evidence

```text
P15-KERNEL   13 passed
P15-CLAIM    13 passed
P15-WORKER   30 passed
P15-ENTRY     9 passed
P15 合计      65 passed / 0 failed

P14 Wave 1   210 passed + 1 failed（D-02 历史记录 · 断言保持原样）
Wave 2       72 passed
```

---

## 3. Security evidence（只读实测）

```text
roles                    = 6（uap / uap_app / uap_bootstrap / uap_migrator / uap_runtime / uap_seed）
privilege fingerprint    = uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245
unexpected privilege     = 0
default_acl              = 0
user-defined membership  = 0
ownership residual       = 0
public schema CREATE     = false（所有非超级用户）
public schema USAGE      = true
C2 md5                   = 185e95be8bc4304edbcd3f4d5cda1eff
CC-7                     = INTACT（tg_acl_subject_types_protect · tgenabled = O）
P13 seed                 = acl_subject_types 3 · permissions 12 · role_permissions 12
Stage 2 canonical actions = 12（未变）
新 subject type / system fallback / platform_admin fallback / bootstrap identity /
  migrator identity      = 0
```

---

## 4. DB evidence

```text
alembic_version          = 0017_p13_seed（不变）
0018+                    = 0
pg_class / pg_proc / pg_trigger = 156 / 22 / 272（不变）
test db uap_b1_test      = 唯一差异为 audit_logs 1412 → 1655（+243 · append-only 预期测试数据）
formal db uap            = prestate == poststate（0 对象 · 未变更）
schema mutation / migration mutation / role mutation / grant mutation / revoke mutation /
  formal DB mutation     = 0
测试数据净零              = events 0 · users 0 · agents family 0
```

---

## 5. Regression evidence

```text
P14 Wave 1       = 210/211 HISTORICAL RECORD · D-02 CLOSED（未改写为 211/211）
Wave 2           = 72 passed
Cross-Wave       = P15 变更后 Wave 1 / Wave 2 结果与历史记录逐项一致
P14 integrity     = commit 15feebad · tag UAP-V0.1.10-P14-RUNTIME-SLICE · origin/main 均未变
P13 integrity     = tag UAP-V0.1.9-P13-SEED → c420403d 未变
Architecture      = Core → Domain = 0（tests/architecture/test_dependency_rules.py passed）
CF-C-4           = PASS（19 禁跑文件 + test_generate_build_info.py executed = 0）
```

---

## 6. 逐项状态汇总（BATCH 4 §17–§53）

```text
 1 Claim correctness               PASS
 2 Concurrent claim                PASS
 3 Lease ownership                 PASS
 4 Expired recovery                PASS
 5 Retryable failure               PASS
 6 Terminal failure                PASS
 7 Max attempts                    PASS
 8 Backoff (5…600/600)             PASS
 9 Duplicate delivery              PASS
10 Idempotency                     PASS
11 Authorization denial            PASS
12 Tenant isolation                PASS
13 Space isolation                 PASS
14 Shutdown                        PASS
15 Crash recovery                  PASS
16 DB unavailable                  PASS
17 Observability / audit separation PASS
18 Unsupported event type          PASS
19 Malformed payload               PASS
20 Heartbeat ownership loss        PASS
21 Delivered terminality           PASS
22 Dead terminality                PASS
23 No privilege expansion          PASS
24 No schema mutation              PASS
25 No D-01 dependency              PASS（见 §7 的继承边说明）
42 Empty production               PASS（allowlist EMPTY · handlers 0 · 启动/轮询/claim 0/健康）
43 Test registry isolation         PASS
44 Batch limit                     PASS（11 事件 ⇒ claim ≤ 10 · active ≤ 4）
45 Config                          PASS
46 Worker lifecycle                PASS（process entry 已补齐并测试 · 见 §8）
47 Persistence boundary            PASS
48 Transaction acceptance          PASS（claim/heartbeat/finalize 均短事务）
49 Failure transaction acceptance  PASS
50 Shutdown acceptance             PASS
51 Crash acceptance                PASS
52 Security actor acceptance       PASS
53 Authorization regression        PASS
```

---

## 7. Known findings

```text
D-01  = DEFERRED（persistence.py 未修 · sha256 69d2c140… 未变）
        P15 活跃路径不调用 defective 的 Repository._fetch_one / _fetch_all：
        ClaimService→EventRepository 继承 SafeReader（services/reads.py），
        SafeReader 用自己的正确实现覆写了这两个 helper。
        仍存在一条「继承边」：SafeReader(Repository) 使其在模块层面 import 了该文件。
        修复该继承边属于 P14 Wave 2 既接受文件（services/reads.py）的语义变更 ⇒ 本轮不改。
        ⇒ 判定：PASS + 登记（非阻塞）。

D-02  = CLOSED（历史记录 · Wave 1 210/211）
FINDING-AUTHZ-1 = DEFERRED / OUT OF P15 SCOPE
missing Batch 1/2 contemporaneous evidence = RETROSPECTIVE RECONSTRUCTION（已补齐并明确标注）
services/consumer/__init__.py pre-image    = UNAVAILABLE（untracked）
PLATFORM_DECISION_LOG.md 附录 O–S           = INTACT（仅 append 附录 T）
worker process entry                        = 已补齐（apps/worker/main.py）· PASS
```

---

## 8. Worker process entry 判定（BATCH 4 §8/§9/§10/§11）

```text
问题 = Does P15 require a runnable process entry?

证据（Contract / Acceptance Matrix / Prep 三条权威输入）：
  · P15_EVENT_OUTBOX_CONSUMER_IMPLEMENTATION_CONTRACT.md §2：
      IN（实现载体）= `apps/worker/**`（专用 consumer 入口）
  · P15_IMPLEMENTATION_PREP.md §Implementation scope（IN）：
      `apps/worker/**`（专用 consumer 入口）
  · 反向证据：P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md 将 apps/worker 列为
      OUT OF SCOPE；P14 FILE_INVENTORY 注明 “Contract 未要求 ⇒ 不自动纳入”

判定 = OUTCOME B（§10）：Contract 明确要求专用 consumer 入口 ⇒ 存在真实 P15 implementation gap
处置 = 最小补齐，仅限 apps/worker/**
补齐后能力 = load config → 既有 runtime DB 依赖 → 构造 worker → SIGINT/SIGTERM →
             poll → drain → exit（exit code 0/1/2）
测试 = tests/unit/test_p15_worker_entry.py（9 passed）
未引入 = 新框架 / process manager / Celery / scheduler / broker / 新 principal / 新 schema / 新 grant
P14 影响 = 0（未修改 P14 commit / tag / history / frozen test）
```

---

## 9. 结论

```text
P15 IMPLEMENTATION = PASS
P15 ACCEPTANCE     = PASS
Blocking findings  = 0

Release preparation / commit / tag / push = NOT STARTED（FORBIDDEN）
下一步必须单独授权：P15 OVERALL ACCEPTANCE → P15 RELEASE PREPARATION
```

