"""Baseline privilege materialization (P16-D15 · F-P16-I-04).

The P14 runtime privilege state was accepted but **environment-applied**: no
GRANT/REVOKE artifact existed in the repository, so a freshly migrated database
had schema but no runtime privileges. This module makes that accepted state
reproducible, versioned and auditable.

What it does
    * grants exactly the accepted P14 baseline for ``uap_runtime`` and ``uap_app``;
    * grants on the partitioned parents **and their existing partitions**
      (privileges on a partitioned parent are not inherited by partitions);
    * is additive and idempotent: re-running changes nothing, and running it
      before or after the P16 delta (migration ``0018``) yields the same state.

What it deliberately does NOT do
    * no new principal, no role redesign, no semantic privilege expansion;
    * no P16 delta (``ai_*`` / ``tool_versions`` / ``tool_permissions`` /
      ``tool_executions`` / ``agent_runs``) — that delta stays in migration 0018;
    * no GRANT ALL, no DELETE on protected ledgers, no DDL privileges.

Usage
    python -m scripts.privileges --dsn <migration-dsn> [--verify-only]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Mapping

import sqlalchemy as sa

#: Accepted P14 baseline: table -> privileges for ``uap_runtime``.
RUNTIME_BASELINE: Mapping[str, str] = {
    "acl_subject_types": "SELECT",
    "agent_permissions": "SELECT",
    "agent_versions": "SELECT",
    "agents": "SELECT",
    "alembic_version": "SELECT",
    "permissions": "SELECT",
    "platform_memberships": "SELECT",
    "platform_state": "SELECT",
    "resource_permissions": "SELECT",
    "role_permissions": "SELECT",
    "roles": "SELECT",
    "spaces": "SELECT",
    "tenants": "SELECT",
    "tools": "SELECT",
    "credentials": "SELECT, INSERT, UPDATE",
    "devices": "SELECT, INSERT, UPDATE",
    "identities": "SELECT, INSERT, UPDATE",
    "resources": "SELECT, INSERT, UPDATE",
    "users": "SELECT, INSERT, UPDATE",
    "events": "SELECT, INSERT, UPDATE",
    "audit_logs": "SELECT, INSERT",
    "memberships": "SELECT, INSERT, UPDATE, DELETE",
    "sessions": "SELECT, INSERT, UPDATE, DELETE",
    "tenant_memberships": "SELECT, INSERT, UPDATE, DELETE",
}

#: Accepted P14 baseline for the application principal (readiness + audit append).
APP_BASELINE: Mapping[str, str] = {
    "alembic_version": "SELECT",
    "audit_logs": "SELECT, INSERT",
}

PARTITIONED_PREFIXES = ("events", "audit_logs")

#: P16 incremental grants (owned by migration ``0018`` — never granted here).
P16_DELTA: Mapping[str, str] = {
    "ai_providers": "SELECT",
    "ai_models": "SELECT",
    "ai_routes": "SELECT",
    "ai_policies": "SELECT",
    "ai_request_logs": "INSERT",
    "tool_versions": "SELECT",
    "tool_permissions": "SELECT",
    "tool_executions": "SELECT, INSERT, UPDATE",
    "agent_runs": "SELECT, INSERT, UPDATE",
}


@dataclass(frozen=True)
class PrivilegeReport:
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    total: int

    @property
    def ok(self) -> bool:
        return not self.missing and not self.unexpected


def _partitions(conn: sa.Connection, parent: str) -> list[str]:
    rows = conn.execute(
        sa.text(
            "SELECT c.relname FROM pg_class c JOIN pg_inherits i ON i.inhrelid = c.oid"
            " JOIN pg_class p ON p.oid = i.inhparent WHERE p.relname = :parent"
        ),
        {"parent": parent},
    ).all()
    return [str(row[0]) for row in rows]


def _targets(conn: sa.Connection, table: str) -> list[str]:
    names = [table]
    if table in PARTITIONED_PREFIXES:
        names.extend(_partitions(conn, table))
    return names


def materialize(engine: sa.Engine, *, baseline: Mapping[str, str] = RUNTIME_BASELINE,
                principal: str = "uap_runtime") -> int:
    """Apply the baseline additively. Returns the number of GRANT statements."""
    granted = 0
    with engine.begin() as conn:
        for table, privileges in baseline.items():
            for target in _targets(conn, table):
                conn.execute(
                    sa.text(f'GRANT {privileges} ON TABLE public."{target}" TO {principal}')
                )
                granted += 1
        for table, privileges in APP_BASELINE.items():
            if principal != "uap_runtime":
                break
            for target in _targets(conn, table):
                conn.execute(
                    sa.text(f'GRANT {privileges} ON TABLE public."{target}" TO uap_app')
                )
                granted += 1
    return granted


def snapshot(engine: sa.Engine, principal: str = "uap_runtime") -> dict[str, set[str]]:
    """Observed (table -> privileges) for one principal."""
    rows = engine.connect().execute(
        sa.text(
            "SELECT table_name, privilege_type FROM information_schema.role_table_grants"
            " WHERE grantee = :principal"
        ),
        {"principal": principal},
    ).all()
    out: dict[str, set[str]] = {}
    for table, privilege in rows:
        out.setdefault(str(table), set()).add(str(privilege))
    return out


def verify(engine: sa.Engine, *, expected: Mapping[str, str], principal: str = "uap_runtime") -> PrivilegeReport:
    """Compare the observed state with the declared baseline (unexpected = 0)."""
    observed = snapshot(engine, principal)
    want: dict[str, set[str]] = {}
    with engine.connect() as conn:
        for table, privileges in expected.items():
            for target in _targets(conn, table):
                want[target] = {p.strip() for p in privileges.split(",")}
    missing = tuple(
        f"{table}:{sorted(want[table] - observed.get(table, set()))}"
        for table in sorted(want)
        if want[table] - observed.get(table, set())
    )
    unexpected = tuple(
        f"{table}:{sorted(observed[table] - want.get(table, set()))}"
        for table in sorted(observed)
        if observed[table] - want.get(table, set())
    )
    return PrivilegeReport(missing=missing, unexpected=unexpected, total=sum(len(v) for v in observed.values()))


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="UAP baseline privilege materialization (P16-D15)")
    parser.add_argument("--dsn", required=True, help="migration identity DSN")
    parser.add_argument("--verify-only", action="store_true", help="do not grant; only report")
    parser.add_argument(
        "--include-p16-delta",
        action="store_true",
        help="expect the P16 delta (migration 0018) in addition to the P14 baseline",
    )
    args = parser.parse_args(argv)

    engine = sa.create_engine(args.dsn)
    try:
        if not args.verify_only:
            granted = materialize(engine)
            print(f"granted_statements={granted}")
        expected: dict[str, str] = dict(RUNTIME_BASELINE)
        if args.include_p16_delta:
            expected.update(P16_DELTA)
        report = verify(engine, expected=expected)
        print(f"observed_runtime_grants={report.total}")
        print(f"missing={list(report.missing)}")
        print(f"unexpected={list(report.unexpected)}")
        return 0 if report.ok else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
