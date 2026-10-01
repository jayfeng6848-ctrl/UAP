"""Credential resolution boundary (P16-D07).

``secret_ref`` is an opaque reference, never a secret. The only supported shape
in this stage is ``env:<NAME>``, resolved from the runtime environment.

The resolved value is wrapped in :class:`SecretValue`, whose ``str``/``repr``
are redacted so the material cannot reach a log line, an exception message, an
audit row or an event payload by accident. Only the provider adapter (inside
``infrastructure``) unwraps it.
"""

from __future__ import annotations

import os
from typing import Mapping, Protocol, runtime_checkable

from core.agent import AgentRuntimeError, ErrorCode

ENV_SCHEME = "env:"
REDACTED = "<redacted>"


class SecretValue:
    """Opaque secret material. Safe to print; unwrapping is explicit."""

    __slots__ = ("_value", "ref")

    def __init__(self, value: str, ref: str) -> None:
        self._value = value
        self.ref = ref

    def reveal(self) -> str:
        """Return the material. Only provider adapters may call this."""
        return self._value

    def __repr__(self) -> str:
        return f"SecretValue({self.ref!r}, {REDACTED})"

    __str__ = __repr__


@runtime_checkable
class SecretResolver(Protocol):
    def resolve(self, secret_ref: str) -> SecretValue:
        ...


class EnvSecretResolver:
    """Resolve ``env:<NAME>`` references from an environment mapping."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = os.environ if environ is None else environ

    def resolve(self, secret_ref: str) -> SecretValue:
        ref = (secret_ref or "").strip()
        if not ref.startswith(ENV_SCHEME) or len(ref) == len(ENV_SCHEME):
            # Never echo the reference back: it may itself be sensitive metadata.
            raise AgentRuntimeError(ErrorCode.CREDENTIAL_UNAVAILABLE, "unsupported secret reference")
        name = ref[len(ENV_SCHEME) :]
        value = self._environ.get(name)
        if not value:
            raise AgentRuntimeError(ErrorCode.CREDENTIAL_UNAVAILABLE, "referenced credential is absent")
        return SecretValue(value, ref)
