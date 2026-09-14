# STEP 1-B / B0 — ACL Implementation Readiness

Status: **DESIGN PREPARATION — 不创建任何表**
来源：STEP 1-A Round 2 P1/P2-04 + Round 3 P2-02 冻结设计
配套：[CORE_DOMAIN_MODEL.md §1.3](./CORE_DOMAIN_MODEL.md)、[STEP1B_CONSTRAINT_MATRIX.md](./STEP1B_CONSTRAINT_MATRIX.md)、[STEP1B_TRIGGER_INVENTORY.md](./STEP1B_TRIGGER_INVENTORY.md)

---

## 1. 目标

`resource_permissions` 的主体引用必须满足：

1. `subject_type_id` 必须存在于 `acl_subject_types`（注册表，FK RESTRICT）
2. 注册表 STEP 1-B 白名单 = **`user` / `role` / `agent`**（P2-02：**无 `group`**）
3. `subject_id` 必须真实存在于对应表（trigger 校验，**无伪造 subject**）
4. tenant/space isolation、删除/归档/cleanup 规则完整
5. 注册表为 **platform-controlled registry**（**D-B14-12 = A，2026-09-13**）：受 `tg_acl_subject_types_protect` 保护 —— 运行时 INSERT / `key` UPDATE / DELETE 拒绝，退役走 `archived_at`；**不允许 Domain / Plugin / 普通业务代码 runtime 自由注册**，亦不得通过未来 API 任意扩展（**registry governance only，不构成 authorization evaluation**）

---

## 2. 数据模型（B1 DDL 形状）

```sql
CREATE TABLE acl_subject_types (
  id          uuid PRIMARY KEY DEFAULT uap_uuid_v7(),
  key         text NOT NULL CHECK (key ~ '^[a-z][a-z0-9_]{1,31}$'
                                   AND key IN ('user','role','agent')),  -- P2-02
  description text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  archived_at timestamptz
);
CREATE UNIQUE INDEX uq_acl_subject_types_key
  ON acl_subject_types (lower(key)) WHERE archived_at IS NULL;

CREATE TABLE resource_permissions (
  id              uuid PRIMARY KEY DEFAULT uap_uuid_v7(),
  resource_id     uuid NOT NULL REFERENCES resources(id) ON DELETE CASCADE,  -- 受控 purge 随删
  subject_type_id uuid NOT NULL REFERENCES acl_subject_types(id) ON DELETE RESTRICT,
  subject_id      uuid NOT NULL,
  action          text NOT NULL,
  effect          text NOT NULL CHECK (effect IN ('allow','deny')),
  conditions      jsonb,
  inherited       boolean NOT NULL DEFAULT false,
  expires_at      timestamptz,
  granted_by      uuid REFERENCES users(id) ON DELETE SET NULL,  -- D-B14-09 = A（2026-09-13）：actor attribution；非 ownership
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (resource_id, subject_type_id, subject_id, action)
);
```

> 注意：CK 同时放 key 正则 + 白名单枚举；`archived` 的 type 在 `WHERE archived_at IS NULL` 下从唯一索引消失（可重建同名 type）。

---

## 3. Subject 验证链（如何杜绝伪造 subject）

`tg_acl_subject_exists`（BEFORE INSERT OR UPDATE）：

```sql
CREATE FUNCTION enforce_acl_subject_exists() RETURNS trigger AS $$
DECLARE stype_key text;
BEGIN
  SELECT key INTO stype_key FROM acl_subject_types WHERE id = NEW.subject_type_id;
  IF stype_key IS NULL THEN
    RAISE EXCEPTION 'acl subject type % not registered', NEW.subject_type_id;
  END IF;
  IF    stype_key = 'user'  AND NOT EXISTS (SELECT 1 FROM users  WHERE id = NEW.subject_id) THEN
    RAISE EXCEPTION 'acl subject user % does not exist', NEW.subject_id;
  ELSIF stype_key = 'role'  AND NOT EXISTS (SELECT 1 FROM roles  WHERE id = NEW.subject_id) THEN
    RAISE EXCEPTION 'acl subject role % does not exist', NEW.subject_id;
  ELSIF stype_key = 'agent' AND NOT EXISTS (SELECT 1 FROM agents WHERE id = NEW.subject_id) THEN
    RAISE EXCEPTION 'acl subject agent % does not exist', NEW.subject_id;
  END IF;
  -- P2-02: 无 group 分支；未来启用路径见 §7
  RETURN NEW;
END $$ LANGUAGE plpgsql;
```

保证矩阵：

| 注入尝试 | 防线 |
|---|---|
| `subject_type_id` = 不存在的 type | FK RESTRICT + trigger RAISE |
| `subject_type_id` = `group`（若历史数据存在） | CK 白名单挡住（不可 INSERT） |
| `subject_id` = 随机 uuid（user） | trigger 查 users.id 失败 → RAISE |
| `subject_id` = 其它租户的 role/agent | **trigger 只做存在性校验**；跨租户语义由授权决策层基于 `resources.tenant_id` + role 的 `tenant_id` 归属校验（见 §5） |

---

## 4. 隔离（Tenant / Space Isolation）

- `resource_permissions` **不冗余 tenant_id/space_id**：隔离随其父 `resources`（resources 已有 NN tenant_id + space_id）
- 查询路径：按 `resources.tenant_id` / `resources.space_id` 过滤 → 命中资源 → 评估 ACL
- 决策时校验 subject 的归属范围：user 的 ACL 只在 user 属于该 tenant 的 active membership 时生效（应用层）；role 的 ACL 仅当 role.tenant_id = resource.tenant_id（或 platform role）时生效
- RLS（可选，Q1）：会话变量 `app.tenant_id` + `USING`；连接池内 `SET LOCAL` 后归还重置

---

## 5. 删除 / 归档 / Cleanup（P2-03 受控 purge）

| 事件 | 行为 | 机制 |
|---|---|---|
| **user 软删**（deleted_at） | ACL **保留**（历史授权可追溯） | 无动作 |
| **user 硬删**（retention purge） | 删除该 user 的全部 ACL | `tg_acl_user_hard_delete` AFTER DELETE ON users → `DELETE FROM resource_permissions WHERE subject_type_id=(user) AND subject_id=OLD.id` |
| **role 删除尝试** | **拒绝**（被 ACL 引用时） | `tg_acl_role_delete_block` BEFORE DELETE ON roles → 若被 resource_permissions 引用 RAISE |
| **role 归档**（archived_at） | deny 行不再参与决策；allow 行保留（审计追溯） | 授权决策层检查 role.archived_at（不改 ACL 数据） |
| **agent 归档** | 该 agent 的 ACL 临时到期 | trigger / 归档流程 `UPDATE resource_permissions SET inherited=true, expires_at=now() WHERE subject=agent` |
| **resource soft delete** | ACL 保留 | 无动作 |
| **resource controlled purge** | ACL 随删 | `resource_id → resources.id ON DELETE CASCADE` |
| **membership removed** | ACL **不**预先清理 | 授权阶段实时校验 membership，失败记 `audit_logs(reason='membership_removed')`；重加入自动恢复 |

---

## 6. 变更（grant/revoke）审计

- `resource_permissions` 写入/删除必须同事务写 `audit_logs`：actor、resource、subject、action、effect、granted_by
- CRITICAL 资源（classification=HIGHLY_CONFIDENTIAL）的 ACL 变更 risk_level=HIGH

---

## 7. 未来 group 启用路径（仅记录，B1 不实现 — P2-02）

```
1. CREATE TABLE groups (...)           -- 由未来授权需求驱动
2. INSERT acl_subject_types ('group')  -- 注册
3. 扩展 enforce_acl_subject_exists():  -- 增 ELSIF stype_key='group' → 查 groups.id
4. 增加 ACL group 测试（注册/存在性/删除/归档）
```

**B1 不创建 `groups` 表，不在任何 trigger 引用 `groups`（P2-02 强制）。**

---

## 8. 测试矩阵摘要（详见 TEST_MATRIX §7）

注册表白名单、user/role/agent subject 存在性、伪造 subject 拒绝、user 软删保留 ACL、user 硬删清理、role 删除被引用拒绝、role 归档 deny 失效、agent 归档 ACL 到期、resource purge 级联清理、group 在当前 schema 不存在。

---

## 9. R2 同步（2026-09-08 Decision Resolution Round 2）

- **DENY > ALLOW（R2-D-14，FROZEN SECURITY INVARIANT）**：同一 `(role, permission)` 并存 allow+deny → 最终 **DENY**；多角色命中时任一 deny → **DENY**。由 Authorization Layer 解释；DB 层仅存数据（PK 含 effect），**不在 trigger 中做授权解释**。
- **Permission scope-neutral（R2-D-15）**：permission = capability，不承担 tenant/space 授权边界；实例级边界来自 Membership / Role Scope / Request Context / Resource ACL。B1-3 不建 ABAC evaluator；`role_permissions.conditions` **storage-only**（存不解析）。
- **Platform binding（R3-D-07 FROZEN，Option A `platform_memberships`，未建表待批准）**：PLATFORM 层绑定载体已定 = `platform_memberships`（user+PLATFORM role，status active/revoked，last-admin 保护，grant/revoke 仅 active platform_admin 并审计）。授权链 Identity→Membership→Role→Role Scope→Permission 在平台层以此补齐；**该表落地前**，授权层对任何"平台级请求"仍必须 fail-closed（DENY）。本表 subject 验证链（user/role/agent）不受影响。

## 10. R4 同步（2026-09-08 D-07 Hardening — PMB-1..4）

- **effective_platform_admin（canonical）** = `pm.active ∧ u.active ∧ r.active ∧ r.scope='PLATFORM' ∧ r.key='platform_admin'`；授权层唯一判定依据；计数恒 ≥1（初始化后）由 `tg_pm_last_admin` + `tg_roles_pm_lifecycle` 双层强制（PMB-1）。
- Re-grant = UPDATE 本行（禁止 INSERT）；duplicate active grant 拒绝（PMB-3）。
- Bootstrap 一次性（PMB-2）；停用用户先 revoke、CASCADE 仅 purge 终态（PMB-4）。
- 平台级请求：无 effective 平台权限 → DENY（fail-closed），与 RBAC subject 验证链无关。

## 11. R5 同步（2026-09-08 Hardening — 平台用户生命周期三分层）

- **DB trigger**：无 users→platform_memberships 自动 revoke；停用 user 时 PM 行保持（不得依赖 DB 自动化）。
- **Application Service（正式 workflow）**：`deactivate(user)` = 单事务 { revoke 该 user 的 active PM（PMB-1 校验）→ 置 user 非 active → audit }；任一步失败 → 整体回滚（U-03）；`reactivate(user)` **不**恢复 PM —— 被撤销的平台权限不可因 reactivate 复活（U-02）。
- **Effective Authorization**：effective_platform_admin 谓词不变；user inactive → 永久 DENY —— 这是 fail-closed 防线，**不是** lifecycle revoke 的替代品（U-04）。
- Bootstrap：`platform_state` 单向状态机（0006）；普通 API 无 actor 伪造面（表无 actor 列）。
