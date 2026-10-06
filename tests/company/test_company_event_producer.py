"""Batch 1 producer tests: envelope mapping, transaction atomicity, event silence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from services import company as company_service
from services.company import producer
from services.company.event_contract import MalformedEventPayload
from services.consumer.kernel import production_allowlist

pytestmark = pytest.mark.integration

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


def _events_for(engine, tenant_id: str, event_type: str | None = None) -> list[dict]:
    sql = (
        "SELECT id, occurred_at, event_type, schema_version, tenant_id, space_id, actor_type,"
        " actor_id, subject_type, subject_id, payload, correlation_id, causation_id, status,"
        " attempts FROM public.events WHERE tenant_id = CAST(:t AS uuid)"
    )
    params: dict[str, object] = {"t": tenant_id}
    if event_type is not None:
        sql += " AND event_type = :event_type"
        params["event_type"] = event_type
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


# --------------------------------------------------------------- envelope mapping
def test_producer_writes_the_frozen_envelope(company_engine, world) -> None:
    tenant_a, admin = world["tenant_a"], world["admin_id"]
    correlation = str(uuid.uuid4())
    employee_id = str(uuid.uuid4())
    with Session(company_engine) as session, session.begin():
        event_id = producer.employee_created(
            session, employee_id=employee_id, tenant_id=tenant_a, actor_id=admin,
            employee_no="E-PROD-1", display_name="Producer", correlation_id=correlation,
        )
    rows = _events_for(company_engine, tenant_a, "employee.created")
    assert len(rows) == 1
    row = rows[0]
    assert str(row["id"]) == event_id and event_id != employee_id
    assert int(row["schema_version"]) == 1
    assert str(row["tenant_id"]) == str(tenant_a)
    assert row["space_id"] is None
    assert str(row["actor_type"]) == "USER"
    assert str(row["actor_id"]) == str(admin)
    assert row["subject_type"] is None and row["subject_id"] is None
    assert row["causation_id"] is None
    assert str(row["correlation_id"]) == correlation
    assert str(row["status"]) == "pending" and int(row["attempts"]) == 0
    assert row["payload"]["resource_type"] == "company_employee"
    assert row["payload"]["resource_id"] == employee_id
    assert set(row["payload"]) == {
        "resource_type", "resource_id", "employee_no", "display_name", "status"
    }


def test_producer_supports_all_four_employee_events(company_engine, world) -> None:
    tenant_a, admin = world["tenant_a"], world["admin_id"]
    employee_id = str(uuid.uuid4())
    with Session(company_engine) as session, session.begin():
        producer.employee_created(
            session, employee_id=employee_id, tenant_id=tenant_a, actor_id=admin,
            employee_no="E-PROD-2", display_name="All",
        )
        producer.employee_updated(
            session, employee_id=employee_id, tenant_id=tenant_a, actor_id=admin,
            changed_fields=["display_name"], display_name="Renamed",
        )
        producer.employee_suspended(
            session, employee_id=employee_id, tenant_id=tenant_a, actor_id=admin
        )
        producer.employee_terminated(
            session, employee_id=employee_id, tenant_id=tenant_a, actor_id=admin,
            from_status="suspended", terminated_at=NOW,
        )
    written = {
        str(row["event_type"]) for row in _events_for(company_engine, tenant_a)
    }
    assert written == {
        "employee.created", "employee.updated", "employee.suspended", "employee.terminated",
    }
    terminated = _events_for(company_engine, tenant_a, "employee.terminated")[0]
    assert terminated["payload"]["to_status"] == "terminated"
    assert terminated["payload"]["terminated_at"].startswith("2026-10-04")


def test_producer_rejects_malformed_payload_before_writing(company_engine, world) -> None:
    tenant_a, admin = world["tenant_a"], world["admin_id"]
    before = len(_events_for(company_engine, tenant_a))
    with Session(company_engine) as session, session.begin():
        with pytest.raises(MalformedEventPayload):
            producer.emit_employee_event(
                session, event_type="employee.created", tenant_id=tenant_a, actor_id=admin,
                payload={"resource_type": "company_employee"},  # missing required fields
            )
    assert len(_events_for(company_engine, tenant_a)) == before


def test_producer_rejects_missing_or_invalid_actor(company_engine, world) -> None:
    tenant_a, admin = world["tenant_a"], world["admin_id"]
    before = len(_events_for(company_engine, tenant_a, "employee.created"))
    with Session(company_engine) as session, session.begin():
        with pytest.raises(MalformedEventPayload):
            producer.employee_created(
                session, employee_id=str(uuid.uuid4()), tenant_id=tenant_a, actor_id="",
                employee_no="E-ACT", display_name="No actor",
            )
    assert len(_events_for(company_engine, tenant_a, "employee.created")) == before


# ------------------------------------------------------------ atomicity harness
def _wired_create(db, *, tenant_id: str, actor_id: str, employee_no: str) -> str:
    """Mirror the future producer wiring: business + audit + event in one transaction."""
    from services.company.repository import EmployeeRepository
    from services.company.use_cases import _audit  # the real audit writer

    with db.transaction() as session:
        employee_id = EmployeeRepository().insert(
            session, tenant_id=tenant_id, employee_no=employee_no,
            display_name="Wired", title=None, hired_at=None,
        )
        _audit(
            session, action="company_employee.create", actor_id=actor_id,
            tenant_id=tenant_id, space_id=None, resource_type="company_employee",
            resource_id=employee_id, correlation_id=str(uuid.uuid4()),
            facts={"operation": "employee.create", "employee_no": employee_no},
        )
        producer.employee_created(
            session, employee_id=employee_id, tenant_id=tenant_id, actor_id=actor_id,
            employee_no=employee_no, display_name="Wired",
        )
    return employee_id


def test_atomic_success_commits_business_audit_and_event(runtime_db, company_engine, world) -> None:
    tenant_a, admin = world["tenant_a"], world["admin_id"]
    number = f"E-ATOM-{uuid.uuid4().hex[:6]}"
    employee_id = _wired_create(runtime_db, tenant_id=tenant_a, actor_id=admin, employee_no=number)
    with company_engine.connect() as conn:
        business = conn.execute(
            sa.text("SELECT count(*) FROM company_employees WHERE id = CAST(:e AS uuid)"),
            {"e": employee_id},
        ).scalar_one()
        audit = conn.execute(
            sa.text("SELECT count(*) FROM audit_logs WHERE resource_id = CAST(:e AS uuid)"),
            {"e": employee_id},
        ).scalar_one()
    assert business == 1 and audit == 1
    assert len(_events_for(company_engine, tenant_a, "employee.created")) >= 1


def test_event_failure_rolls_back_business_and_audit(
    runtime_db, company_engine, world, monkeypatch
) -> None:
    tenant_a, admin = world["tenant_a"], world["admin_id"]
    number = f"E-ATOMF-{uuid.uuid4().hex[:6]}"

    def _boom(*args, **kwargs):
        raise MalformedEventPayload("forced_event_failure")

    monkeypatch.setattr(producer, "employee_created", _boom)
    with pytest.raises(MalformedEventPayload):
        _wired_create(runtime_db, tenant_id=tenant_a, actor_id=admin, employee_no=number)
    monkeypatch.undo()

    with company_engine.connect() as conn:
        business = conn.execute(
            sa.text("SELECT count(*) FROM company_employees WHERE employee_no = :no"),
            {"no": number},
        ).scalar_one()
        audit = conn.execute(
            sa.text(
                "SELECT count(*) FROM audit_logs WHERE metadata->>'employee_no' = :no"
            ),
            {"no": number},
        ).scalar_one()
    assert business == 0 and audit == 0


def test_audit_failure_rolls_back_business_and_event(
    runtime_db, company_engine, world, monkeypatch
) -> None:
    from services.company import use_cases
    from services.company.errors import CompanyError, ErrorCode

    tenant_a, admin = world["tenant_a"], world["admin_id"]
    number = f"E-ATOMA-{uuid.uuid4().hex[:6]}"

    def _boom(*args, **kwargs):
        raise CompanyError(ErrorCode.AUDIT_UNAVAILABLE, "forced audit failure")

    monkeypatch.setattr(use_cases, "_audit", _boom)
    with pytest.raises(CompanyError):
        _wired_create(runtime_db, tenant_id=tenant_a, actor_id=admin, employee_no=number)
    monkeypatch.undo()

    with company_engine.connect() as conn:
        business = conn.execute(
            sa.text("SELECT count(*) FROM company_employees WHERE employee_no = :no"),
            {"no": number},
        ).scalar_one()
    assert business == 0
    assert not [
        row for row in _events_for(company_engine, tenant_a, "employee.created")
        if row["payload"].get("employee_no") == number
    ]


# ------------------------------------------------------- production event silence
def test_production_company_path_remains_event_silent(runtime_db, company_engine, world) -> None:
    """The real Company use cases do not emit: no wiring, allowlist stays EMPTY."""
    tenant_a, admin, space_a = world["tenant_a"], world["admin_id"], world["space_a"]
    before = len(_events_for(company_engine, tenant_a))
    employee = company_service.create_employee(
        runtime_db, actor_id=admin, tenant_id=tenant_a,
        employee_no=f"E-SILENT-{uuid.uuid4().hex[:6]}", display_name="Silent", title="T",
    )
    company_service.update_employee(
        runtime_db, actor_id=admin, tenant_id=tenant_a, employee_id=employee.id,
        display_name="Silent 2",
    )
    company_service.suspend_employee(
        runtime_db, actor_id=admin, tenant_id=tenant_a, employee_id=employee.id
    )
    company_service.terminate_employee(
        runtime_db, actor_id=admin, tenant_id=tenant_a, employee_id=employee.id
    )
    company_service.create_assignment(
        runtime_db, actor_id=admin, tenant_id=tenant_a, employee_id=employee.id,
        space_id=space_a, assignment_role="member",
    )
    assert len(_events_for(company_engine, tenant_a)) == before
    assert production_allowlist().is_empty is True
    assert production_allowlist().specs == {}
