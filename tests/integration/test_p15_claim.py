"""P15 Batch 2 — claim / lease / heartbeat / recovery integration tests.

Runtime assertions run as ``uap_runtime`` (UAP_RUNTIME_TEST_DSN). Synthetic
outbox rows are inserted by the runtime identity (events INSERT is granted) and
removed afterwards through the fixture identity, because the runtime identity
holds no DELETE on ``events`` — that cleanup path is explicit and net-zero.
"""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from services.consumer.claim import ClaimService
from services.consumer.kernel import (
    MAX_ATTEMPTS,
    TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS,
    TERMINAL_REASON_MAX_ATTEMPTS,
    backoff_seconds,
    production_allowlist,
)
from tests.integration.alembic_testkit import BASE_DSN
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn

pytestmark = pytest.mark.integration

WORKER_A = "worker-a"
WORKER_B = "worker-b"


@pytest.fixture(scope="module")
def db():
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=runtime_test_dsn()), require_role=REQUIRED_ROLE
    )
    database.start()
    try:
        yield database
    finally:
        database.dispose()


@pytest.fixture()
def outbox(db):
    """Seed synthetic events as uap_runtime; delete them (net-zero) afterwards."""
    seeded: list[str] = []

    def seed(*, status: str = "pending", attempts: int = 0,
             lease_expired: bool = False, next_attempt_at: str | None = None,
             event_type: str = "p15.test_event") -> tuple[str, object]:
        event_id = str(uuid.uuid4())
        # Interval expressions must be inlined; they are test-controlled literals.
        worker_expr = "'stale-worker'" if status == "claimed" else "NULL"
        claimed_expr = "now() - interval '5 minutes'" if status == "claimed" else "NULL"
        if status == "claimed" and lease_expired:
            lease_expr = "now() - interval '1 minute'"
        elif status == "claimed":
            lease_expr = "now() + interval '5 minutes'"
        else:
            lease_expr = "NULL"
        next_expr = next_attempt_at if next_attempt_at else "NULL"
        with db.transaction() as session:
            row = session.execute(
                sa.text(
                    "INSERT INTO public.events"
                    " (id, occurred_at, event_type, schema_version, payload, status, attempts,"
                    "  worker_id, claimed_at, lease_expires_at, next_attempt_at)"
                    " VALUES (CAST(:id AS uuid), now(), :etype, 1, '{}'::jsonb, :status, :attempts,"
                    f"  {worker_expr}, {claimed_expr}, {lease_expr}, {next_expr})"
                    " RETURNING occurred_at"
                ),
                {
                    "id": event_id,
                    "etype": event_type,
                    "status": status,
                    "attempts": attempts,
                },
            ).one()
        seeded.append(event_id)
        return event_id, row[0]

    try:
        yield seed
    finally:
        if seeded:
            engine = sa.create_engine(BASE_DSN, future=True)
            with engine.begin() as conn:
                conn.execute(
                    sa.text("DELETE FROM public.events WHERE id = ANY(CAST(:ids AS uuid[]))"),
                    {"ids": seeded},
                )
            engine.dispose()


def _state(db, event_id: str, occurred_at) -> dict:
    with db.transaction() as session:
        row = session.execute(
            sa.text(
                "SELECT status, attempts, worker_id, next_attempt_at, last_error,"
                " delivered_at FROM public.events WHERE id = :id AND occurred_at = :ts"
            ),
            {"id": event_id, "ts": occurred_at},
        ).one()
    return dict(row._mapping)


def test_claim_takes_ownership_and_sets_lease(outbox, db) -> None:
    event_id, occurred_at = outbox()
    with db.transaction() as session:
        claimed = ClaimService(session).claim_batch(worker_id=WORKER_A)
    mine = [c for c in claimed if c.id == event_id]
    assert len(mine) == 1
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "claimed"
    assert state["worker_id"] == WORKER_A


def test_claim_batch_is_bounded(outbox, db) -> None:
    for _ in range(3):
        outbox()
    with db.transaction() as session:
        claimed = ClaimService(session).claim_batch(worker_id=WORKER_A, batch_size=2)
    assert 0 < len(claimed) <= 2


def test_claim_batch_rejects_out_of_range_size(db) -> None:
    with pytest.raises(ValueError):
        with db.transaction() as session:
            ClaimService(session).claim_batch(worker_id=WORKER_A, batch_size=11)


def test_two_workers_never_claim_the_same_event(outbox, db) -> None:
    event_id, _ = outbox()
    with db.transaction() as session:
        a = {c.id for c in ClaimService(session).claim_batch(worker_id=WORKER_A)}
    with db.transaction() as session:
        b = {c.id for c in ClaimService(session).claim_batch(worker_id=WORKER_B)}
    assert event_id in a
    assert event_id not in b
    assert not (a & b)


def test_heartbeat_requires_ownership(outbox, db) -> None:
    event_id, _ = outbox()
    with db.transaction() as session:
        service = ClaimService(session)
        claimed = [c for c in service.claim_batch(worker_id=WORKER_A) if c.id == event_id][0]
        assert service.heartbeat(claimed, worker_id=WORKER_A) is True
        assert service.heartbeat(claimed, worker_id=WORKER_B) is False


def test_recovery_requeues_expired_lease_without_adding_attempts(outbox, db) -> None:
    event_id, occurred_at = outbox(status="claimed", attempts=3, lease_expired=True)
    with db.transaction() as session:
        result = ClaimService(session).recover_expired()
    assert result["requeued"] >= 1
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "pending"
    assert state["attempts"] == 3  # attempts are execution attempts, not recovery attempts
    assert state["worker_id"] is None


def test_recovery_terminates_expired_lease_at_the_bound(outbox, db) -> None:
    event_id, occurred_at = outbox(status="claimed", attempts=MAX_ATTEMPTS, lease_expired=True)
    with db.transaction() as session:
        ClaimService(session).recover_expired()
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "dead"
    assert state["last_error"] == TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS
    assert state["attempts"] == MAX_ATTEMPTS  # unchanged by recovery


def test_recovery_ignores_live_leases(outbox, db) -> None:
    event_id, occurred_at = outbox(status="claimed", attempts=1, lease_expired=False)
    with db.transaction() as session:
        ClaimService(session).recover_expired()
    assert _state(db, event_id, occurred_at)["status"] == "claimed"


def test_retry_returns_to_pending_with_attempt_increment_and_backoff(outbox, db) -> None:
    event_id, occurred_at = outbox()
    with db.transaction() as session:
        service = ClaimService(session)
        claimed = [c for c in service.claim_batch(worker_id=WORKER_A) if c.id == event_id][0]
        assert service.mark_retry(claimed, worker_id=WORKER_A, reason="transient") is True
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "pending"
    assert state["attempts"] == 1
    assert state["next_attempt_at"] is not None
    assert state["last_error"] == "transient"
    assert backoff_seconds(1) == 5


def test_retry_at_the_last_attempt_terminates_as_dead(outbox, db) -> None:
    event_id, occurred_at = outbox(attempts=MAX_ATTEMPTS - 1)
    with db.transaction() as session:
        service = ClaimService(session)
        claimed = [c for c in service.claim_batch(worker_id=WORKER_A) if c.id == event_id][0]
        service.mark_retry(claimed, worker_id=WORKER_A, reason="transient")
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "dead"
    assert state["last_error"] == TERMINAL_REASON_MAX_ATTEMPTS
    assert state["attempts"] == MAX_ATTEMPTS


def test_delivered_is_terminal_and_clears_ownership(outbox, db) -> None:
    event_id, occurred_at = outbox()
    with db.transaction() as session:
        service = ClaimService(session)
        claimed = [c for c in service.claim_batch(worker_id=WORKER_A) if c.id == event_id][0]
        assert service.mark_delivered(claimed, worker_id=WORKER_A) is True
        # terminality: a delivered event stays delivered
        assert service.heartbeat(claimed, worker_id=WORKER_A) is False
        assert service.mark_delivered(claimed, worker_id=WORKER_A) is False
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "delivered"
    assert state["delivered_at"] is not None
    assert state["worker_id"] is None


def test_dead_is_terminal(outbox, db) -> None:
    event_id, occurred_at = outbox()
    with db.transaction() as session:
        service = ClaimService(session)
        claimed = [c for c in service.claim_batch(worker_id=WORKER_A) if c.id == event_id][0]
        assert service.mark_dead(claimed, worker_id=WORKER_A, reason="non_retryable_failure") is True
        assert service.mark_delivered(claimed, worker_id=WORKER_A) is False
    state = _state(db, event_id, occurred_at)
    assert state["status"] == "dead"
    assert state["last_error"] == "non_retryable_failure"


def test_production_allowlist_is_empty_and_no_handler_is_enabled() -> None:
    allowlist = production_allowlist()
    assert allowlist.is_empty is True
