"""B1-0 infrastructure: uap_uuid_v7() generator (RFC 9562)

Revision ID: 0002_b1_0_infrastructure
Revises: 0001_baseline
Create Date: 2026-09-07

Scope: B1-0-INFRASTRUCTURE-ONLY（无业务表）
--------------------------------------------------------------------
创建唯一的 UUIDv7 DB 兜底函数（STEP1B_UUID_STRATEGY 冻结方案）：

  * 48-bit Unix ms（大端，取自 int8 低 6 字节）
  * version 0111（byte 6 高 4 位）
  * variant 10xx（byte 8 高 2 位）
  * 随机位来自内置 gen_random_uuid()（PG 13+，无 pgcrypto 依赖）

不创建任何业务表 / 视图 / trigger。业务表由后续 B1-N revisions 建立。
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_b1_0_infrastructure"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

_UAP_UUID_V7_SQL = """
CREATE FUNCTION uap_uuid_v7() RETURNS uuid
LANGUAGE plpgsql VOLATILE PARALLEL SAFE AS $$
DECLARE
  g    uuid := gen_random_uuid();
  ms   bigint := (extract(epoch FROM clock_timestamp()) * 1000)::bigint;
  ts   bytea := substring(int8send(ms) FROM 3 FOR 6);
  bytes bytea := uuid_send(g);
  out  bytea;
BEGIN
  out := overlay(bytes PLACING ts FROM 1 FOR 6);
  out := set_byte(out, 6, (get_byte(out, 6) & 15) | 112);  -- 0x70 version 7
  out := set_byte(out, 8, (get_byte(out, 8) & 63) | 128);  -- 0x80 variant 10
  RETURN encode(out, 'hex')::uuid;
END;
$$;
"""


def upgrade() -> None:
    op.execute(sa.text("DROP FUNCTION IF EXISTS uap_uuid_v7()"))
    op.execute(sa.text(_UAP_UUID_V7_SQL))


def downgrade() -> None:
    op.execute(sa.text("DROP FUNCTION IF EXISTS uap_uuid_v7()"))
