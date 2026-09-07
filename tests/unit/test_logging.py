"""Structured logging: envelope fields and automatic secret redaction."""

from __future__ import annotations

import json
import logging

from infrastructure.logging.redaction import REDACTED, redact_mapping, redact_url
from infrastructure.logging.structured import (
    JsonFormatter,
    clear_context,
    log_context,
)


def _format(record: logging.LogRecord) -> dict:
    return json.loads(JsonFormatter(service="uap").format(record))


def test_record_contains_required_envelope() -> None:
    record = logging.LogRecord(
        name="uap.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    payload = _format(record)
    for field in (
        "timestamp",
        "level",
        "service",
        "module",
        "request_id",
        "trace_id",
        "user_id",
        "tenant_id",
        "space_id",
        "event",
    ):
        assert field in payload


def test_bound_context_is_injected() -> None:
    clear_context()
    record = logging.LogRecord(
        name="uap.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="ctx",
        args=(),
        exc_info=None,
    )
    with log_context(request_id="r-1", tenant_id="t-1", space_id="s-1"):
        payload = _format(record)
    assert payload["request_id"] == "r-1"
    assert payload["tenant_id"] == "t-1"
    assert payload["space_id"] == "s-1"
    clear_context()


def test_sensitive_keys_are_redacted() -> None:
    cleaned = redact_mapping(
        {
            "password": "hunter2",
            "api_key": "abc123",
            "authorization": "Bearer xyz",
            "user_id": "u-1",
        }
    )
    assert cleaned["password"] == REDACTED
    assert cleaned["api_key"] == REDACTED
    assert cleaned["authorization"] == REDACTED
    assert cleaned["user_id"] == "u-1"


def test_secret_shaped_values_are_redacted_even_with_innocent_keys() -> None:
    cleaned = redact_mapping({"note": "key is sk-abcdefghijklmnopqrstuv"})
    assert cleaned["note"] == REDACTED


def test_no_secret_leaks_into_formatted_record() -> None:
    record = logging.LogRecord(
        name="uap.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="token=%s",
        args=("sk-abcdefghijklmnopqrstuv",),
        exc_info=None,
    )
    payload = _format(record)
    assert "sk-abcdefghijklmnopqrstuv" not in json.dumps(payload)


def test_url_credentials_are_stripped() -> None:
    assert redact_url("redis://user:secret@localhost:6379/0") == (
        "redis://user:***@localhost:6379/0"
    )
