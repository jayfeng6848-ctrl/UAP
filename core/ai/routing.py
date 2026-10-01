"""Routing contract: Task -> Capability -> Policy -> Route -> Provider -> Model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteRequest:
    """What the caller wants (no credentials, no vendor detail)."""

    capability: str
    classification: str
    require_private: bool = False
    tenant_id: str | None = None
    space_id: str | None = None
    provider_key: str | None = None
    model_key: str | None = None


@dataclass(frozen=True)
class RouteDecision:
    """A deterministic resolution result (fallback is explicit, never implicit)."""

    route_id: str
    provider_id: str
    model_id: str
    capability: str
    classification: str
    fallback_used: bool = False
    fallback_index: int = 0
