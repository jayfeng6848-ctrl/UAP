"""Wave 2 read base class.

Why this exists (DEFECT ``W2-D-01``): the Wave 1 base class
``infrastructure.database.persistence.Repository`` has two defects that only
surface once a lookup can legitimately miss:

1. both ``except`` handlers reference an undefined name ``err``
   (``raise PersistenceError(_safe(err))``), so any ``SQLAlchemyError`` becomes a
   ``NameError`` instead of a classified ``PersistenceError``;
2. ``_fetch_one`` uses ``.one()``, which raises ``NoResultFound`` on zero rows,
   so "not found" cannot be represented as ``None``.

Wave 1 is ACCEPTED and frozen (Evidence Freeze), so this round does **not**
repair that file. Wave 2 repositories instead inherit :class:`SafeReader`, which
provides the same helper names with correct semantics. The Wave 1 defect is
registered in the Wave 2 implementation report with the recommended fix.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.persistence import Repository
from infrastructure.runtime.errors import PersistenceError


def _safe(exc: BaseException) -> str:
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return line[:200]


class SafeReader(Repository):
    """``Repository`` with working ``_fetch_one`` / ``_fetch_all`` semantics."""

    def _fetch_one(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        """Return the first row, or ``None`` when the query matches nothing."""
        try:
            return self._session.execute(text(sql), params or {}).first()
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc

    def _fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[Any]:
        try:
            return list(self._session.execute(text(sql), params or {}).all())
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc


__all__ = ["SafeReader"]
