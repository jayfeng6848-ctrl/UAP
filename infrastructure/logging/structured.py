"""Structured (JSON) logging for UAP.

Every record carries the platform envelope:

    timestamp, level, service, module, request_id, trace_id,
    user_id, tenant_id, space_id, event, message

Sensitive fields are redacted before emission, see :mod:`redaction`.
Context fields (request_id, trace_id, tenant_id, ...) are bound per execution
context via :class:`LogContext` / :func:`bind_context` and are injected into
every record automatically.
"""

from __future__ import annotations

import contextvars
import json
import logging as _logging
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, MutableMapping

from .redaction import redact_mapping

CONTEXT_FIELDS: tuple[str, ...] = (
    "request_id",
    "trace_id",
    "user_id",
    "tenant_id",
    "space_id",
    "event",
)

_ctx: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "uap_log_context", default={}
)


class JsonFormatter(_logging.Formatter):
    """Emit one JSON object per line with the UAP envelope."""

    def __init__(self, service: str = "uap") -> None:
        super().__init__()
        self.service = service

    def format(self, record: _logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "module": record.module,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in CONTEXT_FIELDS:
            payload[field] = None

        context = dict(_ctx.get())
        context.update(getattr(record, "context", {}) or {})
        for key, value in context.items():
            if key in CONTEXT_FIELDS:
                payload[key] = value

        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, MutableMapping):
            payload.update(extra)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        payload = redact_mapping(payload)
        return json.dumps(payload, ensure_ascii=False, default=str)


class ConsoleFormatter(_logging.Formatter):
    """Human readable formatter used for local development."""

    def format(self, record: _logging.LogRecord) -> str:
        context = dict(_ctx.get())
        context.update(getattr(record, "context", {}) or {})
        suffix = " ".join(
            f"{k}={v}" for k, v in context.items() if v is not None
        )
        base = f"{record.levelname:<7} {record.name}: {record.getMessage()}"
        return f"{base} [{suffix}]" if suffix else base


def bind_context(**fields: Any) -> None:
    """Bind contextual fields for all subsequent records in this context."""
    current = dict(_ctx.get())
    current.update({k: v for k, v in fields.items() if v is not None})
    _ctx.set(current)


def clear_context() -> None:
    _ctx.set({})


@contextmanager
def log_context(**fields: Any) -> Iterator[None]:
    """Temporarily bind contextual fields (restores previous state)."""
    token = _ctx.set({**_ctx.get(), **{k: v for k, v in fields.items() if v is not None}})
    try:
        yield
    finally:
        _ctx.reset(token)


def configure_logging(
    level: str = "INFO",
    fmt: str = "json",
    service: str = "uap",
    stream=None,
) -> None:
    """Configure the root logger exactly once for the current process."""
    handler = _logging.StreamHandler(stream or sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter(service=service))
    else:
        handler.setFormatter(ConsoleFormatter())

    root = _logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    root.propagate = False


def get_logger(name: str) -> _logging.Logger:
    return _logging.getLogger(name)


__all__ = [
    "JsonFormatter",
    "ConsoleFormatter",
    "bind_context",
    "clear_context",
    "log_context",
    "configure_logging",
    "get_logger",
    "CONTEXT_FIELDS",
]
