"""Company domain vocabulary and lifecycle rules (pure — no I/O).

Frozen by PDL Appendix AC / AD (company schema + module decisions) and Appendix AF
(D-P20D-01…11). This module carries **no** persistence import, no infrastructure
import and no authorization logic: the domain only decides whether a business
transition is structurally valid. Whether an actor may perform it is decided by the
canonical AuthorizationService in the service layer.
"""

from __future__ import annotations

import re

#: AD D-P20S-04 — employee lifecycle.
EMPLOYEE_STATUSES: tuple[str, ...] = ("active", "suspended", "terminated")

#: Assignment lifecycle.
ASSIGNMENT_STATUSES: tuple[str, ...] = ("active", "ended")

#: Business assignment role (never an authorization source).
ASSIGNMENT_ROLES: tuple[str, ...] = ("member", "lead")

#: ``terminated`` is terminal: re-hiring creates a new employee row (AF / contract §3).
EMPLOYEE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("suspended", "terminated"),
    "suspended": ("active", "terminated"),
    "terminated": (),
}

#: ``ended`` is terminal: a new assignment row is created instead of re-opening.
ASSIGNMENT_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("ended",),
    "ended": (),
}

#: Mirrors the frozen DB CHECK ``ck_company_employees_no``.
EMPLOYEE_NO_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def is_valid_employee_no(value: object) -> bool:
    """True when ``value`` satisfies the frozen employee-number shape."""
    return isinstance(value, str) and bool(EMPLOYEE_NO_PATTERN.fullmatch(value))


def is_employee_status(value: object) -> bool:
    return isinstance(value, str) and value in EMPLOYEE_STATUSES


def is_assignment_status(value: object) -> bool:
    return isinstance(value, str) and value in ASSIGNMENT_STATUSES


def is_assignment_role(value: object) -> bool:
    return isinstance(value, str) and value in ASSIGNMENT_ROLES


def employee_can_transition(current: str, target: str) -> bool:
    return target in EMPLOYEE_TRANSITIONS.get(current, ())


def assignment_can_transition(current: str, target: str) -> bool:
    return target in ASSIGNMENT_TRANSITIONS.get(current, ())


__all__ = [
    "ASSIGNMENT_ROLES",
    "ASSIGNMENT_STATUSES",
    "ASSIGNMENT_TRANSITIONS",
    "EMPLOYEE_NO_PATTERN",
    "EMPLOYEE_STATUSES",
    "EMPLOYEE_TRANSITIONS",
    "assignment_can_transition",
    "employee_can_transition",
    "is_assignment_role",
    "is_assignment_status",
    "is_employee_status",
    "is_valid_employee_no",
]
