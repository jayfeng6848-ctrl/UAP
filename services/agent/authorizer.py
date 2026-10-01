"""Actor authorization adapter (P16-D05).

The runtime never decides authorization itself: it delegates to the frozen P09
authorization service. This adapter is the only place where the runtime touches
that service, and it fails closed on every error.
"""

from __future__ import annotations

from typing import Any

from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from services.authorization import AuthorizationService


class P09ActorAuthorizer:
    """Actor-side check: may this actor execute this agent?"""

    def __init__(self, service: AuthorizationService) -> None:
        self._service = service

    @classmethod
    def from_engine(cls, engine: Any) -> "P09ActorAuthorizer":
        return cls(AuthorizationService(engine=engine))

    def authorize_actor(
        self,
        *,
        actor_type: str,
        actor_id: str,
        tenant_id: str,
        space_id: str | None,
        agent_id: str,
    ) -> bool:
        request = AuthorizationRequest(
            subject=Subject(
                identity_id=actor_id,
                subject_type=actor_type,
                tenant_id=tenant_id,
                actor_id=actor_id,
            ),
            action=Action(name="execute", resource_type="agent"),
            resource=ResourceRef(
                type="agent",
                id=agent_id,
                tenant_id=tenant_id or "",
                space_id=space_id,
            ),
            tenant_id=tenant_id,
            space_id=space_id,
        )
        try:
            decision = self._service.authorize(request)
        except Exception:  # noqa: BLE001 - any failure is a denial
            return False
        return bool(decision.allowed)
