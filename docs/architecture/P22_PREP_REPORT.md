# P22 PREP REPORT — SCOPE & DESIGN

Decision basis: `HD-P22-01 — P22 PREP / Scope & Design = APPROVED`

Mode: read-only audit + scope/design deliverables. No implementation, no source/database/git change.

## GATE

```text
P22 PREP = PASS

P22 Scope = Frozen (proposal — awaits the Human P22 PREP GATE to become binding)
P22 Non-Scope = Frozen (proposal)   ·   P22 Deferred = Frozen (proposal)
Architecture / Security / Tenant / Runtime / Frontend / Event boundaries = drafted and confined
Acceptance Matrix = Complete (separate document)
Implementation Contract = NOT READY (by design: the scope proposal awaits human ratification)
Decision Log = Synchronized (Appendix AM appended as INPUT, not as a freeze)
Blocking Findings = 0 · Source Changes = 0 · Database Changes = 0 · Git Mutations = 0
```

Companion documents: `P22_SCOPE_CONTRACT.md` · `P22_ACCEPTANCE_MATRIX.md` ·
`PLATFORM_DECISION_LOG.md` Appendix AM.

---

## 1. Baseline (measured this round)

```text
Git ............ HEAD = 7ff9ebc204716a2c1cd36a927e361a7d27e41df2 (release commit = tag target)
                 tag  = UAP-V0.1.18-P21-COMPANY-UI (annotated) · tags = 17 · staged = 0
                 porcelain = 192 (historical dirty work + P21 release evidence) — untouched
                 remote main = 7ff9ebc2… (P21 release published)
DB ............. formal uap: 0 public tables (unchanged)
                 shared uap_b1_test: alembic 0017_p13_seed · users 0 · tenants 0 · spaces 0 ·
                 roles 1 · permissions 12 · acl_subject_types 3 · events 0
                 cluster roles: 7 (uap · uap_app · uap_bootstrap · uap_control · uap_migrator ·
                 uap_runtime · uap_seed) · databases: {uap, uap_b1_test, uap_test}
Migrations ..... head = 0020_p20_company_authorization (19 migration files)
API ............ 45 routes across 10 routers — agent_runs 2 · company 11 · control_plane 8 ·
                 devices 4 · health 2 · identity_runtime 11 · identity 2 · meta 1 · sessions 4
PDL ............ last appendix = AL (P21 frontend architecture); no P22 entry before Appendix AM
Events ......... production_allowlist() = EventAllowlist() (EMPTY)
```

## 2. Platform Audit — what actually exists (evidence, not dossier memory)

| Phase | Subject | Real state | Evidence |
| --- | --- | --- | --- |
| P13 | Seed / authorization baseline | FROZEN · released | `0017_p13_seed`; test DB: permissions 12 · acl_subject_types 3 |
| P14 | Runtime slice (trusted service boundary) | FROZEN · released | runtime principal separation; `uap_runtime` / `uap_app` roles |
| P15 | Event consumer / outbox | ACCEPTED infrastructure, inactive | `production_allowlist()` EMPTY; events table 0 rows |
| P16 | Agent runtime + tool registry | FROZEN · released (`0018_p16_agent_runtime`) | 2 agent-run routes; no domain-facing action authorized |
| P17 | Identity / tenant / space runtime | FROZEN · released | 11 `identity_runtime` routes |
| P18 | Control plane | FROZEN · released (v0.1.17) | 8 `/control/...` routes; `uap_control` ceiling |
| P19 | Event activation governance | DECISION ONLY | Appendix AH–AK: activation requires a real consumer |
| P20 | Company domain + authorization + API | FROZEN · released | `0019`/`0020` migrations; 11 Company routes |
| P21 | Frontend foundation + Company UI V1 + release | RELEASED (v0.1.18) | commit `7ff9ebc2…`; tag `UAP-V0.1.18-P21-COMPANY-UI` |

Capabilities that exist in the backend but are not reachable from the console today:

```text
device enrolment / revoke (4 endpoints in apps/api/routes/devices.py) .... frontend usage = 0
tenant / space structure reads (11 endpoints) ............................ frontend usage = 0 (except the space picker)
control-plane operations (8 endpoints) ................................... no console surface (by design)
agent runs (2 endpoints) ................................................. no console surface (by design)
audit_logs (written by services) ......................................... no read API at all
```

Known debt / observations carried into P22 (all non-blocking, historically recorded):

```text
OBS-1  no device-enrolment UX => a real user cannot sign in to the released console
OBS-2  list counts are page-size bound (frozen API exposes no total)
OBS-3  assignment name enrichment uses the first page of reads
OBS-4  assignment picker offers active spaces only
OBS-RELEASE-01  apps/frontend/package-lock.json root version remains 0.1.0
ACC-04/05  Foundation coverage gaps (AuthContext branches · feedback layer)
ACC-06+  Drawer primitive absent · /ready build-artifact observation
P20 reserved  company_employee.delete · company_assignment.delete · company_employee.admin
P20 deferred  employee ↔ user binding (allowed later) · employee SELF access (not supported in V1)
```

Invariant boundaries that must survive P22:

```text
Core → Domain = 0 · Platform ≠ Domain · Frontend Platform ≠ Domain UI · Runtime ≠ Control Plane ·
Event Infrastructure ≠ Production Event Activation · Agent ≠ Worker · Actor ≠ Agent ·
DB Principal ≠ Application User · production_allowlist() = EMPTY
```

---

## 3. Candidate Direction Analysis (A–E)

### A. Company deepening

```text
available without new backend : tenant-switcher affordance · list affordances within the frozen
                                limit/status contract · empty/error/loading polish
needs a new API decision      : employee ↔ user binding (PATCH contract has no user_id) ·
                                Company dashboard aggregates · delete/admin (permissions reserved, no use case)
value      : high for existing Company users; proves nothing about platform reuse
risk       : "Company UI unlimited expansion" — explicitly cautioned against by HD-P22-01 §7
verdict    : RECOMMENDED only as a bounded V1.1 usability slice; API-dependent items DEFERRED
```

### B. Second real Domain (Commercial / Entertainment / other)

```text
value      : the strongest possible proof that UAP is a platform rather than a Company product
cost/risk  : repeats the whole P20 path (schema → authorization → API → UI) and depends on capabilities the
             platform does not yet share (notification / search / workflow absent; event pipeline inactive)
blocking   : no frozen "Domain Module Contract" exists, so an immediate implementation would risk a second,
             divergent pattern
verdict    : DEFER the implementation · RECOMMENDED as a design-only deliverable in P22
```

### C. Platform capability

```text
identity device enrolment / session access  → RECOMMENDED (highest priority; see §4/§5)
    evidence: 4 device endpoints already released; frontend usage 0; OBS-1 blocks real console use
    cost: no migration · no new API · frontend + existing identity contract only
notification                                → DEFER (needs production event activation + handler + delivery +
    idempotency; no real consumer use case exists — Appendix AK.14)
audit UX (activity view)                    → DEFER (audit_logs have no read API; needs a tenant-scoped
    read API + authorization decision)
search · files · workflow · task/job        → REJECT for P22 (no evidence of need; new APIs and
    cross-tenant filtering would be required)
capability registry · platform navigation   → DEFER (low value until a second domain exists)
```

### D. Agent / AI capability

```text
state      : P16 agent runtime + tool registry released; no domain-facing agent action is authorized;
             ToolGate remains the canonical authorization path
assessment : no real Agent↔Domain use case exists; any autonomous domain mutation would require an explicit
             authorization design (Actor/Agent/Worker/DB-principal separation, tenant/space context,
             auditability, failure semantics, idempotency) — none of which is decided
verdict    : DEFER (design-only questions recorded; no credentials exposure, no implementation)
```

### E. Production event activation

```text
current    : allowlist EMPTY · events table 0 rows · handler count 0 · consumer accepted but inactive
requirement: real producer + real handler + idempotency + authorization + tenant/space semantics +
             acceptance evidence + rollback/recovery (HD-P22-01 §5.E and Appendix AK)
assessment : no real downstream consumer exists today => activation would be speculative
verdict    : REJECT for P22 (keep EMPTY) · DEFER until a real consumer use case exists
```

## 4. Priority Ranking (recommendation input)

Scoring: 5 = strongest/favourable · 1 = weakest. "Dependency" = reliance on unfinished work (5 = none).

| Candidate | User value | Platform value | Reuse | Arch risk | Security risk | Tenant risk | Ops cost | Migration cost | Test cost | Dependency | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Device enrolment / session access UX | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 5 | 4 | 5 | RECOMMENDED |
| Company UI V1.1 bounded usability | 4 | 3 | 4 | 4 | 4 | 4 | 4 | 5 | 4 | 5 | RECOMMENDED (bounded) |
| Domain Module Contract (design only) | 2 | 5 | 5 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | RECOMMENDED (design) |
| Second domain implementation | 3 | 5 | 3 | 2 | 3 | 3 | 2 | 2 | 2 | 2 | DEFER |
| Notification capability | 3 | 3 | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 2 | DEFER |
| Audit UX (activity view) | 3 | 3 | 3 | 3 | 4 | 3 | 3 | 3 | 3 | 3 | DEFER |
| Agent ↔ Domain action | 2 | 4 | 3 | 2 | 2 | 2 | 3 | 3 | 2 | 2 | DEFER |
| Search / Files / Workflow / Task | 2 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | REJECT (P22) |
| Production event activation | 1 | 3 | 3 | 3 | 3 | 3 | 2 | 4 | 2 | 1 | REJECT (P22) |

## 5. Recommended P22 Scope (proposal)

```text
P22 CORE — Platform Identity Session Usability (console access)
  1. device enrolment flow in the console using the existing 4 device endpoints
  2. device list / revoke + session access feedback (device-required · 401 recovery · logout)
  3. secure-access UX so a real user can reach the released Company UI end-to-end
  constraints: no new API · no migration · no authorization change · identity contracts reused as-is

P22 SUPPORTING — bounded Company UI V1.1 usability (no backend change)
  4. tenant switcher affordance on top of the existing URL-driven tenant contract
  5. list affordances limited to the frozen filters (limit/status/employee_id/space_id)
  6. usability polish already identified (empty/error/loading states · correlation display)

P22 DESIGN-ONLY — Domain Module Contract v1
  7. freeze the checklist any new domain must satisfy (schema · authorization · API · UI · tests · evidence)
     derived from the Company precedent — no implementation and no second-domain commitment
```

Full in/out/deferred lists and boundary definitions: `P22_SCOPE_CONTRACT.md`.

---

## 6. Open Questions (require Human Decision — never silently assumed)

```text
OQ-1  Is the recommended P22 core (device enrolment / session access UX) authorized as the P22 scope?
      It uses existing endpoints only: no migration, no new API, frontend + identity contract reuse.
OQ-2  If yes: is the enrolment UX platform-level (console-wide) or reachable from the login flow only?
OQ-3  Should the bounded Company UI V1.1 items be part of P22 or deferred to a Company phase?
OQ-4  Is the Domain Module Contract a P22 deliverable, and which domain is the intended first consumer?
OQ-5  Should an audit read API be considered (backend change) — and is an activity view a P22 or later item?
OQ-6  Employee ↔ user binding requires an API contract change; in scope for a future phase, and under which
      permission decision (D-P20D-05 reserved it as "later allowed")?
OQ-7  Notification: is a real downstream consumer expected soon enough to justify the event-activation
      prerequisites (producer · handler · idempotency · authorization · tenant/space semantics · recovery)?
OQ-8  Under which conditions may an Agent perform a domain action (Actor/Agent/Worker separation,
      authorization boundary, auditability, idempotency)?
```

## 7. Findings

```text
F-P22-PREP-01  OBSERVATION  The released console cannot be used end-to-end by a real user because no
               device-enrolment UX exists, although 4 enrolment/revoke endpoints are already released
               (frontend usage = 0). Elevated to the recommended P22 core (OQ-1).
F-P22-PREP-02  OBSERVATION  The platform has no frozen Domain Module Contract, so a second domain would
               risk a divergent pattern; recommended as a P22 design-only deliverable (OQ-4).
F-P22-PREP-03  OBSERVATION  audit_logs are written but have no read surface; an activity/audit view
               requires a new tenant-scoped read API decision (OQ-5).
F-P22-PREP-04  OBSERVATION  Notification remains the only obvious real consumer of the accepted event
               infrastructure, yet no downstream use case exists; activation stays REJECT for P22 (OQ-7).
F-P22-PREP-05  OBSERVATION  The Company API contract has no user-binding field, so employee↔user binding
               cannot be delivered without an API decision (OQ-6).
historical findings (F-P21-*, ACC-02/03, ACC-04/05, ACC-06+, OBS-1..4, OBS-RELEASE-01) — retained unchanged;
               none is blocking for P22 PREP.
blocking findings = 0
```

## 8. Boundaries Honoured in This Round

```text
source changes = 0 · database changes = 0 (no DDL/DML/seed) · migration = 0 · API change = 0 ·
frontend change = 0 · dependency change = 0 · event activation = 0 · commit/tag/push = 0
git history and historical dirty work: untouched (no clean/reset/restore/stash/bulk add)
```

## 9. Next Step

```text
NEXT = P22 PREP GATE (independent human decision)
  · ratify or amend the scope proposal (IN-SCOPE / OUT-OF-SCOPE / DEFERRED)
  · answer OQ-1 … OQ-8
  · then, and only then, a separate P22 Implementation Authorization may be requested
HARD STOP = ACTIVE (no implementation is authorized by this report)
```
