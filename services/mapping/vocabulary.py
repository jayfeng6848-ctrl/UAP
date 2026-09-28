"""Wave 2 vocabulary mappers (Domain <-> 0017 persistence).

Frozen inputs (PDL Appendix P, 2026-09-28):

* VOC-W2-02 -> A : the persisted credential vocabulary is the persistence truth;
  the Domain enum must cross the boundary through an explicit mapping.
* VOC-W2-03 -> A : the five persisted device statuses are the persistence truth.
* VOC-W2-04 -> C : ``users.status`` and ``identities.status`` are two concurrent
  state machines, each mapped explicitly.
* §十一 : "verification in progress" is an **application workflow state**; it is
  never written as a persisted status.

The in-code Domain vocabulary is the enum below. Crossings are dictionaries, so
an unknown value raises instead of leaking through.
"""

from __future__ import annotations

from enum import Enum

from .errors import UnknownVocabularyValue


class UserStatus(str, Enum):
    """Domain view of ``users.status`` (persistence truth: §九 / §5.2)."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    DELETED = "deleted"


class IdentityStatus(str, Enum):
    """Domain view of ``identities.status`` (§十 / §5.3)."""

    UNVERIFIED = "unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class IdentityProvider(str, Enum):
    """``identities.provider`` — the authentication source, not ``users``."""

    LOCAL = "local"
    OIDC = "oidc"
    SAML = "saml"
    DEVICE = "device"
    SERVICE = "service"


class DeviceStatus(str, Enum):
    """``devices.status`` — five states are persistence truth (§八 / §十二)."""

    PENDING = "pending"
    ACTIVE = "active"
    UNTRUSTED = "untrusted"
    REVOKED = "revoked"
    LOST = "lost"


class SessionStatus(str, Enum):
    """``sessions.status`` — Domain and persistence agree (§十九)."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class CredentialType(str, Enum):
    """**Domain** credential vocabulary (``core.auth.CREDENTIAL_TYPES``).

    The persisted vocabulary is richer (``recovery_code`` / ``device_cert`` /
    ``otp``); the mapping below is explicit and many-to-one on this side.
    """

    PASSWORD = "password"
    TOKEN = "token"
    API_KEY = "api_key"
    DEVICE = "device"


class CredentialAlgorithm(str, Enum):
    """``credentials.algorithm`` — the persisted algorithm vocabulary."""

    ARGON2ID = "argon2id"
    SCRYPT = "scrypt"
    SHA256_HMAC = "sha256_hmac"


USER_STATUSES = tuple(s.value for s in UserStatus)
IDENTITY_STATUSES = tuple(s.value for s in IdentityStatus)
IDENTITY_PROVIDERS = tuple(p.value for p in IdentityProvider)
DEVICE_STATUSES = tuple(s.value for s in DeviceStatus)
SESSION_STATUSES = tuple(s.value for s in SessionStatus)
CREDENTIAL_TYPES = ("password", "api_key", "recovery_code", "device_cert", "otp")
CREDENTIAL_ALGORITHMS = tuple(a.value for a in CredentialAlgorithm)

# --------------------------------------------------------------------------- #
# Explicit mapping tables (no implicit casts, no magic strings)
# --------------------------------------------------------------------------- #

_USER_STATUS: dict[str, UserStatus] = {s.value: s for s in UserStatus}
_IDENTITY_STATUS: dict[str, IdentityStatus] = {s.value: s for s in IdentityStatus}
_IDENTITY_PROVIDER: dict[str, IdentityProvider] = {p.value: p for p in IdentityProvider}
_DEVICE_STATUS: dict[str, DeviceStatus] = {s.value: s for s in DeviceStatus}
_SESSION_STATUS: dict[str, SessionStatus] = {s.value: s for s in SessionStatus}
_CREDENTIAL_ALGORITHM: dict[str, CredentialAlgorithm] = {
    a.value: a for a in CredentialAlgorithm
}

#: Domain credential type -> persisted ``credentials.type`` (§七).
_DOMAIN_TO_PERSISTED_CREDENTIAL: dict[CredentialType, str] = {
    CredentialType.PASSWORD: "password",
    CredentialType.API_KEY: "api_key",
    CredentialType.DEVICE: "device_cert",
    CredentialType.TOKEN: "otp",
}

#: Persisted ``credentials.type`` -> Domain credential type (§七, many-to-one).
_PERSISTED_TO_DOMAIN_CREDENTIAL: dict[str, CredentialType] = {
    "password": CredentialType.PASSWORD,
    "api_key": CredentialType.API_KEY,
    "device_cert": CredentialType.DEVICE,
    "otp": CredentialType.TOKEN,
    "recovery_code": CredentialType.TOKEN,
}


def _lookup(table: dict[str, object], value: str, axis: str) -> object:
    try:
        return table[value]
    except KeyError as exc:
        raise UnknownVocabularyValue(
            f"{value!r} is not part of the frozen {axis} vocabulary "
            f"(allowed: {sorted(table)})"
        ) from exc


def to_domain_user_status(value: str) -> UserStatus:
    return _lookup(_USER_STATUS, value, "users.status")  # type: ignore[return-value]


def to_persistence_user_status(value: UserStatus) -> str:
    return _USER_STATUS[value].value if isinstance(value, UserStatus) else _lookup(
        _USER_STATUS, str(value), "users.status"
    ).value  # type: ignore[union-attr]


def to_domain_identity_status(value: str) -> IdentityStatus:
    return _lookup(_IDENTITY_STATUS, value, "identities.status")  # type: ignore[return-value]


def to_persistence_identity_status(value: IdentityStatus) -> str:
    return value.value


def to_persistence_identity_provider(value: IdentityProvider) -> str:
    return value.value


def to_domain_device_status(value: str) -> DeviceStatus:
    return _lookup(_DEVICE_STATUS, value, "devices.status")  # type: ignore[return-value]


def to_persistence_device_status(value: DeviceStatus) -> str:
    return value.value


def to_domain_session_status(value: str) -> SessionStatus:
    return _lookup(_SESSION_STATUS, value, "sessions.status")  # type: ignore[return-value]


def to_persistence_session_status(value: SessionStatus) -> str:
    return value.value


def to_persistence_credential_type(value: CredentialType) -> str:
    """Domain -> persisted. An unmapped Domain value raises (§七)."""
    try:
        return _DOMAIN_TO_PERSISTED_CREDENTIAL[value]
    except KeyError as exc:
        raise UnknownVocabularyValue(
            f"domain credential type {value!r} has no persisted mapping"
        ) from exc


def to_domain_credential_type(value: str) -> CredentialType:
    return _lookup(  # type: ignore[return-value]
        _PERSISTED_TO_DOMAIN_CREDENTIAL, value, "credentials.type"
    )


def to_persistence_credential_algorithm(value: CredentialAlgorithm) -> str:
    return value.value


def to_domain_credential_algorithm(value: str) -> CredentialAlgorithm:
    return _lookup(  # type: ignore[return-value]
        _CREDENTIAL_ALGORITHM, value, "credentials.algorithm"
    )


# --------------------------------------------------------------------------- #
# Application semantics for the two device states the Domain subset cannot hold
# --------------------------------------------------------------------------- #

#: Only ``active`` satisfies a normal trust requirement. ``untrusted`` and
#: ``lost`` exist in persistence but are NOT authenticatable (§八 / §十二 / §十六).
_AUTHENTICATABLE_DEVICE_STATUSES = frozenset({DeviceStatus.ACTIVE.value})


def is_authenticatable_device(status: DeviceStatus | str) -> bool:
    """Whether the status may be used for normal authentication.

    ``untrusted`` is explicitly **not** equivalent to ``active`` and ``lost`` is
    explicitly **not** equivalent to ``revoked`` — but neither may authenticate.
    """
    raw = status.value if isinstance(status, DeviceStatus) else str(status)
    _ = to_domain_device_status(raw)  # validates vocabulary membership
    return raw in _AUTHENTICATABLE_DEVICE_STATUSES


__all__ = [
    "CREDENTIAL_ALGORITHMS",
    "CREDENTIAL_TYPES",
    "DEVICE_STATUSES",
    "IDENTITY_PROVIDERS",
    "IDENTITY_STATUSES",
    "SESSION_STATUSES",
    "USER_STATUSES",
    "CredentialAlgorithm",
    "CredentialType",
    "DeviceStatus",
    "IdentityProvider",
    "IdentityStatus",
    "SessionStatus",
    "UserStatus",
    "is_authenticatable_device",
    "to_domain_credential_algorithm",
    "to_domain_credential_type",
    "to_domain_device_status",
    "to_domain_identity_status",
    "to_domain_session_status",
    "to_domain_user_status",
    "to_persistence_credential_algorithm",
    "to_persistence_credential_type",
    "to_persistence_device_status",
    "to_persistence_identity_provider",
    "to_persistence_identity_status",
    "to_persistence_session_status",
    "to_persistence_user_status",
]
