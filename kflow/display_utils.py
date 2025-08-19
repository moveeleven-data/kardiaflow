# kflow/display_utils.py
# Utilities to inspect Delta table history.

from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame

__all__ = ["get_history_df", "show_history"]


def get_history_df(target: str, limit: int = 5) -> DataFrame:
    """Return recent Delta transaction history as a DataFrame.

    Args:
        target: Delta table name.
        limit:  Maximum number of history rows to return.
    """
    spark = SparkSession.builder.getOrCreate()

    # Path-like targets get wrapped as delta.
    is_path = (
        "://" in target
        or target.startswith("/")
        or target.startswith("dbfs:")
    )
    target_ref = f"delta.`{target}`" if is_path else target

    query = f"DESCRIBE HISTORY {target_ref}"

    return (
        spark.sql(query)
             .select("version", "timestamp", "operation", "operationParameters")
             .orderBy("version", ascending=False)
             .limit(limit)
    )


def show_history(target: str, limit: int = 5) -> None:
    """Render Delta history in the Databricks UI."""
    display(get_history_df(target, limit))  # type: ignore[name-defined]
