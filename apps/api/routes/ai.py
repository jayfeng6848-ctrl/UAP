"""Customer AI onboarding + assistant endpoints (HD-P21-17 · HD-P21-AI-01..04).

Transport only: no SQL, no authorization decision, no provider SDK. The customer
never sees or supplies a tenant, space, agent or tool identifier — the scope always
comes from the authenticated session, and a raw cloud key only ever enters the
ephemeral per-(actor, tenant) connection store.

HD-P21-AI-04: a connection is ``provider + model + optional credential``. The model
is validated server-side — for a cloud provider against its own enabled catalog, for
a local provider against what the runtime host actually reports on ``GET /v1/models``.
The browser never probes ``localhost`` itself (§13).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_database
from apps.api.error_mapping import translate
from core.agent import AgentRuntimeError, ErrorCode
from intelligence.gateway.interfaces import AIRequest
from services.agent.use_cases import (
    build_provider_registry,
    find_qualification_agent,
    list_provider_models,
    load_model_by_key,
    run_agent,
)
from services.ai.connection import connection_store
from services.ai.credentials import SecretValue
from services.ai.gateway import AIGatewayService
from services.ai.local import detect_local_providers, discover_local_models
from services.ai.providers import (
    AUTH_NONE,
    LOCALITY_LOCAL,
    customer_provider_list,
    get_profile,
)
from services.use_cases import build_context

router = APIRouter(prefix="/ai", tags=["ai"])

#: Synthetic-only probe (HD-P21-17 §30). No customer or production data is ever sent.
CONNECTION_PROBE = "UAP connection check. Reply with the single word: ok"
#: A LOCAL connection has no credential; the sentinel keeps the store's shape total.
LOCAL_SECRET_REF = "local:no-credential"


class ConnectRequest(BaseModel):
    provider: str = Field(default="openai", max_length=32)
    #: HD-P21-AI-04 §6/§7/§9: the customer's explicit model. Never optional.
    model: str = Field(min_length=1, max_length=200)
    api_key: str = Field(default="", max_length=512, repr=False)


class MessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class _CandidateResolver:
    """Resolve the provider credential with the key the customer has just typed."""

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def resolve(self, secret_ref: str) -> SecretValue:
        return SecretValue(self._key, "candidate")


def _scope(db, request: Request):
    """Authenticated actor + authorized context. Never prompt/body supplied."""
    try:
        context = build_context(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    if not context.tenant_id:
        raise HTTPException(status_code=403, detail="tenant context is required")
    return context


def _connection_error(exc: AgentRuntimeError) -> HTTPException:
    """Map an internal failure to a customer-safe code (technical detail stays internal)."""
    code = str(getattr(exc, "code", ""))
    detail = getattr(exc, "detail", None)
    if code in (ErrorCode.CREDENTIAL_UNAVAILABLE, ErrorCode.PROVIDER_UNAVAILABLE):
        return HTTPException(status_code=503, detail="ai_not_configured")
    if code == ErrorCode.MODEL_UNAVAILABLE:
        return HTTPException(status_code=400, detail="model_not_available")
    if code == ErrorCode.MODEL_REQUEST_FAILED:
        if detail == "ProviderHttpError":
            return HTTPException(status_code=400, detail="api_key_rejected")
        return HTTPException(status_code=502, detail="ai_service_unreachable")
    return HTTPException(status_code=503, detail="ai_unavailable")


def _local_error(exc: AgentRuntimeError) -> HTTPException:
    """LOCAL failures keep their own customer-safe vocabulary (fail-closed)."""
    code = str(getattr(exc, "code", ""))
    if code == ErrorCode.LOCAL_PROVIDER_AUTH_REQUIRED:
        return HTTPException(status_code=400, detail="local_auth_required")
    if code == ErrorCode.LOCAL_MODEL_NOT_FOUND:
        return HTTPException(status_code=400, detail="local_model_not_found")
    if code == ErrorCode.LOCAL_PROVIDER_PROTOCOL_ERROR:
        return HTTPException(status_code=502, detail="local_protocol_error")
    if code in (
        ErrorCode.LOCAL_AI_UNAVAILABLE,
        ErrorCode.LOCAL_MODEL_UNAVAILABLE,
        ErrorCode.MODEL_REQUEST_FAILED,
    ):
        return HTTPException(status_code=502, detail="local_service_unreachable")
    return HTTPException(status_code=503, detail="ai_unavailable")


@router.get("/connection")
def read_connection(request: Request, db=Depends(get_database)) -> dict[str, object]:
    """First-use detection: is AI already connected for this actor + tenant?"""
    context = _scope(db, request)
    status = connection_store.describe(actor_id=context.user_id, tenant_id=context.tenant_id)
    status["assistant_ready"] = (
        find_qualification_agent(db, tenant_id=context.tenant_id) is not None
    )
    status["ttl_seconds"] = connection_store.ttl_seconds()
    status["providers"] = customer_provider_list()
    return status


@router.get("/providers")
def list_providers(request: Request, db=Depends(get_database)) -> dict[str, object]:
    """The customer-visible AI service list (names + one line; no URLs or model ids)."""
    _scope(db, request)
    return {"providers": customer_provider_list()}


@router.get("/local/providers")
def list_local_providers(request: Request, db=Depends(get_database)) -> dict[str, object]:
    """Server-side detection of the local runtimes on the UAP runtime host (§13)."""
    _scope(db, request)
    return {"providers": detect_local_providers()}


@router.get("/providers/{provider_key}/models")
def read_provider_models(
    provider_key: str, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """The selectable models of one service (HD-P21-AI-04 §6/§7).

    Cloud -> the provider's own enabled ``ai_models`` rows.
    Local -> ``GET /v1/models`` on the runtime host (discovery is authoritative).
    """
    _scope(db, request)
    profile = get_profile(provider_key)
    if profile is None:
        raise HTTPException(status_code=404, detail="provider_not_supported")
    if profile.locality == LOCALITY_LOCAL:
        try:
            discovered = discover_local_models(profile.key)
        except AgentRuntimeError as exc:
            raise _local_error(exc) from exc
        return {
            "provider": profile.key,
            "locality": profile.locality,
            "models": [{"key": model, "display_name": model} for model in discovered],
        }
    rows = list_provider_models(db, provider_key=profile.key)
    return {
        "provider": profile.key,
        "locality": profile.locality,
        "models": [
            {
                "key": str(row["model_key"]),
                "display_name": str(row.get("display_name") or row["model_key"]),
            }
            for row in rows
        ],
    }


@router.post("/connection", status_code=201)
def create_connection(
    payload: ConnectRequest, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """一键启用：验证 provider + model（+ 必要凭证），然后绑定本次连接。"""
    context = _scope(db, request)
    profile = get_profile(payload.provider)
    if profile is None:
        raise HTTPException(status_code=400, detail="provider_not_supported")
    model = payload.model.strip()
    api_key = payload.api_key.strip()

    if profile.locality == LOCALITY_LOCAL:
        # §9: the model must be one the runtime host actually reports right now.
        try:
            discovered = discover_local_models(profile.key, api_key=api_key or None)
        except AgentRuntimeError as exc:
            raise _local_error(exc) from exc
        if model not in discovered:
            raise HTTPException(status_code=400, detail="local_model_not_found")
        if profile.auth == AUTH_NONE:
            # Ollama ignores the client placeholder; never persist it as a secret.
            api_key = ""
    else:
        provider_row, model_row = load_model_by_key(
            db, provider_key=profile.key, model_key=model
        )
        if provider_row is None:
            raise HTTPException(status_code=503, detail="ai_not_configured")
        if model_row is None:
            # Fail-closed: a model that is not enabled under *this* provider (including
            # another provider's model) is rejected, never silently substituted.
            raise HTTPException(status_code=400, detail="model_not_available")
        if not api_key:
            raise HTTPException(status_code=400, detail="api_key_required")
        gateway = AIGatewayService(
            registry=build_provider_registry(), credentials=_CandidateResolver(api_key)
        )
        try:
            gateway.complete(
                AIRequest(prompt=CONNECTION_PROBE, model=model, tenant_id=context.tenant_id),
                provider_row=provider_row,
                model_row=model_row,
            )
        except AgentRuntimeError as exc:
            raise _connection_error(exc) from exc
        except Exception as exc:  # noqa: BLE001 - never leak provider detail
            raise HTTPException(status_code=503, detail="ai_unavailable") from exc

    connection = connection_store.put(
        actor_id=context.user_id,
        tenant_id=context.tenant_id,
        provider_key=profile.key,
        model_key=model,
        api_key=api_key,
        # Cloud: the profile's own reference, so a DeepSeek key can never satisfy a
        # request made for another provider (§17). Local: an explicit no-credential ref.
        secret_ref=profile.secret_ref or LOCAL_SECRET_REF,
    )
    return {
        "connected": True,
        "provider": connection.provider_key,
        "model": connection.model_key,
        "expires_at": connection.expires_at,
        "ttl_seconds": connection_store.ttl_seconds(),
    }


@router.delete("/connection")
def delete_connection(request: Request, db=Depends(get_database)) -> dict[str, object]:
    context = _scope(db, request)
    cleared = connection_store.clear(actor_id=context.user_id, tenant_id=context.tenant_id)
    return {"cleared": cleared}


@router.post("/messages")
def send_message(
    payload: MessageRequest, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """Customer conversation: discover the tenant's agent, then run one agent run."""
    context = _scope(db, request)
    agent = find_qualification_agent(db, tenant_id=context.tenant_id)
    if agent is None:
        raise HTTPException(status_code=503, detail="ai_not_configured")
    try:
        outcome = run_agent(
            db,
            agent_id=str(agent["id"]),
            actor_type=context.subject_type,
            actor_id=context.user_id,
            tenant_id=context.tenant_id,
            space_id=context.space_id,
            input_text=payload.text,
            request_id=context.request_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "status": outcome.status,
        "result": outcome.result,
        "failure_code": outcome.failure_code,
    }


__all__ = ["router"]
