"""P18 control-plane endpoints (transport only · dedicated namespace).

Structural lifecycle lives behind ``/control/...`` — never inside the P17 runtime
namespace, never a generic CRUD surface and never a physical DELETE endpoint.
The handler authenticates the actor, calls one use case and maps the result; all
authorization happens inside the use case through the canonical service.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from apps.api.dependencies import bearer_token, get_control_database, get_database
from apps.api.error_mapping import translate
from services.use_cases import (
    authenticate_actor,
    provision_space,
    provision_tenant,
    read_space,
    read_tenant,
    transition_space,
    transition_tenant,
    update_space_metadata,
    update_tenant_metadata,
)

router = APIRouter(prefix="/control", tags=["control-plane"])


class TenantProvisionRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=63)
    display_name: str = Field(min_length=1)
    initial_admin_user_id: str = Field(min_length=1)


class TenantMetadataRequest(BaseModel):
    display_name: str | None = None
    plan: str | None = None
    region: str | None = None


class LifecycleRequest(BaseModel):
    state: str = Field(min_length=1)


class SpaceProvisionRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    key: str = Field(min_length=2)
    name: str = Field(min_length=1)
    initial_space_admin_user_id: str = Field(min_length=1)
    kind: str = "team"
    visibility: str = "tenant"


class SpaceMetadataRequest(BaseModel):
    name: str | None = None
    visibility: str | None = None
    owner_id: str | None = None


def _actor(app_db, request: Request):
    # Authentication runs on the application identity boundary (F-P18-I-04 option ①).
    try:
        return authenticate_actor(app_db, token=bearer_token(request) or "")
    except Exception as exc:  # noqa: BLE001 - translated, never echoed
        raise translate(exc) from exc


def _correlation(request: Request) -> str | None:
    return request.headers.get("x-correlation-id")


# ----------------------------------------------------------------- tenants
@router.post("/tenants", status_code=201)
def create_tenant(
    payload: TenantProvisionRequest, request: Request, app_db=Depends(get_database), db=Depends(get_control_database)
) -> dict[str, Any]:
    actor = _actor(app_db, request)
    try:
        result = provision_tenant(
            db, actor_id=actor.user_id, slug=payload.slug, display_name=payload.display_name,
            initial_admin_user_id=payload.initial_admin_user_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "tenant_id": result.tenant_id, "slug": result.slug, "status": result.status,
        "admin_role_id": result.admin_role_id, "membership_id": result.membership_id,
        "replayed": result.replayed,
    }


@router.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: str, request: Request, app_db=Depends(get_database), db=Depends(get_control_database)) -> dict[str, Any]:
    actor = _actor(app_db, request)
    try:
        return read_tenant(db, actor_id=actor.user_id, tenant_id=tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc


@router.patch("/tenants/{tenant_id}")
def patch_tenant(
    tenant_id: str, payload: TenantMetadataRequest, request: Request, app_db=Depends(get_database), db=Depends(get_control_database)
) -> dict[str, str]:
    actor = _actor(app_db, request)
    try:
        update_tenant_metadata(
            db, actor_id=actor.user_id, tenant_id=tenant_id, display_name=payload.display_name,
            plan=payload.plan, region=payload.region, correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"tenant_id": tenant_id, "status": "updated"}


@router.post("/tenants/{tenant_id}/lifecycle")
def post_tenant_lifecycle(
    tenant_id: str, payload: LifecycleRequest, request: Request, app_db=Depends(get_database), db=Depends(get_control_database)
) -> dict[str, str]:
    actor = _actor(app_db, request)
    try:
        state = transition_tenant(
            db, actor_id=actor.user_id, tenant_id=tenant_id, target_state=payload.state,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"tenant_id": tenant_id, "status": state}


# ------------------------------------------------------------------ spaces
@router.post("/spaces", status_code=201)
def create_space(
    payload: SpaceProvisionRequest, request: Request, app_db=Depends(get_database), db=Depends(get_control_database)
) -> dict[str, Any]:
    actor = _actor(app_db, request)
    try:
        result = provision_space(
            db, actor_id=actor.user_id, tenant_id=payload.tenant_id, key=payload.key,
            name=payload.name, initial_space_admin_user_id=payload.initial_space_admin_user_id,
            kind=payload.kind, visibility=payload.visibility,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {
        "space_id": result.space_id, "tenant_id": result.tenant_id, "key": result.key,
        "status": result.status, "admin_role_id": result.admin_role_id,
        "membership_id": result.membership_id, "replayed": result.replayed,
    }


@router.get("/tenants/{tenant_id}/spaces/{space_id}")
def get_space(
    tenant_id: str, space_id: str, request: Request, app_db=Depends(get_database), db=Depends(get_control_database)
) -> dict[str, Any]:
    actor = _actor(app_db, request)
    try:
        return read_space(db, actor_id=actor.user_id, tenant_id=tenant_id, space_id=space_id)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc


@router.patch("/tenants/{tenant_id}/spaces/{space_id}")
def patch_space(
    tenant_id: str, space_id: str, payload: SpaceMetadataRequest, request: Request,
    app_db=Depends(get_database),
    db=Depends(get_control_database),
) -> dict[str, str]:
    actor = _actor(app_db, request)
    try:
        update_space_metadata(
            db, actor_id=actor.user_id, tenant_id=tenant_id, space_id=space_id,
            name=payload.name, visibility=payload.visibility, owner_id=payload.owner_id,
            correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"space_id": space_id, "status": "updated"}


@router.post("/tenants/{tenant_id}/spaces/{space_id}/lifecycle")
def post_space_lifecycle(
    tenant_id: str, space_id: str, payload: LifecycleRequest, request: Request,
    app_db=Depends(get_database),
    db=Depends(get_control_database),
) -> dict[str, str]:
    actor = _actor(app_db, request)
    try:
        state = transition_space(
            db, actor_id=actor.user_id, tenant_id=tenant_id, space_id=space_id,
            target_state=payload.state, correlation_id=_correlation(request),
        )
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return {"space_id": space_id, "status": state}


__all__ = ["router"]
