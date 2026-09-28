"""Wave 1 §15 / §26 -- the Runtime identity must still be unable to escalate.

Every probe connects as ``uap_runtime`` (never migrator / bootstrap / superuser).
Probes run through :func:`probe`, which **always rolls the transaction back** --
whether the statement is refused or silently accepted -- so a probe can never
leave a permanent mutation behind.

A refused statement must be refused for the right reason: SQLSTATE 42501
(``InsufficientPrivilege``), not an unrelated syntax or type error.
"""

from __future__ import annotations

import pytest
from psycopg import errors as pg_errors
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.runtime import RuntimeDatabase
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn

pytestmark = pytest.mark.integration


class _AbortProbe(Exception):
    """Internal sentinel that forces the probe transaction to roll back."""


@pytest.fixture(scope="module")
def security_db():
    db = RuntimeDatabase.from_config(
        DatabaseConfig(url=runtime_test_dsn()), require_role=REQUIRED_ROLE
    )
    db.start()
    try:
        yield db
    finally:
        db.dispose()


def probe(db: RuntimeDatabase, sql: str) -> SQLAlchemyError | None:
    """Run ``sql`` as uap_runtime; **always** roll back. Return the DB error, if any."""
    try:
        with db.transaction() as session:
            session.execute(text(sql))
            raise _AbortProbe
    except _AbortProbe:
        return None
    except SQLAlchemyError as exc:
        return exc


def expect_denied(db: RuntimeDatabase, sql: str) -> str:
    exc = probe(db, sql)
    assert exc is not None, f"{sql!r} was NOT refused by the security boundary"
    orig = getattr(exc, "orig", None)
    assert isinstance(orig, pg_errors.InsufficientPrivilege), (
        f"{sql!r} was refused for the wrong reason: "
        f"{type(orig).__name__}: {str(exc).splitlines()[0]}"
    )
    return str(orig).splitlines()[0]


def scalar(db: RuntimeDatabase, sql: str):
    with db.transaction() as session:
        return session.execute(text(sql)).scalar()


def row(db: RuntimeDatabase, sql: str) -> tuple:
    with db.transaction() as session:
        return tuple(session.execute(text(sql)).one())


def fingerprint(db: RuntimeDatabase) -> dict[str, object]:
    with db.transaction() as session:
        return {
            "pg_class": session.execute(
                text(
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n"
                    " ON n.oid=c.relnamespace WHERE n.nspname='public'"
                    " AND c.relkind IN ('r','p','i','I')"
                )
            ).scalar(),
            "pg_proc": session.execute(
                text(
                    "SELECT count(*) FROM pg_proc p JOIN pg_namespace n"
                    " ON n.oid=p.pronamespace WHERE n.nspname='public'"
                )
            ).scalar(),
            "default_acl": session.execute(text("SELECT count(*) FROM pg_default_acl")).scalar(),
            "runtime_grants": session.execute(
                text(
                    "SELECT count(*) FROM information_schema.role_table_grants"
                    " WHERE grantee='uap_runtime'"
                )
            ).scalar(),
            "schema_create": session.execute(
                text("SELECT has_schema_privilege('uap_runtime','public','CREATE')")
            ).scalar(),
            "users_relacl": session.execute(
                text("SELECT relacl::text FROM pg_class WHERE oid='public.users'::regclass")
            ).scalar(),
        }


# ------------------------------------------------------------- identity binding
@pytest.mark.parametrize(
    "target", ["uap_migrator", "uap_bootstrap", "uap_seed", "uap_app"]
)
def test_principal_switching_is_denied(security_db, target: str) -> None:
    expect_denied(security_db, f"SET ROLE {target}")
    assert scalar(security_db, "SELECT current_user") == REQUIRED_ROLE
    assert scalar(security_db, "SELECT session_user") == REQUIRED_ROLE


@pytest.mark.parametrize("role", ["uap_migrator", "uap_bootstrap", "uap_seed"])
def test_privileged_roles_are_unreachable_by_membership(security_db, role: str) -> None:
    assert scalar(
        security_db, f"SELECT pg_has_role(current_user, '{role}', 'MEMBER')"
    ) is False
    assert scalar(
        security_db, f"SELECT pg_has_role(current_user, '{role}', 'USAGE')"
    ) is False


# ---------------------------------------------------------------------- no DDL
@pytest.mark.parametrize(
    "sql",
    [
        "CREATE ROLE uap_wave1_probe_role LOGIN",
        "CREATE ROLE uap_wave1_probe_role2 SUPERUSER",
        "CREATE SCHEMA uap_wave1_probe_schema",
        "CREATE TABLE public.uap_wave1_probe_table (id integer)",
        "CREATE VIEW public.uap_wave1_probe_view AS SELECT 1 AS one",
        "CREATE MATERIALIZED VIEW public.uap_wave1_probe_mv AS SELECT 1 AS one",
        "CREATE SEQUENCE public.uap_wave1_probe_seq",
        "CREATE TYPE public.uap_wave1_probe_type AS ENUM ('a')",
        "CREATE INDEX uap_wave1_probe_idx ON public.users (status)",
        "CREATE FUNCTION public.uap_wave1_probe_fn() RETURNS integer"
        " LANGUAGE sql AS $$ SELECT 1 $$",
        "CREATE TRIGGER uap_wave1_probe_trg BEFORE INSERT ON public.users"
        " FOR EACH ROW EXECUTE FUNCTION public.enforce_acl_subject_types_protect()",
    ],
)
def test_schema_object_creation_is_denied(security_db, sql: str) -> None:
    expect_denied(security_db, sql)


@pytest.mark.parametrize(
    "sql",
    [
        "ALTER TABLE public.users ADD COLUMN uap_wave1_probe integer",
        "ALTER TABLE public.users OWNER TO uap_runtime",
        "ALTER TABLE public.resource_permissions OWNER TO uap_runtime",
        "ALTER SCHEMA public OWNER TO uap_runtime",
        "ALTER ROLE uap_runtime CREATEDB",
        "ALTER ROLE uap_runtime SUPERUSER",
        "COMMENT ON TABLE public.users IS 'wave1 probe'",
        "DROP TABLE public.users",
        "DROP TABLE public.resource_permissions",
        "DROP SCHEMA public CASCADE",
        "DROP ROLE uap_migrator",
    ],
)
def test_ddl_and_ownership_mutation_is_denied(security_db, sql: str) -> None:
    expect_denied(security_db, sql)


def test_catalog_is_unchanged_by_the_denied_ddl(security_db) -> None:
    before = fingerprint(security_db)
    for sql in (
        "CREATE TABLE public.uap_wave1_probe_table2 (id integer)",
        "CREATE SCHEMA uap_wave1_probe_schema2",
        "DROP TABLE public.users",
        "ALTER TABLE public.users OWNER TO uap_runtime",
    ):
        expect_denied(security_db, sql)
    assert fingerprint(security_db) == before


# ----------------------------------------------- privilege mutation is inert
def test_privilege_mutation_attempts_are_inert(security_db) -> None:
    """GRANT / REVOKE / ALTER DEFAULT PRIVILEGES must not move the fingerprint.

    PostgreSQL answers these with a *warning* (not an error) when the caller has
    no grant option, so the probe only proves what matters: whatever the engine
    says, the ACL and the default-ACL fingerprint are untouched afterwards.
    """
    before = fingerprint(security_db)
    for sql in (
        "GRANT SELECT ON public.users TO uap_seed",
        "GRANT INSERT ON public.resource_permissions TO uap_runtime",
        "REVOKE SELECT ON public.users FROM uap_runtime",
        "ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO uap_seed",
    ):
        probe(security_db, sql)
    assert fingerprint(security_db) == before
    assert scalar(
        security_db, "SELECT has_table_privilege('uap_seed','public.users','SELECT')"
    ) is False
    assert scalar(
        security_db,
        "SELECT has_table_privilege('uap_runtime','public.resource_permissions','INSERT')",
    ) is False


# --------------------------------------------------------- protected write faces
@pytest.mark.parametrize(
    "table,column",
    [
        ("resource_permissions", "effect"),
        ("platform_memberships", "status"),
        ("platform_state", "bootstrap_state"),
        ("tenants", "slug"),
        ("spaces", "name"),
    ],
)
def test_protected_tables_reject_every_write(security_db, table: str, column: str) -> None:
    expect_denied(
        security_db, f"INSERT INTO public.{table} SELECT * FROM public.{table} WHERE false"
    )
    expect_denied(security_db, f"UPDATE public.{table} SET {column} = {column} WHERE false")
    expect_denied(security_db, f"DELETE FROM public.{table}")


def test_credentials_physical_delete_is_denied(security_db) -> None:
    """SEC-08: credentials may be created/updated but never physically deleted."""
    expect_denied(security_db, "DELETE FROM public.credentials")
    assert row(
        security_db,
        "SELECT has_table_privilege('uap_runtime','public.credentials','INSERT'),"
        " has_table_privilege('uap_runtime','public.credentials','UPDATE')",
    ) == (True, True)


@pytest.mark.parametrize("table", ["audit_logs", "events"])
def test_audit_faces_reject_delete(security_db, table: str) -> None:
    expect_denied(security_db, f"DELETE FROM public.{table}")


# ------------------------------------------------------- frozen grant fingerprint
def test_runtime_grant_fingerprint_is_exact(security_db) -> None:
    with security_db.transaction() as session:
        rows = session.execute(
            text(
                "SELECT table_name, privilege_type FROM information_schema.role_table_grants"
                " WHERE grantee='uap_runtime' ORDER BY table_name, privilege_type"
            )
        ).all()
        function_execute = session.execute(
            text(
                "SELECT count(*) FROM information_schema.role_routine_grants"
                " WHERE grantee='uap_runtime'"
            )
        ).scalar()
        schema_priv = session.execute(
            text(
                "SELECT has_schema_privilege('uap_runtime','public','CREATE'),"
                " has_schema_privilege('uap_runtime','public','USAGE')"
            )
        ).one()
        default_acl = session.execute(text("SELECT count(*) FROM pg_default_acl")).scalar()
        memberships = session.execute(
            text(
                "SELECT count(*) FROM pg_auth_members am"
                " JOIN pg_roles m ON m.oid=am.member JOIN pg_roles g ON g.oid=am.roleid"
                " WHERE m.rolname NOT LIKE 'pg\\_%' OR g.rolname NOT LIKE 'pg\\_%'"
            )
        ).scalar()

    assert len(rows) == 51, "runtime row-grant fingerprint drifted"
    assert function_execute == 0
    assert tuple(schema_priv) == (False, True)
    assert default_acl == 0
    assert memberships == 0


def test_delete_faces_match_the_matrix(security_db) -> None:
    with security_db.transaction() as session:
        granted = {
            row[0]
            for row in session.execute(
                text(
                    "SELECT table_name FROM information_schema.role_table_grants"
                    " WHERE grantee='uap_runtime' AND privilege_type='DELETE'"
                )
            )
        }
    assert granted == {"sessions", "memberships", "tenant_memberships"}
