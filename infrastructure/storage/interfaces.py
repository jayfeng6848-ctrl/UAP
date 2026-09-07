"""Abstract object storage interface (contract only in STEP 0)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class StoredObject:
    key: str
    size_bytes: int
    content_type: str
    metadata: dict[str, Any]


@runtime_checkable
class StorageClient(Protocol):
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        ...

    def get(self, key: str) -> bytes:
        ...

    def delete(self, key: str) -> None:
        ...

    def exists(self, key: str) -> bool:
        ...

    def stat(self, key: str) -> StoredObject | None:
        ...


class StorageNotConfiguredError(RuntimeError):
    """Raised when storage is used before a backend is configured."""


__all__ = ["StoredObject", "StorageClient", "StorageNotConfiguredError"]
