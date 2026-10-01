"""Runtime context resolver (P17 WAVE 2 · D05/D06/D07/D08).

Fixed order: actor → tenant membership → (optional) space membership → role
context. It never guesses a tenant, never falls back, never caches, and its
output is context — **not** an authorization decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .errors import ErrorCode, IdentityRuntimeError
from .repository import ACTIVE, MembershipRepository, SpaceRepository, TenantRepository


@dataclass(frozen=True)
class ResolvedContext:
    """Identity/context facts only. Deliberately carries no ALLOW/deny verdict."""

    actor_id: str
    actor_type: str
    tenant_id: str
    space_id: str | None
    tenant_role_id: str
    space_role_id: str | None = None


class RuntimeContextResolver:
    def __init__(
        self,
        *,
        tenants: TenantRepository | None = None,
        spaces: SpaceRepository | None = None,
        memberships: MembershipRepository | None = None,
    ) -> None:
        self._tenants = tenants or TenantRepository()
        self._spaces = spaces or SpaceRepository()
        self._memberships = memberships or MembershipRepository()

    def resolve(
        self,
        session: Session,
        *,
        actor_id: str,
        actor_type: str = "USER",
        tenant_id: str,
        space_id: str | None = None,
    ) -> ResolvedContext:
        """Resolve context or raise a denial. No implicit tenant, no fallback."""
        membership = self._memberships.get_tenant_membership(
            session, tenant_id=tenant_id, user_id=actor_id
        )
        if membership is None or str(membership.get("status")) != ACTIVE:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_REQUIRED, "tenant membership required")
        tenant_row = self._tenants.get_member_tenant(session, tenant_id=tenant_id, actor_id=actor_id)
        if tenant_row is None:
            raise IdentityRuntimeError(ErrorCode.TENANT_SCOPE_DENIED, "tenant not accessible")

        space_role_id: str | None = None
        if space_id is not None:
            if not self._spaces.space_belongs_to_tenant(
                session, tenant_id=tenant_id, space_id=space_id
            ):
                raise IdentityRuntimeError(ErrorCode.SPACE_SCOPE_DENIED, "space is not in this tenant")
            space_row = self._spaces.get_member_space(
                session, tenant_id=tenant_id, space_id=space_id, actor_id=actor_id
            )
            if space_row is None:
                # visibility / tenant membership never substitute for space membership.
                raise IdentityRuntimeError(ErrorCode.SPACE_SCOPE_DENIED, "space membership required")
            space_membership = self._memberships.get_space_membership(
                session, tenant_id=tenant_id, space_id=space_id, user_id=actor_id
            )
            space_role_id = str(space_membership["role_id"]) if space_membership else None

        return ResolvedContext(
            actor_id=actor_id,
            actor_type=actor_type,
            tenant_id=str(membership["tenant_id"]),
            space_id=space_id,
            tenant_role_id=str(membership["role_id"]),
            space_role_id=space_role_id,
        )
