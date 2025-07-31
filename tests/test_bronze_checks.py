# tests/test_bronze_checks.py
# Test for the Bronze validator:
# - 1 null PK
# - 1 duplicate PK
# - valid _ingest_ts present
# We stub the module's `spark.table(...)` to return our in-memory DF.

from datetime import datetime
from pyspark.sql import Row

from kflow.validation import bronze_checks
from kflow.validation.logging_utils import LOGS
from kflow.validation.config import PASS, FAIL


def test_bronze_checks_counts_and_statuses(spark, monkeypatch, clear_logs):
    # Build a small DF with: 1 null PK, 1 duplicate PK, valid _ingest_ts on all rows
    rows = [
        Row(ID=None, _ingest_ts=datetime.utcnow()),
        Row(ID=1,    _ingest_ts=datetime.utcnow()),
        Row(ID=1,    _ingest_ts=datetime.utcnow()),  # duplicate
        Row(ID=2,    _ingest_ts=datetime.utcnow()),
    ]
    df = spark.createDataFrame(rows)

    class SparkStub:
        def table(self, _):
            return df  # always return our DF regardless of table name

    # Replace the module's SparkSession with our stub (keeps the test hermetic)
    monkeypatch.setattr(bronze_checks, "spark", SparkStub())

    # Run the check
    bronze_checks.check_bronze("kardia_bronze.bronze_patients", "ID")

    # Index logs by metric for easy assertions
    by_metric = {r["metric"]: r for r in LOGS}

    # Assertions: simple, outcome-focused
    assert by_metric["row_count"]["status"] == PASS        # rows present
    assert by_metric["dup_pk"]["status"] == FAIL           # duplicate ID=1
    assert by_metric["null_pk_count"]["status"] == FAIL    # one null ID
    assert by_metric["max__ingest_ts"]["status"] == PASS   # timestamp present
