"""Device enrollment / revoke use-cases (Wave 2 §十一 – §十六, §四十二).

Challenge carrier (DV-W2-03 = A, PDL Appendix P): the **existing schema** is
used — a ``credentials`` row of ``type='otp'``. No ``device_challenges`` table is
created (§十四). The challenge is:

* bound to the device fingerprint by hashing ``secret + "\\n" + fingerprint``,
* short-lived (``expires_at``) and explicitly consumed (``revoked_at``), so a
  replayed or expired challenge is simply no longer live (§三十五),
* never stored in plaintext.

Everything is session-scoped; the use-case owns COMMIT/ROLLBACK.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from services.identity.errors import IdentityNotUsable
from services.identity.hashing import PasswordHasher, new_token
from services.identity.repository import IdentityRepository
from services.mapping import (
    CredentialAlgorithm,
    DeviceStatus,
    IdentityStatus,
    is_authenticatable_device,
    to_persistence_credential_algorithm,
    to_persistence_device_status,
)
from services.session.repository import SessionRepository

from .errors import (
    ChallengeRejected,
    DeviceConflict,
    DeviceNotUsable,
    DeviceValidationError,
)
from .repository import DeviceRepository

#: Challenge lifetime and carrier vocabulary.
CHALLENGE_TTL_SECONDS = 900
CHALLENGE_CREDENTIAL_TYPE = "otp"


@dataclass(frozen=True)
class EnrollmentChallenge:
    """One-time enrollment material. The secret is returned exactly once."""

    challenge_id: str
    secret: str
    expires_at: datetime


@dataclass(frozen=True)
class EnrolledDevice:
    device_id: str
    user_id: str
    status: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _challenge_material(secret: str, fingerprint: str) -> str:
    return f"{secret}\n{fingerprint}"


class DeviceService:
    """Device enrollment, trust state and revocation."""

    def __init__(self, session: Session) -> None:
        self._devices = DeviceRepository(session)
        self._identities = IdentityRepository(session)
        self._sessions = SessionRepository(session)

    # ------------------------------------------------------------- enrollment
    def start_enrollment(
        self, *, user_id: str, identity_id: str, fingerprint: str, label: str | None = None
    ) -> EnrollmentChallenge:
        """Issue a one-time challenge for an **active** identity (§十三)."""
        fingerprint = (fingerprint or "").strip()
        if not fingerprint:
            raise DeviceValidationError("fingerprint is required")

        identity = self._identities.get_identity(identity_id)
        if identity is None or str(identity._mapping["user_id"]) != user_id:
            raise IdentityNotUsable("unknown identity for this user")
        if str(identity._mapping["status"]) != IdentityStatus.ACTIVE.value:
            raise IdentityNotUsable("identity is not active")

        if self._devices.find_for_user_fingerprint(user_id, fingerprint) is not None:
            raise DeviceConflict("device already enrolled for this user")

        secret = new_token()
        expires_at = _now() + timedelta(seconds=CHALLENGE_TTL_SECONDS)
        challenge_id = self._identities.insert_credential(
            identity_id=identity_id,
            user_id=user_id,
            credential_type=CHALLENGE_CREDENTIAL_TYPE,
            secret_hash=PasswordHasher.hash(_challenge_material(secret, fingerprint)),
            algorithm=to_persistence_credential_algorithm(CredentialAlgorithm.ARGON2ID),
            expires_at=expires_at,
        )
        return EnrollmentChallenge(challenge_id=challenge_id, secret=secret, expires_at=expires_at)

    def verify_enrollment(
        self,
        *,
        challenge_id: str,
        secret: str,
        fingerprint: str,
        label: str | None = None,
        platform: str | None = None,
    ) -> EnrolledDevice:
        """Consume the challenge, then create the device ``pending -> active``.

        The device row is **never inserted directly as ``active``** (§11.1).
        """
        if not challenge_id or not secret or not fingerprint:
            raise ChallengeRejected("enrollment challenge rejected")

        credential = self._identities.get_credential(challenge_id)
        if credential is None:
            raise ChallengeRejected("enrollment challenge rejected")
        mapping = credential._mapping
        if str(mapping["type"]) != CHALLENGE_CREDENTIAL_TYPE:
            raise ChallengeRejected("enrollment challenge rejected")
        if mapping["revoked_at"] is not None:
            raise ChallengeRejected("enrollment challenge rejected")  # replay denied
        if mapping["expires_at"] is not None and mapping["expires_at"] <= _now():
            raise ChallengeRejected("enrollment challenge rejected")  # expiry denied
        if not PasswordHasher.verify(
            str(mapping["secret_hash"]), _challenge_material(secret, fingerprint)
        ):
            raise ChallengeRejected("enrollment challenge rejected")  # wrong user/fingerprint

        if self._identities.consume_challenge(challenge_id) != 1:
            # somebody consumed it concurrently -> explicit one-time use only
            raise ChallengeRejected("enrollment challenge rejected")

        user_id = str(mapping["user_id"])
        device_id = self._devices.insert_device(
            user_id=user_id,
            fingerprint=fingerprint,
            label=label,
            platform=platform,
            status=to_persistence_device_status(DeviceStatus.PENDING),
        )
        self._devices.set_status(
            device_id, to_persistence_device_status(DeviceStatus.ACTIVE)
        )
        return EnrolledDevice(
            device_id=device_id,
            user_id=user_id,
            status=to_persistence_device_status(DeviceStatus.ACTIVE),
        )

    # ------------------------------------------------------------ trust states
    def get(self, device_id: str) -> dict[str, object]:
        device = self._devices.get_device(device_id)
        if device is None:
            raise DeviceNotUsable("unknown device")
        return dict(device._mapping)

    def is_authenticatable(self, device_id: str) -> bool:
        device = self._devices.get_device(device_id)
        if device is None:
            return False
        return is_authenticatable_device(str(device._mapping["status"]))

    def mark_lost(self, device_id: str, *, reason: str = "reported_lost") -> str:
        """``lost`` is its own state — never a synonym for ``revoked`` (§十六)."""
        self._devices.set_status(
            device_id, to_persistence_device_status(DeviceStatus.LOST), reason=reason
        )
        return DeviceStatus.LOST.value

    def mark_untrusted(self, device_id: str, *, reason: str = "trust_verification_failed") -> str:
        self._devices.set_status(
            device_id, to_persistence_device_status(DeviceStatus.UNTRUSTED), reason=reason
        )
        return DeviceStatus.UNTRUSTED.value

    def reactivate(self, device_id: str, *, verification_completed: bool) -> str:
        """``untrusted/lost -> active`` requires **explicit** verification.

        There is deliberately no automatic recovery path (§十二 / §十六). Without
        ``verification_completed=True`` this refuses.
        """
        if not verification_completed:
            raise DeviceNotUsable("explicit trust verification is required")
        current = self._devices.get_device(device_id)
        if current is None:
            raise DeviceNotUsable("unknown device")
        if str(current._mapping["status"]) == DeviceStatus.REVOKED.value:
            raise DeviceNotUsable("a revoked device can never be reactivated")
        self._devices.set_status(device_id, to_persistence_device_status(DeviceStatus.ACTIVE))
        return DeviceStatus.ACTIVE.value

    # ----------------------------------------------------------------- revoke
    def revoke_device(self, *, device_id: str, reason: str = "device_revoked") -> dict[str, int | str]:
        """``device revoked`` + **all its active sessions revoked**, in ONE transaction.

        DV-W2-04 / SEC-W2-04: committing the device revoke first and cleaning up
        sessions later would open a security window, so both writes happen inside
        the caller's transaction.
        """
        device = self._devices.get_device(device_id)
        if device is None:
            raise DeviceNotUsable("unknown device")
        self._devices.set_status(
            device_id,
            to_persistence_device_status(DeviceStatus.REVOKED),
            reason=reason,
            revoke=True,
        )
        revoked_sessions = self._sessions.revoke_for_device(device_id, reason=reason)
        return {"device_status": DeviceStatus.REVOKED.value, "sessions_revoked": revoked_sessions}


__all__ = [
    "CHALLENGE_CREDENTIAL_TYPE",
    "CHALLENGE_TTL_SECONDS",
    "DeviceService",
    "EnrolledDevice",
    "EnrollmentChallenge",
]
