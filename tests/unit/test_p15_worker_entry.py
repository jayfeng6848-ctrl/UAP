"""P15 Batch 4 — consumer worker process entry (offline).

Covers Batch 4 §11: startup, running, stop signal, draining, stopped, startup
failure, configuration validation, no orphan process, no unhandled signal and
no falsely delivered event. Nothing here opens a real database connection and
nothing here installs a real signal handler in the test process.
"""

from __future__ import annotations

import importlib
import signal
from contextlib import contextmanager
from dataclasses import dataclass

from apps.worker.main import (
    EXIT_OK,
    EXIT_STARTUP_FAILURE,
    build_worker,
    install_signal_handlers,
)
from services.consumer.claim import ClaimService
from services.consumer.worker import ConsumerWorker, WorkerState

# ``apps/worker/__init__.py`` re-exports the ``main`` *function*, which shadows
# the same-named submodule attribute; resolve the module explicitly.
worker_main = importlib.import_module("apps.worker.main")


@dataclass
class _FakeSettings:
    APP_ENV: str = "test"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    DATABASE_URL: str = "postgresql+psycopg://uap_runtime:pw@localhost:5432/uap_b1_test"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False


class _FakeResult:
    def __init__(self, rows: list | None = None) -> None:
        self._rows = rows or []
        self.rowcount = len(self._rows)

    def all(self) -> list:
        return list(self._rows)


class _FakeSession:
    def __init__(self, sql_log: list[str]) -> None:
        self._sql_log = sql_log

    def execute(self, statement, params=None):  # noqa: ANN001 - SQLAlchemy shape
        self._sql_log.append(str(statement))
        return _FakeResult()


class _FakeDatabase:
    """Records transaction open/close so 'short-lived' is provable."""

    def __init__(self, sql_log: list[str]) -> None:
        self._sql_log = sql_log
        self.opened = 0
        self.closed = 0
        self.opened_while_closed = 0

    @contextmanager
    def transaction(self):
        if self.opened != self.closed:
            self.opened_while_closed += 1
        self.opened += 1
        try:
            yield _FakeSession(self._sql_log)
        finally:
            self.closed += 1


class _FakeRuntime:
    def __init__(self, *, fail_start: bool = False) -> None:
        self.sql_log: list[str] = []
        self.database = _FakeDatabase(self.sql_log)
        self.started = False
        self.stopped = False
        self._fail_start = fail_start

    def start(self, *args, **kwargs):  # noqa: ANN002, ANN003 - lifecycle signature
        if self._fail_start:
            raise RuntimeError("database unreachable")
        self.started = True
        return None

    def stop(self) -> None:
        self.stopped = True


def _delivered_sql(sql_log: list[str]) -> list[str]:
    return [sql for sql in sql_log if "delivered" in sql.lower()]


# ------------------------------------------------------------------ wiring
def test_build_worker_uses_the_empty_production_allowlist_and_frozen_config() -> None:
    runtime = _FakeRuntime()
    worker = build_worker(runtime, worker_id="w-entry")

    assert isinstance(worker, ConsumerWorker)
    assert worker.handlers.is_empty is True          # production registry = EMPTY
    assert worker.config.worker_id == "w-entry"
    assert worker.config.worker_processes == 1
    assert worker.config.concurrency == 4
    assert worker.config.batch_size == 10
    assert worker.config.lease_seconds == 120
    assert worker.config.heartbeat_seconds == 40
    assert worker.config.max_attempts == 10


def test_build_worker_generates_a_process_scope_worker_id() -> None:
    first = build_worker(_FakeRuntime())
    second = build_worker(_FakeRuntime())
    assert first.config.worker_id.startswith("worker-")
    assert first.config.worker_id != second.config.worker_id


def test_claim_factory_yields_a_claim_service_in_a_short_lived_transaction() -> None:
    runtime = _FakeRuntime()
    worker = build_worker(runtime, worker_id="w-tx")

    with worker._factory() as service:  # noqa: SLF001 - boundary under test
        assert isinstance(service, ClaimService)
        assert runtime.database.opened == 1
        assert runtime.database.closed == 0
    assert runtime.database.closed == 1                 # never long-lived
    assert runtime.database.opened_while_closed == 0


# --------------------------------------------------------------- lifecycle
def test_entry_claims_nothing_on_the_empty_production_queue_and_stays_healthy() -> None:
    runtime = _FakeRuntime()
    worker = build_worker(runtime, worker_id="w-empty")
    worker.start()
    try:
        result = worker.run_once()
        assert result["claimed"] == 0 and result["dispatched"] == 0
        assert worker.state is WorkerState.RUNNING
        assert _delivered_sql(runtime.sql_log) == []
    finally:
        worker.stop()
    assert worker.state is WorkerState.STOPPED


def test_stop_signal_drains_and_never_falsely_delivers() -> None:
    runtime = _FakeRuntime()
    worker = build_worker(runtime, worker_id="w-signal")
    handler = install_signal_handlers(worker, install=False)
    worker.start()
    worker.run_once()

    handler(signal.SIGTERM, None)

    assert worker.state is WorkerState.STOPPED
    assert _delivered_sql(runtime.sql_log) == []


def test_signal_handler_is_returned_without_installing_when_requested() -> None:
    worker = build_worker(_FakeRuntime(), worker_id="w-noinstall")
    original = signal.getsignal(signal.SIGTERM)
    handler = install_signal_handlers(worker, install=False)
    assert callable(handler)
    assert signal.getsignal(signal.SIGTERM) is original


# -------------------------------------------------------------- process
def test_main_returns_error_when_the_runtime_cannot_start() -> None:
    runtime = _FakeRuntime(fail_start=True)
    code = worker_main.main(settings=_FakeSettings(), runtime_factory=lambda: runtime)
    assert code == EXIT_STARTUP_FAILURE
    assert runtime.started is False
    assert runtime.stopped is False          # never started -> nothing to stop


def test_main_starts_polls_and_shuts_down_cleanly(monkeypatch) -> None:
    runtime = _FakeRuntime()
    started: list[str] = []

    monkeypatch.setattr(
        worker_main,
        "install_signal_handlers",
        lambda worker, **kwargs: (lambda *args: None),
    )
    monkeypatch.setattr(
        ConsumerWorker,
        "run_until_stopped",
        lambda self, **kwargs: started.append("ran"),
    )

    code = worker_main.main(settings=_FakeSettings(), runtime_factory=lambda: runtime)

    assert code == EXIT_OK
    assert started == ["ran"]
    assert runtime.started is True
    assert runtime.stopped is True           # runtime disposed: no orphan process
    # The startup dependency probe is a real DB round-trip that must be closed
    # again; the polling round-trip itself is covered by the empty-queue test.
    assert runtime.database.opened >= 1
    assert runtime.database.opened == runtime.database.closed
    assert _delivered_sql(runtime.sql_log) == []


# ----------------------------------------------------------------- config
def test_required_runtime_role_is_environment_scoped() -> None:
    assert worker_main.required_runtime_role(_FakeSettings(APP_ENV="production")) == "uap_runtime"
    assert worker_main.required_runtime_role(_FakeSettings(APP_ENV="staging")) == "uap_runtime"
    assert worker_main.required_runtime_role(_FakeSettings(APP_ENV="development")) is None
    assert worker_main.required_runtime_role(_FakeSettings(APP_ENV="test")) is None
