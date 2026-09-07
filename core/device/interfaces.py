"""Device contracts.

A device is a trusted endpoint belonging to an identity. Revocation is
explicit and irreversible: a revoked device can never authenticate again.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

DEVICE_STATUS = ("pending", "active", "revoked")


@dataclass(frozen=True)
class Device:
    id: str
    identity_id: str
    fingerprint: str
    label: str = ""
    status: str = "pending"
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@runtime_checkable
class DeviceRegistry(Protocol):
    def register(self, identity_id: str, fingerprint: str, label: str = "") -> Device:
        ...

    def get(self, device_id: str) -> Device | None:
        ...

    def list_for_identity(self, identity_id: str) -> list[Device]:
        ...

    def revoke(self, device_id: str) -> Device:
        ...


__all__ = ["DEVICE_STATUS", "Device", "DeviceRegistry"]
