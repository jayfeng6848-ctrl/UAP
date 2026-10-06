"""P12 implementation tests — canonical index delivery (0015_p12_indexes).

Decision authority: `D-P12-01..15` + `P12_IMPLEMENTATION_CONTRACT.md` §3
(`MEASURE-1` / `GUARD-1` = APPROVED 2026-09-25). 19 new indexes = 12 FK
reverse-lookup + 7 P10 event/audit. `T-1` (`ix_aimodels_capability`) must stay
absent (`D-P12-14`); T-22 retains exactly 5 forbidden names (`GUARD-1`).
"""

from __future__ import annotations

import pathlib
import re

import pytest
import sqlalchemy as sa

from alembic_testkit import (  # noqa: F401
    BASE_DSN, current_revision, downgrade, make_config, reset_test_database, upgrade)

MIGRATION_FILE = pathlib.Path(
    "migrations_alembic/versions/0015_p12_indexes.py"
).resolve()

REVISION = "0015_p12_indexes"
PREVIOUS_REVISION = "0014_p11_triggers"

# (name, table, columns-expression, predicate)
P12_CREATE_SET = {
    # ---- 12 FK reverse-lookup (contract §3.1) ----
    ("ix_ap_permission", "agent_permissions", "permission_id", None),
    ("ix_ap_tool", "agent_permissions", "tool_id", None),
    ("ix_ap_version", "agent_permissions", "version_id", None),
    ("ix_agents_current_version", "agents", "current_version_id", None),
    ("ix_agents_default_route", "agents", "default_route_id", None),
    ("ix_airl_provider", "ai_request_logs", "provider_id", None),
    ("ix_airl_model", "ai_request_logs", "model_id", None),
    ("ix_airoutes_primary_model", "ai_routes", "primary_model_id", None),
    ("ix_texec_tool", "tool_executions", "tool_id", None),
    ("ix_texec_tool_version", "tool_executions", "tool_version_id", None),
    ("ix_tperm_permission", "tool_permissions", "permission_id", None),
    ("ix_tperm_version", "tool_permissions", "version_id", None),
    # ---- 7 P10 event/audit (contract §3.2) ----
    ("ix_events_dispatch", "events", "status, next_attempt_at",
     "status = ANY (ARRAY['pending'::text, 'claimed'::text])"),
    ("ix_events_tenant_type_time", "events",
     "tenant_id, event_type, occurred_at DESC", None),
    ("ix_audit_tenant_time", "audit_logs", "tenant_id, occurred_at DESC", None),
    ("ix_audit_actor_time", "audit_logs", "actor_id, occurred_at DESC", None),
    ("ix_audit_resource", "audit_logs",
     "resource_type, resource_id, occurred_at DESC", None),
    ("ix_audit_correlation", "audit_logs", "correlation_id", None),
    ("ix_audit_risk", "audit_logs", "risk_level, occurred_at",
     "risk_level = ANY (ARRAY['HIGH'::text, 'CRITICAL'::text])"),
}
# T-22 names that P12 delivers (GUARD-1) — removed from the forbidden set
T22_REMOVED = {
    "ix_ap_permission", "ix_ap_tool", "ix_ap_version",
    "ix_agents_current_version", "ix_agents_default_route",
}
# T-22 names that must remain forbidden (NOT part of P12 CREATE set)
T22_RETAINED = {
    "ix_agents_owner", "ix_agents_space", "ix_texec_agent",
    "ix_texec_actor", "ix_agent_versions_published_by",
}
PARTITIONED_PARENTS = {"events", "audit_logs", "ai_request_logs"}


def _engine():
    return sa.create_engine(BASE_DSN)


def _scalar(sql, **params):
    with _engine().connect() as c:
        return c.execute(sa.text(sql), params).scalar()


def _index_map():
    with _engine().connect() as c:
        return {r[0]: (r[1], r[2]) for r in c.execute(sa.text(
            "SELECT indexname, tablename, indexdef FROM pg_indexes "
            "WHERE schemaname = 'public'")).fetchall()}


@pytest.fixture()
def db():
    reset_test_database()
    upgrade(make_config(lock_mode="fail"), "head")
    assert current_revision() == REVISION
    yield
    reset_test_database()


# --------------------------------------------------------------------------- #
# MIG — revision identity / completeness
# --------------------------------------------------------------------------- #
def test_mig1_revision_identity_and_single_head(db) -> None:
    assert MIGRATION_FILE.exists()
    assert MIGRATION_FILE.stem == REVISION
    assert len(REVISION) <= 32
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    assert f'revision = "{REVISION}"' in src
    assert f'down_revision = "{PREVIOUS_REVISION}"' in src
    assert "branch_labels = None" in src and "depends_on = None" in src
    assert current_revision() == REVISION
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(Config(str("alembic.ini")))
    assert script.get_heads() == [REVISION]


def test_mig2_exactly_19_new_indexes_present(db) -> None:
    idx = _index_map()
    names = {n for n, _t, _c, _p in P12_CREATE_SET}
    missing = names - set(idx)
    assert not missing, sorted(missing)
    # and nothing extra was invented: every P12-named index matches the CREATE set
    delivered = {n for n in idx if n in names}
    assert delivered == names


def test_mig3_table_column_and_predicate_match_contract(db) -> None:
    idx = _index_map()
    for name, table, columns, predicate in P12_CREATE_SET:
        assert name in idx, name
        t, ddl = idx[name]
        assert t == table, (name, t)
        norm = re.sub(r"\s+", " ", ddl)
        assert f"USING btree ({columns})" in norm, (name, norm)
        if predicate is None:
            assert " WHERE " not in norm, (name, norm)
        else:
            assert norm.count("WHERE") == 1 and predicate in norm, (name, norm)
        assert norm.startswith("CREATE INDEX"), name  # not UNIQUE


# --------------------------------------------------------------------------- #
# SEC / boundaries
# --------------------------------------------------------------------------- #
def test_t1_hard_ban_ix_aimodels_capability(db) -> None:
    """D-P12-14 — ix_aimodels_capability (and any JSONB capability index) stays absent."""
    idx = _index_map()
    assert "ix_aimodels_capability" not in idx
    assert not [n for n in idx if "aimodels" in n and "capab" in n]


def test_sec_no_concurrently_no_only_no_attach_in_source() -> None:
    """Executable code must not use CONCURRENTLY / ON ONLY / ATTACH PARTITION
    (docstring *mentions* are fine — those are statements about the rule)."""
    src = MIGRATION_FILE.read_text(encoding="utf-8")
    code = src.split('"""')[2] if src.count('"""') >= 2 else src
    for token in ("CONCURRENTLY", "ON ONLY", "ATTACH PARTITION", "ALTER INDEX",
                  "SECURITY DEFINER", "ROW LEVEL SECURITY"):
        assert token not in code, token


def test_boundary_p10_p11_objects_preserved(db) -> None:
    # P10: parent partitioned tables + immutable trigger intact
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                   "AND tgparentid = 0 AND tgname = 'tg_audit_immutable' "
                   "AND tgrelid = 'audit_logs'::regclass") == 1
    assert _scalar("SELECT count(*) FROM information_schema.columns "
                   "WHERE table_name = 'events' AND table_schema = 'public'") == 22
    # P11: 4 canonical triggers intact
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                   "AND tgparentid = 0 AND tgname = ANY(:n)",
                   n=["tg_acl_subject_exists", "tg_acl_user_hard_delete",
                      "tg_acl_role_delete_block", "tg_agent_acl_expire"]) == 4
    # no seed appeared
    assert _scalar("SELECT count(*) FROM acl_subject_types") == 0
    assert _scalar("SELECT count(*) FROM users") == 0


def test_p13_boundary_zero_seed(db) -> None:
    assert "INSERT INTO" not in MIGRATION_FILE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# T-22 / GUARD-1
# --------------------------------------------------------------------------- #
def test_t22_removals_match_gu_evidence(db) -> None:
    """GUARD-1 set algebra: removed ⊆ CREATE set · retained ∩ CREATE = ∅ · exactly 5+5."""
    assert len(T22_REMOVED) == 5 and len(T22_RETAINED) == 5
    create_names = {n for n, _t, _c, _p in P12_CREATE_SET}
    assert T22_REMOVED <= create_names
    assert not (T22_RETAINED & create_names)
    # test file keeps exactly the retained 5 in its forbidden set
    src = pathlib.Path("tests/integration/test_agent_tool_permission_schema.py"
                       ).read_text(encoding="utf-8")
    forbidden_block = re.search(
        r"def test_t22_no_extra_fk_column_indexes.*?forbidden = \{(.*?)\}",
        src, re.S).group(1)
    for name in T22_REMOVED:
        assert f'"{name}"' not in forbidden_block, name
    for name in T22_RETAINED:
        assert f'"{name}"' in forbidden_block, name


def test_t22_retained_forbidden_absent_at_head(db) -> None:
    idx = _index_map()
    assert not (set(idx) & T22_RETAINED), sorted(set(idx) & T22_RETAINED)


def test_three_way_consistency_migration_tests_matrix(db) -> None:
    """migration ↔ tests ↔ acceptance matrix: the 19 names appear verbatim in all three."""
    names = {n for n, _t, _c, _p in P12_CREATE_SET}
    mig = MIGRATION_FILE.read_text(encoding="utf-8")
    tests = pathlib.Path(__file__).read_text(encoding="utf-8")
    matrix = pathlib.Path(
        "docs/architecture/P12_IMPLEMENTATION_ACCEPTANCE_MATRIX.md"
    ).read_text(encoding="utf-8")
    for n in names:
        assert f'"{n}"' in mig, n
        assert f'"{n}"' in tests, n
        assert n in matrix, n


# --------------------------------------------------------------------------- #
# partition behaviour (D-P12-08)
# --------------------------------------------------------------------------- #
def test_partitioned_parent_indexes_propagate(db) -> None:
    """Parent-level creation pushes down to child partitions automatically."""
    p12_partitioned = {"ix_airl_provider", "ix_airl_model",
                       "ix_events_dispatch", "ix_events_tenant_type_time",
                       "ix_audit_tenant_time", "ix_audit_actor_time",
                       "ix_audit_resource", "ix_audit_correlation", "ix_audit_risk"}
    with _engine().connect() as c:
        parents = c.execute(sa.text(
            "SELECT ci.relname FROM pg_index i "
            "JOIN pg_class ct ON ct.oid = i.indrelid "
            "JOIN pg_class ci ON ci.oid = i.indexrelid "
            "WHERE ct.relname = ANY(:t) AND ct.relkind = 'p' "
            "AND ci.relname = ANY(:n)"),
            {"t": sorted(PARTITIONED_PARENTS), "n": sorted(p12_partitioned)}).scalars().fetchall()
        children = c.execute(sa.text(
            "SELECT count(*) FROM pg_index i "
            "JOIN pg_class ct ON ct.oid = i.indrelid "
            "JOIN pg_class ci ON ci.oid = i.indexrelid "
            "JOIN pg_inherits ih ON ih.inhrelid = ct.oid "
            "JOIN pg_class pt ON pt.oid = ih.inhparent "
            "WHERE pt.relname = ANY(:t) "
            "AND ci.relispartition"),
            {"t": sorted(PARTITIONED_PARENTS)}).scalar()
    assert len(parents) == 9, sorted(parents)   # 2 airl + 2 events + 5 audit
    # pre-existing (pkey/ix_airl_tenant_occurred) + 9 P12 = 13 partition-child index rows
    assert children >= 13


# --------------------------------------------------------------------------- #
# existing index protection
# --------------------------------------------------------------------------- #
def test_existing_indexes_not_dropped(db) -> None:
    """Spot-check the 57-object pre-P12 inventory pillars survive untouched."""
    pillars = {
        "ix_rp_subject", "uq_resource_perm", "ix_agents_tenant_status",
        "uq_agents_key", "uq_tool_exec_idem", "ix_airl_tenant_occurred",
        "uq_agent_versions", "ix_role_permissions_permission",
    }
    idx = _index_map()
    for name in pillars:
        assert name in idx, name


# --------------------------------------------------------------------------- #
# downgrade / roundtrip
# --------------------------------------------------------------------------- #
def test_downgrade_and_roundtrip(db) -> None:
    cfg = make_config(lock_mode="fail")

    def p12_index_set():
        return {n for n in _index_map()
                if n in {x[0] for x in P12_CREATE_SET}}

    assert len(p12_index_set()) == 19
    downgrade(cfg, PREVIOUS_REVISION)
    assert current_revision() == PREVIOUS_REVISION
    assert p12_index_set() == set(), "downgrade must remove all 19 indexes"
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                   "AND tgparentid = 0") == 39, "P11 objects must survive downgrade"
    assert _scalar("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                   "AND tgparentid = 0 AND tgname = 'tg_audit_immutable'") == 1
    assert _scalar("SELECT count(*) FROM information_schema.tables "
                   "WHERE table_schema = 'public'") == 35

    upgrade(cfg, "head")
    assert current_revision() == REVISION
    assert len(p12_index_set()) == 19
