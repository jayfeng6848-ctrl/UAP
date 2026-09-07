# Security docs

Model, threat notes and hardening checklist live here.

Implemented in STEP 0:
- default-deny authorization contract (`core/permission`)
- automatic credential redaction in structured logs
- readiness/liveness separation so a dependency outage cannot crash-loop the API
- secret placeholder refused outside development/test
- automated secret scanning (`tests/security`)
