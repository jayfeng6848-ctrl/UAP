"""Tenant contracts.

A tenant is the top level isolation boundary. Cross-tenant reads and writes are
forbidden: any query leaving this layer must already carry a tenant scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Tenant:
    id: str
    slug: str
    display_name: str
    status: str = "active"

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@dataclass(frozen=True)
class TenantContext:
    """Ambient tenant scope for a request or job."""

    tenant_id: str


@runtime_checkable
class TenantResolver(Protocol):
    def get(self, tenant_id: str) -> Tenant | None:
        ...


def require_same_tenant(*tenant_ids: str | None) -> None:
    """Raise when the given tenant scopes disagree."""
    distinct = {t for t in tenant_ids if t is not None}
    if len(distinct) > 1:
        raise PermissionError("cross-tenant access is not allowed")


__all__ = ["Tenant", "TenantContext", "TenantResolver", "require_same_tenant"]
