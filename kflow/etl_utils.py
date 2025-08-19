# kflow/etl_utils.py
# Utility function for DataFrame enrichment during ingestion
# Adds standard audit columns: ingestion timestamp, source file path, batch ID

import pyspark.sql.functions as F
from pyspark.sql import DataFrame

from .config import current_batch_id

def add_audit_cols(df: DataFrame) -> DataFrame:
    """Add standard audit columns to an input DF."""
    df_with_audit = (
        df.withColumn("_ingest_ts",   F.current_timestamp())
          .withColumn("_source_file", F.input_file_name())
          .withColumn("_batch_id",    F.lit(current_batch_id()))
    )

    return df_with_audit