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
from services.identity_runtime import ErrorCode as P17ErrorCode, IdentityRuntimeError
from services.session import SessionNotUsable, SessionTokenRejected, SessionValidationError

#: P17 codes that are authorization denials (no distinction is exposed to the
#: caller between "not a member", "wrong scope", "no permission" and
#: "not provisioned": all are the same safe 403 · P17 §40/§46).
_P17_AUTHORIZATION: frozenset[str] = frozenset(
    {
        P17ErrorCode.TENANT_SCOPE_DENIED,
        P17ErrorCode.SPACE_SCOPE_DENIED,
        P17ErrorCode.MEMBERSHIP_REQUIRED,
        P17ErrorCode.ROLE_SCOPE_MISMATCH,
        P17ErrorCode.AUTHORIZATION_DENIED,
        P17ErrorCode.RESOURCE_NOT_PROVISIONED,
        P17ErrorCode.AGENT_SCOPE_DENIED,
        P17ErrorCode.AGENT_SPACE_SCOPE_DENIED,
        P17ErrorCode.CONTROL_PLANE_WRITE_DENIED,
        P17ErrorCode.AUDIT_UNAVAILABLE,
    }
)

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
    if isinstance(exc, IdentityRuntimeError):
        if exc.code in _P17_AUTHORIZATION:
            return "authorization"
        if exc.code == P17ErrorCode.MEMBERSHIP_DUPLICATE:
            return "conflict"
        return "validation"
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
