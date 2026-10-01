"""P17 WAVE 6 — agent scope resolution (P16 semantics untouched).

P16 froze ``Agent ≠ User``, ``agents.tenant_id`` / ``agents.space_id`` binding and
"actor authorization AND agent authorization". This suite verifies that P17 can
express the *same* facts through the shared context resolver, and that an owner's
permission never becomes the agent's permission.

The P16 runtime itself is not modified by this round; the six P16 integration
scenarios are re-run unchanged in the same round (see the evidence document).
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from core.permission import Action, AuthorizationRequest, Subject
from core.resource import ResourceRef
from scripts.privileges import materialize as materialize_baseline_privileges
from services.authorization import AuthorizationService
from services.control_plane import ensure_agent_projection, provision_space, provision_tenant
from services.identity_runtime import (
    ErrorCode,
    IdentityRuntimeError,
    resolve_agent_execution_context,
)

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P17_DB = "uap_p17_agent_test"
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
    materialize_baseline_privileges(fixtures)
    yield fixtures
    fixtures.dispose()
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P17_DB}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def runtime():
    engine = sa.create_engine(RUNTIME_DSN)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def ids(engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        session = Session(bind=conn)
        tenant_a = provision_tenant(session, slug=f"p17ag-a-{uuid.uuid4().hex[:8]}", display_name="A")
        tenant_b = provision_tenant(session, slug=f"p17ag-b-{uuid.uuid4().hex[:8]}", display_name="B")
        space_a1 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a1-{uuid.uuid4().hex[:6]}", name="A1"
        )
        space_b1 = provision_space(
            session, tenant_id=tenant_b["tenant_id"], key=f"b1-{uuid.uuid4().hex[:6]}", name="B1"
        )
        ids.update(tenant_a=tenant_a["tenant_id"], tenant_b=tenant_b["tenant_id"],
                   space_a1=space_a1["space_id"], space_b1=space_b1["space_id"])
        for key in ("owner", "actor", "foreign"):
            ids[key] = str(conn.execute(
                sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                {"e": f"p17ag-{key}-{uuid.uuid4().hex[:8]}@example.invalid"},
            ).scalar_one())
        role = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (:t, NULL, :k, 'Agent tenant role', 'TENANT', 'active') RETURNING id"
            ),
            {"t": ids["tenant_a"], "k": f"p17ag_role_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        ids["role"] = role
        for user in (ids["owner"], ids["actor"]):
            conn.execute(
                sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status)"
                    " VALUES (CAST(:t AS uuid), CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
                ),
                {"t": ids["tenant_a"], "u": user, "r": role},
            )
        # The actor is also a member of space A1; the owner is not.
        space_role = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (NULL, :s, :k, 'Agent space role', 'SPACE', 'active') RETURNING id"
            ),
            {"s": ids["space_a1"], "k": f"p17ag_srole_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        ids["space_role"] = space_role
        conn.execute(
            sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
                " CAST(:r AS uuid), 'active')"
            ),
            {"t": ids["tenant_a"], "s": ids["space_a1"], "u": ids["actor"], "r": space_role},
        )
        for key, tenant, space, status in (
            ("agent_tenant", ids["tenant_a"], None, "active"),
            ("agent_space", ids["tenant_a"], ids["space_a1"], "active"),
            ("agent_off", ids["tenant_a"], None, "disabled"),
            ("agent_foreign", ids["tenant_b"], None, "active"),
        ):
            ids[key] = str(conn.execute(
                sa.text(
                    "INSERT INTO agents (tenant_id, space_id, owner_id, key, name, status,"
                    " max_risk_level, config) VALUES (CAST(:t AS uuid), CAST(:s AS uuid),"
                    " CAST(:o AS uuid), :k, :k, :status, 'LOW', '{}'::jsonb) RETURNING id"
                ),
                {"t": tenant, "s": space, "o": ids["owner"], "k": f"p17ag_{key}_{uuid.uuid4().hex[:6]}",
                 "status": status},
            ).scalar_one())
            ensure_agent_projection(session, tenant_id=tenant, agent_id=ids[key])
        # The owner holds an explicit ACL allow on their agent resource.
        conn.execute(
            sa.text(
                "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id,"
                " action, effect) SELECT CAST(:r AS uuid), ast.id, CAST(:u AS uuid), 'execute',"
                " 'allow' FROM acl_subject_types ast WHERE ast.key = 'user'"
            ),
            {"r": ids["agent_tenant"], "u": ids["owner"]},
        )
    return ids


def _session(runtime):
    return Session(runtime)


def test_tenant_scoped_agent_resolves_for_a_tenant_member(runtime, ids) -> None:
    with _session(runtime) as session:
        context, binding = resolve_agent_execution_context(
            session, actor_id=ids["actor"], agent_id=ids["agent_tenant"],
            tenant_id=ids["tenant_a"],
        )
    assert binding.tenant_id == ids["tenant_a"]
    assert binding.space_id is None
    assert context.tenant_id == binding.tenant_id


def test_space_scoped_agent_requires_the_same_space(runtime, ids) -> None:
    with _session(runtime) as session:
        _, binding = resolve_agent_execution_context(
            session, actor_id=ids["actor"], agent_id=ids["agent_space"],
            tenant_id=ids["tenant_a"], space_id=ids["space_a1"],
        )
    assert binding.space_id == ids["space_a1"]


def test_space_scoped_agent_without_the_space_context_is_denied(runtime, ids) -> None:
    with _session(runtime) as session, pytest.raises(IdentityRuntimeError) as exc:
        resolve_agent_execution_context(
            session, actor_id=ids["actor"], agent_id=ids["agent_space"],
            tenant_id=ids["tenant_a"],
        )
    assert exc.value.code == ErrorCode.AGENT_SPACE_SCOPE_DENIED


def test_agent_of_another_tenant_is_denied(runtime, ids) -> None:
    """The lookup is tenant-scoped, so a foreign agent is simply not found."""
    with _session(runtime) as session, pytest.raises(IdentityRuntimeError) as exc:
        resolve_agent_execution_context(
            session, actor_id=ids["actor"], agent_id=ids["agent_foreign"],
            tenant_id=ids["tenant_a"],
        )
    assert exc.value.code == ErrorCode.AGENT_SCOPE_DENIED


def test_disabled_agent_is_denied(runtime, ids) -> None:
    with _session(runtime) as session, pytest.raises(IdentityRuntimeError) as exc:
        resolve_agent_execution_context(
            session, actor_id=ids["actor"], agent_id=ids["agent_off"],
            tenant_id=ids["tenant_a"],
        )
    assert exc.value.code == ErrorCode.AGENT_SCOPE_DENIED


def test_actor_outside_the_tenant_cannot_use_the_agent(runtime, ids) -> None:
    with _session(runtime) as session, pytest.raises(IdentityRuntimeError) as exc:
        resolve_agent_execution_context(
            session, actor_id=ids["foreign"], agent_id=ids["agent_tenant"],
            tenant_id=ids["tenant_a"],
        )
    assert exc.value.code == ErrorCode.MEMBERSHIP_REQUIRED


def test_owner_permission_is_not_inherited_by_the_agent(runtime, ids) -> None:
    """N5: the owner's ACL allow does not authorize the agent."""
    service = AuthorizationService(engine=runtime)
    owner = service.authorize(
        AuthorizationRequest(
            subject=Subject(identity_id=ids["owner"], subject_type="USER",
                            tenant_id=ids["tenant_a"], actor_id=ids["owner"]),
            action=Action(name="execute", resource_type="agent"),
            resource=ResourceRef(type="agent", id=ids["agent_tenant"], tenant_id=ids["tenant_a"]),
            tenant_id=ids["tenant_a"],
        )
    )
    agent = service.authorize(
        AuthorizationRequest(
            subject=Subject(identity_id=ids["owner"], subject_type="AGENT",
                            agent_id=ids["agent_tenant"], actor_id=ids["owner"],
                            tenant_id=ids["tenant_a"]),
            action=Action(name="execute", resource_type="agent"),
            resource=ResourceRef(type="agent", id=ids["agent_tenant"], tenant_id=ids["tenant_a"]),
            tenant_id=ids["tenant_a"],
        )
    )
    assert owner.allowed is True
    assert agent.allowed is False
    assert "inheritance" not in str(agent.reason)
