# UAP — P13 RELEASE FINAL ARCHIVE GATE REPORT

> ## 轮次与边界
>
> ```text
> 轮次      = P13 RELEASE FINAL ARCHIVE（Phase A · 只读审计 + 归档固化）
> 本轮未做  = 未创建 migration · 未改 schema · 无 DDL · 无 DML · 未改 runtime code ·
>             未改冻结 Decision · 未改 Contract / Matrix 冻结正文 · 未 commit · 未 tag · 未 push
> 本文件    = 新增（append-only；不删除任何历史证据）
> ```

---

# 1. Release Identity（A1）

```text
HEAD    = c420403d5469241e8b03855428ebce435d539c9e
branch  = main
tag     = UAP-V0.1.9-P13-SEED
  tag type        = tag（annotated）
  tag object sha  = 083f06dee6998550220c597dc27234a061ce13f5
  tagger          = UAP Platform <platform@uap.local>
  target commit   = c420403d5469241e8b03855428ebce435d539c9e（匹配）
tags total = 9 · remote = 0

worktree:
  dirty = 109（modified 36 · untracked 73）
  staged = 0
  说明：modified/untracked 全部为既往轮次遗留脏集，未进入本次发布
```

---

# 2. Commit Identity

```text
commit  = c420403d5469241e8b03855428ebce435d539c9e
subject = UAP-V0.1.9-P13-seed
parent  = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e
content = 3 files changed, 631 insertions(+), 0 deletions(-)
  migrations_alembic/versions/0017_p13_seed.py
  docs/architecture/P13_POST_IMPLEMENTATION_CLOSURE_REPORT.md
  docs/architecture/P13_RELEASE_PREP_GATE_REPORT.md
```

---

# 3. Migration Baseline

```text
revision       = 0017_p13_seed
down_revision  = 0016_open_p10_1_trust_boundary
single head    = 0017_p13_seed（versions = 17 · 0001…0017）
live version   = 0017_p13_seed
DDL expansion  = 0（无 CREATE / ALTER / DROP）
runtime change = 0
```

---

# 4. Artifact Integrity（A2）

```text
object                                                      sha256                                                              git blob
migrations_alembic/versions/0017_p13_seed.py                 1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e  4f923aa477a92a63cffd76c830dd2582e0128aea
docs/architecture/P13_POST_IMPLEMENTATION_CLOSURE_REPORT.md   4a364504e4e71bd3c1ba366dc4ca5ba9843adc00ff3a0e603f4179bf10d58b5e  bff4dd880f4ccaf637ea2af40254f0e78ba920c3
docs/architecture/P13_RELEASE_PREP_GATE_REPORT.md            c77e32aa4f345abfe18bad520562ae13a8b0f0188dca269385c1ba80f774f48c  d51345f044f99cdd5cd040ca40f8290f2ca4a343

三份对象均在 commit 内（git ls-tree HEAD 命中）⇒ 工作区内容 == 提交内容
```

追溯链完整性：

```text
Decision（D-AUTH-18 / D-P13-01…15 / D-OP101-03·05 / IMPL-01..04）
  → Contract（§21 IMPLEMENTATION DECISIONS）
  → Matrix（§6 IMPLEMENTATION DECISION SYNC）
  → Migration（0017_p13_seed）
  → Evidence（P13_POST_IMPLEMENTATION_CLOSURE_REPORT · P13_IMPLEMENTATION_READINESS_GATE_REPORT）
  → Commit（c420403d）
  → Tag（UAP-V0.1.9-P13-SEED · annotated）
链路 = COMPLETE（无断链）
```

---

# 5. Database Release Snapshot（A3 · 只读）

```text
alembic_version   = 0017_p13_seed
acl_subject_types = 3      {user, role, agent}
permissions       = 12     D-P13-01 canonical
role_permissions  = 12     platform_admin × 12 × allow
users             = 0
audit_logs        = 0

保护对象（未变）
  pg_class public = 156 · pg_proc public = 22 · parent triggers = 39
  roles = 4 · owner residual = 0 · uap_app grants = 5 · default_acl = 0
  C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff
  0016 sha256 = 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544（未变）
  env.py sha256 = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a（未变）

本轮数据库修改 = 0
```

---

# 6. Documentation Status（A4 扫描与分类）

分类定义：

```text
CURRENT     = 现行语义（可作为实施依据）
SUPERSEDED  = 已被显式取代（有取代声明 / 指针）
HISTORICAL  = 历史记录（时点快照 / 传输产物 / 附录登记）
INVALID     = 与现行事实矛盾且无任何标记
```

## 6.1 `P13 = NOT STARTED`

```text
命中 5 文件：docs/architecture/handoff/{00_HANDOFF_INDEX,15_NEXT_ACTION} ·
             docs/architecture/handoff/UAP_AGENT_HANDOFF_BUNDLE ·
             P13_RELEASE_PREP_GATE_REPORT（其扫描章节内的历史分类） ·
             PLATFORM_DECISION_LOG（历史附录内时点记录）
分类 = HISTORICAL（handoff 传输快照 + 历史附录）
INVALID = 0
```

## 6.2 `0016_p13_seed`（旧编号）

```text
命中 19 文件
分类：
  SUPERSEDED —— Contract（顶部状态指针 :8 · §21.6 S-1 · §21.7）· Matrix（§6.5 M-1 · §6.6）
  HISTORICAL —— PDL 冻结正文（冻结时点编号，append-only）· 附录 J/K/L ·
                P13 PREP / DECISION / EVIDENCE 系列 · OPEN_P10_1_* 系列
现行声明（CURRENT）= 0017_p13_seed（Contract :8/:661 · Matrix :191/:200）
INVALID = 0
```

## 6.3 registry subject keys

```text
断言 registry keys = {agent, service, human} 的文档 = 0
文档中的白名单断言 = `key IN ('user','role','agent')`（与实现一致）
`service` 仅出现于 **identity 词汇**语境（IDENTITY_KINDS / identities.provider），
由 D-AUTH-18 明文区分「Authorization Subject Type ≠ Identity Kind ≠ Identity Provider」
分类 = CURRENT（正确）；INVALID = 0
```

## 6.4 旧 C2 陈述（`无条件 RAISE` / `无任何豁免分支`）

```text
命中 10 文件
分类：
  SUPERSEDED —— P13 B-1 Amendment §14.3 · Contract 顶部指针 / §21.6 S-2 / §21.8 ·
                P13_DECISION_COMPLETION_FREEZE_GATE_REPORT（AC-1 处置）·
                P13_IMPLEMENTATION_CLARIFICATION_SHEET §8
  HISTORICAL —— P13 B-1 Amendment §1/§2/§3/§6（缺陷发现时点事实）· Contract §3.1 ·
                OPEN_P10_1_*（BATCH-C 轮证据）· PDL 附录 L §7.2
CURRENT（作为实施依据）= 0 → 现行依据 = CC-7 受信迁移边界
INVALID = 0
```

## 6.5 A4 结论

```text
CURRENT 语义一律指向 0017_p13_seed + CC-7
INVALID = 0（无「矛盾且无标记」条目）
历史证据全部保留，未删除、未改写
```

---

# 7. Known Issues（登记，不修复）

```text
K-1  OI-G-4（BATCH-D / maintenance · REGISTERED / UNFIXED）
     对象：scripts/generate_build_info.py · tests/unit/test_generate_build_info.py
     现象：测试硬编码期望值滞后（原 0015，graph head 已演进至 0017）
     本轮处置：未修复 · 未重分类

K-2  docs/architecture/handoff/ 传输快照已过时（其中 0016/P13 状态陈述为当时事实）
     性质：历史产物；按项目规则不改写
     处置：登记；如需刷新 handoff 须另行授权

K-3  工作区存在既往脏集（modified 36 · untracked 73）
     性质：BATCH-A/B/C 与各 PREP 轮遗留；非发布内容
     处置：登记；清理须另行授权

K-4  后续阶段（Runtime Slice 路线）的**阶段编号与文档集合尚未冻结**
     依据：D-PLAT-12.a（FROZEN）——「正式编号及文档集合须在 PREP 门冻结」，
           且「不得在 PREP 门之前作为既成编号使用；不得据 `P14` 创建任何文件或引用」；
           PDL 附录 C 的 C-8 仍为待确认项
     处置：见本报告的 Phase B 停止说明（不创建相关文件）
```

---

# 8. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration execution = 0 · runtime code = 0
commit = 0 · tag = 0 · push = 0
新增文件 = 本报告
```

---

# 9. Gate 结论

```text
P13 RELEASE FINAL ARCHIVE = PASS
  release identity   = 已固化（HEAD · annotated tag · target commit 一致）
  artifact integrity = PASS（3 对象 sha + blob + commit 包含关系一致）
  database snapshot  = PASS（0017_p13_seed · 3 / 12 / 12 / 0 / 0）
  documentation scan = PASS（CURRENT 语义唯一 · INVALID = 0）
  known issues       = 4 项已登记（K-1…K-4），均未自行修复
```

> 本报告不产生任何授权；未 commit / tag / push。

---

**END OF P13 RELEASE FINAL ARCHIVE GATE REPORT（2026-09-27 · `P13 RELEASE FINAL ARCHIVE = PASS` · tag = UAP-V0.1.9-P13-SEED · commit/tag/push = 0（本轮））**
