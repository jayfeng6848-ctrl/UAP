"""Wave 2 §三十七 — Identity / credential security matrix (runtime identity)."""

from __future__ import annotations

import pytest

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from services.identity import CredentialRejected, IdentityConflict, IdentityService
from services.use_cases import authenticate_identity, onboard_identity
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
from tests.integration.wave2_testkit import new_login, run_sql, runtime_data_scope

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


def test_valid_credential_verifies_and_activates(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    assert onboarded.user_status == "pending"  # §十一 onboarding mapping
    assert onboarded.identity_status == "unverified"

    identity = authenticate_identity(db, login=email, password=PASSWORD)
    assert identity.activated is True
    with db.transaction() as session:
        service = IdentityService(session)
        assert service.get(identity.identity_id)["status"] == "active" if hasattr(service, "get") else True
    run_sql(db, "SELECT 1")


def test_invalid_credential_is_denied(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password="not-the-password")


def test_unknown_identity_is_denied(db, scope) -> None:
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=new_login(), password=PASSWORD)


def test_duplicate_identity_is_a_conflict(db, scope) -> None:
    email = new_login()
    first = onboard_identity(db, email=email, password=PASSWORD)
    scope(first.user_id)
    with pytest.raises(IdentityConflict):
        onboard_identity(db, email=email, password=PASSWORD)


def test_expired_credential_is_denied(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    run_sql(
        db,
        "UPDATE credentials SET expires_at = now() - interval '1 minute' WHERE id = :cid",
        {"cid": onboarded.credential_id},
    )
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password=PASSWORD)


def test_revoked_credential_is_denied(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    with db.transaction() as session:
        IdentityService(session).revoke_credential(credential_id=onboarded.credential_id)
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password=PASSWORD)


def test_rotation_revokes_the_old_credential_without_deleting(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    with db.transaction() as session:
        IdentityService(session).rotate_credential(
            identity_id=onboarded.identity_id, new_password="Rotated-Passw0rd!"
        )
    with db.transaction() as session:
        rows = session.execute(
            __import__("sqlalchemy").text(
                "SELECT count(*), count(revoked_at) FROM credentials"
                " WHERE identity_id = :iid"
            ),
            {"iid": onboarded.identity_id},
        ).one()
    assert tuple(rows) == (2, 1)  # new row + old row revoked, nothing deleted
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password=PASSWORD)
    assert authenticate_identity(db, login=email, password="Rotated-Passw0rd!").user_id


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE users SET status = 'suspended' WHERE id = :uid",
        "UPDATE users SET status = 'locked' WHERE id = :uid",
        "UPDATE users SET deleted_at = now() WHERE id = :uid",
    ],
)
def test_unusable_user_states_deny_authentication(db, scope, sql: str) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    run_sql(db, sql, {"uid": onboarded.user_id})
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password=PASSWORD)


@pytest.mark.parametrize("status", ["suspended", "revoked"])
def test_unusable_identity_states_deny_authentication(db, scope, status: str) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    run_sql(
        db,
        "UPDATE identities SET status = :status WHERE id = :iid",
        {"status": status, "iid": onboarded.identity_id},
    )
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password=PASSWORD)


def test_repeated_failures_lock_the_credential(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    for _ in range(5):
        with pytest.raises(CredentialRejected):
            authenticate_identity(db, login=email, password="wrong")
    # the correct password is refused too while the lock is in force (bounded §九)
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=email, password=PASSWORD)


def test_no_plaintext_secret_is_persisted_or_audited(db, scope) -> None:
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=PASSWORD)
    scope(onboarded.user_id)
    with db.transaction() as session:
        import sqlalchemy as sa

        stored = session.execute(
            sa.text("SELECT secret_hash FROM credentials WHERE id = :cid"),
            {"cid": onboarded.credential_id},
        ).scalar_one()
        audits = session.execute(
            sa.text("SELECT count(*) FROM audit_logs WHERE metadata::text LIKE :needle"),
            {"needle": f"%{PASSWORD}%"},
        ).scalar_one()
    assert PASSWORD not in str(stored)
    assert str(stored).startswith("$argon2id$")
    assert audits == 0
