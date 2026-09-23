"""Database health probes used by the readiness endpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

from sqlalchemy import Engine, text

from config.build_info import is_valid_revision

from .config import DatabaseConfig
from .session import build_engine, get_engine, ping

#: Component name used by the readiness response for the migration state gate.
MIGRATION_COMPONENT = "migration"

#: Independent, short server-side statement timeout for the readiness migration
#: probe (``D-PLAT-16``, Human-frozen hard value, 2026-09-23).
READINESS_STATEMENT_TIMEOUT_MS = 2000

#: Read-only probe of the Alembic bookkeeping table. No ORM, no Alembic import.
_ALEMBIC_VERSION_QUERY = "SELECT version_num FROM alembic_version"


@dataclass(frozen=True)
class ComponentHealth:
    name: str
    status: str  # ok | degraded | error | not_configured
    critical: bool
    detail: dict[str, object] | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def check_database(
    config: DatabaseConfig | None = None, engine: Engine | None = None
) -> ComponentHealth:
    """Probe PostgreSQL with ``SELECT 1``.

    Never raises: a failure is reported as a component with status ``error``.
    """
    detail: dict[str, object] = {}
    try:
        if config is not None:
            try:
                config.validate()
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                return ComponentHealth(
                    name="database",
                    status="error",
                    critical=True,
                    error=str(exc),
                )
            detail = {"target": config.safe_url()}
            from .session import build_engine

            probe_engine = build_engine(config)
            try:
                ok, error = ping(probe_engine)
            finally:
                probe_engine.dispose()
        else:
            target = engine or get_engine()
            ok, error = ping(target)
            detail = {"target": target.url.render_as_string(hide_password=True)}

        if ok:
            return ComponentHealth(
                name="database", status="ok", critical=True, detail=detail
            )
        return ComponentHealth(
            name="database",
            status="error",
            critical=True,
            detail=detail,
            error=error,
        )
    except Exception as exc:  # noqa: BLE001 - health probes must not raise
        return ComponentHealth(
            name="database",
            status="error",
            critical=True,
            detail=detail,
            error=f"{exc.__class__.__name__}: {exc}",
        )


def _brief(exc: Exception) -> str:
    """Return a short, log-safe rendering of a probe failure."""
    first_line = str(exc).splitlines()[0] if str(exc) else ""
    return (f"{exc.__class__.__name__}: {first_line}" if first_line else exc.__class__.__name__)[:200]


def _read_alembic_revisions(engine: Engine) -> list[str | None]:
    """Read every ``alembic_version.version_num`` row. Read-only, no Alembic import."""
    with engine.connect() as connection:
        rows = connection.execute(text(_ALEMBIC_VERSION_QUERY)).scalars().all()
    return [None if row is None else str(row).strip() for row in rows]


def check_migration_state(
    expected_revision: str | None,
    *,
    source: str | None = None,
    config: DatabaseConfig | None = None,
    engine: Engine | None = None,
) -> ComponentHealth:
    """Gate readiness on the database matching the build-time Alembic revision.

    Fails **closed** (``D-PLAT-08`` / ``D-PLAT-14``): every failure branch yields a
    ``critical`` component with status ``error``, so ``/ready`` answers 503.
    Never raises. Reports are limited to the two revision strings plus the
    resolution source — none of which is a secret.
    """
    expected = (expected_revision or "").strip()
    detail: dict[str, object] = {
        "expected": expected or None,
        "actual": None,
        "source": source or "missing",
    }

    def _error(message: str) -> ComponentHealth:
        return ComponentHealth(
            name=MIGRATION_COMPONENT,
            status="error",
            critical=True,
            detail=dict(detail),
            error=message,
        )

    # Fail closed *before* touching the database when the expectation is unusable.
    if not is_valid_revision(expected):
        return _error("expected revision is missing or invalid")

    probe_engine: Engine | None = None
    try:
        if config is not None:
            # Dedicated, short-lived probe engine with an independent statement
            # timeout; the global database default is left untouched.
            probe_engine = build_engine(
                replace(config, statement_timeout_ms=READINESS_STATEMENT_TIMEOUT_MS)
            )
            target = probe_engine
        else:
            target = engine or get_engine()

        try:
            revisions = _read_alembic_revisions(target)
        except Exception as exc:  # noqa: BLE001 - reported, never raised
            return _error(f"alembic_version is unreadable: {_brief(exc)}")

        if not revisions:
            return _error("alembic_version is empty (expected exactly one row)")
        if len(revisions) > 1:
            return _error(
                f"alembic_version holds {len(revisions)} rows (expected exactly one)"
            )

        actual = revisions[0]
        detail["actual"] = actual
        if not actual:
            return _error("alembic_version is NULL or empty")
        if actual != expected:
            return _error(f"revision mismatch: expected {expected} actual {actual}")

        return ComponentHealth(
            name=MIGRATION_COMPONENT,
            status="ok",
            critical=True,
            detail=dict(detail),
        )
    except Exception as exc:  # noqa: BLE001 - health probes must not raise
        return _error(_brief(exc))
    finally:
        if probe_engine is not None:
            probe_engine.dispose()


__all__ = [
    "ComponentHealth",
    "MIGRATION_COMPONENT",
    "READINESS_STATEMENT_TIMEOUT_MS",
    "check_database",
    "check_migration_state",
]
