"""AI gateway contract.

The single entry point for model calls. Callers never talk to a vendor SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class AIRequest:
    prompt: str
    model: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None


@dataclass(frozen=True)
class AICompletion:
    text: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class AIProvider(Protocol):
    """A vendor-agnostic model endpoint."""

    @property
    def name(self) -> str:
        ...

    def complete(self, request: AIRequest) -> AICompletion:
        ...


@runtime_checkable
class AIGateway(Protocol):
    def complete(self, request: AIRequest) -> AICompletion:
        ...

    def health(self) -> bool:
        ...


__all__ = ["AIRequest", "AICompletion", "AIProvider", "AIGateway"]
