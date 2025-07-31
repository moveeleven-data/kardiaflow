import importlib
from kflow import config as cfg

def test_phi_cols_contains_new_entries():
    must_have = {"ADDRESS", "MAIDEN", "PREFIX", "SUFFIX", "DRIVERS"}
    # After your code change, PHI_COLS_MASK must contain those
    assert must_have.issubset(set(cfg.PHI_COLS_MASK))

def test_table_helpers():
    assert cfg.bronze_table("encounters") == "kardia_bronze.bronze_encounters"
    assert cfg.silver_table("patients") == "kardia_silver.silver_patients"

def test_current_batch_id_defaults_and_respects_conf(mocker):
    # Default -> "manual"
    # Reload module to ensure a fresh SparkSession context
    import kflow.config as config
    importlib.reload(config)
    assert config.current_batch_id() == "manual"

    # Now set job run id on Spark conf and test again
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.databricks.job.runId", "123")
    importlib.reload(config)
    assert config.current_batch_id() == "123"
