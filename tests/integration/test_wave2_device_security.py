"""Wave 2 §三十八 — Device security matrix (runtime identity)."""

from __future__ import annotations

import sqlalchemy as sa
import pytest

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from services.device import ChallengeRejected, DeviceConflict, DeviceNotUsable
from services.session import SessionService
from services.use_cases import (
    complete_device_enrollment,
    login,
    revoke_device,
    start_device_enrollment,
)
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
from tests.integration.wave2_testkit import (
    enroll_device,
    new_login,
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


def test_valid_enrollment_ends_active(db, scope) -> None:
    user = provision_active_user(db, scope)
    with db.transaction() as session:
        status = session.execute(
            sa.text("SELECT status FROM devices WHERE id = :did"), {"did": user["device_id"]}
        ).scalar_one()
    assert status == "active"


def test_challenge_is_not_usable_twice(db, scope) -> None:
    user = provision_active_user(db, scope)
    fingerprint = "fp-replay-1"
    challenge = start_device_enrollment(
        db, login=user["email"], password=PASSWORD, fingerprint=fingerprint
    )
    complete_device_enrollment(
        db, challenge_id=challenge.challenge_id, secret=challenge.secret, fingerprint=fingerprint
    )
    with pytest.raises(ChallengeRejected):
        complete_device_enrollment(
            db, challenge_id=challenge.challenge_id, secret=challenge.secret,
            fingerprint=fingerprint,
        )


def test_invalid_challenge_secret_is_rejected(db, scope) -> None:
    user = provision_active_user(db, scope)
    challenge = start_device_enrollment(
        db, login=user["email"], password=PASSWORD, fingerprint="fp-bad-secret"
    )
    with pytest.raises(ChallengeRejected):
        complete_device_enrollment(
            db, challenge_id=challenge.challenge_id, secret="not-the-secret",
            fingerprint="fp-bad-secret",
        )


def test_expired_challenge_is_rejected(db, scope) -> None:
    user = provision_active_user(db, scope)
    challenge = start_device_enrollment(
        db, login=user["email"], password=PASSWORD, fingerprint="fp-expired"
    )
    run_sql(
        db,
        "UPDATE credentials SET expires_at = now() - interval '1 minute' WHERE id = :cid",
        {"cid": challenge.challenge_id},
    )
    with pytest.raises(ChallengeRejected):
        complete_device_enrollment(
            db, challenge_id=challenge.challenge_id, secret=challenge.secret,
            fingerprint="fp-expired",
        )


def test_challenge_is_bound_to_its_fingerprint(db, scope) -> None:
    """Wrong user / wrong fingerprint cannot satisfy someone else's challenge."""
    user = provision_active_user(db, scope)
    challenge = start_device_enrollment(
        db, login=user["email"], password=PASSWORD, fingerprint="fp-bound"
    )
    with pytest.raises(ChallengeRejected):
        complete_device_enrollment(
            db, challenge_id=challenge.challenge_id, secret=challenge.secret,
            fingerprint="fp-someone-else",
        )


def test_duplicate_fingerprint_for_same_user_conflicts(db, scope) -> None:
    user = provision_active_user(db, scope)
    enroll_device(db, email=user["email"], password=PASSWORD, fingerprint="fp-dup")
    with pytest.raises(DeviceConflict):
        start_device_enrollment(
            db, login=user["email"], password=PASSWORD, fingerprint="fp-dup"
        )


def test_same_fingerprint_for_a_different_user_is_allowed(db, scope) -> None:
    """Uniqueness is per user (persistence truth, §十三)."""
    first = provision_active_user(db, scope)
    second = provision_active_user(db, scope)
    shared = "fp-shared-across-users"
    enroll_device(db, email=first["email"], password=PASSWORD, fingerprint=shared)
    enroll_device(db, email=second["email"], password=PASSWORD, fingerprint=shared)


@pytest.mark.parametrize("status", ["revoked", "lost", "untrusted", "pending"])
def test_non_active_devices_cannot_authenticate(db, scope, status: str) -> None:
    user = provision_active_user(db, scope)
    run_sql(
        db, "UPDATE devices SET status = :status WHERE id = :did",
        {"status": status, "did": user["device_id"]},
    )
    with pytest.raises(Exception):
        login(db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"])


def test_untrusted_and_lost_are_not_aliases(db, scope) -> None:
    user = provision_active_user(db, scope)
    from services.use_cases import mark_device_lost

    assert mark_device_lost(db, device_id=user["device_id"], reason="lost") == "lost"
    with db.transaction() as session:
        from services.device import DeviceService

        service = DeviceService(session)
        assert service.is_authenticatable(user["device_id"]) is False
        with pytest.raises(DeviceNotUsable):
            # lost -> active requires explicit verification; nothing automatic
            service.reactivate(user["device_id"], verification_completed=False)


def test_device_revoke_revokes_its_sessions_atomically(db, scope) -> None:
    user = provision_active_user(db, scope)
    created = login(
        db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"]
    ).session
    assert created is not None

    result = revoke_device(db, device_id=user["device_id"], reason="lost_device")
    assert result["device_status"] == "revoked"
    assert result["sessions_revoked"] == 1

    with db.transaction() as session:
        assert SessionService(session).revoke(session_id=created.session_id) == 1
        assert session.execute(
            sa.text("SELECT status FROM sessions WHERE id = :sid"),
            {"sid": created.session_id},
        ).scalar_one() == "revoked"
