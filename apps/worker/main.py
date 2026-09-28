"""P15 C-5 consumer worker process entry.

Process sequence (frozen contract §6/§7 · Batch 4 §10):

    load config -> initialize the existing runtime DB dependency ->
    construct the consumer worker -> install SIGINT/SIGTERM ->
    poll -> drain -> exit

The entry is adaptation only: it owns no SQL, no business rule, no
authorization decision and no schema knowledge. It reuses the existing P14
runtime bootstrap (``infrastructure.runtime.lifecycle.RuntimeApplication``)
exactly like ``apps/api`` does -- there is deliberately no second bootstrap.

The production event allowlist stays EMPTY (§8 / O-5): the process boots,
polls, claims zero production events and stays healthy. Test-only handlers are
never imported here, so the production registry cannot be polluted.
"""

from __future__ import annotations

import signal
import threading
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Iterator

from config.settings import Settings, get_settings
from infrastructure.database.config import DatabaseConfig
from infrastructure.logging import configure_logging, get_logger
from infrastructure.runtime.lifecycle import DEFAULT_REQUIRED_ROLE, RuntimeApplication
from services.consumer.claim import ClaimService
from services.consumer.kernel import WORKER_PROCESS_COUNT, production_allowlist
from services.consumer.worker import (
    ConsumerWorker,
    WorkerConfig,
    WorkerConfigurationError,
    WorkerStartupError,
)

logger = get_logger("uap.worker")

#: Bounded drain: shutdown must never wait forever (Batch 3 §26).
WORKER_DRAIN_DEADLINE_SECONDS = 30.0

EXIT_OK = 0
EXIT_STARTUP_FAILURE = 1
EXIT_CONFIGURATION_FAILURE = 2

_SERVICE_NAME = "uap-worker"


def bootstrap_logging(settings: Settings) -> None:
    configure_logging(
        level=settings.LOG_LEVEL,
        fmt=settings.LOG_FORMAT,
        service=_SERVICE_NAME,
    )


def required_runtime_role(settings: Settings) -> str | None:
    """Mirror ``apps/api``: ``uap_runtime`` is mandatory outside local dev.

    The Wave 1 principal assertion (``current_user == session_user == DSN
    role``) always applies; only the extra "must be exactly uap_runtime"
    requirement is environment-scoped.
    """
    return DEFAULT_REQUIRED_ROLE if settings.APP_ENV in ("staging", "production") else None


def log_operational_event(name: str, fields: dict[str, Any]) -> None:
    """Operational worker event -> structured log. Never an audit row (§34)."""
    logger.info("uap.worker.event", extra={"context": {"event": name, **fields}})


def build_worker(
    runtime: RuntimeApplication,
    *,
    worker_id: str | None = None,
    on_event: Callable[[str, dict[str, Any]], None] | None = None,
) -> ConsumerWorker:
    """Construct the consumer worker on top of an already started runtime.

    Each call opens a short-lived transaction that yields a Batch 2
    ``ClaimService``; the worker never holds a transaction open across a handler
    execution and never issues SQL of its own.
    """
    database = runtime.database

    @contextmanager
    def _claim_service() -> Iterator[ClaimService]:
        with database.transaction() as session:
            yield ClaimService(session)

    config = WorkerConfig(
        worker_id=worker_id or f"worker-{uuid.uuid4().hex[:12]}",
        worker_processes=WORKER_PROCESS_COUNT,
    )
    return ConsumerWorker(
        config,
        claim_service_factory=_claim_service,
        handlers=production_allowlist(),
        on_event=on_event or log_operational_event,
    )


def install_signal_handlers(
    worker: ConsumerWorker, *, install: bool | None = None
) -> Callable[[int, Any], None]:
    """SIGINT/SIGTERM -> graceful drain. Returns the handler (for tests).

    Installation is skipped automatically when the current thread is not the
    main thread (``signal.signal`` is main-thread only); the handler itself is
    still returned so the shutdown path stays testable.
    """

    def _handle_stop(signum: int, _frame: Any) -> None:
        logger.info(
            "uap.worker.stop_signal",
            extra={"context": {"event": "worker.stop_signal", "signal": int(signum)}},
        )
        worker.stop(drain_deadline_seconds=WORKER_DRAIN_DEADLINE_SECONDS)

    should_install = (
        threading.current_thread() is threading.main_thread()
        if install is None
        else install
    )
    if should_install:
        signal.signal(signal.SIGINT, _handle_stop)
        signal.signal(signal.SIGTERM, _handle_stop)
    return _handle_stop


def main(
    argv: list[str] | None = None,  # noqa: ARG001 - process entry signature
    *,
    settings: Settings | None = None,
    runtime_factory: Callable[[], RuntimeApplication] | None = None,
) -> int:
    """Run the consumer worker process. Fail-closed: never a half-started worker."""
    settings = settings or get_settings()
    bootstrap_logging(settings)
    runtime = (runtime_factory or RuntimeApplication)()

    try:
        runtime.start(
            settings,
            config=DatabaseConfig.from_settings(settings),
            require_role=required_runtime_role(settings),
        )
    except Exception as exc:  # noqa: BLE001 - startup must fail closed
        logger.error(
            "uap.worker.startup_failed",
            extra={"context": {"event": "worker.startup_failed",
                               "error": type(exc).__name__}},
        )
        return EXIT_STARTUP_FAILURE

    worker: ConsumerWorker | None = None
    try:
        try:
            worker = build_worker(runtime)
        except WorkerConfigurationError as exc:
            logger.error(
                "uap.worker.configuration_rejected",
                extra={"context": {"event": "worker.configuration_rejected",
                                   "error": type(exc).__name__}},
            )
            return EXIT_CONFIGURATION_FAILURE

        install_signal_handlers(worker)
        try:
            worker.start()
        except WorkerStartupError as exc:
            logger.error(
                "uap.worker.startup_failed",
                extra={"context": {"event": "worker.startup_failed",
                                   "error": type(exc).__name__}},
            )
            return EXIT_STARTUP_FAILURE

        worker.run_until_stopped()
        return EXIT_OK
    finally:
        # Graceful drain on every exit path: a stop signal, a crash, or EOF.
        if worker is not None:
            worker.stop(drain_deadline_seconds=WORKER_DRAIN_DEADLINE_SECONDS)
        runtime.stop()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "EXIT_CONFIGURATION_FAILURE",
    "EXIT_OK",
    "EXIT_STARTUP_FAILURE",
    "WORKER_DRAIN_DEADLINE_SECONDS",
    "bootstrap_logging",
    "build_worker",
    "install_signal_handlers",
    "log_operational_event",
    "main",
    "required_runtime_role",
]
