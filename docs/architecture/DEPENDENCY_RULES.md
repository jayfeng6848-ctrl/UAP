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

## Adding a rule

Add the check to `tests/architecture/` in the same commit that introduces the
constraint. A written rule without a test is documentation, not enforcement.
