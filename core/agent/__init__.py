"""Agent runtime contracts (P16-D02 / D12).

Pure contract layer: statuses, transitions, proposals and the error taxonomy.
No I/O, no persistence, no framework or provider dependency.
"""

from .errors import (
    AGENT_RUNTIME_ERROR_CODES,
    AgentRuntimeError,
    ErrorCode,
    is_agent_runtime_error_code,
)
from .run import (
    RUN_STATUSES,
    TERMINAL_RUN_STATUSES,
    AgentRunRecord,
    InvalidRunTransition,
    RunStatus,
    ToolProposal,
    can_transition,
    require_transition,
)

__all__ = [
    "AGENT_RUNTIME_ERROR_CODES",
    "AgentRunRecord",
    "AgentRuntimeError",
    "ErrorCode",
    "InvalidRunTransition",
    "RUN_STATUSES",
    "RunStatus",
    "TERMINAL_RUN_STATUSES",
    "ToolProposal",
    "can_transition",
    "is_agent_runtime_error_code",
    "require_transition",
]
