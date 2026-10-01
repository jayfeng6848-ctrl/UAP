"""P16 use-cases (transaction owners) for the API layer (§18).

Handlers stay transport-only: everything below is built here, including the
runtime, its authorizer and the tool registry.
"""

from __future__ import annotations

from typing import Any

from intelligence.providers.interfaces import ProviderRegistry
from sqlalchemy import text

from services.ai.credentials import EnvSecretResolver

from .authorizer import P09ActorAuthorizer
from .repository import AgentRuntimeRepository
from .runtime import AgentRuntimeService, RunLimits, RunOutcome
from .tool_authorization import ToolAuthorizationFacade
from .tools import ToolExecutor, ToolRegistry, register_builtin_tools

SAFE_RUN_FIELDS = (
    "id, tenant_id, space_id, agent_id, agent_version_id, status, tool_calls, "
    "result_digest, result_metadata, failure_code, created_at, started_at, completed_at"
)


def build_provider_registry() -> ProviderRegistry:
    from infrastructure.ai.adapters import register_default_adapters

    return register_default_adapters(ProviderRegistry())


def build_tool_registry() -> ToolRegistry:
    return register_builtin_tools(ToolRegistry())


def build_runtime(db: Any, *, limits: RunLimits | None = None) -> AgentRuntimeService:
    tools = build_tool_registry()
    return AgentRuntimeService(
        database=db,
        registry=build_provider_registry(),
        credentials=EnvSecretResolver(),
        repository=AgentRuntimeRepository(),
        tools=tools,
        executor=ToolExecutor(tools),
        authorizer=P09ActorAuthorizer.from_engine(db.engine),
        tool_authorization=ToolAuthorizationFacade.from_engine(db.engine),
        limits=limits or RunLimits(),
    )


def run_agent(
    db: Any,
    *,
    agent_id: str,
    actor_type: str,
    actor_id: str,
    tenant_id: str,
    space_id: str | None,
    input_text: str,
    request_id: str | None = None,
) -> RunOutcome:
    return build_runtime(db).run(
        agent_id=agent_id,
        actor_type=actor_type,
        actor_id=actor_id,
        tenant_id=tenant_id,
        space_id=space_id,
        input_text=input_text,
        request_id=request_id,
    )


def read_agent_run(db: Any, *, run_id: str, tenant_id: str) -> dict[str, Any] | None:
    """Read one ledger row, scoped to the caller's tenant (no cross-tenant reads)."""
    with db.transaction() as session:
        row = session.execute(
            text(
                f"SELECT {SAFE_RUN_FIELDS} FROM agent_runs "
                "WHERE id = CAST(:id AS uuid) AND tenant_id = CAST(:tenant AS uuid)"
            ),
            {"id": run_id, "tenant": tenant_id},
        ).one_or_none()
    return dict(row._mapping) if row is not None else None
