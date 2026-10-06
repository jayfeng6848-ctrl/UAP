# 10_OPEN_ISSUES_REGISTRY — OI / 已知问题台账

> 状态口径：RESOLVED / REGISTERED（登记未决）/ CARRIED（约束生效）；blocking 相对 = BATCH-C 实施。

| ID | 内容 | 状态 | blocking? |
|---|---|---|---|
| `OI-BB-5` | 无既有 CI/CD 载体 ⇒ 不新建 CI（B-5 CUSTOM 裁定） | RESOLVED（设计事实） | non-blocking |
| `OI-BB-11` | `config.attributes["url"]` override 通道必须保留（范围外 test_migration_failure.py 依赖） | CARRIED（约束生效） | non-blocking |
| `OI-BB-13` | URL 中 `%` 会被 alembic `set_main_option` 插值处理——URL 不得含裸 `%` | CARRIED | non-blocking |
| `OI-BB-14` | **env.py 不可作为普通模块 import**（import 即进入 Alembic 执行路径）；测试禁止 `import migrations_alembic.env`；只允许 CLI/subprocess 探针、独立可 import helper、DB 集成探针 | CARRIED（**永久约束**） | non-blocking（设计已遵守） |
| `OI-G-3` | `uap_migrator` 无 schema CREATE ⇒ 0016 执行前置。**决定性实测**：`CREATE TABLE → denied`；`CREATE OR REPLACE 自有函数 → denied`（替换自有函数也需要 schema CREATE） | RESOLVED（CF-C-1=A + CF-C-5=B 窗口期授权；语义 = **临时**前置，非永久授 CREATE） | was-blocking → resolved by decision |
| `OI-G-1` | runtime 逐表 DML 矩阵不可核定（不得扩权） | REGISTERED（BATCH-D） | non-blocking now |
| `OI-G-2` | 未来 `audit_logs` 分区不继承授权（未用 ALTER DEFAULT PRIVILEGES） | REGISTERED（BATCH-D） | non-blocking now |
| `CF-C-1` | schema CREATE vs `uap_app` 5 grants 冲突 | RESOLVED（=A，仅 uap_migrator） | resolved |
| `CF-C-2` | CREATE 后能力充分性 vs NOSUPERUSER | RESOLVED（=A） | resolved |
| `CF-C-3` | ownership transition vs residual=0 | RESOLVED（=A，无 transition） | resolved |
| `CF-C-4` | integration `reset_test_database()`（**19 文件**：integration 18 + `tests/security/test_authorization_security.py`）会摧毁 BATCH-A ownership baseline | RESOLVED（=**C 延后 BATCH-D**；本批禁 reset/重放，只用独立最小探针） | resolved by deferral |
| `CF-C-5` | 授权生命周期 | RESOLVED（=B 窗口期 + post-migration REVOKE + retain role） | resolved |
| `CF-C-6` | 0016 内容边界 | RESOLVED（=A 仅 CC-7） | resolved |
| `CF-C-7` | registry/seed 时序 | RESOLVED（=CONFIRM：CC-7 落地验证后才进入后续流程） | resolved |
| **P0-ENV（新）** | **env.py autobegin 缺陷：在线 upgrade 不持久（见 08）** | **OPEN · REAL · UNAUTHORIZED FIX** | **BLOCKING（BATCH-C 唯一阻断项）** |

## 红线（对本新 Agent 直接有效）

1. `import migrations_alembic.env` 一律禁止（OI-BB-14）。
2. 任何会 `reset_test_database()` 的 integration/security 测试在 BATCH-D 决议前禁跑（CF-C-4=C · 19 文件清单见 12）。
3. `uap_migrator` CREATE 权限只能是窗口期状态；结束时必须回到 `false`（OI-G-3 语义）。
4. P0-ENV 未修复并验证前，任何"升级成功"的断言都不可信——必须以 version 表前移 + functiondef 指纹变化为准。
