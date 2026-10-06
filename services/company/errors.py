"""Company service error taxonomy (stable codes, non-leaking messages).

Each code maps onto one stable outcome. Nothing here carries SQL, a constraint or
trigger name, a stack trace or an infrastructure message: the caller sees a code,
the operator sees the audit row (implementation contract §7).
"""

from __future__ import annotations

from domains.company import CompanyDomainError, DomainErrorCode


class ErrorCode:
    INVALID_INPUT = "invalid_company_input"
    PAGINATION_INVALID = "company_pagination_invalid"
    EMPLOYEE_NOT_FOUND = "company_employee_not_found"
    EMPLOYEE_NO_CONFLICT = "company_employee_no_conflict"
    EMPLOYEE_USER_CONFLICT = "company_employee_user_conflict"
    EMPLOYEE_LIFECYCLE_CONFLICT = "company_employee_lifecycle_conflict"
    ASSIGNMENT_NOT_FOUND = "company_assignment_not_found"
    ASSIGNMENT_CONFLICT = "company_assignment_conflict"
    ASSIGNMENT_LIFECYCLE_CONFLICT = "company_assignment_lifecycle_conflict"
    TENANT_NOT_ACTIVE = "company_tenant_not_active"
    SPACE_NOT_FOUND = "company_space_not_found"
    SPACE_NOT_ACTIVE = "company_space_not_active"
    AUTHORIZATION_DENIED = "company_authorization_denied"
    RESOURCE_NOT_PROVISIONED = "company_resource_not_provisioned"
    AUDIT_UNAVAILABLE = "company_audit_unavailable"
    CONSISTENCY_VIOLATION = "company_consistency_violation"


class CompanyError(RuntimeError):
    """A company failure with a stable code and a safe message."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}" if message else code)


#: Frozen database constraint name -> stable service code.
CONSTRAINT_CODES: dict[str, str] = {
    "uq_company_employees_no": ErrorCode.EMPLOYEE_NO_CONFLICT,
    "uq_company_employees_user": ErrorCode.EMPLOYEE_USER_CONFLICT,
    "uq_company_assignments_active": ErrorCode.ASSIGNMENT_CONFLICT,
    "ck_company_employees_no": ErrorCode.INVALID_INPUT,
    "ck_company_employees_status": ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT,
    "ck_company_employees_lifecycle": ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT,
    "ck_company_assignments_status": ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT,
    "ck_company_assignments_role": ErrorCode.INVALID_INPUT,
    "ck_company_assignments_lifecycle": ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT,
}

#: Domain code -> service code.
DOMAIN_CODES: dict[str, str] = {
    DomainErrorCode.INVALID_INPUT: ErrorCode.INVALID_INPUT,
    DomainErrorCode.INVALID_EMPLOYEE_NO: ErrorCode.INVALID_INPUT,
    DomainErrorCode.INVALID_ASSIGNMENT_ROLE: ErrorCode.INVALID_INPUT,
    DomainErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT: ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT,
    DomainErrorCode.EMPLOYEE_ALREADY_TERMINATED: ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT,
    DomainErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT: ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT,
    DomainErrorCode.ASSIGNMENT_ALREADY_ENDED: ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT,
}


def map_domain_error(exc: CompanyDomainError) -> CompanyError:
    """Translate a domain error into its stable service code (message preserved)."""
    return CompanyError(
        DOMAIN_CODES.get(exc.code, ErrorCode.INVALID_INPUT), exc.safe_message
    )


def map_integrity_error(exc: BaseException) -> CompanyError:
    """Translate a database integrity violation without echoing database text.

    The constraint name (when the driver exposes one) is mapped to a stable code;
    an unnamed violation is reported as an opaque consistency failure so the
    trigger message, SQL text and any cross-tenant detail can never reach a caller.
    """
    diag = getattr(getattr(exc, "orig", None), "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    if constraint and constraint in CONSTRAINT_CODES:
        return CompanyError(CONSTRAINT_CODES[constraint], "database constraint violated")
    if constraint:
        return CompanyError(ErrorCode.INVALID_INPUT, "database constraint violated")
    return CompanyError(ErrorCode.CONSISTENCY_VIOLATION, "structural consistency violated")


__all__ = [
    "CONSTRAINT_CODES",
    "DOMAIN_CODES",
    "CompanyError",
    "ErrorCode",
    "map_domain_error",
    "map_integrity_error",
]
