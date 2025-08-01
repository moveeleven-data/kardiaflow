# tests/conftest.py
import pytest

from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName("kflow-tests")
        .getOrCreate()
    )
    yield spark
    spark.stop()

@pytest.fixture(autouse=True)
def clear_logs():
    # Reset LOGS between tests that use logging_utils
    try:
        from kflow.validation.logging_utils import LOGS
        LOGS.clear()
    except Exception:
        pass
