# Kardiaflow tests - Logging utilities
# Validates in-memory logging behavior and message handling.

from kflow.validation.config import PASS, FAIL
from kflow.validation.logging_utils import log, LOGS


def test_log_appends_expected_shape(clear_logs):
    """Verify that `log()` appends a structured record with all required fields."""

    # Call the log function with a standard success case
    log(
        layer="BRONZE",
        table="kardia_bronze.bronze_patients",
        metric="row_count",
        value=5,
        status=PASS
    )

    # Confirm that one record was added to LOGS
    assert len(LOGS) == 1

    record = LOGS[0]

    # Validate that all expected keys are present
    expected_keys = [
        "run_ts",
        "layer",
        "table_name",
        "metric",
        "value",
        "status",
        "message"
    ]

    for key in expected_keys:
        assert key in record

    # Confirm that the status was correctly set
    assert record["status"] == PASS


def test_log_message_optional(clear_logs):
    """Verify that `log()` records the optional message field when provided."""

    # Call the log function with a custom message
    log(
        layer="SILVER",
        table="kardia_silver.silver_encounters",
        metric="missing_cols_count",
        value=2,
        status=FAIL,
        message="missing=['X']"
    )

    # Verify that the message was logged as expected
    last_record = LOGS[-1]
    assert last_record["message"].startswith("missing=")