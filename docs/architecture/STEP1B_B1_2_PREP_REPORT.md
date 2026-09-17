# STEP 1-B / B1-2 — PREP REPORT（Tenant & Space Foundation, PREP ONLY）

Status: **B1-2 PREP = COMPLETE** · **B1-2 IMPLEMENTATION = BLOCKED（等待人工架构审计）**
日期：2026-09-08 · 基线：`72ade9f` · 当前 migration head = `0003_b1_1_root_identity`

> **本阶段未创建任何表、未写 migration、未执行 DDL、未改 Core/API/Frontend/Domain、未 commit/tag。**
> B1-1 五张 Identity 表（`users`/`identities`/`credentials`/`devices`/`sessions`）**保持不变**。

---

## 1. Task List

| # | 任务 | Status |
|---|---|---|
| 1 | 重读冻结架构文档（STEP1A + B0 全套 + B1-1 实现） | ✅ |
| 2 | `STEP1B_B1_2_SCHEMA_REVIEW.md`（4 表逐字段核对） | ✅ |
| 3 | `STEP1B_B1_2_CONSTRAINT_MATRIX.md` | ✅ |
| 4 | `STEP1B_B1_2_DEPENDENCY.md`（含 roles=FUTURE、循环检查） | ✅ |
| 5 | `STEP1B_B1_2_INDEX_STRATEGY.md`（7 索引，逐个 Query Pattern） | ✅ |
| 6 | `STEP1B_B1_2_TRIGGER_STRATEGY.md`（4 updated_at + 1 一致性） | ✅ |
| 7 | `STEP1B_B1_2_TEST_MATRIX.md`（本阶段只规划） | ✅ |
| 8 | 全文档一致性扫描（scope 冲突） | ✅（见 §12） |
| 9 | B1-2 PREP Gate 报告 | ✅（本文档） |

## 2. Frozen Schema Review

- `tenants`：root 表，slug 全局唯一（lower 表达式），status/slug 正则 CK，软删 archived_at+deleted_at，无 FK
- `spaces`：`tenant_id NOT NULL → tenants RESTRICT`（唯一归属），`(tenant_id, lower(key))` 部分唯一，kind 仅约束格式（**不枚举业务值**），owner_id 可空（SET NULL）
- `tenant_memberships`：`(tenant_id, user_id)` 唯一（含历史行），tenant/user CASCADE，role_id → **FUTURE**
- `memberships`：`(space_id, user_id)` 部分唯一（排除 removed），冗余 `tenant_id`（trigger 保证一致），space/user CASCADE，role_id → **FUTURE**
- 与 B1-1 衔接：4 处引用 `users.id`（spaces.owner_id、tm.user_id/invited_by/role_assigned_by、memberships.user_id/invited_by）

## 3. Dependency Graph

```
users(B1-1) ──┬──> tenant_memberships ──> tenants(FUTURE role)
              ├──> memberships ──> spaces ──> tenants(RESTRICT)
              └──> spaces.owner_id
roles = FUTURE DEPENDENCY（不创建）
```
- **无新循环 FK**（6 项检查全清）
- 创建顺序：tenants → spaces → tenant_memberships → memberships；downgrade 反向
- 与 B0 Phase：P03 + P05（P04 roles 延后）

## 4. Constraint Matrix

见 `STEP1B_B1_2_CONSTRAINT_MATRIX.md`：PK(uuid/UUIDv7 兜底) / FK(RESTRICT vs 关系行 CASCADE) / UQ(4，含 2 部分唯一) / CK(7) / NOT NULL / DEFAULT / ON DELETE / ON UPDATE(NO ACTION) / 软删 / 隔离 —— 全部对齐 B0 矩阵。
PROPOSED（不实施）：`ix_tenants_status`、owner ON DELETE 明确化、settings 密钥扫描。

## 5. Index Strategy

7 个（4 UNIQUE + 3 btree），每个给出 **Query Pattern → Why Needed → Expected Cardinality → Why Existing Index Cannot Serve It**：
`uq_tenants_slug` / `uq_spaces_key` / `uq_tenant_memberships` / `uq_memberships` / `ix_spaces_tenant_status` / `ix_tm_user` / `ix_memberships_tenant_user`。
FUTURE（随 roles）：`ix_tm_role`、`ix_memberships_role`。无低基数列索引、无 jsonb GIN。

## 6. Trigger Strategy

- 本阶段：4× `tg_<table>_set_updated_at`（复用 B1-1 的 `set_updated_at()`，不重建）+ `tg_membership_tenant_consistency`（**冻结设计已定义**的跨表校验，只校验不写副作用）
- FUTURE（依赖 roles）：`tg_tm_role_scope`、`tg_membership_role_scope`
- **不新增跨表业务 trigger**（租户删除级联、成员清理、audit 写入均在应用层/purge job）——已逐项列出"为何不建"

## 7. UUID Strategy

所有新 PK = `uuid NOT NULL DEFAULT uap_uuid_v7()`。
- **不重新实现**、**不修改** B1-0 的 `uap_uuid_v7()`
- 应用层 UUIDv7 为主，DB DEFAULT 仅兜底
- 不引入第二套生成方案；不引 pgcrypto

## 8. Seed Strategy

- **本阶段不 seed `roles` / `permissions`**（FUTURE；未经人工批准不得提前）
- `tenants` / `spaces` 实例数据由 **onboarding 运行时流程**创建，不属于 migration seed
- 测试 seed 只允许写入 disposable 库（`uap_b1_test` 等）；**正式 `uap` 库不得被 seed 或测试污染**
- 未来 seed 顺序（SEED_STRATEGY）：acl_subject_types → permissions → platform_admin → 租户 → tenant 角色 → TM → 空间 → space 角色 → M → role_permissions

## 9. Test Matrix

见 `STEP1B_B1_2_TEST_MATRIX.md`：Schema(11) + Isolation(8) + Membership(10) + Scope(8) + Migration(8) + Regression(5) ≈ **50 项规划**。
**本阶段不实现测试代码**（未新增/修改任何测试文件）。

## 10. Security / Isolation Review

| 保证 | 机制 |
|---|---|
| Space 必须属唯一 Tenant | `spaces.tenant_id NOT NULL` + FK |
| 无无主 Space / 无多租户 Space | 单列 tenant_id，无关联表 |
| memberships 冗余 tenant_id 不漂移 | `tg_membership_tenant_consistency` |
| 跨租户访问默认 DENY | 授权 Pipeline [2]+[3] 必须命中 membership；越权写 audit（CRITICAL）；可选 RLS（Q1） |
| 跨空间访问 | 必须命中 `memberships(space_id)` |
| Scope 分离 | TM 只表达租户成员（携带 TENANT role）；M 只表达空间成员（携带 SPACE role）；权限只向下继承，**成员关系不复制**；Space membership 不自动获 Tenant admin；禁止绕过 membership 的 user→space / user→tenant 直连 |
| 删除策略 | 业务实体（tenant↔space）RESTRICT；关系行（membership）CASCADE（白名单），真实清理走 archive→soft delete→retention→**controlled purge** |

## 11. Legacy → Alembic Risk（仅记录，不执行 Cutover）

旧账本 `schema_migrations`（自研 runner）→ 新 `alembic_version`。生产切换**不得直接 `alembic upgrade head`**，必须：

```
1. legacy migration history verification   （确认 schema_migrations 已应用版本与真实 schema 一致）
2. schema verification                    （对比期望对象集合，确认无漂移/无业务表）
3. alembic stamp 0001_baseline            （对齐历史锚点，不执行 DDL）
4. upgrade 0002+                          （仅应用新版本）
5. verification                           （对象/约束/索引/版本复核 + 冒烟）
```
附加要求：切换前备份（PITR + snapshot）、单 runner（advisory lock）、失败即回滚；旧 runner 一个发布周期内只读保留。
**本阶段不执行 Production Cutover。**

## 12. Full Consistency Scan

工具：对 `docs/architecture/*.md` + `migrations_alembic/**/*.py` 静态扫描，区分 Current / Future / Historical / Negative。

| 检查 | 结果 |
|---|---|
| migration 代码中创建 roles/permissions/tenants/spaces/memberships 表 | **0**（未创建任何业务表）✅ |
| User→Space 绕过 membership | **0** ✅ |
| "TM 直接授予 space 权限" | 4 处命中 → 人工判定均为**并列提及/DROP 顺序**表述，非权限授予 → 误报 |
| "Space membership 自动拥有 tenant admin" | 6 处命中 → 均为 "TM 携带 Tenant Role" 的正确描述 → 误报 |
| "tenants/spaces 被 CASCADE 删除" | 2 处命中 → 均为 B0 白名单的**关系行/配置行**（`memberships.tenant_id`、`roles.tenant_id/space_id`），**非**业务实体间级联 → 合理解释 |
| domain 词汇（family/company/…） | 22 处 → 均在 `ARCHITECTURE.md`（STEP 0 domains 占位说明）与文档语境，**未进入 Core schema** |
| 文档字段一致性 / Schema↔Matrix / Dependency↔顺序 / Index / Trigger / UUID / Seed / Test / Guard | **一致**（B1-2 六份文档交叉引用同一冻结来源） |
| B1-1 兼容性 | 新表仅引用 `users.id`；B1-1 五表结构与约束不变（回归 84 passed 含 B1-1 19 项） |

## 13. Architecture Guard Status

`pytest tests/architecture` → **9 passed**；无 Core→Domain、Identity/Tenant→Domain 违规；Tenant/Space 保持平台级抽象（kind 不枚举业务值）。

## 14. Formal DB Status

正式 `uap` 库：**0 张表（untouched）**；所有测试仅使用 disposable `uap_b1_test`。

## 15. Git Status

- commit：`72ade9f`（未变）；tag：`UAP-V0.1.0-INIT`、`UAP-V0.1.0-INIT-DB-VALIDATED`（未新增）
- 已跟踪改动：`pyproject.toml`、`requirements.txt`（仅 B1-0 的 `alembic==1.19.2`）
- untracked：33 项（B1-2 新增 6 份文档 + B1-1/B1-0 产物）
- **未 commit / 未 tag**

## 16. Remaining Risks

### 更新（2026-09-08 Decision Resolution）— 见 `STEP1B_B1_2_DECISION_LOG.md`

| 级别 | 风险 | 缓解/待决 |
|---|---|---|
| ~~P1~~ → **RESOLVED (D-01)** | `role_id` Forward Dependency | **已冻结**：B1-2 保留列、**不建 FK**（NULL 允许）；B1-3 回填→`SET NOT NULL`→`ADD FK`。**明确非 DEFERRABLE FK** |
| ~~P1~~ → **RESOLVED (D-02)** | Role Scope 窗口期 | **已冻结**：B1-2 应用层 **fail-closed**（拒绝不存在/scope 不匹配 role）；B1-3 DB trigger + 5 项验收 |
| **P2** | `spaces.owner_id` ON DELETE（**D-03**） | **PROPOSED — HUMAN APPROVAL REQUIRED**：建议 SET NULL；未批准前不实现；禁止 CASCADE |
| **P3** | RLS（**D-04**） | **OPEN DESIGN QUESTION**：不启用/不创建 policy/不改 PG 配置 |
| **P2** | 冗余 `tenant_id` 依赖 trigger 维护（trigger 失败即拒绝写入） | 一致性 trigger 已规划；性能 P3 |
| **P2** | Legacy(schema_migrations) → Alembic Cutover 未执行 | §11 流程已记录；生产切换前需单独审计 |

---

# GATE

| 门禁项 | 结果 |
|---|---|
| Task List | ✅ PASS |
| Frozen Schema Review | ✅ PASS |
| Dependency Graph（无新循环、roles=B1-3 FUTURE，非 DEFERRABLE） | ✅ PASS |
| Constraint Matrix | ✅ PASS |
| Index Strategy（7，逐项论证） | ✅ PASS |
| Trigger Strategy（无新跨表业务 trigger；B1-2 应用层 fail-closed） | ✅ PASS |
| UUID Strategy（复用 uap_uuid_v7） | ✅ PASS |
| Seed Strategy（不提前 seed roles） | ✅ PASS |
| Test Matrix（≈50 项规划 + B1-2/B1-3 分阶段 scope 项，不实现） | ✅ COMPLETE |
| Security / Isolation Review | ✅ PASS |
| Legacy→Alembic Risk 记录 | ✅ RECORDED |
| Full Consistency Scan | ✅ PASS（6 类禁止错误描述 0 命中） |
| Architecture Guard | ✅ PASS（9 passed） |
| Formal DB Untouched | ✅ PASS（0 表） |
| No New Table / Migration / Code Change | ✅ PASS |
| **Decision Resolution（D-01/D-02 冻结，D-03/D-04 登记）** | ✅ PASS |

```
B1-2 PREP           = COMPLETE
B1-2 IMPLEMENTATION = BLOCKED（等待人工架构审计）
B1-3                = BLOCKED
```

**已停止。未创建 tenants/spaces/memberships/roles/permissions 任何表，未写 migration，未进入 B1-3。**
