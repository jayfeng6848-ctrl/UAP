"""Readiness migration-state probe (``D-PLAT-14`` / ``D-PLAT-16``).

Every branch is exercised with a stub engine: no database is required and none
is touched.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError

from infrastructure.database import health as health_module
from infrastructure.database.config import DatabaseConfig
from infrastructure.database.health import (
    MIGRATION_COMPONENT,
    READINESS_STATEMENT_TIMEOUT_MS,
    check_migration_state,
)

EXPECTED = "0011_p09_agent_tool_permission"
OLDER = "0010_b1_6_ai_gateway"
NEWER = "0012_future_revision"
DSN = "postgresql+psycopg://uap:uap@localhost:5432/uap_test"


class _StubResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = list(rows)

    def scalars(self) -> "_StubResult":
        return self

    def all(self) -> list[object]:
        return list(self._rows)


class _StubConnection:
    def __init__(self, rows: list[object], exc: Exception | None) -> None:
        self._rows = rows
        self._exc = exc

    def __enter__(self) -> "_StubConnection":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def execute(self, statement: object) -> _StubResult:
        if self._exc is not None:
            raise self._exc
        return _StubResult(self._rows)


class _StubEngine:
    def __init__(self, rows: list[object] | None = None, exc: Exception | None = None) -> None:
        self._rows = rows or []
        self._exc = exc
        self.connect_calls = 0
        self.dispose_calls = 0

    def connect(self) -> _StubConnection:
        self.connect_calls += 1
        return _StubConnection(self._rows, self._exc)

    def dispose(self) -> None:
        self.dispose_calls += 1


def _timeout_error() -> OperationalError:
    return OperationalError(
        "SELECT version_num FROM alembic_version",
        {},
        RuntimeError("canceling statement due to statement timeout"),
    )


# ----------------------------------------------------------- unusable expectation


@pytest.mark.parametrize("expected", [None, "", "   ", "0011", "0011_P09", "baseline"])
def test_missing_or_invalid_expectation_fails_closed_without_touching_the_database(
    expected: str | None,
) -> None:
    engine = _StubEngine(rows=[EXPECTED])
    component = check_migration_state(expected, engine=engine)
    assert component.name == MIGRATION_COMPONENT
    assert component.status == "error"
    assert component.critical is True
    assert engine.connect_calls == 0, "must fail closed before contacting the database"


# --------------------------------------------------------------- row evaluation


def test_exact_match_is_ok() -> None:
    component = check_migration_state(EXPECTED, engine=_StubEngine(rows=[EXPECTED]))
    assert component.status == "ok"
    assert component.critical is True
    assert component.error is None
    assert component.detail == {"expected": EXPECTED, "actual": EXPECTED, "source": "missing"}


def test_reported_source_is_preserved() -> None:
    component = check_migration_state(
        EXPECTED,
        source="build_artifact",
        engine=_StubEngine(rows=[EXPECTED]),
    )
    assert component.detail is not None
    assert component.detail["source"] == "build_artifact"


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        ([], "zero rows"),
        ([EXPECTED, OLDER], "multiple rows"),
        ([None], "NULL"),
        ([""], "empty string"),
        (["   "], "blank string"),
    ],
)
def test_unusable_rows_fail_closed(rows: list[object], reason: str) -> None:
    component = check_migration_state(EXPECTED, engine=_StubEngine(rows=rows))
    assert component.status == "error", reason
    assert component.critical is True


def test_behind_fails_closed() -> None:
    component = check_migration_state(EXPECTED, engine=_StubEngine(rows=[OLDER]))
    assert component.status == "error"
    assert component.detail is not None
    assert component.detail["actual"] == OLDER


def test_ahead_fails_closed() -> None:
    """An ahead revision is explicitly *not* accepted (OD-3 strict equality)."""
    component = check_migration_state(EXPECTED, engine=_StubEngine(rows=[NEWER]))
    assert component.status == "error"
    assert component.detail is not None
    assert component.detail["actual"] == NEWER


def test_query_failure_fails_closed() -> None:
    component = check_migration_state(EXPECTED, engine=_StubEngine(exc=_timeout_error()))
    assert component.status == "error"
    assert component.critical is True
    assert component.error is not None
    assert "statement timeout" in component.error
    assert len(component.error) <= 200


def test_arbitrary_exception_fails_closed_without_raising() -> None:
    component = check_migration_state(EXPECTED, engine=_StubEngine(exc=RuntimeError("boom")))
    assert component.status == "error"


# ------------------------------------------------------- timeout / engine lifecycle


def test_probe_uses_a_dedicated_short_statement_timeout(monkeypatch) -> None:
    captured: dict[str, DatabaseConfig] = {}
    stub = _StubEngine(rows=[EXPECTED])

    def _build(config: DatabaseConfig) -> _StubEngine:
        captured["config"] = config
        return stub

    monkeypatch.setattr(health_module, "build_engine", _build)
    config = DatabaseConfig(url=DSN)
    component = check_migration_state(EXPECTED, config=config)

    assert component.status == "ok"
    assert captured["config"].statement_timeout_ms == READINESS_STATEMENT_TIMEOUT_MS
    assert READINESS_STATEMENT_TIMEOUT_MS == 2000
    assert config.statement_timeout_ms is None, "the caller's config must be untouched"
    assert captured["config"].connect_timeout_seconds == 5


def test_global_statement_timeout_default_is_unchanged() -> None:
    assert DatabaseConfig(url=DSN).statement_timeout_ms is None


def test_probe_engine_is_disposed_on_success(monkeypatch) -> None:
    stub = _StubEngine(rows=[EXPECTED])
    monkeypatch.setattr(health_module, "build_engine", lambda config: stub)
    check_migration_state(EXPECTED, config=DatabaseConfig(url=DSN))
    assert stub.dispose_calls == 1


def test_probe_engine_is_disposed_on_failure(monkeypatch) -> None:
    stub = _StubEngine(exc=_timeout_error())
    monkeypatch.setattr(health_module, "build_engine", lambda config: stub)
    component = check_migration_state(EXPECTED, config=DatabaseConfig(url=DSN))
    assert component.status == "error"
    assert stub.dispose_calls == 1


def test_supplied_engine_is_not_disposed() -> None:
    """A test-owned engine stays under the caller's control."""
    engine = _StubEngine(rows=[EXPECTED])
    check_migration_state(EXPECTED, engine=engine)
    assert engine.dispose_calls == 0


def test_probe_never_imports_alembic() -> None:
    """``D-PLAT-15 v2``: runtime compares strings; it does not import Alembic."""
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(health_module.__file__).read_text(encoding="utf-8"))
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
