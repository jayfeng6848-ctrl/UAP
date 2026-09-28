"""Explicit Domain <-> Persistence vocabulary mapping (P14 Wave 2).

The Wave 2 Human decision (PDL Appendix P) is:

    EXISTING 0017 SCHEMA = PERSISTENCE TRUTH
    DOMAIN SEMANTICS     = EXPLICIT DOMAIN / INFRASTRUCTURE MAPPING

Domain vocabulary and the persisted vocabulary may therefore differ, but every
crossing is an explicit, deterministic, testable mapping in
:mod:`services.mapping.vocabulary`. There are no implicit casts, no magic-string
states, and no vocabulary translation inside handlers or repositories.
"""

from .errors import UnknownVocabularyValue, VocabularyMappingError
from .vocabulary import (
    CREDENTIAL_ALGORITHMS,
    CREDENTIAL_TYPES,
    DEVICE_STATUSES,
    IDENTITY_PROVIDERS,
    IDENTITY_STATUSES,
    SESSION_STATUSES,
    USER_STATUSES,
    CredentialAlgorithm,
    CredentialType,
    DeviceStatus,
    IdentityProvider,
    IdentityStatus,
    SessionStatus,
    UserStatus,
    is_authenticatable_device,
    to_domain_credential_algorithm,
    to_domain_credential_type,
    to_domain_device_status,
    to_domain_identity_status,
    to_domain_session_status,
    to_domain_user_status,
    to_persistence_credential_algorithm,
    to_persistence_credential_type,
    to_persistence_device_status,
    to_persistence_identity_provider,
    to_persistence_identity_status,
    to_persistence_session_status,
    to_persistence_user_status,
)

__all__ = [
    "CREDENTIAL_ALGORITHMS",
    "CREDENTIAL_TYPES",
    "DEVICE_STATUSES",
    "IDENTITY_PROVIDERS",
    "IDENTITY_STATUSES",
    "SESSION_STATUSES",
    "USER_STATUSES",
    "CredentialAlgorithm",
    "CredentialType",
    "DeviceStatus",
    "IdentityProvider",
    "IdentityStatus",
    "SessionStatus",
    "UnknownVocabularyValue",
    "UserStatus",
    "VocabularyMappingError",
    "is_authenticatable_device",
    "to_domain_credential_algorithm",
    "to_domain_credential_type",
    "to_domain_device_status",
    "to_domain_identity_status",
    "to_domain_session_status",
    "to_domain_user_status",
    "to_persistence_credential_algorithm",
    "to_persistence_credential_type",
    "to_persistence_device_status",
    "to_persistence_identity_provider",
    "to_persistence_identity_status",
    "to_persistence_session_status",
    "to_persistence_user_status",
]
