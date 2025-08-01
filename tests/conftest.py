# tests/conftest.py
# Shared Pytest fixtures for Kardiaflow tests
# - Provides local SparkSession
# - Clears in-memory log buffer between tests
import pytest

from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """
    Provides a local SparkSession for test modules.

    Shared across all tests to support DataFrame creation and Spark APIs.
    """
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
    """
    Clears logs before each test.

    Prevents log state from leaking across tests that validate pipeline checks.
    """
    try:
        from kflow.validation.logging_utils import LOGS
        LOGS.clear()
    except Exception:
        pass
