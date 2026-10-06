"""Shared test configuration.

The suite must be runnable with no external services: PostgreSQL-dependent
checks live behind the ``integration`` marker and skip when unreachable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Deterministic, offline-safe baseline.
#
# DUAL-DSN CONFIGURATION CHAIN (D-OP101-10 / BATCH-B B-4):
#   * ``DATABASE_URL`` below is the RUNTIME identity (application runtime
#     tests). It is deliberately the ONLY key this conftest injects.
#   * The MIGRATION identity is carried by ``UAP_MIGRATION_DATABASE_URL`` and is
#     injected by ``tests/integration/alembic_testkit.make_config()`` via
#     ``config.attributes["url"]``. This conftest intentionally does NOT set
#     that key, so the migration fixture's source stays provable and
#     FAIL-CLOSED (see ``alembic_testkit.migration_dsn()``).
#   * There is no cross fallback in either direction: the migration side never
#     reads ``DATABASE_URL`` and the runtime side never reads
#     ``UAP_MIGRATION_DATABASE_URL``.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://uap:uap@localhost:5432/uap_test")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("AI_DEFAULT_PROVIDER", "none")
os.environ.setdefault("AI_DEFAULT_MODEL", "none")

from config.settings import Settings, get_settings, reload_settings  # noqa: E402

reload_settings()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def migration_dsn() -> str:
    """The MIGRATION-identity DSN (``UAP_MIGRATION_DATABASE_URL``).

    Env-backed and FAIL-CLOSED: when the key is absent this raises instead of
    falling back to ``DATABASE_URL`` (no cross-identity fallback). Provided by
    ``alembic_testkit``; imported lazily so offline test collection never pays
    for the alembic import.
    """
    from tests.integration.alembic_testkit import migration_dsn as _resolve

    return _resolve()


@pytest.fixture(scope="session")
def runtime_dsn() -> str:
    """The RUNTIME-identity DSN (``DATABASE_URL``).

    Never reads ``UAP_MIGRATION_DATABASE_URL`` -- the runtime side cannot
    inherit the migration identity.
    """
    from tests.integration.alembic_testkit import runtime_dsn as _resolve

    return _resolve()


@pytest.fixture
def api_client(settings: Settings):
    """A FastAPI test client bound to a freshly created application."""
    from fastapi.testclient import TestClient

    from apps.api.main import create_app

    with TestClient(create_app(settings)) as client:
        yield client
