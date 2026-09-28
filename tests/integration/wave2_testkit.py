"""Shared test kit for the P14 Wave 2 suites.

Two clearly separated identities:

* **RUNTIME identity** (`UAP_RUNTIME_TEST_DSN`, role ``uap_runtime``) — every
  behavioural assertion in the Wave 2 suites runs through this connection, so the
  evidence cannot be a false positive produced by a privileged role
  (Wave 1 §17).
* **FIXTURE identity** (``alembic_testkit.BASE_DSN``) — the controlled
  ``uap_b1_test`` database only. ``uap_runtime`` legitimately holds **no**
  INSERT on ``tenants`` / ``spaces`` / ``roles`` (SEC-05), so the membership and
  authorization fixtures cannot be created by the runtime identity at all. The
  fixture identity is used *only* to seed and clean those rows; it never asserts
  runtime behaviour. Provisioning is net-zero: the suite deletes exactly what it
  created (verified by the freeze fingerprint afterwards).
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass

import sqlalchemy as sa

from tests.integration.alembic_testkit import BASE_DSN
from tests.integration.runtime_testkit import REQUIRED_ROLE, runtime_test_dsn
from services.use_cases import (
    authenticate_identity,
    complete_device_enrollment,
    onboard_identity,
    start_device_enrollment,
)

__all__ = [
    "BASE_DSN",
    "REQUIRED_ROLE",
    "Wave2Fixture",
    "activate_identity",
    "enroll_device",
    "new_login",
    "provision_active_user",
    "provision_tenant_space_membership",
    "run_sql",
    "runtime_data_scope",
    "runtime_test_dsn",
]


@dataclass(frozen=True)
class Wave2Fixture:
    """Ids of a provisioned tenant / space / role + membership."""

    tenant_id: str
    space_id: str
    tenant_role_id: str
    space_role_id: str
    tenant_membership_id: str
    space_membership_id: str


@contextlib.contextmanager
def provision_tenant_space_membership(user_id: str, *, active: bool = True):
    """Seed a tenant + space + PLATFORM-admin role binding for ``user_id``.

    Cleaned up on exit so the frozen test baseline returns to
    ``tenants = 0 · spaces = 0 · roles = 1``.
    """
    engine = sa.create_engine(BASE_DSN, future=True)
    fixture: Wave2Fixture | None = None
    try:
        with engine.begin() as conn:
            tenant_id = conn.execute(
                sa.text(
                    "INSERT INTO tenants (slug, display_name, status)"
                    " VALUES (:slug, :name, 'active') RETURNING id"
                ),
                {"slug": f"w2-{uuid.uuid4().hex[:12]}", "name": "Wave2 Tenant"},
            ).scalar_one()
            space_id = conn.execute(
                sa.text(
                    "INSERT INTO spaces (tenant_id, key, name, kind, visibility, status)"
                    " VALUES (:tid, :key, :name, 'team', 'tenant', 'active') RETURNING id"
                ),
                {"tid": tenant_id, "key": f"w2-{uuid.uuid4().hex[:8]}", "name": "Wave2 Space"},
            ).scalar_one()
            # P11 triggers enforce role/scope agreement:
            #   tenant_memberships -> active TENANT role of the same tenant
            #   memberships        -> active SPACE role of the same tenant+space
            tenant_role_id = conn.execute(
                sa.text(
                    "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                    " VALUES (:tid, NULL, :key, :name, 'TENANT', 'active') RETURNING id"
                ),
                {
                    "tid": tenant_id,
                    "key": f"w2_trole_{uuid.uuid4().hex[:8]}",
                    "name": "Wave2 Tenant Role",
                },
            ).scalar_one()
            space_role_id = conn.execute(
                sa.text(
                    "INSERT INTO roles (tenant_id, space_id, key, name, scope, status)"
                    # enforce_roles_scope_shape(): SPACE role = tenant_id NULL,
                    # space_id NOT NULL.
                    " VALUES (NULL, :sid, :key, :name, 'SPACE', 'active') RETURNING id"
                ),
                {
                    "sid": space_id,
                    "key": f"w2_srole_{uuid.uuid4().hex[:8]}",
                    "name": "Wave2 Space Role",
                },
            ).scalar_one()
            status = "active" if active else "suspended"
            tenant_membership_id = conn.execute(
                sa.text(
                    "INSERT INTO tenant_memberships (user_id, tenant_id, role_id, status)"
                    " VALUES (:uid, :tid, :rid, :status) RETURNING id"
                ),
                {
                    "uid": user_id,
                    "tid": tenant_id,
                    "rid": tenant_role_id,
                    "status": status,
                },
            ).scalar_one()
            space_membership_id = conn.execute(
                sa.text(
                    "INSERT INTO memberships (user_id, tenant_id, space_id, role_id, status)"
                    " VALUES (:uid, :tid, :sid, :rid, :status) RETURNING id"
                ),
                {
                    "uid": user_id,
                    "tid": tenant_id,
                    "sid": space_id,
                    "rid": space_role_id,
                    "status": status,
                },
            ).scalar_one()
        fixture = Wave2Fixture(
            tenant_id=str(tenant_id),
            space_id=str(space_id),
            tenant_role_id=str(tenant_role_id),
            space_role_id=str(space_role_id),
            tenant_membership_id=str(tenant_membership_id),
            space_membership_id=str(space_membership_id),
        )
        yield fixture
    finally:
        if fixture is not None:
            with engine.begin() as conn:
                conn.execute(
                    sa.text("DELETE FROM memberships WHERE id = :id"),
                    {"id": fixture.space_membership_id},
                )
                conn.execute(
                    sa.text("DELETE FROM tenant_memberships WHERE id = :id"),
                    {"id": fixture.tenant_membership_id},
                )
                conn.execute(
                    sa.text("DELETE FROM roles WHERE id = ANY(CAST(:ids AS uuid[]))"),
                    {"ids": [fixture.tenant_role_id, fixture.space_role_id]},
                )
                conn.execute(
                    sa.text("DELETE FROM spaces WHERE id = :id"), {"id": fixture.space_id}
                )
                conn.execute(
                    sa.text("DELETE FROM tenants WHERE id = :id"), {"id": fixture.tenant_id}
                )
        engine.dispose()


@contextlib.contextmanager
def runtime_data_scope():
    """Track and clean the identity rows a Wave 2 suite creates.

    * ``users`` / ``identities`` / ``credentials`` / ``devices`` / ``sessions``
      are removed through the fixture identity via ``users`` cascade, so those
      tables return to their frozen baseline (0 rows).
    * ``audit_logs`` is **append-only by design** (``tg_audit_immutable``,
      D-P10-11): DELETE is refused even for the fixture identity, so audit rows
      produced by these suites are *permanent* and are declared as
      **EXPECTED TEST DATA** in the Wave 2 report.

    The cleanup identity is never used to assert runtime behaviour.
    """
    engine = sa.create_engine(BASE_DSN, future=True)
    created_users: list[str] = []

    def track(user_id: str) -> str:
        created_users.append(str(user_id))
        return str(user_id)

    try:
        yield track
    finally:
        if created_users:
            with engine.begin() as conn:
                conn.execute(
                    sa.text("DELETE FROM users WHERE id = ANY(CAST(:ids AS uuid[]))"),
                    {"ids": created_users},
                )
        engine.dispose()


# --------------------------------------------------------------------------- #
# Runtime-identity helpers (all executed through uap_runtime)
# --------------------------------------------------------------------------- #
def new_login() -> str:
    return f"w2-{uuid.uuid4().hex[:12]}@example.invalid"


def activate_identity(db, *, email: str, password: str) -> tuple[str, str]:
    """Authenticate once so ``unverified -> active`` (verification, §十)."""
    identity = authenticate_identity(db, login=email, password=password)
    return identity.user_id, identity.identity_id


def enroll_device(db, *, email: str, password: str, fingerprint: str | None = None) -> str:
    """Full enrollment flow; returns the ``active`` device id."""
    fp = fingerprint or f"fp-{uuid.uuid4().hex[:12]}"
    challenge = start_device_enrollment(
        db, login=email, password=password, fingerprint=fp, label="wave2"
    )
    device = complete_device_enrollment(
        db, challenge_id=challenge.challenge_id, secret=challenge.secret, fingerprint=fp
    )
    return device.device_id


def provision_active_user(db, track, *, password: str = "Wave2-Passw0rd!") -> dict[str, str]:
    """Onboard + verify + enroll one device; every row is tracked for cleanup."""
    email = new_login()
    onboarded = onboard_identity(db, email=email, password=password)
    track(onboarded.user_id)
    user_id, identity_id = activate_identity(db, email=email, password=password)
    device_id = enroll_device(db, email=email, password=password)
    return {
        "email": email,
        "password": password,
        "user_id": user_id,
        "identity_id": identity_id,
        "device_id": device_id,
    }


def run_sql(db, sql: str, params: dict | None = None) -> None:
    """Execute a statement as the **runtime** identity (used to age/alter state)."""
    with db.transaction() as session:
        session.execute(sa.text(sql), params or {})
