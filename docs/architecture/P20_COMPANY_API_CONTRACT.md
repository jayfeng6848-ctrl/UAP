# P20 COMPANY API CONTRACT（FROZEN · PDL 附录 AG · 未实现）

```text
性质     = API CONTRACT（冻结契约；不是实现、不是授权）
状态     = FROZEN（PDL 附录 AG · D-P20A-01…08）；实现需另立 P20 COMPANY API IMPLEMENTATION AUTHORIZATION
基线     = P20 COMPANY API PREP 的 F1–F12 + Company service 11 个已实现 use case
分层     = HTTP Adapter → Service Use Case → Domain（下层永不反向依赖传输层）
```

## 1. 分层与边界

```text
允许：
  apps/api/routes/company.py      传输层：认证、解析 path/query/body、调用一个 use case、映射结果
  apps/api/error_mapping.py       注册 CompanyError → 八类 taxonomy（实现轮新增映射项）

禁止：
  * domains/company/** 出现 FastAPI / HTTP / request / response 概念（域纯度守卫已强制）
  * 传输层出现 SQL、授权判定、角色比较、is_admin 捷径
  * 传输层直接调用 repository（必须经 use case）
  * 任何新认证体系（API token / company login / employee login）

依赖方向：apps → services（use case）→ domains（契约）→ core；apps 不得被下层引用
```

## 2. 端点设计（两个候选形态 · 见 D-API-01）

> **冻结结果（附录 AG · D-P20A-01 = B）**：采用形态 B —— `/{domain}/tenants/{tenant_id}/...`，
> `tenant boundary = API path boundary`。形态 A 未被采纳，仅保留为历史设计记录。

```text
形态 A（本门指令原提案 · 无 tenant 于 path）：
  POST /company/employees · GET /company/employees · GET /company/employees/{id} ·
  PATCH /company/employees/{id} · POST /company/employees/{id}/suspend ·
  POST /company/employees/{id}/terminate ·（assignments 同型）
  ⇒ 需要另行定义 tenant 上下文来源；与 F2「目标作用域来自 path」相冲突

形态 B（建议 · 与 F2 及 P18 `/control/tenants/{tenant_id}/spaces/...` 同型）：
```

| # | 方法 | 路径 | use case | 成功状态 |
| --- | --- | --- | --- | --- |
| E1 | POST | `/company/tenants/{tenant_id}/employees` | create_employee | 201 |
| E2 | GET | `/company/tenants/{tenant_id}/employees` | list_employees | 200 |
| E3 | GET | `/company/tenants/{tenant_id}/employees/{employee_id}` | get_employee | 200 |
| E4 | PATCH | `/company/tenants/{tenant_id}/employees/{employee_id}` | update_employee | 200 |
| E5 | POST | `/company/tenants/{tenant_id}/employees/{employee_id}/suspend` | suspend_employee | 200 |
| E6 | POST | `/company/tenants/{tenant_id}/employees/{employee_id}/terminate` | terminate_employee | 200 |
| A1 | POST | `/company/tenants/{tenant_id}/assignments` | create_assignment | 201 |
| A2 | GET | `/company/tenants/{tenant_id}/assignments` | list_assignments | 200 |
| A3 | GET | `/company/tenants/{tenant_id}/assignments/{assignment_id}` | get_assignment | 200 |
| A4 | PATCH | `/company/tenants/{tenant_id}/assignments/{assignment_id}` | update_assignment | 200 |
| A5 | POST | `/company/tenants/{tenant_id}/assignments/{assignment_id}/end` | end_assignment | 200 |

```text
不提供：DELETE（reserved 权限 · 无物理删除）· admin 端点（reserved）· 批量端点 · 导入导出
生命周期动作使用子路径动词（/suspend · /terminate · /end），与 P18 `/lifecycle` 先例一致
tag = ["company"]；前缀 = `/company`（专用命名空间，不进入 P17 runtime 命名空间）
```

## 3. 请求 / 响应形状

```text
E1 POST body：
  { "employee_no": str(1..64 · 冻结形状) · "display_name": str(1..) ·
    "title": str | null · "hired_at": datetime | null }
  201 → EmployeeView（§4）
E4 PATCH body：{ "display_name": str | null · "title": str | null }（至少一项；两项皆空 ⇒ 422）
E5/E6/A5 POST body：无（使用子路径动词语义）→ 200 EmployeeView / AssignmentView

A1 POST body：{ "employee_id": uuid · "space_id": uuid · "assignment_role": "member" | "lead" }
  201 → AssignmentView
A4 PATCH body：{ "assignment_role": "member" | "lead" } → 200 AssignmentView

E2 GET query：?status=active|suspended|terminated&limit=1..200（默认 50）
A2 GET query：?employee_id=&space_id=&status=active|ended&limit=1..200
列表响应：{ "items": [ ... ], "count": <int>, "limit": <int> }（沿用 F5 封装；无 cursor，见 G-API-03）
```

## 4. 响应暴露面（见 D-API-04）

```text
EmployeeView（建议冻结字段白名单）：
  employee_id · tenant_id · employee_no · display_name · title · status ·
  user_id（可空）· hired_at · terminated_at · created_at · updated_at
AssignmentView：
  assignment_id · tenant_id · employee_id · space_id · assignment_role · status ·
  started_at · ended_at · created_at · updated_at

不含：任何凭据 / 令牌 / 审计内部字段 / 数据库行对象 / 其他租户数据 / 关联平台身份的邮箱等
employee 视图不内联 user 详情（Employee ≠ User；跨实体展开需要新的决策）
```

## 5. 授权映射（完整矩阵见 P20_COMPANY_API_MATRIX.md）

```text
每个端点 = 1 个 use case = 1 次 canonical 授权调用（API 层不做任何权限判断）
resource_type = company_employee / company_assignment（tenant 级集合资源）
permission 由 use case 决定（read / list / create / update 四类动作）
API 不得出现：if user.is_admin / if actor.roles / 手写 permission 字符串比较
未授权 ⇒ 403（taxonomy "authorization"）；缺投影 ⇒ 403（与 P17 RESOURCE_NOT_PROVISIONED 同族，见 G-API-05）
```

## 6. 错误契约

| 服务错误（services.company.ErrorCode） | taxonomy 类 | HTTP | 说明 |
| --- | --- | --- | --- |
| AUTHORIZATION_DENIED | authorization | 403 | 含未授权 / 引擎不可用（fail-closed） |
| RESOURCE_NOT_PROVISIONED | authorization | 403 | 与 P17 同族（不暴露"未投影"细节，G-API-05） |
| INVALID_INPUT / PAGINATION_INVALID | validation | 422 | 请求形状/取值非法 |
| EMPLOYEE_NOT_FOUND / ASSIGNMENT_NOT_FOUND | validation（或新增 not_found·见 D-API-02） | 422（或 404） | 跨租户亦返回同类（不泄露存在性） |
| EMPLOYEE_NO_CONFLICT / EMPLOYEE_USER_CONFLICT / ASSIGNMENT_CONFLICT | conflict | 409 | 自然键冲突 |
| EMPLOYEE_LIFECYCLE_CONFLICT / ASSIGNMENT_LIFECYCLE_CONFLICT | conflict | 409 | 非法或并发状态转换 |
| TENANT_NOT_ACTIVE / SPACE_NOT_ACTIVE / SPACE_NOT_FOUND | conflict / validation | 409 / 422 | 与 P18 语义一致 |
| AUDIT_UNAVAILABLE / CONSISTENCY_VIOLATION | persistence / security_boundary | 503 | 模糊化，绝不回显内部细节 |

```text
禁止泄露：SQL 文本 · 约束/触发器名 · 数据库名/用户名/DSN · 堆栈 · 存在性线索
实现轮需在 apps/api/error_mapping.py 注册 CompanyError 的映射（当前未注册 · 见 G-API-04）
```

## 7. 认证边界（Phase 7）

```text
复用：apps.api.dependencies.bearer_token + services.use_cases.authenticate_actor
      （Wave 2 会话认证；返回 actor.user_id / actor.subject_type）
context：actor 的 tenant 作用域来自 **path 的 tenant_id**（F2）；API 不信任 header/session 推断
禁止：新增 API token 体系 · Company/Employee 登录 · 员工自助认证 · 把 employee_id 当作 actor
Employee ≠ User 保持：员工不是认证主体（D-P20D-05 / F12）
```

## 8. 事件边界（Phase 8）

```text
API mutation 不发布任何事件：不写 events、不注册 producer、不触发 handler
保持：events = 0 · handlers = 0 · producers = 0 · Production Allowlist = EMPTY（P19-D01 OPTION D 不变）
未来若需事件：必须另行通过 P19 / P20 Event Decision
```

## 9. 数据库与事务边界

```text
依赖 = `get_database`（runtime identity · uap_runtime），不使用 P18 的 control identity
事务 = 由 use case 内的 RuntimeDatabase.transaction 拥有；handler 不提交、不回滚
handler = 认证 → 取一个 use case → 序列化结果（UUID/datetime → str/isoformat，沿用 _clean 先例）
```

## 10. 非目标（本轮与实现轮均不含）

```text
UI · Worker / Scheduler · Event / Producer / Handler · 批量与导入导出 ·
DELETE 端点 · admin 端点（reserved 权限）· 员工自助端点 · 新的认证或令牌体系 ·
OpenAPI 客户端生成 · 速率限制/配额 · 跨实体展开（employee→user 详情）
```

## 11. 实现轮所需改动清单（供授权参考 · 本轮不执行）

```text
① apps/api/routes/company.py（11 个端点 · 传输层）
② apps/api/main.py 注册 router（或 routes/__init__.py 导出）
③ apps/api/error_mapping.py 注册 CompanyError → taxonomy（G-API-04）
④ tests/company/test_company_api.py（HTTP 层：授权/跨租户/错误码/路由清单）
⑤ 路由清单守卫更新（若沿用 P17 的 frozen scope 断言）
```

**END OF P20 COMPANY API CONTRACT（设计提案 · 11 端点 × 2 形态 · 请求/响应/错误/认证/事件边界齐备 · 未实现 · 待 D-API-01…D-API-08 裁定；2026-10-02）**
