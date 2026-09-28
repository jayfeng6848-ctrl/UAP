# P15 RELEASE GATE REPORT

日期：2026-09-28
轮次：**P15 RELEASE GATE**（Pre-Commit Decision / Repository Baseline Integrity / Version Authority / Final Release Authorization）
性质：Release Gate 证据报告；**不产生 commit / tag / push / release**

---

## 1. 前置状态

```text
P15 Overall Acceptance  = PASS
P15 Release Preparation = PASS
P15 Release Scope       = FROZEN
Parent baseline         = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（UAP-V0.1.10-P14-RUNTIME-SLICE）
```

---

## 2. F-RP-01 专项裁决

```text
ID             = F-RP-01
Classification = PRE-EXISTING REPOSITORY BASELINE INTEGRITY DEFECT
Impact         = RELEASE BLOCKER（committed tree 无法重建 Alembic graph）
Repair         = BASELINE INTEGRITY REPAIR（P15 RELEASE GATE §6 Option A）
Validation     = PASS（isolated checkout + isolated DB · upgrade → downgrade → upgrade）
Status         = CLOSED
```

同族缺陷 `F-RP-03`（committed `env.py` = P0 fix 之前版本 / `alembic.ini` 仍带可执行 DSN）
一并修复并关闭。完整 pre/post SHA256、forensic 证据与验证记录见
**`P15_BASELINE_INTEGRITY_REPAIR_RECORD.md`**。

```text
ALEMBIC CHAIN
  before（committed tree）= 0012 →（断）→ 0017       · alembic heads/history/upgrade = FAIL
  after （candidate tree）= 0012 → 0013 → 0014 → 0015 → 0016 → 0017 · single head = 0017_p13_seed

FRESH CLONE（git archive HEAD + baseline repair + P15 payload）
  upgrade head         = PASS（alembic_version = 0017_p13_seed）
  downgrade base       = PASS（alembic_version 为空）
  upgrade head（再次） = PASS（alembic_version = 0017_p13_seed）
  alembic current      = 0017_p13_seed (head)
  isolated DB 对象      = pg_class 156 · pg_proc 22 · pg_trigger 272 ·
                          acl_subject_types 3 · permissions 12 · role_permissions 12
                          （与冻结基线完全一致）
  isolated DB 名称      = uap_p15_release_verify（已 DROP · 无残留）
```

---

## 3. Version Authority 裁决

```text
VERSION AUTHORITY DISCREPANCY
Status         = CLOSED
Classification = RELEASE METADATA CONSISTENCY
Target         = 0.1.11
```

```text
Current released version = 0.1.10
Candidate version        = 0.1.11

Static Version Sources（同步后）
  pyproject.toml      = 0.1.11
  config/settings.py  = 0.1.11（APP_VERSION 默认值）
  docker-compose.yml  = 0.1.11（APP_VERSION）

同步性质 = Release Metadata Synchronization（未改依赖 / config 语义 / Docker topology / runtime 行为）
详见 = docs/architecture/P15_RELEASE_VERSION_DECISION.md
```

---

## 4. P15 Scope（保持）

```text
C-1 = DEFERRED · C-2 = OUT · C-3 = ACCEPTED COMPATIBILITY · C-4 = OUT
C-5 = DELIVERED · C-6 = FUTURE · C-7 = FUTURE · C-8 = FUTURE
```

```text
P15 Functional Scope        = C-5 Events / Outbox Consumer
Release Integrity Scope     = historical Alembic chain repair + version metadata synchronization
```

> Release Integrity Scope **不是** P15 业务特性，而是使仓库自身内部一致的
> release readiness remediation。两者不得混为一谈。

---

## 5. Payload（重新计算）

| 分类 | 数量 |
|---|---|
| P15 IMPLEMENTATION | 5 |
| P15 TEST | 4 |
| P15 EVIDENCE（35） + P15 RELEASE（6） | 41 |
| P15 GOVERNANCE（PDL 附录 T） | 1 |
| BASELINE INTEGRITY REPAIR | 9 |
| RELEASE METADATA | 3 |
| **合计** | **63** |

逐文件清单与 SHA256 见 `P15_RELEASE_PAYLOAD_MANIFEST.md`；
排除清单见 `P15_RELEASE_EXCLUSIONS.md`（EXCLUDE = 131）。

```text
missing = 0 · orphan = 0 · unresolved = 0
candidate index simulation 与 manifest = exact match
deleted files = 0
real staged = 0
```

---

## 6. Security / Schema / Event 边界（最终）

```text
roles                 = 6
privilege fingerprint = 51 / 6 / 5 / 0 / 245
default ACL           = 0
C2                    = 185e95be8bc4304edbcd3f4d5cda1eff（unchanged）
CC-7                  = INTACT
Schema new revision   = 0 · 0018+ = 0
Migration mutation    = 0（未新增 revision；0013–0016 为历史文件纳入）
Role / Grant / Revoke mutation = 0
Production Allowlist  = EMPTY
Production Handlers   = 0
Core → Domain         = 0
```

---

## 7. Final Test

```text
P15 smoke（逐文件 allowlist）
  tests/unit/test_p15_consumer_kernel.py
  tests/integration/test_p15_claim.py
  tests/unit/test_p15_worker.py
  tests/unit/test_p15_worker_entry.py
  ⇒ 65 passed / 0 failed

Forbidden tests = 0 executed（含 tests/unit/test_generate_build_info.py）
CF-C-4          = PASS（无目录级 pytest / 无 --collect-only）

Historical Wave 结果保持：
  Wave1 = 210/211 · failure = D-02 historical · D-02 = CLOSED（未改写断言）
  Wave2 = 72 passed
```

---

## 8. Formal DB Final State

```text
FORMAL PRODUCTION-LIKE DB（uap）           = 0 对象 · prestate == poststate
TEST DB（uap_b1_test）                      = 冻结锚点未变
ISOLATED RELEASE-VERIFICATION DB            = uap_p15_release_verify（已 DROP）
三者严格区分，未混淆。
```

---

## 9. Git / Remote Safety

```text
HEAD            = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
origin/main     = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
tag count       = 10（未新增）
real staged     = 0
push            = 0 · 未创建远程分支

未执行：commit / tag / push / git add . / git add -A / clean / reset --hard /
        restore . / checkout -- . / stash
历史 dirty 原样保留
```

---

## 10. 结论

```text
P15 RELEASE GATE          = PASS
P15 RELEASE AUTHORIZATION = READY

COMMIT = STILL FORBIDDEN · TAG = STILL FORBIDDEN · PUSH = STILL FORBIDDEN
HARD STOP = ACTIVE

下一阶段（必须由新的独立指令启动）= P15 COMMIT + TAG GATE
```

