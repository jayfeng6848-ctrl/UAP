"""The authorization service.

One entry point, one algorithm, one answer. Every failure mode — unknown
subject, unknown resource, non-canonical action, a cross-tenant attempt, a
policy failure or an infrastructure error — resolves to a denial. There is no
code path in this module that can turn a failure into an allow, and there is
deliberately no cache: a stale allow is a security hole, and caching is deferred
until a real traffic model exists.
"""

from __future__ import annotations

from core.permission import Action, AuthorizationRequest, Decision, Subject
from core.permission.decision import combine
from core.resource import ResourceRef
from core.permission.vocabulary import is_risk_level, risk_rank
from sqlalchemy import Engine

from .actions import ActionResolver
from .audit import AuditBoundary
from .errors import (
    ActionResolutionError,
    AuthorizationUnavailable,
    ResourceResolutionError,
    SubjectResolutionError,
)
from .permissions import PermissionResolver
from .policy import PolicyEngine
from .repository import AuthorizationRepository
from .resources import ResourceResolver
from .scopes import ScopeEvaluator
from .subjects import SubjectResolver


class AuthorizationService:
    """Decide whether a subject may act on a resource."""

    def __init__(
        self,
        repository: AuthorizationRepository | None = None,
        *,
        engine: Engine | None = None,
        policy: PolicyEngine | None = None,
        audit: AuditBoundary | None = None,
        actions: ActionResolver | None = None,
        scopes: ScopeEvaluator | None = None,
        permissions: PermissionResolver | None = None,
    ) -> None:
        self._repository = repository or AuthorizationRepository(engine)
        self._actions = actions or ActionResolver()
        self._scopes = scopes or ScopeEvaluator()
        self._permissions = permissions or PermissionResolver(self._repository)
        self._subjects = SubjectResolver(self._repository)
        self._resources = ResourceResolver(self._repository)
        self._policy = policy or PolicyEngine()
        self._audit = audit or AuditBoundary()

    # ---------------------------------------------------------------- public
    def authorize(self, request: AuthorizationRequest) -> Decision:
        """Evaluate one request. Never raises; every failure denies."""
        actor_id = request.subject.actor_id or request.subject.identity_id

        try:
            action = self._actions.resolve(request.action, request.resource.type)
        except ActionResolutionError as exc:
            return self._finish(request, action_name="", decision=_deny(f"non-canonical-action:{exc}"))

        try:
            resolved = self._subjects.resolve(
                request.subject,
                tenant_id=request.tenant_id,
                space_id=request.space_id,
            )
        except SubjectResolutionError as exc:
            return self._finish(request, action_name=action.name, decision=_deny(f"subject:{exc}"))
        except AuthorizationUnavailable as exc:
            return self._finish(
                request, action_name=action.name, decision=_deny(f"authorization-unavailable:{exc}")
            )

        try:
            resource = self._resources.resolve(request.resource)
        except ResourceResolutionError as exc:
            return self._finish(request, action_name=action.name, decision=_deny(f"resource:{exc}"))
        except AuthorizationUnavailable as exc:
            return self._finish(
                request, action_name=action.name, decision=_deny(f"authorization-unavailable:{exc}")
            )

        if self._scopes.binding_conflict(resource, request.tenant_id, request.space_id):
            return self._finish(request, action_name=action.name, decision=_deny("cross-tenant"))

        try:
            return self._evaluate(
                request, resolved, action, resource, actor_id=actor_id
            )
        except AuthorizationUnavailable as exc:
            return self._finish(
                request, action_name=action.name, decision=_deny(f"authorization-unavailable:{exc}")
            )

    # --------------------------------------------------------------- internals
    def _evaluate(self, request, resolved, action, resource, *, actor_id: str) -> Decision:
        if resolved.subject.subject_type == "AGENT":
            agent_outcome = self._permissions.agent(resolved, action, resource)
            if agent_outcome.deny:
                return self._finish(
                    request,
                    action_name=action.name,
                    decision=Decision(
                        effect="DENY",
                        reason="agent-denied",
                        matched_rules=agent_outcome.reasons,
                    ),
                    resolved=resolved,
                    resource=resource,
                )
            rbac = agent_outcome
        else:
            rbac = self._permissions.rbac(resolved, action, resource)

        acl = self._permissions.acl(resolved, action, resource)

        from core.policy import PolicyContext

        context = PolicyContext(
            action=action.name,
            actor_id=actor_id,
            tenant_id=resource.tenant_id,
            space_id=resource.space_id,
            environment=dict(request.environment),
            subject_id=resolved.subject.subject_id,
            subject_type=resolved.subject.subject_type,
            delegator_id=resolved.subject.delegator_id,
            resource_type=resource.type,
            resource_id=resource.id,
            scope="SPACE" if request.space_id else "TENANT",
            risk_level=request.risk_level,
            request_id=request.request_id,
        )
        evaluation = self._policy.evaluate(context, request.risk_level)

        if resolved.risk_ceiling is not None:
            if not is_risk_level(resolved.risk_ceiling) or risk_rank(evaluation.risk_level) > risk_rank(
                resolved.risk_ceiling
            ):
                return self._finish(
                    request,
                    action_name=action.name,
                    decision=Decision(effect="DENY", reason="risk-ceiling-exceeded"),
                    resolved=resolved,
                    resource=resource,
                    risk_level=evaluation.risk_level,
                )

        decision = combine(
            rbac=rbac,
            acl=acl,
            policy=evaluation.outcome,
            approval_required=evaluation.approval_required,
            policy_failed=evaluation.failed,
        )
        if decision.policy_version is None and evaluation.policy_version is not None:
            decision = Decision(
                effect=decision.effect,
                reason=decision.reason,
                matched_rules=decision.matched_rules,
                policy_version=evaluation.policy_version,
            )

        return self._finish(
            request,
            action_name=action.name,
            decision=decision,
            resolved=resolved,
            resource=resource,
            risk_level=evaluation.risk_level,
        )

    def _finish(
        self,
        request: AuthorizationRequest,
        *,
        action_name: str,
        decision: Decision,
        resolved=None,
        resource: ResourceRef | None = None,
        risk_level: str | None = None,
    ) -> Decision:
        subject = resolved.subject if resolved is not None else request.subject
        target = resource or request.resource
        self._audit.record(
            decision=decision,
            action=action_name or target.type,
            resource=target,
            subject_id=subject.subject_id,
            subject_type=subject.subject_type,
            tenant_id=target.tenant_id or request.tenant_id,
            space_id=target.space_id or request.space_id,
            delegator_id=subject.delegator_id or request.delegator_id,
            actor_id=subject.actor_id or subject.identity_id,
            risk_level=risk_level,
            approval_required=decision.requires_approval,
            request_id=request.request_id,
        )
        return decision

    # ------------------------------------------------------------------ audit
    @property
    def audit_boundary(self) -> AuditBoundary:
        return self._audit

    def authorize_subject(self, subject: Subject, action: Action, resource: ResourceRef) -> Decision:
        """Convenience wrapper matching the ``Authorizer`` protocol."""
        return self.authorize(
            AuthorizationRequest(subject=subject, action=action, resource=resource)
        )


def _deny(reason: str) -> Decision:
    return Decision(effect="DENY", reason=reason)


__all__ = ["AuthorizationService"]
