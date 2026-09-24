"""Canonical authorization vocabulary.

The vocabulary is frozen: 12 actions, 3 subject types, 3 stored scopes, 3
decision states and 4 risk tiers. These tests pin the shapes and the
normalisation rules so a look-alike character or a spelling variant can never
masquerade as a different action.
"""

from __future__ import annotations

import unicodedata

import pytest

from core.permission.interfaces import Action
from core.permission.vocabulary import (
    ACTIONS,
    CONTEXT_PREDICATES,
    EFFECTS,
    GRANT_EFFECTS,
    RISK_LEVELS,
    STORED_SCOPES,
    SUBJECT_TYPES,
    is_canonical_action,
    is_context_predicate,
    is_risk_level,
    is_stored_scope,
    is_subject_type,
    normalize_action,
    risk_rank,
)


def test_action_vocabulary_is_exactly_twelve_canonical_actions() -> None:
    assert len(ACTIONS) == 12
    assert set(ACTIONS) == {
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
    }
    # ``D-AUTH-25``: the canonical storage/wire form is lowercase.
    assert all(action == action.lower() for action in ACTIONS)


def test_subject_types_are_the_three_authorization_subjects() -> None:
    assert SUBJECT_TYPES == ("USER", "ROLE", "AGENT")


def test_stored_scopes_exclude_the_context_predicates() -> None:
    assert STORED_SCOPES == ("PLATFORM", "TENANT", "SPACE")
    assert CONTEXT_PREDICATES == ("RESOURCE", "SELF")
    for predicate in CONTEXT_PREDICATES:
        assert not is_stored_scope(predicate)


def test_decision_states_are_three_valued() -> None:
    assert EFFECTS == ("ALLOW", "DENY", "REQUIRES_APPROVAL")


def test_risk_has_four_tiers_in_ascending_order() -> None:
    assert RISK_LEVELS == ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert [risk_rank(level) for level in RISK_LEVELS] == [0, 1, 2, 3]


def test_unknown_risk_never_ranks_as_low() -> None:
    assert risk_rank("BOGUS") > risk_rank("CRITICAL")
    assert risk_rank(None) > risk_rank("CRITICAL")


def test_grant_effects_match_the_database_constraint() -> None:
    assert GRANT_EFFECTS == ("allow", "deny")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" read ", "read"),
        ("Read", "read"),
        ("dElEtE", "delete"),
        ("\tEXECUTE\n", "execute"),
        ("ADMIN", "admin"),
    ],
)
def test_action_normalisation_is_case_and_whitespace_insensitive(raw, expected) -> None:
    assert normalize_action(raw) == expected


def test_action_normalisation_folds_to_the_lowercase_canonical_form() -> None:
    """``D-AUTH-25`` — the canonical form is lowercase, not uppercase."""
    for action in ACTIONS:
        assert normalize_action(action.upper()) == action
        assert normalize_action(action) == action
    assert normalize_action("READ") != "READ"


def test_action_normalisation_applies_nfkc() -> None:
    confusable = "\u212a"  # KELVIN SIGN normalises to ASCII "K", then folds to "k"
    assert unicodedata.normalize("NFKC", confusable) == "K"
    assert normalize_action(confusable) == "k"


def test_normalisation_cannot_turn_a_non_action_into_an_action() -> None:
    assert is_canonical_action("read")
    assert not is_canonical_action("readd")
    assert not is_canonical_action("")
    assert not is_canonical_action("READ;DROP")


def test_action_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        normalize_action(None)  # type: ignore[arg-type]
    assert is_canonical_action(None) is False


def test_action_value_object_normalises_on_construction() -> None:
    assert Action("  update ").name == "update"
    assert Action("READ").is_canonical
    assert not Action("NOT_AN_ACTION").is_canonical


def test_predicate_helpers_reject_the_wrong_vocabulary() -> None:
    assert is_subject_type("AGENT")
    assert not is_subject_type("agent")
    assert is_stored_scope("TENANT")
    assert not is_stored_scope("RESOURCE")
    assert is_context_predicate("SELF")
    assert not is_context_predicate("SPACE")
    assert is_risk_level("HIGH")
    assert not is_risk_level("high")
