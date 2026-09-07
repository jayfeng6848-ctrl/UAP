"""Abstract cache interface.

Redis is the intended backing store but **no client is wired in this phase**.
Only the contract exists, so callers can be written and tested against an
in-memory double today and swapped for Redis later without call-site changes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CacheClient(Protocol):
    """Minimal key/value cache contract."""

    def get(self, key: str) -> str | None:
        """Return the value for ``key`` or ``None`` when absent/expired."""
        ...

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Store ``value`` under ``key`` with an optional TTL."""
        ...

    def delete(self, key: str) -> None:
        """Remove ``key``; deleting a missing key is a no-op."""
        ...

    def exists(self, key: str) -> bool:
        ...

    def ping(self) -> bool:
        """Return ``True`` when the backing store answers."""
        ...


class CacheNotConfiguredError(RuntimeError):
    """Raised when a cache operation is attempted without a configured client."""


class NullCache:
    """No-op cache used when no cache is configured.

    Behaviour: every read misses, every write is discarded. This keeps callers
    simple (no ``if cache is None`` branches) while making the degradation
    explicit in logs and health output.
    """

    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        return None

    def delete(self, key: str) -> None:
        return None

    def exists(self, key: str) -> bool:
        return False

    def ping(self) -> bool:
        return False


__all__ = ["CacheClient", "CacheNotConfiguredError", "NullCache"]
