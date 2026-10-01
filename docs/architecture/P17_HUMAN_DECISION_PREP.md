# P17 HUMAN DECISION PREP

```text
主题（推荐）  = P17 — PLATFORM IDENTITY / TENANT / SPACE RUNTIME
性质          = PREP ONLY（只读发现 + 决策输入；NOT FROZEN · NOT AUTHORIZED）
基线          = UAP-V0.1.15-P16-AGENT-RUNTIME = RELEASED
                HEAD = origin/main = 42a4f61c20fe119af77ab822e24c8028ce653e3d
                tree = 242c82f3a2ac90a53fe3ed2b908baf5c1bdf0528 · tags = 14 · staged = 0
证据来源      = migration 0002–0007 / P13 seed / P14 runtime / P16 runtime + live schema + 代码
```

## 1. Existing Schema（实测 · 全部已存在）

| 对象 | 关键列 | 层级语义（由 schema 取证） |
|---|---|---|
| `tenants` | slug · display_name · status · plan · region · settings · archived_at · deleted_at | 租户根，无 parent |
| `spaces` | **tenant_id** · key · kind · visibility · status · settings · owner_id | 空间属租户（tenant-scoped） |
| `users` | email · username · status · primary_identity_id · deleted_at | **无 tenant_id** ⇒ 平台级主体 |
| `identities` | user_id · provider · issuer · subject · status · verified_at | 一个 user 可多身份源 |
| `credentials` | identity_id · user_id · type · secret_hash · algorithm · expires_at · revoked_at | 凭据（Argon2id） |
| `devices` | user_id · fingerprint · platform · status · revoked_at | 设备绑定 |
| `sessions` | user_id · identity_id · device_id · token_hash · expires_at · absolute_expires_at · status | 会话 |
| `platform_memberships` | user_id · role_id · status | 平台级 membership + role |
| `tenant_memberships` | tenant_id · user_id · role_id · status · role_assigned_by/at | 租户级 membership + role |
| `memberships` | tenant_id · **space_id** · user_id · role_id · status | 空间级 membership + role |
| `roles` | **tenant_id** · **space_id** · key · scope · is_system · status | role 可 platform / tenant / space scoped |
| `permissions` | key · resource_type · action · is_system | 平台级权限词表（12 canonical） |
| `role_permissions` | role_id · permission_id · effect · conditions | 角色→权限绑定 |
| `resource_permissions` | resource_id · subject_type_id · subject_id · action · effect · conditions · expires_at | 实例级 ACL |
| `acl_subject_types` | key（user / role / agent） | ACL 主体白名单（P13 seed 3 行） |
| `platform_state` | bootstrap_state · initialized_at | 平台引导状态 |

```text
⇒ 三级 membership 已存在：platform_memberships / tenant_memberships / memberships(space)
⇒ 多租户 = 一个 user 多行 tenant_memberships；空间访问由 memberships(space) 表达
⇒ roles 自带 scope（platform/tenant/space）+ tenant_id/space_id 归属
⇒ 未发现需要新表的语义缺口（P17-D02/D13 倾向 A / NO NEW TABLE）
```

## 2. Existing Runtime（实测 · 代码面）

```text
已有 runtime（services/）
  identity  : identity/{service,repository,hashing}.py —— 凭据校验（Argon2id）
  session   : session/{service,repository}.py —— 会话签发 / 刷新 / 撤销
  device    : device/{service,repository}.py —— 设备注册 / 撤销
  context   : context/{builder,model,authorization_adapter}.py —— AuthenticatedRuntimeContext
              （不可变 · 仅标识与已验证事实 · LOG_SAFE_FIELDS 白名单）
  use_cases : login / logout / refresh_session / onboard_identity / device enrollment / expire sessions
  authorization : services/authorization/*（决策服务 · ToolGate · RBAC + ACL + Policy）

契约层（core/）：identity · tenant · space · membership · permission · policy · resource ·
                session · auth · device · audit · event · agent · ai

完全缺失的 runtime
  无 tenant runtime（无 services/tenant/*）
  无 space runtime（无 services/space/*）
  无 membership runtime（仅 authorization repository 只读查询 membership 解析角色）
  无 tenant / space / membership API

API（apps/api/routes/）：health · meta · identity · devices · sessions · agent_runs
  ⇒ 无 /tenants · /spaces · /memberships 路由（P17 API gap 已确认）
```

## 3. Authentication 现状（P17-D09 输入）

```text
已有：password 凭据（credentials · Argon2id）· session（token hash + absolute expiry）·
      设备身份（devices）· identity provider 抽象（identities.provider/issuer/subject）·
      authentication assurance 三级（credential_verified / identity_verified / session_verified）
未发现：OIDC / JWT 校验 / API key / 外部 IdP federation 实现
⇒ P17 复用既有 session/authentication；不新增 authentication architecture（D09 = OUT）
```

## 4. Security Boundary（P14 grants · 实测 · 关键发现）

| 表 | uap_runtime 现有权限 | 含义 |
|---|---|---|
| users / identities / credentials / devices / sessions | SELECT, INSERT, UPDATE | 身份与认证面可写（P14 已授权） |
| tenant_memberships / memberships | SELECT, INSERT, UPDATE, DELETE | membership 变更已授权 |
| **tenants** | **SELECT only** | 无写权限 ⇒ tenant mutation 属 bootstrap / migrator |
| **spaces** | **SELECT only** | 无写权限 ⇒ space mutation 不在 runtime 面 |
| roles / permissions / role_permissions / resource_permissions / acl_subject_types / platform_memberships / platform_state | SELECT only | 授权配置面只读 |

```text
⇒ P17 若提供 tenant / space 写 API，必须新增 uap_runtime 的 INSERT/UPDATE（甚至 DELETE）
   ⇒ 属新的 privilege surface ⇒ 必须 Human Decision（不得自动扩大）
⇒ P17 若只做读取 + 上下文解析 + membership 管理，则现有 grant 已足够（零新 grant）
⇒ 禁止 GRANT ALL / 扩大默认 ACL / 借用 uap_migrator / uap_bootstrap

## 5. Core Actor Model（P16 继承不变式，不得破坏）

```text
Actor（User / Role / Agent） ≠ Agent（业务执行体） ≠ Worker（执行机制 · 非 ACL subject）
                            ≠ DB Principal（uap_app / uap_runtime / uap_bootstrap / uap_migrator / uap_seed）
Agent 不继承 User 权限（P16-D05 冻结）；受保护操作 = Actor 授权 ∧ Agent 授权 ∧ ToolGate
tenant_id = NULL ⇒ platform-scoped（P15/P16 冻结）；NULL ≠ unknown tenant ≠ bypass
安全先例：P16 修复过「tool 查询缺 tenant 谓词」的跨租户解析缺陷 ⇒ P17 所有查询必须 tenant scoped
```

## 6. Tenant / Space 语义（schema 取证结论）

```text
user 可否属于多个 tenant？      → tenant_memberships 为 (tenant_id, user_id) 多行结构 ⇒ 支持多租户
tenant 可否有多个 space？        → spaces.tenant_id ⇒ 是
membership 是 tenant 还是 space？ → 两者都存在（tenant_memberships / memberships(space)）
role 是 tenant 还是 space scoped？→ roles.scope + tenant_id/space_id ⇒ 两者皆可，platform 亦可
permission 是 global/tenant/space？→ permissions 为平台级词表；作用域由 role scope + ACL 表达
未冻结（进入 OQ）：跨 tenant / 跨 space / 缺失 membership 的默认策略 ·
                  spaces.visibility 与 membership 的关系 · platform_memberships 运维路径
```

## 7. P17 Decision Questions（候选 · 未冻结）

| ID | 主题 | 候选 | BOT 建议（analysis only） | 证据 |
|---|---|---|---|---|
| P17-D01 | Runtime ownership | A 现有 uap_runtime · B 新 role | A | P14 dedicated boundary · P16 已验证 |
| P17-D02 | Schema strategy | A 复用 · B 改既有 · C 新表 | A（现有 schema 已能表达三级 membership） | §1 |
| P17-D03 | Identity runtime scope | A User+Tenant+Space+Membership · B 加完整认证子系统 · C 加外部 IdP | A | §2/§3 |
| P17-D04 | Role assignment 层级 | A tenant · B space · C 两者 | C（schema 已支持两者） | roles.scope · memberships.role_id |
| P17-D05 | Multi-tenant membership | A 单租户 · B 多租户 | B（tenant_memberships 多行天然支持） | §1 |
| P17-D06 | Cross-tenant 行为 | A DENY-by-default · B 显式例外 | A（无冻结例外条款） | P16 tenant-scoped 先例 |
| P17-D07 | Space isolation | A tenant membership ⇒ 全部 space · B 需显式 space membership | B（A 会绕过 memberships 表） | §1 |
| P17-D08 | Agent context | A 继承 owner tenant/space · B 由 agents.tenant_id/space_id 显式解析 | B（A 违反 Agent ≠ User） | 0011 agents |
| P17-D09 | Session / authentication | A OUT · B 最小集成 | A（现有 session/context 已可用） | §3 |
| P17-D10 | API scope | A 只读 · B 读+写 tenant/space/membership · C 仅 membership | 需 Human 决定（B 需新 grant） | §4 |
| P17-D11 | Audit | A identity/membership 变更全部审计 · B 仅授权变更 | A（P14/P16 审计边界已存在） | §2 |
| P17-D12 | Event activation | REJECT | REJECT（Allowlist EMPTY · Handlers 0） | P15 O-5 / P16 D08 |
| P17-D13 | Schema expansion | A 无新表 · B 最小新增 | A | §1 |
| P17-D14 | Testing strategy | 同租户允许 · 跨租户拒绝 · 错 space 拒绝 · 无 membership 拒绝 · 角色移除后拒绝 · agent-user 分离 · actor 传播 · 最小权限 · 审计关联 | — | §1/§4 |

## 8. Open Questions（P17-OQ）

```text
P17-OQ-01 tenant 写操作（create/update/archive）属 runtime 还是 bootstrap？（现状：仅 SELECT ⇒ bootstrap/migrator）
P17-OQ-02 space 写操作同问（现状：uap_runtime 对 spaces 仅 SELECT）
P17-OQ-03 默认拒绝策略是否需要成文冻结（跨 tenant / 跨 space / 缺失 membership）
P17-OQ-04 spaces.visibility（列已存在）的取值语义与 membership 的关系未冻结
P17-OQ-05 platform_memberships 运维路径（谁可授予平台角色）未冻结
P17-OQ-06 roles.is_system / permissions.is_system 的变更约束未冻结
P17-OQ-07 resource_permissions（ACL）是否允许 runtime 写入（现状仅 SELECT）
P17-OQ-08 membership 删除（DELETE 已授权）与审计/事件记录的关联方式未冻结
```

## 9. Scope / 依赖 / 边界

```text
IN（候选）：User/Tenant/Space/Membership context runtime · role binding 集成 · actor/context 解析 ·
           authorization 集成 · 最小 API · audit 关联 · security boundary（零新 grant 前提下）
OUT：业务模块（Company / Restaurant / Entertainment）· Production Event Activation · handlers ·
     workflow engine · multi-agent · 外部 IAM federation · billing / subscription · P18

依赖图：
  P13（seed：acl_subject_types 3 · permissions 12 · platform_admin × 12 allow）
    → identity/tenant/space/membership schema（0002–0004）
    → authorization（P09/P14：RBAC + ACL + Policy · ToolGate）
    → P14 runtime security（uap_runtime · 51 baseline + 分区）
    → P16 actor/agent runtime（Agent ≠ User · tenant-scoped 查询先例）
    → P17 identity/tenant/space runtime（本阶段候选）
    → future Company / Commercial / Entertainment / Event Activation
硬依赖：P13 seed · P14 principal 边界 · authorization 服务
软依赖：P16 agent context（agent owner/tenant 解析）· session/context（已有）
未来依赖：Event Activation（P17 明确不做）
Core → Domain = 0（本轮只读复核通过；PREP 未引入任何代码）
```

## 10. 结论

```text
Migration Required  = NO（唯一可能的变更是 tenant/space 写 API 所需的 GRANT，不是 DDL/migration）
New Tables Required = NO（现有 schema 已表达 platform/tenant/space 三级 membership 与 role scope）
Production Event    = NO（Allowlist EMPTY · Handlers 0 保持不变）
Formal DB           = UNCHANGED（本轮只读）
Git                 = HEAD = origin/main = 42a4f61 · staged = 0 · tags = 14（未 commit/tag/push）
PREP                = PASS（16 项 PREP acceptance 均有实测证据；8 个 OQ 已登记）
IMPLEMENTATION      = NOT AUTHORIZED
```

**END OF P17 HUMAN DECISION PREP（PREP ONLY · NOT FROZEN）**
```
