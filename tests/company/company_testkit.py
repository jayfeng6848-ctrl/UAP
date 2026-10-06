"""Shared harness for the P20 Company suite (not collected as tests).

Creates a dedicated disposable database (``uap_p20_domain_test``) — never ``uap``,
never ``uap_b1_test`` — migrates it to head (0019 + 0020), materializes the frozen
runtime privilege baseline additively and seeds *platform-level* fixtures the way
the platform itself does (bootstrap membership, control-plane provisioning, then
the Company collection projection).
"""

from __future__ import annotations

import uuid
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from scripts.privileges import materialize as materialize_baseline_privileges
from services.company.projection import ensure_company_collections
from services.control_plane import provision_space, provision_tenant

ROOT = Path(__file__).resolve().parents[2]
TEST_DB = "uap_p20_domain_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{TEST_DB}"
MIGRATION_DSN = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{TEST_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{TEST_DB}"

PLATFORM_ADMIN_KEY = "platform_admin"


def create_database() -> None:
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{TEST_DB}" OWNER uap_migrator'))
    admin.dispose()


def drop_database() -> None:
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
    admin.dispose()


def migrate() -> None:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = MIGRATION_DSN
    cfg.attributes["lock_mode"] = "wait"
    command.upgrade(cfg, "head")


def materialize_privileges(engine: sa.Engine) -> int:
    """Apply the frozen runtime baseline additively (never revokes 0019/0020 grants)."""
    return materialize_baseline_privileges(engine)


def _platform_admin_role_id(conn: sa.Connection) -> str:
    row = conn.execute(
        sa.text(
            "SELECT id FROM roles WHERE key = :key AND scope = 'PLATFORM'"
            " AND tenant_id IS NULL AND space_id IS NULL"
        ),
        {"key": PLATFORM_ADMIN_KEY},
    ).fetchone()
    if row is None:
        raise RuntimeError("platform_admin role missing: 0005 must own it")
    return str(row[0])


def create_user(engine: sa.Engine, tag: str) -> str:
    stamp = uuid.uuid4().hex[:10]
    with engine.begin() as conn:
        return str(
            conn.execute(
                sa.text(
                    "INSERT INTO users (email, status) VALUES (:email, 'active') RETURNING id"
                ),
                {"email": f"p20-{tag}-{stamp}@example.invalid"},
            ).scalar_one()
        )


def bootstrap_platform_admin(engine: sa.Engine, *, user_id: str) -> str:
    """Mirror the frozen bootstrap path: first membership, then the one-way state flip."""
    with engine.begin() as conn:
        # 0006 already owns the singleton platform_state row; inserting it again is
        # rejected by the guard (the row is permanent), so only flip it — after the
        # first platform membership exists, exactly as the frozen bootstrap does.
        role_id = _platform_admin_role_id(conn)
        conn.execute(
            sa.text(
                "INSERT INTO platform_memberships (user_id, role_id, status)"
                " VALUES (CAST(:u AS uuid), CAST(:r AS uuid), 'active')"
            ),
            {"u": user_id, "r": role_id},
        )
        conn.execute(
            sa.text(
                "UPDATE platform_state SET bootstrap_state = 'initialized',"
                " initialized_at = now() WHERE id = 1"
            )
        )
    return role_id


def provision_tenant_with_space(
    engine: sa.Engine, *, tag: str
) -> dict[str, str]:
    """Provision one tenant plus one space through the canonical control-plane path."""
    stamp = uuid.uuid4().hex[:10]
    with engine.begin() as conn:
        from sqlalchemy.orm import Session

        session = Session(bind=conn)
        tenant = provision_tenant(
            session, slug=f"p20-{tag}-{stamp}", display_name=f"P20 {tag}",
            status="active",
        )
        space = provision_space(
            session, tenant_id=tenant["tenant_id"], key=f"dept-{tag}-{stamp}",
            name=f"P20 {tag} dept", status="active",
        )
    return {"tenant_id": tenant["tenant_id"], "space_id": space["space_id"]}


def project_company_collections(engine: sa.Engine, *, tenant_id: str) -> dict[str, str]:
    """Pre-provision both Company collection resources (operator path)."""
    with engine.begin() as conn:
        from sqlalchemy.orm import Session

        return ensure_company_collections(Session(bind=conn), tenant_id=tenant_id)


def audit_rows(engine: sa.Engine, *, tenant_id: str, action: str | None = None) -> list[dict]:
    """Read audit rows for one tenant (used by the service assertions)."""
    sql = (
        "SELECT id, action, resource_type, resource_id, result, risk_level, metadata"
        " FROM audit_logs WHERE tenant_id = CAST(:t AS uuid)"
    )
    params: dict[str, object] = {"t": tenant_id}
    if action is not None:
        sql += " AND action = :action"
        params["action"] = action
    sql += " ORDER BY occurred_at, id"
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


__all__ = [
    "ADMIN_DSN",
    "FIXTURE_DSN",
    "MIGRATION_DSN",
    "PLATFORM_ADMIN_KEY",
    "RUNTIME_DSN",
    "TEST_DB",
    "audit_rows",
    "bootstrap_platform_admin",
    "create_database",
    "create_user",
    "drop_database",
    "materialize_privileges",
    "migrate",
    "project_company_collections",
    "provision_tenant_with_space",
]
