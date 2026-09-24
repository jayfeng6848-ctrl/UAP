"""Decision combination — the single authorization algorithm.

There is exactly one evaluation order, and it is order independent: layers are
inspected in a fixed sequence, but a ``deny`` in any layer yields ``DENY``
regardless of where it was found. Results are therefore deterministic and
auditable, and no second code path may produce a different answer.

Frozen properties: default deny, ``DENY`` overrides ``ALLOW``, fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .interfaces import Decision


@dataclass(frozen=True)
class LayerOutcome:
    """The outcome of a single authorization layer: allow, deny, or abstain."""

    allow: bool = False
    deny: bool = False
    reasons: tuple[str, ...] = ()


ABSTAIN = LayerOutcome()


def _matched(*outcomes: tuple[str, LayerOutcome]) -> tuple[str, ...]:
    rules: list[str] = []
    for name, outcome in outcomes:
        rules.extend(f"{name}:{reason}" for reason in outcome.reasons)
    return tuple(rules)


def combine(
    *,
    rbac: LayerOutcome = ABSTAIN,
    acl: LayerOutcome = ABSTAIN,
    policy: LayerOutcome = ABSTAIN,
    approval_required: bool = False,
    policy_failed: bool = False,
) -> Decision:
    """Combine layer outcomes into one decision.

    Order of precedence:

    1. a policy evaluation failure is a denial (fail closed);
    2. any ``deny`` — from RBAC, ACL or Policy — is a denial;
    3. a satisfied approval requirement yields ``REQUIRES_APPROVAL``, which is
       *not* an allow;
    4. any ``allow`` from a *grant source* yields ``ALLOW``;
    5. otherwise ``DENY`` (default deny).

    Only RBAC and ACL are grant sources. A policy may restrict, and may add an
    approval requirement, but it can never originate a grant: letting it do so
    would make a policy a privilege-escalation surface.
    """
    layers = (("rbac", rbac), ("acl", acl), ("policy", policy))

    if policy_failed:
        return Decision(
            effect="DENY",
            reason="policy-failure",
            matched_rules=_matched(*layers),
        )

    for name, outcome in layers:
        if outcome.deny:
            return Decision(
                effect="DENY",
                reason=f"{name}-deny",
                matched_rules=_matched(*layers),
            )

    if approval_required:
        return Decision(
            effect="REQUIRES_APPROVAL",
            reason="approval-required",
            matched_rules=_matched(*layers),
        )

    if rbac.allow or acl.allow:
        return Decision(effect="ALLOW", reason="granted", matched_rules=_matched(*layers))

    return Decision(effect="DENY", reason="default-deny", matched_rules=())


def deny(reason: str) -> Decision:
    """Explicit denial with an inspectable reason (never an internal failure)."""
    return Decision(effect="DENY", reason=reason)


def fail_closed(reason: str) -> Decision:
    """Denial caused by an internal failure rather than an explicit rule.

    Kept distinct from an explicit denial so callers can tell "you may not" from
    "we could not decide" without ever turning either into an allow.
    """
    return Decision(effect="DENY", reason=reason)


__all__ = ["ABSTAIN", "LayerOutcome", "combine", "deny", "fail_closed"]
