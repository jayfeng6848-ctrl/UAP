"""B1-1 Identity schema acceptance checks (Test A–E style + security).

Run against the disposable ``uap_b1_test`` database only. Never touches the
formal ``uap`` database.

Covers
  * Test A fresh upgrade head -> exactly the 5 identity tables (+ metadata)
  * Test B schema inspection: PK / FK / UNIQUE / CHECK / NOT NULL / DEFAULT /
    INDEX / ON DELETE / triggers vs the frozen B0 CONSTRAINT_MATRIX
  * Test C rerun idempotency (covered here via double upgrade guard)
  * Test D downgrade then re-upgrade round trip
  * Identity security: duplicate / FK / plaintext forbidden / partial uniques
"""

from __future__ import annotations

import datetime as _dt
import uuid as _uuid

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

IDENTITY_TABLES = {"users", "identities", "credentials", "devices", "sessions"}
# B1-2 delivered tenants/spaces/memberships; B1-3 delivered roles/permissions/role_permissions/
# platform_memberships — none of those are "forbidden" any more.
FORBIDDEN_BUSINESS_TABLES = {
    "agents", "agent_versions", "agent_permissions",
    "tool_executions",
    "ai_providers", "ai_models", "ai_routes", "ai_policies", "ai_request_logs",
    "events", "audit_logs",
}


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0009_timestamp_precision"
    yield
    reset_test_database()


def _conn():
    engine = sa.create_engine(BASE_DSN)
    return engine, engine.connect()


def _scalar(sql: str, **params):
    engine, conn = _conn()
    try:
        return conn.execute(sa.text(sql), params).scalar()
    finally:
        conn.close()
        engine.dispose()


def _rows(sql: str, **params):
    engine, conn = _conn()
    try:
        return conn.execute(sa.text(sql), params).fetchall()
    finally:
        conn.close()
        engine.dispose()


def _insert(table: str, conn, **cols) -> _uuid.UUID:
    names = ", ".join(cols)
    binds = ", ".join(f":{k}" for k in cols)
    row = conn.execute(
        sa.text(f"INSERT INTO {table} ({names}) VALUES ({binds}) RETURNING id"),
        cols,
    ).one()
    return row[0]


# ============================================================ Test A
def test_fresh_db_has_exactly_identity_tables(db) -> None:
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )}
    # B1-1 identity tables must all be present...
    assert IDENTITY_TABLES <= tables
    # ...and no forbidden business tables may exist.
    # (tenants/spaces/memberships are delivered by B1-2 and are therefore allowed)
    assert tables.isdisjoint(FORBIDDEN_BUSINESS_TABLES)


# ============================================================ Test B: structure
def test_pk_uuid_default(db) -> None:
    for t in sorted(IDENTITY_TABLES):
        row = _rows(
            """
            SELECT a.attname, t.typname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            JOIN pg_class c ON c.oid = i.indrelid
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE i.indisprimary AND c.relname = :t
            """,
            t=t,
        )
        assert row and row[0][0] == "id" and row[0][1] == "uuid", (t, row)


def test_users_constraints_and_defaults(db) -> None:
    # status NOT NULL, email/username nullable, failed_attempts default 0
    assert _scalar("SELECT is_nullable FROM information_schema.columns WHERE table_name='users' AND column_name='status'") == "NO"
    for col in ("email", "username", "display_name", "deleted_at"):
        assert _scalar("SELECT is_nullable FROM information_schema.columns WHERE table_name='users' AND column_name=:c", c=col) == "YES"
    assert _scalar("SELECT column_default FROM information_schema.columns WHERE table_name='users' AND column_name='failed_attempts'") == "0"
    # partial unique indexes on lower(email)/lower(username)
    idx = {r[0]: r[1] for r in _rows("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='users'")}
    assert "uq_users_email" in idx and "WHERE (deleted_at IS NULL)" in idx["uq_users_email"]
    assert "uq_users_username" in idx and "lower(username)" in idx["uq_users_username"]
    # CHECKs
    cks = {r[0] for r in _rows("SELECT conname FROM pg_constraint WHERE conrelid='users'::regclass AND contype='c'")}
    assert {"ck_users_status", "ck_users_login"} <= cks


def test_identities_fk_unique_checks(db) -> None:
    # FK user CASCADE
    rules = {r[0]: r[1] for r in _rows(
        "SELECT rc.constraint_name, rc.delete_rule FROM information_schema.referential_constraints rc "
        "JOIN information_schema.table_constraints tc USING (constraint_name) WHERE tc.table_name='identities'"
    )}
    assert rules.get("fk_identities_user") == "CASCADE"
    uq = {r[0] for r in _rows("SELECT indexname FROM pg_indexes WHERE tablename='identities'")}
    assert {"uq_identities_ref", "uq_identities_email", "ix_identities_user"} <= uq
    cks = {r[0] for r in _rows("SELECT conname FROM pg_constraint WHERE conrelid='identities'::regclass AND contype='c'")}
    assert {"ck_identities_provider", "ck_identities_status"} <= cks


def test_credentials_no_plaintext_and_active_password_unique(db) -> None:
    # Schema must NOT contain plaintext-ish columns.
    cols = [r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns WHERE table_name='credentials'"
    )]
    assert "secret_hash" in cols
    for forbidden in ("plaintext_password", "plaintext_secret", "api_key", "password", "token"):
        assert forbidden not in cols, f"forbidden plaintext column: {forbidden}"
    assert _scalar("SELECT is_nullable FROM information_schema.columns WHERE table_name='credentials' AND column_name='secret_hash'") == "NO"
    idx = {r[0] for r in _rows("SELECT indexname FROM pg_indexes WHERE tablename='credentials'")}
    assert "uq_credentials_active_password" in idx
    assert "ix_credentials_user" in idx
    cks = {r[0] for r in _rows("SELECT conname FROM pg_constraint WHERE conrelid='credentials'::regclass AND contype='c'")}
    assert {"ck_credentials_type", "ck_credentials_algorithm", "ck_credentials_secret"} <= cks


def test_devices_sessions_fk_delete_rules(db) -> None:
    def rule(constraint: str):
        return _scalar(
            "SELECT rc.delete_rule FROM information_schema.referential_constraints rc "
            "WHERE rc.constraint_name = :c",
            c=constraint,
        )

    assert rule("fk_devices_user") == "CASCADE"
    assert rule("fk_sessions_user") == "CASCADE"
    assert rule("fk_sessions_identity") == "RESTRICT"
    assert rule("fk_sessions_device") == "CASCADE"
    idx = {r[0] for r in _rows("SELECT indexname FROM pg_indexes WHERE tablename='sessions'")}
    assert {"uq_sessions_token", "uq_sessions_refresh", "ix_sessions_user_status",
            "ix_sessions_identity", "ix_sessions_device", "ix_sessions_expires_active"} <= idx
    cks = {r[0] for r in _rows("SELECT conname FROM pg_constraint WHERE conrelid='sessions'::regclass AND contype='c'")}
    assert {"ck_sessions_status", "ck_sessions_expiry"} <= cks


def test_updated_at_triggers_present(db) -> None:
    names = {r[0] for r in _rows(
        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid = ANY (ARRAY['users','identities','credentials','devices','sessions']::regclass[])"
    )}
    expected = {f"tg_{t}_set_updated_at" for t in IDENTITY_TABLES}
    assert expected <= names, names


def test_updated_at_trigger_maintains_value(db) -> None:
    engine, conn = _conn()
    try:
        uid = _insert("users", conn, email="a@example.com", username="alice", status="active")
        conn.commit()
        conn.execute(sa.text("UPDATE users SET display_name = 'Alice' WHERE id = :id"), {"id": uid})
        conn.commit()
        before = conn.execute(sa.text("SELECT updated_at FROM users WHERE id=:id"), {"id": uid}).scalar()
        import time as _time
        _time.sleep(0.02)
        conn.execute(sa.text("UPDATE users SET display_name = 'Alice B' WHERE id = :id"), {"id": uid})
        conn.commit()
        after = conn.execute(sa.text("SELECT updated_at FROM users WHERE id=:id"), {"id": uid}).scalar()
        assert after > before
    finally:
        conn.close()
        engine.dispose()


# ============================================================ Test C + D
def test_rerun_and_downgrade_roundtrip(db) -> None:
    upgrade(make_config(lock_mode="fail"), "head")  # C: rerun is a no-op
    assert current_revision() == "0009_timestamp_precision"
    downgrade(make_config(lock_mode="fail"), "base")  # D: full teardown
    assert current_revision() is None
    upgrade(make_config(lock_mode="fail"), "head")  # D: re-upgrade works
    assert current_revision() == "0009_timestamp_precision"


# ============================================================ Security
def test_user_duplicate_email_case_insensitive_rejected(db) -> None:
    engine, conn = _conn()
    try:
        _insert("users", conn, email="Alice@Example.com", username="alice1", status="active")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            conn.execute(
                sa.text("INSERT INTO users (email, username, status) VALUES (:e, :u, 'active')"),
                {"e": "alice@example.com", "u": "alice2"},
            )
            conn.commit()
        conn.rollback()
        # soft-deleted email can be reused
        uid1 = _scalar("SELECT id FROM users WHERE username='alice1'")
        conn.execute(sa.text("UPDATE users SET deleted_at = now() WHERE id=:id"), {"id": uid1})
        conn.commit()
        conn.execute(
            sa.text("INSERT INTO users (email, username, status) VALUES ('alice@example.com', 'alice3', 'active')")
        )
        conn.commit()
    finally:
        conn.close()
        engine.dispose()


def test_user_requires_login_identifier(db) -> None:
    engine, conn = _conn()
    try:
        with pytest.raises(sa.exc.IntegrityError):
            conn.execute(sa.text("INSERT INTO users (status) VALUES ('active')"))
            conn.commit()
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_identity_same_provider_subject_rejected(db) -> None:
    engine, conn = _conn()
    try:
        u1 = _insert("users", conn, email="b1@example.com", username="bob1", status="active")
        u2 = _insert("users", conn, email="b2@example.com", username="bob2", status="active")
        _insert("identities", conn, user_id=u1, provider="oidc", issuer="https://idp", subject="sub-1", status="active")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert("identities", conn, user_id=u2, provider="oidc", issuer="https://idp", subject="sub-1", status="active")
            conn.commit()
        conn.rollback()
        # revoked identity frees its email partial-unique slot
        conn.execute(sa.text("UPDATE identities SET revoked_at = now() WHERE user_id=:id"), {"id": u1})
        conn.commit()
        _insert("identities", conn, user_id=u2, provider="oidc", issuer="https://idp", subject="sub-2", email="dup@example.com", status="active")
        conn.commit()
        conn.execute(sa.text("UPDATE identities SET revoked_at = now() WHERE user_id=:id"), {"id": u2})
        conn.commit()
        _insert("identities", conn, user_id=u1, provider="oidc", issuer="https://idp", subject="sub-3", email="dup@example.com", status="active")
        conn.commit()
    finally:
        conn.close()
        engine.dispose()


def test_credential_single_active_password_per_identity(db) -> None:
    engine, conn = _conn()
    try:
        u = _insert("users", conn, email="c@example.com", username="carol", status="active")
        ident = _insert("identities", conn, user_id=u, provider="local", subject="local-1", status="active")
        conn.commit()
        _insert("credentials", conn, identity_id=ident, user_id=u, type="password",
                secret_hash="h1", algorithm="argon2id")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert("credentials", conn, identity_id=ident, user_id=u, type="password",
                    secret_hash="h2", algorithm="argon2id")
            conn.commit()
        conn.rollback()
        # after revoking the old one a new active password is allowed
        conn.execute(sa.text("UPDATE credentials SET revoked_at = now() WHERE identity_id=:id"), {"id": ident})
        conn.commit()
        _insert("credentials", conn, identity_id=ident, user_id=u, type="password",
                secret_hash="h2", algorithm="argon2id")
        conn.commit()
    finally:
        conn.close()
        engine.dispose()


def test_credential_secret_hash_cannot_be_empty(db) -> None:
    engine, conn = _conn()
    try:
        u = _insert("users", conn, email="d@example.com", username="dave", status="active")
        ident = _insert("identities", conn, user_id=u, provider="local", subject="local-2", status="active")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert("credentials", conn, identity_id=ident, user_id=u, type="password",
                    secret_hash="", algorithm="argon2id")
            conn.commit()
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_device_invalid_owner_fk_rejected(db) -> None:
    engine, conn = _conn()
    try:
        with pytest.raises(sa.exc.IntegrityError):
            _insert("devices", conn, user_id=_uuid.uuid4(), fingerprint="fp-1", status="active")
            conn.commit()
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_device_duplicate_fingerprint_per_user_rejected(db) -> None:
    engine, conn = _conn()
    try:
        u = _insert("users", conn, email="e@example.com", username="erin", status="active")
        conn.commit()
        _insert("devices", conn, user_id=u, fingerprint="fp-same", status="active")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert("devices", conn, user_id=u, fingerprint="fp-same", status="active")
            conn.commit()
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_session_invalid_user_and_device_rejected(db) -> None:
    engine, conn = _conn()
    try:
        u = _insert("users", conn, email="f@example.com", username="frank", status="active")
        ident = _insert("identities", conn, user_id=u, provider="local", subject="local-3", status="active")
        dev = _insert("devices", conn, user_id=u, fingerprint="fp-s1", status="active")
        conn.commit()
        # invalid user
        with pytest.raises(sa.exc.IntegrityError):
            _insert("sessions", conn, user_id=_uuid.uuid4(), identity_id=ident,
                    token_hash="t-1", status="active",
                    expires_at="2030-01-01T00:00:00Z")
            conn.commit()
        conn.rollback()
        # invalid device
        with pytest.raises(sa.exc.IntegrityError):
            _insert("sessions", conn, user_id=u, identity_id=ident, device_id=_uuid.uuid4(),
                    token_hash="t-2", status="active",
                    expires_at="2030-01-01T00:00:00Z")
            conn.commit()
        conn.rollback()
        # duplicate token_hash rejected
        _insert("sessions", conn, user_id=u, identity_id=ident, device_id=dev,
                token_hash="token-dup", status="active", expires_at="2030-01-01T00:00:00Z")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            _insert("sessions", conn, user_id=u, identity_id=ident, device_id=dev,
                    token_hash="token-dup", status="active", expires_at="2030-01-01T00:00:00Z")
            conn.commit()
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_session_state_and_expiry_constraints(db) -> None:
    engine, conn = _conn()
    try:
        u = _insert("users", conn, email="g@example.com", username="grace", status="active")
        ident = _insert("identities", conn, user_id=u, provider="local", subject="local-4", status="active")
        conn.commit()
        # invalid status rejected
        with pytest.raises(sa.exc.IntegrityError):
            _insert("sessions", conn, user_id=u, identity_id=ident,
                    token_hash="t-bad-status", status="flying",
                    expires_at="2030-01-01T00:00:00Z")
            conn.commit()
        conn.rollback()
        # expires_at <= created_at rejected
        with pytest.raises(sa.exc.IntegrityError):
            _insert("sessions", conn, user_id=u, identity_id=ident,
                    token_hash="t-bad-exp", status="active",
                    created_at="2030-01-01T00:00:00Z", expires_at="2029-01-01T00:00:00Z")
            conn.commit()
        conn.rollback()
        # an already-expired session row is expressible (TTL job flips it later)
        _now = _dt.datetime.now(_dt.timezone.utc)
        sid = _insert("sessions", conn, user_id=u, identity_id=ident,
                      token_hash="t-expired", status="active",
                      created_at=_now - _dt.timedelta(hours=2),
                      expires_at=_now - _dt.timedelta(hours=1))
        conn.commit()
        expired = _scalar("SELECT expires_at < now() FROM sessions WHERE id=:id", id=sid)
        assert expired is True
    finally:
        conn.close()
        engine.dispose()


def test_identity_with_sessions_cannot_be_deleted(db) -> None:
    engine, conn = _conn()
    try:
        u = _insert("users", conn, email="h@example.com", username="heidi", status="active")
        ident = _insert("identities", conn, user_id=u, provider="local", subject="local-5", status="active")
        _insert("sessions", conn, user_id=u, identity_id=ident,
                token_hash="t-restrict", status="active", expires_at="2030-01-01T00:00:00Z")
        conn.commit()
        with pytest.raises(sa.exc.IntegrityError):
            conn.execute(sa.text("DELETE FROM identities WHERE id=:id"), {"id": ident})
            conn.commit()
        conn.rollback()
        # ...but deleting the user cascades identities -> credentials/sessions
        conn.execute(sa.text("DELETE FROM users WHERE id=:id"), {"id": u})
        conn.commit()
        assert _scalar("SELECT count(*) FROM sessions WHERE token_hash='t-restrict'") == 0
        assert _scalar("SELECT count(*) FROM identities WHERE id=:id", id=ident) == 0
    finally:
        conn.close()
        engine.dispose()
