# UAP — P14 RELEASE PREPARATION GIT BASELINE

> ```text
> 轮次 = P14 RELEASE PREPARATION（只读基线 · 2026-09-28）
> 性质 = 记录既有状态；**本轮未 stage / 未 commit / 未 tag / 未 push**
> ```

---

# 1. Git freeze 点

```text
HEAD            = c420403d5469241e8b03855428ebce435d539c9e   ✅ 与要求一致
branch          = main                                       ✅
tags            = 9（全部 annotated：objecttype = tag）        ✅
remote          = 0                                          ✅
staged          = 0（**未 stage 任何文件**）                    ✅
dirty（工作树）  = 209 条
```

```text
tag inventory（9）
  UAP-V0.1.0-INIT · UAP-V0.1.0-INIT-DB-VALIDATED · UAP-V0.1.4-B1-4-RESOURCE-ACL ·
  UAP-V0.1.5-PLATFORM-TIMESTAMP-PRECISION · UAP-V0.1.6-B1-6-AI-GATEWAY ·
  UAP-V0.1.7-GOVERNANCE-GATE · UAP-V0.1.7-P09-AGENT-TOOL-PERMISSION ·
  UAP-V0.1.8-AUTHORIZATION · UAP-V0.1.9-P13-SEED
⇒ **P14 尚无 tag**（最后 tag = P13）
```

```text
禁止使用（本轮未使用、后续亦不得借 release-prep 之名使用）
  git add -A / git add . / git commit -am … / git clean -fd / git reset --hard
⇒ 历史 dirty set 不得被清理、不得被 stage
```

---

# 2. Dirty Set Ownership Classification（209 条）

```text
A. P14 release candidate owned            = 30
B. P14 accepted evidence / frozen artifact = 67
C. Earlier UAP historical dirty            = 110
D. BATCH-D maintenance                     = 2
E. Unknown / requires review               = 0
```

## 2.1 A 类（P14 Release Candidate Owned · 30 条）

```text
apps/api/main.py（M）· pyproject.toml（M）· requirements.txt（M）
apps/api/{dependencies,error_mapping}.py · apps/api/routes/{identity,devices,sessions}.py
infrastructure/database/{persistence,principal,runtime}.py · infrastructure/runtime/**
services/{mapping,identity,device,session,context,audit,use_cases}/** · services/reads.py
tests/integration/{wave2_testkit,test_wave2_identity_security,test_wave2_device_security,
                   test_wave2_session_security,test_wave2_authorization_security,
                   test_wave2_api_security,test_wave2_audit_invariant}.py
tests/unit/test_wave2_{vocabulary_mapping,credentials,error_mapping}.py
```

## 2.2 每条 dirty/P14 相关文件的归属说明

```text
path                                          | why dirty                                   | owner phase        | RC? | frozen? | 保持 dirty?
----------------------------------------------|---------------------------------------------|--------------------|-----|---------|-------------
apps/api/main.py                              | Wave 2 lifespan 接线 + 挂载 3 路由           | P14 Wave 2         | 是  | 否      | 是
apps/api/{dependencies,error_mapping}.py      | Wave 2 新增（transport 依赖 + 错误映射）      | P14 Wave 2         | 是  | 否      | 是
apps/api/routes/{identity,devices,sessions}.py| Wave 2 新增（adaptation）                    | P14 Wave 2         | 是  | 否      | 是
services/**（mapping/identity/device/session/  | Wave 2 新增（Domain↔Persistence 映射 +      | P14 Wave 2         | 是  | 否      | 是
  context/audit/use_cases + reads.py）        | service/use-case/context/adapter）           |                    |     |         |
infrastructure/runtime/**                     | Wave 1 新增（lifecycle/errors/retry）        | P14 Wave 1         | 是  | 已验收  | 是
infrastructure/database/{principal,runtime}.py| Wave 1 新增（principal 断言 / DB 边界）      | P14 Wave 1         | 是  | 已验收  | 是
infrastructure/database/persistence.py        | Wave 1 新增（Repository 基类）               | P14 Wave 1         | 是  | **冻结** | 是
  sha256 = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（与 D-01 引用一致）
tests/integration/test_runtime_db_wave1.py    | Wave 1 evidence；**D-02 恢复后冻结**          | P14 Wave 1         | 是  | **冻结** | 是
  sha256 = 51a453f5c1858873525753b556438c4d（含原始 `assert audit == 0`）
tests/integration/test_wave2_*.py             | Wave 2 security/integration evidence         | P14 Wave 2         | 是  | 否      | 是
tests/unit/test_wave2_*.py                    | Wave 2 unit evidence                         | P14 Wave 2         | 是  | 否      | 是
pyproject.toml / requirements.txt             | ENV-1：两处 authoritative manifest 各加一行   | P14 Release Prep   | 是  | 否      | 是
  (ENV-1 变更本身属 release-prep 允许的 dependency declaration)
docs/architecture/PLATFORM_DECISION_LOG.md    | 附录 N/O/P/Q append-only 追加                | Governance (PDL)   | 是  | 否      | 是
  （附录 A–M 语义未改写；O/P/Q 既有正文未改写）
docs/architecture/P14_*.md（67 条 B 类）      | P14 决策/契约/安全/验收/报告 evidence        | P14（多波次）       | 是  | 部分冻结 | 是
tests/security/test_authorization_security.py | OI-G-9（stale head 断言 · CF-C-4 禁跑）      | BATCH-D            | 否  | 否      | 是
tests/unit/test_generate_build_info.py        | OI-G-4（硬编码 head · 既有失败）             | BATCH-D            | 否  | 否      | 是
C 类 110 条                                   | EARLIER-BATCH-B/C 起的既有历史 dirty         | Earlier UAP phases | 否  | —       | 是
```

```text
分类策略
  · A = 本轮 / P14 各波次实际产出、可进入 Release Candidate 的路径
  · B = P14 已验收 evidence 与 frozen artifact（含 PDL）；只读引用，不改写
  · C = P14 之前既有 dirty（BATCH-B/C 遗留），**不属本 RC、不得 stage**
  · D = BATCH-D maintenance（OI-G-4 / OI-G-9），**不属本 RC**
  · E = 0（无未分类路径）

禁止行为
  · 不以重新生成 / 格式化 / 自动排序制造无意义 diff
  · 不 stage 历史 dirty set（C/D）
  · 不清理工作树（no clean / no reset --hard）
```

---

# 3. 本轮工程变更（基线阶段）

```text
新增文档 = 本文件（+ 同轮 4 份 release-prep 文档）
Git：staged = 0 · commit / tag / push = 0
```

**END OF P14 RELEASE PREPARATION GIT BASELINE（2026-09-28 · HEAD c420403d · 9 tags · dirty 209 · 分类 A30/B67/C110/D2/E0 · HARD STOP ACTIVE）**
