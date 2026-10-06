"""Company domain entities: Employee and Assignment.

Pure data + invariants. ``from_row`` accepts the plain mapping a repository
returns, so the domain never imports a persistence library and never sees an ORM
object. Nothing here performs I/O or authorization.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Mapping

from .errors import CompanyDomainError, DomainErrorCode
from .values import (
    ASSIGNMENT_ROLES,
    ASSIGNMENT_STATUSES,
    EMPLOYEE_STATUSES,
    assignment_can_transition,
    employee_can_transition,
    is_valid_employee_no,
)


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CompanyDomainError(DomainErrorCode.INVALID_INPUT, f"{field} is required")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CompanyDomainError(DomainErrorCode.INVALID_INPUT, "text field must be a string")
    return value


@dataclass(frozen=True, slots=True)
class Employee:
    """A company employee (``Employee != User``; ``user_id`` is optional)."""

    id: str
    tenant_id: str
    employee_no: str
    display_name: str
    status: str = "active"
    title: str | None = None
    user_id: str | None = None
    hired_at: datetime | None = None
    terminated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.status not in EMPLOYEE_STATUSES:
            raise CompanyDomainError(
                DomainErrorCode.INVALID_INPUT, f"unknown employee status {self.status!r}"
            )
        if not is_valid_employee_no(self.employee_no):
            raise CompanyDomainError(
                DomainErrorCode.INVALID_EMPLOYEE_NO, "employee number shape is invalid"
            )
        terminated = self.status == "terminated"
        if terminated != (self.terminated_at is not None):
            raise CompanyDomainError(
                DomainErrorCode.INVALID_INPUT,
                "terminated must agree with terminated_at (frozen lifecycle CHECK)",
            )

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Employee":
        """Build an entity from a repository mapping (values already persisted)."""
        return cls(
            id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            employee_no=str(row["employee_no"]),
            display_name=str(row["display_name"]),
            status=str(row["status"]),
            title=row.get("title"),
            user_id=str(row["user_id"]) if row.get("user_id") else None,
            hired_at=row.get("hired_at"),
            terminated_at=row.get("terminated_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    @property
    def is_terminated(self) -> bool:
        return self.status == "terminated"

    def can_transition_to(self, target: str) -> bool:
        return employee_can_transition(self.status, target)

    def transition_to(self, target: str, *, at: datetime) -> "Employee":
        """Return the next lifecycle state, or raise (``terminated`` is terminal)."""
        if self.status == "terminated":
            raise CompanyDomainError(
                DomainErrorCode.EMPLOYEE_ALREADY_TERMINATED, "terminated is terminal"
            )
        if not self.can_transition_to(target):
            raise CompanyDomainError(
                DomainErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT,
                f"transition {self.status} -> {target} is not allowed",
            )
        if target == "terminated":
            return replace(self, status=target, terminated_at=at)
        return replace(self, status=target, terminated_at=None)


@dataclass(frozen=True, slots=True)
class Assignment:
    """A business organizational assignment (employee ↔ space/department)."""

    id: str
    tenant_id: str
    employee_id: str
    space_id: str
    assignment_role: str
    status: str = "active"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.status not in ASSIGNMENT_STATUSES:
            raise CompanyDomainError(
                DomainErrorCode.INVALID_INPUT, f"unknown assignment status {self.status!r}"
            )
        if self.assignment_role not in ASSIGNMENT_ROLES:
            raise CompanyDomainError(
                DomainErrorCode.INVALID_ASSIGNMENT_ROLE,
                f"unknown assignment role {self.assignment_role!r}",
            )
        ended = self.status == "ended"
        if ended != (self.ended_at is not None):
            raise CompanyDomainError(
                DomainErrorCode.INVALID_INPUT,
                "ended must agree with ended_at (frozen lifecycle CHECK)",
            )

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Assignment":
        return cls(
            id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            employee_id=str(row["employee_id"]),
            space_id=str(row["space_id"]),
            assignment_role=str(row["assignment_role"]),
            status=str(row["status"]),
            started_at=row.get("started_at"),
            ended_at=row.get("ended_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def can_transition_to(self, target: str) -> bool:
        return assignment_can_transition(self.status, target)

    def end(self, *, at: datetime) -> "Assignment":
        if self.status == "ended":
            raise CompanyDomainError(
                DomainErrorCode.ASSIGNMENT_ALREADY_ENDED, "ended is terminal"
            )
        if not self.can_transition_to("ended"):
            raise CompanyDomainError(
                DomainErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT,
                f"transition {self.status} -> ended is not allowed",
            )
        return replace(self, status="ended", ended_at=at)


def validate_employee_inputs(
    *, employee_no: str, display_name: str, title: str | None = None
) -> tuple[str, str, str | None]:
    """Validate create/update inputs before any repository write."""
    if not is_valid_employee_no(employee_no):
        raise CompanyDomainError(
            DomainErrorCode.INVALID_EMPLOYEE_NO, "employee number shape is invalid"
        )
    return _text(employee_no, field="employee_no"), _text(
        display_name, field="display_name"
    ), _optional_text(title)


def validate_assignment_inputs(*, assignment_role: str) -> str:
    if assignment_role not in ASSIGNMENT_ROLES:
        raise CompanyDomainError(
            DomainErrorCode.INVALID_ASSIGNMENT_ROLE,
            f"unknown assignment role {assignment_role!r}",
        )
    return assignment_role


__all__ = [
    "Assignment",
    "Employee",
    "validate_assignment_inputs",
    "validate_employee_inputs",
]
