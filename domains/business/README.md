# Business Domain (`business`)

Status: **placeholder** — no implementation in this phase.

## What exists

- `manifest.py` — declares metadata only: id, version, core dependencies,
  permissions this domain intends to request.

## What does NOT exist

- No business logic
- No database tables
- No API routes
- No agents or tools

## Rules

- This domain may import from `core.*`.
- `core.*` must never import from `domains.*`.
- Tables and migrations for this domain arrive in a later phase only.
