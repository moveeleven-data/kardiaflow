# kflow/validation/logging_utils.py
"""Kardiaflow validations - in-memory logger.

Accumulates structured results in LOGS and prints.
"""

from kflow.validation.config import RUN_TS, PASS

# List to hold all validation results for this run
LOGS: list[dict] = []


def log(
    layer: str,
    table: str,
    metric: str,
    value,
    status: str,
    message: str | None = None,
) -> None:
    """
    Append a result to LOGS and print a summary line.

    Args:
        layer (str): Pipeline stage being tested ('BRONZE', 'SILVER', or 'GOLD')
        table (str): Full table name under validation (e.g. 'kardia_bronze.bronze_claims')
        metric (str): Name of the check being performed (e.g. 'row_count')
        value: Observed result of the check (e.g. 123, None, timestamp)
        status (str): Outcome of the check ('PASS', 'FAIL', or 'ERROR')
        message (str, optional): Optional explanation or error detail
    """
    # Format the value as a string
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
    print(f"[{layer}] {table} :: {metric} = {value_str} to {tag}{suffix}")
