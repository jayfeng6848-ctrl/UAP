"""Scope evaluation.

Wraps the pure core scope rules with the service-side checks the decision needs:
which grants a subject holds, whether a grant covers a resource, and whether the
caller's own tenant/space context is consistent with the resource.

There is no resource parent tree, so no implicit inheritance is ever applied.
"""

from __future__ import annotations

from core.permission import Grant, Subject
from core.permission.scope import narrows_or_equals, owns_resource, scope_covers
from core.resource import ResourceRef

from .subjects import ResolvedSubject


class ScopeEvaluator:
    """Evaluate stored scopes and context predicates against a resource."""

    def covering_grants(self, resolved: ResolvedSubject, resource: ResourceRef) -> tuple[Grant, ...]:
        return tuple(g for g in resolved.grants if scope_covers(g, resource))

    def is_self(self, subject: Subject, resource: ResourceRef) -> bool:
        """The ``SELF`` predicate — a context predicate, not a stored scope."""
        return owns_resource(subject, resource)

    def binding_conflict(
        self, resource: ResourceRef, tenant_id: str | None, space_id: str | None
    ) -> bool:
        """True when the caller's context crosses the resource boundary.

        A cross-tenant mismatch is unconditional: there is no allowance path.
        """
        if tenant_id is not None and tenant_id != resource.tenant_id:
            return True
        if space_id is not None and resource.space_id is not None:
            return space_id != resource.space_id
        return False

    @staticmethod
    def narrows_or_equals(child: Grant, parent: Grant) -> bool:
        """Grants may only ever tighten, never widen, an inherited authority."""
        return narrows_or_equals(child, parent)


__all__ = ["ScopeEvaluator"]
