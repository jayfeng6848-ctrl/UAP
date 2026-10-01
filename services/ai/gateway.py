"""AI gateway orchestration (P16-D03 / D04 / D07).

Composes: provider row -> adapter (registry) -> credential (resolver) -> LLM
call -> completion. The gateway never touches a database or a vendor SDK; the
caller supplies an optional ``recorder`` for ``ai_request_logs`` and the runtime
performs the actual write.

Credential material stays inside the adapter boundary: the gateway passes a
:class:`~services.ai.credentials.SecretValue`, never a plaintext string it could
log or return.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from core.agent import AgentRuntimeError, ErrorCode
from intelligence.gateway.interfaces import AICompletion, AIRequest
from intelligence.providers.interfaces import ProviderRegistry

from .credentials import SecretResolver

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

        secret_ref = provider_row.get("secret_ref")
        secret = self._credentials.resolve(str(secret_ref)) if secret_ref else None

        config = {
            "key": provider_row.get("key"),
            "base_url": provider_row.get("base_url"),
            "config": provider_row.get("config") or {},
            "secret": secret,
            "model_key": model_row.get("model_key"),
        }
        provider = adapter.build(config)

        started = time.monotonic()
        try:
            completion = provider.complete(request)
        except AgentRuntimeError:
            raise
        except TimeoutError as exc:  # provider-side timeout
            raise AgentRuntimeError(ErrorCode.MODEL_REQUEST_FAILED, "model request timed out") from exc
        except Exception as exc:  # noqa: BLE001 - never surface vendor detail or credentials
            # Safe diagnostic only: the exception *class* (never its message) is
            # attached so the runtime can persist a classification without leaking.
            error = AgentRuntimeError(ErrorCode.MODEL_REQUEST_FAILED, "model request failed")
            error.detail = type(exc).__name__  # type: ignore[attr-defined]
            raise error from exc

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
