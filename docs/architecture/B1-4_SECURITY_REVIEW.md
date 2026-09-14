# B1-4 — Security Review（PREP / DESIGN ONLY）

Status: **DESIGN — 只做安全设计，不实施**
适用对象：`resources` / `acl_subject_types` / `resource_permissions` 三表及其 trigger

---

## 1. 访问控制矩阵（谁可以创建 / 修改 / 删除 / 读取）

> 说明：**DB 层的"谁"由应用层授权决定**（DB 无 RLS，见 §7）。下表是**目标语义**，将作为后续 Authorization Layer 的实现契约。

| 对象 · 操作 | PLATFORM 管理员 | 租户管理员（tenant_admin） | 空间管理员（space_admin） | 普通成员 | 非成员 / 跨租户 | 备注 |
|---|---|---|---|---|---|---|
| `resources` 读取 | ✅ 全平台 | ✅ 本租户 | ✅ 本空间 | ✅ 本空间（按 ACL/permission） | ❌ **DENY** | 隔离由 `tenant_id`/`space_id` 承载 |
| `resources` 创建 | ✅ | ✅ 本租户 | ✅ 本空间 | ⚠️ 需 `resource.create` 能力（字典未定稿 → 默认为 DENY） | ❌ | `owner_id` 自动 = 创建者 |
| `resources` 修改（label/metadata/classification） | ✅ | ✅ 本租户 | ✅ 本空间 | ❌（默认） | ❌ | **classification 只升不降**（应用层，测试 R6） |
| `resources` archive / soft delete | ✅ | ✅ 本租户 | ⚠️ 需能力 | ❌ | ❌ | 走 `archive → soft delete → retention` |
| `resources` **purge**（硬删） | ✅ 仅受控流程 | ❌ | ❌ | ❌ | ❌ | 受控 purge + 备份 + 审计（运维级，非业务 API） |
| `acl_subject_types` 读取 | ✅ | ✅（只读） | ✅（只读） | ✅（只读） | ✅（只读，字典非敏感） | 注册表为平台级字典 |
| `acl_subject_types` 注册 / 归档 | ✅ **仅经 migration**（人工审计） | ❌ | ❌ | ❌ | ❌ | 运行时**无写路径**；治理模型见 **D-B14-12 = A（FROZEN 2026-09-13）**：platform-controlled registry + `tg_acl_subject_types_protect`（**registry governance only**）。受控写入路径见 `B1-4_DESIGN.md` §8.1 |
| `resource_permissions` 读取 | ✅ | ✅ 本租户资源 | ✅ 本空间资源 | ⚠️ 仅自身相关行（授权层过滤） | ❌ | 不属于"敏感密钥类"，但属**授权拓扑**，默认收敛 |
| `resource_permissions` grant / revoke | ✅ | ✅ 本租户资源 | ✅ 本空间资源 | ❌ **默认 DENY** | ❌ | grant 必须经授权层；**LLM 不可作为决策主体**（§6） |
| `resource_permissions` 跨租户授予 | ❌ | ❌ | ❌ | ❌ | ❌ | `subject` 与 `resource` 必须同租户（或平台 role） |

**默认 Deny 声明**：任何未在表中显式标 ✅ 的组合一律 **DENY**（fail-closed）。无 `role_id`/无 membership/无 ACL 命中 ⇒ DENY，**不得**回落为 allow。

---

## 2. Tenant / Space 隔离

| 机制 | 设计 |
|---|---|
| 物化列 | `resources.tenant_id`（**NN**）· `resources.space_id`（NULL 允许） |
| 父表保护 | 两者均为 **RESTRICT** → 有资源的 tenant/space 不可被删除（防静默批量丢失） |
| ACL 隔离 | `resource_permissions` **不冗余** tenant/space（避免漂移），隔离**随父 `resources`** 传递 |
| 查询路径 | 必须经 `resources` 过滤（`tenant_id` 必带；`space_id` 按上下文）→ 再评估 ACL |
| 跨租户 | 默认 **DENY**；`role` 主体仅当 `roles.tenant_id = resources.tenant_id`（或 PLATFORM role）时生效 —— **判定在授权层**，DB 只做存在性校验（B0 ACL §3 冻结） |
| 一致性缺口 | `resources.space_id` 所属 space 的 tenant **必须等于** `resources.tenant_id`（`space_id IS NULL` 时放行）—— **已冻结 D-B14-10 = A-1**：B1-4 引入 **`tg_resources_tenant_space_consistency`**（**P06 / B1-4** · **BEFORE INSERT OR UPDATE** · **structural integrity only**，不做 authorization evaluation）。相位与依赖见 `TRIGGER_INVENTORY` 条目 **F2** / `SCHEMA_DEPENDENCY` §7；机制与受控写入路径见 `B1-4_DESIGN.md` §8.1 |

---

## 3. Role / Permission 绑定

| 项 | 设计 |
|---|---|
| ACL 的 `role` 主体 | `roles.id` 存在性由 trigger 校验；**归档 role 的 deny 行不参与决策、allow 行保留用于审计追溯**（授权层判断 `archived_at`，**不改 ACL 数据**） |
| ACL 的 `user` 主体 | 存在性校验**不限制 `status`**（软删用户保留历史 ACL）；硬删由 `tg_acl_user_hard_delete` 清理 → 范围受 **D-B14-02** 约束 |
| ACL 的 `agent` 主体 | 依赖 `agents` 表（P09）→ **B1-4 不注册/不校验**（D-B14-01 / D-B14-02） |
| role 删除保护 | 被 ACL 引用时由 `tg_acl_role_delete_block` 拒绝（复刻 RESTRICT 语义，因 FK 指向类型表而非具体主体） |
| 与 RBAC 的关系 | ACL 是**附加**层：角色链给出能力，ACL 给出实例级 allow/deny；**DENY 优先**（R2-D-14 冻结） |
| 与 permission 字典 | B1-4 不写 `permissions` 行、不发明字典；`acl.action` 与 `permissions.key` 的**对齐规则未冻结 → D-B14-08** |

---

## 4. 高危动作处理

| 动作 | 风险等级 | 要求 |
|---|---|---|
| `grant/revoke` on `HIGHLY_CONFIDENTIAL` 资源 | **HIGH** | 授权层放行 + 审计（risk_level=HIGH） |
| `purge`（硬删资源/ACL） | **HIGH** | 受控流程 + 备份 + 审计；只能由运维通道执行 |
| `classification` 降级尝试 | **HIGH** | **拒绝**（只升不降；违规 → DENY + audit） |
| `acl_subject_types` 注册/归档 | **HIGH** | 仅 migration（人工审计），运行时无写路径 |
| 跨租户 grant | **HIGH** | 默认 DENY |
| `resources` 批量导出 | 中 | 需显式能力 + 审计 |

**审计（defer 说明）**：ACL 变更、purge、分类降级拒绝均要求写 `audit_logs`(actor/tenant/space/resource/action/effect/result/risk_level)。`audit_logs` 属 **P10**，当前不存在 → 与 B1-3 的 **P3-4 同类**，**B1-4 不实现审计写入**（D-B14-07），但**契约在此冻结**，实现阶段不得省略。

---

## 5. Secret / 明文禁令

- `resources.metadata jsonb` **严禁存放密钥/凭据/令牌**（如 `api_key`、`secret`、`token`）→ CI 扫描 + 代码审查
- `resource_permissions.conditions` **严禁存放密钥**（ABAC 条件只应含属性谓词）
- 不新增任何明文 secret 列；与既有 `credentials.secret_hash` / `ai_providers.secret_ref` 策略一致

---

## 6. LLM / AI 的权限边界（强制声明）

> **LLM 永远不能成为权限判断主体。**

- AI 只能**提议意图（Intent）**；授权判定由 **Application Authorization Layer** 基于 trusted context（认证主体、membership、role、ACL、classification）执行
- AI **不得**直接写 `resource_permissions`，**不得**参与 `conditions` 求值（本阶段无求值器；未来求值器也必须是与模型解耦的确定性代码）
- AI 输出**不得**作为 `granted_by` 的来源；`granted_by` 必须是**已认证的用户/系统主体**
- `HIGHLY_CONFIDENTIAL` 资源禁止因 AI 厂商故障降级到公共模型（数据架构铁律 5；DB CHECK 在 P08 落地）

---

## 7. RLS 状态

- **RLS = 不启用**（沿用 R5-D-04 / B0 Q1 OPEN）：B1-4 **不 enable RLS、不建 policy、不改 PG 安全配置**
- 隔离在本阶段依赖**应用层强制 + DB 约束（FK/UQ/CK/trigger）**；未来若启用 RLS，需重新评估连接池 `SET LOCAL` 与归还重置语义

---

## 8. 安全边界与已知缺口（暴露，不掩盖）

| # | 缺口 | 影响 | 处置（R1 更正） |
|---|---|---|---|
| S1 | ~~P06→P09 未验证 subject 窗口~~ | **不成立（R1 撤回）** | 冻结原文：P00–P10 无 seed（`SCHEMA_DEPENDENCY.md:193`）⇒ B1-4 期 `acl_subject_types` 为空 ⇒ FK 不可满足 ⇒ `resource_permissions` **不可写入** ⇒ 既无伪造主体也无未注册主体。**该风险已被冻结顺序天然关闭** |
| S1' | **ACL 能力空窗（能力缺口，非安全缺口）**：B1-4→P13 期间 `resource_permissions` 不可写入 | 资源可用但 ACL 暂不可用 | 冻结设计既定顺序；**不构成安全暴露**（无数据可越权访问 ACL 表）；如人工要求提前，须批准修订 G/H/I/J 相位 + seed 阶段（D-B14-02 备选 B） |
| S2 | `resources.space_id` 与 `tenant_id` 一致性无冻结约束 | 可能出现"资源属 tenant A 却挂 tenant B 的 space"→ 隔离绕过 | **已冻结 D-B14-10 = A-1**（`tg_resources_tenant_space_consistency`；仅做完整性，不做授权） |
| S3 | `granted_by` 语义与删除行为未冻结 | 语义误用（当作 owner）/ 悬空引用 | **已冻结 D-B14-09 = A**（语义 = actor attribution；删除 **`ON DELETE SET NULL`**） |
| S4 | `action` 无结构约束、词表未冻结 | 脏值；若擅自冻结词表则越界 | **已冻结 D-B14-08 = A**（**零新增 semantic/format contract**；**不加** CK；**禁止**定义语义；`ACT-03` 条件未成立） |
| S5 | ACL 变更审计依赖 `audit_logs`（P10） | 当前无法满足"审计同事务" | **KEEP DEFERRED**（D-B14-07）；结合 S1 结论，B1-4 期无 ACL 变更可审计 |
| S6 | 无 DB 层跨租户判定 | 跨租户授予只能靠授权层 | **已冻结**（ACL_STRATEGY §3）；授权层实现前 fail-closed |
| S7 | `acl_subject_types` 运行时写权限未冻结 | 若未来开放运行时注册 → 授权层不知如何验证 | **已冻结 D-B14-12 = A**（platform-controlled registry + `tg_acl_subject_types_protect`；**registry governance only**） |
