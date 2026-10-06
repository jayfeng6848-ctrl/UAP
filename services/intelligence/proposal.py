"""Ephemeral, session-bound, non-persistent proposals (OQ-CUI-05 = A).

No table, no event stream, no history: the authoritative record lives only in this
process, keyed by an unguessable 128-bit id and bound to the authenticated actor +
tenant. ``consume`` makes a proposal single-use (non-replay); ``expired`` enforces
the TTL. Anything that cannot be proven here must fail closed.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

#: OQ-CUI-05: proposals must expire. Five minutes is the V1 bound.
PROPOSAL_TTL_SECONDS = 300


@dataclass(frozen=True)
class EphemeralProposal:
    proposal_id: str
    actor_id: str
    tenant_id: str
    scope: str
    resource_type: str
    resource_id: str
    action: str
    expected_state: str
    summary: str
    created_at: float
    expires_at: float

    def expired(self, *, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) >= self.expires_at

    def describe(self) -> dict[str, object]:
        """Customer/API-safe view: identity + semantics, no internals."""
        return {
            "proposal_id": self.proposal_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "expected_state": self.expected_state,
            "summary": self.summary,
            "expires_at": self.expires_at,
        }


class EphemeralProposalStore:
    """Session-bound store: never persisted, single-use, TTL-bounded."""

    def __init__(self, *, ttl_seconds: int = PROPOSAL_TTL_SECONDS) -> None:
        self._ttl = int(ttl_seconds)
        self._by_id: dict[str, EphemeralProposal] = {}

    def ttl_seconds(self) -> int:
        return self._ttl

    def put(
        self,
        *,
        actor_id: str,
        tenant_id: str,
        scope: str,
        resource_type: str,
        resource_id: str,
        action: str,
        expected_state: str,
        summary: str,
    ) -> EphemeralProposal:
        now = time.time()
        proposal = EphemeralProposal(
            # Unguessable server-side identity: the client can only echo it back.
            proposal_id=str(uuid.uuid4()),
            actor_id=str(actor_id),
            tenant_id=str(tenant_id),
            scope=str(scope),
            resource_type=str(resource_type),
            resource_id=str(resource_id),
            action=str(action),
            expected_state=str(expected_state),
            summary=str(summary),
            created_at=now,
            expires_at=now + self._ttl,
        )
        self._by_id[proposal.proposal_id] = proposal
        return proposal

    def get(self, *, proposal_id: str, actor_id: str, tenant_id: str) -> EphemeralProposal | None:
        proposal = self._by_id.get(str(proposal_id))
        if proposal is None:
            return None
        if proposal.expired():
            self._by_id.pop(proposal.proposal_id, None)
            return None
        # A proposal is only visible to the actor + tenant that created it.
        if proposal.actor_id != str(actor_id) or proposal.tenant_id != str(tenant_id):
            return None
        return proposal

    def consume(
        self, *, proposal_id: str, actor_id: str, tenant_id: str
    ) -> EphemeralProposal | None:
        """Return the proposal and remove it — a proposal can never be replayed."""
        proposal = self.get(proposal_id=proposal_id, actor_id=actor_id, tenant_id=tenant_id)
        if proposal is not None:
            self._by_id.pop(proposal.proposal_id, None)
        return proposal

    def clear(self) -> None:
        self._by_id.clear()


#: Process-local store (non-persistent by construction).
proposal_store = EphemeralProposalStore()

__all__ = [
    "EphemeralProposal",
    "EphemeralProposalStore",
    "PROPOSAL_TTL_SECONDS",
    "proposal_store",
]
