# 12_gold_checks.py
# Gold-layer validation for KardiaFlow smoke tests:
# - Ensures specified columns contain no NULL values

from pyspark.sql import SparkSession, functions as F

from .config import PASS, FAIL
from .logging_utils import log

# Create or reuse the Spark session
spark = SparkSession.builder.getOrCreate()

def check_gold_not_null(table, cols):
    """
    Validate each Gold table column to ensure it contains no nulls.

    Rules:
    1. For each column in `cols`, count NULL values.
    2. Mark PASS if count == 0, otherwise mark FAIL.
    """
    layer = "GOLD"
    df = spark.table(table)

    for column_name in cols:
        # Count how many rows have a NULL in this column
        null_count = df.filter(F.col(column_name).isNull()).count()

        # Determine pass/fail status
        if null_count == 0:
            status = PASS
        else:
            status = FAIL

        # Log the result for this column
        log(
            layer,
            table,
            f"nulls[{column_name}]",
            null_count,
            status
        )