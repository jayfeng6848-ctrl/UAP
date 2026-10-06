"""P16 use-cases (transaction owners) for the API layer (§18).

Handlers stay transport-only: everything below is built here, including the
runtime, its authorizer and the tool registry.
"""

from __future__ import annotations

from typing import Any

from intelligence.providers.interfaces import ProviderRegistry
from sqlalchemy import text

from services.ai.credentials import EnvSecretResolver
from services.ai.connection import connection_store
from services.ai.credentials import ConnectionSecretResolver

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


def build_tool_registry(db: Any | None = None) -> ToolRegistry:
    """Built-in tools. Passing the runtime database also enables the read-only
    Company qualification tool (HD-P21-14 §8); without it the registry is exactly
    what it was before."""
    return register_builtin_tools(ToolRegistry(), company_db=db)


def build_runtime(
    db: Any,
    *,
    limits: RunLimits | None = None,
    actor_id: str | None = None,
    tenant_id: str | None = None,
) -> AgentRuntimeService:
    tools = build_tool_registry(db)
    # HD-P21-17 §9/§21: when the caller's scope is known, the credential resolver is
    # bound to (actor, tenant) so a customer-injected key can only satisfy that
    # actor's runs in that tenant. Without a scope the resolver is exactly the
    # previous environment resolver.
    credentials = (
        ConnectionSecretResolver(
            actor_id=actor_id,
            tenant_id=tenant_id,
            store=connection_store,
            fallback=EnvSecretResolver(),
        )
        if actor_id and tenant_id
        else EnvSecretResolver()
    )
    return AgentRuntimeService(
        database=db,
        registry=build_provider_registry(),
        credentials=credentials,
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
    # P18-D14 admission gate (additive): an agent may only run inside an ACTIVE
    # tenant/space. Active scope keeps the P16 behaviour byte-for-byte; an
    # inactive scope is refused before the run is admitted, and the refusal never
    # falls back to an owner/platform scope.
    from core.agent import AgentRuntimeError, ErrorCode
    from services.identity_runtime import IdentityRuntimeError, require_active_agent_scope

    with db.transaction() as session:
        try:
            require_active_agent_scope(
                session, agent_id=agent_id, tenant_id=tenant_id, space_id=space_id
            )
        except IdentityRuntimeError as exc:
            raise AgentRuntimeError(
                ErrorCode.AUTHORIZATION_DENIED, "agent scope lifecycle gate denied"
            ) from exc
    return build_runtime(db, actor_id=actor_id, tenant_id=tenant_id).run(
        agent_id=agent_id,
        actor_type=actor_type,
        actor_id=actor_id,
        tenant_id=tenant_id,
        space_id=space_id,
        input_text=input_text,
        request_id=request_id,
    )


def find_qualification_agent(db: Any, *, tenant_id: str) -> dict[str, Any] | None:
    """Discover the tenant's active, published qualification agent.

    HD-P21-17 §11/§12: the customer never creates or names an agent. The platform
    reuses whatever qualification agent already exists in *this* tenant; a tenant
    without one is a configuration problem, never a silent fallback.
    """
    with db.transaction() as session:
        row = session.execute(
            text(
                "SELECT id, key, name, status FROM agents"
                " WHERE tenant_id = CAST(:t AS uuid) AND status = 'active'"
                "   AND current_version_id IS NOT NULL"
                " ORDER BY created_at ASC LIMIT 1"
            ),
            {"t": tenant_id},
        ).first()
    return dict(row._mapping) if row is not None else None


def load_chat_provider(
    db: Any, *, tenant_id: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return the tenant's enabled chat route as ``(provider_row, model_row)``."""
    with db.transaction() as session:
        route = session.execute(
            text(
                "SELECT primary_model_id FROM ai_routes"
                " WHERE tenant_id = CAST(:t AS uuid) AND capability = 'chat' AND enabled = true"
                " ORDER BY priority ASC LIMIT 1"
            ),
            {"t": tenant_id},
        ).first()
        if route is None:
            return None, None
        model = session.execute(
            text("SELECT * FROM ai_models WHERE id = CAST(:m AS uuid)"), {"m": str(route[0])}
        ).mappings().first()
        if model is None:
            return None, None
        provider = session.execute(
            text("SELECT * FROM ai_providers WHERE id = CAST(:p AS uuid)"),
            {"p": str(model["provider_id"])},
        ).mappings().first()
    return (
        dict(provider) if provider is not None else None,
        dict(model) if model is not None else None,
    )


def load_provider_by_key(
    db: Any, *, provider_key: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return one named provider and its first enabled model (HD-P21-20).

    Provider rows are platform-level descriptors; the customer's choice only picks
    which of the already-provisioned descriptors a run uses.
    """
    with db.transaction() as session:
        provider = session.execute(
            text(
                "SELECT * FROM ai_providers WHERE key = CAST(:k AS text) AND enabled = true"
            ),
            {"k": provider_key},
        ).mappings().first()
        if provider is None:
            return None, None
        model = session.execute(
            text(
                "SELECT * FROM ai_models WHERE provider_id = CAST(:p AS uuid)"
                " AND enabled = true ORDER BY created_at ASC LIMIT 1"
            ),
            {"p": str(provider["id"])},
        ).mappings().first()
    return (
        dict(provider) if provider is not None else None,
        dict(model) if model is not None else None,
    )


def list_provider_models(db: Any, *, provider_key: str) -> list[dict[str, Any]]:
    """The customer-facing model catalog of one cloud provider (HD-P21-AI-04 §6).

    Read-only over the existing ``ai_models``/``ai_providers`` tables: only models
    that belong to the selected, enabled provider and are themselves enabled are
    ever returned. No other provider's model can leak into the list.
    """
    with db.transaction() as session:
        rows = (
            session.execute(
                text(
                    "SELECT m.id, m.model_key, m.display_name, m.context_window,"
                    " m.max_classification, m.is_private"
                    " FROM ai_models m JOIN ai_providers p ON p.id = m.provider_id"
                    " WHERE p.key = CAST(:k AS text) AND p.enabled = true AND m.enabled = true"
                    " ORDER BY m.model_key ASC"
                ),
                {"k": provider_key},
            )
            .mappings()
            .all()
        )
    return [dict(row) for row in rows]


def load_model_by_key(
    db: Any, *, provider_key: str, model_key: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve one explicitly selected ``(provider, model)`` pair.

    Returns ``(provider_row, model_row)`` for a legal pair; ``(provider_row, None)``
    when the provider is fine but the model is not enabled under it. The caller
    decides between ``MODEL_UNAVAILABLE`` and ``MODEL_PROVIDER_MISMATCH`` — this
    function never guesses on the caller's behalf.
    """
    provider, _ = load_provider_by_key(db, provider_key=provider_key)
    if provider is None:
        return None, None
    with db.transaction() as session:
        model = (
            session.execute(
                text(
                    "SELECT * FROM ai_models WHERE provider_id = CAST(:p AS uuid)"
                    " AND model_key = CAST(:m AS text) AND enabled = true LIMIT 1"
                ),
                {"p": str(provider["id"]), "m": str(model_key)},
            )
            .mappings()
            .first()
        )
    return provider, (dict(model) if model is not None else None)


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
