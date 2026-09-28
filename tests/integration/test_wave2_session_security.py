"""Wave 2 §三十九 — Session security matrix (runtime identity)."""

from __future__ import annotations

import sqlalchemy as sa
import pytest

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from services.identity import CredentialRejected, IdentityService
from services.session import SessionNotUsable, SessionService
from services.use_cases import login, logout, revoke_device
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
from tests.integration.wave2_testkit import (
    enroll_device,
    provision_active_user,
    run_sql,
    runtime_data_scope,
)

pytestmark = pytest.mark.integration

PASSWORD = "Wave2-Passw0rd!"


@pytest.fixture(scope="module")
def db():
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=runtime_test_dsn()), require_role=REQUIRED_ROLE
    )
    database.start()
    try:
        yield database
    finally:
        database.dispose()


@pytest.fixture()
def scope():
    with runtime_data_scope() as track:
        yield track


def _session(db, user) -> str:
    result = login(
        db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"]
    )
    assert result.session is not None
    return result.session.token


def test_valid_session_is_accepted(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    with db.transaction() as session:
        view = SessionService(session).validate(token=token)
    assert view.device_id == user["device_id"]
    assert view.user_id == user["user_id"]


def test_unknown_token_is_rejected(db, scope) -> None:
    with pytest.raises(Exception):
        with db.transaction() as session:
            SessionService(session).validate(token="not-a-real-token")


def test_expired_session_is_rejected(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    run_sql(
        db,
        # ck_sessions_expiry requires expires_at > created_at, so age both columns.
        "UPDATE sessions SET created_at = now() - interval '2 hours',"
        " expires_at = now() - interval '1 minute'"
        " WHERE token_hash = (SELECT token_hash FROM sessions ORDER BY created_at DESC LIMIT 1)",
    )
    with pytest.raises(SessionNotUsable):
        with db.transaction() as session:
            SessionService(session).validate(token=token)


def test_absolute_expiry_caps_the_relative_one(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    with db.transaction() as session:
        session_id = SessionService(session).validate(token=token).session_id
    # refresh cannot push the relative ceiling past the absolute one
    run_sql(
        db,
        "UPDATE sessions SET expires_at = now() + interval '30 minutes',"
        " absolute_expires_at = now() + interval '1 minute' WHERE id = :sid",
        {"sid": session_id},
    )
    with db.transaction() as session:
        view = SessionService(session).refresh(session_id=session_id)
        assert view.expires_at <= view.absolute_expires_at
    run_sql(
        db,
        "UPDATE sessions SET absolute_expires_at = now() - interval '1 second'"
        " WHERE id = :sid",
        {"sid": session_id},
    )
    with pytest.raises(SessionNotUsable):
        with db.transaction() as session:
            SessionService(session).validate_session_id(session_id)


def test_revoked_session_is_rejected(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    logout(db, token=token)
    with pytest.raises(SessionNotUsable):
        with db.transaction() as session:
            SessionService(session).validate(token=token)


def test_wrong_device_binding_is_rejected(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    run_sql(
        db, "UPDATE devices SET status = 'revoked' WHERE id = :did",
        {"did": user["device_id"]},
    )
    with pytest.raises(SessionNotUsable):
        with db.transaction() as session:
            SessionService(session).validate(token=token)


def test_wrong_identity_binding_is_rejected(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    run_sql(
        db, "UPDATE identities SET status = 'suspended' WHERE id = :iid",
        {"iid": user["identity_id"]},
    )
    with pytest.raises(SessionNotUsable):
        with db.transaction() as session:
            SessionService(session).validate(token=token)


def test_logout_is_granular_and_concurrent_sessions_survive(db, scope) -> None:
    user = provision_active_user(db, scope)
    first = _session(db, user)
    second = _session(db, user)  # one device may hold many sessions (§十八)
    assert first != second
    logout(db, token=first)
    with db.transaction() as session:
        assert SessionService(session).validate(token=second).session_id
        with pytest.raises(SessionNotUsable):
            SessionService(session).validate(token=first)


def test_device_revoke_revokes_only_that_devices_sessions(db, scope) -> None:
    user = provision_active_user(db, scope)
    other_device = enroll_device(db, email=user["email"], password=PASSWORD)
    token_a = _session(db, user)
    result_b = login(
        db, login_id=user["email"], password=PASSWORD, device_id=other_device
    )
    assert result_b.session is not None
    revoke_device(db, device_id=user["device_id"], reason="lost")
    with db.transaction() as session:
        service = SessionService(session)
        with pytest.raises(SessionNotUsable):
            service.validate(token=token_a)
        assert service.validate(token=result_b.session.token).session_id


def test_identity_revoke_propagates_to_sessions_and_credentials(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _session(db, user)
    with db.transaction() as session:
        result = IdentityService(session).revoke_identity(
            identity_id=user["identity_id"], reason="identity_revoked"
        )
    assert result["sessions"] >= 1
    assert result["credentials"] >= 1
    with pytest.raises(SessionNotUsable):
        with db.transaction() as session:
            SessionService(session).validate(token=token)
    with pytest.raises(CredentialRejected):
        login(db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"])


def test_credential_revoke_blocks_new_authentication(db, scope) -> None:
    """Credential revoke denies *authentication* (SEC-W2-04), it does not delete sessions."""
    user = provision_active_user(db, scope)
    token = _session(db, user)
    with db.transaction() as session:
        n = session.execute(
            sa.text(
                "UPDATE credentials SET revoked_at = now()"
                " WHERE identity_id = :iid AND revoked_at IS NULL"
            ),
            {"iid": user["identity_id"]},
        ).rowcount
    assert n == 1
    with pytest.raises(CredentialRejected):
        login(db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"])
    with db.transaction() as session:
        assert SessionService(session).validate(token=token).session_id
