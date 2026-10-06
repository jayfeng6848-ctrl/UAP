"""0019_p20_company — P20 Company business schema (first Business Module).

Authorization: ``P20 MIGRATION AUTHORIZATION — RETRY AFTER OPT-2 FREEZE``
(base UAP-V0.1.17-P18-CONTROL-PLANE · commit 08a0485b · tags 16;
frozen authority = PDL 附录 AC / AD / AE).

Creates exactly — and only — the following:

1. ``company_employees``   — Employee business entity (``Employee != User``)
2. ``company_assignments`` — business organizational assignment (employee ↔ space/department)
3. ``enforce_company_assignment_tenant_consistency()`` + trigger on ``company_assignments``
   — **structural** tenant consistency only (OPT-2): ``spaces`` has no ``(tenant_id, id)``
   uniqueness, the composite tenant-aware FK is therefore not representable, and existing
   platform tables must not be modified by this migration.
4. The 11 frozen Company permission rows (canonical 12 actions only — no new action, no
   role grant, no ACL subject type).
5. The minimal runtime privilege surface: ``uap_runtime`` ``SELECT`` / ``INSERT`` /
   ``UPDATE`` on the two Company tables — **no** ``DELETE`` / ``TRUNCATE`` /
   ``REFERENCES`` / ``TRIGGER``.

Explicitly NOT in this migration: role grants · audit-table changes · event / handler /
producer · API · worker · domain code · any modification of ``tenants`` / ``spaces`` /
``memberships`` / ``users`` / ``roles`` and of the existing ``permissions`` rows.

Conventions followed from the platform precedent (0004 ``enforce_membership_tenant_consistency``
/ 0011 ``tg_agents_tenant_space_consistency`` / 0014 & 0016 trigger functions):
``SECURITY INVOKER`` (default — ``SECURITY DEFINER`` is forbidden platform-wide, D-P11-08),
no dynamic SQL, no ``SET ROLE``, no audit writes, no DML from the trigger, and
``public.``-qualified references.

Constraint provenance (frozen P20 artifacts): ``company_assignments.employee_id`` uses
``ON DELETE CASCADE`` per P20 COMPANY CONSTRAINT/INDEX MATRIX · ENTITY CATALOG ·
RELATIONSHIP MATRIX ("员工删除随删分配"); ``space_id`` and ``tenant_id`` use
``ON DELETE RESTRICT``. The Company runtime never physically deletes rows
(D-P20S-09: no ``DELETE`` privilege · lifecycle is a status change), so no application
path reaches the cascade.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019_p20_company"
down_revision = "0018_p16_agent_runtime"
branch_labels = None
depends_on = None

RUNTIME_ROLE = "uap_runtime"

#: D-P20S-08 — canonical 12 actions only; (key, resource_type, action)
EMPLOYEE_PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    ("company_employee.read", "company_employee", "read"),
    ("company_employee.list", "company_employee", "list"),
    ("company_employee.create", "company_employee", "create"),
    ("company_employee.update", "company_employee", "update"),
    ("company_employee.delete", "company_employee", "delete"),
    ("company_employee.admin", "company_employee", "admin"),
)

ASSIGNMENT_PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    ("company_assignment.read", "company_assignment", "read"),
    ("company_assignment.list", "company_assignment", "list"),
    ("company_assignment.create", "company_assignment", "create"),
    ("company_assignment.update", "company_assignment", "update"),
    ("company_assignment.delete", "company_assignment", "delete"),
)

PERMISSIONS: tuple[tuple[str, str, str], ...] = EMPLOYEE_PERMISSIONS + ASSIGNMENT_PERMISSIONS
PERMISSION_KEYS: tuple[str, ...] = tuple(key for key, _, _ in PERMISSIONS)

#: OPT-2 — structural tenant consistency only (no authorization, no DML, no audit, no events).
_TENANT_CONSISTENCY_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION enforce_company_assignment_tenant_consistency() RETURNS trigger
LANGUAGE plpgsql AS $fn$
DECLARE
  employee_tenant uuid;
  space_tenant uuid;
BEGIN
  SELECT tenant_id INTO employee_tenant
    FROM public.company_employees WHERE id = NEW.employee_id;
  IF employee_tenant IS NULL THEN
    RAISE EXCEPTION 'company_assignments.employee_id % does not exist', NEW.employee_id;
  END IF;
  IF NEW.tenant_id IS DISTINCT FROM employee_tenant THEN
    RAISE EXCEPTION
      'company_assignments.tenant_id % does not match company_employees.tenant_id % '
      '(cross-tenant assignment denied)', NEW.tenant_id, employee_tenant;
  END IF;

  SELECT tenant_id INTO space_tenant FROM public.spaces WHERE id = NEW.space_id;
  IF space_tenant IS NULL THEN
    RAISE EXCEPTION 'company_assignments.space_id % does not exist', NEW.space_id;
  END IF;
  IF NEW.tenant_id IS DISTINCT FROM space_tenant THEN
    RAISE EXCEPTION
      'company_assignments.tenant_id % does not match spaces.tenant_id % '
      '(cross-tenant assignment denied)', NEW.tenant_id, space_tenant;
  END IF;

  -- structural consistency only: not an authorization check
  RETURN NEW;
END;
$fn$;
"""


def upgrade() -> None:
    # ----------------------------------------------------------- company_employees
    op.create_table(
        "company_employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_no", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("hired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT",
                                name="fk_company_employees_tenant"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT",
                                name="fk_company_employees_user"),
        sa.UniqueConstraint("tenant_id", "employee_no", name="uq_company_employees_no"),
        sa.CheckConstraint("status IN ('active','suspended','terminated')",
                           name="ck_company_employees_status"),
        sa.CheckConstraint(r"employee_no ~ '^[A-Za-z0-9._-]{1,64}$'",
                           name="ck_company_employees_no"),
        sa.CheckConstraint("(status = 'terminated') = (terminated_at IS NOT NULL)",
                           name="ck_company_employees_lifecycle"),
    )
    # uq_company_employees_no carries the frozen (tenant_id, employee_no) index requirement.
    op.create_index("ix_company_employees_tenant_status", "company_employees",
                    ["tenant_id", "status"])
    op.create_index("ix_company_employees_user", "company_employees", ["user_id"],
                    postgresql_where=sa.text("user_id IS NOT NULL"))
    # D-P20S-07 — one employee identity per (tenant, user)
    op.create_index("uq_company_employees_user", "company_employees",
                    ["tenant_id", "user_id"], unique=True,
                    postgresql_where=sa.text("user_id IS NOT NULL"))
    op.execute(sa.text(
        "CREATE TRIGGER tg_company_employees_set_updated_at BEFORE UPDATE ON company_employees"
        " FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))

    # --------------------------------------------------------- company_assignments
    op.create_table(
        "company_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT",
                                name="fk_company_assignments_tenant"),
        # frozen matrix / entity catalog: assignment is subordinate to the employee
        sa.ForeignKeyConstraint(["employee_id"], ["company_employees.id"], ondelete="CASCADE",
                                name="fk_company_assignments_employee"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="RESTRICT",
                                name="fk_company_assignments_space"),
        sa.CheckConstraint("status IN ('active','ended')",
                           name="ck_company_assignments_status"),
        sa.CheckConstraint("assignment_role IN ('member','lead')",
                           name="ck_company_assignments_role"),
        sa.CheckConstraint("(status = 'ended') = (ended_at IS NOT NULL)",
                           name="ck_company_assignments_lifecycle"),
    )
    op.create_index("ix_company_assignments_tenant_space_status", "company_assignments",
                    ["tenant_id", "space_id", "status"])
    op.create_index("ix_company_assignments_employee_status", "company_assignments",
                    ["employee_id", "status"])
    op.create_index("ix_company_assignments_tenant_status", "company_assignments",
                    ["tenant_id", "status"])
    op.create_index("uq_company_assignments_active", "company_assignments",
                    ["employee_id", "space_id"], unique=True,
                    postgresql_where=sa.text("ended_at IS NULL"))
    op.execute(sa.text(
        "CREATE TRIGGER tg_company_assignments_set_updated_at BEFORE UPDATE ON company_assignments"
        " FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))

    # ------------------------------------------- OPT-2 structural tenant consistency
    op.execute(sa.text(
        "DROP FUNCTION IF EXISTS enforce_company_assignment_tenant_consistency()"
    ))
    op.execute(sa.text(_TENANT_CONSISTENCY_FUNCTION_SQL))
    op.execute(sa.text(
        "CREATE TRIGGER tg_company_assignment_tenant_consistency"
        " BEFORE INSERT OR UPDATE ON company_assignments"
        " FOR EACH ROW EXECUTE FUNCTION enforce_company_assignment_tenant_consistency()"
    ))

    # ------------------------------------------------ 11 Company permission rows only
    conn = op.get_bind()
    for key, resource_type, action in PERMISSIONS:
        conn.execute(
            sa.text(
                "INSERT INTO public.permissions "
                "  (key, resource_type, action, description, is_system) "
                "SELECT CAST(:key AS text), CAST(:resource_type AS text), "
                "       CAST(:action AS text), CAST(:description AS text), false "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM public.permissions WHERE key = CAST(:key AS text)"
                ")"
            ),
            {
                "key": key,
                "resource_type": resource_type,
                "action": action,
                "description": f"Company business permission: {key}",
            },
        )

    # ----------------------------------------- minimal runtime privilege surface only
    for table in ("company_employees", "company_assignments"):
        op.execute(sa.text(
            f'GRANT SELECT, INSERT, UPDATE ON TABLE public."{table}" TO {RUNTIME_ROLE}'
        ))


def downgrade() -> None:
    # strict reverse: trigger → function → permission rows → triggers → tables
    # (indexes / constraints / grants disappear with their tables)
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS tg_company_assignment_tenant_consistency"
        " ON company_assignments"
    ))
    op.execute(sa.text(
        "DROP FUNCTION IF EXISTS enforce_company_assignment_tenant_consistency()"
    ))
    op.execute(sa.text(
        "DELETE FROM public.permissions WHERE key = ANY(:keys)"
    ).bindparams(keys=list(PERMISSION_KEYS)))
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS tg_company_assignments_set_updated_at ON company_assignments"
    ))
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS tg_company_employees_set_updated_at ON company_employees"
    ))
    op.drop_table("company_assignments")
    op.drop_table("company_employees")
