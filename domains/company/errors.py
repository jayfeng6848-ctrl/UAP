"""Company domain errors (pure constants + one exception type).

Domain errors describe **business validity only**. They never carry SQL, a
constraint name, a stack trace or any infrastructure text: the service layer maps
them onto its stable, non-leaking error codes (Appendix AF / implementation
contract §7).
"""

from __future__ import annotations


class DomainErrorCode:
    """Stable domain-level codes (business validity, not authorization)."""

    INVALID_INPUT = "invalid_domain_input"
    INVALID_EMPLOYEE_NO = "invalid_employee_no"
    INVALID_ASSIGNMENT_ROLE = "invalid_assignment_role"
    EMPLOYEE_LIFECYCLE_CONFLICT = "employee_lifecycle_conflict"
    ASSIGNMENT_LIFECYCLE_CONFLICT = "assignment_lifecycle_conflict"
    EMPLOYEE_ALREADY_TERMINATED = "employee_already_terminated"
    ASSIGNMENT_ALREADY_ENDED = "assignment_already_ended"


class CompanyDomainError(ValueError):
    """A business rule was violated. Carries a stable code and a safe message."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}" if message else code)


__all__ = ["CompanyDomainError", "DomainErrorCode"]
