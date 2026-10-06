# 15_NEXT_ACTION — 唯一合法下一步

## 当前状态（不得跳过）

```text
P0 ENV FIX         = NOT AUTHORIZED
0016 REEXECUTION   = NOT AUTHORIZED
BATCH-C CONTINUATION = BLOCKED（唯一阻断项 = env.py P0 缺陷）
0017               = NOT STARTED（ABSENT）
P13                = NOT STARTED
```

## 唯一合法入口

```text
P0 ENV FIX AUTHORIZATION PREP
```

（即：为 env.py 修正轮准备授权材料——新 Gate、修改范围锁死为 `migrations_alembic/env.py` 单文件、
Fix A/B/CUSTOM 候选、真实前进探针设计、回滚与验收标准；STRICT READ-ONLY，不实施。）

## 授权后的强制序列（P0 ENV FIX IMPLEMENTATION）

```text
new baseline（只读全锚点）
    ↓ new gate
env.py fix（仅该文件）
    ↓ real forward migration proof（version 表前移 + post-image 指纹 + COMMIT 落库验证）
    ↓ 0016 upgrade（窗口期授权下）
    ↓ post-image + 正/负探针矩阵
    ↓ downgrade（恢复 pre-image md5 68678741…）+ 再 upgrade（终态 0016）
    ↓ full regression（安全探针 + 所有权/授权回归）
    ↓ 权限窗口 REVOKE + 终态证明
```

## 禁止直接进入

```text
0017（P13 seed）      ← 须先完成 BATCH-C 验收 + P13 Implementation Contract
P13 Implementation    ← 顺序冻结：OPEN-P10-1 完成 → P13
Runtime cutover       ← 未授权
commit/tag/push       ← 未授权
```

## 之后的路线图（供预期，非授权）

```text
BATCH-C 完成（I01…I30 PASS）
    ↓ BATCH-C POST-IMPLEMENTATION ACCEPTANCE / P13 HANDOFF
    ↓ BATCH-D（integration 隔离决议执行 + 终验）
    ↓ P13 B-1 Amendment 执行面收尾 → P13 Implementation（0017_p13_seed）
    ↓ Runtime STEP2（cutover）
```
