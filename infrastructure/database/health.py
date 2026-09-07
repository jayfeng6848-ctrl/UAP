"""Database health probe used by the readiness endpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import Engine

from .config import DatabaseConfig
from .session import get_engine, ping


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


__all__ = ["ComponentHealth", "check_database"]
