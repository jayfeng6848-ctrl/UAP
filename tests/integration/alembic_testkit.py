"""Shared test kit for Alembic integration checks (not collected as tests).

Creates/resets the dedicated ``uap_b1_test`` database so no business or
STEP-0 database is ever touched by the migration-infrastructure suite.

Dual-DSN configuration chain (D-OP101-10 · BATCH-B B-4)
    * ``MIGRATION_DSN`` / ``UAP_MIGRATION_DATABASE_URL``  -> Alembic / migration
      fixtures (injected programmatically via ``make_config()`` ->
      ``config.attributes["url"]``).
    * ``RUNTIME_DSN`` / ``DATABASE_URL``                 -> runtime fixtures /
      application runtime tests.
    * There is NO cross fallback: the migration side never reads
      ``DATABASE_URL`` and the runtime side never reads
      ``UAP_MIGRATION_DATABASE_URL``.
    * ``migration_dsn()`` is the fixture resolver for the migration identity and
      is strictly env-backed + FAIL-CLOSED: with
      ``UAP_MIGRATION_DATABASE_URL`` absent it raises instead of silently
      connecting to the runtime database.
    * ``make_config(url=BASE_DSN)`` keeps its existing interface: the DSN is
      *explicitly provided by the caller/testkit* (an explicit migration DSN,
      never the runtime key), so it is not a fallback path.
"""

from __future__ import annotations

import os
import socket
from pathlib import Path
from urllib.parse import urlsplit

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]

#: Environment key carrying the MIGRATION identity (Alembic-only).
MIGRATION_URL_ENV = "UAP_MIGRATION_DATABASE_URL"
#: Environment key carrying the RUNTIME identity (application-only).
RUNTIME_URL_ENV = "DATABASE_URL"

# Dedicated, disposable database. NEVER points at uap or uap_test.
TEST_DB = "uap_b1_test"
BASE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{TEST_DB}"
_ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"

#: Explicit migration-identity DSN used by this testkit (== BASE_DSN).
#: This is an explicitly-provided migration DSN -- NOT derived from, and never
#: falling back to, the runtime key.
MIGRATION_DSN = BASE_DSN
#: Explicit runtime-identity DSN (matches tests/conftest.py's runtime default).
RUNTIME_DSN = "postgresql+psycopg://uap:uap@localhost:5432/uap_test"


class MigrationDSNError(RuntimeError):
    """Raised when the migration identity DSN cannot be established."""


def migration_dsn() -> str:
    """Resolve the MIGRATION-identity DSN for fixtures. Env-backed, FAIL-CLOSED.

    Reads ONLY ``UAP_MIGRATION_DATABASE_URL``. When it is absent this raises
    ``MigrationDSNError`` -- it must never fall back to ``DATABASE_URL`` or to
    any runtime DSN, so a missing migration identity can never silently point
    the migration fixtures at the runtime database.
    """
    env = os.environ.get(MIGRATION_URL_ENV)
    if env and env.strip():
        return env.strip()
    raise MigrationDSNError(
        f"{MIGRATION_URL_ENV} is not set: refusing to resolve the migration "
        f"fixture DSN. {RUNTIME_URL_ENV} is runtime-only and is deliberately "
        f"NOT used as a fallback (no cross-identity fallback is permitted)."
    )


def runtime_dsn() -> str:
    """Resolve the RUNTIME-identity DSN for fixtures.

    Reads ONLY ``DATABASE_URL`` (falling back to this testkit's explicit
    ``RUNTIME_DSN`` constant when unset). It never reads
    ``UAP_MIGRATION_DATABASE_URL``, so the runtime side cannot inherit the
    migration identity.
    """
    env = os.environ.get(RUNTIME_URL_ENV)
    if env and env.strip():
        return env.strip()
    return RUNTIME_DSN


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
    """Build an Alembic ``Config`` bound to an explicitly provided migration DSN.

    ``config.attributes["url"]`` is the programmatic override carrier used by
    tests/CI. It carries the **migration** identity DSN supplied by the caller
    (default: this testkit's explicit ``BASE_DSN``); it is NOT a third
    configuration source and must never be fed the runtime ``DATABASE_URL``.
    Fails closed when called with an empty/blank URL.
    """
    if not url or not str(url).strip():
        raise MigrationDSNError(
            "make_config() received an empty migration URL; refusing to build "
            "an Alembic config without an explicit migration identity"
        )
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
