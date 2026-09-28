"""Shared test kit for the P14 Runtime Slice integration checks.

RUNTIME IDENTITY RULE (§17 / RUNTIME-G-01): runtime integration tests must
connect as ``uap_runtime``. ``uap_migrator``, ``uap_bootstrap``, ``uap_app`` and
the cluster superuser are *never* substituted, otherwise the suite would produce
false-positive security evidence.

CREDENTIAL RULE (DC-7 / DC-9): the runtime credential is **not** stored in this
repository -- not in source, not in a template, not in a fixture. The operator
injects it through ``UAP_RUNTIME_TEST_DSN`` exactly like the migration identity
is injected through ``UAP_MIGRATION_DATABASE_URL``. When the key is absent the
suite SKIPS; it never falls back to ``DATABASE_URL`` or any other identity.

    $env:UAP_RUNTIME_TEST_DSN = "postgresql+psycopg://<role>:<secret>@host:5432/uap_b1_test"

There is deliberately **no cross-identity fallback** in either direction.
"""

from __future__ import annotations

import os
import socket
from urllib.parse import urlsplit

import pytest

#: Environment key carrying the RUNTIME identity for the test suite.
RUNTIME_TEST_DSN_ENV = "UAP_RUNTIME_TEST_DSN"

#: The only role the runtime suite may connect as (RUNTIME-G-01).
REQUIRED_ROLE = "uap_runtime"


class RuntimeDSNError(RuntimeError):
    """Raised when the runtime test identity cannot be established."""


def runtime_test_dsn() -> str:
    """Resolve the runtime-identity DSN, or skip (env-backed, fail-closed)."""
    dsn = os.environ.get(RUNTIME_TEST_DSN_ENV, "").strip()
    if not dsn:
        pytest.skip(
            f"{RUNTIME_TEST_DSN_ENV} is not set: refusing to substitute another "
            f"identity for the runtime integration suite (DC-7 / §17)."
        )

    parts = urlsplit(dsn)
    if parts.username != REQUIRED_ROLE:
        pytest.fail(
            f"{RUNTIME_TEST_DSN_ENV} must name the runtime role "
            f"{REQUIRED_ROLE!r}, got {parts.username!r} "
            f"(false-positive security evidence is banned)."
        )

    try:
        with socket.create_connection(
            (parts.hostname or "localhost", parts.port or 5432), timeout=2.0
        ):
            pass
    except OSError as exc:  # pragma: no cover - depends on infra
        pytest.skip(f"PostgreSQL is not reachable: {exc}")
    return dsn


__all__ = ["RUNTIME_TEST_DSN_ENV", "REQUIRED_ROLE", "RuntimeDSNError", "runtime_test_dsn"]
