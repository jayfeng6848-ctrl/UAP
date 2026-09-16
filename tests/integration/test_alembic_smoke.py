"""Alembic smoke checks against a genuinely empty database.

Verifies the migration infrastructure itself (B1-0 scope):
  * infra upgrade reaches head and creates only infrastructure objects
  * NO business table is created by the B1-0 skeleton
  * downgrade base is reversible
  * rerun is idempotent
  * the seeded uap_uuid_v7() function produces RFC 9562 compliant values
"""

from __future__ import annotations

import pytest
import sqlalchemy as sa

from tests.integration.alembic_testkit import (
    BASE_DSN,
    TEST_DB,
    current_revision,
    database_reachable,
    downgrade,
    make_config,
    reset_test_database,
    upgrade,
)

pytestmark = pytest.mark.integration

if not database_reachable():
    pytest.skip(
        "PostgreSQL is not reachable; start it with `docker compose up -d postgres`",
        allow_module_level=True,
    )


@pytest.fixture()
def empty_db():
    """A genuinely empty database per test."""
    reset_test_database()
    yield
    reset_test_database()  # leave the world clean


def _engine():
    return sa.create_engine(BASE_DSN)


def test_upgrade_head_reaches_infrastructure(empty_db) -> None:
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    assert current_revision() == "0009_timestamp_precision"


def test_no_business_table_created(empty_db) -> None:
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    engine = _engine()
    try:
        with engine.connect() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    sa.text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' ORDER BY 1"
                    )
                )
            ]
    finally:
        engine.dispose()
    # head = 0009_timestamp_precision（corrective migration，不新增表）
    #          = 5 identity + 4 tenant/space + 4 authorization + 1 bootstrap state
    #          + 3 resource/ACL (resources/acl_subject_types/resource_permissions)
    #          + 3 tool tables (tools/tool_versions/tool_permissions)
    #          + alembic version.
    # NO other core/business tables (agents/ai_*/events/tool_executions/... yet).
    assert tables == sorted(
        [
            "alembic_version",
            "users", "identities", "credentials", "devices", "sessions",
            "tenants", "spaces", "tenant_memberships", "memberships",
            "roles", "permissions", "role_permissions", "platform_memberships",
            "platform_state",
            "resources", "acl_subject_types", "resource_permissions",
            "tools", "tool_versions", "tool_permissions",
        ]
    ), f"unexpected tables: {tables}"


def test_uuid_v7_function_present_and_compliant(empty_db) -> None:
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    engine = _engine()
    try:
        with engine.connect() as conn:
            ver, var = conn.execute(
                sa.text(
                    "SELECT (get_byte(uuid_send(uap_uuid_v7()), 6) >> 4)::int AS ver,"
                    "       (get_byte(uuid_send(uap_uuid_v7()), 8) >> 6)::int AS var"
                )
            ).one()
            assert (ver, var) == (7, 2), f"expected version=7 variant=2, got {ver},{var}"

            n, distinct = conn.execute(
                sa.text(
                    "SELECT count(*), count(DISTINCT v) FROM "
                    "(SELECT uap_uuid_v7() AS v FROM generate_series(1, 5000)) s"
                )
            ).one()
            assert n == distinct == 5000

            ts_ok = conn.execute(
                sa.text(
                    "SELECT count(*) FROM "
                    "(SELECT uap_uuid_v7() AS v FROM generate_series(1, 2000)) s "
                    "WHERE (get_byte(uuid_send(v),0)::bigint << 40)"
                    "    + (get_byte(uuid_send(v),1)::bigint << 32)"
                    "    + (get_byte(uuid_send(v),2)::bigint << 24)"
                    "    + (get_byte(uuid_send(v),3)::bigint << 16)"
                    "    + (get_byte(uuid_send(v),4)::bigint << 8)"
                    "    + get_byte(uuid_send(v),5)::bigint > 0"
                )
            ).scalar()
            assert ts_ok == 2000
    finally:
        engine.dispose()


def test_downgrade_base_is_reversible(empty_db) -> None:
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    downgrade(cfg, "base")
    assert current_revision() is None  # no revision applied
    engine = _engine()
    try:
        with engine.connect() as conn:
            fn = conn.execute(
                sa.text(
                    "SELECT count(*) FROM pg_proc WHERE proname = 'uap_uuid_v7'"
                )
            ).scalar()
            tables = [
                r[0]
                for r in conn.execute(
                    sa.text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
            ]
    finally:
        engine.dispose()
    assert fn == 0
    # Alembic may keep an (empty) version table after downgrade base; the
    # important invariant is that nothing migrated remains applied.
    assert set(tables).issubset({"alembic_version"}), f"unexpected tables: {tables}"
    # And from this state a fresh upgrade works again (round trip).
    upgrade(cfg, "head")
    assert current_revision() == "0009_timestamp_precision"


def test_upgrade_rerun_idempotent(empty_db) -> None:
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    upgrade(cfg, "head")  # second run is a no-op but must still succeed
    assert current_revision() == "0009_timestamp_precision"
