# B1-4 — Dependency Audit（PREP / DESIGN ONLY）

Status: **B1-4 PREP — 只读分析，不实施**
基线：已冻结并通过 live 验证的 `0001–0006` —— **14 business tables + `alembic_version` = 15 physical tables**；22 trigger / 12 function / 22 FK / 33 index（B1-4 后为 **17 business tables + `alembic_version` = 18 physical tables**）

---

## 1. 既有基线（B1-4 的输入）

| 域 | 表 | 来源 revision |
|---|---|---|
| Identity | `users` `identities` `credentials` `devices` `sessions` | 0003 |
| Tenant / Space | `tenants` `spaces` `tenant_memberships` `memberships` | 0004（0005 补 role FK） |
| RBAC | `roles` `permissions` `role_permissions` | 0005 |
| Platform | `platform_memberships` `platform_state` | 0005 / 0006 |

公共函数：`uap_uuid_v7()`（0002）· `set_updated_at()`（0003）· `enforce_membership_tenant_consistency()`（0004）· 9 个 B1-3 enforce_*（0005）· 2 个 bootstrap guard（0006）

---

## 2. B1-4 新增表的 FK 依赖图

```
                    users (0003)          tenants (0004)        spaces (0004)
                       ▲  ▲                   ▲                     ▲
        owner_id(SET NULL)│  │granted_by?      │tenant_id(RESTRICT)  │space_id NULL(RESTRICT)
                       │  │                   │                     │
                       │  └───────────┬───────┴──────────┬──────────┘
                       │              │                  │
                  ┌────┴──────────────┴──────────────────┴────┐
                  │              resources  (ROOT 之下第 3 层)  │
                  └────────────────────┬───────────────────────┘
                                       │ resource_id (CASCADE, 受控 purge)
                                       ▼
                       ┌──────────────────────────────────────┐
                       │        resource_permissions          │
                       └───────────────┬──────────────────────┘
                                       │ subject_type_id (RESTRICT)
                                       ▼
                       ┌──────────────────────────────────────┐
                       │        acl_subject_types  (ROOT)     │
                       └──────────────────────────────────────┘
```

### 2.1 逐表依赖

| 表 | 依赖（父表） | 依赖类型 | 是否 root |
|---|---|---|---|
| `resources` | `tenants`（NN, RESTRICT）· `spaces`（NULL, RESTRICT）· `users`（NULL, SET NULL） | 硬 FK | 否（第 3 层） |
| `acl_subject_types` | — | 无 FK | ✅ **ROOT** |
| `resource_permissions` | `resources`（NN, CASCADE）· `acl_subject_types`（NN, RESTRICT）· `users`（NULL, `granted_by`） | 硬 FK | 否（第 4 层） |

> **多态边说明**：`resource_permissions.subject_id` 是**受控多态**（无 FK），完整性由「`acl_subject_types` 注册 + `tg_acl_subject_exists` 校验」承担，**这是 P1/P2-04 的冻结结论**，不是弱引用回归。

---

## 3. Trigger 依赖

| trigger | 表 | 依赖对象 | B0 冻结「最早可挂」 | B1-4 是否实施 |
|---|---|---|---|---|
| `tg_resources_set_updated_at` | resources | `set_updated_at()`（0003） | 表建时（DEPENDENCY §7 行 229） | ✅ **实施**（无跨表依赖） |
| **`tg_resources_tenant_space_consistency`** | resources | `resources` + `spaces`（0004） | **P06 / B1-4**（DEPENDENCY §7 R1 增补行） | ✅ **实施**（D-B14-10 = A-1 FROZEN；无未来对象依赖） |
| **`tg_acl_subject_types_protect`** | acl_subject_types | 本表自身（无跨表依赖） | **P06 / B1-4**（DEPENDENCY §7 R4 增补行） | ✅ **实施**（D-B14-12 = A FROZEN；无未来对象依赖；**registry governance only，不做 authorization evaluation**） |
| `tg_acl_subject_exists` | resource_permissions | `resource_permissions` + `acl_subject_types` + `users` + `roles` + **`agents`** | **P09 后**（TRIGGER_INVENTORY:89/163；DEPENDENCY:235） | ❌ **不实施**（引用不存在的 `agents`） |
| `tg_acl_user_hard_delete` | users | `resource_permissions` + `acl_subject_types` | **P09 后**（TRIGGER_INVENTORY:101/164；DEPENDENCY:236） | ❌ **不实施** |
| `tg_acl_role_delete_block` | roles | `resource_permissions` + `acl_subject_types` | **P09 后**（TRIGGER_INVENTORY:112/165；DEPENDENCY:237） | ❌ **不实施** |
| `tg_agent_acl_expire` | agents | `resource_permissions`（+ `agents` 表） | **P09 后**（TRIGGER_INVENTORY:123/166） | ❌ **不实施** |

### 3.1 R1 原文级结论（上一轮结论已更正）

**Q：B0 的"G/H/I/J 排 P09 之后"意味着"全部必须等 P09"还是"仅 agents 相关需等 P09"？**

**答：A —— 全部必须等 P09 后。** 依据两处独立冻结原文：

| 出处 | 行 | 原文要点 |
|---|---|---|
| `STEP1B_TRIGGER_INVENTORY.md` §2 | 163–166 | `最早 phase` 列：G/H/I/J **全部 = `P09 后`** |
| `STEP1B_TRIGGER_INVENTORY.md` §3 | 177 | "G/H/I/J … **均在 P09 后建**" |
| `STEP1B_SCHEMA_DEPENDENCY.md` §7 | 235–237 | 三者**最早可挂** = "P09 之后 / P09 后" |
| `STEP1B_SCHEMA_DEPENDENCY.md` §7 | 241 | 该列语义 = trigger「**最早**可挂的 phase」 |

**原文不精确之处（如实报告，未自行修正）**：H/I 的 `dependency` 字段**不含 `agents`**，"P09 后"是**显式阶段冻结**而非依赖推导结果；`TRIGGER_INVENTORY:177` 以"依赖 agents"概括四项，对 H/I 理由不充分。**是否提前属冻结文档修订事项**（需人工批准），本 PREP 不自行裁定。

**Q：新增的 `tg_resources_tenant_space_consistency` 是否违反 B0 相位？**

**答：不违反，且已通过冻结文档修订消除覆盖缺口。** 该 trigger 属 **F2**（非 G/H/I/J），仅依赖 `resources`（P06 创建）+ `spaces`（P05/0004 已存在），**无未来对象依赖** ⇒ earliest phase = **P06 / B1-4**；已登记于 `TRIGGER_INVENTORY` 条目 F2、`SCHEMA_DEPENDENCY` §7 相位表、`CONSTRAINT_MATRIX` §3。**G/H/I/J 的「P09 后」未改动**。边界：**structural integrity only**，不做 authorization evaluation。

**Q：新增的 `tg_acl_subject_types_protect` 是否违反 B0 相位？**

**答：不违反，且已通过冻结文档修订消除覆盖缺口。** 该 trigger 属 **C2**（非 G/H/I/J），**仅依赖 `acl_subject_types` 自身**（P06 / B1-4 创建），**无未来对象依赖** ⇒ earliest phase = **P06 / B1-4**；已登记于 `TRIGGER_INVENTORY` 条目 C2、`SCHEMA_DEPENDENCY` §7 相位表、`CONSTRAINT_MATRIX` §3（**D-B14-12 = A，2026-09-13**）。**G/H/I/J 的「P09 后」未改动**。边界：**registry governance only**，**不承担 authorization evaluation**，**不演变为 Domain authorization**。

**Q：B1-4 期间 ACL 是否存在"未验证主体"风险？**

**答：不存在。** 因 B1-4 不 seed（`SCHEMA_DEPENDENCY.md:193`：P00–P10 无 seed；P13 才有 seed）⇒ `acl_subject_types` 在 B1-4→P13 期间为空 ⇒ `resource_permissions.subject_type_id` 的 FK **不可满足** ⇒ **ACL 行物理不可写入**。既无伪造主体，也无"授权层不知如何验证"的主体（另见 D-B14-12 治理结论）。

---

## 4. Event / Audit 依赖

| 需求（冻结文档中的出处） | 依赖对象 | 现状 | B1-4 处理 |
|---|---|---|---|
| ACL 变更同事务写 `audit_logs`（ACL_STRATEGY §6） | `audit_logs`（P10） | **不存在** | **defer**（D-B14-07） |
| role 归档时"由 trigger 写 audit"（CORE §1.3） | `audit_logs` | 不存在，且与 trigger 本体论（trigger 不写 audit）冲突 | 记录为 **P3 文档不一致**，defer |
| membership removed 记 `audit_logs(reason=...)` | `audit_logs` | 不存在 | defer（属授权层） |
| `events` outbox | — | 不存在 | B1-4 不产生事件（无 outbox 写入需求） |

**结论**：B1-4 不依赖 `events` / `audit_logs` 的**结构性存在**；审计写入属后续阶段（与 B1-3 的 P3-4 同类，延续 defer）。

---

## 5. 授权依赖（Authorization）

```
B1-4 提供（数据层）                    B1-4 不提供（后续 Authorization Layer）
─────────────────────────            ──────────────────────────────────────────
resources（对象 + 归属 + 分类）        请求上下文 / ABAC 求值 / DENY>ALLOW 解释
acl_subject_types（主体类型注册）      跨租户语义判定（resource.tenant_id vs role.tenant_id）
resource_permissions（ACL 行）        membership 实时校验（removed → DENY）
expires_at / inherited（数据位）      时间与继承的有效性评估
```

**冻结约束**：DB 层只做**完整性**（存在性、scope shape、级联清理），授权**决策**永远在应用层；`LLM 永远不能成为权限判断主体`（见 SECURITY_REVIEW §6）。

---

## 6. Agent / Tool / AI Gateway 依赖

| 后续域 | 对 B1-4 的依赖 | 方向 |
|---|---|---|
| P07 Tool | 无直接 FK；Tool 归属/授权未来可挂 `resources` | 下游 |
| P08 AI Gateway | 无直接 FK；`ai_*` 为独立 root 域 | 无 |
| P09 Agent | `agent_permissions` 需要 `tools`；`agents.current_version_id → agent_versions`（唯一循环，deferred FK）；**ACL 的 agent 分支需要 `agents` 存在** | **下游（B1-4 为其前置）** |

**结论**：B1-4 **不出现**对 Agent/Tool/AI 的任何 FK 或 trigger 引用（`agents` 相关一律 defer）。

---

## 7. Future Domain 依赖

- 域扩展表以 **1:1 共享主键**（`id` 同时 PK + FK → `resources.id` CASCADE）方式接入，由 **Domain 模块**负责，**永不进入 Core migration**。
- 方向性铁律：`domains/* → core/*` 允许；`core/* → domains/*` **禁止**（AST guard 强制）。
- B1-4 只交付 **registry 侧**；域侧接入机制属 Domain 层设计（登记 D-B14-03，仅记录）。

---

## 8. 循环 FK 检查

| 检查 | 结果 |
|---|---|
| `resources ↔ resource_permissions` | 单向（rp → resources），无环 |
| `resources ↔ tenants/spaces/users` | 单向，无环 |
| `acl_subject_types ↔ resource_permissions` | 单向（rp → acl_subject_types），无环 |
| 与既有表组合是否形成新环 | **否**（三表均为"末端出边"结构，无被既有表回指） |
| `agents ↔ agent_versions` 既有循环 | 不受 B1-4 影响（B1-4 不触碰） |

**结论：B1-4 无循环 FK，无前向依赖（forward dependency）；唯一需要裁定的是 trigger 的 phase 归属（D-B14-02）。**

---

## 9. Core → Domain 违例检查

| 检查项 | 结果 |
|---|---|
| B1-4 引入任何 `domains/*` 表？ | 否 |
| B1-4 migration 中出现行业词汇（family/company/restaurant/…）？ | 否（`resource_type`/`classification` 为开放格式字段，**不枚举业务值**） |
| `resources.resource_type` 是否业务枚举？ | 否 —— 仅格式 CK `^[a-z][a-z0-9_.]{1,63}$`，具体值运行时数据 |

**`Core → Domain` 违例 = 0（设计层）**；实施后须由 `tests/architecture` + Scope Scan 复核。
