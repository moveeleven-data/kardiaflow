# kflow/validation/gold_checks.py
"""Kardiaflow validations - Gold checks.

Asserts that specified columns contain no NULL values.
"""

from __future__ import annotations

from pyspark.sql import SparkSession, functions as F

from kflow.validation.config import PASS, FAIL
from kflow.validation.logging_utils import log


def check_gold_not_null(table: str, cols: list[str] | set[str]) -> None:
    """Fail if any of the given columns contain NULLs."""
    spark = SparkSession.builder.getOrCreate()
    layer = "GOLD"
    df = spark.table(table)

    for column_name in cols:
        # Count how many rows have a NULL in this column
        null_count = df.filter(F.col(column_name).isNull()).count()

        if null_count == 0:
            status = PASS
        else:
            status = FAIL

        # Log result in memory for later write to `kardia_validation.smoke_results`
        log(
            layer,
            table,
            f"nulls[{column_name}]",
            null_count,
            status
        )