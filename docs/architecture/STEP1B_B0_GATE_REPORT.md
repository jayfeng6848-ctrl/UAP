# STEP 1-B / B0 — GATE Report（Schema Implementation Readiness）

Status: **READY FOR HUMAN REVIEW**（待人工审计确认后方可进入 B1）
Phase: `STEP 1-B / B0` · 日期：2026-09-07
基线：`72ade9f` · `UAP-V0.1.0-INIT-DB-VALIDATED`
来源：STEP 1-A 冻结设计（Round 2 P1-01/02/03/04 + Round 3 P2-01/02/03，全量锁定）

> **B0 未创建任何表、未执行 Alembic、未执行 SQL DDL、未修改 Core/API/Domain 代码、未 commit、未 tag。**

---

## 1. 当前状态

```
STEP 0           = FROZEN
STEP 1-A         = APPROVED（第三次人工架构审计通过）
STEP 1-B / B0    = COMPLETE（本文档 = 门禁报告）
STEP 1-B / B1    = BLOCKED / READY FOR HUMAN REVIEW —— 待审计放行
```

## 2. 文档清单

### 新增（9 份，均在 `docs/architecture/`，全部未跟踪未提交）

| 文档 | 对应任务 | 行数 |
|---|---|---|
| `STEP1B_SCHEMA_DEPENDENCY.md` | T1 依赖图 / phase | — |
| `STEP1B_CONSTRAINT_MATRIX.md` | T3 约束矩阵 | — |
| `STEP1B_UUID_STRATEGY.md` | T4 UUIDv7 | — |
| `STEP1B_SEED_STRATEGY.md` | T5 Seed | — |
| `STEP1B_ACL_STRATEGY.md` | T6(9) ACL | — |
| `STEP1B_EVENT_OUTBOX.md` | T7(10) Outbox | — |
| `STEP1B_INDEX_STRATEGY.md` | T8(11) Index | — |
| `STEP1B_TRIGGER_INVENTORY.md` | T9(12) Trigger | — |
| `STEP1B_SCHEMA_TEST_MATRIX.md` | T12(15) Test | — |
| `STEP1B_B0_GATE_REPORT.md` | T14(17) 本文档 | — |

> 任务 13（一致性扫描）结果见 §13；任务 14（Migration 复核）结果见 §11。

## 3. Schema Dependency — **PASS**

- 29+1 表（`resource_relations` 为 P2 可选，B1 不建）；root：users / tenants / permissions / acl_subject_types / ai_providers / tools
- 循环 FK 1 个：`agents ↔ agent_versions`（current_version_id）→ deferred FK（agent_versions 建后补）
- 前向依赖 3 个：`agent_permissions→tools`、`agents→ai_routes`、`tool_executions→agents` → phase 调整（Tool→AI→Agent 顺序）消除
- 拓扑 phase：P00 primitives → P01 users → P02 identity 附属 → P03 tenant/space → P04 role/permission → P05 membership → P06 resource/ACL → P07 tool → P08 AI → P09 agent(+tool_executions+补 FK) → P10 event/audit → P11 triggers → P12 indexes → P13 seed
- 无 trigger 需在 seed 后建；全部 constraint 在 seed 前存在
- `groups` 表不存在于任何依赖（P2-02）

## 4. Constraints — **PASS**

PK（uuid/UUIDv7；分区 PK=(id,occurred_at)）· FK（P2-03 方向/行为逐表）· UQ（tenant/space/global/composite/partial 全列出）· CK（status/scope/risk/classification/时间/正值）· NOT NULL/NULL 逐表 —— 见 CONSTRAINT_MATRIX。ACL subject 验证链完整（§8）。

## 5. UUIDv7 — **PASS**

App 生成器 + DB `uap_uuid_v7()`（`set_byte` 实现）· DEFAULT=`uap_uuid_v7()` 仅兜底 · 25 项探针断言全过（Round 2 已实证）· PG18 内置未来切换路径明确 · 不引 pgcrypto。

## 6. Role / Seed — **PASS**

角色目录最终态（P2-01）：`platform_admin`(PLATFORM) / `tenant_admin`+`tenant_member`(TENANT 每租户) / `space_admin`+`space_member`(SPACE 每空间)。默认 role_id：tenant→`tenant_member`、space→`space_member`。错误场景（TM→PLATFORM/SPACE/异租户、M→TENANT/PLATFORM/异空间）全部触发 trigger 拒绝。seed 顺序 = acl→permissions→platform_admin→首租户→tenant 角色→TM→空间→space 角色→M→role_permissions（修正草案）。

## 7. ACL — **PASS**

`acl_subject_types` seed=user/role/agent（**无 group**）· `tg_acl_subject_exists` 三重存在性校验 · user 软删保留/硬删清理 · role 被引用禁删 · agent 归档 ACL 到期 · resource purge 级联（受控）· membership removed 不预清。group 仅未来路径（P2-02）。

## 8. Resource FK — **PASS**

`resources.tenant_id/space_id → RESTRICT`（P2-03 无 CASCADE 残留）· 删除流程 archive→soft→retention→controlled purge · CASCADE 白名单 §11.1（技术/关系/配置子实体 + 1:1 域扩展随受控 purge）。

## 9. Event Outbox — **PASS**

At-Least-Once（禁止 exactly-once 宣称）· 状态机 pending→claimed→delivered / claimed→pending / lease→Reaper→pending / attempts≥8→dead · CAS 原子 UPDATE（worker_id 条件）· SKIP LOCKED 仅性能 · 消费方 event_id 幂等 · 三个崩溃场景明确。

## 10. Index / Trigger — **PASS**

Index：按已知查询逐表列出（租户过滤/事件轮询/审计/session/device/ACL/幂等锚点），含 FK 反查强制清单 + 冗余反模式排查（低基数列/jsonb GIN 不建）+ P3 候选。Trigger：13 类 inventory（name/table/timing/event/purpose/failure/dependency），**无 trigger 引用未建表，无 groups 引用**，全部先于 seed。

## 11. Migration — **PASS（Alembic 最终使用方式复核）**

| 维度 | 决定 |
|---|---|
| migration version | Alembic revision 链（`0001_baseline` 作为 stamp 起点，见 MIGRATION_STRATEGY） |
| upgrade | 单事务（除非 `transaction_per_migration=false` 的 CONCURRENTLY 类）；P00–P13 分批 revision |
| downgrade | 每 revision 提供（B1 编写时逐 phase 反向 DROP） |
| checksum/integrity | alembic_version 表 + 文件校验；漂移由 autogenerate 对比 + CI 冒烟（upgrade head→downgrade base→upgrade head） |
| transaction | DDL 默认事务；`CREATE INDEX CONCURRENTLY` 显式非事务 + 独立脚本 |
| locking/concurrency | 迁移锁：`pg_advisory_lock` 全局锁（防双实例同时 upgrade）；并发迁移测试在矩阵 M5 |
| failure recovery | 失败自动回滚；重试前人工检查半成品 |
| destructive | DROP/重命名标注 `destructive=true`；生产需备份 + PITR 后执行 |
| data vs schema vs seed | schema migration（P01–P12）、data/seed migration（P13）分开 revision，可独立回滚 |

**问题评级（B0 提出，不修改架构）**：
- **P1**：迁移需要并发锁 —— alembic 默认无跨实例锁；必须在 env.py 注入 `pg_advisory_lock`（或运维约定单实例迁移）
- **P2**：downgrade 对分区表需先 drop 子分区（已写入 DEPENDENCY §9）；trigger 变更 downgrade 需逆序
- **P3**：seed 与 schema 同一 revision 会拖慢回滚 —— 已拆分（P13）

## 12. Security — **PASS**

租户级表全部含 tenant_id（可追溯）· space_id 用于 space-owned · owner 关系（user/device/session/resource/agent）逐项 · 无明文密钥列（credentials.hash/ai_providers.secret_ref，CI 扫描）· audit 覆盖 actor/tenant/space/resource/time/result · DB 角色最小权限（uap_app/uap_migrator/uap_readonly）· audit_logs/版本表不可变 trigger。

## 13. Test Matrix — **COMPLETE**

S(8)+U(7)+I(5)+T(12)+R(7)+E(8)+A(8)+M(8)+SEC(6) ≈ 69 项（`STEP1B_SCHEMA_TEST_MATRIX.md`），覆盖 Schema/Identity/Tenant/Space/ACL/Resource/Event/UUIDv7/Migration 全部要求类别。

## 14. Architecture Consistency Scan（任务 13）— **PASS**

对 docs/architecture 全部 md（含 9 份新文档）静态扫描，分类 Current/Future/Historical/Negative：
- `member` 默认角色残留：**0**（命中均为 tenant_member/space_member 默认表述、P2-01 消歧、历史记录）
- `group` 当前白名单：**0**（所有 group 引用均为未来启用路径语境）
- `resources.tenant_id/space_id` CASCADE：**0**
- 关系矩阵 tenants/spaces→resources CASCADE：**0**
- B0 新文档自检：9 份中 8 份零违规；1 处（ACL_STRATEGY §7）为未来路径代码注释（合法，标注"B1 不实现"）
- UUIDv7/lease/CAS/role_id/acl_subject_types 等扫描点一致

## 15. Remaining Risks（B0 遗留，供 B1/人工审计）

| 级别 | 风险 | 缓解 |
|---|---|---|
| **P0** | 无 | — |
| **P1** | Alembic 并发迁移需 advisory lock（见 §11） | env.py 注入 `pg_advisory_lock`；矩阵 M5 验证 |
| **P1** | 迁移中途失败需人工排查半成品 | 单事务 + CI 冒烟 + 备份先行 |
| **P2** | 自研 migration runner 与 Alembic 并存期（一个发布周期只读保留） | MIGRATION_STRATEGY 切换路径 |
| **P2** | 分区表 downgrade 顺序（子分区先 drop） | DEPENDENCY §9 已记录 |
| **P3** | 索引 P3 候选（低频后台扫描列）是否建 | 上线后 `pg_stat_user_indexes` 数据决策 |
| **P3** | RLS 是否启用（Q1） | B1 先建策略定义，不启用 RLS |
| **P3** | seed permissions 字典清单待人工定稿 | SEED_STRATEGY §4 已给形状 |

---

# GATE

| 门禁项 | 结果 |
|---|---|
| Architecture Consistency | ✅ PASS |
| Dependency Graph | ✅ PASS |
| Constraint Matrix | ✅ PASS |
| UUIDv7 Strategy | ✅ PASS |
| Role Seed Strategy | ✅ PASS |
| ACL Strategy | ✅ PASS |
| Resource Delete Strategy | ✅ PASS |
| Event Outbox Strategy | ✅ PASS |
| Index Strategy | ✅ PASS |
| Trigger Inventory | ✅ PASS |
| Migration Strategy | ✅ PASS |
| Security Review | ✅ PASS |
| Test Matrix | ✅ COMPLETE |

```
STEP 1-B / B0 = READY FOR HUMAN REVIEW
STEP 1-B / B1 = BLOCKED（等待人工审计放行）
```

**B0 已停止，未进入 B1。等待人工审计。**
