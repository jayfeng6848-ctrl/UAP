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


@pytest.fixture
def api_client(settings: Settings):
    """A FastAPI test client bound to a freshly created application."""
    from fastapi.testclient import TestClient

    from apps.api.main import create_app

    with TestClient(create_app(settings)) as client:
        yield client
