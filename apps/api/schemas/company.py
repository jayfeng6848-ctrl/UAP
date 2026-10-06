"""Company API DTOs (frozen contract — PDL Appendix AG · D-P20A-06 = C).

``Database Schema != API Contract``: every field below is an explicit API-contract
decision, never a reflected table column. The API returns these models only — no
ORM object, no database row and no raw table dict ever leaves a Company route.

Adding a field is therefore a *contract* change and requires a new decision; that
is exactly the property the freeze asked for (a future ``salary`` column must not
silently appear in the public API).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domains.company import Assignment, Employee

#: Frozen employee field whitelist (API contract, not database columns).
EMPLOYEE_FIELDS: tuple[str, ...] = (
    "employee_id", "tenant_id", "employee_no", "display_name", "title", "status",
    "user_id", "hired_at", "terminated_at", "created_at", "updated_at",
)

#: Frozen assignment field whitelist.
ASSIGNMENT_FIELDS: tuple[str, ...] = (
    "assignment_id", "tenant_id", "employee_id", "space_id", "assignment_role",
    "status", "started_at", "ended_at", "created_at", "updated_at",
)


class EmployeeCreateRequest(BaseModel):
    """Create one employee (``Employee != User``; no identity fields accepted)."""

    employee_no: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1)
    title: str | None = None
    hired_at: datetime | None = None


class EmployeeUpdateRequest(BaseModel):
    """Profile update: at least one field must be supplied (else 422)."""

    display_name: str | None = None
    title: str | None = None


class EmployeeResponse(BaseModel):
    """Frozen API representation of an employee."""

    employee_id: str
    tenant_id: str
    employee_no: str
    display_name: str
    title: str | None = None
    status: str
    user_id: str | None = None
    hired_at: datetime | None = None
    terminated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, employee: Employee) -> "EmployeeResponse":
        """Explicit, field-by-field projection (never ``vars()`` / ``dict(row)``)."""
        return cls(
            employee_id=employee.id,
            tenant_id=employee.tenant_id,
            employee_no=employee.employee_no,
            display_name=employee.display_name,
            title=employee.title,
            status=employee.status,
            user_id=employee.user_id,
            hired_at=employee.hired_at,
            terminated_at=employee.terminated_at,
            created_at=employee.created_at,
            updated_at=employee.updated_at,
        )


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    count: int
    limit: int


class AssignmentCreateRequest(BaseModel):
    employee_id: str = Field(min_length=1)
    space_id: str = Field(min_length=1)
    assignment_role: str = "member"


class AssignmentUpdateRequest(BaseModel):
    assignment_role: str = Field(min_length=1)


class AssignmentResponse(BaseModel):
    """Frozen API representation of an assignment."""

    assignment_id: str
    tenant_id: str
    employee_id: str
    space_id: str
    assignment_role: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, assignment: Assignment) -> "AssignmentResponse":
        return cls(
            assignment_id=assignment.id,
            tenant_id=assignment.tenant_id,
            employee_id=assignment.employee_id,
            space_id=assignment.space_id,
            assignment_role=assignment.assignment_role,
            status=assignment.status,
            started_at=assignment.started_at,
            ended_at=assignment.ended_at,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )


class AssignmentListResponse(BaseModel):
    items: list[AssignmentResponse]
    count: int
    limit: int


__all__ = [
    "ASSIGNMENT_FIELDS",
    "EMPLOYEE_FIELDS",
    "AssignmentCreateRequest",
    "AssignmentListResponse",
    "AssignmentResponse",
    "AssignmentUpdateRequest",
    "EmployeeCreateRequest",
    "EmployeeListResponse",
    "EmployeeResponse",
    "EmployeeUpdateRequest",
]
