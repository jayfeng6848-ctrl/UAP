"""P18 control-plane persistence (scope-explicit, no generic CRUD).

Every statement names its scope: platform state, one tenant by slug, one space by
(tenant, key), one user, one membership. There is deliberately no ``get_by_id``
and no ``list_all``: the control plane only ever touches the objects a frozen
operation names, and it reads them under the same predicates it writes them.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

ACTIVE = "active"
PROVISIONING = "provisioning"


def _one(session: Session, sql: str, **params: Any) -> dict[str, Any] | None:
    row = session.execute(text(sql), params).one_or_none()
    return dict(row._mapping) if row is not None else None


class ControlPlaneRepository:
    """Structural reads/writes used by the control-plane use cases."""

    # ------------------------------------------------------------ platform
    def bootstrap_state(self, session: Session) -> str | None:
        row = _one(session, "SELECT bootstrap_state FROM platform_state WHERE id = 1")
        return str(row["bootstrap_state"]) if row is not None else None

    def user_status(self, session: Session, *, user_id: str) -> str | None:
        row = _one(
            session,
            "SELECT status FROM users WHERE id = CAST(:u AS uuid)",
            u=user_id,
        )
        return str(row["status"]) if row is not None else None

    # -------------------------------------------------------------- tenants
    def tenant_by_slug(self, session: Session, *, slug: str) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, slug, display_name, status FROM tenants WHERE lower(slug) = lower(:slug)",
            slug=slug,
        )

    def tenant(self, session: Session, *, tenant_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, slug, display_name, status FROM tenants WHERE id = CAST(:t AS uuid)",
            t=tenant_id,
        )

    def insert_tenant(
        self, session: Session, *, slug: str, display_name: str, status: str = PROVISIONING
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO tenants (slug, display_name, status)"
                " VALUES (:slug, :name, :status) RETURNING id"
            ),
            {"slug": slug, "name": display_name, "status": status},
        ).scalar_one()
        return str(row)

    def set_tenant_status(
        self, session: Session, *, tenant_id: str, status: str, expect: str | None = None
    ) -> int:
        sql = (
            "UPDATE tenants SET status = :status,"
            " archived_at = CASE WHEN :status = 'archived' THEN now() ELSE archived_at END,"
            " deleted_at = CASE WHEN :status = 'deleted' THEN now() ELSE deleted_at END"
            " WHERE id = CAST(:t AS uuid)"
        )
        params: dict[str, Any] = {"t": tenant_id, "status": status}
        if expect is not None:
            sql += " AND status = :expect"
            params["expect"] = expect
        return int(session.execute(text(sql), params).rowcount)

    def update_tenant_metadata(
        self, session: Session, *, tenant_id: str, display_name: str | None = None,
        plan: str | None = None, region: str | None = None,
    ) -> int:
        return int(session.execute(
            text(
                "UPDATE tenants SET display_name = COALESCE(:name, display_name),"
                " plan = COALESCE(:plan, plan), region = COALESCE(:region, region)"
                " WHERE id = CAST(:t AS uuid)"
            ),
            {"t": tenant_id, "name": display_name, "plan": plan, "region": region},
        ).rowcount)

    # --------------------------------------------------------------- spaces
    def space_by_key(
        self, session: Session, *, tenant_id: str, key: str
    ) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, tenant_id, key, name, visibility, status FROM spaces"
            " WHERE tenant_id = CAST(:t AS uuid) AND key = :key",
            t=tenant_id,
            key=key,
        )

    def space(self, session: Session, *, tenant_id: str, space_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, tenant_id, key, name, visibility, status FROM spaces"
            " WHERE id = CAST(:s AS uuid) AND tenant_id = CAST(:t AS uuid)",
            s=space_id,
            t=tenant_id,
        )

    def insert_space(
        self, session: Session, *, tenant_id: str, key: str, name: str, kind: str = "team",
        visibility: str = "tenant", status: str = ACTIVE, owner_id: str | None = None,
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status, owner_id)"
                " VALUES (CAST(:t AS uuid), :key, :name, :kind, :visibility, :status,"
                " CAST(:owner AS uuid)) RETURNING id"
            ),
            {"t": tenant_id, "key": key, "name": name, "kind": kind, "visibility": visibility,
             "status": status, "owner": owner_id},
        ).scalar_one()
        return str(row)

    def set_space_status(
        self, session: Session, *, tenant_id: str, space_id: str, status: str,
        expect: str | None = None,
    ) -> int:
        sql = (
            "UPDATE spaces SET status = :status,"
            " archived_at = CASE WHEN :status = 'archived' THEN now() ELSE archived_at END,"
            " deleted_at = CASE WHEN :status = 'deleted' THEN now() ELSE deleted_at END"
            " WHERE id = CAST(:s AS uuid) AND tenant_id = CAST(:t AS uuid)"
        )
        params: dict[str, Any] = {"s": space_id, "t": tenant_id, "status": status}
        if expect is not None:
            sql += " AND status = :expect"
            params["expect"] = expect
        return int(session.execute(text(sql), params).rowcount)

    def update_space_metadata(
        self, session: Session, *, tenant_id: str, space_id: str, name: str | None = None,
        visibility: str | None = None, owner_id: str | None = None,
    ) -> int:
        return int(session.execute(
            text(
                "UPDATE spaces SET name = COALESCE(:name, name),"
                " visibility = COALESCE(:visibility, visibility),"
                " owner_id = COALESCE(CAST(:owner AS uuid), owner_id)"
                " WHERE id = CAST(:s AS uuid) AND tenant_id = CAST(:t AS uuid)"
            ),
            {"s": space_id, "t": tenant_id, "name": name, "visibility": visibility,
             "owner": owner_id},
        ).rowcount)

    # ---------------------------------------------------------------- roles
    def find_role(
        self, session: Session, *, scope: str, tenant_id: str | None, space_id: str | None,
        key: str,
    ) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, scope, tenant_id, space_id, key, status FROM roles"
            " WHERE scope = :scope AND key = :key"
            " AND tenant_id IS NOT DISTINCT FROM CAST(:t AS uuid)"
            " AND space_id IS NOT DISTINCT FROM CAST(:s AS uuid)",
            scope=scope,
            key=key,
            t=tenant_id,
            s=space_id,
        )

    def insert_role(
        self, session: Session, *, scope: str, tenant_id: str | None, space_id: str | None,
        key: str, name: str,
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, is_system, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), :key, :name, :scope, false, 'active')"
                " RETURNING id"
            ),
            {"t": tenant_id, "s": space_id, "key": key, "name": name, "scope": scope},
        ).scalar_one()
        return str(row)

    def role_permission_keys(self, session: Session, *, role_id: str) -> set[str]:
        rows = session.execute(
            text(
                "SELECT p.key FROM role_permissions rp JOIN permissions p ON p.id = rp.permission_id"
                " WHERE rp.role_id = CAST(:r AS uuid)"
            ),
            {"r": role_id},
        ).all()
        return {str(row[0]) for row in rows}

    def bind_permissions(self, session: Session, *, role_id: str, keys: tuple[str, ...]) -> int:
        bound = 0
        for key in keys:
            bound += int(session.execute(
                text(
                    "INSERT INTO role_permissions (role_id, permission_id, effect)"
                    " SELECT CAST(:r AS uuid), p.id, 'allow' FROM permissions p"
                    " WHERE p.key = :key AND NOT EXISTS ("
                    "   SELECT 1 FROM role_permissions rp WHERE rp.role_id = CAST(:r AS uuid)"
                    "   AND rp.permission_id = p.id)"
                ),
                {"r": role_id, "key": key},
            ).rowcount)
        return bound

    # ----------------------------------------------------------- membership
    def tenant_membership(
        self, session: Session, *, tenant_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, status, role_id FROM tenant_memberships"
            " WHERE tenant_id = CAST(:t AS uuid) AND user_id = CAST(:u AS uuid)",
            t=tenant_id,
            u=user_id,
        )

    def insert_tenant_membership(
        self, session: Session, *, tenant_id: str, user_id: str, role_id: str
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status,"
                " role_assigned_at) VALUES (CAST(:t AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active', now()) RETURNING id"
            ),
            {"t": tenant_id, "u": user_id, "r": role_id},
        ).scalar_one()
        return str(row)

    def space_membership(
        self, session: Session, *, tenant_id: str, space_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return _one(
            session,
            "SELECT id, status, role_id FROM memberships"
            " WHERE tenant_id = CAST(:t AS uuid) AND space_id = CAST(:s AS uuid)"
            " AND user_id = CAST(:u AS uuid)",
            t=tenant_id,
            s=space_id,
            u=user_id,
        )

    def insert_space_membership(
        self, session: Session, *, tenant_id: str, space_id: str, user_id: str, role_id: str
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status, joined_at)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active', now()) RETURNING id"
            ),
            {"t": tenant_id, "s": space_id, "u": user_id, "r": role_id},
        ).scalar_one()
        return str(row)

    # ------------------------------------------------------------- lifecycle
    def tenant_state(self, session: Session, *, tenant_id: str) -> str | None:
        row = self.tenant(session, tenant_id=tenant_id)
        return str(row["status"]) if row is not None else None

    def space_state(self, session: Session, *, tenant_id: str, space_id: str) -> str | None:
        row = self.space(session, tenant_id=tenant_id, space_id=space_id)
        return str(row["status"]) if row is not None else None


__all__ = ["ACTIVE", "PROVISIONING", "ControlPlaneRepository"]
