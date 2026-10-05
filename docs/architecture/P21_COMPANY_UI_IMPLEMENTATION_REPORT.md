# P21 COMPANY UI IMPLEMENTATION REPORT

Authorization: `HD-P21-01 — P21 Company UI Implementation Authorization`

Scope executed: the first Company Domain UI vertical slice on top of the accepted
Foundation, Company Domain, Authorization and Company API.

## Final status

```text
P21 COMPANY UI IMPLEMENTATION = COMPLETE
READY FOR BOT VALIDATION / GATE

Overview · Employees · Employee detail · Assignments · Assignment detail .... IMPLEMENTED
Employee Create / Edit / Suspend / Terminate ............................... IMPLEMENTED
Assignment Create / Edit / End ............................................. IMPLEMENTED
Real backend data · real mutations · real 401/403/409/422 handling .......... VERIFIED
Unauthorized actor denied by the backend .................................... VERIFIED (403)
Cross-tenant / stale-tenant rendering ....................................... PREVENTED (guard + browser evidence)
Typecheck · 132 tests · build · E2E ......................................... PASS
Security scans .............................................................. PASS
Backend / schema / migration / permissions .................................. UNCHANGED

RELEASE = NOT AUTHORIZED · COMMIT = NOT AUTHORIZED · TAG = NOT AUTHORIZED · PUSH = NOT AUTHORIZED
HARD STOP = ACTIVE
```

---

## 1. Executive Summary

The Company UI is no longer a placeholder: it is a working vertical slice that talks to the
real Company API through the platform's typed client and renders real authorization outcomes.

```text
new module files ......... 26 (api · hooks · tenant guard · vocabulary · paths · routes ·
                              3 dialogs/state components · 5 pages · 1 module stylesheet ·
                              6 test files · module barrel)
new tests ................ 32 Company tests (+1 rewritten routing test) → suite 99 → 132
suite .................... 20 files · 132 tests · 132 passed · 0 failed · 0 skipped
coverage ................. All files 94.25% stmts · 88.81% branch · 87.31% funcs
                           Company module: api 100% · pages 95.59% stmts · Overview 100%
typecheck ................ PASS (strict, 0 suppressions)
build .................... PASS · dist js 223.14 kB (Company UI now in the bundle)
E2E ...................... 2/2 passed
real backend ............. isolated DB + real FastAPI: 22/22 API steps behaved as frozen
real browser ............. real components + real backend: list/create/suspend/end flows
                           executed through the UI with 201/200 responses, 0 console errors
unauthorized ............. real 403 rendered as the no-access state (no data leak)
```

Two minimal, justified platform-side changes were required and are recorded in §5; everything
else lives inside `src/modules/company/` and consumes the platform unchanged.

---

## 2. Authority and Scope

```text
Authority       : HD-P21-01 (Human Decision) + PDL Appendix AG (frozen Company API)
                  + Appendix AL (frozen frontend architecture) + Appendix AF/AD/AC (domain)
Authorized      : Company UI implementation (pages, components, hooks, API adapter, DTO mapping,
                  route table, UX capability mapping)
Forbidden (kept): Delete · Admin · Employee login · Token API · Event UI · Worker UI ·
                  Production Event activation · new backend endpoints · new permissions ·
                  new migrations · RLS · API versioning · generic CRUD/low-code/plugin engines ·
                  frontend monolith refactor
```

The HD page list (`/company/overview`, `.../employees`, `.../employees/:id`, `.../assignments`,
`.../assignments/:id`) was mapped onto the frozen canonical paths after reading the actual
router contract — see §6.

---

## 3. Contract Verification (read from the repository, not assumed)

```text
API prefix .......... /company/tenants/{tenant_id}/...   (apps/api/routes/company.py)
Endpoints used ...... exactly the accepted 11 (no endpoint added, none unused)
  POST   /employees                     → 201 EmployeeResponse
  GET    /employees?status&limit        → 200 {items,count,limit}
  GET    /employees/{employee_id}       → 200
  PATCH  /employees/{employee_id}       → 200   (display_name? · title?)
  POST   /employees/{id}/suspend        → 200
  POST   /employees/{id}/terminate      → 200
  POST   /assignments                   → 201   (employee_id · space_id · assignment_role)
  GET    /assignments?employee_id&space_id&status&limit → 200 {items,count,limit}
  GET    /assignments/{assignment_id}   → 200
  PATCH  /assignments/{assignment_id}   → 200   (assignment_role)
  POST   /assignments/{id}/end          → 200
DTO whitelist ....... EMPLOYEE_FIELDS (11) · ASSIGNMENT_FIELDS (10) — mirrored exactly, no
                      extra field invented (apps/api/schemas/company.py)
Error taxonomy ...... 403 authorization · 422 validation/not-found · 409 conflict/lifecycle
                      (apps/api/errors/company.py → frozen Core map)
Assignment space .... GET /tenants/{tenant_id}/spaces (P17 structure read, actor's member
                      spaces) — legitimate backend data, never a hard-coded organisation tree
Domain vocabulary ... employee statuses active/suspended/terminated · assignment statuses
                      active/ended · roles member/lead · employee_no pattern
                      ^[A-Za-z0-9._-]{1,64}$ (domains/company/values.py)
Authorization ....... unchanged: the UI calls an endpoint and renders the answer; it contains
                      no allow/deny computation and no role comparison
```

---

## 4. Architecture and Boundaries

```text
apps/frontend/src/modules/company/
  api.ts          Company URL paths + DTO types + typed calls (uses the platform client)
  hooks.ts        useApiResource (abortable, tenant-keyed) · useAction (pending + duplicate-click guard)
  tenant.ts       URL tenant authority guard (ready only when URL tenant === context tenant)
  vocabulary.ts   frozen status/role vocabulary mirror + timestamp rendering
  paths.ts        console route helpers
  routes.tsx      module route table + the module 404
  components/     StatusBadge · CompanyNav · CompanyStates · ConfirmDialog ·
                  EmployeeFormDialog (+status filter) · AssignmentFormDialog
  pages/          OverviewPage · EmployeeListPage · EmployeeDetailPage ·
                  AssignmentListPage · AssignmentDetailPage · CompanyNotFoundPage
  company.module.css  page-level layout + table scroll region (tokens only)
```

```text
module → platform   AuthContext (session + client) · TenantContext · typed API client ·
                    error taxonomy · design tokens · UI primitives · feedback layer
module → app        none (the app mounts the module; the module never imports app internals)
module → backend    HTTP through the platform client only (no SQL, no ORM, no DB driver,
                    no infrastructure import, no authorization internals)
component reuse     12 platform primitives used as-is; no Company copy of Button/Dialog/Table/
                    Field/state surfaces and no second auth/tenant/error system
```

---

## 5. Platform Changes (minimal and justified)

```text
1. src/platform/auth/AuthContext.tsx
   + AuthContextValue.client : ApiClient   (one added field; the provider already owned the client)
   Why: a domain module must consume the platform client instead of building a second one
        (AL H05 / HD "不得建立第二套 API client"). No token accessor is exported — the token
        stays inside the provider ref.

2. vite.config.ts (development only)
   + '/company'                   → API target   (the frozen Company namespace)
   + '^/tenants/[^/]+/spaces'     → API target   (the P17 space read used by the space picker)
   Why: without them the dev server answered those API paths with the SPA (ACC-02). The /tenants
        rule is deliberately an anchored pattern, not a prefix: the console's own routes live
        under /tenants/:tenant_id/company/..., so a prefix rule would swallow SPA deep links.
        Production is unchanged (same-origin reverse proxy, no proxy config in the bundle).
```

No other platform file was modified; no dependency was added.

---

## 6. Delivered Pages and Actions

| HD page list | Implemented console path (frozen AL H03 form) | Contents |
| --- | --- | --- |
| `.../company/overview` | `/tenants/:tenant_id/company` (module entry) | tenant scope, navigation, recent employees + recent assignments (limit 5), links into both collections |
| `.../company/employees` | `/tenants/:tenant_id/company/employees` | real list, frozen status filter, `New employee` |
| `.../company/employees/:employee_id` | `/tenants/:tenant_id/company/employees/:employee_id` | profile, Edit, Suspend, Terminate, the employee's assignments |
| `.../company/assignments` | `/tenants/:tenant_id/company/assignments` | real list with employee/space names, frozen status filter, `New assignment` |
| `.../company/assignments/:assignment_id` | `/tenants/:tenant_id/company/assignments/:assignment_id` | target, role, Edit role, End assignment |
| — (safety) | any other `.../company/*` path | module 404 with a link back to the overview |

```text
Employee actions : Create (dialog) · Edit (PATCH, only changed fields) ·
                   Suspend (confirmation) · Terminate (confirmation)
Assignment actions: Create (employee + space pickers filled from real reads) ·
                   Edit role (PATCH) · End (confirmation)
Not present      : Delete · Admin · employee login · token endpoints · event/worker surfaces
```

---

## 7. Tenant Safety (F-P21-RE-01 as a Company UI constraint)

```text
authority .......... the route parameter (URL) is the tenant authority; nothing else may set it
guard .............. useCompanyTenant() returns ready=true only when URL tenant === context tenant
consequences ....... * requests are issued only after the guard is ready (load receives null otherwise)
                     * a tenant switch renders the resolving state, so the previous tenant's data
                       is not shown under the new tenant
                     * every Company URL is built from the resolved tenant id (no tenant in a body,
                       query or header reaches the API from the UI)
evidence (unit) .... tenantGuard.test.tsx: stale context (URL=A, context=B) → resolving state and
                     0 API calls; switch A→B → all subsequent calls target B and A's row is gone;
                     invalid tenant → no module render, 0 calls
evidence (browser) . real UI flows used only /company/tenants/<tenant>/... and /tenants/<tenant>/spaces
```

No global frontend refactor was performed for this; the constraint is implemented inside the
module, exactly as the HD allowed.

---

## 8. UX States and Safety Rails

```text
loading ....... per-resource loading state (list/detail/options), never a fake empty screen
empty ......... per-area empty state with a next-step description
error ......... one error surface: frozen message for the normalised code + correlation reference
                + retry; 401/403/409/422/503 all render their frozen message
validation .... employee number (frozen pattern) and required fields are checked before submit;
                everything else is decided by the backend and rendered as its 422/409 message
confirmation .. Suspend · Terminate · End assignment each require an explicit confirmation dialog
pending ....... primary/confirm buttons use the platform Button loading state (duplicate submits
                blocked by the Button plus an in-flight guard in useAction)
feedback ...... success/error toasts through the platform FeedbackProvider (single toast region)
responsive .... page-level layout: grid collapses at 767px; wide tables scroll inside their own
                region (the shared Table primitive was NOT modified — ACC-03 handled at page level)
keyboard ...... native controls, platform Dialog focus containment/restoration, visible focus
```

---

## 9. Tests

```text
exact command : npm run test:run
result        : Test Files 20 passed (20) · Tests 132 passed (132) · 0 failed · 0 skipped
                (Foundation baseline before this round: 19 files / 99 tests)
```

New Company tests (32) and what each proves:

| File | Tests | Proves |
| --- | --- | --- |
| `api.test.ts` | 5 | frozen paths + id encoding · query discipline (only set filters) · create/update payloads · lifecycle calls carry no body |
| `tenantGuard.test.tsx` | 3 | stale context → no call · tenant switch targets B only and drops A's data · invalid tenant → no module render |
| `OverviewPage.test.tsx` | 3 | both recent slices render with links and limits · per-area empty state · one failed area does not hide the other |
| `EmployeeListPage.test.tsx` | 9 | loading/empty/403/401 states · create through the real endpoint + reload + toast · 409 keeps the dialog open · invalid employee number blocked client-side · status filter refetch |
| `EmployeeDetailPage.test.tsx` | 6 | profile + assignments · suspend requires confirmation and reloads · 409 rendered inside the dialog · terminal lifecycle disables actions · PATCH sends only changed fields · 422 not-found state |
| `AssignmentPages.test.tsx` | 6 | list enriched with real employee/space names · create uses backend-provided options · "no active space" hint · role edit PATCH · end requires confirmation · terminal assignment disables actions |
| `AppRouter.test.tsx` (rewritten) | 7 | module mounted under auth + tenant boundaries · overview/employees routes · module 404 · invalid tenant · 403/404 · home shows `IMPLEMENTED` |

```text
Test-only support : src/test/companyHarness.tsx (mounts the real module tree inside the real
                    platform providers; records every API call). Not imported by application code.
```

---

## 10. Coverage

```text
exact command : npx vitest run --coverage --coverage.reporter=text
All files     : 94.25% stmts · 88.81% branch · 87.31% funcs · 94.25% lines   (Foundation round: 89.82)
```

| Company file | stmts | branch | funcs |
| --- | --- | --- | --- |
| `api.ts` | 100 | 96.15 | 100 |
| `hooks.ts` | 94.28 | 78.26 | 100 |
| `tenant.ts` · `paths.ts` · `routes.tsx` · `index.ts` | 100 | 50–100 | 100 |
| `vocabulary.ts` | 85.18 | 75 | 100 |
| `components/*` (aggregate) | 97.85 | 86.2 | 88 |
| `pages/*` (aggregate) | 95.59 | 91.12 | 82.85 |
| `OverviewPage.tsx` | 100 | 100 | 100 |
| `EmployeeListPage.tsx` | 100 | 96.66 | 92.3 |
| `EmployeeDetailPage.tsx` | 95.36 | 91.66 | 77.77 |
| `AssignmentDetailPage.tsx` | 86.91 | 82.22 | 56.25 |
| `ConfirmDialog.tsx` · `CompanyNav.tsx` · `StatusBadge.tsx` | 100 | 100 | 50–100 |

Uncovered lines are defensive or presentation-only branches (e.g. `Dialog`'s surface-null guard,
the "unchanged form" hint, secondary branches of the assignment detail). No test was added purely
to move a number.

---

## 11. Typecheck · Build · E2E

```text
exact command : npm run typecheck  → exit 0 (strict; 0 @ts-ignore / @ts-nocheck / eslint-disable)
exact command : npm run build      → PASS · 81 modules · dist/index.html 0.39 kB ·
                                     css 6.20 kB (gzip 1.63) · js 223.14 kB (gzip 71.36)
exact command : npm run e2e        → 2 passed (boot · anonymous deep link fallback)
```

The production bundle grew from 196.49 kB to 223.14 kB because the Company UI is now part of the
application graph (the Dialog primitive is no longer tree-shaken). No new dependency was added.

---

## 12. Live Backend Integration (isolated, disposable)

Method — no source change, no migration file, no formal/shared database mutation:

```text
isolated database ... uap_p21_ui (created for this round, dropped afterwards)
migration identity .. uap_migrator → alembic head 0020_p20_company_authorization
privileges .......... scripts.privileges.materialize (additive) → 29 grant rows
fixtures ............ one tenant + one active space + tenant/space memberships for two users ·
                      platform_admin membership for the primary actor · Company collection
                      projection for the tenant · two isolated identities with verified devices
                      (tests/integration/wave2_testkit.provision_active_user)
API launch .......... existing project path (uvicorn apps.api.main:app), APP_ENV=development,
                      DATABASE_URL = postgresql+psycopg://uap:uap@uap-postgres:5432/uap_p21_ui
```

Real HTTP results (22 steps, all as frozen):

```text
POST /sessions (admin, verified device) ...... 201 · token issued
POST /sessions (plain user, verified device) . 201 · token issued
GET  /me (admin) ............................. 200
GET  /tenants/{t}/spaces ..................... 200 (real space "Engineering", active)
GET  /company/tenants/{t}/employees (admin) .. 200 (empty)
GET  /company/tenants/{t}/employees (plain) .. 403   ← real authorization denial
GET  /company/tenants/{t}/employees (anon) ... 401
POST /company/tenants/{t}/employees .......... 201 (created)
POST ... same employee_no again .............. 409 (natural-key conflict)
POST ... employee_no "bad no!" ............... 422 (validation)
GET  /company/.../employees/{id} ............. 200
PATCH /company/.../employees/{id} ............ 200 (title updated)
GET  .../employees/{id} in a foreign tenant .. 403 (no membership/projection there)
POST /company/tenants/{t}/assignments ........ 201
PATCH /company/.../assignments/{id} .......... 200 (role → lead)
POST /company/.../assignments/{id}/end ....... 200 (status ended)
PATCH ... after end ........................... 409 (terminal lifecycle)
POST /company/.../employees/{id}/suspend ..... 200 (status suspended)
POST /company/.../employees/{id}/terminate ... 200 (status terminated)
POST ... suspend after terminate ............. 409 (terminal lifecycle)
GET  /company/tenants/{t}/employees (final) .. 200 (includes the terminated row)
```

---

## 13. Browser Verification (real components against the real backend)

The console's login surface intentionally cannot produce a session token: the platform issues one
only for a verified device (frozen P17/P18 contract) and P21 ships no device-enrolment UI. The
authenticated Company UI was therefore driven in a real Chromium page that mounts the **real
module** (route tree, pages, dialogs, platform providers, platform API client) with a **real
session obtained from the real backend**, served by the dev server so every request goes through
the dev proxy to FastAPI.

| UI flow | Result | Real network calls observed |
| --- | --- | --- |
| open the Company overview | real terminated employee rendered | `GET /company/.../employees?limit=5` 200 · `GET /company/.../assignments?limit=5` 200 |
| create employee through the dialog | row appears, success toast | `POST /company/.../employees` **201** · list reload 200 |
| create assignment through the dialog | pickers filled from backend reads | `GET /tenants/<t>/spaces` **200** · `GET /company/.../employees?limit=100` 200 · `POST /company/.../assignments` **201** |
| end assignment through the confirmation | detail shows `ended`, success toast | `GET /company/.../assignments/{id}` 200 · `POST /company/.../assignments/{id}/end` **200** |
| suspend employee through the confirmation | no suspend POST before the confirm click; then success toast | `GET /company/.../employees/{id}` 200 · `POST /company/.../employees/{id}/suspend` **200** |
| unauthorized actor (plain user) | "You do not have access to this resource." + real correlation reference | `GET /company/.../employees?limit=5` **403** · `GET /company/.../assignments?limit=5` **403** |

```text
console / page errors ..................... 0
horizontal overflow (390 px, unauthorized)  0 px
```

Additional production-entry checks (dev server + built preview):

```text
GET /company/tenants/<t>/employees (through the dev server) ......... 401 (backend reached — ACC-02 fixed)
GET /tenants/<t>/spaces (through the dev server) ................... 401 (backend reached)
GET /tenants/<t>/company/employees (browser deep link) ............. 200 text/html (SPA still served)
Playwright E2E: anonymous /tenants/<uuid>/company .................. redirect to sign-in
```

---

## 14. Dev Proxy / ACC-02

```text
before : dev server returned SPA HTML for /company/** and the P17 space read → no real integration
after  : /company/** reaches the backend (401 anonymous, 200/201 for the authorized actor)
         ^/tenants/[^/]+/spaces reaches the backend
guard  : the /tenants rule is anchored, so console deep links under /tenants/:tenant_id/company/...
         keep being served by the SPA (verified above and by E2E)
```

This is the minimal necessary fix the HD allowed for ACC-02 (development environment only).

---

## 15. Security

```text
token handling ....... memory-only React ref inside AuthProvider; the module never reads, stores
                       or logs the token (it only calls the platform client)
browser storage ...... localStorage / sessionStorage / document.cookie → 0 uses in src
tenant override ...... no tenant in request body/query/header from the UI; the path segment is
                       built from the URL-derived, guard-confirmed tenant only
secret exposure ...... src and dist scans for DSN/keys/SECRET_KEY/VITE_API_TARGET → 0 findings
error exposure ....... UI renders only frozen messages + a correlation reference; no SQL, table,
                       constraint, stack or internal exception (asserted in tests)
HTML/eval ............ dangerouslySetInnerHTML / innerHTML= / eval( / new Function( → 0
suppressions ......... @ts-ignore / @ts-nocheck / eslint-disable → 0
authorization ........ the UI never decides allow/deny; 403 from the backend is final and is
                       rendered as no-access (verified with a real unauthorized actor)
```

---

## 16. Findings

```text
ACC-02  dev proxy missing the Company/P17 namespaces            → FIXED (minimal, dev-only, §14)
ACC-03  shared Table primitive has no overflow container        → ADDRESSED at page level
        (module table-scroll region; the shared primitive was NOT modified)
F-P21-RE-01  tenant mirrored after paint                        → ADDRESSED inside the module
        (company tenant guard: no request and no stale rendering before the context catches up,
         with unit + browser evidence); no global refactor was performed
F-P21-COR-01  timing-sensitive AppRouter assertion              → unchanged, OBSERVATION
        (the rewritten routing test awaits with findBy-style queries; the full suite passed
         repeatedly during this round — see the validation note below)

New observations (non-blocking, recorded for the validation gate):
OBS-1  The console login surface cannot produce a session token (device-verified sessions, frozen
       P17/P18) and P21 ships no device-enrolment UI. Company UI verification therefore mounted
       the real module with a real backend session; a browser "sign in then use Company" flow
       needs a future authorized device-enrolment surface. This is the same boundary recorded as
       F-P21-ACC-08 / ACC-08 in the Foundation acceptance.
OBS-2  List views show up to the requested page size; the frozen API returns the page count, not
       a total, so the UI states "n record(s) · page size m" instead of inventing a total.
OBS-3  Assignment lists enrich employee/space ids with names from the first page of the
       corresponding reads (limit 100); ids are shown as a fallback when enrichment is
       unavailable (e.g. a reader without employee access). No unbounded scan is performed.
OBS-4  The Assignment create dialog only offers spaces with status `active`; a space that is not
       active (or not visible to the actor) cannot be chosen. Backend validation remains final.
```

---

## 17. Non-Goals Respected

```text
RLS · API versioning · AuditWriter refactor · authorization transaction redesign · Redis ·
NOTIFY · production event activation · worker · new tables · new migrations · new permissions ·
new authorization engine · generic CRUD/low-code/plugin framework · frontend monolith refactor ·
Event UI · Worker UI · Permission admin · Tenant admin · Control-plane UI
— none of these were touched. The Company module contains exactly the five authorized pages
and the seven authorized actions; no Delete/Admin affordance exists.
```

---

## 18. Files

Created (all under `apps/frontend/`):

```text
src/modules/company/  api.ts · hooks.ts · tenant.ts · vocabulary.ts · paths.ts · routes.tsx ·
                      index.ts (updated) · company.module.css
src/modules/company/components/  StatusBadge · CompanyNav · CompanyStates · ConfirmDialog ·
                                 EmployeeFormDialog · AssignmentFormDialog
src/modules/company/pages/       OverviewPage · EmployeeListPage · EmployeeDetailPage ·
                                 AssignmentListPage · AssignmentDetailPage · CompanyNotFoundPage
src/modules/company/*.test.ts(x) 32 Company tests (api · tenant guard · overview · employee list ·
                                 employee detail · assignment pages)
src/test/companyHarness.tsx      test-only harness (no application import)
docs/architecture/P21_COMPANY_UI_IMPLEMENTATION_REPORT.md
```

Modified:

```text
src/platform/auth/AuthContext.tsx   + client exposure (one field)                    [§5]
vite.config.ts                      + /company and anchored /tenants/*/spaces proxy  [§5, ACC-02]
src/app/routing/AppRouter.tsx       mounts the module tree at /tenants/:tenant_id/company/*
src/app/routing/AppRouter.test.tsx  rewritten for the implemented module
src/modules/company/index.ts        placeholder status → IMPLEMENTED + module exports
```

Deleted:

```text
src/app/routing/pages/CompanyPlaceholderPage.tsx   (placeholder superseded by the module)
```

Unchanged: backend, migrations, database, permissions, platform error/auth/tenant semantics,
design tokens, shared primitives (including the Table primitive), E2E specs.

---

## 19. Database and Git Boundary

```text
isolated DB uap_p21_ui ....... created, used, dropped; database list restored to
                               {uap, uap_b1_test, uap_test}
formal DB `uap` .............. public tables = 0 (unchanged; read-only queries only)
shared test DB `uap_b1_test` . alembic 0017_p13_seed · users 0 · tenants 0 · roles 1 ·
                               audit 0 · events 0 (unchanged)
containers ................... uap-p21-ui-api removed; no residue; no listener on 8000/5199/4173
git .......................... HEAD 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (unchanged)
                               staged 0 · tags 16 · no commit / tag / push
historical dirty files ....... preserved untouched
```

---

## 20. Limitations and Residual Risks

```text
1. Authenticated browser entry: the production login form cannot yield a token without a verified
   device (OBS-1). All authenticated Company UI evidence was produced with the real module + real
   backend session; a full "sign in → Company" browser path needs a future device-enrolment
   authorization.
2. Assignment space choice is limited to the actor's active spaces (backend membership read). An
   actor with no active space sees an explicit hint instead of an empty picker.
3. Lists are page-sized reads (no total from the frozen API); no pagination control is offered
   because the frozen contract exposes limit only.
4. The module stores no server data in a global store: revisit-on-navigation is intentional
   (fresh read per page) and acceptable for V1.
5. Employee↔user binding, delete and admin surfaces remain intentionally absent (frozen decisions).
```

---

## 21. Final Status

```text
P21 COMPANY UI IMPLEMENTATION = COMPLETE
READY FOR BOT VALIDATION / GATE

Pages ........... Overview · Employees · Employee detail · Assignments · Assignment detail
Actions ......... Employee Create/Edit/Suspend/Terminate · Assignment Create/Edit/End
Data ............ real Company API + real authorization; no mock, no fake success, no no-op button
Tenant safety ... URL authority + module guard (no wrong-tenant request, no stale rendering)
UX .............. loading · empty · error · validation · confirmation · pending · toasts · responsive
Tests ........... 20 files / 132 tests / 0 failed · coverage 94.25% stmts
Typecheck/Build/E2E  PASS
Security ........ PASS · Backend/schema/migration/permissions UNCHANGED

RELEASE = NOT AUTHORIZED · COMMIT = NOT AUTHORIZED · TAG = NOT AUTHORIZED · PUSH = NOT AUTHORIZED
NEXT = P21 Company UI Validation / Gate (separate authorization)
HARD STOP = ACTIVE
```

Per HD-P21-01, this round stops here: no Company UI acceptance sign-off, no release, no commit,
no tag, no push, and no automatic entry into P22.
