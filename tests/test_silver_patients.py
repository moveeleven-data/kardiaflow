# tests/test_silver_patients.py
"""
Unit-tests for silver_patients:
  • FIRST & LAST masked
  • Gender only M/F
  • IDs unique
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # …/KardiaFlow
NOTEBOOKS = ROOT / "notebooks"                      # …/KardiaFlow/notebooks
sys.path[:0] = [str(NOTEBOOKS)]

import pytest
from pyspark.sql import SparkSession
from utils.common_functions import cfg

# ── Spark session fixture (module-scoped = 1 per test run) -----------------
@pytest.fixture(scope="module")
def spark():
    spark = (
        SparkSession.builder
            .appName("silver_tests")
            .master("local[1]")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    yield spark
    spark.stop()


# ── Convenience fixture: load the Silver DataFrame -------------------------
@pytest.fixture(scope="module")
def df_silver(spark):
    silver_path = Path(f"{cfg('silver_root')}/silver_patients").as_posix()
    return spark.read.format("delta").load(silver_path)


# ── 1. FIRST & LAST must be NULL -------------------------------------------
def test_names_masked(df_silver):
    bad = df_silver.filter("FIRST IS NOT NULL OR LAST IS NOT NULL").count()
    assert bad == 0, "FIRST/LAST should have been masked to NULL"


# ── 2. Only ‘M’ or ‘F’ are allowed in GENDER -------------------------------
def test_gender_enum(df_silver):
    bad = df_silver.filter(~df_silver.GENDER.isin("M", "F")).count()
    assert bad == 0, "GENDER must be ‘M’ or ‘F’"


# ── 3. IDs must be unique --------------------------------------------------
def test_no_duplicate_ids(df_silver):
    from pyspark.sql import functions as F
    dup = (
        df_silver.groupBy("ID")
                 .agg(F.count("*").alias("cnt"))
                 .filter("cnt > 1")
                 .count()
    )
    assert dup == 0, "Duplicate patient IDs found in Silver table"
