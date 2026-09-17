# STEP 1-B / B1-3 — Decision Log（Role & Permission Foundation PREP）

Status: **PREP DECISIONS** · 日期：2026-09-08
格式：`D-0x / Question / Options / Recommended / Reason / Security Impact / Migration Impact / Status`

> **Status 语义**：`FROZEN` = 冻结设计已有明确答案（引用来源，本阶段只确认）；`OPEN` = 冻结设计未定义，**不自行补充**，需人工审计裁定。

---

## D-01 — `roles.description` 字段是否存在？

- **Question**：`roles` 是否需要 `description`（说明文本）列？
- **Options**：A. 不加（严格按冻结） B. 加 `description text NULL`
- **Recommended**：**A（不加）**；如需说明可放 `name`/外部文档，或后续 revision 增列
- **Reason**：冻结 `CORE_DOMAIN_MODEL.md` §1.2 `roles.fields` = `key`、`name`、`scope`、`is_system`、`status`、`created_at`、`updated_at`、`archived_at` —— **无 description**。B1-3 纪律：不自行增加字段
- **Security Impact**：无
- **Migration Impact**：若未来加列需独立 revision（可空，无需回填）
- **Status**：**OPEN — HUMAN DECISION**（默认按 A 实施，除非审计要求增加）

## D-02 — `permissions` 是否需要 `name` / `status`？

- **Question**：用户清单提到 `permission.name` / `status`；冻结字段为 `key`、`resource_type`、`action`、`description`、`is_system`、`created_at`
- **Options**：A. 不加（严格冻结） B. 加 name/status
- **Recommended**：**A**；展示名可用 `key`，生命周期用 `is_system` + 无 status（字典表不软删）
- **Reason**：冻结无这两列；permissions 是**平台级字典**（无租户维度、无 updated_at），不需要状态机
- **Security Impact**：无（权限存在性由 `uq_permissions_key` 与授权层保证）
- **Migration Impact**：无
- **Status**：**OPEN — HUMAN DECISION**

## D-03 — Permission 是否需要 scope？

- **Question**：Permission 是否需要 `PLATFORM/TENANT/SPACE` scope 并与 `Role.scope` 对齐？
- **Options**：A. **scope-neutral（冻结现状）** B. 加 `permissions.scope` + `Role.scope == Permission.scope` 约束
- **Recommended**：**A —— Permission 天然 scope-neutral**
- **Reason**：冻结 `permissions` 无 scope 列，且定位为"平台级权限字典，无租户维度"；权限的**可用范围由 Role 的 scope 决定**（TENANT role 只能授予 TENANT 层可用的权限语义）
- **Security Impact**：中 —— 该语义必须写入文档与授权层实现（不能只存在于代码注释）；否则可能出现"SPACE role 绑定平台级权限"。授权层需在绑定时校验 permission 适用性（B1-3 只提供存储，不实现求值）
- **Migration Impact**：无（不新增列）
- **Status**：**FROZEN（采纳 A，来源 CORE_DOMAIN_MODEL §1.2）+ 实施要求：语义文档化 + 授权层遵守**

## D-04 — `role_permissions` 唯一性：PK 含 effect 还是 UNIQUE(role_id, permission_id)？

- **Question**：冻结 PK = `(role_id, permission_id, effect)`；是否应改为 `UNIQUE(role_id, permission_id)`？
- **Options**：A. **保持冻结（含 effect）** B. 改为两列唯一
- **Recommended**：**A（保持冻结）**
- **Reason**：冻结设计明确复合 PK 含 effect，用于表达同一 (role, permission) 的 allow 与 deny 两行（deny 优先由应用层裁决）
- **Security Impact**：**高** —— 若同一 (role,permission) 同时存在 allow 与 deny 而应用层未实现"deny 绝对优先"，授权结果不确定。**必须在授权层强制 deny 优先**，并测试"deny+allow 并存 → DENY"
- **Migration Impact**：无（不改结构）；应用层需实现 deny 优先
- **Status**：**FROZEN（A）+ 应用层约束（B1-3 不实现求值器，但需记录为授权层硬性要求）**

## D-05 — `is_system` 语义与修改主体

- **Question**：系统角色是否可删/可改、**谁**可以改、与 Tenant 自定义角色如何区分？
- **Options**：A. 冻结现状（`is_system=true` 禁改禁删，trigger）+ 修改主体未定义 B. 定义平台管理员可通过受控流程修改
- **Recommended**：**先按 A 实施；修改主体/流程需审计裁定**
- **Reason**：冻结 CK/trigger 明确"is_system=true 时禁止修改/删除"；但"谁可以改"未定义
- **Security Impact**：高 —— 系统角色（`platform_admin`/`tenant_admin`/`tenant_member`/`space_admin`/`space_member`）是授权骨架；任何绕过 trigger 的修改都是提权路径
- **Migration Impact**：无（trigger 已定义）
- **Status**：**OPEN — HUMAN DECISION**（谁可修改 / 是否允许受控变更流程）

## D-06 — `roles.status` 枚举值

- **Question**：`roles.status` 的合法取值？
- **Options**：A. `'active','archived'`（与 `archived_at` 配套） B. 其它枚举 C. 不设 CK（仅 NOT NULL）
- **Recommended**：**C 或 A 需裁定**；冻结**未给出** roles.status 枚举（与 tenants/spaces 不同）
- **Reason**：冻结 `roles` CK 只列了 `scope IN (...)`，未列 status 枚举
- **Security Impact**：低-中（status 参与授权过滤时，非法值可能导致"僵尸角色"）
- **Migration Impact**：若加 CK 需校验现有数据
- **Status**：**OPEN — HUMAN DECISION**（不自行增加 CK）

## D-07 — Platform Role 的绑定模型

- **Question**：`platform_admin` 如何绑定到具体用户？当前无 `platform_memberships` 表
- **Options**：A. **不建表**：平台管理员由部署配置/首个引导账户（应用层常量或 seed + 环境变量） B. 建 `platform_memberships` C. 复用 `tenant_memberships`（**禁止**：会破坏 scope 边界）
- **Recommended**：**A（不建表）**；**明确禁止**为"完整"提前创建 platform_memberships
- **Reason**：冻结设计无平台成员表；创建它属于新增实体，超出 B1-3 范围
- **Security Impact**：**高** —— 平台管理员是最高权限；绑定方式必须有明确、可审计的机制（建议：seed 时通过受控 bootstrap 指定，且写 audit；不得有"任何用户自动成为 platform_admin"路径）
- **Migration Impact**：无（不建表）；seed 策略需 D-08 裁定
- **Status**：**OPEN — HUMAN DECISION（P1）**

## D-08 — `role_id` NULL 语义（B1-3 收敛后）

- **Question**：B1-3 补 FK 后，`tenant_memberships.role_id` / `memberships.role_id` 是否 NOT NULL？
- **Options**：A. **回填后 SET NOT NULL**（D-01/B1-2 已冻结） B. 保持 NULL（迁移兼容）
- **Recommended**：**A**（已有冻结：B1-2 D-01 决策表明确"B1-3 回填内置角色后 SET NOT NULL"）
- **Reason**：NULL role 会造成"无角色成员"的授权盲区（default deny 虽可挡住，但数据语义不完整）
- **Security Impact**：高 —— NULL role 必须**不能**被解释为任何权限；应用层仍须 fail-closed（D-02）
- **Migration Impact**：**中** —— 必须先 seed 内置角色 → 回填所有 NULL 行 → 校验无 NULL → 再 SET NOT NULL + ADD FK；回填失败必须**中止 migration**（不允许静默填假值）
- **Status**：**FROZEN（A，来源 B1-2 DECISION_LOG D-01）**

## D-09 — Role / Permission 删除语义

- **Question**：删除 Role / Permission 时 `role_permissions` 行为？Role 被 membership 引用时？
- **Options**：A. 冻结：`role_permissions` 两侧 **CASCADE**；membership 对 role **RESTRICT** B. 其它
- **Recommended**：**A（冻结）**
- **Reason**：`CORE_DOMAIN_MODEL` §1.2：`role_permissions` FK 均 `ON DELETE CASCADE`；membership `role_id → roles.id ON DELETE RESTRICT`
- **Security Impact**：中 —— 误删 permission 会级联移除所有角色上的该权限（需审计）；被 membership 引用的角色不可删（防止悬空）
- **Migration Impact**：无（新建表按此实现；membership 侧在 0005 补 FK）
- **Status**：**FROZEN（A）**

## D-10 — Default Role 的归属（Built-in / Seed / Constant）

- **Question**：`platform_admin` / `tenant_admin` / `tenant_member` / `space_admin` / `space_member` 是内置常量还是数据库 seed？
- **Options**：A. **数据库内置角色（`is_system=true`）+ seed**（冻结） B. 应用常量（无数据行）
- **Recommended**：**A（冻结，SEED_STRATEGY）**
- **Reason**：B1-2 SEED_STRATEGY 与 P2-01 已冻结：这些是 **TENANT/SPACE/PLATFORM scope 的系统内置角色**，必须落库（membership.role_id 需要引用实体）
- **Security Impact**：高 —— 内置角色决定默认权限；seed 必须幂等且不可被普通租户操作删除（trigger 保护）
- **Migration Impact**：
  - `platform_admin` + 平台权限字典：初始 seed（migration 或 bootstrap）
  - `tenant_admin/tenant_member`、`space_admin/space_member`：**运行时 onboarding**（每租户/每空间创建时播种），非 migration
- **Status**：**FROZEN（A）+ seed 幂等要求（重复执行不重复创建）**

## D-11 — Role Scope Enforcement 机制

- **Question**：scope 约束用 Trigger / Composite FK / Application？
- **Options**：A. **Trigger（DB 完整性）+ Application（授权决策）双层** B. Composite FK C. 仅应用层
- **Recommended**：**A**
- **Reason**：冻结 B0 TRIGGER_INVENTORY 已定义 `tg_tm_role_scope` / `tg_membership_role_scope`；PG 无跨表 CHECK；Composite FK 无法统一（TENANT 用 tenant_id、SPACE 用 space_id，列不同）
- **Security Impact**：高 —— 必须两层同时存在；**不得**创建"万能 trigger"处理所有权限逻辑
- **Migration Impact**：trigger 在 roles 表建立后创建（0005 步骤 4）
- **Status**：**FROZEN（A）**

## D-12 — Role key 唯一性：global vs (scope, key) vs (tenant_id, scope, key)

- **Question**：role key 的唯一性粒度？
- **Options**：A. global unique B. (scope, key) C. **scope-scoped 部分唯一（冻结）**
- **Recommended**：**C（冻结）**：三条部分唯一索引（platform / (tenant_id,key) / (space_id,key)）
- **Reason**：`CORE_DOMAIN_MODEL` §1.2 明确三条部分唯一索引；语义上允许不同租户/空间各自定义同名 key（如每租户都有 `tenant_member`）
- **Security Impact**：中 —— 必须保证三条索引谓词互斥，否则同一 key 可能重复或冲突；解析角色必须带 tenant_id/space_id（否则歧义）
- **Migration Impact**：无
- **Status**：**FROZEN（C）**

---

## DECISION RESOLUTION ROUND（2026-09-08 晚）— D-05…D-16 全部 FROZEN

> 本段为人工审计后 Resolution；保留此前 D-01…D-13 的原始 Question/Options 作为历史记录，不改写。

### R-D-05 — System Role Protection（原 D-05 → **FROZEN**）

| 操作 | System Role（`is_system=true`） |
|---|---|
| DELETE | ✗ 拒绝（BEFORE DELETE trigger RAISE） |
| 修改 key | ✗ |
| 修改 scope | ✗ |
| 修改 tenant_id | ✗ |
| 修改 space_id | ✗ |
| 修改 is_system（含 true→false） | ✗（禁止降级绕过保护） |
| 修改 name | ✗ |
| 修改 status | ✗ |
| 修改 permissions（role_permissions 绑定） | **DB 层不设 trigger 保护**；保护来自"B1-3 无写入路径"（无 API/应用可改 seed 权限；权限变更 = 新 migration revision，经人工审计） |

- **受保护对象**：`platform_admin` / `tenant_admin` / `tenant_member` / `space_admin` / `space_member`（scope 按各自层）
- 实现：`tg_roles_is_system_protect` = `BEFORE UPDATE OR DELETE ON roles`，`IF OLD.is_system THEN RAISE`（**无条件拒绝 UPDATE 与 DELETE**，比"仅禁改删特定列"更强且无旁路）
- **不做**"超级管理员万能权限"设计（`is_system` 不隐含任何权限；权限只能来自 `role_permissions`）
- 修改/演进系统角色的唯一通道：**新 migration revision（人工审计）**，可临时 drop 保护 trigger、变更、重建
- Security Impact：高（防提权与误改）；Migration Impact：无（trigger 在 0005 建）

### R-D-06 — Role Status（原 D-06 → **FROZEN**）

- **枚举**：`roles.status ∈ ('active','disabled','archived')`（新 CK `ck_roles_status`）
- 命名依据：与已有 status 词族一致（tenants 用 archived/deleted；此处角色无 hard delete，故用 archived），并引入 `disabled` 表达"停用但不归档"
- 授权语义（解释在 **Authorization Layer**，DB 只做枚举 + 绑定校验）：
  | 状态 | 可被新 membership 绑定 | 既有 membership | 恢复 |
  |---|---|---|---|
  | active | ✅（trigger 校验 `status='active'` 才允许引用） | 正常参与授权 | — |
  | disabled | ❌（引用被拒） | 授权层视同无角色 → **DENY**（fail-closed；DB 不自动清行） | 可经 UPDATE 回 active（仅自定义角色；系统角色不可改） |
  | archived | ❌ | 同上 → DENY | 自定义角色可经受控 UPDATE 回 active |
- **role 被 membership 引用时可删除？** ❌（FK RESTRICT）
- 系统角色（is_system）永远 `active`（不可 UPDATE，见 R-D-05）
- 是否阻塞 0005：**否**（CK 与绑定校验均可在 0005 一次实现）
- Security Impact：中高（disabled/archived 必须 fail-closed，不得默认放行）；Migration Impact：需要 `ck_roles_status` + membership 绑定 trigger 增加 `roles.status='active'` 检查

### R-D-07 — Platform Role Binding（原 D-07 → R1 曾 **FROZEN**，**R2 复核撤回 → NOT RESOLVED（P1）**）

> ⚠️ **ROUND-2 复核（2026-09-08，见文末 §R2-D-07）**：R1 的"既有 `platform_metadata` 键值表、零新增结构"前提**不成立**。
> 证据：该表**不在冻结模型**（CORE_DOMAIN_MODEL §1.2 / ER_MODEL / STEP1B_SCHEMA_DEPENDENCY 的 29 张核心表清单均无）；
> 仅存在于 legacy 自研 runner `migrations/0001_platform_baseline.sql`；Alembic `0001_baseline` 为 **no-op 锚点（不建任何对象）**
> → 纯 Alembic 全新库 `upgrade head` 不会创建它；正式 `uap` 库 0 表（从未应用）。
> 以下 R1 原文仅作**历史记录**保留，**不作为生效决策**；生效结论见 §R2-D-07。

**（R1 原文 · 已撤回）** 不建 `platform_memberships`、不改 B1-1。 绑定载体 = **`platform_metadata` 键值表**：

```
key  = 'platform.admin_user_id'
value = <user uuid>     （单例；应用层校验 user 存在且 active）
```

- **1. 绑定存哪**：`platform_metadata`（既有表，零新增结构）
- **2. 谁可获得 `platform_admin`**：仅**安装引导（bootstrap）**：受控 CLI/seed 一次性写入；此后无人能"获得"
- **3. 谁可撤销/转让**：绑定的平台用户通过受控流程（CLI/运维）转让给另一 active user；每次转让写 `audit_logs(action='platform.admin.transfer')`
- **4. 如何验证**：授权层读取 `platform_metadata` → 校验目标 user 存在、`status='active'` → 该 user 获得 `platform_admin`(PLATFORM scope) 的权限
- **5. 如何审计**：绑定建立/读取/转让均写 audit（应用层；B1-3 记录契约）
- **6. 普通 tenant admin 能否获得**：不能（无任何租户侧写入 `platform_metadata` 的路径）
- **7. Tenant/Space membership 绝不可能产生 PLATFORM 权限**：正确 —— DB 层无表可引用 PLATFORM role（`tg_tm_role_scope`/`tg_membership_role_scope` 拒绝 `scope='PLATFORM'`），PLATFORM 权限唯一来源是 `platform_metadata` 绑定
- **8. 新用户默认**：永远没有 Platform role（绑定是单例，默认无）

安全原则：**无明确绑定 → DENY**；`is_system=true` **不**自动获得平台权限；`platform_admin` **不**对所有人生效。
- Security Impact：高（平台最高权限的授予/撤销路径必须唯一、可审计）；Migration Impact：无（无新表）；弱引用（value 无 FK）由应用层校验兜底，如需 DB 级强引用须新表 → 未来人工批准

### R-D-08 — Membership Role Backfill（原 D-08 实施细节 → **FROZEN**）

- 回填目标（按冻结 P2-01/D-10 复核确认）：`tenant_memberships.role_id := tenant_member`（同租户 TENANT role）；`memberships.role_id := space_member`（同空间 SPACE role）
- **实际 0005 顺序**（基于 PG 约束依赖，全部在**单事务**；`transaction_per_migration=false` → 失败整体回滚）：
  1. `CREATE TABLE permissions` → `roles`（root/次级，FK tenants/spaces 已存在）
  2. 建 `tg_roles_*` 与 membership scope trigger（此时 roles 表已存在）
  3. **Seed 系统角色**（幂等）：`platform_admin`(PLATFORM, 全局)；对**每个既有 tenant** 播种 `tenant_admin`+`tenant_member`；对**每个既有 space** 播种 `space_admin`+`space_member`
  4. **回填**：`UPDATE tenant_memberships SET role_id = 同租户 tenant_member 的 id WHERE role_id IS NULL`；memberships 同理
  5. **校验（硬门禁）**：`SELECT count(*) WHERE role_id IS NULL` 必须为 0；逐行校验 role 存在且 scope/归属匹配 —— 任一失败 → **RAISE → ROLLBACK**（不允许部分成功、不允许 silently ignore、不允许随便填 admin）
  6. `ALTER TABLE ... ALTER COLUMN role_id SET NOT NULL`
  7. `ALTER TABLE ... ADD CONSTRAINT fk_tm_role / fk_membership_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT`
  8. commit
- **历史兼容**：正式 `uap` 当前 0 表 → 无生产回填；0005 设计目标 = 对"已执行 0004 且有 membership 数据"的库确定且安全（步骤 3–5 处理任意既有数据）
- **downgrade**（开发用）：DROP FK → DROP NOT NULL（数据保留）→ DROP trigger → DROP 三表 → 恢复 0004 形态
- 测试场景（disposable）：Tenant A/User A/Space A + membership → 0005 后断言 `role_id=tenant_member/space_member`、NOT NULL、scope 正确、FK 有效
- Security Impact：高（回填是"从无角色到有角色"的信任建立；失败必须中止）；Migration Impact：本决策即迁移流程

### R-D-13 — Role Key Format（原 D-13 → **FROZEN**）

- **CHECK**：`roles.key ~ '^[a-z][a-z0-9_]{1,63}$'`
- 字符集：小写字母 a–z、数字 0–9、下划线 `_`；**禁止**大写、`-`、`.`、空格
- 首字符：**必须小写字母**；数字允许（非首位）；`_` 允许且**允许连续**（不做排除，避免过度复杂正则；命名规范由约定治理）
- 长度：2–64（`{1,63}` 尾段 + 首字符）
- 系统角色合规性：`platform_admin`(14) `tenant_admin`(12) `tenant_member`(13) `space_admin`(11) `space_member`(12) —— **全部合法** ✅
- Security Impact：低（约束命名空间，防注入式命名）；Migration Impact：`ck_roles_key` 随建表

### R-D-14 — DENY > ALLOW（**FROZEN SECURITY INVARIANT**）

- 当同一 `(role, permission)` 同时存在 `allow` 与 `deny`：**最终 = DENY**
- 实现层：**Authorization Layer**（数据层允许两行并存，PK 含 effect —— D-04）；**不在 Database Trigger 中做授权解释**
- 写入：DECISION_LOG（本条目）+ SCHEMA_TEST_MATRIX（新增 "allow+deny 并存 → DENY" 用例）+ 授权设计契约
- Security Impact：高（防 deny 被 allow 覆盖）；Migration Impact：无

### R-D-15 — Permission Scope-neutral（**FROZEN**，对齐 D-03）

- **Permission 不拥有授权 Scope**：描述 **Capability**；**Role** 拥有 Role Scope；**Membership** 表达 Membership Context
- 授权链：`Identity → Membership → Role → Role Scope → Permission → Request Context`
- **不**给 `permissions` 增加 `scope` 列（冻结设计无此列）
- Security Impact：中（语义必须在授权层实现并测试，不得只存在于注释）；Migration Impact：无

### R-D-16 — SPACE Role 是否保存 tenant_id（→ **FROZEN：Option A**）

- **SPACE role 只存 `space_id`，`tenant_id` 为 NULL**；租户关系经 `spaces.tenant_id` 间接获得
- Scope Shape（最终冻结，`tg_roles_scope_shape` 强制）：

| Scope | tenant_id | space_id |
|---|---|---|
| PLATFORM | NULL | NULL |
| TENANT | NOT NULL | NULL |
| SPACE | **NULL** | NOT NULL |

- 不接受 Option B（冗余 tenant_id）理由：① 无冗余 → 不需要额外 `tenant_id == spaces.tenant_id` 跨表约束；② 租户一致性由**既有 trigger 传递保证**：`tg_membership_tenant_consistency`（membership.tenant_id = spaces.tenant_id） + `tg_membership_role_scope`（roles.space_id = membership.space_id） ⇒ **role 租户 == membership 租户**；③ 不为性能自行加冗余
- Security Impact：中（隔离证明依赖两个既有 trigger 的合取，需测试覆盖传递场景）；Migration Impact：`tg_roles_scope_shape` 形状含 SPACE→tenant NULL

---

## DECISION RESOLUTION ROUND 2 — Verification & Correction（2026-09-08，人工审计复核轮）

> 触发：审计复核要求"逐项验证前提/载体是否真实存在于冻结模型"，并补充显式 ALLOW/DENY/ACTOR/CONDITION 规则。
> 纪律：**以仓库文件为准，不凭记忆**；宁可 BLOCKED，不把未闭环项伪装成 FROZEN。
> 复核基线：`CORE_DOMAIN_MODEL §1.2` / `ER_MODEL` / `STEP1B_SCHEMA_DEPENDENCY` / `migrations_alembic`（head=0004）。

### R2-D-05 — System Role Protection（R-D-05 保持 FROZEN，补显式 Actor 规则 + 收紧 INSERT 提权口）

**Trigger 升级**：`tg_roles_is_system_protect` = `BEFORE INSERT OR UPDATE OR DELETE ON roles`
- `INSERT`：`NEW.is_system = true` → **RAISE**（运行时/任何应用连接无法创建系统角色）
- `UPDATE` / `DELETE`：`OLD.is_system OR NEW.is_system` → **RAISE**（覆盖三路径：改系统角色、`true→false` 脱保、把自定义角色 `false→true` 提权）
- **0005 顺序配合**：先 seed 系统角色（含初始 `role_permissions`），**后建本 trigger** —— 否则 seed 自身被拦截

| # | 操作 | 结果 | Actor | Condition |
|---|---|---|---|---|
| 1 | 创建 system role（INSERT `is_system=true`） | **DENY** | 应用/API/任何登录用户（含 tenant_admin/space_admin） | trigger：`NEW.is_system` → RAISE |
| 2 | 创建 system role | **ALLOW** | migration revision（人工审计） | 0005：建 trigger 前 seed；后续新系统角色 = 新 revision 临时 DROP trigger → INSERT → 重建 |
| 3 | 修改 system role（key / name / scope / tenant_id / space_id / status / is_system） | **DENY** | 所有人 | trigger 无条件；唯一通道 = 受审计 migration |
| 4 | 删除 system role | **DENY** | 所有人 | trigger +（被引用时）FK RESTRICT |
| 5 | archive / restore system role | **DENY** | 所有人 | status 属受保护列（系统角色恒 active） |
| 6 | 跨 tenant / space 移动 system role | **DENY** | 所有人 | scope/归属列不可改 |
| 7 | 修改 system role 的 permissions（role_permissions 增删改） | **DENY** | 运行时无写入路径（B1-3 无 API）；授权层 default-deny | 变更仅 migration（受审计） |
| 8 | 被 membership 绑定后的 删除 / 改 scope | **DENY** | 所有人 | 同 3/4 |
| 9 | `is_system=true` 是否 = 任何人可用 | **否** | — | 行本身无授权语义；权限只经 `role_permissions` + 绑定；无绑定 → DENY |

防提权要点：① 自定义角色不可被 UPDATE 提升 `is_system`；② 系统角色不可降级/改任何列；③ 运行时不可 INSERT 系统角色；④ 不做"超级管理员万能权限"。

### R2-D-06 — Role Status（R-D-06 保持 FROZEN，补语义定界）

- 枚举 `('active','disabled','archived')`、**默认 `'active'`**；新增绑定仅当被引用 role `status='active'`（绑定 trigger 校验）
- **Role Status ≠ Membership Status**：`roles.status` 与 `tenant_memberships.status` / `memberships.status`（invited/active/suspended/removed）**完全独立、互不隐含**；停用角色**绝不**隐式修改任何 membership 行
- 状态 → 授权（解释层 = Authorization Layer，**fail-closed**；DB 只做枚举 + 绑定校验，不做授权决策）：

| role.status | 可被新绑定 | 既有 membership 行 | 授权效果 | 恢复 |
|---|---|---|---|---|
| active | ✅ | 不变 | 正常参与授权 | — |
| disabled | ❌（引用被拒） | **不变** | **立即 DENY**（视同无角色；不清行） | UPDATE → active（仅自定义角色） |
| archived | ❌ | **不变** | **立即 DENY** | UPDATE → active（仅自定义角色） |

- 删除 vs archive：**DELETE** = 物理删除（仅未被 membership 引用且非系统；FK RESTRICT 拦截）；**archive** = status 变更（行保留、可恢复、**key 仍被占用**）
- 系统角色（is_system）**恒 active**：无法进入 disabled/archived（status 受 R2-D-05 保护）
- 是否阻塞 0005：**否**

### R2-D-07 — Platform Role Binding（R1 结论**撤回** → **NOT RESOLVED（P1）**）

**复核证据（全仓库取证，逐条可查）**：
1. `platform_metadata` **不是冻结 schema 表**：CORE_DOMAIN_MODEL §1.2（29 张核心表）、ER_MODEL、STEP1B_SCHEMA_DEPENDENCY 均无；
2. 它仅存在于 **legacy 自研 runner** `migrations/0001_platform_baseline.sql`（STEP 0 旧体系产物，`CREATE TABLE IF NOT EXISTS platform_metadata`）；
3. Alembic `0001_baseline` 是 **no-op 历史锚点，不创建任何对象** → 纯 Alembic 全新库 `upgrade head` 后 **不存在 platform_metadata**；
4. 正式 `uap` 库 0 表（从未应用任何 runner）→ 全环境无处承载写入。

**正式结论（原样记录本轮审计指令的表述）**：
> "当前 schema 无安全承载点，Platform Binding 必须在后续独立架构决策中解决。"

- 候选方案（**全部需新的人工架构批准**，本轮不选定）：
  - **A.** 新增 `platform_memberships`（或平台级 memberships 结构）+ 相应 FK/trigger/审计 —— 需批准；
  - **B.** 将平台级元数据载体（如 `platform_metadata` 或等价键值表）**正式纳入 Alembic 冻结模型**（新 revision 建表）—— 相对 29 表模型仍是"新增表"，需批准；
  - **C.** 无 DB 绑定（bootstrap 环境/文件 + 应用层校验）—— 不可审计、多实例不一致，**不推荐**。
- D-07 状态：**NOT RESOLVED / OPEN（P1），不伪装已解决**。
- **安全边界（不变，仍然成立）**：无绑定 → DENY；`is_system=true` ≠ 自动授权；Tenant/Space membership 绝不可能产生 PLATFORM 权限（无表可引用 PLATFORM role，trigger 拒绝）；新用户默认无平台角色。
- Migration Impact：**D-07 不阻塞 0005 的 3 表建表、seed、回填、FK**（均不依赖平台绑定）；但**阻塞"B1-3 实施完成"门禁**（平台授权语义未闭环）→ 见 Gate。

### R2-D-08 — Membership Role Backfill（R-D-08 保持 FROZEN，补边界情形）

原则：**migration 不猜测；任何无法确定性推断的数据 → RAISE → 整体 ROLLBACK**。禁止部分成功 / 静默置空 / 乱填 admin。

| 情形 | 处理 |
|---|---|
| 既有 `role_id IS NULL`（常态，B1-2 无 FK、无应用写入） | 回填：TM → 同租户 `tenant_member`；M → 同空间 `space_member` |
| status='removed' / removed_at 非空的历史行 | **仍回填默认角色**（SET NOT NULL 要求每行有值；removed 行无授权效果，回填无风险） |
| archived / deleted 的 tenant / space | seed 对**每个既有行**执行（含非 active）；回填照常 —— 全部须满足 NOT NULL |
| `role_id` 已有值 | 仅当值 = 已存在且 scope/归属/status 匹配的正确角色（等价跳过）时保留；否则 **RAISE** |
| 非法 / 不存在 role_id | FK 建立前由显式校验（SELECT 比对）拦截 → **RAISE**（fail-closed） |
| TM → SPACE role / M → TENANT role | 校验 **RAISE** |
| 跨 tenant / 跨 space role | 校验 **RAISE** |

### R2-D-13 — Role Key Format（R-D-13 保持 FROZEN，复核确认无变化）

`roles.key ~ '^[a-z][a-z0-9_]{1,63}$'`（小写 a–z 开头；后续 a–z/0–9/_；长度 2–64；禁大写、`-`、`.`、空格、Unicode）。5 个系统角色 key 全部合规：`platform_admin`(14) / `tenant_admin`(12) / `tenant_member`(13) / `space_admin`(11) / `space_member`(12)。

### R2-D-14 — DENY > ALLOW（R-D-14 保持 FROZEN，补测试面）

- 语义不变：同一 `(role, permission)` 并存 allow+deny → **最终 DENY**；多个 role 命中时**任一 deny → DENY**。
- 测试用例：仅 ALLOW → ALLOW；仅 DENY → DENY；ALLOW+DENY → **DENY**；多 role 之一 DENY → **DENY**。
- 实现于 **Authorization Layer**；不在 DB trigger 中做授权解释。B1-3 只建数据结构。

### R2-D-15 — Permission Scope-neutral（保持 FROZEN，无变化）

Permission = Capability（不拥有 tenant/space/user/resource 实例边界）；边界来自 Membership + Role Scope + Request Context + Resource ACL。
B1-3 不建 ABAC evaluator；`role_permissions.conditions` 仅 **storage-only**（存不解析、不执行、不让 LLM 决定）。

### R2-D-16 — SPACE Role tenant_id（保持 FROZEN；**标签消歧**）

- 最终语义（以此为准）：**SPACE role 只存 `space_id`（`tenant_id` NULL）**，租户经 `spaces.tenant_id` 间接推导（即 R1 冻结的 "Option A"）。
- **标签消歧**：后续审计提示中"方案 A = 同存 tenant_id+space_id（DB 强制一致）/ 方案 B = 只存 space_id" 的**编号与本仓库相反**；本仓库采用后者语义。凡提及"方案 A/B"一律**以语义为准，不以编号为准**。
- 理由不变：无冗余 → 无需 `tenant_id = spaces.tenant_id` 跨表约束；隔离由 `tg_membership_tenant_consistency` ∧ `tg_membership_role_scope` 传递合取保证（需专项测试）。

### R2-D-12 澄清 — Role Uniqueness 与 archived 语义

- 三条部分唯一谓词（冻结 CORE_DOMAIN_MODEL，**不含 archived 排除**）：
  `uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL`；`uq_roles_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL`；`uq_roles_space ON (space_id, lower(key)) WHERE space_id IS NOT NULL`
- ⇒ **archive 不释放 key**（archived 角色仍占用同 scope/owner 的 key；语义 = 可恢复的停用记录）；**key 复用唯一途径 = DELETE 该自定义角色**（须未被 membership 引用）；系统角色 key 永不复用。
- 断言：同一有效 tenant / space 内同 key 角色 = 0（任意状态）。新增测试：archived 角色仍阻止同 key 创建；restore 后可恢复使用。

### R2 Gate 小结

本轮 FROZEN：**D-05 / D-06 / D-08 / D-13 / D-14 / D-15 / D-16**（含 D-12 澄清）。
本轮 **NOT RESOLVED**：**D-07（P1）** —— 唯一未决项。
→ `B1-3 Decision Resolution = BLOCKED（唯一原因 D-07）`；`B1-3 Implementation = BLOCKED`。

---

## DECISION RESOLUTION ROUND 3 — D-07 Platform Role Binding 独立决策审计（2026-09-08）

> 触发：对 D-07 做独立架构决策审计（Option A/B/C），不预设结论；机械复核唯一谓词与 reserved-key 表述。
> 纪律：仍为只读 + 决策 + 文档同步；**不建表、不 migration、不改代码**。本段决策为**设计冻结**，实施须另经人工批准。

### R3-0 复核产出（本轮机械核查）

**① Role 唯一谓词修正（文档缺陷，已修，未动 DB）**：冻结 CORE_DOMAIN_MODEL 及 5 份衍生文档原写
`uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL`，**缺少 `AND space_id IS NULL`** →
SPACE 行（tenant_id NULL ∧ space_id NOT NULL）会被并入平台命名空间，导致跨空间同名 key 被误拒。
已统一修正为三谓词互斥：
- `uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL`
- `uq_roles_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL`
- `uq_roles_space ON (space_id, lower(key)) WHERE space_id IS NOT NULL`
（受影响的 6 份文档：CORE_DOMAIN_MODEL / STEP1B_CONSTRAINT_MATRIX / STEP1B_B1_3_CONSTRAINT_MATRIX / STEP1B_B1_3_INDEX_STRATEGY / STEP1B_B1_3_SCHEMA_REVIEW / 本 DECISION_LOG R2-D-12）

**② Reserved-key 表述核查（零命中）**：全仓库扫描"Tenant Role 不能使用 System Role 的 key"类表述 =
**0 条** → 无错误表述需修。**语义澄清**（写入文档）：scope-scoped 唯一性只约束**同 scope + 同 owner 命名空间**内 key 不重复；跨 scope/owner 允许同名（如某租户自定义角色可用 `platform_admin` 作为其 TENANT scope key，不与 PLATFORM 的 `platform_admin` 冲突）——**不存在全局 reserved-key 约束**；同租户/同空间内与已存在的系统角色同 key 由唯一索引天然拒绝（非 reserved 语义，是唯一性）。

### R3-1 决策矩阵（Option A / B / C）

| 方案 | Security | Audit | Multi Admin | Revocation | Multi-node | Extensibility | Complexity | Final |
|---|---|---|---|---|---|---|---|---|
| **A：新增 `platform_memberships`** | **高**：FK+trigger 强引用；scope 校验同既有 membership 模式；提权面=仅平台管理员写路径 | **高**：行级历史 + audit_logs 独立 action | **高**：N 用户各持 PLATFORM role | **强**：status='revoked' 即时失效；FK/trigger 原子 | **高**：DB 单一事实源 | **高**：未来平台角色直接可绑 | 中（1 新表 + 2 trigger + 顺序在 roles 后） | ✅ **最优** |
| B：纳入既有模型（改 users 加平台标记/jsonb 或复用 TM/M） | 中/低：users 承载授权列违背 identity/auth 分离；无 FK 到 role；提权/伪造面大 | 低：列变更无独立审计轨迹 | 弱（布尔难多角色） | 弱 | 中 | 低 | 低（但污染冻结 users） | ❌ 拒绝 |
| C：配置/环境变量维护 Platform Admin | 低：配置泄露/漂移；无 FK、无身份绑定校验 | 低：无审计 | 弱 | 弱（部署级） | 低（多实例不一致） | 低 | 低 | ❌ 拒绝 |

**理由要点**：A 与 Tenant/Space Membership 同构（role_id+status+FK trigger 模式），Role Scope 模型一致性最高；默认 deny 与防提权均可由 trigger+授权层双层落地。B/C 无法满足"可审计、可撤销、多管理员、多节点一致"中的任意三项。**采用 A。**

### R3-2 — D-07 FINAL DECISION（**FROZEN — Option A**，实施待人工批准）

> 新增实体 `platform_memberships` —— **PLATFORM scope 角色（当前仅 `platform_admin`）的专用绑定表**；
> 不改变 roles/permissions/role_permissions 结构；Role Scope 三态模型不变。

**Canonical Schema**（字段级；PK/UUID 策略 = `uuid DEFAULT uap_uuid_v7()`）

| 字段 | 类型/约束 | 说明 |
|---|---|---|
| id | uuid PK DEFAULT uap_uuid_v7() | |
| user_id | uuid NOT NULL → users.id **ON DELETE CASCADE** | 绑定用户 |
| role_id | uuid NOT NULL → roles.id **ON DELETE RESTRICT** | 仅 PLATFORM scope 且 active |
| status | text NOT NULL DEFAULT 'active' | CK `('active','revoked')` |
| revoked_at | timestamptz NULL | 撤销时间（历史行） |
| created_at / updated_at | timestamptz NOT NULL DEFAULT now() | updated_at 由 `set_updated_at()` trigger 维护 |

**Unique**
- `uq_platform_memberships_user_role ON (user_id, role_id)`（非部分：每 user+role 仅一条历史，撤销后重授 = UPDATE 回 active）
- `uq_platform_memberships_active_user ON (user_id) WHERE status='active'`（**一用户至多一个 active 平台绑定**）
- `ix_platform_memberships_role_status ON (role_id, status) WHERE status='active'`（持有者查询 / last-admin 计数）

**FK / status / authorization**
- `user_id → users.id CASCADE`（users 硬删清理绑定；正常路径 = 软删，先 revoke）；绑定 active 要求 `users.status='active'`
- `role_id → roles.id RESTRICT`（被引用的 PLATFORM role 不可删；is_system 本身禁删）
- `status`：`active` = 生效（授权查询只读 active 行）；`revoked` = 历史保留、授权立即忽略（**即时失效，无缓存默认**）

**Trigger（roles 表建立后随表创建；与 0005 顺序解耦，可随 0005 或后续 revision）**
- `tg_pm_role_scope`（BEFORE INSERT OR UPDATE OF role_id, status）：引用角色必须存在且 `scope='PLATFORM' AND status='active'`（PLATFORM shape 由 `tg_roles_scope_shape` 保证 tenant/space 均 NULL）；结果态 active 时 `users.status='active'` —— 任一不满足 → RAISE → 回滚
- `tg_pm_last_admin`（BEFORE UPDATE/DELETE）：若变更将导致 **active `platform_admin` 绑定数从 >0 变为 0** → RAISE（禁止撤销/删除最后一名平台管理员）；首行 bootstrap（0→1）允许

**Grant / Revoke / Audit（actor 规则）**
- **grant**：① 初始 = 安装 bootstrap（受控 CLI/seed，actor='system'）；② 后续 = 任一 **active platform_admin**（授权层校验其权限）；目标 user 存在且 active、role PLATFORM 且 active。每次写 `audit_logs(action='platform.admin.grant')`（actor/user/role/result/timestamp）
- **revoke / transfer**：任一 active platform_admin（含本人；本人撤销前须先完成转让或确保仍有其他 admin）；**last-admin 例外 DENY**（R3-2 约束）。写 `audit_logs(action='platform.admin.revoke'/'platform.admin.transfer')`
- **默认 deny**：无 active 绑定 → 无任何平台权限；`is_system=true` 不隐含授权（行本身零权限）
- tenant/space 侧无任何 grant/revoke 路径（无 API/表可写 platform_memberships，授权层 default-deny）

**18 问逐项冻结**（规则而非散文）
1. 一个 User 多个 Platform Role？**否**（`uq_platform_memberships_active_user`：至多 1 个 active；与 tenant_memberships 单角色模型一致）
2. 多个 Platform Admin？**是**（N 用户各持 1 条 active 绑定；仅受 last-admin 约束）
3. `user_id` 约束？NOT NULL FK → users；绑定/生效需 `users.status='active'`（trigger + 授权层）
4. `role_id` 约束？NOT NULL FK → roles RESTRICT；trigger 校验 scope='PLATFORM' 且 role active
5. 如何保证 scope=PLATFORM？`tg_pm_role_scope` join roles 校验；shape 由 roles 上 `tg_roles_scope_shape` 保证
6. status？`('active','revoked')`，默认 active；active=生效、revoked=历史忽略
7. revoke 后如何立即失效？status→revoked（授权查询条件 `status='active'` 即时排除；应用层不默认缓存）
8. 谁可 grant？bootstrap（首行）+ active platform_admin（后续）
9. 谁可 revoke？active platform_admin（受 last-admin 约束）
10. 最后一名 Platform Admin 可否删除/撤销？**否**（`tg_pm_last_admin` DENY；须先授/转让）
11. system role 与 platform membership 关系？membership.role_id 可指向任何 PLATFORM role；system role 保护（R2-D-05）不变
12. `is_system=true` 是否自动获得 PLATFORM 权限？**绝不**（须 active platform_memberships 行 + role_permissions）
13. 独立 audit？是（`platform.*` action 前缀；grant/revoke/transfer 全记录）
14. 删除 FK？user → CASCADE；role → RESTRICT
15. 防重复 active binding 唯一？是（partial unique active user）
16. 历史/revoked binding 保留？是（revoked 行保留；重授 = UPDATE 回 active）
17. Tenant/Space membership 产生 PLATFORM 权限？**绝无路径**（tg_tm_role_scope / tg_membership_role_scope 拒 PLATFORM；唯一来源 = platform_memberships）
18. Role Scope 三态是否仍成立？**成立**（roles 不变；platform_memberships 为 PLATFORM scope 的唯一消费者；shape trigger 不变）

**Threat model（已封堵路径）**
- 应用无法 INSERT is_system=true role（R2-D-05）→ 无法伪造系统角色
- TM/M 无法绑定 PLATFORM role（scope trigger）→ tenant/space 无法横向提权到平台层
- platform_memberships 仅平台管理员可达（授权层 default deny；B1-3 无 API）
- roles shape trigger 杜绝 PLATFORM/TENANT/SPACE 畸形混用
- last-admin trigger 防平台自锁；撤销/重授原子（单事务）

**Failure behavior**
- DB 不可用 → 授权 fail-closed（DENY）
- 任一写入条件不满足 → trigger RAISE → 无半状态
- bootstrap 未执行前无绑定 → 全部平台操作 DENY（部署顺序要求：先 bootstrap 首管理员）

**Migration impact（记录，不实施）**
- 新表依赖 users（B1-1）+ roles（0005）；阶段置于 roles 之后（0005 尾部或独立 0006）；无回填（全新表）；downgrade = DROP 表 + 2 trigger；首行 admin 由部署 bootstrap 写入（非 migration 内置用户 uuid）
- 需更新：CORE_DOMAIN_MODEL / ER_MODEL / CONSTRAINT_MATRIX / TRIGGER_INVENTORY / SCHEMA_DEPENDENCY / SEED_STRATEGY / TEST_MATRIX / GATE_REPORT（本段已记录，文档同步见 R3-3）

### R3-3 — Role Scope 三态互不越权证明（机械验证）

| Scope | tenant_id | space_id | 可被谁引用 | 唯一谓词（互斥） |
|---|---|---|---|---|
| PLATFORM | NULL | NULL | `platform_memberships.role_id`（唯一） | `t IS NULL AND s IS NULL` |
| TENANT | NOT NULL | NULL | `tenant_memberships.role_id` | `t IS NOT NULL AND s IS NULL` |
| SPACE | NULL | NOT NULL | `memberships.role_id` | `s IS NOT NULL` |

- 谓词两两不相交（t/s 值域分区）→ 同一 key 在不同 scope 各可独立存在
- 引用面两两互斥：PM 只接 PLATFORM、TM 只接 TENANT、M 只接 SPACE（三个 scope trigger）
- ⇒ 不存在"某角色行可同时被两类 membership 引用"或"shape 畸形行落入两个命名空间"的路径

**R3 Gate 小结**：D-07 六项（Security / Data Model / Authorization / Lifecycle / Audit / Multi-Admin）全部明确 → **FROZEN（Option A，设计冻结；实施等待人工批准，platform_memberships 未创建、0005 未创建）**。
本段另产出：唯一谓词文档修正（R3-0①）+ reserved-key 语义澄清（R3-0②）。

---

## DECISION RESOLUTION ROUND 4 — D-07 Hardening（2026-09-08：Last-Admin×Role Lifecycle / Bootstrap / Re-grant / User Lifecycle）

> 触发：修复"Last Admin 与 Role Lifecycle 联动"P1，并冻结 Bootstrap Trust Root / Grant-Revoke-Re-grant / User Lifecycle。
> 纪律：纯决策 + 文档 + 只读验证；**不建表、不 migration、不改代码**。

### R4-0 关键事实（前置分析）

**system `platform_admin` 行已被 R2-D-05 冻结为运行时不可变**（`tg_roles_is_system_protect` 无条件拒绝 UPDATE/DELETE）：
- ⇒ "platform_admin role 被 disabled/archived → 全体管理员失效"在**运行时无合法路径**可达（唯一路径 = 受审计 migration 临时撤保护后修改）。
- 但该保证**依赖单一 trigger 的持续存在**；且未来若放开系统角色不可变性，缺口即现。
- ⇒ 需把"至少一名有效平台管理员"固化为**显式不变量**，并加 **role 侧纵深防线**（双 trigger 分层），使该保证不再单点依赖。

### R4-1 — PMB-1：Last Admin × Role Lifecycle 联动（FROZEN）

**方案比较**：
- **Option A**（存在 active 绑定即禁止 role `active→disabled/archived`）：机制直白，但前提隐含"role 当前 active"，语义不自洽（role 已非 active 时无法用"存在绑定"推导），且只拦 status 不拦其它破坏路径。
- **Option B**（定义 effective 谓词并要求计数 ≥1）：语义完整，但单独作为"事后检查"缺少前置拦截。

**冻结 = Option B 语义 + Option A 机制（双 trigger 分层）**。理由：二者互补 —— B 给出**可判定谓词**，A 给出**前置拦截**；组合为全量不变量。

**有效平台管理员谓词（canonical，本仓库唯一权威定义）**：
```
effective_platform_admin(user)
 := pm.status='active'
 AND u.status='active'            -- user 有效
 AND r.status='active'            -- role 有效
 AND r.scope='PLATFORM'
 AND r.key='platform_admin'
```

**不变量 PMB-1（Platform Admin Trust Root）**：信任根初始化后，任意时刻 `effective_platform_admin_count >= 1`。
**分层强制**：
| 层 | 机制 | 拦截 |
|---|---|---|
| PM 侧 | `tg_pm_last_admin`（BEFORE UPDATE/DELETE ON platform_memberships） | 撤销/删除使 active `platform_admin` 绑定数 >0→0；首行 bootstrap 0→1 放行 |
| Role 侧（本轮新增） | `tg_roles_pm_lifecycle`（BEFORE UPDATE OF status ON roles；DELETE 兜底） | `platform_admin` 行（scope='PLATFORM' ∧ key='platform_admin'）在**存在 active 绑定引用**时不得 `active→非active`；DELETE 同 |
| 授权层 | 每次授权按 effective 谓词计算 | 任何 user/role/PM 状态变化后计数为 0 的请求 → DENY（fail-closed） |

> 说明：role 侧防线与 R2-D-05 is_system 保护**重叠但不同质** —— is_system 保护系统角色不可变；PMB-1 保护"信任根不失效"。即使未来经受审计 migration 开放系统角色生命周期，PMB-1 仍要求保留至少 1 名 effective admin（migration 顺序必须满足）。

**测试面**：role `active→disabled`（有 active 绑定）→ 拒绝；role DELETE（有 active 绑定）→ 拒绝；撤掉绑定后再停用角色 → 允许；system role 停用 → 仍被 R2-D-05 拒绝。

### R4-2 — PMB-2：Bootstrap Trust Root（FROZEN）

| # | 规则 |
|---|---|
| 1 | **Bootstrap 条件**：~~`platform_memberships` 行数 = 0（= 未初始化；last-admin 不变量保证初始化后恒 ≥1 行 → 行数=0 ⟺ 未初始化，可判定，无需状态表）~~ → **R5 修正：改显式 `platform_state` 单例行（uninitialized/initialized 单向状态机）**。行数=0 仍作为服务层前置校验之一，但**不再是唯一/权威判据**（见 R5-1） |
| 2 | **仅一次**：首次成功后行数 >0 → 条件永久不成立 → bootstrap path 永久关闭 |
| 3 | **普通 API 不能伪造 actor='system'**：actor 一律由授权层从**认证会话**派生，客户端不得提供；`'system'` 仅供受信 bootstrap 进程（专用 CLI/service，带独立凭据）使用；任何请求体携带 actor 字段 → 校验拒绝；审计写入不可变 `audit_logs` |
| 4 | **独立 audit**：首行写入与 `audit_logs(action='platform.admin.bootstrap', actor='system', target=首管理员, result=success)` **同事务** |
| 5 | **永久关闭**：同 2（由不变量保证，非软性约定） |
| 6 | **丢失恢复**：运行时**不可达**（PMB-1 保证 ≥1）。如因灾难/误操作确需恢复 → **独立机制**：维护/迁移专用程序（非业务 API），须人工批准、应用停写（maintenance），临时撤 PMB-1 防线 → 写入 → 重建防线 → 写 `audit_logs(action='platform.admin.recovery')`。默认无恢复 API |
| 7 | 首行管理员 user 必须已存在且 `status='active'`（trigger 校验同一般绑定） |

### R4-3 — PMB-3：Grant / Revoke / Re-grant 生命周期（FROZEN）

- **单行模型**（`UNIQUE(user_id, role_id)` 非部分）：同一 (user, role) 永远一条历史记录。
- **grant**：无行 → `INSERT (status='active')`；有行且 `revoked` → **`UPDATE status='active', revoked_at=NULL`**（re-grant），**禁止 INSERT 新行**；有行且已 active → **拒绝**（应用层显式错误；直接 INSERT 由 UQ 兜底 IntegrityError）。
- **revoke**：`UPDATE status='revoked', revoked_at=now()`（受 PMB-1 约束）；行与 `created_at`（首次授予时间）保留。
- **历史保留**：revoked 行不删除；`created_at` 不因 re-grant 改变；`updated_at`/`revoked_at` 记录最近操作。
- 状态机：`active → revoked`（revoke）；`revoked → active`（re-grant）；同态转换拒绝。
- 写入 CONSTRAINT_MATRIX / ACL_STRATEGY / SCHEMA_REVIEW / TEST_MATRIX / 本 LOG。
- **测试面**：revoke→re-grant 同 id 行 UPDATE（PM6 强化）；duplicate grant（active 时再 INSERT）→ UQ 拒绝；历史保留断言（created_at 不变、revoked_at 置位/清除）。

### R4-4 — PMB-4：User Lifecycle × PMB（FROZEN）

| 生命周期 | 行为 | 机制 |
|---|---|---|
| **正常撤销路径（软删 / 停用）** | 应用工作流**先 revoke active PM 行（PMB-1 校验）→ 再停用 user**；两动作各自审计 | 应用层顺序强制；**DB 无 users→PM 自动 revoke trigger**（避免与 PMB-1 冲突的隐式级联） |
| 最后一名管理员停用 | 工作流**拒绝**（PMB-1）：须先 transfer/新授 | 授权层 + PMB-1 |
| **授权效果** | user 非 active → effective=0（见谓词），即使 PM 行仍 active 也 **DENY**（fail-closed 兜底） | 授权层按 effective 谓词计算 |
| **hard delete（purge 终态）** | FK `user_id → users.id ON DELETE CASCADE` 清理 PM 行 | 仅终态清理；**绝不作为正常撤销机制**（正常撤销 = 上述 revoke 工作流） |
| 关系结论 | soft-delete ≠ hard-delete：前者行保留 + 授权失效（须先 revoke）；后者行级联清除（purge 后） | — |

**测试面**：停用最后 admin → 拒绝；停用非最后 admin → revoke 后停用成功；user 非 active 但 PM 行 active → 授权 DENY；hard delete user → PM 行 CASCADE（且仅 purge 场景）。

### R4-5 — Platform Scope / 唯一谓词 / Reserved Key（复核确认）

- **Scope 映射（无合法交叉状态）**：PLATFORM→仅 `platform_memberships`；TENANT→仅 `tenant_memberships`；SPACE→仅 `memberships`。TM/M→PLATFORM role 或 PM→TENANT/SPACE role 均被对应 trigger 拒绝；shape 由 `tg_roles_scope_shape` 保证 → 不存在合法 DB 状态使 TM/M 绑定 PLATFORM role。
- **唯一谓词（终版，全文档统一）**：PLATFORM `WHERE tenant_id IS NULL AND space_id IS NULL`；TENANT `WHERE tenant_id IS NOT NULL AND space_id IS NULL`；SPACE `WHERE space_id IS NOT NULL`（R3 已修正，R4 复核无回归）。**禁止**旧版 `WHERE tenant_id IS NULL` 单条件作为 PLATFORM 谓词。
- **Reserved Key**：重申 **无全局保留字约束**；唯一性 = scope+owner 命名空间。Tenant Role 与 Platform/System Role 可跨 scope 同名（如租户自定义 `platform_admin` 属 TENANT 命名空间，不与 PLATFORM 冲突）。不新增任何 reserved-key 规则。

### R4 Gate 小结

D-05 / D-06 / D-07 / D-08 / D-13 / D-14 / D-15 / D-16 全部 **FROZEN**；
**PMB-1（Last Admin×Role Lifecycle）· PMB-2（Bootstrap）· PMB-3（Re-grant）· PMB-4（User Lifecycle）· Role Scope · 文档一致性 全部 CLOSED**。
→ `D-07 FINAL ARCHITECTURE = APPROVED（设计层）`；`B1-3 IMPLEMENTATION = BLOCKED（等待人工批准实施）`。

---

## DECISION RESOLUTION ROUND 5 — HARDENING：Bootstrap Permanent Closure & User Lifecycle（2026-09-08）

> 触发：审计指出两个 P1 生命周期问题。主体架构（4 表 + D-05..D-16）**不改**；仅补强 bootstrap 状态机与 user-lifecycle 契约。
> ⚠️ **取代说明**：R4 PMB-2 曾以"PM row count=0 ⟺ 未初始化（无需状态表）"作为 bootstrap 条件。
> R5 裁定该可派生判据**不足够**（其成立依赖 last-admin trigger 持续存在；形态上允许 count 派生回 0 的讨论），
> 改为**显式、独立、不可重置的初始化状态** —— 审计要求 1–10 全部落实于下。

### R5-1 — PMB-2（修正）Bootstrap Permanent Closure（FROZEN）

**设计（新增 schema 的理由已说明，见 migration `0006_b1_3_bootstrap_state` docstring）**：

| 项 | 结论 |
|---|---|
| 1 状态载体 | 单例表 `platform_state`（`id smallint PK =1`，CK `id=1`；`bootstrap_state CK('uninitialized','initialized')` 默认 `uninitialized`；`initialized_at NULL`；created/updated_at）。**独立于 platform_memberships**：无任何 FK 依赖 PM/users |
| 2 状态机 | 仅 `UNINITIALIZED → INITIALIZED` 单向（`tg_platform_state_guard`）；DELETE 拒绝；二次 INSERT 拒绝（单例行已存在）；UPDATE 仅允许上述单向转换且 `initialized_at` 非空 |
| 3 永久保持 | INITIALIZED 后任何 PM lifecycle（revoke/UPDATE/DELETE）、users 硬删 CASCADE 均**无法**触碰 platform_state（无引用边 + guard）→ 不可重置 |
| 4 count=0 不再重开 bootstrap | PM 写入门 `tg_pm_bootstrap_gate`：INSERT 仅当 `state='initialized'` **或**（`state='uninitialized'` 且 PM 无行）→ 初始化后不存在"uninitialized+empty"分支；state 亦不可回退 |
| 5 硬删/CASCADE 不重置 state | 已由 B-04/B-05/U-05 测试证明（state 与 PM 无 FK、无自动连带） |
| 6 普通 API 不可伪造 state | state 变更仅经 guard 允许的单向转换；表无 actor 列可伪造；客户端 payload `actor` 字段无承载列（B-06） |
| 7 审计 | bootstrap 事务 = 首行 PM + state 翻转 + `audit_logs(action='platform.admin.bootstrap')`（audit 表就绪后同事务写入；当前记录契约 + `initialized_at`） |
| 8 不引入 legacy `platform_metadata` | ✅（新表为 `platform_state`，无任何 legacy 依赖） |
| 9 新 schema 说明 | 见上表 + 0006 docstring（独立性/单向性/无业务 FK 三大理由） |
| 10 不实现 recovery API | ✅（恢复 = 独立维护程序 + 人工批准 + audit，见 PMB-2/R4；不建任何 HTTP/Socket 接口） |

**Bootstrap 原子流程（服务层契约）**：`BEGIN` → 校验 `state='uninitialized' AND PM 无行` → INSERT 首行 PM → `UPDATE platform_state SET bootstrap_state='initialized', initialized_at=now()` → audit → `COMMIT`。第二次执行因 state='initialized' 必然失败（B-02）。

### R5-2 — PMB-4（补强）User Lifecycle 正式 Workflow（FROZEN）

**三分层职责（不得混淆，逐一落实与测试）**：

| 层 | 职责 | 实现/验证 |
|---|---|---|
| **DB trigger** | **无** users→PM 自动 revoke（B/U 系列验证：停用 user 时 PM 行保持原状态） | `test_pm_user_deactivation_does_not_auto_revoke`（R4）+ U-04 |
| **Application Service** | **显式 revoke-first workflow**：deactivate(user) = { revoke 该 user 的 active PM（PMB-1 校验）→ deactivate user } **单事务**；任一步失败 → 整体回滚（U-03）；reactivate(user) **不**恢复 PM（U-02） | U-01/U-02/U-03 |
| **Effective Authorization** | effective 谓词不变；user inactive → 永久 DENY（fail-closed 防线，**不是** revoke 的替代品） | U-04 + `_effective` 纯函数测试 |

失败路径验证：`revoke 成功 → user 停用失败 → 事务回滚` → 断言 PM 仍 active 且 user 仍 active（无半状态，U-03）。

### R5-3 — P1-03 Hard Delete（验证定论，无 schema 变更）

- users hard delete → PM CASCADE 生效（U-05）；**仅 purge/final lifecycle 路径**，正常撤销必须走 R5-2 revoke-first workflow（不依赖 CASCADE）
- **last-admin 保护不被 CASCADE 绕过**：级联 DELETE 触发行级 BEFORE trigger → 最后一名管理员 user 硬删被拒（U-06/B-05）；实测 + 测试双覆盖
- Bootstrap state 不受 CASCADE 影响（U-05/B-04/B-05）

### R5-4 — P1-04 冻结语义复核（无修改）

DENY>ALLOW / Permission=scope-neutral / conditions=storage-only / is_system≠自动授权 / 跨 scope 绑定禁止 —— **全部保持不变**，本轮未触碰（回归套件覆盖）。

### R5 Gate

Bootstrap permanently closed = **PROVEN**（B-01..B-06 + 单向状态机）· User reactivation cannot restore revoked PM = **PROVEN**（U-02）·
Last-admin protection under hard delete = **PROVEN**（U-06/B-05）· No legacy platform_metadata dependency = **PROVEN**（B-06 + schema 无该表）。
→ `B1-3 HARDENING = READY FOR FINAL HUMAN AUDIT`；B1-4 仍 BLOCKED。

---

## 汇总（Resolution 后）

| ID | 主题 | Status |
|---|---|---|
| D-01 | roles.description | OPEN（默认不加；**不阻塞 0005**） |
| D-02 | permissions.name / status | OPEN（默认不加；**不阻塞 0005**） |
| D-03 | Permission scope-neutral | FROZEN |
| D-04 | role_permissions PK 含 effect | FROZEN |
| D-05 | System Role Protection | **FROZEN（R-D-05）** |
| D-06 | roles.status 枚举 | **FROZEN（R-D-06：active/disabled/archived）** |
| D-07 | Platform role 绑定模型 | **FROZEN — FINAL（R3 Option A `platform_memberships` + R4 Hardening：PMB-1 Last-Admin×Role / PMB-2 Bootstrap / PMB-3 Re-grant / PMB-4 User Lifecycle 全 CLOSED；实施待人工批准）** |
| D-08 | role_id NULL → NOT NULL + 回填 | **FROZEN（R-D-08 完整流程）** |
| D-09 | Role/Permission 删除语义 | FROZEN |
| D-10 | Default role = 系统内置 + seed | FROZEN |
| D-11 | Scope enforcement = Trigger + 应用层 | FROZEN |
| D-12 | role key 唯一性 = scope-scoped | FROZEN |
| D-13 | roles.key 格式 CK | **FROZEN（R-D-13：`^[a-z][a-z0-9_]{1,63}$`）** |
| D-14 | DENY > ALLOW | **FROZEN（R-D-14 SECURITY INVARIANT）** |
| D-15 | Permission scope-neutral | **FROZEN（R-D-15）** |
| D-16 | SPACE Role 保存 tenant_id | **FROZEN（R-D-16：Option A，不冗余）** |
