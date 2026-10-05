# P21 FRONTEND FOUNDATION ACCEPTANCE REPORT

Gate: `P21 FRONTEND FOUNDATION ACCEPTANCE GATE`

Mode: `READ · VERIFY · TEST · REPORT · STOP` (no code modification in this round)

Authorities: `Appendix AL (P21-H01…H11)` · `P21_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md` · real repository, real Git, real database, real browser

## Verdict preview (read this first)

```text
P21 FRONTEND FOUNDATION ACCEPTANCE = BLOCKED

Reason = ONE blocking finding:
  F-P21-ACC-01  Dialog primitive is missing focus containment (Tab leaves the
                dialog) and focus restoration (focus is lost to <body> on close)
                — Gate §35 marks an incomplete Dialog as BLOCKING.

Everything else = PROVEN / PASS (framework, routing, auth round trip, /me contract,
401 recovery, tenant context, API client, correlation, error taxonomy, design tokens,
primitives, forms, responsive shell, security, build, tests, E2E, backend round trip,
Company boundary, Event boundary, regression).

Company UI = NOT IMPLEMENTED · Event UI = OUT OF SCOPE
Backend = UNCHANGED BY THIS ROUND · Migration = NONE
Commit = NO · Tag = NO · Push = NO
HARD STOP = ACTIVE
```

---

## 1. Executive Summary

The Foundation implementation was re-verified from scratch (not from its own report):
source, Git, lockfile, tests, coverage, production build, real browser, and a **real
FastAPI backend round trip** on a disposable isolated database.

What was proven with executed evidence:

```text
typecheck (strict) ................ PASS      (0 @ts-ignore / @ts-nocheck / eslint-disable)
unit + component tests ............ 14 files · 88 tests · 88 passed · 0 failed · 0 skipped
coverage .......................... 89.41% stmts · 88.47% branch · 83.56% funcs · 89.41% lines
production build .................. PASS      (81 modules · html 0.40 kB · css 3.67 kB · js 196.49 kB)
dist secret scan .................. 0 findings · 0 source maps · no VITE_API_TARGET
Playwright E2E .................... 2 passed (boot · anonymous deep link)
browser ↔ real backend ............ POST /sessions 201 through the Vite proxy, UI shows the
                                    real "device not enrolled" outcome
real backend round trip ........... /health 200 · /api/v1/meta 200 · /me anonymous 401 ·
                                    /sessions 201 (+token) · /me authenticated 200 ·
                                    /sessions/refresh 200 · /sessions/logout 200 ·
                                    post-logout /me 401 · Company GET 403 / 401
dependency reproducibility ........ npm ci → 230 packages from package-lock.json (v3)
responsive (390/834/1440) ......... overflowX = 0 at all three widths · 0 console errors
platform/domain boundary .......... platform imports 0 company code · company module imports 0 platform code
Company UI ........................ placeholder only (NOT_IMPLEMENTED)
Event UI .......................... absent
```

What blocked acceptance:

```text
Dialog primitive (src/components/Dialog.tsx, 60 lines) provides role/aria/Escape and
initial focus, but NOT focus containment and NOT focus restoration. Measured in a real
browser with real keyboard input:
  Tab from the last control inside the dialog  → focus lands on "outside-after" (page behind the backdrop)
  Shift+Tab from the first control            → focus lands on "trigger"
  Escape with focus inside the dialog         → dialog closes, focus lands on <body> (not returned)
Gate §35 requires role · focus trap/management · Escape · aria-labelledby ·
aria-describedby · return focus and states: incomplete → BLOCKING.
```

This is a small, isolated defect (no consumer exists yet; ~30 lines + tests). It is
recorded, classified and **not fixed**, because this gate is read-only.

---

## 2. Authority Sources

```text
AGENTS.md                                          (test governance, historical baselines, evidence truth)
docs/architecture/PLATFORM_DECISION_LOG.md         (Appendix AL — P21-H01…H11; append-only tail verified)
docs/architecture/P21_FRONTEND_DISCOVERY_PREP_REPORT.md
docs/architecture/P21_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md  (claim set under test)
apps/frontend/**                                   (package.json · package-lock.json · tsconfig · vite ·
                                                    vitest · playwright · .env.example · src/** · e2e/**)
apps/api/routes/{sessions,identity,meta}.py        (auth transport contract, actually executed)
apps/api/main.py                                   (app factory actually launched)
services/context/model.py                          (/me log-safe field set)
docker-compose.yml · Dockerfile                    (existing local launch path actually used)
tests/integration/wave2_testkit.py                 (existing isolated identity fixture actually used)
```

Repository reality was treated as the final authority; the implementation report was
treated as a claim to be re-measured.

---

## 3. Baseline Integrity

```text
git rev-parse HEAD .................. 08a0485babf0560bc8b7d306c31361b1c1d8bdb5  (= UAP-V0.1.17-P18-CONTROL-PLANE)
git diff --cached ................... 0 (nothing staged, before and after this round)
git tag ............................. 16 (unchanged)
git status --porcelain .............. 207 entries = 16 under apps/frontend/** + 191 non-frontend
git diff --check .................... clean for apps/frontend/**; only the 4 pre-existing CRLF
                                      warnings (docs/api/README.md, docs/architecture/ARCHITECTURE.md,
                                      docs/architecture/DEPENDENCY_RULES.md, docs/security/README.md)
```

The 191 non-frontend entries are the pre-existing uncommitted P15–P20 work plus the P21
discovery/implementation reports. Nothing was cleaned, restored, reformatted, staged or
reverted; no line-ending normalization was performed.

---

## 4. Change Scope

Round-level change classification:

```text
Frontend Foundation authorized ... apps/frontend/package.json · vite.config.ts · src/main.tsx · README.md
Frontend test authorized ......... apps/frontend/src/**/*.test.ts(x) · e2e/boot.spec.ts · src/test/**
Frontend config authorized ....... tsconfig.json · vitest.config.ts · playwright.config.ts · .env.example
                                    · .gitignore · package-lock.json · src/** (app · components · modules · platform)
Documentation/report ............. docs/architecture/P21_*  (this round adds only the acceptance report)
Historical unrelated ............. 190 pre-existing P15–P20 entries (untouched)
Unauthorized ..................... none
```

Backend-family paths (`apps/api/**`, `services/company/**`, `services/consumer/**`,
`apps/worker/**`, `migrations/**`) appear in `git status` **only** as pre-existing
uncommitted work; this round produced no diff in them (see §37 for mtime evidence).

---

## 5. H01–H11 Exactness

| ID | Frozen decision | Verified implementation | Verdict |
| --- | --- | --- | --- |
| H01 | Keep React + Vite + TypeScript, no upgrade | `package.json` `^18.3.1` / `^6.0.5` / `^5.7.2`; resolved 18.3.1 / 6.4.3 / 5.9.3 | PASS |
| H02 | Root = `apps/frontend/` | all 16 changed entries are under `apps/frontend/`; no second frontend tree | PASS |
| H03 | Tenant in URL `/tenants/:tenant_id/...` | `src/app/routing/routes.ts`, `TenantBoundary`, verified in browser | PASS |
| H04 | Reuse existing identity/session, memory-first, no localStorage | `AuthContext` + real `/sessions` round trip; 0 storage APIs in executable source | PASS |
| H05 | Native-fetch typed API client | `src/platform/api/client.ts`; exactly one `fetch(` in the whole source tree | PASS |
| H06 | Context + hooks + local state (no Redux/Zustand) | `AuthContext` · `TenantContext` · `FeedbackProvider`; no state library in `package.json` | PASS |
| H07 | Design tokens + CSS Modules (no UI framework) | `platform/design/{tokens,global}.css` + 8 `*.module.css`; no MUI/AntD/Chakra/Bootstrap/Tailwind | PASS (Drawer absent — see ACC-06) |
| H08 | React Router | `react-router-dom@7.18.4`; `AppRouter` with public/auth · platform · Company layers | PASS |
| H09 | Backend-authoritative permission UX, no ACL engine | `platform/permissions/capability.tsx` always `unknown`; no role/scope inference anywhere | PASS |
| H10 | Vitest + RTL + Playwright | 14 Vitest files (RTL + jest-dom + user-event) and Playwright E2E both executed | PASS |
| H11 | Static SPA + reverse proxy, same-origin `/api` | `vite.config.ts` build block; bundle contains no API target; same-origin calls | PASS |

Architecture-drift scan (Next.js · Nuxt/Vue/Svelte · Redux · Zustand · Axios · Tailwind ·
Material UI · Ant Design · Chakra · Bootstrap · parallel auth system · frontend ACL engine):

```text
dependency list ....... 0 hits
source scan ........... 0 hits (only the comment "Native `fetch` only — no Axios …")
```

---

## 6. Dependencies

```text
lockfileVersion ...................... 3
package.json ↔ lockfile .............. consistent (every declared dependency present in the lockfile root;
                                       npm ci succeeded, which itself proves consistency)
direct dependencies .................. 3 (react · react-dom · react-router-dom)
direct devDependencies ............... 15 (typescript · vite · @vitejs/plugin-react · vitest · coverage-v8 ·
                                       @testing-library/{react,dom,jest-dom,user-event} · jsdom ·
                                       @playwright/test · @types/{node,react,react-dom})
transitive total ..................... 230 packages
unnecessary / duplicate library ...... none found
```

Every direct dependency has a stated Foundation responsibility (AL H01/H08/H10/H45/H47);
`react-router-dom` is the single runtime dependency beyond the STEP-0 skeleton and is
required by AL H08. Forbidden/absent: Cypress, Jest, Redux, Zustand, Axios, Tailwind,
Material UI, Ant Design, Chakra, Bootstrap, MSW.

---

## 7. Reproducibility

```text
node --version ..... v24.18.1
npm --version ...... 12.0.2

npm ci --no-fund --no-audit
  → added 230 packages in 8s  (node_modules rebuilt purely from package-lock.json)
  → warnings: deprecated whatwg-encoding@3.1.1 / glob@10.5.0 (transitive);
              esbuild@0.25.12 postinstall blocked by the host npm install-scripts policy (no functional impact)

npm run build (after npm ci)
  → dist/assets/index-CAUR2bKG.js · dist/assets/index-yrJpwHy2.css
    identical file names/content hashes to the implementation round ⇒ deterministic build
```

No `npm update`, no `npm audit fix`, no `--latest`, no new dependency installed in this round.

---

## 8. TypeScript

```text
tsconfig.json : strict = true · noUnusedLocals · noUnusedParameters · noFallthroughCasesInSwitch ·
                noImplicitOverride · verbatimModuleSyntax · jsx react-jsx · moduleResolution bundler
npm run typecheck → exit 0 (PASS)

static scan over src/** and e2e/**:
  @ts-ignore        = 0
  @ts-nocheck       = 0
  @ts-expect-error  = 0
  eslint-disable    = 0
```

---

## 9. Tests

```text
npm run test:run
  Test Files  14 passed (14)
  Tests       88 passed (88)
  Failed      0
  Skipped     0
  Duration    4.69s
```

Suite composition (14 files): API client · API errors · AuthContext · TenantContext ·
capability boundary · Button · Dialog · states · Table · Field/TextField · ErrorBoundary ·
AppShell · AppRouter · static security scan.

Honesty note: the two "used outside provider" tests intentionally print React error
output to stderr; they assert the thrown guard and pass. No test is skipped or silenced.

---

## 10. Coverage

```text
npm run test:coverage  →  All files  89.41% stmts · 88.47% branch · 83.56% funcs · 89.41% lines
```

Security-relevant boundaries (per file):

| File | stmts | branch | funcs | Uncovered statement lines |
| --- | --- | --- | --- | --- |
| `platform/api/client.ts` | 100 | 100 | 87.5 | — |
| `platform/api/errors.ts` | 100 | 100 | 100 | — |
| `platform/api/correlation.ts` | 66.67 | 50 | 50 | 10–12 (randomUUID fallback path) |
| `platform/auth/AuthContext.tsx` | 87.9 | 72.73 | 50 | 68–73 (fetchMe failure), 84–85 (clientRef null guard), 108–111 (default client wiring), 124 (bootstrap fetch with existing token), 133–134 (device_id passthrough) |
| `platform/tenant/TenantContext.tsx` | 100 | 100 | 100 | — |
| `app/routing/RequireAuth.tsx` | 100 | 100 | 100 | — |
| `app/routing/TenantBoundary.tsx` | 100 | 88.89 | 100 | — |
| `platform/permissions/capability.tsx` | 100 | 100 | 100 | — |
| `components/Dialog.tsx` | 100 | 92.86 | 100 | — |
| `modules/company/index.ts` | 100 | 100 | 100 | — |
| `components/Table.tsx` · `Button.tsx` · `form/Field.tsx` | 100 | 100 | 100 | — |
| `platform/feedback/FeedbackProvider.tsx` | 62.16 | 100 | 50 | 34–70 (toast rendering/dismiss) |
| `platform/feedback/states.tsx` | 62.07 | 33.33 | 33.33 | 6–19, 39 (LoadingIndicator/GlobalError) |
| `app/App.tsx` | 0 | 0 | 0 | composition root (exercised by E2E, not by unit tests) |
| `main.tsx` | 0 | 100 | 100 | entry bootstrap (exercised by E2E) |

Verdict on the §10 question ("is the low-coverage area exactly the critical security
boundary?"): **no**. The critical boundaries (API client, error normalisation, tenant
context, route guard, capability boundary) are 100%. The gaps are AuthContext edge
branches, the presentation feedback layer and the composition root. They are recorded as
evidence gaps (ACC-04, ACC-05), not as blocking.

Note: the implementation report recorded branch coverage 88.53%; this acceptance run
measures 88.47% for the same suite (v8 branch accounting). The difference (0.06 pp) is
immaterial and does not change any verdict; the acceptance number is authoritative here.

---

## 11. Build

```text
npm run build  → npm run typecheck && vite build
  vite v6.4.3 · 81 modules transformed
  dist/index.html                0.40 kB │ gzip 0.27 kB
  dist/assets/index-*.css        3.67 kB │ gzip 1.19 kB
  dist/assets/index-*.js       196.49 kB │ gzip 64.86 kB
  source maps                    0 (sourcemap: false)
```

`apps/frontend/.gitignore` covers `node_modules/`, `dist/`, `coverage/`, `.vite/`,
`playwright-report/`, `test-results/` — no build artifact entered Git status.

---

## 12. E2E

```text
npm run e2e   → webServer: vite preview --port 4173 --strictPort --host 127.0.0.1
  ok 1  the console boots and routes an anonymous visitor to sign-in
  ok 2  unauthenticated deep links fall back to sign-in instead of a blank page
  2 passed (3.5s)
```

Scope honesty: the checked-in E2E covers **boot + anonymous routing only**. It is not
reported here as auth/backend E2E. The auth/backend evidence comes from the separate
real-backend round trip and the real-browser login run described in §34/§13.

Additional real-browser observations (same session, dev server + real backend):

```text
GET /            (anonymous)  → http://localhost:5199/login   · heading "Sign in to UAP Console"
GET /tenants/<uuid>/company (anonymous) → /login               · heading "Sign in to UAP Console"
console errors / page errors   → 0
```

---

## 13. Authentication

Source contract (verified against `apps/api/routes/sessions.py`, then executed):

```text
POST /sessions          {login,password,device_id?} → 201; token ONLY with a verified device
POST /sessions/refresh  (Bearer) → 200 session/expiry view
POST /sessions/logout   (Bearer) → 200 {"revoked": n}
GET  /me                (Bearer) → 200 frozen log-safe context | 401 | 403
```

Frontend behaviour (unit tests + real backend):

```text
bootstrap      : no persisted token ⇒ unauthenticated, zero API calls (tested)
login (no dev) : backend 201 credential_verified without token ⇒ 'device_required' (tested + real)
login (device) : backend 201 session_verified + token ⇒ 'authenticated' (real backend)
refresh        : single in-flight attempt, concurrent callers de-duplicated (tested)
logout         : best-effort call, local state always cleared (tested + real 200)
no identity invention / fake session / employee login / role-name-as-auth  (source scan: absent)
```

---

## 14. `/me`

Real, authenticated `GET /me` against the launched FastAPI app (isolated DB, real session):

```json
{
  "correlation_id": "p21-acc-1",
  "session_id": "01a1051b-540f-754f-87aa-d8501a54d047",
  "device_id": "01a1051a-6cd6-7a47-a72f-d3cb84863c33",
  "identity_id": "01a1051a-6b58-7849-a308-66ba2895263c",
  "user_id": "01a1051a-6b55-7372-8390-8836b73a5dd5",
  "tenant_id": "01a1051b-5398-757e-86a0-6e9a11bb7ffd",
  "space_id": "01a1051b-539b-7cf2-8da5-e99d6c953845",
  "subject_type": "USER",
  "scope": "SPACE",
  "authentication_assurance": "session_verified"
}
```

* The 10 returned field names are **exactly** the fields modelled by
  `src/platform/api/types.ts::MeResponse` — no invented field, no missing field.
* `GET /me` anonymous → `401 {"detail":"authentication failed"}`.
* `GET /me` with a valid token but **no tenant/space membership** → `403 {"detail":"permission denied"}`
  (context resolution is authorization-bound, not merely authentication-bound).
* `correlation_id` echoed the caller's `x-correlation-id` header verbatim.
* `scope` is consumed only as context; the frontend never maps `scope` to permissions or
  roles (source scan: no such mapping exists).

---

## 15. 401 Recovery

```text
client unit tests:
  401 → onUnauthorized called exactly once → original request retried once (same correlation id)
  second 401 after recovery → surfaces AUTH_REQUIRED, onUnauthorized still called exactly once (no loop)
  recovery failure → AUTH_REQUIRED
context unit tests:
  concurrent refresh() → exactly one POST /sessions/refresh
  refresh failure → token cleared, user cleared, status unauthenticated
real backend:
  /me without token → 401  ·  token after /sessions/logout → 401  ·  bad password → 401
```

---

## 16. Token Boundary

```text
token storage ......... React ref (memory only) — never localStorage/sessionStorage
browser scan .......... 0 executable uses of localStorage/sessionStorage (1 documentation comment)
document.cookie ....... 0 uses (nothing written, nothing read, no cookie value copied into JS state)
persistence on reload . none by design: a fresh load starts unauthenticated
```

---

## 17. Tenant Context

```text
URL tenant → TenantBoundary (uuid validation) → shared TenantContext → API path tenant
tests: valid tenant mirrored · tenant change followed · invalid blocked (TenantUnresolved) ·
       context cleared when the boundary unmounts (sibling probe proves the shared value)
single context: no second tenant store exists; nothing outside the route boundary can set it
```

No client-side authorization is derived from the tenant: the URL tenant is context only.

---

## 18. Tenant Switching

```text
Implemented   : URL-driven switch — navigating /tenants/A/company → /tenants/B/company
                updates the shared context to B (verified by test with two different uuids)
Not implemented: a tenant-switcher UI control, and per-request tenant path injection for
                domain modules (no domain module calls an API yet)
Classification : NOT YET IMPLEMENTED / Company stage — per Gate §19 this is not a defect
```

---

## 19. API Client

`src/platform/api/client.ts` (single owner; verified by reading the source and by tests):

```text
base URL (same-origin default) · auth transport (Bearer from memory) · headers ·
x-correlation-id · 15 s timeout + caller AbortSignal (AbortController) · JSON parsing
(204 → undefined, unreadable → safe UNKNOWN_ERROR) · typed responses · error normalization
(401/403/409/422/503/unknown/network) · at-most-one 401 recovery

`fetch(` occurrences in the entire source tree = 1  (the client itself)
No SQL · no ORM · no PostgreSQL driver · no backend package import · no filesystem access
in application code (the only `node:fs` use is the static security test).
```

Cancellation: the client aborts on caller signal and timeout and never touches React
state itself; no React component performs requests yet, so "state update after unmount"
has no call site to occur at (recorded, not claimed as exercised).

---

## 20. Correlation

```text
header on every request (incl. the retry after 401 recovery, which reuses the same id) — tested
override supported via request options — tested
surfaced to the user only as a reference string in ErrorState / GlobalError — tested
real backend echo verified: x-correlation-id "p21-acc-1" → /me `correlation_id`: "p21-acc-1"
never displayed: stack trace · SQL · table/constraint · internal exception (asserted by tests)
```

---

## 21. Errors

```text
401 → AUTH_REQUIRED · 403 → ACCESS_DENIED · 409 → CONFLICT · 422 → VALIDATION_OR_NOT_FOUND ·
503 → SERVICE_BOUNDARY_ERROR · transport → NETWORK_ERROR · unmapped → UNKNOWN_ERROR

messageForCode(): every code yields a safe, human-readable message (asserted not to contain
sql/constraint/traceback/psycopg/stack)
422 compatibility with the Company API taxonomy: mapping asserted by unit test; the backend's
own 422 validation/not-found behaviour was frozen and accepted at P20 Company API Acceptance
(no new backend 422 was produced in this round; real 401/403 were)
no competing taxonomy invented
```

---

## 22. Permission Boundary

```text
platform/permissions/capability.tsx : capabilityAvailability() === 'unknown' (always)
CapabilityHint : presentation only (render / hide), never a security decision
source scan for role === "admin", scope === "platform" ⇒ all-permissions shortcuts: 0 hits
no frontend ACL engine, no permission-inference table, no role-permission replica
`/me` returns no permission set (verified against the real response in §14)
```

---

## 23. Platform / Domain Boundary

Static import-graph analysis (production files only):

```text
src/platform/**   imports: react + own siblings              → 0 imports of company/app/components
src/components/** imports: react + CSS + own siblings        → 0 imports of platform/modules
src/app/**        imports: platform · components · modules/company · react-router-dom
src/modules/company/index.ts: 0 imports (constants only)
```

```text
Platform can exist without Company ......... yes (no reference in either direction)
Company can consume Platform ................ yes (via the app composition layer)
Platform does not depend on Company ........ yes (0 hits)
```

No bidirectional dependency; no BLOCKING architecture failure.

---

## 24. Extension Boundary

```text
dynamic plugin loader / remote component loader / schema DSL / code injection /
database-driven component execution: 0 hits in source and dependencies
Extension model present = controlled extension points only:
  routes table (src/app/routing/routes.ts) · provider composition (src/app/App.tsx) ·
  shared primitives + design tokens · tenant boundary · error/feedback layer
Future-module feasibility: a second module needs no change to platform/auth · platform/tenant ·
  platform/api · platform/design (verified by import-graph analysis; no fixture module created)
```

No second business module was created (Gate §27).

---

## 25. Design System

```text
tokens.css : color(surface/text/muted/border/accent/success/warning/danger/focus) · spacing ·
             radius · typography · elevation · motion · documented breakpoints
global.css : reset + body/font defaults + :focus-visible outline only
CSS Modules: 8 component/shell modules; total stylesheets 11
!important occurrences: 0 · no Company-only global CSS · no global selector explosion
```

---

## 26. UI Primitives

```text
present : Button · Input · Select · Dialog · Card · Badge · Table · PageHeader ·
          EmptyState · LoadingState · ErrorState · Field/FieldError/TextField
business nouns in primitives: 0 (only doc comments / test fixture text)
predictable API: props typed, loading/disabled where relevant, no domain coupling
```

Observation ACC-06: AL.2 H07 names `Drawer` in its primitive list; no Drawer exists. The
implementation instruction's required set (P21 §33) does not include it and no consumer
exists yet, so this is an OBSERVATION for the Company UI stage, not a blocker.

---

## 27. Forms

```text
Field/TextField: label `for` ↔ control id association · aria-describedby (hint + error) ·
aria-invalid on error · FieldError role="alert" · no placeholder-only labelling
verified by executed tests (association, invalid state, error relation, typing)
```

---

## 28. Dialog

Measured in a real browser with real keyboard input (component loaded from the dev-server
module graph; no repository file was added):

```text
role="dialog" ........................ PROVEN      (getAttribute → "dialog")
aria-modal ........................... PROVEN      ("true")
aria-labelledby → accessible name .... PROVEN      ("Confirm suspension")
aria-describedby ..................... PROVEN      (present when description is supplied)
Escape closes ........................ PROVEN      (dialog detached)
initial focus inside the dialog ...... PROVEN      (activeElement = dialog surface)
focus containment (Tab / Shift+Tab) .. FAIL        Tab from last inner control → "outside-after";
                                                   Shift+Tab from first inner control → "trigger"
return focus on close ................ FAIL        focus inside dialog + Escape → activeElement = BODY
```

Source confirmation: `src/components/Dialog.tsx` (60 lines) contains no Tab handling, no
sibling `inert`/`aria-hidden`, no previously-focused-element capture/restore. The existing
tests assert only the parts that do work.

```text
Classification: BLOCKING (Gate §35: an incomplete Dialog is BLOCKING because
Suspend / Terminate / End Assignment depend on it)
Scope: src/components/Dialog.tsx (+ Dialog.test.tsx) — no platform, API, backend or
       authorization change required
```

---

## 29. Accessibility

```text
keyboard reachable + Enter activation ............ tested (Button)
visible focus .................................... :focus-visible outline in global.css; observed in browser
labels / invalid / error association ............. tested (Field)
live regions (loading, toasts) ................... tested (LoadingState, Table loading)
non-color-only status ............................ tested (Badge text)
dialog semantics ................................. PROVEN except containment/return focus (§28)
no accessibility tooling dependency was added; no automated axe audit was run
```

---

## 30. Responsive

Measured in a real browser against the real app (login + shell surfaces):

| Viewport | Width | Horizontal overflow | Control sizing | Console errors |
| --- | --- | --- | --- | --- |
| mobile | 390 | 0 px | input 356 px · button 83×41 | 0 |
| tablet | 834 | 0 px | input 800 px · button 83×41 | 0 |
| desktop | 1440 | 0 px | input 1406 px · button 83×41 | 0 |

Shell CSS collapses to a single column at `max-width: 767px`, consistent with the
documented token breakpoints. Not verified at runtime this round: table horizontal
overflow behaviour and dialog-at-narrow-viewport (no rendered consumer exists yet).
Observation ACC-03: `Table.module.css` has no `overflow-x` container, so a wide table
will overflow its parent on narrow screens — recommend a scroll wrapper when the Company
UI consumes it (non-blocking, no consumer today).

---

## 31. Production Deployment

```text
model: Browser → same-origin static SPA → /api → reverse proxy → FastAPI   (AL H11)
evidence: build block has no API base; bundle contains no VITE_API_TARGET / localhost:8000;
          runtime calls are relative, same-origin paths (credentials: 'same-origin')
no browser cross-origin API dependency, no CORS dependency, no development-only private
configuration in the bundle
no static-mount or proxy configuration ships from the frontend repository (deployment-owned)
```

---

## 32. Dev Proxy

Real proxy round trip (dev server on :5199 with `VITE_API_TARGET=http://127.0.0.1:8000` → real FastAPI):

```text
GET  /health                     → 200  {"status":"ok","version":"0.1.17",...}
GET  /ready                      → 503  (schema component ok; migration component "expected revision is
                                         missing or invalid" — the verify image carries no build revision
                                         artifact; environment artifact, not a backend defect)
GET  /api/v1/meta                → 200  real payload
GET  /me                         → 401  {"detail":"authentication failed"}
POST /sessions (no device)       → 201  credential_verified, no token
POST /sessions (bad password)    → 401
POST /sessions (verified device) → 201  session_verified + token + expiry
POST /sessions/refresh           → 200
POST /sessions/logout            → 200  {"revoked":1}
GET  /me (after logout)          → 401
```

Verdict: dev proxy is real and working for `/api`, `/health`, `/ready` and the auth surface.

**Finding ACC-02 (NON-BLOCKING, should be fixed before Company UI):** the proxy list does not
include the Company namespace `/company/**`. Requests through the dev server returned the
SPA (`200 text/html`) instead of reaching the backend:

```text
GET /company/tenants/<uuid>/employees  (through dev server) → 200 SPA HTML
GET /company/tenants/<uuid>/employees  (direct to backend)  → 403 with token · 401 anonymous
```

The Foundation never calls `/company`, so Foundation Acceptance is unaffected, but the next
stage must extend the dev proxy (or the platform must define a single API prefix).

---

## 33. Security

```text
localStorage / sessionStorage .......... 0 executable uses (1 documentation comment)
document.cookie = ...................... 0
eval( / new Function( .................. 0
dangerouslySetInnerHTML / innerHTML = .. 0
secrets in src ......................... 0 (postgres://, sk-…, PRIVATE KEY, jwt_secret,
                                            DATABASE_URL, DB_PASSWORD, SECRET_KEY)
secrets in dist ........................ 0 (same pattern set + VITE_API_TARGET + localhost:8000)
.env.example ........................... exactly one public key (VITE_API_TARGET), no secret assignment
production bundle API target ........... absent (production does not depend on VITE_API_TARGET)
backend access from the browser tree ... 0 (no SQL/ORM/driver/fs in application code)
npm ci scripts policy .................. esbuild postinstall blocked by host policy; build/test/E2E
                                         still pass (recorded, no dependency change)
```

Negative matrix (Gate §56) — each row is backed by the evidence named in §9/§13/§34:

| Scenario | Expected | Observed |
| --- | --- | --- |
| anonymous protected route | auth flow | redirect to `/login` (test + browser) |
| expired/revoked auth | refresh / logout | post-logout `/me` 401; refresh failure clears auth (test + real) |
| backend 403 | access denied | real 403 for Company GET and membership-less `/me` |
| backend 409 | conflict | mapped to CONFLICT (unit test; backend behaviour frozen at P20) |
| backend 422 | validation/not-found | mapped to VALIDATION_OR_NOT_FOUND (unit test; P20-frozen backend) |
| backend 503 | service boundary | mapped to SERVICE_BOUNDARY_ERROR (unit test; real `/ready` 503 observed) |
| tenant mismatch | no client-side trust | URL tenant is context only; backend decides |
| token persistence | forbidden | 0 storage APIs |
| secret in bundle | forbidden | 0 findings |
| unsafe HTML | forbidden | 0 findings |
| worker identity | irrelevant to frontend | no worker code/UI present |
| Company Event UI | absent | 0 hits for event UI terms |

---

## 34. Backend Round-trip (F-P21-FND-04)

Method (no source change, no migration file, no formal/shared DB mutation):

```text
isolated database ...... uap_p21_fnd04 (created for this gate, dropped afterwards)
migration identity ..... uap_migrator via alembic → head 0020_p20_company_authorization
privileges ............. scripts.privileges.materialize (additive) → 29 grant rows
fixture identity ....... uap_runtime via tests/integration/wave2_testkit.provision_active_user
isolation .............. the verification container joined the postgres network namespace
                         (localhost trust); the API container joined the compose bridge so the
                         host browser and dev proxy could reach it on 8000
API launch path ........ existing project path: uvicorn apps.api.main:app (Dockerfile CMD),
                         DATABASE_URL = the documented local-development DSN of docker-compose
```

Results (real HTTP, real database, real authorization):

```text
POST /sessions (no device)        → 201 {"authentication_assurance":"credential_verified"} (no token)
POST /sessions (wrong password)   → 401 {"detail":"authentication failed"}
POST /sessions (verified device)  → 201 {"authentication_assurance":"session_verified", token, expiry}
GET  /me (Bearer, no membership)  → 403 {"detail":"permission denied"}
GET  /me (Bearer + membership)    → 200 with the 10 frozen log-safe fields (§14)
POST /sessions/refresh            → 200 {session_id, expires_at, absolute_expires_at}
GET  /company/.../employees       → 403 (membership without a Company grant) / 401 anonymous
POST /sessions/logout             → 200 {"revoked":1}
GET  /me (after logout)           → 401
```

Frontend-origin evidence (browser → Vite proxy → FastAPI):

```text
POST http://localhost:5199/sessions  → 201 · response keys [user_id, identity_id,
                                        authentication_assurance] · UI rendered
                                        "Credentials verified, but this device is not enrolled…"
```

Environment hygiene (proven, not assumed):

```text
formal DB `uap`         prestate = public tables 0   · poststate = public tables 0  (unchanged)
shared DB `uap_b1_test` prestate = alembic 0017_p13_seed · tenants 0 · spaces 0 · roles 1 ·
                                      users 0 · audit 0 · events 0
                        poststate = identical (no residue)
one failed fixture attempt: a shared-test-DB helper was invoked by mistake, failed on a foreign
key inside its single transaction and rolled back completely — verified by direct counts
immediately afterwards (shared DB still at the frozen baseline)
database list           before = {uap, uap_b1_test, uap_test} + uap_p21_fnd04
                        after  = {uap, uap_b1_test, uap_test}  (isolated DB dropped by name)
containers              uap-p21-api created and removed; no residue
```

FND-04 status:

```text
F-P21-FND-04 = CLOSED
Scope of closure: Auth/API transport, 401/403 behaviour, /me contract (real 200 payload),
token issuance/refresh/logout, and a browser-origin request path are all proven against a
real FastAPI backend.
Explicit residual: a browser-rendered *authenticated* console session is not reachable in
the Foundation — the platform issues a session only for a verified device (frozen P17/P18
contract) and P21 ships no device-enrollment UI, while the token is memory-only by design
(AL H04). That is a design boundary, not a missing integration; see ACC-08.
```

---

## 35. Company Boundary

```text
src/modules/company/index.ts ..................... COMPANY_MODULE_STATUS = 'NOT_IMPLEMENTED'
                                                   COMPANY_MODULE_SCOPE  = 4 placeholder entries
/tenants/:tenant_id/company ...................... placeholder page only (status · tenant · scope list)
employee/assignment page · form · list · API call 0
/tenants/<uuid>/company/employees ................ 404 (no such route)
Company API integration in the frontend .......... 0
```

---

## 36. Event Boundary

```text
Event Center · Event Timeline · Handler Console · Allowlist Admin · Worker Console ... 0 files / 0 hits
frontend producer / handler / worker references ..................................... 0
production allowlist read or written by this round .................................... no
P20 Event state asserted (not re-measured this round): accepted-but-inactive ·
  production allowlist EMPTY · worker NOT AUTHORIZED
```

---

## 37. Regression

```text
this round's code changes .......... none (read-only gate; only this report was written)
backend/API/migration/authorization . no diff introduced by this round

mtime evidence (round activity window ≈ 12:01–12:30; backend artifacts are older):
  apps/api/main.py                                2026-10-02 17:27:15
  apps/api/routes/company.py                      2026-10-02 17:27:14
  domains/company/manifest.py                     2026-10-02 16:45:04
  migrations_alembic/versions/0019_p20_company.py 2026-10-02 16:01:44
  services/consumer/kernel.py                     2026-10-04 11:16:12
  docs/architecture/PLATFORM_DECISION_LOG.md      2026-10-04 11:33:42

frontend gates re-run this round: typecheck PASS · 88/88 tests PASS · build PASS · E2E PASS
backends/DB untouched (see §34 hygiene)
```

---

## 38. Historical Dirty State

```text
190 pre-existing non-frontend entries existed at the start of this round
+1 P21 discovery/implementation report (previous round) = 191 during acceptance
this round adds exactly +1 authorized document (this report)

not touched · not staged · not reverted · not reformatted · no line-ending normalization
git diff --cached = 0 · HEAD unchanged (08a0485babf0560bc8b7d306c31361b1c1d8bdb5)
```

These entries are historical context, not P21 regressions.

---

## 39. Findings

```text
F-P21-ACC-01  BLOCKING  (new — the single reason acceptance is BLOCKED)
  Subject : Dialog primitive lacks focus containment and focus restoration.
  Evidence: browser measurement — Tab from last inner control → "outside-after";
            Shift+Tab from first inner control → "trigger"; Escape with focus inside →
            activeElement = BODY. Source: Dialog.tsx has no trap / inert / restore logic.
  Authority: Gate §35 (role · focus trap/management · Escape · aria-labelledby ·
            aria-describedby · return focus) → incomplete is BLOCKING; §59 lists an
            unsafe component primitive as a blocking class.
  Impact  : Suspend / Terminate / End Assignment dialogs will be non-modal for keyboard
            and screen-reader users; focus is lost on close.
  Fix scope (next authorized round): src/components/Dialog.tsx + Dialog.test.tsx only.

F-P21-ACC-02  NON-BLOCKING  (should be fixed before/within Company UI)
  Subject : the Vite dev proxy does not cover the Company namespace `/company/**`.
  Evidence: through the dev server `/company/...` returned SPA HTML (200 text/html) while the
            same path direct to the backend returned 403 (token) / 401 (anonymous).
  Impact  : Company UI development would silently receive HTML instead of API responses.
  Fix scope: apps/frontend/vite.config.ts proxy list (+ the Company UI stage's own settings).

F-P21-ACC-03  NON-BLOCKING
  Subject : Table has no horizontal-overflow container; wide tables will overflow narrow viewports.
  Evidence: Table.module.css has no overflow-x / scroll wrapper; the 390 px measurement
            passes only because no table is rendered yet.
  Fix scope: src/components/Table.tsx (or a wrapper) when the Company UI consumes it.

F-P21-ACC-04  NON-BLOCKING (evidence gap)
  Subject : AuthContext uncovered branches — fetchMe failure (68–73), clientRef null guard
            (84–85), default client wiring (108–111), bootstrap fetch with token (124),
            device_id passthrough (133–134).
  Note    : 108–111 is exercised end-to-end by the real-browser login run (outside the coverage
            instrumentation); 68–73 remains unexercised.
  Fix scope: AuthContext.test.tsx.

F-P21-ACC-05  NON-BLOCKING (evidence gap)
  Subject : the feedback layer is the least-covered production code (FeedbackProvider 62%,
            states 62%) — no test asserts a toast render/dismiss or GlobalError retry.
  Fix scope: platform/feedback tests.

F-P21-ACC-06  OBSERVATION
  Subject : AL.2 H07 names a `Drawer` primitive; none exists. The required-set instruction
            (P21 §33) omitted it and no consumer exists; re-decide in the Company UI stage.

F-P21-ACC-07  OBSERVATION (environment)
  Subject : /ready answered 503 because the verification image carries no build revision
            artifact ("expected revision is missing or invalid"). The schema component was ok;
            this is image/build-artifact state, not a frontend or backend defect.

F-P21-ACC-08  OBSERVATION (by design)
  Subject : a browser-rendered authenticated session is not reachable in the Foundation —
            sessions require a verified device (frozen P17/P18) and the Foundation ships no
            device-enrollment UI; tokens are memory-only (AL H04). Real token issuance and the
            real /me payload were proven at the transport layer instead (§34/§14).

F-P21-ACC-09  OBSERVATION (environment)
  Subject : host npm policy blocks the esbuild postinstall script; typecheck, tests, build and
            E2E all pass regardless. No dependency change was made.
```

No finding of the "auth boundary broken", "tenant mismatch possible", "secret exposure",
"frontend ACL acts as authority", "Platform depends on Company", "API client cannot integrate
backend", "build/typecheck/test failure" classes was found.

---

## 40. Acceptance Matrix

Status vocabulary used: `PROVEN` · `PASS` · `PARTIAL` · `MISSING` · `BLOCKED` · `NOT APPLICABLE`.

| Area | Status | Evidence |
| --- | --- | --- |
| Framework | PROVEN | React 18.3.1 + Vite 6.4.3 + TypeScript 5.9.3 from the lockfile via `npm ci` |
| Routing | PROVEN | `AppRouter` tests + browser: `/`→login, deep link→login, 403/404 |
| Auth | PROVEN | real `POST /sessions` 201 (credential_verified and session_verified + token) |
| 401 Recovery | PROVEN | client one-shot retry tests + real 401s (anonymous, bad password, post-logout) |
| Tenant | PROVEN | URL→context tests (valid / change / invalid / clear) + browser deep link |
| API Client | PROVEN | single `fetch(` owner; transport/abort/timeout/error-normalisation tests |
| Correlation | PROVEN | header tests + real backend echo of `x-correlation-id` |
| Error Taxonomy | PROVEN | 401/403/409/422/503 mapping tests + real 401/403/503 observed |
| Design Tokens | PROVEN | `tokens.css` inventory; 0 `!important`; CSS Modules only |
| Primitives | PARTIAL | 12 primitives verified; **Dialog focus containment/restore missing** (ACC-01) |
| Accessibility | PARTIAL | labels/keyboard/live regions proven; dialog trap + return focus fail |
| Responsive | PARTIAL | 3 viewports measured overflow-free; table-overflow and dialog-at-width unverified |
| Permission Boundary | PROVEN | capability always `unknown`; no inference/ACL; `/me` has no permission set |
| Platform/Domain Boundary | PROVEN | import graph: platform→company = 0, company→platform = 0 (via app) |
| Extensibility | PROVEN | controlled extension points only; no dynamic loader/DSL; no second module created |
| Security | PROVEN | storage/eval/HTML/secret scans = 0; memory-only token; no backend access |
| Build | PROVEN | deterministic dist, no source maps, 0 secrets |
| E2E | PROVEN | 2/2 Playwright + browser boot/deep-link/console-clean |
| Backend Round-trip | PROVEN | isolated DB + real FastAPI: sessions/me/refresh/logout/403/401 (§34) |
| Company Boundary | PROVEN | placeholder only; no employee/assignment UI or API call |
| Event Boundary | PROVEN | 0 event/handler/allowlist/worker UI |
| Regression | PROVEN | no backend change this round; all frontend gates re-run green |

No cell is `DESIGN ONLY` presented as implemented.

---

## 41. FND-04 Closure

```text
F-P21-FND-04 = CLOSED

Closed by  : real FastAPI backend on an isolated disposable database, real HTTP through the
             dev proxy, real browser request path, real /me payload, real 401/403/refresh/logout.
Not closed by: ECONNREFUSED reasoning, mocks or fixture-only assertions.
Residual   : browser-authenticated render (ACC-08, by design) — documented, not a substitute claim.
Environment restored: isolated DB dropped · API container removed · dev/preview servers stopped ·
             temp files removed · formal and shared DBs verified unchanged.
```

---

## 42. Final Verdict

```text
P21 FRONTEND FOUNDATION ACCEPTANCE = BLOCKED

Blocking findings:
  F-P21-ACC-01 — Dialog primitive: focus containment + focus restoration missing (§35 BLOCKING)

Everything else:
  App Shell        = ACCEPTED-READY (PROVEN)
  Routing          = ACCEPTED-READY (PROVEN)
  Auth             = ACCEPTED-READY (PROVEN, real backend)
  Tenant           = ACCEPTED-READY (PROVEN)
  API Client       = ACCEPTED-READY (PROVEN, real backend)
  Error System     = ACCEPTED-READY (PROVEN)
  Design System    = ACCEPTED-READY (PROVEN)
  Primitives       = BLOCKED by ACC-01 (Dialog only)
  Testing          = ACCEPTED-READY (PROVEN; two evidence gaps recorded)
  Platform/Domain  = ACCEPTED-READY (PROVEN)

Company UI   = NOT IMPLEMENTED   (not accepted, not authorized by this gate)
Event UI     = OUT OF SCOPE
Backend      = UNCHANGED BY THIS ROUND
Migration    = NONE
Commit = NO · Tag = NO · Push = NO
HARD STOP = ACTIVE

Acceptance semantics: IMPLEMENTED is not ACCEPTED. The Foundation is implemented and almost
fully evidenced, but acceptance cannot be granted while a Gate-declared BLOCKING item is open.
```

Recommended next authorized round (small and bounded):

```text
P21 FRONTEND FOUNDATION CORRECTION
  → src/components/Dialog.tsx        (focus containment + focus restoration)
  → src/components/Dialog.test.tsx   (trap, reverse-tab, return focus)
  optional in the same round: F-P21-ACC-04/05 test additions · F-P21-ACC-02 dev-proxy entry
then re-run: typecheck · test:run · test:coverage · build · e2e · browser dialog probe
then: P21 FRONTEND FOUNDATION ACCEPTANCE (re-entry)
```

`P21 COMPANY UI IMPLEMENTATION` must not start until acceptance passes.

---

## 43. Hard Stop

```text
HARD STOP = ACTIVE
```

This round performed read-only verification, executed tests/build/E2E, ran a real backend
round trip on a disposable isolated database, restored the environment, and wrote exactly one
authorized document (this report). It did not fix, refactor, install dependencies, extend the
API, implement Company UI, implement Event UI, or touch the backend, migrations, the formal
database, the shared test database, Git history or any release artifact. No commit, tag or
push was created.
