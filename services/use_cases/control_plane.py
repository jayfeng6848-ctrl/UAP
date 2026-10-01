"""P18 control-plane use cases (transaction owners).

One frozen operation = one logical transaction:

    authorize (canonical engine)  →  validate  →  structural writes  →  audit  →  COMMIT

The actor is always the authenticated platform actor (never the DB principal),
authorization always goes through the existing ``AuthorizationService`` (platform
scope + ``resource=None`` before the object exists, the canonical resource
afterwards), and every write happens inside the caller-owned transaction so a
failure leaves no half-provisioned tenant or space.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from core.audit.interfaces import new_event_id
from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from infrastructure.database.runtime import RuntimeDatabase
from services.authorization import AuthorizationRepository, AuthorizationService
from services.control_plane.errors import ControlPlaneError, ErrorCode
from services.control_plane.provisioning import ensure_resource_projection
from services.control_plane.repository import ACTIVE, ControlPlaneRepository

TENANT_ADMIN_KEY = "tenant_admin"
SPACE_ADMIN_KEY = "space_admin"
TENANT_ADMIN_PERMISSIONS = ("member.read", "member.admin", "tenant.admin")
SPACE_ADMIN_PERMISSIONS = ("space.admin", "member.read", "member.admin")

#: Frozen tenant transitions (P18-D02 / §30–§31). ``deleted`` is terminal.
TENANT_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("suspended", "archived"),
    "suspended": ("active", "archived"),
    "archived": ("active", "deleted"),
    "provisioning": (),
    "deleted": (),
}

#: Frozen space transitions (§33/§34). ``deleted`` is terminal.
SPACE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("archived",),
    "archived": ("active", "deleted"),
    "deleted": (),
}


@dataclass(frozen=True)
class ProvisionedTenant:
    tenant_id: str
    slug: str
    status: str
    admin_role_id: str
    membership_id: str
    replayed: bool = False


@dataclass(frozen=True)
class ProvisionedSpace:
    space_id: str
    tenant_id: str
    key: str
    status: str
    admin_role_id: str
    membership_id: str
    replayed: bool = False


def _correlation(value: str | None) -> str:
    return value or str(uuid.uuid4())


def _authorize(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    resource_type: str,
    resource_id: str | None = None,
    tenant_id: str | None = None,
    space_id: str | None = None,
) -> None:
    """Canonical authorization for one control-plane operation (P18-D06).

    Control-plane authority is **platform scope**: it is evaluated through the
    frozen ``resource is None`` entry point of the existing service, which only a
    PLATFORM-scope grant can satisfy. The resource-bearing path is deliberately
    not used here, because the canonical ACL layer reads ``resource_permissions``
    / ``acl_subject_types`` and those tables are on the absolutely-forbidden list
    for this principal (§49) — the frozen privilege ceiling and the frozen
    authority model are both preserved by evaluating on the platform scope.
    ``resource_id``/``tenant_id``/``space_id`` remain in the signature for the
    audit record and for the caller's own scope validation; they never widen the
    decision.
    """
    service = AuthorizationService(
        engine=db.engine, repository=AuthorizationRepository(db.engine)
    )
    request = AuthorizationRequest(
        subject=Subject(identity_id=actor_id, subject_type="USER", actor_id=actor_id),
        action=Action(name="admin", resource_type=resource_type),
        resource=None,
    )
    try:
        decision = service.authorize(request)
    except Exception as exc:  # noqa: BLE001 - fail closed, never leak the cause
        raise ControlPlaneError(ErrorCode.AUTHORIZATION_DENIED, "authorization unavailable") from exc
    if not getattr(decision, "allowed", False):
        raise ControlPlaneError(ErrorCode.AUTHORIZATION_DENIED, "authorization denied")


def _audit(
    session, *, action: str, actor_id: str, tenant_id: str | None, space_id: str | None,
    resource_type: str, resource_id: str | None, correlation_id: str, facts: dict[str, Any],
) -> None:
    """Append one control-plane audit fact (same transaction as the mutation)."""
    session.execute(
        text(
            "INSERT INTO audit_logs (id, occurred_at, tenant_id, space_id, actor_type, actor_id,"
            " action, resource_type, resource_id, result, risk_level, correlation_id, metadata,"
            " created_at) VALUES (CAST(:id AS uuid), now(), CAST(:tenant AS uuid),"
            " CAST(:space AS uuid), 'user', CAST(:actor AS uuid), :action, :rtype,"
            " CAST(:rid AS uuid), 'success', 'MEDIUM', CAST(:corr AS uuid),"
            " CAST(:meta AS jsonb), now())"
        ),
        {
            "id": new_event_id(),
            "tenant": tenant_id,
            "space": space_id,
            "actor": actor_id,
            "action": action,
            "rtype": resource_type,
            "rid": resource_id,
            "corr": correlation_id,
            "meta": json.dumps(facts),
        },
    )


def _require_platform_initialized(repo: ControlPlaneRepository, session) -> None:
    if repo.bootstrap_state(session) != "initialized":
        raise ControlPlaneError(ErrorCode.BOOTSTRAP_REQUIRED, "platform is not initialized")


def _require_active_user(repo: ControlPlaneRepository, session, *, user_id: str) -> None:
    if repo.user_status(session, user_id=user_id) != ACTIVE:
        raise ControlPlaneError(ErrorCode.INITIAL_ADMIN_INVALID, "initial admin is not an active user")


def _ensure_admin_role(repo, session, *, scope: str, tenant_id: str | None, space_id: str | None,
                       key: str, name: str, permissions: tuple[str, ...]) -> str:
    """Create (or exactly reuse) a non-system scoped administrator role."""
    existing = repo.find_role(session, scope=scope, tenant_id=tenant_id, space_id=space_id, key=key)
    if existing is not None:
        if str(existing["status"]) != ACTIVE or repo.role_permission_keys(
            session, role_id=str(existing["id"])
        ) != set(permissions):
            raise ControlPlaneError(ErrorCode.INITIAL_ROLE_FAILED, "existing role does not match")
        return str(existing["id"])
    role_id = repo.insert_role(
        session, scope=scope, tenant_id=tenant_id, space_id=space_id, key=key, name=name
    )
    repo.bind_permissions(session, role_id=role_id, keys=permissions)
    if repo.role_permission_keys(session, role_id=role_id) != set(permissions):
        raise ControlPlaneError(ErrorCode.INITIAL_ROLE_FAILED, "role permissions incomplete")
    return role_id


def _project(repo, session, *, tenant_id: str, space_id: str | None) -> dict[str, str]:
    try:
        return ensure_resource_projection(session, tenant_id=tenant_id, space_id=space_id)
    except Exception as exc:  # noqa: BLE001 - projection failure aborts provisioning
        raise ControlPlaneError(ErrorCode.RESOURCE_PROJECTION_FAILED, "resource projection failed") from exc


# ------------------------------------------------------------------- provisioning
def provision_tenant(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    slug: str,
    display_name: str,
    initial_admin_user_id: str,
    correlation_id: str | None = None,
) -> ProvisionedTenant:
    """Create a tenant, its admin role, projections and first membership atomically."""
    correlation = _correlation(correlation_id)
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        _authorize(db, actor_id=actor_id, resource_type="tenant")
        _require_platform_initialized(repo, session)
        _require_active_user(repo, session, user_id=initial_admin_user_id)

        existing = repo.tenant_by_slug(session, slug=slug)
        if existing is not None:
            if str(existing["display_name"]) != display_name or str(existing["status"]) != ACTIVE:
                raise ControlPlaneError(ErrorCode.TENANT_CONFLICT, "slug already used")
            membership = repo.tenant_membership(
                session, tenant_id=str(existing["id"]), user_id=initial_admin_user_id
            )
            if membership is None:
                raise ControlPlaneError(ErrorCode.TENANT_CONFLICT, "existing tenant differs")
            return ProvisionedTenant(
                tenant_id=str(existing["id"]), slug=slug, status=ACTIVE,
                admin_role_id=str(membership["role_id"]), membership_id=str(membership["id"]),
                replayed=True,
            )

        tenant_id = repo.insert_tenant(session, slug=slug, display_name=display_name)
        role_id = _ensure_admin_role(
            repo, session, scope="TENANT", tenant_id=tenant_id, space_id=None,
            key=TENANT_ADMIN_KEY, name="Tenant Administrator", permissions=TENANT_ADMIN_PERMISSIONS,
        )
        _project(repo, session, tenant_id=tenant_id, space_id=None)
        membership_id = repo.insert_tenant_membership(
            session, tenant_id=tenant_id, user_id=initial_admin_user_id, role_id=role_id
        )
        _audit(
            session, action="tenant.provision", actor_id=actor_id, tenant_id=tenant_id,
            space_id=None, resource_type="tenant", resource_id=None, correlation_id=correlation,
            facts={"operation": "tenant.provision", "initial_admin_user_id": initial_admin_user_id,
                   "admin_role_id": role_id, "membership_id": membership_id},
        )
        if repo.set_tenant_status(session, tenant_id=tenant_id, status=ACTIVE, expect="provisioning") != 1:
            raise ControlPlaneError(ErrorCode.LIFECYCLE_CONFLICT, "tenant activation failed")
        return ProvisionedTenant(
            tenant_id=tenant_id, slug=slug, status=ACTIVE, admin_role_id=role_id,
            membership_id=membership_id,
        )


def provision_space(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    key: str,
    name: str,
    initial_space_admin_user_id: str,
    kind: str = "team",
    visibility: str = "tenant",
    owner_id: str | None = None,
    correlation_id: str | None = None,
) -> ProvisionedSpace:
    """Create a space, its admin role, projections and first membership atomically."""
    correlation = _correlation(correlation_id)
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        _authorize(db, actor_id=actor_id, resource_type="space")
        tenant = repo.tenant(session, tenant_id=tenant_id)
        if tenant is None:
            raise ControlPlaneError(ErrorCode.TENANT_NOT_FOUND, "tenant not found")
        if str(tenant["status"]) != ACTIVE:
            raise ControlPlaneError(ErrorCode.TENANT_NOT_ACTIVE, "tenant is not active")
        _require_active_user(repo, session, user_id=initial_space_admin_user_id)
        membership = repo.tenant_membership(
            session, tenant_id=tenant_id, user_id=initial_space_admin_user_id
        )
        if membership is None or str(membership["status"]) != ACTIVE:
            raise ControlPlaneError(
                ErrorCode.INITIAL_ADMIN_INVALID, "initial space admin must already belong to the tenant"
            )

        existing = repo.space_by_key(session, tenant_id=tenant_id, key=key)
        if existing is not None:
            if str(existing["name"]) != name or str(existing["status"]) != ACTIVE:
                raise ControlPlaneError(ErrorCode.SPACE_CONFLICT, "space key already used")
            existing_membership = repo.space_membership(
                session, tenant_id=tenant_id, space_id=str(existing["id"]),
                user_id=initial_space_admin_user_id,
            )
            if existing_membership is None:
                raise ControlPlaneError(ErrorCode.SPACE_CONFLICT, "existing space differs")
            return ProvisionedSpace(
                space_id=str(existing["id"]), tenant_id=tenant_id, key=key, status=ACTIVE,
                admin_role_id=str(existing_membership["role_id"]),
                membership_id=str(existing_membership["id"]), replayed=True,
            )

        space_id = repo.insert_space(
            session, tenant_id=tenant_id, key=key, name=name, kind=kind,
            visibility=visibility, status=ACTIVE, owner_id=owner_id,
        )
        role_id = _ensure_admin_role(
            repo, session, scope="SPACE", tenant_id=None, space_id=space_id,
            key=SPACE_ADMIN_KEY, name="Space Administrator", permissions=SPACE_ADMIN_PERMISSIONS,
        )
        _project(repo, session, tenant_id=tenant_id, space_id=space_id)
        space_membership_id = repo.insert_space_membership(
            session, tenant_id=tenant_id, space_id=space_id,
            user_id=initial_space_admin_user_id, role_id=role_id,
        )
        _audit(
            session, action="space.provision", actor_id=actor_id, tenant_id=tenant_id,
            space_id=space_id, resource_type="space", resource_id=space_id,
            correlation_id=correlation,
            facts={"operation": "space.provision",
                   "initial_admin_user_id": initial_space_admin_user_id,
                   "admin_role_id": role_id, "membership_id": space_membership_id},
        )
        return ProvisionedSpace(
            space_id=space_id, tenant_id=tenant_id, key=key, status=ACTIVE,
            admin_role_id=role_id, membership_id=space_membership_id,
        )


# ---------------------------------------------------------------------- lifecycle
def transition_tenant(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    target_state: str,
    correlation_id: str | None = None,
) -> str:
    """Frozen tenant lifecycle transition (``deleted`` is terminal, no DELETE)."""
    correlation = _correlation(correlation_id)
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        tenant = repo.tenant(session, tenant_id=tenant_id)
        if tenant is None:
            raise ControlPlaneError(ErrorCode.TENANT_NOT_FOUND, "tenant not found")
        resource = repo_resource_id(session, tenant_id=tenant_id, resource_type="tenant")
        _authorize(
            db, actor_id=actor_id, resource_type="tenant",
            resource_id=resource, tenant_id=tenant_id,
        )
        current = str(tenant["status"])
        if target_state not in TENANT_TRANSITIONS.get(current, ()):
            raise ControlPlaneError(
                ErrorCode.LIFECYCLE_CONFLICT, f"transition {current} -> {target_state} is not allowed"
            )
        if repo.set_tenant_status(
            session, tenant_id=tenant_id, status=target_state, expect=current
        ) != 1:
            raise ControlPlaneError(ErrorCode.LIFECYCLE_CONFLICT, "state changed concurrently")
        _audit(
            session, action=f"tenant.{target_state}", actor_id=actor_id, tenant_id=tenant_id,
            space_id=None, resource_type="tenant", resource_id=resource,
            correlation_id=correlation,
            facts={"operation": f"tenant.{target_state}", "from": current, "to": target_state},
        )
        return target_state


def transition_space(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    space_id: str,
    target_state: str,
    correlation_id: str | None = None,
) -> str:
    correlation = _correlation(correlation_id)
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        space = repo.space(session, tenant_id=tenant_id, space_id=space_id)
        if space is None:
            raise ControlPlaneError(ErrorCode.SPACE_NOT_FOUND, "space not found")
        resource = repo_resource_id(
            session, tenant_id=tenant_id, resource_type="space", space_id=space_id
        )
        _authorize(
            db, actor_id=actor_id, resource_type="space", resource_id=resource,
            tenant_id=tenant_id, space_id=space_id,
        )
        current = str(space["status"])
        if target_state not in SPACE_TRANSITIONS.get(current, ()):
            raise ControlPlaneError(
                ErrorCode.LIFECYCLE_CONFLICT, f"transition {current} -> {target_state} is not allowed"
            )
        if repo.set_space_status(
            session, tenant_id=tenant_id, space_id=space_id, status=target_state, expect=current
        ) != 1:
            raise ControlPlaneError(ErrorCode.LIFECYCLE_CONFLICT, "state changed concurrently")
        _audit(
            session, action=f"space.{target_state}", actor_id=actor_id, tenant_id=tenant_id,
            space_id=space_id, resource_type="space", resource_id=resource,
            correlation_id=correlation,
            facts={"operation": f"space.{target_state}", "from": current, "to": target_state},
        )
        return target_state


def repo_resource_id(
    session, *, tenant_id: str, resource_type: str, space_id: str | None = None
) -> str | None:
    """The canonical resource row of an existing object (None when unprojected)."""
    row = session.execute(
        text(
            "SELECT id FROM resources WHERE tenant_id = CAST(:t AS uuid)"
            " AND space_id IS NOT DISTINCT FROM CAST(:s AS uuid) AND resource_type = :rtype"
            " AND deleted_at IS NULL"
        ),
        {"t": tenant_id, "s": space_id, "rtype": resource_type},
    ).first()
    return str(row[0]) if row is not None else None


# ---------------------------------------------------------------- metadata updates
VISIBILITY_VALUES = ("private", "tenant", "link")


def read_tenant(db: RuntimeDatabase, *, actor_id: str, tenant_id: str) -> dict[str, Any]:
    """Platform-admin read of one tenant (authorization precedes disclosure)."""
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        tenant = repo.tenant(session, tenant_id=tenant_id)
        if tenant is None:
            raise ControlPlaneError(ErrorCode.TENANT_NOT_FOUND, "tenant not found")
        _authorize(
            db, actor_id=actor_id, resource_type="tenant",
            resource_id=repo_resource_id(session, tenant_id=tenant_id, resource_type="tenant"),
            tenant_id=tenant_id,
        )
        return {k: (str(v) if v is not None else None) for k, v in tenant.items()}


def read_space(
    db: RuntimeDatabase, *, actor_id: str, tenant_id: str, space_id: str
) -> dict[str, Any]:
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        space = repo.space(session, tenant_id=tenant_id, space_id=space_id)
        if space is None:
            raise ControlPlaneError(ErrorCode.SPACE_NOT_FOUND, "space not found")
        _authorize(
            db, actor_id=actor_id, resource_type="space",
            resource_id=repo_resource_id(
                session, tenant_id=tenant_id, resource_type="space", space_id=space_id
            ),
            tenant_id=tenant_id, space_id=space_id,
        )
        return {
            key: (str(value) if value is not None else None) for key, value in space.items()
        }


def update_tenant_metadata(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    display_name: str | None = None,
    plan: str | None = None,
    region: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Metadata-only tenant update (never creates membership, role or ACL)."""
    correlation = _correlation(correlation_id)
    repo = ControlPlaneRepository()
    with db.transaction() as session:
        tenant = repo.tenant(session, tenant_id=tenant_id)
        if tenant is None:
            raise ControlPlaneError(ErrorCode.TENANT_NOT_FOUND, "tenant not found")
        resource = repo_resource_id(session, tenant_id=tenant_id, resource_type="tenant")
        _authorize(
            db, actor_id=actor_id, resource_type="tenant", resource_id=resource,
            tenant_id=tenant_id,
        )
        changed = [f for f, v in (("display_name", display_name), ("plan", plan),
                                  ("region", region)) if v is not None]
        if not changed:
            raise ControlPlaneError(ErrorCode.INVALID_INPUT, "no updatable field supplied")
        if repo.update_tenant_metadata(
            session, tenant_id=tenant_id, display_name=display_name, plan=plan, region=region
        ) != 1:
            raise ControlPlaneError(ErrorCode.LIFECYCLE_CONFLICT, "tenant update matched no row")
        _audit(
            session, action="tenant.metadata.update", actor_id=actor_id, tenant_id=tenant_id,
            space_id=None, resource_type="tenant", resource_id=resource,
            correlation_id=correlation,
            facts={"operation": "tenant.metadata.update", "fields": changed},
        )


def update_space_metadata(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    space_id: str,
    name: str | None = None,
    visibility: str | None = None,
    owner_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Metadata/visibility update for a space (never membership, role or ACL)."""
    correlation = _correlation(correlation_id)
    repo = ControlPlaneRepository()
    if visibility is not None and visibility not in VISIBILITY_VALUES:
        raise ControlPlaneError(ErrorCode.INVALID_INPUT, "unknown visibility value")
    with db.transaction() as session:
        space = repo.space(session, tenant_id=tenant_id, space_id=space_id)
        if space is None:
            raise ControlPlaneError(ErrorCode.SPACE_NOT_FOUND, "space not found")
        resource = repo_resource_id(
            session, tenant_id=tenant_id, resource_type="space", space_id=space_id
        )
        _authorize(
            db, actor_id=actor_id, resource_type="space", resource_id=resource,
            tenant_id=tenant_id, space_id=space_id,
        )
        changed = [f for f, v in (("name", name), ("visibility", visibility),
                                  ("owner_id", owner_id)) if v is not None]
        if not changed:
            raise ControlPlaneError(ErrorCode.INVALID_INPUT, "no updatable field supplied")
        if repo.update_space_metadata(
            session, tenant_id=tenant_id, space_id=space_id, name=name,
            visibility=visibility, owner_id=owner_id,
        ) != 1:
            raise ControlPlaneError(ErrorCode.LIFECYCLE_CONFLICT, "space update matched no row")
        _audit(
            session, action="space.metadata.update", actor_id=actor_id, tenant_id=tenant_id,
            space_id=space_id, resource_type="space", resource_id=resource,
            correlation_id=correlation,
            facts={"operation": "space.metadata.update", "fields": changed},
        )


__all__ = [
    "SPACE_ADMIN_KEY",
    "SPACE_ADMIN_PERMISSIONS",
    "SPACE_TRANSITIONS",
    "TENANT_ADMIN_KEY",
    "TENANT_ADMIN_PERMISSIONS",
    "TENANT_TRANSITIONS",
    "ProvisionedSpace",
    "ProvisionedTenant",
    "provision_space",
    "provision_tenant",
    "read_space",
    "read_tenant",
    "repo_resource_id",
    "update_space_metadata",
    "update_tenant_metadata",
    "transition_space",
    "transition_tenant",
]
