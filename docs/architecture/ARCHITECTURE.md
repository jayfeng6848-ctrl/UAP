# UAP Architecture

Version `0.1.0` · `PHASE-0 / PROJECT-INITIALIZATION`

UAP is a business-agnostic platform core for AI agents. This phase delivers the
foundation only: no domain features, no business tables, no vendor coupling.

## Layers

```text
apps/           delivery (FastAPI api, worker, frontend)
   |
agent/          agent runtime, registry, tools, memory, workflow
   |
intelligence/   provider-agnostic AI gateway, router, embeddings, AI policy
   |
core/           identity auth tenant space membership permission
                device session policy event audit resource
   |
infrastructure/ database cache queue storage logging monitoring
```

Domains sit beside this stack and depend on it:

```text
domains/family         ─┐
domains/company         ├─▶ core  (allowed)
domains/business        │
domains/entertainment  ─┘

core ─▶ domains  (FORBIDDEN)
```

## Core module responsibilities

| Module     | Owns                                                  |
|------------|-------------------------------------------------------|
| identity   | Identity, resolution, external references             |
| auth       | Credentials, authentication flow, token issuance      |
| tenant     | Tenant, tenant isolation                              |
| space      | Space and space context (kind is data, never a constant) |
| membership | Identity ↔ space binding and role key                 |
| permission | RBAC/ABAC authorization, **default deny**             |
| device     | Device registration and revocation                    |
| session    | Session lifecycle and revocation                      |
| policy     | Policy and risk evaluation                            |
| event      | Domain event contract and event bus interface         |
| audit      | Append-only audit for security, agent and tool actions |
| resource   | Generic resource identity, ownership and scope        |

## Agent execution boundary

```text
Agent ─▶ Policy ─▶ Tool ─▶ Service ─▶ Database
```

An agent never touches the database. `tests/architecture` enforces that no
module under `agent/` imports `sqlalchemy`, `psycopg` or `infrastructure`.

## Data

- PostgreSQL is the primary datastore; connections are created lazily.
- Migrations are ordered `.sql` files in `migrations/`, applied transactionally
  with a `schema_migrations` checksum ledger (`scripts/migrate.py`).
- Redis, queue and object storage exist as interfaces only in this phase.

## Observability

- Structured JSON logs with the envelope `timestamp, level, service, module,
  request_id, trace_id, user_id, tenant_id, space_id, event`.
- Credentials are redacted by field name and by value pattern.
- `GET /health` (liveness) never performs I/O; `GET /ready` (readiness) probes
  PostgreSQL. The AI gateway is **not** part of readiness.

## Configuration

All configuration comes from the environment via `config/settings.py`. No secret
has a default and `.env` is never committed.
