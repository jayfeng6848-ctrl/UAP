# P21 COMPANY UI VALIDATION / GATE REPORT

Mode: `READ → VERIFY → TEST → AUDIT → GATE → REPORT → STOP` (no source change in this round)

Predecessor evidence (not overwritten): `P21_COMPANY_UI_IMPLEMENTATION_REPORT.md`

## FINAL GATE

```text
P21 COMPANY UI IMPLEMENTATION = PASS

F-P21-RE-01 = CLOSED     (tenant guard: zero request while unresolved, correct tenant after switch)
ACC-02      = CLOSED     (/company/** and /tenants/{id}/spaces reach the backend; SPA deep links intact)
ACC-03      = CLOSED     (page-level table scroll; shared primitive NOT modified)
F-P21-COR-01 = NON-BLOCKING / OBSERVATION   (suite ran green throughout this round)
F-P21-COR-02 = RESOLVED  (Dialog is now consumed by Company UI and present in the bundle)
F-P21-COR-03 = N/A
OBS-1..4     = NON-BLOCKING / OBSERVATION

P21 COMPANY UI ACCEPTANCE = NOT EXECUTED  (separate authorization required)
RELEASE = NOT AUTHORIZED · COMMIT = NOT AUTHORIZED · TAG = NOT AUTHORIZED · PUSH = NOT AUTHORIZED
HARD STOP = ACTIVE
```

Every PASS below is stated as "PASS because …" with the measurement that produced it.

---

## CURRENT STAGE

`P21 COMPANY UI VALIDATION / GATE` — the gate that judges whether the authorized Company UI
implementation is correct. This round is **not** acceptance, not release, and not a correction:
no source file was modified.

## HUMAN AUTHORIZATION

```text
HD-P21-01 — P21 Company UI Implementation Authorization
  granted : Company UI implementation (5 pages · Employee Create/Edit/Suspend/Terminate ·
            Assignment Create/Edit/End) on the accepted Foundation + Company API
  not granted : acceptance sign-off · release · commit · tag · push · P22
this round : validation / gate of that implementation (read-only + two evidence writes)
```

## BASELINE (re-measured, not inherited)

```text
git rev-parse HEAD ............. 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
git branch --show-current ...... main
git log -1 --oneline ........... 08a0485 release: UAP v0.1.17 P18 control plane
git diff --cached .............. 0 entries (staged = 0)
git tag ........................ 16
git status --porcelain ......... 211 = 16 under apps/frontend/** + 195 historical
git diff --check ............... clean (only the 4 pre-existing CRLF warnings)
historical dirty files ......... preserved; no clean · no reset · no restore · no stash · no add .
```

## SCOPE

PASS because the implemented surface equals the authorized surface:

```text
authorized pages    : Overview · Employees · Employee detail · Assignments · Assignment detail   → all present
authorized actions  : Employee Create/Edit/Suspend/Terminate · Assignment Create/Edit/End        → all present
authorized platform : AuthContext · vite.config.ts (both minimal and Company-serving)            → §CHANGES
forbidden surfaces  : Delete · Admin · employee login · token API · Event UI · Worker UI ·
                      backend feature change · new permission · migration · RLS · API versioning  → 0 occurrences
```

Forbidden-scope scan over the production source returned only false positives, each checked:
`DELETE` appears once as the `HttpMethod` type union in the platform client; every `event` hit is a
DOM event handler (`onChange`, keyboard handlers); no `/admin`, employee-login or event/worker
component exists. The Company module exposes exactly the authorized pages and actions.

## CHANGES

```text
Company UI workspace : added (26 files under src/modules/company/** + 1 test harness)
platform-adjacent    : AuthContext (1 added field: the existing client is exposed) · vite.config.ts
                       (2 development proxy rules) — both required by the Company UI, see §BROWSER/§FINDINGS
application routing  : AppRouter mounts the module tree under the existing auth + tenant boundaries
placeholder removal  : CompanyPlaceholderPage.tsx deleted (superseded by the module)
no other source change: backend · schema · migration · permissions · design tokens · shared primitives ·
                       error/auth/tenant semantics · e2e specs — all unchanged
```

## FILES

```text
added (27)
  src/modules/company/: api.ts · hooks.ts · tenant.ts · vocabulary.ts · paths.ts · routes.tsx ·
      index.ts (rewritten) · company.module.css
  src/modules/company/components/: StatusBadge · CompanyNav · CompanyStates · ConfirmDialog ·
      EmployeeFormDialog · AssignmentFormDialog
  src/modules/company/pages/: OverviewPage · EmployeeListPage · EmployeeDetailPage ·
      AssignmentListPage · AssignmentDetailPage · CompanyNotFoundPage
  src/modules/company/*.test.ts(x): api · tenantGuard · OverviewPage · EmployeeListPage ·
      EmployeeDetailPage · AssignmentPages
  src/test/companyHarness.tsx (test-only)

modified (Company-UI-relevant)
  src/platform/auth/AuthContext.tsx     → +client (1 field)            [platform, justified]
  vite.config.ts                        → +/company, +^/tenants/[^/]+/spaces (dev) [config, justified]
  src/app/routing/AppRouter.tsx         → mounts the module route tree
  src/app/routing/AppRouter.test.tsx    → rewritten for the implemented module
  src/modules/company/index.ts          → placeholder status → IMPLEMENTED

modified (pre-existing Foundation round, NOT this implementation)
  apps/frontend/README.md · apps/frontend/package.json · apps/frontend/src/main.tsx

deleted (1)
  src/app/routing/pages/CompanyPlaceholderPage.tsx

evidence (allowed writes)
  docs/architecture/P21_COMPANY_UI_VALIDATION_GATE_REPORT.md · UAP_项目全程记录本.md
```

## ROUTES

PASS because the real router matches the frozen AL form and every route was exercised:

| Console path | Route owner | Evidence |
| --- | --- | --- |
| `/tenants/:tenant_id/company` | app parent `.../company/*` → module index → OverviewPage | rendered in browser (overview testid, real data) |
| `/tenants/:tenant_id/company/employees` | module `employees` | rendered; real list + create |
| `/tenants/:tenant_id/company/employees/:employee_id` | module `employees/:employee_id` | rendered at 390/834/1440 with real data |
| `/tenants/:tenant_id/company/assignments` | module `assignments` | rendered; real list + create |
| `/tenants/:tenant_id/company/assignments/:assignment_id` | module `assignments/:assignment_id` | rendered at 390/834/1440 with real data |
| any other `.../company/*` | module `*` → CompanyNotFoundPage | "Company page not found" observed |
| any non-company path | app `*` → NotFoundPage | unchanged |

```text
duplicate Company router ....... none (one module <Routes>, one app parent route)
duplicate tenant router ........ none (single TenantBoundary)
shadow route ................... none (module routes are relative children of the parent match)
unexpected catch-all ........... only the two intended 404 surfaces (module + app)
direct navigation .............. SPA serves the deep link, module renders (verified)
refresh ........................ same SPA + guard path (verified via fresh page loads)
```

## API

PASS because the client uses exactly the frozen accepted contract, and no endpoint was added:

```text
endpoint count in apps/api/routes/company.py ......... 11 (unchanged; back-end untouched by this round)
prefix .............................................. /company/tenants/{tenant_id}/...
paths issued by the module (observed in the browser run):
  POST/GET  /company/tenants/{t}/employees                          201 / 200
  GET/PATCH /company/tenants/{t}/employees/{id}                     200 / 200
  POST      /company/tenants/{t}/employees/{id}/suspend|terminate   200 / 200 (409 on replay)
  POST/GET  /company/tenants/{t}/assignments                        201 / 200
  GET/PATCH /company/tenants/{t}/assignments/{id}                   200 / 200
  POST      /company/tenants/{t}/assignments/{id}/end               200 (409 on replay)
  GET       /tenants/{t}/spaces                                     200 (P17 space read for the picker)
DTO mapping .......... api.ts mirrors EMPLOYEE_FIELDS (11) and ASSIGNMENT_FIELDS (10) exactly
mock / fake data ..... none: every value rendered came from these responses
scattered fetch ...... 1 occurrence in the whole source tree (platform/api/client.ts)
```

## AUTH

PASS because the Company UI reuses the platform auth boundary without adding a second one:

```text
token storage ........ memory-only React ref inside AuthProvider; the module never reads/writes the token
browser storage ...... localStorage · sessionStorage · document.cookie → 0 occurrences in src
401 handling ......... real revoked session → the list surfaced "Your session has ended. Please sign in
                       again."; recovery was attempted once per 401'd request (2 attempts for the 2
                       concurrent overview reads) and the client never loops (unit tests: one-shot)
refresh / logout ..... the existing /sessions/refresh and /sessions/logout are the only endpoints used
Company-specific auth  none (no second login, no role check, no token endpoint)
```

## TENANT

PASS because the URL remains the only tenant authority and the module refuses to act early:

```text
stale context (URL tenant A, context tenant B), module rendered without the boundary:
   → resolving state shown, 0 API calls issued  (browser scenario S5: newCalls = [])
tenant switch A → B:
   → unit evidence: all subsequent requests target B; A's row disappears; no request to A after the switch
not-yet-ready guard ....... requests are issued only after URL tenant === context tenant
tenant source in requests . path segment only; no body/query/header tenant from the UI
cross-tenant behaviour .... a tenant without resource projection denies (403, see §AUTHORIZATION)
browser tenants used ...... tenant A (data) and tenant B (empty) — both addressed by URL only
```

## AUTHORIZATION

PASS because denials come from the backend, not from the frontend:

```text
plain user (no Company grant) → GET/POST employees, GET assignments, suspend → real 403
platform admin + tenant without resource projection → GET/POST employees, GET assignments → real 403
anonymous → 401
UI on 403 → "You do not have access to this resource." + real correlation reference (browser S7)
frontend role/scope shortcuts → 0 occurrences (no ACL engine, no permission inference)
```

## EMPLOYEE

PASS because each authorized action was executed against the real API and the UI reflected the result:

| Action | Real result | UI evidence |
| --- | --- | --- |
| List | 200 | table with real rows + status text |
| Detail | 200 | profile fields, assignments section |
| Create | **201** | row appears, "Employee created." toast, list reload 200 |
| Edit | **200 (PATCH)** | title visible after reload; only changed fields sent |
| Suspend | **200** | confirmation required (no POST before confirm), "Employee suspended." toast, status → suspended |
| Terminate | **200** | status → terminated (API-level) |
| Suspend again | **409** | stale-state browser run: out-of-band suspend 200, then the UI confirm returned 409 and the dialog rendered the conflict message |
| Terminate again | **409** | API-level replay check |
| Duplicate employee number | **409** | dialog stays open with the conflict message |
| Invalid employee number | **422** | API-level; the UI blocks the frozen-pattern case before submitting (by design) |
| Unknown employee id | **422** | UI renders the validation/not-found message |

No fake success was observed: every success toast was preceded by the corresponding 2xx response in
the recorded network trace.

## ASSIGNMENT

PASS because each authorized action was executed against the real API:

| Action | Real result | UI evidence |
| --- | --- | --- |
| List | 200 | rows enriched with real employee/space names |
| Detail | 200 | target, role, status |
| Create | **201** | pickers filled from `GET /tenants/{t}/spaces` (200) and the Company employee read (200); "Assignment created." toast |
| Edit role | **200 (PATCH)** | role updated after reload |
| End | **200** | confirmation required; "Assignment ended." toast; detail shows `ended` |
| End again | **409** | API-level replay check |
| Patch after end | **409** | API-level check |
| Employee / Space selectors | real API-backed | options came from the two real reads; IDs (not hard-coded names) are submitted |

## ERROR HANDLING

PASS because each class produced its own frozen message and no internal detail leaked:

```text
401 → "Your session has ended. Please sign in again."            (real revoked session)
403 → "You do not have access to this resource."                 (real plain-user denial)
404 → module "Company page not found" for an unknown company sub-path (UI-level, no API call)
409 → "This change conflicts with the current state. Reload and try again."  (real lifecycle conflict)
422 → "The request could not be processed. Check the values and try again." (real unknown employee id)
5xx → "Something went wrong. Please try again." + retry          (backend stopped: dev proxy returned 500; retry recovered after restart)
network → "The service could not be reached. Please try again."  (unreachable target)
every error surface carried a correlation reference and a retry action, and none rendered SQL, table
names, constraint names, stack traces or internal exception text
```

---

## DIALOG

PASS because the Company UI now consumes the corrected Dialog primitive, and it was exercised in a
real browser (not only in unit tests):

```text
scenario S4 (create-employee dialog, real Chromium, real keyboard):
  initial focus ............ first control inside the dialog
  Tab trail ................ INPUT(:rl:) → INPUT(:rm:) → INPUT(:rn:) → BUTTON → BUTTON → INPUT(:rl:)
                             (walks every control and cycles back to the first)
  containment .............. after 5 Tabs and 2 Shift+Tabs focus was still inside the dialog (true/true)
  Escape ................... dialog closed; focus returned to the trigger button
  Cancel ................... dialog closed
scenario S3 / S1 (confirmation dialogs):
  confirm .................. the mutation is sent only after the explicit confirmation click
  Escape while pending ..... the dialog refuses to close mid-mutation (confirmed by the component contract)
  stale-state 409 .......... the confirmation dialog stays open and renders the conflict message
Foundation Dialog unit suite (17 tests) also re-executed green in this round.
```

## RESPONSIVE

PASS because every page and a dialog were measured at three widths with zero horizontal overflow:

| Viewport | Pages measured | overflowX | Dialog |
| --- | --- | --- | --- |
| 390 × 844 | overview · employees · employee detail · assignments · assignment detail | 0 px on all five | 358 px wide, left 16 px, fits |
| 834 × 1112 | same five | 0 px on all five | 480 px wide, centred, fits |
| 1440 × 900 | same five | 0 px on all five | 480 px wide, centred, fits |

```text
navigation ............ module nav visible and wrapped at every width
tables ................ rendered inside the module's scroll region (page-level solution)
dialogs / forms ....... fit within the viewport; inputs full-width on mobile
shared primitive regressions ........ none observed (the Table primitive was not modified)
```

## BROWSER

Manual browser evidence (real Company module + real FastAPI + real session through the dev proxy).
The console login surface cannot mint a device-verified token (frozen P17/P18) and P21 ships no
enrolment UI, so the authenticated pages were driven by mounting the real module with a real
backend-issued session — recorded accurately as manual browser evidence, not as an E2E suite.

```text
recorded real network trace (through the dev proxy, origin localhost:5199):
  POST 201 /sessions                                (admin session)
  GET  200 /company/.../employees?limit=5           (overview)
  GET  200 /company/.../assignments?limit=5         (overview)
  POST 201 /company/.../employees                   (UI create)
  GET  200 /company/.../employees?limit=25          (list reload)
  GET  200 /company/.../employees/{id}              (detail)
  PATCH 200 /company/.../employees/{id}             (UI edit)
  POST 200 /company/.../employees/{id}/suspend      (UI confirm)
  GET  200 /tenants/{t}/spaces                      (assignment picker source)
  GET  200 /company/.../employees?limit=100         (assignment picker source)
  POST 201 /company/.../assignments                 (UI create)
  POST 200 /company/.../assignments/{id}/end        (UI confirm)
  POST 409 /company/.../employees/{id}/suspend      (stale-state confirm)
  GET  403 /company/.../employees?limit=5           (unauthorized actor)
  GET  403 /company/.../assignments?limit=5         (unauthorized actor)
  GET  422 /company/.../employees/{unknown}         (unknown id)
  GET  500 (dev proxy, backend stopped)             (5xx path) → recovered after restart
console / page errors ....... 0 unexpected (the only console entries were the expected HTTP statuses
                              for the deliberate 409 / 403 / 422 / 500 cases)
UI states verified .......... loading · empty (tenant B) · error (403/422/500/network) · success toasts
                              · pending buttons · confirmation dialogs
```

## SECURITY

PASS because the scans were re-executed in this round:

```text
executable source scan .... localStorage · sessionStorage · document.cookie= · eval( · new Function( ·
                            dangerouslySetInnerHTML · innerHTML= → 0 findings (one documentation comment only)
secret scan (src + dist) ... postgres:// · sk-… · PRIVATE KEY · SECRET_KEY · DATABASE_URL ·
                            VITE_API_TARGET · localhost:8000 → 0 findings
suppressions .............. @ts-ignore · @ts-nocheck · eslint-disable → 0
token leakage ............. no token in storage, no token in logs, no token rendered
existing scanner .......... src/test/security.test.ts re-run green (6/6) — no new scanner introduced
```

## ARCHITECTURE

PASS because the boundaries were re-checked statically:

```text
Core → Domain ................... 0 (core/** import scan)
frontend → backend packages ..... 0 (no import of services/ · infrastructure/ · apps/api/ · domains/ · core/)
frontend → database ............. 0 (single fetch() in platform/api/client.ts; no driver, ORM or SQL)
Company logic inside Core/Platform/shared primitives:
   primitives ......... 0 Company references (only a doc comment in Dialog)
   platform ........... 1 intentional addition: AuthContext exposes the existing client (1 field)
   shared design ...... 0 (module uses tokens only)
module → app imports ........... 0 (the app mounts the module; no reverse dependency)
```

## DATABASE

PASS because no schema, migration or formal-database write occurred, and the temporary environment
was removed:

```text
formal DB `uap` ................. public tables = 0 (unchanged; read-only queries only)
shared test DB `uap_b1_test` .... alembic 0017_p13_seed · users 0 · tenants 0 · roles 1 ·
                                  audit 0 · events 0 (unchanged)
temporary isolated DB ........... uap_p21_gate — created, migrated (as uap_migrator, head 0020),
                                  seeded, used for validation, then DROPPED
database list after cleanup ..... {uap, uap_b1_test, uap_test} (restored)
containers ...................... uap-p21-gate-api removed; no residue; no listener on 8000/5199/4173
schema / migration changes ...... 0 in the repository
```

---

## TESTS

```text
exact command : npm run test:run
result        : Test Files 20 passed (20) · Tests 132 passed (132) · failed 0 · skipped 0
                (duration ≈ 8.1 s; re-executed in this round, not quoted from the implementation report)
focused Company run : the six Company test files plus the routing test passed within that run
```

## COVERAGE

```text
exact command : npx vitest run --coverage --coverage.reporter=text
All files     : 94.25 % statements · 88.81 % branches · 87.31 % functions · 94.25 % lines
Company pages : 95.59 % statements (OverviewPage 100 %)
```

## TYPECHECK

```text
exact command : npm run typecheck   → exit 0 (strict; no suppression comments)
```

## BUILD

```text
exact command : npm run build      → PASS · 81 modules
dist/index.html 0.40 kB · dist/assets/index-*.css 6.20 kB (gzip 1.63) · index-*.js 223.14 kB (gzip 71.36)
Company modules included .... present (bundle markers: "Company overview", "New employee",
                              "New assignment", "company-nav", "Resolving tenant context")
Dialog no longer tree-shaken  present ("uap-dialog-backdrop")
new dependency ............... none
```

## E2E

```text
exact command : npm run e2e       → 2 passed · 0 failed · 0 skipped
coverage ...... boot + anonymous deep-link fallback only
statement ..... these two specs do NOT cover Company flows; the Company browser validation above is
                manual browser evidence and is labelled as such
```

## GIT

```text
HEAD .......................... 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (unchanged)
staged ........................ 0
tags .......................... 16 (unchanged)
porcelain ..................... 211 = 16 frontend + 195 historical (unchanged)
diff --check .................. clean
commit / tag / push ........... none
source changes this round ..... 0 (only the gate report and the record-book entry were written)
```

---

## FINDING RECLASSIFICATION (re-verified, history preserved)

| Finding | Was | Now | Evidence |
| --- | --- | --- | --- |
| `F-P21-RE-01` tenant mirrored after paint | OPEN / OBSERVATION | **CLOSED** | module guard: stale context → resolving state + 0 API calls (browser S5, unit test); A→B switch targets B only and drops A (unit test); requests only after URL tenant === context tenant |
| `F-P21-COR-01` timing-sensitive AppRouter assertion | NON-BLOCKING / OBSERVATION | **NON-BLOCKING / OBSERVATION** | this round: 20/20 files green in every executed run (test:run, coverage, E2E); no failure reproduced; unchanged and not modified |
| `F-P21-COR-02` Dialog not consumed / tree-shaken | OBSERVATION | **RESOLVED (historical record kept)** | Dialog is now consumed by the Company dialogs and present in the built bundle |
| `F-P21-COR-03` nested / multiple dialogs | N/A | **N/A** | no nesting system exists or was designed |
| `ACC-02` dev proxy missing the Company namespace | OPEN | **CLOSED** | `/company/**` → backend (401 anonymous, 404 unknown path); `/tenants/{t}/spaces` → backend (401); SPA deep links still served; `/tenants/{t}/members` correctly NOT proxied |
| `ACC-03` Table overflow | OPEN | **CLOSED (page-level solution)** | 390 px measurement: 0 px overflow on every Company page; the shared Table primitive was **not** modified |
| `OBS-1` login cannot mint a device-verified session | OBSERVATION | **NON-BLOCKING / OBSERVATION** | stated precisely: authenticated Company validation used a real backend session; no enrolment UX was validated (it does not exist in P21) |
| `OBS-2` list counts are page-size bound | OBSERVATION | **NON-BLOCKING / OBSERVATION** | UI shows "n record(s) · page size m"; no total is invented |
| `OBS-3` name enrichment from the first page of reads | OBSERVATION | **NON-BLOCKING / OBSERVATION** | ids are shown when enrichment is unavailable; no unbounded scan |
| `OBS-4` assignment picker offers active spaces only | OBSERVATION | **NON-BLOCKING / OBSERVATION** | explicit "no active space" hint; backend validation remains final |

No historical finding was deleted, rewritten or erased; each row keeps its original description and
adds the resolution evidence where applicable.

---

## FINAL GATE (PASS because …)

```text
scope correct ................ PASS because the implemented pages/actions equal the authorized set and the
                               forbidden surfaces are absent (source scan + route inspection)
real API integration ......... PASS because every read/mutation in the browser trace hit the real
                               /company/... API with the frozen status codes
auth correct ................. PASS because the token stays in memory and the platform 401/refresh/logout
                               path is reused (0 storage APIs, 0 second auth system)
tenant safe .................. PASS because a stale tenant context produced zero requests and no stale
                               rendering, and switching tenants retargets every request (F-P21-RE-01 CLOSED)
authorization preserved ...... PASS because 403s came from the backend for both the permission gate and
                               the resource-projection gate, and the UI only renders them
employee flows correct ....... PASS because list/detail/create/edit/suspend/terminate ran against the real
                               API with 200/201 and the invalid transitions returned 409
assignment flows correct ..... PASS because list/detail/create/edit/end ran against the real API with
                               200/201/200 and end-again returned 409
error semantics correct ...... PASS because 401/403/404/409/422/5xx/network each produced their own
                               frozen message with no internal detail
responsive correct ........... PASS because five pages × three widths measured 0 px overflow and dialogs fit
dialog behavior correct ...... PASS because focus entered, trapped (both directions), Escape/Cancel closed
                               and focus returned to the trigger
tests PASS ................... 20 files / 132 tests / 0 failed / 0 skipped (re-executed)
typecheck PASS ............... exit 0
build PASS ................... Company + Dialog present, 223.14 kB bundle
E2E PASS ..................... 2/2 (boot + anonymous deep link — Company flows are manual browser evidence)
security clean ............... 0 findings, 0 suppressions
Core → Domain = 0 ............ static scan 0
DB unchanged ................. formal and shared DBs unchanged; isolated DB dropped
Git boundary intact .......... HEAD/staged/tags unchanged, no commit/tag/push
no blocking finding .......... every finding re-classified, none blocking

P21 COMPANY UI IMPLEMENTATION = PASS
P21 COMPANY UI ACCEPTANCE = NOT EXECUTED
RELEASE = NOT AUTHORIZED · COMMIT = NOT AUTHORIZED · TAG = NOT AUTHORIZED · PUSH = NOT AUTHORIZED
```

## NEXT AUTHORIZED STEP

```text
P21 COMPANY UI ACCEPTANCE
  — requires a NEW independent acceptance authorization
  — this round does not start it, does not sign it off and does not prepare a release
```

## HARD STOP

```text
HARD STOP = ACTIVE
```

This round read and audited the implementation, re-executed the regression gates, rebuilt an isolated
real-backend environment, ran API-level and real-browser functional/authorization/tenant/dialog/
responsive/error-path validation, restored the environment, and wrote exactly two authorized
artifacts (this report and one append-only record-book entry). No source, configuration, test,
backend, schema, migration, permission or database change was made, and no commit, tag or push was
created.
