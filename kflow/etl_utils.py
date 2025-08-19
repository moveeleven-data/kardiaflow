# kflow/etl_utils.py
"""Kardiaflow - ETL utilities.

Adds standard audit columns during ingestion: ingest timestamp, source file path,
and batch ID.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
import pyspark.sql.functions as F

from kflow.config import current_batch_id


def add_audit_cols(df: DataFrame) -> DataFrame:
    """Add audit columns to the given DataFrame."""
    df_with_audit = (
        df.withColumn("_ingest_ts",   F.current_timestamp())
          .withColumn("_source_file", F.input_file_name())
          .withColumn("_batch_id",    F.lit(current_batch_id()))
    )

    return df_with_audit