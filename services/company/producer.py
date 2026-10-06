"""Company event producer (Batch 1 · implementation present · activation disabled).

Implements the frozen Appendix AI contract for the four Employee events **without**
being wired into the production Company path: the use cases in
``services.company.use_cases`` do not call this module, so a normal API request
still produces **zero** event rows (qualification evidence §25 of the
implementation report). A qualification harness (or a future, separately
authorized wiring round) calls these helpers inside the caller-owned transaction.

Transaction rules (AI D-P20E-DES-08):

* every helper takes the existing ``session`` and therefore joins the **same**
  session / DB transaction / logical transaction as the business write and the
  audit row;
* the producer never commits, never rolls back, never opens a connection.

Identity: ``event_id`` comes from ``core.audit.interfaces.new_event_id()`` (the
existing UUIDv7 generator) — **not** from the database default and never from the
employee id.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.audit.interfaces import new_event_id

from .event_contract import (
    ACTOR_TYPE,
    EVENT_EMPLOYEE_CREATED,
    EVENT_EMPLOYEE_SUSPENDED,
    EVENT_EMPLOYEE_TERMINATED,
    EVENT_EMPLOYEE_UPDATED,
    RESOURCE_TYPE,
    SCHEMA_VERSION,
    MalformedEventPayload,
    is_uuid,
    validate_event_payload,
)

_INSERT_SQL = (
    "INSERT INTO public.events (id, occurred_at, event_type, schema_version, tenant_id,"
    " space_id, actor_type, actor_id, subject_type, subject_id, payload, correlation_id,"
    " causation_id, status, attempts)"
    " VALUES (CAST(:id AS uuid), now(), :event_type, :schema_version,"
    " CAST(:tenant AS uuid), NULL, :actor_type, CAST(:actor AS uuid), NULL, NULL,"
    " CAST(:payload AS jsonb), CAST(:corr AS uuid), NULL, 'pending', 0)"
)


def _correlation(value: str | None) -> str | None:
    """Accept only a UUID correlation (the column type); reject anything else."""
    if value is None:
        return None
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise MalformedEventPayload("invalid_correlation_id") from exc
    return str(value)


def emit_employee_event(
    session: Session,
    *,
    event_type: str,
    tenant_id: str,
    actor_id: str,
    payload: Mapping[str, Any],
    correlation_id: str | None = None,
) -> str:
    """Validate one payload and persist one frozen-contract event row.

    Returns the new ``event_id``. Raises :class:`MalformedEventPayload` before any
    write when the payload violates the contract (⇒ ``malformed_payload``).
    """
    validate_event_payload(event_type, SCHEMA_VERSION, payload)
    if not actor_id:
        raise MalformedEventPayload("missing_actor")
    if not is_uuid(actor_id):
        raise MalformedEventPayload("invalid_actor")
    event_id = new_event_id()
    session.execute(
        text(_INSERT_SQL),
        {
            "id": event_id,
            "event_type": event_type,
            "schema_version": SCHEMA_VERSION,
            "tenant": tenant_id,
            "actor_type": ACTOR_TYPE,
            "actor": actor_id,
            "payload": json.dumps(dict(payload)),
            "corr": _correlation(correlation_id),
        },
    )
    return event_id


def _base_payload(resource_id: str) -> dict[str, Any]:
    return {"resource_type": RESOURCE_TYPE, "resource_id": resource_id}


def employee_created(
    session: Session,
    *,
    employee_id: str,
    tenant_id: str,
    actor_id: str,
    employee_no: str,
    display_name: str,
    status: str = "active",
    user_id: str | None = None,
    correlation_id: str | None = None,
) -> str:
    payload = {
        **_base_payload(employee_id),
        "employee_no": employee_no,
        "display_name": display_name,
        "status": status,
    }
    if user_id is not None:
        payload["user_id"] = user_id
    return emit_employee_event(
        session, event_type=EVENT_EMPLOYEE_CREATED, tenant_id=tenant_id, actor_id=actor_id,
        payload=payload, correlation_id=correlation_id,
    )


def employee_updated(
    session: Session,
    *,
    employee_id: str,
    tenant_id: str,
    actor_id: str,
    changed_fields: list[str],
    display_name: str | None = None,
    title: str | None = None,
    correlation_id: str | None = None,
) -> str:
    payload = {**_base_payload(employee_id), "changed_fields": list(changed_fields)}
    if display_name is not None:
        payload["display_name"] = display_name
    if title is not None:
        payload["title"] = title
    return emit_employee_event(
        session, event_type=EVENT_EMPLOYEE_UPDATED, tenant_id=tenant_id, actor_id=actor_id,
        payload=payload, correlation_id=correlation_id,
    )


def employee_suspended(
    session: Session,
    *,
    employee_id: str,
    tenant_id: str,
    actor_id: str,
    from_status: str = "active",
    to_status: str = "suspended",
    correlation_id: str | None = None,
) -> str:
    payload = {
        **_base_payload(employee_id),
        "from_status": from_status,
        "to_status": to_status,
    }
    return emit_employee_event(
        session, event_type=EVENT_EMPLOYEE_SUSPENDED, tenant_id=tenant_id, actor_id=actor_id,
        payload=payload, correlation_id=correlation_id,
    )


def employee_terminated(
    session: Session,
    *,
    employee_id: str,
    tenant_id: str,
    actor_id: str,
    from_status: str,
    terminated_at: datetime | str,
    to_status: str = "terminated",
    correlation_id: str | None = None,
) -> str:
    stamp = terminated_at.isoformat() if isinstance(terminated_at, datetime) else terminated_at
    payload = {
        **_base_payload(employee_id),
        "from_status": from_status,
        "to_status": to_status,
        "terminated_at": stamp,
    }
    return emit_employee_event(
        session, event_type=EVENT_EMPLOYEE_TERMINATED, tenant_id=tenant_id, actor_id=actor_id,
        payload=payload, correlation_id=correlation_id,
    )


__all__ = [
    "emit_employee_event",
    "employee_created",
    "employee_suspended",
    "employee_terminated",
    "employee_updated",
]
