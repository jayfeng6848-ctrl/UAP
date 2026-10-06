"""P20 Company use cases (transaction owners).

One use case = one logical transaction with a **fixed** order (implementation
authorization Phase 5):

    1+2  authorization gate  : canonical collection resource resolve → AuthorizationService
                               (a missing projection is a denial; it is never created here)
    3    context validation  : tenant is active (and, for assignments, the space is
                               active and belongs to the same tenant)
    4    domain validation   : invariants and lifecycle transitions (pure domain)
    5    repository write    : tenant-scoped, inside the caller-owned transaction
    6    audit               : append-only ``audit_logs`` row in the same transaction
    7    commit              : owned by ``RuntimeDatabase.transaction``

No event is produced, no second authorization engine exists, and no use case can
skip the gate: every code path below starts with :func:`_authorize`.
"""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.audit.interfaces import new_event_id
from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from domains.company import (
    ASSIGNMENT_RESOURCE_TYPE,
    EMPLOYEE_RESOURCE_TYPE,
    Assignment,
    CompanyDomainError,
    Employee,
    validate_assignment_inputs,
    validate_employee_inputs,
)
from infrastructure.database.runtime import RuntimeDatabase
from services.authorization import AuthorizationRepository, AuthorizationService

from .errors import CompanyError, ErrorCode, map_domain_error, map_integrity_error
from .repository import AssignmentRepository, EmployeeRepository, ResourceProjectionRepository

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

_ACTIVE = "active"
_AUDIT_EMPLOYEE = EMPLOYEE_RESOURCE_TYPE
_AUDIT_ASSIGNMENT = ASSIGNMENT_RESOURCE_TYPE

#: Lifecycle state -> audit verb (the frozen audit vocabulary uses verbs:
#: ``company_employee.suspend`` / ``company_employee.terminate``).
_TRANSITION_VERBS: dict[str, str] = {"suspended": "suspend", "terminated": "terminate"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _correlation(value: str | None) -> str:
    return value or str(uuid.uuid4())


def _limit(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_LIMIT:
        raise CompanyError(
            ErrorCode.PAGINATION_INVALID, f"limit must be an integer in 1..{MAX_LIMIT}"
        )
    return value


@contextmanager
def _errors() -> Iterator[None]:
    """Translate domain / database failures into stable company error codes."""
    try:
        yield
    except CompanyError:
        raise
    except CompanyDomainError as exc:  # business rule violated
        raise map_domain_error(exc) from exc
    except IntegrityError as exc:  # database constraint is the last line of defence
        raise map_integrity_error(exc) from exc


# --------------------------------------------------------------------- gate
def _authorize(
    db: RuntimeDatabase,
    session: Any,
    *,
    actor_id: str,
    tenant_id: str,
    action: str,
    resource_type: str,
) -> None:
    """Canonical authorization for one Company operation (steps 1+2).

    The governed object of a Company operation is the tenant-level collection
    resource (D-P20D-02). A missing projection is a **denial** — it is never
    created on this path (P17-AUTH-Q1) — and the decision always comes from the
    single existing engine.
    """
    resource_id = ResourceProjectionRepository().collection(
        session, tenant_id=tenant_id, resource_type=resource_type
    )
    if resource_id is None:
        raise CompanyError(
            ErrorCode.RESOURCE_NOT_PROVISIONED, "company resource projection is missing"
        )

    service = AuthorizationService(
        engine=db.engine, repository=AuthorizationRepository(db.engine)
    )
    request = AuthorizationRequest(
        subject=Subject(
            identity_id=actor_id,
            subject_type="USER",
            actor_id=actor_id,
            tenant_id=tenant_id,
        ),
        action=Action(name=action, resource_type=resource_type),
        resource=ResourceRef(type=resource_type, id=resource_id, tenant_id=tenant_id),
        tenant_id=tenant_id,
    )
    try:
        decision = service.authorize(request)
    except Exception as exc:  # noqa: BLE001 - fail closed, never leak the cause
        raise CompanyError(ErrorCode.AUTHORIZATION_DENIED, "authorization unavailable") from exc
    if not getattr(decision, "allowed", False):
        raise CompanyError(ErrorCode.AUTHORIZATION_DENIED, "authorization denied")


def company_capability(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    action: str,
    resource_type: str,
) -> bool:
    """Public capability read (OQ-CUI-01 = A · PDL Appendix AP).

    It runs the **same** ``_authorize`` gate the Company mutation use cases run and
    turns the frozen denial into a boolean. There is deliberately no second
    evaluator: the capability projection is the existing engine's own answer.
    """
    with db.transaction() as session:
        try:
            _authorize(
                db,
                session,
                actor_id=actor_id,
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
            )
        except CompanyError:
            return False
    return True


def _require_active_tenant(session: Any, tenant_id: str) -> None:
    row = session.execute(
        text("SELECT status FROM tenants WHERE id = CAST(:t AS uuid)"),
        {"t": tenant_id},
    ).one_or_none()
    if row is None or str(row[0]) != _ACTIVE:
        raise CompanyError(ErrorCode.TENANT_NOT_ACTIVE, "tenant is not active")


def _require_active_space(session: Any, *, tenant_id: str, space_id: str) -> None:
    row = session.execute(
        text(
            "SELECT status FROM spaces WHERE id = CAST(:s AS uuid)"
            " AND tenant_id = CAST(:t AS uuid)"
        ),
        {"s": space_id, "t": tenant_id},
    ).one_or_none()
    if row is None:
        raise CompanyError(ErrorCode.SPACE_NOT_FOUND, "space not found in this tenant")
    if str(row[0]) != _ACTIVE:
        raise CompanyError(ErrorCode.SPACE_NOT_ACTIVE, "space is not active")


# -------------------------------------------------------------------- audit
def _audit(
    session: Any,
    *,
    action: str,
    actor_id: str,
    tenant_id: str,
    space_id: str | None,
    resource_type: str,
    resource_id: str | None,
    correlation_id: str,
    facts: dict[str, Any],
    risk_level: str = "LOW",
) -> None:
    """Append one audit fact inside the caller's transaction (append-only)."""
    try:
        session.execute(
            text(
                "INSERT INTO audit_logs (id, occurred_at, tenant_id, space_id, actor_type,"
                " actor_id, action, resource_type, resource_id, result, risk_level,"
                " correlation_id, metadata, created_at)"
                " VALUES (CAST(:id AS uuid), now(), CAST(:tenant AS uuid),"
                " CAST(:space AS uuid), 'user', CAST(:actor AS uuid), :action, :rtype,"
                " CAST(:rid AS uuid), 'success', :risk, CAST(:corr AS uuid),"
                " CAST(:meta AS jsonb), now())"
            ),
            {
                "id": new_event_id(),
                "tenant": tenant_id,
                "space": space_id,
                "actor": actor_id,
                "action": action,
                "rtype": resource_type,
                "rid": resource_id,
                "risk": risk_level,
                "corr": correlation_id,
                "meta": json.dumps(facts),
            },
        )
    except SQLAlchemyError as exc:
        raise CompanyError(ErrorCode.AUDIT_UNAVAILABLE, "audit write failed") from exc


# ---------------------------------------------------------------- employees
def create_employee(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_no: str,
    display_name: str,
    title: str | None = None,
    hired_at: datetime | None = None,
    correlation_id: str | None = None,
) -> Employee:
    """Create one employee (idempotent on an exact replay)."""
    correlation = _correlation(correlation_id)
    employees = EmployeeRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="create", resource_type=EMPLOYEE_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        number, name, clean_title = validate_employee_inputs(
            employee_no=employee_no, display_name=display_name, title=title
        )
        existing = employees.find_by_no(session, tenant_id=tenant_id, employee_no=number)
        if existing is not None:
            if str(existing["display_name"]) == name and (
                existing.get("title") or None
            ) == (clean_title or None):
                return Employee.from_row(existing)
            raise CompanyError(
                ErrorCode.EMPLOYEE_NO_CONFLICT, "employee number already exists"
            )
        employee_id = employees.insert(
            session, tenant_id=tenant_id, employee_no=number, display_name=name,
            title=clean_title, hired_at=hired_at,
        )
        _audit(
            session, action="company_employee.create", actor_id=actor_id,
            tenant_id=tenant_id, space_id=None, resource_type=_AUDIT_EMPLOYEE,
            resource_id=employee_id, correlation_id=correlation,
            facts={"operation": "employee.create", "employee_no": number},
        )
        row = employees.get(session, tenant_id=tenant_id, employee_id=employee_id)
        return Employee.from_row(row)


def get_employee(
    db: RuntimeDatabase, *, actor_id: str, tenant_id: str, employee_id: str
) -> Employee:
    employees = EmployeeRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="read", resource_type=EMPLOYEE_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        row = employees.get(session, tenant_id=tenant_id, employee_id=employee_id)
        if row is None:
            raise CompanyError(ErrorCode.EMPLOYEE_NOT_FOUND, "employee not found")
        return Employee.from_row(row)


def list_employees(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    status: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[Employee]:
    employees = EmployeeRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="list", resource_type=EMPLOYEE_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        rows = employees.list(
            session, tenant_id=tenant_id, status=status, limit=_limit(limit)
        )
        return [Employee.from_row(row) for row in rows]


def update_employee(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_id: str,
    display_name: str | None = None,
    title: str | None = None,
    correlation_id: str | None = None,
) -> Employee:
    """Update the mutable profile fields (never the tenant, never the number)."""
    correlation = _correlation(correlation_id)
    employees = EmployeeRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="update", resource_type=EMPLOYEE_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        row = employees.get(session, tenant_id=tenant_id, employee_id=employee_id)
        if row is None:
            raise CompanyError(ErrorCode.EMPLOYEE_NOT_FOUND, "employee not found")
        current = Employee.from_row(row)
        if display_name is None and title is None:
            raise CompanyError(ErrorCode.INVALID_INPUT, "no updatable field supplied")
        clean_name = (
            validate_employee_inputs(
                employee_no=current.employee_no, display_name=display_name
            )[1]
            if display_name is not None
            else None
        )
        changed = [f for f, v in (("display_name", display_name), ("title", title)) if v is not None]
        rowcount = employees.update_profile(
            session, tenant_id=tenant_id, employee_id=employee_id,
            display_name=clean_name, title=title,
        )
        if rowcount != 1:
            raise CompanyError(ErrorCode.EMPLOYEE_NOT_FOUND, "employee not found")
        _audit(
            session, action="company_employee.update", actor_id=actor_id,
            tenant_id=tenant_id, space_id=None, resource_type=_AUDIT_EMPLOYEE,
            resource_id=employee_id, correlation_id=correlation,
            facts={"operation": "employee.update", "fields": changed},
        )
        updated = employees.get(session, tenant_id=tenant_id, employee_id=employee_id)
        return Employee.from_row(updated)


def _transition_employee(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_id: str,
    target: str,
    correlation_id: str | None,
) -> Employee:
    correlation = _correlation(correlation_id)
    employees = EmployeeRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="update", resource_type=EMPLOYEE_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        row = employees.get(session, tenant_id=tenant_id, employee_id=employee_id)
        if row is None:
            raise CompanyError(ErrorCode.EMPLOYEE_NOT_FOUND, "employee not found")
        current = Employee.from_row(row)
        updated = current.transition_to(target, at=_now())
        rowcount = employees.set_status(
            session, tenant_id=tenant_id, employee_id=employee_id,
            expect=current.status, status=updated.status,
            terminated_at=updated.terminated_at,
        )
        if rowcount != 1:
            raise CompanyError(
                ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT, "state changed concurrently"
            )
        verb = _TRANSITION_VERBS[target]
        _audit(
            session, action=f"company_employee.{verb}", actor_id=actor_id,
            tenant_id=tenant_id, space_id=None, resource_type=_AUDIT_EMPLOYEE,
            resource_id=employee_id, correlation_id=correlation,
            risk_level="MEDIUM",
            facts={"operation": f"employee.{verb}", "from": current.status, "to": target},
        )
        fresh = employees.get(session, tenant_id=tenant_id, employee_id=employee_id)
        return Employee.from_row(fresh)


def suspend_employee(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_id: str,
    correlation_id: str | None = None,
) -> Employee:
    return _transition_employee(
        db, actor_id=actor_id, tenant_id=tenant_id, employee_id=employee_id,
        target="suspended", correlation_id=correlation_id,
    )


def terminate_employee(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_id: str,
    correlation_id: str | None = None,
) -> Employee:
    return _transition_employee(
        db, actor_id=actor_id, tenant_id=tenant_id, employee_id=employee_id,
        target="terminated", correlation_id=correlation_id,
    )


# -------------------------------------------------------------- assignments
def create_assignment(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_id: str,
    space_id: str,
    assignment_role: str = "member",
    correlation_id: str | None = None,
) -> Assignment:
    """Create one assignment (idempotent on an exact replay)."""
    correlation = _correlation(correlation_id)
    employees = EmployeeRepository()
    assignments = AssignmentRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="create", resource_type=ASSIGNMENT_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        _require_active_space(session, tenant_id=tenant_id, space_id=space_id)
        if employees.get(session, tenant_id=tenant_id, employee_id=employee_id) is None:
            raise CompanyError(ErrorCode.EMPLOYEE_NOT_FOUND, "employee not found")
        role = validate_assignment_inputs(assignment_role=assignment_role)
        existing = assignments.find_active(
            session, tenant_id=tenant_id, employee_id=employee_id, space_id=space_id
        )
        if existing is not None:
            if str(existing["assignment_role"]) == role:
                return Assignment.from_row(existing)
            raise CompanyError(
                ErrorCode.ASSIGNMENT_CONFLICT, "active assignment already exists"
            )
        assignment_id = assignments.insert(
            session, tenant_id=tenant_id, employee_id=employee_id,
            space_id=space_id, assignment_role=role,
        )
        _audit(
            session, action="company_assignment.create", actor_id=actor_id,
            tenant_id=tenant_id, space_id=space_id, resource_type=_AUDIT_ASSIGNMENT,
            resource_id=assignment_id, correlation_id=correlation,
            facts={"operation": "assignment.create", "employee_id": employee_id,
                   "space_id": space_id, "assignment_role": role},
        )
        row = assignments.get(
            session, tenant_id=tenant_id, assignment_id=assignment_id
        )
        return Assignment.from_row(row)


def get_assignment(
    db: RuntimeDatabase, *, actor_id: str, tenant_id: str, assignment_id: str
) -> Assignment:
    assignments = AssignmentRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="read", resource_type=ASSIGNMENT_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        row = assignments.get(session, tenant_id=tenant_id, assignment_id=assignment_id)
        if row is None:
            raise CompanyError(ErrorCode.ASSIGNMENT_NOT_FOUND, "assignment not found")
        return Assignment.from_row(row)


def list_assignments(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    employee_id: str | None = None,
    space_id: str | None = None,
    status: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[Assignment]:
    assignments = AssignmentRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="list", resource_type=ASSIGNMENT_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        rows = assignments.list(
            session, tenant_id=tenant_id, employee_id=employee_id,
            space_id=space_id, status=status, limit=_limit(limit),
        )
        return [Assignment.from_row(row) for row in rows]


def update_assignment(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    assignment_id: str,
    assignment_role: str,
    correlation_id: str | None = None,
) -> Assignment:
    """Change the business role of an active assignment."""
    correlation = _correlation(correlation_id)
    assignments = AssignmentRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="update", resource_type=ASSIGNMENT_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        row = assignments.get(session, tenant_id=tenant_id, assignment_id=assignment_id)
        if row is None:
            raise CompanyError(ErrorCode.ASSIGNMENT_NOT_FOUND, "assignment not found")
        current = Assignment.from_row(row)
        if current.status != _ACTIVE:
            raise CompanyError(
                ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT, "ended is terminal"
            )
        role = validate_assignment_inputs(assignment_role=assignment_role)
        rowcount = assignments.update_role(
            session, tenant_id=tenant_id, assignment_id=assignment_id, assignment_role=role
        )
        if rowcount != 1:
            if assignments.get(
                session, tenant_id=tenant_id, assignment_id=assignment_id
            ) is None:
                raise CompanyError(ErrorCode.ASSIGNMENT_NOT_FOUND, "assignment not found")
            raise CompanyError(
                ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT, "state changed concurrently"
            )
        _audit(
            session, action="company_assignment.update", actor_id=actor_id,
            tenant_id=tenant_id, space_id=current.space_id,
            resource_type=_AUDIT_ASSIGNMENT, resource_id=assignment_id,
            correlation_id=correlation,
            facts={"operation": "assignment.update", "assignment_role": role},
        )
        updated = assignments.get(
            session, tenant_id=tenant_id, assignment_id=assignment_id
        )
        return Assignment.from_row(updated)


def end_assignment(
    db: RuntimeDatabase,
    *,
    actor_id: str,
    tenant_id: str,
    assignment_id: str,
    correlation_id: str | None = None,
) -> Assignment:
    """End an active assignment (``ended`` is terminal; no physical delete)."""
    correlation = _correlation(correlation_id)
    assignments = AssignmentRepository()
    with _errors(), db.transaction() as session:
        _authorize(
            db, session, actor_id=actor_id, tenant_id=tenant_id,
            action="update", resource_type=ASSIGNMENT_RESOURCE_TYPE,
        )
        _require_active_tenant(session, tenant_id)
        row = assignments.get(session, tenant_id=tenant_id, assignment_id=assignment_id)
        if row is None:
            raise CompanyError(ErrorCode.ASSIGNMENT_NOT_FOUND, "assignment not found")
        current = Assignment.from_row(row)
        ended = current.end(at=_now())
        rowcount = assignments.end(
            session, tenant_id=tenant_id, assignment_id=assignment_id,
            expect=current.status, ended_at=ended.ended_at,
        )
        if rowcount != 1:
            raise CompanyError(
                ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT, "state changed concurrently"
            )
        _audit(
            session, action="company_assignment.end", actor_id=actor_id,
            tenant_id=tenant_id, space_id=current.space_id,
            resource_type=_AUDIT_ASSIGNMENT, resource_id=assignment_id,
            correlation_id=correlation, risk_level="MEDIUM",
            facts={"operation": "assignment.end", "from": current.status, "to": "ended"},
        )
        fresh = assignments.get(session, tenant_id=tenant_id, assignment_id=assignment_id)
        return Assignment.from_row(fresh)


__all__ = [
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "create_assignment",
    "create_employee",
    "end_assignment",
    "get_assignment",
    "get_employee",
    "list_assignments",
    "list_employees",
    "suspend_employee",
    "terminate_employee",
    "update_assignment",
    "update_employee",
]
