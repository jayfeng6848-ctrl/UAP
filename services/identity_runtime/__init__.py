"""P17 platform identity / tenant / space runtime.

Context resolution + membership runtime on top of the frozen schema. It adds no
schema, no migration and no new runtime privilege; it reuses the existing
authorization service for decisions and the existing audit carrier for evidence.
"""

from .errors import IdentityRuntimeError, ErrorCode
from .agent_scope import (
    AgentBinding,
    AgentScopeRepository,
    AgentScopeResolver,
    resolve_agent_execution_context,
)
from .authorization import MembershipAuthorizer, safe_reason_code
from .membership import MembershipRuntime
from .repository import (
    MembershipRepository,
    MembershipResourceRepository,
    SpaceRepository,
    TenantRepository,
)
from .resolver import ResolvedContext, RuntimeContextResolver

__all__ = [
    "AgentBinding",
    "AgentScopeRepository",
    "AgentScopeResolver",
    "ErrorCode",
    "IdentityRuntimeError",
    "MembershipAuthorizer",
    "MembershipRepository",
    "MembershipResourceRepository",
    "MembershipRuntime",
    "ResolvedContext",
    "RuntimeContextResolver",
    "SpaceRepository",
    "TenantRepository",
    "resolve_agent_execution_context",
    "safe_reason_code",
]
