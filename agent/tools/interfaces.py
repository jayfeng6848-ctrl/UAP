"""Tool contracts.

A tool is the only path from an agent to a service. Tools are registered,
described, and always invoked with an explicit policy context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolContext:
    tenant_id: str
    actor_id: str
    space_id: str | None = None
    request_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@runtime_checkable
class Tool(Protocol):
    @property
    def name(self) -> str:
        ...

    def invoke(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)


__all__ = ["ToolContext", "ToolResult", "Tool", "ToolRegistry"]
