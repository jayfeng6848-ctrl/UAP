"""Authorization service, end to end against a real database.

RBAC, ACL and Policy are composed exactly once, in one place, with deny always
winning and every failure denying. The tests below drive the service through
real rows: cross-tenant attempts, deny precedence, expiry, agent independence,
risk ceilings, and the tool boundary.
"""

from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine

from core.permission import Action, AuthorizationRequest, AuthorizationRequest as Req
from core.permission import Subject
from core.resource import ResourceRef
from services.authorization import AuthorizationRepository, AuthorizationService, ToolGate
from services.authorization.policy import PolicyEngine, PolicyRule
from tests.integration.alembic_testkit import (
    BASE_DSN,
    current_revision,
    database_reachable,
    make_config,
    reset_test_database,
    upgrade,
)

pytestmark = pytest.mark.integration

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


# --------------------------------------------------------------------------- #
# seed
# --------------------------------------------------------------------------- #
def _scalar(conn: Connection, sql: str, **params):
    return conn.execute(sa.text(sql), params).scalar()


def _seed(engine: Engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        for key, slug in (("t1", "t-one"), ("t2", "t-two")):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO tenants (slug, display_name, status) "
                    "VALUES (:slug, :slug, 'active') RETURNING id",
                    slug=slug,
                )
            )
        for key, tenant, name in (
            ("s1", "t1", "Space One"),
            ("s2", "t1", "Space Two"),
            ("s3", "t2", "Space Three"),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                    "VALUES (:t, :k, :n, 'team', 'tenant', 'active') RETURNING id",
                    t=ids[tenant],
                    k=key,
                    n=name,
                )
            )

        for key, email in (
            ("u_ok", "ok@example.test"),
            ("u_acl", "acl@example.test"),
            ("u_susp", "susp@example.test"),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO users (email, status) VALUES (:e, :s) RETURNING id",
                    e=email,
                    s="active" if key != "u_susp" else "suspended",
                )
            )

        # Scope shape is enforced by a trigger: SPACE roles carry a space and no
        # tenant; TENANT roles carry a tenant and no space; PLATFORM roles carry
        # neither.
        for key, scope, tenant, space in (
            ("r_platform", "PLATFORM", None, None),
            ("r_tenant", "TENANT", "t1", None),
            ("r_space", "SPACE", None, "s1"),
            ("r_other", "TENANT", "t2", None),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO roles (key, name, scope, tenant_id, space_id, is_system, status) "
                    "VALUES (:k, :k, :sc, :t, :sp, false, 'active') RETURNING id",
                    k=key,
                    sc=scope,
                    t=ids[tenant] if tenant else None,
                    sp=ids[space] if space else None,
                )
            )

        for key, action, resource_type in (
            ("p_read", "read", "order"),
            ("p_exec", "execute", "order"),
            ("p_deny", "read", "order"),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO permissions (key, action, resource_type, is_system) "
                    "VALUES (:k, :a, :rt, false) RETURNING id",
                    k=f"demo.{key}",
                    a=action,
                    rt=resource_type,
                )
            )

        for role, permission, effect in (
            ("r_platform", "p_read", "allow"),
            ("r_tenant", "p_read", "allow"),
            ("r_space", "p_read", "allow"),
            ("r_other", "p_read", "allow"),
            ("r_space", "p_deny", "deny"),
        ):
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id, effect) "
                    "VALUES (:r, :p, :e)"
                ),
                {"r": ids[role], "p": ids[permission], "e": effect},
            )

        conn.execute(
            sa.text(
                "INSERT INTO platform_memberships (user_id, role_id, status) "
                "VALUES (:u, :r, 'active')"
            ),
            {"u": ids["u_ok"], "r": ids["r_platform"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                "VALUES (:t, :u, :r, 'active')"
            ),
            {"t": ids["t1"], "u": ids["u_ok"], "r": ids["r_tenant"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                "VALUES (:t, :s, :u, :r, 'active')"
            ),
            {"t": ids["t1"], "s": ids["s1"], "u": ids["u_ok"], "r": ids["r_space"]},
        )

        for key, tenant, space, owner, resource_type in (
            ("res1", "t1", "s1", "u_ok", "order"),
            ("res2", "t1", "s2", None, "order"),
            ("res3", "t2", "s3", None, "order"),
            ("res4", "t1", "s1", None, "order"),
            ("res5", "t1", "s1", None, "order"),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO resources (tenant_id, space_id, owner_id, resource_type, "
                    "classification, status) "
                    "VALUES (:t, :s, :o, :rt, 'INTERNAL', 'active') RETURNING id",
                    t=ids[tenant],
                    s=ids[space],
                    o=ids[owner] if owner else None,
                    rt=resource_type,
                )
            )

        # ``acl_subject_types`` is a platform-controlled registry: a trigger
        # rejects runtime INSERT, and its rows are seeded at P13. Until then the
        # ACL table cannot carry a row at all, so ACL-dependent assertions are
        # skipped rather than worked around — bypassing the registry protection
        # to make a test pass would be exactly the wrong trade.
        registry = int(
            _scalar(conn, "SELECT count(*) FROM acl_subject_types") or 0
        )
        ids["acl_available"] = "1" if registry else "0"
        if registry:
            user_type = str(
                _scalar(conn, "SELECT id FROM acl_subject_types WHERE key = 'user'")
            )
            ids["acl_user"] = user_type

            # ACL: an explicit deny on res1, an allow for a user with no role on res2.
            conn.execute(
                sa.text(
                    "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id, "
                    "action, effect, inherited) VALUES (:r, :st, :su, 'read', 'deny', false)"
                ),
                {"r": ids["res1"], "st": user_type, "su": ids["u_ok"]},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id, "
                    "action, effect, inherited) VALUES (:r, :st, :su, 'read', 'allow', false)"
                ),
                {"r": ids["res2"], "st": user_type, "su": ids["u_acl"]},
            )
            # ACL: an allow that has already expired, and a deny that has expired.
            conn.execute(
                sa.text(
                    "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id, "
                    "action, effect, inherited, expires_at) "
                    "VALUES (:r, :st, :su, 'read', 'allow', false, now() - interval '1 day')"
                ),
                {"r": ids["res4"], "st": user_type, "su": ids["u_acl"]},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO resource_permissions (resource_id, subject_type_id, subject_id, "
                    "action, effect, inherited, expires_at) "
                    "VALUES (:r, :st, :su, 'read', 'deny', false, now() - interval '1 day')"
                ),
                {"r": ids["res5"], "st": user_type, "su": ids["u_ok"]},
            )

        for key, owner, tenant, space, status, max_risk in (
            ("ag1", "u_ok", "t1", "s1", "active", "HIGH"),
            ("ag_lowrisk", "u_ok", "t1", "s1", "active", "LOW"),
            ("ag_t2", "u_ok", "t2", "s3", "active", "HIGH"),
            ("ag_off", "u_ok", "t1", "s1", "disabled", "HIGH"),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO agents (tenant_id, space_id, owner_id, key, name, status, "
                    "max_risk_level, config) "
                    "VALUES (:t, :s, :o, :k, :k, :st, :mr, '{}'::jsonb) RETURNING id",
                    t=ids[tenant],
                    s=ids[space],
                    o=ids[owner],
                    k=key,
                    st=status,
                    mr=max_risk,
                )
            )
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, permission_id, effect) "
                "VALUES (:a, :p, 'allow')"
            ),
            {"a": ids["ag1"], "p": ids["p_read"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, permission_id, effect) "
                "VALUES (:a, :p, 'allow')"
            ),
            {"a": ids["ag_lowrisk"], "p": ids["p_read"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO agent_permissions (agent_id, permission_id, effect) "
                "VALUES (:a, :p, 'allow')"
            ),
            {"a": ids["ag_t2"], "p": ids["p_read"]},
        )

        for key, tenant, approval, enabled, risk in (
            ("tool_ok", "t1", False, True, "LOW"),
            ("tool_approval", "t1", True, True, "LOW"),
            ("tool_disabled", "t1", False, False, "LOW"),
            ("tool_highrisk", "t1", False, True, "HIGH"),
        ):
            ids[key] = str(
                _scalar(
                    conn,
                    "INSERT INTO tools (tenant_id, key, name, risk_level, timeout_ms, "
                    "idempotency_mode, audit_policy, approval_required, enabled) "
                    "VALUES (:t, :k, :k, :r, 1000, 'none', 'sampling', :ap, :e) RETURNING id",
                    t=ids[tenant],
                    k=key,
                    r=risk,
                    ap=approval,
                    e=enabled,
                )
            )
        conn.execute(
            sa.text(
                "INSERT INTO tool_permissions (tool_id, permission_id, effect, resource_type, "
                "action, scope) VALUES (:tl, :p, 'allow', 'order', 'execute', 'TENANT')"
            ),
            {"tl": ids["tool_ok"], "p": ids["p_exec"]},
        )
    return ids


def _service(engine: Engine, **kwargs) -> AuthorizationService:
    return AuthorizationService(AuthorizationRepository(engine), **kwargs)


def _require_acl(ids: dict[str, str]) -> None:
    """Skip ACL assertions while the subject-type registry cannot be populated.

    ``acl_subject_types`` is a platform-controlled registry whose rows are
    migration-controlled and seeded at P13, so at this revision no ACL row can
    exist. The ACL evaluation logic is covered by unit tests with a stub
    repository; end-to-end coverage resumes once the registry is seeded.
    """
    if ids.get("acl_available") != "1":
        pytest.skip(
            "acl_subject_types is a migration-controlled registry seeded at P13 "
            "(D-PLAT-11); no ACL row can exist at this revision"
        )


def _order(resource_id: str, tenant_id: str, space_id: str | None = None) -> ResourceRef:
    return ResourceRef(type="order", id=resource_id, tenant_id=tenant_id, space_id=space_id)


def _request(subject: Subject, action: str, resource: ResourceRef, **kwargs) -> Req:
    return AuthorizationRequest(subject=subject, action=Action(action), resource=resource, **kwargs)


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #
def test_rbac_platform_role_grants_across_the_tenant(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "ALLOW"


def test_rbac_space_role_does_not_reach_another_space(env) -> None:
    engine, ids = env
    service = _service(engine)
    # A user holding only a space role must not act outside that space.
    with engine.begin() as conn:
        conn.execute(
            sa.text("DELETE FROM platform_memberships WHERE user_id = :u"),
            {"u": ids["u_ok"]},
        )
        conn.execute(
            sa.text("DELETE FROM tenant_memberships WHERE user_id = :u"),
            {"u": ids["u_ok"]},
        )
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"


def test_default_deny_when_no_grant_matches(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(
            Subject(identity_id=ids["u_acl"]),
            "delete",
            _order(ids["res2"], ids["t1"]),
            tenant_id=ids["t1"],
        )
    )
    assert decision.effect == "DENY"
    assert decision.reason == "default-deny"


# --------------------------------------------------------------------------- #
# ACL
# --------------------------------------------------------------------------- #
def test_acl_allow_grants_without_any_role(env) -> None:
    engine, ids = env
    _require_acl(ids)
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_acl"]), "read", _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "ALLOW"


def test_acl_deny_overrides_rbac_allow(env) -> None:
    engine, ids = env
    _require_acl(ids)
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res1"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"
    assert decision.reason == "acl-deny"


def test_an_expired_allow_is_absent_not_a_grant(env) -> None:
    engine, ids = env
    _require_acl(ids)
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_acl"]), "read", _order(ids["res4"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"


def test_an_expired_deny_is_absent_not_a_block(env) -> None:
    engine, ids = env
    _require_acl(ids)
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res5"], ids["t1"]), tenant_id=ids["t1"])
    )
    # The expired deny no longer exists, so the platform role's grant stands.
    assert decision.effect == "ALLOW"


# --------------------------------------------------------------------------- #
# boundaries and failures
# --------------------------------------------------------------------------- #
def test_cross_tenant_is_unconditionally_denied(env) -> None:
    engine, ids = env
    service = _service(engine)
    # The caller asserts tenant t1 while the resource lives in t2: the boundary
    # check runs before any grant is considered, so no role can rescue it.
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res3"], ids["t2"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"
    assert decision.reason == "cross-tenant"


def test_a_suspended_subject_is_denied(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_susp"]), "read", _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"
    assert "subject" in decision.reason


def test_an_unknown_subject_is_denied(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id="00000000-0000-0000-0000-000000000000"), "read",
                 _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"


def test_an_unknown_resource_is_denied(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read",
                 _order("00000000-0000-0000-0000-000000000000", ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"
    assert "resource" in decision.reason


def test_a_non_canonical_action_is_denied_without_touching_the_store(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "OBLITERATE", _order(ids["res2"], ids["t1"]),
                 tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"
    assert decision.reason.startswith("non-canonical-action")


# --------------------------------------------------------------------------- #
# policy and approval
# --------------------------------------------------------------------------- #
def test_a_policy_deny_overrides_a_grant(env) -> None:
    engine, ids = env
    policy = PolicyEngine((PolicyRule(policy_id="no-reads", action="read", deny=True),))
    service = _service(engine, policy=policy)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res5"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"
    assert decision.reason == "policy-deny"


def test_high_risk_yields_requires_approval(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res5"], ids["t1"]),
                 tenant_id=ids["t1"], risk_level="HIGH")
    )
    assert decision.effect == "REQUIRES_APPROVAL"
    assert decision.allowed is False


def test_a_policy_failure_denies_even_with_a_grant(env) -> None:
    engine, ids = env

    class Exploding(PolicyEngine):
        def evaluate(self, context, risk_level=None):  # type: ignore[override]
            from services.authorization.policy import PolicyEvaluation

            return PolicyEvaluation(failed=True, policy_version="broken")

    service = _service(engine, policy=Exploding())
    decision = service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res5"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert decision.effect == "DENY"


# --------------------------------------------------------------------------- #
# agents
# --------------------------------------------------------------------------- #
def test_an_agent_acts_as_an_independent_subject(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(
            Subject(identity_id=ids["u_ok"], subject_type="AGENT", agent_id=ids["ag1"],
                    actor_id=ids["u_ok"], delegator_id=ids["u_ok"]),
            "read",
            _order(ids["res1"], ids["t1"], ids["s1"]),
            tenant_id=ids["t1"],
            space_id=ids["s1"],
        )
    )
    assert decision.effect == "ALLOW"


def test_an_agent_is_bounded_by_its_own_binding(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(
            Subject(identity_id=ids["u_ok"], subject_type="AGENT", agent_id=ids["ag1"]),
            "read",
            _order(ids["res2"], ids["t1"], ids["s2"]),
            tenant_id=ids["t1"],
            space_id=ids["s2"],
        )
    )
    assert decision.effect == "DENY"


def test_an_agent_from_another_tenant_is_denied(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(
            Subject(identity_id=ids["u_ok"], subject_type="AGENT", agent_id=ids["ag_t2"]),
            "read",
            _order(ids["res1"], ids["t1"], ids["s1"]),
            tenant_id=ids["t1"],
            space_id=ids["s1"],
        )
    )
    assert decision.effect == "DENY"


def test_a_disabled_agent_is_denied(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(
            Subject(identity_id=ids["u_ok"], subject_type="AGENT", agent_id=ids["ag_off"]),
            "read",
            _order(ids["res1"], ids["t1"], ids["s1"]),
            tenant_id=ids["t1"],
            space_id=ids["s1"],
        )
    )
    assert decision.effect == "DENY"


def test_an_agent_cannot_exceed_its_risk_ceiling(env) -> None:
    engine, ids = env
    service = _service(engine)
    decision = service.authorize(
        _request(
            Subject(identity_id=ids["u_ok"], subject_type="AGENT", agent_id=ids["ag_lowrisk"]),
            "read",
            _order(ids["res1"], ids["t1"], ids["s1"]),
            tenant_id=ids["t1"],
            space_id=ids["s1"],
            risk_level="CRITICAL",
        )
    )
    assert decision.effect == "DENY"
    assert decision.reason == "risk-ceiling-exceeded"


# --------------------------------------------------------------------------- #
# tool boundary
# --------------------------------------------------------------------------- #
def test_a_tool_without_a_structured_grant_is_never_allowed(env) -> None:
    """HIGH risk with no grant is *held*, not permitted.

    The frozen algorithm tests the approval requirement before it tests for any
    allow, so a high-risk action with no grant reports ``REQUIRES_APPROVAL``
    rather than ``DENY``. Either way it is not an allow — approval is never a
    grant, and the action stays blocked.
    """
    engine, ids = env
    gate = ToolGate(_service(engine), AuthorizationRepository(engine))
    decision = gate.authorize(
        tool_id=ids["tool_highrisk"],
        subject=Subject(identity_id=ids["u_ok"]),
        action=Action("execute"),
        resource=_order(ids["res5"], ids["t1"]),
        tenant_id=ids["t1"],
    )
    assert decision.effect == "REQUIRES_APPROVAL"
    assert decision.allowed is False


def test_a_low_risk_tool_without_a_grant_is_denied(env) -> None:
    engine, ids = env
    gate = ToolGate(_service(engine), AuthorizationRepository(engine))
    decision = gate.authorize(
        tool_id=ids["tool_ok"],
        subject=Subject(identity_id=ids["u_acl"]),
        action=Action("execute"),
        resource=_order(ids["res5"], ids["t1"]),
        tenant_id=ids["t1"],
    )
    assert decision.effect == "DENY"


def test_a_disabled_tool_is_denied(env) -> None:
    engine, ids = env
    gate = ToolGate(_service(engine), AuthorizationRepository(engine))
    decision = gate.authorize(
        tool_id=ids["tool_disabled"],
        subject=Subject(identity_id=ids["u_ok"]),
        action=Action("execute"),
        resource=_order(ids["res5"], ids["t1"]),
        tenant_id=ids["t1"],
    )
    assert decision.effect == "DENY"
    assert decision.reason == "tool-disabled"


def test_a_tool_that_requires_approval_holds_the_action(env) -> None:
    engine, ids = env
    gate = ToolGate(_service(engine), AuthorizationRepository(engine))
    decision = gate.authorize(
        tool_id=ids["tool_approval"],
        subject=Subject(identity_id=ids["u_ok"]),
        action=Action("execute"),
        resource=_order(ids["res5"], ids["t1"]),
        tenant_id=ids["t1"],
    )
    assert decision.effect in {"DENY", "REQUIRES_APPROVAL"}
    assert decision.effect != "ALLOW"


def test_a_tool_from_another_tenant_is_denied(env) -> None:
    engine, ids = env
    gate = ToolGate(_service(engine), AuthorizationRepository(engine))
    decision = gate.authorize(
        tool_id=ids["tool_ok"],
        subject=Subject(identity_id=ids["u_ok"]),
        action=Action("execute"),
        resource=_order(ids["res5"], ids["t1"]),
        tenant_id=ids["t2"],
    )
    assert decision.effect == "DENY"


def test_an_unknown_tool_is_denied(env) -> None:
    engine, ids = env
    gate = ToolGate(_service(engine), AuthorizationRepository(engine))
    decision = gate.authorize(
        tool_id="00000000-0000-0000-0000-000000000000",
        subject=Subject(identity_id=ids["u_ok"]),
        action=Action("execute"),
        resource=_order(ids["res5"], ids["t1"]),
        tenant_id=ids["t1"],
    )
    assert decision.effect == "DENY"
    assert decision.reason == "unknown-tool"


# --------------------------------------------------------------------------- #
# audit and determinism
# --------------------------------------------------------------------------- #
def test_every_decision_is_recorded_on_the_audit_boundary(env) -> None:
    engine, ids = env
    service = _service(engine)
    service.authorize(
        _request(Subject(identity_id=ids["u_ok"]), "read", _order(ids["res5"], ids["t1"]), tenant_id=ids["t1"])
    )
    events = service.audit_boundary.recent()
    assert len(events) == 1
    assert events[0].decision in {"ALLOW", "DENY", "REQUIRES_APPROVAL"}
    assert events[0].id[14] == "7"


def test_repeated_evaluation_is_deterministic(env) -> None:
    engine, ids = env
    service = _service(engine)
    request = _request(
        Subject(identity_id=ids["u_ok"]), "read", _order(ids["res5"], ids["t1"]), tenant_id=ids["t1"]
    )
    results = {service.authorize(request).effect for _ in range(5)}
    assert len(results) == 1


def test_no_decision_cache_exists_between_calls(env) -> None:
    """A revocation must take effect immediately: nothing is cached."""
    engine, ids = env
    _require_acl(ids)
    service = _service(engine)
    before = service.authorize(
        _request(Subject(identity_id=ids["u_acl"]), "read", _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert before.effect == "ALLOW"

    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "DELETE FROM resource_permissions WHERE resource_id = :r AND subject_id = :s"
            ),
            {"r": ids["res2"], "s": ids["u_acl"]},
        )

    after = service.authorize(
        _request(Subject(identity_id=ids["u_acl"]), "read", _order(ids["res2"], ids["t1"]), tenant_id=ids["t1"])
    )
    assert after.effect == "DENY"
