"""Mapping-layer errors.

A vocabulary value that cannot be mapped is a **hard error**, never a silent
pass-through: an unmapped status must not reach the database or the domain.
"""

from __future__ import annotations


class VocabularyMappingError(ValueError):
    """Base class for mapping failures (a value could not be mapped)."""


class UnknownVocabularyValue(VocabularyMappingError):
    """The value is not part of the frozen vocabulary it claims to belong to."""


__all__ = ["VocabularyMappingError", "UnknownVocabularyValue"]
