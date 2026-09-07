"""Sensitive value redaction for logs and diagnostics.

Anything that looks like a credential is replaced before it reaches a log
record. The redaction is applied to structured field names (precise) and, as a
second net, to values that match well known credential patterns.
"""

from __future__ import annotations

import re
from typing import Any

REDACTED = "***REDACTED***"

#: Field names (case-insensitive, matched as substring) that must never be logged.
SENSITIVE_FIELD_NAMES: tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "credential",
    "authorization",
    "auth_header",
    "session_id",
    "cookie",
    "set-cookie",
    "otp",
    "mfa_code",
    "refresh_token",
)

#: Patterns that look like a credential value regardless of the field name.
SENSITIVE_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),  # OpenAI style keys
    re.compile(r"\bgsk_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),  # Slack tokens
    re.compile(r"\bey[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),  # JWT
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}"),
)


def is_sensitive_field(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in SENSITIVE_FIELD_NAMES)


def redact_value(value: Any) -> Any:
    """Redact a single value if it looks like a credential."""
    if not isinstance(value, str):
        return value
    for pattern in SENSITIVE_VALUE_PATTERNS:
        if pattern.search(value):
            return REDACTED
    return value


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``data`` with sensitive keys and values redacted."""
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        key_str = str(key)
        if is_sensitive_field(key_str):
            cleaned[key_str] = REDACTED
            continue
        cleaned[key_str] = _redact_deep(value)
    return cleaned


def _redact_deep(value: Any) -> Any:
    if isinstance(value, dict):
        return redact_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_redact_deep(item) for item in value]
    return redact_value(value)


def redact_url(url: str | None) -> str | None:
    """Strip credentials from a URL, e.g. ``redis://user:pw@host``."""
    if not url:
        return url
    return re.sub(r"//([^:/@]+):([^@]+)@", r"//\1:***@", url)


__all__ = [
    "REDACTED",
    "SENSITIVE_FIELD_NAMES",
    "is_sensitive_field",
    "redact_value",
    "redact_mapping",
    "redact_url",
]
