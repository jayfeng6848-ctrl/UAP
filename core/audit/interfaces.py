"""Audit contracts.

Audit records are append-only and must be written for every privileged,
agent-driven or policy-relevant action.

An **authorization decision audit** is not a **tool execution audit**: the two
are different concepts with different fields, and they must never be merged.
This module defines the *contract* only — the persistence carrier is deferred.

Event identifiers are time-ordered, application-generated UUIDv7 values.
"""

from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

AUDIT_OUTCOMES = ("success", "denied", "error")

AUDIT_DECISIONS = ("ALLOW", "DENY", "REQUIRES_APPROVAL")

_UUID7_MS_MASK = (1 << 48) - 1


def new_event_id() -> str:
    """Return a UUIDv7 string: globally unique and time ordered.

    The timestamp prefix gives index locality and a natural event chronology,
    which matters for partitioning and archiving later on.
    """
    millis = int(time.time() * 1000) & _UUID7_MS_MASK
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    value = (millis << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return str(uuid.UUID(int=value))


def _new_id() -> str:
    return new_event_id()


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
    # Authorization decision audit fields.
    subject_id: str | None = None
    subject_type: str | None = None
    delegator_id: str | None = None
    decision: str | None = None
    reason: str | None = None
    policy_version: str | None = None
    risk_level: str | None = None
    approval_required: bool | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in AUDIT_OUTCOMES:
            raise ValueError(f"invalid audit outcome {self.outcome!r}")
        if self.decision is not None and self.decision not in AUDIT_DECISIONS:
            raise ValueError(f"invalid audit decision {self.decision!r}")


@dataclass(frozen=True)
class AuthorizationDecisionAudit:
    """The authorization-decision audit record shape (contract only).

    Distinct from a tool-execution record: it captures *why* an action was
    permitted, denied or held for approval, not what the tool then did.
    """

    subject_id: str
    subject_type: str
    action: str
    resource_type: str
    resource_id: str
    decision: str
    reason: str
    tenant_id: str | None = None
    space_id: str | None = None
    delegator_id: str | None = None
    actor_id: str | None = None
    policy_version: str | None = None
    risk_level: str | None = None
    approval_required: bool = False
    request_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.decision not in AUDIT_DECISIONS:
            raise ValueError(f"invalid audit decision {self.decision!r}")

    def as_event(self) -> AuditEvent:
        """Render this record as a generic audit event (still not persisted)."""
        outcome = "success" if self.decision == "ALLOW" else "denied"
        return AuditEvent(
            action=self.action,
            outcome=outcome,
            actor_id=self.actor_id,
            tenant_id=self.tenant_id,
            space_id=self.space_id,
            target_type=self.resource_type,
            target_id=self.resource_id,
            subject_id=self.subject_id,
            subject_type=self.subject_type,
            delegator_id=self.delegator_id,
            decision=self.decision,
            reason=self.reason,
            policy_version=self.policy_version,
            risk_level=self.risk_level,
            approval_required=self.approval_required,
            request_id=self.request_id,
        )


@runtime_checkable
class AuditSink(Protocol):
    def write(self, event: AuditEvent) -> None:
        ...


__all__ = [
    "AUDIT_DECISIONS",
    "AUDIT_OUTCOMES",
    "AuditEvent",
    "AuditSink",
    "AuthorizationDecisionAudit",
    "new_event_id",
]
