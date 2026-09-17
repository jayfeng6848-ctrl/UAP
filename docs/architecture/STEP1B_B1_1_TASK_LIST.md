# STEP 1-B / B1-1 — Task List（Root Identity Schema）

Status: **IN PROGRESS**（本表随执行逐项更新）
范围：仅 5 张 Identity 表 —— `users` / `identities` / `credentials` / `devices` / `sessions`
来源：STEP 1-A Round 3 冻结设计 + B0（CONSTRAINT_MATRIX / INDEX_STRATEGY / TRIGGER_INVENTORY / UUID_STRATEGY）+ B1-0（Migration Contract / alembic 基建）

| # | 任务 | Status | Dependency | Expected Result | Test |
|---|---|---|---|---|---|
| B1-1.1 | `users` | ⏳ | 冻结设计 §1.1 + B0 Matrix | 平台级身份根表，tenant-independent | schema inspection |
| B1-1.2 | `identities` | ⏳ | users | 身份源表示，user_id CASCADE | FK/部分唯一测试 |
| B1-1.3 | `credentials` | ⏳ | users, identities | 仅 secret_hash，永不存明文 | security（无明文列 / active-password 唯一） |
| B1-1.4 | `devices` | ⏳ | users | 设备注册，user_id CASCADE | FK 拒绝测试 |
| B1-1.5 | `sessions` | ⏳ | users, identities, devices | 会话，identity RESTRICT / device CASCADE | FK + 状态测试 |
| B1-1.6 | FK / constraint | ⏳ | 1.1–1.5 | 与 B0 CONSTRAINT_MATRIX 一致 | test_identity_schema |
| B1-1.7 | indexes | ⏳ | 1.1–1.5 | 仅 B0 INDEX_STRATEGY 定义的 7 个非 PK/UQ 索引 | pg_indexes 断言 |
| B1-1.8 | triggers | ⏳ | 1.1–1.5 | `set_updated_at()` 函数 + 5×updated_at trigger | pg_trigger 断言 |
| B1-1.9 | Alembic migration | ⏳ | B1-0 基建 | revision `0003_b1_1_root_identity`（up/down 完整） | alembic upgrade head |
| B1-1.10 | migration tests | ⏳ | 1.9 | fresh DB → 5 表 + 无其它业务表 | test_alembic_smoke（更新基线） |
| B1-1.11 | rollback / rerun | ⏳ | 1.9 | downgrade 后再次 upgrade 成功 | smoke downgrade + rerun |
| B1-1.12 | security tests | ⏳ | 1.2–1.5 | duplicate / FK / plaintext 禁止 / 部分唯一 | test_identity_security.py |
| B1-1.13 | full regression | ⏳ | 全部 | pytest 全量通过 | pytest |
| B1-1.14 | architecture guard | ⏳ | 全部 | 无 Core→Domain / Identity→Domain 违规 | pytest tests/architecture |
| B1-1.15 | final gate | ⏳ | 全部 | 22 项门禁 PASS；正式 uap 库 untouched | 本报告 |

> **范围护栏**：不得创建 tenants/spaces/roles/permissions/memberships/resources/agents/tools/ai_*/events/audit_logs 及任何 Domain 表；不得因 FK 方便提前建表；不修改 API/Socket/Agent/前端/业务 Core。
