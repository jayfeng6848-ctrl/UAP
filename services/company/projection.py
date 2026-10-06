"""Canonical Company collection-resource projection (pre-built, never auto-created).

Frozen by PDL Appendix AF D-P20D-02 (tenant-level collection resource) and the
implementation authorization §G2 (pre-provisioned model):

* one ``resources`` row per tenant **per** resource type (``company_employee`` /
  ``company_assignment``) with the reserved natural keys ``employees`` /
  ``assignments``;
* a missing row is a **denial**, never a self-healing create from a business
  request path (P17-AUTH-Q1);
* projection is a service/infrastructure responsibility — the domain never touches
  ``resources`` and the use cases only ever read it.

``ensure_collection`` is the **operator/pre-provisioning** entry point used by
``scripts/provision_company_resources.py`` and by tests. Business use cases call
``collection_resource`` only.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from domains.company.ports import (
    ASSIGNMENT_COLLECTION_KEY,
    ASSIGNMENT_RESOURCE_TYPE,
    EMPLOYEE_COLLECTION_KEY,
    EMPLOYEE_RESOURCE_TYPE,
)

COLLECTION_NATURAL_KEYS: dict[str, str] = {
    EMPLOYEE_RESOURCE_TYPE: EMPLOYEE_COLLECTION_KEY,
    ASSIGNMENT_RESOURCE_TYPE: ASSIGNMENT_COLLECTION_KEY,
}

_ACTIVE = "active"
_CLASSIFICATION = "INTERNAL"


class ProjectionError(RuntimeError):
    """Projection precondition failed (the caller rolls the transaction back)."""


def collection_resource(
    session: Session, *, tenant_id: str, resource_type: str
) -> str | None:
    """Return the canonical collection resource id, or ``None`` when unprojected."""
    natural_key = COLLECTION_NATURAL_KEYS.get(resource_type)
    if natural_key is None:
        raise ProjectionError("unknown company resource type")
    row = session.execute(
        text(
            "SELECT id FROM resources WHERE tenant_id = CAST(:t AS uuid)"
            " AND resource_type = :rtype AND natural_key = :key"
            " AND status = :status AND deleted_at IS NULL"
        ),
        {"t": tenant_id, "rtype": resource_type, "key": natural_key, "status": _ACTIVE},
    ).first()
    return str(row[0]) if row is not None else None


def ensure_collection(session: Session, *, tenant_id: str, resource_type: str) -> str:
    """Idempotently pre-provision one tenant collection resource.

    Operator/pre-provisioning path only: the business request path must never
    create a projection (a missing row is a denial).
    """
    existing = collection_resource(session, tenant_id=tenant_id, resource_type=resource_type)
    if existing is not None:
        return existing
    natural_key = COLLECTION_NATURAL_KEYS.get(resource_type)
    if natural_key is None:
        raise ProjectionError("unknown company resource type")
    row = session.execute(
        text(
            "INSERT INTO resources (tenant_id, space_id, owner_id, resource_type,"
            " natural_key, classification, status)"
            " VALUES (CAST(:t AS uuid), NULL, NULL, :rtype, :key, :classification, :status)"
            " RETURNING id"
        ),
        {
            "t": tenant_id,
            "rtype": resource_type,
            "key": natural_key,
            "classification": _CLASSIFICATION,
            "status": _ACTIVE,
        },
    ).scalar_one()
    return str(row)


def ensure_company_collections(session: Session, *, tenant_id: str) -> dict[str, str]:
    """Pre-provision both Company collections for one tenant."""
    return {
        resource_type: ensure_collection(
            session, tenant_id=tenant_id, resource_type=resource_type
        )
        for resource_type in COLLECTION_NATURAL_KEYS
    }


def backfill_company_collections(
    engine: Engine, *, tenant_id: str | None = None
) -> dict[str, int]:
    """Explicit operator backfill (never automatic, never in a request path).

    Projects every tenant that lacks a Company collection resource. Each tenant is
    projected in its own transaction so a failure leaves that tenant untouched
    rather than half-projected.
    """
    with engine.connect() as conn:
        if tenant_id is None:
            rows = conn.execute(
                text("SELECT id FROM tenants WHERE status <> 'deleted' ORDER BY id")
            ).all()
            tenant_ids = [str(row[0]) for row in rows]
        else:
            tenant_ids = [tenant_id]

    projected = 0
    created = 0
    for tid in tenant_ids:
        for resource_type in COLLECTION_NATURAL_KEYS:
            with Session(engine) as session, session.begin():
                before = collection_resource(
                    session, tenant_id=tid, resource_type=resource_type
                )
                ensure_collection(session, tenant_id=tid, resource_type=resource_type)
            projected += 1
            if before is None:
                created += 1
    return {"tenants": len(tenant_ids), "projected": projected, "created": created}


__all__ = [
    "COLLECTION_NATURAL_KEYS",
    "ProjectionError",
    "backfill_company_collections",
    "collection_resource",
    "ensure_collection",
    "ensure_company_collections",
]
