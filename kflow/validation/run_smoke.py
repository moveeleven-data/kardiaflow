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

# Now import your smoke‑test modules from inside the kflow.tests package
from .config import (
    RESULTS_TABLE,
    BRONZE,
    SILVER_CONTRACTS,
    GOLD_NOT_NULL,
    PASS,
    FAIL,
    ERROR
)
from .logging_utils   import LOGS, log
from .bronze_checks   import check_bronze
from .silver_checks   import check_silver_contract
from .gold_checks     import check_gold_not_null

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
    ensure_results_table()

    # --- Bronze tests ---
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

    # --- Silver tests ---
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

    # --- Gold tests ---
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

    # --- Persist results ---
    results_df = spark.createDataFrame(LOGS)
    results_df.write.mode("append").saveAsTable(RESULTS_TABLE)

    # --- Summarize and exit ---
    failures = results_df.filter(F.col("status").isin(FAIL, ERROR)).count()
    summary = "FAIL" if failures > 0 else "PASS"
    print(f"\n===== SMOKE TEST SUMMARY: {summary} =====")

    return 1 if failures > 0 else 0

if __name__ == "__main__":
    try:
        exit_code = run_all_smoke_tests()
        if exit_code != 0:
            raise Exception("Smoke tests failed")
    except Exception:
        traceback.print_exc()
        raise
