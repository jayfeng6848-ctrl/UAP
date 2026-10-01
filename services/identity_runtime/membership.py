"""Membership runtime — the only P17 write surface (P17 WAVE 4 · D04/D11/OQ-08).

Every mutation runs inside the caller's transaction together with its audit
append, so ``audit failure ⇒ membership mutation rolls back`` (the inverse of the
P16 failure-durability pattern, and the correct semantics for a security
mutation).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.audit.interfaces import new_event_id
from core.permission.vocabulary import STORED_SCOPES

from .errors import ErrorCode, IdentityRuntimeError
from .repository import ACTIVE, MembershipRepository, SpaceRepository

TENANT_SCOPE, SPACE_SCOPE = STORED_SCOPES[1], STORED_SCOPES[2]


class MembershipRuntime:
    """Server-side validated membership mutations with atomic audit evidence."""

    def __init__(
        self,
        *,
        repository: MembershipRepository | None = None,
        spaces: SpaceRepository | None = None,
    ) -> None:
        self._repo = repository or MembershipRepository()
        self._spaces = spaces or SpaceRepository()

    # ------------------------------------------------------------- validation
    def _validate_tenant_target(self, session: Session, *, tenant_id: str, user_id: str, role_id: str) -> None:
        if not self._repo.user_exists(session, user_id=user_id):
            raise IdentityRuntimeError(ErrorCode.TARGET_NOT_FOUND, "target user not found")
        if not self._repo.tenant_exists(session, tenant_id=tenant_id):
            raise IdentityRuntimeError(ErrorCode.TARGET_NOT_FOUND, "tenant not found")
        role = self._repo.get_role(session, role_id=role_id)
        if role is None or str(role.get("status")) not in ("active", "published"):
            raise IdentityRuntimeError(ErrorCode.TARGET_NOT_FOUND, "role not assignable")
        if str(role.get("scope")) != TENANT_SCOPE:
            raise IdentityRuntimeError(ErrorCode.ROLE_SCOPE_MISMATCH, "role is not tenant-scoped")
        if role.get("space_id") is not None:
            raise IdentityRuntimeError(ErrorCode.ROLE_SCOPE_MISMATCH, "tenant role must not be space-bound")
        if role.get("tenant_id") is not None and str(role["tenant_id"]) != tenant_id:
            raise IdentityRuntimeError(ErrorCode.ROLE_SCOPE_MISMATCH, "role belongs to another tenant")

    def _validate_space_target(
        self, session: Session, *, tenant_id: str, space_id: str, user_id: str, role_id: str
    ) -> None:
        if not self._repo.user_exists(session, user_id=user_id):
            raise IdentityRuntimeError(ErrorCode.TARGET_NOT_FOUND, "target user not found")
        # P17-AUTH §19/§68-14: a space member must already belong to the tenant;
        # a space membership never creates tenant standing (N8).
        if not self._repo.has_active_tenant_membership(
            session, tenant_id=tenant_id, user_id=user_id
        ):
            raise IdentityRuntimeError(
                ErrorCode.TARGET_NOT_IN_TENANT, "target user is not a member of this tenant"
            )
        if not self._spaces.space_belongs_to_tenant(session, tenant_id=tenant_id, space_id=space_id):
            raise IdentityRuntimeError(ErrorCode.SPACE_SCOPE_DENIED, "space is not in this tenant")
        role = self._repo.get_role(session, role_id=role_id)
        if role is None or str(role.get("status")) not in ("active", "published"):
            raise IdentityRuntimeError(ErrorCode.TARGET_NOT_FOUND, "role not assignable")
        if str(role.get("scope")) != SPACE_SCOPE:
            raise IdentityRuntimeError(ErrorCode.ROLE_SCOPE_MISMATCH, "role is not space-scoped")
        if role.get("space_id") is not None and str(role["space_id"]) != space_id:
            raise IdentityRuntimeError(ErrorCode.ROLE_SCOPE_MISMATCH, "role belongs to another space")
        if role.get("tenant_id") is not None and str(role["tenant_id"]) != tenant_id:
            raise IdentityRuntimeError(ErrorCode.ROLE_SCOPE_MISMATCH, "role belongs to another tenant")

    # ------------------------------------------------------------------ audit
    def _audit(
        self,
        session: Session,
        *,
        action: str,
        actor_type: str,
        actor_id: str,
        tenant_id: str,
        space_id: str | None,
        target_user_id: str,
        role_after: str | None,
        role_before: str | None,
        correlation_id: str,
    ) -> None:
        metadata: dict[str, Any] = {
            "action": action,
            "target_user_id": target_user_id,
            "role_after": role_after,
        }
        if role_before is not None:
            metadata["role_before"] = role_before
        session.execute(
            text(
                "INSERT INTO audit_logs (id, occurred_at, tenant_id, space_id, actor_type, actor_id,"
                " action, result, risk_level, correlation_id, metadata, created_at)"
                " VALUES (CAST(:id AS uuid), now(), CAST(:tenant AS uuid), CAST(:space AS uuid),"
                " :actor_type, CAST(:actor AS uuid), :action, 'success', 'LOW',"
                " CAST(:correlation AS uuid), CAST(:meta AS jsonb), now())"
            ),
            {
                "id": new_event_id(),
                "tenant": tenant_id,
                "space": space_id,
                "actor_type": actor_type,
                "actor": actor_id,
                "action": action,
                "correlation": correlation_id,
                "meta": json.dumps(metadata),
            },
        )

    # ------------------------------------------------------- tenant membership
    def create_tenant_membership(
        self, session: Session, *, actor_id: str, actor_type: str, tenant_id: str, user_id: str,
        role_id: str, correlation_id: str,
    ) -> str:
        self._validate_tenant_target(session, tenant_id=tenant_id, user_id=user_id, role_id=role_id)
        if self._repo.get_tenant_membership(session, tenant_id=tenant_id, user_id=user_id) is not None:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_DUPLICATE, "membership already exists")
        membership_id = str(uuid.uuid4())
        session.execute(
            text(
                "INSERT INTO tenant_memberships (id, tenant_id, user_id, role_id, status,"
                " role_assigned_at, role_assigned_by) VALUES (CAST(:id AS uuid),"
                " CAST(:tenant AS uuid), CAST(:user AS uuid), CAST(:role AS uuid), :status, now(),"
                " CAST(:actor AS uuid))"
            ),
            {"id": membership_id, "tenant": tenant_id, "user": user_id, "role": role_id,
             "status": ACTIVE, "actor": actor_id},
        )
        self._audit(session, action="create", actor_type=actor_type, actor_id=actor_id,
                    tenant_id=tenant_id, space_id=None, target_user_id=user_id,
                    role_after=role_id, role_before=None, correlation_id=correlation_id)
        return membership_id

    def update_tenant_membership(
        self, session: Session, *, actor_id: str, actor_type: str, tenant_id: str, user_id: str,
        role_id: str, correlation_id: str,
    ) -> None:
        self._validate_tenant_target(session, tenant_id=tenant_id, user_id=user_id, role_id=role_id)
        current = self._repo.get_tenant_membership(session, tenant_id=tenant_id, user_id=user_id)
        if current is None or str(current.get("status")) != ACTIVE:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership not found")
        updated = session.execute(
            text(
                "UPDATE tenant_memberships SET role_id = CAST(:role AS uuid),"
                " role_assigned_at = now(), role_assigned_by = CAST(:actor AS uuid), updated_at = now()"
                " WHERE tenant_id = CAST(:tenant AS uuid) AND user_id = CAST(:user AS uuid)"
                " AND status = :status"
            ),
            {"role": role_id, "actor": actor_id, "tenant": tenant_id, "user": user_id, "status": ACTIVE},
        ).rowcount
        if updated != 1:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership update matched no row")
        self._audit(session, action="update", actor_type=actor_type, actor_id=actor_id,
                    tenant_id=tenant_id, space_id=None, target_user_id=user_id, role_after=role_id,
                    role_before=str(current["role_id"]), correlation_id=correlation_id)

    def delete_tenant_membership(
        self, session: Session, *, actor_id: str, actor_type: str, tenant_id: str, user_id: str,
        correlation_id: str,
    ) -> None:
        current = self._repo.get_tenant_membership(session, tenant_id=tenant_id, user_id=user_id)
        if current is None or str(current.get("status")) != ACTIVE:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership not found")
        removed = session.execute(
            text(
                "UPDATE tenant_memberships SET status = 'removed', removed_at = now(), updated_at = now()"
                " WHERE tenant_id = CAST(:tenant AS uuid) AND user_id = CAST(:user AS uuid)"
                " AND status = :status"
            ),
            {"tenant": tenant_id, "user": user_id, "status": ACTIVE},
        ).rowcount
        if removed != 1:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership removal matched no row")
        # role_before is captured *before* the row changes: the audit fact survives removal.
        self._audit(session, action="delete", actor_type=actor_type, actor_id=actor_id,
                    tenant_id=tenant_id, space_id=None, target_user_id=user_id, role_after=None,
                    role_before=str(current["role_id"]), correlation_id=correlation_id)

    # -------------------------------------------------------- space membership
    def create_space_membership(
        self, session: Session, *, actor_id: str, actor_type: str, tenant_id: str, space_id: str,
        user_id: str, role_id: str, correlation_id: str,
    ) -> str:
        self._validate_space_target(session, tenant_id=tenant_id, space_id=space_id, user_id=user_id,
                                    role_id=role_id)
        if self._repo.get_space_membership(session, tenant_id=tenant_id, space_id=space_id,
                                           user_id=user_id) is not None:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_DUPLICATE, "membership already exists")
        membership_id = str(uuid.uuid4())
        session.execute(
            text(
                "INSERT INTO memberships (id, tenant_id, space_id, user_id, role_id, status, joined_at)"
                " VALUES (CAST(:id AS uuid), CAST(:tenant AS uuid), CAST(:space AS uuid),"
                " CAST(:user AS uuid), CAST(:role AS uuid), :status, now())"
            ),
            {"id": membership_id, "tenant": tenant_id, "space": space_id, "user": user_id,
             "role": role_id, "status": ACTIVE},
        )
        self._audit(session, action="create", actor_type=actor_type, actor_id=actor_id,
                    tenant_id=tenant_id, space_id=space_id, target_user_id=user_id,
                    role_after=role_id, role_before=None, correlation_id=correlation_id)
        return membership_id

    def update_space_membership(
        self, session: Session, *, actor_id: str, actor_type: str, tenant_id: str, space_id: str,
        user_id: str, role_id: str, correlation_id: str,
    ) -> None:
        self._validate_space_target(session, tenant_id=tenant_id, space_id=space_id, user_id=user_id,
                                    role_id=role_id)
        current = self._repo.get_space_membership(session, tenant_id=tenant_id, space_id=space_id,
                                                  user_id=user_id)
        if current is None or str(current.get("status")) != ACTIVE:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership not found")
        updated = session.execute(
            text(
                "UPDATE memberships SET role_id = CAST(:role AS uuid), updated_at = now()"
                " WHERE tenant_id = CAST(:tenant AS uuid) AND space_id = CAST(:space AS uuid)"
                " AND user_id = CAST(:user AS uuid) AND status = :status"
            ),
            {"role": role_id, "tenant": tenant_id, "space": space_id, "user": user_id, "status": ACTIVE},
        ).rowcount
        if updated != 1:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership update matched no row")
        self._audit(session, action="update", actor_type=actor_type, actor_id=actor_id,
                    tenant_id=tenant_id, space_id=space_id, target_user_id=user_id, role_after=role_id,
                    role_before=str(current["role_id"]), correlation_id=correlation_id)

    def delete_space_membership(
        self, session: Session, *, actor_id: str, actor_type: str, tenant_id: str, space_id: str,
        user_id: str, correlation_id: str,
    ) -> None:
        current = self._repo.get_space_membership(session, tenant_id=tenant_id, space_id=space_id,
                                                  user_id=user_id)
        if current is None or str(current.get("status")) != ACTIVE:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership not found")
        removed = session.execute(
            text(
                "UPDATE memberships SET status = 'removed', removed_at = now(), updated_at = now()"
                " WHERE tenant_id = CAST(:tenant AS uuid) AND space_id = CAST(:space AS uuid)"
                " AND user_id = CAST(:user AS uuid) AND status = :status"
            ),
            {"tenant": tenant_id, "space": space_id, "user": user_id, "status": ACTIVE},
        ).rowcount
        if removed != 1:
            raise IdentityRuntimeError(ErrorCode.MEMBERSHIP_NOT_FOUND, "membership removal matched no row")
        self._audit(session, action="delete", actor_type=actor_type, actor_id=actor_id,
                    tenant_id=tenant_id, space_id=space_id, target_user_id=user_id, role_after=None,
                    role_before=str(current["role_id"]), correlation_id=correlation_id)
