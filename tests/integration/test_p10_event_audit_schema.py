"""P10 Event / Audit (0013_p10_event_audit) — schema, constraints, partition,
immutability, outbox substrate, retention shape, security and migration.

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).

Covers the frozen P10 decisions implemented by ``0013``:

  * D-P10-01 = FROZEN  outbox status columns built in one pass on ``events``
                       (the table **is** the outbox; no third table, no later ALTER)
  * D-P10-02 = FROZEN  Domain Event ID = UUIDv7 (application-generated)
  * D-P10-05 = FROZEN  Authorization Audit five semantic dimensions ->
                       structured ``metadata`` (no new first-class column)
  * D-P10-09 = FROZEN  RANGE (occurred_at) monthly partition; current month only;
                       **no DEFAULT partition**
  * D-P10-11 = FROZEN  ``tg_audit_immutable`` is **P10-owned**: audit immutability
                       exists at P10 and does not depend on P11
  * D-P10-12 = FROZEN  no events <-> audit_logs linkage column
  * D-P10-13 = FROZEN  GRANT / role design = OPEN-P10-1 (DEFER) -> zero GRANT
  * D-P10-15 = FROZEN  no RLS
  * D-P12-08 = FROZEN  the 7 ix_events_* / ix_audit_* indexes belong to P12
  * D-P11-01 = FROZEN  G/H/I/J belong to P11 -> absent here

Out of scope (must NOT exist): G/H/I/J triggers, any P12 index on the two tables,
RLS, a DEFAULT partition, a delivery worker, ``agent_runs`` /
``agent_run_steps``, ``event_types`` registry, partition automation, seed rows.
"""

from __future__ import annotations

import pathlib
import re
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.integration.alembic_testkit import (
    BASE_DSN,
    ROOT,
    current_revision,
    database_reachable,
    downgrade,
    make_config,
    reset_test_database,
    upgrade,
)

pytestmark = pytest.mark.integration

if not database_reachable():
    pytest.skip(
        "PostgreSQL is not reachable; start it with `docker compose up -d postgres`",
        allow_module_level=True,
    )

REVISION = "0013_p10_event_audit"
PREVIOUS_REVISION = "0012_authz_enforcement"
HEAD_REVISION = "0015_p12_indexes"  # head 随链推进（MIG1 的单头检查）
MIGRATION_FILE = ROOT / "migrations_alembic" / "versions" / f"{REVISION}.py"
PLATFORM_PRECISION = 3

EVENTS = "events"
AUDIT = "audit_logs"
PARENTS = (EVENTS, AUDIT)
FAMILIES = ("events_", "audit_logs_")
PARTITION_PREFIXES = ("ai_request_logs_", "events_", "audit_logs_")

EVENTS_COLUMNS = {
    "id", "occurred_at", "event_type", "schema_version", "tenant_id", "space_id",
    "actor_type", "actor_id", "subject_type", "subject_id", "payload",
    "correlation_id", "causation_id", "status", "worker_id", "claimed_at",
    "lease_expires_at", "attempts", "next_attempt_at", "last_error",
    "delivered_at", "created_at",
}
AUDIT_COLUMNS = {
    "id", "occurred_at", "tenant_id", "space_id", "actor_type", "actor_id",
    "actor_ip", "actor_user_agent", "action", "resource_type", "resource_id",
    "classification", "result", "risk_level", "reason", "correlation_id",
    "request_id", "metadata", "created_at",
}
# D-P10-01 — the eight outbox state columns, all present in one pass.
OUTBOX_STATE_COLUMNS = {
    "status", "worker_id", "claimed_at", "lease_expires_at", "attempts",
    "next_attempt_at", "last_error", "delivered_at",
}
EVENTS_TIMESTAMPS = {
    "occurred_at", "claimed_at", "lease_expires_at", "next_attempt_at",
    "delivered_at", "created_at",
}
AUDIT_TIMESTAMPS = {"occurred_at", "created_at"}

CK_EVENTS = {"ck_events_event_type", "ck_events_status", "ck_events_attempts"}
CK_AUDIT = {"ck_audit_logs_result", "ck_audit_logs_risk_level",
            "ck_audit_logs_classification"}
IMMUTABLE_TRIGGER = "tg_audit_immutable"
IMMUTABLE_FUNCTION = "enforce_audit_logs_immutable"
P12_INDEXES = (
    "ix_events_dispatch", "ix_events_tenant_type_time",
    "ix_audit_tenant_time", "ix_audit_actor_time", "ix_audit_resource",
    "ix_audit_correlation", "ix_audit_risk",
)
P11_TRIGGERS = (
    "tg_acl_subject_exists", "tg_acl_user_hard_delete",
    "tg_acl_role_delete_block", "tg_agent_acl_expire",
)


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #
@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    yield
    reset_test_database()


@pytest.fixture()
def empty_db():
    reset_test_database()
    yield
    reset_test_database()


def _engine() -> sa.Engine:
    return sa.create_engine(BASE_DSN)


def _rows(sql: str, **params):
    engine = _engine()
    try:
        with engine.connect() as conn:
            return [tuple(r) for r in conn.execute(sa.text(sql), params)]
    finally:
        engine.dispose()


def _scalar(sql: str, **params):
    engine = _engine()
    try:
        with engine.connect() as conn:
            return conn.execute(sa.text(sql), params).scalar()
    finally:
        engine.dispose()


def _exec(sql: str, **params) -> int:
    engine = _engine()
    try:
        with engine.begin() as conn:
            return conn.execute(sa.text(sql), params).rowcount
    finally:
        engine.dispose()


def _child_partitions(parent: str) -> list[str]:
    return [r[0] for r in _rows(
        "SELECT c.relname FROM pg_inherits i "
        "JOIN pg_class c ON c.oid = i.inhrelid "
        "JOIN pg_class p ON p.oid = i.inhparent "
        "WHERE p.relname = :p ORDER BY c.relname", p=parent
    )]


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m")


AUDIT_INSERT = (
    "INSERT INTO audit_logs "
    "(id, occurred_at, actor_type, action, result, risk_level, metadata, created_at) "
    "VALUES (gen_random_uuid(), now(), 'user', 'authorization.check', "
    "'success', 'LOW', '{}'::jsonb, now())"
)
EVENT_INSERT = (
    "INSERT INTO events "
    "(id, occurred_at, event_type, schema_version, payload, status, attempts) "
    "VALUES (gen_random_uuid(), now(), 'account.created', 1, '{}'::jsonb, 'pending', 0)"
)


# --------------------------------------------------------------------------- #
# SC — schema
# --------------------------------------------------------------------------- #
def test_sc1_both_tables_are_partitioned_parents(db) -> None:
    """SC1 — both P10 tables are RANGE-partitioned parents on ``occurred_at``."""
    rows = dict(_rows(
        "SELECT c.relname, c.relkind FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname='public' AND c.relname = ANY(:t)", t=list(PARENTS)
    ))
    assert rows == {EVENTS: "p", AUDIT: "p"}, rows
    for parent in PARENTS:
        key = _scalar(
            "SELECT pg_get_partkeydef(c.oid) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='public' AND c.relname = :t", t=parent
        )
        assert key == "RANGE (occurred_at)", (parent, key)


def test_sc2_column_sets_are_exactly_the_frozen_shape(db) -> None:
    """SC2 — events 22 columns / audit_logs 19 columns, exact sets (no extras)."""
    for table, expected in ((EVENTS, EVENTS_COLUMNS), (AUDIT, AUDIT_COLUMNS)):
        cols = {r[0] for r in _rows(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t", t=table
        )}
        assert cols == expected, (table, sorted(cols ^ expected))
        assert _scalar(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t", t=table
        ) == len(expected)


def test_sc3_outbox_state_columns_are_built_in_one_pass(db) -> None:
    """SC3 — D-P10-01: all eight outbox state columns exist on ``events``."""
    cols = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t", t=EVENTS
    )}
    assert OUTBOX_STATE_COLUMNS <= cols, sorted(OUTBOX_STATE_COLUMNS - cols)
    # The table *is* the outbox: no separate carrier exists.
    assert _scalar(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name ~ '(outbox|event_outbox)'"
    ) == 0


def test_sc4_audit_is_append_only_in_shape(db) -> None:
    """SC4 — no ``updated_at`` / ``deleted_at``; no linkage column (D-P10-12)."""
    cols = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t", t=AUDIT
    )}
    assert "updated_at" not in cols and "deleted_at" not in cols
    event_cols = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t", t=EVENTS
    )}
    assert not (cols & event_cols - {"id", "occurred_at", "tenant_id", "space_id",
                                     "actor_type", "actor_id", "correlation_id",
                                     "created_at"}), "unexpected linkage column"
    for table in PARENTS:
        assert _scalar(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t "
            "AND column_name IN ('event_id','audit_id','log_id')", t=table
        ) == 0


def test_sc5_timestamp_columns_are_timestamptz_3(db) -> None:
    """SC5 — every P10 timestamp column is ``timestamptz(3)`` (CORE §10)."""
    expected = {("events", c) for c in EVENTS_TIMESTAMPS} | \
               {("audit_logs", c) for c in AUDIT_TIMESTAMPS}
    rows = _rows(
        "SELECT table_name, column_name, datetime_precision "
        "FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name = ANY(:t) "
        "AND data_type = 'timestamp with time zone'", t=list(PARENTS)
    )
    assert {(r[0], r[1]) for r in rows} == expected, rows
    assert all(r[2] == PLATFORM_PRECISION for r in rows), rows


def test_sc6_no_unique_constraint_and_no_foreign_key(db) -> None:
    """SC6 — UQ = 0 and FK = 0 on both tables (fact-log shape)."""
    rows = _rows(
        "SELECT conrelid::regclass::text, contype, count(*) FROM pg_constraint "
        "WHERE conrelid::regclass::text = ANY(:t) GROUP BY 1, 2 ORDER BY 1, 2",
        t=list(PARENTS)
    )
    kinds = {(r[0], r[1]): r[2] for r in rows}
    assert kinds.get((EVENTS, "p")) == 1 and kinds.get((AUDIT, "p")) == 1
    assert not [k for k in kinds if k[1] in ("u", "f")], kinds
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='f' "
        "AND conrelid::regclass::text = ANY(:t)", t=list(PARENTS)
    ) == 0
    # Only the PK-backed unique index may exist (the partition key is in the PK).
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname='public' "
        "AND tablename = ANY(:t) AND indexdef LIKE 'CREATE UNIQUE%' "
        "AND indexname NOT LIKE '%\\_pkey'", t=list(PARENTS)
    ) == 0


def test_sc7_primary_key_is_id_plus_partition_key(db) -> None:
    """SC7 — PK = (id, occurred_at): the partition key must be in the PK."""
    for parent in PARENTS:
        cols = [r[0] for r in _rows(
            "SELECT a.attname FROM pg_index i "
            "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = CAST(:t AS regclass) AND i.indisprimary ORDER BY a.attnum",
            t=parent
        )]
        assert cols == ["id", "occurred_at"], (parent, cols)


def test_sc8_uuidv7_is_the_application_identity(db) -> None:
    """SC8 — D-P10-02: id is ``uuid`` with **no** server default (app generates v7)."""
    for table in PARENTS:
        info = _rows(
            "SELECT data_type, column_default FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND column_name='id'",
            t=table
        )
        assert info and info[0][0] == "uuid", (table, info)
        assert info[0][1] is None, (table, info)
    # The canonical generator produces version 7 (application side).
    import sys
    sys.path.insert(0, str(ROOT))
    from core.audit.interfaces import new_event_id

    value = new_event_id()
    assert value[14] == "7", value
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='uap_uuid_v7'") == 1


# --------------------------------------------------------------------------- #
# CK — constraints
# --------------------------------------------------------------------------- #
def test_ck1_check_constraint_set_is_exact(db) -> None:
    """CK1 — exactly 3 CHECKs per table, with the frozen names."""
    rows = _rows(
        "SELECT conrelid::regclass::text, conname FROM pg_constraint "
        "WHERE contype='c' AND conrelid::regclass::text = ANY(:t)", t=list(PARENTS)
    )
    got = {(r[0], r[1]) for r in rows}
    assert got == {("events", n) for n in CK_EVENTS} | {("audit_logs", n) for n in CK_AUDIT}


@pytest.mark.parametrize("sql", [
    "INSERT INTO events (id,occurred_at,event_type,schema_version,payload,status) "
    "VALUES (gen_random_uuid(),now(),'BadType',1,'{}'::jsonb,'pending')",
    "INSERT INTO events (id,occurred_at,event_type,schema_version,payload,status) "
    "VALUES (gen_random_uuid(),now(),'singleword',1,'{}'::jsonb,'pending')",
    "INSERT INTO events (id,occurred_at,event_type,schema_version,payload,status) "
    "VALUES (gen_random_uuid(),now(),'a.b',1,'{}'::jsonb,'bogus')",
    "INSERT INTO events (id,occurred_at,event_type,schema_version,payload,status,attempts) "
    "VALUES (gen_random_uuid(),now(),'a.b',1,'{}'::jsonb,'pending',101)",
    "INSERT INTO audit_logs (id,occurred_at,actor_type,action,result,risk_level,metadata,created_at) "
    "VALUES (gen_random_uuid(),now(),'user','x','bogus','LOW','{}'::jsonb,now())",
    "INSERT INTO audit_logs "
    "(id,occurred_at,actor_type,action,classification,result,risk_level,metadata,created_at) "
    "VALUES (gen_random_uuid(),now(),'user','x','SECRET','success','LOW','{}'::jsonb,now())",
])
def test_ck2_negative_inserts_are_rejected(db, sql) -> None:
    """CK2 — non-canonical ``event_type`` / ``status`` / ``attempts`` / ``result`` /
    ``classification`` fail."""
    with pytest.raises(sa.exc.DBAPIError):
        _exec(sql)


def test_ck3_positive_inserts_are_accepted(db) -> None:
    """CK3 — canonical values are accepted; nullable ``classification`` stays NULL-able."""
    _exec(EVENT_INSERT)
    _exec(AUDIT_INSERT)
    assert _scalar("SELECT count(*) FROM events") == 1
    assert _scalar("SELECT count(*) FROM audit_logs") == 1
    assert _scalar("SELECT count(*) FROM audit_logs WHERE classification IS NULL") == 1
    _exec("INSERT INTO events (id,occurred_at,event_type,schema_version,payload,status,attempts) "
          "VALUES (gen_random_uuid(),now(),'tool.execution.completed',2,'{}'::jsonb,'dead',100)")
    assert _scalar("SELECT count(*) FROM events WHERE attempts=100") == 1


def test_ck4_not_null_shape(db) -> None:
    """CK4 — the frozen NOT NULL sets (8 per table)."""
    nn_events = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name='events' AND is_nullable='NO'")}
    nn_audit = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name='audit_logs' AND is_nullable='NO'")}
    assert nn_events == {"id", "occurred_at", "event_type", "schema_version", "payload",
                         "status", "attempts", "created_at"}, sorted(nn_events)
    assert nn_audit == {"id", "occurred_at", "actor_type", "action", "result",
                        "risk_level", "metadata", "created_at"}, sorted(nn_audit)


# --------------------------------------------------------------------------- #
# PT — partition
# --------------------------------------------------------------------------- #
def test_pt1_exactly_one_current_month_partition_per_parent(db) -> None:
    """PT1 — current-month child only; the month suffix is never hard-coded."""
    month = _current_month()
    for parent in PARENTS:
        kids = _child_partitions(parent)
        assert kids == [f"{parent}_{month}"], (parent, kids)


def test_pt2_no_default_partition(db) -> None:
    """PT2 — D-P10-09: a DEFAULT partition must not exist (out-of-range fails)."""
    for parent in PARENTS:
        assert _scalar(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname = :t||'_default'", t=parent
        ) == 0
    with pytest.raises(sa.exc.DBAPIError):
        _exec("INSERT INTO events (id,occurred_at,event_type,schema_version,payload,status) "
              "VALUES (gen_random_uuid(), '1999-01-01T00:00:00+00', 'a.b',1,'{}'::jsonb,'pending')")


def test_pt3_rows_route_into_the_child_partition(db) -> None:
    """PT3 — inserts land in the current-month child, not the parent."""
    _exec(EVENT_INSERT)
    _exec(AUDIT_INSERT)
    month = _current_month()
    assert _scalar(f"SELECT count(*) FROM events_{month}") == 1
    assert _scalar(f"SELECT count(*) FROM audit_logs_{month}") == 1
    assert _scalar("SELECT count(*) FROM events") == 1
    # A whole-month drop is the retention mechanism => partitions are the unit.
    assert _scalar(
        "SELECT count(*) FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid "
        "WHERE c.relname = ANY(:n)", n=[f"events_{month}", f"audit_logs_{month}"]
    ) == 2


def test_pt4_partition_creation_is_manual(db) -> None:
    """PT4 — D-P10-10: no scheduler / extension / automation was installed."""
    assert _scalar(
        "SELECT count(*) FROM pg_extension WHERE extname IN ('pg_partman','pg_cron')"
    ) == 0
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    # Drop the module docstring (the first two triple quotes delimit it) and all
    # comments: a rule *stated* in prose is not a violation of it.
    code = src.split('"""', 2)[2] if src.count('"""') >= 2 else src
    code = "\n".join(ln for ln in code.split("\n") if not ln.strip().startswith("#"))
    for token in ("CREATE EXTENSION", "pg_partman", "pg_cron", "cron.schedule",
                  "scheduler", "runbook_exec"):
        assert token not in code, token


# --------------------------------------------------------------------------- #
# IMM — audit immutability (P10-owned)
# --------------------------------------------------------------------------- #
def test_imm1_update_and_delete_are_rejected(db) -> None:
    """IMM1 — D-P10-11: BEFORE UPDATE / BEFORE DELETE raise."""
    _exec(AUDIT_INSERT)
    for sql in ("UPDATE audit_logs SET reason='x'", "DELETE FROM audit_logs"):
        with pytest.raises(sa.exc.DBAPIError) as exc:
            _exec(sql)
        assert "append-only" in str(exc.value)
    assert _scalar("SELECT count(*) FROM audit_logs") == 1, "the row must survive"


def test_imm2_trigger_and_function_are_p10_owned(db) -> None:
    """IMM2 — exactly one trigger on audit_logs, none on events, one function."""
    triggers = _rows(
        "SELECT tgrelid::regclass::text, tgname FROM pg_trigger "
        "WHERE NOT tgisinternal AND tgrelid::regclass::text = ANY(:t) "
        "AND tgparentid = 0 ORDER BY 1, 2", t=list(PARENTS)
    )
    assert triggers == [(AUDIT, IMMUTABLE_TRIGGER)], triggers
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname=:n",
                   n=IMMUTABLE_FUNCTION) == 1
    timing = _rows(
        "SELECT tgtype FROM pg_trigger WHERE tgname=:n AND tgparentid=0",
        n=IMMUTABLE_TRIGGER
    )
    raw = int(timing[0][0])
    assert raw & 2 and raw & 16 and raw & 8, f"expected BEFORE UPDATE OR DELETE, got {raw}"


def test_imm3_function_is_security_invoker_and_search_path_free(db) -> None:
    """IMM3 — SECURITY INVOKER; the body references no object (no search_path risk)."""
    name, secdef, body = _rows(
        "SELECT proname, prosecdef, pg_get_functiondef(oid) FROM pg_proc WHERE proname=:n",
        n=IMMUTABLE_FUNCTION
    )[0]
    assert name == IMMUTABLE_FUNCTION
    assert secdef is False, "SECURITY DEFINER is forbidden"
    assert "plpgsql" in body
    assert "RAISE EXCEPTION" in body
    assert "search_path" not in body
    assert not re.search(r"\bFROM\b", body, re.I), body
    assert not re.search(r"\b(INSERT|UPDATE|DELETE)\b", body, re.I), body


def test_imm4_no_other_trigger_was_added_by_p10(db) -> None:
    """IMM4 — the P10 revision introduces no trigger beyond the immutability one."""
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert len(re.findall(r"CREATE TRIGGER", src)) == 1
    for trigger in P11_TRIGGERS:
        assert trigger not in src, f"{trigger} belongs to P11"


# --------------------------------------------------------------------------- #
# OBX — outbox state machine (application-level CAS)
# --------------------------------------------------------------------------- #
def _seed_event() -> None:
    _exec(EVENT_INSERT)


def test_obx1_claim_is_cas_single_winner(db) -> None:
    """OBX1 — the ``status`` predicate is the optimistic lock: one winner only."""
    _seed_event()
    claim = ("UPDATE events SET status='claimed', worker_id=:w, claimed_at=now(), "
             "lease_expires_at=now()+interval '60 seconds' "
             "WHERE status='pending' AND (next_attempt_at IS NULL OR next_attempt_at <= now())")
    assert _exec(claim, w="w1") == 1
    assert _exec(claim, w="w2") == 0, "a second worker must not claim the same row"


def test_obx2_state_updates_are_worker_scoped(db) -> None:
    """OBX2 — success/retry carry a ``worker_id`` condition."""
    _seed_event()
    _exec("UPDATE events SET status='claimed', worker_id='w1', claimed_at=now(), "
          "lease_expires_at=now()+interval '60 seconds' WHERE status='pending'")
    done = ("UPDATE events SET status='delivered', delivered_at=now(), lease_expires_at=NULL "
            "WHERE status='claimed' AND worker_id=:w")
    assert _exec(done, w="w2") == 0, "a non-owner must not complete the delivery"
    assert _exec(done, w="w1") == 1


def test_obx3_retry_sets_backoff_and_reaper_reclaims_expired_lease(db) -> None:
    """OBX3 — retry backoff + lease reap are expressible on the frozen columns."""
    _seed_event()
    _exec("UPDATE events SET status='claimed', worker_id='w1', claimed_at=now(), "
          "lease_expires_at=now() - interval '1 second' WHERE status='pending'")
    # Reaper: an expired lease goes back to pending (at-least-once, never exactly-once).
    assert _exec(
        "UPDATE events SET status='pending', next_attempt_at=now(), lease_expires_at=NULL, "
        "last_error=COALESCE(last_error,'')||'lease_expired:' "
        "WHERE status='claimed' AND lease_expires_at < now()"
    ) == 1
    assert _scalar("SELECT status FROM events") == "pending"
    # Retry: attempts increments and a backoff deadline is written.
    assert _exec("UPDATE events SET status='pending', attempts=attempts+1, "
                 "next_attempt_at=now()+interval '1 second', last_error='boom' WHERE status='pending'") == 1
    row = _rows("SELECT attempts, next_attempt_at IS NOT NULL, last_error FROM events")[0]
    assert row == (1, True, "boom"), row
    # Not-yet-due rows are not claimable.
    assert _exec("UPDATE events SET status='claimed' WHERE status='pending' "
                 "AND next_attempt_at <= now()") == 0


def test_obx4_max_attempts_marks_dead(db) -> None:
    """OBX4 — ``attempts >= 8`` is the dead-letter threshold."""
    _seed_event()
    _exec("UPDATE events SET attempts=8, status='claimed', worker_id='w1'")
    assert _exec("UPDATE events SET status='dead', lease_expires_at=NULL, "
                 "last_error='max_attempts_exceeded' "
                 "WHERE status='claimed' AND worker_id='w1' AND attempts >= 8") == 1
    assert _scalar("SELECT status FROM events") == "dead"
    assert _scalar("SELECT attempts FROM events") == 8


def test_obx5_no_trigger_on_events(db) -> None:
    """OBX5 — claim is application-level CAS, never a DB trigger."""
    assert _scalar(
        "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid::regclass::text = 'events'"
    ) == 0


# --------------------------------------------------------------------------- #
# RET — retention shape
# --------------------------------------------------------------------------- #
def test_ret1_retention_is_partition_drop_not_row_delete(db) -> None:
    """RET1 — events 30d / audit 365d are whole-partition drops; audit denies DELETE."""
    for parent in PARENTS:
        part = _scalar(
            "SELECT pg_get_partkeydef(c.oid) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='public' AND c.relname = :t", t=parent
        )
        assert part == "RANGE (occurred_at)", (parent, part)
    _exec(AUDIT_INSERT)
    with pytest.raises(sa.exc.DBAPIError):
        _exec("DELETE FROM audit_logs")


def test_ret2_no_soft_delete_books_on_p10_tables(db) -> None:
    """RET2 — no ``deleted_at``: retention is never a row-level soft delete."""
    for table in PARENTS:
        assert _scalar(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t "
            "AND column_name IN ('deleted_at','archived_at','purged_at')", t=table
        ) == 0


# --------------------------------------------------------------------------- #
# SEC — security surface
# --------------------------------------------------------------------------- #
def test_sec1_no_rls_and_no_default_partition(db) -> None:
    """SEC1 — D-P10-15 / D-P10-09: neither table has RLS enabled."""
    for table in PARENTS:
        assert _scalar(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname=:t AND c.relrowsecurity", t=table
        ) == 0


def test_sec2_migration_performs_no_grant(db) -> None:
    """SEC2 — D-P10-13: OPEN-P10-1 stays DEFER; the migration grants nothing."""
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    code_lines = [ln for ln in src.split("\n")
                  if not ln.strip().startswith("#") and '"""' not in ln]
    assert not [ln for ln in code_lines if re.match(r"\s*GRANT\b", ln)], "GRANT found"


def test_sec3_no_seed_rows_are_written(db) -> None:
    """SEC3 — P00–P12 write no seed data (first principal arrives via P13)."""
    for table in PARENTS:
        assert _scalar(f"SELECT count(*) FROM {table}") == 0
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert "INSERT INTO" not in src, "the P10 migration must not seed"


def test_sec4_formal_database_untouched(db) -> None:
    """SEC4 — the suite never migrates the formal ``uap`` database."""
    try:
        engine = sa.create_engine("postgresql+psycopg://uap:uap@localhost:5432/uap")
    except Exception:  # pragma: no cover - defensive
        pytest.skip("formal uap database unreachable")
    try:
        with engine.connect() as conn:
            count = conn.execute(sa.text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog','information_schema')"
            )).scalar()
        assert count == 0, f"formal uap must stay empty, found {count}"
    finally:
        engine.dispose()


# --------------------------------------------------------------------------- #
# BND — P10 / P11 and P10 / P12 boundaries
# --------------------------------------------------------------------------- #
def test_bnd1_p10_p11_trigger_ownership_disjoint(db) -> None:
    """BND1 — P10/P11 trigger 所有权不相交（head 无关不变式）：
    P10 表（events/audit_logs）上无 P11 触发器；4 张 P11 目标表上无 P10 触发器。
    （历史形态「G/H/I/J must not exist yet」随 `D-P11-01` 实施翻转。）"""
    rows = _rows(
        "SELECT tgname, tgrelid::regclass::text FROM pg_trigger "
        "WHERE NOT tgisinternal AND tgparentid = 0")
    p11_on_p10 = [n for n, t in rows
                  if t in ("events", "audit_logs") and n in set(P11_TRIGGERS)]
    p10_on_p11 = [n for n, t in rows
                  if t in ("resource_permissions", "users", "roles", "agents")
                  and n == "tg_audit_immutable"]
    assert not p11_on_p10 and not p10_on_p11, (p11_on_p10, p10_on_p11)


def test_bnd2_p12_indexes_now_delivered_on_p10_tables(db) -> None:
    """BND2 — D-P12-08：七条查询索引 = P12-owned（0013 未建）；`D-P12-01` 实施后
    （0015）此断言翻转为**恰好在 P10 表上交付**，且无其余非 PK 索引。"""
    names = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
        "AND tablename = ANY(:t)", t=list(PARENTS)
    )}
    non_pk = {n for n in names if not n.endswith("_pkey")}
    assert non_pk == set(P12_INDEXES), sorted(non_pk)
    assert names & set(P12_INDEXES) == set(P12_INDEXES)


def test_bnd3_no_runtime_or_worker_objects(db) -> None:
    """BND3 — Runtime / AI Gateway surfaces are out of P10 scope."""
    names = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")}
    for absent in ("agent_runs", "agent_run_steps", "event_types", "outbox",
                   "approval_requests"):
        assert absent not in names, absent


# --------------------------------------------------------------------------- #
# MIG — migration integrity
# --------------------------------------------------------------------------- #
def test_mig1_revision_identity_and_single_head() -> None:
    """MIG1 — filename == revision, <= 32 chars, single head, correct parent."""
    assert MIGRATION_FILE.exists()
    assert MIGRATION_FILE.stem == REVISION
    assert len(REVISION) <= 32, len(REVISION)
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert f'revision = "{REVISION}"' in src
    assert f'down_revision = "{PREVIOUS_REVISION}"' in src
    assert "branch_labels = None" in src and "depends_on = None" in src
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert script.get_heads() == [HEAD_REVISION]
    assert MIGRATION_FILE == ROOT / "migrations_alembic" / "versions" / f"{REVISION}.py"


def test_mig2_upgrade_downgrade_roundtrip_zero_residue(empty_db) -> None:
    """MIG2 — downgrade removes every P10 object; a fresh upgrade restores it."""
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, PREVIOUS_REVISION)
    before = _scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
    upgrade(cfg, REVISION)   # 钉在本套件的 revision（head 已推进到 0014）
    assert current_revision() == REVISION
    upgrade(cfg, REVISION)   # idempotent

    downgrade(cfg, PREVIOUS_REVISION)
    assert current_revision() == PREVIOUS_REVISION
    after = _scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
    assert after == before, (before, after)
    for fragment in ("events", "audit_logs"):
        assert _scalar(
            "SELECT count(*) FROM pg_class WHERE relname = :t OR relname LIKE :f",
            t=fragment, f=fragment + "\\_%"
        ) == 0, fragment
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname=:n",
                   n=IMMUTABLE_FUNCTION) == 0
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE tgname=:n",
                   n=IMMUTABLE_TRIGGER) == 0
    # Pre-existing objects survive.
    assert _scalar("SELECT count(*) FROM pg_class WHERE relname='ai_request_logs'") == 1
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='uap_uuid_v7'") == 1
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1

    upgrade(cfg, REVISION)
    assert current_revision() == REVISION
    assert _scalar("SELECT count(*) FROM information_schema.tables "
                   "WHERE table_schema='public'") == after + 4


def test_mig3_unrelated_objects_are_untouched(empty_db) -> None:
    """MIG3 — 0013 adds no table beyond its own; P09 / P08 shapes are intact."""
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    names = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")}
    assert {"agents", "agent_versions", "agent_permissions", "tool_executions",
            "ai_providers", "ai_models", "ai_routes", "ai_policies",
            "ai_request_logs"} <= names
    # P09 / P08 column shapes are unchanged (spot-check two load-bearing columns).
    assert _scalar("SELECT count(*) FROM information_schema.columns "
                   "WHERE table_schema='public' AND table_name='agent_permissions' "
                   "AND column_name='resource_scope'") == 1
    assert _scalar("SELECT count(*) FROM information_schema.columns "
                   "WHERE table_schema='public' AND table_name='tool_executions' "
                   "AND column_name='status'") == 1
    # The 0013 revision creates exactly two parents and two children.
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert len(re.findall(r"op\.create_table\(", src)) == 2
    # 两个父表的子分区由同一 f-string 在循环内创建 ⇒ 源码中只出现一次模板
    assert src.count("PARTITION OF") == 1
    assert "for parent in (_EVENTS, _AUDIT):" in src


def test_mig4_p10_owns_no_index_at_migration_level() -> None:
    """MIG4 — the migration source contains no index DDL at all."""
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert not re.search(r"CREATE\s+(?:UNIQUE\s+)?INDEX", src, re.I)
    assert "create_index" not in src
