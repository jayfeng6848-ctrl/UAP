"""Device enrollment / revoke service (P14 Wave 2, W2-AUTH-02)."""

from .errors import (
    ChallengeRejected,
    DeviceConflict,
    DeviceError,
    DeviceNotUsable,
    DeviceValidationError,
)
from .repository import DEVICE_COLUMNS, DeviceRepository
from .service import (
    CHALLENGE_CREDENTIAL_TYPE,
    CHALLENGE_TTL_SECONDS,
    DeviceService,
    EnrolledDevice,
    EnrollmentChallenge,
)

__all__ = [
    "CHALLENGE_CREDENTIAL_TYPE",
    "CHALLENGE_TTL_SECONDS",
    "ChallengeRejected",
    "DEVICE_COLUMNS",
    "DeviceConflict",
    "DeviceError",
    "DeviceNotUsable",
    "DeviceRepository",
    "DeviceService",
    "DeviceValidationError",
    "EnrolledDevice",
    "EnrollmentChallenge",
]
