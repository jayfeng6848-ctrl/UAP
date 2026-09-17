"""0010_b1_6_ai_gateway — P08 AI Gateway（provider / model / route / policy / request log）

Revision ID: 0010_b1_6_ai_gateway
Revises: 0009_timestamp_precision
Create Date: 2026-09-17

Scope: B1-6 / P08 — 5 tables（含 1 分区父表 + 1 当月子分区）, 0 seed, 4 triggers, 0 new function.

  ai_providers         厂商/网关连接的**数据化**描述（平台级 ROOT，无 tenant_id）
  ai_models            模型能力 / 成本 / 合规上限目录（provider 技术子实体）
  ai_routes            capability → primary model 的路由与 fallback 链
  ai_policies          分级 → 供应商准入 / fallback / 预算 / 延迟策略
  ai_request_logs      成本 / 配额 / 可观测（分区表；不存 prompt 原文，非审计）

冻结来源（逐项核对见 docs/architecture/B1-6_SCHEMA_DESIGN.md / B1-6_DECISION_LOG.md /
B1-6_MIGRATION_PLAN.md；本 revision 只实现，不重新设计）：

  D-B16-01 = A（FROZEN）B1-6 = P08 AI Gateway
  D-B16-02 = A（FROZEN）ai_routes / ai_policies 的 tenant_id / space_id →
                         tenants.id / spaces.id **ON DELETE RESTRICT**（四列均 nullable）
  D-B16-03 = A（FROZEN）ai_request_logs.provider_id → ai_providers.id RESTRICT
                         ai_request_logs.model_id    → ai_models.id     RESTRICT
                         **agent_id / actor_id / tenant_id / space_id 一律无 FK**
                         ⇒ P08 → P09 forward FK = 0
  D-B16-04 = A（FROZEN）ai_request_logs.status：**CHECK = 0**（不定义 status vocabulary）
  D-B16-05 = A（FROZEN）ai_request_logs：P08 建**父表 + 当月子分区**
  D-B16-06 = A（FROZEN）ai_providers.adapter = opaque text（无 CK/UQ/FK，不解析/不加载/不注册）
  D-B16-07 = A（FROZEN）UNIQUE CONSTRAINT = 2 · UNIQUE INDEX = 2
                         （表达式唯一性只能是 unique INDEX，不计入 constraint）
  D-B16-08 = C（FROZEN）不回改 B0；`SCHEMA_DEPENDENCY:136` 的「Phase 08」为陈旧引用，
                         `agents.current_version_id` deferred FK 属 **P09**
  D-B16-09 = A（FROZEN）B1-6 9 份文档模式
  D-B16-10 = A（FROZEN）独立编号空间 canonical test matrix（S5 对该 status 明确豁免）
  D-B16-11 = A（FROZEN）ai_providers = 平台级 ROOT / 无 tenant_id / 零 seed

  设计层裁定（B1-6_DECISION_LOG.md §9）：
  D-1 = B（FROZEN）ai_policies 的 budget_daily_usd >= 0 / latency_budget_ms >= 0 **不实现**
  D-2 = B（FROZEN）ix_aimodels_capability **不建立**
  T-1 = DEFERRED    该索引的 B0 定义引用了不存在的列；本 revision 不建、不改 B0、不作废
  D-3 = D（FROZEN）分区维护 = **手工运维**；本 revision 不做预建/清理/job/scheduler/pg_partman/扩展
  D-4 = A（FROZEN）ai_request_logs 列名 = prompt_tokens + completion_tokens
  DC-1 = A（FROZEN）子分区命名 = ai_request_logs_<YYYYMM>（UTC calendar month）

对象计数（实测口径见 B1-6_SCHEMA_DESIGN.md §7）：
  tables = 5 · columns = 73 · PK = 5 · FK = 8（CASCADE 1 + RESTRICT 7）
  CK = 8 · status CK = 0 · UNIQUE CONSTRAINT = 2 · UNIQUE INDEX = 2
  non-PK INDEX = 5（含 2 个由 UNIQUE CONSTRAINT 隐式建立）· trigger = 4 · function 新增 = 0
  partition = 父表 1 + 当月子分区 1 · seed = 0

本 revision **不做任何 seed**（P00–P10 无 seed 需求；P13 才有）：
  * 5 张表初始 rows 均为 0；不 INSERT provider / model / route / policy / log

边界（强制）：
  * 不含 agents / agent_versions / agent_permissions / tool_executions（P09）
  * 不含 events / audit_logs（P10）· 不含 resource_relations
  * 不建 agents.default_route_id / fk_agents_current_version（P09 侧建立）
  * 不含 RLS · 不含 Authorization Evaluation · 不含 ABAC / policy evaluator
  * 不含 provider adapter runtime / SDK loading / handler execution / plugin registry
  * 不含 HTTP API / Socket / worker / scheduler / partition automation
  * 不新增未冻结的 CHECK · 不新增未冻结的索引 · 不引入任何 Domain 语义
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_b1_6_ai_gateway"
down_revision = "0009_timestamp_precision"
branch_labels = None
depends_on = None

_TABLES = ("ai_providers", "ai_models", "ai_routes", "ai_policies", "ai_request_logs")

_PARENT = "ai_request_logs"

# 表达式唯一索引的稳定 "NULL 占位"值（与 0008 的 uq_tool_perm 同惯例）。
# B0 文档以 ``COALESCE(tenant_id,'0...')`` 简写指代该占位语义。
_NIL_UUID = "00000000-0000-0000-0000-000000000000"

# 平台时间精度铁律 timestamptz(3)（CORE §10 · 0009 corrective）。
# `sa.DateTime` 结构性无法表达 precision ⇒ 必须用 postgresql.TIMESTAMP(precision=3)。
_TS = postgresql.TIMESTAMP(timezone=True, precision=3)


def _month_bounds() -> tuple[str, str, str]:
    """当月子分区的 (child_name, from_bound, to_bound) —— 一律 UTC calendar month。

    DC-1 = A（FROZEN）：子分区命名 = ``ai_request_logs_<YYYYMM>``。
    D-B16-05 = A（FROZEN）：P08 只建**当月**一个子分区。
    """
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        nxt = start.replace(year=start.year + 1, month=1)
    else:
        nxt = start.replace(month=start.month + 1)
    return (
        f"{_PARENT}_{start.strftime('%Y%m')}",
        start.strftime("%Y-%m-%d %H:%M:%S+00"),
        nxt.strftime("%Y-%m-%d %H:%M:%S+00"),
    )


def _child_partitions() -> list[str]:
    """枚举 ai_request_logs 的实际子分区（downgrade 用；覆盖手工创建的月份分区）。"""
    rows = op.get_bind().execute(sa.text(
        "SELECT c.relname FROM pg_inherits i "
        "JOIN pg_class c ON c.oid = i.inhrelid "
        "JOIN pg_class p ON p.oid = i.inhparent "
        "WHERE p.relname = :parent"
    ), {"parent": _PARENT}).fetchall()
    return [r[0] for r in rows]


# --------------------------------------------------------------------------- #
# upgrade
# --------------------------------------------------------------------------- #
def upgrade() -> None:
    # ------------------------------------------------------------ ai_providers
    # D-B16-11 = A（FROZEN）：平台级 ROOT —— **无 tenant_id 列**、无 FK
    op.create_table(
        "ai_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        # D-B16-06 = A（FROZEN）：opaque 文本引用（无 CK / 无 UQ / 无 FK；不构成代码执行入口）
        sa.Column("adapter", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("health_status", sa.Text(), nullable=False),
        sa.Column("health_checked_at", _TS, nullable=True),
        sa.Column("privacy_tier", sa.Text(), nullable=False),
        sa.Column("max_classification", sa.Text(), nullable=False),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        # config 明确「不含密钥」（CORE §10 安全）；secret_ref 只存引用
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("secret_ref", sa.Text(), nullable=True),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", _TS, nullable=False, server_default=sa.text("now()")),
        # 纯列唯一 ⇒ UNIQUE CONSTRAINT（D-B16-07 = A：constraint 形式）
        sa.UniqueConstraint("key", name="uq_ai_providers_key"),
        sa.CheckConstraint(
            "privacy_tier IN ('public','vetted','private','self_hosted')",
            name="ck_ai_providers_privacy_tier"),
        sa.CheckConstraint(
            "max_classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')",
            name="ck_ai_providers_max_classification"),
        sa.CheckConstraint(
            "health_status IN ('unknown','healthy','degraded','down')",
            name="ck_ai_providers_health_status"),
        # `key` 不做 regex/format CK（opaque application identifier，沿用既有惯例）
    )

    # --------------------------------------------------------------- ai_models
    op.create_table(
        "ai_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        # DC-3：numeric 不限定精度（B0 未规定 numeric(p,s)）
        sa.Column("input_price_per_1k", sa.Numeric(), nullable=True),
        sa.Column("output_price_per_1k", sa.Numeric(), nullable=True),
        sa.Column("max_classification", sa.Text(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("latency_p95_ms", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", _TS, nullable=False, server_default=sa.text("now()")),
        # 技术子实体：模型目录随 provider 受控 purge 清理（CORE §11.1 白名单）
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"],
                                ondelete="CASCADE", name="fk_ai_models_provider"),
        sa.UniqueConstraint("provider_id", "model_key", name="uq_ai_models"),
        sa.CheckConstraint(
            "max_classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','HIGHLY_CONFIDENTIAL')",
            name="ck_ai_models_max_classification"),
        sa.CheckConstraint("context_window > 0", name="ck_ai_models_context_window"),
    )

    # --------------------------------------------------------------- ai_routes
    op.create_table(
        "ai_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        # NULL = 平台默认路由（nullable 保持；D-B16-02 = A 只加 FK，不改 NOT NULL）
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("capability", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("primary_model_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fallback_chain", postgresql.JSONB(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", _TS, nullable=False, server_default=sa.text("now()")),
        # 业务实体一律 RESTRICT（CORE §11.1；D-B16-02 = A FROZEN）
        sa.ForeignKeyConstraint(["primary_model_id"], ["ai_models.id"],
                                ondelete="RESTRICT", name="fk_ai_routes_primary_model"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                ondelete="RESTRICT", name="fk_ai_routes_tenant"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"],
                                ondelete="RESTRICT", name="fk_ai_routes_space"),
        sa.CheckConstraint(
            "capability IN ('chat','embeddings','rerank','vision',"
            "'audio_asr','audio_tts','moderation')",
            name="ck_ai_routes_capability"),
        sa.CheckConstraint("priority >= 0", name="ck_ai_routes_priority"),
        # 不建立 tenant/space 一致性 trigger（TRIGGER_INVENTORY 无该条目）
    )

    # ------------------------------------------------------------- ai_policies
    op.create_table(
        "ai_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("max_classification", sa.Text(), nullable=False),
        sa.Column("allowed_privacy_tiers", postgresql.JSONB(), nullable=True),
        sa.Column("denied_providers", postgresql.JSONB(), nullable=True),
        sa.Column("require_private", sa.Boolean(), nullable=False),
        sa.Column("allow_fallback", sa.Boolean(), nullable=False),
        sa.Column("fallback_preserves_classification", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        # D-1 = B（FROZEN）：**不实现** budget_daily_usd >= 0 / latency_budget_ms >= 0
        sa.Column("budget_daily_usd", sa.Numeric(), nullable=True),
        sa.Column("latency_budget_ms", sa.Integer(), nullable=True),
        sa.Column("redaction_profile", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", _TS, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"],
                                ondelete="RESTRICT", name="fk_ai_policies_tenant"),
        sa.ForeignKeyConstraint(["space_id"], ["spaces.id"],
                                ondelete="RESTRICT", name="fk_ai_policies_space"),
        # 数据架构铁律 5（HIGHLY_CONFIDENTIAL 禁止因故障降级到公共模型）的 DB 层落地
        sa.CheckConstraint(
            "allow_fallback = false OR fallback_preserves_classification = true",
            name="ck_ai_policies_no_unguarded_fallback"),
    )

    # ---------------------------------------------- ai_request_logs（分区父表）
    # D-B16-05 = A（FROZEN）：PARTITION BY RANGE (occurred_at)；分区键必须进 PK
    op.create_table(
        _PARENT,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("uap_uuid_v7()")),
        sa.Column("occurred_at", _TS, nullable=False, server_default=sa.text("now()")),
        # D-B16-03 = A（FROZEN）：以下四列**一律无 FK**（不构成 P08 → P09 前向依赖）
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("capability", sa.Text(), nullable=False),
        sa.Column("classification", sa.Text(), nullable=False),
        # D-4 = A（FROZEN）：CORE 细分命名（非单一 `tokens`）
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        # D-B16-04 = A（FROZEN）：status **无取值域 CHECK**（S5 对该列 EXEMPT）
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "occurred_at"),
        # 分区表 → 普通表的 FK（PG 支持；声明在父表，自动下推至子分区）
        sa.ForeignKeyConstraint(["provider_id"], ["ai_providers.id"],
                                ondelete="RESTRICT", name="fk_ai_request_logs_provider"),
        sa.ForeignKeyConstraint(["model_id"], ["ai_models.id"],
                                ondelete="RESTRICT", name="fk_ai_request_logs_model"),
        postgresql_partition_by="RANGE (occurred_at)",
        # 本表无 updated_at ⇒ 无 set_updated_at trigger；无 UQ ⇒ 不涉及分区唯一键约束
    )

    # ------------------------------------------- 当月子分区（UTC calendar month）
    child, frm, to = _month_bounds()
    op.execute(sa.text(
        f'CREATE TABLE "{child}" PARTITION OF {_PARENT} '
        f"FOR VALUES FROM ('{frm}') TO ('{to}')"
    ))

    # ----------------------------------------------------- 表达式唯一索引（2）
    # D-B16-07 = A（FROZEN）：表达式唯一性必须是 unique INDEX（不能是 UNIQUE CONSTRAINT）
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_ai_routes ON ai_routes ("
        f"COALESCE(tenant_id, '{_NIL_UUID}'::uuid), "
        f"COALESCE(space_id, '{_NIL_UUID}'::uuid), "
        "capability, priority)"
    ))
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_ai_policies ON ai_policies ("
        f"COALESCE(tenant_id, '{_NIL_UUID}'::uuid), "
        f"COALESCE(space_id, '{_NIL_UUID}'::uuid), "
        "lower(name))"
    ))

    # ------------------------------------------------- 查询索引（1，建在父表）
    # D-2 = B（FROZEN）：ix_aimodels_capability **不建立**（T-1 = DEFERRED）
    op.execute(sa.text(
        "CREATE INDEX ix_airl_tenant_occurred ON ai_request_logs "
        "(tenant_id, occurred_at DESC)"
    ))

    # ------------------------------------------------------------- triggers（4）
    # 复用既有 set_updated_at()（不重建函数）；ai_request_logs 无 updated_at ⇒ 无 trigger
    for table in ("ai_providers", "ai_models", "ai_routes", "ai_policies"):
        op.execute(sa.text(
            f"CREATE TRIGGER tg_{table}_set_updated_at BEFORE UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
        ))

    # 无 seed（B1-6 = P08；5 张表初始 rows = 0）


# --------------------------------------------------------------------------- #
# downgrade（严格逆序：trigger → 索引 → 子分区 → 父表 → 表）
# --------------------------------------------------------------------------- #
def downgrade() -> None:
    # [1] triggers（依赖表的触发器先移除）
    for table in ("ai_policies", "ai_routes", "ai_models", "ai_providers"):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS tg_{table}_set_updated_at ON {table}"))

    # [2] indexes（在 DROP TABLE 之前显式移除；uq_ai_providers_key / uq_ai_models 随表移除）
    op.execute(sa.text("DROP INDEX IF EXISTS ix_airl_tenant_occurred"))
    op.execute(sa.text("DROP INDEX IF EXISTS uq_ai_policies"))
    op.execute(sa.text("DROP INDEX IF EXISTS uq_ai_routes"))

    # [3] 子分区（**必须先于父表**，SCHEMA_DEPENDENCY §9 / MIGRATION_PLAN §5）
    #     动态枚举实际子分区 ⇒ 兼容手工创建的月份分区，保证无 orphan。
    for child in _child_partitions():
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{child}"'))

    # [4] tables（逆依赖序；ai_request_logs 父表在子分区之后）
    for table in reversed(_TABLES):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
