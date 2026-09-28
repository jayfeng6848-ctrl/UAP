"""Authenticated-context errors (Wave 2 §二十二 – §二十五)."""

from __future__ import annotations


class ContextError(Exception):
    """Base class for context-layer failures."""

    code = "context_error"


class ContextRequired(ContextError):
    """The request does not carry enough context to choose a tenant/space.

    The caller must be told to supply an explicit context — never be given a
    randomly chosen one (§二十三 / §二十四 / §二十五).
    """

    code = "context_required"


class ContextDenied(ContextError):
    """The requested tenant/space has no active membership for this user."""

    code = "context_denied"


class ContextUnavailable(ContextError):
    """Context assembly failed (fail closed)."""

    code = "context_unavailable"


__all__ = ["ContextDenied", "ContextError", "ContextRequired", "ContextUnavailable"]
