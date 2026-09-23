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
