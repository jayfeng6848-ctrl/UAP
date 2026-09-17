# STEP 1-B / B1-2 — Decision Log（Architecture Decision Resolution）

Status: **FROZEN DECISIONS（PREP）** · 日期：2026-09-08
来源：B1-2 PREP Report 的 P1/P2/P3 未决项 + 人工裁定
范围：`tenants` / `spaces` / `tenant_memberships` / `memberships` 的 B1-2 设计冻结（**不建表、不写 migration**）

> 每条决策含：Problem / Options / Decision / Reason / Security Impact / Implementation Phase / Rejected Alternatives。

---

# D-01 — `role_id` Forward Dependency

| 项 | 内容 |
|---|---|
| **Problem** | 冻结设计要求 `tenant_memberships.role_id` 与 `memberships.role_id` 引用 `roles.id`，但 `roles` 属 B1-3（后续阶段）。如何在不提前创建 `roles` 的前提下表达该引用？ |
| **Options** | A. B1-2 保留 `role_id` 列、不创建 FK；B1-3 建 roles 后补 FK（deferred constraint）<br>B. B1-2 只建 `tenants`+`spaces`，membership 两张表整个延后到 B1-3<br>C. 使用 `DEFERRABLE INITIALLY DEFERRED` FK 引用尚不存在的 roles 表<br>D. B1-2 建 `roles` 表（提前实施） |
| **Decision** | **A（Forward Dependency / Deferred Constraint）**：<br>· **B1-2**：保留 `role_id uuid` 列 → **不创建**指向 `roles` 的 FK constraint<br>· **B1-3**：创建 `roles` 后补 `tenant_memberships.role_id → roles.id` 与 `memberships.role_id → roles.id`（`ON DELETE RESTRICT`），并执行完整 FK / 数据一致性验证<br>· **B1-2 阶段 `role_id` 为 `NULL` 允许**（无 FK、无内置角色可引用；B1-3 回填内置角色后 `SET NOT NULL`） |
| **Reason** | ① 引用完整性只能在目标表存在后建立（FK 是物理约束，不是逻辑约定）；② B1-2 期间没有 `roles` 行可供引用，强制 NOT NULL 会迫使应用层写入**无法校验的假 uuid**，比 NULL 更危险；③ 保留列结构避免 B1-3 迁移时改列（只加约束） |
| **Security Impact** | **重要**：B1-2 阶段 `role_id` **不构成数据库级引用完整性**，因此**不能**把 B1-2 的 `role_id` 当作完整授权安全边界。授权层在 Role 完整实现前必须 **fail-closed**（见 D-02）。B1-3 补 FK + scope trigger 后才形成完整边界 |
| **Implementation Phase** | B1-2 = 列 + 无约束（NULL 允许）→ B1-3 = 回填 → `SET NOT NULL` → `ADD CONSTRAINT FK` → scope trigger → 一致性验证 |
| **Rejected Alternatives** | **C（DEFERRABLE FK）— 明确禁止**：`DEFERRABLE` 只把约束**检查时机**延到事务提交，属于"约束已存在但检查延后"；它**不能**在目标表 `roles` 不存在时创建。把它理解为"可引用不存在的表"是错误认知<br>**B（整表延后）**：与 B1-2 范围（4 表）不符，且 Tenant/Space 上下文缺失 membership 会导致 B1-2 交付不完整<br>**D（提前建 roles）**：违反"禁止创建 Role/Permission 表"的硬约束 |

---

# D-02 — Role Scope Enforcement（B1-2 窗口期）

| 项 | 内容 |
|---|---|
| **Problem** | 冻结设计：`tenant_memberships.role_id` 必须是 **TENANT scope** role；`memberships.role_id` 必须是 **SPACE scope** role。B1-2 无 `roles` 表 → 数据库无法完成 FK 与 scope trigger 校验（PG 也无法用 CHECK 跨表） |
| **Options** | ① B1-2 完全不校验（仅应用层约定）<br>② B1-2 应用层强制 fail-closed 校验，B1-3 补数据库强制<br>③ 用 CHECK 硬编码 scope 字符串（不可行：scope 存于 roles 表） |
| **Decision** | **②**：<br>· **B1-2**：`role_id` 字段保留；**数据库 role FK 不创建**；**数据库 role scope validation 不创建**；<br>· **B1-2 应用层（Authorization Layer）必须拒绝**：不存在 role / role scope 不匹配 / 非 TENANT role 用于 `tenant_memberships` / 非 SPACE role 用于 `memberships`<br>· **B1-3**：完成 `roles` + role scope + role FK + **数据库 scope 强制** + 应用层校验，并通过 5 项验收 |
| **Reason** | 数据库强制依赖表存在（不可提前）；窗口期必须由应用层承担不变式，否则会出现"无校验的 role 引用"漏洞；应用层 fail-closed 是 B1-2 唯一可用的强制点 |
| **Security Impact** | 窗口期（B1-2 交付后至 B1-3 完成前）：授权层**必须 fail-closed**——任何 role 解析失败/不匹配 → DENY（不允许"默认放行"）。B1-3 后形成 DB + 应用双重强制 |
| **Implementation Phase** | B1-2 = 应用层校验（必须实现于授权层，非 DB）→ B1-3 = `tg_tm_role_scope` / `tg_membership_role_scope` + FK + 5 项测试 |
| **Rejected Alternatives** | ①不校验 → 违反 fail-closed，产生越权窗口；③ CHECK 硬编码 → 需要把 scope 复制到 membership 表（冗余且会漂移），且与冻结设计（trigger 校验）不符 |

**B1-3 验收矩阵（5 项，写入 Test Matrix §4）**

| 场景 | 期望 |
|---|---|
| TENANT role → `tenant_memberships` | **PASS** |
| SPACE role → `tenant_memberships` | **DENY** |
| SPACE role → `memberships` | **PASS** |
| TENANT role → `memberships` | **DENY** |
| 不存在 role | **DENY** |

---

# D-03 — `spaces.owner_id` 删除语义

| 项 | 内容 |
|---|---|
| **Problem** | 冻结设计未明示 `spaces.owner_id → users.id` 的 `ON DELETE` 行为 |
| **Options** | ① `ON DELETE SET NULL`（建议）② `ON DELETE RESTRICT` ③ `ON DELETE CASCADE`（禁止） |
| **Decision** | **PROPOSED — HUMAN APPROVAL REQUIRED**：建议 `spaces.owner_id → users.id ON DELETE SET NULL`。语义：User 删除 → Space 保留 → `owner_id = NULL`。**本阶段不实现**，等待人工批准 |
| **Reason** | Space 是协作上下文（承载成员与资源），不得因 owner 删除而消失；SET NULL 保留协作数据，交由租户管理员重新指派 owner |
| **Security Impact** | 中：owner 删除后 Space 无 owner → 授权层须保证仍可通过 `memberships` 与 tenant 角色治理（不依赖 owner 列做唯一授权依据） |
| **Implementation Phase** | B1-2 实施前需人工批准；未批准前 **不得实现任何 owner FK 行为**（或按审计指示） |
| **Rejected Alternatives** | **③ CASCADE：明确禁止** —— "删除 owner 会删除 Space" 是错误且危险语义；② RESTRICT 会阻止用户硬删（retention 流程受阻），不如 SET NULL 灵活 |

---

# D-04 — RLS Status

| 项 | 内容 |
|---|---|
| **Problem** | 是否在本阶段启用 PostgreSQL Row Level Security 作为租户隔离层 |
| **Options** | ① 现在启用 RLS + policy ② 保持 OPEN，待 Resource/ACL 阶段决定 ③ 永不启用 |
| **Decision** | **RLS = OPEN DESIGN QUESTION（保持）**：<br>· **不启用 RLS**<br>· **不创建 RLS policy**<br>· **不修改 PostgreSQL security configuration**<br>· 待 Resource / ACL 阶段结合实际访问模型决定 |
| **Reason** | RLS 的正确形态依赖资源访问模型（Resource/ACL 尚未落地）；过早启用会导致 policy 反复重写，且连接池 `SET LOCAL` 泄漏风险需在压测后评估（Q1） |
| **Security Impact** | 当前隔离依靠：应用层 tenant scope 强制 + 授权 Pipeline [2][3] + 越权审计（CRITICAL）。**这不是最终形态**；RLS 是后续加固项，不构成本阶段安全缺口（但需在审计中记录为开放项） |
| **Implementation Phase** | 后续阶段（Resource/ACL 后）评估；本阶段零动作 |
| **Rejected Alternatives** | ①现在启用 → 与"等待 Resource/ACL 阶段"的裁定冲突；③永不启用 → 过度决定，留给后续阶段 |

---

## 附：决策对 B1-2 各文档的影响

| 文档 | 受影响处 | 更新 |
|---|---|---|
| `SCHEMA_REVIEW.md` | §5（OPEN DECISION）→ 改为 FROZEN D-01；role_id 明确 `NULL`（B1-2）；§9 移除 OPEN 项 | ✅ |
| `CONSTRAINT_MATRIX.md` | role_id 行（FUTURE → D-01 定义）；§5 Forward Dependency 约束表；§7 PROPOSED（D-03） | ✅ |
| `DEPENDENCY.md` | §2 roles FUTURE + **非 DEFERRABLE** 说明；B1-3 收敛步骤 | ✅ |
| `TRIGGER_STRATEGY.md` | T6/T7 FUTURE + B1-2 应用层 fail-closed 要求（D-02）；§4 风险更新 | ✅ |
| `TEST_MATRIX.md` | §4 Scope 增加 B1-2 应用层校验项 + B1-3 DB 5 项；M10 role_id 语义；新增 D-03/D-04 处置 | ✅ |
| `PREP_REPORT.md` | §16 风险表（P1 → RESOLVED）、Gate 状态 | ✅ |
