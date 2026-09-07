"""Event contracts.

Events are immutable facts. The bus interface is intentionally tiny: publish
and subscribe. No transport is chosen here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol, runtime_checkable

EVENT_SCHEMA_VERSION = 1


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class DomainEvent:
    """An immutable fact about something that already happened."""

    type: str
    tenant_id: str
    actor_id: str | None = None
    space_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=_new_id)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: int = EVENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.type or "." not in self.type:
            raise ValueError("event type must look like 'namespace.aggregate.action'")


EventHandler = Callable[[DomainEvent], None]


@runtime_checkable
class EventBus(Protocol):
    def publish(self, event: DomainEvent) -> None:
        ...

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        ...


__all__ = ["EVENT_SCHEMA_VERSION", "DomainEvent", "EventHandler", "EventBus"]
