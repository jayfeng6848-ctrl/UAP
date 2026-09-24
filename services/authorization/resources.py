"""Resource resolution.

The stored row is authoritative: tenant, space, owner and classification are
read from the store, never trusted from the caller. An unresolvable resource is
an error, and every error resolves to a denial downstream.
"""

from __future__ import annotations

from core.resource import ResourceRef

from .errors import AuthorizationUnavailable, ResourceResolutionError
from .repository import AuthorizationRepository

_DELETED = "deleted"


class ResourceResolver:
    """Resolve a declared resource reference into an authoritative reference."""

    def __init__(self, repository: AuthorizationRepository) -> None:
        self._repository = repository

    def resolve(self, ref: ResourceRef) -> ResourceRef:
        try:
            row = self._repository.get_resource(ref.id)
        except ResourceResolutionError:
            raise
        except Exception as exc:  # pragma: no cover - infrastructure failure
            raise AuthorizationUnavailable(str(exc)) from exc

        if row is None:
            raise ResourceResolutionError("unknown resource")

        mapping = row._mapping
        if str(mapping["status"]) == _DELETED:
            raise ResourceResolutionError("resource is deleted")

        resolved = ResourceRef(
            type=str(mapping["resource_type"]),
            id=str(mapping["id"]),
            tenant_id=str(mapping["tenant_id"]),
            space_id=str(mapping["space_id"]) if mapping["space_id"] else None,
            owner_identity_id=(
                str(mapping["owner_id"]) if mapping["owner_id"] else None
            ),
            classification=str(mapping["classification"]),
            status=str(mapping["status"]),
        )

        if ref.type and ref.type != resolved.type:
            raise ResourceResolutionError("resource type mismatch")
        return resolved


__all__ = ["ResourceResolver"]
