"""Migration runner behaviour, exercised on an in-memory database."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from infrastructure.database.migration import (
    applied_migrations,
    discover_migrations,
    run_migrations,
)


def _engine():
    return create_engine("sqlite://", future=True)


def test_baseline_migration_is_discovered() -> None:
    migrations = discover_migrations()
    assert [m.version for m in migrations] == ["0001"]


def test_migrations_apply_and_are_idempotent() -> None:
    engine = _engine()
    try:
        first = run_migrations(engine)
        assert first.applied == ["0001"]

        second = run_migrations(engine)
        assert second.applied == []
        assert second.skipped == ["0001"]
    finally:
        engine.dispose()


def test_migration_creates_expected_objects() -> None:
    engine = _engine()
    try:
        run_migrations(engine)
        tables = set(inspect(engine).get_table_names())
        assert "schema_migrations" in tables
        assert "platform_metadata" in tables
    finally:
        engine.dispose()


def test_dry_run_changes_nothing() -> None:
    engine = _engine()
    try:
        run_migrations(engine, dry_run=True)
        tables = set(inspect(engine).get_table_names())
        assert "platform_metadata" not in tables
        assert applied_migrations(engine) == {}
    finally:
        engine.dispose()


def test_checksum_drift_is_detected() -> None:
    engine = _engine()
    try:
        run_migrations(engine)
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE schema_migrations SET checksum = 'tampered' WHERE version = '0001'")
            )
        try:
            run_migrations(engine)
        except Exception as exc:  # noqa: BLE001
            assert "checksum" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("checksum drift must be detected")
    finally:
        engine.dispose()


def test_no_business_tables_exist() -> None:
    """Guard: STEP 0 must not create industry tables."""
    forbidden = {"orders", "restaurants", "menus", "employees", "family_tasks", "shopping_lists"}
    engine = _engine()
    try:
        run_migrations(engine)
        assert not forbidden & set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
