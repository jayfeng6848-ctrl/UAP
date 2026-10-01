"""P18 WAVE 3 close (metadata/visibility) + D14 agent gate — real DB, uap_control.

The control-plane writes run as the provisioned ``uap_control`` principal; the
runtime lifecycle gate is exercised against the same objects. Privilege state
comes from the versioned sources (``scripts.privileges`` + ``scripts.role_provisioning``).
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
from scripts.role_provisioning import provision as provision_control_plane
from services.control_plane import ensure_agent_projection
from services.control_plane.errors import ControlPlaneError, ErrorCode
from services.identity_runtime import ErrorCode as IdentityCode
from services.identity_runtime import IdentityRuntimeError, require_active_agent_scope
from services.use_cases import (
    provision_space,
    provision_tenant,
    transition_space,
    transition_tenant,
    update_space_metadata,
    update_tenant_metadata,
)

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P18_DB = "uap_p18_meta_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P18_DB}"
CONTROL_DSN = f"postgresql+psycopg://uap_control:trust@localhost:5432/{P18_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P18_DB}"


@pytest.fixture(scope="module")
def engine():
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P18_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{P18_DB}" OWNER uap_migrator'))
    admin.dispose()
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{P18_DB}"
    cfg.attributes["lock_mode"] = "wait"
    command.upgrade(cfg, "head")
    fixtures = sa.create_engine(FIXTURE_DSN)
    materialize_baseline_privileges(fixtures)
    assert provision_control_plane(fixtures).ok
    yield fixtures
    fixtures.dispose()
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P18_DB}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def db(engine):
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=CONTROL_DSN), require_role="uap_control"
    )
    database.start()
    yield database
    database.dispose()


@pytest.fixture(scope="module")
def runtime_db(engine):
    """The runtime principal: the agent lifecycle gate is a runtime capability."""
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime"
    )
    database.start()
    yield database
    database.dispose()


@pytest.fixture(scope="module")
def actors(engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        for key in ("platform", "admin"):
            ids[key] = str(conn.execute(
                sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                {"e": f"p18meta-{key}-{uuid.uuid4().hex[:8]}@example.invalid"},
            ).scalar_one())
        conn.execute(sa.text(
            "UPDATE platform_state SET bootstrap_state = 'initialized', initialized_at = now()"
            " WHERE id = 1 AND bootstrap_state = 'uninitialized'"
        ))
        conn.execute(sa.text(
            "INSERT INTO platform_memberships (user_id, role_id, status)"
            " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
            " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
        ), {"u": ids["platform"]})
    return ids


def _rows(engine, sql: str, **params) -> list[dict]:
    with engine.begin() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


def _tenant(db, actors, *, slug: str | None = None):
    return provision_tenant(
        db, actor_id=actors["platform"], slug=slug or f"p18meta-{uuid.uuid4().hex[:8]}",
        display_name="Meta Tenant", initial_admin_user_id=actors["admin"],
    )


def test_tenant_metadata_update_is_audited(db, engine, actors) -> None:
    tenant = _tenant(db, actors)
    correlation = str(uuid.uuid4())
    update_tenant_metadata(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
        display_name="Renamed Tenant", plan="pro", correlation_id=correlation,
    )
    row = _rows(engine, "SELECT display_name, plan, status FROM tenants WHERE id = CAST(:t AS uuid)",
                t=tenant.tenant_id)[0]
    assert row["display_name"] == "Renamed Tenant" and row["plan"] == "pro"
    assert row["status"] == "active"  # metadata never changes lifecycle
    audits = _rows(engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
                   c=correlation)
    assert len(audits) == 1 and audits[0]["action"] == "tenant.metadata.update"
    assert audits[0]["metadata"]["fields"] == ["display_name", "plan"]


def test_tenant_metadata_rejects_empty_payload(db, actors) -> None:
    tenant = _tenant(db, actors)
    with pytest.raises(ControlPlaneError) as exc:
        update_tenant_metadata(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id)
    assert exc.value.code == ErrorCode.INVALID_INPUT


def test_space_visibility_update_is_audited_and_grants_nothing(db, engine, actors) -> None:
    tenant = _tenant(db, actors)
    space = provision_space(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
        key=f"k-{uuid.uuid4().hex[:6]}", name="Vis Space",
        initial_space_admin_user_id=actors["admin"],
    )
    correlation = str(uuid.uuid4())
    update_space_metadata(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id, space_id=space.space_id,
        visibility="link", correlation_id=correlation,
    )
    row = _rows(engine, "SELECT visibility, status FROM spaces WHERE id = CAST(:s AS uuid)",
                s=space.space_id)[0]
    assert row["visibility"] == "link" and row["status"] == "active"
    audits = _rows(engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
                   c=correlation)
    assert audits and audits[0]["action"] == "space.metadata.update"
    # visibility is metadata only: no membership / role / ACL row was created
    assert _rows(engine, "SELECT id FROM memberships WHERE space_id = CAST(:s AS uuid)"
                         " AND user_id = CAST(:u AS uuid)",
                 s=space.space_id, u=actors["admin"])
    before = len(_rows(engine, "SELECT id FROM resource_permissions"))
    assert before == len(_rows(engine, "SELECT id FROM resource_permissions"))


def test_space_visibility_value_is_validated(db, actors) -> None:
    tenant = _tenant(db, actors)
    space = provision_space(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
        key=f"k-{uuid.uuid4().hex[:6]}", name="Vis Space 2",
        initial_space_admin_user_id=actors["admin"],
    )
    with pytest.raises(ControlPlaneError) as exc:
        update_space_metadata(
            db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
            space_id=space.space_id, visibility="public",
        )
    assert exc.value.code == ErrorCode.INVALID_INPUT


def test_d14_agent_gate_follows_tenant_and_space_lifecycle(
    db, runtime_db, engine, actors
) -> None:
    tenant = _tenant(db, actors)
    space = provision_space(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
        key=f"k-{uuid.uuid4().hex[:6]}", name="Agent Space",
        initial_space_admin_user_id=actors["admin"],
    )
    agent_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO agents (id, tenant_id, space_id, owner_id, key, name, status,"
            " max_risk_level, config) VALUES (CAST(:a AS uuid), CAST(:t AS uuid),"
            " CAST(:s AS uuid), CAST(:o AS uuid), :k, 'Gate Agent', 'active', 'LOW', '{}'::jsonb)"
        ), {"a": agent_id, "t": tenant.tenant_id, "s": space.space_id, "o": actors["admin"],
            "k": f"p18meta_{uuid.uuid4().hex[:8]}"})
        ensure_agent_projection(Session(bind=conn), tenant_id=tenant.tenant_id, agent_id=agent_id)

    # active tenant + active space -> gate passes (P16 semantics untouched)
    with runtime_db.transaction() as session:
        binding = require_active_agent_scope(
            session, agent_id=agent_id, tenant_id=tenant.tenant_id, space_id=space.space_id
        )
    assert binding.space_id == space.space_id

    transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                      target_state="suspended")
    with runtime_db.transaction() as session, pytest.raises(IdentityRuntimeError) as exc:
        require_active_agent_scope(
            session, agent_id=agent_id, tenant_id=tenant.tenant_id, space_id=space.space_id
        )
    assert exc.value.code == IdentityCode.TENANT_NOT_ACTIVE

    transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                      target_state="active")
    transition_space(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                     space_id=space.space_id, target_state="archived")
    with runtime_db.transaction() as session, pytest.raises(IdentityRuntimeError) as exc:
        require_active_agent_scope(
            session, agent_id=agent_id, tenant_id=tenant.tenant_id, space_id=space.space_id
        )
    assert exc.value.code == IdentityCode.SPACE_NOT_ACTIVE
