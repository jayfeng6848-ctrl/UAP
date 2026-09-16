"""0009_timestamp_precision — platform-wide timestamptz(3) correction

Revision ID: 0009_timestamp_precision
Revises: 0008_b1_5_tool_registry
Create Date: 2026-09-15

Scope: **PLATFORM CORRECTIVE** — 这不是新的业务 Phase。

  命名（重要，实测约束）：
    alembic 的 ``alembic_version.version_num`` 为 ``varchar(32)``（``env.py`` 使用默认
    ``version_table="alembic_version"``，未覆盖列类型）。原拟 revision id
    ``0009_platform_timestamp_precision`` = 33 字符 ⇒ 升级在写版本号时被 PostgreSQL 拒绝
    （``value too long for type character varying(32)``）。
    故 revision / filename 定为 ``0009_timestamp_precision``（24 字符）。
    本 revision 属**平台级**校正的范围语义由本文档与
    ``tests/integration/test_platform_timestamp_precision.py`` 承载（PG1–PG7）。

  本 revision 修复平台级时间精度偏差。冻结规则要求 ``timestamptz(3)``：
    * STEP1A_DESIGN_REPORT §12 时间策略：精度 `timestamptz(3)`
    * CORE_DOMAIN_MODEL §10 时间策略："精度 | `timestamptz(3)`（毫秒）"
  而 0001–0008 的时间列一律使用 ``sa.DateTime(timezone=True)``（该构造**无 precision 参数**，
  结构性无法表达精度）⇒ 实际落库为 ``timestamp with time zone``，catalog ``datetime_precision = 6``。

  修复范围（Recon 实测）：**20 张表 · 72 个时间列**，全部从 ``timestamptz`` 收窄为 ``timestamptz(3)``。

  实现方式（Human FROZEN）：
    * **显式静态 (table, column) 清单**驱动，不使用 `information_schema` 动态驱动；
    * 仅执行 ``ALTER TABLE ... ALTER COLUMN ... TYPE timestamptz(N)``；
    * **不新增/删除任何 FK、CK、Index、Trigger、Function**；
    * 不修改任何其他 schema 语义。

  历史 migration 完整性（强制）：
    * 0001–0008 为 historical migration，**本 revision 不修改其任何一行**；
    * P01–P07 阶段定义不变；本 revision 不占用任何业务 Phase 编号；
    * 因 0009 被本 correction 专用，**P08 后续 migration 编号顺延至 0010**。

  downgrade 语义（重要，data-level lossy）：
    * schema declaration 可逆 —— 对称转换回 ``timestamptz(6)``；
    * **已发生的微秒舍入不可恢复** —— ``timestamptz(3)`` 在写入时已把微秒舍入到毫秒，
      升级后再降级只能恢复「声明精度」，无法还原被舍入掉的时间值；
    * 因此本 revision 属于 **data-level lossy downgrade**（结构可逆、数据不可逆）。

  不受影响的对象（Recon 已逐项核实，本 revision 一并不触碰）：
    * 34 个 ``server_default = now()``（ALTER TYPE 保留默认表达式）
    * 27 个 trigger（其中 14 个 ``*_set_updated_at`` 的 ``set_updated_at()`` 仅写
      ``NEW.updated_at = now()``，精度无关）
    * 2 个依赖时间列的索引（``ix_sessions_expires_active`` · ``uq_memberships`` 部分谓词）
    * 1 个依赖时间列的 CHECK（``ck_sessions_expiry``）
    * 函数 ``set_updated_at()`` / ``uap_uuid_v7()``（均为精度无关，不重建）
    * VIEW / 物化视图 / 分区 = 0

  边界（强制）：
    * 不含 seed；不含 API / Socket；不含 RLS；不含 Authorization Evaluation
    * 不引入任何 Domain / 业务语义；Core → Domain = 0
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_timestamp_precision"
down_revision = "0008_b1_5_tool_registry"
branch_labels = None
depends_on = None

# --------------------------------------------------------------------------- #
# Platform timestamp columns — 20 tables / 72 columns (explicit static list)
#
# 来源：0001–0008 historical migrations 的 static 扫描结果（Recon 已确认）。
# 顺序 = migration 顺序；同一表内顺序 = 建表列顺序。
# 仅包含 `*_at` / 平台时间列；不含 `timestamp without time zone`（全库 = 0）。
# --------------------------------------------------------------------------- #
TIMESTAMP_COLUMNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # ---- 0003_b1_1_root_identity（P01+P02）--------------------------------
    ("users", ("email_verified_at", "last_login_at", "locked_until",
               "created_at", "updated_at", "deleted_at")),
    ("identities", ("verified_at", "last_used_at", "revoked_at",
                    "created_at", "updated_at")),
    ("credentials", ("expires_at", "last_used_at", "rotated_at", "revoked_at",
                     "locked_until", "created_at", "updated_at")),
    ("devices", ("first_seen_at", "last_seen_at", "revoked_at",
                 "created_at", "updated_at")),
    ("sessions", ("expires_at", "absolute_expires_at", "last_used_at", "revoked_at",
                  "created_at", "updated_at")),
    # ---- 0004_b1_2_tenant_space（P03+P05）--------------------------------
    ("tenants", ("archived_at", "deleted_at", "created_at", "updated_at")),
    ("spaces", ("archived_at", "deleted_at", "created_at", "updated_at")),
    ("tenant_memberships", ("invited_at", "joined_at", "role_assigned_at", "removed_at",
                            "created_at", "updated_at")),
    ("memberships", ("joined_at", "removed_at", "created_at", "updated_at")),
    # ---- 0005_b1_3_authorization（P04）-----------------------------------
    ("permissions", ("created_at",)),
    ("roles", ("archived_at", "created_at", "updated_at")),
    ("role_permissions", ("created_at",)),
    ("platform_memberships", ("revoked_at", "created_at", "updated_at")),
    # ---- 0006_b1_3_bootstrap_state（P04 收尾）-----------------------------
    ("platform_state", ("initialized_at", "created_at", "updated_at")),
    # ---- 0007_b1_4_resource_acl（P06）------------------------------------
    ("resources", ("archived_at", "deleted_at", "created_at", "updated_at")),
    ("acl_subject_types", ("created_at", "archived_at")),
    ("resource_permissions", ("expires_at", "created_at")),
    # ---- 0008_b1_5_tool_registry（P07）-----------------------------------
    ("tools", ("disabled_at", "created_at", "updated_at")),
    ("tool_versions", ("published_at", "created_at")),
    ("tool_permissions", ("created_at",)),
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_PLATFORM_PRECISION = 3
_LEGACY_PRECISION = 6   # 修复前 `timestamptz` 的默认精度（data-level 不可还原）


def _pairs() -> list[tuple[str, str]]:
    """展开为 (table, column) 平坦清单 —— 期望 72 条。"""
    return [(table, column) for table, columns in TIMESTAMP_COLUMNS for column in columns]


def _set_precision(precision: int) -> None:
    """对全部平台时间列执行同基类型 typmod 转换（不新增/删除任何约束对象）。

    只做 ``ALTER COLUMN ... TYPE timestamptz(N)``：
      * PostgreSQL 允许 timestamptz → timestamptz(N) 的 typmod 收窄**无需 USING**；
      * default 表达式由 PG 保留；依赖的时间列索引自动重建；
        引用时间列的 CHECK 自动重校验。
    """
    for table, column in _pairs():
        op.execute(sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE timestamptz({precision})"
        ))


# --------------------------------------------------------------------------- #
# upgrade / downgrade
# --------------------------------------------------------------------------- #


def upgrade() -> None:
    """平台时间列统一收窄为 timestamptz(3)（20 表 / 72 列）。"""
    _set_precision(_PLATFORM_PRECISION)


def downgrade() -> None:
    """对称恢复声明精度 timestamptz(6)。

    ⚠️ **data-level lossy**：schema 声明可逆，但升级期间已舍入到毫秒的微秒值不可恢复。
    """
    _set_precision(_LEGACY_PRECISION)
