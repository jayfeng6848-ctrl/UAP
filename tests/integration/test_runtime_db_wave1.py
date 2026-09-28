"""Wave 1 §8-§18 -- runtime database boundary against a live PostgreSQL.

The runtime identity and credential resolution live in
``tests.integration.runtime_testkit``; see that module for the DC-7 / §17 rules
that keep this suite from producing false-positive security evidence.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.principal import role_from_url
from infrastructure.database.runtime import RuntimeDatabase
from infrastructure.runtime.errors import PrincipalAssertionError, TransactionError
from infrastructure.runtime.lifecycle import LifecycleState, RuntimeApplication
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def runtime_config() -> DatabaseConfig:
    return DatabaseConfig(url=runtime_test_dsn())


@pytest.fixture
def runtime_db(runtime_config: DatabaseConfig):
    db = RuntimeDatabase.from_config(runtime_config, require_role=REQUIRED_ROLE)
    db.start()
    try:
        yield db
    finally:
        db.dispose()


# --------------------------------------------------------------------- startup
def test_runtime_connects_as_uap_runtime(runtime_config: DatabaseConfig) -> None:
    db = RuntimeDatabase.from_config(runtime_config, require_role=REQUIRED_ROLE)
    principal = db.start()
    try:
        assert principal == {
            "current_user": REQUIRED_ROLE,
            "session_user": REQUIRED_ROLE,
        }
        assert db.principal == principal
        assert db.started is True
        assert db.health() == (True, None)
    finally:
        db.dispose()


def test_dsn_role_is_read_from_the_url(runtime_config: DatabaseConfig) -> None:
    assert role_from_url(runtime_config.url) == REQUIRED_ROLE


def test_principal_assertion_is_enforced_not_merely_configured(
    runtime_config: DatabaseConfig,
) -> None:
    """A mismatch between URL role and required role must fail closed."""
    db = RuntimeDatabase.from_config(runtime_config, require_role="uap_migrator")
    with pytest.raises(PrincipalAssertionError):
        db.start()
    assert db.started is False, "the pool must not survive a failed assertion"


def test_start_is_not_idempotent(runtime_db: RuntimeDatabase) -> None:
    with pytest.raises(TransactionError):
        runtime_db.start()


def test_health_is_false_before_start(runtime_config: DatabaseConfig) -> None:
    db = RuntimeDatabase.from_config(runtime_config, require_role=REQUIRED_ROLE)
    assert db.health() == (False, "runtime database not started")
    with pytest.raises(TransactionError):
        with db.transaction():
            pass


# ------------------------------------------------------------- persistence path
def test_approved_reads(runtime_db: RuntimeDatabase) -> None:
    with runtime_db.transaction() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1
        counts = {
            name: session.execute(text(f"SELECT count(*) FROM public.{name}")).scalar()
            for name in ("acl_subject_types", "permissions", "role_permissions")
        }
        users = session.execute(text("SELECT count(*) FROM public.users")).scalar()
        audit = session.execute(text("SELECT count(*) FROM public.audit_logs")).scalar()
    assert counts == {"acl_subject_types": 3, "permissions": 12, "role_permissions": 12}
    assert users == 0
    assert audit == 0


def test_transaction_commit_is_durable(runtime_db: RuntimeDatabase) -> None:
    """Direct COMMIT evidence: the transaction's xid ends up *committed*.

    ``pg_xact_status`` is read from a *separate* transaction, so this is
    external proof that COMMIT happened -- not an inference from "no error".
    """
    with runtime_db.transaction() as session:
        xid = session.execute(text("SELECT pg_current_xact_id()")).scalar()

    with runtime_db.transaction() as session:
        status = session.execute(
            text("SELECT pg_xact_status(CAST(:xid AS xid8))"), {"xid": str(xid)}
        ).scalar()
    assert status == "committed", f"transaction {xid} did not commit (status={status})"


def test_transaction_rollback_is_observed(runtime_db: RuntimeDatabase) -> None:
    """The counterpart proof: a failed boundary leaves an *aborted* transaction."""
    observed: dict[str, object] = {}
    with pytest.raises(RuntimeError):
        with runtime_db.transaction() as session:
            observed["xid"] = session.execute(
                text("SELECT pg_current_xact_id()")
            ).scalar()
            raise RuntimeError("use-case failed after the write")

    with runtime_db.transaction() as session:
        status = session.execute(
            text("SELECT pg_xact_status(CAST(:xid AS xid8))"),
            {"xid": str(observed["xid"])},
        ).scalar()
    assert status == "aborted"


def test_rollback_leaves_no_residue(runtime_db: RuntimeDatabase) -> None:
    """A rolled-back write must not persist (and no test row is left behind)."""
    # ``ck_users_login`` requires email or username; the insert is authorised for
    # uap_runtime and is *always* rolled back below.
    with pytest.raises(RuntimeError):
        with runtime_db.transaction() as session:
            session.execute(
                text(
                    "INSERT INTO public.users (email, status)"
                    " VALUES ('wave1-probe@example.invalid', 'active') RETURNING id"
                )
            ).scalar()
            raise RuntimeError("abort the use-case")

    with runtime_db.transaction() as session:
        assert session.execute(text("SELECT count(*) FROM public.users")).scalar() == 0


def test_rolled_back_session_does_not_poison_the_pool(runtime_db: RuntimeDatabase) -> None:
    """DC-22: after a rollback the pooled connection is reusable."""
    with pytest.raises(SQLAlchemyError):
        with runtime_db.transaction() as session:
            session.execute(text("SELECT * FROM public.no_such_table_wave1"))

    with runtime_db.transaction() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1
    assert runtime_db.health() == (True, None)


# --------------------------------------------------------------------- shutdown
def test_dispose_is_idempotent_and_releases_the_pool(runtime_config: DatabaseConfig) -> None:
    db = RuntimeDatabase.from_config(runtime_config, require_role=REQUIRED_ROLE)
    db.start()
    db.dispose()
    assert db.started is False
    assert db.health() == (False, "runtime database not started")
    db.dispose()  # second call must not raise


def test_application_lifecycle_against_live_database(
    runtime_config: DatabaseConfig,
) -> None:
    app = RuntimeApplication()
    result = app.start(config=runtime_config, require_role=REQUIRED_ROLE)
    try:
        assert app.state is LifecycleState.STARTED
        assert result.principal == {
            "current_user": REQUIRED_ROLE,
            "session_user": REQUIRED_ROLE,
        }
        assert app.health() == (True, None)
    finally:
        app.stop()
    assert app.state is LifecycleState.STOPPED


# ------------------------------------------------------------------ observability
def test_describe_never_leaks_the_credential(runtime_db: RuntimeDatabase) -> None:
    described = runtime_db.describe()
    rendered = str(described)
    assert described["principal"] == {
        "current_user": REQUIRED_ROLE,
        "session_user": REQUIRED_ROLE,
    }
    # The password never survives into a log-safe description (DC-12).
    assert ":uap_runtime@" not in rendered
    assert ":uap_runtime:" not in rendered
    assert ":***@" in runtime_db.config.safe_url()
    assert runtime_db.config.url not in rendered, "raw DSN must never be described"
