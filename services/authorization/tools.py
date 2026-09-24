"""Tool authorization integration.

A tool is the only controlled exit from an agent to a service, so it is also the
last place where authorization can be enforced. This gate therefore sits in
front of every invocation and composes, rather than replaces, the service:

    Agent -> Authorization -> Policy -> Approval if required -> Tool -> Execution

The tool's own static requirement and the dynamic policy requirement are
combined as an OR: either one is enough to hold the action for a human.
"""

from __future__ import annotations

from core.permission import Action, AuthorizationRequest, Decision, Subject
from core.resource import ResourceRef

from .errors import AuthorizationUnavailable
from .permissions import PermissionResolver
from .policy import approval_required
from .repository import AuthorizationRepository
from .scopes import ScopeEvaluator


class ToolGate:
    """Authorize a tool invocation before it is allowed to execute."""

    def __init__(
        self,
        service,
        repository: AuthorizationRepository | None = None,
        permissions: PermissionResolver | None = None,
        scopes: ScopeEvaluator | None = None,
    ) -> None:
        self._service = service
        self._repository = repository or AuthorizationRepository()
        self._permissions = permissions or PermissionResolver(self._repository)
        self._scopes = scopes or ScopeEvaluator()

    def authorize(
        self,
        *,
        tool_id: str,
        subject: Subject,
        action: Action,
        resource: ResourceRef,
        tenant_id: str | None = None,
        space_id: str | None = None,
        scope: str | None = None,
        request_id: str | None = None,
    ) -> Decision:
        """Deny unless the tool, its grants and the service all agree."""
        try:
            tool = self._repository.get_tool(tool_id)
        except AuthorizationUnavailable as exc:
            return Decision(effect="DENY", reason=f"authorization-unavailable:{exc}")

        if tool is None:
            return Decision(effect="DENY", reason="unknown-tool")
        if not bool(tool._mapping["enabled"]):
            return Decision(effect="DENY", reason="tool-disabled")

        tool_tenant = tool._mapping["tenant_id"]
        if tenant_id is not None and tool_tenant is not None:
            if str(tool_tenant) != tenant_id:
                return Decision(effect="DENY", reason="cross-tenant-tool")

        try:
            grant_rows = self._repository.tool_grants(tool_id)
        except AuthorizationUnavailable as exc:
            return Decision(effect="DENY", reason=f"authorization-unavailable:{exc}")

        tool_outcome = self._permissions.tool(grant_rows, action, resource, scope)
        if tool_outcome.deny:
            return Decision(
                effect="DENY",
                reason="tool-deny",
                matched_rules=tool_outcome.reasons,
            )

        request = AuthorizationRequest(
            subject=subject,
            action=action,
            resource=resource,
            tenant_id=tenant_id if tenant_id is not None else str(tool_tenant or ""),
            space_id=space_id,
            request_id=request_id,
            risk_level=str(tool._mapping["risk_level"]),
        )
        decision = self._service.authorize(request)

        if decision.effect == "DENY":
            return decision

        static_requires = bool(tool._mapping["approval_required"])
        if tool_outcome.allow and decision.effect == "ALLOW":
            decision = Decision(
                effect="ALLOW",
                reason="tool-and-service-granted",
                matched_rules=decision.matched_rules + tool_outcome.reasons,
                policy_version=decision.policy_version,
            )

        if approval_required(
            tool_requires=static_requires,
            policy_requires=decision.effect == "REQUIRES_APPROVAL",
        ):
            return Decision(
                effect="REQUIRES_APPROVAL",
                reason="approval-required",
                matched_rules=decision.matched_rules,
                policy_version=decision.policy_version,
            )

        return decision


__all__ = ["ToolGate"]
