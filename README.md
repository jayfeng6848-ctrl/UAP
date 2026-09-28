# UAP — Universal AI Platform

Version `0.1.0` · Phase `PHASE-0 / PROJECT-INITIALIZATION`

A clean, stable, secure and extensible foundation for an AI agent platform.
**This phase contains platform plumbing only** — no family, company, restaurant,
business or entertainment functionality has been implemented.

## The one rule

```text
domains  ──▶  core        allowed
core     ──▶  domains     FORBIDDEN (enforced by tests/architecture)
```

`core/` is business-agnostic. It knows about identity, tenants, spaces,
permissions and resources — never about a specific industry.

## Layout

```text
apps/            api (FastAPI), worker, frontend skeleton
core/            12 platform modules: identity auth tenant space membership
                 permission device session policy event audit resource
intelligence/    provider-agnostic AI gateway, router, embeddings, AI policy
agent/           runtime, registry, tools, memory, workflow (interfaces only)
domains/         family | company | business | entertainment (manifests only)
infrastructure/  database, cache, queue, storage, logging, monitoring
migrations/      legacy .sql baseline (read-only; Alembic is the schema entry point)
tests/           unit integration contract e2e security concurrency recovery
                 + architecture guard
config/          environment-driven settings (no secrets in code)
docs/            architecture, security, api, socket, ai, agent, operations
```

## Quick start

```bash
cp .env.example .env          # then fill in locally (never commit)
pip install -r requirements.txt
```

There are **two independent database identities** (D-OP101-10); there is no
fallback in either direction:

```bash
# Option A: local PostgreSQL -- fill in BOTH, with separate values
export DATABASE_URL=postgresql+psycopg://<runtime-role>:<password>@<host>:<port>/<db>
export UAP_MIGRATION_DATABASE_URL=postgresql+psycopg://<migration-role>:<password>@<host>:<port>/<db>

# Option B: docker (api + postgres) -- the api service carries DATABASE_URL only
docker compose up --build

# Apply schema migrations. Alembic reads ONLY UAP_MIGRATION_DATABASE_URL:
#   Alembic does NOT use DATABASE_URL.
#   DATABASE_URL is NOT a migration fallback.
# A missing UAP_MIGRATION_DATABASE_URL fails closed.
alembic upgrade head           # apply schema migrations (sole entry point)
uvicorn apps.api.main:app --reload
```

> The legacy `python scripts/migrate.py` is historical only (retained read-only)
> and is **not** a schema entry point; application startup never applies
> migrations. See `docs/architecture/STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md`.

Endpoints: `GET /health` (liveness), `GET /ready` (readiness),
`GET /api/v1/meta`, interactive docs at `/docs`.

## Tests

```bash
pytest                      # full suite (offline-safe)
pytest -m integration       # requires a reachable PostgreSQL
pytest tests/architecture   # dependency-rule guard
```

## Guarantees in this phase

- No business logic and no business tables anywhere.
- No vendor AI SDK is imported by `core/` or `intelligence/`.
- No secret is committed; `.env` is ignored and `.env.example` holds empty keys.
- Structured logs redact credentials automatically.
- The AI gateway never affects platform readiness.
