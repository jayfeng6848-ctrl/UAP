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


def test_ready_contract_when_migration_gate_fails(api_client, monkeypatch) -> None:
    """A schema-revision failure is critical: readiness answers 503."""
    from apps.api.routes import health as health_route
    from infrastructure.database.health import ComponentHealth

    monkeypatch.setattr(
        health_route,
        "collect_components",
        lambda: [
            ComponentHealth(name="database", status="ok", critical=True),
            ComponentHealth(
                name="migration",
                status="error",
                critical=True,
                detail={"expected": None, "actual": None, "source": "missing"},
                error="expected revision is missing or invalid",
            ),
        ],
    )
    response = api_client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert READY_FIELDS <= set(body)
    assert body["status"] == "not_ready"
    assert body["components"][1]["name"] == "migration"


def test_ready_contract_when_migration_gate_passes(api_client, monkeypatch) -> None:
    from apps.api.routes import health as health_route
    from infrastructure.database.health import ComponentHealth

    monkeypatch.setattr(
        health_route,
        "collect_components",
        lambda: [
            ComponentHealth(name="database", status="ok", critical=True),
            ComponentHealth(name="migration", status="ok", critical=True),
        ],
    )
    response = api_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_reports_a_critical_migration_component(api_client) -> None:
    """G-6 (hard): readiness must include a critical ``migration`` component."""
    from apps.api.routes.health import collect_components

    components = {component.name: component for component in collect_components()}
    assert "migration" in components, "readiness must probe the schema revision"
    assert components["migration"].critical is True


def test_health_is_liveness_only(api_client, monkeypatch) -> None:
    """``/health`` must not probe components or touch the database."""
    from apps.api.routes import health as health_route

    def _forbidden() -> object:
        raise AssertionError("/health must not probe readiness components")

    monkeypatch.setattr(health_route, "collect_components", _forbidden)
    monkeypatch.setattr(health_route, "check_database", _forbidden)
    monkeypatch.setattr(health_route, "check_migration_state", _forbidden)

    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_returns_404(api_client) -> None:
    assert api_client.get("/api/v1/does-not-exist").status_code == 404
