"""Database access for the agent runtime (P16-D02 / D11 / D12).

Every statement is explicit (no ORM magic) and every column list is explicit, so
the runtime can never read a column it has no business reading.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

AGENT_COLUMNS = "id, tenant_id, space_id, owner_id, key, name, status, current_version_id"
AGENT_VERSION_COLUMNS = "id, agent_id, version, definition, allowed_tools, status"
POLICY_COLUMNS = (
    "id, tenant_id, space_id, name, max_classification, allowed_privacy_tiers, "
    "denied_providers, require_private, allow_fallback, fallback_preserves_classification, "
    "redaction_profile, enabled"
)
ROUTE_COLUMNS = "id, tenant_id, space_id, capability, priority, primary_model_id, fallback_chain, enabled"
PROVIDER_COLUMNS = (
    "id, key, adapter, base_url, enabled, privacy_tier, max_classification, capabilities, config, secret_ref"
)
MODEL_COLUMNS = (
    "id, provider_id, model_key, capabilities, context_window, max_output_tokens, "
    "max_classification, is_private, enabled"
)
TOOL_COLUMNS = "id, key, name, tenant_id, risk_level, timeout_ms, idempotency_mode, approval_required, enabled"
TOOL_VERSION_COLUMNS = "id, tool_id, version, input_schema, output_schema, risk_level, timeout_ms, handler_ref, status"
AGENT_GRANT_COLUMNS = "id, agent_id, version_id, permission_id, tool_id, effect, conditions"


def _rows(session: Session, sql: str, **params: Any) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in session.execute(text(sql), params).all()]


def _one(session: Session, sql: str, **params: Any) -> dict[str, Any] | None:
    rows = _rows(session, sql, **params)
    return rows[0] if rows else None


class AgentRuntimeRepository:
    """Reads the frozen configuration tables and writes the run ledger."""

    # ------------------------------------------------------------------ reads
    def get_agent(self, session: Session, agent_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {AGENT_COLUMNS} FROM agents WHERE id = CAST(:id AS uuid)",
            id=agent_id,
        )

    def get_agent_version(self, session: Session, version_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {AGENT_VERSION_COLUMNS} FROM agent_versions WHERE id = CAST(:id AS uuid)",
            id=version_id,
        )

    def list_policies(self, session: Session) -> list[dict[str, Any]]:
        return _rows(session, f"SELECT {POLICY_COLUMNS} FROM ai_policies")

    def list_routes(self, session: Session) -> list[dict[str, Any]]:
        return _rows(session, f"SELECT {ROUTE_COLUMNS} FROM ai_routes")

    def list_providers(self, session: Session) -> list[dict[str, Any]]:
        return _rows(session, f"SELECT {PROVIDER_COLUMNS} FROM ai_providers")

    def list_models(self, session: Session) -> list[dict[str, Any]]:
        return _rows(session, f"SELECT {MODEL_COLUMNS} FROM ai_models")

    def get_tool_by_key(self, session: Session, key: str, tenant_id: str) -> dict[str, Any] | None:
        """Tenant-scoped tool lookup: a platform tool or this tenant's own tool.

        Without the tenant predicate a multi-tenant database can resolve another
        tenant's tool row, which the canonical ToolGate then rejects as a
        cross-tenant tool (or worse, would execute under the wrong tenant).
        """
        return _one(
            session,
            f"SELECT {TOOL_COLUMNS} FROM tools WHERE key = :key"
            " AND (tenant_id IS NULL OR tenant_id = CAST(:tenant AS uuid))"
            " ORDER BY tenant_id NULLS LAST LIMIT 1",
            key=key,
            tenant=tenant_id,
        )

    def get_published_tool_version(self, session: Session, tool_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {TOOL_VERSION_COLUMNS} FROM tool_versions "
            "WHERE tool_id = CAST(:id AS uuid) AND status = 'published' "
            "ORDER BY version DESC LIMIT 1",
            id=tool_id,
        )

    def get_agent_tool_grant(self, session: Session, agent_id: str, tool_id: str) -> dict[str, Any] | None:
        return _one(
            session,
            f"SELECT {AGENT_GRANT_COLUMNS} FROM agent_permissions "
            "WHERE agent_id = CAST(:agent AS uuid) AND tool_id = CAST(:tool AS uuid) LIMIT 1",
            agent=agent_id,
            tool=tool_id,
        )

    # ----------------------------------------------------------------- writes
    def insert_agent_run(
        self,
        session: Session,
        *,
        run_id: str,
        tenant_id: str,
        space_id: str | None,
        agent_id: str,
        agent_version_id: str,
        actor_type: str,
        actor_id: str,
        request_id: str | None,
        status: str,
        input_digest: str,
    ) -> None:
        session.execute(
            text(
                "INSERT INTO agent_runs (id, tenant_id, space_id, agent_id, agent_version_id,"
                " actor_type, actor_id, request_id, status, input_digest)"
                " VALUES (CAST(:id AS uuid), CAST(:tenant AS uuid),"
                " CAST(:space AS uuid), CAST(:agent AS uuid), CAST(:version AS uuid),"
                " :actor_type, CAST(:actor AS uuid), CAST(:request AS uuid), :status, :digest)"
            ),
            {
                "id": run_id,
                "tenant": tenant_id,
                "space": space_id,
                "agent": agent_id,
                "version": agent_version_id,
                "actor_type": actor_type,
                "actor": actor_id,
                "request": request_id,
                "status": status,
                "digest": input_digest,
            },
        )

    def finish_agent_run(
        self,
        session: Session,
        *,
        run_id: str,
        status: str,
        result_digest: str | None = None,
        result_metadata: Mapping[str, Any] | None = None,
        failure_code: str | None = None,
        failure_metadata: Mapping[str, Any] | None = None,
        tool_calls: int | None = None,
        started: bool = False,
        completed: bool = True,
    ) -> None:
        session.execute(
            text(
                "UPDATE agent_runs SET status = :status,"
                " result_digest = COALESCE(:digest, result_digest),"
                " result_metadata = COALESCE(CAST(:meta AS jsonb), result_metadata),"
                " failure_code = :failure_code,"
                " failure_metadata = CAST(:failure_meta AS jsonb),"
                " tool_calls = COALESCE(:tool_calls, tool_calls),"
                " started_at = CASE WHEN :started THEN now() ELSE started_at END,"
                " completed_at = CASE WHEN :completed THEN now() ELSE completed_at END,"
                " updated_at = now()"
                " WHERE id = CAST(:id AS uuid)"
            ),
            {
                "id": run_id,
                "status": status,
                "digest": result_digest,
                "meta": json.dumps(dict(result_metadata)) if result_metadata is not None else None,
                "failure_code": failure_code,
                "failure_meta": json.dumps(dict(failure_metadata or {})),
                "tool_calls": tool_calls,
                "started": started,
                "completed": completed,
            },
        )

    def insert_ai_request_log(self, session: Session, fields: Mapping[str, Any]) -> None:
        session.execute(
            text(
                "INSERT INTO ai_request_logs (id, occurred_at, run_id, tenant_id, space_id,"
                " agent_id, actor_id, provider_id, model_id, capability, classification,"
                " status, latency_ms, prompt_tokens, completion_tokens)"
                " VALUES (COALESCE(CAST(:id AS uuid), uap_uuid_v7()), now(), CAST(:run_id AS uuid),"
                " CAST(:tenant AS uuid), CAST(:space AS uuid), CAST(:agent AS uuid),"
                " CAST(:actor AS uuid), CAST(:provider AS uuid), CAST(:model AS uuid),"
                " :capability, :classification, :status, :latency_ms, :prompt_tokens, :completion_tokens)"
            ),
            {
                "id": fields.get("id"),
                "run_id": fields.get("run_id"),
                "tenant": fields.get("tenant_id"),
                "space": fields.get("space_id"),
                "agent": fields.get("agent_id"),
                "actor": fields.get("actor_id"),
                "provider": fields.get("provider_id"),
                "model": fields.get("model_id"),
                "capability": fields.get("capability"),
                "classification": fields.get("classification"),
                "status": fields.get("status"),
                "latency_ms": fields.get("latency_ms"),
                "prompt_tokens": fields.get("prompt_tokens", 0),
                "completion_tokens": fields.get("completion_tokens", 0),
            },
        )

    def mark_run_failed(
        self,
        session: Session,
        *,
        run_id: str,
        failure_code: str,
        failure_metadata: Mapping[str, Any],
    ) -> bool:
        """Existence-aware failure transition. Returns True only when it applied."""
        result = session.execute(
            text(
                "UPDATE agent_runs SET status = 'FAILED', failure_code = :code,"
                " failure_metadata = CAST(:meta AS jsonb), completed_at = now(), updated_at = now()"
                " WHERE id = CAST(:id AS uuid)"
                " AND status IN ('CREATED','RUNNING','WAITING_TOOL')"
            ),
            {"id": run_id, "code": failure_code, "meta": json.dumps(dict(failure_metadata))},
        )
        return result.rowcount == 1

    def insert_tool_execution(self, session: Session, fields: Mapping[str, Any]) -> None:
        session.execute(
            text(
                "INSERT INTO tool_executions (id, tenant_id, tool_id, tool_version_id, agent_id,"
                " actor_id, idempotency_key, status, input_digest, output_digest, risk_level,"
                " attempts, started_at, finished_at, duration_ms, error_code, correlation_id, run_id)"
                " VALUES (CAST(:id AS uuid), CAST(:tenant AS uuid), CAST(:tool AS uuid),"
                " CAST(:version AS uuid), CAST(:agent AS uuid), CAST(:actor AS uuid),"
                " :idem, :status, :input_digest, :output_digest, :risk, :attempts, now(), now(),"
                " :duration_ms, :error_code, :correlation, CAST(:run_id AS uuid))"
            ),
            {
                "id": fields.get("id"),
                "tenant": fields.get("tenant_id"),
                "tool": fields.get("tool_id"),
                "version": fields.get("tool_version_id"),
                "agent": fields.get("agent_id"),
                "actor": fields.get("actor_id"),
                "idem": fields.get("idempotency_key"),
                "status": fields.get("status"),
                "input_digest": fields.get("input_digest"),
                "output_digest": fields.get("output_digest"),
                "risk": fields.get("risk_level"),
                "attempts": fields.get("attempts", 1),
                "duration_ms": fields.get("duration_ms", 0),
                "error_code": fields.get("error_code"),
                "correlation": fields.get("correlation_id"),
                "run_id": fields.get("run_id"),
            },
        )

    def insert_audit(
        self,
        session: Session,
        *,
        audit_id: str,
        actor_type: str,
        actor_id: str | None,
        action: str,
        result: str,
        risk_level: str,
        tenant_id: str | None,
        space_id: str | None,
        correlation_id: str,
        metadata: Mapping[str, Any],
    ) -> None:
        session.execute(
            text(
                "INSERT INTO audit_logs (id, occurred_at, tenant_id, space_id, actor_type, actor_id,"
                " action, result, risk_level, correlation_id, metadata, created_at)"
                " VALUES (CAST(:id AS uuid), now(), CAST(:tenant AS uuid), CAST(:space AS uuid),"
                " :actor_type, CAST(:actor AS uuid), :action, :result, :risk,"
                " CAST(:correlation AS uuid), CAST(:meta AS jsonb), now())"
            ),
            {
                "id": audit_id,
                "tenant": tenant_id,
                "space": space_id,
                "actor_type": actor_type,
                "actor": actor_id,
                "action": action,
                "result": result,
                "risk": risk_level,
                "correlation": correlation_id,
                "meta": json.dumps(dict(metadata)),
            },
        )
