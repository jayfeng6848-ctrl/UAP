"""Model catalogue.

Describes capabilities of a model without naming any vendor type.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIModel:
    id: str
    provider: str
    display_name: str
    context_window: int = 0
    supports_embeddings: bool = False
    enabled: bool = True


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    fallback: tuple[str, ...] = ()


__all__ = ["AIModel", "ModelSpec"]
