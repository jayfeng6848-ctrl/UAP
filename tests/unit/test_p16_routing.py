"""P16 routing unit tests (D04): deterministic, policy-bounded, no random fallback."""

from __future__ import annotations

import pytest

from core.agent import AgentRuntimeError, ErrorCode
from core.ai import RouteRequest
from services.ai.routing import resolve_route

TENANT = "11111111-1111-1111-1111-111111111111"


def _rows(**overrides):
    policy = {
        "id": "p1",
        "tenant_id": None,
        "space_id": None,
        "name": "platform-default",
        "max_classification": "CONFIDENTIAL",
        "allowed_privacy_tiers": None,
        "denied_providers": None,
        "require_private": False,
        "allow_fallback": False,
        "fallback_preserves_classification": True,
        "redaction_profile": None,
        "enabled": True,
    }
    policy.update(overrides.pop("policy", {}))
    route = {
        "id": "r1",
        "tenant_id": None,
        "space_id": None,
        "capability": "chat",
        "priority": 10,
        "primary_model_id": "m1",
        "fallback_chain": None,
        "enabled": True,
    }
    route.update(overrides.pop("route", {}))
    provider = {
        "id": "pr1",
        "key": "echo",
        "adapter": "echo",
        "base_url": "http://localhost",
        "enabled": True,
        "privacy_tier": "private",
        "max_classification": "CONFIDENTIAL",
        "capabilities": {"chat": True},
        "config": {},
        "secret_ref": None,
    }
    provider.update(overrides.pop("provider", {}))
    model = {
        "id": "m1",
        "provider_id": "pr1",
        "model_key": "echo-1",
        "capabilities": {"chat": True},
        "context_window": 8000,
        "max_output_tokens": 1024,
        "max_classification": "CONFIDENTIAL",
        "is_private": True,
        "enabled": True,
    }
    model.update(overrides.pop("model", {}))
    return {"policies": [policy], "routes": [route], "providers": [provider], "models": [model]}


def test_route_resolves_to_primary_model() -> None:
    decision = resolve_route(
        RouteRequest(capability="chat", classification="INTERNAL", tenant_id=TENANT),
        **_rows(),
    )
    assert (decision.provider_id, decision.model_id, decision.fallback_used) == ("pr1", "m1", False)


def test_classification_above_policy_ceiling_is_denied() -> None:
    with pytest.raises(AgentRuntimeError) as exc:
        resolve_route(
            RouteRequest(capability="chat", classification="HIGHLY_CONFIDENTIAL", tenant_id=TENANT),
            **_rows(),
        )
    assert exc.value.code == ErrorCode.POLICY_DENIED


def test_missing_policy_is_denied() -> None:
    rows = _rows()
    rows["policies"] = [dict(rows["policies"][0], enabled=False)]
    with pytest.raises(AgentRuntimeError) as exc:
        resolve_route(RouteRequest(capability="chat", classification="INTERNAL", tenant_id=TENANT), **rows)
    assert exc.value.code == ErrorCode.POLICY_DENIED


def test_require_private_rejects_non_private_model() -> None:
    with pytest.raises(AgentRuntimeError) as exc:
        resolve_route(
            RouteRequest(
                capability="chat", classification="INTERNAL", tenant_id=TENANT, require_private=True
            ),
            **_rows(model={"is_private": False}, provider={"privacy_tier": "public"}),
        )
    assert exc.value.code == ErrorCode.ROUTE_UNAVAILABLE


def test_denied_provider_is_skipped() -> None:
    with pytest.raises(AgentRuntimeError) as exc:
        resolve_route(
            RouteRequest(capability="chat", classification="INTERNAL", tenant_id=TENANT),
            **_rows(policy={"denied_providers": ["pr1"]}),
        )
    assert exc.value.code == ErrorCode.ROUTE_UNAVAILABLE


def test_fallback_requires_policy_permission() -> None:
    rows = _rows(route={"primary_model_id": "missing", "fallback_chain": ["m2"]})
    rows["models"].append({**rows["models"][0], "id": "m2", "model_key": "echo-2"})
    with pytest.raises(AgentRuntimeError):
        resolve_route(RouteRequest(capability="chat", classification="INTERNAL", tenant_id=TENANT), **rows)

    allowed = _rows(
        route={"primary_model_id": "missing", "fallback_chain": ["m2"]},
        policy={"allow_fallback": True},
    )
    allowed["models"].append({**allowed["models"][0], "id": "m2", "model_key": "echo-2"})
    decision = resolve_route(
        RouteRequest(capability="chat", classification="INTERNAL", tenant_id=TENANT), **allowed
    )
    assert decision.model_id == "m2" and decision.fallback_used is True


def test_route_selection_is_deterministic_by_priority_then_id() -> None:
    rows = _rows()
    rows["routes"] = [
        {**rows["routes"][0], "id": "r-b", "priority": 5, "primary_model_id": "m1"},
        {**rows["routes"][0], "id": "r-a", "priority": 5, "primary_model_id": "m1"},
    ]
    decision = resolve_route(RouteRequest(capability="chat", classification="INTERNAL"), **rows)
    assert decision.route_id == "r-a"
