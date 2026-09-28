"""P15 C-5 consumer kernel — frozen-policy unit tests (offline, no DB)."""

from __future__ import annotations

import pytest

from services.consumer.kernel import (
    BACKOFF_CAP_SECONDS,
    CLAIM_BATCH_SIZE,
    CLAIM_SQL,
    COMPLETE_DEAD_SQL,
    COMPLETE_DELIVERED_SQL,
    COMPLETE_PENDING_SQL,
    HEARTBEAT_SECONDS,
    LEASE_SECONDS,
    MAX_ATTEMPTS,
    RECOVER_EXPIRED_DEAD_SQL,
    RECOVER_EXPIRED_SQL,
    WORKER_CONCURRENCY,
    WORKER_PROCESS_COUNT,
    EventAllowlist,
    EventHandlerSpec,
    UnsupportedEventType,
    backoff_seconds,
    is_eligible,
    is_retryable,
    is_terminal_attempt,
    production_allowlist,
)


def test_frozen_o4_parameters() -> None:
    assert (WORKER_PROCESS_COUNT, WORKER_CONCURRENCY, CLAIM_BATCH_SIZE) == (1, 4, 10)
    assert (LEASE_SECONDS, HEARTBEAT_SECONDS) == (120, 40)
    assert MAX_ATTEMPTS == 10


def test_backoff_is_deterministic_exponential_and_capped() -> None:
    """O-2: base 5s, multiplier 2, cap 600s (10 minutes), no jitter.

    O-2 CLARIFICATION (Human decision, 2026-09-28): the canonical sequence is
    ``delay = min(5 * 2 ** (attempt - 1), 600)`` — so attempt 8 and 9 are both
    capped at 600s and attempt 10 is terminal (no further retry delay). The
    earlier table row "+640s at attempt 8" is superseded by this formula and is
    no longer a discrepancy.
    """
    assert [backoff_seconds(n) for n in range(1, 10)] == [5, 10, 20, 40, 80, 160, 320, 600, 600]
    assert backoff_seconds(10) == BACKOFF_CAP_SECONDS
    assert backoff_seconds(1) == backoff_seconds(1)  # no jitter


def test_backoff_rejects_invalid_attempt() -> None:
    with pytest.raises(ValueError):
        backoff_seconds(0)


def test_attempt_bounds_follow_max_attempts() -> None:
    assert is_eligible(0) is True
    assert is_eligible(MAX_ATTEMPTS - 1) is True
    assert is_eligible(MAX_ATTEMPTS) is False
    assert is_terminal_attempt(MAX_ATTEMPTS) is True
    assert is_terminal_attempt(MAX_ATTEMPTS - 1) is False


def test_only_transient_categories_are_retryable() -> None:
    assert is_retryable("connection") is True
    assert is_retryable("persistence") is True
    for category in ("authorization", "authentication", "security_boundary", "validation"):
        assert is_retryable(category) is False


def test_production_allowlist_is_empty() -> None:
    allowlist = production_allowlist()
    assert allowlist.is_empty is True
    with pytest.raises(UnsupportedEventType):
        allowlist.resolve("order.created")


def test_ineligible_handler_cannot_be_registered() -> None:
    allowlist = EventAllowlist()
    with pytest.raises(ValueError):
        allowlist.register(
            EventHandlerSpec("order.created", False, True, True, "naturally_idempotent")
        )
    with pytest.raises(ValueError):
        allowlist.register(EventHandlerSpec("order.created", True, True, True, "probably_safe"))


def test_eligible_handler_can_be_registered() -> None:
    allowlist = EventAllowlist()
    allowlist.register(
        EventHandlerSpec("order.created", True, True, True, "transactional_key")
    )
    assert allowlist.resolve("order.created").event_type == "order.created"
    assert allowlist.is_empty is False


def test_claim_sql_is_conditional_and_bounded() -> None:
    assert "FOR UPDATE SKIP LOCKED" in CLAIM_SQL
    assert "LIMIT :batch_size" in CLAIM_SQL
    assert "attempts < :max_attempts" in CLAIM_SQL
    assert "e.status = 'pending'" in CLAIM_SQL
    assert "RETURNING" in CLAIM_SQL


def test_ownership_is_required_for_every_transition() -> None:
    for sql in (COMPLETE_DELIVERED_SQL, COMPLETE_PENDING_SQL, COMPLETE_DEAD_SQL):
        assert "worker_id = :worker_id" in sql
        assert "status = 'claimed'" in sql


def test_delivered_requires_side_effect_completion_marker() -> None:
    assert "delivered_at = now()" in COMPLETE_DELIVERED_SQL
    assert "status = 'delivered'" in COMPLETE_DELIVERED_SQL


def test_retry_sql_increments_attempts_with_backoff() -> None:
    assert "attempts = attempts + 1" in COMPLETE_PENDING_SQL
    assert "next_attempt_at = now() + make_interval(secs => :delay)" in COMPLETE_PENDING_SQL


def test_recovery_never_increments_attempts() -> None:
    recovery_set_clause = RECOVER_EXPIRED_SQL.split("SET")[1].split("WHERE")[0]
    assert "attempts" not in recovery_set_clause
    assert "status = 'pending'" in RECOVER_EXPIRED_SQL
    assert "attempts < :max_attempts" in RECOVER_EXPIRED_SQL
    assert "attempts >= :max_attempts" in RECOVER_EXPIRED_DEAD_SQL
    assert "status = 'dead'" in RECOVER_EXPIRED_DEAD_SQL
