# UAP — P13 PREP REPORT（Seed / Bootstrap）

> ## 状态
>
> ```text
> READ-ONLY · DESIGN PREPARATION
> P13 DECISION FREEZE = NOT YET
> P13 IMPLEMENTATION  = NOT AUTHORIZED
> ```
>
> 本报告是 **PREP（只读设计准备）**，不是实施记录。**未执行任何 DML/DDL**、**未创建 migration**、
> **未修改 code/test/config**。全部种子内容决策以 `P13_DECISION_RESOLUTION.md` 的
> `OQ-P13-01…14`（`HUMAN DECISION = PENDING` / `STATUS = PROPOSED`）为准。

---

## 1. Baseline（实测 · 2026-09-26）

```text
HEAD = 034ee97c…（tag UAP-V0.1.8-AUTHORIZATION · tags 8 · remote none）
alembic 单头 = 0015_p12_indexes（链长 15）· 0016+ = ABSENT · versions = 15
0010–0015 sha256 未变：6d990723…/cdaf8383…/5ecd1ef3…/da1bdffd…/3be9c8c0…/94b0d228…
D-PLAT-09 = P10 → P11 → P12 → P13 → Runtime（P10/P11/P12 = IMPLEMENTED / ACCEPTED）
```

**实测 schema 对象（fresh deploy @0015）**：

```text
物理表 = 35（31 业务 + 3 当月子分区 + alembic_version）
父级触发器 = 39（含 L=tg_audit_immutable + P11 G/H/I/J）· 触发器函数 = 21
P12 索引 = 19（12 FK 反查 + 7 P10，父表级 + 自动下推 13 子分区索引）· T-1 = ABSENT
FK / CHECK / UQ = P09 冻结形态（57 FK 口径 · MEASURE-1 已 APPROVED）
```

**实测种子数据现状（fresh deploy）**：

| 表 | 行数 | 内容 | 所有权 |
|---|---|---|---|
| `roles` | **1** | `platform_admin`（PLATFORM · is_system） | **0005 migration-controlled** |
| `platform_state` | **1** | `(1, 'uninitialized')` | **0006 migration-controlled** |
| `acl_subject_types` | 0 | — | 待 P13 |
| `permissions` / `role_permissions` | 0 | — | 待 P13（清单未定稿） |
| `users`/`identities`/`credentials`/`tenants`/`spaces`/`tenant_memberships`/`memberships`/`platform_memberships`/`resources`/`resource_permissions`/`agents`… | 0 | — | P13 / Runtime / bootstrap CLI |

> `0005._seed_system_roles()` 幂等语义（`WHERE NOT EXISTS`，R2 键 = scope+ownership+key）：
> `platform_admin` 全局 1 行；`tenant_admin/tenant_member`（TENANT scope）与
> `space_admin/space_member`（SPACE scope）**按既有 tenant/space 行补种** —— 0005 时点为 0 行
> ⇒ **P13 播种首租户/首空间时须按同一模式补种其系统角色**（非 0005 重跑）。

---

## 2. P13 Canonical Scope（权威材料交叉确认）

| 来源 | 对 P13 的定义 |
|---|---|
| `D-PLAT-09` | 路线 A 第 4 段：`P13`（Runtime 之前最后一步） |
| `D-PLAT-11`（FROZEN） | **首个正式可登录主体只经 P13 建立**；不引入第二套 dev bootstrap；P13 之前 `resource_permissions` 不可写入 |
| `STEP1B_SEED_STRATEGY.md` §1 | 10 步 seed 顺序 `[1] acl_subject_types → [2] permissions → [3] platform_admin → [4] 首租户+首管理员 → [5] tenant 角色 → [6] tenant_memberships → [7] 首空间 → [8] space 角色 → [9] memberships → [10] role_permissions（含 deny 行）` |
| `STEP1B_SEED_STRATEGY.md` R2/R4/R5 | 「定义 system role ≠ 授予 system role」：seed **永不写 `platform_memberships`**；bootstrap = 受信 CLI（`platform_state` 状态机，0006 已种 `uninitialized`）；首管理员密码由 onboarding 设置（**非 seed**） |
| `STEP1B_SEED_STRATEGY.md` §4 | permissions 字典**只定形状**（key 正则 `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$` · is_system=true）；**清单待人工审计** ⇒ OPEN |
| `STEP1B_SEED_STRATEGY.md` §5 | `acl_subject_types` = `user / role / agent` 三行；**不注册 group** |
| `D-P11-12` | P13 之前 triggers 必须就位（已满足）；P11 曾禁止的四类 INSERT（registry/bootstrap user/role/agent subject seed）**移交给 P13 处置** |
| `D-B14-*` / `B1-4_DECISION_LOG:58` | ACL 能力在 P13 seed 之后才可用（冻结顺序，非缺陷） |

**边界（确认排除）**：P13 ≠ runtime identity enrollment ≠ authorization runtime ≠ agent runtime ≠
scheduler/worker ≠ AI Gateway Runtime ≠ application startup ≠ test fixture（测试夹具走既有 fixture 模式，
不进 migration）。

---

## 3. SEED MATRIX（每条 seed 的 15 字段登记）

> 状态均为 **PROPOSED**（内容/是否实施由 OQ 裁定）；`seed_id` 命名为本报告登记号。

| seed_id | target_table | identity/natural key | columns（核心） | values（形状） | purpose | source authority | phase ownership | dependency | idempotency | uniqueness | FK prereq | trigger prereq | index prereq | downgrade |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S-01 | `acl_subject_types` | `key`（`uq_acl_subject_types_key` lower(key)+archived_at） | id, key, description | `user / role / agent` | 注册 ACL 主体类型（G 的分派根） | SEED_STRATEGY §5 · P2-02 | **P13**（表=P06） | 无（root） | WHERE NOT EXISTS by key（§6） | UQ 部分（archived_at IS NULL） | 无 | **C2 拦 runtime INSERT ⇒ 需受控 seed 路径（OQ-03）** | UQ 索引在位 | 删 3 行（natural key 可精确识别） |
| S-02 | `permissions` | `key` | id, key, resource_type, action, description, is_system | 平台级系统权限（**清单未定稿**：`system.*`/`tenant.*`/`space.*`/`member.*`/`resource.*`/`agent.execute`/`tool.execute`/`audit.read` 为形状示例） | 权限字典 root | SEED_STRATEGY §4（**清单 OPEN**） | **P13**（表=0005 形状） | 无（root） | WHERE NOT EXISTS by key | 待定（key UQ 形态实测核对） | 无 | 无 | 无 | 删 is_system=true ∧ key ∈ 清单（可精确） |
| S-03 | `roles` | scope+ownership+key（R2 键） | 同 0005 模式 | `platform_admin` 已存在 ⇒ **0 行**；确认不重复 | 内置角色（PLATFORM） | SEED_STRATEGY §2 · 0005 先例 | **0005 已拥有** | 无 | WHERE NOT EXISTS（0005 同款） | 三条部分 UQ | 无 | B/C 形状校验（scope） | 部分 UQ 在位 | 不适用（非 P13 行） |
| S-04 | `tenants` | slug（业务键） | slug, display_name, status | 首租户（**命名/是否属于 P13 ⇒ OQ-05**） | 引导主体容器 | SEED_STRATEGY §1[4] | **P13?（OQ-05）** | S-01…S-03 | WHERE NOT EXISTS by slug | `uq_tenants_slug` 类（实测） | 无 | D 类一致性与 F 族 | 常规 | 与 runtime 数据**不可区分** ⇒ OQ-12 |
| S-05 | `users` | email/username UQ | email, username, display_name, status | 首管理员用户（**无凭据**；密码由 onboarding 设置 ⇒ OQ-06） | 首个可登录主体容器（D-PLAT-11） | D-PLAT-11 · §1[4]/§6 | **P13?（OQ-06）** | S-04 | WHERE NOT EXISTS | `uq_users_email/username` | S-04（若含 tenant 归属列则依赖租户） | 无 | 常规 | 与 runtime 数据**不可区分** ⇒ OQ-12 |
| S-06 | `roles` | scope+ownership+key | 同上 | 首租户的 `tenant_admin` / `tenant_member`（TENANT scope ×2） | 租户内置角色 | SEED_STRATEGY §2 · 0005 补种模式 | **P13（首租户随播）** | S-04 | WHERE NOT EXISTS by (tenant_id,key) | 部分 UQ | S-04 | D/E/tm 族（scope 校验） | 部分 UQ 在位 | is_system=true + tenant 归属可识别；**与 runtime 租户的区分 ⇒ OQ-12** |
| S-07 | `tenant_memberships` | (tenant_id,user_id,role_id) | status='active' | 首管理员 → tenant_admin | 授予（**定义 ≠ 授予**的边界 ⇒ OQ-08） | SEED_STRATEGY R2 · §1[6] | **P13?（OQ-08）** | S-05,S-06 | 冲突即失败（R2：不 upsert） | 部分 UQ | roles+users+tenants | `tg_tm_role_scope`（拒绝错 scope） | 部分 UQ | OQ-12 |
| S-08 | `spaces` | key | tenant_id, key, name, kind, visibility, status | 首空间 | 空间容器 | SEED_STRATEGY §1[7] | **P13?（OQ-05 同族）** | S-04 | by (tenant_id,key) | UQ | S-04 | F/F2 一致性 | 常规 | OQ-12 |
| S-09 | `roles` | scope+ownership+key | 同上 | 首空间的 `space_admin` / `space_member`（SPACE scope ×2） | 空间内置角色 | SEED_STRATEGY §2 | **P13（首空间随播）** | S-08 | 同 S-06 | 部分 UQ | S-08 | B/scope | 部分 UQ | OQ-12 |
| S-10 | `memberships` | (space_id,user_id,role_id) | status='active' | 首成员 → space_admin | 授予（OQ-08 同族） | SEED_STRATEGY §1[9] | **P13?（OQ-08）** | S-05,S-09 | 冲突即失败 | 部分 UQ | 全链 | `tg_membership_role_scope` | 部分 UQ | OQ-12 |
| S-11 | `role_permissions` | (role_id,permission_id,effect) | effect ∈ allow/deny（**含 deny 行**） | 内置角色 ↔ 权限绑定（依赖 S-02 清单） | 角色能力 | SEED_STRATEGY §1[10] · §4 | **P13（依赖 OQ-01 清单）** | S-02,S-03,S-06,S-09 | 冲突即失败 | UQ/部分（实测核对） | permissions+roles | 无（无 trigger） | `ix_role_permissions_permission`（P02 先例） | is_system 关联可识别 ⇒ OQ-12 |
| S-12 | `platform_memberships` | — | — | **不种子**（R4/R5：bootstrap CLI 专属） | 平台管理员授予 | R4/R5 状态机 · `tg_pm_bootstrap_gate` | **部署期 CLI（非 P13）** | — | — | — | — | `tg_pm_bootstrap_gate`/`tg_pm_last_admin` | — | — |
| S-13 | `agents` 等 | — | — | **不种子**（仅注册 `agent` **subject type**；不建实际 Agent） | — | 指令 §8 · SEED_STRATEGY | — | — | — | — | — | — | — | — |

**MANDATORY / OPTIONAL / TEST FIXTURE / RUNTIME 分类（PROPOSED）**：
`S-01` = MANDATORY（ACL 根，无争议）· `S-02/S-11` = MANDATORY-but-content-OPEN（清单待人工审计）
· `S-04…S-10` = **PROPOSED**（「首租户/首管理员是否属于 migration seed」= OQ-05/06/07/08 的核心分歧：
R4/R5 状态机与 D-PLAT-11 的张力）· TEST FIXTURE = 永不进 migration（既有 fixture 模式）·
RUNTIME-CREATED = onboarding 播种（非 P13）。

---

## 4. 所有权映射（防重复纳入）

| 对象 | 所有权 | P13 行为 |
|---|---|---|
| `platform_admin` 角色行 | **0005**（已实测 1 行） | **不重建**；S-03 仅校验存在 |
| `platform_state(1,'uninitialized')` | **0006** | 不触碰；bootstrap CLI 翻转 |
| `tenant_admin/tenant_member/space_admin/space_member` | **onboarding/补种模式**（0005 对既有行） | 首租户/首空间时按同款补种（PROPOSED） |
| `platform_memberships` 首行 | **受信 bootstrap CLI**（R4/R5 · `tg_pm_bootstrap_gate`） | **P13 禁止写入** |
| 首管理员**凭据** | onboarding 流程 | **P13 禁止明文凭据/伪造密码**（OQ-13） |
| `groups` | 不存在（P2-02） | 不注册 subject type |

---

## 5. 依赖图（FK / trigger / index 静态序）

```text
[无环]
acl_subject_types ─┐
permissions ───────┤
roles(platform) ───┤
tenants ──→ roles(tenant) ──→ tenant_memberships ──┐
   └────→ spaces ──→ roles(space) ──→ memberships ──┤
users ──────────────────────────────────────────────┤
permissions + roles ──→ role_permissions ───────────┘
（resource_permissions 本阶段 0 行 ⇒ G 不触发；无 deferred FK ⇒ 无延迟约束问题）
```

- **无循环依赖**；deferred FK：**无**（既有 FK 均非 DEFERRABLE，`0011` 的尾部 ALTER 亦 `condeferrable=false`）。
- **C2 是唯一的前置约束冲突点**：`tg_acl_subject_types_protect` BEFORE INSERT 拒绝 runtime INSERT ⇒
  S-01 需要**受控 seed 路径**（候选：migration 事务内 `ALTER TABLE … DISABLE TRIGGER` + 复原（测试夹具先例
  `test_resource_acl_schema.py:171-184`）· `session_replication_role = replica`（需超级用户）· 或新决策豁免）
  —— **PROPOSED，OQ-03 裁定**。
- **G/H/I/J 对 seed 的影响（实测语义）**：G 仅触发于 `resource_permissions` INSERT/UPDATE（P13 零行 ⇒ 不触发）；
  H 仅 user 硬删（不触发）；I 仅 role DELETE（不触发）；J 仅 agent 归档/删除（不触发）。
  **结论：seed 顺序唯一需要适配的是 C2**（registry protection → controlled seed，指令 §5）。
- **索引就绪**：seed 查询路径（`uq_acl_subject_types_key` · roles 三条部分 UQ · `uq_users_email/username` ·
  `ix_role_permissions_permission` · P12 的 19 条）全部在位 ⇒ **无 seed-specific 新索引需求**（指令 §12）。

---

## 6. 幂等 / 重放（以冻结材料为准，不发明）

```text
SEED_STRATEGY §6：platform_admin / acl 三行 / permissions 用 ON CONFLICT / WHERE NOT EXISTS 只插一次；
R2：幂等键 = scope + tenant/space ownership + key；【重复执行冲突 ⇒ 失败，不做 upsert 覆盖】（保证确定性）
R4/R5：bootstrap 条件 = platform_state 状态机 + PM 无行；seed 永不写 PM
失败重试：单事务，失败整体回滚
```

⇒ P13 设计约束（PROPOSED）：**不**引入统一 `ON CONFLICT DO NOTHING` 改写语义（指令 §10 禁止）；
registry/permissions 用 WHERE NOT EXISTS（与 §6/0005 先例一致）；membership 类冲突即失败。

## 7. 降级语义（OQ-12 登记为 BLOCKING）

```text
可精确识别（natural key）：S-01（key ∈ {user,role,agent}）· S-02（key ∈ 冻结清单 ∧ is_system）
                          · S-06/S-09（is_system=true ∧ 归属 = seed 建的租户/空间）
不可精确区分：S-04/S-05/S-08（首租户/首用户/首空间）—— 若 runtime 已在其下产生数据
              （memberships、credentials、resources…），机械 DELETE 将违反「禁止误删运行后数据」。
⇒ 登记为 BLOCKING OQ-P13-12/14：候选方向（仅登记，不自行发明）：
   (a) downgrade = 仅删除 migration-owned 且未被 runtime 引用的行（RESTRICT 自然保护 + 显式 key 过滤）
   (b) downgrade = NO-OP（保留数据）+ 文档声明「P13 降级不回收业务数据」
   (c) 禁止在有任何 runtime 数据后降级（fail-closed 检查）
```

## 8. 安全分析（OQ-13）

无明文凭据 / 无伪造密码 / 无环境 secret 进入 migration；首管理员凭据归 onboarding（§6 已冻结）；
bootstrap CLI 凭据独立（R4）；seed 行不含敏感数据。**OPEN**：D-PLAT-11 要求「首个可登录主体经 P13」，
但 users 行无凭据不可登录 ⇒ **「可登录」的完成机制（onboarding 设密流程）属 Runtime Slice**，
P13 只建立 user 容器行 —— 该解释 PROPOSED，请 Human 裁定（OQ-06）。

## 9. 跨决策扫描（Charter §7 · 本轮执行）

```text
扫描：PLATFORM_DECISION_LOG（D-PLAT 17 / D-AUTH 25 / D-AGENT 16 / D-P10 18 / D-P11 14 / D-P12 15）
      + AGENT_RUNTIME_*（P13 定义引用一致）+ B1-4_DECISION_LOG（「ACL 能力 P13 后可用」一致）
      + STEP1B_SEED_STRATEGY（R2/R4/R5 与 D-PLAT-11 并读）
结果：ACTIVE vs FROZEN 无冲突 · FROZEN vs FROZEN 无冲突 ·
      SCHEMA vs DECISION：permissions/roles/role_permissions/acl_subject_types 形状与冻结一致；
      唯一张力 = D-PLAT-11「可登录主体经 P13」 vs R4/R5「seed 不含凭据」 ⇒ OQ-06（非冲突，需澄清裁定）
supersession 恒 = 1（D-B14-08）· 本轮不产生新决策、不改写任何冻结正文
陈旧声明扫描（raw/adjudicated）：「P13 才有 seed」类声明 11+ 处全部为**现行有效**描述，无陈旧项。
```

## 10. 连带同步面（实施期预估 · PROPOSED）

```text
head 断言 0015 → 0016（16 文件既有模式）· 链长 15 → 16 · AM5 父节点 → 0015
seed 断言：新套件 test_p13_seed.py（registry 3 行 / permissions 清单 / 角色-绑定 / 负例同规则）
既有「zero seed」类断言（identity/p11/p12/p10 的 count==0 守卫）将翻转 —— 逐文件登记于实施轮
C2 相关：resource_acl 套件的 REG-01（runtime INSERT denied）必须保持通过（seed 走受控路径，不改 C2）
```

## 11. OQ 清单 → `P13_DECISION_RESOLUTION.md`

`OQ-P13-01…14` 全部 `HUMAN DECISION = PENDING` / `STATUS = PROPOSED`（§15 指令清单，无增删；
其中 OQ-12 降级安全 = **BLOCKING**（§14 指令：无可靠区分机制即 blocking））。

---

**END OF P13 PREP REPORT（2026-09-26 · READ-ONLY · DESIGN PREPARATION ONLY）**
