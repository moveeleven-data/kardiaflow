# Databricks notebook source
"""
Create / refresh Gold-layer KPI views.
Builds: vw_gender_breakdown
Runs unchanged in both dev (local paths) and prod (Databricks).
"""
import os, sys, pathlib, logging

# ── expose utils/ *before* imports ───────────────────────────────────────────
HERE = pathlib.Path(__file__).resolve()          # …/notebooks/03_gold/…
ROOT = HERE.parents[1]                           # → repo root (KardiaFlow/)
sys.path.insert(0, str(ROOT))                    # utils/ now importable

from utils.common_functions import cfg           # noqa: E402
from pyspark.sql import SparkSession

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("gold_views")

MODE = os.getenv("KARDIA_ENV", "dev")            # dev | prod
log.info(f"Running in {MODE.upper()} mode")

# ── Spark session (Delta always on) ─────────────────────────────────────────
spark = (
    SparkSession.builder
        .appName("create_gold_views")
        .master("local[1]" if MODE == "dev" else "local[*]")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# ── 1. Temp view pointing at Silver Delta -----------------------------------
silver_patients_path = f"{cfg('silver_root')}/silver_patients"

log.info("Creating temp view tmp_silver_patients …")
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW tmp_silver_patients AS
SELECT * FROM delta.`{silver_patients_path}`
""")

# ── 2. Gold KPI view -------------------------------------------------
log.info("Creating / replacing vw_gender_breakdown (TEMP) …")
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW vw_gender_breakdown AS
SELECT
    GENDER,
    COUNT(*) AS cnt
FROM
    tmp_silver_patients
GROUP BY
    GENDER
""")

# ── 3. Sanity-check ---------------------------------------------------------
log.info("Preview of vw_gender_breakdown:")
spark.sql("SELECT * FROM vw_gender_breakdown").show()

log.info("Gold KPI view created successfully")
