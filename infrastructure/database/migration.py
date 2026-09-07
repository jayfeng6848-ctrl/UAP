"""Minimal forward-only migration runner.

Migrations are plain ``.sql`` files named ``NNNN_name.sql`` inside
``migrations/``. Each migration runs inside a single transaction together with
the bookkeeping insert into ``schema_migrations``.

Scope note: this runner is intentionally small. It provides ordered, idempotent,
transactional schema evolution without pulling in a heavyweight toolchain.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import Engine, text

MIGRATIONS_DIR: Path = Path(__file__).resolve().parents[2] / "migrations"
MIGRATION_TABLE: str = "schema_migrations"

_FILENAME_RE = re.compile(r"^(?P<version>\d{4})_(?P<name>[a-z0-9_]+)\.sql$")


class MigrationError(RuntimeError):
    """Raised for malformed migrations or checksum drift."""


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path

    @property
    def sql(self) -> str:
        return self.path.read_text(encoding="utf-8")

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()[:16]


@dataclass
class MigrationReport:
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def pending(self) -> list[str]:
        return list(self.applied)

    def as_dict(self) -> dict[str, object]:
        return {
            "applied": self.applied,
            "skipped": self.skipped,
            "dry_run": self.dry_run,
        }


def discover_migrations(directory: Path | str | None = None) -> list[Migration]:
    """Return all discovered migrations sorted by version."""
    base = Path(directory) if directory else MIGRATIONS_DIR
    if not base.exists():
        return []

    migrations: list[Migration] = []
    for path in sorted(base.glob("*.sql")):
        match = _FILENAME_RE.match(path.name)
        if not match:
            raise MigrationError(
                f"invalid migration filename {path.name!r}; "
                "expected pattern NNNN_snake_case_name.sql"
            )
        migrations.append(
            Migration(
                version=match.group("version"),
                name=match.group("name"),
                path=path,
            )
        )

    versions = [m.version for m in migrations]
    if len(versions) != len(set(versions)):
        raise MigrationError(f"duplicate migration versions detected: {versions}")
    return migrations


def _split_statements(sql: str) -> list[str]:
    """Split a migration file into executable statements."""
    statements: list[str] = []
    for raw_line in sql.splitlines():
        line = raw_line.split("--", 1)[0].strip()
        if line:
            statements.append(line)
    joined = " ".join(statements)
    return [s.strip() for s in joined.split(";") if s.strip()]


def ensure_migration_table(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                    version       TEXT PRIMARY KEY,
                    name          TEXT NOT NULL,
                    checksum      TEXT NOT NULL,
                    applied_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def applied_migrations(engine: Engine) -> dict[str, str]:
    """Return ``{version: checksum}`` for migrations already applied."""
    ensure_migration_table(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT version, checksum FROM {MIGRATION_TABLE}")
        ).fetchall()
    return {row[0]: row[1] for row in rows}


def run_migrations(
    engine: Engine,
    directory: Path | str | None = None,
    dry_run: bool = False,
) -> MigrationReport:
    """Apply all pending migrations in version order.

    Each migration is applied together with its bookkeeping row in one
    transaction, so a failing migration leaves no partial schema behind.
    """
    migrations = discover_migrations(directory)
    ensure_migration_table(engine)
    already = applied_migrations(engine)
    report = MigrationReport(dry_run=dry_run)

    for migration in migrations:
        if migration.version in already:
            if already[migration.version] != migration.checksum:
                raise MigrationError(
                    f"checksum mismatch for migration {migration.version}_"
                    f"{migration.name}: file changed after it was applied"
                )
            report.skipped.append(migration.version)
            continue

        if dry_run:
            report.applied.append(migration.version)
            continue

        statements = _split_statements(migration.sql)
        if not statements:
            raise MigrationError(f"migration {migration.path.name} contains no statements")

        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
            conn.execute(
                text(
                    f"INSERT INTO {MIGRATION_TABLE} (version, name, checksum) "
                    "VALUES (:version, :name, :checksum)"
                ),
                {
                    "version": migration.version,
                    "name": migration.name,
                    "checksum": migration.checksum,
                },
            )
        report.applied.append(migration.version)

    return report


__all__ = [
    "MIGRATIONS_DIR",
    "MIGRATION_TABLE",
    "Migration",
    "MigrationError",
    "MigrationReport",
    "discover_migrations",
    "applied_migrations",
    "run_migrations",
    "ensure_migration_table",
]
