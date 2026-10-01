"""Agent runtime orchestration (P16-D01 / D02 / D04 / D05 / D06 / D07).

One request-scoped synchronous run:

    load agent -> load published version -> actor authorization -> route ->
    provider (credential resolved inside the adapter boundary) -> AI request ->
    tool proposal -> agent grant -> tool execution -> ledger -> audit

Fail closed: every failure terminates the run with a frozen error code and a
``FAILED`` ledger row. The run never fabricates an actor, never reads a secret
and never retries the provider automatically.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

from agent.tools.interfaces import ToolContext
from core.agent import AgentRuntimeError, ErrorCode, RunStatus, require_transition
from core.ai import RouteRequest
from core.audit.interfaces import new_event_id
from intelligence.gateway.interfaces import AIRequest
from intelligence.providers.interfaces import ProviderRegistry

from infrastructure.logging import get_logger

from services.ai.gateway import AIGatewayService
from services.ai.credentials import SecretResolver
from services.ai.routing import resolve_route

from .repository import AgentRuntimeRepository
from .tool_authorization import ToolAuthorizationFacade
from .tools import ToolExecutor, ToolRegistry

DEFAULT_CAPABILITY = "chat"
DEFAULT_CLASSIFICATION = "INTERNAL"
HIGH_RISK = "HIGH"

logger = get_logger(__name__)


@dataclass(frozen=True)
class RunLimits:
    """Fail-closed bounds (P16 section 25/26)."""

    max_tool_calls: int = 4
    max_runtime_seconds: float = 60.0
    ai_timeout_seconds: float = 30.0
    tool_timeout_seconds: float = 5.0


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    status: str
    result: dict[str, Any] = field(default_factory=dict)
    failure_code: str | None = None


@runtime_checkable
class ActorAuthorizer(Protocol):
    """Actor-side authorization (the real implementation is the P09/P14 service)."""

    def authorize_actor(
        self,
        *,
        actor_type: str,
        actor_id: str,
        tenant_id: str,
        space_id: str | None,
        agent_id: str,
    ) -> bool:
        ...


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _proposals(text: str) -> list[dict[str, Any]]:
    """Tool proposals are an explicit, closed shape produced by the model."""
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, Mapping):
        return []
    raw = parsed.get("tools")
    if raw is None and parsed.get("tool") is not None:
        raw = [parsed.get("tool")]
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, Mapping) and item.get("key"):
            params = item.get("params")
            out.append({"key": str(item["key"]), "params": dict(params) if isinstance(params, Mapping) else {}})
    return out


class AgentRuntimeService:
    """Execute one agent run against the frozen boundaries."""

    def __init__(
        self,
        *,
        database: Any,
        registry: ProviderRegistry,
        credentials: SecretResolver,
        repository: AgentRuntimeRepository | None = None,
        tools: ToolRegistry | None = None,
        executor: ToolExecutor | None = None,
        authorizer: ActorAuthorizer | None = None,
        tool_authorization: ToolAuthorizationFacade | None = None,
        limits: RunLimits | None = None,
    ) -> None:
        self._db = database
        self._registry = registry
        self._credentials = credentials
        self._repo = repository or AgentRuntimeRepository()
        self._tools = tools or ToolRegistry()
        self._executor = executor or ToolExecutor(self._tools)
        self._authorizer = authorizer
        self._tool_auth = tool_authorization
        self._limits = limits or RunLimits()

    # ------------------------------------------------------------------ public
    def run(
        self,
        *,
        agent_id: str,
        actor_type: str,
        actor_id: str,
        tenant_id: str,
        space_id: str | None = None,
        input_text: str = "",
        request_id: str | None = None,
    ) -> RunOutcome:
        """T1 admission (committed) then T2 execution (separate transactions).

        Once T1 commits, the run row is a durable fact: no later failure —
        provider, tool, credential, timeout or internal — may erase it.
        """
        run_id = new_event_id()
        started = time.monotonic()

        # ---------------- T1: run admission (its own committed transaction)
        try:
            with self._db.transaction() as session:
                agent = self._repo.get_agent(session, agent_id)
                version = self._admissible_agent_version(session, agent, tenant_id)
                self._repo.insert_agent_run(
                    session,
                    run_id=run_id,
                    tenant_id=tenant_id,
                    space_id=space_id,
                    agent_id=agent_id,
                    agent_version_id=str(agent["current_version_id"]),
                    actor_type=actor_type,
                    actor_id=actor_id,
                    request_id=request_id,
                    status=RunStatus.CREATED.value,
                    input_digest=_digest(input_text),
                )
        except AgentRuntimeError as exc:
            # Refused before admission: no run exists, so none is claimed.
            self._fail(run_id, exc.code)
            return RunOutcome(run_id=run_id, status=RunStatus.FAILED.value, failure_code=exc.code)
        except Exception as exc:  # noqa: BLE001 - never surface internals or messages
            # The class name (never the message) is safe diagnostic evidence.
            self._fail(run_id, ErrorCode.INTERNAL_RUNTIME_ERROR, detail=type(exc).__name__)
            return RunOutcome(
                run_id=run_id, status=RunStatus.FAILED.value, failure_code=ErrorCode.INTERNAL_RUNTIME_ERROR
            )

        # ---------------- T2: execution (state changes commit independently)
        try:
            with self._db.transaction() as session:
                self._repo.finish_agent_run(
                    session, run_id=run_id, status=RunStatus.RUNNING.value, started=True, completed=False
                )
            with self._db.transaction() as session:
                outcome = self._run(
                    session,
                    run_id=run_id,
                    agent=agent,
                    version=version,
                    agent_id=agent_id,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    tenant_id=tenant_id,
                    space_id=space_id,
                    input_text=input_text,
                    request_id=request_id,
                    started=started,
                )
            return outcome
        except AgentRuntimeError as exc:
            self._fail(
                run_id,
                exc.code,
                detail=getattr(exc, "detail", None),
                decision_reason=getattr(exc, "decision_reason", None),
                auditable=True,
            )
            return RunOutcome(run_id=run_id, status=RunStatus.FAILED.value, failure_code=exc.code)
        except Exception as exc:  # noqa: BLE001
            detail = type(exc).__name__
            self._fail(run_id, ErrorCode.INTERNAL_RUNTIME_ERROR, detail=detail, auditable=True)
            return RunOutcome(
                run_id=run_id, status=RunStatus.FAILED.value, failure_code=ErrorCode.INTERNAL_RUNTIME_ERROR
            )

    # ----------------------------------------------------------------- internals
    def _admissible_agent_version(self, session, agent: Mapping[str, Any] | None, tenant_id: str) -> dict[str, Any]:
        """Identity checks that must pass *before* a run is admitted."""
        if agent is None or str(agent.get("status")) != "active":
            raise AgentRuntimeError(ErrorCode.AGENT_DISABLED, "agent is not active")
        if str(agent.get("tenant_id")) != str(tenant_id):
            raise AgentRuntimeError(ErrorCode.AUTHORIZATION_DENIED, "agent belongs to another tenant")
        version_id = agent.get("current_version_id")
        if not version_id:
            raise AgentRuntimeError(ErrorCode.AGENT_VERSION_INVALID, "agent has no current version")
        version = self._repo.get_agent_version(session, str(version_id))
        if version is None or str(version.get("status")) != "published":
            raise AgentRuntimeError(ErrorCode.AGENT_VERSION_INVALID, "agent version is not published")
        return version

    def _fail(
        self,
        run_id: str,
        code: str,
        *,
        detail: str | None = None,
        decision_reason: str | None = None,
        auditable: bool = False,
    ) -> bool:
        """Failure terminal state, then audit — in two separate transactions.

        Audit failure must never roll back an already-persisted FAILED run: the
        state transition commits first (A), the audit evidence is appended after
        (B, failure-tolerant).
        """
        metadata = {
            "code": code,
            **({"error_class": detail} if detail else {}),
            **({"decision_reason": decision_reason} if decision_reason else {}),
        }
        try:
            with self._db.transaction() as session:
                updated = self._repo.mark_run_failed(
                    session, run_id=run_id, failure_metadata=metadata, failure_code=code
                )
        except Exception:  # noqa: BLE001 - the failure path must never raise
            return False
        if not updated:
            # rowcount must be exactly 1; 0 means the ledger row is missing or the run
            # is already terminal. Never swallowed: surfaced as internal-error evidence.
            self._note_missing_transition(run_id, code)
            return False
        if auditable:
            try:
                with self._db.transaction() as session:
                    self._repo.insert_audit(
                        session,
                        audit_id=new_event_id(),
                        actor_type="USER",
                        actor_id=None,
                        action="execute",
                        result="error" if code != ErrorCode.AUTHORIZATION_DENIED else "denied",
                        risk_level="LOW",
                        tenant_id=None,
                        space_id=None,
                        correlation_id=run_id,
                        metadata={"outcome": code, "reason": "agent-run"},
                    )
            except Exception:  # noqa: BLE001 - audit failure is operational evidence only
                logger.warning(
                    "uap.agent_run.audit_append_failed",
                    extra={"context": {"event": "agent_run.audit_append_failed", "run_id": run_id}},
                )
        return True

    def _note_missing_transition(self, run_id: str, code: str) -> None:
        """rowcount == 0 evidence (ledger row absent or already terminal)."""
        logger.error(
            "uap.agent_run.failure_transition_missing",
            extra={
                "context": {
                    "event": "agent_run.failure_transition_missing",
                    "run_id": run_id,
                    "requested_code": code,
                    "classification": ErrorCode.INTERNAL_RUNTIME_ERROR,
                }
            },
        )

    def _run(self, session, **kw: Any) -> RunOutcome:  # noqa: C901 - explicit pipeline
        run_id = kw["run_id"]
        version = kw["version"]

        if self._authorizer is None:
            # Fail closed: without an actor authorizer nothing may run (D05).
            raise AgentRuntimeError(ErrorCode.AUTHORIZATION_DENIED, "no actor authorizer configured")
        if not self._authorizer.authorize_actor(
            actor_type=kw["actor_type"],
            actor_id=kw["actor_id"],
            tenant_id=kw["tenant_id"],
            space_id=kw["space_id"],
            agent_id=kw["agent_id"],
        ):
            raise AgentRuntimeError(ErrorCode.AUTHORIZATION_DENIED, "actor is not authorized")

        definition = version.get("definition") or {}
        capability = str(definition.get("capability") or DEFAULT_CAPABILITY)
        classification = str(definition.get("classification") or DEFAULT_CLASSIFICATION)
        decision = resolve_route(
            RouteRequest(
                capability=capability,
                classification=classification,
                tenant_id=kw["tenant_id"],
                space_id=kw["space_id"],
            ),
            policies=self._repo.list_policies(session),
            routes=self._repo.list_routes(session),
            providers=self._repo.list_providers(session),
            models=self._repo.list_models(session),
        )
        providers = {str(p["id"]): p for p in self._repo.list_providers(session)}
        models = {str(m["id"]): m for m in self._repo.list_models(session)}

        correlation = {
            "run_id": run_id,
            "tenant_id": kw["tenant_id"],
            "space_id": kw["space_id"],
            "agent_id": kw["agent_id"],
            "actor_id": kw["actor_id"],
            "capability": capability,
            "classification": classification,
            "id": new_event_id(),
        }
        gateway = AIGatewayService(
            registry=self._registry,
            credentials=self._credentials,
            recorder=lambda fields: self._repo.insert_ai_request_log(session, fields),
        )
        call_started = time.monotonic()
        completion = gateway.complete(
            AIRequest(prompt=kw["input_text"], model=None, parameters={}, tenant_id=kw["tenant_id"]),
            provider_row=providers[decision.provider_id],
            model_row=models[decision.model_id],
            correlation=correlation,
        )
        latency_ms = int((time.monotonic() - call_started) * 1000)

        tool_calls = 0
        results: list[dict[str, Any]] = []
        for proposal in _proposals(completion.text):
            if tool_calls >= self._limits.max_tool_calls:
                raise AgentRuntimeError(ErrorCode.TOOL_EXECUTION_FAILED, "tool call bound exceeded")
            if time.monotonic() - kw["started"] > self._limits.max_runtime_seconds:
                raise AgentRuntimeError(ErrorCode.TOOL_TIMEOUT, "run exceeded its duration bound")
            results.append(self._execute_tool(session, proposal, kw, run_id, decision.capability))
            tool_calls += 1

        result_metadata = {
            "provider": completion.provider,
            "model": completion.model,
            "latency_ms": latency_ms,
            "tool_results": results,
        }
        require_transition(RunStatus.RUNNING.value, RunStatus.COMPLETED.value)
        self._repo.finish_agent_run(
            session,
            run_id=run_id,
            status=RunStatus.COMPLETED.value,
            result_digest=_digest(json.dumps(result_metadata, sort_keys=True)),
            result_metadata=result_metadata,
            tool_calls=tool_calls,
            completed=True,
        )
        self._repo.insert_audit(
            session,
            audit_id=new_event_id(),
            actor_type=kw["actor_type"],
            actor_id=kw["actor_id"],
            action="execute",
            result="success",
            risk_level="LOW",
            tenant_id=kw["tenant_id"],
            space_id=kw["space_id"],
            correlation_id=run_id,
            metadata={"outcome": "completed", "reason": "agent-run"},
        )
        return RunOutcome(run_id=run_id, status=RunStatus.COMPLETED.value, result=result_metadata)

    def _execute_tool(
        self,
        session,
        proposal: Mapping[str, Any],
        kw: Mapping[str, Any],
        run_id: str,
        capability: str,
    ) -> dict[str, Any]:
        key = str(proposal["key"])
        params = dict(proposal.get("params") or {})
        tool = self._repo.get_tool_by_key(session, key, str(kw["tenant_id"]))
        if tool is None:
            raise AgentRuntimeError(ErrorCode.TOOL_NOT_FOUND, "tool is not registered")

        # Authorization: exactly one canonical path (ToolGate through the facade).
        # The runtime never re-implements tool/enabled/grant/scope/approval logic.
        if self._tool_auth is None:
            raise AgentRuntimeError(ErrorCode.TOOL_UNAUTHORIZED, "no tool authorization configured")
        self._tool_auth.authorize(
            tool_id=str(tool["id"]),
            agent_id=str(kw["agent_id"]),
            actor_id=str(kw["actor_id"]),
            actor_type=str(kw["actor_type"]),
            tenant_id=str(kw["tenant_id"]),
            space_id=kw["space_id"],
            request_id=kw.get("request_id"),
        )

        # Execution layer: choose the published version + trusted handler (not authorization).
        version = self._repo.get_published_tool_version(session, str(tool["id"]))
        if version is None:
            raise AgentRuntimeError(ErrorCode.TOOL_NOT_FOUND, "tool has no published version")
        handler_key = str(version.get("handler_ref"))
        handler = self._tools.get(handler_key)
        if handler is None:
            raise AgentRuntimeError(ErrorCode.TOOL_NOT_FOUND, "handler is not trusted")
        idempotent = bool(handler.idempotent) or str(tool.get("idempotency_mode")) not in (
            "",
            "none",
            "None",
        )
        if not idempotent:
            raise AgentRuntimeError(ErrorCode.IDEMPOTENCY_CONFLICT, "tool idempotency cannot be proven")

        context = ToolContext(
            tenant_id=str(kw["tenant_id"]),
            actor_id=str(kw["actor_id"]),
            space_id=kw["space_id"],
        )
        started = time.monotonic()
        try:
            result = self._executor.execute(
                handler_key=handler_key,
                params=params,
                context=context,
                timeout_seconds=self._limits.tool_timeout_seconds,
            )
            status, error_code = "succeeded", None
        except AgentRuntimeError as exc:
            status, error_code = "failed", exc.code
            result = None
        duration_ms = int((time.monotonic() - started) * 1000)

        self._repo.insert_tool_execution(
            session,
            {
                "id": new_event_id(),
                "tenant_id": kw["tenant_id"],
                "tool_id": tool["id"],
                "tool_version_id": version["id"],
                "agent_id": kw["agent_id"],
                "actor_id": kw["actor_id"],
                "idempotency_key": f"{run_id}:{key}",
                "status": status,
                "input_digest": _digest(json.dumps(params, sort_keys=True)),
                "output_digest": _digest(json.dumps(result.data, sort_keys=True)) if result else None,
                "risk_level": str(tool.get("risk_level") or "LOW"),
                "attempts": 1,
                "duration_ms": duration_ms,
                "error_code": error_code,
                "correlation_id": run_id,
                "run_id": run_id,
            },
        )
        if result is None:
            raise AgentRuntimeError(
                error_code or ErrorCode.TOOL_EXECUTION_FAILED, "tool execution failed"
            )
        return {"tool": key, "ok": bool(result.ok), "capability": capability}
