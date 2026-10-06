# 13_GIT_HANDOFF_RULES — Git 工作树判读规则

## 当前实测（2026-09-27 21:26）

```text
HEAD   = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e（UAP-V0.1.8-AUTHORIZATION）
branch = main · tags = 8（全 annotated unsigned）· remote = 0
dirty  = 104（67 ?? + 36 M + 1 D）
```

## 核心规则：脏 ≠ 本轮改的

> **判断"本轮修改"必须使用 round-relative snapshot（轮次起始内容快照：每文件 sha256[:16] + mtime 的 JSON，存 %TEMP%），而不是单纯依赖 `git status` 的 M/untracked 状态。**

原因：工作树里**长期携带历史脏文件**（P10–P12 时期 73 个脏文件一路带到现在），它们出现在
`git status` 里并不代表本轮动过；只有「相对轮次快照 sha 发生变化（mutated）」或「快照中不存在（new）」才算本轮变更。

## 脏集构成（分类）

| 类别 | 内容 | 说明 |
|---|---|---|
| 历史脏文件 | P10–P12 实施期遗留（~73 个 M/??）+ 后续各轮 PREP 报告 | 不可当作本轮变更；不清理（清理需授权） |
| BATCH-B 工件 | env.py / alembic.ini / settings.py / testkit / conftest / .env.example / compose / 2×README | 已授权变更（B-1…B-5），FINAL PASS |
| BATCH-C 决策面 | REQUEST / BLOCK（§3 空白+§6 登记）/ RECORD / REVIEW REPORT | 登记轮产物 |
| BATCH-C 实施 | PRE-FLIGHT REPORT / BLOCKER REPORT / **0016 文件** | 本周新增（round-relative NEW = 5） |
| 1 × D | 历史删除标记 | P10–P12 时期遗留 |

## round-relative 判定方法（标准流程）

```python
# 轮次开始：
#   1. git status --porcelain → 每文件 sha256[:16]+mtime 存 JSON（TEMP）
# 轮次结束：
#   2. 再取 status；mutated = 快照存在且 sha 变化；new = 快照不存在的路径
#   3. 断言 mutated/new 恰等于本轮授权变更面
```

本轮（handoff 轮）round-relative NEW 应 = `docs/architecture/handoff/`（16 文件）；mutated = ∅。

## 铁律

```text
- commit/tag/push 各自独立授权（当前均未授权；REQ-8 = NOT AUTHORIZED 维持）
- 禁 -f/--force/amend/rebase/history rewrite
- 未授权不得清理脏文件（含 git clean/checkout --）
- HEAD hash 在任何变更/提交动作前必须复核
- 无 GPG：git tag --verify 恒 "no signature found"，非缺陷
```
