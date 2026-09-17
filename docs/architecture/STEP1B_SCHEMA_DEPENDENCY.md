# STEP 1-B / B0 — Schema Dependency Graph

Status: **DESIGN PREPARATION — 不创建任何表**
来源：STEP 1-A 冻结设计（`CORE_DOMAIN_MODEL.md` + `ER_MODEL.md`，Round 3 版本）
基线：`72ade9f` · `UAP-V0.1.0-INIT-DB-VALIDATED`

> 本文档是 **B0 实施准备**产物：只回答"表按什么顺序、以什么约束安全创建"，不实际执行任何 DDL。

---

## 1. 表清单与依赖总表

共 **29 张正式表 + 1 张可选表（`resource_relations`，P2，B1 不建）**。每张表列出：直接依赖的表、依赖方式（FK 源 → FK 目标）、删除行为。

### 1.1 Identity 域（4 依赖 + users root）

| 表 | 依赖 | FK（→ 目标，删除行为） | 是否 root |
|---|---|---|---|
| `users` | — | — | ✅ **ROOT** |
| `identities` | users | `user_id → users.id CASCADE` | |
| `credentials` | users, identities | `identity_id → identities.id CASCADE`；`user_id → users.id CASCADE` | |
| `devices` | users | `user_id → users.id CASCADE` | |
| `sessions` | users, identities, devices | `user_id → users.id CASCADE`；`identity_id → identities.id RESTRICT`；`device_id → devices.id CASCADE` | |

### 1.2 Tenant / Space / Role / Membership（2 root + 4 依赖）

| 表 | 依赖 | FK | root |
|---|---|---|---|
| `tenants` | — | — | ✅ **ROOT** |
| `spaces` | tenants | `tenant_id → tenants.id RESTRICT` | |
| `roles` | tenants, spaces（均 NULL 允许） | `tenant_id NULL → tenants.id CASCADE`；`space_id NULL → spaces.id CASCADE` | |
| `permissions` | — | — | ✅ **ROOT** |
| `role_permissions` | roles, permissions | `role_id → roles.id CASCADE`；`permission_id → permissions.id CASCADE` | |
| `tenant_memberships` | tenants, users, roles | `tenant_id → tenants.id CASCADE`；`user_id → users.id CASCADE`；`role_id → roles.id RESTRICT` | |
| `memberships` | tenants, spaces, users, roles | `tenant_id → tenants.id CASCADE`（冗余）；`space_id → spaces.id CASCADE`；`user_id → users.id CASCADE`；`role_id → roles.id RESTRICT` | |
| `platform_memberships` ⏳（**R3-D-07 Option A，未建表**） | users, roles | `user_id → users.id CASCADE`；`role_id → roles.id RESTRICT`（仅 PLATFORM scope）；`UNIQUE(user_id) WHERE status='active'`；`tg_pm_role_scope` / `tg_pm_last_admin` | 依赖 roles → 置于 P04 之后 |

### 1.3 Resource / ACL 域（2 root）

| 表 | 依赖 | FK | root |
|---|---|---|---|
| `acl_subject_types` | — | — | ✅ **ROOT**（注册表） |
| `resources` | tenants, spaces, users | `tenant_id → tenants.id RESTRICT`（P2-03）；`space_id NULL → spaces.id RESTRICT`（P2-03）；`owner_id NULL → users.id SET NULL` | |
| `resource_permissions` | resources, acl_subject_types, users | `resource_id → resources.id CASCADE`（受控 purge 时）；`subject_type_id → acl_subject_types.id RESTRICT`；`granted_by NULL → users.id` | |
| `resource_relations`（P2 可选，B1 不建） | resources | `parent_id/child_id → resources.id CASCADE` | |

### 1.4 Tool 域（1 root）

| 表 | 依赖 | FK | root |
|---|---|---|---|
| `tools` | tenants（NULL = 平台内置） | `tenant_id NULL → tenants.id RESTRICT` | ✅ **ROOT**（除 tenants 外无出边） |
| `tool_versions` | tools | `tool_id → tools.id CASCADE` | |
| `tool_permissions` | tools, tool_versions, permissions | `tool_id → tools.id CASCADE`；`version_id NULL → tool_versions.id CASCADE`；`permission_id → permissions.id CASCADE` | |
| `tool_executions` | tenants, tools, tool_versions, agents, users | `tool_id → tools.id RESTRICT`；`tool_version_id → tool_versions.id RESTRICT`；`agent_id NULL → agents.id`（**Agent phase 后补 / 随 Agent 创建**）；`actor_id NULL → users.id` | |

> `tool_executions.agent_id` 使 tool_executions 依赖 agents —— 见 §4 的 phase 调整。

### 1.5 Agent 域（依赖 ai_routes → 依赖 AI 域）

| 表 | 依赖 | FK | root |
|---|---|---|---|
| `agents` | tenants, spaces, users, **ai_routes**, **agent_versions** | `owner_id → users.id`；`current_version_id NULL → agent_versions.id SET NULL`；`default_route_id NULL → ai_routes.id SET NULL` | |
| `agent_versions` | agents, users | `agent_id → agents.id CASCADE`；`published_by NULL → users.id` | |
| `agent_permissions` | agents, agent_versions, permissions, **tools** | `agent_id → agents.id CASCADE`；`version_id NULL → agent_versions.id CASCADE`；`permission_id NULL → permissions.id`；`tool_id NULL → tools.id` | |

> **关键点**：`agents.current_version_id → agent_versions` 且 `agent_versions.agent_id → agents` 构成 **循环**；`agent_permissions.tool_id → tools` 使 Agent 域依赖 Tool 域。

### 1.6 AI Gateway 域（1 root）

| 表 | 依赖 | FK | root |
|---|---|---|---|
| `ai_providers` | — | — | ✅ **ROOT** |
| `ai_models` | ai_providers | `provider_id → ai_providers.id CASCADE` | |
| `ai_routes` | ai_models, tenants, spaces（tenant/space NULL 允许） | `primary_model_id → ai_models.id RESTRICT`；`tenant_id NULL → tenants.id RESTRICT`；`space_id NULL → spaces.id RESTRICT` | |
| `ai_policies` | tenants/spaces（NULL 允许） | `tenant_id NULL → tenants.id RESTRICT`；`space_id NULL → spaces.id RESTRICT` | |
| `ai_request_logs` | ai_providers, ai_models（`agent_id` 仅记录用途，无 FK ⇒ 不构成依赖） | 分区表；`provider_id NULL → ai_providers.id RESTRICT`；`model_id NULL → ai_models.id RESTRICT`；`agent_id` / `actor_id` / `tenant_id` / `space_id` **无 FK**（不构成 P08→P09 前向依赖） | |

### 1.7 Event / Audit 域（弱依赖）

| 表 | 依赖 | FK | 说明 |
|---|---|---|---|
| `events` | tenants/spaces（NULL 允许） | 无强制 FK（事实日志，避免租户删除被历史事件阻塞） | 分区表 |
| `audit_logs` | tenants/spaces（NULL 允许） | 无强制 FK | 分区表；不可变 |

---

## 2. Root Tables（无前置依赖，最先可建）

| Root | 说明 |
|---|---|
| `users` | 全局主体，零依赖 |
| `tenants` | 租户边界，零依赖 |
| `permissions` | 权限字典，零依赖 |
| `acl_subject_types` | ACL 类型注册表，零依赖 |
| `ai_providers` | AI 厂商注册，零依赖 |
| `tools` | 平台工具注册，零依赖（tenant_id NULL 无强制 FK） |

---

## 3. 必须先创建的表（按拓扑排序结果）

```
users, tenants, permissions, acl_subject_types, ai_providers, tools          [root]
  └→ identities, credentials, devices, spaces, ai_models, tool_versions        [第 1 层]
      └→ sessions(还需 identities+devices), roles(还需 tenants/spaces),
         ai_routes(还需 ai_models), tool_permissions(还需 permissions)         [第 2 层]
          └→ role_permissions, tenant_memberships, memberships,
             resources(还需 users)                                              [第 3 层]
              └→ resource_permissions(还需 acl_subject_types),
                 ai_policies, ai_request_logs                                    [第 4 层]
                └→ agents(default_route→ai_routes; 但 current_version 循环),
                   agent_permissions(还需 tools)                                [第 5 层]
                 └→ agent_versions(依赖 agents; 与 agents.current_version 成环)
                    tool_executions(还需 tools+agent_versions+agents)           [第 6 层]
                   └→ events, audit_logs                                        [第 7 层]
```

详细拓扑推导见 §5。

---

## 4. 循环 FK 识别与解法

### 4.1 `agents ↔ agent_versions`（真循环）

```
agents.current_version_id ──(SET NULL)──→ agent_versions.id
agent_versions.agent_id   ──(CASCADE)──→ agents.id
```

**解法（标准 deferred FK）**：
1. 建 `agents` 时**不含** `current_version_id` 的 FK 约束（列存在，仅无约束）
2. 建 `agent_versions`（其 `agent_id → agents` 正常声明）
3. 最后 `ALTER TABLE agents ADD CONSTRAINT fk_agents_current_version FOREIGN KEY (current_version_id) REFERENCES agent_versions(id) ON DELETE SET NULL;`

> 因为 `current_version_id` 在正常生命周期大多为 NULL（发布后才回填），SET NULL 语义下延后补 FK 无数据风险。该约束加入 Phase 08 尾部。

### 4.2 前向依赖（非循环但跨概念域）

| 前向依赖 | 解法 |
|---|---|
| `agent_permissions.tool_id → tools.id` | **把 Tool 域排到 Agent 域之前**（phase 顺序对调：Tool 先、Agent 后）。语义也正确：Tool 是基础能力，Agent 是使用 Tool 的执行实体 |
| `agents.default_route_id → ai_routes.id` | AI Gateway 域排到 Agent 域之前（AI 无核心前置依赖，可提前） |
| `tool_executions.agent_id → agents.id` | `tool_executions` 移到 Agent phase 内创建（在 agents/agent_versions 之后） |

### 4.3 伪循环排查（已排除）

- `roles.tenant_id → tenants` 与 `roles.space_id → spaces`：roles 只是"可属于"tenant/space，无反向边 → 非循环
- `tenant_memberships → roles` 且 `memberships → roles`：roles 不引用 memberships → 非循环
- **PLATFORM role 的唯一消费者 = `platform_memberships`（R3-D-07 Option A，设计冻结、未建表）**：TM/M trigger 拒绝引用 PLATFORM role；新表置于 roles（P04）之后创建，不产生新循环；实施前平台授权语义仍对平台级请求 fail-closed
- `resources.owner_id → users` + `users` 无出边指向 resources → 非循环

---

## 5. 调整后的 Migration Phase 顺序（基于真实 FK，非机械照抄）

用户草案的 Agent(06)/Tool(07)/AI(08) 顺序与依赖冲突（agent_permissions 需要 tools、agents 需要 ai_routes），**调整为 Tool→AI→Agent**：

| Phase | 内容 | 说明 |
|---|---|---|
| **P00** | 扩展 / DB primitives | `uuid`（内置）、`citext`（若用，见 §10）、plpgsql、`uap_uuid_v7()`、`set_updated_at()` 函数（**先建函数，trigger 后挂**） |
| **P01** | Root identity | `users` |
| **P02** | Identity 附属 | `identities` → `credentials` → `devices` → `sessions` |
| **P03** | Tenant / Space | `tenants` → `spaces` |
| **P04** | Role / Permission | `permissions` → `roles`（tenant_id/space_id 可 NULL）→ `role_permissions` |
| **P05** | Membership | `tenant_memberships` → `memberships`（两者依赖 roles，故在 P04 后） |
| **P06** | Resource / ACL | `resources` → `acl_subject_types` → `resource_permissions` |
| **P07** | Tool | `tools` → `tool_versions` → `tool_permissions` |
| **P08** | AI Gateway | `ai_providers` → `ai_models` → `ai_routes` → `ai_policies` → `ai_request_logs` |
| **P09** | Agent（含执行日志） | `agents`（**无** current_version FK）→ `agent_versions` → `agent_permissions` → `tool_executions` → **补** `agents.current_version_id` FK |
| **P10** | Event / Audit | `events` → `audit_logs`（分区父表 + 初始子分区） |
| **P11** | Triggers / 跨表约束 | 见 [STEP1B_TRIGGER_INVENTORY.md](./STEP1B_TRIGGER_INVENTORY.md)；**必须在 seed 前全部就位** |
| **P12** | Indexes | 非 PK 索引（见 [STEP1B_INDEX_STRATEGY.md](./STEP1B_INDEX_STRATEGY.md)）；部分唯一索引可在建表时内联或此处统一 |
| **P13** | Seed / built-in data | 见 [STEP1B_SEED_STRATEGY.md](./STEP1B_SEED_STRATEGY.md) |

> **调整说明（对草案的偏差）**：① Agent/Tool/AI 顺序对调为 Tool(07) → AI(08) → Agent(09)，消除 `agent_permissions→tools` 与 `agents→ai_routes` 前向依赖；② `tool_executions` 从 Tool phase 挪到 Agent phase 尾部（依赖 agents）；③ Triggers 集中在 P11 但**逐条声明所属 phase 的依赖先决**；④ 部分唯一索引若内联建表则不需要 P12 单独执行，P12 只保留"纯查询索引"。

### 每 Phase 交付格式

每个 phase 的执行文件都应包含以下段落（B1 编写 migration 时按此模板）：

```
Phase NN
Tables     : <表清单>
Dependencies : <本 phase 依赖的已有表>
Constraints  : <PK/FK/UQ/CK；DDL 内联>
Triggers     : <挂在本 phase 表上的 trigger；若依赖 P11 跨表 trigger 则标注延迟>
Indexes      : <建表即建的部分唯一索引 vs 延迟索引>
Seed requirement : <无 / 有（描述）>
Rollback consideration : <downgrade 动作：DROP 顺序与依赖>
```

**P00-P10 均无 seed 需求；P13 才有 seed。所有 trigger（P11）必须先于 P13 seed。**

---

## 6. 哪些表可以并行创建

同一 phase 内无相互依赖的表可并行（同一 migration 事务内顺序执行也安全）：

| 并行组 | 表 | 理由 |
|---|---|---|
| P01 单表 | `users` | root |
| P02-a | `identities`、`credentials`、`devices` | 三者都只依赖 users；credentials 同时依赖 identities（放同组尾） |
| P02-b | `sessions` | 依赖 identities+devices+users |
| P03 | `tenants` 先行，`spaces` 单行 | spaces 依赖 tenants |
| P04-a | `permissions` 与 `roles` | 互不依赖 |
| P04-b | `role_permissions` | 依赖两者 |
| P05-a | `tenant_memberships` / `memberships` | 依赖集合相同（tenants/users/spaces/roles） |
| P06 | `resources`、`acl_subject_types` | 互不依赖（resource_permissions 后） |
| P07 | `tools` / `tool_versions` / `tool_permissions` 顺序链 | 链式 |
| P08 | `ai_providers`/`ai_models`/`ai_routes`/`ai_policies`/`ai_request_logs` | 链式 + 并行（ai_policies 与 ai_request_logs 可并行） |
| P09 | `agents`、`agent_versions`、`agent_permissions`、`tool_executions` | 顺序链（见循环解法） |

---

## 7. 哪些 trigger 必须在 seed 后创建

**答案：没有。** 所有 trigger 必须在 seed（P13）**之前**创建：

- trigger 是数据不变式的强制者；seed 数据（platform_admin / tenant_member / acl subject 等）同样必须通过 trigger 校验
- 若 seed 先行而 trigger 后建，seed 中万一有违规数据（如错误的 role scope）将"带病入库"且无法追溯
- **唯一例外**：无。即便 seed 需要的 `uap_uuid_v7()` 函数（P00）也只是函数，不是 trigger

### P11 trigger 的 phase 级先决（依赖哪些表已存在）

| Trigger | 依赖已存在 | 最早可挂 |
|---|---|---|
| `tg_set_updated_at`（每张带 updated_at 的表） | 本表自身 | 各表建时即可（P01–P10 内联） |
| `tg_roles_scope_shape`（scope ↔ tenant_id/space_id 匹配） | roles | P04 |
| `tg_roles_is_system_protect`（is_system 禁改删） | roles | P04 |
| `tg_tm_role_scope`（tenant_memberships.role_id → TENANT scope + 同租户） | tenant_memberships + roles | P05 |
| `tg_membership_role_scope`（memberships.role_id → SPACE scope + 同空间） | memberships + roles | P05 |
| `tg_membership_tenant_consistency`（memberships.tenant_id = spaces.tenant_id） | memberships + spaces | P05 |
| **`tg_resources_tenant_space_consistency`（resources.tenant_id = spaces.tenant_id，`space_id` 非空时；**structural integrity only —— 不做 authorization evaluation**）** | **resources + spaces（均已存在）** | **P06（R1 增补 · D-B14-10 = A-1）** |
| **`tg_acl_subject_types_protect`（platform-controlled registry 保护：运行时 INSERT / `key` UPDATE / DELETE 拒绝；**registry governance only —— 不做 authorization evaluation**）** | **acl_subject_types（已存在）** | **P06（R4 增补 · D-B14-12 = A）** |
| `tg_acl_subject_exists`（subject 存在性 user/role/agent） | resource_permissions + acl_subject_types + users/roles/agents | P09 之后（依赖 agents 表） |
| `tg_acl_user_hard_delete`（用户硬删清理 ACL） | users + resource_permissions | P09 后 |
| `tg_acl_role_delete_block`（role 被 ACL 引用禁删） | roles + resource_permissions | P09 后 |
| `tg_version_immutable`（agent_versions/tool_versions published 禁改删） | 各自表 | 表建时 |
| `tg_audit_immutable`（audit_logs 禁 UPDATE/DELETE） | audit_logs | P10 |

> 上表是 trigger **最早**可挂的 phase。B1 落地时可统一在 P11 执行（更易审计），但依赖表的缺失会造成 P11 建 trigger 失败 —— 因此 P11 的 trigger DDL 也必须按上表顺序排列。
>
> **R1 增补（2026-09-13 · D-B14-10 = A-1）**：新增 `tg_resources_tenant_space_consistency` = **P06**（依赖 `resources` + `spaces`，二者在 P05/P06 已存在，**无未来对象依赖**）。该行**为插入新增，未重排既有行**；**G/H/I/J 仍保持 P09 后**。
>
> **R4 增补（2026-09-13 · D-B14-12 = A）**：新增 `tg_acl_subject_types_protect` = **P06**（依赖 `acl_subject_types`，P06 创建，**无未来对象依赖**）。该行**为插入新增，未重排既有行**；**G/H/I/J 仍保持 P09 后**。边界：**registry governance only，不做 authorization evaluation**。

---

## 8. 哪些 constraint 必须在 seed 前存在

**全部 PK / FK / UQ / CK / NOT NULL + 部分唯一索引都必须在 seed 前存在**（它们是表定义的一部分，P01–P10 建表时声明）。

seed 数据（P13）必须满足：
- `roles.scope` 与 key 匹配内置目录（CK + 部分唯一）
- `tenant_memberships.role_id` 默认落到 `tenant_member`（应用层写入；trigger 校验）
- `acl_subject_types` 初始三行 user/role/agent（CK 白名单）
- seed 写入 `users`/`tenants`/`spaces` 的 owner 关系满足 FK

**结论**：无任何 constraint 需要 seed 之后才建立。

---

## 9. 分区表（events / audit_logs / ai_request_logs）注意事项

- 建父表（`PARTITION BY RANGE (occurred_at)`）+ 当月子分区，子分区继承 PK `(id, occurred_at)`
- 部分唯一索引 / 查询索引建在父表（PG 自动下推到子分区）
- FK：`events.tenant_id/space_id` 与 `audit_logs.tenant_id/space_id` 不设强制 FK（见 §1.7），避免租户长期历史事件阻塞 purge
- migration downgrade 时先 DROP 子分区再 DROP 父表

---

## 10. 扩展依赖（Extension）

| 扩展 | 用途 | 决策（Round 3 已定） |
|---|---|---|
| `pgcrypto` | `gen_random_uuid()`（PG 13+ 内置，无需扩展） | **不引 pgcrypto** |
| `citext` | email/username 大小写不敏感 | **不依赖**：统一用 `text` + `lower()` 表达式（推荐零依赖） |
| 无其它扩展 | — | 平台基线保持最小 |

`uap_uuid_v7()` 纯 plpgsql + 内置函数实现，无扩展依赖（见 [STEP1B_UUID_STRATEGY.md](./STEP1B_UUID_STRATEGY.md)）。

---

## 11. 一致性交叉核对

- 与 `CORE_DOMAIN_MODEL.md` Entity Catalog：表数 29 + 1 可选一致；FK 方向与删除行为逐项一致
- 与 `ER_MODEL.md` 关系矩阵：`tenants→resources` / `spaces→resources` 为 RESTRICT（P2-03）✓
- 与 `STEP1A_DESIGN_REPORT.md` §20（B0→B4 分批）：本文档的 P00–P13 对应 B1 的物理 migration 顺序
- `groups`：本依赖图中**不存在** `groups` 表，任何 trigger/FK 不引用它（P2-02）✓

### R4 注记（2026-09-08 D-07 Hardening）
- `platform_memberships`（⏳ 未建表）生命周期补充：**re-grant = UPDATE 本行**（UQ user+role 非部分，禁止 INSERT 新行）；首行写入 = bootstrap（一次性，PM 行数=0 时）；信任根不变量 = effective_platform_admin 计数 ≥1（`tg_pm_last_admin` + roles 侧 `tg_roles_pm_lifecycle` 双层）；user 停用先 revoke（PMB-4），CASCADE 仅 hard-delete purge 终态。依赖关系不变（users + roles），无新循环。

### R5 注记（2026-09-08 Hardening）
- 新增 `platform_state`（0006，**已建**）：单例行、零业务 FK；`tg_platform_state_guard`（单向 uninitialized→initialized）+ `tg_pm_bootstrap_gate`（PM INSERT 门）。依赖：无（root）；不产生循环。bootstrap 判据 = state='uninitialized' ∧ PM 空；CASCADE/硬删不触 state。
