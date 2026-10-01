"""P18 F-P18-I-04 option ① — real HTTP control API with principal separation.

Authentication runs on the application identity boundary (``DATABASE_URL`` →
``uap_runtime``); structural control-plane execution runs on the dedicated
``CONTROL_DATABASE_URL`` → ``uap_control``. The two principals are proven
distinct, and the audit actor is the authenticated user — never ``uap_control``.
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

from apps.api.main import create_app
from config.settings import load_settings_from_env
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from scripts.privileges import materialize as materialize_baseline_privileges
from scripts.role_provisioning import provision as provision_control_plane
from services.use_cases import login
from tests.integration.wave2_testkit import enroll_device

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P18_DB = "uap_p18_http_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P18_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P18_DB}"
CONTROL_DSN = f"postgresql+psycopg://uap_control:trust@localhost:5432/{P18_DB}"
PASSWORD = "P18-Http-Passw0rd!"


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
def stack(engine):
    settings = load_settings_from_env(
        {
            "APP_ENV": "test",
            "DATABASE_URL": RUNTIME_DSN,
            "CONTROL_DATABASE_URL": CONTROL_DSN,
            "LOG_FORMAT": "console",
            "AI_DEFAULT_PROVIDER": "none",
            "AI_DEFAULT_MODEL": "none",
        }
    )
    runtime = RuntimeDatabase.from_config(
        DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime"
    )
    runtime.start()
    try:
        with TestClient(create_app(settings)) as client:
            ids = _seed(engine, client, runtime)
            yield SimpleNamespace(client=client, runtime=runtime, ids=ids)
    finally:
        runtime.dispose()


def _token(client, db, email: str) -> str:
    response = client.post("/identity/onboarding", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201, response.text
    device_id = enroll_device(db, email=email, password=PASSWORD)
    issued = login(db, login_id=email, password=PASSWORD, device_id=device_id)
    assert issued.session is not None
    return issued.session.token, response.json()["user_id"]


def _seed(engine, client, runtime) -> dict[str, str]:
    stamp = uuid.uuid4().hex[:8]
    platform_token, platform_id = _token(client, runtime, f"p18http-plat-{stamp}@example.invalid")
    plain_token, plain_id = _token(client, runtime, f"p18http-plain-{stamp}@example.invalid")
    with engine.begin() as conn:
        conn.execute(sa.text(
            "UPDATE platform_state SET bootstrap_state = 'initialized', initialized_at = now()"
            " WHERE id = 1 AND bootstrap_state = 'uninitialized'"
        ))
        conn.execute(sa.text(
            "INSERT INTO platform_memberships (user_id, role_id, status)"
            " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
            " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
        ), {"u": platform_id})
    return {
        "platform_token": platform_token, "platform_id": platform_id,
        "plain_token": plain_token, "plain_id": plain_id,
    }


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_principal_separation_is_real(stack, engine) -> None:
    runtime = sa.create_engine(RUNTIME_DSN)
    control = sa.create_engine(CONTROL_DSN)
    with runtime.connect() as conn:
        assert conn.execute(sa.text("SELECT current_user")).scalar_one() == "uap_runtime"
    with control.connect() as conn:
        assert conn.execute(sa.text("SELECT current_user")).scalar_one() == "uap_control"
    runtime.dispose()
    control.dispose()


def test_http_provisioning_metadata_lifecycle_and_audit_actor(stack, engine) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["platform_token"]))
    correlation = str(uuid.uuid4())
    slug = f"p18http-{uuid.uuid4().hex[:8]}"
    created = client.post(
        "/control/tenants",
        json={"slug": slug, "display_name": "HTTP Tenant",
              "initial_admin_user_id": ids["platform_id"]},
        headers={**headers, "x-correlation-id": correlation},
    )
    assert created.status_code == 201, created.text
    tenant_id = created.json()["tenant_id"]
    assert created.json()["status"] == "active" and created.json()["replayed"] is False

    assert client.get(f"/control/tenants/{tenant_id}", headers=headers).status_code == 200
    patched = client.patch(
        f"/control/tenants/{tenant_id}", json={"display_name": "HTTP Renamed"}, headers=headers
    )
    assert patched.status_code == 200, patched.text
    suspended = client.post(
        f"/control/tenants/{tenant_id}/lifecycle", json={"state": "suspended"}, headers=headers
    )
    assert suspended.status_code == 200 and suspended.json()["status"] == "suspended"

    # Audit: actor = authenticated user (never the DB principal)
    with engine.begin() as conn:
        rows = [dict(r._mapping) for r in conn.execute(
            sa.text("SELECT action, actor_id FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)"),
            {"c": correlation},
        ).all()]
    assert rows and rows[0]["action"] == "tenant.provision"
    assert str(rows[0]["actor_id"]) == ids["platform_id"]
    assert str(rows[0]["actor_id"]) != "uap_control"


def test_http_idempotent_replay(stack) -> None:
    ids, client = stack.ids, stack.client
    headers = _auth(str(ids["platform_token"]))
    slug = f"p18http-replay-{uuid.uuid4().hex[:8]}"
    payload = {"slug": slug, "display_name": "Replay", "initial_admin_user_id": ids["platform_id"]}
    first = client.post("/control/tenants", json=payload, headers=headers)
    again = client.post("/control/tenants", json=payload, headers=headers)
    assert first.status_code == 201 and again.status_code == 201
    assert again.json()["tenant_id"] == first.json()["tenant_id"]
    assert again.json()["replayed"] is True
    conflict = client.post(
        "/control/tenants", json={**payload, "display_name": "Other"}, headers=headers
    )
    assert conflict.status_code == 409


def test_http_negative_matrix(stack) -> None:
    ids, client = stack.ids, stack.client
    # unauthenticated (well-formed body: authentication is what must fail)
    assert client.post(
        "/control/tenants",
        json={"slug": f"p18http-anon-{uuid.uuid4().hex[:6]}", "display_name": "Anon",
              "initial_admin_user_id": ids["plain_id"]},
    ).status_code == 401
    # authenticated but not a platform authority
    response = client.post(
        "/control/tenants",
        json={"slug": f"p18http-deny-{uuid.uuid4().hex[:6]}", "display_name": "Denied",
              "initial_admin_user_id": ids["plain_id"]},
        headers=_auth(str(ids["plain_token"])),
    )
    assert response.status_code == 403
    # no physical delete endpoint exists
    for path in ("/control/tenants/x", "/control/tenants/x/spaces/y"):
        assert client.delete(path, headers=_auth(str(ids["platform_token"]))).status_code in (404, 405)
    # unknown lifecycle target is refused, not silently accepted
    created = client.post(
        "/control/tenants",
        json={"slug": f"p18http-life-{uuid.uuid4().hex[:6]}", "display_name": "Life",
              "initial_admin_user_id": ids["platform_id"]},
        headers=_auth(str(ids["platform_token"])),
    )
    tenant_id = created.json()["tenant_id"]
    denied = client.post(
        f"/control/tenants/{tenant_id}/lifecycle", json={"state": "deleted"},
        headers=_auth(str(ids["platform_token"])),
    )
    assert denied.status_code == 409


def test_control_api_unavailable_without_control_dsn(stack) -> None:
    settings = load_settings_from_env(
        {"APP_ENV": "test", "DATABASE_URL": RUNTIME_DSN, "LOG_FORMAT": "console",
         "AI_DEFAULT_PROVIDER": "none", "AI_DEFAULT_MODEL": "none"}
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/control/tenants",
            json={"slug": "unavailable-env", "display_name": "X", "initial_admin_user_id": "u"},
            headers=_auth("x"),
        )
        assert response.status_code == 503
