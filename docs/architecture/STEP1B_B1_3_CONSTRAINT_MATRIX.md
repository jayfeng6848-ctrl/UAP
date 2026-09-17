# STEP 1-B / B1-3 — Constraint Matrix（Role & Permission Foundation）

Status: **PREP ONLY**
每个约束记录：**目的 / 风险 / 测试方法**。
来源：`CORE_DOMAIN_MODEL.md` §1.2 + B0 `STEP1B_CONSTRAINT_MATRIX.md` §2 + B1-2 `DECISION_LOG.md`

---

## 1. `roles`

| 约束 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| PK | `id uuid NOT NULL DEFAULT uap_uuid_v7()` | UUIDv7 主键 | 时钟回拨导致顺序退化（P3） | pg_attribute/pg_attrdef 断言 + UUIDv7 属性测试 |
| FK `tenant_id` | `→ tenants.id ON DELETE CASCADE`（NULL 允许） | 租户级角色随租户受控清理（配置行白名单） | 租户 purge 时静默删除自定义角色 | delete_rule 断言；删租户后角色行清 0 |
| FK `space_id` | `→ spaces.id ON DELETE CASCADE`（NULL 允许） | 空间级角色随空间清理 | 同上 | delete_rule 断言 |
| UQ `uq_roles_platform` | `UNIQUE (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL` | 平台角色 key 唯一（仅 PLATFORM 形状：tenant 与 space 均 NULL） | 谓词必须互斥（已含 space_id 条件，防止 SPACE 行并入平台命名空间） | 重复 key 插入被拒（平台层）；跨 space 同名角色不受影响 |
| UQ `uq_roles_tenant` | `UNIQUE (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL` | 租户内角色 key 唯一 | 谓词写错会导致跨 scope 冲突 | 同租户重复 key 被拒；不同租户同名 key 允许 |
| UQ `uq_roles_space` | `UNIQUE (space_id, lower(key)) WHERE space_id IS NOT NULL` | 空间内角色 key 唯一 | 同上 | 同空间重复 key 被拒 |
| CK `ck_roles_scope` | `scope IN ('PLATFORM','TENANT','SPACE')` | 作用域枚举 | 无 | 非法 scope 插入被拒 |
| CK `ck_roles_status`（R-D-06） | `status IN ('active','disabled','archived')` | 角色生命周期 | disabled/archived 语义需授权层 fail-closed 解释 | 非法 status 被拒；绑定需 active |
| CK `ck_roles_key`（R-D-13） | `key ~ '^[a-z][a-z0-9_]{1,63}$'` | 命名空间（小写开头，禁 - . 空格） | 无 | 非法 key（大写/连字符/点）被拒；5 个系统角色全部合法 |
| TRIGGER `tg_roles_scope_shape`（R-D-16） | PLATFORM→tenant/space 均 NULL；TENANT→tenant 非空 space NULL；**SPACE→tenant NULL space 非空** | 防止畸形 scope 形状（SPACE 不冗余 tenant） | trigger 缺失 → 畸形数据入库 | 三 scope 各验证合法/非法组合 |
| TRIGGER `tg_roles_is_system_protect`（R2-D-05） | **BEFORE INSERT OR UPDATE OR DELETE**：INSERT 时 `NEW.is_system` → 拒绝；UPDATE/DELETE 时 `OLD.is_system OR NEW.is_system` → 拒绝（无条件；含改 key/scope/归属/is_system/name/status、`true→false` 脱保、`false→true` 提权） | 系统角色生命周期保护（防提权/误改/伪造） | 系统角色演进只能走新 migration revision（人工审计）；0005 需**先 seed 后建本 trigger** | INSERT is_system=true / UPDATE 系统角色 / UPDATE 自定义角色→is_system=true / DELETE 系统角色 —— 全被拒 |
| NOT NULL | id, key, name, scope, is_system, status, created_at, updated_at | 必备字段 | — | information_schema 断言 |
| NULL | tenant_id, space_id, archived_at | 可选归属/归档 | — | information_schema 断言 |
| DEFAULT | `created_at/updated_at = now()`；`is_system = false`；`status = 'active'`（R2-D-06） | 时间/默认值/状态初值 | — | column_default 断言 |
| ON UPDATE | `NO ACTION` | PK/FK 不更新 | — | delete/update rule 断言 |
| 软删 | `archived_at` + `status`（冻结未给 status 枚举 → D-06） | 归档而非删除 | status 语义未冻结 | 见 D-06 |

## 2. `permissions`

| 约束 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| PK | `id uuid NOT NULL DEFAULT uap_uuid_v7()` | 主键 | 同 roles | 断言 |
| UQ `uq_permissions_key` | `UNIQUE (key)`（**全局唯一**） | 权限字典 key 唯一 | 与"平台级字典"定位一致；多租户不得重定义同名权限 | 重复 key 插入被拒 |
| CK `ck_permissions_key` | `key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$'` | key 格式（`user.read` 形态） | 无 | 非法 key 被拒 |
| NOT NULL | id, key, action, is_system, created_at（`description` NN? 见 D-02） | 必备字段 | description 空值语义 | 断言 |
| NULL | resource_type | 全局动作权限可无 resource_type | — | 断言 |
| **无 FK** | — | 平台字典，无租户维度 | 若未来需要租户自定义权限需新表 | 断言 pg_constraint 无 FK |
| **无 updated_at** | 冻结无该列 | 字典稳定 | 修改 description 无时间戳 | 断言列不存在 |

## 3. `role_permissions`

| 约束 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| PK | **`(role_id, permission_id, effect)`** | 冻结设计；允许同 (role,permission) 的 allow/deny 两行 | **同一 (role,permission) 可能同时存在 allow 与 deny** → 必须靠应用层"deny 优先"，否则语义不确定（D-04） | 插入两行（allow+deny）成功；第三行重复 effect 被拒 |
| FK `role_id` | `→ roles.id ON DELETE CASCADE` | 角色删除时清理绑定 | 与 membership RESTRICT 并存：被引用角色先被 RESTRICT 拦住，未被引用时才 CASCADE | delete_rule 断言；删未引用角色 → 绑定行清 0 |
| FK `permission_id` | `→ permissions.id ON DELETE CASCADE` | 权限删除时清理绑定 | 误删权限会静默移除所有角色上的该权限（需审计） | delete_rule 断言 |
| CK `ck_role_permissions_effect` | `effect IN ('allow','deny')` | 效果枚举 | 无 | 非法 effect 被拒 |
| NOT NULL | role_id, permission_id, effect, created_at | 必备 | — | 断言 |
| NULL | conditions | ABAC 条件可选 | 条件求值在应用层（本阶段不实现） | 断言 |

## 4. B1-3 补充的既有表约束（**修改既有表，需审计确认**）

| 约束 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| `fk_tm_role` | `tenant_memberships.role_id → roles.id ON DELETE RESTRICT` | 角色引用完整性 | 角色被引用时不可删 | delete_rule 断言；删被引用角色被拒 |
| `fk_membership_role` | `memberships.role_id → roles.id ON DELETE RESTRICT` | 同上 | 同上 | 同上 |
| `role_id NOT NULL` | 回填后 `SET NOT NULL` | 禁止无角色成员 | 回填失败会阻塞 migration（**有意为之**） | NULL 插入被拒；回填后无 NULL 行 |
| `tg_tm_role_scope` | 引用角色必须 `scope='TENANT' AND roles.tenant_id = 本行 tenant_id AND roles.status='active'` | 防止 TM 绑定 SPACE/PLATFORM/异租户/停用角色 | trigger 抛 ProgrammingError（非 IntegrityError） | 5 类非法绑定被拒（含 disabled role） |
| `tg_membership_role_scope` | 引用角色必须 `scope='SPACE' AND roles.space_id = 本行 space_id AND roles.status='active'` | 同上（SPACE role 不存 tenant_id，R-D-16） | 同上 | 5 类非法绑定被拒 |

## 5. Scope Integrity 汇总（安全矩阵落地）

| 场景 | DB 结果 |
|---|---|
| `tenant_memberships` + TENANT role（同租户、`status='active'`） | **PASS** |
| `tenant_memberships` + SPACE role | **DENY**（trigger） |
| `tenant_memberships` + PLATFORM role | **DENY**（trigger） |
| `tenant_memberships` + 其它租户 TENANT role | **DENY**（trigger，tenant_id 不匹配） |
| `tenant_memberships` + disabled/archived role | **DENY**（trigger，非 active） |
| `memberships` + SPACE role（同空间、active） | **PASS** |
| `memberships` + TENANT role | **DENY**（trigger） |
| `memberships` + PLATFORM role | **DENY**（trigger） |
| 不存在的 role | **DENY**（FK violation） |
| 未知 scope 值 | **DENY**（CK `ck_roles_scope`） |

## 6. System Role Protection

| 项 | 冻结状态 |
|---|---|
| 是否允许删除 `is_system=true` 角色 | **否**（trigger） |
| 是否允许修改（key/scope/归属/is_system/name/status） | **否**（`tg_roles_is_system_protect` 无条件拒绝 UPDATE，R-D-05） |
| 谁可以修改 | **仅新 migration revision（人工审计）**（R-D-05）：临时 drop 保护 trigger → 变更 → 重建 |
| 修改 permissions 绑定 | DB 层不设 trigger；保护 = B1-3 无写入路径（权限变更 = 新 migration revision） |
| Tenant 自定义角色区分 | `is_system=false`（不受保护 trigger 约束） |

## 7. Default Deny 原则（B1-3 授权基础）

```
Role 不存在            → DENY
Permission 不存在      → DENY
Role Scope 不匹配      → DENY
Membership 不存在      → DENY
role_permission 不存在 → DENY
NULL role              → DENY（禁止"NULL → 管理员"）
未知 role              → DENY（禁止"未知 → member"）
未知 permission        → DENY（禁止"未知 → 允许"）
```

## 8. PROPOSED / OPEN（不实施）

| 项 | 状态 |
|---|---|
| `roles.description` 字段 | **OPEN D-01**（冻结无；默认不加；**不阻塞 0005**） |
| `permissions.name` / `scope` / `status` | **OPEN D-02**（冻结无；默认不加；不阻塞 0005） |
| `role_permissions` 改 `UNIQUE(role_id, permission_id)` | 不采纳（D-04 FROZEN：保留含 effect 复合 PK；**DENY>ALLOW 由授权层解释 R-D-14**） |
| `roles.status` 枚举 / key 格式 / system 保护 / platform 绑定 / SPACE tenant | **已 FROZEN**（R-D-05/06/07/13/16） |
| Permission 审计/版本 | PROPOSED（不在本阶段） |

---

## platform_memberships（R3-D-07 Option A — 设计冻结，**未建表**，实施待批准）

| 约束 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| PK | `id uuid DEFAULT uap_uuid_v7()` | | | column_default 断言 |
| FK | `user_id → users.id ON DELETE CASCADE` | 平台绑定随 user 硬删清理（正常路径先 revoke） | 误级联 → 仅关系行级联 | FK 规则断言 |
| FK | `role_id → roles.id ON DELETE RESTRICT` | 被绑定 PLATFORM role 不可删 | 无（is_system 已禁删） | 删除被引用 role → 拒绝 |
| UQ | `(user_id, role_id)`（非部分） | 每 user+role 单条历史 | 重授 = UPDATE | 重复插入拒绝 |
| UQ | `(user_id) WHERE status='active'`（部分） | 一用户至多 1 个 active 平台绑定 | — | 第二条 active 拒绝 |
| CK | `status IN ('active','revoked')` | 状态枚举 | — | 非法 status 拒绝 |
| TRIGGER | `tg_pm_role_scope` | 引用 role 必须 PLATFORM + active；结果态 active 时 user active | trigger RAISE 抛 ProgrammingError | 5 类非法绑定拒绝 |
| TRIGGER | `tg_pm_last_admin` | 禁使 active platform_admin 从 >0 → 0 | 首行 bootstrap 需放行（0→1） | last-admin revoke/delete 拒绝 |
| INDEX | `(role_id, status) WHERE status='active'` | 持有者查询 / last-admin 计数 | — | 索引存在断言 |
| 授权语义 | 仅 active 行生效；revoked 忽略；无绑定→DENY；grant/revoke 仅 active platform_admin + audit_logs(action='platform.*') | default deny | 授权层未实现前禁止平台授权上线 | 授权层测试（PM 系列） |

---

## R4 增补（2026-09-08 D-07 Hardening）

| 约束/规则 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| TRIGGER（roles 侧）`tg_roles_pm_lifecycle` | `platform_admin` 行（PLATFORM ∧ key）存在 active PM 绑定时禁止 status `active→disabled/archived`、禁止 DELETE（PMB-1） | 防"Role 停用 → 全体管理员失效"（纵深防线，T3 之外） | 与 T3 重叠（不同质，允许并存） | role 停用（有绑定）拒绝；撤绑定后停用允许 |
| Re-grant 规则 | `revoked → active` 用 **UPDATE 本行**（revoked_at=NULL），**禁止 INSERT 新行**（PMB-3） | 单行历史语义 | 误 INSERT → UQ 拒绝（兜底） | revoke→re-grant 同 id；duplicate INSERT 拒绝 |
| Duplicate grant | 已 active 时再 grant → 应用层拒绝；直接 INSERT → UQ 拒绝 | 语义显式 | — | PM 系列 |
| Bootstrap（PMB-2） | 仅当 PM 行数=0 可执行一次；audit `platform.admin.bootstrap` 同事务；此后永久关闭；丢失恢复=独立维护机制（人工批准） | 一次性信任根 | actor 伪造 | 二次 bootstrap 拒绝；伪造 actor='system' 拒绝 |
| User lifecycle（PMB-4） | 停用/软删先 revoke（PMB-1）再停用；无 users→PM 自动 revoke trigger；hard delete 才 CASCADE（仅 purge 终态）；user 非 active → effective=0 → DENY | 撤销不依赖 CASCADE | 停用最后 admin 被拒属预期 | 停用最后 admin 拒绝；user 停用但 PM 行 active → DENY |
| effective 谓词 | `pm.active ∧ u.active ∧ r.active ∧ r.scope='PLATFORM' ∧ r.key='platform_admin'`（PMB-1 canonical） | 授权判定唯一依据 | — | 授权层测试 |

---

## R5 增补（2026-09-08 Hardening：platform_state / bootstrap gate / 分层职责）

| 约束/规则 | 定义 | 目的 | 风险 | 测试方法 |
|---|---|---|---|---|
| 表 `platform_state` | 单例 `id smallint PK=1`；CK `id=1` + `bootstrap_state IN ('uninitialized','initialized')` 默认 uninitialized；`initialized_at NULL`；created/updated_at | 显式、独立、不可重置的初始化状态（P1-01） | 无业务 FK；与 PM 生命周期零耦合 | schema 断言 |
| TRIGGER `tg_platform_state_guard` | INSERT 仅 uninitialized 且表空；UPDATE 仅 `uninitialized→initialized`（initialized_at 非空）；DELETE 拒绝 | 单向状态机 + 永久保持 | 迁移 seed 须先于 trigger | B-02/B-03/delete/singleton 拒绝 |
| TRIGGER `tg_pm_bootstrap_gate` | PM INSERT 仅当 state=initialized 或（uninitialized 且 PM 无行） | count=0 不再重开 bootstrap；运行时 grant 走 initialized 分支 | 与 last-admin（DELETE/UPDATE 不触发本 INSERT gate）无冲突 | B-01/B-02 语义 |
| User lifecycle workflow | deactivate = revoke PM(PMB-1) → deactivate user，单事务；失败整体回滚；reactivate 不恢复 PM（三分层职责：DB 无自动 revoke / Service revoke-first / Authorization inactive→DENY） | P1-02 | 不可依赖 effective 谓词掩盖未 revoke | U-01..U-04 |
| Hard delete | users DELETE → PM CASCADE（purge 终态）；last-admin 不被 CASCADE 绕过（行级 trigger 拦截）；state 不受影响 | P1-03 | — | U-05/U-06/B-04/B-05 |
