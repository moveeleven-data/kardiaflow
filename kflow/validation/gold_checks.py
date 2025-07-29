# gold_checks.py
# Ensures Gold-layer columns contain no NULL values

from pyspark.sql import SparkSession, functions as F

from .config import PASS, FAIL
from .logging_utils import log

# Create the Spark session. (needed to run via Lakeflow Jobs)
spark = SparkSession.builder.getOrCreate()

def check_gold_not_null(table, cols):
    """Check each specified Gold column for nulls and log the result."""
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