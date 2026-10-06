# UAP HANDOFF — ACTIVE ENGINEERING STATE（00_HANDOFF_INDEX）

> 生成时间：2026-09-27 21:26 · STRICT READ-ONLY / TRANSFER MODE · 生成轮零工程变更

## 第一页必读

```text
BATCH-B = PASS
BATCH-C = BLOCKED（0016 IMPLEMENTATION BLOCKED BY env.py P0 defect）
0016    = CREATED / NOT PERSISTED（静态审计 PASS；upgrade 静默回滚）
P0 env.py defect = REAL / OPEN（修复未授权）
0017    = ABSENT
P13     = NOT STARTED
CURRENT NEXT ACTION = P0 ENV FIX AUTHORIZATION PREP
```

## 阅读顺序

```text
CURRENT STATUS      → 本文件 + 08_CURRENT_BLOCKER.md（最重要）
FROZEN DECISIONS    → 04_P13_FROZEN_DECISIONS.md · 06_D_OP101_DECISION_STATE.md
SECURITY BASELINE   → 11_DATABASE_SECURITY_BASELINE.md · 02_ARCHITECTURE_BOUNDARY.md
COMPLETED WORK      → 03_COMPLETED_MILESTONES.md · 05_OPEN_P10_1_STATUS.md
BLOCKER             → 08_CURRENT_BLOCKER.md · 09_P0_FIX_OPTIONS.md
OPEN ISSUES         → 10_OPEN_ISSUES_REGISTRY.md
NEXT LEGAL ACTION   → 15_NEXT_ACTION.md
行为准则            → 14_AGENT_OPERATING_RULES.md（10 条铁律）
工程规则/证据/Git   → 07_REVISION_AND_MIGRATION_RULES.md · 12_EVIDENCE_MAP.md · 13_GIT_HANDOFF_RULES.md
背景                → 01_PROJECT_OVERVIEW.md
完整合集            → UAP_AGENT_HANDOFF_BUNDLE.md（本文集合一）
```

## 阅读后必须接受的五个事实

1. **不可重新解释任何 FROZEN 决策**（`D-OP101-01…14`、`D-P13-01…15`；权威 = `docs/architecture/PLATFORM_DECISION_LOG.md`，sha256[:16] = `a83fde5c57605252`）。
2. **当前唯一合法下一步** = `P0 ENV FIX AUTHORIZATION PREP`（env.py 缺陷修复未授权；0016 重执行未授权；0017/P13 未开始）。
3. **migration identity ≠ runtime identity**：`UAP_MIGRATION_DATABASE_URL → uap_migrator`（仅迁移）；`DATABASE_URL → settings.DATABASE_URL → uap_app`（仅运行时）；双向禁 fallback。
4. **工作树是脏的，但脏 ≠ 本轮改的**：判定必须用 round-relative snapshot（13_GIT_HANDOFF_RULES.md）。
5. **发现真实缺陷/冲突**：STOP → REPORT → WAIT FOR AUTHORIZATION（14_AGENT_OPERATING_RULES.md Rule 4）。

## 当前基线速览（2026-09-27 21:26 实测）

```text
Git        HEAD 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · main · tags 8 · remote 0 · dirty 104
Migration  单头 0015_p12_indexes（活体一致）· 0016 文件已建未持久执行 · 0017 ABSENT · .py 16
Database   uap_b1_test：角色 4 · 所有权 156+22=178 全 uap_migrator（残留 0）· uap_app grants 5
           uap_migrator CREATE=false · default_acl 0 · 用户成员关系 0 · 触发器 39 · registry 0 行
           正式库 uap：0 表
安全锚点   PDL a83fde5c… · Record 9efbc3fe… · Contract 2c1fec37… · 0007 9e0105b9… · C2 md5 68678741…
```
