"""Company domain contract surface (pure — no I/O, no persistence, no authorization).

Activated under ``P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION`` (PDL Appendix
AF · D-P20D-01…11). The domain owns entities, value objects, invariants, ports and
domain errors only:

* no ORM, no persistence library, no SQL text and no infrastructure import
  (guard ``G-4`` + the domain purity guard),
* no authorization logic — the single engine lives in ``services.authorization``,
* no event, no API, no worker.

Use-case orchestration (authorize → validate → write → audit → commit) lives in
``services.company``, which depends on these contracts.
"""

from __future__ import annotations

from .entities import (
    Assignment,
    Employee,
    validate_assignment_inputs,
    validate_employee_inputs,
)
from .errors import CompanyDomainError, DomainErrorCode
from .ports import (
    ASSIGNMENT_COLLECTION_KEY,
    ASSIGNMENT_RESOURCE_TYPE,
    COLLECTION_KEYS,
    EMPLOYEE_COLLECTION_KEY,
    EMPLOYEE_RESOURCE_TYPE,
    AssignmentRepository,
    EmployeeRepository,
    ResourceProjectionRepository,
)
from .values import (
    ASSIGNMENT_ROLES,
    ASSIGNMENT_STATUSES,
    ASSIGNMENT_TRANSITIONS,
    EMPLOYEE_STATUSES,
    EMPLOYEE_TRANSITIONS,
    assignment_can_transition,
    employee_can_transition,
    is_assignment_role,
    is_assignment_status,
    is_employee_status,
    is_valid_employee_no,
)

__all__ = [
    "ASSIGNMENT_COLLECTION_KEY",
    "ASSIGNMENT_RESOURCE_TYPE",
    "ASSIGNMENT_ROLES",
    "ASSIGNMENT_STATUSES",
    "ASSIGNMENT_TRANSITIONS",
    "COLLECTION_KEYS",
    "EMPLOYEE_COLLECTION_KEY",
    "EMPLOYEE_RESOURCE_TYPE",
    "EMPLOYEE_STATUSES",
    "EMPLOYEE_TRANSITIONS",
    "Assignment",
    "AssignmentRepository",
    "CompanyDomainError",
    "DomainErrorCode",
    "Employee",
    "EmployeeRepository",
    "ResourceProjectionRepository",
    "assignment_can_transition",
    "employee_can_transition",
    "is_assignment_role",
    "is_assignment_status",
    "is_employee_status",
    "is_valid_employee_no",
    "validate_assignment_inputs",
    "validate_employee_inputs",
]
