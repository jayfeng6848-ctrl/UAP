"""GAP-11 guard: the opaque P09 restriction field stays opaque.

``agent_permissions.resource_scope`` is a historical P09 column that carries no
authorization meaning. It must never be read, parsed, normalised, mapped,
promoted or reinterpreted by runtime code, and it must never become a source of
authority. These two checks are the executable form of that decision.

The scan is AST based and skips docstrings, because a declaration *about* the
rule is not a violation of it — only an actual reference is.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]

# The runtime surface. Build tooling (``scripts/``), migrations and tests are
# outside it by construction.
RUNTIME_PACKAGES = (
    "core",
    "agent",
    "apps",
    "intelligence",
    "infrastructure",
    "domains",
    "services",
    "config",
)

# The opaque field, spelled so this guard does not match itself.
OPAQUE_FIELD = "resource" + "_scope"

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}


def _runtime_files() -> list[Path]:
    files: list[Path] = []
    for package in RUNTIME_PACKAGES:
        base = ROOT / package
        if not base.exists():
            continue
        files.extend(
            path
            for path in sorted(base.rglob("*.py"))
            if not any(part in SKIP_DIRS for part in path.parts)
        )
    return files


def _docstring_ids(tree: ast.AST) -> set[int]:
    """Ids of constant nodes that serve as module/class/function docstrings."""
    ids: set[int] = set()
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, holders) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    ids.add(id(first.value))
    return ids


def _references(path: Path) -> list[str]:
    """Return the code-level references to the opaque field in ``path``."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    docstrings = _docstring_ids(tree)
    found: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docstrings:
                continue
            if OPAQUE_FIELD in node.value:
                found.append(f"string literal at line {node.lineno}")
        elif isinstance(node, ast.Name) and OPAQUE_FIELD in node.id:
            found.append(f"identifier {node.id} at line {node.lineno}")
        elif isinstance(node, ast.Attribute) and OPAQUE_FIELD in node.attr:
            found.append(f"attribute {node.attr} at line {node.lineno}")
        elif isinstance(node, ast.keyword) and node.arg and OPAQUE_FIELD in node.arg:
            found.append(f"keyword {node.arg} at line {node.lineno}")
    return found


def test_agent_resource_scope_01_runtime_references_are_zero() -> None:
    """AGENT-RESOURCE-SCOPE-01 — no runtime code consumes the opaque field."""
    offenders: list[str] = []
    for path in _runtime_files():
        hits = _references(path)
        if hits:
            offenders.append(f"{path.relative_to(ROOT)}: {hits}")
    assert not offenders, (
        "the opaque P09 restriction field must not be consumed at runtime: "
        f"{offenders}"
    )


def test_agent_resource_scope_02_it_is_not_an_authorization_authority() -> None:
    """AGENT-RESOURCE-SCOPE-02 — grants never come from the opaque field.

    The agent-grant query must select only structured targets (a permission
    reference or a tool reference) plus the effect. If the opaque restriction
    column ever entered that projection, an agent could derive scope from it.
    """
    repository = (ROOT / "services" / "authorization" / "repository.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(repository)
    docstrings = _docstring_ids(tree)

    # Only *executable* string literals count: the module docstring explains the
    # boundary by naming the field, which is a declaration, not a reference.
    queries = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]
    agent_query = next((text for text in queries if "agent_permissions" in text), None)
    assert agent_query is not None, "the agent grant query must exist"

    assert OPAQUE_FIELD not in agent_query, "the agent grant query must not select it"
    assert "ap.permission_id" in agent_query
    assert "ap.effect" in agent_query


def test_agent_resource_scope_source_declares_the_boundary() -> None:
    """The repository documents why the field is absent, not merely omits it."""
    repository = (ROOT / "services" / "authorization" / "repository.py").read_text(
        encoding="utf-8"
    )
    assert "authorization authority" in repository
