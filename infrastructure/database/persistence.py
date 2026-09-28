"""Persistence adapter boundary (P14 Runtime Implementation Wave 1, §12).

    Service
       v
    Repository (this module's contract)
       v
    SQLAlchemy session owned by RuntimeDatabase
       v
    uap_runtime

Repositories execute queries and map rows. They do **not** decide transaction
outcomes, authorization, or API responses -- the session is handed to them by
the transaction boundary and the service layer owns COMMIT/ROLLBACK.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.runtime.errors import PersistenceError


class Repository(ABC):
    """Base class for persistence adapters.

    A repository receives the session it must use; it never builds its own
    engine and never commits.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def _fetch_one(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        try:
            return self._session.execute(text(sql), params or {}).one()
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(err)) from exc

    def _fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[Any]:
        try:
            return list(self._session.execute(text(sql), params or {}).all())
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(err)) from exc


def _safe(exc: BaseException) -> str:
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return line[:200]


__all__ = ["Repository"]
