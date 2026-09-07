"""Monitoring primitives.

STEP 0 keeps this to a process-local metric registry so that health and
readiness surfaces have data to report. No external collector is wired in.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricPoint:
    name: str
    value: float
    tags: dict[str, str]


class MetricRegistry:
    """Thread-safe in-memory counters/gauges."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[str, float] = {}

    def increment(self, name: str, amount: float = 1.0) -> None:
        with self._lock:
            self._values[name] = self._values.get(name, 0.0) + amount

    def gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)


_registry = MetricRegistry()


def get_registry() -> MetricRegistry:
    return _registry


def reset_registry() -> None:
    _registry = MetricRegistry()  # noqa: F841 - replaced below
    globals()["_registry"] = MetricRegistry()


__all__ = ["MetricPoint", "MetricRegistry", "get_registry", "reset_registry"]
