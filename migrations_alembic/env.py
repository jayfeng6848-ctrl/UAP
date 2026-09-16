"""Alembic environment for UAP schema migrations.

Single migration entry point (see STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md).

Guarantees
    * Exactly one migration runner executes DDL at a time via a documented
      PostgreSQL transactional advisory lock (pg_advisory_xact_lock).
    * The lock is bound to the migration transaction: commit/rollback or
      connection close always releases it (no permanent lockout).
    * Lock key is stable and documented (NOT random): (5_587_280, 1).
    * Lock mode is selected by ``UAP_MIGRATION_LOCK_MODE`` or
      ``config.attributes["lock_mode"]``: wait (default) | fail | timeout.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# Make the project importable when running from this directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stable, documented advisory lock key.
# key1 = 5_587_280 (0x554150 == int value of the bytes "UAP")
# key2 = 1       (migration major version)
MIGRATION_LOCK_KEY: tuple[int, int] = (5_587_280, 1)

DEFAULT_LOCK_TIMEOUT_SECONDS = 30


class MigrationLockError(RuntimeError):
    """Raised in ``fail`` mode when another runner holds the migration lock."""


def _resolve_url() -> str:
    """URL precedence:
    1. config.attributes["url"] (programmatic override, used by tests/CI)
    2. DATABASE_URL environment variable
    3. alembic.ini sqlalchemy.url (dev default)
    """
    attr_url = context.config.attributes.get("url")
    if attr_url:
        return str(attr_url)
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    ini_url = context.config.get_main_option("sqlalchemy.url")
    if not ini_url:
        raise RuntimeError("sqlalchemy.url is not configured")
    return ini_url


def _lock_mode() -> str:
    mode = context.config.attributes.get("lock_mode")
    if mode is None:
        mode = os.environ.get("UAP_MIGRATION_LOCK_MODE", "wait")
    mode = str(mode).lower()
    if mode not in ("wait", "fail", "timeout"):
        raise RuntimeError(
            f"invalid UAP_MIGRATION_LOCK_MODE {mode!r}; expected wait|fail|timeout"
        )
    return mode


def _acquire_lock(connection: Any, mode: str) -> None:
    """Acquire the transactional migration advisory lock.

    Must run inside an open transaction (alembic's ``begin_transaction``);
    the lock is released automatically when that transaction ends.
    """
    k1, k2 = MIGRATION_LOCK_KEY
    if mode == "fail":
        acquired = connection.execute(
            text("SELECT pg_try_advisory_xact_lock(:k1, :k2)"), {"k1": k1, "k2": k2}
        ).scalar()
        if not acquired:
            raise MigrationLockError(
                "another migration runner holds the UAP migration lock "
                f"(key={MIGRATION_LOCK_KEY}); refusing to run concurrently"
            )
        return

    if mode == "timeout":
        seconds = int(
            os.environ.get("UAP_MIGRATION_LOCK_TIMEOUT_SECONDS", DEFAULT_LOCK_TIMEOUT_SECONDS)
        )
        connection.execute(
            text("SELECT set_config('lock_timeout', :v, true)"),
            {"v": f"{max(1, seconds)}s"},
        )

    # wait (default) / timeout: block until the lock is available.
    connection.execute(
        text("SELECT pg_advisory_xact_lock(:k1, :k2)"), {"k1": k1, "k2": k2}
    )


def run_migrations_offline() -> None:
    """Emit SQL without a database connection (no advisory lock possible)."""
    context.configure(
        url=_resolve_url(),
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        version_table="alembic_version",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and run migrations inside one transaction holding the lock."""
    cfg = context.config
    cfg.set_main_option("sqlalchemy.url", _resolve_url())

    connectable = engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            compare_type=True,
            version_table="alembic_version",
        )
        with context.begin_transaction():
            _acquire_lock(connection, _lock_mode())
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
