# Databricks notebook source

#%%
"""
Bronze ingest: patients → Delta (always works, local or Databricks)
"""
import os, sys, pathlib, logging

# Dynamically add project root to PYTHONPATH so "utils" works
HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]         # notebooks/01_bronze/ → KardiaFlow/
sys.path.insert(0, str(ROOT))  # so utils/ is now importable

from pyspark.sql import SparkSession
from utils.common_functions import cfg

# ─── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("bronze_patients")

# ─── Environment & paths ────────────────────────────────────────────
MODE = os.getenv("KARDIA_ENV", "dev")      # dev | prod
RAW_PATH     = f"{cfg('raw_root')}/patients_100.csv"
BRONZE_DIR   = f"{cfg('bronze_root')}/bronze_patients"

# Ensure target dir exists in dev
if MODE == "dev":
    pathlib.Path(BRONZE_DIR).mkdir(parents=True, exist_ok=True)

log.info(f"RAW PATH     → {RAW_PATH}")
log.info(f"BRONZE PATH  → {BRONZE_DIR}")

# ─── SparkSession with *always-on* Delta configs ────────────────────
spark = (
    SparkSession.builder
      .appName("bronze_patients")
      .master("local[1]" if MODE == "dev" else "local[*]")   # 1 core local; Databricks ignores
      .config("spark.sql.shuffle.partitions", "1")
      .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
      .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
      .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# ─── Read CSV (no schema inference) ─────────────────────────────────
df = (
    spark.read
         .option("header", True)
         .option("inferSchema", False)
         .csv(RAW_PATH)
)
row_cnt = df.count()

# ─── Write Delta w/ Change Data Feed on ─────────────────────────────
(df.write
   .format("delta")
   .mode("overwrite")
   .option("delta.enableChangeDataFeed", "true")
   .save(BRONZE_DIR)
)

# ─── Show a tiny preview ────────────────────────────────────────────
log.info("Write finished.")
log.info(f"Row count: {row_cnt}")
log.info(f"Columns : {df.columns}")
log.info("Preview :")
for r in df.take(3):
    log.info(r)
