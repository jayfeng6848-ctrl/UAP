# P21 FRONTEND FOUNDATION IMPLEMENTATION REPORT

Stage: `P21 FRONTEND FOUNDATION IMPLEMENTATION`

Authority: `P21 FRONTEND ARCHITECTURE = APPROVED` · `Appendix AL = FROZEN` · `P21-H01 … P21-H11`

Result: `P21 FRONTEND FOUNDATION IMPLEMENTATION = PASS`

Scope boundary (unchanged, re-affirmed):

```text
Company UI                = NOT AUTHORIZED  (placeholder only)
Company feature           = NOT AUTHORIZED
Event UI                  = OUT OF SCOPE
Production Event          = NOT AUTHORIZED
Worker UI                 = NOT AUTHORIZED
Backend / API / Migration = NOT MODIFIED
Authorization model       = NOT MODIFIED
Commit / Tag / Push       = NO
```

---

## 1. Executive Summary

The frontend foundation for UAP Console is implemented inside `apps/frontend/` and is
evidenced by executed commands rather than intent. Delivered:

```text
App Shell ................. IMPLEMENTED (header · nav · main · feedback region)
Routing ................... IMPLEMENTED (public/auth · platform · tenant-scoped Company placeholder)
Auth Context .............. IMPLEMENTED (existing identity/session; memory-only token)
Tenant Context ............ IMPLEMENTED (URL → context; no client ACL)
Typed API Client .......... IMPLEMENTED (native fetch; correlation; timeout/abort; 401 recovery)
Error System .............. IMPLEMENTED (frozen 401/403/409/422/503 taxonomy; safe messages)
Design Tokens ............. IMPLEMENTED (CSS variables; CSS Modules; no UI framework)
Core UI Primitives ........ IMPLEMENTED (12 primitives)
Testing Foundation ........ IMPLEMENTED (Vitest + RTL + Playwright)
Development Configuration . IMPLEMENTED (Vite dev proxy; env template; build)
```

Measured evidence:

```text
npm run typecheck .......... PASS (tsc --noEmit, strict)
npm run test:run ........... 14 files / 88 tests / 88 passed / 0 failed
npm run test:coverage ...... 88 passed · statements 89.41% · branches 88.53% · functions 83.56%
npm run build .............. PASS (dist/ generated: 0.40 kB html · 3.67 kB css · 196.49 kB js)
npm run e2e ................ 2 passed (chromium)
dist secret scan ........... 0 findings
src security scan .......... 0 executable findings (1 documentation-only mention)
git staged ................. 0
HEAD ....................... 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (unchanged)
```

Honest limitations (see §33 Findings):

```text
* No backend/API was reachable in this environment (port 8000 closed; Docker API unreachable
  from the working shell), so the dev proxy was verified to attempt the upstream hop
  (ECONNREFUSED through the proxy) rather than to reach a live /health or /me.
* The repository carries a large pre-existing uncommitted dirty set (P15–P20) that this round
  neither created nor cleaned; see §30.
```

---

## 2. Authority Sources

Read before implementing (repository reality preferred over narrative):

```text
AGENTS.md                                            (operating rules, test governance, historical baselines)
docs/architecture/PLATFORM_DECISION_LOG.md           (Appendix AL — P21 Frontend Architecture)
docs/architecture/P21_FRONTEND_DISCOVERY_PREP_REPORT.md
docs/architecture/P20_COMPANY_API_ACCEPTANCE_REPORT.md
apps/api/routes/{sessions,identity,meta}.py          (auth transport contract)
services/context/model.py                            (LOG_SAFE_FIELDS for GET /me)
apps/api/main.py                                     (49 routes · no CORS · no static mount)
apps/api/schemas/company.py                          (Company DTO reference — not consumed by P21)
apps/frontend/**                                     (STEP-0 skeleton, committed in 72ade9f)
```

`UAP_PROJECT_MASTER_DOSSIER.md` was treated as continuity aid only.

---

## 3. AL Decision Recovery (P21-H01 … P21-H11)

| ID | Decision | Implementation evidence |
| --- | --- | --- |
| H01 | Keep React 18 + Vite 6 + TypeScript (no upgrades) | `package.json` declares `^18.3.1`, `^6.0.5`, `^5.7.2`; resolved `18.3.1 / 6.4.3 / 5.9.3` |
| H02 | Root at `apps/frontend/` | all changes confined to `apps/frontend/**` |
| H03 | Tenant in the URL `/tenants/:tenant_id/...` | `src/app/routing/routes.ts` |
| H04 | Reuse existing identity/session; memory-first; no `localStorage` | `src/platform/auth/AuthContext.tsx`; scan + test §27 |
| H05 | Native-fetch typed API client (no Axios) | `src/platform/api/client.ts` |
| H06 | Context + hooks + local state (no Redux/Zustand) | `AuthContext` · `TenantContext` · `FeedbackProvider` |
| H07 | UAP design tokens + CSS Modules (no MUI/AntD/Chakra/Bootstrap/Tailwind) | `src/platform/design/*` + `*.module.css` |
| H08 | React Router | `react-router-dom` (only new runtime dependency) |
| H09 | Backend-authoritative permission UX; no frontend ACL engine | `src/platform/permissions/capability.tsx` always reports `unknown` |
| H10 | Vitest + RTL + Playwright | `vitest.config.ts` · `playwright.config.ts` · 14 test files · `e2e/boot.spec.ts` |
| H11 | Static SPA + reverse proxy (same-origin `/api`) | `vite.config.ts` build block · no API base baked into the bundle (§27) |

---

## 4. Baseline Integrity

```text
git rev-parse HEAD  = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
                    = release: UAP v0.1.17 P18 control plane
git diff --cached   = 0 entries (nothing staged)
git diff --check    = clean for apps/frontend/** ; pre-existing CRLF warnings only for
                      docs/api/README.md, docs/architecture/{ARCHITECTURE,DEPENDENCY_RULES}.md,
                      docs/security/README.md (untouched historical files)
```

Tracked frontend files present at baseline (STEP-0 skeleton): `package.json`,
`vite.config.ts`, `index.html`, `README.md`, `src/main.tsx`.

`index.html` was **not** modified.

No cleaning, restoring, reformatting or line-ending normalization was performed.

---

## 5. Dependency Installation

```text
command   : npm install --no-fund --no-audit   (apps/frontend)
result    : added 230 packages in 42s
lockfile  : apps/frontend/package-lock.json (lockfileVersion 3) — created this round
```

Prohibited operations were not used: no `npm audit fix`, no `npm update`, no `--latest`.

Warnings observed and left untouched:

```text
deprecated whatwg-encoding@3.1.1   (transitive, jsdom tree)
deprecated glob@10.5.0             (transitive)
esbuild@0.25.12 postinstall script blocked by the host npm install-scripts policy
                                   (no functional impact: typecheck/test/build/e2e all executed)
```

No forbidden dependency was added: no Cypress, Jest, Redux, Zustand, Axios, Tailwind,
Material UI, Ant Design, Chakra or Bootstrap. Verified by dependency list and by source scan.

---

## 6. Package Versions

Declared (caret) vs. resolved from `package-lock.json`:

| Package | Declared | Resolved | Reason |
| --- | --- | --- | --- |
| react | ^18.3.1 | 18.3.1 | AL H01 (frozen) |
| react-dom | ^18.3.1 | 18.3.1 | AL H01 |
| react-router-dom | ^7.1.1 | 7.18.4 | AL H08 routing |
| vite | ^6.0.5 | 6.4.3 | AL H01 build tool |
| typescript | ^5.7.2 | 5.9.3 | AL H08 strict typing |
| @vitejs/plugin-react | ^4.3.4 | 4.7.0 | React JSX transform |
| vitest | ^3.0.0 | 3.2.7 | AL H10 |
| @vitest/coverage-v8 | ^3.0.0 | 3.2.7 | coverage evidence |
| @testing-library/react | ^16.1.0 | 16.3.3 | AL H10 |
| @testing-library/dom | ^10.4.0 | 10.4.2 | peer of RTL |
| @testing-library/jest-dom | ^6.6.3 | 6.9.1 | DOM matchers |
| @testing-library/user-event | ^14.5.2 | 14.6.7 | keyboard/pointer fidelity |
| jsdom | ^26.0.0 | 26.1.0 | AL H45 environment |
| @playwright/test | ^1.49.1 | 1.63.0 | AL H47 |
| @types/react | ^18.3.18 | 18.3.31 | React 18 types |
| @types/react-dom | ^18.3.5 | 18.3.7 | ReactDOM types |
| @types/node | ^22.10.5 | 22.20.5 | config files |

Scripts established: `dev`, `build` (`typecheck && vite build`), `preview`, `test`,
`test:run`, `test:coverage`, `typecheck`, `e2e`.

---

## 7. TypeScript

`tsconfig.json`: `strict`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`,
`noImplicitOverride`, `verbatimModuleSyntax`, `jsx: react-jsx`, `moduleResolution: bundler`,
`target/lib ES2022 + DOM`, `types: ["vite/client", "vitest/globals", "node"]`,
`include: ["src", "e2e", "vite.config.ts", "vitest.config.ts", "playwright.config.ts"]`.

```text
npm run typecheck = PASS (no @ts-ignore, no suppression)
```

Strict mode surfaced one real defect (`F-P21-FND-01`, §33); it was fixed inside the
authorized frontend scope by removing an `api ↔ refresh` circular reference.

---

## 8. Vite

```text
dev    : port 5173; proxies /api, /health, /ready, /me, /sessions, /identity, /devices
         → VITE_API_TARGET (default http://localhost:8000)
build  : outDir dist · sourcemap false · SPA (Appendix AL H11)
```

The `/api`, `/health`, `/ready` rules are the AL §9 requirement; `/me`, `/sessions`,
`/identity`, `/devices` were added because the AL §19 auth bootstrap consumes the real
platform identity/session surface. Production output never reads `VITE_API_TARGET`
(verified: zero occurrences in `dist/**`).

---

## 9. Application Entry

`src/main.tsx` is now the real entry point: `StrictMode` → design tokens + global reset →
`App`. The STEP-0 skeleton behaviour (a bare scattered `fetch('/api/v1/meta')`) was removed;
any future platform data access goes through the single typed client.

---

## 10. App Shell

`src/app/shell/AppShell.tsx` (+ `AppShell.module.css`) provides the global header (brand,
current tenant, current user, sign-out when authenticated), a navigation area, the main
content area (`<Outlet/>`) and the global feedback region from `FeedbackProvider`.

Shell states are centralized in `src/app/shell/ShellStates.tsx`
(`AppBootstrapLoading`, `TenantUnresolved`), so `undefined`/`null`/`loading` do not leak into
individual pages. The shell contains no Company navigation and no Company behaviour
(asserted by test).

---

## 11. Routing

```text
/                             → AppShell → RequireAuth → HomePage
/login                        → LoginPage (public; outside the shell)
/tenants/:tenant_id/company   → RequireAuth → TenantBoundary → CompanyPlaceholderPage
/403                          → ForbiddenPage
*                             → NotFoundPage
```

`src/app/routing/routes.ts` is the single registration boundary (constants, `TENANT_PARAM`,
`companyPath()`); domain modules build from it instead of mutating the global router.
`RequireAuth` resolves auth once (bootstrapping/refreshing → one controlled
`AppBootstrapLoading`; unauthenticated → redirect to `/login`).

---

## 12. Auth Context

Contract facts verified against `apps/api/routes` before coding:

```text
POST /sessions          {login, password, device_id?} → token ONLY with a verified device
POST /sessions/refresh  (Bearer) → session/expiry view
POST /sessions/logout   (Bearer) → {"revoked": n}
GET  /me                (Bearer) → frozen log-safe context (NO permission set)
```

`AuthProvider` exposes `status` (`bootstrapping | unauthenticated | refreshing | authenticated`),
`user`, `error`, `login`, `logout`, `refresh`.

```text
token storage  : in-memory ref only (never localStorage/sessionStorage)
login outcome  : 'authenticated' | 'device_required' (no token issued) | 'failed'
refresh        : single in-flight attempt; never loops
logout         : best-effort call, then local state cleared regardless
/me mapping    : only fields the backend actually returns (§20 of the instruction);
                 `scope` is never re-labelled as permissions/roles
second auth    : none (no employee login, no API token system)
```

---

## 13. Tenant Context

`TenantProvider` / `useTenant()` expose `tenantId`, `setTenant`, `clearTenant`.
`TenantBoundary` reads the URL parameter, validates it against the backend uuid id contract
(`isValidTenantId`), mirrors a valid value into the shared context, clears it on unmount and
blocks a page render when the identifier is missing/invalid.

```text
URL tenant → Context tenant → API path tenant   (single context; no divergence)
tenant context ≠ authorization credential       (backend answers 403; no client ACL)
```

---

## 14. API Client

`src/platform/api/client.ts` — one owner of transport concerns:

```text
native fetch only (no Axios)
base URL (same-origin default; dev proxy in development)
headers (accept + x-correlation-id + optional Bearer token + content-type)
credentials: 'same-origin'
timeout 15s + caller AbortSignal → AbortController
JSON parse (204 → undefined; unreadable body → safe UNKNOWN_ERROR)
HTTP error normalisation (401/403/409/422/503)
at most ONE controlled 401 recovery, then the original request is retried once
```

No SQL, ORM, or backend package is imported; no secret is embedded.

---

## 15. Correlation

`CORRELATION_HEADER = 'x-correlation-id'`; `newCorrelationId()` uses `crypto.randomUUID()`
with a fallback. Every request carries the header (including the retry after recovery, which
reuses the same id); the id is preserved on `ApiError` for UX/debugging and surfaced as a
reference in error states. No internal exception is exposed.

---

## 16. Error Model

`src/platform/api/errors.ts`:

```text
401 → AUTH_REQUIRED
403 → ACCESS_DENIED
409 → CONFLICT
422 → VALIDATION_OR_NOT_FOUND
503 → SERVICE_BOUNDARY_ERROR
     + NETWORK_ERROR (transport) · UNKNOWN_ERROR (unmapped/unreadable)
```

`ApiError` exposes `status`, `code`, safe `message`, `correlationId` and a length-capped,
string-only `detail` (server-provided, non-sensitive by contract: ≤200 chars, dropped
otherwise). Messages are asserted never to contain SQL, constraint, traceback or stack text.
No backend-conflicting taxonomy was invented.

---

## 17. Feedback

`src/platform/feedback/FeedbackProvider.tsx` owns the single toast region
(`role="status"`, `aria-live="polite"`, `data-testid="uap-toast-region"`) and
`states.tsx` provides `LoadingIndicator`, `InlineError` (`role="alert"`) and `GlobalError`
(safe message + correlation reference + retry). Pages do not implement private toast stacks.

---

## 18. Design Tokens

`src/platform/design/tokens.css` defines colour (surface/text/muted/border/accent/success/
warning/danger/focus), spacing, radius, typography, elevation, motion and the documented
breakpoints (mobile < 768 / tablet 768–1023 / desktop ≥ 1024). `global.css` is limited to
reset, body/font defaults and a visible `:focus-visible` outline. No Tailwind, no UI framework,
no global selector explosion, no `!important`.

---

## 19. UI Primitives

```text
Button (variant/size/disabled/loading/type, duplicate-submit protection)
Input · Select
Field / FieldError / TextField (label for, hint, aria-describedby, invalid)
Dialog (role=dialog, aria-modal, aria-labelledby/-describedby, Escape, initial focus)
Card · PageHeader · Badge
Table (columns/rows/empty/loading only — no pagination, sorting or query DSL)
EmptyState · LoadingState · ErrorState
```

No Company-specific field, form, list or page was created.

---

## 20. Accessibility

Evidenced by executed tests, not declarations:

```text
button keyboard reachable + Enter activation ........ Button.test.tsx
loading button disabled (aria-busy) ................. Button.test.tsx
dialog role/aria/focus/Escape/cleanup ............... Dialog.test.tsx
label association + aria-describedby + invalid ...... Field.test.tsx
error alert semantics ............................... Field/states tests
live-region loading announcement .................... states/Table tests
status conveyed by text, not colour alone ........... Badge test
visible focus ....................................... global.css :focus-visible
```

---

## 21. Responsive

Breakpoint tokens are documented in `tokens.css`; the shell collapses to a single column at
`max-width: 767px` (`AppShell.module.css`). No fixed 1440/1920 layout lock exists. Responsive
behaviour is CSS/evidence-verified, not yet covered by an automated layout test (recorded in
§33 as an acceptance-gate suggestion).

---

## 22. Permission UX Boundary

`src/platform/permissions/capability.tsx` provides only a presentation hint
(`CapabilityHint`) and reports `capabilityAvailability() === 'unknown'`, because `/me`
returns no permission set and AL H09/H41 forbid deriving permissions from role names, scope
strings or an "admin means all" shortcut. There is no frontend ACL engine; `403` remains final.

---

## 23. Testing Foundation

```text
runner   : Vitest 3.2.7 (jsdom, globals, setup ./src/test/setup.ts)
library  : @testing-library/react + jest-dom + user-event
files    : 14 test files (7 platform/context + 3 component + 3 app/router/shell + 1 static scan)
tests    : 88 passed / 0 failed
coverage : statements 89.41% · branches 88.53% · functions 83.56% · lines 89.41%
```

Covered areas: API client transport/recovery/cancellation, error normalisation,
correlation header, auth bootstrap/login/device-required/refresh-dedupe/logout,
tenant URL→context/boundary clearing, shell states, routing (auth redirect, home,
Company placeholder, invalid tenant, 403, 404, no employee/assignment route),
primitives, dialog/form accessibility, static security invariants.

Tests are deterministic and isolated: no formal `uap` DB, no shared test DB, no network, no
production service, no production Event. The forbidden test
`tests/unit/test_generate_build_info.py` was not touched or executed (frontend-only round).

---

## 24. Playwright

```text
config : playwright.config.ts — testDir ./e2e, chromium, webServer = npm run preview
         --port 4173 --strictPort --host 127.0.0.1, baseURL http://127.0.0.1:4173
tests  : e2e/boot.spec.ts (application boots · anonymous deep link falls back to sign-in)
result : 2 passed (5.9s), no page errors, title "UAP Console"
```

One configuration defect was found and fixed (`F-P21-FND-02`): `vite preview` binds `[::1]`
only, so an `http://127.0.0.1` webServer probe timed out; the preview command now pins IPv4.

Chromium (playwright build 1243 / Chrome for Testing 153.0.8010.12) was installed into the
host Playwright cache to execute the baseline; it is not a repository artifact.

---

## 25. Build

```text
npm run build = npm run typecheck && vite build    → PASS
81 modules transformed
dist/index.html                 0.40 kB │ gzip 0.27 kB
dist/assets/index-*.css         3.67 kB │ gzip 1.19 kB
dist/assets/index-*.js        196.49 kB │ gzip 64.86 kB
```

`apps/frontend/.gitignore` covers `node_modules/`, `dist/`, `coverage/`, `.vite/`,
`playwright-report/`, `test-results/`; no build artifact entered Git status.

---

## 26. Dev Proxy

Environment reality: nothing listens on port 8000 and the Docker API is unreachable from the
working shell, so no live backend could be proxied.

Evidence collected against a locally started dev server (`npm run dev -- --port 5199`):

```text
GET /health          → HTTP 500  + vite log "http proxy error: /health  AggregateError [ECONNREFUSED]"
GET /api/v1/meta     → HTTP 500  + vite log "http proxy error: /api/v1/meta  AggregateError [ECONNREFUSED]"
GET /definitely-not-a-route → HTTP 200 SPA index.html
```

Interpretation: `/health` and `/api/*` are routed to the configured upstream target (the hop
is attempted and fails only because the backend is down), while unknown paths fall back to the
SPA — the proxy rules are active, not bypassed. A live `/health` / `/ready` / `/api/v1/meta`
round trip remains unverified (`F-P21-FND-04`).

No Company business endpoint was verified or contacted.

---

## 27. Security

Source-level (executable code, comments excluded) — `src/test/security.test.ts` and a raw scan:

```text
localStorage / sessionStorage  ............ 0 executable uses (1 documentation mention)
document.cookie = ......................... 0
eval( / new Function( ..................... 0
dangerouslySetInnerHTML / innerHTML = ..... 0
postgres://, sk-…, BEGIN …PRIVATE KEY,
jwt_secret, DATABASE_URL, DB_PASSWORD ..... 0
VITE_API_TARGET in src .................... 0        (dev proxy only, vite.config.ts)
localhost:8000 in src ..................... 0
```

`.env.example` contains exactly one public key (`VITE_API_TARGET`) and no secret term in any
assignment. Built bundle scan (`dist/**`) for the same secret patterns: 0 findings — the
production bundle does not depend on `VITE_API_TARGET`.

Error boundaries and error states never render stacks, component internals, API URLs, SQL or
database details (asserted by test).

---

## 28. Company Boundary

```text
src/modules/company/index.ts → COMPANY_MODULE_STATUS = 'NOT_IMPLEMENTED'
                               COMPANY_MODULE_SCOPE  = ['Employee list','Employee detail',
                                                       'Assignment list','Assignment detail']
```

`/tenants/:tenant_id/company` renders a placeholder page only (status, resolved tenant, the
scope list marked "not implemented"). No employee/assignment page, form, table, API call,
DTO or permission wiring exists. Routing is asserted to leave
`/tenants/:tenant_id/company/employees` as a 404.

---

## 29. Event Boundary

```text
Event Center / Timeline / Handler UI / Allowlist UI / Worker UI = absent (0 files)
producer · handler · worker references in frontend            = 0
API mutations from the frontend                               = 0 (no Company calls)
```

P20 Event infrastructure remains accepted-but-inactive and carries no product UI. This round
did not read or modify the production allowlist, so its emptiness is asserted from the frozen
P20 state, not re-measured this round (no backend access — see §30).

---

## 30. Backend Regression

No backend file was written by this round. The backend paths visible in Git status are the
pre-existing, uncommitted P15–P20 work-in-progress; they were left untouched.

Mtime evidence (round writing started ≈ 11:42, newest frontend edit 11:47+):

```text
apps/api/main.py                                     2026-10-02 17:27:15
apps/api/routes/company.py                           2026-10-02 17:27:14
domains/company/manifest.py                          2026-10-02 16:45:04
migrations_alembic/versions/0019_p20_company.py      2026-10-02 16:01:44
services/consumer/kernel.py                          2026-10-04 11:16:12
docs/architecture/PLATFORM_DECISION_LOG.md           2026-10-04 11:33:42
apps/frontend/src/platform/api/client.ts             2026-10-04 11:42:32   (frontend)
apps/frontend/package-lock.json                      2026-10-04 11:47:30   (frontend)
```

```text
git status --porcelain : total 206 = 16 under apps/frontend/** + 190 pre-existing
git diff --name-only   : no apps/frontend file is staged; no backend file diff introduced here
```

Consequence for the acceptance gate: P21 §65's assumption of a clean backend baseline cannot
be satisfied while the P15–P20 dirty set remains uncommitted and committing is not authorized
here (`F-P21-FND-05`).

---

## 31. Files Changed

Modified (tracked):

```text
apps/frontend/package.json          (+ scripts, deps, devDeps)
apps/frontend/vite.config.ts        (+ build block, + auth-surface proxy)
apps/frontend/src/main.tsx          (skeleton → real entry)
apps/frontend/README.md             (foundation status; Company NOT implemented)
```

Added (untracked, all under `apps/frontend/`):

```text
package-lock.json · tsconfig.json · vitest.config.ts · playwright.config.ts
.env.example · .gitignore
e2e/boot.spec.ts
src/app/**            (App, ErrorBoundary, routing/*, routing/pages/*, shell/*)
src/components/**     (Badge, Button, Card, Dialog, Input, PageHeader, Select, Table,
                       states, form/Field + *.module.css + index.ts)
src/modules/company/index.ts (placeholder)
src/platform/api/**       (client, errors, correlation, types, index)
src/platform/auth/AuthContext.tsx
src/platform/design/{tokens,global}.css
src/platform/feedback/{FeedbackProvider.tsx,states.tsx}
src/platform/permissions/capability.tsx
src/platform/tenant/TenantContext.tsx
src/test/setup.ts · src/test/security.test.ts
src/**/*.test.ts(x)  (14 test files, listed in §23)
```

Added by this round specifically: `src/test/setup.ts`, the 14 test files,
`e2e/boot.spec.ts`, `package-lock.json`, the `AuthContext` fix, the `playwright.config.ts`
IPv4 fix, and this report.

Not changed: `index.html`, any repository-root file, any backend/API/migration/authorization
file, any historical release artifact, any version metadata.

Code inventory: 48 production source files (1 806 lines) + 14 test files (1 498 lines).

---

## 32. Test Evidence

```text
$ npm run typecheck
> tsc --noEmit -p tsconfig.json                      (exit 0)

$ npm run test:run
 Test Files  14 passed (14)
      Tests  88 passed (88)
   Duration  4.88s

$ npm run test:coverage
 Test Files  14 passed (14)   Tests  88 passed (88)
 All files | % Stmts 89.41 | % Branch 88.53 | % Funcs 83.56 | % Lines 89.41

$ npm run build
 vite v6.4.3 building for production... ✓ 81 modules transformed.
 dist/index.html 0.40 kB · dist/assets/index-*.css 3.67 kB · dist/assets/index-*.js 196.49 kB

$ npm run e2e
  ok 1 [chromium] › e2e\boot.spec.ts:11:1 › the console boots and routes an anonymous visitor to sign-in
  ok 2 [chromium] › e2e\boot.spec.ts:22:1 › unauthenticated deep links fall back to sign-in
  2 passed (5.9s)

$ git status --porcelain | count                     = 206 (16 frontend + 190 pre-existing)
$ git diff --cached | count                          = 0
$ git rev-parse HEAD                                 = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
```

Acceptance-oriented matrix coverage:

| Area | Test | Status |
| --- | --- | --- |
| Shell | `AppShell.test.tsx` renders header/nav/main, tenant + user, sign-out | PASS |
| Routing | `AppRouter.test.tsx` transitions, placeholders, 403/404 | PASS |
| Auth | bootstrap, login, device_required, failure | PASS |
| 401 | single recovery (client) + refresh de-duplication (context) | PASS |
| Tenant | URL → Context, change, invalid, clear | PASS |
| API | typed fetch, verbs, query, 204 | PASS |
| Correlation | header present, reused on retry, overridable | PASS |
| Errors | 401/403/409/422/503 + unknown + network | PASS |
| Design | primitives render | PASS |
| A11y | labels, keyboard, dialog semantics, live regions | PASS |
| Responsive | CSS token/breakpoint verification | CSS evidence only |
| Security | no token persistence, no eval/HTML, no secrets | PASS |
| Build | production build + bundle scan | PASS |
| Typecheck | strict, no suppression | PASS |
| E2E | application boots | PASS |
| Company | NOT IMPLEMENTED | PASS (placeholder only) |
| Event UI | NOT IMPLEMENTED | PASS (absent) |

---

## 33. Findings

```text
F-P21-FND-01  CLOSED (this round)
  Type           : implementation defect (frontend only)
  Detail         : AuthContext created a circular reference (api useMemo → refreshInternal →
                   api), which strict TypeScript rejected (TS7022/TS7023/TS7024) and which
                   would have produced an unstable client identity.
  Resolution     : refreshInternal reads the client from a ref; the memo depends on
                   [client, refreshInternal]. typecheck now passes; recovery semantics unchanged.
  Scope impact   : apps/frontend only — no API/authorization/migration change.

F-P21-FND-02  CLOSED (this round)
  Type           : configuration defect (test harness only)
  Detail         : Playwright webServer probed http://127.0.0.1:4173 while `vite preview`
                   bound [::1] only → 60 s timeout, no test executed.
  Resolution     : preview command pins `--host 127.0.0.1`; E2E now 2/2 passed.
  Scope impact   : apps/frontend testing configuration only.

F-P21-FND-03  INFORMATIONAL (environment)
  Detail         : host npm policy blocked the esbuild postinstall script; typecheck, tests,
                   build and E2E all executed successfully anyway.
  Action         : none taken (no dependency change).

F-P21-FND-04  OPEN (environment limitation — non-blocking)
  Detail         : no backend/API reachable in this environment (port 8000 closed; Docker API
                   unreachable from the working shell). The dev proxy was verified to attempt
                   the upstream hop and fail with ECONNREFUSED, but no live /health, /ready,
                   /api/v1/meta or /me round trip was performed, and no browser session was
                   exercised against real identity/session endpoints.
  Impact         : the AuthContext contract is implemented against the verified source
                   contract and covered by stubs; real end-to-end identity verification remains
                   outstanding.
  Suggested gate : during P21 FRONTEND FOUNDATION ACCEPTANCE, either provide a running backend
                   for a live proxy/auth smoke, or explicitly accept proxy-level + contract-level
                   evidence.

F-P21-FND-05  OPEN (pre-existing repository condition — non-blocking for this round)
  Detail         : the worktree carries 190 uncommitted non-frontend entries (P15–P20 code and
                   documents) that pre-date this round; `apps/api/main.py`, `domains/company/*`,
                   `migrations_alembic/versions/0019/0020`, `services/company/**` and
                   `apps/api/routes/company.py` appear in `git status`/`git diff --name-only`.
  Action         : preserved untouched (AGENTS.md §70/§73; P21 §3/§73). No cleaning, staging or
                   reverting performed.
  Impact         : the instruction's "backend unchanged" check must be read as "unchanged by
                   this round" (mtime evidence in §30), not "absent from Git status".

F-P21-FND-06  INFORMATIONAL (design boundary)
  Detail         : `/me` exposes no permission set, so `capabilityAvailability()` is always
                   `unknown` and Company UI cannot pre-filter actions client-side.
  Impact         : Company UI implementation must render and reflect the backend's answer
                   (403 final); any permission-aware UX needs a future authorized permission
                   source — not a frontend inference.
```

No blocking finding from §76 of the instruction was triggered by this round:
no unexpected backend edit, no Company feature, no Event UI, no insecure token persistence,
no bypassable tenant context, no frontend authorization claim, no secret exposure, no
typecheck/build failure, no dependency expansion beyond the frozen stack.

---

## 34. Final Status

```text
P21 FRONTEND FOUNDATION IMPLEMENTATION = PASS

App Shell:              IMPLEMENTED
Routing:                IMPLEMENTED
Auth Context:           IMPLEMENTED
Tenant Context:         IMPLEMENTED
UAP API Client:         IMPLEMENTED
Error System:           IMPLEMENTED
Design Tokens:          IMPLEMENTED
Core Primitives:        IMPLEMENTED
Testing Foundation:     IMPLEMENTED
Dev Configuration:      IMPLEMENTED

Dependencies:           INSTALLED (lockfile committed-state ready, not staged)
Typecheck:              PASS
Unit/Component Tests:   88 / 88 PASS
Coverage:               89.41% statements
Build:                  PASS (dist/)
E2E Boot:               2 / 2 PASS
Security Scans:         PASS (source + bundle)

Company UI:             NOT IMPLEMENTED
Company Feature:        NOT AUTHORIZED
Event UI:               NOT IMPLEMENTED (out of scope)
Production Event:       NOT AUTHORIZED
Worker:                 NOT AUTHORIZED

Backend:                UNCHANGED BY THIS ROUND
API:                    UNCHANGED BY THIS ROUND
Migration:              NONE
Authorization:          UNCHANGED

Git staged:             0
HEAD:                   08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (unchanged)
Commit:                 NO
Tag:                    NO
Push:                   NO

Acceptance semantics:   IMPLEMENTED + TESTS PASSING / EVIDENCE READY
                        (ACCEPTED is reserved for the next gate; NOT PRODUCTION)
```

---

## 35. Hard Stop

```text
HARD STOP = ACTIVE
```

This round stops after delivering the foundation implementation, its executed evidence and
this report. Not performed and not authorized here:

```text
Company UI / Employee pages / Assignment pages / Company API integration from the UI
Event Center / Handler UI / Allowlist UI / Worker UI
backend, API, authorization, migration or database change
Event activation, worker start, commit, tag, push
```

Next authorized stage (requires its own execution and must not be assumed from this PASS):

```text
P21 FRONTEND FOUNDATION ACCEPTANCE GATE
```

That gate should independently verify: React/Vite/TS foundation · auth bootstrap · 401
recovery · tenant URL → context · API client · correlation · error normalisation · design
tokens · primitive accessibility · responsive shell · no insecure token persistence · no
secret exposure · strict TypeScript · build · tests · E2E boot · Company untouched · backend
untouched, and settle `F-P21-FND-04` (live backend identity/proxy evidence) and
`F-P21-FND-05` (historical dirty baseline) explicitly.
