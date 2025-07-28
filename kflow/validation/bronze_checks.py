# 10_bronze_checks.py
# Bronze-layer validation for KardiaFlow smoke tests:
# - Ensures row count > 0
# - Verifies no duplicate PKs (with optional downstream suppression)
# - Checks for null PKs
# - Validates presence of _ingest_ts if column exists

import traceback

from pyspark.sql import SparkSession, functions as F

from .config import PASS, FAIL, SUPPRESS
from .logging_utils import log

# Create or reuse the Spark session
spark = SparkSession.builder.getOrCreate()

def check_bronze(table, pk):
    """
    Validate a Bronze table according to the following rules:
    1. row_count > 0
    2. no duplicate primary keys (with suppression if configured)
    3. no null primary keys
    4. valid _ingest_ts when present
    """
    layer = "BRONZE"
    df = spark.table(table)

    # Compute metrics
    total_rows = df.count()
    duplicate_count = (
        df.groupBy(pk)
          .count()
          .filter("count > 1")
          .count()
    )
    null_count = df.filter(F.col(pk).isNull()).count()

    # 1) Row count check
    if total_rows > 0:
        row_status = PASS
    else:
        row_status = FAIL

    log(
        layer,
        table,
        "row_count",
        total_rows,
        row_status,
        "row_count == 0"
    )

    # 2) Duplicate PK check (with optional downstream suppression)
    if duplicate_count > 0:
        status = FAIL
    else:
        status = PASS

    message = None

    if duplicate_count > 0 and table in SUPPRESS:
        downstream_table, downstream_pk = SUPPRESS[table]
        try:
            downstream_duplicates = (
                spark.table(downstream_table)
                     .groupBy(downstream_pk)
                     .count()
                     .filter("count > 1")
                     .count()
            )
            if downstream_duplicates == 0:
                status = PASS
                message = "duplicates suppressed downstream"
        except Exception:
            message = f"Suppression check failed: {traceback.format_exc()}"

    log(
        layer,
        table,
        "dup_pk",
        duplicate_count,
        status,
        message
    )

    # 3) Null PK check
    if null_count == 0:
        null_status = PASS
    else:
        null_status = FAIL

    log(
        layer,
        table,
        "null_pk_count",
        null_count,
        null_status
    )

    # 4) Ingest timestamp check
    if "_ingest_ts" in df.columns:
        max_ts = df.agg(F.max("_ingest_ts")).first()[0]

        # If no max timestamp, mark as FAIL; otherwise PASS
        if max_ts is None:
            ts_status = FAIL
        else:
            ts_status = PASS

        log(
            layer,
            table,
            "max__ingest_ts",
            max_ts,
            ts_status
        )
