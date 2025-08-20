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


def tag_timestamp_source(df: DataFrame, ts_col: str, out_col: str = "timestamp_source") -> DataFrame:
    """Flag whether a raw timestamp string carried a timezone.

    'offset' if the value ends with 'Z' or ±HH(:MM), else 'naive'.
    Preserves provenance after parsing to TIMESTAMP.
    """
    offset_pattern = r"(Z|[+-]\d{2}(?::?\d{2})?)$"

    has_offset = F.col(ts_col).rlike(offset_pattern)
    flag = F.when(has_offset, F.lit("offset")).otherwise(F.lit("naive"))
    result = df.withColumn(out_col, flag)

    return result


def parse_to_utc(df: DataFrame, ts_col: str, out_col: str | None = None) -> DataFrame:
    """Parse a raw string into Spark TIMESTAMP (session pinned to UTC).

    Overwrites ts_col unless out_col is specified.
    """
    target_col = out_col or ts_col
    parsed_ts = F.to_timestamp(F.col(ts_col))
    result = df.withColumn(target_col, parsed_ts)

    return result