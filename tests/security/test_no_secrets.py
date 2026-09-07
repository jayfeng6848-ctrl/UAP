"""Security guard: no committed secrets, no unignored env files."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.security

ROOT = Path(__file__).resolve().parents[2]

SCANNED_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".example", ".json", ".ts", ".tsx"}
# ``tests`` is excluded on purpose: redaction fixtures must contain realistic
# looking (but fake) credential strings to prove they are caught.
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    ".pytest_cache",
    "dist",
    "tests",
}

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\b(password|secret|token|api[_-]?key)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
)


def _iter_files():
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in SCANNED_SUFFIXES:
            # The scanner's own patterns live here; skip self.
            if path.name == "test_no_secrets.py":
                continue
            yield path


def test_env_example_contains_only_empty_values() -> None:
    env_example = ROOT / ".env.example"
    assert env_example.exists(), ".env.example must exist"

    bad_lines: list[str] = []
    for raw in env_example.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            bad_lines.append(line)
            continue
        key, _, value = line.partition("=")
        if value.strip():
            bad_lines.append(line)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key.strip()):
            bad_lines.append(line)
    assert not bad_lines, f".env.example must hold empty templates only: {bad_lines}"


def test_no_hardcoded_secrets_in_repository() -> None:
    offenders: list[str] = []
    for path in _iter_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                offenders.append(f"{path.relative_to(ROOT)}: {pattern.pattern}")
    assert not offenders, f"possible committed secret: {offenders}"


def test_env_file_is_gitignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert re.search(r"^\.env$", gitignore, flags=re.MULTILINE), ".env must be ignored"


def test_no_env_file_is_present() -> None:
    """A real .env must never exist in the working tree."""
    assert not (ROOT / ".env").exists(), ".env must not be committed"


def test_no_vendor_api_key_defaults() -> None:
    from config.settings import get_settings

    settings = get_settings()
    for value in (
        settings.AI_DEFAULT_PROVIDER,
        settings.AI_DEFAULT_MODEL,
    ):
        assert value and len(value) < 64
    assert "sk-" not in settings.model_dump_json()
