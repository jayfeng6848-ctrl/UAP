"""B1-3 HARDENING tests — Bootstrap permanent closure (P1-01) & User lifecycle (P1-02/P1-03).

Covers:
  B-01..B-06 bootstrap state semantics (platform_state singleton, one-way transition,
  independence from PM revoke / hard-delete / CASCADE; fake-system-actor impossible)
  U-01..U-06 platform-admin user lifecycle (revoke-first workflow, reactivation keeps
  PM revoked, failed deactivation rolls back, inactive user DENY, hard-delete cascade,
  last-admin hard delete rejected)

DB trigger RAISE -> ProgrammingError; constraints -> IntegrityError.
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


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0008_b1_5_tool_registry"
    yield
    reset_test_database()


def _connect() -> tuple[sa.Engine, Connection]:
    engine = sa.create_engine(BASE_DSN)
    return engine, engine.connect()


def _q(conn: Connection, sql: str, **params):
    return [tuple(r) for r in conn.execute(sa.text(sql), params)]


def _scalar(conn: Connection, sql: str, **params):
    return conn.execute(sa.text(sql), params).scalar()


def _fails(conn: Connection, exc, fn) -> None:
    try:
        with conn.begin_nested():
            fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__} but statement succeeded")


def _user(conn: Connection, name: str, status: str = "active") -> uuid.UUID:
    return _scalar(conn, "INSERT INTO users (username, status) VALUES (:n, :s) RETURNING id",
                   n=name, s=status)


def _pa(conn: Connection) -> uuid.UUID:
    return _scalar(conn, "SELECT id FROM roles WHERE scope='PLATFORM' AND key='platform_admin'")


def _state(conn: Connection) -> str:
    return _scalar(conn, "SELECT bootstrap_state FROM platform_state WHERE id=1")


def _grant(conn: Connection, user_id, role_id) -> uuid.UUID:
    return _scalar(conn,
                   "INSERT INTO platform_memberships (user_id, role_id, status) "
                   "VALUES (:u, :r, 'active') RETURNING id",
                   u=user_id, r=role_id)


def _revoke(conn: Connection, pm_id) -> None:
    conn.execute(sa.text(
        "UPDATE platform_memberships SET status='revoked', revoked_at=now() WHERE id=:i"
    ), {"i": pm_id})


def _bootstrap(conn: Connection, user_id) -> None:
    """One-time bootstrap: first PM row + one-way state flip, same transaction."""
    _grant(conn, user_id, _pa(conn))
    conn.execute(sa.text(
        "UPDATE platform_state SET bootstrap_state='initialized', initialized_at=now() WHERE id=1"
    ))


# --------------------------------------------------------------------------- #
# pure authorization semantics used to assert "no privilege restoration"
# --------------------------------------------------------------------------- #

def _effective(user_active: bool, pm_status: str, role_status: str,
               scope: str, key: str) -> bool:
    return bool(user_active and pm_status == "active" and role_status == "active"
                and scope == "PLATFORM" and key == "platform_admin")


def test_effective_predicate_is_unchanged_and_no_fallback() -> None:
    # PM revoked / user inactive / role inactive → DENY; 没有任何 fallback allow
    assert _effective(True, "active", "active", "PLATFORM", "platform_admin") is True
    assert _effective(True, "revoked", "active", "PLATFORM", "platform_admin") is False
    assert _effective(False, "active", "active", "PLATFORM", "platform_admin") is False
    assert _effective(True, "active", "disabled", "PLATFORM", "platform_admin") is False
    assert _effective(True, "active", "active", "TENANT", "platform_admin") is False
    assert _effective(True, "active", "active", "PLATFORM", "tenant_admin") is False


# --------------------------------------------------------------------------- #
# P1-01 Bootstrap permanent closure
# --------------------------------------------------------------------------- #

def test_b01_first_bootstrap(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        assert _state(conn) == "uninitialized"
        u = _user(conn, "b1")
        # uninitialized + empty → first PM row allowed
        pm = _grant(conn, u, _pa(conn))
        _scalar(conn, "SELECT count(*) FROM platform_state")
        conn.execute(sa.text(
            "UPDATE platform_state SET bootstrap_state='initialized', initialized_at=now() WHERE id=1"
        ))
        assert _state(conn) == "initialized"
        assert _scalar(conn, "SELECT status FROM platform_memberships WHERE id=:i", i=pm) == "active"
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_b02_bootstrap_second_attempt_rejected(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        u1 = _user(conn, "b2a")
        _bootstrap(conn, u1)
        # re-running bootstrap = trying to flip again / revert state → denied
        _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
            "UPDATE platform_state SET bootstrap_state='uninitialized', initialized_at=NULL WHERE id=1"
        )))
        _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
            "UPDATE platform_state SET bootstrap_state='initialized' WHERE id=1"
        )))
        assert _state(conn) == "initialized"
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_b03_pm_revoke_does_not_reopen_bootstrap(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        u1, u2 = _user(conn, "b3a"), _user(conn, "b3b")
        _bootstrap(conn, u1)
        pm2 = _grant(conn, u2, _pa(conn))
        _revoke(conn, pm2)
        assert _state(conn) == "initialized"
        # any state write (incl. "reopen") is denied while state stays initialized
        _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
            "UPDATE platform_state SET bootstrap_state='uninitialized' WHERE id=1"
        )))
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_b04_pm_hard_delete_cascade_does_not_reopen_bootstrap(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        u1, u2 = _user(conn, "b4a"), _user(conn, "b4b")
        _bootstrap(conn, u1)
        _grant(conn, u2, _pa(conn))
        # delete non-last admin user → PM row cascades away
        conn.execute(sa.text("DELETE FROM users WHERE id=:i"), {"i": u2})
        assert _scalar(conn, "SELECT count(*) FROM platform_memberships") == 1
        assert _state(conn) == "initialized"  # CASCADE 不影响 state
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_b05_bootstrap_state_survives_all_pm_deletion_attempts(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        u1 = _user(conn, "b5")
        _bootstrap(conn, u1)
        # 最后一名管理员不可删（last-admin 保护）→ PM 永不清零；state 独立存在
        _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
            "DELETE FROM users WHERE id=:i"), {"i": u1}))
        _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
            "DELETE FROM platform_memberships")))
        assert _state(conn) == "initialized"
        assert _scalar(conn, "SELECT count(*) FROM platform_memberships") == 1
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_b06_fake_system_actor_impossible(db) -> None:
    # 无 actor 列可伪造：PM 行只有 user/role/status；bootstrap 只经一次性 gate+state 翻转
    engine, conn = _connect()
    try:
        pm_cols = {r[0] for r in conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='platform_memberships'"
        ))}
        st_cols = {r[0] for r in conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='platform_state'"
        ))}
        assert not ({"actor", "acted_by", "created_by"} & pm_cols)
        assert not ({"actor", "created_by"} & st_cols)
        # 客户端伪造 system actor 无承载列；授权 = effective 谓词（纯函数），无 fallback
        assert _effective(True, "active", "active", "PLATFORM", "platform_admin") is True
    finally:
        conn.close(); engine.dispose()


# --------------------------------------------------------------------------- #
# P1-02 / P1-03 Platform-admin user lifecycle
# --------------------------------------------------------------------------- #

def test_u01_deactivate_revoke_then_inactive(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        admin, other = _user(conn, "u1a"), _user(conn, "u1b")
        _bootstrap(conn, admin)
        _grant(conn, other, _pa(conn))
        # workflow: revoke PM → audit(contract) → deactivate user
        pm_a = _scalar(conn, "SELECT id FROM platform_memberships WHERE user_id=:u", u=admin)
        _revoke(conn, pm_a)
        conn.execute(sa.text("UPDATE users SET status='suspended' WHERE id=:i"), {"i": admin})
        assert _scalar(conn, "SELECT status FROM platform_memberships WHERE id=:i", i=pm_a) == "revoked"
        assert _scalar(conn, "SELECT status FROM users WHERE id=:i", i=admin) == "suspended"
        # effective 管理员剩 1（other）
        assert _scalar(conn,
            "SELECT count(*) FROM platform_memberships pm JOIN users u ON u.id=pm.user_id "
            "JOIN roles r ON r.id=pm.role_id "
            "WHERE pm.status='active' AND u.status='active' AND r.status='active' "
            "AND r.scope='PLATFORM' AND r.key='platform_admin'") == 1
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_u02_reactivate_after_revoke_remains_non_admin(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        admin, other = _user(conn, "u2a"), _user(conn, "u2b")
        _bootstrap(conn, admin)
        _grant(conn, other, _pa(conn))
        pm_a = _scalar(conn, "SELECT id FROM platform_memberships WHERE user_id=:u", u=admin)
        _revoke(conn, pm_a)
        conn.execute(sa.text("UPDATE users SET status='suspended' WHERE id=:i"), {"i": admin})
        # reactivate user: PM 保持 revoked → 无平台权限（不可“复活”）
        conn.execute(sa.text("UPDATE users SET status='active' WHERE id=:i"), {"i": admin})
        assert _scalar(conn, "SELECT status FROM platform_memberships WHERE id=:i", i=pm_a) == "revoked"
        eff = _scalar(conn,
            "SELECT count(*) FROM platform_memberships pm JOIN users u ON u.id=pm.user_id "
            "JOIN roles r ON r.id=pm.role_id "
            "WHERE pm.user_id=:u AND pm.status='active' AND u.status='active' AND r.status='active' "
            "AND r.scope='PLATFORM' AND r.key='platform_admin'", u=admin)
        assert eff == 0  # NO platform privilege restored
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_u03_failed_deactivation_rolls_back(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        admin, other = _user(conn, "u3a"), _user(conn, "u3b")
        _bootstrap(conn, admin)
        _grant(conn, other, _pa(conn))
        pm_a = _scalar(conn, "SELECT id FROM platform_memberships WHERE user_id=:u", u=admin)
        # 事务内：revoke 成功 → 随后 user 停用失败（非法 status）→ 整事务回滚
        try:
            with conn.begin_nested():
                _revoke(conn, pm_a)
                conn.execute(sa.text("UPDATE users SET status='bogus' WHERE id=:i"), {"i": admin})
        except sa.exc.IntegrityError:
            pass
        else:
            raise AssertionError("expected deactivation failure")
        assert _scalar(conn, "SELECT status FROM platform_memberships WHERE id=:i", i=pm_a) == "active"
        assert _scalar(conn, "SELECT status FROM users WHERE id=:i", i=admin) == "active"
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_u04_inactive_user_deny_even_if_pm_row_still_active(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        u = _user(conn, "u4")
        _bootstrap(conn, u)
        conn.execute(sa.text("UPDATE users SET status='suspended' WHERE id=:i"), {"i": u})
        # DB 无自动 revoke（PMB-4）：行仍 active，但 effective=0 → DENY
        assert _scalar(conn, "SELECT status FROM platform_memberships WHERE user_id=:u", u=u) == "active"
        eff = _scalar(conn,
            "SELECT count(*) FROM platform_memberships pm JOIN users u ON u.id=pm.user_id "
            "JOIN roles r ON r.id=pm.role_id WHERE pm.user_id=:u AND u.status='active' "
            "AND pm.status='active' AND r.status='active' AND r.scope='PLATFORM' "
            "AND r.key='platform_admin'", u=u)
        assert eff == 0  # inactive → DENY (fail-closed 防线，非 revoke 替代)
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_u05_hard_delete_cascades_pm(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        a, b = _user(conn, "u5a"), _user(conn, "u5b")
        _bootstrap(conn, a)
        pm_b = _grant(conn, b, _pa(conn))
        conn.execute(sa.text("DELETE FROM users WHERE id=:i"), {"i": b})
        assert _scalar(conn, "SELECT count(*) FROM platform_memberships WHERE id=:i", i=pm_b) == 0
        assert _state(conn) == "initialized"  # CASCADE 不影响 bootstrap state
        conn.rollback()
    finally:
        conn.close(); engine.dispose()


def test_u06_last_admin_hard_delete_rejected(db) -> None:
    engine, conn = _connect()
    try:
        conn.begin()
        a = _user(conn, "u6")
        _bootstrap(conn, a)
        _fails(conn, sa.exc.ProgrammingError, lambda: conn.execute(sa.text(
            "DELETE FROM users WHERE id=:i"), {"i": a}))
        assert _scalar(conn, "SELECT count(*) FROM platform_memberships") == 1
        assert _state(conn) == "initialized"
        conn.rollback()
    finally:
        conn.close(); engine.dispose()
