"""P18 WAVE 1–2 + D14 — control-plane provisioning and runtime lifecycle gates.

Every business assertion runs as ``uap_control`` (the provisioned control-plane
principal), on a dedicated database whose privileges come from the versioned
sources only: ``scripts.privileges`` (runtime/app baseline) and
``scripts.role_provisioning`` (CONTROL_PLANE baseline). No private GRANT, no
superuser in the business path, no uap_migrator.
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
from services.control_plane.errors import ControlPlaneError, ErrorCode
from services.identity_runtime import ErrorCode as IdentityCode
from services.identity_runtime import IdentityRuntimeError
from services.use_cases import (
    list_tenant_members,
    provision_space,
    provision_tenant,
    transition_space,
    transition_tenant,
)

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P18_DB = "uap_p18_control_test"
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
    report = provision_control_plane(fixtures)  # versioned CONTROL_PLANE baseline
    assert report.ok, (report.missing, report.unexpected, report.forbidden, report.attribute_drift)
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
        for key in ("platform", "admin", "other"):
            ids[key] = str(conn.execute(
                sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                {"e": f"p18cp-{key}-{uuid.uuid4().hex[:8]}@example.invalid"},
            ).scalar_one())
        conn.execute(
            sa.text(
                "UPDATE platform_state SET bootstrap_state = 'initialized', initialized_at = now()"
                " WHERE id = 1 AND bootstrap_state = 'uninitialized'"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO platform_memberships (user_id, role_id, status)"
                " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
                " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
            ),
            {"u": ids["platform"]},
        )
    return ids


def _rows(engine, sql: str, **params) -> list[dict]:
    with engine.begin() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


def test_tenant_provisioning_is_atomic_and_complete(db, engine, actors) -> None:
    correlation = str(uuid.uuid4())
    result = provision_tenant(
        db, actor_id=actors["platform"], slug=f"p18-tenant-{uuid.uuid4().hex[:8]}",
        display_name="P18 Tenant", initial_admin_user_id=actors["admin"],
        correlation_id=correlation,
    )
    assert result.status == "active" and result.replayed is False

    tenant = _rows(engine, "SELECT * FROM tenants WHERE id = CAST(:t AS uuid)", t=result.tenant_id)[0]
    assert tenant["status"] == "active"

    role = _rows(engine, "SELECT * FROM roles WHERE id = CAST(:r AS uuid)",
                 r=result.admin_role_id)[0]
    assert role["scope"] == "TENANT" and str(role["tenant_id"]) == result.tenant_id
    assert role["space_id"] is None and role["is_system"] is False
    keys = {row["key"] for row in _rows(
        engine,
        "SELECT p.key FROM role_permissions rp JOIN permissions p ON p.id = rp.permission_id"
        " WHERE rp.role_id = CAST(:r AS uuid)",
        r=result.admin_role_id,
    )}
    assert keys == {"member.read", "member.admin", "tenant.admin"}

    resources = _rows(
        engine,
        "SELECT resource_type, space_id FROM resources WHERE tenant_id = CAST(:t AS uuid)",
        t=result.tenant_id,
    )
    assert {(r["resource_type"], r["space_id"]) for r in resources} >= {
        ("tenant", None), ("member", None)
    }

    membership = _rows(
        engine,
        "SELECT status FROM tenant_memberships WHERE id = CAST(:m AS uuid)",
        m=result.membership_id,
    )[0]
    assert membership["status"] == "active"

    audits = _rows(
        engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)", c=correlation
    )
    assert len(audits) == 1 and audits[0]["action"] == "tenant.provision"
    assert str(audits[0]["actor_id"]) == actors["platform"]
    assert str(audits[0]["actor_id"]) != str(audits[0]["metadata"].get("principal", ""))


def test_tenant_provisioning_replay_and_conflict(db, actors) -> None:
    slug = f"p18-replay-{uuid.uuid4().hex[:8]}"
    first = provision_tenant(
        db, actor_id=actors["platform"], slug=slug, display_name="Replay Tenant",
        initial_admin_user_id=actors["admin"],
    )
    replay = provision_tenant(
        db, actor_id=actors["platform"], slug=slug, display_name="Replay Tenant",
        initial_admin_user_id=actors["admin"],
    )
    assert replay.replayed is True and replay.tenant_id == first.tenant_id
    with pytest.raises(ControlPlaneError) as exc:
        provision_tenant(
            db, actor_id=actors["platform"], slug=slug, display_name="Different Name",
            initial_admin_user_id=actors["admin"],
        )
    assert exc.value.code == ErrorCode.TENANT_CONFLICT


def test_space_provisioning_requires_tenant_membership(db, engine, actors) -> None:
    tenant = provision_tenant(
        db, actor_id=actors["platform"], slug=f"p18-space-{uuid.uuid4().hex[:8]}",
        display_name="Space Tenant", initial_admin_user_id=actors["admin"],
    )
    with pytest.raises(ControlPlaneError) as exc:
        provision_space(
            db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
            key=f"k-{uuid.uuid4().hex[:6]}", name="Space",
            initial_space_admin_user_id=actors["other"],
        )
    assert exc.value.code == ErrorCode.INITIAL_ADMIN_INVALID


def test_space_provisioning_is_complete(db, engine, actors) -> None:
    tenant = provision_tenant(
        db, actor_id=actors["platform"], slug=f"p18-sp2-{uuid.uuid4().hex[:8]}",
        display_name="Space Tenant 2", initial_admin_user_id=actors["admin"],
    )
    result = provision_space(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
        key=f"k-{uuid.uuid4().hex[:6]}", name="Main Space",
        initial_space_admin_user_id=actors["admin"],
    )
    assert result.status == "active"
    role = _rows(engine, "SELECT * FROM roles WHERE id = CAST(:r AS uuid)",
                 r=result.admin_role_id)[0]
    assert role["scope"] == "SPACE" and role["tenant_id"] is None
    assert str(role["space_id"]) == result.space_id and role["is_system"] is False
    resources = _rows(
        engine,
        "SELECT resource_type FROM resources WHERE space_id = CAST(:s AS uuid)",
        s=result.space_id,
    )
    assert {r["resource_type"] for r in resources} >= {"space", "member"}


def test_non_platform_actor_cannot_provision(db, engine, actors) -> None:
    before = len(_rows(engine, "SELECT id FROM tenants"))
    with pytest.raises(ControlPlaneError) as exc:
        provision_tenant(
            db, actor_id=actors["admin"], slug=f"p18-denied-{uuid.uuid4().hex[:8]}",
            display_name="Denied", initial_admin_user_id=actors["admin"],
        )
    assert exc.value.code == ErrorCode.AUTHORIZATION_DENIED
    assert len(_rows(engine, "SELECT id FROM tenants")) == before


def test_lifecycle_transitions_and_runtime_gate(db, runtime_db, engine, actors) -> None:
    tenant = provision_tenant(
        db, actor_id=actors["platform"], slug=f"p18-life-{uuid.uuid4().hex[:8]}",
        display_name="Lifecycle Tenant", initial_admin_user_id=actors["admin"],
    )
    # invalid transition first
    with pytest.raises(ControlPlaneError) as exc:
        transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                          target_state="deleted")
    assert exc.value.code == ErrorCode.LIFECYCLE_CONFLICT
    # active -> suspended -> runtime denied -> active -> runtime allowed
    assert transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                             target_state="suspended") == "suspended"
    with pytest.raises(IdentityRuntimeError) as exc:
        list_tenant_members(runtime_db, actor_id=actors["admin"], tenant_id=tenant.tenant_id)
    assert exc.value.code == IdentityCode.TENANT_NOT_ACTIVE
    assert transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                             target_state="active") == "active"
    assert list_tenant_members(runtime_db, actor_id=actors["admin"], tenant_id=tenant.tenant_id)
    # archived -> deleted is terminal
    assert transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                             target_state="archived") == "archived"
    assert transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                             target_state="deleted") == "deleted"
    with pytest.raises(ControlPlaneError):
        transition_tenant(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                          target_state="active")
    assert _rows(engine, "SELECT id FROM tenants WHERE id = CAST(:t AS uuid)",
                 t=tenant.tenant_id)  # row retained (soft lifecycle)


def test_space_lifecycle_gate(db, runtime_db, actors) -> None:
    tenant = provision_tenant(
        db, actor_id=actors["platform"], slug=f"p18-slife-{uuid.uuid4().hex[:8]}",
        display_name="Space Lifecycle", initial_admin_user_id=actors["admin"],
    )
    space = provision_space(
        db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
        key=f"k-{uuid.uuid4().hex[:6]}", name="Gate Space",
        initial_space_admin_user_id=actors["admin"],
    )
    assert transition_space(db, actor_id=actors["platform"], tenant_id=tenant.tenant_id,
                            space_id=space.space_id, target_state="archived") == "archived"
    with pytest.raises(IdentityRuntimeError) as exc:
        list_tenant_members  # noqa: B018 - keep the import used
        from services.use_cases import list_space_members

        list_space_members(
            runtime_db, actor_id=actors["admin"], tenant_id=tenant.tenant_id,
            space_id=space.space_id,
        )
    assert exc.value.code == IdentityCode.SPACE_NOT_ACTIVE


def test_audit_atomicity_rolls_back_provisioning(db, engine, actors) -> None:
    slug = f"p18-atomic-{uuid.uuid4().hex[:8]}"
    with pytest.raises(Exception):
        provision_tenant(
            db, actor_id=actors["platform"], slug=slug, display_name="Atomic",
            initial_admin_user_id=actors["admin"], correlation_id="not-a-uuid",
        )
    assert _rows(engine, "SELECT id FROM tenants WHERE lower(slug) = lower(:s)", s=slug) == []


def test_audit_logs_are_append_only_for_the_control_plane(db, engine, actors) -> None:
    with db.transaction() as session:
        with pytest.raises(sa.exc.SQLAlchemyError):
            session.execute(sa.text("UPDATE audit_logs SET result = 'denied'"))
    with db.transaction() as session:
        with pytest.raises(sa.exc.SQLAlchemyError):
            session.execute(sa.text("DELETE FROM audit_logs"))
