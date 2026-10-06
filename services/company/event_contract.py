"""Frozen Batch 1 Employee event contract (PDL Appendix AI) + pure payload validation.

Single source of truth for the four frozen Employee event types, the frozen
``schema_version``, the payload whitelists and the forbidden-field rules. This
module is **pure** (no I/O, no DB, no authorization): it answers exactly one
question — "is this payload contract-valid for this event type?".

It is intentionally *not* a central schema engine (HD-Q-02 forbids one): it is a
small, explicit whitelist table plus one pure function, used by both the Producer
(before persisting) and the Handler boundary (before any business side effect).
"""

from __future__ import annotations

import uuid
from typing import Any, Mapping

#: Frozen event types (Appendix AI · D-P20E-DES-01).
EVENT_EMPLOYEE_CREATED = "employee.created"
EVENT_EMPLOYEE_UPDATED = "employee.updated"
EVENT_EMPLOYEE_SUSPENDED = "employee.suspended"
EVENT_EMPLOYEE_TERMINATED = "employee.terminated"

BATCH1_EVENT_TYPES: tuple[str, ...] = (
    EVENT_EMPLOYEE_CREATED,
    EVENT_EMPLOYEE_UPDATED,
    EVENT_EMPLOYEE_SUSPENDED,
    EVENT_EMPLOYEE_TERMINATED,
)

#: Frozen contract version (Appendix AI · D-P20E-DES-02).
SCHEMA_VERSION = 1

#: Frozen resource identity (Appendix AI · D-P20E-DES-04).
RESOURCE_TYPE = "company_employee"

#: Frozen actor type (Appendix AI · D-P20E-DES-05).
ACTOR_TYPE = "USER"

#: The only mutable employee fields an ``employee.updated`` payload may describe.
UPDATABLE_FIELDS: tuple[str, ...] = ("display_name", "title")

#: Field-name tokens that must never appear in a Batch 1 payload (AI D-P20E-DES-03).
FORBIDDEN_FIELD_TOKENS: frozenset[str] = frozenset(
    {
        "password", "token", "bearer", "api_key", "apikey", "secret", "secret_ref",
        "dsn", "connection_string", "connectionstring", "sql", "stack", "traceback",
        "exception", "credential", "credentials",
    }
)

#: event_type -> (required fields, optional fields)
_PAYLOAD_SHAPE: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    EVENT_EMPLOYEE_CREATED: (
        frozenset({"resource_type", "resource_id", "employee_no", "display_name", "status"}),
        frozenset({"user_id"}),
    ),
    EVENT_EMPLOYEE_UPDATED: (
        frozenset({"resource_type", "resource_id", "changed_fields"}),
        frozenset({"display_name", "title"}),
    ),
    EVENT_EMPLOYEE_SUSPENDED: (
        frozenset({"resource_type", "resource_id", "from_status", "to_status"}),
        frozenset(),
    ),
    EVENT_EMPLOYEE_TERMINATED: (
        frozenset({"resource_type", "resource_id", "from_status", "to_status", "terminated_at"}),
        frozenset(),
    ),
}


class MalformedEventPayload(ValueError):
    """The payload violates the frozen Batch 1 contract (⇒ ``malformed_payload``)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"malformed_event_payload: {reason}")


def is_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _require_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        raise MalformedEventPayload(f"wrong_type:{field}")
    return value


def validate_event_payload(
    event_type: str, schema_version: int, payload: Mapping[str, Any] | None
) -> None:
    """Validate one payload against the frozen contract; raise on violation.

    Checks (in order): event type is frozen · schema_version is frozen · payload is
    a mapping · no unknown field · no forbidden field · all required fields present ·
    per-field types · resource identity (type + uuid) · per-event semantics
    (changed_fields ⊆ updatable fields, lifecycle directions).
    """
    if event_type not in _PAYLOAD_SHAPE:
        raise MalformedEventPayload(f"unknown_event_type:{event_type}")
    if schema_version != SCHEMA_VERSION:
        raise MalformedEventPayload(f"wrong_schema_version:{schema_version}")
    if payload is None or not isinstance(payload, Mapping):
        raise MalformedEventPayload("payload_not_object")

    required, optional = _PAYLOAD_SHAPE[event_type]
    allowed = required | optional

    for key in payload:
        if not isinstance(key, str):
            raise MalformedEventPayload("payload_key_not_string")
        if key in FORBIDDEN_FIELD_TOKENS or any(
            token in key.lower() for token in FORBIDDEN_FIELD_TOKENS
        ):
            raise MalformedEventPayload(f"forbidden_field:{key}")
        if key not in allowed:
            raise MalformedEventPayload(f"unknown_field:{key}")

    for key in sorted(required):
        if key not in payload:
            raise MalformedEventPayload(f"missing_field:{key}")

    resource_type = _require_text(payload, "resource_type")
    if resource_type != RESOURCE_TYPE:
        raise MalformedEventPayload(f"wrong_resource_type:{resource_type}")
    if not is_uuid(payload.get("resource_id")):
        raise MalformedEventPayload("invalid_resource_id")

    if event_type == EVENT_EMPLOYEE_CREATED:
        _require_text(payload, "employee_no")
        _require_text(payload, "display_name")
        if _require_text(payload, "status") != "active":
            raise MalformedEventPayload("invalid_status:created")
        if payload.get("user_id") is not None and not is_uuid(payload.get("user_id")):
            raise MalformedEventPayload("invalid_user_id")

    elif event_type == EVENT_EMPLOYEE_UPDATED:
        changed = payload.get("changed_fields")
        if (
            not isinstance(changed, list)
            or not changed
            or any(not isinstance(item, str) for item in changed)
            or any(item not in UPDATABLE_FIELDS for item in changed)
        ):
            raise MalformedEventPayload("invalid_changed_fields")
        for key in ("display_name", "title"):
            if key in payload and payload[key] is not None and not isinstance(payload[key], str):
                raise MalformedEventPayload(f"wrong_type:{key}")

    elif event_type == EVENT_EMPLOYEE_SUSPENDED:
        if _require_text(payload, "from_status") != "active":
            raise MalformedEventPayload("invalid_from_status:suspended")
        if _require_text(payload, "to_status") != "suspended":
            raise MalformedEventPayload("invalid_to_status:suspended")

    else:  # EVENT_EMPLOYEE_TERMINATED
        if _require_text(payload, "from_status") not in ("active", "suspended"):
            raise MalformedEventPayload("invalid_from_status:terminated")
        if _require_text(payload, "to_status") != "terminated":
            raise MalformedEventPayload("invalid_to_status:terminated")
        _require_text(payload, "terminated_at")


__all__ = [
    "ACTOR_TYPE",
    "BATCH1_EVENT_TYPES",
    "EVENT_EMPLOYEE_CREATED",
    "EVENT_EMPLOYEE_SUSPENDED",
    "EVENT_EMPLOYEE_TERMINATED",
    "EVENT_EMPLOYEE_UPDATED",
    "FORBIDDEN_FIELD_TOKENS",
    "MalformedEventPayload",
    "RESOURCE_TYPE",
    "SCHEMA_VERSION",
    "UPDATABLE_FIELDS",
    "is_uuid",
    "validate_event_payload",
]
