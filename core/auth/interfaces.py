"""Authentication contracts.

Authentication proves *who* someone is. It never decides what they may do.
Credentials and tokens are treated as secrets: they must never be logged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

CREDENTIAL_TYPES = ("password", "token", "api_key", "device")


@dataclass(frozen=True)
class Credential:
    """A secret presented for authentication. ``repr`` is redacted."""

    type: str
    secret: str = field(repr=False)
    identity_hint: str | None = None

    def __post_init__(self) -> None:
        if self.type not in CREDENTIAL_TYPES:
            raise ValueError(f"unsupported credential type {self.type!r}")


@dataclass(frozen=True)
class AuthenticationResult:
    success: bool
    identity_id: str | None = None
    reason: str | None = None


@runtime_checkable
class Authenticator(Protocol):
    def authenticate(self, credential: Credential) -> AuthenticationResult:
        ...


@runtime_checkable
class TokenIssuer(Protocol):
    def issue(self, identity_id: str, scopes: tuple[str, ...] = ()) -> str:
        ...

    def verify(self, token: str) -> AuthenticationResult:
        ...


__all__ = ["CREDENTIAL_TYPES", "Credential", "AuthenticationResult", "Authenticator", "TokenIssuer"]
