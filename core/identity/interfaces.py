"""Identity contracts.

Identity answers "who is this?". It knows nothing about what a user is allowed
to do (permission) or where they belong (space/membership).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

IDENTITY_KINDS = ("user", "service", "device_subject")


@dataclass(frozen=True)
class IdentityRef:
    """A pointer to an identity, possibly in an external system."""

    identity_id: str
    kind: str = "user"
    external_system: str | None = None


@dataclass(frozen=True)
class Identity:
    id: str
    display_name: str
    kind: str = "user"
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    external_refs: tuple[IdentityRef, ...] = ()

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@runtime_checkable
class IdentityResolver(Protocol):
    def get_by_id(self, identity_id: str) -> Identity | None:
        ...

    def resolve(self, ref: IdentityRef) -> Identity | None:
        ...


__all__ = ["IDENTITY_KINDS", "IdentityRef", "Identity", "IdentityResolver"]
