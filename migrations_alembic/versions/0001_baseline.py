"""0001_baseline — historical alignment point (no-op)

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-07

本 revision 是 **历史对齐点**：代表旧自研 runner 已应用过的
``migrations/0001_platform_baseline.sql``（platform_metadata /
schema_migrations 两张 STEP 0 记账表）。

B1 起所有新 schema 一律走 Alembic；本 revision 只做版本锚定，
upgrade/downgrade 均为 no-op，不创建任何对象。

Scope: B1-0-INFRASTRUCTURE-ONLY（无业务表）
"""

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op: historical alignment anchor."""


def downgrade() -> None:
    """No-op: historical alignment anchor."""
