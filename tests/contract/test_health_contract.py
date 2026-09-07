"""API response contracts for the endpoints that exist in STEP 0."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.contract

HEALTH_FIELDS = {"status", "service", "version", "env", "timestamp"}
READY_FIELDS = {"status", "components", "optional", "checked_at"}


def test_health_contract(api_client) -> None:
    body = api_client.get("/health").json()
    assert HEALTH_FIELDS <= set(body)
    assert body["status"] == "ok"


def test_ready_contract_when_healthy(api_client, monkeypatch) -> None:
    from apps.api.routes import health as health_route
    from infrastructure.database.health import ComponentHealth

    monkeypatch.setattr(
        health_route,
        "collect_components",
        lambda: [ComponentHealth(name="database", status="ok", critical=True)],
    )
    body = api_client.get("/ready").json()
    assert READY_FIELDS <= set(body)
    assert body["status"] == "ready"


def test_ready_contract_when_database_down(api_client, monkeypatch) -> None:
    from apps.api.routes import health as health_route
    from infrastructure.database.health import ComponentHealth

    monkeypatch.setattr(
        health_route,
        "collect_components",
        lambda: [
            ComponentHealth(
                name="database",
                status="error",
                critical=True,
                error="connection refused",
            )
        ],
    )
    response = api_client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["components"][0]["error"] == "connection refused"


def test_meta_contract(api_client) -> None:
    body = api_client.get("/api/v1/meta").json()
    assert body["name"] == "UAP"
    assert body["phase"].startswith("PHASE-0")
    assert "permission" in body["core_modules"]
    assert {d["domain_id"] for d in body["domains"]} == {
        "family",
        "company",
        "business",
        "entertainment",
    }
    assert all(d["status"] == "placeholder" for d in body["domains"])


def test_unknown_route_returns_404(api_client) -> None:
    assert api_client.get("/api/v1/does-not-exist").status_code == 404
