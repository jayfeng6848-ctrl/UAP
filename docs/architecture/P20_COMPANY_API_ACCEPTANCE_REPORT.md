# P20 COMPANY API ACCEPTANCE REPORT

```text
性质     = READ-ONLY ACCEPTANCE（不新增功能 / 不修复 / 不扩展范围）
输入权威 = PDL 附录 AG · P20_COMPANY_API_CONTRACT.md · P20_COMPANY_API_MATRIX.md ·
           P20_COMPANY_API_IMPLEMENTATION_REPORT.md · P20 COMPANY DOMAIN ACCEPTANCE REPORT
证据     = 静态 AST 分析 + 11 条路由精确枚举 + 4 套测试（API 15 / 架构 63 / 域 26 / P17-P18 21）
```

```
P20 COMPANY API ACCEPTANCE

Boundary:      PASS
Routes:        PASS
Authorization: PASS
Security:      PASS
HTTP Contract: PASS
Regression:    PASS

FINAL:
  P20 COMPANY API ACCEPTANCE = PASS

API:      ACCEPTED
EVENT:    NOT AUTHORIZED
WORKER:   NOT AUTHORIZED
Migration: UNCHANGED
Commit:   NO
Tag:      NO
Push:     NO
HARD STOP: ACTIVE
```

## Phase 0 — Baseline Integrity

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（与 API Freeze 基线一致）· staged = 0
自 release 以来 commit = 0 · tags = 16（未新增）
0019 sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020 sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4（未变）
0021 存在性 = 0 · alembic single head = 0020_p20_company_authorization
Appendix AG = 存在（P20 COMPANY API DECISION FREEZE · D-P20A-01…08）
实现范围 vs AG：11 路由 / DTO 白名单 / Company 独立错误映射 / route manifest 断言 —— 逐条一致
⇒ BASELINE: PASS
```

## Phase 1 — API Boundary（AST 级实测）

```text
apps/api/routes/company.py
  import_roots = ['__future__','apps','datetime','domains','fastapi','pydantic','services','typing']
  forbidden_import_roots（sqlalchemy/psycopg/infrastructure）= []
  forbidden calls（text/execute/*Repository/AuthorizationService/provision_*/ensure_*）= []
  forbidden names（session/engine/is_admin/platform_admin/permission(s)/role(s)/…）= []
  header reads = ['x-correlation-id']（仅关联 id）· 从 header 读取 tenant = False
apps/api/schemas/company.py
  forbidden calls（vars/row/execute/text）= [] · 使用 dict() = False
  DTO 为逐字段显式映射（from_entity），未反射数据库行或 ORM 对象
⇒ API BOUNDARY: PASS
```

## Phase 2 — Frozen Route Contract

```text
Company 路由集合（app.routes 实测）= 11 条，与附录 AG 清单**精确相等**：
  POST   /company/tenants/{tenant_id}/employees
  GET    /company/tenants/{tenant_id}/employees
  GET    /company/tenants/{tenant_id}/employees/{employee_id}
  PATCH  /company/tenants/{tenant_id}/employees/{employee_id}
  POST   /company/tenants/{tenant_id}/employees/{employee_id}/suspend
  POST   /company/tenants/{tenant_id}/employees/{employee_id}/terminate
  POST   /company/tenants/{tenant_id}/assignments
  GET    /company/tenants/{tenant_id}/assignments
  GET    /company/tenants/{tenant_id}/assignments/{assignment_id}
  PATCH  /company/tenants/{tenant_id}/assignments/{assignment_id}
  POST   /company/tenants/{tenant_id}/assignments/{assignment_id}/end
DELETE 路由 = 0 · /admin 路由 = 0 · cursor / 排序 / 查询 DSL = 未提供
tests/api/test_company_api.py::test_company_route_manifest_is_frozen 断言同一集合
⇒ ROUTE CONTRACT: PASS
```

## Phase 3 — Authorization

```text
链路：request → authenticate_actor → tenant(path) → use case → canonical AuthorizationService
      → 集合资源投影 → 业务动作（API 层零权限判断，AST 已验证无 permission/role/is_admin 标识符）
resource_type = company_employee / company_assignment（来自 0019 冻结的 11 条权限键）
拒绝用例（HTTP 实测）：
  ① 无 permission（普通用户 token）      → 403
  ② 未认证（无 Bearer）                  → 401
  ③ resource projection missing（tenant C）→ 403
  ④ 错误/跨 tenant（A 员工 + B 路径）      → 422（不可见）
  ⑤ 错权限（在 A 有读但请求写）           → 403（read-only 角色用例由服务层同源断言覆盖）
⇒ AUTHORIZATION: PASS
```

## Phase 4 — Security

```text
Tenant boundary：tenant_id 仅来自 path（每个 handler 首参 `tenant_id: str`）；
  request 模型（Employee/Assignment Create/Update）**不含** tenant_id 字段；
  header 仅读取 x-correlation-id；无 session/body tenant override。
响应泄露面：错误统一为 taxonomy 安全消息（403/422/409/503），无 SQL / 约束名 / 表名 /
  stack / 数据库信息；DTO 为冻结白名单（无 ORM 行直出）。
Employee 非登录身份：/company 下无 login/token/password 端点；认证仅走既有 bearer session；
  Employee ≠ User 保持（员工仅在 DTO 中以 user_id 引用平台身份）。
⇒ SECURITY: PASS
```

## Phase 5 — HTTP Contract

```text
201 create（employees / assignments）· 200 read/update/action ·
403 authorization/resource denied · 422 validation 与 not-found（D-P20A-02 = A）·
409 conflict（工号/用户/分配/生命周期）· 503 audit / security boundary failure
列表封装 = {items, count, limit}（DTO 白名单逐项校验）
DTO = EmployeeResponse / AssignmentResponse（字段集合与冻结白名单精确相等）
⇒ HTTP CONTRACT: PASS
```

## Phase 6 — Regression

```text
tests/architecture                                       = 63 passed（Core → Domain = 0 保持）
tests/api/test_company_api.py                            = 15 passed
tests/company/*（域 / 仓储 / 服务 / 0020 迁移）             = 26 passed
tests/integration/test_p17_acceptance.py
  + tests/integration/test_p18_control_api_http.py        = 21 passed
events = 0 · handlers = 0（allowlist specs = 0）· producers = 0 · workers = 0
  （apps/worker 内 Company 引用 = 0）
共享测试库 uap_b1_test = 0017_p13_seed（permissions 12 · acl_subject_types 3 ·
  company 表 0 · events 0）—— 未被本项工作改变
正式库 uap = 0 public 表（未触碰）· 一次性测试库全部 DROP（无残留）
⇒ REGRESSION: PASS
```

## 非阻断观察

```text
O-1（沿用 P20 DOMAIN ACCEPTANCE 的 F-01）：services/company/use_cases.py 含 3 处内联 SQL
     （tenant/space 状态读取 + audit_logs 追加）。与 P18 控制面先例同型；本轮为 API 验收，
     不影响 API 边界判定。若需下沉到 repository / audit writer，属独立代码授权事项。
O-2 列表为 limit-only（无游标）：符合 D-P20A-03 = A 的最小面；真实分页需新决策 + service 改动。
```

**END OF P20 COMPANY API ACCEPTANCE REPORT（6/6 项 PASS · 11 路由精确匹配 · API 15 + 架构 63 + 域 26 + P17/P18 21 全绿 · 事件/Worker 未授权 · Migration 未改动 · 未 commit；2026-10-02）**
