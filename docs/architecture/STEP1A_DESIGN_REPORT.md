# STEP 1-A DESIGN REPORT — UAP Core Domain Model & Data Architecture

Status: **DESIGN REVISION (Round 3) — 等待第三次人工审计批准**
Created: 2026-09-07 · Phase: `STEP 1-A / DESIGN ONLY`
基线：`72ade9f` · `UAP-V0.1.0-INIT-DB-VALIDATED`

> **本阶段未创建任何表、未写 migration、未改 Core 架构。**
> 配套文档：
> - [CORE_DOMAIN_MODEL.md](./CORE_DOMAIN_MODEL.md) — Entity Catalog 与全部模型细节
> - [ER_MODEL.md](./ER_MODEL.md) — ER 图与关系矩阵
> - [MIGRATION_STRATEGY.md](./MIGRATION_STRATEGY.md) — Alembic 选型与迁移策略
> - [STEP1A_ARCHITECTURE_REVIEW.md](./STEP1A_ARCHITECTURE_REVIEW.md) — **Round 2 修订记录（4 个 P1/P2 问题的逐项追溯）**

---

## 0. Round 2 & 3 修订摘要

第一轮审计发现 3 个 P1 + 1 个 P1/P2 级问题（Round 2），第二轮一致性审计又发现 3 个 P2 级问题（Round 3），已全部修正：

| ID | 问题 | 修正位置 | 状态 |
|---|---|---|---|
| **P1-01** | Tenant Role 无实际分配关系 | `tenant_memberships.role_id`（方案 A） | ✅ R2 |
| **P1-02** | UUIDv7 DB fallback 需重核 bit layout | 探针库实测通过，15+10 项断言全过 | ✅ R2 |
| **P1-03** | Event SKIP LOCKED ≠ exactly-once | 改 `at-least-once` + CAS claim + lease reaper | ✅ R2 |
| **P1/P2-04** | Resource ACL subject 是裸多态弱引用 | 新增 `acl_subject_types` 注册表 + trigger 验证 | ✅ R2 |
| **P2-01** | Tenant Role 默认角色 scope 冲突（`member`） | 默认角色统一 **`tenant_member`**（TENANT scope）；内置角色按 scope 归位 | ✅ R3 |
| **P2-02** | ACL `group` 引用不存在的 `groups` 表 | STEP 1-B 白名单收紧 `user`/`role`/`agent` | ✅ R3 |
| **P2-03** | `resources.tenant_id/space_id` CASCADE 与删除原则冲突 | 改 `RESTRICT`；CASCADE 收敛为受控白名单 | ✅ R3 |

**关键不变量重述**：
- **Tenant Role** = `tenant_memberships.role_id` 指向 `roles`（scope='TENANT'），默认 **`tenant_member`**；撤销 = `status='removed'` 立刻不参与计算
- **UUIDv7** = 时间戳 48bit + version 4bit + 随机 12bit + variant 2bit + 随机 62bit；应用 + DB 双轨实现，probed PASS
- **Event** = `at-least-once`；消费方按 `event_id` 幂等；不再承诺 exactly-once
- **ACL subject** = 必须先在 `acl_subject_types` 注册，否则 trigger 拒绝；不存在弱多态
- **资源删除** = Tenant/Space archive → soft delete → retention → controlled purge；**不依赖 FK CASCADE**

> Round 3 逐项记录与测试设计见 [STEP1A_ARCHITECTURE_REVIEW.md](./STEP1A_ARCHITECTURE_REVIEW.md) Round 3 章节。

---

## 1. Entity Catalog

共 **29 张核心表 + 1 张可选表**，全部字段/约束见 [CORE_DOMAIN_MODEL.md §1](./CORE_DOMAIN_MODEL.md#1-entity-catalog)。

| # | 表 | Purpose | PK | 关键 UQ / CK | 生命周期 |
|---|---|---|---|---|---|
| 1 | `users` | 全局登录主体（跨租户） | `id` | `lower(email)` 部分唯一；status CK | pending→active→suspended→deleted(soft) |
| 2 | `identities` | 用户在某身份源下的表示 | `id` | `(provider, issuer, subject)` 唯一 | active/unverified→revoked |
| 3 | `credentials` | 凭据哈希（永不存明文） | `id` | `(identity_id) WHERE type='password' AND revoked_at IS NULL` 唯一 | rotation：新增 + 旧行 revoke，过期 hard delete |
| 4 | `devices` | 注册设备（多设备） | `id` | `(user_id, fingerprint)` 唯一 | pending→active→revoked（不可逆） |
| 5 | `sessions` | 会话（多开、可单独失效） | `id` | `token_hash` 唯一 | active→expired/revoked→hard delete |
| 6 | `tenants` | 治理与隔离边界 | `id` | `lower(slug)` 唯一 | provisioning→active→archived→deleted→purge |
| 7 | `spaces` | 租户内协作上下文 | `id` | `(tenant_id, lower(key))` 部分唯一 | active→archived→deleted→purge |
| 8 | `tenant_memberships` | 用户 ↔ 租户 + **Tenant Role 分配**（P1-01 方案 A） | `id` | `(tenant_id, user_id)` 唯一；`role_id` 指向 `scope='TENANT'` 的 role | invited→active→suspended→removed；removed 后 Tenant Role 立即失效 |
| 8.5 | `acl_subject_types` | **ACL subject 类型注册表**（P1/P2-04） | `id` | `lower(key)` 部分唯一 | active→archived；新 type 必须先注册 |
| 9 | `memberships` | 用户 ↔ 空间 + 角色 | `id` | `(space_id, user_id) WHERE removed_at IS NULL` 唯一 | 同上 |
| 10 | `roles` | 平台/租户/空间三级角色 | `id` | 三条**部分唯一索引**按作用域互斥 | active→archived；`is_system` 不可改 |
| 11 | `permissions` | 平台级权限字典 | `id` | `key` 唯一 | 系统内置 |
| 12 | `role_permissions` | 角色↔权限（含 deny + ABAC 条件） | `(role_id, permission_id, effect)` | — | 随角色 |
| 13 | `resources` | **通用**资源注册表 | `id` | `(tenant_id, resource_type, natural_key)` 部分唯一 | active→archived→deleted(soft) |
| 14 | `resource_permissions` | 资源级 ACL | `id` | `(resource_id, subject_type, subject_id, action)` 唯一 | 到期/随资源删除 |
| 15 | `resource_relations` ⚠️可选 | 资源层级与权限继承 | `id` | `(parent_id, child_id, relation_type)` | **建议 STEP 1-B 暂不建**（见 Q3） |
| 16 | `agents` | 执行实体（≠ 模型） | `id` | `(tenant_id, lower(key))` 部分唯一 | draft→active→disabled→archived |
| 17 | `agent_versions` | Agent 不可变快照 | `id` | `(agent_id, version)` 唯一 | published 后**不可变** |
| 18 | `agent_permissions` | Agent 白名单（权限/工具/范围） | `id` | 复合唯一（含 NULL 归一） | 随 agent |
| 19 | `tools` | Agent 触达业务唯一通道 | `id` | 平台级/租户级两条部分唯一 | enabled/disabled；不硬删 |
| 20 | `tool_versions` | Tool 契约快照 | `id` | `(tool_id, version)` 唯一 | published 后**不可变** |
| 21 | `tool_permissions` | 调用 Tool 所需权限 | `id` | 复合唯一 | 随 tool |
| 22 | `tool_executions` | 执行记录 + **幂等锚点** | `id` | `(tool_id, idempotency_key)` 部分唯一 | 分区，90 天 hard delete |
| 23 | `ai_providers` | 厂商连接（**数据行，非代码分支**） | `id` | `key` 唯一 | enabled/disabled + health |
| 24 | `ai_models` | 模型能力/成本/合规上限 | `id` | `(provider_id, model_key)` 唯一 | enabled/disabled |
| 25 | `ai_routes` | capability → 主模型 + fallback 链 | `id` | `(tenant, space, capability, priority)` 唯一 | enabled/disabled |
| 26 | `ai_policies` | 分级/准入/预算/降级约束 | `id` | 复合唯一 + `CK allow_fallback ⇒ fallback_preserves_classification` | enabled/disabled |
| 27 | `ai_request_logs` | 成本/配额/可观测 | `(id, occurred_at)` | — | 分区，90 天 |
| 28 | `events` | 领域事实 + **transactional outbox** | `(id, occurred_at)` | `event_type` 格式 CK | pending→delivered/dead，30 天清理 |
| 29 | `audit_logs` | 合规审计（**不可变**） | `(id, occurred_at)` | — | 分区 drop，默认 365 天 |

**通用列**：`id uuid (UUIDv7)`、`created_at timestamptz`、`updated_at timestamptz`（trigger 维护）。
`audit_logs` / `events` / `ai_request_logs` 无 `updated_at`。

---

## 2. ER Diagram

完整图见 [ER_MODEL.md](./ER_MODEL.md)，六组：

| 组 | 内容 | 核心基数 |
|---|---|---|
| 1 | User / Identity / Device / Session / Credential | `users` 1:N 其余；`devices` 1:N `sessions` |
| 2 | Tenant / Space / Membership / Role / Permission | `tenants` 1:N `spaces`；`users` N:M `spaces`（经 `memberships`）；`roles` N:M `permissions` |
| 3 | Resource / ResourcePermission | `resources` 1:1 域扩展表（共享 PK）；1:N ACL |
| 4 | Agent / AgentVersion / Tool / ToolVersion | `agents` 1:N versions/permissions；`tools` 1:N versions/executions |
| 5 | AI Provider / Model / Route / Policy | `providers` 1:N `models`；`models` 1:N `routes` |
| 6 | Event / Audit | 独立分区表，`events` 可由业务事务写入 |

FK 删除策略原则：**业务删除一律 `RESTRICT`**，仅生命周期严格从属的子实体（sessions/credentials/versions）用 `CASCADE`。

---

## 3. Identity Model

**核心决策：User ≠ Identity ≠ Credential ≠ Device ≠ Session。**

| 概念 | 回答的问题 | 为什么不能合并 |
|---|---|---|
| `users` | 这是谁 | 跨租户唯一主体；若把登录方式塞进来，OIDC/密码/设备会打成一锅 |
| `identities` | 用哪种方式证明 | 一人可有多种登录方式；撤销其一不影响其它 |
| `credentials` | 用什么秘密证明 | 需要 rotation 历史、算法升级、失败锁定，生命周期与 identity 不同 |
| `devices` | 用什么设备 | 多设备；设备撤销要级联会话 |
| `sessions` | 这次登录 | 多会话、独立过期与撤销 |

**多设备 / 多会话**：`devices (user_id, fingerprint)` 唯一；同一 user+device 允许多个 active session。

**撤销**：
- 设备撤销 → 同事务撤销其全部 active session（应用层显式实现，**不用跨表 trigger**，保持逻辑可见与可测）
- Session 失效：相对过期 `expires_at` + 绝对过期 `absolute_expires_at`（防无限续期）
- Credential rotation：新行 + 旧行 `revoked_at`，`rotated_at` 串联；已撤销凭据由 retention 硬删除

---

## 4. Tenant / Space Model

### 4.1 八个必答问题

| # | 问题 | 结论 |
|---|---|---|
| 1 | Tenant 与 Space 的区别 | **Tenant 是"墙"（治理/隔离/账单），Space 是"房间"（协作/上下文）** |
| 2 | 一个 User 能否属于多个 Tenant | **能**。`users` 全局，归属由 `tenant_memberships` 表达 |
| 3 | 一个 User 能否属于多个 Space | **能**。`memberships` 以 `(space_id, user_id)` 唯一 |
| 4 | Membership 属于谁 | **两层都有**：`tenant_memberships`（能否进租户 + **Tenant Role 分配**），`memberships`（空间内角色）。后者冗余 `tenant_id` 供隔离与 RLS，trigger 保证一致 |
| 5 | Role 作用域 | **PLATFORM / TENANT / SPACE 三级都支持**，用部分唯一索引互斥；**Tenant Role 通过 `tenant_memberships.role_id` 直接表达（P1-01 方案 A）** |
| 6 | Permission 继承 | **只向下**：租户权限在其所有 Space 生效，Space 不上溯；**deny 绝对优先**于任何 allow |
| 7 | Space 删除/归档 | **archive（可恢复）→ soft delete（30 天）→ purge（分批 ≤1000）**；FK 一律 RESTRICT |
| 8 | Tenant Isolation | **四层**：模式层 `tenant_id` + 复合索引 / 应用层强制断言 / RLS（可选，Q1）/ 越权写入审计 |

### 4.2 Tenant Role 分配与失效（**P1-01 修正**）

- **分配**：`tenant_memberships.role_id NOT NULL`（默认 **`tenant_member`** —— TENANT scope 内置角色；**不是** PLATFORM scope 的 `member`，P2-01），写入时 trigger 校验 `roles.scope='TENANT' AND roles.tenant_id = tenant_memberships.tenant_id`
- **修改**：变更角色 = `UPDATE tenant_memberships SET role_id=$new, role_assigned_at=now(), role_assigned_by=$actor WHERE id=$id` + 写 `audit_logs(action='tenant.role.assign')`
- **撤销**：`status='removed'` 立即不参与任何权限计算（授权实时查询）
- **继承到 Space**：授权 Pipeline [4] 阶段 Role Resolution 自动把 Tenant Role 视为在该租户所有 Space 生效（无需在 memberships 复制）
- **多个 Role 计算**：effective = P(platform) ∪ P(tenant_role) ∪ P(space_role) ∪ P(resource_acl) ；deny 压过一切
- **Membership 移除影响**：removed 后 **Tenant Role 立即失效**（在 [4] 阶段就拿不到 role_id），无需级联清理 audit / resource ACL（membership 重加入时自动恢复）

---

## 5. Authorization Model（RBAC + ABAC）— **P1-01 / P1/P2-04 修正**

```
[1] Authentication          → 谁？（session/token → user + identity + device）
      │
[2] Tenant Resolution       → 哪个租户？(tenant_memberships.status='active')
      │  fail                 → DENY (reason='not_tenant_member')
      ▼
[3] Space Resolution        → 哪个空间？(memberships.status='active')
      │  fail                 → DENY (reason='not_space_member')
      ▼
[4] Role Resolution         → 收集有效 roles:
      │                          - PLATFORM role（始终生效）
      │                          - TENANT role（取 tenant_memberships.role_id）
      │                          - SPACE role（取 memberships.role_id）
      │  fail (无 role)         → DENY (reason='no_role')
      ▼
[5] Permission Resolution   → roles JOIN role_permissions → allow ∪ deny
      ▼
[6] Deny Resolution         → 任一 deny 命中 action → DENY（**包括 Resource ACL 的 allow**）
      ▼
[7] ABAC Condition          → 求值 role_permissions.conditions（subject/resource/action/context/env）
      │  condition 不成立       → 该行视为不存在
      │  求值异常               → DENY (reason='abac_eval_error', fail-closed)
      ▼
[8] Resource ACL            → 显式 ACL 叠加 (resource_permissions)：
      │                          - subject_type_id ∈ acl_subject_types (注册表)
      │                          - subject_id trigger 验证存在
      │                          - membership_removed 不预先清理，由本阶段实时校验
      ▼
[9] Final Decision          → 任一 deny → DENY；无 allow → DENY (default-deny)
                            → 错误即 DENY (fail-closed)
```

**五条铁律**：Default Deny · Deny 优先（**步骤 [6] 压过步骤 [8] 的 allow**）· 错误即拒绝 · 全链路审计（高风险全量，LOW 可采样）· **Subject 必须存在于注册表 + 对应实体表**（P1/P2-04）。

**ABAC 维度**：subject（user/role/tenant）· resource（type/owner/classification/space）· action（risk/write/bulk）· context（time/ip/device_trust/mfa_age/session_age）· environment（tenant/space status）。

条件以 `jsonb` 存储，**求值在 Core（`core/policy`）完成，不在 SQL 里做条件求值**。

---

## 6. Resource Model

**结论：采用「注册表 + 共享主键」而非无外键多态（资源维度）。**

| 方案 | 引用完整性 | 判定 |
|---|---|---|
| A 单表存全部业务字段 | 强但业务塞 jsonb | ❌ |
| B 弱引用 `(resource_type, resource_id)` 无 FK | **无** | ❌ 悬空、无法级联 |
| **C 注册表 + 域表共享 PK** | **强** | ✅ |

```
resources(id PK, tenant_id, space_id, resource_type, owner_id, classification, status, ...)
     ▲ 1:1
domain_<x>(id PK REFERENCES resources(id) ON DELETE CASCADE, ...业务字段)
```

- Core 只查 `resources`（权限/审计/分类），**永不 JOIN 域表** → 双向解耦
- Domain 业务表有强 FK → 删除不悬空
- 纯 Core 资源只有 registry 一行

字段覆盖要求全部满足：`resource_id` / `resource_type` / `tenant_id` / `space_id` / `owner_id` / `classification` / `status` / `created_at` / `updated_at` / `deleted_at`。

### 6.1 ACL Subject 引用（**P1/P2-04 修正**）

> Resource **本身**用强引用（域表 FK → resources.id），但 **Resource 的 ACL 主体**（user/role/agent）如果用 `(subject_type, subject_id)` 弱多态就破坏了同样的不变量。本轮新增 `acl_subject_types` 注册表 + trigger 验证。

- **`acl_subject_types`**：白名单注册表（STEP 1-B 初始 key: **`user`/`role`/`agent`，不含 `group`**，P2-02），新增 type 必须先 INSERT 至此表
- **`resource_permissions.subject_type_id`** 强引用 `acl_subject_types.id`（FK ON DELETE RESTRICT）
- **`resource_permissions.subject_id`** 由 BEFORE INSERT/UPDATE trigger 验证存在：
  - `key='user'` → `users.id`（不限制 status；软删用户保留历史 ACL）
  - `key='role'` → `roles.id`（不限制 archived_at）
  - `key='agent'` → `agents.id`（不限制 archived_at）
  - 其他注册 key → 同模式
- **不在注册表** → 拒绝写入
- **User 软删** → ACL 保留（审计可追溯）；**User 硬删** → trigger 级联清理该 user 的所有 ACL
- **Role 删除** → FK RESTRICT 阻止；Role 归档由 trigger 标记该 role 的 ACL deny 行失效（allow 行保留用于审计追溯）
- **Membership removed** → **不预先清理 ACL**，由授权阶段 [8] 实时校验；用户重加入时 ACL 自动恢复

---

## 7. Agent / Tool Model

**Agent ≠ Model**：Agent 是有状态、有权限、有版本的执行实体；Model 是无状态推理服务，通过 `ai_routes` 间接选择。

**链路**：`agents →(agent_permissions)→ tools →(tool_permissions)→ permissions → Service → DB`
- DB 层不存在 agent 角色；`agents` 表禁止存连接串/凭据（CI 扫描项）
- `agent_permissions` 是**白名单**：未列出即拒绝

**Tool Risk 执行策略**

| Risk | 审批 | 审计 | 幂等 | 超时/重试 |
|---|---|---|---|---|
| LOW | 无 | 采样 10% | 建议 | 5s / ≤2 |
| MEDIUM | 无 | 全量（不含 payload） | 建议 | 15s / ≤3 指数退避 |
| HIGH | 可配置人工审批 | 全量（含 input digest） | **必须** | 60s / ≤2 |
| CRITICAL | **强制人工审批** | 全量 + 审批人 | **必须** | 300s / 不自动重试 |

- Tool 风险 > Agent 的 `max_risk_level` → 拒绝
- CRITICAL 工具默认 `enabled=false`
- 非幂等工具禁止重试（`max_attempts=1`）
- `denied` 也必须写 `tool_executions`

---

## 8. AI Gateway Model

```
ai_policies（分级/准入/预算/是否允许降级）
     ↓ 约束
ai_routes（capability → 主模型 + fallback 链）
     ↓ 选择
ai_models（能力/成本/延迟/合规上限/是否私有）
     ↓ 属于
ai_providers（适配器/base_url/隐私档位/健康/密钥引用）
```

**厂商不是硬编码**：OpenAI / Anthropic / Google / DeepSeek / Qwen / GLM / Ollama / vLLM / OpenAI-compatible / 私有模型，未来**全部只是往 `ai_providers` + `ai_models` 插数据**，Core 代码零改动、零 SDK import（架构守卫持续强制）。

`ai_providers.adapter` 是**适配器注册键**（如 `openai_compatible`），不是 `if provider == 'openai'` 的业务分支。

**路由决策**：policy 匹配（space > tenant > platform）→ route 按 priority → 主模型校验 → 失败则 fallback 链，**每个候选重新校验** → 全失败报错（**绝不降级到不合规模型**）。

**不变式**：`CK (allow_fallback = false OR fallback_preserves_classification = true)` 在数据库层面封死"降级到公共模型"。

---

## 9. Data Classification

```
PUBLIC → INTERNAL → CONFIDENTIAL → HIGHLY_CONFIDENTIAL
```

| 级别 | AI 准入 | 审计 |
|---|---|---|
| PUBLIC | 任意 enabled provider | 采样 |
| INTERNAL | `privacy_tier ∈ {vetted, private, self_hosted}` | 全量 |
| CONFIDENTIAL | `privacy_tier ∈ {private, self_hosted}` | 全量 + 摘要 |
| **HIGHLY_CONFIDENTIAL** | **仅 self_hosted**，`require_private=true`，**禁止跨 provider 降级** | 全量 + 告警 |

流向：`resource.classification → ai_policies.max_classification → provider 准入 → 允许/拒绝`
分级**只能升不能随意降**，降级必须写 `audit_logs` 并注明 `reason`。

---

## 10. Event / Audit Model — **P1-03 修正：at-least-once + CAS claim**

| | Event | Audit |
|---|---|---|
| 语义 | 发生了什么（事实） | 谁对什么做了什么、结果如何（责任） |
| 可否删除 | 投递后可清理 | **不可变**，仅整分区 drop |
| 可否重放 | 可 | 不可 |
| 是否含理由 | 否 | 是（`reason`、`risk_level`） |

**Event delivery = at-least-once**（**绝不承诺 exactly-once**）；消费方按 `event_id` 幂等。

- 写入：业务事务内 `INSERT events (status='pending', attempts=0, next_attempt_at=now())`
- 投递：CAS claim — `UPDATE events SET status='claimed', worker_id=$w, claimed_at=now(), lease_expires_at=now()+interval '60s' WHERE id IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING ...`
- 成功：`UPDATE ... SET status='delivered' WHERE id=$id AND status='claimed' AND worker_id=$w`
- 失败：`UPDATE ... SET status='pending', attempts=attempts+1, next_attempt_at=now()+exp_backoff, last_error=$err`
- 超阈值：`status='dead'` + 告警
- **Lease Reaper**（30s 周期）：`UPDATE events SET status='pending', last_error='lease_expired', next_attempt_at=now() WHERE status='claimed' AND lease_expires_at < now()` —— Worker 崩溃恢复
- 三个场景：① Worker crash → Reaper 接管；② Webhook 已发但写 delivered 失败 → 消费方按 `event_id` 幂等；③ 双 Worker 抢同一行 → CAS 自动胜出

**audit_logs 覆盖**：谁（actor）/ 何时（occurred_at UTC）/ 对什么（resource）/ 做了什么（action）/ 结果（result）/ 从哪（ip, user_agent）/ 为什么（reason）/ 关联（correlation_id, request_id）/ 风险（risk_level, classification）/ 上下文（metadata，**写入前脱敏**）。

---

## 11. ID 策略 → **UUIDv7**（**P1-02 修正：bit layout 已实测**）

| 维度 | BIGINT | UUIDv4 | **UUIDv7** |
|---|---|---|---|
| 索引局部性 | 优 | **差**（随机插入 → 页分裂、WAL 放大） | 优（时间前缀单调） |
| 排序 | 有序 | 无序 | 近似时间序（ms） |
| 分布式生成 | 需协调 | 自由 | 自由 |
| 迁移安全 | 易冲突 | 安全 | 安全 |
| 枚举风险 | 高 | 低 | 中（62bit 随机） |

**结论**：统一 UUIDv7，应用层生成为主，DB 提供 `uap_uuid_v7()` 兜底（回填/运维）。
**例外**：对外不透明标识（邀请码、重置 token）用 UUIDv4；需要隐藏创建时间的资源另设 `public_id`。
分区表主键为 `(id, occurred_at)`。

### 11.1 RFC 9562 Bit Layout

```
[0:47]  unix_ts_ms (48 bits, big-endian)
[48:51] ver        (4 bits, = 0b0111 = 7)
[52:63] rand_a     (12 bits)
[64:65] var        (2 bits, = 0b10)
[66:127] rand_b    (62 bits)
```

### 11.2 双重实现

| 路径 | 实现 | 用途 |
|---|---|---|
| **应用层（主）** | Python: `int(time.time()*1000).to_bytes(6,'big')` 写入 `[0:6]`，`os.urandom(16)` 写入其它位，覆盖 version=7 与 variant=10 | 批量预生成、跨库一致、无 DB 往返 |
| **DB 兜底** | `uap_uuid_v7()` (plpgsql)：基于内置 `gen_random_uuid()` 取 122 bit 随机位，用 `overlay` 覆盖 [0:6] 为当前 `clock_timestamp()*1000` 的大端 int8 | migration 回填、手工运维、跨语言一致 |

### 11.3 STEP 0 实测结果（**P1-02 通过**）

在临时库 `uap_uuid_probe` 上跑过 25 项断言，全部 PASS（详见 [STEP1A_ARCHITECTURE_REVIEW §P1-02](./STEP1A_ARCHITECTURE_REVIEW.md#p1-02-uuidv7-bit-layout--测试矩阵)）：

- **应用生成器** 10000 个：version=7×10000, variant=10xx×10000, 单调递增, 唯一
- **DB 兜底** 10000 个：同上 + timestamp 完美反推（同毫秒生成多个也独立）
- **跨毫秒同毫秒唯一性**：20000 个 DB 生成，单毫秒内零冲突
- **RFC 9562 字节布局**：手工逐字节校验 `[0:6]=ms_be`, `[6]&0xF0=0x70`, `[8]&0xC0=0x80`
- **时间反推**：`ts = uuid_ms_be[0:6]`，与生成时间误差 < 1ms

### 11.4 未来 PG 内置支持

PostgreSQL 18+ 提供内置 `uuidv7()` 函数。STEP 1-B 实施策略：
- DB 16（当前）：保留自定义 `uap_uuid_v7()`，trigger + 函数体一次性装入
- DB 18+：检测 `pg_proc WHERE proname='uuidv7'`，存在则将 `uap_uuid_v7()` 改为别名（无行为差异）

---

## 12. 时间策略

- **只用 `timestamptz`**（禁用 `timestamp`）；连接 `TIME ZONE 'UTC'`；精度 `timestamptz(3)`
- `updated_at` 由 **DB trigger** 维护，不依赖应用
- 语义分工：`created_at` / `updated_at` / `deleted_at` / `archived_at` / `expires_at` / `occurred_at`（业务时间，可回填）/ `revoked_at`
- 分区键一律 UTC 月边界；展示层才做时区转换

---

## 13. Delete / Retention 策略

**不做全局 soft delete**，逐类判定：

| 策略 | 实体 | 理由 |
|---|---|---|
| **soft delete** | `users`、`tenant_memberships`、`memberships`、`tenants`、`spaces`、`resources` | 外键众多、需可恢复窗口、合规留存 |
| **revoke / disable** | `identities`、`devices`、`agents`、`tools` | 撤销即失效，但必须保留"曾存在"证据 |
| **expire + hard delete** | `sessions`、`credentials`、`resource_permissions` | 随时间价值归零；凭据留着只增加泄露面 |
| **immutable** | `agent_versions`、`tool_versions`、`audit_logs` | 可追溯性 / 合规，只能 deprecate 或整分区 drop |
| **hard delete（分区）** | `events`(30d)、`tool_executions`(90d)、`ai_request_logs`(90d) | 高吞吐运维数据 |

保留期默认：audit 365d、events 30d、tool_executions 90d、ai_request_logs 90d、软删 30d 后 purge、归档 90d 后 purge。

### 13.1 FK 删除策略（**P2-03 统一**）

- **业务数据实体一律 `RESTRICT`**：尤其 `resources.tenant_id → tenants.id RESTRICT`、`resources.space_id → spaces.id RESTRICT` —— 资源**不**随 Tenant/Space 物理删除级联
- Tenant/Space 的资源清理只走 **archive → soft delete → retention → controlled purge**（purge job 分批执行，非 DB 级联）
- `ON DELETE CASCADE` 仅限技术/关系子实体，逐项理由见 `CORE_DOMAIN_MODEL.md` §11.1 白名单（sessions / credentials / devices / identities / versions / 权限绑定 / membership 关系行 / roles 配置行 / ACL / 1:1 域扩展随 registry 受控 purge）
- 反向禁例：`resources` 无 CASCADE 出边指向业务表；域扩展表 FK 在域表侧（删 resources 才触发级联，方向受控）

---

## 14. Migration Strategy → **迁移到 Alembic**

**自研 runner 不可持续**，直接引爆点是 **P0 语句切分缺陷**（`$$` 函数体、字符串内分号），而 STEP 1-B 必须写 `set_updated_at()` 等 trigger 函数。此外还缺 autogenerate、downgrade、版本图/merge、离线 SQL 与可逆性测试。

**Alembic 契合点**：与 SQLAlchemy 2.0 同源、版本图与 merge、autogenerate、事务性 DDL、`--sql` 离线审核、成熟生态。
**代价与缓解**：autogenerate 需人工复核（漏 check/分区/RLS/trigger）→ 只当草稿；统一入口禁止裸 SQL 混用。

**策略要点**
- 切换路径：`alembic init` → `stamp 0001_baseline` 对齐现有库 → 后续全部 Alembic；旧 runner 保留一个发布周期只读后下线
- 版本：`NNNN_snake_case_slug`，单一主干，并行分支必须 `merge`
- **expand → migrate → contract** 三阶段发布；破坏性变更拆到 contract 阶段
- downgrade：结构性变更必须提供；**生产默认 forward-fix**，downgrade 仅用于非生产和紧急回退
- checksum：沿用 `schema_migrations.checksum` + CI 门禁（已发布 revision 文件不得修改）
- 生产：单实例 leader 锁、`lock_timeout` / `statement_timeout`、大表用 `CONCURRENTLY`（非事务，需显式清理预案）
- 备份：PITR（7–14 天）+ 每日逻辑备份（30 天）+ 迁移前强制快照；季度恢复演练
- 恢复：事务性 DDL 自动回滚；非事务性操作（CIC、`ALTER TYPE ADD VALUE`）写显式清理；回填幂等可重跑
- CI：up → down → up 冒烟、漂移检测、checksum 门禁、`--sql` 审核、禁止项扫描

详见 [MIGRATION_STRATEGY.md](./MIGRATION_STRATEGY.md)。**本阶段不实施。**

---

## 15. Index 策略

原则：**只为已知查询模式建索引**，季度清理零扫描索引。

关键索引（完整清单见 [§12](./CORE_DOMAIN_MODEL.md#12-index-strategy)）：
- 身份：`lower(email)` 部分唯一、`(user_id, fingerprint)` 唯一、`token_hash` 唯一、`(expires_at) WHERE status='active'` 部分索引（TTL）
- 租户/空间：`(tenant_id, lower(key))` 部分唯一、`(tenant_id, user_id)`、`(space_id, user_id) WHERE removed_at IS NULL`
- 资源：`(tenant_id, space_id, resource_type, status)` 复合（主查询）、`(tenant_id, owner_id)`
- 幂等：`(tool_id, idempotency_key)` 部分唯一
- 审计：`(tenant_id, occurred_at DESC)`、`(actor_id, occurred_at DESC)`、`(correlation_id)`、`(risk_level, occurred_at) WHERE risk_level IN ('HIGH','CRITICAL')`
- outbox：`(status, next_attempt_at) WHERE status='pending'`

**不建**：低基数列单列索引、未确认查询的 jsonb GIN。

---

## 16. Security Review

| 主题 | 设计 |
|---|---|
| 凭据 | 只存 argon2id 哈希；明文列为**禁止列**（CI 扫描） |
| 会话 | 只存 `token_hash`；`absolute_expires_at` 防无限续期 |
| AI 密钥 | `secret_ref` 引用；**任何表不得存 API Key 明文** |
| DB 角色 | `uap_app`(DML) / `uap_migrator`(DDL，仅迁移窗口) / `uap_readonly`；运行时无 DDL 权限 |
| 审计不可变 | 仅 `INSERT, SELECT` + `BEFORE UPDATE/DELETE` trigger 抛异常 |
| 版本不可变 | 已发布 `agent_versions` / `tool_versions` 禁止 UPDATE/DELETE |
| 租户隔离 | 复合索引 + 应用层断言 + RLS(可选) + 越权审计 |
| 分级 | 只升不降；HIGHLY_CONFIDENTIAL 禁止跨 provider 降级 |
| 脱敏 | 审计 metadata 与日志统一走 `redaction`；CRITICAL 只存摘要 |
| 留存 | 按月分区，整分区 drop，避免大表 DELETE 的锁与膨胀 |
| 备份 | PITR + 快照 + 恢复演练；备份加密密钥与 DB 凭据分离 |

---

## 17. Core Independence Audit（实际扫描结果）

扫描脚本：18 个行业词 × 全部 `.py/.sql/.md/.yml/.toml`（排除 `.git`/`node_modules`），按 `Core 实现 / 测试守卫 / 文档 / Domain 层` 四类归类。

### 17.1 Core 实现命中（7 处，逐条定性）

| 文件 | 词 | 上下文 | 判定 |
|---|---|---|---|
| `README.md:6` | family, company, restaurant | "no family, company, restaurant, business or entertainment functionality has been implemented" | ✅ **合理**（文档声明不做这些业务） |
| `README.md:7` | entertainment | 同上 | ✅ 合理 |
| `README.md:27` | family, company, entertainment | "domains/ family \| company \| business \| entertainment (manifests only)" | ✅ 合理 |
| `README.md:29` | order | "ordered .sql files" | ⚪ **误报**（通用英文词） |
| `infrastructure/database/migration.py:7,133` | order | "ordered, idempotent" / "in version order" | ⚪ 误报 |
| `agent/runtime/interfaces.py:3` | order | "Execution order is fixed" | ⚪ 误报 |
| `docs/.../CORE_DOMAIN_MODEL.md:680` | order | SQL `ORDER BY next_attempt_at` | ⚪ 误报 |

### 17.2 结论

| 分类 | 命中 | 判定 |
|---|---|---|
| **Core 实现中的真实业务实体** | **0** | ✅ **PASS** |
| 文档中的业务词（README/架构文档） | 4 文件 | ✅ 合理（均为"禁止/不做"的声明或示例），**不因扫描而删除** |
| 测试/守卫中的业务词 | 3 文件 | ✅ 合理（守卫必须包含这些词才能拦截；`test_migration_runner` 显式断言"不存在业务表"） |
| Domain 层 | 7 文件 | ✅ 设计允许（`domains/*` 本就是业务域） |
| 通用词误报 | 4 处 | ⚪ `order`（ordered / ORDER BY / execution order） |

**审计判定：PASS** —— Core 未出现任何行业业务实体；`core/` 目录零命中（含 `core/*` 全部 12 个模块）。

> 说明：扫描器按路径归类，根目录 `README.md` 被归入"Core 实现"桶，人工复核后属文档。已逐条列出以免"扫描即通过"的自欺。

### 17.3 架构守卫现状（STEP 0 建立，持续有效）

`tests/architecture/test_dependency_rules.py` 9 项全过，含：core 不得 import domains / core 不得含行业词 / intelligence 不得 import 厂商 SDK / agent 不得触碰数据库 / domains 不得定义 schema。

---

## 18. Open Questions（需人工决策）

| # | 问题 | 影响 | 倾向 |
|---|---|---|---|
| **Q1** | **RLS 是否在 STEP 1-B 启用？** | 与连接池配合需事务内 `SET LOCAL`，复杂度与收益权衡 | 建议 1-B 先建策略定义不启用，1-C 压测后启用 |
| **Q2** | `users.email` 用 `citext` 扩展还是 `lower()` 表达式索引？ | 依赖 vs 简洁 | 倾向 **lower() 表达式索引**（零扩展依赖） |
| **Q3** | 是否引入 `resource_relations`（资源层级/权限继承）？ | 权限评估需递归查询，复杂度显著上升 | 建议 **1-B 不建**，先用 `space_id` 扁平归属 |
| **Q4** | `events` 仅用 PG outbox，还是引入外部 broker（Redis Stream / Kafka）？ | 吞吐与运维成本 | 建议 1-B **仅 PG outbox**，量级上来再引 |
| **Q5** | 审计保留期 365 天是否满足合规要求？ | 存储成本与合规 | **需业务方确认** |
| **Q6** | 是否需要独立的配额表 `ai_quotas`（按租户/空间的日/月额度）？ | 当前 `ai_policies.budget_daily_usd` 只覆盖日预算 | 建议 1-B 暂不建，用 policy 字段 |
| **Q7** | `memberships` 与 `tenant_memberships` 是否合并为一张带 scope 的表？ | 查询简洁 vs 语义清晰 | 倾向**保持分离**（语义与约束都更清晰） |
| **Q8** | 是否需要 `groups`（用户组/团队）作为授权单元？ | 多用户授权场景 | 建议 1-B **不建**；`group` 是未来 ACL subject 扩展（P2-02），启用路径见 REVIEW Round 3 |
| **Q9** | `spaces.kind` 是否需要注册表（谁有权注册 kind）？ | 防止 kind 命名混乱 | 建议 1-C 引入 `domain_space_kinds`，1-B 只做格式约束 |
| **Q10** | UUIDv7 DB 兜底函数是否依赖扩展（pgcrypto）？ | 迁移可移植性 | 建议用内置 `gen_random_uuid()` 拼装，**零扩展依赖** |

---

## 19. Architecture Risks

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| **R1** | **Alembic 切换期双轨**（旧 runner + Alembic 并存可能重复执行） | 中 | 切换即 `stamp` 对齐；旧 runner 降级为只读；CI 校验只有一个入口 |
| **R2** | **分区表维护**（按月分区需预建与清理，否则写入失败） | 中 | 分区管理 job + 监控（未来 3 个月分区存在性告警）；或引入 pg_partman |
| **R3** | **RLS + 连接池**（`SET LOCAL` 泄漏到其它请求 → 越权或全表不可见） | 中 | 若启用：连接归还前 `RESET`；单测断言"无 tenant 上下文时查询返回 0 行" |
| **R4** | **共享主键扩展模式**增加写入事务复杂度（两表同事务） | 中 | 仓储层封装 `create_resource_with_payload()`，域侧不直接插两表 |
| **R5** | **ABAC conditions jsonb 求值性能**（高频鉴权路径） | 中 | 条件预编译 + 决策缓存（按 subject+resource+action 缓存，tenant 维度失效） |
| **R6** | **审计全量写入放大** | 中 | HIGH/CRITICAL 同步写，LOW 异步批量；写入失败进 outbox 补偿，不阻塞主流程 |
| **R7** | **fallback 链配置错误导致可用性下降**（配了不允许的 fallback 等于没有 fallback） | 中 | 配置校验器（启动时检查 fallback 候选均满足 policy）+ 演练 |
| **R8** | **UUIDv7 泄露创建时间** | 低 | 对外暴露另设 `public_id`(v4)；枚举防护靠授权层不靠 ID |
| **R9** | **版本不可变导致存储增长**（agent/tool 版本长期累积） | 低 | 只保留最近 N 个版本 + 被引用的历史版本，其余 deprecate 后可归档 |
| **R10** | **`spaces.kind` 无注册表导致命名混乱** | 低 | 格式 CHECK + 1-C 引入注册表（Q9） |

---

## 20. Recommended STEP 1-B Plan

**前提：本设计经人工审计批准并冻结。** 未批准前不写任何 migration。

### B0 — 迁移基础设施切换（先决）
1. 引入 Alembic，`alembic init` + `env.py`（从 `DATABASE_URL` 读取，不 import domain）
2. `alembic stamp 0001_baseline` 对齐现有库（PG 已应用 0001）
3. 建立通用基础设施：`uap_uuid_v7()`、`set_updated_at()` trigger、分区管理 job 与脚本
4. 旧 runner 降级为只读（`--status`），保留一个发布周期
5. CI：up→down→up 冒烟、漂移检测、checksum 门禁

### B1 — Identity 域
`users` / `identities` / `credentials` / `devices` / `sessions` + 索引与 CHECK + 凭据明文禁止扫描测试

### B2 — Tenancy 与授权
`tenants` / `spaces` / `tenant_memberships` / `memberships` / `roles` / `permissions` / `role_permissions`
含：`memberships.tenant_id` 一致性 trigger、三作用域部分唯一索引、（可选）RLS 策略定义（Q1 决定启用与否）

### B3 — Resource / Agent / Tool
`resources` / `resource_permissions` / `agents` / `agent_versions` / `agent_permissions` / `tools` / `tool_versions` / `tool_permissions` / `tool_executions`
含：已发布版本不变性 trigger + 权限回收

### B4 — AI Gateway / Event / Audit
`ai_providers` / `ai_models` / `ai_routes` / `ai_policies` / `ai_request_logs` / `events` / `audit_logs`
含：分区、审计 append-only 权限与 trigger、AI 分级不变式 CHECK

### 每批交付门禁
1. migration + downgrade 通过 CI 冒烟
2. 新增仓储层测试（不越权、tenant 隔离、幂等）
3. 架构守卫（`pytest tests/architecture`）全过
4. 安全守卫（`pytest tests/security`）全过，含"明文凭据列不存在"
5. 全量 `pytest` 无回归 + integration 实连通过
6. 业务表扫描：仍为 0

### 明确不在 STEP 1-B
- 任何 Domain 业务表（family / company / restaurant / entertainment 相关）
- 任何 AI Provider SDK 接入
- 具体 Agent / Tool 实现
- Frontend 产品功能
- 旧"小智"业务代码迁移

---

## 冻结状态

| 项 | 状态 |
|---|---|
| 设计文档 | 已产出（4 份），未提交 git |
| 数据库表 | **未创建任何新表** |
| migration | **未新增** |
| Core 代码 | **未修改**（`git status` 仅有新增文档） |
| Tag | **未创建**（等待审计批准后按指示处理） |

**STOP — 等待人工审计批准，方可进入 STEP 1-B。**
