"""P17 boundary guards (implementation contract §2 · hard invariants 12–23).

The identity/tenant/space runtime may read the identity surface and may write
**only** the two membership carriers plus the append-only audit carrier. It may
not create a second authorization engine, may not touch the role / permission /
ACL / platform-membership registries, and may not open a transport or DDL path.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "services" / "identity_runtime"

#: The only tables a P17 runtime statement may write (P17-D02 / D11 / D13).
WRITABLE = frozenset({"tenant_memberships", "memberships", "audit_logs"})

#: Frozen read-only registries and out-of-scope structure (OQ-01/02/05/06/07).
FORBIDDEN_WRITE_TARGETS = (
    "tenants",
    "spaces",
    "roles",
    "permissions",
    "role_permissions",
    "resource_permissions",
    "acl_subject_types",
    "platform_memberships",
    "platform_state",
    "resources",
    "agents",
    "users",
    "identities",
    "credentials",
)

_WRITE = re.compile(
    r"(?i)\bINSERT\s+INTO\s+(?:public\.)?\"?([a-z_]+)\"?"
    r"|\bUPDATE\s+(?:public\.)?\"?([a-z_]+)\"?\s+SET\b"
    r"|\bDELETE\s+FROM\s+(?:public\.)?\"?([a-z_]+)\"?"
)


def _sources() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)


def test_identity_runtime_package_exists_and_is_not_empty() -> None:
    assert _sources(), "services/identity_runtime must exist"


def test_only_membership_and_audit_tables_are_written() -> None:
    offenders: list[str] = []
    for path in _sources():
        for match in _WRITE.finditer(path.read_text(encoding="utf-8")):
            table = next(group for group in match.groups() if group).lower()
            if table not in WRITABLE:
                offenders.append(f"{path.name}:{table}")
    assert not offenders, f"out-of-scope write target(s): {sorted(set(offenders))}"


def test_frozen_registries_are_never_written_by_name() -> None:
    offenders: list[str] = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        for table in FORBIDDEN_WRITE_TARGETS:
            if re.search(
                rf"(?i)\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(?:public\.)?\"?{table}\"?",
                src,
            ):
                offenders.append(f"{path.name}:{table}")
    assert not offenders, offenders


def test_identity_runtime_never_grants_privileges_or_runs_ddl() -> None:
    offenders: list[str] = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        if re.search(r"(?i)\b(GRANT|REVOKE)\b", src):
            offenders.append(f"{path.name}: grant/revoke")
        if re.search(r"(?i)\b(CREATE\s+(TABLE|ROLE|INDEX)|ALTER\s+ROLE)\b", src):
            offenders.append(f"{path.name}: ddl")
    assert not offenders, offenders


def test_context_resolution_never_produces_an_authorization_verdict() -> None:
    """Context is not a decision: no ALLOW token and no ``Decision`` object."""
    offenders: list[str] = []
    for path in _sources():
        src = path.read_text(encoding="utf-8")
        if re.search(r"[\"']ALLOW[\"']", src):
            offenders.append(f"{path.name}: ALLOW literal")
        if re.search(r"\bDecision\s*\(", src):
            offenders.append(f"{path.name}: constructs a Decision")
    assert not offenders, offenders


def test_identity_runtime_reuses_the_canonical_authorization_package_only() -> None:
    """If authorization is referenced, it must be the canonical service package."""
    offenders: list[str] = []
    for path in _sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                modules.add(node.module)
            elif isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
        for module in modules:
            if "authoriz" in module and not module.startswith("services.authorization"):
                offenders.append(f"{path.name}:{module}")
    assert not offenders, offenders


def test_identity_runtime_is_not_a_transport_layer() -> None:
    offenders: list[str] = []
    for path in _sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name.split(".")[0] in {"fastapi", "starlette"} for alias in node.names
            ):
                offenders.append(path.name)
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in {
                "fastapi",
                "starlette",
                "apps",
            }:
                offenders.append(path.name)
    assert not offenders, offenders


def test_repository_exposes_no_generic_unscoped_accessor() -> None:
    src = (PACKAGE / "repository.py").read_text(encoding="utf-8")
    for forbidden in ("def get_by_id", "def list_all", "def get_any"):
        assert forbidden not in src, f"generic accessor {forbidden!r} is forbidden (P17 §37)"


def test_space_reads_never_use_visibility_as_an_authorization_input() -> None:
    """``spaces.visibility`` may be projected, never used as an access predicate."""
    src = (PACKAGE / "repository.py").read_text(encoding="utf-8")
    assert "visibility =" not in src
    assert "JOIN memberships" in src, "space reads must be membership-joined"


# ------------------------------------------------------- control-plane boundary
PROVISIONING_CALLS = (
    "provision_tenant(",
    "provision_space(",
    "ensure_resource_projection(",
    "backfill_resource_projections(",
)

#: Paths that must never provision a resource (P17-AUTH-Q1: runtime consumes only).
#: ``services/use_cases/control_plane.py`` is deliberately **excluded**: it is the
#: P18 control-plane entry point, the only place allowed to call provisioning.
RUNTIME_PATHS = (
    "apps",
    "services/agent",
    "services/identity_runtime",
    "services/use_cases/identity_runtime.py",
)


def test_runtime_paths_never_provision_resources() -> None:
    offenders: list[str] = []
    for package in RUNTIME_PATHS:
        base = ROOT / package
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for path in candidates:
            if "__pycache__" in path.parts:
                continue
            # The P18 control-plane surface is the one legitimate caller:
            # ``/control/...`` (dedicated namespace) and its use-case module.
            if path.name == "control_plane.py" and (
                path.parent.name == "routes" or path.parent.name == "use_cases"
            ):
                continue
            src = path.read_text(encoding="utf-8")
            for call in PROVISIONING_CALLS:
                if call in src:
                    offenders.append(f"{path.relative_to(ROOT)}:{call}")
    assert not offenders, offenders


def test_control_plane_is_not_a_transport_or_runtime_surface() -> None:
    offenders: list[str] = []
    for path in sorted((ROOT / "services" / "control_plane").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders += [
                    f"{path.name}:{alias.name}"
                    for alias in node.names
                    if alias.name.split(".")[0] in {"fastapi", "starlette", "apps"}
                ]
            elif isinstance(node, ast.ImportFrom) and not node.level:
                module = node.module or ""
                if module.split(".")[0] in {"fastapi", "starlette", "apps"}:
                    offenders.append(f"{path.name}:{module}")
                # Only the shared, behaviour-free vocabulary may be imported
                # from the runtime package (never its repository/resolver).
                elif module.startswith("services.identity_runtime") and module != (
                    "services.identity_runtime.resource_types"
                ):
                    offenders.append(f"{path.name}:{module}")
    assert not offenders, offenders
