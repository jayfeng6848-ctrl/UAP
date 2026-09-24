"""Canonical authorization vocabulary.

Pure constants and pure functions only: no I/O, no persistence and no runtime
imports. Frozen by ``D-AUTH-05`` (actions), ``D-AUTH-06`` (scopes),
``D-AUTH-10`` (risk), ``D-AUTH-14`` (decision states) and ``D-AUTH-18``
(subject types).

Action *storage/wire form* is lowercase, per ``D-AUTH-25`` (which also
supersedes ``D-B14-08`` through ``D-AUTH-24``). Only the action vocabulary is
lowercase: subject types, stored scopes, risk levels and decision states keep
their own frozen casing.

Deliberate separations (``GAP-9``): a *subject type* is not an *identity kind*
(``core.identity.IDENTITY_KINDS``) and not an *identity provider*
(``identities.provider``). The three vocabularies must never be conflated.
"""

from __future__ import annotations

import unicodedata

# ``D-AUTH-18`` — the three and only three authorization subject types.
SUBJECT_TYPES = ("USER", "ROLE", "AGENT")

# ``D-AUTH-05`` — the platform canonical action vocabulary (12 entries).
# Modules may register extra actions later, but only through an auditable
# registry (never an arbitrary string).
# ``D-AUTH-25`` — the canonical *form* of every entry is lowercase.
ACTIONS = (
    "read",
    "list",
    "create",
    "update",
    "delete",
    "execute",
    "approve",
    "reject",
    "publish",
    "export",
    "share",
    "admin",
)

# ``D-AUTH-06`` — scopes that may be *stored* on a grant.
STORED_SCOPES = ("PLATFORM", "TENANT", "SPACE")

# ``D-AUTH-06`` — context predicates. These are *not* stored grant scopes and
# must never be persisted as one.
CONTEXT_PREDICATES = ("RESOURCE", "SELF")

# ``D-AUTH-14`` — canonical decision states. ``REQUIRES_APPROVAL`` is not an
# authorization to execute: it means "allowed only after approval".
EFFECTS = ("ALLOW", "DENY", "REQUIRES_APPROVAL")

# ``D-AUTH-10`` — canonical risk classification. A numeric score may exist as an
# internal signal, but it is never an external authorization vocabulary.
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

# Storage-level grant effects, exactly as constrained by the database.
# Unchanged by this round (``D-AUTH-20``).
GRANT_EFFECTS = ("allow", "deny")


def normalize_action(value: str) -> str:
    """Return the canonical form of an action token.

    NFKC-normalised (defeats confusable look-alikes), stripped and
    case-folded to the lowercase canonical form frozen by ``D-AUTH-25``.
    """
    if not isinstance(value, str):
        raise TypeError("action must be a string")
    return unicodedata.normalize("NFKC", value).strip().casefold()


def is_canonical_action(value: str) -> bool:
    """True when ``value`` normalises to a canonical action."""
    try:
        return normalize_action(value) in ACTIONS
    except TypeError:
        return False


def is_subject_type(value: str) -> bool:
    return isinstance(value, str) and value in SUBJECT_TYPES


def is_stored_scope(value: str) -> bool:
    return isinstance(value, str) and value in STORED_SCOPES


def is_context_predicate(value: str) -> bool:
    return isinstance(value, str) and value in CONTEXT_PREDICATES


def is_risk_level(value: str) -> bool:
    return isinstance(value, str) and value in RISK_LEVELS


def risk_rank(value: str) -> int:
    """Ordinal for a canonical risk level; unknown values rank highest.

    Unknown input must never be treated as low risk (fail closed).
    """
    return RISK_LEVELS.index(value) if is_risk_level(value) else len(RISK_LEVELS)


__all__ = [
    "ACTIONS",
    "CONTEXT_PREDICATES",
    "EFFECTS",
    "GRANT_EFFECTS",
    "RISK_LEVELS",
    "STORED_SCOPES",
    "SUBJECT_TYPES",
    "is_canonical_action",
    "is_context_predicate",
    "is_risk_level",
    "is_stored_scope",
    "is_subject_type",
    "normalize_action",
    "risk_rank",
]
