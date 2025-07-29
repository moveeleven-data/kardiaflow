# run_smoke.py
# Orchestrator for KardiaFlow smoke tests:
# - Installs the kflow package from DBFS
# - Runs all Bronze, Silver, and Gold checks
# - Persists results to Delta and prints a summary

import sys
import subprocess
import traceback

from pyspark.sql import SparkSession, functions as F

# Install the kflow package from shared DBFS libraries
subprocess.check_call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--no-index",
        "--find-links=/dbfs/Shared/libs",
        "kflow"
    ]
)

from .config import (
    RESULTS_TABLE,
    BRONZE,
    SILVER_CONTRACTS,
    GOLD_NOT_NULL,
    PASS,
    FAIL,
    ERROR
)
from .logging_utils import LOGS, log
from .bronze_checks import check_bronze
from .silver_checks import check_silver_contract
from .gold_checks   import check_gold_not_null

# Create the Spark session. (needed to run via Lakeflow Jobs)
spark = SparkSession.builder.getOrCreate()

def ensure_results_table():
    """
    Ensure the validation database and results table exist.
    """
    spark.sql("CREATE DATABASE IF NOT EXISTS kardia_validation")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {RESULTS_TABLE} (
            run_ts     TIMESTAMP,
            layer      STRING,
            table_name STRING,
            metric     STRING,
            value      STRING,
            status     STRING,
            message    STRING
        ) USING DELTA
        """
    )

def run_all_smoke_tests() -> int:
    """
    Execute all Bronze, Silver, and Gold validations and persist results.

    Return 0 if all tests pass, 1 if any fail or error.
    """
    ensure_results_table()

    # Run Bronze-layer checks - Each table is paired with its primary key
    for table_name, pk in BRONZE:
        try:
            check_bronze(table_name, pk)
        except Exception:
            error_message = traceback.format_exc()
            log(
                layer="BRONZE",
                table=table_name,
                metric="exception",
                value=None,
                status=ERROR,
                message=error_message
            )

    # Run Silver-layer checks - Each table is mapped to a list of required columns
    for table_name, expected_cols in SILVER_CONTRACTS.items():
        try:
            check_silver_contract(table_name, expected_cols)
        except Exception:
            error_message = traceback.format_exc()
            log(
                layer="SILVER",
                table=table_name,
                metric="exception",
                value=None,
                status=ERROR,
                message=error_message
            )

    # Run Gold-layer not-null validations
    # Each table is paired with columns that must not contain null values
    for table_name, cols in GOLD_NOT_NULL.items():
        try:
            check_gold_not_null(table_name, cols)
        except Exception:
            error_message = traceback.format_exc()
            log(
                layer="GOLD",
                table=table_name,
                metric="exception",
                value=None,
                status=ERROR,
                message=error_message
            )

    # Write all collected logs to the results table
    results_df = spark.createDataFrame(LOGS)
    results_df.write.mode("append").saveAsTable(RESULTS_TABLE)

    # Summarize overall test results based on status counts
    failures = results_df.filter(F.col("status").isin(FAIL, ERROR)).count()
    summary = "FAIL" if failures > 0 else "PASS"
    print(f"\nSMOKE TEST SUMMARY: {summary}")

    if failures == 0:
        return 0
    else:
        return 1

# When run directly, execute all tests - useful for CI/CD
if __name__ == "__main__":
    try:
        exit_code = run_all_smoke_tests()
        if exit_code != 0:
            raise Exception("Smoke tests failed")
    except Exception:
        traceback.print_exc()
        raise
