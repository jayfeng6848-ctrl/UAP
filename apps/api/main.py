"""FastAPI application factory for the UAP API.

Run locally with::

    uvicorn apps.api.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routes.devices import router as devices_router
from apps.api.routes.health import router as health_router
from apps.api.routes.identity import router as identity_router
from apps.api.routes.meta import router as meta_router
from apps.api.routes.sessions import router as sessions_router
from config.settings import Settings, get_settings
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.session import reset_engine
from infrastructure.logging import configure_logging, get_logger
from infrastructure.runtime.lifecycle import DEFAULT_REQUIRED_ROLE, RuntimeApplication

logger = get_logger(__name__)


def _bootstrap_logging(settings: Settings) -> None:
    configure_logging(
        level=settings.LOG_LEVEL,
        fmt=settings.LOG_FORMAT,
        service=settings.APP_NAME.lower(),
    )


def _required_runtime_role(settings: Settings) -> str | None:
    """The role the runtime DSN must name.

    ``uap_runtime`` is mandatory in staging / production (RTA-02, SEC-P14-01).
    Local development / test intentionally run against convenience DSNs, so only
    the Wave 1 principal assertion (``current_user == session_user == DSN role``)
    applies there. The assertion itself is never skipped — only the extra
    "must be exactly uap_runtime" requirement is environment-scoped.
    """
    return DEFAULT_REQUIRED_ROLE if settings.APP_ENV in ("staging", "production") else None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    # Wave 2 §三十二: the API reuses the Wave 1 runtime bootstrap instead of
    # building a second one. Schema migrations are still never applied at
    # startup: Alembic is the sole schema entry point (D-PLAT-07/08/15).
    runtime = RuntimeApplication()
    runtime.start(
        settings,
        config=DatabaseConfig.from_settings(settings),
        require_role=_required_runtime_role(settings),
    )
    app.state.runtime = runtime
    logger.info(
        "uap.api.startup",
        extra={
            "context": {
                "event": "api.startup",
                "database": runtime.database.describe(),
                "principal": runtime.database.principal,
            }
        },
    )
    try:
        yield
    finally:
        app.state.runtime = None
        runtime.stop()
        reset_engine()
        logger.info("uap.api.shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API application.

    Pass ``settings`` explicitly in tests; otherwise the process environment is
    used.
    """
    settings = settings or get_settings()
    _bootstrap_logging(settings)

    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        description="Universal AI Platform - core API (STEP 0 foundation)",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.database_config = DatabaseConfig.from_settings(settings)

    app.include_router(health_router)
    app.include_router(meta_router)
    app.include_router(identity_router)
    app.include_router(devices_router)
    app.include_router(sessions_router)
    return app


app = create_app()

__all__ = ["create_app", "app"]
