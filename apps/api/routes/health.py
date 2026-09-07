"""Health and readiness endpoints.

``/health``  - liveness: is the process running?
``/ready``   - readiness: can the process serve traffic right now?
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from fastapi import APIRouter, Response, status

from config.settings import get_settings
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.health import ComponentHealth, check_database

router = APIRouter(tags=["health"])

#: Components reported as present-but-unconfigured in STEP 0. They never make
#: the platform unready.
OPTIONAL_COMPONENTS: tuple[str, ...] = ("cache", "queue", "ai_gateway")


def collect_components() -> list[ComponentHealth]:
    """Probe every component that participates in readiness.

    Isolated in one function so tests can replace it wholesale.
    """
    settings = get_settings()
    return [check_database(DatabaseConfig.from_settings(settings))]


def build_readiness_report(components: list[ComponentHealth]) -> tuple[bool, dict]:
    """Turn component probes into an HTTP-ready response body."""
    ready = all(
        component.status == "ok"
        for component in components
        if component.critical
    )
    body = {
        "status": "ready" if ready else "not_ready",
        "components": [component.as_dict() for component in components],
        "optional": [
            {"name": name, "status": "not_configured"} for name in OPTIONAL_COMPONENTS
        ],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    return ready, body


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    """Return 200 whenever the process is alive.

    Deliberately performs no I/O: a liveness probe must never fail because a
    dependency is slow, otherwise the orchestrator would restart a healthy
    process during a transient dependency outage.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.APP_NAME.lower(),
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", summary="Readiness probe")
def ready(response: Response) -> dict:
    """Return 200 when the platform can serve traffic, 503 otherwise.

    The AI gateway is intentionally NOT part of readiness: an unavailable model
    provider must not mark UAP Core as dead.
    """
    ready_flag, body = build_readiness_report(collect_components())
    response.status_code = (
        status.HTTP_200_OK if ready_flag else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return body


__all__ = [
    "router",
    "OPTIONAL_COMPONENTS",
    "collect_components",
    "build_readiness_report",
]
