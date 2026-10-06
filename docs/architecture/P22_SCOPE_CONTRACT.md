# P22 SCOPE CONTRACT (PROPOSAL — AWAITS HUMAN RATIFICATION)

Source: `P22_PREP_REPORT.md` (audit, candidate analysis, ranking) · Decision basis: `HD-P22-01`

Status: **PROPOSAL ONLY** — this contract becomes binding only after the `P22 PREP GATE` Human Decision.
Nothing in this document authorizes implementation.

## 1. Scope Statement

```text
Goal: make the released platform usable by a real user end-to-end, at the lowest architectural risk,
      and freeze the contract that a future second domain must satisfy.

It does NOT add a new domain, does NOT activate production events, does NOT change the authorization
model, and does NOT change the database.
```

## 2. IN-SCOPE (proposed)

| # | Item | Why | Backend change | Migration |
| --- | --- | --- | --- | --- |
| 1 | Device enrolment flow in the console (challenge → register → verify) using the existing 4 device endpoints | The released UI cannot be used by a real user today (OBS-1); endpoints already exist | none | none |
| 2 | Device management surface: list / revoke / lost feedback using the existing endpoints | Operational hygiene for a real device; sessions stay revocable | none | none |
| 3 | Session access UX: device-required path, 401 recovery messaging, logout confirmation, session expiry feedback | Completes the identity session contract the Foundation implements | none | none |
| 4 | Tenant switcher affordance on top of the existing URL-driven tenant contract | Multi-tenant console usability without new semantics | none | none |
| 5 | List affordances limited to the frozen filters (`limit`, `status`, `employee_id`, `space_id`) | Useful and already permitted by the frozen Company API | none | none |
| 6 | Usability polish already identified (empty / error / loading states, correlation display) | Consistency with the accepted error UX | none | none |
| 7 | Design only: Domain Module Contract v1 (checklist a new domain must satisfy, derived from the Company precedent) | Answers the platform-reuse question without committing to a second domain | none | none |

Every in-scope item reuses released contracts. Items 1–6 are frontend-only; item 7 is documentation-only.

## 3. OUT-OF-SCOPE (proposed)

```text
production event activation (the allowlist stays EMPTY) · worker / scheduler / Celery
second domain implementation (schema · authorization · API · UI) · notification capability
search · files · workflow · task / job engines · low-code / plugin / dynamic schema systems
RLS · API versioning · authorization model redesign · new ACL subject types or roles
employee-to-user binding (requires an API contract change) · delete / admin capabilities (permissions reserved)
agent autonomous domain actions · AI-driven data mutation · production deployment
database changes of any kind (tables · migrations · DDL · DML · seed)
platform monolith refactors · global test-architecture rewrites
```

## 4. DEFERRED (proposed, with the decision that would unblock each)

| Item | Unblocking decision |
| --- | --- |
| Second domain implementation (Commercial / Entertainment / …) | Human decision on the domain after the Domain Module Contract is frozen |
| Employee-to-user binding | API contract decision plus permission decision (D-P20D-05 reserved it) |
| Delete / admin Company capabilities | Business use case plus permission decision (D-P20D-03/04 reserved) |
| Notification capability | A real downstream consumer plus the full event activation prerequisites (Appendix AK) |
| Audit / activity view | Decision on a tenant-scoped audit read API and its authorization |
| Search / files / workflow / task | A concrete product requirement (none exists today) |
| Agent-to-Domain action | AI authorization decision (Actor/Agent/Worker separation, boundary, audit, idempotency) |

## 5. Boundary Definitions

### 5.1 Data boundary

```text
no new tables · no migration · no DDL / DML / seed inside P22
data access continues through the released repositories, services and read APIs only
any future schema need is designed and frozen here, then implemented in a separate authorized phase
```

### 5.2 Authorization boundary

```text
the backend remains authoritative for every decision; the console expresses capability UX only
no frontend ACL engine · no role-name shortcut · no scope-to-permission inference
device enrolment is an identity-runtime action: it authenticates the actor and registers a device;
  it must not grant a domain permission and must not become a tenant-authorization bypass
the tenant / space context of every request continues to come from the path, never from client input
```

### 5.3 Runtime boundary

```text
no new process, worker, scheduler or queue
the console keeps talking to the released API surface (45 routes today); items 1–6 add no endpoint
Runtime ≠ Control Plane remains intact: the console never performs control-plane provisioning
```

### 5.4 Frontend boundary

```text
allowed  : new screens / hooks / routes inside the existing React console, using released endpoints
allowed  : platform primitive extension when an in-scope flow requires it (e.g. a Drawer primitive)
forbidden: a second API client · a second auth / tenant store · domain logic inside platform primitives ·
           routing tables owned by more than one module
unchanged: the accepted Foundation boundaries (memory-only token, typed client, backend-authoritative
           permissions, design tokens + CSS Modules)
```

### 5.5 Event boundary

```text
the production allowlist stays EMPTY for the whole of P22
no producer · no handler registration · no allowlist entry · no activation
the accepted event infrastructure remains accepted but inactive (Appendix AK state preserved)
```

### 5.6 AI / Agent boundary

```text
no agent action inside P22; no AI-driven mutation of domain data
Actor ≠ Agent ≠ Worker ≠ DB principal remains intact; plaintext credentials are never exposed
ToolGate remains the canonical authorization path for any future agent action
```

## 6. Acceptance Criteria (summary — full matrix in `P22_ACCEPTANCE_MATRIX.md`)

```text
functional · authorization · tenant isolation · security · API · frontend · database · migration ·
event · regression · Git integrity

every criterion is classified as one of: Blocking · Non-Blocking · Observation · Deferred ·
Out of Scope · N/A
```

## 7. Change Control

```text
scope changes require a new Human Decision; this contract cannot be amended by implementation work
each in-scope item must arrive with: its own implementation authorization, its acceptance evidence and its
  regression result; none of the boundary sections 5.1–5.6 may be relaxed implicitly
the following remain permanently out of scope unless a future decision changes them explicitly:
  production event activation · database changes · authorization model changes · a second domain
  implementation · agent autonomy
```

## 8. Ratification Checklist (for the P22 PREP GATE)

```text
[ ] IN-SCOPE list accepted (or amended)
[ ] OUT-OF-SCOPE list accepted
[ ] DEFERRED list accepted with its unblocking decisions
[ ] OQ-1 … OQ-8 answered (P22_PREP_REPORT.md §6)
[ ] Implementation Contract authorized to be drafted (only after the above)
```
