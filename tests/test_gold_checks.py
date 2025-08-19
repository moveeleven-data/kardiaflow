"""Kardiaflow tests - Gold checks

Validates NOT NULL enforcement on required Gold-layer columns.
"""

from __future__ import annotations

from types import SimpleNamespace
from pyspark.sql import Row

from kflow.validation import gold_checks
from kflow.validation.config import FAIL, PASS
from kflow.validation.logging_utils import LOGS


def test_gold_not_null_fails_when_null_present(spark, monkeypatch, clear_logs):
    """Verify Gold validation fails if any specified column contains NULLs."""

    # Simulate a table where one row has a NULL patient_id
    df = spark.createDataFrame(
        [Row(patient_id=None, avg_score=5.0), Row(patient_id="p1", avg_score=4.0)]
    )

    # Stub SparkSession in gold_checks to return the test DataFrame
    # Return df regardless of the table name
    class _StubSession:
        def table(self, _):  # noqa: D401
            return df

    class _Builder:
        def getOrCreate(self):  # noqa: D401
            return _StubSession()

    monkeypatch.setattr(gold_checks, "SparkSession", SimpleNamespace(builder=_Builder()))

    gold_checks.check_gold_not_null(
        "kardia_gold.gold_feedback_satisfaction",
        ["patient_id"]
    )

    # At least one record should be FAIL for nulls
    null_statuses = [r["status"] for r in LOGS if r["metric"].startswith("nulls[")]
    assert FAIL in null_statuses


def test_gold_not_null_passes_when_no_null(spark, monkeypatch, clear_logs):
    """Verify Gold validation passes when no NULLs are present."""

    # All rows have non-null patient_id values
    df = spark.createDataFrame([Row(patient_id="p1", avg_score=5.0)])

    # Stub SparkSession in gold_checks to return the test DataFrame
    class _StubSession:
        def table(self, _):  # noqa: D401
            return df

    class _Builder:
        def getOrCreate(self):  # noqa: D401
            return _StubSession()

    monkeypatch.setattr(gold_checks, "SparkSession", SimpleNamespace(builder=_Builder()))

    gold_checks.check_gold_not_null("tbl", ["patient_id"])

    # Should pass for the specified column
    null_statuses = [r["status"] for r in LOGS if r["metric"].startswith("nulls[")]
    assert PASS in null_statuses
