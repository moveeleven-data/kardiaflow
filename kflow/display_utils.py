# kflow/display_utils.py
"""Kardiaflow - Delta Lake history helpers.

Fetch and display recent transaction history for a Delta table or path.
"""

from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame


def get_history_df(target: str, limit: int = 5) -> DataFrame:
    """Return recent Delta transaction history as a DataFrame.

    Args:
        target: Delta table name (e.g. "bronze.users")
                or a filesystem path (e.g. "/mnt/lake/bronze/users").
        limit:  Maximum number of history rows to return.
    """
    spark = SparkSession.builder.getOrCreate()

    # Paths must be wrapped in delta.`<path>` so Spark recognizes them
    # as Delta tables instead of plain files.
    is_path = (
        "://" in target
        or target.startswith("/")
        or target.startswith("dbfs:")
    )
    target_ref = f"delta.`{target}`" if is_path else target

    # Build the SQL statement to describe the Delta table’s history.
    query = f"DESCRIBE HISTORY {target_ref}"

    # Execute the query and capture the full history DataFrame.
    df = spark.sql(query)

    # Select a subset of columns that are most useful when viewing history.
    df = df.select(
        "version",
        "timestamp",
        "operation",
        "operationParameters",
    )

    # Sort newest-to-oldest so the latest changes come first.
    df = df.orderBy("version", ascending=False)

    # Keep only the most recent `limit` rows.
    df = df.limit(limit)

    return df


def show_history(target: str, limit: int = 5) -> None:
    """Render the Delta history in the Databricks UI."""
    display(get_history_df(target, limit))  # type: ignore[name-defined]
