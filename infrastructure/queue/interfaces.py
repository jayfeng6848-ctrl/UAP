"""Abstract queue interface (contract only, no broker wired in STEP 0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class QueueMessage:
    """A unit of asynchronous work."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)


@runtime_checkable
class QueueClient(Protocol):
    def publish(self, topic: str, message: QueueMessage) -> None:
        """Enqueue ``message`` on ``topic``."""
        ...

    def consume(self, topic: str, *, batch_size: int = 1) -> list[QueueMessage]:
        """Pull up to ``batch_size`` messages from ``topic`` (non-blocking)."""
        ...

    def ack(self, topic: str, message: QueueMessage) -> None:
        ...

    def depth(self, topic: str) -> int:
        """Approximate number of pending messages."""
        ...

    def ping(self) -> bool:
        ...


class NullQueue:
    """In-memory queue stub that records but never delivers.

    It exists so callers have a concrete object in STEP 0 and so tests can
    assert that work *would* have been enqueued.
    """

    def __init__(self) -> None:
        self._topics: dict[str, list[QueueMessage]] = {}

    def publish(self, topic: str, message: QueueMessage) -> None:
        self._topics.setdefault(topic, []).append(message)

    def consume(self, topic: str, *, batch_size: int = 1) -> list[QueueMessage]:
        pending = self._topics.get(topic, [])
        taken, remaining = pending[:batch_size], pending[batch_size:]
        self._topics[topic] = remaining
        return taken

    def ack(self, topic: str, message: QueueMessage) -> None:
        return None

    def depth(self, topic: str) -> int:
        return len(self._topics.get(topic, []))

    def ping(self) -> bool:
        return False


__all__ = ["QueueMessage", "QueueClient", "NullQueue"]
