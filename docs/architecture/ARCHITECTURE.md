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
services/       use-case orchestration, transaction coordination,
                business persistence access
   |
intelligence/   provider-agnostic AI gateway, router, embeddings, AI policy
   |
core/           identity auth tenant space membership permission
                device session policy event audit resource
   |
infrastructure/ database cache queue storage logging monitoring
```

`services/` depends on `core/` (contracts) and `infrastructure/`; `apps/`
assembles it. `core/` never depends on `services/` and carries no persistence.
Authoritative layer rules: `DEPENDENCY_RULES.md` §7 · decisions `D-PLAT-02` …
`D-PLAT-06` in `PLATFORM_DECISION_LOG.md`.

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

## Event delivery boundary

`EventBus != Outbox` — they are **not** the same delivery mechanism and must never be
described as one (frozen by `D-P10-02`, clarification `C-3`).

```text
Outbox (`events` table) = durable / reliable event delivery authority
                          CAS claim + lease 60s + Reaper; at-least-once;
                          consumer idempotent by `event_id`

EventBus                = optional in-process auxiliary mechanism, and
                          MUST NOT replace outbox persistence
                          MUST NOT be treated as the durable delivery boundary
                          MUST NOT become the canonical cross-process delivery mechanism
```

- Domain event identity is **UUIDv7 canonical** (`D-P10-02`).
- `audit_logs` is immutable, and **audit-local immutability is owned by P10**
  (`tg_audit_immutable`), not deferred to P11 (`D-P10-11`, `C-4`).
- Authoritative decisions: `D-P10-01`…`D-P10-18` in
  [`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md) (appendix G).

## Agent execution boundary

```text
Agent ─▶ Policy ─▶ Tool ─▶ Service ─▶ Database
```

An agent never touches the database. `tests/architecture` enforces that no
module under `agent/` imports `sqlalchemy`, `psycopg` or `infrastructure`.

## Authorization model

Canonical authorization is **RBAC + ACL + Policy**, frozen by `D-AUTH-01`…`D-AUTH-25`
in [`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md).

**Decision registry**: `D-AUTH` total **25** = `FROZEN` **22** + `DEFERRED` **3** + `SUPERSEDED` **0**
(`OQ` sequence: 22 = `FROZEN` 19 + `DEFERRED` 3; plus the non-OQ `D-AUTH-23` (GAP-11) and `D-AUTH-24` / `D-AUTH-25` (D-B14-08 conflict resolution, 2026-09-24); platform-level supersession = 1: `D-B14-08` → SUPERSEDED by `D-AUTH-05`).

```text
Subject (USER | ROLE | AGENT)
   │
   ├─ RBAC    baseline grant       (roles / role_permissions)
   ├─ ACL     resource-specific    (resources / resource_permissions)
   └─ Policy  contextual decision  (core/policy)
        │
        ▼
   Resource ─▶ Action ─▶ Scope ─▶ Risk ─▶ { Execute | Approval } ─▶ Tool ─▶ Audit
```

Frozen properties:

- **Agent is an independent authorization subject** (`D-AUTH-02`); migration 0007
  already registers `user` / `role` / `agent` as ACL subject types.
- **`DENY > ALLOW`**, deterministic, order-independent and auditable
  (`D-AUTH-07`, inheriting `R2-D-14`).
- **Fail closed**: every lookup failure yields `DENY` (`D-AUTH-12`).
- **Scope** is `PLATFORM → TENANT → SPACE`; `RESOURCE` / `SELF` are predicates,
  not stored grant scopes (`D-AUTH-06`).
- **Risk** uses the four canonical tiers `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`;
  risk is neither a permission nor a decision (`D-AUTH-10`).
- Authorization **contracts** live in `core/`; the deciding service belongs in
  `services/` (`D-AUTH-16`), consistent with `D-PLAT-02` / `D-PLAT-03`.
- `Authorization Decision Audit` is a **different record** from
  `Tool Execution Audit` (`D-AUTH-15`).

> Status: **implemented and accepted**. Contracts live in `core/permission` /
> `core/policy` / `core/resource` / `core/audit`; the deciding service is
> `services/authorization/` — the **first package under `services/`** — and
> migration `0012_authz_enforcement` adds the canonical-action and scope CHECK
> constraints. Landed in commit `034ee97`, tag `UAP-V0.1.8-AUTHORIZATION`.
> See [`AUTHORIZATION_PREP_REPORT.md`](./AUTHORIZATION_PREP_REPORT.md) ·
> [`AUTHORIZATION_IMPLEMENTATION_CONTRACT.md`](./AUTHORIZATION_IMPLEMENTATION_CONTRACT.md) ·
> [`AUTHORIZATION_ACCEPTANCE_MATRIX.md`](./AUTHORIZATION_ACCEPTANCE_MATRIX.md).

## Agent runtime (design frozen)

Run semantics are frozen by `D-AGENT-01`…`D-AGENT-16`
([`PLATFORM_DECISION_LOG.md`](./PLATFORM_DECISION_LOG.md)); the contract lives in
[`AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md`](./AGENT_RUNTIME_IMPLEMENTATION_CONTRACT.md).

```text
POST /agent-runs · GET /agent-runs/{id} · POST /agent-runs/{id}/cancel
       │
  AgentRun — one model · one state machine · one authorization model · one audit model
       │            sync fast path          |          async long path
       ▼
  Executor abstraction ──▶ future worker (MUST consume AgentRun, never a second engine)
```

Frozen properties:

- **One Run model, two presentations** — sync and async are *not* two runtimes
  (`D-AGENT-01`); `AgentRun` is a first-class persisted object (`D-AGENT-02`).
- **Eight-state machine** (`CREATED`/`RUNNING`/`WAITING`/`WAITING_APPROVAL`/
  `COMPLETED`/`FAILED`/`CANCELLED`/`TIMEOUT`), table-driven; an invalid transition
  is rejected and **fails closed** (`D-AGENT-05`).
- **Context** is eight authorized, bounded and traceable layers; the snapshot is
  immutable, and lazy retrieval **must re-pass** authorization / policy / boundary
  checks (`D-AGENT-04`).
- **`LLM plan ≠ execution authority`** — every action proposal goes through
  Authorization → Policy → Approval → Tool (`D-AGENT-03`, inheriting `D-AUTH-09`).
- **Tool limits** = `min(platform, tenant, agent)`; a missing layer **inherits**
  the upper bound and is never read as "unlimited" (`D-AGENT-09`).
- **Dual-level idempotency** (run + tool action) **plus** resource-version /
  conditional update for actions at real conflict risk — idempotency alone does
  not close every race (`D-AGENT-06`, `D-AGENT-08`).
- **Cancellation is explicit**; client disconnect is never a cancellation, and a
  cancel request never rolls back an external side effect (`D-AGENT-07`).
- **No vendor SDK in the runtime**: `Runtime → AI Gateway Contract → Gateway
  Runtime → Provider Adapter` (`D-AGENT-16`).

> Status: **design frozen — not implemented**. No runtime code, package or table
> exists; `agent_runs` / `agent_run_steps` are **design only**. Implementation is
> **BLOCKED** until `P10 ∧ P11 ∧ P12 ∧ P13 ∧ AI Gateway Runtime` are ready —
> `D-PLAT-09` route A, **not superseded**.

## Data

- PostgreSQL is the primary datastore; connections are created lazily.
- **Schema migrations**: Alembic is the sole schema-change entry point
  (`alembic.ini` + `migrations_alembic/`). The legacy `.sql` runner
  (`migrations/`, `scripts/migrate.py`) is retained **read-only** for history and
  is **not** an entry point; application startup never applies migrations.
  Authoritative rules: `STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` §1 / §16.
- Redis, queue and object storage exist as interfaces only in this phase.

## Observability

- Structured JSON logs with the envelope `timestamp, level, service, module,
  request_id, trace_id, user_id, tenant_id, space_id, event`.
- Credentials are redacted by field name and by value pattern.
- `GET /health` (liveness) never performs I/O; `GET /ready` (readiness) probes
  PostgreSQL **and gates on database schema state**: the database revision must
  equal the build-time expected revision, otherwise readiness is `503`. Missing,
  behind **or ahead** schema is not ready. The AI gateway is **not** part of
  readiness. See `D-PLAT-08` and `docs/api/README.md`.

## Configuration

All configuration comes from the environment via `config/settings.py`. No secret
has a default and `.env` is never committed.
