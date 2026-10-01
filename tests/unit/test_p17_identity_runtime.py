"""P17 WAVE 1–2 unit contract (identity / tenant / space / membership runtime).

Pure unit level: no database, no transport. The resolver is driven through fake
repositories so the *denial order* and the *scope predicates* are pinned without
an integration dependency. The authorization-dependent half of the P17 test
matrix is intentionally absent here — see
``docs/architecture/P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md``.
"""

from __future__ import annotations

import pytest

from services.identity_runtime import (
    ErrorCode,
    IdentityRuntimeError,
    MembershipRuntime,
    ResolvedContext,
    RuntimeContextResolver,
)

TENANT_A = "11111111-1111-7111-8111-111111111111"
TENANT_B = "22222222-2222-7222-8222-222222222222"
SPACE_A1 = "33333333-3333-7333-8333-333333333333"
SPACE_B1 = "44444444-4444-7444-8444-444444444444"
USER = "55555555-5555-7555-8555-555555555555"
TENANT_ROLE = "66666666-6666-7666-8666-666666666666"
SPACE_ROLE = "77777777-7777-7777-8777-777777777777"


class _Tenants:
    def __init__(self, *, readable: dict | None) -> None:
        self._readable = readable

    def get_member_tenant(self, session, *, tenant_id: str, actor_id: str):
        return self._readable

    def list_member_tenants(self, session, *, actor_id: str):
        return [self._readable] if self._readable else []


class _Spaces:
    def __init__(self, *, belongs: bool, visible: dict | None) -> None:
        self._belongs = belongs
        self._visible = visible

    def space_belongs_to_tenant(self, session, *, tenant_id: str, space_id: str) -> bool:
        return self._belongs

    def get_member_space(self, session, *, tenant_id: str, space_id: str, actor_id: str):
        return self._visible

    def list_member_spaces(self, session, *, tenant_id: str, actor_id: str):
        return [self._visible] if self._visible else []


class _Memberships:
    def __init__(self, tenant_membership, space_membership=None) -> None:
        self._tenant = tenant_membership
        self._space = space_membership

    def get_tenant_membership(self, session, *, tenant_id: str, user_id: str):
        return self._tenant

    def get_space_membership(self, session, *, tenant_id: str, space_id: str, user_id: str):
        return self._space


def _tenant_membership(status: str = "active") -> dict:
    return {"id": "m1", "tenant_id": TENANT_A, "user_id": USER,
            "role_id": TENANT_ROLE, "status": status}


def _resolver(*, tenants=None, spaces=None, memberships=None) -> RuntimeContextResolver:
    return RuntimeContextResolver(
        tenants=tenants if tenants is not None else _Tenants(readable={"id": TENANT_A, "status": "active"}),
        spaces=spaces if spaces is not None else _Spaces(belongs=True, visible={"id": SPACE_A1, "status": "active"}),
        memberships=memberships if memberships is not None else _Memberships(_tenant_membership()),
    )


# ------------------------------------------------------------------ identity
def test_missing_tenant_membership_is_denied() -> None:
    resolver = _resolver(memberships=_Memberships(None))
    with pytest.raises(IdentityRuntimeError) as exc:
        resolver.resolve(None, actor_id=USER, tenant_id=TENANT_A)
    assert exc.value.code == ErrorCode.MEMBERSHIP_REQUIRED


def test_inactive_tenant_membership_is_denied() -> None:
    resolver = _resolver(memberships=_Memberships(_tenant_membership("suspended")))
    with pytest.raises(IdentityRuntimeError) as exc:
        resolver.resolve(None, actor_id=USER, tenant_id=TENANT_A)
    assert exc.value.code == ErrorCode.MEMBERSHIP_REQUIRED


def test_tenant_that_is_not_readable_by_the_actor_is_denied() -> None:
    resolver = _resolver(tenants=_Tenants(readable=None))
    with pytest.raises(IdentityRuntimeError) as exc:
        resolver.resolve(None, actor_id=USER, tenant_id=TENANT_A)
    assert exc.value.code == ErrorCode.TENANT_SCOPE_DENIED


def test_resolved_context_carries_facts_and_no_authorization_verdict() -> None:
    context = _resolver().resolve(None, actor_id=USER, tenant_id=TENANT_A)
    assert isinstance(context, ResolvedContext)
    assert context.actor_id == USER
    assert context.tenant_id == TENANT_A
    assert context.tenant_role_id == TENANT_ROLE
    assert context.space_id is None
    assert not hasattr(context, "allowed")
    assert not hasattr(context, "effect")


# ------------------------------------------------------- tenant-only context
def test_tenant_only_context_is_valid_without_space() -> None:
    context = _resolver().resolve(None, actor_id=USER, tenant_id=TENANT_A)
    assert context.space_id is None


def test_selected_tenant_is_authoritative_for_a_multi_tenant_user() -> None:
    resolver = _resolver(
        tenants=_Tenants(readable={"id": TENANT_B, "status": "active"}),
        memberships=_Memberships({**_tenant_membership(), "tenant_id": TENANT_B}),
    )
    context = resolver.resolve(None, actor_id=USER, tenant_id=TENANT_B)
    assert context.tenant_id == TENANT_B
    assert context.tenant_id != TENANT_A


# --------------------------------------------------------------- space scope
def test_foreign_space_is_denied() -> None:
    resolver = _resolver(spaces=_Spaces(belongs=False, visible={"id": SPACE_B1, "status": "active"}))
    with pytest.raises(IdentityRuntimeError) as exc:
        resolver.resolve(None, actor_id=USER, tenant_id=TENANT_A, space_id=SPACE_B1)
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_space_membership_is_required_even_when_the_space_is_visible() -> None:
    """``spaces.visibility`` is metadata: it never substitutes for membership.

    ``Spaces.space_belongs_to_tenant`` is true (the space really is in the
    tenant) while the membership-joined read returns nothing, which is exactly
    what the scoped repository produces for a visible-but-unjoined space.
    """
    resolver = _resolver(
        spaces=_Spaces(belongs=True, visible=None),
        memberships=_Memberships(_tenant_membership(), None),
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        resolver.resolve(None, actor_id=USER, tenant_id=TENANT_A, space_id=SPACE_A1)
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_valid_space_context_resolves_the_space_role() -> None:
    resolver = _resolver(
        memberships=_Memberships(
            _tenant_membership(),
            {"id": "m2", "tenant_id": TENANT_A, "space_id": SPACE_A1,
             "user_id": USER, "role_id": SPACE_ROLE, "status": "active"},
        )
    )
    context = resolver.resolve(None, actor_id=USER, tenant_id=TENANT_A, space_id=SPACE_A1)
    assert context.space_id == SPACE_A1
    assert context.space_role_id == SPACE_ROLE


# ------------------------------------------------------- repository discipline
def test_repository_has_no_unscoped_accessors() -> None:
    """No generic ``get_by_id`` / ``list_all`` escape hatch exists (P17 §37)."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2] / "services" / "identity_runtime" / "repository.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("def get_by_id", "def list_all", "def fallback"):
        assert forbidden not in source
    assert source.count("WHERE") >= 10, "every lookup must carry an explicit scope predicate"


def test_membership_mutations_are_not_reachable_without_explicit_scope() -> None:
    """A mutation requires tenant + (space) + user + role: there is no shortcut."""
    import inspect

    for name in (
        "create_tenant_membership",
        "update_tenant_membership",
        "delete_tenant_membership",
        "create_space_membership",
        "update_space_membership",
        "delete_space_membership",
    ):
        signature = inspect.signature(getattr(MembershipRuntime, name))
        assert "tenant_id" in signature.parameters
        assert "user_id" in signature.parameters


# --------------------------------------------------- membership role integrity
class _ValidationRepo:
    def __init__(self, *, role: dict | None, target_in_tenant: bool = True) -> None:
        self._role = role
        self._target_in_tenant = target_in_tenant

    def user_exists(self, session, *, user_id: str) -> bool:
        return True

    def tenant_exists(self, session, *, tenant_id: str) -> bool:
        return True

    def has_active_tenant_membership(self, session, *, tenant_id: str, user_id: str) -> bool:
        return self._target_in_tenant

    def get_role(self, session, *, role_id: str):
        return self._role

    def get_tenant_membership(self, session, *, tenant_id: str, user_id: str):
        return None

    def get_space_membership(self, session, *, tenant_id: str, space_id: str, user_id: str):
        return None


def _role(*, scope: str, tenant_id: str | None = None, space_id: str | None = None) -> dict:
    return {"id": "r1", "tenant_id": tenant_id, "space_id": space_id,
            "key": "k", "scope": scope, "is_system": False, "status": "active"}


def test_tenant_membership_rejects_a_space_scoped_role() -> None:
    runtime = MembershipRuntime(repository=_ValidationRepo(role=_role(scope="SPACE", space_id=SPACE_A1)))
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_tenant_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.ROLE_SCOPE_MISMATCH


def test_tenant_membership_rejects_a_role_from_another_tenant() -> None:
    runtime = MembershipRuntime(
        repository=_ValidationRepo(role=_role(scope="TENANT", tenant_id=TENANT_B))
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_tenant_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.ROLE_SCOPE_MISMATCH


def test_space_membership_rejects_a_space_of_another_tenant() -> None:
    spaces = _Spaces(belongs=False, visible=None)
    runtime = MembershipRuntime(
        repository=_ValidationRepo(role=_role(scope="SPACE", space_id=SPACE_B1)),
        spaces=spaces,
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_space_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A, space_id=SPACE_B1,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_space_membership_rejects_a_tenant_scoped_role() -> None:
    runtime = MembershipRuntime(
        repository=_ValidationRepo(role=_role(scope="TENANT", tenant_id=TENANT_A)),
        spaces=_Spaces(belongs=True, visible={"id": SPACE_A1, "status": "active"}),
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_space_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A, space_id=SPACE_A1,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.ROLE_SCOPE_MISMATCH


def test_space_membership_rejects_a_target_outside_the_tenant() -> None:
    """N8: a space member must already belong to the owning tenant."""
    runtime = MembershipRuntime(
        repository=_ValidationRepo(
            role=_role(scope="SPACE", space_id=SPACE_A1), target_in_tenant=False
        ),
        spaces=_Spaces(belongs=True, visible={"id": SPACE_A1, "status": "active"}),
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_space_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A, space_id=SPACE_A1,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.TARGET_NOT_IN_TENANT


def test_duplicate_membership_is_not_silently_swallowed() -> None:
    """No upsert semantics: an existing membership is an explicit conflict."""

    class _Dup(_ValidationRepo):
        def get_tenant_membership(self, session, *, tenant_id: str, user_id: str):
            return {"id": "m1", "tenant_id": tenant_id, "user_id": user_id,
                    "role_id": "r1", "status": "active"}

    runtime = MembershipRuntime(
        repository=_Dup(role=_role(scope="TENANT", tenant_id=TENANT_A))
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_tenant_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.MEMBERSHIP_DUPLICATE


def test_unknown_target_user_or_role_is_not_found() -> None:
    class _NoUser(_ValidationRepo):
        def user_exists(self, session, *, user_id: str) -> bool:
            return False

    runtime = MembershipRuntime(
        repository=_NoUser(role=_role(scope="TENANT", tenant_id=TENANT_A))
    )
    with pytest.raises(IdentityRuntimeError) as exc:
        runtime.create_tenant_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.TARGET_NOT_FOUND

    missing_role = MembershipRuntime(repository=_ValidationRepo(role=None))
    with pytest.raises(IdentityRuntimeError) as exc:
        missing_role.create_tenant_membership(
            None, actor_id=USER, actor_type="USER", tenant_id=TENANT_A,
            user_id=USER, role_id="r1", correlation_id="c",
        )
    assert exc.value.code == ErrorCode.TARGET_NOT_FOUND
