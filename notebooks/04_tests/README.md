# Smoke Test Suite for KardiaFlow

Runs end‑to‑end smoke tests on the Bronze, Silver and Gold Delta tables in Kardiaflow pipeline.

All test records are appended to the Delta table kardia_validation.smoke_results with columns:

> run_ts | layer | table_name | metric | value | status | message

Each row shows what was tested and whether it passed, failed or errored.

---

## File overview

- `config.py`  
  Defines test status constants (`PASS`, `FAIL`, `ERROR`), sets the run timestamp, declares Bronze/Silver/Gold table contracts, and manages the downstream duplicate suppression map.


- `logging_utils.py`  
  Maintains an in-memory `LOGS` list and provides the `log()` function to record and print structured test results.


- `bronze_checks.py`  
  Validates Bronze tables by checking:  
  1. Row count > 0  
  2. No duplicate primary keys (with optional suppression)  
  3. No null primary keys  
  4. Valid `_ingest_ts` column if present


- `silver_checks.py`  
  Ensures each Silver table includes all expected columns defined in the contract.


- `gold_checks.py`  
  Verifies that specified Gold-layer columns contain no `NULL` values.


- `run_smoke.py`  
  Defines the `run_all_smoke_tests()` entrypoint and orchestrates the suite by:
  1. Installing the `kflow` wheel from DBFS (which contains the `kflow.validation` test module)  
  2. Invoking `run_all_smoke_tests()` to run Bronze, Silver, and Gold checks  
  3. Writing the in‑memory `LOGS` list into the Delta table `kardia_validation.smoke_results`  
  4. Printing a PASS/FAIL summary to stdout
