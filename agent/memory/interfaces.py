"""Agent memory contract (interface only in STEP 0)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class MemoryRecord:
    key: str
    value: dict[str, Any]
    scope: str = "session"


@runtime_checkable
class MemoryStore(Protocol):
    def read(self, key: str) -> MemoryRecord | None:
        ...

    def write(self, record: MemoryRecord) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


__all__ = ["MemoryRecord", "MemoryStore"]
