"""P16 negative security tests (D07 / section 37): secrets never escape."""

from __future__ import annotations

import pytest

from core.agent import AgentRuntimeError, ErrorCode
from intelligence.gateway.interfaces import AIRequest
from intelligence.providers.interfaces import ProviderRegistry
from services.ai.credentials import EnvSecretResolver
from services.ai.gateway import AIGatewayService, LOG_FIELDS

pytestmark = pytest.mark.security

SECRET = "sk-live-material-123"
PROVIDER = {
    "id": "pr1",
    "key": "openai_compatible",
    "adapter": "openai_compatible",
    "base_url": "http://provider.invalid",
    "config": {},
    "secret_ref": "env:OPENAI_API_KEY",
}
MODEL = {"id": "m1", "model_key": "gpt-x"}


def test_gateway_error_never_contains_secret_or_reference() -> None:
    def _boom(url, headers, payload):
        raise ConnectionError("transport down")

    registry = ProviderRegistry()
    from infrastructure.ai.adapters import OpenAICompatibleAdapter

    registry.register("openai_compatible", OpenAICompatibleAdapter(_boom))
    gateway = AIGatewayService(
        registry=registry, credentials=EnvSecretResolver({"OPENAI_API_KEY": SECRET})
    )
    with pytest.raises(AgentRuntimeError) as exc:
        gateway.complete(AIRequest(prompt="hi", tenant_id="t1"), provider_row=PROVIDER, model_row=MODEL)
    message = str(exc.value)
    assert exc.value.code == ErrorCode.MODEL_REQUEST_FAILED
    assert SECRET not in message and "OPENAI_API_KEY" not in message


def test_request_log_payload_is_whitelisted() -> None:
    recorded: list[dict] = []

    def _transport(url, headers, payload):
        return {"text": "ok", "model": "gpt-x", "usage": {"prompt_tokens": 3, "completion_tokens": 4}}

    registry = ProviderRegistry()
    from infrastructure.ai.adapters import OpenAICompatibleAdapter

    registry.register("openai_compatible", OpenAICompatibleAdapter(_transport))
    gateway = AIGatewayService(
        registry=registry,
        credentials=EnvSecretResolver({"OPENAI_API_KEY": SECRET}),
        recorder=recorded.append,
    )
    gateway.complete(
        AIRequest(prompt="top secret prompt", tenant_id="t1"),
        provider_row=PROVIDER,
        model_row=MODEL,
        correlation={"run_id": "r1"},
    )
    assert recorded, "the recorder must receive a log row"
    row = recorded[0]
    assert set(row) <= set(LOG_FIELDS)
    assert SECRET not in str(row) and "top secret prompt" not in str(row)


def test_missing_credential_denies_before_any_call() -> None:
    called = {"hit": False}

    def _transport(url, headers, payload):
        called["hit"] = True
        return {}

    registry = ProviderRegistry()
    from infrastructure.ai.adapters import OpenAICompatibleAdapter

    registry.register("openai_compatible", OpenAICompatibleAdapter(_transport))
    gateway = AIGatewayService(registry=registry, credentials=EnvSecretResolver({}))
    with pytest.raises(AgentRuntimeError) as exc:
        gateway.complete(AIRequest(prompt="hi"), provider_row=PROVIDER, model_row=MODEL)
    assert exc.value.code == ErrorCode.CREDENTIAL_UNAVAILABLE
    assert called["hit"] is False


def test_agent_runtime_error_never_carries_credentials() -> None:
    error = AgentRuntimeError(ErrorCode.PROVIDER_UNAVAILABLE, "no adapter registered")
    assert SECRET not in str(error)
