# Security docs

Model, threat notes and hardening checklist live here.

Implemented in STEP 0:
- default-deny authorization contract (`core/permission`)
- automatic credential redaction in structured logs
- readiness/liveness separation so a dependency outage cannot crash-loop the API
- secret placeholder refused outside development/test
- automated secret scanning (`tests/security`)

Readiness additionally gates on **database schema revision consistency**: the
database revision must equal the expected revision (injected at build time as a
read-only artifact that a runtime environment variable cannot override).
Missing, behind, **ahead of**, or unverifiable schema ⇒ `GET /ready` returns **503**, while
`GET /health` remains an I/O-free liveness probe. Application startup never
applies migrations.

Security properties of the gate:

- **Fail closed**: every failure branch produces a `critical` component with
  status `error`, so an unknown or drifted schema state is never treated as ready.
- **Authority cannot drift**: the expected revision is derived from the Alembic
  graph at image build time and frozen into the image; `Dockerfile` args, compose
  literals and runtime environment variables are not authoritative.
- **No runtime derivation**: the running application never scans the migration
  directory, never imports Alembic and never guesses a head from file names.
- **Read-only probing**: the probe executes a single `SELECT` against
  `alembic_version` with a dedicated 2000 ms statement timeout; it cannot alter
  schema, data or the migration authority.
- **No secret leakage**: the probe reports only the expected/actual revision
  strings and their resolution source; none of these is a secret.

> Status: **implemented**. See `D-PLAT-08` / `D-PLAT-14` / `D-PLAT-15 v2` /
> `D-PLAT-16` in `docs/architecture/PLATFORM_DECISION_LOG.md`.

## Authorization model (design frozen)

Frozen by `D-AUTH-01`…`D-AUTH-25` in `PLATFORM_DECISION_LOG.md`. Implementation exists in the working tree (uncommitted); acceptance pending.

> Registry: `D-AUTH` total **25** = `FROZEN` **22** + `DEFERRED` **3** + `SUPERSEDED` **0**
> (`OQ` 22 = 19 + 3; plus the non-OQ `D-AUTH-23` (GAP-11) and `D-AUTH-24` / `D-AUTH-25` (D-B14-08 conflict resolution, 2026-09-24); platform-level supersession = 1: `D-B14-08` → SUPERSEDED by `D-AUTH-05`).
>
> **`D-AUTH-23`**（`FROZEN` · `GAP-11`）: `agent_permissions.resource_scope` = **OPAQUE TEXT** —
> **NOT AUTHORIZATION AUTHORITY**（不构成授权权威）. It must not be parsed / normalized / mapped / promoted /
> reinterpreted as a canonical scope, and `invalid` / `unknown` / empty / whitespace values
> **cannot produce `ALLOW`**. `ND-A = RESOLVED` — **no `<> ''` constraint**.
> `P09` and `0011` remain **unchanged**.

- **Default deny / fail closed**: authorization-service unavailability, policy or
  permission lookup failure, unknown subject/resource/action, and expired or
  revoked grants all yield `DENY` — never `ALLOW` (`D-AUTH-12`).
- **`DENY > ALLOW`**, deterministic, order-independent and auditable (`D-AUTH-07`).
- **Agent cannot exceed delegated authority**; agent authority is never
  automatically the owner's authority (`D-AUTH-02` / `D-AUTH-03`).
- **Tool cannot bypass authorization** — a tool is the only controlled execution
  boundary (`D-AUTH-09`).
- **Tenant boundary** `PLATFORM → TENANT → SPACE`; no implicit resource-parent
  inheritance (`D-AUTH-06` / `D-AUTH-08`).
- **No authorization cache** at present; any future cache must be bounded,
  revocation-invalidating and must never fail open (`D-AUTH-13`).
- **Approval ≠ permission**: a static tool requirement **or** a policy
  requirement triggers approval, and approval never equals `ALLOW` (`D-AUTH-11`).
- **Audit separation**: authorization-decision audit is a different record from
  tool-execution audit (`D-AUTH-15`); audit persistence is deferred to P10.
- **Subject vocabulary**: authorization subjects are `USER` / `ROLE` / `AGENT`,
  orthogonal to identity providers (`D-AUTH-18`).

Inherited and unchanged: `R2-D-14` (`DENY > ALLOW`), `R2-D-15` (permission
scope-neutral), `R4` (`effective_platform_admin`), ACL subject types
`user | role | agent`, P09 schema.

> Status: **design frozen — not implemented**. No authorization code, service or
> schema exists. See
> [`docs/architecture/AUTHORIZATION_PREP_REPORT.md`](../architecture/AUTHORIZATION_PREP_REPORT.md).
