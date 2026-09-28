"""Secret hashing primitives for Wave 2.

Two different secret classes with different requirements:

* **low-entropy human passwords** -> ``PasswordHasher`` (Argon2id, memory-hard).
  Wave 2 §八 requires Argon2id for the ``password`` credential type.
* **high-entropy machine tokens** (session bearer tokens, enrollment challenge
  secrets) -> SHA-256. These are 256-bit random values, so a memory-hard KDF
  adds cost per request without adding meaningful resistance; the stored value
  is still a one-way hash, never the secret itself.

Nothing in this module logs, returns or stores a plaintext secret.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher as _Argon2Hasher
from argon2 import Type as _Argon2Type
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from services.mapping import CredentialAlgorithm

#: Argon2id with the library defaults (RFC 9106 profile); ``Algorithm`` column
#: value persisted for every hash produced here.
ALGORITHM = CredentialAlgorithm.ARGON2ID

_hasher = _Argon2Hasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=_Argon2Type.ID,
)

TOKEN_BYTES = 32


class PasswordHasher:
    """Argon2id hashing for human passwords."""

    algorithm = ALGORITHM

    @staticmethod
    def hash(plaintext: str) -> str:
        if not plaintext:
            raise ValueError("refusing to hash an empty password")
        return _hasher.hash(plaintext)

    @staticmethod
    def verify(stored_hash: str, plaintext: str) -> bool:
        """Constant-time verification; never raises for a wrong password."""
        if not stored_hash or not plaintext:
            return False
        try:
            return _hasher.verify(stored_hash, plaintext)
        except (VerifyMismatchError, InvalidHashError, ValueError):
            return False
        except Exception:  # noqa: BLE001 - any failure is a failed verification
            return False

    @staticmethod
    def needs_rehash(stored_hash: str) -> bool:
        try:
            return _hasher.check_needs_rehash(stored_hash)
        except Exception:  # noqa: BLE001
            return True


def new_token() -> str:
    """A fresh high-entropy bearer / challenge secret (URL-safe)."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """One-way hash for a high-entropy token (stored in ``*_token_hash``)."""
    if not token:
        raise ValueError("refusing to hash an empty token")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(stored_hash: str, token: str) -> bool:
    if not stored_hash or not token:
        return False
    return hmac.compare_digest(stored_hash, hash_token(token))


__all__ = [
    "ALGORITHM",
    "TOKEN_BYTES",
    "PasswordHasher",
    "hash_token",
    "new_token",
    "verify_token",
]
