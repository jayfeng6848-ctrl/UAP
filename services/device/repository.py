"""Persistence adapter for ``devices``."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from infrastructure.runtime.errors import PersistenceError
from services.reads import SafeReader

from .errors import DeviceConflict

DEVICE_COLUMNS = (
    "id, user_id, fingerprint, label, platform, status, first_seen_at, last_seen_at,"
    " revoked_at, revoked_reason"
)


class DeviceRepository(SafeReader):
    """SQL for the device aggregate."""

    def get_device(self, device_id: str) -> Any:
        return self._fetch_one(
            f"SELECT {DEVICE_COLUMNS} FROM public.devices WHERE id = :did",
            {"did": device_id},
        )

    def find_for_user_fingerprint(self, user_id: str, fingerprint: str) -> Any:
        """Per-user fingerprint lookup (persistence truth: UNIQUE(user_id, fingerprint))."""
        return self._fetch_one(
            f"SELECT {DEVICE_COLUMNS} FROM public.devices"
            " WHERE user_id = :uid AND fingerprint = :fp",
            {"uid": user_id, "fp": fingerprint},
        )

    def list_for_user(self, user_id: str) -> list[Any]:
        return self._fetch_all(
            f"SELECT {DEVICE_COLUMNS} FROM public.devices WHERE user_id = :uid"
            " ORDER BY created_at",
            {"uid": user_id},
        )

    def insert_device(
        self,
        *,
        user_id: str,
        fingerprint: str,
        label: str | None,
        platform: str | None,
        status: str,
    ) -> str:
        try:
            return str(
                self.session.execute(
                    text(
                        "INSERT INTO public.devices"
                        " (user_id, fingerprint, label, platform, status, first_seen_at,"
                        "  last_seen_at)"
                        " VALUES (:uid, :fp, :label, :platform, :status, now(), now())"
                        " RETURNING id"
                    ),
                    {
                        "uid": user_id,
                        "fp": fingerprint,
                        "label": label,
                        "platform": platform,
                        "status": status,
                    },
                ).scalar_one()
            )
        except IntegrityError as exc:
            # per-user fingerprint uniqueness is a persistence constraint (§十三)
            raise DeviceConflict(_safe(exc)) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc

    def set_status(
        self, device_id: str, status: str, *, reason: str | None = None, revoke: bool = False
    ) -> int:
        try:
            result = self.session.execute(
                text(
                    "UPDATE public.devices SET status = :status,"
                    " revoked_at = CASE WHEN :revoke THEN now() ELSE revoked_at END,"
                    " revoked_reason = COALESCE(:reason, revoked_reason),"
                    " updated_at = now() WHERE id = :did"
                ),
                {"did": device_id, "status": status, "reason": reason, "revoke": revoke},
            )
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc
        return int(result.rowcount or 0)


def _safe(exc: BaseException) -> str:
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return line[:200]


__all__ = ["DEVICE_COLUMNS", "DeviceRepository"]
