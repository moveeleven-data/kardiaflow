"""Kardiaflow tests - Bronze checks

Validates null/duplicate primary keys and _ingest_ts presence.
"""

from __future__ import annotations

from datetime import datetime
from pyspark.sql import Row

from kflow.validation import bronze_checks
from kflow.validation.config import PASS, FAIL
from kflow.validation.logging_utils import LOGS


def test_bronze_checks_counts_and_statuses(spark, monkeypatch, clear_logs):
    """Verify the Bronze check sees one null PK, one duplicate PK, and valid _ingest_ts."""

    # Create test rows simulating Bronze table contents
    rows = [
        Row(ID=None, _ingest_ts=datetime.utcnow()),
        Row(ID=1,    _ingest_ts=datetime.utcnow()),
        Row(ID=1,    _ingest_ts=datetime.utcnow()),
        Row(ID=2,    _ingest_ts=datetime.utcnow()),
    ]
    test_df = spark.createDataFrame(rows)

    # Stub SparkSession in bronze_checks to return the test DataFrame
    # Return the test_df regardless of table name
    class _StubSession:
            def table(self, _): return test_df
    class _Builder:
            def getOrCreate(self): return _StubSession()

    # Make the module build our stub session instead of a real SparkSession
    from types import SimpleNamespace
    monkeypatch.setattr(bronze_checks, "SparkSession", SimpleNamespace(builder=_Builder()))

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

    assert row_count_status == PASS  # Non-zero row count
    assert dup_pk_status == FAIL     # Duplicate ID=1
    assert null_pk_status == FAIL    # One null ID
    assert ts_status == PASS         # All rows have _ingest_ts
