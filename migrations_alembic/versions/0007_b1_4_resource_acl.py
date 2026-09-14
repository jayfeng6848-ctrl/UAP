"""0007_b1_4_resource_acl — Resource Registry / ACL Subject Registry / Resource ACL

Revision ID: 0007_b1_4_resource_acl
Revises: 0006_b1_3_bootstrap_state
Create Date: 2026-09-14

Scope: B1-4 / P06 — 3 tables, 0 seed, 3 triggers, 2 enforce functions.

  resources              通用资源注册表（授权对象侧）
  acl_subject_types      ACL 主体类型注册表（ROOT，平台受控）
  resource_permissions   资源级 ACL（实例级 allow/deny）

冻结来源（逐项核对见 docs/architecture/B1-4_SCHEMA_DESIGN.md）：
  * D-B14-08 = A（FROZEN）action = NOT NULL + 既有 UQ，**零新增 semantic/format contract**
  * D-B14-09 = A（FROZEN）granted_by → users.id ON DELETE SET NULL（语义 = actor attribution，非 ownership）
  * D-B14-10 = A-1（FROZEN）tg_resources_tenant_space_consistency（structural integrity only）
  * D-B14-12 = A（FROZEN）tg_acl_subject_types_protect（registry governance only）
  * D-B14-01 / D-B14-02（RESOLVED BY FROZEN TEXT）B1-4 零 seed；G/H/I/J 最早 P09 后，本 revision 不实施

本 revision **不做任何 seed**：
  * `acl_subject_types` 三行（user/role/agent）属 **P13**（P00–P10 无 seed 需求）
  * `resource_permissions` 行因 `acl_subject_types` 为空而 FK 不可满足 → 物理不可写入
  * 合法 registry 行**仅经 migration 建立**（schema governance，非 Domain runtime registration）。
    既有先例：0005 先 INSERT 内置 role → 后建 tg_roles_is_system_protect；
              0006 先 INSERT platform_state → 后建 tg_platform_state_guard。
    P13 的受控写入路径见 docs/architecture/B1-4_DESIGN.md §8.1（候选 M-1：迁移内
    DISABLE TRIGGER → INSERT → ENABLE TRIGGER）。

边界（强制）：
  * 不含 RLS · 不含 Authorization Evaluation · 不含 Role/Deny Resolution
  * 不实施 G/H/I/J（tg_acl_subject_exists / tg_acl_user_hard_delete /
    tg_acl_role_delete_block / tg_agent_acl_expire）
  * 不创建 permissions / groups / audit_logs / agents / tools / AI / events / Domain 表
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_b1_4_resource_acl"
down_revision = "0006_b1_3_bootstrap_state"
branch_labels = None
depends_on = None

_TABLES = ("resources", "acl_subject_types", "resource_permissions")


# --------------------------------------------------------------------------- #
# Functions (2) — B1-4 implementation-level; not new Human Decisions
# --------------------------------------------------------------------------- #

# F2 — structural integrity only（不做 authorization evaluation，不引入 RLS）
_RES_TENANT_SPACE_SQL = """
CREATE FUNCTION enforce_resources_tenant_space_consistency() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  space_tenant uuid;
BEGIN
  IF NEW.space_id IS NOT NULL THEN
    SELECT tenant_id INTO space_tenant FROM spaces WHERE id = NEW.space_id;
    IF space_tenant IS NULL THEN
      RAISE EXCEPTION 'resources.space_id % does not exist', NEW.space_id;
    END IF;
    IF NEW.tenant_id IS DISTINCT FROM space_tenant THEN
      RAISE EXCEPTION
        'resources.tenant_id % does not match spaces.tenant_id % (cross-tenant resource denied)',
        NEW.tenant_id, space_tenant;
    END IF;
  END IF;
  -- 仅做结构完整性校验：不写其它表、不做授权判定、不做级联、不写审计
  RETURN NEW;
END;
$$;
"""

# C2 — registry governance only（不演变为 Domain authorization）
_ACL_SUBJECT_TYPES_PROTECT_SQL = """
CREATE FUNCTION enforce_acl_subject_types_protect() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    RAISE EXCEPTION
      'acl_subject_types is a platform-controlled registry: runtime INSERT denied '
      '(registry rows are migration-controlled)';
  ELSIF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION
      'acl_subject_types rows cannot be deleted (retire via archived_at)';
  ELSE  -- UPDATE
    IF NEW.key IS DISTINCT FROM OLD.key THEN
      RAISE EXCEPTION 'acl_subject_types.key is immutable (registry governance)';
    END IF;
    RETURN NEW;
  END IF;
END;
$$;
"""


# --------------------------------------------------------------------------- #
# upgrade
# --------------------------------------------------------------------------- #

def upgrade() -> None:
    # ------------------------------------------------------------- resources
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("natural_key", sa.Text(), nullable=True),
        sa.Column("classification", sa.Text(), nullable=False,
                  server_default=sa.text("'INTERNAL'")),
        sa.Column("status", sa.Text(), nullable=False,
                  server_default=sa.text("'active'")),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # P2-03: 父表删除一律 RESTRICT（必须走 archive → soft delete → retention → purge）
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT",
                                name="fk_resources_tenant"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="RESTRICT",
                                name="fk_resources_space"),
        # owner 删除不得删除资源
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL",
                                name="fk_resources_owner"),
        # resource_type 为开放格式（非 Domain 枚举）——仅格式约束
        sa.CheckConstraint("resource_type ~ '^[a-z][a-z0-9_.]{1,63}$'",
                           name="ck_resources_type"),
        sa.CheckConstraint(
            "classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')",
            name="ck_resources_classification",
        ),
        sa.CheckConstraint("status IN ('active','archived','deleted')",
                           name="ck_resources_status"),
    )

    # ------------------------------------------------------ acl_subject_types
    op.create_table(
        "acl_subject_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        # P2-02: 白名单不含 group
        sa.CheckConstraint("key ~ '^[a-z][a-z0-9_]{1,31}$'",
                           name="ck_acl_subject_types_key"),
        sa.CheckConstraint("key IN ('user','role','agent')",
                           name="ck_acl_subject_types_whitelist"),
    )

    # ---------------------------------------------------- resource_permissions
    op.create_table(
        "resource_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        # D-B14-08 = A（FROZEN）：opaque action identifier —— 仅 NOT NULL，零新增 CK/词表
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("effect", sa.Text(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), nullable=True),
        sa.Column("inherited", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        # D-B14-09 = A（FROZEN）：actor attribution（非 ownership）
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # 受控 purge 白名单：ACL 是资源的纯技术从属
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE",
                                name="fk_resource_permissions_resource"),
        sa.ForeignKeyConstraint(["subject_type_id"], ["acl_subject_types.id"],
                                ondelete="RESTRICT",
                                name="fk_resource_permissions_subject_type"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="SET NULL",
                                name="fk_resource_permissions_granted_by"),
        sa.UniqueConstraint("resource_id", "subject_type_id", "subject_id", "action",
                            name="uq_resource_perm"),
        sa.CheckConstraint("effect IN ('allow','deny')",
                           name="ck_resource_permissions_effect"),
    )

    # ----------------------------------------------------------- indexes (8)
    # 部分唯一（排除软删与空 natural_key）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_resources_natural "
        "ON resources (tenant_id, resource_type, natural_key) "
        "WHERE natural_key IS NOT NULL AND deleted_at IS NULL"
    ))
    op.create_index("ix_res_tenant_space_type_status", "resources",
                    ["tenant_id", "space_id", "resource_type", "status"])
    op.create_index("ix_res_tenant_owner", "resources", ["tenant_id", "owner_id"])
    op.execute(sa.text(
        "CREATE INDEX ix_res_tenant_type_created "
        "ON resources (tenant_id, resource_type, created_at DESC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_res_tenant_deleted "
        "ON resources (tenant_id, deleted_at) WHERE deleted_at IS NOT NULL"
    ))
    # 归档后同名 key 可重建（lower() 归一，不使用 citext）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_acl_subject_types_key "
        "ON acl_subject_types (lower(key)) WHERE archived_at IS NULL"
    ))
    op.create_index("ix_rp_subject", "resource_permissions",
                    ["subject_type_id", "subject_id"])
    # uq_resource_perm 由 create_table 内联 UNIQUE 约束承载（第 8 个索引对象）

    # ---------------------------------------------------------- functions (2)
    for name, sql in (
        ("enforce_resources_tenant_space_consistency", _RES_TENANT_SPACE_SQL),
        ("enforce_acl_subject_types_protect", _ACL_SUBJECT_TYPES_PROTECT_SQL),
    ):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {name}()"))
        op.execute(sa.text(sql))

    # ----------------------------------------------------------- triggers (3)
    # ① 复用 B1-1 set_updated_at()（不重建函数）
    op.execute(sa.text(
        "CREATE TRIGGER tg_resources_set_updated_at BEFORE UPDATE ON resources "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    # ② D-B14-10 = A-1（F2）—— 覆盖 INSERT 与 UPDATE
    op.execute(sa.text(
        "CREATE TRIGGER tg_resources_tenant_space_consistency "
        "BEFORE INSERT OR UPDATE ON resources "
        "FOR EACH ROW EXECUTE FUNCTION enforce_resources_tenant_space_consistency()"
    ))
    # ③ D-B14-12 = A（C2）—— registry governance only
    op.execute(sa.text(
        "CREATE TRIGGER tg_acl_subject_types_protect "
        "BEFORE INSERT OR UPDATE OR DELETE ON acl_subject_types "
        "FOR EACH ROW EXECUTE FUNCTION enforce_acl_subject_types_protect()"
    ))

    # 无 seed（B1-4 = P06；acl_subject_types 初始 rows = 0）


# --------------------------------------------------------------------------- #
# downgrade（严格反向；不留下 orphan objects）
# --------------------------------------------------------------------------- #

def downgrade() -> None:
    # [1] dependent triggers
    for trigger, table in (
        ("tg_acl_subject_types_protect", "acl_subject_types"),
        ("tg_resources_tenant_space_consistency", "resources"),
        ("tg_resources_set_updated_at", "resources"),
    ):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger} ON {table}"))

    # [2] functions（仅 B1-4 新建的 enforce_*；不 DROP set_updated_at / uap_uuid_v7）
    for fn in (
        "enforce_acl_subject_types_protect",
        "enforce_resources_tenant_space_consistency",
    ):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {fn}()"))

    # [3] dependent indexes（在 DROP TABLE 之前显式移除）
    for index in (
        "ix_rp_subject",
        "uq_acl_subject_types_key",
        "ix_res_tenant_deleted",
        "ix_res_tenant_type_created",
        "ix_res_tenant_owner",
        "ix_res_tenant_space_type_status",
        "uq_resources_natural",
    ):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index}"))

    # [4][5][6] tables（逆依赖序；uq_resource_perm 随表移除）
    for table in reversed(_TABLES):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
