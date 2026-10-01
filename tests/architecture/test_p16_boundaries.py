"""P16 architecture guards (D03 / section 31): layers stay where they belong."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]
SKIP = {"__pycache__", ".git"}

CORE_FORBIDDEN_IMPORTS = (
    "sqlalchemy",
    "psycopg",
    "fastapi",
    "urllib",
    "requests",
    "httpx",
    "openai",
    "anthropic",
)


def _files(*packages: str) -> list[Path]:
    out: list[Path] = []
    for package in packages:
        base = ROOT / package
        if base.exists():
            out.extend(p for p in base.rglob("*.py") if not any(part in SKIP for part in p.parts))
    return sorted(out)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    return names


def test_core_has_no_transport_or_db_dependency() -> None:
    offenders: list[str] = []
    for path in _files("core"):
        bad = _imports(path) & set(CORE_FORBIDDEN_IMPORTS)
        if bad:
            offenders.append(f"{path.relative_to(ROOT)}: {sorted(bad)}")
    assert not offenders, offenders


def test_core_does_not_import_services_or_infrastructure() -> None:
    offenders: list[str] = []
    for path in _files("core"):
        bad = _imports(path) & {"services", "infrastructure", "apps", "domains"}
        if bad:
            offenders.append(f"{path.relative_to(ROOT)}: {sorted(bad)}")
    assert not offenders, offenders


def test_core_does_not_reference_vendor_sdks_by_name() -> None:
    pattern = re.compile(r"\b(openai|anthropic|deepseek|ollama)\b", re.I)
    offenders = [
        str(path.relative_to(ROOT))
        for path in _files("core")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, offenders


def test_agent_runtime_never_uses_dynamic_import_or_eval() -> None:
    pattern = re.compile(r"\b(importlib|__import__|eval|exec)\s*\(")
    offenders = [
        str(path.relative_to(ROOT))
        for path in _files("services/agent", "services/ai", "infrastructure/ai")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, offenders


def test_provider_transport_lives_in_infrastructure() -> None:
    """Only infrastructure may import a transport client for providers."""
    offenders: list[str] = []
    for path in _files("services/ai", "services/agent"):
        if _imports(path) & {"urllib", "requests", "httpx", "http"}:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders
