# P17 IDENTITY / TENANT / SPACE RUNTIME — IMPLEMENTATION CONTRACT

## 0. 状态与权威

```text
状态        = RULES AUTHORITY（由已冻结决策派生；不是新决策来源）
派生自      = PLATFORM_DECISION_LOG.md 附录 W（P17-D01…D14 + OQ-01…08）
              + 附录 V（P16）· 附录 U（P15）· P14 runtime security · P13 seed
基线        = UAP-V0.1.15-P16-AGENT-RUNTIME（HEAD 42a4f61 · tree 242c82f3）
不得        = 新建平行 decision authority · 修改冻结决策 · 跳过 Freeze 直接实现
```

## 1. 范围

```text
IN  = User/Tenant/Space 上下文解析 · Membership runtime（读+写）· role binding 集成 ·
      actor/context 解析 · 既有 authorization 集成 · 最小 API（tenant/space 读 + membership 读写）·
      audit 关联 · security boundary
OUT = 业务模块（Company / Commercial / Entertainment）· tenant/space 结构写 ·
      platform membership 写 · role/permission/ACL 管理 · Production Event Activation ·
      IAM federation（OIDC/OAuth/SAML/LDAP）· workflow · multi-agent · billing · P18
```

## 2. 硬不变量（23 条 · 必须逐条可验证）

```text
1  User 无 tenant_id 所有权捷径（users.tenant_id 保持 NULL）
2  User 可属多个 tenant（tenant_memberships 多行）
3  Tenant membership 不隐含 space membership
4  Space 访问需显式 space membership（除非既有平台语义明确授权）
5  Cross-tenant access = DENY by default
6  Cross-space access   = DENY by default
7  Role scope 必须与 membership scope 一致（tenant↔tenant-scoped role；space↔space-scoped role）
8  Agent tenant scope 来自 agents.tenant_id
9  Agent space scope 来自 agents.space_id（NULL = tenant-scoped agent）
10 Agent 永不继承 User 权限（P16-D05）
11 Context resolution ≠ authorization ALLOW
12 既有 authorization engine 保持 canonical（不新增第二套）
13 platform_memberships 不被 P17 runtime 修改
14 roles / permissions / role_permissions / system objects 不被 P17 runtime 修改
15 resource_permissions（ACL）不被 P17 runtime 修改
16 tenants / spaces 对 uap_runtime 只读
17 Membership mutation 必须被审计（且不得 best-effort 后放行）
18 Production Event Allowlist 保持 EMPTY
19 Production Handlers 保持 0
20 Core → Domain = 0
21 Formal DB 在验证期间保持不变
22 无新表
23 无 migration
```

## 3. 上下文模型与解析顺序

```text
User（平台级主体）
  → Identity / Session（既有 runtime）
  → Membership resolution（platform / tenant / space 三级）
  → Tenant（tenant_id 必须显式选择）
  → optional Space（space_id 可空 = tenant-level context）
  → Role context
  → Authorization（既有 canonical path）
```

```text
选择规则：多个 membership ⇒ 必须显式选择 tenant；多个可访问 space ⇒ 必须显式选择 space。
禁止 first / latest / alphabetical / hard-coded default tenant 或 space。
允许 tenant-only context（space_id = NULL）与 tenant+space context 两种形态；
不得强制所有请求携带 space_id。
```

## 4. Agent 集成（不修改 P16 runtime）

```text
tenant mismatch → DENY
agent.space_id 非空 且 request space ≠ agent.space_id → DENY
agent.space_id 为空 且 request 在同一 tenant → 可进入 tenant-level agent context
最终仍需：Actor authorization + Agent authorization +（涉及工具时）ToolGate
agent owner 不自动成为 agent authority
```

## 5. API 边界（行为冻结 · URL 需遵循现有 convention）

```text
允许行为：tenant read · space read · tenant membership read/write · space membership read/write ·
          context resolution
禁止行为：tenant create/update/delete · space create/update/delete ·
          platform membership mutation · role / permission / ACL administration
候选（方向，不是最终 URL）：GET /tenants · GET /tenants/{id} · GET /tenants/{id}/spaces ·
  GET|POST /tenants/{id}/members · PATCH|DELETE /tenants/{id}/members/{user_id} ·
  GET|POST /tenants/{id}/spaces/{space_id}/members · PATCH|DELETE …/{user_id}
实现前必须核对仓库现有 API naming / response / error convention。
```

## 6. Membership 完整性（写入前验证）

```text
Tenant membership：tenant_id ≠ NULL · user_id ≠ NULL · role_id ≠ NULL ·
  role.scope = TENANT（tenant-scoped）· role.tenant_id = membership.tenant_id
Space membership ：tenant_id ≠ NULL · space_id ≠ NULL · user_id ≠ NULL · role_id ≠ NULL ·
  role.scope = SPACE · role.tenant_id = membership.tenant_id · role.space_id = membership.space_id ·
  space.tenant_id = membership.tenant_id
⇒ 客户端提交的 tenant_id / space_id / role_id 组合必须独立验证，不得视为合法关系
⇒ 禁止 「Tenant A + Space B」 这类跨租户组合通过应用层参数拼装成立
```

## 7. Audit 契约

```text
审计对象：tenant membership create/update/delete · space membership create/update/delete
必须包含：actor · tenant_id · space_id（适用时）· target user · role · action · correlation · timestamp
禁止包含：password · secret · credential plaintext · session token · SQL text · stack trace ·
          raw Authorization header
删除审计事实不得依赖被删除的 membership row 继续存在
membership mutation + audit 必须同一逻辑事务边界；若现有审计基础设施无法满足，必须停止并提交
新的 decision exception，不得以 best-effort logging 继续放行
```

## 8. Data Access Rule

```text
每个 repository 查询必须显式声明作用域：tenant-scoped / space-scoped / platform-scoped。
禁止 generic get_by_id() 后在业务层忘记 scope；若存在通用 repository，scope 必须是显式参数，
或在上层明确证明该查询为 platform-global。
tenant predicate 是 runtime correctness requirement，不是优化项（P16 真实缺陷先例：
tool lookup 缺少 tenant 谓词）。
```

## 9. 安全与权限

```text
Privilege gate：implementation 前必须证明 P17 所需权限 = 现有权限（new runtime grants = 0）。
  若发现 tenant INSERT / space INSERT / role UPDATE / ACL UPDATE 必要 ⇒ STOP（新 privilege surface
  ⇒ 新 Human Decision）。
不得：GRANT ALL · 扩大 default ACL · 借用 uap_migrator / uap_bootstrap / platform_admin ·
      绕过既有 authorization · 把 context 当作 ALLOW。
```

## 10. 测试契约（D14）

```text
正路径：authenticated user → valid tenant membership → valid space membership → role context →
        authorization → API operation；multi-tenant user（Tenant A context ≠ Tenant B context）；
        tenant-scoped / space-scoped agent
负路径（必须 DENY 且不改 DB 状态）：no tenant membership · different tenant · no space membership ·
        different space · deleted membership · disabled/ineligible role · tenant-space mismatch ·
        role scope mismatch · platform membership misuse · agent/user inheritance attempt ·
        agent tenant mismatch · agent space mismatch · forged tenant_id · forged space_id ·
        foreign membership mutation · system role mutation · resource_permissions write attempt
纪律：逐文件显式 allowlist（禁目录级 pytest）· forbidden tests = 0 ·
      OI-G-4 = 0 · formal DB unchanged · Core → Domain = 0 · secret leakage = 0 ·
      authorization bypass = 0
```

## 11. 继承的基线（不得回归）

```text
P16 = regression baseline（P16 unit/architecture/security · 6 integration 场景 · R-1 durability）
P15 = regression baseline（65/0 · D-02 历史失败保持）
P14 = security baseline（uap_runtime principal · 51 baseline + 分区）
P13 = seed baseline（acl_subject_types 3 · permissions 12 · platform_admin × 12 allow）
```

**END OF P17 IDENTITY / TENANT / SPACE RUNTIME IMPLEMENTATION CONTRACT（RULES AUTHORITY · 派生自附录 W）**

---

## 12. P17 AUTHORIZATION RESOLUTION（派生自 PDL 附录 X · 2026-10-01）

§2 的 23 条硬不变量全部保留且未被改写；本节只补充授权模型的具体承载。

```text
1  membership CRUD 映射到既有 member 权限（P17-AUTH-Q2）
2  read / list 使用 member.read
3  create / update / delete 使用 member.admin
4  P17 不扩展权限词表（permissions 保持 12 行 · P13 不变）
5  canonical resources 是授权的强制前置条件
6  resource provisioning 属 Control Plane / Bootstrap
7  uap_runtime 永不 self-provision resource（对 tenants/spaces 无写权限 ⇒ 物理不可执行）
8  tenant membership 管理 = tenant-scoped
9  space membership 管理 = space-scoped
10 tenant 角色授权不自动扩展到 space
11 space 角色授权不扩展到 tenant membership
12 space 管理要求 operator 具备 tenant + space membership（Q5）
13 初始 space membership（首位管理员）属 Control Plane / Bootstrap，不作 runtime API
14 target space member 必须已属 target tenant
15 platform_admin 是显式平台授权，永远不作 fallback elevation
16 既有 canonical authorization 保持唯一授权引擎
17 resource lookup 必须遵守 tenant / space scope
18 P17 无 migration
19 P17 无新 runtime privilege
20 Production Event Allowlist 保持 EMPTY
```

授权调用形态（实现事实）：

```text
operation → (resource_type = member, action = read|admin)
resource  = canonical membership-collection resource
            tenant collection : (tenant_id=T, space_id = NULL)
            space  collection : (tenant_id=T, space_id = S)
subject   = 已认证 actor（USER）+ 其 membership-derived roles（既有 SubjectResolver）
engine    = services/authorization.AuthorizationService（唯一引擎；无第二套）
```

补充说明（既有 canonical 语义 · 非 P17 新增）：

```text
· core.permission.scope.scope_covers 冻结语义：TENANT scope 的 grant 覆盖该 tenant 内的资源，
  包含该 tenant 的 space-scoped 资源。因此「同时具备 tenant+space membership 且 tenant 角色
  带 member.admin」的 operator 可以管理该 tenant 内 space 的成员（符合 Q5 双成员资格要求）。
· 该结论不破坏 Q4：跨 tenant 一律 DENY；缺少 space membership 仍一律 DENY（见 N5 / Q5）。
· 本说明记录既有语义在 P17 场景下的表现，不构成新的 permission inheritance。
```

**END OF P17 IDENTITY / TENANT / SPACE RUNTIME IMPLEMENTATION CONTRACT（RULES AUTHORITY · 派生自附录 W + 附录 X）**
