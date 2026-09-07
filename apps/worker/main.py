"""Background worker (placeholder).

STEP 0: no jobs are registered. The worker only proves the process can boot,
configure logging and shut down cleanly.
"""

from __future__ import annotations

import signal
import time

from config.settings import get_settings
from infrastructure.logging import get_logger, log_context

logger = get_logger("uap.worker")

_RUNNING = True


def _handle_stop(signum, frame) -> None:  # noqa: ANN001 - signal signature
    global _RUNNING
    _RUNNING = False
    logger.info("worker.stop_signal_received", extra={"context": {"event": "worker.stop"}})


def main() -> int:
    settings = get_settings()
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    with log_context(event="worker.startup"):
        logger.info("uap.worker.started env=%s", settings.APP_ENV)

    while _RUNNING:
        # No queues are wired in STEP 0; idle until a stop signal arrives.
        time.sleep(1.0)

    logger.info("uap.worker.stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
