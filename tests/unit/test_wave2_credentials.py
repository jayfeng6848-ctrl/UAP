"""Wave 2 §八 / §三十五: Argon2id hashing, no plaintext, one-way tokens."""

from __future__ import annotations

from services.identity import PasswordHasher, hash_token, new_token, verify_token
from services.mapping import CredentialAlgorithm


def test_password_hash_is_argon2id_and_never_plaintext() -> None:
    secret = "correct horse battery staple"
    digest = PasswordHasher.hash(secret)
    assert digest.startswith("$argon2id$")
    assert secret not in digest
    assert PasswordHasher.algorithm is CredentialAlgorithm.ARGON2ID


def test_verification_accepts_only_the_right_secret() -> None:
    digest = PasswordHasher.hash("s3cret-value")
    assert PasswordHasher.verify(digest, "s3cret-value") is True
    assert PasswordHasher.verify(digest, "s3cret-valuE") is False
    assert PasswordHasher.verify("", "s3cret-value") is False


def test_same_password_hashes_differently_each_time() -> None:
    assert PasswordHasher.hash("same") != PasswordHasher.hash("same")


def test_token_hash_is_one_way_and_verifiable() -> None:
    token = new_token()
    assert len(token) >= 32
    digest = hash_token(token)
    assert token not in digest
    assert verify_token(digest, token) is True
    assert verify_token(digest, new_token()) is False
