"""Runtime database boundary (P14 Runtime Implementation Wave 1, §8–§10).

One application-level database infrastructure -- never "N repositories -> N
engines". Provides:

* engine/connection-pool construction from :class:`DatabaseConfig`
* the principal assertion (fail-closed)
* the transaction boundary (BEGIN -> work -> COMMIT, exception -> ROLLBACK)
* a liveness/readiness-grade health probe that never leaks the URL
* deterministic disposal

Repositories participate in transactions owned by this boundary; they never
commit on their own. Handlers never touch this module directly.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.runtime.errors import (
    ConnectionError as RuntimeConnectionError,
    PersistenceError,
    PrincipalAssertionError,
    TransactionError,
)

from .config import DatabaseConfig
from .principal import assert_connection_principal, role_from_url

HEALTH_PROBE_SQL = "SELECT 1"


class RuntimeDatabase:
    """The single runtime database boundary for the process.

    Construct with :meth:`from_config`; call :meth:`start` to validate the
    connection and identity before the application reports itself ready.
    """

    def __init__(self, config: DatabaseConfig, *, require_role: str | None = None) -> None:
        self._config = config
        self._require_role = require_role
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._principal: dict[str, str] | None = None

    # ------------------------------------------------------------ construction
    @classmethod
    def from_config(
        cls, config: DatabaseConfig, *, require_role: str | None = None
    ) -> "RuntimeDatabase":
        config.validate()
        return cls(config, require_role=require_role)

    @property
    def config(self) -> DatabaseConfig:
        return self._config

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            raise TransactionError("runtime database has not been started")
        return self._engine

    @property
    def started(self) -> bool:
        return self._engine is not None

    @property
    def principal(self) -> dict[str, str] | None:
        """Verified principal snapshot (only after a successful start)."""
        return self._principal

    # ----------------------------------------------------------------- startup
    def start(self) -> dict[str, str]:
        """Build the pool and prove the connection identity. Fail-closed."""
        if self._engine is not None:
            raise TransactionError("runtime database already started")

        engine = self._build_engine(self._config)
        try:
            with engine.connect() as connection:
                principal = assert_connection_principal(
                    connection,
                    role_from_url(self._config.url),
                    require_role=self._require_role,
                )
        except PrincipalAssertionError:
            engine.dispose()
            raise
        except SQLAlchemyError as exc:
            engine.dispose()
            raise RuntimeConnectionError(_safe_db_error(exc)) from exc

        self._engine = engine
        self._session_factory = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
        )
        self._principal = principal
        return principal

    @staticmethod
    def _build_engine(config: DatabaseConfig) -> Engine:
        from .session import build_engine

        return build_engine(config)

    # --------------------------------------------------------- transaction ctx
    @contextmanager
    def transaction(self, engine: Engine | None = None) -> Iterator[Session]:
        """Transaction boundary owned by the service/use-case layer.

        COMMIT on success; ROLLBACK and re-raise on any exception. The session
        is always closed. Repository code must not commit.
        """
        factory = self._session_factory
        if factory is None:
            raise TransactionError("runtime database has not been started")

        session = factory() if engine is None else sessionmaker(
            bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
        )()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------ health
    def health(self, timeout_seconds: float | None = None) -> tuple[bool, str | None]:
        """Connectivity probe. Returns ``(ok, safe_message)``; never raises."""
        if self._engine is None:
            return False, "runtime database not started"
        try:
            with self._engine.connect() as connection:
                connection.execute(text(HEALTH_PROBE_SQL))
            return True, None
        except SQLAlchemyError as exc:
            return False, _safe_db_error(exc)

    # ---------------------------------------------------------------- shutdown
    def dispose(self) -> None:
        """Dispose the pool. Idempotent."""
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._principal = None

    # ----------------------------------------------------------------- helpers
    def describe(self) -> dict[str, Any]:
        """Safe description for logs/metrics (password always redacted)."""
        return {
            **self._config.describe(),
            "started": self.started,
            "principal": self._principal,
            "require_role": self._require_role,
        }


def _safe_db_error(exc: BaseException) -> str:
    """Short, credential-free error text for logs and health output."""
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    for marker in ("password=", "postgresql+psycopg://", "postgresql://"):
        if marker in line:
            return "database connection failed (details redacted)"
    return line[:200]


__all__ = ["RuntimeDatabase", "HEALTH_PROBE_SQL"]
