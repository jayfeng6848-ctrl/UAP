"""0016_open_p10_1_trust_boundary — CC-7 Trust Boundary rewrite.

Replaces ``public.enforce_acl_subject_types_protect()`` (first created by
0007_b1_4_resource_acl.py:78, trigger ``tg_acl_subject_types_protect``) with the
CC-7 trusted-migration-identity variant decided in
``OPEN_P10_1_BATCH_C_DECISION_RECORD.md`` (CF-C-6 = A: 0016 scope is strictly the
CC-7 rewrite; nothing else).

Trust predicate (C2 = CP-F, `D-OP101-04`), BOTH must hold — this is a database
execution-identity check, never a connection-string / GUC / application_name /
environment check:

    current_user = 'uap_migrator' AND session_user = 'uap_migrator'

Semantics:

* trusted migration execution context  -> the registry is migration-controlled:
  INSERT / UPDATE / DELETE pass through untouched (RETURN NEW / RETURN OLD);
* every other identity (runtime)       -> behavior byte-identical to the 0007
  pre-image: INSERT denied, DELETE denied, ``key`` immutable on UPDATE.

Invariants kept (see OPEN_P10_1_BATCH_C_IMPLEMENTATION_PRE_FLIGHT_REPORT.md §6):

* signature unchanged: ``() RETURNS trigger``, LANGUAGE plpgsql, SECURITY INVOKER
  (no SECURITY DEFINER — forbidden platform-wide, `D-P11-08`);
* role / ownership / grant statements: none (privilege window is orchestration
  outside this file, CF-C-5 = B / OI-DC-2);
* no dynamic SQL, no GUC / application_name / SET ROLE / env-var trust;
* downgrade restores the exact 0007 pre-image definition
  (``md5(pg_get_functiondef) = 6867874166ae36966763c1026ab2af19``) — no guessing.

First cross-migration security-function replacement in this repository
(0007 created the function; 0014's four CREATE OR REPLACE statements are
first-creations of its own functions — replacement precedent was 0 before 0016).
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_open_p10_1_trust_boundary"
down_revision = "0015_p12_indexes"
branch_labels = None
depends_on = None

# md5(pg_get_functiondef) of the 0007 pre-image; downgrade() must restore it.
PRE_IMAGE_MD5 = "6867874166ae36966763c1026ab2af19"

# --------------------------------------------------------------------------- #
# CC-7 post-image — trusted migration identity gate + unchanged runtime guard
# --------------------------------------------------------------------------- #
_CC7_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION enforce_acl_subject_types_protect() RETURNS trigger
LANGUAGE plpgsql AS $fn$
BEGIN
  -- CC-7 trusted migration execution context (C2 = CP-F): BOTH current_user
  -- and session_user must be the migration identity. A mere SET ROLE mask is
  -- not trusted (session_user remains the login role).
  IF current_user = 'uap_migrator' AND session_user = 'uap_migrator' THEN
    IF TG_OP = 'DELETE' THEN
      RETURN OLD;
    END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'INSERT' THEN
    RAISE EXCEPTION
      'acl_subject_types is a platform-controlled registry: runtime INSERT denied '
      '(registry rows are migration-controlled)';
  ELSIF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION
      'acl_subject_types rows cannot be deleted (retire via archived_at)';
  ELSE  -- UPDATE
    IF NEW.key IS DISTINCT FROM OLD.key THEN
      RAISE EXCEPTION 'acl_subject_types.key is immutable (registry governance)';
    END IF;
    RETURN NEW;
  END IF;
END;
$fn$;
"""

# --------------------------------------------------------------------------- #
# downgrade pre-image — the 0007 definition, byte-identical body (PROVENANCE:
# copied verbatim from migrations_alembic/versions/0007_b1_4_resource_acl.py
# `_ACL_SUBJECT_TYPES_PROTECT_SQL`; fingerprint = PRE_IMAGE_MD5 above).
# --------------------------------------------------------------------------- #
_PRE_IMAGE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION enforce_acl_subject_types_protect() RETURNS trigger
LANGUAGE plpgsql AS $fn$
BEGIN
  IF TG_OP = 'INSERT' THEN
    RAISE EXCEPTION
      'acl_subject_types is a platform-controlled registry: runtime INSERT denied '
      '(registry rows are migration-controlled)';
  ELSIF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION
      'acl_subject_types rows cannot be deleted (retire via archived_at)';
  ELSE  -- UPDATE
    IF NEW.key IS DISTINCT FROM OLD.key THEN
      RAISE EXCEPTION 'acl_subject_types.key is immutable (registry governance)';
    END IF;
    RETURN NEW;
  END IF;
END;
$fn$;
"""


def upgrade() -> None:
    op.execute(sa.text(_CC7_FUNCTION_SQL))


def downgrade() -> None:
    op.execute(sa.text(_PRE_IMAGE_FUNCTION_SQL))
