"""Company capability projection (OQ-CUI-01 = A · PDL Appendix AP).

A **read-only projection** of the existing authorization engine's decision for the
authenticated actor + tenant. It is deliberately not a second ACL engine: every
value comes from the very same ``_authorize`` gate the Company mutation use cases
run (see :func:`services.company.use_cases.company_capability`).

The projection never exposes role names, permission-engine internals or policy
internals — only the effective capability (allowed / denied per action) plus the
frozen Team / SELF disablement markers.
"""

from __future__ import annotations

from typing import Any

from domains.company import ASSIGNMENT_RESOURCE_TYPE, EMPLOYEE_RESOURCE_TYPE

from .use_cases import company_capability

#: The 8 operational Company actions, in the engine's **canonical** shape: the
#: authorization engine keys on ``(verb, resource_type)`` — the same call the
#: Company use cases make — never on the dotted permission key (the engine resolves
#: ``company_employee.read`` from ``("read", "company_employee")`` itself).
OPERATIONAL_ACTIONS: tuple[tuple[str, str], ...] = (
    ("read", EMPLOYEE_RESOURCE_TYPE),
    ("list", EMPLOYEE_RESOURCE_TYPE),
    ("create", EMPLOYEE_RESOURCE_TYPE),
    ("update", EMPLOYEE_RESOURCE_TYPE),
    ("read", ASSIGNMENT_RESOURCE_TYPE),
    ("list", ASSIGNMENT_RESOURCE_TYPE),
    ("create", ASSIGNMENT_RESOURCE_TYPE),
    ("update", ASSIGNMENT_RESOURCE_TYPE),
)

#: RESERVED permission keys: declared here for the record only. They have no API
#: surface and are never projected as capabilities (D-P20D-03/04).
RESERVED_PERMISSIONS: tuple[str, ...] = (
    "company_employee.delete",
    "company_employee.admin",
    "company_assignment.delete",
)

#: Frozen disablement markers (OQ-CUI-07 / OQ-CUI-08).
TEAM_STATE = "DISABLED"
SELF_STATE = "DISABLED"


def _permission_key(verb: str, resource_type: str) -> str:
    return f"{resource_type}.{verb}"


def project_capabilities(db: Any, *, actor_id: str, tenant_id: str) -> dict[str, Any]:
    """Effective Company capability for one authenticated actor in one tenant."""
    actions: dict[str, bool] = {}
    for verb, resource_type in OPERATIONAL_ACTIONS:
        actions[_permission_key(verb, resource_type)] = company_capability(
            db, actor_id=actor_id, tenant_id=tenant_id, action=verb, resource_type=resource_type
        )
    return {
        "tenant_id": str(tenant_id),
        "actions": actions,
        "operational": [_permission_key(v, r) for v, r in OPERATIONAL_ACTIONS],
        "reserved": list(RESERVED_PERMISSIONS),
        # The booleans above are the engine's own answer (platform_admin may hold a
        # RESERVED permission). What is frozen is that RESERVED actions have **no
        # API surface at all** — there is no DELETE/administrative route.
        "reserved_exposed": False,
        "team": TEAM_STATE,
        "self": SELF_STATE,
    }


__all__ = [
    "OPERATIONAL_ACTIONS",
    "RESERVED_PERMISSIONS",
    "SELF_STATE",
    "TEAM_STATE",
    "project_capabilities",
]
