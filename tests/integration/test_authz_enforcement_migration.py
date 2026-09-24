"""0012_authz_enforcement — the approved schema change set, end to end.

Covers the two CHECK constraints (SC-1 / SC-1b), the three structured tool-grant
columns (SC-2), the defensive preflight, full downgrade reversibility, and the
P09 protection surface: the agent/tool-permission tables must come out of this
revision byte-for-byte as they went in.

Disabled entirely when PostgreSQL is not reachable, so the suite still runs
offline.
"""

from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Connection

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

REVISION = "0012_authz_enforcement"
PREVIOUS = "0011_p09_agent_tool_permission"

CANONICAL_ACTIONS = (
    "read", "list", "create", "update", "delete", "execute",
    "approve", "reject", "publish", "export", "share", "admin",
)

NEW_TOOL_COLUMNS = ("resource_type", "action", "scope")

# The P09 protection surface, exactly as 0011 created it.
AGENT_PERMISSIONS_COLUMNS = (
    "id", "agent_id", "version_id", "permission_id", "tool_id",
    "resource_scope", "effect", "conditions", "created_at",
)


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == REVISION
    yield
    reset_test_database()


def _connect() -> tuple[sa.Engine, Connection]:
    engine = sa.create_engine(BASE_DSN)
    return engine, engine.connect()


def _constraint_def(conn: Connection, name: str) -> str | None:
    return conn.execute(
        sa.text(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :n"
        ),
        {"n": name},
    ).scalar()


def _columns(conn: Connection, table: str) -> list[tuple[str, str, str]]:
    rows = conn.execute(
        sa.text(
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"
        ),
        {"t": table},
    ).fetchall()
    return [(str(r[0]), str(r[1]), str(r[2])) for r in rows]


def _table_columns(conn: Connection, table: str) -> list[str]:
    return [name for name, _, _ in _columns(conn, table)]


# --------------------------------------------------------------------------- #
# head / identity
# --------------------------------------------------------------------------- #
def test_head_is_the_single_new_revision(db) -> None:
    engine, conn = _connect()
    try:
        assert current_revision() == REVISION
        rows = conn.execute(
            sa.text("SELECT version_num FROM alembic_version")
        ).fetchall()
        assert len(rows) == 1
        assert str(rows[0][0]) == REVISION
    finally:
        conn.close()
        engine.dispose()


def test_revision_identifier_fits_the_version_column(db) -> None:
    engine, conn = _connect()
    try:
        width = conn.execute(
            sa.text(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_name='alembic_version' AND column_name='version_num'"
            )
        ).scalar()
        assert len(REVISION) <= int(width) <= 32
    finally:
        conn.close()
        engine.dispose()


# --------------------------------------------------------------------------- #
# SC-1 / SC-1b — canonical action enforcement
# --------------------------------------------------------------------------- #
def test_sc1_permissions_action_is_constrained_to_canonical_actions(db) -> None:
    engine, conn = _connect()
    try:
        definition = _constraint_def(conn, "ck_permissions_action_canonical")
        assert definition is not None
        for action in CANONICAL_ACTIONS:
            assert f"'{action}'" in definition
    finally:
        conn.close()
        engine.dispose()


def test_sc1b_resource_permissions_action_is_constrained(db) -> None:
    engine, conn = _connect()
    try:
        definition = _constraint_def(conn, "ck_resource_permissions_action_canonical")
        assert definition is not None
        for action in CANONICAL_ACTIONS:
            assert f"'{action}'" in definition
    finally:
        conn.close()
        engine.dispose()


def test_sc1_rejects_a_non_canonical_action(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            conn.execute(
                sa.text(
                    "INSERT INTO permissions (key, action, is_system) "
                    "VALUES ('demo.bad', 'x9.bogus', false)"
                )
            )
        raise AssertionError("the database accepted a non-canonical action")
    except sa.exc.IntegrityError:
        pass
    finally:
        conn.close()
        engine.dispose()


def test_sc1_accepts_every_canonical_action(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            for index, action in enumerate(CANONICAL_ACTIONS):
                conn.execute(
                    sa.text(
                        "INSERT INTO permissions (key, action, is_system) "
                        "VALUES (:k, :a, false)"
                    ),
                    {"k": f"demo.canonical_{index}", "a": action},
                )
    finally:
        conn.close()
        engine.dispose()


def test_migration_vocabulary_is_the_core_vocabulary() -> None:
    """``D-AUTH-25`` single-source guarantee (§4).

    The migration necessarily carries a *literal* list — an applied migration
    must keep its historical meaning even if the vocabulary later grows — but
    that literal list must stay byte-equal to the core vocabulary. This test
    makes the duplication *verified* instead of incidental.
    """
    import ast
    import pathlib

    from core.permission.vocabulary import ACTIONS

    source = pathlib.Path(
        "migrations_alembic/versions/0012_authz_enforcement.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    in_migration = {
        value for value in literals if value in set(ACTIONS)
    }
    assert in_migration == set(ACTIONS), sorted(set(ACTIONS) - in_migration)
    assert CANONICAL_ACTIONS == tuple(ACTIONS)


def test_storage_boundary_rejects_non_lowercase_spellings(db) -> None:
    """``D-AUTH-25`` — the *storage* boundary is exactly lowercase.

    Case tolerance lives only in the inbound normalisation (``normalize_action``);
    the database accepts the canonical form and nothing else. ``READ`` / ``Read``
    / ``rEaD`` are therefore storage violations even though the *service* would
    have normalised them — the boundary is where the difference is drawn.
    """
    engine, conn = _connect()
    try:
        for index, spelling in enumerate(("READ", "Read", "rEaD", "foo", "x9.opaque")):
            with pytest.raises(sa.exc.IntegrityError):
                with conn.begin():
                    conn.execute(
                        sa.text(
                            "INSERT INTO permissions (key, action, is_system) "
                            "VALUES (:k, :a, false)"
                        ),
                        {"k": f"demo.case_{index}", "a": spelling},
                    )
    finally:
        conn.close()
        engine.dispose()


# --------------------------------------------------------------------------- #
# SC-2 — structured tool grants
# --------------------------------------------------------------------------- #
def test_sc2_tool_permissions_gains_three_nullable_text_columns(db) -> None:
    engine, conn = _connect()
    try:
        columns = {name: (data_type, nullable) for name, data_type, nullable in _columns(conn, "tool_permissions")}
        for column in NEW_TOOL_COLUMNS:
            assert column in columns, column
            assert columns[column] == ("text", "YES")
    finally:
        conn.close()
        engine.dispose()


def test_sc2_tool_scope_is_constrained_to_stored_scopes(db) -> None:
    engine, conn = _connect()
    try:
        definition = _constraint_def(conn, "ck_tool_permissions_scope")
        assert definition is not None
        for scope in ("PLATFORM", "TENANT", "SPACE"):
            assert f"'{scope}'" in definition
        assert "RESOURCE" not in definition
        assert "SELF" not in definition
    finally:
        conn.close()
        engine.dispose()


def test_sc2_rejects_an_unstored_tool_scope(db) -> None:
    engine, conn = _connect()
    try:
        permission_id = conn.execute(
            sa.text(
                "INSERT INTO permissions (key, action, is_system) "
                "VALUES ('demo.tool', 'execute', false) RETURNING id"
            )
        ).scalar()
        tenant_id = conn.execute(
            sa.text(
                "INSERT INTO tenants (slug, display_name, status) "
                "VALUES ('t-scope', 'T', 'active') RETURNING id"
            )
        ).scalar()
        tool_id = conn.execute(
            sa.text(
                "INSERT INTO tools (key, name, risk_level, timeout_ms, "
                "idempotency_mode, audit_policy, approval_required, enabled, tenant_id) "
                "VALUES ('demo_tool', 'Demo', 'LOW', 1000, 'none', 'sampling', false, true, :t) "
                "RETURNING id"
            ),
            {"t": tenant_id},
        ).scalar()
        conn.commit()

        with conn.begin():
            conn.execute(
                sa.text(
                    "INSERT INTO tool_permissions "
                    "(tool_id, permission_id, effect, resource_type, action, scope) "
                    "VALUES (:tl, :p, 'allow', 'order', 'execute', 'SELF')"
                ),
                {"tl": tool_id, "p": permission_id},
            )
        raise AssertionError("the database accepted a context predicate as a stored scope")
    except sa.exc.IntegrityError:
        pass
    finally:
        conn.close()
        engine.dispose()


def test_sc2_accepts_a_structured_grant(db) -> None:
    engine, conn = _connect()
    try:
        permission_id = conn.execute(
            sa.text(
                "INSERT INTO permissions (key, action, is_system) "
                "VALUES ('demo.ok', 'execute', false) RETURNING id"
            )
        ).scalar()
        tenant_id = conn.execute(
            sa.text(
                "INSERT INTO tenants (slug, display_name, status) "
                "VALUES ('t-ok', 'T', 'active') RETURNING id"
            )
        ).scalar()
        tool_id = conn.execute(
            sa.text(
                "INSERT INTO tools (key, name, risk_level, timeout_ms, "
                "idempotency_mode, audit_policy, approval_required, enabled, tenant_id) "
                "VALUES ('ok_tool', 'OK', 'LOW', 1000, 'none', 'sampling', false, true, :t) "
                "RETURNING id"
            ),
            {"t": tenant_id},
        ).scalar()
        conn.commit()
        with conn.begin():
            conn.execute(
                sa.text(
                    "INSERT INTO tool_permissions "
                    "(tool_id, permission_id, effect, resource_type, action, scope) "
                    "VALUES (:tl, :p, 'allow', 'order', 'execute', 'TENANT')"
                ),
                {"tl": tool_id, "p": permission_id},
            )
    finally:
        conn.close()
        engine.dispose()


# --------------------------------------------------------------------------- #
# downgrade / reversibility
# --------------------------------------------------------------------------- #
def test_downgrade_reverts_to_the_previous_revision_with_no_residue(db) -> None:
    engine, conn = _connect()
    before = _columns(conn, "tool_permissions")
    conn.close()
    engine.dispose()

    downgrade(make_config(lock_mode="fail"), PREVIOUS)
    assert current_revision() == PREVIOUS

    engine, conn = _connect()
    try:
        for name in (
            "ck_permissions_action_canonical",
            "ck_resource_permissions_action_canonical",
            "ck_tool_permissions_scope",
        ):
            assert _constraint_def(conn, name) is None, name
        for column in NEW_TOOL_COLUMNS:
            assert column not in _table_columns(conn, "tool_permissions"), column
        assert _columns(conn, "tool_permissions") == [
            (name, data_type, nullable)
            for name, data_type, nullable in before
            if name not in NEW_TOOL_COLUMNS
        ]
    finally:
        conn.close()
        engine.dispose()

    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == REVISION


# --------------------------------------------------------------------------- #
# preflight
# --------------------------------------------------------------------------- #
def test_preflight_refuses_to_tighten_a_column_holding_bad_values(db) -> None:
    base = make_config(lock_mode="fail")
    downgrade(base, PREVIOUS)

    engine, conn = _connect()
    try:
        with conn.begin():
            conn.execute(
                sa.text(
                    "INSERT INTO permissions (key, action, is_system) "
                    "VALUES ('demo.legacy', 'x9.bogus', false)"
                )
            )
    finally:
        conn.close()
        engine.dispose()

    with pytest.raises(Exception) as excinfo:
        upgrade(make_config(lock_mode="fail"), "head")
    assert "SC-1 preflight failed" in str(excinfo.value)

    assert current_revision() == PREVIOUS

    engine, conn = _connect()
    try:
        with conn.begin():
            conn.execute(sa.text("DELETE FROM permissions WHERE key = 'demo.legacy'"))
    finally:
        conn.close()
        engine.dispose()

    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == REVISION


# --------------------------------------------------------------------------- #
# AGENT-RESOURCE-SCOPE-03 — P09 protection
# --------------------------------------------------------------------------- #
def test_agent_resource_scope_03_p09_schema_is_unchanged(db) -> None:
    """AGENT-RESOURCE-SCOPE-03 — the P09 tables are untouched by 0012."""
    engine, conn = _connect()
    try:
        assert _table_columns(conn, "agent_permissions") == list(AGENT_PERMISSIONS_COLUMNS)

        opaque = [
            row
            for row in _columns(conn, "agent_permissions")
            if row[0] == "resource_scope"
        ]
        assert opaque == [("resource_scope", "text", "YES")]

        constraints = conn.execute(
            sa.text(
                "SELECT conname FROM pg_constraint con "
                "JOIN pg_class c ON c.oid = con.conrelid "
                "WHERE c.relname = 'agent_permissions' AND con.contype = 'c' "
                "ORDER BY conname"
            )
        ).fetchall()
        assert [str(row[0]) for row in constraints] == [
            "ck_agent_permissions_effect",
            "ck_agent_permissions_scope_target",
        ]
    finally:
        conn.close()
        engine.dispose()


def test_p09_tables_and_p08_tables_are_untouched(db) -> None:
    """0012 adds no table and leaves every other table's column set alone."""
    engine, conn = _connect()
    try:
        # Partition children repeat in information_schema, so the table set is
        # read from pg_class (partitioned parents only) as the platform does.
        rows = conn.execute(
            sa.text(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relkind = 'r' "
                "AND NOT c.relispartition AND c.relname <> 'alembic_version' "
                "ORDER BY c.relname"
            )
        ).fetchall()
        names = {str(row[0]) for row in rows}
        assert {"agents", "agent_versions", "agent_permissions", "tool_executions"} <= names
        assert not {"events", "audit_logs", "approval_requests"} & names

        physical = conn.execute(
            sa.text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
        ).scalar()
        assert int(physical) == 31
    finally:
        conn.close()
        engine.dispose()
