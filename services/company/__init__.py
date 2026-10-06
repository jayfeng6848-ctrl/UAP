"""Company service layer (orchestration only — no second authorization engine).

Owns use-case orchestration, the transaction boundary, audit coordination and the
collection-resource projection adapter. It publishes no event, exposes no API and
holds no permission logic of its own: every decision comes from
``services.authorization``.
"""

from __future__ import annotations

from .errors import CompanyError, ErrorCode, map_domain_error, map_integrity_error
from .projection import (
    COLLECTION_NATURAL_KEYS,
    backfill_company_collections,
    collection_resource,
    ensure_collection,
    ensure_company_collections,
)
from .repository import (
    AssignmentRepository,
    EmployeeRepository,
    ResourceProjectionRepository,
)
from .capabilities import project_capabilities
from .reports import company_report
from .use_cases import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    company_capability,
    create_assignment,
    create_employee,
    end_assignment,
    get_assignment,
    get_employee,
    list_assignments,
    list_employees,
    suspend_employee,
    terminate_employee,
    update_assignment,
    update_employee,
)

__all__ = [
    "COLLECTION_NATURAL_KEYS",
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "AssignmentRepository",
    "CompanyError",
    "EmployeeRepository",
    "ErrorCode",
    "ResourceProjectionRepository",
    "backfill_company_collections",
    "collection_resource",
    "company_capability",
    "company_report",
    "create_assignment",
    "create_employee",
    "end_assignment",
    "ensure_collection",
    "ensure_company_collections",
    "get_assignment",
    "get_employee",
    "list_assignments",
    "list_employees",
    "map_domain_error",
    "map_integrity_error",
    "project_capabilities",
    "suspend_employee",
    "terminate_employee",
    "update_assignment",
    "update_employee",
]
