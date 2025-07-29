# display_utils.py
# Helpers to inspect Delta table history
from pyspark.sql import SparkSession

def get_history_df(target: str, limit: int = 5):
    """Return a DataFrame of the Delta transaction history for a table or path."""
    spark = SparkSession.builder.getOrCreate()

    # If the input looks like a path, treat it as a path and wrap it in 'delta.'
    # Delta tables stored in filesystems need to be wrapped as `delta.` paths
    is_path = (
        "://" in target
        or target.startswith("/")
        or target.startswith("dbfs:")
    )

    # Build the appropriate DESCRIBE HISTORY query
    if is_path:
        target_ref = f"delta.`{target}`"
    else:
        target_ref = target

    query = f"DESCRIBE HISTORY {target_ref}"

    # Execute the query and return a simplified DataFrame
    history_df = (
        spark.sql(query)
             .select("version", "timestamp", "operation", "operationParameters")
             .orderBy("version", ascending=False)
             .limit(limit)
    )

    return history_df


def show_history(target: str, limit: int = 5):
    """Display Delta history in the Databricks UI."""
    display(get_history_df(target, limit))