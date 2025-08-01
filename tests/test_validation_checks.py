# tests/test_validation_checks.py
# Tests for schema contract and data quality validation in Silver and Gold layers.

from types import SimpleNamespace
from pyspark.sql import Row

from kflow.validation import silver_checks, gold_checks
from kflow.validation.config import FAIL, PASS
from kflow.validation.logging_utils import LOGS


def test_silver_contract_missing_cols(monkeypatch, clear_logs):
    """
    Verifies that Silver contract validation fails when expected columns are missing.
    """

    # Simulate a table with only two of the required columns
    fake_df = SimpleNamespace(columns=["encounter_id", "patient_id"])

    class SparkStub:
        def table(self, _):
            return fake_df

    monkeypatch.setattr(silver_checks, "spark", SparkStub())

    # Expect START_TS to be missing
    expected_columns = {"encounter_id", "patient_id", "START_TS"}

    silver_checks.check_silver_contract(
        "kardia_silver.silver_encounters",
        expected_columns
    )

    # Last log should indicate a failure and mention missing columns
    last_log = LOGS[-1]
    assert last_log["status"] == FAIL
    assert "missing" in (last_log["message"] or "")


def test_gold_not_null_fails_when_null_present(spark, monkeypatch, clear_logs):
    """
    Verifies that Gold-layer validation fails if any specified column contains nulls.
    """

    # Simulate a table where one row has a null patient_id
    test_data = [
        Row(patient_id=None, avg_score=5.0),
        Row(patient_id="p1", avg_score=4.0)
    ]
    df = spark.createDataFrame(test_data)

    class SparkStub:
        def table(self, _):
            return df

    monkeypatch.setattr(gold_checks, "spark", SparkStub())

    gold_checks.check_gold_not_null(
        "kardia_gold.gold_feedback_satisfaction",
        ["patient_id"]
    )

    # At least one record should have status FAIL for nulls
    null_statuses = [
        r["status"] for r in LOGS
        if r["metric"].startswith("nulls[")
    ]

    assert FAIL in null_statuses


def test_gold_not_null_passes_when_no_null(spark, monkeypatch, clear_logs):
    """
    Verifies that Gold-layer validation passes when no nulls are present.
    """

    # All rows have non-null patient_id values
    test_data = [Row(patient_id="p1", avg_score=5.0)]
    df = spark.createDataFrame(test_data)

    class SparkStub:
        def table(self, _):
            return df

    monkeypatch.setattr(gold_checks, "spark", SparkStub())

    gold_checks.check_gold_not_null("tbl", ["patient_id"])

    # The test should pass for the specified column
    null_statuses = [
        r["status"] for r in LOGS
        if r["metric"].startswith("nulls[")
    ]

    assert PASS in null_statuses