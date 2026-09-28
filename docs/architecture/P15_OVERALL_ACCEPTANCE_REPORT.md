# P15 OVERALL ACCEPTANCE REPORT

轮次：**P15 OVERALL ACCEPTANCE**（Full Closure / Cross-Document Consistency / Release Readiness Gate）
日期：2026-09-28
性质：只读核验 + 最终接受判定；不含任何 commit / tag / push / release
前置：P15 Implementation Batch 1–4 = PASS · P15 ACCEPTANCE = PASS

---

## A. Executive Result

```text
P15 DECISION INTEGRITY = PASS
P15 CONTRACT           = FROZEN
P15 IMPLEMENTATION     = PASS
P15 ACCEPTANCE         = PASS
P15 OVERALL ACCEPTANCE = PASS
```

P15 已作为一个**完整、冻结、可发布准备的工程 Slice**被正式接受。

---

## B. Scope（最终边界）

```text
C-5 Events / Outbox Consumer = DELIVERED
C-1 D-01 repair              = DEFERRED
C-2 admin management         = OUT
C-3 /ready redesign          = ACCEPTED COMPATIBILITY（未改动既有权语义）
C-4 Bootstrap CLI            = OUT
C-6 AI                       = FUTURE
C-7 Frontend                 = FUTURE
C-8 Audit deepening          = FUTURE
```

```text
实现载体   = apps/worker/**（专用 consumer 入口）+ services/consumer/**
非目标     = 不新增 schema / role / grant / principal / ACL subject / authorization action
           = 不创建第二套 outbox / dedup 表 / DLQ / scheduler
```

---

## C. Test Evidence

```text
P15 Kernel        = 13 passed
P15 Claim         = 13 passed
P15 Worker        = 30 passed
P15 Worker Entry  =  9 passed
P15 total         = 65 passed / 0 failed        （Overall Acceptance 本轮复跑确认：65 passed in 2.82s）

P14 Wave 1        = 210 passed / 1 failed
  failure         = tests/integration/test_runtime_db_wave1.py::test_approved_reads
  assert          = assert audit == 0
D-02              = CLOSED（historical environment-state condition）
Wave 2            = 72 passed

Total observed execution = 347 passed / 1 historical failed
```

```text
Wave 1 的解释（不得重新分类）：
  该 1 个失败属于已关闭的 D-02 历史环境态条件；原测试断言**未修改**，
  其 sha256 = 51a453f5c1858873525753b556438c4d42240fb393e5b4b770d058a3b0b25c46
  与 P14 Evidence Freeze 记录一致。
  P15 Acceptance **不**把它重新分类为 P15 implementation defect；
  **不**为获得 211/211 修改测试或清空 audit_logs。
  Cross-Wave 结论 = PASS（P15 未使任何 Wave 结果退化）。
```

Cross-Wave 有效性论证（基于 hash 而非记忆）：

```text
Batch 4 回归执行后，P15 实施面文件 hash 未再变化：
  kernel.py / claim.py / worker.py / __init__.py / apps/worker/main.py
  / 全部 4 个 P15 测试文件 —— 与 Batch 4 结束时一致（§N 独立重算表）
⇒ 已在 Batch 4 取得的 Wave 1 / Wave 2 结果对当前代码树仍然有效。
```

---

## D. Security

```text
privilege fingerprint = 51 / 6 / 5 / 0 / 245
  uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245
default ACL           = 0
roles                 = 6
user-defined membership = 0
ownership residual    = 0
public schema CREATE  = false（全部非超级用户）
public schema USAGE   = true
C2 md5                = 185e95be8bc4304edbcd3f4d5cda1eff（未变）
CC-7                  = INTACT（tg_acl_subject_types_protect · tgenabled = O）
P13 seed              = acl_subject_types 3 · permissions 12 · role_permissions 12
unexpected privilege  = 0
```

---

## E. DB

```text
Formal DB state（uap）
  objects / triggers / alembic table = 0 / 0 /（无 alembic_version 表）
  prestate == poststate = TRUE
  schema mutation = 0 · migration mutation = 0 · role mutation = 0 ·
  grant mutation = 0 · revoke mutation = 0 · formal DB mutation = 0
  role/grant/ACL 变更 = 0

Test DB execution state（uap_b1_test）
  alembic_version = 0017_p13_seed
  0018+           = 0
  events          = 0（net zero）
  users           = 0 · agents family = 0
  audit_logs      = 1655（1412 → 1655 · delta = +243）
  pg_class / pg_proc / pg_trigger = 156 / 22 / 272
  grants 51/6/5/0/245 · default_acl 0 · memberships 0 · residual 0 · C2 md5 未变
```

```text
audit_logs +243 的分类 = test-only append-only audit activity（EXPECTED TEST DATA）
  · audit_logs 为 append-only（tg_audit_immutable 亦拒绝超级用户 DELETE）
  · 本轮未对 audit_logs 执行任何 DML
  · **不**删除 · **不**做全局 audit_logs == 0 · **不**为“美观”回滚测试数据
  · **不**把 test DB 的 audit 增长误报为 production DB mutation

⇒ Formal DB state 与 Test DB execution state 在本文档中完全分离陈述。
```

---

## F. Event State（Event / Outbox Final Closure）

```text
Production Allowlist      = EMPTY
Production Handlers       = 0
Production Event Producers = NONE（events 行数 = 0）
```

```text
EMPTY allowlist        = PASS
0 production handlers  = PASS
0 production producers = PASS
```

> P15 实现的是**事件消费执行基础设施与严格边界**，而不是强行创造生产事件业务。
> 该 EMPTY 状态是冻结决策 O-5 的正确产品状态，不是失败。

测试环境中的 test-only event type / handler：

```text
TEST ONLY — NOT REGISTERED IN PRODUCTION
（通过显式注入 EventAllowlist 提供；生产模块不导入测试注册表）
```

不因 production 无事件而扩大 P15 scope。

---

## G. Findings

```text
Blocking Findings = 0

D-01      = DEFERRED / NON-BLOCKING
D-02      = CLOSED
ENV-1     = CLOSED
OI-G-4    = BATCH-D maintenance（未被顺手清除）
F-B4-08   = CLOSED / EXPECTED P15 GOVERNANCE DELTA
```

完整分类见 `P15_FINAL_FINDING_REGISTRY.md` 与 `P15_OVERALL_ACCEPTANCE_CLOSURE.md`。

---

## H. Release Boundary

```text
P15 RELEASE PREPARATION = NOT STARTED
P15 COMMIT              = FORBIDDEN
P15 TAG                 = FORBIDDEN
P15 PUSH                = FORBIDDEN
P16+                    = FORBIDDEN
```

---

# 核验记录（逐项）

## I. Architecture Boundary Final Check

```text
Core → Domain                     = 0（tests/architecture/test_dependency_rules.py passed）
P15 worker → unauthorized Domain mutation = 0（services/consumer/** 无 domains/** import）
worker → migration layer          = 0（无 alembic / migrations_alembic / MigrationRunner 引用）
worker → bootstrap principal      = 0（无 uap_bootstrap 引用）
worker → migrator principal       = 0（无 uap_migrator 引用）
consumer → ACL subject expansion  = 0（无 subject_type 新增）
consumer → new service principal  = 0

O-3 保持：worker = execution mechanism，不是 ACL subject
未出现：worker_subject / service_subject / consumer_subject / system_subject
（扫描 services/consumer/*.py + apps/worker/*.py：matches = 0）
```

## J. O-1…O-6 Semantic Final Audit

```text
O-1 Lease Recovery = PASS
  claimed + lease expired + attempts<10 → pending；worker_id / claimed_at /
  lease_expires_at 置 NULL；attempts 不变；attempts>=10 → dead
  （reason = lease_expired_max_attempts）；使用 conditional UPDATE + rowcount ownership

O-2 Attempts/Backoff = PASS
  canonical = min(5 * 2^(attempt-1), 600) → 5/10/20/40/80/160/320/600/600
  base 5s · multiplier 2 · cap 600s · jitter none · MAX_ATTEMPTS = 10
  640s = 历史算术表的 inconsistency，不属于 canonical P15 behavior（未重新引入）
  attempt 10 → dead，无第 11 次

O-3 Worker Actor = PASS
  无新 ACL subject type；使用事件原始 actor provenance（user / role / agent）
  无 platform_admin / uap_bootstrap / uap_migrator fallback；不自行创建系统身份

O-4 Concurrency = PASS
  worker_processes = 1 · concurrency = 4 · batch <= 10 · lease = 120s · heartbeat = 40s
  未扩张（多进程 = FUTURE，未实现）

O-5 Event Whitelist = PASS
  Production = EMPTY；代码无隐式 wildcard：
  『*』token 扫描 = 0；无 register-all / dynamic event registration / unknown-accepted 路径；
  未知 event_type → dead（unsupported_event_type）；测试 event 不进入 production registry

O-6 Idempotency = PASS
  event_id 为 primary delivery identity；不可证明幂等 ⇒ 不 dispatch；
  允许方式仅 naturally idempotent / transactional key / existing persistence uniqueness；
  本轮未新增 dedup table · 未新增 schema
```

## K. Worker Entry 最终裁决

```text
历史：apps/worker/main.py 原为 STEP 0 placeholder
依据：P15 Contract §2 + P15_IMPLEMENTATION_PREP 均将 apps/worker/**（专用 consumer 入口）列为 IN
      ⇒ OUTCOME B（真实 P15 gap）
本轮已最小补齐：load config → RuntimeApplication bootstrap → construct worker →
                SIGINT/SIGTERM → poll → drain → exit

Worker Entry = PASS

No new framework · No new broker · No new scheduler · No new principal ·
No schema mutation · No grant expansion · No migration

P14 的 apps/worker OUT-OF-SCOPE 记录 = P14 当时的边界定义（历史事实，不改写），
不得用它反向否定 P15 的 IN 判定。
```

## L. Shutdown / Crash / Ownership Final Check

```text
Shutdown：SIGINT/SIGTERM → stop polling → drain → exit（exit code 0/1/2 语义见实现报告）
DRAINING 期间 no new claim / no new task；不得 fake delivered

Handler timeout / abandoned worker：
  处理线程无法强杀 ⇒ result not delivered ⇒ lease eventually expires ⇒ O-1 recovery 处理
  判定 = accepted bounded behavior（Batch 4 已证明不产生错误 terminalization 或 ownership bypass）

Ownership 不可绕过（逐项 SQL 核验）：
  HEARTBEAT_SQL / COMPLETE_DELIVERED_SQL / COMPLETE_PENDING_SQL / COMPLETE_DEAD_SQL
  均包含 worker_id 守卫 + status='claimed'；RECOVER_EXPIRED(_DEAD)_SQL 使用 lease 过期条件
  ⇒ heartbeat 不能刷新别人的 lease；mark_delivered/retry/dead 不能处理别人的 claim
```

## M. Authorization / Tenant / Space / Provenance

```text
Authorization    = PASS（Stage 2 未改；canonical actions = 12 未变）
Tenant Isolation = PASS（worker 不跨 tenant；事件 context 缺失/歧义 ⇒ fail closed）
Space Isolation  = PASS（worker 不跨 space）
Actor Provenance = PASS（使用 originating actor；无 system/platform fallback）
```

## N. D-01 / D-02 / ENV-1

```text
D-01 = DEFERRED / NON-BLOCKING
  infrastructure/database/persistence.py sha256 =
    69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（未变 · 未借 P15 顺手修）
  services/consumer/** 未 import 该缺陷模块（matches = 0）；
  仅经已批准的 SafeReader 路径访问（claim.py:92 self._fetch_one → SafeReader 覆写实现）
  ⇒ PASS

D-02 = CLOSED（历史记录保持）
ENV-1 = CLOSED
OI-G-4 = BATCH-D maintenance（未清除）
```

## O. Evidence Integrity Audit

```text
P15_IMPLEMENTATION_ACCEPTANCE_REPORT.md      EXISTS
P15_IMPLEMENTATION_ACCEPTANCE_MAPPING.md     EXISTS
P15_BATCH4_TEST_EXECUTION_REPORT.md          EXISTS
P15_BATCH4_TEST_EXECUTION_MANIFEST.md        EXISTS
P15_IMPLEMENTATION_REPORT.md                 EXISTS
P15_CHANGE_MATRIX.md                         EXISTS
P15_BATCH1_RETROSPECTIVE_EVIDENCE.md         EXISTS
P15_BATCH2_RETROSPECTIVE_EVIDENCE.md         EXISTS
P15_FINAL_FINDING_REGISTRY.md                EXISTS
P15_FINAL_EVIDENCE_INVENTORY.md              EXISTS
apps/worker/main.py                          EXISTS
tests/unit/test_p15_worker_entry.py          EXISTS

每条最终结论可落到 code / test / document / measured DB evidence 之一
PASS without evidence = 0
```

## P. Retrospective Evidence Final Rule

```text
RETROSPECTIVE = RETROSPECTIVE（保持）
P15_BATCH1_RETROSPECTIVE_EVIDENCE.md / P15_BATCH2_RETROSPECTIVE_EVIDENCE.md 均明确标注
  "Evidence type = RETROSPECTIVE RECONSTRUCTION · Not original execution report"
未伪造 original timestamp / original hash / original contemporaneous record

services/consumer/__init__.py pre-image = UNAVAILABLE / not captured（未猜 hash）
不影响 Acceptance：post-state + implementation + tests + final evidence 完整、真实、可复核
```

## Q. Git Final Audit

```text
HEAD              = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
HEAD subject      = release(p14): accept runtime slice
branch            = main（tracking origin/main）
origin/main       = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
remote            = origin → https://github.com/jayfeng6848-ctrl/UAP.git
tags              = 10（未新增）
staged            = 0（无 accidental staging）
reflog HEAD       = 15feeba / c420403 / 034ee97（无新 commit）

未执行：reset · clean · checkout -- . · stash · add 全部文件 · 修改 unrelated dirty 文件
```

### Dirty-set classification

```text
tracked-modified = 38 · untracked = 147

P15 IMPLEMENTATION (dirty)         = 1   apps/worker/main.py
P15 GOVERNANCE (dirty)             = 1   docs/architecture/PLATFORM_DECISION_LOG.md（附录 T append）
P15 EVIDENCE (untracked)           = 33  docs/architecture/P15_*.md
P15 IMPLEMENTATION (untracked)     = 4   services/consumer/{__init__,kernel,claim,worker}.py
P15 TESTS (untracked)              = 4   tests/unit/test_p15_{consumer_kernel,worker,worker_entry}.py
                                          + tests/integration/test_p15_claim.py
BATCH-D maintenance (dirty)        = 16  CF-C-4 面文件 + OI-G-4 文件（含 tests/conftest.py）
P13 migrations (untracked)         = 4   0013–0016
historical dirty (pre-P15)         = 20  .env.example / README / alembic.ini / config /
                                          core / docker-compose / docs(STEP1B 等) /
                                          infrastructure / migrations README / env.py / conftest
docs/architecture other (untracked)= 80  P09–P14 等历史阶段文档 + AGENT_RUNTIME 等
handoff (untracked)                = 17  docs/architecture/handoff/*
tests other (untracked)            = 5   P10/P11/P12 schema 测试 + runtime_testkit
```

```text
⇒ 本轮的 dirty 增长仅来自 P15 implementation / evidence / governance 三类，与其范围一致。
```

## R. Forbidden Test Governance Final Check

```text
Forbidden Tests Executed = 0
CF-C-4                   = PASS
tests/unit/test_generate_build_info.py（OI-G-4）executed = 0

本轮执行方式 = 逐文件 explicit allowlist
未使用：pytest · pytest tests/ · pytest tests/unit · pytest tests/integration ·
        pytest --collect-only（目录级 broad sweep = 0）
```

## S. 独立 hash 重算（证明文档所载 hash 与磁盘一致）

```text
services/consumer/kernel.py              = d5a304bf4a44526f9256f99f0695fdc6cf6227d5d0ba489683a72de9688c1769
services/consumer/claim.py               = db1be04c40d4448cc836907c80688ac61bb36c8edc5f43e073c4b7f0790f587a
services/consumer/worker.py              = 385306d9fec4b2d71e3ecee0ce87269c01b0c7d4b1ab4b13eb8731d9b64aa263
services/consumer/__init__.py            = 32c146ff42af3490726d9aa56629366f12acad468bd4271017b44ff841700d19
apps/worker/main.py                      = 520a344f200981ed42995ffddd6a567410578e9fee97f5ec30ef712b69061b8c
tests/unit/test_p15_consumer_kernel.py   = aa4cd53f04179744712228ec57064b65cd41cc882b3fd90bf31344c60c3fd94f
tests/integration/test_p15_claim.py      = 599a0550b10d7bfe8ca7db969cf7eae4235b2fb07f0156fb44ffc8f75a91d09b
tests/unit/test_p15_worker.py            = 1bb1a4f158c1775c584ef23636139624c3e92f25b115b270fe7c8baa52e6e23e
tests/unit/test_p15_worker_entry.py      = eb27da282872506580a61242dfee26729adc3e8b7d6bc1a58d04d602acc6dc4a
docs/architecture/PLATFORM_DECISION_LOG.md = 9221b4d78b6543eb9d289593f15bf968da8e73ae62a546db8d0cb194ae5a5c83
migrations_alembic/env.py                = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a
0016_open_p10_1_trust_boundary.py        = 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544
0017_p13_seed.py                         = 1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e
tests/integration/test_runtime_db_wave1.py = 51a453f5c1858873525753b556438c4d42240fb393e5b4b770d058a3b0b25c46
infrastructure/database/persistence.py   = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6

Batch 4 证据文档所载 hash vs 磁盘实测 = 全部 MATCH（0 MISMATCH）
```

---

## 结论

```text
P15 OVERALL ACCEPTANCE = PASS
P15 RELEASE PREPARATION = NOT STARTED（HARD STOP ACTIVE）
```

