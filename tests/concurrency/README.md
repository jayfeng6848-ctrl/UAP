# Concurrency tests

Reserved for races that only appear under parallel load:

- concurrent session creation / revocation
- concurrent migration attempts (advisory locking)
- duplicate event delivery and idempotency
- concurrent tool invocation with the same idempotency key

Nothing here yet in STEP 0.
