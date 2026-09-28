"""Identity / credential use-cases (Wave 2 §五 – §十, §三十三, §四十二).

The service is **session-scoped**: the use-case (API adapter or orchestration)
opens ``RuntimeDatabase.transaction()`` and hands the session down. The service
never commits and never rolls back — the transaction boundary stays where Wave 1
put it.

Vocabulary never crosses the boundary implicitly: every status written here is
produced by :mod:`services.mapping`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from services.mapping import (
    CredentialType,
    IdentityProvider,
    IdentityStatus,
    UserStatus,
    to_persistence_credential_algorithm,
    to_persistence_credential_type,
    to_persistence_identity_provider,
    to_persistence_identity_status,
    to_persistence_user_status,
)
from services.session.repository import SessionRepository

from .errors import (
    CredentialRejected,
    IdentityNotUsable,
    IdentityValidationError,
)
from .hashing import PasswordHasher
from .repository import IdentityRepository

#: Bounded failure policy (§九): after ``MAX_FAILED_ATTEMPTS`` consecutive
#: failures the credential is locked for ``LOCK_SECONDS``. No new counter table.
MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 900


@dataclass(frozen=True)
class OnboardedIdentity:
    """Result of onboarding; carries identifiers only, never secrets."""

    user_id: str
    identity_id: str
    credential_id: str
    user_status: str
    identity_status: str


@dataclass(frozen=True)
class AuthenticatedIdentity:
    """Proof of authentication — evidence for the context, not an authority."""

    user_id: str
    identity_id: str
    credential_id: str
    activated: bool


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IdentityService:
    """Identity, credential and verification rules for Wave 2."""

    def __init__(self, session: Session) -> None:
        self._repo = IdentityRepository(session)
        self._sessions = SessionRepository(session)

    # -------------------------------------------------------------- onboarding
    def onboard(
        self,
        *,
        email: str | None = None,
        username: str | None = None,
        display_name: str | None = None,
        password: str,
        provider: IdentityProvider = IdentityProvider.LOCAL,
    ) -> OnboardedIdentity:
        """Create ``users`` + ``identities`` + ``credentials`` in ONE use-case.

        Status mapping per §十一: ``users.status = pending`` and
        ``identities.status = unverified`` at creation. "verification in
        progress" is *not* a persisted state.
        """
        email = (email or "").strip() or None
        username = (username or "").strip() or None
        if not email and not username:
            raise IdentityValidationError("email or username is required")
        if not password:
            raise IdentityValidationError("password is required")

        user_status = to_persistence_user_status(UserStatus.PENDING)
        identity_status = to_persistence_identity_status(IdentityStatus.UNVERIFIED)

        user_id = self._repo.insert_user(
            email=email, username=username, display_name=display_name, status=user_status
        )
        identity_id = self._repo.insert_identity(
            user_id=user_id,
            provider=to_persistence_identity_provider(provider),
            subject=email or username or user_id,
            email=email,
            display_name=display_name,
            status=identity_status,
        )
        credential_id = self._repo.insert_credential(
            identity_id=identity_id,
            user_id=user_id,
            credential_type=to_persistence_credential_type(CredentialType.PASSWORD),
            secret_hash=PasswordHasher.hash(password),
            algorithm=to_persistence_credential_algorithm(PasswordHasher.algorithm),
            expires_at=None,
        )
        return OnboardedIdentity(
            user_id=user_id,
            identity_id=identity_id,
            credential_id=credential_id,
            user_status=user_status,
            identity_status=identity_status,
        )

    # ------------------------------------------------------------ verification
    def verify_identity(self, identity_id: str, *, activate_user: bool = True) -> None:
        """``unverified -> active`` (one-time; idempotent for an active identity)."""
        identity = self._repo.get_identity(identity_id)
        if identity is None:
            raise IdentityNotUsable("unknown identity")
        status = str(identity._mapping["status"])
        if status == IdentityStatus.REVOKED.value:
            raise IdentityNotUsable("identity is revoked")
        if status != IdentityStatus.ACTIVE.value:
            self._repo.set_identity_status(
                identity_id, to_persistence_identity_status(IdentityStatus.ACTIVE), verified=True
            )
        if activate_user:
            user = self._repo.get_user(str(identity._mapping["user_id"]))
            if user is not None and str(user._mapping["status"]) == UserStatus.PENDING.value:
                self._repo.set_user_status(
                    str(identity._mapping["user_id"]),
                    to_persistence_user_status(UserStatus.ACTIVE),
                )

    # ---------------------------------------------------------- authentication
    def authenticate(
        self, *, login: str, password: str
    ) -> AuthenticatedIdentity:
        """Verify a local password credential. Every failure denies (§三十四)."""
        if not login or not password:
            raise CredentialRejected("authentication failed")

        user = self._repo.find_user_by_login(login.strip())
        if user is None:
            raise CredentialRejected("authentication failed")

        user_id = str(user._mapping["id"])
        user_status = str(user._mapping["status"])
        locked_until = user._mapping["locked_until"]
        if user_status in (UserStatus.SUSPENDED.value, UserStatus.LOCKED.value,
                           UserStatus.DELETED.value):
            raise CredentialRejected("authentication failed")
        if locked_until is not None and locked_until > _now():
            raise CredentialRejected("authentication failed")

        identity = self._repo.get_local_identity_for_user(
            user_id, to_persistence_identity_provider(IdentityProvider.LOCAL)
        )
        if identity is None:
            raise CredentialRejected("authentication failed")
        identity_id = str(identity._mapping["id"])
        identity_status = str(identity._mapping["status"])
        # Fail closed for every state that is not usable: only an active identity
        # (or the unverified one that this very check may verify) may proceed.
        if identity_status not in (
            IdentityStatus.ACTIVE.value,
            IdentityStatus.UNVERIFIED.value,
        ):
            raise CredentialRejected("authentication failed")

        credential = self._repo.get_live_credential(
            identity_id,
            credential_type=to_persistence_credential_type(CredentialType.PASSWORD),
        )
        if credential is None:
            raise CredentialRejected("authentication failed")
        credential_id = str(credential._mapping["id"])
        cred_locked = credential._mapping["locked_until"]
        if cred_locked is not None and cred_locked > _now():
            raise CredentialRejected("authentication failed")
        attempts_so_far = int(credential._mapping["failed_attempts"])
        if attempts_so_far >= MAX_FAILED_ATTEMPTS:
            raise CredentialRejected("authentication failed")

        if not PasswordHasher.verify(str(credential._mapping["secret_hash"]), password):
            # Bounded failure policy (§九): count every failure; lock only when
            # the bound is reached, so a single typo does not lock the account.
            attempts = attempts_so_far + 1
            lock_at = (
                _now() + timedelta(seconds=LOCK_SECONDS)
                if attempts >= MAX_FAILED_ATTEMPTS
                else None
            )
            self._repo.record_credential_failure(credential_id, locked_until=lock_at)
            self._repo.register_user_failure(user_id, locked_until=lock_at)
            raise CredentialRejected("authentication failed")

        self._repo.clear_credential_failures(credential_id)
        self._repo.clear_user_failures(user_id)

        activated = False
        if identity_status == IdentityStatus.UNVERIFIED.value:
            # First successful credential check *is* the verification for a local
            # password identity (§十); it is one-time and fail-closed.
            self.verify_identity(identity_id, activate_user=True)
            activated = True

        return AuthenticatedIdentity(
            user_id=user_id,
            identity_id=identity_id,
            credential_id=credential_id,
            activated=activated,
        )

    # ------------------------------------------------------ credential lifecycle
    def issue_credential(self, *, identity_id: str, password: str) -> str:
        if not password:
            raise IdentityValidationError("password is required")
        identity = self._repo.get_identity(identity_id)
        if identity is None:
            raise IdentityNotUsable("unknown identity")
        return self._repo.insert_credential(
            identity_id=identity_id,
            user_id=str(identity._mapping["user_id"]),
            credential_type=to_persistence_credential_type(CredentialType.PASSWORD),
            secret_hash=PasswordHasher.hash(password),
            algorithm=to_persistence_credential_algorithm(PasswordHasher.algorithm),
            expires_at=None,
        )

    def rotate_credential(self, *, identity_id: str, new_password: str) -> str:
        """Revoke the old row, then insert the new one — never a physical DELETE (§八).

        Order matters: ``uq_credentials_active_password`` allows at most one
        active password credential per identity, so the old row must be revoked
        **before** the replacement is inserted (both inside the caller's
        transaction, so the pair is atomic).
        """
        current = self._repo.get_live_credential(
            identity_id,
            credential_type=to_persistence_credential_type(CredentialType.PASSWORD),
        )
        if current is not None:
            self._repo.mark_credential_rotated(str(current._mapping["id"]))
        return self.issue_credential(identity_id=identity_id, password=new_password)

    def revoke_credential(self, *, credential_id: str) -> int:
        return self._repo.consume_challenge(credential_id)

    # ------------------------------------------------------------- revocation
    def revoke_identity(self, *, identity_id: str, reason: str) -> dict[str, int]:
        """``identity revoked`` + credentials revoked + sessions revoked, atomically.

        Propagation matrix = ID-W2-05 (PDL Appendix P): identity revoke revokes
        the related active sessions **in the same transaction**. Device rows are
        deliberately not rewritten (§八 keeps the device states independent).
        """
        identity = self._repo.get_identity(identity_id)
        if identity is None:
            raise IdentityNotUsable("unknown identity")
        self._repo.set_identity_status(
            identity_id, to_persistence_identity_status(IdentityStatus.REVOKED), revoked=True
        )
        credentials = self._repo.revoke_credentials_for_identity(identity_id)
        sessions = self._sessions.revoke_for_identity(identity_id, reason=reason)
        return {"credentials": credentials, "sessions": sessions}


__all__ = [
    "LOCK_SECONDS",
    "MAX_FAILED_ATTEMPTS",
    "AuthenticatedIdentity",
    "IdentityService",
    "OnboardedIdentity",
]
