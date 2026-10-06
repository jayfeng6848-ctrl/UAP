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
from typing import Any, Mapping, Protocol, runtime_checkable

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


class ConnectionSecretResolver:
    """Resolve a provider credential from the **per-(actor, tenant)** connection store.

    HD-P21-17 §9/§21/§29: the customer-injected key lives only in the ephemeral
    connection store, scoped to the authenticated actor *and* the authorized
    tenant. A resolver instance is built per run with that scope, so one actor's
    connection can never satisfy another actor's run (no global singleton).

    The optional ``fallback`` keeps the operator/qualification path working exactly
    as before (an existing ``env:<NAME>`` credential), and is only consulted when
    the caller has no active connection of their own.
    """

    def __init__(
        self,
        *,
        actor_id: str,
        tenant_id: str,
        store: Any,
        fallback: SecretResolver | None = None,
    ) -> None:
        self._actor_id = str(actor_id)
        self._tenant_id = str(tenant_id)
        self._store = store
        self._fallback = fallback

    def resolve(self, secret_ref: str) -> SecretValue:
        connection = self._store.get(actor_id=self._actor_id, tenant_id=self._tenant_id)
        if connection is not None and str(connection.secret_ref) == str(secret_ref):
            return SecretValue(connection.api_key(), f"session:{connection.connection_id}")
        if self._fallback is not None:
            return self._fallback.resolve(secret_ref)
        raise AgentRuntimeError(
            ErrorCode.CREDENTIAL_UNAVAILABLE, "no active AI connection for this actor"
        )

    def selected_provider_key(self) -> str | None:
        """The provider this actor's connection selected (None when not connected).

        The agent runtime uses this to run on the provider the customer chose, instead
        of the tenant's default route. Keyed by (actor, tenant) like every other read —
        one customer's selection can never steer another customer's run.
        """
        connection = self._store.get(actor_id=self._actor_id, tenant_id=self._tenant_id)
        return str(connection.provider_key) if connection is not None else None

    def selected_model_key(self) -> str | None:
        """The model this actor's connection explicitly selected (HD-P21-AI-04 §10).

        Provider and model are two independent facts; a connection without an
        explicit model is never completed by a silent first-model pick.
        """
        connection = self._store.get(actor_id=self._actor_id, tenant_id=self._tenant_id)
        if connection is None:
            return None
        return str(connection.model_key or "").strip() or None
