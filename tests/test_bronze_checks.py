# tests/test_bronze_checks.py
# Unit test for the Bronze-level validation check.
# Covers:
# - Null primary key detection
# - Duplicate primary key detection
# - Presence of valid _ingest_ts timestamps

from datetime import datetime
from pyspark.sql import Row

from kflow.validation import bronze_checks
from kflow.validation.config import PASS, FAIL
from kflow.validation.logging_utils import LOGS


def test_bronze_checks_counts_and_statuses(spark, monkeypatch, clear_logs):
    """
    Verifies that the Bronze check detects:
    - One null primary key
    - One duplicate primary key
    - Valid _ingest_ts values on all rows
    """

    # Create test rows simulating Bronze table contents
    row1 = Row(ID=None, _ingest_ts=datetime.utcnow())  # null ID
    row2 = Row(ID=1,    _ingest_ts=datetime.utcnow())  # valid
    row3 = Row(ID=1,    _ingest_ts=datetime.utcnow())  # duplicate ID
    row4 = Row(ID=2,    _ingest_ts=datetime.utcnow())  # valid

    test_rows = [row1, row2, row3, row4]
    test_df = spark.createDataFrame(test_rows)

    # Stub SparkSession in bronze_checks to return our test DataFrame
    class SparkStub:
        def table(self, _):
            return test_df

    monkeypatch.setattr(bronze_checks, "spark", SparkStub())

    # Run the Bronze-level check on test data
    bronze_checks.check_bronze("kardia_bronze.bronze_patients", "ID")

    # Reformat log output into a dictionary indexed by metric name
    log_by_metric = {}
    for record in LOGS:
        metric_name = record["metric"]
        log_by_metric[metric_name] = record

    # Assertions
    row_count_status = log_by_metric["row_count"]["status"]
    dup_pk_status = log_by_metric["dup_pk"]["status"]
    null_pk_status = log_by_metric["null_pk_count"]["status"]
    ts_status = log_by_metric["max__ingest_ts"]["status"]

    assert row_count_status == PASS          # Non-zero row count
    assert dup_pk_status == FAIL             # Duplicate ID=1
    assert null_pk_status == FAIL            # One null ID
    assert ts_status == PASS                 # All rows have _ingest_ts
