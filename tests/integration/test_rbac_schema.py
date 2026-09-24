"""B1-3 RBAC schema tests — roles / permissions / role_permissions / platform_memberships.

Runs against the disposable test database (never the formal `uap` DB).
DB trigger RAISE surfaces as ProgrammingError; constraint violations as IntegrityError.
Every expected-failure statement runs inside a SAVEPOINT (begin_nested) so one failure
does not abort the surrounding transaction.
"""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Connection

from tests.integration.alembic_testkit import (
    BASE_DSN,
    current_revision,
    database_reachable,
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

AUTHORIZATION_TABLES = {
    "roles", "permissions", "role_permissions", "platform_memberships",
}
FUTURE_TABLES = {
    # P09 tables were delivered by 0011 (no longer future)
    "events", "audit_logs", "groups",
}


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0012_authz_enforcement"
    yield
    reset_test_database()


def _connect() -> tuple[sa.Engine, Connection]:
    engine = sa.create_engine(BASE_DSN)
    return engine, engine.connect()


def _fails(conn: Connection, exc, fn) -> None:
    """Run fn inside a savepoint and require it to raise `exc`."""
    try:
        with conn.begin_nested():
            fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__} but statement succeeded")


def _q(conn: Connection, sql: str, **params):
    """Read through the SAME connection (sees uncommitted work in the active tx)."""
    return [tuple(r) for r in conn.execute(sa.text(sql), params)]


def _rows(sql: str, **params):
    engine = sa.create_engine(BASE_DSN)
    try:
        with engine.connect() as c:
            return [tuple(r) for r in c.execute(sa.text(sql), params)]
    finally:
        engine.dispose()


def _ins(conn: Connection, table: str, **cols) -> uuid.UUID:
    keys = ", ".join(cols)
    binds = ", ".join(f":{k}" for k in cols)
    return conn.execute(
        sa.text(f"INSERT INTO {table} ({keys}) VALUES ({binds}) RETURNING id"),
        cols,
    ).scalar()


def _mk_role(conn: Connection, key: str, scope: str, tenant_id=None, space_id=None,
             status: str = "active", is_system: bool = False) -> uuid.UUID:
    return _ins(conn, "roles", key=key, name=key, scope=scope,
                tenant_id=tenant_id, space_id=space_id, status=status,
                is_system=is_system)


def _tenant(conn: Connection, slug: str, status: str = "active") -> uuid.UUID:
    return _ins(conn, "tenants", slug=slug, display_name=slug, status=status)


def _space(conn: Connection, tenant_id, key: str) -> uuid.UUID:
    return _ins(conn, "spaces", tenant_id=tenant_id, key=key, name=key, kind="home",
                visibility="private", status="active")


def _user(conn: Connection, name: str, status: str = "active") -> uuid.UUID:
    return _ins(conn, "users", username=name, status=status)


def _ins_rp(conn: Connection, role_id, permission_id, effect: str, conditions=None) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id, effect, conditions) "
            "VALUES (:r, :p, :e, :c)"
        ),
        {"r": role_id, "p": permission_id, "e": effect, "c": conditions},
    )


def _flip_bootstrap(conn: Connection) -> None:
    """0006: first PM insert happens under uninitialized+empty; flip state to allow further grants."""
    conn.execute(sa.text(
        "UPDATE platform_state SET bootstrap_state='initialized', initialized_at=now() WHERE id=1"
    ))


def _platform_admin_id(conn: Connection) -> uuid.UUID:
    return conn.execute(sa.text(
        "SELECT id FROM roles WHERE scope='PLATFORM' AND key='platform_admin'"
    )).scalar()


# --------------------------------------------------------------------------- #
# 1. schema + seed + roles 约束
# --------------------------------------------------------------------------- #

def test_schema_tables_seed_and_basics(db) -> None:
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert AUTHORIZATION_TABLES <= tables
    assert tables.isdisjoint(FUTURE_TABLES)
    (cnt,) = _rows("SELECT count(*) FROM roles WHERE key='platform_admin'")[0]
    assert cnt == 1
    engine, conn = _connect()
    try:
        conn.begin()
        t1 = _tenant(conn, "ck-tenant")
        # key CK fires (shape is valid) → IntegrityError
        _fails(conn, sa.exc.IntegrityError,
               lambda: _mk_role(conn, "Bad-Key!", "TENANT", tenant_id=t1))
        # invalid scope is caught by the shape trigger (runs before CK) → ProgrammingError
        _fails(conn, sa.exc.ProgrammingError, lambda: _mk_role(conn, "ok_key", "GLOBAL"))
        conn.commit()
    finally:
        conn.close(); engine.dispose()


def test_role_scope_shape_trigger(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        _fails(conn, sa.exc.ProgrammingError,
               lambda: _mk_role(conn, "bad_p", "PLATFORM", tenant_id=uuid.uuid4()))
        _fails(conn, sa.exc.ProgrammingError, lambda: _mk_role(conn, "bad_t", "TENANT"))
        _fails(conn, sa.exc.ProgrammingError,
               lambda: _mk_role(conn, "bad_s", "SPACE", tenant_id=uuid.uuid4()))
        conn.commit()
    finally:
        conn.close(); engine.dispose()


def test_role_unique_predicates_and_archive_key(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            t1 = _tenant(conn, "ten-x")
            t2 = _tenant(conn, "ten-y")
            r_ten1 = _mk_role(conn, "ops", "TENANT", tenant_id=t1)
            # same key, same tenant → rejected
            _fails(conn, sa.exc.IntegrityError, lambda: _mk_role(conn, "ops", "TENANT", tenant_id=t1))
            # same key, different tenant → allowed (scope-scoped uniqueness)
            _mk_role(conn, "ops", "TENANT", tenant_id=t2)
            # TENANT namespace may reuse the PLATFORM key text (no global reserved key)
            _mk_role(conn, "platform_admin", "TENANT", tenant_id=t2)
            # second PLATFORM-scope platform_admin → rejected
            _fails(conn, sa.exc.IntegrityError, lambda: _mk_role(conn, "platform_admin", "PLATFORM"))
            # archive keeps the key reserved; delete frees it
            conn.execute(sa.text("UPDATE roles SET status='archived', archived_at=now() WHERE id=:i"),
                         {"i": r_ten1})
            _fails(conn, sa.exc.IntegrityError, lambda: _mk_role(conn, "ops", "TENANT", tenant_id=t1))
            conn.execute(sa.text("DELETE FROM roles WHERE id=:i"), {"i": r_ten1})
            _mk_role(conn, "ops", "TENANT", tenant_id=t1)
    finally:
        conn.close(); engine.dispose()


def test_system_role_protection(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            pa = _platform_admin_id(conn)
            t1 = _tenant(conn, "ten-z")
            custom = _mk_role(conn, "custom1", "TENANT", tenant_id=t1)
            # runtime INSERT is_system=true → reject
            _fails(conn, sa.exc.ProgrammingError,
                   lambda: _mk_role(conn, "rogue", "TENANT", tenant_id=t1, is_system=True))
            # system role row immutable: status / is_system / DELETE
            _fails(conn, sa.exc.ProgrammingError,
                   lambda: conn.execute(sa.text("UPDATE roles SET status='disabled' WHERE id=:i"), {"i": pa}))
            _fails(conn, sa.exc.ProgrammingError,
                   lambda: conn.execute(sa.text("UPDATE roles SET is_system=false WHERE id=:i"), {"i": pa}))
            _fails(conn, sa.exc.ProgrammingError,
                   lambda: conn.execute(sa.text("DELETE FROM roles WHERE id=:i"), {"i": pa}))
            # custom role promotion false→true → reject
            _fails(conn, sa.exc.ProgrammingError,
                   lambda: conn.execute(sa.text("UPDATE roles SET is_system=true WHERE id=:i"), {"i": custom}))
            # unreferenced custom role remains editable/deletable
            conn.execute(sa.text("UPDATE roles SET name='renamed' WHERE id=:i"), {"i": custom})
            conn.execute(sa.text("DELETE FROM roles WHERE id=:i"), {"i": custom})
    finally:
        conn.close(); engine.dispose()


# --------------------------------------------------------------------------- #
# 2. membership role binding
# --------------------------------------------------------------------------- #

def test_membership_role_scope_bindings(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            u = _user(conn, "u1")
            t1 = _tenant(conn, "t-one")
            t2 = _tenant(conn, "t-two")
            s1 = _space(conn, t1, "s1")
            s2 = _space(conn, t1, "s2")
            tr1 = _mk_role(conn, "mgr", "TENANT", tenant_id=t1)
            tr2 = _mk_role(conn, "mgr", "TENANT", tenant_id=t2)
            sr1 = _mk_role(conn, "lead", "SPACE", space_id=s1)
            sr2 = _mk_role(conn, "lead", "SPACE", space_id=s2)
            pa = _platform_admin_id(conn)
            # valid same-tenant TENANT / same-space SPACE bindings
            _ins(conn, "tenant_memberships", tenant_id=t1, user_id=u, role_id=tr1, status="active")
            _ins(conn, "memberships", tenant_id=t1, space_id=s1, user_id=u, role_id=sr1, status="active")
            # TM → SPACE / other-tenant / PLATFORM / missing role → reject
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "tenant_memberships", tenant_id=t1, user_id=u, role_id=sr1, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "tenant_memberships", tenant_id=t1, user_id=u, role_id=tr2, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "tenant_memberships", tenant_id=t1, user_id=u, role_id=pa, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "tenant_memberships", tenant_id=t1, user_id=u, role_id=uuid.uuid4(), status="active"))
            # M → TENANT / other-space / PLATFORM / missing → reject
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "memberships", tenant_id=t1, space_id=s1, user_id=u, role_id=tr1, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "memberships", tenant_id=t1, space_id=s1, user_id=u, role_id=sr2, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "memberships", tenant_id=t1, space_id=s1, user_id=u, role_id=pa, status="active"))
            # disabled role cannot be bound
            disabled = _mk_role(conn, "frozen", "TENANT", tenant_id=t1, status="disabled")
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "tenant_memberships", tenant_id=t1, user_id=u, role_id=disabled, status="active"))
    finally:
        conn.close(); engine.dispose()


def test_backfill_on_upgrade_with_existing_0004_data() -> None:
    reset_test_database()
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "0004_b1_2_tenant_space")
    engine, conn = _connect()
    try:
        with conn.begin():
            u1 = _user(conn, "a1")
            u2 = _user(conn, "a2")
            t_active = _tenant(conn, "live-t")
            t_arch = _tenant(conn, "dead-t", status="archived")
            sp = _space(conn, t_active, "sp1")
            _ins(conn, "tenant_memberships", tenant_id=t_active, user_id=u1, status="active")
            _ins(conn, "tenant_memberships", tenant_id=t_arch, user_id=u2, status="removed")
            _ins(conn, "memberships", tenant_id=t_active, space_id=sp, user_id=u1, status="active")
    finally:
        conn.close(); engine.dispose()
    upgrade(cfg, "head")
    assert current_revision() == "0012_authz_enforcement"
    rows = _rows("SELECT r.key, tm.status FROM tenant_memberships tm "
                 "JOIN roles r ON tm.role_id = r.id ORDER BY tm.status")
    assert rows == [("tenant_member", "active"), ("tenant_member", "removed")]
    rows = _rows("SELECT r.key, m.status FROM memberships m JOIN roles r ON m.role_id = r.id")
    assert rows == [("space_member", "active")]
    (nulls,) = _rows("SELECT count(*) FROM tenant_memberships WHERE role_id IS NULL")[0]
    assert nulls == 0


def test_backfill_invalid_role_id_fails_closed_and_rolls_back() -> None:
    reset_test_database()
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "0004_b1_2_tenant_space")
    engine, conn = _connect()
    try:
        with conn.begin():
            u = _user(conn, "b1")
            t = _tenant(conn, "bogus-t")
            # 0004 has no FK: an arbitrary role_id is expressible
            _ins(conn, "tenant_memberships", tenant_id=t, user_id=u,
                 role_id=uuid.uuid4(), status="active")
    finally:
        conn.close(); engine.dispose()
    with pytest.raises(Exception, match="backfill validation failed"):
        upgrade(cfg, "head")
    assert current_revision() == "0004_b1_2_tenant_space", "must roll back atomically"


# --------------------------------------------------------------------------- #
# 3. permissions + role_permissions
# --------------------------------------------------------------------------- #

def test_permissions_and_role_permissions(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            t1 = _tenant(conn, "perm-t")
            r = _mk_role(conn, "manager", "TENANT", tenant_id=t1)
            _fails(conn, sa.exc.IntegrityError,
                   lambda: _ins(conn, "permissions", key="Bad Key", action="read"))
            p_allow = _ins(conn, "permissions", key="task.read", action="read", is_system=True)
            p_deny = _ins(conn, "permissions", key="task.delete", action="delete")
            _fails(conn, sa.exc.IntegrityError,
                   lambda: _ins(conn, "permissions", key="task.read", action="read"))
            # composite PK includes effect: allow + deny coexist for the same pair
            _ins_rp(conn, r, p_allow, "allow")
            _ins_rp(conn, r, p_allow, "deny")
            _ins_rp(conn, r, p_deny, "allow")
            _fails(conn, sa.exc.IntegrityError,
                   lambda: _ins_rp(conn, r, p_allow, "deny"))
            _fails(conn, sa.exc.IntegrityError,
                   lambda: _ins_rp(conn, r, p_allow, "maybe"))
            # permission DELETE cascades its role_permissions; role DELETE does the same
            conn.execute(sa.text("DELETE FROM permissions WHERE id=:i"), {"i": p_deny})
            assert _q(conn, "SELECT count(*) FROM role_permissions WHERE permission_id=:i",
                      i=p_deny)[0][0] == 0
            conn.execute(sa.text("DELETE FROM roles WHERE id=:i"), {"i": r})
            assert _q(conn, "SELECT count(*) FROM role_permissions WHERE role_id=:i",
                      i=r)[0][0] == 0
    finally:
        conn.close(); engine.dispose()


# --------------------------------------------------------------------------- #
# 4. DENY > ALLOW semantics (pure data-layer rule; interpreter lives in authz layer)
# --------------------------------------------------------------------------- #

def _decide(rows) -> str:
    """DENY > ALLOW + default-deny interpreter used by tests until the engine exists."""
    if any(e == "deny" for e in rows):
        return "deny"
    if any(e == "allow" for e in rows):
        return "allow"
    return "deny"


def test_deny_over_allow_semantics() -> None:
    assert _decide(["allow"]) == "allow"
    assert _decide(["deny"]) == "deny"
    assert _decide(["allow", "deny"]) == "deny"            # same (role, permission)
    assert _decide(["allow", "allow", "deny"]) == "deny"   # multiple roles, one deny
    assert _decide([]) == "deny"                           # no matching rule → DENY


# --------------------------------------------------------------------------- #
# 5. platform_memberships
# --------------------------------------------------------------------------- #

def test_pm_lifecycle_bootstrap_regrant_history(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            pa = _platform_admin_id(conn)
            u1 = _user(conn, "p1")
            u2 = _user(conn, "p2")
            # bootstrap: first insert allowed (0 → 1)
            pm1 = _ins(conn, "platform_memberships", user_id=u1, role_id=pa, status="active")
            _flip_bootstrap(conn)  # 首行为 bootstrap → 状态翻转后后续 grant 可行
            # multi-admin: second user may hold the same platform role (PMB-1 needs >1 for revoke tests)
            pm2 = _ins(conn, "platform_memberships", user_id=u2, role_id=pa, status="active")
            # duplicate active binding for the same user → partial unique rejects
            _fails(conn, sa.exc.IntegrityError, lambda: _ins(
                conn, "platform_memberships", user_id=u1, role_id=pa, status="active"))
            # revoke (another admin remains) → re-INSERT duplicate row rejected by (user_id, role_id)
            conn.execute(sa.text(
                "UPDATE platform_memberships SET status='revoked', revoked_at=now() WHERE id=:i"
            ), {"i": pm1})
            _fails(conn, sa.exc.IntegrityError, lambda: _ins(
                conn, "platform_memberships", user_id=u1, role_id=pa, status="active"))
            # re-grant = UPDATE same row; created_at unchanged
            (created0,) = _q(conn, "SELECT created_at FROM platform_memberships WHERE id=:i",
                              i=pm1)[0]
            conn.execute(sa.text(
                "UPDATE platform_memberships SET status='active', revoked_at=NULL WHERE id=:i"
            ), {"i": pm1})
            row = _q(
                conn,
                "SELECT status, revoked_at IS NULL, created_at = :c "
                "FROM platform_memberships WHERE id=:i", i=pm1, c=created0,
            )[0]
            assert row == ("active", True, True)
            assert _q(conn, "SELECT count(*) FROM platform_memberships WHERE user_id=:u AND role_id=:r",
                       u=u1, r=pa)[0][0] == 1  # single historical row ever
            # hard delete of the second user cascades its membership (purge-only path)
            conn.execute(sa.text("DELETE FROM users WHERE id=:i"), {"i": u2})
            assert _q(conn, "SELECT count(*) FROM platform_memberships WHERE id=:i",
                      i=pm2)[0][0] == 0
    finally:
        conn.close(); engine.dispose()


def test_pm_scope_and_user_guards(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            u = _user(conn, "p3")
            t1 = _tenant(conn, "pm-t")
            sp = _space(conn, t1, "pmsp")
            tr = _mk_role(conn, "tm_member", "TENANT", tenant_id=t1)
            sr = _mk_role(conn, "sm_member", "SPACE", space_id=sp)
            custom_p = _mk_role(conn, "auditor", "PLATFORM")
            # PM cannot reference TENANT / SPACE / missing roles
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "platform_memberships", user_id=u, role_id=tr, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "platform_memberships", user_id=u, role_id=sr, status="active"))
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "platform_memberships", user_id=u, role_id=uuid.uuid4(), status="active"))
            # custom PLATFORM role binding works, then role disable blocks NEW bindings
            _ins(conn, "platform_memberships", user_id=u, role_id=custom_p, status="active")
            conn.execute(sa.text("UPDATE roles SET status='disabled' WHERE id=:i"),
                         {"i": custom_p})
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "platform_memberships", user_id=u, role_id=custom_p, status="active"))
            # inactive user cannot be bound to a platform role
            u_inactive = _user(conn, "p4", status="suspended")
            _fails(conn, sa.exc.ProgrammingError, lambda: _ins(
                conn, "platform_memberships", user_id=u_inactive,
                role_id=_platform_admin_id(conn), status="active"))
    finally:
        conn.close(); engine.dispose()


def test_pm_last_admin_and_role_lifecycle(db) -> None:
    engine, conn = _connect()
    try:
        with conn.begin():
            pa = _platform_admin_id(conn)
            ua = _user(conn, "la")
            ub = _user(conn, "lb")
            pm_a = _ins(conn, "platform_memberships", user_id=ua, role_id=pa, status="active")
            _flip_bootstrap(conn)
            pm_b = _ins(conn, "platform_memberships", user_id=ub, role_id=pa, status="active")
            # revoke one admin → allowed while another remains
            conn.execute(sa.text(
                "UPDATE platform_memberships SET status='revoked', revoked_at=now() WHERE id=:i"
            ), {"i": pm_b})
            # revoking / deleting / hard-deleting the user of the LAST admin → rejected
            _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
                "UPDATE platform_memberships SET status='revoked', revoked_at=now() WHERE id=:i"
            ), {"i": pm_a}))
            _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
                "DELETE FROM platform_memberships WHERE id=:i"), {"i": pm_a}))
            _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
                "DELETE FROM users WHERE id=:i"), {"i": ua}))
            # role-side: system platform_admin row is immutable (T3 + PMB-1)
            _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
                "UPDATE roles SET status='disabled' WHERE id=:i"), {"i": pa}))
            _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
                "DELETE FROM roles WHERE id=:i"), {"i": pa}))
            # two admins again → revoking the first is now allowed
            conn.execute(sa.text(
                "UPDATE platform_memberships SET status='active', revoked_at=NULL WHERE id=:i"
            ), {"i": pm_b})
            conn.execute(sa.text(
                "UPDATE platform_memberships SET status='revoked', revoked_at=now() WHERE id=:i"
            ), {"i": pm_a})
            assert _q(conn, "SELECT count(*) FROM platform_memberships WHERE status='active'")[0][0] == 1
    finally:
        conn.close(); engine.dispose()


def test_pm_user_deactivation_does_not_auto_revoke(db) -> None:
    """PMB-4: no users→platform_memberships auto-revoke trigger at the DB; a deactivation
    workflow must revoke first. User inactivity alone is an authorization-layer DENY."""
    engine, conn = _connect()
    try:
        with conn.begin():
            u = _user(conn, "life")
            _ins(conn, "platform_memberships", user_id=u,
                 role_id=_platform_admin_id(conn), status="active")
            conn.execute(sa.text("UPDATE users SET status='suspended' WHERE id=:i"), {"i": u})
            (rows,) = _q(
                conn,
                "SELECT count(*) FROM platform_memberships pm "
                "JOIN users u ON u.id = pm.user_id "
                "WHERE pm.status='active' AND u.status='suspended'",
            )[0]
            assert rows == 1  # effective == 0 is an authorization-layer decision
    finally:
        conn.close(); engine.dispose()
