"""Canonical authorization resource types used by P17 (P17-AUTH-Q1).

These names are **not invented here**: ``permissions.resource_type`` already
carries ``tenant`` / ``space`` / ``member`` in the P13 canonical seed, and the
canonical RBAC layer only matches a permission whose ``resource_type`` equals
the resource's type. The membership-collection resource must therefore be typed
``member`` for ``member.read`` / ``member.admin`` to apply.

Both sides of the boundary import this module: the control plane when it
projects a resource row, and the runtime when it resolves one. Neither depends
on the other's behaviour.
"""

from __future__ import annotations

TENANT_RESOURCE_TYPE = "tenant"
SPACE_RESOURCE_TYPE = "space"
#: Fixed by ``permissions.resource_type`` of ``member.read`` / ``member.admin``.
MEMBER_RESOURCE_TYPE = "member"

__all__ = ["MEMBER_RESOURCE_TYPE", "SPACE_RESOURCE_TYPE", "TENANT_RESOURCE_TYPE"]
