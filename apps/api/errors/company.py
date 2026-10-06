"""Company API error mapping (PDL Appendix AG · D-P20A-05 = A).

The frozen Core taxonomy classes and their HTTP statuses live in
``apps/api/error_mapping.py`` and are **reused verbatim** — this module never
changes them. It only answers one question for the Company namespace: which
existing taxonomy class does a Company failure belong to.

``core taxonomy ↛ Company``: a future domain copies this file's shape instead of
touching the Core mapping.
"""

from __future__ import annotations

from fastapi import HTTPException

from apps.api.error_mapping import HTTP_STATUS, translate
from services.company.errors import CompanyError, ErrorCode

#: Company failure code -> frozen taxonomy class (see P20_COMPANY_API_CONTRACT §6).
COMPANY_CLASS: dict[str, str] = {
    # authorization: "you may not" — indistinguishable from "it does not exist"
    ErrorCode.AUTHORIZATION_DENIED: "authorization",
    ErrorCode.RESOURCE_NOT_PROVISIONED: "authorization",
    # validation: request shape / unknown or invisible target (D-P20A-02 = A)
    ErrorCode.INVALID_INPUT: "validation",
    ErrorCode.PAGINATION_INVALID: "validation",
    ErrorCode.EMPLOYEE_NOT_FOUND: "validation",
    ErrorCode.ASSIGNMENT_NOT_FOUND: "validation",
    ErrorCode.SPACE_NOT_FOUND: "validation",
    # conflict: natural keys and lifecycle
    ErrorCode.EMPLOYEE_NO_CONFLICT: "conflict",
    ErrorCode.EMPLOYEE_USER_CONFLICT: "conflict",
    ErrorCode.ASSIGNMENT_CONFLICT: "conflict",
    ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT: "conflict",
    ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT: "conflict",
    ErrorCode.TENANT_NOT_ACTIVE: "conflict",
    ErrorCode.SPACE_NOT_ACTIVE: "conflict",
    # opaque infrastructure outcomes (never detailed to the caller)
    ErrorCode.AUDIT_UNAVAILABLE: "persistence",
    ErrorCode.CONSISTENCY_VIOLATION: "security_boundary",
}


def classify_company(exc: BaseException) -> str:
    """Taxonomy class for a Company failure (unknown codes fail closed)."""
    return COMPANY_CLASS.get(getattr(exc, "code", ""), "internal")


def translate_company(exc: BaseException) -> HTTPException:
    """Company-aware translation; everything else keeps the Core behaviour."""
    if isinstance(exc, CompanyError):
        status, message = HTTP_STATUS[classify_company(exc)]
        return HTTPException(status_code=status, detail=message)
    return translate(exc)


__all__ = ["COMPANY_CLASS", "classify_company", "translate_company"]
