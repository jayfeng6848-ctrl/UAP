"""Authorization contracts.

Default deny: an action is forbidden unless a policy explicitly allows it.
Unknown roles, unknown resources and evaluation errors all yield a denial.

Contracts and value objects only — no I/O and no persistence. Orchestration and
persistence live in the service layer, kept separate on purpose so the
dependency direction can never invert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from core.resource.interfaces import ResourceRef

from .vocabulary import ACTIONS, EFFECTS, STORED_SCOPES, SUBJECT_TYPES, normalize_action


@dataclass(frozen=True)
class Action:
    """A canonical action applied to a resource type."""

    name: str
    resource_type: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_action(self.name))

    @property
    def is_canonical(self) -> bool:
        return self.name in ACTIONS


@dataclass(frozen=True)
class Decision:
    """A three-valued authorization decision.

    ``REQUIRES_APPROVAL`` is *not* an authorization to execute: it means the
    action stays blocked until an approval requirement is satisfied. Only
    ``ALLOW`` is executable, which is what ``allowed`` reports.
    """

    effect: str
    reason: str
    matched_rules: tuple[str, ...] = ()
    policy_version: str | None = None

    def __post_init__(self) -> None:
        if self.effect not in EFFECTS:
            raise ValueError(f"invalid decision effect {self.effect!r}")

    @property
    def allowed(self) -> bool:
        """True only for ``ALLOW``; a pending approval is not an allow."""
        return self.effect == "ALLOW"

    @property
    def requires_approval(self) -> bool:
        return self.effect == "REQUIRES_APPROVAL"


DENY = Decision(effect="DENY", reason="default-deny")


@dataclass(frozen=True)
class Subject:
    """An authorization subject.

    An agent is an independent authorization subject, never a mere execution
    profile of its owner. ``actor_id`` / ``delegator_id`` carry the *base*
    delegation context only; the full delegation lifecycle is deferred.
    """

    identity_id: str
    subject_type: str = "USER"
    role_keys: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()
    tenant_id: str | None = None
    agent_id: str | None = None
    actor_id: str | None = None
    delegator_id: str | None = None

    def __post_init__(self) -> None:
        if self.subject_type not in SUBJECT_TYPES:
            raise ValueError(f"unknown subject type {self.subject_type!r}")
        if not self.identity_id:
            raise ValueError("subject identity_id is required")

    @property
    def subject_id(self) -> str:
        """The identifier an authorization decision is resolved against."""
        if self.subject_type == "AGENT" and self.agent_id:
            return self.agent_id
        return self.identity_id


@dataclass(frozen=True)
class Grant:
    """A stored baseline grant: a stored scope plus its tenant/space binding."""

    scope: str
    tenant_id: str | None = None
    space_id: str | None = None

    def __post_init__(self) -> None:
        if self.scope not in STORED_SCOPES:
            raise ValueError(f"unknown stored scope {self.scope!r}")


@dataclass(frozen=True)
class AuthorizationRequest:
    """The single input shape of the authorization service."""

    subject: Subject
    action: Action
    resource: ResourceRef
    tenant_id: str | None = None
    space_id: str | None = None
    request_id: str | None = None
    delegator_id: str | None = None
    risk_level: str | None = None
    environment: dict[str, object] = field(default_factory=dict)


@runtime_checkable
class Authorizer(Protocol):
    def authorize(self, subject: Subject, action: Action, resource: ResourceRef) -> Decision:
        ...


def default_decision() -> Decision:
    return DENY


__all__ = [
    "Action",
    "AuthorizationRequest",
    "Authorizer",
    "DENY",
    "Decision",
    "Grant",
    "Subject",
    "default_decision",
]
