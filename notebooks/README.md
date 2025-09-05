# Kardiaflow Databricks Notebooks

This directory contains the Databricks notebooks that implement Kardiaflow’s Bronze, Silver, Gold, and validation layers (with optional streaming for Encounters).

In Kardiaflow, Bronze and Silver are persisted as Delta tables to support durability,
lineage, and incremental upserts at scale. Gold is also stored as Delta tables with snapshot overwrites,
since the datasets are small enough to rebuild fully each run.

Unlike dbt’s view-heavy convention, we persist earlier since Spark pipelines deal with high velocity datasets from 
many source systems and depend on streaming updates and complex state management, making tables the more practical
choice for reliability and performance.

---

The sections below provide a dataset-by-dataset breakdown of how each notebook processes data through the medallion architecture.

### Raw input paths

| Dataset     | ADLS Path                                                 | Format  |
|------------ |-----------------------------------------------------------|---------|
| Patients    | `abfss://lake@<storage>.dfs.core.windows.net/patients/`   | CSV     |
| Encounters  | `abfss://lake@<storage>.dfs.core.windows.net/encounters/` | Avro    |
| Claims      | `abfss://lake@<storage>.dfs.core.windows.net/claims/`     | Parquet |
| Providers   | `abfss://lake@<storage>.dfs.core.windows.net/providers/`  | TSV     |
| Feedback    | `abfss://lake@<storage>.dfs.core.windows.net/feedback/`   | JSONL   |

---

## Bronze Ingestion

Raw files are ingested into **Bronze** Delta tables under the `kardia_bronze` schema. **Auto Loader** is used for structured tabular datasets (CSV, TSV, Parquet, Avro), while **COPY INTO** is used for the semi-structured JSONL **Feedback** dataset where SQL projection, casting, and optional fields are required. Paths, checkpoints, and schemas are driven by `kflow.config.bronze_paths()`.

- **Change Data Feed (CDF)** enabled on all Bronze tables  
- **Audit columns**: `_ingest_ts`, `_source_file`, `_batch_id`  
- **Auto Loader** for batch-style runs (Encounters can also run in streaming mode)  
- **Schema handling**: explicit schema for CSV/TSV/JSONL; Parquet/Avro rely on embedded schema
- **Config-driven** checkpoint, bad-record, and schema storage locations

| Dataset     | Format   | Loader       | Bronze Table                      |
|-------------|----------|--------------|-----------------------------------|
| Patients    | CSV      | Auto Loader  | `kardia_bronze.bronze_patients`   |
| Encounters  | Avro     | Auto Loader  | `kardia_bronze.bronze_encounters` |
| Claims      | Parquet  | Auto Loader  | `kardia_bronze.bronze_claims`     |
| Providers   | TSV      | Auto Loader  | `kardia_bronze.bronze_providers`  |
| Feedback    | JSONL    | COPY INTO    | `kardia_bronze.bronze_feedback`   |

---

## Silver Transformation

Silver notebooks apply deduplication, SCD logic, and PHI masking

| Dataset     | Method               | Silver Table                        |
|-------------|----------------------|-------------------------------------|
| Patients    | Batch SCD Type 1     | `kardia_silver.silver_patients`     |
| Encounters  | Continuous Streaming | `kardia_silver.silver_encounters`   |
| Claims      | SCD Type 1           | `kardia_silver.silver_claims`       |
| Providers   | SCD Type 2           | `kardia_silver.silver_providers`    |
| Feedback    | Append-only          | `kardia_silver.silver_feedback`     |

### Enriched Silver Views

| View Name                    | Description                                      |
|-----------------------------|--------------------------------------------------|
| `silver_encounters_enriched`| Encounters joined with patient demographics      |
| `silver_claims_enriched`    | Claims joined with current provider attributes   |
| `silver_feedback_enriched`  | Feedback joined with current provider metadata   |

---

## Gold KPIs

Gold notebooks generate business-level aggregations for analytics and dashboards:

| Table Name                    | Description                                                  |
|------------------------------|--------------------------------------------------------------|
| `gold_patient_lifecycle`     | Visit intervals, patient lifespan, new/returning flags       |
| `gold_claim_metrics`       | Approval rates, denials, high‑cost procedures and rapid‑fire claims               |
| `gold_provider_rolling_spend`| Daily spend and 7‑day rolling KPIs for provider payments     |
| `gold_feedback_metrics`      | Satisfaction, tag analysis and encounter match KPIs       |

---

## Validation

Data quality checks in `kflow.validation` can be run via `run_smoke.py`, with results stored in the `kardia_validation.smoke_results` Delta table.  

- **Bronze layer** – Checks row counts, primary key nulls/duplicates, and `_ingest_ts` values.  
- **Silver layer** – Validates schema contract compliance.  
- **Gold layer** – Ensures critical fields are not null.  

---

## Streaming Modes

The Encounters pipeline supports batch or streaming, controlled by a `mode` task parameter. If `mode` is omitted, it runs in batch.

| Mode     | Behavior                                      |
|----------|-----------------------------------------------|
| `batch`  | One-time read of all available data           |
| `stream` | Continuous micro-batches every ~30 seconds    |

`mode` applies only to Encounters tasks: `bronze_encounters_autoloader`, `silver_encounters_scd1`, and `z_silver_encounters_enriched`. All other datasets (Patients, Claims, Providers, Feedback) always run in batch.

### Set the mode (Jobs UI)

Open kardiaflow_encounters → select an Encounters task → **Edit** → add parameter `mode` with value `batch` or 
`stream`.