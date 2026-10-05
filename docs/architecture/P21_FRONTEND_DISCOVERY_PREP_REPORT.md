# P21 FRONTEND DISCOVERY / UI ARCHITECTURE PREP REPORT

```yaml
P21 FRONTEND DISCOVERY / UI ARCHITECTURE PREP = PASS

Frontend Exists:        YES — but only a committed STEP-0 skeleton（非产品 UI）
Frontend Location:      apps/frontend/
Framework:              React 18.3.1 + Vite 6.0.5 + TypeScript 5.7.2（package.json 声明 · 未安装/未锁定）
Production Frontend:    NONE
Company UI:             DESIGN ONLY

Frontend Implementation: NOT AUTHORIZED
Company API:             ACCEPTED / UNCHANGED（11 路由）
Event UI:                OUT OF SCOPE
Event Production:        NOT AUTHORIZED
Worker:                  NOT AUTHORIZED
Migration:               NOT AUTHORIZED
Package Installation:    NOT AUTHORIZED

Commit: NO   Tag: NO   Push: NO
HARD STOP: ACTIVE
```

## 1. Executive Summary

```text
本轮为**只读发现**（未安装依赖、未改代码、未改 lockfile、未改 PDL）。

关键发现：
  ① 仓库**确实存在前端**：`apps/frontend/`（5 个文件 · 已在初始提交 72ade9f 中提交）·
     React 18.3.1 + Vite 6.0.5 + TS 5.7.2 + @vitejs/plugin-react 4.3.4（package.json 声明）·
     **无 lockfile / 无 node_modules / 无测试与 lint 工具** · 唯一页面 `src/main.tsx` 仅调用
     `GET /api/v1/meta`（后端确实提供该路由 · meta router prefix="/api/v1" ⇒ 契约一致）
  ② 该前端被仓库文档明确标注为 **skeleton / C-7 FUTURE**（README / ARCHITECTURE /
     P14_RUNTIME_WAVE2_SCOPE / P15_DECISION_COMPLETION_REPORT），且 P15 复核包明确记录
     "C-7 Frontend → 需独立 frontend/API/auth boundary decision（尚未建立 ID）"
  ③ 后端面：**49 条路由**，其中认证 = /identity/onboarding · /identity/authenticate ·
     /sessions · /sessions/refresh · /sessions/logout · /devices/*；**存在 `GET /me`**
     （返回 log-safe 上下文：user/identity/session/device/tenant/space/subject/scope/assurance，
     **不含 permissions/roles**）；P20 Company = 11 路由（accepted）
  ④ **无 CORS 中间件 · 无 StaticFiles 挂载 · docker-compose/Dockerfile 无前端服务与构建步骤**
     ⇒ 生产部署模型（同源/反向代理/静态托管）尚未建立
  ⑤ 无权限查询端点 ⇒ 前端 permission-aware 渲染的数据源 = **Human Decision Required**
  ⑥ 无浏览器可见密钥风险（前端无任何 secret；.env.example 仅后端变量）

⇒ 发现完成；前端栈、目录、租户 URL、认证集成、API client、状态、样式、路由、权限 UI、
  测试、部署共 11 项列为 P21-H01…H11（见 §42），**本轮不冻结任何一项**。
```

## 2. Authority Sources

```text
AGENTS.md · PDL 附录 AC/AD/AE/AF/AG（P20 Company 模块/Schema/OPT-2/Domain/API）·
  附录 AH/AI/AJ/AK（Event 边界：Design→Contract→Qualification→Acceptance，Production 未授权）
docs/architecture/ARCHITECTURE.md · CORE_DOMAIN_MODEL.md · DEPENDENCY_RULES.md ·
  P14_RUNTIME_WAVE2_SCOPE.md · P15_DECISION_COMPLETION_REPORT.md · P15_HUMAN_DECISION_REVIEW_PACKAGE.md ·
  P20_COMPANY_API_CONTRACT.md · P20_COMPANY_API_MATRIX.md · P20_COMPANY_API_ACCEPTANCE_REPORT.md
真实仓库：apps/frontend/** · apps/api/**（路由与中间件实况）· config/settings.py ·
  docker-compose.yml · Dockerfile · .env.example · README.md
```

## 3. Baseline Integrity

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0 · tags = 16（未新增）
工作区 = 35 modified（历次已授权产物 + 历史脏文件，全部保留未清理）+ 154 untracked
git status -- apps/frontend = 空（前端文件**已提交且干净**，不在 dirty 集合中）
0019 / 0020 sha256 未变 · No 0021（本报告不涉及）
⇒ BASELINE: PASS
```

## 4. Frontend Inventory（实测）

```text
候选目录扫描：frontend/ = 无 · web/ = 无 · ui/ = 无 · client/ = 无 · public/ = 无 · static/ = 无
真实发现：apps/frontend/（git 跟踪 5 个文件）
  apps/frontend/README.md
  apps/frontend/index.html
  apps/frontend/package.json
  apps/frontend/src/main.tsx
  apps/frontend/vite.config.ts
node/前端配置文件扫描：仅 apps/frontend/package.json + apps/frontend/vite.config.ts
  **不存在**：pnpm-lock.yaml · package-lock.json · yarn.lock · bun.lock* · tsconfig.json ·
  jsconfig.json · tailwind.config.* · postcss.config.* · eslint.config.* · .prettierrc*
HTML/CSS/JS 资产（非 docs）：apps/frontend/index.html · src/main.tsx · vite.config.ts（无独立 .css）
```

```text
Frontend Exists   = YES（skeleton）
Frontend Location = apps/frontend/
Framework         = React 18（声明 · 未安装/未锁定）
Version           = react ^18.3.1 · react-dom ^18.3.1 · vite ^6.0.5 · typescript ^5.7.2
Package Manager   = 未确定（无 lockfile、无 packageManager 字段）
Build Tool        = Vite 6（vite.config.ts）
Runtime           = 浏览器 SPA（index.html + createRoot）；开发期 dev server 5173
```

## 5. Current Frontend Classification

```text
分类 = **Prototype / Skeleton（STEP 0）** —— 既非 Production，也非 Legacy/Generated
证据：
  * apps/frontend/README.md：「Status: **skeleton only** (STEP 0)…no product UI has been built」
  * package.json description：「UAP web client skeleton (STEP 0: structure only)」
  * docs/architecture/P15_DECISION_COMPLETION_REPORT.md：`C-7 Frontend = FUTURE`
  * docs/architecture/P15_HUMAN_DECISION_REVIEW_PACKAGE.md：C-7 Frontend → 需独立
    frontend/API/auth boundary decision（**尚未建立 ID**）
  * docs/architecture/P14_RUNTIME_WAVE2_SCOPE.md：apps/frontend/「Vite + React 前端 · 非 Python runtime 面」
  * README.md / ARCHITECTURE.md：apps/ = api · worker · **frontend skeleton**
⇒ 不得把该 skeleton 当作当前正式 UI baseline；它只是已确定的**落点**与最小技术雏形
```

## 6. Technology Stack

| Layer | Actual Current State | Evidence | Status |
| --- | --- | --- | --- |
| Framework | React 18（声明） | package.json dependencies | PARTIAL（未安装/未锁定） |
| Language | TypeScript 5.7（声明） | package.json devDependencies | PARTIAL |
| Build | Vite 6 + @vitejs/plugin-react 4 | vite.config.ts · devDependencies | PARTIAL |
| Routing | **无** | 无 router 依赖、无路由文件 | MISSING |
| State | **无**（仅组件内 useState） | src/main.tsx | MISSING |
| Styling | 仅内联 style（无 CSS 方案/Token） | src/main.tsx | MISSING |
| Components | 无组件层（单文件 App） | src/main.tsx | MISSING |
| API client | 无（裸 fetch 一次 `/api/v1/meta`） | src/main.tsx | MISSING |
| Auth | **无**（未接认证/会话） | 无 auth 代码；README 未提 | MISSING |
| Testing | **无**（无 test 脚本/依赖/工具） | package.json scripts | MISSING |
| Deployment | **无前端服务/构建步骤** | docker-compose.yml · Dockerfile | MISSING |

## 7. Existing UI Architecture

```text
实际结构 = 单页骨架：
  index.html（#root + module script）→ src/main.tsx（App 组件 + useEffect fetch + 内联样式）
无 shell · 无 layout · 无 router · 无状态管理 · 无设计系统 · 无组件库 · 无错误边界 ·
无 loading/empty/error 抽象 · 无 i18n · 无 a11y 结构（仅有语义化 <main>/<h1>）
⇒ 现有 UI 架构 = 0 层抽象，P21 的架构建议为**新建**而非适配既有分层
```

## 8. API Contract Recovery

```text
P20 Company（已 Accepted · 11 条 · 不得扩展）：
  POST   /company/tenants/{tenant_id}/employees                       201
  GET    /company/tenants/{tenant_id}/employees                       200（?status&limit）
  GET    /company/tenants/{tenant_id}/employees/{employee_id}         200
  PATCH  /company/tenants/{tenant_id}/employees/{employee_id}         200
  POST   /company/tenants/{tenant_id}/employees/{employee_id}/suspend 200
  POST   /company/tenants/{tenant_id}/employees/{employee_id}/terminate 200
  POST   /company/tenants/{tenant_id}/assignments                     201
  GET    /company/tenants/{tenant_id}/assignments                     200（?employee_id&space_id&status&limit）
  GET    /company/tenants/{tenant_id}/assignments/{assignment_id}     200
  PATCH  /company/tenants/{tenant_id}/assignments/{assignment_id}     200
  POST   /company/tenants/{tenant_id}/assignments/{assignment_id}/end 200
后端总路由 = 49 条（实枚举），含：/health · /ready · GET /api/v1/meta ·
  /identity/{onboarding,authenticate} · /sessions{,/refresh,/logout} · GET /me ·
  /devices/{enrollment,enrollment-challenge,{id}/lost,{id}/revoke} ·
  /tenants{,/{id},/{id}/spaces,/{id}/members...} · /control/* · /agents/{id}/runs · /agent-runs/{id}
⇒ 前端 skeleton 的 `/api/v1/meta` 与后端 prefix 一致（契约正确）
```

## 9. Company UI Scope（仅基于已 Accepted 能力）

```text
范围 = Company Workspace/Overview · Employee List/Detail/Create/Edit/Suspend/Terminate ·
       Assignment List/Detail/Create/Edit/End
UI 形态建议：List = 页面；Create/Edit = 表单页或抽屉；Suspend/Terminate/End = 确认对话框
  （11 个 API ≠ 11 个页面；但语义必须清晰、动作后果必须显式）
不做：delete / admin（后端无 use case）· 组织树编辑 · 事件/队列/Worker 界面
```

## 10. Information Architecture（Recommendation · 不冻结）

```text
建议：
  /company                     → Company Overview（租户内概览 + 两个入口）
  /company/employees           → Employee List（过滤 status · 分页 limit）
  /company/employees/:id       → Employee Detail（+ suspend/terminate 动作）
  /company/assignments         → Assignment List（过滤 status/employee/space）
  /company/assignments/:id     → Assignment Detail（+ end/role 动作）
共享 Shell（Platform UI）：顶部导航 · 当前 tenant 指示/切换 · 当前用户菜单 · 全局反馈区
备选：把 Overview 合并进 Employees（若首版无真实概览数据来源）；由 Human 裁定
```

## 11. Tenant Context

```text
后端事实：`GET /me` 返回 log-safe 上下文（含 tenant_id/space_id · 可选由 x-tenant-id/x-space-id 头指定）；
  P17 提供 `GET /tenants`（当前 actor 可见租户）与 `/tenants/{id}/spaces`；Company API 的 tenant 来自 **path**。
建议设计（不冻结）：
  Tenant 来源      = 用户登录后从 `GET /tenants` 选择/回退到 /me 的 tenant
  当前 tenant 存放 = 前端全局上下文（auth 之外唯一的全局状态）+ 可选 URL 段（见 §29）
  刷新恢复         = 依据 URL（若采用 URL 承载）或全局上下文持久化 + 每次请求由 `/me` 校验
  API path 注入    = API client 统一以「当前 tenant」填充 `/company/tenants/{tenant_id}/...`
  一致性防线       = ① 前端只在上下文与 URL 一致时发请求；② 后端 403/422 为最终事实；
                     ③ 绝不使用 x-tenant-id 头去覆盖 Company API 的 path tenant（Company API 不接受该头）
原则：UI context → API path tenant_id → Backend Authorization（安全边界始终在后端）
```

## 12. Space Context

```text
Employee：space_id = NULL（UI 不得把员工放入某个 space；员工详情不显示 space 归属）
Assignment：显式 space_id —— 仅在 Assignment 表单/详情出现 Space 选择器
可选 Space 来源：`GET /tenants/{tenant_id}/spaces`（P17 既有端点 · 返回该 actor 可见的 space 列表）
禁止：前端硬编码组织树 · 自行推测 space · 用 space 过滤 Employee
```

## 13. Authentication

```text
后端既有认证面（实枚举）：
  POST /identity/onboarding · POST /identity/authenticate
  POST /sessions · POST /sessions/refresh · POST /sessions/logout
  POST /devices/enrollment · /devices/enrollment-challenge · /devices/{id}/lost · /devices/{id}/revoke
传输方式：`Authorization: Bearer <session token>`（apps/api/dependencies.py::bearer_token）
上下文：`GET /me` 需要有效会话；未认证 ⇒ 401（error_mapping: authentication → 401）
前端现状：**无任何认证集成**（无 token 获取/存储/刷新/登出）
Company Employee 不是登录身份：**不得**创建 Employee Login / Credential / Session（会话/身份属平台）
```

## 14. Current User / Actor

```text
`GET /me` 返回字段（实测 log-safe 白名单）：correlation_id · session_id · device_id · identity_id ·
  user_id · tenant_id · space_id · subject_type · scope · authentication_assurance
⇒ 可支撑：显示当前用户 · tenant 回退 · 审计上下文可见性
⇒ **不包含** permissions / roles / memberships 列表
Employee ≠ User：/me 的 user_id 是平台身份，与 Company 员工记录无自动关联
```

## 15. Permission-Aware UI

```text
Company 权限键（0019 冻结 · 11 条）：employee {read,list,create,update,delete,admin} ·
  assignment {read,list,create,update,delete}
V1 UI 只呈现有 use case 的能力：read/list/create/update（含 suspend/terminate/end）；
  **不呈现** delete / admin（后端无用例）
UI 可 hide / disable / not render；但 **UI 掩藏不是安全控制**，后端仍必须拒绝未授权请求
数据源问题：无权限查询端点（§30）⇒ 首版可采用「能力保守 + 403 后降级」策略（Human Decision）
```

## 16. Error Taxonomy（前端展示映射）

| 后端状态 | 语义（Company 契约） | 前端策略 |
| --- | --- | --- |
| 401 | authentication | 引导重新登录；不泄露细节 |
| 403 | 授权拒绝 / 资源不可见（RESOURCE_NOT_PROVISIONED 同族） | "无权访问或资源不可用"，不区分存在性 |
| 409 | 业务冲突（工号/用户/分配/生命周期） | 就地冲突提示 + 刷新建议 |
| 422 | 校验失败 / 未找到（D-API-02 = A） | 字段级错误（表单）或"未找到"提示 |
| 503 | persistence / security_boundary（模糊化） | "服务暂时不可用"，可重试提示 |

```text
禁止把后端安全错误渲染为 SQL / 约束名 / 栈 / 数据库信息（后端已不返回，前端也不得自行补全）
```

## 17. Loading / Empty / Error

```text
统一状态集（平台层提供，Company 复用）：Loading · Empty · Error · Unauthorized · Conflict ·
Saving · Action in progress · Success
List 页必须区分：loading / empty（无数据）/ forbidden（403）/ error（5xx）
禁止每页各写一套实现（属 Platform UI 的 feedback 层）
```

## 18. Forms

```text
现状：无表单库、无校验库、无错误处理抽象（package.json 无相关依赖）
建议（不选型）：受控组件 + 后端 422 映射到字段错误；保存期间禁用重复提交；
  离开未保存表单需提示（dirty state）；Employee 表单字段严格取自 DTO 白名单
```

## 19. Actions（高风险动作）

```text
Suspend · Terminate · End Assignment：
  显式确认对话框（说明后果：状态不可逆/终态）· in-progress 状态 · 防重复点击 ·
  成功后刷新详情/列表 · 409 冲突处理（提示状态已变化并刷新）
最终业务状态由后端决定；UI 不做乐观状态承诺
```

## 20. Tables / Filters

```text
后端冻结查询面：employees = status + limit(1..200)；assignments = employee_id/space_id/status + limit
后端**无** cursor / 排序 / DSL ⇒ 前端不得发明对应请求
建议：首版 = 简单表格 + status 过滤 + limit 分页（"加载更多/上一页/下一页"由 limit 驱动）；
  若需排序 = **仅在当前已加载数据集上做 client-side 排序**，并在 UI 标注范围；
  真实服务端排序/游标 = 需新的后端决策（记录 Gap，不在 P21 提出 API 变更）
```

## 21. Responsive

```text
目标：desktop / tablet / mobile 三档（UAP 是多设备平台，不得只按宽屏设计）
建议断点（提案）：≥1024 三栏可用 · 768–1023 两栏/抽屉 · <768 单栏 + 抽屉导航
首版要求：Employee/Assignment 列表在窄屏可用（卡片化或横向最小列）；对话式为全屏或底部抽屉
本轮不写 CSS，仅确定要求
```

## 22. Design System

```text
现状：无任何 token / 组件库 / 主题（仅内联样式）
建议最小 Token Layer（第一阶段）：surface · text · muted · border · accent · success ·
  warning · danger · spacing 尺度 · radius 尺度 · typography 尺度
不建议首版自建数十个组件；具体视觉风格（品牌色/密度/暗色模式）= Human Decision
```

## 23. Frontend Architecture（建议结构 · 不冻结）

```text
apps/frontend/src/
  app/            # 启动、Providers、错误边界
  shell/          # 导航、布局、租户切换器、用户菜单
  routing/        # 路由表、受保护路由、403/404
  auth/           # 会话获取/刷新/登出（消费既有认证 API）
  tenant/         # 当前租户上下文
  api/            # UAP API client（base URL、bearer、correlation、错误归一）
  components/     # 平台通用 UI 原语
  forms/          # 表单原语（字段、校验呈现、dirty 保护）
  feedback/       # loading/empty/error/toast/confirm
  modules/company/# Company 页面、feature 组件、DTO 映射、API 调用
目标层次：UAP UI Foundation → Company UI → future Commercial / Entertainment / Industry Templates
禁止：Company-only 前端架构（平台层能力不得写在 company 模块里）
```

## 24. Company Module Boundary

```text
Company 模块只负责：Company 页面 · feature 组件 · DTO 映射 · 权限映射 · Company API 调用
不得复制：认证 · 租户模型 · API client 基础设施 · 全局错误系统 · 全局 UI 组件 · 全局权限引擎
（这些由 Platform UI 层提供；Company 仅消费）
```

## 25. API Client

```text
现状：无 API client（仅 main.tsx 裸 fetch 一次）
建议统一 UAP API Client（平台层）：
  base URL（dev 走 Vite 代理 `/api`；生产由部署模型决定，见 §38）
  bearer transport（Authorization 头）· 401 触发会话恢复
  correlation：自动生成并透传 `x-correlation-id`（若调用方已有则沿用）
  类型化响应（以 API DTO 白名单为准）· 错误归一（401/403/409/422/503 → 前端错误模型）
  超时与取消 · 禁用浏览器默认凭据（如后续采用 cookie 认证需另行决策 CSRF）
```

## 26. Correlation

```text
后端既有约定：`x-correlation-id`（/me 读取；Company 路由 `_correlation(request)` 读取并写入审计）
⇒ 前端 API Client 应**沿用同名头**（不得改名），可在客户端生成 UUID 并在请求链中透传
现状：前端 skeleton 未发送该头（属缺失能力，非冲突）
```

## 27. State

```text
建议分层（不引入新库直到 Human 决策）：
  global：auth（会话）· tenant（当前租户）
  feature/query：Company employees / assignments 查询缓存与失效
  local：表单、对话框、暂时 UI 状态
现状：无状态库；首版可用轻量自建 context + 组件内状态，避免过早引入全局状态框架
```

## 28. Routing

```text
现状：无 router 依赖/文件（index.html 单页骨架）
建议：引入最小客户端路由（选型由 H08 决定）；需要：嵌套路由 · 受保护路由（未登录 → 登录）·
  403 页面 · 404 页面 · 深链可刷新（取决于 §29 的 URL 策略）
Company 路由候选：/company · /company/employees · /company/employees/:id ·
  /company/assignments · /company/assignments/:id
```

## 29. Tenant URL Strategy（重点决策）

| 选项 | 形态 | 优点 | 代价 |
| --- | --- | --- | --- |
| A | `/tenants/:tenant_id/company/...` | 深链/书签/刷新天然正确；多租户切换可见；与后端 path 契约同构 | URL 变长；需处理非法/无权限 tenant 的 URL |
| B | `/company/...` + 全局上下文注入 tenant | URL 简洁；切换租户不改变 URL 结构 | 深链/刷新依赖上下文恢复；分享链接跨租户易混淆 |
| C | 由既有 App Router/URL 规范决定 | — | 当前**不存在**既有 router/规范（§28）⇒ 无法作为依据 |

```text
建议（不冻结）：**Option A** —— 与 Company API 的 path 契约同构，且天然满足"UI tenant 与 API tenant 一致"，
  并让 403/422 的语义（不可见/未找到）在 URL 层可解释。
须在 Human Decision 中确认（P21-H03），并同时确认：非法 tenant URL 的行为（跳转/403 页面）、
租户切换是否保留当前子路径。
```

## 30. Permission Source

```text
实测：`GET /me` 不返回 permissions/roles；平台**不存在**"我的权限"端点；
  `GET /tenants` 仅返回可见租户；成员端点按 tenant/space 粒度返回成员（非"我的权限"）
⇒ Frontend permission data source = **Human Decision Required**
可选方向（均需后端决策，P21 不得自行加 API）：
  (a) 扩展 `/me` 返回权限摘要（后端变更）
  (2) 新增"我的授权"端点（后端变更）
  (3) 首版采用"能力保守 + 403 降级"（无权限数据源，纯 UX 降级）
  (4) 由未来 Control Plane 提供管理态能力（面向管理员 UI）
```

## 31. Authorization UX

```text
对明显无权限的动作：隐藏或禁用，并给出原因提示；但即使按钮可见，后端仍必须拒绝（UI ≠ 安全）
高风险动作（Suspend / Terminate / End Assignment）不得只靠按钮隐藏保护
403 之后：给出统一"无权访问或资源不可用"提示（不区分存在性，与后端语义保持一致）
```

## 31.1 Company Data Display（DTO 事实边界）

```text
EmployeeResponse 字段（API 冻结）：employee_id · tenant_id · employee_no · display_name · title ·
  status · user_id · hired_at · terminated_at · created_at · updated_at
AssignmentResponse 字段：assignment_id · tenant_id · employee_id · space_id · assignment_role ·
  status · started_at · ended_at · created_at · updated_at
⇒ Employee Detail 可显示：工号 · 展示名 · 职务 · 状态 · 平台身份绑定（user_id）· 时间戳
⇒ Assignment Detail 可显示：员工 · 部门（space）· 角色 · 状态 · 生命周期（started/ended）
⇒ **不得**要求 API 未暴露的字段（如员工邮箱、组织层级、审计明细）
```

## 32. Event UI Boundary

```text
P20 Event Infrastructure = BACKEND PLATFORM CAPABILITY（附录 AH/AI/AJ/AK）
当前：Business Handler = 0 · Production Event = NOT AUTHORIZED · Allowlist = EMPTY · Worker = NOT AUTHORIZED
⇒ **P20 Event UI = OUT OF SCOPE**（不做诊断台/队列视图/Handler 管理/Allowlist 管理）
未来仅在出现真实 Handler/Consumer 后，另立决策再评估 Event UI
```

## 33. Backend Regression Constraints

```text
P21 前端设计**不得要求**：Company API 变更 · 授权模型变更 · 新后端端点 · migration · schema 变更
若 UI 发现缺字段/缺能力（例如权限数据源、服务端排序）⇒ 记为 Gap（§43），由后端独立决策
后端 49 路由与 11 条 Company 契约在本轮**未被触碰**（§3 基线）
```

## 34. Testing Strategy（Discovery + 最小建议）

```text
现状：前端**无任何测试工具**（无 test 脚本、无测试依赖、无 e2e/visual/a11y 工具）
建议最小策略（不安装工具）：单元（纯映射/格式化）· 组件（关键反馈态）· 集成（API client + 错误归一）·
  e2e 冒烟（登录 → 选租户 → 员工列表 → 创建 → 挂起 → 终止；分配创建 → 结束）·
  可访问性检查（关键页面键盘可达）
首版至少覆盖：navigation · tenant context · API mapping · permission-aware rendering ·
  form validation · error handling · critical actions · responsive behavior
```

## 35. Accessibility（要求，不实现）

```text
键盘可达与焦点管理（含对话框焦点陷阱与返回）· 表单标签与错误关联（aria-describedby）·
  对话框语义（role=dialog/aria-modal）· 不以颜色单独表达状态（status 需文本/图标）·
  list/detail 语义结构（表头、标题层级）· 空态/错误态对屏幕阅读器可读
```

## 36. Security

```text
Token 存储：**未决定**（当前无认证集成）—— 若采用 bearer（现状 API），需在 Human Decision 中确定
  storage（内存 vs sessionStorage）与 XSS 影响面；不得在 localStorage 长期存放高价值凭据
XSS：React 默认转义；禁止 dangerouslySetInnerHTML 渲染后端文本
CSRF：当前认证为 Authorization 头（非 cookie）⇒ CSRF 面较低；若未来改 cookie 认证需另行决策
CORS：后端**无 CORS 中间件**（实测）⇒ 生产必须同源/反向代理，或另行决策开启 CORS
环境变量：前端**不得**包含 DB DSN / OpenAI key / JWT signing secret / 内部凭据；
  .env.example 全部为后端变量（SECRET_KEY / DATABASE_URL / provider keys 等），无任何 VITE_* 变量
源码映射：尚无构建配置（生产是否发布 sourcemap = 部署决策）
实测结论：**未发现浏览器可见密钥风险**（前端无 secret、无构建注入）
```

## 37. Deployment

```text
现状：docker-compose 仅 postgres + api（+ 可选 redis）；Dockerfile 为纯 Python（uvicorn :8000）；
  **无前端服务、无静态托管、无反向代理、无 CI（无 .github/ 或其它 CI 配置）**
开发期：Vite dev server :5173 代理 `/api`、`/health`、`/ready` 到 API（VITE_API_TARGET，默认 localhost:8000）
生产问题（均未决）：Frontend deployment model? API 同源还是跨域? 是否需要 CORS? 是否需要反向代理?
候选模型（不冻结）：① 静态产物 + 反向代理（同源 /api）② FastAPI 挂载静态文件（需后端改动 → 需决策）
  ③ 独立静态托管 + CORS（需后端 CORS 决策）
```

## 38. Environment

```text
后端 .env.example（实测）：APP_* · DATABASE_URL · UAP_MIGRATION_DATABASE_URL · REDIS_URL ·
  SECRET_KEY · LOG_LEVEL · AI_* · EXPECTED_ALEMBIC_REVISION · *_API_KEY（全部空值）
前端：仅 vite.config.ts 读取 `VITE_API_TARGET`（非密钥 · 可公开）
OBSERVATION：`VITE_API_TARGET` 未在 .env.example 中登记（前端环境变量文档缺口）
规则：浏览器可见的 VITE_* 变量**只允许**存放公开配置（API base URL / 功能开关等），永不存放密钥
```

## 39. Architecture Decision Matrix

| Decision | Current Evidence | Recommendation | Human Decision Required |
| --- | --- | --- | --- |
| Framework | React18+Vite6+TS5.7 声明于已提交 skeleton（无 lockfile/node_modules） | 以现有 skeleton 为基线（保栈、补锁文件与工具链），不另起框架 | **YES**（H01：确认/替换） |
| Frontend directory | `apps/frontend/`（已提交 · 文档确认为前端落点） | 沿用 `apps/frontend/` | NO（ALREADY DETERMINED by existing structure/docs） |
| Routing | 无 router | 引入最小客户端路由（选型见 H08） | **YES**（H08） |
| Tenant URL | 无既有 URL 规范；API 要求 path tenant | Option A `/tenants/:tenant_id/company/...` | **YES**（H03） |
| Auth integration | 后端有完整会话/设备 API；前端零集成 | 复用既有认证 API（bearer 会话） | **YES**（H04：存储/刷新/登出策略） |
| API client | 无（裸 fetch 一次） | 统一 UAP API Client（平台层） | **YES**（H05） |
| State | 无 | global=auth+tenant；feature=查询；local=表单 | **YES**（H06） |
| Styling | 仅内联样式 | 最小 Token Layer + 统一原语 | **YES**（H07） |
| Components | 无 | 平台原语（按钮/输入/表格/对话框/徽章/导航） | **YES**（H07 一并裁定） |
| Permission UI | 无权限数据源（/me 不含权限） | 保守渲染 + 403 降级（或后端补权限端点） | **YES**（H09） |
| Testing | 无任何前端测试工具 | 最小策略（单元+组件+e2e 冒烟+a11y） | **YES**（H10） |
| Deployment | compose/Dockerfile 无前端；无 CORS/静态托管/CI | 静态产物 + 同源反向代理（推荐形态待定） | **YES**（H11） |

## 40. Company UI Route Matrix

| UI Area | Backend API | Permission | Tenant Context | Space Context |
| --- | --- | --- | --- | --- |
| Employees (list) | GET `/company/tenants/{t}/employees` | `company_employee.list` | path tenant | 不适用（NULL） |
| Employee Detail | GET `.../employees/{id}` | `company_employee.read` | path tenant | 不适用 |
| Create Employee | POST `.../employees` | `company_employee.create` | path tenant | 不适用 |
| Edit Employee | PATCH `.../employees/{id}` | `company_employee.update` | path tenant | 不适用 |
| Suspend | POST `.../employees/{id}/suspend` | `company_employee.update` | path tenant | 不适用 |
| Terminate | POST `.../employees/{id}/terminate` | `company_employee.update` | path tenant | 不适用 |
| Assignments (list) | GET `.../assignments` | `company_assignment.list` | path tenant | 过滤 `space_id` |
| Assignment Detail | GET `.../assignments/{id}` | `company_assignment.read` | path tenant | 详情显示 space |
| Create Assignment | POST `.../assignments` | `company_assignment.create` | path tenant | **选择器**（来自 `/tenants/{t}/spaces`） |
| Edit Assignment | PATCH `.../assignments/{id}` | `company_assignment.update` | path tenant | 显示既有 space |
| End Assignment | POST `.../assignments/{id}/end` | `company_assignment.update` | path tenant | 显示既有 space |

```text
未映射（后端无用例 · UI 不呈现）：company_employee.delete · company_employee.admin · company_assignment.delete
```

## 41. Human Decision Topics

```text
P21-H01 Frontend framework          = 待定（现有 skeleton 为 React18+Vite6+TS5.7 · 无锁文件/无工具链）
P21-H02 frontend root directory     = **ALREADY DETERMINED**（apps/frontend/ · 文档与仓库结构已确定）
P21-H03 tenant URL strategy         = 待定（A/B/C · 建议 A）
P21-H04 authentication integration  = 待定（token 存储/刷新/登出/401 恢复策略）
P21-H05 API client architecture     = 待定（统一 UAP API Client 的边界与归属）
P21-H06 state management            = 待定（global=auth+tenant 等分层）
P21-H07 styling / design system     = 待定（最小 Token Layer + 原语范围）
P21-H08 routing structure           = 待定（router 选型与受保护路由/403/404）
P21-H09 permission-aware UI         = 待定（权限数据源缺失：后端补端点 vs 保守降级）
P21-H10 testing baseline            = 待定（单元/组件/e2e/a11y 最小集）
P21-H11 deployment model            = 待定（同源反代 / 静态托管+CORS / FastAPI 静态挂载）
（H02 标记 ALREADY DETERMINED · 其余 10 项需 Human 裁定；本轮不冻结任何一项）
```

## 42. Findings

```text
BLOCKING：**无**
  （未发现浏览器可见密钥 · 无认证边界矛盾 · 租户上下文可安全建立 ·
   无前端绕过后端授权的路径 —— 现有前端仅调用公开 meta · 无数据库直连 · 无不可消费的 API 契约）

NON-BLOCKING / OBSERVATION：
  O-P21-01  前端无 lockfile（package.json 声明 ^ 范围 + 无 lock）⇒ 可复现性缺口（实施前需补）
  O-P21-02  前端无 tsconfig.json（TS 声明存在但无编译配置）⇒ 实施前需补
  O-P21-03  前端无测试 / lint / format 工具（§34）
  O-P21-04  后端无 CORS 中间件 + 无静态托管 ⇒ 生产部署模型必须显式决策（H11）
  O-P21-05  无权限查询端点（/me 不含权限）⇒ permission-aware UI 数据源待裁（H09）
  O-P21-06  `VITE_API_TARGET` 未登记于 .env.example（前端环境变量文档缺口）
  O-P21-07  无 CI/CD 配置（部署仍为手工；属既有状态，非 P21 引入）
  O-P21-08  P15 复核包已登记"C-7 Frontend 需独立 frontend/API/auth boundary decision（尚无 ID）"
            ⇒ P21-H01…H11 即该决策的正式落地入口
```

## 43. Final Verdict

```text
P21 FRONTEND DISCOVERY / UI ARCHITECTURE PREP = PASS

理由：① 真实前端现状已证明（apps/frontend = STEP-0 skeleton · 非生产 UI）
      ② 前端架构选项已识别（框架/路由/租户 URL/认证/API client/状态/样式/权限/测试/部署）
      ③ 实际后端 API 契约已恢复（49 路由 · Company 11 条 · /me · 认证面）
      ④ Company UI 范围与路由矩阵已映射（仅使用已 Accepted 能力）
      ⑤ tenant / auth / permission / space 边界已映射
      ⑥ 安全风险评估完成（无浏览器可见密钥；token 策略与 CORS 待裁）
      ⑦ 部署模型评估完成（当前无前端服务/静态托管/CI）
      ⑧ Human Decisions 已隔离（P21-H01…H11 · H02 ALREADY DETERMINED）
      ⑨ 未执行任何实现（无安装、无 lockfile 变更、无源码改动、无 PDL 改动）

Frontend Implementation: NOT AUTHORIZED
Company UI:              DESIGN ONLY
Company API:             ACCEPTED / UNCHANGED
Event UI:                OUT OF SCOPE
Event Production:        NOT AUTHORIZED · Worker: NOT AUTHORIZED · Migration: NOT AUTHORIZED
Package Installation:    NOT AUTHORIZED

Commit: NO   Tag: NO   Push: NO
HARD STOP: ACTIVE
```

## 44. Hard Stop

```text
HEAD = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5（未变）· staged = 0 · git diff --check 仅历史 CRLF 警告
本轮仓库写入 = 仅本报告（未安装任何依赖 · 未改 lockfile · 无源码实现 · 未修改 PDL ·
  未修改后端 / Company API / 授权 / migration / Event）
历史 dirty files 全部保留未清理

HARD STOP = ACTIVE
下一阶段（必须由 Human 裁定）：P21 FRONTEND ARCHITECTURE DECISION
  其后才可：P21 FRONTEND FOUNDATION IMPLEMENTATION → P21 COMPANY UI IMPLEMENTATION
边界复述：Discovery ≠ Architecture Freeze；Architecture Freeze ≠ Implementation；
  Implementation ≠ UI Acceptance；UI Acceptance ≠ Product Completion。
```

**END OF P21 FRONTEND DISCOVERY / UI ARCHITECTURE PREP REPORT（前端现状 = apps/frontend STEP-0 skeleton（React18+Vite6+TS5.7 · 无 lockfile/无工具链/无认证集成）· 后端 49 路由含 /me 与完整认证面 · Company 11 条 API 已 Accepted · 无 CORS/静态托管/CI · 8 项非阻断观察 · P21-H01…H11 待裁（H02 已定）· 未实现 / 未安装 / 未 commit；2026-10-04）**
