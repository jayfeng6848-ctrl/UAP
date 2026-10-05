# P21 FRONTEND FOUNDATION CORRECTION REPORT

Gate: `P21 FRONTEND FOUNDATION CORRECTION` (single blocker: `F-P21-ACC-01`)

Scope: `apps/frontend/src/components/Dialog.tsx` · `apps/frontend/src/components/Dialog.test.tsx`

## Verdict

```text
P21 FRONTEND FOUNDATION CORRECTION = PASS
READY FOR ACCEPTANCE

F-P21-ACC-01 = FIXED (implementation + unit tests + real-browser verification)

Dialog focus containment (Tab / Shift+Tab) ...... FIXED
Dialog focus restoration (Escape / Close) ....... FIXED
Trigger removed while open ...................... SAFE (no exception, no body hand-off on
                                                  the normal path)
Regression (typecheck · tests · build · E2E) .... PASS
Security regression ............................. PASS
Backend / migration / ACC-02 / ACC-03 / Drawer .. NOT TOUCHED

Commit = NO · Tag = NO · Push = NO · HARD STOP = ACTIVE
```

Next required stage (not executed here): `P21 FRONTEND FOUNDATION ACCEPTANCE RE-ENTRY`.

---

## 1. Executive Summary

The one blocking acceptance finding was repaired with a minimal increment to the existing
Dialog primitive — no redesign, no new abstraction, no new dependency.

```text
Dialog.tsx ....... 60 → 159 lines (focus containment + focus restoration + edge cases)
Dialog.test.tsx .. 84 → 309 lines (17 tests; was 6)
full suite ....... 88 → 99 tests, 99 passed / 0 failed (14 files)
Dialog coverage .. 96.55% stmts · 89.47% branch · 100% funcs
overall coverage . 89.82% stmts · 88.5% branch · 84% funcs
typecheck ........ PASS (0 @ts-ignore / @ts-nocheck / eslint-disable)
build ............ PASS (81 modules; bundle byte-identical — see §10)
E2E .............. 2/2 passed (boot · anonymous deep link)
real browser ..... Tab/Shift+Tab containment + Escape/Close restoration verified at
                   1440 px and 390 px, 0 console/page errors
```

Everything out of scope (ACC-02 dev proxy, ACC-03 table overflow, Drawer, coverage gaps,
`/ready`, npm postinstall, Company/Event UI) was left untouched.

---

## 2. Authority and Scope

```text
Authorized to modify : apps/frontend/src/components/Dialog.tsx
                       apps/frontend/src/components/Dialog.test.tsx
Authorized to write  : docs/architecture/P21_FRONTEND_FOUNDATION_CORRECTION_REPORT.md
Explicitly forbidden : ACC-02 (proxy) · ACC-03 (Table) · Drawer · AuthContext/feedback
                       coverage · /ready · authenticated browser flow · npm postinstall ·
                       Company UI · Event UI · Worker UI · backend · migration · deployment
```

Verified by mtime: only these two source files were written in this round (12:31:27 and
12:33:07); every other frontend file is older.

---

## 3. Baseline

```text
git rev-parse HEAD ....... 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
git diff --cached ........ 0 (nothing staged)
git tag .................. 16 (unchanged)
git status --porcelain ... 208 = 16 under apps/frontend/** + 192 non-frontend (historical)
git diff --check ......... clean for apps/frontend/**
```

Pre-existing dirty entries (P15–P20 plus the earlier P21 documents) were preserved exactly:
no clean, no reset, no restore, no `git add .`, no line-ending normalization.

---

## 4. Root Cause (F-P21-ACC-01)

The Dialog primitive implemented semantics, Escape and initial focus but had **no keyboard
focus management at all**:

```text
before (60 lines)
  effect: surfaceRef.current?.focus()            → initial focus OK
          document keydown → Escape → onClose()  → Escape OK
  missing: Tab / Shift+Tab interception          → focus could leave the dialog
  missing: previously-focused-element capture    → focus fell to <body> on close
```

Acceptance measured the consequence in a real browser: `Tab` from the last control moved
focus to a control behind the backdrop, and closing left `document.activeElement === body`.

---

## 5. Fix Design (minimal increment)

One effect owns focus for the whole open/close lifecycle; there is no second focus path,
so a close cannot restore focus twice.

```text
on open
  1. remember document.activeElement (only a real HTMLElement of this document;
     never <body>/<html>, which is what produced the ACC-01 defect)
  2. focus the first usable control, else the dialog surface (tabIndex=-1)
     → the "no focusable element" case keeps focus on the dialog, never on the page

while open (single document-level keydown listener, capture phase)
  Escape     → preventDefault + onClose (latest handler through a ref)
  Tab        → focus on the surface or outside  → first control
               focus on the last control        → first control (cycle)
  Shift+Tab  → mirror of the above (first → last)
  no control → keep focus on the dialog surface (no throw, no page focus)

on close (effect cleanup, exactly once per close)
  restore focus to the remembered trigger only when it is still isConnected and usable;
  otherwise do nothing (no exception, no wrong element)
```

Design constraints honoured:

```text
latest-value ref for onClose  → the focus effect depends on [open] only, so an inline
                                onClose prop cannot re-run the effect and overwrite the
                                remembered trigger
usability filter              → disabled · hidden · [inert] ancestor · aria-hidden ancestor ·
                                display:none / visibility:hidden · tabindex < 0
no global trap                → the listener only acts on Tab/Escape and only ever moves
                                focus inside the open dialog; the page is never inert
no nested-dialog system       → not designed, not claimed; a closed dialog renders nothing
                                and therefore cannot compete for focus
```

---

## 6. Implementation Diff Summary

```text
Dialog.tsx
  + FOCUSABLE_SELECTOR (a[href] · button · input · select · textarea · [tabindex>=0])
  + isUsable(element)             usability filter
  + focusableElements(root)       candidate list for one dialog
  + onCloseRef                    latest-handler ref (stable effect dependency)
  ~ focus effect                  capture trigger → initial focus → Tab/Escape handling
                                  → single restoration in cleanup
  (unchanged: props, children/footer API, role/aria wiring, module CSS, CSS classes)

Dialog.test.tsx
  ~ semantics suite               kept, replacing only the tests superseded by new behaviour
  + initial focus                 first control focused · surface focused when empty
  + containment                   6 tests (forward, backward, repeated tabbing, surface
                                  start, empty dialog, closed-dialog isolation)
  + usability filter              1 test (disabled / hidden / aria-hidden / display:none
                                  controls skipped by the cycle)
  + restoration                   3 tests (close control, Escape, trigger removed)
```

No change to `Dialog.module.css`, `components/index.ts`, `platform/**`, `app/**`,
`vite.config.ts`, `package.json` or any other file.

---

## 7. Tests

Requested matrix (Correction §20–§23) and where it is covered:

| Required check | Test |
| --- | --- |
| Test 1 open → focus inside dialog | `Dialog initial focus › focuses the first control inside the dialog on open` |
| Test 2 last → Tab → first | `focus containment › cycles forward from the last control to the first` |
| Test 3 first → Shift+Tab → last | `focus containment › cycles backward from the first control to the last` |
| Test 4 Tab repeatedly never leaves | `focus containment › never leaves the dialog while tabbing repeatedly` (8 forward + 8 backward) |
| Test 5 trigger → open → close → trigger | `focus restoration › returns focus to the trigger when closed through its close control` |
| Test 6 trigger → Escape → trigger | `focus restoration › returns focus to the trigger on Escape` |
| Test 7 trigger removed → close → no exception | `focus restoration › does not touch focus when the trigger is gone` |
| §22 no focus leak | covered by Tests 2/3/4 (the harness keeps an `outside after` control behind the dialog) |
| §23 body-focus regression | both restoration tests assert `document.activeElement` is **not** `document.body` before asserting the trigger |
| §24 multiple dialogs | `focus containment › does not let a closed dialog interfere with the open one` (N/A beyond this: no nested-dialog system exists) |
| §11 initial focus kept | `focuses the first control…` + `focuses the dialog surface when the dialog holds no focusable control` |
| §9 usability filter | `cycles only through usable controls (skips disabled, hidden and aria-hidden)` |

```text
src/components/Dialog.test.tsx ....... 17 tests, 17 passed
full suite (npm run test:run) ........ 14 files, 99 tests, 99 passed, 0 failed, 0 skipped
```

jsdom note: the containment tests drive real user-event keyboard input; user-event only
performs its own Tab movement when the event is not prevented, so the assertions observe the
component's own focus decisions.

---

## 8. Coverage

```text
npm run test:coverage  →  All files   89.82% stmts · 88.5% branch · 84% funcs · 89.82% lines
                          Dialog.tsx  96.55% stmts · 89.47% branch · 100% funcs
```

Dialog uncovered statements: lines 27–28 (the `disabled` filter arm) and 99–100 (the
defensive "surface gone" guard). Both are defensive paths; a disabled control is already
excluded by the selector, and the guard cannot fire while the dialog is open. No test was
added purely to move the number, per Correction §27.

---

## 9. Typecheck · Build · E2E

```text
npm run typecheck  → PASS (strict; 0 @ts-ignore / @ts-nocheck / eslint-disable in src/** and e2e/**)
npm run build      → PASS · 81 modules · dist/index.html 0.40 kB · css 3.67 kB · js 196.49 kB
npm run e2e        → 2 passed (boot · anonymous deep link), 3.4s
```

---

## 10. Production Bundle Note

```text
dist/assets/index-CAUR2bKG.js (196.49 kB) and index-yrJpwHy2.css are byte-identical to the
pre-correction build.
Reason: nothing in the application route graph imports Dialog yet, so Rollup tree-shakes the
primitive out of the shipped bundle — verified by scanning dist for Dialog markers
(`uap-dialog-backdrop`, `role="dialog"`, `aria-modal`): 0 hits.
Consequence: this correction cannot change current production runtime behaviour; it changes
the primitive that the Company UI stage will consume.
```

---

## 11. Real Browser Verification (not jsdom-only)

Rendered the corrected component in a real Chromium page loaded from the dev-server module
graph and drove it with real keyboard input.

| Check | Desktop 1440×900 | Mobile 390×844 |
| --- | --- | --- |
| initial focus | first control (`inner-close`) | first control (`inner-close`) |
| Tab from last control | → first control | → first control |
| Shift+Tab from first control | → last control | → last control |
| 6× Tab trail | `close → cancel → confirm → close → cancel → confirm` | same |
| controls reached outside the dialog | 0 | 0 |
| Escape | focus returned to `trigger` | focus returned to `trigger` |
| Close control | focus returned to `trigger` | focus returned to `trigger` |
| trigger removed while open | no exception, no page error | no exception, no page error |
| console / page errors | 0 | 0 |

Keyboard-only interaction is what was exercised (no mouse ever moved focus inside the
dialog), and both widths were checked because the backdrop/dialog CSS is width-dependent.

---

## 12. Strict React Behaviour

```text
StrictMode double-invocation of the focus effect is safe:
  mount 1   → remember the real trigger → focus the surface
  cleanup 1 → restore focus to the remembered trigger
  mount 2   → remember the now-focused element (the same trigger) → focus the surface again
  net state = dialog focused, trigger remembered correctly
StrictMode was NOT disabled anywhere; no dev-only branch was added.
```

---

## 13. Security Regression

```text
executable source scan (src/**, tests excluded)
  localStorage · sessionStorage · document.cookie= · eval( · new Function( ·
  dangerouslySetInnerHTML · innerHTML=        → 0 findings
  (the only textual match is the pre-existing AuthContext comment that forbids storage)
secret scan (src + Dialog files)              → 0 production findings (matches are test
                                                fixtures: an ErrorBoundary error string and
                                                the security-test regex)
dist scan (API target, DSN, key patterns)     → 0 findings
console logging introduced by the fix         → none (no console.* in Dialog.tsx)
focus-driven code injection / unsafe HTML     → none (no HTML API, no dynamic evaluation)
```

---

## 14. Regression and Boundaries

```text
files changed this round ................ Dialog.tsx · Dialog.test.tsx (mtime-verified)
Company UI .............................. still NOT_IMPLEMENTED (placeholder unchanged)
Event / Worker UI ....................... untouched
ACC-02 (dev proxy /company/**) .......... NOT FIXED (kept as a Company-UI precondition)
ACC-03 (Table overflow) ................. NOT FIXED (kept for the Data-View work)
Drawer · AuthContext/feedback coverage · /ready · authenticated browser flow · npm
postinstall ............................. NOT TOUCHED
backend / API / migration / authorization  no diff introduced (pre-existing dirty files only)
git diff --cached = 0 · HEAD unchanged · tags unchanged
```

---

## 15. Findings

```text
F-P21-ACC-01   CLOSED (this round)
  Focus containment and focus restoration implemented and verified in unit tests and in a
  real browser at two viewports; the degraded cases (no focusable control, trigger removed)
  are safe.

F-P21-COR-01   OBSERVATION (new, out of scope — not fixed here)
  Subject : src/app/routing/AppRouter.test.tsx contains a timing-sensitive async test.
  Evidence: during 5 coverage runs one run failed in AppRouter.test.tsx; the same file passes
            3/3 in isolation and 3/3 in subsequent full-coverage runs (99/99 each).
  Assessment: latent test-hygiene issue (default async timeout under a heavier parallel
            suite), not a Dialog regression — the file shares no code with Dialog.
  Suggested fix (future authorized round): raise the async timeout / await the auth transition.

F-P21-COR-02   OBSERVATION
  Subject : the Dialog primitive is still unused by any application route, so the corrected
            code is tree-shaken out of the production bundle (§10). Consumption belongs to
            the Company UI stage.

F-P21-COR-03   NOT APPLICABLE
  Subject : nested / multiple simultaneous dialogs. The current architecture renders one
            dialog and has no nesting system; per Correction §8/§24 nothing was designed or
            extended, and the closed-dialog isolation test documents the boundary.
```

No blocker from Correction §37 (architecture cannot support a trap / trigger relationship
cannot be recovered / React lifecycle prevents restoration / browser differs from test
assumptions) materialized.

---

## 16. Success Criteria Checklist (Correction §39)

```text
[x] Tab trap works                     unit (3 tests) + real browser (desktop + mobile)
[x] Shift+Tab trap works               unit (3 tests) + real browser (desktop + mobile)
[x] Escape restores trigger            unit + real browser
[x] Close restores trigger             unit + real browser
[x] removed trigger is safe            unit + real browser (no exception, no page error)
[x] no body focus on normal close      asserted in both restoration tests; browser confirms
                                       focus returns to the trigger
[x] no regression                      full suite 99/99 · typecheck PASS · build PASS · E2E 2/2
[x] typecheck pass                     PASS (strict, no suppressions)
[x] tests pass                         14 files / 99 tests / 0 failed / 0 skipped
[x] build pass                         PASS
[x] E2E pass                           2 passed
[x] no security regression             0 executable findings, 0 secrets in src/dist
[x] no backend change                  no diff this round; historical dirty files untouched
```

---

## 17. Final Status

```text
P21 FRONTEND FOUNDATION CORRECTION = PASS

F-P21-ACC-01 .................... FIXED
Dialog focus containment ........ IMPLEMENTED + TESTED + BROWSER-VERIFIED
Dialog focus restoration ........ IMPLEMENTED + TESTED + BROWSER-VERIFIED
Files changed ................... apps/frontend/src/components/Dialog.tsx
                                  apps/frontend/src/components/Dialog.test.tsx
Report .......................... docs/architecture/P21_FRONTEND_FOUNDATION_CORRECTION_REPORT.md

Tests: 99 passed / 0 failed (Dialog file: 17 passed)
Typecheck: PASS · Build: PASS · E2E: PASS · Security: PASS
Backend / Migration / Company UI / Event UI: UNCHANGED

HEAD ............................ 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (unchanged)
staged .......................... 0
Commit = NO · Tag = NO · Push = NO

CORRECTION COMPLETE · READY FOR RE-ACCEPTANCE
HARD STOP = ACTIVE
```

---

## 18. Hard Stop

```text
HARD STOP = ACTIVE
```

This round fixed exactly one blocker (`F-P21-ACC-01`) inside the two authorized files,
verified it with unit tests, a real browser at two viewports and a full regression of
typecheck / tests / build / E2E / security, and wrote exactly one authorized document
(this report).

It did **not** execute the Foundation Acceptance itself, did not implement Company UI or
Event UI, did not touch the backend, migrations, the database, configuration or the dev
proxy, and did not commit, tag or push.

The only authorized next step:

```text
P21 FRONTEND FOUNDATION ACCEPTANCE RE-ENTRY
```
