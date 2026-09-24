"""Build-time generator (``D-PLAT-15 v2``).

The generator derives the unique Alembic head **offline** (no database, no
``env.py``, no runtime application import) and freezes it into the artifact.
``--revision`` can only verify, never override.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import pathlib
import subprocess
import sys

import pytest

generator = importlib.import_module("scripts.generate_build_info")

ROOT = pathlib.Path(__file__).resolve().parents[2]
REV = "0012_authz_enforcement"


@pytest.fixture(autouse=True)
def _repo_root_cwd(monkeypatch) -> None:
    """``alembic.ini`` is resolved relative to the working directory."""
    monkeypatch.chdir(ROOT)


class _StubScript:
    def __init__(self, heads: list[str]) -> None:
        self._heads = list(heads)

    def get_heads(self) -> list[str]:
        return list(self._heads)


def _stub_heads(monkeypatch, heads: list[str]) -> None:
    monkeypatch.setattr(
        generator.ScriptDirectory,
        "from_config",
        classmethod(lambda cls, config: _StubScript(heads)),
    )


def test_derives_the_unique_head_from_the_repository_graph() -> None:
    assert generator.derive_head() == REV


def test_zero_heads_is_rejected(monkeypatch) -> None:
    _stub_heads(monkeypatch, [])
    with pytest.raises(generator.BuildInfoError):
        generator.derive_head()


def test_multiple_heads_are_rejected(monkeypatch) -> None:
    _stub_heads(monkeypatch, [REV, "0012_second_head"])
    with pytest.raises(generator.BuildInfoError):
        generator.derive_head()


def test_invalid_head_shape_is_rejected(monkeypatch) -> None:
    _stub_heads(monkeypatch, ["baseline"])
    with pytest.raises(generator.BuildInfoError):
        generator.derive_head()


def test_override_equal_to_the_derived_head_is_accepted(tmp_path) -> None:
    target = tmp_path / "_build_info.py"
    assert generator.main(["--revision", REV, "--output", str(target)]) == 0
    assert target.exists()


def test_override_that_differs_from_the_derived_head_fails(tmp_path) -> None:
    target = tmp_path / "_build_info.py"
    assert generator.main(["--revision", "0012_other_revision", "--output", str(target)]) == 2
    assert not target.exists()


def test_override_with_invalid_shape_fails(tmp_path) -> None:
    target = tmp_path / "_build_info.py"
    assert generator.main(["--revision", "not-a-revision", "--output", str(target)]) == 2
    assert not target.exists()


def test_rendering_is_deterministic(tmp_path) -> None:
    assert generator.render_artifact(REV) == generator.render_artifact(REV)


def test_written_artifact_is_a_python_module_carrying_the_revision(tmp_path) -> None:
    target = generator.write_artifact(REV, tmp_path / "versions_artifact.py")
    spec = importlib.util.spec_from_file_location("_generated_build_info", target)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert getattr(module, "EXPECTED_ALEMBIC_REVISION") == REV


def test_generator_never_imports_database_drivers_or_the_runtime_application() -> None:
    tree = ast.parse(pathlib.Path(generator.__file__).read_text(encoding="utf-8"))
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
    drivers = {"sqlalchemy", "psycopg", "psycopg2"}
    assert not {module for module in modules if module.split(".")[0] in drivers}
    runtime = {"apps", "agent", "infrastructure"}
    assert not {module for module in modules if module.split(".")[0] in runtime}


def test_documented_cli_invocation_succeeds_in_a_real_subprocess(tmp_path) -> None:
    """The CLI form the image executes must work as a real subprocess (U-1).

    In-process imports hide ``sys.path[0]`` semantics: ``python
    path/to/script.py`` puts the **script directory** on ``sys.path``, so the
    module-level ``config.build_info`` import only resolves when the module is
    invoked as ``python -m``. Every other test in this file imports the module
    inside pytest (where ``pythonpath = ["."]`` masks the difference), so the
    real invocation contract the ``Dockerfile`` depends on was never exercised.

    ``PYTHONPATH`` is removed from the child environment on purpose: the contract
    must hold on its own, not because an ambient path happened to be exported.
    Output is written to an isolated temporary directory, never to the repository.
    """
    target = tmp_path / "_build_info.py"
    child_env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}

    completed = subprocess.run(
        [sys.executable, "-m", "scripts.generate_build_info", "--output", str(target)],
        cwd=ROOT,
        env=child_env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert target.exists()

    spec = importlib.util.spec_from_file_location("_cli_build_info", target)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert getattr(module, "EXPECTED_ALEMBIC_REVISION") == generator.derive_head() == REV
