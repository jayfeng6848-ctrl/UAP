"""Device enrollment / revoke adaptation endpoints (transport only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_database
from apps.api.error_mapping import translate
from services.use_cases import (
    build_context,
    complete_device_enrollment,
    mark_device_lost,
    revoke_device,
    start_device_enrollment,
)

router = APIRouter(prefix="/devices", tags=["devices"])


class EnrollmentChallengeRequest(BaseModel):
    login: str
    password: str = Field(min_length=1, repr=False)
    fingerprint: str = Field(min_length=1)
    label: str | None = None


class EnrollmentRequest(BaseModel):
    challenge_id: str
    secret: str = Field(min_length=1, repr=False)
    fingerprint: str = Field(min_length=1)
    label: str | None = None
    platform: str | None = None


class RevokeRequest(BaseModel):
    reason: str = "device_revoked"


@router.post("/enrollment-challenge", status_code=201)
def enrollment_challenge(
    payload: EnrollmentChallengeRequest, db=Depends(get_database)
) -> dict[str, str]:
    try:
        challenge = start_device_enrollment(
            db,
            login=payload.login,
            password=payload.password,
            fingerprint=payload.fingerprint,
            label=payload.label,
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "challenge_id": challenge.challenge_id,
        "secret": challenge.secret,
        "expires_at": challenge.expires_at.isoformat(),
    }


@router.post("/enrollment", status_code=201)
def enrollment(payload: EnrollmentRequest, db=Depends(get_database)) -> dict[str, str]:
    try:
        device = complete_device_enrollment(
            db,
            challenge_id=payload.challenge_id,
            secret=payload.secret,
            fingerprint=payload.fingerprint,
            label=payload.label,
            platform=payload.platform,
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"device_id": device.device_id, "user_id": device.user_id, "status": device.status}


def _actor(request: Request, db) -> str:
    """The caller's own user id, taken from their session context (never trusted input)."""
    token = bearer_token(request)
    context = build_context(db, token=token or "")
    return context.user_id


@router.post("/{device_id}/revoke")
def revoke(
    device_id: str, payload: RevokeRequest, request: Request, db=Depends(get_database)
) -> dict[str, int | str]:
    try:
        actor = _actor(request, db)
        result = revoke_device(db, device_id=device_id, reason=payload.reason, actor_user_id=actor)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return result


@router.post("/{device_id}/lost")
def lost(
    device_id: str, payload: RevokeRequest, request: Request, db=Depends(get_database)
) -> dict[str, str]:
    try:
        actor = _actor(request, db)
        status = mark_device_lost(
            db, device_id=device_id, reason=payload.reason, actor_user_id=actor
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"device_id": device_id, "status": status}


__all__ = ["router"]
