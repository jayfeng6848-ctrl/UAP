"""AI usage policy: budgets, allow-lists and prompt safety gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from intelligence.gateway.interfaces import AIRequest


@dataclass(frozen=True)
class AIPolicyDecision:
    allowed: bool
    reason: str
    max_tokens: int | None = None


@runtime_checkable
class AIPolicy(Protocol):
    def check(self, request: AIRequest) -> AIPolicyDecision:
        ...


class AllowAllPolicy:
    """Placeholder policy used before a real budget policy is implemented."""

    def check(self, request: AIRequest) -> AIPolicyDecision:
        return AIPolicyDecision(allowed=True, reason="policy-not-configured")


__all__ = ["AIPolicyDecision", "AIPolicy", "AllowAllPolicy"]
