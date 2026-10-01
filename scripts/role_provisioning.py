"""Versioned PostgreSQL role provisioning for the control-plane principal (P18-D01/D13).

This module is the **single versioned, auditable source** for the control-plane
DB authority. It exists because P18's PREP found that the platform had no
versioned role-creation mechanism at all (F-P18-I-01) and the P18 implementation
must not leave an unauditable, hand-made cluster state behind.

What it owns
    * the attribute set of the control-plane principal (``uap_control``);
    * the CONTROL_PLANE privilege baseline (write ceiling + read ceiling).

What it deliberately never does
    * no ``DROP ROLE`` / ``REVOKE`` / ``SET ROLE``;
    * no ALTER of any other principal (``uap_migrator`` / ``uap_bootstrap`` /
      ``uap_runtime`` / ``uap_app`` / ``uap_seed`` stay exactly as they are);
    * no secret material: the DSN is supplied by the caller, never stored here;
    * no use from the application path. The runtime and API packages must never
      import this module (guarded by
      ``tests/architecture/test_p18_control_plane_boundaries.py``).

Environment facts this module must respect
    * ``CREATE ROLE`` is a **cluster-level** object: the role is visible to every
      database in the cluster, and it does not disappear with a database;
    * PostgreSQL has no ``CREATE ROLE IF NOT EXISTS``: creation is therefore
      guarded by an explicit existence check, and repeated runs converge to the
      same state (idempotent);
    * role provisioning is environment infrastructure, **not** an Alembic
      migration — the migration head stays at ``0018_p16_agent_runtime``.

Usage
    python -m scripts.role_provisioning --dsn <admin-dsn> [--verify-only]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Mapping

import sqlalchemy as sa

CONTROL_PRINCIPAL = "uap_control"

#: Tables whose privileges must be applied to every partition as well.
PARTITIONED_PREFIXES = ("events", "audit_logs")


@dataclass(frozen=True)
class RoleSpec:
    """The exact attribute set a provisioned principal must end up with."""

    name: str
    can_login: bool = True
    superuser: bool = False
    create_db: bool = False
    create_role: bool = False
    replication: bool = False
    bypass_rls: bool = False
    inherit: bool = False

    def clauses(self) -> str:
        return " ".join(
            (
                "LOGIN" if self.can_login else "NOLOGIN",
                "SUPERUSER" if self.superuser else "NOSUPERUSER",
                "CREATEDB" if self.create_db else "NOCREATEDB",
                "CREATEROLE" if self.create_role else "NOCREATEROLE",
                "REPLICATION" if self.replication else "NOREPLICATION",
                "BYPASSRLS" if self.bypass_rls else "NOBYPASSRLS",
                "INHERIT" if self.inherit else "NOINHERIT",
            )
        )


@dataclass(frozen=True)
class PrivilegeReport:
    """Observed/expected comparison for one principal."""

    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    forbidden: tuple[str, ...]
    attribute_drift: tuple[str, ...]
    total: int

    @property
    def ok(self) -> bool:
        return not (self.missing or self.unexpected or self.forbidden or self.attribute_drift)


#: The control-plane principal: NOINHERIT + no administrative capability beyond
#: the table privileges below (P18-D01 / §4 of the implementation instruction).
CONTROL_PLANE_ROLE = RoleSpec(name=CONTROL_PRINCIPAL)

#: Write ceiling (P18-D13). Additive INSERT/UPDATE only — **no DELETE anywhere**.
CONTROL_PLANE_WRITE: Mapping[str, str] = {
    "tenants": "INSERT, UPDATE",
    "spaces": "INSERT, UPDATE",
    "roles": "INSERT",
    "role_permissions": "INSERT",
    "tenant_memberships": "INSERT",
    "memberships": "INSERT",
    "resources": "INSERT",
    "audit_logs": "INSERT",
}

#: Read ceiling, derived from the control-plane query graph (structural objects,
#: their authorization inputs and the platform bootstrap/state checks).
CONTROL_PLANE_READ: Mapping[str, str] = {
    "users": "SELECT",
    "tenants": "SELECT",
    "spaces": "SELECT",
    "roles": "SELECT",
    "permissions": "SELECT",
    "role_permissions": "SELECT",
    "tenant_memberships": "SELECT",
    "memberships": "SELECT",
    "platform_memberships": "SELECT",
    "platform_state": "SELECT",
    "resources": "SELECT",
}

#: Tables the control plane must not be able to touch at all (any privilege).
CONTROL_PLANE_FORBIDDEN: tuple[str, ...] = (
    "acl_subject_types",
    "credentials",
    "identities",
    "sessions",
    "devices",
    "tools",
    "tool_versions",
    "tool_executions",
    "agent_versions",
    "agents",
    "agent_permissions",
    "ai_providers",
    "ai_models",
    "ai_routes",
    "ai_policies",
    "ai_request_logs",
    "events",
    "resource_permissions",
)


def _merge(*maps: Mapping[str, str]) -> dict[str, set[str]]:
    merged: dict[str, set[str]] = {}
    for mapping in maps:
        for table, privileges in mapping.items():
            merged.setdefault(table, set()).update(
                p.strip() for p in privileges.split(",") if p.strip()
            )
    return merged


def baseline() -> dict[str, set[str]]:
    """The full declared CONTROL_PLANE privilege set (write + read)."""
    return _merge(CONTROL_PLANE_WRITE, CONTROL_PLANE_READ)


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


def role_attributes(conn: sa.Connection, principal: str) -> dict[str, bool] | None:
    row = conn.execute(
        sa.text(
            "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls,"
            " rolcanlogin, rolinherit FROM pg_roles WHERE rolname = :name"
        ),
        {"name": principal},
    ).first()
    if row is None:
        return None
    return {
        "superuser": bool(row[0]),
        "create_db": bool(row[1]),
        "create_role": bool(row[2]),
        "replication": bool(row[3]),
        "bypass_rls": bool(row[4]),
        "can_login": bool(row[5]),
        "inherit": bool(row[6]),
    }


def ensure_role(conn: sa.Connection, spec: RoleSpec = CONTROL_PLANE_ROLE) -> str:
    """Create the principal if absent, otherwise converge it to the spec."""
    existing = role_attributes(conn, spec.name)
    if existing is None:
        conn.execute(sa.text(f'CREATE ROLE "{spec.name}" {spec.clauses()}'))
        return "created"
    conn.execute(sa.text(f'ALTER ROLE "{spec.name}" {spec.clauses()}'))
    return "altered"


def grant(engine: sa.Engine, *, principal: str = CONTROL_PRINCIPAL) -> int:
    """Apply the CONTROL_PLANE baseline additively (partitions included)."""
    declared = baseline()
    granted = 0
    with engine.begin() as conn:
        for table in sorted(declared):
            privileges = ",".join(sorted(declared[table]))
            for target in _targets(conn, table):
                conn.execute(
                    sa.text(f'GRANT {privileges} ON TABLE public."{target}" TO "{principal}"')
                )
                granted += 1
    return granted


def snapshot(engine: sa.Engine, principal: str = CONTROL_PRINCIPAL) -> dict[str, set[str]]:
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


def verify(engine: sa.Engine, *, principal: str = CONTROL_PRINCIPAL) -> PrivilegeReport:
    """Compare observed state with the declared spec (fail-closed, no guessing)."""
    observed = snapshot(engine, principal)
    want: dict[str, set[str]] = {}
    with engine.connect() as conn:
        for table, privileges in baseline().items():
            for target in _targets(conn, table):
                want[target] = set(privileges)

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

    forbidden: list[str] = []
    with engine.connect() as conn:
        for table in CONTROL_PLANE_FORBIDDEN:
            exists = conn.execute(
                sa.text("SELECT to_regclass(:qualified) IS NOT NULL"),
                {"qualified": f"public.{table}"},
            ).scalar()
            if not exists:
                continue
            row = conn.execute(
                sa.text(
                    "SELECT has_table_privilege(:principal, :qualified, 'INSERT'),"
                    " has_table_privilege(:principal, :qualified, 'UPDATE'),"
                    " has_table_privilege(:principal, :qualified, 'DELETE'),"
                    " has_table_privilege(:principal, :qualified, 'SELECT')"
                ),
                {"principal": principal, "qualified": f"public.{table}"},
            ).one()
            if any(bool(flag) for flag in row):
                forbidden.append(
                    f"{table}:{sorted(p for p, f in zip(('INSERT','UPDATE','DELETE','SELECT'), row) if f)}"
                )
        # DELETE must not exist anywhere in the ceiling.
        for table in sorted(baseline()):
            flags = conn.execute(
                sa.text(
                    "SELECT has_table_privilege(:principal, :qualified, 'DELETE'),"
                    " has_table_privilege(:principal, :qualified, 'TRUNCATE'),"
                    " has_table_privilege(:principal, :qualified, 'TRIGGER'),"
                    " has_table_privilege(:principal, :qualified, 'REFERENCES')"
                ),
                {"principal": principal, "qualified": f"public.{table}"},
            ).one()
            if any(bool(flag) for flag in flags):
                forbidden.append(f"{table}:destructive-privilege")

    attribute_drift: list[str] = []
    with engine.connect() as conn:
        actual = role_attributes(conn, principal)
    if actual is None:
        attribute_drift.append("role-missing")
    else:
        for field, expected in (
            ("superuser", CONTROL_PLANE_ROLE.superuser),
            ("create_db", CONTROL_PLANE_ROLE.create_db),
            ("create_role", CONTROL_PLANE_ROLE.create_role),
            ("replication", CONTROL_PLANE_ROLE.replication),
            ("bypass_rls", CONTROL_PLANE_ROLE.bypass_rls),
            ("can_login", CONTROL_PLANE_ROLE.can_login),
            ("inherit", CONTROL_PLANE_ROLE.inherit),
        ):
            if actual[field] != expected:
                attribute_drift.append(f"{field}={actual[field]}")

    return PrivilegeReport(
        missing=missing,
        unexpected=unexpected,
        forbidden=tuple(sorted(set(forbidden))),
        attribute_drift=tuple(attribute_drift),
        total=sum(len(v) for v in observed.values()),
    )


def provision(engine: sa.Engine, *, principal: str = CONTROL_PRINCIPAL) -> PrivilegeReport:
    """Idempotent provisioning of the control-plane principal and its baseline."""
    spec = RoleSpec(name=principal)
    with engine.begin() as conn:
        ensure_role(conn, spec)
    grant(engine, principal=principal)
    return verify(engine, principal=principal)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="UAP P18 control-plane role provisioning (versioned source)"
    )
    parser.add_argument("--dsn", required=True, help="administrative DSN (CREATEROLE required)")
    parser.add_argument("--principal", default=CONTROL_PRINCIPAL)
    parser.add_argument("--verify-only", action="store_true", help="do not provision; only report")
    args = parser.parse_args(argv)

    engine = sa.create_engine(args.dsn)
    try:
        if args.verify_only:
            report = verify(engine, principal=args.principal)
        else:
            report = provision(engine, principal=args.principal)
        print(f"principal={args.principal}")
        print(f"observed_grants={report.total}")
        print(f"missing={list(report.missing)}")
        print(f"unexpected={list(report.unexpected)}")
        print(f"forbidden={list(report.forbidden)}")
        print(f"attribute_drift={list(report.attribute_drift)}")
        print(f"ok={report.ok}")
        return 0 if report.ok else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
