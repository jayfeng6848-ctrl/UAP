# STEP 1-B / B1-2 — Dependency Graph（Tenant / Space Foundation）

Status: **PREP ONLY**
配套：B0 `STEP1B_SCHEMA_DEPENDENCY.md` §5（P03–P05）/ §4（循环与前向依赖处理）

---

## 1. B1-2 依赖图（4 张新表）

```
                    ┌──────────┐
                    │  users   │ ← B1-1 已建（冻结，不改）
                    └────┬─────┘
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
   ┌───────────┐   ┌──────────────────┐  │
   │ tenants   │   │tenant_memberships│  │
   └─────┬─────┘   └────────┬─────────┘  │
         │                  │             │
         │ tenant_id        │ tenant_id   │ user_id
         │ (RESTRICT)       │ (CASCADE)   │
         ▼                  │             │
   ┌───────────┐            │             │
   │  spaces   │            │             │
   └─────┬─────┘            │             │
         │ space_id         │             │
         └──────────┬───────┘             │
                    ▼                     ▼
             ┌─────────────────────────────┐
             │        memberships          │
             │  tenant_id (冗余, CASCADE)  │
             │  space_id  (CASCADE)        │
             │  user_id   (CASCADE)        │
             │  role_id   (无 FK, B1-3 补) │
             └─────────────────────────────┘
```

> `role_id` 在 B1-2 **只有列、没有 FK**（D-01 Forward Dependency）；图中虚语义指向 `roles` 表示 B1-3 收敛。

### 依赖表

| 表 | 依赖 | FK（→ 目标，ON DELETE） |
|---|---|---|
| `tenants` | —（root） | — |
| `spaces` | tenants, users | `tenant_id → tenants RESTRICT`；`owner_id → users SET NULL`（**D-03 PROPOSED，待批准**） |
| `tenant_memberships` | tenants, users（**roles 属 B1-3**） | `tenant_id → tenants CASCADE`；`user_id → users CASCADE`；**`role_id` 无 FK（D-01）** |
| `memberships` | tenants, spaces, users（**roles 属 B1-3**） | `tenant_id → tenants CASCADE`（冗余）；`space_id → spaces CASCADE`；`user_id → users CASCADE`；**`role_id` 无 FK（D-01）** |

---

## 2. roles = FUTURE DEPENDENCY（不创建）

```
memberships.role_id        ──⏳ FUTURE FK──→ roles.id
tenant_memberships.role_id ──⏳ FUTURE FK──→ roles.id
```

- **本阶段不创建 `roles` / `permissions` / `role_permissions`**
- 处理：**D-01 Forward Dependency / Deferred Constraint** —— B1-2 保留 `role_id` 列（NULL 允许）**但不创建 FK**；B1-3 建 roles → seed 内置角色 → 回填 → `SET NOT NULL` → `ADD CONSTRAINT ... ON DELETE RESTRICT` → 挂 scope trigger → 完整一致性验证
- **这不是 DEFERRABLE FK**：`DEFERRABLE` 仅延后**已存在**约束的检查时机，**不能**在 `roles` 表不存在时创建 FK
- 窗口期（B1-2 交付后至 B1-3 完成前）：**授权层 fail-closed**（D-02），拒绝不存在 role / scope 不匹配 / 非 TENANT role 用于 TM / 非 SPACE role 用于 M

---

## 3. 循环 FK 检查

| 检查 | 结论 |
|---|---|
| `tenants ↔ spaces` | spaces→tenants 单向（tenants 无出边）→ **无循环** |
| `spaces ↔ memberships` | memberships→spaces 单向 → **无循环** |
| `tenants ↔ tenant_memberships` | 单向 → **无循环** |
| `users ↔ memberships` | 单向（users 无出边，primary_identity_id 无 FK）→ **无循环** |
| `memberships.tenant_id`（冗余）→ tenants，而 tenants 无回边 | **无循环** |
| 与 B1-1 Identity 域交叉 | users 无出边指向 tenant/space → **无循环** |

**结论：B1-2 不引入任何新循环 FK。**

---

## 4. 创建顺序（B1-2 revision 内部）

```
1. tenants                    (root)
2. spaces                     (依赖 tenants + users)
3. tenant_memberships         (依赖 tenants + users；role_id 列存在，FK 延后)
4. memberships                (依赖 tenants + spaces + users；role_id 列存在，FK 延后)
```

Downgrade 反向：
```
DROP memberships → DROP tenant_memberships → DROP spaces → DROP tenants
（+ DROP 本阶段 trigger/函数；无 CASCADE）
```

## 5. 与 B0 Phase 的对应

| B0 Phase | B1-2 落地 |
|---|---|
| P03 Tenant / Space | tenants → spaces ✅ 本阶段 |
| P05 Membership | tenant_memberships → memberships ✅ 本阶段（role FK 延后） |
| P04 Role / Permission | ⏳ 后续阶段（B1-3 或审计指定） |

> B0 原顺序 P04(roles) 早于 P05(membership)；因 B1-2 范围含 membership 但不含 roles → role FK 按 deferred 处理，不改变 P04/P05 的**逻辑**先后（roles 仍在 membership 约束收敛前建立）。

---

## 6. 与 B1-1 的兼容

- B1-1 五表（`users`/`identities`/`credentials`/`devices`/`sessions`）**零修改**
- 新表仅通过 FK 引用 `users.id`（4 处：spaces.owner_id、tm.user_id、tm.invited_by、tm.role_assigned_by、memberships.user_id、memberships.invited_by）
- 无新表反向引用 Identity 表以外的对象
