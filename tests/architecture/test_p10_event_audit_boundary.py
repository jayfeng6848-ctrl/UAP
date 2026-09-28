"""P10 carrier-boundary guard: the five faces stay separate.

``D-P10-17`` formalises five distinct carrier faces and requires that the
boundary be **enforceable**, not merely declared:

    event           -> ``events``                 (P10)
    audit           -> ``audit_logs``             (P10)
    operational log -> ``infrastructure/logging`` (NOT P10)
    trace           -> log envelope fields        (NOT P10)
    metric          -> undefined                  (NOT P10)

The decision's ``禁止`` column is the acceptance target: an operational log must
never be written into ``audit_logs``, ``event`` and ``audit`` must never fuse
into one carrier, and the boundary must not be claimed as "enforced" while
having no test. This module is that test (``DEPENDENCY_RULES.md`` § "Carrier
faces").

It also pins the P10 / P12 seam: the seven ``ix_events_*`` / ``ix_audit_*``
indexes are P12-owned (``D-P12-08``), so the P10 migration creates none.

Scanning discipline
-------------------
Structural constructs (``CREATE TABLE`` / ``CREATE INDEX`` / ``CREATE TRIGGER``)
live **inside SQL string literals**, so those scans use the raw source. The
forbidden-construct scans use a view with **comments and docstrings removed** —
a rule *stated* in prose is not a violation of it. Table names are referenced
through module constants, so constants are resolved before matching.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]

MIGRATION = ROOT / "migrations_alembic" / "versions" / "0013_p10_event_audit.py"
EVENT_CONTRACT = ROOT / "core" / "event" / "interfaces.py"
AUDIT_CONTRACT = ROOT / "core" / "audit" / "interfaces.py"
DEPENDENCY_RULES = ROOT / "docs" / "architecture" / "DEPENDENCY_RULES.md"

P10_TABLES = {"events", "audit_logs"}
P12_INDEX_PREFIXES = ("ix_events_", "ix_audit_")

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}


# --------------------------------------------------------------------------- #
# readers
# --------------------------------------------------------------------------- #
def _raw(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _blank(text: str, start: tuple[int, int], end: tuple[int, int]) -> str:
    """Blank a (line, col) span of ``text`` in place, preserving line count."""
    lines = text.split("\n")
    sl, sc = start
    el, ec = end
    if sl == el:
        row = lines[sl - 1]
        lines[sl - 1] = row[:sc] + " " * (ec - sc) + row[ec:]
    else:
        lines[sl - 1] = lines[sl - 1][:sc]
        for index in range(sl, el - 1):
            lines[index] = ""
        lines[el - 1] = " " * ec + lines[el - 1][ec:]
    return "\n".join(lines)


def _docstring_spans(src: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    spans = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            first = body[0] if body else None
            value = getattr(first, "value", None)
            if isinstance(first, ast.Expr) and isinstance(value, ast.Constant) \
                    and isinstance(value.value, str):
                spans.append(((value.lineno, value.col_offset),
                              (value.end_lineno, value.end_col_offset)))
    return spans


def _sql_view(path: Path) -> str:
    """Source with comments and docstrings removed, implicit concatenation joined.

    Two transformations are load-bearing:

    * a rule **stated in prose** (comment / docstring) is not a violation of it,
      so both are blanked before scanning for forbidden constructs;
    * SQL is written as implicit string concatenation across lines, which
      defeats naive matching — adjacent literals are therefore joined so
      ``CREATE TRIGGER`` is a single contiguous span.
    """
    src = _raw(path)
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            src = _blank(src, tok.start, tok.end)
    for start, end in _docstring_spans(src):
        src = _blank(src, start, end)
    src = re.sub(r'"\s*\n\s*"', "", src)
    src = re.sub(r"'\s*\n\s*'", "", src)
    return src


def _constants(src: str) -> dict[str, str]:
    """Module-level ``NAME = "literal"`` bindings (table names are variables)."""
    return dict(re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=\s*"([a-z0-9_]+)"\s*$', src, re.M))


def _created_tables(src: str) -> set[str]:
    """Parent tables and child partitions created by the P10 migration."""
    consts = _constants(src)
    names: set[str] = set()
    for literal, ident in re.findall(
            r'op\.create_table\(\s*(?:"([a-z_]+)"|([A-Z_][A-Z0-9_]*))', src):
        names.add(literal or consts.get(ident, ident))
    names |= set(re.findall(r'CREATE TABLE "([a-z0-9_]+)" PARTITION OF', src))
    return names


def _core_files() -> list[Path]:
    return sorted(p for p in (ROOT / "core").rglob("*.py")
                  if not any(part in SKIP_DIRS for part in p.parts))


# --------------------------------------------------------------------------- #
# 1. carrier mapping — one carrier per face, no fusion
# --------------------------------------------------------------------------- #
def test_p10_migration_creates_exactly_the_two_p10_tables() -> None:
    """``event`` -> ``events`` and ``audit`` -> ``audit_logs``: nothing else."""
    created = {n for n in _created_tables(_sql_view(MIGRATION))
               if not re.fullmatch(r"(events|audit_logs)_\d{6}", n)}
    assert created == P10_TABLES, f"unexpected P10 carriers: {sorted(created)}"


def test_event_and_audit_contracts_live_in_separate_core_packages() -> None:
    """``event`` and ``audit`` must not be fused into one core module."""
    assert EVENT_CONTRACT.exists() and AUDIT_CONTRACT.exists()
    event_src, audit_src = _raw(EVENT_CONTRACT), _raw(AUDIT_CONTRACT)
    for token in ("AUDIT_OUTCOMES", "AuditEvent", "AuthorizationDecisionAudit"):
        assert token not in event_src, f"{token} leaked into the event contract"
    assert "DomainEvent" not in audit_src, "DomainEvent leaked into the audit contract"


def test_no_other_core_module_declares_an_event_or_audit_carrier() -> None:
    """Only ``core/event`` / ``core/audit`` may own the two P10 carriers."""
    pattern = re.compile(r"\bclass\s+(DomainEvent|AuditEvent|AuthorizationDecisionAudit)\b")
    offenders = [str(p.relative_to(ROOT)) for p in _core_files()
                 if p.relative_to(ROOT).parts[:2] not in (("core", "event"), ("core", "audit"))
                 and pattern.search(_raw(p))]
    assert not offenders, f"P10 carriers declared outside their package: {offenders}"


def test_operational_logging_never_targets_audit_logs() -> None:
    """The operational-log face must not write into the audit carrier."""
    logging_dir = ROOT / "infrastructure" / "logging"
    if not logging_dir.exists():
        pytest.skip("infrastructure/logging is not present in this tree")
    offenders: list[str] = []
    for path in logging_dir.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        src = _raw(path)
        if re.search(r"\baudit_logs\b", src):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"operational logging writes the audit carrier: {offenders}"


# --------------------------------------------------------------------------- #
# 2. P10 / P12 seam + immutability ownership
# --------------------------------------------------------------------------- #
def test_p10_migration_creates_no_query_index() -> None:
    """The 7 ``ix_events_*`` / ``ix_audit_*`` indexes are P12-owned (D-P12-08)."""
    src = _sql_view(MIGRATION)
    created = re.findall(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z0-9_]+)", src, re.I)
    created += re.findall(r'op\.create_index\(\s*"([a-z0-9_]+)"', src)
    owned_by_p12 = [n for n in created if n.startswith(P12_INDEX_PREFIXES)]
    assert not owned_by_p12, f"P10 migration carries P12-owned indexes: {owned_by_p12}"
    assert not created, f"P10 owns no index at all, but creates: {created}"


def test_audit_immutability_is_p10_owned_and_events_has_no_trigger() -> None:
    """``tg_audit_immutable`` on ``audit_logs``; ``events`` carries no trigger."""
    src = _sql_view(MIGRATION)
    triggers = re.findall(
        r"CREATE TRIGGER\s+([a-z_]+)\s+(BEFORE|AFTER)\s+([A-Z ]+?)\s+ON\s+([a-z_]+)", src)
    assert len(triggers) == 1, f"expected exactly one P10 trigger, got {triggers}"
    name, timing, events, table = triggers[0]
    assert name == "tg_audit_immutable", name
    assert table == "audit_logs", table
    assert timing == "BEFORE", timing
    assert set(events.split(" OR ")) == {"UPDATE", "DELETE"}, events
    assert not re.search(r"CREATE TRIGGER[^;]*?\bON\s+events\b", src, re.I), \
        "events must carry no trigger (claim is application-level CAS)"


def test_audit_logs_has_no_mutation_columns() -> None:
    """Append-only is structural: no ``updated_at`` / ``deleted_at``."""
    cols = re.findall(r'sa\.Column\(\s*"([a-z_]+)"', _sql_view(MIGRATION))
    assert "updated_at" not in cols, "audit/event tables are append-only structures"
    assert "deleted_at" not in cols, "no soft-delete column on the P10 carriers"


# --------------------------------------------------------------------------- #
# 3. security surface of the P10 migration
# --------------------------------------------------------------------------- #
def test_p10_migration_has_no_privilege_escalation_rls_or_default_partition() -> None:
    """No SECURITY DEFINER, no GRANT, no RLS, no DEFAULT partition."""
    src = _sql_view(MIGRATION)
    for forbidden, why in (
        ("SECURITY DEFINER", "functions stay SECURITY INVOKER (P11-08 isomorphic)"),
        ("ROW LEVEL SECURITY", "D-P10-15 forbids RLS"),
        ("CREATE POLICY", "D-P10-15 forbids RLS"),
        ("DEFAULT", "D-P10-09 forbids a DEFAULT partition"),
        ("GRANT", "OPEN-P10-1 = DEFER: the migration performs no GRANT"),
    ):
        assert not re.search(r"\b%s\b" % re.escape(forbidden), src), \
            f"P10 migration must not contain {forbidden!r} ({why})"


def test_p10_migration_function_reads_no_table() -> None:
    """The immutability function must not depend on the caller's search_path."""
    src = _raw(MIGRATION)
    assert "LANGUAGE plpgsql" in src
    body = src.split('_AUDIT_IMMUTABLE_SQL = """', 1)[1].split('"""', 1)[0]
    assert "RAISE EXCEPTION" in body, "the trigger function must raise"
    assert not re.search(r"\bFROM\b", body, re.I), \
        "the immutability function must not read any table (no search_path dependency)"
    assert not re.search(r"\b(?:INSERT|UPDATE|DELETE)\b", body, re.I), \
        "the immutability function must not perform hidden DML (no recursion)"


# --------------------------------------------------------------------------- #
# 4. the declaration itself must exist (the guard is its executable form)
# --------------------------------------------------------------------------- #
def test_five_carrier_faces_are_declared_in_dependency_rules() -> None:
    """The formal five-face boundary statement must exist in the rules doc."""
    src = _raw(DEPENDENCY_RULES)
    assert "Carrier faces" in src, "the carrier-face section is missing"
    for face in ("event", "audit", "operational log", "trace", "metric"):
        assert re.search(re.escape(face), src, re.I), f"carrier face {face!r} is not declared"
    assert "test_p10_event_audit_boundary" in src, \
        "the boundary must name the guard that enforces it"


def test_event_contract_uses_the_canonical_uuid7_generator() -> None:
    """``D-P10-02``: event identity is UUIDv7, never ``uuid4``."""
    src = _raw(EVENT_CONTRACT)
    assert "uuid4" not in src, "DomainEvent identity must not use uuid4()"
    assert "new_event_id" in src, "DomainEvent identity must use the canonical UUIDv7 helper"
