"""Membership contracts.

Membership binds an identity to a space with a role key. Role *definitions*
belong to core.permission; membership only records which role key applies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

MEMBERSHIP_STATUS = ("invited", "active", "suspended", "removed")


@dataclass(frozen=True)
class Membership:
    id: str
    space_id: str
    identity_id: str
    role_key: str
    status: str = "active"

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@runtime_checkable
class MembershipStore(Protocol):
    def get(self, membership_id: str) -> Membership | None:
        ...

    def find(self, space_id: str, identity_id: str) -> Membership | None:
        ...

    def list_for_identity(self, identity_id: str) -> list[Membership]:
        ...

    def list_for_space(self, space_id: str) -> list[Membership]:
        ...


__all__ = ["MEMBERSHIP_STATUS", "Membership", "MembershipStore"]
