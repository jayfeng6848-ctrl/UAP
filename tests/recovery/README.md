# Recovery tests

Reserved for failure-injection scenarios:

- database connection loss and reconnect (pool pre-ping)
- process restart with pending migrations
- partial migration rollback (transactional apply)
- cache/queue unavailable while the API stays up

Nothing here yet in STEP 0.
