"""I-03 guard: the agent runtime has exactly one authorization path.

The runtime must delegate tool authorization to the canonical ToolGate (via the
facade) and must not carry its own scope / grant / approval / deny-precedence
logic. Only the execution concerns (handler dispatch, idempotency execution
semantics, timeout, ledger) belong to the runtime.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "services" / "agent" / "runtime.py"
USE_CASES = ROOT / "services" / "agent" / "use_cases.py"

#: Authorization semantics the runtime must NOT re-implement.
FORBIDDEN_IN_RUNTIME = (
    "approval_required",
    "tool_grants",
    "resource_permissions",
    "permissions.tool",
    "effect",
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_runtime_delegates_to_the_tool_authorization_facade() -> None:
    src = _source(RUNTIME)
    assert "ToolAuthorizationFacade" in src, "runtime must depend on the canonical facade"
    assert "self._tool_auth.authorize(" in src, "runtime must call the facade before executing a tool"


def test_runtime_does_not_reimplement_authorization_semantics() -> None:
    src = _source(RUNTIME)
    offenders = [token for token in FORBIDDEN_IN_RUNTIME if token in src]
    assert not offenders, f"runtime re-implements authorization semantics: {offenders}"


def test_runtime_does_not_touch_authorization_tables_or_packages() -> None:
    src = _source(RUNTIME)
    assert "services.authorization" not in src, "runtime must not reach into the authorization package"
    assert "resource_scope" not in src
    assert not re.search(r"(?i)from\s+services\.authorization", src)


def test_use_cases_wire_the_canonical_gate() -> None:
    src = _source(USE_CASES)
    assert "ToolAuthorizationFacade.from_engine" in src, "production wiring must use the canonical gate"
    assert "P09ActorAuthorizer.from_engine" in src, "actor authorization must stay wired"
