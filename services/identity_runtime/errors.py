"""P17 error taxonomy (closed set · mirrors the frozen decision语言)."""

from __future__ import annotations


class ErrorCode:
    TENANT_SCOPE_DENIED = "TENANT_SCOPE_DENIED"
    SPACE_SCOPE_DENIED = "SPACE_SCOPE_DENIED"
    MEMBERSHIP_REQUIRED = "MEMBERSHIP_REQUIRED"
    MEMBERSHIP_NOT_FOUND = "MEMBERSHIP_NOT_FOUND"
    MEMBERSHIP_DUPLICATE = "MEMBERSHIP_DUPLICATE"
    ROLE_SCOPE_MISMATCH = "ROLE_SCOPE_MISMATCH"
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    TARGET_NOT_IN_TENANT = "TARGET_NOT_IN_TENANT"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_PROVISIONED = "RESOURCE_NOT_PROVISIONED"
    AGENT_SCOPE_DENIED = "AGENT_SCOPE_DENIED"
    AGENT_SPACE_SCOPE_DENIED = "AGENT_SPACE_SCOPE_DENIED"
    CONTROL_PLANE_WRITE_DENIED = "CONTROL_PLANE_WRITE_DENIED"
    AUDIT_UNAVAILABLE = "AUDIT_UNAVAILABLE"


class IdentityRuntimeError(RuntimeError):
    """A P17 failure with a stable code and a safe (non-sensitive) message."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}" if message else code)
