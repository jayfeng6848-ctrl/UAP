"""Authorization decision contract.

The decision is three valued. ``REQUIRES_APPROVAL`` means the action is *held*,
not permitted: only ``ALLOW`` may be treated as permission to execute. A caller
that reads the boolean and ignores the third state would execute an unapproved
action, so the contract makes the distinction explicit and asserts it.
"""

from __future__ import annotations

import pytest

from core.permission import (
    DENY,
    Action,
    AuthorizationRequest,
    Decision,
    Grant,
    Subject,
    default_decision,
)
from core.resource import ResourceRef
from services.authorization import AuthorizationService

pytestmark = pytest.mark.contract

SUBJECT = Subject(identity_id="u1", subject_type="USER")
ACTION = Action("read", "order")
RESOURCE = ResourceRef(type="order", id="o1", tenant_id="t1")


def test_decision_is_three_valued() -> None:
    assert Decision(effect="ALLOW", reason="granted").effect == "ALLOW"
    assert Decision(effect="DENY", reason="default-deny").effect == "DENY"
    assert Decision(effect="REQUIRES_APPROVAL", reason="approval-required").effect == (
        "REQUIRES_APPROVAL"
    )


def test_an_unknown_decision_state_is_rejected() -> None:
    with pytest.raises(ValueError):
        Decision(effect="MAYBE", reason="?")


def test_only_allow_reports_allowed() -> None:
    assert Decision(effect="ALLOW", reason="granted").allowed is True
    assert Decision(effect="DENY", reason="default-deny").allowed is False
    assert Decision(effect="REQUIRES_APPROVAL", reason="held").allowed is False


def test_requires_approval_is_flagged_distinctly() -> None:
    held = Decision(effect="REQUIRES_APPROVAL", reason="held")
    assert held.requires_approval is True
    assert not held.allowed


def test_default_decision_is_a_denial() -> None:
    assert default_decision().effect == "DENY"
    assert default_decision() == DENY


def test_a_decision_carries_its_reasons_and_policy_version() -> None:
    decision = Decision(
        effect="ALLOW",
        reason="granted",
        matched_rules=("rbac:admin:READ",),
        policy_version="authz-policy-v1",
    )
    assert decision.matched_rules == ("rbac:admin:READ",)
    assert decision.policy_version == "authz-policy-v1"


def test_subject_type_is_validated() -> None:
    with pytest.raises(ValueError):
        Subject(identity_id="x", subject_type="ROBOT")


def test_a_subject_requires_an_identifier() -> None:
    with pytest.raises(ValueError):
        Subject(identity_id="")


def test_an_agent_subject_resolves_against_its_own_identifier() -> None:
    agent = Subject(identity_id="owner-1", subject_type="AGENT", agent_id="a1")
    assert agent.subject_id == "a1"


def test_a_grant_accepts_only_stored_scopes() -> None:
    assert Grant(scope="PLATFORM").scope == "PLATFORM"
    with pytest.raises(ValueError):
        Grant(scope="SELF")


def test_authorization_request_shape() -> None:
    request = AuthorizationRequest(
        subject=SUBJECT,
        action=ACTION,
        resource=RESOURCE,
        tenant_id="t1",
        space_id=None,
        request_id="req-1",
    )
    assert request.subject.subject_type == "USER"
    assert request.action.name == "read"
    assert request.resource.id == "o1"
    assert request.request_id == "req-1"


def test_the_service_satisfies_the_authorizer_protocol() -> None:
    from core.permission import Authorizer

    service = AuthorizationService()
    assert isinstance(service, Authorizer)


def test_authorize_subject_returns_a_decision() -> None:
    service = AuthorizationService()
    decision = service.authorize_subject(SUBJECT, ACTION, RESOURCE)
    assert isinstance(decision, Decision)
    # No database backing here, so the contract only requires a denial.
    assert decision.effect == "DENY"


def test_authorization_request_carries_the_base_delegation_context() -> None:
    agent = Subject(
        identity_id="owner-1",
        subject_type="AGENT",
        agent_id="a1",
        actor_id="owner-1",
        delegator_id="owner-1",
    )
    request = AuthorizationRequest(
        subject=agent, action=ACTION, resource=RESOURCE, delegator_id="owner-1"
    )
    assert request.delegator_id == "owner-1"
    assert request.subject.actor_id == "owner-1"
