"""Audit writer for Wave 2 security events (AUTH-W2-03 = A).

Writes to the existing ``audit_logs`` table through the already-granted
``INSERT`` privilege. The table is append-only for the runtime (no UPDATE / no
DELETE) and the payload is whitelisted so no credential material can reach it
(SEC-W2-02 / §四十四).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.runtime.errors import PersistenceError

#: Only these keys may be persisted in ``metadata`` (no secrets, ever).
METADATA_WHITELIST = frozenset(
    {
        "reason",
        "outcome",
        "identity_id",
        "device_id",
        "session_id",
        "tenant_id",
        "space_id",
        "sessions_revoked",
        "credentials_revoked",
        "assurance",
        "channel",
    }
)

RESULTS = ("success", "denied", "error")
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class AuditWriter:
    """Append audit rows inside the caller's transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        action: str,
        actor_type: str = "user",
        actor_id: str | None = None,
        result: str = "success",
        risk_level: str = "LOW",
        tenant_id: str | None = None,
        space_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if result not in RESULTS:
            raise ValueError(f"invalid audit result {result!r}")
        if risk_level not in RISK_LEVELS:
            raise ValueError(f"invalid audit risk level {risk_level!r}")
        payload = {
            key: value
            for key, value in (metadata or {}).items()
            if key in METADATA_WHITELIST and value is not None
        }
        audit_id = str(uuid.uuid4())
        try:
            self._session.execute(
                text(
                    "INSERT INTO public.audit_logs"
                    " (id, occurred_at, tenant_id, space_id, actor_type, actor_id, action,"
                    "  resource_type, resource_id, result, risk_level, correlation_id,"
                    "  request_id, metadata, created_at)"
                    " VALUES (CAST(:id AS uuid), now(), CAST(:tenant AS uuid),"
                    "  CAST(:space AS uuid), :actor_type, CAST(:actor AS uuid), :action,"
                    "  :resource_type, CAST(:resource AS uuid), :result, :risk,"
                    "  :correlation, :request, CAST(:metadata AS jsonb), now())"
                ),
                {
                    "id": audit_id,
                    "tenant": tenant_id,
                    "space": space_id,
                    "actor_type": actor_type,
                    "actor": actor_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource": resource_id,
                    "result": result,
                    "risk": risk_level,
                    "correlation": correlation_id,
                    "request": request_id,
                    "metadata": json.dumps(payload),
                },
            )
        except SQLAlchemyError as exc:
            line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
            raise PersistenceError(line[:200]) from exc
        return audit_id


__all__ = ["METADATA_WHITELIST", "RESULTS", "RISK_LEVELS", "AuditWriter"]
