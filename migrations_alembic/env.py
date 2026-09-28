"""Alembic environment for UAP schema migrations.

Single migration entry point (see STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md).

Migration identity (D-OP101-10 · CF-BB-1 = NEW_STRUCTURE)
    * ``UAP_MIGRATION_DATABASE_URL`` is the canonical -- and only -- *environment*
      source of the migration DSN.
    * ``DATABASE_URL`` is RUNTIME-ONLY. It is deliberately never read here: the
      runtime key must not decide the migration identity.
    * ``alembic.ini`` no longer carries an executable DSN, so it cannot act as a
      connection fallback either.
    * Resolution order: (1) ``UAP_MIGRATION_DATABASE_URL``,
      (2) ``config.attributes["url"]`` (explicit programmatic override used by
      tests/CI), (3) FAIL-CLOSED -- the identity is never inferred.
    * No fallback in either direction (runtime->migration or migration->runtime).
    * The effective connection's DB role is asserted against the role named in
      the effective URL (``_assert_effective_role``).

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
from sqlalchemy.engine import make_url

# Make the project importable when running from this directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stable, documented advisory lock key.
# key1 = 5_587_280 (0x554150 == int value of the bytes "UAP")
# key2 = 1       (migration major version)
MIGRATION_LOCK_KEY: tuple[int, int] = (5_587_280, 1)

DEFAULT_LOCK_TIMEOUT_SECONDS = 30

#: Canonical migration identity source (env). See D-OP101-10.
MIGRATION_URL_ENV = "UAP_MIGRATION_DATABASE_URL"
#: Runtime-only key. Read by config/settings.py -- NEVER by this module.
RUNTIME_URL_ENV = "DATABASE_URL"


class MigrationLockError(RuntimeError):
    """Raised in ``fail`` mode when another runner holds the migration lock."""


class MigrationIdentityError(RuntimeError):
    """Raised when the effective migration identity cannot be established."""


def _resolve_url() -> str:
    """Resolve the EFFECTIVE MIGRATION URL. Single-source, FAIL-CLOSED.

    Precedence
        1. ``UAP_MIGRATION_DATABASE_URL`` -- canonical migration identity source
        2. ``config.attributes["url"]``   -- explicit programmatic override
                                             (tests / CI; never a runtime fallback)
        3. raise ``MigrationIdentityError``

    Deliberately NOT consulted: ``DATABASE_URL`` (runtime-only) and
    ``alembic.ini::sqlalchemy.url`` (removed -- no executable default DSN).
    """
    env_url = os.environ.get(MIGRATION_URL_ENV)
    if env_url and env_url.strip():
        return env_url.strip()

    attr_url = context.config.attributes.get("url")
    if attr_url and str(attr_url).strip():
        return str(attr_url).strip()

    raise MigrationIdentityError(
        f"{MIGRATION_URL_ENV} is not set and no config.attributes['url'] override "
        f"was supplied; refusing to run migrations without an explicit migration "
        f"identity. {RUNTIME_URL_ENV} is runtime-only and is deliberately NOT "
        f"used as a fallback, and alembic.ini carries no executable DSN."
    )


def _assert_effective_role(connection: Any, url: str) -> None:
    """Assert the effective connection really is the role named in ``url``.

    Guards against the silent-wrong-identity class of failure (R-02.4): a DSN
    that is resolved but then rewritten (role mapping, pg_hba, pooled URL) would
    otherwise run DDL as an unexpected principal.
    """
    try:
        expected = make_url(url).username
    except Exception as exc:  # pragma: no cover - defensive
        raise MigrationIdentityError(f"unparseable migration URL: {exc}") from exc

    if not expected:
        raise MigrationIdentityError(
            "the effective migration URL names no DB role; refusing to run "
            "migrations with an anonymous identity"
        )

    row = connection.execute(text("SELECT current_user, session_user")).one()
    effective, session_user = str(row[0]), str(row[1])
    if effective != expected:
        raise MigrationIdentityError(
            f"effective migration role {effective!r} does not match the role named "
            f"in the migration URL {expected!r} (session_user={session_user!r}); "
            f"refusing to run migrations under an unexpected identity"
        )


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
    url = _resolve_url()
    cfg.set_main_option("sqlalchemy.url", url)

    connectable = engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Migration-identity assertion (D-OP101-10 · requirement 7):
        # the effective connection must be the role named in the effective URL.
        _assert_effective_role(connection, url)
        # _assert_effective_role() executes SELECT statements before Alembic transaction setup.
        # SQLAlchemy 2.0 autobegin leaves the connection in an active transaction.
        # Roll back only this assertion transaction and return transaction ownership to Alembic.
        connection.rollback()
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
