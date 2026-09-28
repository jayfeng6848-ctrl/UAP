"""Persistence adapter for users / identities / credentials.

Pure persistence: SQL execution and row mapping only. It does not decide
transaction outcomes (the use-case owns COMMIT/ROLLBACK) and it does not apply
business rules — vocabulary mapping lives in :mod:`services.mapping`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from infrastructure.runtime.errors import PersistenceError
from services.reads import SafeReader

from .errors import IdentityConflict

USER_COLUMNS = "id, email, username, display_name, status, locked_until, failed_attempts"
IDENTITY_COLUMNS = "id, user_id, provider, issuer, subject, email, display_name, status"
CREDENTIAL_COLUMNS = (
    "id, identity_id, user_id, type, secret_hash, algorithm, expires_at, "
    "revoked_at, rotated_at, failed_attempts, locked_until"
)


class IdentityRepository(SafeReader):
    """SQL for the identity aggregate."""

    # ------------------------------------------------------------------ users
    def find_user_by_login(self, login: str) -> Any:
        return self._fetch_one(
            f"SELECT {USER_COLUMNS} FROM public.users"
            " WHERE (lower(email) = lower(:login) OR lower(username) = lower(:login))"
            " AND deleted_at IS NULL LIMIT 1",
            {"login": login},
        )

    def get_user(self, user_id: str) -> Any:
        return self._fetch_one(
            f"SELECT {USER_COLUMNS} FROM public.users WHERE id = :uid",
            {"uid": user_id},
        )

    def insert_user(
        self, *, email: str | None, username: str | None, display_name: str | None, status: str
    ) -> str:
        return self._insert(
            "INSERT INTO public.users (email, username, display_name, status)"
            " VALUES (:email, :username, :display_name, :status) RETURNING id",
            {
                "email": email,
                "username": username,
                "display_name": display_name,
                "status": status,
            },
        )

    def set_user_status(self, user_id: str, status: str) -> None:
        self._execute(
            "UPDATE public.users SET status = :status, updated_at = now()"
            " WHERE id = :uid",
            {"uid": user_id, "status": status},
        )

    def register_user_failure(self, user_id: str, *, locked_until: datetime | None) -> None:
        self._execute(
            "UPDATE public.users SET failed_attempts = failed_attempts + 1,"
            " locked_until = :locked, updated_at = now() WHERE id = :uid",
            {"uid": user_id, "locked": locked_until},
        )

    def clear_user_failures(self, user_id: str) -> None:
        self._execute(
            "UPDATE public.users SET failed_attempts = 0, locked_until = NULL,"
            " last_login_at = now(), updated_at = now() WHERE id = :uid",
            {"uid": user_id},
        )

    # ------------------------------------------------------------ identities
    def insert_identity(
        self,
        *,
        user_id: str,
        provider: str,
        subject: str,
        email: str | None,
        display_name: str | None,
        status: str,
    ) -> str:
        return self._insert(
            "INSERT INTO public.identities"
            " (user_id, provider, subject, email, display_name, status)"
            " VALUES (:uid, :provider, :subject, :email, :display_name, :status)"
            " RETURNING id",
            {
                "uid": user_id,
                "provider": provider,
                "subject": subject,
                "email": email,
                "display_name": display_name,
                "status": status,
            },
        )

    def get_identity(self, identity_id: str) -> Any:
        return self._fetch_one(
            f"SELECT {IDENTITY_COLUMNS} FROM public.identities WHERE id = :iid",
            {"iid": identity_id},
        )

    def get_local_identity_for_user(self, user_id: str, provider: str) -> Any:
        return self._fetch_one(
            f"SELECT {IDENTITY_COLUMNS} FROM public.identities"
            " WHERE user_id = :uid AND provider = :provider"
            " ORDER BY created_at LIMIT 1",
            {"uid": user_id, "provider": provider},
        )

    def set_identity_status(
        self,
        identity_id: str,
        status: str,
        *,
        verified: bool = False,
        revoked: bool = False,
    ) -> None:
        self._execute(
            "UPDATE public.identities SET status = :status,"
            " verified_at = CASE WHEN :verified THEN now() ELSE verified_at END,"
            " revoked_at = CASE WHEN :revoked THEN now() ELSE revoked_at END,"
            " updated_at = now() WHERE id = :iid",
            {"iid": identity_id, "status": status, "verified": verified, "revoked": revoked},
        )

    # ----------------------------------------------------------- credentials
    def insert_credential(
        self,
        *,
        identity_id: str,
        user_id: str,
        credential_type: str,
        secret_hash: str,
        algorithm: str,
        expires_at: datetime | None,
    ) -> str:
        return self._insert(
            "INSERT INTO public.credentials"
            " (identity_id, user_id, type, secret_hash, algorithm, expires_at)"
            " VALUES (:iid, :uid, :ctype, :hash, :alg, :expires) RETURNING id",
            {
                "iid": identity_id,
                "uid": user_id,
                "ctype": credential_type,
                "hash": secret_hash,
                "alg": algorithm,
                "expires": expires_at,
            },
        )

    def get_credential(self, credential_id: str) -> Any:
        return self._fetch_one(
            f"SELECT {CREDENTIAL_COLUMNS} FROM public.credentials WHERE id = :cid",
            {"cid": credential_id},
        )

    def get_live_credential(
        self, identity_id: str, *, credential_type: str
    ) -> Any:
        """The single non-revoked, non-expired credential of that type, if any."""
        return self._fetch_one(
            f"SELECT {CREDENTIAL_COLUMNS} FROM public.credentials"
            " WHERE identity_id = :iid AND type = :ctype AND revoked_at IS NULL"
            " AND (expires_at IS NULL OR expires_at > now())"
            " ORDER BY created_at DESC LIMIT 1",
            {"iid": identity_id, "ctype": credential_type},
        )

    def revoke_credential(self, credential_id: str) -> None:
        self._execute(
            "UPDATE public.credentials SET revoked_at = now(), updated_at = now()"
            " WHERE id = :cid AND revoked_at IS NULL",
            {"cid": credential_id},
        )

    def revoke_credentials_for_identity(self, identity_id: str) -> int:
        result = self.session.execute(
            text(
                "UPDATE public.credentials SET revoked_at = now(), updated_at = now()"
                " WHERE identity_id = :iid AND revoked_at IS NULL"
            ),
            {"iid": identity_id},
        )
        return int(result.rowcount or 0)

    def mark_credential_rotated(self, credential_id: str) -> None:
        self._execute(
            "UPDATE public.credentials SET rotated_at = now(), revoked_at = now(),"
            " updated_at = now() WHERE id = :cid",
            {"cid": credential_id},
        )

    def record_credential_failure(
        self, credential_id: str, *, locked_until: datetime | None
    ) -> None:
        self._execute(
            "UPDATE public.credentials SET failed_attempts = failed_attempts + 1,"
            " locked_until = :locked, updated_at = now() WHERE id = :cid",
            {"cid": credential_id, "locked": locked_until},
        )

    def clear_credential_failures(self, credential_id: str) -> None:
        self._execute(
            "UPDATE public.credentials SET failed_attempts = 0, locked_until = NULL,"
            " last_used_at = now(), updated_at = now() WHERE id = :cid",
            {"cid": credential_id},
        )

    def consume_challenge(self, credential_id: str) -> int:
        """Explicit one-time consumption (no DELETE is granted; §十四 / §三十五)."""
        result = self.session.execute(
            text(
                "UPDATE public.credentials SET revoked_at = now(), updated_at = now()"
                " WHERE id = :cid AND revoked_at IS NULL"
            ),
            {"cid": credential_id},
        )
        return int(result.rowcount or 0)

    # ----------------------------------------------------------------- helpers
    def _execute(self, sql: str, params: dict[str, Any]) -> int:
        try:
            result = self.session.execute(text(sql), params)
        except IntegrityError as exc:
            raise IdentityConflict(_safe(exc)) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc
        return int(result.rowcount or 0)

    def _insert(self, sql: str, params: dict[str, Any]) -> str:
        try:
            return str(self.session.execute(text(sql), params).scalar_one())
        except IntegrityError as exc:
            raise IdentityConflict(_safe(exc)) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc


def _safe(exc: BaseException) -> str:
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return line[:200]


__all__ = ["IdentityRepository"]
