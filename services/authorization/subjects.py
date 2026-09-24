"""Subject resolution.

Turns a declared subject into a resolved subject with its effective grants.
An agent is resolved as an independent subject: its identity is the agent
record's own id, and its owner is recorded only as the actor/delegator context —
never as a source of authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.permission import Grant, Subject

from .errors import AuthorizationUnavailable, SubjectResolutionError
from .repository import AuthorizationRepository

_ACTIVE = "active"


@dataclass(frozen=True)
class ResolvedSubject:
    """A subject together with the grants that apply to it."""

    subject: Subject
    grants: tuple[Grant, ...] = ()
    role_ids: tuple[str, ...] = ()
    role_keys: tuple[str, ...] = ()
    risk_ceiling: str | None = None
    facts: dict[str, Any] = field(default_factory=dict)


class SubjectResolver:
    """Resolve ``USER`` / ``ROLE`` / ``AGENT`` subjects against the store."""

    def __init__(self, repository: AuthorizationRepository) -> None:
        self._repository = repository

    def resolve(self, subject: Subject, *, tenant_id: str | None = None,
                space_id: str | None = None) -> ResolvedSubject:
        try:
            if subject.subject_type == "USER":
                return self._resolve_user(subject, tenant_id, space_id)
            if subject.subject_type == "ROLE":
                return self._resolve_role(subject)
            if subject.subject_type == "AGENT":
                return self._resolve_agent(subject)
        except SubjectResolutionError:
            raise
        except Exception as exc:  # pragma: no cover - infrastructure failure
            raise AuthorizationUnavailable(str(exc)) from exc
        raise SubjectResolutionError(f"unsupported subject type {subject.subject_type!r}")

    # ------------------------------------------------------------------ levels
    def _resolve_user(self, subject: Subject, tenant_id: str | None,
                      space_id: str | None) -> ResolvedSubject:
        user = self._repository.get_user(subject.identity_id)
        if user is None:
            raise SubjectResolutionError("unknown subject")
        if str(user._mapping["status"]) != _ACTIVE:
            raise SubjectResolutionError("subject is not active")

        role_ids = self._repository.role_ids_for_user(
            subject.identity_id, tenant_id, space_id
        )
        roles = self._repository.get_roles(role_ids)
        grants, role_keys, active_ids = self._grants_from_roles(roles)
        return ResolvedSubject(
            subject=subject,
            grants=grants,
            role_ids=active_ids,
            role_keys=tuple(sorted(role_keys)),
            facts={"scope": "USER"},
        )

    def _resolve_role(self, subject: Subject) -> ResolvedSubject:
        role = self._repository.get_role(subject.identity_id)
        if role is None:
            raise SubjectResolutionError("unknown subject")
        if str(role._mapping["status"]) != _ACTIVE:
            raise SubjectResolutionError("subject is not active")
        grants, role_keys, active_ids = self._grants_from_roles([role])
        return ResolvedSubject(
            subject=subject,
            grants=grants,
            role_ids=active_ids,
            role_keys=tuple(role_keys),
        )

    def _resolve_agent(self, subject: Subject) -> ResolvedSubject:
        agent_id = subject.agent_id or subject.identity_id
        agent = self._repository.get_agent(agent_id)
        if agent is None:
            raise SubjectResolutionError("unknown subject")
        if str(agent._mapping["status"]) != _ACTIVE:
            raise SubjectResolutionError("subject is not active")

        resolved = Subject(
            identity_id=subject.identity_id,
            subject_type="AGENT",
            role_keys=subject.role_keys,
            scopes=subject.scopes,
            tenant_id=str(agent._mapping["tenant_id"]),
            agent_id=agent_id,
            actor_id=subject.actor_id,
            delegator_id=subject.delegator_id or str(agent._mapping["owner_id"]),
        )
        return ResolvedSubject(
            subject=resolved,
            grants=(),
            risk_ceiling=str(agent._mapping["max_risk_level"]),
            facts={
                "owner_id": str(agent._mapping["owner_id"]),
                "agent_tenant_id": str(agent._mapping["tenant_id"]),
                "agent_space_id": (
                    str(agent._mapping["space_id"]) if agent._mapping["space_id"] else None
                ),
            },
        )

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _grants_from_roles(
        roles: list[Any],
    ) -> tuple[tuple[Grant, ...], set[str], tuple[str, ...]]:
        grants: list[Grant] = []
        keys: set[str] = set()
        ids: list[str] = []
        for role in roles:
            mapping = role._mapping
            if str(mapping["status"]) != _ACTIVE:
                continue
            grants.append(
                Grant(
                    scope=str(mapping["scope"]),
                    tenant_id=(
                        str(mapping["tenant_id"]) if mapping["tenant_id"] else None
                    ),
                    space_id=str(mapping["space_id"]) if mapping["space_id"] else None,
                )
            )
            keys.add(str(mapping["key"]))
            ids.append(str(mapping["id"]))
        return tuple(grants), keys, tuple(ids)


__all__ = ["ResolvedSubject", "SubjectResolver"]
