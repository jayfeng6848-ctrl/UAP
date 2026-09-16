"""Migration failure / recovery checks (B1-0).

Uses a throwaway copy of the alembic script location with an intentionally
broken revision to prove:
  * a failing migration rolls back the WHOLE upgrade (no partial objects)
  * the advisory lock is released after failure
  * after removing the bad revision the same runner recovers and reaches head
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from tests.integration.alembic_testkit import (
    BASE_DSN,
    TEST_DB,
    advisory_lock_rows,
    current_revision,
    database_reachable,
    reset_test_database,
)

pytestmark = pytest.mark.integration

if not database_reachable():
    pytest.skip(
        "PostgreSQL is not reachable; start it with `docker compose up -d postgres`",
        allow_module_level=True,
    )

_GOOD_REV = """\
revision = "0002_failure_probe"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

def upgrade() -> None:
    from alembic import op
    op.execute("CREATE FUNCTION f_b1_failure_probe() RETURNS int LANGUAGE sql AS 'SELECT 1'")

def downgrade() -> None:
    from alembic import op
    op.execute("DROP FUNCTION IF EXISTS f_b1_failure_probe()")
"""

_BAD_REV = """\
revision = "0003_will_fail"
down_revision = "0002_failure_probe"
branch_labels = None
depends_on = None

def upgrade() -> None:
    raise RuntimeError("boom: intentional migration failure")

def downgrade() -> None:
    pass
"""


@pytest.fixture()
def tmp_alembic_env():
    """A throwaway copy of migrations_alembic with a broken head revision."""
    reset_test_database()
    src = Path(__file__).resolve().parents[2] / "migrations_alembic"
    with tempfile.TemporaryDirectory() as td:
        dst = Path(td) / "ma"
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        versions = dst / "versions"
        for f in versions.glob("*.py"):
            f.unlink()
        (versions / "0001_baseline.py").write_text(
            'revision = "0001_baseline"\ndown_revision = None\n'
            "branch_labels = None\ndepends_on = None\n\n"
            "def upgrade() -> None:\n    pass\n\n"
            "def downgrade() -> None:\n    pass\n",
            encoding="utf-8",
        )
        (versions / "0002_failure_probe.py").write_text(_GOOD_REV, encoding="utf-8")
        (versions / "0003_will_fail.py").write_text(_BAD_REV, encoding="utf-8")

        cfg = Config(str(src.parent.parent / "alembic.ini"))
        cfg.set_main_option("script_location", str(dst))
        cfg.attributes["url"] = BASE_DSN
        cfg.attributes["lock_mode"] = "wait"
        yield cfg


def _probe_function_count() -> int:
    engine = sa.create_engine(BASE_DSN)
    try:
        with engine.connect() as conn:
            return conn.execute(
                sa.text("SELECT count(*) FROM pg_proc WHERE proname = 'f_b1_failure_probe'")
            ).scalar()
    finally:
        engine.dispose()


def test_failing_migration_rolls_back_and_releases_lock(tmp_alembic_env) -> None:
    cfg = tmp_alembic_env
    with pytest.raises(RuntimeError, match="boom"):
        command.upgrade(cfg, "head")

    # Whole run was one transaction: everything (even the version table and
    # the 0002 function) was rolled back -> strongest no-half-objects proof.
    assert current_revision() is None, "no revision may survive a failed run"
    assert _probe_function_count() == 0, "partial objects must not remain"

    # Lock is released after the failure (no permanent lockout).
    assert advisory_lock_rows() == 0


def test_runner_recovers_after_removing_bad_revision(tmp_alembic_env) -> None:
    cfg = tmp_alembic_env
    with pytest.raises(RuntimeError, match="boom"):
        command.upgrade(cfg, "head")
    assert advisory_lock_rows() == 0

    # Remove the broken revision, then the same infra recovers to head.
    bad = Path(cfg.get_main_option("script_location")) / "versions" / "0003_will_fail.py"
    bad.unlink()
    command.upgrade(cfg, "head")
    assert current_revision() == "0002_failure_probe"
    assert _probe_function_count() == 1
    assert advisory_lock_rows() == 0
