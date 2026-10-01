"""P16 full-chain integration on a real database (F-P16-I-01 / F-P16-I-02).

Uses a dedicated database ``uap_p16_test`` migrated to head, so the frozen
``uap_b1_test`` baseline is never touched. DB state, authorization and the tool
execution ledger are real rows; only the provider transport is stubbed.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from core.agent import ErrorCode
from infrastructure.ai.adapters import EchoAdapter, OpenAICompatibleAdapter
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from intelligence.providers.interfaces import ProviderRegistry
from services.agent.authorizer import P09ActorAuthorizer
from services.agent.repository import AgentRuntimeRepository
from services.agent.runtime import AgentRuntimeService, RunLimits
from services.agent.tool_authorization import ToolAuthorizationFacade
from services.agent.tools import ToolExecutor, ToolRegistry, register_builtin_tools
from services.ai.credentials import EnvSecretResolver
from scripts.privileges import materialize as materialize_baseline_privileges

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P16_DB = "uap_p16_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P16_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P16_DB}"
TOOL_KEY = "platform.clock.now"


@pytest.fixture(scope="module")
def engine():
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P16_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{P16_DB}" OWNER uap_migrator'))
    admin.dispose()

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{P16_DB}"
    cfg.attributes["lock_mode"] = "wait"
    command.upgrade(cfg, "head")

    fixtures = sa.create_engine(FIXTURE_DSN)
    # Official, versioned baseline privilege materialization (P16-D15).
    # The fixture never carries its own GRANT list.
    materialize_baseline_privileges(fixtures)
    yield fixtures
    fixtures.dispose()


def _seed(
    engine,
    *,
    acl: str = "allow",
    tool_enabled: bool = True,
    adapter: str = "echo",
    secret_ref: str | None = None,
) -> dict[str, str]:
    ids = {name: str(uuid.uuid4()) for name in (
        "tenant", "tenant_b", "user", "agent", "version", "tool", "tool_version",
        "provider", "model", "route", "policy", "resource", "acl",
    )}
    ids["tool_key"] = TOOL_KEY
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO tenants (id, slug, display_name, status) VALUES"
            " (CAST(:t AS uuid), :slug, :name, 'active'), (CAST(:tb AS uuid), :slugb, :nameb, 'active')"
        ), {"t": ids["tenant"], "slug": f"p16-{ids['tenant'][:8]}", "name": "P16 A",
            "tb": ids["tenant_b"], "slugb": f"p16b-{ids['tenant_b'][:8]}", "nameb": "P16 B"})
        conn.execute(sa.text(
            "INSERT INTO users (id, email, status) VALUES (CAST(:u AS uuid), :email, 'active')"
        ), {"u": ids["user"], "email": f"p16-{ids['user'][:8]}@example.invalid"})
        conn.execute(sa.text(
            "INSERT INTO resources (id, tenant_id, resource_type, classification, status)"
            " VALUES (CAST(:r AS uuid), CAST(:t AS uuid), 'agent', 'INTERNAL', 'active')"
        ), {"r": ids["agent"], "t": ids["tenant"]})
        conn.execute(sa.text(
            "INSERT INTO resource_permissions (id, resource_id, subject_type_id, subject_id, action, effect)"
            " SELECT CAST(:id AS uuid), CAST(:r AS uuid), ast.id, CAST(:u AS uuid), 'execute', :effect"
            " FROM acl_subject_types ast WHERE ast.key = 'user'"
        ), {"id": ids["acl"], "r": ids["agent"], "u": ids["user"], "effect": acl})
        conn.execute(sa.text(
            "INSERT INTO agents (id, tenant_id, owner_id, key, name, status, max_risk_level, config)"
            " VALUES (CAST(:a AS uuid), CAST(:t AS uuid), CAST(:u AS uuid), :key, 'P16 Agent',"
            " 'active', 'LOW', '{}'::jsonb)"
        ), {"a": ids["agent"], "t": ids["tenant"], "u": ids["user"], "key": f"p16-{ids['agent'][:8]}"})
        conn.execute(sa.text(
            "INSERT INTO agent_versions (id, agent_id, version, definition, allowed_tools, checksum, status)"
            " VALUES (CAST(:v AS uuid), CAST(:a AS uuid), 1,"
            " '{\"capability\": \"chat\", \"classification\": \"INTERNAL\"}'::jsonb,"
            " '[]'::jsonb, 'checksum', 'published')"
        ), {"v": ids["version"], "a": ids["agent"]})
        conn.execute(sa.text(
            "UPDATE agents SET current_version_id = CAST(:v AS uuid) WHERE id = CAST(:a AS uuid)"
        ), {"v": ids["version"], "a": ids["agent"]})
        conn.execute(sa.text(
            "INSERT INTO tools (id, tenant_id, key, name, risk_level, timeout_ms, idempotency_mode,"
            " audit_policy, approval_required, enabled) VALUES"
            " (CAST(:tool AS uuid), CAST(:t AS uuid), :key, 'Clock', 'LOW', 1000, 'natural_key',"
            " 'full', false, :enabled)"
        ), {"tool": ids["tool"], "t": ids["tenant"], "key": TOOL_KEY, "enabled": tool_enabled})
        conn.execute(sa.text(
            "INSERT INTO tool_versions (id, tool_id, version, input_schema, output_schema, risk_level,"
            " timeout_ms, handler_ref, checksum, status) VALUES (CAST(:tv AS uuid), CAST(:tool AS uuid), 1,"
            " '{}'::jsonb, '{}'::jsonb, 'LOW', 1000, :handler, 'checksum', 'published')"
        ), {"tv": ids["tool_version"], "tool": ids["tool"], "handler": TOOL_KEY})
        # The canonical ToolGate resolves the *tool* as a resource, so the fixture
        # must carry the tool's resource row and its ACL entry as well.
        conn.execute(sa.text(
            "INSERT INTO resources (id, tenant_id, resource_type, classification, status)"
            " VALUES (CAST(:tool AS uuid), CAST(:t AS uuid), 'tool', 'INTERNAL', 'active')"
        ), {"tool": ids["tool"], "t": ids["tenant"]})
        conn.execute(sa.text(
            "INSERT INTO resource_permissions (id, resource_id, subject_type_id, subject_id, action, effect)"
            " SELECT gen_random_uuid(), CAST(:tool AS uuid), ast.id, CAST(:u AS uuid), 'execute', 'allow'"
            " FROM acl_subject_types ast WHERE ast.key = 'user'"
        ), {"tool": ids["tool"], "u": ids["user"]})
        conn.execute(sa.text(
            "INSERT INTO agent_permissions (id, agent_id, tool_id, effect) VALUES"
            " (gen_random_uuid(), CAST(:a AS uuid), CAST(:tool AS uuid), 'allow')"
        ), {"a": ids["agent"], "tool": ids["tool"]})
        conn.execute(sa.text(
            "INSERT INTO ai_providers (id, key, adapter, base_url, enabled, health_status, privacy_tier,"
            " max_classification, capabilities, secret_ref) VALUES (CAST(:p AS uuid), :key, :adapter,"
            " 'http://provider.invalid', true, 'healthy', 'private', 'CONFIDENTIAL', '{\"chat\": true}'::jsonb, :secret)"
        ), {"p": ids["provider"], "key": f"p16p-{ids['provider'][:8]}", "adapter": adapter,
            "secret": secret_ref})
        conn.execute(sa.text(
            "INSERT INTO ai_models (id, provider_id, model_key, capabilities, context_window,"
            " max_classification, is_private, enabled) VALUES (CAST(:m AS uuid), CAST(:p AS uuid),"
            " 'echo-1', '{\"chat\": true}'::jsonb, 8000, 'CONFIDENTIAL', true, true)"
        ), {"m": ids["model"], "p": ids["provider"]})
        conn.execute(sa.text(
            "INSERT INTO ai_routes (id, tenant_id, capability, priority, primary_model_id, enabled)"
            " VALUES (CAST(:r AS uuid), CAST(:t AS uuid), 'chat', 1, CAST(:m AS uuid), true)"
        ), {"r": ids["route"], "m": ids["model"], "t": ids["tenant"]})
        conn.execute(sa.text(
            "INSERT INTO ai_policies (id, tenant_id, name, max_classification, require_private,"
            " allow_fallback, fallback_preserves_classification, enabled) VALUES"
            " (CAST(:pol AS uuid), CAST(:t AS uuid), 'p16-default', 'CONFIDENTIAL', false, false,"
            " true, true)"
        ), {"pol": ids["policy"], "t": ids["tenant"]})
    return ids


def _runtime(registry: ProviderRegistry, *, environ: dict[str, str] | None = None):
    database = RuntimeDatabase.from_config(DatabaseConfig(url=RUNTIME_DSN), require_role="uap_runtime")
    database.start()
    tools = register_builtin_tools(ToolRegistry())
    service = AgentRuntimeService(
        database=database,
        registry=registry,
        credentials=EnvSecretResolver(environ if environ is not None else {}),
        repository=AgentRuntimeRepository(),
        tools=tools,
        executor=ToolExecutor(tools),
        authorizer=P09ActorAuthorizer.from_engine(database.engine),
        tool_authorization=ToolAuthorizationFacade.from_engine(database.engine),
        limits=RunLimits(max_tool_calls=2, max_runtime_seconds=30.0, tool_timeout_seconds=2.0),
    )
    return database, service


def _stub_registry(adapter: str, **kwargs) -> ProviderRegistry:
    registry = ProviderRegistry()
    if adapter == "echo":
        registry.register("echo", EchoAdapter(proposal={"key": TOOL_KEY, "params": {}}, **kwargs))
    else:
        registry.register("openai_compatible", OpenAICompatibleAdapter(**kwargs))
    return registry


def _rows(engine, sql: str, **params):
    with engine.begin() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


def test_full_chain_allow_records_run_request_tool_and_audit(engine) -> None:
    ids = _seed(engine)
    database, service = _runtime(_stub_registry("echo"))
    try:
        outcome = service.run(
            agent_id=ids["agent"], actor_type="USER", actor_id=ids["user"],
            tenant_id=ids["tenant"], input_text="hello p16",
        )
    finally:
        database.dispose()

    assert outcome.status == "COMPLETED", outcome.failure_code
    run = _rows(engine, "SELECT * FROM agent_runs WHERE id = CAST(:id AS uuid)", id=outcome.run_id)[0]
    assert run["tenant_id"] == uuid.UUID(ids["tenant"])
    assert run["agent_id"] == uuid.UUID(ids["agent"])
    assert run["agent_version_id"] == uuid.UUID(ids["version"])
    assert run["actor_id"] == uuid.UUID(ids["user"])
    assert run["status"] == "COMPLETED" and run["tool_calls"] == 1

    logs = _rows(engine, "SELECT * FROM ai_request_logs WHERE run_id = CAST(:id AS uuid)", id=outcome.run_id)
    assert len(logs) == 1
    log = logs[0]
    assert log["provider_id"] == uuid.UUID(ids["provider"]) and log["model_id"] == uuid.UUID(ids["model"])
    assert log["agent_id"] == uuid.UUID(ids["agent"]) and log["actor_id"] == uuid.UUID(ids["user"])
    assert log["status"] == "succeeded"

    executions = _rows(engine, "SELECT * FROM tool_executions WHERE run_id = CAST(:id AS uuid)", id=outcome.run_id)
    assert len(executions) == 1
    exec_row = executions[0]
    assert exec_row["tool_id"] == uuid.UUID(ids["tool"])
    assert exec_row["tool_version_id"] == uuid.UUID(ids["tool_version"])
    assert exec_row["agent_id"] == uuid.UUID(ids["agent"])
    assert exec_row["tenant_id"] == uuid.UUID(ids["tenant"])
    assert exec_row["status"] == "succeeded"

    audits = _rows(engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:id AS uuid)", id=outcome.run_id)
    assert len(audits) >= 1
    assert audits[0]["actor_id"] == uuid.UUID(ids["user"])
    assert audits[0]["result"] == "success"


def test_acl_deny_fails_the_run_without_tool_execution(engine) -> None:
    ids = _seed(engine, acl="deny")
    database, service = _runtime(_stub_registry("echo"))
    try:
        outcome = service.run(
            agent_id=ids["agent"], actor_type="USER", actor_id=ids["user"],
            tenant_id=ids["tenant"], input_text="denied",
        )
    finally:
        database.dispose()
    assert outcome.status == "FAILED" and outcome.failure_code == ErrorCode.AUTHORIZATION_DENIED
    assert _rows(engine, "SELECT * FROM tool_executions WHERE run_id = CAST(:id AS uuid)", id=outcome.run_id) == []


def test_cross_tenant_run_is_denied(engine) -> None:
    ids = _seed(engine)
    database, service = _runtime(_stub_registry("echo"))
    try:
        outcome = service.run(
            agent_id=ids["agent"], actor_type="USER", actor_id=ids["user"],
            tenant_id=ids["tenant_b"], input_text="cross tenant",
        )
    finally:
        database.dispose()
    assert outcome.status == "FAILED" and outcome.failure_code == ErrorCode.AUTHORIZATION_DENIED


def test_disabled_tool_is_denied_by_the_gate(engine) -> None:
    ids = _seed(engine, tool_enabled=False)
    database, service = _runtime(_stub_registry("echo"))
    try:
        outcome = service.run(
            agent_id=ids["agent"], actor_type="USER", actor_id=ids["user"],
            tenant_id=ids["tenant"], input_text="tool disabled",
        )
    finally:
        database.dispose()
    assert outcome.status == "FAILED" and outcome.failure_code == ErrorCode.TOOL_DISABLED
    assert _rows(engine, "SELECT * FROM tool_executions WHERE run_id = CAST(:id AS uuid)", id=outcome.run_id) == []


def test_missing_credential_fails_closed_without_leak(engine) -> None:
    ids = _seed(engine, secret_ref="env:P16_ABSENT_SECRET")
    database, service = _runtime(_stub_registry("echo"), environ={})
    try:
        outcome = service.run(
            agent_id=ids["agent"], actor_type="USER", actor_id=ids["user"],
            tenant_id=ids["tenant"], input_text="credential",
        )
    finally:
        database.dispose()
    assert outcome.status == "FAILED" and outcome.failure_code == ErrorCode.CREDENTIAL_UNAVAILABLE
    run = _rows(engine, "SELECT * FROM agent_runs WHERE id = CAST(:id AS uuid)", id=outcome.run_id)[0]
    assert "P16_ABSENT_SECRET" not in str(run["failure_metadata"])


def test_provider_transport_failure_is_a_safe_model_failure(engine) -> None:
    ids = _seed(engine, adapter="openai_compatible")

    def _boom(url, headers, payload):
        raise ConnectionError("transport down")

    database, service = _runtime(_stub_registry("openai_compatible", transport=_boom))
    try:
        outcome = service.run(
            agent_id=ids["agent"], actor_type="USER", actor_id=ids["user"],
            tenant_id=ids["tenant"], input_text="provider failure",
        )
    finally:
        database.dispose()
    assert outcome.status == "FAILED" and outcome.failure_code == ErrorCode.MODEL_REQUEST_FAILED
    assert _rows(engine, "SELECT * FROM tool_executions WHERE run_id = CAST(:id AS uuid)", id=outcome.run_id) == []
