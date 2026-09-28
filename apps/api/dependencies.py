"""FastAPI dependencies.

Transport-level accessors only: no SQL, no authorization decision, no business
rule. The runtime database boundary is built once by the application lifespan
(Wave 1 ``RuntimeApplication``) and reused here.
"""

from __future__ import annotations

from fastapi import Request

from infrastructure.database.runtime import RuntimeDatabase
from infrastructure.runtime.lifecycle import LifecycleState, RuntimeApplication


def get_runtime(request: Request) -> RuntimeApplication:
    runtime: RuntimeApplication | None = getattr(request.app.state, "runtime", None)
    if runtime is None or runtime.state is not LifecycleState.STARTED:
        raise RuntimeError("runtime application is not started")
    return runtime


def get_database(request: Request) -> RuntimeDatabase:
    return get_runtime(request).database


def bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header:
        return None
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


__all__ = ["bearer_token", "get_database", "get_runtime"]
