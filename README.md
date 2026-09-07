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
migrations/      ordered .sql files applied by the built-in runner
tests/           unit integration contract e2e security concurrency recovery
                 + architecture guard
config/          environment-driven settings (no secrets in code)
docs/            architecture, security, api, socket, ai, agent, operations
```

## Quick start

```bash
cp .env.example .env          # then fill in locally (never commit)
pip install -r requirements.txt

# Option A: local PostgreSQL
export DATABASE_URL=postgresql+psycopg://uap:uap@localhost:5432/uap

# Option B: docker (api + postgres)
docker compose up --build

python scripts/migrate.py      # apply migrations
uvicorn apps.api.main:app --reload
```

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
