# KardiaFlow Unit Tests

This folder contains unit tests for the `kflow` package, covering key components used across Bronze, Silver, and Gold pipelines.

## Modules Tested

- `auth_adls`: ADLS OAuth config via mocked `dbutils` + Spark confs  
- `config`: Path helpers, PHI masking, batch ID detection  
- `etl_utils`: Adds audit metadata (e.g., `_ingest_ts`, `_batch_id`)  
- `validation`: Bronze/Silver/Gold checks + logging utils

## CI: GitHub Actions

Unit tests run automatically via kflow-ci on all pushes and PRs to master.

- Python 3.10
- Java 17 (for PySpark 4.x)
- Validates test suite against latest package code with pytest