# P0_FIX_ACCEPTANCE_RECORD

> UAP · OPEN-P10-1 · BATCH-C 唯一阻断项之修复验收
> 状态：STRICT READ-ONLY 验收（无代码/迁移/DB 变更）
> 日期：2026-09-27 · 本文件位于 Agent 工作区，不在 UAP 仓库内（待 Human 指示是否落入 docs/architecture/）

---

## 1. 变更身份

```text
file        = migrations_alembic/env.py（唯一修改文件）
pre-image   = cc569fd54e5e769e6651a76f0ff8a8c5658a1d1168f0c9065f53fa173ac98ed6
post-image  = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a
diff        = +4 / -0
```

唯一语义新增：

```python
connection.rollback()
```

（另 3 行为解释性注释，逐字来自 Human 授权文本。）

插入位置：`_assert_effective_role(connection, url)` 之后、`context.configure(connection=connection, ...)` 之前（落地后行号 198–201）。

---

## 2. 保留性核对（逐项实测）

```text
assertion before configure = retained
   :197  _assert_effective_role(connection, url)   -> :202 context.configure(...)
   :113  connection.execute(text("SELECT current_user, session_user")).one()
   :115  if effective != expected: -> :116 raise MigrationIdentityError

FAIL-CLOSED = retained
   role mismatch            -> MigrationIdentityError（探针 S1 · exit=1）
   missing migration DSN    -> MigrationIdentityError（探针 S2 · exit=1）

DSN separation = retained
   env.py 仅读取 UAP_MIGRATION_DATABASE_URL（:79）与两个锁相关变量（:126/:155）
   未出现对 DATABASE_URL 取值的读取；alembic.ini 无可执行 DSN

role assertion = retained（见上；签名与语义均未改）

advisory lock = unchanged
   :135 _acquire_lock() 定义不变；:208 with context.begin_transaction() -> :209 _acquire_lock(...) -> :210 run_migrations()
   UAP_MIGRATION_LOCK_MODE / UAP_MIGRATION_LOCK_TIMEOUT_SECONDS 语义不变
   lock_mode=fail 实测仍 MigrationLockError（探针 S5 · exit=1）；锁释放后恢复（S5b · exit=0）
```

---

## 3. 结论

```text
P0 env.py fix = ACCEPTED
```

```text
本记录未修改任何文件；验收过程仅执行只读查询与 Alembic 只读命令。
```

