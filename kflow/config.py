# src/kflow/config.py
# Core configuration module for Kardiaflow pipeline
# Defines constants for database names, change tracking, PHI masking
# Builds standardized paths across pipeline layers

from types import SimpleNamespace
from typing import Final

from pyspark.sql import SparkSession

from kflow.adls import RAW_BASE

# Database names
BRONZE_DB:     Final = "kardia_bronze"
SILVER_DB:     Final = "kardia_silver"
GOLD_DB:       Final = "kardia_gold"
VALIDATION_DB: Final = "kardia_validation"

# Change data config - Only rows with these change types will be preserved
CHANGE_TYPES:  Final = ("insert", "update_postimage")

# Columns considered sensitive and masked in the Silver layer
PHI_COLS_MASK: Final = [
    "DEATHDATE", "SSN", "DRIVERS", "PASSPORT", "FIRST", "LAST",
    "BIRTHPLACE", "ADDRESS", "MAIDEN", "PREFIX", "SUFFIX"
]

# Unified ADLS base path for all Delta tables and streaming metadata.
# Structure under RAW_BASE:
#   /kardia/
#     ├─ bronze/bronze_*    - Bronze Delta tables
#     ├─ silver/silver_*    - Silver Delta tables
#     ├─ gold/              - CTAS target for Gold tables
#     ├─ _schemas/          - Auto Loader schema evolution
#     ├─ _checkpoints/      - Streaming checkpoints (CDF, joins)
#     └─ _quarantine/       - Bad records from ingest
LAKE_BASE: Final = f"{RAW_BASE}/kardia"

# DB-level default paths for managed Delta tables
BRONZE_DB_LOCATION: Final = f"{LAKE_BASE}/bronze"
SILVER_DB_LOCATION: Final = f"{LAKE_BASE}/silver"
GOLD_DB_LOCATION:   Final = f"{LAKE_BASE}/gold"

# Path builders
def raw_path(ds: str) -> str:
    return f"{RAW_BASE}/{ds}/"

def bronze_table(ds: str) -> str:
    return f"{BRONZE_DB}.bronze_{ds}"

def bronze_path(ds: str) -> str:
    return f"{LAKE_BASE}/bronze/bronze_{ds}"

def schema_path(ds: str) -> str:
    return f"{LAKE_BASE}/_schemas/{ds}"

def checkpoint_path(name: str) -> str:
    return f"{LAKE_BASE}/_checkpoints/{name}"

def quarantine_path(ds: str) -> str:
    return f"{LAKE_BASE}/_quarantine/raw/bad_{ds}"

def silver_table(ds: str) -> str:
    return f"{SILVER_DB}.silver_{ds}"

def silver_path(ds: str) -> str:
    return f"{LAKE_BASE}/silver/silver_{ds}"

def gold_table(name: str) -> str:
    return f"{GOLD_DB}.{name}"

def validation_summary_table(name: str) -> str:
    return f"{VALIDATION_DB}.{name}_summary"

# Bundled path namespaces
def bronze_paths(ds: str, checkpoint_suffix: str | None = None) -> SimpleNamespace:
    """
    Return a namespace with all paths related to a Bronze-layer dataset.

    Includes raw input, table name, storage path, schema history, checkpoint, quarantine.
    """
    cp = checkpoint_suffix or f"bronze_{ds}"
    return SimpleNamespace(
        db         = BRONZE_DB,
        table      = bronze_table(ds),
        raw        = raw_path(ds),
        bronze     = bronze_path(ds),
        schema     = schema_path(ds),
        checkpoint = checkpoint_path(cp),
        bad        = quarantine_path(ds),
    )

def silver_paths(ds: str, checkpoint_suffix: str | None = None) -> SimpleNamespace:
    """
    Return a namespace with all paths related to a Silver-layer dataset.

    Includes table name, storage path, and checkpoint directory.
    """
    cp = checkpoint_suffix or f"silver_{ds}"
    return SimpleNamespace(
        db         = SILVER_DB,
        table      = silver_table(ds),
        path       = silver_path(ds),
        checkpoint = checkpoint_path(cp),
    )

def current_batch_id() -> str:
    """
    Return the current Databricks job run ID for traceability in audit columns.

    Falls back to 'manual' if not executing within a job context.
    Used in both streaming and batch pipelines to support data lineage and reproducibility.
    """
    spark = SparkSession.builder.getOrCreate()
    return spark.conf.get("spark.databricks.job.runId", "manual")
