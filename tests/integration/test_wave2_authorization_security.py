"""Wave 2 §四十 — Authorization / context security matrix (runtime identity).

Runtime assertions always run as ``uap_runtime``. The membership fixtures cannot
be created by that identity at all (``tenants`` / ``spaces`` / ``roles`` are
SELECT-only for the runtime, SEC-05), so they are provisioned by the fixture
identity in ``wave2_testkit`` and cleaned up afterwards.
"""

from __future__ import annotations

import uuid

import pytest
from core.resource import ResourceRef

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from services.context import (
    AuthorizationAdapter,
    ContextDenied,
    ContextRequired,
)
from services.use_cases import build_context, login
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
from tests.integration.wave2_testkit import (
    provision_active_user,
    provision_tenant_space_membership,
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


def _token(db, user) -> str:
    result = login(
        db, login_id=user["email"], password=PASSWORD, device_id=user["device_id"]
    )
    assert result.session is not None
    return result.session.token


def test_no_tenant_membership_denies_context(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with pytest.raises(ContextDenied):
        build_context(db, token=token)


def test_inactive_tenant_membership_denies_context(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"], active=False):
        with pytest.raises(ContextDenied):
            build_context(db, token=token)


def test_active_membership_resolves_a_single_candidate_deterministically(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as fixture:
        context = build_context(db, token=token)
        assert context.tenant_id == fixture.tenant_id
        assert context.space_id == fixture.space_id  # single active candidate
        assert context.authentication_assurance.value == "session_verified"


def test_wrong_tenant_is_denied(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]):
        with pytest.raises(ContextDenied):
            build_context(db, token=token, tenant_id=str(uuid.uuid4()))


def test_wrong_or_missing_space_membership_is_denied(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as fixture:
        with pytest.raises(ContextDenied):
            build_context(
                db, token=token, tenant_id=fixture.tenant_id, space_id=str(uuid.uuid4())
            )


def test_multiple_tenants_require_an_explicit_context(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as first:
        with provision_tenant_space_membership(user["user_id"]) as second:
            with pytest.raises(ContextRequired):
                build_context(db, token=token)  # never a random pick
            chosen = build_context(db, token=token, tenant_id=second.tenant_id)
            assert chosen.tenant_id == second.tenant_id
            assert chosen.tenant_id != first.tenant_id


def test_default_deny_for_an_ungranted_action(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as fixture:
        context = build_context(db, token=token)
        adapter = AuthorizationAdapter(db.engine)
        decision = adapter.authorize(
            context,
            action="resource.read",
            resource=ResourceRef(
                type="order",
                id=str(uuid.uuid4()),
                tenant_id=fixture.tenant_id,
                space_id=fixture.space_id,
                owner_identity_id=user["user_id"],
            ),
        )
        assert decision.allowed is False
        assert decision.effect == "DENY"


def test_unknown_subject_is_denied(db, scope) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as fixture:
        context = build_context(db, token=token)
        from dataclasses import replace

        ghost = replace(context, user_id=str(uuid.uuid4()))
        adapter = AuthorizationAdapter(db.engine)
        decision = adapter.authorize(
            ghost,
            action="resource.read",
            resource=ResourceRef(
                type="order", id=str(uuid.uuid4()), tenant_id=fixture.tenant_id
            ),
        )
        assert decision.allowed is False


def test_authorization_evaluator_failure_fails_closed(db, scope, monkeypatch) -> None:
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as fixture:
        context = build_context(db, token=token)
        adapter = AuthorizationAdapter(db.engine)

        class _Boom:
            def authorize(self, _request):  # noqa: ANN001
                raise RuntimeError("evaluator unavailable")

        monkeypatch.setattr(adapter, "_service", _Boom())
        decision = adapter.authorize(
            context,
            action="resource.read",
            resource=ResourceRef(
                type="order", id=str(uuid.uuid4()), tenant_id=fixture.tenant_id
            ),
        )
        assert decision.allowed is False
        assert decision.reason == "authorization-unavailable"


def test_adapter_subject_uses_the_user_id_anchor(db, scope) -> None:
    """Stage 2 resolves USER subjects through ``users.id`` (VOC-W2-01)."""
    user = provision_active_user(db, scope)
    token = _token(db, user)
    with provision_tenant_space_membership(user["user_id"]) as fixture:
        context = build_context(db, token=token)
        subject = AuthorizationAdapter.subject_for(context)
        assert subject.identity_id == user["user_id"]
        assert subject.identity_id != user["identity_id"]
        assert subject.subject_type == "USER"
        assert subject.tenant_id == fixture.tenant_id
