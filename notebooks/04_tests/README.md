# Smoke Test Suite for KardiaFlow

Runs end‑to‑end smoke tests on the Bronze, Silver and Gold Delta tables in Kardiaflow pipeline.

All test records are appended to the Delta table kardia_validation.smoke_results with columns:

> run_ts | layer | table_name | metric | value | status | message

Each row shows what was tested and whether it passed, failed or errored.

---

## File overview

- `00_config.py`  
  Defines test status constants (`PASS`, `FAIL`, `ERROR`), sets the run timestamp, declares Bronze/Silver/Gold table contracts, and manages the downstream duplicate suppression map.


- `01_logging_utils.py`  
  Maintains an in-memory `LOGS` list and provides the `log()` function to record and print structured test results.


- `10_bronze_checks.py`  
  Validates Bronze tables by checking:  
  1. Row count > 0  
  2. No duplicate primary keys (with optional suppression)  
  3. No null primary keys  
  4. Valid `_ingest_ts` column if present


- `11_silver_checks.py`  
  Ensures each Silver table includes all expected columns defined in the contract.


- `12_gold_checks.py`  
  Verifies that specified Gold-layer columns contain no `NULL` values.


- `99_run_smoke.py`  
  Coordinates test execution by:  
  1. Installing the `kflow` package from DBFS  
  2. Running all Bronze, Silver, and Gold checks  
  3. Writing results from `LOGS` to the Delta table `kardia_validation.smoke_results`  
  4. Printing a final PASS/FAIL summary
