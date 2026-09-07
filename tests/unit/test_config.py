"""Settings behaviour: environment parsing, validation, redaction."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from config.settings import (
    SECRET_KEY_PLACEHOLDER,
    Settings,
    load_settings_from_env,
)

#: Every environment key the settings object reads.
SETTING_ENV_KEYS = (
    "APP_ENV",
    "APP_NAME",
    "APP_VERSION",
    "APP_HOST",
    "APP_PORT",
    "DATABASE_URL",
    "REDIS_URL",
    "SECRET_KEY",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "AI_DEFAULT_PROVIDER",
    "AI_DEFAULT_MODEL",
    "AI_REQUEST_TIMEOUT_SECONDS",
    "ENABLE_MIGRATIONS_ON_STARTUP",
)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch) -> None:
    """Settings tests must not inherit the ambient environment."""
    for key in SETTING_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_defaults_are_safe() -> None:
    settings = load_settings_from_env({})
    assert settings.APP_ENV == "development"
    assert settings.SECRET_KEY == SECRET_KEY_PLACEHOLDER
    assert settings.is_development


def test_invalid_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        load_settings_from_env({"APP_ENV": "unknown-env"})


def test_non_postgres_database_url_is_rejected() -> None:
    with pytest.raises(ValidationError):
        load_settings_from_env({"DATABASE_URL": "mysql://user:pw@localhost/db"})


def test_secret_placeholder_is_refused_outside_development() -> None:
    settings = load_settings_from_env({"APP_ENV": "production"})
    with pytest.raises(RuntimeError):
        settings.require_secret_key()


def test_secret_placeholder_is_allowed_in_test() -> None:
    settings = load_settings_from_env({"APP_ENV": "test"})
    assert settings.require_secret_key() == SECRET_KEY_PLACEHOLDER


def test_database_url_is_redacted() -> None:
    settings = load_settings_from_env(
        {"DATABASE_URL": "postgresql+psycopg://uap:supersecret@localhost:5432/uap"}
    )
    redacted = settings.database_url_without_credentials()
    assert "supersecret" not in redacted
    assert "***" in redacted


def test_redacted_snapshot_hides_secret_key() -> None:
    settings = load_settings_from_env({"SECRET_KEY": "a-real-looking-value"})
    snapshot = settings.redacted()
    assert snapshot["SECRET_KEY"] == "***"
    assert "a-real-looking-value" not in str(snapshot)


def test_settings_are_immutable_in_practice() -> None:
    settings = load_settings_from_env({})
    assert isinstance(settings, Settings)
    with pytest.raises(ValidationError):
        settings.APP_ENV = "whatever"  # type: ignore[misc]
