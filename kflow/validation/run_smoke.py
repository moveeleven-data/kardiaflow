# kflow/validation/run_smoke.py
"""Kardiaflow validations — smoke test runner.

Runs Bronze, Silver, and Gold checks, persists results to Delta, and prints a
PASS/FAIL summary.
"""

from __future__ import annotations

from pyspark.sql import SparkSession, functions as F
import traceback

from kflow.auth_adls import ensure_adls_oauth
from kflow.validation.config import (
    BRONZE,
    ERROR,
    FAIL,
    GOLD_NOT_NULL,
    RESULTS_TABLE,
    SILVER_CONTRACTS
)
from kflow.validation.bronze_checks import check_bronze
from kflow.validation.gold_checks import check_gold_not_null
from kflow.validation.logging_utils import LOGS, log
from kflow.validation.silver_checks import check_silver_contract


def _ensure_results_table(spark: SparkSession) -> None:
    """Create the database/table used to store validation results if missing."""
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
    """Execute all validations and persist results. Returns 0 on success, 1 otherwise."""
    spark = SparkSession.builder.getOrCreate()

    # Catalog selection
    spark.sql("USE CATALOG hive_metastore")

    # Configure ABFS OAuth (validates container root by default).
    ensure_adls_oauth()

    _ensure_results_table(spark)

    # Bronze checks (table, primary key)
    for table_name, pk in BRONZE:
        try:
            check_bronze(table_name, pk)
        except Exception:
            log(
                layer="BRONZE",
                table=table_name,
                metric="exception",
                value=None,
                status=ERROR,
                message=traceback.format_exc(),
            )

    # Silver checks (contract: required columns per table)
    for table_name, expected_cols in SILVER_CONTRACTS.items():
        try:
            check_silver_contract(table_name, expected_cols)
        except Exception:
            log(
                layer="SILVER",
                table=table_name,
                metric="exception",
                value=None,
                status=ERROR,
                message=traceback.format_exc(),
            )

    # Gold checks (columns that must be NOT NULL)
    for table_name, cols in GOLD_NOT_NULL.items():
        try:
            check_gold_not_null(table_name, cols)
        except Exception:
            log(
                layer="GOLD",
                table=table_name,
                metric="exception",
                value=None,
                status=ERROR,
                message=traceback.format_exc(),
            )

    # Persist logs and summarize.
    results_df = spark.createDataFrame(LOGS)
    results_df.write.mode("append").saveAsTable(RESULTS_TABLE)

    failures = results_df.filter(F.col("status").isin(FAIL, ERROR)).count()
    print(f"\nSMOKE TEST SUMMARY: {'FAIL' if failures else 'PASS'}")
    return 0 if failures == 0 else 1