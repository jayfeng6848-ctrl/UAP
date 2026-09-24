"""Authorization decision audit boundary.

Builds the record that explains *why* an action was allowed, denied or held for
approval. This is deliberately not the same thing as a tool-execution record:
one describes a decision, the other describes what a tool then did, and merging
them would destroy both.

Persistence is deferred: this boundary produces records and hands them to an
optional sink. It never creates tables and never opens a write path of its own.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from core.audit import AuditEvent, AuditSink, AuthorizationDecisionAudit
from core.permission import Decision
from core.resource import ResourceRef

DEFAULT_CAPACITY = 256


class AuditBoundary:
    """Produce authorization-decision audit records.

    With no sink configured the boundary keeps a small bounded in-memory window
    so callers and tests can inspect decisions. That window is not a durable
    audit trail and must never be treated as one.
    """

    def __init__(self, sink: AuditSink | None = None, capacity: int = DEFAULT_CAPACITY) -> None:
        self._sink = sink
        self._window: deque[AuditEvent] = deque(maxlen=capacity)

    def record(
        self,
        *,
        decision: Decision,
        action: str,
        resource: ResourceRef,
        subject_id: str,
        subject_type: str,
        tenant_id: str | None = None,
        space_id: str | None = None,
        delegator_id: str | None = None,
        actor_id: str | None = None,
        risk_level: str | None = None,
        approval_required: bool = False,
        request_id: str | None = None,
    ) -> AuthorizationDecisionAudit:
        entry = AuthorizationDecisionAudit(
            subject_id=subject_id,
            subject_type=subject_type,
            action=action,
            resource_type=resource.type,
            resource_id=resource.id,
            decision=decision.effect,
            reason=decision.reason,
            tenant_id=tenant_id,
            space_id=space_id,
            delegator_id=delegator_id,
            actor_id=actor_id,
            policy_version=decision.policy_version,
            risk_level=risk_level,
            approval_required=approval_required,
            request_id=request_id,
        )
        event = entry.as_event()
        self._window.append(event)
        if self._sink is not None:
            self._sink.write(event)
        return entry

    def recent(self) -> tuple[AuditEvent, ...]:
        """The bounded in-memory window; not a durable audit trail."""
        return tuple(self._window)

    def drain(self) -> Iterable[AuditEvent]:
        while self._window:
            yield self._window.popleft()


__all__ = ["AuditBoundary", "DEFAULT_CAPACITY"]
