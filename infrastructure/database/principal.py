"""Database principal assertion (P14 Runtime Implementation Wave 1, §14).

The runtime must never assume that the connection identity matches the identity
configured in the DSN. "The application says X" is not evidence; PostgreSQL has
to say X too. The assertion therefore reads ``current_user`` / ``session_user``
from the live connection and compares them with the role named in the URL.

P14 RTA-02: the runtime DSN must target ``uap_runtime``. This module makes that
check enforceable in code instead of relying on configuration review alone.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import make_url

from infrastructure.runtime.errors import PrincipalAssertionError

SELECT_CURRENT_PRINCIPAL = "SELECT current_user, session_user"


def role_from_url(url: str) -> str:
    """Return the role named in a DSN, or raise if it names none."""
    try:
        username = make_url(url).username
    except Exception as exc:  # pragma: no cover - defensive
        raise PrincipalAssertionError("runtime DSN is not parseable") from exc
    if not username:
        raise PrincipalAssertionError("runtime DSN names no database role")
    return str(username)


def assert_connection_principal(
    connection: Any,
    expected_role: str,
    *,
    require_role: str | None = None,
) -> dict[str, str]:
    """Assert the live connection is ``expected_role`` (and ``require_role``).

    Returns ``{"current_user": ..., "session_user": ...}`` for observability.
    Raises :class:`PrincipalAssertionError` (fail-closed) on any mismatch.
    """
    row = connection.execute(text(SELECT_CURRENT_PRINCIPAL)).one()
    current_user, session_user = str(row[0]), str(row[1])

    if current_user != expected_role:
        raise PrincipalAssertionError(
            f"effective database role {current_user!r} does not match the role "
            f"named in the runtime DSN {expected_role!r} "
            f"(session_user={session_user!r})"
        )
    if require_role is not None and current_user != require_role:
        raise PrincipalAssertionError(
            f"runtime requires role {require_role!r} but the connection is "
            f"{current_user!r}"
        )
    return {"current_user": current_user, "session_user": session_user}


__all__ = ["assert_connection_principal", "role_from_url", "SELECT_CURRENT_PRINCIPAL"]
