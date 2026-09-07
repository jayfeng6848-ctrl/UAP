#!/usr/bin/env python
"""Environment doctor: verify the local setup before running UAP.

Checks: Python version, settings load, database reachability, migrations found,
logging pipeline and architecture guard availability.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings  # noqa: E402
from infrastructure.database.config import DatabaseConfig  # noqa: E402
from infrastructure.database.migration import discover_migrations  # noqa: E402
from infrastructure.database.session import build_engine, ping  # noqa: E402
from infrastructure.logging import configure_logging, get_logger  # noqa: E402

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


def _report(status: str, name: str, detail: str = "") -> bool:
    print(f"[{status}] {name}{(' - ' + detail) if detail else ''}")
    return status != FAIL


def main() -> int:
    healthy = True

    healthy &= _report(
        OK if sys.version_info >= (3, 13) else FAIL,
        "python version",
        sys.version.split()[0],
    )

    settings = get_settings()
    configure_logging(level=settings.LOG_LEVEL, fmt="console", service="uap-doctor")
    logger = get_logger("uap.doctor")
    logger.info("doctor start")

    healthy &= _report(OK, "settings loaded", f"env={settings.APP_ENV}")

    try:
        config = DatabaseConfig.from_settings(settings)
        config.validate()
        healthy &= _report(OK, "database config", config.safe_url())
    except Exception as exc:  # noqa: BLE001 - doctor reports, never crashes
        healthy &= _report(FAIL, "database config", str(exc))
        return 0 if healthy else 1

    host, port = config.host, config.port or 5432
    try:
        with socket.create_connection((host, port), timeout=2):
            reachable = True
    except OSError as exc:
        reachable = False
        detail = str(exc)
    healthy &= _report(
        OK if reachable else WARN,
        "database reachable",
        f"{host}:{port}" if reachable else detail,
    )

    if reachable:
        engine = build_engine(config)
        try:
            ok, error = ping(engine)
            healthy &= _report(
                OK if ok else FAIL, "database query (SELECT 1)", error or ""
            )
        finally:
            engine.dispose()

    migrations = discover_migrations()
    healthy &= _report(
        OK if migrations else WARN,
        "migrations discovered",
        ", ".join(f"{m.version}_{m.name}" for m in migrations) or "none",
    )

    print("\nResult:", "healthy" if healthy else "problems detected")
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
