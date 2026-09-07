"""Agent registry: what agents exist and how they are described."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class AgentDescriptor:
    agent_id: str
    name: str
    version: str = "0.1.0"
    capabilities: tuple[str, ...] = ()
    tool_names: tuple[str, ...] = field(default=())


@runtime_checkable
class AgentRegistry(Protocol):
    def register(self, descriptor: AgentDescriptor) -> None:
        ...

    def get(self, agent_id: str) -> AgentDescriptor | None:
        ...

    def list(self) -> list[AgentDescriptor]:
        ...


__all__ = ["AgentDescriptor", "AgentRegistry"]
