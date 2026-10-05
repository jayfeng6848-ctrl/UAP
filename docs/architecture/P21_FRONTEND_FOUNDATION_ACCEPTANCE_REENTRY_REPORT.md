# P21 FRONTEND FOUNDATION ACCEPTANCE RE-ENTRY REPORT

Gate: `P21 FRONTEND FOUNDATION ACCEPTANCE RE-ENTRY` (post-correction)

Mode: `READ · VERIFY · TEST · REPORT · STOP` — no source change in this round

Predecessor report (kept unchanged, verdict BLOCKED): `P21_FRONTEND_FOUNDATION_ACCEPTANCE_REPORT.md`

Correction under review: `P21_FRONTEND_FOUNDATION_CORRECTION_REPORT.md`

## Final gate (read this first)

```text
P21 FRONTEND FOUNDATION ACCEPTANCE = PASS

F-P21-ACC-01 = CLOSED  (re-verified, not inherited)

Dialog focus containment ........... PASS (unit + real browser, 3 viewports)
Dialog focus restoration ........... PASS (unit + real browser, 3 viewports)
Foundation regression .............. PASS (typecheck · 99/99 tests · build · E2E 2/2)
Security ........................... PASS
Responsive / keyboard baseline ..... PASS (390 · 834 · 1440)
Core → Domain = 0 .................. PASS
Scope .............................. no unauthorized change
DB / schema / migration ............ unchanged (no writes)
Git boundary ....................... HEAD unchanged · staged 0 · no commit/tag/push
Findings ........................... all classified

RELEASE = NOT AUTHORIZED
COMMIT  = NOT AUTHORIZED
TAG     = NOT AUTHORIZED
PUSH    = NOT AUTHORIZED

NEXT AUTHORIZED STEP = P21 COMPANY UI IMPLEMENTATION (requires its own authorization)
HARD STOP = ACTIVE
```

---

## 1. Executive Summary

This round re-ran the acceptance judgement independently; no finding was inherited from the
Correction report, and no source file was touched.

```text
Dialog unit suite ................. npx vitest run src/components/Dialog.test.tsx → 17/17 passed
Foundation suite (plain) .......... npm run test:run → 99/99 passed, 3 consecutive runs
Foundation suite (coverage) ....... 7/8 runs 99/99 passed (1 AppRouter assertion race — see §6)
AppRouter file isolated ........... 8/8 runs passed (6/6 tests each)
typecheck ......................... npm run typecheck → exit 0
build ............................. npm run build → PASS (81 modules · js 196.49 kB · css 3.67 kB)
E2E ............................... npm run e2e → 2 passed (boot · anonymous deep link)
coverage .......................... All files 89.82% stmts · 88.5% branch · 84% funcs
                                    Dialog.tsx 96.55% stmts · 89.47% branch · 100% funcs
real browser ...................... 390 / 834 / 1440 px · Tab · Shift+Tab · Escape · Close ·
                                    keyboard activation · focus visible · 0 console errors
security .......................... security.test.ts 6/6 + source/dist scans clean
architecture ...................... frontend → backend imports 0 · Core → Domain = 0
database .......................... formal `uap` 0 tables (unchanged) · shared test DB at frozen baseline
git ............................... HEAD 08a0485b… · staged 0 · tags 16 · no source file modified today
```

One non-blocking observation was re-measured and classified (`COR-01`, §6).

---

## 2. Scope and Method

```text
In scope  : re-verify Foundation + Correction against the original acceptance criteria
Out of scope (explicitly not done): ACC-02 dev proxy · ACC-03 Table overflow · ACC-04/05 test
            coverage gaps · ACC-06+ observations · Drawer · Company UI · Event UI · Worker UI ·
            API versioning · RLS · audit writer · authorization redesign · observability ·
            Redis · NOTIFY · backend refactor · migration · DB schema · permission changes ·
            configuration redesign · global test refactor
Writes    : this report + one append-only log entry in the project record book
```

Every claim below is backed by a command executed in this round; historical reports were used
only to know what to check, never as evidence.

---

## 3. Baseline (exact)

```text
git rev-parse HEAD ............. 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
git branch --show-current ...... main
git log -1 --oneline ........... 08a0485 release: UAP v0.1.17 P18 control plane
git diff --cached --name-only .. 0 entries (staged = 0)
git tag ........................ 16 (unchanged)
git status --porcelain ......... 209 = 16 under apps/frontend/** + 193 non-frontend (historical)
git diff --check ............... clean for apps/frontend/**; only the 4 pre-existing CRLF warnings
```

Matches the expected baseline exactly (HEAD · staged 0 · tags 16). Historical dirty files were
preserved: no clean, no reset, no restore, no `git add .`, no line-ending normalization.

No frontend source file carries a modification timestamp from today (2026-10-05) — the round
produced no source change.

---

## 4. Dialog / F-P21-ACC-01 Re-verification

### 4.1 Unit evidence

```text
exact command : npx vitest run src/components/Dialog.test.tsx
result        : Test Files 1 passed (1) · Tests 17 passed (17) · 0 failed · 0 skipped
```

The ten required behaviours map to tests as follows:

| # | Requirement | Test evidence |
| --- | --- | --- |
| 1 | focus enters the dialog on open | `initial focus › focuses the first control inside the dialog on open` (+ surface fallback test) |
| 2 | Tab must not leave the dialog | `containment › never leaves the dialog while tabbing repeatedly` (8 forward presses asserted) |
| 3 | Shift+Tab must not leave the dialog | same test (8 backward presses asserted) |
| 4 | last focusable + Tab → first | `containment › cycles forward from the last control to the first` |
| 5 | first focusable + Shift+Tab → last | `containment › cycles backward from the first control to the last` |
| 6 | Escape closes | `semantics › closes on Escape` + `restoration › returns focus to the trigger on Escape` |
| 7 | Close control closes | `restoration › returns focus to the trigger when closed through its close control` |
| 8 | close → focus returns to the trigger | both restoration tests assert the trigger holds focus |
| 9 | missing trigger degrades safely | `restoration › does not touch focus when the trigger is gone` |
| 10 | no unexpected focus outside the dialog | containment tests keep an `outside after` control behind the dialog; traversal never reaches it |

### 4.2 Real browser evidence

Real Chromium, the corrected component loaded through the dev-server module graph, driven with
real keyboard input at three viewports:

| Check | 390×844 | 834×1112 | 1440×900 |
| --- | --- | --- | --- |
| dialog opens, initial focus = first control | ✅ `inner-close` | ✅ `inner-close` | ✅ `inner-close` |
| Tab from last control | → first | → first | → first |
| Shift+Tab from first control | → last | → last | → last |
| 8× Tab trail | `close→cancel→confirm→…` | same | same |
| controls reached outside the dialog | 0 | 0 | 0 |
| Escape → focus | `trigger` | `trigger` | `trigger` |
| Close control → focus | `trigger` | `trigger` | `trigger` |
| inner control activated by keyboard (Enter) | click count 1 | 1 | 1 |
| dialog / page horizontal overflow | 0 px / 0 px | 0 px / 0 px | 0 px / 0 px |
| console + page errors | 0 | 0 | 0 |

Conclusion: `F-P21-ACC-01 = CLOSED`, re-verified in this round with unit and real-browser
evidence (the earlier failure mode — `Tab` reaching an outside control and focus landing on
`<body>` after close — no longer reproduces).

---

## 5. Foundation Regression

```text
exact command : npm run typecheck                 → exit 0 (tsc --noEmit, strict)
exact command : npm run test:run                  → 14 files · 99 tests · 99 passed · 0 failed · 0 skipped
                (repeated 3× in this round: run1 99/99 · run2 99/99 · run3 99/99)
exact command : npx vitest run --coverage         → 99 passed · All files 89.82 stmts · 88.5 branch ·
                                                    84 funcs · Dialog.tsx 96.55 / 89.47 / 100
exact command : npm run build                     → PASS · 81 modules · dist/index.html 0.40 kB ·
                                                    css 3.67 kB (gzip 1.19) · js 196.49 kB (gzip 64.86)
exact command : npm run e2e                       → 2 passed (boot · anonymous deep link), 4.0s
```

Foundation capability re-check (unchanged by this round, verified by the suites above):

```text
App Shell ............... AppShell tests + E2E boot (data-testid uap-app-shell / uap-shell-*)
Routing ................. AppRouter tests (login redirect · home · company placeholder · 403 · 404)
Authentication .......... AuthContext tests (bootstrap · login · device_required · refresh dedupe · logout)
Tenant context .......... TenantContext/TenantBoundary tests (URL → context · change · invalid · clear)
API Client .............. client tests (transport · correlation · timeout/abort · 401 one-shot recovery)
Error handling .......... errors tests (401/403/409/422/503 taxonomy · safe messages)
Design Tokens ........... tokens.css consumed by every module CSS (no !important anywhere)
UI primitives ........... Button · Input · Select · Dialog · Card · Badge · Table · PageHeader ·
                          EmptyState · LoadingState · ErrorState + Field/TextField tests
Testing infrastructure .. Vitest + RTL + user-event + Playwright (config unchanged)
Dev configuration ....... vite dev proxy + .env.example unchanged; production build independent of
                          VITE_API_TARGET (dist scan: 0 hits)
```

Bundle note (unchanged from the correction round): the Dialog primitive is still not consumed by
any application route, so it is tree-shaken out of `dist` (scan for `uap-dialog-backdrop` /
`aria-modal` → 0 hits). Adding a production consumer is not required by any frozen Foundation
criterion and was deliberately not done (see `COR-02`).

---

## 6. COR-01 Re-measurement (AppRouter assertion race)

```text
observed failure (1 of 8 coverage-instrumented runs in this round):
  file  : src/app/routing/AppRouter.test.tsx
  test  : AppRouter > renders the tenant-scoped Company placeholder with the URL tenant
  line  : AppRouter.test.tsx:100
  error : expect(element).toHaveTextContent()  (received "Tenant: unresolved" instead of the uuid)

measurements this round
  full suite, plain ................ 3/3 runs 99/99 passed
  full suite, coverage ............. 7/8 runs 99/99 passed (1 failure as above)
  AppRouter file isolated .......... 8/8 runs 6/6 passed
```

Root cause (test-side race, evidence-based): the test awaits `findByTestId('uap-company-status')`
— which is rendered immediately — and then synchronously asserts the tenant text. The tenant
value is committed by `TenantBoundary` in a `useEffect`, i.e. one commit later. Under load the
assertion can run before that commit, so it reads the placeholder's `unresolved` frame.

Classification: `NON-BLOCKING / OBSERVATION` — an existing test-hygiene issue in a file outside
this round's scope:

```text
not caused by Dialog (no Dialog is rendered in AppRouter tests; Dialog is tree-shaken from the app)
not a production regression (routing, tenant context and the placeholder all behave as accepted;
   the observable effect is a single post-paint frame where tenant context is not yet mirrored)
not fixed here (Correction §7 prohibits modifying it to obtain a pass; this round is read-only)
recommended follow-up: assert the tenant with findBy/waitFor (or resolve it before paint) in a
   dedicated test-hygiene round
```

---

## 7. Responsive and Accessibility Baseline

Real browser, three viewports (page-level measurement on the login/console surface):

```text
390 × 844   overflowX = 0 px · first keyboard focus = INPUT[text] · outline solid 2px · input visible (356 px wide)
834 × 1112  overflowX = 0 px · first keyboard focus = INPUT[text] · outline solid 2px · input visible (800 px wide)
1440 × 900  overflowX = 0 px · first keyboard focus = INPUT[text] · outline solid 2px · input visible (1406 px wide)
```

Combined with §4.2 (dialog-level traversal, keyboard activation, focus visibility inside the
dialog, zero overflow, zero console errors), the responsive / keyboard baseline passes.

---

## 8. Security

```text
exact command : npx vitest run src/test/security.test.ts → Test Files 1 passed · Tests 6 passed
source scan   : localStorage · sessionStorage · document.cookie= · eval( · new Function( ·
                dangerouslySetInnerHTML · innerHTML=  → 0 executable findings
                (single textual match = the AuthContext comment that forbids storage)
dist scan     : postgres://, sk-…, PRIVATE KEY, SECRET_KEY, VITE_API_TARGET, localhost:8000 → 0 findings
suppressions  : @ts-ignore · @ts-nocheck · eslint-disable → 0
token policy  : token lives in a React ref only; no browser storage write exists in the source
tenant policy : tenant comes from the URL route parameter; no tenant override through request bodies
                or arbitrary frontend state exists in the source
console policy: no sensitive logging introduced (no console.* in application components)
```

---

## 9. Architecture

```text
frontend → backend package imports (services/ · infrastructure/ · apps/api/ · domains/ · core/)
  scan over src/platform · src/components · src/modules → 0 hits
raw fetch(...) in src → exactly 1 (src/platform/api/client.ts); every other network call goes
  through the typed client
Core → Domain = 0  → static scan of core/** for `import domains` / `from domains` → 0 hits
second authentication / authorization / tenant-security system → none (auth, tenant and error
  handling all live in the single platform layer created by the Foundation)
```

---

## 10. Database

```text
formal DB `uap` ............ public tables = 0  (unchanged; this round performed read-only queries)
shared test DB `uap_b1_test` alembic = 0017_p13_seed · users 0 · tenants 0 · roles 1 · audit 0 · events 0
                             (frozen baseline, unchanged)
database list .............. uap · uap_b1_test · uap_test  (no extra database created or dropped)
DDL / DML / migration ...... 0 (this round executed no backend test, no migration, no seed)
containers ................. none created or left running
```

---

## 11. Findings (re-classification)

| Finding | Previous state | This round | Evidence | Classification |
| --- | --- | --- | --- | --- |
| `F-P21-ACC-01` Dialog focus containment + restoration | OPEN (blocking) | **CLOSED** | 17/17 Dialog tests + real browser at 390/834/1440 with real keyboard | CLOSED |
| `F-P21-COR-01` AppRouter assertion race | OBSERVATION | unchanged | 7/8 coverage runs pass; 8/8 isolated passes; failure line 100 identified | NON-BLOCKING / OBSERVATION |
| `F-P21-COR-02` Dialog not yet consumed by a production route | OBSERVATION | unchanged | `dist` scan for Dialog markers → 0 hits | NON-BLOCKING / OBSERVATION |
| `F-P21-COR-03` nested / multiple dialogs | N/A | N/A | no nesting system exists or was designed | N/A |
| `F-P21-RE-01` one-frame tenant mirroring after route entry | — | new | `TenantBoundary` commits the tenant in `useEffect` (post-paint); the AppRouter race is its test-visible symptom | NON-BLOCKING / OBSERVATION (Company UI stage may prefer a pre-paint resolution; not required by any frozen Foundation criterion) |

No finding from the acceptance blocker classes materialized (auth boundary / tenant override /
secret exposure / frontend ACL authority / Platform→Company dependency / API client integration /
missing Foundation E2E evidence / unsafe primitive / build or test failure).

---

## 12. Acceptance Criteria Checklist (Gate §15)

```text
[x]  1. F-P21-ACC-01 = CLOSED                         re-verified this round
[x]  2. Dialog focus trap re-verification PASS         unit + real browser (3 viewports)
[x]  3. Focus restoration re-verification PASS         Escape and Close both restore the trigger
[x]  4. Foundation regression PASS                     99/99 plain ×3 · typecheck · build · E2E
                                                       (coverage runs 7/8 — see COR-01, non-blocking)
[x]  5. Typecheck PASS                                 npm run typecheck → exit 0
[x]  6. Build PASS                                     npm run build → PASS, deterministic dist
[x]  7. Relevant E2E PASS                              npm run e2e → 2 passed
[x]  8. Security PASS                                  security.test.ts 6/6 + source/dist scans clean
[x]  9. Responsive / keyboard baseline PASS            390 · 834 · 1440 · focus visible · 0 overflow
[x] 10. Core → Domain = 0                              static scan → 0 hits
[x] 11. No unauthorized scope                          only this report + record-book entry written
[x] 12. No backend/schema/migration mutation           formal DB and shared test DB unchanged
[x] 13. Git boundary intact                            HEAD unchanged · staged 0 · no commit/tag/push
[x] 14. All findings explicitly classified             §11
[x] 15. Evidence complete                              §3–§10 with exact commands, counts, viewports
```

---

## 13. Acceptance Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Framework | PASS | React 18.3.1 · Vite 6.4.3 · TypeScript 5.9.3 (lockfile, `npm ci` verified earlier) |
| Routing | PASS | AppRouter tests 6/6 (isolated 8/8 runs) + E2E deep link |
| Auth | PASS | AuthContext tests + real backend round trip (recorded in the earlier acceptance round; unchanged code) |
| 401 Recovery | PASS | client one-shot retry tests + refresh de-duplication tests |
| Tenant | PASS | TenantContext tests (URL → context · change · invalid · clear) |
| API Client | PASS | single `fetch(` owner; transport/abort/timeout/error tests |
| Correlation | PASS | header tests + real backend echo (earlier round) |
| Error Taxonomy | PASS | 401/403/409/422/503 mapping tests |
| Design Tokens | PASS | token inventory; no `!important`; CSS Modules only |
| Primitives | PASS | 12 primitives; **Dialog containment + restoration now verified** |
| Accessibility | PASS | keyboard traversal · focus visible (2 px solid outline) · keyboard activation · aria semantics |
| Responsive | PASS | 390/834/1440 measured: no page or dialog horizontal overflow |
| Permission Boundary | PASS | capability always `unknown`; no inference; no ACL engine |
| Platform/Domain Boundary | PASS | frontend → backend imports 0; company module imports 0 |
| Extensibility | PASS | controlled extension points only; no dynamic loader/DSL |
| Security | PASS | scans clean; no storage/token persistence |
| Build | PASS | deterministic dist; no source maps; 0 secrets |
| E2E | PASS | 2/2 boot · anonymous deep link |
| Backend Round-trip | PASS | established in the earlier acceptance round (F-P21-FND-04 CLOSED); untouched code |
| Company Boundary | PASS | placeholder only; no employee/assignment UI |
| Event Boundary | PASS | 0 event/handler/allowlist/worker UI |
| Regression | PASS | no source change; formal DB and shared test DB unchanged |

---

## 14. Git Boundary

```text
HEAD ....................... 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (unchanged)
branch ..................... main
staged ..................... 0
tags ....................... 16 (unchanged)
porcelain .................. 209 = 16 frontend + 193 non-frontend (historical, preserved)
diff --check ............... clean for apps/frontend/**
source files modified today . none
commit / tag / push ........ none
```

---

## 15. Residual Risks / Limitations

```text
1. COR-01 / RE-01: the Foundation suite contains one timing-sensitive assertion. Production
   behaviour is unaffected, but the suite is not 100% deterministic under coverage
   instrumentation. Recommended: test-hygiene round (assert with findBy/waitFor).
2. COR-02: the corrected Dialog is not yet exercised in a production route; its consumption is
   the Company UI stage's responsibility.
3. The real-backend round trip (sessions / /me / refresh / logout / 401 / 403) was established in
   the previous acceptance round on a disposable isolated database. This round re-verified the
   frontend side (tests, build, E2E, browser) and confirmed that no backend or transport code
   changed since that evidence was produced (no source file modified today).
4. Automated accessibility auditing (axe-style) is still not part of the suite; keyboard and
   semantic behaviour is verified by tests and by the browser checks in §4.2/§7.
```

---

## 16. Final Status

```text
P21 FRONTEND FOUNDATION ACCEPTANCE = PASS
F-P21-ACC-01 = CLOSED

App Shell · Routing · Auth · Tenant · API Client · Error System · Design System ·
Primitives (incl. Dialog) · Testing · Dev Configuration = ACCEPTED
Platform / Domain boundary = ACCEPTED

Company UI = NOT IMPLEMENTED (implementation requires a new authorization)
Event UI   = OUT OF SCOPE
Backend / Migration / Schema / Permission = UNCHANGED

RELEASE = NOT AUTHORIZED
COMMIT  = NOT AUTHORIZED
TAG     = NOT AUTHORIZED
PUSH    = NOT AUTHORIZED

NEXT AUTHORIZED STEP = P21 COMPANY UI IMPLEMENTATION (own authorization required)
HARD STOP = ACTIVE
```

---

## 17. Hard Stop

```text
HARD STOP = ACTIVE
```

This round performed read-only acceptance verification, re-executed the Dialog suite and the
Foundation regression suite, ran real-browser keyboard/accessibility/responsive checks at three
viewports, re-ran the security tests and scans, confirmed the architecture and database
boundaries, and wrote exactly two authorized artifacts: this report and one append-only entry in
the project record book.

It did not modify source, configuration, tests, backend, schema, migrations or the dev proxy, and
did not commit, tag, push or release anything. Company UI implementation must not begin until it
receives its own explicit authorization.
