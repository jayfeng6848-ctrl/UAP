"""Intelligence Facade endpoints (OQ-CUI-03 / 09 · PDL Appendix AP).

Transport only: the actor and tenant always come from the session and the path;
the body's ``context`` is a UX hint the facade never trusts for authorization.
The facade touches no SQL and no repository — it calls the existing Company service
use cases and the existing AI runtime.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_database
from apps.api.error_mapping import translate
from services.intelligence import ErrorCode, IntelligenceError, confirm_proposal, run_copilot
from services.use_cases import build_context

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

#: Customer-safe mapping for the facade's frozen failure codes.
_STATUS: dict[str, tuple[int, str]] = {
    ErrorCode.MODE_NOT_ALLOWED: (400, "mode_not_allowed"),
    ErrorCode.ACTION_NOT_PROPOSABLE: (400, "action_not_proposable"),
    ErrorCode.RESOURCE_NOT_FOUND: (403, "not_authorized"),
    ErrorCode.PROPOSAL_NOT_FOUND: (404, "proposal_not_found"),
    ErrorCode.PROPOSAL_STALE: (409, "proposal_stale"),
    ErrorCode.AI_UNAVAILABLE: (503, "ai_not_configured"),
}


class CopilotContext(BaseModel):
    surface: str | None = Field(default=None, max_length=64)
    space_id: str | None = Field(default=None, max_length=64)
    resource_id: str | None = Field(default=None, max_length=64)
    filters: dict[str, str] = Field(default_factory=dict)


class CopilotRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: CopilotContext = Field(default_factory=CopilotContext)
    mode: str = Field(default="answer", max_length=16)
    client_request_id: str | None = Field(default=None, max_length=64)


class ConfirmRequest(BaseModel):
    proposal_id: str = Field(min_length=8, max_length=64)


def _scope(db, request: Request, tenant_id: str):
    """Authenticated actor + authorized context; the path tenant must match."""
    try:
        context = build_context(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    if not context.tenant_id or str(context.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=403, detail="tenant context mismatch")
    return context


def _facade_error(exc: IntelligenceError) -> HTTPException:
    status, detail = _STATUS.get(exc.code, (503, "ai_unavailable"))
    return HTTPException(status_code=status, detail=detail)


@router.post("/tenants/{tenant_id}/assistant/runs", status_code=201)
def assistant_run(
    tenant_id: str, payload: CopilotRequest, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """One Copilot turn: ``answer`` (read) or ``propose`` (ephemeral proposal)."""
    context = _scope(db, request, tenant_id)
    try:
        return run_copilot(
            db,
            actor_id=context.user_id,
            actor_type=context.subject_type,
            tenant_id=tenant_id,
            space_id=context.space_id,
            message=payload.message,
            mode=payload.mode,
            context=payload.context.model_dump(),
            request_id=payload.client_request_id or context.request_id,
            action=payload.context.filters.get("action"),
            resource_id=payload.context.resource_id,
        )
    except IntelligenceError as exc:
        raise _facade_error(exc) from exc
    except Exception as exc:  # noqa: BLE001 - translated, never echoed
        raise translate(exc) from exc


@router.post("/tenants/{tenant_id}/assistant/proposals/confirm")
def assistant_confirm(
    tenant_id: str, payload: ConfirmRequest, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """Human confirmation: single-use proposal, re-authorized at confirm time."""
    context = _scope(db, request, tenant_id)
    try:
        return confirm_proposal(
            db,
            actor_id=context.user_id,
            tenant_id=tenant_id,
            proposal_id=payload.proposal_id,
            request_id=context.request_id,
        )
    except IntelligenceError as exc:
        raise _facade_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc


__all__ = ["router"]
