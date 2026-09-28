"""P12 — canonical index delivery: 12 FK reverse-lookup + 7 P10 event/audit indexes.

Decision authority: `D-P12-01..15` + `P12_IMPLEMENTATION_CONTRACT.md` §3.1/§3.2
(`MEASURE-1` = APPROVED 2026-09-25; `GUARD-1` = APPROVED 2026-09-25).

Part B CREATE set = exactly 19 indexes:

  FK reverse-lookup (12) — adjudicated per `D-P12-13`
      (FK GAP → query evidence → CREATE); partial indexes do NOT serve FK checks
      (`D-P12-05`): ix_texec_tool exists because `uq_tool_exec_idem` is partial.
  P10 carriers (7, `D-P12-08`) — created on the partition PARENT tables; PG
      propagates to child partitions automatically. No ON ONLY, no ATTACH
      PARTITION, no child-local indexes, no partition/PK/retention changes.

Hard bans honoured here (`D-P12-14`): `ix_aimodels_capability` is NOT created
(DO NOT IMPLEMENT), nor any JSONB capability index. No existing index is
dropped / renamed / merged; no UNIQUE or partial predicate is altered.

No CONCURRENTLY (Alembic runs inside a transaction — `D-P12-10`). No seed,
no trigger, no table — P12 delivers indexes only.

upgrade: FK indexes → Event indexes → Audit indexes
downgrade: strict reverse DROP INDEX IF EXISTS — zero residue.
"""

import sqlalchemy as sa
from alembic import op

revision = "0015_p12_indexes"
down_revision = "0014_p11_triggers"
branch_labels = None
depends_on = None

# --------------------------------------------------------------------------- #
# Part B canonical CREATE set (name, table, columns, predicate)
# --------------------------------------------------------------------------- #
_FK_INDEXES = (
    ("ix_ap_permission", "agent_permissions", "(permission_id)", None),
    ("ix_ap_tool", "agent_permissions", "(tool_id)", None),
    ("ix_ap_version", "agent_permissions", "(version_id)", None),
    ("ix_agents_current_version", "agents", "(current_version_id)", None),
    ("ix_agents_default_route", "agents", "(default_route_id)", None),
    ("ix_airoutes_primary_model", "ai_routes", "(primary_model_id)", None),
    ("ix_texec_tool", "tool_executions", "(tool_id)", None),
    ("ix_texec_tool_version", "tool_executions", "(tool_version_id)", None),
    ("ix_tperm_permission", "tool_permissions", "(permission_id)", None),
    ("ix_tperm_version", "tool_permissions", "(version_id)", None),
)

# partitioned tables: created on the parent; PG pushes down to child partitions
_PARTITIONED_FK_INDEXES = (
    ("ix_airl_provider", "ai_request_logs", "(provider_id)", None),
    ("ix_airl_model", "ai_request_logs", "(model_id)", None),
)

_EVENT_INDEXES = (
    ("ix_events_dispatch", "events", "(status, next_attempt_at)",
     "WHERE status IN ('pending', 'claimed')"),
    ("ix_events_tenant_type_time", "events",
     "(tenant_id, event_type, occurred_at DESC)", None),
)

_AUDIT_INDEXES = (
    ("ix_audit_tenant_time", "audit_logs", "(tenant_id, occurred_at DESC)", None),
    ("ix_audit_actor_time", "audit_logs", "(actor_id, occurred_at DESC)", None),
    ("ix_audit_resource", "audit_logs",
     "(resource_type, resource_id, occurred_at DESC)", None),
    ("ix_audit_correlation", "audit_logs", "(correlation_id)", None),
    ("ix_audit_risk", "audit_logs", "(risk_level, occurred_at)",
     "WHERE risk_level IN ('HIGH', 'CRITICAL')"),
)


def upgrade() -> None:
    for name, table, columns, predicate in _FK_INDEXES:
        op.execute(sa.text(
            f"CREATE INDEX {name} ON {table} {columns}" + (f" {predicate}" if predicate else "")
        ))
    for name, table, columns, predicate in _PARTITIONED_FK_INDEXES + _EVENT_INDEXES:
        op.execute(sa.text(
            f"CREATE INDEX {name} ON {table} {columns}" + (f" {predicate}" if predicate else "")
        ))
    for name, table, columns, predicate in _AUDIT_INDEXES:
        op.execute(sa.text(
            f"CREATE INDEX {name} ON {table} {columns}" + (f" {predicate}" if predicate else "")
        ))


def downgrade() -> None:
    # strict reverse: audit → event → partitioned FK → plain FK
    for name, table, _columns, _predicate in reversed(_AUDIT_INDEXES):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
    for name, table, _columns, _predicate in reversed(
            tuple(_PARTITIONED_FK_INDEXES) + tuple(_EVENT_INDEXES)):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
    for name, _table, _columns, _predicate in reversed(_FK_INDEXES):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {name}"))
