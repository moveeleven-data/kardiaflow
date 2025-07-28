# 11_silver_checks.py
# Silver-layer validation for KardiaFlow smoke tests:
# - Checks that each Silver table contains its required columns

from pyspark.sql import SparkSession

from .config import PASS, FAIL
from .logging_utils import log

# Create or reuse the Spark session
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

    # Determine overall status
    if missing_cols:
        status = FAIL
    else:
        status = PASS

    # Prepare an explanatory message if there are missing columns
    if missing_cols:
        message = f"missing={sorted(missing_cols)}"
    else:
        message = None

    # Log the result: count of missing columns, status, and message
    log(
        layer,
        table,
        "missing_cols_count",
        len(missing_cols),
        status,
        message
    )
