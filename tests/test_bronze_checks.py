from datetime import datetime
from pyspark.sql import Row
from pyspark.sql.functions import lit
from kflow.validation import bronze_checks
from kflow.validation.logging_utils import LOGS
from kflow.validation.config import PASS, FAIL

def test_bronze_checks_counts_and_statuses(spark, monkeypatch, clear_logs):
    rows = [
        Row(ID=None,  _ingest_ts=datetime.utcnow()),
        Row(ID=1,     _ingest_ts=datetime.utcnow()),
        Row(ID=1,     _ingest_ts=datetime.utcnow()),  # duplicate
        Row(ID=2,     _ingest_ts=datetime.utcnow()),
    ]
    df = spark.createDataFrame(rows)

    class SparkStub:
        def table(self, name):  # return the DF for any name
            return df

    monkeypatch.setattr(bronze_checks, "spark", SparkStub())

    bronze_checks.check_bronze("kardia_bronze.bronze_patients", "ID")

    # Collect by metric
    by_metric = {r["metric"]: r for r in LOGS}

    # Row count > 0 => PASS
    assert by_metric["row_count"]["status"] == PASS
    # Duplicates exist => FAIL unless suppressed (not in this test)
    assert by_metric["dup_pk"]["status"] == FAIL
    # Null PK exists => FAIL
    assert by_metric["null_pk_count"]["status"] == FAIL
    # _ingest_ts present and non-null => PASS
    assert by_metric["max__ingest_ts"]["status"] == PASS
