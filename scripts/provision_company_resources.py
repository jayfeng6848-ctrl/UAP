#!/usr/bin/env python
"""Pre-provision Company collection resources (operator path — never automatic).

Frozen by PDL Appendix AF D-P20D-02 and the implementation authorization §G2
(pre-built collection model): Company authorization resolves a **tenant-level
collection resource** (``company_employee`` / ``company_assignment``), and a
missing row is a denial. Business request paths never create it, so this operator
entry point pre-builds it.

Usage:
    python scripts/provision_company_resources.py --status
    python scripts/provision_company_resources.py --tenant <tenant-uuid>
    python scripts/provision_company_resources.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sqlalchemy as sa  # noqa: E402

from config.settings import get_settings  # noqa: E402
from infrastructure.database.config import DatabaseConfig  # noqa: E402
from infrastructure.database.session import build_engine  # noqa: E402
from services.company.projection import (  # noqa: E402
    COLLECTION_NATURAL_KEYS,
    backfill_company_collections,
    collection_resource,
)


def _pending(engine: sa.Engine) -> dict[str, list[str]]:
    """Tenants that still lack one of the Company collection resources."""
    pending: dict[str, list[str]] = {}
    with engine.connect() as conn:
        tenants = [
            str(row[0])
            for row in conn.execute(
                sa.text("SELECT id FROM tenants WHERE status <> 'deleted' ORDER BY id")
            ).all()
        ]
        for resource_type in COLLECTION_NATURAL_KEYS:
            missing = [
                tenant_id
                for tenant_id in tenants
                if collection_resource(
                    conn, tenant_id=tenant_id, resource_type=resource_type
                )
                is None
            ]
            if missing:
                pending[resource_type] = missing
    return pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Company collection-resource provisioning")
    parser.add_argument("--tenant", help="project one tenant id")
    parser.add_argument("--all", action="store_true", help="project every tenant")
    parser.add_argument("--status", action="store_true", help="report only, change nothing")
    args = parser.parse_args(argv)

    settings = get_settings()
    config = DatabaseConfig.from_settings(settings)
    config.validate()
    engine = build_engine(config)
    try:
        if args.status or not (args.all or args.tenant):
            print(json.dumps({"pending": _pending(engine)}, sort_keys=True))
            return 0
        result = backfill_company_collections(engine, tenant_id=args.tenant)
        print(json.dumps(result, sort_keys=True))
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
