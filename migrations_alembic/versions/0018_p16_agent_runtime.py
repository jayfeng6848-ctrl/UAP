"""0018_p16_agent_runtime — Agent Run ledger + P16 runtime correlation + runtime grants

Revision ID: 0018_p16_agent_runtime
Revises: 0017_p13_seed
Create Date: 2026-09-28

P16 LIMITED SCHEMA EXPANSION（PDL 附录 V · P16-D12 / D11 / D02）

  agent_runs         Agent Run 执行台账（唯一新增表；不建 run_steps / attempts / tool_history）
  ai_request_logs    + run_id（correlation；尊重既有分区设计 · **不建** 跨分区 FK · 不改既有列）
  tool_executions    + run_id（correlation；**不建** FK，避免历史台账被级联影响）
  GRANT（uap_runtime）：按 P16_RUNTIME_PRIVILEGE_MATRIX.md 最小面

不得（本 revision 明确不做）：
  * 修改 0013–0017 或任何既有 migration
  * 修改 P13 / P14 表语义 · 修改 ai_request_logs 分区设计 · 删除既有列 · 变更既有 FK policy
  * 新增 dedup table · 新增 role · GRANT ALL · 任何 DELETE 授权
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0018_p16_agent_runtime"
down_revision = "0017_p13_seed"
branch_labels = None
depends_on = None

_TS = sa.DateTime(timezone=True)

RUN_STATUSES = ("CREATED", "RUNNING", "WAITING_TOOL", "COMPLETED", "FAILED", "CANCELLED")

#: P16 新增到 uap_runtime 的 SELECT 面（D11 · 逐表 reason 见 privilege matrix）
_GRANT_SELECT = (
    "tool_versions",
    "tool_permissions",
    "ai_providers",
    "ai_models",
    "ai_routes",
    "ai_policies",
)
#: 台账读回
_GRANT_SELECT_LEDGER = ("agent_runs", "tool_executions")
#: 写入面
_GRANT_INSERT = ("ai_request_logs", "agent_runs", "tool_executions")
_GRANT_UPDATE = ("agent_runs", "tool_executions")
_RUNTIME = "uap_runtime"


def _grant(table: str, privileges: str) -> None:
    op.execute(sa.text(f'GRANT {privileges} ON TABLE public."{table}" TO {_RUNTIME}'))


def upgrade() -> None:
    # ---------------------------------------------------------------- agent_runs
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_digest", sa.Text(), nullable=False),
        sa.Column("result_digest", sa.Text(), nullable=True),
        sa.Column("result_metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("failure_code", sa.Text(), nullable=True),
        sa.Column("failure_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("tool_calls", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", _TS, nullable=True),
        sa.Column("completed_at", _TS, nullable=True),
        sa.Column("updated_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('CREATED','RUNNING','WAITING_TOOL','COMPLETED','FAILED','CANCELLED')",
            name="ck_agent_runs_status",
        ),
        sa.CheckConstraint("actor_type IN ('USER','ROLE','AGENT')", name="ck_agent_runs_actor_type"),
        sa.CheckConstraint("tool_calls >= 0", name="ck_agent_runs_tool_calls"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="RESTRICT", name="fk_agent_runs_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"], ondelete="RESTRICT", name="fk_agent_runs_agent"
        ),
        sa.ForeignKeyConstraint(
            ["agent_version_id"],
            ["agent_versions.id"],
            ondelete="RESTRICT",
            name="fk_agent_runs_agent_version",
        ),
    )
    # FK policy：全部 RESTRICT（历史执行台账不得因父行删除而消失；与 tool_executions 同构，无 CASCADE）

    op.create_index("ix_agent_runs_tenant_created", "agent_runs", ["tenant_id", "created_at"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])

    op.execute(sa.text(
        "CREATE TRIGGER tg_agent_runs_set_updated_at BEFORE UPDATE ON agent_runs "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))

    # ------------------------------------------------- correlation columns（不改既有列）
    op.execute(sa.text("ALTER TABLE ai_request_logs ADD COLUMN run_id uuid NULL"))
    op.execute(sa.text("ALTER TABLE tool_executions ADD COLUMN run_id uuid NULL"))
    op.execute(sa.text(
        "CREATE INDEX ix_texec_run ON tool_executions (run_id) WHERE run_id IS NOT NULL"
    ))

    # ---------------------------------------------------------------- grants（D11）
    for table in _GRANT_SELECT:
        _grant(table, "SELECT")
    for table in _GRANT_SELECT_LEDGER:
        _grant(table, "SELECT")
    for table in _GRANT_INSERT:
        _grant(table, "INSERT")
    for table in _GRANT_UPDATE:
        _grant(table, "UPDATE")


def downgrade() -> None:
    # 权限先撤（ownership-aware：撤销后 owner 仍持有，故顺序不影响可执行性）
    for table in _GRANT_UPDATE + _GRANT_INSERT + _GRANT_SELECT_LEDGER:
        op.execute(sa.text(f'REVOKE ALL PRIVILEGES ON TABLE public."{table}" FROM {_RUNTIME}'))
    for table in _GRANT_SELECT:
        op.execute(sa.text(f'REVOKE ALL PRIVILEGES ON TABLE public."{table}" FROM {_RUNTIME}'))

    op.execute(sa.text("DROP INDEX IF EXISTS ix_texec_run"))
    op.execute(sa.text("ALTER TABLE tool_executions DROP COLUMN IF EXISTS run_id"))
    op.execute(sa.text("ALTER TABLE ai_request_logs DROP COLUMN IF EXISTS run_id"))

    op.execute(sa.text("DROP TRIGGER IF EXISTS tg_agent_runs_set_updated_at ON agent_runs"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_agent_runs_status"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_agent_runs_tenant_created"))
    op.drop_table("agent_runs")
