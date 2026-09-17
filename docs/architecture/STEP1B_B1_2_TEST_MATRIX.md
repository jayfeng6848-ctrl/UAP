# STEP 1-B / B1-2 — Test Matrix（Tenant / Space Foundation）

Status: **PREP ONLY — 本阶段只定义测试，不实现测试代码**
执行环境：disposable `uap_b1_test`（或新建 `uap_b1_2_test`）；**正式 `uap` 库不被测试触碰**
配套：`STEP1B_B1_2_CONSTRAINT_MATRIX.md` / `SCHEMA_REVIEW.md` / `INDEX_STRATEGY.md` / `TRIGGER_STRATEGY.md`

图例：`⏳ FUTURE` = 依赖 roles（本阶段不适用）；`A/B` = 依赖 §5 前向依赖方案的最终选择。

---

## 1. Schema

| # | 测试 | 期望 |
|---|---|---|
| S1 | 4 张新表存在（tenants/spaces/tenant_memberships/memberships） | table_exists |
| S2 | **精确表数量**：public = 5 Identity + 4 B1-2 + alembic_version = **10** | count == 10 |
| S3 | 无 roles / permissions / resources / acl / agents / tools / ai_* / events / audit_logs | 表集合 disjoint |
| S4 | 每表 PK = uuid，DEFAULT `uap_uuid_v7()` | information_schema + pg_attrdef |
| S5 | FK 方向与 ON DELETE 符合 Matrix（`spaces.tenant_id RESTRICT`、membership 关系行 CASCADE、owner SET NULL） | referential_constraints.delete_rule |
| S6 | UNIQUE：`uq_tenants_slug`、`uq_spaces_key`(部分)、`uq_tenant_memberships`、`uq_memberships`(部分) | pg_indexes；重复插入被拒 |
| S7 | CHECK：tenants status/slug、spaces status/kind/visibility、membership status | 非法值拒绝 |
| S8 | NOT NULL / DEFAULT 符合 Matrix | information_schema.columns |
| S9 | 索引集合 == INDEX_STRATEGY §5（7 个） | pg_indexes 差集为空 |
| S10 | updated_at trigger 4 个 + `tg_membership_tenant_consistency` 存在 | pg_trigger |
| S11 | B1-1 五表结构与约束**未变化**（回归快照） | 与 B1-1 断言一致 |

## 2. Isolation

| # | 测试 | 期望 |
|---|---|---|
| I1 | Space 必须有 tenant（tenant_id NOT NULL） | NULL 插入被拒 |
| I2 | Space 不能改属其它租户（无多租户归属） | tenant_id 单列，无关联表 |
| I3 | memberships.tenant_id 与 spaces.tenant_id 不一致 → trigger 拒绝 | RAISE |
| I4 | memberships.tenant_id 随 space 更新不一致 → UPDATE 被拒 | RAISE |
| I5 | 跨租户访问（用 A 租户成员访问 B 租户 Space）→ 授权层 DENY | 无 membership 行 → DENY（本阶段 DB 层：B 租户 space 无该 user 的 membership） |
| I6 | 跨空间访问（同租户不同 Space 无 membership）→ DENY | 无 memberships 行 |
| I7 | 删除有 Space 的 Tenant → RESTRICT 拒绝 | FK violation |
| I8 | 删除有 membership 的 Space | FK CASCADE（关系行）或 purge job 先清；断言无孤儿 membership |

## 3. Membership

| # | 测试 | 期望 |
|---|---|---|
| M1 | 重复 tenant_memberships (tenant_id,user_id) → 拒绝 | UQ |
| M2 | 重复 memberships (space_id,user_id) 且 removed_at IS NULL → 拒绝 | 部分 UQ |
| M3 | removed 的 membership 允许同一 (space,user) 再插入 | 部分 UQ 排除 removed 行 → 通过 |
| M4 | invalid user（不存在 user_id）→ 拒绝 | FK |
| M5 | invalid tenant → 拒绝；invalid space → 拒绝 | FK |
| M6 | 删除 user → 其 tenant_memberships / memberships 级联清理 | CASCADE |
| M7 | 删除 tenant → tenant_memberships 级联；memberships（冗余 tenant_id）级联 | CASCADE |
| M8 | 删除 space → memberships 级联 | CASCADE |
| M9 | membership status 枚举非法 → 拒绝 | CK |
| M10 | `role_id` 语义（B1-2, D-01） | 列存在、可 NULL、**无 FK**（pg_constraint 中无指向 roles 的 FK） |
| M11 | `owner_id` 语义（D-03 未批准前） | 不实现 ON DELETE 行为；删除 owner **不得**删除 Space（回归断言：Space 仍存在） |

## 4. Scope（角色作用域）

### B1-2 阶段（应用层 fail-closed，DB 无 roles，D-02）

| # | 测试 | 期望 |
|---|---|---|
| SC0-a | `roles` 表不存在（本阶段未创建） | information_schema 无 roles / permissions |
| SC0-b | migration 代码中无指向 roles 的 FK | pg_constraint 无相关 FK |
| SC1 | 授权层：不存在 role（role_id NULL / 引用不存在） → DENY | 应用层 fail-closed |
| SC2 | 授权层：非 TENANT role 用于 `tenant_memberships` → DENY | 应用层 |
| SC3 | 授权层：非 SPACE role 用于 `memberships` → DENY | 应用层 |
| SC8 | Tenant 成员不自动成为 Space 成员（无 memberships 行） | 查询无 membership → 访问 DENY |

### B1-3 阶段（DB 强制，D-02 验收 5 项）

| # | 测试 | 期望 |
|---|---|---|
| SC4 | TENANT role → `tenant_memberships` | **PASS** |
| SC5 | SPACE role → `tenant_memberships` | **DENY**（trigger RAISE） |
| SC6 | SPACE role → `memberships` | **PASS** |
| SC7 | TENANT role → `memberships` | **DENY**（trigger RAISE） |
| SC9 | 不存在 role（FK 违反） | **DENY**（FK violation） |
| SC10 | 默认 tenant role = `tenant_member`；默认 space role = `space_member` | PASS |
| SC11 | B1-3 补 FK 后数据一致性验证（无孤儿 role_id） | 全部 role_id 可解析到 roles 行 |

## 5. Migration

| # | 测试 | 期望 |
|---|---|---|
| MG1 | fresh DB → `upgrade head` → 4 张新表 + 既有 5 表 | version = B1-2 revision |
| MG2 | rerun `upgrade head` | no-op，无破坏 |
| MG3 | `downgrade -1` / `base` → B1-2 对象全部撤销（表/trigger/索引） | 表不存在，B1-1 五表仍在（若只 down 一级） |
| MG4 | 再次 `upgrade head` | 成功回到 head |
| MG5 | 失败 revision → 整事务回滚 + advisory lock 释放 + 无半成品 | 复用 B1-0 failure 机制 |
| MG6 | 迁移期间第二 runner（fail 模式）被拒 | 复用 B1-0 lock 测试 |
| MG7 | 迁移锁在完成后释放 | pg_locks 零残留 |
| MG8 | B1-1 数据在 B1-2 升级后不变（若预置数据） | 行数/内容一致 |

## 6. Regression

| # | 测试 | 期望 |
|---|---|---|
| R1 | B1-0：advisory lock / concurrency / failure recovery 全通过 | 既有 12 项 |
| R2 | B1-1：Identity schema + security 19 项全通过 | 既有 19 项 |
| R3 | Architecture Guard（core→domains 等） | 9 passed |
| R4 | 正式 `uap` 库表数仍为 0（测试未触碰） | count == 0 |
| R5 | 全量 `pytest` | 无回归 |
| R6 | D-04：RLS 未启用（无 RLS policy 对象） | `pg_policies` 为空；PG 安全配置未变更 |
| R7 | D-01：B1-2 无 roles FK（扫描 pg_constraint 与 migration 代码） | 0 条指向 roles 的 FK |

---

## 7. 本阶段是否实现测试代码

- **PREP 阶段：不实现**（仅规划）
- 若审计认为需"验证当前冻结设计本身"的最小验证，可增量实现 S1–S3 / I1 / M1–M2（不建表前提下的**文档级/只读**校验）—— 本轮未实现任何测试代码。
