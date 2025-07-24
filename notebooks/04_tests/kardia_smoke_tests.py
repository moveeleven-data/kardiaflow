# kardia_smoke_tests.py  — drop‑in with persisted results
import sys
from datetime import datetime
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

RESULTS_TABLE = "kardia_validation.smoke_results"
RUN_TS = datetime.utcnow()

# Config
BRONZE = [
    ("kardia_bronze.bronze_claims",     "ClaimID"),
    ("kardia_bronze.bronze_feedback",   "feedback_id"),
    ("kardia_bronze.bronze_providers",  "ProviderID"),
    ("kardia_bronze.bronze_encounters", "ID"),
    ("kardia_bronze.bronze_patients",   "ID"),
]

SILVER_CONTRACTS = {
    "kardia_silver.silver_claims": {
        "claim_id", "patient_id", "provider_id", "claim_amount",
        "claim_date", "diagnosis_code", "procedure_code",
        "claim_status", "claim_type", "claim_submission_method", "_ingest_ts"
    },
    "kardia_silver.silver_patients": {
        "id", "birth_year", "marital", "race", "ethnicity", "gender"
    },
    "kardia_silver.silver_encounters": {
        "encounter_id", "patient_id", "START_TS", "CODE", "DESCRIPTION",
        "REASONCODE", "REASONDESCRIPTION"
    },
}

GOLD_NOT_NULL = {
    "kardia_gold.gold_patient_lifecycle": ["patient_id"],
    "kardia_gold.gold_feedback_satisfaction": ["provider_id", "avg_score"],  # fixed
}

# In-memory log persisted at the end
LOGS = []

def ensure_results_table():
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


def log(layer, table, metric, value, status, message=None):
    LOGS.append({
        "run_ts": RUN_TS,
        "layer": layer,
        "table_name": table,
        "metric": metric,
        "value": str(value) if value is not None else None,
        "status": status,
        "message": message
    })
    tag = "OK" if status == "PASS" else status
    msg = f" ({message})" if message else ""
    print(f"[{layer}] {table} :: {metric} = {value} -> {tag}{msg}")


# Checks (no asserts; return PASS/FAIL via logs)
def check_bronze(table, pk):
    layer = "BRONZE"
    df = spark.table(table)
    total = df.count()
    dup   = df.groupBy(pk).count().filter("count > 1").count()
    nulls = df.filter(F.col(pk).isNull()).count()

    log(layer, table, "row_count", total, "PASS" if total > 0 else "FAIL", "row_count == 0")
    log(layer, table, "dup_pk", dup, "PASS" if dup == 0 else "FAIL")
    log(layer, table, "null_pk", nulls, "PASS" if nulls == 0 else "FAIL")

    if "_ingest_ts" in df.columns:
        max_ts = df.agg(F.max("_ingest_ts")).first()[0]
        status = "PASS" if max_ts is not None else "FAIL"
        log(layer, table, "max__ingest_ts", max_ts, status)


def check_silver_contract(table, expected_cols):
    layer = "SILVER"
    cols = set(spark.table(table).columns)
    missing = expected_cols - cols
    status = "PASS" if not missing else "FAIL"
    log(layer, table, "missing_cols_count", len(missing), status,
        f"missing={sorted(missing)}" if missing else None)


def check_gold_not_null(table, cols):
    layer = "GOLD"
    df = spark.table(table)
    for c in cols:
        n = df.filter(F.col(c).isNull()).count()
        log(layer, table, f"nulls[{c}]", n, "PASS" if n == 0 else "FAIL")


# Orchestrator
def run_all_smoke_tests() -> int:
    ensure_results_table()

    # Run tests
    for (t, pk) in BRONZE:
        try:
            check_bronze(t, pk)
        except Exception as e:
            log("BRONZE", t, "exception", None, "ERROR", str(e))

    for t, expected in SILVER_CONTRACTS.items():
        try:
            check_silver_contract(t, expected)
        except Exception as e:
            log("SILVER", t, "exception", None, "ERROR", str(e))

    for t, cols in GOLD_NOT_NULL.items():
        try:
            check_gold_not_null(t, cols)
        except Exception as e:
            log("GOLD", t, "exception", None, "ERROR", str(e))

    # Persist results
    df = spark.createDataFrame(LOGS)
    df.write.mode("append").saveAsTable(RESULTS_TABLE)

    # Exit code
    failed = df.filter(F.col("status").isin("FAIL", "ERROR")).count() > 0
    print("\n===== SMOKE TEST SUMMARY:", "FAIL" if failed else "PASS", "=====")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(run_all_smoke_tests())
