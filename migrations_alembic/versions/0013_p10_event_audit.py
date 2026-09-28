"""0013_p10_event_audit — P10 Event / Audit persistence + outbox substrate + audit immutability

Revision ID: 0013_p10_event_audit
Revises: 0012_authz_enforcement
Create Date: 2026-09-25

Scope: P10 — 2 partitioned parent tables + 2 current-month child partitions +
1 function + 1 trigger. **0 index · 0 seed · 0 FK · 0 UNIQUE constraint.**

  events         transactional outbox 载体（事件即投递记录；at-least-once）
  audit_logs     不可变审计日志（append-only；仅 INSERT / SELECT）

冻结来源（逐项核对见 docs/architecture/P10_IMPLEMENTATION_CONTRACT.md §4/§5/§8/§10；
本 revision 只实现，不重新设计）：

  D-P10-01（FROZEN）events 的 outbox 状态列 8 列**一次建齐**（status / worker_id /
                     claimed_at / lease_expires_at / attempts / next_attempt_at /
                     last_error / delivered_at）；**不新增第三张表**（events 即 outbox）
  D-P10-02（FROZEN）Domain Event ID = **UUIDv7**（canonical；应用层生成）
  D-P10-05（FROZEN）Authorization Audit 五语义维度（subject / delegator / decision /
                     policy / approval）以**结构化 metadata** 表达 ⇒ **不新增列**
  D-P10-09（FROZEN）分区 = RANGE (occurred_at) 月分区；仅建**当月**子分区；
                     **不建 DEFAULT 分区**
  D-P10-10（FROZEN）分区维护 = **手工运维**（无 job / scheduler / pg_partman / 扩展）
  D-P10-11（FROZEN）**tg_audit_immutable = P10-owned** —— P10 内即建立 audit 基础不可变性，
                     消除「P10 implemented → audit exists but mutable → P11 later fixes」窗口
  D-P10-12（FROZEN）不建 events ↔ audit_logs linkage 列
  D-P10-13（FROZEN）DB GRANT / 角色体系 = **OPEN-P10-1（DEFER）** ⇒ 本 revision **零 GRANT**
  D-P10-14（FROZEN）classification 可空；分级只升不降（应用层纪律，不新增列）
  D-P10-15（FROZEN）**不引入 RLS**
  D-P10-16（FROZEN）correlation_id 为跨面关联键载体（不加 linkage 列）
  D-P10-17（FROZEN）五类承载面边界由 tests/architecture 守卫（非 migration 物）
  D-P10-18（FROZEN）投递 worker 属 Runtime ⇒ 本 revision 不含任何 worker / 队列框架
  D-P12-08（FROZEN）ix_events_* / ix_audit_*（7 条）= **P12** ⇒ 本 revision **不建索引**
  D-AUTH-22（FROZEN）ID = UUIDv7；时间列 timestamptz(3)

字段权威：CORE_DOMAIN_MODEL §1.6 + STEP1B_EVENT_OUTBOX §1 + STEP1B_CONSTRAINT_MATRIX §7
（三者一致）。**不自行补字段**；ER_MODEL §6 的两处偏差（DISC-1 误标 FK / DISC-2 缺
created_at）以 SCHEMA/CONSTRAINT 为准，不据 ER 图实施。

对象计数（实测口径见 P10_IMPLEMENTATION_CONTRACT §4.2 / §5.2）：
  tables            = 2（父表；均 partitioned）
  columns           = 22（events） + 19（audit_logs） = 41
  PK                = 2（均为 (id, occurred_at) —— 分区键进 PK）
  FK                = 0 · UQ = 0 · CHECK = 3 + 3 = 6
  non-PK INDEX      = 0（7 条查询索引归 P12）
  trigger           = 1（仅 audit_logs 的 tg_audit_immutable；events **无** trigger）
  function（新增）   = 1（enforce_audit_logs_immutable）
  partition         = 父表 2 + 当月子分区 2 · seed = 0 · GRANT = 0

安全（P10_IMPLEMENTATION_CONTRACT §8/§9）：
  * 函数为默认 **SECURITY INVOKER**（**禁止** SECURITY DEFINER —— 全仓先例 0 例）
  * 函数体**不引用任何对象** ⇒ 天然不依赖调用方 search_path（无限定名解析风险）
  * 不引入 RLS · 不引入 DEFAULT 分区 · 不执行任何 GRANT
  * audit_logs 无 updated_at / deleted_at ⇒ 结构性追加写

边界（强制）：
  * 不含 G/H/I/J（P11）· 不含 P12 索引 · 不含 partition 自动化
  * 不含 agent_runs / agent_run_steps（Runtime）· 不含 event_types 注册表
  * 不含 outbox 投递 worker / 队列框架（Runtime）
  * 不改动 0001–0012 的任何对象；append-only；down_revision = 0012 ⇒ 单头
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013_p10_event_audit"
down_revision = "0012_authz_enforcement"
branch_labels = None
depends_on = None

# 平台时间精度铁律 timestamptz(3)（CORE §10 · 0009 corrective）。
# `sa.DateTime` 结构性无法表达 precision ⇒ 必须用 postgresql.TIMESTAMP(precision=3)。
_TS = postgresql.TIMESTAMP(timezone=True, precision=3)

# 分区父表（子分区命名沿用 B1-6 先例形态 <parent>_<YYYYMM>；D-P10-09 / DC-1）
_EVENTS = "events"
_AUDIT = "audit_logs"

# D-P10-09：`event_type` 必须为**点分层级**的 canonical 形（`<domain>.<action>`）。
# 单段名（如 `login`）不合法 —— 强制命名空间，避免扁平词表漂移。
_EVENT_TYPE_RE = r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$"

# audit_logs.classification —— 与 CORE §7 四级一致（**可空**：NULL = 未分级/按策略）
_CLASSIFICATIONS = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")


def _month_bounds(parent: str) -> tuple[str, str, str]:
    """当月子分区的 (child_name, from_bound, to_bound) —— 一律 UTC calendar month。

    D-P10-09（FROZEN）：只建**当月**一个子分区；命名 = ``<parent>_<YYYYMM>``。
    """
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        nxt = start.replace(year=start.year + 1, month=1)
    else:
        nxt = start.replace(month=start.month + 1)
    return (
        f"{parent}_{start.strftime('%Y%m')}",
        start.strftime("%Y-%m-%d %H:%M:%S+00"),
        nxt.strftime("%Y-%m-%d %H:%M:%S+00"),
    )


def _child_partitions(parent: str) -> list[str]:
    """枚举某父表的实际子分区（downgrade 用；覆盖手工创建的月份分区 ⇒ 无孤儿）。"""
    rows = op.get_bind().execute(
        sa.text(
            "SELECT c.relname FROM pg_inherits i "
            "JOIN pg_class c ON c.oid = i.inhrelid "
            "JOIN pg_class p ON p.oid = i.inhparent "
            "WHERE p.relname = :parent ORDER BY c.relname"
        ),
        {"parent": parent},
    ).fetchall()
    return [r[0] for r in rows]


# --------------------------------------------------------------------------- #
# Function (1) — audit-local immutability（P10-owned，D-P10-11）
# --------------------------------------------------------------------------- #
# 设计要点（P10_IMPLEMENTATION_CONTRACT §8.2）：
#   * 归属 = P10（P11 **不得** create / replace / modify）
#   * failure semantics = RAISE ⇒ 语句失败 ⇒ 事务回滚（禁 silent ignore / warn-only）
#   * 无递归：audit_logs 上仅此一个 trigger；函数内**不做任何 DML**
#   * 无 search_path 依赖：函数体**不引用任何对象**（仅 RAISE）⇒ 天然免疫限定名解析风险
#   * privilege：默认 SECURITY INVOKER；不依赖 GRANT 才具不可变性
_AUDIT_IMMUTABLE_SQL = """
CREATE FUNCTION enforce_audit_logs_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION
    'audit_logs is append-only: % denied (tg_audit_immutable, D-P10-11)', TG_OP
    USING ERRCODE = 'raise_exception';
  RETURN NULL;  -- unreachable：RAISE 已终止语句
END;
$$;
"""


# --------------------------------------------------------------------------- #
# upgrade
# --------------------------------------------------------------------------- #
def upgrade() -> None:
    # ------------------------------------------------------------- [1] events
    # D-P10-01 = FROZEN：outbox 8 状态列一次建齐；本表**即** outbox 载体。
    op.create_table(
        _EVENTS,
        # E-01/E-02 —— UUIDv7（应用层生成，无 server_default；D-P10-02 / D-AUTH-22）
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", _TS, nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        # E-05/E-06 —— **无 FK**（事实日志；避免租户历史阻塞 purge；DISC-1）
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.Text(), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_type", sa.Text(), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        # E-11 —— 写入前 redaction 由应用层强制单点（D-P10-08）；DB 侧不加转换逻辑
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
        # ---- outbox 状态列（D-P10-01，一次建齐）----
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=True),
        sa.Column("claimed_at", _TS, nullable=True),
        sa.Column("lease_expires_at", _TS, nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("next_attempt_at", _TS, nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("delivered_at", _TS, nullable=True),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        # PK = (id, occurred_at)：分区键必须进 PK；UQ = 0、FK = 0（CONSTRAINT_MATRIX §7）
        sa.PrimaryKeyConstraint("id", "occurred_at"),
        sa.CheckConstraint(
            f"event_type ~ '{_EVENT_TYPE_RE}'", name="ck_events_event_type"
        ),
        sa.CheckConstraint(
            "status IN ('pending','claimed','delivered','dead')",
            name="ck_events_status",
        ),
        sa.CheckConstraint(
            "attempts >= 0 AND attempts <= 100", name="ck_events_attempts"
        ),
        postgresql_partition_by="RANGE (occurred_at)",
        # 无 updated_at ⇒ 无 set_updated_at trigger；**events 无任何 trigger**
        # （claim = 应用层 CAS，TRIGGER_INVENTORY §M）
    )

    # --------------------------------------------------------- [2] audit_logs
    # 无 updated_at / deleted_at ⇒ 结构性追加写；不可变性由 [5] 的 trigger 强制。
    op.create_table(
        _AUDIT,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", _TS, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        # A-07/A-08 —— PII：应用层最小化 / 脱敏（D-P10-08）
        sa.Column("actor_ip", postgresql.INET(), nullable=True),
        sa.Column("actor_user_agent", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        # A-12 —— 可空（NULL = 未分级/按策略）；分级只升不降（D-P10-14）
        sa.Column("classification", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        # A-16 —— 跨面关联键载体（Runtime 关联 run；不新增 linkage 列，D-P10-16）
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
        # A-18 —— Authorization Audit 五语义维度（subject/delegator/decision/policy/
        #         approval）以**结构化 metadata** 承载（D-P10-05；不新增列）
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.PrimaryKeyConstraint("id", "occurred_at"),
        sa.CheckConstraint(
            "result IN ('success','denied','error')", name="ck_audit_logs_result"
        ),
        sa.CheckConstraint(
            "risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_audit_logs_risk_level",
        ),
        sa.CheckConstraint(
            "classification IS NULL OR classification IN "
            "('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')",
            name="ck_audit_logs_classification",
        ),
        postgresql_partition_by="RANGE (occurred_at)",
    )

    # ------------------------------------- [3] 当月子分区（UTC calendar month）
    # 父表之后创建；**不建 DEFAULT 分区**（D-P10-09）
    for parent in (_EVENTS, _AUDIT):
        child, frm, to = _month_bounds(parent)
        op.execute(sa.text(
            f'CREATE TABLE "{child}" PARTITION OF {parent} '
            f"FOR VALUES FROM ('{frm}') TO ('{to}')"
        ))

    # ------------------------------------------------------------- [5] function
    # **先函数后触发器**（§11.2 [5] → [6]）；仅新建本函数，不 DROP 既有
    # set_updated_at() / uap_uuid_v7() / P09 的 enforce_*。
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_audit_logs_immutable()"))
    op.execute(sa.text(_AUDIT_IMMUTABLE_SQL))

    # ------------------------------------------------------------- [6] trigger
    # D-P10-11 = FROZEN：audit 的**基础**不可变性在 P10 内建立，**不依赖 P11**。
    op.execute(sa.text(
        "CREATE TRIGGER tg_audit_immutable "
        "BEFORE UPDATE OR DELETE ON audit_logs "
        "FOR EACH ROW EXECUTE FUNCTION enforce_audit_logs_immutable()"
    ))

    # [7] 索引 = 0（7 条 ix_events_* / ix_audit_* 归 P12，D-P12-08）
    # [8] seed = 0（P00–P12 无 seed；首个可登录主体只经 P13，D-PLAT-11）
    # [9] GRANT = 0（OPEN-P10-1 = DEFER，D-P10-13）


# --------------------------------------------------------------------------- #
# downgrade
# --------------------------------------------------------------------------- #
def downgrade() -> None:
    # [1] dependent trigger（先触发器）
    op.execute(sa.text("DROP TRIGGER IF EXISTS tg_audit_immutable ON audit_logs"))

    # [2] function（后函数；不得留下悬空函数）
    op.execute(sa.text("DROP FUNCTION IF EXISTS enforce_audit_logs_immutable()"))

    # [3] 子分区（**必须先于父表**）；动态枚举 ⇒ 兼容手工创建的月份分区，保证无孤儿
    for parent in (_AUDIT, _EVENTS):
        for child in _child_partitions(parent):
            op.execute(sa.text(f'DROP TABLE IF EXISTS "{child}"'))

    # [4] 父表（逆依赖序）
    for table in (_AUDIT, _EVENTS):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
