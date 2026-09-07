# End-to-end tests

Reserved for full-stack flows (API + database + worker) once features exist.

In STEP 0 there is nothing user-facing to drive end to end. Tests here must:

- run against a disposable environment (docker compose profile or test DB)
- never touch a development or production database
- be marked `e2e` and excluded from the default offline run
