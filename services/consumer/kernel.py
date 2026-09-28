"""P15 C-5 Event/Outbox Consumer kernel (pure logic · no I/O).

Implements the frozen contract values from PDL Appendix S without touching the
database: deterministic backoff, eligibility, the conditional claim / heartbeat /
complete / recovery SQL text (executed elsewhere by a session-scoped service),
the terminal-reason vocabulary and the CLOSED event allowlist.

Frozen inputs (PDL Appendix S):
  O-2  MAX_ATTEMPTS = 10 · deterministic exponential backoff (base 5s, x2, cap 10min), no jitter
  O-4  worker = 1 · concurrency = 4 · batch <= 10 · lease = 120s · heartbeat = 40s
  O-5  CLOSED ALLOWLIST (currently EMPTY: no producer exists) · unknown type -> dead
  O-6  idempotency must be provable; otherwise the use-case is NOT eligible
"""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_ATTEMPTS = 10
BACKOFF_BASE_SECONDS = 5
BACKOFF_MULTIPLIER = 2
BACKOFF_CAP_SECONDS = 600

WORKER_PROCESS_COUNT = 1
WORKER_CONCURRENCY = 4
CLAIM_BATCH_SIZE = 10
LEASE_SECONDS = 120
HEARTBEAT_SECONDS = 40

TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS = "lease_expired_max_attempts"
TERMINAL_REASON_UNSUPPORTED_EVENT_TYPE = "unsupported_event_type"
TERMINAL_REASON_NON_RETRYABLE = "non_retryable_failure"
TERMINAL_REASON_MAX_ATTEMPTS = "max_attempts_reached"
TERMINAL_REASON_MALFORMED_PAYLOAD = "malformed_payload"
TERMINAL_REASON_AUTHORIZATION_DENIED = "authorization_denied"

#: Idempotency proofs accepted by O-6.
IDEMPOTENCY_PROOFS = frozenset(
    {"naturally_idempotent", "transactional_key", "schema_guaranteed"}
)

#: Exception categories that must never be retried (P14 taxonomy + §5 of the contract).
NON_RETRYABLE_CATEGORIES = frozenset(
    {"authorization", "authentication", "security_boundary", "validation", "configuration"}
)
RETRYABLE_CATEGORIES = frozenset({"connection", "persistence"})


def backoff_seconds(failed_attempt: int) -> int:
    """Deterministic exponential backoff for the n-th failure (O-2): 5,10,20,...,600."""
    if failed_attempt < 1:
        raise ValueError("failed_attempt must be >= 1")
    return min(BACKOFF_BASE_SECONDS * (BACKOFF_MULTIPLIER ** (failed_attempt - 1)),
               BACKOFF_CAP_SECONDS)


def is_terminal_attempt(attempts: int) -> bool:
    """True when a further failure must terminate the event as ``dead``."""
    return attempts >= MAX_ATTEMPTS


def is_eligible(attempts: int) -> bool:
    """Claim eligibility also requires status/next_attempt_at, enforced in SQL."""
    return 0 <= attempts < MAX_ATTEMPTS


def is_retryable(category: str) -> bool:
    """Only transient infrastructure categories may be retried (§5 / P14 never-retry)."""
    if category in NON_RETRYABLE_CATEGORIES:
        return False
    return category in RETRYABLE_CATEGORIES


class UnsupportedEventType(LookupError):
    """The event type is not in the CLOSED allowlist (O-5)."""


@dataclass(frozen=True)
class EventHandlerSpec:
    """A production handler exists only with all four provable properties (O-5/O-6)."""

    event_type: str
    has_producer_evidence: bool
    has_authorization_semantics: bool
    has_acceptance_coverage: bool
    idempotency: str

    @property
    def eligible(self) -> bool:
        return (
            self.has_producer_evidence
            and self.has_authorization_semantics
            and self.has_acceptance_coverage
            and self.idempotency in IDEMPOTENCY_PROOFS
        )


@dataclass
class EventAllowlist:
    """CLOSED allowlist: unknown or ineligible event types are never executed."""

    specs: dict[str, EventHandlerSpec] = field(default_factory=dict)

    def register(self, spec: EventHandlerSpec) -> None:
        if not spec.eligible:
            raise ValueError(
                f"event type {spec.event_type!r} is not eligible: producer evidence + "
                f"authorization semantics + acceptance coverage + provable idempotency "
                f"are all required"
            )
        self.specs[spec.event_type] = spec

    def resolve(self, event_type: str) -> EventHandlerSpec:
        try:
            return self.specs[event_type]
        except KeyError as exc:
            raise UnsupportedEventType(event_type) from exc

    @property
    def is_empty(self) -> bool:
        return not self.specs


def production_allowlist() -> EventAllowlist:
    """P15 production allowlist = EMPTY (no event producer exists; events table 0 rows)."""
    return EventAllowlist()


# --------------------------------------------------------------- frozen SQL text
CLAIM_SQL = (
    "WITH candidate AS ("
    " SELECT id, occurred_at FROM public.events"
    " WHERE status = 'pending'"
    "   AND (next_attempt_at IS NULL OR next_attempt_at <= now())"
    "   AND attempts < :max_attempts"
    " ORDER BY occurred_at"
    " LIMIT :batch_size"
    " FOR UPDATE SKIP LOCKED"
    ") UPDATE public.events e SET status = 'claimed', worker_id = :worker_id,"
    " claimed_at = now(), lease_expires_at = now() + make_interval(secs => :lease)"
    " FROM candidate c"
    " WHERE e.id = c.id AND e.occurred_at = c.occurred_at AND e.status = 'pending'"
    " RETURNING e.id, e.occurred_at, e.event_type, e.schema_version, e.tenant_id,"
    " e.space_id, e.actor_type, e.actor_id, e.payload, e.attempts, e.correlation_id"
)

HEARTBEAT_SQL = (
    "UPDATE public.events SET lease_expires_at = now() + make_interval(secs => :lease)"
    " WHERE id = :id AND occurred_at = :occurred_at AND status = 'claimed'"
    "   AND worker_id = :worker_id AND lease_expires_at > now()"
)

COMPLETE_DELIVERED_SQL = (
    "UPDATE public.events SET status = 'delivered', delivered_at = now(),"
    " last_error = NULL, worker_id = NULL, claimed_at = NULL, lease_expires_at = NULL"
    " WHERE id = :id AND occurred_at = :occurred_at AND status = 'claimed'"
    "   AND worker_id = :worker_id"
)

COMPLETE_PENDING_SQL = (
    "UPDATE public.events SET status = 'pending', attempts = attempts + 1,"
    " next_attempt_at = now() + make_interval(secs => :delay),"
    " last_error = :reason, worker_id = NULL, claimed_at = NULL, lease_expires_at = NULL"
    " WHERE id = :id AND occurred_at = :occurred_at AND status = 'claimed'"
    "   AND worker_id = :worker_id"
)

COMPLETE_DEAD_SQL = (
    "UPDATE public.events SET status = 'dead', attempts = attempts + 1,"
    " last_error = :reason, worker_id = NULL, claimed_at = NULL, lease_expires_at = NULL"
    " WHERE id = :id AND occurred_at = :occurred_at AND status = 'claimed'"
    "   AND worker_id = :worker_id"
)

#: O-1 recovery: expired leases return to pending without adding attempts.
RECOVER_EXPIRED_SQL = (
    "UPDATE public.events SET status = 'pending', worker_id = NULL, claimed_at = NULL,"
    " lease_expires_at = NULL"
    " WHERE status = 'claimed' AND lease_expires_at < now() AND attempts < :max_attempts"
)

RECOVER_EXPIRED_DEAD_SQL = (
    "UPDATE public.events SET status = 'dead', worker_id = NULL, claimed_at = NULL,"
    " lease_expires_at = NULL, last_error = :reason"
    " WHERE status = 'claimed' AND lease_expires_at < now() AND attempts >= :max_attempts"
)


__all__ = [
    "BACKOFF_BASE_SECONDS", "BACKOFF_CAP_SECONDS", "BACKOFF_MULTIPLIER",
    "CLAIM_BATCH_SIZE", "CLAIM_SQL", "COMPLETE_DEAD_SQL", "COMPLETE_DELIVERED_SQL",
    "COMPLETE_PENDING_SQL", "EventAllowlist", "EventHandlerSpec", "HEARTBEAT_SECONDS",
    "HEARTBEAT_SQL", "IDEMPOTENCY_PROOFS", "LEASE_SECONDS", "MAX_ATTEMPTS",
    "NON_RETRYABLE_CATEGORIES", "RECOVER_EXPIRED_DEAD_SQL", "RECOVER_EXPIRED_SQL",
    "RETRYABLE_CATEGORIES", "TERMINAL_REASON_AUTHORIZATION_DENIED",
    "TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS", "TERMINAL_REASON_MALFORMED_PAYLOAD",
    "TERMINAL_REASON_MAX_ATTEMPTS", "TERMINAL_REASON_NON_RETRYABLE",
    "TERMINAL_REASON_UNSUPPORTED_EVENT_TYPE", "UnsupportedEventType",
    "WORKER_CONCURRENCY", "WORKER_PROCESS_COUNT", "backoff_seconds", "is_eligible",
    "is_retryable", "is_terminal_attempt", "production_allowlist",
]
