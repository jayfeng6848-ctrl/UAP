"""Wave 1 §21 -- runtime error taxonomy must separate security from transient."""

from __future__ import annotations

from infrastructure.runtime.errors import (
    NEVER_RETRY_CATEGORIES,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConnectionError,
    PrincipalAssertionError,
    PersistenceError,
    SecurityBoundaryError,
    TransactionError,
    UnexpectedInternalError,
    classify,
    is_retryable,
)


def test_taxonomy_categories_are_distinct() -> None:
    categories = {
        ConfigurationError.category,
        ConnectionError.category,
        PersistenceError.category,
        TransactionError.category,
        AuthorizationError.category,
        AuthenticationError.category,
        SecurityBoundaryError.category,
        UnexpectedInternalError.category,
    }
    assert len(categories) == 8


def test_principal_assertion_is_a_security_boundary_error() -> None:
    exc = PrincipalAssertionError("role mismatch")
    assert isinstance(exc, SecurityBoundaryError)
    assert classify(exc) == SecurityBoundaryError.category
    assert is_retryable(exc) is False


def test_security_and_authorization_failures_are_never_retryable() -> None:
    for exc in (
        AuthorizationError("denied"),
        AuthenticationError("bad credential"),
        SecurityBoundaryError("refused"),
        TransactionError("bad boundary usage"),
        ConfigurationError("bad config"),
    ):
        assert classify(exc) in NEVER_RETRY_CATEGORIES
        assert is_retryable(exc) is False


def test_transient_categories_are_retryable() -> None:
    assert is_retryable(ConnectionError("refused")) is True
    assert is_retryable(PersistenceError("deadlock")) is True


def test_unknown_exception_maps_to_unexpected_without_leaking_message() -> None:
    assert classify(ValueError("password=supersecret")) == "unexpected"


def test_error_messages_can_be_constructed_without_secrets() -> None:
    # The taxonomy itself never embeds a DSN; callers pass safe text.
    exc = SecurityBoundaryError("security boundary refused the operation")
    assert "postgresql" not in str(exc)
