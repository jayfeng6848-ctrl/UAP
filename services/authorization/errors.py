"""Authorization service errors.

Every failure mode here maps to a denial. No code path may turn one of these
into an allow: authorization failure must never widen access.
"""

from __future__ import annotations


class AuthorizationError(Exception):
    """Base class for authorization service failures."""


class AuthorizationUnavailable(AuthorizationError):
    """The service could not complete an evaluation (infrastructure failure)."""


class SubjectResolutionError(AuthorizationError):
    """The subject is unknown or not eligible to act."""


class ResourceResolutionError(AuthorizationError):
    """The resource is unknown or outside the caller's boundary."""


class ActionResolutionError(AuthorizationError):
    """The action is not part of the canonical vocabulary."""


__all__ = [
    "ActionResolutionError",
    "AuthorizationError",
    "AuthorizationUnavailable",
    "ResourceResolutionError",
    "SubjectResolutionError",
]
