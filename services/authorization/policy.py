"""Contextual policy evaluation, risk classification and the approval decision.

A policy is *contextual*: it decides whether an action that is otherwise
granted may proceed in this particular context. A policy may only ever tighten
a decision — a rule that would widen a static grant is not representable here,
because that would be a privilege-escalation surface.

Risk is a classification, not a permission and not a decision. The numeric score
is an internal signal used for policy and approval thresholds only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.permission import LayerOutcome
from core.permission.vocabulary import is_risk_level, normalize_action, risk_rank
from core.policy import PolicyContext, PolicyDecision, RiskSignal

POLICY_VERSION = "authz-policy-v1"

# Risk at or above this level requires human approval, on top of any static tool
# requirement. Approval is an OR of the two, never an AND.
DEFAULT_APPROVAL_RISK = "HIGH"


@dataclass(frozen=True)
class PolicyRule:
    """A single contextual rule.

    ``deny`` and ``require_approval`` restrict; ``allow`` may support an
    otherwise-granted action but can never create a grant by itself.
    """

    policy_id: str
    action: str | None = None
    resource_type: str | None = None
    deny: bool = False
    allow: bool = False
    require_approval: bool = False
    min_risk_level: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class PolicyEvaluation:
    """The policy layer outcome plus the approval signal it produced."""

    outcome: LayerOutcome = LayerOutcome()
    approval_required: bool = False
    failed: bool = False
    policy_version: str | None = None
    risk_level: str = "LOW"
    reasons: tuple[str, ...] = field(default_factory=tuple)


class RiskEvaluator:
    """Classify risk across every signal that applies to a request.

    The classification is the highest applicable tier: an unknown or missing
    signal is never treated as low risk when a higher tier is present.
    """

    def classify(self, *levels: str | None) -> str:
        """Return the highest applicable tier for the given signals.

        An unrecognised non-empty signal escalates to ``CRITICAL`` rather than
        being discarded: dropping it would understate the risk of exactly the
        requests we understand least.
        """
        unknown = [level for level in levels if level is not None and not is_risk_level(level)]
        if unknown:
            return "CRITICAL"
        known = [level for level in levels if is_risk_level(level)]
        if not known:
            return "LOW"
        return max(known, key=risk_rank)

    def signal(self, level: str, reasons: tuple[str, ...] = ()) -> RiskSignal:
        canonical = level if is_risk_level(level) else "CRITICAL"
        return RiskSignal(
            level=canonical,
            score=risk_rank(canonical) / (len(("LOW", "MEDIUM", "HIGH", "CRITICAL")) - 1),
            reasons=reasons,
        )

    def at_least(self, level: str, threshold: str) -> bool:
        return risk_rank(level) >= risk_rank(threshold)


class PolicyEngine:
    """Evaluate a fixed rule set against a context.

    Conditions stored on grants remain storage-only: this engine evaluates rules
    registered here and never interprets stored condition payloads.
    """

    def __init__(
        self,
        rules: tuple[PolicyRule, ...] = (),
        *,
        risk: RiskEvaluator | None = None,
        approval_risk: str = DEFAULT_APPROVAL_RISK,
        version: str = POLICY_VERSION,
    ) -> None:
        self._rules = tuple(rules)
        self._risk = risk or RiskEvaluator()
        self._approval_risk = approval_risk
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    @property
    def rules(self) -> tuple[PolicyRule, ...]:
        return self._rules

    def evaluate(self, context: PolicyContext, risk_level: str | None = None) -> PolicyEvaluation:
        """Evaluate every applicable rule and fold the result.

        Never raises: an unexpected failure is reported as ``failed`` so the
        caller can deny rather than guess.
        """
        try:
            return self._evaluate(context, risk_level)
        except Exception:  # pragma: no cover - defensive, fail closed
            return PolicyEvaluation(failed=True, policy_version=self._version)

    def _evaluate(self, context: PolicyContext, risk_level: str | None) -> PolicyEvaluation:
        deny_reasons: list[str] = []
        allow_reasons: list[str] = []
        approval = False
        reasons: list[str] = []

        action = normalize_action(context.action)
        for rule in self._rules:
            if rule.action is not None and normalize_action(rule.action) != action:
                continue
            if rule.resource_type is not None and context.resource_type is not None:
                if rule.resource_type != context.resource_type:
                    continue

            label = rule.reason or rule.policy_id
            if rule.deny:
                deny_reasons.append(label)
                reasons.append(label)
                continue
            if rule.require_approval:
                approval = True
                reasons.append(f"{label}:approval")
            if rule.allow:
                allow_reasons.append(label)

        effective_risk = self._risk.classify(risk_level, context.risk_level)
        if self._risk.at_least(effective_risk, self._approval_risk):
            approval = True
            reasons.append(f"risk:{effective_risk}")

        if deny_reasons:
            outcome = LayerOutcome(deny=True, reasons=tuple(deny_reasons))
        elif allow_reasons:
            outcome = LayerOutcome(allow=True, reasons=tuple(allow_reasons))
        else:
            outcome = LayerOutcome()

        return PolicyEvaluation(
            outcome=outcome,
            approval_required=approval,
            failed=False,
            policy_version=self._version,
            risk_level=effective_risk,
            reasons=tuple(reasons),
        )

    @staticmethod
    def combine(decisions: list[PolicyDecision]) -> PolicyDecision:
        from core.policy import combine

        return combine(decisions)


def approval_required(*, tool_requires: bool, policy_requires: bool) -> bool:
    """Approval is a static tool requirement **OR** a dynamic policy one.

    Never an AND: either source is sufficient to hold the action for a human.
    """
    return bool(tool_requires) or bool(policy_requires)


__all__ = [
    "DEFAULT_APPROVAL_RISK",
    "POLICY_VERSION",
    "PolicyEngine",
    "PolicyEvaluation",
    "PolicyRule",
    "RiskEvaluator",
    "approval_required",
]
