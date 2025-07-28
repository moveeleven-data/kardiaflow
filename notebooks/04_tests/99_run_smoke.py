# 99_run_smoke.py
# Orchestrator for KardiaFlow smoke tests:
# - Installs the kflow package from DBFS
# - Runs all Bronze, Silver, and Gold checks
# - Persists results to Delta and prints a summary

import sys
import subprocess
import traceback

from pyspark.sql import SparkSession, functions as F

# Install the kflow package from shared DBFS libraries
subprocess.check_call([
    sys.executable,
    "-m", "pip", "install",
    "--no-deps", "--no-index",
    "--find-links=/dbfs/Shared/libs",
    "kflow"
])

from _00_config import (
    RESULTS_TABLE,
    BRONZE,
    SILVER_CONTRACTS,
    GOLD_NOT_NULL,
    PASS,
    FAIL,
    ERROR
)
from _01_logging_utils import LOGS, log
from _10_bronze_checks import check_bronze
from _11_silver_checks import check_silver_contract
from _12_gold_checks import check_gold_not_null

# Create or reuse the Spark session
spark = SparkSession.builder.getOrCreate()

def ensure_results_table():
    """
    Create the validation database and results table if they do not already exist.
    """
    spark.sql("CREATE DATABASE IF NOT EXISTS kardia_validation")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {RESULTS_TABLE} (
            run_ts     TIMESTAMP,
            layer      STRING,
            table_name STRING,
            metric     STRING,
            value      STRING,
            status     STRING,
            message    STRING
        ) USING DELTA
    """)

def run_all_smoke_tests() -> int:
    """
    Execute all Bronze, Silver, and Gold smoke tests and persist results.

    Returns:
        int: 0 if all tests PASS; 1 if any FAIL or ERROR.
    """
    # Prepare the results table
    ensure_results_table()

    # --- Bronze tests ---
    for table_name, pk in BRONZE:
        try:
            check_bronze(table_name, pk)
        except Exception:
            error_msg = traceback.format_exc()
            log("BRONZE", table_name, "exception", None, ERROR, error_msg)

    # --- Silver tests ---
    for table_name, expected_cols in SILVER_CONTRACTS.items():
        try:
            check_silver_contract(table_name, expected_cols)
        except Exception:
            error_msg = traceback.format_exc()
            log("SILVER", table_name, "exception", None, ERROR, error_msg)

    # --- Gold tests ---
    for table_name, cols in GOLD_NOT_NULL.items():
        try:
            check_gold_not_null(table_name, cols)
        except Exception:
            error_msg = traceback.format_exc()
            log("GOLD", table_name, "exception", None, ERROR, error_msg)

    # --- Persist results ---
    results_df = spark.createDataFrame(LOGS)
    results_df.write.mode("append").saveAsTable(RESULTS_TABLE)

    # --- Summarize and return exit code ---
    failure_count = results_df.filter(F.col("status").isin(FAIL, ERROR)).count()
    if failure_count > 0:
        summary = "FAIL"
        exit_code = 1
    else:
        summary = "PASS"
        exit_code = 0

    print(f"\n===== SMOKE TEST SUMMARY: {summary} =====")
    return exit_code

if __name__ == "__main__":
    try:
        code = run_all_smoke_tests()
        if code != 0:
            raise Exception("Smoke tests failed")
    except Exception:
        traceback.print_exc()
        raise
