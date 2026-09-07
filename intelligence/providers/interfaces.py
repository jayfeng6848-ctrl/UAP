"""Provider adapters.

Every vendor is integrated through an adapter. This package must never import a
vendor SDK directly (enforced by tests/architecture); the concrete adapters are
registered at runtime.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from intelligence.gateway.interfaces import AIProvider


@runtime_checkable
class ProviderAdapter(Protocol):
    def build(self, config: dict[str, object]) -> AIProvider:
        """Create a provider from configuration (credentials come from env)."""
        ...


class ProviderRegistry:
    """Registry of provider names to adapter factories."""

    def __init__(self) -> None:
        self._adapters: dict[str, ProviderAdapter] = {}

    def register(self, name: str, adapter: ProviderAdapter) -> None:
        self._adapters[name] = adapter

    def get(self, name: str) -> ProviderAdapter | None:
        return self._adapters.get(name)

    def names(self) -> list[str]:
        return sorted(self._adapters)


FORBIDDEN_DIRECT_IMPORTS = ("openai", "anthropic", "deepseek", "ollama")

__all__ = ["ProviderAdapter", "ProviderRegistry", "FORBIDDEN_DIRECT_IMPORTS"]
