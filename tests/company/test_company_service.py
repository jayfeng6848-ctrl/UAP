"""P20 Company service tests: authorization, isolation, audit and use-case behaviour."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from services import company as company_service
from services.authorization import AuthorizationService
from services.company import CompanyError, ErrorCode
from tests.company import company_testkit as kit
from tests.company.company_testkit import audit_rows

pytestmark = pytest.mark.integration

FORBIDDEN_AUDIT_TEXT = ("select ", "insert ", "password", "traceback", "sqlalchemy")
ALLOWED_AUDIT_METADATA_KEYS = {
    "operation", "employee_no", "employee_id", "space_id", "fields", "from", "to",
    "assignment_role",
}


def _new_no(tag: str) -> str:
    return f"S-{tag}-{uuid.uuid4().hex[:8]}"


def _create_employee(db, world, *, tag: str, tenant_id: str | None = None):
    return company_service.create_employee(
        db,
        actor_id=world["admin_id"],
        tenant_id=tenant_id or world["tenant_a"],
        employee_no=_new_no(tag),
        display_name=f"Employee {tag}",
        title="Engineer",
    )


def test_create_employee_is_authorized_and_audited(runtime_db, company_engine, world) -> None:
    before = len(audit_rows(company_engine, tenant_id=world["tenant_a"]))
    employee = _create_employee(runtime_db, world, tag="create")

    assert employee.status == "active"
    assert employee.tenant_id == world["tenant_a"]
    rows = audit_rows(company_engine, tenant_id=world["tenant_a"], action="company_employee.create")
    assert len(rows) == 1
    assert str(rows[0]["resource_id"]) == employee.id
    assert str(rows[0]["resource_type"]) == "company_employee"
    assert str(rows[0]["result"]) == "success"
    assert len(audit_rows(company_engine, tenant_id=world["tenant_a"])) == before + 1

    metadata = rows[0]["metadata"]
    assert set(metadata) <= ALLOWED_AUDIT_METADATA_KEYS
    text = str(metadata).lower()
    for token in FORBIDDEN_AUDIT_TEXT:
        assert token not in text


def test_create_employee_replay_is_idempotent(runtime_db, company_engine, world) -> None:
    number = _new_no("replay")
    first = company_service.create_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_no=number, display_name="Replay", title=None,
    )
    second = company_service.create_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_no=number, display_name="Replay", title=None,
    )
    assert first.id == second.id
    rows = audit_rows(company_engine, tenant_id=world["tenant_a"], action="company_employee.create")
    assert sum(1 for row in rows if str(row["resource_id"]) == first.id) == 1

    with pytest.raises(CompanyError) as err:
        company_service.create_employee(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            employee_no=number, display_name="Different", title=None,
        )
    assert err.value.code == ErrorCode.EMPLOYEE_NO_CONFLICT


def test_unauthorized_actor_is_denied(runtime_db, world) -> None:
    with pytest.raises(CompanyError) as err:
        company_service.create_employee(
            runtime_db, actor_id=world["plain_id"], tenant_id=world["tenant_a"],
            employee_no=_new_no("deny"), display_name="Denied", title=None,
        )
    assert err.value.code == ErrorCode.AUTHORIZATION_DENIED

    with pytest.raises(CompanyError) as list_err:
        company_service.list_employees(
            runtime_db, actor_id=world["plain_id"], tenant_id=world["tenant_a"]
        )
    assert list_err.value.code == ErrorCode.AUTHORIZATION_DENIED


def test_missing_projection_is_denied(runtime_db, world) -> None:
    """Tenant C has no Company collection resource: the gate denies, never creates."""
    with pytest.raises(CompanyError) as err:
        company_service.create_employee(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_c"],
            employee_no=_new_no("proj"), display_name="No projection", title=None,
        )
    assert err.value.code == ErrorCode.RESOURCE_NOT_PROVISIONED


def test_employee_lifecycle_use_cases(runtime_db, company_engine, world) -> None:
    employee = _create_employee(runtime_db, world, tag="life")
    suspended = company_service.suspend_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_id=employee.id,
    )
    assert suspended.status == "suspended"
    terminated = company_service.terminate_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_id=employee.id,
    )
    assert terminated.status == "terminated" and terminated.terminated_at is not None

    with pytest.raises(CompanyError) as err:
        company_service.suspend_employee(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            employee_id=employee.id,
        )
    assert err.value.code == ErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT

    actions = {
        str(row["action"])
        for row in audit_rows(company_engine, tenant_id=world["tenant_a"])
        if str(row["resource_id"]) == employee.id
    }
    assert actions == {
        "company_employee.create", "company_employee.suspend", "company_employee.terminate"
    }


def test_update_employee_and_list_guard(runtime_db, world) -> None:
    employee = _create_employee(runtime_db, world, tag="upd")
    updated = company_service.update_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_id=employee.id, display_name="Renamed",
    )
    assert updated.display_name == "Renamed"
    assert updated.title == "Engineer"  # COALESCE keeps the previous title

    with pytest.raises(CompanyError) as empty_err:
        company_service.update_employee(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            employee_id=employee.id,
        )
    assert empty_err.value.code == ErrorCode.INVALID_INPUT

    listed = company_service.list_employees(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"], limit=5
    )
    assert any(item.id == employee.id for item in listed)
    assert len(listed) <= 5

    with pytest.raises(CompanyError) as limit_err:
        company_service.list_employees(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"], limit=0
        )
    assert limit_err.value.code == ErrorCode.PAGINATION_INVALID


def test_cross_tenant_employee_access_is_not_found(runtime_db, world) -> None:
    employee = _create_employee(runtime_db, world, tag="xtenant")
    with pytest.raises(CompanyError) as err:
        company_service.get_employee(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_b"],
            employee_id=employee.id,
        )
    assert err.value.code == ErrorCode.EMPLOYEE_NOT_FOUND


def test_assignment_allow_and_cross_tenant_denials(runtime_db, company_engine, world) -> None:
    employee = _create_employee(runtime_db, world, tag="asg")
    assignment = company_service.create_assignment(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_id=employee.id, space_id=world["space_a"], assignment_role="member",
    )
    assert assignment.status == "active" and assignment.employee_id == employee.id
    rows = audit_rows(
        company_engine, tenant_id=world["tenant_a"], action="company_assignment.create"
    )
    assert any(str(row["resource_id"]) == assignment.id for row in rows)

    # employee + space from another tenant -> the space is not in this tenant
    with pytest.raises(CompanyError) as space_err:
        company_service.create_assignment(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            employee_id=employee.id, space_id=world["space_b"],
        )
    assert space_err.value.code == ErrorCode.SPACE_NOT_FOUND

    # employee from tenant A under tenant B -> the employee is invisible
    with pytest.raises(CompanyError) as employee_err:
        company_service.create_assignment(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_b"],
            employee_id=employee.id, space_id=world["space_b"],
        )
    assert employee_err.value.code == ErrorCode.EMPLOYEE_NOT_FOUND

    # employee + assignment across tenants -> the assignment is invisible
    with pytest.raises(CompanyError) as assignment_err:
        company_service.get_assignment(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_b"],
            assignment_id=assignment.id,
        )
    assert assignment_err.value.code == ErrorCode.ASSIGNMENT_NOT_FOUND


def test_assignment_update_end_and_replay(runtime_db, world) -> None:
    employee = _create_employee(runtime_db, world, tag="asg2")
    assignment = company_service.create_assignment(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_id=employee.id, space_id=world["space_a"], assignment_role="member",
    )
    replayed = company_service.create_assignment(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_id=employee.id, space_id=world["space_a"], assignment_role="member",
    )
    assert replayed.id == assignment.id

    with pytest.raises(CompanyError) as conflict:
        company_service.create_assignment(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            employee_id=employee.id, space_id=world["space_a"], assignment_role="lead",
        )
    assert conflict.value.code == ErrorCode.ASSIGNMENT_CONFLICT

    updated = company_service.update_assignment(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        assignment_id=assignment.id, assignment_role="lead",
    )
    assert updated.assignment_role == "lead"

    ended = company_service.end_assignment(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        assignment_id=assignment.id,
    )
    assert ended.status == "ended" and ended.ended_at is not None

    with pytest.raises(CompanyError) as err:
        company_service.update_assignment(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            assignment_id=assignment.id, assignment_role="member",
        )
    assert err.value.code == ErrorCode.ASSIGNMENT_LIFECYCLE_CONFLICT


def test_audit_failure_rolls_the_business_write_back(
    runtime_db, company_engine, world, monkeypatch
) -> None:
    from services.company import use_cases

    number = _new_no("rollback")

    def _boom(*args, **kwargs):
        raise CompanyError(ErrorCode.AUDIT_UNAVAILABLE, "audit write failed")

    monkeypatch.setattr(use_cases, "_audit", _boom)
    with pytest.raises(CompanyError) as err:
        company_service.create_employee(
            runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
            employee_no=number, display_name="Rollback", title=None,
        )
    assert err.value.code == ErrorCode.AUDIT_UNAVAILABLE
    monkeypatch.undo()

    with company_engine.connect() as conn:
        remaining = conn.execute(
            sa.text(
                "SELECT count(*) FROM company_employees WHERE tenant_id = CAST(:t AS uuid)"
                " AND employee_no = :no"
            ),
            {"t": world["tenant_a"], "no": number},
        ).scalar_one()
    assert remaining == 0


def test_no_events_are_produced_and_audit_stays_append_only(company_engine, world) -> None:
    with company_engine.connect() as conn:
        events = conn.execute(sa.text("SELECT count(*) FROM events")).scalar_one()
    assert events == 0


def test_engine_denies_resource_context_mismatch(company_engine, world) -> None:
    """The canonical engine denies a resource reached with another tenant's context."""
    with company_engine.connect() as conn:
        resource_id = conn.execute(
            sa.text(
                "SELECT id FROM resources WHERE tenant_id = CAST(:t AS uuid)"
                " AND resource_type = 'company_employee' AND deleted_at IS NULL"
            ),
            {"t": world["tenant_a"]},
        ).scalar_one()
    decision = AuthorizationService(engine=company_engine).authorize(
        AuthorizationRequest(
            subject=Subject(
                identity_id=world["admin_id"], subject_type="USER",
                actor_id=world["admin_id"],
            ),
            action=Action(name="read", resource_type="company_employee"),
            resource=ResourceRef(
                type="company_employee", id=str(resource_id), tenant_id=world["tenant_a"]
            ),
            tenant_id=world["tenant_b"],
        )
    )
    assert not decision.allowed
