"""Control-plane / bootstrap capabilities (not reachable from the runtime API).

P17-AUTH-Q1 froze *who* owns the canonical resource projection: the control
plane / bootstrap, never ``uap_runtime``. The capability in this package exists
so a future tenant/space provisioning operation can create the structural
object **and** its ``resources`` projection inside one transaction.

It is deliberately not an HTTP surface: ``uap_runtime`` holds no INSERT on
``tenants`` / ``spaces``, so the runtime principal physically cannot run it.
"""

from .provisioning import (
    MEMBER_RESOURCE_TYPE,
    RESERVED_TENANT_COLLECTION_KEY,
    SPACE_RESOURCE_TYPE,
    TENANT_RESOURCE_TYPE,
    ProvisioningError,
    backfill_resource_projections,
    ensure_agent_projection,
    ensure_resource_projection,
    provision_space,
    provision_tenant,
)

__all__ = [
    "MEMBER_RESOURCE_TYPE",
    "RESERVED_TENANT_COLLECTION_KEY",
    "SPACE_RESOURCE_TYPE",
    "TENANT_RESOURCE_TYPE",
    "ProvisioningError",
    "backfill_resource_projections",
    "ensure_agent_projection",
    "ensure_resource_projection",
    "provision_space",
    "provision_tenant",
]
