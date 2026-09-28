"""Session-layer errors (Wave 2 §十七 – §二十一)."""

from __future__ import annotations


class SessionError(Exception):
    """Base class for session-layer failures."""

    code = "session_error"


class SessionValidationError(SessionError):
    """The caller supplied an input the session rules cannot accept."""

    code = "session_validation_error"


class SessionNotUsable(SessionError):
    """The session is unknown, expired, revoked, or its bindings are broken.

    Coarse by design: callers must not learn *which* check failed
    (§三十四 fail-closed).
    """

    code = "session_not_usable"


class SessionTokenRejected(SessionError):
    """The presented bearer token does not map to a usable session."""

    code = "authentication_failed"


__all__ = [
    "SessionError",
    "SessionNotUsable",
    "SessionTokenRejected",
    "SessionValidationError",
]
