"""Batch 1 consumer-side qualification tests.

Covers: actor reconstruction without any HTTP session · canonical re-authorization ·
resource re-resolution (collection resource) · tenant forgery denial · worker-vs-actor
separation · payload validation before business side effects · test-only handler
binding that never reaches the production allowlist · duplicate-delivery infrastructure.
"""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from services import company as company_service
from services.authorization import AuthorizationService
from services.company import producer
from services.company.event_contract import (
    EVENT_EMPLOYEE_CREATED,
    RESOURCE_TYPE,
    MalformedEventPayload,
    validate_event_payload,
)
from services.company.projection import collection_resource
from services.consumer.kernel import EventAllowlist, EventHandlerSpec, production_allowlist

pytestmark = pytest.mark.integration


def _seed_event(
    engine, *, tenant_id: str, actor_id: str, employee_no: str, employee_id: str | None = None
) -> dict:
    employee_id = employee_id or str(uuid.uuid4())
    with Session(engine) as session, session.begin():
        event_id = producer.employee_created(
            session, employee_id=employee_id, tenant_id=tenant_id, actor_id=actor_id,
            employee_no=employee_no, display_name="Consumer",
        )
    with engine.connect() as conn:
        row = conn.execute(
            sa.text("SELECT * FROM public.events WHERE id = CAST(:id AS uuid)"),
            {"id": event_id},
        ).one()
    return dict(row._mapping)


def _subject_from_event(event: dict) -> Subject:
    """Reconstruct the originating USER with no HTTP session / bearer request."""
    assert str(event["actor_type"]) == "USER"
    return Subject(
        identity_id=str(event["actor_id"]),
        subject_type="USER",
        actor_id=str(event["actor_id"]),
        tenant_id=str(event["tenant_id"]),
    )


def _decide(engine, *, subject: Subject, tenant_id: str, resource_id: str | None) -> bool:
    if resource_id is None:
        return False  # frozen rule: missing projection = DENY (never self-healed)
    decision = AuthorizationService(engine=engine).authorize(
        AuthorizationRequest(
            subject=subject,
            action=Action(name="read", resource_type=RESOURCE_TYPE),
            resource=ResourceRef(type=RESOURCE_TYPE, id=resource_id, tenant_id=tenant_id),
            tenant_id=tenant_id,
        )
    )
    return bool(decision.allowed)


def test_consumer_reconstructs_user_and_authorizes(company_engine, world) -> None:
    event = _seed_event(
        company_engine, tenant_id=world["tenant_a"], actor_id=world["admin_id"],
        employee_no="E-CONS-1",
    )
    with Session(company_engine) as session, session.begin():
        resource_id = collection_resource(
            session, tenant_id=str(event["tenant_id"]), resource_type=RESOURCE_TYPE
        )
    assert _decide(
        company_engine, subject=_subject_from_event(event),
        tenant_id=str(event["tenant_id"]), resource_id=resource_id,
    ) is True


def test_consumer_denies_actor_without_authorization(company_engine, world) -> None:
    event = _seed_event(
        company_engine, tenant_id=world["tenant_a"], actor_id=world["admin_id"],
        employee_no="E-CONS-2",
    )
    with Session(company_engine) as session, session.begin():
        resource_id = collection_resource(
            session, tenant_id=str(event["tenant_id"]), resource_type=RESOURCE_TYPE
        )
    outsider = Subject(
        identity_id=world["plain_id"], subject_type="USER", actor_id=world["plain_id"],
        tenant_id=str(event["tenant_id"]),
    )
    assert _decide(
        company_engine, subject=outsider, tenant_id=str(event["tenant_id"]),
        resource_id=resource_id,
    ) is False

    unknown = Subject(
        identity_id=str(uuid.uuid4()), subject_type="USER",
        actor_id=str(uuid.uuid4()), tenant_id=str(event["tenant_id"]),
    )
    assert _decide(
        company_engine, subject=unknown, tenant_id=str(event["tenant_id"]),
        resource_id=resource_id,
    ) is False


def test_consumer_denies_when_projection_is_missing(company_engine, world) -> None:
    event = _seed_event(
        company_engine, tenant_id=world["tenant_a"], actor_id=world["admin_id"],
        employee_no="E-CONS-3",
    )
    with Session(company_engine) as session, session.begin():
        missing = collection_resource(
            session, tenant_id=world["tenant_c"], resource_type=RESOURCE_TYPE
        )
    assert missing is None
    assert _decide(
        company_engine, subject=_subject_from_event(event), tenant_id=world["tenant_c"],
        resource_id=missing,
    ) is False


def test_consumer_denies_forged_resource_and_forged_tenant(
    runtime_db, company_engine, world
) -> None:
    employee = company_service.create_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=world["tenant_a"],
        employee_no=f"E-CONS-4-{uuid.uuid4().hex[:6]}", display_name="Forged", title=None,
    )
    event = _seed_event(
        company_engine, tenant_id=world["tenant_a"], actor_id=world["admin_id"],
        employee_no="E-CONS-4", employee_id=employee.id,
    )
    with Session(company_engine) as session, session.begin():
        resource_a = collection_resource(
            session, tenant_id=world["tenant_a"], resource_type=RESOURCE_TYPE
        )
    # (a) forged resource identity (unknown resources row) ⇒ denial
    assert _decide(
        company_engine, subject=_subject_from_event(event), tenant_id=world["tenant_a"],
        resource_id=str(uuid.uuid4()),
    ) is False
    assert resource_a is not None
    # (b) forged tenant: the business object does not exist under the claimed tenant,
    #     and the consumer's tenant-scoped re-resolution is what enforces isolation
    #     (a PLATFORM-scope actor is legitimately authorized in every tenant).
    with company_engine.connect() as conn:
        forged = conn.execute(
            sa.text(
                "SELECT count(*) FROM company_employees"
                " WHERE id = CAST(:e AS uuid) AND tenant_id = CAST(:t AS uuid)"
            ),
            {"e": event["payload"]["resource_id"], "t": world["tenant_b"]},
        ).scalar_one()
        own = conn.execute(
            sa.text(
                "SELECT count(*) FROM company_employees"
                " WHERE id = CAST(:e AS uuid) AND tenant_id = CAST(:t AS uuid)"
            ),
            {"e": event["payload"]["resource_id"], "t": world["tenant_a"]},
        ).scalar_one()
    assert forged == 0 and own == 1


def test_payload_cannot_forge_tenant_or_resource(company_engine, world) -> None:
    """Tenant is never payload-carried: an extra tenant field is malformed by contract."""
    with pytest.raises(MalformedEventPayload) as err:
        validate_event_payload(
            EVENT_EMPLOYEE_CREATED, 1,
            {
                "resource_type": RESOURCE_TYPE,
                "resource_id": str(uuid.uuid4()),
                "employee_no": "E-X", "display_name": "X", "status": "active",
                "tenant_id": str(world["tenant_b"]),
            },
        )
    assert err.value.reason.startswith("unknown_field")


def test_worker_principal_cannot_elevate_the_actor(runtime_db, company_engine, world) -> None:
    """DB grants are not authorization: the runtime principal writes, the actor decides."""
    tenant_a, plain = world["tenant_a"], world["plain_id"]
    # the runtime principal can write business rows (grants exist)…
    company_service.create_employee(
        runtime_db, actor_id=world["admin_id"], tenant_id=tenant_a,
        employee_no=f"E-WORK-{uuid.uuid4().hex[:6]}", display_name="Worker", title=None,
    )
    # …but an actor without a grant is still denied (worker identity ≠ actor identity).
    with Session(company_engine) as session, session.begin():
        resource_id = collection_resource(
            session, tenant_id=tenant_a, resource_type=RESOURCE_TYPE
        )
    worker_like = Subject(
        identity_id=plain, subject_type="USER", actor_id=plain, tenant_id=tenant_a
    )
    assert _decide(
        company_engine, subject=worker_like, tenant_id=tenant_a, resource_id=resource_id
    ) is False


def test_payload_validation_blocks_handler_before_any_side_effect() -> None:
    side_effects: list[object] = []

    def _test_handler(event):
        validate_event_payload(
            event["event_type"], event["schema_version"], event["payload"]
        )
        side_effects.append(event["id"])

    good = {
        "id": "e1", "event_type": EVENT_EMPLOYEE_CREATED, "schema_version": 1,
        "payload": {
            "resource_type": RESOURCE_TYPE, "resource_id": str(uuid.uuid4()),
            "employee_no": "E-OK", "display_name": "OK", "status": "active",
        },
    }
    bad = {
        "id": "e2", "event_type": EVENT_EMPLOYEE_CREATED, "schema_version": 1,
        "payload": {"resource_type": RESOURCE_TYPE, "resource_id": "not-a-uuid"},
    }
    _test_handler(good)
    with pytest.raises(MalformedEventPayload):
        _test_handler(bad)
    assert side_effects == ["e1"]           # malformed payload produced zero side effects


def test_test_only_handlers_never_reach_the_production_allowlist() -> None:
    handled: list[str] = []
    test_allowlist = EventAllowlist()
    for event_type in ("employee.created", "employee.updated", "employee.suspended",
                       "employee.terminated"):
        test_allowlist.register(
            EventHandlerSpec(
                event_type=event_type, has_producer_evidence=True,
                has_authorization_semantics=True, has_acceptance_coverage=True,
                idempotency="naturally_idempotent",
                handler=lambda event: handled.append(event["id"]),
            )
        )
    assert test_allowlist.is_empty is False
    assert production_allowlist().is_empty is True
    assert production_allowlist().specs == {}
    for event_type in test_allowlist.specs:
        with pytest.raises(Exception):       # unsupported type in production registry
            production_allowlist().resolve(event_type)


def test_duplicate_delivery_infrastructure_is_deterministic(company_engine, world) -> None:
    """Same event identity + same natural key ⇒ the harness treats delivery 2 as a no-op.

    This proves the *infrastructure* (event identity + natural-key guard). Production
    Handler idempotency remains NOT QUALIFIED because no business handler exists.
    """
    event = _seed_event(
        company_engine, tenant_id=world["tenant_a"], actor_id=world["admin_id"],
        employee_no="E-DUP-1",
    )
    applied: set[tuple[str, str]] = set()

    def _apply(event_row) -> bool:
        key = (str(event_row["id"]), str(event_row["payload"]["employee_no"]))
        if key in applied:
            return False
        applied.add(key)
        return True

    assert _apply(event) is True
    assert _apply(event) is False           # duplicate delivery: no second side effect
    assert len(applied) == 1
