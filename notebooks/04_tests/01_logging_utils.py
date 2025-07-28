# 01_logging_utils.py
# Logging utilities for KardiaFlow smoke tests:
# - LOGS: in-memory list of all test results
# - log(): appends results and prints a summary line

from _00_config import RUN_TS, PASS

# A list to collect each test result as a dict.
# Populated by log(), then written out in run_smoke.py.
LOGS = []


def log(layer, table, metric, value, status, message=None):
    """
    Append a structured test result to LOGS and print a summary.

    Args:
        layer (str): 'BRONZE', 'SILVER', or 'GOLD'
        table (str): Table under test (e.g. 'kardia_bronze.bronze_claims')
        metric (str): Metric name (e.g. 'row_count')
        value: Measured value (e.g. 123 or timestamp)
        status (str): PASS, FAIL, or ERROR
        message (str, optional): Extra context or error details
    """
    # Prepare the value for storage: keep None as None, else stringify
    if value is None:
        value_str = None
    else:
        value_str = str(value)

    # Build the result record
    result = {
        "run_ts": RUN_TS,
        "layer": layer,
        "table_name": table,
        "metric": metric,
        "value": value_str,
        "status": status,
        "message": message
    }

    # Store it in memory
    LOGS.append(result)

    # Format status tag for printing: show "OK" for PASS, else show the status itself
    if status == PASS:
        tag = "OK"
    else:
        tag = status

    # Build the message suffix only if an extra message is provided
    if message:
        suffix = f" ({message})"
    else:
        suffix = ""

    # Print a readable summary line
    print(f"[{layer}] {table} :: {metric} = {value_str} -> {tag}{suffix}")
