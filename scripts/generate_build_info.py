#!/usr/bin/env python
"""Generate the build-time revision artifact (``D-PLAT-15 v2``).

The image build derives the expected schema revision from the **Alembic graph**
and freezes it into ``config/_build_info.py``. Runtime never derives it again.

Usage::

    python -m scripts.generate_build_info                  # derive from Alembic graph
    python -m scripts.generate_build_info --revision X      # optional *verification* input
    python -m scripts.generate_build_info --output P --ini I

This module must be invoked as ``python -m`` (the form the Dockerfile uses). Running
it as ``python scripts/generate_build_info.py`` puts ``scripts/`` - not the repository
root - on ``sys.path``, and the ``config.build_info`` import below then fails.

Guarantees:

* no database connection is opened;
* no migration is executed;
* the runtime application is never imported;
* ``alembic/env.py`` is never executed (``ScriptDirectory`` only parses files);
* the derived head is the single authority — ``--revision`` can only *verify*.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from config.build_info import REVISION_PATTERN

DEFAULT_INI = "alembic.ini"
DEFAULT_OUTPUT = Path("config/_build_info.py")

EXIT_OK = 0
EXIT_BUILD_FAILURE = 2


class BuildInfoError(RuntimeError):
    """Raised when the revision authority cannot be established unambiguously."""


def derive_head(ini_path: str | Path = DEFAULT_INI) -> str:
    """Return the unique Alembic head, validated against the canonical shape."""
    config = Config(str(ini_path))
    script = ScriptDirectory.from_config(config)
    heads = list(script.get_heads())

    if len(heads) != 1:
        raise BuildInfoError(
            f"expected exactly one Alembic head, found {len(heads)}: {sorted(heads)}"
        )

    head = str(heads[0]).strip()
    if not REVISION_PATTERN.fullmatch(head):
        raise BuildInfoError(
            f"derived head {head!r} does not match the canonical revision shape"
        )
    return head


def verify_override(derived: str, override: str | None) -> None:
    """Fail when an explicit ``--revision`` disagrees with the derived head."""
    if override is None:
        return
    candidate = override.strip()
    if not REVISION_PATTERN.fullmatch(candidate):
        raise BuildInfoError(
            f"--revision {override!r} does not match the canonical revision shape"
        )
    if candidate != derived:
        raise BuildInfoError(
            "--revision is a verification input only and must equal the derived "
            f"head: derived={derived!r} provided={candidate!r}"
        )


def render_artifact(revision: str) -> str:
    """Render the artifact deterministically (no timestamps, stable bytes)."""
    return (
        '"""Generated at image build time by scripts/generate_build_info.py.\n'
        "\n"
        "Do not edit by hand and do not commit: this file is a build artifact.\n"
        '"""\n'
        "\n"
        f'EXPECTED_ALEMBIC_REVISION = "{revision}"\n'
    )


def write_artifact(revision: str, output: str | Path = DEFAULT_OUTPUT) -> Path:
    """Write the artifact atomically enough for a build step and return its path."""
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_artifact(revision), encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Derive the Alembic head and freeze it into the build artifact."
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Optional verification input; must equal the derived head.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--ini", default=DEFAULT_INI)
    args = parser.parse_args(argv)

    try:
        derived = derive_head(args.ini)
        verify_override(derived, args.revision)
        target = write_artifact(derived, args.output)
    except BuildInfoError as exc:
        print(f"build-info generation failed: {exc}", file=sys.stderr)
        return EXIT_BUILD_FAILURE

    print(f"uap.build.revision={derived}")
    print(f"uap.build.artifact={target.as_posix()}")
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover - exercised via main()
    raise SystemExit(main())
