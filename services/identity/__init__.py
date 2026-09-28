"""Identity / credential service (P14 Wave 2, W2-AUTH-01)."""

from .errors import (
    CredentialRejected,
    IdentityConflict,
    IdentityError,
    IdentityNotUsable,
    IdentityValidationError,
)
from .hashing import PasswordHasher, hash_token, new_token, verify_token
from .repository import IdentityRepository
from .service import (
    LOCK_SECONDS,
    MAX_FAILED_ATTEMPTS,
    AuthenticatedIdentity,
    IdentityService,
    OnboardedIdentity,
)

__all__ = [
    "LOCK_SECONDS",
    "MAX_FAILED_ATTEMPTS",
    "AuthenticatedIdentity",
    "CredentialRejected",
    "IdentityConflict",
    "IdentityError",
    "IdentityNotUsable",
    "IdentityRepository",
    "IdentityService",
    "IdentityValidationError",
    "OnboardedIdentity",
    "PasswordHasher",
    "hash_token",
    "new_token",
    "verify_token",
]
