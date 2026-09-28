"""Thin adapter: authenticated context -> **existing** Stage 2 authorization.

Wave 2 forbids a second authorization engine, a second role evaluator, a second
ABAC engine or a second permission vocabulary (§二十六 / §二十七). This module
contains no decision logic of its own: it only shapes the frozen
``core.permission`` inputs and delegates to ``services.authorization``.

Integration fact (verified while reading Stage 2): ``SubjectResolver`` resolves a
``USER`` subject through ``users.id`` — it calls
``AuthorizationRepository.get_user(subject.identity_id)``. A normal human subject
must therefore carry the **user id** in ``Subject.identity_id``. That is exactly
the VOC-W2-01 decision (persistence anchor = ``users.id``), and it is asserted
here in one place rather than guessed at each call site.

Fail-closed: any unexpected failure becomes ``DENY`` (§二十八 / §三十四).
"""

from __future__ import annotations

from core.permission import Action, AuthorizationRequest, Decision, Subject
from core.resource import ResourceRef
from sqlalchemy import Engine

from services.authorization import AuthorizationService

from .model import AuthenticatedRuntimeContext

DENY_UNKNOWN = Decision(effect="DENY", reason="authorization-unavailable")


class AuthorizationAdapter:
    """The only Wave 2 bridge into Stage 2 authorization."""

    def __init__(self, engine: Engine | None = None) -> None:
        self._service = AuthorizationService(engine=engine)

    # ------------------------------------------------------------------ subject
    @staticmethod
    def subject_for(context: AuthenticatedRuntimeContext) -> Subject:
        """Identity/device/session are *evidence*; the subject is the user (§二十七)."""
        return Subject(
            identity_id=context.user_id,  # Stage 2 resolves USER subjects by users.id
            subject_type="USER",
            tenant_id=context.tenant_id,
            actor_id=context.user_id,
        )

    # ---------------------------------------------------------------- authorize
    def authorize(
        self,
        context: AuthenticatedRuntimeContext,
        *,
        action: str,
        resource: ResourceRef,
        risk_level: str | None = None,
    ) -> Decision:
        """Delegate to Stage 2. Never raises; every failure denies."""
        try:
            request = AuthorizationRequest(
                subject=self.subject_for(context),
                action=Action(name=action),
                resource=resource,
                tenant_id=context.tenant_id,
                space_id=context.space_id,
                request_id=context.request_id,
                risk_level=risk_level,
            )
            return self._service.authorize(request)
        except Exception:  # noqa: BLE001 - authorization exception => DENY
            return DENY_UNKNOWN

    def is_allowed(
        self,
        context: AuthenticatedRuntimeContext,
        *,
        action: str,
        resource: ResourceRef,
        risk_level: str | None = None,
    ) -> bool:
        return self.authorize(
            context, action=action, resource=resource, risk_level=risk_level
        ).allowed


__all__ = ["DENY_UNKNOWN", "AuthorizationAdapter"]
