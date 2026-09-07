"""Authorization contracts.

Default deny: an action is forbidden unless a policy explicitly allows it.
Unknown roles, unknown resources and evaluation errors all yield a denial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.resource.interfaces import ResourceRef


@dataclass(frozen=True)
class Action:
    name: str
    resource_type: str


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    matched_rules: tuple[str, ...] = ()


DENY = Decision(allowed=False, reason="default-deny")


@dataclass(frozen=True)
class Subject:
    identity_id: str
    role_keys: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()


@runtime_checkable
class Authorizer(Protocol):
    def authorize(self, subject: Subject, action: Action, resource: ResourceRef) -> Decision:
        ...


def default_decision() -> Decision:
    return DENY


__all__ = ["Action", "Decision", "DENY", "Subject", "Authorizer", "default_decision"]
