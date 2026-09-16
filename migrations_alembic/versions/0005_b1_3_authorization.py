"""0005_b1_3_authorization — Role & Permission Foundation + Platform Membership

Revision ID: 0005_b1_3_authorization
Revises: 0004_b1_2_tenant_space
Create Date: 2026-09-08

Scope: B1-3（仅 4 张表）
  roles / permissions / role_permissions / platform_memberships
+ 冻结约束 / 索引 / trigger（T1–T8）
+ 系统角色 seed（幂等，transaction-safe）
+ B1-2 遗留 role_id 回填 + 硬门禁校验 + SET NOT NULL + ADD FK（D-08）
+ D-07 platform_memberships（Option A + PMB-1..4）

冻结来源（逐字段/约束核对）：
  * CORE_DOMAIN_MODEL §1.2（roles/permissions/role_permissions/platform_memberships）
  * STEP1B_B1_3_SCHEMA_REVIEW / CONSTRAINT_MATRIX / INDEX_STRATEGY / TRIGGER_INVENTORY
  * STEP1B_B1_3_DECISION_LOG R2-D-05/R-D-06/R2-D-08/R2-D-13/R2-D-14/R2-D-15/R2-D-16
    + R3-D-07（Option A）+ R4 PMB-1..4

关键实施要点（与冻结决策一一对应）：
  * 唯一谓词终版（R3 修正后）：PLATFORM = tenant_id IS NULL AND space_id IS NULL；
    TENANT = tenant_id IS NOT NULL AND space_id IS NULL；SPACE = space_id IS NOT NULL
  * scope 形状由 trigger 强制（tg_roles_scope_shape）
  * 系统角色保护 tg_roles_is_system_protect = INSERT/UPDATE/DELETE 三路径
    （INSERT NEW.is_system / UPDATE-DELETE OLD.is_system OR NEW.is_system）→ seed 必须先于该 trigger
  * role.status ∈ active/disabled/archived 默认 active；绑定 trigger 要求 status='active'
  * 回填 = tenant_member / space_member（同租户/同空间）；removed 历史行与 archived tenant/space 均回填；
    硬门禁（NULL 残留 / scope 错配 / 跨租户·跨空间）→ RAISE → 整体回滚（D-08/R2-D-08）
  * role_permissions PK = (role_id, permission_id, effect)，effect allow/deny；
    conditions 仅 storage-only；两侧 CASCADE
  * platform_memberships（D-07 Option A）：user CASCADE / role RESTRICT；UQ(user_id,role_id) +
    partial UQ(user_id) WHERE status='active'；re-grant = UPDATE 本行（PMB-3）
  * trigger：tg_pm_role_scope（仅 PLATFORM role 且 active；user active）、tg_pm_last_admin（PMB-1 PM 侧）、
    tg_roles_pm_lifecycle（PMB-1 Role 侧，有 active 绑定时禁止 platform_admin 行 status 离开 active / DELETE）
  * permissions 字典本轮 seed 0 行（冻结清单未定稿，见 SEED_STRATEGY §4：仅定形状、清单待人工审计）
  * 本 migration 不实现 bootstrap 写入（platform_memberships 保持 0 行；bootstrap = 部署期受信 CLI，PMB-2）
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_b1_3_authorization"
down_revision = "0004_b1_2_tenant_space"
branch_labels = None
depends_on = None

# --------------------------------------------------------------------------- #
# 角色显示名（seed 用，确定性；系统角色 key 不变）
_SYSTEM_ROLE_NAMES = {
    "platform_admin": "Platform Admin",
    "tenant_admin": "Tenant Admin",
    "tenant_member": "Tenant Member",
    "space_admin": "Space Admin",
    "space_member": "Space Member",
}

_T2_SCOPE_SHAPE_SQL = """
CREATE FUNCTION enforce_roles_scope_shape() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.scope = 'PLATFORM' THEN
    IF NEW.tenant_id IS NOT NULL OR NEW.space_id IS NOT NULL THEN
      RAISE EXCEPTION 'PLATFORM role must have tenant_id IS NULL AND space_id IS NULL (scope shape)';
    END IF;
  ELSIF NEW.scope = 'TENANT' THEN
    IF NEW.tenant_id IS NULL OR NEW.space_id IS NOT NULL THEN
      RAISE EXCEPTION 'TENANT role must have tenant_id NOT NULL AND space_id IS NULL (scope shape)';
    END IF;
  ELSIF NEW.scope = 'SPACE' THEN
    IF NEW.tenant_id IS NOT NULL OR NEW.space_id IS NULL THEN
      RAISE EXCEPTION 'SPACE role must have tenant_id IS NULL AND space_id NOT NULL (scope shape)';
    END IF;
  ELSE
    RAISE EXCEPTION 'invalid roles.scope % (scope shape)', NEW.scope;
  END IF;
  RETURN NEW;
END;
$$;
"""

_T3_SYSTEM_PROTECT_SQL = """
CREATE FUNCTION enforce_roles_is_system_protect() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.is_system THEN
      RAISE EXCEPTION 'system roles cannot be created at runtime (is_system=true)';
    END IF;
  ELSE  -- UPDATE / DELETE
    IF OLD.is_system OR NEW.is_system THEN
      RAISE EXCEPTION 'system role rows are immutable (UPDATE/DELETE denied; no is_system transition)';
    END IF;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;
"""

_T4_TM_ROLE_SCOPE_SQL = """
CREATE FUNCTION enforce_tm_role_scope() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  r_scope text;
  r_tenant uuid;
  r_active boolean;
BEGIN
  IF NEW.role_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT scope, tenant_id, status = 'active'
    INTO r_scope, r_tenant, r_active
    FROM roles WHERE id = NEW.role_id;
  IF r_scope IS NULL THEN
    RAISE EXCEPTION 'tenant_memberships.role_id % does not exist', NEW.role_id;
  END IF;
  IF NOT (r_scope = 'TENANT' AND r_tenant = NEW.tenant_id AND r_active) THEN
    RAISE EXCEPTION
      'tenant_memberships may only reference an active TENANT role of the same tenant (got scope=%, role tenant mismatch or inactive)',
      r_scope;
  END IF;
  RETURN NEW;
END;
$$;
"""

_T5_MEMBERSHIP_ROLE_SCOPE_SQL = """
CREATE FUNCTION enforce_membership_role_scope() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  r_scope text;
  r_space uuid;
  r_active boolean;
BEGIN
  IF NEW.role_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT scope, space_id, status = 'active'
    INTO r_scope, r_space, r_active
    FROM roles WHERE id = NEW.role_id;
  IF r_scope IS NULL THEN
    RAISE EXCEPTION 'memberships.role_id % does not exist', NEW.role_id;
  END IF;
  IF NOT (r_scope = 'SPACE' AND r_space = NEW.space_id AND r_active) THEN
    RAISE EXCEPTION
      'memberships may only reference an active SPACE role of the same space (got scope=%, role space mismatch or inactive)',
      r_scope;
  END IF;
  RETURN NEW;
END;
$$;
"""

_T6_PM_ROLE_SCOPE_SQL = """
CREATE FUNCTION enforce_pm_role_scope() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  r_scope text;
  r_active boolean;
  u_active boolean;
BEGIN
  SELECT scope, status = 'active' INTO r_scope, r_active FROM roles WHERE id = NEW.role_id;
  IF r_scope IS NULL THEN
    RAISE EXCEPTION 'platform_memberships.role_id % does not exist', NEW.role_id;
  END IF;
  IF NOT (r_scope = 'PLATFORM' AND r_active) THEN
    RAISE EXCEPTION
      'platform_memberships may only reference an active PLATFORM role (got scope=%)', r_scope;
  END IF;
  IF NEW.status = 'active' THEN
    SELECT status = 'active' INTO u_active FROM users WHERE id = NEW.user_id;
    IF NOT COALESCE(u_active, false) THEN
      RAISE EXCEPTION 'platform_memberships cannot bind an inactive or missing user';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
"""

_T7_PM_LAST_ADMIN_SQL = """
CREATE FUNCTION enforce_pm_last_admin() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  old_eff boolean;
  new_eff boolean;
  other_active bigint;
BEGIN
  old_eff := (OLD.status = 'active') AND EXISTS (
      SELECT 1 FROM roles r WHERE r.id = OLD.role_id
        AND r.scope = 'PLATFORM' AND r.key = 'platform_admin');
  IF TG_OP = 'DELETE' THEN
    new_eff := false;
  ELSE
    new_eff := (NEW.status = 'active') AND EXISTS (
        SELECT 1 FROM roles r WHERE r.id = NEW.role_id
          AND r.scope = 'PLATFORM' AND r.key = 'platform_admin');
  END IF;

  IF old_eff AND NOT new_eff THEN
    SELECT count(*) INTO other_active FROM platform_memberships pm
      JOIN roles r ON pm.role_id = r.id
     WHERE pm.status = 'active' AND r.scope = 'PLATFORM' AND r.key = 'platform_admin'
       AND pm.id <> OLD.id;
    IF other_active = 0 THEN
      RAISE EXCEPTION
        'cannot revoke/delete the last active platform_admin binding (PMB-1; transfer first or bootstrap a replacement)';
    END IF;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;
"""

_T8_ROLES_PM_LIFECYCLE_SQL = """
CREATE FUNCTION enforce_roles_pm_lifecycle() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT (OLD.scope = 'PLATFORM' AND OLD.key = 'platform_admin') THEN
    RETURN COALESCE(NEW, OLD);  -- 仅保护平台信任根角色行
  END IF;
  IF TG_OP = 'DELETE' OR (TG_OP = 'UPDATE' AND NEW.status IS DISTINCT FROM 'active') THEN
    IF EXISTS (
        SELECT 1 FROM platform_memberships pm
         WHERE pm.role_id = OLD.id AND pm.status = 'active'
    ) THEN
      RAISE EXCEPTION
        'platform_admin role cannot leave active while active platform bindings exist (PMB-1 role side)';
    END IF;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;
"""

_BACKFILL_VALIDATION_SQL = """
DO $$
DECLARE
  null_tm bigint;
  null_m  bigint;
  bad_tm  bigint;
  bad_m   bigint;
BEGIN
  SELECT count(*) INTO null_tm FROM tenant_memberships WHERE role_id IS NULL;
  SELECT count(*) INTO null_m  FROM memberships        WHERE role_id IS NULL;
  IF null_tm > 0 OR null_m > 0 THEN
    RAISE EXCEPTION 'backfill failed: % tenant_memberships and % memberships still have NULL role_id', null_tm, null_m;
  END IF;

  SELECT count(*) INTO bad_tm FROM tenant_memberships tm
    LEFT JOIN roles r ON tm.role_id = r.id
   WHERE r.id IS NULL OR NOT (r.scope = 'TENANT' AND r.tenant_id = tm.tenant_id);
  SELECT count(*) INTO bad_m FROM memberships m
    LEFT JOIN roles r ON m.role_id = r.id
   WHERE r.id IS NULL OR NOT (r.scope = 'SPACE' AND r.space_id = m.space_id);
  IF bad_tm > 0 OR bad_m > 0 THEN
    RAISE EXCEPTION 'backfill validation failed: % tenant_memberships and % memberships reference a missing/out-of-scope role (fail closed)', bad_tm, bad_m;
  END IF;
END;
$$;
"""


def _seed_system_roles() -> None:
    """幂等 seed：platform_admin 全局 1 行；既有每个 tenant/space 补种两级角色。"""
    # PLATFORM（全局单例；部分唯一谓词含 AND space_id IS NULL）
    op.execute(
        sa.text(
            "INSERT INTO roles (id, tenant_id, space_id, key, name, scope, is_system, status) "
            "SELECT uap_uuid_v7(), NULL, NULL, 'platform_admin', :name, 'PLATFORM', true, 'active' "
            "WHERE NOT EXISTS (SELECT 1 FROM roles "
            "WHERE tenant_id IS NULL AND space_id IS NULL AND key = 'platform_admin')"
        ).bindparams(name=_SYSTEM_ROLE_NAMES["platform_admin"])
    )
    # 既有 tenants：tenant_admin / tenant_member
    for key in ("tenant_admin", "tenant_member"):
        op.execute(
            sa.text(
                "INSERT INTO roles (id, tenant_id, space_id, key, name, scope, is_system, status) "
                "SELECT uap_uuid_v7(), t.id, NULL, :key, :name, 'TENANT', true, 'active' "
                "FROM tenants t WHERE NOT EXISTS (SELECT 1 FROM roles r "
                "WHERE r.tenant_id = t.id AND r.space_id IS NULL AND r.key = :key)"
            ).bindparams(key=key, name=_SYSTEM_ROLE_NAMES[key])
        )
    # 既有 spaces：space_admin / space_member
    for key in ("space_admin", "space_member"):
        op.execute(
            sa.text(
                "INSERT INTO roles (id, tenant_id, space_id, key, name, scope, is_system, status) "
                "SELECT uap_uuid_v7(), NULL, s.id, :key, :name, 'SPACE', true, 'active' "
                "FROM spaces s WHERE NOT EXISTS (SELECT 1 FROM roles r "
                "WHERE r.space_id = s.id AND r.key = :key)"
            ).bindparams(key=key, name=_SYSTEM_ROLE_NAMES[key])
        )


def _backfill_membership_roles() -> None:
    """回填 B1-2 遗留 role_id（removed/archived 行也覆盖；任何残留/错配在验证阶段 RAISE）。"""
    op.execute(
        sa.text(
            "UPDATE tenant_memberships tm SET role_id = ("
            "  SELECT r.id FROM roles r WHERE r.tenant_id = tm.tenant_id"
            "    AND r.scope = 'TENANT' AND r.key = 'tenant_member' AND r.status = 'active'"
            ") WHERE tm.role_id IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE memberships m SET role_id = ("
            "  SELECT r.id FROM roles r WHERE r.space_id = m.space_id"
            "    AND r.scope = 'SPACE' AND r.key = 'space_member' AND r.status = 'active'"
            ") WHERE m.role_id IS NULL"
        )
    )


def upgrade() -> None:
    # ---------------------------------------------------------------- permissions
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(r"key ~ '^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$'", name="ck_permissions_key"),
    )
    op.create_index("uq_permissions_key", "permissions", ["key"], unique=True)

    # ------------------------------------------------------------------- roles
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_roles_tenant"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="CASCADE", name="fk_roles_space"),
        sa.CheckConstraint("scope IN ('PLATFORM','TENANT','SPACE')", name="ck_roles_scope"),
        sa.CheckConstraint("status IN ('active','disabled','archived')", name="ck_roles_status"),
        sa.CheckConstraint("key ~ '^[a-z][a-z0-9_]{1,63}$'", name="ck_roles_key"),
    )
    # 三条互斥的部分唯一索引（终版谓词，R3 修正：PLATFORM 含 AND space_id IS NULL）
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_roles_platform ON roles (lower(key)) "
            "WHERE tenant_id IS NULL AND space_id IS NULL"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_roles_tenant ON roles (tenant_id, lower(key)) "
            "WHERE tenant_id IS NOT NULL AND space_id IS NULL"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_roles_space ON roles (space_id, lower(key)) "
            "WHERE space_id IS NOT NULL"
        )
    )

    # ------------------------------------------------------------ role_permissions
    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effect", sa.Text(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("role_id", "permission_id", "effect", name="pk_role_permissions"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE", name="fk_role_permissions_role"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE", name="fk_role_permissions_permission"),
        sa.CheckConstraint("effect IN ('allow','deny')", name="ck_role_permissions_effect"),
    )
    # permission 侧删除（CASCADE）需反查
    op.create_index("ix_role_permissions_permission", "role_permissions", ["permission_id"])

    # ------------------------------------------------------- 系统角色 seed（先于保护 trigger）
    _seed_system_roles()

    # ------------------------------------------------------- roles/scope/membership triggers
    for name, sql in (
        ("enforce_roles_scope_shape", _T2_SCOPE_SHAPE_SQL),
        ("enforce_roles_is_system_protect", _T3_SYSTEM_PROTECT_SQL),
        ("enforce_tm_role_scope", _T4_TM_ROLE_SCOPE_SQL),
        ("enforce_membership_role_scope", _T5_MEMBERSHIP_ROLE_SCOPE_SQL),
    ):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {name}()"))
        op.execute(sa.text(sql))

    op.execute(sa.text(
        "CREATE TRIGGER tg_roles_set_updated_at BEFORE UPDATE ON roles "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_roles_scope_shape BEFORE INSERT OR UPDATE OF scope, tenant_id, space_id ON roles "
        "FOR EACH ROW EXECUTE FUNCTION enforce_roles_scope_shape()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_roles_is_system_protect BEFORE INSERT OR UPDATE OR DELETE ON roles "
        "FOR EACH ROW EXECUTE FUNCTION enforce_roles_is_system_protect()"
    ))
    # 绑定校验 trigger（roles 表已建）—— 在回填前生效，非法写入即失败
    op.execute(sa.text(
        "CREATE TRIGGER tg_tm_role_scope BEFORE INSERT OR UPDATE OF role_id, tenant_id ON tenant_memberships "
        "FOR EACH ROW EXECUTE FUNCTION enforce_tm_role_scope()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_membership_role_scope BEFORE INSERT OR UPDATE OF role_id, space_id ON memberships "
        "FOR EACH ROW EXECUTE FUNCTION enforce_membership_role_scope()"
    ))

    # ------------------------------------------------------- 回填 + 硬门禁（D-08）
    _backfill_membership_roles()
    op.execute(sa.text(_BACKFILL_VALIDATION_SQL))

    # ------------------------------------------------------- role_id: SET NOT NULL + ADD FK
    op.execute(sa.text("ALTER TABLE tenant_memberships ALTER COLUMN role_id SET NOT NULL"))
    op.execute(sa.text("ALTER TABLE memberships ALTER COLUMN role_id SET NOT NULL"))
    op.execute(sa.text(
        "ALTER TABLE tenant_memberships ADD CONSTRAINT fk_tm_role "
        "FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT"
    ))
    op.execute(sa.text(
        "ALTER TABLE memberships ADD CONSTRAINT fk_membership_role "
        "FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT"
    ))
    op.create_index("ix_tenant_memberships_role", "tenant_memberships", ["role_id"])
    op.create_index("ix_memberships_role", "memberships", ["role_id"])

    # ------------------------------------------------------- platform_memberships（D-07 Option A）
    op.create_table(
        "platform_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_pm_user"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT", name="fk_pm_role"),
        sa.CheckConstraint("status IN ('active','revoked')", name="ck_platform_memberships_status"),
    )
    op.create_index(
        "uq_platform_memberships_user_role", "platform_memberships", ["user_id", "role_id"], unique=True
    )
    op.create_index(
        "uq_platform_memberships_active_user", "platform_memberships", ["user_id"], unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_platform_memberships_role_status", "platform_memberships", ["role_id", "status"],
        postgresql_where=sa.text("status = 'active'"),
    )

    for name, sql in (
        ("enforce_pm_role_scope", _T6_PM_ROLE_SCOPE_SQL),
        ("enforce_pm_last_admin", _T7_PM_LAST_ADMIN_SQL),
        ("enforce_roles_pm_lifecycle", _T8_ROLES_PM_LIFECYCLE_SQL),
    ):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {name}()"))
        op.execute(sa.text(sql))

    op.execute(sa.text(
        "CREATE TRIGGER tg_platform_memberships_set_updated_at BEFORE UPDATE ON platform_memberships "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_pm_role_scope BEFORE INSERT OR UPDATE OF role_id, status ON platform_memberships "
        "FOR EACH ROW EXECUTE FUNCTION enforce_pm_role_scope()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_pm_last_admin BEFORE UPDATE OR DELETE ON platform_memberships "
        "FOR EACH ROW EXECUTE FUNCTION enforce_pm_last_admin()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_roles_pm_lifecycle BEFORE UPDATE OF status OR DELETE ON roles "
        "FOR EACH ROW EXECUTE FUNCTION enforce_roles_pm_lifecycle()"
    ))


def downgrade() -> None:
    # ------------------------------------------------------- triggers / functions
    for trigger, table in (
        ("tg_roles_pm_lifecycle", "roles"),
        ("tg_pm_last_admin", "platform_memberships"),
        ("tg_pm_role_scope", "platform_memberships"),
        ("tg_platform_memberships_set_updated_at", "platform_memberships"),
        ("tg_membership_role_scope", "memberships"),
        ("tg_tm_role_scope", "tenant_memberships"),
        ("tg_roles_is_system_protect", "roles"),
        ("tg_roles_scope_shape", "roles"),
        ("tg_roles_set_updated_at", "roles"),
    ):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger} ON {table}"))
    for fn in (
        "enforce_roles_pm_lifecycle",
        "enforce_pm_last_admin",
        "enforce_pm_role_scope",
        "enforce_membership_role_scope",
        "enforce_tm_role_scope",
        "enforce_roles_is_system_protect",
        "enforce_roles_scope_shape",
    ):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {fn}()"))

    # ------------------------------------------------------- 恢复 0004 形态
    op.execute(sa.text("ALTER TABLE memberships DROP CONSTRAINT IF EXISTS fk_membership_role"))
    op.execute(sa.text("ALTER TABLE tenant_memberships DROP CONSTRAINT IF EXISTS fk_tm_role"))
    op.execute(sa.text("ALTER TABLE memberships ALTER COLUMN role_id DROP NOT NULL"))
    op.execute(sa.text("ALTER TABLE tenant_memberships ALTER COLUMN role_id DROP NOT NULL"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_memberships_role"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_tenant_memberships_role"))

    # ------------------------------------------------------- 表（反向）
    op.execute(sa.text("DROP TABLE IF EXISTS platform_memberships"))
    op.execute(sa.text("DROP TABLE IF EXISTS role_permissions"))
    op.execute(sa.text("DROP TABLE IF EXISTS roles"))
    op.execute(sa.text("DROP TABLE IF EXISTS permissions"))
