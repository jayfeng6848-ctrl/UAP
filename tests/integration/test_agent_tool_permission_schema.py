"""P09 Agent / Tool Permission — schema, delete-rules, constraints, triggers, migration.

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).

Covers the frozen P09 decisions (canonical obligation list = T-01 ～ T-37):
  * D-P09-01 = B      tool_executions is **NOT partitioned**; PK = id; 90d hard delete
                      (executor is NOT part of P09 — manual operations / DESIGN DEFERRED)
  * D-P09-02 = A      tool_executions.tenant_id NOT NULL -> tenants.id ON DELETE RESTRICT
  * D-P09-03          ON DELETE for 16 FKs (5 CASCADE / 6 RESTRICT / 5 SET NULL);
                      tool_executions has **CASCADE = 0** (history survives agent/user purge)
  * D-P09-04 = A      uq_tool_exec_idem is a **UNIQUE INDEX** (partial), never a CONSTRAINT
  * D-P09-05 = B      agent_permissions has **2** CHECKs (scope target + effect)
  * D-P09-06 = A      G/H/I/J stay "after P09" (must NOT exist)
  * D-P09-07 = A      P09 = SCHEMA ONLY (no runtime / API / worker / scheduler)
  * D-P09-09          revision identity 0011_p09_agent_tool_permission
  * D-P09-10          ai_request_logs.agent_id stays **NO FK** (P08 -> P09 forward FK = 0)
  * D-P09-11 = A      deferred-*creation* FK, downgraded **first** (not DEFERRABLE)
  * D-P09-12 = A      agents tenant/space consistency trigger (structural integrity only)
  * D-P09-13          tool_executions = 3 CHECKs (status / attempts >= 1 / duration_ms >= 0)
  * D-P09-14 = A      agent_versions published rows: UPDATE and DELETE both RAISE (no exemption)
  * D-P09-15          index authority = STEP1B_INDEX_STRATEGY; 8 index objects; no extra FK indexes
  * D-P09-16          UNIQUE CONSTRAINT = 1 (uq_agent_versions) · UNIQUE INDEX = 3
  * D-P09-17 = A      0008 is untouched (append-only)
  * D-P09-18          ND-06 annotations (CM 3x / CORE 1x) reflected in the schema
  * ND-A FROZEN AS NO-TIGHTENING   ck_agent_permissions_scope_target = pure IS NOT NULL (no <> '')
  * ND-B FROZEN AS NON-DEFERRABLE  fk_agents_current_version: condeferrable = false

Out of scope (must NOT exist): events, audit_logs, groups, resource_relations,
G/H/I/J ACL triggers, RLS, Authorization evaluation, retention executor,
partitions, runtime agent execution.
"""

from __future__ import annotations

import hashlib
import pathlib
import re

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

ROOT = pathlib.Path(__file__).resolve().parents[2]

P09_TABLES = {"agents", "agent_versions", "agent_permissions", "tool_executions"}
P09_TRIGGERS = {
    "tg_agents_set_updated_at",
    "tg_agents_tenant_space_consistency",
    "tg_version_immutable",
    "tg_agent_acl_expire",  # P11 (0014) 交付（D-P11-01）；agents 表上的 AFTER U/D
}
P09_FUNCTIONS = {"enforce_agents_tenant_space_consistency", "enforce_agent_versions_immutable"}
P09_CHECK_CONSTRAINTS = {
    "ck_agents_status",
    "ck_agents_max_risk_level",
    "ck_agent_versions_status",
    "ck_agent_permissions_scope_target",
    "ck_agent_permissions_effect",
    "ck_tool_executions_status",
    "ck_tool_executions_attempts",
    "ck_tool_executions_duration",
}
# 8 index objects (T-21). uq_agent_versions is a UNIQUE CONSTRAINT (created with the table).
P09_INDEX_OBJECTS = {
    "uq_agents_key",
    "ix_agents_tenant_status",
    "uq_agent_perm",
    "ix_ap_agent",
    "uq_tool_exec_idem",
    "ix_texec_tenant_created",
    "ix_texec_status",
}
P09_UNIQUE_INDEX_OBJECTS = {"uq_agents_key", "uq_agent_perm", "uq_tool_exec_idem"}
P09_PK_INDEXES = {
    "agents_pkey",
    "agent_versions_pkey",
    "agent_permissions_pkey",
    "tool_executions_pkey",
}
# uq_agent_versions is a UNIQUE **CONSTRAINT**; PostgreSQL names its backing index
# identically, so it is visible in ``pg_indexes`` as well (T-23 keeps the two apart).
P09_CONSTRAINT_BACKED_INDEXES = {"uq_agent_versions"}

# T-05/T-06 — the 16 frozen FK delete rules.
FK_DELETE_RULES = {
    # F1/F2/F3 — new (D-P09-03)
    "fk_agents_tenant": "r",
    "fk_agents_space": "r",
    "fk_agents_owner": "r",
    # F4/F5 — pre-existing
    "fk_agents_default_route": "n",
    "fk_agents_current_version": "n",
    # F6 — pre-existing · F7 — new
    "fk_agent_versions_agent": "c",
    "fk_agent_versions_published_by": "n",
    # F8/F9 — pre-existing · F10/F11 — new
    "fk_agent_permissions_agent": "c",
    "fk_agent_permissions_version": "c",
    "fk_agent_permissions_permission": "c",
    "fk_agent_permissions_tool": "c",
    # F12 — new · F13/F14 — pre-existing · F15/F16 — new
    "fk_tool_executions_tenant": "r",
    "fk_tool_executions_tool": "r",
    "fk_tool_executions_tool_version": "r",
    "fk_tool_executions_agent": "n",
    "fk_tool_executions_actor": "n",
}

COLUMN_COUNTS = {
    "agents": 15,
    "agent_versions": 12,
    "agent_permissions": 9,
    "tool_executions": 18,
}
NULLABLE_COLUMNS = {
    "agents": {"space_id", "description", "current_version_id", "default_route_id", "archived_at"},
    "agent_versions": {"input_schema", "output_schema", "published_by", "published_at"},
    "agent_permissions": {"version_id", "permission_id", "tool_id", "resource_scope", "conditions"},
    "tool_executions": {
        "agent_id", "actor_id", "idempotency_key", "output_digest",
        "risk_level", "finished_at", "duration_ms", "error_code",
    },
}
TIMESTAMP_COLUMNS = {
    "agents": {"archived_at", "created_at", "updated_at"},
    "agent_versions": {"published_at", "created_at"},
    "agent_permissions": {"created_at"},
    "tool_executions": {"started_at", "finished_at", "created_at"},
}
NOW_DEFAULT_COLUMNS = {
    ("agents", "created_at"), ("agents", "updated_at"),
    ("agent_versions", "created_at"), ("agent_permissions", "created_at"),
    ("tool_executions", "created_at"),
}
G_H_I_J = {
    "tg_acl_subject_exists",
    "tg_acl_user_hard_delete",
    "tg_acl_role_delete_block",
    "tg_agent_acl_expire",
}
FORBIDDEN_TABLES = {"groups", "resource_relations"}  # P10 交付 events/audit_logs

# 非 published 的夹具状态字面值：ck_agent_versions_status 允许 4 值，draft 属其中，
# 这里用它表示"尚未发布"（不构成新词表）。
_FIXTURE_NOT_PUBLISHED = "draft"


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #
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


def _connect():
    engine = _engine()
    return engine, engine.connect()


def _fresh_tenant(conn, slug: str = "p09") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tenants (slug, display_name, status) "
            "VALUES (:s, :s, 'active') RETURNING id"
        ),
        {"s": slug},
    ).scalar()


def _fresh_user(conn, name: str = "p09user") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO users (email, username, status) "
            "VALUES (:e, :u, 'active') RETURNING id"
        ),
        {"e": f"{name}@example.com", "u": name},
    ).scalar()


def _fresh_space(conn, tenant_id, key: str = "p09space") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
            "VALUES (:t, :k, :k, 'work', 'private', 'active') RETURNING id"
        ),
        {"t": tenant_id, "k": key},
    ).scalar()


def _fresh_permission(conn, key: str = "agent.invoke") -> str:
    """`permissions` is a P04 table with zero rows (seed is P13); a fixture row is required.

    The action literal is ``'execute'`` because ``SC-1`` (``D-AUTH-05`` via
    ``0012``) constrains ``permissions.action`` to the canonical vocabulary.
    The original fixture value ``'invoke'`` predates that vocabulary
    (§24 classification: historical compatibility) and no test asserts it.
    """
    return conn.execute(
        sa.text(
            "INSERT INTO permissions (key, action, description) "
            "VALUES (:k, 'execute', 'fixture') RETURNING id"
        ),
        {"k": key},
    ).scalar()


def _fresh_tool(conn, tenant_id=None, key: str = "p09tool") -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tools (tenant_id, key, name, risk_level, timeout_ms, "
            "idempotency_mode, audit_policy, approval_required, enabled) "
            "VALUES (:t, :k, :k, 'LOW', 1000, 'none', 'full', false, true) RETURNING id"
        ),
        {"t": tenant_id, "k": key},
    ).scalar()


def _fresh_tool_version(conn, tool_id, version: int = 1) -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO tool_versions (tool_id, version, input_schema, output_schema, "
            "risk_level, timeout_ms, handler_ref, checksum, status) "
            "VALUES (:t, :v, '{}'::jsonb, '{}'::jsonb, 'LOW', 1000, "
            "'svc.handler', 'sha256:fixture', 'draft') RETURNING id"
        ),
        {"t": tool_id, "v": version},
    ).scalar()


def _fresh_agent(conn, tenant_id, owner_id, key: str = "agent1", **over) -> str:
    values = {"t": tenant_id, "o": owner_id, "k": key, "s": None}
    values.update(over)
    return conn.execute(
        sa.text(
            "INSERT INTO agents (tenant_id, owner_id, key, name, status, max_risk_level, "
            "config, space_id) "
            "VALUES (:t, :o, :k, :k, 'draft', 'LOW', '{}'::jsonb, :s) RETURNING id"
        ),
        values,
    ).scalar()


def _fresh_agent_version(conn, agent_id, version: int = 1, status: str = _FIXTURE_NOT_PUBLISHED) -> str:
    return conn.execute(
        sa.text(
            "INSERT INTO agent_versions (agent_id, version, definition, allowed_tools, "
            "checksum, status) "
            "VALUES (:a, :v, '{}'::jsonb, '[]'::jsonb, 'sha256:fixture', :s) RETURNING id"
        ),
        {"a": agent_id, "v": version, "s": status},
    ).scalar()


def _expect_failure(conn, sql: str, params: dict | None = None, *, contains: str | None = None) -> str:
    """Run a statement expected to violate a constraint, inside a SAVEPOINT.

    The savepoint keeps the outer transaction usable (so a single connection can
    exercise several independent negative cases), and guarantees the raised error
    comes from the statement itself rather than from an aborted transaction.
    """
    sp = conn.begin_nested()
    try:
        with pytest.raises(sa.exc.DBAPIError) as exc:
            conn.execute(sa.text(sql), params or {})
        message = str(exc.value)
        if contains is not None:
            assert contains in message, message
        return message
    finally:
        sp.rollback()

# ===================================================== T-19 / T-20 (identity)
def test_t19_revision_identity() -> None:
    """T-19 — revision id == filename, <= 32 chars, single head."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    path = ROOT / "migrations_alembic" / "versions" / "0011_p09_agent_tool_permission.py"
    assert path.exists()
    assert path.stem == "0011_p09_agent_tool_permission"
    assert len(path.stem) <= 32
    source = path.read_text(encoding="utf-8")
    assert 'revision = "0011_p09_agent_tool_permission"' in source
    assert 'down_revision = "0010_b1_6_ai_gateway"' in source
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert script.get_heads() == ["0015_p12_indexes"]


def test_t20_tables_exist(db) -> None:
    """T-20 — the four P09 tables exist."""
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert P09_TABLES <= tables


# ===================================================== T-01 / T-02 / T-03
def test_t01_tool_executions_not_partitioned(db) -> None:
    """T-01 — tool_executions is an ordinary table (D-P09-01 = B)."""
    relkind = _scalar("SELECT relkind FROM pg_class WHERE relname='tool_executions'")
    assert relkind == "r"
    assert _scalar("SELECT count(*) FROM pg_partitioned_table p JOIN pg_class c ON c.oid=p.partrelid "
                   "WHERE c.relname='tool_executions'") == 0
    children = _rows(
        "SELECT c.relname FROM pg_inherits i "
        "JOIN pg_class c ON c.oid = i.inhrelid "
        "JOIN pg_class p ON p.oid = i.inhparent "
        "WHERE p.relname = 'tool_executions'"
    )
    assert children == []
    # no partition keys anywhere in the P09 tables
    assert _scalar(
        "SELECT count(*) FROM pg_partitioned_table p JOIN pg_class c ON c.oid = p.partrelid "
        "WHERE c.relname = ANY(:t)", t=list(P09_TABLES)
    ) == 0


def test_t02_tool_executions_pk_is_id(db) -> None:
    """T-02 — tool_executions PK = (id) only."""
    cols = [r[0] for r in _rows(
        "SELECT a.attname FROM pg_constraint c "
        "JOIN pg_class t ON t.oid = c.conrelid "
        "JOIN unnest(c.conkey) k(attnum) ON true "
        "JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum "
        "WHERE c.contype='p' AND t.relname='tool_executions' ORDER BY 1"
    )]
    assert cols == ["id"]


def test_t03_tool_executions_tenant_id_not_null(db) -> None:
    """T-03 — D-P09-02 = A: tenant_id is NOT NULL."""
    nullable = _scalar(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name='tool_executions' AND column_name='tenant_id'"
    )
    assert nullable == "NO"


# ===================================================== T-04 ～ T-07 (delete rules)
def test_t04_tenant_fk_is_restrict(db) -> None:
    """T-04 — F12: tool_executions.tenant_id -> tenants.id = RESTRICT."""
    assert _scalar(
        "SELECT confdeltype FROM pg_constraint "
        "WHERE conname='fk_tool_executions_tenant' AND contype='f'"
    ) == "r"


def test_t05_and_t06_fk_delete_rules_exact(db) -> None:
    """T-05/T-06 — all 16 ON DELETE actions match the frozen decisions."""
    actual = {
        r[0]: r[1]
        for r in _rows(
            "SELECT c.conname, c.confdeltype FROM pg_constraint c "
            "JOIN pg_class t ON t.oid = c.conrelid "
            "WHERE c.contype='f' AND t.relname = ANY(:t)", t=list(P09_TABLES)
        )
    }
    assert actual == FK_DELETE_RULES
    assert len(actual) == 16


def test_t07_tool_executions_has_zero_cascade(db) -> None:
    """T-07 — history protection: the 5 tool_executions FKs are only R / N."""
    rules = {
        r[0]: r[1]
        for r in _rows(
            "SELECT c.conname, c.confdeltype FROM pg_constraint c "
            "JOIN pg_class t ON t.oid = c.conrelid "
            "WHERE c.contype='f' AND t.relname='tool_executions'"
        )
    }
    assert len(rules) == 5
    assert set(rules.values()) <= {"r", "n"}
    assert not any(v == "c" for v in rules.values())


# ===================================================== T-08 / T-23 / T-21 / T-22
def test_t08_uq_tool_exec_idem_is_unique_index_not_constraint(db) -> None:
    """T-08 — D-P09-04 = A: UNIQUE INDEX with the partial predicate."""
    indexdef = _scalar(
        "SELECT indexdef FROM pg_indexes WHERE indexname='uq_tool_exec_idem'"
    )
    assert indexdef is not None
    assert "UNIQUE INDEX" in indexdef
    assert "idempotency_key IS NOT NULL" in indexdef
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE conname='uq_tool_exec_idem'"
    ) == 0


def test_t23_uq_accounting_constraint_1_index_3(db) -> None:
    """T-23 — D-P09-16: UNIQUE CONSTRAINT = 1 · UNIQUE INDEX = 3 (pg_constraint vs pg_indexes)."""
    constraints = {r[0] for r in _rows(
        "SELECT c.conname FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE c.contype='u' AND t.relname = ANY(:t)", t=list(P09_TABLES)
    )}
    assert constraints == {"uq_agent_versions"}
    unique_indexes = {
        r[0]
        for r in _rows(
            "SELECT i.indexname FROM pg_indexes i "
            "WHERE i.schemaname='public' AND i.tablename = ANY(:t) "
            # PK indexes are unique indexes too, and uq_agent_versions is a UNIQUE
            # CONSTRAINT: both are constraint-backed, so only standalone unique
            # indexes are counted here (D-P09-16: UNIQUE INDEX = 3).
            "AND i.indexdef LIKE 'CREATE UNIQUE INDEX%' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM pg_constraint c "
            "  JOIN pg_class tc ON tc.oid = c.conrelid "
            "  JOIN pg_class ic ON ic.oid = c.conindid "
            "  WHERE c.contype IN ('p','u') "
            "  AND tc.relname = i.tablename AND ic.relname = i.indexname"
            ")",
            t=list(P09_TABLES),
        )
    }
    assert unique_indexes == P09_UNIQUE_INDEX_OBJECTS
    assert len(unique_indexes) == 3


# P12 (0015) delivered 7 FK reverse-lookup indexes on P09 tables (`D-P12-13`,
# GUARD-1 removed 5 of these names from T-22's forbidden set).
P12_P09_TABLE_INDEXES = {
    "ix_ap_permission", "ix_ap_tool", "ix_ap_version",
    "ix_agents_current_version", "ix_agents_default_route",
    "ix_texec_tool", "ix_texec_tool_version",
}


def test_t21_index_objects_exactly_eight(db) -> None:
    """T-21 — D-P09-15 的 8 对象（+4 隐式 PK）+ P12 (0015) 交付的 7 个反查索引。"""
    names = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename = ANY(:t)",
        t=list(P09_TABLES),
    )}
    assert names == (P09_INDEX_OBJECTS | P09_CONSTRAINT_BACKED_INDEXES | P09_PK_INDEXES
                     | P12_P09_TABLE_INDEXES)
    assert len(names) == 19
    # D-P09-15 deliverables = 8 index objects: 7 explicit index objects
    # + 1 UNIQUE CONSTRAINT (uq_agent_versions, backing index of the same name)
    assert len(P09_INDEX_OBJECTS) == 7
    assert len(P09_INDEX_OBJECTS) + len(P09_CONSTRAINT_BACKED_INDEXES) == 8


def test_t22_no_extra_fk_column_indexes(db) -> None:
    """T-22 — no additional single FK-column indexes (STEP1B_INDEX_STRATEGY authority).

    `GUARD-1`（2026-09-25 Human Decision · APPROVED）：P12（0015）交付其中恰 5 名
    （ix_ap_permission / ix_ap_tool / ix_ap_version / ix_agents_current_version /
    ix_agents_default_route）⇒ 已从本 forbidden 集移除（`removed ⊆ P12 CREATE set`）；
    其余 5 名保留（`remaining ∩ P12 CREATE set = ∅`）。
    """
    names = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename = ANY(:t)",
        t=list(P09_TABLES),
    )}
    forbidden = {
        "ix_agents_owner", "ix_agents_space",
        "ix_texec_agent", "ix_texec_actor",
        "ix_agent_versions_published_by",
    }
    assert not (names & forbidden)


# ===================================================== T-09 / T-24 (CHECKs)
def test_t09_agent_permissions_has_two_checks(db) -> None:
    """T-09 — D-P09-05 = B: exactly 2 CHECKs, never merged."""
    checks = {r[0] for r in _rows(
        "SELECT c.conname FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE c.contype='c' AND t.relname='agent_permissions'"
    )}
    assert checks == {"ck_agent_permissions_scope_target", "ck_agent_permissions_effect"}
    assert len(checks) == 2


def test_t24_tool_executions_three_checks_semantics(db) -> None:
    """T-24 — D-P09-13: status domain + attempts >= 1 + duration_ms >= 0."""
    checks = {r[0] for r in _rows(
        "SELECT c.conname FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE c.contype='c' AND t.relname='tool_executions'"
    )}
    assert checks == {
        "ck_tool_executions_status",
        "ck_tool_executions_attempts",
        "ck_tool_executions_duration",
    }

    insert = (
        "INSERT INTO tool_executions (tenant_id, tool_id, tool_version_id, status, "
        "input_digest, attempts, started_at, correlation_id, duration_ms) "
        "VALUES (:t, :tl, :tv, :st, :dg, :at, now(), :cor, :dur)"
    )
    engine, conn = _connect()
    try:
        tenant = _fresh_tenant(conn)
        tool = _fresh_tool(conn, tenant)
        tver = _fresh_tool_version(conn, tool)
        base = {
            "t": tenant, "tl": tool, "tv": tver, "st": "running",
            "dg": "sha256:in", "at": 1, "cor": "cid-1", "dur": None,
        }
        # valid rows accepted (duration_ms NULL passes: NULL comparison semantics)
        conn.execute(sa.text(insert), base)
        conn.execute(sa.text(insert), {**base, "cor": "cid-2", "dur": 0})
        # ck_tool_executions_status
        _expect_failure(conn, insert, {**base, "st": "bogus", "cor": "cid-3"},
                        contains="ck_tool_executions_status")
        # ck_tool_executions_attempts
        _expect_failure(conn, insert, {**base, "at": 0, "cor": "cid-4"},
                        contains="ck_tool_executions_attempts")
        # ck_tool_executions_duration
        _expect_failure(conn, insert, {**base, "dur": -1, "cor": "cid-5"},
                        contains="ck_tool_executions_duration")
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_t34_no_secret_columns(db) -> None:
    """T-34 — no secret / DSN / token / credential columns in the P09 tables."""
    cols = [r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ANY(:t)",
        t=list(P09_TABLES),
    )]
    pattern = re.compile(r"(secret|dsn|password|passwd|token|credential|api[_-]?key)", re.I)
    assert [c for c in cols if pattern.search(c)] == []


# ===================================================== T-10 / T-11 / T-35 (consistency trigger)
def test_t10_agents_tenant_space_consistency(db) -> None:
    """T-10 — D-P09-12: NULL passes; same-tenant space passes; cross-tenant space rejected."""
    agent_sql = (
        "INSERT INTO agents (tenant_id, owner_id, key, name, status, max_risk_level, "
        "config, space_id) VALUES (:t, :o, :k, :k, 'draft', 'LOW', '{}'::jsonb, :s)"
    )
    engine, conn = _connect()
    try:
        tenant_a = _fresh_tenant(conn, "p09a")
        tenant_b = _fresh_tenant(conn, "p09b")
        user = _fresh_user(conn)
        space_a = _fresh_space(conn, tenant_a, "space-a")
        space_b = _fresh_space(conn, tenant_b, "space-b")

        # space_id IS NULL -> allowed
        conn.execute(sa.text(agent_sql), {"t": tenant_a, "o": user, "k": "a-null", "s": None})
        # space of the same tenant -> allowed
        conn.execute(sa.text(agent_sql), {"t": tenant_a, "o": user, "k": "a-ok", "s": space_a})
        # space of another tenant -> rejected by the consistency trigger
        _expect_failure(conn, agent_sql,
                        {"t": tenant_a, "o": user, "k": "a-cross", "s": space_b},
                        contains="cross-tenant agent denied")
        # non-existent space -> rejected (trigger raises before the FK check)
        _expect_failure(conn, agent_sql,
                        {"t": tenant_a, "o": user, "k": "a-ghost",
                         "s": "00000000-0000-0000-0000-00000000beef"},
                        contains="does not exist")
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_t11_consistency_trigger_has_no_authorization_semantics(db) -> None:
    """T-11 — the trigger only checks structural integrity (no ALLOW/DENY/role/permission logic)."""
    prosrc = _scalar(
        "SELECT prosrc FROM pg_proc WHERE proname='enforce_agents_tenant_space_consistency'"
    )
    assert prosrc is not None
    lowered = prosrc.lower()
    for token in ("allow", "deny", "permission", "role", "acl", "grant", "policy"):
        assert token not in lowered, token
    # and it never writes to other tables
    for token in ("insert into", "update ", "delete from"):
        assert token not in lowered, token


def test_t35_consistency_trigger_does_not_replace_fk(db) -> None:
    """T-35 — with the trigger disabled, the FK still rejects a non-existent space_id."""
    engine, conn = _connect()
    try:
        conn.execute(sa.text(
            "ALTER TABLE agents DISABLE TRIGGER tg_agents_tenant_space_consistency"
        ))
        tenant = _fresh_tenant(conn)
        user = _fresh_user(conn)
        with pytest.raises(sa.exc.DBAPIError):
            _fresh_agent(
                conn, tenant, user, key="fk-only",
                s="00000000-0000-0000-0000-00000000dead",
            )
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


# ===================================================== T-13 / T-25 (immutability)
def test_t13_agent_versions_published_is_immutable(db) -> None:
    """T-13 — published rows reject UPDATE and DELETE."""
    engine, conn = _connect()
    try:
        tenant = _fresh_tenant(conn)
        user = _fresh_user(conn)
        agent = _fresh_agent(conn, tenant, user)
        version = _fresh_agent_version(conn, agent, status="published")

        _expect_failure(conn, "UPDATE agent_versions SET checksum='x' WHERE id=:i",
                        {"i": version}, contains="immutable")
        _expect_failure(conn, "DELETE FROM agent_versions WHERE id=:i",
                        {"i": version}, contains="immutable")
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_t25_no_state_migration_exemption(db) -> None:
    """T-25 — D-P09-14: published -> deprecated / revoked are BOTH rejected at the DB layer."""
    engine, conn = _connect()
    try:
        tenant = _fresh_tenant(conn)
        user = _fresh_user(conn)
        agent = _fresh_agent(conn, tenant, user)
        version = _fresh_agent_version(conn, agent, status="published")
        for target in ("deprecated", "revoked"):
            _expect_failure(conn, "UPDATE agent_versions SET status=:s WHERE id=:i",
                            {"s": target, "i": version}, contains="immutable")
        _expect_failure(conn, "UPDATE agent_versions SET status='published' WHERE id=:i",
                        {"i": version}, contains="immutable")
        # a draft row stays mutable (the trigger only guards published rows)
        draft = _fresh_agent_version(conn, agent, version=2, status="draft")
        conn.execute(sa.text("UPDATE agent_versions SET checksum='changed' WHERE id=:i"),
                     {"i": draft})
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


# ===================================================== T-36 / T-37 (index semantics)
def test_t36_uq_agents_key_partial_predicate(db) -> None:
    """T-36 — the partial predicate releases the key once the agent is archived."""
    agent_sql = (
        "INSERT INTO agents (tenant_id, owner_id, key, name, status, max_risk_level, "
        "config, space_id) VALUES (:t, :o, :k, :k, 'draft', 'LOW', '{}'::jsonb, :s)"
    )
    engine, conn = _connect()
    try:
        tenant = _fresh_tenant(conn)
        user = _fresh_user(conn)
        first = conn.execute(
            sa.text(agent_sql + " RETURNING id"),
            {"t": tenant, "o": user, "k": "dup", "s": None},
        ).scalar()
        # same (tenant_id, lower(key)) while archived_at IS NULL -> conflict
        _expect_failure(conn, agent_sql, {"t": tenant, "o": user, "k": "dup", "s": None},
                        contains="uq_agents_key")
        # the index uses lower(key) -> an upper-case variant collides as well
        _expect_failure(conn, agent_sql, {"t": tenant, "o": user, "k": "DUP", "s": None},
                        contains="uq_agents_key")
        # archive the first agent -> the key becomes reusable
        conn.execute(sa.text("UPDATE agents SET archived_at = now() WHERE id=:i"),
                     {"i": first})
        conn.execute(sa.text(agent_sql), {"t": tenant, "o": user, "k": "dup", "s": None})
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


def test_t37_uq_agent_perm_coalesce_normalization(db) -> None:
    """T-37 — COALESCE normalization.

    ``uq_agent_perm`` indexes ``COALESCE(version_id, nil)``, ``COALESCE(permission_id, nil)``,
    ``COALESCE(tool_id, nil)`` and ``COALESCE(resource_scope, '')``.  Therefore
    NULL placeholders and explicit nil-uuid / '' placeholders are **equivalent**
    for uniqueness purposes, while a distinct non-empty value ('   ') is not.
    """
    insert = (
        "INSERT INTO agent_permissions (agent_id, version_id, permission_id, tool_id, "
        "resource_scope, effect) VALUES (:a, :v, :p, :tl, :rs, 'allow')"
    )
    engine, conn = _connect()
    try:
        tenant = _fresh_tenant(conn)
        user = _fresh_user(conn)
        agent = _fresh_agent(conn, tenant, user)
        permission = _fresh_permission(conn)
        base = {"a": agent, "v": None, "p": permission, "tl": None, "rs": None}
        nil = "00000000-0000-0000-0000-000000000000"

        # NULL placeholders
        conn.execute(sa.text(insert), base)
        # explicit nil-uuid placeholders are equivalent to NULL -> conflict
        _expect_failure(conn, insert, {**base, "v": nil, "tl": nil},
                        contains="uq_agent_perm")
        # resource_scope '' COALESCEs to the same value as NULL -> conflict
        _expect_failure(conn, insert, {**base, "rs": ""}, contains="uq_agent_perm")
        # a distinct non-empty value is a separate scope -> accepted
        conn.execute(sa.text(insert), {**base, "rs": "   "})
        # duplicate of the distinct value -> conflict
        _expect_failure(conn, insert, {**base, "rs": "   "}, contains="uq_agent_perm")
        # degenerate row (all three target columns NULL) is rejected by CK-4
        _expect_failure(conn,
                        "INSERT INTO agent_permissions (agent_id, effect) VALUES (:a, 'allow')",
                        {"a": agent}, contains="ck_agent_permissions_scope_target")
        conn.rollback()
    finally:
        conn.close()
        engine.dispose()


# ===================================================== T-27 / T-28 / T-29 / T-30
def test_t27_column_type_matrix(db) -> None:
    """T-27 — 54 columns: uuid 20 · text 16 · timestamptz 9 · jsonb 6 · integer 3."""
    rows = _rows(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name = ANY(:t)", t=list(P09_TABLES)
    )
    assert len(rows) == 54
    per_table = {}
    for table, _c, _t in rows:
        per_table[table] = per_table.get(table, 0) + 1
    assert per_table == COLUMN_COUNTS

    def bucket(data_type: str) -> str:
        if data_type == "uuid":
            return "uuid"
        if data_type == "text":
            return "text"
        if data_type.startswith("timestamp"):
            return "timestamptz"
        if data_type == "jsonb":
            return "jsonb"
        if data_type == "integer":
            return "integer"
        return data_type

    counts = {}
    for _t, _c, data_type in rows:
        key = bucket(data_type)
        counts[key] = counts.get(key, 0) + 1
    assert counts == {"uuid": 20, "text": 16, "timestamptz": 9, "jsonb": 6, "integer": 3}


def test_t28_timestamp_precision_is_three(db) -> None:
    """T-28 — all 9 timestamp columns are timestamptz(3)."""
    rows = _rows(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name = ANY(:t) "
        "AND data_type LIKE 'timestamp%'", t=list(P09_TABLES)
    )
    found = {}
    for table, column in rows:
        found.setdefault(table, set()).add(column)
    assert found == TIMESTAMP_COLUMNS
    assert _scalar(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name = ANY(:t) AND data_type='timestamp with time zone' "
        "AND datetime_precision=3", t=list(P09_TABLES)
    ) == 9
    assert _scalar(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name = ANY(:t) AND data_type LIKE 'timestamp%' "
        "AND (data_type <> 'timestamp with time zone' OR datetime_precision <> 3)",
        t=list(P09_TABLES),
    ) == 0


def test_t29_object_names_exact(db) -> None:
    """T-29 — CK / FK / index / trigger / function names match the design verbatim."""
    checks = {r[0] for r in _rows(
        "SELECT c.conname FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid "
        "WHERE c.contype='c' AND t.relname = ANY(:t)", t=list(P09_TABLES)
    )}
    fks = {r[0] for r in _rows(
        "SELECT c.conname FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid "
        "WHERE c.contype='f' AND t.relname = ANY(:t)", t=list(P09_TABLES)
    )}
    indexes = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename = ANY(:t)",
        t=list(P09_TABLES),
    )}
    triggers = {r[0] for r in _rows(
        "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgrelid::regclass::text = ANY(:t)",
        t=list(P09_TABLES),
    )}
    functions = {r[0] for r in _rows(
        "SELECT proname FROM pg_proc WHERE proname = ANY(:n)", n=sorted(P09_FUNCTIONS)
    )}
    assert checks == P09_CHECK_CONSTRAINTS
    assert fks == set(FK_DELETE_RULES)
    assert indexes == (P09_INDEX_OBJECTS | P09_CONSTRAINT_BACKED_INDEXES | P09_PK_INDEXES
                       | P12_P09_TABLE_INDEXES)   # + P12 (0015) 7 个反查索引
    assert triggers == P09_TRIGGERS
    assert functions == P09_FUNCTIONS


def test_t30_default_matrix(db) -> None:
    """T-30 — defaults: id -> uap_uuid_v7(); created_at/updated_at -> now(); nothing else."""
    rows = _rows(
        "SELECT table_name, column_name, column_default FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name = ANY(:t)", t=list(P09_TABLES)
    )
    now_defaults = {(t, c) for t, c, d in rows if d == "now()"}
    uuid_defaults = {(t, c) for t, c, d in rows if d and "uap_uuid_v7" in d}
    assert now_defaults == NOW_DEFAULT_COLUMNS
    assert uuid_defaults == {(t, "id") for t in P09_TABLES}
    others = {
        (t, c, d)
        for t, c, d in rows
        if d and d != "now()" and "uap_uuid_v7" not in d
    }
    assert others == set()


# ===================================================== T-12 / T-14 / T-15 / T-16 / T-17 / T-18
def test_t12_acl_triggers_g_h_i_j_present_on_canonical_tables(db) -> None:
    """T-12 — D-P09-06（历史）：G/H/I/J 在 P09 时不存在；`D-P11-01`（2026-09-26
    实施授权）已交付四者，此断言翻转为**规范表挂载**的存在性检查。"""
    placement = dict(_rows(
        "SELECT tgname, tgrelid::regclass::text FROM pg_trigger "
        "WHERE NOT tgisinternal AND tgparentid = 0 AND tgname = ANY(:n)",
        n=sorted(G_H_I_J)))
    assert placement == {
        "tg_acl_subject_exists": "resource_permissions",
        "tg_acl_user_hard_delete": "users",
        "tg_acl_role_delete_block": "roles",
        "tg_agent_acl_expire": "agents",
    }
    # P09 自身交付面不含任何 G/H/I/J 同名函数（函数名 = enforce_*，无重叠）
    functions = {r[0] for r in _rows("SELECT proname FROM pg_proc")}
    assert not {f for f in functions if f in G_H_I_J}


def test_t14_deferred_creation_fk(db) -> None:
    """T-14 — fk_agents_current_version exists (SET NULL) and is created last."""
    rule = _scalar(
        "SELECT confdeltype FROM pg_constraint WHERE conname='fk_agents_current_version'"
    )
    assert rule == "n"
    source = (ROOT / "migrations_alembic" / "versions" / "0011_p09_agent_tool_permission.py").read_text(
        encoding="utf-8"
    )
    upgrade_body = source.split("def upgrade()")[1].split("def downgrade()")[0]
    assert upgrade_body.index("CREATE TRIGGER") < upgrade_body.index(
        "ADD CONSTRAINT fk_agents_current_version"
    )


def test_t15_zero_seed(db) -> None:
    """T-15 — P09 delivers zero seed rows."""
    for table in sorted(P09_TABLES):
        assert _scalar(f"SELECT count(*) FROM {table}") == 0


def test_t16_ai_request_logs_still_has_no_agent_fk(db) -> None:
    """T-16 — D-P09-10: ai_request_logs FK columns remain {provider_id, model_id}."""
    cols = sorted(r[0] for r in _rows(
        "SELECT a.attname FROM pg_constraint c "
        "JOIN pg_class t ON t.oid = c.conrelid "
        "JOIN unnest(c.conkey) k(attnum) ON true "
        "JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum "
        "WHERE c.contype='f' AND t.relname='ai_request_logs' ORDER BY 1"
    ))
    assert cols == ["model_id", "provider_id"]


def test_t17_p08_has_no_forward_fk_to_p09() -> None:
    """T-17 — 0010 contains no FK pointing at P09 tables (P08 -> P09 forward FK = 0)."""
    source = (
        ROOT / "migrations_alembic" / "versions" / "0010_b1_6_ai_gateway.py"
    ).read_text(encoding="utf-8")
    targets = re.findall(r'sa\.ForeignKeyConstraint\(\s*\["\w+"\],\s*\["(\w+)', source)
    assert targets
    assert [t for t in targets if "agent" in t] == []


def test_t18_agent_package_never_touches_the_database() -> None:
    """T-18 — agent/** must not import sqlalchemy / psycopg / infrastructure (STEP 0 skeleton)."""
    import ast

    forbidden = {"sqlalchemy", "psycopg", "psycopg2", "infrastructure", "apps", "intelligence"}
    offenders = []
    for path in (ROOT / "agent").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = {node.module.split(".")[0]}
            else:
                continue
            if roots & forbidden:
                offenders.append((str(path), sorted(roots & forbidden)))
    assert offenders == []


# ===================================================== T-26 (historical protection)
def test_t26_0008_is_untouched() -> None:
    """T-26 — D-P09-17 = A: 0008 is append-only and must not change."""
    path = ROOT / "migrations_alembic" / "versions" / "0008_b1_5_tool_registry.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest.startswith("8b29cc23a93e2058")


# ===================================================== T-31 / T-32
def test_t31_retention_anchor_present_and_no_executor(db) -> None:
    """T-31 — U-1: created_at is the retention anchor; no executor object is delivered."""
    assert _scalar(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name='tool_executions' AND column_name='created_at'"
    ) == "NO"
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE indexname='ix_texec_tenant_created'"
    ) == 1
    # no scheduler / job / extension machinery
    assert _scalar("SELECT count(*) FROM pg_extension WHERE extname IN ('pg_cron','pg_partman')") == 0
    job_objects = _rows(
        "SELECT relname FROM pg_class WHERE relname ~ '(job|schedule|retention|purge)'"
    )
    assert job_objects == []
    # tools for tracking retention state must not have been added
    assert _scalar(
        "SELECT count(*) FROM information_schema.columns WHERE table_name='tool_executions' "
        "AND column_name ~ '(purge|delete|expire|retention)'"
    ) == 0


def test_t32_deferred_fk_is_not_deferrable(db) -> None:
    """T-32 — ND-B = FROZEN AS NON-DEFERRABLE."""
    row = _rows(
        "SELECT condeferrable, condeferred FROM pg_constraint "
        "WHERE conname='fk_agents_current_version' AND contype='f'"
    )
    assert len(row) == 1
    assert row[0][0] is False
    assert row[0][1] is False


# ===================================================== T-33 (downgrade)
def test_t33_downgrade_leaves_zero_residual() -> None:
    """T-33 — downgrade removes every P09 object, then re-upgrade restores it."""
    reset_test_database()
    cfg = make_config(lock_mode="fail")
    upgrade(cfg, "head")
    assert current_revision() == "0015_p12_indexes"

    downgrade(cfg, "0010_b1_6_ai_gateway")
    assert current_revision() == "0010_b1_6_ai_gateway"
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert not (tables & P09_TABLES)
    indexes = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND indexname = ANY(:n)",
        n=sorted(P09_INDEX_OBJECTS),
    )}
    assert indexes == set()
    functions = {r[0] for r in _rows(
        "SELECT proname FROM pg_proc WHERE proname = ANY(:n)", n=sorted(P09_FUNCTIONS)
    )}
    assert functions == set()
    triggers = {
        (r[0], r[1])
        for r in _rows(
            "SELECT t.tgname, t.tgrelid::regclass::text FROM pg_trigger t "
            "JOIN pg_class c ON c.oid = t.tgrelid "
            "WHERE NOT t.tgisinternal AND t.tgname = ANY(:n) AND c.relname = ANY(:tbl)",
            n=sorted(P09_TRIGGERS), tbl=list(P09_TABLES),
        )
    }
    assert triggers == set()
    # B1-5 keeps its own same-named trigger on tool_versions (D-B15-03 shared name)
    assert _scalar(
        "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
        "WHERE NOT t.tgisinternal AND t.tgname = 'tg_version_immutable' "
        "AND c.relname = 'tool_versions'"
    ) == 1
    # other revisions' objects survive (B1-5 baseline spot-check)
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='enforce_tool_versions_immutable'") == 1

    # re-upgrade roundtrip
    upgrade(cfg, "head")
    assert current_revision() == "0015_p12_indexes"
    reset_test_database()
