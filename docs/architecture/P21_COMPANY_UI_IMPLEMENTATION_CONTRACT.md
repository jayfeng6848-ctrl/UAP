# P21 COMPANY UI — IMPLEMENTATION CONTRACT

**Status: FINAL（P21 COMPANY UI DESIGN = FULLY FROZEN）· 仍不构成实现授权**
Base commit: `e20b35f83a1912b0f051d8d0d2d7009f0ee6f7f9` (`UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS`)
Authority: PDL 附录 AO（D-CUI-01…18）+ **附录 AP**（OQ-CUI-01…09 = FROZEN · F-1…F-4 = ACCEPTED）
Produced by: `P21 COMPANY UI PREP` → `OQ-CUI HUMAN DECISION FINAL AUTHORIZATION`（2026-10-05）

> 本文件把已冻结的 D-CUI-01…18（附录 AO）与 OQ-CUI-01…09 / F-1…F-4（附录 AP）翻译为**实现规则**。
> 全部原 OPEN QUESTION 已由附录 AP 裁定并落位；残余项见 §34/§35。
> 本文件不引入新语义、不构成实现授权：`IMPLEMENTATION = NOT AUTHORIZED`。

---

## 1. Purpose

定义 `P21 Company Desktop UI` 的实现规则：Company Workspace 信息架构、路由、角色/能力/范围 UX、
员工与分配生命周期 UX、Reports 边界、AI Copilot 边界、安全与质量约束。

## 2. Authority

权威优先级：Human/Frozen Decision > Frozen Contract > `PLATFORM_DECISION_LOG.md` > 实际仓库源码 >
实际 Git 状态 > 实际 DB 状态 > 既有 Gate/Acceptance 证据 > Master Dossier > 记录本 > 设计建议。

本合约的直接权威：**PDL 附录 AO**（D-CUI-01…18 + AO.0 的 C1–C5 修正 + AO.3 能力矩阵 + AO.7 S1–S18）。
相关前置权威：附录 AF（P20 Company Domain）· 附录 AG（P20 Company API）· 附录 AN（P21 Local AI / Universal
Model Selection）· 附录 AL（P21 Frontend Foundation）。

**Dossier / 记录本不是技术权威。** 若其与本合约发现的事实冲突，以 Git/源码/DB 为准并登记 CONFLICT。

## 3. Current Baseline（2026-10-05 实测）

```text
Git      : HEAD e20b35f8 · branch main · staged 0 · porcelain 227
           modified tracked 58 · untracked 169 · diff 3631 insertions / 263 deletions · diff --check clean
           tags_at_HEAD = UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS
前端      : 公司模块 5 页面 + CompanyNotFound；路由 4 条 + index + *；测试 6 个文件
           capability.tsx = 占位（availability 恒为 'unknown'，仅 'unavailable' 时隐藏）
路由      : /login · / · /tenants/:tenant_id/company/* · /ai · /tenants/:tenant_id/ai/* · /403 · *
后端      : Company API 11 路由；授权集中在 services/company/use_cases.py::_authorize，每个用例先授权
角色/授予 : platform_admin 23 授予（含 11 条 company）· space_admin 15（0 company）· tenant_admin 6（0 company）
Team      : 无 team/delegation 表，且 information_schema.columns 中 team/delegat 列 = 0 → 权威来源 NONE
SELF      : 依 AF D-P20D-07 = A（V1 不支持）
AI        : /ai/providers · /ai/providers/{k}/models · /ai/local/providers · /ai/connection · /ai/messages
           工具：registry 有 platform.clock.now + company.employee_list；DB tools 仅 company.employee_list（LOW）
           /intelligence · copilot · orchestrator · citation = 0 命中 → NOT EXISTS
AI supply : ai_providers=6 · ai_models=6 · ai_routes=1 · ai_policies=1
分类      : core/resource/interfaces.py CLASSIFICATIONS = PUBLIC/INTERNAL/CONFIDENTIAL/HIGHLY_CONFIDENTIAL（未变）
数据库    : 平行体系表 0（company_departments/company_teams/ai_conversations/ai_quotas/sys_* 等）
```

## 4. Frozen Decisions（D-CUI-01…18 摘要）

```text
01 Workspace-first（Overview/Employees/Assignments/Reports/AI Copilot，capability-aware）
02 Company=Tenant · Department=Space · Team=授权范围概念（不建 Team Domain）
03 Effective Capability = AuthN×Role×Permission×Scope×Resource×Classification×State×Transition
04 五层逻辑角色 L0–L4（逻辑语义；实际授予另立决策）
05 AI Scope = SELF/TEAM/SPACE/TENANT，且 AI Scope ≤ User Effective Scope
06 仅 ANSWER / PROPOSE，禁止 AI DIRECT EXECUTE
07 沿用既有 11 条 company 权限；permission ≠ transition；delete/admin RESERVED 不开放
08 Terminate 仅 Company Admin
09 Team Lead 有限团队能力（当前 DISABLED）
10 KB 授权 = UAP Resource Authorization + Classification + AI Policy
11 只读=LOW；高风险=PROPOSAL + HUMAN CONFIRMATION → 走 Company API
12 Quota policy-ready / schema-deferred
13 显式 Provider+Model；无静默替换、无本地→云端回退
14 /intelligence 仅 Domain-facing Facade，非第二套 AI Runtime
15 Team Scope 权威延后（不可用 ⇒ Team Lead disabled）
16 Proposal 需过期 + 确认时重新授权；STALE 不得执行
17 Platform Governance 与 Company Business Administration 分离
18 Classification 在进入 Provider 前强制执行，禁止 downgrade
```

## 5. Scope / Non-Scope

**In scope（实现时）**：Company Workspace 导航与页面、路由与租户边界、能力/范围 UX（受 OQ 约束）、
员工与分配生命周期 UX（消费既有 API）、AI Copilot 面板（**仅 Read/Propose**）、错误/加载/空/403/404、
可访问性、响应式、测试。

**Non-scope（本合约不授权）**：任何 DB/DDL/DML/migration/seed、权限或角色变更、Team 物化、SELF 授权、
第二套认证/授权/AI Gateway/模型注册表、持久化 AI 会话、Reports 分析模型、Proposal 持久化、
Redis/OPA/Casbin/Keycloak/Milvus/MinIO/Tauri/Electron。

## 6. UI Architecture

延续 P21 Frontend Foundation：React + Vite + TypeScript + React Router + Context/hooks +
typed API client（memory-only token）+ Design Tokens + CSS Modules + Vitest/RTL/Playwright。
**不引入**第二套 Dialog/状态组件/DOM 层；Company 模块继续拥有自身 routes/paths/pages/components。

## 7. Routing

```text
P20 既有 11 条业务路由（语义冻结、不得修改/重定义）：
  /company（index=Overview）· /company/employees · /company/employees/:employee_id ·
  /company/assignments · /company/assignments/:assignment_id · /*（CompanyNotFound）

F-2：本决策授权扩展 Company route manifest（11 → N）。允许新增 Company-facing routes：
  capabilities   → GET /tenants/{tenant_id}/company/capabilities           （OQ-CUI-01）
  reports        → Reports 只读运营端点（OQ-CUI-02；具体路径在实现授权轮冻结）
  intelligence   → POST /intelligence/tenants/{tenant_id}/assistant/runs   （OQ-CUI-03/09，非 /company 前缀）
硬约束：新增路由不得改变任何 P20 既有路由的语义；Acceptance 必须同时验证
        「既有 11 条完整」+「新增 P21 路由符合新冻结语义」。
AI：`/ai/*` 与 `/intelligence/*` 的分工见 F-4 / §15。
```

硬规则：`tenant_id` 只能来自路由参数（`TENANT_PARAM`），不得来自 body / query / header /
localStorage / AI context。既有 `RequireAuth → TenantBoundary → module tree` 组合不得绕过。

## 8. Role UX

```text
目标逻辑角色（AO D-CUI-04）：company_admin / department_manager / team_lead / employee
V1 可物化（OQ-CUI-06 + F-1）：仅 company_admin（scope=TENANT）与 department_manager（scope=SPACE）
不可物化：team_lead（需 scope=TEAM）与 employee（需 scope=SELF）—— 只冻结逻辑语义，不创建角色行
实测现状：platform_admin(PLATFORM,is_system) · tenant_admin(TENANT) · space_admin(SPACE)；
          目标角色 NOT PROVISIONED
```

规则：继续使用现有 `roles` / `role_permissions` / `membership` 体系；禁止 `company_roles` /
`company_role_permissions` 等第二套角色系统。Scope 词表（TEAM / SELF）扩展须新的 Human Decision + DDL 授权。
前端**不得**假定目标角色存在、不得按角色名推断权限、不得创建测试身份。
`Semantic Freeze ≠ Grant Execution`：本合约**不执行** `role_permissions` DML；`platform_admin` 现有
部署态 Company grants **保持不撤销**（OQ-CUI-06.3 / OQ-CUI-14）。

## 9. Capability UX

OQ-CUI-01 = A（FROZEN）：**Server-projected Capability**。Company UI 消费服务端能力投影：

```text
Authenticated Actor + Tenant + Existing AuthorizationService + Authorized Resource/Scope
        ↓  Capability Projection（非第二套授权引擎、非角色查询 API）
GET /tenants/{tenant_id}/company/capabilities
```

投影必须由已有 AuthorizationService 对当前 actor/tenant/资源计算结果得出，**不得**接受
`body permissions` 或 `client-provided role`。前端禁止依据 role name / username / URL /
localStorage / 客户端提交的 permission 自行推断权限。
`Hide button ≠ permission denial`：后端 403 始终是最终结论（AL H09/H40/H41 继续有效——
禁止前端 ACL 引擎；能力投影是后端结论的消费，不是前端计算）。

## 10. Scope UX

```text
TENANT : 已存在（路由租户路径 + 后端集合资源授权）
SPACE  : 已存在的 space 过滤/选择语义；Department = Space（不得引入 department 概念）
TEAM   : DISABLED —— 无权威来源（AO D-CUI-09/15），禁止前端假过滤/客户端 team_id 视为授权
SELF   : unavailable（AF D-P20D-07）—— 禁止实现“本人视图”授权
```

## 11. Company Pages

| Surface | 现状 | 实现规则 |
| --- | --- | --- |
| Overview | 存在（index） | 保持；补充范围/状态呈现时不得新增授权语义 |
| Employees | 存在 | 保持 |
| Employee Detail | 存在 | 保持 |
| Assignments | 存在 | 保持 |
| Assignment Detail | 存在 | 保持 |
| Reports | **MISSING** | 需后端语义与数据来源决策（OQ-CUI-02）；不得自行发明分析 schema |
| AI Copilot（工作区内） | **MISSING** | 见 §15–§20 与 OQ-CUI-03/09 |

## 12. Employee Lifecycle UX

```text
Create / Edit / Suspend / Terminate → 既有 Company API（POST / PATCH / POST suspend / POST terminate）
权限映射（AO D-CUI-07）：Suspend/Terminate → company_employee.update + lifecycle transition rule
delete / admin：NOT EXPOSED（AO D-CUI-07 + AF D-P20D-03/04）
transition 合法性由后端/域规则判定；前端只呈现 409/422 的冻结语义
```

## 13. Assignment UX

```text
Create / Edit / End → 既有 Company API；End → company_assignment.update + transition rule
space_id = Department；跨租户一致性由 DB 触发器（结构性，非授权）与授权层共同保证
```

## 14. Reports Boundary

OQ-CUI-02 = A（FROZEN）：**Operational Read-only Reports**（Company Admin 目标视图）。

```text
允许：Headcount · Employee lifecycle summary · Assignment summary ·
      Unassigned employee summary · Space-level employee counts · Space-level assignment counts
数据链：Existing Company Data → Authorized Query → Aggregation → Read-only Response
Space-level employee counts 必须 derive from company_assignments（该 space 下符合条件
  Assignment 所关联 Employee 的有效计数）；不得为 company_employees 增加 space_id（F-3）
禁止：company_reports / reporting DB / analytics DB / data warehouse / 预计算报表表
```

Reports 继续服从 Tenant + Authorization + Scope + Resource；Department Manager 进入 Reports
页面**不获得** Tenant-wide 数据。若某具体报告需要新后端业务语义 → 列入实现合约，不得自行创造数据模型。

## 15. AI Copilot Boundary

OQ-CUI-03 = A / OQ-CUI-09 = A（FROZEN）：Company Copilot 使用
`POST /intelligence/tenants/{tenant_id}/assistant/runs`，定位为
**Domain-facing Intelligence Facade**（非第二套 AI Runtime / AI Gateway / 授权引擎）。

```text
Company UI → Intelligence API → Existing AI Orchestration/Runtime → Authorization →
AI Policy → AI Gateway → Selected Model → Provider
请求：{ message, context{surface, space_id, resource_id}, mode: "answer" | "propose" }
禁止：mode = execute ；body tenant_id / actor_id / role / permission / client authorization context
      禁止 Intelligence → direct SQL ；→ authorization bypass ；→ repository bypass ；AI → DB
Actor/Tenant/Scope/Permission/Classification/AI Policy 一律由后端重新推导
```

F-4：`/ai/*` = 独立 AI onboarding / standalone assistant 面（继续使用）；
`/intelligence/*` = Company / Domain-facing Intelligence Facade。二者不得演化为重复入口；
Company Copilot **必须**通过 `/intelligence`；不得出现第三套 AI entry。

## 16. AI Context Trust Boundary

前端可发送 `surface / space_id / filters` 等 UX 提示；后端必须重新推导
`Actor / Tenant / Role / Scope / Permission / Resource / Classification` 得到 Authorized Context 后才进入
AI Runtime。**Frontend Context ≠ Authorization Context。**

## 17. AI Read / Proposal Boundary

```text
Read     : User → AuthN → Tenant → Permission → Scope → Resource → Classification → AI Policy →
           AI Gateway → Selected Model → Provider → Answer
Proposal : AI → Proposal → Human Confirm → current session verification → Re-Authorization →
           Scope → Resource → Current State → Existing Company API
```

只读工具 = LOW RISK（当前 `company.employee_list`）可直接回答；高风险动作**必须** PROPOSAL + 人工确认。
当前**不存在**提案生命周期对象（`proposal_id/expires_at/expected_state`）→ 见 §29。

## 18. Citation

OQ-CUI-04 = A（FROZEN）：**Backend-authoritative Citation**。

```text
Authorized Backend Query → Authoritative Resource → Citation Reference → AI Response
Citation = { type, id, label }，必须指向 existing Company Resource
禁止：Model 自行生成“看起来真实”的资源 ID
点击：Citation → Company UI → Existing Authorization → Resource Check → Detail
不得因 AI 已产生 Citation 而跳过权限检查
```

## 19. Model Selection

```text
Provider ≠ Model；每次请求必须携带显式选定 model
禁止：silent model replacement · silent provider switch · silent local→cloud fallback
模型来源：既有 catalog（云端）或经校验的实时发现（本地）；前端不得 invent model ID
```

## 20. Classification

沿用 `PUBLIC / INTERNAL / CONFIDENTIAL / HIGHLY_CONFIDENTIAL`（词表不变）。
进入 Provider 前必须完成 Resource → Classification → AI Policy → Provider/Model Eligibility；
`classification` 不得被 Frontend / Prompt / Tool 降低；禁止分类降级。

## 21. Data Minimization

```text
Question → Authorized Query → Minimal Result → Redaction → AI
只发送必要字段（如 employee_id / name / status / assignment_status）
不发送 credentials / secret / private metadata / 无关敏感字段
UI Visible ≠ AI Required；原始 prompt 不写入 ai_request_logs；raw secret 永不记录
```

## 22. Security（S1–S18 → 实现规则）

```text
S1–S3  Frontend 不得覆盖 Tenant / Scope / Permission（路由与请求体均不得作为授权来源）
S4–S5  AI 不得绕过授权、不得访问未授权 Resource
S6–S8  AI 不得直接访问 DB / Repository；AI 变更必须经 Company API
S9     AI 不得降低 Classification
S10–11 AI 不得静默更换 Model；本地失败不得静默回退云端
S12    Provider secret 不得进入浏览器
S13    原始 prompt 不写入 ai_request_logs
S14–15 提案确认必须重新授权；STALE 提案不得执行
S16    Team Scope 不得由前端上下文推断
S17–18 Platform Admin 与 Company Admin 不得互相自动继承

现状：S6/S7/S8/S10/S11/S13 已成立（工具仅只读 + 不写原始 prompt）；
      S17 尚未成立（platform_admin 现持有全部 11 条 company 权限，AF D-P20D-01）。
```

## 23. Accessibility

复用 Foundation：Dialog 焦点陷阱与焦点恢复、键盘导航、可访问名称；不得另造第二套 Dialog 行为。

## 24. Error / Loading / Empty

复用既有 `CompanyStates` / `ShellStates` / `InlineError` 与 403/404 页面语义；
禁止自造第二套状态语义；后端 403 为最终结论。

## 25. Responsive

沿用 Foundation 响应式规则；Company 页面级响应式优先，仅在确有必要时才最小改动共享 primitive。

## 26. Backend Contract Consumption

```text
UI → existing Company API → Authorization → Company Domain → Repository → DB
禁止：UI → repository；禁止第二套 mutation path
AI：AI Proposal → Human Confirmation → Re-Authorization → Existing Company API
```

## 27. API Boundary

```text
Company API        = Company Business Mutation Authority
Intelligence API   = AI-facing orchestration boundary（尚未存在）
AI Gateway         = Platform AI infrastructure
Company Domain     = Business rules
AI ≠ Authorization Authority ；AI ≠ Domain Authority ；AI ≠ Database Authority
```

## 28. Team / SELF Disabled Boundary

```text
Team  : 无权威来源 → Team Lead runtime DISABLED；Team AI = N/E；禁止前端假过滤/假 membership
SELF  : AF D-P20D-07 = A → Company SELF authorization = unavailable；
        Employee Company Workspace = DISABLED / N/E
        Personal AI（无公司数据的通用对话）必须与 Company-scoped SELF AI 明确区分，不得伪装
```

## 29. Proposal Technical Design

OQ-CUI-05 = A（FROZEN）：**Ephemeral / session-bound / non-persistent Proposal**。

```text
语义必须包含：proposal identity · actor · tenant · scope · resource · action · expected state · expiration
确认链：Re-authentication / Current Session Verification → Authorization → Scope → Resource →
        Current State Revalidation → Existing Company API
技术物化：由本合约规定（不可伪造 / 不可重放 / 过期保护），但不得新增
        proposal table · proposal event system · persistent proposal history
禁止：AI approval → frontend direct mutation ；old proposal → blind execution
```

实现若无法在“无持久化”前提下满足不可伪造/不可重放/过期语义，必须 STOP 并申请新的 Human Decision。

## 30. Database Boundary

```text
NO NEW DATABASE MODEL
不新增：company_departments · company_teams · ai_conversations · ai_messages · ai_threads ·
        company_ai_* · ai_quotas · 任何平行 sys_* 体系
不新增：migration / DDL / DML / index / trigger / route persistence / local credential persistence
```

## 31. Testing

```text
单元/组件：Vitest + RTL（reuse 既有 harness：makeStubClient / renderCompanyModule 风格）
后端：显式 allowlist pytest（禁止 broad sweep）；架构守卫 tests/architecture 必须保持绿
E2E：Playwright（真实 Chromium，认证会话）——在 Acceptance 轮执行；PREP 只定义命令/夹具/证据要求
禁止：为通过测试而 seed 数据或修改权限
```

## 32. Acceptance Gate

验收标准见同批产出的 `docs/architecture/P21_COMPANY_UI_ACCEPTANCE_MATRIX.md`（DRAFT）。
本合约不授权实现；`P21 COMPANY UI IMPLEMENTATION AUTHORIZATION` 需新的 Human Decision。

## 33. Release Boundary

不授权 version bump / commit / tag / push / release / production activation。

## 34. Deferred Items

角色实际定义与授予 · 解除 platform_admin 默认公司变更权 · Team Scope 权威来源与 Team Domain ·
Proposal 技术物化 · Quota schema · 持久化 AI 会话 / 共享 AI memory · Knowledge Base 存储实现 ·
自动与跨 Provider fallback · 高级 RAG · 新 AI route persistence · AI billing · Redis · 向量库 ·
对象存储 · RLS 重设计 · Platform Control Plane 重设计。
（全部 = FUTURE HUMAN DECISION；不得作为“缺陷”修复。）

## 35. Resolved Questions & Residual Deferred Items

```text
OQ-CUI-01 = A FROZEN（服务端能力投影）        → §9
OQ-CUI-02 = A FROZEN（只读运营报表）          → §14
OQ-CUI-03 = A FROZEN（Intelligence Facade）   → §15
OQ-CUI-04 = A FROZEN（后端权威 Citation）     → §18
OQ-CUI-05 = A FROZEN（临时非持久化 Proposal） → §29
OQ-CUI-06 = B FROZEN（V1 仅 company_admin[TENANT] / department_manager[SPACE]）→ §8
OQ-CUI-07 = C FROZEN（Team 延后；runtime DISABLED；Team AI = N/E）→ §28
OQ-CUI-08 = C FROZEN（SELF 延后；Company SELF = NOT ENABLED）→ §28
OQ-CUI-09 = A FROZEN（/intelligence 拥有 Copilot 边界）→ §15
F-1 = ACCEPTED（仅两角色可物化；TEAM/SELF scope 扩展需新决策 + DDL 授权）
F-2 = ACCEPTED（Company route manifest 可扩展；P20 业务路由语义不得改动）
F-3 = ACCEPTED（employee-space 关系继续经 company_assignments）
F-4 = ACCEPTED（/ai 与 /intelligence 边界不重叠，无第三套 AI entry）
```

仍属 FUTURE HUMAN DECISION（不得作为缺陷修复）：角色/授予物化执行 · `platform_admin` Company
grant 撤销 · Team Scope Authority · SELF authorization · Proposal 持久化 · AI 会话持久化 ·
Quota schema · 自动/跨 Provider fallback · 高级 RAG · Scope 词表扩展。
