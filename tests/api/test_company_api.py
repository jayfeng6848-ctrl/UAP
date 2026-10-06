"""P20 Company API tests — HTTP layer over the frozen contract (PDL Appendix AG).

Covers the authorization surface (allow / deny / missing projection), tenant
isolation, the frozen DTO contract, the error mapping (422 / 403 / 409) and the
route manifest. Behaviour runs through the real FastAPI app on a disposable
database; the runtime identity is ``uap_runtime``.
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
from apps.api.schemas.company import ASSIGNMENT_FIELDS, EMPLOYEE_FIELDS
from config.settings import load_settings_from_env
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from scripts.privileges import materialize as materialize_baseline_privileges
from services.company.projection import ensure_company_collections
from services.control_plane import provision_space, provision_tenant
from services.use_cases import login
from tests.integration.wave2_testkit import enroll_device

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
TEST_DB = "uap_p20_api_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
MIGRATION_DSN = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{TEST_DB}"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{TEST_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{TEST_DB}"
PASSWORD = "P20-Api-Passw0rd!"

#: Frozen Company route manifest (Appendix AG · D-P20A-08 = A).
COMPANY_ROUTES: tuple[tuple[str, str], ...] = (
    ("POST", "/company/tenants/{tenant_id}/employees"),
    ("GET", "/company/tenants/{tenant_id}/employees"),
    ("GET", "/company/tenants/{tenant_id}/employees/{employee_id}"),
    ("PATCH", "/company/tenants/{tenant_id}/employees/{employee_id}"),
    ("POST", "/company/tenants/{tenant_id}/employees/{employee_id}/suspend"),
    ("POST", "/company/tenants/{tenant_id}/employees/{employee_id}/terminate"),
    ("POST", "/company/tenants/{tenant_id}/assignments"),
    ("GET", "/company/tenants/{tenant_id}/assignments"),
    ("GET", "/company/tenants/{tenant_id}/assignments/{assignment_id}"),
    ("PATCH", "/company/tenants/{tenant_id}/assignments/{assignment_id}"),
    ("POST", "/company/tenants/{tenant_id}/assignments/{assignment_id}/end"),
    # P21 additions (PDL Appendix AP · F-2). The 11 routes above are unchanged.
    ("GET", "/company/tenants/{tenant_id}/capabilities"),
    ("GET", "/company/tenants/{tenant_id}/reports/operational"),
)


# ------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def engine():
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{TEST_DB}" OWNER uap_migrator'))
    admin.dispose()
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = MIGRATION_DSN
    cfg.attributes["lock_mode"] = "wait"
    command.upgrade(cfg, "head")
    fixtures = sa.create_engine(FIXTURE_DSN)
    materialize_baseline_privileges(fixtures)
    yield fixtures
    fixtures.dispose()
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
    admin.dispose()


def _token(client: TestClient, db: RuntimeDatabase, email: str) -> tuple[str, str]:
    response = client.post("/identity/onboarding", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201, response.text
    device_id = enroll_device(db, email=email, password=PASSWORD)
    issued = login(db, login_id=email, password=PASSWORD, device_id=device_id)
    assert issued.session is not None
    return issued.session.token, response.json()["user_id"]


def _tenant_with_space(engine: sa.Engine, tag: str) -> dict[str, str]:
    stamp = uuid.uuid4().hex[:10]
    with engine.begin() as conn:
        session = Session(bind=conn)
        tenant = provision_tenant(
            session, slug=f"p20api-{tag}-{stamp}", display_name=f"API {tag}", status="active"
        )
        space = provision_space(
            session, tenant_id=tenant["tenant_id"], key=f"dept-{tag}-{stamp}",
            name=f"API dept {tag}", status="active",
        )
        return {"tenant_id": tenant["tenant_id"], "space_id": space["space_id"]}


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
    runtime = RuntimeDatabase.from_config(
        DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime"
    )
    runtime.start()
    try:
        with TestClient(create_app(settings)) as client:
            admin_token, admin_id = _token(client, runtime, f"p20api-admin-{uuid.uuid4().hex[:8]}@example.invalid")
            plain_token, plain_id = _token(client, runtime, f"p20api-plain-{uuid.uuid4().hex[:8]}@example.invalid")
            with engine.begin() as conn:
                conn.execute(sa.text(
                    "UPDATE platform_state SET bootstrap_state = 'initialized',"
                    " initialized_at = now() WHERE id = 1 AND bootstrap_state = 'uninitialized'"
                ))
                conn.execute(sa.text(
                    "INSERT INTO platform_memberships (user_id, role_id, status)"
                    " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
                    " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
                ), {"u": admin_id})
            tenant_a = _tenant_with_space(engine, "a")
            tenant_b = _tenant_with_space(engine, "b")
            tenant_c = _tenant_with_space(engine, "c")  # deliberately unprojected
            with engine.begin() as conn:
                session = Session(bind=conn)
                ensure_company_collections(session, tenant_id=tenant_a["tenant_id"])
                ensure_company_collections(session, tenant_id=tenant_b["tenant_id"])
            yield SimpleNamespace(
                client=client, runtime=runtime, engine=engine,
                admin_token=admin_token, plain_token=plain_token,
                tenant_a=tenant_a["tenant_id"], space_a=tenant_a["space_id"],
                tenant_b=tenant_b["tenant_id"], space_b=tenant_b["space_id"],
                tenant_c=tenant_c["tenant_id"],
            )
    finally:
        runtime.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _employee_body(tag: str = "x") -> dict[str, object]:
    return {
        "employee_no": f"API-{tag}-{uuid.uuid4().hex[:8]}",
        "display_name": f"Employee {tag}",
        "title": "Engineer",
    }


def _create_employee(stack, tag: str = "x") -> dict:
    response = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees",
        json=_employee_body(tag),
        headers=_auth(stack.admin_token),
    )
    assert response.status_code == 201, response.text
    return response.json()


# --------------------------------------------------------------- authorization
def test_create_employee_returns_201_with_the_frozen_dto(stack) -> None:
    body = _create_employee(stack, "dto")
    assert set(body) == set(EMPLOYEE_FIELDS)
    assert body["tenant_id"] == str(stack.tenant_a)
    assert body["status"] == "active"
    assert body["terminated_at"] is None


def test_create_employee_requires_authorization(stack) -> None:
    denied = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees",
        json=_employee_body("deny"),
        headers=_auth(stack.plain_token),
    )
    assert denied.status_code == 403

    anonymous = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees", json=_employee_body("anon")
    )
    assert anonymous.status_code == 401


def test_missing_resource_projection_is_forbidden(stack) -> None:
    response = stack.client.post(
        f"/company/tenants/{stack.tenant_c}/employees",
        json=_employee_body("proj"),
        headers=_auth(stack.admin_token),
    )
    assert response.status_code == 403


def test_wrong_permission_is_forbidden(stack) -> None:
    """A tenant-scoped role without Company grants cannot reach the namespace."""
    assert stack.client.get(
        f"/company/tenants/{stack.tenant_a}/employees", headers=_auth(stack.plain_token)
    ).status_code == 403


# ------------------------------------------------------------ tenant isolation
def test_cross_tenant_employee_is_invisible(stack) -> None:
    employee = _create_employee(stack, "xtenant")
    response = stack.client.get(
        f"/company/tenants/{stack.tenant_b}/employees/{employee['employee_id']}",
        headers=_auth(stack.admin_token),
    )
    assert response.status_code == 422  # D-P20A-02 = A (no 404 class exists)


def test_cross_tenant_space_assignment_is_rejected(stack) -> None:
    employee = _create_employee(stack, "xspace")
    response = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/assignments",
        json={
            "employee_id": employee["employee_id"],
            "space_id": str(stack.space_b),
            "assignment_role": "member",
        },
        headers=_auth(stack.admin_token),
    )
    assert response.status_code == 422  # SPACE_NOT_FOUND -> validation


# -------------------------------------------------------------------- contract
def test_unknown_employee_maps_to_422(stack) -> None:
    response = stack.client.get(
        f"/company/tenants/{stack.tenant_a}/employees/{uuid.uuid4()}",
        headers=_auth(stack.admin_token),
    )
    assert response.status_code == 422


def test_invalid_employee_no_maps_to_422(stack) -> None:
    response = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees",
        json={"employee_no": "bad no!", "display_name": "Bad"},
        headers=_auth(stack.admin_token),
    )
    assert response.status_code == 422


def test_duplicate_employee_no_maps_to_409(stack) -> None:
    body = _employee_body("dup")
    first = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees", json=body, headers=_auth(stack.admin_token)
    )
    assert first.status_code == 201
    second = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees",
        json={**body, "display_name": "Different"},
        headers=_auth(stack.admin_token),
    )
    assert second.status_code == 409
    replay = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees", json=body, headers=_auth(stack.admin_token)
    )
    assert replay.status_code == 201  # D-P20A-07 = A (no 200/201 distinction)
    assert replay.json()["employee_id"] == first.json()["employee_id"]


def test_lifecycle_endpoints_and_conflicts(stack) -> None:
    employee = _create_employee(stack, "life")
    employee_id = employee["employee_id"]

    suspended = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees/{employee_id}/suspend",
        headers=_auth(stack.admin_token),
    )
    assert suspended.status_code == 200 and suspended.json()["status"] == "suspended"

    terminated = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees/{employee_id}/terminate",
        headers=_auth(stack.admin_token),
    )
    assert terminated.status_code == 200
    assert terminated.json()["status"] == "terminated"
    assert terminated.json()["terminated_at"] is not None

    again = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/employees/{employee_id}/suspend",
        headers=_auth(stack.admin_token),
    )
    assert again.status_code == 409


def test_update_employee_and_list_contract(stack) -> None:
    employee = _create_employee(stack, "upd")
    updated = stack.client.patch(
        f"/company/tenants/{stack.tenant_a}/employees/{employee['employee_id']}",
        json={"display_name": "Renamed"},
        headers=_auth(stack.admin_token),
    )
    assert updated.status_code == 200 and updated.json()["display_name"] == "Renamed"

    listed = stack.client.get(
        f"/company/tenants/{stack.tenant_a}/employees",
        params={"limit": 5, "status": "active"},
        headers=_auth(stack.admin_token),
    )
    assert listed.status_code == 200
    payload = listed.json()
    assert set(payload) == {"items", "count", "limit"}
    assert payload["limit"] == 5 and payload["count"] == len(payload["items"]) <= 5
    assert all(set(item) == set(EMPLOYEE_FIELDS) for item in payload["items"])


def test_list_limit_guard_is_422(stack) -> None:
    for limit in (0, 201):
        response = stack.client.get(
            f"/company/tenants/{stack.tenant_a}/employees",
            params={"limit": limit},
            headers=_auth(stack.admin_token),
        )
        assert response.status_code == 422, limit


def test_assignment_endpoints_full_flow(stack) -> None:
    employee = _create_employee(stack, "asg")
    created = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/assignments",
        json={
            "employee_id": employee["employee_id"],
            "space_id": str(stack.space_a),
            "assignment_role": "member",
        },
        headers=_auth(stack.admin_token),
    )
    assert created.status_code == 201, created.text
    assignment = created.json()
    assert set(assignment) == set(ASSIGNMENT_FIELDS)

    read = stack.client.get(
        f"/company/tenants/{stack.tenant_a}/assignments/{assignment['assignment_id']}",
        headers=_auth(stack.admin_token),
    )
    assert read.status_code == 200

    listed = stack.client.get(
        f"/company/tenants/{stack.tenant_a}/assignments",
        params={"employee_id": employee["employee_id"], "status": "active", "limit": 10},
        headers=_auth(stack.admin_token),
    )
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    patched = stack.client.patch(
        f"/company/tenants/{stack.tenant_a}/assignments/{assignment['assignment_id']}",
        json={"assignment_role": "lead"},
        headers=_auth(stack.admin_token),
    )
    assert patched.status_code == 200 and patched.json()["assignment_role"] == "lead"

    ended = stack.client.post(
        f"/company/tenants/{stack.tenant_a}/assignments/{assignment['assignment_id']}/end",
        headers=_auth(stack.admin_token),
    )
    assert ended.status_code == 200 and ended.json()["status"] == "ended"

    patched_after_end = stack.client.patch(
        f"/company/tenants/{stack.tenant_a}/assignments/{assignment['assignment_id']}",
        json={"assignment_role": "member"},
        headers=_auth(stack.admin_token),
    )
    assert patched_after_end.status_code == 409


# --------------------------------------------------------------------- routes
def test_company_route_manifest_is_frozen(stack) -> None:
    routes = {(method, route.path) for route in stack.client.app.routes for method in getattr(route, "methods", set()) or set() if route.path.startswith("/company")}
    assert routes == set(COMPANY_ROUTES)
    assert not any(method == "DELETE" for method, _ in routes)
    assert not any(path.endswith("/admin") for _, path in routes)


def test_no_event_surface_is_created(stack) -> None:
    with stack.engine.connect() as conn:
        events = conn.execute(sa.text("SELECT count(*) FROM events")).scalar_one()
    assert events == 0
