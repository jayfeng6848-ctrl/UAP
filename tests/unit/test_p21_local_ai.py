"""P21 Universal Model Selection + Local AI Provider unit tests.

Offline only (no database, no sockets): the loopback policy, the no-redirect
transport, the explicit provider+model resolution and the frozen LOCAL failure
taxonomy are all pure boundaries and are exercised exactly as shipped.

Coverage map to the Implementation Authorization §22:
  4  provider/model mismatch      7  model switching (store rebinding)
  5  disabled model              8  provider switching (store rebinding)
  2  local model discovery       15 no silent model substitution
  3  model selection            16 no silent provider fallback
  12 invalid local token         25 SSRF / arbitrary URL rejection
  13 credential isolation        26 redirect rejection
"""

from __future__ import annotations

import urllib.error

import pytest

from core.agent import AgentRuntimeError, ErrorCode
from infrastructure.ai import adapters
from infrastructure.ai.adapters import assert_local_base_url_allowed
from intelligence.gateway.interfaces import AIRequest
from intelligence.providers.interfaces import ProviderRegistry
from services.agent.runtime import AgentRuntimeService
from services.ai import local as local_mod
from services.ai.connection import AIConnectionStore
from services.ai.credentials import SecretValue
from services.ai.gateway import AIGatewayService
from services.ai.providers import (
    LOCALITY_CLOUD,
    LOCALITY_LOCAL,
    PROVIDER_PROFILES,
    customer_provider_list,
    get_profile,
)


class _FakeCredentials:
    """Minimal credential boundary: what the runtime asks, and nothing else."""

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self._provider = provider
        self._model = model

    def selected_provider_key(self) -> str | None:
        return self._provider

    def selected_model_key(self) -> str | None:
        return self._model


class _NoopResolver:
    def resolve(self, secret_ref: str) -> SecretValue:
        return SecretValue("test-credential", secret_ref)


class _RaisingAdapter:
    """Adapter whose provider always raises a given transport failure."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def build(self, config: object):  # noqa: ANN201
        exc = self._exc

        class _Provider:
            @property
            def name(self) -> str:
                return "raising"

            def complete(self, request):  # noqa: ANN001, ANN201
                raise exc

        return _Provider()


def _runtime(credentials: _FakeCredentials) -> AgentRuntimeService:
    return AgentRuntimeService(
        database=None, registry=ProviderRegistry(), credentials=credentials
    )


def _gateway(exc: BaseException) -> AIGatewayService:
    registry = ProviderRegistry()
    registry.register("openai_compatible", _RaisingAdapter(exc))
    return AIGatewayService(registry=registry, credentials=_NoopResolver())


_CLOUD_ROW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "key": "deepseek",
    "adapter": "openai_compatible",
    "base_url": "https://api.deepseek.com",
    "enabled": True,
    "privacy_tier": "public",
    "max_classification": "INTERNAL",
    "capabilities": None,
    "config": {"mode": "chat-completions"},
    "secret_ref": "env:UAP_AI_API_KEY_DEEPSEEK",
}
_LOCAL_ROW = {
    "id": None,
    "key": "ollama-local",
    "adapter": "openai_compatible",
    "base_url": "http://127.0.0.1:11434/v1",
    "enabled": True,
    "privacy_tier": "self_hosted",
    "max_classification": "HIGHLY_CONFIDENTIAL",
    "capabilities": None,
    "config": {"mode": "chat-completions", "protocol": "openai-compatible", "locality": "local"},
    "secret_ref": None,
}


# --------------------------------------------------------------- loopback policy
@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:11434/v1",
        "http://localhost:11434/v1",
        "http://[::1]:11434/v1",
    ],
)
def test_loopback_endpoints_are_allowed(base_url: str) -> None:
    assert_local_base_url_allowed("ollama-local", base_url)


@pytest.mark.parametrize(
    "base_url",
    [
        "http://192.168.1.5:11434/v1",  # RFC1918
        "http://10.0.0.9:11434/v1",  # RFC1918
        "http://169.254.169.254:11434/v1",  # link-local / cloud metadata
        "http://100.64.0.7:11434/v1",  # CGNAT
        "http://0.0.0.0:11434/v1",
        "http://example.com:11434/v1",  # arbitrary hostname
        "http://127.0.0.1:1234/v1",  # wrong port for this provider
        "https://127.0.0.1:11434/v1",  # non-http scheme
        "http://user:pass@127.0.0.1:11434/v1",  # userinfo
        "http://127.0.0.1:11434/other",  # unexpected path
        "http://127.0.0.1:11434/v1/../../evil",  # traversal-ish suffix
        "http://127.0.0.1:11434@evil.example.com/v1",  # userinfo spoof
    ],
)
def test_ssrf_shaped_endpoints_are_rejected(base_url: str) -> None:
    with pytest.raises(AgentRuntimeError) as exc:
        assert_local_base_url_allowed("ollama-local", base_url)
    assert exc.value.code == ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR


def test_local_profiles_are_loopback_only_and_credentialless() -> None:
    for profile in PROVIDER_PROFILES:
        if profile.locality != LOCALITY_LOCAL:
            continue
        assert profile.secret_ref is None
        assert profile.auth in ("none", "optional")
        assert_local_base_url_allowed(profile.key, profile.base_url)


def test_customer_provider_list_has_no_endpoint_or_model() -> None:
    for entry in customer_provider_list():
        assert set(entry) == {"key", "display_name", "description", "locality", "auth"}
        assert "http" not in str(entry["description"])


# ------------------------------------------------------------ transport hardening
def test_transport_refuses_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    def _redirect(request, timeout=None):  # noqa: ANN001, ANN202
        raise urllib.error.HTTPError(request.full_url, 302, "Found", {}, None)

    monkeypatch.setattr(adapters.NO_REDIRECT_OPENER, "open", _redirect)
    with pytest.raises(adapters.ProviderRedirectError) as exc:
        adapters.http_json_get("http://127.0.0.1:11434/v1/models", {})
    assert exc.value.status == 302


def test_transport_maps_http_status_and_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _unauthorized(request, timeout=None):  # noqa: ANN001, ANN202
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(adapters.NO_REDIRECT_OPENER, "open", _unauthorized)
    with pytest.raises(adapters.ProviderHttpError) as exc:
        adapters.http_json_get("http://127.0.0.1:11434/v1/models", {})
    assert exc.value.status == 401

    def _unreachable(request, timeout=None):  # noqa: ANN001, ANN202
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(adapters.NO_REDIRECT_OPENER, "open", _unreachable)
    with pytest.raises(ConnectionError) as net:
        adapters.http_json_get("http://127.0.0.1:11434/v1/models", {})
    assert not isinstance(net.value, adapters.ProviderHttpError)
    assert "connection refused" not in str(net.value)


def test_protocol_mode_has_no_implicit_default() -> None:
    adapter = adapters.OpenAICompatibleAdapter(transport=lambda url, headers, payload: {})
    with pytest.raises(ValueError):
        adapter.build({"key": "ollama-local", "base_url": "http://127.0.0.1:11434/v1"})
    # 'responses' must never be inferred from an absent mode.
    with pytest.raises(ValueError):
        adapter.build(
            {"key": "ollama-local", "base_url": "http://127.0.0.1:11434/v1", "mode": "rsp"}
        )


def test_local_request_sends_no_authorization_header() -> None:
    seen: dict[str, object] = {}

    def _transport(url, headers, payload):  # noqa: ANN001, ANN202
        seen["headers"] = dict(headers)
        seen["url"] = url
        return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    provider = adapters.OpenAICompatibleAdapter(transport=_transport).build(
        {
            "key": "ollama-local",
            "base_url": "http://127.0.0.1:11434/v1",
            "mode": "chat-completions",
            "model_key": "qwen3:8b",
        }
    )
    completion = provider.complete(AIRequest(prompt="hi", model="qwen3:8b"))
    assert completion.text == "ok"
    assert "authorization" not in seen["headers"]
    assert seen["url"] == "http://127.0.0.1:11434/v1/chat/completions"


def test_fetch_model_keys_parses_and_dedupes() -> None:
    def _get(url, headers):  # noqa: ANN001, ANN202
        assert url.endswith("/v1/models")
        return {"object": "list", "data": [{"id": "a"}, {"id": "b"}, {"id": "a"}]}

    assert adapters.fetch_model_keys("http://127.0.0.1:11434/v1", get=_get) == ["a", "b"]

    def _get_named(url, headers):  # noqa: ANN001, ANN202
        return {"models": [{"name": "x"}, "y"]}

    assert adapters.fetch_model_keys("http://127.0.0.1:11434/v1", get=_get_named) == ["x", "y"]


def test_fetch_model_keys_rejects_non_list_payload() -> None:
    with pytest.raises(adapters.ProviderProtocolError):
        adapters.fetch_model_keys("http://127.0.0.1:11434/v1", get=lambda url, headers: {"data": "nope"})


# --------------------------------------------------------------- local discovery
def test_discovery_maps_every_failure_to_the_local_taxonomy() -> None:
    def _ok(url, headers):  # noqa: ANN001, ANN202
        return {"data": [{"id": "m1"}]}

    assert local_mod.discover_local_models("ollama-local", get=_ok) == ["m1"]

    def _auth(url, headers):  # noqa: ANN001, ANN202
        raise adapters.ProviderHttpError(401)

    with pytest.raises(AgentRuntimeError) as auth:
        local_mod.discover_local_models("lmstudio-local", get=_auth)
    assert auth.value.code == ErrorCode.LOCAL_PROVIDER_AUTH_REQUIRED

    def _redirect(url, headers):  # noqa: ANN001, ANN202
        raise adapters.ProviderRedirectError(302)

    with pytest.raises(AgentRuntimeError) as redirect:
        local_mod.discover_local_models("ollama-local", get=_redirect)
    assert redirect.value.code == ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR

    def _unreachable(url, headers):  # noqa: ANN001, ANN202
        raise ConnectionError("provider transport failed")

    with pytest.raises(AgentRuntimeError) as down:
        local_mod.discover_local_models("ollama-local", get=_unreachable)
    assert down.value.code == ErrorCode.LOCAL_AI_UNAVAILABLE


def test_detection_reports_absence_without_raising() -> None:
    def _down(url, headers):  # noqa: ANN001, ANN202
        raise ConnectionError("provider transport failed")

    detected = {entry["key"]: entry for entry in local_mod.detect_local_providers(get=_down)}
    assert set(detected) == {"ollama-local", "lmstudio-local"}
    assert all(entry["available"] is False for entry in detected.values())
    assert all(entry["error"] == ErrorCode.LOCAL_AI_UNAVAILABLE for entry in detected.values())


def test_detection_reports_models_and_empty_catalog() -> None:
    def _with_models(url, headers):  # noqa: ANN001, ANN202
        return {"data": [{"id": "qwen3:8b"}]}

    entry = next(
        item
        for item in local_mod.detect_local_providers(get=_with_models)
        if item["key"] == "ollama-local"
    )
    assert entry["available"] is True
    assert entry["models"] == ["qwen3:8b"]
    assert entry["error"] is None

    def _empty(url, headers):  # noqa: ANN001, ANN202
        return {"data": []}

    empty = next(
        item
        for item in local_mod.detect_local_providers(get=_empty)
        if item["key"] == "ollama-local"
    )
    assert empty["available"] is True
    assert empty["error"] == ErrorCode.LOCAL_MODEL_UNAVAILABLE


# ------------------------------------------------------------------- gateway map
def test_gateway_maps_local_auth_failure_and_keeps_cloud_behaviour() -> None:
    request = AIRequest(prompt="hi", model="m")
    with pytest.raises(AgentRuntimeError) as local:
        _gateway(adapters.ProviderHttpError(403)).complete(
            request, provider_row=_LOCAL_ROW, model_row={"id": None, "model_key": "m"}
        )
    assert local.value.code == ErrorCode.LOCAL_PROVIDER_AUTH_REQUIRED

    with pytest.raises(AgentRuntimeError) as cloud:
        _gateway(adapters.ProviderHttpError(403)).complete(
            request, provider_row=_CLOUD_ROW, model_row={"id": "m-1", "model_key": "m"}
        )
    assert cloud.value.code == ErrorCode.MODEL_REQUEST_FAILED
    assert getattr(cloud.value, "detail", None) == "ProviderHttpError"


def test_gateway_refuses_local_redirect_and_off_loopback_endpoint() -> None:
    request = AIRequest(prompt="hi", model="m")
    with pytest.raises(AgentRuntimeError) as redirect:
        _gateway(adapters.ProviderRedirectError(302)).complete(
            request, provider_row=_LOCAL_ROW, model_row={"id": None, "model_key": "m"}
        )
    assert redirect.value.code == ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR

    hostile = dict(_LOCAL_ROW, base_url="http://192.168.1.5:11434/v1")
    with pytest.raises(AgentRuntimeError) as ssrf:
        _gateway(adapters.ProviderHttpError(500)).complete(
            request, provider_row=hostile, model_row={"id": None, "model_key": "m"}
        )
    assert ssrf.value.code == ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR


def test_gateway_requires_an_explicit_mode() -> None:
    row = dict(_CLOUD_ROW, key="unknown-provider", config={})
    with pytest.raises(AgentRuntimeError) as exc:
        _gateway(adapters.ProviderHttpError(500)).complete(
            AIRequest(prompt="hi", model="m"), provider_row=row, model_row={"id": "m", "model_key": "m"}
        )
    assert exc.value.code == ErrorCode.PROVIDER_UNAVAILABLE


# ------------------------------------------------------- explicit target resolve
def _catalog() -> tuple[dict[str, dict], dict[str, dict]]:
    providers = {_CLOUD_ROW["id"]: dict(_CLOUD_ROW)}
    models = {
        "m-deepseek": {
            "id": "22222222-2222-2222-2222-222222222222",
            "provider_id": _CLOUD_ROW["id"],
            "model_key": "deepseek-chat",
            "enabled": True,
        },
        "m-qwen-off": {
            "id": "33333333-3333-3333-3333-333333333333",
            "provider_id": "99999999-9999-9999-9999-999999999999",
            "model_key": "qwen-plus",
            "enabled": True,
        },
        "m-deepseek-off": {
            "id": "44444444-4444-4444-4444-444444444444",
            "provider_id": _CLOUD_ROW["id"],
            "model_key": "deepseek-reasoner",
            "enabled": False,
        },
    }
    return providers, models


def test_explicit_target_resolves_provider_and_model() -> None:
    providers, models = _catalog()
    runtime = _runtime(_FakeCredentials("deepseek", "deepseek-chat"))
    provider_row, model_row = runtime._explicit_target(
        preferred_provider="deepseek", providers=providers, models=models
    )
    assert provider_row["key"] == "deepseek"
    assert model_row["model_key"] == "deepseek-chat"


def test_explicit_target_never_substitutes_a_model() -> None:
    providers, models = _catalog()
    # A disabled model under the right provider is unavailable, not replaced.
    with pytest.raises(AgentRuntimeError) as disabled:
        _runtime(_FakeCredentials("deepseek", "deepseek-reasoner"))._explicit_target(
            preferred_provider="deepseek", providers=providers, models=models
        )
    assert disabled.value.code == ErrorCode.MODEL_UNAVAILABLE
    # A model that exists under another provider is a mismatch, not a fallback.
    with pytest.raises(AgentRuntimeError) as mismatch:
        _runtime(_FakeCredentials("deepseek", "qwen-plus"))._explicit_target(
            preferred_provider="deepseek", providers=providers, models=models
        )
    assert mismatch.value.code == ErrorCode.MODEL_PROVIDER_MISMATCH
    # Provider-only is never a complete connection (§5).
    with pytest.raises(AgentRuntimeError) as inexplicit:
        _runtime(_FakeCredentials("deepseek", None))._explicit_target(
            preferred_provider="deepseek", providers=providers, models=models
        )
    assert inexplicit.value.code == ErrorCode.MODEL_UNAVAILABLE


def test_explicit_target_never_falls_back_to_another_provider() -> None:
    providers, models = _catalog()
    with pytest.raises(AgentRuntimeError) as exc:
        _runtime(_FakeCredentials("openai", "gpt-4o-mini"))._explicit_target(
            preferred_provider="openai", providers=providers, models=models
        )
    assert exc.value.code == ErrorCode.PROVIDER_UNAVAILABLE


def test_local_explicit_target_uses_discovery_not_the_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    providers, models = _catalog()
    monkeypatch.setattr(
        "services.agent.runtime.discover_local_models", lambda key: ["qwen3:8b", "llama3:8b"]
    )
    provider_row, model_row = _runtime(_FakeCredentials("ollama-local", "qwen3:8b"))._explicit_target(
        preferred_provider="ollama-local", providers=providers, models=models
    )
    assert provider_row["key"] == "ollama-local"
    assert provider_row["secret_ref"] is None
    assert model_row["id"] is None  # no persistent Local ai_models row (HD-P21-AI-03)
    assert model_row["model_key"] == "qwen3:8b"

    with pytest.raises(AgentRuntimeError) as missing:
        _runtime(_FakeCredentials("ollama-local", "ghost:1b"))._explicit_target(
            preferred_provider="ollama-local", providers=providers, models=models
        )
    assert missing.value.code == ErrorCode.LOCAL_MODEL_NOT_FOUND


# ---------------------------------------------------------- connection binding
def test_connection_binds_provider_and_model_and_rebinds_on_switch() -> None:
    store = AIConnectionStore(ttl_seconds=60)
    store.put(
        actor_id="a",
        tenant_id="t",
        provider_key="deepseek",
        model_key="deepseek-chat",
        api_key="k1",
        secret_ref="env:UAP_AI_API_KEY_DEEPSEEK",
    )
    assert store.describe(actor_id="a", tenant_id="t")["model"] == "deepseek-chat"

    # §19/§20: switching provider+model rebinds the whole tuple, no stale state.
    store.put(
        actor_id="a",
        tenant_id="t",
        provider_key="ollama-local",
        model_key="qwen3:8b",
        api_key="",
        secret_ref="local:no-credential",
    )
    status = store.describe(actor_id="a", tenant_id="t")
    assert status["provider"] == "ollama-local"
    assert status["model"] == "qwen3:8b"
    assert store.get(actor_id="a", tenant_id="t").api_key() == ""
    # A different actor never sees this connection (§13 credential isolation).
    assert store.get(actor_id="b", tenant_id="t") is None


def test_connection_expiry_clears_the_model_binding() -> None:
    store = AIConnectionStore(ttl_seconds=0)
    store.put(
        actor_id="a",
        tenant_id="t",
        provider_key="deepseek",
        model_key="deepseek-chat",
        api_key="k",
        secret_ref="env:X",
    )
    assert store.describe(actor_id="a", tenant_id="t") == {
        "connected": False,
        "provider": None,
        "model": None,
        "expires_at": None,
    }


def test_cloud_and_local_profiles_stay_distinct() -> None:
    assert get_profile("deepseek").locality == LOCALITY_CLOUD
    assert get_profile("ollama-local").locality == LOCALITY_LOCAL
    assert get_profile("lmstudio-local").auth == "optional"
    assert get_profile("ollama-local").auth == "none"
