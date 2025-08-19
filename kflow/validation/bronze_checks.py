# kflow/validation/bronze_checks.py
# Validates Bronze tables for row count and PK uniqueness/nulls

import traceback

from pyspark.sql import SparkSession, functions as F

from .config import PASS, FAIL, SUPPRESS
from .logging_utils import log

# Create the Spark session. (needed to run via Lakeflow Jobs)
spark = SparkSession.builder.getOrCreate()

def check_bronze(table, pk):
    """
    Validate a Bronze table according to the following rules:
    1. row_count > 0
    2. no duplicate primary keys
    3. no null primary keys
    4. valid _ingest_ts
    """
    layer = "BRONZE"
    df = spark.table(table)
    total_rows = df.count()

    # Count how many times each primary key value appears
    pk_counts = df.groupBy(pk).count()

    # Filter to keep only keys that appear more than once
    duplicated_keys = pk_counts.filter(F.col("count") > 1)

    # Count how many unique primary key values are duplicated
    duplicate_count = duplicated_keys.count()

    # Count how many records have a null primary key
    null_count = df.filter(F.col(pk).isNull()).count()

    # 1. Row count check
    if total_rows > 0:
        row_status = PASS
    else:
        row_status = FAIL

    # Log result in memory for later write to `kardia_validation.smoke_results`
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

    # Prepare a default log message for the duplicate check
    message = None

    # If there are duplicate PKs AND the table is listed in the SUPPRESS registry,
    # validate whether those duplicates are resolved downstream.
    if duplicate_count > 0 and table in SUPPRESS:

        # Get the downstream table name and its PK from the SUPPRESS dictionary
        downstream_table, downstream_pk = SUPPRESS[table]

        try:
            ds_df = spark.table(downstream_table)

            # Count how many times each downstream PK appears
            ds_pk_counts = ds_df.groupBy(downstream_pk).count()

            # Filter to keep only downstream PKs that appear more than once
            duplicated_ds_keys = ds_pk_counts.filter(F.col("count") > 1)

            # Count how many unique PKs are duplicated downstream
            downstream_duplicates = duplicated_ds_keys.count()

            # If no duplicates remain downstream, override FAIL status with PASS
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

    # 3. Null PK check
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

    # 4. Ingest timestamp check
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
