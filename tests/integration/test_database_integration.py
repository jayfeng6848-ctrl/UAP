"""PostgreSQL integration checks.

Skipped automatically when no database is reachable, so the default suite stays
offline-safe. Run with::

    docker compose up -d postgres
    pytest -m integration
"""

from __future__ import annotations

import socket

import pytest
from sqlalchemy import text

from config.settings import get_settings
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.migration import run_migrations
from infrastructure.database.session import build_engine, ping, session_scope

pytestmark = pytest.mark.integration


def _database_is_reachable(config: DatabaseConfig, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((config.host, config.port or 5432), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="module")
def database_engine():
    config = DatabaseConfig.from_settings(get_settings())
    if not _database_is_reachable(config):
        pytest.skip("PostgreSQL is not reachable; start it with `docker compose up -d postgres`")
    engine = build_engine(config)
    try:
        yield engine
    finally:
        engine.dispose()


def test_database_ping(database_engine) -> None:
    ok, error = ping(database_engine)
    assert ok, error


def test_migrations_apply_on_postgres(database_engine) -> None:
    report = run_migrations(database_engine)
    assert set(report.applied) | set(report.skipped) == {"0001"}


def test_transaction_scope_commits(database_engine) -> None:
    run_migrations(database_engine)
    with session_scope(database_engine) as session:
        session.execute(
            text(
                "INSERT INTO platform_metadata (key, value) VALUES (:k, :v) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            ),
            {"k": "uap.smoke", "v": "ok"},
        )
    with session_scope(database_engine) as session:
        value = session.execute(
            text("SELECT value FROM platform_metadata WHERE key = :k"),
            {"k": "uap.smoke"},
        ).scalar()
    assert value == "ok"
