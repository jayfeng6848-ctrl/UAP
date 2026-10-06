"""AI gateway orchestration (P16-D03 / D04 / D07 · HD-P21-AI-01..04).

Composes: provider row -> adapter (registry) -> credential (resolver) -> LLM
call -> completion. The gateway never touches a database or a vendor SDK; the
caller supplies an optional ``recorder`` for ``ai_request_logs`` and the runtime
performs the actual write.

Credential material stays inside the adapter boundary: the gateway passes a
:class:`~services.ai.credentials.SecretValue`, never a plaintext string it could
log or return.

HD-P21-AI-01..04: the protocol mode is resolved **explicitly** (row config, then
the server-side profile — never an implicit ``responses``), a LOCAL endpoint is
checked against the loopback allowlist before any request is built, and a local
failure maps onto the frozen LOCAL taxonomy instead of a generic cloud failure.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from core.agent import AgentRuntimeError, ErrorCode
from infrastructure.ai.adapters import (
    ProviderHttpError,
    ProviderProtocolError,
    ProviderRedirectError,
    assert_local_base_url_allowed,
)
from intelligence.gateway.interfaces import AICompletion, AIRequest
from intelligence.providers.interfaces import ProviderRegistry

from .credentials import SecretResolver
from .providers import LOCALITY_LOCAL, MODES, get_profile

#: Fields that may be handed to ``ai_request_logs`` (never prompt/secret material).
LOG_FIELDS = (
    "id",
    "run_id",
    "tenant_id",
    "space_id",
    "agent_id",
    "actor_id",
    "provider_id",
    "model_id",
    "capability",
    "classification",
    "status",
    "latency_ms",
    "prompt_tokens",
    "completion_tokens",
)


def _model_request_failed(exc: BaseException) -> AgentRuntimeError:
    """Safe diagnostic only: the exception *class* (never its message) is attached."""
    error = AgentRuntimeError(ErrorCode.MODEL_REQUEST_FAILED, "model request failed")
    error.detail = type(exc).__name__  # type: ignore[attr-defined]
    return error


class AIGatewayService:
    """Resolve a provider, call it, and report a safe completion."""

    def __init__(
        self,
        *,
        registry: ProviderRegistry,
        credentials: SecretResolver,
        recorder: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        self._registry = registry
        self._credentials = credentials
        self._recorder = recorder

    def complete(
        self,
        request: AIRequest,
        *,
        provider_row: Mapping[str, Any],
        model_row: Mapping[str, Any],
        correlation: Mapping[str, Any] | None = None,
    ) -> AICompletion:
        adapter_key = str(provider_row.get("adapter", "")).strip()
        adapter = self._registry.get(adapter_key) if adapter_key else None
        if adapter is None:
            raise AgentRuntimeError(ErrorCode.PROVIDER_UNAVAILABLE, "no adapter registered")

        profile = get_profile(provider_row.get("key"))
        row_config = provider_row.get("config") or {}
        # HD-P21-AI-01..04 §8: no implicit mode. The row's own config wins, then the
        # server-side profile; anything else is a configuration error, not a guess.
        mode = row_config.get("mode") or (profile.mode if profile is not None else None)
        if mode not in MODES:
            raise AgentRuntimeError(
                ErrorCode.PROVIDER_UNAVAILABLE, "provider protocol mode is not configured"
            )
        local = (profile.locality if profile is not None else None) == LOCALITY_LOCAL or str(
            row_config.get("locality") or ""
        ) == LOCALITY_LOCAL
        if local and profile is not None:
            # §12: refuse a non-loopback endpoint before the request exists.
            assert_local_base_url_allowed(profile.key, str(provider_row.get("base_url") or ""))

        secret_ref = provider_row.get("secret_ref")
        secret = self._credentials.resolve(str(secret_ref)) if secret_ref else None

        config = {
            "key": provider_row.get("key"),
            "base_url": provider_row.get("base_url"),
            "config": row_config,
            "secret": secret,
            "model_key": model_row.get("model_key"),
            "mode": mode,
        }
        try:
            provider = adapter.build(config)
        except ValueError as exc:  # adapter-level fail-closed assertion
            raise AgentRuntimeError(
                ErrorCode.PROVIDER_UNAVAILABLE, "provider configuration is not usable"
            ) from exc

        started = time.monotonic()
        try:
            completion = provider.complete(request)
        except AgentRuntimeError:
            raise
        except ProviderRedirectError as exc:
            # A 3xx is refused, never followed (§12) — for a local endpoint that is
            # a protocol violation; for a cloud endpoint it is a transport failure.
            if local:
                raise AgentRuntimeError(
                    ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR, "local provider redirect refused"
                ) from exc
            raise _model_request_failed(exc) from exc
        except ProviderHttpError as exc:
            if local and exc.status in (401, 403):
                raise AgentRuntimeError(
                    ErrorCode.LOCAL_PROVIDER_AUTH_REQUIRED,
                    "local provider requires authentication",
                ) from exc
            raise _model_request_failed(exc) from exc
        except ProviderProtocolError as exc:
            if local:
                raise AgentRuntimeError(
                    ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR,
                    "local provider answered a non OpenAI-compatible payload",
                ) from exc
            raise _model_request_failed(exc) from exc
        except TimeoutError as exc:  # provider-side timeout
            if local:
                raise AgentRuntimeError(
                    ErrorCode.LOCAL_AI_UNAVAILABLE, "local provider timed out"
                ) from exc
            raise AgentRuntimeError(ErrorCode.MODEL_REQUEST_FAILED, "model request timed out") from exc
        except ConnectionError as exc:
            if local:
                raise AgentRuntimeError(
                    ErrorCode.LOCAL_AI_UNAVAILABLE, "local provider is not reachable"
                ) from exc
            raise _model_request_failed(exc) from exc
        except Exception as exc:  # noqa: BLE001 - never surface vendor detail or credentials
            raise _model_request_failed(exc) from exc

        self._record(
            correlation=correlation,
            provider_row=provider_row,
            model_row=model_row,
            completion=completion,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        return completion

    # ------------------------------------------------------------------ helpers
    def _record(
        self,
        *,
        correlation: Mapping[str, Any] | None,
        provider_row: Mapping[str, Any],
        model_row: Mapping[str, Any],
        completion: AICompletion,
        latency_ms: int = 0,
    ) -> None:
        if self._recorder is None:
            return
        payload: dict[str, Any] = dict(correlation or {})
        payload["provider_id"] = provider_row.get("id")
        payload["model_id"] = model_row.get("id")
        payload["status"] = "succeeded"
        payload["latency_ms"] = int(latency_ms)
        payload["prompt_tokens"] = int((completion.usage or {}).get("prompt_tokens", 0))
        payload["completion_tokens"] = int((completion.usage or {}).get("completion_tokens", 0))
        # Whitelisted keys only: a prompt or a credential can never reach the log row.
        self._recorder({key: payload[key] for key in LOG_FIELDS if key in payload})
