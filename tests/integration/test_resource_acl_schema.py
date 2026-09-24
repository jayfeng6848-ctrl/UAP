"""B1-4 Resource / ACL — schema, isolation, protection tests.

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).

Covers the frozen B1-4 decisions:
  * D-B14-08 = A  action is an opaque identifier: NOT NULL + UQ only, zero new
                  semantic/format contract (no regex / enum / whitelist / vocabulary)
  * D-B14-09 = A  granted_by → users.id ON DELETE SET NULL (actor attribution,
                  NOT ownership; independent from resources.owner_id)
  * D-B14-10 = A-1 tg_resources_tenant_space_consistency (structural integrity only)
  * D-B14-12 = A  platform-controlled registry + tg_acl_subject_types_protect
                  (registry governance only; whitelist user/role/agent, no group)
  * D-B14-01 / D-B14-02  zero seed; G/H/I/J stay P09-after (not implemented here)

Out of scope (must NOT exist): RLS, Authorization evaluation, G/H/I/J,
permissions/groups/audit_logs/agents/tools/AI/events/Domain tables.
"""

from __future__ import annotations

import uuid as _uuid

import pytest
import sqlalchemy as sa

from tests.integration.alembic_testkit import (
    BASE_DSN,
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

B14_TABLES = {"resources", "acl_subject_types", "resource_permissions"}
B14_TRIGGERS = {
    "tg_resources_set_updated_at",
    "tg_resources_tenant_space_consistency",
    "tg_acl_subject_types_protect",
}
B14_FUNCTIONS = {
    "enforce_resources_tenant_space_consistency",
    "enforce_acl_subject_types_protect",
}
B14_INDEXES = {
    "uq_resources_natural",
    "ix_res_tenant_space_type_status",
    "ix_res_tenant_owner",
    "ix_res_tenant_type_created",
    "ix_res_tenant_deleted",
    "uq_acl_subject_types_key",
    "uq_resource_perm",
    "ix_rp_subject",
}
B14_CHECK_CONSTRAINTS = {
    # resources (3)
    "ck_resources_type",
    "ck_resources_classification",
    "ck_resources_status",
    # acl_subject_types (2)
    "ck_acl_subject_types_key",
    "ck_acl_subject_types_whitelist",
    # resource_permissions (1) — plus the SC-1b canonical-action CK added by the
    # STAGE 2 authorization change set (see the note on the CK assertion below).
    "ck_resource_permissions_effect",
    "ck_resource_permissions_action_canonical",
}
B14_FK_DELETE_RULES = {
    "fk_resources_tenant": "r",              # RESTRICT
    "fk_resources_space": "r",               # RESTRICT
    "fk_resources_owner": "n",               # SET NULL
    "fk_resource_permissions_resource": "c",  # CASCADE
    "fk_resource_permissions_subject_type": "r",  # RESTRICT
    "fk_resource_permissions_granted_by": "n",    # SET NULL
}
# Never implemented in B1-4 (earliest phase = P09 after)
P09_ACL_TRIGGERS = {
    "tg_acl_subject_exists",
    "tg_acl_user_hard_delete",
    "tg_acl_role_delete_block",
    "tg_agent_acl_expire",
}
FORBIDDEN_TABLES = {
    "resource_relations",
    # P09 tables were delivered by 0011 (no longer forbidden)
    "events", "audit_logs", "groups",
}


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #
@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == "0012_authz_enforcement"
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


def _fresh_tenant(conn, slug: str = "b14") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tenants (slug, display_name, status) "
            "VALUES (:s, :s, 'active') RETURNING id"
        ),
        {"s": slug},
    ).scalar()


def _fresh_space(conn, tenant_id, key: str = "sp") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
            "VALUES (:t, :k, :k, 'room', 'private', 'active') RETURNING id"
        ),
        {"t": tenant_id, "k": key},
    ).scalar()


def _fresh_user(conn, email: str = "b14@example.com") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO users (email, username, status) "
            "VALUES (:e, :u, 'active') RETURNING id"
        ),
        {"e": email, "u": email.split("@")[0]},
    ).scalar()


def _registry_fixture(conn, key: str = "user"):
    """Controlled registry write path (docs/architecture/B1-4_DESIGN.md §8.1, M-1).

    The registry is migration-controlled; a fixture row is created by
    temporarily disabling the protect trigger, then re-enabling it.
    """
    conn.execute(sa.text(
        "ALTER TABLE acl_subject_types DISABLE TRIGGER tg_acl_subject_types_protect"
    ))
    try:
        row = conn.execute(
            sa.text(
                "INSERT INTO acl_subject_types (key, description) "
                "VALUES (:k, 'fixture') RETURNING id"
            ),
            {"k": key},
        ).scalar()
    finally:
        conn.execute(sa.text(
            "ALTER TABLE acl_subject_types ENABLE TRIGGER tg_acl_subject_types_protect"
        ))
    return row


# =========================================================== S1/S2 / M1-M4
AI_PARTITION_PREFIX = "ai_request_logs_"


def test_exact_table_set_and_no_forbidden_tables(db) -> None:
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    expected = {
        "alembic_version",
        "users", "identities", "credentials", "devices", "sessions",
        "tenants", "spaces", "tenant_memberships", "memberships",
        "roles", "permissions", "role_permissions", "platform_memberships",
        "platform_state",
        # B1-5 (P07) delivered tool tables — no longer "forbidden"
        "tools", "tool_versions", "tool_permissions",
        # B1-6 (P08) delivered the AI gateway tables；其当月子分区
        # ai_request_logs_<YYYYMM> 动态并入（分区名含 UTC 月份）
        "ai_providers", "ai_models", "ai_routes", "ai_policies", "ai_request_logs",
        # P09 (0011) delivered the agent / tool-permission tables
        "agents", "agent_versions", "agent_permissions", "tool_executions",
    } | B14_TABLES
    partitions = {t for t in tables if t.startswith(AI_PARTITION_PREFIX)}
    expected |= partitions
    assert tables == expected, (
        f"unexpected: {tables - expected} / missing: {expected - tables}"
    )
    assert len(partitions) == 1, sorted(partitions)
    assert tables.isdisjoint(FORBIDDEN_TABLES)


def test_migration_roundtrip_0006_to_0007(db) -> None:
    # 0007 -> 0006 removes every B1-4 object and keeps B1-3 intact
    cfg = make_config(lock_mode="fail")
    downgrade(cfg, "0006_b1_3_bootstrap_state")
    assert current_revision() == "0006_b1_3_bootstrap_state"
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert tables.isdisjoint(B14_TABLES), "downgrade left B1-4 tables behind"
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(B14_TRIGGERS)) == 0
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)", n=list(B14_FUNCTIONS)) == 0
    assert _scalar("SELECT count(*) FROM pg_indexes WHERE indexname = ANY(:n)", n=list(B14_INDEXES)) == 0
    # set_updated_at / uap_uuid_v7 survive the downgrade
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='uap_uuid_v7'") == 1
    # re-upgrade restores the exact same object set
    upgrade(cfg, "head")
    assert current_revision() == "0012_authz_enforcement"
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert B14_TABLES <= tables


# ================================================================= S3 / S6
def test_resources_schema(db) -> None:
    cols = {r[0]: r[1] for r in _rows(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name='resources'"
    )}
    assert len(cols) == 14, cols
    for c in ("tenant_id", "resource_type", "classification", "status",
              "metadata", "created_at", "updated_at"):
        assert cols[c] == "NO", c
    for c in ("space_id", "owner_id", "natural_key", "label",
              "archived_at", "deleted_at"):
        assert cols[c] == "YES", c
    # FK delete rules (D-B14-09 / P2-03)
    rules = {r[0]: r[1] for r in _rows(
        "SELECT conname, confdeltype FROM pg_constraint "
        "WHERE contype='f' AND conrelid='resources'::regclass"
    )}
    assert rules == {
        "fk_resources_tenant": "r",
        "fk_resources_space": "r",
        "fk_resources_owner": "n",
    }
    cks = {r[0] for r in _rows(
        "SELECT conname FROM pg_constraint WHERE contype='c' AND conrelid='resources'::regclass"
    )}
    assert cks == {"ck_resources_type", "ck_resources_classification", "ck_resources_status"}
    assert _scalar(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_name='resources' AND column_name='id'"
    ) == "uap_uuid_v7()"


def test_resources_indexes_and_partial_uniqueness(db) -> None:
    names = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE tablename='resources'"
    )}
    assert {
        "uq_resources_natural",
        "ix_res_tenant_space_type_status",
        "ix_res_tenant_owner",
        "ix_res_tenant_type_created",
        "ix_res_tenant_deleted",
    } <= names
    # the natural-key unique index is partial
    ddl = _scalar(
        "SELECT indexdef FROM pg_indexes WHERE indexname='uq_resources_natural'"
    )
    assert "WHERE" in ddl and "natural_key IS NOT NULL" in ddl and "deleted_at IS NULL" in ddl

    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "nat")
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, resource_type, natural_key) "
                "VALUES (:t, 'doc', 'k1')"
            ), {"t": tid})
            # NULL natural_key rows may repeat (partial index does not apply)
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, resource_type) VALUES (:t, 'doc')"
            ), {"t": tid})
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, resource_type) VALUES (:t, 'doc')"
            ), {"t": tid})
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO resources (tenant_id, resource_type, natural_key) "
                    "VALUES (:t, 'doc', 'k1')"
                ), {"t": tid})
                conn.commit()
            conn.rollback()
            # soft delete releases the natural key
            conn.execute(sa.text(
                "UPDATE resources SET deleted_at = now(), status='deleted' "
                "WHERE natural_key='k1'"
            ))
            conn.commit()
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, resource_type, natural_key) "
                "VALUES (:t, 'doc', 'k1')"
            ), {"t": tid})
            conn.commit()
    finally:
        engine.dispose()


# ================================================================= S4 / S5
def test_acl_subject_types_schema(db) -> None:
    cols = {r[0]: r[1] for r in _rows(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name='acl_subject_types'"
    )}
    assert set(cols) == {"id", "key", "description", "created_at", "archived_at"}
    assert cols["key"] == "NO" and cols["description"] == "YES"
    cks = {r[0] for r in _rows(
        "SELECT conname FROM pg_constraint WHERE contype='c' AND conrelid='acl_subject_types'::regclass"
    )}
    assert cks == {"ck_acl_subject_types_key", "ck_acl_subject_types_whitelist"}
    # no updated_at column and no set_updated_at trigger on this table
    assert _scalar(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_name='acl_subject_types' AND column_name='updated_at'"
    ) == 0
    assert _scalar(
        "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid='acl_subject_types'::regclass AND tgname LIKE '%set_updated_at'"
    ) == 0
    ddl = _scalar("SELECT indexdef FROM pg_indexes WHERE indexname='uq_acl_subject_types_key'")
    assert "lower(key)" in ddl and "archived_at IS NULL" in ddl


def test_resource_permissions_schema_and_action_is_opaque(db) -> None:
    cols = {r[0]: r[1] for r in _rows(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_name='resource_permissions'"
    )}
    assert len(cols) == 11, cols
    for c in ("resource_id", "subject_type_id", "subject_id", "action",
              "effect", "inherited", "created_at"):
        assert cols[c] == "NO", c
    for c in ("conditions", "expires_at", "granted_by"):
        assert cols[c] == "YES", c
    rules = {r[0]: r[1] for r in _rows(
        "SELECT conname, confdeltype FROM pg_constraint "
        "WHERE contype='f' AND conrelid='resource_permissions'::regclass"
    )}
    assert rules == {
        "fk_resource_permissions_resource": "c",
        "fk_resource_permissions_subject_type": "r",
        "fk_resource_permissions_granted_by": "n",
    }
    # ``D-B14-08 = A`` originally froze "action has NO format/vocabulary CK" for
    # this table. That is no longer the platform state: ``SC-1b`` of the STAGE 2
    # authorization change set adds ``ck_resource_permissions_action_canonical``
    # to enforce the canonical action vocabulary (``D-AUTH-05``), which
    # supersedes that clause. The effect CK is unchanged.
    cks = {r[0] for r in _rows(
        "SELECT conname FROM pg_constraint "
        "WHERE contype='c' AND conrelid='resource_permissions'::regclass"
    )}
    assert cks == {
        "ck_resource_permissions_effect",
        "ck_resource_permissions_action_canonical",
    }
    # the unique key is exactly the frozen 4-tuple
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE conname='uq_resource_perm' "
        "AND contype='u' AND conrelid='resource_permissions'::regclass"
    ) == 1
    assert _scalar(
        "SELECT string_agg(a.attname, ',' ORDER BY a.attname) "
        "FROM pg_constraint c JOIN pg_attribute a "
        "  ON a.attrelid=c.conrelid AND a.attnum = ANY(c.conkey) "
        "WHERE c.conname='uq_resource_perm'"
    ) == "action,resource_id,subject_id,subject_type_id"


# ==================================================== S11 / functions (D)
def test_trigger_set_is_exactly_three(db) -> None:
    names = {r[0] for r in _rows(
        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid::regclass::text = ANY(:t)", t=list(B14_TABLES)
    )}
    assert names == B14_TRIGGERS, names
    assert not (names & P09_ACL_TRIGGERS)


def test_trigger_timings_match_frozen_decisions(db) -> None:
    tgtype = {r[0]: r[1] for r in _rows(
        "SELECT tgname, tgtype FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid::regclass::text = ANY(:t)", t=list(B14_TABLES)
    )}
    # tgtype bits: ROW=1, BEFORE=2, INSERT=4, DELETE=8, UPDATE=16
    assert tgtype["tg_resources_set_updated_at"] == 1 + 2 + 16          # BEFORE UPDATE
    assert tgtype["tg_resources_tenant_space_consistency"] == 1 + 2 + 4 + 16  # BEFORE I/U
    assert tgtype["tg_acl_subject_types_protect"] == 1 + 2 + 4 + 8 + 16  # BEFORE I/U/D


def test_functions_and_reuse(db) -> None:
    names = {r[0] for r in _rows(
        "SELECT proname FROM pg_proc WHERE proname = ANY(:n)", n=list(B14_FUNCTIONS)
    )}
    assert names == B14_FUNCTIONS
    # set_updated_at() is reused from B1-1, never re-declared
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE tgname LIKE '%_set_updated_at'") >= 1


# ===================================================== S9/S10 / zero seed
def test_zero_seed_and_unwritable_acl(db) -> None:
    assert _scalar("SELECT count(*) FROM acl_subject_types") == 0
    assert _scalar("SELECT count(*) FROM resource_permissions") == 0
    assert _scalar("SELECT count(*) FROM resources") == 0
    # A0-1: with an empty registry the FK is unsatisfiable -> ACL rows are not writable
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "seedless")
            rid = conn.execute(sa.text(
                "INSERT INTO resources (id, tenant_id, resource_type) "
                "VALUES (:i, :t, 'doc') RETURNING id"
            ), {"i": str(_uuid.uuid4()), "t": tid}).scalar()
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO resource_permissions "
                    "(resource_id, subject_type_id, subject_id, action, effect) "
                    "VALUES (:r, :st, :su, 'read', 'allow')"
                ), {"r": rid, "st": str(_uuid.uuid4()), "su": str(_uuid.uuid4())})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_migration_source_has_no_seed_statement(db) -> None:
    import pathlib
    src = pathlib.Path("migrations_alembic/versions/0007_b1_4_resource_acl.py").read_text(encoding="utf-8")
    assert "INSERT INTO acl_subject_types" not in src
    assert "INSERT INTO resource_permissions" not in src
    assert "INSERT INTO resources" not in src


# ============================================================ F1 / F2 / F7
def test_parent_delete_with_resources_is_restricted(db) -> None:
    """F1 / F2 — P2-03: a tenant/space holding resources can never be deleted."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "restrict")
            sid = _fresh_space(conn, tid, "r")
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, space_id, resource_type) "
                "VALUES (:t, :s, 'doc')"
            ), {"t": tid, "s": sid})
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("DELETE FROM spaces WHERE id=:s"), {"s": sid})
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("DELETE FROM tenants WHERE id=:t"), {"t": tid})
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM resources") == 1
    finally:
        engine.dispose()


def test_migration_cascade_whitelist(db) -> None:
    """F7 — the only approved CASCADE out of B1-4 is resource_permissions.resource_id."""
    name = "fk_resource_permissions_resource"
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE conname=:n AND confdeltype='c'", n=name
    ) == 1
    others = {r[0] for r in _rows(
        "SELECT conname FROM pg_constraint WHERE contype='f' AND confdeltype='c' "
        "AND conrelid::regclass::text = ANY(:t)", t=list(B14_TABLES)
    )}
    assert others == {name}, others


# ======================================================== D-B14-10 (F2)
def test_d_b14_10_insert_path(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            t_a = _fresh_tenant(conn, "corp-a")
            t_b = _fresh_tenant(conn, "corp-b")
            sp_a = _fresh_space(conn, t_a, "a")
            sp_b = _fresh_space(conn, t_b, "b")
            conn.commit()
            # TC-01 / R-ISOLATION-02: same tenant -> ALLOW
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, space_id, resource_type) "
                "VALUES (:t, :s, 'doc')"
            ), {"t": t_a, "s": sp_a})
            conn.commit()
            # TC-03 / I3: space_id IS NULL -> ALLOW
            conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, space_id, resource_type) "
                "VALUES (:t, NULL, 'doc')"
            ), {"t": t_a})
            conn.commit()
            # TC-02 / R-ISOLATION-01: cross-tenant space -> REJECT
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO resources (tenant_id, space_id, resource_type) "
                    "VALUES (:t, :s, 'doc')"
                ), {"t": t_a, "s": sp_b})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_d_b14_10_update_path(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            t_a = _fresh_tenant(conn, "upd-a")
            t_b = _fresh_tenant(conn, "upd-b")
            sp_a = _fresh_space(conn, t_a, "a")
            sp_b = _fresh_space(conn, t_b, "b")
            rid = conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, space_id, resource_type) "
                "VALUES (:t, :s, 'doc') RETURNING id"
            ), {"t": t_a, "s": sp_a}).scalar()
            conn.commit()
            # TC-04 / R-ISOLATION-03: cross-tenant on UPDATE -> REJECT
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text("UPDATE resources SET space_id=:s WHERE id=:i"),
                             {"s": sp_b, "i": rid})
                conn.commit()
            conn.rollback()
            # R-ISOLATION-05: NOT NULL -> NULL (leave the space) -> ALLOW
            conn.execute(sa.text("UPDATE resources SET space_id=NULL WHERE id=:i"), {"i": rid})
            conn.commit()
            # R-ISOLATION-05: NULL -> NOT NULL same tenant -> ALLOW
            conn.execute(sa.text("UPDATE resources SET space_id=:s WHERE id=:i"),
                         {"s": sp_a, "i": rid})
            conn.commit()
            # R-ISOLATION-04: same-tenant space change -> ALLOW
            sp_a2 = _fresh_space(conn, t_a, "a2")
            conn.execute(sa.text("UPDATE resources SET space_id=:s WHERE id=:i"),
                         {"s": sp_a2, "i": rid})
            conn.commit()
    finally:
        engine.dispose()


def test_d_b14_10_rejects_nonexistent_space(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "ghost")
            conn.commit()
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO resources (tenant_id, space_id, resource_type) "
                    "VALUES (:t, :s, 'doc')"
                ), {"t": tid, "s": str(_uuid.uuid4())})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


# ======================================================== D-B14-09 (GB)
def test_d_b14_09_granted_by_set_null_and_owner_independence(db) -> None:
    """GB-01 (granted_by) and F3 / GB-02 (owner_id) are separate assertions."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "gb14")
            actor = _fresh_user(conn, "actor@example.com")
            owner = _fresh_user(conn, "owner@example.com")
            stype = _registry_fixture(conn, "user")
            rid = conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, owner_id, resource_type) "
                "VALUES (:t, :o, 'doc') RETURNING id"
            ), {"t": tid, "o": owner}).scalar()
            conn.execute(sa.text(
                "INSERT INTO resource_permissions "
                "(resource_id, subject_type_id, subject_id, action, effect, granted_by) "
                "VALUES (:r, :st, :su, 'read', 'allow', :g)"
            ), {"r": rid, "st": stype, "su": actor, "g": actor})
            conn.commit()

            # GB-01: delete the actor -> ACL row survives, granted_by becomes NULL
            conn.execute(sa.text("DELETE FROM users WHERE id=:u"), {"u": actor})
            conn.commit()
            row = conn.execute(sa.text(
                "SELECT granted_by FROM resource_permissions WHERE resource_id=:r"
            ), {"r": rid}).one()
            assert row[0] is None
            assert _scalar(
                "SELECT count(*) FROM resource_permissions WHERE resource_id=:r", r=rid
            ) == 1

            # F3 / GB-02 (independent): delete the owner -> resource survives, owner_id NULL
            conn.execute(sa.text("DELETE FROM users WHERE id=:u"), {"u": owner})
            conn.commit()
            assert _scalar("SELECT count(*) FROM resources WHERE id=:r", r=rid) == 1
            assert _scalar("SELECT owner_id FROM resources WHERE id=:r", r=rid) is None
            # granted_by was already NULL and must not have been re-purposed as ownership
            assert _scalar(
                "SELECT granted_by FROM resource_permissions WHERE resource_id=:r", r=rid
            ) is None
    finally:
        engine.dispose()


# ================================================= D-B14-08 (ACT) / F4
def test_d_b14_08_action_not_null_and_duplicate_rejected(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "act")
            stype = _registry_fixture(conn, "role")
            rid = conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, resource_type) "
                "VALUES (:t, 'doc') RETURNING id"
            ), {"t": tid}).scalar()
            conn.commit()
            sid = str(_uuid.uuid4())
            # ACT-01: action IS NULL -> rejected by NOT NULL
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO resource_permissions "
                    "(resource_id, subject_type_id, subject_id, action, effect) "
                    "VALUES (:r, :st, :su, NULL, 'allow')"
                ), {"r": rid, "st": stype, "su": sid})
                conn.commit()
            conn.rollback()
            # ``D-B14-08`` was SUPERSEDED by ``D-AUTH-05`` (recorded as
            # ``D-AUTH-24``), so this column now holds canonical actions only, in
            # the lowercase form frozen by ``D-AUTH-25``. A canonical action is
            # therefore accepted...
            conn.execute(sa.text(
                "INSERT INTO resource_permissions "
                "(resource_id, subject_type_id, subject_id, action, effect) "
                "VALUES (:r, :st, :su, 'read', 'allow')"
            ), {"r": rid, "st": stype, "su": sid})
            conn.commit()
            # ...and ``SC-1b`` makes a non-canonical action fail closed.
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO resource_permissions "
                    "(resource_id, subject_type_id, subject_id, action, effect) "
                    "VALUES (:r, :st, :su, 'x9.opaque', 'allow')"
                ), {"r": rid, "st": stype, "su": sid})
                conn.commit()
            conn.rollback()
            # ACT-02: duplicate (resource, subject_type, subject_id, action) -> rejected
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO resource_permissions "
                    "(resource_id, subject_type_id, subject_id, action, effect) "
                    "VALUES (:r, :st, :su, 'read', 'deny')"
                ), {"r": rid, "st": stype, "su": sid})
                conn.commit()
            conn.rollback()
            # effect CK still enforced
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text(
                    "INSERT INTO resource_permissions "
                    "(resource_id, subject_type_id, subject_id, action, effect) "
                    "VALUES (:r, :st, :su, 'delete', 'maybe')"
                ), {"r": rid, "st": stype, "su": sid})
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_acl_row_cascades_with_resource_delete(db) -> None:
    """F4: ACL rows are purely technical dependents of the resource."""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tid = _fresh_tenant(conn, "f4")
            stype = _registry_fixture(conn, "agent")
            rid = conn.execute(sa.text(
                "INSERT INTO resources (tenant_id, resource_type) "
                "VALUES (:t, 'doc') RETURNING id"
            ), {"t": tid}).scalar()
            conn.execute(sa.text(
                "INSERT INTO resource_permissions "
                "(resource_id, subject_type_id, subject_id, action, effect) "
                "VALUES (:r, :st, :su, 'read', 'allow')"
            ), {"r": rid, "st": stype, "su": str(_uuid.uuid4())})
            conn.commit()
            conn.execute(sa.text("DELETE FROM resources WHERE id=:r"), {"r": rid})
            conn.commit()
            assert _scalar(
                "SELECT count(*) FROM resource_permissions WHERE resource_id=:r", r=rid
            ) == 0
    finally:
        engine.dispose()


# ====================================================== D-B14-12 (REG/C)
def test_registry_protection(db) -> None:
    engine = _engine()
    try:
        with engine.connect() as conn:
            # REG-01: runtime INSERT denied (zero seed must be preserved)
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "INSERT INTO acl_subject_types (key) VALUES ('user')"
                ))
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM acl_subject_types") == 0

            # fixture row via the migration-controlled path
            stype = _registry_fixture(conn, "user")
            conn.commit()
            # REG-02: key UPDATE denied, description UPDATE allowed
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text(
                    "UPDATE acl_subject_types SET key='admin' WHERE id=:i"
                ), {"i": stype})
                conn.commit()
            conn.rollback()
            conn.execute(sa.text(
                "UPDATE acl_subject_types SET description='renamed' WHERE id=:i"
            ), {"i": stype})
            conn.commit()
            # archival (retire path) stays allowed
            conn.execute(sa.text(
                "UPDATE acl_subject_types SET archived_at=now() WHERE id=:i"
            ), {"i": stype})
            conn.commit()
            # REG-03: DELETE denied
            with pytest.raises(sa.exc.ProgrammingError):
                conn.execute(sa.text("DELETE FROM acl_subject_types WHERE id=:i"), {"i": stype})
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM acl_subject_types WHERE id=:i", i=stype) == 1
    finally:
        engine.dispose()


def test_d_b14_12_trigger_is_the_enforcing_object(db) -> None:
    """Layer 2 evidence: the protect trigger — not the FK / CK / UQ — is the enforcer.

    Layer 1 is the empty registry (FK unsatisfiable). That alone does NOT prove
    the protection mechanism exists. This test isolates the trigger with an
    A/B contrast (DISABLE -> allowed, ENABLE -> rejected) and asserts the
    trigger's own message, so CK/UQ/FK are ruled out:

      * INSERT is rejected by the trigger while the same row is accepted with
        the trigger disabled (so CK + UQ permit it).
      * key UPDATE 'user' -> 'role' is rejected although both keys pass the
        whitelist CK and no uniqueness conflict exists.
      * DELETE is rejected although nothing else forbids it.
    """
    engine = _engine()
    disabled_sql = "ALTER TABLE acl_subject_types DISABLE TRIGGER tg_acl_subject_types_protect"
    enabled_sql = "ALTER TABLE acl_subject_types ENABLE TRIGGER tg_acl_subject_types_protect"
    try:
        with engine.connect() as conn:
            conn.execute(sa.text(enabled_sql))
            conn.commit()

            def attempt(sql, **params):
                try:
                    conn.execute(sa.text(sql), params)
                    conn.commit()
                    return None
                except sa.exc.ProgrammingError as ex:
                    conn.rollback()
                    return str(ex)

            # trigger ENABLED: INSERT denied by the trigger itself
            msg = attempt("INSERT INTO acl_subject_types (key) VALUES ('user')")
            assert msg and "platform-controlled registry" in msg

            # A/B contrast: with the trigger disabled the very same INSERT is legal
            conn.execute(sa.text(disabled_sql))
            conn.commit()
            assert attempt("INSERT INTO acl_subject_types (key) VALUES ('user')") is None
            conn.execute(sa.text(enabled_sql))
            conn.commit()

            # key UPDATE denied (both keys pass the whitelist CK; no UQ conflict)
            msg = attempt("UPDATE acl_subject_types SET key='role' WHERE key='user'")
            assert msg and "key is immutable" in msg

            # DELETE denied (no FK/CK forbids it; only the trigger does)
            msg = attempt("DELETE FROM acl_subject_types WHERE key='user'")
            assert msg and "retire via archived_at" in msg

            # non-controlled columns stay writable (selective enforcement)
            assert attempt("UPDATE acl_subject_types SET description='ok' WHERE key='user'") is None
            assert attempt("UPDATE acl_subject_types SET archived_at=now() WHERE key='user'") is None

            # trigger is left enabled; registry returns to its frozen zero-seed state
            assert _scalar(
                "SELECT tgenabled FROM pg_trigger WHERE tgname='tg_acl_subject_types_protect'"
            ) == "O"
        # controlled cleanup path (M-1)
        with engine.connect() as conn:
            conn.execute(sa.text(disabled_sql))
            conn.commit()
            conn.execute(sa.text("DELETE FROM acl_subject_types"))
            conn.commit()
            conn.execute(sa.text(enabled_sql))
            conn.commit()
        assert _scalar("SELECT count(*) FROM acl_subject_types") == 0
    finally:
        engine.dispose()


def test_registry_whitelist_rejects_group_and_bad_format(db) -> None:
    """C8 / C9 — the registry CHECKs are isolated from the protect trigger.

    A BEFORE trigger runs before CHECK constraints, so the trigger is disabled
    on the controlled path (B1-4_DESIGN.md §8.1, M-1) to prove that the
    whitelist CK and the format CK are the objects rejecting bad keys.
    """
    engine = _engine()
    try:
        with engine.connect() as conn:
            conn.execute(sa.text(
                "ALTER TABLE acl_subject_types DISABLE TRIGGER tg_acl_subject_types_protect"
            ))
            conn.commit()  # DDL must survive the rollbacks below
            try:
                for bad in ("group", "team", "user2"):
                    with pytest.raises(sa.exc.IntegrityError):
                        conn.execute(sa.text(
                            "INSERT INTO acl_subject_types (key) VALUES (:k)"
                        ), {"k": bad})
                        conn.commit()
                    conn.rollback()
                # format CK (not the whitelist) rejects malformed keys
                for bad in ("GROUP", "User", "user-x", "1user", "u" * 33):
                    with pytest.raises(sa.exc.IntegrityError):
                        conn.execute(sa.text(
                            "INSERT INTO acl_subject_types (key) VALUES (:k)"
                        ), {"k": bad})
                        conn.commit()
                    conn.rollback()
            finally:
                conn.execute(sa.text(
                    "ALTER TABLE acl_subject_types ENABLE TRIGGER tg_acl_subject_types_protect"
                ))
                conn.commit()
            # no bad key leaked into the registry
            assert _scalar("SELECT count(*) FROM acl_subject_types") == 0
    finally:
        engine.dispose()


# =================================================== scope / boundary audit
def test_g_h_i_j_absent_and_rls_disabled(db) -> None:
    present = {r[0] for r in _rows(
        "SELECT tgname FROM pg_trigger WHERE tgname = ANY(:n)", n=list(P09_ACL_TRIGGERS)
    )}
    assert present == set()
    assert _scalar("SELECT count(*) FROM pg_policies") == 0
    assert _scalar(
        "SELECT count(*) FROM pg_class WHERE relname = ANY(:t) "
        "AND (relrowsecurity OR relforcerowsecurity)", t=list(B14_TABLES)
    ) == 0


def test_migration_has_no_domain_or_rls_statements(db) -> None:
    import pathlib
    src = pathlib.Path("migrations_alembic/versions/0007_b1_4_resource_acl.py").read_text(encoding="utf-8").lower()
    for term in ("row level security", "create policy", "'group'", "restaurant",
                 "company", "entertainment", "family"):
        assert term not in src, term
