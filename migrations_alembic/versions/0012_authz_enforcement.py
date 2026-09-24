"""0012_authz_enforcement — canonical action enforcement + structured tool grants

Revision ID: 0012_authz_enforcement
Revises: 0011_p09_agent_tool_permission
Create Date: 2026-09-23

Scope: STAGE 2 authorization implementation — the approved schema change set
only. Three changes, all additive, no trigger, no index, no seed.

  SC-1   permissions.action           + CHECK (canonical action vocabulary)
  SC-1b  resource_permissions.action  + CHECK (canonical action vocabulary)
  SC-2   tool_permissions             + resource_type / action / scope columns
                                        (+ CHECK on scope)

冻结来源（逐项核对见 docs/architecture/AUTHORIZATION_SCHEMA_IMPACT.md）：
  * D-AUTH-05（FROZEN）Action 词表 = 12 项 canonical；实现必须能够在数据层校验
  * D-AUTH-24（FROZEN）D-B14-08 由 D-AUTH-05 取代 ⇒ resource_permissions.action
                        不再维持「零新增约束／opaque」语义，SC-1b 由此成立
  * D-AUTH-25（FROZEN）Action canonical 存储形 = **小写**（与平台既有 action 惯例一致）
  * D-AUTH-09（FROZEN）Tool = 唯一受控执行出口；工具授权必须能结构化表达
                        （Tool + Action/Capability + Scope + Resource Context）
  * D-AUTH-17（FROZEN）本冻结本身不产生 schema 变更；实施期变更以此 change set 为限
  * D-AUTH-06（FROZEN）stored scope = PLATFORM | TENANT | SPACE
                       ⇒ SC-2 的 scope 列以同名 CHECK 约束，RESOURCE / SELF 不得入库

明确不采用（D-AUTH-17 冻结）：
  * 不新增 resources.parent_id · 不新增 resource_relations
  * 不重建 resource_permissions 唯一键（D-AUTH-20：ACL 唯一键不变）
  * 不实施 SC-3（Module 扩展 action registry —— 仍为 PROPOSED ONLY）

P09 保护（D-AUTH-23 / §7）：
  * 不触碰 agents / agent_versions / agent_permissions / tool_executions
  * 特别是 agent_permissions.resource_scope 保持 OPAQUE TEXT、不解释、不构成授权判定
    —— 本 revision 不读取、不规范化、不约束该列
  * 不改动 0001–0011 的任何对象；append-only；down_revision = 0011 ⇒ 单头

可逆性：纯附加式变更（2 条 CHECK + 3 个可空列），downgrade 完全还原，无数据迁移。

其他边界：
  * 不创建 events / audit_logs / approval_requests（P10 / Tool Runtime）
  * 不新增触发器（延续 R2-D-14「DB 不做授权解释」）
  * 不新增索引（属 P12 范畴）
  * 不做任何 seed（P00–P12 无 seed；首个可登录主体只经 P13）
"""

import sqlalchemy as sa
from alembic import op

revision = "0012_authz_enforcement"
down_revision = "0011_p09_agent_tool_permission"
branch_labels = None
depends_on = None

# D-AUTH-05 — the canonical action vocabulary, frozen at 12 entries.
# D-AUTH-25 — its canonical storage form is lowercase; the CHECK enforces the
# lowercase form exactly, and callers normalise (NFKC + casefold) before write.
_CANONICAL_ACTIONS = (
    "read",
    "list",
    "create",
    "update",
    "delete",
    "execute",
    "approve",
    "reject",
    "publish",
    "export",
    "share",
    "admin",
)

# D-AUTH-06 — scopes that may be stored on a grant.
_STORED_SCOPES = ("PLATFORM", "TENANT", "SPACE")

_ACTION_LIST = ", ".join(f"'{action}'" for action in _CANONICAL_ACTIONS)
_SCOPE_LIST = ", ".join(f"'{scope}'" for scope in _STORED_SCOPES)

_CHECK_PERMISSIONS = f"action IN ({_ACTION_LIST})"
_CHECK_TOOL_SCOPE = f"scope IS NULL OR scope IN ({_SCOPE_LIST})"


def _assert_no_non_canonical(table: str) -> None:
    """Refuse to tighten a column that already holds out-of-vocabulary values.

    A failure here is a migration abort, not a silent data rewrite: the contract
    forbids guessing what a non-canonical value was meant to be.
    """
    op.execute(
        sa.text(
            f"DO $$ BEGIN "
            f"IF EXISTS (SELECT 1 FROM {table} WHERE action IS NULL "
            f"OR action NOT IN ({_ACTION_LIST})) THEN "
            f"RAISE EXCEPTION 'SC-1 preflight failed: non-canonical action values in {table}'; "
            f"END IF; END $$;"
        )
    )


def upgrade() -> None:
    # [1] defensive preflight — fail before touching anything
    _assert_no_non_canonical("permissions")
    _assert_no_non_canonical("resource_permissions")

    # [2] SC-1 / SC-1b — canonical action enforcement
    op.execute(sa.text(
        "ALTER TABLE permissions ADD CONSTRAINT ck_permissions_action_canonical "
        f"CHECK ({_CHECK_PERMISSIONS})"
    ))
    op.execute(sa.text(
        "ALTER TABLE resource_permissions "
        "ADD CONSTRAINT ck_resource_permissions_action_canonical "
        f"CHECK ({_CHECK_PERMISSIONS})"
    ))

    # [3] SC-2 — structured tool grants (all nullable, additive)
    op.execute(sa.text("ALTER TABLE tool_permissions ADD COLUMN resource_type text"))
    op.execute(sa.text("ALTER TABLE tool_permissions ADD COLUMN action text"))
    op.execute(sa.text("ALTER TABLE tool_permissions ADD COLUMN scope text"))
    op.execute(sa.text(
        "ALTER TABLE tool_permissions ADD CONSTRAINT ck_tool_permissions_scope "
        f"CHECK ({_CHECK_TOOL_SCOPE})"
    ))


def downgrade() -> None:
    # Strict reverse order: constraints first, then the columns they cover.
    op.execute(sa.text(
        "ALTER TABLE tool_permissions DROP CONSTRAINT IF EXISTS ck_tool_permissions_scope"
    ))
    for column in ("scope", "action", "resource_type"):
        op.execute(sa.text(f"ALTER TABLE tool_permissions DROP COLUMN IF EXISTS {column}"))

    op.execute(sa.text(
        "ALTER TABLE resource_permissions "
        "DROP CONSTRAINT IF EXISTS ck_resource_permissions_action_canonical"
    ))
    op.execute(sa.text(
        "ALTER TABLE permissions DROP CONSTRAINT IF EXISTS ck_permissions_action_canonical"
    ))
