"""P21 Company UI unit tests — proposal lifecycle, facade guards, capability shape.

Offline (no database, no network): the ephemeral proposal store, the facade's mode
and action guards, the citation builder and the capability projection's declared
shape are all pure boundaries.
"""

from __future__ import annotations

import pytest

from services.company.capabilities import (
    OPERATIONAL_ACTIONS,
    RESERVED_PERMISSIONS,
    project_capabilities,
)
from services.intelligence import ErrorCode, IntelligenceError
from services.intelligence.facade import (
    ASSIGNMENT_FIELDS,
    EMPLOYEE_FIELDS,
    PROPOSABLE_ACTIONS,
    _citations,
    confirm_proposal,
    run_copilot,
)
from services.intelligence.proposal import EphemeralProposalStore


class _Employee:
    id = "emp-1"
    display_name = "Ada Lovelace"
    status = "active"


def test_proposal_is_single_use_and_actor_bound() -> None:
    store = EphemeralProposalStore(ttl_seconds=60)
    proposal = store.put(
        actor_id="a",
        tenant_id="t",
        scope="TENANT",
        resource_type="company_employee",
        resource_id="emp-1",
        action="company_employee.suspend",
        expected_state="suspended",
        summary="suspend",
    )
    # Another actor (or tenant) can never see it.
    assert store.get(proposal_id=proposal.proposal_id, actor_id="b", tenant_id="t") is None
    # First consume succeeds, the second cannot (non-replay).
    assert store.consume(proposal_id=proposal.proposal_id, actor_id="a", tenant_id="t") is not None
    assert store.consume(proposal_id=proposal.proposal_id, actor_id="a", tenant_id="t") is None


def test_proposal_expires() -> None:
    store = EphemeralProposalStore(ttl_seconds=0)
    proposal = store.put(
        actor_id="a",
        tenant_id="t",
        scope="TENANT",
        resource_type="company_employee",
        resource_id="emp-1",
        action="company_employee.suspend",
        expected_state="suspended",
        summary="suspend",
    )
    assert store.get(proposal_id=proposal.proposal_id, actor_id="a", tenant_id="t") is None


def test_citations_come_from_authorized_rows_only() -> None:
    citations = _citations([{"id": "emp-1", "display_name": "Ada"}], [{"id": "asg-1"}])
    assert citations == [
        {"type": "company_employee", "id": "emp-1", "label": "Ada"},
        {"type": "company_assignment", "id": "asg-1", "label": "asg-1"},
    ]
    assert _citations([], []) == []


def test_facade_rejects_execute_mode() -> None:
    with pytest.raises(IntelligenceError) as exc:
        run_copilot(
            None,
            actor_id="a",
            actor_type="USER",
            tenant_id="t",
            space_id=None,
            message="hi",
            mode="execute",
        )
    assert exc.value.code == ErrorCode.MODE_NOT_ALLOWED


def test_proposable_actions_are_the_frozen_three() -> None:
    assert set(PROPOSABLE_ACTIONS) == {
        "company_employee.suspend",
        "company_employee.terminate",
        "company_assignment.end",
    }
    for _action, (_rt, _state, verb, legal) in PROPOSABLE_ACTIONS.items():
        # High-risk mutations map to the existing ``update`` permission, never a new one.
        assert verb == "update"
        assert legal


def test_confirm_without_a_proposal_is_not_found() -> None:
    with pytest.raises(IntelligenceError) as exc:
        confirm_proposal(None, actor_id="a", tenant_id="t", proposal_id="does-not-exist")
    assert exc.value.code == ErrorCode.PROPOSAL_NOT_FOUND


def test_capability_projection_shape_and_field_whitelists() -> None:
    recorded: list[tuple[str, str]] = []

    def _fake(verb: str, resource_type: str) -> bool:
        recorded.append((verb, resource_type))
        return verb == "read"

    assert len(OPERATIONAL_ACTIONS) == 8
    assert RESERVED_PERMISSIONS == (
        "company_employee.delete",
        "company_employee.admin",
        "company_assignment.delete",
    )
    # The projection must never leak un-whitelisted employee/assignment fields.
    assert EMPLOYEE_FIELDS == ("id", "display_name", "status")
    assert ASSIGNMENT_FIELDS == ("id", "employee_id", "space_id", "status")
    assert _Employee.id == "emp-1"
