"""Application settings loaded from the environment.

Rules:
    * No secret value is ever hard coded here.
    * Settings are loaded once and cached; use ``reload_settings`` only in tests.
    * Access is read-only from the caller's point of view.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Placeholder used when SECRET_KEY is not provided. Never valid outside local dev.
SECRET_KEY_PLACEHOLDER = "unsafe-development-secret-key"

VALID_ENVIRONMENTS = ("development", "test", "staging", "production")


def _default_env_file() -> Path:
    """Return the project level .env file (may not exist, that is fine)."""
    return PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Strongly typed view over the process environment."""

    model_config = SettingsConfigDict(
        env_file=str(_default_env_file()),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        frozen=True,  # configuration is read-only once loaded
    )

    # ------------------------------------------------------------------ core
    APP_ENV: str = Field(default="development", description="development | test | staging | production")
    APP_NAME: str = Field(default="UAP", description="Universal AI Platform")
    APP_VERSION: str = Field(default="0.1.13")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # -------------------------------------------------------------- security
    SECRET_KEY: str = Field(default=SECRET_KEY_PLACEHOLDER)

    # ---------------------------------------------------------- data storage
    # RUNTIME-ONLY (D-OP101-10 / CF-BB-3 = A). This key feeds the application
    # engine (infrastructure/database/*) and NOTHING else. The migration identity
    # is carried by ``UAP_MIGRATION_DATABASE_URL`` and is resolved exclusively in
    # ``migrations_alembic/env.py`` -- it is deliberately NOT a settings field, so
    # the runtime process can neither read nor fall back to the migration DSN.
    DATABASE_URL: str = Field(default="postgresql+psycopg://uap:uap@localhost:5432/uap")
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_ECHO: bool = Field(default=False)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # ----------------------------------------------------------- intelligence
    AI_DEFAULT_PROVIDER: str = Field(default="none")
    AI_DEFAULT_MODEL: str = Field(default="none")
    AI_REQUEST_TIMEOUT_SECONDS: int = Field(default=30, ge=1, le=600)

    # ------------------------------------------------------- schema governance
    EXPECTED_ALEMBIC_REVISION: str = Field(
        default="",
        description=(
            "Expected Alembic revision used by the /ready schema gate. "
            "Built images read the build-time artifact (config/_build_info.py), which "
            "this value can never override; it is a local development/test fallback. "
            "Empty means readiness fails closed. Not a secret."
        ),
    )

    @field_validator("APP_ENV")
    @classmethod
    def _validate_app_env(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"APP_ENV must be one of {VALID_ENVIRONMENTS}, got {value!r}"
            )
        return normalized

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DATABASE_URL must not be empty")
        scheme = urlsplit(value).scheme
        if not scheme.startswith("postgresql"):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL URL "
                "(postgresql:// or postgresql+psycopg://), got scheme "
                f"{scheme!r}"
            )
        return value

    # ------------------------------------------------------------- helpers
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"

    def require_secret_key(self) -> str:
        """Return SECRET_KEY, refusing the placeholder outside local development.

        This guard exists so that a deployment can never silently run with the
        well known development placeholder as its signing key.
        """
        if self.SECRET_KEY == SECRET_KEY_PLACEHOLDER and not (
            self.is_development or self.is_test
        ):
            raise RuntimeError(
                "SECRET_KEY is still the development placeholder; "
                "set a real value before running outside development/test."
            )
        return self.SECRET_KEY

    def database_url_without_credentials(self) -> str:
        """Return DATABASE_URL with any password replaced by ``***``."""
        return _redact_url_password(self.DATABASE_URL)

    def redacted(self) -> dict[str, Any]:
        """Return a log-safe snapshot of the configuration."""
        data = self.model_dump()
        data["DATABASE_URL"] = self.database_url_without_credentials()
        data["SECRET_KEY"] = "***" if self.SECRET_KEY != SECRET_KEY_PLACEHOLDER else "<placeholder>"
        return data


def _redact_url_password(url: str) -> str:
    parts = urlsplit(url)
    if not parts.password:
        return url
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    user = parts.username or ""
    netloc = f"{user}:***@{host}"
    return parts._replace(netloc=netloc).geturl()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings for the current process."""
    return Settings()


def reload_settings() -> Settings:
    """Drop the cached settings and reload from the environment (tests only)."""
    get_settings.cache_clear()
    return get_settings()


def load_settings_from_env(env: dict[str, str] | None = None) -> Settings:
    """Build settings from an explicit mapping, bypassing the cache."""
    if env is None:
        return Settings(_env_file=None)
    return Settings(_env_file=None, **{k: v for k, v in env.items() if v is not None})


__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "load_settings_from_env",
    "PROJECT_ROOT",
    "SECRET_KEY_PLACEHOLDER",
]
