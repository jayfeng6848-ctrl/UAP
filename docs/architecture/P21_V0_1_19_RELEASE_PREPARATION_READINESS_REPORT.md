# P21 v0.1.19 RELEASE PREPARATION & READINESS REPORT

> **Preparation authorization:** HD-P21-10 (preparation only)
> **Release decision:** HD-P21-11 = APPROVED — release, commit, tag and push authorized
> **Base:** `7ff9ebc204716a2c1cd36a927e361a7d27e41df2` · `UAP-V0.1.18-P21-COMPANY-UI` (immutable)
> **Release:** `0.1.19` · `UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS`

## 1. Frozen release scope — 10 files

```text
A. Correction payload (5) — validated RUT-03 / RUT-04
   apps/frontend/src/app/routing/pages/LoginPage.tsx
   apps/frontend/src/app/routing/pages/LoginPage.test.tsx
   apps/frontend/src/platform/api/client.ts
   apps/frontend/src/platform/auth/AuthContext.tsx
   apps/frontend/src/platform/auth/AuthContext.recovery.test.tsx

B. Frontend version metadata (2) — version-only update to 0.1.19
   apps/frontend/package.json
   apps/frontend/package-lock.json

C. Release documentation (3)
   docs/architecture/P21_V0_1_19_RELEASE_CANDIDATE_MANIFEST.md
   docs/architecture/P21_V0_1_19_RELEASE_NOTES.md
   docs/architecture/P21_V0_1_19_RELEASE_PREPARATION_READINESS_REPORT.md
```

Exact hashes and diff accounting live in the release candidate manifest.

## 2. Findings carried by this release

| Finding | Nature | Status |
| --- | --- | --- |
| P21-RUT-03 | Login UX capability (Device ID input → existing login path) | CLOSED |
| P21-RUT-04 | Authentication recovery-path correctness | CLOSED / VALIDATED |

## 3. Version metadata (decision taken under HD-P21-11)

| Source | Before | After | Classification |
| --- | --- | --- | --- |
| `apps/frontend/package.json` | `0.1.18` | `0.1.19` | REQUIRED — version-only |
| `apps/frontend/package-lock.json` (root + `packages[""]`) | `0.1.0` | `0.1.19` | REQUIRED — version-only (2 lines, no dependency/resolution change) |
| `pyproject.toml` | `0.1.17` | unchanged | NOT REQUIRED — back end not changed by this release |
| `config/settings.py` `APP_VERSION` | `0.1.17` | unchanged | NOT REQUIRED — same reason |
| `docker-compose.yml` `APP_VERSION` | `0.1.17` | unchanged | NOT REQUIRED — same reason |
| `README.md` hero line | `0.1.0 / PHASE-0` | unchanged | OBSERVATION — stale historical doc, out of scope |

`package-lock.json` was edited by hand; `npm install` was never run, so no dependency or resolution
drift could be introduced. `git diff --numstat` proves the change is exactly `+1/-1`
(`package.json`) and `+2/-2` (`package-lock.json`).

## 4. Pre-release verification (re-measured)

```text
focused tests : AuthContext.recovery + AuthContext + client + LoginPage + AppRouter → 43 passed / 0 failed
typecheck     : PASS
build         : PASS
real Chromium : success path / rejected sign-in / expired session / refresh transport failure → 4 PASS
security      : 0 localStorage · 0 sessionStorage · 0 cookie auth · 0 hard-coded credentials ·
                0 hard-coded device ids · 0 auth bypass · 0 second auth engine · 0 eval · 0 unsafe HTML
architecture  : Core → Domain = 0 · frontend → backend imports = 0 · single API client ·
                single AuthProvider · single recovery mechanism (recovery=false on the refresh path only)
database      : DDL 0 · migration 0 · schema change 0 · formal `uap` untouched
git           : historical dirty work preserved (195 paths) · candidate ⊆ authorized scope · unexpected = 0
```

## 5. Readiness

```text
scope frozen (10 files) ................. YES
correction files accounted .............. YES (SHA-256 + diff + reason)
version metadata decided ................ YES (frontend 0.1.19 · back end unchanged 0.1.17)
historical dirty work preserved ......... YES
release evidence + notes complete ....... YES
security / architecture / regression .... PASS
DB unchanged ............................ YES
unexpected paths = 0 .................... YES
blocking findings = 0 ................... YES
```

```text
P21 POST-RELEASE CORRECTION RELEASE PREPARATION = READY
```
