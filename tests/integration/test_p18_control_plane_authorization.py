"""P18-D06 / §11–§14 — pre-resource authorization proof on a real database.

Proves that the *existing, canonical* ``AuthorizationService`` can evaluate
``platform scope + resource = None`` safely (a clean ALLOW/DENY rather than an
exception escaping the engine), and that only an explicit platform authority
obtains the allow.

Execution context: the authorization layer is read-only, so the proof runs as
``uap_runtime`` (the principal that already holds every SELECT the decision
needs) — the uap_control-equivalent **read** context. Provisioning the actual
``uap_control`` principal is blocked separately (F-P18-I-01).
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from core.permission import Action, AuthorizationRequest, Decision, Subject
from scripts.privileges import materialize as materialize_baseline_privileges
from services.authorization import AuthorizationRepository, AuthorizationService

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P18_DB = "uap_p18_authz_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P18_DB}"
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
    yield fixtures
    fixtures.dispose()
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P18_DB}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def actors(engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        for key in ("platform", "plain"):
            ids[key] = str(conn.execute(
                sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                {"e": f"p18authz-{key}-{uuid.uuid4().hex[:8]}@example.invalid"},
            ).scalar_one())
        # The first platform binding is admitted by the existing bootstrap gate.
        conn.execute(
            sa.text(
                "INSERT INTO platform_memberships (user_id, role_id, status)"
                " SELECT CAST(:u AS uuid), r.id, 'active' FROM roles r"
                " WHERE r.key = 'platform_admin' AND r.scope = 'PLATFORM'"
            ),
            {"u": ids["platform"]},
        )
    return ids


@pytest.fixture(scope="module")
def service(engine):
    runtime = sa.create_engine(RUNTIME_DSN)
    yield AuthorizationService(engine=runtime, repository=AuthorizationRepository(runtime))
    runtime.dispose()


def _ask(service, *, actor: str, action: str, resource_type: str) -> Decision:
    return service.authorize(
        AuthorizationRequest(
            subject=Subject(identity_id=actor, subject_type="USER", actor_id=actor),
            action=Action(name=action, resource_type=resource_type),
            resource=None,
        )
    )


def test_platform_authority_allows_pre_resource_operation(service, actors) -> None:
    decision = _ask(service, actor=actors["platform"], action="admin", resource_type="tenant")
    assert decision.effect == "ALLOW", decision.reason


def test_non_platform_actor_is_denied(service, actors) -> None:
    decision = _ask(service, actor=actors["plain"], action="admin", resource_type="tenant")
    assert decision.effect == "DENY"


def test_decision_is_returned_never_an_exception(service, actors) -> None:
    """The engine's contract: every failure denies — no exception escapes."""
    for actor in (actors["platform"], actors["plain"]):
        for resource_type in ("tenant", "space"):
            decision = _ask(service, actor=actor, action="admin", resource_type=resource_type)
            assert decision.effect in ("ALLOW", "DENY", "REQUIRES_APPROVAL")


def test_crud_actions_have_no_structural_permission(service, actors) -> None:
    """Structural authority is the frozen `admin` action, not a new CRUD taxonomy."""
    for action in ("create", "update", "delete"):
        decision = _ask(service, actor=actors["platform"], action=action, resource_type="tenant")
        assert decision.effect == "DENY", f"{action} must not be a structural grant"


def test_missing_declared_resource_type_denies_without_exception(service, actors) -> None:
    decision = service.authorize(
        AuthorizationRequest(
            subject=Subject(
                identity_id=actors["platform"], subject_type="USER", actor_id=actors["platform"]
            ),
            action=Action(name="admin"),
            resource=None,
        )
    )
    assert decision.effect == "DENY"
    assert decision.reason == "pre-resource-requires-declared-resource-type"
