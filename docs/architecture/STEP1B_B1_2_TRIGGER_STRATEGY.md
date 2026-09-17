# STEP 1-B / B1-2 — Trigger Strategy（Tenant / Space Foundation）

Status: **PREP ONLY**
默认原则：**不创建新的跨表业务 trigger**；仅实现冻结设计已定义的 trigger。
来源：B0 `STEP1B_TRIGGER_INVENTORY.md` §1（A / F / D / E 组）。

---

## 1. B1-2 trigger 清单

| # | name | table | timing / event | purpose | failure | dependency | B1-2? |
|---|---|---|---|---|---|---|---|
| T1 | `tg_tenants_set_updated_at` | tenants | BEFORE UPDATE | `NEW.updated_at = now()` | — | 本表 + `set_updated_at()` | ✅ |
| T2 | `tg_spaces_set_updated_at` | spaces | BEFORE UPDATE | 同上 | — | 本表 | ✅ |
| T3 | `tg_tenant_memberships_set_updated_at` | tenant_memberships | BEFORE UPDATE | 同上 | — | 本表 | ✅ |
| T4 | `tg_memberships_set_updated_at` | memberships | BEFORE UPDATE | 同上 | — | 本表 | ✅ |
| T5 | `tg_membership_tenant_consistency` | memberships | BEFORE INSERT OR UPDATE OF tenant_id, space_id | 校验 `NEW.tenant_id = (SELECT tenant_id FROM spaces WHERE id = NEW.space_id)`（冗余列不漂移） | RAISE → 回滚 | spaces + memberships | ✅ |
| T6 | `tg_tm_role_scope` | tenant_memberships | BEFORE INSERT OR UPDATE OF role_id, tenant_id | 校验 role `scope='TENANT' AND roles.tenant_id = 本行 tenant_id` | RAISE → 回滚 | **roles（B1-3）** | ⏳ B1-3（**D-02**） |
| T7 | `tg_membership_role_scope` | memberships | BEFORE INSERT OR UPDATE OF role_id, space_id | 校验 role `scope='SPACE' AND roles.space_id = 本行 space_id` | RAISE → 回滚 | **roles（B1-3）** | ⏳ B1-3（**D-02**） |

- `set_updated_at()` 函数由 B1-1 的 `0003` 创建 → **复用，不重建**
- T5 是**冻结设计已定义**的跨表校验 trigger（非本阶段新发明），且只做**一致性校验**（不写其它表、不产生副作用）
- T6/T7 依赖 roles 表 → **B1-3** 建立（D-02）；B1-2 **不建**（禁止引用不存在的表）

### 1.1 B1-2 Role Scope 窗口：应用层 fail-closed 强制（D-02）

B1-2 无 `roles` 表 → DB 无法做 FK 与 scope 校验。窗口期内 **Authorization Layer 必须拒绝**：

| 场景 | 期望 |
|---|---|
| 不存在 role（role_id 为 NULL 或引用不存在的角色） | **DENY** |
| role scope ≠ TENANT 用于 `tenant_memberships` | **DENY** |
| role scope ≠ SPACE 用于 `memberships` | **DENY** |
| 非 TENANT role 用于 tenant_memberships | **DENY** |
| 非 SPACE role 用于 memberships | **DENY** |

> 实现位置：授权层（Core `core/policy` / `core/permission`），**不是** DB trigger。B1-3 完成后由 DB trigger + 应用层双重强制。

---

## 2. 明确不创建的 trigger（需报告才可实现）

| 候选 | 为何不建 |
|---|---|
| 租户删除 → 级联清理 spaces | 违反 RESTRICT 原则；清理走 archive→soft delete→purge job（应用层） |
| Space 软删 → 自动清 memberships | 同上（purge job 显式执行，每批 ≤1000 并写 audit） |
| Space 删除 → 同步置 resources.deleted_at | 属 Resource 阶段（B1-3+），且冻结设计为**异步 job** |
| 成员变更 → 自动写 audit_logs | 审计由应用层/服务层写入（审计不可变表由应用 INSERT，非 trigger） |
| 成员移除 → 清理 resource_permissions | 冻结设计明确"不预先清理 ACL"，授权实时校验 |

> 以上若未来确需实现，**必须先提出并说明理由**（B1-2 PREP 阶段只记录，不实现）。

---

## 3. 与 B1-1 的关系

- B1-1 已创建 `set_updated_at()` 函数与 5 个 Identity trigger → **不修改**
- B1-2 新增 4 个 updated_at trigger（T1–T4）绑定同函数
- 无 trigger 修改 B1-1 表

---

## 4. 风险

| 项 | 说明 | 级别 |
|---|---|---|
| `tg_membership_tenant_consistency` 对批量 UPDATE 的性能 | 每行一次子查询（spaces PK 查找，代价低） | P3 |
| trigger 顺序 | 同一表多 BEFORE trigger 按名称顺序执行；updated_at 与一致性校验互不干扰 | P3 |
| role scope trigger 缺失期（B1-2 交付后至 B1-3 完成前） | **D-02 已裁定**：DB 无校验，由**应用层 fail-closed** 替代（见 §1.1）；B1-3 补 DB trigger。**B1-2 的 role_id 不构成完整授权安全边界** | **P2→已缓解**（应用层强制；需在审计中确认实现项） |
| `spaces.owner_id` ON DELETE | **D-03 PROPOSED**：建议 SET NULL，**未批准前不实现** | 待人工批准 |
| RLS | **D-04**：不启用、不创建 policy、不改 PG 配置（OPEN DESIGN QUESTION） | 后续阶段决定 |
