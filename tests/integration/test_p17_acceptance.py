"""P17 ACCEPTANCE GATE — explicit acceptance suite (§7–§57 of the gate).

This file adds the scenarios the gate names but the implementation suite did not
yet carry as first-class evidence: tenant-scope→space-resource semantics (Q4/Q5
Cases A–D), platform authority without fallback, system-object write denial,
API-level audit + correlation, rowcount behaviour, audit content safety,
provisioning atomicity, projection consistency, production-event emptiness and
the P17 route inventory.

Runs on its own isolated database ``uap_p17_acceptance_test``; behaviour is
executed as ``uap_runtime``, provisioning as the fixture identity, and the
canonical privilege state comes from ``scripts.privileges.materialize()``.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import create_app
from config.settings import load_settings_from_env
from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from scripts.privileges import materialize as materialize_baseline_privileges
from services.authorization import AuthorizationService
from services.control_plane import (
    MEMBER_RESOURCE_TYPE,
    ProvisioningError,
    ensure_agent_projection,
    ensure_resource_projection,
    provision_space,
    provision_tenant,
)
from services.consumer.kernel import production_allowlist
from services.identity_runtime import ErrorCode, IdentityRuntimeError
from services.use_cases import (
    create_space_membership,
    create_tenant_membership,
    delete_tenant_membership,
    list_space_members,
    list_tenant_members,
    login,
    update_tenant_membership,
)
from tests.integration.wave2_testkit import enroll_device

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P17_DB = "uap_p17_acceptance_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P17_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P17_DB}"
PASSWORD = "P17-Acc-Passw0rd!"

#: The closed set of keys the P17 membership audit payload may carry (§30).
AUDIT_METADATA_KEYS = {"action", "target_user_id", "role_before", "role_after"}
FORBIDDEN_AUDIT_TEXT = ("password", "passw0rd", "bearer", "authorization", "select ", "traceback")


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
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime"
    )
    database.start()
    yield database
    database.dispose()


def _role(conn, *, scope: str, tenant_id: str | None, space_id: str | None, admin: bool) -> str:
    role_id = str(conn.execute(
        sa.text(
            "INSERT INTO roles (tenant_id, space_id, key, name, scope, is_system, status)"
            " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), :k, 'P17 acceptance role', :scope,"
            " false, 'active') RETURNING id"
        ),
        {"t": tenant_id, "s": space_id, "k": f"p17acc_{uuid.uuid4().hex[:10]}", "scope": scope},
    ).scalar_one())
    for key in (("member.read", "member.admin") if admin else ("member.read",)):
        conn.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id, effect)"
                " SELECT CAST(:r AS uuid), p.id, 'allow' FROM permissions p WHERE p.key = :key"
            ),
            {"r": role_id, "key": key},
        )
    return role_id


def _user(conn, tag: str) -> str:
    return str(conn.execute(
        sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
        {"e": f"p17acc-{tag}-{uuid.uuid4().hex[:8]}@example.invalid"},
    ).scalar_one())


@pytest.fixture(scope="module")
def ids(engine) -> dict[str, str]:
    out: dict[str, str] = {}
    stamp = uuid.uuid4().hex[:8]
    with engine.begin() as conn:
        session = Session(bind=conn)
        tenant_a = provision_tenant(session, slug=f"p17acc-a-{stamp}", display_name="Acc A")
        tenant_b = provision_tenant(session, slug=f"p17acc-b-{stamp}", display_name="Acc B")
        space_a1 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a1-{stamp}", name="A1",
            visibility="tenant",
        )
        space_a2 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a2-{stamp}", name="A2",
            visibility="link",  # the most permissive canonical value (§18)
        )
        space_b1 = provision_space(
            session, tenant_id=tenant_b["tenant_id"], key=f"b1-{stamp}", name="B1"
        )
        out.update(
            tenant_a=tenant_a["tenant_id"], tenant_b=tenant_b["tenant_id"],
            space_a1=space_a1["space_id"], space_a2=space_a2["space_id"],
            space_b1=space_b1["space_id"],
            tenant_a_collection=tenant_a["member_collection"],
            space_a1_collection=space_a1["member_collection"],
        )
        for tag in ("operator", "reader", "target", "spare", "outsider", "platform_holder",
                    "space_only", "platform_removed", "audit_target", "rowcount_target"):
            out[tag] = _user(conn, tag)

        role_admin_a = _role(conn, scope="TENANT", tenant_id=out["tenant_a"], space_id=None,
                             admin=True)
        role_read_a = _role(conn, scope="TENANT", tenant_id=out["tenant_a"], space_id=None,
                            admin=False)
        role_admin_b = _role(conn, scope="TENANT", tenant_id=out["tenant_b"], space_id=None,
                             admin=True)
        role_space_admin_a1 = _role(conn, scope="SPACE", tenant_id=None,
                                    space_id=out["space_a1"], admin=True)
        role_space_admin_b1 = _role(conn, scope="SPACE", tenant_id=None,
                                    space_id=out["space_b1"], admin=True)
        out.update(role_admin_a=role_admin_a, role_read_a=role_read_a, role_admin_b=role_admin_b,
                   role_space_admin_a1=role_space_admin_a1,
                   role_space_admin_b1=role_space_admin_b1)

        memberships = (
            (out["operator"], out["tenant_a"], role_admin_a),
            (out["reader"], out["tenant_a"], role_read_a),
            (out["target"], out["tenant_a"], role_read_a),
            (out["space_only"], out["tenant_a"], role_admin_a),
            (out["outsider"], out["tenant_b"], role_admin_b),
        )
        for user, tenant, role in memberships:
            conn.execute(
                sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                    " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
                ),
                {"t": tenant, "u": user, "r": role},
            )
        conn.execute(
            sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active')"
            ),
            {"t": out["tenant_a"], "s": out["space_a1"], "u": out["operator"],
             "r": role_space_admin_a1},
        )
        # Q5 Case C: a live space membership whose tenant membership was removed.
        conn.execute(
            sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active')"
            ),
            {"t": out["tenant_a"], "s": out["space_a1"], "u": out["space_only"],
             "r": role_space_admin_a1},
        )
        conn.execute(
            sa.text(
                "UPDATE tenant_memberships SET status = 'removed'"
                " WHERE tenant_id = CAST(:t AS uuid) AND user_id = CAST(:u AS uuid)"
            ),
            {"t": out["tenant_a"], "u": out["space_only"]},
        )
        # Tenant B space role holder (Case D source).
        conn.execute(
            sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active')"
            ),
            {"t": out["tenant_b"], "s": out["space_b1"], "u": out["outsider"],
             "r": role_space_admin_b1},
        )
        # One-time platform bootstrap transition (the only path the PM gate allows
        # before 'initialized'); afterwards PM rows may be provisioned normally.
        conn.execute(
            sa.text(
                "UPDATE platform_state SET bootstrap_state = 'initialized', initialized_at = now()"
                " WHERE id = 1 AND bootstrap_state = 'uninitialized'"
            )
        )
        for holder in ("platform_holder", "platform_removed"):
            conn.execute(
                sa.text(
                    "INSERT INTO platform_memberships (user_id, role_id, status)"
                    " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
                    " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
                ),
                {"u": out[holder]},
            )
        # Agent for the Agent/User separation case (P16 governs the object).
        out["agent"] = str(conn.execute(
            sa.text(
                "INSERT INTO agents (tenant_id, space_id, owner_id, key, name, status,"
                " max_risk_level, config) VALUES (CAST(:t AS uuid), NULL, CAST(:o AS uuid),"
                " :k, 'acc agent', 'active', 'HIGH', '{}'::jsonb) RETURNING id"
            ),
            {"t": out["tenant_a"], "o": out["operator"], "k": f"p17acc_agent_{stamp}"},
        ).scalar_one())
        ensure_agent_projection(session, tenant_id=out["tenant_a"], agent_id=out["agent"])
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, permission_id, effect)"
                " SELECT CAST(:a AS uuid), p.id, 'allow' FROM permissions p"
                " WHERE p.key = 'agent.execute'"
            ),
            {"a": out["agent"]},
        )
        # The operator holds an ACL allow on the agent resource (actor side).
        conn.execute(
            sa.text(
                "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id,"
                " action, effect) SELECT CAST(:r AS uuid), ast.id, CAST(:u AS uuid), 'execute',"
                " 'allow' FROM acl_subject_types ast WHERE ast.key = 'user'"
            ),
            {"r": out["agent"], "u": out["operator"]},
        )
    return out


def _rows(engine, sql: str, **params) -> list[dict]:
    with engine.begin() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


def _count(engine, table: str) -> int:
    with engine.begin() as conn:
        return conn.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()


# ---------------------------------------------------------------- §15 Q4 / Q5
def test_q15_tenant_scoped_admin_may_manage_its_own_tenant_space(db, engine, ids) -> None:
    """Q4 note: a tenant-scoped member.admin covers the tenant's space resource."""
    membership_id = create_space_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"],
        space_id=ids["space_a1"], user_id=ids["target"],
        role_id=ids["role_space_admin_a1"], correlation_id=str(uuid.uuid4()),
    )
    assert membership_id


def test_q5_case_a_tenant_and_space_member_is_allowed(db, ids) -> None:
    rows = list_space_members(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], space_id=ids["space_a1"]
    )
    assert rows


def test_q5_case_b_tenant_member_without_space_membership_is_denied(db, engine, ids) -> None:
    before = _count(engine, "memberships")
    with pytest.raises(IdentityRuntimeError) as exc:
        create_space_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"],
            space_id=ids["space_a2"], user_id=ids["target"],
            role_id=ids["role_space_admin_a1"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code in {ErrorCode.SPACE_SCOPE_DENIED, ErrorCode.AUTHORIZATION_DENIED}
    assert _count(engine, "memberships") == before


def test_q5_case_c_space_membership_without_tenant_standing_is_denied(db, engine, ids) -> None:
    before = _count(engine, "memberships")
    with pytest.raises(IdentityRuntimeError) as exc:
        create_space_membership(
            db, actor_id=ids["space_only"], tenant_id=ids["tenant_a"],
            space_id=ids["space_a1"], user_id=ids["target"],
            role_id=ids["role_space_admin_a1"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code in {ErrorCode.MEMBERSHIP_REQUIRED, ErrorCode.AUTHORIZATION_DENIED}
    assert _count(engine, "memberships") == before


def test_q5_case_d_foreign_tenant_space_role_is_denied(db, engine, ids) -> None:
    before = _count(engine, "memberships")
    with pytest.raises(IdentityRuntimeError):
        create_space_membership(
            db, actor_id=ids["outsider"], tenant_id=ids["tenant_a"],
            space_id=ids["space_a1"], user_id=ids["target"],
            role_id=ids["role_space_admin_a1"], correlation_id=str(uuid.uuid4()),
        )
    assert _count(engine, "memberships") == before


# ------------------------------------------------------------------- §20/§21
def test_platform_authority_is_explicit_and_never_a_fallback(db, engine, ids) -> None:
    # Explicit platform authority: allowed without tenant membership.
    granted = create_tenant_membership(
        db, actor_id=ids["platform_holder"], tenant_id=ids["tenant_a"],
        user_id=ids["spare"], role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
    )
    assert granted
    delete_tenant_membership(
        db, actor_id=ids["platform_holder"], tenant_id=ids["tenant_a"],
        user_id=ids["spare"], correlation_id=str(uuid.uuid4()),
    )
    # Remove the platform membership: the same actor loses the capability (no fallback).
    with engine.begin() as conn:
        conn.execute(
            sa.text("DELETE FROM platform_memberships WHERE user_id = CAST(:u AS uuid)"),
            {"u": ids["platform_removed"]},
        )
    with pytest.raises(IdentityRuntimeError) as exc:
        create_tenant_membership(
            db, actor_id=ids["platform_removed"], tenant_id=ids["tenant_a"],
            user_id=ids["spare"], role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code in {ErrorCode.MEMBERSHIP_REQUIRED, ErrorCode.AUTHORIZATION_DENIED}


def test_system_objects_reject_runtime_writes(db, engine) -> None:
    statements = (
        "INSERT INTO role_permissions (role_id, permission_id, effect)"
        " SELECT id, id, 'allow' FROM roles LIMIT 1",
        "INSERT INTO acl_subject_types (key) VALUES ('p17acc')",
        "UPDATE platform_state SET bootstrap_state = 'bogus'",
    )
    with engine.begin() as conn:
        before = {
            table: conn.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in ("role_permissions", "acl_subject_types", "platform_state")
        }
    for statement in statements:
        with db.transaction() as session:
            with pytest.raises(sa.exc.SQLAlchemyError):
                session.execute(sa.text(statement))
    with engine.begin() as conn:
        after = {
            table: conn.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in ("role_permissions", "acl_subject_types", "platform_state")
        }
    assert before == after


# ------------------------------------------------------------- §29/§30/§31
def test_rowcount_zero_is_not_silently_accepted(db, engine, ids) -> None:
    """A valid target with no active membership is refused, never a silent 0-row success."""
    with pytest.raises(IdentityRuntimeError) as exc:
        update_tenant_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"],
            user_id=ids["rowcount_target"],
            role_id=ids["role_read_a"], correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code == ErrorCode.MEMBERSHIP_NOT_FOUND
    with pytest.raises(IdentityRuntimeError) as exc:
        delete_tenant_membership(
            db, actor_id=ids["operator"], tenant_id=ids["tenant_a"],
            user_id=ids["rowcount_target"],
            correlation_id=str(uuid.uuid4()),
        )
    assert exc.value.code == ErrorCode.MEMBERSHIP_NOT_FOUND
    assert _rows(
        engine,
        "SELECT 1 FROM tenant_memberships WHERE tenant_id = CAST(:t AS uuid)"
        " AND user_id = CAST(:u AS uuid)",
        t=ids["tenant_a"], u=ids["rowcount_target"],
    ) == []


def test_audit_content_and_correlation(db, engine, ids) -> None:
    correlation = str(uuid.uuid4())
    create_tenant_membership(
        db, actor_id=ids["operator"], tenant_id=ids["tenant_a"], user_id=ids["audit_target"],
        role_id=ids["role_admin_a"], correlation_id=correlation,
    )
    audits = _rows(
        engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
        c=correlation,
    )
    assert len(audits) == 1
    audit = audits[0]
    assert str(audit["actor_id"]) == ids["operator"]
    assert str(audit["tenant_id"]) == ids["tenant_a"]
    assert audit["action"] == "create"
    assert audit["occurred_at"] is not None
    assert str(audit["metadata"]["target_user_id"]) == ids["audit_target"]
    assert set(audit["metadata"]) <= AUDIT_METADATA_KEYS
    blob = str(audit).lower()
    for forbidden in FORBIDDEN_AUDIT_TEXT:
        assert forbidden not in blob, forbidden


# --------------------------------------------------------- §33 agent/user
def test_agent_authorization_never_substitutes_for_actor_authorization(engine, ids) -> None:
    """Case B: agent ALLOW + actor DENY → the frozen conjunction denies."""
    service = AuthorizationService(engine=engine)
    resource = ResourceRef(type="agent", id=ids["agent"], tenant_id=ids["tenant_a"])
    agent = service.authorize(
        AuthorizationRequest(
            subject=Subject(identity_id=ids["agent"], subject_type="AGENT",
                            agent_id=ids["agent"], tenant_id=ids["tenant_a"]),
            action=Action(name="execute", resource_type="agent"),
            resource=resource, tenant_id=ids["tenant_a"],
        )
    )
    # A tenant member without any grant: the actor side denies.
    actor = service.authorize(
        AuthorizationRequest(
            subject=Subject(identity_id=ids["reader"], subject_type="USER",
                            tenant_id=ids["tenant_a"], actor_id=ids["reader"]),
            action=Action(name="execute", resource_type="agent"),
            resource=resource, tenant_id=ids["tenant_a"],
        )
    )
    assert agent.allowed is True
    assert actor.allowed is False


# ------------------------------------------------------ §54/§55 provisioning
def test_provisioning_rolls_back_when_projection_fails(engine, ids) -> None:
    """A projection failure must roll the structural object back (§54/§76)."""
    before = _count(engine, "spaces")
    with pytest.raises(ProvisioningError):
        with Session(engine) as session, session.begin():
            provision_space(
                session, tenant_id=ids["tenant_a"], key="members", name="reserved key"
            )
    assert _count(engine, "spaces") == before


def test_projection_consistency_fields(engine, ids) -> None:
    rows = _rows(
        engine,
        "SELECT id, tenant_id, space_id, resource_type, natural_key FROM resources"
        " WHERE deleted_at IS NULL",
    )
    by_key = {(r["resource_type"], r["tenant_id"], r["space_id"]): r for r in rows}
    tenant_a = uuid.UUID(ids["tenant_a"])
    space_a1 = uuid.UUID(ids["space_a1"])
    assert ("tenant", tenant_a, None) in by_key
    assert (MEMBER_RESOURCE_TYPE, tenant_a, None) in by_key
    assert ("space", tenant_a, space_a1) in by_key
    assert (MEMBER_RESOURCE_TYPE, tenant_a, space_a1) in by_key
    assert by_key[("space", tenant_a, space_a1)]["natural_key"] != "members"


def test_resource_absence_denies_read_and_admin_and_creates_nothing(engine, db, ids) -> None:
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "DELETE FROM resources WHERE tenant_id = CAST(:t AS uuid)"
                " AND resource_type = :r AND space_id IS NULL"
            ),
            {"t": ids["tenant_a"], "r": MEMBER_RESOURCE_TYPE},
        )
    resources_before = _count(engine, "resources")
    try:
        with pytest.raises(IdentityRuntimeError) as exc:
            list_tenant_members(db, actor_id=ids["operator"], tenant_id=ids["tenant_a"])
        assert exc.value.code == ErrorCode.RESOURCE_NOT_PROVISIONED
        with pytest.raises(IdentityRuntimeError) as exc:
            create_tenant_membership(
                db, actor_id=ids["operator"], tenant_id=ids["tenant_a"],
                user_id=ids["spare"], role_id=ids["role_read_a"],
                correlation_id=str(uuid.uuid4()),
            )
        assert exc.value.code == ErrorCode.RESOURCE_NOT_PROVISIONED
        assert _count(engine, "resources") == resources_before  # no runtime auto-repair
    finally:
        with engine.begin() as conn:
            ensure_resource_projection(Session(bind=conn), tenant_id=ids["tenant_a"])


# ------------------------------------------------------------ §39/§57 API
def test_production_event_allowlist_is_empty_and_handlers_zero() -> None:
    allowlist = production_allowlist()
    assert allowlist.is_empty is True
    assert allowlist.specs == {}


def test_api_route_inventory_matches_the_frozen_scope() -> None:
    app = create_app(load_settings_from_env({"APP_ENV": "test"}))
    paths = sorted({route.path for route in app.routes})  # type: ignore[attr-defined]
    expected = {
        "/tenants",
        "/tenants/{tenant_id}",
        "/tenants/{tenant_id}/spaces",
        "/tenants/{tenant_id}/members",
        "/tenants/{tenant_id}/members/{user_id}",
        "/tenants/{tenant_id}/spaces/{space_id}/members",
        "/tenants/{tenant_id}/spaces/{space_id}/members/{user_id}",
    }
    assert expected <= set(paths)
    for forbidden in (
        "/platform-memberships", "/roles", "/permissions", "/resource-permissions",
        "/spaces", "/memberships",
    ):
        assert forbidden not in paths, forbidden


def test_api_membership_write_records_audit_with_the_request_correlation(engine, ids) -> None:
    """§25/§26/§27/§31: real HTTP path → DB mutation + audit under the caller correlation."""
    settings = load_settings_from_env(
        {
            "APP_ENV": "test",
            "DATABASE_URL": RUNTIME_DSN,
            "LOG_FORMAT": "console",
            "AI_DEFAULT_PROVIDER": "none",
            "AI_DEFAULT_MODEL": "none",
        }
    )
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime"
    )
    database.start()
    try:
        with TestClient(create_app(settings)) as client:
            email = f"p17acc-api-{uuid.uuid4().hex[:8]}@example.invalid"
            created = client.post(
                "/identity/onboarding", json={"email": email, "password": PASSWORD}
            )
            assert created.status_code == 201, created.text
            actor_id = created.json()["user_id"]
            target_email = f"p17acc-api-target-{uuid.uuid4().hex[:8]}@example.invalid"
            target_created = client.post(
                "/identity/onboarding", json={"email": target_email, "password": PASSWORD}
            )
            assert target_created.status_code == 201, target_created.text
            api_target = target_created.json()["user_id"]
            # Provision standing for the freshly onboarded actor (control-plane style,
            # fixture identity): tenant membership + a space membership.
            with engine.begin() as conn:
                conn.execute(
                    sa.text(
                        "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                        " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
                    ),
                    {"t": ids["tenant_a"], "u": actor_id, "r": ids["role_admin_a"]},
                )
            device_id = enroll_device(database, email=email, password=PASSWORD)
            issued = login(database, login_id=email, password=PASSWORD, device_id=device_id)
            assert issued.session is not None
            correlation = str(uuid.uuid4())
            response = client.post(
                f"/tenants/{ids['tenant_a']}/members",
                json={"user_id": api_target, "role_id": ids["role_read_a"]},
                headers={
                    "Authorization": f"Bearer {issued.session.token}",
                    "x-correlation-id": correlation,
                },
            )
            assert response.status_code == 201, response.text
            created_rows = _rows(
                engine,
                "SELECT status FROM tenant_memberships WHERE tenant_id = CAST(:t AS uuid)"
                " AND user_id = CAST(:u AS uuid)",
                t=ids["tenant_a"], u=api_target,
            )
            assert created_rows == [{"status": "active"}]  # exactly one mutation
            audits = _rows(
                engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
                c=correlation,
            )
            assert len(audits) == 1
            assert str(audits[0]["actor_id"]) == actor_id
            assert audits[0]["action"] == "create"
            assert set(audits[0]["metadata"]) <= AUDIT_METADATA_KEYS

            # UPDATE then DELETE through the same real path, each with its own correlation.
            update_correlation = str(uuid.uuid4())
            patched = client.patch(
                f"/tenants/{ids['tenant_a']}/members/{api_target}",
                json={"role_id": ids["role_admin_a"]},
                headers={
                    "Authorization": f"Bearer {issued.session.token}",
                    "x-correlation-id": update_correlation,
                },
            )
            assert patched.status_code == 200, patched.text
            update_audit = _rows(
                engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
                c=update_correlation,
            )
            assert len(update_audit) == 1 and update_audit[0]["action"] == "update"
            assert str(update_audit[0]["metadata"]["role_before"]) == ids["role_read_a"]

            delete_correlation = str(uuid.uuid4())
            removed = client.delete(
                f"/tenants/{ids['tenant_a']}/members/{api_target}",
                headers={
                    "Authorization": f"Bearer {issued.session.token}",
                    "x-correlation-id": delete_correlation,
                },
            )
            assert removed.status_code == 204, removed.text
            delete_audit = _rows(
                engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
                c=delete_correlation,
            )
            assert len(delete_audit) == 1 and delete_audit[0]["action"] == "delete"
            assert delete_audit[0]["metadata"]["role_before"]  # audit survives the removal
            assert _rows(
                engine,
                "SELECT status FROM tenant_memberships WHERE tenant_id = CAST(:t AS uuid)"
                " AND user_id = CAST(:u AS uuid)",
                t=ids["tenant_a"], u=api_target,
            ) == [{"status": "removed"}]
    finally:
        database.dispose()

