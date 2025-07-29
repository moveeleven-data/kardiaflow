# silver_checks.py
# Ensures each Silver table adheres to its contract
# This guards against schema drift and incomplete transformations

from pyspark.sql import SparkSession

from .config import PASS, FAIL
from .logging_utils import log

# Create the Spark session. (needed to run via Lakeflow Jobs)
spark = SparkSession.builder.getOrCreate()

def check_silver_contract(table, expected_cols):
    """
    Validate a Silver table to ensure it contains all expected columns.

    Rules:
    1. Compute the set of actual columns in the table
    2. Compare against expected_cols
    3. PASS if none are missing, otherwise FAIL
    """
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
