# STEP 1-B / B1-3 — Trigger Inventory（Role & Permission Foundation）

Status: **PREP ONLY**
原则：**Trigger 只负责数据库完整性（Database Integrity）**，不做授权决策、不产生业务副作用。
来源：B0 `STEP1B_TRIGGER_INVENTORY.md`（B/C/D/E 组）+ B1-2 `DECISION_LOG.md` D-02

---

## 1. Trigger 清单

| # | name | table | timing / event | purpose | failure behavior | dependency | B1-3? |
|---|---|---|---|---|---|---|---|
| T1 | `tg_roles_set_updated_at` | roles | BEFORE UPDATE | `NEW.updated_at = now()` | —（纯赋值） | 本表 + `set_updated_at()`（B1-1 已有，**不重建**） | ✅ |
| T2 | `tg_roles_scope_shape` | roles | BEFORE INSERT OR UPDATE OF scope, tenant_id, space_id | 形状匹配（R-D-16）：`PLATFORM`→两者 NULL；`TENANT`→tenant_id 非空且 space_id NULL；`SPACE`→**tenant_id NULL** 且 space_id 非空 | RAISE → 回滚 | roles | ✅ |
| T3 | `tg_roles_is_system_protect` | roles | BEFORE **INSERT OR UPDATE OR DELETE** | R2-D-05：INSERT 时 `NEW.is_system` → 拒绝（运行时不可创建系统角色）；UPDATE/DELETE 时 `OLD.is_system OR NEW.is_system` → 无条件拒绝（含改 key/scope/归属/is_system/name/status、`true→false` 脱保、自定义角色 `false→true` 提权）。**0005 先 seed 后建本 trigger** | RAISE → 回滚 | roles | ✅ |
| T4 | `tg_tm_role_scope` | tenant_memberships | BEFORE INSERT OR UPDATE OF role_id, tenant_id | 引用 role 必须 `scope='TENANT' AND roles.tenant_id = 本行 tenant_id AND roles.status='active'`（R-D-06） | RAISE → 回滚 | roles + tenant_memberships | ✅（B1-3 才具备条件） |
| T5 | `tg_membership_role_scope` | memberships | BEFORE INSERT OR UPDATE OF role_id, space_id | 引用 role 必须 `scope='SPACE' AND roles.space_id = 本行 space_id AND roles.status='active'` | RAISE → 回滚 | roles + memberships | ✅（B1-3 才具备条件） |
| T6 | `tg_pm_role_scope` | platform_memberships | BEFORE INSERT OR UPDATE OF role_id, status | R3-D-07：引用 role 必须 `scope='PLATFORM' AND roles.status='active'`；结果态 active 时 `users.status='active'` | RAISE → 回滚 | roles + platform_memberships + users | ⏳（R3 设计冻结，表随 roles 后建） |
| T7 | `tg_pm_last_admin` | platform_memberships | BEFORE UPDATE OR DELETE | R3-D-07：禁止使 active `platform_admin` 绑定数从 >0 变为 0（防平台自锁）；首行 bootstrap（0→1）允许 | RAISE → 回滚 | platform_memberships + roles | ⏳（同上） |
| T8 | `tg_roles_pm_lifecycle` | roles | BEFORE UPDATE OF status（DELETE 兜底） | R4 PMB-1（Role 侧纵深防线）：`platform_admin` 行（`scope='PLATFORM' AND key='platform_admin'`）在**存在 active PM 绑定引用**时不得 `active→非active`，也不得 DELETE（与 T3 is_system 保护重叠但不同质：T3 保系统角色不可变，T8 保信任根计数 ≥1） | RAISE → 回滚 | roles + platform_memberships | ⏳（随 platform_memberships） |

**不建**：
- `permissions` / `role_permissions` 的 updated_at trigger → 冻结设计**无 updated_at 列**（字典/关系表）
- 任何 role_permissions 业务 trigger

## 2. Enforcement 分层（明确，不留模糊）

| 层 | 职责 | 机制 |
|---|---|---|
| **Database（T2–T5）** | **引用完整性**：scope 与归属匹配、系统角色保护、角色形状 | trigger RAISE |
| **Application Authorization** | **授权决策**：default deny、deny 优先、ABAC 条件求值 | `core/policy` / `core/permission`（B1-3 不实现求值器） |

> 两层**必须同时存在**：DB 保证"数据不越界"，应用层保证"决策不默认放行"（含 **R-D-14：同一 (role,permission) 并存 allow/deny → 授权层裁决 DENY**）。
> **不能只靠 trigger 做授权**：trigger 不知道请求上下文，也不应写审计。

**明确：`role_permissions` 不需要系统角色保护 trigger**（R-D-05）：B1-3 无任何应用写入路径可改 seed 权限绑定；权限变更 = 新 migration revision（人工审计）。避免多余 trigger。

## 3. 明确禁止的 Trigger 行为（B1-3 及后续）

Trigger **不得**：
- 修改权限（自动 grant/revoke）
- 自动提升角色（如"首个用户自动 admin"）
- 自动复制 Membership（tenant → space 自动建成员）
- 自动创建用户 / Space / Tenant
- 写 `audit_logs`（审计由应用层写入）
- 调用外部 API / AI
- 产生任何业务副作用（发事件、改状态机）
- 跨租户复制数据

Trigger **只能**：
- 校验数据完整性（形状、scope、归属、存在性）
- 维护 `updated_at`

## 4. 为什么不用 Composite FK

| 方案 | 评估 |
|---|---|
| **Trigger（采用）** | PG 无跨表 CHECK；trigger 可读 roles 行做 scope/归属校验；无需在 membership 冗余 role scope 列 |
| Composite FK（`(role_id, tenant_id) → roles(id, tenant_id)`） | 需 roles 上有唯一键 `(id, tenant_id)`，且 TENANT role 的 tenant_id 非空；SPACE role 用 space_id 又不同列 → 无法统一；且会把 scope 语义塞进物理约束，变更成本高 |
| Application only | 不满足"数据库级安全约束"要求（B1-3 P1） |

## 5. 风险

| 项 | 说明 | 级别 |
|---|---|---|
| trigger 抛错类型 | PL/pgSQL RAISE → psycopg `RaiseException` → SQLAlchemy **ProgrammingError**（不是 IntegrityError） | P3（测试断言需兼容两者） |
| `is_system` 保护过强 | 合法定制（如重命名内置角色）被拒 → 需 D-05 定义流程 | P2 |
| T4/T5 每行一次 roles 查询 | 批量导入成员时逐行子查询（roles PK 查找，代价低） | P3 |
| 回填期间 trigger 状态 | B1-3 回填 role_id 时可临时禁用/或确保回填值合法（建议：先建 roles+seed → 回填 → 再挂 trigger → 再 SET NOT NULL + FK） | P2（migration 顺序需在实施时确认） |

## 6. Migration 顺序建议（未来 0005，本阶段不创建）

```
1) CREATE TABLE permissions / roles / role_permissions
2) seed 内置角色与平台权限（幂等）
3) 回填 tenant_memberships.role_id / memberships.role_id（NULL → 内置角色；失败即中止）
4) 创建 T1–T5 trigger（此时 roles 已存在）
5) ALTER ... SET NOT NULL role_id
6) ALTER ... ADD CONSTRAINT fk_tm_role / fk_membership_role (RESTRICT)
7) 一致性验证（无 NULL、无孤儿 role_id、scope 全部匹配）
```
> 顺序 3→4 保证回填值合法；4→5/6 保证后续写入受约束。**不修改 0004。**

### R5 增补 trigger（2026-09-08 Hardening — P1-01）

| # | name | table | timing / event | purpose | failure behavior | dependency | B1-3? |
|---|---|---|---|---|---|---|---|
| T9 | `tg_platform_state_guard` | platform_state | BEFORE INSERT OR UPDATE OR DELETE | R5-1：仅允许 seed 插入 uninitialized 单例；仅允许 `uninitialized→initialized`（initialized_at 非空）；DELETE/再插/回退 → 拒绝 | RAISE → 回滚 | platform_state | ✅（0006） |
| T10 | `tg_pm_bootstrap_gate` | platform_memberships | BEFORE INSERT | R5-1：PM INSERT 仅当 state=initialized 或（uninitialized 且 PM 无行）；初始化后无 "uninitialized+empty" 分支可被伪造 | RAISE → 回滚 | platform_state + platform_memberships | ✅（0006） |
| — | `tg_platform_state_set_updated_at` | platform_state | BEFORE UPDATE | updated_at 维护（复用 set_updated_at） | 纯赋值 | set_updated_at（0003） | ✅（0006） |
