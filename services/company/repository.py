"""Company persistence adapters (SQLAlchemy · tenant-scoped · no commits).

Implementations of the domain's repository ports. Every statement names its
tenant; there is deliberately no ``get_by_id`` without a tenant predicate (the
P16 lesson: an id-only lookup is a cross-tenant defect). Repositories never
commit — :class:`RuntimeDatabase.transaction` owns the boundary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from .projection import collection_resource, ensure_collection

_EMPLOYEE_COLUMNS = (
    "id, tenant_id, user_id, employee_no, display_name, title, status,"
    " hired_at, terminated_at, created_at, updated_at"
)
_ASSIGNMENT_COLUMNS = (
    "id, tenant_id, employee_id, space_id, assignment_role, status,"
    " started_at, ended_at, created_at, updated_at"
)

_ACTIVE = "active"


def _one(session: Session, sql: str, **params: Any) -> dict[str, Any] | None:
    row = session.execute(text(sql), params).one_or_none()
    return dict(row._mapping) if row is not None else None


class EmployeeRepository:
    """Tenant-scoped employee persistence (implements the domain port)."""

    def insert(
        self,
        session: Session,
        *,
        tenant_id: str,
        employee_no: str,
        display_name: str,
        title: str | None,
        hired_at: datetime | None,
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO company_employees (tenant_id, employee_no, display_name,"
                " title, status, hired_at)"
                " VALUES (CAST(:t AS uuid), :no, :name, :title, :status, :hired_at)"
                " RETURNING id"
            ),
            {
                "t": tenant_id,
                "no": employee_no,
                "name": display_name,
                "title": title,
                "status": _ACTIVE,
                "hired_at": hired_at,
            },
        ).scalar_one()
        return str(row)

    def get(
        self, session: Session, *, tenant_id: str, employee_id: str
    ) -> Mapping[str, Any] | None:
        return _one(
            session,
            f"SELECT {_EMPLOYEE_COLUMNS} FROM company_employees"
            " WHERE id = CAST(:e AS uuid) AND tenant_id = CAST(:t AS uuid)",
            e=employee_id,
            t=tenant_id,
        )

    def find_by_no(
        self, session: Session, *, tenant_id: str, employee_no: str
    ) -> Mapping[str, Any] | None:
        return _one(
            session,
            f"SELECT {_EMPLOYEE_COLUMNS} FROM company_employees"
            " WHERE tenant_id = CAST(:t AS uuid) AND employee_no = :no",
            t=tenant_id,
            no=employee_no,
        )

    def list(
        self,
        session: Session,
        *,
        tenant_id: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mapping[str, Any]]:
        rows = session.execute(
            text(
                f"SELECT {_EMPLOYEE_COLUMNS} FROM company_employees"
                " WHERE tenant_id = CAST(:t AS uuid)"
                " AND (CAST(:status AS text) IS NULL OR status = CAST(:status AS text))"
                " ORDER BY created_at DESC, id DESC LIMIT :limit"
            ),
            {"t": tenant_id, "status": status, "limit": limit},
        ).all()
        return [dict(row._mapping) for row in rows]

    def update_profile(
        self,
        session: Session,
        *,
        tenant_id: str,
        employee_id: str,
        display_name: str | None,
        title: str | None,
    ) -> int:
        result = session.execute(
            text(
                "UPDATE company_employees SET"
                " display_name = COALESCE(:name, display_name),"
                " title = COALESCE(:title, title)"
                " WHERE id = CAST(:e AS uuid) AND tenant_id = CAST(:t AS uuid)"
            ),
            {"name": display_name, "title": title, "e": employee_id, "t": tenant_id},
        )
        return int(result.rowcount or 0)

    def bind_user(
        self,
        session: Session,
        *,
        tenant_id: str,
        employee_id: str,
        user_id: str | None,
    ) -> int:
        result = session.execute(
            text(
                "UPDATE company_employees SET user_id = CAST(:u AS uuid)"
                " WHERE id = CAST(:e AS uuid) AND tenant_id = CAST(:t AS uuid)"
            ),
            {"u": user_id, "e": employee_id, "t": tenant_id},
        )
        return int(result.rowcount or 0)

    def set_status(
        self,
        session: Session,
        *,
        tenant_id: str,
        employee_id: str,
        expect: str,
        status: str,
        terminated_at: datetime | None,
    ) -> int:
        result = session.execute(
            text(
                "UPDATE company_employees SET status = :status,"
                " terminated_at = :terminated_at"
                " WHERE id = CAST(:e AS uuid) AND tenant_id = CAST(:t AS uuid)"
                " AND status = :expect"
            ),
            {
                "status": status,
                "terminated_at": terminated_at,
                "e": employee_id,
                "t": tenant_id,
                "expect": expect,
            },
        )
        return int(result.rowcount or 0)


class AssignmentRepository:
    """Tenant-scoped assignment persistence (implements the domain port)."""

    def insert(
        self,
        session: Session,
        *,
        tenant_id: str,
        employee_id: str,
        space_id: str,
        assignment_role: str,
    ) -> str:
        row = session.execute(
            text(
                "INSERT INTO company_assignments (tenant_id, employee_id, space_id,"
                " assignment_role, status)"
                " VALUES (CAST(:t AS uuid), CAST(:e AS uuid), CAST(:s AS uuid), :role, :status)"
                " RETURNING id"
            ),
            {
                "t": tenant_id,
                "e": employee_id,
                "s": space_id,
                "role": assignment_role,
                "status": _ACTIVE,
            },
        ).scalar_one()
        return str(row)

    def get(
        self, session: Session, *, tenant_id: str, assignment_id: str
    ) -> Mapping[str, Any] | None:
        return _one(
            session,
            f"SELECT {_ASSIGNMENT_COLUMNS} FROM company_assignments"
            " WHERE id = CAST(:a AS uuid) AND tenant_id = CAST(:t AS uuid)",
            a=assignment_id,
            t=tenant_id,
        )

    def list(
        self,
        session: Session,
        *,
        tenant_id: str,
        employee_id: str | None = None,
        space_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mapping[str, Any]]:
        rows = session.execute(
            text(
                f"SELECT {_ASSIGNMENT_COLUMNS} FROM company_assignments"
                " WHERE tenant_id = CAST(:t AS uuid)"
                " AND (CAST(:employee_id AS uuid) IS NULL"
                "      OR employee_id = CAST(:employee_id AS uuid))"
                " AND (CAST(:space_id AS uuid) IS NULL OR space_id = CAST(:space_id AS uuid))"
                " AND (CAST(:status AS text) IS NULL OR status = CAST(:status AS text))"
                " ORDER BY created_at DESC, id DESC LIMIT :limit"
            ),
            {
                "t": tenant_id,
                "employee_id": employee_id,
                "space_id": space_id,
                "status": status,
                "limit": limit,
            },
        ).all()
        return [dict(row._mapping) for row in rows]

    def find_active(
        self, session: Session, *, tenant_id: str, employee_id: str, space_id: str
    ) -> Mapping[str, Any] | None:
        return _one(
            session,
            f"SELECT {_ASSIGNMENT_COLUMNS} FROM company_assignments"
            " WHERE tenant_id = CAST(:t AS uuid) AND employee_id = CAST(:e AS uuid)"
            " AND space_id = CAST(:s AS uuid) AND ended_at IS NULL",
            t=tenant_id,
            e=employee_id,
            s=space_id,
        )

    def update_role(
        self,
        session: Session,
        *,
        tenant_id: str,
        assignment_id: str,
        assignment_role: str,
    ) -> int:
        result = session.execute(
            text(
                "UPDATE company_assignments SET assignment_role = :role"
                " WHERE id = CAST(:a AS uuid) AND tenant_id = CAST(:t AS uuid)"
            ),
            {"role": assignment_role, "a": assignment_id, "t": tenant_id},
        )
        return int(result.rowcount or 0)

    def end(
        self,
        session: Session,
        *,
        tenant_id: str,
        assignment_id: str,
        expect: str,
        ended_at: datetime,
    ) -> int:
        result = session.execute(
            text(
                "UPDATE company_assignments SET status = 'ended', ended_at = :ended_at"
                " WHERE id = CAST(:a AS uuid) AND tenant_id = CAST(:t AS uuid)"
                " AND status = :expect"
            ),
            {"ended_at": ended_at, "a": assignment_id, "t": tenant_id, "expect": expect},
        )
        return int(result.rowcount or 0)


class ResourceProjectionRepository:
    """Tenant collection-resource projection (read for use cases, ensure for operators)."""

    def collection(
        self, session: Session, *, tenant_id: str, resource_type: str
    ) -> str | None:
        return collection_resource(session, tenant_id=tenant_id, resource_type=resource_type)

    def ensure_collection(
        self, session: Session, *, tenant_id: str, resource_type: str
    ) -> str:
        return ensure_collection(session, tenant_id=tenant_id, resource_type=resource_type)


__all__ = ["AssignmentRepository", "EmployeeRepository", "ResourceProjectionRepository"]
