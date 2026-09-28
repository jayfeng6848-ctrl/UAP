"""Event contracts.

Events are immutable facts. The bus interface is intentionally tiny: publish
and subscribe. No transport is chosen here.

``EventBus != Outbox`` (``D-P10-02``): the bus below is an **optional in-process
auxiliary**. It is not the durable delivery boundary and must never replace the
``events`` outbox carrier, whose claim / lease / retry semantics live in the
application layer. See ``P10_IMPLEMENTATION_CONTRACT.md`` §6 before wiring any
transport.

Event identifiers are time-ordered, application-generated **UUIDv7** values
(``D-AUTH-22`` / ``D-P10-02``). The canonical generator is
:func:`core.audit.interfaces.new_event_id` — mirrored by the database function
``uap_uuid_v7()``; this module delegates to it rather than duplicating it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol, runtime_checkable

from core.audit.interfaces import new_event_id

EVENT_SCHEMA_VERSION = 1


def _new_id() -> str:
    return new_event_id()


@dataclass(frozen=True)
class DomainEvent:
    """An immutable fact about something that already happened."""

    type: str
    # The frozen P10 schema allows NULL: platform-level events carry no tenant.
    tenant_id: str | None = None
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
