# B1-4 — Scope Definition（PREP / DESIGN ONLY）

Status: **B1-4 PREP — 不建表、不写 migration、不执行 DDL、不改代码**
前置：`B1-3 FINAL HUMAN AUDIT = APPROVED`（含 live evidence recheck，128 passed）
当前 Alembic head：`0006_b1_3_bootstrap_state`
来源（唯一依据）：`STEP1B_SCHEMA_DEPENDENCY.md` §5 P06 · `CORE_DOMAIN_MODEL.md` §1.3 · `STEP1B_ACL_STRATEGY.md` · `STEP1B_CONSTRAINT_MATRIX.md` §3 · `STEP1B_INDEX_STRATEGY.md` · `STEP1B_SEED_STRATEGY.md` §5 · `STEP1B_TRIGGER_INVENTORY.md`

---

## 1. B1-4 的准确目标

**B1-4 = P06「Resource / ACL」基础层**：把"任何可被授权的对象"从散落的业务概念收敛为**平台级资源注册表 + 资源级 ACL**，使 B1-1~B1-3 建立的 **身份 / 租户 / 空间 / 角色 / 权限** 首次获得**作用对象（object）**，从而形成完整的最小授权闭环：

```
Identity → Membership → Role → Permission   (B1-1 ~ B1-3：主体与能力)
                     +  Resource / ACL      (B1-4：对象与实例级授权)
                     =  可评估的授权请求
```

### 1.1 本阶段解决的 Core 能力

| 能力 | 说明 |
|---|---|
| **统一资源注册（object registry）** | Core 只管理资源的`身份、归属、分类、状态`，不理解业务语义 → 业务表通过 **1:1 共享主键**挂到 `resources`（本阶段只建 registry，不建任何域扩展表） |
| **资源归属与隔离** | `resources.tenant_id`（NN, RESTRICT）+ `space_id`（NULL 允许, RESTRICT）+ `owner_id`（NULL, SET NULL）→ 租户/空间隔离的物化落点 |
| **分类与状态机** | `classification`（PUBLIC/INTERNAL/CONFIDENTIAL/HIGHLY_CONFIDENTIAL）+ `status`（active→archived→deleted）→ 与 AI 厂商降级、审计等级、purge 策略的公共输入 |
| **ACL 主体注册机制** | `acl_subject_types` 注册表：把"subject 是多态"从字符串拼接升级为受控注册 + 校验（P1/P2-04 冻结） |
| **资源级显式授权/拒绝** | `resource_permissions`：`(resource, subject, action) → allow/deny`，含 `conditions`（storage-only）与 `expires_at` |

### 1.2 为什么必须在这一阶段（而不是更早/更晚）

1. **更早不可**：`resources` 依赖 `tenants` / `spaces` / `users`；`resource_permissions` 依赖 `acl_subject_types`。B1-1~B1-3 才使这些父表存在（B0 DEPENDENCY §3 拓扑排序：resources 位于第 3 层，resource_permissions 第 4 层）。
2. **更晚有害**：P07 Tool / P08 AI / P09 Agent 均以 `resources` 为公共归属与 ACL 挂载点；`agent_permissions.tool_id → tools.id` 与 `tool_executions.agent_id → agents.id` 的前提链已经很长。若资源层缺位，后续每个域都会**各自发明**一套归属与授权，直接违反架构铁律（`Space.kind` 运行时数据、Core 无行业词汇）。
3. **与本阶段的顺序一致性**：B0 §5 明确 `P06 Resource / ACL = resources → acl_subject_types → resource_permissions`，紧跟 B1-3 的 P04/P05。

### 1.3 明确不属于 B1-4 的能力

| 不属于 | 归属 | 理由 |
|---|---|---|
| 任何 **Domain 表**（family / company / business / entertainment 的业务列） | Domain 层（永不进 Core migration） | `domains/* → core/*` 单向；域扩展表以 1:1 共享主键挂 `resources`，由域模块负责 |
| `resource_relations`（层级边） | 明确 **defer**（B0 Q3 决策：先用扁平 `space_id`） | 引入递归权限评估成本，无真实需求 |
| Tool / AI / Agent 域 | P07 / P08 / P09 | 依赖顺序在 `resources` 之后 |
| `events` / `audit_logs` | P10 | 分区 + outbox 复杂度独立；ACL 变更审计依赖 `audit_logs` 存在（见 D-B14-07） |
| **授权决策引擎 / ABAC evaluator** | 后续「Authorization Layer」阶段 | 本阶段只建**数据结构**；`conditions` **storage-only**（R2-D-15 冻结） |
| permission 字典（`permissions` 行） | 授权语义阶段（B0 P3 遗留） | 不得发明字典（B1-3 已冻结 0 行） |
| HTTP / Socket 接口实现 | 见 `B1-4_API_DESIGN.md`（本阶段只冻结契约） | B1-4 为 schema 阶段 |
| RLS 启用 | OPEN（Q1 / R5-D-04） | 不启用、不建 policy |

### 1.4 In / Out 清单

**IN（本阶段唯一可实施范围）** —— **Revision R1 修订：移除 seed，ACL trigger 归零**
1. `resources` 表
2. `acl_subject_types` 表（**不含任何 seed 行** —— 三行 `user`/`role`/`agent` 属 **P13**，见 D-B14-01）
3. `resource_permissions` 表
4. 三表所需的 PK / FK / UQ / CK / NN / INDEX
5. **trigger 3 个**（**R4 更新：D-B14-10 = A-1 / D-B14-12 = A 均已 FROZEN**）
   ① `tg_resources_set_updated_at`（复用 B1-1 `set_updated_at()`）
   ② `tg_resources_tenant_space_consistency`（**D-B14-10 = A-1 FROZEN**；`structural integrity only`）
   ③ `tg_acl_subject_types_protect`（**D-B14-12 = A FROZEN**；`registry governance only`）
   · **不实施** G/H/I/J（冻结为"最早 P09 后"，见 D-B14-02）
6. migration `0007_b1_4_resource_acl`（down_revision = `0006_b1_3_bootstrap_state`）+ 对应测试

> **R1 修订说明**：上一轮把"`acl_subject_types` 初始 seed"与"ACL 校验 trigger（G/H/I 提前）"列入 IN，**均与 B0 冻结原文冲突**，已撤回。依据：`STEP1B_SCHEMA_DEPENDENCY.md:193`（P00–P10 无 seed；P13 才有 seed）与 `STEP1B_TRIGGER_INVENTORY.md:163-166` / `STEP1B_SCHEMA_DEPENDENCY.md:235-237`（G/H/I/J 最早可挂 = P09 后）。
> **能力影响（如实告知）**：B1-4 交付后 `resources` 可用，但 `resource_permissions` 因 `acl_subject_types` 为空（FK 不可满足）而**不可写入** —— ACL 能力要到 P13 才真正可用。这是冻结顺序的既定结果，非缺陷。

**OUT（严禁）**
- 建任何业务/域/Tool/AI/Agent/Event/Audit 表 · 修改 0001–0006 · 修改 B1-1~B1-3 已冻结语义 · 新建 Socket/HTTP 接口实现 · 实现授权引擎 · 发明 permission 字典 · commit/tag · 生产迁移

---

## 2. 与既有冻结决策的一致性声明

| 冻结项 | B1-4 遵守方式 |
|---|---|
| P2-02（无 `group`） | `acl_subject_types` CK 保持 `IN ('user','role','agent')`，**不注册 group、不引用 groups 表**；未来路径仅记录 |
| P2-03（Resource FK） | `resources.tenant_id/space_id` **RESTRICT**；`resource_permissions.resource_id` CASCADE（受控 purge 白名单，逐项理由见 §SCHEMA_DESIGN） |
| P2-01（Role scope） | `resource_permissions.subject_type_id='role'` 时，跨租户语义由**授权层**按 `resources.tenant_id` vs `roles.tenant_id` 判定；DB 只做存在性校验（B0 ACL §3 冻结） |
| R2-D-14（DENY > ALLOW） | ACL 表只存 allow/deny 行；**不在 trigger 中做授权解释** |
| R2-D-15（scope-neutral） | `resource_permissions` 不冗余 tenant/space（随父 `resources`），`conditions` storage-only |
| D-05（系统角色不可变） | B1-4 不触碰 `roles` 语义 |
| R5（platform_state） | B1-4 不触碰 |

---

## 3. Scope 边界自检

- ✅ 无任何 `domains/*` 实现，无行业词汇
- ✅ 不新增 Socket/HTTP 实现
- ✅ 不修改 B1-3 语义、不修改已批准 migration
- ✅ 未把 P3-1…P3-5 隐式纳入（逐项 `KEEP DEFERRED`，见 `B1-4_PREP_GATE_REPORT.md` §5）
- ✅ **R1 已按冻结原文解决 2 项原 OPEN**：D-B14-01（B1-4 无 seed）· D-B14-02（B1-4 实施 0 个 ACL trigger）
- ✅ **R4（2026-09-13）全部 Human Decision 已 FROZEN，待裁定 = 0 项**：
  **D-B14-08 = FROZEN — A**（`action` 零新增 semantic/format contract；opaque identifier）·
  **D-B14-09 = FROZEN — A**（`granted_by ON DELETE SET NULL`）·
  **D-B14-10 = FROZEN — A-1**（`tg_resources_tenant_space_consistency`）·
  **D-B14-12 = FROZEN — A**（platform-controlled registry + `tg_acl_subject_types_protect`）→ 见 `B1-4_DECISION_LOG.md`
- ✅ **R4 计数口径**：`O-1 = FROZEN — A`（Canonical Total = **84**）· `O-2 = FROZEN`（`Current Status` + `Post-Approval Level`）
