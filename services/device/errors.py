"""Device-layer errors (Wave 2 §十一 – §十六)."""

from __future__ import annotations


class DeviceError(Exception):
    """Base class for device-layer failures."""

    code = "device_error"


class DeviceValidationError(DeviceError):
    """The caller supplied an unusable value."""

    code = "device_validation_error"


class DeviceConflict(DeviceError):
    """The device already exists for this user (per-user fingerprint rules)."""

    code = "device_conflict"


class DeviceNotUsable(DeviceError):
    """The device is unknown, revoked, lost or untrusted for this operation."""

    code = "device_not_usable"


class ChallengeRejected(DeviceError):
    """The enrollment challenge is unknown, expired, consumed or mismatched.

    Coarse by design (§三十四 fail-closed); replay is denied because a consumed
    challenge is no longer live (§三十五).
    """

    code = "challenge_rejected"


__all__ = [
    "ChallengeRejected",
    "DeviceConflict",
    "DeviceError",
    "DeviceNotUsable",
    "DeviceValidationError",
]
