"""Operational read-only Company reports (OQ-CUI-02 = A · PDL Appendix AP).

Every number is derived from existing Company data through an **authorized** query:
the caller is authorized on the tenant-level collection resources first (the single
existing engine, no second evaluator), then explicit tenant-scoped aggregates run.

There is no report table, no analytics schema and no warehouse. Space-level employee
counts are **assignment-derived** (F-3): ``company_employees`` gains no ``space_id``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from domains.company import ASSIGNMENT_RESOURCE_TYPE, EMPLOYEE_RESOURCE_TYPE
from infrastructure.database.runtime import RuntimeDatabase

from .errors import CompanyError, ErrorCode
from .use_cases import company_capability

_READ_ACTIONS = (
    # Canonical engine shape: (verb, resource_type) — see services.company.capabilities.
    ("read", EMPLOYEE_RESOURCE_TYPE),
    ("read", ASSIGNMENT_RESOURCE_TYPE),
)


def _require_report_access(db: RuntimeDatabase, *, actor_id: str, tenant_id: str) -> None:
    """Reports obey Tenant + Authorization + Scope + Resource (same gate as reads)."""
    for action, resource_type in _READ_ACTIONS:
        if not company_capability(
            db, actor_id=actor_id, tenant_id=tenant_id, action=action, resource_type=resource_type
        ):
            raise CompanyError(ErrorCode.AUTHORIZATION_DENIED, "reports access denied")


def _counts(session: Any, sql: str, **params: Any) -> dict[str, int]:
    return {str(row[0]): int(row[1]) for row in session.execute(text(sql), params).all()}


def company_report(db: RuntimeDatabase, *, actor_id: str, tenant_id: str) -> dict[str, Any]:
    """The six frozen V1 report sections, all tenant-scoped and read-only."""
    _require_report_access(db, actor_id=actor_id, tenant_id=tenant_id)
    with db.transaction() as session:
        employee_lifecycle = _counts(
            session,
            "SELECT status, count(*) FROM company_employees WHERE tenant_id = CAST(:t AS uuid)"
            " GROUP BY status",
            t=tenant_id,
        )
        assignment_summary = _counts(
            session,
            "SELECT status, count(*) FROM company_assignments WHERE tenant_id = CAST(:t AS uuid)"
            " GROUP BY status",
            t=tenant_id,
        )
        unassigned = session.execute(
            text(
                "SELECT count(*) FROM company_employees e WHERE e.tenant_id = CAST(:t AS uuid)"
                " AND e.status <> 'terminated' AND NOT EXISTS ("
                "   SELECT 1 FROM company_assignments a WHERE a.employee_id = e.id"
                "   AND a.status = 'active')"
            ),
            {"t": tenant_id},
        ).scalar_one()
        space_employee_counts = _counts(
            session,
            # F-3: the employee↔space relation is expressed ONLY through assignments.
            "SELECT space_id, count(DISTINCT employee_id) FROM company_assignments"
            " WHERE tenant_id = CAST(:t AS uuid) AND status = 'active' GROUP BY space_id",
            t=tenant_id,
        )
        space_assignment_counts = _counts(
            session,
            "SELECT space_id, count(*) FROM company_assignments"
            " WHERE tenant_id = CAST(:t AS uuid) AND status = 'active' GROUP BY space_id",
            t=tenant_id,
        )
    headcount = sum(employee_lifecycle.values())
    return {
        "headcount": headcount,
        "employee_lifecycle": employee_lifecycle,
        "assignment_summary": assignment_summary,
        "unassigned_employees": int(unassigned),
        "space_employee_counts": space_employee_counts,
        "space_assignment_counts": space_assignment_counts,
    }


__all__ = ["company_report"]
