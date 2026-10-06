"""P20 Company suite fixtures: one disposable database, one seeded world."""

from __future__ import annotations

import pytest
import sqlalchemy as sa

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase

from tests.company import company_testkit as kit


@pytest.fixture(scope="module")
def company_engine():
    kit.create_database()
    try:
        kit.migrate()
        engine = sa.create_engine(kit.FIXTURE_DSN)
        kit.materialize_privileges(engine)
        yield engine
        engine.dispose()
    finally:
        kit.drop_database()


@pytest.fixture(scope="module")
def runtime_db(company_engine):
    database = RuntimeDatabase.from_config(
        DatabaseConfig(url=kit.RUNTIME_DSN), require_role="uap_runtime"
    )
    database.start()
    yield database
    database.dispose()


@pytest.fixture(scope="module")
def world(company_engine) -> dict[str, object]:
    """Platform-level seeds: an authorized actor, an unauthorized actor, three tenants."""
    admin_id = kit.create_user(company_engine, "admin")
    kit.bootstrap_platform_admin(company_engine, user_id=admin_id)
    plain_id = kit.create_user(company_engine, "plain")

    tenant_a = kit.provision_tenant_with_space(company_engine, tag="a")
    tenant_b = kit.provision_tenant_with_space(company_engine, tag="b")
    tenant_c = kit.provision_tenant_with_space(company_engine, tag="c")

    # Company collection projections exist for A and B; C stays unprojected on
    # purpose (a missing projection must deny, never self-heal).
    kit.project_company_collections(company_engine, tenant_id=tenant_a["tenant_id"])
    kit.project_company_collections(company_engine, tenant_id=tenant_b["tenant_id"])

    return {
        "admin_id": admin_id,
        "plain_id": plain_id,
        "tenant_a": tenant_a["tenant_id"],
        "space_a": tenant_a["space_id"],
        "tenant_b": tenant_b["tenant_id"],
        "space_b": tenant_b["space_id"],
        "tenant_c": tenant_c["tenant_id"],
        "space_c": tenant_c["space_id"],
    }
