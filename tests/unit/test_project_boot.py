"""First boot test: proves the project is alive end to end."""

from __future__ import annotations

import importlib

import pytest

from config.settings import get_settings
from core import CORE_MODULES
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.migration import discover_migrations


def test_all_core_modules_import() -> None:
    """Each declared core module must import cleanly."""
    assert CORE_MODULES, "core must declare its modules"
    for module_name in CORE_MODULES:
        module = importlib.import_module(f"core.{module_name}.interfaces")
        assert module is not None


def test_config_loads() -> None:
    settings = get_settings()
    assert settings.APP_NAME
    assert settings.APP_VERSION
    assert settings.APP_ENV in {"development", "test", "staging", "production"}
    assert settings.AI_DEFAULT_PROVIDER


def test_database_configuration_is_valid() -> None:
    config = DatabaseConfig.from_settings(get_settings())
    config.validate()
    assert config.driver.startswith("postgresql")
    assert config.database


def test_migrations_are_discoverable() -> None:
    migrations = discover_migrations()
    assert migrations, "at least the platform baseline migration must exist"
    assert migrations[0].version == "0001"


def test_application_starts(api_client) -> None:
    """The application boots and serves the liveness endpoint."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint_reports_components(api_client, monkeypatch) -> None:
    """Readiness reflects component state without touching a real database."""
    from apps.api.routes import health as health_route
    from infrastructure.database.health import ComponentHealth

    monkeypatch.setattr(
        health_route,
        "collect_components",
        lambda: [ComponentHealth(name="database", status="ok", critical=True)],
    )
    response = api_client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["components"][0]["name"] == "database"


def test_ready_is_not_broken_by_missing_ai_provider(api_client, monkeypatch) -> None:
    """An unavailable AI provider must never mark the platform unready."""
    from apps.api.routes import health as health_route
    from infrastructure.database.health import ComponentHealth

    monkeypatch.setattr(
        health_route,
        "collect_components",
        lambda: [ComponentHealth(name="database", status="ok", critical=True)],
    )
    body = api_client.get("/ready").json()
    optional = {item["name"] for item in body["optional"]}
    assert "ai_gateway" in optional
    assert all(item["status"] == "not_configured" for item in body["optional"])


@pytest.mark.parametrize("module", ["identity", "permission", "audit", "resource"])
def test_core_module_interfaces_are_business_agnostic(module: str) -> None:
    """Core interfaces must not reference any concrete domain package."""
    source = importlib.import_module(f"core.{module}.interfaces").__doc__ or ""
    assert "domains." not in source
