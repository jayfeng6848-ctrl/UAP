# UAP Migration Strategy

Status: **DESIGN — STEP 1-A**（选型完成，**不实施**，STEP 1-B 执行）

## 1. 现状（STEP 0）

`infrastructure/database/migration.py`：顺序执行 `migrations/NNNN_name.sql`，`schema_migrations` 表记录 `(version, name, checksum, applied_at)`，每份迁移与其账本写入在同一事务。

它解决了 STEP 0 需要的最小问题：有序、幂等、校验和防篡改、事务性。已在 SQLite 与 PostgreSQL 16.15 上验证。

## 2. 为什么继续自研不合适

| 问题 | 影响 | 严重度 |
|---|---|---|
| **语句切分脆弱** | `--` 注释剥离 + 分号切分，遇到 `$$ ... $$` 函数体、字符串内分号、`CASE ... END;` 即解析错误 | **P0**（STEP 1-B 必然要写函数/触发器，如 `set_updated_at()`） |
| **无 autogenerate** | 模型与库结构靠人工同步，漂移不可检测 | P1 |
| **无 downgrade** | 只能向前，回滚靠备份恢复 | P1 |
| **无版本图** | 多人并行开发两个 migration 都叫 `0007_*` → 冲突只能靠人沟通；无 merge 能力 | P1 |
| **无依赖/分支管理** | 无法表达"基于哪个 revision"、无法多 head 合并 | P1 |
| **无离线 SQL 生成** | DBA 需要"先给我 SQL 审核"流程时无解 | P2 |
| **生态与心智** | 新人无文档、无社区、无工具链（lint、CI 插件） | P2 |
| **测试能力弱** | 无法自动跑 up→down→up 验证可逆性 | P2 |

结论：自研 runner 的复杂度会随 schema 规模**线性转指数**增长，而它要解决的问题 Alembic 已解决十五年。**继续自研是净负债。**

## 3. 为什么 Alembic 合适

| 契合点 | 说明 |
|---|---|
| 与 SQLAlchemy 同源 | UAP 已用 SQLAlchemy 2.0，Alembic 直接复用 engine 与 metadata，零额外抽象层 |
| 版本图 + 多 head merge | 支持并行分支与 `alembic merge`，团队开发必需 |
| autogenerate | `--autogenerate` 对比 metadata 与库结构，生成草稿（**人工审核后使用**） |
| 事务性 DDL | PostgreSQL DDL 支持事务，Alembic 默认单事务；可按需关闭（`transaction_per_migration`） |
| 离线 SQL | `alembic upgrade head --sql` 输出 SQL 供 DBA 审核，符合变更管理流程 |
| 可逆性 | `downgrade()` 强制思考回滚；CI 可跑 up→down→up |
| 生态成熟 | 与 CI、代码评审、运维流程天然对接 |

**不适合/需注意的点**

| 风险 | 缓解 |
|---|---|
| autogenerate 不完美（会漏 check constraint、分区、RLS、trigger） | **只当草稿**，必须人工复核；复杂对象手写 `op.execute` |
| 与纯 SQL 迁移混用需要纪律 | 统一入口：全部走 Alembic；历史 `0001` 用 `alembic stamp` 对齐，不再新增裸 SQL 文件 |
| 需要应用代码可导入（autogenerate 依赖 metadata） | 迁移脚本不 import domains；只依赖 `core`/`infrastructure` 的 metadata |
| 团队学习成本 | 提供 `docs/operations/migrations.md` 与 Makefile 封装（`make db-upgrade`） |

## 4. 结论

> **STEP 1-B 将迁移工具切换为 Alembic，保留 STEP 0 的 checksum 精神与既有 `schema_migrations` 账本兼容。**

不是"为了升级工具而升级"：直接触发因素是 **P0 语句切分缺陷**（`$$` 函数体），它在 STEP 1-B 写 `set_updated_at()` trigger 时必然引爆。

## 5. 迁移到 Alembic 的路径

1. 保留 `migrations/0001_platform_baseline.sql` 的历史事实，**不加新裸 SQL**
2. `alembic init migrations/alembic`（或独立 `alembic/` 目录），配置 `sqlalchemy.url` 从 `DATABASE_URL` 读取
3. 对已应用 `0001` 的环境执行 `alembic stamp 0001_baseline`（把现有库标记为基线），避免重放
4. 后续所有变更以 `alembic revision -m "..."` 创建，revision id 采用 **4 位序号 + 语义 slug**（`0002_add_identity_tables`），兼顾可读与排序
5. 旧 runner 保留一个发布周期作为只读工具（`--status` 查看历史），随后移除

## 6. Versioning

| 项 | 规则 |
|---|---|
| 命名 | `NNNN_snake_case_slug.py`，`NNNN` 四位递增，slug 用动词短语（`add_identity_tables`） |
| revision id | 与文件名前缀一致，便于人读与 diff |
| down_revision | 单一线性主干；并行分支必须 `alembic merge`，merge 后主干恢复线性 |
| 一个 revision 一件事 | 禁止"大杂烩"revision（无法部分回滚） |
| 数据迁移与结构迁移分离 | 结构变更用 `op.*`，数据回填单独 revision（可分批、可限流） |

## 7. Upgrade / Downgrade 策略

### 7.1 原则：**expand → migrate → contract**

| 阶段 | 发布 | 操作 | 可回滚性 |
|---|---|---|---|
| **Expand** | N | 加新列/新表（可空、无默认值或带默认值但 PG11+ 为元数据操作）、加索引 `CONCURRENTLY` | 完全可回滚 |
| **Migrate** | N+1 | 应用双写 / 后台回填（分批、限流） | 可停可退 |
| **Contract** | N+2 | 切换读取、加 NOT NULL / 唯一约束、删旧列 | 破坏性，需评估 |

### 7.2 downgrade 要求

| 变更类型 | downgrade 要求 |
|---|---|
| 加表 / 加可空列 / 加索引 | **必须提供**真实 `downgrade()` |
| 加 NOT NULL / 加唯一约束 / 改类型 | **必须提供**（或注明"仅通过备份恢复"，需审批） |
| 删列 / 删表（contract 阶段） | 提供"重建空结构"的 downgrade，并显式注明**数据不可恢复** |
| 数据回填 | downgrade 为 no-op（数据保留无害）或清理脚本 |

### 7.3 生产默认策略

- **生产默认不执行 downgrade**，优先 forward-fix（再发一个 revision 修正）
- downgrade 只在以下场景使用：预发/测试环境、演练、变更窗口内的紧急回退（且已确认数据兼容）

## 8. Checksum / 不可变 revision

Alembic 自带 revision hash，但**不阻止**修改已应用文件。因此保留 STEP 0 的实践并加 CI 门禁：

1. 每个 revision 文件的 SHA-256 记入 `schema_migrations.checksum`（沿用现有列）
2. CI 校验：已存在于主干（已合并到 `main`）的 revision 文件**不得修改**（`git diff` 检测 + 与库中 checksum 比对）
3. 需要修改已发布 revision → 必须新增一个修正 revision，禁止改写历史
4. 运行时保留"checksum 漂移即报错"的行为（现有 `MigrationError` 语义）

## 9. Production Migration Policy

| 项 | 规则 |
|---|---|
| 执行时机 | 变更窗口；DDL 与代码发布解耦（结构先于代码上线） |
| 执行账号 | `uap_migrator`（仅迁移窗口授予 DDL）；应用账号 `uap_app` 无 DDL 权限 |
| 前置 | 备份/PITR 可用 → 在预发环境完整演练 → 生成 `--sql` 供审核 |
| 大表变更 | `CREATE INDEX CONCURRENTLY`（非事务，需 `transaction_per_migration=false` + 失败清理脚本）；`ADD COLUMN` 不带默认值；回填分批（≤5000 行/批 + sleep） |
| 锁 | 设置 `lock_timeout`（如 3s）与 `statement_timeout`，避免 DDL 长时间阻塞业务 |
| 验证 | 迁移后跑健康检查 + 冒烟；失败立即进入回滚流程 |
| 并发 | 部署编排保证**单实例**执行迁移（leader 锁），避免多副本同时 DDL |

## 10. Backup Policy

| 层 | 策略 |
|---|---|
| PITR | WAL 归档，保留 7–14 天；任意时间点恢复 |
| 逻辑备份 | 每日 `pg_dump`（自定义格式），保留 30 天，异地/对象存储加密存放 |
| 迁移前 | 强制 snapshot（云盘）或 `pg_dump --schema-only` + 全量；**无备份不迁移** |
| 恢复演练 | 每季度一次：从备份恢复到临时实例 → 跑 `pytest -m integration` → 记录 RTO/RPO |
| 密钥 | 备份加密密钥与数据库凭据分离管理，不入仓库 |

## 11. Failure Recovery

| 场景 | 处理 |
|---|---|
| 事务性 DDL 失败 | PostgreSQL DDL 支持事务 → 自动回滚，库保持迁移前状态；修复后重跑 |
| **非事务性操作失败**（`CREATE INDEX CONCURRENTLY`、`ALTER TYPE ... ADD VALUE`） | 留下 `INVALID` 索引 / 部分变更 → 预案脚本必须显式处理：`DROP INDEX CONCURRENTLY IF EXISTS`；revision 中写明该 revision 非事务 |
| 回填中断 | 回填幂等（按主键区间 + 状态标记），可安全重跑 |
| 迁移后应用异常 | 优先 forward-fix；必要时按 §10 恢复到迁移前时间点 |
| 迁移死锁 | `lock_timeout` 触发中止 → 重试；反复失败则人工介入（查 `pg_locks`） |
| 多副本并发迁移 | leader 锁（数据库 advisory lock）保证单执行者 |

## 12. CI 门禁（STEP 1-B 建立）

1. **迁移冒烟**：临时 PostgreSQL（docker）→ `alembic upgrade head` → `downgrade base` → `upgrade head`（验证可逆 + 幂等）
2. **漂移检测**：`alembic check`（对比 metadata）→ 有漂移即失败
3. **checksum 门禁**：已发布 revision 文件不得修改
4. **SQL 审核**：`upgrade head --sql` 输出入库，供人工评审
5. **禁止项扫描**：迁移脚本中不得出现 `DROP TABLE`（除非 contract revision 并标注）、不得出现业务词汇

## 13. 本阶段不做

- 不创建 Alembic 目录、不写 `env.py`、不生成 revision
- 不删除 STEP 0 的 runner（先切换，后下线）
- 不改变现有 `0001_platform_baseline.sql` 内容
