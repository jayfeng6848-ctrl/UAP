"""Scope evaluation: coverage, narrowing and the context predicates.

Inheritance is explicit and downward only, and there is no resource parent
tree — so nothing can inherit implicitly. A grant may tighten an inherited
authority, never widen it.
"""

from __future__ import annotations

import pytest

from core.permission import Action, Grant, Subject
from core.permission.scope import (
    narrows_or_equals,
    owns_resource,
    scope_covers,
    scope_matches_predicate,
)
from core.resource import ResourceRef

PLATFORM_GRANT = Grant(scope="PLATFORM")
TENANT_GRANT = Grant(scope="TENANT", tenant_id="t1")
OTHER_TENANT_GRANT = Grant(scope="TENANT", tenant_id="t2")
SPACE_GRANT = Grant(scope="SPACE", tenant_id="t1", space_id="s1")

RESOURCE_T1_S1 = ResourceRef(type="order", id="o1", tenant_id="t1", space_id="s1")
RESOURCE_T1_S2 = ResourceRef(type="order", id="o2", tenant_id="t1", space_id="s2")
RESOURCE_T2_S1 = ResourceRef(type="order", id="o3", tenant_id="t2", space_id="s1")


def test_platform_grant_covers_everything() -> None:
    for resource in (RESOURCE_T1_S1, RESOURCE_T1_S2, RESOURCE_T2_S1):
        assert scope_covers(PLATFORM_GRANT, resource)


def test_tenant_grant_covers_its_own_tenant_only() -> None:
    assert scope_covers(TENANT_GRANT, RESOURCE_T1_S1)
    assert scope_covers(TENANT_GRANT, RESOURCE_T1_S2)
    assert not scope_covers(TENANT_GRANT, RESOURCE_T2_S1)


def test_space_grant_covers_its_own_space_only() -> None:
    assert scope_covers(SPACE_GRANT, RESOURCE_T1_S1)
    assert not scope_covers(SPACE_GRANT, RESOURCE_T1_S2)
    assert not scope_covers(SPACE_GRANT, RESOURCE_T2_S1)


def test_a_foreign_tenant_grant_never_covers() -> None:
    assert not scope_covers(OTHER_TENANT_GRANT, RESOURCE_T1_S1)


def test_a_space_grant_without_a_space_never_covers() -> None:
    assert not scope_covers(Grant(scope="SPACE", tenant_id="t1"), RESOURCE_T1_S1)


def test_a_space_grant_without_a_tenant_still_covers_its_space() -> None:
    """A space belongs to exactly one tenant, so a bare space grant is safe.

    This mirrors how the platform stores space roles: a space and no tenant.
    """
    assert scope_covers(Grant(scope="SPACE", space_id="s1"), RESOURCE_T1_S1)
    assert not scope_covers(Grant(scope="SPACE", space_id="s1"), RESOURCE_T1_S2)


def test_a_space_grant_with_a_mismatched_tenant_never_covers() -> None:
    assert not scope_covers(Grant(scope="SPACE", tenant_id="t2", space_id="s1"),
                            RESOURCE_T1_S1)


def test_unknown_scope_cannot_be_constructed() -> None:
    with pytest.raises(ValueError):
        Grant(scope="RESOURCE")
    with pytest.raises(ValueError):
        Grant(scope="SELF")


def test_narrowing_allows_equal_or_tighter_grants() -> None:
    assert narrows_or_equals(PLATFORM_GRANT, PLATFORM_GRANT)
    assert narrows_or_equals(TENANT_GRANT, PLATFORM_GRANT)
    assert narrows_or_equals(SPACE_GRANT, PLATFORM_GRANT)
    assert narrows_or_equals(SPACE_GRANT, TENANT_GRANT)


def test_narrowing_rejects_widening() -> None:
    assert not narrows_or_equals(PLATFORM_GRANT, TENANT_GRANT)
    assert not narrows_or_equals(TENANT_GRANT, SPACE_GRANT)
    assert not narrows_or_equals(OTHER_TENANT_GRANT, TENANT_GRANT)


def test_self_predicate_requires_a_user_owner() -> None:
    user = Subject(identity_id="u1", subject_type="USER")
    agent = Subject(identity_id="a1", subject_type="AGENT", agent_id="a1")
    owned = ResourceRef(
        type="doc", id="d1", tenant_id="t1", owner_identity_id="u1"
    )
    assert owns_resource(user, owned)
    assert not owns_resource(agent, owned)


def test_self_predicate_is_false_without_an_owner() -> None:
    user = Subject(identity_id="u1", subject_type="USER")
    unowned = ResourceRef(type="doc", id="d1", tenant_id="t1")
    assert not owns_resource(user, unowned)


def test_resource_predicate_is_true_and_self_is_not_a_stored_scope() -> None:
    user = Subject(identity_id="u1", subject_type="USER")
    assert scope_matches_predicate("RESOURCE", user, RESOURCE_T1_S1)
    assert not scope_matches_predicate("SELF", user, RESOURCE_T1_S1)
    assert not scope_matches_predicate("BOGUS", user, RESOURCE_T1_S1)


def test_scope_matchers_are_independent_of_action() -> None:
    # Scope is a property of the grant binding, never of the action taken.
    assert scope_covers(TENANT_GRANT, RESOURCE_T1_S1)
    # Action normalisation folds to the lowercase canonical form (``D-AUTH-25``),
    # but scope matching must not depend on it.
    assert Action("READ").name == "read"
