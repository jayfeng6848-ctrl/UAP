"""Platform metadata endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from config.settings import get_settings
from core import CORE_MODULES
from domains import list_domains

router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get("/meta", summary="Platform metadata")
def meta() -> dict:
    """Return what this deployment is and which placeholders exist."""
    settings = get_settings()
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "phase": "PHASE-0 / PROJECT-INITIALIZATION",
        "core_modules": list(CORE_MODULES),
        "domains": [
            {
                "domain_id": manifest["domain_id"],
                "version": manifest["version"],
                "status": manifest["status"],
            }
            for manifest in list_domains()
        ],
    }


__all__ = ["router"]
