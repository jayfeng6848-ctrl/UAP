"""Policy contracts.

Policies are evaluated *before* an action is executed. They are advisory in
isolation but binding in combination: any policy that denies wins. A policy may
only ever *tighten* the decision — it can never widen a static grant, otherwise
it would become a privilege-escalation surface.

The policy context carries the base delegation context (actor and delegator) so
that ``agent`` / ``actor`` / ``delegator`` stay distinguishable in both the
decision and the audit trail.
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
    # Base delegation context (the full delegation lifecycle is deferred).
    subject_id: str | None = None
    subject_type: str | None = None
    delegator_id: str | None = None
    # Resource context.
    resource_type: str | None = None
    resource_id: str | None = None
    scope: str | None = None
    # Evaluation metadata.
    risk_level: str | None = None
    request_id: str | None = None
    policy_version: str | None = None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    policy_id: str
    reasons: tuple[str, ...] = ()
    policy_version: str | None = None


@dataclass(frozen=True)
class RiskSignal:
    """An *internal* risk signal.

    A numeric score is a calculation input only: the canonical, externally
    visible risk vocabulary is the four-tier classification, and risk is never
    itself a permission or an authorization decision.
    """

    level: str
    score: float
    reasons: tuple[str, ...] = ()


@runtime_checkable
class PolicyEvaluator(Protocol):
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        ...


@runtime_checkable
class RiskPolicy(Protocol):
    def score(self, context: PolicyContext) -> float:
        """Return an internal risk score in [0.0, 1.0]."""
        ...


def combine(decisions: list[PolicyDecision]) -> PolicyDecision:
    """Any denial wins; when all allow, report the union of reasons.

    An empty list abstains: it reports "no policy denied" without inventing an
    allow. Callers combine that with the RBAC/ACL layers.
    """
    for decision in decisions:
        if not decision.allowed:
            return decision
    reasons = tuple(r for d in decisions for r in d.reasons)
    policy_version = next(
        (d.policy_version for d in decisions if d.policy_version is not None), None
    )
    return PolicyDecision(
        allowed=True,
        policy_id="combined",
        reasons=reasons,
        policy_version=policy_version,
    )


__all__ = [
    "PolicyContext",
    "PolicyDecision",
    "PolicyEvaluator",
    "RiskPolicy",
    "RiskSignal",
    "combine",
]
