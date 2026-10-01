"""R-1 specialised durability tests (P16 F-P16-I-05 §19 / §21).

Real runtime, real database, real failure path. Only the audit append is made to
fail (controlled injection at the canonical audit write boundary), and the run's
terminal state is then verified from an independent connection.
"""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from core.agent import ErrorCode
from services.agent.repository import AgentRuntimeRepository
from tests.integration.test_p16_agent_run import (
    P16_DB,
    _rows,
    _runtime,
    _seed,
    _stub_registry,
    engine as p16_engine,  # reuse the module-scoped fresh-DB fixture
)

pytestmark = pytest.mark.integration

ABSENT_SECRET = "env:P16_ABSENT_SECRET"


def test_failure_audit_does_not_rollback_failed_state(p16_engine, monkeypatch) -> None:
    """An audit append failure must not roll back an already-persisted FAILED run."""
    ids = _seed(p16_engine, secret_ref=ABSENT_SECRET)
    calls = {"injected": 0}

    def _injected_audit_failure(self, session, **kwargs):  # noqa: ANN001, ANN003
        calls["injected"] += 1
        raise RuntimeError("injected audit append failure")

    monkeypatch.setattr(AgentRuntimeRepository, "insert_audit", _injected_audit_failure)
    database, service = _runtime(_stub_registry("echo"), environ={})
    try:
        outcome = service.run(
            agent_id=ids["agent"],
            actor_type="USER",
            actor_id=ids["user"],
            tenant_id=ids["tenant"],
            input_text="audit injection",
        )
    finally:
        database.dispose()

    assert calls["injected"] >= 1, "audit failure injection was never triggered"
    assert outcome.status == "FAILED"
    assert outcome.failure_code == ErrorCode.CREDENTIAL_UNAVAILABLE

    # Independent connection: the terminal state survived the audit failure.
    rows = _rows(
        p16_engine,
        "SELECT status, failure_code, failure_metadata::text AS meta FROM agent_runs"
        " WHERE id = CAST(:id AS uuid)",
        id=outcome.run_id,
    )
    assert len(rows) == 1, "run ledger row disappeared"
    assert rows[0]["status"] == "FAILED"
    assert rows[0]["failure_code"] == ErrorCode.CREDENTIAL_UNAVAILABLE
    assert ErrorCode.CREDENTIAL_UNAVAILABLE in rows[0]["meta"]


def test_mark_run_failed_rowcount_one(p16_engine) -> None:
    """rowcount == 1 persists the terminal state; rowcount == 0 is never silent."""
    ids = _seed(p16_engine, secret_ref=ABSENT_SECRET)
    database, service = _runtime(_stub_registry("echo"), environ={})
    try:
        outcome = service.run(
            agent_id=ids["agent"],
            actor_type="USER",
            actor_id=ids["user"],
            tenant_id=ids["tenant"],
            input_text="rowcount probe",
        )

        # --- rowcount == 1 (real admitted run, real failure transition)
        rows = _rows(
            p16_engine,
            "SELECT status, failure_code FROM agent_runs WHERE id = CAST(:id AS uuid)",
            id=outcome.run_id,
        )
        assert len(rows) == 1
        assert rows[0]["status"] == "FAILED" and rows[0]["failure_code"] == ErrorCode.CREDENTIAL_UNAVAILABLE

        # --- rowcount == 0 (no matching row): must be reported, not accepted
        missing_run_id = str(uuid.uuid4())
        with database.transaction() as session:
            applied = service._repo.mark_run_failed(
                session,
                run_id=missing_run_id,
                failure_code=ErrorCode.INTERNAL_RUNTIME_ERROR,
                failure_metadata={"code": ErrorCode.INTERNAL_RUNTIME_ERROR},
            )
        assert applied is False, "rowcount == 0 was silently accepted"

        # the runtime's failure path reports False (evidence is logged, never swallowed)
        assert service._fail(missing_run_id, ErrorCode.INTERNAL_RUNTIME_ERROR) is False

        rows = _rows(
            p16_engine,
            "SELECT count(*) AS n FROM agent_runs WHERE id = CAST(:id AS uuid)",
            id=missing_run_id,
        )
        assert rows[0]["n"] == 0
    finally:
        database.dispose()
