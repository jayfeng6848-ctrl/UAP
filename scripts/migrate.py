#!/usr/bin/env python
"""Apply pending database migrations.

Usage:
    python scripts/migrate.py            # apply
    python scripts/migrate.py --dry-run  # report only, change nothing
    python scripts/migrate.py --status   # list applied / pending
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings  # noqa: E402
from infrastructure.database.config import DatabaseConfig  # noqa: E402
from infrastructure.database.migration import (  # noqa: E402
    applied_migrations,
    discover_migrations,
    run_migrations,
)
from infrastructure.database.session import build_engine  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UAP migration runner")
    parser.add_argument("--dry-run", action="store_true", help="report only")
    parser.add_argument("--status", action="store_true", help="show applied/pending")
    args = parser.parse_args(argv)

    settings = get_settings()
    config = DatabaseConfig.from_settings(settings)
    config.validate()

    if args.status:
        engine = build_engine(config)
        try:
            applied = applied_migrations(engine)
        finally:
            engine.dispose()
        pending = [m.version for m in discover_migrations() if m.version not in applied]
        print(json.dumps({"applied": sorted(applied), "pending": pending}, indent=2))
        return 0

    engine = build_engine(config)
    try:
        report = run_migrations(engine, dry_run=args.dry_run)
    finally:
        engine.dispose()

    print(
        json.dumps(
            {
                "target": config.safe_url(),
                "applied": report.applied,
                "skipped": report.skipped,
                "dry_run": report.dry_run,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
