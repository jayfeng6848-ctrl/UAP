# B1-4 — Schema Design（PREP / DESIGN ONLY — 不执行 DDL）

Status: **DESIGN — 不建表、不写 migration、不执行 DDL**
依据：`CORE_DOMAIN_MODEL.md` §1.3 · `STEP1B_CONSTRAINT_MATRIX.md` §3 · `STEP1B_INDEX_STRATEGY.md` · `STEP1B_ACL_STRATEGY.md` §2
命名与风格对齐：B1-1/B1-2/B1-3 既有 migration（`uap_uuid_v7()` 兜底 · `timestamptz(3)` · `set_updated_at()` 复用 · RAISE 型 trigger）

---

## 1. 为什么需要每一张表（必要性论证）

| 表 | 为什么必须存在 | 若不建的后果 |
|---|---|---|
| `resources` | 授权的**对象侧**：把"可被授权的东西"收敛为单一注册表，业务语义留在域扩展表 | 每个域各自定义归属/分类/状态 → 隔离与分类不可统一治理；P2-03 的 purge 策略无处落地 |
| `acl_subject_types` | 把 ACL 主体的**多态**从裸字符串升级为受控注册表 + 校验 | 裸 `subject_type + subject_id` → 无法阻止伪造主体（P1/P2-04 原问题） |
| `resource_permissions` | 实例级显式授权/拒绝（ABAC 落点之一），承载 `allow/deny + conditions + expires_at` | 只有角色级 RBAC → 无法表达"某人/某角色对这个具体对象"的授权与拒绝 |

> `resource_relations`：**本阶段不建**（B0 Q3 + CONSTRAINT_MATRIX §3 明确"P2 可选，B1 不建"）。理由：权限继承需递归评估，当前用扁平 `space_id` 已够；无真实需求前不引入。

---

## 2. `resources` — 通用资源注册表

### 2.1 字段

| 列 | 类型 | NULL | DEFAULT | 说明 |
|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()`（兜底；应用层 UUIDv7 为准） | PK |
| `tenant_id` | uuid | NN | — | 归属租户（隔离物化） |
| `space_id` | uuid | NULL | — | 空间归属；NULL = 平台级/未定空间 |
| `owner_id` | uuid | NULL | — | 创建者/所有者 |
| `resource_type` | text | NN | — | **开放格式**，CK 仅校验 `^[a-z][a-z0-9_.]{1,63}$` |
| `natural_key` | text | NULL | — | 幂等键（同 type 内唯一，部分唯一索引） |
| `classification` | text | NN | `'INTERNAL'` | 四档枚举（见 CK） |
| `status` | text | NN | `'active'` | `active/archived/deleted` |
| `label` | text | NULL | — | 展示名 |
| `metadata` | jsonb | NN | `'{}'` | 扩展元数据（**严禁密钥**，CI 扫描） |
| `archived_at` | timestamptz | NULL | — | 归档时间 |
| `deleted_at` | timestamptz | NULL | — | 软删时间 |
| `created_at` / `updated_at` | timestamptz | NN | `now()` | `updated_at` 由 trigger 维护 |

### 2.2 约束

| 类别 | 定义 |
|---|---|
| PK | `id` |
| FK | `tenant_id → tenants.id ON DELETE **RESTRICT**`（NN）<br>`space_id → spaces.id ON DELETE **RESTRICT**`（NULL 允许）<br>`owner_id → users.id ON DELETE **SET NULL**`（NULL 允许） |
| UQ（部分） | `uq_resources_natural ON (tenant_id, resource_type, natural_key) WHERE natural_key IS NOT NULL AND deleted_at IS NULL` |
| CK | `ck_resources_type`: `resource_type ~ '^[a-z][a-z0-9_.]{1,63}$'`<br>`ck_resources_classification`: `classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')`<br>`ck_resources_status`: `status IN ('active','archived','deleted')` |
| INDEX | `ix_res_tenant_space_type_status (tenant_id, space_id, resource_type, status)` — 列表主查询<br>`ix_res_tenant_owner (tenant_id, owner_id)` — "我创建的资源"<br>`ix_res_tenant_type_created (tenant_id, resource_type, created_at DESC)` — 时间序/分页<br>`ix_res_tenant_deleted (tenant_id, deleted_at) WHERE deleted_at IS NOT NULL` — retention purge 扫描 |
| TRIGGER | ① `tg_resources_set_updated_at` BEFORE UPDATE → 复用 `set_updated_at()`（**不重建函数**）<br>② **`tg_resources_tenant_space_consistency`** BEFORE INSERT OR UPDATE（**D-B14-10 = A-1，FROZEN 2026-09-13**）：`space_id IS NULL` → 放行；`space_id IS NOT NULL` → 要求 `resources.tenant_id = spaces.tenant_id`，否则 RAISE。**boundary: structural integrity only —— 不是 authorization evaluator**；不引入 RLS |

### 2.3 删除行为（P2-03 铁律）

- 父表删除**一律 RESTRICT**：删除有资源的 tenant/space **被拒绝**，必须走 `archive → soft delete → retention → controlled purge`
- 资源自身的域扩展表（未来）随受控 purge 通过 1:1 共享主键 CASCADE 清理（**本阶段无域表**）
- `owner_id` 的 SET NULL 保证：删除用户**不会**删除资源

---

## 3. `acl_subject_types` — ACL 主体类型注册表（ROOT）

### 3.1 字段

| 列 | 类型 | NULL | DEFAULT | 说明 |
|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK |
| `key` | text | NN | — | 主体类型键（CK 白名单 + 格式） |
| `description` | text | NULL | — | 说明 |
| `created_at` | timestamptz | NN | `now()` | — |
| `archived_at` | timestamptz | NULL | — | 归档（从部分唯一索引中消失 → 可重建同名 key） |

> 该表**无 `updated_at`**（冻结字段清单不含）→ **不挂 updated_at trigger**。

### 3.2 约束

| 类别 | 定义 |
|---|---|
| PK | `id` |
| UQ（部分） | `uq_acl_subject_types_key ON (lower(key)) WHERE archived_at IS NULL` |
| CK | `ck_acl_subject_types_key`: `key ~ '^[a-z][a-z0-9_]{1,31}$'`<br>`ck_acl_subject_types_whitelist`: `key IN ('user','role','agent')`（**P2-02：不含 `group`**） |
| TRIGGER | **`tg_acl_subject_types_protect`** BEFORE INSERT OR UPDATE OR DELETE（**D-B14-12 = A，FROZEN 2026-09-13**）：**platform-controlled registry 保护** —— 运行时 INSERT 拒绝；`key` UPDATE 拒绝（`description` 等非受控列允许）；DELETE 拒绝（退役走 `archived_at`）。**boundary: registry governance only —— 不是 authorization evaluator，不演变为 Domain authorization** |
| 受控写入（**W-3 决议**） | **Initial registry population is migration-controlled and is part of schema governance, not Domain runtime registration.** 运行时无写入口；`user`/`role`/`agent` 三行属 **P13**。合法写入须经 migration（既有先例：`0005` 先 INSERT 内置 role → 后建 protect trigger；`0006` 先 INSERT `platform_state` → 后建 guard）。机制候选见 `B1-4_DESIGN.md` §8.1（**不得**引入 runtime / plugin / domain registration API） |
| 初始 seed | **B1-4 不 seed**（三行属 P13）—— 见 §3.3 |

### 3.3 初始 seed —— **B1-4 不做任何 seed（R1 更正）**

| 事实 | 原文依据 |
|---|---|
| P06（=B1-4）**不属于 seed phase** | `STEP1B_SCHEMA_DEPENDENCY.md:193`："**P00-P10 均无 seed 需求；P13 才有 seed**。所有 trigger（P11）必须先于 P13 seed。" |
| 三行 `user`/`role`/`agent` 属 **P13** | `STEP1B_SEED_STRATEGY.md:14`（seed 清单 `[1] acl_subject_types`）· `:111-116`（初始三行） |
| `group` 永不注册 | `CORE_DOMAIN_MODEL.md:248/249` · P2-02 |
| B1-4 期间的直接后果 | `acl_subject_types` 为空 ⇒ `resource_permissions.subject_type_id` FK 不可满足 ⇒ **ACL 行不可写入**（既无未验证主体，也无 ACL 能力） |

> **R1 撤回**：上一轮本节提出的"B1-4 只 seed `user`/`role`（推荐 A）"**作废** —— 其前提（B1-4 会 seed）与冻结原文冲突。幂等/单事务/无敏感数据等 seed 要求属 **P13** 的执行规则，B1-4 不适用。

---

## 4. `resource_permissions` — 资源级 ACL

### 4.1 字段

| 列 | 类型 | NULL | DEFAULT | 说明 |
|---|---|---|---|---|
| `id` | uuid | NN | `uap_uuid_v7()` | PK |
| `resource_id` | uuid | NN | — | 受保护资源 |
| `subject_type_id` | uuid | NN | — | 引用注册表（**不是裸字符串**） |
| `subject_id` | uuid | NN | — | 主体 id（受控多态，由 trigger 校验存在性） |
| `action` | text | NN | — | **opaque action identifier**（占位记法 `<action>`）：**当前未冻结语义**的非空标识符；**D-B14-08 = A（FROZEN 2026-09-13）** ⇒ 本阶段**零新增 semantic/format contract**（不加 regex CHECK、不加命名空间 CHECK、不加 enum/whitelist/vocabulary） |
| `effect` | text | NN | — | `allow` / `deny` |
| `conditions` | jsonb | NULL | — | **storage-only**（ABAC 未来输入，本阶段不解析） |
| `inherited` | bool | NN | `false` | 是否继承（agent 归档时置 true 使其到期） |
| `expires_at` | timestamptz | NULL | — | 到期时间 |
| `granted_by` | uuid | NULL | — | **actor attribution**（谁授予；**非 ownership**）→ `users.id` **`ON DELETE SET NULL`**（**D-B14-09 = A FROZEN**） |
| `created_at` | timestamptz | NN | `now()` | — |

> 冻结字段清单**无 `updated_at`** → 不挂 updated_at trigger；**不冗余 tenant_id/space_id**（隔离随父 `resources`，ACL_STRATEGY §4 冻结）。

### 4.2 约束

| 类别 | 定义 |
|---|---|
| PK | `id` |
| FK | `resource_id → resources.id ON DELETE **CASCADE**`（NN；受控 purge 白名单，理由：ACL 是资源的纯技术从属）<br>`subject_type_id → acl_subject_types.id ON DELETE **RESTRICT**`（NN）<br>`granted_by → users.id` **`ON DELETE SET NULL`**（NULL；**D-B14-09 = A FROZEN 2026-09-13** —— 语义 = **actor attribution**，与 `resources.owner_id` 的 ownership SET NULL **语义正交、相互独立**） |
| UQ | `uq_resource_perm ON (resource_id, subject_type_id, subject_id, action)`（非部分）<br>→ **同一 (资源, 主体, 动作) 只能一行**；`effect` 变更 = `UPDATE`（不新增行） |
| CK | `ck_resource_permissions_effect`: `effect IN ('allow','deny')` |
| INDEX | `uq_resource_perm`（主查询：按资源取 ACL）<br>`ix_rp_subject (subject_type_id, subject_id)` — 主体反查（撤销/审计） |
| TRIGGER | `tg_acl_subject_exists` BEFORE INSERT OR UPDATE —— **B1-4 不实施**（B0 冻结「最早可挂 = P09 后」，见 D-B14-02）。B1-4 期间 `acl_subject_types` 为空 ⇒ 该表**不可写入**，无未验证主体风险。<br>**注**：`tg_acl_subject_types_protect` 是 **`acl_subject_types` 上的** trigger（见 §3.2），不属于本表 |

### 4.3 删除 / 归档 / 清理矩阵（B0 ACL_STRATEGY §5 冻结）—— R1 更正「B1-4 可否落地」列

| 事件 | 行为 | 机制 | 最早 phase | B1-4 |
|---|---|---|---|---|
| user 软删 | ACL **保留** | 无动作 | — | ✅ 无动作即符合 |
| user 硬删 | 清该 user 的 ACL | `tg_acl_user_hard_delete` | **P09 后**（TRIGGER_INVENTORY:101/164） | ❌ 不实施 |
| role 删除尝试 | 被 ACL 引用时 **拒绝** | `tg_acl_role_delete_block` | **P09 后**（:112/165） | ❌ 不实施 |
| role 归档 | deny 行不参与决策、allow 行保留 | 授权层检查 `archived_at` | 授权层阶段 | ✅（本阶段无 DB 动作） |
| agent 归档 | 该 agent ACL 临时到期 | `tg_agent_acl_expire` | **P09 后**（:123/166） | ❌ 不实施 |
| resource 软删 | ACL 保留 | 无动作 | — | ✅ |
| resource 受控 purge | ACL 随删 | FK CASCADE | 表建时 | ✅ |
| membership removed | ACL 不预清理；授权阶段实时校验 → DENY + audit | 授权层 | 后续阶段 | ✅（审计 defer P10/D-B14-07） |

### 4.4 Idempotency（不可变/重放要求）

| 场景 | 规则 |
|---|---|
| 重复 grant 同 `(resource, subject_type, subject_id, action)` | UQ 拒绝 → 应用层应转为 `UPDATE effect`（幂等语义） |
| `effect` 变更（allow↔deny） | `UPDATE` 本行（§R2-D-14 语义保留在授权层） |
| ACL 撤销 | `DELETE` 该行（或 `expires_at=now()` 使其自然到期） |
| audit 同事务 | **defer**（`audit_logs` 不存在，D-B14-07） |

---

## 5. tenant / space scope 归属规则

| 表 | tenant scope | space scope | 规则 |
|---|---|---|---|
| `resources` | `tenant_id` **NN** | `space_id` NULL 允许 | 平台级资源 `space_id=NULL`；`space_id IS NOT NULL` 时由 **`tg_resources_tenant_space_consistency`**（**D-B14-10 = A-1 FROZEN**，BEFORE INSERT OR UPDATE）强制 `spaces.tenant_id = resources.tenant_id` —— **structural integrity only，不做 authorization evaluation** |
| `acl_subject_types` | 无 | 无 | 全局注册表（平台级字典）；受 **`tg_acl_subject_types_protect`** 保护（**D-B14-12 = A FROZEN**）—— **registry governance only** |
| `resource_permissions` | 不冗余 | 不冗余 | 随父 `resources` 隔离；跨租户语义在授权层（B0 ACL §3 冻结） |

---

## 6. 索引策略（无 inflation）

| 索引 | 类型 | Query Pattern | Why | 为何现有索引不可用 |
|---|---|---|---|---|
| `uq_resources_natural` | 部分 UQ | 按 `(tenant, type, natural_key)` 幂等查找 | 幂等/去重 | 需部分谓词排除软删与空 key |
| `ix_res_tenant_space_type_status` | btree | 资源列表（tenant→space→type→status 前缀） | 主列表查询 | 列顺序与前缀不匹配其他索引 |
| `ix_res_tenant_owner` | btree | "我创建的资源" | 按 owner 过滤 | 前缀为 tenant,owner，不能被 type 索引替代 |
| `ix_res_tenant_type_created` | btree DESC | 时间序列表/分页 | 分页 | 需要 `created_at DESC` 序 |
| `ix_res_tenant_deleted` | 部分 btree | retention purge 扫描软删超期行 | purge job | 部分谓词避免为活跃行建条目 |
| `uq_acl_subject_types_key` | 部分 UQ | by key（含大小写归一） | 注册唯一性 | 部分谓词允许归档后重建 |
| `uq_resource_perm` | UQ | 按资源取 ACL（主查询） | 授权主路径 | 打头 resource_id，兼作主查询索引 |
| `ix_rp_subject` | btree | 主体反查（撤销/审计） | 反查 | UQ 打头是 resource_id，无法服务 subject 反查 |

**不建**：`resources` 低基数列单列索引、jsonb GIN、`subject_type_id` 单独索引（FK 目标几乎不删，B0 已判免）。

---

## 7. 与冻结文档的差异登记（只记录，不修改）

| # | 差异/待定 | 处理（R1 更新） |
|---|---|---|
| 1 | B0 冻结 ACL trigger 全在 P09 后；H/I 的 dependency 列不含 agents（原文不精确） | **已按冻结原文裁定**：B1-4 实施 0 个 ACL trigger（D-B14-02 RESOLVED）；是否**提前**属冻结文档修订事项，需人工批准 |
| 2 | B0 冻结 `acl_subject_types` 三行 seed，且 seed 阶段 = P13 | **已按冻结原文裁定**：B1-4 **不 seed**（D-B14-01 RESOLVED）；无"已注册未校验"窗口 |
| 3 | `granted_by → users.id` 语义与删除行为均未明示 | **已冻结 D-B14-09 = A（2026-09-13）**：语义 = **actor attribution**；删除 = **`ON DELETE SET NULL`**。B0 文档（`CONSTRAINT_MATRIX` §3 FK 行 · `ACL_STRATEGY` §2 DDL）已同步 |
| 4 | `action` 无格式/取值约束；action/权限词表未冻结 | **已冻结 D-B14-08 = A（2026-09-13）**：**零新增 semantic/format contract**（不加 regex/命名空间 CK；不加 enum/whitelist/vocabulary）；`action` = **opaque identifier**；**不得**迁移未来 `permissions` seed dictionary。候选 B 未采纳 ⇒ **`ACT-03` 条件未成立** |
| 5 | `resources.tenant_id`/`space_id` 归属一致性原无冻结约束（**B0 coverage gap**） | **已冻结 D-B14-10 = A-1（2026-09-13）**：B1-4 引入 `tg_resources_tenant_space_consistency`（P06）；B0 三份文档（TRIGGER_INVENTORY 条目 **F2** / SCHEMA_DEPENDENCY §7 / CONSTRAINT_MATRIX §3）已同步修订；**G/H/I/J 保持 P09 后** |
| 6 | `acl_subject_types` 治理（谁可写）未冻结 | **已冻结 D-B14-12 = A（2026-09-13）**：**platform-controlled registry + `tg_acl_subject_types_protect`**（BEFORE I/U/D）；whitelist 保持 `user`/`role`/`agent`（不增 `group`、不改 whitelist、不提前 seed）；**registry governance only，不演变为 Domain authorization**。B0 三份文档（`TRIGGER_INVENTORY` 条目 **C2** · `SCHEMA_DEPENDENCY` §7 · `CONSTRAINT_MATRIX` §3）已同步 |
| 7 | CORE §1.3 写"role 归档由 trigger 写 audit"，与"trigger 不写 audit"本体论冲突 | **P3 文档不一致**（KEEP DEFERRED，见 GATE §4） |
