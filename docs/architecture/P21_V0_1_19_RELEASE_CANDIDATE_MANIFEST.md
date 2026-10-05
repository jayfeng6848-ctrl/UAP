# P21 V0.1.19 RELEASE MANIFEST (FINAL)

> **Release type:** Post-Release Correction
> **Version:** `0.1.19`
> **Tag:** `UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS`
> **Title:** `UAP v0.1.19 — P21 Authentication UX Corrections`
> **Parent commit (must be exact):** `7ff9ebc204716a2c1cd36a927e361a7d27e41df2`
> **Parent tag (immutable):** `UAP-V0.1.18-P21-COMPANY-UI`

## 1. Hash basis — canonical rule

```text
Release Payload SHA-256 BASIS = COMMITTED GIT BLOB BYTES
                                (verified equal to the clean-clone artifact bytes)
NOT: working-tree line endings on another platform

All ten payload paths are LF in the working tree and `.gitattributes` is `* text=auto eol=lf`,
so the committed blob bytes equal the working-tree bytes. Every hash below was nevertheless
derived from the STAGED GIT BLOB (`git cat-file blob :<path>` → SHA-256), i.e. the canonical
committed-artifact basis required by the frozen F-RP-06 rule.
```

**Manifest self-hash rule:** this manifest is itself a payload path, and its own row is
**SELF-EXCLUDED FROM ITS OWN HASH** (a file cannot truthfully contain its own SHA-256). The other
nine rows are exact and independently re-verifiable from the commit.

## 2. Release payload — exactly 10 paths, sorted by path

| # | Path | Status | SHA-256 (committed blob basis) | Bytes | Lines |
| --- | --- | --- | --- | --- | --- |
| 1 | `apps/frontend/package-lock.json` | M | `85820a0395d31d875e87632698f8fb3dadf2d6b68635b3bbc6d43cd1d2664823` | 136608 | 3991 |
| 2 | `apps/frontend/package.json` | M | `6a1ec5b8492f31335771609eabc47a55d64139fb0f6a1e1f905c85eccbf3866a` | 1089 | 38 |
| 3 | `apps/frontend/src/app/routing/pages/LoginPage.test.tsx` | A | `b860532e5083f742c149ef93efd6666d768ad3e6a405b65ff59f2282930feb34` | 5879 | 177 |
| 4 | `apps/frontend/src/app/routing/pages/LoginPage.tsx` | M | `81dabee0e07b40bc4193e6d66563b9def2a91a8263784ed67e8ba832a5c85837` | 4211 | 109 |
| 5 | `apps/frontend/src/platform/api/client.ts` | M | `4cfd5d176675296adcbff8ca3d90035fd97f0fff6cacc01eb045dd9243215ff2` | 5203 | 148 |
| 6 | `apps/frontend/src/platform/auth/AuthContext.recovery.test.tsx` | A | `a677e852ce735cf3957490ed18096666575001c9fac771f93c6314da1f28ff57` | 7426 | 186 |
| 7 | `apps/frontend/src/platform/auth/AuthContext.tsx` | M | `451262badf4973b75c980b679fe47e0e813e2f54a411cc4ea475595f9d0da2c7` | 6808 | 209 |
| 8 | `docs/architecture/P21_V0_1_19_RELEASE_CANDIDATE_MANIFEST.md` | A | `<SELF-EXCLUDED>` | — | — |
| 9 | `docs/architecture/P21_V0_1_19_RELEASE_NOTES.md` | A | `aadddce0bc329a4c5bd90d620618d0b6bfd3a38aac1635a6133e3d16fafcb9fa` | 3088 | 83 |
| 10 | `docs/architecture/P21_V0_1_19_RELEASE_PREPARATION_READINESS_REPORT.md` | A | `9d37c669da709adf49ec38fcead5bd5c19b179ad59f25d22ac5f7340a7cbe937` | 3939 | 83 |

Composition: 5 validated correction files (RUT-03 / RUT-04) + 2 frontend version-metadata files
(version-only) + 3 release documents.

Diff accounting (git, tracked files only):

```text
apps/frontend/src/app/routing/pages/LoginPage.tsx                 +55 / -10
apps/frontend/src/platform/api/client.ts                          +16 / -1
apps/frontend/src/platform/auth/AuthContext.tsx                   +24 / -5
apps/frontend/package.json                                        +1  / -1   (version-only)
apps/frontend/package-lock.json                                   +2  / -2   (version-only)
added files (5): 2 correction tests + 3 release documents
```

## 3. Why each path is in the payload

| Path | Reason |
| --- | --- |
| `LoginPage.tsx` | P21-RUT-03 — shipped sign-in form exposes an explicit **Device ID** input and forwards it through the existing `AuthProvider.login(login, password, deviceId)`. No enrollment/trust/back-end change. |
| `LoginPage.test.tsx` | P21-RUT-03 coverage (7 cases). |
| `client.ts` | P21-RUT-04 — optional `RequestOptions.recovery` switch, default `true` (existing behaviour unchanged). |
| `AuthContext.tsx` | P21-RUT-04 — the refresh path runs with `recovery: false`, removing the refresh self-await. |
| `AuthContext.recovery.test.tsx` | P21-RUT-04 coverage (5 cases). |
| `package.json` | Frontend version → `0.1.19` (version-only). |
| `package-lock.json` | Root + `packages[""]` version → `0.1.19` (version-only; no dependency, resolution, script or tooling change). |
| release documents (3) | Formal release evidence for this correction release. |

## 4. Scope proof

```text
Staged payload paths = 10 exactly ................................ PASS
Payload ⊆ authorized release scope (HD-P21-11 §3/§5/§8) .......... PASS
Historical dirty paths ∩ payload ................................. 0
Unexpected staged paths .......................................... 0
Missing required payload paths ................................... 0
Backend / migration / permission / schema paths in payload ....... 0
```

Historical dirty work stays untouched and is **outside** this release (195 paths: docs 155 ·
tests 23 · domains 7 · apps/api 4 · migrations_alembic 2 · services 2 · infrastructure 1 · scripts 1).

## 5. Explicitly excluded

```text
P22 · Company feature expansion · new API · backend auth changes · database schema · migration
new permissions · new device lifecycle · new tenant semantics · Production Event activation
AI functionality · unaccepted features · other unauthorized frontend findings
OBS-RUT-03 · OBS-RELEASE-01 · apps/api historical work · unrelated documentation
```

## 6. Verification procedure (reproducible)

```text
for p in <the 10 paths>:
    git cat-file blob <release-commit>:<p> | sha256sum   # compare with this manifest (row 8 self-excluded)
git show --name-status <release-commit>                  # exactly these 10 paths
git cat-file -t UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS      # tag (annotated)
git rev-parse UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS^{}     # = release commit
```

This manifest must not be modified after commit + tag; any later change would create a new
unpublished working-tree change.
