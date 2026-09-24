"""RBAC and ACL layer resolution, driven by a stub repository.

The database-backed ACL path cannot be exercised yet: ``acl_subject_types`` is
a migration-controlled registry whose rows are seeded at P13, and its protection
trigger rejects runtime inserts. Rather than bypass a deliberate control to make
a test pass, the layer logic is verified here with a stub repository, and the
end-to-end ACL assertions resume once the registry is seeded.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.permission import Action, Grant, Subject
from core.permission.vocabulary import normalize_action
from core.resource import ResourceRef
from services.authorization.permissions import PermissionResolver, _same_action
from services.authorization.subjects import ResolvedSubject

NOW = datetime.now(timezone.utc)


class _Row:
    """Minimal stand-in for a SQLAlchemy ``Row``."""

    def __init__(self, **values) -> None:
        self._mapping = dict(values)


class _StubRepository:
    def __init__(self, role_grants=(), acl=(), agent_grants=()) -> None:
        self._role_grants = list(role_grants)
        self._acl = list(acl)
        self._agent_grants = list(agent_grants)

    def role_grants(self, role_ids):
        return list(self._role_grants)

    def acl_entries(self, resource_id):
        return list(self._acl)

    def agent_grants(self, agent_id):
        return list(self._agent_grants)


RESOURCE = ResourceRef(type="order", id="o1", tenant_id="t1", space_id="s1")
ACTION = Action("read", "order")


def _resolved(**overrides) -> ResolvedSubject:
    subject = overrides.pop("subject", Subject(identity_id="u1", subject_type="USER"))
    defaults = {
        "subject": subject,
        "grants": (Grant(scope="PLATFORM"),),
        "role_ids": ("r1",),
        "role_keys": ("admin",),
    }
    defaults.update(overrides)
    return ResolvedSubject(**defaults)


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #
def _grant(**overrides):
    base = {
        "role_id": "r1",
        "key": "demo.read",
        "resource_type": None,
        "action": "read",
        "effect": "allow",
    }
    base.update(overrides)
    return _Row(**base)


def test_rbac_allow() -> None:
    resolver = PermissionResolver(_StubRepository(role_grants=[_grant()]))
    outcome = resolver.rbac(_resolved(), ACTION, RESOURCE)
    assert outcome.allow and not outcome.deny


def test_rbac_deny() -> None:
    resolver = PermissionResolver(
        _StubRepository(role_grants=[_grant(effect="deny")])
    )
    outcome = resolver.rbac(_resolved(), ACTION, RESOURCE)
    assert outcome.deny and not outcome.allow


def test_rbac_deny_wins_over_allow_in_the_same_layer() -> None:
    resolver = PermissionResolver(
        _StubRepository(role_grants=[_grant(), _grant(key="demo.revoke", effect="deny")])
    )
    assert resolver.rbac(_resolved(), ACTION, RESOURCE).deny is True


def test_rbac_abstains_for_an_unrelated_action() -> None:
    resolver = PermissionResolver(_StubRepository(role_grants=[_grant(action="delete")]))
    outcome = resolver.rbac(_resolved(), ACTION, RESOURCE)
    assert not outcome.allow and not outcome.deny


def test_rbac_abstains_for_an_unrelated_resource_type() -> None:
    resolver = PermissionResolver(
        _StubRepository(role_grants=[_grant(resource_type="invoice")])
    )
    assert not resolver.rbac(_resolved(), ACTION, RESOURCE).allow


def test_rbac_a_null_resource_type_matches_any_resource() -> None:
    resolver = PermissionResolver(_StubRepository(role_grants=[_grant(resource_type=None)]))
    assert resolver.rbac(_resolved(), ACTION, RESOURCE).allow


def test_rbac_action_comparison_is_case_insensitive() -> None:
    resolver = PermissionResolver(_StubRepository(role_grants=[_grant(action="read")]))
    assert resolver.rbac(_resolved(), ACTION, RESOURCE).allow


def test_same_action_matches_every_case_and_unicode_form_of_a_canonical_action() -> None:
    """``D-AUTH-25`` — the stored value may arrive in any spelling of ``read``.

    The storage boundary enforces the lowercase form, but the *comparison*
    must not depend on the caller having normalised first: both sides fold
    through the one canonical normaliser (NFKC + casefold).
    """
    for stored in ("read", "READ", " ReAd ", "Read", "\tREAD\n"):
        assert _same_action(stored, ACTION), stored
    # NFKC: a fullwidth ``ｒ`` (U+FF52) normalises to ASCII ``r`` — a look-alike
    # character must fold into the canonical action, not slip past it.
    assert normalize_action("\uff52ead") == "read"
    assert _same_action("\uff52ead", ACTION)


def test_same_action_never_matches_a_non_canonical_value() -> None:
    """``D-AUTH-24`` — an opaque stored action can never grant a canonical one."""
    for stored in ("x9.opaque", "", "   ", "readd", "read;drop"):
        assert not _same_action(stored, ACTION), stored


def test_same_action_survives_non_string_storage_without_raising() -> None:
    assert not _same_action(None, ACTION)
    assert not _same_action(7, ACTION)


def test_rbac_abstains_when_the_role_scope_does_not_reach() -> None:
    resolver = PermissionResolver(_StubRepository(role_grants=[_grant()]))
    foreign = _resolved(grants=(Grant(scope="TENANT", tenant_id="t2"),))
    assert not resolver.rbac(foreign, ACTION, RESOURCE).allow


def test_rbac_abstains_without_roles() -> None:
    resolver = PermissionResolver(_StubRepository(role_grants=[_grant()]))
    assert not resolver.rbac(_resolved(role_ids=(), grants=()), ACTION, RESOURCE).allow


# --------------------------------------------------------------------------- #
# ACL
# --------------------------------------------------------------------------- #
def _acl(**overrides):
    base = {
        "subject_id": "u1",
        "subject_type": "user",
        "action": "read",
        "effect": "allow",
        "inherited": False,
        "expires_at": None,
    }
    base.update(overrides)
    return _Row(**base)


def test_acl_allow() -> None:
    resolver = PermissionResolver(_StubRepository(acl=[_acl()]))
    outcome = resolver.acl(_resolved(), ACTION, RESOURCE)
    assert outcome.allow and not outcome.deny


def test_acl_deny() -> None:
    resolver = PermissionResolver(_StubRepository(acl=[_acl(effect="deny")]))
    assert resolver.acl(_resolved(), ACTION, RESOURCE).deny is True


def test_acl_ignores_another_subject() -> None:
    resolver = PermissionResolver(_StubRepository(acl=[_acl(subject_id="someone-else")]))
    assert not resolver.acl(_resolved(), ACTION, RESOURCE).allow


def test_acl_ignores_another_subject_type() -> None:
    resolver = PermissionResolver(_StubRepository(acl=[_acl(subject_type="role")]))
    assert not resolver.acl(_resolved(), ACTION, RESOURCE).allow


def test_acl_ignores_another_action() -> None:
    resolver = PermissionResolver(_StubRepository(acl=[_acl(action="delete")]))
    assert not resolver.acl(_resolved(), ACTION, RESOURCE).allow


def test_acl_ignores_an_expired_allow() -> None:
    resolver = PermissionResolver(
        _StubRepository(acl=[_acl(expires_at=NOW - timedelta(days=1))])
    )
    outcome = resolver.acl(_resolved(), ACTION, RESOURCE)
    assert not outcome.allow and not outcome.deny


def test_acl_ignores_an_expired_deny() -> None:
    resolver = PermissionResolver(
        _StubRepository(acl=[_acl(effect="deny", expires_at=NOW - timedelta(seconds=1))])
    )
    assert resolver.acl(_resolved(), ACTION, RESOURCE).deny is False


def test_acl_honours_a_future_expiry() -> None:
    resolver = PermissionResolver(
        _StubRepository(acl=[_acl(expires_at=NOW + timedelta(days=1))])
    )
    assert resolver.acl(_resolved(), ACTION, RESOURCE).allow is True


def test_acl_deny_wins_over_allow() -> None:
    resolver = PermissionResolver(_StubRepository(acl=[_acl(), _acl(effect="deny")]))
    assert resolver.acl(_resolved(), ACTION, RESOURCE).deny is True


def test_acl_matches_an_agent_subject_on_its_own_identifier() -> None:
    agent = Subject(identity_id="owner-1", subject_type="AGENT", agent_id="a1")
    resolver = PermissionResolver(_StubRepository(acl=[_acl(subject_type="agent", subject_id="a1")]))
    assert resolver.acl(_resolved(subject=agent), ACTION, RESOURCE).allow is True


def test_acl_abstains_when_there_are_no_entries() -> None:
    resolver = PermissionResolver(_StubRepository())
    outcome = resolver.acl(_resolved(), ACTION, RESOURCE)
    assert not outcome.allow and not outcome.deny


# --------------------------------------------------------------------------- #
# agent grants
# --------------------------------------------------------------------------- #
def _agent_row(**overrides):
    base = {
        "effect": "allow",
        "permission_id": "p1",
        "tool_id": None,
        "key": "demo.read",
        "resource_type": None,
        "action": "read",
    }
    base.update(overrides)
    return _Row(**base)


def _agent_subject() -> ResolvedSubject:
    return ResolvedSubject(
        subject=Subject(identity_id="owner-1", subject_type="AGENT", agent_id="a1"),
        grants=(),
        risk_ceiling="HIGH",
        facts={"agent_tenant_id": "t1", "agent_space_id": "s1"},
    )


def test_agent_grant_allows_within_its_binding() -> None:
    resolver = PermissionResolver(_StubRepository(agent_grants=[_agent_row()]))
    assert resolver.agent(_agent_subject(), ACTION, RESOURCE).allow is True


def test_agent_deny_is_honoured() -> None:
    resolver = PermissionResolver(
        _StubRepository(agent_grants=[_agent_row(effect="deny")])
    )
    assert resolver.agent(_agent_subject(), ACTION, RESOURCE).deny is True


def test_agent_is_denied_outside_its_space_binding() -> None:
    resolver = PermissionResolver(_StubRepository(agent_grants=[_agent_row()]))
    other_space = ResourceRef(type="order", id="o9", tenant_id="t1", space_id="s2")
    assert resolver.agent(_agent_subject(), ACTION, other_space).deny is True


def test_agent_is_denied_in_another_tenant() -> None:
    resolver = PermissionResolver(_StubRepository(agent_grants=[_agent_row()]))
    other_tenant = ResourceRef(type="order", id="o9", tenant_id="t2", space_id="s1")
    assert resolver.agent(_agent_subject(), ACTION, other_tenant).deny is True


def test_a_row_without_a_structured_target_grants_nothing() -> None:
    """A row carrying only an opaque restriction is not a grant."""
    resolver = PermissionResolver(
        _StubRepository(agent_grants=[_agent_row(permission_id=None, tool_id=None, key=None)])
    )
    outcome = resolver.agent(_agent_subject(), ACTION, RESOURCE)
    assert not outcome.allow and not outcome.deny


def test_a_tool_scoped_agent_row_is_a_target() -> None:
    resolver = PermissionResolver(
        _StubRepository(agent_grants=[_agent_row(permission_id=None, tool_id="t1")])
    )
    assert resolver.agent(_agent_subject(), ACTION, RESOURCE).allow is True


def test_agent_resolution_ignores_a_user_subject() -> None:
    resolver = PermissionResolver(_StubRepository(agent_grants=[_agent_row()]))
    assert not resolver.agent(_resolved(), ACTION, RESOURCE).allow


# --------------------------------------------------------------------------- #
# tool grants
# --------------------------------------------------------------------------- #
def test_tool_grant_matches_the_structured_triple() -> None:
    resolver = PermissionResolver(_StubRepository())
    rows = [_Row(**{"effect": "allow", "resource_type": "order", "action": "read",
                    "scope": "TENANT", "key": "demo.read"})]
    assert resolver.tool(rows, ACTION, RESOURCE, "TENANT").allow is True


def test_tool_grant_rejects_a_scope_mismatch() -> None:
    resolver = PermissionResolver(_StubRepository())
    rows = [_Row(**{"effect": "allow", "resource_type": "order", "action": "read",
                    "scope": "PLATFORM", "key": "demo.read"})]
    assert not resolver.tool(rows, ACTION, RESOURCE, "TENANT").allow


def test_tool_grant_deny_wins() -> None:
    resolver = PermissionResolver(_StubRepository())
    rows = [
        _Row(**{"effect": "allow", "resource_type": None, "action": "read",
                "scope": None, "key": "a"}),
        _Row(**{"effect": "deny", "resource_type": None, "action": "read",
                "scope": None, "key": "b"}),
    ]
    assert resolver.tool(rows, ACTION, RESOURCE, None).deny is True
