"""Tool authorization facade (P16-D06 / I-03).

The runtime must not re-implement authorization. This facade is a thin
delegation to the canonical :class:`~services.authorization.tools.ToolGate`:
it adds nothing but the mapping from a ``Decision`` to the frozen error code,
so there is exactly one authorization path.
"""

from __future__ import annotations

import re
from typing import Any

from core.agent import AgentRuntimeError, ErrorCode
from core.permission import Action, Subject
from core.resource import ResourceRef
from services.authorization import ToolGate

#: Decision reason -> frozen runtime error code (closed mapping).
_REASONS: dict[str, str] = {
    "unknown-tool": ErrorCode.TOOL_NOT_FOUND,
    "tool-disabled": ErrorCode.TOOL_DISABLED,
    "tool-deny": ErrorCode.TOOL_UNAUTHORIZED,
    "agent-deny": ErrorCode.TOOL_UNAUTHORIZED,
    "agent-no-grant": ErrorCode.TOOL_UNAUTHORIZED,
    "cross-tenant-tool": ErrorCode.TOOL_UNAUTHORIZED,
    "scope-denied": ErrorCode.TOOL_SCOPE_DENIED,
}

#: Denial layer -> stable machine-readable evidence code (never raw text or SQL).
_LAYERS: dict[str, str] = {
    "unknown-tool": "TOOL_NOT_FOUND",
    "tool-disabled": "TOOL_DISABLED",
    "tool-deny": "TOOL_PERMISSION_DENIED",
    "agent-deny": "AGENT_PERMISSION_DENIED",
    "agent-no-grant": "AGENT_PERMISSION_DENIED",
    "cross-tenant-tool": "TENANT_SCOPE_DENIED",
    "cross-tenant": "TENANT_SCOPE_DENIED",
    "resource": "RESOURCE_UNRESOLVED",
    "subject": "SUBJECT_UNRESOLVED",
    "authorization-unavailable": "AUTHORIZATION_UNAVAILABLE",
    "approval-required": "APPROVAL_REQUIRED",
}


def _safe_reason(reason: str) -> str:
    """Reduce a ToolGate reason to a code: no message text, no SQL, no secrets."""
    layer = reason.split(":", 1)[0].strip()
    if layer in _LAYERS:
        return _LAYERS[layer]
    if re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", layer):
        return layer.upper().replace("-", "_")
    return "DENIED"


class ToolAuthorizationFacade:
    """Delegate every tool authorization question to ``ToolGate``."""

    def __init__(self, gate: ToolGate) -> None:
        self._gate = gate

    @classmethod
    def from_engine(cls, engine: Any) -> "ToolAuthorizationFacade":
        from services.authorization import AuthorizationRepository, AuthorizationService

        # The gate must query through the *runtime* engine. A gate constructed without
        # an explicit repository falls back to the process-global engine, i.e. the
        # authorization query would run against the wrong database.
        repository = AuthorizationRepository(engine)
        return cls(
            ToolGate(
                AuthorizationService(engine=engine, repository=repository),
                repository=repository,
            )
        )

    def authorize(
        self,
        *,
        tool_id: str,
        agent_id: str,
        actor_id: str,
        actor_type: str,
        tenant_id: str,
        space_id: str | None,
        request_id: str | None = None,
        scope: str | None = None,
    ) -> None:
        """Raise the frozen error code when the gate does not allow."""
        decision = self._gate.authorize(
            tool_id=tool_id,
            subject=Subject(
                identity_id=actor_id,
                subject_type=actor_type,
                tenant_id=tenant_id,
                actor_id=actor_id,
            ),
            action=Action(name="execute", resource_type="tool"),
            resource=ResourceRef(
                type="tool",
                id=tool_id,
                tenant_id=tenant_id,
                space_id=space_id,
            ),
            tenant_id=tenant_id,
            space_id=space_id,
            scope=scope,
            request_id=request_id,
            agent_id=agent_id,
        )
        if decision.effect == "ALLOW":
            return
        # Safe diagnostic evidence: a machine-readable denial layer, never the raw
        # ToolGate message (which may embed SQL or infrastructure text).
        raw_reason = str(decision.reason)
        reason_code = _safe_reason(raw_reason)
        if decision.effect == "REQUIRES_APPROVAL":
            error = AgentRuntimeError(ErrorCode.TOOL_APPROVAL_REQUIRED, "tool requires approval")
        else:
            error = AgentRuntimeError(
                _REASONS.get(raw_reason, ErrorCode.TOOL_UNAUTHORIZED), "tool authorization denied"
            )
        error.decision_reason = reason_code  # type: ignore[attr-defined]
        raise error
