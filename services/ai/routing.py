"""Deterministic model routing (P16-D04).

    Task -> Capability -> Policy -> Route -> Provider -> Model

Pure function over plain rows: no I/O, no vendor detail, no randomness. Every
rejection is a frozen error code; fallback happens only when the policy allows
it and never silently changes classification.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from core.agent import AgentRuntimeError, ErrorCode
from core.ai import RouteDecision, RouteRequest
from core.resource.interfaces import CLASSIFICATIONS

CLASSIFICATION_RANK: dict[str, int] = {name: rank for rank, name in enumerate(CLASSIFICATIONS)}

#: Mirrors ``ck_ai_providers_privacy_tier`` (public < vetted < private < self_hosted).
PRIVACY_TIERS = ("public", "vetted", "private", "self_hosted")
PRIVATE_TIERS = frozenset({"private", "self_hosted"})


def _rank(classification: str) -> int:
    return CLASSIFICATION_RANK.get(classification, len(CLASSIFICATIONS))


def _capabilities(row: Mapping[str, Any]) -> set[str]:
    raw = row.get("capabilities")
    if isinstance(raw, Mapping):
        return {str(k) for k, v in raw.items() if v}
    if isinstance(raw, (list, tuple, set)):
        return {str(item) for item in raw}
    return set()


def _fallback_models(route: Mapping[str, Any]) -> list[str]:
    """Fallback chain = explicit ordered list of model ids (strings or dicts)."""
    raw = route.get("fallback_chain")
    out: list[str] = []
    if isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, Mapping) and item.get("model_id"):
                out.append(str(item["model_id"]))
    return out


def _scope_match(row: Mapping[str, Any], request: RouteRequest) -> bool:
    tenant = row.get("tenant_id")
    space = row.get("space_id")
    if tenant is not None and str(tenant) != str(request.tenant_id):
        return False
    if space is not None and str(space) != str(request.space_id):
        return False
    return True


def _specificity(row: Mapping[str, Any]) -> tuple[int, int, str]:
    tenant = 1 if row.get("tenant_id") is not None else 0
    space = 1 if row.get("space_id") is not None else 0
    return (-(tenant + space), 0, str(row.get("id", "")))


def _select_policy(policies: Iterable[Mapping[str, Any]], request: RouteRequest) -> Mapping[str, Any] | None:
    candidates = [
        row for row in policies if bool(row.get("enabled")) and _scope_match(row, request)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=_specificity)[0]


def _provider_ok(
    provider: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    request: RouteRequest,
    require_private: bool,
) -> bool:
    if not bool(provider.get("enabled")):
        return False
    allowed = policy.get("allowed_privacy_tiers")
    if isinstance(allowed, (list, tuple)) and provider.get("privacy_tier") not in allowed:
        return False
    if _rank(str(provider.get("max_classification", ""))) < _rank(request.classification):
        return False
    denied = policy.get("denied_providers") or []
    if isinstance(denied, (list, tuple)) and str(provider.get("id")) in {str(d) for d in denied}:
        return False
    if require_private and str(provider.get("privacy_tier")) not in PRIVATE_TIERS:
        return False
    return True


def _model_ok(
    model: Mapping[str, Any],
    *,
    request: RouteRequest,
    require_private: bool,
    capability: str,
) -> bool:
    if not bool(model.get("enabled")):
        return False
    if capability and capability not in _capabilities(model):
        return False
    if _rank(str(model.get("max_classification", ""))) < _rank(request.classification):
        return False
    if require_private and not bool(model.get("is_private")):
        return False
    return True


def resolve_route(
    request: RouteRequest,
    *,
    policies: Sequence[Mapping[str, Any]],
    routes: Sequence[Mapping[str, Any]],
    providers: Sequence[Mapping[str, Any]],
    models: Sequence[Mapping[str, Any]],
) -> RouteDecision:
    """Resolve one deterministic route, or raise a frozen error code."""
    if request.classification not in CLASSIFICATION_RANK:
        raise AgentRuntimeError(ErrorCode.POLICY_DENIED, "unknown classification")

    policy = _select_policy(policies, request)
    if policy is None:
        raise AgentRuntimeError(ErrorCode.POLICY_DENIED, "no applicable policy")
    if _rank(request.classification) > _rank(str(policy.get("max_classification", ""))):
        raise AgentRuntimeError(ErrorCode.POLICY_DENIED, "classification exceeds policy ceiling")

    require_private = bool(request.require_private) or bool(policy.get("require_private"))
    allow_fallback = bool(policy.get("allow_fallback"))
    fallback_preserves = bool(policy.get("fallback_preserves_classification"))

    providers_by_id = {str(p.get("id")): p for p in providers}
    models_by_id = {str(m.get("id")): m for m in models}

    candidates = [
        row
        for row in routes
        if bool(row.get("enabled"))
        and str(row.get("capability")) == request.capability
        and _scope_match(row, request)
    ]
    if not candidates:
        raise AgentRuntimeError(ErrorCode.ROUTE_UNAVAILABLE, "no enabled route for capability")
    candidates.sort(key=lambda row: (int(row.get("priority", 0)), str(row.get("id", ""))))

    for route in candidates:
        primary = str(route.get("primary_model_id"))
        chain = [primary] + _fallback_models(route)
        for index, model_id in enumerate(chain):
            if index > 0 and not (allow_fallback and fallback_preserves):
                break
            model = models_by_id.get(str(model_id))
            if model is None:
                continue
            provider = providers_by_id.get(str(model.get("provider_id")))
            if provider is None:
                continue
            if not _provider_ok(provider, policy=policy, request=request, require_private=require_private):
                continue
            if not _model_ok(
                model,
                request=request,
                require_private=require_private,
                capability=request.capability,
            ):
                continue
            return RouteDecision(
                route_id=str(route.get("id")),
                provider_id=str(provider.get("id")),
                model_id=str(model.get("id")),
                capability=request.capability,
                classification=request.classification,
                fallback_used=index > 0,
                fallback_index=index,
            )

    raise AgentRuntimeError(ErrorCode.ROUTE_UNAVAILABLE, "no eligible provider/model for route")
