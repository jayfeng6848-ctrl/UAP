# P15 FOUNDATION RESOLUTION REPORT

## 0. 摘要

```text
Human Decision        = HD-FRP-FOUNDATION-01（FROZEN · 2026-09-28）
Parent commit         = a238e85710fe7f13796a89cae8816bbd1ebbfca8（0.1.12 · immutable）
Candidate version     = 0.1.13
Candidate tag（未创建）= UAP-V0.1.13-P15-EVENT-CONSUMER
性质                  = Foundation / historical baseline / contract alignment correction
                        （不是 P16 · 不是新的 P15 feature · 不是重新设计 Event 系统）
```

```text
F-RP-05 = CLOSED（Wave 1 committed clean-clone verification 不再依赖 worktree-only 修改）
F-RP-02 = PARTIALLY RESOLVED
          CLOSED   = UUIDv7 alignment · tenant_id contract · Carrier Faces
          REMAINING OPEN = tests/conftest.py · infrastructure/database/__init__.py
F-RP-04 = CLOSED（未回退）
```

---

## 1. Human Decision 登记

```text
UUIDv7               = ACCEPT / IMPLEMENT（authority = D-P10-02 + D-AUTH-22）
tenant_id nullable   = ACCEPT / FREEZE（event application contract 对齐 P10 schema）
platform-level event = ACCEPT / FREEZE（tenant_id = NULL = platform-scoped；
                       不是未知 tenant · 不是 tenant impersonation · actor provenance 仍必需）
Wave 1               = allowlist 17 · NO REDUCTION · NO TEST SUPPRESSION
Verification baseline = committed clean clone = release verification authority
Dependency Rules     = 仅恢复 D-P10-17 Carrier Faces；AGENT_RUNTIME future scope 排除
```

已登记于 `PLATFORM_DECISION_LOG.md` **附录 U**（append-only · 附录 A–T 零改写）。

---

## 2. 本轮变更（payload）

| 路径 | 分类 | 变更 |
|---|---|---|
| `core/event/interfaces.py` | CONTRACT ALIGNMENT | `_new_id()` 委托 `core.audit.interfaces.new_event_id()`（UUIDv7）；`tenant_id: str \| None = None`；docstring 记录 `EventBus != Outbox` |
| `docs/architecture/DEPENDENCY_RULES.md` | DOCUMENTATION BASELINE | 仅恢复 `D-P10-17` 的 **Carrier faces** 段（+24 / −0）；不纳入 AGENT_RUNTIME §9；不重写 P09 状态块 |
| `docs/architecture/PLATFORM_DECISION_LOG.md` | GOVERNANCE | 追加**附录 U**（append-only） |
| `docs/architecture/P15_EVENT_CONTRACT_ALIGNMENT.md` | CONTRACT（新） | Event / tenant / platform scope / 可追溯性 |
| `tests/architecture/test_event_contract_alignment.py` | TEST（新） | 9 项对齐守卫（无 DB） |
| `docs/architecture/P15_FOUNDATION_RESOLUTION_REPORT.md` | RELEASE EVIDENCE（新） | 本文件 |
| `docs/architecture/P15_WAVE1_BASELINE_CLOSURE.md` | RELEASE EVIDENCE（新） | Wave 1 基线闭合 |
| `pyproject.toml` · `config/settings.py` · `docker-compose.yml` | RELEASE METADATA | 0.1.12 → 0.1.13 |

```text
schema mutation = 0 · migration mutation = 0 · 0018+ = 0
role / grant / revoke / ACL / subject vocabulary = 0
tests/conftest.py · infrastructure/database/__init__.py = 未纳入（F-RP-02 remaining）
```

---

## 3. Wave 1 — Before / After / Closure

```text
Wave 1 allowlist = 17（未修改 · 未删 · 未 skip · 未 xfail · 未改断言）
```

| 条件 | 结果 |
|---|---|
| Before（0.1.12 tree · clean clone） | 208 passed / 3 failed / 0 collection error（1 × D-02 + 2 × F-RP-05） |
| After（0.1.13 candidate tree · clean clone） | 210 passed / 1 failed / 0 collection error（1 × D-02 · F-RP-05 failures = 0） |

```text
F-RP-05 两条断言现已 PASS：
  test_p10_event_audit_boundary.py::test_event_contract_uses_the_canonical_uuid7_generator
  test_p10_event_audit_boundary.py::test_five_carrier_faces_are_declared_in_dependency_rules

对应实现：
  UUIDv7 alignment            → core/event/interfaces.py 委托 new_event_id()
  Carrier faces documentation → DEPENDENCY_RULES.md（D-P10-17 段）

D-02 仍为唯一失败（CLOSED historical condition · test_runtime_db_wave1.py::test_approved_reads
的 assert audit == 0 未被触碰 · 未被改写 · 未与 F-RP-05 合并）
```

---

## 4. 其他验证（0.1.13 candidate tree · clean clone）

```text
P15 allowlist（4 文件）                          = 65 passed / 0 failed / 0 collection error
Wave 2 allowlist（9 文件）                       = 72 passed / 0 failed / 0 collection error
新增对齐守卫（test_event_contract_alignment.py）  = 9 passed
boundary 守卫（test_p10_event_audit_boundary.py） = 11 passed
Forbidden Tests                                  = 0（tests/unit/test_generate_build_info.py 未执行）
CF-C-4                                           = PASS（denylist 未执行 · 无目录级 sweep）
```

---

## 5. 依赖闭包

```text
对 0.1.13 candidate tree 重跑 Wave 1 闭包（import + 路径字面量）：
  closure_size = 69（roots = 17）
  path-literal 命中（非 clean）= 0   ← 先前的 DEPENDENCY_RULES.md / core/event/interfaces.py 已闭合
  闭包内非 clean 成员 = infrastructure/database/__init__.py
                        （F-RP-02 remaining · 非必需：clean tree 下 Wave 1 = 210/1，无该项依赖）

untracked required dependencies = 0（F-RP-04 CLOSED 未回退）
tracked worktree-only required  = 0
```

---

## 6. Security / DB / Migration / Boundary

```text
Privilege fingerprint = 51/6/5/0/245（五段本轮全部独立复算一致）
  runtime grants = 51 · roles = 6 · uap_app grants = 5 · default ACL = 0 · uap_migrator grants = 245
  （runtime routine grants = 0 · uap_migrator routine grants = 22 ·
    uap_runtime schema CREATE = false · 非系统 memberships = 0）
C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）
CC-7 触发器 tg_acl_subject_types_protect = O（INTACT）
pg_class = 156 · pg_proc = 22 · pg_trigger = 272
P13 seed = acl_subject_types 3 · permissions 12
Core → Domain = 0（core/event 未反向依赖 domains）

Alembic = 单一 head 0017_p13_seed · 0012 → … → 0017 链完整 · 0018+ = 0
upgrade head → downgrade base → upgrade head = PASS（隔离 verification DB uap_p15_verify · 已删除）

Formal DB `uap` = 0 表（prestate == poststate · 未触碰）
Test DB `uap_b1_test` = 0017_p13_seed · events 0（net zero）· users 0 · audit_logs 1898 → 2384
  （test-only append-only 活动 · 未清空 · 未使用 audit_logs == 0 作为全局条件）

P15 production allowlist = EMPTY · production handlers = 0
P15 worker 参数（processes=1 · concurrency=4 · batch<=10 · lease=120s · hb=40s · MAX_ATTEMPTS=10）= 未改动
O-1 / O-2（cap 600 · 无 640）/ O-3 / O-5 / O-6 = 未改动
```

---

## 7. Git 保护与发布状态

```text
old 0.1.11（remote）= dc44c99 · tag object bc312cd = 未修改
old 0.1.12（local） = a238e85 · tag object dfcc694 = 未修改
new commit parent   = a238e85
real staged         = 0（全程使用 isolated temporary index）
historical dirty / F-RP-02 exclusions / BATCH-D = 保留

0.1.13 REMOTE PUSH = FORBIDDEN
下一阶段 = P15 V0.1.13 RELEASE GATE → P15 V0.1.13 REMOTE PUSH GATE
P16+ = FORBIDDEN
```

**END OF P15 FOUNDATION RESOLUTION REPORT**
