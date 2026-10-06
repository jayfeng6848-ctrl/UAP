"""Local AI provider discovery (HD-P21-AI-01 / -02 / -03).

LOCAL = the AI service running **on the UAP runtime host**. Discovery is a
server-side operation against a fixed loopback endpoint; the browser never
probes ``localhost`` itself (§13) and the customer never supplies a URL (§12).

The authoritative model list for a local runtime is its own ``GET /v1/models``
(HD-P21-AI-02), not the ``ai_models`` catalog.
"""

from __future__ import annotations

from typing import Any

from core.agent import AgentRuntimeError, ErrorCode
from infrastructure.ai.adapters import (
    GetTransport,
    ProviderHttpError,
    ProviderProtocolError,
    ProviderRedirectError,
    assert_local_base_url_allowed,
    fetch_model_keys,
)

from .providers import LOCALITY_LOCAL, PROVIDER_PROFILES, get_profile

#: The local runtimes this version knows about (server-side constants only).
LOCAL_PROFILES = tuple(p for p in PROVIDER_PROFILES if p.locality == LOCALITY_LOCAL)


def local_provider_list() -> list[dict[str, Any]]:
    """Customer-safe description of the local runtimes UAP can look for."""
    return [
        {
            "key": p.key,
            "display_name": p.display_name,
            "description": p.description,
            "auth": p.auth,
        }
        for p in LOCAL_PROFILES
    ]


def discover_local_models(
    provider_key: str, *, api_key: str | None = None, get: GetTransport | None = None
) -> list[str]:
    """Ask one local runtime which models it actually has installed.

    Every failure maps onto the frozen LOCAL failure taxonomy — never onto a cloud
    code and never onto a silent provider switch.
    """
    profile = get_profile(provider_key)
    if profile is None or profile.locality != LOCALITY_LOCAL:
        raise AgentRuntimeError(ErrorCode.PROVIDER_UNAVAILABLE, "not a local provider")
    assert_local_base_url_allowed(profile.key, profile.base_url)
    try:
        return fetch_model_keys(profile.base_url, api_key, get=get)
    except ProviderRedirectError as exc:  # subclass of ProviderHttpError: check first
        raise AgentRuntimeError(
            ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR, "local provider redirect refused"
        ) from exc
    except ProviderHttpError as exc:
        if exc.status in (401, 403):
            raise AgentRuntimeError(
                ErrorCode.LOCAL_PROVIDER_AUTH_REQUIRED, "local provider requires authentication"
            ) from exc
        raise AgentRuntimeError(
            ErrorCode.LOCAL_AI_UNAVAILABLE, "local provider rejected the model list request"
        ) from exc
    except ProviderProtocolError as exc:
        raise AgentRuntimeError(
            ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR,
            "local provider answered a non OpenAI-compatible payload",
        ) from exc
    except ConnectionError as exc:
        raise AgentRuntimeError(
            ErrorCode.LOCAL_AI_UNAVAILABLE, "local provider is not reachable"
        ) from exc
    except TimeoutError as exc:
        raise AgentRuntimeError(ErrorCode.LOCAL_AI_UNAVAILABLE, "local provider timed out") from exc


def detect_local_providers(*, get: GetTransport | None = None) -> list[dict[str, Any]]:
    """Probe each known local runtime. Never raises: absence is a normal answer."""
    detected: list[dict[str, Any]] = []
    for profile in LOCAL_PROFILES:
        entry: dict[str, Any] = {
            "key": profile.key,
            "display_name": profile.display_name,
            "description": profile.description,
            "auth": profile.auth,
            "available": False,
            "auth_required": False,
            "models": [],
            "error": None,
        }
        try:
            models = discover_local_models(profile.key, get=get)
        except AgentRuntimeError as exc:
            entry["error"] = exc.code
            entry["auth_required"] = exc.code == ErrorCode.LOCAL_PROVIDER_AUTH_REQUIRED
            detected.append(entry)
            continue
        entry["available"] = True
        entry["models"] = models
        if not models:
            entry["error"] = ErrorCode.LOCAL_MODEL_UNAVAILABLE
        detected.append(entry)
    return detected


__all__ = ["LOCAL_PROFILES", "detect_local_providers", "discover_local_models", "local_provider_list"]
