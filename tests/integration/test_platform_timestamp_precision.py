"""Platform timestamp precision guard — frozen rule `timestamptz(3)`.

Platform rule (not B1-5-local):
  * ``STEP1A_DESIGN_REPORT.md §12 时间策略`` — 精度 ``timestamptz(3)``
  * ``CORE_DOMAIN_MODEL.md §10 时间策略`` — "精度 | ``timestamptz(3)``（毫秒）"

Corrected platform-wide by the corrective migration
``0009_timestamp_precision`` (20 tables / 72 columns), which is **not**
a business phase. Historical migrations 0001–0008 are untouched.

What this file guards (platform-wide, hence separate from the B1-5 suite):
  * PG1  UAP 范围内禁止 `timestamp without time zone`
  * PG2  UAP 全部时间列 `datetime_precision = 3`
  * PG3  覆盖集合 = 0009 清单（20 表 / 72 列）∪ P08（5 表 / 10 列）∪ P09（4 表 / 9 列）
  * PG4  0009 是 corrective migration（`down_revision = 0008`），不与业务 Phase 混编
  * PG5  校正未新增/删除任何业务表对象（表数不变）
  * PG6  校正未丢对象：依赖时间列的 CHECK / 部分索引 / trigger / function 完好
  * PG7  downgrade → precision 6，re-upgrade → precision 3（双向可执行）

Runs against the disposable ``uap_b1_test`` database only (never ``uap``).
"""

from __future__ import annotations

import importlib.util
import pathlib

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

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PREVIOUS_REVISION = "0008_b1_5_tool_registry"
CORRECTIVE_REVISION = "0009_timestamp_precision"
PLATFORM_PRECISION = 3
LEGACY_PRECISION = 6

# Platform scope at P10 (0013_p10_event_audit).
#   20 business tables @P07 + 5 AI gateway + 4 P09 = 29 business tables
#   + 2 P10 tables (events / audit_logs) = 31 business tables
#   + 3 当月子分区（ai_request_logs_ / events_ / audit_logs_ <YYYYMM>） = 34 public tables
#   + alembic_version = 35 physical tables
BUSINESS_TABLES = 34
PHYSICAL_TABLES = 35

# Current chain head（本文件只断言 head 常量，不假设具体业务阶段）。
# P10 (0013_p10_event_audit) 新增 2 张分区父表 / 8 个 timestamptz(3) 列 ⇒
# 覆盖集合扩为 0009 清单 ∪ P08 清单 ∪ P09 清单 ∪ P10 清单。
CURRENT_HEAD = "0015_p12_indexes"

# --------------------------------------------------------------------------- #
# P08 (0010_b1_6_ai_gateway) timestamp columns — explicit static list.
#
# 这些列在 0010 中**直接以 timestamptz(3) 创建**（`postgresql.TIMESTAMP(precision=3)`）；
# 0009 的静态清单（20 表 / 72 列）只覆盖 0003–0008 建立的时间列，**不因 P08 改变**。
# 本 guard 的覆盖集合 = 0009 清单 ∪ P08 清单 ⇒ 平台内不存在"清单外"时间列。
# --------------------------------------------------------------------------- #
P08_TIMESTAMP_COLUMNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ai_providers", ("health_checked_at", "created_at", "updated_at")),
    ("ai_models", ("created_at", "updated_at")),
    ("ai_routes", ("created_at", "updated_at")),
    ("ai_policies", ("created_at", "updated_at")),
    ("ai_request_logs", ("occurred_at",)),
)
P08_TABLES = 5
P08_PAIRS = 10

# --------------------------------------------------------------------------- #
# P09 (0011_p09_agent_tool_permission) timestamp columns — explicit static list.
#
# 这些列在 0011 中同样**直接以 timestamptz(3) 创建**；0009 的清单不因 P09 改变。
# --------------------------------------------------------------------------- #
P09_TIMESTAMP_COLUMNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("agents", ("created_at", "updated_at", "archived_at")),
    ("agent_versions", ("created_at", "published_at")),
    ("agent_permissions", ("created_at",)),
    ("tool_executions", ("started_at", "finished_at", "created_at")),
)
P09_TABLES = 4
P09_PAIRS = 9

# --------------------------------------------------------------------------- #
# P10 (0013_p10_event_audit) timestamp columns — explicit static list.
#
# 这两张表在 0013 中直接以 timestamptz(3) 创建；0009 的清单不因 P10 改变。
#   events     : created_at + occurred_at（分区键）+ 4 个 outbox 状态列（D-P10-01 一次建齐）
#   audit_logs : created_at + occurred_at（分区键）；无 updated_at / deleted_at（append-only）
# --------------------------------------------------------------------------- #
P10_TIMESTAMP_COLUMNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("events", ("occurred_at", "claimed_at", "lease_expires_at",
                "next_attempt_at", "delivered_at", "created_at")),
    ("audit_logs", ("occurred_at", "created_at")),
)
P10_TABLES = 2
P10_PAIRS = 8

PLATFORM_TABLES = 20 + P08_TABLES + P09_TABLES + P10_TABLES   # 31 张业务表（含分区父表）
PLATFORM_PAIRS = 72 + P08_PAIRS + P09_PAIRS + P10_PAIRS      # 99 个时间列（含 3 个分区键）


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #
@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == CURRENT_HEAD
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


def _migration_module():
    """Load the corrective migration module to reuse its authoritative static list."""
    path = REPO_ROOT / "migrations_alembic" / "versions" / f"{CORRECTIVE_REVISION}.py"
    spec = importlib.util.spec_from_file_location("_m0009", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 时间列扫描：只审计**声明的**平台表，跳过分区子表（分区列按父表继承，
# 在 information_schema 中会重复出现；P08 的 ai_request_logs_<YYYYMM> 即属此类）。
_TS_SCAN = (
    "FROM information_schema.columns c "
    "JOIN pg_class k ON k.relname = c.table_name "
    "JOIN pg_namespace n ON n.oid = k.relnamespace AND n.nspname = c.table_schema "
    "WHERE c.table_schema = 'public' AND c.data_type LIKE 'timestamp%' "
    "AND NOT k.relispartition "
)


def _platform_timestamps():
    """All timestamp columns of the platform (public schema), as (table, column, type, precision)."""
    return _rows(
        "SELECT c.table_name, c.column_name, c.data_type, c.datetime_precision "
        + _TS_SCAN
        + "ORDER BY c.table_name, c.ordinal_position"
    )


# --------------------------------------------------------------------------- #
# PG1 — no `timestamp without time zone` inside UAP
# --------------------------------------------------------------------------- #
def test_pg1_no_timestamp_without_time_zone(db) -> None:
    """PG1 — UAP 范围内禁止 `timestamp without time zone`（CORE §10: 禁用无时区类型）。"""
    offenders = [
        (r[0], r[1]) for r in _platform_timestamps() if r[2] != "timestamp with time zone"
    ]
    assert offenders == [], offenders


# --------------------------------------------------------------------------- #
# PG2 — every platform timestamp column is `timestamptz(3)`
# --------------------------------------------------------------------------- #
def test_pg2_all_platform_timestamps_are_precision_3(db) -> None:
    """PG2 — 平台全部时间列 `datetime_precision = 3`（冻结规则 `timestamptz(3)`）。"""
    rows = _platform_timestamps()
    assert rows, "expected platform timestamp columns"
    bad = [(r[0], r[1], r[2], r[3]) for r in rows if r[3] != PLATFORM_PRECISION]
    assert bad == [], bad
    assert _scalar(
        "SELECT count(*) " + _TS_SCAN
        + f"AND c.datetime_precision = {PLATFORM_PRECISION}"
    ) == len(rows)


# --------------------------------------------------------------------------- #
# PG3 — coverage set: 20 tables / 72 columns, matching the migration's static list
# --------------------------------------------------------------------------- #
def test_pg3_coverage_matches_migration_static_list(db) -> None:
    """PG3 — 覆盖集合 = 0009（20 表 / 72 列）∪ P08（5/10）∪ P09（4/9）∪ P10（2/8）。

    0009 的清单是 historical migration 的产物，**未因 P08 / P09 / P10 改变**；
    0010 / 0011 / 0013 新建的时间列在同一 guard 下逐项登记 ⇒ 无遗漏、无多余。
    """
    module = _migration_module()
    corrective = set(module._pairs())
    assert len(module.TIMESTAMP_COLUMNS) == 20, len(module.TIMESTAMP_COLUMNS)
    assert len(corrective) == 72, len(corrective)

    p08 = {(table, column) for table, columns in P08_TIMESTAMP_COLUMNS for column in columns}
    assert len(P08_TIMESTAMP_COLUMNS) == P08_TABLES, len(P08_TIMESTAMP_COLUMNS)
    assert len(p08) == P08_PAIRS, len(p08)

    p09 = {(table, column) for table, columns in P09_TIMESTAMP_COLUMNS for column in columns}
    assert len(P09_TIMESTAMP_COLUMNS) == P09_TABLES, len(P09_TIMESTAMP_COLUMNS)
    assert len(p09) == P09_PAIRS, len(p09)
    assert p09 == {
        ("agents", "archived_at"), ("agents", "created_at"), ("agents", "updated_at"),
        ("agent_versions", "published_at"), ("agent_versions", "created_at"),
        ("agent_permissions", "created_at"),
        ("tool_executions", "started_at"), ("tool_executions", "finished_at"),
        ("tool_executions", "created_at"),
    }

    p10 = {(table, column) for table, columns in P10_TIMESTAMP_COLUMNS for column in columns}
    assert len(P10_TIMESTAMP_COLUMNS) == P10_TABLES, len(P10_TIMESTAMP_COLUMNS)
    assert len(p10) == P10_PAIRS, len(p10)

    expected = corrective | p08 | p09 | p10
    assert len(expected) == PLATFORM_PAIRS, len(expected)

    catalog = {(r[0], r[1]) for r in _platform_timestamps()}
    assert catalog == expected, {
        "missing_in_catalog": sorted(expected - catalog),
        "extra_in_catalog": sorted(catalog - expected),
    }

    # 反向核对：平台业务表内不存在"清单外"的时间列
    assert _scalar(
        "SELECT count(DISTINCT c.table_name) " + _TS_SCAN
    ) == PLATFORM_TABLES


# --------------------------------------------------------------------------- #
# PG4 — 0009 is a corrective migration, linked to 0008
# --------------------------------------------------------------------------- #
def test_pg4_corrective_migration_linkage() -> None:
    """PG4 — 0009 为 corrective migration：`down_revision = 0008`，且链条可达 head。"""
    module = _migration_module()
    assert module.revision == CORRECTIVE_REVISION
    assert module.down_revision == PREVIOUS_REVISION
    reset_test_database()
    try:
        upgrade(make_config(lock_mode="fail"), "head")
        assert current_revision() == CURRENT_HEAD
    finally:
        reset_test_database()


# --------------------------------------------------------------------------- #
# PG5 — correction did not add/drop business tables
# --------------------------------------------------------------------------- #
def test_pg5_table_count_unchanged(db) -> None:
    """PG5 — head(=P10) 处表集合与冻结阶段一致：业务表 31 + 3 当月子分区 = 34 / 物理 35。

    原断言意图（"0009 未新增表"）由 `PG4` 的链检查与 0010 / 0011 的冻结范围承载；
    此处按当前 head 校准平台表集合（0009 的 corrective 语义未变）。
    """
    tables = {
        r[0]
        for r in _rows(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )
    }
    assert len(tables - {"alembic_version"}) == BUSINESS_TABLES, sorted(tables)
    assert _scalar(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema NOT IN ('pg_catalog','information_schema')"
    ) == PHYSICAL_TABLES


# --------------------------------------------------------------------------- #
# PG6 — correction dropped nothing that depends on those columns
# --------------------------------------------------------------------------- #
def test_pg6_timestamp_dependent_objects_survive(db) -> None:
    """PG6 — 依赖时间列的 CHECK / 部分索引 / trigger / function 全部完好。"""
    # CHECK 引用时间列
    assert _scalar(
        "SELECT count(*) FROM pg_constraint WHERE conname='ck_sessions_expiry'"
    ) == 1
    # 部分索引引用时间列
    indexes = {
        r[0]
        for r in _rows(
            "SELECT indexname FROM pg_indexes WHERE schemaname='public' "
            "AND (indexdef ILIKE '%expires_at%' OR indexdef ILIKE '%removed_at%')"
        )
    }
    assert indexes == {"ix_sessions_expires_active", "uq_memberships"}, indexes
    # trigger / function（精度无关，必须未被重建或丢失）
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='set_updated_at'") == 1
    assert _scalar("SELECT count(*) FROM pg_proc WHERE proname='uap_uuid_v7'") == 1
    # 14 @P07 + 4 @P08（tg_ai_*_set_updated_at）+ 1 @P09（tg_agents_set_updated_at）= 19
    assert _scalar(
        "SELECT count(*) FROM pg_trigger t JOIN pg_proc p ON p.oid = t.tgfoid "
        "WHERE NOT t.tgisinternal AND p.proname = 'set_updated_at'"
    ) == 19
    # UAP trigger 总数：27 @P07 + 4 @P08 + 3 @P09 + 2 @P10 + 4 @P11 = 40。
    # P10 的 tg_audit_immutable 建在**分区父表**上，PG 会为子分区克隆一行
    # （tgparentid 指向父触发器），故 P10 计 2 而非 1；P11 的 4 个触发器
    # 均在非分区表上 ⇒ 无克隆行。
    assert _scalar(
        "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE NOT t.tgisinternal AND n.nspname = 'public'"
    ) == 40
    # 时间列上的 now() 默认：34 @P07 + 9 @P08 + 5 @P09 + 1 @P10（events.created_at；
    # audit_logs.created_at 按契约不加 server default）= 49
    assert _scalar(
        "SELECT count(*) " + _TS_SCAN + "AND c.column_default = 'now()'"
    ) == 49


# --------------------------------------------------------------------------- #
# PG7 — downgrade restores declaration precision; re-upgrade re-applies
# --------------------------------------------------------------------------- #
def test_pg7_downgrade_and_reupgrade_roundtrip() -> None:
    """PG7 — `0009 → 0008` 恢复 precision 6；`0008 → 0009` 再次应用 precision 3。

    NOTE: downgrade 只恢复 **声明精度**；已舍入到毫秒的微秒值不可恢复
    （data-level lossy，见 migration docstring）。
    """
    cfg = make_config(lock_mode="fail")
    reset_test_database()
    try:
        upgrade(cfg, "head")

        def _precisions():
            return {(r[0], r[1]): r[3] for r in _platform_timestamps()}

        assert set(_precisions().values()) == {PLATFORM_PRECISION}

        downgrade(cfg, PREVIOUS_REVISION)
        assert current_revision() == PREVIOUS_REVISION
        after_down = _precisions()
        assert set(after_down.values()) == {LEGACY_PRECISION}, sorted(set(after_down.values()))
        assert len(after_down) == 72

        upgrade(cfg, "head")
        assert current_revision() == CURRENT_HEAD
        assert set(_precisions().values()) == {PLATFORM_PRECISION}
        assert len(_precisions()) == PLATFORM_PAIRS
    finally:
        reset_test_database()
