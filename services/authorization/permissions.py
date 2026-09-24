"""Permission resolution: RBAC and ACL.

RBAC is the *baseline* grant: it answers "what does this subject's role carry?".
ACL is the *resource-specific* grant: it answers "who may touch this resource?".
The two never merge into one concept, and neither widens the other.

A deny found in either layer beats any allow found anywhere. Nothing in this
module can produce an allow on its own.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.permission import Action, Grant, LayerOutcome
from core.permission.scope import scope_covers
from core.permission.vocabulary import normalize_action
from core.resource import ResourceRef

from .errors import AuthorizationUnavailable
from .repository import AuthorizationRepository
from .subjects import ResolvedSubject

# ACL subject-type keys are lowercase in the database; canonical subject types
# are uppercase. The mapping is explicit so the two vocabularies never mix.
_SUBJECT_TYPE_KEYS = {"USER": "user", "ROLE": "role", "AGENT": "agent"}


def _expired(value: Any) -> bool:
    """True when a grant carries an expiry that has already passed."""
    if value is None:
        return False
    if isinstance(value, datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return moment <= datetime.now(timezone.utc)
    return False


def _same_action(stored: Any, action: Action) -> bool:
    """Compare a stored action with a request action.

    Both sides are folded through the canonical normaliser, so a stored value
    that differs only in case or Unicode form still matches its canonical
    action (``D-AUTH-25``). Unknown values normalise to themselves and simply
    never match a canonical action.
    """
    try:
        return normalize_action(str(stored)) == action.name
    except TypeError:
        return False


class PermissionResolver:
    """Resolve the RBAC and ACL layers for one request."""

    def __init__(self, repository: AuthorizationRepository) -> None:
        self._repository = repository

    # ------------------------------------------------------------------ RBAC
    def rbac(
        self, resolved: ResolvedSubject, action: Action, resource: ResourceRef
    ) -> LayerOutcome:
        """Baseline grants carried by the subject's roles.

        A role only grants where its *own* stored scope actually reaches, so a
        space role can never act on another space and a tenant role can never
        reach across tenants.
        """
        if not resolved.role_ids:
            return LayerOutcome()

        role_scope: dict[str, Grant] = dict(zip(resolved.role_ids, resolved.grants))

        try:
            rows = self._repository.role_grants(resolved.role_ids)
        except AuthorizationUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - infrastructure failure
            raise AuthorizationUnavailable(str(exc)) from exc

        allows: list[str] = []
        denies: list[str] = []
        for row in rows:
            mapping = row._mapping
            grant = role_scope.get(str(mapping["role_id"]))
            if grant is None or not scope_covers(grant, resource):
                continue
            if not _same_action(mapping["action"], action):
                continue
            resource_type = mapping["resource_type"]
            if resource_type is not None and str(resource_type) != resource.type:
                continue
            reason = f"{mapping['key']}:{action.name}"
            if str(mapping["effect"]) == "deny":
                denies.append(reason)
            else:
                allows.append(reason)

        if denies:
            return LayerOutcome(deny=True, reasons=tuple(denies))
        if allows:
            return LayerOutcome(allow=True, reasons=tuple(allows))
        return LayerOutcome()

    # ----------------------------------------------------------------- agents
    def agent(
        self, resolved: ResolvedSubject, action: Action, resource: ResourceRef
    ) -> LayerOutcome:
        """Agent-level grants.

        An agent is an independent subject, so its authority comes from its own
        grants and is bounded by its own binding. It is never derived from the
        owner's authority, and it can never exceed it.
        """
        if resolved.subject.subject_type != "AGENT" or not resolved.subject.agent_id:
            return LayerOutcome()

        binding = Grant(
            scope="SPACE" if resolved.facts.get("agent_space_id") else "TENANT",
            tenant_id=resolved.facts.get("agent_tenant_id"),
            space_id=resolved.facts.get("agent_space_id"),
        )
        if not scope_covers(binding, resource):
            return LayerOutcome(deny=True, reasons=("agent-binding",))

        try:
            rows = self._repository.agent_grants(resolved.subject.agent_id)
        except AuthorizationUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - infrastructure failure
            raise AuthorizationUnavailable(str(exc)) from exc

        allows: list[str] = []
        denies: list[str] = []
        for row in rows:
            mapping = row._mapping
            if mapping["permission_id"] is None and mapping["tool_id"] is None:
                continue
            if not _same_action(mapping["action"], action):
                continue
            resource_type = mapping["resource_type"]
            if resource_type is not None and str(resource_type) != resource.type:
                continue
            reason = f"agent:{mapping['key'] or 'opaque'}:{action.name}"
            if str(mapping["effect"]) == "deny":
                denies.append(reason)
            else:
                allows.append(reason)

        if denies:
            return LayerOutcome(deny=True, reasons=tuple(denies))
        if allows:
            return LayerOutcome(allow=True, reasons=tuple(allows))
        return LayerOutcome()

    # ------------------------------------------------------------------- ACL
    def acl(
        self, resolved: ResolvedSubject, action: Action, resource: ResourceRef
    ) -> LayerOutcome:
        """Resource-specific grants for one resource instance."""
        try:
            rows = self._repository.acl_entries(resource.id)
        except AuthorizationUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - infrastructure failure
            raise AuthorizationUnavailable(str(exc)) from exc

        expected_key = _SUBJECT_TYPE_KEYS[resolved.subject.subject_type]
        subject_id = resolved.subject.subject_id

        allows: list[str] = []
        denies: list[str] = []
        for row in rows:
            mapping = row._mapping
            if str(mapping["subject_type"]) != expected_key:
                continue
            if str(mapping["subject_id"]) != subject_id:
                continue
            if not _same_action(mapping["action"], action):
                continue
            if _expired(mapping["expires_at"]):
                # An expired grant no longer exists: it neither allows nor denies.
                continue
            reason = f"acl:{mapping['action']}"
            if str(mapping["effect"]) == "deny":
                denies.append(reason)
            else:
                allows.append(reason)

        if denies:
            return LayerOutcome(deny=True, reasons=tuple(denies))
        if allows:
            return LayerOutcome(allow=True, reasons=tuple(allows))
        return LayerOutcome()

    # ------------------------------------------------------------------ tools
    def tool(
        self,
        rows: list[Any],
        action: Action,
        resource: ResourceRef,
        scope: str | None = None,
    ) -> LayerOutcome:
        """Structured tool grants, matched on the ``(type, action, scope)`` triple."""
        allows: list[str] = []
        denies: list[str] = []
        for row in rows:
            mapping = row._mapping
            if not _same_action(mapping["action"], action):
                continue
            resource_type = mapping["resource_type"]
            if resource_type is not None and str(resource_type) != resource.type:
                continue
            granted_scope = mapping["scope"]
            if granted_scope is not None and scope is not None:
                if str(granted_scope) != scope:
                    continue
            reason = f"tool:{mapping['key']}"
            if str(mapping["effect"]) == "deny":
                denies.append(reason)
            else:
                allows.append(reason)

        if denies:
            return LayerOutcome(deny=True, reasons=tuple(denies))
        if allows:
            return LayerOutcome(allow=True, reasons=tuple(allows))
        return LayerOutcome()


__all__ = ["PermissionResolver"]
