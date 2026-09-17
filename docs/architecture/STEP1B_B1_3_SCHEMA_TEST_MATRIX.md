# STEP 1-B / B1-3 — Schema Test Matrix（Role & Permission Foundation）

Status: **PREP ONLY — 本阶段只定义测试，不实现测试代码**
执行环境：disposable `uap_b1_test`（**正式 `uap` 库不被测试触碰**）
未来 revision：`0005`（本阶段不存在）

图例：`OPEN` = 依赖未决决策（D-0x），决策冻结后补全；`FROZEN` = 冻结设计已定义。

---

## 1. Schema

| # | 测试 | 期望 |
|---|---|---|
| S1 | 3 张新表存在（roles / permissions / role_permissions） | table_exists |
| S2 | **精确表数**：public = 5 Identity + 4 Tenant/Space + 3 B1-3 + alembic_version = **13** | count == 13 |
| S3 | 无 resources / resource_permissions / resource_relations / acl_subject_types / agents / tools / ai_* / events / audit_logs / groups / domain 表 | 集合 disjoint |
| S4 | PK：roles/permissions = uuid（`DEFAULT uap_uuid_v7()`）；role_permissions = 复合 PK | pg_index + pg_attrdef |
| S5 | FK：`roles.tenant_id/space_id CASCADE`；`role_permissions.role_id/permission_id CASCADE`；`tenant_memberships.role_id/memberships.role_id RESTRICT` | referential_constraints.delete_rule |
| S6 | UNIQUE：roles 三条部分唯一（按 scope 互斥）；permissions key 全局唯一 | pg_indexes；重复插入被拒 |
| S7 | CHECK：`ck_roles_scope`、`ck_permissions_key`、`ck_role_permissions_effect` | 非法值被拒 |
| S8 | NOT NULL / DEFAULT 符合 Constraint Matrix | information_schema |
| S9 | 索引集合 == INDEX_STRATEGY §5（4 UQ + 1 PK + 3 btree） | pg_indexes 差集为空 |
| S10 | trigger：T1–T5 存在；`set_updated_at()` 仅 1 个（复用 B1-1） | pg_trigger / pg_proc |
| S11 | B1-1（5 表）与 B1-2（4 表）结构**未变化**（回归快照） | 与既有断言一致 |

## 2. Role

| # | 测试 | 期望 |
|---|---|---|
| R1 | 重复 role key（同 scope 同租户/空间）→ 拒绝 | 部分 UQ |
| R2 | 同名 key 在不同租户/不同空间/平台 → 允许 | scope 命名空间独立 |
| R3 | invalid scope（如 'GLOBAL'）→ 拒绝 | CK |
| R4 | scope 形状非法（TENANT 无 tenant_id；SPACE 无 space_id；PLATFORM 带 tenant_id）→ 拒绝 | `tg_roles_scope_shape` |
| R5 | role key 格式（R-D-13）：大写 / `-` / `.` / 空格 / 数字开头 → 拒绝；`tenant_admin` 等合法 | CK `^[a-z][a-z0-9_]{1,63}$` |
| R6 | `is_system=true` 角色：UPDATE（含改 name/status/is_system）与 DELETE → 拒绝 | `tg_roles_is_system_protect`（无条件） |
| R7 | 自定义角色（is_system=false）可修改/删除 | 允许（未被 membership 引用时） |
| R8 | `roles.status` 枚举（R-D-06）：`'active'/'disabled'/'archived'` 合法，其它拒绝 | CK `ck_roles_status` |
| R9 | 删除带 membership 引用的角色 → 拒绝（RESTRICT） | FK violation |
| R10 | 删除无引用角色 → 成功，其 role_permissions 级联删除 | CASCADE |
| R11 | `disabled`/`archived` role 不能被新 membership 绑定（R-D-06） | trigger（非 active 拒绝） |
| R12 | 系统角色 5 个 key 全部符合 key 格式（R-D-13） | 合规断言 |

## 3. Permission

| # | 测试 | 期望 |
|---|---|---|
| P1 | 重复 permission key → 拒绝 | UQ |
| P2 | invalid key 格式（`Bad Key!`、`User..read`）→ 拒绝 | CK 正则 |
| P3 | Permission 无 tenant_id/space_id（平台字典） | 列不存在 |
| P4 | Permission 无 updated_at | 列不存在 |
| P5 | invalid scope / status | **OPEN D-02/D-03**（冻结无此列）→ 测试不适用 |
| P6 | 删除 permission → 相关 role_permissions 级联 | CASCADE |

## 4. Role ↔ Permission

| # | 测试 | 期望 |
|---|---|---|
| RP1 | 重复关系（同 role+permission+effect）→ 拒绝 | PK |
| RP2 | 同一 (role,permission) 的 allow 与 deny **两行均可存在** | 冻结 PK 含 effect（D-04 风险：需应用层 deny 优先） |
| RP3 | invalid role FK → 拒绝 | FK |
| RP4 | invalid permission FK → 拒绝 | FK |
| RP5 | effect 非法 → 拒绝 | CK |
| RP6 | 删除 role → 其 role_permissions 清空 | CASCADE |

## 5. Scope（核心安全矩阵）

| # | 测试 | 期望 |
|---|---|---|
| SC1 | `tenant_memberships` + TENANT role（同租户、`active`） | **PASS** |
| SC2 | `tenant_memberships` + SPACE role | **DENY**（trigger） |
| SC3 | `tenant_memberships` + PLATFORM role | **DENY**（trigger） |
| SC4 | `tenant_memberships` + **其它租户**的 TENANT role | **DENY**（tenant_id 不匹配） |
| SC5 | `memberships` + SPACE role（同空间、`active`） | **PASS** |
| SC6 | `memberships` + TENANT role | **DENY** |
| SC7 | `memberships` + PLATFORM role | **DENY** |
| SC8 | 不存在 role | **DENY**（FK violation） |
| SC9 | 未知 scope 值 | **DENY**（CK） |
| SC10 | `role_id` 为 NULL（B1-3 收敛后） | **DENY**（NOT NULL） |
| SC11 | `disabled` / `archived` role 被 membership 绑定 | **DENY**（R-D-06：非 active 拒绝） |
| SC12 | 同一 (role,permission) 并存 allow+deny → **授权层裁决 DENY**（R-D-14） | 授权层测试（DB 允许并存；决策 DENY） |
| SC13 | SPACE role 形状 = `space_id 非空 ∧ tenant_id NULL`（R-D-16） | trigger 形状断言 |

## 6. Isolation

| # | 测试 | 期望 |
|---|---|---|
| I1 | Tenant A 的 role 不能被 Tenant B 的 membership 引用 | DENY（SC4） |
| I2 | Tenant A 不能操作/删除 Tenant B 的自定义 role | 应用层隔离 + 无跨租户路径（DB 层：role.tenant_id 决定可见性） |
| I3 | Space A（Tenant A）+ Tenant B role | DENY（scope/space 不匹配 + tenant consistency trigger） |
| I4 | Platform role 绑定 | **R3-D-07 FROZEN（Option A `platform_memberships`，未建表）**：用例见 §12（PM1–PM15）；安全断言不变：无绑定→DENY、tenant/space membership 无任何路径产生 PLATFORM 权限 |
| I5 | Tenant/Space membership 产生 PLATFORM 权限 | **DENY**（无表可引用 PLATFORM role；trigger 拒绝 scope='PLATFORM'） |
| I6 | 传递隔离（R-D-16）：membership 租户一致性 + role space 一致性 ⇒ role 租户 == membership 租户 | DB + 应用层测试 |

## 7. Seed / 幂等

| # | 测试 | 期望 |
|---|---|---|
| SD1 | 内置角色 seed 幂等（重复执行不重复创建）；识别键 = scope + tenant/space ownership + key（与唯一索引一致，R-D-15/R-D-12） | WHERE NOT EXISTS / ON CONFLICT |
| SD2 | 内置角色 scope 正确（platform_admin=PLATFORM 等） | 断言 |
| SD3 | 默认 role_id：`tenant_memberships → tenant_member`、`memberships → space_member` | 应用层/回填断言 |
| SD4 | 回填后无 NULL role_id | count(NULL)=0 |
| SD5 | 系统角色不被普通租户操作删除 | trigger 拒绝 |
| SD6 | 0005 回填确定性（R-D-08）：Tenant A/User A/Space A+membership → role_id=tenant_member/space_member、NOT NULL、scope 正确、FK 有效 | disposable 库场景 |
| SD7 | 回填失败（人为构造缺角色租户）→ migration **RAISE → ROLLBACK**，无部分成功 | failure 测试 |

## 8. Migration（未来 0005）

| # | 测试 | 期望 |
|---|---|---|
| M1 | fresh DB → upgrade head（0005） | 13 表 |
| M2 | 0004 → 0005 增量升级（保留既有数据） | 数据不丢 |
| M3 | rerun | no-op |
| M4 | downgrade 0005 → 0004（撤销 3 表 + FK + NOT NULL + trigger） | B1-2 四表仍在且结构不变 |
| M5 | 再 upgrade | 成功 |
| M6 | 失败 revision → 整事务回滚 + advisory lock 释放 + 无半成品 | 复用 B1-0 机制 |
| M7 | 迁移期间第二 runner（fail 模式）被拒 | 复用 B1-0 lock 测试 |
| M8 | **不修改 0001–0004 文件内容**（git diff 校验） | 无改动 |

## 9. Regression

| # | 测试 | 期望 |
|---|---|---|
| G1 | B1-0：lock / concurrency / failure / smoke | 12 项通过 |
| G2 | B1-1：Identity schema + security | 19 项通过 |
| G3 | B1-2：Tenant/Space schema + isolation + delete | 18 项通过 |
| G4 | Architecture Guard | 9 passed，Core→Domain 0 |
| G5 | 正式 `uap` 库表数仍为 0 | count == 0 |
| G6 | 全量 `pytest` | 无回归 |

---

## 10. 本阶段是否实现测试代码

**PREP 阶段：不实现。** 仅规划；决策（D-01…D-09）冻结后再实现对应断言。

---

## 11. R2 增补用例（2026-09-08 Decision Resolution Round 2 — 仅设计，不实现）

### 11.1 System Role Protection（R2-D-05，trigger `tg_roles_is_system_protect`）

| # | 测试 | 期望 |
|---|---|---|
| R20 | INSERT 一行 `is_system=true`（运行时连接） | **拒绝**（trigger RAISE；seed 已先行，0005 完成后无窗口） |
| R21 | UPDATE 系统角色任意列（key/name/scope/status/…） | **拒绝** |
| R22 | UPDATE 系统角色 `is_system: true→false` | **拒绝**（防脱保绕过） |
| R23 | UPDATE 自定义角色 `is_system: false→true` | **拒绝**（防提权） |
| R24 | DELETE 系统角色（含被 membership 引用/未引用） | **拒绝** |
| R25 | 系统角色权限（role_permissions）变更无运行时写路径 | 无 API/应用入口（授权层 default-deny；变更仅 migration） |
| R26 | 自定义角色（is_system=false）可创建/修改/删除（未引用时） | 允许 |

### 11.2 Role Status 语义（R2-D-06）

| # | 测试 | 期望 |
|---|---|---|
| R27 | 新 membership 绑定 `status='disabled'/'archived'` role | **拒绝**（绑定 trigger） |
| R28 | role 变 disabled 后：既有 membership 行**不变** | SELECT 行数/内容不变（Role Status ≠ Membership Status） |
| R29 | role 变 disabled 后：授权查询（应用层）返回 DENY（fail-closed） | 授权层测试（B1-3 只建数据，断言留待授权层） |
| R30 | archived 自定义角色 UPDATE 回 active → 恢复授权（绑定未变） | 允许；授权恢复 |
| R31 | 系统角色进入 disabled/archived | **拒绝**（status 受 is_system 保护） |
| R32 | 默认 `roles.status` | `'active'`（column_default） |

### 11.3 Role Key / Uniqueness 澄清（R2-D-13 / R2-D-12）

| # | 测试 | 期望 |
|---|---|---|
| R33 | 同 tenant 同 key 第二个角色（含 archived 占位） | **拒绝**（唯一索引含 archived 行 → archive 不释放 key） |
| R34 | 自定义角色 DELETE（未引用）后再建同 key | 允许（key 复用唯一途径） |
| R35 | 5 个系统角色 key 全部匹配 `^[a-z][a-z0-9_]{1,63}$` | 断言 |

### 11.4 Backfill 边界（R2-D-08，disposable 库场景）

| # | 测试 | 期望 |
|---|---|---|
| R36 | removed/removed_at 历史 membership 行回填默认角色 | 成功（NOT NULL 满足；无授权影响） |
| R37 | archived tenant/space 的 membership 回填 | 成功（role seed 覆盖每既有行） |
| R38 | 回填后 `role_id IS NULL` 计数 = 0 | 硬门禁（任一残留 → migration ROLLBACK） |
| R39 | 预置非法 role_id（不存在/scope 错/跨租户）→ 0005 校验 | RAISE → 整体 ROLLBACK（无部分成功） |

### 11.5 DENY > ALLOW（R2-D-14，授权层语义测试，B1-3 不实现）

| # | 场景 | 期望 |
|---|---|---|
| R40 | 仅 ALLOW | ALLOW |
| R41 | 仅 DENY | DENY |
| R42 | 同 (role, permission) ALLOW + DENY | **DENY** |
| R43 | 多角色命中、任一 DENY | **DENY** |

---

## 12. R3 增补用例（2026-09-08 D-07 Round 3 — platform_memberships；**表未建，仅设计**）

| # | 测试 | 期望 |
|---|---|---|
| PM1 | 建表结构：PK uuid / user FK CASCADE / role FK RESTRICT / status CK | schema inspection |
| PM2 | 绑定 role.scope='TENANT'/'SPACE' → 拒绝 | `tg_pm_role_scope` RAISE |
| PM3 | 绑定不存在的 role / 非 active role → 拒绝 | RAISE |
| PM4 | 绑定 status != active 的 user → 拒绝 | RAISE |
| PM5 | 同一 user 第二条 active 绑定 → 拒绝 | `uq_platform_memberships_active_user` |
| PM6 | revoke（status→revoked）后同 (user,role) 再授 = UPDATE 回 active | 允许；唯一行保留 |
| PM7 | revoked 行不参与授权（授权查询只见 active） | 授权层/DB 断言 |
| PM8 | DELETE/revoke 使 active platform_admin 数 →0（且原>0）→ 拒绝 | `tg_pm_last_admin` RAISE |
| PM9 | 首行 bootstrap（0→1） | 允许（部署流程） |
| PM10 | 删除绑定用户（硬删）→ 绑定 CASCADE 清理 | 关联删除 |
| PM11 | DELETE 被绑定的 PLATFORM role | 拒绝（FK RESTRICT + is_system） |
| PM12 | grant/revoke/transfer 均产生 `audit_logs(action='platform.*')` | 授权层审计断言 |
| PM13 | tenant_admin/space_admin 尝试授予平台角色 | DENY（无写路径 + 授权层） |
| PM14 | is_system=true 角色行本身不产生任何平台授权 | 无绑定→DENY |
| PM15 | 多节点部署：平台管理员列表来自 DB（无本地缓存） | 一致性断言 |
| PM16 | 唯一谓词：PLATFORM 角色与跨空间角色可同名；同 space/tenant 内同 key 拒绝 | 与 R3-0① 谓词一致 |

---

## 13. R4 增补用例（2026-09-08 D-07 Hardening — 设计层）

### 13.1 PMB-1 Last Admin × Role Lifecycle
| # | 测试 | 期望 |
|---|---|---|
| PM17 | `platform_admin` 行（PLATFORM）存在 active 绑定时 status active→disabled/archived | **拒绝**（`tg_roles_pm_lifecycle`，RAISE） |
| PM18 | 同上 DELETE | **拒绝** |
| PM19 | 撤掉全部绑定后再停用该角色 | 允许（无信任根风险；system 角色仍受 T3 保护） |
| PM20 | effective 计数：PM active ∧ user active ∧ role active ∧ PLATFORM ∧ key=platform_admin | =1（授权层谓词测试） |
| PM21 | user 变非 active（PM 行仍 active）→ effective | =0 → DENY（PMB-4） |

### 13.2 PMB-2 Bootstrap
| # | 测试 | 期望 |
|---|---|---|
| PM22 | PM 行数=0 时首次 bootstrap（INSERT 首行） | 允许；audit `platform.admin.bootstrap` 同事务 |
| PM23 | 行数>0 时再次 bootstrap | **拒绝**（条件不成立；路径永久关闭） |
| PM24 | 普通 API 提交 actor='system' | **拒绝**（actor 由认证派生，请求体携带即校验失败） |

### 13.3 PMB-3 Re-grant 生命周期
| # | 测试 | 期望 |
|---|---|---|
| PM25 | revoke 后 re-grant = UPDATE 同 id 行（status→active, revoked_at=NULL） | 成功；无新行 |
| PM26 | 已 active 时直接 INSERT 同 (user,role) | **拒绝**（UQ） |
| PM27 | 历史保留：created_at 不变；revoked_at 置位/清除正确 | 断言 |
| PM28 | 同态转换（active→active / revoked→revoked） | 拒绝（应用层） |

### 13.4 PMB-4 User Lifecycle
| # | 测试 | 期望 |
|---|---|---|
| PM29 | 停用最后一名 effective admin | **拒绝**（工作流须先 transfer/新授） |
| PM30 | 停用非最后 admin：先 revoke 后停用 | 成功；两动作均审计 |
| PM31 | user 非 active 但 PM 行 active → 授权 | DENY（fail-closed 兜底） |
| PM32 | hard delete user → PM 行 CASCADE | 仅 purge 终态；正常撤销不依赖 CASCADE |

### 13.5 Scope / Predicate / Reserved-Key 回归
| # | 测试 | 期望 |
|---|---|---|
| PM33 | TM/M 绑定 PLATFORM role / PM 绑定 TENANT·SPACE role | 无合法 DB 状态（scope trigger） |
| PM34 | 全文档唯一谓词：PLATFORM 含 `AND space_id IS NULL`（无旧单条件版本） | 静态扫描 0 残留 |
| PM35 | 跨 scope 同名 key（如租户自定义 `platform_admin`）合法 | 允许（无 reserved-key） |

---

## 14. R5 增补用例（2026-09-08 Hardening — 已实现于 test_rbac_hardening.py）

| # | 测试 | 期望 |
|---|---|---|
| B-01 | 首次 bootstrap（uninitialized+空 → PM 首行 + 翻转 initialized） | 允许；state=initialized |
| B-02 | 第二次 bootstrap / 回退 / 再翻转 | **拒绝**（guard，单向） |
| B-03 | PM revoke 后不重开 bootstrap | state 恒 initialized；写 state 被拒 |
| B-04 | 非最后管理员 user 硬删（PM CASCADE）不重开 | PM 减少但 state 不变 |
| B-05 | 最后管理员不可删 / 不可清空 PM；state 存活 | 拒绝 + state=initialized |
| B-06 | 伪造 system actor 无承载列 | 无 actor 列；effective 无 fallback |
| U-01 | deactivate = revoke PM → 停用 user | 两者落库；其余管理员不受影响 |
| U-02 | reactivate 后 PM 保持 revoked | effective=0（权限不复活） |
| U-03 | revoke 成功后停用失败 | 事务回滚 → PM 仍 active、user 仍 active |
| U-04 | inactive user（PM 行仍 active） | effective=0 → DENY（fail-closed） |
| U-05 | hard delete → PM CASCADE；state 不变 | 行清除；state=initialized |
| U-06 | 最后管理员 user 硬删 | **拒绝**（last-admin 不被 CASCADE 绕过） |
| U-00 | effective 谓词纯函数回归（无 fallback） | 6 组合断言 |
