"""P15 Batch 3 — worker entry / lifecycle / shutdown / bounded concurrency.

Frozen parameters (PDL Appendix S · O-4): worker process count = 1,
concurrency = 4, batch <= 10, lease = 120s, heartbeat = 40s.

The worker owns no SQL of its own: it drives the Batch 2 ``ClaimService`` through an
injected factory, executes handlers from a CLOSED allowlist, and keeps the production
allowlist EMPTY until a producer + handler + authorization semantics + acceptance
coverage + provable idempotency all exist.

Implementation details (finite, configurable, testable — NOT new frozen decisions):
  * poll interval, recovery interval and drain deadline (§16 / §26 / §48);
  * claims are capacity-aware: the worker never claims more events than it can execute
    concurrently, so a claimed event never waits un-renewed (§18);
  * one managed heartbeat thread renews the lease of every in-flight execution (§22)
    and classifies ownership loss (§23 / §43).

All dependencies (clock, sleep, claim service factory, handler registry, dependency
probe) are injectable so lifecycle, concurrency and failure semantics are verifiable
without a database.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .kernel import (
    CLAIM_BATCH_SIZE,
    HEARTBEAT_SECONDS,
    LEASE_SECONDS,
    MAX_ATTEMPTS,
    TERMINAL_REASON_UNSUPPORTED_EVENT_TYPE,
    WORKER_CONCURRENCY,
    WORKER_PROCESS_COUNT,
    EventAllowlist,
    UnsupportedEventType,
    production_allowlist,
)

DEFAULT_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_RECOVERY_INTERVAL_SECONDS = 30.0
DEFAULT_DRAIN_DEADLINE_SECONDS = 30.0
POLL_ERROR_BACKOFF_SECONDS = 5.0
DRAIN_TICK_SECONDS = 0.02
HEARTBEAT_JOIN_TIMEOUT_SECONDS = 5.0
HANDLER_NOT_BOUND_REASON = "handler_not_bound"


class WorkerConfigurationError(ValueError):
    """The worker configuration violates the frozen O-4 bounds (§30/§31)."""


class WorkerStartupError(RuntimeError):
    """Startup failed: the worker never reaches RUNNING (§10 fail-closed)."""


class WorkerState(str, Enum):
    """Runtime/application state only — never a database enum (§11)."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    DRAINING = "draining"
    STOPPED = "stopped"


@dataclass(frozen=True)
class WorkerConfig:
    """Worker configuration. Bounds are the frozen O-4 / O-2 values."""

    worker_id: str
    worker_processes: int = WORKER_PROCESS_COUNT
    batch_size: int = CLAIM_BATCH_SIZE
    concurrency: int = WORKER_CONCURRENCY
    lease_seconds: int = LEASE_SECONDS
    heartbeat_seconds: int = HEARTBEAT_SECONDS
    max_attempts: int = MAX_ATTEMPTS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    recovery_interval_seconds: float = DEFAULT_RECOVERY_INTERVAL_SECONDS
    drain_deadline_seconds: float = DEFAULT_DRAIN_DEADLINE_SECONDS

    def validate(self) -> None:
        """Fail closed on any out-of-bound value: never fall back to unsafe defaults."""
        if not self.worker_id or not self.worker_id.strip():
            raise WorkerConfigurationError("worker_id must be a non-empty process-scope id")
        if self.worker_processes != WORKER_PROCESS_COUNT:
            raise WorkerConfigurationError(
                f"worker_processes must be {WORKER_PROCESS_COUNT}"
                " (multi-process scaling is FUTURE — §5/§47)"
            )
        if not 1 <= self.batch_size <= CLAIM_BATCH_SIZE:
            raise WorkerConfigurationError(f"batch_size must be within 1..{CLAIM_BATCH_SIZE}")
        if not 1 <= self.concurrency <= WORKER_CONCURRENCY:
            raise WorkerConfigurationError(f"concurrency must be within 1..{WORKER_CONCURRENCY}")
        if self.lease_seconds < 1:
            raise WorkerConfigurationError("lease_seconds must be >= 1")
        if not 0 < self.heartbeat_seconds < self.lease_seconds:
            raise WorkerConfigurationError(
                "heartbeat_seconds must be > 0 and strictly shorter than lease_seconds"
            )
        if self.max_attempts != MAX_ATTEMPTS:
            raise WorkerConfigurationError(
                f"max_attempts must be exactly {MAX_ATTEMPTS} (§31)"
            )
        for name in ("poll_interval_seconds", "recovery_interval_seconds",
                     "drain_deadline_seconds"):
            if getattr(self, name) <= 0:
                raise WorkerConfigurationError(f"{name} must be > 0")


class HandlerExecutionError(Exception):
    """A handler failed. ``retryable`` decides pending-vs-dead (contract §9)."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class ConsumerWorker:
    """Bounded-concurrency consumer worker with a crash-safe lifecycle."""

    def __init__(
        self,
        config: WorkerConfig,
        *,
        claim_service_factory: Callable[[], Any],
        handlers: EventAllowlist | None = None,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
        dependency_probe: Callable[[], None] | None = None,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        config.validate()
        self._config = config
        self._factory = claim_service_factory
        self._handlers = handlers if handlers is not None else production_allowlist()
        self._sleep = sleep or time.sleep
        self._clock = clock or time.monotonic
        self._dependency_probe = dependency_probe or self._probe_database
        self._on_event = on_event or (lambda _name, _fields: None)
        self._state = WorkerState.CREATED
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()
        self._in_flight: dict[str, Any] = {}
        self._ownership_lost: set[str] = set()
        self._abandoned: set[str] = set()
        self._stop_requested = False
        self._last_recovery_at: float | None = None
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

    # ------------------------------------------------------------------ state
    @property
    def state(self) -> WorkerState:
        return self._state

    @property
    def in_flight(self) -> int:
        with self._lock:
            return len(self._in_flight)

    @property
    def handlers(self) -> EventAllowlist:
        return self._handlers

    @property
    def config(self) -> WorkerConfig:
        return self._config

    # ---------------------------------------------------------------- startup
    def start(self) -> None:
        """validate config -> observability -> DB dependency -> identity -> RUNNING."""
        if self._state is not WorkerState.CREATED:
            raise ValueError(f"cannot start from state {self._state.value}")
        self._state = WorkerState.STARTING
        self._emit("worker.startup", {
            "worker_id": self._config.worker_id,
            "worker_processes": self._config.worker_processes,
            "concurrency": self._config.concurrency,
            "batch_size": self._config.batch_size,
            "lease_seconds": self._config.lease_seconds,
            "heartbeat_seconds": self._config.heartbeat_seconds,
            "max_attempts": self._config.max_attempts,
        })
        try:
            self._config.validate()          # 1. configuration
            self._dependency_probe()         # 2. runtime DB dependency
            self._initialize_identity()      # 3. process-scope worker identity
        except Exception as exc:  # noqa: BLE001 - fail closed, never a half-started worker
            self._state = WorkerState.STOPPED
            self._emit("worker.startup_failed", {"error": type(exc).__name__})
            raise WorkerStartupError(
                f"worker startup failed during initialization: {type(exc).__name__}"
            ) from exc
        self._executor = ThreadPoolExecutor(
            max_workers=self._config.concurrency, thread_name_prefix="p15-consumer"
        )
        self._stop_requested = False
        self._last_recovery_at = None
        self._heartbeat_stop.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, name="p15-heartbeat", daemon=True
        )
        self._state = WorkerState.RUNNING
        self._heartbeat_thread.start()
        self._emit("worker.running", {"worker_id": self._config.worker_id})

    def _probe_database(self) -> None:
        """Prove the runtime DB dependency is reachable before the first claim (§10)."""
        with self._factory():
            return None

    def _initialize_identity(self) -> None:
        """Process-scope identity: one worker_id, stable for the lifetime (§29)."""
        self._emit("worker.identity", {"worker_id": self._config.worker_id})

    # --------------------------------------------------------------- shutdown
    def stop(self, *, drain_deadline_seconds: float | None = None) -> dict[str, int]:
        """Graceful shutdown: stop claiming, drain in-flight work, then exit (§25/§26)."""
        if self._state is WorkerState.STOPPED:
            return {"drained": 0, "cancelled": 0}
        if self._state is WorkerState.CREATED:
            self._state = WorkerState.STOPPED
            self._emit("worker.stopped", {"worker_id": self._config.worker_id})
            return {"drained": 0, "cancelled": 0}

        self._stop_requested = True
        self._state = WorkerState.DRAINING
        pending = self.in_flight
        self._emit("worker.draining", {"in_flight": pending})

        deadline = drain_deadline_seconds or self._config.drain_deadline_seconds
        waited = 0.0
        while self.in_flight and waited < deadline:
            # Draining must really wait; the injectable ``sleep`` only paces the poll loop.
            time.sleep(DRAIN_TICK_SECONDS)
            waited += DRAIN_TICK_SECONDS

        cancelled = 0
        if self.in_flight:
            with self._lock:
                cancelled = len(self._in_flight)
                # Never finalize work we stopped waiting for: the lease expires and
                # O-1 recovery decides the outcome instead.
                self._abandoned.update(self._in_flight)
                self._in_flight.clear()
            self._emit("worker.drain_deadline_exceeded", {"cancelled": cancelled})

        self._heartbeat_stop.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=HEARTBEAT_JOIN_TIMEOUT_SECONDS)
            self._heartbeat_thread = None
        if self._executor is not None:
            # The pool threads keep running to completion; their results are ignored
            # because the event is already marked abandoned.
            self._executor.shutdown(wait=False)
            self._executor = None
        self._state = WorkerState.STOPPED
        self._emit("worker.stopped", {"worker_id": self._config.worker_id})
        return {"drained": max(pending - cancelled, 0), "cancelled": cancelled}

    # -------------------------------------------------------------- poll loop
    def run_once(self) -> dict[str, int]:
        """One poll iteration: scheduled recovery + one bounded, capacity-aware claim."""
        if self._state is not WorkerState.RUNNING:
            raise ValueError(f"worker is not running (state={self._state.value})")
        result = {"claimed": 0, "dispatched": 0, "requeued": 0, "terminated": 0}
        capacity = self._config.concurrency - self.in_flight
        if capacity <= 0:  # §18: never claim without bounded execution capacity
            return result
        effective_batch = min(self._config.batch_size, capacity)
        try:
            with self._factory() as service:
                recovered = self._maybe_recover(service)
                claimed = service.claim_batch(
                    worker_id=self._config.worker_id,
                    batch_size=effective_batch,
                    max_attempts=self._config.max_attempts,
                    lease_seconds=self._config.lease_seconds,
                )
        except Exception as exc:  # noqa: BLE001 - poll failures are transient (§15)
            self._emit("worker.poll_failed", {"error": type(exc).__name__})
            self._sleep(POLL_ERROR_BACKOFF_SECONDS)
            return result
        result["requeued"] = int(recovered.get("requeued", 0))
        result["terminated"] = int(recovered.get("terminated", 0))
        result["claimed"] = len(claimed)
        if claimed:
            self._emit("worker.claim", {
                "claimed": len(claimed),
                "batch_size": self._config.batch_size,
                "effective_batch": effective_batch,
            })
        for event in claimed:
            if self._stop_requested:
                break
            self._dispatch(event)
            result["dispatched"] += 1
        if result["claimed"] or result["requeued"] or result["terminated"]:
            self._emit("worker.poll", dict(result))
        return result

    def _maybe_recover(self, service: Any) -> dict[str, int]:
        """O-1 recovery on a bounded interval — not on every loop (§16)."""
        now = self._clock()
        if (self._last_recovery_at is not None
                and now - self._last_recovery_at < self._config.recovery_interval_seconds):
            return {"requeued": 0, "terminated": 0}
        self._last_recovery_at = now
        stats = service.recover_expired(max_attempts=self._config.max_attempts)
        self._emit("worker.recovery", {
            "requeued": int(stats.get("requeued", 0)),
            "terminated": int(stats.get("terminated", 0)),
        })
        return stats

    def run_until_stopped(self, *, max_iterations: int | None = None) -> None:
        iterations = 0
        while self._state is WorkerState.RUNNING:
            self.run_once()
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                return
            if self._state is WorkerState.RUNNING:
                self._sleep(self._config.poll_interval_seconds)

    # ------------------------------------------------------------- dispatch
    def _dispatch(self, event: Any) -> None:
        with self._lock:
            self._in_flight[event.id] = event
        assert self._executor is not None
        self._executor.submit(self._handle, event)

    def _handle(self, event: Any) -> None:
        try:
            self._execute(event)
        finally:
            with self._lock:
                self._in_flight.pop(event.id, None)

    def _may_finalize(self, event: Any) -> bool:
        """False when the lease was lost or the execution was abandoned (§23/§26)."""
        return event.id not in self._ownership_lost and event.id not in self._abandoned

    def _mark_ownership_lost(self, event: Any, *, error: str | None = None) -> None:
        with self._lock:
            self._ownership_lost.add(event.id)
        if error is not None:
            self._emit("worker.heartbeat_failed", {"event_id": event.id, "error": error})
        self._emit("worker.ownership_lost", {"event_id": event.id})

    def _abandon(self, event: Any) -> None:
        self._emit("worker.task_abandoned", {"event_id": event.id})

    def _finalize_dead(self, event: Any, reason: str) -> None:
        if not self._may_finalize(event):
            self._abandon(event)
            return
        try:
            with self._factory() as service:
                service.mark_dead(event, worker_id=self._config.worker_id, reason=reason)
        except Exception as exc:  # noqa: BLE001 - §44: finalize failure is never success
            self._emit("worker.finalize_failed", {"event_id": event.id,
                                                  "error": type(exc).__name__})
            return
        self._emit("worker.task_dead", {"event_id": event.id, "reason": reason})

    def _execute(self, event: Any) -> None:
        try:
            spec = self._handlers.resolve(event.event_type)
        except UnsupportedEventType:
            self._finalize_dead(event, TERMINAL_REASON_UNSUPPORTED_EVENT_TYPE)
            return

        handler = getattr(spec, "handler", None)
        if handler is None:
            self._finalize_dead(event, HANDLER_NOT_BOUND_REASON)
            return

        self._emit("worker.task_start", {
            "event_id": event.id,
            "event_type": event.event_type,
            "attempt": getattr(event, "attempts", None),
        })
        try:
            with self._factory() as service:
                owned = service.heartbeat(event, worker_id=self._config.worker_id,
                                          lease_seconds=self._config.lease_seconds)
        except Exception as exc:  # noqa: BLE001 - §43: never assume ownership
            self._mark_ownership_lost(event, error=type(exc).__name__)
            return
        if not owned:
            self._mark_ownership_lost(event)
            return

        # The handler runs outside any claim transaction: the claim session ended above.
        try:
            handler(event)
        except HandlerExecutionError as exc:
            if not self._may_finalize(event):
                self._abandon(event)
                return
            if not exc.retryable:
                self._finalize_dead(event, str(exc))
                return
            try:
                with self._factory() as service:
                    service.mark_retry(event, worker_id=self._config.worker_id,
                                       reason=str(exc))
            except Exception as finalize_exc:  # noqa: BLE001 - §44
                self._emit("worker.finalize_failed", {"event_id": event.id,
                                                      "error": type(finalize_exc).__name__})
                return
            self._emit("worker.task_retry", {"event_id": event.id, "reason": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001 - unknown => terminal denial (§5)
            self._finalize_dead(event, type(exc).__name__)
            return

        if not self._may_finalize(event):
            self._abandon(event)
            return
        try:
            with self._factory() as service:
                delivered = service.mark_delivered(event, worker_id=self._config.worker_id)
        except Exception as exc:  # noqa: BLE001 - §44: never claim success
            self._emit("worker.finalize_failed", {"event_id": event.id,
                                                  "error": type(exc).__name__})
            return
        if delivered:
            self._emit("worker.task_success", {"event_id": event.id})
        else:
            self._emit("worker.finalize_failed", {"event_id": event.id})

    # ------------------------------------------------- heartbeat coordination
    def _heartbeat_loop(self) -> None:
        """One managed heartbeat lifecycle for the whole worker (§22)."""
        interval = float(self._config.heartbeat_seconds)
        while not self._heartbeat_stop.wait(interval):
            if self._state is WorkerState.STOPPED:
                return
            self._heartbeat_once()

    def _heartbeat_once(self) -> None:
        with self._lock:
            events = [event for event_id, event in self._in_flight.items()
                      if event_id not in self._ownership_lost
                      and event_id not in self._abandoned]
        for event in events:
            try:
                with self._factory() as service:
                    owned = service.heartbeat(event, worker_id=self._config.worker_id,
                                              lease_seconds=self._config.lease_seconds)
            except Exception as exc:  # noqa: BLE001 - §43: ownership unknown => not owned
                self._mark_ownership_lost(event, error=type(exc).__name__)
                continue
            if owned:
                self._emit("worker.heartbeat", {"event_id": event.id})
            else:
                self._mark_ownership_lost(event)

    def _emit(self, name: str, fields: dict[str, Any]) -> None:
        self._on_event(name, fields)


__all__ = [
    "DRAIN_TICK_SECONDS",
    "DEFAULT_DRAIN_DEADLINE_SECONDS",
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "DEFAULT_RECOVERY_INTERVAL_SECONDS",
    "HANDLER_NOT_BOUND_REASON",
    "HEARTBEAT_JOIN_TIMEOUT_SECONDS",
    "POLL_ERROR_BACKOFF_SECONDS",
    "WORKER_PROCESS_COUNT",
    "ConsumerWorker",
    "HandlerExecutionError",
    "WorkerConfig",
    "WorkerConfigurationError",
    "WorkerStartupError",
    "WorkerState",
]
