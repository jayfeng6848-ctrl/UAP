"""FastAPI application factory for the UAP API.

Run locally with::

    uvicorn apps.api.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routes.health import router as health_router
from apps.api.routes.meta import router as meta_router
from config.settings import Settings, get_settings
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.session import reset_engine
from infrastructure.logging import configure_logging, get_logger

logger = get_logger(__name__)


def _bootstrap_logging(settings: Settings) -> None:
    configure_logging(
        level=settings.LOG_LEVEL,
        fmt=settings.LOG_FORMAT,
        service=settings.APP_NAME.lower(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    logger.info(
        "uap.api.startup",
        extra={
            "context": {
                "event": "api.startup",
            }
        },
    )
    if settings.ENABLE_MIGRATIONS_ON_STARTUP:
        from infrastructure.database.migration import run_migrations
        from infrastructure.database.session import get_engine

        report = run_migrations(get_engine())
        logger.info(
            "migrations applied=%s skipped=%s",
            report.applied,
            report.skipped,
        )
    yield
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
    return app


app = create_app()

__all__ = ["create_app", "app"]
