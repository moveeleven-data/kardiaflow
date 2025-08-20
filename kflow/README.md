# kflow/

Library of utilities powering the KardiaFlow pipeline. Designed Databricks notebooks/jobs.

## Modules

- **auth_adls** – OAuth authentication to ADLS Gen2 via dbutils secrets
- **config** – Centralized paths, job IDs, SCD keys, and PHI column config
- **display_utils** – Convenience display helpers for notebooks
- **etl_utils** – Shared ETL helpers (e.g., audit columns, convert timestamps to UTC)
- **validation/** – Data quality checks:
  - `bronze_checks` – nulls, duplicates, ingest timestamps
  - `silver_checks` – schema contracts
  - `gold_checks` – not-null assertions
  - `logging_utils` – testable, structured audit logs
  - `run_smoke` – entrypoint for `notebooks/04_tests/run_validation.ipynb`