# 08_CURRENT_BLOCKER — 当前真实 Blocker（交接包最重要文件）

## 状态（2026-09-27 实测）

```text
0016                    = CREATED（文件存在 · 静态审计 PASS）
0016 static audit       = PASS
0016 upgrade persistence= FAILED（exit 0 · 无输出 · DB 无变化 · 静默回滚）
0016 downgrade          = NOT REACHED
live alembic_version    = 0015_p12_indexes（0016 未持久化）
C2 md5                  = 6867874166ae36966763c1026ab2af19（未变）
uap_migrator CREATE     = false（窗口已回收）
```

## 定性（必须原样接受）

这是 **REAL ENGINEERING DEFECT · P0**：

- ❌ 不是 harness defect（harness 独立复算过；缺陷在产品文件 env.py）；
- ❌ 不是 environment issue（ psycopg/网络/口令问题均已排除并单独解决）；
- ❌ 不是 database corruption（对象/所有权/版本表全部完好）。

## 根因链（完整 · 已插桩实证）

```text
migrations_alembic/env.py:197  _assert_effective_role(connection, url)
        ↓
SELECT current_user, session_user            （在 context.configure 之前执行）
        ↓
SQLAlchemy 2.0 autobegin                     ← 该 SELECT 隐式开启事务
        ↓
context.configure(connection=…) 时连接已 in-transaction
        ↓
alembic/runtime/migration.py:154
    _in_external_transaction = _get_connection_in_transaction(connection)  = True
        ↓
env.py:204  context.begin_transaction()
        ↓
migration.py:411  if self._in_external_transaction: return nullcontext()
        ↓
（nullcontext：alembic 认为提交由「外部事务」负责）
        ↓
migration 执行（日志打印 "Running upgrade 0015_p12_indexes -> 0016_open_p10_1_trust_boundary"）
        ↓
COMMIT never called
        ↓
NullPool 连接关闭
        ↓
DBAPI ROLLBACK ⇒ 所有 DDL/版本表更新蒸发 ⇒ exit 0 静默"成功"
```

## 插桩证据（DBAPI + MigrationContext 层）

```text
### DBAPI ROLLBACK
### begin_transaction: _in_external_transaction=True  transactional_ddl=True
### returned context type: nullcontext
### DBAPI ROLLBACK
```

（`Connection.begin` 全程 1 次；`COMMIT` 从未发生。日志：`uap-stage3-evidence/batch_c_0016_implementation.log`）

## 排除记录（都试过、都不是）

```text
伪 revision       → 正确报错（升级路径存活）
offline --sql     → 正常吐 SQL（脚本侧存活）
+1 / in-process   → 同样空转（非 CLI 参数问题）
双 alembic_version 表 / 角色级 search_path → 不存在
psycopg2 缺失     → 已解决（方言 = postgresql+psycopg，仓库约定）
TCP 口令          → 已解决（uap_migrator 口令 = 角色名，BATCH-A 约定）
```

## 为什么之前没发现（B-1/B-2 探针缺口）

B-1/B-2 探针 P1 是 **at-head no-op**（`upgrade head` 时 DB 已位于 head）——"静默空转"与"成功无操作"不可区分。
**探针铁律（新增）**：升级探针必须断言「version 表真实前移 + 副作用落库持久」。

## 影响面

- 自 BATCH-B B-1 起，**任何**经此 env.py 的在线 upgrade/downgrade 都不会持久；
- B-1 之前的旧 env.py 无 pre-configure SELECT，历史上 636 全量回归有效；
- integration 套件中任何依赖 alembic CLI 升级的测试（B-4 之后同样受影响）——BATCH-D 排查；
- 与 0016 内容无关：换任何迁移文件都会同样失败。

## 当前处置

- env.py **未修改**（无授权 · 指令 §6）；
- privilege window 已回收（CREATE=false）· 基线完整恢复（零持久副作用）；
- 0016 文件保留为授权工件；
- 报告：`docs/architecture/OPEN_P10_1_BATCH_C_0016_IMPLEMENTATION_BLOCKER_REPORT.md`（含 A–E 归因与 Fix 建议）。
