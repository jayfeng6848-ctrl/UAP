"""B1-2 Tenant / Space Foundation — schema, isolation, delete tests.

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).

Covers
  * Schema acceptance: tenants / spaces / tenant_memberships / memberships
  * D-01: role_id stored but NO roles FK (Forward Dependency, B1-3)
  * D-02: role scope full enforcement is NOT implemented in B1-2 (B1-3 responsibility)
  * D-03: spaces.owner_id → users ON DELETE SET NULL (space survives owner deletion)
  * D-04: RLS not enabled (OPEN DESIGN QUESTION)
  * Isolation: cross-tenant membership denied by tg_membership_tenant_consistency
  * Delete: tenant RESTRICT / user CASCADE / owner SET NULL / space CASCADE
"""

from __future__ import annotations

import re

import uuid as _uuid

import pytest
import sqlalchemy as sa

from tests.integration.alembic_testkit import (
    BASE_DSN,
    current_revision,
    database_reachable,
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

EXPECTED_TABLES = {
    "alembic_version",
    "users", "identities", "credentials", "devices", "sessions",
    "tenants", "spaces", "tenant_memberships", "memberships",
    # B1-3 delivered roles/permissions/role_permissions/platform_memberships
    "roles", "permissions", "role_permissions", "platform_memberships",
    # B1-3 hardening: platform bootstrap state singleton
    "platform_state",
    # B1-4 delivered resources / acl_subject_types / resource_permissions
    "resources", "acl_subject_types", "resource_permissions",
    # B1-5 (P07) delivered tools / tool_versions / tool_permissions
    "tools", "tool_versions", "tool_permissions",
    # B1-6 (P08) delivered the AI gateway tables (ai_request_logs 为分区父表；
    # 其当月子分区 ai_request_logs_<YYYYMM> 由 _expected_tables() 动态并入)
    "ai_providers", "ai_models", "ai_routes", "ai_policies", "ai_request_logs",
    # P09 (0011) delivered the agent / tool-permission tables
    "agents", "agent_versions", "agent_permissions", "tool_executions",
    # P10 (0013) delivered the event / audit carriers (both partition parents)
    "events", "audit_logs",
}
AI_PARTITION_PREFIX = "ai_request_logs_"
PARTITION_PREFIXES = ("ai_request_logs_", "events_", "audit_logs_")


def _actual_tables() -> set[str]:
    return {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}


def _expected_tables() -> set[str]:
    """EXPECTED_TABLES + 实际存在的当月子分区（分区名含 UTC 月份 ⇒ 动态并入）。"""
    return EXPECTED_TABLES | {t for t in _actual_tables()
                              if t.startswith(PARTITION_PREFIXES)}
FORBIDDEN = {
    "resource_relations",
    # P09 tables were delivered by 0011; P10 delivered events/audit_logs
    "groups",
}


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0015_p12_indexes"
    yield
    reset_test_database()


def _engine():
    return sa.create_engine(BASE_DSN)


def _rows(sql: str, **params):
    engine = _engine()
    try:
        with engine.connect() as conn:
            return conn.execute(sa.text(sql), params).fetchall()
    finally:
        engine.dispose()


def _scalar(sql: str, **params):
    engine = _engine()
    try:
        with engine.connect() as conn:
            return conn.execute(sa.text(sql), params).scalar()
    finally:
        engine.dispose()


def _rule(constraint: str):
    return _scalar(
        "SELECT rc.delete_rule FROM information_schema.referential_constraints rc "
        "WHERE rc.constraint_name = :c",
        c=constraint,
    )


# ======================================================== exact table set
def test_exact_table_count_and_no_forbidden_tables(db) -> None:
    tables = _actual_tables()
    expected = _expected_tables()
    assert tables == expected, f"unexpected: {tables - expected} / missing: {expected - tables}"
    assert tables.isdisjoint(FORBIDDEN)
    # P08 分区表：恰好一个当月子分区，命名符合 ai_request_logs_<YYYYMM>（DC-1 = A FROZEN）
    partitions = {t for t in tables if t.startswith(PARTITION_PREFIXES)}
    assert len(partitions) == 3, sorted(partitions)
    for prefix in PARTITION_PREFIXES:
        kids = {t for t in partitions if t.startswith(prefix)}
        assert len(kids) == 1, sorted(kids)
        assert re.fullmatch(re.escape(prefix) + r"\d{6}", next(iter(kids)))


# ================================================================= tenants
def test_tenants_schema(db) -> None:
    # PK uuid with UUIDv7 fallback default
    pk = _rows(
        "SELECT a.attname, t.typname FROM pg_index i "
        "JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum = ANY(i.indkey) "
        "JOIN pg_class c ON c.oid=i.indrelid JOIN pg_type t ON t.oid=a.atttypid "
        "WHERE i.indisprimary AND c.relname='tenants'"
    )[0]
    assert (pk[0], pk[1]) == ("id", "uuid")
    assert _scalar(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_name='tenants' AND column_name='id'"
    ) == "uap_uuid_v7()"
    # NOT NULL set
    for col in ("slug", "display_name", "status", "settings", "created_at", "updated_at"):
        assert _scalar(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name='tenants' AND column_name=:c", c=col
        ) == "NO", col
    for col in ("plan", "region", "archived_at", "deleted_at"):
        assert _scalar(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name='tenants' AND column_name=:c", c=col
        ) == "YES", col
    cks = {r[0] for r in _rows("SELECT conname FROM pg_constraint WHERE conrelid='tenants'::regclass AND contype='c'")}
    assert {"ck_tenants_status", "ck_tenants_slug"} <= cks
    assert "uq_tenants_slug" in {r[0] for r in _rows("SELECT indexname FROM pg_indexes WHERE tablename='tenants'")}


def test_tenants_slug_case_insensitive_unique_and_format(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("INSERT INTO tenants (slug, display_name, status) VALUES ('acme', 'Acme', 'active')"))
            conn.commit()
            # duplicate slug rejected (lower() expression unique index)
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("INSERT INTO tenants (slug, display_name, status) VALUES ('acme', 'Acme 2', 'active')"))
                conn.commit()
            conn.rollback()
            # uppercase slug rejected by the format CHECK (slug must be lowercase)
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("INSERT INTO tenants (slug, display_name, status) VALUES ('ACME', 'Acme 3', 'active')"))
                conn.commit()
            conn.rollback()
            # invalid slug format rejected
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("INSERT INTO tenants (slug, display_name, status) VALUES ('bad_slug!', 'X', 'active')"))
                conn.commit()
            conn.rollback()
            # invalid status rejected
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("INSERT INTO tenants (slug, display_name, status) VALUES ('other', 'X', 'flying')"))
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


# ================================================================== spaces
def test_spaces_schema_and_fk(db) -> None:
    assert _scalar(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name='spaces' AND column_name='tenant_id'"
    ) == "NO"
    assert _rule("fk_spaces_tenant") == "RESTRICT"
    assert _rule("fk_spaces_owner") == "SET NULL"
    cks = {r[0] for r in _rows("SELECT conname FROM pg_constraint WHERE conrelid='spaces'::regclass AND contype='c'")}
    assert {"ck_spaces_status", "ck_spaces_kind", "ck_spaces_visibility"} <= cks


def test_space_kind_is_runtime_data_not_domain_enum(db) -> None:
    """kind only enforces format; business values live in the Domain layer."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('kind-tenant', 'K', 'active') RETURNING id"
            )).scalar()
            # a hypothetical domain value must NOT be rejected by the Core schema
            conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's1', 'S1', 'family', 'private', 'active')"
            ), {"t": tid})
            conn.commit()
            # but a malformed kind is rejected by the format CHECK
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                    "VALUES (:t, 's2', 'S2', 'Family!', 'private', 'active')"
                ), {"t": tid})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_space_key_unique_per_tenant(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            t1 = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('t1', 'T1', 'active') RETURNING id"
            )).scalar()
            t2 = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('t2', 'T2', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 'general', 'G', 'work', 'private', 'active')"
            ), {"t": t1})
            conn.commit()
            # same key in another tenant is allowed
            conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 'general', 'G', 'work', 'private', 'active')"
            ), {"t": t2})
            conn.commit()
            # duplicate key within the same tenant rejected (case-insensitive)
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                    "VALUES (:t, 'GENERAL', 'G2', 'work', 'private', 'active')"
                ), {"t": t1})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


# =================================================== tenant_memberships
def test_tenant_membership_basics(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('mem-tenant', 'M', 'active') RETURNING id"
            )).scalar()
            rid = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, tenant_id, status) "
                "VALUES ('tmem', 'Tenant Member', 'TENANT', :t, 'active') RETURNING id"
            ), {"t": tid}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('tm@example.com', 'tm', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                "VALUES (:t, :u, :r, 'active')"
            ), {"t": tid, "u": uid, "r": rid})
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                    "VALUES (:t, :u, :r, 'invited')"
                ), {"t": tid, "u": uid, "r": rid})
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                    "VALUES (:t, :u, :r, 'active')"
                ), {"t": tid, "u": _uuid.uuid4(), "r": rid})
                conn.commit()
            conn.rollback()
            # invalid tenant: BEFORE scope trigger (role tenant != NEW.tenant_id) fires first
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                    "VALUES (:t, :u, :r, 'active')"
                ), {"t": _uuid.uuid4(), "u": uid, "r": rid})
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                    "VALUES (:t, :u, :r, 'flying')"
                ), {"t": tid, "u": uid, "r": rid})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()



# ========================================================= memberships
def test_membership_basics_and_tenant_consistency(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            t1 = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('a1', 'A1', 'active') RETURNING id"
            )).scalar()
            t2 = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('b1', 'B1', 'active') RETURNING id"
            )).scalar()
            s1 = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's', 'S', 'work', 'private', 'active') RETURNING id"
            ), {"t": t1}).scalar()
            sr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, space_id, status) "
                "VALUES ('smem', 'Space Member', 'SPACE', :s, 'active') RETURNING id"
            ), {"s": s1}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('mb@example.com', 'mb', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                "VALUES (:t, :s, :u, :r, 'active')"
            ), {"t": t1, "s": s1, "u": uid, "r": sr})
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                    "VALUES (:t, :s, :u, :r, 'invited')"
                ), {"t": t1, "s": s1, "u": uid, "r": sr})
                conn.commit()
            conn.rollback()
            with pytest.raises((sa.exc.IntegrityError, sa.exc.ProgrammingError)):
                conn.execute(sa.text(
                    "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                    "VALUES (:t, :s, :u, :r, 'active')"
                ), {"t": t2, "s": s1, "u": uid, "r": sr})
                conn.commit()
            conn.rollback()
            conn.execute(sa.text(
                "UPDATE memberships SET removed_at = now(), status='removed' WHERE space_id=:s AND user_id=:u"
            ), {"s": s1, "u": uid})
            conn.commit()
            conn.execute(sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                "VALUES (:t, :s, :u, :r, 'active')"
            ), {"t": t1, "s": s1, "u": uid, "r": sr})
            conn.commit()
    finally:
        engine.dispose()

def test_no_implicit_user_to_space_relation(db) -> None:
    """User→Space must go through memberships; no implicit grant exists."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('iso', 'Iso', 'active') RETURNING id"
            )).scalar()
            sid = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 'room', 'Room', 'work', 'private', 'active') RETURNING id"
            ), {"t": tid}).scalar()
            tr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, tenant_id, status) "
                "VALUES ('tiso', 'Iso', 'TENANT', :t, 'active') RETURNING id"
            ), {"t": tid}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('iso@example.com', 'iso', 'active') RETURNING id"
            )).scalar()
            conn.commit()
            assert _scalar(
                "SELECT count(*) FROM memberships WHERE space_id=:s AND user_id=:u", s=sid, u=uid
            ) == 0
            conn.execute(sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                "VALUES (:t, :u, :r, 'active')"
            ), {"t": tid, "u": uid, "r": tr})
            conn.commit()
            assert _scalar(
                "SELECT count(*) FROM memberships WHERE space_id=:s AND user_id=:u", s=sid, u=uid
            ) == 0
    finally:
        engine.dispose()



# ============================================================ D-01 / D-02
def test_b13_role_id_fk_restrict_and_not_null(db) -> None:
    """B1-3 delivered the role FK (D-08): role_id is NOT NULL + FK RESTRICT now."""
    assert "roles" in {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    rules = {r[0]: r[1] for r in _rows(
        "SELECT conname, confdeltype FROM pg_constraint "
        "WHERE contype='f' AND conrelid = ANY(ARRAY['tenant_memberships','memberships']::regclass[])"
    )}
    # confdeltype: 'r' = RESTRICT
    assert rules.get("fk_tm_role") == "r"
    assert rules.get("fk_membership_role") == "r"
    for tbl in ("tenant_memberships", "memberships"):
        assert _scalar(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name=:t AND column_name='role_id'", t=tbl
        ) == "NO"
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('r1', 'R1', 'active') RETURNING id"
            )).scalar()
            rid = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, tenant_id, status) "
                "VALUES ('r1m', 'R1M', 'TENANT', :t, 'active') RETURNING id"
            ), {"t": tid}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('r1@example.com', 'r1', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                "VALUES (:t, :u, :r, 'active')"
            ), {"t": tid, "u": uid, "r": rid})
            conn.commit()
            # an arbitrary role_id is denied by the BEFORE scope trigger (fail-closed),
            # and by the FK once the trigger passes
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                    "VALUES (:t, :u, :r, 'active')"
                ), {"t": tid, "u": uid, "r": _uuid.uuid4()})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()

def test_b13_membership_role_scope_enforcement_present(db) -> None:
    """B1-3 added the membership↔role scope triggers (D-11/D-02 close-out)."""
    scope_triggers = {r[0] for r in _rows(
        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid = ANY(ARRAY['tenant_memberships','memberships']::regclass[])"
    )}
    assert {"tg_tm_role_scope", "tg_membership_role_scope"} <= scope_triggers
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('r2', 'R2', 'active') RETURNING id"
            )).scalar()
            sid = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's', 'S', 'work', 'private', 'active') RETURNING id"
            ), {"t": tid}).scalar()
            tr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, tenant_id, status) "
                "VALUES ('r2t', 'T', 'TENANT', :t, 'active') RETURNING id"
            ), {"t": tid}).scalar()
            sr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, space_id, status) "
                "VALUES ('r2s', 'S', 'SPACE', :s, 'active') RETURNING id"
            ), {"s": sid}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('r2@example.com', 'r2', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                "VALUES (:t, :u, :r, 'active')"
            ), {"t": tid, "u": uid, "r": tr})
            conn.execute(sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                "VALUES (:t, :s, :u, :r, 'active')"
            ), {"t": tid, "s": sid, "u": uid, "r": sr})
            conn.commit()
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                    "VALUES (:t, :u, :r, 'active')"
                ), {"t": tid, "u": uid, "r": sr})
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                    "VALUES (:t, :s, :u, :r, 'active')"
                ), {"t": tid, "s": sid, "u": uid, "r": tr})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()



# ============================================================ D-03 / D-04
def test_d03_owner_deletion_keeps_space_and_nulls_owner(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('own', 'Own', 'active') RETURNING id"
            )).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('own@example.com', 'own', 'active') RETURNING id"
            )).scalar()
            sid = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status, owner_id) "
                "VALUES (:t, 'o', 'O', 'work', 'private', 'active', :u) RETURNING id"
            ), {"t": tid, "u": uid}).scalar()
            conn.commit()
            conn.execute(sa.text("DELETE FROM users WHERE id=:id"), {"id": uid})
            conn.commit()
            row = conn.execute(
                sa.text("SELECT owner_id FROM spaces WHERE id=:id"), {"id": sid}
            ).one()
            assert row[0] is None
            assert _scalar("SELECT count(*) FROM spaces WHERE id=:id", id=sid) == 1
    finally:
        engine.dispose()


def test_d04_rls_not_enabled(db) -> None:
    policies = _scalar("SELECT count(*) FROM pg_policies")
    assert policies == 0
    rls_tables = _rows(
        "SELECT relname FROM pg_class WHERE relrowsecurity OR relforcerowsecurity"
    )
    assert rls_tables == []


# =========================================================== delete policy
def test_delete_tenant_with_space_is_restricted(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('del', 'Del', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's', 'S', 'work', 'private', 'active')"
            ), {"t": tid})
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("DELETE FROM tenants WHERE id=:id"), {"id": tid})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_delete_user_cascades_membership_rows(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('cas', 'Cas', 'active') RETURNING id"
            )).scalar()
            sid = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's', 'S', 'work', 'private', 'active') RETURNING id"
            ), {"t": tid}).scalar()
            tr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, tenant_id, status) "
                "VALUES ('casm', 'CasM', 'TENANT', :t, 'active') RETURNING id"
            ), {"t": tid}).scalar()
            sr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, space_id, status) "
                "VALUES ('cass', 'CasS', 'SPACE', :s, 'active') RETURNING id"
            ), {"s": sid}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('cas@example.com', 'cas', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO tenant_memberships (tenant_id, user_id, role_id, status) "
                "VALUES (:t, :u, :r, 'active')"
            ), {"t": tid, "u": uid, "r": tr})
            conn.execute(sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                "VALUES (:t, :s, :u, :r, 'active')"
            ), {"t": tid, "s": sid, "u": uid, "r": sr})
            conn.commit()
            conn.execute(sa.text("DELETE FROM users WHERE id=:id"), {"id": uid})
            conn.commit()
            assert _scalar("SELECT count(*) FROM tenant_memberships WHERE user_id=:u", u=uid) == 0
            assert _scalar("SELECT count(*) FROM memberships WHERE user_id=:u", u=uid) == 0
    finally:
        engine.dispose()

def test_delete_space_cascades_memberships(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('sp', 'Sp', 'active') RETURNING id"
            )).scalar()
            sid = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's', 'S', 'work', 'private', 'active') RETURNING id"
            ), {"t": tid}).scalar()
            sr = conn.execute(sa.text(
                "INSERT INTO roles (key, name, scope, space_id, status) "
                "VALUES ('spm', 'SpM', 'SPACE', :s, 'active') RETURNING id"
            ), {"s": sid}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('sp@example.com', 'sp', 'active') RETURNING id"
            )).scalar()
            conn.execute(sa.text(
                "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status) "
                "VALUES (:t, :s, :u, :r, 'active')"
            ), {"t": tid, "s": sid, "u": uid, "r": sr})
            conn.commit()
            conn.execute(sa.text("DELETE FROM spaces WHERE id=:id"), {"id": sid})
            conn.commit()
            assert _scalar("SELECT count(*) FROM memberships WHERE space_id=:s", s=sid) == 0
    finally:
        engine.dispose()



# ================================================================ triggers
def test_updated_at_triggers_for_b1_2_tables(db) -> None:
    names = {r[0] for r in _rows(
        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid = ANY(ARRAY['tenants','spaces','tenant_memberships','memberships']::regclass[])"
    )}
    expected = {f"tg_{t}_set_updated_at" for t in ("tenants", "spaces", "tenant_memberships", "memberships")}
    assert expected <= names
    assert "tg_membership_tenant_consistency" in names
    # set_updated_at() is reused from B1-1 (not duplicated)
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1


def test_consistency_trigger_does_not_write_side_effects(db) -> None:
    """The trigger only validates; it must not auto-authorize or replicate."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            t1 = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('sa', 'SA', 'active') RETURNING id"
            )).scalar()
            t2 = conn.execute(sa.text(
                "INSERT INTO tenants (slug, display_name, status) VALUES ('sb', 'SB', 'active') RETURNING id"
            )).scalar()
            s1 = conn.execute(sa.text(
                "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, 's', 'S', 'work', 'private', 'active') RETURNING id"
            ), {"t": t1}).scalar()
            uid = conn.execute(sa.text(
                "INSERT INTO users (email, username, status) VALUES ('se@example.com', 'se', 'active') RETURNING id"
            )).scalar()
            conn.commit()
            before_tm = _scalar("SELECT count(*) FROM tenant_memberships")
            before_sp = _scalar("SELECT count(*) FROM spaces WHERE tenant_id=:t", t=t2)
            with pytest.raises((sa.exc.IntegrityError, sa.exc.ProgrammingError)):
                conn.execute(sa.text(
                    "INSERT INTO memberships (tenant_id, space_id, user_id, status) VALUES (:t, :s, :u, 'active')"
                ), {"t": t2, "s": s1, "u": uid})
                conn.commit()
            conn.rollback()
            # no side effects: no auto tenant membership, no space replication
            assert _scalar("SELECT count(*) FROM tenant_memberships") == before_tm
            assert _scalar("SELECT count(*) FROM spaces WHERE tenant_id=:t", t=t2) == before_sp
    finally:
        engine.dispose()
