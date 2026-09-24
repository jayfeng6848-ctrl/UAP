"""B1-6 AI Gateway (P08) — schema, FK/delete rules, constraints, indexes, triggers,
partition, seed, guard and migration.

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).

Covers the frozen B1-6 decisions (canonical TEST_MATRIX = 38):
  * D-B16-01 = A  B1-6 = P08 AI Gateway
  * D-B16-02 = A  ai_routes / ai_policies tenant_id + space_id -> tenants / spaces
                  **ON DELETE RESTRICT**（四列均 nullable）
  * D-B16-03 = A  ai_request_logs.provider_id -> ai_providers.id RESTRICT
                  ai_request_logs.model_id    -> ai_models.id     RESTRICT
                  **agent_id / actor_id / tenant_id / space_id 一律无 FK**
                  ⇒ P08 -> P09 forward FK = 0
  * D-B16-04 = A  ai_request_logs.status **无 CHECK**（S5 EXEMPT / NOT APPLICABLE）
  * D-B16-05 = A  ai_request_logs = 分区父表 + **当月子分区**
  * D-B16-06 = A  ai_providers.adapter = opaque text（无 CK/UQ/FK，不构成执行入口）
  * D-B16-07 = A  UNIQUE CONSTRAINT = 2 · UNIQUE INDEX = 2（表达式唯一不计入 constraint）
  * D-B16-08 = C  agents.current_version_id deferred FK 属 **P09**（不在本阶段）
  * D-B16-09 = A  9 份文档模式
  * D-B16-10 = A  独立编号空间 canonical matrix（S5 豁免已登记）
  * D-B16-11 = A  ai_providers = 平台级 ROOT / 无 tenant_id / 零 seed
  * D-1  = B      ai_policies 的 budget_daily_usd >= 0 / latency_budget_ms >= 0 **不实现**
  * D-2  = B      ix_aimodels_capability **不建立**
  * T-1  = DEFERRED（不建、不改 B0、不作废）
  * D-3  = D      分区维护 = **手工运维**（无 job / scheduler / pg_partman / 扩展）
  * D-4  = A      ai_request_logs 列名 = prompt_tokens + completion_tokens
  * DC-1 = A      子分区命名 = ai_request_logs_<YYYYMM>（UTC calendar month）

Out of scope (must NOT exist): agents, agent_versions, agent_permissions,
tool_executions, events, audit_logs, resource_relations, groups, G/H/I/J ACL triggers,
RLS, Authorization evaluation, provider adapter runtime, partition automation.

Canonical mapping (TEST_MATRIX): AS1-AS6 · AF1-AF5 · AC1-AC8 · AX1-AX2 · AT1-AT2 ·
AP1-AP3 · AE1 · AG1-AG4 · AM1-AM6 · AD1  ->  38.
"""

from __future__ import annotations

import ast
import pathlib
import re
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.integration.alembic_testkit import (
    BASE_DSN,
    ROOT,
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

REVISION = "0010_b1_6_ai_gateway"
# 当前链 head（STAGE 2 / 0012）——head 断言用；REVISION 仅用于 B1-6 自身身份校验。
HEAD_REVISION = "0012_authz_enforcement"
PREVIOUS_REVISION = "0009_timestamp_precision"
MIGRATION_FILE = ROOT / "migrations_alembic" / "versions" / f"{REVISION}.py"
PARENT = "ai_request_logs"
CHILD_PREFIX = "ai_request_logs_"
PLATFORM_PRECISION = 3

AI_TABLES = {
    "ai_providers", "ai_models", "ai_routes", "ai_policies", "ai_request_logs",
}
AI_TRIGGERS = {
    "tg_ai_providers_set_updated_at",
    "tg_ai_models_set_updated_at",
    "tg_ai_routes_set_updated_at",
    "tg_ai_policies_set_updated_at",
}
AI_INDEXES = {
    "uq_ai_providers_key",
    "uq_ai_models",
    "uq_ai_routes",
    "uq_ai_policies",
    "ix_airl_tenant_occurred",
}
# 固定 5 个 ai_* 表上的期望对象（不含分区子表）
AI_PK_COLUMNS = {
    "ai_providers": ["id"],
    "ai_models": ["id"],
    "ai_routes": ["id"],
    "ai_policies": ["id"],
    "ai_request_logs": ["id", "occurred_at"],
}
AI_FK_DELETE_RULES = {
    "fk_ai_models_provider": "c",            # CASCADE（技术子实体：模型目录随 provider purge）
    "fk_ai_routes_primary_model": "r",       # RESTRICT
    "fk_ai_routes_tenant": "r",              # RESTRICT  ← D-B16-02
    "fk_ai_routes_space": "r",               # RESTRICT  ← D-B16-02
    "fk_ai_policies_tenant": "r",            # RESTRICT  ← D-B16-02
    "fk_ai_policies_space": "r",             # RESTRICT  ← D-B16-02
    "fk_ai_request_logs_provider": "r",      # RESTRICT  ← D-B16-03
    "fk_ai_request_logs_model": "r",         # RESTRICT  ← D-B16-03
}
AI_CHECK_CONSTRAINTS = {
    "ck_ai_providers_privacy_tier",
    "ck_ai_providers_max_classification",
    "ck_ai_providers_health_status",
    "ck_ai_models_max_classification",
    "ck_ai_models_context_window",
    "ck_ai_routes_capability",
    "ck_ai_routes_priority",
    "ck_ai_policies_no_unguarded_fallback",
}
AI_COLUMN_COUNTS = {
    "ai_providers": 15,
    "ai_models": 15,
    "ai_routes": 10,
    "ai_policies": 16,
    "ai_request_logs": 17,
}
AI_NN_COLUMNS = {
    "ai_providers": {"id", "key", "adapter", "enabled", "health_status",
                     "privacy_tier", "max_classification", "created_at", "updated_at"},
    "ai_models": {"id", "provider_id", "model_key", "context_window",
                  "max_classification", "is_private", "enabled",
                  "created_at", "updated_at"},
    "ai_routes": {"id", "capability", "priority", "primary_model_id", "enabled",
                  "created_at", "updated_at"},
    "ai_policies": {"id", "name", "max_classification", "require_private",
                    "allow_fallback", "fallback_preserves_classification",
                    "enabled", "created_at", "updated_at"},
    "ai_request_logs": {"id", "occurred_at", "capability", "classification", "status"},
}
FORBIDDEN_TABLES = {
    # P09 (agents / agent_versions / agent_permissions / tool_executions) was delivered by 0011
    # and is therefore no longer forbidden.
    "events", "audit_logs", "resource_relations", "groups",
}

P09_TABLES = {"agents", "agent_versions", "agent_permissions", "tool_executions"}
# D-B16-04：本表 status 无词表；测试夹具使用**中性字面值**，不构成任何 schema vocabulary
_FIXTURE_STATUS = "fixture_note_checked"
_NIL_UUID = "00000000-0000-0000-0000-000000000000"


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #
@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == HEAD_REVISION
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


def _fresh_tenant(conn, slug: str = "b16") -> str:
    return conn.execute(
        sa.text("INSERT INTO tenants (slug, display_name, status) "
                "VALUES (:s, :s, 'active') RETURNING id"),
        {"s": slug},
    ).scalar()


def _fresh_space(conn, tenant_id: str, key: str = "b16") -> str:
    return conn.execute(
        sa.text("INSERT INTO spaces (tenant_id, key, name, kind, visibility, status) "
                "VALUES (:t, :k, :k, 'work', 'private', 'active') RETURNING id"),
        {"t": tenant_id, "k": key},
    ).scalar()


def _fresh_provider(conn, key: str = "p1", **over) -> str:
    values = {
        "key": key, "adapter": "openai_compatible", "enabled": True,
        "health_status": "unknown", "privacy_tier": "public",
        "max_classification": "PUBLIC",
    }
    values.update(over)
    cols = ", ".join(values)
    binds = ", ".join(f":{k}" for k in values)
    return conn.execute(
        sa.text(f"INSERT INTO ai_providers ({cols}) VALUES ({binds}) RETURNING id"), values
    ).scalar()


def _fresh_model(conn, provider_id: str, key: str = "m1", **over) -> str:
    values = {"provider_id": provider_id, "model_key": key, "context_window": 8192,
              "max_classification": "PUBLIC", "is_private": False, "enabled": True}
    values.update(over)
    cols = ", ".join(values)
    binds = ", ".join(f":{k}" for k in values)
    return conn.execute(
        sa.text(f"INSERT INTO ai_models ({cols}) VALUES ({binds}) RETURNING id"), values
    ).scalar()


def _fresh_route(conn, model_id: str, capability: str = "chat", priority: int = 0,
                 tenant_id=None, space_id=None) -> str:
    return conn.execute(
        sa.text("INSERT INTO ai_routes "
                "(tenant_id, space_id, capability, priority, primary_model_id, enabled) "
                "VALUES (:t, :s, :c, :p, :m, true) RETURNING id"),
        {"t": tenant_id, "s": space_id, "c": capability, "p": priority, "m": model_id},
    ).scalar()


def _fresh_policy(conn, name: str = "pol", tenant_id=None, space_id=None, **over) -> str:
    values = {"tenant_id": tenant_id, "space_id": space_id, "name": name,
              "max_classification": "PUBLIC", "require_private": False,
              "allow_fallback": True, "enabled": True}
    values.update(over)
    cols = ", ".join(values)
    binds = ", ".join(f":{k}" for k in values)
    return conn.execute(
        sa.text(f"INSERT INTO ai_policies ({cols}) VALUES ({binds}) RETURNING id"), values
    ).scalar()


def _fresh_log(conn, **over) -> str:
    values = {"capability": "chat", "classification": "PUBLIC", "status": _FIXTURE_STATUS}
    values.update(over)
    cols = ", ".join(values)
    binds = ", ".join(f":{k}" for k in values)
    return conn.execute(
        sa.text(f"INSERT INTO ai_request_logs ({cols}) VALUES ({binds}) RETURNING id"), values
    ).scalar()


def _children() -> list[str]:
    return [r[0] for r in _rows(
        "SELECT c.relname FROM pg_inherits i "
        "JOIN pg_class c ON c.oid = i.inhrelid "
        "JOIN pg_class p ON p.oid = i.inhparent "
        "WHERE p.relname = :p", p=PARENT,
    )]


def _catalog_snapshot() -> tuple:
    """B1-6 对象快照（roundtrip 比对用）。"""
    return (
        tuple(sorted(r[0] for r in _rows(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name LIKE 'ai\\_%'"))),
        tuple(sorted(r[0] for r in _rows(
            "SELECT conname FROM pg_constraint WHERE conrelid::regclass::text LIKE 'ai\\_%'"))),
        tuple(sorted(r[0] for r in _rows(
            "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
            "AND (tablename LIKE 'ai\\_%' OR indexname LIKE '%ai\\_%')"))),
        tuple(sorted(r[0] for r in _rows(
            "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal "
            "AND tgrelid::regclass::text LIKE 'ai\\_%'"))),
    )


# ============================================================== AS1-AS6 (schema)
def test_as1_tables_exist(db) -> None:
    """AS1 — the five P08 tables exist."""
    tables = {r[0] for r in _rows(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )}
    assert AI_TABLES <= tables, sorted(AI_TABLES - tables)


def test_as2_primary_key_shapes(db) -> None:
    """AS2 — 4 单列 PK + 1 复合 PK `(id, occurred_at)`（分区键进 PK）。"""
    for table, expected in AI_PK_COLUMNS.items():
        cols = [r[0] for r in _rows(
            "SELECT a.attname FROM pg_index i "
            "JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indisprimary AND i.indrelid::regclass::text = :t "
            "ORDER BY array_position(i.indkey, a.attnum)", t=table,
        )]
        assert cols == expected, (table, cols)


def test_as3_column_sets_and_types(db) -> None:
    """AS3 — 逐表列数 15/15/10/16/17 与类型映射（uuid/text/bool/int/numeric/jsonb/timestamptz）。"""
    for table, count in AI_COLUMN_COUNTS.items():
        assert _scalar(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t", t=table
        ) == count, table
    assert _scalar("SELECT count(*) FROM information_schema.columns "
                   "WHERE table_schema='public' AND table_name = ANY(:t)", t=list(AI_TABLES)) == 73
    types = dict(_rows(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='ai_models'"
    ))
    assert types["id"] == "uuid"
    assert types["model_key"] == "text"
    assert types["capabilities"] == "jsonb"
    assert types["context_window"] == "integer"
    assert types["input_price_per_1k"] == "numeric"
    assert types["is_private"] == "boolean"
    assert types["created_at"] == "timestamp with time zone"


def test_as4_timestamp_columns_are_precision_3(db) -> None:
    """AS4 — ai_* 全部时间列为 `timestamp with time zone` 且 `datetime_precision = 3`。"""
    rows = _rows(
        "SELECT table_name, column_name, data_type, datetime_precision "
        "FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name = ANY(:t) AND data_type LIKE 'timestamp%' "
        "ORDER BY table_name, ordinal_position", t=list(AI_TABLES),
    )
    assert len(rows) == 10, rows          # providers 3 + models 2 + routes 2 + policies 2 + logs 1
    bad = [r for r in rows if r[2] != "timestamp with time zone" or r[3] != PLATFORM_PRECISION]
    assert bad == [], bad


def test_as5_nullability_matches_design(db) -> None:
    """AS5 — NOT NULL 集合与冻结设计逐列一致。"""
    for table, expected in AI_NN_COLUMNS.items():
        nn = {r[0] for r in _rows(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND is_nullable='NO'", t=table,
        )}
        assert nn == expected, (table, sorted(nn ^ expected))


def test_as6_ai_providers_has_no_tenant_id(db) -> None:
    """AS6 — `ai_providers` 无 `tenant_id` 列（D-B16-11 = A：平台级 ROOT）。"""
    cols = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='ai_providers'"
    )}
    assert "tenant_id" not in cols
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='f' "
        "AND conrelid::regclass::text='ai_providers'"
    ) == 0


# ====================================================== AF1-AF5 (FK / delete rules)
def test_af1_fk_count_and_delete_rules(db) -> None:
    """AF1 — FK = 8：CASCADE 1（ai_models.provider_id）+ RESTRICT 7。"""
    rows = dict(_rows(
        "SELECT conname, confdeltype FROM pg_constraint WHERE contype='f' "
        "AND conrelid::regclass::text = ANY(:t)", t=list(AI_TABLES),
    ))
    assert rows == AI_FK_DELETE_RULES, rows
    assert _scalar("SELECT count(*) FROM pg_constraint WHERE contype='f' "
                   "AND conrelid::regclass::text = ANY(:t)", t=list(AI_TABLES)) == 8
    assert sum(1 for v in rows.values() if v == "r") == 7
    assert sum(1 for v in rows.values() if v == "c") == 1


def test_af2_restrict_blocks_referenced_deletes(db) -> None:
    """AF2 — RESTRICT：被引用的 tenants / spaces / ai_models / ai_providers 不可删除。"""
    engine = _engine()
    try:
        with engine.connect() as conn:
            tenant = _fresh_tenant(conn, "af2")
            space = _fresh_space(conn, tenant, "af2")
            provider = _fresh_provider(conn, "af2p")
            model = _fresh_model(conn, provider, "af2m")
            _fresh_route(conn, model, tenant_id=tenant, space_id=space)
            _fresh_policy(conn, "af2pol", tenant_id=tenant, space_id=space)
            _fresh_log(conn, provider_id=provider, model_id=model)
            conn.commit()

            for sql, params, table in (
                ("DELETE FROM ai_models WHERE id=:i", {"i": model}, "ai_models"),
                ("DELETE FROM ai_providers WHERE id=:i", {"i": provider}, "ai_providers"),
            ):
                with pytest.raises(sa.exc.IntegrityError):
                    conn.execute(sa.text(sql), params)
                    conn.commit()
                conn.rollback()
                assert _scalar(f"SELECT count(*) FROM {table}") == 1

            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("DELETE FROM tenants WHERE id=:i"), {"i": tenant})
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.IntegrityError):
                conn.execute(sa.text("DELETE FROM spaces WHERE id=:i"), {"i": space})
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM tenants WHERE id=:i", i=tenant) == 1
    finally:
        engine.dispose()


def test_af3_cascade_removes_unreferenced_models(db) -> None:
    """AF3 — CASCADE（唯一 1 条）：无其它引用时，删 provider 连带删其 models。"""
    engine = _engine()
    try:
        with engine.connect() as conn:
            provider = _fresh_provider(conn, "af3p")
            _fresh_model(conn, provider, "af3m1")
            _fresh_model(conn, provider, "af3m2")
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_models") == 2
            conn.execute(sa.text("DELETE FROM ai_providers WHERE id=:i"), {"i": provider})
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_models") == 0
            assert _scalar("SELECT count(*) FROM ai_providers") == 0
    finally:
        engine.dispose()


def test_af4_logs_fk_nullable_but_enforced_when_set(db) -> None:
    """AF4 — `ai_request_logs.provider_id` / `model_id` 可 NULL，非 NULL 时必须存在。"""
    engine = _engine()
    try:
        with engine.connect() as conn:
            _fresh_log(conn)                     # both NULL -> allowed
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_log(conn, provider_id="00000000-0000-0000-0000-0000000000aa")
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_log(conn, model_id="00000000-0000-0000-0000-0000000000bb")
                conn.commit()
            conn.rollback()
            provider = _fresh_provider(conn, "af4p")
            model = _fresh_model(conn, provider, "af4m")
            _fresh_log(conn, provider_id=provider, model_id=model)
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_request_logs") == 2
    finally:
        engine.dispose()


def test_af5_no_fk_on_agent_actor_tenant_space(db) -> None:
    """AF5 — `agent_id` / `actor_id` / `tenant_id` / `space_id` 一律无 FK（P08→P09 = 0）。"""
    cols = [r[0] for r in _rows(
        "SELECT a.attname FROM pg_constraint c "
        "JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) "
        "WHERE c.contype='f' AND c.conrelid::regclass::text='ai_request_logs'"
    )]
    assert sorted(cols) == ["model_id", "provider_id"], cols
    engine = _engine()
    try:
        with engine.connect() as conn:
            # 任意 uuid 可写入（无引用检查）⇒ 不构成 P08 → P09 结构依赖
            _fresh_log(conn, agent_id=_NIL_UUID, actor_id=_NIL_UUID,
                       tenant_id=_NIL_UUID, space_id=_NIL_UUID)
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_request_logs") == 1
    finally:
        engine.dispose()
    # B1-6 的不变量口径（P09 落地后仍然成立）：**P08 → P09 forward FK = 0**，
    # 即没有任何 ai_* 表的外键指向 P09 表（原断言以"agents 表不存在"作等价前提，
    # 该前提在 0011 之后不再适用，改为直接断言依赖方向）。
    assert _scalar(
        "SELECT count(*) FROM pg_constraint c "
        "WHERE c.contype='f' AND c.conrelid::regclass::text LIKE 'ai\\_%' "
        "AND c.confrelid::regclass::text = ANY(:t)", t=sorted(P09_TABLES)
    ) == 0, "P08 -> P09 forward FK must stay 0"


# ========================================================= AC1-AC8 (constraints)
def test_ac1_uq_ai_providers_key_is_unique_constraint(db) -> None:
    """AC1 — `uq_ai_providers_key` 为 UNIQUE CONSTRAINT（contype='u'），纯列。"""
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='u' AND conname='uq_ai_providers_key'"
    ) == 1
    engine = _engine()
    try:
        with engine.connect() as conn:
            _fresh_provider(conn, "dup")
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_provider(conn, "dup")
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_ac2_uq_ai_models_is_unique_constraint(db) -> None:
    """AC2 — `uq_ai_models (provider_id, model_key)` 为 UNIQUE CONSTRAINT，同 provider 内唯一。"""
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='u' AND conname='uq_ai_models'"
    ) == 1
    engine = _engine()
    try:
        with engine.connect() as conn:
            p1 = _fresh_provider(conn, "ac2p1")
            p2 = _fresh_provider(conn, "ac2p2")
            _fresh_model(conn, p1, "same")
            _fresh_model(conn, p2, "same")     # 不同 provider 允许
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_model(conn, p1, "same")
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM ai_models") == 2
    finally:
        engine.dispose()


def test_ac3_uq_ai_routes_is_expression_unique_index(db) -> None:
    """AC3 — `uq_ai_routes` 为表达式唯一**索引**（COALESCE），**不得**计为 UNIQUE CONSTRAINT。"""
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND indexname='uq_ai_routes'"
    ) == 1
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='u' AND conname='uq_ai_routes'"
    ) == 0
    engine = _engine()
    try:
        with engine.connect() as conn:
            provider = _fresh_provider(conn, "ac3p")
            model = _fresh_model(conn, provider, "ac3m")
            _fresh_route(conn, model, "chat", 0)                       # (NULL, NULL)
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):                 # 同一 COALESCE 键
                _fresh_route(conn, model, "chat", 0)
                conn.commit()
            conn.rollback()
            # 不同 capability / priority 允许
            _fresh_route(conn, model, "chat", 1)
            _fresh_route(conn, model, "embeddings", 0)
            conn.commit()
            # NULL tenant/space 与显式 nil-uuid 在 COALESCE 下等价 ⇒ 冲突
            # （先建 id = nil-uuid 的合法租户，使 FK 通过，从而只暴露唯一性语义）
            conn.execute(sa.text(
                "INSERT INTO tenants (id, slug, display_name, status) "
                "VALUES (:i, 'nil-uuid', 'NIL', 'active')"), {"i": _NIL_UUID})
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_route(conn, model, "chat", 0, tenant_id=_NIL_UUID)
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM ai_routes") == 3
    finally:
        engine.dispose()


def test_ac4_uq_ai_policies_is_expression_unique_index(db) -> None:
    """AC4 — `uq_ai_policies` 为表达式唯一索引（含 `lower(name)`），不计入 constraint。"""
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND indexname='uq_ai_policies'"
    ) == 1
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='u' AND conname='uq_ai_policies'"
    ) == 0
    engine = _engine()
    try:
        with engine.connect() as conn:
            _fresh_policy(conn, "PolicyA")
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):     # lower(name) 等价
                _fresh_policy(conn, "policya")
                conn.commit()
            conn.rollback()
            assert _scalar("SELECT count(*) FROM ai_policies") == 1
    finally:
        engine.dispose()


def test_ac5_ai_providers_checks(db) -> None:
    """AC5 — `ai_providers` CK ×3 生效（privacy_tier / max_classification / health_status）。"""
    engine = _engine()
    try:
        with engine.connect() as conn:
            for col, value in (("privacy_tier", "nope"),
                               ("max_classification", "SECRET"),
                               ("health_status", "sick")):
                with pytest.raises(sa.exc.IntegrityError):
                    _fresh_provider(conn, f"ac5{col}", **{col: value})
                    conn.commit()
                conn.rollback()
            _fresh_provider(conn, "ac5ok")
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_providers") == 1
    finally:
        engine.dispose()


def test_ac6_ai_models_checks(db) -> None:
    """AC6 — `ai_models` CK ×2 生效（max_classification 词表；context_window > 0）。"""
    engine = _engine()
    try:
        with engine.connect() as conn:
            provider = _fresh_provider(conn, "ac6p")
            conn.commit()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_model(conn, provider, "bad", max_classification="SECRET")
                conn.commit()
            conn.rollback()
            for bad_window in (0, -1):
                with pytest.raises(sa.exc.IntegrityError):
                    _fresh_model(conn, provider, f"w{bad_window}", context_window=bad_window)
                    conn.commit()
                conn.rollback()
            _fresh_model(conn, provider, "good")
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_models") == 1
    finally:
        engine.dispose()


def test_ac7_ai_routes_checks(db) -> None:
    """AC7 — `ai_routes` CK ×2 生效（capability 7 值词表；priority >= 0）。"""
    engine = _engine()
    try:
        with engine.connect() as conn:
            provider = _fresh_provider(conn, "ac7p")
            model = _fresh_model(conn, provider, "ac7m")
            conn.commit()
            allowed = ("chat", "embeddings", "rerank", "vision",
                       "audio_asr", "audio_tts", "moderation")
            for i, cap in enumerate(allowed):
                _fresh_route(conn, model, cap, i)
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_routes") == 7
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_route(conn, model, "not_a_capability", 0)
                conn.commit()
            conn.rollback()
            with pytest.raises(sa.exc.IntegrityError):
                _fresh_route(conn, model, "chat", -1)
                conn.commit()
            conn.rollback()
    finally:
        engine.dispose()


def test_ac8_ai_request_logs_has_no_check(db) -> None:
    """AC8 — `ai_request_logs` CK 计数 = 0；任意 status 值可写入（S5 豁免）。"""
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='c' "
        "AND conrelid::regclass::text='ai_request_logs'"
    ) == 0
    engine = _engine()
    try:
        with engine.connect() as conn:
            for status in (_FIXTURE_STATUS, "", "任意值", "STATUS_OUTSIDE_ANY_VOCABULARY"):
                _fresh_log(conn, status=status)
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_request_logs") == 4
    finally:
        engine.dispose()


# ============================================================= AX1-AX2 (indexes)
def test_ax1_ix_airl_tenant_occurred_on_parent(db) -> None:
    """AX1 — `ix_airl_tenant_occurred` 建在**父表**并下推至当月子分区。"""
    ddl = _scalar(
        "SELECT indexdef FROM pg_indexes WHERE schemaname='public' "
        "AND indexname='ix_airl_tenant_occurred'"
    )
    assert ddl is not None and "tenant_id" in ddl and "occurred_at DESC" in ddl, ddl
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename=:t", t=PARENT
    ) >= 1
    for child in _children():
        assert _scalar(
            "SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename=:t", t=child
        ) >= 1, f"index not pushed down to {child}"


def test_ax2_non_pk_index_set_is_five(db) -> None:
    """AX2 — 非 PK 索引集合 = 5（含 2 个由 UNIQUE CONSTRAINT 隐式建立）。"""
    got = {r[0] for r in _rows(
        "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
        "AND tablename = ANY(:t) AND indexname NOT LIKE '%_pkey'", t=list(AI_TABLES),
    )}
    assert got == AI_INDEXES, got
    # D-2 = B（FROZEN）：不建立 ix_aimodels_capability
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE indexname='ix_aimodels_capability'"
    ) == 0


# ============================================================ AT1-AT2 (triggers)
def test_at1_four_updated_at_triggers(db) -> None:
    """AT1 — 4 个 `tg_ai_*_set_updated_at`（BEFORE UPDATE ROW）复用 set_updated_at()。"""
    rows = dict(_rows(
        "SELECT tgname, tgtype FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid::regclass::text = ANY(:t)", t=list(AI_TABLES),
    ))
    assert set(rows) == AI_TRIGGERS, rows
    assert set(rows.values()) == {19}, rows          # ROW | BEFORE | UPDATE
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1


def test_at2_logs_has_no_trigger_and_updated_at_is_maintained(db) -> None:
    """AT2 — `ai_request_logs` 无 trigger（无 updated_at）；其余 4 表 updated_at 由 trigger 维护。"""
    assert _scalar(
        "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
        "AND tgrelid::regclass::text='ai_request_logs'"
    ) == 0
    columns = {r[0] for r in _rows(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='ai_request_logs'"
    )}
    assert "updated_at" not in columns
    engine = _engine()
    try:
        with engine.connect() as conn:
            provider = _fresh_provider(conn, "at2p")
            conn.commit()
            before = _scalar("SELECT updated_at FROM ai_providers WHERE id=:i", i=provider)
            conn.execute(sa.text(
                "UPDATE ai_providers SET display_name='touched' WHERE id=:i"), {"i": provider})
            conn.commit()
            after = _scalar("SELECT updated_at FROM ai_providers WHERE id=:i", i=provider)
            assert after >= before
            assert _scalar(
                "SELECT display_name FROM ai_providers WHERE id=:i", i=provider
            ) == "touched"
    finally:
        engine.dispose()


# =========================================================== AP1-AP3 (partition)
def test_ap1_parent_is_partitioned_by_range_occurred_at(db) -> None:
    """AP1 — `ai_request_logs` 为分区父表：relkind='p'，RANGE (occurred_at)。"""
    assert _scalar("SELECT relkind FROM pg_class WHERE relname=:t", t=PARENT) == "p"
    key = [r[0] for r in _rows(
        "SELECT a.attname FROM pg_partitioned_table pt "
        "JOIN pg_attribute a ON a.attrelid = pt.partrelid AND a.attnum = ANY(pt.partattrs) "
        "WHERE pt.partrelid::regclass::text = :t", t=PARENT,
    )]
    assert key == ["occurred_at"], key
    strategy = _scalar(
        "SELECT partstrat FROM pg_partitioned_table WHERE partrelid::regclass::text=:t", t=PARENT
    )
    assert strategy == "r"


def test_ap2_current_month_child_exists_and_inherits_pk(db) -> None:
    """AP2 — 当月子分区存在、命名符合 `ai_request_logs_<YYYYMM>`、继承 PK。"""
    children = _children()
    assert len(children) == 1, children
    child = children[0]
    expected = f"{CHILD_PREFIX}{datetime.now(timezone.utc).strftime('%Y%m')}"
    assert child == expected, (child, expected)
    pk_cols = [r[0] for r in _rows(
        "SELECT a.attname FROM pg_index i "
        "JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum = ANY(i.indkey) "
        "WHERE i.indisprimary AND i.indrelid::regclass::text = :t "
        "ORDER BY array_position(i.indkey, a.attnum)", t=child,
    )]
    assert pk_cols == ["id", "occurred_at"], pk_cols


def test_ap3_bounds_are_utc_calendar_month(db) -> None:
    """AP3 — 分区键边界 = UTC calendar month；向父表 INSERT 路由至当月子分区。"""
    child = _children()[0]
    bound = _scalar("SELECT pg_get_expr(relpartbound, oid) FROM pg_class WHERE relname=:t",
                    t=child)
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    nxt = (start.replace(year=start.year + 1, month=1) if start.month == 12
           else start.replace(month=start.month + 1))
    assert start.strftime("%Y-%m-%d %H:%M:%S") in bound, bound
    assert nxt.strftime("%Y-%m-%d %H:%M:%S") in bound, bound
    assert bound.startswith("FOR VALUES FROM"), bound
    engine = _engine()
    try:
        with engine.connect() as conn:
            _fresh_log(conn)
            conn.commit()
            routed = _scalar(f"SELECT count(*) FROM {child}")
            assert routed == 1
    finally:
        engine.dispose()


# ===================================================================== AE1 (seed)
def test_ae1_zero_seed_rows(db) -> None:
    """AE1 — 5 张表 seed rows = 0（D-B16-11 = A：零 seed）。"""
    for table in sorted(AI_TABLES):
        assert _scalar(f"SELECT count(*) FROM {table}") == 0, table


# ==================================================== AG1-AG4 (guard / repo)
def test_ag1_no_vendor_sdk_imports_in_core_or_intelligence(db) -> None:
    """AG1 — core / intelligence 不直接 import 厂商 SDK（架构铁律 3）。"""
    vendor = ("openai", "anthropic", "deepseek", "ollama")
    offenders = []
    for base in ("core", "intelligence"):
        for path in pathlib.Path(base).rglob("*.py"):
            src = path.read_text(encoding="utf-8", errors="ignore")
            for line in src.splitlines():
                stripped = line.strip()
                if stripped.startswith(("import ", "from ")) and any(
                    v in stripped for v in vendor
                ):
                    offenders.append(f"{path}:{stripped}")
    assert offenders == [], offenders
    assert current_revision() == HEAD_REVISION


def test_ag2_core_has_no_industry_vocabulary(db) -> None:
    """AG2 — core 无行业词汇（架构铁律 2）。"""
    banned = ("restaurant", "menu", "employee", "company", "entertainment",
              "family", "hospital", "hotel")
    offenders = []
    for path in pathlib.Path("core").rglob("*.py"):
        src = path.read_text(encoding="utf-8", errors="ignore").lower()
        for word in banned:
            if word in src:
                offenders.append(f"{path}:{word}")
    assert offenders == [], offenders


def _forbidden_sets(path: pathlib.Path) -> dict[str, set[str]]:
    """AST 提取模块级 `FORBIDDEN*` / `FUTURE_TABLES` 集合字面量。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.startswith("FORBIDDEN") or name == "FUTURE_TABLES":
                try:
                    found[name] = set(ast.literal_eval(node.value))
                except ValueError:  # pragma: no cover - defensive
                    continue
    return found


def test_ag3_forbidden_sets_synced(db) -> None:
    """AG3 — 既有测试的 FORBIDDEN/FUTURE 集合已移除 ai_* 与 P09 表；保留 P10 及未来名称。"""
    files = (
        "test_identity_schema.py",
        "test_rbac_schema.py",
        "test_resource_acl_schema.py",
        "test_tenant_space_schema.py",
        "test_tool_registry_schema.py",
    )
    for name in files:
        sets = _forbidden_sets(pathlib.Path("tests/integration") / name)
        assert sets, name
        for set_name, values in sets.items():
            assert values.isdisjoint(AI_TABLES), (name, set_name, sorted(values & AI_TABLES))
            assert values.isdisjoint(P09_TABLES), (name, set_name, sorted(values & P09_TABLES))
    # 平台 guard 的 head 常量同步
    guard = pathlib.Path("tests/integration/test_platform_timestamp_precision.py").read_text(
        encoding="utf-8")
    assert 'CURRENT_HEAD = "0012_authz_enforcement"' in guard


def test_ag4_repository_safety(db) -> None:
    """AG4 — 0010 存在且 down_revision = 0009；formal uap 表数 = 0（未在正式库执行）。"""
    assert MIGRATION_FILE.exists()
    module = _load_migration()
    assert module.down_revision == PREVIOUS_REVISION
    assert MIGRATION_FILE.stem == REVISION
    # 正式库未被触碰（只读 SELECT；连接不可达时跳过该断言）
    try:
        engine = sa.create_engine("postgresql+psycopg://uap:uap@localhost:5432/uap")
    except Exception:  # pragma: no cover - defensive
        pytest.skip("formal uap database unreachable")
    try:
        with engine.connect() as conn:
            count = conn.execute(sa.text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog','information_schema')"
            )).scalar()
            assert count == 0, f"formal uap must stay empty, found {count} tables"
    finally:
        engine.dispose()


def _load_migration():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_m0010", MIGRATION_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ========================================================= AM1-AM6 (migration)
def test_am1_revision_metadata() -> None:
    """AM1 — 0010 元信息：down_revision = 0009；revision 长度 ≤ 32；filename == revision。"""
    assert MIGRATION_FILE.exists(), MIGRATION_FILE
    tree = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    assigned = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                assigned[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    assert assigned["revision"] == REVISION
    assert assigned["down_revision"] == PREVIOUS_REVISION
    assert assigned["branch_labels"] is None
    assert assigned["depends_on"] is None
    assert len(REVISION) <= 32, len(REVISION)
    assert MIGRATION_FILE.stem == REVISION


def test_am2_upgrade_order(db) -> None:
    """AM2 — upgrade 顺序：providers → models → routes → policies → 父表 → 子分区 → 索引 → trigger。"""
    cfg = make_config(lock_mode="fail")
    reset_test_database()
    upgrade(cfg, PREVIOUS_REVISION)
    assert current_revision() == PREVIOUS_REVISION
    assert _scalar(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name = ANY(:t)", t=list(AI_TABLES)
    ) == 0
    upgrade(cfg, "head")
    assert current_revision() == HEAD_REVISION
    assert _scalar(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name = ANY(:t)", t=list(AI_TABLES)
    ) == 5
    assert len(_children()) == 1
    # 源码顺序核对（与冻结 MIGRATION_PLAN §3 一致）
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    order = [
        '"ai_providers",\n        sa.Column("id"',
        '"ai_models",\n        sa.Column("id"',
        '"ai_routes",\n        sa.Column("id"',
        '"ai_policies",\n        sa.Column("id"',
        "_PARENT,\n        sa.Column",
        "PARTITION OF",
        "CREATE UNIQUE INDEX uq_ai_routes",
        "CREATE UNIQUE INDEX uq_ai_policies",
        "CREATE INDEX ix_airl_tenant_occurred",
        "CREATE TRIGGER tg_{table}_set_updated_at",
    ]
    positions = [src.index(token) for token in order]
    assert positions == sorted(positions), list(zip(order, positions))


def test_am3_downgrade_leaves_no_residue(db) -> None:
    """AM3 — downgrade 逆序无 orphan：先子分区后父表；B1-6 对象残留 = 0。"""
    cfg = make_config(lock_mode="fail")
    downgrade(cfg, PREVIOUS_REVISION)
    assert current_revision() == PREVIOUS_REVISION
    assert _children() == []
    assert _scalar(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name LIKE 'ai\\_%'"
    ) == 0
    assert _scalar(
        "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgname = ANY(:n)",
        n=list(AI_TRIGGERS)
    ) == 0
    assert _scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND indexname = ANY(:n)",
        n=list(AI_INDEXES)
    ) == 0
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE conname = ANY(:n)",
        n=list(AI_FK_DELETE_RULES) + list(AI_CHECK_CONSTRAINTS)
    ) == 0
    # 既有对象完好
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='uap_uuid_v7'") == 1
    assert _scalar("SELECT count(*) FROM information_schema.tables "
                   "WHERE table_name='tools'") == 1
    upgrade(cfg, "head")


def test_am4_roundtrip_object_set_stable(db) -> None:
    """AM4 — upgrade → downgrade → upgrade 三次对象集逐项一致。"""
    cfg = make_config(lock_mode="fail")
    before = _catalog_snapshot()
    downgrade(cfg, PREVIOUS_REVISION)
    assert _catalog_snapshot()[0] == ()
    upgrade(cfg, "head")
    after = _catalog_snapshot()
    assert before == after, (before, after)
    assert current_revision() == HEAD_REVISION


def test_am5_chain_shape() -> None:
    """AM5 — 链长 = 12（0001…0012）· 唯一 head = 0012 · 无重复/缺失/分支。"""
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    heads = script.get_heads()
    assert heads == [HEAD_REVISION], heads
    revisions = list(script.walk_revisions())
    assert len(revisions) == 12, [r.revision for r in revisions]
    ids = [r.revision for r in revisions]
    assert len(ids) == len(set(ids))
    assert ids[0] == HEAD_REVISION and ids[-1] == "0001_baseline"
    revision = next(r for r in revisions if r.revision == HEAD_REVISION)
    # B1-6 的直接后继必须仍指向 0010（不随 head 推进而失效——原断言写死了
    # ``head.down_revision == REVISION``，在 head 为 0011 时成立、0012 时失效，
    # 属 §24 分类 2「Test Expectation Defect」）
    successor = next(r for r in revisions if r.down_revision == REVISION)
    assert successor.revision == "0011_p09_agent_tool_permission"
    assert revision.down_revision == "0011_p09_agent_tool_permission"   # 0012 → 0011
    parent = next(r for r in revisions if r.revision == REVISION)
    assert parent.down_revision == PREVIOUS_REVISION   # 0010 → 0009
    # Alembic 将未声明值规范化为空 set（等价于 None）；depends_on 由 AM1 的模块级断言覆盖
    assert not revision.branch_labels
    assert "0009_timestamp_precision" in ids


def test_am6_no_seed_statements() -> None:
    """AM6 — 迁移内无 seed 语句（INSERT 计数 = 0）。"""
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    body = src.split('def upgrade() -> None:', 1)[1]
    assert not re.search(r"\bINSERT\s+INTO\b", body, re.IGNORECASE)
    assert "op.bulk_insert" not in body
    assert not re.search(r"\bCOPY\b", body)


# ================================================== AD1 (decision-derived, S5)
def test_ad1_s5_status_exemption_registered(db) -> None:
    """AD1 — D-B16-04 = A：S5 对 `ai_request_logs.status` **EXEMPT / NOT APPLICABLE**。

    豁免 = **正向断言"该表不存在 status CHECK"**（而非断言存在 CHECK）。
    """
    checks = [r[0] for r in _rows(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE contype='c' AND conrelid::regclass::text='ai_request_logs'"
    )]
    assert checks == [], checks
    # 且 ai_* 内不存在针对**列名 status**的取值域 CHECK（`health_status` 不匹配，用词边界）
    vocab = _scalar(
        "SELECT count(*) FROM pg_constraint WHERE contype='c' "
        r"AND pg_get_constraintdef(oid) ~ '\ystatus\y' "
        "AND conrelid::regclass::text LIKE 'ai\\_%'"
    )
    assert vocab == 0
    engine = _engine()
    try:
        with engine.connect() as conn:
            _fresh_log(conn, status="EXEMPT_PROBE")
            conn.commit()
            assert _scalar("SELECT count(*) FROM ai_request_logs") == 1
    finally:
        engine.dispose()
