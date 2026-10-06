"""Idempotent materialization of the P21 Company roles (OQ-CUI-06 + F-1 · PDL AP).

Creates (or converges) exactly TWO application roles on the **existing** role
tables — there is no second role system:

    company_admin       scope = TENANT   (tenant-scoped row)
    department_manager  scope = SPACE    (space-scoped row)

plus the 8 operational Company permission grants and an optional membership binding.

What it deliberately never does
    * never touches ``platform_admin`` / ``tenant_admin`` / ``space_admin`` (no grant
      revocation, no attribute drift);
    * never grants the RESERVED permissions
      (``company_employee.delete`` / ``company_employee.admin`` /
      ``company_assignment.delete``);
    * never creates ``company_roles`` / ``company_role_permissions`` or any other
      parallel table; never issues DDL; never runs a migration;
    * re-running converges to the same state (idempotent) — no duplicate role and no
      duplicate grant.

``TEAM`` / ``SELF`` scopes are intentionally absent: ``ck_roles_scope`` admits only
PLATFORM / TENANT / SPACE, and extending it requires a new Human Decision + DDL
authorization (F-1).

Usage:
    python -m scripts.provision_company_roles --dsn <dsn> --tenant <tenant-uuid> \
        [--space <space-uuid> ...] [--bind <user-uuid>] [--verify-only]
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable, Mapping

import sqlalchemy as sa

#: The 8 operational Company permissions (PDL AP.1 OQ-CUI-06.2).
OPERATIONAL_PERMISSIONS: tuple[str, ...] = (
    "company_employee.read",
    "company_employee.list",
    "company_employee.create",
    "company_employee.update",
    "company_assignment.read",
    "company_assignment.list",
    "company_assignment.create",
    "company_assignment.update",
)

#: Never granted by this script (AO.6.2 / D-P20D-03/04).
RESERVED_PERMISSIONS: tuple[str, ...] = (
    "company_employee.delete",
    "company_employee.admin",
    "company_assignment.delete",
)

COMPANY_ADMIN = ("company_admin", "TENANT", "Company Administrator")
DEPARTMENT_MANAGER = ("department_manager", "SPACE", "Department Manager")


def _uuid(value: str | None) -> str | None:
    return None if value in (None, "", "-") else str(value)


def _role_id(conn: sa.Connection, *, key: str, tenant_id: str | None, space_id: str | None) -> str | None:
    row = conn.execute(
        sa.text(
            "SELECT id FROM roles WHERE lower(key) = lower(:k)"
            " AND tenant_id IS NOT DISTINCT FROM CAST(:t AS uuid)"
            " AND space_id IS NOT DISTINCT FROM CAST(:s AS uuid)"
        ),
        {"k": key, "t": _uuid(tenant_id), "s": _uuid(space_id)},
    ).first()
    return str(row[0]) if row is not None else None


def ensure_role(
    conn: sa.Connection,
    *,
    key: str,
    scope: str,
    name: str,
    tenant_id: str | None,
    space_id: str | None,
) -> tuple[str, bool]:
    """Return ``(role_id, created)``; an existing role is reused, never duplicated."""
    existing = _role_id(conn, key=key, tenant_id=tenant_id, space_id=space_id)
    if existing is not None:
        return existing, False
    role_id = conn.execute(
        sa.text(
            "INSERT INTO roles (key, name, scope, tenant_id, space_id, is_system, status)"
            " VALUES (:k, :n, :sc, CAST(:t AS uuid), CAST(:s AS uuid), false, 'active')"
            " RETURNING id"
        ),
        {"k": key, "n": name, "sc": scope, "t": _uuid(tenant_id), "s": _uuid(space_id)},
    ).scalar_one()
    return str(role_id), True


def ensure_grants(conn: sa.Connection, *, role_id: str, permissions: Iterable[str]) -> int:
    """Grant ``allow`` for each permission; duplicate grants are impossible."""
    granted = 0
    for key in permissions:
        permission_id = conn.execute(
            sa.text("SELECT id FROM permissions WHERE key = :k"), {"k": key}
        ).scalar()
        if permission_id is None:
            raise RuntimeError(f"permission is not in the vocabulary: {key}")
        result = conn.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id, effect)"
                " VALUES (CAST(:r AS uuid), CAST(:p AS uuid), 'allow')"
                " ON CONFLICT DO NOTHING"
            ),
            {"r": role_id, "p": str(permission_id)},
        )
        granted += int(result.rowcount or 0)
    return granted


def ensure_membership(
    conn: sa.Connection,
    *,
    tenant_id: str,
    space_id: str | None,
    user_id: str,
    role_id: str,
) -> bool:
    """Bind a user to a role idempotently (existing live row is reused)."""
    existing = conn.execute(
        sa.text(
            "SELECT id FROM memberships WHERE user_id = CAST(:u AS uuid)"
            " AND role_id = CAST(:r AS uuid) AND removed_at IS NULL"
            " AND space_id IS NOT DISTINCT FROM CAST(:s AS uuid)"
        ),
        {"u": user_id, "r": role_id, "s": _uuid(space_id)},
    ).first()
    if existing is not None:
        return False
    conn.execute(
        sa.text(
            "INSERT INTO memberships (tenant_id, space_id, user_id, role_id, status)"
            " VALUES (CAST(:t AS uuid), CAST(:s AS uuid), CAST(:u AS uuid),"
            " CAST(:r AS uuid), 'active')"
        ),
        {"t": tenant_id, "s": _uuid(space_id), "u": user_id, "r": role_id},
    )
    return True


def materialize(
    engine: sa.Engine,
    *,
    tenant_id: str,
    space_ids: Iterable[str] = (),
    bind_user: str | None = None,
) -> dict[str, Any]:
    """Converge the two Company roles, their grants and (optionally) a binding."""
    report: dict[str, Any] = {"tenant_id": tenant_id, "roles": [], "grants": 0, "memberships": 0}
    with engine.begin() as conn:
        admin_id, created = ensure_role(
            conn,
            key=COMPANY_ADMIN[0],
            scope=COMPANY_ADMIN[1],
            name=COMPANY_ADMIN[2],
            tenant_id=tenant_id,
            space_id=None,
        )
        report["roles"].append({"key": COMPANY_ADMIN[0], "scope": "TENANT", "created": created})
        report["grants"] += ensure_grants(
            conn, role_id=admin_id, permissions=OPERATIONAL_PERMISSIONS
        )
        if bind_user:
            report["memberships"] += int(
                ensure_membership(
                    conn,
                    tenant_id=tenant_id,
                    space_id=None,
                    user_id=bind_user,
                    role_id=admin_id,
                )
            )

        for space_id in space_ids:
            manager_id, created = ensure_role(
                conn,
                key=DEPARTMENT_MANAGER[0],
                scope=DEPARTMENT_MANAGER[1],
                name=DEPARTMENT_MANAGER[2],
                # The frozen ``enforce_roles_scope_shape()`` trigger requires a SPACE
                # role to carry tenant_id IS NULL (same shape as space_admin).
                tenant_id=None,
                space_id=space_id,
            )
            report["roles"].append(
                {"key": DEPARTMENT_MANAGER[0], "scope": "SPACE", "space_id": space_id, "created": created}
            )
            report["grants"] += ensure_grants(
                conn, role_id=manager_id, permissions=OPERATIONAL_PERMISSIONS
            )
            if bind_user:
                report["memberships"] += int(
                    ensure_membership(
                        conn,
                        # memberships keep the real tenant; only the role row is shape-bound.
                        tenant_id=tenant_id,
                        space_id=space_id,
                        user_id=bind_user,
                        role_id=manager_id,
                    )
                )
    return report


def verify(engine: sa.Engine, *, tenant_id: str, space_ids: Iterable[str] = ()) -> dict[str, Any]:
    """Read-only snapshot of the two roles and their granted permission counts."""
    out: dict[str, Any] = {"company_admin": None, "department_manager": []}
    with engine.connect() as conn:
        for key, role_tenant, space_id, slot in [
            (COMPANY_ADMIN[0], tenant_id, None, "company_admin")
        ] + [
            # SPACE roles carry tenant_id IS NULL (enforce_roles_scope_shape).
            (DEPARTMENT_MANAGER[0], None, space, None) for space in space_ids
        ]:
            role_id = _role_id(conn, key=key, tenant_id=role_tenant, space_id=space_id)
            if role_id is None:
                continue
            count = conn.execute(
                sa.text(
                    "SELECT count(*) FROM role_permissions WHERE role_id = CAST(:r AS uuid)"
                ),
                {"r": role_id},
            ).scalar_one()
            entry = {"key": key, "space_id": space_id, "grants": int(count)}
            if slot:
                out[slot] = entry
            else:
                out["department_manager"].append(entry)
    return out


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision the P21 Company roles (idempotent)")
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--space", action="append", default=[])
    parser.add_argument("--bind", default=None)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)

    engine = sa.create_engine(args.dsn)
    try:
        if args.verify_only:
            print(json.dumps(verify(engine, tenant_id=args.tenant, space_ids=args.space), indent=2))
            return 0
        report = materialize(
            engine, tenant_id=args.tenant, space_ids=args.space, bind_user=args.bind
        )
        report["verify"] = verify(engine, tenant_id=args.tenant, space_ids=args.space)
        print(json.dumps(report, indent=2))
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(_main())
