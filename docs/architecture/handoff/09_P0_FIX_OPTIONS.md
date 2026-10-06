# 09_P0_FIX_OPTIONS — P0 修复候选（仅候选 · 不得替 Human 决定）

```text
P0 FIX = NOT AUTHORIZED
0016 REEXECUTION = NOT AUTHORIZED
```

## Fix A（BLOCKER 报告推荐 · 最小 diff = 1 行）

```python
# migrations_alembic/env.py（run_migrations_online 内）
_assert_effective_role(connection, url)      # :197 现状
connection.rollback()                        # ← 新增：归零只读 autobegin 事务，交还 alembic 事务管理
context.configure(                           # :198 现状
```

- 语义：断言仍 FAIL-CLOSED、仍在真实迁移连接上执行；仅将其只读 SELECT 触发的隐式事务**显式回滚**，
  使 `MigrationContext.configure` 看到干净的 non-in-transaction 连接 ⇒ `_in_external_transaction=False`
  ⇒ `begin_transaction()` 正常管理事务并在结束时 COMMIT。
- 影响面：`current`/`upgrade`/`downgrade` 三条路径一致受益；不触碰解析链/断言语义/双键边界（OI-BB 系列保持）。

## Fix B（更彻底 · +3~5 行）

用**独立短连接**执行 role assertion（临时 `engine.connect()` → SELECT → 关闭），主连接在
`context.configure` 之前零 SQL ⇒ 天然无 autobegin。

## CUSTOM

Human 自定义（例如：env.py 全面重构为显式外部事务 + 自行 commit；或其他）。

## 无论选哪种，授权后的强制序列

```text
1. env.py 修正（仅该文件 · 新 Gate）
2. new baseline（只读全锚点）
3. alembic current 探针（FAIL-CLOSED 断言仍生效）
4. 真实前进探针：upgrade 至 0016 后必须断言
   a) version 表前移 = 0016   b) C2 functiondef md5 ≠ 68678741…（post-image 新指纹）
   —— 防止再次被 no-op/回滚假象欺骗
5. downgrade 探针：恢复 pre-image（md5 = 68678741…）+ 不触碰 roles/grants/ownership
6. 再次 upgrade（最终态 = 0016）
7. 全部安全探针（正/负 · SET ROLE 反例 · uap_app 边界）
8. I01…I30 harness + 权限窗口 REVOKE + 回归
```

在获得 Human 授权前：**不得实施任何一种**。
