"""Identity / credential errors (Wave 2 §六 / §三十三)."""

from __future__ import annotations


class IdentityError(Exception):
    """Base class for identity-layer failures."""

    code = "identity_error"


class IdentityConflict(IdentityError):
    """A uniqueness constraint of the *persistence* vocabulary was violated.

    Wave 2 maps this to ``identity_conflict`` rather than a generic internal
    error (§六).
    """

    code = "identity_conflict"


class IdentityValidationError(IdentityError):
    """The caller supplied a value the identity rules cannot accept."""

    code = "identity_validation_error"


class IdentityNotUsable(IdentityError):
    """The identity exists but may not be used (not active / revoked / ...)."""

    code = "identity_not_usable"


class CredentialRejected(IdentityError):
    """The presented credential is invalid, expired, revoked or locked.

    Deliberately carries a single coarse reason so callers cannot distinguish
    "wrong secret" from "no such identity" (§三十四 fail-closed).
    """

    code = "authentication_failed"


__all__ = [
    "CredentialRejected",
    "IdentityConflict",
    "IdentityError",
    "IdentityNotUsable",
    "IdentityValidationError",
]
