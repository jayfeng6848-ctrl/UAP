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

## Authorization decision (contract)

Frozen by `D-AUTH-01`…`D-AUTH-25`. Implemented and accepted — commit `034ee97`,
tag `UAP-V0.1.8-AUTHORIZATION` (`services/authorization/` + migration
`0012_authz_enforcement`; full regression `542 passed`).

> Registry: `D-AUTH` total **25** = `FROZEN` **22** + `DEFERRED` **3** + `SUPERSEDED` **0**
> (`OQ` 22 = 19 + 3; plus the non-OQ `D-AUTH-23` (GAP-11) and `D-AUTH-24` / `D-AUTH-25` (D-B14-08 conflict resolution, 2026-09-24); platform-level supersession = 1: `D-B14-08` → SUPERSEDED by `D-AUTH-05`).

```json
{
  "subject": "…",           // USER | ROLE | AGENT
  "delegator": "…",         // actor / delegator context, when applicable
  "action": "read",         // canonical vocabulary, lowercase form (D-AUTH-25; see below)
  "resource": {"type": "…", "id": "…", "tenant_id": "…", "space_id": "…"},
  "scope": "TENANT",        // PLATFORM | TENANT | SPACE
  "context": {},
  "decision": "ALLOW",      // ALLOW | DENY | REQUIRES_APPROVAL
  "reason": "…",
  "policy_version": "…"
}
```

Canonical actions (**lowercase** storage/transport form, `D-AUTH-25`; normalised
on ingress via NFKC → strip → casefold): `read` `list` `create` `update` `delete`
`execute` `approve` `reject` `publish` `export` `share` `admin`.

- `REQUIRES_APPROVAL` is a **decision state, not a grant** — no caller may treat
  it as executable (`D-AUTH-14`).
- `DENY > ALLOW`; results are deterministic, order-independent and auditable
  (`D-AUTH-07`).
- Every failure path returns `DENY` (`D-AUTH-12`).

> Status: **implemented and accepted**. The contract lives in `core/permission` /
> `core/policy`; the deciding service is `services/authorization/`. See
> [`docs/architecture/AUTHORIZATION_IMPLEMENTATION_CONTRACT.md`](../architecture/AUTHORIZATION_IMPLEMENTATION_CONTRACT.md).

## Agent runs (design frozen — no endpoint exists yet)

Run semantics are frozen by `D-AGENT-01`…`D-AGENT-16`; the contract is
[`docs/architecture/AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`](../architecture/AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md).

```text
POST /agent-runs              → 202 Accepted + run_id   (carries idempotency_key)
GET  /agent-runs/{id}         → state / result          (redacted view)
POST /agent-runs/{id}/cancel  → idempotent cancellation
```

- Every route must pass authentication, tenant resolution and authorization
  **before** doing anything — a Run is itself a controlled operation.
- The **sync fast path** may return a completed result only when the Run already
  finished **and** the API contract explicitly allows it; it must **not** create a
  second execution model (`D-AGENT-01`, `D-AGENT-11`).
- **Streaming (SSE / WebSocket) = DEFERRED** to a separate decision.
- A **fourth endpoint** must not be added without a decision.

> Status: **design frozen — not implemented**. No route, package or table exists.
> Implementation is **BLOCKED** until `P10 ∧ P11 ∧ P12 ∧ P13 ∧ AI Gateway
> Runtime` are ready (`D-PLAT-09` route A, not superseded).
