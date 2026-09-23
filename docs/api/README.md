# API docs

Endpoint reference lives here once routes exist.

Currently available: `GET /health`, `GET /ready`, `GET /api/v1/meta`.
Interactive OpenAPI docs: `http://localhost:8000/docs`.

## Readiness and schema state

`GET /ready` additionally gates on database schema state: the database revision
must equal the expected revision (injected at build time as a read-only artifact
that a runtime environment variable cannot override), otherwise the endpoint
returns **503** and the platform is not considered ready. Schema that is missing,
behind, **ahead of**, or cannot be confirmed is treated as not ready.

`GET /health` remains a liveness probe and performs no I/O, so a dependency
outage cannot crash-loop the API. Application startup never applies migrations —
run `alembic upgrade head` before starting a deployment.

Readiness answers with two critical components:

```json
{"status": "ready", "components": [{"name": "database", ...}, {"name": "migration", ...}], "optional": [...], "checked_at": "..."}
```

`migration` compares the database revision (`SELECT version_num FROM
alembic_version`) with the expected revision and fails closed (HTTP 503) when the
expectation is missing/invalid, the table is missing or unreadable, there is not
exactly one row, the value is NULL/empty, or the two revisions differ (ahead
counts as a mismatch). The probe is read-only, uses its own short statement
timeout (2000 ms) and never imports Alembic.

Operational guidance: [`docs/operations/DEPLOYMENT_AND_RECOVERY.md`](../operations/DEPLOYMENT_AND_RECOVERY.md).

> Status: **implemented**. See `D-PLAT-08` / `D-PLAT-14` / `D-PLAT-15 v2` /
> `D-PLAT-16` in `docs/architecture/PLATFORM_DECISION_LOG.md`.
