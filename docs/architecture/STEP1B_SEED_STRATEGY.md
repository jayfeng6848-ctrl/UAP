# STEP 1-B / B0 — Seed Strategy（内置角色 / 权限 / ACL 初始化）

Status: **DESIGN PREPARATION — 不创建任何数据**
来源：STEP 1-A Round 3 冻结设计（P2-01 / P2-02）
配套：[STEP1B_SCHEMA_DEPENDENCY.md](./STEP1B_SCHEMA_DEPENDENCY.md)（P13 phase）

> 本文档定义 B1 **P13 Seed** 的内容与顺序。所有 FK/trigger 先于 seed 就位（见 DEPENDENCY §7/§8）。

---

## 1. Seed 总顺序（按 FK 依赖修正）

```
[1] acl_subject_types        (user / role / agent)         -- root，最先
[2] permissions              (平台权限字典)                -- root
[3] platform_admin role      (PLATFORM scope, 全局 1 行)   -- 依赖: roles 表
[4] 首租户 + 首管理员用户     (bootstrapping 主体)
[5] tenant_admin / tenant_member   (TENANT scope, 每租户 1 行)
[6] tenant_memberships       (首管理员 → tenant_member/tenant_admin)
[7] 首空间
[8] space_admin / space_member     (SPACE scope, 每空间 1 行)
[9] memberships              (首成员 → space_admin)
[10] role_permissions        (内置角色 ↔ 权限绑定，含 deny 行)
```

> 用户草案顺序 `permissions → roles → role_permissions → tenant → tenant_memberships → spaces → memberships` 的**偏差说明**：真实依赖要求 acl_subject_types 最先（root 且被 resource_permissions 引用）；roles 在 tenant 之前（role 的 tenant_id 可 NULL/平台播种后仍可指向新租户，但**每租户内置角色必须等租户存在**，因此租户播种拆为"租户行 → 其 tenant 级角色 → membership"两步）。

**引导（bootstrap）顺序**（新建租户的运行时流程，非一次性 seed）：
```
create tenant
  → seed tenant_admin + tenant_member (scope=TENANT, tenant_id=租户)
  → create owner user (users)
  → insert tenant_memberships (user, role_id=tenant_admin, status='active')
  → create default space
  → seed space_admin + space_member (scope=SPACE, space_id=空间)
  → insert memberships (owner, role_id=space_admin)
```

---

## 2. 内置角色目录（P2-01 最终态，scope 严格正确）

| key | scope | tenant_id | space_id | is_system | 播种位置 | 用途 |
|---|---|---|---|---|---|---|
| `platform_admin` | **PLATFORM** | NULL | NULL | true | 全局 1 行（首次 seed） | 平台根管理 |
| `tenant_admin` | **TENANT** | 该租户 id | NULL | true | 每租户创建时 | 租户管理 |
| `tenant_member` | **TENANT** | 该租户 id | NULL | true | 每租户创建时 | **`tenant_memberships.role_id` 默认** |
| `space_admin` | **SPACE** | 冗余可空 | 该空间 id | true | 每空间创建时 | 空间管理 |
| `space_member` | **SPACE** | 冗余可空 | 该空间 id | true | 每空间创建时 | **`memberships.role_id` 默认** |

**scope 正确性验证**（B1 测试）：
- `tenant_memberships.role_id` 指向 `tenant_member`/`tenant_admin` → scope=TENANT ✅
- `memberships.role_id` 指向 `space_member`/`space_admin` → scope=SPACE ✅
- `platform_admin` 永不被 membership 引用 ✅

**禁止恢复旧 `member` 角色名作为默认**（P2-01）。文档中出现的 `member`（如 permission 示例 key `member.manage`、reason `not_tenant_member`）是词典/错误码，不是角色默认值。

---

## 3. 默认角色落地（应用层 + trigger 双保险）

```sql
-- 应用层 INSERT（角色默认由应用代码显式传入；不在 DB 设 DEFAULT 指向 role，避免角色未创建时 FK 失败）
INSERT INTO tenant_memberships (id, tenant_id, user_id, role_id, status, ...)
VALUES (uap_uuid_v7_py(), $tenant, $user,
        (SELECT id FROM roles WHERE tenant_id=$tenant AND key='tenant_member' AND scope='TENANT'),
        'active', ...);

INSERT INTO memberships (id, tenant_id, space_id, user_id, role_id, status, ...)
VALUES (uap_uuid_v7_py(), $tenant, $space, $user,
        (SELECT id FROM roles WHERE space_id=$space AND key='space_member' AND scope='SPACE'),
        'active', ...);
```

DB 层防线：`tg_tm_role_scope` / `tg_membership_role_scope` trigger 拒绝任何指向错误 scope/异租户/异空间 role 的写入（见 TRIGGER_INVENTORY）。

### 必须被拒绝的错误场景（seed 与运行时同规则）

| 场景 | 期望 |
|---|---|
| `tenant_memberships.role_id → PLATFORM role`（platform_admin） | trigger 拒绝 |
| `tenant_memberships.role_id → SPACE role`（space_admin） | trigger 拒绝 |
| `tenant_memberships.role_id → 其它租户的 tenant_member` | trigger 拒绝（tenant_id 不匹配） |
| `memberships.role_id → TENANT role`（tenant_member） | trigger 拒绝 |
| `memberships.role_id → PLATFORM role` | trigger 拒绝 |
| `memberships.role_id → 其它空间的 space_member` | trigger 拒绝（space_id 不匹配） |

---

## 4. 初始 permissions 字典（seed 示例，B1 定稿）

seed 仅注入**平台级系统权限**；域级权限由 Domain 层注册（不在本阶段）：

```
system.*                    平台系统操作
tenant.read / tenant.manage
space.read  / space.manage
member.read / member.manage
resource.read / resource.write / resource.delete
agent.execute / tool.execute
audit.read
```

> 具体清单 B1 定稿前由人工审计确认 —— 本文档只给形状：`key` 满足正则 `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$`；`is_system=true`。

> **边界声明（O-5 澄清，非规范性，不改变任何冻结决策）**：上列示例属于**未来 `permissions` 表（平台级权限字典，P13）**的 seed 草稿，**仅用于说明 `key` 的形状**；
> **不构成 B1-4 `resource_permissions.action` 的 vocabulary 冻结**，亦不得迁移为该列的取值约束（后者当前**仅 NOT NULL**，语义未冻结；**D-B14-08 = FROZEN — A（2026-09-13）**：B1-4 **零新增 semantic/format contract**）。

---

## 5. ACL Subject 初始 seed（P2-02）

```sql
INSERT INTO acl_subject_types (id, key) VALUES
  (uap_uuid_v7(), 'user'),
  (uap_uuid_v7(), 'role'),
  (uap_uuid_v7(), 'agent');
```

- **不注册 `group`**；`groups` 表不存在（P2-02）
- 未来启用路径（仅记录，不实现）：`CREATE groups` → 注册 `group` → 扩展 `tg_acl_subject_exists` → 增补测试

---

## 6. Seed 幂等与重放

| 规则 | 说明 |
|---|---|
| 幂等 | seed 以 `ON CONFLICT` / `WHERE NOT EXISTS` 保护：`platform_admin`、acl 三行、permissions 字典只插一次 |
| 失败重试 | seed 在单事务执行；失败整体回滚，无半成品 |
| 审计 | seed 事件写 `audit_logs`（actor=`system`） |
| 无用户敏感数据 | seed 不含真实凭据；首管理员密码由 onboarding 流程设置（非 seed） |

---

## 7. 依赖与次序核对

- seed 前必须有：全部表（P01–P10）+ 全部 trigger（P11）+ 全部 index（P12）—— trigger 必须早于 seed（见 DEPENDENCY §7）
- seed 依赖表：`acl_subject_types`（root）、`permissions`（root）、`roles`、`users`、`tenants`、`spaces`、`tenant_memberships`、`memberships`、`role_permissions`
- `role_permissions` 需在 roles+permissions 有数据后插
- 域扩展/资源/事件 seed：本阶段无

---

## R2 增补（2026-09-08 Decision Resolution Round 2 同步）

- **"定义 system role" ≠ "授予 system role"**：seed 只创建角色行与 role_permissions 绑定；**不**给任何用户授予角色（无用户会因 seed 获得平台/租户/空间权限）。
- 平台管理员授予 = **R3-D-07（FROZEN，Option A `platform_memberships`）**：seed 只创建 `platform_admin` 角色行（**不**绑定任何 user）；首名平台管理员的绑定由**部署 bootstrap（CLI，actor='system'，写 audit）** 写入 `platform_memberships`；后续 grant/revoke/transfer 由 active platform_admin 执行并审计。**该表落地前**任何人（含 tenant/space admin）都无平台权限（default deny）。
- `tenant_member` / `space_member` 是 TENANT / SPACE scope 角色，**绝不可能被 seed 成 PLATFORM role**（scope 由 seed 语句固定；trigger 形状校验拒绝任何越界）。
- 每租户/每空间的系统角色在**租户/空间创建时**播种（onboarding），`0005` 只负责为**既有** tenant/space 行补种 + 回填（R2-D-08 顺序）。
- 幂等识别键 = `scope + tenant/space ownership + key`（与三条部分唯一索引一致）；重复执行不重复创建（R2 复核：唯一谓词**不含 archived** → seed 冲突即失败，不做"upsert 覆盖"，保证 seed 确定性）。

## R4 增补（2026-09-08 D-07 Hardening — Bootstrap 定稿）

- **Bootstrap 一次性规则**（PMB-2）：条件 = `platform_memberships` 行数=0；行数=0 ⟺ 未初始化（last-admin 不变量保证初始化后恒 ≥1 行）→ **无需状态表**。首行写入 + `audit_logs(action='platform.admin.bootstrap', actor='system')` 同事务；成功后路径永久关闭。
- 普通 API/seed 不得扮演 bootstrap：seed 只建角色行与 role_permissions，**永不写 PM 行**；bootstrap 由受信 CLI（独立凭据）执行。
- 丢失恢复（运行时不可达，PMB-1）：如确需 → 独立维护程序 + 人工批准 + audit `platform.admin.recovery`；默认无恢复 API。

## R5 增补（2026-09-08 Hardening — Bootstrap 定稿：显式状态机）

- bootstrap 条件改双前置：`platform_state.bootstrap_state='uninitialized'`（权威判据）**AND** `platform_memberships` 无行（次前置）。
  原子流程 = 插首行 PM → 翻转 `platform_state` 为 initialized（initialized_at=now()）→ audit `platform.admin.bootstrap` → COMMIT（单事务）。
- seed（migration 0006）只写 `platform_state(id=1,'uninitialized')`；**永不**写 initialized —— 初始化只由受信 bootstrap CLI 完成。
- 硬删/CASCADE/revoke 均不影响 platform_state（无 FK 边 + guard）→ initialized 永久保持，count=0 不能重开。
- 不允许恢复 API；恢复 = 独立维护程序 + 人工批准 + audit `platform.admin.recovery`（沿用 R4）。

---

## 附注（2026-09-26 · P13 决策指针 —— §4 草稿为**历史候选**）

> 上文 **§4「初始 permissions 字典（seed 示例，B1 定稿）」** 的 13 项草稿 = **historical candidate**，
> **已被裁定取代**（其原本性质即为「形状示例 / 清单待人工审计」，不构成 vocabulary 冻结）。
>
> **current canonical 清单 = `D-P13-01` 的 12 项**（`PLATFORM_DECISION_LOG.md` · 附录 J）：
>
> ```text
> tenant.read · tenant.admin · space.read · space.admin
> member.read · member.admin · resource.read · resource.update · resource.delete
> agent.execute · tool.execute · audit.read
> ```
>
> **明确排除（不得 seed）**：`system.*` · `tenant.manage` · `space.manage` · `member.manage` ·
> `resource.write` · **任何 deny permission**。
> **映射**：`manage → admin` · `write → update`（仅作**输入别名**，**不进入** DB 词表；`D-AUTH-05` 未被修改）。
>
> ⇒ 任何一致性扫描**不得**将 §4 草稿识别为 current decision。
