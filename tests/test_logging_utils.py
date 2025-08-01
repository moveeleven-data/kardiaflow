# tests/test_logging_utils.py
from kflow.validation.logging_utils import log, LOGS
from kflow.validation.config import PASS, FAIL

def test_log_appends_expected_shape(clear_logs):
    log("BRONZE", "kardia_bronze.bronze_patients", "row_count", 5, PASS)
    assert len(LOGS) == 1
    rec = LOGS[0]
    # keys exist
    for k in ["run_ts","layer","table_name","metric","value","status","message"]:
        assert k in rec
    assert rec["status"] == PASS

def test_log_message_optional(clear_logs):
    log("SILVER", "kardia_silver.silver_encounters", "missing_cols_count", 2, FAIL, message="missing=['X']")
    assert LOGS[-1]["message"].startswith("missing=")
