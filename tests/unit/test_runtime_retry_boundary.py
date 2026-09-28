"""Wave 1 §11 -- retry must be bounded and must never mask security failures."""

from __future__ import annotations

import pytest

from infrastructure.runtime.errors import AuthorizationError, ConnectionError
from infrastructure.runtime.retry import retry_idempotent


def test_retry_is_bounded() -> None:
    calls = {"n": 0}

    def always_fail() -> None:
        calls["n"] += 1
        raise ConnectionError("transient")

    with pytest.raises(ConnectionError):
        retry_idempotent(always_fail, max_attempts=3, sleep=lambda _s: None)
    assert calls["n"] == 3


def test_retry_succeeds_after_transient_failure() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("transient")
        return "ok"

    assert retry_idempotent(flaky, max_attempts=3, sleep=lambda _s: None) == "ok"
    assert calls["n"] == 2


def test_security_failure_is_never_retried() -> None:
    calls = {"n": 0}

    def denied() -> None:
        calls["n"] += 1
        raise AuthorizationError("denied")

    with pytest.raises(AuthorizationError):
        retry_idempotent(denied, max_attempts=5, sleep=lambda _s: None)
    assert calls["n"] == 1, "authorization failures must not be retried"


def test_max_attempts_must_be_positive() -> None:
    with pytest.raises(ValueError):
        retry_idempotent(lambda: None, max_attempts=0)
