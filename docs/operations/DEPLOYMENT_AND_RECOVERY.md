# Deployment and Recovery

**Scope**: minimum operational contract for deploying UAP with the readiness
schema gate enabled. This document is a **manual plus command contract** — it is
not an executable pipeline, and nothing here is run automatically.

**Authority**:
`D-PLAT-08` (+ note) · `D-PLAT-14` · `D-PLAT-15 v2` · `D-PLAT-16` ·
`STEP1B_MIGRATION_IMPLEMENTATION_CONTRACT.md` §1 / §11 / §12 / §16.

**Hard rule**: never mutate a real production database by following this
document during a non-deployment activity. Backups and restores are operator
actions, not agent actions.

---

## 0. Deployment order (invariant)

```text
build image (revision frozen from the Alembic graph)
      ↓
backup            D-R-2
      ↓
verify backup     D-R-2
      ↓
migrate           D-R-3   (alembic upgrade head only)
      ↓
start / rollout   D-R-5   (new image, after the migration)
      ↓
/ready            D-R-6   (must be 200 before traffic is accepted)
```

Starting an image **before** its migration step makes `/ready` answer `503` by
design (see D-R-7). That is the gate working, not a failure.

---

## D-R-1 — Build revision comes from the artifact

- The expected schema revision is **derived at image build time** from the
  Alembic graph (`migrations_alembic/versions/`) and frozen into
  `config/_build_info.py` inside the image.
- There is **no** Docker `ARG`, **no** compose literal and **no** environment
  variable that carries an authoritative revision. Runtime configuration cannot
  override the artifact.
- Record per deployment (release manifest / change ticket):

```text
git commit          = <sha of the deployed source>
image digest        = <registry/image@sha256:…>
artifact revision   = EXPECTED_ALEMBIC_REVISION (inside the image)
database revision   = alembic current (after D-R-3)
```

- Inspect the frozen value without starting traffic:

```bash
docker run --rm --entrypoint python <image> \
  -c "from config.build_info import get_artifact_revision; print(get_artifact_revision())"
```

- Inspect the database revision (read-only):

```bash
alembic current
# or: psql -c "SELECT version_num FROM alembic_version;"
```

`artifact revision == database revision` is the deployment's consistency
contract; `/ready` enforces it continuously (D-R-6).

---

## D-R-2 — Backup before any migration

**Mandatory, and an explicit human gate.** No `alembic upgrade` without a
verified backup of the target database.

```bash
# 1. custom-format dump (or a PITR baseline, whichever the environment uses)
pg_dump -Fc -h <host> -U <migrator> -d <database> -f uap_<utc-timestamp>.dump

# 2. verify the archive is readable and complete
pg_restore --list uap_<utc-timestamp>.dump > /dev/null

# 3. record evidence
```

Backup evidence required for the deployment record:

```text
backup artifact path
pg_restore --list output (exit 0)
backup id
timestamp (UTC)
target revision            (= the revision the database will be at after D-R-3)
```

If any of the five items is missing, **stop**: the deployment is not authorised.

---

## D-R-3 — Migrate (Alembic is the only entry point)

```bash
alembic upgrade head
```

- Only `head` is allowed for a forward deployment; do not target an arbitrary
  revision to "match" a running image.
- Alembic is the sole schema entry point (`alembic.ini` + `migrations_alembic/`).
  Do **not** run the legacy `.sql` runner (`scripts/migrate.py`) and do **not**
  execute DDL with `psql` (Contract §1).
- The Alembic run takes a PostgreSQL advisory lock, so a single runner at a time
  is guaranteed (Contract §11).
- The application **never** applies migrations at startup.

---

## D-R-4 — Maintenance window

- Run D-R-2 and D-R-3 inside an announced maintenance window.
- Expect readiness to be `503` for the whole window for any image whose artifact
  revision does not yet match the database — that is intended.
- Do not scale up new replicas of the old image during the window (D-R-7).

---

## D-R-5 — Start / roll out after the migration

- Start or roll out the **new** image only after D-R-3 has completed.
- Rolling releases: because the gate requires **strict equality**, an old image
  whose artifact precedes the new head will report `503` once the database has
  moved. Finish the rollout promptly; do not leave old and new revisions serving
  side by side for longer than the window (~ `OD-3` assigns this compatibility
  responsibility to the deployment process).
- The deployer must not "fix" a `503` by setting `EXPECTED_ALEMBIC_REVISION` in
  the environment: the artifact wins and the mismatch is a real one.

---

## D-R-6 — Post-upgrade checks (smoke)

```text
1. alembic current                     == artifact revision inside the image
2. GET /health                         == 200 (liveness, no database I/O)
3. GET /ready                          == 200 ("status": "ready")
4. application logs                    no ERROR entries since startup
5. read-only sample queries            representative tables still readable
   (e.g. SELECT count(*) FROM agents; on an environment where that is expected)
```

Only after all five pass may the deployment be declared complete.

---

## D-R-7 — Readiness failure decision tree

| `/ready` component state | Meaning | Action |
|---|---|---|
| `migration`: `expected` is `null`, `source` = `missing` | the image carries no usable artifact (e.g. a locally run process without one) | run the image built by CI, or (development only) export a revision locally — never on a shared environment |
| `migration`: `error` "expected revision is missing or invalid" | expectation unusable | rebuild/redeploy a correct image; do not patch the database |
| `migration`: `error` "alembic_version is unreadable / table missing" | database not migrated at all | execute D-R-2 then D-R-3 |
| `migration`: `error` "revision mismatch: expected X actual Y" with `actual` older | deployment ahead of the database | execute D-R-3 |
| `migration`: `error` "revision mismatch …" with `actual` newer | database ahead of the image | roll out the matching image (or forward-fix); **never** "fix" by editing the expectation |
| `migration`: `error` "holds N rows" | multiple heads written — a broken migration run | investigate with a human; do not delete rows blindly |
| `migration`: `error` containing "statement timeout" | database slow/locked beyond 2000 ms | treat as infrastructure incident; the probe is bounded by design (`D-PLAT-16`) |
| `database`: `error` | connectivity/auth/target problem | infrastructure; `/ready` stays `503` by design |
| `optional` entries (`cache`, `queue`, `ai_gateway`) | never affect readiness | ignore for readiness purposes |

`/health` returning 200 while `/ready` returns 503 is the **expected** signature
of "process alive, platform not ready". Do not wire an orchestrator to restart on
`/ready` failures.

---

## F-1 — Rollback is coupled to the database schema state

**Architectural property, not a defect:**

```text
strict readiness equality  +  image-bound build artifact
        ⇒  the application rollback cannot be performed as "image only"
```

An application rollback that ignores the database leaves the old image with an
artifact revision older than `alembic_version`, so the old pods report `503`
forever. Choose one of:

```text
application rollback
        +
database downgrade            (only when the downgrade is proven safe)
```

or

```text
forward-fix                   (ship a new image at the current head)
```

Rules for the database side:

- Prefer **backup restore** for a data/schema incident (Contract §11 / §12).
- `alembic downgrade` is allowed **only** when all three hold:
  previous version available · no data loss · downgrade proven safe.
- Never downgrade away audit/immutable data (Contract §10).

Before any rollback, re-run D-R-2 (a fresh backup of the *current* state).

---

## Failure triage summary

```text
/health 200 + /ready 503  →  schema/connectivity gate; follow D-R-7
/health 503               →  process/container problem; not a schema issue
/ready 200 unexpectedly   →  investigate: the gate should be strict
backup gate not satisfied →  stop the deployment
```
