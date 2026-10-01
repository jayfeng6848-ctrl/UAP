"""P17 identity / tenant / space endpoints (D10 = C · transport only).

The handler authenticates the actor from the bearer session, takes the **target**
from the path (never from a header, never from a first-row guess), calls one use
case and maps the result. It contains no SQL, no role comparison and no
``is_admin`` shortcut: every administrative decision happens inside the use case
through the canonical authorization service.

IN : tenant read · space read · tenant membership read/write · space membership read/write
OUT: tenant/space create/update/delete · platform membership · role / permission / ACL admin
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_database
from apps.api.error_mapping import translate
from services.use_cases import (
    authenticate_actor,
    create_space_membership,
    create_tenant_membership,
    delete_space_membership,
    delete_tenant_membership,
    get_tenant,
    list_space_members,
    list_spaces,
    list_tenant_members,
    list_tenants,
    update_space_membership,
    update_tenant_membership,
)

router = APIRouter(tags=["identity-runtime"])


class MembershipWriteRequest(BaseModel):
    """Role change for an existing membership (the target comes from the path)."""

    role_id: str = Field(min_length=1)


class MembershipCreateRequest(BaseModel):
    """New membership: the target user and the role are both explicit."""

    user_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)


def _actor(db, request: Request):
    """Authenticated actor from the bearer session; the target scope is the path.

    No tenant/space is derived from the session or from a header (P17 §44): the
    request path names the target, and the use case decides whether the actor
    may act there. The session check reuses the frozen Wave 2 service.
    """
    try:
        return authenticate_actor(db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001 - translated, never echoed
        raise translate(exc) from exc


def _correlation(request: Request) -> str | None:
    return request.headers.get("x-correlation-id")


def _clean(row: dict[str, Any]) -> dict[str, Any]:
    """JSON-safe projection of a storage row (no ORM object escapes the route)."""
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, uuid.UUID):
            out[key] = str(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


# ------------------------------------------------------------------ structure
@router.get("/tenants")
def list_visible_tenants(request: Request, db=Depends(get_database)) -> dict[str, Any]:
    actor = _actor(db, request)
    try:
        rows = list_tenants(db, actor_id=actor.user_id, actor_type=actor.subject_type)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"items": [_clean(row) for row in rows], "count": len(rows)}


@router.get("/tenants/{tenant_id}")
def read_tenant(tenant_id: str, request: Request, db=Depends(get_database)) -> dict[str, Any]:
    actor = _actor(db, request)
    try:
        row = get_tenant(
            db, actor_id=actor.user_id, tenant_id=tenant_id, actor_type=actor.subject_type
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return _clean(row)


@router.get("/tenants/{tenant_id}/spaces")
def list_tenant_spaces(
    tenant_id: str, request: Request, db=Depends(get_database)
) -> dict[str, Any]:
    actor = _actor(db, request)
    try:
        rows = list_spaces(
            db, actor_id=actor.user_id, tenant_id=tenant_id, actor_type=actor.subject_type
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"items": [_clean(row) for row in rows], "count": len(rows)}


# --------------------------------------------------------- tenant membership
@router.get("/tenants/{tenant_id}/members")
def list_members(tenant_id: str, request: Request, db=Depends(get_database)) -> dict[str, Any]:
    actor = _actor(db, request)
    try:
        rows = list_tenant_members(
            db, actor_id=actor.user_id, tenant_id=tenant_id, actor_type=actor.subject_type
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"items": [_clean(row) for row in rows], "count": len(rows)}


@router.post("/tenants/{tenant_id}/members", status_code=201)
def add_member(
    tenant_id: str, payload: MembershipCreateRequest, request: Request, db=Depends(get_database)
) -> dict[str, str]:
    actor = _actor(db, request)
    try:
        membership_id = create_tenant_membership(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            user_id=payload.user_id,
            role_id=payload.role_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"membership_id": membership_id}


@router.patch("/tenants/{tenant_id}/members/{user_id}")
def change_member(
    tenant_id: str,
    user_id: str,
    payload: MembershipWriteRequest,
    request: Request,
    db=Depends(get_database),
) -> dict[str, str]:
    actor = _actor(db, request)
    try:
        update_tenant_membership(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=payload.role_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"user_id": user_id, "role_id": payload.role_id}


@router.delete("/tenants/{tenant_id}/members/{user_id}", status_code=204)
def remove_member(
    tenant_id: str, user_id: str, request: Request, db=Depends(get_database)
) -> Response:
    actor = _actor(db, request)
    try:
        delete_tenant_membership(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return Response(status_code=204)


# ---------------------------------------------------------- space membership
@router.get("/tenants/{tenant_id}/spaces/{space_id}/members")
def list_space_member_rows(
    tenant_id: str, space_id: str, request: Request, db=Depends(get_database)
) -> dict[str, Any]:
    actor = _actor(db, request)
    try:
        rows = list_space_members(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            space_id=space_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"items": [_clean(row) for row in rows], "count": len(rows)}


@router.post("/tenants/{tenant_id}/spaces/{space_id}/members", status_code=201)
def add_space_member(
    tenant_id: str,
    space_id: str,
    payload: MembershipCreateRequest,
    request: Request,
    db=Depends(get_database),
) -> dict[str, str]:
    actor = _actor(db, request)
    try:
        membership_id = create_space_membership(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            space_id=space_id,
            user_id=payload.user_id,
            role_id=payload.role_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"membership_id": membership_id}


@router.patch("/tenants/{tenant_id}/spaces/{space_id}/members/{user_id}")
def change_space_member(
    tenant_id: str,
    space_id: str,
    user_id: str,
    payload: MembershipWriteRequest,
    request: Request,
    db=Depends(get_database),
) -> dict[str, str]:
    actor = _actor(db, request)
    try:
        update_space_membership(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            space_id=space_id,
            user_id=user_id,
            role_id=payload.role_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"user_id": user_id, "role_id": payload.role_id}


@router.delete("/tenants/{tenant_id}/spaces/{space_id}/members/{user_id}", status_code=204)
def remove_space_member(
    tenant_id: str,
    space_id: str,
    user_id: str,
    request: Request,
    db=Depends(get_database),
) -> Response:
    actor = _actor(db, request)
    try:
        delete_space_membership(
            db,
            actor_id=actor.user_id,
            actor_type=actor.subject_type,
            tenant_id=tenant_id,
            space_id=space_id,
            user_id=user_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return Response(status_code=204)


__all__ = ["router"]
