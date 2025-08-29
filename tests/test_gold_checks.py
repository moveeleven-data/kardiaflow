# Kardiaflow tests - Gold checks
# Ensures Gold-layer validation enforces NOT NULL constraints
# on specified critical columns.

from pyspark.sql import Row

from kflow.validation import gold_checks
from kflow.validation.config import FAIL, PASS
from kflow.validation.logging_utils import LOGS


def test_gold_not_null_fails_when_null_present(spark, clear_logs):
    """Fail if any specified column contains NULLs."""

    # Create a DataFrame where one row has a NULL patient_id (should fail)
    df = spark.createDataFrame(
        [Row(patient_id=None, avg_score=5.0), Row(patient_id="p1", avg_score=4.0)]
    )

    # Register as a temp view so check_gold_not_null can resolve it by name
    df.createOrReplaceTempView("gold_feedback_satisfaction")

    # Run the NOT NULL check on patient_id
    gold_checks.check_gold_not_null("gold_feedback_satisfaction", ["patient_id"])

    # Confirm at least one log entry reports FAIL for nulls in patient_id
    null_statuses = [r["status"] for r in LOGS if r["metric"].startswith("nulls[")]
    assert FAIL in null_statuses


def test_gold_not_null_passes_when_no_null(spark, clear_logs):
    """Pass when all values in the specified column are non-null."""

    # Create a DataFrame where every row has a non-null patient_id (should pass)
    df = spark.createDataFrame([Row(patient_id="p1", avg_score=5.0)])

    # Register as a temp view so check_gold_not_null can resolve it by name
    df.createOrReplaceTempView("tbl")

    # Run the NOT NULL check on patient_id
    gold_checks.check_gold_not_null("tbl", ["patient_id"])

    # Confirm the log reports PASS for nulls in patient_id
    null_statuses = [r["status"] for r in LOGS if r["metric"].startswith("nulls[")]
    assert PASS in null_statuses