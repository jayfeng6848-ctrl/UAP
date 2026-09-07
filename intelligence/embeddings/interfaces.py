"""Embedding contracts (interface only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int:
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


__all__ = ["EmbeddingProvider"]
