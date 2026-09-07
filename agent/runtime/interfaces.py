"""Agent runtime contract.

Execution order is fixed and non-negotiable:

    Agent -> Policy -> Tool -> Service -> Database

An agent never touches the database directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class AgentInput:
    text: str
    tenant_id: str
    space_id: str | None = None
    actor_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentRunResult:
    status: str  # completed | denied | failed
    output: dict[str, Any] = field(default_factory=dict)
    reason: str | None = None


@runtime_checkable
class AgentRuntime(Protocol):
    def run(self, agent_id: str, payload: AgentInput) -> AgentRunResult:
        ...


__all__ = ["AgentInput", "AgentRunResult", "AgentRuntime"]
