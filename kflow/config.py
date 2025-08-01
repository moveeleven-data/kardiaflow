# src/kflow/config.py
# Core configuration module for Kardiaflow pipeline
# Defines constants for database names, change tracking, PHI masking
# Builds standardized paths across pipeline layers

from types import SimpleNamespace
from typing import Final

from pyspark.sql import SparkSession

# Static ADLS identifiers
_ADLS_ACCOUNT:  Final = "kardiaadlsdemo"
_ADLS_SUFFIX:   Final = "core.windows.net"
_CONTAINER:     Final = "lake"

# Root URIs
LAKE_BASE: Final = f"abfss://{_CONTAINER}@{_ADLS_ACCOUNT}.dfs.{_ADLS_SUFFIX}"
RAW_BASE:  Final = f"{LAKE_BASE}/source"           # raw datasets live directly here
LAKE_ROOT: Final = f"{LAKE_BASE}/kardia"           # medallion layers

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

# Path helpers
def raw_path(ds: str)      -> str: return f"{RAW_BASE}/{ds}/"
def bronze_table(ds: str)  -> str: return f"{BRONZE_DB}.bronze_{ds}"
def silver_table(ds: str)  -> str: return f"{SILVER_DB}.silver_{ds}"

def bronze_path(ds: str)   -> str: return f"{LAKE_ROOT}/bronze/bronze_{ds}"
def silver_path(ds: str)   -> str: return f"{LAKE_ROOT}/silver/silver_{ds}"

def schema_path(ds: str)   -> str: return f"{LAKE_ROOT}/_schemas/{ds}"
def checkpoint_path(tag)   -> str: return f"{LAKE_ROOT}/_checkpoints/{tag}"
def quarantine_path(ds: str)-> str: return f"{LAKE_ROOT}/_quarantine/bad_{ds}"

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
