# B1-4 — Design（PREP / DESIGN ONLY）

Status: **DESIGN — 不含任何实施**
关联：`B1-4_SCOPE.md`（范围）· `B1-4_SCHEMA_DESIGN.md`（字段级）· `B1-4_SECURITY_REVIEW.md`（安全）· `B1-4_DECISION_LOG.md`（决策冻结记录）

---

## 1. 设计定位

B1-4 在既有 RBAC 之上补齐**对象侧与实例侧授权数据**，形成如下完整链条的**数据层**：

```
Identity → Membership → Role → Role Scope → Permission        （B1-1~B1-3：谁能做什么）
                                   +
Resource(对象) → resource_permissions(实例级 allow/deny)        （B1-4：对哪个对象）
                                   +
Request Context / Classification / expires_at / membership 实时校验  （后续 Authorization Layer）
                                   =
最终授权结果（DENY 优先 · 默认拒绝 · fail-closed）
```

**分层职责（不可混淆）**

| 层 | 职责 | 本阶段是否交付 |
|---|---|---|
| **DB 完整性** | FK / UQ / CK / 级联清理 —— **B1-4 交付**；`updated_at` trigger 交付；**ACL 主体存在性校验（`tg_acl_subject_exists`）属 P09 后，不交付**（D-B14-02：冻结「最早可挂 = P09 后」） | ✅ 部分交付（见左） |
| **Application Service** | grant/revoke 的幂等语义、审计、受控 purge 编排 | ❌ 后续阶段（契约在本文件 §5 冻结） |
| **Authorization Layer** | DENY>ALLOW 解释、跨租户语义、membership 实时校验、classification 门控 | ❌ 后续阶段（契约 §4 冻结） |

---

## 2. 资源模型设计

### 2.1 注册表 + 1:1 域扩展（非多态弱引用）

```
resources (Core: 身份/归属/分类/状态)
   │ id (PK)
   └──1:1──> <domain_extension>.id (PK & FK → resources.id ON DELETE CASCADE)   ← Domain 层，本阶段不建
```

- **共享主键**使域表天然具备强 RI，**禁止**无外键的多态弱引用
- Core **不出现任何行业词汇**；`resource_type` 与 `label` 为开放运行时数据
- `metadata jsonb` 仅承载非业务关键扩展；**严禁密钥**（CI 扫描 + 安全审查 §5）

### 2.2 生命周期

```
active ──archive──> archived ──soft delete──> deleted(deleted_at 置位)
                                                    │ retention（默认 30d，可配置）
                                                    ▼
                                        controlled purge（先子后父，分批）
```
- 父实体（tenant/space）删除**被 RESTRICT 拒绝**；purge 必须先清资源（连 ACL 与域扩展表），再清父行

### 2.3 classification 语义（与既有冻结项联动）

| 值 | 授权/审计含义（冻结联动） | B1-4 提供的机制 |
|---|---|---|
| `PUBLIC` | 无额外门控 | 数据列 |
| `INTERNAL` | 默认档 | 数据列（默认值） |
| `CONFIDENTIAL` | 授权需显式 allow | 数据列 |
| `HIGHLY_CONFIDENTIAL` | **禁止因 AI 厂商故障降级到公共模型**（数据架构铁律 5）；ACL 变更 risk=HIGH | 数据列（DB 层 CHECK 保证取值域；降级禁令由 `ai_policies` 的 DB CHECK 在 P08 落地） |

**只升不降**：由应用层保证（测试项 R6 冻结）—— 本阶段不加 DB 约束（避免越权收紧）。

---

## 3. ACL 模型设计

### 3.1 主体类型注册（受控多态）

```
acl_subject_types(user | role | agent)   ← 唯一可接受的注册集合（CK 白名单；无 group）
        ▲ subject_type_id (FK RESTRICT)
resource_permissions(subject_id 受控多态)
        │
        └── trigger: subject_id 必须真实存在于类型对应表（user→users / role→roles / agent→agents）
```

- **拒绝裸字符串**：`subject_type`（text）被 `subject_type_id`（FK）取代（P1/P2-04 冻结）
- **无伪造 subject**：存在性由 trigger 校验（**agent 分支依赖 `agents` 表 → D-B14-02**）
- **跨租户语义不在 DB 判定**：`action` 语义 + `resource.tenant_id` vs `role.tenant_id` 由授权层评估（B0 ACL §3 冻结）

### 3.2 ACL 行语义

| 概念 | 表达 |
|---|---|
| 允许 | `effect='allow'` |
| 拒绝 | `effect='deny'` |
| 条件（未来 ABAC） | `conditions jsonb` —— **storage-only**，本阶段无求值器 |
| 期限 | `expires_at`（到期即失效，由授权层判断；不在 DB 删除行） |
| 继承/失效标记 | `inherited`（agent 归档时置 true 使其自然到期） |
| 授予者 | `granted_by`（**actor attribution**，非 ownership）→ `users.id` **`ON DELETE SET NULL`**（**D-B14-09 = A FROZEN 2026-09-13**）；与 `resources.owner_id` 的 ownership SET NULL **语义正交、相互独立** |

### 3.3 冲突与优先级（授权层契约，**DB 不实现**）

```
同一 (resource, subject, action) 只能一行（UQ）→ 单行内 effect 唯一 → 无行内冲突
跨主体/跨来源冲突（如 user 直接 allow 但所属 role 被 deny）：
   DENY 绝对优先（R2-D-14 FROZEN SECURITY INVARIANT）
   无匹配规则 → DENY（默认拒绝）
```
- **不允许**在 trigger 中做授权解释（R2-D-14 明确）
- 行内 `effect` 变更 = `UPDATE`（不是新增行）→ 保留"同一授权关系"的历史语义

---

## 4. 授权评估链（B1-4 输出的数据，后续层消费）

```
[1] 请求上下文（actor, action, resource_id, tenant/space 上下文）   ← 后续层
[2] 解析资源：resources.tenant_id / space_id / classification / status
[3] 主体资格：membership active? → 否则 DENY（membership_removed 场景）
[4] 角色链：role active? scope 匹配? permission 命中?   （B1-3 数据）
[5] 实例 ACL：resource_permissions 命中 (resource, subject, action)?
        ├── 命中 deny  → DENY（优先）
        ├── 命中 allow → 进入 [6]（仍需满足 conditions/expires/membership）
        └── 无命中     → 回落角色链结果；角色链也无 → DENY
[6] 附加门控：expires_at 未过期 ∧ conditions 满足（本阶段无求值器）∧ classification 规则
```

**B1-4 只提供 [2]/[5] 的数据与完整性；[1][3][4][6] 属后续层。**

---

## 5. Application Service 契约（本阶段冻结、后续实现）

| 操作 | 契约 |
|---|---|
| `grant(resource, subject, action, effect, conditions?, expires_at?)` | 单事务：① 校验调用者具备该资源的授权权限（授权层）② UPSERT 到 `resource_permissions`（UQ 冲突 → UPDATE effect）③ 写 `audit_logs`（**defer**，P10）<br>**前置**：`acl_subject_types` 必须已注册对应类型（**最早 P13**）—— 在此之前该操作在 DB 层**不可执行**（FK 不可满足） |
| `revoke(resource, subject, action)` | `DELETE` 该行（或 `expires_at=now()`） + 审计 |
| `archive_resource(id)` | `resources.status='archived', archived_at=now()`（ACL 保留） |
| `soft_delete_resource(id)` | `deleted_at=now(), status='deleted'`（ACL 保留） |
| `purge_resources(tenant, space)` | 分批：域扩展表 → ACL（FK CASCADE）→ resources 行；**先子后父**，不触碰 tenant/space 行本身 |
| 幂等 | 上述操作必须可重复执行而不产生额外副作用（依赖 UQ + 幂等 UPDATE） |
| 失败 | 任一步失败 → 整体回滚（无半状态） |

---

## 6. 与既有冻结设计的关系

| 冻结项 | B1-4 的处理（R1） |
|---|---|
| `acl_subject_types` 白名单 `IN ('user','role','agent')` | CK **原样保留**；**B1-4 不 seed 任何行**（三行属 P13，D-B14-01 RESOLVED）⇒ 期间表为空、ACL 不可写 |
| ACL trigger 统一 P09 后 | **完全遵守**：B1-4 实施 **0 个** ACL trigger（D-B14-02 RESOLVED）；提前需人工批准并修订冻结文档 |
| `resource_relations` 不建 | 遵守（defer） |
| RLS 不启用 | 遵守（沿用 R5-D-04 OPEN） |
| permission 字典不发明 | 遵守（B1-4 不写 `permissions`；词表属 Permission Dictionary 阶段，D-B14-08） |
| `group` 不注册、不引用 | 遵守（仅记录未来路径） |
| DENY>ALLOW / scope-neutral / conditions storage-only | 遵守（DB 不做授权解释） |

---

## 8. `acl_subject_types` 治理模型（R1 新增设计结论）

**定性**：**平台受控 Subject Type Registry** —— 不是自由业务注册表。

| 操作 | 允许者 | 机制 | 依据 |
|---|---|---|---|
| **INSERT**（注册新类型） | **仅经 migration**（伴随 trigger 校验分支 + 测试） | 运行时**无写入口**；CK 白名单 `('user','role','agent')` 已阻断其它 key 的运行时插入 | `CORE:244`（"受控的注册机制"）· `CORE:249`（注册与 trigger 扩展成对）· `ACL_STRATEGY:124-126`（group 路径为 migration 驱动） |
| **UPDATE** | 仅 `description`；`key` **不可变** | 防止改写 key 绕过白名单语义 | 同上 |
| **DELETE** | **禁止物理删除**；退役走 `archived_at`（部分唯一索引随之释放，可重建同名） | `CORE:249` "删除：先归档 + 清理该 type 的所有 `resource_permissions`" | 同上 |
| **Domain / Plugin 自行注册** | **不允许** | 无路径；本阶段**不定义** Plugin 注册 API（越界） | 用户第八条要求 + B1-4 scope |
| **未实现主体类型能否产生有效 ACL** | **不能** | 注册表为空 ⇒ `subject_type_id` FK 不可满足 ⇒ `resource_permissions` 不可写入 | D-B14-01/02 结论的直接推论 |

**保护机制（D-B14-12 = A，FROZEN 2026-09-13）**：`tg_acl_subject_types_protect`（**BEFORE INSERT OR UPDATE OR DELETE**）—— 拒绝运行时 INSERT、`key` 不可变、DELETE 拒绝（退役走 `archived_at`）。该 trigger **仅依赖 `acl_subject_types` 自身**，**不违反** G/H/I/J 的 P09 相位约束，**P06 / B1-4** 建立（`TRIGGER_INVENTORY` 条目 **C2**）。
**whitelist 保持不变**：`key IN ('user','role','agent')`（**不含 `group`**，**不得修改 whitelist，不得提前 seed**）。

**职责边界（强制）**：该治理只保证**注册表自身**的结构完整性（**registry governance only**）；**授权判定仍全部由 Authorization Layer 执行**（DB 不做授权）。该 trigger **不得**承担 resource authorization / ACL decision / role resolution / deny resolution / business authorization。

### 8.1 受控写入路径（**W-3 决议**，2026-09-13）

**策略（已由 D-B14-12 = A 冻结）**：
> **Initial registry population is migration-controlled and is part of schema governance, not Domain runtime registration.**
> 即：`acl_subject_types` 的合法行只能由 **migration** 建立（`user`/`role`/`agent` 三行属 **P13** seed），**不提供任何运行时注册入口**。

**既有先例（仓库内已成文的事实，非新裁定）**：

| migration | 先例 | 顺序 |
|---|---|---|
| `0005_b1_3_authorization.py` | 内置 4 个 role 行（L269/L279/L289） | **先 INSERT → 后 `CREATE TRIGGER tg_roles_is_system_protect`（L410）** |
| `0006_b1_3_bootstrap_state.py` | `platform_state` bootstrap 行（L115） | **先 INSERT → 后 `CREATE TRIGGER tg_platform_state_guard`（L130）** |

**机制 = 实施细节（不新增 Human Decision；以下为候选，实施计划阶段定稿）**：

| # | 机制 | 说明 |
|---|---|---|
| **M-1** | P13 其自身 migration 内 `ALTER TABLE … DISABLE TRIGGER` → INSERT → `ENABLE TRIGGER` | 迁移以 **table owner** 执行；同事务；与 0005/0006"受控写入"精神一致 |
| M-2 | trigger 函数检测受控会话标记（如 `current_setting('uap.registry_governance', true)`） | 需 P13 显式设置；**不引入任何运行时 API** |
| M-3 | 由 P13 migration 在同一 revision 内先 `DROP TRIGGER` → INSERT → 重建 | 与 M-1 等效，但破坏性更强 |

> **推荐 M-1**（最小、可审计、复用 owner 权限，不新增运行时开关）。
> **不属于 Human Decision**：三者均只解决"迁移如何合法写入"，**不改变** registry 治理语义、whitelist、或与 Authorization Layer 的边界。
> **明确禁止**（§7 边界）：runtime / plugin / domain registration API · application-level bypass · 新增 `group` · 新增 permission/action vocabulary · 新增 authorization mechanism。

**REG-02 / REG-03 夹具路径**：同属上表（`acl_subject_types` 受保护 ⇒ 夹具行须经受控路径构造），**夹具构造方式在实施阶段随 M-1…M-3 一并确定**（`B1-4_TEST_MATRIX.md` §8.4 保持一致）。

---

## 7. 未来扩展路径（仅记录，本次不实施）

| 扩展 | 路径 |
|---|---|
| `group` 主体 | `CREATE groups` → 注册 `group` → CK 白名单加值 → trigger 增分支 → 测试 |
| `agent` 主体 | P09 `agents` 建表 → 注册/保持 `agent` → `tg_acl_subject_exists` 增 agent 分支 → `tg_agent_acl_expire` |
| 资源层级 | `resource_relations`（parent/child）+ 递归评估（需权限继承需求驱动） |
| ABAC | `conditions` 求值器（独立阶段；本阶段仅存储） |
| RLS | 会话变量 + policy（Q1 未决） |
