# STEP 1-B / B1-3 — Index Strategy（Role & Permission Foundation）

Status: **PREP ONLY**
原则：只按**真实 Query Pattern** 建索引；每个索引回答 **index / query pattern / why / cardinality**；禁止 index inflation。

---

## 1. `roles`

| index | type | Query Pattern | Why | Cardinality |
|---|---|---|---|---|
| `uq_roles_platform ON (lower(key)) WHERE tenant_id IS NULL AND space_id IS NULL` | UNIQUE（部分+表达式） | `WHERE tenant_id IS NULL AND lower(key)=:k`（解析平台角色） | 平台角色 key 唯一即查询索引；大小写不敏感 | 极少（个位数平台角色） |
| `uq_roles_tenant ON (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL AND space_id IS NULL` | UNIQUE（部分+表达式） | `WHERE tenant_id=:t AND lower(key)=:k`（解析租户内置/自定义角色） | 租户内角色 key 唯一；授权解析主路径 | 租户 × 角色（10–10² 每租户） |
| `uq_roles_space ON (space_id, lower(key)) WHERE space_id IS NOT NULL` | UNIQUE（部分+表达式） | `WHERE space_id=:s AND lower(key)=:k`（解析空间角色） | 空间内角色 key 唯一 | 空间 × 角色（10–10² 每空间） |

**不建**（除非审计批准）：
- `ix_roles_scope`：低基数列（3 值）；角色解析总是带 tenant_id/space_id 前缀 → UQ 已覆盖
- `ix_roles_tenant`（单列）：`uq_roles_tenant` 以 tenant_id 打头，已可服务"某租户的角色列表"
- `ix_roles_space`（单列）：`uq_roles_space` 以 space_id 打头，已覆盖
- `ix_roles_status`：低基数 + 无批扫需求
- `ix_roles_is_system`：极低基数

## 2. `permissions`

| index | type | Query Pattern | Why | Cardinality |
|---|---|---|---|---|
| `uq_permissions_key ON (key)` | UNIQUE | `WHERE key=:k`（按 key 解析权限；seed/校验重复） | 全局唯一即查询索引 | 平台字典（10²–10³） |

**不建**：`ix_permissions_resource_type`（低基数 + 无明确查询）；`ix_permissions_action`（低基数）；jsonb 无 GIN 需求。

## 3. `role_permissions`

| index | type | Query Pattern | Why | Cardinality |
|---|---|---|---|---|
| PK `(role_id, permission_id, effect)` | PK（btree） | `WHERE role_id=:r`（取某角色的全部权限 — 授权主查询） | 以 role_id 打头，天然服务权限展开 | 角色 × 权限（10²–10⁴） |

**补充需求（FK 反查）**：

| index | type | Query Pattern | Why | Cardinality |
|---|---|---|---|---|
| `ix_rp_permission ON (permission_id)` | btree | ① `WHERE permission_id=:p`（"哪些角色拥有该权限"）② 删除 permission 时 FK CASCADE 扫表 | PK 以 role_id 打头，**无法**服务 permission 侧查询/删除 | 中 |

> B0 `STEP1B_INDEX_STRATEGY.md` §1 已列 `ix_rp_permission`（标注 P3 候选）；本阶段**建议建**（permission 删除与影响分析是已知需求）。若审计认为仍可选 → 标记 PROPOSED。

## 4. B1-3 为既有表补充的索引（随 role FK 一起）

| index | type | Query Pattern | Why | Cardinality |
|---|---|---|---|---|
| `ix_tm_role ON tenant_memberships(role_id)` | btree | 删除 role 时的 RESTRICT 检查 | 无索引则删除角色触发全表扫（B0 §3 FK 反查清单） | 中 |
| `ix_memberships_role ON memberships(role_id)` | btree | 同上 | 同上 | 中 |

> 两者在 B0 INDEX_STRATEGY §3 已列为"FK 反查强制清单（随 roles 建立）"。

## 5. 汇总

| 类别 | 数量 | 索引 |
|---|---|---|
| UNIQUE（部分/表达式） | 4 | uq_roles_platform、uq_roles_tenant、uq_roles_space、uq_permissions_key |
| PK | 1 | role_permissions PK（三列复合） |
| 非唯一 btree | 3 | ix_rp_permission、ix_tm_role、ix_memberships_role |
| **B1-3 实际新建** | **8** | （4 UQ + 1 PK + 3 btree；PK 随表创建） |

## 6. 反模式排查

| 检查 | 结论 |
|---|---|
| 低基数列单列索引（scope/status/is_system/effect） | **不建** |
| jsonb GIN（`role_permissions.conditions`） | **不建**（本阶段不求值） |
| 冗余前缀索引 | roles 三条 UQ 谓词互斥、前缀不同 → 服务不同解析路径，非冗余 |
| "未来可能查询"索引 | 一律不建（如需，单独立项） |

---

## R3 增补（2026-09-08 D-07 Round 3）— platform_memberships 索引（设计冻结，未建表）

| index | type | query pattern | why | cardinality |
|---|---|---|---|---|
| `uq_platform_memberships_user_role (user_id, role_id)` | UNIQUE（非部分） | 每 user+role 单条历史（撤销后重授=UPDATE） | 关系唯一性 | user × role（个位数） |
| `uq_platform_memberships_active_user (user_id) WHERE status='active'` | UNIQUE（部分） | 一用户 active 平台绑定查重 | 单 active 约束 | 绑定数 |
| `ix_platform_memberships_role_status (role_id, status) WHERE status='active'` | 非唯一（部分） | "谁是 platform_admin" / last-admin 计数 | 撤销/转让决策主查询 | 绑定数（极少） |

### R4 注记（2026-09-08 D-07 Hardening — 无新增索引）
- PMB-1..4 不需要新索引：effective 计数/持有者查询由既有 `uq_platform_memberships_active_user` + `ix_platform_memberships_role_status` 覆盖；re-grant 复用 `uq_platform_memberships_user_role`（UPDATE 同 id，无新查找路径）。
