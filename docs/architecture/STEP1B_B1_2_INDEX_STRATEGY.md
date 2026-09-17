# STEP 1-B / B1-2 — Index Strategy（Tenant / Space Foundation）

Status: **PREP ONLY**
原则：只为已知查询模式建索引；每个非 PK/UQ 索引必须回答
**Query Pattern → Why Needed → Expected Cardinality → Why Existing Index Cannot Serve It**。
禁止 index inflation。

来源：B0 `STEP1B_INDEX_STRATEGY.md` §1（tenants/spaces/memberships 条目）+ §3（FK 反查清单）。

---

## 1. tenants

| index | type | Query Pattern | Why Needed | Cardinality | Why Existing Cannot Serve |
|---|---|---|---|---|---|
| `uq_tenants_slug ON (lower(slug))` | **UNIQUE**（表达式） | `WHERE lower(slug) = :slug`（按 slug 定位租户） | slug 是租户的对外稳定标识；唯一性即查询索引 | 租户数少（10²–10⁴），高选择性 | 无其它索引（PK 是 uuid） |

**不建**：
- `ix_tenants_status`：B0 标为 P3 候选（"后台按状态批扫"），B1-2 无批扫 job → **不建**
- `ix_tenants_plan` / `ix_tenants_region`：无查询需求 → 不建

## 2. spaces

| index | type | Query Pattern | Why Needed | Cardinality | Why Existing Cannot Serve |
|---|---|---|---|---|---|
| `uq_spaces_key ON (tenant_id, lower(key)) WHERE deleted_at IS NULL` | **UNIQUE 部分**（表达式+部分） | `WHERE tenant_id = :t AND lower(key) = :k`（租户内按 key 定位空间） | 空间 key 在租户内唯一；排除软删行 | 租户 × 空间（10²–10⁵），高选择性 | PK(uuid) 无法服务 key 查找 |
| `ix_spaces_tenant_status ON (tenant_id, status)` | btree | `WHERE tenant_id = :t AND status = 'active'`（租户空间列表 / 归档扫描） | 列表页与 purge 扫描按租户+状态过滤 | 中（每租户数十至数千） | `uq_spaces_key` 以 (tenant_id, lower(key)) 打头，**不含 status 谓词**，无法服务状态过滤 |

**不建**：`ix_spaces_owner`（owner 查询低频，且无明确需求）；`ix_spaces_kind`（低基数 + 无查询）；`ix_spaces_visibility`（低基数）

## 3. tenant_memberships

| index | type | Query Pattern | Why Needed | Cardinality | Why Existing Cannot Serve |
|---|---|---|---|---|---|
| `uq_tenant_memberships ON (tenant_id, user_id)` | **UNIQUE** | ① 成员唯一性 ② `WHERE tenant_id = :t`（租户成员列表） | 防止同用户重复加入；租户成员列表 | 高（用户×租户） | 无 |
| `ix_tm_user ON (user_id)` | btree | `WHERE user_id = :u`（"我属于哪些租户" — 切换租户列表） | 登录后的租户选择器主查询 | 中（每用户 1–N 租户） | `uq_tenant_memberships` 以 `tenant_id` 打头，**无法**服务仅按 user_id 的前缀查询 |
| `ix_tm_role ON (role_id)` | btree | FK 反查（role 删除 RESTRICT 检查） | 防止 role 删除时全表扫 | — | ⏳ **FUTURE**（随 role FK 一起建） |

**不建**：`ix_tm_status`（低基数）；`(tenant_id, status)`（成员列表通常全量展示且与 UQ 前缀重复度高）

## 4. memberships

| index | type | Query Pattern | Why Needed | Cardinality | Why Existing Cannot Serve |
|---|---|---|---|---|---|
| `uq_memberships ON (space_id, user_id) WHERE removed_at IS NULL` | **UNIQUE 部分** | ① 成员唯一性 ② `WHERE space_id = :s`（空间成员列表） | 防重复加入；空间成员列表 | 高 | 无 |
| `ix_memberships_tenant_user ON (tenant_id, user_id)` | btree | `WHERE tenant_id = :t AND user_id = :u`（"我在该租户的哪些空间"） | 租户视角的成员汇总（跨空间） | 中高 | `uq_memberships` 以 `space_id` 打头，不含 tenant_id 作为前缀列 → 无法按 tenant 聚合 |
| `ix_memberships_role ON (role_id)` | btree | FK 反查（role 删除 RESTRICT） | 防全表扫 | — | ⏳ **FUTURE**（随 role FK） |

**不建**：`ix_memberships_status`（低基数）；`ix_memberships_space_status`（无明确状态过滤需求）

---

## 5. 汇总

| 类别 | 数量 | 索引 |
|---|---|---|
| UNIQUE（含部分/表达式） | 4 | uq_tenants_slug、uq_spaces_key、uq_tenant_memberships、uq_memberships |
| 非唯一 btree | 3 | ix_spaces_tenant_status、ix_tm_user、ix_memberships_tenant_user |
| FUTURE（roles 后） | 2 | ix_tm_role、ix_memberships_role |
| **B1-2 实际新建** | **7** | （4 UQ + 3 btree） |

> 每个非唯一索引均已给出 Query Pattern / Why / Cardinality / 现有索引为何不可用（见上表）。

## 6. 反模式排查

| 检查 | 结论 |
|---|---|
| 低基数列单列索引（status / visibility / kind） | **不建** |
| jsonb GIN（settings） | **不建**（无过滤查询需求） |
| 外键列一律建索引 | 只建**需要反查**者（ix_tm_user / ix_memberships_tenant_user / FUTURE role 索引）；tenant_id/space_id 已被 UQ 前缀覆盖 |
| 重复前缀索引 | `ix_spaces_tenant_status` 与 `uq_spaces_key` 共享 tenant 前缀但谓词不同（status vs key）→ 服务不同查询，非冗余 |