"""P17 WAVE 5 — API security matrix over real HTTP paths.

Positive and negative cases run through ``TestClient`` against a dedicated
database as ``uap_runtime``: the session is a real device-bound session, the
tenant/space come from the path, and every denial is a real canonical
authorization decision (never a handler-side role check).
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
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from scripts.privileges import materialize as materialize_baseline_privileges
from services.control_plane import provision_space, provision_tenant
from services.use_cases import login
from tests.integration.wave2_testkit import enroll_device

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P17_DB = "uap_p17_api_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P17_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P17_DB}"
PASSWORD = "P17-Api-Passw0rd!"


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


def _role(conn, *, scope: str, tenant_id: str | None, space_id: str | None, admin: bool) -> str:
    role_id = str(
        conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, is_system, status)"
                " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), :k, 'P17 api role', :scope,"
                " false, 'active') RETURNING id"
            ),
            {"t": tenant_id, "s": space_id, "k": f"p17_{uuid.uuid4().hex[:10]}", "scope": scope},
        ).scalar_one()
    )
    keys = ("member.read", "member.admin") if admin else ("member.read",)
    for key in keys:
        conn.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id, effect)"
                " SELECT CAST(:r AS uuid), p.id, 'allow' FROM permissions p WHERE p.key = :key"
            ),
            {"r": role_id, "key": key},
        )
    return role_id


@pytest.fixture(scope="module")
def stack(engine):
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
            yield SimpleNamespace(client=client, db=database, ids=_seed(engine, client, database))
    finally:
        database.dispose()


def _onboard_and_login(client, db, email: str) -> tuple[str, str]:
    response = client.post("/identity/onboarding", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201, response.text
    user_id = response.json()["user_id"]
    device_id = enroll_device(db, email=email, password=PASSWORD)
    issued = login(db, login_id=email, password=PASSWORD, device_id=device_id)
    assert issued.session is not None
    return user_id, issued.session.token


def _seed(engine, client, database) -> dict[str, object]:
    stamp = uuid.uuid4().hex[:8]
    operator_id, operator_token = _onboard_and_login(client, database, f"p17api-op-{stamp}@example.invalid")
    platform_id, platform_token = _onboard_and_login(
        client, database, f"p17api-plat-{stamp}@example.invalid"
    )
    target_id, _ = _onboard_and_login(client, database, f"p17api-target-{stamp}@example.invalid")
    outsider_id, outsider_token = _onboard_and_login(
        client, database, f"p17api-out-{stamp}@example.invalid"
    )
    spare_id, _ = _onboard_and_login(client, database, f"p17api-spare-{stamp}@example.invalid")

    ids: dict[str, object] = {
        "operator": operator_id, "operator_token": operator_token,
        "platform": platform_id, "platform_token": platform_token,
        "target": target_id,
        "spare": spare_id,
        "outsider": outsider_id, "outsider_token": outsider_token,
    }
    with engine.begin() as conn:
        session = Session(bind=conn)
        tenant_a = provision_tenant(session, slug=f"p17api-a-{stamp}", display_name="P17 API A")
        tenant_b = provision_tenant(session, slug=f"p17api-b-{stamp}", display_name="P17 API B")
        space_a1 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a1-{stamp}", name="A1"
        )
        space_a2 = provision_space(
            session, tenant_id=tenant_a["tenant_id"], key=f"a2-{stamp}", name="A2"
        )
        ids.update(
            tenant_a=tenant_a["tenant_id"], tenant_b=tenant_b["tenant_id"],
            space_a1=space_a1["space_id"], space_a2=space_a2["space_id"],
        )
        role_admin_a = _role(conn, scope="TENANT", tenant_id=tenant_a["tenant_id"],
                             space_id=None, admin=True)
        role_read_a = _role(conn, scope="TENANT", tenant_id=tenant_a["tenant_id"],
                            space_id=None, admin=False)
        role_space_a1 = _role(conn, scope="SPACE", tenant_id=None,
                              space_id=space_a1["space_id"], admin=True)
        role_admin_b = _role(conn, scope="TENANT", tenant_id=tenant_b["tenant_id"],
                             space_id=None, admin=True)
        ids.update(role_admin_a=role_admin_a, role_read_a=role_read_a,
                   role_space_a1=role_space_a1, role_admin_b=role_admin_b)
        for user, tenant, role in (
            (operator_id, tenant_a["tenant_id"], role_admin_a),
            (target_id, tenant_a["tenant_id"], role_read_a),
            (outsider_id, tenant_b["tenant_id"], role_admin_b),
        ):
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
            {"t": tenant_a["tenant_id"], "s": space_a1["space_id"], "u": operator_id,
             "r": role_space_a1},
        )
        conn.execute(
            sa.text(
                "INSERT INTO platform_memberships (user_id, role_id, status)"
                " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
                " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
            ),
            {"u": platform_id},
        )
    return ids


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------- positives
def test_positive_membership_lifecycle_over_http(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["operator_token"]))
    assert client.get("/tenants", headers=headers).status_code == 200
    assert client.get(f"/tenants/{ids['tenant_a']}", headers=headers).status_code == 200
    assert client.get(f"/tenants/{ids['tenant_a']}/spaces", headers=headers).status_code == 200
    assert client.get(f"/tenants/{ids['tenant_a']}/members", headers=headers).status_code == 200

    created = client.post(
        f"/tenants/{ids['tenant_a']}/members",
        json={"user_id": ids["outsider"], "role_id": ids["role_read_a"]},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    patched = client.patch(
        f"/tenants/{ids['tenant_a']}/members/{ids['outsider']}",
        json={"role_id": ids["role_admin_a"]},
        headers=headers,
    )
    assert patched.status_code == 200, patched.text
    removed = client.delete(
        f"/tenants/{ids['tenant_a']}/members/{ids['outsider']}", headers=headers
    )
    assert removed.status_code == 204, removed.text


def test_positive_space_membership_lifecycle_over_http(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["operator_token"]))
    base = f"/tenants/{ids['tenant_a']}/spaces/{ids['space_a1']}/members"
    assert client.get(base, headers=headers).status_code == 200
    created = client.post(
        base, json={"user_id": ids["target"], "role_id": ids["role_space_a1"]}, headers=headers
    )
    assert created.status_code == 201, created.text
    assert client.patch(
        f"{base}/{ids['target']}", json={"role_id": ids["role_space_a1"]}, headers=headers
    ).status_code == 200
    assert client.delete(f"{base}/{ids['target']}", headers=headers).status_code == 204


def test_positive_platform_admin_is_explicit_authority(stack) -> None:
    """PASS-5 over HTTP: platform authority acts without tenant membership."""
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["platform_token"]))
    response = client.post(
        f"/tenants/{ids['tenant_a']}/members",
        json={"user_id": ids["spare"], "role_id": ids["role_admin_a"]},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert client.delete(
        f"/tenants/{ids['tenant_a']}/members/{ids['spare']}", headers=headers
    ).status_code == 204


# ----------------------------------------------------------------- negatives
def test_missing_authentication_is_401(stack) -> None:
    assert stack.client.get("/tenants").status_code == 401
    assert stack.client.get(f"/tenants/{stack.ids['tenant_a']}/members").status_code == 401


def test_cross_tenant_and_forged_paths_are_denied(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["outsider_token"]))
    assert client.get(f"/tenants/{ids['tenant_a']}", headers=headers).status_code == 403
    assert client.get(f"/tenants/{ids['tenant_a']}/members", headers=headers).status_code == 403
    assert client.post(
        f"/tenants/{ids['tenant_a']}/members",
        json={"user_id": ids["outsider"], "role_id": ids["role_admin_a"]},
        headers=headers,
    ).status_code == 403


def test_missing_space_membership_and_forged_space_are_denied(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["operator_token"]))
    assert client.get(
        f"/tenants/{ids['tenant_a']}/spaces/{ids['space_a2']}/members", headers=headers
    ).status_code == 403
    assert client.post(
        f"/tenants/{ids['tenant_a']}/spaces/{ids['space_a2']}/members",
        json={"user_id": ids["target"], "role_id": ids["role_space_a1"]},
        headers=headers,
    ).status_code == 403


def test_denials_do_not_leak_foreign_objects(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["outsider_token"]))
    body = client.get(f"/tenants/{ids['tenant_a']}/members", headers=headers).text.lower()
    for leaked in (str(ids["tenant_a"]).lower(), "p17 api a", "tenant_b", "space"):
        assert leaked not in body


def test_duplicate_membership_is_a_conflict_not_a_silent_success(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["operator_token"]))
    response = client.post(
        f"/tenants/{ids['tenant_a']}/members",
        json={"user_id": ids["target"], "role_id": ids["role_read_a"]},
        headers=headers,
    )
    assert response.status_code == 409, response.text


def test_wrong_role_scope_is_rejected(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["operator_token"]))
    response = client.post(
        f"/tenants/{ids['tenant_a']}/members",
        json={"user_id": ids["outsider"], "role_id": ids["role_space_a1"]},
        headers=headers,
    )
    assert response.status_code == 403, response.text


def test_structural_and_registry_surfaces_do_not_exist(stack) -> None:
    """§43/§79: tenant/space CRUD and registry administration are OUT of P17."""
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["operator_token"]))
    assert client.post("/tenants", json={"slug": "x"}, headers=headers).status_code in (404, 405)
    assert client.patch(
        f"/tenants/{ids['tenant_a']}", json={"name": "x"}, headers=headers
    ).status_code in (404, 405)
    assert client.delete(f"/tenants/{ids['tenant_a']}", headers=headers).status_code in (404, 405)
    for path in ("/platform-memberships", "/roles", "/permissions", "/resource-permissions"):
        response = client.post(path, json={}, headers=headers)
        assert response.status_code in (404, 405), f"{path} must not exist ({response.status_code})"
