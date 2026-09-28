"""Authenticated runtime context + the single Stage 2 bridge
(P14 Wave 2, W2-AUTH-04 / W2-AUTH-05)."""

from .authorization_adapter import DENY_UNKNOWN, AuthorizationAdapter
from .builder import ContextBuilder, MembershipReader, ResolvedScope
from .errors import ContextDenied, ContextError, ContextRequired, ContextUnavailable
from .model import LOG_SAFE_FIELDS, AuthenticatedRuntimeContext, AuthenticationAssurance

__all__ = [
    "DENY_UNKNOWN",
    "LOG_SAFE_FIELDS",
    "AuthenticatedRuntimeContext",
    "AuthenticationAssurance",
    "AuthorizationAdapter",
    "ContextBuilder",
    "ContextDenied",
    "ContextError",
    "ContextRequired",
    "ContextUnavailable",
    "MembershipReader",
    "ResolvedScope",
]
