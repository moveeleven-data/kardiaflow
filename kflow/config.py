# kflow/config.py
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

# Single base URI for the ADLS Gen2 container (public)
_CONTAINER_URI: Final = f"abfss://{_CONTAINER}@{_ADLS_ACCOUNT}.dfs.{_ADLS_SUFFIX}"

# Medallion layer root directories
GOLD_DIR: Final = f"{_CONTAINER_URI}/kardia/gold"

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
def raw_path(ds: str)      -> str: return f"{_CONTAINER_URI}/source/{ds}/"
def bronze_table(ds: str)  -> str: return f"{BRONZE_DB}.bronze_{ds}"
def silver_table(ds: str)  -> str: return f"{SILVER_DB}.silver_{ds}"

def bronze_path(ds: str)   -> str: return f"{_CONTAINER_URI}/kardia/bronze/bronze_{ds}"
def silver_path(ds: str)   -> str: return f"{_CONTAINER_URI}/kardia/silver/silver_{ds}"

def schema_path(ds: str)   -> str: return f"{_CONTAINER_URI}/kardia/_schemas/{ds}"
def checkpoint_path(tag)   -> str: return f"{_CONTAINER_URI}/kardia/_checkpoints/{tag}"
def quarantine_path(ds: str)-> str: return f"{_CONTAINER_URI}/kardia/_quarantine/bad_{ds}"

# Bundled path namespaces
def bronze_paths(ds: str, checkpoint_suffix: str | None = None) -> SimpleNamespace:
    """ Return a namespace with all paths related to a Bronze-layer dataset. """
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
    """ Return a namespace with all paths related to a Silver-layer dataset. """
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
    """
    spark = SparkSession.builder.getOrCreate()
    return spark.conf.get("spark.databricks.job.runId", "manual")
