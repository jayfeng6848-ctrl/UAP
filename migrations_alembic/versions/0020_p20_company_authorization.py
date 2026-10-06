"""0020_p20_company_authorization — grant the 11 Company permissions to platform_admin.

Authorization: ``P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION EXECUTION
CONTRACT`` §Phase 1 (G1). PDL Appendix AF D-P20D-01 froze the decision
("platform_admin initially owns Company permissions") and deferred the actual
grant to the implementation round; this migration performs exactly that grant.

Scope (nothing else):

1. bind the 11 Company permissions seeded by ``0019_p20_company`` to the existing
   ``platform_admin`` role (``role_permissions`` · ``effect = 'allow'``);
2. idempotent: an existing binding is left untouched and no duplicate is created.

Explicitly NOT in this migration: no new role, no new ACL subject type, no new or
modified canonical action, no modification of an existing permission row, no
table/column/constraint change, no GRANT/REVOKE, no event.

Downgrade removes **only** the bindings this migration owns (platform_admin × the
11 Company keys × allow) and leaves every other row untouched.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0020_p20_company_authorization"
down_revision = "0019_p20_company"
branch_labels = None
depends_on = None

PLATFORM_ADMIN_KEY = "platform_admin"

#: The 11 Company permission keys frozen by 0019 (canonical 12 actions).
COMPANY_PERMISSION_KEYS: tuple[str, ...] = (
    "company_employee.read",
    "company_employee.list",
    "company_employee.create",
    "company_employee.update",
    "company_employee.delete",
    "company_employee.admin",
    "company_assignment.read",
    "company_assignment.list",
    "company_assignment.create",
    "company_assignment.update",
    "company_assignment.delete",
)


def _platform_admin_id(conn) -> str:
    """Return the existing platform_admin role id (never created here)."""
    row = conn.execute(
        sa.text(
            "SELECT id FROM public.roles WHERE key = :key AND scope = 'PLATFORM'"
            " AND tenant_id IS NULL AND space_id IS NULL"
        ),
        {"key": PLATFORM_ADMIN_KEY},
    ).fetchone()
    if row is None:
        raise RuntimeError(
            "P20 authorization precondition failed: platform_admin (PLATFORM scope)"
            " not found; 0005 owns that role and 0020 must not seed it."
        )
    return str(row[0])


def _require_permissions(conn) -> None:
    """Fail closed unless every Company permission row from 0019 is present."""
    rows = conn.execute(
        sa.text("SELECT key FROM public.permissions WHERE key = ANY(:keys)"),
        {"keys": list(COMPANY_PERMISSION_KEYS)},
    ).fetchall()
    present = {str(row[0]) for row in rows}
    missing = sorted(set(COMPANY_PERMISSION_KEYS) - present)
    if missing:
        raise RuntimeError(
            "P20 authorization precondition failed: Company permission rows missing "
            f"({missing}); 0019_p20_company must be applied first."
        )


def upgrade() -> None:
    conn = op.get_bind()
    _require_permissions(conn)
    role_id = _platform_admin_id(conn)
    for key in COMPANY_PERMISSION_KEYS:
        conn.execute(
            sa.text(
                "INSERT INTO public.role_permissions (role_id, permission_id, effect)"
                " SELECT CAST(:role_id AS uuid), p.id, 'allow'"
                " FROM public.permissions p"
                " WHERE p.key = CAST(:key AS text)"
                "   AND NOT EXISTS ("
                "     SELECT 1 FROM public.role_permissions rp"
                "     WHERE rp.role_id = CAST(:role_id AS uuid)"
                "       AND rp.permission_id = p.id"
                "       AND rp.effect = 'allow'"
                "   )"
            ),
            {"role_id": role_id, "key": key},
        )


def downgrade() -> None:
    conn = op.get_bind()
    role_id = _platform_admin_id(conn)
    conn.execute(
        sa.text(
            "DELETE FROM public.role_permissions rp"
            " USING public.permissions p"
            " WHERE rp.permission_id = p.id"
            "   AND rp.role_id = CAST(:role_id AS uuid)"
            "   AND rp.effect = 'allow'"
            "   AND p.key = ANY(:keys)"
        ),
        {"role_id": role_id, "keys": list(COMPANY_PERMISSION_KEYS)},
    )


__all__ = ["COMPANY_PERMISSION_KEYS", "PLATFORM_ADMIN_KEY"]
