# P21 RELEASE PREPARATION / READINESS REPORT

Decision: `HD-P21-03 — P21 Release Preparation = APPROVED`

Mode: preparation only — no source change, no commit, no tag, no push, no release candidate freeze.

## GATE RESULT

```text
P21 RELEASE PREPARATION = READY

Blocking Findings ............... 0
Release Scope ................... Frozen Candidate (frontend foundation + Company UI V1 + P21 documents)
Historical Dirty Work ........... Preserved (189 non-P21 entries untouched; none in the candidate payload)
Acceptance Evidence ............. Complete (Foundation · Company UI implementation · validation gate · acceptance)
Documentation ................... Complete (9 P21 documents)
Version / Tag ................... Candidate only — NOT frozen, NOT created
Commit / Tag / Push ............. NOT AUTHORIZED

NEXT = P21 RELEASE DECISION (new Human Decision required)
HARD STOP = ACTIVE
```

---

## 1. Objective

Turn the accepted P21 work into a release-ready, auditable, reproducible and reversible candidate:
an exact payload inventory, an explicit boundary against historical dirty work, a consolidated
evidence index, metadata candidates and a documented readiness judgement — without performing any
release action.

## 2. Human Decision and Authorization Boundary

```text
HD-P21-03 = APPROVED
authorized     : release preparation · readiness analysis · candidate payload preparation ·
                 metadata candidates · evidence consolidation · record-book entry
not authorized : any source change · commit · tag · push · GitHub release · production deployment ·
                 P22 · production event activation · freezing the final version or tag name
```

## 3. Baseline (measured in this round, not quoted)

```text
git rev-parse HEAD ............. 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
git branch --show-current ...... main
git log -1 --oneline ........... 08a0485 release: UAP v0.1.17 P18 control plane
git diff --cached .............. 0 (staged = 0)
git tag ........................ 16
git status --porcelain ......... 213 entries = 16 frontend-scope + 197 other
git diff --check ............... clean (4 pre-existing CRLF warnings only)
```

## 4. Release Scope (frozen candidate)

In scope:

```text
1. P21 Frontend Foundation
   apps/frontend/** — platform layer (auth · tenant · api · permissions · feedback · design),
   app shell + routing, core UI primitives, testing foundation, development configuration
2. P21 Company UI V1
   apps/frontend/src/modules/company/** — 5 pages (Overview · Employees · Employee detail ·
   Assignments · Assignment detail) and 7 actions (Employee Create/Edit/Suspend/Terminate ·
   Assignment Create/Edit/End), plus the module route table, API adapter and module styles
3. P21 documentation
   discovery prep · foundation implementation · foundation acceptance (blocked) ·
   foundation acceptance re-entry · foundation correction · Company UI implementation ·
   Company UI validation gate · Company UI acceptance · this readiness report
```

Out of scope (must not be absorbed by the release):

```text
P22 or any future phase · unaccepted functionality · unauthorized repairs ·
historical unfinished work (P15–P20 code and documents) · production event activation ·
worker · other domains · any capability not covered by a Human Decision
```

## 5. Candidate Payload Inventory

```text
frontend files ......... 98 (all files under apps/frontend/** excluding node_modules · dist ·
                            coverage · test-results · playwright-report · .vite)
P21 documents .......... 9 (docs/architecture/P21_*.md)
payload files .......... 107
authoritative list ..... docs/architecture/P21_RELEASE_CANDIDATE_MANIFEST.txt
                          (one line per file: sha256 + path, sorted; generated after this report)
self-hash rule ......... the manifest does not contain itself; its own sha256 is recorded in the
                          record-book entry and can be re-derived at release-decision time
```

Payload composition (by area):

```text
apps/frontend/src/platform/** ........ auth · tenant · api client · permissions · feedback · design tokens
apps/frontend/src/app/** ............. App · ErrorBoundary · routing (routes, boundaries, pages) · shell
apps/frontend/src/components/** ...... 12 primitives + module CSS
apps/frontend/src/modules/company/** . Company UI V1 (20 production files + 6 test files)
apps/frontend/src/test/** ............ test setup + static security scan + Company harness (test-only)
apps/frontend/e2e/** ................. Playwright boot baseline
apps/frontend/{package.json,package-lock.json,tsconfig.json,vite.config.ts,vitest.config.ts,
  playwright.config.ts,index.html,.env.example,.gitignore,README.md}
docs/architecture/P21_*.md ........... 9 documents
```

## 6. Tracked-File Diff (vs HEAD)

```text
apps/frontend/README.md        | 27 +++++++++++++++++++--------
apps/frontend/package.json     | 27 ++++++++++++++++++++++-----
apps/frontend/src/main.tsx     | 39 +++++++++++++++++++--------------------
apps/frontend/vite.config.ts   | 21 +++++++++++++++++++++
4 files changed, 81 insertions(+), 33 deletions(-)
```

All four modified files belong to the release scope (frontend foundation + development proxy
configuration required by Company UI). No other tracked file is modified by P21.

## 7. Historical Dirty Work Boundary (strict proof)

```text
porcelain total ...................... 213
frontend-scope entries ............... 16   → release payload candidates
P21 document entries ................. 9    → release payload candidates (docs)
historical entries ................... 188  → NOT release payload; preserved untouched

historical entry distribution (by top-level path):
  docs/**               148  (P15–P20 architecture documents, handoffs, decision records)
  tests/**               23  (historical test-suites)
  domains/**              7  ·  apps/**  4  ·  migrations_alembic/**  2
  services/**             2  ·  infrastructure/**  1  ·  scripts/**  1

proof of separation:
  * the candidate payload contains only apps/frontend/** and docs/architecture/P21_*.md;
    no historical path appears in the payload list (verifiable line-by-line)
  * no historical file was modified, staged, restored, cleaned or deleted in this round
  * git diff --cached = 0; the release payload remains untracked until a future authorized commit
risk note: the release commit (future round) must stage an explicit allowlist of the payload
  paths only; `git add .` / `git add -A` must not be used
```

## 8. Invariants Re-verified (static, this round)

```text
Company UI pages ................ 5 authorized pages present (Overview · Employees · Employee detail ·
                                  Assignments · Assignment detail) + the module 404 page
Company UI actions .............. 7 action functions present (create/update/suspend/terminate employee ·
                                  create/update/end assignment)
forbidden surfaces .............. 0 (/admin · employee login · event console · worker console · allowlist UI)
single platform API client ...... 1 fetch() in the whole source tree (platform/api/client.ts)
memory-only auth ................ 0 executable storage APIs (the only textual match is the AuthContext
                                  comment that forbids persistence)
Core → Domain ................... 0
frontend → backend packages ..... 0
production event state .......... production_allowlist() returns an empty allowlist (services/consumer/kernel.py);
                                  no backend file is modified by P21, so the accepted P20 state is unchanged
```

## 9. Acceptance Evidence Index

| Stage | Document | Result |
| --- | --- | --- |
| Foundation implementation | `P21_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md` | PASS (88 tests at that time) |
| Foundation acceptance (first pass) | `P21_FRONTEND_FOUNDATION_ACCEPTANCE_REPORT.md` | BLOCKED (Dialog focus containment/restoration) — historical |
| Foundation correction | `P21_FRONTEND_FOUNDATION_CORRECTION_REPORT.md` | PASS (ACC-01 closed) |
| Foundation acceptance re-entry | `P21_FRONTEND_FOUNDATION_ACCEPTANCE_REENTRY_REPORT.md` | PASS |
| Company UI implementation | `P21_COMPANY_UI_IMPLEMENTATION_REPORT.md` | COMPLETE |
| Company UI validation / gate | `P21_COMPANY_UI_VALIDATION_GATE_REPORT.md` | PASS |
| Company UI acceptance | `P21_COMPANY_UI_ACCEPTANCE_REPORT.md` | PASS |

Consolidated test evidence (last full runs, all re-executed within the P21 rounds):

```text
npm run test:run ..... 20 files · 132 tests · 132 passed · 0 failed · 0 skipped
npx vitest --coverage  94.25 % statements · 88.83 % branches · 87.31 % functions
npm run typecheck .... exit 0 (strict, 0 suppressions)
npm run build ........ PASS · js 223.14 kB · Company UI and Dialog present in the bundle
npm run e2e .......... 2 passed (boot + anonymous deep-link; Company journey = manual browser evidence)
real backend ......... isolated database, real FastAPI, real authorization (403/409/422 verified);
                       Company UI journey verified in a real browser with recorded 201/200 responses
```

## 10. Version / Tag Candidates (candidates only — not frozen)

```text
current platform version ....... 0.1.17  (pyproject.toml · config/settings.py · docker-compose.yml)
current frontend package ....... 0.1.0   (apps/frontend/package.json — never aligned to the platform line)

CANDIDATE Release Version ...... 0.1.18
CANDIDATE Release Tag .......... UAP-V0.1.18-P21-COMPANY-UI
CANDIDATE Release Title ........ UAP v0.1.18 — P21 Company UI V1 (Foundation + Company Domain UI)
CANDIDATE scope ................ frontend foundation + Company UI V1 + P21 documents (this payload)
```

```text
explicitly NOT decided here: the final version number, the final tag name, whether the frontend
package version should be aligned to the platform version, and whether the historical 16 tags
remain as-is. All of these require the P21 Release Decision.
observation for that decision: aligning apps/frontend/package.json to the platform version would be
a source change and is therefore out of scope for this preparation round.
```

## 11. Release Notes Draft (candidate)

```text
UAP v0.1.18 — P21 Company UI V1

Platform UI foundation
  · React + Vite + TypeScript console shell, routing, auth context, tenant context,
    typed API client, error system, design tokens, 12 UI primitives, Vitest/RTL/Playwright baseline
  · memory-only session token; single typed API client; backend-authoritative authorization

Company Domain UI V1 (first business domain UI)
  · pages: Overview · Employees · Employee detail · Assignments · Assignment detail
  · actions: employee Create / Edit / Suspend / Terminate; assignment Create / Edit / End
  · real Company API integration, explicit confirmation for irreversible actions,
    loading / empty / error states, validated forms, responsive layout, keyboard-accessible dialogs
  · tenant isolation via the URL-authoritative tenant guard; blocked by the backend when unauthorized

Not included
  · Delete / Admin surfaces, employee login, event or worker UI, production event activation,
    new backend endpoints, schema or migration changes
```

## 12. Reproducibility and Rollback

```text
reproducible build .... npm ci (lockfile v3) → npm run typecheck → npm run test:run → npm run build
real verification ..... isolated database recipe (create DB → alembic head 0020 as uap_migrator →
                        materialize privileges → seed identities/tenants/space → uvicorn) is captured
                        in the Company UI acceptance report
rollback .............. the release payload is not committed and introduces no migration, no schema
                        change and no dependency outside apps/frontend/package*.json; discarding the
                        working-tree payload returns the repository to HEAD 08a0485b exactly
historical safety ..... historical dirty work is never staged, so a rollback cannot lose it
```

## 13. Findings (re-classified; history preserved)

| Finding | Classification | Note |
| --- | --- | --- |
| `F-P21-RE-01` tenant mirrored after paint | CLOSED | module tenant guard; zero calls + no stale render; verified in gate and acceptance |
| `F-P21-COR-01` timing-sensitive AppRouter assertion | NON-BLOCKING / OBSERVATION | no recurrence in any executed run during the P21 rounds |
| `F-P21-COR-02` Dialog not consumed | CLOSED / RESOLVED | Dialog present in the production bundle and consumed by Company dialogs |
| `F-P21-COR-03` nested dialogs | N/A | no such architecture exists |
| `ACC-02` dev proxy namespace | CLOSED | `/company/**` + `/tenants/{id}/spaces` reach the backend; SPA deep links preserved |
| `ACC-03` Table overflow | CLOSED (page-level) | 0 px overflow at 390/834/1440; shared Table primitive not modified |
| `ACC-04` / `ACC-05` Foundation coverage gaps | NON-BLOCKING / OBSERVATION | unrelated to Company UI; unchanged by P21 |
| `ACC-06+` (Drawer, /ready artifact, …) | OUT OF SCOPE / OBSERVATION | not part of the P21 release scope |
| `OBS-1` no device-enrolment UX | NON-BLOCKING / OBSERVATION | authenticated acceptance used a real backend session |
| `OBS-2` page-size-bound counts | NON-BLOCKING / OBSERVATION | UI never invents a total |
| `OBS-3` first-page name enrichment | NON-BLOCKING / OBSERVATION | ids rendered as fallback |
| `OBS-4` active-space-only picker | NON-BLOCKING / OBSERVATION | explicit hint; backend remains final |

No historical finding was deleted or rewritten. No new blocking finding was identified in this round.

## 14. Readiness Checklist

```text
[x] git baseline re-measured (HEAD · branch · staged · tags · porcelain)
[x] release scope defined and frozen as a candidate
[x] payload inventory generated with per-file SHA-256 (manifest file)
[x] tracked-file diff enumerated (4 files, all in scope)
[x] historical dirty work boundary proven (188 entries preserved, none in payload)
[x] Company UI invariants re-verified (5 pages · 7 actions · forbidden 0 · 1 client · memory-only auth)
[x] architecture invariants re-verified (Core → Domain 0 · frontend → backend 0)
[x] production event state re-verified (allowlist empty; no backend change)
[x] acceptance evidence index consolidated (7 stage documents + test evidence)
[x] documentation set complete (9 P21 documents)
[x] version / tag / title candidates proposed (not frozen)
[x] release notes draft prepared
[x] reproducibility and rollback described
[x] findings re-classified; blocking findings = 0
[ ] release decision, version freeze, commit, tag, push — NOT AUTHORIZED in this round
```

## 15. Next Authorized Step

```text
P21 RELEASE DECISION
  — requires a NEW Human Decision
  — expected decisions: final version, final tag name, explicit payload allowlist for staging,
    release notes approval, and whether any metadata (e.g. the frontend package version) changes
  — this round performs none of those actions
```

## 16. Hard Stop

```text
HARD STOP = ACTIVE
```

This round was read-only preparation: it measured the repository state, classified the payload and
the historical dirty work, re-verified the P21 invariants and architecture boundaries, consolidated
evidence, generated a hashed candidate manifest, and wrote exactly three authorized artifacts
(this report, the candidate manifest, and one append-only record-book entry). No source, test,
configuration, backend, schema, migration, permission or database change was made, and no version
was frozen, no commit/tag/push/release was created, and P22 was not started.
