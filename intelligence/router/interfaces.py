"""Model routing.

Chooses which provider/model serves a request based on policy and health.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from intelligence.gateway.interfaces import AIRequest
from intelligence.models.interfaces import ModelSpec


@runtime_checkable
class ModelRouter(Protocol):
    def route(self, request: AIRequest, candidates: tuple[ModelSpec, ...]) -> ModelSpec:
        ...


class FirstAvailableRouter:
    """Reference router: pick the first enabled candidate, else fall back."""

    def route(self, request: AIRequest, candidates: tuple[ModelSpec, ...]) -> ModelSpec:
        if not candidates:
            raise ValueError("no model candidates configured")
        return candidates[0]


__all__ = ["ModelRouter", "FirstAvailableRouter"]
