# STEP 1-B / B1-0 — Migration Implementation Contract

Status: **IMPLEMENTATION CONTRACT（B1 起强制执行）**
来源：B0 GATE（Migration Strategy PASS + P1 遗留：并发互斥）+ MIGRATION_STRATEGY.md
基线：`72ade9f` · 本文档随 B1-0 落地的 Alembic 基建一同生效

> 本 Contract 是 **B1 全阶段 migration 的唯一行为规范**。任何 B1 版本都必须遵守；与旧自研 runner（`infrastructure/database/migration.py`）的并存规则见 §16。

---

## 1. Migration Runner 唯一入口

- **唯一入口**：项目根 `alembic.ini` + `migrations_alembic/`（env.py / versions/）
- 命令形态：
  ```bash
  alembic upgrade head          # 正式/测试库升级
  alembic downgrade base        # 回滚
  alembic history               # 版本图查看
  alembic check                 # 模型漂移检测（可选）
  alembic heads                 # 头部一致性
  ```
- **禁止**绕过 env.py 直接 psql 执行 DDL（除非 destructive 迁移的显式独立脚本，见 §13）
- 程序化调用：`alembic.config.Config` + `alembic.command.upgrade/downgrade`（测试与 CI 用）

## 2. PostgreSQL Advisory Lock（B0 P1 解决）

迁移执行前必须获取数据库级互斥锁，防止并发 runner 同时执行 DDL。

```sql
SELECT pg_advisory_xact_lock(:key1, :key2);     -- 阻塞等待（默认 wait）
SELECT pg_try_advisory_xact_lock(:key1, :key2); -- 立即失败（fail 模式）
```

- **锁类型**：事务级（xact）—— 锁绑定当前事务；**事务 commit/rollback / 连接关闭自动释放**，异常也不会永久残留（满足 Contract 测试 3/4）
- 不使用 session 级 `pg_advisory_lock`（连接归还池后可能残留，需手工 UNLOCK，风险高）

## 3. Lock Key（稳定且文档化，禁止随机）

| 项 | 值 | 含义 |
|---|---|---|
| key1 | `5_587_280`（0x554150 = `'UAP'` 三字节的整数值） | 平台命名空间 |
| key2 | `1` | migration major 版本 |

- 代码内常量：`MIGRATION_LOCK_KEY = (5_587_280, 1)`（定义于 `migrations_alembic/env.py`，单点维护）
- **禁止**随机/时间戳/主机相关 key；**禁止**依赖应用层 mutex；**禁止**假设"部署系统不会并发"

## 4. Lock 获取策略（三模式）

`env.py` 通过 `config.attributes["lock_mode"]` 或环境变量 `UAP_MIGRATION_LOCK_MODE` 选择：

| 模式 | SQL | 行为 | 使用场景 |
|---|---|---|---|
| `wait`（默认） | `pg_advisory_xact_lock` | 阻塞直到锁可用，然后继续 | 生产/CI（串行化，无 DDL 并发） |
| `fail` | `pg_try_advisory_xact_lock` | 拿不到立即抛 `MigrationLockError` | 快速失败测试、双 runner 验证 |
| `timeout`（可选） | `SET LOCAL lock_timeout` + 阻塞锁 | 等待 N 秒后失败 | 未来需要限时等待时 |

- **并发语义**：wait 模式下 Runner B 阻塞在锁上，**直到 Runner A 整个迁移事务提交/回滚后才获得锁** —— B 期间不执行任何 DDL；fail 模式 B 直接退出（exit code 非 0）

```
Runner A: BEGIN → LOCK → migrations... → COMMIT (释放)
Runner B: BEGIN → LOCK(阻塞/失败) → ...
```

## 5. Transaction Policy

- 默认 **transaction_per_migration = false**：一次 `alembic upgrade head` 的**全部迁移在同一事务**内执行；任一失败整体回滚（满足"中途失败无半成品"）
- 需要逐迁移独立事务的命令用 `alembic upgrade <rev1>:<rev2>` 分段执行（人工控制）
- **非事务 DDL**（`CREATE INDEX CONCURRENTLY` 等）严禁进入默认流；必须作为**独立 revision 显式标注** `transaction_per_migration = True` + 运维手册执行（见 §13）
- 锁与迁移同事务：锁获取位于 `context.begin_transaction()` 内第一个语句 —— 保证"持锁 ↔ 迁移原子结束"

## 6. Failure Behavior

| 场景 | 行为 |
|---|---|
| 迁移中途异常 | 事务回滚，DB 无半成品；`alembic_version` 不推进 |
| 锁获取失败（fail 模式） | 立即抛错退出，不执行任何 DDL |
| 连接断开 | xact 锁随事务/连接释放；无残留（测试 3） |
| 数据库重启 | advisory lock 是内存状态，重启即清（测试 4） |
| 失败后重试 | 修复问题后重新执行同一条 `alembic upgrade head`（幂等） |

## 7. Migration Version Tracking

- `alembic_version` 表记录当前 revision（单行）；分支用 `down_revision` 图表达
- 版本命名：`<4位序号>_<snake_case 语义>`；基线 = `0001_baseline`（**历史对齐点，no-op**，代表旧自研 runner 已应用的 `0001_platform_baseline.sql`）
- `alembic heads` 必须始终为单头（禁并行分支，除非显式 merge revision 并经审计）
- 已发布 revision **永不改写文件**（只允许追加新 revision）

## 8. Checksum / Integrity

- revision 文件内容即事实；**不额外维护 checksum**（git 提供文件完整性；alembic 不内置 checksum）
- 漂移检测：`alembic check`（需 autogenerate 元数据就绪后启用）+ CI 冒烟：`upgrade head → downgrade base → upgrade head`（可逆性证明）
- 与旧自研 runner 的 schema_migrations 账本：**并存期内互不干预**；正式切换到 Alembic 后旧账本冻结为历史（见 §16）

## 9. Upgrade Strategy

- 开发/测试：单命令 `alembic upgrade head`
- 生产：`alembic upgrade head` 前置三件事：①备份（§12）②lock wait ③观察 `alembic_version` 从旧 → 新
- 每个 revision 的 upgrade 必须：声明式表对象优先（`op.create_table`）；复杂对象（函数/trigger/分区/RLS）用 `op.execute` + 显式注释；**禁止在一个 revision 里混 schema 与 seed 数据**（数据迁移见 §14）

## 10. Downgrade Strategy

- 每个 revision 必须实现 downgrade（反向 DROP，顺序与 upgrade 相反）
- 分区表：先 drop 子分区再 drop 父表（B0 DEPENDENCY §9）
- `downgrade base` 用于测试可逆性；生产回滚 = 备份恢复优先，downgrade 仅限"上一版本 + 数据无损已验证"
- **禁止 downgrade 删除审计/不可变类数据**（audit_logs 分区按保留期 drop，不随版本回滚）

## 11. Production Migration Policy

- 迁移窗口：维护时段；`pg_advisory_xact_lock` 确保同刻单 runner
- 顺序：备份 → `alembic upgrade head` → 冒烟（health/ready）→ 观察错误日志
- 迁移用户：专用 `uap_migrator`（DDL 权限）；运行时 `uap_app` 无 DDL
- 每次生产迁移打 commit；DB schema 状态与代码版本一一对应（deploy 清单记录 revision）

## 12. Backup Requirement

- **任何生产 DDL 前必须有备份**：PITR（WAL 归档）为基座 + 迁移前 `pg_dump`（一致性快照）
- destructive migration（§13）执行前额外要求：快照恢复演练通过（恢复时间目标验证）

## 13. Destructive Migration Policy

- destructive = DROP TABLE / DROP COLUMN / 类型变更 / 数据重写
- 审批：revision 文件头标注 `# destructive: true` + 说明 + 迁移前备份校验
- 分步：`CREATE 新结构 → 双写/迁移数据（§14）→ 验证 → 停写 → rename/swap → DROP 旧`
- 避免 `DROP ... CASCADE`（审计面扩大）；业务表删除一律经 archive/soft delete/purge（P2-03）

## 14. Data Migration Policy

- data migration 与 schema migration 分 revision；禁止"建表+插数据"同 revision
- 数据迁移可重入：幂等（`ON CONFLICT` / `WHERE NOT EXISTS`）
- 大批量数据迁移：分批（≤ 1000/批）+ 进度日志 + 失败续跑（断点）；不阻塞线上（低峰执行）
- seed/built-in 数据（P13）单独 revision，仅在空库/首次安装时全量，重复执行幂等

## 15. 本 Contract 的验证（B1-0 落地测试）

| 测试 | 文件 |
|---|---|
| 单 runner 正常 | `tests/integration/test_migration_lock.py` |
| 双 runner 互斥（fail + wait） | 同上 |
| 失败 → 锁释放/无残留 | 同上 |
| 连接关闭/重启锁不残留 | 同上 |
| 空库 smoke（upgrade head → downgrade base） | `tests/integration/test_alembic_smoke.py` |
| 可逆性（up→down→up） | 同上 |
| 失败迁移事务回滚 | `tests/integration/test_migration_failure.py`（临时坏 revision） |

## 16. 与旧自研 Runner 的并存（过渡期）

- 旧 `scripts/migrate.py` + `infrastructure/database/migration.py` **只读保留**，不再新增 `.sql`
- `migrations/*.sql` 冻结；新 schema 全部走 Alembic（`migrations_alembic/`）
- 正式库从 0 业务表起步：B1 起 Alembic 是**唯一建表入口**
- 一个发布周期后旧 runner 下线（README 标注 deprecation）

> **[D-PLAT-07 注记 · 2026-09-23]** 「旧 runner 下线」条款的**启动入口部分**已执行完毕：应用启动不再调用 legacy runner（`ENABLE_MIGRATIONS_ON_STARTUP` 与启动分支已删除），runtime 的 schema 权威改为构建期从 Alembic 图推导的工件 + `/ready` 严格相等门。
> 关联：D-PLAT-07.a（本文档 §16「一个发布周期后旧 runner 下线」与「只读保留」两条）
> 性质：状态更新 + 交叉引用。**不修改本文档既有结论** —— 文件与本体**仍全部保留**（`migrations/*.sql` · `scripts/migrate.py` · `scripts/doctor.py` · `infrastructure/database/migration.py` 及其测试），删除其文件的决定**仍未作出**；运维契约见 `docs/operations/DEPLOYMENT_AND_RECOVERY.md`（D-R-3）。

---

## 附：B1-0 落地物

- `alembic.ini`（项目根）
- `migrations_alembic/env.py`（advisory lock + wait/fail 模式 + URL 解析）
- `migrations_alembic/versions/0001_baseline.py`（no-op 历史对齐点）
- `migrations_alembic/versions/0002_b1_0_infrastructure.py`（**B1-0-INFRASTRUCTURE-ONLY**：`uap_uuid_v7()` 函数；无任何业务表）
- 测试：lock / smoke / failure
