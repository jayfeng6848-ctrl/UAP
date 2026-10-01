"""Agent Run endpoints (P16-D13). Transport only: no SQL, no provider SDK."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_database
from apps.api.error_mapping import translate
from services.agent.use_cases import read_agent_run, run_agent
from services.use_cases import build_context

router = APIRouter(tags=["agent-runs"])


class AgentRunRequest(BaseModel):
    input: str = Field(min_length=1, max_length=8000)
    request_id: str | None = None


def _context(db, request: Request):
    try:
        return build_context(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc


@router.post("/agents/{agent_id}/runs", status_code=201)
def create_agent_run(
    agent_id: str, payload: AgentRunRequest, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """Create and execute exactly one agent run (fail-closed on any stage)."""
    context = _context(db, request)
    if not context.tenant_id:
        raise HTTPException(status_code=403, detail="tenant context is required")
    try:
        outcome = run_agent(
            db,
            agent_id=agent_id,
            actor_type=context.subject_type,
            actor_id=context.user_id,
            tenant_id=context.tenant_id,
            space_id=context.space_id,
            input_text=payload.input,
            request_id=payload.request_id or context.request_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "run_id": outcome.run_id,
        "status": outcome.status,
        "result": outcome.result,
        "failure_code": outcome.failure_code,
    }


@router.get("/agent-runs/{run_id}")
def get_agent_run(run_id: str, request: Request, db=Depends(get_database)) -> dict[str, object]:
    """Read status / safe result metadata for one run (tenant-scoped)."""
    context = _context(db, request)
    if not context.tenant_id:
        raise HTTPException(status_code=403, detail="tenant context is required")
    row = read_agent_run(db, run_id=run_id, tenant_id=context.tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "run_id": row["id"],
        "status": row["status"],
        "agent_id": row["agent_id"],
        "tool_calls": row["tool_calls"],
        "result": row.get("result_metadata") or {},
        "failure_code": row.get("failure_code"),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
    }
