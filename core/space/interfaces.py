"""Space contracts.

A space is a generic collaboration context. The *kind* of a space is a runtime
value supplied by a domain layer; this module must never enumerate concrete
kinds, otherwise the core would depend on a domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Space:
    id: str
    tenant_id: str
    kind: str
    name: str
    status: str = "active"

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@dataclass(frozen=True)
class SpaceContext:
    tenant_id: str
    space_id: str
    kind: str | None = None


@runtime_checkable
class SpaceResolver(Protocol):
    def get(self, space_id: str) -> Space | None:
        ...

    def list_for_tenant(self, tenant_id: str) -> list[Space]:
        ...


__all__ = ["Space", "SpaceContext", "SpaceResolver"]
