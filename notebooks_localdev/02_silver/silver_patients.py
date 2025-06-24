# Databricks notebook source
"""
Silver transform: bronze_patients_changes ➜ silver_patients
  • keeps only inserts / update_postimage
  • drops duplicate IDs
  • masks FIRST & LAST (sets to NULL)
Works unchanged in local dev or Databricks.
"""
import sys, pathlib, os
from pyspark.sql import SparkSession, functions as F

# ── import utils ----------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]   # …/notebooks
sys.path.insert(0, str(ROOT))                        # expose utils/
from utils.common_functions import cfg               # path resolver

# ── Spark session (always with Delta ext) ---------------------------
spark = (
    SparkSession.builder
      .appName("silver_patients")
      .master("local[1]")                           # harmless on Databricks
      .config("spark.sql.extensions",
              "io.delta.sql.DeltaSparkSessionExtension")
      .config("spark.sql.catalog.spark_catalog",
              "org.apache.spark.sql.delta.catalog.DeltaCatalog")
      .config("spark.sql.shuffle.partitions", "1")
      .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# ── Bronze Delta location ------------------------------------------
bronze_dir   = pathlib.Path(f"{cfg('bronze_root')}/bronze_patients")
bronze_uri   = f"delta.`{bronze_dir.as_posix()}`"         # delta.`file:///…`

# ── (Re)create CDF temp-view in THIS session -----------------------
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW bronze_patients_changes AS
SELECT *
FROM table_changes('{bronze_uri}', 0)
""")

# ── Build Silver ----------------------------------------------------
silver_dir = pathlib.Path(f"{cfg('silver_root')}/silver_patients")

(
  spark.table("bronze_patients_changes")
       .filter("_change_type IN ('insert','update_postimage')")
       .dropDuplicates(["ID"])
       .withColumn("FIRST", F.lit(None).cast("string"))
       .withColumn("LAST",  F.lit(None).cast("string"))
       .write.format("delta")
       .mode("overwrite")
       .save(silver_dir.as_posix())
)

print(f"Silver written → {silver_dir}")
print("Row count :", spark.read.format("delta").load(silver_dir.as_posix()).count())
