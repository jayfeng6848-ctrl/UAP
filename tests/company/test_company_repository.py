"""P20 Company repository tests: tenant-scoped CRUD and constraint mapping."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.company import (
    AssignmentRepository,
    EmployeeRepository,
    ErrorCode,
    ResourceProjectionRepository,
    map_integrity_error,
)
from services.company.projection import ProjectionError

pytestmark = pytest.mark.integration

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def _employee_no(tag: str) -> str:
    return f"R-{tag}-{uuid.uuid4().hex[:8]}"


def test_employee_crud_and_tenant_predicates(company_engine, world) -> None:
    employees = EmployeeRepository()
    tenant_a, tenant_b = world["tenant_a"], world["tenant_b"]
    number = _employee_no("crud")
    with Session(company_engine) as session, session.begin():
        employee_id = employees.insert(
            session, tenant_id=tenant_a, employee_no=number, display_name="Repo A",
            title="Engineer", hired_at=NOW,
        )
        row = employees.get(session, tenant_id=tenant_a, employee_id=employee_id)
        assert row is not None and str(row["employee_no"]) == number
        assert employees.find_by_no(session, tenant_id=tenant_a, employee_no=number) is not None
        assert employees.list(session, tenant_id=tenant_a, limit=10) is not None

        # tenant predicate: the same id is invisible from another tenant
        assert employees.get(session, tenant_id=tenant_b, employee_id=employee_id) is None

        assert employees.update_profile(
            session, tenant_id=tenant_a, employee_id=employee_id,
            display_name="Repo A2", title=None,
        ) == 1
        updated = employees.get(session, tenant_id=tenant_a, employee_id=employee_id)
        assert str(updated["display_name"]) == "Repo A2"
        assert str(updated["title"]) == "Engineer"  # COALESCE keeps the old value

        assert employees.set_status(
            session, tenant_id=tenant_a, employee_id=employee_id, expect="active",
            status="terminated", terminated_at=NOW,
        ) == 1
        # a conditional update with a stale expectation matches no row
        assert employees.set_status(
            session, tenant_id=tenant_a, employee_id=employee_id, expect="active",
            status="suspended", terminated_at=None,
        ) == 0


def test_employee_constraint_mapping(company_engine, world) -> None:
    employees = EmployeeRepository()
    tenant_a = world["tenant_a"]
    number = _employee_no("dup")
    with Session(company_engine) as session, session.begin():
        employees.insert(
            session, tenant_id=tenant_a, employee_no=number, display_name="First",
            title=None, hired_at=None,
        )
        with pytest.raises(IntegrityError) as err:
            session.execute(
                sa.text(
                    "INSERT INTO company_employees (tenant_id, employee_no, display_name,"
                    " status) VALUES (CAST(:t AS uuid), :no, 'Second', 'active')"
                ),
                {"t": tenant_a, "no": number},
            )
        assert map_integrity_error(err.value).code == ErrorCode.EMPLOYEE_NO_CONFLICT


def test_employee_user_uniqueness_mapping(company_engine, world) -> None:
    employees = EmployeeRepository()
    tenant_a = world["tenant_a"]
    with company_engine.begin() as conn:
        user_id = str(
            conn.execute(
                sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                {"e": f"p20-repo-{uuid.uuid4().hex[:8]}@example.invalid"},
            ).scalar_one()
        )
    with Session(company_engine) as session, session.begin():
        first = employees.insert(
            session, tenant_id=tenant_a, employee_no=_employee_no("u1"),
            display_name="U1", title=None, hired_at=None,
        )
        assert employees.bind_user(
            session, tenant_id=tenant_a, employee_id=first, user_id=user_id
        ) == 1
        with pytest.raises(IntegrityError) as err:
            session.execute(
                sa.text(
                    "INSERT INTO company_employees (tenant_id, user_id, employee_no,"
                    " display_name, status)"
                    " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), :no, 'U2', 'active')"
                ),
                {"t": tenant_a, "u": user_id, "no": _employee_no("u2")},
            )
        assert map_integrity_error(err.value).code == ErrorCode.EMPLOYEE_USER_CONFLICT


def test_assignment_crud_and_constraint_mapping(company_engine, world) -> None:
    employees = EmployeeRepository()
    assignments = AssignmentRepository()
    tenant_a, space_a = world["tenant_a"], world["space_a"]
    with Session(company_engine) as session, session.begin():
        employee_id = employees.insert(
            session, tenant_id=tenant_a, employee_no=_employee_no("asg"),
            display_name="Asg", title=None, hired_at=None,
        )
        assignment_id = assignments.insert(
            session, tenant_id=tenant_a, employee_id=employee_id, space_id=space_a,
            assignment_role="member",
        )
        assert assignments.get(
            session, tenant_id=tenant_a, assignment_id=assignment_id
        ) is not None
        assert assignments.find_active(
            session, tenant_id=tenant_a, employee_id=employee_id, space_id=space_a
        ) is not None
        assert assignments.list(session, tenant_id=tenant_a, limit=10)

        with pytest.raises(IntegrityError) as err:
            # the savepoint keeps the surrounding transaction usable after the failure
            with session.begin_nested():
                session.execute(
                    sa.text(
                        "INSERT INTO company_assignments (tenant_id, employee_id, space_id,"
                        " assignment_role, status)"
                        " VALUES (CAST(:t AS uuid), CAST(:e AS uuid), CAST(:s AS uuid),"
                        " 'member', 'active')"
                    ),
                    {"t": tenant_a, "e": employee_id, "s": space_a},
                )
        assert map_integrity_error(err.value).code == ErrorCode.ASSIGNMENT_CONFLICT

        # A distinct employee isolates the role CHECK from the active-uniqueness index.
        other_employee = employees.insert(
            session, tenant_id=tenant_a, employee_no=_employee_no("role"),
            display_name="Role", title=None, hired_at=None,
        )
        with pytest.raises(IntegrityError) as role_err:
            with session.begin_nested():
                session.execute(
                    sa.text(
                        "INSERT INTO company_assignments (tenant_id, employee_id, space_id,"
                        " assignment_role, status)"
                        " VALUES (CAST(:t AS uuid), CAST(:e AS uuid), CAST(:s AS uuid),"
                        " 'owner', 'active')"
                    ),
                    {"t": tenant_a, "e": other_employee, "s": space_a},
                )
        assert map_integrity_error(role_err.value).code == ErrorCode.INVALID_INPUT

        assert assignments.update_role(
            session, tenant_id=tenant_a, assignment_id=assignment_id,
            assignment_role="lead",
        ) == 1
        assert assignments.end(
            session, tenant_id=tenant_a, assignment_id=assignment_id,
            expect="active", ended_at=NOW,
        ) == 1
        ended = assignments.get(session, tenant_id=tenant_a, assignment_id=assignment_id)
        assert str(ended["status"]) == "ended"


def test_projection_repository_is_tenant_scoped(company_engine, world) -> None:
    projections = ResourceProjectionRepository()
    tenant_a, tenant_c = world["tenant_a"], world["tenant_c"]
    with Session(company_engine) as session, session.begin():
        assert projections.collection(
            session, tenant_id=tenant_a, resource_type="company_employee"
        ) is not None
        assert projections.collection(
            session, tenant_id=tenant_c, resource_type="company_employee"
        ) is None
        with pytest.raises(ProjectionError):
            projections.collection(
                session, tenant_id=tenant_a, resource_type="not_a_company_type"
            )
