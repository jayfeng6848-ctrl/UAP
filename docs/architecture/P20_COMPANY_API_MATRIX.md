# P20 COMPANY API MATRIX（FROZEN · PDL 附录 AG · 未实现）

```text
性质 = Endpoint → Use Case → Permission → Action → Resource Type → Audit Action 的单一映射表
口径 = permission / action 取自 0019 冻结的 11 条键；审计 action 取自已实现的 service（实测）
作用域 = tenant_id 一律来自 path（形态 B）；授权目标 = tenant 级集合资源（D-P20D-02）
```

## 1. Employee

| # | Endpoint（形态 B） | Use Case | Permission | Action | Resource Type | 审计 action | 成功 | 主要拒绝 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | POST `/company/tenants/{t}/employees` | create_employee | `company_employee.create` | create | company_employee | `company_employee.create` | 201 | 403 未授权/未投影 · 409 工号冲突 · 422 形状非法 |
| E2 | GET `/company/tenants/{t}/employees` | list_employees | `company_employee.list` | list | company_employee | —（读取不写审计） | 200 | 403 · 422 limit 越界 |
| E3 | GET `/company/tenants/{t}/employees/{id}` | get_employee | `company_employee.read` | read | company_employee | — | 200 | 403 · 422/404 未找到（含跨租户不可见） |
| E4 | PATCH `/company/tenants/{t}/employees/{id}` | update_employee | `company_employee.update` | update | company_employee | `company_employee.update` | 200 | 403 · 409? · 422 无字段/未找到 |
| E5 | POST `/company/tenants/{t}/employees/{id}/suspend` | suspend_employee | `company_employee.update` | update | company_employee | `company_employee.suspend` | 200 | 403 · 409 生命周期冲突 |
| E6 | POST `/company/tenants/{t}/employees/{id}/terminate` | terminate_employee | `company_employee.update` | update | company_employee | `company_employee.terminate` | 200 | 403 · 409 生命周期冲突（terminated 终态） |

## 2. Assignment

| # | Endpoint（形态 B） | Use Case | Permission | Action | Resource Type | 审计 action | 成功 | 主要拒绝 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | POST `/company/tenants/{t}/assignments` | create_assignment | `company_assignment.create` | create | company_assignment | `company_assignment.create` | 201 | 403 · 409 有效分配已存在 · 422 角色非法 · 422/404 员工或空间不可见 · 409 空间非 active |
| A2 | GET `/company/tenants/{t}/assignments` | list_assignments | `company_assignment.list` | list | company_assignment | — | 200 | 403 · 422 limit 越界 |
| A3 | GET `/company/tenants/{t}/assignments/{id}` | get_assignment | `company_assignment.read` | read | company_assignment | — | 200 | 403 · 422/404 未找到 |
| A4 | PATCH `/company/tenants/{t}/assignments/{id}` | update_assignment | `company_assignment.update` | update | company_assignment | `company_assignment.update` | 200 | 403 · 409 已 ended · 422 角色非法 |
| A5 | POST `/company/tenants/{t}/assignments/{id}/end` | end_assignment | `company_assignment.update` | update | company_assignment | `company_assignment.end` | 200 | 403 · 409 生命周期冲突 |

## 3. 未暴露能力（冻结保留项）

```text
company_employee.delete · company_assignment.delete  → 无端点（D-P20D-03 RESERVED · 无物理删除）
company_employee.admin                                → 无端点（D-P20D-04 RESERVED）
无 DELETE / PUT（整体替换）/ 批量 / 导入导出端点
无 admin 命名空间端点（未来若需要 → 新 Decision）
```

## 4. 授权调用形态（每端点一致）

```text
Subject      = 认证 actor（identity_id = users.id · subject_type = USER · actor_id 同值）
Action       = 上表 Action（resource_type = 上表 Resource Type）
Resource     = ResourceRef(type=<resource_type>, id=<tenant 集合资源 id>, tenant_id=<path tenant>)
tenant_id    = path 中的 {tenant_id}（绝不来自 session/header）
决策         = 唯一引擎 AuthorizationService；非 ALLOW ⇒ 403
资源缺失     = 403（RESOURCE_NOT_PROVISIONED 同族 · 不自动创建 · G-API-05）
```

## 5. 与 P18/P17 命名空间对照

```text
P17 runtime（actor 自身的 tenant/space 视图）: /tenants · /tenants/{id}/spaces · 成员管理
P18 control plane（结构生命周期·平台作用域） : /control/tenants · /control/spaces · /lifecycle
P20 company（业务组织数据·租户作用域）       : /company/tenants/{tenant_id}/employees · assignments
⇒ 三个命名空间互不复用，Company 不进入 /control，也不进入 P17 runtime 前缀
```

**END OF P20 COMPANY API MATRIX（11 端点 · 8 条审计 action · 3 项保留能力无端点 · 每端点 1 次 canonical 授权；2026-10-02）**
