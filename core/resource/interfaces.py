"""Generic resource contracts.

A resource is identified by a free-form ``type`` plus an ``id``. This module
deliberately defines *no* concrete types: those belong to the domain layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ResourceRef:
    type: str
    id: str
    tenant_id: str
    space_id: str | None = None
    owner_identity_id: str | None = None

    def __post_init__(self) -> None:
        if not self.type or not self.id:
            raise ValueError("resource type and id are required")


@dataclass(frozen=True)
class ResourceScope:
    tenant_id: str
    space_id: str | None = None


@runtime_checkable
class ResourceResolver(Protocol):
    def resolve(self, ref: ResourceRef) -> ResourceRef | None:
        ...


def is_in_scope(ref: ResourceRef, scope: ResourceScope) -> bool:
    """Return True when ``ref`` falls inside ``scope``."""
    if ref.tenant_id != scope.tenant_id:
        return False
    if scope.space_id is not None and ref.space_id != scope.space_id:
        return False
    return True


__all__ = ["ResourceRef", "ResourceScope", "ResourceResolver", "is_in_scope"]
