"""Wave 2 §三十三: HTTP mapping must follow the Wave 1 eight-class taxonomy."""

from __future__ import annotations

from apps.api.error_mapping import classify, translate
from infrastructure.runtime.errors import (
    ConnectionError as RuntimeConnectionError,
    PersistenceError,
    SecurityBoundaryError,
)
from services.context import ContextDenied, ContextRequired
from services.device import ChallengeRejected, DeviceConflict, DeviceValidationError
from services.identity import CredentialRejected, IdentityConflict, IdentityValidationError
from services.session import SessionNotUsable, SessionTokenRejected


def test_authentication_failures_map_to_401() -> None:
    for exc in (CredentialRejected("x"), SessionTokenRejected("x"), ChallengeRejected("x"),
                SessionNotUsable("x")):
        assert classify(exc) == "authentication"
        assert translate(exc).status_code == 401


def test_authorization_and_context_failures_are_distinguished() -> None:
    assert translate(ContextDenied("x")).status_code == 403
    assert translate(ContextRequired("x")).status_code == 400


def test_conflict_is_not_reported_as_validation() -> None:
    assert classify(IdentityConflict("x")) == "conflict"
    assert classify(DeviceConflict("x")) == "conflict"
    assert translate(IdentityConflict("x")).status_code == 409
    assert translate(IdentityValidationError("x")).status_code == 422
    assert translate(DeviceValidationError("x")).status_code == 422


def test_security_boundary_and_persistence_are_fuzzed_not_leaked() -> None:
    for exc in (SecurityBoundaryError("relation public.users denied to role uap_runtime"),
                PersistenceError("connection string postgresql://uap:uap@host/db"),
                RuntimeConnectionError("password=uap failed")):
        response = translate(exc)
        assert response.status_code == 503
        assert response.detail == "service temporarily unavailable"
        assert "uap" not in str(response.detail)


def test_nothing_maps_to_500_by_accident() -> None:
    assert translate(ValueError("bad input")).status_code == 422
    assert translate(RuntimeError("boom")).status_code == 500
