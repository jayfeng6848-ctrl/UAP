"""Session / authenticated-context adaptation endpoints (transport only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_database
from apps.api.error_mapping import translate
from services.use_cases import build_context, login, logout, refresh_session

router = APIRouter(tags=["sessions"])


class LoginRequest(BaseModel):
    login: str
    password: str = Field(min_length=1, repr=False)
    device_id: str | None = None


@router.post("/sessions", status_code=201)
def create_session(
    payload: LoginRequest, request: Request, db=Depends(get_database)
) -> dict[str, object]:
    """Authenticate and, when a verified device is supplied, open a session (§十七)."""
    try:
        result = login(
            db,
            login_id=payload.login,
            password=payload.password,
            device_id=payload.device_id,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    body: dict[str, object] = {
        "user_id": result.identity.user_id,
        "identity_id": result.identity.identity_id,
        "authentication_assurance": (
            "session_verified" if result.session else "credential_verified"
        ),
    }
    if result.session is not None:
        body |= {
            "session_id": result.session.session_id,
            "token": result.session.token,
            "device_id": result.session.device_id,
            "expires_at": result.session.expires_at.isoformat(),
            "absolute_expires_at": result.session.absolute_expires_at.isoformat(),
        }
    return body


@router.post("/sessions/refresh")
def refresh(request: Request, db=Depends(get_database)) -> dict[str, object]:
    try:
        view = refresh_session(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "session_id": view.session_id,
        "expires_at": view.expires_at.isoformat(),
        "absolute_expires_at": (
            view.absolute_expires_at.isoformat() if view.absolute_expires_at else None
        ),
    }


@router.post("/sessions/logout")
def logout_endpoint(request: Request, db=Depends(get_database)) -> dict[str, int]:
    try:
        revoked = logout(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"revoked": revoked}


@router.get("/me")
def me(
    request: Request,
    db=Depends(get_database),
    x_tenant_id: str | None = Header(default=None),
    x_space_id: str | None = Header(default=None),
) -> dict[str, object]:
    """Return the frozen request context (identifiers only — never secrets)."""
    try:
        context = build_context(
            db,
            token=bearer_token(request) or "",
            tenant_id=x_tenant_id,
            space_id=x_space_id,
            correlation_id=request.headers.get("x-correlation-id"),
            request_id=request.headers.get("x-request-id"),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return dict(context.log_fields())


__all__ = ["router"]
