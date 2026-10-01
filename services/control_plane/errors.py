"""P18 control-plane error taxonomy (additive to the existing application model).

Each code maps onto one stable, non-leaking outcome. Nothing here carries SQL, a
constraint name, a stack trace or any infrastructure text: the caller sees a
code, the operator sees the audit row.
"""

from __future__ import annotations


class ErrorCode:
    BOOTSTRAP_REQUIRED = "platform_bootstrap_required"
    AUTHORIZATION_DENIED = "platform_authorization_denied"
    INVALID_INPUT = "invalid_provisioning_input"
    TENANT_CONFLICT = "tenant_conflict"
    SPACE_CONFLICT = "space_conflict"
    PROVISIONING_CONFLICT = "provisioning_conflict"
    INITIAL_ADMIN_INVALID = "initial_admin_invalid"
    RESOURCE_PROJECTION_FAILED = "resource_projection_failed"
    INITIAL_ROLE_FAILED = "initial_role_failed"
    LIFECYCLE_CONFLICT = "lifecycle_conflict"
    TENANT_NOT_FOUND = "tenant_not_found"
    SPACE_NOT_FOUND = "space_not_found"
    TENANT_NOT_ACTIVE = "tenant_not_active"
    SPACE_NOT_ACTIVE = "space_not_active"


class ControlPlaneError(RuntimeError):
    """A control-plane failure with a stable code and a safe message."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}" if message else code)


__all__ = ["ControlPlaneError", "ErrorCode"]
