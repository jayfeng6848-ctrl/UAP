"""P15 C-5 Event/Outbox Consumer (primary theme of P15).

Batch 1 — kernel (frozen pure logic + SQL text + CLOSED allowlist).
Batch 2 — session-scoped ClaimService (claim / lease / heartbeat / recovery).
Batch 3 — ConsumerWorker (entry / lifecycle / bounded concurrency / shutdown).

Not yet executed: full P15 acceptance (Batch 4) and cross-wave regression.
Production allowlist and production handler registry are EMPTY by design.
"""

from .kernel import (
    BACKOFF_BASE_SECONDS, BACKOFF_CAP_SECONDS, BACKOFF_MULTIPLIER, CLAIM_BATCH_SIZE,
    CLAIM_SQL, COMPLETE_DEAD_SQL, COMPLETE_DELIVERED_SQL, COMPLETE_PENDING_SQL,
    HEARTBEAT_SECONDS, HEARTBEAT_SQL, IDEMPOTENCY_PROOFS, LEASE_SECONDS, MAX_ATTEMPTS,
    RECOVER_EXPIRED_DEAD_SQL, RECOVER_EXPIRED_SQL, TERMINAL_REASON_AUTHORIZATION_DENIED,
    TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS, TERMINAL_REASON_MALFORMED_PAYLOAD,
    TERMINAL_REASON_MAX_ATTEMPTS, TERMINAL_REASON_NON_RETRYABLE,
    TERMINAL_REASON_UNSUPPORTED_EVENT_TYPE, WORKER_CONCURRENCY, WORKER_PROCESS_COUNT,
    EventAllowlist, EventHandlerSpec, UnsupportedEventType, backoff_seconds, is_eligible,
    is_retryable, is_terminal_attempt, production_allowlist,
)
from .worker import (
    ConsumerWorker,
    HandlerExecutionError,
    WorkerConfig,
    WorkerConfigurationError,
    WorkerStartupError,
    WorkerState,
)

__all__ = [
    "BACKOFF_BASE_SECONDS", "BACKOFF_CAP_SECONDS", "BACKOFF_MULTIPLIER", "CLAIM_BATCH_SIZE",
    "CLAIM_SQL", "COMPLETE_DEAD_SQL", "COMPLETE_DELIVERED_SQL", "COMPLETE_PENDING_SQL",
    "EventAllowlist", "EventHandlerSpec", "HEARTBEAT_SECONDS", "HEARTBEAT_SQL",
    "IDEMPOTENCY_PROOFS", "LEASE_SECONDS", "MAX_ATTEMPTS", "RECOVER_EXPIRED_DEAD_SQL",
    "RECOVER_EXPIRED_SQL", "TERMINAL_REASON_AUTHORIZATION_DENIED",
    "TERMINAL_REASON_LEASE_EXPIRED_MAX_ATTEMPTS", "TERMINAL_REASON_MALFORMED_PAYLOAD",
    "TERMINAL_REASON_MAX_ATTEMPTS", "TERMINAL_REASON_NON_RETRYABLE",
    "TERMINAL_REASON_UNSUPPORTED_EVENT_TYPE", "UnsupportedEventType", "WORKER_CONCURRENCY",
    "WORKER_PROCESS_COUNT", "backoff_seconds", "is_eligible", "is_retryable",
    "is_terminal_attempt", "production_allowlist",
    "ConsumerWorker", "HandlerExecutionError", "WorkerConfig", "WorkerConfigurationError",
    "WorkerStartupError", "WorkerState",
]
