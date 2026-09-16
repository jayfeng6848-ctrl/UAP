"""0003_b1_1_root_identity — five core Identity tables

Revision ID: 0003_b1_1_root_identity
Revises: 0002_b1_0_infrastructure
Create Date: 2026-09-07

Scope: B1-1（仅 5 张 Identity 表；无任何 Tenant/Space/RBAC/ACL/AI/Event/Domain 表）

   users → identities → credentials
   users → devices     → sessions (identity RESTRICT / device CASCADE)

遵循冻结设计（CORE_DOMAIN_MODEL §1.1 + B0 CONSTRAINT_MATRIX / INDEX_STRATEGY /
TRIGGER_INVENTORY / UUID_STRATEGY）。逐字段核对见
docs/architecture/STEP1B_B1_1_SCHEMA_REVIEW.md。

实现约定
  * id uuid PRIMARY KEY DEFAULT uap_uuid_v7()（B1-0 函数，仅兜底）
  * citext 不用：email/username 为 text + lower() 表达式索引
  * created_at/updated_at timestamptz；updated_at 由 set_updated_at() trigger 维护
  * 状态/枚举：text + CHECK（不用 PG enum）
  * 无明文列：仅 secret_hash / token_hash / refresh_token_hash（哈希）
  * users.primary_identity_id 不加 FK（冻结设计无此边，避免循环）
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_b1_1_root_identity"
down_revision = "0002_b1_0_infrastructure"
branch_labels = None
depends_on = None

_SET_UPDATED_AT_SQL = """
CREATE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;
"""

UPDATED_AT_TABLES = ("users", "identities", "credentials", "devices", "sessions")


def _bind_updated_at_triggers() -> None:
    for table in UPDATED_AT_TABLES:
        op.execute(
            sa.text(
                f"CREATE TRIGGER tg_{table}_set_updated_at "
                f"BEFORE UPDATE ON {table} FOR EACH ROW "
                f"EXECUTE FUNCTION set_updated_at()"
            )
        )


def upgrade() -> None:
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at()"))
    op.execute(sa.text(_SET_UPDATED_AT_SQL))

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("primary_identity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','active','suspended','locked','deleted')",
            name="ck_users_status",
        ),
        sa.CheckConstraint(
            "email IS NOT NULL OR username IS NOT NULL",
            name="ck_users_login",
        ),
    )
    # email/username: text + lower() expression unique indexes (no citext)
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_users_email ON users (lower(email)) "
            "WHERE deleted_at IS NULL"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_users_username ON users (lower(username)) "
            "WHERE deleted_at IS NULL"
        )
    )

    op.create_table(
        "identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("issuer", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_identities_user"),
        sa.CheckConstraint("provider IN ('local','oidc','saml','device','service')", name="ck_identities_provider"),
        sa.CheckConstraint("status IN ('active','unverified','suspended','revoked')", name="ck_identities_status"),
    )
    # expression-based: (provider, COALESCE(issuer,''), subject)
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_identities_ref ON identities "
            "(provider, COALESCE(issuer, ''), subject)"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_identities_email ON identities (provider, lower(email)) "
            "WHERE email IS NOT NULL AND revoked_at IS NULL"
        )
    )
    op.create_index("ix_identities_user", "identities", ["user_id"])

    op.create_table(
        "credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("secret_hash", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.Text(), nullable=False),
        sa.Column("secret_hint", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["identity_id"], ["identities.id"], ondelete="CASCADE", name="fk_credentials_identity"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_credentials_user"),
        sa.CheckConstraint("type IN ('password','api_key','recovery_code','device_cert','otp')", name="ck_credentials_type"),
        sa.CheckConstraint("algorithm IN ('argon2id','scrypt','sha256_hmac')", name="ck_credentials_algorithm"),
        sa.CheckConstraint("secret_hash <> ''", name="ck_credentials_secret"),
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_credentials_active_password ON credentials (identity_id) "
            "WHERE type = 'password' AND revoked_at IS NULL"
        )
    )
    op.create_index("ix_credentials_user", "credentials", ["user_id"])

    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.Column("app_version", sa.Text(), nullable=True),
        sa.Column("public_key", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_last", postgresql.INET(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_devices_user"),
        sa.CheckConstraint("status IN ('pending','active','untrusted','revoked','lost')", name="ck_devices_status"),
    )
    op.create_index("uq_devices_fingerprint", "devices", ["user_id", "fingerprint"], unique=True)
    op.create_index("ix_devices_user_status", "devices", ["user_id", "status"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uap_uuid_v7()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("ip_created", postgresql.INET(), nullable=True),
        sa.Column("ip_last", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("replaced_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_sessions_user"),
        sa.ForeignKeyConstraint(["identity_id"], ["identities.id"], ondelete="RESTRICT", name="fk_sessions_identity"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE", name="fk_sessions_device"),
        sa.CheckConstraint("status IN ('active','expired','revoked')", name="ck_sessions_status"),
        sa.CheckConstraint("expires_at > created_at", name="ck_sessions_expiry"),
    )
    op.create_index("uq_sessions_token", "sessions", ["token_hash"], unique=True)
    op.create_index(
        "uq_sessions_refresh", "sessions", ["refresh_token_hash"], unique=True,
        postgresql_where=sa.text("refresh_token_hash IS NOT NULL"),
    )
    op.create_index("ix_sessions_user_status", "sessions", ["user_id", "status"])
    op.create_index("ix_sessions_identity", "sessions", ["identity_id"])
    op.create_index("ix_sessions_device", "sessions", ["device_id"])
    op.create_index(
        "ix_sessions_expires_active", "sessions", ["expires_at"],
        postgresql_where=sa.text("status = 'active'"),
    )

    _bind_updated_at_triggers()


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS sessions"))
    op.execute(sa.text("DROP TABLE IF EXISTS devices"))
    op.execute(sa.text("DROP TABLE IF EXISTS credentials"))
    op.execute(sa.text("DROP TABLE IF EXISTS identities"))
    op.execute(sa.text("DROP TABLE IF EXISTS users"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at()"))
