"""Identity adaptation endpoints (transport only — no SQL, no authorization)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.dependencies import get_database
from apps.api.error_mapping import translate
from services.use_cases import authenticate_identity, onboard_identity

router = APIRouter(prefix="/identity", tags=["identity"])


class OnboardingRequest(BaseModel):
    password: str = Field(min_length=1, repr=False)
    email: str | None = None
    username: str | None = None
    display_name: str | None = None


class AuthenticateRequest(BaseModel):
    login: str
    password: str = Field(min_length=1, repr=False)


@router.post("/onboarding", status_code=201)
def onboarding(payload: OnboardingRequest, db=Depends(get_database)) -> dict[str, str]:
    """Create user + identity + password credential in one use-case transaction."""
    try:
        result = onboard_identity(
            db,
            password=payload.password,
            email=payload.email,
            username=payload.username,
            display_name=payload.display_name,
        )
    except Exception as exc:  # noqa: BLE001 - translated, never echoed
        raise translate(exc) from exc
    return {
        "user_id": result.user_id,
        "identity_id": result.identity_id,
        "user_status": result.user_status,
        "identity_status": result.identity_status,
    }


@router.post("/authenticate")
def authenticate(payload: AuthenticateRequest, db=Depends(get_database)) -> dict[str, str]:
    """Verify a password credential. No session is issued here (§十七)."""
    try:
        identity = authenticate_identity(db, login=payload.login, password=payload.password)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "user_id": identity.user_id,
        "identity_id": identity.identity_id,
        "authentication_assurance": "credential_verified",
    }


__all__ = ["router"]
