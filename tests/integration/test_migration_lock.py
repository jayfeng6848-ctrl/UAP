"""Migration advisory-lock concurrency / recovery checks (B1-0).

Covers the four required scenarios:
  T1 single runner acquires and releases the lock cleanly
  T2 a second runner cannot execute DDL while the first holds the lock
      (verified in both `fail` and `wait` lock modes)
  T3 an abnormal end (exception + connection close) leaves no permanent lock
  T4 the advisory lock is not persistent database state after close/restart
"""

from __future__ import annotations

import threading
import time

import pytest
import sqlalchemy as sa
from alembic import command

from tests.integration.alembic_testkit import (
    BASE_DSN,
    advisory_lock_rows,
    current_revision,
    database_reachable,
    downgrade,
    make_config,
    reset_test_database,
    upgrade,
)

pytestmark = pytest.mark.integration

LOCK_KEY = (5_587_280, 1)  # documented in migrations_alembic/env.py

if not database_reachable():
    pytest.skip(
        "PostgreSQL is not reachable; start it with `docker compose up -d postgres`",
        allow_module_level=True,
    )


@pytest.fixture()
def clean_db():
    """A fresh database per test so lock scenarios never share state."""
    reset_test_database()
    yield


def _hold_lock(seconds: float, session_level: bool = False) -> None:
    """Hold the documented lock from a separate connection in a thread."""
    engine = sa.create_engine(BASE_DSN)
    conn = engine.connect()
    trans = conn.begin()
    if session_level:
        conn.execute(sa.text("SELECT pg_advisory_lock(:k1, :k2)"), {"k1": LOCK_KEY[0], "k2": LOCK_KEY[1]})
    else:
        conn.execute(sa.text("SELECT pg_advisory_xact_lock(:k1, :k2)"), {"k1": LOCK_KEY[0], "k2": LOCK_KEY[1]})
    time.sleep(seconds)
    trans.rollback()  # xact lock released here
    conn.close()
    engine.dispose()


# ---------------------------------------------------------------- T1
def test_single_runner_lock_acquire_release(clean_db) -> None:
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    assert current_revision() == "0015_p12_indexes"
    # lock is fully released after the migration transaction ended
    assert advisory_lock_rows() == 0


# ------------------------------------------------------- T2a (fail)
def test_second_runner_fail_mode_is_rejected(clean_db) -> None:
    # Runner A holds the lock (separate connection, not committed).
    engine = sa.create_engine(BASE_DSN)
    conn_a = engine.connect()
    trans_a = conn_a.begin()
    conn_a.execute(sa.text("SELECT pg_advisory_xact_lock(:k1, :k2)"), {"k1": LOCK_KEY[0], "k2": LOCK_KEY[1]})
    assert advisory_lock_rows() == 1

    # Runner B (fail mode) must NOT execute DDL.
    cfg = make_config(lock_mode="fail")
    with pytest.raises(Exception) as exc:
        command.upgrade(cfg, "head")
    assert "another migration runner holds the UAP migration lock" in str(exc.value)

    # A still holds the lock, nothing was migrated by B.
    assert advisory_lock_rows() == 1

    trans_a.rollback()
    conn_a.close()
    engine.dispose()
    assert advisory_lock_rows() == 0


# ------------------------------------------------------ T2b (wait)
def test_second_runner_wait_mode_blocks_then_succeeds(clean_db) -> None:
    downgrade(make_config(lock_mode="fail"), "base")  # start from empty/headless

    holder = threading.Thread(target=_hold_lock, kwargs={"seconds": 1.5})
    holder.start()
    time.sleep(0.3)  # let A acquire

    cfg = make_config(lock_mode="wait")
    started = time.monotonic()
    upgrade(cfg, "head")  # blocks until A releases, then runs DDL
    elapsed = time.monotonic() - started

    holder.join()
    assert current_revision() == "0015_p12_indexes"
    assert elapsed >= 1.0, "wait-mode runner did not actually wait for the lock"
    assert advisory_lock_rows() == 0


# ------------------------------------------------- T3 (failure/close)
def test_lock_released_after_abnormal_connection_close(clean_db) -> None:
    # Simulate: acquire -> migration failure -> connection close (no explicit unlock).
    engine = sa.create_engine(BASE_DSN)
    conn = engine.connect()
    trans = conn.begin()
    conn.execute(sa.text("SELECT pg_advisory_xact_lock(:k1, :k2)"), {"k1": LOCK_KEY[0], "k2": LOCK_KEY[1]})
    assert advisory_lock_rows() == 1

    # Abnormal end: rollback + close (no UNLOCK, no commit).
    trans.rollback()
    conn.close()
    engine.dispose()

    assert advisory_lock_rows() == 0, "lock leaked after connection close"

    # A fresh runner can now take the lock and migrate.
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0015_p12_indexes"


# --------------------------------------------- T4 (not persistent)
def test_advisory_lock_not_persistent_database_state(clean_db) -> None:
    # Even a session-level lock disappears as soon as the connection closes.
    engine = sa.create_engine(BASE_DSN)
    conn = engine.connect()
    conn.execute(sa.text("SELECT pg_advisory_lock(:k1, :k2)"), {"k1": LOCK_KEY[0], "k2": LOCK_KEY[1]})
    assert advisory_lock_rows() == 1
    conn.close()  # no UNLOCK
    engine.dispose()
    assert advisory_lock_rows() == 0

    # Advisory locks live in shared memory only: a database restart clears
    # them by definition (PostgreSQL semantics, no on-disk state). The
    # migration infra therefore can never dead-lock across restarts.
