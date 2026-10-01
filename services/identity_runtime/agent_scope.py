"""P17 WAVE 6 — agent scope resolution on top of the P17 context resolver.

P16 froze ``Agent ≠ User`` and ``Actor authorization AND Agent authorization``.
This module adds nothing to that contract: it only lets an agent execution be
described in P17 terms, so a future runtime can consume the shared resolver.

Rules (P17-AUTH §48/§49/§50, P17-D08 = B):

* ``agent tenant = agents.tenant_id`` — never the requester's, never the
  owner's, never a default;
* ``agent space  = agents.space_id``; when it is set, the runtime space must be
  exactly that space;
* the owner is carried as context only — it is never a source of authority.

The agent row is read tenant-scoped (the P16 lesson: a lookup without a tenant
predicate is a cross-tenant defect).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .errors import ErrorCode, IdentityRuntimeError
from .resolver import ResolvedContext, RuntimeContextResolver

_ACTIVE = "active"


class AgentScopeRepository:
    """Tenant-scoped agent binding reads (no id-only lookup)."""

    def get_agent(self, session: Session, *, agent_id: str, tenant_id: str) -> dict | None:
        from sqlalchemy import text

        row = session.execute(
            text(
                "SELECT id, tenant_id, space_id, owner_id, status FROM agents"
                " WHERE id = CAST(:agent AS uuid) AND tenant_id = CAST(:tenant AS uuid)"
            ),
            {"agent": agent_id, "tenant": tenant_id},
        ).one_or_none()
        return dict(row._mapping) if row is not None else None

    def tenant_status(self, session: Session, *, tenant_id: str) -> str | None:
        from sqlalchemy import text

        row = session.execute(
            text("SELECT status FROM tenants WHERE id = CAST(:t AS uuid)"),
            {"t": tenant_id},
        ).one_or_none()
        return str(row[0]) if row is not None else None

    def space_status(self, session: Session, *, tenant_id: str, space_id: str) -> str | None:
        from sqlalchemy import text

        row = session.execute(
            text(
                "SELECT status FROM spaces WHERE id = CAST(:s AS uuid)"
                " AND tenant_id = CAST(:t AS uuid)"
            ),
            {"s": space_id, "t": tenant_id},
        ).one_or_none()
        return str(row[0]) if row is not None else None


@dataclass(frozen=True)
class AgentBinding:
    """The agent's own scope facts. Carries no capability and no verdict."""

    agent_id: str
    tenant_id: str
    space_id: str | None
    owner_id: str


class AgentScopeResolver:
    """Resolve the agent binding for one execution request."""

    def __init__(self, *, repository: AgentScopeRepository | None = None) -> None:
        self._agents = repository or AgentScopeRepository()

    def resolve(
        self,
        session: Session,
        *,
        agent_id: str,
        tenant_id: str,
        space_id: str | None = None,
    ) -> AgentBinding:
        row = self._agents.get_agent(session, agent_id=agent_id, tenant_id=tenant_id)
        if row is None or str(row.get("status")) != _ACTIVE:
            raise IdentityRuntimeError(ErrorCode.AGENT_SCOPE_DENIED, "agent is not in this tenant")
        agent_space = str(row["space_id"]) if row.get("space_id") else None
        if agent_space is not None and agent_space != space_id:
            raise IdentityRuntimeError(
                ErrorCode.AGENT_SPACE_SCOPE_DENIED, "agent is bound to another space"
            )
        return AgentBinding(
            agent_id=str(row["id"]),
            tenant_id=str(row["tenant_id"]),
            space_id=agent_space,
            owner_id=str(row["owner_id"]),
        )


def resolve_agent_execution_context(
    session: Session,
    *,
    actor_id: str,
    agent_id: str,
    actor_type: str = "USER",
    tenant_id: str,
    space_id: str | None = None,
    context_resolver: RuntimeContextResolver | None = None,
    agent_resolver: AgentScopeResolver | None = None,
) -> tuple[ResolvedContext, AgentBinding]:
    """Resolve the actor context **and** the agent binding for one execution.

    The actor must hold a valid membership context (P17 WAVE 2), and the agent
    must be bound to that same tenant (and to that exact space when it is
    space-scoped). Ownership never substitutes for either.
    """
    context = (context_resolver or RuntimeContextResolver()).resolve(
        session, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, space_id=space_id
    )
    binding = (agent_resolver or AgentScopeResolver()).resolve(
        session, agent_id=agent_id, tenant_id=context.tenant_id, space_id=context.space_id
    )
    return context, binding


#: Lifecycle states that may admit an ordinary runtime operation (P18-D14).
ACTIVE_STATE = "active"


def require_active_agent_scope(
    session: Session,
    *,
    agent_id: str,
    tenant_id: str,
    space_id: str | None = None,
    resolver: AgentScopeResolver | None = None,
    repository: AgentScopeRepository | None = None,
) -> AgentBinding:
    """P18-D14 gate: an agent may only run inside an ACTIVE tenant/space.

    Reuses the P17 agent-scope resolution (tenant-scoped agent lookup + space
    binding) and adds the lifecycle condition. An inactive tenant (or an inactive
    bound space) is a denial — it never becomes an agent-run admission, and it
    never falls back to a platform or owner scope.
    """
    binding = (resolver or AgentScopeResolver()).resolve(
        session, agent_id=agent_id, tenant_id=tenant_id, space_id=space_id
    )
    repo = repository or AgentScopeRepository()
    if repo.tenant_status(session, tenant_id=binding.tenant_id) != ACTIVE_STATE:
        raise IdentityRuntimeError(ErrorCode.TENANT_NOT_ACTIVE, "tenant is not active")
    if binding.space_id is not None:
        if repo.space_status(
            session, tenant_id=binding.tenant_id, space_id=binding.space_id
        ) != ACTIVE_STATE:
            raise IdentityRuntimeError(ErrorCode.SPACE_NOT_ACTIVE, "space is not active")
    return binding


__all__ = [
    "AgentBinding",
    "AgentScopeRepository",
    "AgentScopeResolver",
    "require_active_agent_scope",
    "resolve_agent_execution_context",
]
