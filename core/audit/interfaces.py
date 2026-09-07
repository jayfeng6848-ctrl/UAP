"""Audit contracts.

Audit records are append-only and must be written for every privileged,
agent-driven or policy-relevant action.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

AUDIT_OUTCOMES = ("success", "denied", "error")


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class AuditEvent:
    action: str
    outcome: str
    actor_id: str | None = None
    tenant_id: str | None = None
    space_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=_new_id)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.outcome not in AUDIT_OUTCOMES:
            raise ValueError(f"invalid audit outcome {self.outcome!r}")


@runtime_checkable
class AuditSink(Protocol):
    def write(self, event: AuditEvent) -> None:
        ...


__all__ = ["AUDIT_OUTCOMES", "AuditEvent", "AuditSink"]
