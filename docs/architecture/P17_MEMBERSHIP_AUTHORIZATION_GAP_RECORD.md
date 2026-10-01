# P17 — MEMBERSHIP AUTHORIZATION DESIGN GAP RECORD

```text
登记日期      = 2026-10-01
阶段          = P17 IMPLEMENTATION（Wave 3 · Authorization Integration）
状态          = RESOLVED BY HUMAN DECISION（2026-10-01 · 同日闭合；原始 observation 保留）
分类          = DESIGN GAP（不是代码缺陷 · 不是环境缺陷 · 不是历史回归）
性质          = 已由 Human Decision 裁定为 OPTION A；本轮据此完成 Wave 3–6
基线          = UAP-V0.1.15-P16-AGENT-RUNTIME（HEAD = origin/main = 42a4f61c…）
依据          = P17 IMPLEMENTATION 指令 §19 / §20 / §84（STOP-2 · STOP-3）
                + P17 Implementation Contract §2 不变式 12/13/14/15/16
                + PDL 附录 W（P17-D01…D14 · OQ-01…08）
裁定          = PDL 附录 X（P17 AUTHORIZATION GAP RESOLUTION）· P17-AUTH-01…Q5
```

---

## 0. RESOLUTION（Human Decision · 2026-10-01）

```text
P17 Authorization Model = OPTION A（复用既有 12 canonical permissions · 不扩展 P13）

Q1 = Control Plane / Bootstrap 在 provisioning 时创建 canonical resources rows
Q2 = admin 单动作（read/list → member.read ；create/update/delete → member.admin）
Q3 = platform_admin + tenant-scoped role + space-scoped role（各自满足 scope 条件）
Q4 = 不互通（tenant 角色 ≠ space 成员管理授权；反之亦然）
Q5 = YES（space membership 管理要求 operator 同时具备 target tenant + target space membership）

F-P17-I-01 = RESOLVED BY HUMAN DECISION（CRUD → 单一 member.admin，非缺陷）
F-P17-I-02 = RESOLVED BY ARCHITECTURAL DECISION（resource provisioning = control-plane invariant）
F-P17-I-03 = RESOLVED BY PROVISIONING MODEL（既有 role_permissions 由 control plane 赋值）
```

实现结果（本轮实测）：

```text
canonical permission count = 12 → 12        （未新增 permission）
P17 migration               = NONE          （未新增 migration · schema 未变）
uap_runtime grants          = 56 → 56       （P17 privilege delta = 0）
resource projection         = services/control_plane/provisioning.py（tenant/space/member-collection/agent）
runtime self-provisioning    = 0（uap_runtime 对 tenants/spaces 无写权限 ⇒ 物理不可执行）
authorization bridge        = services/identity_runtime/authorization.py → 既有 AuthorizationService
```

保留的原始 observation（未删除 · 未改写）：

```text
· resources = 0 行（当时无任何 provisioning 路径）
· permissions = 12 行，member 仅 member.read / member.admin
· 除 platform_admin 外无任何 role_permissions
· 探针实测：无 resources 行 ⇒ 一律 DENY（resource:unknown resource）
  —— 该事实现已成为正式安全测试（resource absence ⇒ fail closed）
```

---

## 1. 触发的问题

指令 §20 冻结了 membership 授权的操作映射：

```text
Tenant Membership:  GET/List → read/list · POST → create · PATCH → update · DELETE → delete
Space  Membership:  同上（read/list/create/update/delete）
resource mapping 必须复用现有权限模型
如果发现当前 permission/resource model 无法表达 membership authorization: STOP
不要: GRANT · seed new permission · modify P13 seed · add ACL row · hard-code platform_admin
```

本轮按该条做了**取证**（见 §3）。结论：

```text
当前冻结的 canonical permission / resource model 无法表达 membership authorization
⇒ STOP-2（permission system 无法表达 membership authorization）
⇒ STOP-3（需要 new permission seed / new ACL write / new resource row 才能表达）
```

---

## 2. Findings

### F-P17-I-01 — Canonical permission registry 无 member 写权限

```text
Classification = RELEASE BLOCKER（P17 membership 写路径不可授权）
Root cause     = P13 canonical registry 只有 member.read / member.admin 两项 member 权限；
                 不存在 member.create / member.update / member.delete / member.list
Impact         = §20 的 POST→create / PATCH→update / DELETE→delete 无任何可授权事实；
                 即使 actor 持有 member.admin，action=create/update/delete 仍为 default-deny
不可自愈       = 新增权限 = 修改 P13 seed（§20 明令禁止；OQ-06 SYSTEM IMMUTABLE）
```

### F-P17-I-02 — 被治理对象在 resources 模型中没有表示

```text
Classification = RELEASE BLOCKER（membership 授权对所有人一律 DENY）
Root cause     = canonical AuthorizationService 的资源解析以 resources 行为权威
                 （services/authorization/resources.py: ResourceResolver.resolve →
                  repository.get_resource(id)；缺失即 ResourceResolutionError → DENY）；
                 tenants / spaces / membership collection 均无 resources 行，
                 且平台无任何 provisioning 路径创建它们（实测 resources = 0 行）
Impact         = 即便 actor 合法持有 member.admin，canonical 决策结果仍是
                 DENY / reason = "resource:unknown resource"
                 ⇒ P17 membership API 对任何调用者（含 platform_admin）都无法成功
不可自愈       = 补 resources 行 = 新的写面（resource mirror）；§20 禁止 add ACL row，
                 同类自我授权一律禁止；资源镜像属 provisioning/control-plane 决策
```

### F-P17-I-03 — 除 platform_admin 外没有任何 role_permissions（观察项 · 非独立阻断）

```text
Classification = OBSERVATION（影响授权可用性，不是实现缺陷）
Evidence       = P13 seed 只写入 platform_admin × 12 allow；role_permissions 总行数 = 12
Impact         = 即便 F-P17-I-02 解决，也只有 platform_admin（PLATFORM scope）能通过 RBAC；
                 tenant/space 角色的成员管理授权必须由新的 grant 决策产生
注意           = §20 禁止 hard-code platform_admin；本条必须由决策显式裁定，
                 不得以「反正只有 platform_admin 能过」作为实现理由
```

---

## 3. 取证（可复现 · 一次性探针库 · 不留痕）

探针：`uap_p17_probe`（`CREATE DATABASE … OWNER uap_migrator` → `alembic upgrade head`
→ 官方 `scripts.privileges.materialize()`），断言以 `uap_runtime` 身份执行，运行后即 DROP。
探针造出最有利的条件：actor 拥有 tenant A 的 active tenant membership，
其 tenant role 绑定 `member.admin` + `member.read` + `tenant.admin`（三者均为 P13 既有权限）。

```text
--- probe 1: canonical registry shape ---
permissions_rows=12
member_permissions=['member.admin', 'member.read']
resources_rows=0

--- probe 2: membership administration WITHOUT a resources row ---
action=read    effect=DENY   reason=resource:unknown resource
action=create  effect=DENY   reason=resource:unknown resource
action=update  effect=DENY   reason=resource:unknown resource
action=delete  effect=DENY   reason=resource:unknown resource
action=admin   effect=DENY   reason=resource:unknown resource

--- probe 3: same question AFTER inserting the missing resources row ---
action=read    effect=ALLOW  reason=granted        # member.read
action=admin   effect=ALLOW  reason=granted        # member.admin
action=create  effect=DENY   reason=default-deny   # 无 member.create
action=update  effect=DENY   reason=default-deny   # 无 member.update
action=delete  effect=DENY   reason=default-deny   # 无 member.delete

--- probe 4: cross-tenant attempt with the same resource row ---
cross-tenant effect=DENY reason=cross-tenant       # 隔离性本身完好
```

冻结基线库实测（`uap_b1_test`，本轮前后一致）：

```text
permissions = 12（tenant.read/admin · space.read/admin · member.read/admin ·
                resource.read/update/delete · agent.execute · tool.execute · audit.read）
resources   = 0 行 · tenants = 0 · spaces = 0 · roles = 1（platform_admin）
role_permissions = 12（全部属 platform_admin）
```

结论：探针 2 是**平台现状**下的真实结论（不是权限不足、不是配置漂移）——
canonical 路径对 membership 治理对象一律 `resource:unknown resource`。

---

## 4. Impact（本轮到哪一步为止）

```text
Wave 0 基线/清单                  = PASS
Wave 1 Tenant/Space/Membership 仓储 = PASS（含 scope 强制 · 无通用 get_by_id）
Wave 2 Context Resolver           = PASS（真实 DB 证据 · 11/11）
Wave 3 Authorization Integration  = BLOCKED（本记录）
Wave 4 Membership mutation + audit = 载体已实现且原子性已取证（5/5）；但
                                     **未接入任何 use-case / API**（缺少前置授权门）
Wave 5 API                        = NOT STARTED（依赖 Wave 3）
Wave 6 Agent Integration          = NOT STARTED（依赖 Wave 3）
Wave 7 Authorization 相关测试      = NOT STARTED（依赖 Wave 3）
Wave 7 解析/仓储相关测试            = PASS（单元 26 + 集成 11 + 原子性 5）
Wave 8 Evidence                   = 部分完成（P17_IMPLEMENTATION_EVIDENCE.md）
```

安全影响评估：

```text
authorization bypass      = 0（无新路径被引入；未绕过 canonical）
cross-tenant 隔离          = 保持 DENY（探针 4 · 集成 N1/N2/N6/N7）
新 runtime privilege       = 0
新表 / 新 migration        = 0
Production Event Allowlist = EMPTY · Handlers = 0
Core → Domain              = 0
```

即：本轮没有引入安全弱化；被阻断的是**功能交付**，不是安全性。

---

## 5. 需要 Human Decision 的选项

> **已裁定：选项 A（2026-10-01）。** 下列 A/B/C 与 Q1–Q5 保留为历史决策输入。
> 实际采用的映射、provisioning 归属与 scope 规则见 §0 与 PDL 附录 X。

### 选项 A（推荐）— 复用既有 12 权限 + 明确资源镜像不变式

```text
映射：read/list  → action read   （member.read / tenant.read / space.read）
      create/update/delete → action admin（member.admin / tenant.admin / space.admin）
前提：裁定「每个 tenant / space 在被 provisioning 时必须同时拥有对应 resources 行」
      （resource_type ∈ {tenant, space, member}），并明确由谁创建（control-plane / bootstrap）
代价：无新权限 · 无新表 · 无 migration · 无新 runtime privilege
代价：§20 的 create/update/delete 映射被 admin 取代 —— 需 Human 明确批准该等价
风险：把「管理成员」收敛为单一 admin 动作，无法区分 read-only 管理员与可写管理员
```

### 选项 B — 扩展 P13 canonical permission registry

```text
新增 member.list / member.create / member.update / member.delete（+ 资源镜像定义）
代价：修改 P13 seed（新 migration）· 触碰 OQ-06 SYSTEM IMMUTABLE · 需重开 P17-D13（migration = NONE）
收益：保留 §20 的 CRUD→动作一一映射，粗细度更好
```

### 选项 C — 本轮只交付只读（tenant/space/member 读），membership 写延后

```text
代价：与 P17-D10 = C（membership = READ + WRITE）冲突 ⇒ 同样需要 Human 修订 D10
收益：可在零新决策的前提下先把「上下文 + 只读面」交付并验收
```

---

## 6. 未决问题（决策时必须一并回答）

```text
Q1 谁在 provisioning 时创建 tenant/space/member 的 resources 行？（control-plane？bootstrap？）
Q2 membership 管理的授权动作是 admin 单动作，还是 CRUD 四动作（需扩展 registry）？
Q3 允许哪些主体管理 member？（platform_admin only / tenant scoped role / space scoped role）
Q4 若采用 tenant/space scoped 管理，置入 tenant 角色还是 space 角色？两者权限是否互通？
Q5 space membership 管理是否需要同时满足 tenant role + space role（D04 = C 的双层语义）？
```

---

**END OF P17 MEMBERSHIP AUTHORIZATION DESIGN GAP RECORD（F-P17-I-01 / I-02 / I-03 = RESOLVED BY HUMAN DECISION（OPTION A · Q1…Q5）· STOP-2 + STOP-3 解除 · 未执行 GRANT / seed / ACL / migration / commit / tag / push；2026-10-01）**
