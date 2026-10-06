"""Provider adapters: transport + credential unwrapping boundary.

The transport is injectable so the vertical slice can be verified without any
network call, and so no vendor SDK becomes a repository dependency. Credentials
are unwrapped here and nowhere else; errors raised from here never include the
credential material, the auth header or a provider response body.

HD-P21-AI-01..04 hardening:
  * the request opener **refuses** every 3xx instead of following it, so a local
    service can never bounce a request to an external host (§12);
  * the protocol mode has no implicit default — an unset mode is a configuration
    error, never a silent ``/responses`` (PREP finding F-P21-LOCAL-AI-01);
  * ``fetch_model_keys`` implements the ``GET {base}/models`` discovery both
    Ollama and LM Studio expose (HD-P21-AI-02).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from typing import Any, Callable, Mapping, Protocol

from core.agent import AgentRuntimeError, ErrorCode
from intelligence.gateway.interfaces import AICompletion, AIProvider, AIRequest
from intelligence.providers.interfaces import ProviderRegistry

#: A transport takes (url, headers, payload) and returns a decoded JSON mapping.
Transport = Callable[[str, Mapping[str, str], Mapping[str, Any]], Mapping[str, Any]]
#: A read transport takes (url, headers) and returns a decoded JSON mapping.
GetTransport = Callable[[str, Mapping[str, str]], Mapping[str, Any]]

#: The only protocol modes the adapter can express (mirrors services.ai.providers.MODES).
MODES = ("responses", "chat-completions")

REQUEST_TIMEOUT_SECONDS = 30.0
DISCOVERY_TIMEOUT_SECONDS = 5.0

#: HD-P21-AI-01..03 §12 — the ONLY hosts a LOCAL provider may ever reach.
LOCAL_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
#: Fixed loopback ports. Server-side constants — never customer input.
LOCAL_PROVIDER_PORTS = {"ollama-local": 11434, "lmstudio-local": 1234}
#: Allowed path suffixes for a LOCAL base URL.
LOCAL_ALLOWED_PATHS = ("", "/", "/v1", "/v1/")


def assert_local_base_url_allowed(provider_key: str, base_url: str) -> None:
    """A LOCAL provider may only reach loopback (HD-P21-AI-01..03 §12).

    Rejects any other host, any other port, userinfo in the URL, a non-http
    scheme and any path other than ``/v1``. This runs BEFORE a request is built,
    so a local flow can never become an SSRF primitive. This lives here — not in
    ``services`` — because URL/transport reasoning belongs to the transport layer
    (``tests/architecture/test_p16_boundaries`` enforces that split).
    """
    expected_port = LOCAL_PROVIDER_PORTS.get(str(provider_key))
    try:
        parts = urlsplit(str(base_url or "").strip())
        port = parts.port
    except ValueError:
        parts, port = None, None
    host = (parts.hostname or "").strip().lower() if parts is not None else ""
    allowed = (
        parts is not None
        and parts.scheme == "http"
        and host in LOCAL_LOOPBACK_HOSTS
        and port == expected_port
        and parts.username is None
        and parts.password is None
        and parts.path in LOCAL_ALLOWED_PATHS
    )
    if not allowed:
        raise AgentRuntimeError(
            ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR,
            "local provider endpoint is not an allowed loopback address",
        )


class ProviderHttpError(ConnectionError):
    """The provider answered with an HTTP status.

    Carries **only** the numeric status (never the header, the key or the response
    body) so the caller can tell "the provider rejected this credential" apart from
    "the network was unreachable" without leaking anything (HD-P21-17 §14).
    """

    def __init__(self, status: int) -> None:
        super().__init__(f"provider http status {int(status)}")
        self.status = int(status)


class ProviderRedirectError(ProviderHttpError):
    """The provider answered with a 3xx. Refused — never followed (§12).

    A redirect is how a hostile (or merely misconfigured) local service would try
    to move the request — and the customer's prompt — onto another host.
    """


class ProviderProtocolError(ConnectionError):
    """A 2xx answer whose body is not the expected OpenAI-compatible JSON object."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse every redirect (HD-P21-AI-01..03 §12)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, D102
        return None


#: One opener, no redirect handler that follows. Module-level so the behaviour is
#: identical for every transport call (including the injectable ones in tests).
NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirect)


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
        mode: str,
    ) -> None:
        if mode not in MODES:
            # Fail-closed: an unset/unknown mode is a configuration error, not a
            # reason to guess 'responses' (PREP finding F-P21-LOCAL-AI-01).
            raise ValueError(f"unsupported provider protocol mode: {mode!r}")
        self._name = name
        self._model_key = model_key
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport
        self._mode = mode

    @property
    def name(self) -> str:
        return self._name

    @property
    def mode(self) -> str:
        return self._mode

    def health(self) -> bool:
        return bool(self._base_url)

    def complete(self, request: AIRequest) -> AICompletion:
        headers: dict[str, str] = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"
        # HD-P21-AI-04: the customer's explicit model wins over the row default.
        model = request.model or self._model_key
        if not model:
            raise ValueError("no model selected for this provider")
        if self._mode == "chat-completions":
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": request.prompt}],
            }
            data = self._transport(f"{self._base_url}/chat/completions", headers, payload)
            choices = data.get("choices") or []
            message = (choices[0] or {}).get("message") if choices else {}
            text = str((message or {}).get("content", ""))
        else:
            payload = {
                "model": model,
                "input": request.prompt,
                "parameters": dict(request.parameters or {}),
            }
            data = self._transport(f"{self._base_url}/responses", headers, payload)
            text = str(data.get("text", ""))
        usage = data.get("usage") or {}
        return AICompletion(
            text=text,
            model=str(data.get("model", model)),
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
            # Mode comes from the server-side provider profile (never from a customer).
            mode=str(config.get("mode") or ""),
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


def _decode(response_body: bytes) -> Mapping[str, Any]:
    try:
        data = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProviderProtocolError("provider answered a non-JSON payload") from exc
    if not isinstance(data, Mapping):
        raise ProviderProtocolError("provider answered a non-object payload")
    return data


def _open(request: urllib.request.Request, timeout: float) -> Mapping[str, Any]:
    """One place decides what an HTTP/transport failure *is* — never what it says."""
    try:
        with NO_REDIRECT_OPENER.open(request, timeout=timeout) as response:  # noqa: S310
            body = response.read()
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
        if 300 <= code < 400:
            raise ProviderRedirectError(code) from exc
        raise ProviderHttpError(code) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        # Deliberately generic: the message must not carry the auth header or body.
        raise ConnectionError("provider transport failed") from exc
    return _decode(body)


def http_json_transport(
    url: str, headers: Mapping[str, str], payload: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Minimal stdlib HTTP POST transport (no vendor SDK). Never echoes credentials."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )
    return _open(request, REQUEST_TIMEOUT_SECONDS)


def http_json_get(url: str, headers: Mapping[str, str]) -> Mapping[str, Any]:
    """Minimal stdlib HTTP GET transport — used only for model discovery."""
    request = urllib.request.Request(url, headers=dict(headers), method="GET")
    return _open(request, DISCOVERY_TIMEOUT_SECONDS)


def fetch_model_keys(
    base_url: str,
    api_key: str | None = None,
    *,
    get: GetTransport | None = None,
) -> list[str]:
    """``GET {base}/models`` -> the model keys the service actually exposes.

    Both Ollama and LM Studio answer with the OpenAI ``{"data":[{"id": ...}]}``
    shape; a bare ``{"models": [...]}`` is also accepted. The result is de-duplicated
    and order-stable so the customer sees a stable list.
    """
    getter = get or http_json_get
    headers: dict[str, str] = {"accept": "application/json"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    data = getter(f"{str(base_url).rstrip('/')}/models", headers)
    raw = data.get("data")
    if raw is None:
        raw = data.get("models")
    if not isinstance(raw, (list, tuple)):
        raise ProviderProtocolError("provider model list is not a list")
    keys: list[str] = []
    seen: set[str] = set()
    for row in raw:
        if isinstance(row, Mapping):
            value = row.get("id") or row.get("name") or row.get("model")
        else:
            value = row
        if isinstance(value, str) and value.strip() and value.strip() not in seen:
            seen.add(value.strip())
            keys.append(value.strip())
    return keys


def register_default_adapters(
    registry: ProviderRegistry, *, transport: Transport | None = None
) -> ProviderRegistry:
    """Register the adapters P16 ships with (echo = offline verification)."""
    registry.register("echo", EchoAdapter())
    registry.register("openai_compatible", OpenAICompatibleAdapter(transport))
    return registry


__all__ = [
    "EchoAdapter",
    "GetTransport",
    "MODES",
    "NO_REDIRECT_OPENER",
    "OpenAICompatibleAdapter",
    "ProviderHttpError",
    "ProviderProtocolError",
    "ProviderRedirectError",
    "Transport",
    "fetch_model_keys",
    "http_json_get",
    "http_json_transport",
    "register_default_adapters",
]
