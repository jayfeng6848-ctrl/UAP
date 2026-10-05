# UAP v0.1.19 — P21 Authentication UX Corrections

> **Release type:** Post-Release Correction
> **Version:** `0.1.19`
> **Tag:** `UAP-V0.1.19-P21-AUTH-UX-CORRECTIONS`
> **Base (immutable):** `UAP-V0.1.18-P21-COMPANY-UI` — `7ff9ebc204716a2c1cd36a927e361a7d27e41df2`

## Summary

Two independently validated post-release corrections to the P21 **frontend authentication UX**.
This is a **frontend-only** correction release: the back end, the API contract, the database schema,
the authorization model and tenant semantics are unchanged.

## P21-RUT-03 — Device ID Login UX

The shipped sign-in form now exposes the three facts a real user needs:

```text
Login · Password · Device ID
```

and forwards the device id through the already existing
`AuthProvider.login(login, password, deviceId)` entry point. A session is still issued **only** by the
existing back-end session endpoint, and **only** for an already enrolled device.

Not added: device enrollment bypass · device-trust bypass · any new back-end auth endpoint.

## P21-RUT-04 — Authentication Recovery Fix

```text
401 protected request
  → one recovery attempt
  → refresh request runs with recovery = false
  → refresh failure
  → deterministic terminal state (explicit failure, usable login form)
```

Fixed: refresh self-await · recursive refresh · permanently disabled sign-in button · silent failure.

## Validation statements

```text
real Chromium                    = PASS (shipped login form, no harness, no mocked refresh)
real back end                    = PASS
real enrolled device             = PASS
real session                     = PASS
refresh 401 deterministic settle = PASS (no self-await, no second refresh)
failure login recovery           = PASS (explicit notice, form usable, re-login succeeds)
memory-only auth                 = PASS (0 localStorage / 0 sessionStorage / 0 cookie auth)
focused tests                    = 43 passed / 0 failed · typecheck = PASS · build = PASS
Company successful journey       = PASS (Overview / Employees / Assignments with real data)
```

## Version metadata

```text
apps/frontend/package.json      : 0.1.18 → 0.1.19
apps/frontend/package-lock.json : root version and packages[""] version 0.1.0 → 0.1.19 (version-only)
```

`0.1.19` is a **P21 frontend authentication UX correction release**. The back-end implementation is
not changed by this release, so the back-end service metadata (`pyproject.toml`,
`config/settings.py`, `docker-compose.yml` → `APP_VERSION`) intentionally continues to read
`0.1.17`. That is the accepted platform-source state recorded at the 0.1.18 release, not a version
error.

## Unchanged by this release

```text
Backend source          = unchanged
Database schema         = unchanged
Migration               = unchanged
Authorization semantics = unchanged
Tenant semantics        = unchanged
Production Event        = INACTIVE
P22                     = NOT STARTED
```

## Explicitly not claimed

```text
P22 started · Production deployment · Production Event active · All authentication UX complete
```
