"""P15 C-5 Batch 2 — claim / lease / heartbeat / recovery service.

Session-scoped: the caller (worker, Batch 3) owns the transaction via
``RuntimeDatabase.transaction()``; this service never commits. Every state
transition is a **conditional UPDATE whose rowcount decides ownership** — the
DB, not Python memory, guarantees single ownership (O-1/O-4).

Reads go through :class:`services.reads.SafeReader` (D-01 stays deferred: the
Wave 1 defective helper is never used).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.runtime.errors import PersistenceError
from services.reads import SafeReader

from .kernel import (
    CLAIM_BATCH_SIZE,
    CLAIM_SQL,
    COMPLETE_DEAD_SQL,
    COMPLETE_DELIVERED_SQL,
    COMPLETE_PENDING_SQL,
    HEARTBEAT_SQL,
    LEASE_SECONDS,
    MAX_ATTEMPTS,
    RECOVER_EXPIRED_DEAD_SQL,
    RECOVER_EXPIRED_SQL,
    TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS,
    TERMINAL_REASON_MAX_ATTEMPTS,
    backoff_seconds,
)


@dataclass(frozen=True)
class ClaimedEvent:
    """A claimed event. Carries identifiers + payload only (never secrets)."""

    id: str
    occurred_at: Any
    event_type: str
    schema_version: int
    tenant_id: str | None
    space_id: str | None
    actor_type: str | None
    actor_id: str | None
    payload: dict[str, Any]
    attempts: int
    correlation_id: str | None


class EventRepository(SafeReader):
    """Persistence adapter for the events(outbox) table."""

    def claim_batch(self, *, worker_id: str, batch_size: int, max_attempts: int,
                    lease_seconds: int) -> list[ClaimedEvent]:
        rows = self._execute_returning(
            CLAIM_SQL,
            {
                "worker_id": worker_id,
                "batch_size": batch_size,
                "max_attempts": max_attempts,
                "lease": lease_seconds,
            },
        )
        return [
            ClaimedEvent(
                id=str(r._mapping["id"]),
                occurred_at=r._mapping["occurred_at"],
                event_type=str(r._mapping["event_type"]),
                schema_version=int(r._mapping["schema_version"]),
                tenant_id=(str(r._mapping["tenant_id"]) if r._mapping["tenant_id"] else None),
                space_id=(str(r._mapping["space_id"]) if r._mapping["space_id"] else None),
                actor_type=r._mapping["actor_type"],
                actor_id=(str(r._mapping["actor_id"]) if r._mapping["actor_id"] else None),
                payload=dict(r._mapping["payload"] or {}),
                attempts=int(r._mapping["attempts"]),
                correlation_id=(
                    str(r._mapping["correlation_id"]) if r._mapping["correlation_id"] else None
                ),
            )
            for r in rows
        ]

    def get(self, *, event_id: str, occurred_at: Any) -> Any:
        return self._fetch_one(
            "SELECT status, attempts, worker_id, last_error, delivered_at"
            " FROM public.events WHERE id = :id AND occurred_at = :ts",
            {"id": event_id, "ts": occurred_at},
        )

    def _execute_returning(self, sql: str, params: dict[str, Any]) -> list[Any]:
        try:
            return list(self.session.execute(text(sql), params).all())
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc


class ClaimService:
    """Claim/lease/heartbeat/recovery + terminal transitions (Batch 2)."""

    def __init__(self, session: Session) -> None:
        self._repo = EventRepository(session)

    # ------------------------------------------------------------------- claim
    def claim_batch(self, *, worker_id: str, batch_size: int = CLAIM_BATCH_SIZE,
                    max_attempts: int = MAX_ATTEMPTS,
                    lease_seconds: int = LEASE_SECONDS) -> list[ClaimedEvent]:
        """Claim up to ``batch_size`` eligible events atomically (O-4 bound)."""
        if batch_size < 1 or batch_size > CLAIM_BATCH_SIZE:
            raise ValueError(f"batch_size must be within 1..{CLAIM_BATCH_SIZE}")
        return self._repo.claim_batch(
            worker_id=worker_id, batch_size=batch_size, max_attempts=max_attempts,
            lease_seconds=lease_seconds,
        )

    # --------------------------------------------------------------- heartbeat
    def heartbeat(self, event: ClaimedEvent, *, worker_id: str,
                  lease_seconds: int = LEASE_SECONDS) -> bool:
        """Extend the lease only while this worker still owns it.

        ``False`` means ownership was lost: the caller MUST stop executing.
        """
        return self._execute(
            HEARTBEAT_SQL,
            {"id": event.id, "occurred_at": event.occurred_at, "worker_id": worker_id,
             "lease": lease_seconds},
        ) == 1

    # ------------------------------------------------------------- transitions
    def mark_delivered(self, event: ClaimedEvent, *, worker_id: str) -> bool:
        """Success: only after the use-case side effect is durable (§20)."""
        return self._execute(
            COMPLETE_DELIVERED_SQL,
            {"id": event.id, "occurred_at": event.occurred_at, "worker_id": worker_id},
        ) == 1

    def mark_retry(self, event: ClaimedEvent, *, worker_id: str, reason: str) -> bool:
        """Retryable failure: back to pending, attempts+1, deterministic backoff."""
        attempts_after = event.attempts + 1
        if attempts_after >= MAX_ATTEMPTS:
            return self.mark_dead(event, worker_id=worker_id,
                                  reason=TERMINAL_REASON_MAX_ATTEMPTS)
        return self._execute(
            COMPLETE_PENDING_SQL,
            {"id": event.id, "occurred_at": event.occurred_at, "worker_id": worker_id,
             "reason": reason, "delay": backoff_seconds(attempts_after)},
        ) == 1

    def mark_dead(self, event: ClaimedEvent, *, worker_id: str, reason: str) -> bool:
        return self._execute(
            COMPLETE_DEAD_SQL,
            {"id": event.id, "occurred_at": event.occurred_at, "worker_id": worker_id,
             "reason": reason},
        ) == 1

    # ---------------------------------------------------------------- recovery
    def recover_expired(self, *, max_attempts: int = MAX_ATTEMPTS) -> dict[str, int]:
        """O-1: expired leases -> pending (attempts preserved) or dead at the bound."""
        requeued = self._execute(RECOVER_EXPIRED_SQL, {"max_attempts": max_attempts})
        terminated = self._execute(
            RECOVER_EXPIRED_DEAD_SQL,
            {"max_attempts": max_attempts,
             "reason": TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS},
        )
        return {"requeued": requeued, "terminated": terminated}

    # ----------------------------------------------------------------- helpers
    def _execute(self, sql: str, params: dict[str, Any]) -> int:
        try:
            return int(self.session.execute(text(sql), params).rowcount or 0)
        except SQLAlchemyError as exc:
            raise PersistenceError(_safe(exc)) from exc

    @property
    def session(self) -> Session:
        return self._repo.session


def _safe(exc: BaseException) -> str:
    line = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    return line[:200]


__all__ = ["ClaimService", "ClaimedEvent", "EventRepository"]
