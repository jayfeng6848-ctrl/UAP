"""Agent runtime error taxonomy (frozen list — P16 section 24).

The taxonomy is closed: a new failure mode requires a decision, not a new
string invented at a call site. Messages are safe by construction — callers
must never interpolate credential material into them.

HD-P21-AI-04 (Universal Provider Model Selection) extends the closed list with
``MODEL_UNAVAILABLE`` / ``MODEL_PROVIDER_MISMATCH``: a missing or mismatched
model is its own frozen failure and never a silent substitution.
HD-P21-AI-01/-02/-03 (Local AI) add the local-provider failure codes. There is
exactly ONE taxonomy — no parallel error system.
"""

from __future__ import annotations

from typing import Final


class ErrorCode:
    AUTHORIZATION_DENIED: Final = "AUTHORIZATION_DENIED"
    AGENT_DISABLED: Final = "AGENT_DISABLED"
    AGENT_VERSION_INVALID: Final = "AGENT_VERSION_INVALID"
    POLICY_DENIED: Final = "POLICY_DENIED"
    ROUTE_UNAVAILABLE: Final = "ROUTE_UNAVAILABLE"
    PROVIDER_UNAVAILABLE: Final = "PROVIDER_UNAVAILABLE"
    CREDENTIAL_UNAVAILABLE: Final = "CREDENTIAL_UNAVAILABLE"
    MODEL_REQUEST_FAILED: Final = "MODEL_REQUEST_FAILED"
    # HD-P21-AI-04 §10 — provider + model are two independent execution facts.
    MODEL_UNAVAILABLE: Final = "MODEL_UNAVAILABLE"
    MODEL_PROVIDER_MISMATCH: Final = "MODEL_PROVIDER_MISMATCH"
    # HD-P21-AI-01..03 §14 — LOCAL provider failure taxonomy (fail-closed).
    LOCAL_AI_UNAVAILABLE: Final = "LOCAL_AI_UNAVAILABLE"
    LOCAL_MODEL_UNAVAILABLE: Final = "LOCAL_MODEL_UNAVAILABLE"
    LOCAL_MODEL_NOT_FOUND: Final = "LOCAL_MODEL_NOT_FOUND"
    LOCAL_PROVIDER_PROTOCOL_ERROR: Final = "LOCAL_PROVIDER_PROTOCOL_ERROR"
    LOCAL_PROVIDER_AUTH_REQUIRED: Final = "LOCAL_PROVIDER_AUTH_REQUIRED"
    TOOL_NOT_FOUND: Final = "TOOL_NOT_FOUND"
    TOOL_DISABLED: Final = "TOOL_DISABLED"
    TOOL_UNAUTHORIZED: Final = "TOOL_UNAUTHORIZED"
    TOOL_SCOPE_DENIED: Final = "TOOL_SCOPE_DENIED"
    TOOL_APPROVAL_REQUIRED: Final = "TOOL_APPROVAL_REQUIRED"
    TOOL_TIMEOUT: Final = "TOOL_TIMEOUT"
    TOOL_EXECUTION_FAILED: Final = "TOOL_EXECUTION_FAILED"
    IDEMPOTENCY_CONFLICT: Final = "IDEMPOTENCY_CONFLICT"
    INTERNAL_RUNTIME_ERROR: Final = "INTERNAL_RUNTIME_ERROR"


AGENT_RUNTIME_ERROR_CODES: Final = tuple(
    value for name, value in vars(ErrorCode).items() if name.isupper() and isinstance(value, str)
)


def is_agent_runtime_error_code(value: str) -> bool:
    return value in AGENT_RUNTIME_ERROR_CODES


class AgentRuntimeError(RuntimeError):
    """A failure with a frozen code and a safe (non-credential) message."""

    def __init__(self, code: str, message: str = "") -> None:
        if not is_agent_runtime_error_code(code):
            raise ValueError(f"non-canonical agent runtime error code: {code!r}")
        self.code = code
        self.safe_message = message
        super().__init__(f"{code}: {message}" if message else code)
