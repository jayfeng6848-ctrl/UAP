"""The authenticated runtime context (Wave 2 §二十二 / §二十三).

A **minimal, immutable, request-scoped** representation. It carries identifiers
and validated facts only:

* no credential, password, token, secret or hash,
* no whole ORM row (user / device / credential),
* no membership or authorization collections,
* no decision result — authorization is evaluated per use-case, never cached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AuthenticationAssurance(str, Enum):
    """How far the request got along the frozen evaluation chain (§二十九).

    ``CREDENTIAL_VERIFIED``   -> credential check only (mid-login)
    ``IDENTITY_VERIFIED``     -> identity is active (device-less / service)
    ``SESSION_VERIFIED``      -> active device-bound session (normal human path)
    """

    CREDENTIAL_VERIFIED = "credential_verified"
    IDENTITY_VERIFIED = "identity_verified"
    SESSION_VERIFIED = "session_verified"


#: Exactly the fields that may reach logs / metrics / traces (§四十四, CTX-W2-03).
LOG_SAFE_FIELDS = (
    "correlation_id",
    "session_id",
    "device_id",
    "identity_id",
    "user_id",
    "tenant_id",
    "space_id",
    "subject_type",
    "scope",
    "authentication_assurance",
)


@dataclass(frozen=True, slots=True)
class AuthenticatedRuntimeContext:
    """The minimum a service/use-case needs. Frozen; never reused across requests."""

    user_id: str
    identity_id: str
    session_id: str | None = None
    device_id: str | None = None
    tenant_id: str | None = None
    space_id: str | None = None
    subject_type: str = "USER"
    scope: str = "PLATFORM"
    actor_type: str = "user"
    authentication_assurance: AuthenticationAssurance = (
        AuthenticationAssurance.CREDENTIAL_VERIFIED
    )
    correlation_id: str | None = None
    request_id: str | None = None
    extra: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def is_device_bound(self) -> bool:
        """True only for the normal human path (device present and verified)."""
        return self.device_id is not None

    def log_fields(self) -> dict[str, str | None]:
        """Whitelisted projection for observability (never contains secrets)."""
        return {name: getattr(self, name) for name in LOG_SAFE_FIELDS}


__all__ = ["LOG_SAFE_FIELDS", "AuthenticatedRuntimeContext", "AuthenticationAssurance"]
