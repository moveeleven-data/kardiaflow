"""Kardiaflow tests - Silver checks

Validates Silver-layer schema contracts and column requirements.
"""

from __future__ import annotations

from types import SimpleNamespace

from kflow.validation import silver_checks
from kflow.validation.config import FAIL
from kflow.validation.logging_utils import LOGS


def test_silver_contract_missing_cols(monkeypatch, clear_logs):
    """Verify Silver contract validation fails when expected columns are missing."""

    # Simulate a table with only two of the required columns
    fake_df = SimpleNamespace(columns=["encounter_id", "patient_id"])

    # Stub SparkSession in silver_checks to return the fake_df
    # Return fake_df regardless of the table name
    class _StubSession:
        def table(self, _):  # noqa: D401
            return fake_df

    class _Builder:
        def getOrCreate(self):  # noqa: D401
            return _StubSession()

    # Make the module build our stub session instead of a real SparkSession
    monkeypatch.setattr(silver_checks, "SparkSession", SimpleNamespace(builder=_Builder()))

    # Expect START_TS to be missing
    expected = {"encounter_id", "patient_id", "START_TS"}

    silver_checks.check_silver_contract(
        "kardia_silver.silver_encounters",
        expected
    )

    # Last log should indicate a failure and mention missing columns
    last_log = LOGS[-1]
    assert last_log["status"] == FAIL
    assert "missing" in (last_log["message"] or "")
