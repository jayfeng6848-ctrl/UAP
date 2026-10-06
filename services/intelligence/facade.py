"""Company Copilot orchestration (OQ-CUI-03 / 04 / 05 / 09 · PDL Appendix AP).

Read path:  session → authorized context → **Company use cases** (never SQL, never
the repository) → minimal fields → citations → existing AI runtime → answer.

Propose path: the same read context, plus an ephemeral proposal. Nothing is
executed here: confirmation re-authenticates, re-authorizes and re-validates the
current state, then the caller uses the existing Company API.
"""

from __future__ import annotations

from typing import Any

from domains.company import ASSIGNMENT_RESOURCE_TYPE, EMPLOYEE_RESOURCE_TYPE

from services.agent.use_cases import find_qualification_agent, run_agent
from services.company import get_assignment, get_employee, list_assignments, list_employees
from services.company.errors import CompanyError
from services.company.use_cases import company_capability

from .proposal import EphemeralProposal, proposal_store

#: Modes the facade accepts. ``execute`` is deliberately not one of them.
ALLOWED_MODES = ("answer", "propose")

#: action → (resource type, target state, permission *verb*, legal current states)
PROPOSABLE_ACTIONS: dict[str, tuple[str, str, str, tuple[str, ...]]] = {
    "company_employee.suspend": (
        EMPLOYEE_RESOURCE_TYPE,
        "suspended",
        "update",
        ("active",),
    ),
    "company_employee.terminate": (
        EMPLOYEE_RESOURCE_TYPE,
        "terminated",
        "update",
        ("active", "suspended"),
    ),
    "company_assignment.end": (
        ASSIGNMENT_RESOURCE_TYPE,
        "ended",
        "update",
        ("active",),
    ),
}

#: Fields that may leave the authorized query (contract §21: UI Visible ≠ AI Required).
#: Names follow the frozen domain entities (``Employee.id`` / ``Assignment.id``).
EMPLOYEE_FIELDS = ("id", "display_name", "status")
ASSIGNMENT_FIELDS = ("id", "employee_id", "space_id", "status")


class ErrorCode:
    MODE_NOT_ALLOWED = "MODE_NOT_ALLOWED"
    ACTION_NOT_PROPOSABLE = "ACTION_NOT_PROPOSABLE"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PROPOSAL_NOT_FOUND = "PROPOSAL_NOT_FOUND"
    PROPOSAL_STALE = "PROPOSAL_STALE"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"


class IntelligenceError(RuntimeError):
    """A safe, customer-mappable facade failure (never carries internals)."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


def _field(row: Any, name: str) -> Any:
    return getattr(row, name, None)


def _employee_view(row: Any) -> dict[str, Any]:
    return {name: _field(row, name) for name in EMPLOYEE_FIELDS}


def _assignment_view(row: Any) -> dict[str, Any]:
    return {name: _field(row, name) for name in ASSIGNMENT_FIELDS}


def _citations(
    employees: list[dict[str, Any]], assignments: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """Citations come from rows the authorized query actually returned (OQ-CUI-04)."""
    out: list[dict[str, str]] = []
    for row in employees:
        if row.get("id"):
            out.append(
                {
                    "type": "company_employee",
                    "id": str(row["id"]),
                    "label": str(row.get("display_name") or row["id"]),
                }
            )
    for row in assignments:
        if row.get("id"):
            out.append(
                {
                    "type": "company_assignment",
                    "id": str(row["id"]),
                    "label": str(row["id"]),
                }
            )
    return out


def _authorized_context(
    db: Any, *, actor_id: str, tenant_id: str, space_id: str | None
) -> dict[str, Any]:
    """Read the minimal authorized Company data (Company use cases only)."""
    if not company_capability(
        db,
        actor_id=actor_id,
        tenant_id=tenant_id,
        action="read",
        resource_type=EMPLOYEE_RESOURCE_TYPE,
    ):
        raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "company read not authorized")
    try:
        employees = [
            _employee_view(row)
            for row in list_employees(db, actor_id=actor_id, tenant_id=tenant_id, limit=50)
        ]
    except CompanyError as exc:
        raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "company data unavailable") from exc

    assignments: list[dict[str, Any]] = []
    if company_capability(
        db,
        actor_id=actor_id,
        tenant_id=tenant_id,
        action="read",
        resource_type=ASSIGNMENT_RESOURCE_TYPE,
    ):
        try:
            assignments = [
                _assignment_view(row)
                for row in list_assignments(
                    db, actor_id=actor_id, tenant_id=tenant_id, space_id=space_id, limit=50
                )
            ]
        except CompanyError:
            assignments = []
    return {"employees": employees, "assignments": assignments, "space_id": space_id}


def _current(resource_type: str, db: Any, *, actor_id: str, tenant_id: str, resource_id: str) -> Any:
    if resource_type == EMPLOYEE_RESOURCE_TYPE:
        return get_employee(db, actor_id=actor_id, tenant_id=tenant_id, employee_id=resource_id)
    return get_assignment(db, actor_id=actor_id, tenant_id=tenant_id, assignment_id=resource_id)


def run_copilot(
    db: Any,
    *,
    actor_id: str,
    actor_type: str,
    tenant_id: str,
    space_id: str | None,
    message: str,
    mode: str = "answer",
    context: dict[str, Any] | None = None,
    request_id: str | None = None,
    action: str | None = None,
    resource_id: str | None = None,
) -> dict[str, Any]:
    """One Copilot turn. ``answer`` returns data + citations; ``propose`` adds a proposal."""
    if mode not in ALLOWED_MODES:
        raise IntelligenceError(ErrorCode.MODE_NOT_ALLOWED, "mode is not allowed")

    # The client's context is a UX hint only; the authorized context is re-derived.
    authorized = _authorized_context(
        db, actor_id=actor_id, tenant_id=tenant_id, space_id=space_id
    )
    citations = _citations(authorized["employees"], authorized["assignments"])

    proposal: EphemeralProposal | None = None
    current_state = ""
    if mode == "propose":
        if action is None or action not in PROPOSABLE_ACTIONS:
            raise IntelligenceError(ErrorCode.ACTION_NOT_PROPOSABLE, "action is not proposable")
        resource_type, expected_state, permission_action, _legal = PROPOSABLE_ACTIONS[action]
        if not company_capability(
            db,
            actor_id=actor_id,
            tenant_id=tenant_id,
            action=permission_action,
            resource_type=resource_type,
        ):
            raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "proposal not authorized")
        if not resource_id:
            raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "resource is required")
        try:
            # Current state is read through the existing Company API, not SQL.
            current = _current(
                resource_type,
                db,
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource_id=str(resource_id),
            )
        except CompanyError as exc:
            raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "resource not found") from exc
        current_state = str(_field(current, "status") or "")
        proposal = proposal_store.put(
            actor_id=actor_id,
            tenant_id=tenant_id,
            scope=str(space_id or "TENANT"),
            resource_type=resource_type,
            resource_id=str(resource_id),
            action=action,
            expected_state=expected_state,
            summary=f"{action} → {expected_state}",
        )

    agent = find_qualification_agent(db, tenant_id=tenant_id)
    if agent is None:
        raise IntelligenceError(ErrorCode.AI_UNAVAILABLE, "assistant is not configured")

    # Minimal, already-authorized payload — never the whole table (contract §21).
    prompt = (
        "你是企业助手。只能基于以下已授权的最少字段回答，不得推断未提供的数据。\n"
        f"问题：{message}\n"
        f"员工：{authorized['employees']}\n"
        f"分配：{authorized['assignments']}\n"
    )
    outcome = run_agent(
        db,
        agent_id=str(agent["id"]),
        actor_type=actor_type,
        actor_id=actor_id,
        tenant_id=tenant_id,
        space_id=space_id,
        input_text=prompt,
        request_id=request_id,
    )
    return {
        "status": outcome.status,
        "failure_code": outcome.failure_code,
        "mode": mode,
        "answer": outcome.result,
        "citations": citations,
        "current_state": current_state,
        "proposal": proposal.describe() if proposal is not None else None,
    }


def confirm_proposal(
    db: Any,
    *,
    actor_id: str,
    tenant_id: str,
    proposal_id: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Human confirmation: single-use, then re-authorize + re-validate current state."""
    proposal = proposal_store.consume(
        proposal_id=proposal_id, actor_id=actor_id, tenant_id=tenant_id
    )
    if proposal is None:
        raise IntelligenceError(ErrorCode.PROPOSAL_NOT_FOUND, "proposal is unknown or expired")

    _resource_type, expected_state, permission_action, legal = PROPOSABLE_ACTIONS[proposal.action]
    # Re-authorization at confirmation time (never reuse the earlier decision).
    if not company_capability(
        db,
        actor_id=actor_id,
        tenant_id=tenant_id,
        action=permission_action,
        resource_type=proposal.resource_type,
    ):
        raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "confirmation not authorized")

    try:
        current = _current(
            proposal.resource_type,
            db,
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource_id=proposal.resource_id,
        )
    except CompanyError as exc:
        raise IntelligenceError(ErrorCode.RESOURCE_NOT_FOUND, "resource not found") from exc

    observed = str(_field(current, "status") or "")
    if observed not in legal:
        # The world moved since the proposal was issued: never execute blind.
        raise IntelligenceError(ErrorCode.PROPOSAL_STALE, "proposal is stale")

    return {
        "proposal_id": proposal.proposal_id,
        "action": proposal.action,
        "resource_type": proposal.resource_type,
        "resource_id": proposal.resource_id,
        "current_state": observed,
        "expected_state": expected_state,
        "authorized": True,
        "request_id": request_id,
    }


__all__ = [
    "ALLOWED_MODES",
    "ASSIGNMENT_FIELDS",
    "EMPLOYEE_FIELDS",
    "ErrorCode",
    "IntelligenceError",
    "PROPOSABLE_ACTIONS",
    "confirm_proposal",
    "run_copilot",
]
