"""Database configuration derived from application settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlsplit

from config.settings import Settings

PostgresSchemes = ("postgresql", "postgresql+psycopg", "postgresql+psycopg2")


class DatabaseConfigurationError(RuntimeError):
    """Raised when the database configuration is invalid."""


@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable database configuration.

    Holds everything needed to build an engine. Nothing here connects.
    """

    url: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    echo: bool = False
    connect_timeout_seconds: int = 5
    statement_timeout_ms: int | None = None
    application_name: str = "uap"
    options: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: Settings) -> "DatabaseConfig":
        return cls(
            url=settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            echo=settings.DB_ECHO,
        )

    # ------------------------------------------------------------ inspection
    @property
    def driver(self) -> str:
        return urlsplit(self.url).scheme

    @property
    def host(self) -> str | None:
        return urlsplit(self.url).hostname

    @property
    def port(self) -> int | None:
        return urlsplit(self.url).port

    @property
    def database(self) -> str:
        return (urlsplit(self.url).path or "/").lstrip("/")

    def safe_url(self) -> str:
        """URL with the password removed, safe for logs and health output."""
        parts = urlsplit(self.url)
        if not parts.password:
            return self.url
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        netloc = f"{parts.username or ''}:***@{host}"
        return parts._replace(netloc=netloc).geturl()

    def describe(self) -> dict[str, object]:
        return {
            "driver": self.driver,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "url": self.safe_url(),
        }

    # ------------------------------------------------------------- validation
    def validate(self) -> None:
        """Fail fast on a configuration that can never work."""
        if self.driver not in PostgresSchemes:
            raise DatabaseConfigurationError(
                f"unsupported database driver {self.driver!r}; "
                f"expected one of {PostgresSchemes}"
            )
        if not self.database:
            raise DatabaseConfigurationError("database name is missing in DATABASE_URL")
        if not self.host:
            raise DatabaseConfigurationError("database host is missing in DATABASE_URL")
        if self.pool_size < 1:
            raise DatabaseConfigurationError("pool_size must be >= 1")


__all__ = ["DatabaseConfig", "DatabaseConfigurationError"]
