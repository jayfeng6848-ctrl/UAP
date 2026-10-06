"""Company repository ports (interfaces only — no implementation).

The domain declares *what* it needs; the persistence library, the database and the
transaction boundary belong to the service/infrastructure adapters (implementation
contract §3–§4). ``session`` is typed as ``Any`` on purpose so this module stays
free of any persistence import.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol, runtime_checkable

#: Authorization resource types (frozen by the 0019 permission rows).
EMPLOYEE_RESOURCE_TYPE = "company_employee"
ASSIGNMENT_RESOURCE_TYPE = "company_assignment"

#: Reserved collection natural keys (D-P20D-02; AF delegated the exact value to
#: the implementation contract).
EMPLOYEE_COLLECTION_KEY = "employees"
ASSIGNMENT_COLLECTION_KEY = "assignments"

COLLECTION_KEYS: dict[str, str] = {
    EMPLOYEE_RESOURCE_TYPE: EMPLOYEE_COLLECTION_KEY,
    ASSIGNMENT_RESOURCE_TYPE: ASSIGNMENT_COLLECTION_KEY,
}


@runtime_checkable
class EmployeeRepository(Protocol):
    """Tenant-scoped employee persistence (no method may omit the tenant)."""

    def insert(
        self,
        session: Any,
        *,
        tenant_id: str,
        employee_no: str,
        display_name: str,
        title: str | None,
        hired_at: datetime | None,
    ) -> str: ...

    def get(self, session: Any, *, tenant_id: str, employee_id: str) -> Mapping[str, Any] | None: ...

    def find_by_no(
        self, session: Any, *, tenant_id: str, employee_no: str
    ) -> Mapping[str, Any] | None: ...

    def list(
        self,
        session: Any,
        *,
        tenant_id: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mapping[str, Any]]: ...

    def update_profile(
        self,
        session: Any,
        *,
        tenant_id: str,
        employee_id: str,
        display_name: str | None,
        title: str | None,
    ) -> int: ...

    def bind_user(
        self, session: Any, *, tenant_id: str, employee_id: str, user_id: str | None
    ) -> int: ...

    def set_status(
        self,
        session: Any,
        *,
        tenant_id: str,
        employee_id: str,
        expect: str,
        status: str,
        terminated_at: datetime | None,
    ) -> int: ...


@runtime_checkable
class AssignmentRepository(Protocol):
    """Tenant-scoped assignment persistence."""

    def insert(
        self,
        session: Any,
        *,
        tenant_id: str,
        employee_id: str,
        space_id: str,
        assignment_role: str,
    ) -> str: ...

    def get(self, session: Any, *, tenant_id: str, assignment_id: str) -> Mapping[str, Any] | None: ...

    def list(
        self,
        session: Any,
        *,
        tenant_id: str,
        employee_id: str | None = None,
        space_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mapping[str, Any]]: ...

    def find_active(
        self, session: Any, *, tenant_id: str, employee_id: str, space_id: str
    ) -> Mapping[str, Any] | None: ...

    def update_role(
        self, session: Any, *, tenant_id: str, assignment_id: str, assignment_role: str
    ) -> int: ...

    def end(
        self,
        session: Any,
        *,
        tenant_id: str,
        assignment_id: str,
        expect: str,
        ended_at: datetime,
    ) -> int: ...


@runtime_checkable
class ResourceProjectionRepository(Protocol):
    """Canonical collection-resource projection (pre-built; never business-path created)."""

    def collection(
        self, session: Any, *, tenant_id: str, resource_type: str
    ) -> str | None: ...

    def ensure_collection(
        self, session: Any, *, tenant_id: str, resource_type: str
    ) -> str: ...


__all__ = [
    "ASSIGNMENT_COLLECTION_KEY",
    "ASSIGNMENT_RESOURCE_TYPE",
    "COLLECTION_KEYS",
    "EMPLOYEE_COLLECTION_KEY",
    "EMPLOYEE_RESOURCE_TYPE",
    "AssignmentRepository",
    "EmployeeRepository",
    "ResourceProjectionRepository",
]
