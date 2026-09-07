"""Architecture guard.

These tests are the executable form of docs/architecture/DEPENDENCY_RULES.md.
If someone adds a forbidden import, CI fails here rather than in production.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]

# Industry vocabulary that must never appear inside core.
FORBIDDEN_BUSINESS_TERMS = (
    "restaurant",
    "menu",
    "dish",
    "kitchen",
    "employee",
    "payroll",
    "shopping_list",
    "family",
    "company",
    "patient",
    "reservation",
    "invoice",
    "warehouse",
)

VENDOR_SDKS = ("openai", "anthropic", "deepseek", "ollama")

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}


def _python_files(package: str) -> list[Path]:
    base = ROOT / package
    return sorted(
        p
        for p in base.rglob("*.py")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def _module_package(path: Path) -> str:
    parts = list(path.relative_to(ROOT).parts[:-1])
    return ".".join(parts)


def _imported_top_levels(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    package_parts = _module_package(path).split(".")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                base = package_parts
                if node.level > 1:
                    base = base[: -(node.level - 1)]
                if base:
                    found.add(base[0])
            elif node.module:
                found.add(node.module.split(".")[0])
    return found


def test_core_never_imports_domains() -> None:
    offenders: list[str] = []
    for path in _python_files("core"):
        if "domains" in _imported_top_levels(path):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"core -> domains dependency found: {offenders}"


def test_core_imports_only_core() -> None:
    """Core may use stdlib/third-party but never another UAP layer."""
    forbidden = {"domains", "apps", "agent", "intelligence", "infrastructure"}
    offenders: list[str] = []
    for path in _python_files("core"):
        hits = _imported_top_levels(path) & forbidden
        if hits:
            offenders.append(f"{path.relative_to(ROOT)}: {sorted(hits)}")
    assert not offenders, f"core leaked into other layers: {offenders}"


def test_core_contains_no_business_vocabulary() -> None:
    offenders: list[str] = []
    for path in _python_files("core"):
        text = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_BUSINESS_TERMS:
            if re.search(rf"\b{term}\b", text):
                offenders.append(f"{path.relative_to(ROOT)}: {term}")
    assert not offenders, f"business vocabulary leaked into core: {offenders}"


def test_intelligence_has_no_vendor_sdk_imports() -> None:
    offenders: list[str] = []
    for path in _python_files("intelligence"):
        hits = _imported_top_levels(path) & set(VENDOR_SDKS)
        if hits:
            offenders.append(f"{path.relative_to(ROOT)}: {sorted(hits)}")
    assert not offenders, f"vendor SDK imported directly: {offenders}"


def test_intelligence_does_not_import_domains() -> None:
    offenders = [
        str(p.relative_to(ROOT))
        for p in _python_files("intelligence")
        if "domains" in _imported_top_levels(p)
    ]
    assert not offenders, f"intelligence -> domains dependency: {offenders}"


def test_agent_never_reaches_the_database() -> None:
    """Agents must go through Policy -> Tool -> Service -> Database."""
    forbidden = {"sqlalchemy", "psycopg", "psycopg2", "infrastructure", "apps"}
    offenders: list[str] = []
    for path in _python_files("agent"):
        hits = _imported_top_levels(path) & forbidden
        if hits:
            offenders.append(f"{path.relative_to(ROOT)}: {sorted(hits)}")
    assert not offenders, f"agent bypasses the tool boundary: {offenders}"


def test_domains_define_no_schema_or_persistence() -> None:
    offenders: list[str] = []
    for path in _python_files("domains"):
        text = path.read_text(encoding="utf-8").lower()
        if "create table" in text or "sqlalchemy" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"domain must not define schema in STEP 0: {offenders}"


def test_domain_manifests_are_placeholders() -> None:
    from domains import list_domains

    manifests = list_domains()
    assert {m["domain_id"] for m in manifests} == {
        "family",
        "company",
        "business",
        "entertainment",
    }
    for manifest in manifests:
        assert manifest["status"] == "placeholder"
        assert manifest["tables"] == []
        assert manifest["core_dependencies"]


def test_domains_may_depend_on_core_but_not_reverse() -> None:
    """Explicit statement of the allowed direction."""
    core_files = _python_files("core")
    assert core_files, "core package must exist"
    for path in core_files:
        assert "domains" not in _imported_top_levels(path)
