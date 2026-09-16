"""0004_b1_2_tenant_space — Tenant / Space Foundation

Revision ID: 0004_b1_2_tenant_space
Revises: 0003_b1_1_root_identity
Create Date: 2026-09-08

Scope: B1-2（仅 4 张表；无 roles / permissions / resources / ACL / Agent / Tool / AI / Event / Domain 表）

   tenants → spaces → memberships
   users   → tenant_memberships → tenants
   users   → memberships        → spaces

冻结来源（逐字段核对见 docs/architecture/STEP1B_B1_2_SCHEMA_REVIEW.md）：
  * CORE_DOMAIN_MODEL.md §1.2 + B0 CONSTRAINT_MATRIX / INDEX_STRATEGY / TRIGGER_INVENTORY
  * Decision Log D-01 / D-02 / D-03 / D-04

D-01: role_id 列存在，但 **B1-2 不创建指向 roles 的 FK**（Forward Dependency，roles 属 B1-3）
      —— 这不是 DEFERRABLE FK：DEFERRABLE 只延后已存在约束的检查时机。
D-02: Role scope 由应用层 fail-closed 校验（B1-3 才做 DB 强制）→ 本 revision 无 scope trigger
D-03: spaces.owner_id → users.id ON DELETE SET NULL（禁止 CASCADE）
D-04: RLS 未启用（OPEN DESIGN QUESTION）→ 本 revision 无任何 RLS 语句
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_b1_2_tenant_space"
down_revision = "0003_b1_1_root_identity"
branch_labels = None
depends_on = None

_TABLES = ("tenants", "spaces", "tenant_memberships", "memberships")

_TENANT_CONSISTENCY_SQL = """
CREATE FUNCTION enforce_membership_tenant_consistency() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  space_tenant uuid;
BEGIN
  SELECT tenant_id INTO space_tenant FROM spaces WHERE id = NEW.space_id;
  IF space_tenant IS NULL THEN
    RAISE EXCEPTION 'memberships.space_id % does not exist', NEW.space_id;
  END IF;
  IF NEW.tenant_id IS DISTINCT FROM space_tenant THEN
    RAISE EXCEPTION
      'memberships.tenant_id % does not match spaces.tenant_id % (cross-tenant membership denied)',
      NEW.tenant_id, space_tenant;
  END IF;
  -- 只做一致性校验：不写其它表、不做授权、不做级联、不写审计
  RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
    # ---------------------------------------------------------------- tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("plan", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('provisioning','active','suspended','archived','deleted')",
            name="ck_tenants_status",
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'",
            name="ck_tenants_slug",
        ),
    )
    # slug uniqueness is case-insensitive via lower() expression index (no citext)
    op.execute(
        sa.text("CREATE UNIQUE INDEX uq_tenants_slug ON tenants (lower(slug))")
    )

    # ----------------------------------------------------------------- spaces
    op.create_table(
        "spaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT", name="fk_spaces_tenant"),
        # D-03: owner removal must never delete the space
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL", name="fk_spaces_owner"),
        sa.CheckConstraint("status IN ('active','archived','deleted')", name="ck_spaces_status"),
        # kind is runtime data: format only, never an enum of business domains
        sa.CheckConstraint("kind ~ '^[a-z][a-z0-9_.]{1,63}$'", name="ck_spaces_kind"),
        sa.CheckConstraint("visibility IN ('private','tenant','link')", name="ck_spaces_visibility"),
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_spaces_key ON spaces (tenant_id, lower(key)) "
            "WHERE deleted_at IS NULL"
        )
    )
    op.create_index("ix_spaces_tenant_status", "spaces", ["tenant_id", "status"])

    # ------------------------------------------------------ tenant_memberships
    op.create_table(
        "tenant_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # D-01: column exists, NO FK to roles (roles belongs to B1-3)
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_tm_tenant"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_tm_user"),
        sa.CheckConstraint(
            "status IN ('invited','active','suspended','removed')",
            name="ck_tenant_memberships_status",
        ),
    )
    # Historical rows are retained: (tenant_id, user_id) is UNIQUE (not partial).
    op.create_index(
        "uq_tenant_memberships", "tenant_memberships", ["tenant_id", "user_id"], unique=True
    )
    op.create_index("ix_tm_user", "tenant_memberships", ["user_id"])

    # ------------------------------------------------------------- memberships
    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # D-01: column exists, NO FK to roles
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_memberships_tenant"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="CASCADE", name="fk_memberships_space"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_memberships_user"),
        sa.CheckConstraint(
            "status IN ('invited','active','suspended','removed')",
            name="ck_memberships_status",
        ),
    )
    op.create_index(
        "uq_memberships", "memberships", ["space_id", "user_id"], unique=True,
        postgresql_where=sa.text("removed_at IS NULL"),
    )
    op.create_index("ix_memberships_tenant_user", "memberships", ["tenant_id", "user_id"])

    # ---------------------------------------------------------------- triggers
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_membership_tenant_consistency()"))
    op.execute(sa.text(_TENANT_CONSISTENCY_SQL))
    for table in _TABLES:
        op.execute(
            sa.text(
                f"CREATE TRIGGER tg_{table}_set_updated_at "
                f"BEFORE UPDATE ON {table} FOR EACH ROW "
                f"EXECUTE FUNCTION set_updated_at()"
            )
        )
    op.execute(
        sa.text(
            "CREATE TRIGGER tg_membership_tenant_consistency "
            "BEFORE INSERT OR UPDATE OF tenant_id, space_id ON memberships "
            "FOR EACH ROW EXECUTE FUNCTION enforce_membership_tenant_consistency()"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS tg_membership_tenant_consistency ON memberships"))
    for table in reversed(_TABLES):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS tg_{table}_set_updated_at ON {table}"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_membership_tenant_consistency()"))
    op.execute(sa.text("DROP TABLE IF EXISTS memberships"))
    op.execute(sa.text("DROP TABLE IF EXISTS tenant_memberships"))
    op.execute(sa.text("DROP TABLE IF EXISTS spaces"))
    op.execute(sa.text("DROP TABLE IF EXISTS tenants"))
