"""P17 WAVE 3–4 — canonical authorization + membership mutation (real database).

Everything runs on a dedicated database ``uap_p17_auth_test`` migrated to head
with the **official** privilege materialization. Structural objects and their
canonical resource projections are created through the control-plane
provisioning boundary (never a raw ``INSERT INTO resources``), role permission
assignments use the existing ``role_permissions`` model, and every behavioural
assertion executes as ``uap_runtime`` through the P17 use cases.

Matrix covered here: PASS-1…PASS-5, N1…N17 except the API-surface cases, the
resource-absence fail-closed rule, the provisioning→ALLOW rule and the
privilege boundary of §27.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from scripts.privileges import materialize as materialize_baseline_privileges
from services.control_plane import (
    MEMBER_RESOURCE_TYPE,
    ensure_resource_projection,
    provision_space,
    provision_tenant,
)
from services.identity_runtime import (
    ErrorCode,
    IdentityRuntimeError,
    MembershipAuthorizer,
    RuntimeContextResolver,
)
from services.use_cases import (
    create_space_membership,
    create_tenant_membership,
    delete_space_membership,
    delete_tenant_membership,
    list_space_members,
    list_spaces,
    list_tenant_members,
    list_tenants,
    update_space_membership,
    update_tenant_membership,
)

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P17_DB = "uap_p17_auth_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P17_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P17_DB}"

PERMISSION_KEYS = {
    "admin": ("member.read", "member.admin"),
    "read": ("member.read",),
    "none": (),
}


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
    materialize_baseline_privileges(fixtures)
    yield fixtures
    fixtures.dispose()
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P17_DB}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def db(engine):
    """Runtime-identity database; depends on ``engine`` so the DB exists first."""
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime"
    )
    database.start()
    yield database
    database.dispose()


def _user(conn, email: str) -> str:
    return str(
        conn.execute(
            sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
            {"e": email},
        ).scalar_one()
    )


def _role(conn, *, scope: str, tenant_id: str | None, space_id: str | None, permissions: str) -> str:
    role_id = str(
        conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, is_system, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), :k, :n, :scope, false, 'active')"
                " RETURNING id"
            ),
            {"t": tenant_id, "s": space_id, "k": f"p17_{uuid.uuid4().hex[:10]}",
             "n": f"P17 {scope} role", "scope": scope},
        ).scalar_one()
    )
    for key in PERMISSION_KEYS[permissions]:
        conn.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id, effect)"
                " SELECT CAST(:r AS uuid), p.id, 'allow' FROM permissions p WHERE p.key = :key"
            ),
            {"r": role_id, "key": key},
        )
    return role_id


@pytest.fixture(scope="module")
def ids(engine) -> dict[str, object]:
    out: dict[str, object] = {}
    with engine.begin() as conn:
        session = Session(bind=conn)
        tenant_a = provision_tenant(session, slug=f"p17a-{uuid.uuid4().hex[:8]}", display_name="P17 A")
        tenant_b = provision_tenant(session, slug=f"p17b-{uuid.uuid4().hex[:8]}", display_name="P17 B")
        space_a1 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a1-{uuid.uuid4().hex[:6]}",
            name="Space A1", visibility="tenant",
        )
        space_a2 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a2-{uuid.uuid4().hex[:6]}",
            name="Space A2", visibility="link",
        )
        space_b1 = provision_space(
            session, tenant_id=tenant_b["tenant_id"], key=f"b1-{uuid.uuid4().hex[:6]}",
            name="Space B1", visibility="tenant",
        )
        out.update(
            tenant_a=tenant_a["tenant_id"], tenant_b=tenant_b["tenant_id"],
            space_a1=space_a1["space_id"], space_a2=space_a2["space_id"],
            space_b1=space_b1["space_id"],
            tenant_a_members=tenant_a["member_collection"],
            space_a1_members=space_a1["member_collection"],
        )
        out["operator"] = _user(conn, f"p17-op-{uuid.uuid4().hex[:8]}@example.invalid")
        out["peer"] = _user(conn, f"p17-peer-{uuid.uuid4().hex[:8]}@example.invalid")
        out["outsider"] = _user(conn, f"p17-out-{uuid.uuid4().hex[:8]}@example.invalid")
        out["target"] = _user(conn, f"p17-target-{uuid.uuid4().hex[:8]}@example.invalid")
        out["platform"] = _user(conn, f"p17-plat-{uuid.uuid4().hex[:8]}@example.invalid")
        out["spare"] = _user(conn, f"p17-spare-{uuid.uuid4().hex[:8]}@example.invalid")

        role_admin_a = _role(conn, scope="TENANT", tenant_id=out["tenant_a"], space_id=None,
                             permissions="admin")
        role_read_a = _role(conn, scope="TENANT", tenant_id=out["tenant_a"], space_id=None,
                            permissions="read")
        role_admin_b = _role(conn, scope="TENANT", tenant_id=out["tenant_b"], space_id=None,
                             permissions="admin")
        role_space_admin_a1 = _role(conn, scope="SPACE", tenant_id=None,
                                    space_id=out["space_a1"], permissions="admin")
        role_space_plain_a1 = _role(conn, scope="SPACE", tenant_id=None,
                                    space_id=out["space_a1"], permissions="none")
        role_space_admin_b1 = _role(conn, scope="SPACE", tenant_id=None,
                                    space_id=out["space_b1"], permissions="admin")
        out.update(
            role_admin_a=role_admin_a, role_read_a=role_read_a, role_admin_b=role_admin_b,
            role_space_admin_a1=role_space_admin_a1, role_space_plain_a1=role_space_plain_a1,
            role_space_admin_b1=role_space_admin_b1,
        )
        for user, tenant, role in (
            (out["operator"], out["tenant_a"], role_admin_a),
            (out["peer"], out["tenant_a"], role_read_a),
            (out["target"], out["tenant_a"], role_read_a),
            (out["outsider"], out["tenant_b"], role_admin_b),
        ):
            conn.execute(
                sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                    " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
                ),
                {"t": tenant, "u": user, "r": role},
            )
        for user, tenant, space, role in (
            (out["operator"], out["tenant_a"], out["space_a1"], role_space_admin_a1),
            (out["target"], out["tenant_a"], out["space_a1"], role_space_plain_a1),
            (out["outsider"], out["tenant_b"], out["space_b1"], role_space_admin_b1),
        ):
            conn.execute(
                sa.text(
                    "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
                    " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                    " CAST(:r AS uuid), 'active')"
                ),
                {"t": tenant, "s": space, "u": user, "r": role},
            )
        # Explicit platform authority: P13's platform_admin holds the 12 canonical
        # permissions at PLATFORM scope. It is never used as a fallback.
        conn.execute(
            sa.text(
                "INSERT INTO platform_memberships (user_id, role_id, status)"
                " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
                " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
            ),
            {"u": out["platform"]},
        )
    return out


def _rows(engine, sql: str, **params) -> list[dict]:
    with engine.begin() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


def _memberships(engine, *, tenant_id: str, user_id: str) -> list[dict]:
    return _rows(
        engine,
        "SELECT status, role_id FROM tenant_memberships"
        " WHERE tenant_id = CAST(:t AS uuid) AND user_id = CAST(:u AS uuid)",
        t=tenant_id, u=user_id,
    )


def _audits(engine, *, action: str) -> list[dict]:
    return _rows(
        engine,
        "SELECT * FROM audit_logs WHERE action = :a ORDER BY occurred_at DESC LIMIT 5",
        a=action,
    )


# ------------------------------------------------------------------- PASS-1..5
def test_pass1_tenant_membership_read(db, ids) -> None:
    rows = list_tenant_members(db, actor_id=ids["operator"], tenant_id=ids["tenant_a"])
    assert {str(row["user_id"]) for row in rows} >= {ids["operator"], ids["peer"], ids["target"]}


def test_pass2_tenant_membership_mutation(db, engine, ids) -> None:
    membership_id = create_tenant_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"],
        user_id=ids["outsider"], role_id=ids["role_admin_a"], correlation_id=str(uuid.uuid4()),
    )
    assert membership_id
    assert [row["status"] for row in _memberships(engine, tenant_id=ids["tenant_a"],
                                                  user_id=ids["outsider"])] == ["active"]
    update_tenant_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], user_id=ids["outsider"],
        role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
    )
    assert _memberships(engine, tenant_id=ids["tenant_a"], user_id=ids["outsider"])[0]["role_id"] \
        == uuid.UUID(str(ids["role_read_a"]))
    delete_tenant_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], user_id=ids["outsider"],
        correlation_id=str(uuid.uuid4()),
    )
    assert _memberships(engine, tenant_id=ids["tenant_a"], user_id=ids["outsider"])[0]["status"] \
        == "removed"
    assert len(_audits(engine, action="create")) >= 1


def test_pass3_space_membership_read(db, ids) -> None:
    rows = list_space_members(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"]
    )
    assert {str(row["user_id"]) for row in rows} == {ids["operator"], ids["target"]}


def test_pass4_space_membership_mutation(db, engine, ids) -> None:
    membership_id = create_space_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"],
        user_id=ids["peer"], role_id=ids["role_space_plain_a1"],
        correlation_id=str(uuid.uuid4()),
    )
    assert membership_id
    assert _rows(
        engine,
        "SELECT status FROM memberships WHERE tenant_id = CAST(:t AS uuid)"
        " AND space_id = CAST(:s AS uuid) AND user_id = CAST(:u AS uuid)",
        t=ids["tenant_a"], s=ids["space_a1"], u=ids["peer"],
    ) == [{"status": "active"}]
    update_space_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"],
        user_id=ids["peer"], role_id=ids["role_space_admin_a1"],
        correlation_id=str(uuid.uuid4()),
    )
    delete_space_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"],
        user_id=ids["peer"], correlation_id=str(uuid.uuid4()),
    )
    assert _rows(
        engine,
        "SELECT status FROM memberships WHERE tenant_id = CAST(:t AS uuid)"
        " AND space_id = CAST(:s AS uuid) AND user_id = CAST(:u AS uuid)",
        t=ids["tenant_a"], s=ids["space_a1"], u=ids["peer"],
    ) == [{"status": "removed"}]


def test_pass5_platform_admin_is_explicit_authority(db, engine, ids) -> None:
    """PASS-5: explicit platform authority works, and only as a real grant."""
    membership_id = create_tenant_membership(
        db, actor_id=ids["platform"], tenant_id=ids["tenant_a"],
        user_id=ids["spare"], role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
    )
    assert membership_id
    delete_tenant_membership(
        db, actor_id=ids["platform"], tenant_id=ids["tenant_a"], user_id=ids["spare"],
        correlation_id=str(uuid.uuid4()),
    )
    assert _memberships(engine, tenant_id=ids["tenant_a"], user_id=ids["spare"])[0]["status"] \
        == "removed"


# ------------------------------------------------------------------ N1..N13
def test_n1_n12_cross_tenant_and_forged_path_are_denied(db, engine, ids) -> None:
    before = len(_rows(engine, "SELECT id FROM tenant_memberships"))
    for actor, tenant in ((ids["operator"], ids["tenant_b"]), (ids["outsider"], ids["tenant_a"])):
        with pytest.raises(IdentityRuntimeError) as exc:
            create_tenant_membership(
                db, actor_id=actor, tenant_id=tenant, user_id=ids["target"],
                role_id=ids["role_admin_a"], correlation_id=str(uuid.uuid4()),
            )
        assert exc.value.code in {ErrorCode.MEMBERSHIP_REQUIRED, ErrorCode.AUTHORIZATION_DENIED}
    assert len(_rows(engine, "SELECT id FROM tenant_memberships")) == before


def test_n2_n7_n13_cross_space_and_forged_space_are_denied(db, engine, ids) -> None:
    before = len(_rows(engine, "SELECT id FROM memberships"))
    with pytest.raises(IdentityRuntimeError):
        create_space_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a2"],
            user_id=ids["target"], role_id=ids["role_space_plain_a1"],
            correlation_id=str(uuid.uuid4()),
        )
    with pytest.raises(IdentityRuntimeError):
        create_space_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_b1"],
            user_id=ids["target"], role_id=ids["role_space_admin_b1"],
            correlation_id=str(uuid.uuid4()),
        )
    assert len(_rows(engine, "SELECT id FROM memberships")) == before


def test_n3_tenant_role_cannot_manage_another_tenant(db, engine, ids) -> None:
    """Tenant B's admin role must not reach Tenant A (no scope interchange)."""
    before = len(_rows(engine, "SELECT id FROM tenant_memberships"))
    with pytest.raises(IdentityRuntimeError) as exc:
        create_tenant_membership(
            db, actor_id=ids["target"], tenant_id=ids["tenant_b"], user_id=ids["peer"],
            role_id=ids["role_admin_b"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code in {ErrorCode.MEMBERSHIP_REQUIRED, ErrorCode.AUTHORIZATION_DENIED}
    assert len(_rows(engine, "SELECT id FROM tenant_memberships")) == before


def test_n4_space_role_cannot_manage_tenant_membership(db, engine, ids) -> None:
    """N4 · Q4: a space-scoped role never authorizes a tenant-level mutation."""
    # `peer` holds only a space role in A1 (no member.admin at tenant level).
    before = len(_rows(engine, "SELECT id FROM tenant_memberships"))
    with pytest.raises(IdentityRuntimeError) as exc:
        create_tenant_membership(
            db, actor_id=ids["peer"], tenant_id=ids["tenant_a"], user_id=ids["outsider"],
            role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code in {ErrorCode.AUTHORIZATION_DENIED, ErrorCode.MEMBERSHIP_REQUIRED}
    assert len(_rows(engine, "SELECT id FROM tenant_memberships")) == before


def test_n5_tenant_role_cannot_manage_an_arbitrary_space(db, engine, ids) -> None:
    """N5 · Q5: tenant authority does not extend to a space the actor is not in."""
    before = len(_rows(engine, "SELECT id FROM memberships"))
    with pytest.raises(IdentityRuntimeError) as exc:
        create_space_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a2"],
            user_id=ids["peer"], role_id=ids["role_space_admin_a1"],
            correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED
    assert len(_rows(engine, "SELECT id FROM memberships")) == before


def test_n6_actor_outside_the_tenant_is_denied(db, engine, ids) -> None:
    with pytest.raises(IdentityRuntimeError) as exc:
        list_tenant_members(db, actor_id=ids["outsider"], tenant_id=ids["tenant_a"])
    assert exc.value.code == ErrorCode.MEMBERSHIP_REQUIRED


def test_n8_target_user_outside_the_tenant_is_denied(db, engine, ids) -> None:
    """N8: a space membership cannot create tenant standing for its target."""
    before = len(_rows(engine, "SELECT id FROM memberships"))
    with pytest.raises(IdentityRuntimeError) as exc:
        create_space_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"],
            user_id=ids["outsider"], role_id=ids["role_space_plain_a1"],
            correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code == ErrorCode.TARGET_NOT_IN_TENANT
    assert len(_rows(engine, "SELECT id FROM memberships")) == before


def test_n9_wrong_role_scope_is_denied(db, engine, ids) -> None:
    before = len(_rows(engine, "SELECT id FROM tenant_memberships"))
    with pytest.raises(IdentityRuntimeError) as exc:
        create_tenant_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], user_id=ids["peer"],
            role_id=ids["role_space_admin_a1"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code == ErrorCode.ROLE_SCOPE_MISMATCH
    with pytest.raises(IdentityRuntimeError) as exc:
        create_space_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"],
            user_id=ids["peer"], role_id=ids["role_admin_a"],
            correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code == ErrorCode.ROLE_SCOPE_MISMATCH
    assert len(_rows(engine, "SELECT id FROM tenant_memberships")) == before


def test_n11_visibility_never_bypasses_authorization(db, ids) -> None:
    """N11: ``link`` (the most permissive canonical visibility) grants nothing."""
    with pytest.raises(IdentityRuntimeError) as exc:
        list_space_members(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a2"]
        )
    assert exc.value.code == ErrorCode.SPACE_SCOPE_DENIED


def test_n14_n15_n16_n17_registries_are_read_only_for_the_runtime(engine, db) -> None:
    """The runtime principal physically cannot mutate the registries (§27)."""
    statements = (
        "INSERT INTO platform_memberships (user_id, role_id, status)"
        " SELECT :u::uuid, id, 'active' FROM roles WHERE key = 'platform_admin'",
        "UPDATE roles SET name = 'x' WHERE key = 'platform_admin'",
        "INSERT INTO permissions (key, resource_type, action) VALUES ('p17.x', 'x', 'read')",
        "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id, action, effect)"
        " SELECT r.id, a.id, :u::uuid, 'read', 'allow' FROM resources r, acl_subject_types a LIMIT 1",
    )
    params = {"u": str(uuid.uuid4())}
    with engine.begin() as conn:
        before = {
            table: conn.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in ("platform_memberships", "roles", "permissions", "resource_permissions")
        }
    for statement in statements:
        with db.transaction() as session:
            with pytest.raises(sa.exc.SQLAlchemyError):
                session.execute(sa.text(statement), params)
    with engine.begin() as conn:
        after = {
            table: conn.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in ("platform_memberships", "roles", "permissions", "resource_permissions")
        }
    assert before == after


# ------------------------------------------------------ resource provisioning
def test_resource_projection_exists_for_every_provisioned_object(engine, ids) -> None:
    """§75: object exists ⇒ canonical resource exists (projection consistency)."""
    rows = _rows(
        engine,
        "SELECT tenant_id, space_id, resource_type, natural_key FROM resources"
        " WHERE deleted_at IS NULL",
    )
    tenant_a = uuid.UUID(str(ids["tenant_a"]))
    space_a1 = uuid.UUID(str(ids["space_a1"]))
    assert ("tenant", tenant_a, None) in {
        (r["resource_type"], r["tenant_id"], r["space_id"]) for r in rows
    }
    assert (MEMBER_RESOURCE_TYPE, tenant_a, None) in {
        (r["resource_type"], r["tenant_id"], r["space_id"]) for r in rows
    }
    assert ("space", tenant_a, space_a1) in {
        (r["resource_type"], r["tenant_id"], r["space_id"]) for r in rows
    }
    assert (MEMBER_RESOURCE_TYPE, tenant_a, space_a1) in {
        (r["resource_type"], r["tenant_id"], r["space_id"]) for r in rows
    }


def test_provisioning_is_idempotent(engine, ids) -> None:
    with engine.begin() as conn:
        session = Session(bind=conn)
        before = conn.execute(sa.text("SELECT count(*) FROM resources")).scalar_one()
        ensure_resource_projection(session, tenant_id=str(ids["tenant_a"]))
        ensure_resource_projection(
            session, tenant_id=str(ids["tenant_a"]), space_id=str(ids["space_a1"])
        )
        after = conn.execute(sa.text("SELECT count(*) FROM resources")).scalar_one()
    assert before == after


def test_n10_resource_absence_denies_and_writes_nothing(engine, db, ids) -> None:
    """Removing the canonical projection turns an otherwise-ALLOW op into DENY."""
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "DELETE FROM resources WHERE tenant_id = CAST(:t AS uuid)"
                " AND resource_type = :rtype AND space_id IS NULL"
            ),
            {"t": ids["tenant_a"], "rtype": MEMBER_RESOURCE_TYPE},
        )
    try:
        with pytest.raises(IdentityRuntimeError) as exc:
            list_tenant_members(db, actor_id=ids["operator"], tenant_id=ids["tenant_a"])
        assert exc.value.code == ErrorCode.RESOURCE_NOT_PROVISIONED
        before = len(_rows(engine, "SELECT id FROM tenant_memberships"))
        with pytest.raises(IdentityRuntimeError) as exc:
            create_tenant_membership(
                db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], user_id=ids["peer"],
                role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
            )
        assert exc.value.code == ErrorCode.RESOURCE_NOT_PROVISIONED
        assert len(_rows(engine, "SELECT id FROM tenant_memberships")) == before
    finally:
        with engine.begin() as conn:
            ensure_resource_projection(Session(bind=conn), tenant_id=str(ids["tenant_a"]))


def test_use_case_surface_has_no_structural_write() -> None:
    """No tenant/space/platform/role/permission/ACL write surface exists in P17."""
    source = (ROOT / "services" / "use_cases" / "identity_runtime.py").read_text(encoding="utf-8")
    for forbidden in ("provision_tenant", "provision_space", "platform_memberships",
                      "INSERT INTO tenants", "INSERT INTO spaces"):
        assert forbidden not in source
