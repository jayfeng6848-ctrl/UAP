"""Bounded retry helper for idempotent infrastructure operations.

P14 RTA-07 / Wave 1 §11: retry is allowed only for clearly idempotent
infrastructure operations (e.g. establishing a connection). Authorization,
constraint, credential and security failures are never retried so that a retry
can never mask a security outcome.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from .errors import is_retryable

T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY_SECONDS = 0.05


def retry_idempotent(
    operation: Callable[[], T],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay_seconds: float = DEFAULT_BASE_DELAY_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run ``operation`` under a bounded retry policy.

    ``max_attempts`` bounds the total number of invocations (1 = no retry).
    Only retryable taxonomy categories are retried; everything else propagates
    on the first failure.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 0
    while True:
        attempt += 1
        try:
            return operation()
        except BaseException as exc:  # noqa: BLE001 - re-raised unless retryable
            if attempt >= max_attempts or not is_retryable(exc):
                raise
            sleep(base_delay_seconds * (2 ** (attempt - 1)))


__all__ = ["retry_idempotent", "DEFAULT_MAX_ATTEMPTS", "DEFAULT_BASE_DELAY_SECONDS"]
