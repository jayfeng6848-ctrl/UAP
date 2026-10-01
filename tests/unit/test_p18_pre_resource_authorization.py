"""P18-D06 — pre-resource (platform-scope) authorization contract.

The canonical ``AuthorizationService`` gained one **additive** entry point: a
request with ``resource = None`` is evaluated on the platform scope alone, which
is what a structural operation needs *before* the object exists (P18-D06).

These tests pin the semantics without a database by driving the service through
a minimal fake repository, and they pin the failure modes that must never become
an allow: no declared resource type, a non-canonical action, a scope that is not
PLATFORM, and a deny row.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from core.permission import Action, AuthorizationRequest, Subject
from services.authorization import AuthorizationRepository, AuthorizationService

PLATFORM_ROLE = "platform-role"
TENANT_ROLE = "tenant-role"
PLATFORM_ACTOR = "11111111-1111-7111-8111-111111111111"
PLAIN_ACTOR = "22222222-2222-7222-8222-222222222222"


@dataclass
class _Row:
    """Minimal stand-in for a SQLAlchemy row (only ``_mapping`` is consumed)."""

    _mapping: dict


class _Repository(AuthorizationRepository):
    """Fake read-only authorization state (no database)."""

    def __init__(self, *, grants: dict[str, list[tuple[str, str, str]]] | None = None) -> None:
        # role_id -> [(permission_key, resource_type, action)] with effect allow
        self._grants = grants if grants is not None else {
            PLATFORM_ROLE: [("tenant.admin", "tenant", "admin")],
            TENANT_ROLE: [("member.admin", "member", "admin")],
        }
        self._role_scope = {
            PLATFORM_ROLE: ("PLATFORM", None, None),
            TENANT_ROLE: ("TENANT", None, None),
        }

    # subjects
    def get_user(self, user_id: str):
        if user_id not in (PLATFORM_ACTOR, PLAIN_ACTOR):
            return None
        return _Row({"id": user_id, "status": "active", "primary_identity_id": None})

    def role_ids_for_user(self, user_id: str, tenant_id, space_id):
        return [PLATFORM_ROLE] if user_id == PLATFORM_ACTOR else []

    def get_roles(self, role_ids):
        rows = []
        for role_id in role_ids:
            scope, tenant_id, space_id = self._role_scope[role_id]
            rows.append(
                _Row({
                    "id": role_id, "tenant_id": tenant_id, "space_id": space_id,
                    "key": role_id, "scope": scope, "status": "active",
                })
            )
        return rows

    def role_grants(self, role_ids):
        rows = []
        for role_id in role_ids:
            for key, resource_type, action in self._grants.get(role_id, []):
                rows.append(
                    _Row({
                        "role_id": role_id, "key": key, "resource_type": resource_type,
                        "action": action, "effect": "allow",
                    })
                )
        return rows

    def get_resource(self, resource_id: str):
        """No resource rows exist in this fake (mirrors an unprovisioned object)."""
        return None

    def acl_entries(self, resource_id: str):
        return []


def _service(repository: _Repository) -> AuthorizationService:
    return AuthorizationService(repository=repository)


def _pre_resource(actor: str, *, action: str = "admin", resource_type: str = "tenant"):
    return AuthorizationRequest(
        subject=Subject(identity_id=actor, subject_type="USER", actor_id=actor),
        action=Action(name=action, resource_type=resource_type),
        resource=None,
    )


def test_platform_scope_grant_allows_pre_resource_operation() -> None:
    decision = _service(_Repository()).authorize(_pre_resource(PLATFORM_ACTOR))
    assert decision.effect == "ALLOW"
    assert decision.allowed is True


def test_actor_without_platform_scope_is_denied() -> None:
    decision = _service(_Repository()).authorize(_pre_resource(PLAIN_ACTOR))
    assert decision.effect == "DENY"


def test_missing_declared_resource_type_is_denied() -> None:
    request = AuthorizationRequest(
        subject=Subject(identity_id=PLATFORM_ACTOR, subject_type="USER", actor_id=PLATFORM_ACTOR),
        action=Action(name="admin"),
        resource=None,
    )
    decision = _service(_Repository()).authorize(request)
    assert decision.effect == "DENY"
    assert decision.reason == "pre-resource-requires-declared-resource-type"


def test_declared_resource_type_must_match_the_permission() -> None:
    """A platform grant for tenant.admin must not authorize a space-scoped ask."""
    decision = _service(_Repository()).authorize(
        _pre_resource(PLATFORM_ACTOR, resource_type="space")
    )
    assert decision.effect == "DENY"


def test_non_canonical_action_is_denied() -> None:
    decision = _service(_Repository()).authorize(
        _pre_resource(PLATFORM_ACTOR, action="manage_tenant")
    )
    assert decision.effect == "DENY"
    assert decision.reason.startswith("non-canonical-action")


def test_tenant_scoped_grant_cannot_authorize_a_platform_operation() -> None:
    """Scope isolation: a non-PLATFORM grant never reaches the pre-resource path."""
    repository = _Repository(grants={TENANT_ROLE: [("tenant.admin", "tenant", "admin")]})

    class _TenantGrantRepository(_Repository):
        def role_ids_for_user(self, user_id: str, tenant_id, space_id):
            return [TENANT_ROLE] if user_id == PLATFORM_ACTOR else []

        def get_roles(self, role_ids):
            return [
                _Row({
                    "id": TENANT_ROLE, "tenant_id": "33333333-3333-7333-8333-333333333333",
                    "space_id": None, "key": "tenant_admin", "scope": "TENANT", "status": "active",
                })
            ]

    decision = _service(_TenantGrantRepository(grants=repository._grants)).authorize(
        _pre_resource(PLATFORM_ACTOR)
    )
    assert decision.effect == "DENY"


def test_deny_row_wins_over_allow_row() -> None:
    class _DenyRepository(_Repository):
        def role_grants(self, role_ids):
            rows = super().role_grants(role_ids)
            rows.append(
                _Row({
                    "role_id": PLATFORM_ROLE, "key": "explicit.deny", "resource_type": "tenant",
                    "action": "admin", "effect": "deny",
                })
            )
            return rows

    decision = _service(_DenyRepository()).authorize(_pre_resource(PLATFORM_ACTOR))
    assert decision.effect == "DENY"


def test_resource_bearing_requests_are_unchanged() -> None:
    """The additive path must not alter an ordinary (resource-bearing) request."""
    from core.resource import ResourceRef

    request = AuthorizationRequest(
        subject=Subject(identity_id=PLATFORM_ACTOR, subject_type="USER", actor_id=PLATFORM_ACTOR),
        action=Action(name="admin", resource_type="tenant"),
        resource=ResourceRef(type="tenant", id="44444444-4444-7444-8444-444444444444",
                             tenant_id="33333333-3333-7333-8333-333333333333"),
        tenant_id="33333333-3333-7333-8333-333333333333",
    )
    decision = _service(_Repository()).authorize(request)
    # The resource does not exist in this fake repository: it must still deny,
    # through the resource layer, exactly as before.
    assert decision.effect == "DENY"
    assert decision.reason.startswith("resource:")


def test_pre_resource_decision_is_audited() -> None:
    service = _service(_Repository())
    service.authorize(_pre_resource(PLATFORM_ACTOR))
    recent = service.audit_boundary.recent()
    assert recent, "every decision must produce an audit record"
    assert recent[-1].target_type == "tenant"
    assert recent[-1].decision == "ALLOW"
