"""Runtime error taxonomy (P14 Runtime Implementation Wave 1, §21).

Every runtime failure must be classifiable so that a *security* failure is never
confused with a normal transient failure. Messages must never carry credentials
or raw connection strings.
"""

from __future__ import annotations


class RuntimeLayerError(Exception):
    """Base class for all runtime-layer errors."""

    category = "runtime"


class ConfigurationError(RuntimeLayerError):
    """Configuration is missing, malformed, or self-contradictory."""

    category = "configuration"


class ConnectionError(RuntimeLayerError):
    """The database could not be reached (transient or permanent)."""

    category = "connection"


class PersistenceError(RuntimeLayerError):
    """A repository / persistence operation failed."""

    category = "persistence"


class TransactionError(RuntimeLayerError):
    """A transaction boundary was used incorrectly or failed to settle."""

    category = "transaction"


class AuthorizationError(RuntimeLayerError):
    """Authorization denied the operation (fail-closed by design)."""

    category = "authorization"


class AuthenticationError(RuntimeLayerError):
    """Credential / identity verification failed or was ambiguous."""

    category = "authentication"


class SecurityBoundaryError(RuntimeLayerError):
    """The database security boundary refused an operation it must refuse.

    Not a transient failure: the runtime attempted something the security
    matrix does not allow, or the boundary drifted. Never retried.
    """

    category = "security_boundary"


class PrincipalAssertionError(SecurityBoundaryError):
    """The effective database principal is not the configured runtime principal."""


class UnexpectedInternalError(RuntimeLayerError):
    """Anything that does not fit the categories above."""

    category = "unexpected"


#: Categories that must never be retried (P14 RTA-07 / Wave 1 §11).
NEVER_RETRY_CATEGORIES = frozenset(
    {
        ConfigurationError.category,
        TransactionError.category,
        AuthorizationError.category,
        AuthenticationError.category,
        SecurityBoundaryError.category,
    }
)


def classify(exc: BaseException) -> str:
    """Return the taxonomy category of ``exc`` (never leaks the message)."""
    if isinstance(exc, RuntimeLayerError):
        return exc.category
    return UnexpectedInternalError.category


def is_retryable(exc: BaseException) -> bool:
    """Whether ``exc`` belongs to a category that may be retried at all."""
    return classify(exc) not in NEVER_RETRY_CATEGORIES


__all__ = [
    "RuntimeLayerError",
    "ConfigurationError",
    "ConnectionError",
    "PersistenceError",
    "TransactionError",
    "AuthorizationError",
    "AuthenticationError",
    "SecurityBoundaryError",
    "PrincipalAssertionError",
    "UnexpectedInternalError",
    "NEVER_RETRY_CATEGORIES",
    "classify",
    "is_retryable",
]
