# Dependency Rules

These rules are enforced automatically by `tests/architecture/test_dependency_rules.py`.
A violation fails CI — code review cannot override it.

## 1. Domains depend on Core

```text
domains/*  ──▶  core/*     ALLOWED
core/*     ──▶  domains/*  FORBIDDEN
```

Core must stay business-agnostic forever. The moment core knows what a space is
*for*, every domain pays for it.

Enforced by:
- `test_core_never_imports_domains`
- `test_core_imports_only_core`
- `test_domains_may_depend_on_core_but_not_reverse`

## 2. No industry vocabulary in Core

Words such as restaurant, menu, employee, payroll, invoice, patient, family,
company must never appear in `core/**`. Space kinds are runtime data supplied
by a domain, never constants declared in core.

Enforced by: `test_core_contains_no_business_vocabulary`

## 3. No vendor AI SDK in Core or Intelligence

`openai`, `anthropic`, `deepseek`, `ollama` and friends may only be imported
inside provider adapters. Business code binds to `AIProvider`, never to a
vendor type.

Enforced by: `test_intelligence_has_no_vendor_sdk_imports`

## 4. Agents never touch the database

```text
Agent ─▶ Policy ─▶ Tool ─▶ Service ─▶ Database
```

`agent/**` must not import `sqlalchemy`, `psycopg` or `infrastructure`.

Enforced by: `test_agent_never_reaches_the_database`

## 5. Domains do not define schema in this phase

No `CREATE TABLE`, no ORM models, no migrations for any domain yet. Domain
packages contain a manifest and documentation only.

Enforced by: `test_domains_define_no_schema_or_persistence`

## 6. Secrets never enter the repository

`.env` is git-ignored, `.env.example` holds empty keys only, and no credential
shaped literal may be committed.

Enforced by: `tests/security/test_no_secrets.py`

## 7. Services layer

```text
apps/*     ──▶  services/*          ALLOWED
apps/*     ──▶  infrastructure/*    ALLOWED (assembly, lifecycle, health checks only)
agent/*    ──▶  services/*          FORBIDDEN (enter via Policy / Tool contracts)
domains/*  ──▶  services/*          FORBIDDEN
domains/*  ──▶  infrastructure/*    FORBIDDEN
services/* ──▶  domains/*           ALLOWED (public, stable domain contracts only)
core/*     ──▶  services/*          FORBIDDEN
```

`core/` stays contracts and base abstractions: it never depends on `services/`
and carries no SQLAlchemy persistence. `services/` owns use-case orchestration,
transaction coordination and business persistence access — it is the only
business layer allowed to reach persistence. `apps/` must not use
SQLAlchemy/psycopg for business persistence (it may still use `infrastructure/`
for assembly, lifecycle and health checks). `domains/` never depends on
`services/` or infrastructure implementations.

> **Enforcement status**: the guards for this section are **implemented** in
> `tests/architecture/test_dependency_rules.py` (and `tests/contract/` for the
> readiness component). Classification follows `D-PLAT-17`:
>
> | Guard | Rule | Level |
> |---|---|---|
> | `G-1` | `core ↛ sqlalchemy / psycopg / psycopg2` | **hard** |
> | `G-2` | `core ↛ services` | **hard** |
> | `G-3` | `agent ↛ services` | **hard** |
> | `G-4` | `domains ↛ services / infrastructure` | **hard** |
> | `G-5` | `apps ↛ sqlalchemy / psycopg` (**proxy** criterion, not equivalent to "business persistence") | advisory |
> | `G-6` | readiness must report a critical `migration` component | **hard** |
> | `G-7` | startup must not run the legacy runner; no startup migration switch | **hard** |
> | `G-8` | bootstrap uniqueness | deferred (out of this slice) |
> | `G-9` | compose revision drift detection | cancelled (`D-PLAT-15 v2` removed revision literals) |
>
> There is no CI in this slice: hard gates are executed manually and their
> evidence is retained (`D-PLAT-17` ⑦). Advisory results must never be used as
> the sole basis for declaring a hard gate passed.

Authoritative decisions: `D-PLAT-02` … `D-PLAT-06`, `D-PLAT-17` in
[`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md).

## Adding a rule

Add the check to `tests/architecture/` in the same commit that introduces the
constraint. A written rule without a test is documentation, not enforcement.
