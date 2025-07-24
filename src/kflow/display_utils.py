# src/kflow/display_utils.py
from pyspark.sql import SparkSession

def show_history(target: str, limit: int = 5) -> None:
    """
    Uniform Delta history printer.
    Works for both table names (e.g., kardia_bronze.bronze_claims)
    and Delta paths (e.g., dbfs:/..., abfss:/...).

    Usage:
        show_history(P.bronze)   # path
        show_history(P.table)    # table name
    """
    spark = SparkSession.builder.getOrCreate()

    # Heuristic: if it looks like a path, address with delta.`...`, else treat as table
    if "://" in target or target.startswith("/") or target.startswith("dbfs:"):
        query = f"DESCRIBE HISTORY delta.`{target}`"
    else:
        query = f"DESCRIBE HISTORY {target}"

    (spark.sql(query)
          .select("version", "timestamp", "operation", "operationParameters")
          .orderBy("version", ascending=False)
          .show(limit, truncate=False))
