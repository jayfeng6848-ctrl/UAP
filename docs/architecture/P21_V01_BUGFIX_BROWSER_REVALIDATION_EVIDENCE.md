# LOG ENTRY — 2026-10-05 — P21 / V-01 Bug Fix + Browser Revalidation

## Authorization

```
Human Decision / Bug-Fix + Revalidation：
  FIX V-01 · RUN RELEVANT TESTS · RUN REAL CHROMIUM E2E · VERIFY NETWORK ·
  VERIFY COPILOT TERMINAL STATE · APPEND RECORDBOOK · STOP
唯一授权源码变更：apps/frontend/vite.config.ts（新增 /intelligence 代理，复用 API_TARGET）
唯一授权测试变更：Company Copilot 浏览器 E2E 断言
NO COMMIT / TAG / PUSH / RELEASE / DB CHANGE / AI CHANGE
```

## Baseline → After

```
BEFORE: HEAD=e20b35f83a1912b0f051d8d0d2d7009f0ee6f7f9 · main · staged=0 · porcelain=240 · diff --check 干净
AFTER : HEAD 同 · staged=0 · porcelain=240 · 本轮 changed files = **仅 apps/frontend/vite.config.ts**
```

## V-01 FIX

```
apps/frontend/vite.config.ts：在 '/ai/' 之后新增
  '/intelligence': { target: API_TARGET, changeOrigin: true }
理由：与 /api · /company · /ai 等既有开发代理保持一致；复用同一 API_TARGET（未新增第二个 target）；
      不改 production API routing / backend endpoint / API contract / AI runtime。
E2E 断言调整（同一轮授权）：终态判定改为「先等 /intelligence 网络响应，再等有效终态」——
      有效终态 = 渲染出的状态行 或 设计内的客户可读失败提示；不再以预先存在的元素做断言，
      未放宽 timeout，未删除 Copilot 覆盖。
```

## NETWORK EVIDENCE（真实 Chromium，同 origin）

```
POST /intelligence/tenants/{t}/assistant/runs
  status = 201 · server = uvicorn · content-type = application/json · duration = 148 ms
  → 从 http://localhost:5173 发出并**到达 backend**（无 Vite 404，无空响应）
代理回归（同 origin 探针）：
  /intelligence/... → 401 application/json（uvicorn）
  /company/...      → 405 application/json（uvicorn，allow: GET）
  /ai/connection    → 422 application/json（uvicorn）
  → 三者互不覆盖、无代理冲突
证据文件不含 token / cookie / API key / Authorization 值（仅 method·path·status·duration·content-type·server）
```

## BROWSER E2E / COPILOT TERMINAL STATE

```
真实 Chromium（Desktop Chrome · 1280×800）：
  login → tenant Company → Copilot → 输入问题 → 发送
  → POST /intelligence 到达 backend（201）
  → 面板进入有效终态：**"状态：FAILED"**（copilot-status 渲染）
  → page_errors = [] · 无挂起 · 无 JS 崩溃 · 无意外跳转
结果：**1 passed / 0 failed**（904 ms）
说明：无真实 AI credential 时 CREDENTIAL_UNAVAILABLE 属设计内 fail-closed 终态，未伪造成功。
```

## TESTS

```
vitest（allowlist）：P21Surfaces + api + security                → 15 passed / 0 failed / 0 skipped
npm run typecheck                                               → exit 0
playwright（V-01 revalidation）                                  → 1 passed
临时夹具清理：e2e-validation/ · playwright.validation.config.ts · test-results/ 全部删除，residue=False
```

## SECURITY / DATABASE / ARCHITECTURE / GIT

```
Security：无 secret 暴露（证据不含凭据）；代理仅转发字节，不保存/不注入 provider secret；
          无 tenant/scope override；无授权绕过；无 raw prompt 泄漏
Database：DDL=0 · DML=0 · migration=0 · role changes=0 · permission changes=0 · membership changes=0
          仅 runtime append-only：agent_runs 13→15 · audit_logs 191→198（ai_request_logs=3 未变）
          roles=14 · role_permissions=92（未变）
Architecture：本轮未改任何后端/前端业务代码；Core → Domain 未受影响
Git：仅 apps/frontend/vite.config.ts 变更；历史 dirty work 未丢失；未 add -A / clean / reset / restore
```

## V-01 FINAL STATUS

```
V-01 = **CLOSED**
  /intelligence dev proxy works ✓ · browser reaches backend ✓ ·
  Copilot reaches valid terminal state ✓ · E2E passes ✓ · no regression ✓
```

## Gate / Next step

```
GATE-A = PASS · GATE-B = EXTERNAL ENVIRONMENT BLOCK（真实 Cloud credential / 真实 Local model 仍缺）
P21 COMPANY UI ACCEPTANCE：GATE-A 全绿；GATE-B 仅剩外部环境项 → 需重新执行 P21 Company UI Acceptance
NEXT：P21 COMPANY UI ACCEPTANCE（重跑，重点 Browser Copilot + AI terminal state）
COMMIT / TAG / PUSH / RELEASE / PRODUCTION AI / P22 = NOT AUTHORIZED · HARD STOP = ACTIVE
```

# LOG ENTRY END
