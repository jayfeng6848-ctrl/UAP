"""Scope-explicit repositories (P17 §8–§12 / §37–§38).

Every query carries its scope predicate. There is deliberately no generic
``get_by_id``: tenant and space reads are actor-scoped through membership, so a
row can never be mistaken for an authorization fact.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .resource_types import MEMBER_RESOURCE_TYPE

ACTIVE = "active"

TENANT_COLUMNS = "id, slug, display_name, status"
SPACE_COLUMNS = "id, tenant_id, key, name, kind, visibility, status"
TENANT_MEMBERSHIP_COLUMNS = "id, tenant_id, user_id, role_id, status"
SPACE_MEMBERSHIP_COLUMNS = "id, tenant_id, space_id, user_id, role_id, status"
ROLE_COLUMNS = "id, tenant_id, space_id, key, scope, is_system, status"


def _one(session: Session, sql: str, **params: Any) -> dict[str, Any] | None:
    row = session.execute(text(sql), params).one_or_none()
    return dict(row._mapping) if row is not None else None


def _all(session: Session, sql: str, **params: Any) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in session.execute(text(sql), params).all()]


class TenantRepository:
    """Tenant reads only (tenant writes are control-plane · OUT of P17)."""

    def get_member_tenant(self, session: Session, *, tenant_id: str, actor_id: str) -> dict[str, Any] | None:
        """Tenant readable by this actor (membership required · no fallback)."""
        return _one(
            session,
            f"SELECT t.{TENANT_COLUMNS.replace(', ', ', t.')} FROM tenants t"
            " JOIN tenant_memberships tm ON tm.tenant_id = t.id"
            " WHERE t.id = CAST(:tenant AS uuid) AND tm.user_id = CAST(:actor AS uuid)"
            " AND tm.status = :active",
            tenant=tenant_id,
            actor=actor_id,
            active=ACTIVE,
        )

    def list_member_tenants(self, session: Session, *, actor_id: str) -> list[dict[str, Any]]:
        return _all(
            session,
            f"SELECT t.{TENANT_COLUMNS.replace(', ', ', t.')} FROM tenants t"
            " JOIN tenant_memberships tm ON tm.tenant_id = t.id"
            " WHERE tm.user_id = CAST(:actor AS uuid) AND tm.status = :active"
            " ORDER BY t.id",
            actor=actor_id,
            active=ACTIVE,
        )


class SpaceRepository:
    """Space reads, always scoped by tenant **and** membership."""

    def get_member_space(
        self, session: Session, *, tenant_id: str, space_id: str, actor_id: str
    ) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT s.{SPACE_COLUMNS.replace(', ', ', s.')} FROM spaces s"
            " JOIN tenant_memberships tm ON tm.tenant_id = s.tenant_id"
            " JOIN memberships m ON m.space_id = s.id AND m.user_id = tm.user_id"
            " WHERE s.id = CAST(:space AS uuid) AND s.tenant_id = CAST(:tenant AS uuid)"
            " AND tm.user_id = CAST(:actor AS uuid) AND tm.status = :active AND m.status = :active",
            space=space_id,
            tenant=tenant_id,
            actor=actor_id,
            active=ACTIVE,
        )

    def list_member_spaces(self, session: Session, *, tenant_id: str, actor_id: str) -> list[dict[str, Any]]:
        return _all(
            session,
            f"SELECT s.{SPACE_COLUMNS.replace(', ', ', s.')} FROM spaces s"
            " JOIN memberships m ON m.space_id = s.id"
            " WHERE s.tenant_id = CAST(:tenant AS uuid) AND m.user_id = CAST(:actor AS uuid)"
            " AND m.status = :active ORDER BY s.id",
            tenant=tenant_id,
            actor=actor_id,
            active=ACTIVE,
        )

    def space_belongs_to_tenant(self, session: Session, *, tenant_id: str, space_id: str) -> bool:
        row = _one(
            session,
            "SELECT id FROM spaces WHERE id = CAST(:space AS uuid) AND tenant_id = CAST(:tenant AS uuid)",
            space=space_id,
            tenant=tenant_id,
        )
        return row is not None


class MembershipRepository:
    """Membership reads/writes (the only P17 write surface)."""

    # ------------------------------------------------------------------ tenant
    def get_tenant_membership(self, session: Session, *, tenant_id: str, user_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {TENANT_MEMBERSHIP_COLUMNS} FROM tenant_memberships"
            " WHERE tenant_id = CAST(:tenant AS uuid) AND user_id = CAST(:user AS uuid)",
            tenant=tenant_id,
            user=user_id,
        )

    def list_tenant_members(self, session: Session, *, tenant_id: str) -> list[dict[str, Any]]:
        return _all(
            session,
            f"SELECT {TENANT_MEMBERSHIP_COLUMNS} FROM tenant_memberships"
            " WHERE tenant_id = CAST(:tenant AS uuid) ORDER BY created_at, id",
            tenant=tenant_id,
        )

    # ------------------------------------------------------------------- space
    def get_space_membership(
        self, session: Session, *, tenant_id: str, space_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {SPACE_MEMBERSHIP_COLUMNS} FROM memberships"
            " WHERE tenant_id = CAST(:tenant AS uuid) AND space_id = CAST(:space AS uuid)"
            " AND user_id = CAST(:user AS uuid)",
            tenant=tenant_id,
            space=space_id,
            user=user_id,
        )

    def list_space_members(self, session: Session, *, tenant_id: str, space_id: str) -> list[dict[str, Any]]:
        return _all(
            session,
            f"SELECT {SPACE_MEMBERSHIP_COLUMNS} FROM memberships"
            " WHERE tenant_id = CAST(:tenant AS uuid) AND space_id = CAST(:space AS uuid)"
            " ORDER BY created_at, id",
            tenant=tenant_id,
            space=space_id,
        )

    # ------------------------------------------------------------- role lookup
    def get_role(self, session: Session, *, role_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {ROLE_COLUMNS} FROM roles WHERE id = CAST(:role AS uuid)",
            role=role_id,
        )

    def user_exists(self, session: Session, *, user_id: str) -> bool:
        row = _one(session, "SELECT id FROM users WHERE id = CAST(:user AS uuid)", user=user_id)
        return row is not None

    def tenant_exists(self, session: Session, *, tenant_id: str) -> bool:
        row = _one(session, "SELECT id FROM tenants WHERE id = CAST(:tenant AS uuid)", tenant=tenant_id)
        return row is not None

    def has_active_tenant_membership(self, session: Session, *, tenant_id: str, user_id: str) -> bool:
        """True when ``user_id`` is an active member of ``tenant_id``.

        P17-AUTH invariant 14: a space member must already belong to the tenant
        that owns the space — a space membership never creates tenant standing.
        """
        row = self.get_tenant_membership(session, tenant_id=tenant_id, user_id=user_id)
        return row is not None and str(row.get("status")) == ACTIVE


class MembershipResourceRepository:
    """The canonical membership-collection resources (P17-AUTH-Q1).

    Authorization resolves the governed object from ``resources``
    (F-P17-I-02): the tenant collection is ``(tenant, 'member', space NULL)``
    and the space collection is ``(tenant, 'member', space S)``. Every lookup
    carries the full scope predicate — never an id-only read (P17 §32).
    """

    def tenant_collection(self, session: Session, *, tenant_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, tenant_id, space_id, resource_type FROM resources"
            " WHERE tenant_id = CAST(:tenant AS uuid) AND space_id IS NULL"
            " AND resource_type = :rtype AND status = :active AND deleted_at IS NULL",
            tenant=tenant_id,
            rtype=MEMBER_RESOURCE_TYPE,
            active=ACTIVE,
        )

    def space_collection(
        self, session: Session, *, tenant_id: str, space_id: str
    ) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, tenant_id, space_id, resource_type FROM resources"
            " WHERE tenant_id = CAST(:tenant AS uuid) AND space_id = CAST(:space AS uuid)"
            " AND resource_type = :rtype AND status = :active AND deleted_at IS NULL",
            tenant=tenant_id,
            space=space_id,
            rtype=MEMBER_RESOURCE_TYPE,
            active=ACTIVE,
        )
