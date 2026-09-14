# B1-4 — Test Matrix · **Revision R4**

Status: **PREP R4 — 设计层测试矩阵，未编写任何测试代码**

冻结事实（R4）：B1-4 = **P06 Resource / ACL** · **B1-4 不 seed `acl_subject_types`** · 三个 Subject Type seed 属 **P13** · **G/H/I/J 最早 P09 后** · **B1-4 不实现 G/H/I/J** · **B1-4 不实现 Authorization Evaluation** · **DENY > ALLOW 属 Authorization Layer** · **`conditions` = storage-only** · **不启用 RLS** · **不创建 Domain / Tool / AI / Agent / Event / Audit 表**

**R4 Human Decision 冻结（2026-09-13）**：**`D-B14-08 = FROZEN — A`**（action 零新增 semantic/format contract）· **`D-B14-09 = FROZEN — A`**（`granted_by ON DELETE SET NULL`）· **`D-B14-10 = FROZEN — A-1`** · **`D-B14-12 = FROZEN — A`**（platform-controlled registry + protection mechanism）· **`O-1 = FROZEN — A`**（canonical total = **84**）· **`O-2 = FROZEN`**（双字段状态模型）

---

## 状态模型（O-2 = FROZEN，2026-09-13）

每个测试项**只能有一个** `Current Status`。

| 字段 | 规则 |
|---|---|
| `Current Status` | 取值 ∈ {`【B1-4】`,`【后续】`,`【待裁定】`}；**禁止**在同一字段内出现两个 `【…】` |
| `Post-Approval Level` | **仅当**存在"批准后归属阶段"且**当前尚未批准**时填写；已批准或无需批准时填 `—` |

三类合法组合：

| 情形 | Current Status | Post-Approval Level |
|---|---|---|
| 本阶段可执行 | `【B1-4】` | `—` |
| 决策尚未裁定 | `【待裁定】` | `【B1-4】` / `【后续】` |
| 决策已批准但受阶段约束 | `【后续】` | `—` |

> **R4 现状：不存在任何 `【待裁定】` 项** —— `D-B14-08` / `D-B14-09` / `D-B14-12` 均已 FROZEN，`O-1` / `O-2` 已 FROZEN。

---

## 0. 计数口径与 Canonical Total（O-1 = A FROZEN）

### 0.1 表数口径（全文一致）

```text
14 existing business tables   （users, identities, credentials, devices, sessions,
                               tenants, spaces, tenant_memberships, memberships,
                               roles, permissions, role_permissions,
                               platform_memberships, platform_state）
+ 3 B1-4 business tables      （resources, acl_subject_types, resource_permissions）
= 17 business tables
+ alembic_version
= 18 physical tables
```

**依据**：migration `create_table` 实测 = 14（`0003:5 + 0004:4 + 0005:4 + 0006:1`）；B1-4 目标 revision = `0007_b1_4_resource_acl`（新增 3）。

### 0.2 Canonical Test Total = **84**（唯一口径）

> **Canonical Total 定义**：**正式 TEST_MATRIX 表格中的测试行数量**。

```text
71（基础七类正式表格行）
+ 13（§8 decision-dependent 正式表格行）
= 84
```

| 段落 | 行数 |
|---|---|
| §1 Schema | 11 |
| §2 FK / Delete | 7 |
| §3 Constraint / Idempotency | 10 |
| §4 ACL Subject（4.1:5 + 4.2:11） | 16 |
| §5 Isolation（I1–I5:5 + R-ISOLATION-01…05:5） | 10 |
| §6 Migration | 10 |
| §7 Security / Architecture | 7 |
| **基础七类小计** | **71** |
| §8.1 ACT-01/02 | 2 |
| §8.2 GB-00/01/02 | 3 |
| §8.3 TC-00…TC-04 | 5 |
| §8.4 REG-01…03 | 3 |
| **§8 小计** | **13** |
| **Canonical Total** | **84** |

- **`ACT-03` = 条件项（`conditional / non-canonical`）**：`D-B14-08 = A`（**零新增 semantic/format contract**）⇒ **条件未成立**，**不登记为表格行、不计入 84**。除未来被正式提升为表格行外，**不得**计入。
- **§10 登记项 `D1–D7`（7 行）不属于 canonical count**。
- 全文**不得**把 `85` 表述为 canonical total。

---

## 1. Schema Tests

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| S1 | 精确表数：B1-4 后 = **17 business tables + alembic_version = 18 physical tables**（与 §0.1 口径逐字一致） | 集合相等 | 【B1-4】 | — |
| S2 | 无 `resource_relations` / 无 Domain 表 / 无 Tool·AI·Agent·Event·Audit 表 | 断言不存在 | 【B1-4】 | — |
| S3 | `resources` PK/FK/CK/NN/DEFAULT 与 `STEP1B_CONSTRAINT_MATRIX.md` §3 逐项一致 | schema inspection | 【B1-4】 | — |
| S4 | `acl_subject_types` 部分 UQ（含 `archived_at IS NULL`）+ CK 白名单 `('user','role','agent')` + 格式 CK | 断言 | 【B1-4】 | — |
| S5 | `resource_permissions` UQ `(resource_id, subject_type_id, subject_id, action)` + `effect` CK | 断言 | 【B1-4】 | — |
| S6 | 8 个索引存在且定义正确（含 2 个部分索引） | `pg_indexes` 断言 | 【B1-4】 | — |
| S7 | `resources.updated_at` 由 `tg_resources_set_updated_at` 自动维护；**复用** `set_updated_at()`（不重建函数） | UPDATE 后时间推进 + 函数唯一 | 【B1-4】 | — |
| S8 | `acl_subject_types` / `resource_permissions` **无** `updated_at` 列、**无** `tg_*_set_updated_at`（`acl_subject_types` 的 protect trigger 属 **C2** 家族，见 S11） | 断言 | 【B1-4】 | — |
| S9 | `acl_subject_types` 行数 = **0**（B1-4 不 seed） | 0 | 【B1-4】 | — |
| S10 | `resource_permissions` 行数 = **0**（不可写入，见 §4.1） | 0 | 【B1-4】 | — |
| S11 | B1-4 新增 **3 个** trigger：`tg_resources_set_updated_at` + `tg_resources_tenant_space_consistency`（**D-B14-10 = A-1 FROZEN**）+ `tg_acl_subject_types_protect`（**D-B14-12 = A FROZEN**）；**不含** G/H/I/J | trigger 集合断言 | 【B1-4】 | — |

## 2. FK / Delete Tests

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| F1 | 删除有资源的 `tenants` → **RESTRICT 拒绝** | FK violation | 【B1-4】 | — |
| F2 | 删除有资源的 `spaces` → **RESTRICT 拒绝** | FK violation | 【B1-4】 | — |
| F3 | **`resources.owner_id`：**硬删 owner（user）→ **资源保留，`owner_id = NULL`**（SET NULL，**已冻结**） | SET NULL | 【B1-4】 | — |
| F4 | 删除 `resources` 行 → 其 `resource_permissions` 级联清理 | 行数归零 | 【后续】（需先有 ACL 行，P13 后） | — |
| F5 | 删除被 ACL 引用的 `acl_subject_types` 行 → **RESTRICT 拒绝** | FK violation | 【后续】（需先有 ACL 行） | — |
| F6 | 软删资源 → ACL **保留**（不级联） | 行数不变 | 【后续】 | — |
| F7 | 静态扫描：migration 中 CASCADE **仅** `resource_permissions.resource_id` 一处（受控 purge 白名单）；无其它未批准 CASCADE | 扫描 0 违例 | 【B1-4】 | — |

> **F3 与 GB-01 是两条独立测试，禁止合并**：`owner_id` 的 SET NULL = **所有权**语义（已冻结）；`granted_by` 的 SET NULL = **actor attribution** 语义（`D-B14-09 = A` 已冻结）—— 二者**对象不同、语义正交**。

## 3. Constraint / Idempotency Tests

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| C1 | `resource_type` 非法格式（大写/空格/超长）→ 拒绝 | CK | 【B1-4】 | — |
| C2 | `classification` 非法值 → 拒绝 | CK | 【B1-4】 | — |
| C3 | `status` 非法值 → 拒绝 | CK | 【B1-4】 | — |
| C4 | `natural_key` 为空 → 部分 UQ 不生效，允许重复 | 允许 | 【B1-4】 | — |
| C5 | `natural_key` 重复（同 tenant+type、未删）→ 拒绝 | UQ | 【B1-4】 | — |
| C6 | 软删后同 `natural_key` 可重建 | 允许 | 【B1-4】 | — |
| C7 | `metadata` 默认 `'{}'` 且 NN | DEFAULT 断言 | 【B1-4】 | — |
| C8 | `acl_subject_types` 插入 `'group'` → CK 拒绝（P2-02；`D-B14-12 = A` 未增 whitelist） | 拒绝 | 【B1-4】 | — |
| C9 | `acl_subject_types` key 非法格式（大写/空格/超长）→ CK 拒绝 | 拒绝 | 【B1-4】 | — |
| C10 | ACL `effect` 非法值 → 拒绝 | CK | 【后续】（需先有 ACL 行） | — |

## 4. ACL Subject Tests

**前置事实（R4 保持）**：B1-4 不 seed ⇒ `acl_subject_types` **0 rows** ⇒ `subject_type_id` FK 不可满足 ⇒ **`resource_permissions` 不可写入**；ACL 校验 trigger G/H/I/J 最早 **P09 后**。

### 4.1 B1-4 可执行

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| A0-1 | 尝试插入任意 `resource_permissions` 行（含全部字段合法）→ **FK 拒绝**（无已注册 type） | 拒绝 | 【B1-4】 | — |
| A0-2 | `acl_subject_types` 无任何行（含 `user`/`role`/`agent`） | 0 行 | 【B1-4】 | — |
| A0-3 | **G/H/I/J** 四个 trigger **均不存在**（`tg_acl_subject_types_protect` 属 **C2** 家族，不在 G/H/I/J 之列） | 断言 | 【B1-4】 | — |
| A0-4 | 无任何 trigger 依赖不存在的表（DG 扫描：`tg_*` 引用的表全部已建） | 0 违例 | 【B1-4】 | — |
| A0-5 | `resource_permissions.subject_type_id` FK 目标为 `acl_subject_types`、行为 RESTRICT | 断言 | 【B1-4】 | — |

### 4.2 后续阶段执行（P13 seed / P09 trigger 之后）

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| A1 | `subject_type_id` = 未注册 type → FK/trigger 拒绝 | 拒绝 | 【后续】 | — |
| A2 | `group` 型 ACL 行 → 无法构造（CK 白名单） | 拒绝 | 【后续】 | — |
| A3 | user subject 存在 → 通过；随机 uuid → trigger RAISE | PASS / RAISE | 【后续】 | — |
| A4 | role subject 存在 → 通过；随机 uuid → trigger RAISE | PASS / RAISE | 【后续】 | — |
| A5 | agent subject 存在性（依赖 `agents`） | RAISE | 【后续】 | — |
| A6 | 软删 user → ACL 保留 | 行数不变 | 【后续】 | — |
| A7 | 硬删 user → 清理其 ACL | 行数归零 | 【后续】 | — |
| A8 | 删除被 ACL 引用的 role → 拒绝 | RAISE | 【后续】 | — |
| A9 | 删除未被引用 role → 允许 | 通过 | 【后续】 | — |
| A10 | agent 归档 → ACL 到期 | P09 后 | 【后续】 | — |
| A11 | membership removed → ACL 保留但授权 DENY；重加入恢复 | 授权层阶段 | 【后续】 | — |

## 5. Isolation Tests

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| I1 | 资源列表必须按 `tenant_id` 过滤（越权查询 → 0 行） | 0 行 | 【B1-4】 | — |
| I2 | 归属 tenant A 的 resource 不可被 tenant B 上下文读取；DB 侧验证 `tenant_id` NN + FK 存在 | 拒绝 / 0 行 | 【B1-4】 | — |
| I3 | `space_id IS NULL`（平台级资源/未定空间）可插入 | 允许 | 【B1-4】 | — |
| I4 | **历史项**：`D-B14-10 = A-1` 前 `Tenant-A + Tenant-B 的 Space` **可成立（无 DB 约束）**；A-1 冻结后该组合被 `tg_resources_tenant_space_consistency` 拒绝 | **原 KNOWN OPEN DECISION 已由 A-1 关闭**（历史记录保留） | 【B1-4】（历史项） | — |
| R-ISOLATION-01 | `space.tenant_id ≠ resource.tenant_id` → **REJECT**（**INSERT 路径**） | 拒绝 | 【B1-4】（D-B14-10 = A-1 FROZEN） | — |
| R-ISOLATION-02 | `space.tenant_id =  resource.tenant_id` → **ALLOW**（**INSERT 路径**） | 允许 | 【B1-4】（D-B14-10 = A-1 FROZEN） | — |
| R-ISOLATION-03 | 同上 R-01 的 **UPDATE 路径**：把 `space_id` 改为异租户 space → **REJECT** | 拒绝 | 【B1-4】（D-B14-10 = A-1 FROZEN） | — |
| R-ISOLATION-04 | 同上 R-02 的 **UPDATE 路径**：把 `space_id` 改为同租户 space → **ALLOW** | 允许 | 【B1-4】（D-B14-10 = A-1 FROZEN） | — |
| R-ISOLATION-05 | `space_id`: NOT NULL → NULL 的 UPDATE（离开空间）→ 允许；NULL → 非 NULL 且同租户 → 允许 | 允许 | 【B1-4】（D-B14-10 = A-1 FROZEN） | — |
| I5 | ACL 跨租户语义由授权层判定；DB 只做存在性校验 | 记录（非 PASS/FAIL） | 【后续】 | — |

> **R-ISOLATION-01…05 必须同时覆盖 INSERT 与 UPDATE**（避免只防 INSERT 不防 UPDATE）。
> **职责声明**：`tg_resources_tenant_space_consistency` **仅负责 structural integrity**（拒绝非法归属组合）；**不负责 authorization evaluation** —— 授权判定仍全部在 Authorization Layer。**所有 TC / R-ISOLATION 测试均为结构测试，不得改写为 authorization test。**

## 6. Migration Tests

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| M1 | fresh DB：`upgrade head` → `0007_b1_4_resource_acl`；**17 business tables + alembic_version = 18 physical tables**（§0.1 口径） | PASS | 【B1-4】 | — |
| M2 | `0006 → 0007` 增量升级（已有 B1-3 数据）成功 | PASS | 【B1-4】 | — |
| M3 | `downgrade` 到 `0006`：三表 + B1-4 的 **3 个 trigger**/index 全部移除，B1-3 对象完好（回到 14 business tables + alembic_version = 15 physical tables） | PASS | 【B1-4】 | — |
| M4 | re-upgrade（`0006 → 0007`）成功；对象数与 M1 一致 | PASS | 【B1-4】 | — |
| M5 | 重跑 `upgrade head` 幂等 | PASS | 【B1-4】 | — |
| M6 | 失败迁移 → 整体回滚 + 锁释放，`alembic_version` 不前进 | PASS | 【B1-4】 | — |
| M7 | 并发迁移 → advisory lock 串行化（第二 runner 失败/阻塞） | PASS | 【B1-4】 | — |
| M8 | 正式 `uap` 库在跑完全套后仍 **0 tables** | PASS | 【B1-4】 | — |
| M9 | `0007` 无 seed 语句（B1-4 = P06 无 seed） | 0 命中 | 【B1-4】 | — |
| M10 | migration 静态扫描：`create_table` 集合 = **17 business tables**（14 + 3） | 断言 | 【B1-4】 | — |

## 7. Security / Architecture Tests

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| SEC1 | Architecture Guard 9 项全过 | PASS | 【B1-4】 | — |
| SEC2 | Scope Scan：migration `create_table` 集合 = **17 business tables**（14 existing + 3 B1-4）；禁止表命中 **0** | PASS | 【B1-4】 | — |
| SEC3 | migration / B1-4 文档无行业词汇实质使用（family/company/restaurant/entertainment） | 0 命中 | 【B1-4】 | — |
| SEC4 | `metadata` / `conditions` 无密钥模式（api_key/secret/token） | 0 命中 | 【B1-4】 | — |
| SEC5 | 全量回归 0 失败（B1-1/1-2/1-3 套件不回退）；现基线 `128 passed` + Guard `9 passed` | PASS | 【B1-4】 | — |
| SEC6 | 未修改 `0001–0006` / `env.py` / 代码 / 既有测试；`git diff` 无已跟踪代码改动 | PASS | 【B1-4】 | — |
| SEC7 | `acl_subject_types` 治理：运行时**无写入口**（**D-B14-12 = A FROZEN** ⇒ `tg_acl_subject_types_protect` 断言：运行时 INSERT / `key` UPDATE / DELETE 被拒） | 拒绝 | 【B1-4】（D-B14-12 = A FROZEN） | — |

## 8. 决策依赖测试（Decision-dependent）

### 8.1 D-B14-08 — `action`（**FROZEN — A（2026-09-13）**）

**冻结内容**：保留 `NOT NULL` + `UQ(resource_id, subject_type_id, subject_id, action)`；**零新增 semantic/format contract**（**不加** regex CHECK、**不加** 命名空间 CHECK、**不加** semantic format contract、**不加** enum/whitelist/vocabulary）。`action` = **当前未冻结语义的非空 opaque action identifier**。

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| ACT-01 | `action IS NULL` → **拒绝**（NN；NOT NULL 先于 FK 检查，故 B1-4 可执行，无需已注册 type） | 拒绝 | 【B1-4】 | — |
| ACT-02 | 重复 `(resource_id, subject_type_id, subject_id, action)` → **拒绝**（UQ） | 拒绝 | 【后续】（需已注册 subject type，P13 后） | — |

- **`ACT-03` = 条件项（`conditional / non-canonical`）**：仅在采纳候选 **B（结构性 CHECK）** 时成立；`D-B14-08 = A` ⇒ **B 未采纳 ⇒ 条件未成立** ⇒ **不登记为表格行、不计入 canonical total 84**。
- **明确禁止**（R2 起强制，R4 保持）：任何针对 `read` / `write` / `create` / `update` / `delete` / `share` / `resource.read` / `resource.write` 等**未冻结词表**的取值测试。
- **依据**：`STEP1B_CONSTRAINT_MATRIX.md`（`action` 仅 NN，CK 行仅有 `effect IN ('allow','deny')`）· `STEP1B_SEED_STRATEGY.md` §4（属未来 `permissions` 表，**仅给形状**）· `STEP1B_B0_GATE_REPORT.md`（"seed permissions 字典清单待人工定稿"）· **`B1-4_DECISION_LOG.md` D-B14-08 = FROZEN — A**。
- **不得**把未来 `permissions` 字典 seed 草稿迁移为 `resource_permissions.action` 的 vocabulary。

### 8.2 D-B14-09 — `granted_by`（**FROZEN — A（2026-09-13）**）

**冻结内容**：`resource_permissions.granted_by` **`ON DELETE SET NULL`**；语义 = **actor attribution**（`resources.owner_id` = **ownership**，二者**独立**）。

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| GB-00 | `granted_by` 语义断言：列存在、nullable、FK → `users.id`、**`ON DELETE SET NULL`**；**语义为 actor attribution**（非 owner：ACL 无 owner 概念） | 断言 | 【B1-4】 | — |
| GB-01 | 删除 `granted_by` 对应 user → `resource_permissions` 行**保留**且 `granted_by = NULL`（**D-B14-09 = A 已批准 SET NULL**） | 保留 + NULL | 【后续】（需先有 ACL 行，P13 后） | — |
| GB-02 | `owner_id` 的 SET NULL（**独立测试，不得与 GB-01 / F3 合并**）：删除 owner → `resources` 保留且 `owner_id = NULL` | 保留 + NULL | 【B1-4】 | — |

> **R4 强制**：`F3`（owner_id SET NULL）· `GB-02`（owner_id SET NULL，独立断言）· `GB-01`（granted_by SET NULL）**三条分别存在，禁止合并**。
> **GB-01 的【后续】依据**：`D-B14-09 = A` 已批准 ⇒ **无待批准项**（`Post-Approval Level = —`）；但其执行需**先存在 ACL 行**，而 `acl_subject_types` 在 B1-4 为 0 rows ⇒ 属**阶段约束**，不属决策待定。
> **不得**因 `granted_by` 采用 SET NULL 而修改 `owner_id` 的既有删除策略。

### 8.3 D-B14-10 — Resource 归属一致性（**FROZEN — A-1（2026-09-13）**）

**冻结内容**：`tg_resources_tenant_space_consistency` · 最早 phase **P06 / B1-4** · **BEFORE INSERT OR UPDATE** · 依赖 `resources` + `spaces` · `space_id IS NULL` → allowed；`space_id IS NOT NULL` → `spaces.tenant_id` MUST equal `resources.tenant_id` · **structural integrity only**（非 authorization evaluator / ABAC engine / permission evaluator / business authorization logic）。

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| TC-00 | **历史项**：A-1 决策前 `Tenant-A + Tenant-B 的 Space` 可成立（无 DB 约束） | **原 KNOWN OPEN DECISION —— 已由 A-1 关闭**（历史记录保留） | 【B1-4】（历史项） | — |
| TC-01 | `Tenant-A + Tenant-A Space` → **ALLOW**（INSERT） | 允许 | 【B1-4】（A-1 FROZEN） | — |
| TC-02 | `Tenant-A + Tenant-B Space` → **REJECT**（INSERT） | 拒绝 | 【B1-4】（A-1 FROZEN） | — |
| TC-03 | `space_id = NULL` → **ALLOW**（平台级资源/未定空间） | 允许 | 【B1-4】（A-1 FROZEN） | — |
| TC-04 | **UPDATE 路径**（`tenant_id` / `space_id` 变更）同样被校验 | 拒绝/允许按 §5 | 【B1-4】（A-1 FROZEN） | — |

> **职责声明**：该 trigger **仅负责 structural integrity**（拒绝非法归属组合）；**不负责 authorization evaluation**。**TC / R-ISOLATION 系列均为结构测试，不得改写为 authorization test。**

### 8.4 D-B14-12 — 注册表治理（**FROZEN — A（2026-09-13）**）

**冻结内容**：`acl_subject_types` 为 **platform-controlled registry**；whitelist 保持 `user` / `role` / `agent`（**不得新增 `group` 或任何未冻结 subject type**，**不得修改 whitelist**，**不得提前 seed**）；采用 **platform-controlled registry + protection mechanism**（`tg_acl_subject_types_protect`）。

| # | 测试 | 期望 | Current Status | Post-Approval Level |
|---|---|---|---|---|
| REG-01 | 运行时 INSERT `acl_subject_types` 被拒 | 拒绝 | 【B1-4】（D-B14-12 = A FROZEN） | — |
| REG-02 | `key` UPDATE 被拒；`description` UPDATE 允许 | 拒绝/允许 | 【B1-4】（D-B14-12 = A FROZEN） | — |
| REG-03 | DELETE 被拒（退役走 `archived_at`） | 拒绝 | 【B1-4】（D-B14-12 = A FROZEN） | — |

> **执行说明（不改变测试语义）**：`REG-02` / `REG-03` 需先存在一行 `acl_subject_types`；因 registry 受保护（`REG-01`），夹具行须经**受控写入路径**构造 —— **W-3 已决议**：合法行**仅经 migration 建立**（schema governance，非 Domain runtime registration），机制候选 M-1…M-3 见 `B1-4_DESIGN.md` §8.1，**不影响本测试的层级归属**。
> **边界**：protection mechanism 仅承担 **registry 治理**，不得演变为 Domain authorization；registry 不允许 Domain / Plugin / 普通业务代码 runtime 自由注册，亦不得通过未来 API 任意扩展。

## 9. 优先级汇总（R4 重核，未人为升降级）

**判定原则**：P0 = 缺失会使交付物不可用或产生未授权状态；P1 = 完整性/可运维性；P2 = 记录性/低频；P3 = 后续阶段。

| 优先级 | 测试 | Current Status 分布 |
|---|---|---|
| **P0** | S1–S5、S9–S11、F1–F3、F7、A0-1…A0-5、I1–I2、I4、TC-01…TC-04、R-ISOLATION-01…05、M1–M4/M6/M8–M10、SEC1–SEC2、SEC5–SEC7、ACT-01、REG-01…03 | 全为 【B1-4】 |
| **P1** | S6–S8、F4–F6、C1–C9、M5/M7、SEC3–SEC4 | 【B1-4】为主；F4–F6 为【后续】 |
| **P2** | C10、I3、I5、TC-00（历史项） | 【后续】/【B1-4 历史项】 |
| **P3** | §10 后续阶段登记项 | 【后续】 |
| **【待裁定】组** | **空** —— `D-B14-08` / `D-B14-09` / `D-B14-12` 已 FROZEN，`GB-01` / `REG-01…03` / `SEC7` 已按裁定归类 | — |

> **未因"矩阵好看"而升降级**：`I4` / `TC-00` 保留为**历史项**（原 KNOWN OPEN DECISION，已关闭）；`ACT-02` 因依赖 P13 数据条件而降为【后续】，而非因其重要性下降。

## 10. 后续阶段登记（承接，不在 B1-4 执行）

**以下 `D1–D7`（7 行）为矩阵外登记项，不属于 B1-4 TEST_MATRIX canonical count（84），且不参与状态统计。**

| # | 测试 | 归属阶段 |
|---|---|---|
| D1 | `conditions` ABAC 求值 | Authorization Layer |
| D2 | `HIGHLY_CONFIDENTIAL` 禁止降级到公共模型（DB CHECK） | P08 `ai_policies` |
| D3 | DENY > ALLOW 端到端（ACL 与 role 链混合） | Authorization Layer |
| D4 | RLS 策略（若启用 Q1） | 独立阶段 |
| D5 | `group` 主体注册 + 校验 + 测试 | 未来（P2-02 路径） |
| D6 | ACL 变更同事务审计 | P10（`audit_logs`） |
| D7 | ACL 行 UQ/effect/CK 完整校验（A1–A11、F4–F6、C10、ACT-02） | P13 后 |

## 11. 本轮声明

**Implementation tests written = 0** —— 本文件仅为设计层测试矩阵；未修改 `tests/` 下任何文件、未新增测试代码、未执行 `pytest` 变更、未创建 migration、未执行 DDL/DML。

**Canonical Total = 84**（R4 唯一口径）；**ACT-03 = conditional / non-canonical（不计入）**；**D1–D7 不计入**。
