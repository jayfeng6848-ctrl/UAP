"""Read-only access to the authorization state.

The only module in the authorization service that touches the database, and it
only ever reads. Every statement is parameter bound; nothing here writes, and
nothing here decides — decisions belong to ``AuthorizationService``.

Note: ``agent_permissions.resource_scope`` is deliberately never selected. It is
an opaque P09 field that is not an authorization authority; deriving any grant
from it is forbidden.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Engine
from sqlalchemy.engine import Row

from infrastructure.database.session import session_scope

from .errors import AuthorizationUnavailable

_ACTIVE_USER_STATUS = "active"
_ACTIVE_AGENT_STATUS = "active"
_ACTIVE_MEMBERSHIP_STATUS = "active"
_ACTIVE_ROLE_STATUS = "active"


class AuthorizationRepository:
    """Parameter-bound read-only queries over the authorization tables."""

    def __init__(self, engine: Engine | None = None) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ helpers
    def _fetch(self, sql: str, params: dict[str, Any]) -> list[Row[Any]]:
        try:
            with session_scope(self._engine) as session:
                return list(session.execute(sa.text(sql), params).fetchall())
        except Exception as exc:  # pragma: no cover - depends on infrastructure
            raise AuthorizationUnavailable(str(exc)) from exc

    def _fetch_one(self, sql: str, params: dict[str, Any]) -> Row[Any] | None:
        rows = self._fetch(sql, params)
        return rows[0] if rows else None

    # ------------------------------------------------------------------ subjects
    def get_user(self, user_id: str) -> Row[Any] | None:
        return self._fetch_one(
            "SELECT id, status, primary_identity_id FROM users WHERE id = :uid",
            {"uid": user_id},
        )

    def get_agent(self, agent_id: str) -> Row[Any] | None:
        return self._fetch_one(
            "SELECT id, tenant_id, space_id, owner_id, status, max_risk_level "
            "FROM agents WHERE id = :aid",
            {"aid": agent_id},
        )

    def get_role(self, role_id: str) -> Row[Any] | None:
        return self._fetch_one(
            "SELECT id, tenant_id, space_id, key, scope, status "
            "FROM roles WHERE id = :rid",
            {"rid": role_id},
        )

    # ------------------------------------------------------------------ grants
    def role_ids_for_user(
        self, user_id: str, tenant_id: str | None, space_id: str | None
    ) -> list[str]:
        """Role ids bound to a user across platform, tenant and space levels."""
        found: list[str] = []

        rows = self._fetch(
            "SELECT role_id FROM platform_memberships "
            "WHERE user_id = :uid AND status = :st",
            {"uid": user_id, "st": _ACTIVE_MEMBERSHIP_STATUS},
        )
        found.extend(str(row._mapping["role_id"]) for row in rows)

        if tenant_id is not None:
            rows = self._fetch(
                "SELECT role_id FROM tenant_memberships "
                "WHERE user_id = :uid AND tenant_id = :tid AND status = :st",
                {"uid": user_id, "tid": tenant_id, "st": _ACTIVE_MEMBERSHIP_STATUS},
            )
            found.extend(str(row._mapping["role_id"]) for row in rows)

        if tenant_id is not None and space_id is not None:
            rows = self._fetch(
                "SELECT role_id FROM memberships "
                "WHERE user_id = :uid AND tenant_id = :tid AND space_id = :sid "
                "AND status = :st",
                {"uid": user_id, "tid": tenant_id, "sid": space_id, "st": _ACTIVE_MEMBERSHIP_STATUS},
            )
            found.extend(str(row._mapping["role_id"]) for row in rows)

        return found

    def get_roles(self, role_ids: Iterable[str]) -> list[Row[Any]]:
        ids = [str(rid) for rid in role_ids]
        if not ids:
            return []
        return self._fetch(
            "SELECT id, tenant_id, space_id, key, scope, status FROM roles "
            "WHERE id = ANY(:ids)",
            {"ids": ids},
        )

    def agent_grants(self, agent_id: str) -> list[Row[Any]]:
        """Agent-level grants from ``agent_permissions``.

        Only the structured targets are selected: a permission reference, a tool
        reference and the effect. The opaque restriction column on that table is
        deliberately **not** selected — it is not an authorization authority and
        no grant may ever be derived from it.
        """
        return self._fetch(
            "SELECT ap.effect, ap.permission_id, ap.tool_id, "
            "p.key, p.resource_type, p.action "
            "FROM agent_permissions ap "
            "LEFT JOIN permissions p ON p.id = ap.permission_id "
            "WHERE ap.agent_id = :aid",
            {"aid": agent_id},
        )

    def role_grants(self, role_ids: Sequence[str]) -> list[Row[Any]]:
        """Effective RBAC grants: ``(role_id, key, resource_type, action, effect)``."""
        ids = [str(rid) for rid in role_ids]
        if not ids:
            return []
        return self._fetch(
            "SELECT rp.role_id, p.key, p.resource_type, p.action, rp.effect "
            "FROM role_permissions rp JOIN permissions p ON p.id = rp.permission_id "
            "WHERE rp.role_id = ANY(:ids)",
            {"ids": ids},
        )

    # ------------------------------------------------------------------ resources
    def get_resource(self, resource_id: str) -> Row[Any] | None:
        return self._fetch_one(
            "SELECT id, tenant_id, space_id, owner_id, resource_type, "
            "classification, status FROM resources WHERE id = :rid",
            {"rid": resource_id},
        )

    def acl_entries(self, resource_id: str) -> list[Row[Any]]:
        """ACL rows for a resource, joined to the subject-type whitelist."""
        return self._fetch(
            "SELECT rp.subject_id, ast.key AS subject_type, rp.action, rp.effect, "
            "rp.inherited, rp.expires_at "
            "FROM resource_permissions rp "
            "JOIN acl_subject_types ast ON ast.id = rp.subject_type_id "
            "WHERE rp.resource_id = :rid",
            {"rid": resource_id},
        )

    # ------------------------------------------------------------------ tools
    def get_tool(self, tool_id: str) -> Row[Any] | None:
        return self._fetch_one(
            "SELECT id, tenant_id, key, name, risk_level, approval_required, enabled "
            "FROM tools WHERE id = :tid",
            {"tid": tool_id},
        )

    def tool_grants(self, tool_id: str) -> list[Row[Any]]:
        """Structured tool grants (``resource_type`` / ``action`` / ``scope``)."""
        return self._fetch(
            "SELECT tp.effect, tp.resource_type, tp.action, tp.scope, p.key "
            "FROM tool_permissions tp JOIN permissions p ON p.id = tp.permission_id "
            "WHERE tp.tool_id = :tid",
            {"tid": tool_id},
        )


__all__ = ["AuthorizationRepository"]
