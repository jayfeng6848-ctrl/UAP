"""Engine and session lifecycle.

The engine is created lazily so importing the package never opens a socket.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import DatabaseConfig

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def build_engine(config: DatabaseConfig) -> Engine:
    """Create a SQLAlchemy engine from a validated configuration."""
    connect_args: dict[str, Any] = {}
    if config.statement_timeout_ms is not None:
        connect_args["options"] = (
            f"-c statement_timeout={int(config.statement_timeout_ms)}"
        )
    return create_engine(
        config.url,
        echo=config.echo,
        pool_pre_ping=config.pool_pre_ping,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        connect_args=connect_args,
        future=True,
    )


def init_engine(config: DatabaseConfig) -> Engine:
    """Initialise the process wide engine (idempotent)."""
    global _engine, _session_factory
    config.validate()
    if _engine is None:
        _engine = build_engine(config)
        _session_factory = sessionmaker(
            bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False
        )
    return _engine


def get_engine() -> Engine:
    """Return the process wide engine, creating it from settings if needed."""
    if _engine is None:
        from config.settings import get_settings

        init_engine(DatabaseConfig.from_settings(get_settings()))
    assert _engine is not None
    return _engine


def reset_engine() -> None:
    """Dispose and forget the engine (used by tests and shutdown hooks)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Transactional scope: commit on success, rollback on error, always close."""
    if engine is not None:
        factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    elif _session_factory is not None:
        factory = _session_factory
    else:
        factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping(engine: Engine | None = None, timeout: float | None = None) -> tuple[bool, str | None]:
    """Run ``SELECT 1``; return ``(ok, error_message)`` without raising."""
    target = engine or get_engine()
    try:
        with target.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as exc:  # pragma: no cover - depends on infra
        return False, _short_error(exc)


def _short_error(exc: Exception) -> str:
    message = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return message[:200]


__all__ = [
    "build_engine",
    "init_engine",
    "get_engine",
    "reset_engine",
    "session_scope",
    "ping",
]
