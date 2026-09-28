"""Persistence adapter for ``sessions``.

Session rows are the one identity-side object the runtime may physically
``DELETE``; Wave 2 nevertheless prefers an explicit status transition
(``revoked`` / ``expired``) so that revocation is observable and audit-friendly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from infrastructure.runtime.errors import PersistenceError
from services.reads import SafeReader

SESSION_COLUMNS = (
    "id, user_id, identity_id, device_id, status, expires_at, absolute_expires_at,"
    " revoked_at, revoked_reason, replaced_by, last_used_at"
)


class SessionRepository(SafeReader):
    """SQL for the session aggregate."""

    def insert_session(
        self,
        *,
        user_id: str,
        identity_id: str,
        device_id: str | None,
        token_hash: str,
        refresh_token_hash: str | None,
        expires_at: datetime,
        absolute_expires_at: datetime,
        ip_created: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        try:
            return str(
                self.session.execute(
                    text(
                        "INSERT INTO public.sessions"
                        " (user_id, identity_id, device_id, token_hash, refresh_token_hash,"
                        "  status, expires_at, absolute_expires_at, ip_created, ip_last,"
                        "  user_agent)"
                        " VALUES (:uid, :iid, :did, :token, :refresh, 'active', :expires,"
                        "  :absolute, :ip, :ip, :ua) RETURNING id"
                    ),
                    {
                        "uid": user_id,
                        "iid": identity_id,
                        "did": device_id,
                        "token": token_hash,
                        "refresh": refresh_token_hash,
                        "expires": expires_at,
                        "absolute": absolute_expires_at,
                        "ip": ip_created,
                        "ua": user_agent,
                    },
                ).scalar_one()
            )
        except IntegrityError as exc:
            raise PersistenceError(_safe(exc)) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc

    def get_session(self, session_id: str) -> Any:
        return self._fetch_one(
            f"SELECT {SESSION_COLUMNS} FROM public.sessions WHERE id = :sid",
            {"sid": session_id},
        )

    def find_by_token_hash(self, token_hash: str) -> Any:
        return self._fetch_one(
            f"SELECT {SESSION_COLUMNS} FROM public.sessions WHERE token_hash = :token",
            {"token": token_hash},
        )

    def set_status(
        self,
        session_id: str,
        status: str,
        *,
        reason: str | None = None,
        revoke: bool = False,
        replaced_by: str | None = None,
    ) -> int:
        try:
            result = self.session.execute(
                text(
                    "UPDATE public.sessions SET status = :status,"
                    " revoked_at = CASE WHEN :revoke THEN now() ELSE revoked_at END,"
                    " revoked_reason = COALESCE(:reason, revoked_reason),"
                    " replaced_by = COALESCE(:replaced, replaced_by),"
                    " updated_at = now() WHERE id = :sid"
                ),
                {
                    "sid": session_id,
                    "status": status,
                    "revoke": revoke,
                    "reason": reason,
                    "replaced": replaced_by,
                },
            )
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc
        return int(result.rowcount or 0)

    def revoke_for_device(self, device_id: str, *, reason: str) -> int:
        """Revoke every active session bound to a device (same transaction)."""
        return self._revoke_where("device_id = :key", device_id, reason=reason)

    def revoke_for_identity(self, identity_id: str, *, reason: str) -> int:
        return self._revoke_where("identity_id = :key", identity_id, reason=reason)

    def revoke_for_user(self, user_id: str, *, reason: str) -> int:
        return self._revoke_where("user_id = :key", user_id, reason=reason)

    def expire_overdue(self) -> int:
        """Mark overdue sessions expired (status transition, never a delete)."""
        try:
            result = self.session.execute(
                text(
                    "UPDATE public.sessions SET status = 'expired', updated_at = now()"
                    " WHERE status = 'active' AND (expires_at <= now()"
                    " OR (absolute_expires_at IS NOT NULL AND absolute_expires_at <= now()))"
                )
            )
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc
        return int(result.rowcount or 0)

    def touch(self, session_id: str) -> None:
        self._execute(
            "UPDATE public.sessions SET last_used_at = now(), updated_at = now()"
            " WHERE id = :sid",
            {"sid": session_id},
        )

    def count_active_for_device(self, device_id: str) -> int:
        return int(
            self._fetch_one(
                "SELECT count(*) FROM public.sessions"
                " WHERE device_id = :did AND status = 'active'",
                {"did": device_id},
            )[0]
        )

    # ----------------------------------------------------------------- helpers
    def _revoke_where(self, predicate: str, key: str, *, reason: str) -> int:
        try:
            result = self.session.execute(
                text(
                    "UPDATE public.sessions SET status = 'revoked', revoked_at = now(),"
                    f" revoked_reason = :reason, updated_at = now()"
                    f" WHERE {predicate} AND status = 'active'"
                ),
                {"key": key, "reason": reason},
            )
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc
        return int(result.rowcount or 0)

    def _execute(self, sql: str, params: dict[str, Any]) -> int:
        try:
            result = self.session.execute(text(sql), params)
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc
        return int(result.rowcount or 0)


def _safe(exc: BaseException) -> str:
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return line[:200]


__all__ = ["SessionRepository"]
