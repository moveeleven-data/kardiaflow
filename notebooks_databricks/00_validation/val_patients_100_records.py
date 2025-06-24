#%%
# Databricks notebook source
# MAGIC %md
# MAGIC ## KardiaFlow – micro-inspection of 100-row patients slice (ultra-cheap)

# COMMAND ----------
import os, sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from pyspark.sql import SparkSession
from utils.common_functions import cfg
from pyspark.sql import functions as F

# ─── Runtime switch ────────────────────────────────────────────────────────────
MODE = os.getenv("KARDIA_ENV", "dev")        # dev | prod
raw_root      = cfg("raw_root")
patients_path = f"{raw_root}/patients_100.csv"   # already only 100 rows

# ─── Spark session (1 core in dev, normal in prod) ────────────────────────────
builder = (
    SparkSession.builder
    .appName("validate_patients_100")
    .config("spark.sql.shuffle.partitions", "1")
)
if MODE == "dev":
    builder = builder.master("local[1]")     # single JVM thread
else:
    builder = (
        builder
        .config("spark.sql.extensions","io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# ─── Tiny read, no schema inference ────────────────────────────────────────────
df = (
    spark.read
         .option("header", True)
         .option("inferSchema", False)
         .csv(patients_path)
         .cache()                # touch the 100 rows only once
)
row_cnt = df.count()             # single action

# ─── Rule checks (done in one pass) ────────────────────────────────────────────
bad_gender = df.filter(~F.col("GENDER").isin("M","F"))
null_id    = df.filter(F.col("ID").isNull())

# ─── (prod only) light Delta footprint: use temp view, no actual files ─────────
if MODE == "prod":
    df.createOrReplaceTempView("kardia_patients_stage")   # in-memory, free
else:
    print("🛈 DEV mode – no Delta write.")

# ─── Human summary ────────────────────────────────────────────────────────────
print("\n=== VALIDATION SUMMARY (100-row slice) ===")
print(f"Row count OK?          {row_cnt == 100}  ({row_cnt})")
print(f"ID column no NULLs?    {null_id.count() == 0}")
print(f"GENDER values OK?      {bad_gender.count() == 0}")
print("==========================================\n")

if row_cnt != 100 or null_id.count() or bad_gender.count():
    print("Data quality failed. Sample offending rows ↓")
    null_id.take(5)    and print(null_id.take(5))
    bad_gender.take(5) and print(bad_gender.take(5))
    sys.exit(1)
else:
    print("All checks passed.")
