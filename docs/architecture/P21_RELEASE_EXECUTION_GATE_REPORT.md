# P21 RELEASE EXECUTION GATE REPORT

Decision: `HD-P21-04 — P21 Release = AUTHORIZED` (version 0.1.18 · tag `UAP-V0.1.18-P21-COMPANY-UI` ·
frontend package version alignment · commit · tag · push authorized)

## GATE RESULT

```text
P21 RELEASE EXECUTION = LOCAL RELEASE COMPLETE (Commit PASS + Tag PASS)
PUSH = BLOCKED — environment egress to github.com is unavailable (no remote mutation occurred)

Version ................ 0.1.18
Tag .................... UAP-V0.1.18-P21-COMPANY-UI (annotated, points to the release commit)
Commit ................. 7ff9ebc204716a2c1cd36a927e361a7d27e41df2 (verified)
Tag .................... ea66fbfe226fd9fdb63656b55d94b006c2c0681b → 7ff9ebc2… (verified)
Push ................... NOT COMPLETED (github.com:443 unreachable; npm registry reachable)

Blocking Findings ...... 0
Unexpected Release Paths = 0
Historical Dirty Work .. Preserved (35 modified filed + untracked set untouched, none staged)
Production Event ....... INACTIVE (production_allowlist() = EMPTY; backend unchanged)
P22 .................... NOT STARTED
```

Per HD-P21-04 §16 the release success criteria include "Push = completed and verified"; that criterion is
**not met**, so this report does not claim a complete release. It records exactly what was executed,
verified and blocked, and stops.

---

## 1. Pre-Commit Release Gate (all measured in this round)

```text
HEAD baseline .......... 08a0485babf0560bc8b7d306c31361b1c1d8bdb5 (expected pre-release state)  ✅
branch ................. main                                                                    ✅
staged before staging .. 0                                                                       ✅
historical dirty work .. unchanged (no clean / reset / restore / stash / bulk add)               ✅
package version ........ apps/frontend/package.json = 0.1.18 (after the authorized metadata change) ✅
manifest ............... 107 rows read from docs/architecture/P21_RELEASE_CANDIDATE_MANIFEST.txt  ✅
  file presence ........ 107/107 payload paths exist                                             ✅
  hash verification .... 106/107 match the manifest; exactly 1 expected delta                     ✅
                         (apps/frontend/package.json — the authorized Release Metadata Change)
diff --check ........... PASS (only pre-existing CRLF warnings)                                  ✅
regression ............. npm ci exit 0 · typecheck exit 0 · 132/132 tests · build PASS           ✅
unexpected changes ..... 0                                                                       ✅
```

## 2. Release Metadata Change (version-only proof)

```text
file ................... apps/frontend/package.json
change ................. "version": "0.1.0" → "version": "0.1.18"

version-only proof (content-level):
  * candidate state hash (from the frozen manifest) .......... 5db9d116829d26cc44407c606f206d1aee0a1c28451b06ec8b65dbc5a6ea07b8
  * current file hash ....................................... c18b97457be9bc78744efe45641690b20a6b957a21c776a3e6ceee71d2467559
  * reconstructing the candidate by reverting ONLY the version string reproduced the manifest hash
    exactly (5db9d116…), therefore the file delta versus the release candidate is version-only
  * dependency / script / tooling sections: unchanged (no other semantic change)
  * apps/frontend/package-lock.json: hash unchanged (637b916f…) — the lockfile was intentionally
    left untouched (see §9 OBS-RELEASE-01)
```

## 3. Regression After the Metadata Change

```text
npm ci --no-fund --no-audit .... exit 0 (lockfile coherent; 230 packages)
npm run typecheck .............. exit 0 (strict, 0 suppressions)
npm run test:run ............... 20 files · 132 tests · 132 passed · 0 failed · 0 skipped
npm run build .................. PASS · 81 modules · js 223.14 kB (Company UI + Dialog present)
git diff --check ............... PASS
release scope verification ..... PASS (see §4)
```

## 4. Staging (explicit allowlist only)

```text
mechanism ............... git add --pathspec-from-file=<generated from the frozen manifest>
                          (no `git add .` / `-A` / `-u`; no glob; no bulk staging)
pathspec entries ........ 108 = 107 manifest paths + the manifest file itself
                          (the manifest cannot list itself under the self-hash rule; it is a P21
                           release document and therefore part of the frozen release scope)
staged changed paths .... 107
  apps/frontend/index.html was NOT staged because it is byte-identical to HEAD (already committed);
  its manifest hash matched, so the payload is complete (108/108 paths present in the resulting tree)

scope proof:
  staged paths ∩ historical dirty paths ........ 0
  staged paths ⊆ frozen release scope .......... true (0 non-payload paths)
  unexpected staged paths ...................... 0
  missing required release paths ............... 0
staged shortstat ........ 107 files changed, 15813 insertions(+), 34 deletions(-)
```

## 5. Release Commit

```text
subject ................ release: UAP v0.1.18 — P21 Company UI V1
commit SHA ............. 7ff9ebc204716a2c1cd36a927e361a7d27e41df2
parent SHA ............. 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
commit tree SHA ........ 7d2c7ef6e3d3f97c0450cfba107cf63f04aea814
staged path count ...... 107
commit path count ...... 107
historical files in the commit ...... 0
non-payload files in the commit ..... 0
staged after commit ................. 0
```

## 6. Release Tag

```text
tag .................... UAP-V0.1.18-P21-COMPANY-UI
type ................... annotated (git cat-file -t → tag)
tag object SHA ......... ea66fbfe226fd9fdb63656b55d94b006c2c0681b
tag target commit ...... 7ff9ebc204716a2c1cd36a927e361a7d27e41df2  (exactly the release commit)
tag subject ............ UAP v0.1.18 — P21 Company UI V1
repository tag count ... 17 (16 historical tags untouched; none moved or deleted)
```

## 7. Push Attempt (authorized, not completed)

```text
command ................ git push origin main UAP-V0.1.18-P21-COMPANY-UI
                          (explicit refspec — no other branch and no other tag was pushed)
result ................. FAILED
error .................. fatal: unable to access 'https://github.com/jayfeng6848-ctrl/UAP.git/':
                          Recv failure: Connection was reset

environment diagnosis (read-only):
  github.com:443 ............ TCP connect FAILED ("Could not connect to server", 21 s timeout)
  registry.npmjs.org:443 .... reachable (package installs worked earlier in this round)
  proxy environment ......... none configured
  credentials ............... git-credential-manager is configured; the failure is network, not auth
remote state ........... NOT re-measured (no connectivity); the last recorded remote baseline in the
                          project record is origin/main = dc44c9939d7708b68e5b461a7ccb6684588d1106
                          and it remains unverified in this round
```

No remote object was created, moved or deleted — the push never reached the server.

## 8. Release Notes (authoritative text for the eventual GitHub release)

```text
UAP v0.1.18 — P21 Company UI V1

Platform UI foundation
  · React + Vite + TypeScript console shell, routing, auth context, tenant context, typed API client,
    error system, design tokens, 12 UI primitives, Vitest + RTL + Playwright testing baseline
  · memory-only session token; one typed API client for the whole console; backend-authoritative
    authorization (no frontend ACL engine)

Company Domain UI V1 — the first business-domain UI
  · 5 pages: Overview · Employees · Employee detail · Assignments · Assignment detail
  · 7 actions: employee Create / Edit / Suspend / Terminate; assignment Create / Edit / End
  · real Company API integration (frozen 11-endpoint contract, no backend change)
  · tenant isolation: the URL is the tenant authority; a tenant-context guard issues no request and
    renders no data while the context is unresolved
  · real authorization: denials come from the backend (403) and are rendered as no-access
  · explicit confirmation for irreversible actions, loading / empty / error states, validated forms
  · responsive validation at 390 / 834 / 1440 px (0 horizontal overflow) and keyboard-accessible
    dialogs (focus containment, Escape, focus restoration)
  · security validation: no browser token storage, no secret in source or bundle, no unsafe HTML

Architecture guarantees
  · Core → Domain = 0 · frontend → backend package imports = 0
  · production event pipeline remains INACTIVE (production_allowlist() = EMPTY)

Evidence disclosure
  · Automated E2E: 2 Playwright tests (application boot + anonymous deep-link fallback)
  · The complete Company business journey was verified as MANUAL BROWSER EVIDENCE (real backend,
    real session, real browser) — it is NOT a Playwright/Cypress suite

Not included in this release
  · no production event activation, no worker, no P22 work, no other domain, no Delete/Admin surface,
    no employee login, no token API, no new backend endpoint, no schema or migration change
```

## 9. Findings and Observations

```text
historical findings (unchanged, cited per the accepted state):
  F-P21-RE-01 = CLOSED · ACC-02 = CLOSED · ACC-03 = CLOSED (page-level) ·
  F-P21-COR-02 = CLOSED / RESOLVED · F-P21-COR-01 = NON-BLOCKING / OBSERVATION ·
  F-P21-COR-03 = N/A · ACC-04 / ACC-05 = NON-BLOCKING · ACC-06+ = OUT OF SCOPE / OBSERVATION ·
  OBS-1..4 = NON-BLOCKING / OBSERVATION

new observation from this round (non-blocking):
  OBS-RELEASE-01  apps/frontend/package-lock.json keeps its root "version": "0.1.0" because the
                  authorization for this round covered only apps/frontend/package.json.
                  Impact: cosmetic (npm ci succeeds; the dependency graph, integrity hashes and
                  reproducible install are unaffected — verified by npm ci exit 0 in this round).
                  Suggested handling: align the lockfile root version in a future authorized change.

blocking findings = 0 · no other anomaly was identified during release execution
```

## 10. Success Criteria Matrix (HD-P21-04 §16)

| Criterion | Status | Evidence |
| --- | --- | --- |
| Version = 0.1.18 | PASS | `git show HEAD:apps/frontend/package.json` → 0.1.18; platform sources remain 0.1.17 (unchanged) |
| Tag = UAP-V0.1.18-P21-COMPANY-UI | PASS | annotated tag object `ea66fbfe…` → commit `7ff9ebc2…` |
| Commit created and verified | PASS | `7ff9ebc2…`, parent `08a0485b…`, tree `7d2c7ef6…`, 107 paths, 0 historical |
| Tag created and verified | PASS | `git cat-file -t` → tag; target = release commit |
| Push completed and verified | **NOT MET** | github.com:443 unreachable from this environment; no remote mutation |
| Blocking Findings = 0 | PASS | §9 |
| Unexpected Release Paths = 0 | PASS | §4 staging scope proof |
| Historical Dirty Work = Preserved | PASS | 0 historical paths staged; 35 modified tracked files and the untracked set untouched |
| Production Event = INACTIVE | PASS | `production_allowlist()` = EMPTY; no backend file in the release commit |
| P22 = NOT STARTED | PASS | no P22 artifact exists in the commit or the working tree |

## 11. Final Status and Next Authorized Step

```text
P21 RELEASE = LOCAL COMPLETE (Commit PASS · Tag PASS) · REMOTE PUBLICATION PENDING (environment)

the release payload is committed and tagged locally and can be pushed unchanged once egress to
github.com is available; nothing in the payload needs to change for that push

NEXT AUTHORIZED STEP = P21 REMOTE PUSH GATE (retry)
  — requires network access to https://github.com/jayfeng6848-ctrl/UAP.git from the execution host
  — the gate must re-verify: local commit/tag, remote target, refspec (main + the release tag only),
    no unrelated commit or tag is pushed, and no historical dirty work is pushed
  — this round does not retry indefinitely and does not modify the release to work around the network

HARD STOP = ACTIVE
```

## 12. Hard Stop

```text
HARD STOP = ACTIVE
```

This round executed the authorized release steps that the environment permitted — pre-commit gate,
version-only metadata change, regression, explicit allowlist staging, release commit and annotated
tag — and recorded the exact blocker for the remaining step (network egress to GitHub). The remote
publication was attempted with an explicit refspec and failed before reaching the server, so no
remote state changed. No historical dirty work was touched, no tag was moved, no history was
rewritten, and P22 / production event activation were not started.

Evidence placement: this report and the record-book entries were written **after** the release commit
and are therefore post-release evidence — they are not members of the release commit `7ff9ebc2`. The
committed release payload remains exactly the 108 paths described in §4.
