# 14_AGENT_OPERATING_RULES — 新 Agent 行为准则（10 条铁律）

## Rule 1 — PREP ≠ IMPLEMENTATION

PREP/DESIGN/审计轮 = STRICT READ-ONLY（禁 migration/DDL/DML/code/test/doc/commit/tag/push）。
每阶段 HARD STOP 等显式授权；"PREP 完成"不等于"可以动手"。

## Rule 2 — Human Decision ≠ inferred decision

只有 Human **逐槽明确提交**的取值才是决策。Gate 规程、候选矩阵、建议文本、历史习惯、
上下文语气**都不构成裁定**；空白 = PENDING（不等于 KEEP OPEN）；禁止自动纠错
（`AUTHORIZED` ≠ `AUTHORISED`，不得静默归一）。

## Rule 3 — Frozen decision 不得重新解释

`D-PLAT-* / D-AUTH-* / D-AGENT-* / D-P10…13-* / D-OP101-01…14`（PDL 权威）一经 FROZEN：
append-only、禁改结论、禁 supersede 除非 Human 明示并走登记轮。
canonical action 词表 12 项 lowercase（NFKC→casefold）严禁 AI 增删改。

## Rule 4 — 真实 blocker：STOP → REPORT → WAIT FOR AUTHORIZATION

发现 P0/P1 级缺陷或决策冲突：立即停止、出 BLOCKER 报告（根因链 + 证据 + 修复候选 + A–E 归因）、
等 Human 授权。**不得擅自修复、不得绕过、不得降低断言继续跑。**

## Rule 5 — 区分 harness defect 与 product defect

Gate 失败先归因：脚本缺陷（修 harness 重跑，留档自证缺陷）vs 产品缺陷（STOP 上报）。
**不得修改生产实现去迁就 harness**；空集合不得视为 PASS；集合断言必须验证 expected set。

## Rule 6 — migration implementation 必备序列

```text
static audit → pre-image 取证（指纹）→ privilege boundary（窗口）→ identity probe
→ forward execution proof（version 表前移 + post-image 指纹 + 持久性验证）
→ rollback proof（恢复 pre-image）→ post-image 复核 → 探针矩阵
```
历史迁移 0001–0015 不可改写；filename==revision；钉自己的 revision（不用 head）。

## Rule 7 — 权限窗口生命周期

```text
open（deployment 身份）→ prove（CREATE=true）→ execute → revoke → prove final state（CREATE=false）
```
GRANT/REVOKE 永远不写进 migration 文件；禁止自授/自撤/SET ROLE/SECURITY DEFINER/SUPERUSER workaround。

## Rule 8 — 禁止 `import migrations_alembic.env`

（OI-BB-14 · 永久）import 即进入 Alembic 执行路径。测试只能用：
real Alembic CLI probe（testkit `migration_dsn()` FAIL-CLOSED）/ 独立 helper / DB 集成探针。

## Rule 9 — integration 隔离（CF-C-4=C）

19 个会 `reset_test_database()` 的测试文件（integration 18 + `tests/security/test_authorization_security.py`）
在 BATCH-D 决议前**禁跑**——reset 会 DROP/CREATE 数据库，摧毁 BATCH-A 的 178 项 ownership 基线。

## Rule 10 — 绝不为 Gate PASS 而作弊

不得 weaken assertion / introduce fallback / expand scope / modify unrelated code / hide failure。
探针必须断言「version 表前移 + 副作用落库」——**at-head no-op 探针与静默回滚不可区分，等于没测**
（本轮 P0 缺陷的直接教训）。

## 附：沟通与输出纪律

- 输出带 frozen-rule 引用、证据路径、PASS/BLOCKED、A–E 归因；
- 不得把计划/静态审阅表述为"已实施/已测试"；环境受限项注明 NOT EXECUTED（非缺陷）；
- "不知道就说不知道"，严禁捏造历史/IDs/路径；
- 记忆/日志写仓库外（uap-stage3-evidence 与 WorkBuddy memory），审计期间不写 memory。
