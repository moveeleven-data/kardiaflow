# src/kflow/display_utils.py
from pyspark.sql import SparkSession

def show_history(delta_path: str, limit: int = 5) -> None:
    """Uniform history printer used everywhere."""
    (spark.sql(f"DESCRIBE HISTORY delta.`{delta_path}`")
         .select("version","timestamp","operation","operationParameters")
         .orderBy("version", ascending=False)
         .show(limit, truncate=False))
