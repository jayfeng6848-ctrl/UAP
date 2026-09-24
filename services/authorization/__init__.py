"""Authorization service.

The single authority for authorization decisions. It composes RBAC, ACL and
Policy over the frozen core contracts and is the only place allowed to read
authorization state from the database.

An agent reaches controlled capability **only** through this service together
with the policy and tool contracts; a tool never bypasses it.

Design frozen; nothing here caches a decision, and nothing here writes to the
database.
"""

from .actions import ActionResolver
from .audit import AuditBoundary
from .errors import (
    ActionResolutionError,
    AuthorizationError,
    AuthorizationUnavailable,
    ResourceResolutionError,
    SubjectResolutionError,
)
from .permissions import PermissionResolver
from .policy import (
    POLICY_VERSION,
    PolicyEngine,
    PolicyEvaluation,
    PolicyRule,
    RiskEvaluator,
    approval_required,
)
from .repository import AuthorizationRepository
from .resources import ResourceResolver
from .scopes import ScopeEvaluator
from .service import AuthorizationService
from .subjects import ResolvedSubject, SubjectResolver
from .tools import ToolGate

__all__ = [
    "POLICY_VERSION",
    "ActionResolutionError",
    "ActionResolver",
    "AuditBoundary",
    "AuthorizationError",
    "AuthorizationRepository",
    "AuthorizationService",
    "AuthorizationUnavailable",
    "PermissionResolver",
    "PolicyEngine",
    "PolicyEvaluation",
    "PolicyRule",
    "ResolvedSubject",
    "ResourceResolutionError",
    "ResourceResolver",
    "RiskEvaluator",
    "ScopeEvaluator",
    "SubjectResolutionError",
    "SubjectResolver",
    "ToolGate",
    "approval_required",
]
