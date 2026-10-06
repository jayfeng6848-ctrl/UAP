"""P20 authorization migration tests (0020_p20_company_authorization).

Proves the frozen G1 decision end to end on a disposable database: the 11 Company
permissions are bound to ``platform_admin`` as ``allow`` rows, the downgrade
removes **only** those bindings (its own ownership) and leaves the permission
vocabulary untouched, and a re-upgrade restores exactly the same state.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
TEST_DB = "uap_p20_authz_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
MIGRATION_DSN = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{TEST_DB}"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{TEST_DB}"


def _company_permission_keys() -> tuple[str, ...]:
    """Read the frozen key list from the migration itself (single source of truth)."""
    path = ROOT / "migrations_alembic" / "versions" / "0020_p20_company_authorization.py"
    spec = importlib.util.spec_from_file_location("p20_0020_migration", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return tuple(module.COMPANY_PERMISSION_KEYS)


COMPANY_PERMISSION_KEYS = _company_permission_keys()


def _config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = MIGRATION_DSN
    cfg.attributes["lock_mode"] = "wait"
    return cfg


def _company_grants(engine: sa.Engine) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT p.key FROM role_permissions rp"
                " JOIN permissions p ON p.id = rp.permission_id"
                " JOIN roles r ON r.id = rp.role_id"
                " WHERE r.key = 'platform_admin' AND rp.effect = 'allow'"
                "   AND p.key = ANY(:keys)"
            ),
            {"keys": list(COMPANY_PERMISSION_KEYS)},
        ).all()
    return {str(row[0]) for row in rows}


def _counts(engine: sa.Engine) -> tuple[int, int]:
    with engine.connect() as conn:
        permissions = conn.execute(sa.text("SELECT count(*) FROM permissions")).scalar_one()
        grants = conn.execute(
            sa.text(
                "SELECT count(*) FROM role_permissions rp"
                " JOIN roles r ON r.id = rp.role_id WHERE r.key = 'platform_admin'"
                " AND rp.effect = 'allow'"
            )
        ).scalar_one()
    return int(permissions), int(grants)


def test_0020_grants_platform_admin_and_downgrade_is_owned() -> None:
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{TEST_DB}" OWNER uap_migrator'))
    admin.dispose()

    try:
        command.upgrade(_config(), "head")
        engine = sa.create_engine(FIXTURE_DSN)

        permissions, platform_grants = _counts(engine)
        assert permissions == 23  # 12 platform + 11 company
        assert _company_grants(engine) == set(COMPANY_PERMISSION_KEYS)
        assert platform_grants == 12 + len(COMPANY_PERMISSION_KEYS)

        command.downgrade(_config(), "0019_p20_company")
        permissions, platform_grants = _counts(engine)
        assert _company_grants(engine) == set()
        assert permissions == 23  # the permission rows are 0019's, not 0020's
        assert platform_grants == 12  # only the 0020 bindings were removed

        command.upgrade(_config(), "head")
        assert _company_grants(engine) == set(COMPANY_PERMISSION_KEYS)
        engine.dispose()
    finally:
        admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
        with admin.begin() as conn:
            conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
        admin.dispose()
