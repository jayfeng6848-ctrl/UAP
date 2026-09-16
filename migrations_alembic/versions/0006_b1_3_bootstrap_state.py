"""0006_b1_3_bootstrap_state — Platform Bootstrap Initialization State (P1-01)

Revision ID: 0006_b1_3_bootstrap_state
Revises: 0005_b1_3_authorization
Create Date: 2026-09-08

Scope: B1-3 HARDENING — P1-01 Bootstrap Permanent Closure
  * 新增单例表 `platform_state`（显式初始化状态，**独立于 platform_memberships 生命周期**）
  * `tg_platform_state_guard`：状态只允许单向 `uninitialized → initialized`，禁删/禁回退/禁再插
  * `tg_pm_bootstrap_gate`：PM 写入门（INSERT）—— 仅当（state='initialized'）或
    （state='uninitialized' AND PM 无行）时允许；CASCADE/user 硬删不可能重置 state

为什么需要新表（对应审计要求 9 的设计说明）：
  * 旧模型以 `PM row count = 0` 判定“未初始化”。虽然 last-admin 不变量使初始化后 PM
    恒 ≥1 行，但该证明依赖 trigger 持续存在，且“count 可派生回 0”的形态本身不够强；
    审计要求一个 **不被 PM lifecycle（revoke / DELETE / CASCADE）重置**的显式状态。
  * `platform_state` 为单例行（PK id=1 + CHECK），与任何业务表无 FK 依赖；
    users 硬删 / PM CASCADE 不会触碰它 → 永久 INITIALIZED。
  * 无 legacy `platform_metadata` 依赖；不实现 recovery API（PMB-2 契约保留）。

初始化（部署期受信 CLI，actor 由服务内部上下文提供，写入 audit_logs(action='platform.admin.bootstrap')
于 audit 表存在后；本 revision 只建结构、**不写 INITIALIZED**，seed 行为 'uninitialized'）：
  1. BEGIN
  2. CHECK state='uninitialized' AND platform_memberships 无行
  3. INSERT 首行 platform_memberships（bootstrap gate 放行：uninitialized AND empty）
  4. UPDATE platform_state SET bootstrap_state='initialized', initialized_at=now()
  5. audit(platform.admin.bootstrap)  // 与 2–4 同事务
  6. COMMIT  → 路径永久关闭（guard 拒绝任何回退/再初始化）

downgrade：DROP 两 trigger + platform_state（恢复 0005 形态；不重建任何 0005 对象）。
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_b1_3_bootstrap_state"
down_revision = "0005_b1_3_authorization"
branch_labels = None
depends_on = None

_STATE_GUARD_SQL = """
CREATE FUNCTION enforce_platform_state_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'platform_state row cannot be deleted (bootstrap state is permanent)';
  ELSIF TG_OP = 'INSERT' THEN
    IF NEW.bootstrap_state IS DISTINCT FROM 'uninitialized' THEN
      RAISE EXCEPTION 'platform_state can only be inserted as uninitialized (migration seed)';
    END IF;
    IF EXISTS (SELECT 1 FROM platform_state) THEN
      RAISE EXCEPTION 'platform_state is a singleton (only one row)';
    END IF;
    RETURN NEW;
  ELSE  -- UPDATE
    IF NOT (OLD.bootstrap_state = 'uninitialized'
            AND NEW.bootstrap_state = 'initialized'
            AND NEW.initialized_at IS NOT NULL) THEN
      RAISE EXCEPTION
        'platform_state may only transition uninitialized -> initialized once (permanent closure)';
    END IF;
    RETURN NEW;
  END IF;
END;
$$;
"""

_PM_BOOTSTRAP_GATE_SQL = """
CREATE FUNCTION enforce_pm_bootstrap_gate() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  st text;
  pm_count bigint;
BEGIN
  SELECT bootstrap_state INTO st FROM platform_state WHERE id = 1;
  IF st IS NULL THEN
    RAISE EXCEPTION 'platform_state row missing (corrupt install)';
  END IF;
  IF st = 'initialized' THEN
    RETURN NEW;  -- 运行时 grant 路径（应用层仍须平台管理员授权 + audit）
  END IF;
  -- st = 'uninitialized'：仅允许 bootstrap 首行（同事务内先插 PM 再翻转 state）
  SELECT count(*) INTO pm_count FROM platform_memberships;
  IF pm_count = 0 THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION
    'platform not initialized: PM writes are only allowed through the one-time bootstrap path';
END;
$$;
"""


def upgrade() -> None:
    # ------------------------------------------------------ platform_state
    op.create_table(
        "platform_state",
        sa.Column("id", sa.SmallInteger(), primary_key=True, server_default=sa.text("1")),
        sa.Column("bootstrap_state", sa.Text(), nullable=False,
                  server_default=sa.text("'uninitialized'")),
        sa.Column("initialized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint("id = 1", name="ck_platform_state_singleton"),
        sa.CheckConstraint(
            "bootstrap_state IN ('uninitialized','initialized')",
            name="ck_platform_state_bootstrap",
        ),
    )
    # seed：uninitialized（先于 guard trigger，使 seed 可行）
    op.execute(
        sa.text(
            "INSERT INTO platform_state (id, bootstrap_state) VALUES (1, 'uninitialized') "
            "ON CONFLICT (id) DO NOTHING"
        )
    )
    for name, sql in (
        ("enforce_platform_state_guard", _STATE_GUARD_SQL),
        ("enforce_pm_bootstrap_gate", _PM_BOOTSTRAP_GATE_SQL),
    ):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {name}()"))
        op.execute(sa.text(sql))
    op.execute(sa.text(
        "CREATE TRIGGER tg_platform_state_set_updated_at BEFORE UPDATE ON platform_state "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_platform_state_guard BEFORE INSERT OR UPDATE OR DELETE ON platform_state "
        "FOR EACH ROW EXECUTE FUNCTION enforce_platform_state_guard()"
    ))
    op.execute(sa.text(
        "CREATE TRIGGER tg_pm_bootstrap_gate BEFORE INSERT ON platform_memberships "
        "FOR EACH ROW EXECUTE FUNCTION enforce_pm_bootstrap_gate()"
    ))


def downgrade() -> None:
    for trigger, table in (
        ("tg_pm_bootstrap_gate", "platform_memberships"),
        ("tg_platform_state_guard", "platform_state"),
        ("tg_platform_state_set_updated_at", "platform_state"),
    ):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger} ON {table}"))
    for fn in ("enforce_pm_bootstrap_gate", "enforce_platform_state_guard"):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {fn}()"))
    op.execute(sa.text("DROP TABLE IF EXISTS platform_state"))
