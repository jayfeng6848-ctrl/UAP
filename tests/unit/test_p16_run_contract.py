"""P16 run lifecycle + error taxonomy unit tests (D02 / section 24)."""

from __future__ import annotations

import pytest

from core.agent import (
    AGENT_RUNTIME_ERROR_CODES,
    AgentRuntimeError,
    ErrorCode,
    InvalidRunTransition,
    RunStatus,
    TERMINAL_RUN_STATUSES,
    can_transition,
    is_agent_runtime_error_code,
    require_transition,
)

def test_lifecycle_allows_declared_transitions() -> None:
    assert can_transition(RunStatus.CREATED.value, RunStatus.RUNNING.value)
    assert can_transition(RunStatus.RUNNING.value, RunStatus.WAITING_TOOL.value)
    assert can_transition(RunStatus.WAITING_TOOL.value, RunStatus.COMPLETED.value)
    assert can_transition(RunStatus.RUNNING.value, RunStatus.FAILED.value)


def test_terminal_states_never_transition() -> None:
    for status in TERMINAL_RUN_STATUSES:
        for target in (RunStatus.RUNNING.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value):
            assert not can_transition(status, target)


def test_illegal_transition_raises() -> None:
    with pytest.raises(InvalidRunTransition):
        require_transition(RunStatus.COMPLETED.value, RunStatus.RUNNING.value)


def test_error_taxonomy_is_closed() -> None:
    # 17 (P16) + MODEL_UNAVAILABLE / MODEL_PROVIDER_MISMATCH (HD-P21-AI-04 §10)
    #    + 5 LOCAL_* codes (HD-P21-AI-01..03 §14) = 24. Still ONE closed taxonomy.
    assert len(AGENT_RUNTIME_ERROR_CODES) == 24
    assert is_agent_runtime_error_code(ErrorCode.TOOL_TIMEOUT)
    with pytest.raises(ValueError):
        AgentRuntimeError("SOMETHING_NEW", "not allowed")
