# B1-4 — Migration Plan（PREP ONLY — 不创建 migration、不执行 DDL）

Status: **DESIGN — 本阶段仅规划**
基线：head = `0006_b1_3_bootstrap_state`（live 已验证）

---

## 1. Revision 定义

```text
current head            = 0006_b1_3_bootstrap_state
B1-4 target revision    = 0007_b1_4_resource_acl
down_revision           = 0006_b1_3_bootstrap_state
```

| 项 | 规则 |
|---|---|
| 文件 | `migrations_alembic/versions/0007_b1_4_resource_acl.py`（**本阶段不创建**） |
| 修改 0001–0006 | **禁止** |
| 单事务 | 整个 revision 在一个事务内（沿用 B1-0 契约） |
| 并发锁 | 复用 `env.py` 的 `pg_advisory_xact_lock`（key `(5_587_280,1)`），**不修改 env.py** |
| seed 与 schema | **B1-4 无 seed**（P00–P10 无 seed 需求；`acl_subject_types` 三行属 P13）。因此**不存在**"同 revision 混 schema 与 seed"的情形；**不引入 permissions 字典** |

---

## 2. Upgrade 顺序（按真实 FK 依赖）

```
BEGIN
 [1] resources                     （依赖 tenants/spaces/users，均已存在）
 [2] acl_subject_types             （ROOT，零 FK）
 [3] resource_permissions          （依赖 resources + acl_subject_types）
 [4] trigger（**3 个** —— R4 更新：D-B14-10 = A-1 / D-B14-12 = A 均已 FROZEN）
       · tg_resources_set_updated_at          ← 复用 set_updated_at()（0003，函数已存在）
       · tg_resources_tenant_space_consistency ← D-B14-10 = A-1（F2；structural integrity only）
       · tg_acl_subject_types_protect          ← D-B14-12 = A（C2；registry governance only）
       · G/H/I/J 全部不实施（冻结"最早 P09 后"，D-B14-02）
 [4b] 说明：本 revision 不写 `acl_subject_types` 行（**B1-4 零 seed**）。
      `user`/`role`/`agent` 三行属 **P13**，其受控写入路径见 `B1-4_DESIGN.md` §8.1（**W-3 决议**）。
 [5] indexes（部分唯一索引建表内联；查询索引显式创建）
COMMIT  → 无回填、无 seed（B1-4 = P06，seed 属 P13）
```

> **R1 更正**：上一轮把"seed acl_subject_types"列入 upgrade 步骤，**已移除** —— 依据 `STEP1B_SCHEMA_DEPENDENCY.md:193`（P00–P10 无 seed 需求；P13 才有 seed）。B1-4 **零 seed**。

### 约束/索引明细

| 阶段 | 对象 |
|---|---|
| 建表内联 | PK ×3 · FK ×6（resources 3 + rp 3）· UQ ×1（`uq_resource_perm`）· **CK ×6** · NN/DEFAULT |

> **R4 计数更正（2026-09-13 报告 / 2026-09-14 更正）**：上一版本行写 `CK ×5`，与冻结 Schema 的逐项枚举不符。
> canonical source = `B1-4_SCHEMA_DESIGN.md` §2.2/§3.2/§4.2 的**逐名枚举**，共 **6** 个 CHECK：
> `ck_resources_type` · `ck_resources_classification` · `ck_resources_status` ·
> `ck_acl_subject_types_key` · `ck_acl_subject_types_whitelist` · `ck_resource_permissions_effect`。
> 交叉印证：`B1-4_TEST_MATRIX.md` C1/C2/C3/C8/C9/C10 = 6 条 CK 测试；实现实测 = 6。
> **本更正只修正数量摘要，不改变任何 CHECK 的实际定义。**
| 表达式/部分索引 | `uq_resources_natural`（部分）· `uq_acl_subject_types_key`（部分，`lower(key)`） |
| 查询索引 | `ix_res_tenant_space_type_status` · `ix_res_tenant_owner` · `ix_res_tenant_type_created` · `ix_res_tenant_deleted`（部分）· `ix_rp_subject` |

**无数据回填**：B1-4 不修改任何既有表、不改既有行 → 与 B1-3 的 D-08 回填性质不同（无 fail-closed 回填门禁需求）。
> **ACL trigger 不提前**（D-B14-02 已按冻结原文裁定：最早可挂 = P09 后）。仅当人工**另行批准修订冻结相位文档**时才会考虑提前；彼时因 `resource_permissions` 在 B1-4 前不存在，**无既有数据可核对**，故不构成回填。

---

## 3. Downgrade（严格反向）

```
BEGIN
 [1] DROP TRIGGERS（逆序，共 3 个）：
        · tg_acl_subject_types_protect          （D-B14-12 = A）
        · tg_resources_tenant_space_consistency （D-B14-10 = A-1）
        · tg_resources_set_updated_at
 [2] DROP 相关 FUNCTION（仅 B1-4 新建的 enforce_*；**不 DROP set_updated_at / uap_uuid_v7**）
 [3] DROP TABLE resource_permissions → acl_subject_types → resources
 [4] 不触碰 B1-3 及更早对象
COMMIT
```

| 规则 | 说明 |
|---|---|
| 不破坏历史语义 | downgrade 仅移除 B1-4 对象；B1-0~B1-3 的 15 表 / trigger / function 保持 |
| 不 DROP DATABASE / 不用 CASCADE DROP | 显式顺序删除 |
| 数据丢失 | 三表为 B1-4 新建且无外部依赖 → downgrade 丢弃其数据属预期（生产环境须先备份） |

---

## 4. 失败与恢复

| 场景 | 期望 | 验证方式 |
|---|---|---|
| revision 中途失败 | 单事务整体回滚（含建表、trigger、索引），`alembic_version` 不前进 | 临时坏 revision 探针（复刻 `test_migration_failure.py` 既有模式） |
| 锁释放 | 失败后 advisory lock 无残留，后续 runner 立即可用 | `pg_locks` 断言 |
| 半成品状态 | 不得存在"表已建但 trigger 未挂"的中间态 | schema 断言 |
| 重跑 | `upgrade head` 幂等 | smoke |

---

## 5. 并发与生产策略

| 项 | 策略 |
|---|---|
| 并发迁移 | `pg_advisory_xact_lock` 串行化；`fail` 模式第二 runner 立即拒绝（CI/测试），`wait` 模式生产默认 |
| 生产迁移 | **本阶段不执行**；生产 cutover 属独立门禁（Legacy `schema_migrations` → alembic 验证流程，B1-2 已记录） |
| 备份 | 任何生产 DDL 前必须备份（MIGRATION_CONTRACT §12） |
| destructive | 0007 **非 destructive**（仅新增对象）；downgrade 属 destructive（丢三表数据）→ 需审批 |
| 迁移用户 | 生产使用专用 `uap_migrator`（DDL 权限），运行时不具备 DDL |

---

## 6. 上线前置检查清单（实施阶段用）

| # | 检查 | 期望 |
|---|---|---|
| 1 | `alembic heads` 唯一 = `0006_b1_3_bootstrap_state` | 单头 |
| 2 | 正式 `uap` 库表数 = 0（untouched 基线） | 0 |
| 3 | disposable 库可 reset / upgrade / downgrade / re-upgrade | 全通过 |
| 4 | 0001–0006 内容未变（mtime + 内容复核） | 未变 |
| 5 | `git diff` 无已跟踪代码改动、未 commit/tag | 干净 |
| 6 | D-B14-01 / D-B14-02 已获人工裁定 | **BLOCKING** |

---

## 7. 与 MIGRATION_IMPLEMENTATION_CONTRACT 的一致性

| 契约条款 | B1-4 遵守 |
|---|---|
| 唯一入口 / advisory lock / 事务策略 | ✅ 复用 env.py，不改动 |
| 版本追踪 / 校验 | ✅ `0007`，单头链 |
| downgrade 必须实现 | ✅ 反向删除 |
| 禁止同 revision 混 schema 与业务 seed | ✅ B1-4 无 seed（P13 才有 seed），天然合规 |
| destructive 标注 | downgrade 属 destructive → 实施时在文件头标注并说明 |
| 生产策略 | ✅ 本阶段不执行生产迁移 |

> **已知 P3（不属 B1-4 scope）**：`alembic.ini` 默认 URL 指向正式 `uap` 库，`env.py` 无环境级 opt-in 拒绝 → 裸 `alembic upgrade head` 可对正式库执行 DDL（B1-3 审计 P3-3）。B1-4 计划在实施前**再次记录**，是否纳入见 GATE §4（默认 defer，不隐式扩范围）。
