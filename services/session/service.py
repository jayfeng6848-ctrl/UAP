"""Session lifecycle use-cases (Wave 2 §十七 – §二十一, §四十二).

Expiry model (SS-W2-05 = B): the *semantics* are frozen here while the concrete
numbers come from deployment configuration. Both ceilings are always enforced —
a refresh can never push a session past ``absolute_expires_at`` (§二十).

All comparisons use timezone-aware UTC (§二十). The service is session-scoped and
never commits; the use-case owns the transaction.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from services.identity.hashing import hash_token, new_token
from services.identity.repository import IdentityRepository
from services.mapping import (
    DeviceStatus,
    IdentityStatus,
    SessionStatus,
    UserStatus,
    is_authenticatable_device,
    to_persistence_credential_type,
    to_persistence_session_status,
)
from services.mapping import CredentialType

from services.device.repository import DeviceRepository

from .errors import SessionNotUsable, SessionTokenRejected, SessionValidationError
from .repository import SessionRepository

#: Deployment-tunable defaults (semantics frozen, numbers configurable).
DEFAULT_RELATIVE_TTL_SECONDS = 3600
DEFAULT_ABSOLUTE_TTL_SECONDS = 43200


@dataclass(frozen=True)
class IssuedSession:
    """A freshly created session. The bearer token is returned exactly once."""

    session_id: str
    token: str
    user_id: str
    identity_id: str
    device_id: str
    expires_at: datetime
    absolute_expires_at: datetime


@dataclass(frozen=True)
class SessionView:
    """Validated session facts — evidence, never an authority."""

    session_id: str
    user_id: str
    identity_id: str
    device_id: str | None
    expires_at: datetime
    absolute_expires_at: datetime | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_client_ip(value: str | None) -> str | None:
    """Return a valid IP literal or ``None``.

    ``ip_created`` / ``ip_last`` are ``inet`` columns, so a non-IP client
    identifier (proxy header, ASGI test client, hostname) must never reach the
    database. Request metadata must not be able to break authentication, so an
    unparseable value is dropped rather than persisted.
    """
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


class SessionService:
    """Create, validate, refresh and revoke sessions."""

    def __init__(
        self,
        session: Session,
        *,
        relative_ttl_seconds: int = DEFAULT_RELATIVE_TTL_SECONDS,
        absolute_ttl_seconds: int = DEFAULT_ABSOLUTE_TTL_SECONDS,
    ) -> None:
        if relative_ttl_seconds < 1 or absolute_ttl_seconds < relative_ttl_seconds:
            raise SessionValidationError("invalid session TTL configuration")
        self._sessions = SessionRepository(session)
        self._identities = IdentityRepository(session)
        self._devices = DeviceRepository(session)
        self._relative = relative_ttl_seconds
        self._absolute = absolute_ttl_seconds

    # -------------------------------------------------------------------- create
    def create(
        self,
        *,
        user_id: str,
        identity_id: str,
        device_id: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> IssuedSession:
        """Create a session for an authenticated identity + verified device.

        Preconditions (§十七): valid identity (active), an active credential, and
        an ``active`` device. A normal human session **must** carry ``device_id``
        (§十八) — the nullable column is not an invitation to omit it.
        """
        if not device_id:
            raise SessionValidationError("a human session requires a verified device")

        identity = self._identities.get_identity(identity_id)
        if identity is None or str(identity._mapping["user_id"]) != user_id:
            raise SessionNotUsable("identity does not belong to this user")
        if str(identity._mapping["status"]) != IdentityStatus.ACTIVE.value:
            raise SessionNotUsable("identity is not active")

        user = self._identities.get_user(user_id)
        if user is None or str(user._mapping["status"]) not in (
            UserStatus.ACTIVE.value,
            UserStatus.PENDING.value,
        ):
            raise SessionNotUsable("user is not usable")

        credential = self._identities.get_live_credential(
            identity_id, credential_type=to_persistence_credential_type(CredentialType.PASSWORD)
        )
        if credential is None:
            raise SessionNotUsable("no active credential")

        device = self._devices.get_device(device_id)
        if device is None or str(device._mapping["user_id"]) != user_id:
            raise SessionNotUsable("device does not belong to this user")
        if not is_authenticatable_device(str(device._mapping["status"])):
            raise SessionNotUsable("device is not authenticatable")

        now = _now()
        expires_at = now + timedelta(seconds=self._relative)
        absolute_expires_at = now + timedelta(seconds=self._absolute)
        token = new_token()
        session_id = self._sessions.insert_session(
            user_id=user_id,
            identity_id=identity_id,
            device_id=device_id,
            token_hash=hash_token(token),
            refresh_token_hash=None,
            expires_at=expires_at,
            absolute_expires_at=absolute_expires_at,
            ip_created=normalize_client_ip(ip),
            user_agent=user_agent,
        )
        return IssuedSession(
            session_id=session_id,
            token=token,
            user_id=user_id,
            identity_id=identity_id,
            device_id=device_id,
            expires_at=expires_at,
            absolute_expires_at=absolute_expires_at,
        )

    # ------------------------------------------------------------------ validate
    def validate(self, *, token: str) -> SessionView:
        """Validate a bearer token; every failure mode denies (§三十四)."""
        if not token:
            raise SessionTokenRejected("invalid session")
        row = self._sessions.find_by_token_hash(hash_token(token))
        if row is None:
            raise SessionTokenRejected("invalid session")
        return self.validate_session_id(str(row._mapping["id"]))

    def validate_session_id(self, session_id: str) -> SessionView:
        row = self._sessions.get_session(session_id)
        if row is None:
            raise SessionNotUsable("unknown session")
        mapping = row._mapping
        if str(mapping["status"]) != SessionStatus.ACTIVE.value:
            raise SessionNotUsable("session is not active")

        now = _now()
        if mapping["expires_at"] is not None and mapping["expires_at"] <= now:
            self._sessions.set_status(session_id, to_persistence_session_status(SessionStatus.EXPIRED))
            raise SessionNotUsable("session expired")
        absolute = mapping["absolute_expires_at"]
        if absolute is not None and absolute <= now:
            self._sessions.set_status(session_id, to_persistence_session_status(SessionStatus.EXPIRED))
            raise SessionNotUsable("session expired")

        identity = self._identities.get_identity(str(mapping["identity_id"]))
        if identity is None or str(identity._mapping["status"]) != IdentityStatus.ACTIVE.value:
            raise SessionNotUsable("identity is not usable")

        user = self._identities.get_user(str(mapping["user_id"]))
        if user is None or str(user._mapping["status"]) not in (
            UserStatus.ACTIVE.value,
            UserStatus.PENDING.value,
        ):
            raise SessionNotUsable("user is not usable")

        device_id = str(mapping["device_id"]) if mapping["device_id"] else None
        if device_id is not None:
            device = self._devices.get_device(device_id)
            if device is None or not is_authenticatable_device(str(device._mapping["status"])):
                raise SessionNotUsable("device is not authenticatable")

        self._sessions.touch(session_id)
        return SessionView(
            session_id=session_id,
            user_id=str(mapping["user_id"]),
            identity_id=str(mapping["identity_id"]),
            device_id=device_id,
            expires_at=mapping["expires_at"],
            absolute_expires_at=absolute,
        )

    # ------------------------------------------------------------------- refresh
    def refresh(self, *, session_id: str) -> SessionView:
        """Extend the relative ceiling, **never** the absolute one (§二十)."""
        view = self.validate_session_id(session_id)
        now = _now()
        target = now + timedelta(seconds=self._relative)
        if view.absolute_expires_at is not None and target > view.absolute_expires_at:
            target = view.absolute_expires_at
        self._sessions._execute(
            "UPDATE public.sessions SET expires_at = :expires, updated_at = now()"
            " WHERE id = :sid",
            {"sid": session_id, "expires": target},
        )
        return SessionView(
            session_id=view.session_id,
            user_id=view.user_id,
            identity_id=view.identity_id,
            device_id=view.device_id,
            expires_at=target,
            absolute_expires_at=view.absolute_expires_at,
        )

    # -------------------------------------------------------------------- revoke
    def revoke(self, *, session_id: str, reason: str = "logout") -> int:
        """Granular revoke: exactly one session (§二十一)."""
        return self._sessions.set_status(
            session_id,
            to_persistence_session_status(SessionStatus.REVOKED),
            reason=reason,
            revoke=True,
        )

    def revoke_for_device(self, device_id: str, *, reason: str) -> int:
        return self._sessions.revoke_for_device(device_id, reason=reason)

    def revoke_for_identity(self, identity_id: str, *, reason: str) -> int:
        return self._sessions.revoke_for_identity(identity_id, reason=reason)

    def revoke_for_user(self, user_id: str, *, reason: str) -> int:
        return self._sessions.revoke_for_user(user_id, reason=reason)

    def expire_overdue(self) -> int:
        return self._sessions.expire_overdue()


__all__ = [
    "DEFAULT_ABSOLUTE_TTL_SECONDS",
    "DEFAULT_RELATIVE_TTL_SECONDS",
    "IssuedSession",
    "SessionService",
    "SessionView",
    "normalize_client_ip",
]
