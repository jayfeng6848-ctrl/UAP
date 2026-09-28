"""Wave 2 §四 / §七 / §八: Domain <-> persistence mapping must be explicit."""

from __future__ import annotations

import pytest

from services.mapping import (
    CREDENTIAL_TYPES,
    DEVICE_STATUSES,
    IDENTITY_STATUSES,
    USER_STATUSES,
    CredentialType,
    DeviceStatus,
    IdentityStatus,
    UnknownVocabularyValue,
    UserStatus,
    is_authenticatable_device,
    to_domain_credential_type,
    to_domain_device_status,
    to_persistence_credential_type,
    to_persistence_device_status,
    to_persistence_identity_status,
    to_persistence_user_status,
)


def test_domain_user_vocabulary_matches_persistence_truth() -> None:
    assert USER_STATUSES == ("pending", "active", "suspended", "locked", "deleted")
    assert IDENTITY_STATUSES == ("unverified", "active", "suspended", "revoked")
    assert DEVICE_STATUSES == ("pending", "active", "untrusted", "revoked", "lost")


def test_round_trip_is_lossless_for_every_persistence_value() -> None:
    for status in USER_STATUSES:
        assert to_persistence_user_status(UserStatus(status)) == status
    for status in IDENTITY_STATUSES:
        assert to_persistence_identity_status(IdentityStatus(status)) == status
    for status in DEVICE_STATUSES:
        assert to_persistence_device_status(DeviceStatus(status)) == status
        assert to_domain_device_status(status).value == status


def test_unknown_values_are_rejected_not_passed_through() -> None:
    with pytest.raises(UnknownVocabularyValue):
        to_domain_device_status("verified")  # never a persisted device state
    with pytest.raises(UnknownVocabularyValue):
        to_domain_credential_type("bearer")  # not in the frozen credential set
    with pytest.raises(UnknownVocabularyValue):
        to_persistence_user_status("onboarding")  # §十一 forbids new statuses


def test_credential_type_mapping_is_explicit_and_many_to_one() -> None:
    # Domain -> persisted (§七: only the frozen values may be written)
    assert to_persistence_credential_type(CredentialType.PASSWORD) == "password"
    assert to_persistence_credential_type(CredentialType.DEVICE) == "device_cert"
    assert to_persistence_credential_type(CredentialType.TOKEN) == "otp"
    # persisted -> Domain (recovery_code has no distinct Domain value)
    assert to_domain_credential_type("recovery_code") is CredentialType.TOKEN
    assert set(CREDENTIAL_TYPES) == {
        "password",
        "api_key",
        "recovery_code",
        "device_cert",
        "otp",
    }


def test_only_active_devices_are_authenticatable() -> None:
    assert is_authenticatable_device(DeviceStatus.ACTIVE) is True
    # untrusted is explicitly not active; lost is explicitly not revoked, but
    # neither may authenticate.
    for status in ("pending", "untrusted", "revoked", "lost"):
        assert is_authenticatable_device(status) is False
