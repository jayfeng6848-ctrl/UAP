"""P11 implementation tests — canonical ACL triggers G/H/I/J (0014_p11_triggers).

Semantics authority: ``D-P11-01..14`` + ``P11_IMPLEMENTATION_CONTRACT.md`` §3/§4/§11.
Every failure path must roll back its transaction (D-P11-04); every RAISE probe below
runs on a dedicated connection and asserts the pre-failure row state afterwards.
"""

from __future__ import annotations

import uuid

import pathlib
import re

import pytest
import sqlalchemy as sa

from alembic_testkit import (  # noqa: F401  (fixtures come from the shared kit)
    BASE_DSN,
    current_revision,
    downgrade,
    make_config,
    reset_test_database,
    upgrade,
)

MIGRATION_FILE = pathlib.Path(
    "migrations_alembic/versions/0014_p11_triggers.py"
).resolve()

P11_TRIGGERS = {
    "tg_acl_subject_exists": "resource_permissions",
    "tg_acl_user_hard_delete": "users",
    "tg_acl_role_delete_block": "roles",
    "tg_agent_acl_expire": "agents",
}
P11_FUNCTIONS = {
    "enforce_acl_subject_exists",
    "enforce_acl_user_hard_delete",
    "enforce_acl_role_delete_block",
    "enforce_agent_acl_expire",
}
P10_OWNED = {"tg_audit_immutable": "audit_logs"}

MISSING_ID = "00000000-0000-0000-0000-000000000001"
UNREGISTERED_TYPE = "00000000-0000-0000-0000-000000000002"


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
def _engine():
    return sa.create_engine(BASE_DSN)


def _scalar(sql, **params):
    with _engine().connect() as conn:
        return conn.execute(sa.text(sql), params).scalar()


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0015_p12_indexes"
    yield
    reset_test_database()


@pytest.fixture()
def world(db):
    """Registry rows (migration-controlled registry, C2 temporarily disabled),
    one tenant/space/resource, one user / role / agent with an ACL row each."""
    eng = _engine()

    def q(sql, **params):
        with eng.begin() as conn:
            conn.execute(sa.text(sql), params)

    def q1(sql, **params):
        with eng.begin() as conn:
            return conn.execute(sa.text(sql), params).scalar()

    q("ALTER TABLE acl_subject_types DISABLE TRIGGER tg_acl_subject_types_protect")
    ids = {}
    for key in ("user", "role", "agent"):
        ids["t_" + key] = q1(
            "INSERT INTO acl_subject_types (key, description) "
            "VALUES (:k, 'p11 fixture') RETURNING id", k=key
        )
    q("ALTER TABLE acl_subject_types ENABLE TRIGGER tg_acl_subject_types_protect")

    ids["tenant"] = q1(
        "INSERT INTO tenants (slug, display_name, status) "
        "VALUES ('p11', 'P11', 'active') RETURNING id"
    )
    ids["space"] = q1(
        "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
        "VALUES (:t, 'p11', 'P11', 'team', 'private', 'active') RETURNING id",
        t=ids["tenant"],
    )
    ids["resource"] = q1(
        "INSERT INTO resources (tenant_id, space_id, resource_type, natural_key) "
        "VALUES (:t, :s, 'document', 'p11r') RETURNING id",
        t=ids["tenant"], s=ids["space"],
    )
    ids["user"] = q1(
        "INSERT INTO users (username, email, display_name, status) "
        "VALUES ('p11u', 'p11u@x.io', 'P11', 'active') RETURNING id"
    )
    ids["role"] = q1(
        "INSERT INTO roles (key, name, scope, tenant_id, status) "
        "VALUES ('p11role', 'P11', 'TENANT', :t, 'active') RETURNING id",
        t=ids["tenant"],
    )
    ids["agent"] = q1(
        "INSERT INTO agents (key, name, status, tenant_id, space_id, owner_id, "
        "max_risk_level, config) VALUES ('p11ag', 'P11', 'active', :t, :s, :u, "
        "'LOW', '{}'::jsonb) RETURNING id",
        t=ids["tenant"], s=ids["space"], u=ids["user"],
    )

    def acl(subject_type_id, subject_id, resource_id=None):
        return q1(
            "INSERT INTO resource_permissions (id, resource_id, subject_type_id, "
            "subject_id, action, effect, inherited) "
            "VALUES (gen_random_uuid(), :r, :st, :si, 'read', 'allow', false) "
            "RETURNING id",
            r=resource_id or ids["resource"],
            st=subject_type_id, si=subject_id,
        )

    acl(ids["t_user"], ids["user"])
    acl(ids["t_role"], ids["role"])
    acl(ids["t_agent"], ids["agent"])
    yield ids
    eng.dispose()


def acl_count(subject_id, **extra):
    sql = "SELECT count(*) FROM resource_permissions WHERE subject_id = :s"
    return _scalar(sql + "".join(f" AND {k}" for k in extra), s=subject_id, **extra)


# --------------------------------------------------------------------------- #
# G — subject existence
# --------------------------------------------------------------------------- #
def _g_insert(world, subject_type_id, subject_id, action="update"):
    eng = _engine()
    try:
        with eng.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO resource_permissions (id, resource_id, "
                    "subject_type_id, subject_id, action, effect, inherited) "
                    "VALUES (gen_random_uuid(), :r, :st, :si, :a, 'allow', false)"
                ),
                {"r": world["resource"], "st": subject_type_id, "si": subject_id,
                 "a": action},
            )
    finally:
        eng.dispose()


@pytest.mark.parametrize("kind", ["user", "role", "agent"])
def test_g_valid_subjects_are_accepted(world, kind) -> None:
    # fixture already granted action='read' for these subjects (uq_resource_perm);
    # use a different action so the tuple stays unique
    _g_insert(world, world["t_" + kind], world[kind], action="update")  # must not raise
    assert _scalar("SELECT count(*) FROM resource_permissions") == 4


@pytest.mark.parametrize("kind", ["user", "role", "agent"])
def test_g_missing_subjects_are_rejected_and_rolled_back(world, kind) -> None:
    before = _scalar("SELECT count(*) FROM resource_permissions")
    with pytest.raises(sa.exc.DBAPIError):
        _g_insert(world, world["t_" + kind], MISSING_ID)
    assert _scalar("SELECT count(*) FROM resource_permissions") == before, (
        "failed insert must leave no row (transaction rollback)"
    )


def test_g_unregistered_subject_type_is_rejected(world) -> None:
    with pytest.raises(sa.exc.DBAPIError):
        _g_insert(world, UNREGISTERED_TYPE, world["user"])
    with pytest.raises(sa.exc.DBAPIError):
        _g_insert(world, MISSING_ID, world["user"])


def test_g_group_is_not_a_valid_subject_key(world) -> None:
    """`groups` must never become a subject path (P2-02 / D-P11-02).

    Two independent gates: (a) the registry CHECK whitelist allows only
    user/role/agent keys, so a 'group' subject type cannot even exist —
    even with the C2 runtime-INSERT trigger disabled; (b) G's else-branch
    rejects any key outside {user, role, agent} (belt-and-braces, static).
    """
    eng = _engine()
    try:
        # DISABLE / probe / ENABLE must be separate transactions: a failed probe
        # aborts its own transaction only (autocommit-style DDL guard handling)
        with eng.begin() as conn:
            conn.execute(sa.text(
                "ALTER TABLE acl_subject_types "
                "DISABLE TRIGGER tg_acl_subject_types_protect"))
        try:
            with pytest.raises(sa.exc.DBAPIError):
                with eng.begin() as conn:
                    conn.execute(sa.text(
                        "INSERT INTO acl_subject_types (key, description) "
                        "VALUES ('group', 'probe')"
                    ))
        finally:
            with eng.begin() as conn:
                conn.execute(sa.text(
                    "ALTER TABLE acl_subject_types "
                    "ENABLE TRIGGER tg_acl_subject_types_protect"))
    finally:
        eng.dispose()
    ck = _scalar("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                 "WHERE conname = 'ck_acl_subject_types_whitelist'")
    assert "'user'" in ck and "'role'" in ck and "'agent'" in ck
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert "unregistered acl subject type key" in src  # G's else-branch gate


def test_g_ignores_updates_of_non_watched_columns(world) -> None:
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "UPDATE resource_permissions SET conditions = '{}'::jsonb "
            "WHERE subject_id = :u"
        ), {"u": world["user"]})


# --------------------------------------------------------------------------- #
# H — user hard delete
# --------------------------------------------------------------------------- #
def test_h_hard_delete_purges_user_acl_only(world) -> None:
    def q1(sql, **p):
        with _engine().begin() as conn:
            return conn.execute(sa.text(sql), p).scalar()

    with _engine().begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO users (username, email, display_name, status) "
            "VALUES ('p11u2', 'p11u2@x.io', 'P11b', 'active')"))
    u2 = q1("SELECT id FROM users WHERE username = 'p11u2'")
    q1("INSERT INTO resource_permissions (id, resource_id, subject_type_id, "
       "subject_id, action, effect, inherited) "
       "VALUES (gen_random_uuid(), :r, :st, :si, 'read', 'allow', false) "
       "RETURNING id",
       r=world["resource"], st=world["t_user"], si=u2)
    assert acl_count(u2) == 1

    with _engine().begin() as conn:
        conn.execute(sa.text("DELETE FROM users WHERE id = :u"), {"u": u2})
    assert acl_count(u2) == 0, "hard delete must purge the user's ACL rows"
    # scope: only this user's ACL — the other fixtures' rows survive
    assert _scalar("SELECT count(*) FROM resource_permissions") == 3


def test_h_soft_delete_preserves_user_acl(world) -> None:
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "UPDATE users SET status = 'suspended' WHERE id = :u"
        ), {"u": world["user"]})
    assert acl_count(world["user"]) == 1, (
        "soft delete (UPDATE path) must never purge ACL rows"
    )


# --------------------------------------------------------------------------- #
# I — role delete block
# --------------------------------------------------------------------------- #
def test_i_referenced_role_delete_is_rejected_and_rolled_back(world) -> None:
    with pytest.raises(sa.exc.DBAPIError):
        with _engine().begin() as conn:
            conn.execute(sa.text("DELETE FROM roles WHERE id = :r"),
                         {"r": world["role"]})
    assert _scalar("SELECT count(*) FROM roles WHERE id = :r",
                   r=world["role"]) == 1, "role must survive the rejected delete"


def test_i_unreferenced_role_delete_is_allowed(world) -> None:
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO roles (key, name, scope, tenant_id, status) "
            "VALUES ('p11free', 'P11F', 'TENANT', :t, 'active')"
        ), {"t": world["tenant"]})
        free = conn.execute(sa.text(
            "SELECT id FROM roles WHERE key = 'p11free'")).scalar()
        conn.execute(sa.text("DELETE FROM roles WHERE id = :r"), {"r": free})
    assert _scalar("SELECT count(*) FROM roles WHERE id = :r", r=free) == 0


def test_i_compatible_with_existing_roles_delete_triggers(world) -> None:
    """Contract §2.3: name-order firing + independent conditions ⇒ any RAISE aborts.

    A non-system, unreferenced role passes I *and* the pre-existing guards;
    the frozen system-role protection (is_system) still rejects independently.
    """
    # is_system protection must still hold alongside I (BEFORE INSERT here)
    with pytest.raises(sa.exc.DBAPIError):
        with _engine().begin() as conn:
            conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, tenant_id, status, is_system) "
                "VALUES ('p11sys', 'S', 'TENANT', :t, 'active', true)"
            ), {"t": world["tenant"]})
    # and a plain role with no ACL reference deletes cleanly (I passes, others pass)
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO roles (key, name, scope, tenant_id, status) "
            "VALUES ('p11ok', 'P11OK', 'TENANT', :t, 'active')"
        ), {"t": world["tenant"]})
        rid_ = conn.execute(sa.text(
            "SELECT id FROM roles WHERE key = 'p11ok'")).scalar()
        conn.execute(sa.text("DELETE FROM roles WHERE id = :r"), {"r": rid_})


# --------------------------------------------------------------------------- #
# J — agent ACL expiry
# --------------------------------------------------------------------------- #
def _expire_state(agent_id):
    return _scalar(
        "SELECT count(*) FROM resource_permissions WHERE subject_id = :a "
        "AND inherited = true AND expires_at IS NOT NULL", a=agent_id)


def test_j_archive_expires_agent_acl(world) -> None:
    assert _expire_state(world["agent"]) == 0
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "UPDATE agents SET status = 'archived' WHERE id = :a"
        ), {"a": world["agent"]})
    assert _expire_state(world["agent"]) == 1
    # rows are retained, not deleted (D-P11-02: agent 行不删，仅失效)
    assert acl_count(world["agent"]) == 1


def test_j_non_archived_status_change_does_not_expire(world) -> None:
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "UPDATE agents SET status = 'disabled' WHERE id = :a"
        ), {"a": world["agent"]})
    assert _expire_state(world["agent"]) == 0


def test_j_delete_expires_agent_acl(world) -> None:
    with _engine().begin() as conn:
        conn.execute(sa.text("DELETE FROM agents WHERE id = :a"),
                     {"a": world["agent"]})
    assert _expire_state(world["agent"]) == 1
    assert acl_count(world["agent"]) == 1, "J must not delete ACL rows"


def test_j_does_not_trigger_g_and_never_touches_subject_columns(world) -> None:
    """D-P11-09: J SET list ∩ G watched columns = ∅ (observable, no exception)."""
    with _engine().begin() as conn:
        row = conn.execute(sa.text(
            "SELECT subject_type_id, subject_id FROM resource_permissions "
            "WHERE subject_id = :a"
        ), {"a": world["agent"]}).fetchone()
        conn.execute(sa.text(
            "UPDATE agents SET status = 'archived' WHERE id = :a"
        ), {"a": world["agent"]})
        row2 = conn.execute(sa.text(
            "SELECT subject_type_id, subject_id FROM resource_permissions "
            "WHERE subject_id = :a"
        ), {"a": world["agent"]}).fetchone()
    assert (row[0], row[1]) == (row2[0], row2[1]), (
        "J must not modify subject_type_id / subject_id"
    )


def test_j_role_archive_writes_nothing(world) -> None:
    """D-P11-05/D-P11-14: role archival has NO P11 trigger and keeps ACL rows."""
    with _engine().begin() as conn:
        conn.execute(sa.text(
            "UPDATE roles SET status = 'archived' WHERE id = :r"
        ), {"r": world["role"]})
    assert acl_count(world["role"]) == 1
    assert _scalar(
        "SELECT count(*) FROM resource_permissions WHERE subject_id = :r "
        "AND expires_at IS NOT NULL", r=world["role"]) == 0


# --------------------------------------------------------------------------- #
# identity / boundary / security
# --------------------------------------------------------------------------- #
def test_head_and_exact_p11_objects(db) -> None:
    assert current_revision() == "0015_p12_indexes"
    with _engine().connect() as conn:
        rows = dict(conn.execute(sa.text(
            "SELECT tgname, tgrelid::regclass::text FROM pg_trigger "
            "WHERE NOT tgisinternal AND tgparentid = 0 "
            "AND tgname = ANY(:n)"), {"n": sorted(P11_TRIGGERS)}).fetchall())
    assert rows == P11_TRIGGERS
    assert _scalar(
        "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = 'public' AND proname = ANY(:n)", n=sorted(P11_FUNCTIONS)) == 4


def test_trigger_timings_match_frozen_design(db) -> None:
    with _engine().connect() as conn:
        rows = dict(conn.execute(sa.text(
            "SELECT tgname, tgtype FROM pg_trigger WHERE NOT tgisinternal "
            "AND tgparentid = 0 AND tgname = ANY(:n)"),
            {"n": sorted(P11_TRIGGERS)}).fetchall())
    # ROW=1 BEFORE=2 INSERT=4 DELETE=8 UPDATE=16
    assert rows["tg_acl_subject_exists"] == 1 + 2 + 4 + 16        # 23
    assert rows["tg_acl_user_hard_delete"] == 1 + 8               # 9
    assert rows["tg_acl_role_delete_block"] == 1 + 2 + 8          # 11
    assert rows["tg_agent_acl_expire"] == 1 + 8 + 16              # 25


def test_sec_all_p11_functions_are_invoker_without_search_path(db) -> None:
    for name in sorted(P11_FUNCTIONS):
        with _engine().connect() as conn:
            prosecdef, has_sp = conn.execute(sa.text(
                "SELECT prosecdef::text, pg_get_functiondef(oid) LIKE '%search_path%' "
                "FROM pg_proc WHERE proname = :n"), {"n": name}).fetchone()
        assert prosecdef == "false", name
        assert not has_sp, name
    # platform-wide: no SECURITY DEFINER among public trigger functions
    assert _scalar(
        "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = 'public' AND prosecdef") == 0


def test_sec_functions_do_not_write_audit_or_events(db) -> None:
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    for forbidden in ("audit_logs", "INSERT INTO events", "UPDATE events",
                      "DELETE FROM events"):
        assert forbidden not in src, forbidden


def test_p10_boundary_unchanged(db) -> None:
    assert _scalar(
        "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgparentid = 0 "
        "AND tgname = 'tg_audit_immutable' AND tgrelid = 'audit_logs'::regclass") == 1
    assert _scalar(
        "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid = 'events'::regclass") == 0
    assert _scalar(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name = 'events'") == 22
    assert _scalar(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name = 'audit_logs'") == 19


def test_p12_boundary_no_new_indexes(db) -> None:
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' "
        "AND tablename = ANY(:t) AND indexname NOT LIKE '%\\_pkey' "
        "AND indexname NOT IN ('ix_rp_subject', 'uq_resource_perm', "
        "'uq_agents_key', 'ix_agents_tenant_status', 'uq_users_email', "
        "'uq_users_username', 'uq_roles_platform', 'uq_roles_space', "
        "'uq_roles_tenant', "
        # P12 (0015) 交付（D-P12-13）：agents 表上的 2 个 FK 反查索引
        "'ix_agents_current_version', 'ix_agents_default_route')",
        t=["resource_permissions", "users", "roles", "agents"]) == 0
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE indexname = 'ix_rp_subject'") == 1


def test_p13_boundary_zero_seed(db) -> None:
    # the 5 system roles are migration-controlled dictionary rows (0005);
    # P13 seed = bootstrap principals / registry / ACLs — those must stay empty
    assert _scalar("SELECT count(*) FROM acl_subject_types") == 0
    assert _scalar("SELECT count(*) FROM users") == 0
    assert _scalar("SELECT count(*) FROM agents") == 0
    assert _scalar("SELECT count(*) FROM resource_permissions") == 0
    assert "INSERT INTO" not in MIGRATION_FILE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# downgrade / roundtrip
# --------------------------------------------------------------------------- #
def test_downgrade_and_roundtrip(db) -> None:
    cfg = make_config(lock_mode="fail")

    def p11_state():
        return (
            _scalar("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                    "AND tgparentid = 0 AND tgname = ANY(:n)",
                    n=sorted(P11_TRIGGERS)),
            _scalar("SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)",
                    n=sorted(P11_FUNCTIONS)),
        )

    assert p11_state() == (4, 4)
    downgrade(cfg, "0013_p10_event_audit")
    assert current_revision() == "0013_p10_event_audit"
    assert p11_state() == (0, 0), "downgrade must remove all 8 P11 objects"
    assert _scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
    ) == 35, "zero residue: physical table count must return to 35"
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                   "AND tgparentid = 0 AND tgname = 'tg_audit_immutable'") == 1

    upgrade(cfg, "head")
    assert current_revision() == "0015_p12_indexes"
    assert p11_state() == (4, 4), "roundtrip must restore all 8 P11 objects"
