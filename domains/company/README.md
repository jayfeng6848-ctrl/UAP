# Company Domain (`company`)

Status: **active** (contract layer only) — activated by
`P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION` (PDL Appendix AF, D-P20D-01…11).

## What exists

- `entities.py` — `Employee` / `Assignment` entities with their frozen invariants.
- `values.py` — lifecycle vocabularies and transition tables (pure functions).
- `ports.py` — `EmployeeRepository` / `AssignmentRepository` /
  `ResourceProjectionRepository` interfaces (no implementation).
- `errors.py` — domain error codes and `CompanyDomainError`.
- `manifest.py` — metadata: status `active`, the two business tables, the 11
  canonical Company permission keys, core dependencies.

## What does NOT exist (by boundary)

- No ORM / SQLAlchemy / SQL / infrastructure import (architecture guard `G-4`).
- No authorization logic — the single engine is `services.authorization`.
- No API route, no worker, no event producer/handler.
- No migration owned by this package (`0019_p20_company` + `0020_p20_company_authorization`
  live under `migrations_alembic/`).

## Rules

- This domain may import from `core.*` and from itself; nothing else.
- `core.*` must never import from `domains.*` (Core → Domain = 0).
- Use-case orchestration (authorize → validate → write → audit → commit) belongs to
  `services/company/`; the domain exposes contracts, not transactions.
