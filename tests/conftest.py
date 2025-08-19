"""Kardiaflow tests - Shared fixtures

Provides a SparkSession and clears the in-memory log buffer between tests.
"""

from __future__ import annotations

import pytest
from pyspark.sql import SparkSession

from kflow.validation.logging_utils import LOGS


@pytest.fixture(scope="session")
def spark():
    """Provide a local SparkSession for test modules."""
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
    """Clear in-memory logs before each test."""
    LOGS.clear()