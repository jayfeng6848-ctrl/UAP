"""Wave 2 use-cases: the transaction boundary lives here, not in handlers.

Each function owns exactly one ``RuntimeDatabase.transaction()`` (Wave 1 rule
DC-16/17/18: service/use-case owns the boundary, repositories never commit,
handlers never open a transaction). The API layer only adapts HTTP.

Secret material (bearer tokens, challenge secrets) is returned to the caller
exactly once and is never logged.
"""

from __future__ import annotations

from dataclasses import dataclass

from infrastructure.database.runtime import RuntimeDatabase
from services.audit import AuditWriter
from services.context import AuthenticatedRuntimeContext, ContextBuilder
from services.device import DeviceService, EnrolledDevice, EnrollmentChallenge
from services.device import DeviceNotUsable
from services.identity import (
    AuthenticatedIdentity,
    CredentialRejected,
    IdentityService,
    OnboardedIdentity,
)
from services.session import IssuedSession, SessionService, SessionView


@dataclass(frozen=True)
class LoginResult:
    """Credential verification result (session is optional per §十七)."""

    identity: AuthenticatedIdentity
    session: IssuedSession | None = None


def _authenticate_recorded(
    session, *, login_id: str, password: str, action: str
) -> tuple[AuthenticatedIdentity | None, CredentialRejected | None]:
    """Authenticate and record the outcome **without raising**.

    §九 requires bounded failed attempts and lock behaviour, which only exist if
    the attempt counter survives the denial. ``RuntimeDatabase.transaction()``
    rolls back on exception, so a denial is returned to the caller instead of
    being raised inside the transaction: the caller lets the bookkeeping
    (counter + audit row) commit and *then* raises. No authority is granted by
    that commit — only counters and an audit row are persisted.
    """
    try:
        identity = IdentityService(session).authenticate(login=login_id, password=password)
    except CredentialRejected as exc:
        AuditWriter(session).record(
            action=action,
            actor_type="anonymous",
            result="denied",
            risk_level="MEDIUM",
            metadata={"reason": "credential_rejected"},
        )
        return None, exc
    return identity, None


# --------------------------------------------------------------------- identity
def onboard_identity(
    db: RuntimeDatabase,
    *,
    password: str,
    email: str | None = None,
    username: str | None = None,
    display_name: str | None = None,
) -> OnboardedIdentity:
    """``users`` + ``identities`` + ``credentials`` in one transaction (§四十二)."""
    with db.transaction() as session:
        result = IdentityService(session).onboard(
            email=email, username=username, display_name=display_name, password=password
        )
        AuditWriter(session).record(
            action="identity.onboard",
            actor_type="user",
            actor_id=result.user_id,
            result="success",
            risk_level="MEDIUM",
            metadata={"identity_id": result.identity_id},
        )
        return result


def authenticate_identity(
    db: RuntimeDatabase, *, login: str, password: str
) -> AuthenticatedIdentity:
    """Verify a password credential; audit both outcomes.

    A denial commits its bookkeeping (bounded attempt counter + audit row) and
    then re-raises the rejection outside the transaction.
    """
    denial: CredentialRejected | None = None
    identity: AuthenticatedIdentity | None = None
    with db.transaction() as session:
        identity, denial = _authenticate_recorded(
            session, login_id=login, password=password, action="identity.authenticate"
        )
        if denial is None:
            AuditWriter(session).record(
                action="identity.authenticate",
                actor_type="user",
                actor_id=identity.user_id,
                result="success",
                risk_level="LOW",
                metadata={"identity_id": identity.identity_id, "channel": "password"},
            )
    if denial is not None:
        raise denial
    assert identity is not None
    return identity


# ----------------------------------------------------------------------- device
def start_device_enrollment(
    db: RuntimeDatabase,
    *,
    login: str,
    password: str,
    fingerprint: str,
    label: str | None = None,
) -> EnrollmentChallenge:
    """Authenticate an eligible user, then issue a one-time challenge (§十三)."""
    denial: CredentialRejected | None = None
    challenge: EnrollmentChallenge | None = None
    with db.transaction() as session:
        identity, denial = _authenticate_recorded(
            session, login_id=login, password=password, action="device.enrollment.attempt"
        )
        if denial is None:
            challenge = DeviceService(session).start_enrollment(
                user_id=identity.user_id,
                identity_id=identity.identity_id,
                fingerprint=fingerprint,
                label=label,
            )
            AuditWriter(session).record(
                action="device.enrollment.started",
                actor_id=identity.user_id,
                result="success",
                risk_level="MEDIUM",
                metadata={"identity_id": identity.identity_id, "channel": "challenge"},
            )
    if denial is not None:
        raise denial
    assert challenge is not None
    return challenge


def complete_device_enrollment(
    db: RuntimeDatabase,
    *,
    challenge_id: str,
    secret: str,
    fingerprint: str,
    label: str | None = None,
    platform: str | None = None,
) -> EnrolledDevice:
    """Consume the challenge and create the device ``pending -> active`` atomically."""
    with db.transaction() as session:
        device = DeviceService(session).verify_enrollment(
            challenge_id=challenge_id,
            secret=secret,
            fingerprint=fingerprint,
            label=label,
            platform=platform,
        )
        AuditWriter(session).record(
            action="device.enrolled",
            actor_id=device.user_id,
            result="success",
            risk_level="MEDIUM",
            resource_type="device",
            resource_id=device.device_id,
            metadata={"device_id": device.device_id},
        )
        return device


def revoke_device(
    db: RuntimeDatabase,
    *,
    device_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> dict[str, int | str]:
    """Device revoke + its active sessions revoke in ONE transaction (§十五).

    ``actor_user_id`` (when supplied) enforces ownership inside the use-case, so
    a handler never has to make an ownership decision of its own.
    """
    with db.transaction() as session:
        devices = DeviceService(session)
        if actor_user_id is not None:
            device = devices.get(device_id)
            if str(device["user_id"]) != actor_user_id:
                raise DeviceNotUsable("device does not belong to this user")
        result = devices.revoke_device(device_id=device_id, reason=reason)
        AuditWriter(session).record(
            action="device.revoked",
            result="success",
            risk_level="HIGH",
            resource_type="device",
            resource_id=device_id,
            metadata={
                "device_id": device_id,
                "reason": reason,
                "sessions_revoked": result["sessions_revoked"],
            },
        )
        return result


def mark_device_lost(
    db: RuntimeDatabase, *, device_id: str, reason: str, actor_user_id: str | None = None
) -> str:
    with db.transaction() as session:
        devices = DeviceService(session)
        if actor_user_id is not None:
            device = devices.get(device_id)
            if str(device["user_id"]) != actor_user_id:
                raise DeviceNotUsable("device does not belong to this user")
        status = devices.mark_lost(device_id, reason=reason)
        AuditWriter(session).record(
            action="device.lost",
            result="success",
            risk_level="HIGH",
            resource_type="device",
            resource_id=device_id,
            metadata={"device_id": device_id, "reason": reason},
        )
        return status


# ---------------------------------------------------------------------- session
def login(
    db: RuntimeDatabase,
    *,
    login_id: str,
    password: str,
    device_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> LoginResult:
    """Authenticate and (when a device is supplied) create a session atomically."""
    denial: CredentialRejected | None = None
    identity: AuthenticatedIdentity | None = None
    created: IssuedSession | None = None
    with db.transaction() as session:
        identity, denial = _authenticate_recorded(
            session, login_id=login_id, password=password, action="session.login.attempt"
        )
        if denial is None:
            if device_id:
                created = SessionService(session).create(
                    user_id=identity.user_id,
                    identity_id=identity.identity_id,
                    device_id=device_id,
                    ip=ip,
                    user_agent=user_agent,
                )
            AuditWriter(session).record(
                action="session.created" if created else "identity.authenticate",
                actor_id=identity.user_id,
                result="success",
                risk_level="LOW",
                metadata={
                    "identity_id": identity.identity_id,
                    "device_id": device_id,
                    "session_id": created.session_id if created else None,
                    "channel": "password",
                },
            )
    if denial is not None:
        raise denial
    assert identity is not None
    return LoginResult(identity=identity, session=created)


def refresh_session(db: RuntimeDatabase, *, token: str) -> SessionView:
    with db.transaction() as session:
        view = SessionService(session).refresh(session_id=SessionService(session).validate(token=token).session_id)
        return view


def logout(db: RuntimeDatabase, *, token: str, reason: str = "logout") -> int:
    """Granular logout: exactly this session (§二十一)."""
    with db.transaction() as session:
        sessions = SessionService(session)
        view = sessions.validate(token=token)
        revoked = sessions.revoke(session_id=view.session_id, reason=reason)
        AuditWriter(session).record(
            action="session.logout",
            actor_id=view.user_id,
            result="success",
            risk_level="LOW",
            metadata={"session_id": view.session_id, "reason": reason},
        )
        return revoked


def expire_overdue_sessions(db: RuntimeDatabase) -> int:
    with db.transaction() as session:
        return SessionService(session).expire_overdue()


# ---------------------------------------------------------------------- context
def build_context(
    db: RuntimeDatabase,
    *,
    token: str,
    tenant_id: str | None = None,
    space_id: str | None = None,
    correlation_id: str | None = None,
    request_id: str | None = None,
) -> AuthenticatedRuntimeContext:
    """Validate the bearer session and freeze the minimal request context."""
    with db.transaction() as session:
        session_id = SessionService(session).validate(token=token).session_id
        return ContextBuilder(session).build(
            session_id=session_id,
            requested_tenant_id=tenant_id,
            requested_space_id=space_id,
            correlation_id=correlation_id,
            request_id=request_id,
        )


__all__ = [
    "LoginResult",
    "authenticate_identity",
    "build_context",
    "complete_device_enrollment",
    "expire_overdue_sessions",
    "login",
    "logout",
    "mark_device_lost",
    "onboard_identity",
    "refresh_session",
    "revoke_device",
    "start_device_enrollment",
]
