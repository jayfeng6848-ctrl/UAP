"""Workflow contract (interface only in STEP 0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    tool_name: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class WorkflowRunner(Protocol):
    def run(self, steps: list[WorkflowStep]) -> list[Any]:
        ...


__all__ = ["WorkflowStep", "WorkflowRunner"]
