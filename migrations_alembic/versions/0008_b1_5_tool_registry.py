"""0008_b1_5_tool_registry — Tool Registry / Tool Versions / Tool Permissions

Revision ID: 0008_b1_5_tool_registry
Revises: 0007_b1_4_resource_acl
Create Date: 2026-09-14

Scope: B1-5 / P07 — 3 tables, 0 seed, 2 triggers, 1 enforce function.

  tools                Tool 注册表（平台级 tenant_id IS NULL / 租户级），Agent 触达业务的唯一通道
  tool_versions        Tool 契约快照（schema / risk / timeout / handler_ref / checksum），published 后不可变
  tool_permissions     「调用该 Tool 需要哪些 permissions」绑定行（P04 permissions 字典）

冻结来源（逐项核对见 docs/architecture/B1-5_SCHEMA_DESIGN.md 与 B1-5_DECISION_LOG.md）：
  * D-B15-01 = A（FROZEN）B1-5 = P07 Tool
  * D-B15-02 = A（FROZEN）tools.tenant_id NULL → tenants.id ON DELETE RESTRICT；NULL = platform-level
                            （不改 NOT NULL、不用 CASCADE/SET NULL、不取消 FK）
  * D-B15-03 = A（FROZEN）immutable trigger 统一名 tg_version_immutable（与 P09 agent_versions 共用）
  * D-B15-04 = A（FROZEN）tool_versions.status：**status CHECK = 0**；仅 published 为 immutable 语义锚点
                            （不建 enumerate CK，不自创 draft/active/disabled/archived 等词）
  * D-B15-05 = A（FROZEN）tools.key 不新增 regex/format CHECK（opaque application identifier）
  * D-B15-06 = A（FROZEN）UNIQUE CONSTRAINT = 1 · UNIQUE INDEX = 3（表达式唯一性不计入 constraint）
  * D-B15-07 = A（FROZEN）canonical B1-5 tests = 39（本 revision 不写测试）
  * D-B15-08 = A（FROZEN）不新增 snapshot value-domain CHECK（tool_versions 保持零 CK）
  * D-B15-09 = A（FROZEN）handler_ref = opaque text（不 resolve/load/execute/plugin registration）

对象计数（实测口径见 B1-5_SCHEMA_DESIGN.md §5）：
  PK = 3 · FK = 5 · CK = 5 · UNIQUE CONSTRAINT = 1 · UNIQUE INDEX = 3 · non-PK INDEX = 4

本 revision **不做任何 seed**（P00–P10 无 seed 需求；P13 才有）：
  * tools / tool_versions / tool_permissions 初始 rows 均为 0
  * 不 INSERT permissions / acl_subject_types / roles，不创建默认 Tool

边界（强制）：
  * 不含 RLS · 不含 Authorization Evaluation · 不含 ABAC / policy evaluator / role / deny resolution
  * conditions = storage-only（只存不解释）
  * 不实施 G/H/I/J（tg_acl_subject_exists / tg_acl_user_hard_delete /
    tg_acl_role_delete_block / tg_agent_acl_expire）—— 仍属 P09
  * 不含 tool_executions（属 P09，依赖 agents）
  * 不创建 agents / agent_versions / agent_permissions / ai_* / events / audit_logs / Domain 表
  * 不引入 runtime tool execution / plugin runtime / dynamic loading / handler resolution
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_b1_5_tool_registry"
down_revision = "0007_b1_4_resource_acl"
branch_labels = None
depends_on = None

_TABLES = ("tools", "tool_versions", "tool_permissions")

# 表达式唯一索引需要一个稳定的"NULL 占位"值（version_id IS NULL = 适用于全部版本）
_NIL_UUID = "00000000-0000-0000-0000-000000000000"


# --------------------------------------------------------------------------- #
# Function (1) — B1-5 implementation-level; not a new Human Decision
# --------------------------------------------------------------------------- #

# K — structural invariant only（published 快照不可改删；不做 authorization evaluation）
_VERSION_IMMUTABLE_SQL = """
CREATE FUNCTION enforce_tool_versions_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.status = 'published' THEN
      RAISE EXCEPTION
        'tool_versions: published version is immutable (DELETE denied; deprecate/revoke via application lifecycle)';
    END IF;
    RETURN OLD;
  END IF;

  IF OLD.status = 'published' THEN
    RAISE EXCEPTION
      'tool_versions: published version is immutable (UPDATE denied; deprecate/revoke via application lifecycle)';
  END IF;
  RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
    # ---------------------------------------------------------------- tools
    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        # D-B15-02 = A（FROZEN）：NULL = platform-level tool
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        # D-B15-05 = A（FROZEN）：opaque application identifier —— 无 regex/format CHECK
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=False),
        sa.Column("retry_policy", postgresql.JSONB(), nullable=True),
        sa.Column("idempotency_mode", sa.Text(), nullable=False),
        sa.Column("audit_policy", sa.Text(), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # 业务实体一律 RESTRICT（CORE §11.1 白名单不含 tenants → tools）
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT",
                                name="fk_tools_tenant"),
        sa.CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')",
                           name="ck_tools_risk_level"),
        sa.CheckConstraint("timeout_ms BETWEEN 100 AND 600000",
                           name="ck_tools_timeout"),
        sa.CheckConstraint("idempotency_mode IN ('none','key_required','natural_key')",
                           name="ck_tools_idempotency"),
        sa.CheckConstraint("audit_policy IN ('sampling','full','full_with_payload')",
                           name="ck_tools_audit_policy"),
    )

    # -------------------------------------------------------- tool_versions
    op.create_table(
        "tool_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("input_schema", postgresql.JSONB(), nullable=False),
        sa.Column("output_schema", postgresql.JSONB(), nullable=False),
        # 快照值；D-B15-08 = A（FROZEN）：本表**无** value-domain CK
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=False),
        # D-B15-09 = A（FROZEN）：opaque text（非代码路径，不解析）
        sa.Column("handler_ref", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=False),
        # D-B15-04 = A（FROZEN）：status CHECK = 0；仅 published 为 immutable 语义锚点
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        # 本表**无 updated_at** ⇒ 无 set_updated_at trigger
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # 版本快照：父实体受控 purge 时整棵删除（CORE §11.1 白名单）
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE",
                                name="fk_tool_versions_tool"),
        sa.UniqueConstraint("tool_id", "version", name="uq_tool_versions"),
    )

    # ----------------------------------------------------- tool_permissions
    op.create_table(
        "tool_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effect", sa.Text(), nullable=False),
        # storage-only（不解释，不构成 ABAC 契约）
        sa.Column("conditions", postgresql.JSONB(), nullable=True),
        # 本表**无 updated_at**
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # 配置行：随父实体受控 purge 清理（CORE §11.1 白名单）
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE",
                                name="fk_tool_permissions_tool"),
        sa.ForeignKeyConstraint(["version_id"], ["tool_versions.id"],
                                ondelete="CASCADE",
                                name="fk_tool_permissions_version"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"],
                                ondelete="CASCADE",
                                name="fk_tool_permissions_permission"),
        sa.CheckConstraint("effect IN ('allow','deny')",
                           name="ck_tool_permissions_effect"),
    )

    # -------------------------------------------------------- indexes (3 UQ)
    # 平台级 key 唯一（tenant_id IS NULL 时）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_tools_platform "
        "ON tools (lower(key)) WHERE tenant_id IS NULL"
    ))
    # 租户级 key 唯一（同租户内）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_tools_tenant "
        "ON tools (tenant_id, lower(key)) WHERE tenant_id IS NOT NULL"
    ))
    # D-B15-06 = A（FROZEN）：表达式唯一性必须是 unique INDEX，不能是 UNIQUE CONSTRAINT
    #   version_id IS NULL（适用于全部版本）与 version_id 具体值不得互相冲突
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_tool_perm "
        "ON tool_permissions ("
        "tool_id, "
        f"COALESCE(version_id, '{_NIL_UUID}'::uuid), "
        "permission_id)"
    ))

    # ----------------------------------------------------------- function (1)
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_tool_versions_immutable()"))
    op.execute(sa.text(_VERSION_IMMUTABLE_SQL))

    # ----------------------------------------------------------- triggers (2)
    # ① 复用 B1-1 set_updated_at()（不重建函数）—— tools 是 B1-5 唯一带 updated_at 的表
    op.execute(sa.text(
        "CREATE TRIGGER tg_tools_set_updated_at BEFORE UPDATE ON tools "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    # ② D-B15-03 = A（FROZEN）—— published 快照不可改删（structural invariant only）
    op.execute(sa.text(
        "CREATE TRIGGER tg_version_immutable "
        "BEFORE UPDATE OR DELETE ON tool_versions "
        "FOR EACH ROW EXECUTE FUNCTION enforce_tool_versions_immutable()"
    ))

    # 无 seed（B1-5 = P07；三表初始 rows = 0）


def downgrade() -> None:
    # [1] dependent triggers
    for trigger, table in (
        ("tg_version_immutable", "tool_versions"),
        ("tg_tools_set_updated_at", "tools"),
    ):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger} ON {table}"))

    # [2] function（仅 B1-5 新建；不 DROP set_updated_at / uap_uuid_v7）
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_tool_versions_immutable()"))

    # [3] dependent indexes（在 DROP TABLE 之前显式移除；uq_tool_versions 随表移除）
    for index in ("uq_tool_perm", "uq_tools_tenant", "uq_tools_platform"):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index}"))

    # [4] tables（逆依赖序）
    for table in reversed(_TABLES):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
