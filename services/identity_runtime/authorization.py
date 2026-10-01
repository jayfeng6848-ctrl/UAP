"""P17 WAVE 3 — the single bridge from runtime context to canonical authorization.

This module owns **no** authorization algorithm: no permission lookup, no role
name comparison, no scope math, no fallback. It performs exactly three things:

1. map a membership operation onto the frozen action vocabulary
   (``read``/``list`` → ``member.read``; ``create``/``update``/``delete`` →
   ``member.admin`` — P17-AUTH-Q2, no permission taxonomy extension);
2. resolve the canonical membership-collection resource for the target scope
   (P17-AUTH-Q1: provisioning owns it, missing means deny — never self-create);
3. delegate the decision to the existing ``AuthorizationService``.

Resource type is ``member`` because the canonical RBAC layer only matches a
permission whose ``resource_type`` equals the resource's type, and P13 seeded
``member.read`` / ``member.admin``. Nothing here is invented.
"""

from __future__ import annotations

import re
from typing import Any

from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from services.authorization import AuthorizationRepository, AuthorizationService

from .errors import ErrorCode, IdentityRuntimeError
from .repository import MEMBER_RESOURCE_TYPE, MembershipResourceRepository

#: Membership operations that map onto the read half of the frozen vocabulary.
READ_OPERATIONS = ("read", "list")
#: Membership operations that map onto the administrative half.
ADMIN_OPERATIONS = ("create", "update", "delete")

_SAFE_REASON = re.compile(r"[a-z][a-z0-9_-]{0,39}")


def safe_reason_code(reason: str) -> str:
    """Reduce a canonical denial reason to a machine-readable code.

    The canonical engine may embed rule keys in its reason (never SQL, but keys
    are still internal); only the leading machine token is kept so a response
    can never carry rule text, a policy name or an infrastructure message.
    """
    layer = str(reason).split(":", 1)[0].strip()
    return layer.upper().replace("-", "_") if _SAFE_REASON.fullmatch(layer) else "DENIED"


class MembershipAuthorizer:
    """Ask the canonical engine whether an actor may manage members here."""

    def __init__(
        self,
        engine: Engine | None = None,
        *,
        service: Any | None = None,
        repository: AuthorizationRepository | None = None,
        resources: MembershipResourceRepository | None = None,
    ) -> None:
        self._service = service or AuthorizationService(
            engine=engine, repository=repository or AuthorizationRepository(engine)
        )
        self._resources = resources or MembershipResourceRepository()

    @classmethod
    def from_engine(cls, engine: Any) -> "MembershipAuthorizer":
        return cls(engine=engine)

    # ------------------------------------------------------------------ inputs
    @staticmethod
    def action_for(operation: str) -> str:
        """The canonical action name for a membership operation (frozen map)."""
        if operation in READ_OPERATIONS:
            return "read"
        if operation in ADMIN_OPERATIONS:
            return "admin"
        raise IdentityRuntimeError(ErrorCode.AUTHORIZATION_DENIED, "unsupported operation")

    def collection_resource(
        self, session: Session, *, tenant_id: str, space_id: str | None
    ) -> dict[str, Any]:
        """Resolve the canonical collection, or fail closed (never self-provision)."""
        row = (
            self._resources.space_collection(session, tenant_id=tenant_id, space_id=space_id)
            if space_id is not None
            else self._resources.tenant_collection(session, tenant_id=tenant_id)
        )
        if row is None:
            raise IdentityRuntimeError(
                ErrorCode.RESOURCE_NOT_PROVISIONED, "canonical resource is not provisioned"
            )
        return row

    # ----------------------------------------------------------------- decision
    def _ask(
        self,
        session: Session,
        *,
        actor_id: str,
        actor_type: str,
        operation: str,
        tenant_id: str | None,
        resource_tenant_id: str,
        space_id: str | None,
    ) -> Any:
        """Ask the canonical engine one question about the collection resource."""
        collection = self.collection_resource(
            session, tenant_id=resource_tenant_id, space_id=space_id
        )
        return self._service.authorize(
            AuthorizationRequest(
                subject=Subject(
                    identity_id=actor_id,
                    subject_type=actor_type,
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                ),
                action=Action(name=self.action_for(operation), resource_type=MEMBER_RESOURCE_TYPE),
                resource=ResourceRef(
                    type=MEMBER_RESOURCE_TYPE,
                    id=str(collection["id"]),
                    tenant_id=resource_tenant_id,
                    space_id=space_id,
                ),
                tenant_id=tenant_id,
                space_id=space_id,
            )
        )

    def decide(
        self,
        session: Session,
        *,
        actor_id: str,
        actor_type: str = "USER",
        operation: str,
        tenant_id: str,
        space_id: str | None = None,
    ) -> Any:
        """The canonical decision for this actor in this tenant/space context."""
        return self._ask(
            session,
            actor_id=actor_id,
            actor_type=actor_type,
            operation=operation,
            tenant_id=tenant_id,
            resource_tenant_id=tenant_id,
            space_id=space_id,
        )

    def authorize(
        self,
        session: Session,
        *,
        actor_id: str,
        actor_type: str = "USER",
        operation: str,
        tenant_id: str,
        space_id: str | None = None,
    ) -> Any:
        """Return the canonical ``Decision``; raise a stable P17 denial otherwise."""
        decision = self.decide(
            session, actor_id=actor_id, actor_type=actor_type, operation=operation,
            tenant_id=tenant_id, space_id=space_id,
        )
        if not getattr(decision, "allowed", False):
            raise self._denied(decision)
        return decision

    def authorize_without_membership(
        self,
        session: Session,
        *,
        actor_id: str,
        actor_type: str = "USER",
        operation: str,
        tenant_id: str,
        space_id: str | None = None,
    ) -> Any:
        """Canonical decision with the tenant/space **context removed**.

        Only explicit authority survives this question: subject resolution then
        sees exactly the platform-scope roles (plus any ACL provisioned on the
        collection resource). A tenant- or space-scoped role contributes nothing,
        so this is how P17 asks "may this actor act here without any membership
        context?". It is not a fallback — the answer still comes from the same
        canonical engine, and a plain member always answers DENY.
        """
        decision = self._ask(
            session,
            actor_id=actor_id,
            actor_type=actor_type,
            operation=operation,
            tenant_id=None,
            resource_tenant_id=tenant_id,
            space_id=space_id,
        )
        if not getattr(decision, "allowed", False):
            raise self._denied(decision)
        return decision

    @staticmethod
    def _denied(decision: Any) -> IdentityRuntimeError:
        error = IdentityRuntimeError(ErrorCode.AUTHORIZATION_DENIED, "authorization denied")
        error.decision_reason = safe_reason_code(  # type: ignore[attr-defined]
            getattr(decision, "reason", "")
        )
        return error


__all__ = [
    "ADMIN_OPERATIONS",
    "READ_OPERATIONS",
    "MembershipAuthorizer",
    "safe_reason_code",
]
