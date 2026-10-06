"""P20 Company domain tests: lifecycle, invariants and invalid transitions (no database)."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest

from domains.company import (
    Assignment,
    CompanyDomainError,
    DomainErrorCode,
    Employee,
    assignment_can_transition,
    employee_can_transition,
    is_valid_employee_no,
    validate_assignment_inputs,
)

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]


def _employee(**overrides) -> Employee:
    data = dict(
        id="00000000-0000-7000-8000-000000000001",
        tenant_id="00000000-0000-7000-8000-0000000000aa",
        employee_no="E-001",
        display_name="Ada",
        status="active",
    )
    data.update(overrides)
    return Employee(**data)


def _assignment(**overrides) -> Assignment:
    data = dict(
        id="00000000-0000-7000-8000-000000000002",
        tenant_id="00000000-0000-7000-8000-0000000000aa",
        employee_id="00000000-0000-7000-8000-000000000001",
        space_id="00000000-0000-7000-8000-0000000000bb",
        assignment_role="member",
        status="active",
    )
    data.update(overrides)
    return Assignment(**data)


def test_employee_lifecycle_allows_only_frozen_transitions() -> None:
    assert employee_can_transition("active", "suspended")
    assert employee_can_transition("active", "terminated")
    assert employee_can_transition("suspended", "active")
    assert employee_can_transition("suspended", "terminated")
    assert not employee_can_transition("terminated", "active")
    assert not employee_can_transition("terminated", "suspended")
    assert not employee_can_transition("active", "active")


def test_transitions_apply_to_entities() -> None:
    suspended = _employee().transition_to("suspended", at=NOW)
    assert suspended.status == "suspended" and suspended.terminated_at is None
    terminated = suspended.transition_to("terminated", at=NOW)
    assert terminated.status == "terminated" and terminated.terminated_at == NOW


def test_terminated_is_terminal() -> None:
    terminated = _employee(status="terminated", terminated_at=NOW)
    with pytest.raises(CompanyDomainError) as err:
        terminated.transition_to("active", at=NOW)
    assert err.value.code == DomainErrorCode.EMPLOYEE_ALREADY_TERMINATED


def test_invalid_employee_transition_is_rejected() -> None:
    suspended = _employee(status="suspended")
    with pytest.raises(CompanyDomainError) as err:
        suspended.transition_to("suspended", at=NOW)
    assert err.value.code == DomainErrorCode.EMPLOYEE_LIFECYCLE_CONFLICT


def test_employee_entity_rejects_inconsistent_lifecycle() -> None:
    with pytest.raises(CompanyDomainError) as err:
        _employee(status="terminated")  # terminated without terminated_at
    assert err.value.code == DomainErrorCode.INVALID_INPUT
    with pytest.raises(CompanyDomainError):
        _employee(status="active", terminated_at=NOW)  # active with terminated_at
    with pytest.raises(CompanyDomainError):
        _employee(status="retired")  # unknown status


def test_employee_number_shape() -> None:
    assert is_valid_employee_no("E-001")
    assert is_valid_employee_no("a.b_c-9")
    assert not is_valid_employee_no("bad no")
    assert not is_valid_employee_no("")
    assert not is_valid_employee_no("x" * 65)
    with pytest.raises(CompanyDomainError) as err:
        _employee(employee_no="bad no")
    assert err.value.code == DomainErrorCode.INVALID_EMPLOYEE_NO


def test_assignment_lifecycle_and_role() -> None:
    assert assignment_can_transition("active", "ended")
    assert not assignment_can_transition("ended", "active")
    ended = _assignment().end(at=NOW)
    assert ended.status == "ended" and ended.ended_at == NOW
    with pytest.raises(CompanyDomainError) as err:
        ended.end(at=NOW)
    assert err.value.code == DomainErrorCode.ASSIGNMENT_ALREADY_ENDED
    with pytest.raises(CompanyDomainError) as role_err:
        _assignment(assignment_role="owner")
    assert role_err.value.code == DomainErrorCode.INVALID_ASSIGNMENT_ROLE
    with pytest.raises(CompanyDomainError) as lifecycle_err:
        _assignment(status="ended")  # ended without ended_at
    assert lifecycle_err.value.code == DomainErrorCode.INVALID_INPUT
    assert validate_assignment_inputs(assignment_role="lead") == "lead"
    with pytest.raises(CompanyDomainError):
        validate_assignment_inputs(assignment_role="owner")


def test_domain_sources_stay_pure() -> None:
    """The domain must not reach for persistence, other layers or authorization."""
    forbidden = {"sqlalchemy", "psycopg", "psycopg2", "infrastructure", "services", "apps"}
    for path in sorted((ROOT / "domains" / "company").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                root = module.split(".")[0]
                assert root not in forbidden, f"{path.name} imports {module!r}"
