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

#: The read-only Company qualification tool (HD-P21-14 §8). Its scope is always
#: taken from the runtime ``ToolContext`` — never from the model's parameters.
COMPANY_EMPLOYEE_LIST_KEY = "company.employee_list"
COMPANY_EMPLOYEE_STATUSES = ("active", "suspended", "terminated")
COMPANY_EMPLOYEE_MAX_LIMIT = 100
COMPANY_EMPLOYEE_DEFAULT_LIMIT = 25


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


def _make_company_employee_list(company_db: Any) -> HandlerFn:
    """Bind one read-only Company employee reader to a runtime database.

    Read-only by construction: the handler can only call
    ``services.company.use_cases.list_employees``, which runs the canonical
    ``AuthorizationService`` check (action ``list`` on ``company_employee``) and
    raises a :class:`CompanyError` when the caller is not allowed. The tenant and
    the actor come from the runtime ``ToolContext``; parameters may only filter.
    """
    from services.company.errors import CompanyError, ErrorCode as CompanyErrorCode
    from services.company.use_cases import list_employees

    def _company_employee_list(params: Mapping[str, Any], context: ToolContext) -> ToolResult:
        allowed_params = {"status", "limit", "search"}
        if set(params) - allowed_params:
            return ToolResult(ok=False, error="unsupported_parameter")

        status = params.get("status")
        if status is not None and (
            not isinstance(status, str) or status not in COMPANY_EMPLOYEE_STATUSES
        ):
            return ToolResult(ok=False, error="invalid_status")

        raw_limit = params.get("limit", COMPANY_EMPLOYEE_DEFAULT_LIMIT)
        if not isinstance(raw_limit, int) or isinstance(raw_limit, bool):
            return ToolResult(ok=False, error="invalid_limit")
        limit = max(1, min(int(raw_limit), COMPANY_EMPLOYEE_MAX_LIMIT))

        search = params.get("search")
        if search is not None and not isinstance(search, str):
            return ToolResult(ok=False, error="invalid_search")
        # A search must look at the whole authorized collection, not just the first
        # page, otherwise a name that sorts later would be silently missed. The read
        # stays bounded by the same hard cap.
        fetch_limit = COMPANY_EMPLOYEE_MAX_LIMIT if isinstance(search, str) and search.strip() else limit

        try:
            # tenant_id / actor_id are session-derived (ToolContext), never prompt-derived.
            rows = list_employees(
                company_db,
                actor_id=context.actor_id,
                tenant_id=context.tenant_id,
                status=status,
                limit=fetch_limit,
            )
        except CompanyError as exc:
            if exc.code in (
                CompanyErrorCode.AUTHORIZATION_DENIED,
                CompanyErrorCode.RESOURCE_NOT_PROVISIONED,
                CompanyErrorCode.TENANT_NOT_ACTIVE,
            ):
                return ToolResult(ok=False, error="not_authorized")
            return ToolResult(ok=False, error="company_read_failed")
        except Exception:  # noqa: BLE001 - fail closed, never leak internals
            return ToolResult(ok=False, error="company_read_failed")

        items = [
            {
                "employee_id": employee.id,
                "employee_no": employee.employee_no,
                "display_name": employee.display_name,
                "title": employee.title,
                "status": employee.status,
                "hired_at": employee.hired_at.isoformat() if employee.hired_at else None,
            }
            for employee in rows
        ]
        if isinstance(search, str) and search.strip():
            needle = search.strip().lower()
            items = [
                item
                for item in items
                if needle in str(item["display_name"]).lower()
                or needle in str(item["employee_no"]).lower()
            ]
        items.sort(key=lambda item: str(item["display_name"]))
        items = items[:limit]

        return ToolResult(
            ok=True,
            data={
                "items": items,
                "count": len(items),
                "tenant_id": context.tenant_id,
                "status_filter": status,
                "read_only": True,
            },
        )

    return _company_employee_list


def register_builtin_tools(registry: ToolRegistry, *, company_db: Any | None = None) -> ToolRegistry:
    """Built-in tools: LOW risk, deterministic, side-effect free.

    ``platform.clock.now`` is always present. The read-only Company qualification
    tool (``company.employee_list``) is registered only when a runtime database is
    supplied, so existing callers keep the exact previous behaviour.
    """
    registry.register(ToolHandler(key="platform.clock.now", fn=_clock_now))
    if company_db is not None:
        registry.register(
            ToolHandler(key=COMPANY_EMPLOYEE_LIST_KEY, fn=_make_company_employee_list(company_db))
        )
    return registry
