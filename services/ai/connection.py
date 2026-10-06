"""Ephemeral AI connection store (HD-P21-17 §9 / §21 / §29 ; HD-P21-AI-04).

Process-local, memory-only, **per (actor, tenant)**. The raw key never reaches the
database, a log line, an audit row or any accessor: ``AIConnection.api_key()`` is
the only door and it is used solely by the credential resolver.

HD-P21-AI-04: a connection now also binds the *model* the customer explicitly
selected, so provider and model travel together as one execution choice. A local
connection may carry no credential at all (Ollama, or LM Studio with auth off).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

DEFAULT_TTL_SECONDS = 1800  # §9: 30 minutes


@dataclass
class AIConnection:
    connection_id: str
    actor_id: str
    tenant_id: str
    provider_key: str
    model_key: str
    secret_ref: str
    created_at: float
    expires_at: float
    _api_key: str

    def api_key(self) -> str:
        """Return the material. Only the credential resolver may call this."""
        return self._api_key

    def expired(self, *, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) >= self.expires_at

    def describe(self) -> dict[str, object]:
        """Customer/API-safe view: no key, no secret ref."""
        return {
            "connected": not self.expired(),
            "provider": self.provider_key,
            "model": self.model_key,
            "expires_at": self.expires_at,
        }


class AIConnectionStore:
    """One entry per (actor, tenant); never persisted, never shared across actors."""

    def __init__(self, *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = int(ttl_seconds)
        self._by_scope: dict[tuple[str, str], AIConnection] = {}

    def _key(self, actor_id: str, tenant_id: str) -> tuple[str, str]:
        return (str(actor_id), str(tenant_id))

    def put(
        self,
        *,
        actor_id: str,
        tenant_id: str,
        provider_key: str,
        model_key: str,
        api_key: str,
        secret_ref: str,
    ) -> AIConnection:
        now = time.time()
        connection = AIConnection(
            connection_id=str(uuid.uuid4()),
            actor_id=str(actor_id),
            tenant_id=str(tenant_id),
            provider_key=str(provider_key),
            model_key=str(model_key),
            secret_ref=str(secret_ref),
            created_at=now,
            expires_at=now + self._ttl,
            _api_key=api_key,
        )
        self._by_scope[self._key(actor_id, tenant_id)] = connection
        return connection

    def get(self, *, actor_id: str, tenant_id: str) -> AIConnection | None:
        connection = self._by_scope.get(self._key(actor_id, tenant_id))
        if connection is None:
            return None
        if connection.expired():
            # Expiry invalidates immediately; the key is never silently resurrected.
            self._by_scope.pop(self._key(actor_id, tenant_id), None)
            return None
        return connection

    def describe(self, *, actor_id: str, tenant_id: str) -> dict[str, object]:
        connection = self.get(actor_id=actor_id, tenant_id=tenant_id)
        if connection is None:
            return {"connected": False, "provider": None, "model": None, "expires_at": None}
        return connection.describe()

    def clear(self, *, actor_id: str, tenant_id: str) -> bool:
        return self._by_scope.pop(self._key(actor_id, tenant_id), None) is not None

    def ttl_seconds(self) -> int:
        return self._ttl


#: Process-local store. Deliberately not a database object and not a global credential:
#: every read is keyed by the authenticated actor **and** tenant.
connection_store = AIConnectionStore()

__all__ = ["AIConnection", "AIConnectionStore", "DEFAULT_TTL_SECONDS", "connection_store"]
