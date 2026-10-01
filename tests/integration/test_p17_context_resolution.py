"""P17 WAVE 1–2 integration evidence on a real database.

Scope of this suite: tenant / space / membership **resolution** and the scope
discipline of its repositories. The authorization-dependent half of the P17
matrix (membership administration through the canonical decision path) is
blocked and documented in
``docs/architecture/P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md``.

Uses a dedicated database ``uap_p17_test`` migrated to head with the official
privilege materialization, so no frozen baseline (``uap`` / ``uap_b1_test`` /
``uap_test``) is touched. Behavioural assertions run as ``uap_runtime``.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from scripts.privileges import materialize as materialize_baseline_privileges
from services.identity_runtime import ErrorCode, IdentityRuntimeError, RuntimeContextResolver
from services.identity_runtime.repository import MembershipRepository, SpaceRepository, TenantRepository

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P17_DB = "uap_p17_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P17_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P17_DB}"


@pytest.fixture(scope="module")
def engine():
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P17_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{P17_DB}" OWNER uap_migrator'))
    admin.dispose()

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{P17_DB}"
    cfg.attributes["lock_mode"] = "wait"
    command.upgrade(cfg, "head")

    fixtures = sa.create_engine(FIXTURE_DSN)
    materialize_baseline_privileges(fixtures)  # official, versioned — never private GRANTs
    yield fixtures
    fixtures.dispose()

    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P17_DB}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def runtime(engine):
    runtime_engine = sa.create_engine(RUNTIME_DSN)
    yield runtime_engine
    runtime_engine.dispose()


def _seed(engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        for key, slug in (("tenant_a", "p17-a"), ("tenant_b", "p17-b")):
            ids[key] = str(
                conn.execute(
                    sa.text(
                        "INSERT INTO tenants (slug, display_name, status)"
                        " VALUES (:slug, :name, 'active') RETURNING id"
                    ),
                    {"slug": f"{slug}-{uuid.uuid4().hex[:8]}", "name": slug},
                ).scalar_one()
            )
        for key, tenant, visibility in (
            ("space_a1", "tenant_a", "tenant"),
            ("space_a2", "tenant_a", "tenant"),   # visible in tenant A, no membership
            ("space_b1", "tenant_b", "link"),
        ):
            ids[key] = str(
                conn.execute(
                    sa.text(
                        "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status)"
                        " VALUES (:t, :k, :n, 'team', :v, 'active') RETURNING id"
                    ),
                    {"t": ids[tenant], "k": f"p17-{key}-{uuid.uuid4().hex[:6]}",
                     "n": key, "v": visibility},
                ).scalar_one()
            )
        for key in ("user_1", "user_2", "user_3"):
            ids[key] = str(
                conn.execute(
                    sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                    {"e": f"{key}-{uuid.uuid4().hex[:8]}@example.invalid"},
                ).scalar_one()
            )
        # Trigger-enforced scope shape: TENANT role carries a tenant and no space;
        # SPACE role carries a space and no tenant.
        ids["role_a"] = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (:t, NULL, :k, 'Tenant A Role', 'TENANT', 'active') RETURNING id"
            ),
            {"t": ids["tenant_a"], "k": f"p17_role_a_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        ids["role_b"] = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (:t, NULL, :k, 'Tenant B Role', 'TENANT', 'active') RETURNING id"
            ),
            {"t": ids["tenant_b"], "k": f"p17_role_b_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        ids["space_role_a1"] = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (NULL, :s, :k, 'Space A1 Role', 'SPACE', 'active') RETURNING id"
            ),
            {"s": ids["space_a1"], "k": f"p17_srole_a1_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())

        # U1 belongs to Tenant A and Tenant B (multi-tenant, D05).
        conn.execute(
            sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
            ),
            {"t": ids["tenant_a"], "u": ids["user_1"], "r": ids["role_a"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
            ),
            {"t": ids["tenant_b"], "u": ids["user_1"], "r": ids["role_b"]},
        )
        # U2 belongs to Tenant B only.
        conn.execute(
            sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
            ),
            {"t": ids["tenant_b"], "u": ids["user_2"], "r": ids["role_b"]},
        )
        # U3 belongs to Tenant A only; used for the suspended/removed case.
        conn.execute(
            sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
            ),
            {"t": ids["tenant_a"], "u": ids["user_3"], "r": ids["role_a"]},
        )
        # U1 is in Space A1 only: not in A2, not in B1.
        conn.execute(
            sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active')"
            ),
            {"t": ids["tenant_a"], "s": ids["space_a1"], "u": ids["user_1"],
             "r": ids["space_role_a1"]},
        )
    return ids


@pytest.fixture(scope="module")
def ids(engine):
    return _seed(engine)


def _resolve(runtime, **kwargs):
    resolver = RuntimeContextResolver(
        tenants=TenantRepository(), spaces=SpaceRepository(), memberships=MembershipRepository()
    )
    with Session(runtime) as session:
        return resolver.resolve(session, **kwargs)


def test_tenant_context_resolves_for_a_member(runtime, ids) -> None:
    context = _resolve(runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_a"])
    assert context.tenant_id == ids["tenant_a"]
    assert context.tenant_role_id == ids["role_a"]
    assert context.space_id is None  # tenant-level context is legitimate


def test_multi_tenant_user_resolves_the_explicitly_selected_tenant(runtime, ids) -> None:
    a = _resolve(runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_a"])
    b = _resolve(runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_b"])
    assert a.tenant_id == ids["tenant_a"] and a.tenant_role_id == ids["role_a"]
    assert b.tenant_id == ids["tenant_b"] and b.tenant_role_id == ids["role_b"]
    assert a.tenant_id != b.tenant_id


def test_space_context_resolves_only_with_space_membership(runtime, ids) -> None:
    context = _resolve(
        runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"]
    )
    assert context.space_id == ids["space_a1"]
    assert context.space_role_id == ids["space_role_a1"]


def test_visible_space_without_membership_is_denied(runtime, ids) -> None:
    """N7: ``visibility`` is metadata; it never substitutes for membership."""
    with pytest.raises(IdentityRuntimeError) as exc:
        _resolve(
            runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_a"], space_id=ids["space_a2"]
        )
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_foreign_space_is_denied(runtime, ids) -> None:
    """N2/N4: a space of another tenant can never be reached."""
    with pytest.raises(IdentityRuntimeError) as exc:
        _resolve(
            runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_a"], space_id=ids["space_b1"]
        )
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_cross_tenant_context_is_denied(runtime, ids) -> None:
    """N1: an actor of Tenant B has no context in Tenant A."""
    with pytest.raises(IdentityRuntimeError) as exc:
        _resolve(runtime, actor_id=ids["user_2"], tenant_id=ids["tenant_a"])
    assert exc.value.code == ErrorCode.MEMBERSHIP_REQUIRED


def test_forged_tenant_and_space_pair_is_denied(runtime, ids) -> None:
    """N6: client-supplied ids are candidates, never authorization facts."""
    with pytest.raises(IdentityRuntimeError) as exc:
        _resolve(
            runtime, actor_id=ids["user_1"], tenant_id=ids["tenant_b"], space_id=ids["space_a1"]
        )
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_suspended_membership_is_not_resolvable(runtime, engine, ids) -> None:
    """A non-active tenant membership yields no context (fail closed)."""
    _set_status = (
        "UPDATE tenant_memberships SET status = :status"
        " WHERE tenant_id = CAST(:t AS uuid) AND user_id = CAST(:u AS uuid)"
    )
    params = {"t": ids["tenant_a"], "u": ids["user_3"], "status": "removed"}
    with engine.begin() as conn:
        conn.execute(sa.text(_set_status), params)
    try:
        with pytest.raises(IdentityRuntimeError) as exc:
            _resolve(runtime, actor_id=ids["user_3"], tenant_id=ids["tenant_a"])
        assert exc.value.code == ErrorCode.MEMBERSHIP_REQUIRED
    finally:
        params["status"] = "active"
        with engine.begin() as conn:
            conn.execute(sa.text(_set_status), params)


def test_tenant_and_space_lists_are_membership_scoped(runtime, ids) -> None:
    with Session(runtime) as session:
        tenants = TenantRepository().list_member_tenants(session, actor_id=ids["user_1"])
        spaces = SpaceRepository().list_member_spaces(
            session, tenant_id=ids["tenant_a"], actor_id=ids["user_1"]
        )
    assert sorted(str(t["id"]) for t in tenants) == sorted([ids["tenant_a"], ids["tenant_b"]])
    assert [str(s["id"]) for s in spaces] == [ids["space_a1"]]


def test_listed_tenants_never_include_a_foreign_tenant(runtime, ids) -> None:
    with Session(runtime) as session:
        tenants = TenantRepository().list_member_tenants(session, actor_id=ids["user_2"])
    assert [str(t["id"]) for t in tenants] == [ids["tenant_b"]]


def test_runtime_identity_holds_no_tenant_or_space_write_grant(runtime) -> None:
    """P17 privilege delta must stay 0: tenant/space stay SELECT-only (SEC-05)."""
    with runtime.begin() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT table_name, privilege_type FROM information_schema.role_table_grants"
                " WHERE grantee = 'uap_runtime' AND table_name IN ('tenants','spaces','roles',"
                " 'permissions','role_permissions','resource_permissions','platform_memberships')"
            )
        ).all()
    unexpected = sorted(
        f"{row[0]}:{row[1]}" for row in rows if row[1] != "SELECT"
    )
    assert not unexpected, unexpected
