"""Scope evaluation.

Pure functions only. Inheritance is **explicit and downward**: a grant covers a
resource when the resource sits inside the grant's scope, and there is **no
implicit resource-parent inheritance** — the platform has no resource parent
tree, and this module must never invent one.

``RESOURCE`` and ``SELF`` are context predicates, not stored grant scopes.
"""

from __future__ import annotations

from core.resource.interfaces import ResourceRef

from .interfaces import Grant, Subject

_SCOPE_RANK = {"PLATFORM": 0, "TENANT": 1, "SPACE": 2}


def scope_covers(grant: Grant, resource: ResourceRef) -> bool:
    """Return True when ``grant`` covers ``resource``.

    Tenant isolation is never negotiable:

    * a tenant grant covers only its own tenant;
    * a space grant covers only its own space, and additionally only when any
      tenant binding it carries also matches.

    The platform stores a space role with a space and **no** tenant, so a space
    grant is matched on its space alone. That remains tenant safe because a
    space belongs to exactly one tenant — a resource in another tenant can never
    share the space identifier.
    """
    if grant.scope == "PLATFORM":
        return True

    if grant.scope == "TENANT":
        return grant.tenant_id is not None and resource.tenant_id == grant.tenant_id

    # SPACE
    if grant.space_id is None:
        return False
    if resource.space_id != grant.space_id:
        return False
    if grant.tenant_id is not None and resource.tenant_id != grant.tenant_id:
        return False
    return True


def narrows_or_equals(child: Grant, parent: Grant) -> bool:
    """True when ``child`` is *provably* no broader than ``parent``.

    Deliberately conservative: when containment cannot be proven from the two
    grants alone, the answer is False. A grant must never be treated as narrower
    just because we cannot see that it is wider.
    """
    if _SCOPE_RANK[child.scope] < _SCOPE_RANK[parent.scope]:
        return False

    if parent.scope == "PLATFORM":
        return True

    if parent.scope == "TENANT":
        if parent.tenant_id is None:
            return False
        return child.tenant_id == parent.tenant_id

    # parent is SPACE
    if parent.space_id is None:
        return False
    return child.space_id == parent.space_id


def owns_resource(subject: Subject, resource: ResourceRef) -> bool:
    """The ``SELF`` predicate: only a user can be a resource owner."""
    if subject.subject_type != "USER" or resource.owner_identity_id is None:
        return False
    return resource.owner_identity_id == subject.identity_id


def scope_matches_predicate(predicate: str, subject: Subject, resource: ResourceRef) -> bool:
    """Evaluate a context predicate (``SELF`` / ``RESOURCE``)."""
    if predicate == "SELF":
        return owns_resource(subject, resource)
    if predicate == "RESOURCE":
        # A concrete resource instance: the ACL table carries the decision.
        return True
    return False


__all__ = [
    "narrows_or_equals",
    "owns_resource",
    "scope_covers",
    "scope_matches_predicate",
]
