"""P11 — canonical ACL triggers G/H/I/J (D-P11-01..14).

Semantics (FROZEN, `PLATFORM_DECISION_LOG.md` §P11 + `P11_IMPLEMENTATION_CONTRACT.md`):

  G  tg_acl_subject_exists     resource_permissions  BEFORE INSERT OR UPDATE OF
                               (subject_type_id, subject_id) — subject existence only
                               (user→users.id / role→roles.id / agent→agents.id);
                               NOT an authorization evaluator; never references `groups`.
  H  tg_acl_user_hard_delete   users AFTER DELETE — purge that user's ACL rows only
                               (hard-delete path; soft delete never fires this).
  I  tg_acl_role_delete_block  roles BEFORE DELETE — reject deletion while the role is
                               still referenced by resource_permissions (reference
                               protection, not authorization). Behaviorally compatible
                               with the three pre-existing BEFORE DELETE triggers on
                               `roles` (name-order firing; any RAISE aborts the DELETE).
  J  tg_agent_acl_expire       agents AFTER UPDATE OF status OR AFTER DELETE — expire the
                               agent's ACL rows (inherited = true, expires_at = now());
                               data retained. J MUST NOT touch subject_type_id/subject_id
                               ⇒ J → G recursion = ∅ (D-P11-09: J SET list ∩ G watched
                               columns = ∅).

All four functions are SECURITY INVOKER (default; `D-P11-08` — SECURITY DEFINER is
forbidden platform-wide), raise on violation (`D-P11-04` FAIL-CLOSED: the surrounding
transaction rolls back), never write audit rows (`D-P11-14`), and perform no seed
(`D-P11-12`). No indexes are created here — the reverse-lookup path
`resource_permissions(subject_type_id, subject_id)` is already served by
`ix_rp_subject` (0007 / P06); new P12 dependency = 0 (`D-P11-11`).

upgrade: functions → G → H → I → J
downgrade: J → I → H → G → functions (strict reverse; zero residue)
"""

import sqlalchemy as sa
from alembic import op

revision = "0014_p11_triggers"
down_revision = "0013_p10_event_audit"
branch_labels = None
depends_on = None

# --------------------------------------------------------------------------- #
# object inventories (downgrade iterates these in strict reverse order)
# --------------------------------------------------------------------------- #
_FUNCTIONS = (
    "enforce_acl_subject_exists",
    "enforce_acl_user_hard_delete",
    "enforce_acl_role_delete_block",
    "enforce_agent_acl_expire",
)

_TRIGGERS = (
    ("tg_acl_subject_exists", "resource_permissions"),
    ("tg_acl_user_hard_delete", "users"),
    ("tg_acl_role_delete_block", "roles"),
    ("tg_agent_acl_expire", "agents"),
)


def upgrade() -> None:
    # ------------------------------------------------------------- functions
    # G — subject existence (structural integrity only; D-P11-02/07)
    op.execute(sa.text(
        "CREATE OR REPLACE FUNCTION enforce_acl_subject_exists() RETURNS trigger"
        " LANGUAGE plpgsql AS $fn$"
        " DECLARE"
        "     v_key text;"
        " BEGIN"
        "     SELECT key INTO v_key FROM acl_subject_types WHERE id = NEW.subject_type_id;"
        "     IF v_key IS NULL THEN"
        "         RAISE EXCEPTION 'acl subject type % is not registered',"
        "             NEW.subject_type_id;"
        "     END IF;"
        "     IF v_key = 'user' THEN"
        "         IF NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.subject_id) THEN"
        "             RAISE EXCEPTION 'acl subject user % does not exist',"
        "                 NEW.subject_id;"
        "         END IF;"
        "     ELSIF v_key = 'role' THEN"
        "         IF NOT EXISTS (SELECT 1 FROM roles WHERE id = NEW.subject_id) THEN"
        "             RAISE EXCEPTION 'acl subject role % does not exist',"
        "                 NEW.subject_id;"
        "         END IF;"
        "     ELSIF v_key = 'agent' THEN"
        "         IF NOT EXISTS (SELECT 1 FROM agents WHERE id = NEW.subject_id) THEN"
        "             RAISE EXCEPTION 'acl subject agent % does not exist',"
        "                 NEW.subject_id;"
        "         END IF;"
        "     ELSE"
        "         RAISE EXCEPTION 'unregistered acl subject type key %', v_key;"
        "     END IF;"
        "     RETURN NEW;"
        " END;"
        " $fn$"
    ))

    # H — user hard delete purges that user's ACL rows only (D-P11-02)
    op.execute(sa.text(
        "CREATE OR REPLACE FUNCTION enforce_acl_user_hard_delete() RETURNS trigger"
        " LANGUAGE plpgsql AS $fn$"
        " BEGIN"
        "     DELETE FROM resource_permissions rp"
        "      WHERE rp.subject_id = OLD.id"
        "        AND rp.subject_type_id = (SELECT id FROM acl_subject_types"
        "                                   WHERE key = 'user');"
        "     RETURN NULL;"
        " END;"
        " $fn$"
    ))

    # I — role delete block while ACL-referenced (reference protection; D-P11-02)
    op.execute(sa.text(
        "CREATE OR REPLACE FUNCTION enforce_acl_role_delete_block() RETURNS trigger"
        " LANGUAGE plpgsql AS $fn$"
        " BEGIN"
        "     IF EXISTS (SELECT 1 FROM resource_permissions rp"
        "                 WHERE rp.subject_id = OLD.id"
        "                   AND rp.subject_type_id = (SELECT id FROM acl_subject_types"
        "                                              WHERE key = 'role')) THEN"
        "         RAISE EXCEPTION 'role % is still referenced by resource_permissions',"
        "             OLD.id;"
        "     END IF;"
        "     RETURN OLD;"
        " END;"
        " $fn$"
    ))

    # J — agent archival/deletion expires its ACL rows; SET list ∩ G watched cols = ∅
    op.execute(sa.text(
        "CREATE OR REPLACE FUNCTION enforce_agent_acl_expire() RETURNS trigger"
        " LANGUAGE plpgsql AS $fn$"
        " BEGIN"
        "     IF TG_OP = 'UPDATE' AND NEW.status <> 'archived' THEN"
        "         RETURN NULL;"
        "     END IF;"
        "     UPDATE resource_permissions"
        "        SET inherited = true, expires_at = now()"
        "      WHERE subject_id = OLD.id"
        "        AND subject_type_id = (SELECT id FROM acl_subject_types"
        "                                WHERE key = 'agent');"
        "     RETURN NULL;"
        " END;"
        " $fn$"
    ))

    # ------------------------------------------------------------- triggers
    # G
    op.execute(sa.text(
        "CREATE TRIGGER tg_acl_subject_exists"
        " BEFORE INSERT OR UPDATE OF subject_type_id, subject_id"
        " ON resource_permissions"
        " FOR EACH ROW EXECUTE FUNCTION enforce_acl_subject_exists()"
    ))
    # H
    op.execute(sa.text(
        "CREATE TRIGGER tg_acl_user_hard_delete"
        " AFTER DELETE ON users"
        " FOR EACH ROW EXECUTE FUNCTION enforce_acl_user_hard_delete()"
    ))
    # I
    op.execute(sa.text(
        "CREATE TRIGGER tg_acl_role_delete_block"
        " BEFORE DELETE ON roles"
        " FOR EACH ROW EXECUTE FUNCTION enforce_acl_role_delete_block()"
    ))
    # J
    op.execute(sa.text(
        "CREATE TRIGGER tg_agent_acl_expire"
        " AFTER UPDATE OF status OR DELETE ON agents"
        " FOR EACH ROW EXECUTE FUNCTION enforce_agent_acl_expire()"
    ))


def downgrade() -> None:
    # strict reverse: triggers (J → I → H → G) then functions (reverse creation order)
    for trigger, table in reversed(_TRIGGERS):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger} ON {table}"))
    for fn in reversed(_FUNCTIONS):
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {fn}()"))
