"""P20 Company endpoints (transport only · frozen by PDL Appendix AG).

Call chain (fixed):

    HTTP request → FastAPI router → request validation → authenticate actor
                 → Company use case (authorization → context → domain → write → audit)
                 → response DTO

The handler owns no business rule: it contains no SQL, no ORM, no repository call,
no permission/role check, no tenant lookup, no resource creation and no audit
insert. Tenant scope comes from the **path** (D-P20A-01 = B), the response is an
explicit DTO whitelist (D-P20A-06 = C) and every failure is mapped onto the frozen
taxonomy by the Company namespace mapper (D-P20A-05 = A).
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends, Query, Request

from apps.api.dependencies import bearer_token, get_database
from apps.api.errors.company import translate_company
from apps.api.schemas.company import (
    AssignmentCreateRequest,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdateRequest,
    EmployeeCreateRequest,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdateRequest,
)
from services.company import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    company_report,
    project_capabilities,
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
from services.use_cases import authenticate_actor

router = APIRouter(prefix="/company", tags=["company"])


def _actor(db, request: Request):
    """Authenticated actor from the bearer session (never from the request body)."""
    try:
        return authenticate_actor(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001 - translated, never echoed
        raise translate_company(exc) from exc


def _correlation(request: Request) -> str | None:
    return request.headers.get("x-correlation-id")


def _run(use_case: Callable[..., Any], /, **kwargs: Any) -> Any:
    """Invoke exactly one use case and map any failure onto the frozen taxonomy."""
    try:
        return use_case(**kwargs)
    except Exception as exc:  # noqa: BLE001 - translated, never echoed
        raise translate_company(exc) from exc


# ------------------------------------------------------- P21 capability / reports
# F-2 (PDL AP.2) authorizes extending the Company route manifest; the P20 route
# semantics above are untouched and remain intact.
# NOTE: PDL AP writes this path as ``/tenants/{tenant_id}/company/capabilities``.
# The deployed P20 API namespace is ``/company/tenants/{tenant_id}/...`` (frozen
# Appendix AG manifest), and F-2 requires new routes to obey the frozen P20 route
# semantics — so the endpoint is served under the API namespace and the SPA route
# stays ``/tenants/:tenant_id/company/...``. Recorded as an implementation
# observation in the recordbook.
@router.get("/tenants/{tenant_id}/capabilities")
def read_company_capabilities(
    tenant_id: str, request: Request, db=Depends(get_database)
) -> dict[str, Any]:
    """Capability projection for the authenticated actor (OQ-CUI-01 = A).

    A projection of the existing authorization engine's answer — never a role
    lookup, never a frontend ACL. No role name, permission key internals or policy
    internals are exposed beyond the effective action booleans.
    """
    actor = _actor(db, request)
    try:
        return project_capabilities(db, actor_id=actor.user_id, tenant_id=tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise translate_company(exc) from exc


@router.get("/tenants/{tenant_id}/reports/operational")
def read_company_reports(
    tenant_id: str, request: Request, db=Depends(get_database)
) -> dict[str, Any]:
    """Operational read-only report (OQ-CUI-02 = A). No report table, no analytics."""
    actor = _actor(db, request)
    try:
        return company_report(db, actor_id=actor.user_id, tenant_id=tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise translate_company(exc) from exc


# ------------------------------------------------------------------ employees
@router.post(
    "/tenants/{tenant_id}/employees", status_code=201, response_model=EmployeeResponse
)
def create_company_employee(
    tenant_id: str,
    payload: EmployeeCreateRequest,
    request: Request,
    db=Depends(get_database),
) -> EmployeeResponse:
    actor = _actor(db, request)
    employee = _run(
        create_employee,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_no=payload.employee_no,
        display_name=payload.display_name,
        title=payload.title,
        hired_at=payload.hired_at,
        correlation_id=_correlation(request),
    )
    return EmployeeResponse.from_entity(employee)


@router.get("/tenants/{tenant_id}/employees", response_model=EmployeeListResponse)
def list_company_employees(
    tenant_id: str,
    request: Request,
    status: str | None = Query(None),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    db=Depends(get_database),
) -> EmployeeListResponse:
    actor = _actor(db, request)
    rows = _run(
        list_employees,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        status=status,
        limit=limit,
    )
    items = [EmployeeResponse.from_entity(row) for row in rows]
    return EmployeeListResponse(items=items, count=len(items), limit=limit)


@router.get(
    "/tenants/{tenant_id}/employees/{employee_id}", response_model=EmployeeResponse
)
def read_company_employee(
    tenant_id: str, employee_id: str, request: Request, db=Depends(get_database)
) -> EmployeeResponse:
    actor = _actor(db, request)
    employee = _run(
        get_employee,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
    )
    return EmployeeResponse.from_entity(employee)


@router.patch(
    "/tenants/{tenant_id}/employees/{employee_id}", response_model=EmployeeResponse
)
def update_company_employee(
    tenant_id: str,
    employee_id: str,
    payload: EmployeeUpdateRequest,
    request: Request,
    db=Depends(get_database),
) -> EmployeeResponse:
    actor = _actor(db, request)
    employee = _run(
        update_employee,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        display_name=payload.display_name,
        title=payload.title,
        correlation_id=_correlation(request),
    )
    return EmployeeResponse.from_entity(employee)


@router.post(
    "/tenants/{tenant_id}/employees/{employee_id}/suspend",
    response_model=EmployeeResponse,
)
def suspend_company_employee(
    tenant_id: str, employee_id: str, request: Request, db=Depends(get_database)
) -> EmployeeResponse:
    actor = _actor(db, request)
    employee = _run(
        suspend_employee,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        correlation_id=_correlation(request),
    )
    return EmployeeResponse.from_entity(employee)


@router.post(
    "/tenants/{tenant_id}/employees/{employee_id}/terminate",
    response_model=EmployeeResponse,
)
def terminate_company_employee(
    tenant_id: str, employee_id: str, request: Request, db=Depends(get_database)
) -> EmployeeResponse:
    actor = _actor(db, request)
    employee = _run(
        terminate_employee,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        correlation_id=_correlation(request),
    )
    return EmployeeResponse.from_entity(employee)


# ---------------------------------------------------------------- assignments
@router.post(
    "/tenants/{tenant_id}/assignments", status_code=201, response_model=AssignmentResponse
)
def create_company_assignment(
    tenant_id: str,
    payload: AssignmentCreateRequest,
    request: Request,
    db=Depends(get_database),
) -> AssignmentResponse:
    actor = _actor(db, request)
    assignment = _run(
        create_assignment,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_id=payload.employee_id,
        space_id=payload.space_id,
        assignment_role=payload.assignment_role,
        correlation_id=_correlation(request),
    )
    return AssignmentResponse.from_entity(assignment)


@router.get("/tenants/{tenant_id}/assignments", response_model=AssignmentListResponse)
def list_company_assignments(
    tenant_id: str,
    request: Request,
    employee_id: str | None = Query(None),
    space_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    db=Depends(get_database),
) -> AssignmentListResponse:
    actor = _actor(db, request)
    rows = _run(
        list_assignments,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        space_id=space_id,
        status=status,
        limit=limit,
    )
    items = [AssignmentResponse.from_entity(row) for row in rows]
    return AssignmentListResponse(items=items, count=len(items), limit=limit)


@router.get(
    "/tenants/{tenant_id}/assignments/{assignment_id}", response_model=AssignmentResponse
)
def read_company_assignment(
    tenant_id: str, assignment_id: str, request: Request, db=Depends(get_database)
) -> AssignmentResponse:
    actor = _actor(db, request)
    assignment = _run(
        get_assignment,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        assignment_id=assignment_id,
    )
    return AssignmentResponse.from_entity(assignment)


@router.patch(
    "/tenants/{tenant_id}/assignments/{assignment_id}", response_model=AssignmentResponse
)
def update_company_assignment(
    tenant_id: str,
    assignment_id: str,
    payload: AssignmentUpdateRequest,
    request: Request,
    db=Depends(get_database),
) -> AssignmentResponse:
    actor = _actor(db, request)
    assignment = _run(
        update_assignment,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        assignment_role=payload.assignment_role,
        correlation_id=_correlation(request),
    )
    return AssignmentResponse.from_entity(assignment)


@router.post(
    "/tenants/{tenant_id}/assignments/{assignment_id}/end",
    response_model=AssignmentResponse,
)
def end_company_assignment(
    tenant_id: str, assignment_id: str, request: Request, db=Depends(get_database)
) -> AssignmentResponse:
    actor = _actor(db, request)
    assignment = _run(
        end_assignment,
        db=db,
        actor_id=actor.user_id,
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        correlation_id=_correlation(request),
    )
    return AssignmentResponse.from_entity(assignment)


__all__ = ["router"]
