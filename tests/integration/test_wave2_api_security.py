"""Wave 2 §四十一 — API adaptation security matrix.

The application is created with an explicit settings object whose ``DATABASE_URL``
is the runtime DSN, so the API talks to ``uap_b1_test`` **as ``uap_runtime``**
through the Wave 1 runtime bootstrap.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app
from config.settings import load_settings_from_env
from infrastructure.runtime.errors import PersistenceError
from tests.integration.runtime_testkit import runtime_test_dsn
from tests.integration.wave2_testkit import (
    new_login,
    provision_tenant_space_membership,
    runtime_data_scope,
)

pytestmark = pytest.mark.integration

PASSWORD = "Wave2-Passw0rd!"


@pytest.fixture(scope="module")
def client():
    settings = load_settings_from_env(
        {
            "APP_ENV": "test",
            "DATABASE_URL": runtime_test_dsn(),
            "LOG_FORMAT": "console",
            "AI_DEFAULT_PROVIDER": "none",
            "AI_DEFAULT_MODEL": "none",
        }
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _onboard(client, scope, email: str) -> None:
    response = client.post(
        "/identity/onboarding", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    scope(response.json()["user_id"])


def test_missing_credential_is_401(client) -> None:
    assert client.get("/me").status_code == 401
    response = client.post("/sessions", json={"login": new_login(), "password": PASSWORD})
    assert response.status_code == 401
    assert "password" not in response.text.lower()


def test_malformed_credential_is_401(client) -> None:
    for header in ("Basic abc", "Bearer", "Token abc"):
        response = client.get("/me", headers={"Authorization": header})
        assert response.status_code == 401


def test_invalid_password_is_401_and_leaks_nothing(client, scope=None) -> None:
    with runtime_data_scope() as track:
        email = new_login()
        _onboard(client, track, email)
        response = client.post(
            "/sessions", json={"login": email, "password": "wrong-password"}
        )
        assert response.status_code == 401
        body = response.text.lower()
        for needle in ("argon2", "sql", "uap_runtime", "postgres", "traceback"):
            assert needle not in body


def test_full_login_and_context_round_trip(client, scope=None) -> None:
    with runtime_data_scope() as track:
        email = new_login()
        fingerprint = f"fp-{uuid.uuid4().hex[:8]}"
        onboarded = client.post(
            "/identity/onboarding", json={"email": email, "password": PASSWORD}
        )
        assert onboarded.status_code == 201, onboarded.text
        user_id = track(onboarded.json()["user_id"])
        challenge = client.post(
            "/devices/enrollment-challenge",
            json={"login": email, "password": PASSWORD, "fingerprint": fingerprint},
        )
        assert challenge.status_code == 201, challenge.text
        payload = challenge.json()
        enrolled = client.post(
            "/devices/enrollment",
            json={
                "challenge_id": payload["challenge_id"],
                "secret": payload["secret"],
                "fingerprint": fingerprint,
            },
        )
        assert enrolled.status_code == 201, enrolled.text
        device_id = enrolled.json()["device_id"]

        session = client.post(
            "/sessions", json={"login": email, "password": PASSWORD, "device_id": device_id}
        )
        assert session.status_code == 201, session.text
        token = session.json()["token"]
        assert session.json()["authentication_assurance"] == "session_verified"

        # authenticated, but with no membership the context is denied (403) —
        # authentication is not tenant authorization (§二十三).
        assert client.get(
            "/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code == 403

        with provision_tenant_space_membership(user_id) as fixture:
            me = client.get(
                "/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-Id": fixture.tenant_id,
                },
            )
            assert me.status_code == 200, me.text
            assert me.json()["user_id"] == user_id
            assert "password" not in me.text.lower()

        assert client.post(
            "/sessions/logout", headers={"Authorization": f"Bearer {token}"}
        ).json()["revoked"] == 1
        assert client.get(
            "/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code == 401


def test_wrong_tenant_is_403(client) -> None:
    with runtime_data_scope() as track:
        email = new_login()
        _onboard(client, track, email)
        fingerprint = f"fp-{uuid.uuid4().hex[:8]}"
        challenge = client.post(
            "/devices/enrollment-challenge",
            json={"login": email, "password": PASSWORD, "fingerprint": fingerprint},
        ).json()
        device = client.post(
            "/devices/enrollment",
            json={
                "challenge_id": challenge["challenge_id"],
                "secret": challenge["secret"],
                "fingerprint": fingerprint,
            },
        ).json()
        token = client.post(
            "/sessions",
            json={"login": email, "password": PASSWORD, "device_id": device["device_id"]},
        ).json()["token"]
        # no membership at all -> context denied (fail closed, not a random pick)
        response = client.get(
            "/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-Id": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 403


def test_database_failure_maps_to_503_without_leaking(client, monkeypatch) -> None:
    import apps.api.routes.identity as identity_route

    def _boom(*_args, **_kwargs):
        raise PersistenceError(
            'permission denied for table users (role "uap_runtime", DSN postgresql://uap:uap@db/uap)'
        )

    monkeypatch.setattr(identity_route, "onboard_identity", _boom)
    response = client.post(
        "/identity/onboarding", json={"email": new_login(), "password": PASSWORD}
    )
    assert response.status_code == 503
    body = response.text
    for needle in ("uap", "postgresql", "permission denied", "users"):
        assert needle not in body
