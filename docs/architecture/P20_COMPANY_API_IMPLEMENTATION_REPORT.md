# P20 COMPANY API IMPLEMENTATION REPORT

```yaml
Implementation = PASS

Routes:        11/11（Appendix AG 冻结清单 · 精确匹配断言）
DTO:           EmployeeResponse / AssignmentResponse（显式白名单 · D-P20A-06 = C）
Authorization: 端点 100% 经 use case 的 canonical 引擎；无权限判断落在传输层
Security:      tenant 入 path · 统一 403 · 无 DELETE/admin 端点 · 无事件
Tests:         tests/api/test_company_api.py = 15 passed
Regression:    tests/architecture 63 passed · P17/P18 API 21 passed · Company 域/服务 26 passed

API:    IMPLEMENTED（Company 命名空间）
Event:  NOT IMPLEMENTED（allowlist EMPTY · events = 0）
Worker: NOT IMPLEMENTED

Migration touched: NO（0019 / 0020 哈希未变 · 无 0021）
Permission changed: NO        Role changed: NO

Commit: NO   Tag: NO   Push: NO
HARD STOP: ACTIVE
```

## 1. Phase 0 — Implementation Gate（只读实测）

```text
git rev-parse HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（与 API Freeze 基线一致）· staged = 0
git diff --check = 仅既有 CRLF 警告（历史文件）
0019 sha256 = 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020 sha256 = 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4（未变）
0021 存在性 = 0（未创建）· alembic heads = 0020_p20_company_authorization（单 head）
Appendix AG = 存在（P20 COMPANY API DECISION FREEZE）
允许区域内改动：apps/api/** · tests/api/**（新增 apps/api/schemas · apps/api/errors · tests/api）
禁止区域零改动：domains/company/** · services/company/** · core/auth/** · 授权引擎 · migrations · events
```

## 2. Phase 1–3 — 交付物

```text
apps/api/schemas/company.py        DTO：EmployeeCreateRequest / EmployeeUpdateRequest /
                                   EmployeeResponse / EmployeeListResponse /
                                   AssignmentCreateRequest / AssignmentUpdateRequest /
                                   AssignmentResponse / AssignmentListResponse
                                   字段白名单常量 EMPLOYEE_FIELDS / ASSIGNMENT_FIELDS
                                   （逐字段显式映射，禁止 vars()/dict(row) 直出）
apps/api/errors/company.py         Company 命名空间错误映射（COMPANY_CLASS / classify_company /
                                   translate_company）：复用 Core HTTP_STATUS，不改 Core taxonomy
apps/api/routes/company.py         11 个端点（transport only）
apps/api/main.py                   router 注册（唯一既有文件改动）
tests/api/test_company_api.py      HTTP 层验收（15 项）
```

## 3. Phase 2 — 路由（与附录 AG 逐条一致）

```text
POST   /company/tenants/{tenant_id}/employees                       201  EmployeeResponse
GET    /company/tenants/{tenant_id}/employees                       200  EmployeeListResponse
GET    /company/tenants/{tenant_id}/employees/{employee_id}         200  EmployeeResponse
PATCH  /company/tenants/{tenant_id}/employees/{employee_id}         200  EmployeeResponse
POST   /company/tenants/{tenant_id}/employees/{employee_id}/suspend 200  EmployeeResponse
POST   /company/tenants/{tenant_id}/employees/{employee_id}/terminate 200 EmployeeResponse
POST   /company/tenants/{tenant_id}/assignments                     201  AssignmentResponse
GET    /company/tenants/{tenant_id}/assignments                     200  AssignmentListResponse
GET    /company/tenants/{tenant_id}/assignments/{assignment_id}     200  AssignmentResponse
PATCH  /company/tenants/{tenant_id}/assignments/{assignment_id}     200  AssignmentResponse
POST   /company/tenants/{tenant_id}/assignments/{assignment_id}/end 200  AssignmentResponse

查询面（D-P20A-03 = A）：employees = status + limit(1..200)；
                        assignments = employee_id / space_id / status + limit(1..200)
无 DELETE / 无 admin / 无 cursor / 无排序 / 无查询 DSL
```

## 4. Phase 4 — 错误映射（固定表实测）

```text
403  AUTHORIZATION_DENIED · RESOURCE_NOT_PROVISIONED
422  INVALID_INPUT · PAGINATION_INVALID · EMPLOYEE_NOT_FOUND · ASSIGNMENT_NOT_FOUND · SPACE_NOT_FOUND
409  EMPLOYEE_NO_CONFLICT · EMPLOYEE_USER_CONFLICT · ASSIGNMENT_CONFLICT ·
     EMPLOYEE_LIFECYCLE_CONFLICT · ASSIGNMENT_LIFECYCLE_CONFLICT · TENANT_NOT_ACTIVE · SPACE_NOT_ACTIVE
503  AUDIT_UNAVAILABLE（persistence）· CONSISTENCY_VIOLATION（security_boundary）
请求体校验失败由 FastAPI 直接 422（与 D-P20A-02 = A 一致）
任何响应都不含 SQL / 约束名 / 堆栈 / 数据库名 / 存在性线索
```

## 5. Phase 5 — Route Manifest（D-P20A-08 = A）

```text
tests/api/test_company_api.py::test_company_route_manifest_is_frozen
  → 对 /company/* 做**精确集合等值**断言（11 条，无多无少）+ 无 DELETE 方法 + 无 /admin 端点
既有 P17 frozen route inventory 断言保持原样且仍通过（其性质为子集断言）
domain manifest 未改动；Company 路由不需要新的 manifest 字段
```

## 6. Phase 6 — API 测试（15 passed）

```text
Authorization：201 + 冻结 DTO / 无授权 403 / 匿名 401 / 错误权限 403 / 缺投影 403
Tenant Isolation：跨租户 employee → 422（不可见）· 跨租户 space assignment → 422
Contract：未知 employee → 422 · 非法工号 → 422 · 重复工号 → 409（一致重放仍 201 同 id）·
          生命周期 200/200/409 · PATCH 200 · 列表封装 {items,count,limit} · limit 0/201 → 422
Assignment：create 201 / read 200 / list 200（过滤）/ PATCH 200 / end 200 / end 后 PATCH 409
Route manifest：11 条精确匹配
Security：无 DELETE 端点 · 无 admin 端点 · events = 0
```

## 7. Phase 7 — 回归门禁

```text
tests/api/test_company_api.py                     = 15 passed
tests/architecture                                = 63 passed
tests/integration/test_p17_acceptance.py
  + tests/integration/test_p18_control_api_http.py = 21 passed
tests/company/*（域 / 仓储 / 服务 / 0020 迁移）     = 26 passed
events = 0 · handlers = 0 · producers = 0 · allowlist EMPTY
workers = 0（未创建 Company worker）
常驻库未变：uap_b1_test = 0017_p13_seed（perms 12 · company 0 · events 0）· 正式库 uap = 0 public 表
一次性测试库全部 DROP（uap_p20_api_test 等，无残留）
```

## 8. 边界与停止点

```text
未修改 domains/company/** · services/company/** · core/** · 授权引擎 · migrations ·
permission / role / role grant / resources 数据 · 未新增 event / producer / handler / worker ·
未实现商业 Runtime / UI · 未 commit / tag / push
```

**END OF P20 COMPANY API IMPLEMENTATION REPORT（11 端点 + 冻结 DTO + Company 独立错误映射 · API 15 passed / 架构 63 passed / 既有 API 21 passed / 域 26 passed · 事件与 Worker 未实现 · 未 commit；2026-10-02）**
