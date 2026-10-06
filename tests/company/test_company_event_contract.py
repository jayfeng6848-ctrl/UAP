"""Batch 1 event contract tests: payload whitelist validator + handler binding."""

from __future__ import annotations

import uuid

import pytest

from services.company.event_contract import (
    ACTOR_TYPE,
    BATCH1_EVENT_TYPES,
    EVENT_EMPLOYEE_CREATED,
    EVENT_EMPLOYEE_SUSPENDED,
    EVENT_EMPLOYEE_TERMINATED,
    EVENT_EMPLOYEE_UPDATED,
    RESOURCE_TYPE,
    SCHEMA_VERSION,
    MalformedEventPayload,
    validate_event_payload,
)
from services.consumer.kernel import EventAllowlist, EventHandlerSpec, production_allowlist


def _created(**overrides) -> dict:
    payload = {
        "resource_type": RESOURCE_TYPE,
        "resource_id": str(uuid.uuid4()),
        "employee_no": "E-001",
        "display_name": "Ada",
        "status": "active",
    }
    payload.update(overrides)
    return payload


def test_frozen_contract_constants() -> None:
    assert SCHEMA_VERSION == 1
    assert RESOURCE_TYPE == "company_employee"
    assert ACTOR_TYPE == "USER"
    assert BATCH1_EVENT_TYPES == (
        "employee.created", "employee.updated", "employee.suspended", "employee.terminated",
    )


def test_valid_payloads_pass_all_four_event_types() -> None:
    resource_id = str(uuid.uuid4())
    validate_event_payload(EVENT_EMPLOYEE_CREATED, 1, _created(resource_id=resource_id))
    validate_event_payload(
        EVENT_EMPLOYEE_UPDATED, 1,
        {"resource_type": RESOURCE_TYPE, "resource_id": resource_id,
         "changed_fields": ["display_name"]},
    )
    validate_event_payload(
        EVENT_EMPLOYEE_SUSPENDED, 1,
        {"resource_type": RESOURCE_TYPE, "resource_id": resource_id,
         "from_status": "active", "to_status": "suspended"},
    )
    validate_event_payload(
        EVENT_EMPLOYEE_TERMINATED, 1,
        {"resource_type": RESOURCE_TYPE, "resource_id": resource_id,
         "from_status": "suspended", "to_status": "terminated",
         "terminated_at": "2026-10-04T12:00:00+00:00"},
    )


@pytest.mark.parametrize(
    "event_type,payload,reason",
    [
        (EVENT_EMPLOYEE_CREATED, {"resource_type": RESOURCE_TYPE}, "missing_field"),
        (EVENT_EMPLOYEE_CREATED, _created(secret_token="x"), "forbidden_field"),
        (EVENT_EMPLOYEE_CREATED, _created(user_id="not-a-uuid"), "invalid_user_id"),
        (EVENT_EMPLOYEE_CREATED, _created(display_name=123), "wrong_type"),
        (EVENT_EMPLOYEE_CREATED, _created(extra="nope"), "unknown_field"),
        (EVENT_EMPLOYEE_CREATED, _created(resource_type="company_assignment"), "wrong_resource_type"),
        (EVENT_EMPLOYEE_CREATED, _created(resource_id="nope"), "invalid_resource_id"),
        (EVENT_EMPLOYEE_CREATED, _created(status="suspended"), "invalid_status"),
        (EVENT_EMPLOYEE_UPDATED, {"resource_type": RESOURCE_TYPE,
                                  "resource_id": str(uuid.uuid4()), "changed_fields": []},
         "invalid_changed_fields"),
        (EVENT_EMPLOYEE_UPDATED, {"resource_type": RESOURCE_TYPE,
                                  "resource_id": str(uuid.uuid4()), "changed_fields": ["status"]},
         "invalid_changed_fields"),
        (EVENT_EMPLOYEE_SUSPENDED, {"resource_type": RESOURCE_TYPE,
                                    "resource_id": str(uuid.uuid4()),
                                    "from_status": "terminated", "to_status": "suspended"},
         "invalid_from_status"),
        (EVENT_EMPLOYEE_TERMINATED, {"resource_type": RESOURCE_TYPE,
                                     "resource_id": str(uuid.uuid4()),
                                     "from_status": "terminated", "to_status": "terminated",
                                     "terminated_at": "2026-10-04T12:00:00+00:00"},
         "invalid_from_status"),
    ],
)
def test_malformed_payloads_are_rejected(event_type, payload, reason) -> None:
    with pytest.raises(MalformedEventPayload) as err:
        validate_event_payload(event_type, 1, payload)
    assert err.value.reason.startswith(reason)


def test_wrong_schema_version_and_unknown_event_type_are_rejected() -> None:
    with pytest.raises(MalformedEventPayload) as version_err:
        validate_event_payload(EVENT_EMPLOYEE_CREATED, 2, _created())
    assert version_err.value.reason == "wrong_schema_version:2"
    with pytest.raises(MalformedEventPayload) as type_err:
        validate_event_payload("employee.deleted", 1, _created())
    assert type_err.value.reason.startswith("unknown_event_type")


def test_payload_is_inspectable_without_database() -> None:
    """The validator is pure: it never touches a session, DB or business state."""
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2] / "services" / "company" / "event_contract.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    roots = {module.split(".")[0] for module in modules}
    assert roots & {"sqlalchemy", "psycopg", "infrastructure", "services"} == set()


def test_handler_binding_is_explicit_and_production_registry_stays_empty() -> None:
    calls: list[str] = []
    spec = EventHandlerSpec(
        event_type=EVENT_EMPLOYEE_CREATED,
        has_producer_evidence=True,
        has_authorization_semantics=True,
        has_acceptance_coverage=True,
        idempotency="schema_guaranteed",
        handler=lambda event: calls.append(event),
    )
    allowlist = EventAllowlist()
    allowlist.register(spec)
    assert spec.handler is not None
    spec.handler("event")          # trusted code calls it directly
    assert calls == ["event"]

    # A spec without a handler is still registerable (frozen eligibility rules)…
    unbound = EventHandlerSpec("employee.updated", True, True, True, "naturally_idempotent")
    assert unbound.handler is None          # …and the worker will mark handler_not_bound

    # …but nothing above ever reaches the production allowlist.
    assert production_allowlist().is_empty is True
    assert production_allowlist().specs == {}
