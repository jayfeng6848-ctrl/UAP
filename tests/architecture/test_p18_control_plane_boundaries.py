"""P18 architecture guards for the freeze-authorized authorization capability.

P18-D06 allowed exactly one thing inside the canonical authorization package: a
minimal **additive** pre-resource entry point (``resource is None``) for
structural operations that have no resource row yet. Everything else stays
forbidden, and these guards keep it that way:

* no ``platform_admin`` name check and no role-name comparison in the engine;
* no role/privilege administration from authorization code;
* no second authorization engine and no runtime path into control-plane code.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = ROOT / "services" / "authorization"

#: Strings that must never appear in the canonical authorization implementation.
FORBIDDEN_TOKENS = (
    "platform_admin",
    "tenant_admin",
    "space_admin",
    "SET ROLE",
    "CREATE ROLE",
    "create_role",
)


def _sources() -> list[Path]:
    return sorted(p for p in AUTHORIZATION.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_role_name_or_admin_literals_in_the_engine() -> None:
    offenders: list[str] = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        offenders += [f"{path.name}:{token}" for token in FORBIDDEN_TOKENS if token in src]
    assert not offenders, offenders


def test_no_role_admin_sql_in_the_engine() -> None:
    offenders: list[str] = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        # Case-sensitive: SQL keywords are written in upper case in this repo,
        # while the prose uses lower-case words such as "grant".
        if re.search(r"\b(GRANT|REVOKE|ALTER ROLE|CREATE ROLE|DROP ROLE)\b", src):
            offenders.append(path.name)
    assert not offenders, offenders


def test_engine_does_not_import_control_plane_or_transport() -> None:
    offenders: list[str] = []
    for path in _sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                module = node.module
                if module.split(".")[0] in {"apps", "fastapi", "starlette"} or module.startswith(
                    "services.control_plane"
                ):
                    offenders.append(f"{path.name}:{module}")
            elif isinstance(node, ast.Import):
                offenders += [
                    f"{path.name}:{alias.name}"
                    for alias in node.names
                    if alias.name.split(".")[0] in {"apps", "fastapi", "starlette"}
                ]
    assert not offenders, offenders


def test_pre_resource_entry_requires_an_explicit_declared_resource_type() -> None:
    """The additive path must never fall back to a blanket platform allow."""
    src = (AUTHORIZATION / "service.py").read_text(encoding="utf-8")
    assert "pre-resource-requires-declared-resource-type" in src
    assert "def _authorize_pre_resource" in src
    assert "request.resource is None" in src


def test_role_provisioning_is_not_reachable_from_the_application_path() -> None:
    """Role provisioning is environment infrastructure: no app/runtime import."""
    offenders: list[str] = []
    for package in ("apps", "services", "infrastructure", "core"):
        base = ROOT / package
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            src = path.read_text(encoding="utf-8")
            if "role_provisioning" in src:
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders


def test_role_provisioning_never_drops_or_switches_roles() -> None:
    """Scan executable text only: the module docstring states these prohibitions."""
    raw = (ROOT / "scripts" / "role_provisioning.py").read_text(encoding="utf-8")
    tree = ast.parse(raw)
    src = raw
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                src = src.replace(doc, "")
    for forbidden in ("DROP ROLE", "REVOKE", "SET ROLE", "uap_migrator", "uap_bootstrap"):
        assert forbidden not in src, f"role provisioning must not reference {forbidden!r}"
