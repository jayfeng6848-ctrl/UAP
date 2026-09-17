# STEP 1-B / B0 — Trigger Inventory

Status: **DESIGN PREPARATION — 不创建任何 trigger**
来源：STEP 1-A 冻结设计（Round 2 P1/P2-04 + Round 3 P2-01/02/03）
配套：[STEP1B_SCHEMA_DEPENDENCY.md](./STEP1B_SCHEMA_DEPENDENCY.md)（§7 触发 phase 先决）

> 每个 trigger 给出：name / table / timing / event / purpose / failure behavior / dependency。
> **任何 trigger 不得引用尚未存在的表；`groups` 不出现在任何 trigger dependency（P2-02）。**

---

## 1. Inventory

### A. `updated_at` 维护（每张带 updated_at 的表）

| 项 | 值 |
|---|---|
| name | `tg_<table>_set_updated_at` |
| table | users, identities, credentials, devices, sessions, tenants, spaces, tenant_memberships, memberships, roles, resources, agents, tools, ai_providers, ai_models, ai_routes, ai_policies（凡有 updated_at 者） |
| timing/event | BEFORE UPDATE |
| purpose | `NEW.updated_at = now()`；应用层不依赖 |
| failure | 无（纯赋值）；trigger 异常则 UPDATE 失败 → 事务回滚 |
| dependency | 无（函数 `set_updated_at()` 在 P00 建） |

### B. `roles` scope 形状校验

| 项 | 值 |
|---|---|
| name | `tg_roles_scope_shape` |
| table | roles |
| timing/event | BEFORE INSERT OR UPDATE |
| purpose | scope ↔ tenant_id/space_id 必须匹配：`PLATFORM`→两者 NULL；`TENANT`→tenant_id 非空且 space_id NULL；`SPACE`→space_id 非空 |
| failure | RAISE EXCEPTION → INSERT/UPDATE 失败回滚 |
| dependency | roles（P04 后可建） |

### C. `roles.is_system` 保护

| 项 | 值 |
|---|---|
| name | `tg_roles_is_system_protect` |
| table | roles |
| timing/event | BEFORE UPDATE OR DELETE |
| purpose | `is_system=true` 的行禁止修改/删除 |
| failure | RAISE EXCEPTION → 回滚 |
| dependency | roles |

### D. `tenant_memberships.role_id` scope/归属校验（P2-01 关键防线）

| 项 | 值 |
|---|---|
| name | `tg_tm_role_scope` |
| table | tenant_memberships |
| timing/event | BEFORE INSERT OR UPDATE OF role_id, tenant_id |
| purpose | 引用 role 必须 `scope='TENANT' AND roles.tenant_id = NEW.tenant_id`；默认角色只能落到 tenant_member/tenant_admin |
| failure | RAISE（错误场景：指向 PLATFORM/SPACE role、其它租户 role 均被拒） |
| dependency | roles + tenant_memberships（P05 后可建；**早于 seed**） |

### E. `memberships.role_id` scope/归属校验（P2-01）

| 项 | 值 |
|---|---|
| name | `tg_membership_role_scope` |
| table | memberships |
| timing/event | BEFORE INSERT OR UPDATE OF role_id, space_id |
| purpose | 引用 role 必须 `scope='SPACE' AND roles.space_id = NEW.space_id` |
| failure | RAISE（指向 TENANT/PLATFORM role 或其它空间 role 被拒） |
| dependency | roles + memberships（P05） |

### F. `memberships.tenant_id` 冗余一致性

| 项 | 值 |
|---|---|
| name | `tg_membership_tenant_consistency` |
| table | memberships |
| timing/event | BEFORE INSERT OR UPDATE OF tenant_id, space_id |
| purpose | `NEW.tenant_id = (SELECT tenant_id FROM spaces WHERE id = NEW.space_id)` |
| failure | RAISE → 回滚 |
| dependency | spaces + memberships（P05） |

### F2. `resources` tenant / space 冗余一致性（**R1 增补 — D-B14-10 Human Decision A-1，2026-09-13**）

> 命名说明：为避免重排既有 **A–M** 编号，本条以 **F2** 登记（与 F 同族：冗余归属一致性校验）。**G/H/I/J 的 P09 后定义完全未改动。**

| 项 | 值 |
|---|---|
| name | `tg_resources_tenant_space_consistency` |
| table | resources |
| timing/event | BEFORE INSERT OR UPDATE（覆盖 `tenant_id` / `space_id` 变更） |
| purpose | `NEW.space_id IS NULL` → 放行；`NEW.space_id IS NOT NULL` → 要求 `NEW.tenant_id = (SELECT tenant_id FROM spaces WHERE id = NEW.space_id)`，否则拒绝 |
| failure | RAISE → 回滚（Tenant-A + Tenant-B 的 Space 被拒） |
| dependency | resources + spaces（**均已存在**） |
| 禁引用 | 不引用 `agents` / `ai_*` / `tools` / `events` / `audit_logs`（无未来对象依赖） |
| **earliest phase** | **P06 / B1-4** |
| phase 依据 | ① `resources` 在 **P06** 创建；② `spaces` 已在 **P05 / B1-2** 存在（migration `0004`）；③ **不依赖任何未来阶段对象** |
| 边界（强制声明） | **structural integrity only** —— 仅拒绝非法归属组合；**不承担 authorization evaluation**（授权判定仍在 Authorization Layer）；**不引入 RLS** |

### C2. `acl_subject_types` 平台注册表保护（**R4 增补 — D-B14-12 Human Decision A，2026-09-13**）

> 命名说明：为避免重排既有 **A–M** 编号，本条以 **C2** 登记（与 C 同族：**受保护行不被运行期改写/删除**）。**G/H/I/J 的 P09 后定义完全未改动。**

| 项 | 值 |
|---|---|
| name | `tg_acl_subject_types_protect` |
| table | acl_subject_types |
| timing/event | BEFORE INSERT OR UPDATE OR DELETE |
| purpose | **platform-controlled registry 保护**：运行时 INSERT 拒绝；`key` UPDATE 拒绝（`description` 等非受控列允许）；DELETE 拒绝（退役走 `archived_at`） |
| failure | RAISE → 回滚 |
| dependency | acl_subject_types（**已存在**） |
| 禁引用 | 不引用 `resource_permissions` / `users` / `roles` / `agents` / `permissions`（**无未来对象依赖**，亦不构成 authorization 判定） |
| **earliest phase** | **P06 / B1-4** |
| phase 依据 | ① `acl_subject_types` 在 **P06 / B1-4** 创建；② 不依赖任何未来阶段对象；③ 与既有 C（`roles.is_system` 保护，P04 = 该表所属 phase）口径一致 |
| 边界（强制声明） | **registry governance only** —— 仅强制平台受控注册表的写入面；**不承担 authorization evaluation**，**不演变为 Domain authorization**；registry 不允许 Domain / Plugin / 普通业务代码 runtime 自由注册 |
| 受控写入（**W-3 决议**） | 合法 registry 行**仅经 migration 建立**（schema governance，非 Domain runtime registration）；既有先例：`0005` 先 INSERT 内置 role → 后建 `tg_roles_is_system_protect`；`0006` 先 INSERT `platform_state` → 后建 `tg_platform_state_guard`。P13 seed 的受控路径见 `B1-4_DESIGN.md` §8.1 |

### G. ACL subject 存在性（P1/P2-04 + P2-02）

| 项 | 值 |
|---|---|
| name | `tg_acl_subject_exists` |
| table | resource_permissions |
| timing/event | BEFORE INSERT OR UPDATE OF subject_type_id, subject_id |
| purpose | subject_id 必须存在于 subject_type 对应表：user→users.id / role→roles.id / agent→agents.id；type 必须已注册 |
| failure | RAISE（伪造 subject 被拒）；注册表无该 type → FK RESTRICT 先拦 |
| dependency | resource_permissions + acl_subject_types + users + roles + agents → **最早 P09 后**（agents 表存在） |
| 禁引用 | **不引用 groups（P2-02）** |

### H. user 硬删 → 清理其 ACL

| 项 | 值 |
|---|---|
| name | `tg_acl_user_hard_delete` |
| table | users |
| timing/event | AFTER DELETE（仅 retention purge 触发硬删） |
| purpose | `DELETE FROM resource_permissions WHERE subject_type_id=(SELECT id FROM acl_subject_types WHERE key='user') AND subject_id=OLD.id` |
| failure | DELETE 失败回滚（硬删流程整体回滚，安全） |
| dependency | resource_permissions + acl_subject_types（P09 后） |

### I. role 被 ACL 引用时禁删

| 项 | 值 |
|---|---|
| name | `tg_acl_role_delete_block` |
| table | roles |
| timing/event | BEFORE DELETE |
| purpose | `IF EXISTS (SELECT 1 FROM resource_permissions WHERE subject_type_id=(role type) AND subject_id=OLD.id) THEN RAISE` —— 复刻 RESTRICT 语义（FK 在 type 表上，需业务 trigger） |
| failure | RAISE → 删除被拒 |
| dependency | resource_permissions + acl_subject_types（P09 后） |

### J. agent 归档 → ACL 到期

| 项 | 值 |
|---|---|
| name | `tg_agent_acl_expire` |
| table | agents |
| timing/event | AFTER UPDATE OF status（→ archived）或 AFTER DELETE |
| purpose | 使该 agent 的 ACL 到期：`UPDATE resource_permissions SET inherited=true, expires_at=now() WHERE subject=agent`（agent 行不删，仅失效） |
| failure | 归档事务失败回滚（安全） |
| dependency | resource_permissions（P09 后） |

### K. 版本不可变（agent_versions / tool_versions）

| 项 | 值 |
|---|---|
| name | `tg_version_immutable`（agent_versions / tool_versions 共用同一名） |
| table | agent_versions / tool_versions |
| timing/event | BEFORE UPDATE OR DELETE |
| purpose | `status='published'` 的行禁止 UPDATE/DELETE（deprecate/revoke 走应用层状态迁移 + 权限） |
| failure | RAISE → 回滚 |
| dependency | 本表 |

### L. audit_logs 不可变

| 项 | 值 |
|---|---|
| name | `tg_audit_immutable` |
| table | audit_logs |
| timing/event | BEFORE UPDATE OR DELETE |
| purpose | 直接 RAISE —— append-only 双保险（另一道是 DB 角色仅 INSERT/SELECT） |
| failure | RAISE → 任何 UPDATE/DELETE 失败 |
| dependency | audit_logs（P10） |

### M. 可选：events 无 DB trigger

events 的 claim 状态迁移由**应用层 CAS UPDATE 完成**，不加 trigger（避免触发逻辑与 CAS 竞争）。依赖在应用侧 worker 进程。

---

## 2. 汇总表

| # | trigger | table | 时机 | 依赖已存在 | 最早 phase | 必须早于 seed |
|---|---|---|---|---|---|---|
| A | tg_*_set_updated_at | 各带 updated_at 表 | BEFORE UPDATE | 本表 | 表建时 | ✅ |
| B | tg_roles_scope_shape | roles | BEFORE I/U | roles | P04 | ✅ |
| C | tg_roles_is_system_protect | roles | BEFORE U/D | roles | P04 | ✅ |
| D | tg_tm_role_scope | tenant_memberships | BEFORE I/U | roles, tenant_memberships | P05 | ✅ |
| E | tg_membership_role_scope | memberships | BEFORE I/U | roles, memberships | P05 | ✅ |
| F | tg_membership_tenant_consistency | memberships | BEFORE I/U | spaces, memberships | P05 | ✅ |
| **F2** | **tg_resources_tenant_space_consistency** | **resources** | **BEFORE I/U** | **resources, spaces** | **P06 / B1-4**（R1 增补 D-B14-10 A-1） | ✅ |
| **C2** | **tg_acl_subject_types_protect** | **acl_subject_types** | **BEFORE I/U/D** | **acl_subject_types** | **P06 / B1-4**（R4 增补 D-B14-12 A） | ✅ |
| G | tg_acl_subject_exists | resource_permissions | BEFORE I/U | + users/roles/**agents** | **P09 后** | ✅ |
| H | tg_acl_user_hard_delete | users | AFTER DELETE | resource_permissions | P09 后 | ✅ |
| I | tg_acl_role_delete_block | roles | BEFORE DELETE | resource_permissions | P09 后 | ✅ |
| J | tg_agent_acl_expire | agents | AFTER U/D | resource_permissions | P09 后 | ✅ |
| K | tg_version_immutable | agent/tool_versions | BEFORE U/D | 本表 | 表建时 | ✅ |
| L | tg_audit_immutable | audit_logs | BEFORE U/D | audit_logs | P10 | ✅ |
| M | （events 无 trigger） | events | — | — | — | — |

**没有 trigger 需要 seed 之后才创建**（全部必须在 P13 seed 前就位，见 DEPENDENCY §7）。

---

## 3. 一致性检查

- **不引用不存在表**：G/H/I/J 依赖 agents/resource_permissions 等，均在 P09 后建 —— 满足"trigger 不得引用未建表"
- **groups**：本清单无任何 trigger 依赖 `groups`（P2-02）✅
- **R1 增补（2026-09-13 · D-B14-10 = A-1）**：新增 **F2** `tg_resources_tenant_space_consistency`（P06 / B1-4）。
  该条**仅依赖 `resources` + `spaces`（均已存在）**，**不含任何未来对象**；**G / H / I / J 的「P09 后」定义未改动**，
  既有相位顺序亦未重排。F2 与 F **同族**（冗余归属一致性），但**边界不同**：F2 = **structural integrity only**，
  不做 authorization evaluation，不引入 RLS。
- 与 CORE_DOMAIN_MODEL / ACL_STRATEGY / SEED_STRATEGY 的 trigger 描述一致 ✅
- **R4 增补（2026-09-13 · D-B14-12 = A）**：新增 **C2** `tg_acl_subject_types_protect`（**P06 / B1-4**）。
  该条**仅依赖 `acl_subject_types`（P06 创建，已存在）**，**不含任何未来对象**；**G / H / I / J 的「P09 后」定义未改动**，
  既有相位顺序亦未重排。C2 与 C **同族**（受保护行不可被运行期改写/删除），但**边界不同**：C2 = **registry governance only**，
  不做 authorization evaluation，**不替换** G/H/I/J 的主体存在性校验。
- application-layer 行为（设备 revoked 级联会话、events CAS claim）**不落 DB trigger**（设计文档明确应用层实现，避免跨表 trigger 复杂度）
