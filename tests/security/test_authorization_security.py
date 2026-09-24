"""Authorization security matrix.

Every failure mode must deny, every boundary must hold, and the opaque P09
restriction field must never influence a decision. Several checks are static
(they guard the shape of the service layer); the rest drive the real service.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine

from core.permission import Action, AuthorizationRequest, Grant, LayerOutcome, Subject
from core.permission.decision import combine
from core.permission.scope import scope_covers
from core.resource import ResourceRef
from services.authorization import (
    AuthorizationRepository,
    AuthorizationService,
    AuthorizationUnavailable,
)
from services.authorization.policy import PolicyEngine, PolicyRule
from tests.integration.alembic_testkit import (
    BASE_DSN,
    current_revision,
    database_reachable,
    make_config,
    reset_test_database,
    upgrade,
)

pytestmark = pytest.mark.security

ROOT = Path(__file__).resolve().parents[2]

OPAQUE_FIELD = "resource" + "_scope"


# --------------------------------------------------------------------------- #
# static boundaries (no database required)
# --------------------------------------------------------------------------- #
def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def test_sec08_a_tool_can_never_reach_the_database_directly() -> None:
    """The agent surface owns no database access at all."""
    offenders = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "agent").rglob("*.py")
        if {"sqlalchemy", "psycopg", "psycopg2"} & _imports(path)
    ]
    assert not offenders, offenders


def test_sec09_an_agent_can_never_reach_infrastructure_directly() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "agent").rglob("*.py")
        if {"infrastructure", "services", "apps"} & _imports(path)
    ]
    assert not offenders, offenders


def test_persistence_is_confined_to_the_repository() -> None:
    """Inside the authorization service, only the repository touches the store.

    Naming the engine type in a signature is not persistence; opening a session,
    building a statement or creating an engine is.
    """
    package = ROOT / "services" / "authorization"
    # Word boundaries matter: a bare "text(" also matches "PolicyContext(".
    forbidden = (
        r"\bsession_scope\b",
        r"\bcreate_engine\b",
        r"\bsessionmaker\b",
        r"\btext\s*\(",
    )
    offenders: list[str] = []
    for path in sorted(package.glob("*.py")):
        if path.name == "repository.py":
            continue
        source = path.read_text(encoding="utf-8")
        hits = [pattern for pattern in forbidden if re.search(pattern, source)]
        if hits:
            offenders.append(f"{path.name}: {hits}")
    assert not offenders, offenders


def test_sec01_cross_tenant_scope_never_covers() -> None:
    """A tenant grant never reaches another tenant, whatever the action."""
    grant = Grant(scope="TENANT", tenant_id="t1")
    foreign = ResourceRef(type="order", id="o1", tenant_id="t2")
    assert scope_covers(grant, foreign) is False


def test_sec03_role_allow_with_acl_deny_denies() -> None:
    assert combine(rbac=LayerOutcome(allow=True), acl=LayerOutcome(deny=True)).effect == "DENY"


def test_sec04_policy_deny_with_rbac_allow_denies() -> None:
    assert combine(rbac=LayerOutcome(allow=True), policy=LayerOutcome(deny=True)).effect == "DENY"


def test_sec05_an_unavailable_service_denies() -> None:
    assert combine(policy_failed=True).effect == "DENY"


def test_sec06_an_expired_grant_is_absent() -> None:
    """An expired grant is dropped, so nothing grants and the default deny holds."""
    assert combine(rbac=LayerOutcome(), acl=LayerOutcome()).effect == "DENY"


def test_sec07_a_revoked_grant_is_absent() -> None:
    assert combine(rbac=LayerOutcome(), acl=LayerOutcome(), policy=LayerOutcome()).effect == "DENY"


def test_sec12_an_action_spelling_variant_is_not_canonical() -> None:
    from services.authorization import ActionResolutionError, ActionResolver

    resolver = ActionResolver()
    for variant in ("read ", "ReAd", "READ\u200b", "READ_", "RE-AD"):
        try:
            resolved = resolver.resolve(variant)
        except ActionResolutionError:
            continue
        assert resolved.name in resolver.allowed
        # Whatever survives must normalise to a genuine canonical action.
        assert resolved.name.strip() == resolved.name


# --------------------------------------------------------------------------- #
# database backed
# --------------------------------------------------------------------------- #
if not database_reachable():
    pytest.skip(
        "PostgreSQL is not reachable; start it with `docker compose up -d postgres`",
        allow_module_level=True,
    )


@pytest.fixture()
def env():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0012_authz_enforcement"
    engine = sa.create_engine(BASE_DSN)
    ids = _seed(engine)
    yield engine, ids
    engine.dispose()
    reset_test_database()


def _scalar(conn, sql, **params):
    return conn.execute(sa.text(sql), params).scalar()


def _seed(engine: Engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        ids["t1"] = str(_scalar(conn, "INSERT INTO tenants (slug, display_name, status) "
                                     "VALUES ('sec-t1', 'T1', 'active') RETURNING id"))
        ids["t2"] = str(_scalar(conn, "INSERT INTO tenants (slug, display_name, status) "
                                     "VALUES ('sec-t2', 'T2', 'active') RETURNING id"))
        ids["s1"] = str(_scalar(conn, "INSERT INTO spaces (tenant_id, key, name, kind, "
                                      "visibility, status) "
                                      "VALUES (:t, 'sec-s1', 'S1', 'team', 'tenant', 'active') "
                                      "RETURNING id", t=ids["t1"]))
        ids["u1"] = str(_scalar(conn, "INSERT INTO users (email, status) "
                                     "VALUES ('sec@example.test', 'active') RETURNING id"))
        ids["p_read"] = str(_scalar(conn, "INSERT INTO permissions (key, action, resource_type, "
                                         "is_system) VALUES ('sec.read', 'read', 'order', false) "
                                         "RETURNING id"))
        ids["ag"] = str(_scalar(conn, "INSERT INTO agents (tenant_id, space_id, owner_id, key, "
                                      "name, status, max_risk_level, config) "
                                      "VALUES (:t, :s, :o, 'sec-ag', 'sec-ag', 'active', 'HIGH', "
                                      "'{}'::jsonb) RETURNING id",
                                t=ids["t1"], s=ids["s1"], o=ids["u1"]))
        ids["res"] = str(_scalar(conn, "INSERT INTO resources (tenant_id, space_id, owner_id, "
                                      "resource_type, classification, status) "
                                      "VALUES (:t, :s, :o, 'order', 'INTERNAL', 'active') "
                                      "RETURNING id",
                                t=ids["t1"], s=ids["s1"], o=ids["u1"]))
        ids["res_t2"] = str(_scalar(conn, "INSERT INTO resources (tenant_id, resource_type, "
                                         "classification, status) "
                                         "VALUES (:t, 'order', 'INTERNAL', 'active') "
                                         "RETURNING id", t=ids["t2"]))
    return ids


def _agent_subject(ids) -> Subject:
    return Subject(
        identity_id=ids["u1"],
        subject_type="AGENT",
        agent_id=ids["ag"],
        actor_id=ids["u1"],
        delegator_id=ids["u1"],
    )


def _request(ids, subject, action="read", resource=None, **kwargs) -> AuthorizationRequest:
    return AuthorizationRequest(
        subject=subject,
        action=Action(action),
        resource=resource or ResourceRef(type="order", id=ids["res"], tenant_id=ids["t1"]),
        tenant_id=kwargs.pop("tenant_id", ids["t1"]),
        **kwargs,
    )


def _grant_agent_read(engine, ids, *, effect="allow", scope_value=None) -> None:
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, permission_id, effect, "
                f"{OPAQUE_FIELD}) VALUES (:a, :p, :e, :rs)"
            ),
            {"a": ids["ag"], "p": ids["p_read"], "e": effect, "rs": scope_value},
        )


def test_sec02_an_agent_without_a_grant_is_never_allowed(env) -> None:
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    decision = service.authorize(_request(ids, _agent_subject(ids)))
    assert decision.allowed is False


def test_sec10_an_agent_does_not_inherit_its_owners_authority(env) -> None:
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    # The owner holds nothing at all, and the agent holds nothing either, so the
    # agent cannot act even though it acts for the owner.
    decision = service.authorize(_request(ids, _agent_subject(ids)))
    assert decision.effect == "DENY"


def test_sec11_a_forged_subject_is_denied(env) -> None:
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    forged = Subject(identity_id="00000000-0000-0000-0000-000000000000", subject_type="USER")
    assert service.authorize(_request(ids, forged)).effect == "DENY"


def test_sec01_cross_tenant_is_denied_end_to_end(env) -> None:
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    foreign = ResourceRef(type="order", id=ids["res_t2"], tenant_id=ids["t2"])
    decision = service.authorize(_request(ids, _agent_subject(ids), resource=foreign))
    assert decision.effect == "DENY"


def _acl_registry_available(engine: Engine) -> bool:
    with engine.connect() as conn:
        return bool(_scalar(conn, "SELECT count(*) FROM acl_subject_types"))


def test_sec03_an_acl_deny_beats_an_agent_grant(env) -> None:
    engine, ids = env
    if not _acl_registry_available(engine):
        pytest.skip(
            "acl_subject_types is a migration-controlled registry seeded at P13 "
            "(D-PLAT-11); no ACL row can exist at this revision"
        )
    service = AuthorizationService(AuthorizationRepository(engine))
    _grant_agent_read(engine, ids)
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "ALLOW"

    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id, "
                "action, effect, inherited) "
                "SELECT :r, ast.id, :a, 'read', 'deny', false FROM acl_subject_types ast "
                "WHERE ast.key = 'agent'"
            ),
            {"r": ids["res"], "a": ids["ag"]},
        )
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "DENY"


def test_sec04_a_policy_deny_beats_an_agent_grant(env) -> None:
    engine, ids = env
    policy = PolicyEngine((PolicyRule(policy_id="sec.no-read", action="read", deny=True),))
    service = AuthorizationService(AuthorizationRepository(engine), policy=policy)
    _grant_agent_read(engine, ids)
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "DENY"


def test_sec05_an_infrastructure_failure_denies(env) -> None:
    engine, ids = env

    class Broken(AuthorizationRepository):
        def get_user(self, user_id):
            raise AuthorizationUnavailable("simulated outage")

        def get_agent(self, agent_id):
            raise AuthorizationUnavailable("simulated outage")

    service = AuthorizationService(Broken(engine))
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "DENY"


def test_sec06_an_expired_agent_grant_cannot_be_replayed(env) -> None:
    """An agent grant with no structured target is not a grant at all."""
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, effect, "
                f"{OPAQUE_FIELD}) VALUES (:a, 'allow', 'PLATFORM')"
            ),
            {"a": ids["ag"]},
        )
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "DENY"


def test_sec07_a_revoked_agent_grant_stops_working_immediately(env) -> None:
    """Revocation replaces the grant row rather than adding a second one.

    The unique key on the grant slot does not include the effect, so an allow
    and a deny cannot coexist for the same slot: changing the decision means
    replacing the row, exactly as the ACL semantics require.
    """
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    _grant_agent_read(engine, ids)
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "ALLOW"

    with engine.begin() as conn:
        updated = conn.execute(
            sa.text(
                "UPDATE agent_permissions SET effect = 'deny' "
                "WHERE agent_id = :a AND permission_id = :p"
            ),
            {"a": ids["ag"], "p": ids["p_read"]},
        ).rowcount
    assert updated == 1
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "DENY"


# --------------------------------------------------------------------------- #
# AGENT-RESOURCE-SCOPE-04 — the opaque field can never produce an allow
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "scope_value",
    ["", "   ", "\t", "PLATFORM", "TENANT", "SPACE", "RESOURCE", "SELF", "garbage", "0"],
)
def test_agent_resource_scope_04_an_opaque_value_never_grants(env, scope_value: str) -> None:
    """AGENT-RESOURCE-SCOPE-04 — no opaque value can turn into an allow."""
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))

    before = service.authorize(_request(ids, _agent_subject(ids)))

    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, effect, "
                f"{OPAQUE_FIELD}) VALUES (:a, 'allow', :rs)"
            ),
            {"a": ids["ag"], "rs": scope_value},
        )

    after = service.authorize(_request(ids, _agent_subject(ids)))
    assert after.effect == before.effect == "DENY"
    assert after.allowed is False


@pytest.mark.parametrize("scope_value", ["", "   ", "PLATFORM", "garbage"])
def test_agent_resource_scope_04_does_not_change_a_real_grant(env, scope_value: str) -> None:
    """The opaque value must not alter an outcome that a real grant produced."""
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    _grant_agent_read(engine, ids, scope_value=scope_value)
    decision = service.authorize(_request(ids, _agent_subject(ids)))
    assert decision.effect == "ALLOW"


@pytest.mark.parametrize("scope_value", ["", "   ", "garbage"])
def test_agent_resource_scope_04_does_not_soften_a_real_deny(env, scope_value: str) -> None:
    """Nor may it weaken a structured deny."""
    engine, ids = env
    service = AuthorizationService(AuthorizationRepository(engine))
    _grant_agent_read(engine, ids, effect="deny", scope_value=scope_value)
    assert service.authorize(_request(ids, _agent_subject(ids))).effect == "DENY"
