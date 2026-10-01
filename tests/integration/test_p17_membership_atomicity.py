"""P17 WAVE 4 carrier evidence: membership mutation + audit are one transaction.

This suite verifies the *carrier* semantics the frozen decision requires
(P17-D11 / OQ-08 / §24 / §50):

* a successful mutation and its audit row both survive;
* a delete keeps ``role_before`` as a durable audit fact;
* an audit failure rolls the membership mutation back (verified from an
  independent connection), i.e. ``audit failure ⇒ no membership change``.

It deliberately does **not** exercise any API or use-case: the authorization
gate that must precede a membership mutation is unresolved (see
``docs/architecture/P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md``), so no
public entry point exists yet.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from scripts.privileges import materialize as materialize_baseline_privileges
from services.identity_runtime import ErrorCode, IdentityRuntimeError, MembershipRuntime

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
P17_DB = "uap_p17_atomic_test"
ADMIN_DSN = "postgresql+psycopg://uap:uap@localhost:5432/postgres"
FIXTURE_DSN = f"postgresql+psycopg://uap:uap@localhost:5432/{P17_DB}"
RUNTIME_DSN = f"postgresql+psycopg://uap_runtime:trust@localhost:5432/{P17_DB}"


@pytest.fixture(scope="module")
def engine():
    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P17_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{P17_DB}" OWNER uap_migrator'))
    admin.dispose()

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = f"postgresql+psycopg://uap_migrator:trust@localhost:5432/{P17_DB}"
    cfg.attributes["lock_mode"] = "wait"
    command.upgrade(cfg, "head")

    fixtures = sa.create_engine(FIXTURE_DSN)
    materialize_baseline_privileges(fixtures)
    yield fixtures
    fixtures.dispose()

    admin = sa.create_engine(ADMIN_DSN, isolation_level="AUTOCOMMIT")
    with admin.begin() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{P17_DB}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def runtime():
    runtime_engine = sa.create_engine(RUNTIME_DSN)
    yield runtime_engine
    runtime_engine.dispose()


@pytest.fixture(scope="module")
def ids(engine) -> dict[str, str]:
    ids: dict[str, str] = {}
    with engine.begin() as conn:
        ids["tenant"] = str(conn.execute(
            sa.text(
                "INSERT INTO tenants (slug, display_name, status)"
                " VALUES (:slug, 'P17 Atomic', 'active') RETURNING id"
            ),
            {"slug": f"p17-atomic-{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        ids["role"] = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (:t, NULL, :k, 'Atomic Tenant Role', 'TENANT', 'active') RETURNING id"
            ),
            {"t": ids["tenant"], "k": f"p17_atomic_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        for key in ("actor", "target"):
            ids[key] = str(conn.execute(
                sa.text("INSERT INTO users (email, status) VALUES (:e, 'active') RETURNING id"),
                {"e": f"p17-atomic-{key}-{uuid.uuid4().hex[:8]}@example.invalid"},
            ).scalar_one())
    return ids


def _rows(engine, sql: str, **params):
    with engine.begin() as conn:
        return [dict(row._mapping) for row in conn.execute(sa.text(sql), params).all()]


def test_create_writes_membership_and_audit_in_one_transaction(runtime, engine, ids) -> None:
    correlation = str(uuid.uuid4())
    membership_id = None
    with runtime.begin() as conn:
        session = Session(bind=conn)
        membership_id = MembershipRuntime().create_tenant_membership(
            session, actor_id=ids["actor"], actor_type="USER", tenant_id=ids["tenant"],
            user_id=ids["target"], role_id=ids["role"], correlation_id=correlation,
        )

    # Independent connection: both facts are durable.
    members = _rows(
        engine,
        "SELECT * FROM tenant_memberships WHERE tenant_id = CAST(:t AS uuid)"
        " AND user_id = CAST(:u AS uuid)",
        t=ids["tenant"], u=ids["target"],
    )
    assert len(members) == 1 and str(members[0]["id"]) == membership_id
    assert members[0]["status"] == "active"

    audits = _rows(
        engine,
        "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)",
        c=correlation,
    )
    assert len(audits) == 1
    audit = audits[0]
    assert audit["action"] == "create"
    assert str(audit["actor_id"]) == ids["actor"]
    assert str(audit["tenant_id"]) == ids["tenant"]
    assert str(audit["metadata"]["target_user_id"]) == ids["target"]
    assert str(audit["metadata"]["role_after"]) == ids["role"]
    assert "role_before" not in audit["metadata"]


def test_update_records_role_before_and_after(runtime, engine, ids) -> None:
    with engine.begin() as conn:
        second_role = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (:t, NULL, :k, 'Atomic Tenant Role 2', 'TENANT', 'active') RETURNING id"
            ),
            {"t": ids["tenant"], "k": f"p17_atomic2_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
    correlation = str(uuid.uuid4())
    with runtime.begin() as conn:
        session = Session(bind=conn)
        MembershipRuntime().update_tenant_membership(
            session, actor_id=ids["actor"], actor_type="USER", tenant_id=ids["tenant"],
            user_id=ids["target"], role_id=second_role, correlation_id=correlation,
        )
    audits = _rows(
        engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)", c=correlation
    )
    assert len(audits) == 1
    assert str(audits[0]["metadata"]["role_before"]) == ids["role"]
    assert str(audits[0]["metadata"]["role_after"]) == second_role


def test_delete_keeps_the_audit_fact_after_the_row_is_removed(runtime, engine, ids) -> None:
    correlation = str(uuid.uuid4())
    with runtime.begin() as conn:
        session = Session(bind=conn)
        MembershipRuntime().delete_tenant_membership(
            session, actor_id=ids["actor"], actor_type="USER", tenant_id=ids["tenant"],
            user_id=ids["target"], correlation_id=correlation,
        )
    members = _rows(
        engine,
        "SELECT status, role_id FROM tenant_memberships WHERE tenant_id = CAST(:t AS uuid)"
        " AND user_id = CAST(:u AS uuid)",
        t=ids["tenant"], u=ids["target"],
    )
    assert members[0]["status"] == "removed"
    audits = _rows(
        engine, "SELECT * FROM audit_logs WHERE correlation_id = CAST(:c AS uuid)", c=correlation
    )
    assert len(audits) == 1 and audits[0]["action"] == "delete"
    assert audits[0]["metadata"]["role_before"]  # the historical role survives the removal


def test_unaudited_membership_mutation_is_impossible(runtime, engine, ids) -> None:
    """Audit failure ⇒ the membership mutation rolls back (atomic security write).

    The audit carrier casts ``correlation_id`` to ``uuid``; a non-uuid value
    makes the audit INSERT fail inside the same transaction as the membership
    write, so an independent connection must observe **no** membership row.
    """
    with pytest.raises(sa.exc.SQLAlchemyError):
        with runtime.begin() as conn:
            session = Session(bind=conn)
            MembershipRuntime().create_tenant_membership(
                session, actor_id=ids["actor"], actor_type="USER", tenant_id=ids["tenant"],
                user_id=ids["actor"], role_id=ids["role"], correlation_id="not-a-uuid",
            )
    leaked = _rows(
        engine,
        "SELECT * FROM tenant_memberships WHERE tenant_id = CAST(:t AS uuid)"
        " AND user_id = CAST(:u AS uuid)",
        t=ids["tenant"], u=ids["actor"],
    )
    assert leaked == [], "the membership row must not survive an audit failure"


def test_scope_mismatch_targets_are_rejected_before_any_write(runtime, engine, ids) -> None:
    """N3/N8: a foreign / wrong-scope role is refused, and nothing is written."""
    with engine.begin() as conn:
        foreign_tenant = str(conn.execute(
            sa.text(
                "INSERT INTO tenants (slug, display_name, status)"
                " VALUES (:slug, 'P17 Foreign', 'active') RETURNING id"
            ),
            {"slug": f"p17-foreign-{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
        foreign_role = str(conn.execute(
            sa.text(
                "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                " VALUES (:t, NULL, :k, 'Foreign Tenant Role', 'TENANT', 'active') RETURNING id"
            ),
            {"t": foreign_tenant, "k": f"p17_foreign_{uuid.uuid4().hex[:8]}"},
        ).scalar_one())
    with pytest.raises(IdentityRuntimeError) as exc:
        with runtime.begin() as conn:
            session = Session(bind=conn)
            MembershipRuntime().create_tenant_membership(
                session, actor_id=ids["actor"], actor_type="USER", tenant_id=ids["tenant"],
                user_id=ids["actor"], role_id=foreign_role, correlation_id=str(uuid.uuid4()),
            )
    assert exc.value.code == ErrorCode.ROLE_SCOPE_MISMATCH
    assert _rows(
        engine,
        "SELECT * FROM tenant_memberships WHERE user_id = CAST(:u AS uuid)",
        u=ids["actor"],
    ) == []
