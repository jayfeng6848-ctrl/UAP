"""Application runtime bootstrap / lifecycle (Wave 1 §5, §18).

Explicit startup:

    configuration load -> validation -> dependency construction ->
    DB connection initialisation -> repository construction ->
    service construction -> application ready

Any failure in configuration, connection, or a required dependency aborts
startup. There is deliberately no "startup anyway" and no degraded security
mode.

Shutdown stops accepting work, disposes application resources and the pool,
flushes observability, and never swallows disposal errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.settings import Settings, get_settings
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from infrastructure.logging import get_logger
from infrastructure.runtime.errors import (
    ConfigurationError,
    TransactionError,
)

logger = get_logger(__name__)

#: Role the P14 runtime must use (RTA-02). Enforcement is opt-in per
#: environment: production runtime passes this explicitly, unit tests may not.
DEFAULT_REQUIRED_ROLE = "uap_runtime"


class LifecycleState(str, Enum):
    NEW = "new"
    STARTED = "started"
    STOPPED = "stopped"


@dataclass(frozen=True)
class StartupResult:
    """Evidence that startup completed; safe to log."""

    state: LifecycleState
    database: dict[str, Any] = field(default_factory=dict)
    principal: dict[str, str] | None = None


class RuntimeApplication:
    """Explicit runtime lifecycle holder.

    Usage::

        app = RuntimeApplication()
        app.start(settings)          # fail-closed
        ...                          # serve traffic
        app.stop()
    """

    def __init__(self) -> None:
        self._state = LifecycleState.NEW
        self._settings: Settings | None = None
        self._database: RuntimeDatabase | None = None
        self._services: dict[str, Any] = {}

    # -------------------------------------------------------------- properties
    @property
    def state(self) -> LifecycleState:
        return self._state

    @property
    def database(self) -> RuntimeDatabase:
        if self._database is None:
            raise TransactionError("runtime application has not been started")
        return self._database

    # ----------------------------------------------------------------- startup
    def start(
        self,
        settings: Settings | None = None,
        *,
        config: DatabaseConfig | None = None,
        require_role: str | None = DEFAULT_REQUIRED_ROLE,
    ) -> StartupResult:
        if self._state is LifecycleState.STARTED:
            raise TransactionError("runtime application already started")
        if self._state is LifecycleState.STOPPED:
            raise TransactionError("runtime application was already stopped")

        settings = settings or get_settings()
        database_config = config or DatabaseConfig.from_settings(settings)

        # 1. configuration load + validation
        try:
            database_config.validate()
        except Exception as exc:
            raise ConfigurationError(str(exc)) from exc

        # 2. dependency construction (DB boundary + pool + principal proof)
        database = RuntimeDatabase.from_config(database_config, require_role=require_role)
        principal = database.start()  # raises Connection/PrincipalAssertion on failure

        # 3. repository / service construction boundary (populated by later waves)
        self._settings = settings
        self._database = database
        self._services = {}
        self._state = LifecycleState.STARTED

        logger.info(
            "uap.runtime.startup",
            extra={
                "context": {
                    "event": "runtime.startup",
                    "database": database.describe(),
                    "principal": principal,
                }
            },
        )
        return StartupResult(
            state=self._state, database=database.describe(), principal=principal
        )

    # ---------------------------------------------------------------- shutdown
    def stop(self) -> None:
        if self._state is not LifecycleState.STARTED:
            raise TransactionError("runtime application is not started")
        errors: list[BaseException] = []
        # 1. stop accepting new work (owned by the API/worker layer in later waves)
        # 2. dispose application resources
        self._services.clear()
        # 3. dispose the database pool
        try:
            if self._database is not None:
                self._database.dispose()
        except BaseException as exc:  # pragma: no cover - defensive
            errors.append(exc)
        # 4. flush observability
        logger.info(
            "uap.runtime.shutdown",
            extra={"context": {"event": "runtime.shutdown"}},
        )
        self._state = LifecycleState.STOPPED
        if errors:
            raise TransactionError(
                f"runtime shutdown encountered {len(errors)} disposal error(s)"
            ) from errors[0]

    # ------------------------------------------------------------------ health
    def health(self) -> tuple[bool, str | None]:
        """Database-level readiness signal (distinct from 'process alive')."""
        if self._database is None:
            return False, "runtime database not started"
        return self._database.health()

    def register_service(self, name: str, service: Any) -> None:
        """Register a constructed service (used by later waves)."""
        if self._state is not LifecycleState.STARTED:
            raise TransactionError("runtime application is not started")
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        if name not in self._services:
            raise ConfigurationError(f"runtime service {name!r} is not constructed")
        return self._services[name]


__all__ = [
    "RuntimeApplication",
    "StartupResult",
    "LifecycleState",
    "DEFAULT_REQUIRED_ROLE",
]
