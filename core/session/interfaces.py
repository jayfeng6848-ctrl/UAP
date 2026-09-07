"""Session contracts.

A session represents an authenticated, device-bound period of access. Sessions
are revocable at any time and expire on their own.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

SESSION_STATUS = ("active", "expired", "revoked")


@dataclass(frozen=True)
class Session:
    id: str
    identity_id: str
    device_id: str
    created_at: datetime
    expires_at: datetime
    status: str = "active"

    def is_valid(self, now: datetime | None = None) -> bool:
        moment = now or datetime.now(timezone.utc)
        return self.status == "active" and self.expires_at > moment


@runtime_checkable
class SessionStore(Protocol):
    def create(self, identity_id: str, device_id: str, ttl_seconds: int) -> Session:
        ...

    def get(self, session_id: str) -> Session | None:
        ...

    def revoke(self, session_id: str) -> None:
        ...

    def revoke_all_for_identity(self, identity_id: str) -> int:
        ...


__all__ = ["SESSION_STATUS", "Session", "SessionStore"]
