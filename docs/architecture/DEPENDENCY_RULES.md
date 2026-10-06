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

## 8. Authorization boundary

Frozen by `D-AUTH-01`…`D-AUTH-25` (see
[`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md)).

Registry: `D-AUTH` total **25** = `FROZEN` **22** + `DEFERRED` **3** + `SUPERSEDED` **0**
(`OQ` 22 = 19 + 3; plus the non-OQ `D-AUTH-23` (GAP-11) and `D-AUTH-24` / `D-AUTH-25` (D-B14-08 conflict resolution, 2026-09-24); platform-level supersession = 1: `D-B14-08` → SUPERSEDED by `D-AUTH-05`).

```text
Subject ──▶ Authorization Contract ──▶ (services) authorization decision
                 ▲
Agent ───────────┘   NEVER directly to Database / Infrastructure / services

core/*           = authorization contracts, value objects, pure rules   (no I/O)
services/*       = authorization decision orchestration + persistence
infrastructure/* = persistence adapters only
```

Rules:

- An agent reaches controlled capability **only** through the Authorization
  Contract, the Policy Contract and the Tool Contract (`D-AUTH-16`, `D-PLAT-05`).
- A **Tool must never bypass** the authorization service (`D-AUTH-09`).
- A **Module must never create a second permission system** (`D-AUTH-21`).
- Authorization failure must **never** become `ALLOW` (`D-AUTH-12`).
- **No implicit resource-parent inheritance** (`D-AUTH-08`).
- Authorization **contracts** stay in `core/`; **implementations** belong in
  `services/` — `core ↛ services` (`G-2`) and `agent ↛ services` (`G-3`) hold.

> Status: **implemented and accepted** (commit `034ee97`, tag
> `UAP-V0.1.8-AUTHORIZATION`). `core/permission` · `core/policy` ·
> `core/resource` · `core/audit` hold the contracts; `services/authorization/`
> holds the deciding service (the first package under `services/`). This round
> adds **no new guard**: `G-1`…`G-9` are unchanged. The rules above are covered
> by the existing dependency guards (`G-1`…`G-4`) plus `tests/security` and
> `tests/architecture`.

## 9. Agent runtime boundary (design frozen)

Frozen by `D-AGENT-01`…`D-AGENT-16` —
[`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md) ·
[`AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`](./AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md).

```text
Agent Runtime ──▶ AI Gateway Contract    ALLOWED   (core contract — D-AGENT-16)
Agent Runtime ──▶ Authorization Contract ALLOWED   (core contract — D-AUTH-16)
Agent Runtime ──▶ Tool Contract          ALLOWED
Agent Runtime ──▶ Executor abstraction   ALLOWED   (D-AGENT-12)

✗ Runtime ──▶ OpenAI / Anthropic / Gemini / other provider SDK
✗ Runtime ──▶ PostgreSQL direct  (Agent ─▶ Policy ─▶ Tool ─▶ Service ─▶ Database)
✗ Runtime ──▶ Celery / Redis Queue / RabbitMQ / other concrete worker framework
✗ core ──▶ services · agent ──▶ services · agent ──▶ infrastructure  (unchanged)
```

Rules:

- The runtime **never rebuilds provider abstraction**; it binds only to the
  gateway contract (`D-AGENT-16`).
- A worker is a **future** addition: it only exists behind the execution
  abstraction, **must consume the unified `AgentRun`**, and **must re-verify
  authorization and approval** — an enqueue-time decision is not trusted
  (`D-AGENT-12`).
- A **second execution engine must never exist**; a workflow orchestrates by
  starting `AgentRun`s (`D-AUTH-21`).
- **No new vendor SDK** may appear in `core/`, `intelligence/`, `agent/` or the
  runtime (extends rule 3 above).

> Status: **design frozen — not implemented**. **No guard is added this round**;
> `G-1`…`G-9` unchanged. The runtime guards proposed as **`G-10`…`G-14`**
> (no provider SDK in the runtime · no DB in `core/agent` · no worker framework ·
> exhaustive state-machine transitions · error-code set) are recorded in the
> contract §M.3 and must land **in the implementation commit itself**. A written
> rule without a test is documentation, not enforcement (see the last section).

## Carrier faces — five distinct surfaces (`D-P10-17`)

A single "log" does not exist. Five carrier faces are formally separated, and
`event` must never be fused with `audit` (nor either with an operational log):

| face | carrier | owner |
|---|---|---|
| **event** | `events` table (domain fact + outbox; at-least-once, replayable) | **P10** |
| **audit** | `audit_logs` table (compliance, immutable, not replayable) | **P10** |
| **operational log** | `infrastructure/logging` (structured JSON + redaction; **never a DB table**) | not P10 |
| **trace** | `trace_id` in the log envelope (a correlation identifier, not a carrier) | not P10 |
| **metric** | undefined (a future monitoring surface) | not P10 |

Rules:

- An operational log is **never** written into `audit_logs`; audit records are
  compliance artefacts with `reason` / `risk_level`, not diagnostics.
- `event` and `audit` are **never** merged into one carrier: an event is a
  replayable fact, an audit row is an immutable non-replayable record.
- P10 owns the two carriers and **only** those two. The seven
  `ix_events_*` / `ix_audit_*` indexes belong to **P12** (`D-P12-08`), so the
  P10 migration creates none.
- Enforced by `tests/architecture/test_p10_event_audit_boundary.py`.

## Adding a rule

Add the check to `tests/architecture/` in the same commit that introduces the
constraint. A written rule without a test is documentation, not enforcement.
