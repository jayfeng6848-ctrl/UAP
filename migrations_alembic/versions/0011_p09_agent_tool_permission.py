"""0011_p09_agent_tool_permission — Agent / Agent Versions / Agent Permissions / Tool Executions

Revision ID: 0011_p09_agent_tool_permission
Revises: 0010_b1_6_ai_gateway
Create Date: 2026-09-18

Scope: P09 — 4 tables, 0 seed, 3 triggers, 2 functions, 1 deferred-created FK.

  agents             执行实体（编排工具、策略与模型路由），**不是模型**
  agent_versions     Agent 定义的不可变快照（published 后不可改删）
  agent_permissions  Agent 白名单（权限 / 工具 / 资源范围）—— "Agent 无 DB 权限"的数据表达
  tool_executions    执行记录 + 幂等锚点 + 重试依据（**不分区**，90 天 hard delete）

冻结来源（逐项核对见 docs/architecture/P09_DECISION_LOG.md / P09_SCHEMA_DESIGN.md /
P09_MIGRATION_PLAN.md / P09_TEST_MATRIX.md）：
  * D-P09-01 = B（FROZEN）tool_executions **不分区**；PK = id；保留 = 90 天 hard delete
                          （executor 不属 P09 —— DESIGN DEFERRED / 手工运维，D-3 = D 先例）
  * D-P09-02 = A（FROZEN）tool_executions.tenant_id NOT NULL → tenants.id ON DELETE RESTRICT
  * D-P09-03（FROZEN）16 条 FK 的 ON DELETE：F1/F2/F3/F12 = RESTRICT · F7/F15/F16 = SET NULL ·
                      F10/F11 = CASCADE（既有：F4/F5 SET NULL · F6/F8/F9 CASCADE · F13/F14 RESTRICT）
                      ⇒ tool_executions 的 5 条 FK 中 **CASCADE = 0**（历史记录不被级联清除）
  * D-P09-04 = A（FROZEN）uq_tool_exec_idem = **UNIQUE INDEX**（部分谓词），不得伪装为 UNIQUE CONSTRAINT
  * D-P09-05 = B（FROZEN）agent_permissions = **2 条 CHECK**（scope target + effect），不得合并
  * D-P09-06 = A（FROZEN）G/H/I/J 属 **P09 后** —— 本 revision 不实施
  * D-P09-07 = A（FROZEN）P09 = **SCHEMA ONLY**：不修改 agent/ · 不引入任何 Runtime / API / worker
  * D-P09-09（FROZEN）revision = 0011_p09_agent_tool_permission（filename == revision · ≤32 · 单头）
  * D-P09-10（FROZEN）ai_request_logs.agent_id 维持 **NO FK**（P08 → P09 forward FK = 0）
  * D-P09-11 = A（FROZEN）deferred FK 采用 0005 同构：**最后 ADD** · downgrade **首先 DROP 该约束**
  * D-P09-12 = A（FROZEN）agents tenant/space consistency trigger（**structural integrity only**）
  * D-P09-13（ND-01）tool_executions = 3 条 CHECK（status / attempts>=1 / duration_ms>=0）
  * D-P09-14 = A（ND-02）agent_versions published 行 UPDATE/DELETE **均 RAISE**（无迁移豁免；沿用 0008 同构）
  * D-P09-15（ND-03）索引权威 = STEP1B_INDEX_STRATEGY；交付 **8 个索引对象**；不额外补 FK 列索引
  * D-P09-16（ND-04）UNIQUE CONSTRAINT = 1（uq_agent_versions）· UNIQUE INDEX = 3
  * D-P09-17 = A（ND-05）不修改 0008 / 任何已发布 migration
  * D-P09-18（ND-06）最小补注包（CM ×3 / CORE ×1）已执行 —— 本 revision 按其语义实现
  * DESIGN WRITE（DESIGN RESOLVED，非 Human Decision）：
      - 列类型 / DEFAULT 矩阵（54 列；时间列一律 timestamptz(3)）—— P09_SCHEMA_DESIGN.md §2B.1
      - 对象命名表（FK 16 / CK 8 / 索引 8 / trigger 3 / function 2）—— §2B.2
      - U-2 trigger 名与语义 §2B.3 · NU-07 immutability 函数 §2B.4 · U-3 八个 CHECK 名 §2B.5
      - NU-09 CK-1 边界 = 纯 IS NOT NULL（**不**追加 `<> ''` —— Human ACK: FROZEN AS NO-TIGHTENING）
      - ND-B Human ACK: FROZEN AS NON-DEFERRABLE（该 FK **不带** DEFERRABLE / INITIALLY DEFERRED；
        "deferred" 指**最后创建**的 migration 顺序，不是 PostgreSQL DEFERRABLE）

对象计数（实测口径见 P09_SCHEMA_DESIGN.md §2B.8）：
  PK = 4 · 列 = 54 · FK = 16（CASCADE 5 / RESTRICT 6 / SET NULL 5）· CK = 8 ·
  UNIQUE CONSTRAINT = 1 · UNIQUE INDEX = 3 · non-PK INDEX = 8（含 UQ 形）· trigger = 3 · function（新增）= 2

迁移顺序（D-P09-11 / P09_MIGRATION_PLAN.md §3）：
  agents（**不含** current_version FK）→ agent_versions → agent_permissions → tool_executions →
  indexes → functions → triggers → **最后** ADD fk_agents_current_version

本 revision **不做任何 seed**（SD:193：P00–P10 无 seed；P13 才有）：
  * 四表初始 rows = 0
  * 不 INSERT permissions / acl_subject_types / roles，不创建默认 Agent / Tool

边界（强制）：
  * 不含分区（D-P09-01 = B）· 不含保留期执行器（scheduler / job / extension）
  * 不含 RLS · 不含 Authorization Evaluation · 不含 ABAC / policy evaluator / role / deny resolution
  * conditions = storage-only（只存不解释）
  * 不实施 G/H/I/J（tg_acl_subject_exists / tg_acl_user_hard_delete /
    tg_acl_role_delete_block / tg_agent_acl_expire）—— 属 P09 后
  * 不创建 events / audit_logs（P10）· 不创建 Domain 表 · 不改动 0001–0010 建立的任何对象
  * 不引入 runtime agent execution / registry binding / tool runtime / plugin loading
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_p09_agent_tool_permission"
down_revision = "0010_b1_6_ai_gateway"
branch_labels = None
depends_on = None

_TABLES = ("agents", "agent_versions", "agent_permissions", "tool_executions")

# `sa.DateTime` 结构性无法表达 precision ⇒ 必须用 postgresql.TIMESTAMP(precision=3)。
# 平台铁律：所有时间列 = timestamptz(3)（CORE §10；0009 correction 已统一 0003–0008）。
_TS = postgresql.TIMESTAMP(timezone=True, precision=3)

# 表达式唯一索引需要一个稳定的 "NULL 占位" 值（沿用 0008 `uq_tool_perm` 的 nil-uuid 惯例）：
#   version_id / permission_id / tool_id IS NULL 与具体值不得互相冲突
_NIL_UUID = "00000000000000000000000000000000"


# --------------------------------------------------------------------------- #
# Functions (2) — P09 implementation-level; not new Human Decisions
# --------------------------------------------------------------------------- #

# U-2 / D-P09-12 — structural integrity only（不做 authorization evaluation，不引入 RLS）
_AGENTS_TENANT_SPACE_SQL = """
CREATE FUNCTION enforce_agents_tenant_space_consistency() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  space_tenant uuid;
BEGIN
  IF NEW.space_id IS NOT NULL THEN
    SELECT tenant_id INTO space_tenant FROM spaces WHERE id = NEW.space_id;
    IF space_tenant IS NULL THEN
      RAISE EXCEPTION 'agents.space_id % does not exist', NEW.space_id;
    END IF;
    IF NEW.tenant_id IS DISTINCT FROM space_tenant THEN
      RAISE EXCEPTION
        'agents.tenant_id % does not match spaces.tenant_id % (cross-tenant agent denied)',
        NEW.tenant_id, space_tenant;
    END IF;
  END IF;
  -- 仅做结构完整性校验：不写其它表、不做授权判定、不做级联、不写审计
  RETURN NEW;
END;
$$;
"""

# NU-07 / D-P09-14 — published 快照不可改删（structural invariant only）
# 独立于 0008 的 enforce_tool_versions_immutable()：0008 的消息硬编码 tool_versions，
# 且 0008 属已发布 revision（append-only，不得修改）。两函数语义同构（trigger 名共用 D-B15-03）。
_AGENT_VERSIONS_IMMUTABLE_SQL = """
CREATE FUNCTION enforce_agent_versions_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.status = 'published' THEN
      RAISE EXCEPTION
        'agent_versions: published version is immutable (DELETE denied; deprecate/revoke via application governance in a later phase)';
    END IF;
    RETURN OLD;
  END IF;

  IF OLD.status = 'published' THEN
    RAISE EXCEPTION
      'agent_versions: published version is immutable (UPDATE denied; deprecate/revoke via application governance in a later phase)';
  END IF;
  RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
    # --------------------------------------------------------------- agents
    # D-P09-11：本表**不含** current_version_id 的 FK 约束（该约束在本 revision 末尾补）
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        # 业务实体一律 RESTRICT（CORE §11.1 白名单不含 tenants → agents）
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        # D-B15-05 同口径：opaque application identifier —— 无 regex / format CHECK
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("max_risk_level", sa.Text(), nullable=False),
        # FK 在末尾补（deferred *creation*，非 DEFERRABLE —— ND-B = FROZEN AS NON-DEFERRABLE）
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        # P09 → P08 引用（唯一一处）；SET NULL（D-P09-03 F4）
        sa.Column("default_route_id", postgresql.UUID(as_uuid=True), nullable=True),
        # 安全：config jsonb 禁止 DSN / 凭据（CI 扫描项，CORE:272）
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("archived_at", _TS, nullable=True),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT",
                                name="fk_agents_tenant"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"], ondelete="RESTRICT",
                                name="fk_agents_space"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT",
                                name="fk_agents_owner"),
        sa.ForeignKeyConstraint(["default_route_id"], ["ai_routes.id"], ondelete="SET NULL",
                                name="fk_agents_default_route"),
        sa.CheckConstraint("status IN ('draft','active','disabled','archived')",
                           name="ck_agents_status"),
        sa.CheckConstraint("max_risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')",
                           name="ck_agents_max_risk_level"),
    )

    # -------------------------------------------------------- agent_versions
    op.create_table(
        "agent_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False),
        sa.Column("input_schema", postgresql.JSONB(), nullable=True),
        sa.Column("output_schema", postgresql.JSONB(), nullable=True),
        sa.Column("allowed_tools", postgresql.JSONB(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", _TS, nullable=True),
        # 本表**无 updated_at** ⇒ 无 set_updated_at trigger（不可变快照）
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        # 版本快照：父实体受控 purge 时整棵删除（CORE §11.1 白名单）
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE",
                                name="fk_agent_versions_agent"),
        # actor attribution（与 ownership 正交）
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="SET NULL",
                                name="fk_agent_versions_published_by"),
        sa.UniqueConstraint("agent_id", "version", name="uq_agent_versions"),
        sa.CheckConstraint("status IN ('draft','published','deprecated','revoked')",
                           name="ck_agent_versions_status"),
    )

    # ----------------------------------------------------- agent_permissions
    op.create_table(
        "agent_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=True),
        # 范围限定（opaque text —— 不解释、不构成授权判定）
        sa.Column("resource_scope", sa.Text(), nullable=True),
        sa.Column("effect", sa.Text(), nullable=False),
        # storage-only（不解释，不构成 ABAC 契约）
        sa.Column("conditions", postgresql.JSONB(), nullable=True),
        # 本表**无 updated_at**
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        # 配置行：随父实体受控 purge 清理（CORE §11.1 白名单）
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE",
                                name="fk_agent_permissions_agent"),
        sa.ForeignKeyConstraint(["version_id"], ["agent_versions.id"], ondelete="CASCADE",
                                name="fk_agent_permissions_version"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE",
                                name="fk_agent_permissions_permission"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE",
                                name="fk_agent_permissions_tool"),
        # D-P09-05 = B（FROZEN）：2 条 CHECK，不得合并
        # ND-A = FROZEN AS NO-TIGHTENING ⇒ 纯 IS NOT NULL（**不**追加 `<> ''`）
        sa.CheckConstraint(
            "permission_id IS NOT NULL OR tool_id IS NOT NULL OR resource_scope IS NOT NULL",
            name="ck_agent_permissions_scope_target"),
        sa.CheckConstraint("effect IN ('allow','deny')",
                           name="ck_agent_permissions_effect"),
    )

    # ------------------------------------------------------- tool_executions
    op.create_table(
        "tool_executions",
        # D-P09-01 = B（FROZEN）：**不分区**；PK = id；90 天 hard delete（executor 不属 P09）
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        # D-P09-02 = A（FROZEN）：NOT NULL
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        # 历史归属：SET NULL（记录保留、归属置空）—— 不得 CASCADE
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_digest", sa.Text(), nullable=False),
        sa.Column("output_digest", sa.Text(), nullable=True),
        # 运行时风险等级：无 CK（D-P09-13 仅 3 条；不得顺手新增词表）
        sa.Column("risk_level", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("started_at", _TS, nullable=False),
        sa.Column("finished_at", _TS, nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.Text(), nullable=False),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        # 业务/运维数据一律 RESTRICT（父侧删除前须先清执行记录）
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT",
                                name="fk_tool_executions_tenant"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="RESTRICT",
                                name="fk_tool_executions_tool"),
        sa.ForeignKeyConstraint(["tool_version_id"], ["tool_versions.id"], ondelete="RESTRICT",
                                name="fk_tool_executions_tool_version"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL",
                                name="fk_tool_executions_agent"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL",
                                name="fk_tool_executions_actor"),
        # D-P09-13（ND-01）：3 条 CHECK
        sa.CheckConstraint("status IN ('running','succeeded','failed','denied','timeout')",
                           name="ck_tool_executions_status"),
        sa.CheckConstraint("attempts >= 1",
                           name="ck_tool_executions_attempts"),
        sa.CheckConstraint("duration_ms >= 0",
                           name="ck_tool_executions_duration"),
    )

    # ------------------------------------------------------------------ indexes
    # D-P09-15（ND-03）：权威 = STEP1B_INDEX_STRATEGY；共 8 个索引对象
    #   ① uq_agents_key（部分唯一）  ② ix_agents_tenant_status  ③ uq_agent_versions（随表 = CONSTRAINT）
    #   ④ ix_ap_agent  ⑤ uq_agent_perm（表达式唯一）  ⑥ uq_tool_exec_idem（部分唯一）
    #   ⑦ ix_texec_tenant_created  ⑧ ix_texec_status（部分）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_agents_key "
        "ON agents (tenant_id, lower(key)) WHERE archived_at IS NULL"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_agents_tenant_status ON agents (tenant_id, status)"
    ))
    # D-P09-16（ND-04）：表达式唯一性必须是 unique INDEX（不计入 UNIQUE CONSTRAINT）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_agent_perm "
        "ON agent_permissions ("
        "agent_id, "
        f"COALESCE(version_id, '{_NIL_UUID}'::uuid), "
        f"COALESCE(permission_id, '{_NIL_UUID}'::uuid), "
        f"COALESCE(tool_id, '{_NIL_UUID}'::uuid), "
        "COALESCE(resource_scope, ''))"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_ap_agent ON agent_permissions (agent_id)"
    ))
    # D-P09-04 = A（FROZEN）：部分唯一 ⇒ UNIQUE INDEX（不得伪装为 CONSTRAINT）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_tool_exec_idem "
        "ON tool_executions (tool_id, idempotency_key) "
        "WHERE idempotency_key IS NOT NULL"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_texec_tenant_created "
        "ON tool_executions (tenant_id, created_at DESC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_texec_status "
        "ON tool_executions (status, started_at) WHERE status = 'running'"
    ))

    # ---------------------------------------------------------------- functions
    # 仅新建 P09 的 2 个 enforce_*；不 DROP / 不重建 set_updated_at() / uap_uuid_v7()
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_agents_tenant_space_consistency()"))
    op.execute(sa.text(_AGENTS_TENANT_SPACE_SQL))
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_agent_versions_immutable()"))
    op.execute(sa.text(_AGENT_VERSIONS_IMMUTABLE_SQL))

    # ----------------------------------------------------------------- triggers
    # ① 复用 B1-1 set_updated_at()（agents 是 P09 唯一带 updated_at 的表）
    op.execute(sa.text(
        "CREATE TRIGGER tg_agents_set_updated_at BEFORE UPDATE ON agents "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    # ② D-P09-12 = A（FROZEN）—— tenant/space 一致性（structural integrity only）
    op.execute(sa.text(
        "CREATE TRIGGER tg_agents_tenant_space_consistency "
        "BEFORE INSERT OR UPDATE ON agents "
        "FOR EACH ROW EXECUTE FUNCTION enforce_agents_tenant_space_consistency()"
    ))
    # ③ D-P09-14 = A（ND-02）—— published 快照不可改删（trigger 名与 tool_versions 共用 D-B15-03）
    op.execute(sa.text(
        "CREATE TRIGGER tg_version_immutable "
        "BEFORE UPDATE OR DELETE ON agent_versions "
        "FOR EACH ROW EXECUTE FUNCTION enforce_agent_versions_immutable()"
    ))

    # ------------------------------------------------- deferred-created FK（最后）
    # D-P09-11 = A（FROZEN）· ND-B = FROZEN AS NON-DEFERRABLE
    # 循环 agents ⇄ agent_versions 通过「最后创建」解决；**不使用** PostgreSQL DEFERRABLE
    op.execute(sa.text(
        "ALTER TABLE agents ADD CONSTRAINT fk_agents_current_version "
        "FOREIGN KEY (current_version_id) REFERENCES agent_versions(id) ON DELETE SET NULL"
    ))

    # 无 seed（P09 四表初始 rows = 0；SD:193）


def downgrade() -> None:
    # [1] dependent triggers
    for trigger, table in (
        ("tg_version_immutable", "agent_versions"),
        ("tg_agents_tenant_space_consistency", "agents"),
        ("tg_agents_set_updated_at", "agents"),
    ):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger} ON {table}"))

    # [2] functions（仅 P09 新建；不 DROP set_updated_at / uap_uuid_v7）
    for fn in ("enforce_agent_versions_immutable", "enforce_agents_tenant_space_consistency"):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {fn}()"))

    # [3] deferred-created FK —— **首先解除**（D-P09-11：不得留下悬空约束）
    op.execute(sa.text(
        "ALTER TABLE agents DROP CONSTRAINT IF EXISTS fk_agents_current_version"
    ))

    # [4] dependent indexes（在 DROP TABLE 之前显式移除；uq_agent_versions 随表移除）
    for index in (
        "ix_texec_status",
        "ix_texec_tenant_created",
        "uq_tool_exec_idem",
        "ix_ap_agent",
        "uq_agent_perm",
        "ix_agents_tenant_status",
        "uq_agents_key",
    ):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index}"))

    # [5] tables（严格逆依赖序：tool_executions → agent_permissions → agent_versions → agents）
    for table in reversed(_TABLES):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
