"""Policy, risk and approval.

A policy is contextual: it may restrict an otherwise-granted action and may add
an approval requirement, but it can never originate a grant. Risk is a
classification, not a permission and not a decision. Approval is an OR of a
static tool requirement and a dynamic policy requirement — never an AND.
"""

from __future__ import annotations

import pytest

from core.policy import PolicyContext
from services.authorization.policy import (
    DEFAULT_APPROVAL_RISK,
    PolicyEngine,
    PolicyRule,
    RiskEvaluator,
    approval_required,
)


def _context(**overrides) -> PolicyContext:
    base = {"action": "execute", "actor_id": "u1", "tenant_id": "t1"}
    base.update(overrides)
    return PolicyContext(**base)


def test_an_empty_rule_set_abstains_without_approval() -> None:
    result = PolicyEngine().evaluate(_context())
    assert result.outcome.allow is False
    assert result.outcome.deny is False
    assert result.approval_required is False
    assert result.failed is False


def test_a_deny_rule_denies() -> None:
    engine = PolicyEngine((PolicyRule(policy_id="p1", action="execute", deny=True),))
    result = engine.evaluate(_context())
    assert result.outcome.deny is True
    assert "p1" in result.outcome.reasons


def test_a_deny_rule_does_not_leak_to_other_actions() -> None:
    engine = PolicyEngine((PolicyRule(policy_id="p1", action="delete", deny=True),))
    assert engine.evaluate(_context(action="read")).outcome.deny is False


def test_an_allow_rule_reports_allow_but_cannot_grant_alone() -> None:
    engine = PolicyEngine((PolicyRule(policy_id="p1", allow=True),))
    result = engine.evaluate(_context())
    assert result.outcome.allow is True


def test_an_approval_rule_requests_approval() -> None:
    engine = PolicyEngine((PolicyRule(policy_id="p1", require_approval=True),))
    assert engine.evaluate(_context()).approval_required is True


def test_deny_and_approval_can_coexist_and_deny_wins() -> None:
    engine = PolicyEngine(
        (
            PolicyRule(policy_id="deny", deny=True),
            PolicyRule(policy_id="approve", require_approval=True),
        )
    )
    result = engine.evaluate(_context())
    assert result.outcome.deny is True


def test_resource_type_scoping() -> None:
    engine = PolicyEngine((PolicyRule(policy_id="p1", resource_type="order", deny=True),))
    assert engine.evaluate(_context(resource_type="order")).outcome.deny is True
    assert engine.evaluate(_context(resource_type="doc")).outcome.deny is False


def test_high_risk_requires_approval() -> None:
    result = PolicyEngine().evaluate(_context(risk_level="HIGH"))
    assert result.approval_required is True
    assert result.risk_level == "HIGH"


def test_low_and_medium_risk_do_not_require_approval() -> None:
    for level in ("LOW", "MEDIUM"):
        assert PolicyEngine().evaluate(_context(risk_level=level)).approval_required is False


def test_critical_risk_requires_approval() -> None:
    assert PolicyEngine().evaluate(_context(risk_level="CRITICAL")).approval_required is True


def test_the_highest_applicable_risk_tier_wins() -> None:
    risk = RiskEvaluator()
    assert risk.classify("LOW", "CRITICAL", "MEDIUM") == "CRITICAL"
    assert risk.classify(None, "HIGH") == "HIGH"
    assert risk.classify(None, None) == "LOW"


def test_an_unrecognised_risk_signal_is_never_treated_as_low() -> None:
    risk = RiskEvaluator()
    assert risk.classify("WHATEVER") == "CRITICAL"
    assert risk.classify("WHATEVER", "LOW") == "CRITICAL"


def test_risk_signal_score_is_an_internal_bounded_signal() -> None:
    risk = RiskEvaluator()
    assert risk.signal("LOW").score == 0.0
    assert risk.signal("CRITICAL").score == 1.0
    assert 0.0 <= risk.signal("MEDIUM").score <= 1.0


def test_approval_threshold_is_configurable_but_defaults_to_high() -> None:
    assert DEFAULT_APPROVAL_RISK == "HIGH"
    engine = PolicyEngine(approval_risk="CRITICAL")
    assert engine.evaluate(_context(risk_level="HIGH")).approval_required is False
    assert engine.evaluate(_context(risk_level="CRITICAL")).approval_required is True


def test_policy_version_is_reported_for_the_audit_trail() -> None:
    result = PolicyEngine().evaluate(_context())
    assert result.policy_version


def test_policy_failure_is_reported_rather_than_raised() -> None:
    class Exploding(RiskEvaluator):
        def classify(self, *levels):  # type: ignore[override]
            raise RuntimeError("boom")

    engine = PolicyEngine(risk=Exploding())
    result = engine.evaluate(_context())
    assert result.failed is True
    assert result.outcome.deny is False


def test_approval_is_a_static_or_dynamic_or() -> None:
    assert approval_required(tool_requires=True, policy_requires=False) is True
    assert approval_required(tool_requires=False, policy_requires=True) is True
    assert approval_required(tool_requires=True, policy_requires=True) is True
    assert approval_required(tool_requires=False, policy_requires=False) is False


def test_approval_is_never_an_and() -> None:
    # If it were an AND, a single source would be insufficient and a high-risk
    # action would silently execute.
    assert approval_required(tool_requires=True, policy_requires=False) is True


@pytest.mark.parametrize("level", ["CRITICAL", "HIGH"])
def test_engine_risk_level_is_reflected_in_the_result(level: str) -> None:
    assert PolicyEngine().evaluate(_context(risk_level=level)).risk_level == level
