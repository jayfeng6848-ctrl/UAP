# OPEN-P10-1 BATCH-C · 0016 IMPLEMENTATION · BLOCKER REPORT（HARD STOP）

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次                       = BATCH-C 0016 IMPLEMENTATION（START = AUTHORIZED）
> IMPLEMENTATION             = BLOCKED（self-disclosed defect · 未进入持久化升级）
> 0016 文件                  = CREATED（静态审计 PASS · 未成功持久执行 · 保留为授权工件）
> 0016 执行                  = FAILED-TO-PERSIST（alembic 在线升级静默空转 · 事务从不提交）
> 受保护对象                 = 全部恢复 BATCH-A 基线（§5 终态等号组）
> 根因                       = env.py 真实缺陷（B-1 引入 · P0 级 · 自证披露 · 修复未授权）
> HARD STOP 依据             = 指令 §6（"没有新 Gate 前，不得碰 env.py"）+ HARD STOP POLICY
> ```

---

## §1 已完成步骤（全部留档 `batch_c_0016_implementation.log`）

| Phase | 动作 | 结果 |
|---|---|---|
| 0 | 实施入口基线 | PASS（零 drift：HEAD/0015 单头/角色 4/CREATE=false/grants 5/178 所有权/C2 md5） |
| 2 | CC-7 pre-image 取证 | PASS（functiondef 全文 + owner=`uap_migrator` + plpgsql + `prosecdef=false` + 触发器 `O` + registry 0 行 + agents 族 0 行） |
| 4 | 创建 `0016_open_p10_1_trust_boundary.py` | DONE（INLINE/自包含/无动态 SQL；`op.execute` 恰 2 处；禁词命中仅 docstring/注释声明区；AST OK；单头） |
| 5 | 静态审计 | PASS |
| 6 | Privilege window | 开启 PASS（deployment 身份 `uap` per D-OP101-04 + BATCH-A 台账佐证；CREATE false→true；socket 身份探针 `uap_migrator\|uap_migrator`） |
| 8 | CLI 身份探针 | PASS（`alembic current` 走通 env.py FAIL-CLOSED 断言，exit 0） |
| 8 | `alembic upgrade 0016…` | **FAILED-TO-PERSIST**（exit 0 无输出无效果 · 版本仍 0015） |
| 6↔11 | 窗口回收（提前） | PASS（REVOKE 后 CREATE=false，恢复基线） |

## §2 决定性根因（插桩证据 · 三层验证）

### §2.1 现象

`alembic upgrade 0016_open_p10_1_trust_boundary` exit 0、无输出、`alembic_version` 不变、C2 md5 不变。`alembic current` 正常（0015）。伪 revision 正确报错（升级路径存活）。`--sql` offline 正常吐 SQL（脚本侧存活）。`+1`/in-process `command.upgrade` 同样空转。

### §2.2 插桩实锤（DBAPI + MigrationContext 层）

```text
### DBAPI ROLLBACK
### begin_transaction: _in_external_transaction=True  transactional_ddl=True
### returned context type: nullcontext
### DBAPI ROLLBACK
```

`Connection.begin` 全程仅 1 次；`COMMIT` **从未发生**；连接关闭隐式 ROLLBACK。

### §2.3 因果链（alembic 1.19.2 `runtime/migration.py:151-158, :411-412`）

```text
env.py:197  _assert_effective_role(connection, url)     ← SELECT current_user, session_user
            ↓ SQLAlchemy 2.0 「autobegin」：该 SELECT 隐式开启事务
env.py:198  context.configure(connection=connection, …)
            ↓ migration.py:154  _in_external_transaction = _get_connection_in_transaction(connection) = True
env.py:204  with context.begin_transaction():
            ↓ migration.py:411  if self._in_external_transaction: return nullcontext()
            ⇒ begin_transaction 退化为空上下文 —— alembic 认为提交由「外部」负责
            ⇒ run_migrations 正常执行并打印 "Running upgrade 0015 -> 0016"
            ⇒ 无任何 COMMIT；NullPool 连接关闭 ⇒ 隐式 ROLLBACK ⇒ 全部效果蒸发
```

### §2.4 缺陷定性

- **env.py 真实缺陷（B-1 引入）**：角色断言置于 `context.configure` 之前且未归零 autobegin 事务；
- **自 B-1 起一切在线 upgrade 静默空转**；
- **为何 B-1/B-2 探针未发现**：探针 P1 为 at-head no-op（`upgrade head` 时已位于 head），空转与"成功无操作"不可区分——探针设计缺口（未覆盖"真实前进 + 持久性验证"）；
- 与 BATCH-B 前的全量回归不矛盾：B-1 之前的旧 env.py 无 pre-configure SELECT，无 autobegin，提交正常。

## §3 建议最小修复（待 Human 授权 · 本轮未动 env.py）

| 方案 | 内容 | 评估 |
|---|---|---|
| **A（推荐）** | env.py `:197` 断言之后追加一行 `connection.rollback()`（+注释：归零只读 autobegin 事务，交还 alembic 事务管理） | 最小 diff（1 行）；断言语义/FAIL-CLOSED 不变；`current`/`upgrade`/`downgrade` 行为一致；符合 OI-BB-13/14 约束 |
| B | 断言改用独立短连接（`engine.connect()` 临时会话）后关闭 | 隔离更彻底但 +3~5 行、多一次连接建立 |
| C | 不改 env.py：外层以显式外部事务托管并自行 commit | 改变调用契约、违背「env.py 自包含治理」，不推荐 |

授权修复后流程 = **env.py 修正轮（新 Gate）→ 重验 `alembic current` → B-1/B-2 探针补真实前进断言 → 重跑本报告 §1 Phase 6–11 全序列 → I01…I30 harness**。

## §4 A–E 归因

| 类 | 归因 |
|---|---|
| A（真实缺陷） | env.py B-1 引入：pre-configure SELECT → autobegin → alembic external-transaction 判定 → 无提交（**本项目自证缺陷，非 harness 缺陷**） |
| B（流程缺陷） | B-1/B-2 探针仅覆盖 at-head no-op，未断言"升级后版本表前移"（持久性） |
| C（环境因素，非缺陷） | ① venv 无 psycopg2，方言须 `postgresql+psycopg`（仓库既有约定）；② TCP 经 docker bridge 落入 scram 规则，需角色口令（`uap_migrator` 口令 = 角色名，BATCH-A 约定）；③ 容器内 local socket trust 不适用于宿主 CLI |
| D（本轮 harness 缺陷） | 首轮 P07/P16 两项（已修复复跑 23/23，见 PRE-FLIGHT 报告） |
| E（真实数据损坏） | **0**（见 §5 终态等号组） |

## §5 终态等号组（零持久副作用证明）

```text
alembic_version        = 0015_p12_indexes        （0016 未持久化）
C2 functiondef md5     = 6867874166ae36966763c1026ab2af19（未变）
owner / prosecdef      = uap_migrator / false（未变）
trigger tgenabled      = O（未变）
registry rows          = 0（acl_subject_types 无残留）
agents 族 rows         = 0
uap_migrator CREATE    = false（窗口已回收）
uap_app grants         = 5
roles                  = 4
commit / tag / push    = 0
```

## §6 HARD STOP

`BATCH-C 0016 IMPLEMENTATION = BLOCKED`。等待 Human 决定：

1. 批准 **Fix A**（env.py 一行修正）并授权 env.py 修正轮（新 Gate + 探针补真实前进断言）；
2. 或选择 Fix B / 其他方案 / 自定义。

授权后重入本报告 §1 的 Phase 6–11 序列（窗口重开 → upgrade → 全部探针 → downgrade 验证 → 回收 → I01…I30）。

**END OF OPEN-P10-1 BATCH-C 0016 IMPLEMENTATION BLOCKER REPORT（2026-09-27 · `IMPLEMENTATION = BLOCKED` · `0016 = CREATED-ONLY` · 基线完整恢复 · 零持久副作用）**
