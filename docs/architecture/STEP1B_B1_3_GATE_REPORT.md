# STEP 1-B / B1-3 — GATE REPORT（Role & Permission Foundation PREP）

Status: **B1-3 HARDENING = READY FOR FINAL HUMAN AUDIT**（D-05…D-16 FROZEN + R5：Bootstrap Permanent Closure / User Lifecycle / Hard-delete 全 PROVEN；migration 0005/0006 已实施于 disposable DB）** · **正式 uap 库 untouched · 未 commit/tag · B1-4 BLOCKED**
日期：2026-09-08 · 基线 `72ade9f` · 当前 migration head = `0004_b1_2_tenant_space`（**未创建 0005、未改 0001–0004**）

> 本阶段**未创建任何表、未写 migration、未执行 DDL、未改 B1-1/B1-2 表、未实现授权代码、未 commit/tag**。

---

## 1. Frozen Design Verification
重读 `CORE_DOMAIN_MODEL.md` §1.2（roles/permissions/role_permissions）、`ER_MODEL.md` §2、B0 全套（CONSTRAINT_MATRIX / INDEX_STRATEGY / TRIGGER_INVENTORY / SCHEMA_DEPENDENCY / SEED_STRATEGY / UUID_STRATEGY）、B1-2 `DECISION_LOG.md`（D-01/D-02）、`STEP1B_B1_2_*` 系列，并核对 migration tree（0001→0002→0003→0004）。**文档间无冲突**；用户清单中若干字段（`roles.description`、`permissions.name/scope/status`）在冻结设计中不存在 → 已登记 OPEN，未新增。

## 2. Scope
仅 `roles` / `permissions` / `role_permissions`；并负责为 B1-2 的两个 `role_id` **补 FK + NOT NULL + scope trigger**。不含 Resource/ACL、Agent/Tool、AI、Event/Audit、Domain。

## 3. Role Design
`id(uuid/uap_uuid_v7())`、`tenant_id`(NULL→tenants CASCADE)、`space_id`(NULL→spaces CASCADE)、`key`、`name`、`scope`、`is_system`、`status`、`created_at/updated_at`、`archived_at`。**无 description（D-01 OPEN）**。
唯一性 = **scope-scoped 三条部分唯一索引**（platform / (tenant_id,key) / (space_id,key)），**非 global unique**（D-12 FROZEN）。

## 4. Permission Design
`id`、`key`(全局唯一)、`resource_type`(NULL)、`action`、`description`、`is_system`、`created_at`；**无 name/scope/status（D-02/D-03 OPEN）**；**无 updated_at**（字典表）；无 FK。

## 5. Role-Permission Design
`role_permissions` PK = **`(role_id, permission_id, effect)`**（冻结，非两列唯一）；FK 两侧 **CASCADE**；`effect CK('allow','deny')`；`conditions jsonb NULL`（仅存储位，求值在应用层）。

## 6. Role Scope
PLATFORM（tenant/space 均 NULL）/ TENANT（tenant_id 非空）/ SPACE（space_id 非空）；`tg_roles_scope_shape` 强制形状；`ck_roles_scope` 强制枚举。

## 7. Membership Scope Enforcement
**两层并存（D-11 FROZEN）**：DB trigger（`tg_tm_role_scope` / `tg_membership_role_scope`）负责**引用完整性**；Application Authorization Layer 负责**授权决策**（default deny、deny 优先）。不采用 Composite FK（TENANT/SPACE 归属列不同，无法统一）。

## 8. Tenant Isolation
TENANT role 带 `tenant_id`，`uq_roles_tenant (tenant_id, key)` 保证租户命名空间；`tg_tm_role_scope` 拒绝"Tenant A membership 绑定 Tenant B role"；SPACE role 带 `space_id`，配合已有 `tg_membership_tenant_consistency`。**自定义租户角色亦按 tenant_id 隔离**，不存在跨租户引用路径。

## 9. Default / System Roles
`platform_admin`(PLATFORM) · `tenant_admin`/`tenant_member`(TENANT，每租户) · `space_admin`/`space_member`(SPACE，每空间) —— **系统内置角色 + 数据库 seed（is_system=true，trigger 保护）**（D-10/R2-D-05 FROZEN）。`platform_admin` **绑定 = `platform_memberships`（R3-D-07 Option A，设计冻结、未建表待批准）**：PLATFORM role 唯一绑定载体；grant/revoke 仅 active platform_admin（首行 bootstrap）；last-admin 不可撤。不创建 platform_memberships（本轮）。

## 10. Constraints
见 `STEP1B_B1_3_CONSTRAINT_MATRIX.md`：PK/FK/ON DELETE/ON UPDATE/UNIQUE/CHECK/NOT NULL/DEFAULT/NULL 语义/Scope integrity/System role protection/Role-Permission integrity，**每项含目的·风险·测试方法**。

## 11. Indexes
8 个（4 部分唯一 + 1 复合 PK + 3 btree：`ix_rp_permission`、`ix_tm_role`、`ix_memberships_role`），每个写明 Query Pattern / Why / Cardinality；无低基数列索引、无 GIN、无"未来可能"索引（`STEP1B_B1_3_INDEX_STRATEGY.md`）。

## 12. Triggers
5 个：`tg_roles_set_updated_at`（复用 B1-1 函数，**不重建**）、`tg_roles_scope_shape`、`tg_roles_is_system_protect`、`tg_tm_role_scope`、`tg_membership_role_scope`。**只做数据库完整性**，禁止改权限/提权/复制 membership/建用户/写审计/调外部/业务副作用（`STEP1B_B1_3_TRIGGER_INVENTORY.md`）。

## 13. UUID
三表 PK 沿用 `uuid DEFAULT uap_uuid_v7()`；**不重建、不修改** B1-0 函数；**不使用 `gen_random_uuid()` 作为 PK 生成器**。

## 14. Seed
内置角色 = 系统角色（`is_system=true`）+ seed；**幂等**（重复执行不重复创建）；`platform_admin` 与平台权限字典属初始 seed，租户/空间级内置角色属**运行时 onboarding**（非 migration）。系统角色不可被普通租户操作删除（trigger）。

## 15. Delete Semantics
`role_permissions` 两侧 **CASCADE**（D-09 FROZEN）；membership 对 role **RESTRICT**（被引用角色不可删）；`permissions` 删除级联清理绑定（需审计）；Role 删除：被 membership 引用→拒绝，否则删除并级联其 role_permissions。

## 16. Test Matrix
`STEP1B_B1_3_SCHEMA_TEST_MATRIX.md`：Schema(11) + Role(10) + Permission(6) + Role-Permission(6) + Scope(10) + Isolation(4) + Seed(5) + Migration(8) + Regression(6) ≈ **66 项规划**；**本阶段未实现任何测试代码**。

## 17. Dependency Graph
无新循环 FK、无遗留前向依赖（B1-3 所有依赖表已存在）；B1-2 `role_id` 收敛路径：建表→seed→回填→trigger→SET NOT NULL→ADD FK→验证（`STEP1B_B1_3_SCHEMA_REVIEW.md` §1–2）。

## 18. Architecture Guard
`pytest tests/architecture` → **9 passed**，Core→Domain **0 violations**；roles/permissions 保持平台级抽象，无 domain 业务值。

## 19. Scope Scan
- migration 已建表集合 = 9（5 Identity + 4 Tenant/Space）；**B1-3 三表未创建** ✅；后续阶段表（resources/agents/tools/ai_*/events/audit/groups/domain）**均未创建** ✅
- `roles → family/company/restaurant/entertainment`：**0** ✅
- B1-1 / B1-2 / B1-3 文档在字段、FK、Scope、Delete、Index、Trigger 上**无冲突**

## 20. DB Status
正式 `uap` 库 **0 张表（untouched）**；测试仅用 disposable `uap_b1_test`；pytest **102 passed**（B1-0 12 + B1-1 19 + B1-2 18 等）。

## 21. Git Status
commit `72ade9f` 未变；已跟踪改动仅 `pyproject.toml`+`requirements.txt`（B1-0 的 alembic，2 行）；untracked 42 项（含 B1-3 新增 6 份文档）；**未 commit / 未 tag**。

## 22. Decision Log
`STEP1B_B1_3_DECISION_LOG.md`：D-01…D-16。
**RESOLUTION R4/R5 后状态**：D-05…D-16 → **全部 FROZEN**；D-07 = Option A `platform_memberships` + R4 PMB-1..4 CLOSED；**R5 HARDENING**：bootstrap 判据由"PM count=0"改为显式 `platform_state` 单向状态机（0006），User lifecycle 三分层契约定稿 → 四项 PROVEN（见 Gate）。
**R3 文档修正**：`uq_roles_platform` 唯一谓词补齐 `AND space_id IS NULL`（6 份文档）；reserved-key 表述扫描 = 0（无全局保留字约束，scope-scoped 唯一性即边界）。
**剩余 OPEN（不阻塞 0005）**：D-01 `roles.description` · D-02 `permissions.name/status`（均"默认不加列"，仅当审计要求时增列）。

## 23. Remaining Risks
| 级别 | 风险 |
|---|---|
| **P1→已冻结（待实施批准）** | D-07 载体选定 = **新增 `platform_memberships`（Option A）** + **R4 Hardening 全 CLOSED**：PMB-1（role 侧 `tg_roles_pm_lifecycle` 纵深防线 + effective 谓词 ≥1）、PMB-2（bootstrap 一次性、行数=0 可判定）、PMB-3（re-grant = UPDATE 本行）、PMB-4（停用先 revoke、CASCADE 仅 purge）。实施 = 新表 + 3 trigger（T6/T7/T8），置于 roles 之后（0005 尾或独立 revision）；**未经人工批准不得建表/写 migration** |
| **P1→已冻结** | D-08 回填（先 seed → 回填 → 校验 → SET NOT NULL → ADD FK；失败即 ROLLBACK）→ 已解，实施时顺序不可变 |
| **P2** | R-D-14：allow/deny 并存 → 授权层必须"deny 绝对优先"（未实现求值器前不得上线授权决策） |
| **P2** | R-D-15：scope-neutral 语义需授权层遵守 + 测试（不能只在注释） |
| **P2** | R-D-16：租户传递隔离依赖两 trigger 合取 → 需专门测试用例 |
| **P2** | Legacy(schema_migrations) → Alembic Cutover 未执行（生产门控；不 stamp） |
| **P3** | trigger RAISE 抛 ProgrammingError（测试断言兼容）；`ix_rp_permission` 是否建 |

## 24. Gate

| 项 | 结果 |
|---|---|
| Frozen design reread | ✅ |
| Role / Permission / Role-Permission schema defined | ✅ |
| Role Scope / Membership Role Scope frozen | ✅（D-11/D-12） |
| role_id FK strategy frozen | ✅（D-08） |
| Tenant isolation frozen | ✅ |
| Default/System roles frozen | ✅（D-10；**绑定 = D-07 FINAL（Option A + R4 PMB-1..4），设计层 APPROVED**） |
| System role semantics | ✅（R-D-05 保护 + 修改通道 = 新 migration revision） |
| D-05…D-16 Resolution | ✅ 全部 FROZEN（D-07 = FINAL APPROVED 设计层；D-01/D-02 保持 OPEN 但不阻塞 0005） |
| Last Admin × Role Lifecycle | ✅ CLOSED（PMB-1：effective ≥1，`tg_pm_last_admin` + `tg_roles_pm_lifecycle`） |
| Bootstrap Trust Root | ✅ CLOSED（R5-1：`platform_state` 单向状态机 + `tg_pm_bootstrap_gate`；R4 count 判据作废/次级前置） |
| Re-grant lifecycle | ✅ CLOSED（PMB-3：UPDATE 本行、禁 INSERT、duplicate 拒） |
| User lifecycle | ✅ CLOSED（PMB-4 + R5-2 三分层：DB 无自动 revoke / Service revoke-first 单事务 / Authorization inactive→DENY） |
| Role Scope / 唯一谓词 / Reserved Key | ✅ CLOSED（三态互斥谓词终版；无全局保留字） |
| Delete semantics frozen | ✅（D-09） |
| Constraint / Index / Trigger / Test / Dependency 文档 | ✅ |
| UUID / Seed aligned | ✅ |
| Architecture Guard | ✅ 9 passed |
| Scope Scan | ✅ |
| No B1-1/B1-2/0001–0004 修改 / No Domain 变更 | ✅ |
| No commit / No tag | ✅ |
| Bootstrap permanently closed | ✅ PROVEN（B-01..B-06，platform_state 单向） |
| User reactivation cannot restore revoked PM | ✅ PROVEN（U-02） |
| Last-admin protection under hard delete | ✅ PROVEN（U-06/B-05，级联 DELETE 亦拦） |
| No legacy platform_metadata dependency | ✅ PROVEN（schema 无该表；B-06） |

```
B1-3 HARDENING          = READY FOR FINAL HUMAN AUDIT
B1-3 IMPLEMENTATION     = COMPLETE（0005/0006 于 disposable 库；正式 uap 库 0 表 untouched）
B1-4                    = BLOCKED
```

**已停止。未自行 commit/tag，未进入 B1-4。migration 0005/0006 仅运行于 disposable 测试库；正式 `uap` 库未执行任何迁移。等待最终人工审计。**
