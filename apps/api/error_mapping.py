"""HTTP error mapping for Wave 2 (§三十三).

The Wave 1 eight-class taxonomy stays authoritative; this module only decides
which HTTP status a class becomes. Security-relevant classes
(``security_boundary`` / ``persistence``) are deliberately **fuzzed**: the caller
never learns the database name, a role name, SQL text or a connection string
(§四十一).
"""

from __future__ import annotations

from fastapi import HTTPException

from infrastructure.runtime.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConnectionError as RuntimeConnectionError,
    PersistenceError,
    SecurityBoundaryError,
    TransactionError,
    UnexpectedInternalError,
)
from services.context import ContextDenied, ContextRequired, ContextUnavailable
from services.device import ChallengeRejected, DeviceConflict, DeviceNotUsable, DeviceValidationError
from services.identity import (
    CredentialRejected,
    IdentityConflict,
    IdentityNotUsable,
    IdentityValidationError,
)
from services.session import SessionNotUsable, SessionTokenRejected, SessionValidationError

#: class -> (status, safe message). The message never carries internal detail.
HTTP_STATUS: dict[str, tuple[int, str]] = {
    "authentication": (401, "authentication failed"),
    "authorization": (403, "permission denied"),
    "context_required": (400, "context required"),
    "validation": (422, "request rejected"),
    "conflict": (409, "conflict"),
    "persistence": (503, "service temporarily unavailable"),
    "security_boundary": (503, "service temporarily unavailable"),
    "connection": (503, "service temporarily unavailable"),
    "transaction": (503, "service temporarily unavailable"),
    "configuration": (500, "internal error"),
    "internal": (500, "internal error"),
}


def classify(exc: BaseException) -> str:
    """Map a service/infrastructure exception to a taxonomy class name."""
    if isinstance(exc, (CredentialRejected, SessionTokenRejected, SessionNotUsable,
                        IdentityNotUsable, DeviceNotUsable, ChallengeRejected)):
        return "authentication"
    if isinstance(exc, (ContextDenied, AuthorizationError)):
        return "authorization"
    if isinstance(exc, ContextRequired):
        return "context_required"
    if isinstance(exc, (IdentityConflict, DeviceConflict)):
        return "conflict"
    if isinstance(exc, (IdentityValidationError, SessionValidationError,
                        DeviceValidationError, ValueError, TypeError)):
        return "validation"
    if isinstance(exc, SecurityBoundaryError):
        return "security_boundary"
    if isinstance(exc, PersistenceError):
        return "persistence"
    if isinstance(exc, RuntimeConnectionError):
        return "connection"
    if isinstance(exc, TransactionError):
        return "transaction"
    if isinstance(exc, ConfigurationError):
        return "configuration"
    if isinstance(exc, ContextUnavailable):
        return "security_boundary"
    if isinstance(exc, (AuthenticationError,)):
        return "authentication"
    if isinstance(exc, UnexpectedInternalError):
        return "internal"
    return "internal"


def translate(exc: BaseException) -> HTTPException:
    """Turn any service failure into an HTTP error without leaking internals."""
    if isinstance(exc, HTTPException):
        return exc
    status, message = HTTP_STATUS[classify(exc)]
    return HTTPException(status_code=status, detail=message)


__all__ = ["HTTP_STATUS", "classify", "translate"]
