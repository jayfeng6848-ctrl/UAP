"""Agent Run contract: lifecycle state machine + correlation shapes.

Frozen by P16-D02 (request-scoped synchronous run + agent_runs ledger) and
P16-D12 (limited schema expansion). Pure logic only — the state machine is the
executable form of the lifecycle rule, so an illegal transition cannot silently
become a stored status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_TOOL = "WAITING_TOOL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


RUN_STATUSES = tuple(s.value for s in RunStatus)

#: Terminal states never transition again.
TERMINAL_RUN_STATUSES = frozenset(
    {RunStatus.COMPLETED.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value}
)

_ALLOWED: dict[str, frozenset[str]] = {
    RunStatus.CREATED.value: frozenset(
        {RunStatus.RUNNING.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value}
    ),
    RunStatus.RUNNING.value: frozenset(
        {
            RunStatus.WAITING_TOOL.value,
            RunStatus.COMPLETED.value,
            RunStatus.FAILED.value,
            RunStatus.CANCELLED.value,
        }
    ),
    RunStatus.WAITING_TOOL.value: frozenset(
        {
            RunStatus.RUNNING.value,
            RunStatus.COMPLETED.value,
            RunStatus.FAILED.value,
            RunStatus.CANCELLED.value,
        }
    ),
    RunStatus.COMPLETED.value: frozenset(),
    RunStatus.FAILED.value: frozenset(),
    RunStatus.CANCELLED.value: frozenset(),
}


class InvalidRunTransition(RuntimeError):
    """Raised when a state change would violate the frozen lifecycle."""


def can_transition(source: str, target: str) -> bool:
    return target in _ALLOWED.get(source, frozenset())


def require_transition(source: str, target: str) -> None:
    if not can_transition(source, target):
        raise InvalidRunTransition(f"{source} -> {target} is not an allowed run transition")


@dataclass(frozen=True)
class ToolProposal:
    """A tool invocation proposed by the model/agent — not yet authorized."""

    tool_key: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentRunRecord:
    """The correlation identity of one run (D02: one run_id spans the chain)."""

    id: str
    tenant_id: str
    space_id: str | None
    agent_id: str
    agent_version_id: str
    actor_type: str
    actor_id: str
    status: str
    input_digest: str
    result_digest: str | None = None
    request_id: str | None = None
    failure_code: str | None = None
