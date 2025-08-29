# Kardiaflow tests - Bronze checks
# Ensures Bronze-level validation catches null/duplicate primary keys
# and verifies that every row has an _ingest_ts column.

from datetime import datetime
from pyspark.sql import Row

from kflow.validation import bronze_checks
from kflow.validation.config import PASS, FAIL
from kflow.validation.logging_utils import LOGS


def test_bronze_checks_counts_and_statuses(spark, clear_logs):
    """Verify one null PK, one duplicate PK, and valid _ingest_ts."""

    # Build a small DataFrame to simulate Bronze table contents
    rows = [
        Row(ID=None, _ingest_ts=datetime.utcnow()),  # one null PK
        Row(ID=1,    _ingest_ts=datetime.utcnow()),  # duplicate PK
        Row(ID=1,    _ingest_ts=datetime.utcnow()),  # duplicate PK
        Row(ID=2,    _ingest_ts=datetime.utcnow()),  # unique PK
    ]
    df = spark.createDataFrame(rows)

    # Expose the DataFrame as a temporary view so check_bronze can query it
    df.createOrReplaceTempView("bronze_patients")

    # Run the Bronze-level validation against the temp view
    bronze_checks.check_bronze("bronze_patients", "ID")

    # Collect log records into a dictionary keyed by metric name
    log_by_metric = {rec["metric"]: rec for rec in LOGS}

    # Verify expected outcomes for each metric
    assert log_by_metric["row_count"]["status"] == PASS       # Table has rows
    assert log_by_metric["dup_pk"]["status"] == FAIL          # Duplicate ID detected
    assert log_by_metric["null_pk_count"]["status"] == FAIL   # Null ID detected
    assert log_by_metric["max__ingest_ts"]["status"] == PASS  # All rows have _ingest_ts
