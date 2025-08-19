# kflow/validation/silver_checks.py
"""Kardiaflow validations — Silver checks.

Verifies each Silver table contains all expected columns (schema contract).
"""

from __future__ import annotations

from pyspark.sql import SparkSession

from kflow.validation.config import PASS, FAIL
from kflow.validation.logging_utils import log


def check_silver_contract(table, expected_cols):
    """Validate a Silver table to ensure it contains all expected columns.

    Rules:
    1. Compute the set of actual columns in the table
    2. Compare against expected_cols
    3. PASS if none are missing, otherwise FAIL
    """
    spark = SparkSession.builder.getOrCreate()
    layer = "SILVER"

    # Retrieve the actual columns from the table
    actual_cols = set(spark.table(table).columns)

    # Determine which expected columns are missing
    missing_cols = expected_cols - actual_cols

    if missing_cols:
        status = FAIL
        message = f"missing={sorted(missing_cols)}"
    else:
        status = PASS
        message = None

    # Log result in memory for later write to `kardia_validation.smoke_results`
    log(
        layer,
        table,
        "missing_cols_count",
        len(missing_cols),
        status,
        message
    )
