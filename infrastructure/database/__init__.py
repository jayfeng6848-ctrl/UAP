"""Database infrastructure: configuration, sessions, migrations, health.

PostgreSQL is the primary datastore. Nothing in this package connects at import
time; engines are created lazily by :func:`session.get_engine`.
"""

from .config import DatabaseConfig, DatabaseConfigurationError
from .health import ComponentHealth, check_database
from .migration import (
    MIGRATIONS_DIR,
    MIGRATION_TABLE,
    Migration,
    MigrationError,
    MigrationReport,
    applied_migrations,
    discover_migrations,
    run_migrations,
)
from .session import (
    build_engine,
    get_engine,
    init_engine,
    ping,
    reset_engine,
    session_scope,
)

__all__ = [
    "DatabaseConfig",
    "DatabaseConfigurationError",
    "ComponentHealth",
    "check_database",
    "MIGRATIONS_DIR",
    "MIGRATION_TABLE",
    "Migration",
    "MigrationError",
    "MigrationReport",
    "applied_migrations",
    "discover_migrations",
    "run_migrations",
    "build_engine",
    "get_engine",
    "init_engine",
    "ping",
    "reset_engine",
    "session_scope",
]
