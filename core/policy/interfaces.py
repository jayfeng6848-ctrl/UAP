"""Policy contracts.

Policies are evaluated *before* an action is executed. They are advisory in
isolation but binding in combination: any policy that denies wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class PolicyContext:
    action: str
    actor_id: str
    tenant_id: str
    space_id: str | None = None
    environment: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    policy_id: str
    reasons: tuple[str, ...] = ()


@runtime_checkable
class PolicyEvaluator(Protocol):
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        ...


@runtime_checkable
class RiskPolicy(Protocol):
    def score(self, context: PolicyContext) -> float:
        """Return a risk score in [0.0, 1.0]."""
        ...


def combine(decisions: list[PolicyDecision]) -> PolicyDecision:
    """Any denial wins; when all allow, report the union of reasons."""
    for decision in decisions:
        if not decision.allowed:
            return decision
    reasons = tuple(r for d in decisions for r in d.reasons)
    return PolicyDecision(allowed=True, policy_id="combined", reasons=reasons)


__all__ = ["PolicyContext", "PolicyDecision", "PolicyEvaluator", "RiskPolicy", "combine"]
