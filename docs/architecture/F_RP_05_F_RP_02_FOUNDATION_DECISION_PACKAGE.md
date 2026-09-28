# F-RP-05 / F-RP-02 FOUNDATION DECISION PACKAGE

## 0. 文档性质与用途

```text
类型 = FOUNDATION DECISION PREPARATION（事实包）
日期 = 2026-09-28
用途 = 为 Human Decision 提供完整、可复现的事实基础
约束 = 本文件不替 Human 决定语义；不修改任何代码/测试/allowlist；
       不 commit / 不 tag / 不 push
性质 = uncommitted working-tree evidence
```

本轮 PASS 标准（§37）：Facts / Timeline / Authority Scan / Dependency Closure /
Semantic Classification / Decision Matrix / Release Consequences 全部完整，
且无 scope expansion、无 allowlist 修改、无语义修改、无 commit/tag/push。

---

## 1. Finding Summary

```text
F-RP-04 = CLOSED（0.1.12 已纳入 runtime_testkit.py 与 test_p10_event_audit_boundary.py）
F-RP-05 = OPEN（PRE-EXISTING VERIFICATION-VISIBILITY DEFECT · BLOCKING FOR REMOTE RELEASE）
F-RP-02 = OPEN / REGISTERED（未修改）
```

核心事实：

```text
Wave 1 allowlist（17 文件）自 P14 起即引用未提交文件；
其 2 条断言在 committed tree 上依赖工作区未提交的 tracked 内容：
  core/event/interfaces.py      （语义：UUIDv7 / tenant_id nullable）
  docs/architecture/DEPENDENCY_RULES.md（文档：Carrier faces 等）

其中 core/event/interfaces.py 的目标行为并非“无据可依”：
D-P10-02（FROZEN · 已 committed）明确 Domain Event ID = UUIDv7 canonical，
并明确 uuid.uuid4() 属“实现遗留、实施期修正”。
⇒ 缺的不是决策，而是该修正的 implementation acceptance 与提交。
```

---

## 2. Timeline（四层）

### Layer A — P14 Decision Time（决策层）

```text
2026-09-23  D-AUTH-22 冻结：Audit / Event ID = UUIDv7（19 FROZEN + 3 DEFERRED）
2026-09-25  D-P10-02 注记（append-only clarification · C-2）：
            现行实现契约 core/audit 已与 UUIDv7 对齐（new_event_id()）；
            历史 “core/audit exception” 表述作废；
            与 UUIDv7 不对齐者为 core/event（由 OQ-P10-02 裁定实施期修正）。
2026-09-28  P14 WAVE 1 INCIDENT RECOVERY + TEST SCOPE REMEDIATION（HD-P14-REC-03）
            产生 Wave 1 逐文件 allowlist（17 文件 + denylist 19 + OI-G-4 1）
```

### Layer B — P14 Release Commit

```text
commit = 15feebadeecd6f7d90e81569c3e869bc20cb18c5（P14 release）
evidence：
  · docs/architecture/P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md 在此 commit 进入 git
  · docs/architecture/P14_RUNTIME_WAVE2_TEST_EXECUTION_MANIFEST.md 同样
  · PLATFORM_DECISION_LOG.md 在此 commit 已含 D-P10-02（6 处命中）与 D-P10-17
  · 但该 commit 的 tests/ 树（53 文件）缺少 allowlist 中的
      tests/architecture/test_p10_event_audit_boundary.py
      以及测试支撑 tests/integration/runtime_testkit.py
⇒ 文档基线与 committed 基线自 P14 起即不一致
```

### Layer C — Working Tree Development State（当前工作区）

```text
core/event/interfaces.py          HEAD blob f25ee33 → worktree blob dda81c9（+16 / −3）
docs/architecture/DEPENDENCY_RULES.md
                                  HEAD blob 848e523 → worktree blob 51c5bf0（+69 / −3）
tests/conftest.py                 HEAD blob d032495 → worktree blob b555dee（+38 / −0）
infrastructure/database/__init__.py
                                  HEAD blob d1ed0c2 → worktree blob 540b0fc（+8 / −0）
tests/integration/alembic_testkit.py（worktree modified）
```

### Layer D — P15 / Release State

```text
15feebad  P14 release（0.1.10）
dc44c99   P15 release commit（0.1.11）· REMOTE · RELEASE-BLOCKED
          · 纳入 P15 consumer slice + 0013–0016 基线迁移修复
          · 明确排除 F-RP-02 三件（tests/conftest.py · core/event/interfaces.py ·
            infrastructure/database/__init__.py）
a238e85   P15 corrective（0.1.12）· LOCAL · NOT PUSHED
          · 新增 runtime_testkit.py + test_p10_event_audit_boundary.py
          · 版本元数据 0.1.12
          · 未纳入 core/event/interfaces.py 与 DEPENDENCY_RULES.md
```

---

## 3. Git Evidence（当前实测）

```text
HEAD                = a238e85710fe7f13796a89cae8816bbd1ebbfca8
origin/main         = dc44c9939d7708b68e5b461a7ccb6684588d1106
0.1.11 tag object   = bc312cd95ef65c5d4fa9a302a0832915107e5fac → dc44c99
0.1.12 tag object   = dfcc694744d56b369d0752e0708352f29a56337c → a238e85
real staged         = 0
0.1.12 tag          = 未移动 · 0.1.11 tag = 未移动
```

三个文件的 blob 对照：

| 文件 | HEAD blob | worktree blob | 状态 |
|---|---|---|---|
| `core/event/interfaces.py` | `f25ee332d571e7d03ea3f9ae9d485837751c877c` | `dda81c983f37f3173258bae20f3747407cb09c08` | 未提交语义变化 |
| `docs/architecture/DEPENDENCY_RULES.md` | `848e52302befae7d728e4afb86227fc3fb8dcd11` | `51c5bf0545233ffb35684a8f93dff5ced86843cc` | 未提交文档变化 |
| `core/audit/interfaces.py` | `6abb70a96dcc43a5d48ed1a84f4d07add51d94ed` | 同 HEAD | 已 committed 且 clean |

```text
DEPENDENCY_RULES.md 最近一次 commit = 034ee97
  “feat(authz): implement authorization model and enforcement”（P09 / 0.1.8 期）
⇒ 该文件的 committed 内容停留在 P09 期；工作区 delta 从未提交
```

---

## 4. File Forensic Record — `core/event/interfaces.py`

```text
Current HEAD blob      = f25ee332d571e7d03ea3f9ae9d485837751c877c
Worktree blob          = dda81c983f37f3173258bae20f3747407cb09c08
Worktree SHA-256       = afd5ce7b7104c694235cf39092953f43161583c4d868b8b1726eec6ddec4c67c
Delta                  = +16 / −3（working-tree only · 从未提交）
First known appearance = 该 delta 无 git 历史；首次进入 git 的候选版本尚未提交
Relevant decisions     = D-P10-02 决策①（FROZEN · committed）
                         D-AUTH-22（FROZEN · committed）
                         C-2 append-only clarification（CLARIFIED）
                         OQ-P10-02（裁定实施期修正 core/event）
Relevant tests         = tests/architecture/test_p10_event_audit_boundary.py
                           ::test_event_contract_uses_the_canonical_uuid7_generator
                         （Wave 1 allowlist · 0.1.12 起已 committed）
                         tests/integration/test_p10_event_audit_schema.py（DENY 面 · untracked）
Consumers              = production consumer = 0
                         （core/event 之外无 DomainEvent 使用；P15 consumer 走 events 表 + ClaimService）
Impact                 = 应用层契约对齐（见 §6/§7）；DB 层既有 schema 不变
P15 relevance          = NONE（P15 不使用 DomainEvent）
Foundation relevance   = HIGH（冻结决策的实现落地，缺 implementation acceptance）
```

---

## 5. UUID 变化专项（§8）

```text
问题：uuid.uuid4() → new_event_id() 的变化，事实状态是什么？
```

| 问题 | 事实 | 证据来源 | 状态 |
|---|---|---|---|
| 是否已被 Human Decision 冻结？ | **是** | `PLATFORM_DECISION_LOG.md` D-P10-02 决策①（FROZEN）· D-AUTH-22（FROZEN） | tracked / committed |
| 是否已出现在 accepted artifact？ | 部分：`core/audit/interfaces.py`（`new_event_id()`）已 committed；`core/event` 侧未提交 | `core/audit/interfaces.py` blob 与 HEAD 相同 | tracked |
| 哪个阶段首次引入？ | 应用侧：P10 实施期（工作区）；DB 侧：`uap_uuid_v7()` 自 B1-0（0002） | `B1-4_DEPENDENCY.md` · migration 0002 | — |
| 是否有测试证明 UUIDv7 是 canonical？ | 有：`test_p10_event_audit_boundary.py`（Wave 1）· `test_p10_event_audit_schema.py`（DENY 面） | 两测试均断言 `new_event_id` | — |
| 数据库是否要求该格式？ | **否**：`events.id` / `audit_logs.id` 为 `uuid NOT NULL`，无 server default、无格式 CHECK | live DB `pg_attribute/pg_attrdef/pg_constraint` | 实测 |
| 是否影响 event_id uniqueness / ordering？ | 唯一性不受影响（uuid 类型）；排序性提升（v7 时间有序）仅对索引/分区裁剪有益 | D-AUTH-22 理由段 | 已冻结理由 |
| 是否影响 audit / trace / outbox？ | audit 侧已对齐（`core/audit` 已用 `new_event_id()`）；outbox 语义由 `events` 表承担，不受本变更影响；trace 不在此面 | `core/audit/interfaces.py` · P15 consumer | — |

```text
重要限定：D-P10-02 同时写明「本轮不得修改 core/event/interfaces.py」，
        即该修正是 deferred-to-implementation 项，需独立 implementation acceptance。
```

---

## 6. tenant_id nullable 专项（§9 / §31）

TYPE：这是 **DB schema 事实 + Python 契约对齐**，不是新的 schema 决策（schema 早已允许 NULL）。

| 层面 | 事实 | 证据 |
|---|---|---|
| DB schema（committed） | `events.tenant_id` `nullable=True`；`audit_logs.tenant_id` `nullable=True` | `migrations_alembic/versions/0013_p10_event_audit.py` L161 / L204 |
| DB live（实测） | `events.tenant_id` is_nullable = YES；`audit_logs.tenant_id` = YES；`id` = NO | `information_schema.columns` |
| application contract（committed） | `tenant_id: str`（必填） | HEAD `core/event/interfaces.py` |
| application contract（worktree） | `tenant_id: str | None = None` | worktree blob `dda81c9` |
| 相关决策（committed） | **NO FROZEN DECISION FOUND**（tracked 决策日志无 DomainEvent.tenant_id 可空条文） | `PLATFORM_DECISION_LOG.md` grep |
| 相关决策（untracked） | `P10_PREP_REPORT` L35/L145 · `P10_DECISION_RESOLUTION` Option A · `P10_IMPLEMENTATION_CONTRACT` E-05 / L284 / L495 / L566（含 “tenant_id 由必填改为可空（对齐冻结 schema 允许 NULL）”） | untracked P10 文档 |

```text
一致性判定（app contract vs committed DB schema）：**不一致**
一致性判定（worktree contract vs committed DB schema）：**一致**
与 tenant isolation policy 的交互：**证据不足**
  （未找到“platform-level event（tenant_id = NULL）与租户隔离谓词如何交织”的冻结条文）
```

---

## 7. D-P10-02 专项（§10）

```text
是否已冻结？ = 是。PLATFORM_DECISION_LOG.md D-P10-02（FROZEN），
               进入 git 时点 = 15feebad（P14 release commit）。
是否已发布？ = 决策已随 P14 发布物进入 git；
               其「实施期修正」目标（core/event 对齐）尚未提交。
是否只是工作区演进？ = 决策不是；该决策的实现（core/event/interfaces.py delta）是。

EventBus != Outbox：C-3 = RESOLVED（冻结原文「EventBus != Outbox」）；
  三项 MUST NOT（不替代 outbox 持久化 / 不视为持久边界 / 不成为跨进程投递机制）。
```

---

## 8. `DEPENDENCY_RULES.md` 深度审计（§11 / §32）

### 8.1 Section Ownership

| Section（worktree 行号） | Origin | Decision | Historical release | Current status | 性质 | P15 relevance | Include/Exclude candidate |
|---|---|---|---|---|---|---|---|
| §1–§7（L6–L103） | STEP-0 / B1 基础 | 既有规则 | 已发布（72ade9f / eb6d4cb） | committed 且 clean | rule text | 无 | 保持 committed |
| §8 Authorization boundary（L104–L136） | P09 / 0.1.8 | D-AUTH 系列 | 已发布（034ee97 · UAP-V0.1.8-AUTHORIZATION） | worktree 状态块 = “implemented and accepted”；committed 版本仍写 “design frozen — not implemented” | documentation（状态描述） | 无 | 文档基线修复候选（非语义） |
| §9 Agent runtime boundary（L141–L178） | AGENT_RUNTIME（未来 scope · D-AGENT-01…16） | 设计冻结未实施 | 未发布 | worktree-only | future-scope documentation | 无（P15 明确禁止 P16+） | EXCLUDE（未来 scope） |
| Carrier faces（L179–L202） | P10 / D-P10-17 | FROZEN（committed 于 15feebad） | 决策已发布；文档段未提交 | worktree-only | documentation（决策的实施落地） | 间接（Wave1 断言依赖） | 文档基线修复候选（非语义） |
| Adding a rule（L203+） | 基础 | 既有 | 已发布 | committed | rule text | 无 | 保持 committed |

```text
工作区 delta 组成（+69 / −3）= §8 状态块改写 + §9 新段 + Carrier faces 新段
⇒ 不得整体归类为 P15；三段来源不同，须分别裁决
```

### 8.2 “Carrier faces” 来源判定（§12）

```text
决策来源 = D-P10-17（FROZEN · 已 committed，自 15feebad 起在 tracked 决策日志内）
         = 五类承载面边界形式化 + tests/architecture 守卫（实施期落地）
文档段落  = 该决策的**实施期文档落地**，从未进入 git（非“已发布后丢失”）
佐证      = P10_ACCEPTANCE_MATRIX REL-06 / REL-07（untracked）·
           test_p10_event_audit_boundary.py 直接断言该段与守卫名
```

---

## 9. Wave 1 Evidence

```text
Wave 1 allowlist 权威 = docs/architecture/P14_RUNTIME_WAVE1_TEST_EXECUTION_MANIFEST.md
                        （P14 commit 15feebad 进入 git；P15_BATCH4 manifest §5 原样继承 17 文件）
Committed baseline    = 15feebad / dc44c99 / a238e85 上分别缺 2 / 缺 2（0.1.12 后缺 0）/
                        17 文件全部在位（但 2 条断言依赖 worktree 内容）
Worktree baseline     = 含未提交的 core/event/interfaces.py 与 DEPENDENCY_RULES.md
Expected verification baseline = 见 §10
```

ASSERTION → SOURCE → BASELINE → DECISION：

| Assertion | Source | Baseline | Decision needed |
|---|---|---|---|
| `assert "uuid4" not in src` | `core/event/interfaces.py` | committed: 含 uuid4（FAIL）· worktree: 无（PASS） | F-RP-02 semantic foundation decision（D-P10-02 实施落地） |
| `assert "new_event_id" in src` | 同上 | committed: 无（FAIL）· worktree: 有（PASS） | 同上 |
| `assert "Carrier faces" in src` | `DEPENDENCY_RULES.md` | committed: 无（FAIL）· worktree: 有（PASS） | documentation baseline repair decision（D-P10-17 实施落地） |
| 五个 face 关键字 | 同上 | committed: 均无 · worktree: 均有 | 同上 |
| `assert "test_p10_event_audit_boundary" in src` | 同上 | committed: 无 · worktree: 有 | 同上 |

---

## 10. Wave 1 Baseline Decision（三基线必须分开）

```text
COMMITTED BASELINE（P14 15feebad）
  allowlist 17 文件中 16 在位 → 无法收集（file not found）

WORKTREE DEVELOPMENT BASELINE
  含未提交 core/event/interfaces.py（语义）与 DEPENDENCY_RULES.md（文档）
  ⇒ 历史 210 passed / 1 failed 仅在此条件下成立

EXPECTED VERIFICATION BASELINE（0.1.12 committed tree = a238e85）
  17 文件全部可收集（0 collection error）；实测 208 passed / 3 failed
  = 1 × D-02 历史事实 + 2 × F-RP-05

COMMITTED BASELINE ≠ WORKTREE DEVELOPMENT BASELINE
```

---

## 11. P15 Evidence

```text
P15 clean-clone smoke（4 文件） = 65 passed / 0 failed / 0 collection error
P15 不使用 DomainEvent（consumer 走 events 表 + ClaimService）
P15 production allowlist = EMPTY · production handlers = 0
P15 未修改 core/event/interfaces.py 与 DEPENDENCY_RULES.md（0.1.11 / 0.1.12 均未纳入）
0.1.11 = RELEASE-BLOCKED（remote）· 0.1.12 = LOCAL / NOT PUSHED
```

---

## 12. Dependency Closure（P15 / Wave1 / Wave2）

方法：对三套 allowlist 的 root 文件做传递闭包（import + 路径字面量），再判定 working tree 差异。

| 集合 | roots | closure 大小 | 闭包内非 clean | 路径字面量命中（非 clean） | required worktree-only |
|---|---|---|---|---|---|
| P15 | 4 | 22 | `tests/integration/alembic_testkit.py` | 无 | 0 |
| Wave 1 | 17 | 69 | `infrastructure/database/__init__.py` | `docs/architecture/DEPENDENCY_RULES.md` · `core/event/interfaces.py` | **2** |
| Wave 2 | 9 | 89 | `tests/integration/alembic_testkit.py` | 无 | 0 |

```text
分类：
  Required historical artifact      = DEPENDENCY_RULES.md 的 Carrier faces 段（TYPE A）
  Semantic foundation artifact      = core/event/interfaces.py（TYPE B）
  Documentation artifact（未来 scope）= DEPENDENCY_RULES.md §9 Agent runtime
  Optional artifact                 = tests/integration/alembic_testkit.py ·
                                      tests/integration/test_p10_event_audit_schema.py ·
                                      test_p11_triggers.py · test_p12_indexes.py
  False positive                    = `core.permission.Decision`（大小写不敏感路径解析）

untracked required dependencies = 0（F-RP-04 CLOSED）
tracked worktree-only required dependencies = 2（Wave 1 面）
```

### 12.1 `tests/conftest.py` 专项（§20）

```text
delta        = +38 / −0（纯注释 + 两个 session fixture：migration_dsn / runtime_dsn）
来源         = D-OP101-10 / BATCH-B B-4（dual-DSN 配置链）
被依赖？      = 未被任何 allowlist 测试请求（全仓 grep：仅 alembic_testkit.py 定义同名函数）
clean-clone 必需？ = 否（P15 65/0 · Wave2 72/0 · Wave1 仅 2 条 F-RP-05 失败）
行为变化？    = 新增 fixture 与其文档；对现有测试路径无强制影响
判定         = F-RP-02 残留 · 默认 EXCLUDE（不得自动纳入）
```

### 12.2 `infrastructure/database/__init__.py` 专项（§21）

```text
delta        = +8 / −0（新增导出：Repository · RuntimeDatabase ·
               PrincipalAssertionError · assert_connection_principal · role_from_url）
被依赖？      = Wave1 closure 含该文件，但 clean tree 下 Wave1 除 2 条 F-RP-05 外全部通过
               （唯一包级 import 是 `from infrastructure.database import health`，不依赖新增导出）
clean-clone 必需？ = 否
判定         = F-RP-02 残留 · 默认 EXCLUDE
```

---

## 13. Authority Scan（§29）

```text
已找到的 FROZEN / RESOLVED 决策（tracked 且 committed）
  D-AUTH-22   Audit / Event ID = UUIDv7                        FROZEN（2026-09-23）
  D-P10-02    Domain Event ID = UUIDv7 canonical               FROZEN
              Outbox = durable delivery authority              FROZEN
              EventBus = optional in-process auxiliary         FROZEN（三项 MUST NOT）
              c2          core/audit 已对齐；core/event 实施期修正  CLARIFIED
  D-P10-17    五类承载面边界形式化 + tests/architecture 守卫      FROZEN（实施期落地）
  C-3         EventBus != Outbox                              RESOLVED

未在 tracked authority 中找到（NO FROZEN DECISION FOUND）
  DomainEvent.tenant_id 可空性
    ↳ 间接支撑：committed DB schema（0013 · nullable=True）+ untracked P10 契约文档
  Wave 1 的 clean-clone 验收口径
    ↳ 相关要求出现在 P15 COMMIT+TAG / PUSH / CORRECTION 期文档（0.1.11 / 0.1.12）

核心判读（§30）
  test_event_contract_uses_the_canonical_uuid7_generator
    = 测试「已冻结的 canonical event contract（D-P10-02 决策①）」
    ≠ 测试「未来实现期望」
  依据：D-P10-02 明确 uuid.uuid4() 为“实现遗留”，并规定在实施期修正；
        同决策又写明“本轮不得修改 core/event/interfaces.py” ⇒ 修正需独立实施验收。
```

---

## 14. Decision Matrix（§22）

| Option | Description | Scope Impact | Semantic Impact | Test Impact | Git Impact | Release Impact | Advantages | Risks | Required Human Decision |
|---|---|---|---|---|---|---|---|---|---|
| **A** | 维持当前 P15 边界：F-RP-02 / F-RP-05 保持 OPEN，0.1.12 不推送 | 无 | 无 | 无 | 无 | 0.1.12 继续 BLOCKED | 零风险 · 不触语义 | P15 长期停在本地；验证面持续不闭合 | 是否接受长期 blocked |
| **B** | 授权 historical baseline repair（仅非语义产物） | 文档 / 测试基础设施 | 无 | 需重跑 Wave1 | 新 commit（+可能新 corrective tag） | 需新的 corrective release | 关闭 DEPENDENCY_RULES 侧缺口 | 该文件含未来 scope（AGENT_RUNTIME），必须先拆分 | 拆分方案 + 纳入范围 |
| **C** | 授权 semantic foundation decision（UUIDv7 / tenant_id nullable） | core 契约 | 有（对齐既有 FROZEN 决策） | Wave1 2 条断言转 PASS | 新 commit + 新版本 | 需新 corrective release | 落实 D-P10-02 实施项；应用与 DB 契约一致 | 触及冻结区；须明确 tenant_id 可空的隔离语义 | 正式 semantic decision + 验收口径 |
| **D** | 授权新的 verification baseline | 验收口径 | 无 | allowlist / expected 需治理修订 | 治理类 commit | 影响 release 判据 | 使 Wave1 基线可复现 | 可能被视为降低回归覆盖 | 是否修订基线及其边界 |

```text
禁止项（本轮与后续均不得由 Agent 自行选择）：
  以“UUIDv7 更合理”为由自行纳入 · 以“nullable 更灵活”为由自行纳入 ·
  因 Wave1 失败而改 allowlist · 以工作区通过为由当作 release baseline
```

---

## 15. Release Consequences（§25 · 只计算，不执行）

| Option | 0.1.12 可否继续？ | 需新 corrective version？ | 需新 commit？ | 需新 tag？ | 需重跑 P15 Acceptance？ | 需重跑 Wave1？ | 涉 schema？ | 涉 migration？ | 属 foundation phase？ |
|---|---|---|---|---|---|---|---|---|---|
| A | 否（BLOCKED） | 否 | 否 | 否 | 否 | 否 | 否 | 否 | 否（保持 deferred） |
| B | 否（需先完成 B 的交付） | 是（0.1.13 或等价） | 是 | 是 | 视范围（建议是） | 是 | 否 | 否 | 是 |
| C | 否（需先完成 C 的交付） | 是 | 是 | 是 | 是 | 是 | 否（DB 已允许 NULL） | 否（0018+ 保持 0） | 是 |
| D | 否（需先完成 D 的治理修订） | 视修订结果 | 是（治理类） | 视结果 | 建议是 | 是 | 否 | 否 | 是 |

```text
0.1.11 = immutable remote FAILED RELEASE CANDIDATE（不得修改 / 覆盖 / 移动 tag）
0.1.12 = immutable local corrective release（LOCAL · NOT PUSHED）
```

---

## 16. Open Questions（须由 Human 回答）

```text
Q1  core/event/interfaces.py 的 UUIDv7 对齐是否作为 D-P10-02 的实施落地被正式验收？
    验收载体是哪一个 Gate？
Q2  DomainEvent.tenant_id 可空性是否需要一个独立的冻结条文（当前只有 DB schema 与
    未提交的 P10 契约文档支撑）？
Q3  Wave 1 allowlist 是否应当包含 tests/architecture/test_p10_event_audit_boundary.py？
    （该文件同时是 D-P10-17 的守卫与 Wave1 回归项，属跨阶段归属）
Q4  DEPENDENCY_RULES.md 是否需要按 §8 状态块 / §9 未来 scope / Carrier faces 三段拆分？
    §9 是否应从该文件移出到 AGENT_RUNTIME 文档集（未来 scope）？
Q5  Wave 1 的权威验收基线定义为何：committed tree 还是含既定工作区内容的 development baseline？
Q6  platform-level event（tenant_id = NULL）在租户隔离策略下的预期行为是否有冻结条文？
```

## 17. Recommended Decision Categories

```text
本轮不推荐单一选项，只提供类别：
  · Category 1：接受 Option A（保持 deferred）—— 最小风险，但 0.1.12 继续 BLOCKED
  · Category 2：Option B + C 组合 —— 先拆文档（B），再做语义落地验收（C）
  · Category 3：Option D —— 若判定 Wave1 allowlist 口径自始不适配 clean-clone 验收
  · Category 4：B / C / D 全部推迟，先建立 Foundation Contract（UUID / tenant / carrier faces）
```

---

## 18. Release State（本轮结束）

```text
P15 Functional Semantics = INTACT（本轮未修改任何 P15 代码/测试/allowlist）
P15 Release Push         = BLOCKED
Real Staged              = 0
HEAD                     = a238e85（未变）· 0.1.12 tag（未变）· 0.1.11 tag（未变）
remote/main              = dc44c99（未推送）
P16+                     = FORBIDDEN
HARD STOP                = ACTIVE
```

**END OF F-RP-05 / F-RP-02 FOUNDATION DECISION PACKAGE（uncommitted evidence）**

---

## 19. 追加（2026-09-28 · HUMAN DECISION 已下达 · append-only）

本节不改写 §1–§18 的任何事实与选项（决策前事实包保持原样），只登记决策结果：

```text
HD-FRP-FOUNDATION-01 = FROZEN（Human Decision）

UUIDv7               = ACCEPT / IMPLEMENT（D-P10-02 + D-AUTH-22）
tenant_id nullable   = ACCEPT / FREEZE（对齐 P10 schema；NULL = platform-scoped）
platform-scoped event = ACCEPT / FREEZE（NULL ≠ 未知 tenant ≠ 授权旁路）
Wave 1               = allowlist 17（NO REDUCTION · NO TEST SUPPRESSION）
Verification baseline = committed clean-clone tree（不再接受 worktree baseline）
Dependency Rules     = 恢复 D-P10-17 Carrier Faces；排除 AGENT_RUNTIME future scope

F-RP-05 = CLOSED（Wave 1 committed clean-clone：210 passed / 1 failed（D-02 only）/ 0 collection error）
F-RP-02 = PARTIALLY RESOLVED
          CLOSED = UUIDv7 alignment · tenant_id contract · Carrier Faces
          REMAINING OPEN = tests/conftest.py · infrastructure/database/__init__.py
```

采纳选项：`Option B（非语义文档基线修复）+ Option C（已冻结语义的实施落地）` 的组合；
`Option A`（保持 deferred）与 `Option D`（新 verification baseline）未被采纳。

详见 `docs/architecture/P15_FOUNDATION_RESOLUTION_REPORT.md` ·
`docs/architecture/P15_WAVE1_BASELINE_CLOSURE.md` ·
`PLATFORM_DECISION_LOG.md` 附录 U。

**END OF AMENDMENT（2026-09-28 · Human Decision 已登记）**
