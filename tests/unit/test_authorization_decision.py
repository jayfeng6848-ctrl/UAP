"""Decision combination — the 14-row truth table and its invariants.

The combination must be deterministic and order independent: the same inputs
always produce the same answer, and no evaluation order can change it. Default
deny, deny-overrides-allow and fail-closed are frozen properties.
"""

from __future__ import annotations

from itertools import permutations

from core.permission.decision import ABSTAIN, LayerOutcome, combine

ALLOW = LayerOutcome(allow=True, reasons=("grant",))
DENY = LayerOutcome(deny=True, reasons=("revoke",))


def test_row01_rbac_allow() -> None:
    assert combine(rbac=ALLOW).effect == "ALLOW"


def test_row02_acl_allow() -> None:
    assert combine(acl=ALLOW).effect == "ALLOW"


def test_row03_all_three_allow() -> None:
    assert combine(rbac=ALLOW, acl=ALLOW, policy=ALLOW).effect == "ALLOW"


def test_row04_rbac_deny_beats_acl_and_policy_allow() -> None:
    assert combine(rbac=DENY, acl=ALLOW, policy=ALLOW).effect == "DENY"


def test_row05_acl_deny_beats_rbac_allow() -> None:
    decision = combine(rbac=ALLOW, acl=DENY, policy=ALLOW)
    assert decision.effect == "DENY"
    assert decision.reason == "acl-deny"


def test_row06_policy_deny_beats_rbac_and_acl_allow() -> None:
    assert combine(rbac=ALLOW, acl=ALLOW, policy=DENY).effect == "DENY"


def test_row07_every_layer_denies() -> None:
    assert combine(rbac=DENY, acl=DENY, policy=DENY).effect == "DENY"


def test_row08_no_layer_abstains_to_default_deny() -> None:
    decision = combine(rbac=ABSTAIN, acl=ABSTAIN, policy=ABSTAIN)
    assert decision.effect == "DENY"
    assert decision.reason == "default-deny"


def test_row09_approval_precedes_allow() -> None:
    decision = combine(rbac=ALLOW, approval_required=True)
    assert decision.effect == "REQUIRES_APPROVAL"
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_row10_policy_only_approval() -> None:
    assert combine(policy=ABSTAIN, approval_required=True).effect == "REQUIRES_APPROVAL"


def test_row11_policy_failure_denies_even_with_allow() -> None:
    decision = combine(rbac=ALLOW, acl=ALLOW, policy_failed=True)
    assert decision.effect == "DENY"
    assert decision.reason == "policy-failure"


def test_row12_nothing_resolves_denies() -> None:
    assert combine().effect == "DENY"


def test_row13_unknown_inputs_deny() -> None:
    assert combine(rbac=ABSTAIN, acl=ABSTAIN, policy=ABSTAIN).effect == "DENY"


def test_row14_an_expired_grant_is_simply_absent() -> None:
    # The resolver drops an expired grant, so the layer abstains and the default
    # deny applies — the expired grant can never yield an allow.
    assert combine(rbac=ABSTAIN, acl=ABSTAIN).effect == "DENY"


def test_deny_precedence_is_independent_of_layer_order() -> None:
    layers = {"rbac": DENY, "acl": ALLOW, "policy": ALLOW}
    results = {
        combine(**dict(zip(order, (layers[name] for name in order))))
        for order in permutations(("rbac", "acl", "policy"))
    }
    assert {decision.effect for decision in results} == {"DENY"}


def test_double_deny_is_deterministic() -> None:
    first = combine(rbac=DENY, acl=DENY)
    second = combine(acl=DENY, rbac=DENY)
    assert first == second


def test_repeated_evaluation_is_stable() -> None:
    results = {combine(rbac=ALLOW, acl=ABSTAIN, policy=ABSTAIN) for _ in range(50)}
    assert len(results) == 1


def test_matched_rules_are_auditable() -> None:
    decision = combine(rbac=ALLOW, acl=DENY)
    assert "rbac:grant" in decision.matched_rules
    assert "acl:revoke" in decision.matched_rules


def test_approval_is_never_reported_as_allowed() -> None:
    for approval in (True,):
        decision = combine(rbac=ALLOW, acl=ALLOW, policy=ALLOW, approval_required=approval)
        assert decision.effect == "REQUIRES_APPROVAL"
        assert not decision.allowed


def test_failure_beats_approval() -> None:
    decision = combine(approval_required=True, policy_failed=True)
    assert decision.effect == "DENY"


def test_policy_allow_alone_can_never_originate_a_grant() -> None:
    """A policy restricts; it is never a grant source."""
    decision = combine(policy=ALLOW)
    assert decision.effect == "DENY"
    assert decision.reason == "default-deny"


def test_policy_allow_cannot_widen_a_denied_request() -> None:
    assert combine(rbac=DENY, policy=ALLOW).effect == "DENY"


def test_policy_allow_still_accompanies_a_real_grant() -> None:
    assert combine(rbac=ALLOW, policy=ALLOW).effect == "ALLOW"
