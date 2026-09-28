# P15 COMMIT + TAG GATE REPORT

日期：2026-09-28
轮次：**P15 COMMIT + TAG GATE**（Final Explicit Staging / Commit / Annotated Tag / Post-Commit Integrity Gate）
性质：提交前定稿的 Gate 证据；**本文件属于 Release Payload**，提交后不得再修改

> commit SHA / tag object SHA 属提交后才可知的信息，按 §40 记录在**独立的**
> post-release metadata record（`P15_COMMIT_TAG_POST_RELEASE_RECORD.md`），
> 该文件**不进入** 本次 commit payload。

---

## 1. Scope 裁决

```text
F-RP-01 = CLOSED · PRE-EXISTING REPOSITORY BASELINE INTEGRITY DEFECT
          RELEASE BLOCKER → REPAIRED → VALIDATED
F-RP-03 = AUTHORIZED · INCLUDE IN P15 RELEASE COMMIT · BASELINE INTEGRITY REPAIR
F-RP-02 = EXCLUDED · NOT AUTHORIZED FOR P15 · DEFERRED / REGISTERED
```

```text
F-RP-03 纳入文件（9 · BASELINE INTEGRITY REPAIR）
  migrations_alembic/versions/0013_p10_event_audit.py
  migrations_alembic/versions/0014_p11_triggers.py
  migrations_alembic/versions/0015_p12_indexes.py
  migrations_alembic/versions/0016_open_p10_1_trust_boundary.py
  migrations_alembic/env.py
  alembic.ini
  migrations_alembic/README.md
  .env.example
  README.md

理由 = committed repository 必须能在 fresh clone 中完整重建
       **已存在** 的 migration graph 与 runtime migration configuration
不是 = P15 feature / P15 schema change / P15 new migration
revision 语义 = 未修改（revision id / down_revision / upgrade / downgrade 全部保持）

F-RP-02 排除文件（3 · NOT STAGED / NOT COMMITTED）
  tests/conftest.py
  core/event/interfaces.py            ← 含 UUIDv7 / tenant_id nullable 真实语义变化
  infrastructure/database/__init__.py
```

---

## 2. Version / Parent

```text
Version  = 0.1.11
Tag      = UAP-V0.1.11-P15-EVENT-CONSUMER
Parent   = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（UAP-V0.1.10-P14-RUNTIME-SLICE）
Subject  = release(p15): accept event consumer slice

Static version sources: pyproject.toml 0.1.11 · config/settings.py 0.1.11 ·
                        docker-compose.yml 0.1.11（三源一致 · 无非历史 0.1.0 歧义）
```

---

## 3. P15 Payload（commit 前最终重新计算）

```text
分类计数
  P15 IMPLEMENTATION        = 5
  P15 TEST                  = 4
  P15 EVIDENCE              = 35
  P15 RELEASE (docs)        = 7（含本文件）
  P15 GOVERNANCE            = 1（PLATFORM_DECISION_LOG.md · 附录 T）
  BASELINE INTEGRITY REPAIR = 9
  RELEASE METADATA          = 3
  --------------------------------------------------
  Payload total             = 64

物理 payload 由 explicit path allowlist 形成；
严禁 git add . / -A / --all / 目录级 add。
```

## 4. Manifest Hash Integrity / Self-Hash Rule

```text
SELF-HASH RULE = manifest 对自身行不写入 SHA256（该行为说明性文字，不是 hash）；
                 self-hash field is EXCLUDED from the canonical hash set。
                 ⇒ 不存在 SHA256(full file) == embedded SHA256 的自引用断言。
                 canonical hash set = 携带 64-hex SHA256 的行 = 行总数 − 1
                 校验 = 逐行 sha256(磁盘文件) 必须相等 + 行数 = 行总数 − 1
                 manifest 自身完整性由 commit object / annotated tag 背书
```

```text
独立重算结果（P15_COMMIT + TAG GATE 实测）
  manifest 行总数                        = 64
  携带 64-hex SHA256 的行                = 63
  逐行 sha256 与磁盘实测相等             = 63 / 63（mismatch = 0）
  disk 上 P15_*.md 未被 manifest 收录    = 0
⇒ Manifest Hash Integrity = PASS · Self-Hash Rule = VALID
```

## 5. Alembic Chain / Fresh Clone Validation（commit 前复验）

```text
chain              = 0012 → 0013 → 0014 → 0015 → 0016 → 0017
alembic heads      = 0017_p13_seed (head)          ← single head
0018+              = 0

isolated checkout  = git archive HEAD + baseline repair + P15 payload
isolated DB        = uap_p15_release_verify（owner uap_migrator · 已 DROP）
migration identity = UAP_MIGRATION_DATABASE_URL

upgrade head        rc = 0 → alembic_version = 0017_p13_seed
downgrade base      rc = 0 → alembic_version = 空
upgrade head（再次） rc = 0 → alembic_version = 0017_p13_seed
alembic current     rc = 0 → 0017_p13_seed (head)

isolated DB 对象 = pg_class 156 · pg_proc 22 · pg_trigger 272 ·
                   acl_subject_types 3 · permissions 12 · role_permissions 12
⇒ 与冻结基线一致 · Fresh Clone Migration = PASS
正式库 uap = 0 对象 · prestate == poststate（未参与任何实验）
```

## 6. Test State

```text
P15 smoke（逐文件 allowlist · commit 前复跑）
  tests/unit/test_p15_consumer_kernel.py
  tests/integration/test_p15_claim.py
  tests/unit/test_p15_worker.py
  tests/unit/test_p15_worker_entry.py
  ⇒ 65 passed / 0 failed

Forbidden Tests = 0 executed（含 tests/unit/test_generate_build_info.py）
CF-C-4          = PASS（无目录级 pytest / 无 --collect-only）

Historical Wave 结论不变：Wave1 = 210/211（D-02 CLOSED · assert audit == 0 未改）
                          Wave2 = 72 passed
```

## 7. Security / Architecture / Event Boundary

```text
roles = 6 · privilege fingerprint = 51/6/5/0/245 · default ACL = 0
C2 = 185e95be8bc4304edbcd3f4d5cda1eff（unchanged）· CC-7 = INTACT
role / grant / revoke / default privilege mutation = 0

Core → Domain = 0
P15 payload scope：C-5 = yes · C-1 / C-2 / C-4 / C-6 / C-7 / C-8 = no
                   C-3 = 仅保留既有 accepted compatibility

Production Allowlist = EMPTY · Production Handlers = 0
PDL Appendix T = INCLUDED（A–S unchanged · T append-only）
```

## 8. Explicit Exclusion Assertions（candidate index 实测）

```text
tests/conftest.py                     = NOT STAGED
core/event/interfaces.py              = NOT STAGED
infrastructure/database/__init__.py   = NOT STAGED
tests/unit/test_generate_build_info.py = NOT STAGED

BATCH-D 文件（16）        = absent
historical dirty（13）    = absent
handoff（17）             = absent
unrelated docs（80）      = absent
P13 unrelated files       = absent
future scope              = absent
deleted files             = 0
```

## 9. Candidate Diff（隔离临时 index 实测）

```text
payload paths submitted = 64
added    = 54
modified = 10
deleted  = 0
total    = 64
64 files changed, 9021 insertions(+), 46 deletions(-)
非 payload 泄漏 = 0 · real staged = 0
```

## 10. 结论

```text
P15 COMMIT PAYLOAD = FROZEN
P15 COMMIT         = READY
P15 ANNOTATED TAG  = READY

PUSH = FORBIDDEN · GITHUB RELEASE = FORBIDDEN · P16+ = FORBIDDEN
HARD STOP = ACTIVE（commit + tag 完成后）
```
