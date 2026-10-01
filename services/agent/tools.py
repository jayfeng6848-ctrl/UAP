"""Tool registry + executor (P16-D06 / D09 / §22).

``handler_ref`` is used **only** as a registry key: no dynamic import, no
``eval``, no arbitrary callable lookup. The first tool is low risk, deterministic
and side-effect free, which is also why abandoning a timed-out call is safe.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from agent.tools.interfaces import ToolContext, ToolResult
from core.agent import AgentRuntimeError, ErrorCode

HandlerFn = Callable[[Mapping[str, Any], ToolContext], ToolResult]


@dataclass(frozen=True)
class ToolHandler:
    """One trusted handler plus the execution facts the runtime needs."""

    key: str
    fn: HandlerFn
    risk_level: str = "LOW"
    idempotent: bool = True
    timeout_seconds: float = 5.0


class ToolRegistry:
    """Fixed key -> trusted handler map. Keys are never executable paths."""

    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, handler: ToolHandler) -> None:
        self._handlers[handler.key] = handler

    def get(self, key: str) -> ToolHandler | None:
        return self._handlers.get(key)

    def keys(self) -> list[str]:
        return sorted(self._handlers)


class ToolExecutor:
    """Execute one authorized handler with a hard timeout."""

    def __init__(self, registry: ToolRegistry, *, default_timeout_seconds: float = 5.0) -> None:
        self._registry = registry
        self._default_timeout = default_timeout_seconds

    def execute(
        self,
        *,
        handler_key: str,
        params: Mapping[str, Any],
        context: ToolContext,
        timeout_seconds: float | None = None,
    ) -> ToolResult:
        handler = self._registry.get(handler_key)
        if handler is None:
            raise AgentRuntimeError(ErrorCode.TOOL_NOT_FOUND, "tool handler is not registered")
        timeout = timeout_seconds or handler.timeout_seconds or self._default_timeout
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(handler.fn, params, context)
            try:
                return future.result(timeout=timeout)
            except FutureTimeout as exc:
                raise AgentRuntimeError(ErrorCode.TOOL_TIMEOUT, "tool exceeded its timeout") from exc
            except AgentRuntimeError:
                raise
            except Exception as exc:  # noqa: BLE001 - never leak handler internals
                raise AgentRuntimeError(ErrorCode.TOOL_EXECUTION_FAILED, "tool handler failed") from exc


def _clock_now(params: Mapping[str, Any], context: ToolContext) -> ToolResult:
    """``platform.clock.now`` — deterministic-ish, pure, side-effect free."""
    return ToolResult(
        ok=True,
        data={
            "now": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "tenant_id": context.tenant_id,
        },
    )


def register_builtin_tools(registry: ToolRegistry) -> ToolRegistry:
    """The only tools P16 ships: LOW risk, deterministic, side-effect free."""
    registry.register(ToolHandler(key="platform.clock.now", fn=_clock_now))
    return registry
