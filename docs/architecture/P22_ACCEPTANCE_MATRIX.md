# P22 ACCEPTANCE MATRIX (DESIGN — AWAITS HUMAN RATIFICATION)

Source: `P22_PREP_REPORT.md` · `P22_SCOPE_CONTRACT.md` · Decision basis: `HD-P22-01`

Status: **DESIGN ONLY** — defines what acceptance will require *before* any implementation is authorized.
P22 implementation has not started and is not authorized.

## 0. Classification Vocabulary

```text
Blocking       failure stops the phase; no commit / tag / push / release may proceed
Non-Blocking   must be recorded and reported; does not stop the phase by itself
Observation    informational; tracked for future phases
Deferred       intentionally postponed with a named unblocking decision
Out of Scope   explicitly excluded from the phase
N/A            not applicable to this phase, with a stated reason
```

## 1. Functional Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| F-1 | A real user can complete device enrolment in the console and reach an authenticated session | browser evidence: challenge → enrolment → session; real HTTP statuses | Blocking |
| F-2 | Device management actions (revoke / lost) behave per the released contract | real API responses + UI state; terminal-state handling | Blocking |
| F-3 | Session access paths behave correctly: device-required, expired session, logout, refresh | recorded statuses + UI transitions | Blocking |
| F-4 | The released Company UI remains fully usable after the changes (5 pages / 7 actions) | regression run of the Company suite + browser smoke | Blocking |
| F-5 | Bounded usability items (tenant switcher, frozen filters, state polish) behave as specified | per-item evidence | Non-Blocking |
| F-6 | Domain Module Contract v1 is complete and reviewable | document exists, derived from the Company precedent | Blocking |

## 2. Authorization Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| A-1 | Every new action is authorized by the backend; the console performs no allow/deny decision | source scan + real 403 for an unauthorized actor | Blocking |
| A-2 | Device enrolment grants no domain permission and creates no tenant bypass | authorization analysis + real denial checks | Blocking |
| A-3 | No new role, permission or ACL subject type is introduced without a decision | diff review + PDL check | Blocking |
| A-4 | Tenant / space context never originates from client input | request trace + source scan | Blocking |

## 3. Tenant Isolation Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| T-1 | URL tenant remains the single authority; unresolved context yields zero requests and no stale render | guard tests + browser measurement | Blocking |
| T-2 | Tenant switching retargets every request; previous-tenant data never renders | browser scenario | Blocking |
| T-3 | A tenant the actor cannot reach is refused by the backend, not by the UI | real 403 evidence | Blocking |

## 4. Security Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| S-1 | Token remains memory-only; no browser storage API is used | existing security scanner + source scan | Blocking |
| S-2 | No secret, credential, DSN or internal error text reaches source, bundle or UI | scans + error-surface review | Blocking |
| S-3 | Enrolment secrets (challenge secret / device credentials) are handled per the released contract and never logged | code review + log inspection | Blocking |
| S-4 | No unsafe HTML / dynamic code execution is introduced | scan | Blocking |

## 5. API Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| P-1 | No endpoint is added, changed or removed unless separately authorized | route inventory diff | Blocking |
| P-2 | Requests use the released contracts (method, path, body, DTO) exactly | real request trace | Blocking |
| P-3 | Error taxonomy stays the frozen one (401/403/404/409/422/5xx/network) | per-class UI evidence | Blocking |

## 6. Frontend Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| U-1 | Platform boundaries hold: no second auth store, no second API client, module-owned routes only | import graph + source scan | Blocking |
| U-2 | Accessibility baseline holds (keyboard, focus visible, dialog semantics, labels, pending states) | browser measurements | Blocking |
| U-3 | Responsive baseline holds at 390 / 834 / 1440 (0 px overflow; dialogs fit) | browser measurements | Blocking |
| U-4 | Design tokens + CSS Modules remain the only styling system | source scan | Non-Blocking |

## 7. Database Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| D-1 | No schema change, no DDL/DML/seed in the phase | DB prestate/poststate + diff review | Blocking |
| D-2 | Formal database untouched; shared test database at its frozen baseline | read-only state capture | Blocking |
| D-3 | Any temporary verification database is isolated, recorded and removed | environment log | Blocking |

## 8. Migration Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| M-1 | Alembic head unchanged (0020_p20_company_authorization); no new revision | migration inventory | Blocking |
| M-2 | No migration is executed against the formal database | execution log | Blocking |

## 9. Event Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| E-1 | Production allowlist remains EMPTY; no producer, handler or worker is registered | code scan + allowlist inspection | Blocking |
| E-2 | No implicit event activation through another feature | review of the phase's diff | Blocking |
| E-3 | The accepted-but-inactive event state remains documented | PDL / report reference | Non-Blocking |

## 10. Regression Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| R-1 | Full frontend suite green (file/test/pass/fail/skip counts recorded) | executed command output | Blocking |
| R-2 | Typecheck, build and E2E re-executed | executed command output | Blocking |
| R-3 | Backend suites relevant to touched contracts remain green | allowlisted test results | Blocking |
| R-4 | P21 acceptance/release evidence remains valid (no silent scope change) | diff review | Blocking |

## 11. Git Integrity Acceptance

| # | Criterion | Evidence required | Class if failed |
| --- | --- | --- | --- |
| G-1 | Historical dirty work preserved (never cleaned, staged or rewritten) | porcelain comparison | Blocking |
| G-2 | No commit / tag / push without explicit authorization | git log + tag list | Blocking |
| G-3 | Release tag `UAP-V0.1.18-P21-COMPANY-UI` and its commit remain untouched | tag verification | Blocking |
| G-4 | Any temporary evidence file is either committed by an authorized decision or reported | file inventory | Non-Blocking |

## 12. Matrix Maintenance Rules

```text
each implemented item must be mapped to the criteria above before implementation starts
criteria may be added by a new Human Decision, never removed implicitly
acceptance evidence must be reproducible: exact commands, exact counts, exact hashes, exact viewports
no phase may declare PASS while a Blocking criterion is unresolved
```
