"""B1-5 Tool Registry — schema, delete-rules, constraints, immutability, migration.

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).

Covers the frozen B1-5 decisions (canonical TEST_MATRIX = 39):
  * D-B15-01 = A  B1-5 = P07 Tool
  * D-B15-02 = A  tools.tenant_id NULL -> tenants.id ON DELETE RESTRICT
                  (NULL = platform-level tool)
  * D-B15-03 = A  immutable trigger is named ``tg_version_immutable``
                  (shared with P09 ``agent_versions``)
  * D-B15-04 = A  tool_versions.status has **no** CHECK; ``published`` is only the
                  immutable semantic anchor
  * D-B15-05 = A  tools.key is an opaque identifier — no regex/format CHECK
  * D-B15-06 = A  UQ accounting: 1 UNIQUE CONSTRAINT + 3 UNIQUE INDEX
  * D-B15-07 = A  canonical test rows = 39 (38 base + 1 decision-dependent)
  * D-B15-08 = A  no snapshot value-domain CHECK (tool_versions = zero CK)
  * D-B15-09 = A  handler_ref is opaque text (never resolved/loaded/executed)

Out of scope (must NOT exist): tool_executions, agents, agent_versions,
agent_permissions, ai_*, events, audit_logs, groups, G/H/I/J ACL triggers,
RLS, Authorization evaluation, runtime plugin/discovery.

Canonical mapping (TEST_MATRIX): TS1-TS8 · TF1-TF4 · TC1-TC9 · TV1-TV4 ·
TM1-TM8 · TSEC1-TSEC5 · TD-01  ->  39.
"""

from __future__ import annotations

import re
import pathlib

import pytest
import sqlalchemy as sa

from tests.integration.alembic_testkit import (
    BASE_DSN,
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

B15_TABLES = {"tools", "tool_versions", "tool_permissions"}
B15_TRIGGERS = {"tg_tools_set_updated_at", "tg_version_immutable"}
B15_FUNCTIONS = {"enforce_tool_versions_immutable"}
B15_INDEXES = {"uq_tools_platform", "uq_tools_tenant", "uq_tool_perm", "uq_tool_versions"}
B15_CHECK_CONSTRAINTS = {
    "ck_tools_risk_level",
    "ck_tools_timeout",
    "ck_tools_idempotency",
    "ck_tools_audit_policy",
    "ck_tool_permissions_effect",
}
B15_FK_DELETE_RULES = {
    "fk_tools_tenant": "r",                     # RESTRICT
    "fk_tool_versions_tool": "c",               # CASCADE
    "fk_tool_permissions_tool": "c",            # CASCADE
    "fk_tool_permissions_version": "c",         # CASCADE
    "fk_tool_permissions_permission": "c",      # CASCADE
}
FORBIDDEN_TABLES = {
    "tool_executions",
    "agents", "agent_versions", "agent_permissions",
    "events", "audit_logs", "groups", "resource_relations",
}
G_H_I_J = {
    "tg_acl_subject_exists",
    "tg_acl_user_hard_delete",
    "tg_acl_role_delete_block",
    "tg_agent_acl_expire",
}

# 非 published 的测试夹具状态字面值。
# D-B15-04 = A 明确「status CHECK = 0，不得自创 draft/active/disabled/... 词表」——
# 因此这里刻意使用一个**中性夹具字面值**，它不构成任何 schema vocabulary。
_FIXTURE_NOT_PUBLISHED = "fixture_note_published"


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #
@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0010_b1_6_ai_gateway"
    yield
    reset_test_database()


def _engine():
    return sa.create_engine(BASE_DSN)


def _rows(sql: str, **params):
    engine = _engine()
    try:
        with engine.connect() as conn:
            return conn.execute(sa.text(sql), params).fetchall()
    finally:
        engine.dispose()


def _scalar(sql: str, **params):
    engine = _engine()
    try:
        with engine.connect() as conn:
            return conn.execute(sa.text(sql), params).scalar()
    finally:
        engine.dispose()


def _fresh_tenant(conn, slug: str = "b15") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tenants (slug, display_name, status) "
            "VALUES (:s, :s, 'active') RETURNING id"
        ),
        {"s": slug},
    ).scalar()


def _fresh_permission(conn, key: str = "tool.execute") -> str:
    """`permissions` is a P04 table with zero rows (seed is P13); a fixture row is required."""
    return conn.execute(
        sa.text(
            "INSERT INTO permissions (key, action, description) "
            "VALUES (:k, 'execute', 'fixture') RETURNING id"
        ),
        {"k": key},
    ).scalar()


def _fresh_tool(conn, tenant_id=None, key: str = "t1", **overrides) -> str:
    values = {
        "t": tenant_id,
        "k": key,
        "n": key,
        "risk": "LOW",
        "timeout": 1000,
        "idem": "none",
        "audit": "full",
        "approval": False,
        "enabled": True,
    }
    values.update(overrides)
    return conn.execute(
        sa.text(
            "INSERT INTO tools (tenant_id, key, name, risk_level, timeout_ms, "
            "idempotency_mode, audit_policy, approval_required, enabled) "
            "VALUES (:t, :k, :n, :risk, :timeout, :idem, :audit, :approval, :enabled) "
            "RETURNING id"
        ),
        values,
    ).scalar()


def _fresh_version(conn, tool_id, version: int = 1, status: str = _FIXTURE_NOT_PUBLISHED) -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tool_versions (tool_id, version, input_schema, output_schema, "
            "risk_level, timeout_ms, handler_ref, checksum, status) "
            "VALUES (:t, :v, '{}'::jsonb, '{}'::jsonb, 'LOW', 1000, "
            "'svc.handler', 'sha256:fixture', :s) RETURNING id"
        ),
        {"t": tool_id, "v": version, "s": status},
    ).scalar()


def _fresh_tool_permission(conn, tool_id, permission_id, version_id=None, effect: str = "allow") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tool_permissions (tool_id, version_id, permission_id, effect) "
            "VALUES (:t, :v, :p, :e) RETURNING id"
        ),
        {"t": tool_id, "v": version_id, "p": permission_id, "e": effect},
    ).scalar()


# ===================================================== TS1-TS2 / TM8 (schema)
def test_ts1_tables_exist(db) -> None:
    """TS1 — the three B1-5 tables exist."""
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert B15_TABLES <= tables


def test_ts2_table_counts(db) -> None:
    """TS2 — P08 后：25 业务表 + 1 当月子分区 = 26 public 表；物理 27（含 alembic_version）。"""
    business = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )} - {"alembic_version"}
    partition = {t for t in business if t.startswith("ai_request_logs_")}
    assert len(partition) == 1, sorted(business)
    assert len(business) == 26, sorted(business)
    physical = _scalar(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema NOT IN ('pg_catalog','information_schema')"
    )
    assert physical == 27


def test_ts3_tools_schema(db) -> None:
    """TS3 — tools has exactly the 15 frozen columns with frozen NN/NULL shape."""
    cols = {r[0]: r[1] for r in _rows(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name='tools'"
    )}
    assert set(cols) == {
        "id", "tenant_id", "key", "name", "description", "risk_level", "timeout_ms",
        "retry_policy", "idempotency_mode", "audit_policy", "approval_required",
        "enabled", "disabled_at", "created_at", "updated_at",
    }
    assert len(cols) == 15
    nullable = {c for c, n in cols.items() if n == "YES"}
    assert nullable == {"tenant_id", "description", "retry_policy", "disabled_at"}
    # D-B15-02: platform-level tool => tenant_id stays NULLable
    assert cols["tenant_id"] == "YES"


def test_ts4_tool_versions_schema(db) -> None:
    """TS4 — tool_versions has exactly 12 frozen columns and NO updated_at."""
    cols = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns WHERE table_name='tool_versions'"
    )}
    assert cols == {
        "id", "tool_id", "version", "input_schema", "output_schema", "risk_level",
        "timeout_ms", "handler_ref", "checksum", "status", "published_at", "created_at",
    }
    assert len(cols) == 12
    assert "updated_at" not in cols, "frozen schema has no tool_versions.updated_at"
    assert "handler_ref" in cols, "handler_ref belongs to tool_versions (not tools)"


def test_ts5_tool_permissions_schema(db) -> None:
    """TS5 — tool_permissions has exactly 7 frozen columns and NO updated_at."""
    cols = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns WHERE table_name='tool_permissions'"
    )}
    assert cols == {
        "id", "tool_id", "version_id", "permission_id", "effect", "conditions", "created_at",
    }
    assert len(cols) == 7
    assert "updated_at" not in cols


def test_ts6_primary_keys(db) -> None:
    """TS6 — PK x3, each defaulting to uap_uuid_v7()."""
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='p' "
        "AND conrelid::regclass::text = ANY(:t)", t=list(B15_TABLES)
    ) == 3
    for table in B15_TABLES:
        default = _scalar(
            "SELECT column_default FROM information_schema.columns "
            "WHERE table_name=:t AND column_name='id'", t=table
        )
        assert default == "uap_uuid_v7()", (table, default)


def test_ts7_timestamp_columns_are_timestamptz(db) -> None:
    """TS7 — every B1-5 timestamp column is `timestamptz(3)`.

    Platform rule (CORE_DOMAIN_MODEL §10 时间策略 / STEP1A_DESIGN_REPORT §12):
    precision `timestamptz(3)`. Corrected platform-wide by the corrective
    migration `0009_timestamp_precision` (20 tables / 72 columns).

    Strengthened per the platform correction: asserts **both** the timezone type
    and `datetime_precision = 3` (the previous assertion only checked the type,
    so it could not have caught the precision drift).
    """
    rows = _rows(
        "SELECT table_name, column_name, data_type, datetime_precision "
        "FROM information_schema.columns "
        "WHERE table_name = ANY(:t) AND data_type LIKE 'timestamp%'",
        t=list(B15_TABLES),
    )
    assert rows, "expected timestamp columns on B1-5 tables"
    # (a) timezone-aware
    bad_type = [(r[0], r[1], r[2]) for r in rows if r[2] != "timestamp with time zone"]
    assert bad_type == [], bad_type
    # (b) platform precision = 3（冻结规则）
    bad_precision = [(r[0], r[1], r[3]) for r in rows if r[3] != 3]
    assert bad_precision == [], bad_precision
    # (c) 覆盖 B1-5 全部时间列：tools×3 + tool_versions×2 + tool_permissions×1
    assert len(rows) == 6, sorted((r[0], r[1]) for r in rows)
    assert {r[0] for r in rows} == B15_TABLES
    # tools carries the only updated_at in B1-5
    updated = {r[0] for r in rows if r[1] == "updated_at"}
    assert updated == {"tools"}


def test_ts8_no_forbidden_tables(db) -> None:
    """TS8 — no P08/P09/P10 or Domain tables leaked into B1-5."""
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert tables.isdisjoint(FORBIDDEN_TABLES), tables & FORBIDDEN_TABLES


# ============================================================== TF1-TF4 (FK)
def test_tf1_delete_tool_cascades_versions(db) -> None:
    """TF1 — deleting a tool cascades its versions."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn)
            tool = _fresh_tool(conn, tid, "cascade_v")
            _fresh_version(conn, tool, 1)
            _fresh_version(conn, tool, 2)
            conn.commit()
            conn.execute(sa.text("DELETE FROM tools WHERE id=:i"), {"i": tool})
            conn.commit()
            assert _scalar("SELECT count(*) FROM tool_versions") == 0
    finally:
        engine.dispose()


def test_tf2_delete_tool_cascades_tool_permissions(db) -> None:
    """TF2 — deleting a tool cascades its permission bindings."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn)
            tool = _fresh_tool(conn, tid, "cascade_p")
            perm = _fresh_permission(conn, "cascade.p")
            _fresh_tool_permission(conn, tool, perm)
            conn.commit()
            conn.execute(sa.text("DELETE FROM tools WHERE id=:i"), {"i": tool})
            conn.commit()
            assert _scalar("SELECT count(*) FROM tool_permissions") == 0
    finally:
        engine.dispose()


def test_tf3_delete_version_cascades_tool_permissions(db) -> None:
    """TF3 — deleting a tool_versions row cascades bindings that reference it."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn)
            tool = _fresh_tool(conn, tid, "cascade_ver")
            ver = _fresh_version(conn, tool, 1)
            perm = _fresh_permission(conn, "cascade.ver")
            _fresh_tool_permission(conn, tool, perm, version_id=ver)
            conn.commit()
            conn.execute(sa.text("DELETE FROM tool_versions WHERE id=:i"), {"i": ver})
            conn.commit()
            assert _scalar("SELECT count(*) FROM tool_permissions") == 0
    finally:
        engine.dispose()


def test_tf4_delete_permission_cascades_tool_permissions(db) -> None:
    """TF4 — deleting a permissions row cascades the bindings that reference it."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn)
            tool = _fresh_tool(conn, tid, "cascade_perm")
            perm = _fresh_permission(conn, "cascade.perm")
            _fresh_tool_permission(conn, tool, perm, effect="deny")
            conn.commit()
            conn.execute(sa.text("DELETE FROM permissions WHERE id=:i"), {"i": perm})
            conn.commit()
            assert _scalar("SELECT count(*) FROM tool_permissions") == 0
    finally:
        engine.dispose()


# ======================================================= TC1-TC9 (constraints)
def test_tc1_ck_risk_level(db) -> None:
    """TC1 — risk_level domain is enforced (canonical row = 1 test function)."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            for i, bad in enumerate(("low", "UNKNOWN", "critical", "")):
                with pytest.raises(sa.exc.IntegrityError):
                    _fresh_tool(conn, None, f"ck1_{i}", risk=bad)
                    conn.commit()
                conn.rollback()
            for good in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                _fresh_tool(conn, None, f"ck1_{good}", risk=good)
            conn.commit()
    finally:
        engine.dispose()


def test_tc2_ck_timeout_ms(db) -> None:
    """TC2 — timeout_ms BETWEEN 100 AND 600000, boundaries inclusive (canonical row = 1)."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            for value in (100, 600000):
                _fresh_tool(conn, None, f"ck2_ok_{value}", timeout=value)
            conn.commit()
            for value in (99, 600001, 0):
                with pytest.raises(sa.exc.IntegrityError):
                    _fresh_tool(conn, None, f"ck2_bad_{value}", timeout=value)
                    conn.commit()
                conn.rollback()
    finally:
        engine.dispose()


def test_tc3_ck_idempotency_mode(db) -> None:
    """TC3 — idempotency_mode domain is enforced."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_tool(conn, None, "ck3", idem="sometimes")
                conn.commit()
            conn.rollback()
            for good in ("none", "key_required", "natural_key"):
                _fresh_tool(conn, None, f"ck3_{good}", idem=good)
            conn.commit()
    finally:
        engine.dispose()


def test_tc4_ck_audit_policy(db) -> None:
    """TC4 — audit_policy domain is enforced."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_tool(conn, None, "ck4", audit="always")
                conn.commit()
            conn.rollback()
            for good in ("sampling", "full", "full_with_payload"):
                _fresh_tool(conn, None, f"ck4_{good}", audit=good)
            conn.commit()
    finally:
        engine.dispose()


def test_tc5_ck_effect(db) -> None:
    """TC5 — tool_permissions.effect ∈ {allow, deny}."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tool = _fresh_tool(conn, None, "ck5")
            base_perm = _fresh_permission(conn, "ck5.p")
            conn.commit()   # fixtures must survive the rollback below
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_tool_permission(conn, tool, base_perm, effect="maybe")
                conn.commit()
            conn.rollback()
            # NOTE: uq_tool_perm is (tool_id, COALESCE(version_id,nil), permission_id),
            #       so each accepted effect needs its own permission row.
            for i, good in enumerate(("allow", "deny")):
                perm = _fresh_permission(conn, f"ck5.p{i}")
                _fresh_tool_permission(conn, tool, perm, effect=good)
            conn.commit()
            assert _scalar(
                "SELECT count(*) FROM tool_permissions WHERE effect IN ('allow','deny')"
            ) == 2
    finally:
        engine.dispose()


def test_tc6_uq_tools_platform(db) -> None:
    """TC6 — platform-level key uniqueness (case-insensitive)."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            _fresh_tool(conn, None, "platform_key")
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_tool(conn, None, "PLATFORM_KEY")
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_tc7_uq_tools_tenant(db) -> None:
    """TC7 — tenant-level key uniqueness; same key in different tenants is allowed."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            t1 = _fresh_tenant(conn, "b15t1")
            t2 = _fresh_tenant(conn, "b15t2")
            _fresh_tool(conn, t1, "shared_key")
            _fresh_tool(conn, t2, "shared_key")   # different tenant -> allowed
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_tool(conn, t1, "SHARED_KEY")   # same tenant, case-insensitive -> rejected
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_tc8_platform_and_tenant_scopes_do_not_conflict(db) -> None:
    """TC8 — platform-level and tenant-level keys live in disjoint unique scopes."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            t1 = _fresh_tenant(conn, "b15t3")
            _fresh_tool(conn, None, "scope_key")   # platform-level
            _fresh_tool(conn, t1, "scope_key")     # tenant-level, same literal -> allowed
            conn.commit()
            assert _scalar("SELECT count(*) FROM tools") == 2
    finally:
        engine.dispose()


def test_tc9_uq_tool_versions_and_tool_perm_expression(db) -> None:
    """TC9 — (tool_id, version) uniqueness + expression unique index on tool_permissions.

    The tool_permissions uniqueness is an expression index over
    ``(tool_id, COALESCE(version_id, nil), permission_id)``: it must NOT be
    reinterpreted as a plain UNIQUE CONSTRAINT (D-B15-06 = A).
    """
    engine = _engine()
    try:
        with engine.connect() as conn:
            tool = _fresh_tool(conn, None, "uq9")
            perm = _fresh_permission(conn, "uq9.p")
            _fresh_version(conn, tool, 1)
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_version(conn, tool, 1)
                conn.commit()
            conn.rollback()
            # two NULL-version rows with the same permission -> expression conflict
            _fresh_tool_permission(conn, tool, perm, version_id=None)
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_tool_permission(conn, tool, perm, version_id=None)
                conn.commit()
            conn.rollback()
            # one NULL + one concrete version -> allowed
            ver = _fresh_version(conn, tool, 2)
            _fresh_tool_permission(conn, tool, perm, version_id=ver)
            conn.commit()
            assert _scalar("SELECT count(*) FROM tool_permissions") == 2
            # accounting: expression uniqueness must NOT appear as UNIQUE CONSTRAINT
            assert _scalar(
                "SELECT count(*) FROM pg_constraint WHERE contype='u' "
                "AND conrelid::regclass::text = ANY(:t)", t=list(B15_TABLES)
            ) == 1
    finally:
        engine.dispose()


# ==================================================== TV1-TV4 (immutability)
def test_tv1_published_update_rejected(db) -> None:
    """TV1 — a published version can never be UPDATEd."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tool = _fresh_tool(conn, None, "tv1")
            ver = _fresh_version(conn, tool, 1, status="published")
            conn.commit()
            with pytest.raises(sa.exc.ProgrammingError) as exc:
                conn.execute(sa.text("UPDATE tool_versions SET checksum='changed' WHERE id=:i"), {"i": ver})
                conn.commit()
            assert "published version is immutable" in str(exc.value)
            conn.rollback()
    finally:
        engine.dispose()


def test_tv2_published_delete_rejected(db) -> None:
    """TV2 — a published version can never be DELETEd."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tool = _fresh_tool(conn, None, "tv2")
            ver = _fresh_version(conn, tool, 1, status="published")
            conn.commit()
            with pytest.raises(sa.exc.ProgrammingError) as exc:
                conn.execute(sa.text("DELETE FROM tool_versions WHERE id=:i"), {"i": ver})
                conn.commit()
            assert "published version is immutable" in str(exc.value)
            conn.rollback()
            assert _scalar("SELECT count(*) FROM tool_versions") == 1
    finally:
        engine.dispose()


def test_tv3_non_published_update_delete_allowed(db) -> None:
    """TV3 — non-published rows remain writable (selective enforcement)."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tool = _fresh_tool(conn, None, "tv3")
            ver = _fresh_version(conn, tool, 1, status=_FIXTURE_NOT_PUBLISHED)
            conn.commit()
            conn.execute(sa.text("UPDATE tool_versions SET checksum='updated' WHERE id=:i"), {"i": ver})
            conn.commit()
            assert _scalar("SELECT checksum FROM tool_versions WHERE id=:i", i=ver) == "updated"
            conn.execute(sa.text("DELETE FROM tool_versions WHERE id=:i"), {"i": ver})
            conn.commit()
            assert _scalar("SELECT count(*) FROM tool_versions") == 0
    finally:
        engine.dispose()


def test_tv4_trigger_is_the_enforcing_object(db) -> None:
    """TV4 — A/B contrast proves the trigger (not CHECK/FK/UQ) is the enforcer.

    Methodology (B1-4 lesson): BEFORE triggers run before CHECK constraints, so a
    "rejected" outcome alone cannot be attributed. Disabling the trigger must make
    the very same statement succeed.
    """
    engine = _engine()
    disabled = "ALTER TABLE tool_versions DISABLE TRIGGER tg_version_immutable"
    enabled = "ALTER TABLE tool_versions ENABLE TRIGGER tg_version_immutable"
    try:
        with engine.connect() as conn:
            tool = _fresh_tool(conn, None, "tv4")
            ver = _fresh_version(conn, tool, 1, status="published")
            conn.commit()

            # ENABLED: rejected by the trigger
            with pytest.raises(sa.exc.ProgrammingError) as exc:
                conn.execute(sa.text("UPDATE tool_versions SET checksum='x' WHERE id=:i"), {"i": ver})
                conn.commit()
            assert "published version is immutable" in str(exc.value)
            conn.rollback()

            # DISABLED: the identical statement succeeds -> trigger is the enforcer
            conn.execute(sa.text(disabled))
            conn.commit()
            conn.execute(sa.text("UPDATE tool_versions SET checksum='x' WHERE id=:i"), {"i": ver})
            conn.commit()
            assert _scalar("SELECT checksum FROM tool_versions WHERE id=:i", i=ver) == "x"

            conn.execute(sa.text(enabled))
            conn.commit()
            # trigger restored and enforcing again
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text("UPDATE tool_versions SET checksum='y' WHERE id=:i"), {"i": ver})
                conn.commit()
            conn.rollback()
            assert _scalar(
                "SELECT tgenabled FROM pg_trigger WHERE tgname='tg_version_immutable'"
            ) == "O"
    finally:
        engine.dispose()


# ========================================================= TM1-TM8 (migration)
def test_tm1_upgrade_0007_to_0008(db) -> None:
    """TM1 — 0007 -> 0008 upgrade succeeds."""
    assert current_revision() == "0010_b1_6_ai_gateway"


def test_tm2_downgrade_0008_to_0007(db) -> None:
    """TM2 — 0008 -> 0007 downgrade succeeds."""
    cfg = make_config(lock_mode="fail")
    downgrade(cfg, "0007_b1_4_resource_acl")
    assert current_revision() == "0007_b1_4_resource_acl"
    upgrade(cfg, "head")


def test_tm3_roundtrip_object_set_is_stable(db) -> None:
    """TM3 — 0007->0008->0007->0008 restores an identical object set."""
    cfg = make_config(lock_mode="fail")
    before = _scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = ANY(:t)",
        t=list(B15_TABLES),
    )
    downgrade(cfg, "0007_b1_4_resource_acl")
    upgrade(cfg, "head")
    after = _scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = ANY(:t)",
        t=list(B15_TABLES),
    )
    assert before == after == 3


def test_tm4_downgrade_leaves_no_residue(db) -> None:
    """TM4 — downgrade removes every B1-5 object."""
    cfg = make_config(lock_mode="fail")
    downgrade(cfg, "0007_b1_4_resource_acl")
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert tables.isdisjoint(B15_TABLES), "downgrade left B1-5 tables behind"
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(B15_TRIGGERS)) == 0
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)", n=list(B15_FUNCTIONS)) == 0
    assert _scalar("SELECT count(*) FROM pg_indexes WHERE indexname = ANY(:n)", n=list(B15_INDEXES)) == 0
    upgrade(cfg, "head")


def test_tm5_set_updated_at_not_recreated(db) -> None:
    """TM5 — the shared set_updated_at() function is reused, never recreated."""
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1
    src = pathlib.Path("migrations_alembic/versions/0008_b1_5_tool_registry.py").read_text(
        encoding="utf-8"
    )
    assert "CREATE OR REPLACE FUNCTION set_updated_at" not in src
    assert "CREATE FUNCTION set_updated_at" not in src


def test_tm6_uap_uuid_v7_intact(db) -> None:
    """TM6 — the shared uap_uuid_v7() primitive survives untouched."""
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='uap_uuid_v7'") == 1


def test_tm7_b1_4_objects_intact(db) -> None:
    """TM7 — B1-4 objects are unaffected by 0008."""
    b14_tables = {"resources", "acl_subject_types", "resource_permissions"}
    b14_triggers = {
        "tg_resources_set_updated_at",
        "tg_resources_tenant_space_consistency",
        "tg_acl_subject_types_protect",
    }
    b14_functions = {
        "enforce_resources_tenant_space_consistency",
        "enforce_acl_subject_types_protect",
    }
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert b14_tables <= tables
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(b14_triggers)) == 3
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)", n=list(b14_functions)) == 2
    assert _scalar("SELECT count(*) FROM acl_subject_types") == 0


def test_tm8_head_and_trigger_set(db) -> None:
    """TM8 — head is 0009 and B1-5 introduces exactly two triggers."""
    assert current_revision() == "0010_b1_6_ai_gateway"
    rows = _rows(
        "SELECT tgname, tgtype FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid::regclass::text = ANY(:t)", t=list(B15_TABLES)
    )
    names = {r[0] for r in rows}
    assert names == B15_TRIGGERS, names
    timings = dict(rows)
    assert timings["tg_tools_set_updated_at"] == 19      # ROW|BEFORE|UPDATE
    assert timings["tg_version_immutable"] == 27         # ROW|BEFORE|DELETE|UPDATE


# ========================================================== TSEC1-TSEC5
def test_tsec1_rls_disabled(db) -> None:
    """TSEC1 — no RLS enabled, no policies."""
    assert _scalar("SELECT count(*) FROM pg_policies WHERE schemaname='public'") == 0
    assert _scalar(
        "SELECT count(*) FROM pg_class WHERE relname = ANY(:t) AND relrowsecurity",
        t=list(B15_TABLES),
    ) == 0
    src = pathlib.Path("migrations_alembic/versions/0008_b1_5_tool_registry.py").read_text(
        encoding="utf-8"
    ).lower()
    assert "row level security" not in src
    assert "create policy" not in src
    assert "enable row level" not in src


def test_tsec2_core_domain_boundary() -> None:
    """TSEC2 — Core never imports Domain / agent / intelligence."""
    core = pathlib.Path("core")
    violations = []
    for path in core.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^\s*(?:from|import)\s+(domains|agent|intelligence|apps)[\w.]*",
                             text, re.M):
            violations.append(f"{path}: {m.group(1)}")
    assert violations == [], violations


def test_tsec3_zero_seed(db) -> None:
    """TSEC3 — B1-5 performs no seed at all."""
    for table in sorted(B15_TABLES):
        assert _scalar(f"SELECT count(*) FROM {table}") == 0, table
    src = pathlib.Path("migrations_alembic/versions/0008_b1_5_tool_registry.py").read_text(
        encoding="utf-8"
    )
    assert "INSERT INTO" not in src


def test_tsec4_g_h_i_j_absent(db) -> None:
    """TSEC4 — G/H/I/J stay P09-after, never implemented in B1-5."""
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(G_H_I_J)) == 0


def test_tsec5_no_unauthorized_objects_or_industry_terms(db) -> None:
    """TSEC5 — no unauthorized tables, no domain/industry vocabulary, no evaluators."""
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert tables.isdisjoint(FORBIDDEN_TABLES), tables & FORBIDDEN_TABLES
    src = pathlib.Path("migrations_alembic/versions/0008_b1_5_tool_registry.py").read_text(
        encoding="utf-8"
    )
    # The module docstring / inline comments *state* what is excluded, so strip
    # triple-quoted blocks (docstrings + SQL literals) AND `#` comments, then scan
    # only the executable code for real traces.
    code = re.sub(r'"""(?:.|\n)*?"""', "", src)
    code = re.sub(r"#[^\n]*", "", code).lower()
    for term in ("row level security", "create policy", "'group'", "restaurant", "company",
                 "entertainment", "family", "draft", "deprecated", "revoked"):
        assert term not in code, term
    for trace in ("plugin_runtime", "register_plugin", "handler_resolve", "resolve_handler",
                  "import_plugin", "load_plugin", "abac", "policy_evaluator",
                  "authorization_evaluator", "rls"):
        assert trace not in code, trace


# ==================================================== TD-01 (decision-dependent)
def test_td_01_tenant_fk_behaviour(db) -> None:
    """TD-01 — D-B15-02 = A: tenant FK exists with RESTRICT; NULL stays platform-level.

      * tenant_id pointing at a non-existent tenant          -> rejected (FK)
      * deleting a tenant that still owns a tool              -> rejected (RESTRICT)
      * tenant_id IS NULL (platform-level tool)               -> allowed
    """
    fk = _rows(
        "SELECT confdeltype FROM pg_constraint "
        "WHERE conname='fk_tools_tenant' AND contype='f'"
    )
    assert fk and fk[0][0] == "r", f"expected RESTRICT, got {fk}"

    engine = _engine()
    try:
        with engine.connect() as conn:
            # 1) dangling tenant reference
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(
                    sa.text(
                        "INSERT INTO tools (tenant_id, key, name, risk_level, timeout_ms, "
                        "idempotency_mode, audit_policy, approval_required, enabled) "
                        "VALUES ('00000000-0000-0000-0000-0000000000ff', 'dangling', 'd', "
                        "'LOW', 1000, 'none', 'full', false, true)"
                    )
                )
                conn.commit()
            conn.rollback()

            # 2) RESTRICT: a tenant owning a tool cannot be deleted
            tid = _fresh_tenant(conn, "b15restrict")
            _fresh_tool(conn, tid, "owned")
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("DELETE FROM tenants WHERE id=:i"), {"i": tid})
                conn.commit()
            conn.rollback()

            # 3) platform-level tool (tenant_id IS NULL) remains allowed
            _fresh_tool(conn, None, "platform_ok")
            conn.commit()
            assert _scalar("SELECT count(*) FROM tools WHERE tenant_id IS NULL") == 1
    finally:
        engine.dispose()
