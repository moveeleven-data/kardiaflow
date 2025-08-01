# tests/test_validation_checks.py
from types import SimpleNamespace

from pyspark.sql import Row

from kflow.validation import silver_checks, gold_checks
from kflow.validation.logging_utils import LOGS
from kflow.validation.config import FAIL, PASS

def test_silver_contract_missing_cols(monkeypatch, clear_logs):
    # Fake DF with limited columns
    fake_df = SimpleNamespace(columns=["encounter_id", "patient_id"])
    class SparkStub:
        def table(self, name):  # ignore table name, return fake df
            return fake_df
    monkeypatch.setattr(silver_checks, "spark", SparkStub())

    expected = {"encounter_id", "patient_id", "START_TS"}  # START_TS missing
    silver_checks.check_silver_contract("kardia_silver.silver_encounters", expected)

    # Last log reflects FAIL and mentions missing column
    assert LOGS[-1]["status"] == FAIL
    assert "missing" in (LOGS[-1]["message"] or "")

def test_gold_not_null_fails_when_null_present(spark, monkeypatch, clear_logs):
    df = spark.createDataFrame([Row(patient_id=None, avg_score=5.0), Row(patient_id="p1", avg_score=4.0)])
    class SparkStub:
        def table(self, name):  # return our real DF
            return df
    monkeypatch.setattr(gold_checks, "spark", SparkStub())

    gold_checks.check_gold_not_null("kardia_gold.gold_feedback_satisfaction", ["patient_id"])
    # at least one FAIL should be logged for patient_id nulls
    statuses = [r["status"] for r in LOGS if r["metric"].startswith("nulls[")]
    assert FAIL in statuses

def test_gold_not_null_passes_when_no_null(spark, monkeypatch, clear_logs):
    df = spark.createDataFrame([Row(patient_id="p1", avg_score=5.0)])
    class SparkStub:
        def table(self, name):  # return DF without nulls
            return df
    monkeypatch.setattr(gold_checks, "spark", SparkStub())

    gold_checks.check_gold_not_null("tbl", ["patient_id"])
    statuses = [r["status"] for r in LOGS if r["metric"].startswith("nulls[")]
    assert PASS in statuses
