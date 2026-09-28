"""Wave 2 audit invariant (independent of the Wave 1 baseline assertion).

``audit_logs`` is append-only (``tg_audit_immutable``, D-P10-11): rows can never
be removed, so an absolute baseline (``audit_logs == 0``) cannot describe it once
Wave 2 security suites have run. This suite asserts the *delta* instead:
an operation either appends nothing, or appends exactly the audit rows its
use-case is specified to write — and never leaks a secret into them.
"""

from __future__ import annotations

import sqlalchemy as sa
import pytest

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from services.identity import CredentialRejected
from services.session import SessionService
from services.use_cases import authenticate_identity, login, revoke_device
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
from tests.integration.wave2_testkit import provision_active_user, runtime_data_scope

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


def _audit_count(db) -> int:
    with db.transaction() as session:
        return int(session.execute(sa.text("SELECT count(*) FROM public.audit_logs")).scalar_one())


def test_pure_read_path_appends_no_audit(db, scope) -> None:
    """A validated read (session validation) must not write audit rows."""
    user = provision_active_user(db, scope)
    created = login(
        db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"]
    ).session
    assert created is not None
    before = _audit_count(db)
    with db.transaction() as session:
        SessionService(session).validate_session_id(created.session_id)
    assert _audit_count(db) - before == 0


def test_successful_authentication_appends_exactly_one_audit_row(db, scope) -> None:
    user = provision_active_user(db, scope)
    before = _audit_count(db)
    authenticate_identity(db, login=user["email"], password=PASSWORD)
    assert _audit_count(db) - before == 1


def test_denied_authentication_appends_exactly_one_denial_row(db, scope) -> None:
    user = provision_active_user(db, scope)
    before = _audit_count(db)
    with pytest.raises(CredentialRejected):
        authenticate_identity(db, login=user["email"], password="wrong-password")
    assert _audit_count(db) - before == 1
    with db.transaction() as session:
        row = session.execute(
            sa.text(
                "SELECT result, metadata::text FROM public.audit_logs"
                " ORDER BY occurred_at DESC, id DESC LIMIT 1"
            )
        ).one()
    assert row[0] == "denied"
    assert "wrong-password" not in row[1]  # only a coarse reason is recorded


def test_device_revoke_audit_records_the_atomic_propagation(db, scope) -> None:
    user = provision_active_user(db, scope)
    created = login(
        db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"]
    ).session
    assert created is not None
    before = _audit_count(db)
    result = revoke_device(db, device_id=user["device_id"], reason="final_acceptance")
    assert _audit_count(db) - before == 1
    assert result["sessions_revoked"] == 1
    with db.transaction() as session:
        row = session.execute(
            sa.text(
                "SELECT action, result, risk_level, metadata::text FROM public.audit_logs"
                " ORDER BY occurred_at DESC, id DESC LIMIT 1"
            )
        ).one()
    assert row[0] == "device.revoked"
    assert row[1] == "success"
    assert row[2] == "HIGH"
    assert '"sessions_revoked": 1' in row[3] or '"sessions_revoked":1' in row[3]
