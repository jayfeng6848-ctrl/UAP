"""Canonical resource projection for tenant / space provisioning (P17-AUTH-Q1).

Canonical authorization resolves the governed object from ``resources``: a
missing row is a denial, never an allow (F-P17-I-02 · P17-AUTH-Q1). Therefore a
tenant or a space is not fully provisioned until its resource projection exists.

What this module owns
    * the structural object **and** its projection in one caller-owned
      transaction (``provision_tenant`` / ``provision_space``);
    * idempotent projection of already-existing objects (``ensure_*``);
    * an explicit, manual backfill entry point for pre-existing rows.

What this module deliberately does not own
    * no HTTP surface, no tenant/space CRUD API, no runtime entry point;
    * no migration, no DDL, no GRANT;
    * no schema invention — the resource grammar reused here is the existing
      ``(tenant_id, resource_type, natural_key)`` idempotency key plus
      ``space_id`` (see ``CORE_DOMAIN_MODEL.md`` §resources and
      ``B1-4_SCHEMA_DESIGN.md`` ``uq_resources_natural``).

Resource types reuse the canonical permission vocabulary
    ``permissions.resource_type`` already carries ``tenant`` / ``space`` /
    ``member`` (P13 seed), and the canonical RBAC layer only matches a
    permission when its ``resource_type`` equals the resource's type. The
    membership-collection resource is therefore typed ``member`` — not a name
    invented here.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from services.identity_runtime.resource_types import (
    MEMBER_RESOURCE_TYPE,
    SPACE_RESOURCE_TYPE,
    TENANT_RESOURCE_TYPE,
)

#: Natural key of the tenant-level membership collection within its tenant.
RESERVED_TENANT_COLLECTION_KEY = "members"

_ACTIVE = "active"
_CLASSIFICATION = "INTERNAL"


class ProvisioningError(RuntimeError):
    """A provisioning precondition failed (the operation must roll back)."""


def _insert_resource(
    session: Session,
    *,
    tenant_id: str,
    space_id: str | None,
    resource_type: str,
    natural_key: str,
    owner_id: str | None = None,
    resource_id: str | None = None,
) -> str:
    """Insert a resource row. ``resource_id`` mirrors the governed object when the
    platform addresses the resource by that object's own identifier (P16 does this
    for agents and tools: the authorization target *is* the object id)."""
    if resource_id is None:
        statement = (
            "INSERT INTO resources (tenant_id, space_id, owner_id, resource_type,"
            " natural_key, classification, status)"
            " VALUES (CAST(:tenant AS uuid), CAST(:space AS uuid), CAST(:owner AS uuid),"
            " :rtype, :natural, :classification, :status) RETURNING id"
        )
    else:
        statement = (
            "INSERT INTO resources (id, tenant_id, space_id, owner_id, resource_type,"
            " natural_key, classification, status)"
            " VALUES (CAST(:rid AS uuid), CAST(:tenant AS uuid), CAST(:space AS uuid),"
            " CAST(:owner AS uuid), :rtype, :natural, :classification, :status) RETURNING id"
        )
    row = session.execute(
        sa.text(statement),
        {
            "rid": resource_id,
            "tenant": tenant_id,
            "space": space_id,
            "owner": owner_id,
            "rtype": resource_type,
            "natural": natural_key,
            "classification": _CLASSIFICATION,
            "status": _ACTIVE,
        },
    ).scalar_one()
    return str(row)


def _find_resource(
    session: Session, *, tenant_id: str, space_id: str | None, resource_type: str
) -> str | None:
    row = session.execute(
        sa.text(
            "SELECT id FROM resources WHERE tenant_id = CAST(:tenant AS uuid)"
            " AND space_id IS NOT DISTINCT FROM CAST(:space AS uuid)"
            " AND resource_type = :rtype AND status = :status AND deleted_at IS NULL"
        ),
        {"tenant": tenant_id, "space": space_id, "rtype": resource_type, "status": _ACTIVE},
    ).first()
    return str(row[0]) if row is not None else None


def _tenant_exists(session: Session, tenant_id: str) -> bool:
    return session.execute(
        sa.text("SELECT 1 FROM tenants WHERE id = CAST(:t AS uuid)"), {"t": tenant_id}
    ).first() is not None


def _space_row(session: Session, tenant_id: str, space_id: str) -> dict[str, Any] | None:
    row = session.execute(
        sa.text(
            "SELECT id, tenant_id, key FROM spaces"
            " WHERE id = CAST(:s AS uuid) AND tenant_id = CAST(:t AS uuid)"
        ),
        {"s": space_id, "t": tenant_id},
    ).first()
    return dict(row._mapping) if row is not None else None


# --------------------------------------------------------------------- public
def ensure_resource_projection(
    session: Session, *, tenant_id: str, space_id: str | None = None
) -> dict[str, str]:
    """Idempotently project an existing structural object.

    Returns the resource ids that can be used as authorization targets. The
    caller owns the transaction: a projection failure must roll the whole
    provisioning operation back (P17-AUTH §76/§77).
    """
    if not _tenant_exists(session, tenant_id):
        raise ProvisioningError("tenant does not exist")

    created: dict[str, str] = {}
    if space_id is None:
        tenant_resource = _find_resource(
            session, tenant_id=tenant_id, space_id=None, resource_type=TENANT_RESOURCE_TYPE
        )
        if tenant_resource is None:
            slug = session.execute(
                sa.text("SELECT slug FROM tenants WHERE id = CAST(:t AS uuid)"), {"t": tenant_id}
            ).scalar_one()
            tenant_resource = _insert_resource(
                session, tenant_id=tenant_id, space_id=None,
                resource_type=TENANT_RESOURCE_TYPE, natural_key=str(slug),
            )
            created["tenant"] = tenant_resource
        collection = _find_resource(
            session, tenant_id=tenant_id, space_id=None, resource_type=MEMBER_RESOURCE_TYPE
        )
        if collection is None:
            collection = _insert_resource(
                session, tenant_id=tenant_id, space_id=None,
                resource_type=MEMBER_RESOURCE_TYPE, natural_key=RESERVED_TENANT_COLLECTION_KEY,
            )
            created["member_collection"] = collection
        return {"tenant": tenant_resource, "member_collection": collection}

    space = _space_row(session, tenant_id, space_id)
    if space is None:
        raise ProvisioningError("space does not exist in this tenant")
    space_resource = _find_resource(
        session, tenant_id=tenant_id, space_id=space_id, resource_type=SPACE_RESOURCE_TYPE
    )
    if space_resource is None:
        space_resource = _insert_resource(
            session, tenant_id=tenant_id, space_id=space_id,
            resource_type=SPACE_RESOURCE_TYPE, natural_key=str(space["key"]),
        )
        created["space"] = space_resource
    collection = _find_resource(
        session, tenant_id=tenant_id, space_id=space_id, resource_type=MEMBER_RESOURCE_TYPE
    )
    if collection is None:
        # The unique key is (tenant, type, natural_key); the tenant-level
        # collection owns the reserved key, so a space may not reuse it.
        if str(space["key"]) == RESERVED_TENANT_COLLECTION_KEY:
            raise ProvisioningError(
                f"space key {RESERVED_TENANT_COLLECTION_KEY!r} is reserved for the"
                " tenant-level membership collection"
            )
        collection = _insert_resource(
            session, tenant_id=tenant_id, space_id=space_id,
            resource_type=MEMBER_RESOURCE_TYPE, natural_key=str(space["key"]),
        )
        created["member_collection"] = collection
    return {"space": space_resource, "member_collection": collection}


def ensure_agent_projection(session: Session, *, tenant_id: str, agent_id: str) -> str:
    """Project the agent object P16 governs onto its canonical resource row.

    Same invariant as the tenant/space projection (P17-AUTH-Q1): a governed
    object without a ``resources`` row can never be authorized, so provisioning
    owns the row. ``space_id`` is taken from the agent itself, never from the
    caller, so the projection cannot be pointed at another space.
    """
    row = session.execute(
        sa.text(
            "SELECT id, tenant_id, space_id, key FROM agents"
            " WHERE id = CAST(:a AS uuid) AND tenant_id = CAST(:t AS uuid)"
        ),
        {"a": agent_id, "t": tenant_id},
    ).first()
    if row is None:
        raise ProvisioningError("agent does not exist in this tenant")
    agent = dict(row._mapping)
    agent_space = str(agent["space_id"]) if agent["space_id"] else None
    existing = _find_resource(
        session, tenant_id=tenant_id, space_id=agent_space, resource_type="agent"
    )
    if existing is not None:
        return existing
    return _insert_resource(
        session, tenant_id=tenant_id, space_id=agent_space,
        resource_type="agent", natural_key=str(agent["key"]), resource_id=agent_id,
    )


def provision_tenant(
    session: Session, *, slug: str, display_name: str, status: str = _ACTIVE
) -> dict[str, str]:
    """Create a tenant **and** its canonical projection in one transaction."""
    tenant_id = str(
        session.execute(
            sa.text(
                "INSERT INTO tenants (slug, display_name, status)"
                " VALUES (:slug, :name, :status) RETURNING id"
            ),
            {"slug": slug, "name": display_name, "status": status},
        ).scalar_one()
    )
    projection = ensure_resource_projection(session, tenant_id=tenant_id)
    return {"tenant_id": tenant_id, **projection}


def provision_space(
    session: Session,
    *,
    tenant_id: str,
    key: str,
    name: str,
    kind: str = "team",
    visibility: str = "tenant",
    status: str = _ACTIVE,
) -> dict[str, str]:
    """Create a space **and** its canonical projection in one transaction."""
    if key == RESERVED_TENANT_COLLECTION_KEY:
        raise ProvisioningError(
            f"space key {RESERVED_TENANT_COLLECTION_KEY!r} is reserved for the"
            " tenant-level membership collection"
        )
    space_id = str(
        session.execute(
            sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status)"
                " VALUES (CAST(:t AS uuid), :key, :name, :kind, :visibility, :status)"
                " RETURNING id"
            ),
            {"t": tenant_id, "key": key, "name": name, "kind": kind,
             "visibility": visibility, "status": status},
        ).scalar_one()
    )
    projection = ensure_resource_projection(session, tenant_id=tenant_id, space_id=space_id)
    return {"space_id": space_id, **projection}


def backfill_resource_projections(engine: Engine) -> dict[str, int]:
    """Explicit, manual backfill for structural rows that lack a projection.

    Never automatic, never part of the runtime request path, never silent: the
    operator runs it (for example ``python -m scripts.provision_resources``) and
    every object is projected in its own transaction, so a failure leaves that
    object unprojected instead of half-projected.
    """
    result = {"tenants": 0, "spaces": 0}
    with engine.connect() as conn:
        tenant_rows = conn.execute(
            sa.text(
                "SELECT t.id FROM tenants t"
                " WHERE NOT EXISTS (SELECT 1 FROM resources r WHERE r.tenant_id = t.id"
                "   AND r.resource_type = :rtype AND r.space_id IS NULL AND r.deleted_at IS NULL)"
            ),
            {"rtype": TENANT_RESOURCE_TYPE},
        ).all()
        space_rows = conn.execute(
            sa.text(
                "SELECT s.id, s.tenant_id FROM spaces s"
                " WHERE NOT EXISTS (SELECT 1 FROM resources r WHERE r.tenant_id = s.tenant_id"
                "   AND r.space_id = s.id AND r.resource_type = :rtype AND r.deleted_at IS NULL)"
            ),
            {"rtype": SPACE_RESOURCE_TYPE},
        ).all()

    tenant_ids = [str(row[0]) for row in tenant_rows]
    spaces = [(str(row[1]), str(row[0])) for row in space_rows]
    for tenant_id in tenant_ids:
        with Session(engine) as session, session.begin():
            ensure_resource_projection(session, tenant_id=tenant_id)
        result["tenants"] += 1
    for tenant_id, space_id in spaces:
        with Session(engine) as session, session.begin():
            ensure_resource_projection(session, tenant_id=tenant_id, space_id=space_id)
        result["spaces"] += 1
    return result


__all__ = [
    "MEMBER_RESOURCE_TYPE",
    "RESERVED_TENANT_COLLECTION_KEY",
    "SPACE_RESOURCE_TYPE",
    "TENANT_RESOURCE_TYPE",
    "ProvisioningError",
    "backfill_resource_projections",
    "ensure_agent_projection",
    "ensure_resource_projection",
    "provision_space",
    "provision_tenant",
]
