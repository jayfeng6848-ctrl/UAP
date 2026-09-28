"""Tenant / space resolution and context assembly (Wave 2 §二十三 – §二十五).

Authentication success is **not** tenant or space authorization. The rules are
frozen:

* exactly one active candidate  -> the service may resolve it deterministically;
* several candidates            -> the request must name the context
                                  (``context_required``), never a random pick;
* no active membership          -> ``context_denied`` (fail closed);
* handlers never choose a tenant or space.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.database.persistence import Repository
from infrastructure.runtime.errors import PersistenceError
from services.session.service import SessionService, SessionView

from .errors import ContextDenied, ContextRequired, ContextUnavailable
from .model import AuthenticatedRuntimeContext, AuthenticationAssurance


class MembershipReader(Repository):
    """Read-only membership lookups (tenants / spaces are SELECT-only)."""

    def active_tenant_ids(self, user_id: str) -> list[str]:
        return self._distinct(
            "SELECT DISTINCT tenant_id FROM public.tenant_memberships"
            " WHERE user_id = :uid AND status = 'active'"
            " UNION SELECT DISTINCT tenant_id FROM public.memberships"
            " WHERE user_id = :uid AND status = 'active'",
            user_id,
        )

    def has_active_tenant(self, user_id: str, tenant_id: str) -> bool:
        return tenant_id in self.active_tenant_ids(user_id)

    def active_space_ids(self, user_id: str, tenant_id: str) -> list[str]:
        return self._distinct(
            "SELECT DISTINCT space_id FROM public.memberships"
            " WHERE user_id = :uid AND tenant_id = :tid AND status = 'active'"
            " AND space_id IS NOT NULL",
            user_id,
            tenant_id,
        )

    def has_active_space(self, user_id: str, tenant_id: str, space_id: str) -> bool:
        return space_id in self.active_space_ids(user_id, tenant_id)

    def _distinct(self, sql: str, *args: str) -> list[str]:
        params = {"uid": args[0]}
        if len(args) > 1:
            params["tid"] = args[1]
        try:
            rows = self.session.execute(text(sql), params).all()
        except SQLAlchemyError as exc:
            raise PersistenceError(str(exc).splitlines()[0][:200]) from exc
        return [str(row[0]) for row in rows]


@dataclass(frozen=True)
class ResolvedScope:
    tenant_id: str | None
    space_id: str | None


class ContextBuilder:
    """Assemble a :class:`AuthenticatedRuntimeContext` from a live session."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._sessions = SessionService(session)
        self._memberships = MembershipReader(session)

    # ------------------------------------------------------------------ scope
    def resolve_scope(
        self,
        *,
        user_id: str,
        requested_tenant_id: str | None = None,
        requested_space_id: str | None = None,
    ) -> ResolvedScope:
        tenant_id: str | None = None
        if requested_tenant_id:
            if not self._memberships.has_active_tenant(user_id, requested_tenant_id):
                raise ContextDenied("no active tenant membership")
            tenant_id = requested_tenant_id
        else:
            candidates = self._memberships.active_tenant_ids(user_id)
            if not candidates:
                raise ContextDenied("no active tenant membership")
            if len(candidates) > 1:
                # Never pick one silently: the request must say which.
                raise ContextRequired("tenant context is required")
            tenant_id = candidates[0]

        space_id: str | None = None
        if requested_space_id:
            if not self._memberships.has_active_space(user_id, tenant_id, requested_space_id):
                raise ContextDenied("no active space membership")
            space_id = requested_space_id
        else:
            spaces = self._memberships.active_space_ids(user_id, tenant_id)
            if len(spaces) == 1:
                space_id = spaces[0]
            elif len(spaces) > 1:
                raise ContextRequired("space context is required")
            else:
                # A tenant-level request legitimately has no space.
                space_id = None

        return ResolvedScope(tenant_id=tenant_id, space_id=space_id)

    # ---------------------------------------------------------------- context
    def build(
        self,
        *,
        session_id: str,
        requested_tenant_id: str | None = None,
        requested_space_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> AuthenticatedRuntimeContext:
        """Validate the session, resolve scope and freeze the context."""
        try:
            view: SessionView = self._sessions.validate_session_id(session_id)
            scope = self.resolve_scope(
                user_id=view.user_id,
                requested_tenant_id=requested_tenant_id,
                requested_space_id=requested_space_id,
            )
        except (ContextDenied, ContextRequired):
            raise
        except Exception as exc:  # noqa: BLE001 - fail closed on any failure
            raise ContextUnavailable("context assembly failed") from exc

        assurance = (
            AuthenticationAssurance.SESSION_VERIFIED
            if view.device_id is not None
            else AuthenticationAssurance.IDENTITY_VERIFIED
        )
        return AuthenticatedRuntimeContext(
            user_id=view.user_id,
            identity_id=view.identity_id,
            session_id=view.session_id,
            device_id=view.device_id,
            tenant_id=scope.tenant_id,
            space_id=scope.space_id,
            scope="SPACE" if scope.space_id else ("TENANT" if scope.tenant_id else "PLATFORM"),
            authentication_assurance=assurance,
            correlation_id=correlation_id,
            request_id=request_id,
        )


__all__ = ["ContextBuilder", "MembershipReader", "ResolvedScope"]
