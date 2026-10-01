"""P16 tool registry / executor unit tests (D06 / section 22)."""

from __future__ import annotations

import time

import pytest

from agent.tools.interfaces import ToolContext, ToolResult
from core.agent import AgentRuntimeError, ErrorCode
from services.agent.tools import (
    ToolExecutor,
    ToolHandler,
    ToolRegistry,
    register_builtin_tools,
)

CONTEXT = ToolContext(tenant_id="t1", actor_id="u1")


def test_registry_requires_a_registered_key() -> None:
    executor = ToolExecutor(ToolRegistry())
    with pytest.raises(AgentRuntimeError) as exc:
        executor.execute(handler_key="os.system", params={}, context=CONTEXT)
    assert exc.value.code == ErrorCode.TOOL_NOT_FOUND


def test_handler_ref_is_only_a_registry_key() -> None:
    registry = ToolRegistry()
    registry.register(ToolHandler(key="demo.tool", fn=lambda p, c: ToolResult(ok=True, data={"p": dict(p)})))
    executor = ToolExecutor(registry)
    assert executor.execute(handler_key="demo.tool", params={"x": 1}, context=CONTEXT).ok
    assert "demo.tool" in registry.keys()


def test_timeout_is_bounded_and_reported() -> None:
    registry = ToolRegistry()

    def _slow(params, context):
        time.sleep(0.5)
        return ToolResult(ok=True)

    registry.register(ToolHandler(key="slow.tool", fn=_slow, timeout_seconds=0.01))
    with pytest.raises(AgentRuntimeError) as exc:
        ToolExecutor(registry).execute(handler_key="slow.tool", params={}, context=CONTEXT)
    assert exc.value.code == ErrorCode.TOOL_TIMEOUT


def test_handler_failure_is_not_leaked() -> None:
    registry = ToolRegistry()

    def _boom(params, context):
        raise RuntimeError("sk-secret-value")

    registry.register(ToolHandler(key="boom.tool", fn=_boom))
    with pytest.raises(AgentRuntimeError) as exc:
        ToolExecutor(registry).execute(handler_key="boom.tool", params={}, context=CONTEXT)
    assert exc.value.code == ErrorCode.TOOL_EXECUTION_FAILED
    assert "sk-secret-value" not in str(exc.value)


def test_builtin_tool_is_side_effect_free_and_idempotent() -> None:
    registry = register_builtin_tools(ToolRegistry())
    handler = registry.get("platform.clock.now")
    assert handler is not None and handler.idempotent and handler.risk_level == "LOW"
    result = ToolExecutor(registry).execute(
        handler_key="platform.clock.now", params={}, context=CONTEXT
    )
    assert result.ok and result.data["tenant_id"] == "t1"
