"""Provider adapters: transport + credential unwrapping boundary.

The transport is injectable so the vertical slice can be verified without any
network call, and so no vendor SDK becomes a repository dependency. Credentials
are unwrapped here and nowhere else; errors raised from here never include the
credential material, the auth header or a provider response body.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping, Protocol

from intelligence.gateway.interfaces import AICompletion, AIProvider, AIRequest
from intelligence.providers.interfaces import ProviderRegistry

#: A transport takes (url, headers, payload) and returns a decoded JSON mapping.
Transport = Callable[[str, Mapping[str, str], Mapping[str, Any]], Mapping[str, Any]]


class _HttpProvider:
    """Thin provider bound to one transport + one credential."""

    def __init__(
        self,
        *,
        name: str,
        model_key: str,
        base_url: str,
        api_key: str | None,
        transport: Transport,
    ) -> None:
        self._name = name
        self._model_key = model_key
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> bool:
        return bool(self._base_url)

    def complete(self, request: AIRequest) -> AICompletion:
        headers: dict[str, str] = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": request.model or self._model_key,
            "input": request.prompt,
            "parameters": dict(request.parameters or {}),
        }
        data = self._transport(f"{self._base_url}/responses", headers, payload)
        usage = data.get("usage") or {}
        return AICompletion(
            text=str(data.get("text", "")),
            model=str(data.get("model", self._model_key)),
            provider=self._name,
            usage={
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "completion_tokens": int(usage.get("completion_tokens", 0)),
            },
        )


class OpenAICompatibleAdapter:
    """Builds an HTTP provider from configuration (credentials from the resolver)."""

    def __init__(self, transport: Transport | None = None) -> None:
        self._transport = transport or http_json_transport

    def build(self, config: Mapping[str, Any]) -> AIProvider:
        secret = config.get("secret")
        api_key = secret.reveal() if secret is not None else None  # unwrap only here
        return _HttpProvider(
            name=str(config.get("key") or "openai-compatible"),
            model_key=str(config.get("model_key") or ""),
            base_url=str(config.get("base_url") or ""),
            api_key=api_key,
            transport=self._transport,
        )


class EchoAdapter:
    """Deterministic offline adapter used by the vertical slice and unit tests.

    ``proposal`` lets a test declare the tool proposal the model "returns",
    so the ToolGate -> execution half of the chain is exercised without a
    network call.
    """

    def __init__(self, reply: str = "ok", proposal: Mapping[str, Any] | None = None) -> None:
        self._reply = reply
        self._proposal = dict(proposal) if proposal is not None else None

    def build(self, config: Mapping[str, Any]) -> AIProvider:
        reply = self._reply
        proposal = self._proposal  # bound for the nested provider (was an unbound name)
        name = str(config.get("key") or "echo")
        model_key = str(config.get("model_key") or "echo-model")

        class _EchoProvider:
            @property
            def name(self) -> str:
                return name

            def health(self) -> bool:
                return True

            def complete(self, request: AIRequest) -> AICompletion:
                body: dict[str, Any] = {"reply": reply}
                if proposal is not None:
                    body["tools"] = [proposal]
                text = json.dumps(body)
                return AICompletion(
                    text=text,
                    model=request.model or model_key,
                    provider=name,
                    usage={"prompt_tokens": 1, "completion_tokens": 1},
                )

        return _EchoProvider()


def http_json_transport(url: str, headers: Mapping[str, str], payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Minimal stdlib HTTP transport (no vendor SDK). Never echoes credentials."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed scheme
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        # Deliberately generic: the message must not carry the auth header or body.
        raise ConnectionError("provider transport failed") from exc
    return json.loads(body)


def register_default_adapters(registry: ProviderRegistry, *, transport: Transport | None = None) -> ProviderRegistry:
    """Register the adapters P16 ships with (echo = offline verification)."""
    registry.register("echo", EchoAdapter())
    registry.register("openai_compatible", OpenAICompatibleAdapter(transport))
    return registry
