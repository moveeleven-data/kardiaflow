# Bronze Ingestion: Claims, Providers & Feedback

This layer ingests raw files into Delta tables under the `kardia_bronze` schema using Auto Loader (or COPY INTO where required), with **Change Data Feed (CDF)** and **audit columns** enabled. Each dataset has its own dedicated notebook, schema, and checkpoint path, powered by `kflow.config.bronze_paths()`.

---

## Ingested Datasets

| Dataset   | Source Location                              | Format    | Loader Type     | Bronze Table                     |
|-----------|-----------------------------------------------|-----------|------------------|----------------------------------|
| Claims    | `dbfs:/kardia/raw/claims/`                   | Parquet   | Auto Loader      | `kardia_bronze.bronze_claims`    |
| Providers | `abfss://raw@kardiaadlsdemo.../providers/`   | TSV       | Auto Loader      | `kardia_bronze.bronze_providers` |
| Feedback  | `abfss://raw@kardiaadlsdemo.../feedback/`    | JSONL     | Auto Loader      | `kardia_bronze.bronze_feedback`  |

---

## Features

- CDF enabled on all Bronze tables  
- Audit columns: `_ingest_ts`, `_source_file`, `_batch_id`  
- Auto Loader in `availableNow` mode for batch-style ingestion  
- Schema evolution enabled  
- Config-driven checkpointing, bad record paths, and schema storage  
- Explicit schema enforcement for TSV/JSONL (Parquet uses embedded schema)

---

## Notebooks

| Notebook                          | Target Table                      | Notes                            |
|----------------------------------|-----------------------------------|----------------------------------|
| `01_bronze_claims_autoloader`    | `bronze_claims`                   | Parquet from DBFS                |
| `01_bronze_providers_autoloader`| `bronze_providers`                | TSV from ADLS, tab-delimited     |
| `01_bronze_feedback_copy_into`   | `bronze_feedback`                 | JSONL from ADLS, explicit schema |

---

## Post-Ingestion Validation

After each Bronze write, a matching `01_validate_bronze_<dataset>.ipynb` logs key quality metrics to the `kardia_validation.<table>_summary` tables.

Example:
```sql
SELECT * FROM kardia_validation.bronze_claims_summary ORDER BY validation_run_ts DESC;
```

---
