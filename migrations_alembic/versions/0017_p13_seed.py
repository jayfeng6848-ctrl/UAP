"""0017_p13_seed — P13 canonical baseline seed.

Scope (frozen): OPen-P10-1 之后的 P13 seed，**仅**插入基线数据，不新建任何 schema 对象。

    1. ``acl_subject_types``     3 rows  : user / role / agent
       （D-AUTH-18 canonical subject vocabulary · D-P13-04 register-only）
    2. ``permissions``          12 rows  : D-P13-01 canonical 12-item allow list
    3. ``role_permissions``     12 rows  : platform_admin x (those 12) x effect=allow

Explicitly NOT touched (frozen decisions):
    users (IMPL-01 = A) · audit_logs (IMPL-03 = A) · roles (D-P13-02 read-only)
    tenants / spaces / memberships / platform_memberships (D-P13-05 / D-P13-07 / D-P13-08)
    agents / agent_versions / agent_permissions / tool_executions (D-P13-04)

Transaction: the migration runs inside Alembic's own transaction (env.py P0 fix
restores transaction ownership to Alembic), so an explicit COMMIT occurs and the
changes persist. The registry seed itself is protected by C2/CC-7, which admits the
trusted migration identity (``current_user = session_user = uap_migrator``).

Downgrade (IMPL-04 = C): FAIL-CLOSED. Only P13 migration-owned rows may be removed,
and only when the current state is provably the clean P13 baseline. Any deviation --
extra rows, missing rows, runtime rows in ``users``, or dependent
``resource_permissions`` rows -- raises and rolls the whole downgrade back with
**zero deletes**. ``users`` is never deleted.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0017_p13_seed"
down_revision = "0016_open_p10_1_trust_boundary"
branch_labels = None
depends_on = None

PLATFORM_ADMIN_KEY = "platform_admin"

SUBJECT_TYPES: tuple[tuple[str, str], ...] = (
    ("user", "Human user authorization subject"),
    ("role", "Role authorization subject"),
    ("agent", "Agent authorization subject"),
)

# D-P13-01 canonical 12-item allow list: (key, resource_type, action)
PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    ("tenant.read", "tenant", "read"),
    ("tenant.admin", "tenant", "admin"),
    ("space.read", "space", "read"),
    ("space.admin", "space", "admin"),
    ("member.read", "member", "read"),
    ("member.admin", "member", "admin"),
    ("resource.read", "resource", "read"),
    ("resource.update", "resource", "update"),
    ("resource.delete", "resource", "delete"),
    ("agent.execute", "agent", "execute"),
    ("tool.execute", "tool", "execute"),
    ("audit.read", "audit", "read"),
)

PERMISSION_KEYS: tuple[str, ...] = tuple(p[0] for p in PERMISSIONS)
SUBJECT_TYPE_KEYS: tuple[str, ...] = tuple(s[0] for s in SUBJECT_TYPES)


def _platform_admin_id(conn) -> str:
    """Return the id of the existing platform_admin role (D-P13-02: read-only)."""
    row = conn.execute(
        sa.text(
            "SELECT id FROM public.roles "
            "WHERE key = :key AND scope = 'PLATFORM' "
            "  AND tenant_id IS NULL AND space_id IS NULL"
        ),
        {"key": PLATFORM_ADMIN_KEY},
    ).fetchone()
    if row is None:
        raise RuntimeError(
            "P13 seed precondition failed: platform_admin (PLATFORM scope) not found; "
            "0005 must own this role and P13 must not seed it (D-P13-02)."
        )
    return str(row[0])


def upgrade() -> None:
    conn = op.get_bind()

    # ---- 1. acl_subject_types: canonical subject vocabulary (register only) ----
    for key, description in SUBJECT_TYPES:
        conn.execute(
            sa.text(
                "INSERT INTO public.acl_subject_types (key, description) "
                "SELECT CAST(:key AS text), CAST(:description AS text) "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM public.acl_subject_types WHERE key = CAST(:key AS text)"
                ")"
            ),
            {"key": key, "description": description},
        )

    # ---- 2. permissions: D-P13-01 canonical 12-item allow list ----
    for key, resource_type, action in PERMISSIONS:
        conn.execute(
            sa.text(
                "INSERT INTO public.permissions "
                "  (key, resource_type, action, description, is_system) "
                "SELECT CAST(:key AS text), CAST(:resource_type AS text), "
                "       CAST(:action AS text), CAST(:description AS text), true "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM public.permissions WHERE key = CAST(:key AS text)"
                ")"
            ),
            {
                "key": key,
                "resource_type": resource_type,
                "action": action,
                "description": f"Platform baseline permission: {key}",
            },
        )

    # ---- 3. role_permissions: platform_admin x 12 x allow ----
    role_id = _platform_admin_id(conn)

    # conflict = explicit failure (D-P13-10): a non-allow binding for the same pair
    clash = conn.execute(
        sa.text(
            "SELECT p.key FROM public.role_permissions rp "
            "JOIN public.permissions p ON p.id = rp.permission_id "
            "WHERE rp.role_id = CAST(:role_id AS uuid) "
            "  AND rp.effect <> 'allow' "
            "  AND p.key = ANY(:keys)"
        ),
        {"role_id": role_id, "keys": list(PERMISSION_KEYS)},
    ).fetchall()
    if clash:
        raise RuntimeError(
            "P13 seed conflict: non-allow binding(s) already exist for platform_admin: "
            f"{sorted(str(r[0]) for r in clash)} (D-P13-01 forbids deny rows)."
        )

    for key in PERMISSION_KEYS:
        conn.execute(
            sa.text(
                "INSERT INTO public.role_permissions (role_id, permission_id, effect) "
                "SELECT CAST(:role_id AS uuid), p.id, 'allow' "
                "FROM public.permissions p "
                "WHERE p.key = CAST(:key AS text) "
                "  AND NOT EXISTS ("
                "    SELECT 1 FROM public.role_permissions rp "
                "    WHERE rp.role_id = CAST(:role_id AS uuid) "
                "      AND rp.permission_id = p.id "
                "      AND rp.effect = 'allow'"
                "  )"
            ),
            {"role_id": role_id, "key": key},
        )


def downgrade() -> None:
    conn = op.get_bind()
    role_id = _platform_admin_id(conn)

    # ---- FAIL-CLOSED pre-flight (IMPL-04 = C / D-P13-12) ------------------------
    checks: list[str] = []

    count = conn.execute(sa.text("SELECT count(*) FROM public.acl_subject_types")).scalar_one()
    keys = conn.execute(
        sa.text("SELECT array_agg(key ORDER BY key) FROM public.acl_subject_types")
    ).scalar_one()
    if count != len(SUBJECT_TYPE_KEYS) or sorted(keys or []) != sorted(SUBJECT_TYPE_KEYS):
        checks.append(f"acl_subject_types deviates from P13 baseline (count={count}, keys={keys})")

    count = conn.execute(sa.text("SELECT count(*) FROM public.permissions")).scalar_one()
    keys = conn.execute(
        sa.text("SELECT array_agg(key ORDER BY key) FROM public.permissions")
    ).scalar_one()
    if count != len(PERMISSION_KEYS) or sorted(keys or []) != sorted(PERMISSION_KEYS):
        checks.append(f"permissions deviates from P13 baseline (count={count})")

    count = conn.execute(
        sa.text(
            "SELECT count(*) FROM public.role_permissions rp "
            "JOIN public.roles r ON r.id = rp.role_id "
            "JOIN public.permissions p ON p.id = rp.permission_id "
            "WHERE r.key = :role_key AND rp.effect = 'allow' "
            "  AND p.key = ANY(:keys)"
        ),
        {"role_key": PLATFORM_ADMIN_KEY, "keys": list(PERMISSION_KEYS)},
    ).scalar_one()
    total_rp = conn.execute(
        sa.text("SELECT count(*) FROM public.role_permissions")
    ).scalar_one()
    if count != len(PERMISSION_KEYS) or total_rp != len(PERMISSION_KEYS):
        checks.append(
            f"role_permissions deviates from P13 baseline (matched={count}, total={total_rp})"
        )

    users_count = conn.execute(sa.text("SELECT count(*) FROM public.users")).scalar_one()
    if users_count != 0:
        checks.append(f"users is not empty (count={users_count}); P13 never creates users")

    dependents = conn.execute(
        sa.text(
            "SELECT count(*) FROM public.resource_permissions rp "
            "JOIN public.acl_subject_types t ON t.id = rp.subject_type_id"
        )
    ).scalar_one()
    if dependents != 0:
        checks.append(f"resource_permissions references registry rows (count={dependents})")

    if checks:
        raise RuntimeError(
            "P13 downgrade refused (FAIL-CLOSED, IMPL-04 = C / D-P13-12): "
            + "; ".join(checks)
            + " -- no rows were deleted."
        )

    # ---- deterministic removal of P13 migration-owned rows only ----------------
    conn.execute(
        sa.text(
            "DELETE FROM public.role_permissions rp "
            "USING public.permissions p "
            "WHERE rp.permission_id = p.id "
            "  AND rp.role_id = CAST(:role_id AS uuid) "
            "  AND rp.effect = 'allow' "
            "  AND p.key = ANY(:keys)"
        ),
        {"role_id": role_id, "keys": list(PERMISSION_KEYS)},
    )
    conn.execute(
        sa.text("DELETE FROM public.acl_subject_types WHERE key = ANY(:keys)"),
        {"keys": list(SUBJECT_TYPE_KEYS)},
    )
    conn.execute(
        sa.text("DELETE FROM public.permissions WHERE key = ANY(:keys)"),
        {"keys": list(PERMISSION_KEYS)},
    )
