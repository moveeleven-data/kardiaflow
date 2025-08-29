# kflow/notebook_utils.py
"""
Kardiaflow — Notebook helpers.

Convenience functions for use in Databricks notebooks:

1. init(): configure ADLS OAuth and switch to the Hive Metastore catalog
2. get_history_df(): query recent Delta transaction history
3. show_history(): display history (pretty in notebooks, .show() in jobs)
"""

from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame

from kflow.auth_adls import ensure_adls_oauth

def init() -> None:
    """Authenticate to ADLS and set the default catalog to Hive Metastore.

    This ensures both storage access and the expected metastore context
    are available for all subsequent SQL statements.
    """
    ensure_adls_oauth()
    spark = SparkSession.builder.getOrCreate()
    spark.sql("USE CATALOG hive_metastore")


def get_history_df(target: str, limit: int = 5) -> DataFrame:
    """Return recent Delta transaction history as a DataFrame.

    Args:
        target: Delta table name (e.g. "bronze.users")
                or a path (e.g. "/mnt/lake/bronze/users").
        limit:  Max number of history rows to return.
    """
    spark = SparkSession.builder.getOrCreate()

    # Wrap paths as delta.`<path>` so Spark treats them as Delta tables.
    is_path = (
        "://" in target
        or target.startswith("/")
        or target.startswith("dbfs:")
    )
    target_ref = f"delta.`{target}`" if is_path else target

    # Query the table's full Delta history
    df = spark.sql(f"DESCRIBE HISTORY {target_ref}")

    # Select key columns only
    df = df.select(
        "version",
        "timestamp",
        "operation",
        "operationParameters",
    )

    # Sort by most recent and apply limit
    df = df.orderBy("version", ascending=False)
    df = df.limit(limit)

    return df


def show_history(target: str, limit: int = 5) -> None:
    """Show Delta history in Databricks notebooks; print in Jobs as a fallback."""
    df = get_history_df(target, limit)
    try:
        display(df)  # type: ignore[name-defined]
    except NameError:
        df.show(truncate=False)