"""Shared test kit for Alembic integration checks (not collected as tests).

Creates/resets the dedicated ``uap_b1_test`` database so no business or
STEP-0 database is ever touched by the migration-infrastructure suite.
"""

from __future__ import annotations

import socket
from pathlib import Path
from urllib.parse import urlsplit

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]

# Dedicated, disposable database. NEVER points at uap or uap_test.
TEST_DB = "uap_b1_test"
BASE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{TEST_DB}"
_ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"


def database_reachable(dsn: str = BASE_DSN, timeout: float = 2.0) -> bool:
    parts = urlsplit(dsn)
    try:
        with socket.create_connection((parts.hostname or "localhost", parts.port or 5432), timeout=timeout):
            return True
    except OSError:
        return False


def reset_test_database() -> None:
    """Drop and recreate the dedicated test database (autocommit DDL)."""
    admin = sa.create_engine(_ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{TEST_DB}"'))
    admin.dispose()


def make_config(url: str = BASE_DSN, lock_mode: str = "wait") -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = url
    cfg.attributes["lock_mode"] = lock_mode
    return cfg


def upgrade(cfg: Config, target: str = "head") -> None:
    command.upgrade(cfg, target)


def downgrade(cfg: Config, target: str = "base") -> None:
    command.downgrade(cfg, target)


def current_revision(url: str = BASE_DSN) -> str | None:
    engine = sa.create_engine(url)
    try:
        with engine.connect() as conn:
            return conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar()
    except sa.exc.DBAPIError:
        return None  # version table does not exist (base state)
    finally:
        engine.dispose()


def advisory_lock_rows(url: str = BASE_DSN, key: tuple[int, int] = (5_587_280, 1)) -> int:
    """Count pg_locks rows for the documented UAP migration lock key."""
    engine = sa.create_engine(url)
    try:
        with engine.connect() as conn:
            return conn.execute(
                sa.text(
                    "SELECT count(*) FROM pg_locks "
                    "WHERE locktype = 'advisory' AND classid = :k1 AND objid = :k2"
                ),
                {"k1": key[0], "k2": key[1]},
            ).scalar()
    finally:
        engine.dispose()
