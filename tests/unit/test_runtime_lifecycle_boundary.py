"""Wave 1 §5 / §18 -- explicit application lifecycle, fail-closed startup.

The database boundary is replaced with a fake so the lifecycle can be exercised
offline: configuration failure, dependency failure and disposal failure must all
abort (never "startup anyway", never a swallowed shutdown error).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from infrastructure.database.config import DatabaseConfig
from infrastructure.runtime import lifecycle
from infrastructure.runtime.errors import (
    ConfigurationError,
    PrincipalAssertionError,
    TransactionError,
)
from infrastructure.runtime.lifecycle import LifecycleState, RuntimeApplication

VALID_URL = "postgresql+psycopg://uap_runtime:uap_runtime@localhost:5432/uap_b1_test"


class _FakeRuntimeDatabase:
    """Minimal stand-in for :class:`RuntimeDatabase`."""

    def __init__(self, *, principal, fail_start=None, fail_dispose=None):
        self._principal = principal
        self._fail_start = fail_start
        self._fail_dispose = fail_dispose
        self.started = False
        self.disposed = 0

    def start(self):
        if self._fail_start is not None:
            raise self._fail_start
        self.started = True
        return dict(self._principal)

    def dispose(self):
        self.disposed += 1
        if self._fail_dispose is not None:
            raise self._fail_dispose
        self.started = False

    def health(self):
        return (True, None) if self.started else (False, "runtime database not started")

    def describe(self):
        return {"started": self.started, "principal": self._principal}


def _install_fake(monkeypatch, **kwargs):
    """Replace the DB boundary used by the lifecycle; return the created fake."""
    created: dict[str, _FakeRuntimeDatabase] = {}

    def from_config(config, *, require_role=None):
        created["database"] = _FakeRuntimeDatabase(**kwargs)
        created["config"] = config
        created["require_role"] = require_role
        return created["database"]

    monkeypatch.setattr(
        lifecycle, "RuntimeDatabase", SimpleNamespace(from_config=from_config)
    )
    return created


def test_start_requires_valid_configuration(monkeypatch) -> None:
    _install_fake(monkeypatch, principal={"current_user": "uap_runtime"})
    app = RuntimeApplication()
    with pytest.raises(ConfigurationError):
        app.start(config=DatabaseConfig(url="mysql://uap@localhost:3306/uap"))
    assert app.state is LifecycleState.NEW


def test_startup_succeeds_and_records_principal(monkeypatch) -> None:
    created = _install_fake(
        monkeypatch,
        principal={"current_user": "uap_runtime", "session_user": "uap_runtime"},
    )
    app = RuntimeApplication()
    result = app.start(config=DatabaseConfig(url=VALID_URL), require_role="uap_runtime")
    assert app.state is LifecycleState.STARTED
    assert result.principal == {
        "current_user": "uap_runtime",
        "session_user": "uap_runtime",
    }
    assert created["database"].started is True
    assert created["require_role"] == "uap_runtime"
    assert app.database is created["database"]


def test_dependency_failure_aborts_startup(monkeypatch) -> None:
    _install_fake(monkeypatch, principal={}, fail_start=PrincipalAssertionError("mismatch"))
    app = RuntimeApplication()
    with pytest.raises(PrincipalAssertionError):
        app.start(config=DatabaseConfig(url=VALID_URL))
    assert app.state is LifecycleState.NEW, "startup must fail closed, not partially"


def test_double_start_is_rejected(monkeypatch) -> None:
    _install_fake(monkeypatch, principal={"current_user": "uap_runtime"})
    app = RuntimeApplication()
    app.start(config=DatabaseConfig(url=VALID_URL))
    with pytest.raises(TransactionError):
        app.start(config=DatabaseConfig(url=VALID_URL))


def test_database_property_and_health_before_start(monkeypatch) -> None:
    app = RuntimeApplication()
    with pytest.raises(TransactionError):
        _ = app.database
    assert app.health() == (False, "runtime database not started")


def test_stop_before_start_is_rejected(monkeypatch) -> None:
    app = RuntimeApplication()
    with pytest.raises(TransactionError):
        app.stop()


def test_stop_disposes_pool_and_is_terminal(monkeypatch) -> None:
    created = _install_fake(monkeypatch, principal={"current_user": "uap_runtime"})
    app = RuntimeApplication()
    app.start(config=DatabaseConfig(url=VALID_URL))
    app.stop()
    assert created["database"].disposed == 1
    assert app.state is LifecycleState.STOPPED
    assert app.health() == (False, "runtime database not started")
    with pytest.raises(TransactionError):
        app.start(config=DatabaseConfig(url=VALID_URL))


def test_shutdown_disposal_error_is_not_swallowed(monkeypatch) -> None:
    _install_fake(
        monkeypatch,
        principal={"current_user": "uap_runtime"},
        fail_dispose=RuntimeError("pool did not drain"),
    )
    app = RuntimeApplication()
    app.start(config=DatabaseConfig(url=VALID_URL))
    with pytest.raises(TransactionError):
        app.stop()
    assert app.state is LifecycleState.STOPPED


def test_service_registry_boundary(monkeypatch) -> None:
    _install_fake(monkeypatch, principal={"current_user": "uap_runtime"})
    app = RuntimeApplication()
    with pytest.raises(TransactionError):
        app.register_service("identity", object())
    app.start(config=DatabaseConfig(url=VALID_URL))
    app.register_service("identity", "svc")
    assert app.get_service("identity") == "svc"
    with pytest.raises(ConfigurationError):
        app.get_service("device")


def test_no_degraded_mode_surface() -> None:
    """The lifecycle deliberately exposes no 'startup anyway' / degraded switch."""
    assert not hasattr(RuntimeApplication, "startup_anyway")
    assert {s.value for s in LifecycleState} == {"new", "started", "stopped"}
