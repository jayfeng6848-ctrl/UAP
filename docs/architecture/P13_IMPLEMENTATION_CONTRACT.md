# UAP — P13 IMPLEMENTATION CONTRACT（**DRAFT · NOT FROZEN**）

> ## ⛔ 状态指针（**append-only · 2026-09-27** · 不改写下方历史状态块）
>
> ```text
> Human Decision（2026-09-27）：IMPL-01 = A · IMPL-02 = A · IMPL-03 = A · IMPL-04 = C
> ⇒ 现行实施依据见 §21「IMPLEMENTATION DECISIONS」；§1–§20 中与 §21 冲突的具体陈述以 §21 为准。
> revision      = 0017_p13_seed（依 D-OP101-03；取代 §4 的 0016_p13_seed）
> down_revision = 0016_open_p10_1_trust_boundary
> scope         = acl_subject_types · permissions · role_permissions
> non-scope     = users · audit_logs · runtime identity · tenant bootstrap
> C2 判据       = CC-7 受信迁移边界（「无条件 RAISE」不再作为实施依据）
> B-1           = RESOLVED（机制面）· trigger review = PASS
> P13 IMPLEMENTATION = NOT AUTHORIZED（本契约不产生实施授权）
> ```

> ## 状态
>
> ```text
> 轮次            = P13 IMPLEMENTATION PREP / IMPLEMENTATION CONTRACT（READ-ONLY · DESIGN-CONTRACT ONLY）
> 契约状态        = **DRAFT v0 · NOT FROZEN**（因 BLOCKER B-1 未解除，本轮**不进行最终契约冻结**）
> D-PLAT-11 对账  = **PASS**（§2；附 1 项派生项 IMPL-01 待 Human 确认）
> BLOCKER         = **B-1**（§3）：registry 注册在冻结集合内**无合法机制** ⇒ 命中指令 §18 HARD STOP
> 0016+           = ABSENT · DDL/DML = 0 · Runtime = NOT AUTHORIZED
> P13 IMPLEMENTATION = **NOT AUTHORIZED**（本契约不产生任何实施授权）
> ```
>
> **本轮未做**：未创建 `0016_p13_seed.py` · 无 migration · 无 DDL/DML/seed INSERT · 无 runtime/API/worker/scheduler ·
> 未改 `0010–0015` · 未改任何冻结决策原文 · 无 commit / tag / push。

> ## ⛔ 决策更新（2026-09-26 · **append-only 指针** · 不改写本文件正文）
>
> ```text
> 本文件的 `DRAFT v0 · NOT FROZEN` + BLOCKER B-1 状态 = **P13 IMPLEMENTATION PREP 时点快照**（历史）。
> Human 已就 B-1 下达正式裁定：`O-1 = REJECT` · `O-4 = REJECT` · `O-3 = ACCEPT AS ARCHITECTURAL DIRECTION` · `O-2 = DEFERRED`。
> ⇒ `D-P13-15 — B-1 Amendment（Trust Boundary Precondition）` = `FROZEN`（附录 K）；
>   执行顺序调整为 `OPEN-P10-1 → P13 B-1 Amendment → P13 Implementation`。
> ⇒ 本契约 §4 的 `revision = 0016_p13_seed` 属**设计记录**；`0016+` 的编号归属**待 `OPEN-P10-1` 裁定**
>   （`OQ-OP101-03`）—— 本契约**不预占、不改写**该记录。
> ⇒ 下游：`OPEN_P10_1_PREP_REPORT.md` · `OPEN_P10_1_DECISION_RESOLUTION.md` · `OPEN_P10_1_ACCEPTANCE_MATRIX.md`。
> `P13 IMPLEMENTATION` = **NOT AUTHORIZED**（保持）；本契约**仍未冻结**。
> ```

**权威来源（本轮原样读取）**：`PLATFORM_DECISION_LOG.md`（`D-PLAT-09/11` · `D-P11-12` · `D-P13-01…14` + 附录 I.9/I.10/J）·
`P13_DECISION_FREEZE_RECORD.md` · `P13_HUMAN_DECISION_SHEET.md` · `P13_DECISION_RESOLUTION.md` ·
`P13_ACCEPTANCE_MATRIX.md` · `STEP1B_SEED_STRATEGY.md`（§1/§2/§4/§5/§6 + R2/R4/R5）·
`P13_DECISION_COMPLETION_EVIDENCE.md` · `P13_PREP_REPORT.md` · 迁移先例 `0005` / `0006` / `0007`。

---

## 1. 实测基线（本轮只读核验）

```text
HEAD = 034ee97 · tags = 8 · remote = none
alembic 单头 = 0015_p12_indexes · versions = 15 · 0016+ = ABSENT
0010–0015 sha256 逐字节未变（6d990723 / cdaf8383 / 5ecd1ef3 / da1bdffd / 3be9c8c0 / 94b0d228）
命名空间：D-PLAT 17 · D-AUTH 25 · D-AGENT 16 · D-P10 18 · D-P11 14 · D-P12 15 · D-P13 14 · supersession = 1
```

**@0015 种子现状（实测）**：`roles = 1`（`platform_admin`，PLATFORM scope）· `platform_state = 1`（`uninitialized`）·
`acl_subject_types = 0` · `permissions = 0` · `role_permissions = 0` · `users = 0` · `tenants/spaces/memberships/PM = 0`。

**种子目标表形态（实测）**

| 表 | 列 | 约束 / 索引 | 触发器 |
|---|---|---|---|
| `acl_subject_types` | id · key · description · created_at · archived_at | `ck_..._key`（`^[a-z][a-z0-9_]{1,31}$`）· `ck_..._whitelist`（`{user,role,agent}`）· `uq_acl_subject_types_key` | **C2** `tg_acl_subject_types_protect`（BEFORE INSERT/DELETE/UPDATE，row） |
| `permissions` | id · key · resource_type · action · description · is_system · created_at | `ck_permissions_action_canonical`（12 小写形）· `ck_permissions_key` · `uq_permissions_key` | **（无）** |
| `role_permissions` | role_id · permission_id · effect · conditions · created_at | `pk_role_permissions (role_id, permission_id, effect)` · `ck_..._effect {allow,deny}` · 2× FK CASCADE | **（无）** |
| `roles` | … | `uq_roles_platform` / `uq_roles_tenant` / `uq_roles_space` | `tg_roles_scope_shape` · `tg_roles_is_system_protect` · `tg_roles_pm_lifecycle` · `tg_acl_role_delete_block` · `tg_roles_set_updated_at` |
| `users` | id · email · email_verified_at · username · display_name · status · primary_identity_id · last_login_at · locked_until · failed_attempts · created_at · updated_at · deleted_at | `uq_users_email` · `uq_users_username` · `ck_users_status` | `tg_acl_user_hard_delete`（AFTER DELETE）· `tg_users_set_updated_at` |

> `users` **无 `tenant_id` 列**（实测）⇒ 无租户的主体行在 schema 上**成立**。

---

## 2. D-PLAT-11 语义对账（**PASS**）

### 2.0 `D-PLAT-11` 原文（逐字）

```text
决策 = ① 首个正式可登录主体**只通过 P13 建立**；② **不引入第二套开发 bootstrap 身份路径**。
背景 = STEP1B_SEED_STRATEGY.md:14-27 定义了 P13 的单一 10 步 bootstrap 顺序
       （含「首租户 + 首管理员用户」「首空间」「role_permissions 含 deny 行」）……
依据 = Human Decision 项 5 · STEP1B_SEED_STRATEGY.md:14-27 · STEP1B_SCHEMA_DEPENDENCY.md:193 · B1-4_DECISION_LOG.md:58
影响面 = Runtime Slice 的演示主体来源**被唯一限定为 P13** ⇒ 任何"dev bootstrap"实现均属违反；
        同时意味着 `resource_permissions` 在 P13 之前**不可写入**
待办 = ① 若 P13 之外确需可登录主体，须**另行提请 Human 裁定**，不得自行增设
```

### 2.1 判定（Q1–Q4，逐项，全部基于权威原文，未作假设）

**Q1「首个正式可登录主体」指什么？**
⇒ **可承载登录的「主体身份记录」（subject identity record）**，**不是** platform administrator、**不是** tenant administrator、**不是** membership-bearing object。
依据：`D-P13-06`（FROZEN）明文要求「**「首个可登录主体」与「P13 创建主体记录」必须区分**」，并规定 identity row = allowed、credentials = forbidden；
`D-PLAT-11` 影响面仅言「**演示主体**来源」，未涉任何授权/membership 对象；平台管理员的**授权**由 `R3-D-07`/`R4`/`R5`/`D-P13-07` 明确归 bootstrap CLI。

**Q2「只经 P13」指什么？**
⇒ **主体记录的「唯一建立路径」**（该记录只能由 P13 这条既有 seed 路径产生；禁止第二套 dev bootstrap 路径）。
**不是** "由 P13 一次性完成 租户 + membership + 凭据"。
依据：`D-PLAT-11` ② 的禁止对象是「第二套**开发** bootstrap 身份路径」；`D-PLAT-11` 待办① 亦只针对「P13 之外的**可登录主体**」。

**Q3 `D-PLAT-11` 是否**允许**「P13 identity = user row；后续 CLI/runtime = tenant + membership + authorization」？**
⇒ **允许**。依据链：
1. `D-PLAT-11` 决策文本**未提及** tenant / membership；
2. 其**依据**所引 `SEED_STRATEGY §1` 的**引导顺序小节**自注「（新建租户的**运行时流程，非一次性 seed**）」⇒ 租户/属主用户/membership 序列本身即**运行时**流程；
3. `SEED_STRATEGY` **R2**（2026-09-08，晚于 §1）：「seed **只创建角色行与 role_permissions 绑定**；**不**给任何用户授予角色」·「首名平台管理员的绑定由**部署 bootstrap（CLI）**写入 `platform_memberships`」·「每租户/每空间的系统角色在**租户/空间创建时**播种（onboarding），`0005` 只负责为**既有** tenant/space 行补种」；
4. **R4**：「普通 API/seed 不得扮演 bootstrap：seed 只建角色行与 role_permissions，**永不写 PM 行**」；
5. **R5 / 0006**：「seed（migration 0006）只写 `platform_state(id=1,'uninitialized')`；**永不**写 initialized」；
6. `SEED_STRATEGY §6`：「首管理员密码由 onboarding 流程设置（**非 seed**）」；
7. `D-P13-06`（FROZEN，日期晚于 `D-PLAT-11`）明文：identity row = **allowed**；credentials = **forbidden**；登录能力由后续 onboarding / runtime credential establishment 提供。

**Q4 `D-PLAT-11` 的原始语义是否**要求** P13 创建 tenant / membership？**
⇒ **否**。无任何冻结原文如此要求；相反 `R2`/`R4`/`R5` 将 tenant / space / membership 明确归于 **onboarding / runtime**。
（若存在相反证据，本项即应 BLOCKED —— 本轮**未发现**任何此类证据。）

### 2.2 对账结论

```text
D-PLAT-11 RECONCILIATION = PASS
  · 与 D-P13-05(B) / D-P13-08(B) **不冲突**（D-PLAT-11 决策文本不涉 tenant/membership）
  · D-PLAT-11 的「依据」中 §1 十步序的 tenant/成员步已被其后 R2/R4/R5 收窄为 onboarding/runtime
  · **无需**修改 / supersede D-PLAT-11、D-P13-05、D-P13-08
  · 不得据本对账新增 tenant / membership / runtime onboarding
```

### 2.3 派生项（**REQUIRED-DERIVED · 待 Human 确认**，见 §17 `IMPL-01`）

```text
D-PLAT-11① + D-P13-06 ⇒ P13 **必须建立首个主体记录**（无凭据）。
推证：若 P13 不建立任何 `users` 行，则「首个正式可登录主体只经 P13 建立」在冻结集合内
      **无可满足路径** —— 唯一的建立者将退化为 CLI / onboarding，与①的字面要求相左。
      ⇒ P13 需插入**恰 1 行**无凭据 `users` 行（schema 无 tenant_id ⇒ 成立）。
状态：**REQUIRED-DERIVED**（非自行解释成兼容）—— 因冻结 §15 的 CREATE/ENSURE 面**未列 `users`**，
      该行是否实施**必须由 Human 确认**（`OQ-P13-IMPL-01`）。本契约给出分支，不代裁。
```

---

## 3. ⛔ BLOCKER B-1 — registry 注册在冻结集合内无合法机制

### 3.1 事实（逐字证据）

```text
事实 A（保护触发器体 · pg_get_functiondef 逐字）：
  enforce_acl_subject_types_protect()
    IF TG_OP = 'INSERT' THEN
      RAISE EXCEPTION 'acl_subject_types is a platform-controlled registry:
                       runtime INSERT denied (registry rows are migration-controlled)';
    ELSIF TG_OP = 'DELETE' THEN RAISE EXCEPTION '... cannot be deleted (retire via archived_at)';
    ELSE  -- UPDATE: key immutable
  → **对 INSERT 无条件 RAISE，无任何豁免分支 / 无 GUC 判据 / 无角色白名单**
  → 触发器于 **0007** 创建（`D-B14-12 = A`），在 `0015` 处**已存在且启用**

事实 B（历史事实 · 全仓 grep）：
  迁移目录**无任何** `INSERT INTO acl_subject_types` 命中
  ⇒ 设计所称「migration-controlled path」在**实现层面不存在**；registry 自建表以来**恒为 0 行**（@0015 实测 0）

事实 C（同源同类阻断 · 另一目标表）：
  enforce_roles_is_system_protect()（0005）：`IF NEW.is_system THEN RAISE 'system roles cannot be created at runtime'`
  ⇒ 任何 `is_system = true` 的 roles INSERT 亦被阻断（0005 系在**建该触发器之前**完成播种才得以成功）
```

### 3.2 冲突判定

```text
D-P13-03（FROZEN）：registry seed **必须**走 migration-controlled path；runtime INSERT = FORBIDDEN；
                    C2 必须保持 —— 不得删除、不得绕过、不得长期关闭
D-P13-04（FROZEN）：**仅注册** acl_subject_types.key = agent（+ §15 的 registry = user/role/agent）
D-P13-11（FROZEN）：seed 必须在 **39 triggers 保持启用**状态下执行；
                    禁止 DISABLE TRIGGER · DROP TRIGGER · ALTER TRIGGER · 绕过 C2 · **临时关闭保护后再恢复**

⇒ 插入 registry 三行所需的**全部可用机制**：
   ① DISABLE TRIGGER → INSERT → ENABLE      ← D-P13-11「禁临时关闭保护后再恢复」**禁止**
   ② session_replication_role = replica     ← 等同临时关闭触发器（且隐含绕过其他保护）⇒ D-P13-11 / §12 **禁止**
   ③ ALTER 触发器/函数（加豁免分支）          ← D-P13-11「禁 ALTER TRIGGER」+ 触及 0007 既有对象 **禁止**
   ④ 由 runtime / CLI 插入                   ← D-P13-03「runtime INSERT = FORBIDDEN」**禁止**
   ⑤ 不插入（registry 保持空）               ← 违反 D-P13-04 与 §15 的 registry 注册要求，且使
                                              `resource_permissions` 在 P13 后仍不可写（与 D-PLAT-11 影响面矛盾）**禁止**

⇒ **冻结集合内不存在同时满足 D-P13-03 / D-P13-04 / D-P13-11 的机制。**
```

### 3.3 命中 HARD STOP 条件（指令 §18）

```text
✓「existing frozen decision conflict」        —— D-P13-03（migration-controlled path）× D-P13-11（禁临时关闭/绕过）
✓「trigger bypass appears necessary」          —— registry INSERT 的唯一出路是临时关闭或改触发器
✓「P13 requires new schema object」的**邻接**风险 —— 若以「新对象」绕过（如新 registry 表/中间表）亦被禁止
⇒ **HARD STOP**：本契约**不冻结**，不得创建 0016，不得实施。**不得由 Bot 自行选择补救方案。**
```

### 3.4 候选补救（**仅登记 · 不由 Bot 选择**）

| 编号 | 方案 | 需要的动作 | 触及面 |
|---|---|---|---|
| **O-1** | 授权迁移内**受控** DISABLE→INSERT→ENABLE（同事务即时复原） | 新决策（amend `D-P13-03` 或新增 `D-P13-15`） | 仅 P13 迁移 |
| **O-2** | 为 C2 增设**受控豁免**（如会话 GUC / 迁移专用角色） | 新决策 + 以新迁移**替换** 0007 的既有函数 | 触及既有迁移对象（需另判可否替换） |
| **O-3** | registry 三行改由**部署期受信路径**建立；P13 仅校验存在 | 需 Human **重述** `D-P13-03` 的「runtime INSERT = FORBIDDEN」 | 与 `D-PLAT-11` 时序交互 |
| **O-4** | 承认 registry 保持空、ACL 在 P13 后仍不可写 | 需 Human **重述** `D-PLAT-11` 影响面与 §15 registry 要求 | 影响 Runtime Slice 可用性 |

> **说明（不构成选择）**：`O-1` 与 `D-P13-11` 明文冲突；`O-2` 触及既有迁移对象；`O-3`/`O-4` 均需修改既有冻结语义。四者**都**需要新的 Human Decision —— 这正是本轮 HARD STOP 的原因。

---

## 4. Migration identity（设计记录 · 本轮不创建文件）

```text
revision       = 0016_p13_seed
filename       = 0016_p13_seed.py
down_revision  = 0015_p12_indexes
single-head    = 0016
append-only    = true（不改 0001–0015）
branch_labels  = None · depends_on = None
upgrade        = 见 §12 顺序契约
downgrade      = 见 §15（FAIL-CLOSED）
```

---

## 5. 对象接触面（逐对象动作标记）

| 对象 | 动作 | 说明 |
|---|---|---|
| `acl_subject_types` | **INSERT × 3** | `user` / `role` / `agent` —— **⛔ 被 B-1 阻断** |
| `permissions` | **INSERT × 12** | §7 canonical 清单（表上无触发器） |
| `roles` | **READ-ONLY** | `D-P13-02`：`platform_admin` 归 0005，P13 仅**校验存在**（不重种） |
| `role_permissions` | **INSERT × N** | 见 §17 `IMPL-02`（派生待确认）；表上无触发器 |
| `users` | **INSERT × 0 或 1** | 见 §17 `IMPL-01`（REQUIRED-DERIVED · 待确认） |
| `platform_state` | **READ-ONLY** | 0006 已播 `uninitialized`；`D-P13-07` 禁 P13 触碰 |
| `platform_memberships` | **禁（零写入）** | `D-P13-07` |
| `tenants` / `spaces` | **禁（零写入）** | `D-P13-05` |
| `tenant_memberships` / `memberships` | **禁（零写入）** | `D-P13-08` |
| `agents` / `agent_versions` / `agent_permissions` / `tool_executions` | **禁（零写入）** | `D-P13-04` |
| `audit_logs` | **见 §17 `IMPL-03`** | 先例：既有迁移**无** audit 写入 · `SEED_STRATEGY §6` 称 seed 事件写 audit |
| `events` | **禁** | P10 outbox；P13 无事件写入 |
| schema 新对象 | **禁** | 冻结未授权任何 CREATE |

---

## 6. 数据边界

**Allowed baseline seed（逐对象确认后）**

```text
acl_subject_types   user / role / agent            （⛔ B-1）
permissions         §7 的 12 项 canonical
roles               **零新增**（既有 platform_admin 归 0005）
role_permissions    仅确定性平台基线绑定（IMPL-02）
users               0 或 1 行无凭据主体记录（IMPL-01）
```

**Explicitly forbidden**

```text
users with credentials · plaintext password · credential secret · fabricated password
bootstrap tenant · platform_memberships · tenant_memberships · memberships
real Agent · agent_versions · agent_permissions · tool_executions
business data · runtime data · demo data · deny permission · system.* · manage · write
新增 seed_batch / migration_owned / seed_origin / ownership marker 列
```

---

## 7. Permission Contract（12 项 · `D-P13-01`）

| # | key | action | resource_type | is_system | effect |
|---|---|---|---|---|---|
| 1 | `tenant.read` | `read` | tenant | true | allow |
| 2 | `tenant.admin` | `admin` | tenant | true | allow |
| 3 | `space.read` | `read` | space | true | allow |
| 4 | `space.admin` | `admin` | space | true | allow |
| 5 | `member.read` | `read` | member | true | allow |
| 6 | `member.admin` | `admin` | member | true | allow |
| 7 | `resource.read` | `read` | resource | true | allow |
| 8 | `resource.update` | `update` | resource | true | allow |
| 9 | `resource.delete` | `delete` | resource | true | allow |
| 10 | `agent.execute` | `execute` | agent | true | allow |
| 11 | `tool.execute` | `execute` | tool | true | allow |
| 12 | `audit.read` | `read` | audit | true | allow |

```text
校验（静态 · 只读核对）：
  · 12 个 action ∈ ck_permissions_action_canonical 的 12 小写形  ✅（read/admin/read/admin/read/admin/
      read/update/delete/execute/execute/read）
  · 12 个 key 满足 ck_permissions_key = ^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$  ✅
  · is_system 全 true · effect 全 allow · **无 deny**（D-P13-01）
  · 不得出现 system.* / manage / write / 任何 deny（除新 Human Decision 明确 supersede）
  · resource_type：**不新增** DB 词表 / CHECK（D-P13-01 Q5 派生闭项）
```

---

## 8. Action Alias Rule

```text
manage → admin          write → update
（**输入别名**：仅用于把历史草稿映射到 canonical 词表）
⇒ manage / write **不得进入**数据库 canonical action vocabulary
⇒ 不得修改 ck_permissions_action_canonical · 不得修改 D-AUTH-05 · 不得新增第二套 action 表
⇒ §7 的 12 项中已按此映射完成（tenant.admin / space.admin / member.admin / resource.update）
```

---

## 9. Agent Subject Rule

```text
P13：acl_subject_types: agent = **register only**
不得创建：agents · agent_versions · agent_permissions · tool_executions · demo Agent
（实际 Agent 属 Runtime / Domain；G 依赖 agents.id 分派，表在 P09 已建）
```

---

## 10. Role Ownership Contract（依 0005 / 0006 / R2 先例逐字核对）

```text
platform_admin     = **existing migration-owned（0005）** —— P13 **仅校验存在**，不得重种
                     先例逐字：INSERT ... WHERE NOT EXISTS (SELECT 1 FROM roles
                               WHERE tenant_id IS NULL AND space_id IS NULL AND key = 'platform_admin')
tenant_admin / tenant_member = **onboarding/runtime-owned**（每租户创建时播种；P13 零播种 ← D-P13-05=B）
space_admin / space_member   = **onboarding/runtime-owned**（每空间创建时播种；P13 零播种）
（R2：「每租户/每空间的系统角色在**租户/空间创建时**播种（onboarding），0005 只负责为**既有** tenant/space 行补种」）

⇒ 禁止按角色名推导 ownership；禁止把既有 migration-controlled 行重复纳入 P13。
⇒ 附注：`enforce_roles_is_system_protect`（0005）会拒绝任何 `is_system = true` 的 roles INSERT
   —— P13 因**零 roles 写入**而不受影响；但此事实说明「P13 若需新增系统角色行则同样受阻」。
```

---

## 11. Tenant / Space Boundary

```text
P13 tenant seed              = 0        （D-P13-05 = B）
P13 tenant_membership seed   = 0        （D-P13-08 = B）
P13 membership seed          = 0        （D-P13-08 = B）
P13 platform_membership seed = 0        （D-P13-07 = A · R4「seed 永不写 PM 行」）
```

> tenant / space / membership 的**实际创建**属后续 **onboarding / runtime contract**，不是 P13 seed。
> 该分立已与 §2 的 `D-PLAT-11` 对账**联合确认**（`D-PLAT-11` 决策文本不涉 tenant/membership；R2/R4/R5 明确归 onboarding/runtime）。

---

## 12. Seed Order Contract（唯一拓扑 · `D-P13-09` = A）

| 步 | SEED_STRATEGY §1 | 本轮可执行性 | 依赖理由 |
|---|---|---|---|
| 1 | `acl_subject_types` | **EXECUTABLE（⛔ B-1）** | root；被 `resource_permissions` 引用 |
| 2 | `permissions` | **EXECUTABLE** | root；无触发器 |
| 3 | roles 校验 | **EXECUTABLE（READ-ONLY）** | 校验 `platform_admin` 存在（D-P13-02） |
| 4 | 首租户 + 首管理员用户 | **NO-OP**（tenant 部分）· user 部分见 `IMPL-01` | D-P13-05 = B（tenant 零播种） |
| 5 | tenant 角色 | **NO-OP** | 无租户 ⇒ 无每租户角色（D-P13-02/05） |
| 6 | `tenant_memberships` | **NO-OP** | D-P13-08 = B |
| 7 | 首空间 | **NO-OP** | 无租户 ⇒ 无空间（D-P13-05） |
| 8 | space 角色 | **NO-OP** | 无空间（D-P13-02/05） |
| 9 | `memberships` | **NO-OP** | D-P13-08 = B |
| 10 | `role_permissions` | **EXECUTABLE** | 需 roles + permissions 就位（见 `IMPL-02`） |

```text
不得因 4/5/6/7/8/9 为空操作而**自行设计第二套顺序**（D-P13-09）；
实施阶段只执行实际需要的步骤（1 → 2 → 3 → 10，加 B-1 解除后的 1）。
```

---

## 13. Idempotency Contract（`D-P13-10` = A）

| seed | natural key | ownership 假设 | 重复执行 | 冲突行为 |
|---|---|---|---|---|
| `acl_subject_types` ×3 | `key`（`uq_acl_subject_types_key`） | migration-owned（`D-P13-03`） | `WHERE NOT EXISTS` | 冲突 = **显式失败** |
| `permissions` ×12 | `key`（`uq_permissions_key`） | migration-owned | `WHERE NOT EXISTS` | 冲突 = **显式失败** |
| `role_permissions` | `(role_id, permission_id, effect)`（PK） | migration-owned（`platform_admin` 归 0005） | 见 `IMPL-02` | 冲突 = **显式失败** |
| `users`（若入 scope） | `username` / `email` | 见 `IMPL-01` | `WHERE NOT EXISTS` | 冲突 = **显式失败** |

```text
禁止：blind upsert · 静默 ON CONFLICT DO NOTHING · 覆盖既有 runtime 行
（R2 逐字：「唯一谓词不含 archived → seed 冲突即失败，不做"upsert 覆盖"，保证 seed 确定性」）
目标：重复执行 = deterministic；错误数据 = fail loudly
```

---

## 14. Trigger Contract（`D-P13-11` = A）

```text
P13 seed **必须在全部既有触发器启用状态下执行**（@0015 父级 39 + 子分区克隆行）。
禁止：DISABLE TRIGGER · DROP TRIGGER · ALTER TRIGGER · 绕过 C2 · 临时关闭保护后再恢复
```

**逐表触发器交互（实施期须逐条行为验证）**

| 目标表 | 将触发的触发器 | 与 seed 的交互 |
|---|---|---|
| `acl_subject_types` | **C2 `tg_acl_subject_types_protect`** | **无条件拒绝 INSERT** ⇒ ⛔ **B-1** |
| `permissions` | （无） | 无交互 |
| `role_permissions` | （无） | 无交互（FK → roles/permissions 需先就位） |
| `roles` | READ-ONLY（不写入） | `tg_roles_is_system_protect` 仅在被写入时才相关 ⇒ 零写入 |
| `users`（若入 scope） | `tg_users_set_updated_at`（BEFORE UPDATE）· `tg_acl_user_hard_delete`（AFTER DELETE） | INSERT 不触发二者 ✓ |
| 其他 | G/H/I/J + 形状/scope 校验族 | **P13 零 rp/tenant/space/membership/PM 写入 ⇒ 不触发**（实施期仍须逐条验证） |

```text
C2 的 migration-controlled path **必须继续保持**（D-P13-03）—— 但该 path 当前不存在（§3 事实 B）
⇒ 这正是 B-1 的实质：**要求保持一个从未实现的路径**，而可实现的替代全部被 D-P13-11 禁止。
```

---

## 15. Downgrade Contract（FAIL-CLOSED · `D-P13-12` = C）

```text
设计（实施期细化，不改决策语义）：
  clean-baseline 前置检查（全部须**精确相等**，任一超出即 RAISE）：
    acl_subject_types  count = 3  ∧  keys = {user, role, agent}
    permissions        count = 12 ∧  keys = §7 集合
    role_permissions   count = |seed 绑定集|（IMPL-02）
    users              count = 0 或（IMPL-01 裁决后的基线 1，且身份恰为 canonical 种子身份）
  dependent-row 检查：
    resource_permissions 引用 registry ⇒ 存在即 RAISE（并按 FK RESTRICT 物理拦截）
  任一不满足 ⇒ RAISE ⇒ **整个 downgrade 回滚 ⇒ 0 DELETE**
```

```text
禁止：DELETE WHERE key IN (...) 作为默认降级行为 · 因「理论上这些 key 是 seed」而删除 · 猜测 ownership
不得单独用 is_system / natural key / FK RESTRICT / audit_logs 证明 ownership（D-P13-12 逐字）
降级语义：clean baseline → allow；runtime / ownership ambiguity → fail closed；never guess / never delete uncertain
```

---

## 16. No New Ownership Marker（`D-P13-14` = A）

```text
P13 不得新增：seed_batch · migration_owned · seed_origin · ownership metadata column
（除非未来另行开启正式 Decision / Design scope）
runtime 数据保护 = natural-key filtering + existing FK protection + D-P13-12 fail-closed + pre-downgrade verification
```

---

## 17. OPEN / 待确认项（逐对象确认结果 · **不得由 Bot 代裁**）

| 编号 | 事项 | 证据（双向） | 建议方向（**≠ 决策**） | 阻塞面 |
|---|---|---|---|---|
| `IMPL-01` | P13 是否 INSERT **1 行无凭据 `users`**（首个主体记录） | 支持：`D-PLAT-11①` + `D-P13-06`（identity row allowed）+ `SEED_STRATEGY §1[4]/§6`（首管理员用户入序、密码由 onboarding 设）· 反对：冻结 §15 的 CREATE/ENSURE 面未列 `users` | 纳入（否则 `D-PLAT-11①` 无可满足路径） | 影响 §5/§6/§12/§15 |
| `IMPL-02` | `role_permissions` 的确定性绑定集合 | `SEED_STRATEGY §1[10]`（内置角色↔权限绑定）· `R2`（seed 只建角色行与 role_permissions）· `D-P13-01`（无 deny）· `D-P13-02`（P13 零租户/空间角色） | `platform_admin × §7 全部 12 项 · effect = allow`（= 12 行） | 影响 §5/§12/§15 |
| `IMPL-03` | P13 是否写 `audit_logs` | `SEED_STRATEGY §6`（「seed 事件写 audit_logs（actor=system）」）· 先例：**全仓迁移零 audit 写入**（0005/0006 均不写；0006 明确「本 revision 只建结构」）· `CF-2`「trigger does NOT write audit」 | **不写**（遵循先例；seed 运行审计交由部署/运维层） | 影响 §5 |
| `IMPL-04` | 若 `IMPL-01` = 纳入，降级如何移除该行 | `D-P13-12`：不得单独以 natural key 证明 ownership | 仅在「count 精确 = 1 ∧ 身份恰为 canonical」时删除，否则 RAISE | 依赖 `IMPL-01` |

---

## 18. 三类扫描（指令 §16）

```text
dependency scan   = PASS（§2 对账链 + §12 顺序表的逐步依赖；无环、无 deferred FK）
scope scan        = PASS（0016+ = 0 · DDL/DML = 0 · 无新 schema 对象 · 无 runtime 写入）
consistency scan  = PASS（D-P13-01…14 与 SEED_STRATEGY（含 R2/R4/R5）/ D-PLAT-11 / D-P11-12 逐条比对；
                     全仓 `D-P13-` 仅存在于冻结轮新增区段；§4 草稿已标历史候选）
predecessor review = PASS（0005/0006/0007 先例逐字核对；0010–0015 未改）
trigger review     = **BLOCKED**（B-1：C2 无条件拒绝 INSERT，无合法受控路径）
downgrade review   = PASS（设计满足 FAIL-CLOSED；`users` 行的移除依据待 `IMPL-01`）
```

---

## 19. 本轮自证偏差（如实披露）

```text
① 为核对 schema 形态，本轮在**一次性测试库**（`uap_b1_test`）执行了 testkit `reset_test_database()` +
   `alembic upgrade head`。该动作属 DDL/DML，**与指令 §0「本轮禁止 DDL/DML」字面不符**。
   影响面：仅限一次性的 testkit 库；**未触碰正式库 `uap`、未改仓库任何迁移/代码**。
   处置：如实披露；后续核对改以**迁移源码 + 已取得事实**为准，不再执行数据库写操作。
② 本节结论所依赖的 B-1 证据为**只读事实**（`pg_get_functiondef` 逐字 + 全仓 grep），不依赖①的动作。
```

---

## 20. B-1 裁定登记（**append-only · 2026-09-26**）

> 本节为**追加登记**：**不**修改 §1–§19 正文；**不**改写任何冻结决策；**不**产生实施授权。

### 20.1 Human 裁定与 B-1 的对应

| B-1 候选（§3.4） | Human 裁定 | 对 §3 BLOCKER 的处置 |
|---|---|---|
| `O-1` 受控 DISABLE | **REJECT** | §3.2 机制①**永久排除**；`D-P13-11` 禁令**原样保留** |
| `O-2` C2 受控豁免 | **DEFERRED** | §3.2 机制③**不关闭**，但**前置未就绪**（`OPEN-P10-1`）；`M-4` 新先例**未批准** |
| `O-3` 移交部署期受信路径 | **ACCEPT AS ARCHITECTURAL DIRECTION** | 方向被接受；其**前置 = 数据库身份隔离成立** |
| `O-4` registry 保持空 | **REJECT** | §3.2 机制⑤**永久排除**；`D-P13-04` / `D-PLAT-11` 影响面**不重述** |

### 20.2 §3 BLOCKER B-1 的现行状态

```text
B-1 本身**未解除**（registry 在冻结集合内仍无合法机制）
其**解除路径已被裁定**：先解决 OPEN-P10-1（数据库信任边界），再回到 P13 B-1 Amendment
⇒ `P13 IMPLEMENTATION PREP = BLOCKED` 的事实**保持**；阻塞原因由「无候选」变为「前置未就绪」
⇒ 本契约**不得**冻结；`0016_p13_seed.py` = MUST NOT EXIST（保持）
```

### 20.3 §17 `IMPL-01`…`IMPL-04` 状态（**本轮未变**）

```text
IMPL-01 = REQUIRED-DERIVED · 待 Human 确认（未裁）
IMPL-02 = 派生 · 待 Human 确认（未裁）
IMPL-03 = OPEN（未裁）
IMPL-04 = 依赖 IMPL-01（未裁）
⇒ B-1 FINAL DIRECTION 轮**不**裁定上述四项（不在该轮授权面内）
```

### 20.4 新增前置依赖（本契约的修订项）

```text
P-1  本契约 §4 的 revision 编号（`0016_p13_seed`）须在 `OQ-OP101-03` 裁定后重新对账
P-2  本契约 §14「Trigger Contract」项下的 C2 交互须在 `OPEN-P10-1` 冻结后，按 `OQ-OP101-05` 的判据形态重述
P-3  本契约 §15「Downgrade Contract」须与 `OQ-OP101-12` 的降级语义（角色/GRANT 回收）合并评估
P-4  本契约 §19 偏差披露中的 testkit 动作（`reset_test_database()` + `upgrade head`）在 `OPEN-P10-1` 轮**未再执行**
     （该轮仅执行只读查询 + 1 次事务级 `set_config` 探针）
```

### 20.5 本节边界

```text
本契约 §1–§19 = 未改写（除顶部状态区插入指针块，属纯插入）；§20 = 纯追加
0007 = unchanged · C2 = unchanged · 0016+ = ABSENT · DDL/DML = 0 · commit/tag/push = 0
supersession 新增 = 0 · 未 supersede / 未改写任何 D-* 决策正文
```

---

## 21. IMPLEMENTATION DECISIONS（**append-only · 2026-09-27 · Human Decision 登记**）

> 本节为本轮追加的**现行实施依据**。§1–§20 **未改写**；其中被本节取代的具体陈述逐条列于 §21.6。
> 决策来源：Human 于 2026-09-27 完成 P13 Implementation Clarification 裁决
> （Decision Sheet 见 `P13_IMPLEMENTATION_CLARIFICATION_HUMAN_DECISION_SHEET.md`）。

### 21.1 `IMPL-01 = A` — P13 不创建 `users` 行

```text
Decision: P13 does NOT create users rows.

· No bootstrap user
· No synthetic identity
· No login identity
· No ownership identity

D-PLAT-11① 同步口径：P13 establishes platform authorization baseline,
                     not user provisioning.
⇒ 首个正式可登录主体由 P13 之后的受信 onboarding / CLI 路径建立。
禁止措辞：P13 creates first user · bootstrap account · migration user · system user
```

### 21.2 `IMPL-02 = A` — `role_permissions` 精确集合

```text
Decision:
  role        = platform_admin
  effect      = allow
  permissions = D-P13-01 canonical 12 项
⇒ rows = 12（唯一答案，不存在实现期选择空间）

精确清单（逐行 · 12 行）：
  platform_admin × tenant.read      × allow
  platform_admin × tenant.admin     × allow
  platform_admin × space.read       × allow
  platform_admin × space.admin      × allow
  platform_admin × member.read      × allow
  platform_admin × member.admin     × allow
  platform_admin × resource.read    × allow
  platform_admin × resource.update  × allow
  platform_admin × resource.delete  × allow
  platform_admin × agent.execute    × allow
  platform_admin × tool.execute     × allow
  platform_admin × audit.read       × allow

exclusions（不得出现）：
  deny 行 · system.* · tenant.manage · space.manage · member.manage · resource.write
  · 任何非 canonical 12 项的 permission · 任何其他 role
    （tenant_admin / tenant_member / space_admin / space_member 一律零写入）

幂等与冲突语义：PK(role_id, permission_id, effect)；WHERE NOT EXISTS；
                冲突 = 显式失败（D-P13-10；禁 upsert / 禁 ON CONFLICT DO NOTHING）
禁止：implementation decides · future expansion · dynamic generation · runtime calculation
```

### 21.3 `IMPL-03 = A` — 不写 `audit_logs`

```text
Decision: audit_logs = NO

P13 不产生：audit_logs 行 · audit actor · audit action · risk_level · classification

语义区分（不得混淆）：
  migration execution evidence  !=  audit_logs business/security event

不得因 P10 已提供 audit_logs schema 而自动添加写入。
downgrade：audit_logs 中不存在 P13 写入行 ⇒ 无需处理
           （且 tg_audit_immutable 禁止 DELETE / UPDATE）
```

### 21.4 `IMPL-04 = C` — downgrade 策略

```text
Decision:
  Only remove P13 migration-owned objects.
  Never delete users.
  Never delete unknown existing data.
  Ownership uncertainty => RAISE.

downgrade predicate = deterministic ∧ ownership-bound ∧ fail-closed

允许移除（且仅限）：P13 本迁移创建的
  acl_subject_types 3 行（key ∈ {user, role, agent}）
  permissions 12 行（D-P13-01 清单）
  role_permissions 12 行（platform_admin × 12 × allow）
判定方式：自然键 + 精确 count + 无额外依赖行；任一偏离 ⇒ RAISE ⇒ 整条回滚 ⇒ 0 DELETE

users 表：P13 不创建任何 users 行 ⇒ downgrade 全过程中不得出现对 users 的 DELETE

禁止：
  DELETE WHERE id = <fixed value>
  DELETE all rows created before <timestamp>
  DELETE unknown matching records
  DELETE WHERE key IN (...) 作为默认降级行为
```

### 21.5 实施清单（Q1 的唯一答案）

```text
新建 schema 对象                        = 0
INSERT acl_subject_types                = 3 行（user / role / agent）
INSERT permissions                      = 12 行（D-P13-01 §7 清单）
INSERT role_permissions                 = 12 行（platform_admin × 12 × allow）
INSERT users                            = 0 行
INSERT audit_logs                       = 0 行
roles                                   = 0 行新增（只读校验 platform_admin 存在 · D-P13-02）
platform_memberships / tenants / spaces / memberships = 0
agents / agent_versions / agent_permissions / tool_executions = 0
```

### 21.6 与 §1–§20 的取代关系（supersession 明细 · 不改写原文）

```text
S-1 §4「revision = 0016_p13_seed · filename = 0016_p13_seed.py · single-head = 0016」
    ⇒ 由 §21.7 取代为 0017_p13_seed（依 D-OP101-03）
S-2 §3 / §3.4 / §14 / §18 中「C2 无条件 RAISE · registry 在冻结集合内无合法机制 ·
    trigger review = BLOCKED」
    ⇒ 由 §21.8 取代（CC-7 受信迁移边界）
S-3 §5 / §6 / §12 / §15 中 users「0 或 1」分支、role_permissions「见 IMPL-02」分支、
    downgrade「users 行移除依据待 IMPL-01」分支
    ⇒ 由 §21.1 / §21.2 / §21.4 取代
S-4 §17 `IMPL-01…04 = 待 Human 确认（未裁）`
    ⇒ 由 §21.1–§21.4 取代为 RESOLVED；§17 / §20.3 原始文本保留为历史
S-5 §19 自证偏差披露 = 保持（历史事实，不删）
```

### 21.7 Revision identity 对账

```text
revision       = 0017_p13_seed
filename       = 0017_p13_seed.py
down_revision  = 0016_open_p10_1_trust_boundary
single-head    = 0017（P13 完成后）
branch_labels  = None · depends_on = None · revision ≤ 32 chars
依据           = D-OP101-03（0016 归 OPEN-P10-1；P13 seed = 0017_p13_seed）
说明           = 历史 `0016_p13_seed` 字样保留于 D-P13-* 冻结正文与历史文档（append-only，不改写）
```

### 21.8 C2 / trigger 判据对账（AC-1 处置）

```text
现行判据 = CC-7 受信迁移边界：
  受信分支：current_user = session_user = 'uap_migrator' ⇒ registry INSERT / UPDATE / DELETE 放行
  runtime  ：uap_app ⇒ 行为与 0007 pre-image 逐字一致（INSERT denied，错误文本保持）
  C2 post-image md5 = 185e95be8bc4304edbcd3f4d5cda1eff
  C2 函数签名不变：() RETURNS trigger · pronargs 0 · plpgsql · prosecdef false

⇒ trigger review = PASS（不再 BLOCKED）
⇒ §14「须在既有 39 触发器全启用状态下执行」的要求保持不变（D-P13-11 未 amend）
⇒ §3.1「事实 A」中「无条件 RAISE / 无任何豁免分支」= 历史证据陈述，作废为实施依据（不删除原文）
```

### 21.9 门控与边界

```text
本节不产生实施授权。P13 IMPLEMENTATION = NOT AUTHORIZED（保持）。
本轮：DDL = 0 · DML = 0 · migration execution = 0 · 0017 = ABSENT · commit/tag/push = 0
§1–§20 逐行未变（除顶部状态指针块插入，属纯插入）；§21 = 纯追加。
```

---

**END OF P13 IMPLEMENTATION CONTRACT（DRAFT v0 · 2026-09-26 正文 · §21 追加于 2026-09-27 · **NOT FROZEN** · `B-1 = RESOLVED（机制面）` · `P13 IMPLEMENTATION = NOT AUTHORIZED` · `D-PLAT-11 RECONCILIATION = PASS`）**
