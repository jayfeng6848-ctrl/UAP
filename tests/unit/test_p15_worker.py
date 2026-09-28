"""P15 Batch 3 — worker entry / lifecycle / shutdown / bounded concurrency (offline).

Every dependency is injected, so the lifecycle, concurrency, heartbeat, recovery and
failure semantics are provable without a database. No test in this module touches
PostgreSQL, the formal ``uap`` database, or any schema object.
"""

from __future__ import annotations

import threading
import time

import pytest

from services.consumer.kernel import EventAllowlist, EventHandlerSpec, production_allowlist
from services.consumer.worker import (
    ConsumerWorker,
    HandlerExecutionError,
    WorkerConfig,
    WorkerConfigurationError,
    WorkerStartupError,
    WorkerState,
)


class _Event:
    def __init__(self, event_id: str, event_type: str = "p15.test_event") -> None:
        self.id = event_id
        self.event_type = event_type
        self.attempts = 0


class _FakeService:
    """Records every transition; shared state is injected through the factory closure."""

    def __init__(self, events, calls, *, heartbeat=True) -> None:
        self._events = events
        self._calls = calls
        self._heartbeat = heartbeat

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def recover_expired(self, *, max_attempts):
        self._calls.append(("recover", max_attempts))
        return {"requeued": 0, "terminated": 0}

    def claim_batch(self, *, worker_id, batch_size, max_attempts, lease_seconds):
        self._calls.append(("claim", worker_id, batch_size))
        batch, self._events[:] = self._events[:batch_size], self._events[batch_size:]
        return batch

    def heartbeat(self, event, *, worker_id, lease_seconds):
        self._calls.append(("heartbeat", event.id))
        verdict = self._heartbeat
        return bool(verdict()) if callable(verdict) else bool(verdict)

    def mark_delivered(self, event, *, worker_id):
        self._calls.append(("delivered", event.id))
        return True

    def mark_retry(self, event, *, worker_id, reason):
        self._calls.append(("retry", event.id, reason))
        return True

    def mark_dead(self, event, *, worker_id, reason):
        self._calls.append(("dead", event.id, reason))
        return True


def _factory(events, calls, **kwargs):
    return lambda: _FakeService(events, calls, **kwargs)


class _BreakingFactory:
    """Succeeds for the startup probe, then fails every later poll (transient outage)."""

    def __init__(self, error: type[BaseException] = RuntimeError) -> None:
        self._error = error

    def __call__(self):
        return self

    def __enter__(self):
        raise self._error("db unavailable")

    def __exit__(self, *_exc):
        return False


def _config(**overrides) -> WorkerConfig:
    base = dict(worker_id="w1")
    base.update(overrides)
    return WorkerConfig(**base)


def _registry(handler, event_type: str = "p15.test_event") -> EventAllowlist:
    allowlist = EventAllowlist()
    spec = EventHandlerSpec(event_type, True, True, True, "naturally_idempotent")
    object.__setattr__(spec, "handler", handler)
    allowlist.register(spec)
    return allowlist


def _registry_without_handler() -> EventAllowlist:
    allowlist = EventAllowlist()
    allowlist.register(EventHandlerSpec(
        "p15.test_event", True, True, True, "naturally_idempotent"
    ))
    return allowlist


def _wait_idle(worker: ConsumerWorker, timeout: float = 3.0) -> None:
    deadline = time.time() + timeout
    while worker.in_flight and time.time() < deadline:
        time.sleep(0.01)


def _names(emitted: list[tuple[str, dict]]) -> set[str]:
    return {name for name, _ in emitted}


# ------------------------------------------------------------------ config
def test_config_defaults_match_the_frozen_o4_bounds() -> None:
    config = _config()
    assert (config.worker_processes, config.concurrency) == (1, 4)
    assert (config.batch_size, config.lease_seconds, config.heartbeat_seconds) == (10, 120, 40)
    assert config.max_attempts == 10


def test_config_fails_closed_on_every_illegal_value() -> None:
    for bad in (
        {"worker_id": "  "},
        {"worker_processes": 2},
        {"batch_size": 0},
        {"batch_size": 11},
        {"concurrency": 0},
        {"concurrency": 5},
        {"lease_seconds": 0},
        {"heartbeat_seconds": 0},
        {"heartbeat_seconds": 120},   # heartbeat == lease
        {"heartbeat_seconds": 121},   # heartbeat > lease
        {"max_attempts": 5},
        {"max_attempts": 11},
        {"poll_interval_seconds": 0},
        {"recovery_interval_seconds": 0},
        {"drain_deadline_seconds": 0},
    ):
        with pytest.raises(WorkerConfigurationError):
            _config(**bad).validate()


def test_config_defaults_are_valid() -> None:
    _config().validate()


# ------------------------------------------------------------- state machine
def test_state_machine_passes_through_starting() -> None:
    emitted: list[tuple[str, dict]] = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([], []),
        on_event=lambda name, fields: emitted.append((name, fields)),
    )
    assert worker.state is WorkerState.CREATED
    observed: list[WorkerState] = []
    original = worker._initialize_identity

    def spy() -> None:
        observed.append(worker.state)
        original()

    worker._initialize_identity = spy  # type: ignore[method-assign]
    worker.start()
    assert observed == [WorkerState.STARTING]
    assert worker.state is WorkerState.RUNNING
    worker.stop()
    assert worker.state is WorkerState.STOPPED
    assert {"worker.startup", "worker.running", "worker.draining",
            "worker.stopped"} <= _names(emitted)


def test_start_is_rejected_from_every_state_except_created() -> None:
    running = ConsumerWorker(_config(), claim_service_factory=_factory([], []))
    running.start()
    with pytest.raises(ValueError):
        running.start()          # never two poll loops / two workers in one instance
    running.stop()
    with pytest.raises(ValueError):
        running.start()          # STOPPED -> RUNNING is not a legal transition


def test_stop_from_created_reaches_stopped_without_starting() -> None:
    worker = ConsumerWorker(_config(), claim_service_factory=_factory([], []))
    assert worker.stop() == {"drained": 0, "cancelled": 0}
    assert worker.state is WorkerState.STOPPED


def test_run_once_requires_running_state() -> None:
    worker = ConsumerWorker(_config(), claim_service_factory=_factory([], []))
    with pytest.raises(ValueError):
        worker.run_once()


# ------------------------------------------------------------------ startup
def test_startup_failure_is_fail_closed() -> None:
    def boom() -> None:
        raise RuntimeError("database unreachable")

    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([], []), dependency_probe=boom
    )
    with pytest.raises(WorkerStartupError):
        worker.start()
    assert worker.state is WorkerState.STOPPED     # never a partially initialized worker


def test_startup_requires_the_runtime_database_dependency() -> None:
    worker = ConsumerWorker(_config(), claim_service_factory=_BreakingFactory())
    with pytest.raises(WorkerStartupError):
        worker.start()
    assert worker.state is WorkerState.STOPPED


# ------------------------------------------------------------------- polling
def test_empty_production_loop_claims_nothing() -> None:
    calls: list = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([], calls), handlers=production_allowlist()
    )
    worker.start()
    result = worker.run_once()
    assert result["claimed"] == 0 and result["dispatched"] == 0
    assert worker.handlers.is_empty is True
    assert worker.state is WorkerState.RUNNING
    worker.stop()


def test_claim_is_bounded_by_batch_limit_and_execution_capacity() -> None:
    calls: list = []
    events = [_Event(f"e{i}") for i in range(11)]
    worker = ConsumerWorker(
        _config(batch_size=10, concurrency=4), claim_service_factory=_factory(events, calls),
        handlers=_registry(lambda _e: None),
    )
    worker.start()
    result = worker.run_once()
    assert result["claimed"] <= 10
    assert ("claim", "w1", 4) in calls      # capacity-aware: 11 events, cap 4
    _wait_idle(worker)
    worker.stop()


def test_poll_failure_is_classified_and_backed_off() -> None:
    slept: list[float] = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_BreakingFactory(),
        sleep=slept.append, dependency_probe=lambda: None,
    )
    worker.start()
    result = worker.run_once()
    assert result["claimed"] == 0
    assert slept and slept[-1] == 5.0       # POLL_ERROR_BACKOFF_SECONDS
    assert worker.state is WorkerState.RUNNING
    worker.stop()


def test_recovery_respects_the_configured_interval() -> None:
    calls: list = []
    clock = {"t": 0.0}
    worker = ConsumerWorker(
        _config(recovery_interval_seconds=30.0),
        claim_service_factory=_factory([], calls), clock=lambda: clock["t"],
    )
    worker.start()
    worker.run_once()
    assert [c[0] for c in calls].count("recover") == 1    # first poll is due
    worker.run_once()
    assert [c[0] for c in calls].count("recover") == 1    # inside the interval
    clock["t"] = 31.0
    worker.run_once()
    assert [c[0] for c in calls].count("recover") == 2    # interval elapsed
    worker.stop()


# ---------------------------------------------------------------- execution
def test_supported_test_event_is_delivered() -> None:
    calls: list = []
    seen: list[str] = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("e1")], calls),
        handlers=_registry(lambda e: seen.append(e.id)),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert seen == ["e1"]
    assert ("delivered", "e1") in calls
    worker.stop()


def test_unsupported_event_type_goes_dead() -> None:
    calls: list = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("x1", "unknown.type")], calls)
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert ("dead", "x1", "unsupported_event_type") in calls
    worker.stop()


def test_unbound_handler_goes_dead() -> None:
    calls: list = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("n1")], calls),
        handlers=_registry_without_handler(),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert ("dead", "n1", "handler_not_bound") in calls
    worker.stop()


def test_retryable_handler_failure_marks_retry() -> None:
    calls: list = []

    def failing(_event):
        raise HandlerExecutionError("transient", retryable=True)

    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("r1")], calls),
        handlers=_registry(failing),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert ("retry", "r1", "transient") in calls
    worker.stop()


def test_non_retryable_handler_failure_marks_dead() -> None:
    calls: list = []

    def denied(_event):
        raise HandlerExecutionError("authorization_denied", retryable=False)

    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("d1")], calls),
        handlers=_registry(denied),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert ("dead", "d1", "authorization_denied") in calls
    assert ("delivered", "d1") not in calls
    worker.stop()


def test_ownership_loss_stops_execution_before_side_effect() -> None:
    calls: list = []
    executed: list[str] = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("o1")], calls, heartbeat=False),
        handlers=_registry(lambda e: executed.append(e.id)),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert executed == []                    # never executed without ownership
    assert ("heartbeat", "o1") in calls
    assert ("delivered", "o1") not in calls
    worker.stop()


def test_heartbeat_db_failure_is_treated_as_ownership_loss() -> None:
    calls: list = []
    emitted: list[tuple[str, dict]] = []

    def broken():
        raise RuntimeError("heartbeat db down")

    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("h1")], calls, heartbeat=broken),
        handlers=_registry(lambda _e: None),
        on_event=lambda name, fields: emitted.append((name, fields)),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert ("delivered", "h1") not in calls
    assert "worker.ownership_lost" in _names(emitted)
    assert "worker.heartbeat_failed" in _names(emitted)
    worker.stop()


def test_heartbeat_monitor_renews_the_lease_during_a_long_execution() -> None:
    calls: list = []
    started = threading.Event()

    def slow(_event):
        started.set()
        time.sleep(0.30)

    worker = ConsumerWorker(
        _config(heartbeat_seconds=0.05, lease_seconds=5),
        claim_service_factory=_factory([_Event("hb1")], calls),
        handlers=_registry(slow),
    )
    worker.start()
    worker.run_once()
    assert started.wait(1.0)
    time.sleep(0.20)
    renewals = [c for c in calls if c[0] == "heartbeat" and c[1] == "hb1"]
    assert len(renewals) >= 2                # initial claim check + managed renewals
    _wait_idle(worker)
    assert ("delivered", "hb1") in calls
    worker.stop()


def test_heartbeat_monitor_ownership_loss_prevents_delivery() -> None:
    calls: list = []
    verdict = {"ok": True}

    def slow(_event):
        time.sleep(0.25)

    worker = ConsumerWorker(
        _config(heartbeat_seconds=0.05, lease_seconds=5),
        claim_service_factory=_factory([_Event("ol1")], calls,
                                       heartbeat=lambda: verdict["ok"]),
        handlers=_registry(slow),
    )
    worker.start()
    worker.run_once()
    time.sleep(0.06)                         # at least one healthy renewal
    verdict["ok"] = False                    # lease stolen by another owner
    time.sleep(0.10)                         # monitor observes the loss
    _wait_idle(worker)
    assert ("delivered", "ol1") not in calls
    worker.stop()


def test_finalize_failure_never_claims_success() -> None:
    calls: list = []
    emitted: list[tuple[str, dict]] = []

    class _NoDeliver(_FakeService):
        def mark_delivered(self, event, *, worker_id):
            self._calls.append(("delivered", event.id))
            raise RuntimeError("db down at finalize")

    worker = ConsumerWorker(
        _config(), claim_service_factory=lambda: _NoDeliver([_Event("f1")], calls),
        handlers=_registry(lambda _e: None),
        on_event=lambda name, fields: emitted.append((name, fields)),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    assert "worker.finalize_failed" in _names(emitted)
    assert "worker.task_success" not in _names(emitted)
    worker.stop()


# ---------------------------------------------------------------- concurrency
def test_concurrency_is_bounded_by_config() -> None:
    peak = {"value": 0}
    active = {"value": 0}
    lock = threading.Lock()

    def slow(_event):
        with lock:
            active["value"] += 1
            peak["value"] = max(peak["value"], active["value"])
        time.sleep(0.05)
        with lock:
            active["value"] -= 1

    events = [_Event(f"c{i}") for i in range(10)]
    worker = ConsumerWorker(
        _config(concurrency=4, batch_size=10),
        claim_service_factory=_factory(events, []), handlers=_registry(slow),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker, timeout=5.0)
    assert peak["value"] <= 4
    worker.stop()


# ------------------------------------------------------------------ shutdown
def test_shutdown_on_empty_queue_stops_cleanly() -> None:
    worker = ConsumerWorker(_config(), claim_service_factory=_factory([], []))
    worker.start()
    result = worker.stop()
    assert result == {"drained": 0, "cancelled": 0}
    assert worker.state is WorkerState.STOPPED


def test_shutdown_drains_active_tasks_within_deadline() -> None:
    def quick(_event):
        time.sleep(0.01)

    events = [_Event(f"d{i}") for i in range(4)]
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory(events, []), handlers=_registry(quick)
    )
    worker.start()
    worker.run_once()
    result = worker.stop(drain_deadline_seconds=2.0)
    assert worker.state is WorkerState.STOPPED
    assert result["drained"] == 4 and result["cancelled"] == 0


def test_shutdown_past_the_deadline_never_delivers_abandoned_work() -> None:
    calls: list = []

    def stuck(_event):
        time.sleep(0.5)

    worker = ConsumerWorker(
        _config(poll_interval_seconds=0.01),
        claim_service_factory=_factory([_Event("s1")], calls),
        handlers=_registry(stuck),
    )
    worker.start()
    worker.run_once()
    time.sleep(0.05)
    result = worker.stop(drain_deadline_seconds=0.05)
    assert result["cancelled"] == 1
    assert worker.state is WorkerState.STOPPED
    time.sleep(0.6)                          # let the abandoned handler finish
    assert ("delivered", "s1") not in calls  # lease recovery decides, not the worker


def test_stop_is_idempotent() -> None:
    worker = ConsumerWorker(_config(), claim_service_factory=_factory([], []))
    worker.start()
    worker.stop()
    assert worker.stop() == {"drained": 0, "cancelled": 0}


# ------------------------------------------------------------- observability
def test_observability_vocabulary_is_emitted_and_carries_no_secret() -> None:
    emitted: list[tuple[str, dict]] = []
    worker = ConsumerWorker(
        _config(), claim_service_factory=_factory([_Event("a1")], []),
        handlers=_registry(lambda _e: None),
        on_event=lambda name, fields: emitted.append((name, fields)),
    )
    worker.start()
    worker.run_once()
    _wait_idle(worker)
    worker.stop()
    assert {
        "worker.startup", "worker.identity", "worker.running", "worker.recovery",
        "worker.claim", "worker.poll", "worker.task_start", "worker.task_success",
        "worker.draining", "worker.stopped",
    } <= _names(emitted)
    assert all("secret" not in str(f).lower() for _, f in emitted)


def test_production_registry_is_empty_and_test_registry_is_explicit() -> None:
    assert production_allowlist().is_empty is True
    production_worker = ConsumerWorker(_config(), claim_service_factory=_factory([], []))
    assert production_worker.handlers.is_empty is True
    injected = _registry(lambda _e: None)
    assert injected.is_empty is False
    assert production_worker.handlers is not injected
