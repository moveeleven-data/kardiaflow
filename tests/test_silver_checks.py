# Kardiaflow tests - Silver checks
# Ensures Silver-layer validation enforces schema contracts:
# required columns must exist in every Silver table.

from kflow.validation import silver_checks
from kflow.validation.config import FAIL
from kflow.validation.logging_utils import LOGS


def test_silver_contract_missing_cols(spark, clear_logs):
    """Fail when required Silver columns are missing."""

    # Build a DataFrame that deliberately omits a required column (START_TS)
    df = spark.createDataFrame(
        [(None, None)],
        schema="encounter_id string, patient_id string",
    )

    # Register as a temp view so check_silver_contract can resolve it by name
    df.createOrReplaceTempView("silver_encounters")

    # Define the expected schema contract — START_TS is intentionally missing
    expected = {"encounter_id", "patient_id", "START_TS"}

    # Run the Silver contract validation
    silver_checks.check_silver_contract("silver_encounters", expected)

    # Verify the last log entry reports a failure with the missing column
    last_log = LOGS[-1]
    assert last_log["status"] == FAIL
    assert "missing" in (last_log["message"] or "")
    assert "START_TS" in (last_log["message"] or "")