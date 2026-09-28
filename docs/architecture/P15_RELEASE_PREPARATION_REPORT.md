# P15 RELEASE PREPARATION REPORT

日期：2026-09-28（**P15 RELEASE GATE 后刷新版本**）
轮次：P15 RELEASE PREPARATION → 由 P15 RELEASE GATE 刷新 payload / 计数 / 版本权威
性质：只读审计 + payload 冻结；**不产生 commit / tag / push / release**

> 历史说明：本报告的初版（Release Preparation 轮）记录 payload = 49 files、
> 7478 insertions / 22 deletions、EXCLUDE = 142。经 **P15 RELEASE GATE** 完成
> baseline integrity repair 与 version synchronization 后，上述数字已**作废**，
> 以本版本为准（payload = 63 · 8808 insertions / 46 deletions · EXCLUDE = 131）。

---

## 1. Release Identity

```text
Release Version Candidate = 0.1.11
Tag Candidate             = UAP-V0.1.11-P15-EVENT-CONSUMER
Commit Subject Candidate  = release(p15): accept event consumer slice
Release Title Candidate   = UAP v0.1.11 — P15 Event Consumer Slice
```

## 2. Parent Baseline

```text
parent commit = 15feebadeecd6f7d90e81569c3e869bc20cb18c5
parent tag    = UAP-V0.1.10-P14-RUNTIME-SLICE → 15feebad
HEAD = origin/main = 15feebad（均未变）· branch = main · tag count = 10 · real staged = 0
```

## 3. Overall Acceptance（前置）

```text
P15 Decision Integrity = PASS · P15 Contract = FROZEN
P15 Implementation = PASS · P15 Overall Acceptance = PASS · Blocking Findings = 0
```

## 4. Implementation Scope

```text
C-5 = DELIVERED · C-1 = DEFERRED · C-2 = OUT · C-3 = ACCEPTED COMPATIBILITY
C-4 = OUT · C-6 = FUTURE · C-7 = FUTURE · C-8 = FUTURE
```

## 5. Payload Rules

```text
INCLUDE 仅限下列 ownership：
  P15 IMPLEMENTATION · P15 TEST · P15 EVIDENCE · P15 GOVERNANCE ·
  BASELINE INTEGRITY REPAIR · RELEASE METADATA · P15 RELEASE(docs)
EXCLUDE：BATCH-D maintenance · historical dirty · handoff · 非 P15 架构文档 · 未来 scope
禁止：git add . / -A / 目录级 add / clean / reset --hard / checkout -- . / stash
```

## 6. Included Files（最终）

逐文件清单（含 SHA256）见 **`P15_RELEASE_PAYLOAD_MANIFEST.md`**。

```text
P15 IMPLEMENTATION         = 5
P15 TEST                   = 4
P15 GOVERNANCE             = 1（PLATFORM_DECISION_LOG.md · 附录 T）
P15 EVIDENCE               = 35
P15 RELEASE (docs)         = 6
BASELINE INTEGRITY REPAIR  = 9（4 migration + env.py + alembic.ini + 3 文档）
RELEASE METADATA           = 3（pyproject.toml / config/settings.py / docker-compose.yml）
--------------------------------------------------------------
P15 Payload total          = 63
```

## 7. Excluded Files（最终）

逐文件清单与 reason 见 **`P15_RELEASE_EXCLUSIONS.md`**。

```text
Excluded classes = 5
Excluded total   = 131（16 BATCH-D + 13 historical dirty + 17 handoff
                     + 5 tests other + 80 non-P15 architecture docs）
```

## 8. P13 Exclusions

```text
P13 专有 dirty                      = 0（0017_p13_seed.py 已随 c420403d 提交）
历史未跟踪 migration 0013–0016       = 不再是 EXCLUDE；
                                      转入 BASELINE INTEGRITY REPAIR（F-RP-01 CLOSED）
0017_p13_seed.py                    = 未被当作 P15 migration（保持 P13 归属）
```

## 9. BATCH-D Exclusions

```text
BATCH-D maintenance = 16 文件 ⇒ EXCLUDE（another batch）
tests/unit/test_generate_build_info.py（OI-G-4）executed = 0 · 未修 · 未纳入 payload
```

## 10. PDL Appendix T

```text
docs/architecture/PLATFORM_DECISION_LOG.md → INCLUDE（P15 GOVERNANCE）
记录项 = P15 governance authority append-only update
Appendix A–S unchanged · Appendix T append-only · 文件不拆分
sha256 = 9221b4d78b6543eb9d289593f15bf968da8e73ae62a546db8d0cb194ae5a5c83
F-B4-08 = CLOSED / EXPECTED P15 GOVERNANCE DELTA（未回滚）
```

## 11. Security Boundary

```text
roles 6 · uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245
default ACL 0 · privilege fingerprint 51/6/5/0/245
C2 = 185e95be8bc4304edbcd3f4d5cda1eff（unchanged）· CC-7 = INTACT
role / grant / revoke / default ACL mutation = 0
```

## 12. Schema State

```text
alembic_version（uap_b1_test）= 0017_p13_seed · 0018+ = 0
schema mutation = 0 · migration mutation = 0 · pg_class/proc/trigger = 156/22/272
formal db uap = 0 对象 · prestate == poststate
```

## 13. Test State

```text
P15 smoke（逐文件 allowlist · Release Gate 后复跑）:
  tests/unit/test_p15_consumer_kernel.py · tests/integration/test_p15_claim.py ·
  tests/unit/test_p15_worker.py · tests/unit/test_p15_worker_entry.py
  ⇒ 65 passed / 0 failed

forbidden tests = 0 · CF-C-4 = PASS · 无目录级 pytest
Wave1 = 210/211（D-02 CLOSED · 断言未改）· Wave2 = 72 passed
```

## 14. Version Authority（最终：RESOLVED）

```text
CURRENT RELEASED VERSION = 0.1.10
CANDIDATE VERSION        = 0.1.11
pyproject.toml = 0.1.11 · config/settings.py = 0.1.11 · docker-compose.yml = 0.1.11
VERSION AUTHORITY DISCREPANCY = CLOSED / RELEASE METADATA CONSISTENCY
```

## 15. Git State

```text
HEAD = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
origin/main = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（未变）
tag count = 10 · real staged = 0
working tree = dirty（预期保留）
tracked-modified = 39 · untracked = 155
```

## 16. Candidate Diff（最终 · 隔离临时 index 实测）

```text
payload paths submitted = 63
added    = 53
modified = 10
deleted  = 0
total    = 63
63 files changed, 8807 insertions(+), 46 deletions(-)

非 payload 路径泄漏 = 0
临时 index 已删除；模拟后 real staged = 0

注：candidate diff 在隔离临时 index 上实测，且 payload 包含记录该数值的文档本身
    ⇒ 存在 ±数行 的自引用漂移；最终冻结数值以 P15 COMMIT + TAG GATE 的实测为准。

tracked-only diff（工作树 vs HEAD）：39 files changed,
  其 P15 ownership = 10（见 §6）
```

## 17. Final Readiness

```text
P15 RELEASE SCOPE          = FROZEN
P15 RELEASE PREPARATION    = PASS
P15 RELEASE GATE           = PASS（见 P15_RELEASE_GATE_REPORT.md）
P15 RELEASE AUTHORIZATION  = READY
F-RP-01                    = CLOSED（BASELINE INTEGRITY REPAIR）
VERSION AUTHORITY          = RESOLVED（0.1.11 三源一致）
```

```text
COMMIT = FORBIDDEN · TAG = FORBIDDEN · PUSH = FORBIDDEN · RELEASE = FORBIDDEN · P16+ = FORBIDDEN
HARD STOP = ACTIVE
```

---

## 附：Release Artifacts

| Artifact | SHA256 |
|---|---|
| `docs/architecture/P15_BASELINE_INTEGRITY_REPAIR_RECORD.md` | 见 manifest |
| `docs/architecture/P15_RELEASE_GATE_REPORT.md` | 见 manifest |
| `docs/architecture/P15_RELEASE_VERSION_DECISION.md` | 见 manifest |
| `docs/architecture/P15_RELEASE_EXCLUSIONS.md` | 见 manifest |
| `docs/architecture/P15_RELEASE_PAYLOAD_MANIFEST.md` | 见该文件（自引用项在 Final Gate 输出中给出） |
| `docs/architecture/P15_RELEASE_PREPARATION_REPORT.md` | 见 manifest |
