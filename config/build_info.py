"""Build-time revision artifact loader.

This module is the **stable runtime read entry point** for the expected Alembic
revision (``D-PLAT-15 v2``). It never derives the head itself: deriving the head
is a **build-time** concern handled by ``scripts/generate_build_info.py``.

Authority model::

    migrations_alembic/versions/  ->  Alembic graph  ->  unique HEAD
        ->  build-time generator  ->  config/_build_info.py (artifact)
        ->  image  ->  /ready  ->  DB alembic_version

Rules enforced here:

* the artifact (``config/_build_info.py``) is **authoritative**;
* an environment variable / settings value is only a local development and test
  fallback and can **never** override the artifact;
* this module must not import Alembic, scan the migration directory or infer a
  head from file names.
"""

from __future__ import annotations

import importlib
import re

#: Build artifact module generated at image build time (git-ignored).
ARTIFACT_MODULE = "config._build_info"

#: Attribute holding the derived revision inside the artifact module.
ARTIFACT_ATTRIBUTE = "EXPECTED_ALEMBIC_REVISION"

#: Canonical revision shape, shared by the generator and the readiness probe.
REVISION_PATTERN = re.compile(r"^\d{4}_[a-z0-9_]+$")

#: Resolution sources reported by :func:`resolve_expected_revision`.
SOURCE_BUILD_ARTIFACT = "build_artifact"
SOURCE_ENVIRONMENT = "environment"
SOURCE_MISSING = "missing"


def is_valid_revision(value: str | None) -> bool:
    """Return ``True`` when ``value`` has the canonical revision shape."""
    if value is None:
        return False
    return REVISION_PATTERN.fullmatch(value.strip()) is not None


def get_artifact_revision() -> str | None:
    """Return the revision recorded in the build artifact.

    Returns ``None`` when the artifact is absent or carries no usable value.
    Never raises: a missing artifact is a *fail-closed* readiness condition,
    not a crash.
    """
    try:
        module = importlib.import_module(ARTIFACT_MODULE)
    except ImportError:
        return None
    value = getattr(module, ARTIFACT_ATTRIBUTE, None)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def resolve_expected_revision(
    settings_value: str | None = None,
) -> tuple[str, str]:
    """Resolve the effective expected revision and where it came from.

    Precedence (``D-PLAT-15 v2``):

    1. ``build_artifact`` — authoritative inside a built image;
    2. ``environment`` — local development / test fallback only;
    3. ``missing`` — empty value, which makes readiness fail closed.

    The returned value is always stripped; it is **not** shape-validated here so
    that an invalid value is reported by the readiness probe (fail closed)
    instead of raising during configuration loading.
    """
    artifact = get_artifact_revision()
    if artifact:
        return artifact, SOURCE_BUILD_ARTIFACT
    fallback = (settings_value or "").strip()
    if fallback:
        return fallback, SOURCE_ENVIRONMENT
    return "", SOURCE_MISSING


__all__ = [
    "ARTIFACT_ATTRIBUTE",
    "ARTIFACT_MODULE",
    "REVISION_PATTERN",
    "SOURCE_BUILD_ARTIFACT",
    "SOURCE_ENVIRONMENT",
    "SOURCE_MISSING",
    "get_artifact_revision",
    "is_valid_revision",
    "resolve_expected_revision",
]
