"""Build-time revision resolution (``D-PLAT-14`` / ``D-PLAT-15 v2``).

The artifact is authoritative; the environment is a local development/test
fallback that can never override it.
"""

from __future__ import annotations

import ast
import pathlib
import sys
import types

import pytest

from config import build_info

REV = "0011_p09_agent_tool_permission"
OTHER_REV = "0012_future_revision"


def _install_artifact(monkeypatch, value: object) -> None:
    module = types.ModuleType(build_info.ARTIFACT_MODULE)
    setattr(module, build_info.ARTIFACT_ATTRIBUTE, value)
    monkeypatch.setitem(sys.modules, build_info.ARTIFACT_MODULE, module)


def _hide_artifact(monkeypatch) -> None:
    """Simulate "no artifact in this environment" (import raises)."""
    monkeypatch.setitem(sys.modules, build_info.ARTIFACT_MODULE, None)


@pytest.fixture(autouse=True)
def _no_ambient_artifact(monkeypatch) -> None:
    """Tests must not depend on a developer's locally generated artifact."""
    _hide_artifact(monkeypatch)


@pytest.mark.parametrize(
    "value",
    ["0011_p09_agent_tool_permission", "0001_baseline", "0011_timestamp_precision"],
)
def test_is_valid_revision_accepts_the_canonical_shape(value: str) -> None:
    assert build_info.is_valid_revision(value)


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "0011", "001_baseline", "0011-P09", "0011_P09", "0011_p09_AGENT", "baseline", "0011_"],
)
def test_is_valid_revision_rejects_everything_else(value: str | None) -> None:
    assert not build_info.is_valid_revision(value)


def test_missing_artifact_is_not_an_error(monkeypatch) -> None:
    _hide_artifact(monkeypatch)
    assert build_info.get_artifact_revision() is None


def test_artifact_without_the_attribute_is_treated_as_absent(monkeypatch) -> None:
    module = types.ModuleType(build_info.ARTIFACT_MODULE)
    monkeypatch.setitem(sys.modules, build_info.ARTIFACT_MODULE, module)
    assert build_info.get_artifact_revision() is None


def test_empty_artifact_value_is_treated_as_absent(monkeypatch) -> None:
    _install_artifact(monkeypatch, "   ")
    assert build_info.get_artifact_revision() is None


def test_artifact_is_authoritative_over_the_environment(monkeypatch) -> None:
    _install_artifact(monkeypatch, OTHER_REV)
    value, source = build_info.resolve_expected_revision(REV)
    assert (value, source) == (OTHER_REV, build_info.SOURCE_BUILD_ARTIFACT)


def test_environment_is_used_only_when_the_artifact_is_absent(monkeypatch) -> None:
    _hide_artifact(monkeypatch)
    value, source = build_info.resolve_expected_revision(f"  {REV}  ")
    assert (value, source) == (REV, build_info.SOURCE_ENVIRONMENT)


def test_nothing_configured_resolves_to_missing(monkeypatch) -> None:
    _hide_artifact(monkeypatch)
    assert build_info.resolve_expected_revision("") == ("", build_info.SOURCE_MISSING)
    assert build_info.resolve_expected_revision(None) == ("", build_info.SOURCE_MISSING)


def test_malformed_environment_value_is_reported_not_hidden(monkeypatch) -> None:
    """Validation belongs to the readiness probe, which must fail closed."""
    _hide_artifact(monkeypatch)
    value, source = build_info.resolve_expected_revision("0011")
    assert (value, source) == ("0011", build_info.SOURCE_ENVIRONMENT)
    assert not build_info.is_valid_revision(value)


def test_empty_artifact_falls_back_to_the_environment(monkeypatch) -> None:
    _install_artifact(monkeypatch, "")
    value, source = build_info.resolve_expected_revision(REV)
    assert (value, source) == (REV, build_info.SOURCE_ENVIRONMENT)


def test_build_info_never_imports_alembic_or_scans_the_migration_directory() -> None:
    """``D-PLAT-15 v2``: deriving the head is a build-time concern only."""
    source = pathlib.Path(build_info.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not {module for module in modules if module.split(".")[0] == "alembic"}

    # Executable code only: the module docstring legitimately *describes* the
    # authority chain, but no statement may reference the migration directory.
    code = source.replace(ast.get_docstring(tree) or "", "")
    assert "migrations_alembic" not in code
    assert "glob(" not in code
