"""Generic resource contracts.

A resource is identified by a free-form ``type`` plus an ``id``. This module
deliberately defines *no* concrete types: those belong to the domain layers.

Canonical resource attributes are: type, id, tenant, space, classification,
owner and lifecycle status. There is intentionally **no** parent relation — the
platform has no resource parent tree, so no implicit inheritance can arise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

CLASSIFICATIONS = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")

RESOURCE_STATUSES = ("active", "archived", "deleted")


@dataclass(frozen=True)
class ResourceRef:
    type: str
    id: str
    tenant_id: str = ""
    space_id: str | None = None
    owner_identity_id: str | None = None
    classification: str = "INTERNAL"
    status: str = "active"

    def __post_init__(self) -> None:
        if not self.type or not self.id:
            raise ValueError("resource type and id are required")
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"unknown classification {self.classification!r}")

    @property
    def is_active(self) -> bool:
        return self.status == "active"


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


__all__ = [
    "CLASSIFICATIONS",
    "RESOURCE_STATUSES",
    "ResourceRef",
    "ResourceResolver",
    "ResourceScope",
    "is_in_scope",
]
