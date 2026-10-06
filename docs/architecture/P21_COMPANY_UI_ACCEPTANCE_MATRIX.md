# P21 COMPANY UI — ACCEPTANCE MATRIX

**Status: FINAL（Design fully frozen）· NOT an Acceptance**
Companion: `docs/architecture/P21_COMPANY_UI_IMPLEMENTATION_CONTRACT.md`（FINAL）
Authority: PDL 附录 AO（D-CUI-01…18）+ **附录 AP**（OQ-CUI-01…09 = FROZEN · F-1…F-4 = ACCEPTED）
Date: 2026-10-05

> 本矩阵定义未来 Acceptance 的检查项与证据要求。**本 PREP 不执行验收**；任何未实测项一律 `N/E`，
> 不得以“设计上支持”“组件存在”“路由存在”代替实测。

---

## AREA 1 — Architecture

| ID | Requirement | Evidence | Expected |
| --- | --- | --- | --- |
| ARC-01 | Core → Domain = 0 | `tests/architecture` | 0 / PASS |
| ARC-02 | 无第二套 Authorization | source scan | PASS |
| ARC-03 | 无第二套 Tenant 模型 | source + DB | PASS |
| ARC-04 | 无第二套 User 模型 | source + DB | PASS |
| ARC-05 | 无第二套 AI Gateway | source | PASS |
| ARC-06 | 无第二套 Model Registry | source + DB | PASS |

## AREA 2 — Routing / Workspace

| ID | Surface | 检查内容 | 当前 PREP 状态 |
| --- | --- | --- | --- |
| NAV-01 | Company route structure | `/tenants/:tenant_id/company/...` 成立且可直达 | 存在（EXISTS） |
| NAV-02 | Tenant path | tenant 仅来自路由参数；无 body/query/header/localStorage 来源 | 存在（EXISTS） |
| NAV-03 | Overview | index 路由 + 可达 | 存在（EXISTS） |
| NAV-04 | Employees | 列表路由 + 可达 | 存在（EXISTS） |
| NAV-05 | Employee Detail | 详情路由 + 可达 | 存在（EXISTS） |
| NAV-06 | Assignments | 列表路由 + 可达 | 存在（EXISTS） |
| NAV-07 | Assignment Detail | 详情路由 + 可达 | 存在（EXISTS） |
| NAV-08 | Reports | 路由 + 页面 + 只读运营汇总（Headcount / lifecycle / assignment / unassigned / space 计数） | **MISSING**（语义已冻结：OQ-CUI-02 = A） |
| NAV-09 | AI Copilot entry | Company 内入口 → `POST /intelligence/tenants/{id}/assistant/runs` | **MISSING**（API 面已冻结：OQ-CUI-03/09 = A） |
| NAV-10 | Capability projection | `GET /tenants/{tenant_id}/company/capabilities` 消费 | **MISSING**（OQ-CUI-01 = A） |
| NAV-11 | Route manifest | 既有 11 条 P20 路由完整 + 新增 P21 路由符合新语义 | 需在 Acceptance 双向验证（F-2） |

每项 Acceptance 时必须记录：role · route · access · 403 行为 · 404 行为。

## AREA 3 — Role / Capability

| ID | 目标逻辑角色 | 当前物化状态 | Acceptance 预期 |
| --- | --- | --- | --- |
| ROLE-01 | Company Admin（`company_admin`，scope=TENANT） | NOT PROVISIONED（V1 可物化） | 实现后 PASS；未物化则 N/E |
| ROLE-02 | Department Manager（`department_manager`，scope=SPACE） | NOT PROVISIONED（V1 可物化） | 实现后 PASS；未物化则 N/E |
| ROLE-03 | Team Lead | 只冻结语义，**不创建角色行**（需 scope=TEAM） | DISABLED / N/E |
| ROLE-04 | Employee | 只冻结语义，**不创建角色行**（需 scope=SELF） | DISABLED / N/E |
| ROLE-05 | Platform Admin | 已物化（23 授予，含 11 company；**本决策不撤销**） | PASS（现状兼容态） |
| ROLE-06 | 能力投影 | `GET .../company/capabilities` 由既有 AuthorizationService 推导 | 实现后 PASS |

不得制造测试身份；不得修改 `role_permissions`。

## AREA 4 — Permission

必须验证 11 条 company 权限的真实作用（read/list/create/update/delete/admin × employee、assignment）：

```text
PERM-01..11  11 条权限存在且语义正确
PERM-12      delete = NOT EXPOSED（无路由、无运行时授权）
PERM-13      admin  = NOT EXPOSED
PERM-14      Suspend   → company_employee.update + transition rule（非新权限）
PERM-15      Terminate → company_employee.update + transition rule（非新权限）
PERM-16      End       → company_assignment.update + transition rule（非新权限）
```

## AREA 5 — Scope

| ID | Scope | 当前状态 | 预期 |
| --- | --- | --- | --- |
| SCOPE-01 | TENANT | 已实现（租户路径 + 集合资源授权） | PASS |
| SCOPE-02 | SPACE | 已实现（space 语义 = Department） | PASS |
| SCOPE-03 | TEAM | 权威来源 NONE（OQ-CUI-07 = C） | N/E / DISABLED |
| SCOPE-04 | SELF | AF D-P20D-07；OQ-CUI-08 = C | N/E / DISABLED |
| SCOPE-05 | Space 派生 | 员工-空间关系仅经 `company_assignments`（F-3） | PASS（不得新增 employee.space_id） |

## AREA 6 — Security

```text
SEC-01  Tenant override            SEC-10  AI Authorization bypass
SEC-02  Scope override             SEC-11  AI direct DB
SEC-03  Permission override        SEC-12  AI direct Repository
SEC-04  Resource override          SEC-13  AI direct mutation
SEC-05  Wrong tenant               SEC-14  Provider secret exposure
SEC-06  Wrong space                SEC-15  Prompt logging
SEC-07  Team spoof                 SEC-16  Classification downgrade
SEC-08  SELF spoof                 SEC-17  Silent model substitution
SEC-09  AI scope expansion         SEC-18  Silent cloud fallback
```

每项必须给出：攻击输入 → 期望 DENY/fail-closed → 实测响应（含安全错误文案无内部信息）。

## AREA 7 — AI Read

```text
AI-READ-01 Ask Data    AI-READ-04 Summarize
AI-READ-02 Find        AI-READ-05 Explain
AI-READ-03 Filter      AI-READ-06 Citation
```

同时必须证明：authorized data = 可回答；unauthorized data = DENY（不得靠“模型没看见”代替授权）。

## AREA 8 — AI Context

验证 `surface / space_id / filters / resource` 全为 UX 提示；必须证明
**backend reconstructs authoritative context**（frontend context 不得成为授权依据）。

## AREA 9 — AI Proposal

```text
PROP-01 proposal generated            PROP-06 current state revalidation
PROP-02 proposal displayed            PROP-07 stale proposal rejected
PROP-03 human confirmation            PROP-08 proposal expiration
PROP-04 cancel
PROP-05 re-authorization on confirm
```

OQ-CUI-05 = A 已冻结：Proposal 为 **ephemeral / session-bound / non-persistent**，语义含
identity/actor/tenant/scope/resource/action/expected state/expiration；确认链必须
Re-auth → Authorization → Scope → Resource → Current State Revalidation → Existing Company API。
当前无实现 → 全部 **N/E**，直到 Company UI 实现轮完成。

## AREA 10 — Model

```text
MODEL-01 provider selection        MODEL-05 runtime model equality
MODEL-02 model selection           MODEL-06 model switch
MODEL-03 provider/model consistency MODEL-07 provider switch
MODEL-04 no first-enabled fallback MODEL-08 no None / no silent substitution
```

必须证明 `selected model = actual outbound model = ledger model`（参考 P21 Local AI Validation 的证据形式）。

## AREA 11 — Classification

验证 PUBLIC / INTERNAL / CONFIDENTIAL / HIGHLY_CONFIDENTIAL 四档下的
provider eligibility · model eligibility · classification deny · 无降级路径。

## AREA 12 — Data Minimization

```text
DM-01 minimum fields        DM-04 no unnecessary metadata
DM-02 redaction             DM-05 no raw prompt in ai_request_logs
DM-03 no secret/credential  DM-06 UI Visible ≠ AI Required
```

## AREA 13 — UI Quality

Loading · Empty · Error · 403 · 404 · 表单校验 · 成功反馈 · Dialog 行为 · 键盘 · 焦点 · 响应式。
必须**复用** Foundation 能力，不得重新实现第二套。

## AREA 14 — Browser E2E（Acceptance 轮执行，本 PREP 不执行）

```text
E2E-01 real Chromium 认证流程        E2E-05 AI flow
E2E-02 Company route 直达            E2E-06 proposal flow
E2E-03 role-aware UI                 E2E-07 citation
E2E-04 forbidden flow（403）         E2E-08 model selection
环境   ：隔离 synthetic 环境 + 既有 demo 身份（不得新建身份）
证据   ：trace / screenshot / network 记录；本地 AI 无模型时允许 N/E，但不得伪造成功
```

## AREA 15 — DB / Git Integrity

```text
DBG-01 schema 未变（除非单独授权）      DBG-05 无平行表
DBG-02 migration history 完整           DBG-06 无持久化 local credential
DBG-03 无未授权 DDL                     DBG-07 Git：无历史 dirty work 丢失
DBG-04 无未授权 DML                     DBG-08 Git：无 force push / history rewrite
```

验收时必须提供前后 fingerprint（`ai_providers / ai_models / ai_routes / ai_policies /
company_employees / company_assignments / roles / permissions / role_permissions`）。

## AREA 16 — Route Manifest / AI Boundary（F-2 / F-4）

```text
RM-01  既有 11 条 P20 business routes 语义与数量不变（不得重定义）
RM-02  新增 P21 路由（capabilities / reports / intelligence）符合附录 AP 冻结语义
RM-03  无第三套 AI entry：Company Copilot 必经 /intelligence；/ai/* 保持独立 onboarding/assistant
RM-04  新增路由不引入 body tenant_id / client role / client permission 作为授权依据
```

---

## 状态分类字典（强制）

```text
EXISTS / MATCH  ·  EXISTS / PARTIAL  ·  MISSING  ·  CONFLICT  ·  DEFERRED
DISABLED  ·  N/E  ·  OUT OF SCOPE
```

`MISSING ≠ BUG`；`DEFERRED` 与 `DISABLED` 均属**已冻结的预期状态**，不得计入缺陷。

## PREP 阶段状态汇总（不构成验收）

```text
已存在：Company 5 页面 + 路由 + 租户边界 + 11 条 Company API + 单点授权 + 只读 AI 工具 + 显式模型选择
缺失（实现目标）：Reports · Company 内 AI Copilot · Citation · Ephemeral Proposal ·
                Capability projection（`/company/capabilities`）· Intelligence Facade（`/intelligence`）
禁用（按冻结）：Team Lead UI · Team AI · Employee SELF 工作区 · TEAM/SELF scope 词表扩展
已裁定（附录 AP）：OQ-CUI-01…09 = FROZEN · F-1…F-4 = ACCEPTED → 无残余阻塞 PREP 的未决项
仍需独立 Human Decision（非缺陷）：角色/授予物化执行 · platform_admin grant 撤销 · Team 权威 ·
SELF 授权 · Proposal 持久化 · AI 会话持久化 · Quota schema · 自动 fallback
```
