"""P17 use cases (transaction owners) — tenant/space read + membership read/write.

Each function owns exactly one ``RuntimeDatabase.transaction()`` (Wave 1 rule:
the use case owns the boundary, repositories never commit, handlers never open a
transaction) and runs the frozen order:

    resolve P17 context  →  canonical authorization  →  membership mutation  →  audit

The authorization step delegates to ``MembershipAuthorizer`` (the single bridge
into the existing canonical engine). Nothing here compares a role name, checks
``is_admin`` or falls back to a platform role: an unauthorized request performs
**zero** writes and produces no audit row that would imply success.

Tenant / space **read** is membership-resolved: an actor sees exactly the
tenants it belongs to and exactly the spaces it is a member of (the P17 WAVE 2
rules). Structural writes (tenant/space create/update/delete) do not exist here
at all — they belong to the control plane.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from infrastructure.database.runtime import RuntimeDatabase
from services.session import SessionService
from services.identity_runtime import (
    ErrorCode,
    IdentityRuntimeError,
    MembershipAuthorizer,
    MembershipRepository,
    MembershipRuntime,
    RuntimeContextResolver,
    SpaceRepository,
    TenantRepository,
)


@dataclass(frozen=True)
class RuntimeActor:
    """The authenticated actor, before any tenant/space context is attached."""

    user_id: str
    identity_id: str
    session_id: str
    device_id: str | None = None
    subject_type: str = "USER"


def authenticate_actor(db: RuntimeDatabase, *, token: str) -> RuntimeActor:
    """Validate the bearer session and return the actor (P17-D09: reuse, no new auth).

    The tenant/space are **not** resolved here: the target scope comes from the
    request path, and P17's context rules are applied per operation. That keeps
    explicit platform authority reachable without inventing a header or a
    default tenant, while the session itself is still the frozen Wave 2 path.
    """
    with db.transaction() as session:
        view = SessionService(session).validate(token=token)
        return RuntimeActor(
            user_id=view.user_id,
            identity_id=view.identity_id,
            session_id=view.session_id,
            device_id=view.device_id,
        )


def _correlation_id(value: str | None) -> str:
    """Reuse the request correlation when present; never invent a second scheme."""
    return value or str(uuid.uuid4())


def _authorize_membership(
    db: RuntimeDatabase,
    session,
    *,
    actor_id: str,
    actor_type: str,
    operation: str,
    tenant_id: str,
    space_id: str | None = None,
) -> None:
    """The single membership gate: P17 context, then existing canonical authority.

    * a tenant/space membership context exists → the canonical decision is taken
      in that context (tenant- and space-scoped roles apply);
    * no membership context → only **explicit** authority may proceed, which P17
      asks by removing the tenant/space context from subject resolution. A plain
      member, a foreign actor and a space role without tenant standing all fail
      both questions, so this is a strict gate and never a fallback.

    Raises ``IdentityRuntimeError`` on every denial; nothing is written before it
    returns.
    """
    authorizer = MembershipAuthorizer.from_engine(db.engine)
    try:
        RuntimeContextResolver().resolve(
            session, actor_id=actor_id, actor_type=actor_type,
            tenant_id=tenant_id, space_id=space_id,
        )
    except IdentityRuntimeError as context_error:
        try:
            authorizer.authorize_without_membership(
                session, actor_id=actor_id, actor_type=actor_type, operation=operation,
                tenant_id=tenant_id, space_id=space_id,
            )
        except IdentityRuntimeError:
            # No membership context and no explicit authority: report the scope
            # failure the caller's own context produced (same 403 class).
            raise context_error from None
        return
    authorizer.authorize(
        session, actor_id=actor_id, actor_type=actor_type, operation=operation,
        tenant_id=tenant_id, space_id=space_id,
    )


# ------------------------------------------------------------------ structure
def list_tenants(db: RuntimeDatabase, *, actor_id: str, actor_type: str = "USER") -> list[dict[str, Any]]:
    """The tenants this actor belongs to (membership-scoped · never a guess)."""
    with db.transaction() as session:
        return TenantRepository().list_member_tenants(session, actor_id=actor_id)


def get_tenant(
    db: RuntimeDatabase, *, actor_id: str, tenant_id: str, actor_type: str = "USER"
) -> dict[str, Any]:
    with db.transaction() as session:
        RuntimeContextResolver().resolve(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id
        )
        row = TenantRepository().get_member_tenant(
            session, tenant_id=tenant_id, actor_id=actor_id
        )
        if row is None:  # pragma: no cover - the resolver already proved membership
            raise IdentityRuntimeError(ErrorCode.TENANT_SCOPE_DENIED, "tenant not accessible")
        return row


def list_spaces(
    db: RuntimeDatabase, *, actor_id: str, tenant_id: str, actor_type: str = "USER"
) -> list[dict[str, Any]]:
    """The spaces this actor is a member of inside ``tenant_id``."""
    with db.transaction() as session:
        RuntimeContextResolver().resolve(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id
        )
        return SpaceRepository().list_member_spaces(session, tenant_id=tenant_id, actor_id=actor_id)


def list_tenant_members(
    db: RuntimeDatabase, *, actor_id: str, tenant_id: str, actor_type: str = "USER"
) -> list[dict[str, Any]]:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="list", tenant_id=tenant_id,
        )
        return MembershipRepository().list_tenant_members(session, tenant_id=tenant_id)


def list_space_members(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    space_id: str,
    actor_type: str = "USER",
) -> list[dict[str, Any]]:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="list", tenant_id=tenant_id, space_id=space_id,
        )
        return MembershipRepository().list_space_members(
            session, tenant_id=tenant_id, space_id=space_id
        )


# --------------------------------------------------------- tenant membership
def create_tenant_membership(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    user_id: str,
    role_id: str,
    actor_type: str = "USER",
    correlation_id: str | None = None,
) -> str:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="create", tenant_id=tenant_id,
        )
        return MembershipRuntime().create_tenant_membership(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id,
            user_id=user_id, role_id=role_id, correlation_id=_correlation_id(correlation_id),
        )


def update_tenant_membership(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    user_id: str,
    role_id: str,
    actor_type: str = "USER",
    correlation_id: str | None = None,
) -> None:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="update", tenant_id=tenant_id,
        )
        MembershipRuntime().update_tenant_membership(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id,
            user_id=user_id, role_id=role_id, correlation_id=_correlation_id(correlation_id),
        )


def delete_tenant_membership(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    user_id: str,
    actor_type: str = "USER",
    correlation_id: str | None = None,
) -> None:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="delete", tenant_id=tenant_id,
        )
        MembershipRuntime().delete_tenant_membership(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id,
            user_id=user_id, correlation_id=_correlation_id(correlation_id),
        )


# ---------------------------------------------------------- space membership
def create_space_membership(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    space_id: str,
    user_id: str,
    role_id: str,
    actor_type: str = "USER",
    correlation_id: str | None = None,
) -> str:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="create", tenant_id=tenant_id, space_id=space_id,
        )
        return MembershipRuntime().create_space_membership(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id,
            space_id=space_id, user_id=user_id, role_id=role_id,
            correlation_id=_correlation_id(correlation_id),
        )


def update_space_membership(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    space_id: str,
    user_id: str,
    role_id: str,
    actor_type: str = "USER",
    correlation_id: str | None = None,
) -> None:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="update", tenant_id=tenant_id, space_id=space_id,
        )
        MembershipRuntime().update_space_membership(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id,
            space_id=space_id, user_id=user_id, role_id=role_id,
            correlation_id=_correlation_id(correlation_id),
        )


def delete_space_membership(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    space_id: str,
    user_id: str,
    actor_type: str = "USER",
    correlation_id: str | None = None,
) -> None:
    with db.transaction() as session:
        _authorize_membership(
            db, session, actor_id=actor_id, actor_type=actor_type,
            operation="delete", tenant_id=tenant_id, space_id=space_id,
        )
        MembershipRuntime().delete_space_membership(
            session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id,
            space_id=space_id, user_id=user_id, correlation_id=_correlation_id(correlation_id),
        )


__all__ = [
    "RuntimeActor",
    "authenticate_actor",
    "create_space_membership",
    "create_tenant_membership",
    "delete_space_membership",
    "delete_tenant_membership",
    "get_tenant",
    "list_space_members",
    "list_spaces",
    "list_tenant_members",
    "list_tenants",
    "update_space_membership",
    "update_tenant_membership",
]
