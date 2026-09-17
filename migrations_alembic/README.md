# UAP Alembic Migrations

Alembic 是 UAP **唯一** schema 变更入口（自 STEP 1-B 起）。

```bash
# 开发/CI（需要 DATABASE_URL 指向目标库；缺省用 alembic.ini 的 dev DSN）
alembic upgrade head
alembic downgrade base
alembic current
alembic history
```

## Advisory Lock

每次迁移在事务内先获取 PostgreSQL advisory lock（key `(5_587_280, 1)`，
见 `env.py` 的 `MIGRATION_LOCK_KEY`），保证任意时刻只有一个 runner 执行 DDL。

| 模式 | 行为 |
|---|---|
| `wait`（默认） | `pg_advisory_xact_lock` 阻塞直到锁可用 |
| `fail` | `pg_try_advisory_xact_lock`，拿不到立即报错退出 |
| `timeout` | `SET LOCAL lock_timeout` 后阻塞等待（秒数见 `UAP_MIGRATION_LOCK_TIMEOUT_SECONDS`） |

选择方式：环境变量 `UAP_MIGRATION_LOCK_MODE`，或程序化调用时
`config.attributes["lock_mode"] = "fail"`。

## 版本

- `0001_baseline`：历史对齐点（no-op，对应旧自研 runner 的 0001 .sql）
- `0002_b1_0_infrastructure`：B1-0-INFRASTRUCTURE-ONLY（`uap_uuid_v7()` 函数）

**B1-0 未创建任何业务表。** 29 张核心表由后续 B1-N revisions 分阶段建立。

## 纪律（详见 STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md）

- schema 与 data/seed 分离；每个 revision 必须实现 downgrade
- 禁止 DROP ... CASCADE 做业务删除；禁止 CREATE INDEX CONCURRENTLY 进入默认事务流
- revision 发布后不改写（追加新 revision）
